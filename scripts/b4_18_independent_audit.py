"""Independent arithmetic over retained B4.17 scalars; no FEM or loss evaluation."""

import math
from pathlib import Path
from time import perf_counter

from b4_16_independent_audit import agree, distribution
from b4_18_fem_objective_method_review import (
    PROBE_SHA,
    SOLVER_NEXT,
    SURROGATE_NEXT,
    arguments,
    canonical,
    check_inputs,
    execution_release,
    peak_rss,
    plan_payload,
    prior_plan,
    read,
    sha,
)


def reconstruct(probe, closed, report):
    plan = prior_plan()
    ids = [e["case"]["case_id"] for e in plan["entries"]]
    expected_rows = [(cid, s) for cid in ids for s in ("interior", "clipped")]
    if (
        probe["plan"] != plan
        or [(r["case_id"], r["state"]) for r in probe["rows"]] != expected_rows
    ):
        raise ValueError("independent complete fixture population differs")
    if [(s["case_id"], s["arm"]) for s in probe["setup"]] != [
        (cid, a) for cid in ids for a in ("original", "prepared")
    ]:
        raise ValueError("independent setup population differs")
    observations, phase_rows = [], []
    for index, row in enumerate(probe["rows"]):
        scale = (
            "small"
            if plan["entries"][index // 2]["case"]["problem"]["mesh"]["element_counts"][0] == 12
            else "large"
        )
        order = [
            (0, "prepared"),
            (0, "original"),
            (1, "original"),
            (1, "prepared"),
            (2, "prepared"),
            (2, "original"),
        ]
        if (
            row["scale"] != scale
            or [(m["repeat"], m["arm"]) for m in row["measurements"]] != order
            or [p["phase"] for p in row["phases"]] != plan["phases"]
        ):
            raise ValueError("independent paired/phase order differs")
        for timing in row["measurements"] + row["phases"] + [row["phase_total"]]:
            if any(
                not math.isfinite(timing[k]) or timing[k] <= 0
                for k in ("wall_seconds", "cpu_seconds")
            ):
                raise ValueError("independent timer must be positive finite")
        for k in ("wall_seconds", "cpu_seconds"):
            remainder = row["phase_total"][k] - sum(p[k] for p in row["phases"])
            if remainder < -1e-12:
                raise ValueError("independent exclusive phase total differs")
            agree(float(remainder), row["phase_residual"][k])
        identity = {"case_id": row["case_id"], "state": row["state"], "scale": scale}
        for measurement in row["measurements"]:
            observations.append(
                {
                    **identity,
                    **{k: measurement[k] for k in ("repeat", "arm", "wall_seconds", "cpu_seconds")},
                }
            )
        phase_rows.append(
            {**identity, **{k: row[k] for k in ("phases", "phase_total", "phase_residual")}}
        )
    for s in probe["setup"]:
        if any(not math.isfinite(s[k]) or s[k] <= 0 for k in ("wall_seconds", "cpu_seconds")) or (
            s["arm"] == "prepared"
            and (type(s["retained_array_bytes"]) is not int or s["retained_array_bytes"] <= 0)
        ):
            raise ValueError("independent setup timer/bytes differs")
    distributions, attribution, setups, remaining = {}, {}, {}, []
    for scale in ("small", "large"):
        selected = [r for r in phase_rows if r["scale"] == scale]
        distributions[scale] = {}
        for arm in ("prepared", "original"):
            times = [o for o in observations if o["scale"] == scale and o["arm"] == arm]
            distributions[scale][arm] = {
                k: distribution([o[k] for o in times]) for k in ("wall_seconds", "cpu_seconds")
            }
        attribution[scale] = {}
        for metric in ("wall_seconds", "cpu_seconds"):
            phase_sums = {
                p: sum(t[metric] for r in selected for t in r["phases"] if t["phase"] == p)
                for p in plan["phases"]
            }
            total = sum(r["phase_total"][metric] for r in selected)
            attribution[scale][metric] = {
                "phase_sums": phase_sums,
                "outer_sum": total,
                "residual_sum": sum(r["phase_residual"][metric] for r in selected),
                "factorization_share": phase_sums["factorization"] / total,
            }
        selected_ids = {r["case_id"] for r in selected}
        timers = [
            s for s in probe["setup"] if s["case_id"] in selected_ids and s["arm"] == "prepared"
        ]
        setups[scale] = {
            "wall": distribution([s["wall_seconds"] for s in timers]),
            "cpu": distribution([s["cpu_seconds"] for s in timers]),
            "retained_array_maximum_bytes": max(s["retained_array_bytes"] for s in timers),
        }
        remaining.append(
            max(r["phase_total"]["wall_seconds"] - r["phases"][3]["wall_seconds"] for r in selected)
        )
    prepare = (
        3
        * 1.25
        * (432 * setups["small"]["wall"]["maximum"] + 76 * setups["large"]["wall"]["maximum"])
    )
    fixed = math.fsum([3870.204341, 84.33, 55.99, closed["charged_seconds"], prepare])
    available = 7200 - fixed
    if available <= 0:
        raise ValueError("independent fixed costs exhaust budget")
    units = {
        "prepared_maximum": [
            distributions[s]["prepared"]["wall_seconds"]["maximum"] for s in ("small", "large")
        ],
        "prepared_minimum": [
            distributions[s]["prepared"]["wall_seconds"]["minimum"] for s in ("small", "large")
        ],
        "zero_small": [0.0, distributions["large"]["prepared"]["wall_seconds"]["minimum"]],
        "zero_factorization_instrumented": remaining,
    }
    scenarios = {}
    for name, times in units.items():
        contributions = [750 * 432 * times[0], 750 * 76 * times[1]]
        extra = sum(contributions)
        scenarios[name] = {
            "unit_seconds": times,
            "physics_seconds_by_scale": contributions,
            "additional_physics_seconds": extra,
            "total_prospective_seconds": extra + fixed,
            "diagnostic_only": name != "prepared_maximum",
        }
    for k in ("additional_physics_seconds", "total_prospective_seconds"):
        agree(float(scenarios["prepared_maximum"][k]), closed["fit_proxy"][k])
    array_bytes = (
        432 * setups["small"]["retained_array_maximum_bytes"]
        + 76 * setups["large"]["retained_array_maximum_bytes"]
    )
    if array_bytes != closed["fit_proxy"]["population_retained_array_bytes_estimate"]:
        raise ValueError("independent static population memory differs")
    recommend = (
        scenarios["prepared_maximum"]["total_prospective_seconds"] > 7200
        and scenarios["zero_small"]["total_prospective_seconds"] > 7200
        and attribution["large"]["wall_seconds"]["factorization_share"] >= 0.5
    )
    expected = {
        "plan": plan_payload(),
        "observations": observations,
        "phase_rows": phase_rows,
        "distributions": distributions,
        "phase_attribution": attribution,
        "setup": setups,
        "scenarios": scenarios,
        "full_population_preparation_seconds": prepare,
        "budget_requirements": {
            "available_physics_seconds": available,
            "weighted_unit_target_seconds": available / 381000,
            "isolated_scale_unit_ceiling_seconds": [available / 324000, available / 57000],
            "required_common_speedup": scenarios["prepared_maximum"]["additional_physics_seconds"]
            / available,
        },
        "memory": {
            "population_static_array_bytes_estimate": array_bytes,
            "four_gib_minus_static_bytes": 4294967296 - array_bytes,
            "full_fit_feasibility_pending": True,
        },
        "method_dispositions": {
            "immutable_setup_reuse": "stopped_failed_B4_17_cost_gate",
            "startup_only_repair": "startup_descriptions_cannot_replace_frozen_gate",
            "stale_numeric_factorization": "incompatible_with_changing_density_and_exact_adjoint",
            "new_ordering_or_iterative_solver": (
                "deferred_requires_separate_numerical_cost_contract"
            ),
            "fixed_terminal_weighted_mse": "prior_B4_6_confirmation_reliability_failure_preserved",
            "local_signed_compliance_tangent": (
                "train_only_fidelity_gradient_cost_probe_before_any_fit"
            ),
        },
        "prior_charge_seconds_unchanged": closed["charged_seconds"],
        "prior_peak_rss_bytes_unchanged": closed["peak_rss_bytes"],
        "original_b4_15_proxy_seconds_unchanged": 60339.39413004646,
        "original_cost_gate_passed": False,
        "next_slice": SURROGATE_NEXT if recommend else SOLVER_NEXT,
        "next_slice_started": False,
        "repaired_gate": False,
        "final_access": False,
        "old_fresh_sealed": True,
        "solver_calls": 0,
        "fits": 0,
        "claim": "method_review_only_not_revised_gate_or_acceleration",
    }
    checks = agree(expected, {k: report[k] for k in expected})
    return {
        "passed": True,
        "arithmetic_conditions": checks,
        "cases": 8,
        "states": 16,
        "paired_measurements": len(observations),
        "phase_intervals": sum(len(r["phases"]) for r in phase_rows),
        "method_dispositions": 6,
        "original_cost_gate_passed": False,
        "next_slice": expected["next_slice"],
    }


def main(argv=None):
    started = perf_counter()
    args, root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    target = output / "independent_audit.json"
    if target.exists():
        raise ValueError("refuses to overwrite independent audit")
    revision = execution_release(output)
    bound = check_inputs(root)
    report = read(output, "review.json")
    if report["source_revision"] != revision or report["input_sha256"] != PROBE_SHA:
        raise ValueError("independent source/input binding differs")
    result = reconstruct(read(root, "probe.json", PROBE_SHA), bound["resource_close.json"], report)
    check_inputs(root)
    result.update(
        source_revision=revision,
        source_sha256=sha(Path(__file__).read_bytes()),
        review_sha256=sha(canonical(report)),
        probe_sha256=PROBE_SHA,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
    )
    if result["charged_seconds"] > 60 or result["peak_rss_bytes"] > 1073741824:
        raise RuntimeError("independent method audit exceeds cap")
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
