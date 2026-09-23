"""Recoverable manifest-to-label indexing for frozen dataset contracts."""

import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated, Final, Literal

from pydantic import Field, ValidationError, field_validator, model_validator

from topolab.dataset import DatasetManifest, DatasetSplit
from topolab.experiment import CASE_ID_PREFIX
from topolab.label_artifacts import (
    LabelArtifactError,
    LabelArtifactReference,
    read_label_artifact,
    write_label_artifact,
)
from topolab.labels import LabelGenerationError, generate_label
from topolab.m2_dataset import M2DatasetManifest
from topolab.problem import ContractModel

MATERIALIZATION_INDEX_VERSION: Final = "topolab.m0.materialization.v1"
M2_MATERIALIZATION_INDEX_VERSION: Final = "topolab.m2.materialization.v1"

_CASE_ID_PATTERN = rf"^{CASE_ID_PREFIX}[0-9a-f]{{64}}$"
_SHA256_PATTERN = r"^[0-9a-f]{64}$"


class MaterializationIndexError(RuntimeError):
    """Raised when a materialization checkpoint cannot be safely used."""


class MaterializationSuccess(ContractModel):
    """One manifest sample backed by a verified label artifact reference."""

    status: Literal["succeeded"] = "succeeded"
    case_id: Annotated[str, Field(pattern=_CASE_ID_PATTERN)]
    split: DatasetSplit
    artifact: LabelArtifactReference

    @model_validator(mode="after")
    def validate_artifact_case(self) -> "MaterializationSuccess":
        if self.artifact.case_id != self.case_id:
            raise ValueError("artifact case_id does not match materialization entry")
        return self


class MaterializationFailure(ContractModel):
    """One terminal, sanitized failure for a manifest sample."""

    status: Literal["failed"] = "failed"
    case_id: Annotated[str, Field(pattern=_CASE_ID_PATTERN)]
    split: DatasetSplit
    failure_code: Literal["label_generation_error", "label_artifact_error"]


type MaterializationEntry = Annotated[
    MaterializationSuccess | MaterializationFailure,
    Field(discriminator="status"),
]
type MaterializationManifest = Annotated[
    DatasetManifest | M2DatasetManifest,
    Field(discriminator="manifest_version"),
]


class DatasetMaterializationIndex(ContractModel):
    """Canonical, append-only checkpoint for one immutable dataset manifest."""

    index_version: Literal[
        "topolab.m0.materialization.v1",
        "topolab.m2.materialization.v1",
    ] = MATERIALIZATION_INDEX_VERSION
    state: Literal["in_progress", "complete"]
    manifest_sha256: Annotated[str, Field(pattern=_SHA256_PATTERN)]
    manifest: MaterializationManifest
    entries: tuple[MaterializationEntry, ...] = ()

    @classmethod
    def start(cls, manifest: MaterializationManifest) -> "DatasetMaterializationIndex":
        """Create the empty deterministic checkpoint for one manifest."""

        return cls(
            index_version=(
                M2_MATERIALIZATION_INDEX_VERSION
                if isinstance(manifest, M2DatasetManifest)
                else MATERIALIZATION_INDEX_VERSION
            ),
            state="in_progress",
            manifest_sha256=build_manifest_sha256(manifest),
            manifest=manifest,
        )

    @field_validator("entries", mode="after")
    @classmethod
    def sort_entries(
        cls,
        entries: tuple[MaterializationEntry, ...],
    ) -> tuple[MaterializationEntry, ...]:
        return tuple(sorted(entries, key=lambda entry: entry.case_id))

    @model_validator(mode="after")
    def validate_index(self) -> "DatasetMaterializationIndex":
        expected_version: Literal[
            "topolab.m0.materialization.v1",
            "topolab.m2.materialization.v1",
        ] = (
            M2_MATERIALIZATION_INDEX_VERSION
            if isinstance(self.manifest, M2DatasetManifest)
            else MATERIALIZATION_INDEX_VERSION
        )
        if self.index_version != expected_version:
            raise ValueError("index_version does not match the manifest contract")
        if self.manifest_sha256 != build_manifest_sha256(self.manifest):
            raise ValueError("manifest_sha256 does not match the embedded manifest")

        samples = {sample.case.case_id: sample for sample in self.manifest.samples}
        entry_ids = tuple(entry.case_id for entry in self.entries)
        if len(set(entry_ids)) != len(entry_ids):
            raise ValueError("materialization entries must have unique case IDs")
        if any(case_id not in samples for case_id in entry_ids):
            raise ValueError("materialization entry is not present in the manifest")

        for entry in self.entries:
            sample = samples[entry.case_id]
            if entry.split != sample.split:
                raise ValueError("materialization split does not match the manifest")
            if isinstance(entry, MaterializationSuccess):
                if entry.artifact.generator_version != self.manifest.generator_version:
                    raise ValueError("artifact generator version does not match the manifest")
                if entry.artifact.source_revision != self.manifest.source_revision:
                    raise ValueError("artifact source revision does not match the manifest")

        if self.state == "complete" and set(entry_ids) != set(samples):
            raise ValueError("complete materialization must record every manifest case")
        return self


def canonical_manifest_bytes(manifest: MaterializationManifest) -> bytes:
    """Return the exact canonical bytes used to identify one dataset manifest."""

    return _canonical_json_bytes(manifest.model_dump(mode="json"))


def build_manifest_sha256(manifest: MaterializationManifest) -> str:
    """Return the stable digest of one canonical dataset manifest."""

    return hashlib.sha256(canonical_manifest_bytes(manifest)).hexdigest()


def canonical_materialization_index_bytes(
    index: DatasetMaterializationIndex,
) -> bytes:
    """Serialize one materialization checkpoint in its canonical form."""

    return _canonical_json_bytes(index.model_dump(mode="json"))


def materialization_index_path(root: Path, manifest: MaterializationManifest) -> Path:
    """Return the stable checkpoint path for one immutable manifest."""

    return root / "materializations" / f"{build_manifest_sha256(manifest)}.json"


def materialize_dataset(
    root: Path,
    manifest: MaterializationManifest,
) -> DatasetMaterializationIndex:
    """Materialize pending labels in canonical order and checkpoint every outcome."""

    target = materialization_index_path(root, manifest)
    if target.exists():
        index = read_materialization_index(root, manifest)
    else:
        index = DatasetMaterializationIndex.start(manifest)
        write_materialization_index(root, index)

    if index.state == "complete":
        return index

    recorded = {entry.case_id for entry in index.entries}
    for sample in manifest.samples:
        if sample.case.case_id in recorded:
            continue
        try:
            label = generate_label(
                sample.case,
                source_revision=manifest.source_revision,
                environment=manifest.environment,
            )
        except LabelGenerationError:
            entry: MaterializationEntry = MaterializationFailure(
                case_id=sample.case.case_id,
                split=sample.split,
                failure_code="label_generation_error",
            )
        else:
            try:
                artifact = write_label_artifact(root, label)
            except LabelArtifactError:
                entry = MaterializationFailure(
                    case_id=sample.case.case_id,
                    split=sample.split,
                    failure_code="label_artifact_error",
                )
            else:
                entry = MaterializationSuccess(
                    case_id=sample.case.case_id,
                    split=sample.split,
                    artifact=artifact,
                )

        index = DatasetMaterializationIndex(
            state="in_progress",
            manifest_sha256=index.manifest_sha256,
            manifest=manifest,
            entries=(*index.entries, entry),
        )
        write_materialization_index(root, index)
        recorded.add(entry.case_id)

    complete = DatasetMaterializationIndex(
        state="complete",
        manifest_sha256=index.manifest_sha256,
        manifest=manifest,
        entries=index.entries,
    )
    write_materialization_index(root, complete)
    return complete


def write_materialization_index(
    root: Path,
    index: DatasetMaterializationIndex,
) -> Path:
    """Atomically publish one append-only, artifact-verified checkpoint."""

    _verify_successful_artifacts(root, index)
    target = materialization_index_path(root, index.manifest)
    contents = canonical_materialization_index_bytes(index)
    temporary_path: Path | None = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            previous_contents = target.read_bytes()
            if previous_contents == contents:
                return target
            previous = _parse_materialization_index(previous_contents)
            if previous.manifest != index.manifest:
                raise MaterializationIndexError(
                    "existing materialization index has a different manifest"
                )
            _verify_successful_artifacts(root, previous)
            _validate_append_only(previous, index)

        with NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=".topolab-materialization-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(contents)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, target)
    except MaterializationIndexError:
        raise
    except OSError as error:
        raise MaterializationIndexError(
            "could not write materialization index"
        ) from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
    return target


def read_materialization_index(
    root: Path,
    manifest: MaterializationManifest,
) -> DatasetMaterializationIndex:
    """Read a canonical checkpoint and verify every successful label artifact."""

    target = materialization_index_path(root, manifest)
    try:
        contents = target.read_bytes()
    except FileNotFoundError as error:
        raise MaterializationIndexError("materialization index is missing") from error
    except OSError as error:
        raise MaterializationIndexError(
            "could not read materialization index"
        ) from error

    index = _parse_materialization_index(contents)
    if index.manifest != manifest:
        raise MaterializationIndexError(
            "materialization index does not match the requested manifest"
        )
    _verify_successful_artifacts(root, index)
    return index


def _canonical_json_bytes(payload: object) -> bytes:
    serialized = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"{serialized}\n".encode()


def _parse_materialization_index(contents: bytes) -> DatasetMaterializationIndex:
    try:
        index = DatasetMaterializationIndex.model_validate_json(contents)
    except ValidationError as error:
        raise MaterializationIndexError(
            "materialization index schema validation failed"
        ) from error
    if canonical_materialization_index_bytes(index) != contents:
        raise MaterializationIndexError("materialization index is not canonical JSON")
    return index


def _verify_successful_artifacts(
    root: Path,
    index: DatasetMaterializationIndex,
) -> None:
    samples = {sample.case.case_id: sample for sample in index.manifest.samples}
    for entry in index.entries:
        if not isinstance(entry, MaterializationSuccess):
            continue
        try:
            label = read_label_artifact(root, entry.artifact)
        except LabelArtifactError as error:
            raise MaterializationIndexError(
                f"label artifact verification failed for {entry.case_id}"
            ) from error
        sample = samples[entry.case_id]
        if label.case != sample.case:
            raise MaterializationIndexError(
                f"label case does not match manifest sample {entry.case_id}"
            )
        if label.environment != index.manifest.environment:
            raise MaterializationIndexError(
                f"label environment does not match manifest for {entry.case_id}"
            )
        if (
            label.case_schema_version != index.manifest.case_schema_version
            or label.generator_version != index.manifest.generator_version
            or label.solver_contract_version != index.manifest.solver_contract_version
            or label.source_revision != index.manifest.source_revision
        ):
            raise MaterializationIndexError(
                f"label provenance does not match manifest for {entry.case_id}"
            )


def _validate_append_only(
    previous: DatasetMaterializationIndex,
    current: DatasetMaterializationIndex,
) -> None:
    if previous.state == "complete":
        raise MaterializationIndexError("complete materialization index is immutable")
    current_entries = {entry.case_id: entry for entry in current.entries}
    for entry in previous.entries:
        if current_entries.get(entry.case_id) != entry:
            raise MaterializationIndexError(
                "materialization updates must preserve recorded outcomes"
            )
