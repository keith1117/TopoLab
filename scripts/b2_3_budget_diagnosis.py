"""Read-only extended trajectories for the eight fixed B2.2 failures."""

from __future__ import annotations

import hashlib
import json
import resource
import subprocess
import sys
from time import perf_counter
from typing import Any

import numpy as np
from b2_2_data_feasibility import HISTORICAL_FAILED_TRAIN, PlannedCase, select_plan
from b2_workload_pilot import _raw_uniform

from topolab.experiment import project_design_density
from topolab.problem import TopologyProblem, TopologyResult, solve_problem
from topolab.simp import PHYSICAL_PLATEAU_SOLVER_VERSION

RUNNER_VERSION = "topolab.b2_3.diagnosis.v1"
LARGE_FAILED_ID = "tlcase-v1-58e145330eb9318f46e047e638b5387aa558d944c370d5ea707e3e6d3d2ba328"
FAILED_IDS = HISTORICAL_FAILED_TRAIN | {LARGE_FAILED_ID}
DIAGNOSTIC_MAX_ITERATIONS = 240


def select_failed_sources() -> tuple[PlannedCase, ...]:
    """Reconstruct exactly the eight reported failures from catalog metadata."""

    selected = tuple(row for row in select_plan() if row.case.case_id in FAILED_IDS)
    if len(selected) != 8 or {row.case.case_id for row in selected} != FAILED_IDS:
        raise ValueError("B2.3 fixed failure identities do not match the B2.2 plan")
    return selected


def _revision() -> str:
    for arguments in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"]):
        if subprocess.run(arguments, check=False).returncode != 0:
            raise RuntimeError("diagnosis requires a clean tracked revision")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _peak_rss_bytes() -> int:
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def _metrics(result: TopologyResult, index: int) -> dict[str, float]:
    history = result.history
    state = history[index - 1]
    recent = history[index - 11 : index]
    max_physical_change = max(
        float(np.max(np.abs(np.asarray(right.physical_density) - left.physical_density)))
        for left, right in zip(recent[:-1], recent[1:], strict=True)
    )
    return {
        "design_change": state.density_change,
        "ten_step_max_physical_change": max_physical_change,
        "ten_step_relative_compliance_improvement": 1.0 - state.compliance / recent[0].compliance,
        "compliance": state.compliance,
        "physical_volume": state.volume_fraction,
    }


def diagnose() -> dict[str, Any]:
    sources = select_failed_sources()
    revision = _revision()
    rows: list[dict[str, Any]] = []
    started = perf_counter()
    for item in sources:
        case_started = perf_counter()
        source = item.case
        payload = source.problem.model_dump(mode="json")
        payload["optimization"]["max_iterations"] = DIAGNOSTIC_MAX_ITERATIONS
        diagnostic_case = TopologyProblem.model_validate(payload)
        projected = project_design_density(source, _raw_uniform(source))
        payload["initial_density"] = tuple(float(value) for value in projected.design_density)
        problem = TopologyProblem.model_validate(payload)
        result = solve_problem(problem, termination_policy="physical_plateau")
        if len(result.history) < 120:
            raise RuntimeError("diagnostic trajectory did not reproduce the 120-update failure")
        rows.append(
            {
                "source_case_id": source.case_id,
                "diagnostic_problem_sha256": hashlib.sha256(
                    json.dumps(
                        diagnostic_case.model_dump(mode="json"),
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest(),
                "scale": item.scale,
                "direction": item.direction,
                "volume": item.volume,
                "converged_by_240": result.converged,
                "iterations": len(result.history),
                "at_120": _metrics(result, 120),
                "terminal": _metrics(result, len(result.history)),
                "seconds": perf_counter() - case_started,
            }
        )
        print(f"diagnosed {len(rows)}/8 {source.case_id}", file=sys.stderr, flush=True)
    return {
        "runner_version": RUNNER_VERSION,
        "source_revision": revision,
        "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION,
        "diagnostic_max_iterations": DIAGNOSTIC_MAX_ITERATIONS,
        "seconds": perf_counter() - started,
        "peak_rss_bytes": _peak_rss_bytes(),
        "rows": rows,
    }


if __name__ == "__main__":
    print(json.dumps(diagnose(), sort_keys=True))
