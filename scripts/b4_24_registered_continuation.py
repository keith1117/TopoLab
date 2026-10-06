"""Owner-approved B4.24 continuation; retain historical failures and unknown RSS."""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from time import perf_counter

import b4_24_saved_schema_recovery as recovery

original = recovery.original
VERSION = "topolab.b4_24.registered-continuation.v3"
AUTHORIZATION_SHA256 = "73646d6b914c260440760e155b3fafd5ed2caa35a074f3dd4c8a348a6c61bcf1"
HISTORY_BINDINGS = {
    "audit_receipts/evidence_final_head_ci.json": (
        "ebc91d6d3dbe01a0de9c24477a1e01a4aa395cad7800259c2c146198f903c9eb"
    ),
    "audit_receipts/evidence_main_ci.json": (
        "2b4d4e13e81e184f2b7c98239cfc9f11385056c50e202f03d868a2a0c8be4ff0"
    ),
    "audit_receipts/execution_commands.json": (
        "ec6839c73ead10ebe9960345c4d15ff04ee606363c1522dca5970960fe379a1a"
    ),
    "audit_receipts/failure-closure_command.json": (
        "9ae791dcd8898ed8505660e3ee1d4f40b082f5ec4dcad88eac6189e79b60a85d"
    ),
    "audit_receipts/failure-verification_command.json": (
        "99e797aecd4157f08d6c585f7d35b662e89929898ff2899ae938628b8547916d"
    ),
    "audit_receipts/interrupted_evidence_release.json": (
        "2bae114133b1b3e5966d9223a0b063957135fd85e02044bf8b3c95c07080fe19"
    ),
    "audit_receipts/interruption_profile_verification.json": (
        "841de07fbef03da4c6dc534a7e6f3b692fe2b025f7d17d30017dda87416afdac"
    ),
    "audit_receipts/interruption_reservation_verification.json": (
        "d5a1e8c3d0465a8bcd1f17c0d50ffcf89cbcc7ca88da341e4c7448c371f56b79"
    ),
    "audit_receipts/plan.json": (
        "7d13888f44bf78598c5b80a82b132e0ca3adcc3ed357667434d370d6a44b0663"
    ),
    "audit_receipts/plan_command.json": (
        "16b6d7bb64bcc5be73b5a8d9904a3fb887bd064810e5db7f0b9ae6950f8db59d"
    ),
    "audit_receipts/production_release.json": (
        "f697fb45c3b3fa5e9677e82b695f4adfd8d82e383166daf6d4e47164f77cc621"
    ),
    "audit_receipts/recovery-plan_command.json": (
        "819b8affccdaedb4a60c4ff18dfa2d41eab1fd01df105d66d54da3fa4c3261be"
    ),
    "audit_receipts/recovery_release.json": (
        "8a7ca83ba33cce347de1b29c434aaf86a429c581583aad2e7f753620a54212f5"
    ),
    "audit_receipts/recovery_source_final_head_ci.json": (
        "e7ddd386e35c0240808fd795fda01e9d0d6ee8a2dea7e9d1e2ed30875e27a1dc"
    ),
    "audit_receipts/recovery_source_main_ci.json": (
        "635b062fe5b99718c764e900aa5145d0d3d6e9b3940d3f2b8e9a09be4f4d35f0"
    ),
    "audit_receipts/review_command.json": (
        "4298af75a956c804d32b58d5778f785af6ccc4ed99e4f2ff6e3f406b2d8619e1"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "a818af8a2ae2cbeb91b233b39b1959a967124ef387f238ff9e4421e8df093f56"
    ),
    "audit_receipts/source_main_ci.json": (
        "1f8df214a04119b68013bfc130f367d250a8a205309f89c1c53ba2324691507a"
    ),
    "audit_sources/b4_24_interruption_accounting.py": (
        "140eb76b808e05db97ccde8b8efbdcf53546058b3afc5c31883223a41f8818c2"
    ),
    "audit_sources/b4_24_interruption_native.py": (
        "ad1b875d3460202d45fddeb2fdd9920163f67b05027455271438e3623f7295a5"
    ),
    "audit_sources/b4_24_recovery_workflow.py": (
        "0ab4268fa09cf50c81d6e2a98eec0d3478c5b12418876595cf2a5525f43481e3"
    ),
    "audit_sources/b4_24_workflow.py": (
        "0788b998e628e13c8232890f4265d0a6a1dc6e3396c45364d0fe331f9f1a1a5c"
    ),
    "logs/failure-closure.log": (
        "fa688f9e79b2fbf47cc5f9c4f32aa9e8d3dbb9fd0baf64a6fade9737b300e009"
    ),
    "logs/failure-verification.log": (
        "60d151e8bb660ba3a8aa21e0bdadbdab4f6b47eff4027b7169c5f64567a74645"
    ),
    "logs/plan.log": (
        "7d13888f44bf78598c5b80a82b132e0ca3adcc3ed357667434d370d6a44b0663"
    ),
    "logs/recovery-plan.log": (
        "c41968eacbd47c74e0984e061cf44721478272e7d7f809a02fe718c41708ec95"
    ),
    "logs/review.log": (
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    ),
    "profiles/failure-closure.time": (
        "d723104c6176d0ceca4d3f92b30d27e7e541c3e44f3a807ca20ebf9b76150c31"
    ),
    "profiles/failure-verification.time": (
        "af9e94a7e3a6772dcfe0e9ca98c4616e8f5f391b8160d69139ac6bb4da94d006"
    ),
    "profiles/plan.time": (
        "f5487887d660f1b1704212f0a9411591bdfcd8a842e5b1906c0734bc9af7f43b"
    ),
    "profiles/recovery-plan.time": (
        "bddb11a795d1a8bbfb57c475bf02c27dd2179f30b9d59f0d0244abe7ed8c3f38"
    ),
    "profiles/review.time": (
        "222f3425546ff0d40556bf9f511f2777f23281bdd4b2b2f3de02476e53d505c0"
    ),
    "resource_close_incomplete.json": (
        "fa688f9e79b2fbf47cc5f9c4f32aa9e8d3dbb9fd0baf64a6fade9737b300e009"
    ),
}


def plan_payload():
    value = {
        **recovery.plan_payload(),
        "version": VERSION,
        "recovery_plan_sha256": recovery.plan_payload()["plan_sha256"],
        "history_bindings": HISTORY_BINDINGS,
        "authorization_sha256": AUTHORIZATION_SHA256,
        "historical_time_charge_seconds": 76.19,
        "historical_reserved_use_seconds": 50.53,
        "historical_whole_peak_rss_bytes": None,
        "additional_paid_reservation_seconds": 60,
        "total_paid_reservation_seconds": 120,
        "maximum_new_review_charge_seconds": 43.81,
        "maximum_independent_charge_seconds": 60,
        "maximum_remaining_review_attempts": 1,
        "historical_memory_compliance_established": False,
        "continuation_memory_cap_bytes": 1073741824,
        "scalar_conditions": 2104,
        "independent_scalar_conditions": 1728,
        "historical_failed_native_processes": 2,
    }
    value.pop("plan_sha256")
    return {**value, "plan_sha256": original.sha(original.canonical(value))}


def validate_history(partial, reserve, commands):
    if (
        partial["closed"]
        or partial["resource_proof_complete"]
        or partial["peak_rss_bytes"] is not None
        or partial["planning_child_exit_code"] is not None
        or partial["native_profiles"]["recovery-plan"]["rss_bytes"] is not None
        or partial["time_charge_seconds"] != 76.19
        or partial["paid_reservation_seconds"] != 60
        or partial["failed_review_charge_seconds"] != 16.19
        or partial["failed_native_processes"] != 2
        or partial["registered_recovery_review_attempts"] != 0
        or partial["arithmetic_audit_attempts"] != 0
        or not reserve["passed"]
        or reserve["resource_proof_complete"]
        or reserve["combined_reserved_use_seconds"] != 50.53
        or [c["name"] for c in commands] != ["plan", "review", "recovery-plan"]
        or [c["exit_code"] for c in commands] != [0, 1, 1]
    ):
        raise ValueError("requires unchanged historical failures, charges and unknown memory")


def check_history(prior):
    for path, digest in HISTORY_BINDINGS.items():
        original.safe_hash(prior, path, digest)
    # These two exact SHA-bound metadata receipts used standard JSON whitespace.
    # Preserve their bytes; numerical panels/releases retain the frozen reader.
    partial = history_metadata(prior, "resource_close_incomplete.json")
    reserve = history_metadata(prior, "audit_receipts/interruption_reservation_verification.json")
    commands = original.read(prior, "audit_receipts/execution_commands.json")
    validate_history(partial, reserve, commands)
    for filename in ("production_release", "recovery_release"):
        release = original.read(prior, "audit_receipts/" + filename + ".json")
        for path, digest in release["source_sha256"].items():
            original.safe_hash(Path(__file__).resolve().parents[1], path, digest)
    return partial


def history_metadata(prior, name):
    original.safe_hash(prior, name, HISTORY_BINDINGS[name])
    return json.loads((prior / name).read_bytes())


def review(panel, prior_audit, closed):
    result = recovery.review(panel, prior_audit, closed)
    result.update(plan=plan_payload(), registered_continuation=True)
    return result


def audit(panel, prior_audit, closed, report):
    if report["plan"] != plan_payload() or not report["registered_continuation"]:
        raise ValueError("independent registered continuation boundary differs")
    # Frozen independent adapter/mathematics; candidate functions are not called.
    result = recovery.audit(panel, prior_audit, closed, {**report, "plan": recovery.plan_payload()})
    result.update(
        review_sha256=original.sha(original.canonical(report)),
        plan_sha256=plan_payload()["plan_sha256"],
        registered_continuation=True,
        historical_whole_peak_rss_bytes=None,
    )
    return result


def native_profile(path):
    text = path.read_text()
    cpu = re.search(r"([\d.]+)\s+real\s+([\d.]+)\s+user\s+([\d.]+)\s+sys", text)
    memory = re.search(r"(\d+)\s+maximum resident set size", text)
    if cpu is None or memory is None:
        raise ValueError("complete native wall/user/system/RSS required")
    return {
        "wall_seconds": float(cpu[1]),
        "user_seconds": float(cpu[2]),
        "system_seconds": float(cpu[3]),
        "rss_bytes": int(memory[1]),
    }


def close_resources(output, commands, report, audit_result):
    names = [c["name"] for c in commands]
    if not names or names != ["plan", "review", "independent"][: len(names)]:
        raise ValueError("requires one ordered continuation attempt without retries")
    profiles, charges = {}, {}
    for command in commands:
        name = command["name"]
        if (
            command["profile"] != "profiles/" + name + ".time"
            or command["log"] != "logs/" + name + ".log"
        ):
            raise ValueError("requires contained distinct native records")
        original.safe_hash(output, command["profile"], command["profile_sha256"])
        original.safe_hash(output, command["log"], command["log_sha256"])
        native = native_profile(output / command["profile"])
        profiles[name] = native
        receipt = report if name == "review" else audit_result if name == "independent" else None
        if name != "plan":
            if command["exit_code"] == 0 and receipt is None:
                raise ValueError("successful continuation result missing")
            charges[name] = max(
                native["wall_seconds"] + 10, receipt["charged_seconds"] if receipt else 0
            )
    cumulative_review = 16.19 + charges.get("review", 0)
    total = 16.19 + 120 + sum(charges.values())
    if (
        cumulative_review > 60
        or charges.get("independent", 0) > 60
        or total > 240
        or max(p["rss_bytes"] for p in profiles.values()) > 1073741824
        or profiles["plan"]["wall_seconds"] + 10 > 60
    ):
        raise ValueError("registered cumulative resource caps exceeded")
    complete = names == ["plan", "review", "independent"] and all(
        c["exit_code"] == 0 for c in commands
    )
    if complete and (
        report["plan"] != plan_payload()
        or not audit_result["passed"]
        or audit_result["review_sha256"] != original.sha(original.canonical(report))
        or any(
            v[k] != expected
            for v in (report, audit_result)
            for k, expected in original.boundary_fields().items()
        )
    ):
        raise ValueError("complete independent continuation binding differs")
    return {
        "closed": True,
        "closure_scope": "owner-approved v3 continuation and reconciled historical time",
        "plan_sha256": plan_payload()["plan_sha256"],
        "charged_seconds": total,
        "paid_reservation_seconds": 120,
        "historical_time_charge_seconds": 76.19,
        "historical_reserved_use_seconds": 50.53,
        "historical_resource_proof_complete": False,
        "whole_slice_peak_rss_bytes": None,
        "whole_slice_memory_compliance": None,
        "continuation_native_profiles_before_closure": profiles,
        "continuation_peak_rss_before_closure": max(p["rss_bytes"] for p in profiles.values()),
        "continuation_stage_charges": charges,
        "cumulative_review_charge_seconds": cumulative_review,
        "historical_failed_native_processes": 2,
        "continuation_failed_processes": sum(c["exit_code"] != 0 for c in commands),
        "full_panel_review_complete": complete,
        "review_acceptance_passed": bool(complete and report["review_acceptance_passed"]),
        "original_fit_proxy_unchanged": report["original_fit_proxy_unchanged"]
        if complete
        else None,
        "next_slice": report["next_slice"] if complete else original.EVIDENCE_NEXT,
        "review_sha256": original.sha(original.canonical(report)) if report else None,
        "independent_audit_sha256": original.sha(original.canonical(audit_result))
        if audit_result
        else None,
        **original.boundary_fields(),
    }


def verify_resources(output, closed):
    if not closed["closed"] or closed["whole_slice_peak_rss_bytes"] is not None:
        raise ValueError("requires scoped closure with historical memory still unknown")
    profiles = {}
    for name in (*closed["continuation_native_profiles_before_closure"], "closure"):
        command = original.read(output, "audit_receipts/" + name + "_command.json")
        original.safe_hash(output, command["profile"], command["profile_sha256"])
        original.safe_hash(output, command["log"], command["log_sha256"])
        profiles[name] = native_profile(output / command["profile"])
    reserved = (
        profiles["plan"]["wall_seconds"]
        + 10
        + max(profiles["closure"]["wall_seconds"] + 10, closed["closure_internal_charge_seconds"])
    )
    if reserved > 50 or max(p["rss_bytes"] for p in profiles.values()) > 1073741824:
        raise ValueError("insufficient registered reserve for final verification or RSS exceeded")
    return {
        "passed": True,
        "metadata_only": True,
        "new_numerical_calls": 0,
        "native_profiles": profiles,
        "reserved_use_before_verification": reserved,
        "resource_close_sha256": original.sha((output / "resource_close.json").read_bytes()),
        "historical_resource_proof_complete": False,
        "whole_slice_peak_rss_bytes": None,
    }


def publish(output, name, value, revision, started, cap):
    value.update(
        source_revision=revision,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=original.peak_rss(),
    )
    if value["charged_seconds"] > cap or value["peak_rss_bytes"] > 1073741824:
        raise RuntimeError("registered native stage cap exceeded")
    with (output / name).open("xb") as stream:
        stream.write(original.canonical(value))
    print(
        original.canonical({"output": name, "charged_seconds": value["charged_seconds"]}).decode(),
        end="",
    )


def main(argv=None):
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=("plan", "review", "audit", "close", "verify"), required=True
    )
    parser.add_argument("--probe-root", type=Path, required=True)
    parser.add_argument("--prior-review-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    root, prior, output = (
        p.resolve() for p in (args.probe_root, args.prior_review_root, args.output_root)
    )
    original.roots(root, output)
    original.roots(prior, output)
    if not args.execute:
        print(original.canonical(plan_payload()).decode(), end="")
        return 0
    if (
        args.mode == "plan"
        or (root.name, prior.name, output.name)
        != (
            "b4-23-versioned-surrogate-feasibility",
            "b4-24-versioned-correctness-failure-review",
            "b4-24-registered-continuation-v3",
        )
        or not root.parent == prior.parent == output.parent
    ):
        raise ValueError("requires fixed registered sibling roots and nonexecuting plan")
    name = {
        "review": "review.json",
        "audit": "independent_audit.json",
        "close": "resource_close.json",
        "verify": "resource_verification.json",
    }[args.mode]
    if (output / name).exists():
        raise ValueError("refuses to overwrite registered continuation output")
    if os.environ.get("NUMEXPR_NUM_THREADS") != "1":
        raise ValueError("requires all five one-thread settings")
    revision = original.execution_release(output)
    repo = Path(__file__).resolve().parents[1]
    if (
        subprocess.check_output(["git", "branch", "--show-current"], cwd=repo, text=True).strip()
        != "main"
    ):
        raise ValueError("requires merged main source")
    original.safe_hash(output, "audit_receipts/authorization.json", AUTHORIZATION_SHA256)
    check_history(prior)
    if args.mode in ("review", "audit"):
        bound = original.check_inputs(root)
        panel = original.read(root, "probe.json")
        from b4_23_independent_audit import journal_check

        journal_check(root, panel)
        if args.mode == "review":
            result = review(panel, bound["independent_audit.json"], bound["resource_close.json"])
        else:
            report = original.read(output, "review.json")
            if report["source_revision"] != revision:
                raise ValueError("review source differs")
            result = audit(
                panel, bound["independent_audit.json"], bound["resource_close.json"], report
            )
        original.check_inputs(root)
        check_history(prior)
        publish(output, name, result, revision, started, 43.81 if args.mode == "review" else 60)
    elif args.mode == "close":
        commands = original.read(output, "audit_receipts/execution_commands.json")
        results = [
            original.read(output, p) if (output / p).exists() else None
            for p in ("review.json", "independent_audit.json")
        ]
        result = close_resources(output, commands, *results)
        result.update(
            source_revision=revision,
            closure_internal_charge_seconds=perf_counter() - started + 10,
            closure_internal_peak_rss_bytes=original.peak_rss(),
            execution_commands_sha256=original.sha(original.canonical(commands)),
        )
        if (
            result["closure_internal_charge_seconds"] > 60
            or result["closure_internal_peak_rss_bytes"] > 1073741824
        ):
            raise RuntimeError("registered closure cap exceeded")
        with (output / name).open("xb") as stream:
            stream.write(original.canonical(result))
        print(original.canonical(result).decode(), end="")
    else:
        result = verify_resources(output, original.read(output, "resource_close.json"))
        publish(output, name, result, revision, started, 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
