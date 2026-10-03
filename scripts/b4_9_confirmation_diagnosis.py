"""Bounded read-only B4.8 diagnosis; no queries, checkpoint or label byte reads."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import subprocess
from itertools import combinations
from pathlib import Path
from time import perf_counter
from typing import Any

from b4_3_failure_cost import attempt_summary, same_model_pair, speed_summary

from topolab.b3_artifacts import atomic_write, safe_path
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_materialization import _peak_rss_bytes
from topolab.b3_queries import QueryAttempt, QueryOutcome, policy_route
from topolab.b4_evidence import read_packet, recording_receipt
from topolab.b4_rollback_confirmation import CAPS, RECEIPT_VERSION, assignments, fresh_cases, units
from topolab.b4_rollback_confirmation import VERSION as SOURCE_VERSION
from topolab.b4_telemetry import digest
from topolab.b4_weighted_terminal import METHODS, RECORDING_ALLOWANCE, read_units
from topolab.dataset_cli import validate_external_output_root

VERSION = "topolab.b4_9.confirmation-diagnosis.v1"
SOURCE_REVISION = "c185caffd5f3b3cd16b2f2f80948caee1e836784"
SOURCE_PLAN = "1981e64c41fc6b958d530a161bc6d41739e668ca04a3cd2dcdc623aee59dec15"
MAX_SECONDS = 360.0
MAX_RSS_BYTES = 1_073_741_824
SEEDS = (17, 29, 43)
BINDINGS = {
    "audit_receipts/plan.json": "31dece2979a469ea600911036d9e2ab15ae45c593c7b22cf770a4d135758f56f",
    "audit_receipts/production_release.json": (
        "051867604ce5b4dab18d7dca91a046faa077de0578ede07e18a4390e39d21e6c"
    ),
    "context.json": "b405d69754c5c22a1fd936581d44beea2f261db2069600ee327421f953bad5be",
    "reference/progress.json": "aaf793eac36bdbb6a600170c3dfbe26f1ec6f3b59e5eca684254c146e8396616",
    "reference/summary.json": "e55f6f54a94b754c6575bea93a183d71ae3bef3d854447c0277fda5bd15badea",
    "screen/progress.json": "241a73288bf7301c09d8fe17258d250316ea5c8703b8bb1c1c393d1a7b2d84e9",
    "screen/summary.json": "9cf1eb1999c36c2340c53194830dd531c3c4149eeb156e17ab38ab7d46f903af",
    "audit/progress.json": "f1d06c3a99351ffcfbbcc4624d176ab11b2539d6be3c7a5243db70da37d6f98d",
    "audit/summary.json": "7a4ef6d95cbba59734f01ee260f8fae818b89fbec3238b13595f9d63ae9f783b",
    "independent_audit.json": "88c37018ca9f6ca325003c4c5f4b57debf0855bd2313eb3a62dbed50064cd663",
    "resource_close.json": "c4128a77de823b0de2cc83d093157db52e689ee4dbdc4e0f908b675e9c5150ec",
}


def plan_payload() -> dict[str, Any]:
    payload = {
        "version": VERSION,
        "source_revision": SOURCE_REVISION,
        "source_plan_sha256": SOURCE_PLAN,
        "bindings": BINDINGS,
        "case_ids": [c.case_id for c in fresh_cases()],
        "methods": METHODS,
        "bounds": ["measured", "fallback_free", "failed_to_uniform"],
        "same_model_pairs": "C:P:W same-seed shared specialist, all three pairs",
        "timing_spread_factor": 1.25,
        "trace_updates": [1, 10, 30, 60, 120, 240, "terminal"],
        "decision_order": [
            "reject_incomplete_or_changed_evidence",
            "fixed_post_plateau_polish_probe_if_primary_failed_at_physical_plateau",
            "terminal_basin_reliability_review_otherwise",
        ],
        "proposed_polish_updates": 20,
        "max_seconds": MAX_SECONDS,
        "max_rss_bytes": MAX_RSS_BYTES,
        "close_allowance_per_process": 10.0,
        "new_solver_calls": 0,
        "label_and_model_byte_reads": 0,
        "final_artifact_reads": 0,
    }
    return {**payload, "plan_sha256": digest(canonical_metadata_bytes(payload))}


def input_receipts(root: Path) -> dict[str, Any]:
    """Bind every closed receipt before a journal unit or outcome is opened."""
    bound = {}
    for path, expected in BINDINGS.items():
        raw = safe_path(root, path).read_bytes()
        if digest(raw) != expected:
            raise ValueError(f"B4.9 input checksum differs: {path}")
        bound[path] = json.loads(raw)
        if canonical_metadata_bytes(bound[path]) != raw:
            raise ValueError("B4.9 input canonical bytes differ")
    context, decision = bound["context.json"], bound["audit/summary.json"]["decision"]
    if (
        context["version"] != SOURCE_VERSION
        or context["source"]["source_revision"] != SOURCE_REVISION
        or context["plan_sha256"] != SOURCE_PLAN
        or decision["fixed_primary"] != 17
        or decision["confirmation_gate_passed"]
        or decision["final_access"]
        or decision != bound["screen/summary.json"]["decision"]
    ):
        raise ValueError("B4.9 requires the complete unchanged failed fixed-primary Gate")
    match_numbers(decision, bound["independent_audit.json"]["decision"])
    for stage in CAPS:
        progress, summary = bound[f"{stage}/progress.json"], bound[f"{stage}/summary.json"]
        if any(
            progress[k] != summary[k]
            for k in ("attempted", "completed", "head_sha256", "context_sha256", "peak_rss_bytes")
        ):
            raise ValueError("B4.9 summary differs from its closed journal")
    return bound


def match_numbers(actual: Any, expected: Any) -> None:
    if isinstance(expected, dict):
        if actual.keys() != expected.keys():
            raise ValueError("recomputed evidence keys differ")
        for key in expected:
            match_numbers(actual[key], expected[key])
    elif isinstance(expected, float):
        if not math.isclose(actual, expected, rel_tol=1e-14, abs_tol=1e-14):
            raise ValueError("recomputed evidence arithmetic differs")
    elif actual != expected:
        raise ValueError("recomputed evidence classification differs")


def checked_attempt(attempt: QueryAttempt, uniform: QueryAttempt, volume: float) -> dict[str, Any]:
    summary = attempt_summary(attempt, uniform)
    assert attempt.state is not None and attempt.metrics is not None and uniform.metrics is not None
    error = abs(statistics.mean(attempt.state.result.physical_density) - volume)
    if not math.isclose(error, attempt.metrics.physical_volume_error, abs_tol=1e-14):
        raise ValueError("stored physical-volume arithmetic differs")
    summary["minimum_trace_compliance_ratio"] = (
        min(t.compliance for t in attempt.state.trace) / uniform.metrics.final_compliance
    )
    summary["terminal_excess_over_limit"] = summary["compliance_ratio"] - 1.001
    summary["recent_compliance_ratios"] = [
        s.compliance / uniform.metrics.final_compliance for s in attempt.state.result.history
    ]
    return summary


def measured_decision(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute the unchanged Gate from compact rows without retaining density panels."""
    uniform = [r for r in rows if r["method"] == "uniform"]
    table = {}
    for name in METHODS:
        group = [r for r in rows if r["method"] == name]
        stats = speed_summary(group, "measured")
        table[name] = {
            **{k: stats[k] for k in ("overall_mean", "scale_means", "direction_means")},
            "failures": stats["observed_failures"],
            "fallbacks": sum(r["fallback"] is not None for r in group),
            "non_specialist_y_failures": sum(
                not r["candidate"]["succeeded"]
                and r["direction"] == "y"
                and r["route"] != "specialist"
                for r in group
            ),
            "scale_total_ratios": {
                s: sum(r["seconds"] for r in group if r["scale"] == s)
                / sum(r["seconds"] for r in uniform if r["scale"] == s)
                for s in ("small", "large")
            },
        }
    passing = []
    for seed in SEEDS:
        p, c, w = (table[f"{m}/{seed}"] for m in ("P", "C", "W"))
        passed = (
            max(p["scale_means"].values()) <= 0.9
            and max(p["direction_means"].values()) <= 1.0
            and p["failures"] <= min(2, c["failures"], w["failures"])
            and p["non_specialist_y_failures"]
            <= min(c["non_specialist_y_failures"], w["non_specialist_y_failures"])
            and p["overall_mean"]
            < min(table[m]["overall_mean"] for m in ("physics_heuristic", "nearest_neighbor"))
        )
        p["seed_gate_passed"] = passed
        p["primary_eligible"] = (
            passed
            and p["failures"] == p["fallbacks"] == 0
            and p["overall_mean"] < c["overall_mean"]
            and (p["overall_mean"] < w["overall_mean"] or p["failures"] < w["failures"])
        )
        if passed:
            passing.append(seed)
    cells = {
        str(v): sum(
            r["candidate"]["succeeded"]
            for r in rows
            if r["method"].startswith("P/")
            and r["scale"] == "large"
            and r["direction"] == "y"
            and r["volume"] == v
        )
        for v in (0.5413, 0.6013)
    }
    passed = (
        len(passing) >= 2
        and min(cells.values()) >= 12
        and table["P/17"]["primary_eligible"]
        and max(table["P/17"]["scale_total_ratios"].values()) <= 0.9
    )
    return {
        "table": table,
        "passing_seeds": passing,
        "quality_cells": cells,
        "fixed_primary": 17,
        "confirmation_gate_passed": passed,
        "development_gate_passed": passed,
        "final_access": False,
    }


def next_mechanism(rows: list[dict[str, Any]]) -> str:
    primary_failures = [
        r for r in rows if r["method"] == "P/17" and not r["candidate"]["succeeded"]
    ]
    if primary_failures and all(
        r["candidate"]["stop"] == "physical_plateau"
        and r["candidate"]["quality_reasons"] == ["compliance_above_matched_uniform"]
        for r in primary_failures
    ):
        return "fixed_20_update_post_plateau_polish_probe"
    return "terminal_basin_reliability_review"


def diagnostic_bound(rows: list[dict[str, Any]], bound: str) -> dict[str, Any]:
    result = speed_summary(rows, bound)
    result.pop("quality_feasible")
    return {**result, "diagnostic_only": True, "observed_statuses_preserved": True}


def diagnose(root: Path) -> dict[str, Any]:
    started = perf_counter()
    bound = input_receipts(root)
    sha = BINDINGS["context.json"]
    refs = {s: read_units(root / s, sha, units(s), caps=CAPS) for s in CAPS}
    ordered = assignments()
    rows, pairs = [], []
    audited = 0
    for case_index, case in enumerate(fresh_cases()):
        if perf_counter() - started > MAX_SECONDS or _peak_rss_bytes() > MAX_RSS_BYTES:
            raise RuntimeError("B4.9 diagnostic resource cap exceeded")
        ref = refs["reference"][case_index]
        recording_receipt(root / "reference", case_index, ref, sha, RECEIPT_VERSION)
        packet = read_packet(root / "reference", ref, sha, case.case_id, "uniform", SOURCE_VERSION)
        uniform = QueryOutcome.model_validate(packet["outcome"]).attempt
        assert uniform is not None and uniform.metrics is not None
        volume = case.problem.optimization.volume_fraction
        if not checked_attempt(uniform, uniform, volume)["succeeded"]:
            raise ValueError("mandatory reference is not quality-feasible")
        audited += 1
        panel = {}
        uniform_seconds = None
        for ordinal in range(case_index * 12, (case_index + 1) * 12):
            case_id, method = ordered[ordinal]
            ref = refs["screen"][ordinal]
            recording_receipt(root / "screen", ordinal, ref, sha, RECEIPT_VERSION)
            packet = read_packet(root / "screen", ref, sha, case_id, method, SOURCE_VERSION)
            outcome = QueryOutcome.model_validate(packet["outcome"])
            name, _, seed = method.partition("/")
            if (
                case_id != case.case_id
                or outcome.method != ("P" if name == "W" else name)
                or outcome.seed != (int(seed) if seed else None)
                or outcome.route != policy_route(case, outcome.method)
                or outcome.operational is None
                or outcome.attempt is None
                or packet["recording_allowance_seconds"] != RECORDING_ALLOWANCE
                or not math.isfinite(packet["timing"]["wall_seconds"])
                or packet["timing"]["wall_seconds"] <= 0
                or packet["timing"]["legacy_phase_seconds"] > packet["timing"]["wall_seconds"]
            ):
                raise ValueError("query assignment, quality or full timing envelope differs")
            panel[method] = outcome
            seconds = packet["timing"]["wall_seconds"] + RECORDING_ALLOWANCE
            if method == "uniform":
                uniform_seconds = seconds
            if uniform_seconds is None:
                raise ValueError("uniform must precede every matched candidate")
            candidate = checked_attempt(outcome.attempt, uniform, volume)
            fallback = (
                None
                if outcome.fallback is None
                else checked_attempt(outcome.fallback, uniform, volume)
            )
            for attempt in (outcome.attempt if method == "uniform" else None, outcome.fallback):
                if attempt is not None and (
                    not attempt.succeeded
                    or attempt.metrics is None
                    or abs(attempt.metrics.final_compliance / uniform.metrics.final_compliance - 1)
                    > 1e-9
                ):
                    raise ValueError("uniform query/fallback differs from mandatory reference")
            audited += 1 + (fallback is not None)
            nx, ny, _ = case.problem.mesh.element_counts
            load = case.problem.loads[0]
            rows.append(
                {
                    "case_id": case_id,
                    "case_order": case_index,
                    "method": method,
                    "scale": "small" if nx == 12 else "large",
                    "direction": load.direction,
                    "volume": volume,
                    "load_position": [
                        load.node % (nx + 1),
                        load.node // (nx + 1) % (ny + 1),
                        load.node // ((nx + 1) * (ny + 1)),
                    ],
                    "route": outcome.route,
                    "route_seconds": outcome.route_seconds,
                    "seconds": seconds,
                    "uniform_seconds": uniform_seconds,
                    "fallback_seconds": 0
                    if outcome.fallback is None
                    else outcome.fallback.timing.seconds,
                    "candidate": candidate,
                    "fallback": fallback,
                    "query_timing": packet["timing"],
                    "callback": packet["callback"],
                    "recording_before_receipt": json.loads(
                        safe_path(root / "screen", f"recording/{ordinal:04d}.json").read_bytes()
                    )["recording_seconds_before_receipt"],
                }
            )
        for seed in SEEDS:
            if panel[f"P/{seed}"].route == "specialist":
                for left, right in combinations(("C", "P", "W"), 2):
                    pair = same_model_pair(panel[f"{left}/{seed}"], panel[f"{right}/{seed}"])
                    a, b = (
                        r
                        for r in rows[-12:]
                        if r["method"] in (f"{left}/{seed}", f"{right}/{seed}")
                    )
                    # Rotation changes row order; retain policy-labelled charged envelopes.
                    timing = {r["method"]: r["seconds"] for r in (a, b)}
                    pair.update(left=f"{left}/{seed}", right=f"{right}/{seed}")
                    pair["charged_seconds"] = timing
                    pair["charged_spread_factor"] = max(timing.values()) / min(timing.values())
                    pairs.append({"case_id": case.case_id, **pair})
    if (
        len(rows) != 1152
        or len(pairs) != 54
        or audited != 1295
        or any(
            not all(p[k] for k in ("states_identical", "metrics_identical", "status_identical"))
            for p in pairs
        )
    ):
        raise ValueError("complete query, witness or shared-specialist identity differs")
    decision = measured_decision(rows)
    match_numbers(decision, bound["audit/summary.json"]["decision"])
    if decision["confirmation_gate_passed"]:
        raise ValueError("diagnosis cannot clear the failed confirmation")
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
                        "cases": len(group),
                        "paired_time_mean": statistics.mean(
                            r["seconds"] / r["uniform_seconds"] for r in group
                        ),
                        "iteration_ratio_mean": statistics.mean(
                            r["candidate"]["iteration_ratio"] for r in group
                        ),
                        "refinement_seconds_mean": statistics.mean(
                            r["candidate"]["timing"]["refinement_seconds"] for r in group
                        ),
                        "fallback_seconds_sum": sum(r["fallback_seconds"] for r in group),
                        "failures": sum(not r["candidate"]["succeeded"] for r in group),
                    }
                )
    totals = {
        "query_wall": sum(r["query_timing"]["wall_seconds"] for r in rows),
        "query_cpu": sum(r["query_timing"]["cpu_seconds"] for r in rows),
        "callback_wall": sum(r["callback"]["wall_seconds"] for r in rows),
        "callback_cpu": sum(r["callback"]["cpu_seconds"] for r in rows),
        "callback_bytes": sum(r["callback"]["bytes_written"] for r in rows),
        "recording_before_receipt": sum(r["recording_before_receipt"] for r in rows),
    }
    match_numbers(totals, {k: bound["independent_audit.json"]["timing_totals"][k] for k in totals})
    # Recheck immutable bound receipts after all reads; never open a writer on them.
    input_receipts(root)
    return {
        "plan": plan_payload(),
        "scientific_decision": decision,
        "cases": 96,
        "outcomes": len(rows),
        "classified_attempts": audited,
        "rows": rows,
        "strata": strata,
        "identical_model_pairs": pairs,
        "timing_totals": totals,
        "source_resource_close": bound["resource_close.json"],
        "speed_only_bounds": {
            b: {
                str(s): diagnostic_bound([r for r in rows if r["method"] == f"P/{s}"], b)
                for s in SEEDS
            }
            for b in plan_payload()["bounds"]
        },
        "next_mechanism": next_mechanism(rows),
        "elapsed_seconds": perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
        "claim": "read_only_diagnosis_not_a_repaired_gate",
    }


def main(argv: list[str] | None = None) -> int:
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen-root", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    repository = Path(__file__).resolve().parents[1]
    root = validate_external_output_root(repository, args.screen_root)
    output = validate_external_output_root(repository, args.output_root)
    if root.is_relative_to(output) or output.is_relative_to(root):
        raise ValueError("diagnostic output must be separate from the immutable input")
    if not args.execute:
        print(json.dumps(plan_payload(), sort_keys=True))
        return 0
    if any(
        subprocess.run(cmd, cwd=repository, check=False).returncode
        for cmd in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"])
    ):
        raise ValueError("B4.9 execution requires clean committed tracked source")
    if any(
        os.environ.get(k) != "1"
        for k in (
            "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
        )
    ):
        raise ValueError("B4.9 requires one BLAS/OpenMP thread")
    if output.exists():
        raise ValueError("B4.9 refuses to overwrite an existing diagnosis")
    report = diagnose(root)
    report["diagnostic_source_revision"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    report["script_sha256"] = digest(Path(__file__).read_bytes())
    report["protocol_sha256"] = digest(
        (repository / "docs/planning/b4_9_confirmation_diagnosis_protocol.md").read_bytes()
    )
    report["elapsed_seconds"] = perf_counter() - started
    report["charged_seconds"] = report["elapsed_seconds"] + 10
    if report["charged_seconds"] > MAX_SECONDS or report["peak_rss_bytes"] > MAX_RSS_BYTES:
        raise RuntimeError("B4.9 complete diagnostic resource cap exceeded")
    atomic_write(output / "diagnosis.json", canonical_metadata_bytes(report))
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "cases",
                    "outcomes",
                    "classified_attempts",
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
