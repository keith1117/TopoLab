"""Read-only complete failed-panel arithmetic; no numerical candidate invocation."""

import argparse
import math
from pathlib import Path
from time import perf_counter

import numpy as np
from b4_14_generalist_method_review import (
    canonical,
    execution_release,
    peak_rss,
    read,
    roots,
    safe_hash,
    sha,
)
from b4_20_surrogate_correctness import FAIL_NEXT, direction_vector, selected_entries
from b4_20_surrogate_correctness import check_inputs as check_prior
from b4_20_surrogate_correctness import plan_payload as prior_plan

from topolab.baselines import _case_system
from topolab.simp import build_density_filter

VERSION = "topolab.b4_21.correctness-failure-review.v1"
NUMERICAL_NEXT = "B4.22 bounded stable-projection correctness probe"
REVIEW_NEXT = "B4.22 bounded correctness evidence review"
BINDINGS = {
    "audit_receipts/plan.json": "3ab9680cd27f416c04803c20a8da96195ae921508e63a1bb7c52e0d798e19c15",
    "audit_receipts/production_release.json": (
        "488f4a97d69d259d7fdb32dd6b8d5d547f214cb7caf531707f2294724f897ec2"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "536740f6f1dbf44d8b589ead279badf36f241bc8cb56e503dc7e54af826ed9f0"
    ),
    "probe.json": "8d5424601a51f1b7a4755f4a730ff40997a0cabed66be5fb6d4919ba1f231bbb",
    "probe.events.jsonl": "581757fc2cd043fbb5a06f878f370569a75129ca9c585991ff4643994a41cbe9",
    "independent_audit.json": "f54c3ae3815a8de7710d88d8b40202f4900adb94c66f8dfef14e541ee25fc718",
    "independent.events.jsonl": "18f0ae95e42a1e99b0d195d8bc1ba5b78f4937dd5bcf632906d5a5b6d5fe410e",
    "resource_close.json": "8fa693a39a1156cb600d87807e9de27222c8e580278b8ea23e21cb7ab2d45d66",
    "audit_receipts/execution_commands.json": (
        "7c3ca149a7e5ca0f58cd08a90f4ca0c82250380ff70c72e80c6a97e4214e66fa"
    ),
    "audit_receipts/closure_profile_verification.json": (
        "e0c9ba4033793b8c75a395c8ed088e70fbdae0fde3ce728e14a83dae0c944ce7"
    ),
    "audit_receipts/postexit_controller_reservation.json": (
        "d555de75c8b525e831135ee5cbeea3f450b0c7af68d9ff37312673690f462d66"
    ),
    "audit_receipts/evidence_release.json": (
        "96440ba458891b102c97945780c1e01ac24c5b4d4c981d0cddde052357071d90"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "f97bdc6dc6f1e3f5e27b6d35f9140c68e97b1121c27025a4526ee54e8ac877b0"
    ),
}


def plan_payload():
    value = {
        "version": VERSION,
        "bindings": BINDINGS,
        "prior_plan_sha256": prior_plan()["plan_sha256"],
        "cases": 8,
        "fixtures": 16,
        "directional_rows": 64,
        "original_conditions": 984,
        "original_failed_conditions": 1,
        "volume_tolerance": 1e-12,
        "fd_tolerance": 1e-4,
        "arithmetic_tolerance": 1e-12,
        "process_seconds": 60,
        "max_seconds": 240,
        "closure_seconds": 60,
        "max_rss_bytes": 1073741824,
        "solver_calls": 0,
        "new_projection_calls": 0,
        "label_model_byte_reads": 0,
        "fits": 0,
        "final_access": False,
    }
    return {**value, "plan_sha256": sha(canonical(value))}


def check_inputs(root):
    # Panel bytes are hash-bound here but parsed only after all metadata guards.
    for path, digest in BINDINGS.items():
        safe_hash(root, path, digest)
    bound = {
        p: read(root, p)
        for p in (
            "audit_receipts/plan.json",
            "resource_close.json",
            "independent_audit.json",
            "audit_receipts/evidence_release.json",
        )
    }
    closed, audit, release = (
        bound[p]
        for p in (
            "resource_close.json",
            "independent_audit.json",
            "audit_receipts/evidence_release.json",
        )
    )
    if (
        bound["audit_receipts/plan.json"] != prior_plan()
        or not closed["closed"]
        or not closed["full_panel_complete"]
        or closed["correctness_acceptance_passed"]
        or closed["charged_seconds"] != 100.30
        or closed["next_slice"] != FAIL_NEXT
        or not audit["passed"]
        or audit["correctness_passed"]
        or audit["numerical_conditions"] != 984
        or audit["failed_numerical_conditions"] != 1
        or audit["total_solver_calls"] != 32
        or audit["probe_sha256"] != BINDINGS["probe.json"]
        or not release["all_applicable_ci_passed_before_merge"]
        or not release["merged_tree_equals_tested_tree"]
        or release["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
        or any(
            v["final_access"] or v["repaired_gate"] or not v["old_fresh_sealed"]
            for v in (closed, audit, release)
        )
    ):
        raise ValueError("requires complete closed failed B4.20 and unchanged seals")
    for name, digest in closed["profile_sha256"].items():
        safe_hash(root, "profiles/" + name, digest)
    for name in ("closure_profile_verification", "postexit_controller_reservation"):
        proof = read(root, "audit_receipts/" + name + ".json")
        if not proof["passed"] or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]:
            raise ValueError("prior closure proof differs")
    check_prior(root.parent / "b4-19-local-compliance-surrogate", root.parent / "b3-v1-data")
    return bound


def review(probe, audit):
    entries = selected_entries()
    if probe["plan"] != prior_plan() or [c["case_id"] for c in probe["cases"]] != [
        e.case.case_id for e in entries
    ]:
        raise ValueError("complete ordered case population differs")
    rows, checks = [], []
    for entry, case in zip(entries, probe["cases"], strict=True):
        mesh, _, _ = _case_system(entry.case)
        filt = build_density_filter(mesh, entry.case.problem.optimization.filter_radius)
        g, anchor = np.asarray(case["design_gradient"]), np.asarray(case["anchor"])
        weights = np.asarray(filt.matrix.T @ (1 / filt.row_sums)) / g.size
        if g.shape != weights.shape or anchor.shape != g.shape or not np.all(np.isfinite(g)):
            raise ValueError("finite complete anchor gradient required")
        if [r["state"] for r in case["rows"]] != ["interior", "clipped"]:
            raise ValueError("complete ordered fixture population differs")
        for row in case["rows"]:
            free, design = np.asarray(row["free"], dtype=bool), np.asarray(row["design"])
            if free.shape != g.shape or design.shape != g.shape:
                raise ValueError("complete saved vector required")
            a, denominator = float(np.sum(g[free])), float(np.sum(weights[free]))
            if denominator <= 0 or not math.isfinite(denominator):
                raise ValueError("positive free volume derivative required")
            expected_gradient = np.where(free, g - weights * a / denominator, 0)
            checks.append(
                bool(np.allclose(row["gradient"], expected_gradient, rtol=1e-9, atol=1e-10))
            )
            arithmetic_scale = abs(case["intercept"]) + float(np.sum(abs(g * (design - anchor))))
            eps = np.finfo(np.float64).eps
            gamma = (g.size + 2) * eps / (1 - (g.size + 2) * eps)
            if [(d["direction"], d["step"]) for d in row["differences"]] != [
                (name, step) for name in ("sine", "cosine") for step in (1e-4, 2e-4)
            ]:
                raise ValueError("complete ordered directional population differs")
            for item in row["differences"]:
                plus, minus = item["values"]
                h = item["step"]
                fd = (plus - minus) / (2 * h)
                derivative = float(
                    np.asarray(row["gradient"]) @ direction_vector(g.size, item["direction"])
                )
                error = abs(fd - derivative) / max(abs(fd), abs(derivative), 1e-8)
                stable = all(np.array_equal(free, side) for side in item["free"])
                if not all(math.isfinite(x) for x in (plus, minus, fd, derivative, error)):
                    raise ValueError("finite directional scalars required")
                if (item["fd"], item["derivative"], item["error"]) != (fd, derivative, error):
                    raise ValueError("saved directional arithmetic differs")
                checks.append(stable)
                root_envelope = abs(a) * 1e-12 / (denominator * h)
                roundoff_envelope = gamma * arithmetic_scale / h
                envelope = root_envelope + roundoff_envelope
                rows.append(
                    {
                        "case_id": case["case_id"],
                        "state": row["state"],
                        "direction": item["direction"],
                        "step": h,
                        "values": item["values"],
                        "fd": fd,
                        "derivative": derivative,
                        "error": error,
                        "failed": error > 1e-4,
                        "stable_saved_masks": stable,
                        "absolute_discrepancy": abs(fd - derivative),
                        "free_gradient_sum": a,
                        "free_volume_derivative": denominator,
                        "root_tolerance_envelope": root_envelope,
                        "floating_arithmetic_envelope": roundoff_envelope,
                        "discrepancy_to_envelope": abs(fd - derivative) / envelope,
                        "paired_step_error": next(
                            d["error"]
                            for d in row["differences"]
                            if d["direction"] == item["direction"] and d["step"] != h
                        ),
                    }
                )
    failures = [r for r in rows if r["failed"]]
    if (
        len(rows) != 64
        or len(failures) != 1
        or audit["numerical_conditions"] != 984
        or audit["failed_numerical_conditions"] != 1
    ):
        raise ValueError("original failed panel completeness differs")
    passed = all(checks)
    compatible = all(r["discrepancy_to_envelope"] <= 1 for r in failures)
    return {
        "plan": plan_payload(),
        "rows": rows,
        "review_acceptance_passed": passed,
        "scalar_conditions": len(checks),
        "failed_scalar_conditions": sum(not c for c in checks),
        "original_conditions": 984,
        "original_failed_conditions": 1,
        "original_correctness_gate_passed": False,
        "original_charge_seconds_unchanged": 100.30,
        "failed_discrepancies_compatible_with_envelope": compatible,
        "cause_established": False,
        "side_offsets_and_volume_residuals": None,
        "next_slice": NUMERICAL_NEXT if passed and compatible else REVIEW_NEXT,
        "next_slice_started": False,
        "solver_calls": 0,
        "new_projection_calls": 0,
        "label_model_byte_reads": 0,
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
        "fit_proxy": None,
        "local_fidelity_evaluated": False,
        "full_fit_memory_feasibility_pending": True,
        "prior_b4_19_actual_counts_and_gap_still_unknown": True,
    }


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    root, output = args.probe_root.resolve(), args.output_root.resolve()
    roots(root, output)
    if args.execute and (
        (root.name, output.name)
        != ("b4-20-surrogate-correctness", "b4-21-correctness-failure-review")
        or root.parent != output.parent
    ):
        raise ValueError("requires fixed sibling external roots")
    return args, root, output


def publish(output, name, value, revision, started):
    value.update(
        source_revision=revision,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
    )
    if value["charged_seconds"] > 60 or value["peak_rss_bytes"] > 1073741824:
        raise RuntimeError("read-only review process cap exceeded")
    with (output / name).open("xb") as stream:
        stream.write(canonical(value))
    print(canonical({k: value[k] for k in ("charged_seconds", "next_slice")}).decode(), end="")


def main(argv=None):
    started = perf_counter()
    args, root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    if (output / "review.json").exists():
        raise ValueError("refuses to overwrite review")
    revision = execution_release(output)
    bound = check_inputs(root)
    result = review(read(root, "probe.json"), bound["independent_audit.json"])
    check_inputs(root)
    publish(output, "review.json", result, revision, started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
