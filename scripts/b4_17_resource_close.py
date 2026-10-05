"""Close the full offline feasibility cost, then apply the frozen negative stop rule."""

from pathlib import Path
from time import perf_counter

from b4_10_resource_close import profile
from b4_17_prepared_fem_probe import (
    arguments,
    canonical,
    check_inputs,
    execution_release,
    peak_rss,
    plan_payload,
    read,
    sha,
)


def fit_proxy(probe, total_charge):
    plan = plan_payload()
    scales = ("small", "large")
    worst = {
        s: max(
            m["wall_seconds"]
            for r in probe["rows"]
            if r["scale"] == s
            for m in r["measurements"]
            if m["arm"] == "prepared"
        )
        for s in scales
    }
    scale_by_id = {r["case_id"]: r["scale"] for r in probe["rows"]}
    setups = {
        s: max(
            t["wall_seconds"]
            for t in probe["setup"]
            if t["arm"] == "prepared" and scale_by_id[t["case_id"]] == s
        )
        for s in scales
    }
    sizes = {
        s: max(
            t["retained_array_bytes"]
            for t in probe["setup"]
            if t["arm"] == "prepared" and scale_by_id[t["case_id"]] == s
        )
        for s in scales
    }

    def weighted(values):
        return sum(n * values[s] for s, n in zip(scales, plan["fit_population"], strict=True))

    additional = plan["fit_seeds"] * plan["fit_epochs"] * plan["cost_factor"] * weighted(worst)
    setup = plan["fit_seeds"] * plan["cost_factor"] * weighted(setups)
    total = (
        additional
        + setup
        + plan["baseline_fit_seconds"]
        + plan["prior_probe_seconds"]
        + plan["prior_review_seconds"]
        + total_charge
    )
    return {
        "maximum_seconds_per_scale": worst,
        "maximum_setup_seconds_per_scale": setups,
        "additional_physics_seconds": additional,
        "full_population_preparation_seconds": setup,
        "population_retained_array_bytes_estimate": weighted(sizes),
        "total_prospective_seconds": total,
        "limit_seconds": 7200,
        "cost_feasible": total <= 7200,
        "planning_proxy_only": True,
        "full_fit_memory_feasibility_pending": True,
        "original_b4_15_proxy_seconds_unchanged": 60339.39413004646,
    }


def next_slice(numerical, cost):
    from b4_17_prepared_fem_probe import CORRECTNESS_NEXT, COST_NEXT, FIT_NEXT

    return CORRECTNESS_NEXT if not numerical else COST_NEXT if not cost else FIT_NEXT


def close_resources(output, probe, audit, commands):
    if not audit["passed"] or audit["probe_sha256"] != sha(canonical(probe)):
        raise ValueError("complete independent audit binding differs")
    if (
        probe["plan"] != plan_payload()
        or audit["measurements"] != 96
        or audit["phase_observations"] != 96
        or audit["directional_checks"] != 64
        or audit["total_solver_calls"] != 256
        or probe["fits"]
        or probe["final_access"]
        or probe["repaired_gate"]
        or not probe["old_fresh_sealed"]
    ):
        raise ValueError("complete frozen probe boundary differs")
    successful = [c for c in commands if c["exit_code"] == 0]
    if len(successful) != 2 or {c["profile"] for c in successful} != {
        "profiles/probe.time",
        "profiles/independent.time",
    }:
        raise ValueError("successful command population differs")
    profiles = output / "profiles"
    processes, hashes, peak = [], {}, 0
    for name, receipt in (("probe", probe), ("independent", audit)):
        path = profiles / (name + ".time")
        if not path.resolve().is_relative_to(profiles.resolve()):
            raise ValueError("profile escapes output")
        wall, rss = profile(path)
        charge = max(wall + 10, receipt["charged_seconds"])
        if charge > 600:
            raise ValueError("successful process exceeds cap")
        hashes[path.name] = sha(path.read_bytes())
        peak = max(peak, rss, receipt["peak_rss_bytes"])
        processes.append(
            {
                "process": name,
                "command_wall_seconds": wall,
                "closed_charge_seconds": charge,
                "peak_rss_bytes": rss,
            }
        )
    for command in successful:
        path = output / command["profile"]
        if command["profile_sha256"] != sha(path.read_bytes()):
            raise ValueError("command/native profile hash differs")
    failed = set(profiles.glob("failed_*.time"))
    for c in commands:
        path = (output / c["profile"]).resolve()
        if not path.is_relative_to(profiles.resolve()):
            raise ValueError("command profile escapes output")
        if c["exit_code"]:
            if c["profile_sha256"] != sha(path.read_bytes()):
                raise ValueError("failed command/native profile hash differs")
            failed.add(path)
    for path in sorted(failed):
        if not path.resolve().is_relative_to(profiles.resolve()):
            raise ValueError("failed profile escapes output")
        wall, rss = profile(path)
        hashes[path.name] = sha(path.read_bytes())
        peak = max(peak, rss)
        processes.append(
            {
                "process": "failed_" + path.stem,
                "command_wall_seconds": wall,
                "closed_charge_seconds": wall + 10,
                "peak_rss_bytes": rss,
            }
        )
    total = sum(p["closed_charge_seconds"] for p in processes) + 60
    peak = max(peak, peak_rss())
    if total > 1260 or peak > 1073741824:
        raise ValueError("whole offline probe exceeds resource cap")
    cost = fit_proxy(probe, total)
    import math

    from b4_17_independent_audit import independent_proxy

    independent = independent_proxy(probe, total)
    if any(
        not math.isclose(cost[k], v, rel_tol=1e-12, abs_tol=1e-12) for k, v in independent.items()
    ):
        raise ValueError("independent candidate proxy differs")
    numerical = audit["numerical_passed"]
    following = next_slice(numerical, cost["cost_feasible"])
    return {
        "processes": processes,
        "profile_sha256": hashes,
        "charged_seconds": total,
        "peak_rss_bytes": peak,
        "close_charge_seconds": 60.0,
        "fit_proxy": cost,
        "numerical_passed": numerical,
        "feasibility_passed": numerical and cost["cost_feasible"],
        "next_slice": following,
        "next_slice_started": False,
    }


def main(argv=None):
    started = perf_counter()
    args, review_root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    target = output / "resource_close.json"
    if target.exists():
        raise ValueError("refuses to overwrite resource closure")
    revision = execution_release(output)
    check_inputs(review_root)
    probe, audit = (read(output, p) for p in ("probe.json", "independent_audit.json"))
    if probe["source_revision"] != revision or audit["source_revision"] != revision:
        raise ValueError("complete source revision differs")
    if audit["source_sha256"] != sha(
        (Path(__file__).parent / "b4_17_independent_audit.py").read_bytes()
    ):
        raise ValueError("independent source differs")
    commands = read(output, "audit_receipts/execution_commands.json")
    result = close_resources(output, probe, audit, commands)
    check_inputs(review_root)
    internal = perf_counter() - started + 10
    if internal > 60:
        raise RuntimeError("resource closure exceeds reservation")
    result.update(
        version=plan_payload()["version"],
        closed=True,
        source_revision=revision,
        close_internal_charge_seconds=internal,
        source_sha256=sha(Path(__file__).read_bytes()),
        probe_sha256=sha(canonical(probe)),
        independent_audit_sha256=sha(canonical(audit)),
        execution_commands_sha256=sha(canonical(commands)),
        repaired_gate=False,
        final_access=False,
        old_fresh_sealed=True,
        prior_b4_15_charge_seconds_unchanged=84.33,
        prior_b4_16_charge_seconds_unchanged=55.99,
    )
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
