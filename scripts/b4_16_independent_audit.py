"""Independent raw-JSON arithmetic for the B4.16 complete cost review."""

import math
import statistics
from pathlib import Path
from time import perf_counter

from b4_16_offline_adjoint_cost_review import (
    PHASE_NEXT,
    PROBE_SHA,
    STABILITY_NEXT,
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


def distribution(values):
    ordered = sorted(values)
    middle = len(values) // 2
    return {
        "count": len(values),
        "minimum": ordered[0],
        "maximum": ordered[-1],
        "sum": math.fsum(values),
        "mean": statistics.fmean(values),
        "median": (ordered[middle - 1] + ordered[middle]) / 2
        if len(values) % 2 == 0
        else ordered[middle],
    }


def agree(expected, actual):
    if isinstance(expected, dict):
        if set(expected) != set(actual):
            raise ValueError("independent field population differs")
        return sum(agree(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        if len(expected) != len(actual):
            raise ValueError("independent list population differs")
        return sum(agree(x, y) for x, y in zip(expected, actual, strict=True))
    if isinstance(expected, float):
        equal = math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-12)
    else:
        equal = type(expected) is type(actual) and expected == actual
    if not equal:
        raise ValueError("independent cost arithmetic differs")
    return 1


def reconstruct(probe, closed, report):
    plan = prior_plan()
    expected_keys = [
        (e["case"]["case_id"], state) for e in plan["entries"] for state in plan["states"]
    ]
    if (
        probe["plan"] != plan
        or [(r["case_id"], r["state"]) for r in probe["rows"]] != expected_keys
    ):
        raise ValueError("independent complete ordered fixture population differs")
    observations = []
    for index, row in enumerate(probe["rows"]):
        scale = (
            "small"
            if plan["entries"][index // 2]["case"]["problem"]["mesh"]["element_counts"][0] == 12
            else "large"
        )
        if row["scale"] != scale or len(row["timings"]) != 3:
            raise ValueError("independent complete scale/repeat population differs")
        for i, timer in enumerate(row["timings"]):
            wall, cpu = (timer[k] for k in ("wall_seconds", "cpu_seconds"))
            if not all(math.isfinite(t) and t > 0 for t in (wall, cpu)):
                raise ValueError("independent timing is not finite positive")
            observations.append(
                {
                    "case_id": row["case_id"],
                    "state": row["state"],
                    "scale": scale,
                    "repeat": i,
                    **timer,
                    "wall_minus_cpu_seconds": wall - cpu,
                }
            )
    groups = {"all": observations}
    for scale in ("small", "large"):
        groups[scale] = [o for o in observations if o["scale"] == scale]
    for i in range(3):
        groups[f"repeat_{i}"] = [o for o in observations if o["repeat"] == i]
    for cid, state in expected_keys:
        groups[f"{cid}/{state}"] = [
            o for o in observations if (o["case_id"], o["state"]) == (cid, state)
        ]
    distributions = {}
    for name, group in groups.items():
        distributions[name] = {
            metric: distribution([o[metric] for o in group])
            for metric in ("wall_seconds", "cpu_seconds", "wall_minus_cpu_seconds")
        }
    setup = probe["setup"]
    if [s["case_id"] for s in setup] != [e["case"]["case_id"] for e in plan["entries"]] or any(
        not math.isfinite(s[k]) or s[k] <= 0 for s in setup for k in ("wall_seconds", "cpu_seconds")
    ):
        raise ValueError("independent complete setup population differs")
    small, large = distributions["small"], distributions["large"]
    units = {
        "original_maximum": [small["wall_seconds"]["maximum"], large["wall_seconds"]["maximum"]],
        "wall_minimum": [small["wall_seconds"]["minimum"], large["wall_seconds"]["minimum"]],
        "wall_median": [small["wall_seconds"]["median"], large["wall_seconds"]["median"]],
        "cpu_minimum": [small["cpu_seconds"]["minimum"], large["cpu_seconds"]["minimum"]],
        "zero_small": [0.0, large["wall_seconds"]["minimum"]],
    }
    scenarios = {}
    for name, times in units.items():
        contributions = [600 * 1.25 * 432 * times[0], 600 * 1.25 * 76 * times[1]]
        additional = math.fsum(contributions)
        scenarios[name] = {
            "unit_seconds": times,
            "physics_seconds_by_scale": contributions,
            "additional_physics_seconds": additional,
            "total_prospective_seconds": additional + 3870.204341 + closed["charged_seconds"],
            "diagnostic_only": name != "original_maximum",
        }
    original = scenarios["original_maximum"]
    if not all(
        math.isclose(original[k], closed["fit_proxy"][k], rel_tol=1e-12, abs_tol=1e-12)
        for k in ("additional_physics_seconds", "total_prospective_seconds")
    ):
        raise ValueError("independent original maximum proxy differs")
    available = 7200 - 3870.204341 - closed["charged_seconds"]
    phase = (
        original["total_prospective_seconds"] > 7200
        and scenarios["zero_small"]["total_prospective_seconds"] > 7200
    )
    expected = {
        "observations": observations,
        "distributions": distributions,
        "setup": {k: distribution([s[k] for s in setup]) for k in ("wall_seconds", "cpu_seconds")},
        "scenarios": scenarios,
        "budget_requirements": {
            "available_physics_seconds": available,
            "weighted_unit_target_seconds": available / (600 * 1.25 * 508),
            "isolated_scale_unit_ceiling_seconds": [
                available / (600 * 1.25 * n) for n in (432, 76)
            ],
            "required_common_speedup": original["additional_physics_seconds"] / available,
            "required_fractional_physics_reduction": 1
            - available / original["additional_physics_seconds"],
        },
        "prior_processes": closed["processes"],
        "prior_charge_seconds_unchanged": closed["charged_seconds"],
        "prior_peak_rss_bytes_unchanged": closed["peak_rss_bytes"],
        "original_cost_gate_passed": False,
        "phase_costs_available": False,
        "full_fit_memory_feasibility_pending": True,
        "next_slice": PHASE_NEXT if phase else STABILITY_NEXT,
        "next_slice_started": False,
        "repaired_gate": False,
        "final_access": False,
        "old_fresh_sealed": True,
        "solver_calls": 0,
        "fits": 0,
        "claim": "cost_review_only_not_revised_gate_or_acceleration",
    }
    checks = agree(expected, {k: report[k] for k in expected})
    if report["plan"] != plan_payload():
        raise ValueError("independent frozen review plan differs")
    return {
        "passed": True,
        "arithmetic_conditions": checks,
        "observations": len(observations),
        "states": len(expected_keys),
        "cases": len(probe["setup"]),
        "next_slice": expected["next_slice"],
        "original_cost_gate_passed": False,
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
    probe, report = read(root, "probe.json", PROBE_SHA), read(output, "review.json")
    if report["source_revision"] != revision or report["input_sha256"] != PROBE_SHA:
        raise ValueError("independent complete source/input binding differs")
    result = reconstruct(probe, bound["resource_close.json"], report)
    profiles = {}
    for name in ("probe", "independent", "closure"):
        lines = (root / "profiles" / (name + ".time")).read_text().splitlines()
        timer = next(
            line.split()
            for line in lines
            if " real " in line and " user " in line and " sys" in line
        )
        rss = next(line.split()[0] for line in lines if "maximum resident set size" in line)
        profiles[name] = {
            "wall_seconds": float(timer[0]),
            "user_seconds": float(timer[2]),
            "system_seconds": float(timer[4]),
            "peak_rss_bytes": int(rss),
        }
    result["arithmetic_conditions"] += agree(profiles, report["prior_native_profiles"])
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
        raise RuntimeError("independent cost audit exceeds cap")
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
