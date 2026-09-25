"""B2.3 versioned 240-update development sentinel and prior-result guard."""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from b2_2_data_feasibility import (
    EXPECTED_PLAN_SHA256 as B22_PLAN_SHA256,
)
from b2_2_data_feasibility import (
    PlannedCase,
    select_plan,
    select_sentinel,
)
from b2_2_data_feasibility import (
    result_id as b22_result_id,
)
from b2_workload_pilot import _raw_uniform

from topolab.baselines import validate_refinement_quality
from topolab.experiment import ExperimentCase, project_design_density
from topolab.problem import TopologyProblem, TopologyResult, solve_problem
from topolab.simp import PHYSICAL_PLATEAU_SOLVER_VERSION

PLAN_VERSION = "topolab.b2_3.budget240.plan.v1"
LABEL_VERSION = "topolab.b2_3.label.v1"
RUNNER_VERSION = "topolab.b2_3.budget_sentinel.v1"
MAX_ITERATIONS = 240
MAX_SECONDS = 1_500.0
MAX_RSS_BYTES = 1_073_741_824
B22_PROBE_SHA256 = "45d29dd6568da34fd097a522aff072d08afc121dd98a5f784411d79db7004b78"
B22_RUNNER_REVISION = "d8c2e55d6fbc795c01b80e40b7b1cf9600153b97"
EXPECTED_PLAN_SHA256 = "45baa0f74c74fca3ea3d7594b7576f1150a6dc950b23daafdab5acc8e1f5c289"


@dataclass(frozen=True)
class BudgetCase:
    source: PlannedCase
    case: ExperimentCase

    def metadata(self) -> dict[str, Any]:
        return {
            "b2_2_source_case_id": self.source.case.case_id,
            "new_case_id": self.case.case_id,
            "result_id": result_id(self.source.case.case_id, self.case.case_id),
            "source_split": self.source.split,
            "scale": self.source.scale,
            "direction": self.source.direction,
            "volume": self.source.volume,
        }


def result_id(source_case_id: str, new_case_id: str) -> str:
    payload = json.dumps(
        {
            "b2_2_source_case_id": source_case_id,
            "new_case_id": new_case_id,
            "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION,
            "label_version": LABEL_VERSION,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "tlcase-b23-v1-" + hashlib.sha256(payload.encode()).hexdigest()


def select_cases() -> tuple[BudgetCase, ...]:
    sources = select_sentinel(select_plan())
    rows: list[BudgetCase] = []
    for source in sources:
        payload = source.case.problem.model_dump(mode="json")
        if payload["optimization"]["max_iterations"] != 120:
            raise ValueError("B2.2 source iteration budget changed")
        payload["optimization"]["max_iterations"] = MAX_ITERATIONS
        new_case = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
        if new_case.case_id == source.case.case_id:
            raise ValueError("the B2.3 budget must change the physical case identity")
        rows.append(BudgetCase(source, new_case))
    if len(rows) != 61 or len({row.case.case_id for row in rows}) != 61:
        raise ValueError("B2.3 sentinel must contain exactly 61 distinct new cases")
    return tuple(rows)


def plan_payload(cases: tuple[BudgetCase, ...]) -> dict[str, Any]:
    identity = {
        "plan_version": PLAN_VERSION,
        "label_version": LABEL_VERSION,
        "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION,
        "max_iterations": MAX_ITERATIONS,
        "b2_2_plan_sha256": B22_PLAN_SHA256,
        "cases": [item.metadata() for item in cases],
    }
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return {**identity, "plan_sha256": hashlib.sha256(canonical.encode()).hexdigest()}


def read_prior_probe(path: Path, cases: tuple[BudgetCase, ...]) -> dict[str, dict[str, Any]]:
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != B22_PROBE_SHA256:
        raise ValueError("B2.2 prior probe does not match its reported checksum")
    document = json.loads(raw)
    if (
        document["source_revision"] != B22_RUNNER_REVISION
        or document["plan_sha256"] != B22_PLAN_SHA256
        or document["solver_policy"] != PHYSICAL_PLATEAU_SOLVER_VERSION
    ):
        raise ValueError("B2.2 prior probe has the wrong revision or policy")
    rows = document["rows"]
    if len(rows) != 61 or [row["case_id"] for row in rows] != [
        item.source.case.case_id for item in cases
    ]:
        raise ValueError("B2.2 prior probe does not contain the fixed 61-case order")
    if sum(bool(row["quality_passed"]) for row in rows) != 53:
        raise ValueError("B2.2 prior probe must preserve 53 accepted sources")
    for row in rows:
        if row["result_id"] != b22_result_id(row["case_id"]):
            raise ValueError("B2.2 prior result identity changed")
    return {str(row["case_id"]): row for row in rows}


def _revision() -> str:
    for arguments in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"]):
        if subprocess.run(arguments, check=False).returncode != 0:
            raise RuntimeError("sentinel execution requires a clean tracked revision")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def _peak_rss_bytes() -> int:
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def _validate_final_state(result: TopologyResult) -> None:
    if not result.history:
        raise ValueError("solver returned no completed update")
    last = result.history[-1]
    if (
        last.iteration != len(result.history)
        or not np.array_equal(result.design_density, last.design_density)
        or not np.array_equal(result.physical_density, last.physical_density)
        or result.compliance != last.compliance
        or not np.isclose(
            last.volume_fraction,
            np.mean(result.physical_density),
            rtol=0.0,
            atol=1e-12,
        )
    ):
        raise ValueError("terminal state and final history row differ")


def gate_passed(rows: list[dict[str, Any]], elapsed: float, peak_rss: int) -> bool:
    return (
        len(rows) == 61
        and all(row["quality_passed"] for row in rows)
        and elapsed <= MAX_SECONDS
        and peak_rss <= MAX_RSS_BYTES
    )


def run_sentinel(cases: tuple[BudgetCase, ...], prior: dict[str, dict[str, Any]]) -> dict[str, Any]:
    revision = _revision()
    started = perf_counter()
    rows: list[dict[str, Any]] = []
    for item in cases:
        if perf_counter() - started > MAX_SECONDS:
            break
        case_started = perf_counter()
        outcome: dict[str, Any] = item.metadata()
        previous = prior[item.source.case.case_id]
        try:
            projected = project_design_density(item.case, _raw_uniform(item.case))
            payload = item.case.problem.model_dump(mode="json")
            payload["initial_density"] = tuple(float(value) for value in projected.design_density)
            result = solve_problem(
                TopologyProblem.model_validate(payload), termination_policy="physical_plateau"
            )
            _validate_final_state(result)
            metrics = validate_refinement_quality(item.case, result, None)
            prior_guard = True
            if previous["quality_passed"]:
                relative = abs(metrics.final_compliance - float(previous["compliance"])) / float(
                    previous["compliance"]
                )
                prior_guard = metrics.iterations == previous["iterations"] and relative <= 1e-10
                if not prior_guard:
                    raise ValueError("previously accepted source changed under budget extension")
            outcome.update(
                {
                    "quality_passed": True,
                    "prior_guard_passed": prior_guard,
                    "iterations": metrics.iterations,
                    "compliance": metrics.final_compliance,
                    "physical_volume_error": metrics.physical_volume_error,
                    "stop_reason": (
                        "design_max"
                        if result.history[-1].density_change
                        <= item.case.problem.optimization.convergence_tolerance
                        else "physical_plateau"
                    ),
                }
            )
        except (ValueError, RuntimeError, ArithmeticError) as error:
            outcome.update({"quality_passed": False, "failure": str(error)})
        outcome["seconds"] = perf_counter() - case_started
        rows.append(outcome)
        print(f"sentinel {len(rows)}/{len(cases)} {item.case.case_id}", file=sys.stderr, flush=True)
    elapsed = perf_counter() - started
    peak_rss = _peak_rss_bytes()
    return {
        "runner_version": RUNNER_VERSION,
        "source_revision": revision,
        "plan_sha256": EXPECTED_PLAN_SHA256,
        "prior_probe_sha256": B22_PROBE_SHA256,
        "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION,
        "seconds": elapsed,
        "peak_rss_bytes": peak_rss,
        "sentinel_gate_passed": gate_passed(rows, elapsed, peak_rss),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--b22-probe", type=Path)
    args = parser.parse_args()
    cases = select_cases()
    payload = plan_payload(cases)
    if EXPECTED_PLAN_SHA256 and payload["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise RuntimeError("B2.3 candidate plan differs from its frozen identity")
    if args.execute:
        if not EXPECTED_PLAN_SHA256 or args.b22_probe is None:
            parser.error("--execute requires the frozen plan and --b22-probe")
        prior = read_prior_probe(args.b22_probe, cases)
        output = run_sentinel(cases, prior)
        print(json.dumps(output, sort_keys=True))
        if not output["sentinel_gate_passed"]:
            raise SystemExit(1)
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
