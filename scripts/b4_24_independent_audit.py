"""Separate scalar secant reconstruction from immutable saved arrays."""

import math
from time import perf_counter

from b4_21_independent_audit import volume_weights
from b4_24_versioned_correctness_failure_review import (
    EVIDENCE_NEXT,
    METHOD_NEXT,
    arguments,
    canonical,
    check_inputs,
    execution_release,
    plan_payload,
    publish,
    read,
    selected_entries,
    sha,
    state_specs,
)


def reconstruct(panel, prior_audit, closed, report):
    if report["plan"] != plan_payload():
        raise ValueError("independent frozen plan differs")
    expected_rows, checks, state_checks, position = [], [], [], 0
    entries = selected_entries()
    specs = [list(s) for s in state_specs()]
    if [label["case_id"] for label in panel["labels"]] != [e.case.case_id for e in entries] or [
        (r["case_id"], r["state"], r["spec"]) for r in panel["rows"]
    ] != [(e.case.case_id, j, s) for e in entries for j, s in enumerate(specs)]:
        raise ValueError("independent complete population differs")
    for entry, label in zip(entries, panel["labels"], strict=True):
        weights = volume_weights(entry.case)
        g, anchor = label["design_gradient"], label["anchor"]
        n = len(weights)
        settings = entry.case.problem.optimization
        if len(g) != n or len(anchor) != n:
            raise ValueError("independent complete anchor required")

        def state_conditions(
            state,
            raw,
            value,
            gradient,
            n=n,
            g=g,
            anchor=anchor,
            weights=weights,
            settings=settings,
            label=label,
        ):
            design, physical, free, info = [
                state[k] for k in ("design", "physical", "free", "projection")
            ]
            if any(len(v) != n for v in (design, physical, free, raw, gradient)):
                raise ValueError("independent complete vector required")
            if not all(
                math.isfinite(x) for v in (design, physical, raw, gradient, g, anchor) for x in v
            ):
                raise ValueError("independent finite vectors required")
            shifted = [x + info["offset"] for x in raw]
            a = math.fsum(x for x, f in zip(g, free, strict=True) if f)
            b = math.fsum(w for w, f in zip(weights, free, strict=True) if f)
            if b <= 0:
                raise ValueError("independent positive free volume derivative required")
            cotangent = [
                (x - w * a / b if f else 0) for x, w, f in zip(g, weights, free, strict=True)
            ]
            arithmetic = label["intercept"] + math.fsum(
                x * (y - z) for x, y, z in zip(g, design, anchor, strict=True)
            )
            return [
                all(
                    abs(x - min(1, max(settings.minimum_density, z))) <= 2e-11
                    for x, z in zip(design, shifted, strict=True)
                ),
                free == [settings.minimum_density < z < 1 for z in shifted],
                abs(
                    info["weighted_volume_residual"]
                    - (
                        math.fsum(w * x for w, x in zip(weights, design, strict=True))
                        - settings.volume_fraction
                    )
                )
                <= 1e-12,
                abs(
                    info["physical_volume_residual"]
                    - (math.fsum(physical) / n - settings.volume_fraction)
                )
                <= 1e-12,
                abs(
                    info["kink_margin"]
                    - min(min(abs(z - settings.minimum_density), abs(z - 1)) for z in shifted)
                )
                <= 1e-12,
                math.isclose(value, arithmetic, rel_tol=1e-12, abs_tol=1e-12),
                all(
                    abs(x - y) <= 1e-10 + 1e-9 * abs(y)
                    for x, y in zip(gradient, cotangent, strict=True)
                ),
            ]

        position += 9
        for row in [r for r in panel["rows"] if r["case_id"] == label["case_id"]]:
            position += 24
            state_checks += state_conditions(row, row["raw"], row["surrogate"], row["gradient"])
            required = [(d, h) for d in ("sine", "cosine") for h in (1e-4, 2e-4)]
            if (
                [(d["direction"], d["step"]) for d in row["differences"]]
                != (required if row["state"] in (0, 4) else [])
                or len(row["timings"]) != 3
                or [t["repeat"] for t in row["timings"]] != [0, 1, 2]
            ):
                raise ValueError("independent complete directions/timings required")
            free, center, center_offset = row["free"], row["design"], row["projection"]["offset"]
            for item in row["differences"]:
                h = item["step"]
                trig, frequency = (
                    (math.sin, 0.37) if item["direction"] == "sine" else (math.cos, 0.13)
                )
                d = [trig(frequency * i) for i in range(1, n + 1)]
                maximum = max(abs(x) for x in d)
                d = [x / maximum for x in d]
                if len(item["sides"]) != 2:
                    raise ValueError("independent both sides required")
                plus, minus = item["sides"]
                departures = []
                for side, sign in zip((plus, minus), (1, -1), strict=True):
                    raw = [x + sign * h * v for x, v in zip(row["raw"], d, strict=True)]
                    state_checks += state_conditions(
                        {**side["physics"], "projection": side["projection"]},
                        raw,
                        side["surrogate"],
                        side["gradient"],
                    )
                    state_checks.append(side["free"] == side["physics"]["free"])
                    departures.append(
                        [
                            x
                            - c
                            - (
                                sign * h * v + side["projection"]["offset"] - center_offset
                                if f
                                else 0
                            )
                            for x, c, v, f in zip(
                                side["physics"]["design"], center, d, free, strict=True
                            )
                        ]
                    )
                a = math.fsum(x for x, f in zip(g, free, strict=True) if f)
                b = math.fsum(w for w, f in zip(weights, free, strict=True) if f)
                ratio = a / b
                weighted_direction = (
                    math.fsum(w * v for w, v, f in zip(weights, d, free, strict=True) if f) / b
                )
                tangent = [
                    (v - weighted_direction if f else 0) for v, f in zip(d, free, strict=True)
                ]
                delta = [
                    x - y
                    for x, y in zip(
                        plus["physics"]["design"], minus["physics"]["design"], strict=True
                    )
                ]
                chord = math.fsum(x * y / (2 * h) for x, y in zip(g, delta, strict=True))
                tangent_derivative = math.fsum(x * y for x, y in zip(g, tangent, strict=True))
                clipping = math.fsum(
                    (x - w * ratio) * (p - m) / (2 * h)
                    for x, w, p, m in zip(g, weights, *departures, strict=True)
                )
                volume = (
                    ratio * math.fsum(w * x for w, x in zip(weights, delta, strict=True)) / (2 * h)
                )
                fd = (plus["surrogate"] - minus["surrogate"]) / (2 * h)
                derivative, discrepancy = item["derivative"], fd - item["derivative"]
                error = abs(discrepancy) / max(abs(fd), abs(derivative), 1e-8)
                value_roundoff, gradient_roundoff = fd - chord, tangent_derivative - derivative
                gamma = (8 * n + 64) * 2.0**-52 / (1 - (8 * n + 64) * 2.0**-52)
                scale = (
                    1
                    + abs(plus["surrogate"])
                    + abs(minus["surrogate"])
                    + abs(derivative) * h
                    + math.fsum(abs(x) for x in g)
                    + abs(ratio)
                )
                envelope = gamma * scale / h
                mask_failed = any(s["free"] != free for s in (plus, minus))
                result = {
                    "case_id": entry.case.case_id,
                    "state": row["state"],
                    "direction": item["direction"],
                    "step": h,
                    "mask_condition": position + 32,
                    "fd_condition": position + 33,
                    "fd": fd,
                    "derivative": derivative,
                    "error": error,
                    "fd_failed": error > 1e-4,
                    "mask_failed": mask_failed,
                    "exact_fd": (plus["exact"] - minus["exact"]) / (2 * h),
                    "exact_derivative": item["exact_derivative"],
                    "signed_discrepancy": discrepancy,
                    "projected_chord_derivative": chord,
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
                    "clipping_accounts_for_gap_within_arithmetic_envelope": abs(
                        discrepancy - clipping
                    )
                    <= envelope,
                    "changed_plus_components": sum(
                        p != f for p, f in zip(plus["free"], free, strict=True)
                    ),
                    "changed_minus_components": sum(
                        p != f for p, f in zip(minus["free"], free, strict=True)
                    ),
                    "offsets": [
                        center_offset,
                        plus["projection"]["offset"],
                        minus["projection"]["offset"],
                    ],
                    "weighted_residuals": [
                        row["projection"]["weighted_volume_residual"],
                        plus["projection"]["weighted_volume_residual"],
                        minus["projection"]["weighted_volume_residual"],
                    ],
                }
                state_checks += [
                    item["fd"] == fd,
                    item["error"] == error,
                    item["same_active_set"] == (not mask_failed),
                    item["exact_fd"] == result["exact_fd"],
                    math.isclose(
                        math.fsum(x * v for x, v in zip(row["gradient"], d, strict=True)),
                        derivative,
                        rel_tol=1e-9,
                        abs_tol=1e-10,
                    ),
                    math.isclose(
                        math.fsum(x * v for x, v in zip(row["exact_gradient"], d, strict=True)),
                        item["exact_derivative"],
                        rel_tol=1e-9,
                        abs_tol=1e-10,
                    ),
                    abs(result["decomposition_residual"]) <= envelope,
                ]
                for key in ("mask", "fd"):
                    state_checks.append(
                        prior_audit["condition_results"][result[key + "_condition"]]
                        == (not result[key + "_failed"])
                    )
                expected_rows.append(result)
                position += 34
    failed_indices = sorted(
        r[k + "_condition"] for r in expected_rows for k in ("mask", "fd") if r[k + "_failed"]
    )
    if (
        position != 3976
        or len(report["rows"]) != 64
        or len(expected_rows) != 64
        or prior_audit["numerical_conditions"] != 3976
        or prior_audit["failed_numerical_conditions"] != 69
        or len(prior_audit["condition_results"]) != 3976
        or [i for i, v in enumerate(prior_audit["condition_results"]) if not v] != failed_indices
        or prior_audit["failed_condition_indices"] != failed_indices
    ):
        raise ValueError("independent every original failure identity differs")
    for actual, expected in zip(report["rows"], expected_rows, strict=True):
        if actual.keys() != expected.keys():
            raise ValueError("independent diagnostic row schema differs")
        for key, value in expected.items():
            checks.append(
                math.isclose(
                    actual[key],
                    value,
                    rel_tol=1e-12,
                    abs_tol=max(1e-12, 2 * expected["arithmetic_envelope"]),
                )
                if type(value) is float and key not in ("step", "fd", "derivative", "error")
                else actual[key] == value
            )
    explained = all(
        r["mask_failed"] and r["clipping_accounts_for_gap_within_arithmetic_envelope"]
        for r in expected_rows
        if r["fd_failed"]
    )
    passed = all(state_checks)
    fields = {
        "review_acceptance_passed": passed,
        "scalar_conditions": len(state_checks),
        "failed_scalar_conditions": sum(not v for v in state_checks),
        "mask_failures": sum(r["mask_failed"] for r in expected_rows),
        "fd_failures": sum(r["fd_failed"] for r in expected_rows),
        "overlapping_mask_and_fd_failures": sum(
            r["fd_failed"] and r["mask_failed"] for r in expected_rows
        ),
        "all_fd_failures_have_saved_clipping_explanation": explained,
        "original_fit_proxy_unchanged": closed["fit_proxy"],
        "retained_measurements": 216,
        "next_slice": METHOD_NEXT if passed and explained else EVIDENCE_NEXT,
        "original_conditions": 3976,
        "original_failed_conditions": 69,
        "original_correctness_gate_passed": False,
        "original_feasibility_gate_passed": False,
        "original_charge_seconds_unchanged": 143.47,
        "prior_charged_seconds_unchanged": [
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
    if (
        fields["mask_failures"] != 35
        or fields["fd_failures"] != 34
        or not all(checks)
        or any(report[k] != v for k, v in fields.items())
    ):
        raise ValueError("independent complete scalar review or boundary differs")
    return {
        "passed": True,
        "independent_scalar_conditions": len(checks),
        "review_sha256": sha(canonical(report)),
        "cases": 8,
        "central_states": 72,
        "side_states": 128,
        "directional_rows": 64,
        **{k: v for k, v in fields.items() if k != "scalar_conditions"},
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
        raise ValueError("independent source differs")
    panel = read(root, "probe.json")
    from b4_23_independent_audit import journal_check

    journal_check(root, panel)
    result = reconstruct(
        panel, bound["independent_audit.json"], bound["resource_close.json"], report
    )
    check_inputs(root)
    publish(output, "independent_audit.json", result, revision, started)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
