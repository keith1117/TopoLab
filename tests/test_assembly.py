import numpy as np
import pytest
from scipy.sparse import csr_matrix, eye

from topolab.fem import (
    assemble_global_stiffness,
    hex8_element_stiffness,
    solve_linear_static,
)
from topolab.mesh import Hex8Mesh, generate_structured_hex8

DENSE_SPARSE_RELATIVE_TOLERANCE = 1e-9
EQUILIBRIUM_RELATIVE_TOLERANCE = 1e-10
SYMMETRY_RELATIVE_TOLERANCE = 1e-10


def test_sparse_assembly_matches_independent_dense_scatter() -> None:
    mesh = generate_structured_hex8(2, 1, 1, lengths=(2.0, 1.0, 1.0))
    element_stiffness = hex8_element_stiffness(1000.0, 0.3)

    sparse_stiffness = assemble_global_stiffness(mesh, element_stiffness)
    dense_stiffness = np.zeros(sparse_stiffness.shape)
    for element_dofs in mesh.element_dofs:
        dense_stiffness[np.ix_(element_dofs, element_dofs)] += element_stiffness

    assert isinstance(sparse_stiffness, csr_matrix)
    assert sparse_stiffness.has_canonical_format
    np.testing.assert_allclose(
        sparse_stiffness.toarray(),
        dense_stiffness,
        rtol=DENSE_SPARSE_RELATIVE_TOLERANCE,
        atol=0.0,
    )
    asymmetry = sparse_stiffness - sparse_stiffness.T
    symmetry_residual = np.linalg.norm(asymmetry.data) / np.linalg.norm(
        sparse_stiffness.data
    )
    assert symmetry_residual <= SYMMETRY_RELATIVE_TOLERANCE


def test_sparse_solve_matches_dense_reduced_system_and_balances_load() -> None:
    mesh, stiffness = _two_element_system()
    constrained_dofs = _dofs_on_x_plane(mesh, x_coordinate=0.0)
    loads = np.zeros(stiffness.shape[0])
    loaded_node = _node_at(mesh, (2.0, 1.0, 1.0))
    loads[3 * loaded_node + 1] = -1.0

    result = solve_linear_static(stiffness, loads, constrained_dofs)

    free_dofs = np.setdiff1d(np.arange(stiffness.shape[0]), constrained_dofs)
    dense_reduced = stiffness.toarray()[np.ix_(free_dofs, free_dofs)]
    expected_free_displacements = np.linalg.solve(dense_reduced, loads[free_dofs])
    np.testing.assert_allclose(
        result.displacements[free_dofs],
        expected_free_displacements,
        rtol=DENSE_SPARSE_RELATIVE_TOLERANCE,
        atol=1e-12,
    )
    np.testing.assert_array_equal(result.displacements[constrained_dofs], 0.0)
    np.testing.assert_allclose(
        result.reactions[free_dofs],
        0.0,
        rtol=0.0,
        atol=EQUILIBRIUM_RELATIVE_TOLERANCE,
    )
    total_load = loads.reshape(-1, 3).sum(axis=0)
    total_reaction = result.reactions.reshape(-1, 3).sum(axis=0)
    np.testing.assert_allclose(
        total_load + total_reaction,
        0.0,
        rtol=0.0,
        atol=EQUILIBRIUM_RELATIVE_TOLERANCE,
    )


@pytest.mark.parametrize(
    "element_stiffness",
    [
        np.zeros((23, 24)),
        np.full((24, 24), np.nan),
    ],
)
def test_sparse_assembly_rejects_invalid_element_matrix(
    element_stiffness: np.ndarray,
) -> None:
    mesh = generate_structured_hex8(1, 1, 1)

    with pytest.raises(ValueError):
        assemble_global_stiffness(mesh, element_stiffness)


def test_solve_rejects_missing_loads_or_constraints() -> None:
    _, stiffness = _two_element_system()
    loads = np.zeros(stiffness.shape[0])

    with pytest.raises(ValueError, match="loads must contain at least one nonzero value"):
        solve_linear_static(stiffness, loads, np.array([0], dtype=np.int64))

    loads[-1] = 1.0
    with pytest.raises(ValueError, match="constrained_dofs must contain at least one DOF"):
        solve_linear_static(stiffness, loads, np.array([], dtype=np.int64))


@pytest.mark.parametrize(
    ("constrained_dofs", "error_type", "message"),
    [
        (np.array([0.0]), TypeError, "one-dimensional integer array"),
        (np.array([[0]], dtype=np.int64), TypeError, "one-dimensional integer array"),
        (np.array([-1], dtype=np.int64), ValueError, "out-of-range DOF"),
        (np.array([0, 0], dtype=np.int64), ValueError, "must not contain duplicates"),
    ],
)
def test_solve_rejects_invalid_constrained_dofs(
    constrained_dofs: np.ndarray,
    error_type: type[Exception],
    message: str,
) -> None:
    _, stiffness = _two_element_system()
    loads = np.zeros(stiffness.shape[0])
    loads[-1] = 1.0

    with pytest.raises(error_type, match=message):
        solve_linear_static(stiffness, loads, constrained_dofs)


def test_solve_rejects_singular_reduced_stiffness() -> None:
    stiffness = csr_matrix(np.diag([1.0, 0.0, 1.0]))
    loads = np.array([0.0, 1.0, 0.0])

    with pytest.raises(ValueError, match="reduced stiffness is singular"):
        solve_linear_static(stiffness, loads, np.array([0], dtype=np.int64))


def test_solve_rejects_partial_support_that_leaves_rigid_body_modes() -> None:
    mesh = generate_structured_hex8(1, 1, 1)
    element_stiffness = hex8_element_stiffness(1.0, 0.3)
    stiffness = assemble_global_stiffness(mesh, element_stiffness)
    loads = np.zeros(stiffness.shape[0])
    loads[-1] = 1.0
    only_node_zero_fixed = np.array([0, 1, 2], dtype=np.int64)

    with pytest.raises(ValueError, match="constraints may leave rigid body modes"):
        solve_linear_static(stiffness, loads, only_node_zero_fixed)


def test_solve_rejects_non_csr_or_nonsquare_stiffness() -> None:
    loads = np.array([0.0, 1.0])
    constrained_dofs = np.array([0], dtype=np.int64)

    with pytest.raises(TypeError, match="scipy.sparse.csr_matrix"):
        solve_linear_static(np.eye(2), loads, constrained_dofs)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="stiffness must be square"):
        solve_linear_static(csr_matrix((2, 3)), loads, constrained_dofs)


def test_solve_rejects_wrong_load_shape_and_nonfinite_load() -> None:
    stiffness = eye(3, format="csr")
    constrained_dofs = np.array([0], dtype=np.int64)

    with pytest.raises(ValueError, match=r"loads must have shape \(3,\)"):
        solve_linear_static(stiffness, np.zeros((3, 1)), constrained_dofs)

    with pytest.raises(ValueError, match="loads must contain only finite values"):
        solve_linear_static(stiffness, np.array([0.0, np.nan, 1.0]), constrained_dofs)


def _two_element_system() -> tuple[Hex8Mesh, csr_matrix]:
    mesh = generate_structured_hex8(2, 1, 1, lengths=(2.0, 1.0, 1.0))
    element_stiffness = hex8_element_stiffness(1000.0, 0.3)
    return mesh, assemble_global_stiffness(mesh, element_stiffness)


def _dofs_on_x_plane(mesh: Hex8Mesh, x_coordinate: float) -> np.ndarray:
    nodes = np.flatnonzero(np.isclose(mesh.coordinates[:, 0], x_coordinate))
    return (3 * nodes[:, np.newaxis] + np.arange(3)).ravel()


def _node_at(mesh: Hex8Mesh, coordinates: tuple[float, float, float]) -> int:
    matching_nodes = np.flatnonzero(
        np.all(np.isclose(mesh.coordinates, coordinates), axis=1)
    )
    assert matching_nodes.size == 1
    return int(matching_nodes[0])
