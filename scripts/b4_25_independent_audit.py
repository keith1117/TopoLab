"""Separate scalar enumeration/cost audit; imports only boundary and IO helpers."""

import math

from b4_25_active_set_method_review import (
    BINDINGS,
    CASE_IDS,
    EVIDENCE_NEXT,
    METHOD_NEXT,
    METHODS,
    boundary_fields,
    canonical,
    plan_payload,
    sha,
)


def audit(prior, report):
    rows = prior["rows"]
    cases = CASE_IDS
    if len(rows) != 64 or len(cases) != 8:
        raise ValueError("independent complete population differs")
    checks, failures, groups = [], [], {}
    for case_number, case_id in enumerate(cases):
        for state in (0, 4):
            for direction_number, direction in enumerate(("sine", "cosine")):
                for step_number, step in enumerate((1e-4, 2e-4)):
                    index = (
                        8 * case_number
                        + (4 if state == 4 else 0)
                        + 2 * direction_number
                        + step_number
                    )
                    row = rows[index]
                    position = (
                        497 * case_number
                        + (297 if state == 4 else 65)
                        + 34 * (2 * direction_number + step_number)
                    )
                    if (
                        row["case_id"],
                        row["state"],
                        row["direction"],
                        row["step"],
                        row["mask_condition"],
                        row["fd_condition"],
                    ) != (case_id, state, direction, step, position, position + 1):
                        raise ValueError("independent condition position/order differs")
                    crossing = (
                        row["changed_plus_components"] > 0 or row["changed_minus_components"] > 0
                    )
                    gap = math.fsum((row["fd"], -row["derivative"]))
                    normalized = abs(gap) / max(1e-8, abs(row["derivative"]), abs(row["fd"]))
                    failed = normalized > 0.0001
                    clipping = row["clipping_departure_contribution"]
                    residual = math.fsum(
                        (
                            gap,
                            -clipping,
                            -row["volume_residual_contribution"],
                            -row["saved_value_roundoff_contribution"],
                            -row["saved_gradient_roundoff_contribution"],
                        )
                    )
                    compatible = abs(gap - clipping) <= row["arithmetic_envelope"]
                    checks += [
                        type(row["mask_failed"]) is bool and row["mask_failed"] == crossing,
                        type(row["fd_failed"]) is bool and row["fd_failed"] == failed,
                        math.isclose(normalized, row["error"], rel_tol=1e-12, abs_tol=1e-12),
                        math.isclose(gap, row["signed_discrepancy"], rel_tol=1e-12, abs_tol=1e-12),
                        math.isclose(
                            residual, row["decomposition_residual"], rel_tol=1e-12, abs_tol=1e-12
                        ),
                        abs(residual) <= row["arithmetic_envelope"],
                        row["clipping_accounts_for_gap_within_arithmetic_envelope"] == compatible,
                    ]
                    if crossing:
                        failures.append(position)
                    if failed:
                        failures.append(position + 1)
                    key = f"{state}/{step}"
                    group = groups.setdefault(
                        key, {"rows": 0, "mask_failures": 0, "fd_failures": 0, "overlap": 0}
                    )
                    group["rows"] += 1
                    group["mask_failures"] += crossing
                    group["fd_failures"] += failed
                    group["overlap"] += crossing and failed
    proxy = prior["original_fit_proxy_unchanged"]
    maxima = proxy["maximum_seconds_per_scale"]
    setup = proxy["maximum_setup_seconds_per_scale"]
    prediction = math.fsum((324000 * maxima["small"], 57000 * maxima["large"]))
    preparation = math.fsum((1620 * setup["small"], 285 * setup["large"]))
    fixed = math.fsum((preparation, 3870.204341, 851.38))
    total = fixed + prediction
    if (
        not all(
            math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
            for a, b in (
                (prediction, proxy["additional_surrogate_seconds"]),
                (preparation, proxy["full_population_preparation_seconds"]),
                (total, proxy["total_prospective_seconds"]),
            )
        )
        or proxy["cost_feasible"]
        or proxy["limit_seconds"] != 7200
    ):
        raise ValueError("independent complete original cost differs")
    remaining = 7200 - fixed - 200.98
    costs = {
        "original_maximum_seconds": total,
        "zero_small_recorded_large_max_seconds": fixed + 57000 * maxima["large"],
        "zero_prediction_seconds": fixed,
        "original_plus_b4_24_seconds": total + 200.98,
        "conditional_prediction_budget_before_b4_25_seconds": remaining,
        "common_prediction_reduction_required_before_b4_25": prediction / remaining
        if remaining > 0
        else None,
        "population_weighted_unit_budget_before_b4_25_seconds": remaining / 381000,
        "retained_array_bytes_estimate": proxy["population_retained_array_bytes_estimate"],
        "signed_retained_array_headroom_to_4gib": 4294967296
        - proxy["population_retained_array_bytes_estimate"],
        "diagnostic_only": True,
        "original_cost_gate_passed": False,
        "full_fit_memory_feasibility_pending": True,
    }
    masks = sum(r["mask_failed"] for r in rows)
    fds = sum(r["fd_failed"] for r in rows)
    explained = all(
        r["mask_failed"] and r["clipping_accounts_for_gap_within_arithmetic_envelope"]
        for r in rows
        if r["fd_failed"]
    )
    if masks != 35 or fds != 34 or len(set(failures)) != 69:
        raise ValueError("independent preserved failure population differs")
    expected = {
        "plan": plan_payload(),
        "retained_rows": rows,
        "original_fit_proxy_unchanged": proxy,
        "failed_condition_indices": sorted(failures),
        "groups": groups,
        "scalar_conditions": len(checks),
        "failed_scalar_conditions": sum(not v for v in checks),
        "mask_failures": masks,
        "fd_failures": fds,
        "overlapping_mask_and_fd_failures": sum(r["mask_failed"] and r["fd_failed"] for r in rows),
        "all_failed_fd_rows_cross_and_are_clipping_compatible": explained,
        "method_dispositions": dict(METHODS),
        "cost_diagnostics": costs,
        "review_acceptance_passed": all(checks),
        "next_slice": METHOD_NEXT if all(checks) and explained else EVIDENCE_NEXT,
        "prior_review_sha256": BINDINGS["review.json"],
        **boundary_fields(),
    }
    if canonical(report["retained_rows"]) != canonical(rows) or canonical(
        report["original_fit_proxy_unchanged"]
    ) != canonical(proxy):
        raise ValueError("independent retained original rows/cost must remain byte-identical")
    compared = 0

    def compare(actual, wanted):
        nonlocal compared
        if isinstance(wanted, dict):
            if not isinstance(actual, dict) or set(actual) != set(wanted):
                raise ValueError("independent field population differs")
            for key in wanted:
                compare(actual[key], wanted[key])
        elif isinstance(wanted, list):
            if not isinstance(actual, list) or len(actual) != len(wanted):
                raise ValueError("independent sequence differs")
            for a, b in zip(actual, wanted, strict=True):
                compare(a, b)
        else:
            compared += 1
            if isinstance(wanted, float):
                matches = type(actual) is float and math.isclose(
                    actual, wanted, rel_tol=1e-12, abs_tol=1e-12
                )
            else:
                matches = type(actual) is type(wanted) and actual == wanted
            if not matches:
                raise ValueError("independent scalar or disposition differs")

    compare({k: report[k] for k in expected}, expected)
    return {
        "passed": True,
        "metadata_only": False,
        "review_sha256": sha(canonical(report)),
        "prior_review_sha256": BINDINGS["review.json"],
        "scalar_conditions": len(checks),
        "independent_scalar_comparisons": compared,
        "review_acceptance_passed": all(checks),
        "next_slice": expected["next_slice"],
        **boundary_fields(),
    }
