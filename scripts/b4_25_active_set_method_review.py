"""Bounded review of certified scalar evidence; no numerical kernel is invoked."""

import argparse
import copy
import hashlib
import json
import math
import os
import re
import resource
import subprocess
import sys
from pathlib import Path
from time import perf_counter

VERSION = "topolab.b4_25.active-set-method-review.v1"
METHOD_NEXT = "B4.26 bounded active-set-aware correctness and cost preregistration"
EVIDENCE_NEXT = "B4.26 bounded active-set method evidence review"
CASE_IDS = (
    "tlcase-v1-0079bd9f0d927e20866f2c73be19e1f57471576f7cd0494b6898a46f7fab9858",
    "tlcase-v1-01504c9e63d2dfa11017438a813a3dfd23f27f9f9997bb59edfc3a24a3d21f50",
    "tlcase-v1-03a2c40639cc65aedf22d7ddc65359616807735e87c680949b09638d4eaa1e8f",
    "tlcase-v1-04ab9b94039197973b9e3ca5b1a855528197f30cce70635b1c1014002673461c",
    "tlcase-v1-0ca7ef4d765a4e8403221471f98c061684e99dde777b047a1a3f5f0642fc47b6",
    "tlcase-v1-144d548fd53ff9798a62251e0d02258eda28d17fdf6fb87ff5979b3f0b904900",
    "tlcase-v1-0294749064eb3e7aacc57d5f4a3ce11b01133fb2e10d01fa44722dfdb3860f26",
    "tlcase-v1-0ea4104dcf6c16b35ef4c239eb34a1341a4e554813a1ad8c15cc1eade6d54768",
)
BINDINGS = {
    "review.json": ("46f6819585660a49575ce4d01fcaf6cb014ce9a5eb617e4f91662d9c9a60f61d"),
    "independent_audit.json": ("bc5931d7b85a18577d8239b9c119ea46c40ac7315f6604ec30fc2dc9ddb7bfae"),
    "resource_close.json": ("be01008c74277fbdaaee125565476a442714507d4ea1ebe62c03871507cf6209"),
    "resource_verification.json": (
        "4e7142194372d82f7fc8be27303f150107144a55f2c590866a36acfa6bcf88f6"
    ),
    "audit_receipts/plan.json": (
        "a3dc438013ef3251225e1568d7c8c2c4a13e85999b4ae1de5df74e4d1317c667"
    ),
    "audit_receipts/production_release.json": (
        "16a9b25e66a637c8975ab326c12d52168e3a6ec312c2921c5d0f74d2a791d873"
    ),
    "audit_receipts/source_final_head_ci.json": (
        "7383f64d783e6f24d0595a8be54d7b977f6f18281f00e2df1ab2ae0653b59c00"
    ),
    "audit_receipts/source_main_ci.json": (
        "2456d18db5913abfbad44d5445db42bcdea286e036cd109644f02533e9426fd9"
    ),
    "audit_receipts/postexit_reservation.json": (
        "1a07b7bc2a3dc48126caa8061cc65061c2e4c7dfdf2b646606a25bc9473b237f"
    ),
    "audit_receipts/execution_commands.json": (
        "da5a2030849236c221118596d6a70a97dbea8d38c2587912128714400531f502"
    ),
    "audit_receipts/evidence_release.json": (
        "0e72c20722719bd8a336f277e5689e241a6947439ed4ae9225f1526c3220d297"
    ),
    "audit_receipts/evidence_final_head_ci.json": (
        "a6655e80bc9e0204e5fb4e26939bb0cdcc665d9c7af899b1d7ec46d76bbe4287"
    ),
    "audit_receipts/evidence_main_ci.json": (
        "08bc192d1c86d2c5ae35cc49a981b3f0b3bb19f7cc57a8204f402eff5cfdeaea"
    ),
    "audit_receipts/closure_command.json": (
        "242630457b6b4961da49576d50b2d82f7bba5fd80fc9840d42b9b43a93b7c36b"
    ),
    "audit_receipts/verification_command.json": (
        "535e742d889ef6f441057524031c416214d5c1485f984f5f8a70912c12265ecc"
    ),
}
METHODS = {
    "existing_v3_original_criteria": "stopped_B4_23_integrity_and_cost_failure_no_fit",
    "active_set_aware_evidence": "separate_correctness_cost_preregistration_only",
    "smooth_bounded_volume_projection": "deferred_new_map_needs_separate_contract",
    "detached_offset_or_straight_through": "incompatible_with_frozen_constrained_derivative",
    "exact_current_prediction_fem": "stopped_cost_failure_no_cache_ordering_search",
    "startup_or_schedule_search": "no_retiming_first_removal_or_population_frequency_search",
}
THREADS = (
    "OPENBLAS_NUM_THREADS",
    "OMP_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
PRIOR_CHARGES = (84.33, 55.99, 112.34, 86.13, 73.93, 100.30, 90.27, 104.62, 143.47)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def safe_hash(root, name, expected):
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or Path(name).is_absolute():
        raise ValueError("requires contained relative evidence path")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1048576), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError("frozen evidence hash differs: " + name)


def read(root, name, expected=None):
    if expected is not None:
        safe_hash(root, name, expected)
    path = (root / name).resolve()
    if not path.is_relative_to(root.resolve()) or Path(name).is_absolute():
        raise ValueError("requires contained relative evidence path")
    raw = path.read_bytes()
    value = json.loads(raw)
    if canonical(value) != raw:
        raise ValueError("requires canonical finite JSON")
    return value


def boundary_fields():
    return {
        "original_correctness_gate_passed": False,
        "original_feasibility_gate_passed": False,
        "original_conditions": 3976,
        "original_failed_conditions": 69,
        "prior_b4_15_23_charge_seconds": 851.38,
        "prior_b4_24_charge_seconds": 200.98,
        "historical_resource_proof_complete": False,
        "historical_whole_slice_peak_rss_bytes": None,
        "historical_whole_slice_memory_compliance": None,
        "prior_b4_19_actual_counts_and_gap_still_unknown": True,
        "full_fit_memory_feasibility_pending": True,
        "global_cause_or_gradient_failure_established": False,
        "solver_calls": 0,
        "new_projection_calls": 0,
        "new_objective_gradient_calls": 0,
        "new_timing_measurements": 0,
        "label_model_byte_reads": 0,
        "raw_prior_panel_reads": 0,
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
        "next_slice_started": False,
    }


def plan_payload():
    value = {
        "version": VERSION,
        "bindings": BINDINGS,
        "cases": 8,
        "case_ids": list(CASE_IDS),
        "case_order": "mesh_direction_then_canonical_case_id",
        "inherited_central_states": 72,
        "inherited_side_states": 128,
        "directional_rows": 64,
        "inherited_measurements": 216,
        "original_mask_failures": 35,
        "original_fd_failures": 34,
        "original_fd_tolerance": 1e-4,
        "original_fd_floor": 1e-8,
        "arithmetic_tolerance": 1e-12,
        "methods": METHODS,
        "scenarios": ["original_maximum", "zero_small_recorded_large_max", "zero_prediction"],
        "fit_population": [432, 76],
        "fit_seeds": 3,
        "fit_epochs": 200,
        "cost_factor": 1.25,
        "baseline_fit_seconds": 3870.204341,
        "prior_charged_seconds": list(PRIOR_CHARGES),
        "process_seconds": 60,
        "reserve_seconds": 60,
        "max_seconds": 180,
        "max_rss_bytes": 1073741824,
        "decision_order": [METHOD_NEXT, EVIDENCE_NEXT],
        **boundary_fields(),
    }
    return {**value, "plan_sha256": sha(canonical(value))}


def ci_passed(value, main):
    checks = value["checks"]
    return (
        value["passed"]
        and bool(checks)
        and all(c["head_sha"] == value["head"] and c["status"] == "completed" for c in checks)
        and all(
            c["conclusion"] == "success"
            or (not main and c["name"] == "clean-linux-smoke" and c["conclusion"] == "skipped")
            for c in checks
        )
        and all(
            any(c["name"] == name and c["conclusion"] == "success" for c in checks)
            for name in ("quality", "frontend", "clean-linux-smoke")
        )
    )


def native_profile(path):
    content = path.read_text()
    cpu = re.search(r"([\d.]+)\s+real\s+([\d.]+)\s+user\s+([\d.]+)\s+sys", content)
    memory = re.search(r"(\d+)\s+maximum resident set size", content)
    if cpu is None or memory is None:
        raise ValueError("complete native wall/user/system/RSS required")
    value = dict(
        zip(
            ("wall_seconds", "user_seconds", "system_seconds"),
            map(float, cpu.groups()),
            strict=True,
        )
    )
    value["rss_bytes"] = int(memory[1])
    if any(not math.isfinite(v) or v < 0 for v in value.values()) or value["rss_bytes"] <= 0:
        raise ValueError("invalid native resources")
    return value


def check_command(root, command):
    name = command["name"]
    for directory, suffix in (("profiles", ".time"), ("logs", ".log")):
        field = "profile" if directory == "profiles" else "log"
        if command[field] != directory + "/" + name + suffix:
            raise ValueError("requires distinct contained native records")
        safe_hash(root, command[field], command[field + "_sha256"])
    return native_profile(root / command["profile"])


def check_inputs(root):
    bound = {name: read(root, name, digest) for name, digest in BINDINGS.items()}
    report, audit, closed, proof = (
        bound[name]
        for name in (
            "review.json",
            "independent_audit.json",
            "resource_close.json",
            "audit_receipts/postexit_reservation.json",
        )
    )
    if (
        report["plan"] != bound["audit_receipts/plan.json"]
        or report["plan"]["version"] != "topolab.b4_24.registered-continuation.v3"
        or not report["review_acceptance_passed"]
        or report["scalar_conditions"] != 2104
        or report["failed_scalar_conditions"] != 0
        or not audit["passed"]
        or audit["independent_scalar_conditions"] != 1728
        or audit["review_sha256"] != BINDINGS["review.json"]
        or not closed["closed"]
        or not closed["review_acceptance_passed"]
        or not math.isclose(closed["charged_seconds"], 200.98, rel_tol=1e-12, abs_tol=1e-12)
        or closed["historical_resource_proof_complete"]
        or closed["whole_slice_peak_rss_bytes"] is not None
        or closed["whole_slice_memory_compliance"] is not None
        or closed["historical_time_charge_seconds"] != 76.19
        or closed["historical_reserved_use_seconds"] != 50.53
        or closed["historical_failed_native_processes"] != 2
        or closed["continuation_failed_processes"] != 0
        or not proof["passed"]
        or proof["historical_resource_proof_complete"]
        or proof["whole_slice_peak_rss_bytes"] is not None
        or proof["new_reserved_use_seconds"] > 60
        or proof["continuation_peak_rss_bytes"] != 415268864
        or closed["next_slice"] != "B4.25 bounded active-set objective-method review"
        or any(
            report[k] != v
            for k, v in {
                "original_correctness_gate_passed": False,
                "original_feasibility_gate_passed": False,
                "retained_measurements": 216,
                "fits": 0,
                "final_access": False,
                "repaired_gate": False,
                "old_fresh_sealed": True,
            }.items()
        )
    ):
        raise ValueError("requires accepted scoped B4.24 with historical unknowns preserved")
    for stage in ("source", "evidence"):
        if not all(
            ci_passed(bound[f"audit_receipts/{stage}_{name}_ci.json"], name == "main")
            for name in ("final_head", "main")
        ):
            raise ValueError("prior exact-head/main CI differs")
    release = bound["audit_receipts/production_release.json"]
    evidence = bound["audit_receipts/evidence_release.json"]
    if (
        not all(
            r["all_applicable_ci_passed_before_merge"] and r["same_tree_as_tested_head"]
            for r in (release, evidence)
        )
        or not evidence["publication_complete"]
    ):
        raise ValueError("prior source/evidence publication differs")
    repository = Path(__file__).resolve().parents[1]
    for name, digest in release["source_sha256"].items():
        safe_hash(repository, name, digest)
    commands = bound["audit_receipts/execution_commands.json"] + [
        bound["audit_receipts/" + name + "_command.json"] for name in ("closure", "verification")
    ]
    if [c["name"] for c in commands] != [
        "plan",
        "review",
        "independent",
        "closure",
        "verification",
    ]:
        raise ValueError("prior ordered native records differ")
    for command in commands:
        if command["exit_code"] or check_command(root, command)["rss_bytes"] > 1073741824:
            raise ValueError("prior continuation native proof differs")
    return bound


def row_identities(case_ids):
    rows, position = [], 0
    for case_id in case_ids:
        position += 9
        for state in range(9):
            position += 24
            if state in (0, 4):
                for direction in ("sine", "cosine"):
                    for step in (1e-4, 2e-4):
                        rows.append(
                            {
                                "case_id": case_id,
                                "state": state,
                                "direction": direction,
                                "step": step,
                                "mask_condition": position + 32,
                                "fd_condition": position + 33,
                            }
                        )
                        position += 34
    return rows


def cost_review(proxy):
    units, setup = (
        proxy[k] for k in ("maximum_seconds_per_scale", "maximum_setup_seconds_per_scale")
    )
    if (
        set(units) != {"small", "large"}
        or set(setup) != set(units)
        or any(not math.isfinite(v) or v <= 0 for values in (units, setup) for v in values.values())
    ):
        raise ValueError("complete positive first-inclusive scale maxima required")
    preparation = 3 * 1.25 * (432 * setup["small"] + 76 * setup["large"])
    prediction = 3 * 200 * 1.25 * (432 * units["small"] + 76 * units["large"])
    fixed = preparation + 3870.204341 + math.fsum(PRIOR_CHARGES)
    total = fixed + prediction
    if (
        not math.isclose(
            proxy["additional_surrogate_seconds"], prediction, rel_tol=1e-12, abs_tol=1e-12
        )
        or not math.isclose(
            proxy["full_population_preparation_seconds"], preparation, rel_tol=1e-12, abs_tol=1e-12
        )
        or not math.isclose(proxy["total_prospective_seconds"], total, rel_tol=1e-12, abs_tol=1e-12)
        or proxy["limit_seconds"] != 7200
        or proxy["cost_feasible"]
        or not proxy["planning_proxy_only"]
        or not proxy["full_fit_memory_feasibility_pending"]
    ):
        raise ValueError("original complete failed cost proxy differs")
    remaining = 7200 - fixed - 200.98
    return {
        "original_maximum_seconds": total,
        "zero_small_recorded_large_max_seconds": fixed + 750 * 76 * units["large"],
        "zero_prediction_seconds": fixed,
        "original_plus_b4_24_seconds": total + 200.98,
        "conditional_prediction_budget_before_b4_25_seconds": remaining,
        "common_prediction_reduction_required_before_b4_25": prediction / remaining
        if remaining > 0
        else None,
        "population_weighted_unit_budget_before_b4_25_seconds": remaining / (750 * 508),
        "retained_array_bytes_estimate": proxy["population_retained_array_bytes_estimate"],
        "signed_retained_array_headroom_to_4gib": 4294967296
        - proxy["population_retained_array_bytes_estimate"],
        "diagnostic_only": True,
        "original_cost_gate_passed": False,
        "full_fit_memory_feasibility_pending": True,
    }


def review(prior):
    rows = prior["rows"]
    case_ids = list(dict.fromkeys(r["case_id"] for r in rows))
    if len(case_ids) != 8 or tuple(case_ids) != CASE_IDS or len(rows) != 64:
        raise ValueError("complete canonical eight-case/64-row population required")
    checks, failures, groups = [], [], {}
    for row, identity in zip(rows, row_identities(case_ids), strict=True):
        if any(row[k] != v for k, v in identity.items()):
            raise ValueError("original ordered row/condition identity differs")
        numbers = (
            "fd",
            "derivative",
            "error",
            "signed_discrepancy",
            "clipping_departure_contribution",
            "volume_residual_contribution",
            "saved_value_roundoff_contribution",
            "saved_gradient_roundoff_contribution",
            "decomposition_residual",
            "arithmetic_envelope",
            "exact_fd",
            "exact_derivative",
        )
        if any(not math.isfinite(row[k]) for k in numbers) or row["arithmetic_envelope"] < 0:
            raise ValueError("finite complete saved scalars required")
        changed = [row[k] for k in ("changed_plus_components", "changed_minus_components")]
        if any(type(n) is not int or n < 0 for n in changed):
            raise ValueError("original changed-component counts required")
        mask = any(changed)
        discrepancy = row["fd"] - row["derivative"]
        error = abs(discrepancy) / max(abs(row["fd"]), abs(row["derivative"]), 1e-8)
        fd_failed = error > 1e-4
        residual = discrepancy - math.fsum(row[k] for k in numbers[4:8])
        compatible = (
            abs(discrepancy - row["clipping_departure_contribution"]) <= row["arithmetic_envelope"]
        )
        checks.extend(
            [
                type(row["mask_failed"]) is bool and row["mask_failed"] == mask,
                type(row["fd_failed"]) is bool and row["fd_failed"] == fd_failed,
                math.isclose(row["error"], error, rel_tol=1e-12, abs_tol=1e-12),
                math.isclose(row["signed_discrepancy"], discrepancy, rel_tol=1e-12, abs_tol=1e-12),
                math.isclose(row["decomposition_residual"], residual, rel_tol=1e-12, abs_tol=1e-12),
                abs(residual) <= row["arithmetic_envelope"],
                row["clipping_accounts_for_gap_within_arithmetic_envelope"] == compatible,
            ]
        )
        for kind, failed in (("mask", mask), ("fd", fd_failed)):
            if failed:
                failures.append(row[kind + "_condition"])
        key = str(row["state"]) + "/" + str(row["step"])
        group = groups.setdefault(
            key, {"rows": 0, "mask_failures": 0, "fd_failures": 0, "overlap": 0}
        )
        for name, value in (
            ("rows", 1),
            ("mask_failures", mask),
            ("fd_failures", fd_failed),
            ("overlap", mask and fd_failed),
        ):
            group[name] += value
    masks = sum(r["mask_failed"] for r in rows)
    fds = sum(r["fd_failed"] for r in rows)
    explained = all(
        r["mask_failed"] and r["clipping_accounts_for_gap_within_arithmetic_envelope"]
        for r in rows
        if r["fd_failed"]
    )
    if masks != 35 or fds != 34 or len(set(failures)) != 69:
        raise ValueError("all original failed condition identities must remain")
    passed = all(checks)
    return {
        "plan": plan_payload(),
        "retained_rows": copy.deepcopy(rows),
        "original_fit_proxy_unchanged": copy.deepcopy(prior["original_fit_proxy_unchanged"]),
        "failed_condition_indices": sorted(failures),
        "groups": groups,
        "scalar_conditions": len(checks),
        "failed_scalar_conditions": sum(not c for c in checks),
        "mask_failures": masks,
        "fd_failures": fds,
        "overlapping_mask_and_fd_failures": sum(r["mask_failed"] and r["fd_failed"] for r in rows),
        "all_failed_fd_rows_cross_and_are_clipping_compatible": explained,
        "method_dispositions": dict(METHODS),
        "cost_diagnostics": cost_review(prior["original_fit_proxy_unchanged"]),
        "review_acceptance_passed": passed,
        "next_slice": METHOD_NEXT if passed and explained else EVIDENCE_NEXT,
        "prior_review_sha256": BINDINGS["review.json"],
        **boundary_fields(),
    }


def execution_release(output):
    repo = Path(__file__).resolve().parents[1]

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()

    if git("branch", "--show-current") != "main" or git(
        "status", "--porcelain", "--untracked-files=no"
    ):
        raise ValueError("requires clean tracked merged main source")
    if sys.version_info[:2] != (3, 12) or Path(sys.prefix) != repo / ".venv":
        raise ValueError("requires locked repository Python")
    if any(os.environ.get(k) != "1" for k in THREADS):
        raise ValueError("requires all five one-thread settings")
    release = read(output, "audit_receipts/production_release.json")
    revision = git("rev-parse", "HEAD")
    if (
        release["source_revision"] != revision
        or not release["all_applicable_ci_passed_before_merge"]
        or not release["same_tree_as_tested_head"]
        or not ci_passed(read(output, "audit_receipts/source_final_head_ci.json"), False)
        or not ci_passed(read(output, "audit_receipts/source_main_ci.json"), True)
        or git("rev-parse", release["tested_head"] + "^{tree}") != git("rev-parse", "HEAD^{tree}")
    ):
        raise ValueError("requires separately CI-passed merged source release")
    for name, digest in release["source_sha256"].items():
        safe_hash(repo, name, digest)
    return revision


def peak_rss():
    return int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * (
        1 if sys.platform == "darwin" else 1024
    )


def close_resources(output, commands, report, audit):
    names = [c["name"] for c in commands]
    if not names or names != ["plan", "review", "independent"][: len(names)]:
        raise ValueError("requires ordered unique attempts without retry")
    profiles, charges = {}, {}
    for command in commands:
        name = command["name"]
        profiles[name] = native = check_command(output, command)
        receipt = report if name == "review" else audit if name == "independent" else None
        if name != "plan":
            if command["exit_code"] == 0 and receipt is None:
                raise ValueError("successful stage result missing")
            charges[name] = max(
                native["wall_seconds"] + 10, receipt["charged_seconds"] if receipt else 0
            )
    total = 60 + math.fsum(charges.values())
    if (
        total > 180
        or any(c > 60 for c in charges.values())
        or max(p["rss_bytes"] for p in profiles.values()) > 1073741824
    ):
        raise ValueError("frozen whole/process/memory cap exceeded")
    complete = len(names) == 3 and all(c["exit_code"] == 0 for c in commands)
    if complete and (
        report["plan"] != plan_payload()
        or not audit["passed"]
        or audit["review_sha256"] != sha(canonical(report))
        or any(
            v[k] != expected for v in (report, audit) for k, expected in boundary_fields().items()
        )
    ):
        raise ValueError("complete independent review binding differs")
    prospective = None
    if complete:
        fixed = report["cost_diagnostics"]["zero_prediction_seconds"] + 200.98 + total
        prospective = {
            "original_proxy_seconds_unchanged": report["cost_diagnostics"][
                "original_maximum_seconds"
            ],
            "with_b4_24_and_b4_25_seconds": report["cost_diagnostics"]["original_maximum_seconds"]
            + 200.98
            + total,
            "conditional_prediction_budget_seconds": 7200 - fixed,
            "diagnostic_only": True,
            "full_fit_memory_feasibility_pending": True,
        }
    return {
        "closed": True,
        "full_review_complete": complete,
        "review_acceptance_passed": bool(complete and report["review_acceptance_passed"]),
        "plan_sha256": plan_payload()["plan_sha256"],
        "charged_seconds": total,
        "paid_reservation_seconds": 60,
        "native_profiles_before_closure": profiles,
        "stage_charges": charges,
        "failed_processes": sum(c["exit_code"] != 0 for c in commands),
        "prospective_accounting_diagnostic": prospective,
        "review_sha256": sha(canonical(report)) if report else None,
        "independent_audit_sha256": sha(canonical(audit)) if audit else None,
        "next_slice": report["next_slice"] if complete else EVIDENCE_NEXT,
        **boundary_fields(),
    }


def verify_resources(output, closed):
    profiles = {
        name: check_command(output, read(output, "audit_receipts/" + name + "_command.json"))
        for name in (*closed["native_profiles_before_closure"], "closure")
    }
    reserve = (
        profiles["plan"]["wall_seconds"]
        + 10
        + max(profiles["closure"]["wall_seconds"] + 10, closed["closure_internal_charge_seconds"])
    )
    if reserve > 50 or max(p["rss_bytes"] for p in profiles.values()) > 1073741824:
        raise ValueError("insufficient remaining verification reserve or memory exceeded")
    return {
        "passed": True,
        "metadata_only": True,
        "native_profiles": profiles,
        "reserved_use_before_verification_seconds": reserve,
        "resource_close_sha256": sha((output / "resource_close.json").read_bytes()),
        **boundary_fields(),
    }


def publish(output, name, value, revision, started):
    value.update(
        source_revision=revision,
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
    )
    if value["charged_seconds"] > 60 or value["peak_rss_bytes"] > 1073741824:
        raise RuntimeError("read-only process cap exceeded")
    with (output / name).open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())
    print(canonical({"output": name, "charged_seconds": value["charged_seconds"]}).decode(), end="")


def main(argv=None):
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=("plan", "review", "audit", "close", "verify"), default="plan"
    )
    parser.add_argument("--review-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    root, output = args.review_root.resolve(), args.output_root.resolve()
    repo = Path(__file__).resolve().parents[1]
    if (
        args.mode == "plan"
        or root.parent != output.parent
        or root.name != "b4-24-registered-continuation-v3"
        or output.name != "b4-25-active-set-method-review"
        or any(p.is_relative_to(repo) for p in (root, output))
    ):
        raise ValueError("requires fixed distinct external sibling roots and execution mode")
    name = {
        "review": "review.json",
        "audit": "independent_audit.json",
        "close": "resource_close.json",
        "verify": "resource_verification.json",
    }[args.mode]
    if (output / name).exists():
        raise ValueError("refuses to overwrite frozen attempt")
    revision = execution_release(output)
    if args.mode in ("review", "audit"):
        bound = check_inputs(root)
        if args.mode == "review":
            result = review(bound["review.json"])
        else:
            from b4_25_independent_audit import audit

            result = audit(bound["review.json"], read(output, "review.json"))
        check_inputs(root)
        publish(output, name, result, revision, started)
    elif args.mode == "close":
        results = [
            read(output, p) if (output / p).exists() else None
            for p in ("review.json", "independent_audit.json")
        ]
        result = close_resources(
            output, read(output, "audit_receipts/execution_commands.json"), *results
        )
        result.update(
            source_revision=revision,
            closure_internal_charge_seconds=perf_counter() - started + 10,
            closure_internal_peak_rss_bytes=peak_rss(),
        )
        if (
            result["closure_internal_charge_seconds"] > 60
            or result["closure_internal_peak_rss_bytes"] > 1073741824
        ):
            raise RuntimeError("closure cap exceeded")
        with (output / name).open("xb") as stream:
            stream.write(canonical(result))
            stream.flush()
            os.fsync(stream.fileno())
        print(
            canonical({"output": name, "charged_seconds": result["charged_seconds"]}).decode(),
            end="",
        )
    else:
        publish(
            output,
            name,
            verify_resources(output, read(output, "resource_close.json")),
            revision,
            started,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
