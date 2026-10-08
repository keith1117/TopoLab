"""One immutable read-only campaign, source-only plan and native exit receipts."""

import argparse
import sys
from decimal import Decimal
from pathlib import Path

from b4_29_common import canonical, digest, read, save
from b4_29_native_execution import checked_native, invoke
from b4_31_common import contract, execute_stage, plan_payload, release
from b4_31_independent_audit import independent
from b4_31_reflection_failure_cost_review import review


def decimal(value):
    return Decimal(str(value))


def stage_accounting(output):
    commands = read(output / "audit_receipts/execution_commands.json")
    if [c["name"] for c in commands] != ["review", "independent"]:
        raise ValueError("exactly one review and one audit required")
    charges, results, peaks = {}, {}, []
    complete = True
    for command in commands:
        name = command["name"]
        path = output / (name + ".json")
        result = read(path) if path.exists() else None
        results[name] = result
        measured = checked_native(output, command) if command["native"] else None
        wall = max(
            decimal(command["observed_outer_wall_seconds"]),
            decimal(measured["wall_seconds"] if measured else 0),
        )
        charges[name] = max(wall + 10, decimal(result["internal_seconds"] if result else 0))
        if measured:
            peaks.append(measured["rss_bytes"])
        complete = bool(
            complete
            and measured
            and command["exit_code"] == 0
            and not command["terminated"]
            and result
            and charges[name] <= contract()["new_budget"][name + "_seconds"]
        )
    q31 = Decimal(60) + sum(charges.values(), Decimal(0))
    complete = bool(complete and q31 <= 180 and max(peaks, default=0) <= 1073741824)
    return commands, charges, q31, complete, results


def close(output):
    revision = release(output / "audit_receipts/production_release.json")
    _, charges, q31, complete, results = stage_accounting(output)
    metadata = all(r and r["passed"] for r in results.values())
    old_cost = Decimal(contract()["b4_30"]["cumulative_charge_decimal"])
    result = {
        "source_revision": revision,
        "plan_sha256": plan_payload()["plan_sha256"],
        "stage_charge_decimals": {k: str(v) for k, v in charges.items()},
        "q31_decimal": str(q31),
        "q31_seconds": float(q31),
        "fully_paid_reserve_seconds": 60,
        "own_stage_resource_acceptance": complete,
        "whole_resource_acceptance": "PENDING_POSTEXIT",
        "metadata_review_passed": bool(metadata),
        "scientific_gate": "FAIL",
        "immutable_B4_30_charge_decimal": str(old_cost),
        "campaign_plus_review_charge_decimal": str(old_cost + q31),
        "numerical_calls": 0,
        "fits": 0,
        "new_payload_reads": 0,
        "final_access": False,
        "old_fresh_sealed": True,
        "unknowns": contract()["unknowns"],
        "execution_commands_sha256": digest(output / "audit_receipts/execution_commands.json"),
    }
    save(output / "resource_close.json", result)
    return result


def auxiliary(output, names):
    peaks, outer = [], Decimal(0)
    for name in names:
        command = read(output / "audit_receipts" / (name + "_command.json"))
        measured = checked_native(output, command)
        if command["exit_code"] != 0 or command["terminated"]:
            raise ValueError("failed auxiliary exit remains resource failure")
        peaks.append(measured["rss_bytes"])
        outer += decimal(command["observed_outer_wall_seconds"])
    return peaks, outer


def bind(output):
    release(output / "audit_receipts/production_release.json")
    commands, charges, q31, complete, _ = stage_accounting(output)
    closed = read(output / "resource_close.json")
    peaks, _ = auxiliary(output, ("plan", "closure", "controller"))
    controller = read(output / "audit_receipts/controller_command.json")
    stage_outer = sum((decimal(c["observed_outer_wall_seconds"]) for c in commands), Decimal(0))
    reserved = max(Decimal(0), decimal(controller["observed_outer_wall_seconds"]) - stage_outer)
    result = {
        "passed_before_own_exit": bool(
            complete
            and closed["own_stage_resource_acceptance"]
            and decimal(closed["q31_decimal"]) == q31
        ),
        "whole_resource_acceptance": "PENDING_BINDER_EXIT",
        "independent_q31_decimal": str(q31),
        "independent_stage_charge_decimals": {k: str(v) for k, v in charges.items()},
        "reserved_controller_seconds_decimal": str(reserved),
        "native_rss_sum_before_binder": sum(peaks),
        "resource_close_sha256": digest(output / "resource_close.json"),
        "controller_command_sha256": digest(output / "audit_receipts/controller_command.json"),
        "old_unknowns_unchanged": True,
        "scientific_gate": "FAIL",
        "final_access": False,
    }
    save(output / "audit_receipts/platform_exit_binding.json", result)
    return result


def verify(output):
    release(output / "audit_receipts/production_release.json")
    binding = read(output / "audit_receipts/platform_exit_binding.json")
    closed = read(output / "resource_close.json")
    _, _, q31, complete, _ = stage_accounting(output)
    peaks, binder_outer = auxiliary(output, ("binder",))
    ok = (
        binding["passed_before_own_exit"]
        and complete
        and digest(output / "resource_close.json") == binding["resource_close_sha256"]
        and digest(output / "audit_receipts/controller_command.json")
        == binding["controller_command_sha256"]
        and q31 == decimal(binding["independent_q31_decimal"]) == decimal(closed["q31_decimal"])
    )
    result = {
        "passed_before_own_exit": bool(ok),
        "whole_resource_acceptance": "PENDING_VERIFIER_EXIT",
        "binding_sha256": digest(output / "audit_receipts/platform_exit_binding.json"),
        "q31_decimal": str(q31),
        "reserved_before_verifier_decimal": str(
            decimal(binding["reserved_controller_seconds_decimal"]) + binder_outer
        ),
        "native_rss_sum_before_verifier": binding["native_rss_sum_before_binder"] + sum(peaks),
        "scientific_gate": "FAIL",
        "final_access": False,
        "old_unknowns_unchanged": True,
    }
    save(output / "audit_receipts/platform_exit_verification.json", result)
    return result


def campaign(root, output, release_input):
    revision = release(release_input)  # Before creating anything or opening production metadata.
    if output.name != contract()["output_root_name"] or output.is_symlink():
        raise ValueError("fixed exclusive output root required")
    if Path(root).name != contract()["allowed_input_root_name"] or Path(root).is_symlink():
        raise ValueError("fixed nonsymlink metadata root required")
    output.mkdir()  # A second campaign cannot enter, including after a failed prefix.
    for name in ("profiles", "logs", "audit_receipts"):
        (output / name).mkdir()
    save(output / "audit_receipts/production_release.json", read(release_input))
    save(output / "audit_receipts/one_attempt.json", {"campaigns": 1, "source_revision": revision})
    save(output / "audit_receipts/plan.json", plan_payload())
    script = str(Path(__file__).resolve())
    planned = invoke(output, "plan", [sys.executable, script], 15)
    if planned["exit_code"] != 0 or planned["terminated"] or not planned["native"]:
        raise ValueError("source-only native preparation failed; no metadata entry")
    argv = [
        sys.executable,
        script,
        "--execute",
        "--input-root",
        str(root),
        "--output-root",
        str(output),
        "--mode",
    ]
    commands = [invoke(output, name, [*argv, name], 45) for name in ("review", "independent")]
    save(output / "audit_receipts/execution_commands.json", commands)
    command = invoke(output, "closure", [*argv, "close"], 15)
    if command["exit_code"] != 0 or command["terminated"]:
        raise ValueError("closure failed; preserve complete attempted prefix")
    return read(output / "resource_close.json")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.add_argument("--release", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--mode",
        choices=("campaign", "review", "independent", "close", "bind", "verify"),
        default="campaign",
    )
    args = parser.parse_args()
    if not args.execute:
        result = plan_payload()
    elif args.mode == "campaign":
        if args.release is None or args.input_root is None or args.output_root is None:
            parser.error("campaign requires explicit release and roots")
        result = campaign(args.input_root, args.output_root, args.release)
    elif args.mode in ("review", "independent"):
        result = execute_stage(
            args.mode,
            args.input_root,
            args.output_root,
            review if args.mode == "review" else independent,
        )
    else:
        result = {"close": close, "bind": bind, "verify": verify}[args.mode](args.output_root)
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
