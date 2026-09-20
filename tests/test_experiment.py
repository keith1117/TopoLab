import json

import numpy as np
import pytest
from pydantic import ValidationError

from topolab.experiment import (
    CASE_SCHEMA_VERSION,
    INPUT_CHANNEL_NAMES,
    ExperimentCase,
    build_case_id,
    canonical_case_json,
    encode_case,
    project_design_density,
)
from topolab.mesh import generate_structured_hex8
from topolab.problem import (
    FaceLoadDefinition,
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)
from topolab.simp import apply_density_filter, build_density_filter


def test_experiment_case_has_stable_identity_and_json_round_trip() -> None:
    problem = _problem()

    case = ExperimentCase.from_problem(problem)
    restored = ExperimentCase.model_validate_json(case.model_dump_json())

    assert restored == case
    assert case.schema_version == CASE_SCHEMA_VERSION
    assert case.case_id == build_case_id(problem)
    assert json.loads(case.canonical_identity_json()) == json.loads(
        canonical_case_json(problem)
    )
    assert case.case_id == (
        "tlcase-v1-35ffd0d15a9fe631f3d5fe629e1c5f162096a3e0da8f49eda6d96d73d6cfc0d2"
    )


def test_case_identity_normalizes_order_direction_aliases_and_repeated_supports() -> None:
    first = _problem(
        supports=(
            FixedFaceSupportDefinition(
                axis="x",
                side="min",
                directions=("z", 0),
            ),
            FixedFaceSupportDefinition(
                axis="x",
                side="min",
                directions=(1, "x"),
            ),
        ),
        loads=(
            FaceLoadDefinition(
                axis="x",
                side="max",
                direction=2,
                total=-0.25,
            ),
            PointLoadDefinition(node=11, direction=1, magnitude=-0.75),
        ),
    )
    second = _problem(
        supports=(
            FixedFaceSupportDefinition(
                axis="x",
                side="min",
                directions=("x", "y", "z"),
            ),
        ),
        loads=(
            PointLoadDefinition(node=11, direction="y", magnitude=-0.75),
            FaceLoadDefinition(
                axis="x",
                side="max",
                direction="z",
                total=-0.25,
            ),
        ),
    )

    first_case = ExperimentCase.from_problem(first)
    second_case = ExperimentCase.from_problem(second)

    assert first_case == second_case
    assert first_case.problem == second_case.problem
    assert build_case_id(first) == build_case_id(second)
    assert canonical_case_json(first) == canonical_case_json(second)


def test_all_case_identity_sections_change_the_identifier() -> None:
    base = _problem()
    variants = (
        _problem(element_counts=(3, 1, 1), loaded_node=11),
        _problem(lengths=(4.0, 1.0, 1.0)),
        _problem(solid_modulus=2000.0),
        _problem(
            supports=(FixedFaceSupportDefinition(axis="y", side="min"),),
        ),
        _problem(load_magnitude=-2.0),
        _problem(volume_fraction=0.4),
        _problem(filter_radius=2.0),
        _problem(convergence_tolerance=0.005),
    )

    identifiers = {build_case_id(base), *(build_case_id(case) for case in variants)}

    assert len(identifiers) == len(variants) + 1


def test_experiment_case_rejects_initial_density_and_stale_identity() -> None:
    problem = _problem(initial_density=(0.5, 0.5))

    with pytest.raises(ValueError, match="must not define initial_density"):
        ExperimentCase.from_problem(problem)

    valid = ExperimentCase.from_problem(_problem())
    stale_payload = valid.model_dump(mode="json")
    stale_payload["problem"]["optimization"]["volume_fraction"] = 0.4  # type: ignore[index]
    with pytest.raises(ValidationError, match="case_id does not match"):
        ExperimentCase.model_validate(stale_payload)


def test_experiment_case_rejects_unknown_or_changed_schema_fields() -> None:
    payload = ExperimentCase.from_problem(_problem()).model_dump(mode="json")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        ExperimentCase.model_validate(payload)

    payload = ExperimentCase.from_problem(_problem()).model_dump(mode="json")
    payload["schema_version"] = "topolab.m0.case.v2"
    with pytest.raises(ValidationError):
        ExperimentCase.model_validate(payload)


def test_case_encoding_has_frozen_shape_axes_supports_coordinates_and_volume() -> None:
    case = ExperimentCase.from_problem(
        _problem(
            element_counts=(2, 2, 2),
            lengths=(2.0, 4.0, 6.0),
            supports=(
                FixedFaceSupportDefinition(
                    axis="x",
                    side="min",
                    directions=("x", "z"),
                ),
            ),
        )
    )

    encoded = encode_case(case)

    assert encoded.input_tensor.shape == (10, 2, 2, 2)
    assert encoded.input_tensor.dtype == np.float32
    assert encoded.input_tensor.flags.c_contiguous
    assert INPUT_CHANNEL_NAMES == (
        "support_x",
        "support_y",
        "support_z",
        "load_x",
        "load_y",
        "load_z",
        "coord_x",
        "coord_y",
        "coord_z",
        "volume_fraction",
    )
    np.testing.assert_array_equal(encoded.input_tensor[0, :, :, 0], 1.0)
    np.testing.assert_array_equal(encoded.input_tensor[0, :, :, 1], 0.0)
    np.testing.assert_array_equal(encoded.input_tensor[1], 0.0)
    np.testing.assert_array_equal(encoded.input_tensor[2], encoded.input_tensor[0])
    np.testing.assert_array_equal(
        encoded.input_tensor[6],
        np.broadcast_to(np.array([0.25, 0.75], dtype=np.float32), (2, 2, 2)),
    )
    np.testing.assert_array_equal(
        encoded.input_tensor[7],
        np.broadcast_to(
            np.array([[0.25], [0.75]], dtype=np.float32),
            (2, 2, 2),
        ),
    )
    np.testing.assert_array_equal(
        encoded.input_tensor[8],
        np.broadcast_to(
            np.array([[[0.25]], [[0.75]]], dtype=np.float32),
            (2, 2, 2),
        ),
    )
    np.testing.assert_array_equal(encoded.input_tensor[9], 0.5)


def test_case_encoding_scatters_loads_conservatively_and_records_scale() -> None:
    case = ExperimentCase.from_problem(
        _problem(
            element_counts=(2, 2, 1),
            lengths=(2.0, 2.0, 1.0),
            loads=(
                PointLoadDefinition(node=13, direction="y", magnitude=-8.0),
                FaceLoadDefinition(
                    axis="x",
                    side="max",
                    direction="z",
                    total=4.0,
                ),
            ),
        )
    )

    encoded = encode_case(case)

    assert encoded.load_scale == pytest.approx(12.0, abs=1e-12)
    np.testing.assert_array_equal(encoded.input_tensor[3], 0.0)
    np.testing.assert_allclose(
        encoded.input_tensor[4],
        np.full((1, 2, 2), -1.0 / 6.0, dtype=np.float32),
        rtol=0.0,
        atol=1e-8,
    )
    assert float(np.sum(encoded.input_tensor[4], dtype=np.float64)) == pytest.approx(
        -8.0 / 12.0,
        abs=1e-7,
    )
    assert float(np.sum(encoded.input_tensor[5], dtype=np.float64)) == pytest.approx(
        4.0 / 12.0,
        abs=1e-7,
    )


def test_case_encoding_is_deterministic() -> None:
    case = ExperimentCase.from_problem(_problem())

    first = encode_case(case)
    second = encode_case(case)

    assert first.load_scale == second.load_scale
    np.testing.assert_array_equal(first.input_tensor, second.input_tensor)


def test_density_projection_matches_filtered_volume_and_x_fast_order() -> None:
    case = ExperimentCase.from_problem(
        _problem(
            element_counts=(3, 2, 1),
            lengths=(3.0, 2.0, 1.0),
            volume_fraction=0.4,
        )
    )
    raw = np.array(
        [[[[0.0, 0.2, 0.4], [0.6, 0.8, 1.0]]]],
        dtype=np.float32,
    )

    projected = project_design_density(case, raw)
    repeated = project_design_density(case, raw)

    assert projected.design_density.shape == (6,)
    assert projected.physical_density.shape == (6,)
    assert projected.design_density.dtype == np.float64
    assert projected.physical_density.dtype == np.float64
    assert np.all(projected.design_density >= 0.05)
    assert np.all(projected.design_density <= 1.0)
    assert float(np.mean(projected.physical_density)) == pytest.approx(0.4, abs=1e-6)
    assert np.all(np.diff(projected.design_density) >= 0.0)
    np.testing.assert_array_equal(projected.design_density, repeated.design_density)
    np.testing.assert_array_equal(projected.physical_density, repeated.physical_density)

    mesh = generate_structured_hex8(3, 2, 1, lengths=(3.0, 2.0, 1.0))
    density_filter = build_density_filter(mesh, radius=1.5)
    np.testing.assert_allclose(
        projected.physical_density,
        apply_density_filter(density_filter, projected.design_density),
        rtol=0.0,
        atol=1e-15,
    )


def test_uniform_density_projection_is_unchanged() -> None:
    case = ExperimentCase.from_problem(_problem(volume_fraction=0.4))
    raw = np.full((1, 1, 1, 2), 0.4, dtype=np.float32)

    projected = project_design_density(case, raw)

    np.testing.assert_allclose(projected.design_density, 0.4, rtol=0.0, atol=1e-7)
    np.testing.assert_allclose(projected.physical_density, 0.4, rtol=0.0, atol=1e-7)


@pytest.mark.parametrize(
    ("raw_density", "error_type", "message"),
    [
        (np.zeros((2,), dtype=np.float32), ValueError, "must have shape"),
        (
            np.zeros((1, 1, 1, 2), dtype=np.int64),
            TypeError,
            "floating-point dtype",
        ),
        (
            np.array([[[[0.5, np.nan]]]], dtype=np.float32),
            ValueError,
            "only finite",
        ),
        (
            np.array([[[[-0.1, 0.5]]]], dtype=np.float32),
            ValueError,
            r"interval \[0, 1\]",
        ),
        (
            np.array([[[[0.5, 1.1]]]], dtype=np.float32),
            ValueError,
            r"interval \[0, 1\]",
        ),
    ],
)
def test_density_projection_rejects_invalid_model_fields(
    raw_density: np.ndarray,
    error_type: type[Exception],
    message: str,
) -> None:
    case = ExperimentCase.from_problem(_problem())

    with pytest.raises(error_type, match=message):
        project_design_density(case, raw_density)  # type: ignore[arg-type]


def test_case_encoding_rejects_a_zero_resultant_load_vector() -> None:
    case = ExperimentCase.from_problem(
        _problem(
            loads=(
                PointLoadDefinition(node=11, direction="y", magnitude=-1.0),
                PointLoadDefinition(node=11, direction="y", magnitude=1.0),
            )
        )
    )

    with pytest.raises(ValueError, match="loads cancel to a zero load vector"):
        encode_case(case)


def _problem(
    *,
    element_counts: tuple[int, int, int] = (2, 1, 1),
    lengths: tuple[float, float, float] = (2.0, 1.0, 1.0),
    solid_modulus: float = 1000.0,
    supports: tuple[FixedFaceSupportDefinition, ...] | None = None,
    loads: tuple[PointLoadDefinition | FaceLoadDefinition, ...] | None = None,
    loaded_node: int = 11,
    load_magnitude: float = -1.0,
    volume_fraction: float = 0.5,
    filter_radius: float = 1.5,
    convergence_tolerance: float = 0.01,
    initial_density: tuple[float, ...] | None = None,
) -> TopologyProblem:
    return TopologyProblem(
        mesh=MeshDefinition(element_counts=element_counts, lengths=lengths),
        material=MaterialDefinition(
            solid_modulus=solid_modulus,
            minimum_modulus=1.0,
            poisson_ratio=0.3,
        ),
        supports=supports
        or (FixedFaceSupportDefinition(axis="x", side="min"),),
        loads=loads
        or (
            PointLoadDefinition(
                node=loaded_node,
                direction="y",
                magnitude=load_magnitude,
            ),
        ),
        optimization=OptimizationDefinition(
            volume_fraction=volume_fraction,
            filter_radius=filter_radius,
            minimum_density=0.05,
            convergence_tolerance=convergence_tolerance,
            max_iterations=60,
        ),
        initial_density=initial_density,
    )
