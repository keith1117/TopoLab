"""Bounded method review of the closed, independently audited B4.13 rows."""

from __future__ import annotations

import argparse
import math
import os
import subprocess
from pathlib import Path
from time import perf_counter

from b4_11_polish_diagnosis import METHODS, canonical, costs, peak_rss, read, sha
from b4_13_preservation_diagnosis import check_inputs as check_screen
from b4_13_preservation_diagnosis import safe_hash

VERSION = "topolab.b4_14.generalist-method-review.v1"
SOURCE_PLAN = "165bdf5be73e3f62a719bf6931580ead53ed685f74b564aebb6dd1ecacd5094f"
DIAGNOSIS_SHA = "25e591c71968e10b46c49b61bdf9e4ebc3e7008a09f23d701176c85c83cbbb4e"
BINDINGS = {
    "audit_receipts/plan.json": "ff8780518984ca389ce220edb0e0f867896642823a6853246cd3c7ea0966a38f",
    "audit_receipts/production_release.json": (
        "eef7b7a2c2055d79dc16a2c8bbf3ce39d627d7d1d582ac7fdac555741b1a0443"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "46bd90fa71571b459d8be37cf4d6e8e21193b9415b8d5f66f79df2c50848ac04"
    ),
    "independent_audit.json": "ba4e118ed6a8b70e16fd91f646bd360fe1314fc6b0e763d642ab3444ca6f1b2a",
    "resource_close.json": "3114a774d7261c8039a21730bdd80acbfaa365deb04d87e081e21850cbe326b0",
    "audit_receipts/closure_profile_verification.json": (
        "b749ccd457ce992cf9a9647340710509b8171c01575be5288e7eeeee6e5b3766"
    ),
    "audit_receipts/evidence_release.json": (
        "ecdff20a49d5c3398bd2bbbb3f302dbce6cf31d5cb22b5dd71704c30579b6a7d"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "9b0c76f296f101e219351ef5b16300c8392e4e000581c020396fc6a6130d429a"
    ),
    "audit_receipts/execution_commands.json": (
        "aa03d6c1c374547b3769f104371a68e3697e0a68c386414c2fb336e309e472e1"
    ),
    "audit_receipts/closure_command.json": (
        "3e07c6745c50c807c148b415162ca011361670d8d8337ba8f6bd9e32dff88e05"
    ),
}
MECHANISMS = (
    "additional_fixed_continuation",
    "own_terminal_certificate_only",
    "perfect_failure_rejection",
    "complete_uniform_shadow",
    "paid_uniform_energy_input",
    "offline_direct_compliance_objective",
)
NEXT_SLICE = "B4.15 bounded offline compliance-adjoint feasibility probe"


def plan_payload():
    value = {
        "version": VERSION,
        "source_plan_sha256": SOURCE_PLAN,
        "source_diagnosis_sha256": DIAGNOSIS_SHA,
        "bindings": BINDINGS,
        "methods": list(METHODS),
        "cohorts": {"sentinel": [9, 108, 179, 24], "fresh": [48, 576, 922, 135]},
        "fixed_primary": 17,
        "mechanisms": list(MECHANISMS),
        "scenarios": ["measured", "fallback_free", "failed_to_uniform"],
        "analyses": ["all_retained_rows", "fixed_primary_cost_headroom", "uniform_shadow_floor"],
        "max_seconds": 180,
        "process_seconds": 60,
        "closure_seconds": 30,
        "max_rss_bytes": 1073741824,
        "solver_calls": 0,
        "raw_terminal_byte_reads": 0,
        "label_model_byte_reads": 0,
        "final_artifact_reads": 0,
        "length_or_threshold_search": False,
        "sources": [
            "https://arxiv.org/abs/1807.10787v3",
            "https://arxiv.org/abs/2012.05359v2",
            "https://arxiv.org/abs/2305.10460v1",
        ],
    }
    return {**value, "plan_sha256": sha(canonical(value))}


def check_inputs(root):
    """Metadata checks precede the single certified compact-row read."""
    bound = {p: read(root, p, d) for p, d in BINDINGS.items()}
    audit, closed, proof, evidence = (
        bound[p]
        for p in (
            "independent_audit.json",
            "resource_close.json",
            "audit_receipts/closure_profile_verification.json",
            "audit_receipts/evidence_release.json",
        )
    )
    if (
        bound["audit_receipts/plan.json"]["plan_sha256"] != SOURCE_PLAN
        or not audit["passed"]
        or audit["diagnosis_sha256"] != DIAGNOSIS_SHA
        or audit["terminal_classifications"] != 1101
        or audit["strata"] != 96
        or audit["same_specialist_pairs"] != 36
        or not closed["closed"]
        or not closed["diagnostic_acceptance_passed"]
        or closed["repaired_gate"]
        or closed["charged_seconds"] != 107.78
        or closed["diagnosis_sha256"] != DIAGNOSIS_SHA
        or not proof["passed"]
        or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]
        or not evidence["all_applicable_ci_passed_before_merge"]
        or not evidence["merged_tree_equals_tested_tree"]
        or evidence["repaired_gate"]
        or evidence["final_access"]
        or evidence["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
        or not closed["old_fresh_sealed"]
    ):
        raise ValueError("requires complete closed failed-primary B4.13 evidence")
    for name, digest in closed["profile_sha256"].items():
        safe_hash(root, "profiles/" + name, digest)
    safe_hash(root, "profiles/closure.time", proof["closure_profile_sha256"])
    # Historical receipt/index checks only; no original outcome/model/label reads.
    check_screen(root.parent / "b4-12-terminal-preservation")
    return bound


def margin(rows, scenario, limit):
    result = costs(rows, scenario)
    inverse_mean = math.fsum(1 / r["uniform_seconds"] for r in rows) / len(rows)
    return {
        **result,
        "mean_limit": limit,
        "signed_constant_overhead_seconds": (limit - result["mean_paired_ratio"]) / inverse_mean,
        "required_mean_ratio_reduction": max(0.0, result["mean_paired_ratio"] - limit),
    }


def primary_review(rows):
    primary = [r for r in rows if r["method"] == "P/17"]
    groups = {
        "all": primary,
        **{s: [r for r in primary if r["scale"] == s] for s in ("small", "large")},
        "large_y_generalist": [
            r
            for r in primary
            if (r["scale"], r["direction"], r["route"]) == ("large", "y", "generalist")
        ],
    }
    scenarios = {}
    for group, selected in groups.items():
        limit = 0.9 if group in ("small", "large") else 1.0
        scenarios[group] = {s: margin(selected, s, limit) for s in plan_payload()["scenarios"]}
    # Hypothetical full fresh-uniform shadow plus existing candidate work; its
    # nonnegative cost cannot be hidden by successful selection of uniform.
    shadow = {
        name: {
            "cases": len(group),
            "mean_ratio_floor": math.fsum(
                1 + (r["seconds"] - r["fallback_seconds"]) / r["uniform_seconds"] for r in group
            )
            / len(group),
            "every_query_floor_above_uniform": all(
                r["seconds"] - r["fallback_seconds"] > 0 for r in group
            ),
            "diagnostic_only": True,
        }
        for name, group in groups.items()
    }
    target = groups["large_y_generalist"]
    return {
        "scenarios": scenarios,
        "complete_uniform_shadow": shadow,
        "target_rows": target,
        "slow_accepted_targets": [
            {
                "case_id": r["case_id"],
                "ratio": r["seconds"] / r["uniform_seconds"],
                "performed_updates": r["performed_iterations"],
                "uniform_updates": next(
                    u["performed_iterations"]
                    for u in rows
                    if u["case_id"] == r["case_id"] and u["method"] == "uniform"
                ),
            }
            for r in target
            if r["candidate"]["succeeded"] and r["seconds"] > r["uniform_seconds"]
        ],
    }


def review(diagnosis):
    cohorts = {}
    for name, expected in plan_payload()["cohorts"].items():
        source = diagnosis["cohorts"][name]
        rows = source["rows"]
        case_ids = {r["case_id"] for r in rows}
        if (
            [
                source["cases"],
                len(rows),
                source["terminal_classifications"],
                sum(r["before"] is not None for r in rows),
            ]
            != expected
            or len(case_ids) != expected[0]
            or len({(r["case_id"], r["method"]) for r in rows}) != len(rows)
            or any(
                {r["method"] for r in rows if r["case_id"] == cid} != set(METHODS)
                for cid in case_ids
            )
        ):
            raise ValueError("complete certified row population differs")
        for row in rows:
            if (
                not all(
                    math.isfinite(row[k])
                    for k in ("seconds", "uniform_seconds", "fallback_seconds")
                )
                or row["seconds"] <= 0
                or row["uniform_seconds"] <= 0
                or not 0 <= row["fallback_seconds"] < row["seconds"]
                or (row["fallback"] is not None) == row["candidate"]["succeeded"]
            ):
                raise ValueError("certified status or complete cost differs")
        cohorts[name] = {
            "cases": source["cases"],
            "rows": len(rows),
            "prior_terminal_classifications": source["terminal_classifications"],
            "retained_strata": source["strata"],
            "scientific_decision": source["scientific_decision"],
            "failures": {
                m: sum(not r["candidate"]["succeeded"] for r in rows if r["method"] == m)
                for m in METHODS
            },
            "fixed_primary": primary_review(rows),
        }
    failed = [
        r
        for r in diagnosis["cohorts"]["fresh"]["rows"]
        if r["method"] == "P/17" and not r["candidate"]["succeeded"]
    ]
    if (
        diagnosis["next_mechanism"] != "generalist_reliability_refinement_method_review"
        or diagnosis["repaired_gate"]
        or diagnosis["final_access"]
        or not diagnosis["old_fresh_sealed"]
        or not failed
        or not all(
            r["triggered"]
            and r["added_updates"] == 20
            and r["candidate"]["converged"]
            and r["candidate"]["quality_reasons"] == ["compliance_above_matched_uniform"]
            and not r["before"]["succeeded"]
            and r["endpoint"]["compliance_ratio"] < r["before"]["compliance_ratio"]
            for r in failed
        )
    ):
        raise ValueError("frozen quality-basin method-review condition differs")
    return {
        "plan": plan_payload(),
        "cohorts": cohorts,
        "mechanism_dispositions": dict(
            zip(
                MECHANISMS,
                (
                    "no_length_search_or_repair_evidence",
                    "observed_own_certificates_do_not_establish_reference_quality",
                    "optimistic_failure_rejection_leaves_accepted_refinement_cost",
                    "full_uniform_plus_candidate_cannot_accelerate",
                    "prior_B2_19_failure_no_retest_without_new_mechanism",
                    "one_separately_registered_offline_adjoint_feasibility_probe",
                ),
                strict=True,
            )
        ),
        "next_slice": NEXT_SLICE,
        "next_slice_started": False,
        "repaired_gate": False,
        "final_access": False,
        "old_fresh_sealed": True,
        "prior_b4_13_charge_seconds_unchanged": 107.78,
        "claim": "method_review_only_not_repair_or_acceleration",
    }


def execution_release(output):
    repository = Path(__file__).resolve().parents[1]
    if any(
        subprocess.run(c, cwd=repository, check=False).returncode
        for c in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"])
    ):
        raise ValueError("requires clean committed source")
    if any(
        os.environ.get(k) != "1"
        for k in (
            "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
        )
    ):
        raise ValueError("requires one BLAS/OpenMP thread")
    release = read(output, "audit_receipts/production_release.json")
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    if (
        release["source_revision"] != revision
        or not release["all_applicable_ci_passed_before_merge"]
    ):
        raise ValueError("requires CI-passed merged source release")
    for path, digest in release["source_sha256"].items():
        safe_hash(repository, path, digest)
    return revision


def roots(root, output):
    repository = Path(__file__).resolve().parents[1]
    if root.is_relative_to(repository) or output.is_relative_to(repository):
        raise ValueError("evidence roots must be outside repository")
    if root.is_relative_to(output) or output.is_relative_to(root):
        raise ValueError("output must be separate from immutable input")


def main(argv=None):
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnosis-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    root, output = args.diagnosis_root.resolve(), args.output_root.resolve()
    roots(root, output)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    if (root.name, output.name) != (
        "b4-13-preservation-diagnosis",
        "b4-14-generalist-method-review",
    ) or root.parent != output.parent:
        raise ValueError("execution requires fixed sibling evidence roots")
    target = output / "review.json"
    if target.exists():
        raise ValueError("refuses to overwrite method review")
    revision = execution_release(output)
    check_inputs(root)
    diagnosis = read(root, "diagnosis.json", DIAGNOSIS_SHA)
    report = review(diagnosis)
    check_inputs(root)
    report.update(
        source_revision=revision,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
        input_sha256=DIAGNOSIS_SHA,
    )
    if report["charged_seconds"] > 60 or report["peak_rss_bytes"] > 1073741824:
        raise RuntimeError("method review resource cap exceeded")
    with target.open("xb") as stream:
        stream.write(canonical(report))
    print(
        canonical(
            {k: report[k] for k in ("next_slice", "claim", "charged_seconds", "peak_rss_bytes")}
        ).decode(),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
