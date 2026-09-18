"""Finite-element building blocks for small-strain 3D elasticity."""

from collections.abc import Sequence
from dataclasses import dataclass
from itertools import product
from math import isfinite, sqrt
from numbers import Integral, Real

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import coo_matrix, csr_matrix  # type: ignore[import-untyped]
from scipy.sparse.linalg import splu  # type: ignore[import-untyped]

from topolab.mesh import HEX8_LOCAL_NODE_OFFSETS, Hex8Mesh
from topolab.model import Axis, FaceLoad, FaceSide, FixedFaceSupport, Load, PointLoad

_HEX8_REFERENCE_COORDINATES = 2.0 * np.asarray(HEX8_LOCAL_NODE_OFFSETS, dtype=np.float64) - 1.0
_GAUSS_POINTS = (-1.0 / sqrt(3.0), 1.0 / sqrt(3.0))


@dataclass(frozen=True, slots=True)
class LinearStaticResult:
    """Displacements and reactions for a zero-prescribed-displacement solve."""

    displacements: NDArray[np.float64]
    reactions: NDArray[np.float64]


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


def assemble_global_stiffness(
    mesh: Hex8Mesh,
    element_stiffness: NDArray[np.float64],
    *,
    element_factors: NDArray[np.float64] | None = None,
) -> csr_matrix:
    """Assemble optionally scaled Hex8 element matrices into a global CSR matrix."""

    element_stiffness = np.asarray(element_stiffness, dtype=np.float64)
    if element_stiffness.shape != (24, 24):
        raise ValueError("element_stiffness must have shape (24, 24)")
    if not np.all(np.isfinite(element_stiffness)):
        raise ValueError("element_stiffness must contain only finite values")

    element_dofs = mesh.element_dofs
    number_of_elements = element_dofs.shape[0]
    if element_factors is None:
        factors = np.ones(number_of_elements, dtype=np.float64)
    else:
        factors = np.asarray(element_factors, dtype=np.float64)
        if factors.shape != (number_of_elements,):
            raise ValueError(
                f"element_factors must have shape ({number_of_elements},)"
            )
        if not np.all(np.isfinite(factors)) or np.any(factors <= 0.0):
            raise ValueError("element_factors must contain only positive finite values")
    row_indices = np.broadcast_to(
        element_dofs[:, :, np.newaxis],
        (number_of_elements, 24, 24),
    ).ravel()
    column_indices = np.broadcast_to(
        element_dofs[:, np.newaxis, :],
        (number_of_elements, 24, 24),
    ).ravel()
    values = (factors[:, np.newaxis, np.newaxis] * element_stiffness).ravel()
    number_of_dofs = 3 * mesh.coordinates.shape[0]

    stiffness = coo_matrix(
        (values, (row_indices, column_indices)),
        shape=(number_of_dofs, number_of_dofs),
    ).tocsr()
    stiffness.sum_duplicates()
    stiffness.sort_indices()
    return stiffness


def solve_linear_static(
    stiffness: csr_matrix,
    loads: NDArray[np.float64],
    constrained_dofs: NDArray[np.int64],
) -> LinearStaticResult:
    """Solve a sparse linear-elastic system with zero prescribed displacements."""

    if not isinstance(stiffness, csr_matrix):
        raise TypeError("stiffness must be a scipy.sparse.csr_matrix")
    if stiffness.shape[0] != stiffness.shape[1]:
        raise ValueError("stiffness must be square")
    if not np.all(np.isfinite(stiffness.data)):
        raise ValueError("stiffness must contain only finite values")

    number_of_dofs = stiffness.shape[0]
    load_vector = np.asarray(loads, dtype=np.float64)
    if load_vector.shape != (number_of_dofs,):
        raise ValueError(f"loads must have shape ({number_of_dofs},)")
    if not np.all(np.isfinite(load_vector)):
        raise ValueError("loads must contain only finite values")
    if not np.any(load_vector):
        raise ValueError("loads must contain at least one nonzero value")

    constrained = np.asarray(constrained_dofs)
    if constrained.ndim != 1 or not np.issubdtype(constrained.dtype, np.integer):
        raise TypeError("constrained_dofs must be a one-dimensional integer array")
    constrained = constrained.astype(np.int64, copy=False)
    if constrained.size == 0:
        raise ValueError("constrained_dofs must contain at least one DOF")
    if np.any(constrained < 0) or np.any(constrained >= number_of_dofs):
        raise ValueError("constrained_dofs contains an out-of-range DOF")
    if np.unique(constrained).size != constrained.size:
        raise ValueError("constrained_dofs must not contain duplicates")

    free_mask = np.ones(number_of_dofs, dtype=np.bool_)
    free_mask[constrained] = False
    free_dofs = np.flatnonzero(free_mask)
    if free_dofs.size == 0:
        raise ValueError("at least one unconstrained DOF is required")

    reduced_stiffness = stiffness[free_dofs][:, free_dofs].tocsc()
    try:
        factorization = splu(reduced_stiffness)
    except RuntimeError as error:
        raise ValueError(
            "reduced stiffness is singular; constraints may leave rigid body modes"
        ) from error
    pivot_magnitudes = np.abs(factorization.U.diagonal())
    pivot_scale = float(np.max(pivot_magnitudes))
    singular_threshold = (
        np.finfo(np.float64).eps * reduced_stiffness.shape[0] * pivot_scale
    )
    if pivot_scale == 0.0 or float(np.min(pivot_magnitudes)) <= singular_threshold:
        raise ValueError(
            "reduced stiffness is singular; constraints may leave rigid body modes"
        )

    free_displacements = factorization.solve(load_vector[free_dofs])
    if not np.all(np.isfinite(free_displacements)):
        raise ValueError(
            "reduced stiffness solve was non-finite; constraints may leave rigid body modes"
        )

    displacements = np.zeros(number_of_dofs, dtype=np.float64)
    displacements[free_dofs] = free_displacements
    reactions = np.asarray(stiffness @ displacements).reshape(-1) - load_vector
    return LinearStaticResult(displacements=displacements, reactions=reactions)


def select_face_nodes(
    mesh: Hex8Mesh,
    axis: Axis,
    side: FaceSide,
) -> NDArray[np.int64]:
    """Return nodes on a minimum or maximum structured-domain face."""

    axis_index = _axis_index(axis)
    if side not in ("min", "max"):
        raise ValueError("side must be 'min' or 'max'")
    coordinate = 0.0 if side == "min" else mesh.lengths[axis_index]
    return np.flatnonzero(mesh.coordinates[:, axis_index] == coordinate)


def build_constrained_dofs(
    mesh: Hex8Mesh,
    supports: Sequence[FixedFaceSupport],
) -> NDArray[np.int64]:
    """Discretize fixed-face supports into sorted unique global DOF indices."""

    if len(supports) == 0:
        raise ValueError("supports must contain at least one support")

    support_dofs: list[NDArray[np.int64]] = []
    for support in supports:
        if not isinstance(support, FixedFaceSupport):
            raise TypeError("supports must contain only FixedFaceSupport objects")
        direction_indices = _direction_indices(support.directions)
        face_nodes = select_face_nodes(mesh, support.axis, support.side)
        dofs = (
            3 * face_nodes[:, np.newaxis]
            + np.asarray(direction_indices, dtype=np.int64)
        ).ravel()
        support_dofs.append(dofs)

    return np.unique(np.concatenate(support_dofs))


def build_load_vector(
    mesh: Hex8Mesh,
    loads: Sequence[Load],
) -> NDArray[np.float64]:
    """Discretize and superpose point and equal-node face loads."""

    if len(loads) == 0:
        raise ValueError("loads must contain at least one load")

    number_of_nodes = mesh.coordinates.shape[0]
    load_vector = np.zeros(3 * number_of_nodes, dtype=np.float64)
    for load in loads:
        if isinstance(load, PointLoad):
            node = _node_index(load.node, number_of_nodes)
            direction = _direction_index(load.direction)
            magnitude = _nonzero_finite("magnitude", load.magnitude)
            load_vector[3 * node + direction] += magnitude
        elif isinstance(load, FaceLoad):
            direction = _direction_index(load.direction)
            total = _nonzero_finite("total", load.total)
            face_nodes = select_face_nodes(mesh, load.axis, load.side)
            load_vector[3 * face_nodes + direction] += total / face_nodes.size
        else:
            raise TypeError("loads must contain only PointLoad or FaceLoad objects")

    if not np.any(load_vector):
        raise ValueError("loads cancel to a zero load vector")
    return load_vector


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


def _axis_index(axis: Axis) -> int:
    if axis not in ("x", "y", "z"):
        raise ValueError("axis must be 'x', 'y', or 'z'")
    return {"x": 0, "y": 1, "z": 2}[axis]


def _direction_index(direction: object) -> int:
    if isinstance(direction, bool):
        raise ValueError("direction must be 'x', 'y', 'z', 0, 1, or 2")
    if isinstance(direction, str):
        if direction not in ("x", "y", "z"):
            raise ValueError("direction must be 'x', 'y', 'z', 0, 1, or 2")
        return {"x": 0, "y": 1, "z": 2}[direction]
    if isinstance(direction, Integral):
        index = int(direction)
        if 0 <= index <= 2:
            return index
    raise ValueError("direction must be 'x', 'y', 'z', 0, 1, or 2")


def _direction_indices(directions: Sequence[object]) -> tuple[int, ...]:
    if len(directions) == 0:
        raise ValueError("directions must contain at least one direction")
    indices = tuple(_direction_index(direction) for direction in directions)
    if len(set(indices)) != len(indices):
        raise ValueError("directions must not contain duplicate components")
    return indices


def _node_index(node: object, number_of_nodes: int) -> int:
    if isinstance(node, bool) or not isinstance(node, Integral):
        raise TypeError("node must be an integer")
    index = int(node)
    if index < 0 or index >= number_of_nodes:
        raise ValueError("node is outside the mesh")
    return index


def _nonzero_finite(name: str, value: float) -> float:
    result = _finite_real(name, value)
    if result == 0.0:
        raise ValueError(f"{name} must be nonzero")
    return result


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
