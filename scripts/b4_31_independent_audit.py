"""Separate Decimal/status enumeration. Never import or call the float reviewer."""

from decimal import Decimal, localcontext

from b4_29_common import read


def independent(values, c, output):
    with localcontext() as context:
        context.prec = 50
        return enumerate_panel(values, c, output)


def enumerate_panel(values, c, output):
    old = c["b4_30"]
    a = values["b4-30-z-reflection-repair-v2/sentinel/independent_audit.json"]
    ledger = values["b4-30-z-reflection-repair-v2/resource_close.json"]
    failed = values["b4-30-z-reflection-repair/resource_close.json"]
    soft = "b4-30-software-validation-v2/"
    certified = values[soft + "final_native_profile_review.json"]
    counts = values[soft + "report_method_failure_counts.json"]
    targets = values[soft + "historical_target_status_reporting.json"]
    packet = values[soft + "report_failure_scalars.json"]
    extra = values[soft + "extra_progress_snapshot_preservation.json"]
    predicates = []

    def require(ok, name):
        predicates.append({"name": name, "passed": bool(ok)})

    def d(value):
        return Decimal(str(value))

    def close(left, right):
        left, right = d(left), d(right)
        return abs(left - right) <= max(d("1e-14"), d("1e-14") * max(abs(left), abs(right)))

    require(a["passed"] is True and a["gate_passed"] is False, "certified FAIL")
    for field, n in {
        "references": 18,
        "outcomes": 270,
        "selected_terminal_classifications": 323,
        "guard_witness_classifications": 204,
        "prediction_replays": 78,
        "unchanged_outcome_identities": 249,
    }.items():
        require(type(a[field]) is int and a[field] == n, field)
    decision = a["decision"]
    expected = [[u["case_id"], u["policy"]] for u in old["historical_target_units"]]
    require(decision["repaired"] == expected[:4], "four historical passes")
    require(decision["unrepaired"] == expected[4:], "three historical failures")
    require(decision["negative_controls"] == old["negative_controls"], "negative controls")
    require(decision["primary_failures"] == [old["failed_case_id"]], "fixed17 failed case")
    require(
        decision["regressions"] == [] and decision["non_target_status_identity"] is True,
        "all non-target statuses",
    )
    require(decision["fixed_primary"] == 17 and decision["target_cases"] == 13, "fixed workload")
    for field in ("final_access", "sentinel_gate_passed", "repair_gate_passed"):
        require(decision[field] is False, field)
    mean = d(decision["large_y_primary_mean"])
    summed = d(decision["large_y_primary_total_ratio"])
    require(mean > 1 and summed <= 1, "distinct mean/sum")
    require(set(counts["methods"]) == set(old["methods"]), "complete method set")
    methods = []
    total_queries = total_failures = 0
    for i in range(15):
        name = old["methods"][i]
        row = counts["methods"][name]
        for field, n in (
            ("queries", 18),
            ("failures", old["method_failures"][i]),
            ("fallbacks", old["method_failures"][i]),
        ):
            require(type(row[field]) is int and row[field] == n, name + " " + field)
        total_queries += row["queries"]
        total_failures += row["failures"]
        methods.append({"method": name, **row})
    require(
        total_queries == 270 and total_failures == counts["total_failures"] == 35, "total count"
    )
    require(
        counts["all_from_audited_stored_packets"] is True and counts["new_execution"] is False,
        "no new execution",
    )
    require(len(targets["rows"]) == 7, "all historical targets")
    statuses = []
    for i in range(7):
        unit, observation = old["historical_target_units"][i], targets["rows"][i]
        r_name = unit["policy"]
        p_name = "P/" + r_name.split("/")[1]
        require(
            observation["case_id"] == unit["case_id"] and observation["R_policy"] == r_name,
            "identity " + str(i),
        )
        for name in (p_name, r_name):
            require(
                observation[name]["succeeded"] is (i < 4), name + " historical status " + str(i)
            )
            require(
                observation[name]["fallback"] is (i >= 4), name + " historical fallback " + str(i)
            )
        statuses.append(
            {
                "case_id": unit["case_id"],
                "P": p_name,
                "R": r_name,
                "P_succeeded": observation[p_name]["succeeded"],
                "R_succeeded": observation[r_name]["succeeded"],
                "newly_repaired_P_failure": False,
            }
        )
    for field, expected_value in {
        "historical_target_predicates_passed": 4,
        "historical_target_predicates_failed": 3,
        "all_seven_matched_current_P_R_statuses_same": True,
        "currently_failed_B4_12_P_target_units_newly_repaired": 0,
        "B4_12_identity_already_verified_by_independent_audit": True,
        "historical_failures_do_not_imply_current_P_failure": True,
    }.items():
        require(targets[field] == expected_value, field)
    require(packet["case_id"] == old["failed_case_id"], "scalar case identity")
    names = ["uniform"] + [f"{method}/{seed}" for method in ("P", "R") for seed in (17, 29, 43)]
    rows = packet["rows"]
    require(len(rows) == 7 and [r["policy"] for r in rows] == names, "all seven scalar rows")
    scalars = []
    for i, row in enumerate(rows):
        require(row["failed"] is (i != 0), "attempt status " + str(i))
        require(row["fallback"] is (i != 0), "fallback status " + str(i))
        require(row["failure_code"] == (None if i == 0 else "quality_error"), "code " + str(i))
        require(
            row["failure_type"] == (None if i == 0 else "_BaselineQualityError"), "type " + str(i)
        )
        compliance, volume = d(row["compliance_ratio"]), d(row["volume_error"])
        require(compliance > d("1.001") if i else compliance == 1, "quality " + str(i))
        require(0 <= volume <= d("0.005"), "volume " + str(i))
        require(type(row["iterations"]) is int and row["iterations"] > 0, "iterations " + str(i))
        require(d(row["fully_charged_query_cost_seconds"]) > 0, "cost " + str(i))
        scalars.append(
            {
                "policy": row["policy"],
                "compliance_ratio": float(compliance),
                "quality_excess": float(compliance - d("1.001")),
                "volume_error": float(volume),
                "iterations": row["iterations"],
                "fully_charged_query_cost_seconds": row["fully_charged_query_cost_seconds"],
                "failed": row["failed"],
                "fallback": row["fallback"],
            }
        )
    pairs = []
    for seed in (17, 29, 43):
        before = next(r for r in rows if r["policy"] == f"P/{seed}")
        after = next(r for r in rows if r["policy"] == f"R/{seed}")
        pairs.append(
            {
                "seed": seed,
                "compliance_delta_R_minus_P": float(
                    d(after["compliance_ratio"]) - d(before["compliance_ratio"])
                ),
                "iterations_delta_R_minus_P": after["iterations"] - before["iterations"],
                "paid_cost_delta_R_minus_P": float(
                    d(after["fully_charged_query_cost_seconds"])
                    - d(before["fully_charged_query_cost_seconds"])
                ),
                "paid_cost_ratio_R_over_P": float(
                    d(after["fully_charged_query_cost_seconds"])
                    / d(before["fully_charged_query_cost_seconds"])
                ),
            }
        )
    process_names = [
        "sentinel_reference",
        "sentinel_screen",
        "sentinel_audit",
        "sentinel_policy-audit",
        "sentinel_independent",
    ]
    require([r["process"] for r in ledger["processes"]] == process_names, "five prior stages")
    require(
        [r["process"] for r in certified["independent_stage_rows"]] == process_names,
        "five certifications",
    )
    amount = d(failed["charged_decimal"]) + 180
    stage_decimals = []
    for row, proof in zip(ledger["processes"], certified["independent_stage_rows"], strict=True):
        charge = d(row["closed_charge_decimal"])
        require(
            charge == d(proof["independent_charge_decimal"]) and charge <= d(proof["cap_decimal"]),
            row["process"] + " Decimal charge",
        )
        require(
            row["complete_resource_evidence"] is True and proof["complete_native_resource"] is True,
            row["process"] + " complete native",
        )
        require(row["native"] and 0 < row["peak_rss_bytes"] <= 2147483648, row["process"] + " RSS")
        amount += charge
        stage_decimals.append(str(charge))
    require(amount == d(old["cumulative_charge_decimal"]), "unchanged cumulative Decimal")
    require(
        d(failed["charged_decimal"]) == d(old["original_failed_charge_decimal"]),
        "original failed amount",
    )
    require(failed["fully_paid_chain_reserve_seconds"] == 180, "failed FULL180")
    require(
        ledger["fully_paid_chain_reserve_seconds"] == 180
        and ledger["retained_failed_paid_chain_reserve_seconds"] == 180,
        "second FULL180",
    )
    require(
        ledger["aggregate_fully_paid_chain_reserve_seconds"]
        == certified["aggregate_FULL_reserves_seconds"]
        == 360,
        "no refunded reserves",
    )
    for record in (ledger, certified):
        require(record["source_revision"] == old["source_revision"], "old source SHA")
        require(
            d(record["charged_decimal"]) == amount and close(record["charged_seconds"], amount),
            "Decimal/float total",
        )
        require(
            d(record["retained_failed_charge_decimal"]) == d(old["original_failed_charge_decimal"]),
            "failed charge retained",
        )
        require(record["full_training_memory"] == "PENDING/4GiB", "fit memory pending")
    require(
        ledger["fresh_sealed"] is True
        and ledger["final_access"] is False
        and ledger["new_fits"] == 0,
        "old seals unchanged",
    )
    require(ledger["whole_resource_acceptance"] == "PENDING_POSTEXIT", "immutable lifecycle")
    require(
        certified["whole_resource_passed"] is True
        and certified["final_native_verifier_exit_checked"] is True,
        "later scoped native proof",
    )
    require(
        certified["scientific_gate"] == "FAIL" and certified["repair_gate_passed"] is False,
        "scientific stop",
    )
    require(
        certified["conservative_whole_chain_rss_upper_bound_bytes"] == 800047104,
        "scoped old memory",
    )
    require(
        certified["administrative_invocations"] == 2
        and certified["maximum_completed_numerical_campaigns"] == 1,
        "unchanged old invocations",
    )
    require(
        extra["passed"] is True
        and extra["preserved"] is True
        and extra["origin"] == "UNKNOWN"
        and extra["not_used_as_canonical_progress"] is True
        and extra["does_not_replace_final_chain_or_its_audits"] is True,
        "extra snapshot UNKNOWN",
    )
    facts = {
        "methods": methods,
        "historical_statuses": statuses,
        "failure_scalars": scalars,
        "paired": pairs,
        "target_mean": float(mean),
        "target_sum_ratio": float(summed),
        "target_mean_margin_to_limit": float(1 - mean),
        "target_sum_margin_to_limit": float(1 - summed),
        "old_cumulative_charge": float(amount),
        "scientific_gate": "FAIL",
        "unknowns": c["unknowns"],
        "next_proposed_slice": c["stops"]["next_proposed_slice"],
    }
    reviewed = read(output / "review.json")

    def compare(left, right, location="facts"):
        if type(left) is dict:
            require(type(right) is dict and set(left) == set(right), location + " keys")
            for key in left:
                compare(left[key], right[key], location + "." + key)
        elif type(left) is list:
            require(type(right) is list and len(left) == len(right), location + " length")
            for i, item in enumerate(left):
                compare(item, right[i], location + "." + str(i))
        elif type(left) is float:
            require(close(left, right), location + " arithmetic")
        else:
            require(type(left) is type(right) and left == right, location + " identity")

    require(reviewed["passed"] is True, "review acceptance retained")
    compare(facts, reviewed["facts"])
    return {
        "passed": all(p["passed"] for p in predicates),
        "predicates": predicates,
        "accepted_predicates": sum(p["passed"] for p in predicates),
        "facts": facts,
        "old_cumulative_charge_decimal": str(amount),
        "prior_stage_charge_decimals": stage_decimals,
        "inputs_sha256": c["inputs_sha256"],
    }
