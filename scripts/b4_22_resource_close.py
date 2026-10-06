"""Fully charged closure of complete or failed exclusive correctness attempts."""

from pathlib import Path
from time import perf_counter

from b4_10_resource_close import profile
from b4_22_stable_projection_correctness import (
    FAIL_NEXT,
    PASS_NEXT,
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


def close_resources(output, commands, probe, audit):
    names, seen, charges, peaks, profiles = [], set(), [], [], {}
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
            internal = (probe if name == "probe" else audit) if command["exit_code"] == 0 else None
            charge = max(wall + 10, internal["charged_seconds"] if internal else 0)
            if charge > 300:
                raise ValueError("process resource cap exceeded")
            charges.append(charge)
    if names not in (["probe"], ["probe", "independent"]):
        raise ValueError("requires one attempt per frozen numerical stage, no free retry")
    complete = (
        probe is not None and audit is not None and all(c["exit_code"] == 0 for c in commands)
    )
    if complete:
        if (
            probe["plan"] != plan_payload()
            or not audit["passed"]
            or audit["probe_sha256"] != sha(canonical(probe))
            or audit["metadata_only"]
            or audit["total_solver_calls"] != 32
            or audit["total_projection_calls"] != 304
            or audit["numerical_conditions"] != 1704
            or audit["cases"] != 8
            or audit["fixtures"] != 16
            or audit["directional_rows"] != 64
            or any(
                v["fits"] or v["final_access"] or v["repaired_gate"] or not v["old_fresh_sealed"]
                for v in (probe, audit)
            )
        ):
            raise ValueError("complete numerical audit boundary differs")
        for name, data in (("probe", probe), ("independent", audit)):
            safe_hash(output, name + ".events.jsonl", data["journal_sha256"])
    charge = sum(charges) + 60
    if charge > 660:
        raise ValueError("whole slice cap exceeded")
    accepted = complete and audit["correctness_passed"]
    return {
        "version": plan_payload()["version"],
        "closed": True,
        "charged_seconds": charge,
        "paid_reservation_seconds": 60,
        "peak_rss_bytes": max(peaks),
        "full_panel_complete": complete,
        "correctness_acceptance_passed": bool(accepted),
        "next_slice": PASS_NEXT if accepted else FAIL_NEXT,
        "next_slice_started": False,
        "profile_sha256": profiles,
        "numerical_stage_charges": dict(zip(names, charges, strict=True)),
        "failed_attempts": sum(c["exit_code"] != 0 for c in commands),
        "local_fidelity_evaluated": False,
        "fit_proxy": None,
        "full_fit_memory_feasibility_pending": True,
        "prior_b4_19_charge_unchanged": 73.93,
        "prior_b4_19_actual_counts_and_gap_still_unknown": True,
        "fits": 0,
        "new_labels": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
        "probe_sha256": sha(canonical(probe)) if probe else None,
        "independent_audit_sha256": sha(canonical(audit)) if audit else None,
    }


def main(argv=None):
    started = perf_counter()
    args, root, data, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    revision = execution_release(output)
    check_inputs(root, data)
    commands = read(output, "audit_receipts/execution_commands.json")
    values = [
        read(output, p) if (output / p).exists() else None
        for p in ("probe.json", "independent_audit.json")
    ]
    result = close_resources(output, commands, *values)
    from b4_22_independent_audit import event_prefix

    prefixes = {}
    for name in ("probe", "independent"):
        if (output / (name + ".events.jsonl")).exists():
            events, counts, pending = event_prefix(output, name, revision)
            prefixes[name] = {
                "counts": counts,
                "pending_operations": pending,
                "journal_sha256": sha((output / (name + ".events.jsonl")).read_bytes()),
            }
    result.update(
        actual_attempt_prefixes=prefixes,
        source_revision=revision,
        closure_internal_charge_seconds=perf_counter() - started + 10,
        closure_internal_peak_rss_bytes=peak_rss(),
        execution_commands_sha256=sha(canonical(commands)),
    )
    if (
        result["closure_internal_charge_seconds"] > 60
        or result["closure_internal_peak_rss_bytes"] > 1073741824
    ):
        raise ValueError("resource closure cap exceeded")
    with (output / "resource_close.json").open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
