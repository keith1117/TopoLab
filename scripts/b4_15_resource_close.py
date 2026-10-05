"""Close the full offline feasibility cost, then apply the frozen negative stop rule."""

from pathlib import Path
from time import perf_counter

from b4_10_resource_close import profile
from b4_15_offline_compliance_adjoint import (
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
    worst = {
        scale: max(
            t["wall_seconds"] for r in probe["rows"] if r["scale"] == scale for t in r["timings"]
        )
        for scale in ("small", "large")
    }
    additional = (
        plan["fit_seeds"]
        * plan["fit_epochs"]
        * plan["cost_factor"]
        * sum(
            count * worst[scale]
            for scale, count in zip(("small", "large"), plan["fit_population"], strict=True)
        )
    )
    total = additional + plan["baseline_fit_seconds"] + total_charge
    return {
        "maximum_seconds_per_scale": worst,
        "additional_physics_seconds": additional,
        "total_prospective_seconds": total,
        "limit_seconds": 7200,
        "cost_feasible": total <= 7200,
        "planning_proxy_only": True,
        "full_fit_memory_feasibility_pending": True,
        "conditional_amortization": [
            {
                "queries": n,
                "assumed_saving_seconds_per_query": saving,
                "physics_cost_seconds_per_query": additional / n,
                "net_seconds_after_complete_fit_proxy": n * saving - total,
                "break_even_queries": total / saving,
                "observed_acceleration": False,
            }
            for n in (1000, 10000)
            for saving in (0.1, 1.0)
        ],
    }


def close_resources(output, probe, audit, commands):
    if not audit["passed"] or audit["probe_sha256"] != sha(canonical(probe)):
        raise ValueError("complete independent audit binding differs")
    if (
        probe["plan"] != plan_payload()
        or audit["directional_checks"] != 64
        or audit["total_solver_calls"] != 200
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
    total = sum(p["closed_charge_seconds"] for p in processes) + 30
    peak = max(peak, peak_rss())
    if total > 1260 or peak > 1073741824:
        raise ValueError("whole offline probe exceeds resource cap")
    cost = fit_proxy(probe, total)
    numerical = audit["numerical_passed"]
    next_slice = (
        "B4.16 bounded adjoint correctness review"
        if not numerical
        else "B4.16 bounded offline adjoint cost-feasibility review"
        if not cost["cost_feasible"]
        else "B4.16 compliance-objective fit preregistration"
    )
    return {
        "processes": processes,
        "profile_sha256": hashes,
        "charged_seconds": total,
        "peak_rss_bytes": peak,
        "close_charge_seconds": 30.0,
        "fit_proxy": cost,
        "numerical_passed": numerical,
        "feasibility_passed": numerical and cost["cost_feasible"],
        "next_slice": next_slice,
        "next_slice_started": False,
    }


def main(argv=None):
    started = perf_counter()
    args, review_root, data_root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    target = output / "resource_close.json"
    if target.exists():
        raise ValueError("refuses to overwrite resource closure")
    revision = execution_release(output)
    check_inputs(review_root, data_root)
    probe, audit = (read(output, p) for p in ("probe.json", "independent_audit.json"))
    if probe["source_revision"] != revision or audit["source_revision"] != revision:
        raise ValueError("complete source revision differs")
    if audit["source_sha256"] != sha(
        (Path(__file__).parent / "b4_15_independent_audit.py").read_bytes()
    ):
        raise ValueError("independent source differs")
    commands = read(output, "audit_receipts/execution_commands.json")
    result = close_resources(output, probe, audit, commands)
    check_inputs(review_root, data_root)
    internal = perf_counter() - started + 10
    if internal > 30:
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
        prior_b4_14_charge_seconds_unchanged=50.39,
    )
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
