"""Separate scalar reconstruction; geometry weights without the production filter."""

import math
from time import perf_counter

from b4_21_correctness_failure_review import (
    NUMERICAL_NEXT,
    REVIEW_NEXT,
    arguments,
    canonical,
    check_inputs,
    execution_release,
    plan_payload,
    publish,
    read,
    selected_entries,
    sha,
)


def volume_weights(case):
    counts = case.problem.mesh.element_counts
    spacing = [
        length / count for length, count in zip(case.problem.mesh.lengths, counts, strict=True)
    ]
    radius = case.problem.optimization.filter_radius
    widths = [int(math.floor(radius / step)) for step in spacing]
    nx, ny, nz = counts
    n = nx * ny * nz
    contributions = [[] for _ in range(n)]
    for z in range(nz):
        for y in range(ny):
            for x in range(nx):
                neighbors = []
                for dz in range(max(-widths[2], -z), min(widths[2], nz - 1 - z) + 1):
                    for dy in range(max(-widths[1], -y), min(widths[1], ny - 1 - y) + 1):
                        for dx in range(max(-widths[0], -x), min(widths[0], nx - 1 - x) + 1):
                            distance = math.sqrt(
                                math.fsum(
                                    (d * s) ** 2 for d, s in zip((dx, dy, dz), spacing, strict=True)
                                )
                            )
                            weight = max(0.0, radius - distance)
                            if weight > 0:
                                neighbors.append((x + dx + nx * (y + dy + ny * (z + dz)), weight))
                total = math.fsum(w for _, w in neighbors)
                for j, weight in neighbors:
                    contributions[j].append(weight / total / n)
    return [math.fsum(values) for values in contributions]


def reconstruct(probe, prior_audit, report):
    entries = selected_entries()
    if report["plan"] != plan_payload() or [c["case_id"] for c in probe["cases"]] != [
        e.case.case_id for e in entries
    ]:
        raise ValueError("independent case/plan population differs")
    checks, rows, gradient_passes, stable_passes = [], [], [], []
    for entry, case in zip(entries, probe["cases"], strict=True):
        weights = volume_weights(entry.case)
        g, anchor = case["design_gradient"], case["anchor"]
        if len(g) != len(weights) or len(anchor) != len(g):
            raise ValueError("independent complete anchor required")
        if [r["state"] for r in case["rows"]] != ["interior", "clipped"]:
            raise ValueError("independent fixture population differs")
        n = len(g)
        for state in case["rows"]:
            free = state["free"]
            if any(len(state[k]) != n for k in ("free", "design", "gradient")):
                raise ValueError("independent complete state required")
            a = math.fsum(value for value, active in zip(g, free, strict=True) if active)
            denominator = math.fsum(w for w, active in zip(weights, free, strict=True) if active)
            if denominator <= 0:
                raise ValueError("independent positive free volume derivative required")
            gradient_passes.append(
                all(
                    abs(actual - (value - w * a / denominator if active else 0))
                    <= 1e-10 + 1e-9 * abs(value - w * a / denominator if active else 0)
                    for actual, value, w, active in zip(
                        state["gradient"], g, weights, free, strict=True
                    )
                )
            )
            scale = abs(case["intercept"]) + math.fsum(
                abs(value * (design - origin))
                for value, design, origin in zip(g, state["design"], anchor, strict=True)
            )
            eps = 2.0**-52
            gamma = (n + 2) * eps / (1 - (n + 2) * eps)
            if [(d["direction"], d["step"]) for d in state["differences"]] != [
                (direction, h) for direction in ("sine", "cosine") for h in (1e-4, 2e-4)
            ]:
                raise ValueError("independent complete differences required")
            for item in state["differences"]:
                values, h = item["values"], item["step"]
                vector = [
                    (math.sin if item["direction"] == "sine" else math.cos)(
                        (0.37 if item["direction"] == "sine" else 0.13) * i
                    )
                    for i in range(1, n + 1)
                ]
                maximum = max(abs(v) for v in vector)
                derivative = math.fsum(
                    v * d / maximum for v, d in zip(state["gradient"], vector, strict=True)
                )
                fd = (values[0] - values[1]) / (2 * h)
                checks.append(
                    math.isclose(derivative, item["derivative"], rel_tol=1e-9, abs_tol=1e-10)
                )
                # Original error is reconstructed from its exact saved dot product;
                # the separate fsum product above checks that retained derivative.
                old_derivative = item["derivative"]
                discrepancy = abs(fd - old_derivative)
                error = discrepancy / max(abs(fd), abs(old_derivative), 1e-8)
                if item["fd"] != fd or item["error"] != error:
                    raise ValueError("independent retained arithmetic differs")
                stable = item["free"] == [free, free]
                stable_passes.append(stable)
                root_bound = abs(a) * 1e-12 / (denominator * h)
                floating_bound = gamma * scale / h
                rows.append(
                    {
                        "case_id": case["case_id"],
                        "state": state["state"],
                        "direction": item["direction"],
                        "step": h,
                        "values": values,
                        "fd": fd,
                        "derivative": old_derivative,
                        "error": error,
                        "failed": error > 1e-4,
                        "stable_saved_masks": stable,
                        "absolute_discrepancy": discrepancy,
                        "free_gradient_sum": a,
                        "free_volume_derivative": denominator,
                        "root_tolerance_envelope": root_bound,
                        "floating_arithmetic_envelope": floating_bound,
                        "discrepancy_to_envelope": discrepancy / (root_bound + floating_bound),
                        "paired_step_error": next(
                            d["error"]
                            for d in state["differences"]
                            if d["direction"] == item["direction"] and d["step"] != h
                        ),
                    }
                )
    if len(rows) != 64 or len(report["rows"]) != 64:
        raise ValueError("independent complete scalar rows required")
    for expected, actual in zip(rows, report["rows"], strict=True):
        if expected.keys() != actual.keys():
            raise ValueError("independent row schema differs")
        for key, value in expected.items():
            checks.append(
                math.isclose(value, actual[key], rel_tol=1e-12, abs_tol=1e-12)
                if type(value) is float
                else value == actual[key]
            )
    passed = all(gradient_passes + stable_passes)
    compatible = all(r["discrepancy_to_envelope"] <= 1 for r in rows if r["failed"])
    next_slice = NUMERICAL_NEXT if passed and compatible else REVIEW_NEXT
    expected_fields = {
        "review_acceptance_passed": passed,
        "failed_discrepancies_compatible_with_envelope": compatible,
        "scalar_conditions": 80,
        "failed_scalar_conditions": sum(not c for c in gradient_passes + stable_passes),
        "original_conditions": 984,
        "original_failed_conditions": 1,
        "original_correctness_gate_passed": False,
        "original_charge_seconds_unchanged": 100.30,
        "cause_established": False,
        "side_offsets_and_volume_residuals": None,
        "next_slice": next_slice,
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
    if (
        sum(r["failed"] for r in rows) != 1
        or prior_audit["numerical_conditions"] != 984
        or prior_audit["failed_numerical_conditions"] != 1
        or not all(checks)
        or any(report[k] != v for k, v in expected_fields.items())
    ):
        raise ValueError("independent complete review arithmetic/boundary differs")
    return {
        "passed": True,
        "independent_scalar_conditions": len(checks),
        "cases": 8,
        "fixtures": 16,
        "directional_rows": 64,
        "review_sha256": sha(canonical(report)),
        "next_slice": next_slice,
        **{k: v for k, v in expected_fields.items() if k != "scalar_conditions"},
    }


def main(argv=None):
    started = perf_counter()
    args, root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    if (output / "independent_audit.json").exists():
        raise ValueError("refuses to overwrite independent audit")
    revision = execution_release(output)
    bound = check_inputs(root)
    report = read(output, "review.json")
    if report["source_revision"] != revision:
        raise ValueError("independent execution source differs")
    result = reconstruct(read(root, "probe.json"), bound["independent_audit.json"], report)
    check_inputs(root)
    publish(output, "independent_audit.json", result, revision, started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
