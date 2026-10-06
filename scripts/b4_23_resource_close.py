"""Close all native charges and the original finite fidelity/cost decision."""

import math
from pathlib import Path
from time import perf_counter

from b4_10_resource_close import profile
from b4_23_versioned_surrogate_feasibility import (
    CORRECTNESS_NEXT,
    COST_NEXT,
    FIDELITY_NEXT,
    FIT_NEXT,
    arguments,
    canonical,
    check_inputs,
    execution_release,
    peak_rss,
    plan_payload,
    read,
    safe_hash,
    sha,
)


def fit_proxy(panel, charge):
    plan = plan_payload()
    scales = ("small", "large")
    units = {
        s: max(t["wall_seconds"] for r in panel["rows"] if r["scale"] == s for t in r["timings"])
        for s in scales
    }
    ids = {r["case_id"]: r["scale"] for r in panel["rows"]}
    setup = {
        s: max(r["wall_seconds"] for r in panel["setup"] if ids[r["case_id"]] == s) for s in scales
    }
    sizes = {
        s: max(r["retained_array_bytes"] for r in panel["setup"] if ids[r["case_id"]] == s)
        for s in scales
    }

    def weighted(values):
        return sum(n * values[s] for s, n in zip(scales, plan["fit_population"], strict=True))

    forward = plan["fit_seeds"] * plan["fit_epochs"] * plan["cost_factor"] * weighted(units)
    preparation = plan["fit_seeds"] * plan["cost_factor"] * weighted(setup)
    total = (
        forward
        + preparation
        + plan["baseline_fit_seconds"]
        + sum(plan["prior_charged_seconds"])
        + charge
    )
    return {
        "maximum_seconds_per_scale": units,
        "maximum_setup_seconds_per_scale": setup,
        "additional_surrogate_seconds": forward,
        "full_population_preparation_seconds": preparation,
        "population_retained_array_bytes_estimate": weighted(sizes),
        "total_prospective_seconds": total,
        "limit_seconds": 7200,
        "cost_feasible": total <= 7200,
        "planning_proxy_only": True,
        "full_fit_memory_feasibility_pending": True,
        "original_b4_15_proxy_seconds_unchanged": 60339.39413004646,
        "original_b4_17_proxy_seconds_unchanged": 58257.4579573346,
    }


def next_slice(integrity, fidelity, cost):
    return (
        CORRECTNESS_NEXT
        if not integrity
        else FIDELITY_NEXT
        if not fidelity
        else COST_NEXT
        if not cost
        else FIT_NEXT
    )


def close_resources(output, commands, panel, audit):
    names, seen, charges, peaks, profiles = [], set(), [], [], {}
    if [c["name"] for c in commands] not in (["plan", "probe"], ["plan", "probe", "independent"]):
        raise ValueError("requires one attempt per frozen stage, no free retry")
    for command in commands:
        name = command["name"]
        path = Path(command["profile"])
        if path.parent != Path("profiles") or path.name in seen or path.name != name + ".time":
            raise ValueError("requires distinct contained native profiles")
        seen.add(path.name)
        safe_hash(output, str(path), command["profile_sha256"])
        safe_hash(output, command["log"], command["log_sha256"])
        wall, rss = profile(output / path)
        if rss > 1073741824:
            raise ValueError("native memory cap exceeded")
        peaks.append(rss)
        profiles[path.name] = command["profile_sha256"]
        if name != "plan":
            names.append(name)
            internal = (panel if name == "probe" else audit) if command["exit_code"] == 0 else None
            if command["exit_code"] == 0 and internal is None:
                raise ValueError("successful stage missing result")
            charge = max(wall + 10, internal["charged_seconds"] if internal else 0)
            if charge > 600:
                raise ValueError("process resource cap exceeded")
            charges.append(charge)
    complete = (
        panel is not None and audit is not None and all(c["exit_code"] == 0 for c in commands)
    )
    if complete:
        if (
            panel["plan"] != plan_payload()
            or not audit["passed"]
            or audit["metadata_only"]
            or audit["probe_sha256"] != sha(canonical(panel))
            or audit["total_solver_calls"] != 432
            or audit["total_projection_calls"] != 816
            or audit["numerical_conditions"] != 3976
            or audit["arithmetic_conditions"] != 960
            or audit["cases"] != 8
            or audit["central_states"] != 72
            or audit["measurements"] != 216
            or audit["local_states"] != 32
            or audit["directional_rows"] != 64
            or any(
                v["fits"] or v["final_access"] or v["repaired_gate"] or not v["old_fresh_sealed"]
                for v in (panel, audit)
            )
        ):
            raise ValueError("complete independent panel boundary differs")
        for name, value in (("probe", panel), ("independent", audit)):
            safe_hash(output, name + ".events.jsonl", value["journal_sha256"])
    total = sum(charges) + 60
    peak = max([peak_rss(), *peaks])
    if total > 1260 or peak > 1073741824:
        raise ValueError("whole slice resource cap exceeded")
    cost = fit_proxy(panel, total) if complete else None
    if complete:
        from b4_23_independent_audit import independent_proxy

        if any(
            not math.isclose(cost[k], v, rel_tol=1e-12, abs_tol=1e-12)
            for k, v in independent_proxy(panel, total).items()
        ):
            raise ValueError("independent prospective cost arithmetic differs")
    integrity = bool(complete and audit["integrity_passed"])
    fidelity = audit["local_fidelity_passed"] if complete else None
    return {
        "version": plan_payload()["version"],
        "closed": True,
        "charged_seconds": total,
        "paid_reservation_seconds": 60,
        "peak_rss_bytes": peak,
        "full_panel_complete": complete,
        "integrity_passed": integrity,
        "local_fidelity_passed": fidelity,
        "fit_proxy": cost,
        "feasibility_passed": bool(integrity and fidelity and cost["cost_feasible"]),
        "next_slice": next_slice(integrity, fidelity, cost["cost_feasible"] if cost else False),
        "next_slice_started": False,
        "profile_sha256": profiles,
        "numerical_stage_charges": dict(zip(names, charges, strict=True)),
        "failed_attempts": sum(c["exit_code"] != 0 for c in commands),
        "full_fit_memory_feasibility_pending": True,
        "prior_charged_seconds_unchanged": plan_payload()["prior_charged_seconds"],
        "prior_b4_19_actual_counts_and_gap_still_unknown": True,
        "fits": 0,
        "new_labels": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
        "probe_sha256": sha(canonical(panel)) if panel else None,
        "independent_audit_sha256": sha(canonical(audit)) if audit else None,
    }


def main(argv=None):
    started = perf_counter()
    args, root, data, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    if (output / "resource_close.json").exists():
        raise ValueError("refuses to overwrite resource closure")
    revision = execution_release(output)
    check_inputs(root, data)
    commands = read(output, "audit_receipts/execution_commands.json")
    panel, audit = [
        read(output, p) if (output / p).exists() else None
        for p in ("probe.json", "independent_audit.json")
    ]
    if any(value is not None and value["source_revision"] != revision for value in (panel, audit)):
        raise ValueError("complete production source differs")
    result = close_resources(output, commands, panel, audit)
    from b4_23_independent_audit import event_prefix, expected_events

    prefixes = {}
    for name in ("probe", "independent"):
        if (output / (name + ".events.jsonl")).exists():
            events, counts, pending = event_prefix(output, name, revision)
            if result["full_panel_complete"] and (
                pending or [e["event"] for e in events] != expected_events(name == "independent")
            ):
                raise ValueError("complete durable stage order differs")
            prefixes[name] = {
                "counts": counts,
                "pending_operations": pending,
                "events": len(events),
                "journal_sha256": sha((output / (name + ".events.jsonl")).read_bytes()),
            }
    result.update(
        actual_attempt_prefixes=prefixes,
        source_revision=revision,
        closure_internal_charge_seconds=perf_counter() - started + 10,
        closure_internal_peak_rss_bytes=peak_rss(),
        execution_commands_sha256=sha(canonical(commands)),
    )
    result["peak_rss_bytes"] = max(
        result["peak_rss_bytes"], result["closure_internal_peak_rss_bytes"]
    )
    if result["closure_internal_charge_seconds"] > 60 or result["peak_rss_bytes"] > 1073741824:
        raise ValueError("resource closure cap exceeded")
    with (output / "resource_close.json").open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
