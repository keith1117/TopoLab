import hashlib
from pathlib import Path, PurePosixPath

import pytest
from pydantic import ValidationError

from topolab.dataset import DatasetEnvironment
from topolab.experiment import ExperimentCase
from topolab.label_artifacts import (
    LABEL_ARTIFACT_VERSION,
    LabelArtifactError,
    LabelArtifactReference,
    canonical_label_bytes,
    read_label_artifact,
    write_label_artifact,
)
from topolab.labels import LabelRecord, generate_label
from topolab.problem import (
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)


@pytest.fixture(scope="module")
def label() -> LabelRecord:
    case = ExperimentCase.from_problem(
        TopologyProblem(
            mesh=MeshDefinition(
                element_counts=(4, 2, 1),
                lengths=(4.0, 2.0, 1.0),
            ),
            material=MaterialDefinition(
                solid_modulus=1000.0,
                minimum_modulus=1.0,
                poisson_ratio=0.3,
            ),
            supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
            loads=(
                PointLoadDefinition(
                    node=29,
                    direction="y",
                    magnitude=-1.0,
                ),
            ),
            optimization=OptimizationDefinition(
                volume_fraction=0.5,
                filter_radius=1.5,
                minimum_density=0.05,
                convergence_tolerance=0.01,
                max_iterations=60,
            ),
        )
    )
    return generate_label(
        case,
        source_revision="b" * 40,
        environment=DatasetEnvironment(
            python_version="3.12.10",
            numpy_version="2.3.3",
            scipy_version="1.16.2",
            lockfile_sha256="a" * 64,
        ),
    )


def test_canonical_label_artifact_is_deterministic_and_content_addressed(
    label: LabelRecord,
) -> None:
    first = canonical_label_bytes(label)
    second = canonical_label_bytes(label)
    reference = LabelArtifactReference.from_label(label)

    assert first == second
    assert first.endswith(b"\n")
    assert b'": ' not in first
    assert b", " not in first
    assert reference.artifact_version == LABEL_ARTIFACT_VERSION
    assert reference.case_id == label.case.case_id
    assert reference.source_revision == label.source_revision
    assert reference.sha256 == hashlib.sha256(first).hexdigest()
    assert reference.byte_size == len(first)
    assert reference.relative_path == (
        f"labels/{label.case.case_id}/{reference.sha256}.json"
    )


def test_label_artifact_write_is_idempotent_and_read_verifies_content(
    tmp_path: Path,
    label: LabelRecord,
) -> None:
    reference = write_label_artifact(tmp_path, label)
    repeated = write_label_artifact(tmp_path, label)
    artifact_path = _artifact_path(tmp_path, reference)

    assert repeated == reference
    assert artifact_path.read_bytes() == canonical_label_bytes(label)
    assert read_label_artifact(tmp_path, reference) == label


def test_label_artifact_rejects_checksum_tampering_and_conflicting_write(
    tmp_path: Path,
    label: LabelRecord,
) -> None:
    reference = write_label_artifact(tmp_path, label)
    artifact_path = _artifact_path(tmp_path, reference)
    corrupted = bytearray(artifact_path.read_bytes())
    corrupted[-2] ^= 1
    artifact_path.write_bytes(corrupted)

    with pytest.raises(LabelArtifactError, match="checksum"):
        read_label_artifact(tmp_path, reference)
    with pytest.raises(LabelArtifactError, match="different content"):
        write_label_artifact(tmp_path, label)


def test_label_artifact_rejects_schema_invalid_and_noncanonical_json(
    tmp_path: Path,
    label: LabelRecord,
) -> None:
    invalid = b"{}\n"
    invalid_reference = _reference_for_bytes(label, invalid)
    invalid_path = _artifact_path(tmp_path, invalid_reference)
    invalid_path.parent.mkdir(parents=True)
    invalid_path.write_bytes(invalid)

    with pytest.raises(LabelArtifactError, match="schema"):
        read_label_artifact(tmp_path, invalid_reference)

    noncanonical = f"{label.model_dump_json(indent=2)}\n".encode()
    noncanonical_reference = _reference_for_bytes(label, noncanonical)
    noncanonical_path = _artifact_path(tmp_path, noncanonical_reference)
    noncanonical_path.write_bytes(noncanonical)

    with pytest.raises(LabelArtifactError, match="canonical"):
        read_label_artifact(tmp_path, noncanonical_reference)


def test_label_artifact_atomic_failure_leaves_no_partial_file(
    tmp_path: Path,
    label: LabelRecord,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = LabelArtifactReference.from_label(label)
    artifact_path = _artifact_path(tmp_path, reference)

    def fail_replace(source: object, destination: object) -> None:
        assert not artifact_path.exists()
        raise OSError("injected replace failure")

    monkeypatch.setattr("topolab.label_artifacts.os.replace", fail_replace)

    with pytest.raises(LabelArtifactError, match="write"):
        write_label_artifact(tmp_path, label)

    assert not artifact_path.exists()
    assert not tuple(artifact_path.parent.iterdir())


def test_label_artifact_rejects_missing_file_and_changed_relative_path(
    tmp_path: Path,
    label: LabelRecord,
) -> None:
    reference = LabelArtifactReference.from_label(label)

    with pytest.raises(LabelArtifactError, match="missing"):
        read_label_artifact(tmp_path, reference)

    write_label_artifact(tmp_path, label)
    payload = reference.model_dump(mode="json")
    payload["source_revision"] = "c" * 40
    mismatched_reference = LabelArtifactReference.model_validate(payload)
    with pytest.raises(LabelArtifactError, match="content does not match"):
        read_label_artifact(tmp_path, mismatched_reference)

    payload = reference.model_dump(mode="json")
    payload["relative_path"] = f"labels/{label.case.case_id}/moved.json"
    with pytest.raises(ValidationError, match="content-addressed path"):
        LabelArtifactReference.model_validate(payload)


def _reference_for_bytes(
    label: LabelRecord,
    contents: bytes,
) -> LabelArtifactReference:
    digest = hashlib.sha256(contents).hexdigest()
    return LabelArtifactReference(
        case_id=label.case.case_id,
        generator_version=label.generator_version,
        source_revision=label.source_revision,
        sha256=digest,
        byte_size=len(contents),
        relative_path=f"labels/{label.case.case_id}/{digest}.json",
    )


def _artifact_path(root: Path, reference: LabelArtifactReference) -> Path:
    return root.joinpath(*PurePosixPath(reference.relative_path).parts)
