"""Float scalar review of the entire frozen metadata panel; no payload dereferences."""

import math


def review(values, c, _output):
    old = c["b4_30"]
    root = "b4-30-z-reflection-repair-v2/"
    soft = "b4-30-software-validation-v2/"
    audit = values[root + "sentinel/independent_audit.json"]
    closed = values[root + "resource_close.json"]
    resource = values[soft + "final_native_profile_review.json"]
    failures = values[soft + "report_failure_scalars.json"]
    methods = values[soft + "report_method_failure_counts.json"]
    historical = values[soft + "historical_target_status_reporting.json"]
    extra = values[soft + "extra_progress_snapshot_preservation.json"]
    failed = values["b4-30-z-reflection-repair/resource_close.json"]
    checks = []

    def check(value, name):
        checks.append({"name": name, "passed": bool(value)})

    def same(a, b):
        return math.isclose(float(a), float(b), rel_tol=1e-14, abs_tol=1e-14)

    check(
        audit["passed"] and not audit["gate_passed"], "prior independent acceptance, science FAIL"
    )
    for field, expected in (
        ("references", 18),
        ("outcomes", 270),
        ("selected_terminal_classifications", 323),
        ("guard_witness_classifications", 204),
        ("prediction_replays", 78),
        ("unchanged_outcome_identities", 249),
    ):
        check(audit[field] == expected, field)
    decision = audit["decision"]
    units = [[u["case_id"], u["policy"]] for u in old["historical_target_units"]]
    check(
        decision["repaired"] == units[:4] and decision["unrepaired"] == units[4:], "all seven units"
    )
    check(decision["negative_controls"] == old["negative_controls"], "both negative controls")
    check(decision["primary_failures"] == [old["failed_case_id"]], "fixed17 single failure")
    check(
        decision["non_target_status_identity"] and not decision["regressions"],
        "old status identities",
    )
    check(decision["fixed_primary"] == 17 and decision["target_cases"] == 13, "primary and targets")
    check(
        not decision["final_access"] and not decision["sentinel_gate_passed"],
        "sealed failed sentinel",
    )
    check(not decision["repair_gate_passed"], "repair remains failed")
    mean, pooled = decision["large_y_primary_mean"], decision["large_y_primary_total_ratio"]
    check(mean > 1.0 and pooled <= 1.0, "mean/sum predicates distinct")
    check(set(methods["methods"]) == set(old["methods"]), "all 15 methods")
    method_rows = []
    for method, expected in zip(old["methods"], old["method_failures"], strict=True):
        row = methods["methods"][method]
        check(row == {"queries": 18, "failures": expected, "fallbacks": expected}, method)
        method_rows.append({"method": method, **row})
    check(sum(r["queries"] for r in method_rows) == 270, "270 queries")
    check(sum(r["failures"] for r in method_rows) == methods["total_failures"] == 35, "35 failures")
    check(
        methods["all_from_audited_stored_packets"] and not methods["new_execution"], "stored only"
    )
    check(len(historical["rows"]) == 7, "seven historical rows")
    status_rows = []
    for i, unit in enumerate(old["historical_target_units"]):
        row = historical["rows"][i]
        r, p = unit["policy"], unit["policy"].replace("R/", "P/")
        expected = i < 4
        check(row["case_id"] == unit["case_id"] and row["R_policy"] == r, f"unit identity {i}")
        check(
            all(
                row[m]["succeeded"] is expected and row[m]["fallback"] is not expected
                for m in (p, r)
            ),
            f"matched P/R status {i}",
        )
        status_rows.append(
            {
                "case_id": unit["case_id"],
                "P": p,
                "R": r,
                "P_succeeded": row[p]["succeeded"],
                "R_succeeded": row[r]["succeeded"],
                "newly_repaired_P_failure": False,
            }
        )
    for field, expected in (
        ("historical_target_predicates_passed", 4),
        ("historical_target_predicates_failed", 3),
        ("all_seven_matched_current_P_R_statuses_same", True),
        ("currently_failed_B4_12_P_target_units_newly_repaired", 0),
        ("B4_12_identity_already_verified_by_independent_audit", True),
        ("historical_failures_do_not_imply_current_P_failure", True),
    ):
        check(historical[field] == expected, field)
    rows = failures["rows"]
    names = ["uniform", "P/17", "P/29", "P/43", "R/17", "R/29", "R/43"]
    check(failures["case_id"] == old["failed_case_id"], "failed case identity")
    check([r["policy"] for r in rows] == names, "all seven scalar rows")
    scalar_rows = []
    for i, row in enumerate(rows):
        check(row["failed"] is (i > 0) and row["fallback"] is (i > 0), f"failure retained {i}")
        check(
            row["failure_code"] == ("quality_error" if i else None)
            and row["failure_type"] == ("_BaselineQualityError" if i else None),
            f"code {i}",
        )
        check(0 <= row["volume_error"] <= old["volume_error_limit"], f"volume {i}")
        check(
            row["compliance_ratio"] > 1.001 if i else same(row["compliance_ratio"], 1),
            f"quality {i}",
        )
        check(
            isinstance(row["iterations"], int)
            and row["iterations"] > 0
            and row["fully_charged_query_cost_seconds"] > 0,
            f"positive cost/iterations {i}",
        )
        scalar_rows.append(
            {
                "policy": row["policy"],
                "compliance_ratio": row["compliance_ratio"],
                "quality_excess": row["compliance_ratio"] - 1.001,
                "volume_error": row["volume_error"],
                "iterations": row["iterations"],
                "fully_charged_query_cost_seconds": row["fully_charged_query_cost_seconds"],
                "failed": row["failed"],
                "fallback": row["fallback"],
            }
        )
    paired = []
    for i, seed in enumerate(old["seeds"]):
        p, r = rows[i + 1], rows[i + 4]
        paired.append(
            {
                "seed": seed,
                "compliance_delta_R_minus_P": r["compliance_ratio"] - p["compliance_ratio"],
                "iterations_delta_R_minus_P": r["iterations"] - p["iterations"],
                "paid_cost_delta_R_minus_P": r["fully_charged_query_cost_seconds"]
                - p["fully_charged_query_cost_seconds"],
                "paid_cost_ratio_R_over_P": r["fully_charged_query_cost_seconds"]
                / p["fully_charged_query_cost_seconds"],
            }
        )
    processes = [
        "sentinel_" + s for s in ("reference", "screen", "audit", "policy-audit", "independent")
    ]
    check([r["process"] for r in closed["processes"]] == processes, "five old stages")
    check(
        [r["process"] for r in resource["independent_stage_rows"]] == processes,
        "five certified stages",
    )
    for a, b in zip(closed["processes"], resource["independent_stage_rows"], strict=True):
        check(
            a["complete_resource_evidence"]
            and b["complete_native_resource"]
            and same(a["closed_charge_decimal"], b["independent_charge_decimal"])
            and float(b["independent_charge_decimal"]) <= float(b["cap_decimal"]),
            a["process"] + " cost",
        )
        check(a["native"] and a["peak_rss_bytes"] <= 2147483648, a["process"] + " RSS")
    old_cost = sum(float(r["closed_charge_decimal"]) for r in closed["processes"])
    old_cost += float(failed["charged_decimal"]) + 180
    check(
        same(old_cost, old["cumulative_charge_decimal"]), "failed prefix and FULL reserve charged"
    )
    for record in (closed, resource):
        check(record["source_revision"] == old["source_revision"], "old release identity")
        check(
            same(record["charged_decimal"], old_cost) and same(record["charged_seconds"], old_cost),
            "old cumulative cost",
        )
        check(
            same(record["retained_failed_charge_decimal"], old["original_failed_charge_decimal"]),
            "retained failure",
        )
    check(
        closed["aggregate_fully_paid_chain_reserve_seconds"]
        == resource["aggregate_FULL_reserves_seconds"]
        == 360,
        "both FULL180",
    )
    check(
        closed["fresh_sealed"] and not closed["final_access"] and closed["new_fits"] == 0,
        "old seals",
    )
    check(
        closed["whole_resource_acceptance"] == "PENDING_POSTEXIT"
        and resource["whole_resource_passed"]
        and resource["final_native_verifier_exit_checked"],
        "lifecycle",
    )
    check(
        resource["scientific_gate"] == "FAIL" and not resource["repair_gate_passed"], "science FAIL"
    )
    check(
        resource["conservative_whole_chain_rss_upper_bound_bytes"] == 800047104, "scoped old peak"
    )
    check(
        resource["administrative_invocations"] == 2
        and resource["maximum_completed_numerical_campaigns"] == 1,
        "old quota",
    )
    check(
        extra["passed"]
        and extra["preserved"]
        and extra["origin"] == "UNKNOWN"
        and extra["not_used_as_canonical_progress"]
        and extra["does_not_replace_final_chain_or_its_audits"],
        "unused snapshot origin UNKNOWN",
    )
    facts = {
        "methods": method_rows,
        "historical_statuses": status_rows,
        "failure_scalars": scalar_rows,
        "paired": paired,
        "target_mean": mean,
        "target_sum_ratio": pooled,
        "target_mean_margin_to_limit": 1.0 - mean,
        "target_sum_margin_to_limit": 1.0 - pooled,
        "old_cumulative_charge": old_cost,
        "scientific_gate": "FAIL",
        "unknowns": c["unknowns"],
        "next_proposed_slice": c["stops"]["next_proposed_slice"],
    }
    return {
        "passed": all(r["passed"] for r in checks),
        "predicates": checks,
        "accepted_predicates": sum(r["passed"] for r in checks),
        "facts": facts,
        "inputs_sha256": c["inputs_sha256"],
    }
