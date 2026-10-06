"""One registered saved-schema compatibility recovery; cumulative v1 caps remain."""

import argparse
import os
import subprocess
import sys
from pathlib import Path
from time import perf_counter

import b4_24_independent_audit as independent
import b4_24_versioned_correctness_failure_review as original
from b4_10_resource_close import profile

VERSION = "topolab.b4_24.saved-schema-recovery.v2"
FAILED_BINDINGS = {
    "audit_receipts/production_release.json": (
        "f697fb45c3b3fa5e9677e82b695f4adfd8d82e383166daf6d4e47164f77cc621"
    ),
    "audit_receipts/review_command.json": (
        "4298af75a956c804d32b58d5778f785af6ccc4ed99e4f2ff6e3f406b2d8619e1"
    ),
    "profiles/review.time": "222f3425546ff0d40556bf9f511f2777f23281bdd4b2b2f3de02476e53d505c0",
}


def plan_payload():
    value = {
        **original.plan_payload(),
        "version": VERSION,
        "original_plan_sha256": original.plan_payload()["plan_sha256"],
        "failed_bindings": FAILED_BINDINGS,
        "schema_mapping": {
            "fd": "surrogate_fd",
            "derivative": "surrogate_derivative",
            "error": "surrogate_error",
        },
        "failed_review_charge_seconds": 16.19,
        "maximum_registered_recovery_attempts": 1,
        "stage_caps_are_cumulative": True,
    }
    value.pop("plan_sha256")
    return {**value, "plan_sha256": original.sha(original.canonical(value))}


def check_failure(output):
    for path, digest in FAILED_BINDINGS.items():
        original.safe_hash(output, path, digest)
    command = original.read(output, "audit_receipts/review_command.json")
    original.safe_hash(output, command["log"], command["log_sha256"])
    wall, rss = profile(output / command["profile"])
    text = (output / command["profile"]).read_text()
    if (
        command["name"] != "review"
        or command["exit_code"] != 1
        or wall != 6.19
        or rss != 482017280
        or "KeyError: 'derivative'" not in text
    ):
        raise ValueError("requires exact preserved schema interruption")
    return wall + 10


def execution_release(output):
    repo = Path(__file__).resolve().parents[1]
    for command in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"]):
        subprocess.run(command, cwd=repo, check=True)
    if any(
        os.environ.get(k) != "1"
        for k in (
            "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        )
    ):
        raise ValueError("requires all five one-thread settings")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    release = original.read(output, "audit_receipts/recovery_release.json")
    if (
        release["source_revision"] != revision
        or not release["all_applicable_ci_passed_before_merge"]
    ):
        raise ValueError("requires separately merged CI-passed recovery release")
    for path, digest in release["source_sha256"].items():
        original.safe_hash(repo, path, digest)
    # Preserve the original source release and every file it bound.
    prior = original.read(output, "audit_receipts/production_release.json")
    for path, digest in prior["source_sha256"].items():
        original.safe_hash(repo, path, digest)
    check_failure(output)
    return revision


def candidate_schema(panel):
    rows = []
    for row in panel["rows"]:
        items = []
        for item in row["differences"]:
            if any(k in item for k in ("fd", "derivative", "error")):
                raise ValueError("ambiguous legacy aliases are forbidden")
            items.append(
                {
                    **item,
                    "fd": item["surrogate_fd"],
                    "derivative": item["surrogate_derivative"],
                    "error": item["surrogate_error"],
                }
            )
        rows.append({**row, "differences": items})
    return {**panel, "rows": rows}


def review(panel, prior_audit, closed):
    result = original.review(candidate_schema(panel), prior_audit, closed)
    result.update(
        plan=plan_payload(),
        registered_schema_recovery=True,
        first_failed_review_charge_seconds=16.19,
        first_failed_review_profile_sha256=FAILED_BINDINGS["profiles/review.time"],
    )
    return result


def audit(panel, prior_audit, closed, report):
    if (
        report["plan"] != plan_payload()
        or not report["registered_schema_recovery"]
        or report["first_failed_review_charge_seconds"] != 16.19
        or report["first_failed_review_profile_sha256"] != FAILED_BINDINGS["profiles/review.time"]
    ):
        raise ValueError("independent recovery boundary differs")
    # Separate literal adapter, without the candidate schema or scalar functions.
    rows = []
    for row in panel["rows"]:
        items = []
        for item in row["differences"]:
            if set(item) & {"fd", "derivative", "error"}:
                raise ValueError("independent ambiguous schema")
            converted = dict(item)
            converted["error"] = item["surrogate_error"]
            converted["fd"] = item["surrogate_fd"]
            converted["derivative"] = item["surrogate_derivative"]
            items.append(converted)
        rows.append({**row, "differences": items})
    result = independent.reconstruct(
        {**panel, "rows": rows}, prior_audit, closed, {**report, "plan": original.plan_payload()}
    )
    result.update(
        review_sha256=original.sha(original.canonical(report)),
        registered_schema_recovery=True,
        first_failed_review_charge_seconds=16.19,
        first_failed_review_profile_sha256=FAILED_BINDINGS["profiles/review.time"],
    )
    return result


def close_resources(output, commands, report, audit_result):
    if [c["name"] for c in commands] != [
        "plan",
        "review",
        "recovery-plan",
        "review-recovery",
        "independent",
    ]:
        raise ValueError("requires one preserved failure and exactly one registered recovery")
    charges, peaks, hashes = {}, [original.peak_rss()], {}
    for c in commands:
        name = c["name"]
        if c["profile"] != "profiles/" + name + ".time" or c["log"] != "logs/" + name + ".log":
            raise ValueError("requires contained unique profiles/logs")
        original.safe_hash(output, c["profile"], c["profile_sha256"])
        original.safe_hash(output, c["log"], c["log_sha256"])
        wall, rss = profile(output / c["profile"])
        peaks.append(rss)
        hashes[name + ".time"] = c["profile_sha256"]
        if name not in ("plan", "recovery-plan"):
            receipt = (
                report
                if name == "review-recovery"
                else audit_result
                if name == "independent"
                else None
            )
            if c["exit_code"] == 0 and receipt is None:
                raise ValueError("successful review/audit receipt missing")
            charges[name] = max(wall + 10, receipt["charged_seconds"] if receipt else 0)
    cumulative = {
        "review": charges["review"] + charges["review-recovery"],
        "independent": charges["independent"],
    }
    total = sum(charges.values()) + 60
    if max(cumulative.values()) > 60 or total > 240 or max(peaks) > 1073741824:
        raise ValueError("unchanged cumulative caps exceeded")
    complete = all(c["exit_code"] == 0 for c in commands if c["name"] != "review")
    if commands[1]["exit_code"] != 1 or charges["review"] != 16.19:
        raise ValueError("original failed attempt and full charge must remain")
    if complete and (
        report["plan"] != plan_payload()
        or not audit_result["passed"]
        or audit_result["review_sha256"] != original.sha(original.canonical(report))
        or any(
            v[k] != expected
            for v in (report, audit_result)
            for k, expected in original.boundary_fields().items()
        )
    ):
        raise ValueError("complete recovered audit binding differs")
    return {
        "closed": True,
        "plan_sha256": plan_payload()["plan_sha256"],
        "charged_seconds": total,
        "paid_reservation_seconds": 60,
        "peak_rss_bytes": max(peaks),
        "stage_charges": charges,
        "cumulative_stage_charges": cumulative,
        "profile_sha256": hashes,
        "full_panel_review_complete": complete,
        "review_acceptance_passed": bool(complete and report["review_acceptance_passed"]),
        "original_fit_proxy_unchanged": report["original_fit_proxy_unchanged"]
        if complete
        else None,
        "failed_attempts": sum(c["exit_code"] != 0 for c in commands),
        "registered_schema_recovery": True,
        "recovery_attempts": 1,
        "next_slice": report["next_slice"] if complete else original.EVIDENCE_NEXT,
        "review_sha256": original.sha(original.canonical(report)) if report else None,
        "independent_audit_sha256": original.sha(original.canonical(audit_result))
        if audit_result
        else None,
        **original.boundary_fields(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("plan", "review", "audit", "close"), required=True)
    mode, rest = parser.parse_known_args(sys.argv[1:] if argv is None else argv)
    started = perf_counter()
    args, root, output = original.arguments(rest)
    if not args.execute:
        print(original.canonical(plan_payload()).decode(), end="")
        return 0
    name = {
        "review": "review.json",
        "audit": "independent_audit.json",
        "close": "resource_close.json",
    }[mode.mode]
    if (output / name).exists():
        raise ValueError("refuses to overwrite recovery output")
    revision = execution_release(output)
    bound = original.check_inputs(root)
    if mode.mode in ("review", "audit"):
        panel = original.read(root, "probe.json")
        from b4_23_independent_audit import journal_check

        journal_check(root, panel)
        if mode.mode == "review":
            result = review(panel, bound["independent_audit.json"], bound["resource_close.json"])
        else:
            report = original.read(output, "review.json")
            if report["source_revision"] != revision:
                raise ValueError("recovered review source differs")
            result = audit(
                panel, bound["independent_audit.json"], bound["resource_close.json"], report
            )
        original.check_inputs(root)
        prior_charge = 16.19 if mode.mode == "review" else 0
        if perf_counter() - started + 10 + prior_charge > 60:
            raise RuntimeError("unchanged cumulative stage cap exceeded")
        original.publish(output, name, result, revision, started)
    else:
        commands = original.read(output, "audit_receipts/execution_commands.json")
        report, audit_result = [
            original.read(output, p) if (output / p).exists() else None
            for p in ("review.json", "independent_audit.json")
        ]
        result = close_resources(output, commands, report, audit_result)
        result.update(
            source_revision=revision,
            closure_internal_charge_seconds=perf_counter() - started + 10,
            closure_internal_peak_rss_bytes=original.peak_rss(),
            execution_commands_sha256=original.sha(original.canonical(commands)),
        )
        result["peak_rss_bytes"] = max(
            result["peak_rss_bytes"], result["closure_internal_peak_rss_bytes"]
        )
        if result["closure_internal_charge_seconds"] > 60 or result["peak_rss_bytes"] > 1073741824:
            raise RuntimeError("unchanged closure cap exceeded")
        with (output / name).open("xb") as stream:
            stream.write(original.canonical(result))
        print(original.canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
