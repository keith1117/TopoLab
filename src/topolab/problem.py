"""Serializable problem and result contracts for platform callers."""

from collections.abc import Callable, Iterable
from typing import Annotated, Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import BaseModel, ConfigDict, Field, model_validator

from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.mesh import generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport, PointLoad
from topolab.simp import SimpConfig, SimpIteration, TerminationPolicy, optimize_simp

type Axis = Literal["x", "y", "z"]
type Direction = Literal["x", "y", "z", 0, 1, 2]
type FaceSide = Literal["min", "max"]
type IterationCallback = Callable[[SimpIteration], None]
type CancellationCheck = Callable[[], bool]


class ContractModel(BaseModel):
    """Strict, immutable base for public platform contracts."""

    model_config = ConfigDict(frozen=True, extra="forbid", allow_inf_nan=False)


class MeshDefinition(ContractModel):
    """Structured Hex8 mesh dimensions."""

    element_counts: tuple[
        Annotated[int, Field(strict=True, gt=0)],
        Annotated[int, Field(strict=True, gt=0)],
        Annotated[int, Field(strict=True, gt=0)],
    ]
    lengths: tuple[
        Annotated[float, Field(gt=0.0)],
        Annotated[float, Field(gt=0.0)],
        Annotated[float, Field(gt=0.0)],
    ] = (1.0, 1.0, 1.0)


class MaterialDefinition(ContractModel):
    """Elastic and SIMP modulus parameters."""

    solid_modulus: Annotated[float, Field(gt=0.0)]
    minimum_modulus: Annotated[float, Field(gt=0.0)]
    poisson_ratio: Annotated[float, Field(gt=-1.0, lt=0.5)]

    @model_validator(mode="after")
    def validate_moduli(self) -> "MaterialDefinition":
        if self.minimum_modulus >= self.solid_modulus:
            raise ValueError("minimum_modulus must be less than solid_modulus")
        return self


class OptimizationDefinition(ContractModel):
    """Serializable density-filtered SIMP configuration."""

    volume_fraction: Annotated[float, Field(gt=0.0, le=1.0)]
    filter_radius: Annotated[float, Field(gt=0.0)]
    penalty: Annotated[float, Field(ge=1.0)] = 3.0
    minimum_density: Annotated[float, Field(gt=0.0, lt=1.0)] = 1e-3
    move_limit: Annotated[float, Field(gt=0.0, le=1.0)] = 0.2
    convergence_tolerance: Annotated[float, Field(gt=0.0)] = 0.01
    max_iterations: Annotated[int, Field(strict=True, gt=0)] = 100

    @model_validator(mode="after")
    def validate_density_bounds(self) -> "OptimizationDefinition":
        if self.minimum_density >= self.volume_fraction:
            raise ValueError("minimum_density must be less than volume_fraction")
        return self


class FixedFaceSupportDefinition(ContractModel):
    """Serializable fixed-face support."""

    axis: Axis
    side: FaceSide
    directions: Annotated[tuple[Direction, ...], Field(min_length=1)] = (
        "x",
        "y",
        "z",
    )


class PointLoadDefinition(ContractModel):
    """Serializable signed point load."""

    kind: Literal["point"] = "point"
    node: Annotated[int, Field(strict=True, ge=0)]
    direction: Direction
    magnitude: float

    @model_validator(mode="after")
    def validate_magnitude(self) -> "PointLoadDefinition":
        if self.magnitude == 0.0:
            raise ValueError("magnitude must be nonzero")
        return self


class FaceLoadDefinition(ContractModel):
    """Serializable signed equal-node face resultant."""

    kind: Literal["face"] = "face"
    axis: Axis
    side: FaceSide
    direction: Direction
    total: float

    @model_validator(mode="after")
    def validate_total(self) -> "FaceLoadDefinition":
        if self.total == 0.0:
            raise ValueError("total must be nonzero")
        return self


type LoadDefinition = Annotated[
    PointLoadDefinition | FaceLoadDefinition,
    Field(discriminator="kind"),
]


class TopologyProblem(ContractModel):
    """Complete serializable input for one optimization run."""

    mesh: MeshDefinition
    material: MaterialDefinition
    supports: Annotated[tuple[FixedFaceSupportDefinition, ...], Field(min_length=1)]
    loads: Annotated[tuple[LoadDefinition, ...], Field(min_length=1)]
    optimization: OptimizationDefinition
    initial_density: tuple[float, ...] | None = None

    @model_validator(mode="after")
    def validate_cross_fields(self) -> "TopologyProblem":
        number_of_nodes = (
            (self.mesh.element_counts[0] + 1)
            * (self.mesh.element_counts[1] + 1)
            * (self.mesh.element_counts[2] + 1)
        )
        if any(
            isinstance(load, PointLoadDefinition) and load.node >= number_of_nodes
            for load in self.loads
        ):
            raise ValueError("point-load node must lie within the mesh")
        if self.initial_density is None:
            return self
        number_of_elements = (
            self.mesh.element_counts[0]
            * self.mesh.element_counts[1]
            * self.mesh.element_counts[2]
        )
        if len(self.initial_density) != number_of_elements:
            raise ValueError(
                f"initial_density must contain {number_of_elements} values"
            )
        if any(
            value < self.optimization.minimum_density or value > 1.0
            for value in self.initial_density
        ):
            raise ValueError("initial_density must lie within [minimum_density, 1]")
        return self


class IterationResult(ContractModel):
    """Serializable metrics for one post-update optimization state."""

    iteration: int
    compliance: float
    volume_fraction: float
    density_change: float
    design_density: tuple[float, ...]
    physical_density: tuple[float, ...]


class TopologyResult(ContractModel):
    """Serializable output for one completed optimization run."""

    design_density: tuple[float, ...]
    physical_density: tuple[float, ...]
    compliance: float
    displacements: tuple[float, ...]
    reactions: tuple[float, ...]
    history: tuple[IterationResult, ...]
    converged: bool


def solve_problem(
    problem: TopologyProblem,
    *,
    iteration_callback: IterationCallback | None = None,
    should_cancel: CancellationCheck | None = None,
    termination_policy: TerminationPolicy = "design_max",
) -> TopologyResult:
    """Translate one public problem contract and run the numerical core."""

    mesh = generate_structured_hex8(
        *problem.mesh.element_counts,
        lengths=problem.mesh.lengths,
    )
    supports = [
        FixedFaceSupport(
            axis=support.axis,
            side=support.side,
            directions=support.directions,
        )
        for support in problem.supports
    ]
    constrained_dofs = build_constrained_dofs(mesh, supports)
    loads = build_load_vector(mesh, [_build_load(load) for load in problem.loads])
    settings = problem.optimization
    config = SimpConfig(
        volume_fraction=settings.volume_fraction,
        filter_radius=settings.filter_radius,
        penalty=settings.penalty,
        minimum_density=settings.minimum_density,
        move_limit=settings.move_limit,
        convergence_tolerance=settings.convergence_tolerance,
        max_iterations=settings.max_iterations,
        termination_policy=termination_policy,
    )
    initial_density = (
        None if problem.initial_density is None else _as_float_array(problem.initial_density)
    )
    result = optimize_simp(
        mesh,
        loads,
        constrained_dofs,
        solid_modulus=problem.material.solid_modulus,
        minimum_modulus=problem.material.minimum_modulus,
        poisson_ratio=problem.material.poisson_ratio,
        config=config,
        initial_density=initial_density,
        iteration_callback=iteration_callback,
        should_cancel=should_cancel,
    )
    return TopologyResult(
        design_density=_as_float_tuple(result.design_density),
        physical_density=_as_float_tuple(result.physical_density),
        compliance=result.compliance,
        displacements=_as_float_tuple(result.displacements),
        reactions=_as_float_tuple(result.reactions),
        history=tuple(
            IterationResult(
                iteration=state.iteration,
                compliance=state.compliance,
                volume_fraction=state.volume_fraction,
                density_change=state.density_change,
                design_density=_as_float_tuple(state.design_density),
                physical_density=_as_float_tuple(state.physical_density),
            )
            for state in result.history
        ),
        converged=result.converged,
    )


def _build_load(load: LoadDefinition) -> PointLoad | FaceLoad:
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


def _as_float_tuple(values: Iterable[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _as_float_array(values: tuple[float, ...]) -> NDArray[np.float64]:
    return np.asarray(values, dtype=np.float64)
