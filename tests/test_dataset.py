import json

import pytest
from pydantic import ValidationError

from topolab.dataset import (
    DATASET_MANIFEST_VERSION,
    DATASET_SAMPLE_VERSION,
    SPLIT_CONTRACT_VERSION,
    DatasetEnvironment,
    DatasetManifest,
    assign_case_split,
)
from topolab.experiment import INPUT_CHANNEL_NAMES, ExperimentCase
from topolab.problem import (
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)


def test_frozen_split_contract_assigns_known_cases_and_direction_ood() -> None:
    cases = _partition_cases()

    assert [assign_case_split(case) for case in cases] == [
        "train",
        "validation",
        "test",
        "ood",
    ]
    assert cases[0].case_id == (
        "tlcase-v1-e07563d417766dcc685bc99413b01c5c9f4b08d4592bde6c06588288b28a547b"
    )
    assert cases[1].case_id == (
        "tlcase-v1-2a81a1de753b358bda7d3a9743543c4ca0cdf21c4bc48fe0044e9ec79c33f5e5"
    )
    assert cases[2].case_id == (
        "tlcase-v1-c8026202fba0a6bc9cb0065faa101927fe1816383b19bbc686dcb5045080aed7"
    )


def test_manifest_is_versioned_sorted_and_json_round_trips() -> None:
    cases = _partition_cases()

    manifest = DatasetManifest.from_cases(
        reversed(cases),
        source_revision="b" * 40,
        environment=_environment(),
    )
    restored = DatasetManifest.model_validate_json(manifest.model_dump_json())

    assert restored == manifest
    assert manifest.manifest_version == DATASET_MANIFEST_VERSION
    assert manifest.split_contract_version == SPLIT_CONTRACT_VERSION
    assert manifest.input_channels == INPUT_CHANNEL_NAMES
    assert manifest.tensor_dtype == "float32"
    assert manifest.tensor_axis_order == "channel,z,y,x"
    assert manifest.split_counts.model_dump() == {
        "train": 1,
        "validation": 1,
        "test": 1,
        "ood": 1,
    }
    assert tuple(sample.case.case_id for sample in manifest.samples) == tuple(
        sorted(case.case_id for case in cases)
    )
    assert {sample.sample_version for sample in manifest.samples} == {
        DATASET_SAMPLE_VERSION
    }
    assert {sample.load_scale for sample in manifest.samples} == {1.0}
    assert all(sample.case.problem.initial_density is None for sample in manifest.samples)
    assert json.loads(manifest.model_dump_json())["source_tree_clean"] is True


def test_manifest_rejects_duplicate_case_identity() -> None:
    cases = _partition_cases()

    with pytest.raises(ValidationError, match="unique case IDs"):
        DatasetManifest.from_cases(
            (*cases, cases[0]),
            source_revision="b" * 40,
            environment=_environment(),
        )


def test_manifest_rejects_tampered_split_count_and_load_scale() -> None:
    payload = _manifest().model_dump(mode="json")
    payload["samples"][0]["split"] = "train"  # type: ignore[index]
    with pytest.raises(ValidationError, match="split does not match"):
        DatasetManifest.model_validate(payload)

    payload = _manifest().model_dump(mode="json")
    payload["split_counts"]["train"] = 2  # type: ignore[index]
    with pytest.raises(ValidationError, match="split_counts do not match"):
        DatasetManifest.model_validate(payload)

    payload = _manifest().model_dump(mode="json")
    payload["samples"][0]["load_scale"] = 2.0  # type: ignore[index]
    with pytest.raises(ValidationError, match="load_scale does not match"):
        DatasetManifest.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("manifest_version", "topolab.m0.dataset.v2"),
        ("source_revision", "not-a-commit"),
        ("source_tree_clean", False),
        ("tensor_dtype", "float64"),
        ("tensor_axis_order", "channel,x,y,z"),
    ],
)
def test_manifest_rejects_changed_frozen_metadata(field: str, value: object) -> None:
    payload = _manifest().model_dump(mode="json")
    payload[field] = value

    with pytest.raises(ValidationError):
        DatasetManifest.model_validate(payload)


def test_manifest_rejects_changed_channels_unknown_fields_and_bad_lock_digest() -> None:
    payload = _manifest().model_dump(mode="json")
    payload["input_channels"][0] = "fixed_x"  # type: ignore[index]
    with pytest.raises(ValidationError, match="frozen M0 channel order"):
        DatasetManifest.model_validate(payload)

    payload = _manifest().model_dump(mode="json")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        DatasetManifest.model_validate(payload)

    payload = _manifest().model_dump(mode="json")
    payload["environment"]["lockfile_sha256"] = "a" * 63  # type: ignore[index]
    with pytest.raises(ValidationError):
        DatasetManifest.model_validate(payload)


def test_manifest_rejects_mixed_cohorts_and_unmatched_ood_cases() -> None:
    cases = _partition_cases()
    changed_material = ExperimentCase.from_problem(
        _problem(volume_fraction=0.4, solid_modulus=2000.0)
    )
    with pytest.raises(ValidationError, match="fixed-shape cohort"):
        DatasetManifest.from_cases(
            (*cases, changed_material),
            source_revision="b" * 40,
            environment=_environment(),
        )

    unmatched_ood = ExperimentCase.from_problem(
        _problem(volume_fraction=0.4, load_direction="z")
    )
    with pytest.raises(ValidationError, match="matched ID counterpart"):
        DatasetManifest.from_cases(
            (*cases[:3], unmatched_ood),
            source_revision="b" * 40,
            environment=_environment(),
        )


@pytest.mark.parametrize("directions", [("x",), ("y", "z")])
def test_split_contract_rejects_out_of_contract_load_directions(
    directions: tuple[str, ...],
) -> None:
    problem = _problem()
    payload = problem.model_dump(mode="json")
    payload["loads"] = [
        {
            "kind": "point",
            "node": 11,
            "direction": direction,
            "magnitude": -1.0,
        }
        for direction in directions
    ]
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))

    with pytest.raises(ValueError, match="y-directed ID loads or z-directed OOD"):
        assign_case_split(case)


def _manifest() -> DatasetManifest:
    return DatasetManifest.from_cases(
        _partition_cases(),
        source_revision="b" * 40,
        environment=_environment(),
    )


def _partition_cases() -> tuple[ExperimentCase, ...]:
    train = ExperimentCase.from_problem(_problem(volume_fraction=0.06))
    validation = ExperimentCase.from_problem(_problem(volume_fraction=0.18))
    test = ExperimentCase.from_problem(_problem(volume_fraction=0.08))
    ood = ExperimentCase.from_problem(
        _problem(volume_fraction=0.06, load_direction="z")
    )
    return train, validation, test, ood


def _environment() -> DatasetEnvironment:
    return DatasetEnvironment(
        python_version="3.13.7",
        numpy_version="2.3.3",
        scipy_version="1.16.2",
        lockfile_sha256="a" * 64,
    )


def _problem(
    *,
    volume_fraction: float = 0.5,
    load_direction: str = "y",
    solid_modulus: float = 1000.0,
) -> TopologyProblem:
    return TopologyProblem(
        mesh=MeshDefinition(
            element_counts=(2, 1, 1),
            lengths=(2.0, 1.0, 1.0),
        ),
        material=MaterialDefinition(
            solid_modulus=solid_modulus,
            minimum_modulus=1.0,
            poisson_ratio=0.3,
        ),
        supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
        loads=(
            PointLoadDefinition(
                node=11,
                direction=load_direction,  # type: ignore[arg-type]
                magnitude=-1.0,
            ),
        ),
        optimization=OptimizationDefinition(
            volume_fraction=volume_fraction,
            filter_radius=1.5,
            minimum_density=0.05,
            convergence_tolerance=0.01,
            max_iterations=60,
        ),
    )
