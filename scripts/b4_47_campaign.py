"""B4.47 actual standalone candidate bootstrap and immutable public campaign.

This file imports no candidate at startup. Parent pending precedes child startup;
child started precedes checked candidate import and all registered case bytes.
"""

import hashlib
import importlib.machinery
import importlib.util
import json
import os
import re
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

VERSION = "topolab.b4_47.fresh-public-arithmetic-campaign.v1"
CONTRACT = "docs/planning/b4_47_public_arithmetic_campaign_contract.json"
PROTOCOL = "docs/planning/b4_47_public_arithmetic_campaign_protocol.md"
CANDIDATE = "src/topolab/public_campaign_arithmetic.py"
ORACLE = "scripts/b4_47_arithmetic_oracle.py"
PROGRAMS = (CANDIDATE, ORACLE, "scripts/b4_47_campaign.py", "scripts/b4_47_campaign_audit.py")
FORBIDDEN = ("topolab", "numpy", "scipy", "torch", "safetensors")
RELEASE_FIELDS = {
    "version",
    "execution_kind",
    "source_root",
    "executable",
    "executable_sha256",
    "python_version",
    "isolated_sys_path",
    "head",
    "tree",
    "lock_sha256",
    "pyproject_sha256",
    "contract_sha256",
    "protocol_sha256",
    "program_sha256",
    "stdlib_sha256",
    "source_manifest_sha256",
    "external_root",
    "ci",
}
REQUEST_FIELDS = {"version", "mode", "release", "expectations"}
EXPECTATION_FIELDS = {"executable", "cwd", "head", "lock_sha256", "origin", "candidate_sha256"}
MODES = (
    "actual_candidate_import",
    "wrong_interpreter",
    "wrong_cwd",
    "wrong_lock",
    "wrong_source",
    "wrong_origin",
    "wrong_hash",
    "dependency_import_failure",
    "exit7_after_import",
    "timeout_after_import",
    "producer",
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def executable_hash(path):
    """Hash the complete declared interpreter, without a metadata-text ceiling."""
    path = path.resolve()
    if not path.is_file():
        raise ValueError("declared interpreter regular file required")
    state = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(262144), b""):
            state.update(block)
    return state.hexdigest()


def encode(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def save(path, value):
    raw = value if isinstance(value, bytes) else encode(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return sha(raw)


def strict(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate JSON field")
            value[key] = item
        return value

    def nonfinite(text):
        raise ValueError("nonfinite JSON: " + text)

    if type(raw) is not bytes or len(raw) > 1048576:
        raise ValueError("bounded metadata bytes required")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def read(path, limit=1048576):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("listed regular bounded file required: " + str(path))
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("input exceeds bound")
    return raw


def checked(root, relative, digest, limit=1048576):
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError("path escape")
    raw = read(path, limit)
    if sha(raw) != digest:
        raise ValueError("changed bound bytes: " + relative)
    return raw


def release_schema(value):
    if type(value) is not dict or set(value) != RELEASE_FIELDS or value["version"] != VERSION:
        raise ValueError("closed release schema")
    if value["execution_kind"] not in ("FORMAL_B4_47", "REGISTERED_REGRESSION_B4_47"):
        raise ValueError("closed execution kind")
    for key in RELEASE_FIELDS - {"ci", "program_sha256", "stdlib_sha256", "isolated_sys_path"}:
        if type(value[key]) is not str:
            raise ValueError("release literal type")
    if (
        type(value["program_sha256"]) is not dict
        or set(value["program_sha256"]) != set(PROGRAMS)
        or type(value["stdlib_sha256"]) is not dict
        or type(value["isolated_sys_path"]) is not list
        or any(type(x) is not str for x in value["isolated_sys_path"])
    ):
        raise ValueError("closed source/runtime maps")
    if type(value["ci"]) is not list:
        raise ValueError("closed CI list")
    for key in ("head", "tree"):
        if not re.fullmatch(r"[0-9a-f]{40}", value[key]):
            raise ValueError("Git identity schema")
    hash_keys = {
        "lock_sha256",
        "pyproject_sha256",
        "contract_sha256",
        "protocol_sha256",
        "source_manifest_sha256",
        "executable_sha256",
    }
    if any(not re.fullmatch(r"[0-9a-f]{64}", value[k]) for k in hash_keys):
        raise ValueError("hash schema")
    if any(
        type(d) is not str or not re.fullmatch(r"[0-9a-f]{64}", d)
        for d in value["program_sha256"].values()
    ):
        raise ValueError("program hash schema")
    if set(value["stdlib_sha256"]) != {
        "math",
        "fractions",
        "struct",
        "dataclasses",
        "re",
        "json",
        "hashlib",
        "types",
    }:
        raise ValueError("closed direct standard-library dependencies")
    for row in value["stdlib_sha256"].values():
        if (
            type(row) is not dict
            or set(row) != {"origin", "sha256"}
            or type(row["origin"]) is not str
            or type(row["sha256"]) is not str
            or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
        ):
            raise ValueError("closed dependency origin/hash schema")
    for row in value["ci"]:
        if (
            type(row) is not dict
            or set(row) != {"scope", "name", "head_sha", "conclusion", "app_id", "id"}
            or type(row["app_id"]) is not int
            or type(row["id"]) is not int
            or row["scope"] not in ("pr", "main")
        ):
            raise ValueError("closed CI row schema")
    if value["execution_kind"] == "FORMAL_B4_47":
        if value["python_version"] != "3.12.10" or len(value["ci"]) != 6:
            raise ValueError("formal locked CPython/CI prerequisite")
        for group in ("pr", "main"):
            rows = [r for r in value["ci"] if r["scope"] == group]
            if (
                len(rows) != 3
                or {r["name"] for r in rows} != {"quality", "frontend", "clean-linux-smoke"}
                or any(r["conclusion"] != "success" or r["app_id"] != 15368 for r in rows)
                or any(r["head_sha"] != value["head"] for r in rows if group == "main")
            ):
                raise ValueError("all exact-head and main CI required")
            if len({r["head_sha"] for r in rows}) != 1:
                raise ValueError("CI must refer to one exact head")
    return value


class Journal:
    def __init__(self, root):
        self.root = root
        self.index = 0
        self.previous = None
        self.stack = []
        self.attempted = self.completed = self.failed = 0

    def emit(self, phase, event):
        if phase == "before":
            self.attempted += 1
            self.stack.append(event["stage"])
        elif phase == "after":
            if not self.stack or self.stack[-1] != event["stage"]:
                raise ValueError("operation phase order changed")
            self.stack.pop()
            self.completed += 1
        elif phase == "failure":
            self.failed += len(self.stack)
            self.stack.clear()
        else:
            raise ValueError("unknown operation phase")
        self.previous = save(
            self.root / f"{self.index:06}.json",
            {
                "index": self.index,
                "previous_sha256": self.previous,
                "event": event,
                "attempted": self.attempted,
                "completed": self.completed,
                "failed": self.failed,
                "pending": len(self.stack),
            },
        )
        self.index += 1

    def counts(self):
        return {
            "attempted": self.attempted,
            "completed": self.completed,
            "failed": self.failed,
            "pending": len(self.stack),
            "events": self.index,
            "last_sha256": self.previous,
        }


def candidate_load(root, release, expectations, output, block_dependency=False):
    directory = root / "src/topolab"
    spec = importlib.machinery.PathFinder.find_spec("public_campaign_arithmetic", [str(directory)])
    origin = None if spec is None else spec.origin
    if origin is None or str(Path(origin).resolve()) != expectations["origin"]:
        return None, "STOP_ORIGIN"
    raw = read(Path(origin))
    if sha(raw) != expectations["candidate_sha256"]:
        return None, "STOP_HASH"
    save(output / "candidate_source.py", raw)
    save(
        output / "candidate_import_before.json",
        {
            "attempted": 1,
            "completed": 0,
            "origin": origin,
            "sha256": sha(raw),
            "case_input_reads": 0,
        },
    )
    if block_dependency:
        if "fractions" in sys.modules:
            raise ValueError("dependency-control prerequisite changed")

        class DenyFractions:
            def find_spec(self, fullname, path=None, target=None):
                if fullname == "fractions":
                    raise ModuleNotFoundError("registered fresh fractions dependency control")
                return None

        sys.meta_path.insert(0, DenyFractions())
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        exec(compile(raw.decode("utf-8"), origin, "exec"), module.__dict__)
    except Exception:
        save(output / "import_exception.txt", traceback.format_exc().encode())
        return None, "STOP_IMPORT"
    if any(name.split(".")[0] in FORBIDDEN for name in sys.modules):
        raise ValueError("forbidden application dependency imported")
    observed = {}
    for name, expected in release["stdlib_sha256"].items():
        dependency = sys.modules.get(name)
        dependency_origin = getattr(getattr(dependency, "__spec__", None), "origin", None)
        if dependency_origin is None:
            raise ValueError("declared actual dependency origin missing: " + name)
        if dependency_origin in ("built-in", "frozen"):
            # Portable software regressions bind embedded modules to this interpreter image.
            # The frozen formal Mac environment still requires actual dependency files.
            if release["execution_kind"] != "REGISTERED_REGRESSION_B4_47":
                raise ValueError("formal dependency file origin required: " + name)
            actual_hash = release["executable_sha256"]
        else:
            actual_hash = sha(read(Path(dependency_origin), 8388608))
        if actual_hash != expected["sha256"] or dependency_origin != expected["origin"]:
            raise ValueError("changed actual dependency bytes: " + name)
        observed[name] = {"origin": dependency_origin, "sha256": actual_hash}
    if not callable(getattr(module, "enclose_assembled_residual", None)):
        raise ValueError("actual candidate API absent")
    if read(Path(origin)) != raw:
        raise ValueError("source identity race")
    save(
        output / "candidate_import_complete.json",
        {
            "attempted": 1,
            "completed": 1,
            "candidate_origin": origin,
            "candidate_sha256": sha(raw),
            "dependencies": observed,
            "module": spec.name,
            "case_input_reads": 0,
            "forbidden_imports": [],
        },
    )
    return module, "PASS_IMPORT_ONLY"


def child(request_path, output):
    save(
        output / "started.json",
        {
            "pid": os.getpid(),
            "parent_pid": os.getppid(),
            "sys_executable": sys.executable,
            "python_version": ".".join(map(str, sys.version_info[:3])),
            "isolated": sys.flags.isolated,
            "cwd": str(Path.cwd()),
            "sys_path": sys.path,
            "candidate_imported": False,
            "case_input_reads": 0,
            "operations_attempted": 0,
        },
    )
    try:
        request = strict(read(request_path))
        if type(request) is not dict or set(request) != REQUEST_FIELDS:
            raise ValueError("closed request schema")
        if request["version"] != VERSION or request["mode"] not in MODES:
            raise ValueError("closed mode/version")
        release = release_schema(request["release"])
        expectations = request["expectations"]
        if (
            type(expectations) is not dict
            or set(expectations) != EXPECTATION_FIELDS
            or any(type(x) is not str for x in expectations.values())
        ):
            raise ValueError("closed expectation schema")
        root = Path(release["source_root"])
        status = "PASS_IMPORT_ONLY"
        if (
            sys.executable != expectations["executable"]
            or sys.flags.isolated != 1
            or ".".join(map(str, sys.version_info[:3])) != release["python_version"]
            or sys.path != release["isolated_sys_path"]
            or executable_hash(Path(sys.executable)) != release["executable_sha256"]
        ):
            status = "STOP_INTERPRETER"
        elif str(Path.cwd()) != expectations["cwd"]:
            status = "STOP_CWD"
        elif sha(read(root / "uv.lock")) != expectations["lock_sha256"]:
            status = "STOP_LOCK"
        else:
            head = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True
            ).strip()
            tree = subprocess.check_output(
                ["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True
            ).strip()
            dirty = subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root
            )
            if (
                head != expectations["head"]
                or tree != release["tree"]
                or (release["execution_kind"] == "FORMAL_B4_47" and dirty)
            ):
                status = "STOP_SOURCE"
        if status != "PASS_IMPORT_ONLY":
            save(
                output / "result.json",
                {
                    "status": status,
                    "case_input_reads": 0,
                    "candidate_imports_attempted": 0,
                    "candidate_imports_completed": 0,
                },
            )
            return 0
        checked(root, CONTRACT, release["contract_sha256"])
        checked(root, PROTOCOL, release["protocol_sha256"])
        checked(root, "pyproject.toml", release["pyproject_sha256"])
        checked(
            root,
            "scripts/b4_47_campaign.py",
            release["program_sha256"]["scripts/b4_47_campaign.py"],
        )
        candidate, status = candidate_load(
            root, release, expectations, output, request["mode"] == "dependency_import_failure"
        )
        if status != "PASS_IMPORT_ONLY":
            save(
                output / "result.json",
                {
                    "status": status,
                    "case_input_reads": 0,
                    "candidate_imports_attempted": int(status == "STOP_IMPORT"),
                    "candidate_imports_completed": 0,
                },
            )
            return 0
        if request["mode"] == "exit7_after_import":
            os._exit(7)
        if request["mode"] == "timeout_after_import":
            time.sleep(10)
        if request["mode"] != "producer":
            save(
                output / "result.json",
                {
                    "status": "PASS_IMPORT_ONLY",
                    "case_input_reads": 0,
                    "candidate_imports_attempted": 1,
                    "candidate_imports_completed": 1,
                },
            )
            return 0
        contract = strict(checked(root, CONTRACT, release["contract_sha256"]))
        rows = []
        for index, entry in enumerate(contract["catalog"]):
            case_root = output / "cases" / entry["id"]
            save(
                case_root / "before.json",
                {
                    "index": index,
                    "id": entry["id"],
                    "input_path": entry["path"],
                    "input_sha256": entry["sha256"],
                    "cases_attempted": index + 1,
                    "cases_completed": index,
                    "cases_pending": 1,
                    "operations_attempted": 0,
                    "operations_completed": 0,
                },
            )
            binding = {
                "version": VERSION,
                "role": "fresh-public-arithmetic-software",
                "fixture_id": entry["id"],
                "sha256": entry["sha256"],
                "source_main": contract["starting_main"],
                "free_space": "b4-47-public-space:" + entry["id"],
                "path": entry["path"],
            }

            def reader(entry=entry, case_root=case_root):
                save(case_root / "input_before.json", {"path": entry["path"], "read_attempted": 1})
                raw = checked(root, entry["path"], entry["sha256"], 32768)
                save(case_root / "input_snapshot.json", raw)
                if checked(root, entry["path"], entry["sha256"], 32768) != raw:
                    raise ValueError("case input race")
                save(
                    case_root / "input_after.json",
                    {"explicit_case_file_reads": 2, "bytes": len(raw), "sha256": sha(raw)},
                )
                return raw

            fixture = candidate.read_public_fixture(binding, reader)
            journal = Journal(case_root / "operations")
            result = candidate.enclose_assembled_residual(fixture, journal.emit)
            save(case_root / "result.json", result)
            save(
                case_root / "after.json",
                {
                    "id": entry["id"],
                    "status": result["status"],
                    "result_sha256": sha(read(case_root / "result.json")),
                    "operations": journal.counts(),
                    "cases_attempted": index + 1,
                    "cases_completed": index + 1,
                    "cases_pending": 0,
                },
            )
            rows.append(
                {
                    "id": entry["id"],
                    "status": result["status"],
                    "result_sha256": sha(read(case_root / "result.json")),
                    "operations": journal.counts(),
                }
            )
            if result["status"] != entry["expected_status"] or journal.counts()["pending"]:
                raise ValueError("unexpected formal case result; quota consumed")
        save(
            output / "result.json",
            {
                "status": "PASS_PUBLIC_ARITHMETIC_CASES",
                "cases": rows,
                "cases_attempted": 10,
                "cases_completed": 10,
                "cases_pending": 0,
                "explicit_case_file_reads": 20,
                "Git_internal_content_read_counts": "UNKNOWN_NOT_INSTRUMENTED",
                "candidate_imports_attempted": 1,
                "candidate_imports_completed": 1,
            },
        )
        return 0
    except Exception:
        save(output / "child_failure.txt", traceback.format_exc().encode())
        save(
            output / "result.json",
            {
                "status": "FAIL_CHILD_EXCEPTION",
                "complete_counts": (
                    "UNKNOWN_NOT_WRITTEN; inspect immutable before/operation prefixes"
                ),
            },
        )
        return 1


def make_request(release, mode):
    release_schema(release)
    root = Path(release["source_root"])
    expectations = {
        "executable": release["executable"],
        "cwd": str(root),
        "head": release["head"],
        "lock_sha256": release["lock_sha256"],
        "origin": str(root / CANDIDATE),
        "candidate_sha256": release["program_sha256"][CANDIDATE],
    }
    replacements = {
        "wrong_interpreter": ("executable", "/unregistered/python"),
        "wrong_cwd": ("cwd", str(root / "unregistered-cwd")),
        "wrong_lock": ("lock_sha256", "0" * 64),
        "wrong_source": ("head", "0" * 40),
        "wrong_origin": ("origin", str(root / "unregistered-origin.py")),
        "wrong_hash": ("candidate_sha256", "0" * 64),
    }
    if mode in replacements:
        key, value = replacements[mode]
        expectations[key] = value
    return {"version": VERSION, "mode": mode, "release": release, "expectations": expectations}


def run_one(request_path, output, native=True):
    # First operation: exclusive ownership; no request/source bytes on refusal.
    output.mkdir(parents=True)
    raw = read(request_path)
    save(output / "request_snapshot.json", raw)
    request = strict(raw)
    release = release_schema(request["release"])
    if not output.resolve().is_relative_to(Path(release["external_root"]).resolve()):
        raise ValueError("output outside registered fresh root")
    save(
        output / "pending.json",
        {
            "version": VERSION,
            "request_sha256": sha(raw),
            "source_head": release["head"],
            "source_tree": release["tree"],
            "program_sha256": release["program_sha256"],
            "contract_sha256": release["contract_sha256"],
            "candidate_imported": False,
            "case_input_reads": 0,
            "operations_attempted": 0,
        },
    )
    argv = [
        release["executable"],
        "-I",
        str(Path(release["source_root"]) / "scripts/b4_47_campaign.py"),
        "child",
        str(output / "request_snapshot.json"),
        str(output),
    ]
    command = ["/usr/bin/time", "-l", "-o", str(output / "native.time"), *argv] if native else argv
    timed_out = False
    started_clock = time.perf_counter()
    with (output / "stdout.log").open("xb") as stdout, (output / "stderr.log").open("xb") as stderr:
        process = subprocess.Popen(
            command, cwd=release["source_root"], stdout=stdout, stderr=stderr
        )
        try:
            process.wait(timeout=3 if request["mode"] == "timeout_after_import" else 60)
        except subprocess.TimeoutExpired:
            timed_out = True
            started_path = output / "started.json"
            if not started_path.is_file():
                process.kill()
            else:
                started = strict(read(started_path))
                if native and started["parent_pid"] != process.pid:
                    process.kill()
                    raise ValueError("timeout child ownership unknown") from None
                os.kill(started["pid"], signal.SIGKILL)
            process.wait(timeout=15)
    status = "FAIL_TIMEOUT" if timed_out else "FAIL_CHILD_EXIT" if process.returncode else None
    if status is None:
        status = strict(read(output / "result.json"))["status"]
    names = (
        "request_snapshot.json",
        "pending.json",
        "started.json",
        "candidate_source.py",
        "candidate_import_before.json",
        "candidate_import_complete.json",
        "result.json",
        "import_exception.txt",
        "child_failure.txt",
        "stdout.log",
        "stderr.log",
        "native.time",
    )
    hashes = {
        n: sha(read(output / n, 8388608)) if (output / n).is_file() else "UNKNOWN_NOT_WRITTEN"
        for n in names
    }
    terminal = {
        "status": status,
        "observed_exit_code": process.returncode,
        "timed_out": timed_out,
        "through_exit": True,
        "observed_wall_seconds": time.perf_counter() - started_clock,
        "hashes": hashes,
        "missing_completion": "UNKNOWN_NOT_WRITTEN" if status.startswith("FAIL_") else None,
    }
    save(output / "terminal.json", terminal)
    return terminal


def main():
    role, *args = sys.argv[1:]
    if role == "child":
        return child(Path(args[0]), Path(args[1]))
    if role not in ("controls", "producer") or len(args) != 2:
        raise ValueError("closed formal entrypoint")
    release_path, output = map(Path, args)
    output.mkdir(parents=True)
    raw = read(release_path)
    release = release_schema(strict(raw))
    if release["execution_kind"] != "FORMAL_B4_47":
        raise ValueError("formal CLI requires released source")
    save(output / "release_snapshot.json", raw)
    save(
        output / "pending.json",
        {
            "role": role,
            "source_head": release["head"],
            "release_sha256": sha(raw),
            "candidate_imported": False,
            "case_input_reads": 0,
        },
    )
    contract = strict(checked(Path(release["source_root"]), CONTRACT, release["contract_sha256"]))
    entries = contract["launch_controls"] if role == "controls" else [{"id": "producer"}]
    results = []
    for entry in entries:
        mode = entry["id"]
        if mode == "existing_output":
            existing = output / "actual_candidate_import"
            originals = {
                str(p.relative_to(existing)): sha(read(p))
                for p in existing.rglob("*")
                if p.is_file()
            }
            try:
                run_one(output / "NONEXISTENT_REQUEST_MUST_NOT_BE_READ", existing)
            except FileExistsError:
                after = {
                    str(p.relative_to(existing)): sha(read(p))
                    for p in existing.rglob("*")
                    if p.is_file()
                }
                if originals != after:
                    raise ValueError("refused output changed") from None
                save(
                    output / "existing_output_refusal.json",
                    {
                        "status": "REFUSED_EXISTING_OUTPUT",
                        "unchanged": True,
                        "original_sha256": originals,
                        "after_sha256": after,
                        "request_reads": 0,
                        "new_child_launches": 0,
                    },
                )
                result = {"status": "REFUSED_EXISTING_OUTPUT"}
            else:
                raise ValueError("existing output not refused")
        else:
            request = output / "requests" / (mode + ".json")
            save(request, make_request(release, mode))
            result = run_one(request, output / mode)
        results.append({"id": mode, "status": result["status"]})
        if role == "controls" and result["status"] != entry["expected_status"]:
            raise ValueError("unexpected control outcome; no formal retry")
    passed = role == "controls" or results[0]["status"] == "PASS_PUBLIC_ARITHMETIC_CASES"
    save(
        output / "result.json",
        {
            "passed": passed,
            "role": role,
            "cases": results,
            "formal_retry": False,
            "candidate_is_actual_arithmetic_source": True,
        },
    )
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
