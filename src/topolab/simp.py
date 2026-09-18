"""Compliance and sensitivity operations for density-based topology optimization."""

from dataclasses import dataclass
from math import isfinite
from numbers import Real

import numpy as np
from numpy.typing import NDArray

from topolab.fem import (
    assemble_global_stiffness,
    hex8_element_stiffness,
    solve_linear_static,
)
from topolab.mesh import Hex8Mesh


@dataclass(frozen=True, slots=True)
class ComplianceResult:
    """Compliance state and physical-density derivative for one linear solve."""

    compliance: float
    sensitivity: NDArray[np.float64]
    displacements: NDArray[np.float64]
    reactions: NDArray[np.float64]


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
    solution = solve_linear_static(global_stiffness, loads, constrained_dofs)

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
