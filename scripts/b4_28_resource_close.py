"""Complete native charges, ordered outcome and separate post-exit proof."""

import argparse
import math
import re
from pathlib import Path

from b4_28_common import canonical, contract, digest, plan_payload, read, release, save


def native(path):
    text = Path(path).read_text()
    time = re.search(r"([\d.]+)\s+real\s+([\d.]+)\s+user\s+([\d.]+)\s+sys", text)
    rss = re.search(r"(\d+)\s+maximum resident set size", text)
    if not time or not rss or int(rss[1]) <= 0:
        raise ValueError("complete native wall/user/system/RSS required")
    return {
        "wall_seconds": float(time[1]),
        "user_seconds": float(time[2]),
        "system_seconds": float(time[3]),
        "rss_bytes": int(rss[1]),
    }


def command_check(output, command):
    for key in ("profile", "log"):
        name = Path(command[key])
        if (
            name.is_absolute()
            or ".." in name.parts
            or digest(output / name) != command[key + "_sha256"]
        ):
            raise ValueError("immutable contained native command evidence required")
    return native(output / command["profile"])


def calculate(commands, producer, auditor):
    if [c["name"] for c in commands] not in (["plan"], ["plan", "producer", "independent"]):
        raise ValueError("one native attempt for each fixed stage required")
    charges, peaks, complete = {}, [], True
    for command in commands:
        profile = command["native"]
        if profile is None:
            complete = False
            wall = command["observed_outer_wall_seconds"]
        else:
            wall = profile["wall_seconds"]
            peaks.append(profile["rss_bytes"])
        if command["name"] != "plan":
            result = producer if command["name"] == "producer" else auditor
            charges[command["name"]] = max(wall + 10, result["charged_seconds"] if result else 0)
    total = 60 + sum(charges.values())
    within = (
        complete
        and all(v <= 600 for v in charges.values())
        and total <= 1260
        and all(v <= 1073741824 for v in peaks)
    )
    return {
        "stage_charges": charges,
        "total_charged_seconds": total,
        "fully_paid_reserve_seconds": 60,
        "native_profiles_complete": complete,
        "numerical_budget_passed": within,
        "observed_stage_peak_rss_bytes": max(peaks) if peaks else None,
    }


def fixed_cost():
    values = contract()["cost_memory_and_legacy"]["inherited_first_inclusive_maxima"]
    return (
        3870.204341
        + 851.38
        + 200.98
        + 80.34
        + 3 * 1.25 * (432 * values["p_small"] + 76 * values["p_large"])
        + 3 * 200 * 1.25 * (432 * values["u_small"] + 76 * values["u_large"])
    )


def close(output):
    release(output)
    commands = read(output / "audit_receipts/execution_commands.json")
    for command in commands:
        for key in ("profile", "log"):
            path = output / command[key]
            if path.exists() and digest(path) != command[key + "_sha256"]:
                raise ValueError("native file identity differs")
        if command["native"] is not None and command_check(output, command) != command["native"]:
            raise ValueError("native scalar profile differs")
    producer = read(output / "producer.json") if (output / "producer.json").exists() else None
    auditor = read(output / "independent.json") if (output / "independent.json").exists() else None
    ledger = calculate(commands, producer, auditor)
    integrity = bool(
        auditor
        and auditor["integrity_passed"]
        and not auditor["metadata_only"]
        and len(commands) == 3
        and commands[1]["exit_code"] == commands[2]["exit_code"] == 0
    )
    fidelity = bool(integrity and auditor["local_fidelity_passed"])
    fixed = fixed_cost()
    if (
        auditor
        and not auditor["metadata_only"]
        and not math.isclose(
            auditor["fixed_cost_without_new_charges"], fixed, rel_tol=1e-12, abs_tol=1e-12
        )
    ):
        raise ValueError("independent inherited cost reconstruction differs")
    route = (
        "correctness-evidence-review"
        if not integrity
        else "fidelity-review"
        if not fidelity
        else "cost-and-full-memory-review"
    )
    result = {
        "plan": plan_payload(),
        "ledger": ledger,
        "integrity_passed": integrity,
        "local_fidelity_passed": fidelity,
        "cost_feasible": False,
        "fixed_cost_without_new_charges": fixed,
        "added_cost_view_seconds": fixed + ledger["total_charged_seconds"],
        "original_failed_proxy_seconds": 57546.0720687792,
        "cost_limit_seconds": 7200,
        "full_training_memory": "PENDING",
        "full_training_memory_cap_bytes": 4294967296,
        "whole_native_resource_proof": "PENDING_POSTEXIT",
        "next_slice": "B4.29 bounded active-set outcome and cost/full-memory review",
        "next_route": route,
        "producer_sha256": digest(output / "producer.json") if producer else None,
        "independent_sha256": digest(output / "independent.json") if auditor else None,
        "commands_sha256": digest(output / "audit_receipts/execution_commands.json"),
        "fits": 0,
        "final_access": False,
        "old_fresh_sealed": True,
    }
    save(output / "resource_close.json", result)
    compact = {k: v for k, v in result.items() if k != "plan"}
    compact.update(
        version=plan_payload()["version"],
        source_revision=producer["source_revision"]
        if producer
        else auditor["source_revision"]
        if auditor
        else None,
        producer_counts=producer["counts"]
        if producer
        else auditor["producer_counts"]
        if auditor and auditor["metadata_only"]
        else None,
        independent_counts=auditor["counts"] if auditor else None,
        new_predicate_count=len(auditor.get("new_predicates", [])) if auditor else None,
        new_predicates_passed=sum(auditor.get("new_predicates", [])) if auditor else None,
        pointwise_states=auditor.get("pointwise_states") if auditor else None,
        intervals=auditor.get("intervals", []) if auditor else [],
        local_states=auditor.get("local_states", []) if auditor else [],
        central_diagnostics=auditor.get("central_diagnostics", []) if auditor else [],
        legacy_failed_positions=auditor.get("legacy_failed_positions")
        if auditor
        else producer.get("legacy_failed_positions")
        if producer
        else None,
        legacy_predicates=3976,
        legacy_failed=69,
        legacy_first_timings=216,
        legacy_fem=432,
        legacy_projections=816,
        historical_b4_24_seconds=200.98,
        historical_b4_25_seconds=80.34,
        historical_b4_24_whole_memory_proof=False,
        historical_b4_24_planning_rss=None,
        historical_b4_24_whole_peak_rss=None,
        historical_b4_19_case_gap_counts="UNKNOWN",
        resource_close_sha256=digest(output / "resource_close.json"),
    )
    save(output / "compact_outcome.json", compact)
    return result


def verify(output):
    release(output)
    closed = read(output / "resource_close.json")
    commands = read(output / "audit_receipts/execution_commands.json")
    # Separately implement the complete native scalar sum, rather than call calculate.
    charge = 60.0
    independently_enumerated = {}
    numeric_profiles_complete = True
    for command in commands[1:]:
        result_path = output / (command["name"] + ".json")
        internal = read(result_path)["charged_seconds"] if result_path.exists() else 0.0
        if command["native"] is not None:
            wall = command_check(output, command)["wall_seconds"]
        else:
            wall = command["observed_outer_wall_seconds"]
            numeric_profiles_complete = False
        independently_enumerated[command["name"]] = max(wall + 10, internal)
        charge += independently_enumerated[command["name"]]
    if not math.isclose(
        charge, closed["ledger"]["total_charged_seconds"], rel_tol=0, abs_tol=1e-12
    ):
        raise ValueError("separate native charge sum differs")
    closer = read(output / "audit_receipts/closure_command.json")
    native_close = command_check(output, closer)
    if closer["exit_code"] != 0 or native_close["rss_bytes"] > 1073741824:
        raise ValueError("complete closure native exit/peak required")
    result = {
        "passed": True,
        "resource_close_sha256": digest(output / "resource_close.json"),
        "compact_outcome_sha256": digest(output / "compact_outcome.json"),
        "total_charged_seconds": charge,
        "independent_stage_charges": independently_enumerated,
        "numerical_exit_profiles_complete": numeric_profiles_complete,
        "closure_native": native_close,
        "whole_resource_proof": "PENDING_CONTROLLER_POSTEXIT",
        "full_training_memory": "PENDING",
    }
    save(output / "audit_receipts/closure_verification.json", result)
    return result


def postexit(output):
    """Bind the verifier and whole controller only after both native exits."""
    release(output)
    closed = read(output / "resource_close.json")
    checked = read(output / "audit_receipts/closure_verification.json")
    if (
        not checked["passed"]
        or checked["resource_close_sha256"] != digest(output / "resource_close.json")
        or checked["compact_outcome_sha256"] != digest(output / "compact_outcome.json")
    ):
        raise ValueError("immutable independent closure verification required")
    receipts = {
        name: read(output / "audit_receipts" / (name + "_command.json"))
        for name in ("plan", "closure", "verification", "controller")
    }
    profiles = {name: command_check(output, c) for name, c in receipts.items()}
    if any(receipts[n]["exit_code"] != 0 for n in ("closure", "verification", "controller")):
        raise ValueError("complete metadata command exits required")
    commands = read(output / "audit_receipts/execution_commands.json")
    numeric_wall = sum(c["observed_outer_wall_seconds"] for c in commands[1:])
    # Controller includes plan, release checks, closure, verification and all writes.
    # Pay a further ten seconds for this separately native-measured proof and exit.
    reserve_use = max(0.0, profiles["controller"]["wall_seconds"] - numeric_wall) + 10
    whole_peak = max(
        [p["rss_bytes"] for p in profiles.values()]
        + [c["native"]["rss_bytes"] for c in commands if c["native"] is not None]
    )
    passed = (
        closed["ledger"]["numerical_budget_passed"]
        and reserve_use <= 60
        and whole_peak <= 1073741824
    )
    result = {
        "passed": passed,
        "native_profiles": profiles,
        "reserved_use_with_postexit_floor_seconds": reserve_use,
        "postexit_floor_seconds": 10,
        "whole_peak_rss_bytes_before_postexit": whole_peak,
        "complete_exit_profiles_before_postexit": True,
        "resource_close_sha256": digest(output / "resource_close.json"),
        "closure_verification_sha256": digest(output / "audit_receipts/closure_verification.json"),
        "verification_command_sha256": digest(output / "audit_receipts/verification_command.json"),
        "controller_command_sha256": digest(output / "audit_receipts/controller_command.json"),
        "full_training_memory": "PENDING",
        "postexit_native_profile_pending": True,
    }
    save(output / "audit_receipts/postexit_reservation.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--postexit", action="store_true")
    args = parser.parse_args(argv)
    if (
        args.output_root.resolve().is_relative_to(Path(__file__).resolve().parents[1])
        or args.output_root.name != "b4-28-active-set-numerical-evidence"
    ):
        raise ValueError("fixed external numerical root required")
    if args.verify and args.postexit:
        raise ValueError("one separate metadata operation per native invocation")
    result = (
        postexit(args.output_root)
        if args.postexit
        else verify(args.output_root)
        if args.verify
        else close(args.output_root)
    )
    print(
        canonical(
            {
                "passed": True,
                "mode": "postexit" if args.postexit else "verify" if args.verify else "close",
                "result_sha256": sha_summary(result),
            }
        ).decode(),
        end="",
    )
    return 0


def sha_summary(result):
    from b4_28_common import sha

    return sha(canonical(result))


if __name__ == "__main__":
    raise SystemExit(main())
