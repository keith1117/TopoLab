"""Separate stdlib audit of finite public launch receipts; no candidate import."""

import ast
import hashlib
import json
import sys
from pathlib import Path

VERSION = "topolab.public-launch-preflight.v1"
EXPECTED = (
    ("clean_external_launch", "PASS_PUBLIC_PREFLIGHT"),
    ("wrong_interpreter", "STOP_INTERPRETER"),
    ("wrong_cwd", "STOP_CWD"),
    ("wrong_lock", "STOP_LOCK"),
    ("missing_package_origin", "STOP_PACKAGE_ORIGIN"),
    ("shadow_probe_origin", "STOP_PROBE_ORIGIN"),
    ("changed_probe_bytes", "STOP_PROBE_HASH"),
    ("public_import_failure", "STOP_IMPORT"),
    ("public_early_exit", "FAIL_CHILD_EXIT"),
    ("public_timeout", "FAIL_TIMEOUT"),
    ("existing_receipt_refusal", "REFUSED_EXISTING_OUTPUT"),
    ("changed_package_hash", "STOP_PACKAGE_HASH"),
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(path):
    raw = path.read_bytes()
    if len(raw) > 131072:
        raise ValueError("receipt exceeds public audit cap")

    def obj(pairs):
        if len({k for k, _ in pairs}) != len(pairs):
            raise ValueError("duplicate object key")
        return dict(pairs)

    def deny(value):
        raise ValueError("nonfinite constant: " + value)

    result = json.loads(raw, object_pairs_hook=obj, parse_constant=deny)
    if not isinstance(result, dict):
        raise ValueError("closed receipt root must be object")
    return result


def schema(value, fields):
    if set(value) != set(fields):
        raise ValueError("closed field set differs")


def main():
    source, contract_path, evidence, freeze_path, destination = map(Path, sys.argv[1:])
    checks, failure, audited = [], None, 0
    reads = []

    def load(path):
        reads.append(str(path))
        return read_json(path)

    def hashed(path):
        reads.append(str(path))
        return digest(path.read_bytes())

    def check(name, passed):
        checks.append({"id": name, "passed": bool(passed)})
        if not passed:
            raise ValueError("independent predicate failed: " + name)

    with destination.with_suffix(".pending.json").open("x") as stream:
        json.dump({"phase": "BEFORE_INDEPENDENT_RECEIPT_AUDIT", "software_only": True}, stream)
    try:
        c = load(contract_path)
        schema(
            c,
            (
                "version",
                "authority",
                "starting_main",
                "slice_limit",
                "scope",
                "source_inputs_at_starting_main_sha256",
                "fixture_path",
                "fixture_sha256",
                "public_cases",
                "public_source_sha256",
                "request_fields",
                "request_policy",
                "launch_policy",
                "receipt_policy",
                "role_access",
                "software_audits",
                "public_evidence_retained",
                "b4_44_retained",
                "boundaries",
                "future_criteria_unchanged",
                "preserved_failures",
                "preserved_cost",
                "full_training_memory",
                "real_prerequisites",
                "new_production_budget_or_reserve",
                "real_values_and_new_arithmetic_evaluated",
                "stops",
                "allowed_publish_paths",
                "software_failure_policy",
                "software_cost_policy",
                "next_proposed",
                "next_authorized",
                "next_started",
            ),
        )
        check(
            "finite-owner-scope",
            c["slice_limit"] == 1
            and not c["next_authorized"]
            and not c["next_started"]
            and not c["real_values_and_new_arithmetic_evaluated"],
        )
        prior_path = source / (
            "docs/planning/b4_44_public_assembled_residual_limitations_real_certification_contract.json"
        )
        check(
            "bound-prior-contract",
            hashed(prior_path)
            == c["source_inputs_at_starting_main_sha256"][str(prior_path.relative_to(source))],
        )
        prior = load(prior_path)
        for key in (
            "future_criteria_unchanged",
            "preserved_failures",
            "preserved_cost",
            "full_training_memory",
            "boundaries",
            "public_evidence_retained",
            "real_prerequisites",
        ):
            check("complete-inherited-" + key, c[key] == prior[key])
        fixture_path = source / c["fixture_path"]
        check("fixture-hash", hashed(fixture_path) == c["fixture_sha256"])
        fixture = load(fixture_path)
        schema(
            fixture, ("version", "module_name", "marker", "source_texts", "source_sha256", "cases")
        )
        check(
            "fixed-case-identities",
            tuple((r["id"], r["expected_status"]) for r in fixture["cases"]) == EXPECTED
            and fixture["cases"] == c["public_cases"],
        )
        check(
            "four-fixed-texts",
            len(fixture["source_texts"]) == 4
            and fixture["source_sha256"] == c["public_source_sha256"],
        )
        for key, text in fixture["source_texts"].items():
            check("public-source-" + key, digest(text.encode()) == fixture["source_sha256"][key])
        frozen = load(freeze_path)
        for name, value in frozen["program_sha256"].items():
            path = source / name
            check("frozen-program-" + name, hashed(path) == value)
            if path.suffix == ".py":
                tree = ast.parse(path.read_text())
                modules = []
                for n in ast.walk(tree):
                    if isinstance(n, ast.Import):
                        modules.extend(alias.name.split(".")[0] for alias in n.names)
                    elif isinstance(n, ast.ImportFrom) and n.module:
                        modules.append(n.module.split(".")[0])
                check(
                    "stdlib-only-" + name,
                    all(m in sys.stdlib_module_names for m in modules)
                    if not name.startswith("tests/")
                    else True,
                )
        primary = load(evidence / "primary.json")
        schema(
            primary,
            (
                "version",
                "passed",
                "formal_calls",
                "formal_retry",
                "cases",
                "failure",
                "not_evaluated",
                "numeric_cases",
                "real_payload_reads",
                "fits",
                "software_only",
            ),
        )
        check(
            "complete-primary",
            primary["passed"]
            and primary["failure"] is None
            and primary["not_evaluated"] == []
            and len(primary["cases"]) == 12
            and primary["formal_calls"] == 1
            and primary["formal_retry"] is False,
        )
        check(
            "no-real-execution",
            primary["numeric_cases"] == primary["real_payload_reads"] == primary["fits"] == 0
            and primary["software_only"] is True,
        )
        for position, (ident, expected) in enumerate(EXPECTED):
            case_dir = evidence / ident
            observed = load(case_dir / "observed.json")
            schema(
                observed,
                (
                    "id",
                    "expected_status",
                    "actual_status",
                    "exit_code",
                    "passed",
                    "output",
                    "before_existing_sha256",
                    "after_output_sha256",
                    "request_sha256",
                    "controller_stdout_sha256",
                    "controller_stderr_sha256",
                ),
            )
            check(
                ident + "-primary-identity",
                primary["cases"][position] == observed
                and observed["id"] == ident
                and observed["actual_status"] == expected
                and observed["passed"],
            )
            request_path = case_dir / "request.json"
            request = load(request_path)
            schema(request, c["request_fields"])
            check(ident + "-request-bind", hashed(request_path) == observed["request_sha256"])
            for log in ("stdout", "stderr"):
                path = case_dir / ("controller_" + log + ".log")
                check(
                    ident + "-controller-" + log,
                    hashed(path) == observed["controller_" + log + "_sha256"],
                )
            stdout_path = case_dir / "controller_stdout.log"
            check(ident + "-observed-disposition", read_json(stdout_path)["status"] == expected)
            output = Path(observed["output"])
            check(ident + "-new-owned-output", output.is_relative_to(evidence))
            actual_files = {p.name: hashed(p) for p in output.iterdir() if p.is_file()}
            check(ident + "-immutable-final-files", actual_files == observed["after_output_sha256"])
            if ident == "existing_receipt_refusal":
                check(
                    ident + "-unchanged-existing",
                    observed["before_existing_sha256"] == actual_files
                    and observed["exit_code"] == 2
                    and output == evidence / "clean_external_launch/output",
                )
                audited += 1
                continue
            pending, terminal = load(output / "pending.json"), load(output / "terminal.json")
            schema(pending, ("version", "phase", "request_path", "request_sha256", "request_error"))
            schema(
                terminal,
                (
                    "version",
                    "phase",
                    "status",
                    "request_sha256",
                    "child_exit_code",
                    "timeout",
                    "launch_error",
                    "parse_error",
                    "sha256",
                    "attempts",
                    "completed",
                    "result_state",
                ),
            )
            check(
                ident + "-phase-and-request",
                pending["version"] == terminal["version"] == VERSION
                and pending["phase"] == "PENDING_BEFORE_CHILD_LAUNCH"
                and terminal["phase"] == "TERMINAL_AFTER_OBSERVED_EXIT"
                and pending["request_sha256"]
                == terminal["request_sha256"]
                == observed["request_sha256"]
                and pending["request_path"] == str(request_path)
                and pending["request_error"] is None,
            )
            check(
                ident + "-terminal-disposition",
                terminal["status"] == expected
                and observed["exit_code"] == (0 if expected == "PASS_PUBLIC_PREFLIGHT" else 1),
            )
            schema(
                terminal["sha256"],
                ("pending.json", "started.json", "probe_result.json", "stdout.log", "stderr.log"),
            )
            for n, value in terminal["sha256"].items():
                check(ident + "-terminal-link-" + n, value == actual_files.get(n))
            aborted = ident in ("public_early_exit", "public_timeout")
            attempted = ident in (
                "clean_external_launch",
                "public_import_failure",
                "public_early_exit",
                "public_timeout",
            )
            check(ident + "-started-prefix", (output / "started.json").exists() == attempted)
            if attempted:
                start = load(output / "started.json")
                schema(
                    start,
                    (
                        "version",
                        "phase",
                        "attempts",
                        "request_sha256",
                        "probe_sha256",
                        "probe_origin",
                    ),
                )
                check(
                    ident + "-pre-probe-identity",
                    start["version"] == VERSION
                    and start["phase"] == "BEFORE_CHECKED_PUBLIC_PROBE"
                    and start["attempts"] == 1
                    and start["request_sha256"] == observed["request_sha256"]
                    and start["probe_sha256"] == request["expected_probe_sha256"]
                    and start["probe_origin"] == request["expected_probe_origin"],
                )
            check(
                ident + "-counts-not-inferred",
                terminal["attempts"] == int(attempted)
                and terminal["completed"]
                == ("UNKNOWN_NOT_WRITTEN" if aborted else int(ident == "clean_external_launch")),
            )
            check(
                ident + "-complete-result-status",
                terminal["result_state"] == ("NOT_WRITTEN" if aborted else "WRITTEN"),
            )
            check(
                ident + "-exit-timeout",
                terminal["timeout"] == (ident == "public_timeout")
                and terminal["child_exit_code"]
                == (
                    None
                    if ident == "public_timeout"
                    else 7
                    if ident == "public_early_exit"
                    else 0
                    if ident == "clean_external_launch"
                    else 1
                ),
            )
            if not aborted:
                result = load(output / "probe_result.json")
                schema(
                    result,
                    (
                        "version",
                        "status",
                        "detail",
                        "context",
                        "attempts",
                        "completed",
                        "traceback",
                    ),
                )
                ctx = result["context"]
                allowed = {
                    "executable",
                    "real_executable",
                    "python",
                    "implementation",
                    "prefix",
                    "base_prefix",
                    "isolated",
                    "cwd",
                    "initial_sys_path",
                    "package_origin",
                    "probe_origin",
                    "probe_loaded_origin",
                    "application_modules_before",
                    "application_modules_after",
                    "source_revision",
                    "uv.lock_sha256",
                    "pyproject.toml_sha256",
                    "sys_path",
                    "package_sha256",
                    "probe_sha256",
                }
                check(
                    ident + "-context-closed",
                    set(ctx) <= allowed
                    and {
                        "executable",
                        "cwd",
                        "initial_sys_path",
                        "isolated",
                        "application_modules_after",
                    }
                    <= set(ctx),
                )
                check(
                    ident + "-runtime-not-old-reconstruction",
                    ctx["executable"] == str(source / ".venv/bin/python")
                    and ctx["cwd"] == str(source)
                    and ctx["isolated"] == 1
                    and ctx["python"][:2] == [3, 12]
                    and ctx["implementation"] == "cpython",
                )
                check(
                    ident + "-no-application-import",
                    ctx["application_modules_before"] == ctx["application_modules_after"] == [],
                )
                check(
                    ident + "-outcome-counts",
                    result["status"] == expected
                    and result["attempts"] == int(attempted)
                    and result["completed"] == int(ident == "clean_external_launch"),
                )
                if attempted:
                    check(
                        ident + "-bound-origins",
                        ctx["package_origin"] == str(source / "src/topolab/__init__.py")
                        and ctx["probe_origin"] == request["expected_probe_origin"]
                        and ctx["probe_sha256"] == request["expected_probe_sha256"],
                    )
                if ident == "clean_external_launch":
                    check(
                        ident + "-loaded-source",
                        ctx["probe_loaded_origin"] == ctx["probe_origin"]
                        and ctx["source_revision"] == c["starting_main"]
                        and ctx["package_sha256"]
                        == c["source_inputs_at_starting_main_sha256"]["src/topolab/__init__.py"],
                    )
                if ident == "public_import_failure":
                    check(
                        ident + "-full-exception",
                        "RuntimeError" in result["traceback"]
                        and "prescribed public import failure" in result["detail"],
                    )
            audited += 1
        check("all-twelve-independent", audited == 12 and len(checks) <= 1000)
    except Exception as exc:
        import traceback

        failure = {
            "type": type(exc).__name__,
            "detail": str(exc),
            "traceback": traceback.format_exc(),
        }
    receipt = {
        "version": "topolab.b4_45.independent-launch-audit.v1",
        "passed": failure is None,
        "checks": checks,
        "case_audits": audited,
        "failure": failure,
        "read_paths": sorted(set(reads)),
        "formal_calls": 1,
        "formal_retry": False,
        "candidate_imports": 0,
        "numeric_cases": 0,
    }
    with destination.open("x") as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(
        json.dumps(
            {
                "passed": receipt["passed"],
                "predicates": len(checks),
                "cases": audited,
                "failure": failure,
            }
        )
    )
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
