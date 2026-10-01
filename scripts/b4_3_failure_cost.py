"""Read-only diagnosis of B4.2's immutable development outcomes; never run queries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any

from topolab.b3_artifacts import atomic_write, safe_path
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_materialization import _peak_rss_bytes
from topolab.b3_queries import METHODS, QueryAttempt, QueryOutcome
from topolab.b3_screening import (
    B3EvaluationIndex,
    method_name,
    read_case,
    screen_entries,
    selection_decision,
)
from topolab.dataset_cli import validate_external_output_root

VERSION = "topolab.b4_3.failure_cost.v1"
B42_SOURCE = "4279d20c4922cc2cbfaba0bca722aba8868cd914"
BINDINGS = {
    "b3_screen.json": "a647f420cb2d498c961a6e8ca965511b4a18e33e26056b10cf987d989df8a421",
    "audit_receipts/execution_index.json": (
        "89a7e66ce2c61294c8dcf36585965d04ffeabe1a00b479cf5bd1843427bd588c"
    ),
    "audit_receipts/independent_audit.json": (
        "55bd68b3786b56e30cd74d584f7603e40ed3adf0d701bd9aba62b5cc5b59cab0"
    ),
}
MAX_SECONDS = 180.0
MAX_RSS_BYTES = 1_073_741_824
SEEDS = (17, 29, 43)


def sha256(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def plan_payload() -> dict[str, Any]:
    plan = {
        "version": VERSION,
        "source_revision": B42_SOURCE,
        "bindings": BINDINGS,
        "case_ids": [e.case.case_id for e in screen_entries()],
        "methods": [method_name(m, s) for m, s in METHODS],
        "bounds": ["measured", "fallback_free", "failed_to_uniform"],
        "same_model_pairs": ["P:P_without_S generalist", "C:P:A shared specialist"],
        "timing_spread_factor": 1.25,
        "decision_order": [
            "timing_fidelity_and_checkpoint_instrumentation",
            "terminal_quality_reliability",
            "refinement_cost_if_not_explained_by_recording",
        ],
        "max_seconds": MAX_SECONDS,
        "max_rss_bytes": MAX_RSS_BYTES,
        "scope": "existing_screen_outcomes_only",
        "new_solver_calls": 0,
        "label_and_model_byte_reads": 0,
        "final_artifact_reads": 0,
    }
    return {**plan, "plan_sha256": sha256(canonical_metadata_bytes(plan))}


def input_index(root: Path) -> B3EvaluationIndex:
    """Bind closed failed and successful snapshots without mutating either ledger."""
    contents = {}
    for name, expected in BINDINGS.items():
        raw = safe_path(root, name).read_bytes()
        if sha256(raw) != expected:
            raise ValueError(f"B4.3 input checksum differs: {name}")
        contents[name] = raw
    index = B3EvaluationIndex.model_validate_json(contents["b3_screen.json"])
    original = B3EvaluationIndex.model_validate_json(
        contents["audit_receipts/execution_index.json"]
    )
    if (
        index.context.source.source_revision != B42_SOURCE
        or index.context != original.context
        or index.cases != original.cases
        or not original.completeness_passed
        or len(index.cases) != 48
        or index.attempted_cases != 48
        or index.active_checkpoint_at is not None
        or not index.integrity_failed
        or index.resource_failed
        or index.numerical_failed
        or canonical_metadata_bytes(index.model_dump(mode="json")) != contents["b3_screen.json"]
    ):
        raise ValueError("B4.3 requires the exact complete, closed, retained B4.2 evidence")
    return index


def attempt_summary(attempt: QueryAttempt, uniform: QueryAttempt) -> dict[str, Any]:
    """Read scalar/recent-state evidence without an FEM re-solve or model inference."""
    if attempt.state is None or attempt.metrics is None or uniform.metrics is None:
        raise ValueError("B4.3 requires a retained terminal witness for every attempt")
    state, metrics = attempt.state, attempt.metrics
    reference = uniform.metrics.final_compliance
    recent = state.result.history
    changes = [
        max(abs(a - b) for a, b in zip(left.physical_density, right.physical_density, strict=True))
        for left, right in zip(recent[:-1], recent[1:], strict=True)
    ]
    improvement = (recent[0].compliance - recent[-1].compliance) / recent[0].compliance
    quality_reasons = []
    if not state.result.converged:
        quality_reasons.append("not_converged")
    if metrics.final_compliance > 1.001 * reference:
        quality_reasons.append("compliance_above_matched_uniform")
    if metrics.physical_volume_error > 0.005:
        quality_reasons.append("physical_volume_error")
    if attempt.succeeded != (not quality_reasons):
        raise ValueError("retained candidate status differs from terminal quality conditions")
    plateau = len(recent) == 11 and max(changes) <= 0.01 and 0 <= improvement <= 0.0002
    stopped = (
        "design_change"
        if recent[-1].density_change <= 0.01
        else "physical_plateau"
        if plateau
        else "iteration_cap"
        if not state.result.converged
        else "inconsistent"
    )
    if stopped == "inconsistent":
        raise ValueError("terminal convergence differs from retained stopping evidence")
    crossings = [t.iteration for t in state.trace if t.compliance <= 1.001 * reference]
    return {
        "succeeded": attempt.succeeded,
        "failure_code": attempt.failure_code,
        "quality_reasons": quality_reasons,
        "converged": state.result.converged,
        "stop": stopped,
        "iterations": metrics.iterations,
        "uniform_iterations": uniform.metrics.iterations,
        "iteration_ratio": metrics.iterations / uniform.metrics.iterations,
        "compliance_ratio": metrics.final_compliance / reference,
        "physical_volume_error": metrics.physical_volume_error,
        "last_design_change": recent[-1].density_change,
        "last_ten_physical_change_max": max(changes) if changes else None,
        "last_ten_compliance_improvement": improvement if len(recent) == 11 else None,
        "first_quality_crossing": min(crossings) if crossings else None,
        "trace_samples": [
            t.model_dump(mode="json")
            for t in state.trace
            if t.iteration in (1, 10, 30, 60, 120, 240, metrics.iterations)
        ],
        "timing": attempt.timing.model_dump(mode="json"),
    }


def effective_ratio(row: dict[str, Any], bound: str) -> float:
    if bound == "measured":
        return row["seconds"] / row["uniform_seconds"]
    if bound == "fallback_free":
        return (row["seconds"] - row["fallback_seconds"]) / row["uniform_seconds"]
    if bound == "failed_to_uniform":
        return 1.0 if not row["candidate"]["succeeded"] else effective_ratio(row, "measured")
    raise ValueError("unknown diagnostic bound")


def speed_summary(rows: list[dict[str, Any]], bound: str) -> dict[str, Any]:
    cells = {
        f"{scale}/{direction}": statistics.mean(
            effective_ratio(r, bound)
            for r in rows
            if r["scale"] == scale and r["direction"] == direction
        )
        for scale in ("small", "large")
        for direction in ("y", "z")
    }
    scales = {
        scale: statistics.mean(effective_ratio(r, bound) for r in rows if r["scale"] == scale)
        for scale in ("small", "large")
    }
    return {
        "scale_means": scales,
        "direction_means": cells,
        "overall_mean": statistics.mean(effective_ratio(r, bound) for r in rows),
        "speed_bounds_met": max(scales.values()) <= 0.90 and max(cells.values()) <= 1.0,
        "observed_failures": sum(not r["candidate"]["succeeded"] for r in rows),
        "quality_feasible": bound == "measured",
    }


def same_model_pair(left: QueryOutcome, right: QueryOutcome) -> dict[str, Any]:
    if left.attempt is None or right.attempt is None:
        raise ValueError("same-model comparison requires two candidate attempts")
    a, b = left.attempt, right.attempt
    return {
        "left": method_name(left.method, left.seed),
        "right": method_name(right.method, right.seed),
        "states_identical": a.state == b.state,
        "metrics_identical": a.metrics == b.metrics,
        "status_identical": (a.succeeded, a.failure_code) == (b.succeeded, b.failure_code),
        "left_seconds": left.seconds,
        "right_seconds": right.seconds,
        "right_left_time_ratio": right.seconds / left.seconds,
        "spread_factor": max(left.seconds, right.seconds) / min(left.seconds, right.seconds),
        "left_refinement_seconds": a.timing.refinement_seconds,
        "right_refinement_seconds": b.timing.refinement_seconds,
    }


def diagnose(root: Path) -> dict[str, Any]:
    started = perf_counter()
    index = input_index(root)
    decision = selection_decision(tuple(f.measures for f in index.cases))
    if not decision["complete"] or decision["model_gate_passed"]:
        raise ValueError("B4.3 expects the unchanged complete failed scientific Gate")
    rows = []
    pairs = []
    for number, reference in enumerate(index.cases):
        if perf_counter() - started > MAX_SECONDS or _peak_rss_bytes() > MAX_RSS_BYTES:
            raise RuntimeError("B4.3 diagnostic resource cap exceeded")
        record = read_case(root, index.context, reference)
        case = record.entry.case
        nx, ny, _ = case.problem.mesh.element_counts
        uniform = record.outcomes[0].attempt
        assert uniform is not None
        info = {
            "case_id": case.case_id,
            "case_order": number,
            "scale": "small" if nx == 12 else "large",
            "direction": case.problem.loads[0].direction,
            "volume": case.problem.optimization.volume_fraction,
            "load_position": [
                case.problem.loads[0].node % (nx + 1),
                case.problem.loads[0].node // (nx + 1) % (ny + 1),
                case.problem.loads[0].node // ((nx + 1) * (ny + 1)),
            ],
            "uniform_seconds": record.outcomes[0].seconds,
        }
        by_name = {}
        for query in record.outcomes:
            assert query.attempt is not None
            name = method_name(query.method, query.seed)
            by_name[name] = query
            rows.append(
                {
                    **info,
                    "method": name,
                    "route": query.route,
                    "route_seconds": query.route_seconds,
                    "seconds": query.seconds,
                    "fallback_seconds": 0
                    if query.fallback is None
                    else query.fallback.timing.seconds,
                    "candidate": attempt_summary(query.attempt, uniform),
                    "fallback": None
                    if query.fallback is None
                    else attempt_summary(query.fallback, uniform),
                }
            )
        for seed in SEEDS:
            p = by_name[f"P/{seed}"]
            if p.route == "generalist":
                comparisons = [(p, by_name[f"P_without_S/{seed}"])]
            else:
                c, a = by_name[f"C/{seed}"], by_name[f"A/{seed}"]
                comparisons = [(c, p), (c, a), (p, a)]
            pairs.extend({**info, **same_model_pair(a, b)} for a, b in comparisons)
    if len(rows) != 720 or any(
        not p["states_identical"] or not p["metrics_identical"] or not p["status_identical"]
        for p in pairs
    ):
        raise ValueError("complete methods or identical-checkpoint numerical evidence differ")
    groups = defaultdict(list)
    for row in rows:
        groups[(row["method"], row["scale"], row["direction"])].append(row)
    summaries = []
    for (method, scale, direction), group in sorted(groups.items()):
        summaries.append(
            {
                "method": method,
                "scale": scale,
                "direction": direction,
                "cases": len(group),
                "paired_time_mean": statistics.mean(effective_ratio(r, "measured") for r in group),
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
    bounds = {
        bound: {
            str(seed): speed_summary([r for r in rows if r["method"] == f"P/{seed}"], bound)
            for seed in SEEDS
        }
        for bound in plan_payload()["bounds"]
    }
    return {
        "plan": plan_payload(),
        "index_flags": {
            k: getattr(index, k)
            for k in ("integrity_failed", "resource_failed", "numerical_failed")
        },
        "scientific_decision": decision,
        "cases": 48,
        "outcomes": len(rows),
        "rows": rows,
        "strata": summaries,
        "identical_model_pairs": pairs,
        "speed_only_bounds": bounds,
        "next_mechanism": "timing_fidelity_and_checkpoint_instrumentation_then_quality_reliability",
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
    if output.is_relative_to(root) or root.is_relative_to(output):
        raise ValueError("diagnostic output must be separate from the immutable screen root")
    if not args.execute:
        print(json.dumps(plan_payload(), sort_keys=True))
        return 0
    if any(
        subprocess.run(cmd, cwd=repository, check=False).returncode
        for cmd in (
            ["git", "diff", "--quiet"],
            ["git", "diff", "--cached", "--quiet"],
        )
    ):
        raise ValueError("B4.3 execution requires a clean tracked source revision")
    if any(
        os.environ.get(name) != "1"
        for name in (
            "OPENBLAS_NUM_THREADS",
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
            "VECLIB_MAXIMUM_THREADS",
        )
    ):
        raise ValueError("B4.3 requires one BLAS/OpenMP thread")
    if output.exists():
        raise ValueError("B4.3 refuses to overwrite an existing diagnosis")
    report = diagnose(root)
    report["diagnostic_source_revision"] = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=repository,
        text=True,
    ).strip()
    report["script_sha256"] = sha256(Path(__file__).read_bytes())
    report["elapsed_seconds"] = perf_counter() - started
    if report["elapsed_seconds"] + 10 > MAX_SECONDS or report["peak_rss_bytes"] > MAX_RSS_BYTES:
        raise RuntimeError("B4.3 complete diagnostic resource cap exceeded")
    report["charged_seconds"] = report["elapsed_seconds"] + 10
    atomic_write(output / "diagnosis.json", canonical_metadata_bytes(report))
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "cases",
                    "outcomes",
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
