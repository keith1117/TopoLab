"""Separate explicit scalar enumeration and Decimal cost; never imports reviewer."""

import math
import re
from decimal import Decimal

from b4_29_common import canonical, read, sha


def audit(records, c, output):
    x = records["compact_outcome.json"]
    flags = []

    def demand(name, accepted):
        flags.append({"name": name, "passed": bool(accepted)})

    # Enumeration is separate from the reviewer, including every summarized row.
    demand("source", x["source_revision"] == c["b4_28"]["source_revision"])
    demand(
        "new integrity",
        x["integrity_passed"] is True
        and x["new_predicate_count"] == 3232
        and x["new_predicates_passed"] == 3232
        and x["pointwise_states"] == 200,
    )
    for stage in c["b4_28"]["numeric_counts"]:
        for kind, expected in c["b4_28"]["numeric_counts"][stage].items():
            row = x[stage + "_counts"][kind]
            demand(stage + kind, row["attempted"] == row["completed"] == expected)
    expected_old = {
        "legacy_predicates": 3976,
        "legacy_failed": 69,
        "legacy_first_timings": 216,
        "legacy_fem": 432,
        "legacy_projections": 816,
    }
    for key, value in expected_old.items():
        demand(key, x[key] == value)
    positions = x["legacy_failed_positions"]
    seen = set()
    for index in positions:
        demand("legacy position", type(index) is int and 0 <= index < 3976 and index not in seen)
        seen.add(index)
    demand("69 preserved", len(seen) == 69 == len(positions))
    stable, crossing, maximum, interval_keys = 0, 0, 0, set()
    for row in x["intervals"]:
        key = (row["case_id"], row["state"], row["direction"], row["step"])
        demand("interval unique", key not in interval_keys)
        interval_keys.add(key)
        demand(
            "interval predicates",
            row["passed"] is True
            and len(row["predicates"]) == 3
            and all(v is True for v in row["predicates"])
            and 1 <= row["pieces"] <= 256,
        )
        if row["crossing"] is True:
            crossing += 1
        else:
            stable += 1
        maximum = max(maximum, row["pieces"])
    demand(
        "complete partition panel",
        len(interval_keys) == 64 and (stable, crossing, maximum) == (29, 35, 81),
    )
    maxima = dict.fromkeys(
        ("normalized_value_error", "increment_relative_error", "gradient_relative_error"), 0
    )
    local_keys = set()
    for row in x["local_states"]:
        key = (row["case_id"], row["state"])
        demand("LOCAL unique", key not in local_keys)
        local_keys.add(key)
        for name, limit in zip(
            maxima, (Decimal(".0001"), Decimal(".25"), Decimal(".25")), strict=True
        ):
            value = row["metrics"][name]
            demand(name, type(value) in (int, float) and Decimal(0) <= Decimal(str(value)) <= limit)
            maxima[name] = max(maxima[name], value)
        demand(
            "LOCAL sign", row["passed"] is True and row["metrics"]["increment_sign_agrees"] is True
        )
    demand(
        "complete LOCAL",
        len(local_keys) == len(x["local_states"]) == 32 and x["local_fidelity_passed"] is True,
    )
    diagnostic_keys, regions, negative = set(), set(), 0
    for row in x["central_diagnostics"]:
        key = (row["case_id"], row["state"])
        demand("diagnostic unique", key not in diagnostic_keys)
        diagnostic_keys.add(key)
        regions.add(row["region"])
        demand(
            "negative scalar retained", row["negative_surrogate"] == (row["surrogate_value"] < 0)
        )
        negative += int(row["negative_surrogate"])
    demand(
        "diagnostics",
        len(diagnostic_keys) == len(x["central_diagnostics"]) == 72
        and regions == {"local", "outside", "uniform"},
    )
    q = Decimal(60)
    commands = {row["name"]: row for row in records["audit_receipts/execution_commands.json"]}
    for stage in ("producer", "independent"):
        profile = records["profiles/" + stage + ".time"]
        times = re.search(r"([\d.]+)\s+real\s+([\d.]+)\s+user\s+([\d.]+)\s+sys", profile)
        rss = re.search(r"(\d+)\s+maximum resident set size", profile)
        demand(stage + " profile", bool(times and rss and int(rss[1]) > 0))
        if not times or not rss:
            raise ValueError("independent native fields unavailable")
        retained = commands[stage]
        for field, group in (("wall_seconds", 1), ("user_seconds", 2), ("system_seconds", 3)):
            demand(stage + field, Decimal(str(retained["native"][field])) == Decimal(times[group]))
        demand(
            stage + " rss/exit",
            retained["exit_code"] == 0 and retained["native"]["rss_bytes"] == int(rss[1]),
        )
        charged = Decimal(times[1]) + Decimal(10)
        demand(stage + " charge", charged == Decimal(str(x["ledger"]["stage_charges"][stage])))
        q += charged
    demand(
        "Q28 reserve",
        q == Decimal("234.60") == Decimal(str(x["ledger"]["total_charged_seconds"]))
        and x["ledger"]["fully_paid_reserve_seconds"] == 60,
    )
    p = {k: Decimal(str(v)) for k, v in c["cost"]["inherited_first_inclusive_maxima"].items()}
    fixed = sum((Decimal("3870.204341"), Decimal("851.38"), Decimal("200.98"), Decimal("80.34")))
    fixed += Decimal("3.75") * (Decimal(432) * p["p_small"] + Decimal(76) * p["p_large"])
    fixed += Decimal(750) * (Decimal(432) * p["u_small"] + Decimal(76) * p["u_large"])
    cost = fixed + q
    for name, expected in (
        ("fixed_cost_without_new_charges", fixed),
        ("added_cost_view_seconds", cost),
    ):
        demand(name, math.isclose(float(expected), x[name], rel_tol=1e-12, abs_tol=1e-12))
    demand(
        "failed cost",
        cost > Decimal(7200)
        and x["cost_feasible"] is False
        and x["cost_limit_seconds"] == 7200
        and x["original_failed_proxy_seconds"] == 57546.0720687792,
    )
    gap = records["audit_receipts/platform_exit_binding.json"]
    prep = records["audit_receipts/platform_prepare_command.json"]
    demand(
        "preparation gap retained",
        gap["passed"] is False
        and gap["preparation_native"] is None
        and gap["whole_observed_peak_rss_bytes"] is None
        and prep["exit_code"] == 1
        and prep["native"] is None,
    )
    demand(
        "whole resource unresolved",
        records["audit_receipts/final_scope_summary.json"]["complete_resource_acceptance"] is False,
    )
    demand(
        "scoped proof separate",
        records["audit_receipts/final_postexit_proof.json"]["passed"] is True
        and x["whole_native_resource_proof"] == "PENDING_POSTEXIT",
    )
    demand(
        "historical unknowns",
        x["historical_b4_24_planning_rss"] is None
        and x["historical_b4_24_whole_peak_rss"] is None
        and x["historical_b4_24_whole_memory_proof"] is False
        and x["historical_b4_19_case_gap_counts"] == "UNKNOWN",
    )
    demand(
        "old charges",
        x["historical_b4_24_seconds"] == 200.98 and x["historical_b4_25_seconds"] == 80.34,
    )
    demand(
        "full memory unresolved",
        x["full_training_memory"] == "PENDING"
        and x["full_training_memory_cap_bytes"] == 4294967296,
    )
    demand("closed ledger", x["ledger"] == records["resource_close.json"]["ledger"])
    demand(
        "stops",
        x["fits"] == 0
        and x["final_access"] is False
        and x["old_fresh_sealed"] is True
        and x["next_route"] == c["route"],
    )
    facts = {
        "q28": float(q),
        "fixed_cost": float(fixed),
        "cost_before_q29": float(cost),
        "stable": stable,
        "crossing": crossing,
        "max_pieces": maximum,
        "local_maxima": maxima,
        "negative_diagnostics": negative,
        "failed_positions_sha256": sha(canonical(positions)),
        "legacy_failed": len(positions),
        "intervals": len(interval_keys),
        "local_states": len(local_keys),
        "diagnostics": len(diagnostic_keys),
        "b4_28_whole_peak_rss_bytes": None,
        "full_training_memory": "PENDING",
        "cost_feasible": False,
        "fit_authorized": False,
    }
    prior = read(output / "review.json")
    if prior["passed"]:
        for key, value in facts.items():
            other = prior["facts"][key]
            demand(
                "reviewer agreement " + key,
                math.isclose(value, other, rel_tol=1e-12, abs_tol=1e-12)
                if type(value) is float
                else value == other,
            )
    else:
        demand("review failed; acceptance stops", False)
    return {
        "passed": all(v["passed"] for v in flags),
        "checks": flags,
        "facts": facts,
        "decimal_fixed_cost": str(fixed),
        "decimal_cost_before_q29": str(cost),
        "input_sha256": c["inputs_sha256"],
        "scientific_gate_repaired": False,
        "route": c["route"],
    }
