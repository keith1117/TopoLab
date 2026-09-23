from pathlib import Path

import pytest
from pydantic import ValidationError

from topolab.dataset import DatasetEnvironment
from topolab.m2_dataset import M2DatasetManifest, build_m2_case_catalog
from topolab.materialization import (
    M2_MATERIALIZATION_INDEX_VERSION,
    MATERIALIZATION_INDEX_VERSION,
    DatasetMaterializationIndex,
    MaterializationFailure,
    build_manifest_sha256,
    canonical_materialization_index_bytes,
    read_materialization_index,
    write_materialization_index,
)


@pytest.fixture(scope="module")
def m2_manifest() -> M2DatasetManifest:
    return build_m2_case_catalog().build_manifest(
        source_revision="d" * 40,
        environment=DatasetEnvironment(
            python_version="3.12.10",
            numpy_version="2.3.3",
            scipy_version="1.16.2",
            lockfile_sha256="e" * 64,
        ),
    )


def test_m2_index_uses_distinct_version_and_round_trips(
    m2_manifest: M2DatasetManifest,
) -> None:
    index = DatasetMaterializationIndex.start(m2_manifest)
    restored = DatasetMaterializationIndex.model_validate_json(
        canonical_materialization_index_bytes(index)
    )

    assert index == restored
    assert index.index_version == M2_MATERIALIZATION_INDEX_VERSION
    assert index.manifest == m2_manifest
    assert index.manifest_sha256 == build_manifest_sha256(m2_manifest)


def test_m2_index_rejects_m0_index_version(
    m2_manifest: M2DatasetManifest,
) -> None:
    payload = DatasetMaterializationIndex.start(m2_manifest).model_dump(mode="json")
    payload["index_version"] = MATERIALIZATION_INDEX_VERSION

    with pytest.raises(ValidationError, match="index_version"):
        DatasetMaterializationIndex.model_validate(payload)


def test_complete_m2_index_writes_and_reads_canonically(
    tmp_path: Path,
    m2_manifest: M2DatasetManifest,
) -> None:
    entries = tuple(
        MaterializationFailure(
            case_id=sample.case.case_id,
            split=sample.split,
            failure_code="label_generation_error",
        )
        for sample in m2_manifest.samples
    )
    index = DatasetMaterializationIndex(
        index_version=M2_MATERIALIZATION_INDEX_VERSION,
        state="complete",
        manifest_sha256=build_manifest_sha256(m2_manifest),
        manifest=m2_manifest,
        entries=entries,
    )

    target = write_materialization_index(tmp_path, index)

    assert target.read_bytes() == canonical_materialization_index_bytes(index)
    assert read_materialization_index(tmp_path, m2_manifest) == index
