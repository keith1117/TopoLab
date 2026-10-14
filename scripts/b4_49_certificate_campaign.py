"""B4.49 immutable parent/child launch; actual candidate import after pending."""

import hashlib
import importlib.machinery
import importlib.util
import json
import os
import signal
import subprocess
import sys
import time
import traceback
from pathlib import Path

VERSION = "topolab.b4_49.public-combined-diagnostic-certificate.v1"
CONTRACT = "docs/planning/b4_49_public_combined_diagnostic_certificate_contract.json"
PROTOCOL = CONTRACT.replace("_contract.json", "_protocol.md")
CANDIDATE = "src/topolab/combined_certificate.py"
PROGRAMS = (
    CANDIDATE,
    "scripts/b4_49_combined_oracle.py",
    "scripts/b4_49_certificate_campaign.py",
    "scripts/b4_49_certificate_audit.py",
)
DEPS = (
    "hashlib",
    "json",
    "math",
    "re",
    "struct",
    "collections.abc",
    "fractions",
    "typing",
    "types",
)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    raw = (
        value
        if type(value) is bytes
        else (
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
        ).encode()
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return sha(raw)


def read(path, maximum=1048576):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > maximum:
        raise ValueError("listed regular bounded input required")
    raw = path.read_bytes()
    if len(raw) > maximum:
        raise ValueError("input size changed")
    return raw


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate metadata field")
            result[key] = value
        return result

    def reject(text):
        raise ValueError("nonfinite metadata " + text)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)


def checked(root, relative, digest, maximum=1048576):
    path = root / relative
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("path escape")
    raw = read(path, maximum)
    if sha(raw) != digest:
        raise ValueError("changed checked source/input: " + relative)
    return raw


def runtime():
    dependencies = {}
    for name in DEPS:
        spec = importlib.util.find_spec(name)
        if spec is None or spec.origin is None:
            raise ValueError("declared standard-library origin")
        dependencies[name] = {"origin": spec.origin, "sha256": sha(Path(spec.origin).read_bytes())}
    return {
        "executable": sys.executable,
        "executable_sha256": sha(Path(sys.executable).resolve().read_bytes()),
        "python_version": sys.version,
        "sys_path": sys.path,
        "stdlib": dependencies,
    }


def make_release(root, external, kind, ci=None):
    root, external = Path(root).resolve(), Path(external).resolve()

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=root).decode().split("\0")[:-1]
    # Administrative freeze of versioned public source only; no old external payload read.
    manifest = {n: sha((root / n).read_bytes()) for n in paths}
    return {
        "version": VERSION,
        "kind": kind,
        "root": str(root),
        "external_root": str(external),
        "head": git("rev-parse", "HEAD"),
        "tree": git("rev-parse", "HEAD^{tree}"),
        "runtime": runtime(),
        "source_manifest": manifest,
        "source_manifest_sha256": sha((json.dumps(manifest, sort_keys=True) + "\n").encode()),
        "program_sha256": {n: sha((root / n).read_bytes()) for n in PROGRAMS},
        "contract_sha256": sha((root / CONTRACT).read_bytes()),
        "protocol_sha256": sha((root / PROTOCOL).read_bytes()),
        "lock_sha256": sha((root / "uv.lock").read_bytes()),
        "ci": ci or [],
    }


def verify_release(release):
    if (
        type(release) is not dict
        or set(release)
        != {
            "version",
            "kind",
            "root",
            "external_root",
            "head",
            "tree",
            "runtime",
            "source_manifest",
            "source_manifest_sha256",
            "program_sha256",
            "contract_sha256",
            "protocol_sha256",
            "lock_sha256",
            "ci",
        }
        or release["version"] != VERSION
    ):
        raise ValueError("closed release schema")
    if release["kind"] not in ("FORMAL_B4_49", "REGISTERED_REGRESSION_B4_49"):
        raise ValueError("closed execution kind")
    root = Path(release["root"])
    if Path.cwd().resolve() != root or runtime() != release["runtime"]:
        raise ValueError("exact runtime/cwd mismatch")
    if not sys.flags.isolated or sys.version_info[:2] != (3, 12):
        raise ValueError("locked isolated CPython3.12.10 required")
    if release["kind"] == "FORMAL_B4_49" and sys.version_info[:3] != (3, 12, 10):
        raise ValueError("formal CPython3.12.10 required")
    if set(release["program_sha256"]) != set(PROGRAMS):
        raise ValueError("closed program set")
    for path, digest in release["program_sha256"].items():
        checked(root, path, digest)
    checked(root, "uv.lock", release["lock_sha256"])
    checked(root, CONTRACT, release["contract_sha256"])
    checked(root, PROTOCOL, release["protocol_sha256"])
    encoded = (json.dumps(release["source_manifest"], sort_keys=True) + "\n").encode()
    if sha(encoded) != release["source_manifest_sha256"]:
        raise ValueError("source manifest mismatch")
    if release["kind"] == "FORMAL_B4_49":

        def git(*args):
            return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

        if (
            git("rev-parse", "HEAD") != release["head"]
            or git("rev-parse", "HEAD^{tree}") != release["tree"]
        ):
            raise ValueError("changed released revision")
        if git("status", "--porcelain", "--untracked-files=all"):
            raise ValueError("formal source must be clean")
        for scope in ("pr", "main"):
            rows = [x for x in release["ci"] if x["scope"] == scope]
            if (
                {x["name"] for x in rows} != {"quality", "frontend", "clean-linux-smoke"}
                or len(rows) != 3
                or any(x["conclusion"] != "success" for x in rows)
                or (scope == "main" and any(x["head_sha"] != release["head"] for x in rows))
            ):
                raise ValueError("all exact-source PR/main CI required")
    if any(x in sys.modules for x in ("topolab", "numpy", "scipy", "torch", "safetensors")):
        raise ValueError("forbidden eager/scientific import")
    return root


class Journal:
    def __init__(self, root):
        self.root = root
        self.index = 0
        self.previous = None
        self.pending = []
        self.attempted = self.completed = 0

    def event(self, phase, data):
        if phase == "before":
            self.attempted += 1
            self.pending.append(data["stage"])
        elif phase == "after":
            if not self.pending or self.pending.pop() != data["stage"]:
                raise ValueError("operation phase mismatch")
            self.completed += 1
        else:
            raise ValueError("closed operation phase")
        self.previous = write(
            self.root / f"{self.index:06}.json",
            {
                "index": self.index,
                "previous_sha256": self.previous,
                "phase": phase,
                "event": data,
                "attempted": self.attempted,
                "completed": self.completed,
                "pending": len(self.pending),
            },
        )
        self.index += 1

    def counts(self):
        return {
            "attempted": self.attempted,
            "completed": self.completed,
            "pending": len(self.pending),
            "events": self.index,
            "last_sha256": self.previous,
        }


def child(request_path, output):
    write(
        output / "started.json",
        {
            "pid": os.getpid(),
            "parent_pid": os.getppid(),
            "executable": sys.executable,
            "cwd": str(Path.cwd()),
            "sys_path": sys.path,
            "before_candidate_import": True,
            "case_reads": 0,
        },
    )
    try:
        request = strict(read(request_path))
        if (
            set(request) != {"version", "role", "release"}
            or request["version"] != VERSION
            or request["role"] != "primary"
        ):
            raise ValueError("closed request/role")
        release = request["release"]
        root = verify_release(release)
        raw = checked(root, CANDIDATE, release["program_sha256"][CANDIDATE])
        write(output / "candidate_source.py", raw)
        spec = importlib.machinery.PathFinder.find_spec(
            "combined_certificate", [str((root / CANDIDATE).parent)]
        )
        if spec is None or spec.origin != str(root / CANDIDATE):
            raise ValueError("actual candidate origin mismatch")
        write(
            output / "import_before.json",
            {"origin": spec.origin, "sha256": sha(raw), "actual_dependencies": DEPS},
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        exec(compile(raw, spec.origin, "exec"), module.__dict__)
        if module.__spec__.origin != spec.origin or runtime() != release["runtime"]:
            raise ValueError("changed actual import/dependency origin")
        write(
            output / "import_complete.json",
            {
                "origin": module.__file__,
                "sha256": sha(raw),
                "stdlib": release["runtime"]["stdlib"],
                "candidate_imported": True,
            },
        )
        contract = strict(checked(root, CONTRACT, release["contract_sha256"]))
        results = []
        for entry in contract["catalog"]:
            case_root = output / "cases" / entry["id"]
            write(case_root / "before_input.json", entry)
            grant = {
                "id": entry["id"],
                "sha256": entry["sha256"],
                "role": module.ROLE,
                "version": VERSION,
                "source_main": contract["starting_main"],
                "space": "b4-49-public-space:" + entry["id"],
            }

            def provide(row=entry, destination=case_root):
                case_raw = checked(root, row["path"], row["sha256"], 32768)
                write(destination / "input.json", case_raw)
                return case_raw

            fixture = module.load_registered(entry["id"], provide, grant)
            journal = Journal(case_root / "operations")
            write(
                case_root / "before_arithmetic.json", {"id": entry["id"], "sha256": entry["sha256"]}
            )
            result = module.evaluate(fixture, journal.event)
            write(case_root / "result.json", result)
            write(case_root / "operation_counts.json", journal.counts())
            results.append(
                {
                    "id": entry["id"],
                    "status": result["status"],
                    "result_sha256": sha(read(case_root / "result.json")),
                    "operation_counts": journal.counts(),
                }
            )
            if result["status"] != entry["expected_status"] or journal.pending:
                raise ValueError("unexpected case outcome; frozen formal quota consumed")
        write(
            output / "result.json",
            {
                "status": "PASS_PUBLIC_COMBINED_PRODUCER_ONLY",
                "cases": results,
                "cases_attempted": 12,
                "cases_completed": 12,
                "cases_pending": 0,
                "candidate_imports_attempted": 1,
                "candidate_imports_completed": 1,
                "explicit_fixture_file_reads": 12,
                "git_internal_reads": "UNKNOWN_NOT_INSTRUMENTED",
            },
        )
        return 0
    except Exception:
        write(output / "failure.txt", traceback.format_exc().encode())
        write(
            output / "result.json",
            {"status": "FAIL_PRODUCER", "counters": "UNKNOWN_NOT_WRITTEN; inspect prefixes"},
        )
        return 1


def run(request_path, output):
    output.mkdir(parents=True)  # Refusal before request/source/case bytes.
    raw = read(request_path)
    request = strict(raw)
    write(output / "request_snapshot.json", raw)
    release = request["release"]
    if not output.resolve().is_relative_to(Path(release["external_root"]).resolve()):
        raise ValueError("fresh registered external output required")
    write(
        output / "pending.json",
        {
            "before_interpreter": True,
            "before_import": True,
            "before_fixture_bytes": True,
            "request_sha256": sha(raw),
            "source": release["head"],
        },
    )
    command = [
        "/usr/bin/time",
        "-lp",
        "-o",
        str(output / "native.time"),
        release["runtime"]["executable"],
        "-I",
        str(Path(release["root"]) / PROGRAMS[2]),
        "child",
        str(output / "request_snapshot.json"),
        str(output),
    ]
    if release["kind"] == "REGISTERED_REGRESSION_B4_49":
        # Ordinary portable tests make no native resource claim.
        command = command[4:]
        write(output / "native.time", b"UNKNOWN_NOT_PROFILED_REGISTERED_REGRESSION\n")
    start = time.monotonic()
    with (output / "stdout.log").open("xb") as out, (output / "stderr.log").open("xb") as err:
        process = subprocess.Popen(command, cwd=release["root"], stdout=out, stderr=err)
        timeout = False
        try:
            process.wait(timeout=55)
        except subprocess.TimeoutExpired:
            timeout = True
            started = strict(read(output / "started.json"))
            if started["parent_pid"] != process.pid:
                raise ValueError("bound child PID ownership required") from None
            os.kill(started["pid"], signal.SIGKILL)
            process.wait(timeout=5)
    files = (
        "pending.json",
        "started.json",
        "import_before.json",
        "import_complete.json",
        "candidate_source.py",
        "result.json",
        "stdout.log",
        "stderr.log",
        "native.time",
    )
    terminal = {
        "observed_exit": process.returncode,
        "timeout": timeout,
        "through_exit": True,
        "observed_elapsed_seconds": str(time.monotonic() - start),
        "files_sha256": {
            n: sha(read(output / n)) if (output / n).is_file() else "UNKNOWN_NOT_WRITTEN"
            for n in files
        },
    }
    write(output / "terminal.json", terminal)
    return 1 if timeout or process.returncode else 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] in ("run", "child"):
        action = child if sys.argv[1] == "child" else run
        raise SystemExit(action(Path(sys.argv[2]), Path(sys.argv[3])))
    raise ValueError("closed B4.49 invocation")
