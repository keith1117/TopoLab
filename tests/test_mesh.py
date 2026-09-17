import numpy as np
import pytest

from topolab.mesh import generate_structured_hex8


def test_single_element_coordinates_follow_x_fastest_indexing() -> None:
    mesh = generate_structured_hex8(1, 1, 1, lengths=(2.0, 4.0, 6.0))

    expected = np.array(
        [
            [0.0, 0.0, 0.0],
            [2.0, 0.0, 0.0],
            [0.0, 4.0, 0.0],
            [2.0, 4.0, 0.0],
            [0.0, 0.0, 6.0],
            [2.0, 0.0, 6.0],
            [0.0, 4.0, 6.0],
            [2.0, 4.0, 6.0],
        ]
    )
    np.testing.assert_array_equal(mesh.coordinates, expected)


def test_connectivity_uses_documented_local_node_order() -> None:
    mesh = generate_structured_hex8(2, 1, 1)

    expected = np.array(
        [
            [0, 1, 4, 3, 6, 7, 10, 9],
            [1, 2, 5, 4, 7, 8, 11, 10],
        ],
        dtype=np.int64,
    )
    np.testing.assert_array_equal(mesh.connectivity, expected)


def test_node_element_and_dof_indexing_are_consistent() -> None:
    nx, ny, nz = 2, 3, 2
    mesh = generate_structured_hex8(nx, ny, nz, lengths=(2.0, 3.0, 4.0))

    assert mesh.coordinates.shape == ((nx + 1) * (ny + 1) * (nz + 1), 3)
    assert mesh.connectivity.shape == (nx * ny * nz, 8)
    assert mesh.element_dofs.shape == (nx * ny * nz, 24)

    node_id = 2 + (nx + 1) * (1 + (ny + 1) * 2)
    np.testing.assert_array_equal(mesh.coordinates[node_id], [2.0, 1.0, 4.0])

    element_id = 1 + nx * (2 + ny * 1)
    origin_node = 1 + (nx + 1) * (2 + (ny + 1) * 1)
    assert mesh.connectivity[element_id, 0] == origin_node

    expected_dofs = (
        3 * mesh.connectivity[element_id, :, np.newaxis] + np.arange(3)
    ).reshape(24)
    np.testing.assert_array_equal(mesh.element_dofs[element_id], expected_dofs)


def test_every_element_has_positive_hex8_orientation() -> None:
    mesh = generate_structured_hex8(2, 3, 4, lengths=(3.0, 6.0, 2.0))
    reference_coordinates = np.array(
        [
            [-1.0, -1.0, -1.0],
            [1.0, -1.0, -1.0],
            [1.0, 1.0, -1.0],
            [-1.0, 1.0, -1.0],
            [-1.0, -1.0, 1.0],
            [1.0, -1.0, 1.0],
            [1.0, 1.0, 1.0],
            [-1.0, 1.0, 1.0],
        ]
    )
    center_shape_gradients = reference_coordinates / 8.0

    determinants = np.array(
        [
            np.linalg.det(mesh.coordinates[element_nodes].T @ center_shape_gradients)
            for element_nodes in mesh.connectivity
        ]
    )
    expected_determinant = (3.0 / 2) * (6.0 / 3) * (2.0 / 4) / 8
    np.testing.assert_allclose(determinants, expected_determinant, rtol=0.0, atol=1e-15)
    assert np.all(determinants > 0.0)


@pytest.mark.parametrize(
    ("counts", "error_type", "message"),
    [
        ((0, 1, 1), ValueError, "nx must be positive"),
        ((1, -1, 1), ValueError, "ny must be positive"),
        ((1, 1, 0), ValueError, "nz must be positive"),
        ((1.5, 1, 1), TypeError, "nx must be an integer"),
        ((1, True, 1), TypeError, "ny must be an integer"),
    ],
)
def test_invalid_element_counts_are_rejected(
    counts: tuple[object, object, object],
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        generate_structured_hex8(*counts)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("lengths", "error_type", "message"),
    [
        ((1.0, 0.0, 1.0), ValueError, "Ly must be positive and finite"),
        ((1.0, 1.0, -1.0), ValueError, "Lz must be positive and finite"),
        ((float("inf"), 1.0, 1.0), ValueError, "Lx must be positive and finite"),
        ((1.0, float("nan"), 1.0), ValueError, "Ly must be positive and finite"),
        ((True, 1.0, 1.0), TypeError, "Lx must be a real number"),
    ],
)
def test_invalid_physical_lengths_are_rejected(
    lengths: tuple[object, object, object],
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        generate_structured_hex8(1, 1, 1, lengths=lengths)  # type: ignore[arg-type]


def test_wrong_number_of_physical_lengths_is_rejected() -> None:
    with pytest.raises(ValueError, match="lengths must contain exactly three values"):
        generate_structured_hex8(1, 1, 1, lengths=(1.0, 1.0))  # type: ignore[arg-type]
