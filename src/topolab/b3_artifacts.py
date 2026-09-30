"""Content-addressed B3 artifacts, with consumer guards before filesystem access."""

import hashlib
import os
from collections.abc import Iterable
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated, Literal

from pydantic import Field, TypeAdapter, model_validator

from topolab.b3_access import B3Access, B3ArtifactReference
from topolab.b3_catalog import Sha256, canonical_metadata_bytes
from topolab.b3_dataset import B3DataRecord, B3DatasetManifest, Revision
from topolab.dataset_cli import validate_external_output_root
from topolab.problem import ContractModel

_RECORD_ADAPTER: TypeAdapter[B3DataRecord] = TypeAdapter(B3DataRecord)


class B3DataArtifact(ContractModel):
    """Portable reference binding bytes to their data manifest and implementation."""

    artifact_version: Literal["topolab.b3.data-artifact.v1"] = "topolab.b3.data-artifact.v1"
    access: B3ArtifactReference
    manifest_sha256: Sha256
    source_revision: Revision
    byte_size: Annotated[int, Field(strict=True, gt=0)]
    relative_path: str

    @classmethod
    def from_record(cls, record: B3DataRecord) -> "B3DataArtifact":
        contents = canonical_metadata_bytes(record.model_dump(mode="json"))
        access = B3ArtifactReference(
            kind=record.kind,
            entry=record.entry,
            artifact_sha256=hashlib.sha256(contents).hexdigest(),
            origins=(record.entry.case,),
        )
        return cls(
            access=access,
            manifest_sha256=record.manifest_sha256,
            source_revision=record.context.source_revision,
            byte_size=len(contents),
            relative_path=_relative_path(access),
        )

    @model_validator(mode="after")
    def validate_path_and_kind(self) -> "B3DataArtifact":
        if self.access.kind not in ("label", "reference"):
            raise ValueError("B3 data artifacts cannot contain query outcomes")
        if self.relative_path != _relative_path(self.access):
            raise ValueError("artifact path must match its content-addressed identity")
        return self


def _relative_path(access: B3ArtifactReference) -> str:
    return f"artifacts/{access.kind}/{access.entry.case.case_id}/{access.artifact_sha256}.json"


def safe_path(root: Path, relative: str) -> Path:
    """Reject symlink escapes before reading or writing any artifact bytes."""

    root = root.resolve()
    target = root.joinpath(relative).resolve()
    if not target.is_relative_to(root) or target == root:
        raise ValueError("artifact path escapes its external data root")
    return target


def atomic_write(path: Path, contents: bytes) -> None:
    """Publish a flushed checkpoint; interrupted temporary files are never inputs."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".b3-", delete=False) as stream:
            temporary_path = Path(stream.name)
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _verify_artifact_metadata(
    artifact: B3DataArtifact, manifest: B3DatasetManifest
) -> B3DataArtifact:
    verified = B3DataArtifact.model_validate(artifact.model_dump(mode="json"))
    if (
        verified.manifest_sha256 != manifest.sha256()
        or verified.source_revision != manifest.context.source_revision
    ):
        raise ValueError("artifact metadata differs from the frozen data manifest")
    return verified


def write_b3_record(
    root: Path, manifest: B3DatasetManifest, record: B3DataRecord
) -> B3DataArtifact:
    """Write a new B3 record atomically; never accept historical artifact schemas."""

    root = validate_external_output_root(Path(__file__).resolve().parents[2], root)
    manifest = B3DatasetManifest.model_validate(manifest.model_dump(mode="json"))
    record = _RECORD_ADAPTER.validate_python(record.model_dump(mode="json"))
    if record.context != manifest.context or record.manifest_sha256 != manifest.sha256():
        raise ValueError("record provenance differs from the data manifest")
    artifact = B3DataArtifact.from_record(record)
    contents = canonical_metadata_bytes(record.model_dump(mode="json"))
    target = safe_path(root, artifact.relative_path)
    if target.exists():
        if target.read_bytes() != contents:
            raise ValueError("existing content-addressed artifact differs from its bytes")
    else:
        atomic_write(target, contents)
    return artifact


def _parse_record(
    contents: bytes, artifact: B3DataArtifact, manifest: B3DatasetManifest
) -> B3DataRecord:
    record = _RECORD_ADAPTER.validate_json(contents)
    if canonical_metadata_bytes(record.model_dump(mode="json")) != contents:
        raise ValueError("B3 artifact is not canonical JSON")
    if record.context != manifest.context or B3DataArtifact.from_record(record) != artifact:
        raise ValueError("artifact contents differ from their metadata/provenance")
    return record


def _read_bytes(root: Path, artifact: B3DataArtifact) -> bytes:
    contents = safe_path(root, artifact.relative_path).read_bytes()
    if len(contents) != artifact.byte_size:
        raise ValueError("artifact byte size differs from its reference")
    return contents


def read_b3_record(
    root: Path, manifest: B3DatasetManifest, artifact: B3DataArtifact, access: B3Access
) -> B3DataRecord:
    """Verify permissions before opening bytes, then verify schema and provenance."""

    manifest = B3DatasetManifest.model_validate(manifest.model_dump(mode="json"))
    verified = _verify_artifact_metadata(artifact, manifest)
    contents = access.read_artifact(verified.access, lambda _: _read_bytes(root, verified))
    return _parse_record(contents, verified, manifest)


def read_b3_population(
    root: Path,
    manifest: B3DatasetManifest,
    artifacts: Iterable[B3DataArtifact],
    access: B3Access,
    kind: Literal["label", "reference"] = "label",
) -> tuple[B3DataRecord, ...]:
    """Read exactly the consumer's complete population, including train-only NN."""

    manifest = B3DatasetManifest.model_validate(manifest.model_dump(mode="json"))
    verified = tuple(_verify_artifact_metadata(a, manifest) for a in artifacts)
    by_id = {a.access.entry.case.case_id: a for a in verified}
    contents = access.read_population(
        (a.access for a in verified),
        kind,
        lambda ref: _read_bytes(root, by_id[ref.entry.case.case_id]),
    )
    ordered = sorted(verified, key=lambda a: a.access.entry.case.case_id)
    return tuple(
        _parse_record(data, artifact, manifest)
        for data, artifact in zip(contents, ordered, strict=True)
    )
