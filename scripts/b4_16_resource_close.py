"""Close complete native B4.16 review/audit costs without changing the failed Gate."""

from pathlib import Path
from time import perf_counter

from b4_10_resource_close import profile
from b4_16_offline_adjoint_cost_review import (
    BINDINGS,
    PROBE_SHA,
    arguments,
    canonical,
    check_inputs,
    execution_release,
    peak_rss,
    plan_payload,
    read,
    sha,
)


def close_resources(output, review, audit, commands):
    if not audit["passed"] or audit["review_sha256"] != sha(canonical(review)):
        raise ValueError("complete independent audit binding differs")
    if (
        review["plan"] != plan_payload()
        or audit["observations"] != 48
        or audit["states"] != 16
        or audit["cases"] != 8
        or audit["next_slice"] != review["next_slice"]
        or audit["original_cost_gate_passed"]
        or review["original_cost_gate_passed"]
        or review["fits"]
        or review["solver_calls"]
        or review["final_access"]
        or review["repaired_gate"]
        or not review["old_fresh_sealed"]
    ):
        raise ValueError("complete frozen cost review differs")
    successful = [c for c in commands if c["exit_code"] == 0]
    if len(successful) != 2 or {c["profile"] for c in successful} != {
        "profiles/review.time",
        "profiles/independent.time",
    }:
        raise ValueError("successful command population differs")
    profiles = output / "profiles"
    processes, hashes, peak = [], {}, 0
    for name, receipt in (("review", review), ("independent", audit)):
        path = profiles / (name + ".time")
        if not path.resolve().is_relative_to(profiles.resolve()):
            raise ValueError("profile escapes output")
        wall, rss = profile(path)
        charge = max(wall + 10, receipt["charged_seconds"])
        if charge > 60:
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
    if total > 180 or peak > 1073741824:
        raise ValueError("whole offline review exceeds resource cap")
    return {
        "processes": processes,
        "profile_sha256": hashes,
        "charged_seconds": total,
        "peak_rss_bytes": peak,
        "close_charge_seconds": 30.0,
        "cost_review_acceptance_passed": True,
        "original_cost_gate_passed": False,
        "next_slice": review["next_slice"],
        "next_slice_started": False,
    }


def main(argv=None):
    started = perf_counter()
    args, root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    target = output / "resource_close.json"
    if target.exists():
        raise ValueError("refuses to overwrite resource closure")
    revision = execution_release(output)
    check_inputs(root)
    review, audit = (read(output, p) for p in ("review.json", "independent_audit.json"))
    if review["source_revision"] != revision or audit["source_revision"] != revision:
        raise ValueError("complete source revision differs")
    if audit["source_sha256"] != sha(
        (Path(__file__).parent / "b4_16_independent_audit.py").read_bytes()
    ):
        raise ValueError("independent source differs")
    commands = read(output, "audit_receipts/execution_commands.json")
    result = close_resources(output, review, audit, commands)
    check_inputs(root)
    internal = perf_counter() - started + 10
    if internal > 30:
        raise RuntimeError("resource closure exceeds reservation")
    result.update(
        version=plan_payload()["version"],
        closed=True,
        source_revision=revision,
        close_internal_charge_seconds=internal,
        source_sha256=sha(Path(__file__).read_bytes()),
        review_sha256=sha(canonical(review)),
        independent_audit_sha256=sha(canonical(audit)),
        execution_commands_sha256=sha(canonical(commands)),
        protected_inputs=BINDINGS,
        probe_sha256=PROBE_SHA,
        repaired_gate=False,
        final_access=False,
        old_fresh_sealed=True,
        prior_b4_15_charge_seconds_unchanged=review["prior_charge_seconds_unchanged"],
    )
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
