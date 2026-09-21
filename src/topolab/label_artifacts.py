"""Content-addressed persistence for one validated M0 label."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from typing import Annotated, Literal

from pydantic import Field, ValidationError, model_validator

from topolab.experiment import CASE_ID_PREFIX
from topolab.labels import LabelRecord
from topolab.problem import ContractModel

LABEL_ARTIFACT_VERSION = "topolab.m0.label-artifact.v1"

_CASE_ID_PATTERN = rf"^{CASE_ID_PREFIX}[0-9a-f]{{64}}$"
_REVISION_PATTERN = r"^[0-9a-f]{40}$"
_SHA256_PATTERN = r"^[0-9a-f]{64}$"


class LabelArtifactError(RuntimeError):
    """Raised when a label artifact cannot be written or verified."""


class LabelArtifactReference(ContractModel):
    """Portable content-addressed reference to one canonical label file."""

    artifact_version: Literal["topolab.m0.label-artifact.v1"] = (
        "topolab.m0.label-artifact.v1"
    )
    case_id: Annotated[str, Field(pattern=_CASE_ID_PATTERN)]
    generator_version: Literal["topolab.m0.generator.v1"]
    source_revision: Annotated[str, Field(pattern=_REVISION_PATTERN)]
    sha256: Annotated[str, Field(pattern=_SHA256_PATTERN)]
    byte_size: Annotated[int, Field(strict=True, gt=0)]
    relative_path: Annotated[str, Field(min_length=1)]

    @classmethod
    def from_label(cls, label: LabelRecord) -> "LabelArtifactReference":
        contents = canonical_label_bytes(label)
        digest = hashlib.sha256(contents).hexdigest()
        return cls(
            case_id=label.case.case_id,
            generator_version=label.generator_version,
            source_revision=label.source_revision,
            sha256=digest,
            byte_size=len(contents),
            relative_path=_relative_path(label.case.case_id, digest),
        )

    @model_validator(mode="after")
    def validate_relative_path(self) -> "LabelArtifactReference":
        expected = _relative_path(self.case_id, self.sha256)
        if self.relative_path != expected:
            raise ValueError("relative_path must match the content-addressed path")
        return self


def canonical_label_bytes(label: LabelRecord) -> bytes:
    """Serialize one label as the exact bytes covered by its artifact checksum."""

    payload = label.model_dump(mode="json")
    serialized = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"{serialized}\n".encode()


def write_label_artifact(root: Path, label: LabelRecord) -> LabelArtifactReference:
    """Atomically write one canonical label without replacing different content."""

    contents = canonical_label_bytes(label)
    reference = LabelArtifactReference.from_label(label)
    target = _artifact_path(root, reference)
    temporary_path: Path | None = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != contents:
                raise LabelArtifactError(
                    "existing label artifact has different content"
                )
            return reference

        with NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=".topolab-label-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(contents)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, target)
    except LabelArtifactError:
        raise
    except OSError as error:
        raise LabelArtifactError("could not write label artifact") from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
    return reference


def read_label_artifact(
    root: Path,
    reference: LabelArtifactReference,
) -> LabelRecord:
    """Read one label after size, checksum, schema, and canonical-form checks."""

    target = _artifact_path(root, reference)
    try:
        contents = target.read_bytes()
    except FileNotFoundError as error:
        raise LabelArtifactError("label artifact is missing") from error
    except OSError as error:
        raise LabelArtifactError("could not read label artifact") from error

    if len(contents) != reference.byte_size:
        raise LabelArtifactError("label artifact byte size does not match reference")
    if hashlib.sha256(contents).hexdigest() != reference.sha256:
        raise LabelArtifactError("label artifact checksum does not match reference")
    try:
        label = LabelRecord.model_validate_json(contents)
    except ValidationError as error:
        raise LabelArtifactError("label artifact schema validation failed") from error
    if canonical_label_bytes(label) != contents:
        raise LabelArtifactError("label artifact is not canonical JSON")
    if LabelArtifactReference.from_label(label) != reference:
        raise LabelArtifactError("label artifact content does not match reference")
    return label


def _relative_path(case_id: str, digest: str) -> str:
    return f"labels/{case_id}/{digest}.json"


def _artifact_path(root: Path, reference: LabelArtifactReference) -> Path:
    return root.joinpath(*PurePosixPath(reference.relative_path).parts)
