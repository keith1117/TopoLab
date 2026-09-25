"""Read-only development probe for attainable M2-label warm-start speedup.

The deliberately impossible oracle initializes SIMP with each validation case's
own converged label. It estimates warm-start viability; it is not a deployable model
or held-out evaluation. Test/OOD label artifacts are never opened.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median
from time import perf_counter
from typing import Any, TypedDict

import numpy as np

from topolab.baselines import solve_case_with_initial_density, validate_refinement_quality
from topolab.experiment import ExperimentCase, project_design_density
from topolab.label_artifacts import LabelArtifactReference, read_label_artifact
from topolab.problem import TopologyResult, solve_problem

INDEX_SHA256 = "c1374735bc80ace561f99a6e03497ad2dce3e08c1fb600a4e1d938c73383fd7f"
EXPECTED_VALIDATION = 36
EXPECTED_FAILED_TRAIN = 7


@dataclass(frozen=True)
class ValidationCase:
    case: ExperimentCase
    label: LabelArtifactReference


class ValidationRow(TypedDict):
    direction: str
    volume: float
    passed: bool
    uniform_iterations: int
    oracle_iterations: int
    oracle_compliance_ratio: float
    oracle_time_ratio: float
    oracle_without_fallback_ratio: float
    oracle_projection_fraction: float
    uniform_time_seconds: float
    oracle_time_seconds: float
    fallback_seconds: float
    quality_checked_iterations: int | None


class FailedTrainRow(TypedDict):
    direction: str
    volume: float
    terminal_change: float
    two_step_difference: float
    one_step_difference: float
    last_ten_changes_decrease: bool
    last_ten_compliances_decrease: bool


def select_development_cases(
    index: dict[str, Any],
) -> tuple[list[ValidationCase], list[ExperimentCase]]:
    """Select only validation labels and failed training metadata."""

    if index.get("state") != "complete":
        raise ValueError("M2 index must be complete")
    manifest = index["manifest"]
    if index.get("manifest_sha256") != (
        "99b63e4b49d29764b033b8d8af6664801454d6e5bcf34df68d9e6471a71ba33f"
    ):
        raise ValueError("unexpected M2 manifest")
    samples = {sample["case"]["case_id"]: sample for sample in manifest["samples"]}
    validation: list[ValidationCase] = []
    failed_train: list[ExperimentCase] = []
    for entry in index["entries"]:
        split = entry["split"]
        if split not in {"validation", "train"}:
            continue
        sample = samples[entry["case_id"]]
        if sample["split"] != split:
            raise ValueError("entry split differs from manifest")
        if split == "validation":
            if entry["status"] != "succeeded":
                raise ValueError("validation label is unavailable")
            validation.append(
                ValidationCase(
                    case=ExperimentCase.model_validate(sample["case"]),
                    label=LabelArtifactReference.model_validate(entry["artifact"]),
                )
            )
        elif entry["status"] == "failed":
            failed_train.append(ExperimentCase.model_validate(sample["case"]))
    if len(validation) != EXPECTED_VALIDATION or len(failed_train) != EXPECTED_FAILED_TRAIN:
        raise ValueError("unexpected M2 development cohort size")
    validation.sort(key=lambda item: item.case.case_id)
    failed_train.sort(key=lambda item: item.case_id)
    return validation, failed_train


def _run_start(case: ExperimentCase, raw: np.ndarray) -> tuple[TopologyResult, float, float]:
    projected_started = perf_counter()
    projected = project_design_density(case, raw)
    projection_seconds = perf_counter() - projected_started
    solved_started = perf_counter()
    result = solve_case_with_initial_density(case, projected.design_density)
    solve_seconds = perf_counter() - solved_started
    return result, projection_seconds, solve_seconds


def _uniform_raw(case: ExperimentCase) -> np.ndarray:
    nx, ny, nz = case.problem.mesh.element_counts
    return np.full((1, nz, ny, nx), case.problem.optimization.volume_fraction, dtype=np.float32)


def _read_validation_label(root: Path, item: ValidationCase) -> np.ndarray:
    label = read_label_artifact(root, item.label)
    if label.case != item.case:
        raise ValueError("validation label does not match the M2 manifest")
    return label.design_tensor()


def _validation_probe(items: list[ValidationCase], root: Path) -> dict[str, object]:
    rows: list[ValidationRow] = []
    for index, item in enumerate(items):
        case = item.case
        label_design = _read_validation_label(root, item)
        uniform_raw = _uniform_raw(case)
        # Alternate the solve order to reduce a systematic warm-cache advantage.
        if index % 2:
            oracle, op, os = _run_start(case, label_design)
            uniform, up, us = _run_start(case, uniform_raw)
        else:
            uniform, up, us = _run_start(case, uniform_raw)
            oracle, op, os = _run_start(case, label_design)
        uniform_metrics = validate_refinement_quality(case, uniform, None)
        try:
            oracle_metrics = validate_refinement_quality(
                case, oracle, uniform_metrics.final_compliance
            )
            passed = True
        except (RuntimeError, ValueError):
            oracle_metrics = None
            passed = False
        uniform_time = up + us
        oracle_time = op + os
        # A failed attempt pays for a fresh complete uniform fallback. The label
        # read and quality-audit time are excluded from both methods as diagnostics.
        fallback_seconds = 0.0
        if not passed:
            fallback, fp, fs = _run_start(case, uniform_raw)
            validate_refinement_quality(case, fallback, None)
            fallback_seconds = fp + fs
        rows.append(
            {
                "direction": str(case.problem.loads[0].direction),
                "volume": case.problem.optimization.volume_fraction,
                "passed": passed,
                "uniform_iterations": uniform_metrics.iterations,
                "oracle_iterations": len(oracle.history),
                "oracle_compliance_ratio": oracle.compliance / uniform_metrics.final_compliance,
                "oracle_time_ratio": (oracle_time + fallback_seconds) / uniform_time,
                "oracle_without_fallback_ratio": oracle_time / uniform_time,
                "oracle_projection_fraction": op / uniform_time,
                "uniform_time_seconds": uniform_time,
                "oracle_time_seconds": oracle_time,
                "fallback_seconds": fallback_seconds,
                "quality_checked_iterations": (
                    oracle_metrics.iterations if oracle_metrics is not None else None
                ),
            }
        )
    groups: dict[str, list[ValidationRow]] = defaultdict(list)
    for row in rows:
        groups[f"{row['direction']}:{row['volume']:.2f}"].append(row)
    return {
        "case_count": len(rows),
        "failure_count": sum(not row["passed"] for row in rows),
        "mean_charged_ratio": mean(row["oracle_time_ratio"] for row in rows),
        "median_charged_ratio": median(row["oracle_time_ratio"] for row in rows),
        "mean_unfallbacked_ratio": mean(row["oracle_without_fallback_ratio"] for row in rows),
        "median_uniform_iterations": median(row["uniform_iterations"] for row in rows),
        "median_oracle_iterations": median(row["oracle_iterations"] for row in rows),
        "max_oracle_compliance_ratio": max(row["oracle_compliance_ratio"] for row in rows),
        "by_direction_volume": {
            key: {
                "cases": len(group),
                "failures": sum(not row["passed"] for row in group),
                "mean_charged_ratio": mean(row["oracle_time_ratio"] for row in group),
                "median_oracle_iterations": median(row["oracle_iterations"] for row in group),
            }
            for key, group in sorted(groups.items())
        },
    }


def _failed_train_probe(cases: list[ExperimentCase]) -> dict[str, object]:
    rows: list[FailedTrainRow] = []
    for case in cases:
        result = solve_problem(case.problem)
        if result.converged or len(result.history) != case.problem.optimization.max_iterations:
            raise ValueError("M2 failed training case changed termination behavior")
        tail = result.history[-3:]
        latest = np.asarray(tail[-1].design_density, dtype=np.float64)
        prior = np.asarray(tail[-2].design_density, dtype=np.float64)
        two_back = np.asarray(tail[-3].design_density, dtype=np.float64)
        rows.append(
            {
                "direction": str(case.problem.loads[0].direction),
                "volume": case.problem.optimization.volume_fraction,
                "terminal_change": tail[-1].density_change,
                "two_step_difference": float(np.max(np.abs(latest - two_back))),
                "one_step_difference": float(np.max(np.abs(latest - prior))),
                "last_ten_changes_decrease": all(
                    earlier.density_change > later.density_change
                    for earlier, later in zip(
                        result.history[-10:-1], result.history[-9:], strict=True
                    )
                ),
                "last_ten_compliances_decrease": all(
                    earlier.compliance > later.compliance
                    for earlier, later in zip(
                        result.history[-10:-1], result.history[-9:], strict=True
                    )
                ),
            }
        )
    return {
        "case_count": len(rows),
        "min_terminal_change": min(row["terminal_change"] for row in rows),
        "max_terminal_change": max(row["terminal_change"] for row in rows),
        "max_two_step_difference": max(row["two_step_difference"] for row in rows),
        "min_one_step_difference": min(row["one_step_difference"] for row in rows),
        "decreasing_change_tails": sum(row["last_ten_changes_decrease"] for row in rows),
        "decreasing_compliance_tails": sum(
            row["last_ten_compliances_decrease"] for row in rows
        ),
        "all_y_at_045": all(row["direction"] == "y" and row["volume"] == 0.45 for row in rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--artifact-root", required=True, type=Path)
    args = parser.parse_args()
    index_bytes = args.index.read_bytes()
    if hashlib.sha256(index_bytes).hexdigest() != INDEX_SHA256:
        raise ValueError("M2 index checksum mismatch")
    validation, failed_train = select_development_cases(json.loads(index_bytes))
    summary = {
        "probe_version": "topolab.ml-feasibility-probe.v1",
        "source_index_sha256": INDEX_SHA256,
        "validation_oracle": _validation_probe(validation, args.artifact_root),
        "failed_training_cases": _failed_train_probe(failed_train),
    }
    print(json.dumps(summary, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
