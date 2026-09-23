import json
from collections import Counter

import pytest
from pydantic import ValidationError

from topolab.catalog import build_m0_case_catalog
from topolab.dataset import DatasetEnvironment
from topolab.experiment import ExperimentCase
from topolab.m2_dataset import (
    M2_CASE_CATALOG_ID,
    M2_CASE_CATALOG_ID_PREFIX,
    M2_CASE_CATALOG_VERSION,
    M2_DATASET_MANIFEST_VERSION,
    M2_DATASET_SAMPLE_VERSION,
    M2_SPLIT_CONTRACT_VERSION,
    M2CaseCatalog,
    M2DatasetManifest,
    assign_m2_case_splits,
    build_m2_case_catalog,
    build_m2_catalog_id,
    canonical_m2_catalog_json,
)
from topolab.problem import PointLoadDefinition


@pytest.fixture(scope="module")
def catalog() -> M2CaseCatalog:
    return build_m2_case_catalog()


@pytest.fixture(scope="module")
def manifest(catalog: M2CaseCatalog) -> M2DatasetManifest:
    return catalog.build_manifest(
        source_revision="b" * 40,
        environment=_environment(),
    )


def test_m2_catalog_has_frozen_identity_and_round_trips(
    catalog: M2CaseCatalog,
) -> None:
    restored = M2CaseCatalog.model_validate_json(catalog.model_dump_json())

    assert restored == catalog
    assert catalog.catalog_version == M2_CASE_CATALOG_VERSION
    assert catalog.catalog_id == M2_CASE_CATALOG_ID
    assert catalog.catalog_id == (
        "tlcatalog-m2-v1-af5b7fcffed5a070c3fc370a318605d3652e98c57b706f432203a7fd173fea12"
    )
    assert catalog.catalog_id.startswith(M2_CASE_CATALOG_ID_PREFIX)
    assert catalog.catalog_id == build_m2_catalog_id(reversed(catalog.cases))
    assert json.loads(catalog.canonical_identity_json()) == json.loads(
        canonical_m2_catalog_json(catalog.cases)
    )
    assert tuple(case.case_id for case in catalog.cases) == tuple(
        sorted(case.case_id for case in catalog.cases)
    )
    assert catalog.cases[0].case_id == (
        "tlcase-v1-0030af2e9d265d398665198304d7f4d34a4f51f2432394e1e07d9eb750de30d0"
    )
    assert catalog.cases[-1].case_id == (
        "tlcase-v1-fffa6c821de04e3168fcc2fe25e6b35a1f454a615069b2129db4a445fae7d5ac"
    )


def test_m2_catalog_exactly_enumerates_the_pre_registered_cohort(
    catalog: M2CaseCatalog,
) -> None:
    assert len(catalog.cases) == 756
    assert len({case.case_id for case in catalog.cases}) == 756
    assert {case.schema_version for case in catalog.cases} == {"topolab.m0.case.v1"}
    assert {case.problem.mesh.element_counts for case in catalog.cases} == {(12, 6, 3)}
    assert {case.problem.mesh.lengths for case in catalog.cases} == {(12.0, 6.0, 3.0)}
    assert {case.problem.optimization.volume_fraction for case in catalog.cases} == {
        0.2,
        0.25,
        0.3,
        0.35,
        0.4,
        0.45,
        0.5,
        0.55,
        0.6,
    }

    directions = Counter(_direction(case) for case in catalog.cases)
    assert directions == {"x": 252, "y": 252, "z": 252}

    nx, ny = 12, 6
    expected_nodes = {
        nx + (nx + 1) * (y_index + (ny + 1) * z_index)
        for y_index in range(7)
        for z_index in range(4)
    }
    assert {_point_load(case).node for case in catalog.cases} == expected_nodes

    signatures = {
        (
            _point_load(case).node,
            case.problem.optimization.volume_fraction,
            _direction(case),
        )
        for case in catalog.cases
    }
    assert len(signatures) == 756
    for loaded_node in expected_nodes:
        for volume_fraction in (
            0.2,
            0.25,
            0.3,
            0.35,
            0.4,
            0.45,
            0.5,
            0.55,
            0.6,
        ):
            for direction in ("x", "y", "z"):
                assert (loaded_node, volume_fraction, direction) in signatures


def test_m2_manifest_freezes_exposure_aware_balanced_partitions(
    catalog: M2CaseCatalog,
    manifest: M2DatasetManifest,
) -> None:
    restored = M2DatasetManifest.model_validate_json(manifest.model_dump_json())

    assert restored == manifest
    assert manifest.manifest_version == M2_DATASET_MANIFEST_VERSION
    assert manifest.split_contract_version == M2_SPLIT_CONTRACT_VERSION
    assert manifest.catalog_id == M2_CASE_CATALOG_ID
    assert manifest.split_counts.model_dump() == {
        "train": 432,
        "validation": 36,
        "test": 36,
        "ood": 252,
    }
    assert len(manifest.samples) == len(catalog.cases) == 756
    assert {sample.sample_version for sample in manifest.samples} == {M2_DATASET_SAMPLE_VERSION}
    assert {sample.load_scale for sample in manifest.samples} == {1.0}

    m1_case_ids = {case.case_id for case in build_m0_case_catalog().cases}
    samples_by_id = {sample.case.case_id: sample for sample in manifest.samples}
    assert len(m1_case_ids) == 160
    assert all(samples_by_id[case_id].split == "train" for case_id in m1_case_ids)
    assert not m1_case_ids.intersection(
        sample.case.case_id for sample in manifest.samples if sample.split in {"validation", "test"}
    )

    for direction in ("y", "z"):
        for volume_fraction in (
            0.2,
            0.25,
            0.3,
            0.35,
            0.4,
            0.45,
            0.5,
            0.55,
            0.6,
        ):
            stratum = [
                sample
                for sample in manifest.samples
                if _direction(sample.case) == direction
                and sample.case.problem.optimization.volume_fraction == volume_fraction
            ]
            assert sum(sample.split == "validation" for sample in stratum) == 2
            assert sum(sample.split == "test" for sample in stratum) == 2

    assert all(
        _direction(sample.case) == "x" for sample in manifest.samples if sample.split == "ood"
    )
    assert all(
        sample.split == "ood" for sample in manifest.samples if _direction(sample.case) == "x"
    )


def test_m2_split_assignment_is_complete_and_deterministic(
    catalog: M2CaseCatalog,
    manifest: M2DatasetManifest,
) -> None:
    assignments = assign_m2_case_splits(catalog)

    assert len(assignments) == 756
    assert assignments == {sample.case.case_id: sample.split for sample in manifest.samples}
    assert Counter(assignments.values()) == {
        "train": 432,
        "validation": 36,
        "test": 36,
        "ood": 252,
    }


def test_m2_contract_rejects_duplicate_stale_and_tampered_data(
    catalog: M2CaseCatalog,
    manifest: M2DatasetManifest,
) -> None:
    with pytest.raises(ValueError, match="unique case IDs"):
        M2CaseCatalog.from_cases((*catalog.cases, catalog.cases[0]))

    payload = catalog.model_dump(mode="json")
    payload["cases"] = payload["cases"][1:]  # type: ignore[index]
    with pytest.raises(ValidationError, match="catalog_id does not match"):
        M2CaseCatalog.model_validate(payload)

    payload = manifest.model_dump(mode="json")
    validation_index = next(
        index for index, sample in enumerate(manifest.samples) if sample.split == "validation"
    )
    payload["samples"][validation_index]["split"] = "train"  # type: ignore[index]
    with pytest.raises(ValidationError, match="split does not match"):
        M2DatasetManifest.model_validate(payload)

    payload = manifest.model_dump(mode="json")
    payload["split_counts"]["train"] = 433  # type: ignore[index]
    with pytest.raises(ValidationError, match="split_counts do not match"):
        M2DatasetManifest.model_validate(payload)

    payload = manifest.model_dump(mode="json")
    payload["samples"][0]["load_scale"] = 2.0  # type: ignore[index]
    with pytest.raises(ValidationError, match="load_scale does not match"):
        M2DatasetManifest.model_validate(payload)

    payload = manifest.model_dump(mode="json")
    payload["unexpected"] = True
    with pytest.raises(ValidationError):
        M2DatasetManifest.model_validate(payload)


def _direction(case: ExperimentCase) -> str:
    return str(_point_load(case).direction)


def _point_load(case: ExperimentCase) -> PointLoadDefinition:
    problem = case.problem
    assert len(problem.loads) == 1
    load = problem.loads[0]
    assert isinstance(load, PointLoadDefinition)
    assert load.magnitude == -1.0
    return load


def _environment() -> DatasetEnvironment:
    return DatasetEnvironment(
        python_version="3.12.10",
        numpy_version="2.5.3",
        scipy_version="1.18.1",
        lockfile_sha256="a" * 64,
    )
