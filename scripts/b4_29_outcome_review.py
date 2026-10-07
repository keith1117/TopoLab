"""Read-only float review of the complete closed active-set scalar panel."""

import math

from b4_29_common import canonical, native, sha


def review(records, c, output):
    x = records["compact_outcome.json"]
    checks = []

    def check(name, accepted):
        checks.append({"name": name, "passed": bool(accepted)})

    def equal(name, actual, expected):
        check(name, actual == expected)

    b = c["b4_28"]
    equal("source", x["source_revision"], b["source_revision"])
    equal("integrity", x["integrity_passed"], True)
    equal("LOCAL", x["local_fidelity_passed"], True)
    equal("new predicates", (x["new_predicates_passed"], x["new_predicate_count"]), (3232, 3232))
    equal("point states", x["pointwise_states"], 200)
    for stage, kinds in b["numeric_counts"].items():
        for kind, n in kinds.items():
            equal(stage + kind, x[stage + "_counts"][kind], {"attempted": n, "completed": n})
    for field, key in [
        ("predicates", "legacy_predicates"),
        ("failed", "legacy_failed"),
        ("first_timings", "legacy_first_timings"),
        ("fem", "legacy_fem"),
        ("projections", "legacy_projections"),
    ]:
        equal(key, x[key], c["legacy"][field])
    positions = x["legacy_failed_positions"]
    check(
        "all69 positions",
        len(positions) == 69
        and len(set(positions)) == 69
        and all(type(i) is int and 0 <= i < 3976 for i in positions),
    )
    intervals = x["intervals"]
    equal("all intervals", len(intervals), 64)
    keys = {(v["case_id"], v["state"], v["direction"], v["step"]) for v in intervals}
    equal("unique intervals", len(keys), 64)
    check(
        "complete interval predicates",
        all(
            v["passed"] is True and v["predicates"] == [True] * 3 and 1 <= v["pieces"] <= 256
            for v in intervals
        ),
    )
    crossing = sum(v["crossing"] for v in intervals)
    equal("stable/crossing", (64 - crossing, crossing), (29, 35))
    equal("maximum pieces", max(v["pieces"] for v in intervals), 81)
    local = x["local_states"]
    equal("all LOCAL", len(local), 32)
    equal("unique LOCAL", len({(v["case_id"], v["state"]) for v in local}), 32)
    maxima = {}
    for metric, threshold in [
        ("normalized_value_error", 1e-4),
        ("increment_relative_error", 0.25),
        ("gradient_relative_error", 0.25),
    ]:
        values = [v["metrics"][metric] for v in local]
        maxima[metric] = max(values)
        check(metric, all(type(v) in (float, int) and 0 <= v <= threshold for v in values))
    check(
        "all LOCAL signs",
        all(v["passed"] is True and v["metrics"]["increment_sign_agrees"] is True for v in local),
    )
    diagnostics = x["central_diagnostics"]
    equal("all diagnostics", len(diagnostics), 72)
    equal("unique diagnostics", len({(v["case_id"], v["state"]) for v in diagnostics}), 72)
    equal("diagnostic regions", {v["region"] for v in diagnostics}, {"local", "outside", "uniform"})
    check(
        "diagnostic signs",
        all(v["negative_surrogate"] == (v["surrogate_value"] < 0) for v in diagnostics),
    )
    charges = {}
    commands = {v["name"]: v for v in records["audit_receipts/execution_commands.json"]}
    for stage in ("producer", "independent"):
        measured = native(records["profiles/" + stage + ".time"])
        equal(stage + " native", commands[stage]["native"], measured)
        equal(stage + " exit", commands[stage]["exit_code"], 0)
        charges[stage] = x["ledger"]["stage_charges"][stage]
        check(
            stage + " charge",
            math.isclose(
                charges[stage], measured["wall_seconds"] + 10, rel_tol=1e-12, abs_tol=1e-12
            ),
        )
    q28 = 60 + sum(charges.values())
    check("Q28", math.isclose(q28, b["q_seconds"], rel_tol=1e-12, abs_tol=1e-12))
    equal("FULL60", x["ledger"]["fully_paid_reserve_seconds"], 60)
    equal("ledger Q28", x["ledger"]["total_charged_seconds"], q28)
    p = c["cost"]["inherited_first_inclusive_maxima"]
    fixed = (
        3870.204341
        + 851.38
        + 200.98
        + 80.34
        + 3 * 1.25 * (432 * p["p_small"] + 76 * p["p_large"])
        + 3 * 200 * 1.25 * (432 * p["u_small"] + 76 * p["u_large"])
    )
    cost = fixed + q28
    check(
        "fixed cost",
        math.isclose(fixed, x["fixed_cost_without_new_charges"], rel_tol=1e-12, abs_tol=1e-12),
    )
    check(
        "added cost", math.isclose(cost, x["added_cost_view_seconds"], rel_tol=1e-12, abs_tol=1e-12)
    )
    equal(
        "original failed cost",
        x["original_failed_proxy_seconds"],
        c["legacy"]["original_failed_proxy"],
    )
    equal("cost limit", x["cost_limit_seconds"], 7200)
    check("cost stops", cost > 7200 and x["cost_feasible"] is False)
    for field in ("historical_b4_24_planning_rss", "historical_b4_24_whole_peak_rss"):
        equal(field, x[field], None)
    equal("old memory gap", x["historical_b4_24_whole_memory_proof"], False)
    equal("B419 unknown", x["historical_b4_19_case_gap_counts"], "UNKNOWN")
    equal("B424 charge", x["historical_b4_24_seconds"], 200.98)
    equal("B425 charge", x["historical_b4_25_seconds"], 80.34)
    equal("full memory", x["full_training_memory"], "PENDING")
    equal("fit memory cap", x["full_training_memory_cap_bytes"], 4294967296)
    equal("early lifecycle", x["whole_native_resource_proof"], "PENDING_POSTEXIT")
    equal("scoped postexit", records["audit_receipts/final_postexit_proof.json"]["passed"], True)
    platform = records["audit_receipts/platform_exit_binding.json"]
    equal("whole proof incomplete", platform["passed"], False)
    equal("whole peak UNKNOWN", platform["whole_observed_peak_rss_bytes"], None)
    equal("prep profile UNKNOWN", platform["preparation_native"], None)
    prep = records["audit_receipts/platform_prepare_command.json"]
    equal("retained failed prep", prep["exit_code"], 1)
    equal("retained missing profile", prep["native"], None)
    equal(
        "complete resource stop",
        records["audit_receipts/final_scope_summary.json"]["complete_resource_acceptance"],
        False,
    )
    equal("closed resource ledger", records["resource_close.json"]["ledger"], x["ledger"])
    for field, expected in (
        ("fits", 0),
        ("final_access", False),
        ("old_fresh_sealed", True),
        ("next_route", c["route"]),
    ):
        equal(field, x[field], expected)
    facts = {
        "q28": q28,
        "fixed_cost": fixed,
        "cost_before_q29": cost,
        "stable": 64 - crossing,
        "crossing": crossing,
        "max_pieces": 81,
        "local_maxima": maxima,
        "negative_diagnostics": sum(v["negative_surrogate"] for v in diagnostics),
        "failed_positions_sha256": sha(canonical(positions)),
        "legacy_failed": 69,
        "intervals": 64,
        "local_states": 32,
        "diagnostics": 72,
        "b4_28_whole_peak_rss_bytes": None,
        "full_training_memory": "PENDING",
        "cost_feasible": False,
        "fit_authorized": False,
    }
    return {
        "passed": all(v["passed"] for v in checks),
        "checks": checks,
        "facts": facts,
        "input_sha256": c["inputs_sha256"],
        "historical_scope_metadata": records["audit_receipts/final_scope_summary.json"],
        "scientific_gate_repaired": False,
        "route": c["route"],
    }
