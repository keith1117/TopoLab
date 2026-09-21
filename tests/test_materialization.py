import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from topolab.dataset import DatasetEnvironment, DatasetManifest
from topolab.experiment import ExperimentCase
from topolab.label_artifacts import LabelArtifactReference, write_label_artifact
from topolab.labels import LabelRecord, generate_label
from topolab.materialization import (
    MATERIALIZATION_INDEX_VERSION,
    DatasetMaterializationIndex,
    MaterializationFailure,
    MaterializationIndexError,
    MaterializationSuccess,
    build_manifest_sha256,
    canonical_manifest_bytes,
    canonical_materialization_index_bytes,
    materialization_index_path,
    read_materialization_index,
    write_materialization_index,
)
from topolab.problem import (
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)


@pytest.fixture(scope="module")
def manifest() -> DatasetManifest:
    return DatasetManifest.from_cases(
        _partition_cases(),
        source_revision="b" * 40,
        environment=_environment(),
    )


@pytest.fixture(scope="module")
def train_label(manifest: DatasetManifest) -> LabelRecord:
    sample = next(sample for sample in manifest.samples if sample.split == "train")
    return generate_label(
        sample.case,
        source_revision=manifest.source_revision,
        environment=manifest.environment,
    )


def test_materialization_index_starts_with_stable_manifest_identity(
    manifest: DatasetManifest,
) -> None:
    first = DatasetMaterializationIndex.start(manifest)
    second = DatasetMaterializationIndex.start(manifest)
    restored = DatasetMaterializationIndex.model_validate_json(
        canonical_materialization_index_bytes(first)
    )

    assert first == second == restored
    assert first.index_version == MATERIALIZATION_INDEX_VERSION
    assert first.state == "in_progress"
    assert first.entries == ()
    assert first.manifest_sha256 == hashlib.sha256(
        canonical_manifest_bytes(manifest)
    ).hexdigest()
    assert first.manifest_sha256 == build_manifest_sha256(manifest)


def test_complete_index_is_sorted_and_records_every_manifest_case(
    manifest: DatasetManifest,
) -> None:
    entries = tuple(
        MaterializationFailure(
            case_id=sample.case.case_id,
            split=sample.split,
            failure_code="label_generation_error",
        )
        for sample in reversed(manifest.samples)
    )
    index = _index(manifest, state="complete", entries=entries)

    assert tuple(entry.case_id for entry in index.entries) == tuple(
        sample.case.case_id for sample in manifest.samples
    )


def test_index_rejects_missing_duplicate_unknown_and_changed_sample_metadata(
    manifest: DatasetManifest,
) -> None:
    sample = manifest.samples[0]
    failure = _failure(sample.case.case_id, sample.split)

    with pytest.raises(ValidationError, match="record every manifest case"):
        _index(manifest, state="complete", entries=(failure,))
    with pytest.raises(ValidationError, match="unique case IDs"):
        _index(manifest, entries=(failure, failure))

    unknown = _failure("tlcase-v1-" + "f" * 64, sample.split)
    with pytest.raises(ValidationError, match="not present in the manifest"):
        _index(manifest, entries=(unknown,))

    payload = failure.model_dump(mode="json")
    payload["split"] = "ood" if sample.split != "ood" else "train"
    changed_split = MaterializationFailure.model_validate(payload)
    with pytest.raises(ValidationError, match="split does not match"):
        _index(manifest, entries=(changed_split,))

    payload = DatasetMaterializationIndex.start(manifest).model_dump(mode="json")
    payload["manifest_sha256"] = "a" * 64
    with pytest.raises(ValidationError, match="manifest_sha256"):
        DatasetMaterializationIndex.model_validate(payload)


def test_success_rejects_changed_case_and_manifest_provenance(
    manifest: DatasetManifest,
) -> None:
    sample = manifest.samples[0]
    other = manifest.samples[1]
    reference = _reference(sample.case.case_id)

    with pytest.raises(ValidationError, match="artifact case_id"):
        MaterializationSuccess(
            case_id=other.case.case_id,
            split=other.split,
            artifact=reference,
        )

    changed_revision = _reference(sample.case.case_id, source_revision="c" * 40)
    success = MaterializationSuccess(
        case_id=sample.case.case_id,
        split=sample.split,
        artifact=changed_revision,
    )
    with pytest.raises(ValidationError, match="source revision"):
        _index(manifest, entries=(success,))


def test_index_write_resume_complete_and_verified_read(
    tmp_path: Path,
    manifest: DatasetManifest,
    train_label: LabelRecord,
) -> None:
    artifact = write_label_artifact(tmp_path, train_label)
    sample = next(sample for sample in manifest.samples if sample.split == "train")
    success = MaterializationSuccess(
        case_id=sample.case.case_id,
        split=sample.split,
        artifact=artifact,
    )
    started = DatasetMaterializationIndex.start(manifest)
    progress = _index(manifest, entries=(success,))
    complete = _index(
        manifest,
        state="complete",
        entries=(
            success,
            *(
                _failure(other.case.case_id, other.split)
                for other in manifest.samples
                if other.case.case_id != sample.case.case_id
            ),
        ),
    )

    target = write_materialization_index(tmp_path, started)
    assert target == materialization_index_path(tmp_path, manifest)
    assert write_materialization_index(tmp_path, progress) == target
    assert write_materialization_index(tmp_path, complete) == target
    assert write_materialization_index(tmp_path, complete) == target
    assert target.read_bytes() == canonical_materialization_index_bytes(complete)
    assert read_materialization_index(tmp_path, manifest) == complete


def test_index_rejects_missing_artifact_and_non_append_only_update(
    tmp_path: Path,
    manifest: DatasetManifest,
) -> None:
    sample = manifest.samples[0]
    missing = MaterializationSuccess(
        case_id=sample.case.case_id,
        split=sample.split,
        artifact=_reference(sample.case.case_id),
    )
    with pytest.raises(MaterializationIndexError, match="artifact verification"):
        write_materialization_index(tmp_path, _index(manifest, entries=(missing,)))

    first = _failure(sample.case.case_id, sample.split)
    write_materialization_index(tmp_path, _index(manifest, entries=(first,)))
    replacement = MaterializationFailure(
        case_id=sample.case.case_id,
        split=sample.split,
        failure_code="label_artifact_error",
    )
    with pytest.raises(MaterializationIndexError, match="preserve recorded outcomes"):
        write_materialization_index(tmp_path, _index(manifest, entries=(replacement,)))

    complete = _index(
        manifest,
        state="complete",
        entries=(
            first,
            *(
                _failure(other.case.case_id, other.split)
                for other in manifest.samples
                if other.case.case_id != sample.case.case_id
            ),
        ),
    )
    write_materialization_index(tmp_path, complete)
    complete_payload = complete.model_dump(mode="json")
    complete_payload["entries"][0]["failure_code"] = "label_artifact_error"  # type: ignore[index]
    changed_complete = DatasetMaterializationIndex.model_validate(complete_payload)
    with pytest.raises(MaterializationIndexError, match="complete.*immutable"):
        write_materialization_index(tmp_path, changed_complete)


def test_index_rejects_label_environment_mismatch(
    tmp_path: Path,
    manifest: DatasetManifest,
    train_label: LabelRecord,
) -> None:
    payload = train_label.model_dump(mode="json")
    payload["environment"]["python_version"] = "3.12.11"  # type: ignore[index]
    changed_label = LabelRecord.model_validate(payload)
    artifact = write_label_artifact(tmp_path, changed_label)
    sample = next(sample for sample in manifest.samples if sample.split == "train")
    success = MaterializationSuccess(
        case_id=sample.case.case_id,
        split=sample.split,
        artifact=artifact,
    )

    with pytest.raises(MaterializationIndexError, match="environment"):
        write_materialization_index(tmp_path, _index(manifest, entries=(success,)))


def test_atomic_write_failure_preserves_previous_checkpoint(
    tmp_path: Path,
    manifest: DatasetManifest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started = DatasetMaterializationIndex.start(manifest)
    target = write_materialization_index(tmp_path, started)
    sample = manifest.samples[0]
    progress = _index(
        manifest,
        entries=(_failure(sample.case.case_id, sample.split),),
    )

    def fail_replace(source: object, destination: object) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr("topolab.materialization.os.replace", fail_replace)
    with pytest.raises(MaterializationIndexError, match="write"):
        write_materialization_index(tmp_path, progress)

    assert target.read_bytes() == canonical_materialization_index_bytes(started)
    assert not tuple(target.parent.glob(".topolab-materialization-*.tmp"))


def test_read_rejects_noncanonical_checkpoint(
    tmp_path: Path,
    manifest: DatasetManifest,
) -> None:
    index = DatasetMaterializationIndex.start(manifest)
    target = materialization_index_path(tmp_path, manifest)
    target.parent.mkdir(parents=True)
    target.write_text(index.model_dump_json(indent=2) + "\n")

    with pytest.raises(MaterializationIndexError, match="canonical"):
        read_materialization_index(tmp_path, manifest)


def _index(
    manifest: DatasetManifest,
    *,
    state: str = "in_progress",
    entries: tuple[MaterializationSuccess | MaterializationFailure, ...] = (),
) -> DatasetMaterializationIndex:
    return DatasetMaterializationIndex(
        state=state,  # type: ignore[arg-type]
        manifest_sha256=build_manifest_sha256(manifest),
        manifest=manifest,
        entries=entries,
    )


def _failure(case_id: str, split: str) -> MaterializationFailure:
    return MaterializationFailure(
        case_id=case_id,
        split=split,  # type: ignore[arg-type]
        failure_code="label_generation_error",
    )


def _reference(
    case_id: str,
    *,
    source_revision: str = "b" * 40,
) -> LabelArtifactReference:
    digest = hashlib.sha256(case_id.encode()).hexdigest()
    return LabelArtifactReference(
        case_id=case_id,
        generator_version="topolab.m0.generator.v1",
        source_revision=source_revision,
        sha256=digest,
        byte_size=1,
        relative_path=f"labels/{case_id}/{digest}.json",
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
        python_version="3.12.10",
        numpy_version="2.3.3",
        scipy_version="1.16.2",
        lockfile_sha256="a" * 64,
    )


def _problem(
    *,
    volume_fraction: float,
    load_direction: str = "y",
) -> TopologyProblem:
    return TopologyProblem(
        mesh=MeshDefinition(
            element_counts=(2, 1, 1),
            lengths=(2.0, 1.0, 1.0),
        ),
        material=MaterialDefinition(
            solid_modulus=1000.0,
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
