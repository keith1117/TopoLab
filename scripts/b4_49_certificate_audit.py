"""Independent B4.49 launch/receipt audit; imports ONLY own numerical oracle."""

import ast
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

VERSION = "topolab.b4_49.public-combined-diagnostic-certificate.v1"
CONTRACT = "docs/planning/b4_49_public_combined_diagnostic_certificate_contract.json"
ORACLE = "scripts/b4_49_combined_oracle.py"
SELF = "scripts/b4_49_certificate_audit.py"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def put(path, value):
    raw = (
        value
        if isinstance(value, bytes)
        else (
            json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
        ).encode()
    )
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
    return digest(raw)


def get(path, limit=1048576):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        raise ValueError("listed bounded independent input")
    raw = path.read_bytes()
    if len(raw) > limit:
        raise ValueError("input changed size")
    return raw


def parse(raw):
    def pairs(items):
        answer = {}
        for name, value in items:
            if name in answer:
                raise ValueError("duplicate independent metadata field")
            answer[name] = value
        return answer

    def nonfinite(value):
        raise ValueError("nonfinite metadata " + value)

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def assert_hash(path, expected, maximum=1048576):
    raw = get(path, maximum)
    if digest(raw) != expected:
        raise ValueError("changed independent bound input: " + str(path))
    return raw


class Operations:
    def __init__(self, root):
        self.root = root
        self.sequence = 0
        self.last = None
        self.stack = []
        self.attempted = self.completed = 0

    def record(self, phase, value):
        if phase == "before":
            self.stack.append(value["stage"])
            self.attempted += 1
        elif phase == "after":
            if not self.stack or self.stack[-1] != value["stage"]:
                raise ValueError("independent stage completion mismatch")
            self.stack.pop()
            self.completed += 1
        else:
            raise ValueError("independent phase")
        self.last = put(
            self.root / f"{self.sequence:06}.json",
            {
                "index": self.sequence,
                "previous_sha256": self.last,
                "phase": phase,
                "event": value,
                "attempted": self.attempted,
                "completed": self.completed,
                "pending": len(self.stack),
            },
        )
        self.sequence += 1

    def counts(self):
        return {
            "attempted": self.attempted,
            "completed": self.completed,
            "pending": len(self.stack),
            "events": self.sequence,
            "last_sha256": self.last,
        }


def verify_journal(root, expected, result):
    last, attempted, completed, stack, trace = None, 0, 0, [], []
    files = sorted(root.glob("*.json"))
    for index, path in enumerate(files):
        raw = get(path)
        item = parse(raw)
        if (
            path.name != f"{index:06}.json"
            or item["index"] != index
            or item["previous_sha256"] != last
        ):
            raise ValueError("immutable primary operation chain")
        if item["phase"] == "before":
            stack.append(item["event"]["stage"])
            attempted += 1
        elif item["phase"] == "after":
            if not stack or stack.pop() != item["event"]["stage"]:
                raise ValueError("before-operation primary phase")
            completed += 1
            if "mode" in item["event"]:
                trace.append(item["event"])
        else:
            raise ValueError("closed primary operation phase")
        if (item["attempted"], item["completed"], item["pending"]) != (
            attempted,
            completed,
            len(stack),
        ):
            raise ValueError("primary actual operation counters")
        last = digest(raw)
    actual = {
        "attempted": attempted,
        "completed": completed,
        "pending": len(stack),
        "events": len(files),
        "last_sha256": last,
    }
    if expected != actual or stack or trace != result["trace"]:
        raise ValueError("complete independent prefix and result binding")
    return len(files)


def profile(raw):
    text = raw.decode()
    match = re.search(r"(?:real\s+([0-9.]+)\s+user\s+([0-9.]+)\s+sys\s+([0-9.]+))", text)
    if match is None:
        match = re.search(r"([0-9.]+)\s+real\s+([0-9.]+)\s+user\s+([0-9.]+)\s+sys", text)
    rss = re.search(r"(\d+)\s+maximum resident set size", text)
    if match is None or rss is None:
        raise ValueError("UNKNOWN_STOP native profile")
    return {"wall": match[1], "user": match[2], "sys": match[3], "rss_bytes": int(rss[1])}


def child(request_path, output):
    put(
        output / "started.json",
        {
            "before_oracle_import": True,
            "pid": os.getpid(),
            "parent_pid": os.getppid(),
            "cwd": str(Path.cwd()),
            "executable": sys.executable,
            "sys_path": sys.path,
            "case_reads": 0,
        },
    )
    try:
        request = parse(get(request_path))
        if (
            set(request)
            != {"version", "role", "release", "primary_root", "primary_terminal_sha256"}
            or request["role"] != "independent"
            or request["version"] != VERSION
        ):
            raise ValueError("closed independent request")
        release = request["release"]
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
            or release["kind"] not in ("FORMAL_B4_49", "REGISTERED_REGRESSION_B4_49")
        ):
            raise ValueError("closed independent release")
        programs = {
            "src/topolab/combined_certificate.py",
            ORACLE,
            SELF,
            "scripts/b4_49_certificate_campaign.py",
        }
        if set(release["program_sha256"]) != programs:
            raise ValueError("independent exact program paths")
        if (
            digest((json.dumps(release["source_manifest"], sort_keys=True) + "\n").encode())
            != release["source_manifest_sha256"]
        ):
            raise ValueError("independent source manifest identity")
        root = Path(release["root"])
        if Path.cwd().resolve() != root or sys.executable != release["runtime"]["executable"]:
            raise ValueError("independent exact cwd/interpreter")
        if (
            sys.version != release["runtime"]["python_version"]
            or sys.path != release["runtime"]["sys_path"]
            or not sys.flags.isolated
        ):
            raise ValueError("independent locked isolated runtime")
        if (
            digest(Path(sys.executable).resolve().read_bytes())
            != release["runtime"]["executable_sha256"]
        ):
            raise ValueError("interpreter bytes")
        if release["kind"] == "FORMAL_B4_49":
            if sys.version_info[:3] != (3, 12, 10):
                raise ValueError("formal independent CPython3.12.10")
            if subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root
            ):
                raise ValueError("independent clean source")
            if (
                subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
                != release["head"]
            ):
                raise ValueError("independent released source")
            if (
                subprocess.check_output(
                    ["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True
                ).strip()
                != release["tree"]
            ):
                raise ValueError("independent exact released tree")
            for scope in ("pr", "main"):
                ci = [x for x in release["ci"] if x["scope"] == scope]
                if (
                    len(ci) != 3
                    or {x["name"] for x in ci} != {"quality", "frontend", "clean-linux-smoke"}
                    or any(x["conclusion"] != "success" for x in ci)
                ):
                    raise ValueError("independent all applicable source CI")
                if scope == "main" and any(x["head_sha"] != release["head"] for x in ci):
                    raise ValueError("independent exact main CI head")
        assert_hash(root / "uv.lock", release["lock_sha256"])
        contract = parse(assert_hash(root / CONTRACT, release["contract_sha256"]))
        assert_hash(
            root / CONTRACT.replace("_contract.json", "_protocol.md"), release["protocol_sha256"]
        )
        if contract["version"] != VERSION or len(contract["catalog"]) != 12:
            raise ValueError("independent finite contract")
        for path, expected in release["program_sha256"].items():
            raw = assert_hash(root / path, expected)
            # Source HASH/AST only; never import primary/candidate/shared helpers.
            for node in ast.walk(ast.parse(raw)):
                names = (
                    [node.module]
                    if isinstance(node, ast.ImportFrom)
                    else [x.name for x in node.names]
                    if isinstance(node, ast.Import)
                    else []
                )
                if any(x is None or x.split(".")[0] not in sys.stdlib_module_names for x in names):
                    raise ValueError("stdlib-only sources")
        for name, info in release["runtime"]["stdlib"].items():
            spec = importlib.util.find_spec(name)
            if spec is None or spec.origin != info["origin"]:
                raise ValueError("independent dependency origin")
            if spec.origin in ("built-in", "frozen"):
                if (
                    release["kind"] != "REGISTERED_REGRESSION_B4_49"
                    or info["sha256"] != "UNKNOWN_NOT_SEPARATE_ORIGIN_FILE"
                ):
                    raise ValueError("formal missing independent dependency file hash")
            else:
                assert_hash(Path(spec.origin), info["sha256"])
        if any(
            x in sys.modules
            for x in (
                "topolab",
                "combined_certificate",
                "b4_49_certificate_campaign",
                "numpy",
                "scipy",
                "torch",
            )
        ):
            raise ValueError("candidate-free independent process")
        raw = assert_hash(root / ORACLE, release["program_sha256"][ORACLE])
        put(output / "oracle_source.py", raw)
        spec = importlib.machinery.PathFinder.find_spec(
            "b4_49_combined_oracle", [str(root / "scripts")]
        )
        if spec is None or spec.origin != str(root / ORACLE):
            raise ValueError("independent own oracle origin")
        put(output / "import_before.json", {"origin": spec.origin, "sha256": digest(raw)})
        oracle = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = oracle
        exec(compile(raw, spec.origin, "exec"), oracle.__dict__)
        put(
            output / "import_complete.json",
            {
                "origin": oracle.__file__,
                "sha256": digest(raw),
                "oracle_imported": True,
                "candidate_imported": False,
            },
        )
        primary = Path(request["primary_root"])
        if not primary.resolve().is_relative_to(Path(release["external_root"]).resolve()):
            raise ValueError("only this slice primary output")
        terminal = parse(assert_hash(primary / "terminal.json", request["primary_terminal_sha256"]))
        if terminal["observed_exit"] != 0 or not terminal["through_exit"] or terminal["timeout"]:
            raise ValueError("FAIL_INCOMPLETE primary receipt")
        for path, expected in terminal["files_sha256"].items():
            if expected == "UNKNOWN_NOT_WRITTEN":
                raise ValueError("UNKNOWN_STOP primary terminal field")
            assert_hash(primary / path, expected)
        pending, started = (
            parse(get(primary / "pending.json")),
            parse(get(primary / "started.json")),
        )
        primary_request = parse(get(primary / "request_snapshot.json"))
        if (
            not pending["before_interpreter"]
            or not pending["before_import"]
            or not pending["before_fixture_bytes"]
            or not started["before_candidate_import"]
        ):
            raise ValueError("primary phase identities")
        if (
            pending["request_sha256"] != digest(get(primary / "request_snapshot.json"))
            or primary_request["release"] != release
        ):
            raise ValueError("same released source/request lineage")
        summary = parse(get(primary / "result.json"))
        if (
            len(summary["cases"]) != 12
            or summary["cases_completed"] != 12
            or summary["cases_pending"] != 0
        ):
            raise ValueError("incomplete primary case population")
        audits, total = [], 0
        for entry, closed in zip(contract["catalog"], summary["cases"], strict=True):
            case_root = primary / "cases" / entry["id"]
            own = output / "cases" / entry["id"]
            put(own / "before_input.json", entry)
            case_raw = assert_hash(root / entry["path"], entry["sha256"], 32768)
            put(own / "input.json", case_raw)
            fixture = parse(case_raw)
            if (
                get(case_root / "input.json") != case_raw
                or parse(get(case_root / "before_input.json")) != entry
            ):
                raise ValueError("exact public input identity")
            if closed["id"] != entry["id"]:
                raise ValueError("fixed case order")
            result = parse(assert_hash(case_root / "result.json", closed["result_sha256"]))
            counts = parse(get(case_root / "operation_counts.json"))
            verify_journal(case_root / "operations", counts, result)
            if counts != closed["operation_counts"]:
                raise ValueError("closed immutable counters")
            journal = Operations(own / "operations")
            audit = oracle.audit(fixture, result, entry["expected_status"], journal.record)
            if journal.stack:
                raise ValueError("incomplete independent proof")
            put(own / "audit.json", audit)
            put(own / "operation_counts.json", journal.counts())
            total += audit["predicates"]
            if total > 16000:
                raise ValueError("frozen independent predicate cap")
            audits.append(audit)
        if release["kind"] == "FORMAL_B4_49":
            native = profile(get(primary / "native.time"))
            if float(native["wall"]) > 60 or native["rss_bytes"] > 536870912:
                raise ValueError("primary SOFTWARE resource cap")
        else:
            native = {
                "wall": "UNKNOWN_NOT_PROFILED_REGISTERED_REGRESSION",
                "rss_bytes": "UNKNOWN_NOT_PROFILED_REGISTERED_REGRESSION",
            }
        put(
            output / "result.json",
            {
                "status": "PASS_PUBLIC_COMBINED_DIAGNOSTIC_ONLY",
                "audits": audits,
                "predicates": total,
                "RN_even_proofs": sum(x["RN_even_proofs"] for x in audits),
                "fixed80_root_proofs": sum(x["fixed80_root_proofs"] for x in audits),
                "case_audits": 12,
                "primary_native": native,
                "scientific_gate": "FAIL",
                "real_fem_certified": False,
                "loss_gradient_changed": False,
            },
        )
        return 0
    except Exception:
        put(output / "failure.txt", traceback.format_exc().encode())
        put(
            output / "result.json",
            {"status": "FAIL_INDEPENDENT", "predicates": "UNKNOWN_NOT_WRITTEN; inspect prefixes"},
        )
        return 1


def run(request_path, output):
    output.mkdir(parents=True)
    raw = get(request_path)
    request = parse(raw)
    release = request["release"]
    if not output.resolve().is_relative_to(Path(release["external_root"]).resolve()):
        raise ValueError("independent fresh external output")
    put(output / "request_snapshot.json", raw)
    put(
        output / "pending.json",
        {
            "before_interpreter": True,
            "before_oracle_import": True,
            "before_fixture_bytes": True,
            "request_sha256": digest(raw),
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
        str(Path(release["root"]) / SELF),
        "child",
        str(output / "request_snapshot.json"),
        str(output),
    ]
    if release["kind"] == "REGISTERED_REGRESSION_B4_49":
        command = command[4:]
        put(output / "native.time", b"UNKNOWN_NOT_PROFILED_REGISTERED_REGRESSION\n")
    start = time.monotonic()
    with (output / "stdout.log").open("xb") as out, (output / "stderr.log").open("xb") as err:
        process = subprocess.Popen(command, cwd=release["root"], stdout=out, stderr=err)
        timeout = False
        try:
            process.wait(timeout=55)
        except subprocess.TimeoutExpired:
            timeout = True
            started = parse(get(output / "started.json"))
            if started["parent_pid"] != process.pid:
                raise ValueError("independent bound child PID") from None
            os.kill(started["pid"], signal.SIGKILL)
            process.wait(timeout=5)
    names = (
        "pending.json",
        "started.json",
        "import_before.json",
        "import_complete.json",
        "oracle_source.py",
        "result.json",
        "stdout.log",
        "stderr.log",
        "native.time",
    )
    put(
        output / "terminal.json",
        {
            "observed_exit": process.returncode,
            "timeout": timeout,
            "through_exit": True,
            "observed_elapsed_seconds": str(time.monotonic() - start),
            "files_sha256": {
                n: digest(get(output / n)) if (output / n).is_file() else "UNKNOWN_NOT_WRITTEN"
                for n in names
            },
        },
    )
    return 1 if timeout or process.returncode else 0


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("run", "child"):
        raise ValueError("closed independent invocation")
    raise SystemExit(
        (child if sys.argv[1] == "child" else run)(Path(sys.argv[2]), Path(sys.argv[3]))
    )
