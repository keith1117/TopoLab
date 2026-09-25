"""Read-only B2 pilot on development-exposed cantilever case definitions.

The oracle uses a just-computed uniform result and is not deployable. No M2
label artifact or held-out result is opened; all candidate outcomes are printed
to stdout for an external, untracked validation report.
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
from ml_feasibility_probe import select_development_cases
from numpy.typing import NDArray

import topolab.simp as simp
from topolab.baselines import (
    NearestNeighborIndex,
    _physics_heuristic_raw_density,
    build_nearest_neighbor_index,
    solve_case_with_initial_density,
    validate_refinement_quality,
)
from topolab.evaluation_cli import production_selection_references
from topolab.experiment import ExperimentCase, project_design_density
from topolab.learned_evaluation import M1LearnedCandidate, load_m1_candidate
from topolab.problem import TopologyProblem, TopologyResult
from topolab.training_cli import load_frozen_m1_materialization

INDEX_SHA256 = "c1374735bc80ace561f99a6e03497ad2dce3e08c1fb600a4e1d938c73383fd7f"
VOLUMES = (0.2, 0.45, 0.6)
DIRECTIONS = ("y", "z")
SMALL = (12, 6, 3)
LARGE = (24, 12, 6)


@dataclass(frozen=True)
class PilotCase:
    source_case_id: str
    case: ExperimentCase
    scale: str
    direction: str
    volume: float


def select_pilot_cases(index: dict[str, Any]) -> tuple[PilotCase, ...]:
    """Choose one prior validation case per fixed stratum and its scaled peer."""

    validation, _failed_train = select_development_cases(index)
    grouped: dict[tuple[str, float], list[ExperimentCase]] = {}
    for item in validation:
        case = item.case
        key = (str(case.problem.loads[0].direction), case.problem.optimization.volume_fraction)
        grouped.setdefault(key, []).append(case)
    cohort: list[PilotCase] = []
    for volume in VOLUMES:
        for direction in DIRECTIONS:
            options = grouped.get((direction, volume), [])
            if len(options) != 2:
                raise ValueError("unexpected M2 validation stratum")
            small = min(options, key=lambda case: case.case_id)
            cohort.append(PilotCase(small.case_id, small, "small", direction, volume))
            cohort.append(
                PilotCase(
                    small.case_id,
                    scaled_case(small),
                    "large",
                    direction,
                    volume,
                )
            )
    if len({item.case.case_id for item in cohort}) != 12:
        raise ValueError("pilot cases must have distinct identities")
    return tuple(cohort)


def scaled_case(small: ExperimentCase) -> ExperimentCase:
    """Refine the same physical domain and map the point load to the same location."""

    problem = small.problem
    if problem.mesh.element_counts != SMALL or len(problem.loads) != 1:
        raise ValueError("pilot source must use the M2 small-mesh case")
    load = problem.loads[0]
    if load.kind != "point":
        raise ValueError("pilot source must have one point load")
    nx, ny, _nz = SMALL
    plane = load.node // (nx + 1)
    if load.node % (nx + 1) != nx:
        raise ValueError("pilot load must be on x=max")
    y_index = plane % (ny + 1)
    z_index = plane // (ny + 1)
    big_nx, big_ny, _big_nz = LARGE
    big_node = big_nx + (big_nx + 1) * (
        2 * y_index + (big_ny + 1) * (2 * z_index)
    )
    payload = problem.model_dump(mode="json")
    payload["mesh"]["element_counts"] = LARGE
    payload["loads"][0]["node"] = big_node
    return ExperimentCase.from_problem(TopologyProblem.model_validate(payload))


def _raw_uniform(case: ExperimentCase) -> NDArray[np.float32]:
    nx, ny, nz = case.problem.mesh.element_counts
    return np.full(
        (1, nz, ny, nx), case.problem.optimization.volume_fraction, dtype=np.float32
    )


def _refine(
    case: ExperimentCase, raw: NDArray[np.float32]
) -> tuple[TopologyResult, float, float, float, int]:
    projection_started = perf_counter()
    projected = project_design_density(case, raw)
    projection_seconds = perf_counter() - projection_started
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
        result = solve_case_with_initial_density(case, projected.design_density)
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
    started = perf_counter()
    raw = setup()
    setup_seconds = perf_counter() - started
    result, projection, refinement, fem, fem_calls = _refine(case, raw)
    passed = True
    failure = None
    try:
        validate_refinement_quality(case, result, uniform_compliance)
    except (ValueError, RuntimeError) as error:
        passed = False
        failure = type(error).__name__
    fallback_seconds = 0.0
    fallback_fem = 0.0
    if fallback and not passed:
        repeated, fb_projection, fb_refinement, fallback_fem, _fb_calls = _refine(
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
        "fallback_fem_seconds": fallback_fem,
        "charged_seconds": setup_seconds + projection + refinement + fallback_seconds,
        "peak_rss_bytes": _peak_rss_bytes(),
        "quality_audit_excluded": True,
    }, result


def _nearest_raw(
    nearest: NearestNeighborIndex, case: ExperimentCase
) -> NDArray[np.float32]:
    return nearest.query(case).design_density


def _progress(count: int, case_id: str) -> None:
    print(json.dumps({"completed": count, "case_id": case_id}), file=sys.stderr, flush=True)


def _peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def run_pilot(
    cohort: tuple[PilotCase, ...],
    m1_data_root: Path,
    m1_artifact_root: Path,
) -> dict[str, Any]:
    index_started = perf_counter()
    materialization = load_frozen_m1_materialization(m1_data_root)
    nearest: NearestNeighborIndex = build_nearest_neighbor_index(
        m1_data_root, materialization
    )
    index_setup_seconds = perf_counter() - index_started
    checkpoint_started = perf_counter()
    candidates: tuple[M1LearnedCandidate, ...] = tuple(
        load_m1_candidate(m1_artifact_root, reference)
        for reference in production_selection_references(m1_artifact_root)
    )
    checkpoint_setup_seconds = perf_counter() - checkpoint_started
    rows: list[dict[str, Any]] = []
    started = perf_counter()
    for item in cohort:
        case = item.case
        uniform, uniform_result = _attempt(
            case, "uniform", partial(_raw_uniform, case), None, fallback=False
        )
        row: dict[str, Any] = {
            "case_id": case.case_id,
            "source_case_id": item.source_case_id,
            "element_counts": case.problem.mesh.element_counts,
            "scale": item.scale,
            "direction": item.direction,
            "volume": item.volume,
            "uniform": uniform,
            "methods": [],
        }
        if not uniform["passed"]:
            row["uniform_failure"] = True
            rows.append(row)
            _progress(len(rows), case.case_id)
            continue
        reference = float(uniform["compliance"])
        design = np.asarray(
            uniform_result.design_density,
            dtype=np.float32,
        ).reshape(_raw_uniform(case).shape)
        row["methods"].append(
            _attempt(case, "oracle", partial(np.copy, design), reference, fallback=True)[0]
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
        rows.append(row)
        _progress(len(rows), case.case_id)
    return {
        "schema_version": "topolab.b2.pilot.v1",
        "cohort_size": len(cohort),
        "solver_ordering": "auto: COLAMD below 5000 free DOFs, MMD_AT_PLUS_A otherwise",
        "thread_policy": "caller must set all numerical threads to one",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "total_wall_seconds": perf_counter() - started,
        "index_setup_seconds": index_setup_seconds,
        "index_size_bytes": nearest.stored_size_bytes,
        "checkpoint_setup_seconds": checkpoint_setup_seconds,
        "checkpoint_count": len(candidates),
        "peak_rss_bytes": _peak_rss_bytes(),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2-index", type=Path, required=True)
    parser.add_argument("--m1-data-root", type=Path)
    parser.add_argument("--m1-artifact-root", type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    contents = args.m2_index.read_bytes()
    if hashlib.sha256(contents).hexdigest() != INDEX_SHA256:
        raise ValueError("M2 index checksum mismatch")
    cohort = select_pilot_cases(json.loads(contents))
    if not args.execute:
        print(
            json.dumps(
                {"schema_version": "topolab.b2.pilot-plan.v1", "cases": [
                    {"case_id": item.case.case_id, "source_case_id": item.source_case_id,
                     "scale": item.scale, "direction": item.direction, "volume": item.volume}
                    for item in cohort
                ]}, sort_keys=True
            )
        )
        return
    if args.m1_data_root is None or args.m1_artifact_root is None:
        parser.error("--execute requires both M1 roots")
    print(json.dumps(run_pilot(cohort, args.m1_data_root, args.m1_artifact_root), sort_keys=True))


if __name__ == "__main__":
    main()
