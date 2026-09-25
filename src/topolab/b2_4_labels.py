"""Versioned B2.3-policy labels for the complete B2.4 development cohort."""

from typing import Annotated, Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import Field, model_validator

from topolab.baselines import validate_refinement_quality
from topolab.dataset import DatasetEnvironment
from topolab.experiment import ExperimentCase, project_design_density
from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.mesh import generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport, PointLoad
from topolab.problem import (
    ContractModel,
    FaceLoadDefinition,
    PointLoadDefinition,
    TopologyProblem,
    TopologyResult,
    solve_problem,
)
from topolab.simp import (
    apply_density_filter,
    backpropagate_density_gradient,
    build_density_filter,
    evaluate_compliance,
)

LABEL_VERSION = "topolab.b2_3.label.v1"
ARTIFACT_VERSION = "topolab.b2_4.artifact.v1"
VOLUME_TOLERANCE = 0.005
COMPLIANCE_RTOL = 1e-9


class B24Label(ContractModel):
    """One audited physical-plateau label with its sensitivity loss weights."""

    artifact_version: Literal["topolab.b2_4.artifact.v1"] = "topolab.b2_4.artifact.v1"
    label_version: Literal["topolab.b2_3.label.v1"] = "topolab.b2_3.label.v1"
    solver_policy: Literal["topolab.simp.physical_plateau.v1"] = (
        "topolab.simp.physical_plateau.v1"
    )
    source_revision: Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
    source_tree_clean: Literal[True] = True
    environment: DatasetEnvironment
    source_case_id: str
    result_id: str
    case: ExperimentCase
    split: Literal["train", "validation"]
    scale: Literal["small", "large"]
    direction: Literal["y", "z"]
    volume: Annotated[float, Field(gt=0.0, lt=1.0)]
    tensor_dtype: Literal["float32"] = "float32"
    tensor_axis_order: Literal["channel,z,y,x"] = "channel,z,y,x"
    tensor_shape: tuple[int, int, int, int]
    design_density: tuple[float, ...]
    physical_density: tuple[float, ...]
    sensitivity_weight: tuple[float, ...]
    compliance: Annotated[float, Field(gt=0.0, allow_inf_nan=False)]
    physical_volume_fraction: Annotated[
        float, Field(gt=0.0, le=1.0, allow_inf_nan=False)
    ]
    iterations: Annotated[int, Field(strict=True, gt=0)]
    terminal_density_change: Annotated[
        float, Field(ge=0.0, allow_inf_nan=False)
    ]
    stop_reason: Literal["design_max", "physical_plateau"]

    @model_validator(mode="after")
    def validate_stored_state(self) -> "B24Label":
        problem = self.case.problem
        nx, ny, nz = problem.mesh.element_counts
        if self.tensor_shape != (1, nz, ny, nx):
            raise ValueError("label tensor shape differs from physical mesh")
        if self.scale != ("small" if (nx, ny, nz) == (12, 6, 3) else "large"):
            raise ValueError("label scale differs from physical mesh")
        if problem.loads[0].direction != self.direction:
            raise ValueError("label direction differs from case")
        if problem.optimization.volume_fraction != self.volume:
            raise ValueError("label volume differs from case")
        if self.iterations > problem.optimization.max_iterations:
            raise ValueError("label exceeds case iteration budget")
        if self.stop_reason == "design_max" and (
            self.terminal_density_change > problem.optimization.convergence_tolerance
        ):
            raise ValueError("design stop exceeds density tolerance")
        if self.stop_reason == "physical_plateau" and (
            self.terminal_density_change <= problem.optimization.convergence_tolerance
        ):
            raise ValueError("physical stop conflicts with design tolerance")

        count = nx * ny * nz
        design = _exact_float32(self.design_density, count)
        physical = _exact_float32(self.physical_density, count)
        weights = _exact_float32(self.sensitivity_weight, count)
        if np.any(design < np.float32(problem.optimization.minimum_density)) or np.any(
            design > 1.0
        ):
            raise ValueError("design density exceeds case bounds")
        if np.any(physical <= 0.0) or np.any(physical > 1.0):
            raise ValueError("physical density exceeds bounds")
        if np.any(weights <= 0.0) or not np.isclose(
            np.mean(weights, dtype=np.float64), 1.0, rtol=0.0, atol=1e-6
        ):
            raise ValueError("sensitivity weights must be positive with mean one")
        mesh = generate_structured_hex8(nx, ny, nz, lengths=problem.mesh.lengths)
        density_filter = build_density_filter(mesh, problem.optimization.filter_radius)
        expected = np.asarray(
            apply_density_filter(density_filter, design.astype(np.float64)),
            dtype=np.float32,
        )
        if not np.array_equal(physical, expected):
            raise ValueError("physical density differs from stored filtered design")
        volume = float(np.mean(physical, dtype=np.float64))
        if self.physical_volume_fraction != volume:
            raise ValueError("stored physical volume differs from density")
        if abs(volume - self.volume) > VOLUME_TOLERANCE:
            raise ValueError("physical volume exceeds quality tolerance")
        return self


def _exact_float32(values: tuple[float, ...], count: int) -> NDArray[np.float32]:
    if len(values) != count:
        raise ValueError("label vector length differs from mesh")
    original = np.asarray(values, dtype=np.float64)
    if not np.all(np.isfinite(original)):
        raise ValueError("label vector has non-finite values")
    stored = original.astype(np.float32)
    if not np.array_equal(original, stored.astype(np.float64)):
        raise ValueError("label vector contains non-float32 values")
    return stored


def _core_load(load: PointLoadDefinition | FaceLoadDefinition) -> PointLoad | FaceLoad:
    if isinstance(load, PointLoadDefinition):
        return PointLoad(node=load.node, direction=load.direction, magnitude=load.magnitude)
    return FaceLoad(
        axis=load.axis,
        side=load.side,
        direction=load.direction,
        total=load.total,
    )


def _analysis_and_weights(
    case: ExperimentCase,
    design: NDArray[np.float32],
    physical: NDArray[np.float32],
) -> tuple[float, NDArray[np.float32]]:
    problem = case.problem
    mesh = generate_structured_hex8(
        *problem.mesh.element_counts, lengths=problem.mesh.lengths
    )
    density_filter = build_density_filter(mesh, problem.optimization.filter_radius)
    expected = np.asarray(
        apply_density_filter(density_filter, design.astype(np.float64)),
        dtype=np.float32,
    )
    if not np.array_equal(physical, expected):
        raise ValueError("stored physical density differs from filtered design")
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
    loads = build_load_vector(mesh, [_core_load(load) for load in problem.loads])
    analysis = evaluate_compliance(
        mesh,
        physical.astype(np.float64),
        loads,
        constrained,
        solid_modulus=problem.material.solid_modulus,
        minimum_modulus=problem.material.minimum_modulus,
        poisson_ratio=problem.material.poisson_ratio,
        penalty=problem.optimization.penalty,
    )
    absolute_gradient = np.abs(
        backpropagate_density_gradient(density_filter, analysis.sensitivity)
    )
    mean = float(np.mean(absolute_gradient))
    if not np.isfinite(mean) or mean <= 0.0:
        raise ValueError("sensitivity gradient has no positive finite mean")
    clipped = np.clip(absolute_gradient / mean, 0.25, 4.0)
    normalized = clipped / np.mean(clipped)
    weights = np.asarray(normalized, dtype=np.float32)
    if not np.isfinite(analysis.compliance) or analysis.compliance <= 0.0:
        raise ValueError("independent compliance is invalid")
    return analysis.compliance, weights


def audit_label(label: B24Label) -> None:
    """Independently re-solve and verify persisted compliance and weights."""

    design = np.asarray(label.design_density, dtype=np.float32)
    physical = np.asarray(label.physical_density, dtype=np.float32)
    compliance, expected_weights = _analysis_and_weights(label.case, design, physical)
    if not np.isclose(label.compliance, compliance, rtol=COMPLIANCE_RTOL, atol=0.0):
        raise ValueError("stored compliance failed independent audit")
    if not np.array_equal(
        np.asarray(label.sensitivity_weight, dtype=np.float32), expected_weights
    ):
        raise ValueError("stored sensitivity weights failed independent audit")


def _validate_terminal_state(case: ExperimentCase, result: TopologyResult) -> None:
    if not result.converged or not result.history:
        raise ValueError("label solver did not converge")
    last = result.history[-1]
    if (
        last.iteration != len(result.history)
        or len(result.history) > case.problem.optimization.max_iterations
        or result.design_density != last.design_density
        or result.physical_density != last.physical_density
        or result.compliance != last.compliance
        or not np.isclose(
            last.volume_fraction,
            np.mean(result.physical_density),
            rtol=0.0,
            atol=1e-12,
        )
    ):
        raise ValueError("solver final state differs from terminal history")


def generate_b24_label(
    *,
    case: ExperimentCase,
    source_case_id: str,
    result_id: str,
    split: Literal["train", "validation"],
    scale: Literal["small", "large"],
    direction: Literal["y", "z"],
    volume: float,
    source_revision: str,
    environment: DatasetEnvironment,
) -> B24Label:
    """Solve one budget-240 uniform case and store a complete audited label."""

    nx, ny, nz = case.problem.mesh.element_counts
    raw = np.full((1, nz, ny, nx), volume, dtype=np.float32)
    projected = project_design_density(case, raw)
    payload = case.problem.model_dump(mode="json")
    payload["initial_density"] = tuple(float(value) for value in projected.design_density)
    result = solve_problem(
        TopologyProblem.model_validate(payload), termination_policy="physical_plateau"
    )
    _validate_terminal_state(case, result)
    validate_refinement_quality(case, result, None)
    design = np.asarray(result.design_density, dtype=np.float32)
    mesh = generate_structured_hex8(nx, ny, nz, lengths=case.problem.mesh.lengths)
    density_filter = build_density_filter(
        mesh, case.problem.optimization.filter_radius
    )
    physical = np.asarray(
        apply_density_filter(density_filter, design.astype(np.float64)),
        dtype=np.float32,
    )
    compliance, weights = _analysis_and_weights(case, design, physical)
    last = result.history[-1]
    return B24Label(
        source_revision=source_revision,
        environment=environment,
        source_case_id=source_case_id,
        result_id=result_id,
        case=case,
        split=split,
        scale=scale,
        direction=direction,
        volume=volume,
        tensor_shape=(1, nz, ny, nx),
        design_density=tuple(float(v) for v in design),
        physical_density=tuple(float(v) for v in physical),
        sensitivity_weight=tuple(float(v) for v in weights),
        compliance=compliance,
        physical_volume_fraction=float(np.mean(physical, dtype=np.float64)),
        iterations=len(result.history),
        terminal_density_change=last.density_change,
        stop_reason=(
            "design_max"
            if last.density_change <= case.problem.optimization.convergence_tolerance
            else "physical_plateau"
        ),
    )
