import json

import pytest
from pydantic import ValidationError

from topolab.experiment import (
    CASE_SCHEMA_VERSION,
    ExperimentCase,
    build_case_id,
    canonical_case_json,
)
from topolab.problem import (
    FaceLoadDefinition,
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)


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
