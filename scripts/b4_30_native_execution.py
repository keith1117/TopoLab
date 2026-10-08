"""One bounded native campaign, complete charges and immutable post-exit proof."""

import argparse
import json
import math
import os
import resource
import signal
import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from time import perf_counter

from b4_30_common import (
    REPO,
    canonical,
    contract,
    digest,
    native,
    plan_payload,
    read,
    release,
    save,
)

STAGES = ("reference", "screen", "audit", "policy-audit", "independent")
CAPS = {
    "reference": 3600,
    "screen": 21600,
    "audit": 3600,
    "policy-audit": 3600,
    "independent": 1800,
}


def invoke(output, name, argv, timeout):
    profile = output / "profiles" / (name + ".time")
    log = output / "logs" / (name + ".log")
    started = perf_counter()
    terminated, observed_rss = False, 0
    with log.open("xb") as stream:
        if profile.exists():
            raise FileExistsError(profile)
        child = subprocess.Popen(
            ["/usr/bin/time", "-l", "-o", str(profile), *argv],
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        while child.poll() is None:
            # Keep only our group's summed RSS; discard unrelated process rows.
            snapshot = subprocess.check_output(["ps", "-axo", "pgid=,rss="], text=True)
            rss = sum(
                int(parts[1]) * 1024
                for line in snapshot.splitlines()
                if len(parts := line.split()) == 2 and parts[0] == str(child.pid)
            )
            controller_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            observed_rss = max(observed_rss, rss + controller_rss)
            if perf_counter() - started > timeout or observed_rss > 2147483648:
                terminated = True
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait(timeout=2)
                break
            try:
                child.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                pass
    elapsed = perf_counter() - started
    try:
        measured = native(profile.read_text())
    except (FileNotFoundError, ValueError):
        measured = None
    command = {
        "name": name,
        "argv": argv,
        "exit_code": child.returncode,
        "terminated": terminated,
        "observed_outer_wall_seconds": elapsed,
        "observed_process_group_plus_controller_rss_bytes": observed_rss,
        "native": measured,
        "profile": str(profile.relative_to(output)),
        "profile_sha256": digest(profile) if profile.exists() else None,
        "log": str(log.relative_to(output)),
        "log_sha256": digest(log),
    }
    save(output / "audit_receipts" / (name + "_command.json"), command)
    return command


def command_native(output, command):
    for field in ("profile", "log"):
        name = Path(command[field])
        if (
            name.is_absolute()
            or ".." in name.parts
            or digest(output / name) != command[field + "_sha256"]
        ):
            raise ValueError("immutable contained command/profile/log required")
    value = native((output / command["profile"]).read_text())
    if value != command["native"]:
        raise ValueError("native record differs")
    return value


def stage_charges(output, cohort):
    total, complete, rows = Decimal(0), True, []
    for stage in STAGES:
        path = output / "audit_receipts" / f"{cohort}_{stage}_command.json"
        if not path.exists():
            complete = False
            continue
        command = read(path)
        receipt_path = (
            output
            / cohort
            / ("independent_audit.json" if stage == "independent" else stage + "/progress.json")
        )
        receipt = read(receipt_path) if receipt_path.exists() else None
        measured = command_native(output, command) if command["native"] else None
        wall = max(
            command["observed_outer_wall_seconds"], measured["wall_seconds"] if measured else 0
        )
        attempts = receipt["attempted"] if receipt and stage in ("reference", "screen") else 0
        charge = max(
            Decimal(str(wall)) + attempts + 10,
            Decimal(str(receipt["charged_seconds"] if receipt else 0)),
        )
        peak = max(
            measured["rss_bytes"] if measured else 0,
            command["observed_process_group_plus_controller_rss_bytes"],
            receipt["peak_rss_bytes"] if receipt else 0,
        )
        resource_ok = bool(
            measured
            and command["exit_code"] == 0
            and not command["terminated"]
            and receipt
            and charge <= CAPS[stage]
            and peak <= 2147483648
        )
        if receipt and stage != "independent":
            resource_ok = bool(
                resource_ok
                and not receipt["resource_failed"]
                and not receipt["integrity_failed"]
                and receipt["active_at"] is None
                and receipt["pending"] is None
            )
        complete = bool(complete and resource_ok)
        total += charge
        rows.append(
            {
                "process": cohort + "_" + stage,
                "closed_charge_seconds": float(charge),
                "closed_charge_decimal": str(charge),
                "attempted_queries_or_references": attempts,
                "native": measured,
                "observed_outer_wall_seconds": command["observed_outer_wall_seconds"],
                "complete_resource_evidence": resource_ok,
                "peak_rss_bytes": peak if measured else None,
                "command_sha256": digest(path),
            }
        )
    return float(total), complete, rows


def prepare(output, release_input):
    if (
        output.exists()
        or output.is_relative_to(REPO)
        or output.name != contract()["evidence_root_name"]
    ):
        raise ValueError("one new fixed external root required; never overwrite retained evidence")
    value = read(release_input)
    if value["plan"] != plan_payload():
        raise ValueError("prospective tested release source differs before production")
    for name in ("profiles", "logs", "audit_receipts"):
        (output / name).mkdir(parents=True)
    save(output / "audit_receipts/production_release.json", value)
    release(output)
    save(
        output / "audit_receipts/one_attempt.json",
        {
            "campaigns": 1,
            "source_revision": value["source_revision"],
            "new_fits": 0,
            "final_access": False,
        },
    )
    command = invoke(
        output, "plan", [sys.executable, str(REPO / "scripts/b4_30_z_reflection_repair.py")], 60
    )
    if command["exit_code"] != 0 or command["native"] is None:
        raise ValueError(
            "single native source-only preparation failed; preserve its UNKNOWN fields"
        )
    payload = json.loads((output / command["log"]).read_bytes())
    if payload["contract_sha256"] != value["plan"]["contract_sha256"]:
        raise ValueError("numerical plan contract differs")
    save(output / "audit_receipts/plan.json", payload)


def close(output):
    release(output)
    cohorts = ["sentinel"]
    if (output / "fresh").exists():
        cohorts.append("fresh")
    rows, complete = [], True
    for cohort in cohorts:
        _, ok, added = stage_charges(output, cohort)
        rows.extend(added)
        complete = bool(complete and ok)
    amount = sum((Decimal(r["closed_charge_decimal"]) for r in rows), Decimal(180))
    independent = output / cohorts[-1] / "independent_audit.json"
    audit = read(independent) if independent.exists() else None
    gate = bool(
        complete
        and cohorts == ["sentinel", "fresh"]
        and audit
        and audit["passed"]
        and audit["gate_passed"]
    )
    peak = max((r["peak_rss_bytes"] or 0 for r in rows), default=0)
    value = {
        "version": contract()["version"],
        "closed": True,
        "source_revision": release(output),
        "processes": rows,
        "charged_seconds": float(amount),
        "charged_decimal": str(amount),
        "fully_paid_chain_reserve_seconds": 180,
        "own_stage_resource_acceptance": complete and amount <= 43200 and peak <= 2147483648,
        "whole_resource_acceptance": "PENDING_POSTEXIT",
        "peak_rss_bytes_before_postexit": peak if complete else None,
        "repair_gate_passed_before_postexit": gate,
        "fresh_sealed": cohorts == ["sentinel"],
        "final_access": False,
        "new_fits": 0,
        "old_exact_FEM_route_restarted": False,
        "old_known_added_cost_display_seconds": 58142.252069,
        "old_exact_FEM_cost_cap_seconds": 7200,
        "full_training_memory": "PENDING/4GiB",
    }
    save(output / "resource_close.json", value)
    return value


def campaign(output, release_input):
    prepare(output, release_input)
    commands = []
    parent = output.parent
    for cohort in ("sentinel", "fresh"):
        if cohort == "fresh":
            policy = read(output / "sentinel/policy-audit/summary.json")
            independent = read(output / "sentinel/independent_audit.json")
            spent, valid, _ = stage_charges(output, "sentinel")
            if not (
                policy["passed"]
                and policy["policy_integrity_passed"]
                and independent["passed"]
                and independent["gate_passed"]
                and valid
                and spent + 34200 + 180 <= 43200
            ):
                break
        for stage in STAGES:
            if stage == "independent":
                argv = [
                    sys.executable,
                    str(REPO / "scripts/b4_30_independent_audit.py"),
                    "--output",
                    str(output),
                    "--cohort",
                    cohort,
                ]
                timeout = 1785
            else:
                argv = [
                    sys.executable,
                    str(REPO / "scripts/b4_30_z_reflection_repair.py"),
                    "--execute",
                    "--stage",
                    stage,
                    "--cohort",
                    cohort,
                    "--data-root",
                    str(parent / "b3-v1-data"),
                    "--fit-root",
                    str(parent / "b3-v1-fits"),
                    "--weighted-root",
                    str(parent / "b4-5-weighted-terminal"),
                    "--output",
                    str(output),
                ]
                allowance = (
                    contract()["population"][cohort]["count" if stage == "reference" else "queries"]
                    if stage in ("reference", "screen")
                    else 0
                )
                timeout = CAPS[stage] - allowance - 15
            command = invoke(output, cohort + "_" + stage, argv, timeout)
            commands.append(command)
            print(
                canonical(
                    {
                        "stage": command["name"],
                        "exit": command["exit_code"],
                        "wall": command["observed_outer_wall_seconds"],
                        "native": command["native"],
                    }
                ).decode(),
                end="",
                flush=True,
            )
            if command["exit_code"] != 0 or command["native"] is None or command["terminated"]:
                save(output / "audit_receipts/execution_commands.json", commands)
                return close(output)
    save(output / "audit_receipts/execution_commands.json", commands)
    return close(output)


def bind_postexit(output, campaign_profile, campaign_log, exit_code):
    started = perf_counter()
    release(output)
    # The outer profile includes native preparation, source-only plan and closure,
    # and all child exits. It is preserved independently of the pre-exit receipt.
    measured = native(campaign_profile.read_text())
    save(
        output / "audit_receipts/campaign_native.json",
        {
            "native": measured,
            "exit_code": exit_code,
            "profile": str(campaign_profile),
            "profile_sha256": digest(campaign_profile),
            "log": str(campaign_log),
            "log_sha256": digest(campaign_log),
        },
    )
    closed = read(output / "resource_close.json")
    amount, stage_outer, peak, complete = Decimal(180), 0.0, measured["rss_bytes"], True
    cohorts = ["sentinel", "fresh"] if not closed["fresh_sealed"] else ["sentinel"]
    for cohort in cohorts:
        _, ok, rows = stage_charges(output, cohort)
        complete = bool(complete and ok)
        for row in rows:
            amount += Decimal(row["closed_charge_decimal"])
            stage_outer += row["observed_outer_wall_seconds"]
            peak = max(peak, row["peak_rss_bytes"] or 0)
    plan_command = read(output / "audit_receipts/plan_command.json")
    plan_native = command_native(output, plan_command)
    peak = max(
        peak,
        plan_native["rss_bytes"],
        plan_command["observed_process_group_plus_controller_rss_bytes"],
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )
    # Native rounding is at 0.01s; the full final ten seconds also covers this
    # read-only metadata binder and its exit. The paid reserve is never refunded.
    reserve = max(0.0, measured["wall_seconds"] - stage_outer) + 10
    agreement = amount == Decimal(closed["charged_decimal"]) and math.isclose(
        float(amount), closed["charged_seconds"], rel_tol=1e-14, abs_tol=1e-14
    )
    resource_passed = bool(
        complete
        and agreement
        and exit_code == 0
        and reserve <= 180
        and perf_counter() - started <= 10
        and peak <= 2147483648
        and amount <= 43200
    )
    value = {
        "version": contract()["version"],
        "resource_passed_before_binder_exit": resource_passed,
        "whole_resource_acceptance": "PENDING_BINDER_EXIT",
        "repair_gate_passed_before_binder_exit": bool(
            resource_passed and closed["repair_gate_passed_before_postexit"]
        ),
        "source_revision": release(output),
        "independent_decimal_charge": str(amount),
        "charged_seconds": float(amount),
        "fully_paid_chain_reserve_seconds": 180,
        "observed_chain_reserve_plus_final_exit_floor_seconds": reserve,
        "final_metadata_exit_floor_seconds": 10,
        "whole_peak_rss_bytes": peak,
        "resource_close_sha256": digest(output / "resource_close.json"),
        "campaign_native_sha256": digest(output / "audit_receipts/campaign_native.json"),
        "historical_unknowns_retained": True,
        "fresh_sealed": closed["fresh_sealed"],
        "full_training_memory": "PENDING/4GiB",
        "final_access": False,
    }
    save(output / "audit_receipts/platform_exit_binding.json", value)
    return value


def verify_binder_exit(output, binder_profile, binder_log, exit_code):
    started = perf_counter()
    revision = release(output)
    binding_path = output / "audit_receipts/platform_exit_binding.json"
    binding = read(binding_path)
    measured = native(binder_profile.read_text())
    # Pay the full final ten seconds for the binder and this small metadata
    # verifier, including their exits. A final native verifier profile must also
    # be retained and checked after exit; absence keeps publication incomplete.
    peak = max(
        binding["whole_peak_rss_bytes"],
        measured["rss_bytes"],
        resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )
    passed = bool(
        binding["resource_passed_before_binder_exit"]
        and exit_code == 0
        and measured["wall_seconds"] <= 5
        and perf_counter() - started <= 5
        and peak <= 2147483648
        and binding["source_revision"] == revision
    )
    value = {
        "version": contract()["version"],
        "passed": passed,
        "whole_resource_acceptance": "PASS" if passed else "FAIL",
        "repair_gate_passed": bool(passed and binding["repair_gate_passed_before_binder_exit"]),
        "source_revision": revision,
        "binding_sha256": digest(binding_path),
        "binder_native": measured,
        "binder_exit_code": exit_code,
        "binder_profile": str(binder_profile),
        "binder_profile_sha256": digest(binder_profile),
        "binder_log": str(binder_log),
        "binder_log_sha256": digest(binder_log),
        "whole_peak_rss_bytes": peak,
        "fully_paid_chain_reserve_seconds": 180,
        "final_metadata_exit_floor_seconds": 10,
        "final_verifier_native_exit_required_before_publication": True,
        "historical_unknowns_retained": True,
        "final_access": False,
    }
    save(output / "audit_receipts/platform_exit_profile_verification.json", value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--mode", choices=("campaign", "bind", "verify"), default="campaign")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--release-input", type=Path)
    parser.add_argument("--campaign-profile", type=Path)
    parser.add_argument("--campaign-log", type=Path)
    parser.add_argument("--exit-code", type=int)
    args = parser.parse_args()
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return
    if args.output is None:
        parser.error("execution requires a fixed external output")
    output = args.output.resolve()
    if args.mode == "campaign":
        if args.release_input is None:
            parser.error("campaign requires exact-head/main CI release evidence")
        result = campaign(output, args.release_input)
    else:
        if any(x is None for x in (args.campaign_profile, args.campaign_log, args.exit_code)):
            parser.error("postexit proof requires immutable outer native profile/log/exit")
        binder = bind_postexit if args.mode == "bind" else verify_binder_exit
        result = binder(output, args.campaign_profile, args.campaign_log, args.exit_code)
    print(canonical(result).decode(), end="", flush=True)


if __name__ == "__main__":
    main()
