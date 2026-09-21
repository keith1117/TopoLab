"""Versioned single-case label generation for the frozen M0 contract."""

from typing import Annotated, Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import Field, model_validator

from topolab.dataset import DatasetEnvironment
from topolab.experiment import ExperimentCase
from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.mesh import generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport, PointLoad
from topolab.problem import (
    ContractModel,
    FaceLoadDefinition,
    PointLoadDefinition,
    TopologyResult,
    solve_problem,
)
from topolab.simp import apply_density_filter, build_density_filter, evaluate_compliance

LABEL_RECORD_VERSION = "topolab.m0.label.v1"
LABEL_VOLUME_TOLERANCE = 5e-3
LABEL_COMPLIANCE_RELATIVE_TOLERANCE = 1e-9

_REVISION_PATTERN = r"^[0-9a-f]{40}$"


class LabelGenerationError(RuntimeError):
    """Raised when one case cannot produce a valid M0 label."""


class LabelRecord(ContractModel):
    """One converged, state-consistent M0 label and its provenance."""

    label_version: Literal["topolab.m0.label.v1"] = "topolab.m0.label.v1"
    case_schema_version: Literal["topolab.m0.case.v1"] = "topolab.m0.case.v1"
    generator_version: Literal["topolab.m0.generator.v1"] = (
        "topolab.m0.generator.v1"
    )
    solver_contract_version: Literal["topolab.simp.v1"] = "topolab.simp.v1"
    source_revision: Annotated[str, Field(pattern=_REVISION_PATTERN)]
    source_tree_clean: Literal[True] = True
    environment: DatasetEnvironment
    case: ExperimentCase
    tensor_dtype: Literal["float32"] = "float32"
    tensor_axis_order: Literal["channel,z,y,x"] = "channel,z,y,x"
    tensor_shape: tuple[
        Annotated[int, Field(strict=True, gt=0)],
        Annotated[int, Field(strict=True, gt=0)],
        Annotated[int, Field(strict=True, gt=0)],
        Annotated[int, Field(strict=True, gt=0)],
    ]
    design_density: Annotated[tuple[float, ...], Field(min_length=1)]
    physical_density: Annotated[tuple[float, ...], Field(min_length=1)]
    compliance: Annotated[float, Field(gt=0.0)]
    physical_volume_fraction: Annotated[float, Field(gt=0.0, le=1.0)]
    iterations: Annotated[int, Field(strict=True, gt=0)]
    terminal_density_change: Annotated[float, Field(ge=0.0)]
    termination_reason: Literal["density_change"] = "density_change"

    @model_validator(mode="after")
    def validate_label(self) -> "LabelRecord":
        nx, ny, nz = self.case.problem.mesh.element_counts
        expected_shape = (1, nz, ny, nx)
        if self.tensor_shape != expected_shape:
            raise ValueError("tensor shape does not match the case mesh")

        number_of_elements = nx * ny * nz
        design = _stored_float32_vector(
            self.design_density,
            number_of_elements,
            "design_density",
        )
        physical = _stored_float32_vector(
            self.physical_density,
            number_of_elements,
            "physical_density",
        )
        minimum_density = np.float32(
            self.case.problem.optimization.minimum_density
        )
        if np.any(design < minimum_density) or np.any(design > 1.0):
            raise ValueError("design_density must lie within the frozen density bounds")

        mesh = generate_structured_hex8(
            *self.case.problem.mesh.element_counts,
            lengths=self.case.problem.mesh.lengths,
        )
        density_filter = build_density_filter(
            mesh,
            self.case.problem.optimization.filter_radius,
        )
        expected_physical = np.asarray(
            apply_density_filter(density_filter, design.astype(np.float64)),
            dtype=np.float32,
        )
        if not np.array_equal(physical, expected_physical):
            raise ValueError("physical_density must match the frozen density filter")

        expected_volume = float(np.mean(physical, dtype=np.float64))
        if self.physical_volume_fraction != expected_volume:
            raise ValueError("physical_volume_fraction does not match physical_density")
        target_volume = self.case.problem.optimization.volume_fraction
        if abs(expected_volume - target_volume) > LABEL_VOLUME_TOLERANCE:
            raise ValueError("physical density violates the label volume tolerance")

        settings = self.case.problem.optimization
        if self.iterations > settings.max_iterations:
            raise ValueError("iterations exceeds the case maximum")
        if self.terminal_density_change > settings.convergence_tolerance:
            raise ValueError("terminal density change exceeds the convergence tolerance")
        return self

    def design_tensor(self) -> NDArray[np.float32]:
        """Materialize the serialized design label in frozen tensor order."""

        return np.asarray(self.design_density, dtype=np.float32).reshape(
            self.tensor_shape
        )

    def physical_tensor(self) -> NDArray[np.float32]:
        """Materialize the serialized physical label in frozen tensor order."""

        return np.asarray(self.physical_density, dtype=np.float32).reshape(
            self.tensor_shape
        )


def generate_label(
    case: ExperimentCase,
    *,
    source_revision: str,
    environment: DatasetEnvironment,
) -> LabelRecord:
    """Generate one converged uniform-start label through the frozen SIMP solver."""

    try:
        result = solve_problem(case.problem)
    except Exception as error:
        raise LabelGenerationError("label solver failed") from error
    try:
        _validate_solver_result(case, result)
    except LabelGenerationError:
        raise
    except Exception as error:
        raise LabelGenerationError("label validation failed") from error

    design = np.asarray(result.design_density, dtype=np.float32)
    mesh = generate_structured_hex8(
        *case.problem.mesh.element_counts,
        lengths=case.problem.mesh.lengths,
    )
    density_filter = build_density_filter(
        mesh,
        case.problem.optimization.filter_radius,
    )
    physical = np.asarray(
        apply_density_filter(density_filter, design.astype(np.float64)),
        dtype=np.float32,
    )
    try:
        stored_analysis = _evaluate_case_density(case, physical.astype(np.float64))
    except Exception as error:
        raise LabelGenerationError("stored label compliance solve failed") from error
    nx, ny, nz = case.problem.mesh.element_counts
    return LabelRecord(
        source_revision=source_revision,
        environment=environment,
        case=case,
        tensor_shape=(1, nz, ny, nx),
        design_density=tuple(float(value) for value in design),
        physical_density=tuple(float(value) for value in physical),
        compliance=stored_analysis,
        physical_volume_fraction=float(np.mean(physical, dtype=np.float64)),
        iterations=len(result.history),
        terminal_density_change=result.history[-1].density_change,
    )


def _validate_solver_result(case: ExperimentCase, result: TopologyResult) -> None:
    settings = case.problem.optimization
    if not result.converged:
        raise LabelGenerationError("label solver did not converge")
    if not result.history:
        raise LabelGenerationError("label solver returned no terminal state")

    final_state = result.history[-1]
    if final_state.iteration != len(result.history):
        raise LabelGenerationError("label history iteration numbering is inconsistent")
    if len(result.history) > settings.max_iterations:
        raise LabelGenerationError("label history exceeds the iteration limit")
    if final_state.density_change > settings.convergence_tolerance:
        raise LabelGenerationError("label solver reported inconsistent convergence")
    if result.design_density != final_state.design_density:
        raise LabelGenerationError("label design density is not the terminal state")
    if result.physical_density != final_state.physical_density:
        raise LabelGenerationError("label physical density is not the terminal state")
    if result.compliance != final_state.compliance:
        raise LabelGenerationError("label compliance is not the terminal state")

    physical = np.asarray(result.physical_density, dtype=np.float64)
    expected_volume = float(np.mean(physical))
    if final_state.volume_fraction != expected_volume:
        raise LabelGenerationError("label volume is not the terminal state")
    if abs(expected_volume - settings.volume_fraction) > LABEL_VOLUME_TOLERANCE:
        raise LabelGenerationError("label solver violated the volume tolerance")

    independently_resolved = _evaluate_case_density(case, physical)
    if not np.isclose(
        result.compliance,
        independently_resolved,
        rtol=LABEL_COMPLIANCE_RELATIVE_TOLERANCE,
        atol=0.0,
    ):
        raise LabelGenerationError("label compliance failed independent re-solve")


def _evaluate_case_density(
    case: ExperimentCase,
    physical_density: NDArray[np.float64],
) -> float:
    problem = case.problem
    mesh = generate_structured_hex8(
        *problem.mesh.element_counts,
        lengths=problem.mesh.lengths,
    )
    constrained_dofs = build_constrained_dofs(
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
    loads = build_load_vector(
        mesh,
        [_core_load(load) for load in problem.loads],
    )
    analysis = evaluate_compliance(
        mesh,
        physical_density,
        loads,
        constrained_dofs,
        solid_modulus=problem.material.solid_modulus,
        minimum_modulus=problem.material.minimum_modulus,
        poisson_ratio=problem.material.poisson_ratio,
        penalty=problem.optimization.penalty,
    )
    return analysis.compliance


def _core_load(load: PointLoadDefinition | FaceLoadDefinition) -> PointLoad | FaceLoad:
    if isinstance(load, PointLoadDefinition):
        return PointLoad(
            node=load.node,
            direction=load.direction,
            magnitude=load.magnitude,
        )
    return FaceLoad(
        axis=load.axis,
        side=load.side,
        direction=load.direction,
        total=load.total,
    )


def _stored_float32_vector(
    values: tuple[float, ...],
    expected_size: int,
    name: str,
) -> NDArray[np.float32]:
    if len(values) != expected_size:
        raise ValueError(f"{name} must contain {expected_size} values")
    stored = np.asarray(values, dtype=np.float64)
    converted = stored.astype(np.float32)
    if not np.array_equal(stored, converted.astype(np.float64)):
        raise ValueError(f"{name} must contain exact float32 values")
    return converted
