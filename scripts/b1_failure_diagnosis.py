"""Read-only B1 diagnosis over exposed M2 metadata and validation labels.

The 240-iteration extension is diagnostic only. It never creates a label, changes
the frozen M2 outcome, or reads M2 test/OOD label artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import median
from typing import Any, Literal

import numpy as np
import torch
from numpy.typing import NDArray

from topolab.baselines import solve_case_with_initial_density, validate_refinement_quality
from topolab.evaluation_cli import production_selection_references
from topolab.experiment import ExperimentCase, encode_case, project_design_density
from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.label_artifacts import LabelArtifactReference, read_label_artifact
from topolab.learned_evaluation import M1LearnedCandidate, load_m1_candidate
from topolab.mesh import Hex8Mesh, generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport, PointLoad
from topolab.problem import (
    FaceLoadDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
    solve_problem,
)
from topolab.simp import apply_density_filter, build_density_filter, evaluate_compliance

M2_INDEX_SHA256 = "c1374735bc80ace561f99a6e03497ad2dce3e08c1fb600a4e1d938c73383fd7f"
M2_MANIFEST_SHA256 = "99b63e4b49d29764b033b8d8af6664801454d6e5bcf34df68d9e6471a71ba33f"
EXPECTED_VALIDATION = 36
EXPECTED_FAILURE_SPLITS = {"train": 7, "test": 1, "ood": 2}
FROZEN_BUDGET = 120
DIAGNOSTIC_BUDGET = 240


@dataclass(frozen=True)
class ValidationCase:
    case: ExperimentCase
    label: LabelArtifactReference


@dataclass(frozen=True)
class FailedCase:
    case: ExperimentCase
    split: Literal["train", "test", "ood"]


@dataclass(frozen=True)
class ConvergenceRow:
    case_id: str
    split: str
    direction: str
    volume: float
    change_at_120: float
    compliance_at_120: float
    last_ten_changes_decrease: bool
    last_ten_compliances_decrease: bool
    update_cosine_at_120: float
    two_step_difference_at_120: float
    max_independent_volume_error: float
    max_recorded_volume_disagreement: float
    compliance_resolve_relative_error_at_120: float
    converged_by_240: bool
    diagnostic_iterations: int
    diagnostic_terminal_change: float


@dataclass(frozen=True)
class LearnedRow:
    case_id: str
    seed: int
    direction: str
    volume: float
    raw_mse: float
    projected_mse: float
    raw_volume_error: float
    projected_volume_error: float
    projected_initial_compliance_ratio: float
    projected_initial_compliance_over_oracle: float
    first_refinement_compliance_ratio: float
    tenth_refinement_compliance_ratio: float
    final_compliance_ratio: float
    terminal_density_change: float
    uniform_iterations: int
    oracle_iterations: int
    learned_iterations: int
    converged: bool
    quality_passed: bool


def select_diagnostic_cases(
    index: dict[str, Any],
) -> tuple[list[ValidationCase], list[FailedCase]]:
    """Read validation label references and failed-case metadata only."""

    if index.get("state") != "complete":
        raise ValueError("M2 index must be complete")
    if index.get("manifest_sha256") != M2_MANIFEST_SHA256:
        raise ValueError("unexpected M2 manifest")
    samples = {sample["case"]["case_id"]: sample for sample in index["manifest"]["samples"]}
    validation: list[ValidationCase] = []
    failures: list[FailedCase] = []
    for entry in index["entries"]:
        split = entry["split"]
        status = entry["status"]
        if split == "validation":
            if status != "succeeded":
                raise ValueError("validation label is unavailable")
            sample = samples[entry["case_id"]]
            if sample["split"] != split:
                raise ValueError("entry split differs from manifest")
            validation.append(
                ValidationCase(
                    case=ExperimentCase.model_validate(sample["case"]),
                    label=LabelArtifactReference.model_validate(entry["artifact"]),
                )
            )
        elif status == "failed":
            if split not in EXPECTED_FAILURE_SPLITS:
                raise ValueError("unexpected failed partition")
            sample = samples[entry["case_id"]]
            if sample["split"] != split:
                raise ValueError("entry split differs from manifest")
            failures.append(
                FailedCase(
                    case=ExperimentCase.model_validate(sample["case"]),
                    split=split,
                )
            )
        # Successful train/test/OOD entries, including their artifact references,
        # are deliberately ignored by this development-only diagnostic.
    if len(validation) != EXPECTED_VALIDATION:
        raise ValueError("unexpected validation cohort size")
    if dict(Counter(item.split for item in failures)) != EXPECTED_FAILURE_SPLITS:
        raise ValueError("unexpected failed-case split counts")
    validation.sort(key=lambda item: item.case.case_id)
    failures.sort(key=lambda item: item.case.case_id)
    return validation, failures


def _case_system(
    case: ExperimentCase,
) -> tuple[Hex8Mesh, NDArray[np.float64], NDArray[np.int64]]:
    problem = case.problem
    mesh = generate_structured_hex8(*problem.mesh.element_counts, lengths=problem.mesh.lengths)
    constrained = build_constrained_dofs(
        mesh,
        [
            FixedFaceSupport(
                axis=support.axis,
                side=support.side,
                directions=support.directions,
            )
            for support in problem.supports
        ],
    )
    core_loads: list[PointLoad | FaceLoad] = []
    for load in problem.loads:
        if isinstance(load, PointLoadDefinition):
            core_loads.append(
                PointLoad(node=load.node, direction=load.direction, magnitude=load.magnitude)
            )
        elif isinstance(load, FaceLoadDefinition):
            core_loads.append(
                FaceLoad(
                    axis=load.axis,
                    side=load.side,
                    direction=load.direction,
                    total=load.total,
                )
            )
    loads = build_load_vector(mesh, core_loads)
    return mesh, loads, constrained


def _compliance(
    case: ExperimentCase,
    system: tuple[Hex8Mesh, NDArray[np.float64], NDArray[np.int64]],
    physical: NDArray[np.float64],
) -> float:
    mesh, loads, constrained = system
    material = case.problem.material
    return evaluate_compliance(
        mesh,
        physical,
        loads,
        constrained,
        solid_modulus=material.solid_modulus,
        minimum_modulus=material.minimum_modulus,
        poisson_ratio=material.poisson_ratio,
        penalty=case.problem.optimization.penalty,
    ).compliance


def diagnose_convergence(failures: list[FailedCase]) -> list[ConvergenceRow]:
    """Extend each failed run in memory while preserving its frozen 120-step state."""

    rows: list[ConvergenceRow] = []
    for item in failures:
        case = item.case
        original = case.problem.optimization
        if original.max_iterations != FROZEN_BUDGET:
            raise ValueError("failed case does not use the frozen 120-step budget")
        extended_settings = OptimizationDefinition.model_validate(
            {**original.model_dump(), "max_iterations": DIAGNOSTIC_BUDGET}
        )
        extended_problem = TopologyProblem.model_validate(
            {**case.problem.model_dump(), "optimization": extended_settings.model_dump()}
        )
        result = solve_problem(extended_problem)
        if len(result.history) <= FROZEN_BUDGET:
            raise ValueError("failed M2 case now converges within the original budget")
        frozen_history = result.history[:FROZEN_BUDGET]
        terminal = frozen_history[-1]
        if terminal.density_change <= original.convergence_tolerance:
            raise ValueError("original failed outcome no longer reproduces")
        system = _case_system(case)
        mesh = system[0]
        density_filter = build_density_filter(mesh, original.filter_radius)
        volume_errors: list[float] = []
        recorded_disagreements: list[float] = []
        for state in (frozen_history[0], frozen_history[59], terminal, result.history[-1]):
            physical = apply_density_filter(
                density_filter, np.asarray(state.design_density, dtype=np.float64)
            )
            independent_volume = float(np.mean(physical))
            volume_errors.append(abs(independent_volume - original.volume_fraction))
            recorded_disagreements.append(abs(independent_volume - state.volume_fraction))
        last = np.asarray(terminal.design_density, dtype=np.float64)
        previous = np.asarray(frozen_history[-2].design_density, dtype=np.float64)
        two_back = np.asarray(frozen_history[-3].design_density, dtype=np.float64)
        update = last - previous
        preceding_update = previous - two_back
        cosine = float(
            np.dot(update, preceding_update)
            / (np.linalg.norm(update) * np.linalg.norm(preceding_update))
        )
        resolved_compliance = _compliance(
            case,
            system,
            np.asarray(terminal.physical_density, dtype=np.float64),
        )
        rows.append(
            ConvergenceRow(
                case_id=case.case_id,
                split=item.split,
                direction=str(case.problem.loads[0].direction),
                volume=original.volume_fraction,
                change_at_120=terminal.density_change,
                compliance_at_120=terminal.compliance,
                last_ten_changes_decrease=all(
                    a.density_change > b.density_change
                    for a, b in zip(frozen_history[-10:-1], frozen_history[-9:], strict=True)
                ),
                last_ten_compliances_decrease=all(
                    a.compliance > b.compliance
                    for a, b in zip(frozen_history[-10:-1], frozen_history[-9:], strict=True)
                ),
                update_cosine_at_120=cosine,
                two_step_difference_at_120=float(np.max(np.abs(last - two_back))),
                max_independent_volume_error=max(volume_errors),
                max_recorded_volume_disagreement=max(recorded_disagreements),
                compliance_resolve_relative_error_at_120=(
                    abs(resolved_compliance - terminal.compliance) / terminal.compliance
                ),
                converged_by_240=result.converged,
                diagnostic_iterations=len(result.history),
                diagnostic_terminal_change=result.history[-1].density_change,
            )
        )
    return rows


def _predict(case: ExperimentCase, candidate: M1LearnedCandidate) -> NDArray[np.float32]:
    inputs = torch.from_numpy(encode_case(case).input_tensor).unsqueeze(0)
    candidate.model.eval()
    with torch.inference_mode():
        output = candidate.model(inputs)
    nx, ny, nz = case.problem.mesh.element_counts
    if output.shape != (1, 1, nz, ny, nx):
        raise ValueError("M1 prediction shape changed")
    if output.device.type != "cpu" or output.dtype != torch.float32:
        raise ValueError("M1 prediction device or dtype changed")
    if not torch.isfinite(output).all() or torch.any(output < 0) or torch.any(output > 1):
        raise ValueError("M1 prediction is invalid")
    return np.asarray(output.squeeze(0).numpy(), dtype=np.float32).copy()


def diagnose_learned(
    validation: list[ValidationCase],
    label_root: Path,
    artifact_root: Path,
) -> list[LearnedRow]:
    """Replay all fixed M1 seeds against development-only M2 validation cases."""

    candidates = tuple(
        load_m1_candidate(artifact_root, reference)
        for reference in production_selection_references(artifact_root)
    )
    rows: list[LearnedRow] = []
    for item in validation:
        case = item.case
        label = read_label_artifact(label_root, item.label)
        if label.case != case:
            raise ValueError("validation label does not match its case")
        target = label.design_tensor().astype(np.float64).reshape(-1)
        uniform = solve_problem(case.problem)
        uniform_metrics = validate_refinement_quality(case, uniform, None)
        uniform_raw = np.full(
            label.design_tensor().shape,
            case.problem.optimization.volume_fraction,
            dtype=np.float32,
        )
        uniform_projected = project_design_density(case, uniform_raw)
        oracle_projected = project_design_density(case, label.design_tensor())
        oracle = solve_case_with_initial_density(case, oracle_projected.design_density)
        validate_refinement_quality(case, oracle, uniform_metrics.final_compliance)
        system = _case_system(case)
        uniform_initial = _compliance(case, system, uniform_projected.physical_density)
        if uniform_initial <= 0.0:
            raise ValueError("nonpositive uniform initial compliance")
        oracle_initial = _compliance(case, system, oracle_projected.physical_density)
        density_filter = build_density_filter(system[0], case.problem.optimization.filter_radius)
        for candidate in candidates:
            raw = _predict(case, candidate)
            raw_design = np.asarray(raw, dtype=np.float64).reshape(-1)
            raw_physical = apply_density_filter(
                density_filter,
                np.clip(raw_design, case.problem.optimization.minimum_density, 1.0),
            )
            projected = project_design_density(case, raw)
            result = solve_case_with_initial_density(case, projected.design_density)
            try:
                validate_refinement_quality(case, result, uniform_metrics.final_compliance)
                quality_passed = True
            except (RuntimeError, ValueError):
                quality_passed = False
            projected_initial = _compliance(case, system, projected.physical_density)
            rows.append(
                LearnedRow(
                    case_id=case.case_id,
                    seed=candidate.seed,
                    direction=str(case.problem.loads[0].direction),
                    volume=case.problem.optimization.volume_fraction,
                    raw_mse=float(np.mean((raw_design - target) ** 2)),
                    projected_mse=float(np.mean((projected.design_density - target) ** 2)),
                    raw_volume_error=abs(
                        float(np.mean(raw_physical)) - case.problem.optimization.volume_fraction
                    ),
                    projected_volume_error=abs(
                        float(np.mean(projected.physical_density))
                        - case.problem.optimization.volume_fraction
                    ),
                    projected_initial_compliance_ratio=projected_initial / uniform_initial,
                    projected_initial_compliance_over_oracle=(projected_initial / oracle_initial),
                    first_refinement_compliance_ratio=(
                        result.history[0].compliance / uniform_metrics.final_compliance
                    ),
                    tenth_refinement_compliance_ratio=(
                        result.history[min(9, len(result.history) - 1)].compliance
                        / uniform_metrics.final_compliance
                    ),
                    final_compliance_ratio=result.compliance / uniform_metrics.final_compliance,
                    terminal_density_change=result.history[-1].density_change,
                    uniform_iterations=len(uniform.history),
                    oracle_iterations=len(oracle.history),
                    learned_iterations=len(result.history),
                    converged=result.converged,
                    quality_passed=quality_passed,
                )
            )
    return rows


def _learned_summary(rows: list[LearnedRow]) -> dict[str, object]:
    def group_summary(group: list[LearnedRow]) -> dict[str, object]:
        return {
            "attempts": len(group),
            "quality_failures": sum(not row.quality_passed for row in group),
            "nonconverged": sum(not row.converged for row in group),
            "median_raw_mse": median(row.raw_mse for row in group),
            "median_projected_mse": median(row.projected_mse for row in group),
            "median_raw_volume_error": median(row.raw_volume_error for row in group),
            "max_projected_volume_error": max(row.projected_volume_error for row in group),
            "median_initial_compliance_ratio": median(
                row.projected_initial_compliance_ratio for row in group
            ),
            "median_initial_compliance_over_oracle": median(
                row.projected_initial_compliance_over_oracle for row in group
            ),
            "median_first_refinement_compliance_ratio": median(
                row.first_refinement_compliance_ratio for row in group
            ),
            "median_tenth_refinement_compliance_ratio": median(
                row.tenth_refinement_compliance_ratio for row in group
            ),
            "median_final_compliance_ratio": median(row.final_compliance_ratio for row in group),
            "median_uniform_iterations": median(row.uniform_iterations for row in group),
            "median_oracle_iterations": median(row.oracle_iterations for row in group),
            "median_learned_iterations": median(row.learned_iterations for row in group),
        }

    return {
        "validation_cases": len({row.case_id for row in rows}),
        "seeds": sorted({row.seed for row in rows}),
        "all": group_summary(rows),
        "projection_reduced_mse_count": sum(row.projected_mse < row.raw_mse for row in rows),
        "quality_failures_after_convergence": sum(
            not row.quality_passed and row.converged for row in rows
        ),
        "compliance_limit_exceeded": sum(row.final_compliance_ratio > 1.001 for row in rows),
        "lower_initial_compliance_yet_failed": sum(
            row.projected_initial_compliance_ratio < 1.0 and not row.quality_passed for row in rows
        ),
        "fewer_iterations_yet_failed": sum(
            row.learned_iterations < row.uniform_iterations and not row.quality_passed
            for row in rows
        ),
        "quality_passed_and_fewer_iterations": sum(
            row.quality_passed and row.learned_iterations < row.uniform_iterations for row in rows
        ),
        "by_direction": {
            direction: group_summary([row for row in rows if row.direction == direction])
            for direction in sorted({row.direction for row in rows})
        },
        "by_volume": {
            f"{volume:.2f}": group_summary([row for row in rows if row.volume == volume])
            for volume in sorted({row.volume for row in rows})
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m2-index", required=True, type=Path)
    parser.add_argument("--m2-root", required=True, type=Path)
    parser.add_argument("--m1-artifact-root", required=True, type=Path)
    args = parser.parse_args()
    index_bytes = args.m2_index.read_bytes()
    if hashlib.sha256(index_bytes).hexdigest() != M2_INDEX_SHA256:
        raise ValueError("M2 index checksum mismatch")
    validation, failures = select_diagnostic_cases(json.loads(index_bytes))
    convergence = diagnose_convergence(failures)
    learned = diagnose_learned(validation, args.m2_root, args.m1_artifact_root)
    summary = {
        "diagnostic_version": "topolab.b1.failure-diagnosis.v1",
        "m2_index_sha256": M2_INDEX_SHA256,
        "m2_validation_label_count": len(validation),
        "failed_case_definition_count": len(failures),
        "held_out_label_artifacts_opened": 0,
        "frozen_budget": FROZEN_BUDGET,
        "diagnostic_budget": DIAGNOSTIC_BUDGET,
        "convergence": {
            "at_120_nonconverged": sum(row.change_at_120 > 0.01 for row in convergence),
            "by_split": dict(Counter(row.split for row in convergence)),
            "converged_by_240": sum(row.converged_by_240 for row in convergence),
            "decreasing_change_tails": sum(row.last_ten_changes_decrease for row in convergence),
            "decreasing_compliance_tails": sum(
                row.last_ten_compliances_decrease for row in convergence
            ),
            "min_update_cosine_at_120": min(row.update_cosine_at_120 for row in convergence),
            "max_independent_volume_error": max(
                row.max_independent_volume_error for row in convergence
            ),
            "max_recorded_volume_disagreement": max(
                row.max_recorded_volume_disagreement for row in convergence
            ),
            "max_compliance_resolve_relative_error_at_120": max(
                row.compliance_resolve_relative_error_at_120 for row in convergence
            ),
            "rows": [asdict(row) for row in convergence],
        },
        "learned": {
            **_learned_summary(learned),
            "rows": [asdict(row) for row in learned],
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
