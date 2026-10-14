"""Independent B4.47 receipt/launch/case audit; no producer/candidate import.

Own JSON/hash/journal/bootstrap logic; loads only the separate arithmetic oracle.
"""

import hashlib
import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
import sys
import traceback
from pathlib import Path

VERSION = "topolab.b4_47.fresh-public-arithmetic-campaign.v1"
CONTRACT = "docs/planning/b4_47_public_arithmetic_campaign_contract.json"
PROTOCOL = "docs/planning/b4_47_public_arithmetic_campaign_protocol.md"
ORACLE = "scripts/b4_47_arithmetic_oracle.py"
SELF = "scripts/b4_47_campaign_audit.py"
FORBIDDEN = (
    "topolab",
    "numpy",
    "scipy",
    "torch",
    "safetensors",
    "public_campaign_arithmetic",
    "b4_47_campaign",
)


def digest(raw):
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
    fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    return digest(raw)


def load(path, ceiling=8388608):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > ceiling:
        raise ValueError("bounded listed regular input required")
    data = path.read_bytes()
    if len(data) > ceiling:
        raise ValueError("oversized input")
    return data


def parse(raw):
    def closed_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate field")
            result[key] = value
        return result

    def reject_nonfinite(text):
        raise ValueError("nonfinite JSON " + text)

    return json.loads(raw, object_pairs_hook=closed_pairs, parse_constant=reject_nonfinite)


class ProofJournal:
    def __init__(self, root):
        self.root = root
        self.next = 0
        self.previous = None
        self.stack = []
        self.attempted = self.completed = self.failed = 0

    def operation(self, phase, event):
        if phase == "before":
            self.attempted += 1
            self.stack.append(event["stage"])
        elif phase == "after":
            if not self.stack or self.stack[-1] != event["stage"]:
                raise ValueError("independent operation phase mismatch")
            self.stack.pop()
            self.completed += 1
        elif phase == "failure":
            self.failed += len(self.stack)
            self.stack.clear()
        else:
            raise ValueError("unknown independent operation phase")
        self.previous = write(
            self.root / f"{self.next:06}.json",
            {
                "index": self.next,
                "previous_sha256": self.previous,
                "event": event,
                "attempted": self.attempted,
                "completed": self.completed,
                "failed": self.failed,
                "pending": len(self.stack),
            },
        )
        self.next += 1

    def counts(self):
        return {
            "attempted": self.attempted,
            "completed": self.completed,
            "failed": self.failed,
            "pending": len(self.stack),
            "events": self.next,
            "last_sha256": self.previous,
        }


class Checks:
    def __init__(self):
        self.rows = {}

    def require(self, name, condition):
        if name in self.rows:
            raise ValueError("duplicate independent predicate")
        self.rows[name] = bool(condition)
        if not condition:
            raise ValueError(name)
        if len(self.rows) > 16000:
            raise ValueError("frozen predicate budget")


def release_proof(release, native, check):
    fields = {
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
    check("closed_release_schema", type(release) is dict and set(release) == fields)
    check(
        "release_field_types",
        all(
            type(release[k]) is str
            for k in fields - {"isolated_sys_path", "program_sha256", "stdlib_sha256", "ci"}
        )
        and type(release["ci"]) is list
        and type(release["isolated_sys_path"]) is list
        and all(type(x) is str for x in release["isolated_sys_path"]),
    )
    programs = {
        "src/topolab/public_campaign_arithmetic.py",
        ORACLE,
        SELF,
        "scripts/b4_47_campaign.py",
    }
    check(
        "closed_program_hashes",
        type(release["program_sha256"]) is dict
        and set(release["program_sha256"]) == programs
        and all(
            type(d) is str and re.fullmatch(r"[0-9a-f]{64}", d)
            for d in release["program_sha256"].values()
        ),
    )
    check(
        "closed_dependency_map",
        type(release["stdlib_sha256"]) is dict
        and set(release["stdlib_sha256"])
        == {"math", "fractions", "struct", "dataclasses", "re", "json", "hashlib", "types"},
    )
    for name, row in release["stdlib_sha256"].items():
        check(
            "closed_dependency:" + name,
            type(row) is dict
            and set(row) == {"origin", "sha256"}
            and type(row["origin"]) is str
            and type(row["sha256"]) is str
            and re.fullmatch(r"[0-9a-f]{64}", row["sha256"]),
        )
    for i, row in enumerate(release["ci"]):
        check(
            "closed_ci_row:" + str(i),
            type(row) is dict
            and set(row) == {"scope", "name", "head_sha", "conclusion", "app_id", "id"}
            and type(row["app_id"]) is int
            and type(row["id"]) is int,
        )
    if native:
        check("all_six_source_ci", len(release["ci"]) == 6)
        for scope in ("pr", "main"):
            rows = [r for r in release["ci"] if r["scope"] == scope]
            check(
                "exact_head_ci:" + scope,
                len(rows) == 3
                and {r["name"] for r in rows} == {"quality", "frontend", "clean-linux-smoke"}
                and len({r["head_sha"] for r in rows}) == 1
                and all(r["conclusion"] == "success" and r["app_id"] == 15368 for r in rows)
                and (scope != "main" or all(r["head_sha"] == release["head"] for r in rows)),
            )


def profile(raw):
    text = raw.decode()
    duration = re.search(r"([0-9.]+)\s+real\s+([0-9.]+)\s+user\s+([0-9.]+)\s+sys", text)
    rss = re.search(r"(\d+)\s+maximum resident set size", text)
    if duration is None or rss is None:
        raise ValueError("UNKNOWN_STOP native time/RSS")
    return {"wall": duration[1], "user": duration[2], "sys": duration[3], "rss_bytes": int(rss[1])}


def receipt_proof(root, release, expected, check, prefix, native=True):
    terminal = parse(load(root / "terminal.json"))
    check(
        prefix + ":terminal_schema",
        set(terminal)
        == {
            "status",
            "observed_exit_code",
            "timed_out",
            "through_exit",
            "observed_wall_seconds",
            "hashes",
            "missing_completion",
        },
    )
    check(prefix + ":status", terminal["status"] == expected)
    check(
        prefix + ":through_exit",
        terminal["through_exit"] is True and type(terminal["observed_exit_code"]) is int,
    )
    hash_names = {
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
    }
    check(prefix + ":hash_schema", set(terminal["hashes"]) == hash_names)
    for name, wanted in terminal["hashes"].items():
        path = root / name
        check(
            prefix + ":hash:" + name,
            digest(load(path)) == wanted if path.is_file() else wanted == "UNKNOWN_NOT_WRITTEN",
        )
    request_raw = load(root / "request_snapshot.json")
    request = parse(request_raw)
    pending = parse(load(root / "pending.json"))
    check(
        prefix + ":request_schema", set(request) == {"version", "mode", "release", "expectations"}
    )
    check(prefix + ":request_release", request["release"] == release)
    check(prefix + ":request_version", request["version"] == VERSION)
    check(
        prefix + ":pending_schema",
        set(pending)
        == {
            "version",
            "request_sha256",
            "source_head",
            "source_tree",
            "program_sha256",
            "contract_sha256",
            "candidate_imported",
            "case_input_reads",
            "operations_attempted",
        },
    )
    check(
        prefix + ":pending_before_import",
        pending["candidate_imported"] is False
        and pending["case_input_reads"] == pending["operations_attempted"] == 0
        and pending["request_sha256"] == digest(request_raw)
        and pending["program_sha256"] == release["program_sha256"]
        and pending["contract_sha256"] == release["contract_sha256"]
        and pending["source_head"] == release["head"]
        and pending["source_tree"] == release["tree"],
    )
    started = parse(load(root / "started.json"))
    check(
        prefix + ":started_schema",
        set(started)
        == {
            "pid",
            "parent_pid",
            "sys_executable",
            "python_version",
            "isolated",
            "cwd",
            "sys_path",
            "candidate_imported",
            "case_input_reads",
            "operations_attempted",
        },
    )
    check(
        prefix + ":actual_runtime",
        started["sys_executable"] == release["executable"]
        and started["cwd"] == release["source_root"]
        and started["python_version"] == release["python_version"]
        and started["sys_path"] == release["isolated_sys_path"]
        and started["isolated"] == 1,
    )
    check(
        prefix + ":started_before_import",
        started["candidate_imported"] is False
        and started["case_input_reads"] == started["operations_attempted"] == 0,
    )
    # Monotonic local publication order is observed separately from hash identity.
    check(
        prefix + ":phase_order",
        (root / "pending.json").stat().st_mtime_ns
        <= (root / "started.json").stat().st_mtime_ns
        <= (root / "terminal.json").stat().st_mtime_ns,
    )
    imported = (root / "candidate_import_complete.json").is_file()
    expected_import = expected in (
        "PASS_IMPORT_ONLY",
        "FAIL_CHILD_EXIT",
        "FAIL_TIMEOUT",
        "PASS_PUBLIC_ARITHMETIC_CASES",
    )
    check(prefix + ":actual_import_scope", imported == expected_import)
    if imported:
        complete = parse(load(root / "candidate_import_complete.json"))
        check(
            prefix + ":import_schema",
            set(complete)
            == {
                "attempted",
                "completed",
                "candidate_origin",
                "candidate_sha256",
                "dependencies",
                "module",
                "case_input_reads",
                "forbidden_imports",
            },
        )
        check(
            prefix + ":actual_candidate",
            complete["candidate_origin"]
            == str(Path(release["source_root"]) / "src/topolab/public_campaign_arithmetic.py")
            and complete["candidate_sha256"]
            == release["program_sha256"]["src/topolab/public_campaign_arithmetic.py"]
            and complete["dependencies"] == release["stdlib_sha256"]
            and complete["module"] == "public_campaign_arithmetic"
            and complete["attempted"] == complete["completed"] == 1
            and complete["case_input_reads"] == 0
            and complete["forbidden_imports"] == [],
        )
        check(
            prefix + ":candidate_snapshot",
            digest(load(root / "candidate_source.py")) == complete["candidate_sha256"],
        )
    if expected.startswith("FAIL_"):
        check(
            prefix + ":missing_result_unknown",
            not (root / "result.json").exists()
            and terminal["missing_completion"] == "UNKNOWN_NOT_WRITTEN",
        )
        check(
            prefix + ":negative_exit",
            terminal["observed_exit_code"] != 0
            and terminal["timed_out"] is (expected == "FAIL_TIMEOUT"),
        )
    else:
        result = parse(load(root / "result.json"))
        check(
            prefix + ":observed_exit",
            terminal["observed_exit_code"] == 0 and not terminal["timed_out"],
        )
        check(prefix + ":closed_result_status", result["status"] == expected)
        if expected != "PASS_PUBLIC_ARITHMETIC_CASES":
            check(
                prefix + ":precase_result_schema",
                set(result)
                == {
                    "status",
                    "case_input_reads",
                    "candidate_imports_attempted",
                    "candidate_imports_completed",
                },
            )
            check(
                prefix + ":no_case_bytes",
                result["case_input_reads"] == 0 and not (root / "cases").exists(),
            )
    if expected == "STOP_IMPORT":
        attempt = parse(load(root / "candidate_import_before.json"))
        check(
            prefix + ":failed_actual_dependency_import",
            attempt["attempted"] == 1
            and attempt["completed"] == 0
            and b"registered fresh fractions dependency control"
            in load(root / "import_exception.txt"),
        )
    if native:
        observed = profile(load(root / "native.time"))
        check(
            prefix + ":native_cap",
            float(observed["wall"]) <= 60 and 0 < observed["rss_bytes"] <= 536870912,
        )
    return terminal


def journal_proof(root, expected_events, expected_counts, check, prefix):
    names = sorted(p.name for p in root.iterdir())
    check(
        prefix + ":finite_event_paths",
        names == [f"{i:06}.json" for i in range(len(expected_events))],
    )
    previous = None
    stack = []
    attempted = completed = failed = 0
    for i, expected in enumerate(expected_events):
        raw = load(root / f"{i:06}.json")
        event = parse(raw)
        check(
            prefix + ":schema:" + str(i),
            set(event)
            == {"index", "previous_sha256", "event", "attempted", "completed", "failed", "pending"},
        )
        check(
            prefix + ":immutable_prefix:" + str(i),
            event["index"] == i
            and event["previous_sha256"] == previous
            and event["event"] == expected,
        )
        phase = expected["phase"]
        if phase == "before":
            attempted += 1
            stack.append(expected["stage"])
        elif phase == "after":
            check(prefix + ":phase:" + str(i), bool(stack) and stack[-1] == expected["stage"])
            stack.pop()
            completed += 1
        elif phase == "failure":
            failed += len(stack)
            stack.clear()
        else:
            raise ValueError("unknown phase")
        check(
            prefix + ":counts:" + str(i),
            event["attempted"] == attempted
            and event["completed"] == completed
            and event["failed"] == failed
            and event["pending"] == len(stack),
        )
        previous = digest(raw)
    check(
        prefix + ":final_counts",
        expected_counts
        == {
            "attempted": attempted,
            "completed": completed,
            "failed": failed,
            "pending": len(stack),
            "events": len(expected_events),
            "last_sha256": previous,
        },
    )


def audit_evidence(release_path, controls_root, producer_root, output, *, native=True):
    output.mkdir(parents=True)
    raw = load(release_path, 1048576)
    release = parse(raw)
    write(output / "release_snapshot.json", raw)
    write(
        output / "pending.json",
        {
            "role": "independent",
            "release_sha256": digest(raw),
            "source_head": release["head"],
            "oracle_imported": False,
            "case_input_reads": 0,
        },
    )
    checks = Checks()
    rows = []
    try:
        release_proof(release, native, checks.require)
        checks.require(
            "formal_version_kind",
            release["version"] == VERSION
            and release["execution_kind"]
            == ("FORMAL_B4_47" if native else "REGISTERED_REGRESSION_B4_47"),
        )
        external = Path(release["external_root"])
        checks.require(
            "literal_fresh_role_paths",
            controls_root == external / "formal-controls"
            and producer_root == external / "formal-producer"
            and output == external / "formal-independent",
        )
        root = Path(release["source_root"])
        checks.require(
            "actual_independent_runtime",
            sys.executable == release["executable"]
            and sys.flags.isolated == 1
            and str(Path.cwd()) == str(root)
            and sys.path == release["isolated_sys_path"]
            and ".".join(map(str, sys.version_info[:3])) == release["python_version"]
            and (not native or release["python_version"] == "3.12.10")
            and digest(load(Path(sys.executable).resolve())) == release["executable_sha256"],
        )
        checks.require(
            "clean_exact_released_source",
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            == release["head"]
            and subprocess.check_output(
                ["git", "rev-parse", "HEAD^{tree}"], cwd=root, text=True
            ).strip()
            == release["tree"]
            and (
                not native
                or not subprocess.check_output(
                    ["git", "status", "--porcelain", "--untracked-files=all"], cwd=root
                )
            ),
        )
        for name, wanted in [
            (CONTRACT, release["contract_sha256"]),
            (PROTOCOL, release["protocol_sha256"]),
            ("uv.lock", release["lock_sha256"]),
            (SELF, release["program_sha256"][SELF]),
            (ORACLE, release["program_sha256"][ORACLE]),
        ]:
            checks.require("bound_text:" + name, digest(load(root / name)) == wanted)
        contract = parse(load(root / CONTRACT))
        write(
            output / "started.json",
            {
                "pid": os.getpid(),
                "sys_executable": sys.executable,
                "cwd": str(root),
                "sys_path": sys.path,
                "isolated": sys.flags.isolated,
                "oracle_imported": False,
                "case_input_reads": 0,
            },
        )
        spec = importlib.machinery.PathFinder.find_spec(
            "b4_47_arithmetic_oracle", [str(root / "scripts")]
        )
        checks.require(
            "actual_oracle_origin", spec is not None and spec.origin == str(root / ORACLE)
        )
        oracle_raw = load(root / ORACLE)
        write(output / "oracle_source.py", oracle_raw)
        oracle = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = oracle
        exec(compile(oracle_raw.decode(), spec.origin, "exec"), oracle.__dict__)
        checks.require(
            "no_candidate_producer_shared_import",
            not any(n.split(".")[0] in FORBIDDEN for n in sys.modules),
        )
        write(
            output / "oracle_import_complete.json",
            {
                "module": spec.name,
                "origin": spec.origin,
                "sha256": digest(oracle_raw),
                "case_input_reads": 0,
                "forbidden_imports": [],
            },
        )
        controls = parse(load(controls_root / "result.json"))
        checks.require(
            "controls_complete",
            controls["passed"] is True
            and controls["formal_retry"] is False
            and controls["cases"]
            == [
                {"id": e["id"], "status": e["expected_status"]} for e in contract["launch_controls"]
            ],
        )
        for entry in contract["launch_controls"]:
            if entry["id"] == "existing_output":
                refusal = parse(load(controls_root / "existing_output_refusal.json"))
                checks.require(
                    "refusal_closed",
                    set(refusal)
                    == {
                        "status",
                        "unchanged",
                        "original_sha256",
                        "after_sha256",
                        "request_reads",
                        "new_child_launches",
                    },
                )
                checks.require(
                    "refusal_unchanged_prebyte",
                    refusal["status"] == "REFUSED_EXISTING_OUTPUT"
                    and refusal["unchanged"] is True
                    and refusal["original_sha256"] == refusal["after_sha256"]
                    and refusal["request_reads"] == refusal["new_child_launches"] == 0,
                )
                for name, wanted in refusal["original_sha256"].items():
                    checks.require(
                        "refusal_original:" + name,
                        digest(load(controls_root / "actual_candidate_import" / name)) == wanted,
                    )
            else:
                receipt_proof(
                    controls_root / entry["id"],
                    release,
                    entry["expected_status"],
                    checks.require,
                    "control:" + entry["id"],
                    native=native,
                )
        producer = producer_root / "producer"
        receipt_proof(
            producer,
            release,
            "PASS_PUBLIC_ARITHMETIC_CASES",
            checks.require,
            "producer",
            native=native,
        )
        summary = parse(load(producer / "result.json"))
        checks.require(
            "closed_producer_summary",
            set(summary)
            == {
                "status",
                "cases",
                "cases_attempted",
                "cases_completed",
                "cases_pending",
                "explicit_case_file_reads",
                "Git_internal_content_read_counts",
                "candidate_imports_attempted",
                "candidate_imports_completed",
            },
        )
        checks.require(
            "ALL10_complete_case_counts",
            summary["cases_attempted"] == summary["cases_completed"] == 10
            and summary["cases_pending"] == 0
            and len(summary["cases"]) == 10
            and summary["explicit_case_file_reads"] == 20,
        )
        for index, entry in enumerate(contract["catalog"]):
            own = output / "cases" / entry["id"]
            write(
                own / "before.json",
                {
                    "id": entry["id"],
                    "index": index,
                    "cases_attempted": index + 1,
                    "cases_completed": index,
                    "cases_pending": 1,
                    "input_sha256": entry["sha256"],
                    "input_path": entry["path"],
                },
            )
            fixture_raw = load(root / entry["path"], 32768)
            checks.require("fixture_hash:" + entry["id"], digest(fixture_raw) == entry["sha256"])
            write(own / "input_snapshot.json", fixture_raw)
            fixture = parse(fixture_raw)
            prior = producer / "cases" / entry["id"]
            checks.require(
                "same_input_snapshot:" + entry["id"],
                fixture_raw == load(prior / "input_snapshot.json"),
            )
            result_raw = load(prior / "result.json")
            result = parse(result_raw)
            checks.require(
                "case_result_binding:" + entry["id"],
                digest(result_raw) == summary["cases"][index]["result_sha256"]
                and summary["cases"][index]["id"] == entry["id"]
                and result["status"] == entry["expected_status"],
            )
            journal = ProofJournal(own / "operations")
            case = oracle.audit_case(fixture, result, journal.operation)
            for name, passed in case["checks"].items():
                checks.require("case:" + entry["id"] + ":" + name, passed)
            checks.require(
                "case_audit_complete:" + entry["id"],
                case["passed"] is True and journal.counts()["pending"] == 0,
            )
            journal_proof(
                prior / "operations",
                result["operations"],
                summary["cases"][index]["operations"],
                checks.require,
                "journal:" + entry["id"],
            )
            write(own / "result.json", case)
            write(
                own / "after.json",
                {
                    "id": entry["id"],
                    "passed": case["passed"],
                    "cases_attempted": index + 1,
                    "cases_completed": index + 1,
                    "cases_pending": 0,
                    "operations": journal.counts(),
                    "RN_even_proofs": case["RN_even_proofs"],
                },
            )
            rows.append(
                {
                    "id": entry["id"],
                    "passed": True,
                    "RN_even_proofs": case["RN_even_proofs"],
                    "operations": journal.counts(),
                }
            )
        write(
            output / "result.json",
            {
                "passed": True,
                "status": "PASS_FRESH_PUBLIC_ARITHMETIC_AUDIT",
                "predicates": checks.rows,
                "cases": rows,
                "cases_attempted": 10,
                "cases_completed": 10,
                "cases_pending": 0,
                "formal_retry": False,
                "candidate_or_producer_imported": False,
            },
        )
        return 0
    except Exception:
        write(output / "failure.txt", traceback.format_exc().encode())
        write(
            output / "result.json",
            {
                "passed": False,
                "status": "FAIL_INCOMPLETE_INDEPENDENT",
                "predicates": checks.rows,
                "cases": rows,
                "unexecuted_or_missing": "UNKNOWN_NOT_WRITTEN",
                "formal_retry": False,
                "candidate_or_producer_imported": False,
            },
        )
        return 1


def main():
    if len(sys.argv) != 5:
        raise ValueError("closed formal independent entrypoint")
    return audit_evidence(*map(Path, sys.argv[1:]))


if __name__ == "__main__":
    sys.exit(main())
