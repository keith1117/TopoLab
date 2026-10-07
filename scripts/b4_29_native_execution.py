"""Single bounded readonly chain, immutable native closure and output-free plan."""

import argparse
import math
import os
import signal
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from time import perf_counter

from b4_29_common import (
    canonical,
    contract,
    digest,
    execute_stage,
    native,
    plan_payload,
    read,
    release,
    save,
)


def invoke(output, name, argv, timeout):
    profile = output / "profiles" / (name + ".time")
    log = output / "logs" / (name + ".log")
    started = perf_counter()
    terminated = False
    with log.open("xb") as stream:
        if profile.exists():
            raise FileExistsError(profile)
        child = subprocess.Popen(
            ["/usr/bin/time", "-l", "-o", str(profile), *argv],
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            code = child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            terminated = True
            os.killpg(child.pid, signal.SIGTERM)
            try:
                code = child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                code = child.wait(timeout=2)
    elapsed = perf_counter() - started
    try:
        measured = native(profile.read_text())
    except (ValueError, FileNotFoundError):
        measured = None
    command = {
        "name": name,
        "argv": argv,
        "exit_code": code,
        "terminated": terminated,
        "observed_outer_wall_seconds": elapsed,
        "native": measured,
        "profile": str(profile.relative_to(output)),
        "profile_sha256": digest(profile) if profile.exists() else None,
        "log": str(log.relative_to(output)),
        "log_sha256": digest(log),
    }
    save(output / "audit_receipts" / (name + "_command.json"), command)
    return command


def checked_native(output, command):
    for field in ("profile", "log"):
        name = Path(command[field])
        if (
            name.is_absolute()
            or ".." in name.parts
            or digest(output / name) != command[field + "_sha256"]
        ):
            raise ValueError("immutable contained command required")
    measured = native((output / command["profile"]).read_text())
    if measured != command["native"]:
        raise ValueError("native record differs")
    return measured


def close(output):
    revision = release(output)
    commands = read(output / "audit_receipts/execution_commands.json")
    if [v["name"] for v in commands] != ["review", "independent"]:
        raise ValueError("exactly one review and one scalar audit required")
    charges, complete, peaks = {}, True, []
    results = {}
    for command in commands:
        name = command["name"]
        result = read(output / (name + ".json")) if (output / (name + ".json")).exists() else None
        results[name] = result
        if command["native"]:
            measured = checked_native(output, command)
            wall = measured["wall_seconds"]
            peaks.append(measured["rss_bytes"])
        else:
            wall = command["observed_outer_wall_seconds"]
            complete = False
        charges[name] = max(wall + 10, result["internal_seconds"] if result else 0)
        complete = bool(
            complete and command["exit_code"] == 0 and not command["terminated"] and result
        )
    q29 = 60 + sum(charges.values())
    passed = (
        complete
        and max(peaks, default=0) <= 1073741824
        and all(v <= 60 for v in charges.values())
        and q29 <= 180
    )
    review_passed = bool(results["review"] and results["review"]["passed"])
    audit_passed = bool(results["independent"] and results["independent"]["passed"])
    facts = results["independent"].get("facts") if results["independent"] else None
    cost = facts["cost_before_q29"] + q29 if facts else None
    result = {
        "source_revision": revision,
        "plan_sha256": plan_payload()["plan_sha256"],
        "stage_charges": charges,
        "fully_paid_reserve_seconds": 60,
        "q29_seconds": q29,
        "own_stage_resource_acceptance": passed,
        "whole_resource_acceptance": "PENDING_POSTEXIT",
        "scalar_review_passed": review_passed,
        "independent_scalar_audit_passed": audit_passed,
        "metadata_review_passed": review_passed and audit_passed,
        "known_added_cost_seconds": cost,
        "cost_feasible": bool(cost is not None and cost <= 7200),
        "full_training_memory": "PENDING",
        "b4_28_resource_acceptance": False,
        "b4_28_whole_peak_rss_bytes": None,
        "fit_authorized": False,
        "numerical_calls": 0,
        "fits": 0,
        "final_access": False,
        "old_fresh_sealed": True,
        "resource_commands_sha256": digest(output / "audit_receipts/execution_commands.json"),
    }
    save(output / "resource_close.json", result)
    return result


def verify(output):
    release(output)
    closed = read(output / "resource_close.json")
    total = Decimal(60)
    for command in read(output / "audit_receipts/execution_commands.json"):
        result = (
            read(output / (command["name"] + ".json"))
            if (output / (command["name"] + ".json")).exists()
            else None
        )
        wall = Decimal(str(command["observed_outer_wall_seconds"]))
        if command["native"]:
            wall = Decimal(str(checked_native(output, command)["wall_seconds"]))
        total += max(wall + Decimal(10), Decimal(str(result["internal_seconds"] if result else 0)))
    closure = read(output / "audit_receipts/closure_command.json")
    profile = checked_native(output, closure)
    result = {
        "passed": math.isclose(float(total), closed["q29_seconds"], rel_tol=0, abs_tol=1e-12)
        and closure["exit_code"] == 0
        and profile["rss_bytes"] <= 1073741824,
        "independent_decimal_q29": str(total),
        "resource_close_sha256": digest(output / "resource_close.json"),
        "closure_command_sha256": digest(output / "audit_receipts/closure_command.json"),
        "full_training_memory": "PENDING",
        "b4_28_unknowns_retained": True,
    }
    save(output / "audit_receipts/closure_verification.json", result)
    return result


def postexit(output):
    release(output)
    controller = read(output / "audit_receipts/controller_command.json")
    verifier = read(output / "audit_receipts/verification_command.json")
    control_native = checked_native(output, controller)
    verify_native = checked_native(output, verifier)
    verified = read(output / "audit_receipts/closure_verification.json")
    result = {
        "passed": controller["exit_code"] == verifier["exit_code"] == 0 and verified["passed"],
        "source_revision": release(output),
        "whole_peak_rss_bytes_before_postexit": max(
            control_native["rss_bytes"], verify_native["rss_bytes"]
        ),
        "controller_command_sha256": digest(output / "audit_receipts/controller_command.json"),
        "verification_command_sha256": digest(output / "audit_receipts/verification_command.json"),
        "closure_verification_sha256": digest(output / "audit_receipts/closure_verification.json"),
        "fully_paid_reserve_seconds": 60,
        "final_metadata_exit_floor_seconds": 10,
        "historical_unknowns_retained": True,
    }
    save(output / "audit_receipts/postexit_reservation.json", result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--mode",
        choices=("chain", "review", "independent", "close", "verify", "postexit"),
        default="chain",
    )
    args = parser.parse_args(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    root, output = args.input_root.resolve(), args.output_root.resolve()
    if (
        root == output
        or root.is_relative_to(output)
        or output.is_relative_to(root)
        or root.is_relative_to(Path(__file__).resolve().parents[1])
        or output.is_relative_to(Path(__file__).resolve().parents[1])
        or root.name != contract()["allowed_input_root_name"]
        or output.name != "b4-29-active-set-outcome-review"
    ):
        raise ValueError("fixed separate external roots required")
    release(output)
    if args.mode in ("review", "independent"):
        if args.mode == "review":
            from b4_29_outcome_review import review as algorithm
        else:
            from b4_29_independent_audit import audit as algorithm
        result = execute_stage(args.mode, root, output, algorithm)
    elif args.mode in ("close", "verify", "postexit"):
        result = {"close": close, "verify": verify, "postexit": postexit}[args.mode](output)
    else:
        save(
            output / "audit_receipts/one_attempt.json",
            {"attempts": 1, "source_revision": release(output), "numerical_calls": 0},
        )
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--input-root",
            str(root),
            "--output-root",
            str(output),
            "--execute",
            "--mode",
        ]
        commands = [
            invoke(output, name, [*command, name], 45) for name in ("review", "independent")
        ]
        save(output / "audit_receipts/execution_commands.json", commands)
        invoke(output, "closure", [*command, "close"], 15)
        invoke(output, "verification", [*command, "verify"], 15)
        result = read(output / "resource_close.json")
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
