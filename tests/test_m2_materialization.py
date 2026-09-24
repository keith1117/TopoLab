from pathlib import Path

import pytest
from pydantic import ValidationError

import topolab.materialization as materialization_module
from topolab.dataset import DatasetEnvironment
from topolab.labels import LabelGenerationError
from topolab.m2_dataset import M2DatasetManifest, build_m2_case_catalog
from topolab.materialization import (
    M2_MATERIALIZATION_INDEX_VERSION,
    MATERIALIZATION_INDEX_VERSION,
    DatasetMaterializationIndex,
    MaterializationFailure,
    build_manifest_sha256,
    canonical_materialization_index_bytes,
    materialize_dataset,
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


def test_m2_materializer_preserves_index_version_across_checkpoints(
    tmp_path: Path,
    m2_manifest: M2DatasetManifest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkpoints: list[DatasetMaterializationIndex] = []

    def fail_generation(*args: object, **kwargs: object) -> None:
        raise LabelGenerationError("injected failure")

    def capture_checkpoint(
        root: Path,
        index: DatasetMaterializationIndex,
    ) -> Path:
        checkpoints.append(index)
        if len(checkpoints) == 2:
            raise KeyboardInterrupt
        return root / "ignored.json"

    monkeypatch.setattr(materialization_module, "generate_label", fail_generation)
    monkeypatch.setattr(
        materialization_module,
        "write_materialization_index",
        capture_checkpoint,
    )

    with pytest.raises(KeyboardInterrupt):
        materialize_dataset(tmp_path, m2_manifest)

    assert len(checkpoints) == 2
    assert all(
        index.index_version == M2_MATERIALIZATION_INDEX_VERSION
        for index in checkpoints
    )
    assert checkpoints[1].entries[0].status == "failed"
