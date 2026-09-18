import numpy as np
import pytest

from topolab.fem import (
    assemble_global_stiffness,
    build_constrained_dofs,
    build_load_vector,
    hex8_element_stiffness,
    select_face_nodes,
    solve_linear_static,
)
from topolab.mesh import generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport, PointLoad

LOAD_CONSERVATION_ABSOLUTE_TOLERANCE = 1e-12


@pytest.mark.parametrize(
    ("axis", "side", "expected_nodes"),
    [
        ("x", "min", [0, 2, 4, 6]),
        ("x", "max", [1, 3, 5, 7]),
        ("y", "min", [0, 1, 4, 5]),
        ("y", "max", [2, 3, 6, 7]),
        ("z", "min", [0, 1, 2, 3]),
        ("z", "max", [4, 5, 6, 7]),
    ],
)
def test_face_selection_matches_documented_node_indexing(
    axis: str,
    side: str,
    expected_nodes: list[int],
) -> None:
    mesh = generate_structured_hex8(1, 1, 1)

    np.testing.assert_array_equal(
        select_face_nodes(mesh, axis, side),  # type: ignore[arg-type]
        expected_nodes,
    )


def test_fixed_face_support_maps_named_and_numeric_directions_to_dofs() -> None:
    mesh = generate_structured_hex8(1, 1, 1)
    support = FixedFaceSupport(axis="x", side="min", directions=("x", 2))

    constrained_dofs = build_constrained_dofs(mesh, [support])

    face_nodes = np.array([0, 2, 4, 6])
    expected = np.sort(
        (3 * face_nodes[:, np.newaxis] + np.array([0, 2])).ravel()
    )
    np.testing.assert_array_equal(constrained_dofs, expected)


def test_point_load_uses_signed_magnitude_not_direction_sign() -> None:
    mesh = generate_structured_hex8(1, 1, 1)

    load_vector = build_load_vector(
        mesh,
        [PointLoad(node=7, direction="y", magnitude=-7.5)],
    )

    expected = np.zeros(24)
    expected[3 * 7 + 1] = -7.5
    np.testing.assert_array_equal(load_vector, expected)


def test_face_load_distributes_total_exactly_once_over_selected_nodes() -> None:
    mesh = generate_structured_hex8(2, 2, 1, lengths=(2.0, 2.0, 1.0))
    face_nodes = select_face_nodes(mesh, "x", "max")

    load_vector = build_load_vector(
        mesh,
        [FaceLoad(axis="x", side="max", direction=2, total=-12.0)],
    )

    loaded_dofs = 3 * face_nodes + 2
    np.testing.assert_allclose(load_vector[loaded_dofs], -12.0 / face_nodes.size)
    assert np.count_nonzero(load_vector) == face_nodes.size
    assert load_vector[2::3].sum() == pytest.approx(
        -12.0,
        abs=LOAD_CONSERVATION_ABSOLUTE_TOLERANCE,
    )


def test_multiple_loads_superpose_on_the_same_dof() -> None:
    mesh = generate_structured_hex8(1, 1, 1)

    load_vector = build_load_vector(
        mesh,
        [
            PointLoad(node=7, direction="z", magnitude=-2.0),
            PointLoad(node=7, direction=2, magnitude=-3.0),
        ],
    )

    assert load_vector[3 * 7 + 2] == -5.0
    assert np.count_nonzero(load_vector) == 1


def test_support_and_face_load_integrate_with_sparse_solver() -> None:
    mesh = generate_structured_hex8(2, 1, 1, lengths=(2.0, 1.0, 1.0))
    element_stiffness = hex8_element_stiffness(1000.0, 0.3)
    stiffness = assemble_global_stiffness(mesh, element_stiffness)
    constrained_dofs = build_constrained_dofs(
        mesh,
        [FixedFaceSupport(axis="x", side="min")],
    )
    load_vector = build_load_vector(
        mesh,
        [FaceLoad(axis="x", side="max", direction="y", total=-4.0)],
    )

    result = solve_linear_static(stiffness, load_vector, constrained_dofs)

    total_load = load_vector.reshape(-1, 3).sum(axis=0)
    total_reaction = result.reactions.reshape(-1, 3).sum(axis=0)
    np.testing.assert_allclose(
        total_load + total_reaction,
        0.0,
        rtol=0.0,
        atol=LOAD_CONSERVATION_ABSOLUTE_TOLERANCE,
    )


def test_empty_supports_and_loads_are_rejected() -> None:
    mesh = generate_structured_hex8(1, 1, 1)

    with pytest.raises(ValueError, match="supports must contain at least one support"):
        build_constrained_dofs(mesh, [])
    with pytest.raises(ValueError, match="loads must contain at least one load"):
        build_load_vector(mesh, [])


@pytest.mark.parametrize(
    "support",
    [
        FixedFaceSupport(axis="x", side="min", directions=()),
        FixedFaceSupport(axis="x", side="min", directions=("x", 0)),
        FixedFaceSupport(axis="x", side="min", directions=(-1,)),  # type: ignore[arg-type]
        FixedFaceSupport(axis="q", side="min"),  # type: ignore[arg-type]
        FixedFaceSupport(axis="x", side="middle"),  # type: ignore[arg-type]
    ],
)
def test_invalid_support_selectors_and_directions_are_rejected(
    support: FixedFaceSupport,
) -> None:
    mesh = generate_structured_hex8(1, 1, 1)

    with pytest.raises(ValueError):
        build_constrained_dofs(mesh, [support])


@pytest.mark.parametrize(
    "load",
    [
        PointLoad(node=-1, direction="x", magnitude=1.0),
        PointLoad(node=8, direction="x", magnitude=1.0),
        PointLoad(node=0, direction=-1, magnitude=1.0),  # type: ignore[arg-type]
        PointLoad(node=0, direction="x", magnitude=0.0),
        PointLoad(node=0, direction="x", magnitude=float("nan")),
        FaceLoad(axis="x", side="max", direction="y", total=0.0),
        FaceLoad(axis="x", side="max", direction="y", total=float("inf")),
        FaceLoad(axis="q", side="max", direction="y", total=1.0),  # type: ignore[arg-type]
        FaceLoad(axis="x", side="middle", direction="y", total=1.0),  # type: ignore[arg-type]
    ],
)
def test_invalid_loads_are_rejected(load: object) -> None:
    mesh = generate_structured_hex8(1, 1, 1)

    with pytest.raises((TypeError, ValueError)):
        build_load_vector(mesh, [load])  # type: ignore[list-item]


def test_exactly_cancelling_loads_are_rejected() -> None:
    mesh = generate_structured_hex8(1, 1, 1)

    with pytest.raises(ValueError, match="loads cancel to a zero load vector"):
        build_load_vector(
            mesh,
            [
                PointLoad(node=0, direction="x", magnitude=1.0),
                PointLoad(node=0, direction=0, magnitude=-1.0),
            ],
        )
