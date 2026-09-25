"""B2.1 fixed-cohort, opt-in physical-plateau development comparison.

Only M2 catalog/split metadata and M1 training/checkpoint artifacts are read.
No M2 label, test/OOD outcome, or future final artifact is opened. JSON goes
to stdout for an external validation report, never to a repository file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import resource
import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from b1_failure_diagnosis import _predict
from b2_workload_pilot import _nearest_raw, _raw_uniform, scaled_case
from numpy.typing import NDArray

import topolab.simp as simp
from topolab.baselines import (
    _physics_heuristic_raw_density,
    build_nearest_neighbor_index,
    validate_refinement_quality,
)
from topolab.evaluation_cli import production_selection_references
from topolab.experiment import ExperimentCase, project_design_density
from topolab.learned_evaluation import load_m1_candidate
from topolab.m2_dataset import assign_m2_case_splits, build_m2_case_catalog
from topolab.problem import TopologyProblem, TopologyResult, solve_problem
from topolab.simp import PHYSICAL_PLATEAU_SOLVER_VERSION
from topolab.training_cli import load_frozen_m1_materialization

RUNNER_VERSION = "topolab.b2_1.convergence.v1"
EXPECTED_LARGE_IDS = (
    "tlcase-v1-3303f49ad6b4a791a18e89871b650978b10c40bdcade055283e9a068bc599ac2",
    "tlcase-v1-26085a2a8177c288f4506633fc1660fdbdae96306800fc02d69cbf988f1106b1",
    "tlcase-v1-cc988eff60275239d82a848ce0d2c5663978c0b8238a3d75c477627255795727",
    "tlcase-v1-0323121accc756500ebbbf75c037863169a128796d2950a02ffd564b9d4e1cf3",
    "tlcase-v1-17b81b5d678bd05109b31b55272ace9421584ea2e06fad1d39c39c4afa846fdd",
    "tlcase-v1-628d8eeca241819a6dc010777e25f3e990705d98d59c098446710d2770df7ef2",
)
# Historical valid B2 uniform references; failures intentionally have no value.
_B2_VALID_IDS = (
    "tlcase-v1-23a0367ad56d5e1bf4b3fb502f53d3497b3fe06058814ce8f8051c9118f681b4",
    "tlcase-v1-3303f49ad6b4a791a18e89871b650978b10c40bdcade055283e9a068bc599ac2",
    "tlcase-v1-3a3c61d075ba282bb28cf96698a91056352dc3de640bf2f3f3d97d368ef827f1",
    "tlcase-v1-26085a2a8177c288f4506633fc1660fdbdae96306800fc02d69cbf988f1106b1",
    "tlcase-v1-a640fec6eb238af6d2d05b428ff604771d02db192a1c3bc72a481680bfbe85f5",
    "tlcase-v1-cc988eff60275239d82a848ce0d2c5663978c0b8238a3d75c477627255795727",
    "tlcase-v1-6b801ea17e378624f5f56824b854d9315cf79e4ce6e16e3305a3919587d84ccc",
    "tlcase-v1-c107c6c0660eb2a8b85a2470d1f9ae663abc2148edf764856f2b5c948e0bca7b",
    "tlcase-v1-28444cf2c927b14fd8188eebb851f09a8455a9b70f703e13b0d9d25948bf814c",
)
_B2_VALID_VALUES = (
    0.23410159558797244,
    0.20826889721863345,
    0.7757667645196058,
    0.6768288241606875,
    0.038728321039843014,
    0.04079609956628393,
    0.11117481095334457,
    0.02545523703904539,
    0.07961646076011474,
)
B2_VALID_COMPLIANCE = dict(zip(_B2_VALID_IDS, _B2_VALID_VALUES, strict=True))


@dataclass(frozen=True)
class CohortCase:
    case: ExperimentCase
    source_case_id: str
    scale: str
    direction: str
    volume: float


def select_cases() -> tuple[CohortCase, ...]:
    """Reconstruct only the twelve B2 definitions from frozen catalog metadata."""

    catalog = build_m2_case_catalog()
    splits = assign_m2_case_splits(catalog)
    cohort: list[CohortCase] = []
    for volume in (0.2, 0.45, 0.6):
        for direction in ("y", "z"):
            options = [
                case
                for case in catalog.cases
                if splits[case.case_id] == "validation"
                and case.problem.optimization.volume_fraction == volume
                and case.problem.loads[0].direction == direction
            ]
            if len(options) != 2:
                raise ValueError("unexpected B2 validation stratum")
            small = min(options, key=lambda case: case.case_id)
            large = scaled_case(small)
            cohort.extend(
                (
                    CohortCase(small, small.case_id, "small", direction, volume),
                    CohortCase(large, small.case_id, "large", direction, volume),
                )
            )
    if tuple(item.case.case_id for item in cohort if item.scale == "large") != (
        EXPECTED_LARGE_IDS
    ):
        raise ValueError("B2.1 large case identities differ from frozen protocol")
    if {item.case.case_id for item in cohort if item.scale == "small"} != (
        B2_VALID_COMPLIANCE.keys() - set(EXPECTED_LARGE_IDS)
    ):
        raise ValueError("B2.1 small case identities differ from frozen protocol")
    return tuple(cohort)


def result_id(case_id: str) -> str:
    """Bind the old physical case to the new solver semantics."""

    payload = json.dumps(
        {"base_case_id": case_id, "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION},
        sort_keys=True,
        separators=(",", ":"),
    )
    return "tlcase-b21-v1-" + hashlib.sha256(payload.encode()).hexdigest()


def _peak_rss_bytes() -> int:
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def _termination_metrics(result: TopologyResult, tolerance: float) -> dict[str, Any]:
    history = result.history
    window_max = None
    improvement = None
    if len(history) >= 11:
        recent = history[-11:]
        window_max = max(
            float(
                np.max(
                    np.abs(np.asarray(right.physical_density) - left.physical_density)
                )
            )
            for left, right in zip(recent[:-1], recent[1:], strict=True)
        )
        improvement = 1.0 - recent[-1].compliance / recent[0].compliance
    reason = "limit"
    if result.converged:
        reason = (
            "design_max" if history[-1].density_change <= tolerance else "physical_plateau"
        )
    return {
        "termination_reason": reason,
        "last_ten_max_physical_change": window_max,
        "last_ten_relative_compliance_improvement": improvement,
    }


def _refine(
    case: ExperimentCase, raw: NDArray[np.float32]
) -> tuple[TopologyResult, float, float, float, int]:
    projection_started = perf_counter()
    projected = project_design_density(case, raw)
    projection_seconds = perf_counter() - projection_started
    payload = case.problem.model_dump(mode="json")
    payload["initial_density"] = tuple(float(v) for v in projected.design_density)
    problem = TopologyProblem.model_validate(payload)
    fem_seconds = 0.0
    fem_calls = 0
    original = simp.evaluate_compliance

    def measured(*args: Any, **kwargs: Any) -> Any:
        nonlocal fem_seconds, fem_calls
        started = perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            fem_seconds += perf_counter() - started
            fem_calls += 1

    simp.evaluate_compliance = measured
    refinement_started = perf_counter()
    try:
        result = solve_problem(problem, termination_policy="physical_plateau")
    finally:
        refinement_seconds = perf_counter() - refinement_started
        simp.evaluate_compliance = original
    return result, projection_seconds, refinement_seconds, fem_seconds, fem_calls


def _attempt(
    case: ExperimentCase,
    method: str,
    setup: Callable[[], NDArray[np.float32]],
    uniform_compliance: float | None,
    *,
    fallback: bool,
) -> tuple[dict[str, Any], TopologyResult]:
    setup_started = perf_counter()
    raw = setup()
    setup_seconds = perf_counter() - setup_started
    result, projection, refinement, fem, fem_calls = _refine(case, raw)
    passed = True
    failure = None
    try:
        validate_refinement_quality(case, result, uniform_compliance)
    except (ValueError, RuntimeError) as error:
        passed = False
        failure = type(error).__name__
    fallback_seconds = 0.0
    fallback_fem_seconds = 0.0
    if fallback and not passed:
        repeated, fb_projection, fb_refinement, fallback_fem_seconds, _ = _refine(
            case, _raw_uniform(case)
        )
        validate_refinement_quality(case, repeated, None)
        fallback_seconds = fb_projection + fb_refinement
    return {
        "method": method,
        "passed": passed,
        "failure": failure,
        "iterations": len(result.history),
        "converged": result.converged,
        "terminal_design_change": result.history[-1].density_change,
        **_termination_metrics(result, case.problem.optimization.convergence_tolerance),
        "compliance": result.compliance,
        "volume_error": abs(
            float(np.mean(result.physical_density))
            - case.problem.optimization.volume_fraction
        ),
        "setup_seconds": setup_seconds,
        "projection_seconds": projection,
        "refinement_seconds": refinement,
        "fem_seconds": fem,
        "fem_calls": fem_calls,
        "fallback_seconds": fallback_seconds,
        "fallback_fem_seconds": fallback_fem_seconds,
        "charged_seconds": setup_seconds + projection + refinement + fallback_seconds,
        "peak_rss_bytes": _peak_rss_bytes(),
        "quality_audit_excluded": True,
    }, result


def run_comparison(
    cohort: tuple[CohortCase, ...],
    m1_data_root: Path,
    m1_artifact_root: Path,
) -> dict[str, Any]:
    """Run the uniform gate first, then the matched panel only if it passes."""

    rows: list[dict[str, Any]] = []
    uniform_results: dict[str, TopologyResult] = {}
    started = perf_counter()
    for item in cohort:
        case = item.case
        uniform, result = _attempt(
            case, "uniform", partial(_raw_uniform, case), None, fallback=False
        )
        historical_compliance = B2_VALID_COMPLIANCE.get(case.case_id)
        historical_guard = (
            historical_compliance is None
            or result.compliance <= 1.001 * historical_compliance
        )
        uniform["historical_quality_guard_passed"] = historical_guard
        uniform["historical_compliance"] = historical_compliance
        rows.append(
            {
                "case_id": case.case_id,
                "source_case_id": item.source_case_id,
                "result_id": result_id(case.case_id),
                "scale": item.scale,
                "direction": item.direction,
                "volume": item.volume,
                "element_counts": case.problem.mesh.element_counts,
                "uniform": uniform,
                "methods": [],
            }
        )
        uniform_results[case.case_id] = result
        print(
            json.dumps({"uniform_completed": len(rows), "case_id": case.case_id}),
            file=sys.stderr,
            flush=True,
        )
    uniform_gate_passed = all(
        row["uniform"]["passed"] and row["uniform"]["historical_quality_guard_passed"]
        for row in rows
    )
    index_setup_seconds = 0.0
    index_size_bytes = 0
    checkpoint_setup_seconds = 0.0
    checkpoint_count = 0
    if uniform_gate_passed:
        setup_started = perf_counter()
        materialization = load_frozen_m1_materialization(m1_data_root)
        nearest = build_nearest_neighbor_index(m1_data_root, materialization)
        index_setup_seconds = perf_counter() - setup_started
        index_size_bytes = nearest.stored_size_bytes
        setup_started = perf_counter()
        candidates = tuple(
            load_m1_candidate(m1_artifact_root, reference)
            for reference in production_selection_references(m1_artifact_root)
        )
        checkpoint_setup_seconds = perf_counter() - setup_started
        checkpoint_count = len(candidates)
        if tuple(candidate.seed for candidate in candidates) != (17, 29, 43, 71, 113):
            raise ValueError("M1 checkpoint panel differs from frozen five seeds")
        for item, row in zip(cohort, rows, strict=True):
            case = item.case
            uniform_result = uniform_results[case.case_id]
            reference = float(row["uniform"]["compliance"])
            design = np.asarray(uniform_result.design_density, dtype=np.float32)
            nx, ny, nz = case.problem.mesh.element_counts
            oracle = design.reshape(1, nz, ny, nx)
            row["methods"].append(
                _attempt(case, "oracle", partial(np.copy, oracle), reference, fallback=True)[0]
            )
            row["methods"].append(
                _attempt(
                    case,
                    "physics_heuristic",
                    partial(_physics_heuristic_raw_density, case),
                    reference,
                    fallback=True,
                )[0]
            )
            if item.scale == "small":
                row["methods"].append(
                    _attempt(
                        case,
                        "nearest_neighbor",
                        partial(_nearest_raw, nearest, case),
                        reference,
                        fallback=True,
                    )[0]
                )
            for candidate in candidates:
                row["methods"].append(
                    _attempt(
                        case,
                        f"learned_seed_{candidate.seed}",
                        partial(_predict, case, candidate),
                        reference,
                        fallback=True,
                    )[0]
                )
            print(
                json.dumps({"panel_completed": case.case_id}),
                file=sys.stderr,
                flush=True,
            )
    return {
        "schema_version": RUNNER_VERSION,
        "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION,
        "cohort_size": len(cohort),
        "uniform_gate_passed": uniform_gate_passed,
        "panel_executed": uniform_gate_passed,
        "index_setup_seconds": index_setup_seconds,
        "index_size_bytes": index_size_bytes,
        "checkpoint_setup_seconds": checkpoint_setup_seconds,
        "checkpoint_count": checkpoint_count,
        "total_wall_seconds": perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "thread_policy": "caller must set all numerical threads to one",
        "solver_ordering": "auto: COLAMD below 5000 free DOFs, MMD_AT_PLUS_A otherwise",
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m1-data-root", type=Path)
    parser.add_argument("--m1-artifact-root", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    cohort = select_cases()
    if not args.execute:
        print(
            json.dumps(
                {
                    "schema_version": RUNNER_VERSION + ".plan",
                    "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION,
                    "cases": [
                        {
                            "case_id": item.case.case_id,
                            "result_id": result_id(item.case.case_id),
                            "scale": item.scale,
                            "direction": item.direction,
                            "volume": item.volume,
                        }
                        for item in cohort
                    ],
                },
                sort_keys=True,
            )
        )
        return
    if args.m1_data_root is None or args.m1_artifact_root is None:
        parser.error("--execute requires both M1 roots")
    print(
        json.dumps(
            run_comparison(cohort, args.m1_data_root, args.m1_artifact_root),
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
