"""Bounded public launch checks, invoked as a file without importing TopoLab.

This executes only four preregistered public marker texts. It neither imports
TopoLab nor repairs/replays a historical launch or numerical campaign.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import traceback
import types
from importlib.machinery import PathFinder
from pathlib import Path
from typing import Any

VERSION = "topolab.public-launch-preflight.v1"
MARKER = "topolab.b4_45.public-marker.v1"
MODULE = "b4_45_public_marker"
TIMEOUT_SECONDS = 3
ALLOWED_PROBE_HASHES = frozenset(
    (
        "d36d447dbf7695aa137906cd4a959fb19e99795fa40ab056fd5cdf9803312ae8",
        "cdcb1a916684b849322d86701888f3728551c2d1502b323f6e4ddf196cb0e231",
        "93282c58074845b329ab221cf9158983eaa3a9f9701cc6a58ec5cdc7929025f6",
        "fb7f08c90f4813077a6764b43e0c521ecfef80e0dcbba6d0c119a3812f83b342",
    )
)
REQUEST_FIELDS = frozenset(
    (
        "version",
        "source_root",
        "expected_executable",
        "expected_cwd",
        "expected_source_revision",
        "expected_lock_sha256",
        "expected_pyproject_sha256",
        "expected_package_sha256",
        "probe_root",
        "expected_probe_origin",
        "expected_probe_sha256",
        "path_mode",
    )
)
FORBIDDEN_MODULES = ("topolab", "numpy", "scipy", "torch", "safetensors")


class PreflightStop(Exception):
    """A retained public preflight stop, without an alternate launch."""

    def __init__(self, status: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_exclusive(path: Path, value: dict[str, Any]) -> None:
    """Never replace an existing receipt; fsync before the next phase."""
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def read_bounded(path: Path, limit: int) -> bytes:
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise PreflightStop("STOP_SCHEMA", "public text exceeds its byte cap")
    return raw


def strict_json(raw: bytes) -> dict[str, Any]:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    def constant(value: str) -> Any:
        raise ValueError("nonfinite JSON constant: " + value)

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def validate_request(value: dict[str, Any], root: Path) -> None:
    if set(value) != REQUEST_FIELDS or any(type(v) is not str for v in value.values()):
        raise PreflightStop("STOP_SCHEMA", "closed request fields/types differ")
    if value["version"] != VERSION or value["source_root"] != str(root):
        raise PreflightStop("STOP_SCHEMA", "request version/source root differs")
    if value["path_mode"] not in ("source", "without_source", "shadow_probe"):
        raise PreflightStop("STOP_SCHEMA", "unsupported fixed path mode")
    for key in ("expected_executable", "expected_cwd", "probe_root", "expected_probe_origin"):
        if not Path(value[key]).is_absolute():
            raise PreflightStop("STOP_SCHEMA", "request paths must be absolute")
    for key in REQUEST_FIELDS:
        if key.endswith("sha256") and not re.fullmatch(r"[0-9a-f]{64}", value[key]):
            raise PreflightStop("STOP_SCHEMA", "invalid SHA256 spelling")
    if not re.fullmatch(r"[0-9a-f]{40}", value["expected_source_revision"]):
        raise PreflightStop("STOP_SCHEMA", "invalid source revision")
    if value["expected_probe_sha256"] not in ALLOWED_PROBE_HASHES:
        raise PreflightStop("STOP_SCHEMA", "probe is outside the four public texts")


def application_modules() -> list[str]:
    return sorted(n for n in sys.modules if n.split(".")[0] in FORBIDDEN_MODULES)


def child(request_path: Path, output: Path) -> int:
    root = Path(__file__).resolve().parents[2]
    context: dict[str, Any] = {
        "executable": sys.executable,
        "real_executable": str(Path(sys.executable).resolve()),
        "python": list(sys.version_info[:3]),
        "implementation": sys.implementation.name,
        "prefix": sys.prefix,
        "base_prefix": sys.base_prefix,
        "isolated": sys.flags.isolated,
        "cwd": str(Path.cwd()),
        "initial_sys_path": list(sys.path),
        "package_origin": None,
        "probe_origin": None,
        "probe_loaded_origin": None,
        "application_modules_before": application_modules(),
    }
    status, detail, started, completed = "STOP_SCHEMA", "", False, False
    failure_traceback: str | None = None
    try:
        value = strict_json(read_bounded(request_path, 32768))
        validate_request(value, root)
        if (
            sys.executable != value["expected_executable"]
            or sys.flags.isolated != 1
            or sys.implementation.name != "cpython"
            or sys.version_info[:2] != (3, 12)
        ):
            raise PreflightStop("STOP_INTERPRETER", "exact locked isolated interpreter differs")
        if str(Path.cwd()) != value["expected_cwd"]:
            raise PreflightStop("STOP_CWD", "declared cwd differs")
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
        context["source_revision"] = head
        if head != value["expected_source_revision"]:
            raise PreflightStop("STOP_SOURCE", "source HEAD differs")
        for name, key in (
            ("uv.lock", "expected_lock_sha256"),
            ("pyproject.toml", "expected_pyproject_sha256"),
        ):
            actual = digest(read_bounded(root / name, 1048576))
            context[name + "_sha256"] = actual
            if actual != value[key]:
                raise PreflightStop("STOP_LOCK", "locked environment source differs")
        source = str(root / "src")
        probe = value["probe_root"]
        remainder = [p for p in sys.path if str(Path(p).resolve()) != source and p != probe]
        sys.path[:] = [source] if value["path_mode"] != "without_source" else []
        sys.path += [probe, *remainder]
        context["sys_path"] = list(sys.path)
        package_spec = PathFinder.find_spec("topolab", sys.path)
        package_origin = package_spec.origin if package_spec else None
        context["package_origin"] = package_origin
        if package_origin != str(root / "src/topolab/__init__.py"):
            raise PreflightStop("STOP_PACKAGE_ORIGIN", "package resolution differs; no import")
        package_hash = digest(read_bounded(Path(package_origin), 1048576))
        context["package_sha256"] = package_hash
        if package_hash != value["expected_package_sha256"]:
            raise PreflightStop("STOP_PACKAGE_HASH", "package text hash differs; no import")
        spec = PathFinder.find_spec(MODULE, sys.path)
        context["probe_origin"] = spec.origin if spec else None
        if spec is None or spec.origin is None or spec.origin != value["expected_probe_origin"]:
            raise PreflightStop("STOP_PROBE_ORIGIN", "public probe resolution differs")
        raw = read_bounded(Path(spec.origin), 8192)
        context["probe_sha256"] = digest(raw)
        if digest(raw) != value["expected_probe_sha256"]:
            raise PreflightStop("STOP_PROBE_HASH", "public probe text changed")
        if application_modules():
            raise PreflightStop("STOP_APPLICATION_IMPORT", "application module already imported")
        write_exclusive(
            output / "started.json",
            {
                "version": VERSION,
                "phase": "BEFORE_CHECKED_PUBLIC_PROBE",
                "attempts": 1,
                "request_sha256": digest(request_path.read_bytes()),
                "probe_sha256": digest(raw),
                "probe_origin": spec.origin,
            },
        )
        started = True
        module = types.ModuleType(MODULE)
        module.__file__, module.__spec__ = spec.origin, spec
        # Execute precisely the checked bytes, never a cached or re-read loader payload.
        exec(compile(raw, spec.origin, "exec"), module.__dict__)
        completed = True
        context["probe_loaded_origin"] = module.__file__
        if module.__dict__.get("MARKER") != MARKER:
            raise PreflightStop("STOP_PROBE_MARKER", "public marker differs")
        if application_modules():
            raise PreflightStop("STOP_APPLICATION_IMPORT", "application module imported")
        status, detail = "PASS_PUBLIC_PREFLIGHT", "fixed public marker and context match"
    except PreflightStop as exc:
        status, detail = exc.status, str(exc)
    except (OSError, ValueError, RuntimeError, SyntaxError) as exc:
        status = "STOP_IMPORT" if started else "STOP_SCHEMA"
        detail = type(exc).__name__ + ": " + str(exc)
        failure_traceback = traceback.format_exc()
    context["application_modules_after"] = application_modules()
    write_exclusive(
        output / "probe_result.json",
        {
            "version": VERSION,
            "status": status,
            "detail": detail,
            "context": context,
            "attempts": int(started),
            "completed": int(completed),
            "traceback": failure_traceback,
        },
    )
    return 0 if status == "PASS_PUBLIC_PREFLIGHT" else 1


def run_preflight(request_path: Path, output: Path) -> dict[str, Any]:
    """Write pending before child launch and terminal after its observed exit."""
    root = Path(__file__).resolve().parents[2]
    if output.resolve().is_relative_to(root):
        raise ValueError("public receipts must be outside the source repository")
    output.mkdir(mode=0o700)  # Refuse existing directories, files and symlinks.
    request_hash: str | None = None
    request_error: str | None = None
    try:
        request_hash = digest(read_bounded(request_path, 32768))
    except (OSError, PreflightStop) as exc:
        request_error = type(exc).__name__ + ": " + str(exc)
    write_exclusive(
        output / "pending.json",
        {
            "version": VERSION,
            "phase": "PENDING_BEFORE_CHILD_LAUNCH",
            "request_path": str(request_path),
            "request_sha256": request_hash,
            "request_error": request_error,
        },
    )
    code: int | None = None
    timeout = False
    launch_error: str | None = None
    with (output / "stdout.log").open("xb") as stdout, (output / "stderr.log").open("xb") as stderr:
        if request_error is None:
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-I",
                        str(Path(__file__).resolve()),
                        "--child",
                        str(request_path),
                        str(output),
                    ],
                    cwd=root,
                    stdout=stdout,
                    stderr=stderr,
                    timeout=TIMEOUT_SECONDS,
                )
                code = result.returncode
            except subprocess.TimeoutExpired:
                timeout = True
            except OSError as exc:
                launch_error = type(exc).__name__ + ": " + str(exc)
        stdout.flush()
        stderr.flush()
        os.fsync(stdout.fileno())
        os.fsync(stderr.fileno())
    probe_result: dict[str, Any] | None = None
    parse_error: str | None = None
    if (output / "probe_result.json").exists():
        try:
            probe_result = strict_json(read_bounded(output / "probe_result.json", 32768))
            if (
                set(probe_result)
                != {
                    "version",
                    "status",
                    "detail",
                    "context",
                    "attempts",
                    "completed",
                    "traceback",
                }
                or probe_result["version"] != VERSION
            ):
                raise ValueError("closed child result schema differs")
        except (OSError, ValueError, PreflightStop) as exc:
            parse_error = type(exc).__name__ + ": " + str(exc)
            probe_result = None
    if timeout:
        status = "FAIL_TIMEOUT"
    elif request_error:
        status = "STOP_REQUEST"
    elif launch_error:
        status = "FAIL_CHILD_LAUNCH"
    elif parse_error:
        status = "FAIL_RESULT_SCHEMA"
    elif probe_result and code == (0 if probe_result["status"] == "PASS_PUBLIC_PREFLIGHT" else 1):
        status = str(probe_result["status"])
    else:
        status = "FAIL_CHILD_EXIT"
    links = {
        n: digest((output / n).read_bytes()) if (output / n).exists() else None
        for n in ("pending.json", "started.json", "probe_result.json", "stdout.log", "stderr.log")
    }
    terminal = {
        "version": VERSION,
        "phase": "TERMINAL_AFTER_OBSERVED_EXIT",
        "status": status,
        "request_sha256": request_hash,
        "child_exit_code": code,
        "timeout": timeout,
        "launch_error": launch_error,
        "parse_error": parse_error,
        "sha256": links,
        "attempts": probe_result["attempts"]
        if probe_result
        else (1 if links["started.json"] else "UNKNOWN_NOT_WRITTEN"),
        "completed": probe_result["completed"] if probe_result else "UNKNOWN_NOT_WRITTEN",
        "result_state": "WRITTEN" if probe_result else "NOT_WRITTEN",
    }
    write_exclusive(output / "terminal.json", terminal)
    return terminal


def main() -> int:
    if len(sys.argv) == 4 and sys.argv[1] == "--child":
        return child(Path(sys.argv[2]), Path(sys.argv[3]))
    if len(sys.argv) != 3:
        raise ValueError("usage: launch_preflight.py REQUEST_JSON FRESH_EXTERNAL_OUTPUT")
    try:
        result = run_preflight(Path(sys.argv[1]), Path(sys.argv[2]))
    except FileExistsError:
        print(json.dumps({"status": "REFUSED_EXISTING_OUTPUT"}))
        return 2
    print(json.dumps({"status": result["status"]}))
    return 0 if result["status"] == "PASS_PUBLIC_PREFLIGHT" else 1


if __name__ == "__main__":
    sys.exit(main())
