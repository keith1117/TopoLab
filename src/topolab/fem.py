"""Finite-element building blocks for small-strain 3D elasticity."""

from itertools import product
from math import isfinite, sqrt
from numbers import Real

import numpy as np
from numpy.typing import NDArray

from topolab.mesh import HEX8_LOCAL_NODE_OFFSETS

_HEX8_REFERENCE_COORDINATES = 2.0 * np.asarray(HEX8_LOCAL_NODE_OFFSETS, dtype=np.float64) - 1.0
_GAUSS_POINTS = (-1.0 / sqrt(3.0), 1.0 / sqrt(3.0))


def isotropic_elasticity_matrix(
    youngs_modulus: float,
    poisson_ratio: float,
) -> NDArray[np.float64]:
    """Return the 3D isotropic constitutive matrix in engineering-Voigt order."""

    youngs_modulus = _positive_finite("youngs_modulus", youngs_modulus)
    poisson_ratio = _finite_real("poisson_ratio", poisson_ratio)
    if not -1.0 < poisson_ratio < 0.5:
        raise ValueError("poisson_ratio must be greater than -1 and less than 0.5")

    lame_lambda = (
        youngs_modulus
        * poisson_ratio
        / ((1.0 + poisson_ratio) * (1.0 - 2.0 * poisson_ratio))
    )
    shear_modulus = youngs_modulus / (2.0 * (1.0 + poisson_ratio))
    normal_modulus = lame_lambda + 2.0 * shear_modulus

    return np.array(
        [
            [normal_modulus, lame_lambda, lame_lambda, 0.0, 0.0, 0.0],
            [lame_lambda, normal_modulus, lame_lambda, 0.0, 0.0, 0.0],
            [lame_lambda, lame_lambda, normal_modulus, 0.0, 0.0, 0.0],
            [0.0, 0.0, 0.0, shear_modulus, 0.0, 0.0],
            [0.0, 0.0, 0.0, 0.0, shear_modulus, 0.0],
            [0.0, 0.0, 0.0, 0.0, 0.0, shear_modulus],
        ],
        dtype=np.float64,
    )


def hex8_element_stiffness(
    youngs_modulus: float,
    poisson_ratio: float,
    *,
    dimensions: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> NDArray[np.float64]:
    """Return the 24-by-24 stiffness of an axis-aligned rectangular Hex8 element."""

    constitutive_matrix = isotropic_elasticity_matrix(youngs_modulus, poisson_ratio)
    hx, hy, hz = _validate_dimensions(dimensions)
    inverse_jacobian = np.diag((2.0 / hx, 2.0 / hy, 2.0 / hz))
    jacobian_determinant = hx * hy * hz / 8.0
    stiffness = np.zeros((24, 24), dtype=np.float64)

    for xi, eta, zeta in product(_GAUSS_POINTS, repeat=3):
        reference_gradients = _shape_function_gradients(xi, eta, zeta)
        physical_gradients = reference_gradients @ inverse_jacobian
        strain_displacement = _strain_displacement_matrix(physical_gradients)
        stiffness += (
            strain_displacement.T
            @ constitutive_matrix
            @ strain_displacement
            * jacobian_determinant
        )

    return stiffness


def _shape_function_gradients(
    xi: float,
    eta: float,
    zeta: float,
) -> NDArray[np.float64]:
    node_xi = _HEX8_REFERENCE_COORDINATES[:, 0]
    node_eta = _HEX8_REFERENCE_COORDINATES[:, 1]
    node_zeta = _HEX8_REFERENCE_COORDINATES[:, 2]

    return np.column_stack(
        (
            node_xi * (1.0 + node_eta * eta) * (1.0 + node_zeta * zeta),
            node_eta * (1.0 + node_xi * xi) * (1.0 + node_zeta * zeta),
            node_zeta * (1.0 + node_xi * xi) * (1.0 + node_eta * eta),
        )
    ) / 8.0


def _strain_displacement_matrix(
    physical_gradients: NDArray[np.float64],
) -> NDArray[np.float64]:
    matrix = np.zeros((6, 24), dtype=np.float64)
    for local_node, (derivative_x, derivative_y, derivative_z) in enumerate(
        physical_gradients
    ):
        column = 3 * local_node
        matrix[0, column] = derivative_x
        matrix[1, column + 1] = derivative_y
        matrix[2, column + 2] = derivative_z
        matrix[3, column] = derivative_y
        matrix[3, column + 1] = derivative_x
        matrix[4, column + 1] = derivative_z
        matrix[4, column + 2] = derivative_y
        matrix[5, column] = derivative_z
        matrix[5, column + 2] = derivative_x
    return matrix


def _validate_dimensions(
    dimensions: tuple[float, float, float],
) -> tuple[float, float, float]:
    if len(dimensions) != 3:
        raise ValueError("dimensions must contain exactly three values")
    hx, hy, hz = dimensions
    return (
        _positive_finite("hx", hx),
        _positive_finite("hy", hy),
        _positive_finite("hz", hz),
    )


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
