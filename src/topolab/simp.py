"""Compliance and sensitivity operations for density-based topology optimization."""

from collections.abc import Callable
from dataclasses import dataclass
from math import ceil, isfinite, sqrt
from numbers import Integral, Real
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import coo_matrix, csr_matrix  # type: ignore[import-untyped]

from topolab.fem import (
    FactorizationOrdering,
    assemble_global_stiffness,
    hex8_element_stiffness,
    solve_linear_static,
)
from topolab.mesh import Hex8Mesh

type TerminationPolicy = Literal["design_max", "physical_plateau"]

PHYSICAL_PLATEAU_SOLVER_VERSION = "topolab.simp.physical_plateau.v1"
_PHYSICAL_PLATEAU_WINDOW = 10
_PHYSICAL_PLATEAU_COMPLIANCE_RELATIVE_LIMIT = 2e-4


@dataclass(frozen=True, slots=True)
class ComplianceResult:
    """Compliance state and physical-density derivative for one linear solve."""

    compliance: float
    sensitivity: NDArray[np.float64]
    displacements: NDArray[np.float64]
    reactions: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class DensityFilter:
    """Sparse element-center density filter and its row normalization."""

    matrix: csr_matrix
    row_sums: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class SimpConfig:
    """Configuration for the first deterministic SIMP/OC optimization loop."""

    volume_fraction: float
    filter_radius: float
    penalty: float = 3.0
    minimum_density: float = 1e-3
    move_limit: float = 0.2
    convergence_tolerance: float = 0.01
    max_iterations: int = 100
    termination_policy: TerminationPolicy = "design_max"


@dataclass(frozen=True, slots=True)
class SimpIteration:
    """Metrics and densities for one post-update, re-solved optimization state."""

    iteration: int
    compliance: float
    volume_fraction: float
    density_change: float
    design_density: NDArray[np.float64]
    physical_density: NDArray[np.float64]


@dataclass(frozen=True, slots=True)
class SimpResult:
    """Final re-solved SIMP state and its state-consistent iteration history."""

    design_density: NDArray[np.float64]
    physical_density: NDArray[np.float64]
    compliance: float
    displacements: NDArray[np.float64]
    reactions: NDArray[np.float64]
    history: tuple[SimpIteration, ...]
    converged: bool


class OptimizationCancelledError(RuntimeError):
    """Raised when a caller requests cooperative optimization cancellation."""


def simp_element_moduli(
    densities: NDArray[np.float64],
    *,
    solid_modulus: float,
    minimum_modulus: float,
    penalty: float,
) -> NDArray[np.float64]:
    """Interpolate absolute element moduli from physical densities."""

    density_values = _validate_densities(densities)
    solid_modulus, minimum_modulus, penalty = _validate_simp_parameters(
        solid_modulus,
        minimum_modulus,
        penalty,
    )
    return minimum_modulus + density_values**penalty * (
        solid_modulus - minimum_modulus
    )


def evaluate_compliance(
    mesh: Hex8Mesh,
    densities: NDArray[np.float64],
    loads: NDArray[np.float64],
    constrained_dofs: NDArray[np.int64],
    *,
    solid_modulus: float,
    minimum_modulus: float,
    poisson_ratio: float,
    penalty: float,
    ordering: FactorizationOrdering = "auto",
) -> ComplianceResult:
    """Solve one physical-density state and return compliance and its derivative."""

    density_values = _validate_densities(densities)
    number_of_elements = mesh.element_dofs.shape[0]
    if density_values.shape != (number_of_elements,):
        raise ValueError(f"densities must have shape ({number_of_elements},)")
    solid_modulus, minimum_modulus, penalty = _validate_simp_parameters(
        solid_modulus,
        minimum_modulus,
        penalty,
    )

    nx, ny, nz = mesh.element_counts
    lx, ly, lz = mesh.lengths
    element_dimensions = (lx / nx, ly / ny, lz / nz)
    unit_stiffness = hex8_element_stiffness(
        1.0,
        poisson_ratio,
        dimensions=element_dimensions,
    )
    element_moduli = minimum_modulus + density_values**penalty * (
        solid_modulus - minimum_modulus
    )
    global_stiffness = assemble_global_stiffness(
        mesh,
        unit_stiffness,
        element_factors=element_moduli,
    )
    solution = solve_linear_static(
        global_stiffness, loads, constrained_dofs, ordering=ordering
    )

    element_displacements = solution.displacements[mesh.element_dofs]
    unit_energies = np.einsum(
        "ei,ij,ej->e",
        element_displacements,
        unit_stiffness,
        element_displacements,
    )
    modulus_derivative = (
        penalty
        * density_values ** (penalty - 1.0)
        * (solid_modulus - minimum_modulus)
    )
    sensitivity = -modulus_derivative * unit_energies
    compliance = float(
        np.dot(np.asarray(loads, dtype=np.float64), solution.displacements)
    )

    return ComplianceResult(
        compliance=compliance,
        sensitivity=sensitivity,
        displacements=solution.displacements,
        reactions=solution.reactions,
    )


def build_density_filter(mesh: Hex8Mesh, radius: float) -> DensityFilter:
    """Build sparse distance weights between structured element centers."""

    validated_radius = _positive_finite("radius", radius)
    nx, ny, nz = mesh.element_counts
    lx, ly, lz = mesh.lengths
    dx, dy, dz = lx / nx, ly / ny, lz / nz
    search_x = int(ceil(validated_radius / dx))
    search_y = int(ceil(validated_radius / dy))
    search_z = int(ceil(validated_radius / dz))
    rows: list[int] = []
    columns: list[int] = []
    weights: list[float] = []

    for element_z in range(nz):
        for element_y in range(ny):
            for element_x in range(nx):
                row = element_x + nx * (element_y + ny * element_z)
                for neighbor_z in range(
                    max(0, element_z - search_z),
                    min(nz, element_z + search_z + 1),
                ):
                    for neighbor_y in range(
                        max(0, element_y - search_y),
                        min(ny, element_y + search_y + 1),
                    ):
                        for neighbor_x in range(
                            max(0, element_x - search_x),
                            min(nx, element_x + search_x + 1),
                        ):
                            distance = sqrt(
                                ((element_x - neighbor_x) * dx) ** 2
                                + ((element_y - neighbor_y) * dy) ** 2
                                + ((element_z - neighbor_z) * dz) ** 2
                            )
                            weight = validated_radius - distance
                            if weight > 0.0:
                                column = neighbor_x + nx * (
                                    neighbor_y + ny * neighbor_z
                                )
                                rows.append(row)
                                columns.append(column)
                                weights.append(weight)

    number_of_elements = nx * ny * nz
    matrix = coo_matrix(
        (weights, (rows, columns)),
        shape=(number_of_elements, number_of_elements),
    ).tocsr()
    matrix.sum_duplicates()
    matrix.sort_indices()
    row_sums = np.asarray(matrix.sum(axis=1)).reshape(-1)
    return DensityFilter(matrix=matrix, row_sums=row_sums)


def apply_density_filter(
    density_filter: DensityFilter,
    design_density: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Map design density to physical density."""

    design = _validate_filter_vector(density_filter, design_density, "design_density")
    if np.any(design < 0.0) or np.any(design > 1.0):
        raise ValueError("design_density must lie in the interval [0, 1]")
    physical = (
        np.asarray(density_filter.matrix @ design).reshape(-1)
        / density_filter.row_sums
    )
    return np.clip(physical, np.min(design), np.max(design))


def backpropagate_density_gradient(
    density_filter: DensityFilter,
    physical_gradient: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Apply the transpose density-filter map to a physical-density gradient."""

    gradient = _validate_filter_vector(
        density_filter,
        physical_gradient,
        "physical_gradient",
    )
    return np.asarray(
        density_filter.matrix.T @ (gradient / density_filter.row_sums)
    ).reshape(-1)


def optimality_criteria_update(
    design_density: NDArray[np.float64],
    objective_gradient: NDArray[np.float64],
    volume_gradient: NDArray[np.float64],
    density_filter: DensityFilter,
    *,
    volume_fraction: float,
    minimum_density: float,
    move_limit: float,
    bisection_tolerance: float = 1e-8,
) -> NDArray[np.float64]:
    """Perform one move-limited OC update under filtered physical volume."""

    design = _validate_filter_vector(density_filter, design_density, "design_density")
    objective = _validate_filter_vector(
        density_filter,
        objective_gradient,
        "objective_gradient",
    )
    volume = _validate_filter_vector(
        density_filter,
        volume_gradient,
        "volume_gradient",
    )
    target, lower_density, move, tolerance = _validate_oc_parameters(
        volume_fraction,
        minimum_density,
        move_limit,
        bisection_tolerance,
    )
    if np.any(design < lower_density) or np.any(design > 1.0):
        raise ValueError("design_density must lie within [minimum_density, 1]")
    if np.any(objective > 0.0) or not np.any(objective < 0.0):
        raise ValueError("objective_gradient must be nonpositive with a negative entry")
    if np.any(volume <= 0.0):
        raise ValueError("volume_gradient must contain only positive values")

    lower_bound = np.maximum(lower_density, design - move)
    upper_bound = np.minimum(1.0, design + move)
    minimum_volume = float(np.mean(apply_density_filter(density_filter, lower_bound)))
    maximum_volume = float(np.mean(apply_density_filter(density_filter, upper_bound)))
    if target <= minimum_volume + tolerance:
        return lower_bound
    if target >= maximum_volume - tolerance:
        return upper_bound

    def candidate(lagrange_multiplier: float) -> NDArray[np.float64]:
        ratio = np.maximum(0.0, -objective / (volume * lagrange_multiplier))
        return np.clip(design * np.sqrt(ratio), lower_bound, upper_bound)

    lagrange_lower = 0.0
    lagrange_upper = 1.0
    while float(
        np.mean(apply_density_filter(density_filter, candidate(lagrange_upper)))
    ) > target:
        lagrange_upper *= 2.0

    updated = candidate(lagrange_upper)
    for _ in range(100):
        lagrange_midpoint = 0.5 * (lagrange_lower + lagrange_upper)
        updated = candidate(lagrange_midpoint)
        physical_volume = float(
            np.mean(apply_density_filter(density_filter, updated))
        )
        if abs(physical_volume - target) <= tolerance:
            break
        if physical_volume > target:
            lagrange_lower = lagrange_midpoint
        else:
            lagrange_upper = lagrange_midpoint
    return updated


def optimize_simp(
    mesh: Hex8Mesh,
    loads: NDArray[np.float64],
    constrained_dofs: NDArray[np.int64],
    *,
    solid_modulus: float,
    minimum_modulus: float,
    poisson_ratio: float,
    config: SimpConfig,
    initial_density: NDArray[np.float64] | None = None,
    iteration_callback: Callable[[SimpIteration], None] | None = None,
    should_cancel: Callable[[], bool] | None = None,
    ordering: FactorizationOrdering = "auto",
) -> SimpResult:
    """Run deterministic density-filtered SIMP with Optimality Criteria updates."""

    _validate_optimizer_config(config)
    _raise_if_cancelled(should_cancel)
    number_of_elements = mesh.element_dofs.shape[0]
    density_filter = build_density_filter(mesh, config.filter_radius)
    if initial_density is None:
        design_density = np.full(number_of_elements, config.volume_fraction)
    else:
        design_density = _validate_densities(initial_density).copy()
        if design_density.shape != (number_of_elements,):
            raise ValueError(f"initial_density must have shape ({number_of_elements},)")
        if np.any(design_density < config.minimum_density):
            raise ValueError("initial_density must be at least minimum_density")

    physical_density = apply_density_filter(density_filter, design_density)
    analysis = evaluate_compliance(
        mesh,
        physical_density,
        loads,
        constrained_dofs,
        solid_modulus=solid_modulus,
        minimum_modulus=minimum_modulus,
        poisson_ratio=poisson_ratio,
        penalty=config.penalty,
        ordering=ordering,
    )
    physical_volume_gradient = np.full(number_of_elements, 1.0 / number_of_elements)
    design_volume_gradient = backpropagate_density_gradient(
        density_filter,
        physical_volume_gradient,
    )
    history: list[SimpIteration] = []
    recent_physical_changes: list[float] = []
    converged = False

    for iteration in range(1, config.max_iterations + 1):
        _raise_if_cancelled(should_cancel)
        design_objective_gradient = backpropagate_density_gradient(
            density_filter,
            analysis.sensitivity,
        )
        updated_design = optimality_criteria_update(
            design_density,
            design_objective_gradient,
            design_volume_gradient,
            density_filter,
            volume_fraction=config.volume_fraction,
            minimum_density=config.minimum_density,
            move_limit=config.move_limit,
        )
        density_change = float(np.max(np.abs(updated_design - design_density)))
        updated_physical = apply_density_filter(density_filter, updated_design)
        if config.termination_policy == "physical_plateau":
            recent_physical_changes.append(
                float(np.max(np.abs(updated_physical - physical_density)))
            )
            if len(recent_physical_changes) > _PHYSICAL_PLATEAU_WINDOW:
                recent_physical_changes.pop(0)
        updated_analysis = evaluate_compliance(
            mesh,
            updated_physical,
            loads,
            constrained_dofs,
            solid_modulus=solid_modulus,
            minimum_modulus=minimum_modulus,
            poisson_ratio=poisson_ratio,
            penalty=config.penalty,
            ordering=ordering,
        )
        iteration_state = SimpIteration(
            iteration=iteration,
            compliance=updated_analysis.compliance,
            volume_fraction=float(np.mean(updated_physical)),
            density_change=density_change,
            design_density=updated_design.copy(),
            physical_density=updated_physical.copy(),
        )
        history.append(iteration_state)
        if iteration_callback is not None:
            iteration_callback(iteration_state)
        design_density = updated_design
        physical_density = updated_physical
        analysis = updated_analysis
        if density_change <= config.convergence_tolerance or (
            config.termination_policy == "physical_plateau"
            and len(history) >= _PHYSICAL_PLATEAU_WINDOW + 1
            and max(recent_physical_changes) <= config.convergence_tolerance
            and 0.0
            <= (
                history[-_PHYSICAL_PLATEAU_WINDOW - 1].compliance
                - analysis.compliance
            )
            / history[-_PHYSICAL_PLATEAU_WINDOW - 1].compliance
            <= _PHYSICAL_PLATEAU_COMPLIANCE_RELATIVE_LIMIT
        ):
            converged = True
            break

    return SimpResult(
        design_density=design_density.copy(),
        physical_density=physical_density.copy(),
        compliance=analysis.compliance,
        displacements=analysis.displacements,
        reactions=analysis.reactions,
        history=tuple(history),
        converged=converged,
    )


def _raise_if_cancelled(should_cancel: Callable[[], bool] | None) -> None:
    if should_cancel is not None and should_cancel():
        raise OptimizationCancelledError("optimization was cancelled")


def _validate_densities(densities: NDArray[np.float64]) -> NDArray[np.float64]:
    values = np.asarray(densities, dtype=np.float64)
    if values.ndim != 1 or values.size == 0:
        raise ValueError("densities must be a nonempty one-dimensional array")
    if not np.all(np.isfinite(values)):
        raise ValueError("densities must contain only finite values")
    if np.any(values <= 0.0) or np.any(values > 1.0):
        raise ValueError("densities must lie in the interval (0, 1]")
    return values


def _validate_simp_parameters(
    solid_modulus: float,
    minimum_modulus: float,
    penalty: float,
) -> tuple[float, float, float]:
    solid = _positive_finite("solid_modulus", solid_modulus)
    minimum = _positive_finite("minimum_modulus", minimum_modulus)
    if minimum >= solid:
        raise ValueError("minimum_modulus must be less than solid_modulus")
    validated_penalty = _finite_real("penalty", penalty)
    if validated_penalty < 1.0:
        raise ValueError("penalty must be greater than or equal to 1")
    return solid, minimum, validated_penalty


def _validate_filter_vector(
    density_filter: DensityFilter,
    values: NDArray[np.float64],
    name: str,
) -> NDArray[np.float64]:
    vector = np.asarray(values, dtype=np.float64)
    number_of_elements = density_filter.matrix.shape[0]
    if vector.shape != (number_of_elements,):
        raise ValueError(f"{name} must have shape ({number_of_elements},)")
    if not np.all(np.isfinite(vector)):
        raise ValueError(f"{name} must contain only finite values")
    return vector


def _validate_oc_parameters(
    volume_fraction: float,
    minimum_density: float,
    move_limit: float,
    bisection_tolerance: float,
) -> tuple[float, float, float, float]:
    target = _positive_finite("volume_fraction", volume_fraction)
    if target > 1.0:
        raise ValueError("volume_fraction must be less than or equal to 1")
    lower_density = _positive_finite("minimum_density", minimum_density)
    if lower_density >= target:
        raise ValueError("minimum_density must be less than volume_fraction")
    move = _positive_finite("move_limit", move_limit)
    if move > 1.0:
        raise ValueError("move_limit must be less than or equal to 1")
    tolerance = _positive_finite("bisection_tolerance", bisection_tolerance)
    return target, lower_density, move, tolerance


def _validate_optimizer_config(config: SimpConfig) -> None:
    if not isinstance(config, SimpConfig):
        raise TypeError("config must be a SimpConfig")
    _validate_oc_parameters(
        config.volume_fraction,
        config.minimum_density,
        config.move_limit,
        1e-8,
    )
    _positive_finite("filter_radius", config.filter_radius)
    penalty = _finite_real("penalty", config.penalty)
    if penalty < 1.0:
        raise ValueError("penalty must be greater than or equal to 1")
    _positive_finite("convergence_tolerance", config.convergence_tolerance)
    if isinstance(config.max_iterations, bool) or not isinstance(
        config.max_iterations, Integral
    ):
        raise TypeError("max_iterations must be an integer")
    if config.max_iterations <= 0:
        raise ValueError("max_iterations must be positive")
    if config.termination_policy not in {"design_max", "physical_plateau"}:
        raise ValueError("unsupported termination_policy")


def _positive_finite(name: str, value: float) -> float:
    result = _finite_real(name, value)
    if result <= 0.0:
        raise ValueError(f"{name} must be positive and finite")
    return result


def _finite_real(name: str, value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result
