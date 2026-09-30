"""Actual B3 artifact IO and authorization ordering, using synthetic solver states."""

import hashlib
import json
from pathlib import Path

import pytest

import topolab.b3_artifacts as artifacts
from topolab.b3_access import B3Access, B3ArtifactReference
from topolab.b3_catalog import canonical_metadata_bytes


def test_content_addressed_roundtrip_and_permissions(tmp_path, b3_manifest, b3_label, b3_reference):  # type: ignore[no-untyped-def]
    artifact = artifacts.write_b3_record(tmp_path, b3_manifest, b3_label)
    path = tmp_path / artifact.relative_path
    contents = path.read_bytes()
    assert artifact.access.artifact_sha256 == hashlib.sha256(contents).hexdigest()
    assert artifact.byte_size == len(contents)
    assert artifacts.write_b3_record(tmp_path, b3_manifest, b3_label) == artifact
    assert (
        artifacts.read_b3_record(tmp_path, b3_manifest, artifact, B3Access(consumer="data_audit"))
        == b3_label
    )
    for consumer in ("planning", "screen", "final_query", "nearest_neighbor"):
        with pytest.raises(PermissionError):
            artifacts.read_b3_record(tmp_path, b3_manifest, artifact, B3Access(consumer=consumer))
    reference = artifacts.write_b3_record(tmp_path, b3_manifest, b3_reference)
    assert (
        artifacts.read_b3_record(tmp_path, b3_manifest, reference, B3Access(consumer="data_audit"))
        == b3_reference
    )
    with pytest.raises(PermissionError):
        artifacts.read_b3_record(
            tmp_path, b3_manifest, reference, B3Access(consumer="fitting", training_set="base")
        )


def test_denied_metadata_and_incomplete_nn_do_not_open_bytes(
    tmp_path, b3_manifest, b3_label, monkeypatch
):  # type: ignore[no-untyped-def]
    artifact = artifacts.B3DataArtifact.from_record(b3_label)

    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("authorization must precede byte access")

    monkeypatch.setattr(artifacts, "_read_bytes", forbidden)
    bad_context = b3_manifest.context.model_copy(update={"contract_sha256": "b" * 64})
    with pytest.raises(ValueError):
        artifacts.read_b3_record(
            tmp_path,
            b3_manifest.model_copy(update={"context": bad_context}),
            artifact,
            B3Access(consumer="data_audit"),
        )
    with pytest.raises(PermissionError):
        artifacts.read_b3_record(tmp_path, b3_manifest, artifact, B3Access(consumer="planning"))
    with pytest.raises(ValueError, match="manifest"):
        artifacts.read_b3_record(
            tmp_path,
            b3_manifest,
            artifact.model_copy(update={"source_revision": "b" * 40}),
            B3Access(consumer="data_audit"),
        )
    with pytest.raises((ValueError, PermissionError)):
        artifacts.read_b3_population(
            tmp_path, b3_manifest, [artifact], B3Access(consumer="nearest_neighbor")
        )


def test_checksum_and_size_corruption(tmp_path, b3_manifest, b3_label):  # type: ignore[no-untyped-def]
    artifact = artifacts.write_b3_record(tmp_path, b3_manifest, b3_label)
    path = tmp_path / artifact.relative_path
    original = path.read_bytes()
    path.write_bytes(original + b" ")
    with pytest.raises(ValueError, match="byte size"):
        artifacts.read_b3_record(tmp_path, b3_manifest, artifact, B3Access(consumer="data_audit"))
    changed = bytearray(original)
    changed[0] = ord("[")
    path.write_bytes(changed)
    with pytest.raises(ValueError, match="checksum"):
        artifacts.read_b3_record(tmp_path, b3_manifest, artifact, B3Access(consumer="data_audit"))
    with pytest.raises(ValueError, match="existing content-addressed"):
        artifacts.write_b3_record(tmp_path, b3_manifest, b3_label)


@pytest.mark.parametrize("change", ["noncanonical", "old_version", "other_revision", "other_case"])
def test_rehashed_invalid_contents_are_rejected(
    tmp_path, b3_manifest, b3_label, b3_reference, change
):  # type: ignore[no-untyped-def]
    original = artifacts.B3DataArtifact.from_record(b3_label)
    payload = b3_label.model_dump(mode="json")
    if change == "old_version":
        payload["label_version"] = "topolab.b2_3.label.v1"
    elif change == "other_revision":
        payload["context"]["source_revision"] = "b" * 40
    elif change == "other_case":
        payload["entry"] = b3_reference.entry.model_dump(mode="json")
    contents = (
        json.dumps(payload, indent=2).encode()
        if change == "noncanonical"
        else canonical_metadata_bytes(payload)
    )
    digest = hashlib.sha256(contents).hexdigest()
    access = original.access.model_copy(update={"artifact_sha256": digest})
    reference = original.model_copy(
        update={
            "access": access,
            "byte_size": len(contents),
            "relative_path": f"artifacts/label/{access.entry.case.case_id}/{digest}.json",
        }
    )
    path = tmp_path / reference.relative_path
    path.parent.mkdir(parents=True)
    path.write_bytes(contents)
    with pytest.raises(ValueError):
        artifacts.read_b3_record(tmp_path, b3_manifest, reference, B3Access(consumer="data_audit"))


def test_symlink_escape_and_repository_output_are_rejected(tmp_path, b3_manifest, b3_label):  # type: ignore[no-untyped-def]
    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "artifacts").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="escapes"):
        artifacts.write_b3_record(root, b3_manifest, b3_label)
    with pytest.raises(RuntimeError, match="outside"):
        artifacts.write_b3_record(
            Path(__file__).resolve().parents[1] / "forbidden-b3-data", b3_manifest, b3_label
        )


def test_complete_nn_population_keeps_canonical_pairing(tmp_path, b3_manifest, monkeypatch):  # type: ignore[no-untyped-def]
    # Real authorization/checksums with metadata byte spies; numerical parsing is
    # independently covered by the actual single-record round trips above.
    references = []
    manifest_sha = b3_manifest.sha256()
    for entry in b3_manifest.catalog.for_role("train"):
        contents = entry.case.case_id.encode()
        digest = hashlib.sha256(contents).hexdigest()
        references.append(
            artifacts.B3DataArtifact(
                access=B3ArtifactReference(
                    kind="label", entry=entry, artifact_sha256=digest, origins=(entry.case,)
                ),
                manifest_sha256=manifest_sha,
                source_revision=b3_manifest.context.source_revision,
                byte_size=len(contents),
                relative_path=f"artifacts/label/{entry.case.case_id}/{digest}.json",
            )
        )
    opened = []

    def read(root, artifact):  # type: ignore[no-untyped-def]
        opened.append(artifact.access.entry.case.case_id)
        return opened[-1].encode()

    def parse(contents, artifact, manifest):  # type: ignore[no-untyped-def]
        assert contents.decode() == artifact.access.entry.case.case_id
        return contents.decode()

    monkeypatch.setattr(artifacts, "_read_bytes", read)
    monkeypatch.setattr(artifacts, "_parse_record", parse)
    result = artifacts.read_b3_population(
        tmp_path, b3_manifest, reversed(references), B3Access(consumer="nearest_neighbor")
    )
    assert len(result) == 528
    assert result == tuple(sorted(opened))
