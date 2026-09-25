"""B2.2 development-only data plan and uniform-label feasibility probe.

Select cases from frozen M2 catalog/split metadata, never from label artifacts.
The optional execution prints aggregate quality metadata, not density fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import resource
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Literal

from b2_workload_pilot import _raw_uniform, scaled_case

from topolab.baselines import validate_refinement_quality
from topolab.experiment import ExperimentCase, project_design_density
from topolab.m2_dataset import assign_m2_case_splits, build_m2_case_catalog
from topolab.problem import TopologyProblem, solve_problem
from topolab.simp import PHYSICAL_PLATEAU_SOLVER_VERSION

PLAN_VERSION = "topolab.b2_2.plan.v1"
LABEL_VERSION = "topolab.b2_2.label.v1"
RUNNER_VERSION = "topolab.b2_2.feasibility.v1"
MAX_PROBE_SECONDS = 1_200.0
MAX_PROBE_RSS_BYTES = 1_073_741_824
EXPECTED_PLAN_SHA256 = "f2f7b27ff396e11fd44845f8c6811e42f86a48587f329b94a2548ca610073dc8"
HISTORICAL_FAILED_TRAIN = frozenset(
    {
        "tlcase-v1-24b747bb3124e5a73377d242f3495ba21eafcae733951d71825959df9cc5db46",
        "tlcase-v1-30e4d8d6e46e95725d887bb2ea1358670b6652087dd247ef1b7c36ce54ddeede",
        "tlcase-v1-7e3a39ed50d58afcaaa5dd1a629cfa50a7ec4cef6188cec0417770c99d2b3f72",
        "tlcase-v1-a94c489359cea9ca6511cff800362deac849af8804fca28d90b889e6b8bb6dfe",
        "tlcase-v1-ae72ada0ed6dc2623ce41a4da79c99ac4a01bc6a2953eef4e5c857616de98ade",
        "tlcase-v1-f9b7ae089d571f57c5b50cb1e78f7f5df8a433ff34d821794282d22fa86ba382",
        "tlcase-v1-fc9cf47d23948ae3be2030824679ed3879ab85f3e7d300cf46878f1ad631b25f",
    }
)


@dataclass(frozen=True)
class PlannedCase:
    case: ExperimentCase
    source_case_id: str
    split: Literal["train", "validation"]
    scale: Literal["small", "large"]
    direction: Literal["y", "z"]
    volume: float

    def metadata(self) -> dict[str, Any]:
        return {
            "case_id": self.case.case_id,
            "source_case_id": self.source_case_id,
            "result_id": result_id(self.case.case_id),
            "split": self.split,
            "scale": self.scale,
            "direction": self.direction,
            "volume": self.volume,
        }


def result_id(case_id: str) -> str:
    """Bind a physical case to the new solver and prospective label contract."""

    payload = json.dumps(
        {
            "case_id": case_id,
            "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION,
            "label_version": LABEL_VERSION,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "tlcase-b22-v1-" + hashlib.sha256(payload.encode()).hexdigest()


def select_plan() -> tuple[PlannedCase, ...]:
    """Freeze 468 small and 54 physically paired large development cases."""

    catalog = build_m2_case_catalog()
    splits = assign_m2_case_splits(catalog)
    strata: defaultdict[
        tuple[Literal["y", "z"], float, Literal["train", "validation"]],
        list[ExperimentCase],
    ] = defaultdict(list)
    rows: list[PlannedCase] = []
    for case in catalog.cases:
        original_split = splits[case.case_id]
        if original_split not in ("train", "validation"):
            continue
        split: Literal["train", "validation"] = (
            "train" if original_split == "train" else "validation"
        )
        original_direction = case.problem.loads[0].direction
        if original_direction not in ("y", "z"):
            raise ValueError("ID development case has an unexpected load direction")
        direction: Literal["y", "z"] = "y" if original_direction == "y" else "z"
        volume = case.problem.optimization.volume_fraction
        rows.append(PlannedCase(case, case.case_id, split, "small", direction, volume))
        strata[(direction, volume, split)].append(case)
    if len(rows) != 468 or len(strata) != 36:
        raise ValueError("M2 development boundary differs from the frozen plan")
    for (direction, volume, split), cases in sorted(strata.items()):
        selected = sorted(cases, key=lambda case: case.case_id)[: 2 if split == "train" else 1]
        if len(selected) != (2 if split == "train" else 1):
            raise ValueError("B2.2 development stratum is incomplete")
        for small in selected:
            rows.append(
                PlannedCase(scaled_case(small), small.case_id, split, "large", direction, volume)
            )
    ordered = tuple(sorted(rows, key=lambda row: (row.scale, row.split, row.case.case_id)))
    if len(ordered) != 522 or len({row.case.case_id for row in ordered}) != 522:
        raise ValueError("B2.2 plan must contain 522 distinct cases")
    return ordered


def select_sentinel(plan: tuple[PlannedCase, ...]) -> tuple[PlannedCase, ...]:
    """Include old train failures and one case per scale/split/ID stratum."""

    chosen: set[str] = set(HISTORICAL_FAILED_TRAIN)
    train_ids = {row.case.case_id for row in plan if row.scale == "small" and row.split == "train"}
    if not HISTORICAL_FAILED_TRAIN <= train_ids:
        raise ValueError("historical failed training cases left the development set")
    strata: defaultdict[tuple[str, str, float, str], list[PlannedCase]] = defaultdict(list)
    for row in plan:
        if row.scale == "small" and row.split == "train":
            continue
        strata[(row.scale, row.direction, row.volume, row.split)].append(row)
    for key, rows in strata.items():
        if key[0] == "small" and key[3] != "validation":
            raise ValueError("unexpected small sentinel split")
        chosen.add(min(rows, key=lambda row: row.case.case_id).case.case_id)
    sentinel = tuple(row for row in plan if row.case.case_id in chosen)
    if len(sentinel) != 61 or len(chosen) != 61:
        raise ValueError("B2.2 sentinel must contain exactly 61 cases")
    return sentinel


def plan_payload(plan: tuple[PlannedCase, ...]) -> dict[str, Any]:
    rows = [row.metadata() for row in plan]
    identity = {
        "plan_version": PLAN_VERSION,
        "label_version": LABEL_VERSION,
        "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION,
        "cases": rows,
    }
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    return {
        **identity,
        "plan_sha256": digest,
        "sentinel_case_ids": [row.case.case_id for row in select_sentinel(plan)],
        "counts": {
            f"{scale}_{split}": count
            for (scale, split), count in sorted(
                Counter((row.scale, row.split) for row in plan).items()
            )
        },
    }


def probe_gate(rows: list[dict[str, Any]], elapsed: float, peak_rss: int) -> bool:
    return (
        len(rows) == 61
        and all(row["quality_passed"] for row in rows)
        and elapsed <= MAX_PROBE_SECONDS
        and peak_rss <= MAX_PROBE_RSS_BYTES
    )


def _peak_rss_bytes() -> int:
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return raw if sys.platform == "darwin" else raw * 1024


def _committed_revision() -> str:
    if subprocess.run(["git", "diff", "--quiet"], check=False).returncode != 0:
        raise RuntimeError("probe requires a clean tracked worktree")
    if subprocess.run(["git", "diff", "--cached", "--quiet"], check=False).returncode != 0:
        raise RuntimeError("probe requires a clean index")
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def run_probe(sentinel: tuple[PlannedCase, ...]) -> dict[str, Any]:
    revision = _committed_revision()
    started = perf_counter()
    rows: list[dict[str, Any]] = []
    for item in sentinel:
        if perf_counter() - started > MAX_PROBE_SECONDS:
            break
        case = item.case
        case_started = perf_counter()
        outcome: dict[str, Any] = item.metadata()
        try:
            projected = project_design_density(case, _raw_uniform(case))
            payload = case.problem.model_dump(mode="json")
            payload["initial_density"] = tuple(float(v) for v in projected.design_density)
            problem = TopologyProblem.model_validate(payload)
            result = solve_problem(problem, termination_policy="physical_plateau")
            metrics = validate_refinement_quality(case, result, None)
            outcome.update(
                {
                    "quality_passed": True,
                    "iterations": metrics.iterations,
                    "compliance": metrics.final_compliance,
                    "physical_volume_error": metrics.physical_volume_error,
                    "stop_reason": (
                        "design_max"
                        if result.history[-1].density_change
                        <= case.problem.optimization.convergence_tolerance
                        else "physical_plateau"
                    ),
                }
            )
        except (ValueError, RuntimeError, ArithmeticError) as error:
            outcome.update({"quality_passed": False, "failure": str(error)})
        outcome["seconds"] = perf_counter() - case_started
        rows.append(outcome)
        print(f"probe {len(rows)}/{len(sentinel)} {case.case_id}", file=sys.stderr, flush=True)
    elapsed = perf_counter() - started
    peak_rss = _peak_rss_bytes()
    return {
        "runner_version": RUNNER_VERSION,
        "source_revision": revision,
        "plan_sha256": EXPECTED_PLAN_SHA256,
        "solver_policy": PHYSICAL_PLATEAU_SOLVER_VERSION,
        "seconds": elapsed,
        "peak_rss_bytes": peak_rss,
        "probe_gate_passed": probe_gate(rows, elapsed, peak_rss),
        "rows": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan = select_plan()
    payload = plan_payload(plan)
    if EXPECTED_PLAN_SHA256 and payload["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise RuntimeError("B2.2 plan differs from the frozen identity")
    if args.execute:
        if not EXPECTED_PLAN_SHA256:
            raise RuntimeError("B2.2 plan identity has not been frozen")
        output = run_probe(select_sentinel(plan))
        print(json.dumps(output, sort_keys=True))
        if not output["probe_gate_passed"]:
            raise SystemExit(1)
    else:
        print(json.dumps(payload, sort_keys=True))


if __name__ == "__main__":
    main()
