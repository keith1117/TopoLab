"""Read-only reconstruction of the complete saved B4.23 finite panel."""

import argparse
import math
import os
from pathlib import Path
from time import perf_counter

import numpy as np
from b4_14_generalist_method_review import (
    canonical,
    peak_rss,
    read,
    roots,
    safe_hash,
    sha,
)
from b4_14_generalist_method_review import execution_release as prior_execution_release
from b4_23_versioned_surrogate_feasibility import (
    CORRECTNESS_NEXT,
    direction_vector,
    selected_entries,
    state_specs,
)
from b4_23_versioned_surrogate_feasibility import check_inputs as check_prior
from b4_23_versioned_surrogate_feasibility import plan_payload as prior_plan

from topolab.baselines import _case_system
from topolab.simp import build_density_filter

VERSION = "topolab.b4_24.versioned-correctness-failure-review.v1"
METHOD_NEXT = "B4.25 bounded active-set objective-method review"
EVIDENCE_NEXT = "B4.25 bounded versioned correctness evidence review"
BINDINGS = {
    "audit_receipts/plan.json": "7fb8e8c29d59ea1a85e3457ce8a5218709362a44a7b59647b354e3c158dd3590",
    "audit_receipts/production_release.json": (
        "045eb0811072191277c65bc0caac39457a28415947a927f285f7096b03e5ae4c"
    ),
    "probe.json": "211bec69650f8b3783a29527d9621eec05173ed952b8f5b7f70f0f3ee1287608",
    "audit_receipts/source_final_head_ci.json": (
        "f3e05e41d85d550cbed65a12e6e30d1b950456bb9d009116d30adaafc0817d31"
    ),
    "audit_receipts/source_main_ci.json": (
        "e8da6d35ee6b2d985e1ee67df02c093ee44c6e13a9fcd12b1dd85ea5ca8a85b6"
    ),
    "independent_audit.json": "445d51fef08191b0e988bb9c76a1863a061c4e392db35c5a76ff812234942440",
    "audit_receipts/evidence_metadata_summary.json": (
        "9a9648dc5de4aab4ff613b42ad9eefd13fc65fb86fdf4126069da51eed0c41a6"
    ),
    "resource_close.json": "5b7f5440a81922fb6afa65c6976dac74552b33f64a6d29e46702ca2f3c4f9276",
    "audit_receipts/execution_commands.json": (
        "2ed99417285cf26f1475240a78f9969fed0b5ffde7886c7dc834e81f2db182e2"
    ),
    "audit_receipts/closure_profile_verification.json": (
        "06c253844a8f10146c2e2f71a552ead151cfe970b6d0d2560cd589127050137c"
    ),
    "audit_receipts/postexit_controller_reservation.json": (
        "b7be4064b40c82bf6b96b3e6eaf357763d21719c4ba657f1f8bd31283fb2b36a"
    ),
    "probe.events.jsonl": "e6d9438c0d26d69f26ab1f02f4d51b9fd836305ee965b7789e5a58469dc2d0b9",
    "independent.events.jsonl": "a5a66a7336d720648a4770a7643ab919d6fec15934baab225d22b4893c3611a5",
    "audit_receipts/evidence_release.json": (
        "bbe76feb3ef04d1454f5fe0f3cb1700a8e5caad2d8bad447c10ee90362626829"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "b409f44ec6bdedc7e250a84dcb776dedf7a125b52402986995ff35336b3ada2d"
    ),
    "audit_receipts/evidence_main_ci.json": (
        "1bf84aba31aba0106046741a278b48a8205d37b70ec15cb6e07e02bca88f5427"
    ),
}


def plan_payload():
    value = {
        "version": VERSION,
        "bindings": BINDINGS,
        "prior_plan_sha256": prior_plan()["plan_sha256"],
        "cases": 8,
        "central_states": 72,
        "side_states": 128,
        "directional_rows": 64,
        "retained_measurements": 216,
        "original_conditions": 3976,
        "original_failed_conditions": 69,
        "original_mask_failures": 35,
        "original_fd_failures": 34,
        "fd_tolerance": 1e-4,
        "fd_floor": 1e-8,
        "arithmetic_tolerance": 1e-12,
        "process_seconds": 60,
        "max_seconds": 240,
        "closure_seconds": 60,
        "max_rss_bytes": 1073741824,
        "prior_charged_seconds": [
            84.33,
            55.99,
            112.34,
            86.13,
            73.93,
            100.30,
            90.27,
            104.62,
            143.47,
        ],
        "solver_calls": 0,
        "new_projection_calls": 0,
        "new_objective_gradient_calls": 0,
        "new_timing_measurements": 0,
        "label_model_byte_reads": 0,
        "fits": 0,
        "final_access": False,
    }
    return {**value, "plan_sha256": sha(canonical(value))}


def check_inputs(root):
    # Immutable saved bytes are parsed only during the released execution.
    for path, digest in BINDINGS.items():
        safe_hash(root, path, digest)
    bound = {
        p: read(root, p)
        for p in (
            "resource_close.json",
            "independent_audit.json",
            "audit_receipts/evidence_release.json",
        )
    }
    closed, audit, release = bound.values()
    if (
        read(root, "audit_receipts/plan.json") != prior_plan()
        or not closed["closed"]
        or not closed["full_panel_complete"]
        or closed["integrity_passed"]
        or closed["feasibility_passed"]
        or closed["charged_seconds"] != 143.47
        or closed["next_slice"] != CORRECTNESS_NEXT
        or closed["fit_proxy"]["cost_feasible"]
        or not audit["passed"]
        or audit["metadata_only"]
        or audit["integrity_passed"]
        or audit["numerical_conditions"] != 3976
        or audit["failed_numerical_conditions"] != 69
        or audit["arithmetic_conditions"] != 960
        or audit["probe_sha256"] != BINDINGS["probe.json"]
        or not release["all_applicable_ci_passed_before_merge"]
        or not release["merged_tree_equals_tested_tree"]
        or release["ci_sha256"] != BINDINGS["audit_receipts/evidence_final_head_ci.json"]
        or release["main_ci_sha256"] != BINDINGS["audit_receipts/evidence_main_ci.json"]
        or any(
            v["final_access"] or v["repaired_gate"] or not v["old_fresh_sealed"]
            for v in (closed, audit, release)
        )
    ):
        raise ValueError("requires complete closed failed B4.23 and unchanged seals")
    for name, digest in closed["profile_sha256"].items():
        safe_hash(root, "profiles/" + name, digest)
    for name in ("closure_profile_verification", "postexit_controller_reservation"):
        proof = read(root, "audit_receipts/" + name + ".json")
        if not proof["passed"] or proof["resource_close_sha256"] != BINDINGS["resource_close.json"]:
            raise ValueError("prior native resource proof differs")
    check_prior(root.parent / "b4-22-stable-projection-correctness", root.parent / "b3-v1-data")
    return bound


def condition_map():
    rows, position = [], 0
    for entry in selected_entries():
        position += 9
        for state in range(9):
            position += 24
            if state in (0, 4):
                for direction in ("sine", "cosine"):
                    for step in (1e-4, 2e-4):
                        rows.append(
                            {
                                "case_id": entry.case.case_id,
                                "state": state,
                                "direction": direction,
                                "step": step,
                                "mask_condition": position + 32,
                                "fd_condition": position + 33,
                            }
                        )
                        position += 34
    assert position == 3976
    return rows


def saved_state_checks(
    state, raw, gradient, weights, target, minimum, value, signed, anchor, intercept
):
    design, physical, free = [np.asarray(state[k]) for k in ("design", "physical", "free")]
    free = free.astype(bool)
    n = len(raw)
    if any(v.shape != (n,) for v in (design, physical, free, gradient, signed, anchor, weights)):
        raise ValueError("complete saved vectors required")
    if not all(np.all(np.isfinite(v)) for v in (raw, design, physical, gradient, signed, anchor)):
        raise ValueError("finite saved vectors required")
    shifted = raw + state["projection"]["offset"]
    denominator = float(weights[free].sum())
    if denominator <= 0:
        raise ValueError("positive saved free volume derivative required")
    cotangent = np.where(free, signed - weights * signed[free].sum() / denominator, 0)
    arithmetic = intercept + float(signed @ (design - anchor))
    info = state["projection"]
    return [
        bool(np.allclose(design, np.clip(shifted, minimum, 1), rtol=0, atol=2e-11)),
        bool(np.array_equal(free, (shifted > minimum) & (shifted < 1))),
        math.isclose(
            info["weighted_volume_residual"],
            float(weights @ design) - target,
            rel_tol=0,
            abs_tol=1e-12,
        ),
        math.isclose(
            info["physical_volume_residual"],
            float(physical.mean()) - target,
            rel_tol=0,
            abs_tol=1e-12,
        ),
        math.isclose(
            info["kink_margin"],
            float(np.minimum(abs(shifted - minimum), abs(shifted - 1)).min()),
            rel_tol=0,
            abs_tol=1e-12,
        ),
        math.isclose(value, arithmetic, rel_tol=1e-12, abs_tol=1e-12),
        bool(np.allclose(gradient, cotangent, rtol=1e-9, atol=1e-10)),
    ]


def decompose(row, item, signed, weights):
    h = item["step"]
    free, design = np.asarray(row["free"], dtype=bool), np.asarray(row["design"])
    vector = direction_vector(len(signed), item["direction"])
    plus, minus = item["sides"]
    sides = [np.asarray(s["physics"]["design"]) for s in (plus, minus)]
    offset = row["projection"]["offset"]
    departures = [
        sides[k] - design - free * (sign * h * vector + side["projection"]["offset"] - offset)
        for k, (side, sign) in enumerate(zip((plus, minus), (1, -1), strict=True))
    ]
    a, denominator = float(signed[free].sum()), float(weights[free].sum())
    ratio = a / denominator
    tangent = free * (vector - float(weights[free] @ vector[free]) / denominator)
    chord = (sides[0] - sides[1]) / (2 * h)
    clipping = float((signed - weights * ratio) @ ((departures[0] - departures[1]) / (2 * h)))
    volume = ratio * float(weights @ (sides[0] - sides[1])) / (2 * h)
    chord_derivative, tangent_derivative = float(signed @ chord), float(signed @ tangent)
    fd = (plus["surrogate"] - minus["surrogate"]) / (2 * h)
    derivative = item["derivative"]
    value_roundoff = fd - chord_derivative
    gradient_roundoff = tangent_derivative - derivative
    discrepancy = fd - derivative
    # Conservative forward arithmetic envelope; no scientific tolerance changes.
    eps = float(np.finfo(np.float64).eps)
    operations = 8 * len(signed) + 64
    gamma = operations * eps / (1 - operations * eps)
    scale = (
        1
        + abs(plus["surrogate"])
        + abs(minus["surrogate"])
        + abs(derivative) * h
        + float(abs(signed).sum())
        + abs(ratio)
    )
    envelope = gamma * scale / h
    stable = all(s["free"] == row["free"] for s in (plus, minus))
    error = abs(discrepancy) / max(abs(fd), abs(derivative), 1e-8)
    return {
        "fd": fd,
        "derivative": derivative,
        "error": error,
        "fd_failed": error > 1e-4,
        "mask_failed": not stable,
        "exact_fd": (plus["exact"] - minus["exact"]) / (2 * h),
        "exact_derivative": item["exact_derivative"],
        "signed_discrepancy": discrepancy,
        "projected_chord_derivative": chord_derivative,
        "central_tangent_derivative": tangent_derivative,
        "clipping_departure_contribution": clipping,
        "volume_residual_contribution": volume,
        "saved_value_roundoff_contribution": value_roundoff,
        "saved_gradient_roundoff_contribution": gradient_roundoff,
        "decomposition_residual": discrepancy
        - clipping
        - volume
        - value_roundoff
        - gradient_roundoff,
        "arithmetic_envelope": envelope,
        "clipping_accounts_for_gap_within_arithmetic_envelope": abs(discrepancy - clipping)
        <= envelope,
        "changed_plus_components": sum(
            p != c for p, c in zip(plus["free"], row["free"], strict=True)
        ),
        "changed_minus_components": sum(
            p != c for p, c in zip(minus["free"], row["free"], strict=True)
        ),
        "offsets": [
            row["projection"]["offset"],
            plus["projection"]["offset"],
            minus["projection"]["offset"],
        ],
        "weighted_residuals": [
            row["projection"]["weighted_volume_residual"],
            plus["projection"]["weighted_volume_residual"],
            minus["projection"]["weighted_volume_residual"],
        ],
    }


def boundary_fields():
    return {
        "original_conditions": 3976,
        "original_failed_conditions": 69,
        "original_correctness_gate_passed": False,
        "original_feasibility_gate_passed": False,
        "original_charge_seconds_unchanged": 143.47,
        "prior_charged_seconds_unchanged": plan_payload()["prior_charged_seconds"],
        "next_slice_started": False,
        "solver_calls": 0,
        "new_projection_calls": 0,
        "new_objective_gradient_calls": 0,
        "new_timing_measurements": 0,
        "label_model_byte_reads": 0,
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
        "global_cause_or_gradient_failure_established": False,
        "full_fit_memory_feasibility_pending": True,
        "prior_b4_19_actual_counts_and_gap_still_unknown": True,
    }


def review(panel, audit, closed):
    entries = selected_entries()
    specs = [list(s) for s in state_specs()]
    if (
        panel["plan"] != prior_plan()
        or [s["case_id"] for s in panel["labels"]] != [e.case.case_id for e in entries]
        or [(r["case_id"], r["state"], r["spec"]) for r in panel["rows"]]
        != [(e.case.case_id, j, s) for e in entries for j, s in enumerate(specs)]
        or audit["numerical_conditions"] != 3976
        or audit["failed_numerical_conditions"] != 69
        or len(audit["condition_results"]) != 3976
        or [i for i, v in enumerate(audit["condition_results"]) if not v]
        != audit["failed_condition_indices"]
    ):
        raise ValueError("complete ordered failed panel differs")
    rows, checks, original_indices, mapping = [], [], [], condition_map()
    for entry, label in zip(entries, panel["labels"], strict=True):
        mesh, _, _ = _case_system(entry.case)
        filt = build_density_filter(mesh, entry.case.problem.optimization.filter_radius)
        weights = np.asarray(filt.matrix.T @ (1 / filt.row_sums)) / filt.row_sums.size
        signed, anchor = np.asarray(label["design_gradient"]), np.asarray(label["anchor"])
        settings = entry.case.problem.optimization
        for row in [r for r in panel["rows"] if r["case_id"] == label["case_id"]]:
            raw, gradient = np.asarray(row["raw"]), np.asarray(row["gradient"])
            checks += saved_state_checks(
                row,
                raw,
                gradient,
                weights,
                settings.volume_fraction,
                settings.minimum_density,
                row["surrogate"],
                signed,
                anchor,
                label["intercept"],
            )
            expected = [(d, h) for d in ("sine", "cosine") for h in (1e-4, 2e-4)]
            if (
                [(d["direction"], d["step"]) for d in row["differences"]]
                != (expected if row["state"] in (0, 4) else [])
                or len(row["timings"]) != 3
                or [t["repeat"] for t in row["timings"]] != [0, 1, 2]
            ):
                raise ValueError("complete fixed directions and first-inclusive timings required")
            for item in row["differences"]:
                vector = direction_vector(len(signed), item["direction"])
                if len(item["sides"]) != 2:
                    raise ValueError("both saved sides required")
                for side, sign in zip(item["sides"], (1, -1), strict=True):
                    checks += saved_state_checks(
                        {**side["physics"], "projection": side["projection"]},
                        raw + sign * item["step"] * vector,
                        np.asarray(side["gradient"]),
                        weights,
                        settings.volume_fraction,
                        settings.minimum_density,
                        side["surrogate"],
                        signed,
                        anchor,
                        label["intercept"],
                    )
                    checks.append(side["free"] == side["physics"]["free"])
                result = {**mapping[len(rows)], **decompose(row, item, signed, weights)}
                checks += [
                    item["fd"] == result["fd"],
                    item["error"] == result["error"],
                    item["same_active_set"] == (not result["mask_failed"]),
                    item["exact_fd"] == result["exact_fd"],
                    math.isclose(
                        float(gradient @ vector), item["derivative"], rel_tol=1e-9, abs_tol=1e-10
                    ),
                    math.isclose(
                        float(np.asarray(row["exact_gradient"]) @ vector),
                        item["exact_derivative"],
                        rel_tol=1e-9,
                        abs_tol=1e-10,
                    ),
                    abs(result["decomposition_residual"]) <= result["arithmetic_envelope"],
                ]
                for key in ("mask", "fd"):
                    index = result[key + "_condition"]
                    checks.append(
                        audit["condition_results"][index] == (not result[key + "_failed"])
                    )
                    if result[key + "_failed"]:
                        original_indices.append(index)
                rows.append(result)
    if (
        len(rows) != 64
        or sorted(original_indices) != audit["failed_condition_indices"]
        or sum(r["mask_failed"] for r in rows) != 35
        or sum(r["fd_failed"] for r in rows) != 34
    ):
        raise ValueError("every original failure must retain its exact condition identity")
    explained = all(
        r["mask_failed"] and r["clipping_accounts_for_gap_within_arithmetic_envelope"]
        for r in rows
        if r["fd_failed"]
    )
    passed = all(checks)
    return {
        "plan": plan_payload(),
        "rows": rows,
        "review_acceptance_passed": passed,
        "scalar_conditions": len(checks),
        "failed_scalar_conditions": sum(not c for c in checks),
        "mask_failures": 35,
        "fd_failures": 34,
        "overlapping_mask_and_fd_failures": sum(r["mask_failed"] and r["fd_failed"] for r in rows),
        "all_fd_failures_have_saved_clipping_explanation": explained,
        "original_fit_proxy_unchanged": closed["fit_proxy"],
        "retained_measurements": 216,
        "next_slice": METHOD_NEXT if passed and explained else EVIDENCE_NEXT,
        **boundary_fields(),
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
        != ("b4-23-versioned-surrogate-feasibility", "b4-24-versioned-correctness-failure-review")
        or root.parent != output.parent
    ):
        raise ValueError("requires fixed sibling external roots")
    return args, root, output


def execution_release(output):
    if os.environ.get("NUMEXPR_NUM_THREADS") != "1":
        raise ValueError("requires all five frozen thread settings")
    return prior_execution_release(output)


def publish(output, name, value, revision, started):
    value.update(
        source_revision=revision,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
    )
    if value["charged_seconds"] > 60 or value["peak_rss_bytes"] > 1073741824:
        raise RuntimeError("read-only process cap exceeded")
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
    panel = read(root, "probe.json")
    from b4_23_independent_audit import journal_check

    journal_check(root, panel)  # Saved-context verification, zero new numerical invocation.
    result = review(panel, bound["independent_audit.json"], bound["resource_close.json"])
    check_inputs(root)
    publish(output, "review.json", result, revision, started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
