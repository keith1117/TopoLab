"""Frozen read-only B4.10 terminal-certificate and charged-cost diagnosis."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import resource
import statistics
import subprocess
from itertools import combinations
from pathlib import Path
from time import perf_counter
from typing import Any

VERSION = "topolab.b4_11.polish-diagnosis.v1"
SOURCE_VERSION = "topolab.b4_10.post-plateau-probe.v1"
SOURCE_REVISION = "fd13aa1c85a05e638ea02e74712c216319c7488d"
SOURCE_PLAN = "6583e32416d789e719e6bccc9707e7083d30acfefb7c2fc2b5ae314fd77aa983"
MAX_SECONDS = 360.0
PROCESS_SECONDS = 120.0
MAX_RSS_BYTES = 1_073_741_824
METHODS = (
    "uniform",
    "physics_heuristic",
    "nearest_neighbor",
    *(f"{arm}/{seed}" for arm in ("C", "P", "W") for seed in (17, 29, 43)),
)
BINDINGS = {
    "audit_receipts/plan.json": "19c866cf2edd7c3322aa4f4360745a7a30a0827bb49b904b9c3ff1df2d36c10a",
    "audit_receipts/production_release.json": (
        "18a8b09b39e9e45dfdb917ffe42c14d2e27d10d3b45838431513869d673a705f"
    ),
    "audit_receipts/evidence_release.json": (
        "4b5d38eb6fbfabba5c7af69ce0000f85a4e0a2b204afc5a6ed50528747bd4752"
    ),
    "context.json": "30d732690a14d92ae4d7dd865c84eab06dd14a241de70225effadd46beec672a",
    "sentinel/reference/progress.json": (
        "d87ac44e28d8cfcba7f636a88eb4238e6f73e302f161e242e892fdccdf8eba3b"
    ),
    "sentinel/reference/summary.json": (
        "1a9fc1d43bb554a13e23ddcde2aa142f535046b3446aa4adf589a7c2b31d8fad"
    ),
    "sentinel/screen/progress.json": (
        "aa4eed9c1c5ef61c19db66f91464f85eec5d7e88ff249d68aad7d6899dc61e46"
    ),
    "sentinel/screen/summary.json": (
        "6680f57d0b80d8c785ad8378f64c2ce5cbf05596f70fccbedb711da1449336af"
    ),
    "sentinel/audit/progress.json": (
        "f98a5c04412480bb92d5db4be32e5f26bba5efb8fe47efbd29b609d1deca2436"
    ),
    "sentinel/audit/summary.json": (
        "0ba791238a9ae5a54f49d205719d7730f31824fa91f02334f96ed730bb1e1a1d"
    ),
    "sentinel/policy-audit/progress.json": (
        "71e052a0dabc6f5c3523c17096d753fa9b186285667b3abe6c33f0473dfdc20b"
    ),
    "sentinel/policy-audit/summary.json": (
        "063dce98cf700eb9c2b745d0b026fb2d47b3ca39a2a1054c514912c135f2e09e"
    ),
    "sentinel/independent_audit.json": (
        "9b888e761bf404010cf902bb4d5b0df1fef06233b13909b734f0b7268c050fa8"
    ),
    "resource_close.json": "f95d29fca1fe9515de887892f888417ea17e5746ef07fe9923b584d7d2157c5d",
}


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read(root: Path, relative: str, expected: str | None = None) -> dict[str, Any]:
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("artifact path escapes its permitted evidence root")
    raw = target.read_bytes()
    if expected is not None and sha(raw) != expected:
        raise ValueError(f"input checksum differs: {relative}")
    value = json.loads(raw)
    if canonical(value) != raw:
        raise ValueError("evidence canonical bytes differ")
    return value


def plan_payload() -> dict[str, Any]:
    value = {
        "version": VERSION,
        "source_revision": SOURCE_REVISION,
        "source_plan_sha256": SOURCE_PLAN,
        "bindings": BINDINGS,
        "cases": 9,
        "outcomes": 108,
        "methods": list(METHODS),
        "prepolish_witnesses": 24,
        "fixed_twenty_update_continuations": 12,
        "analyses": [
            "terminal_certificates_before_after",
            "all_method_strata_and_phases",
            "fixed_primary_measured_fallback_free_failed_to_uniform",
            "shared_specialist_pairs",
        ],
        "decision_order": [
            "reject_changed_or_incomplete_evidence",
            "candidate_terminal_witness_preservation_probe_if_certificates_and_cost",
            "generalist_reliability_and_refinement_method_review_otherwise",
        ],
        "bounds": ["measured", "fallback_free", "failed_to_uniform"],
        "timing_spread_factor": 1.25,
        "max_seconds": MAX_SECONDS,
        "process_seconds": PROCESS_SECONDS,
        "closure_seconds": 30,
        "max_rss_bytes": MAX_RSS_BYTES,
        "close_allowance_per_process": 10,
        "solver_calls": 0,
        "label_model_byte_reads": 0,
        "final_artifact_reads": 0,
        "fresh_cases_sealed": 48,
        "polish_length_search": False,
    }
    return {**value, "plan_sha256": sha(canonical(value))}


def check_inputs(root: Path) -> dict[str, Any]:
    bound = {p: read(root, p, expected) for p, expected in BINDINGS.items()}
    plan, context = bound["audit_receipts/plan.json"], bound["context.json"]
    decision = bound["sentinel/policy-audit/summary.json"]["decision"]
    close = bound["resource_close.json"]
    if (
        context["version"] != SOURCE_VERSION
        or context["plan_sha256"] != SOURCE_PLAN
        or context["source"]["source_revision"] != SOURCE_REVISION
        or plan["plan_sha256"] != SOURCE_PLAN
        or sha(canonical({k: v for k, v in plan.items() if k != "plan_sha256"})) != SOURCE_PLAN
        or len(plan["cases"]["sentinel"]) != 9
        or len(plan["assignments"]["sentinel"]) != 108
        or decision["fixed_primary"] != 17
        or decision["sentinel_gate_passed"]
        or decision["final_access"]
        or not close["closed"]
        or close["polish_gate_passed"]
        or not close["fresh_sealed"]
        or (root / "fresh").exists()
        or not bound["sentinel/policy-audit/summary.json"]["policy_integrity_passed"]
        or not bound["sentinel/independent_audit.json"]["passed"]
        or bound["sentinel/independent_audit.json"]["gate_passed"]
        or not bound["audit_receipts/evidence_release.json"][
            "all_applicable_ci_passed_before_merge"
        ]
    ):
        raise ValueError("requires complete failed fixed-primary evidence and sealed fresh cases")
    for stage in ("screen", "audit"):
        if bound[f"sentinel/{stage}/summary.json"]["decision"] != decision:
            raise ValueError("closed scientific decisions differ")
    if bound["sentinel/independent_audit.json"]["decision"] != decision:
        raise ValueError("independent failed decision differs")
    if len(close["protected_inputs"]) != 18:
        raise ValueError("protected historical population differs")
    for path, expected in close["protected_inputs"].items():
        target = (root.parent / path).resolve()
        if not target.is_relative_to(root.parent.resolve()) or sha(target.read_bytes()) != expected:
            raise ValueError("protected historical input changed")
    return bound


def chain(root: Path, stage: str, expected: list[str], context: str) -> list[dict[str, Any]]:
    progress, summary = (read(root, f"sentinel/{stage}/{s}.json") for s in ("progress", "summary"))
    if (
        progress["context_sha256"] != context
        or progress["units_sha256"] != sha(canonical(expected))
        or progress["completed"] != len(expected)
        or progress["attempted"] != len(expected)
        or progress["pending"] is not None
        or progress["active_at"] is not None
        or progress["integrity_failed"]
        or progress["resource_failed"]
        or any(
            progress[k] != summary[k]
            for k in ("completed", "attempted", "head_sha256", "charged_seconds", "peak_rss_bytes")
        )
    ):
        raise ValueError("closed assigned journal differs")
    head, payloads = "0" * 64, []
    for ordinal, unit in enumerate(expected):
        item = read(root, f"sentinel/{stage}/units/{ordinal:04d}.json")
        if (
            item["unit"] != unit
            or item["previous_sha256"] != head
            or item["context_sha256"] != context
        ):
            raise ValueError("journal identity or hash chain differs")
        head = sha(canonical(item))
        payloads.append(item["payload"])
    if head != progress["head_sha256"]:
        raise ValueError("journal terminal head differs")
    return payloads


def blob(root: Path, stage: str, ref: dict[str, Any], kind: str) -> dict[str, Any]:
    expected = f"artifacts/{kind}/{ref['sha256']}.json"
    if ref["path"] != expected:
        raise ValueError("content-addressed path differs")
    value = read(root, f"sentinel/{stage}/{expected}", ref["sha256"])
    if len(canonical(value)) != ref["byte_size"]:
        raise ValueError("content-addressed size differs")
    return value


def terminal(
    witness: dict[str, Any], reference: float, volume: float, polished: bool = False
) -> dict[str, Any]:
    result, trace = witness["result"], witness["trace"]
    states, count = result["history"], len(trace)
    if not 1 <= count <= 360 or len(states) != min(11, count):
        raise ValueError("terminal trace or state count differs")
    if [p["iteration"] for p in trace] != list(range(1, count + 1)):
        raise ValueError("terminal trace is not contiguous")
    if (
        reference <= 0
        or not math.isfinite(reference)
        or not all(
            math.isfinite(p[k])
            for p in trace
            for k in ("compliance", "volume_fraction", "density_change")
        )
    ):
        raise ValueError("nonfinite or invalid scalar trace")
    for state, point in zip(states, trace[-11:], strict=True):
        if any(
            state[k] != point[k]
            for k in ("iteration", "compliance", "volume_fraction", "density_change")
        ):
            raise ValueError("retained state differs from scalar trace")
    for key in ("design_density", "physical_density", "compliance"):
        if result[key] != states[-1][key]:
            raise ValueError("terminal state differs")
    if not all(
        math.isfinite(v)
        for key in ("design_density", "physical_density", "displacements", "reactions")
        for v in result[key]
    ):
        raise ValueError("nonfinite terminal state")
    changes = [
        max(abs(a - b) for a, b in zip(x["physical_density"], y["physical_density"], strict=True))
        for x, y in zip(states, states[1:], strict=False)
    ]
    gain = (states[0]["compliance"] - states[-1]["compliance"]) / states[0]["compliance"]
    physical = max(changes, default=0.0)
    design_pass = states[-1]["density_change"] <= 0.01
    plateau = len(states) == 11 and physical <= 0.01 and 0 <= gain <= 0.0002
    error = abs(math.fsum(result["physical_density"]) / len(result["physical_density"]) - volume)
    reasons = []
    if not result["converged"] or not (design_pass or plateau):
        reasons.append("not_converged")
    if result["compliance"] > reference * 1.001:
        reasons.append("compliance_above_matched_uniform")
    if error > 0.005:
        reasons.append("physical_volume_error")
    if result["converged"] and not (design_pass or plateau):
        raise ValueError("declared convergence lacks its terminal certificate")
    stop = (
        "design_change"
        if design_pass
        else "physical_plateau"
        if plateau
        else "post_polish_nonconvergence"
        if polished
        else "iteration_cap"
        if count == 360
        else "nonconverged"
    )
    return {
        "succeeded": not reasons,
        "converged": result["converged"],
        "stop": stop,
        "quality_reasons": reasons,
        "iterations": count,
        "compliance_ratio": result["compliance"] / reference,
        "physical_volume_error": error,
        "last_design_change": states[-1]["density_change"],
        "last_ten_physical_change_max": physical if len(states) == 11 else None,
        "last_ten_compliance_improvement": gain if len(states) == 11 else None,
        "design_certificate": design_pass,
        "plateau_certificate": plateau,
    }


def costs(rows: list[dict[str, Any]], scenario: str) -> dict[str, Any]:
    if scenario not in ("measured", "fallback_free", "failed_to_uniform"):
        raise ValueError("unknown fixed cost scenario")
    paid = [
        r["seconds"]
        if scenario == "measured"
        else r["seconds"] - r["fallback_seconds"]
        if scenario == "fallback_free"
        else r["uniform_seconds"]
        if not r["candidate"]["succeeded"]
        else r["seconds"]
        for r in rows
    ]
    uniform = [r["uniform_seconds"] for r in rows]
    ratios = [a / b for a, b in zip(paid, uniform, strict=True)]
    return {
        "cases": len(rows),
        "mean_paired_ratio": statistics.mean(ratios),
        "ratio_of_sums": math.fsum(paid) / math.fsum(uniform),
        "charged_seconds": math.fsum(paid),
        "uniform_seconds": math.fsum(uniform),
        "observed_failures": sum(not r["candidate"]["succeeded"] for r in rows),
        "diagnostic_only": scenario != "measured",
        "observed_statuses_preserved": True,
    }


def scientific_decision(rows: list[dict[str, Any]]) -> dict[str, Any]:
    repaired, regressions, negative, failures, primary = [], [], [], [], []
    for row in rows:
        if not row["method"].startswith("P/"):
            continue
        before = row["before"] or row["candidate"]
        key = [row["case_id"], row["method"]]
        target = (
            row["scale"] == "large" and row["direction"] == "y" and row["route"] == "generalist"
        )
        if target and not before["succeeded"]:
            (repaired if row["candidate"]["succeeded"] else regressions).append(key)
        if before["succeeded"] and not row["candidate"]["succeeded"]:
            regressions.append(key)
        if not target and not before["succeeded"]:
            negative.append(key)
        if row["method"] == "P/17":
            if not row["candidate"]["succeeded"]:
                failures.append(row["case_id"])
            if target:
                primary.append(row)
    measured = costs(primary, "measured")
    mean, total = measured["mean_paired_ratio"], measured["ratio_of_sums"]
    return {
        "sentinel_gate_passed": len(repaired) == 4
        and not regressions
        and not failures
        and mean <= 1
        and total <= 1,
        "fixed_primary": 17,
        "repaired": repaired,
        "regressions": regressions,
        "primary_failures": failures,
        "negative_controls": negative,
        "large_y_primary_mean": mean,
        "large_y_primary_total_ratio": total,
        "final_access": False,
    }


def next_mechanism(rows: list[dict[str, Any]], bound: dict[str, Any]) -> str:
    regressions = [
        r
        for r in rows
        if r["method"] == "P/17"
        and r["before"] is not None
        and r["before"]["succeeded"]
        and not r["candidate"]["succeeded"]
    ]
    if (
        len(regressions) == 1
        and regressions[0]["triggered"]
        and regressions[0]["candidate"]["stop"] == "post_polish_nonconvergence"
        and regressions[0]["candidate"]["quality_reasons"] == ["not_converged"]
        and regressions[0]["candidate"]["compliance_ratio"]
        <= regressions[0]["before"]["compliance_ratio"]
        and max(bound["mean_paired_ratio"], bound["ratio_of_sums"]) < 1
    ):
        return "bounded_candidate_terminal_witness_preservation_probe"
    return "generalist_reliability_and_refinement_method_review"


def peak_rss() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if platform.system() == "Darwin" else 1024
    )


def diagnose(root: Path) -> dict[str, Any]:
    started = perf_counter()
    bound = check_inputs(root)
    plan = bound["audit_receipts/plan.json"]
    context = BINDINGS["context.json"]
    cases = {c["case_id"]: c for c in plan["cases"]["sentinel"]}
    ordered = plan["assignments"]["sentinel"]
    names = [c + ":" + p for c, p in ordered]
    refs = chain(root, "reference", list(cases), context)
    screens = chain(root, "screen", names, context)
    audited = chain(
        root,
        "audit",
        [
            "inputs",
            "nn_labels",
            *("reference:" + c for c in cases),
            *("screen:" + s for s in names),
        ],
        context,
    )
    policy = chain(
        root,
        "policy-audit",
        [*("reference:" + c for c in cases), *("policy:" + s for s in names)],
        context,
    )
    if audited[0]["audited_checkpoints"] != 12 or audited[1]["audited_nn_labels"] != 528:
        raise ValueError("prior complete input audit population differs")
    rows, reference_rows, pairs = [], [], []
    classified, prepolish, continuations, unchanged = 0, 0, 0, 0
    for case_number, (case_id, case) in enumerate(cases.items()):
        if perf_counter() - started + 10 > PROCESS_SECONDS or peak_rss() > MAX_RSS_BYTES:
            raise RuntimeError("diagnostic process resource cap exceeded")
        problem = case["problem"]
        nx, ny, _ = problem["mesh"]["element_counts"]
        volume, direction = (
            problem["optimization"]["volume_fraction"],
            problem["loads"][0]["direction"],
        )
        ref_packet = blob(root, "reference", refs[case_number], "outcome")
        if (
            ref_packet["case_id"],
            ref_packet["policy"],
            ref_packet["version"],
            ref_packet["context_sha256"],
        ) != (case_id, "uniform", SOURCE_VERSION, context):
            raise ValueError("reference assignment differs")
        reference = ref_packet["outcome"]["attempt"]["metrics"]["final_compliance"]
        ref_summary = terminal(ref_packet["outcome"]["attempt"]["state"], reference, volume)
        if not ref_summary["succeeded"] or not policy[case_number]["reference_identity_checked"]:
            raise ValueError("mandatory unchanged reference failed")
        recording = read(root, f"sentinel/reference/recording/{case_number:04d}.json")
        if (
            recording["context_sha256"] != context
            or recording["outcome_sha256"] != refs[case_number]["sha256"]
            or recording["version"] != "topolab.b4_10.recording.v1"
            or not 0 <= recording["recording_seconds_before_receipt"] <= 1
        ):
            raise ValueError("reference durable recording receipt differs")
        reference_rows.append({"case_id": case_id, **ref_summary})
        classified += 1
        panel, uniform_seconds = {}, None
        for ordinal in range(case_number * 12, (case_number + 1) * 12):
            cid, method = ordered[ordinal]
            packet = blob(root, "screen", screens[ordinal], "outcome")
            if (
                cid,
                packet["case_id"],
                packet["policy"],
                packet["version"],
                packet["context_sha256"],
            ) != (case_id, case_id, method, SOURCE_VERSION, context):
                raise ValueError("query assignment differs")
            outcome = packet["outcome"]
            name, _, seed = method.partition("/")
            route = (
                "baseline"
                if not seed
                else (
                    "specialist"
                    if nx == 24 and direction == "y" and volume >= 0.55
                    else "generalist"
                )
            )
            if (outcome["method"], outcome["seed"], outcome["route"]) != (
                "P" if name == "W" else name,
                int(seed) if seed else None,
                route,
            ):
                raise ValueError("query method, seed or route differs")
            timing, callback = packet["timing"], packet["callback"]
            phases = [outcome["attempt"]["timing"]]
            if outcome["fallback"] is not None:
                phases.append(outcome["fallback"]["timing"])
            phase_sum = outcome["route_seconds"] + sum(sum(p.values()) for p in phases)
            if (
                packet["recording_allowance_seconds"] != 1
                or timing["wall_seconds"] <= 0
                or not all(math.isfinite(v) and v >= 0 for v in timing.values())
                or timing["legacy_phase_seconds"] > timing["wall_seconds"]
                or not math.isclose(phase_sum, timing["legacy_phase_seconds"], rel_tol=1e-14)
                or not all(math.isfinite(v) and v >= 0 for p in phases for v in p.values())
                or not all(
                    math.isfinite(callback[k]) and callback[k] >= 0
                    for k in ("wall_seconds", "cpu_seconds", "bytes_written")
                )
                or callback["wall_seconds"] > timing["wall_seconds"]
            ):
                raise ValueError("complete query timing differs")
            recording = read(root, f"sentinel/screen/recording/{ordinal:04d}.json")
            if (
                recording["context_sha256"] != context
                or recording["outcome_sha256"] != screens[ordinal]["sha256"]
                or recording["version"] != "topolab.b4_10.recording.v1"
                or not 0 <= recording["recording_seconds_before_receipt"] <= 1
            ):
                raise ValueError("durable recording receipt differs")
            seconds = timing["wall_seconds"] + 1
            if method == "uniform":
                uniform_seconds = seconds
            if uniform_seconds is None:
                raise ValueError("uniform must precede candidates")
            before, triggered, updates = None, False, 0
            policy_unit = policy[9 + ordinal]
            if name == "P" and route == "generalist":
                record = read(root, f"sentinel/screen/polish/{case_id}_{seed}.json")
                witness = blob(root, "screen", record["before"], "prepolish")
                before = terminal(witness, reference, volume)
                triggered = (
                    nx == 24
                    and direction == "y"
                    and volume < 0.55
                    and before["converged"]
                    and not before["design_certificate"]
                    and before["plateau_certificate"]
                )
                updates = 20 if triggered else 0
                if (
                    record["context_sha256"],
                    record["case_id"],
                    record["seed"],
                    record["triggered"],
                    record["first_stop_iteration"],
                    record["updates"],
                ) != (context, case_id, int(seed), triggered, before["iterations"], updates):
                    raise ValueError("prepolish receipt or fixed twenty-update rule differs")
                now = outcome["attempt"]["state"]
                if (
                    now["trace"][: before["iterations"]] != witness["trace"]
                    or len(now["trace"]) != before["iterations"] + updates
                    or sha(canonical(now)) != record["after_witness_sha256"]
                    or not policy_unit["prepolish_audited"]
                ):
                    raise ValueError("prepolish state, identity or continuation differs")
                if not triggered and witness != now:
                    raise ValueError("untriggered witness changed")
                prepolish += 1
                continuations += triggered
            candidate = terminal(outcome["attempt"]["state"], reference, volume, triggered)
            fallback = (
                None
                if outcome["fallback"] is None
                else terminal(outcome["fallback"]["state"], reference, volume)
            )
            for attempt, summary in (
                (outcome["attempt"], candidate),
                (outcome["fallback"], fallback),
            ):
                if attempt is None:
                    continue
                if (
                    attempt["succeeded"] != summary["succeeded"]
                    or (attempt["failure_code"] is None) != summary["succeeded"]
                    or attempt["metrics"]["iterations"] != summary["iterations"]
                    or attempt["metrics"]["final_compliance"]
                    != attempt["state"]["result"]["compliance"]
                    or not math.isclose(
                        attempt["metrics"]["physical_volume_error"],
                        summary["physical_volume_error"],
                        abs_tol=1e-12,
                    )
                ):
                    raise ValueError("retained terminal status or metrics differ")
            if (fallback is not None) != (method != "uniform" and not candidate["succeeded"]):
                raise ValueError("fresh fallback status differs")
            if fallback is not None and (
                not fallback["succeeded"] or abs(fallback["compliance_ratio"] - 1) > 1e-9
            ):
                raise ValueError("paid uniform fallback differs from reference")
            if method == "uniform" and (
                not candidate["succeeded"] or abs(candidate["compliance_ratio"] - 1) > 1e-9
            ):
                raise ValueError("uniform query differs from reference")
            if not triggered:
                if not policy_unit["unchanged_identity_checked"]:
                    raise ValueError("unchanged control identity lacks its closed audit")
                unchanged += 1
            classified += 1 + (fallback is not None)
            fallback_seconds = (
                0 if fallback is None else sum(outcome["fallback"]["timing"].values())
            )
            row = {
                "case_id": case_id,
                "method": method,
                "scale": "small" if nx == 12 else "large",
                "direction": direction,
                "volume": volume,
                "load_node": problem["loads"][0]["node"],
                "route": route,
                "seconds": seconds,
                "uniform_seconds": uniform_seconds,
                "fallback_seconds": fallback_seconds,
                "candidate": candidate,
                "fallback": fallback,
                "before": before,
                "triggered": triggered,
                "added_updates": updates,
                "timing": timing,
                "callback": callback,
                "attempt_phases": outcome["attempt"]["timing"],
                "route_seconds": outcome["route_seconds"],
                "fallback_phases": None if fallback is None else outcome["fallback"]["timing"],
                "recording_seconds": recording["recording_seconds_before_receipt"],
            }
            rows.append(row)
            panel[method] = outcome
        if direction == "y" and nx == 24 and volume >= 0.55:
            for seed in (17, 29, 43):
                for a, b in combinations(("C", "P", "W"), 2):
                    left, right = panel[f"{a}/{seed}"]["attempt"], panel[f"{b}/{seed}"]["attempt"]
                    if any(
                        left[k] != right[k]
                        for k in ("state", "metrics", "succeeded", "failure_code")
                    ):
                        raise ValueError("shared specialist numerical identity differs")
                    paid = {
                        r["method"]: r["seconds"]
                        for r in rows[-12:]
                        if r["method"] in (f"{a}/{seed}", f"{b}/{seed}")
                    }
                    spread = max(paid.values()) / min(paid.values())
                    pairs.append(
                        {
                            "case_id": case_id,
                            "left": f"{a}/{seed}",
                            "right": f"{b}/{seed}",
                            "charged_seconds": paid,
                            "spread": spread,
                            "flagged": spread >= 1.25,
                        }
                    )
    if (len(rows), classified, prepolish, continuations, unchanged, len(pairs)) != (
        108,
        132,
        24,
        12,
        96,
        9,
    ):
        raise ValueError("complete diagnostic population differs")
    primary = [
        r
        for r in rows
        if r["method"] == "P/17"
        and r["scale"] == "large"
        and r["direction"] == "y"
        and r["route"] == "generalist"
    ]
    scenarios = {s: costs(primary, s) for s in plan_payload()["bounds"]}
    decision = scientific_decision(rows)
    retained = bound["sentinel/policy-audit/summary.json"]["decision"]
    if any(
        decision[k] != retained[k]
        for k in decision
        if k not in ("large_y_primary_mean", "large_y_primary_total_ratio")
    ):
        raise ValueError("recomputed fixed-primary quality decision differs")
    measured = scenarios["measured"]
    if not math.isclose(
        measured["mean_paired_ratio"], retained["large_y_primary_mean"], rel_tol=1e-14
    ) or not math.isclose(
        measured["ratio_of_sums"], retained["large_y_primary_total_ratio"], rel_tol=1e-14
    ):
        raise ValueError("fixed-primary complete costs differ")
    strata = []
    for method in METHODS:
        for scale in ("small", "large"):
            for direction in ("y", "z"):
                group = [
                    r
                    for r in rows
                    if (r["method"], r["scale"], r["direction"]) == (method, scale, direction)
                ]
                strata.append(
                    {
                        "method": method,
                        "scale": scale,
                        "direction": direction,
                        **costs(group, "measured"),
                        "updates": sum(r["candidate"]["iterations"] for r in group),
                        "fallback_seconds": sum(r["fallback_seconds"] for r in group),
                    }
                )
    optimistic = scenarios["fallback_free"]
    slack = min(
        (1 - optimistic["mean_paired_ratio"])
        * len(primary)
        / sum(1 / r["uniform_seconds"] for r in primary),
        (optimistic["uniform_seconds"] - optimistic["charged_seconds"]) / len(primary),
    )
    check_inputs(root)
    return {
        "plan": plan_payload(),
        "cases": 9,
        "outcomes": 108,
        "classified_attempts": classified,
        "prepolish_witnesses": prepolish,
        "continuations": continuations,
        "added_updates": sum(r["added_updates"] for r in rows),
        "unchanged_identities": unchanged,
        "references": reference_rows,
        "rows": rows,
        "strata": strata,
        "shared_specialist_pairs": pairs,
        "scientific_decision": decision,
        "fixed_primary_cost_scenarios": scenarios,
        "optimistic_constant_guard_budget_seconds_per_target_query": max(0.0, slack),
        "timing_totals": {
            k: sum(r["timing"][k] for r in rows)
            for k in ("wall_seconds", "cpu_seconds", "legacy_phase_seconds")
        },
        "callback_totals": {
            k: sum(r["callback"][k] for r in rows)
            for k in ("wall_seconds", "cpu_seconds", "bytes_written")
        },
        "next_mechanism": next_mechanism(rows, optimistic),
        "fresh_sealed": True,
        "source_resource_close": bound["resource_close.json"],
        "claim": "read_only_diagnosis_not_a_repaired_gate",
    }


def main(argv: list[str] | None = None) -> int:
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    root, output = args.screen_root.resolve(), args.output_root.resolve()
    repository = Path(__file__).resolve().parents[1]
    if root.is_relative_to(repository) or output.is_relative_to(repository):
        raise ValueError("evidence roots must be outside the source repository")
    if root.is_relative_to(output) or output.is_relative_to(root):
        raise ValueError("output must be separate from immutable input")
    if not args.execute:
        print(json.dumps(plan_payload(), sort_keys=True))
        return 0
    if (
        root.name != "b4-10-post-plateau-polish"
        or output.name != "b4-11-polish-diagnosis"
        or root.parent != output.parent
    ):
        raise ValueError("execution requires the fixed sibling evidence roots")
    if output.exists():
        raise ValueError("refuses to overwrite an existing diagnosis")
    if any(
        subprocess.run(c, cwd=repository, check=False).returncode
        for c in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"])
    ):
        raise ValueError("execution requires clean committed tracked source")
    if any(
        os.environ.get(k) != "1"
        for k in (
            "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
        )
    ):
        raise ValueError("execution requires one BLAS/OpenMP thread")
    report = diagnose(root)
    report.update(
        diagnostic_source_revision=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository, text=True
        ).strip(),
        source_sha256=sha(Path(__file__).read_bytes()),
        protocol_sha256=sha(
            (repository / "docs/planning/b4_11_polish_diagnosis_protocol.md").read_bytes()
        ),
        charged_seconds=perf_counter() - started + 10,
        peak_rss_bytes=peak_rss(),
    )
    if report["charged_seconds"] > PROCESS_SECONDS or report["peak_rss_bytes"] > MAX_RSS_BYTES:
        raise RuntimeError("complete diagnostic process resource cap exceeded")
    output.mkdir()
    (output / "diagnosis.json").write_bytes(canonical(report))
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "cases",
                    "outcomes",
                    "classified_attempts",
                    "continuations",
                    "next_mechanism",
                    "charged_seconds",
                    "peak_rss_bytes",
                    "claim",
                )
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
