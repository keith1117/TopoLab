"""Content-addressed M1 checkpoints and auditable selection records."""

import hashlib
import importlib.metadata
import json
import os
import platform
from pathlib import Path, PurePosixPath
from tempfile import NamedTemporaryFile
from typing import Annotated, Literal

import torch
from pydantic import Field, ValidationError, model_validator
from safetensors import SafetensorError
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors
from torch import Tensor

from topolab.materialization import (
    DatasetMaterializationIndex,
    MaterializationFailure,
    build_manifest_sha256,
)
from topolab.problem import ContractModel
from topolab.training import (
    M1_SEEDS,
    M1_TRAINING_CONTRACT,
    M1EpochMetrics,
    M1FitResult,
    M1TensorDataset,
    M1TrainingContract,
    WarmStartCNN,
    build_m1_tensor_dataset,
    fit_m1_model,
)

M1_CHECKPOINT_ARTIFACT_VERSION = "topolab.m1.checkpoint.v1"
M1_SELECTION_ARTIFACT_VERSION = "topolab.m1.selection.v1"

_REVISION_PATTERN = r"^[0-9a-f]{40}$"
_SHA256_PATTERN = r"^[0-9a-f]{64}$"


class M1ArtifactError(RuntimeError):
    """Raised when an M1 training artifact cannot be written or verified."""


class M1RuntimeEnvironment(ContractModel):
    """Non-sensitive runtime and thread metadata for one fitting execution."""

    python_version: Annotated[str, Field(min_length=1)]
    numpy_version: Annotated[str, Field(min_length=1)]
    scipy_version: Annotated[str, Field(min_length=1)]
    torch_version: Annotated[str, Field(min_length=1)]
    safetensors_version: Annotated[str, Field(min_length=1)]
    lockfile_sha256: Annotated[str, Field(pattern=_SHA256_PATTERN)]
    platform_system: Annotated[str, Field(min_length=1)]
    platform_machine: Annotated[str, Field(min_length=1)]
    processor: str
    torch_num_threads: Annotated[int, Field(strict=True, gt=0)]
    torch_num_interop_threads: Annotated[int, Field(strict=True, gt=0)]


class M1CheckpointReference(ContractModel):
    """Provenance-bound reference to one content-addressed Safetensors file."""

    artifact_version: Literal["topolab.m1.checkpoint.v1"] = (
        "topolab.m1.checkpoint.v1"
    )
    training_contract_version: Literal["topolab.m1.training.v1"] = (
        "topolab.m1.training.v1"
    )
    model_version: Literal["topolab.m1.cnn.v1"] = "topolab.m1.cnn.v1"
    manifest_sha256: Annotated[str, Field(pattern=_SHA256_PATTERN)]
    label_source_revision: Annotated[str, Field(pattern=_REVISION_PATTERN)]
    training_source_revision: Annotated[str, Field(pattern=_REVISION_PATTERN)]
    source_tree_clean: Literal[True] = True
    runtime: M1RuntimeEnvironment
    seed: Annotated[int, Field(strict=True)]
    selected_epoch: Annotated[int, Field(strict=True, gt=0)]
    sha256: Annotated[str, Field(pattern=_SHA256_PATTERN)]
    byte_size: Annotated[int, Field(strict=True, gt=0)]
    relative_path: Annotated[str, Field(min_length=1)]

    @model_validator(mode="after")
    def validate_reference(self) -> "M1CheckpointReference":
        if self.seed not in M1_SEEDS:
            raise ValueError("checkpoint seed must belong to the frozen M1 sequence")
        expected = _checkpoint_relative_path(
            self.manifest_sha256,
            self.seed,
            self.sha256,
        )
        if self.relative_path != expected:
            raise ValueError("relative_path must match the checkpoint content address")
        return self


class M1SelectionRecord(ContractModel):
    """Auditable history and selected checkpoint for one frozen M1 seed."""

    selection_version: Literal["topolab.m1.selection.v1"] = (
        "topolab.m1.selection.v1"
    )
    training_contract: M1TrainingContract = M1_TRAINING_CONTRACT
    manifest_sha256: Annotated[str, Field(pattern=_SHA256_PATTERN)]
    label_source_revision: Annotated[str, Field(pattern=_REVISION_PATTERN)]
    training_source_revision: Annotated[str, Field(pattern=_REVISION_PATTERN)]
    source_tree_clean: Literal[True] = True
    runtime: M1RuntimeEnvironment
    seed: Annotated[int, Field(strict=True)]
    training_case_ids: Annotated[tuple[str, ...], Field(min_length=1)]
    validation_case_ids: Annotated[tuple[str, ...], Field(min_length=1)]
    history: Annotated[tuple[M1EpochMetrics, ...], Field(min_length=1)]
    selected_epoch: Annotated[int, Field(strict=True, gt=0)]
    selected_validation_mse: Annotated[float, Field(strict=True, ge=0.0)]
    stopped_early: bool
    training_duration_seconds: Annotated[float, Field(strict=True, ge=0.0)]
    checkpoint: M1CheckpointReference

    @model_validator(mode="after")
    def validate_selection(self) -> "M1SelectionRecord":
        if self.seed not in M1_SEEDS:
            raise ValueError("selection seed must belong to the frozen M1 sequence")
        if self.training_case_ids != tuple(sorted(self.training_case_ids)):
            raise ValueError("training_case_ids must be sorted")
        if self.validation_case_ids != tuple(sorted(self.validation_case_ids)):
            raise ValueError("validation_case_ids must be sorted")
        if set(self.training_case_ids) & set(self.validation_case_ids):
            raise ValueError("training and validation case IDs must be disjoint")
        epochs = tuple(metrics.epoch for metrics in self.history)
        if epochs != tuple(range(1, len(self.history) + 1)):
            raise ValueError("selection history epochs must be contiguous from one")
        if len(self.history) > M1_TRAINING_CONTRACT.max_epochs:
            raise ValueError("selection history exceeds the frozen epoch budget")

        best = min(
            self.history,
            key=lambda metrics: (metrics.mean_validation_mse, metrics.epoch),
        )
        if (
            self.selected_epoch != best.epoch
            or self.selected_validation_mse != best.mean_validation_mse
        ):
            raise ValueError("selected checkpoint must be the earliest validation minimum")
        if self.stopped_early != (
            len(self.history) < M1_TRAINING_CONTRACT.max_epochs
        ):
            raise ValueError("stopped_early must match the frozen epoch budget")
        if self.stopped_early and (
            self.history[-1].epoch - self.selected_epoch
            != M1_TRAINING_CONTRACT.early_stopping_patience
        ):
            raise ValueError("early stopping must match the frozen patience")
        checkpoint = self.checkpoint
        if (
            checkpoint.manifest_sha256 != self.manifest_sha256
            or checkpoint.label_source_revision != self.label_source_revision
            or checkpoint.training_source_revision != self.training_source_revision
            or checkpoint.runtime != self.runtime
            or checkpoint.seed != self.seed
            or checkpoint.selected_epoch != self.selected_epoch
        ):
            raise ValueError("checkpoint reference does not match the selection")
        return self

    @classmethod
    def from_fit(
        cls,
        fit: M1FitResult,
        *,
        materialization: DatasetMaterializationIndex,
        training_dataset: M1TensorDataset,
        validation_dataset: M1TensorDataset,
        training_source_revision: str,
        runtime: M1RuntimeEnvironment,
        checkpoint: M1CheckpointReference,
    ) -> "M1SelectionRecord":
        return cls(
            manifest_sha256=build_manifest_sha256(materialization.manifest),
            label_source_revision=materialization.manifest.source_revision,
            training_source_revision=training_source_revision,
            runtime=runtime,
            seed=fit.seed,
            training_case_ids=training_dataset.case_ids,
            validation_case_ids=validation_dataset.case_ids,
            history=fit.history,
            selected_epoch=fit.selected_epoch,
            selected_validation_mse=fit.selected_validation_mse,
            stopped_early=fit.stopped_early,
            training_duration_seconds=fit.duration_seconds,
            checkpoint=checkpoint,
        )


class M1SelectionReference(ContractModel):
    """Verified content-addressed reference to one canonical selection record."""

    artifact_version: Literal["topolab.m1.selection.v1"] = (
        "topolab.m1.selection.v1"
    )
    manifest_sha256: Annotated[str, Field(pattern=_SHA256_PATTERN)]
    seed: Annotated[int, Field(strict=True)]
    sha256: Annotated[str, Field(pattern=_SHA256_PATTERN)]
    byte_size: Annotated[int, Field(strict=True, gt=0)]
    relative_path: Annotated[str, Field(min_length=1)]

    @classmethod
    def from_selection(cls, selection: M1SelectionRecord) -> "M1SelectionReference":
        contents = canonical_selection_bytes(selection)
        digest = hashlib.sha256(contents).hexdigest()
        return cls(
            manifest_sha256=selection.manifest_sha256,
            seed=selection.seed,
            sha256=digest,
            byte_size=len(contents),
            relative_path=_selection_relative_path(
                selection.manifest_sha256,
                selection.seed,
                digest,
            ),
        )

    @model_validator(mode="after")
    def validate_reference(self) -> "M1SelectionReference":
        if self.seed not in M1_SEEDS:
            raise ValueError("selection seed must belong to the frozen M1 sequence")
        expected = _selection_relative_path(
            self.manifest_sha256,
            self.seed,
            self.sha256,
        )
        if self.relative_path != expected:
            raise ValueError("relative_path must match the selection content address")
        return self


def capture_m1_runtime(lockfile: Path) -> M1RuntimeEnvironment:
    """Capture locked package, platform, and PyTorch thread metadata."""

    try:
        lockfile_sha256 = hashlib.sha256(lockfile.read_bytes()).hexdigest()
    except OSError as error:
        raise M1ArtifactError("could not read the training uv.lock") from error
    return M1RuntimeEnvironment(
        python_version=platform.python_version(),
        numpy_version=importlib.metadata.version("numpy"),
        scipy_version=importlib.metadata.version("scipy"),
        torch_version=torch.__version__,
        safetensors_version=importlib.metadata.version("safetensors"),
        lockfile_sha256=lockfile_sha256,
        platform_system=platform.system(),
        platform_machine=platform.machine(),
        processor=platform.processor(),
        torch_num_threads=torch.get_num_threads(),
        torch_num_interop_threads=torch.get_num_interop_threads(),
    )


def canonical_selection_bytes(selection: M1SelectionRecord) -> bytes:
    """Serialize one selection record as the exact bytes covered by its checksum."""

    return _canonical_json_bytes(selection.model_dump(mode="json"))


def write_m1_checkpoint(
    root: Path,
    fit: M1FitResult,
    *,
    materialization: DatasetMaterializationIndex,
    training_source_revision: str,
    runtime: M1RuntimeEnvironment,
) -> M1CheckpointReference:
    """Atomically write the selected model state as verified Safetensors bytes."""

    reference, contents = _build_checkpoint(
        fit,
        materialization=materialization,
        training_source_revision=training_source_revision,
        runtime=runtime,
    )
    _write_content_addressed(root, reference.relative_path, contents, "checkpoint")
    return reference


def read_m1_checkpoint(
    root: Path,
    reference: M1CheckpointReference,
) -> dict[str, Tensor]:
    """Read and validate one content-addressed Safetensors checkpoint."""

    contents = _read_content_addressed(root, reference, "checkpoint")
    try:
        state = load_tensors(contents)
    except SafetensorError as error:
        raise M1ArtifactError("checkpoint Safetensors validation failed") from error
    _validate_checkpoint_state(state)
    if _read_checkpoint_metadata(contents) != _checkpoint_metadata(reference):
        raise M1ArtifactError("checkpoint provenance does not match its reference")
    return state


def load_m1_model(root: Path, reference: M1CheckpointReference) -> WarmStartCNN:
    """Load a verified checkpoint into the frozen M1 architecture."""

    model = WarmStartCNN()
    model.load_state_dict(read_m1_checkpoint(root, reference), strict=True)
    model.eval()
    return model


def write_m1_selection(
    root: Path,
    selection: M1SelectionRecord,
) -> M1SelectionReference:
    """Atomically write one canonical checkpoint-selection record."""

    read_m1_checkpoint(root, selection.checkpoint)
    contents = canonical_selection_bytes(selection)
    reference = M1SelectionReference.from_selection(selection)
    _write_content_addressed(root, reference.relative_path, contents, "selection")
    return reference


def read_m1_selection(
    root: Path,
    reference: M1SelectionReference,
) -> M1SelectionRecord:
    """Read one canonical selection record and verify its checkpoint."""

    contents = _read_content_addressed(root, reference, "selection")
    try:
        selection = M1SelectionRecord.model_validate_json(contents)
    except ValidationError as error:
        raise M1ArtifactError("selection schema validation failed") from error
    if canonical_selection_bytes(selection) != contents:
        raise M1ArtifactError("selection is not canonical JSON")
    if M1SelectionReference.from_selection(selection) != reference:
        raise M1ArtifactError("selection content does not match its reference")
    read_m1_checkpoint(root, selection.checkpoint)
    return selection


def write_m1_fit_artifacts(
    root: Path,
    fit: M1FitResult,
    *,
    materialization: DatasetMaterializationIndex,
    training_dataset: M1TensorDataset,
    validation_dataset: M1TensorDataset,
    training_source_revision: str,
    runtime: M1RuntimeEnvironment,
) -> M1SelectionReference:
    """Persist one selected checkpoint followed by its auditable selection record."""

    _validate_fit_context(materialization, training_dataset, validation_dataset)
    checkpoint, checkpoint_bytes = _build_checkpoint(
        fit,
        materialization=materialization,
        training_source_revision=training_source_revision,
        runtime=runtime,
    )
    selection = M1SelectionRecord.from_fit(
        fit,
        materialization=materialization,
        training_dataset=training_dataset,
        validation_dataset=validation_dataset,
        training_source_revision=training_source_revision,
        runtime=runtime,
        checkpoint=checkpoint,
    )
    _write_content_addressed(
        root,
        checkpoint.relative_path,
        checkpoint_bytes,
        "checkpoint",
    )
    return write_m1_selection(root, selection)


def train_all_m1_seeds(
    data_root: Path,
    artifact_root: Path,
    materialization: DatasetMaterializationIndex,
    *,
    training_source_revision: str,
    runtime: M1RuntimeEnvironment,
) -> tuple[M1SelectionReference, ...]:
    """Train and persist all five frozen seeds without opening held-out labels."""

    training_dataset = build_m1_tensor_dataset(
        data_root,
        materialization,
        split="train",
    )
    validation_dataset = build_m1_tensor_dataset(
        data_root,
        materialization,
        split="validation",
    )
    references: list[M1SelectionReference] = []
    for seed in M1_SEEDS:
        fit = fit_m1_model(training_dataset, validation_dataset, seed=seed)
        references.append(
            write_m1_fit_artifacts(
                artifact_root,
                fit,
                materialization=materialization,
                training_dataset=training_dataset,
                validation_dataset=validation_dataset,
                training_source_revision=training_source_revision,
                runtime=runtime,
            )
        )
    return tuple(references)


def _build_checkpoint(
    fit: M1FitResult,
    *,
    materialization: DatasetMaterializationIndex,
    training_source_revision: str,
    runtime: M1RuntimeEnvironment,
) -> tuple[M1CheckpointReference, bytes]:
    state = {name: tensor.detach().cpu().contiguous() for name, tensor in fit.selected_state}
    _validate_checkpoint_state(state)
    manifest_sha256 = build_manifest_sha256(materialization.manifest)
    provenance = _checkpoint_metadata_values(
        manifest_sha256=manifest_sha256,
        label_source_revision=materialization.manifest.source_revision,
        training_source_revision=training_source_revision,
        runtime=runtime,
        seed=fit.seed,
        selected_epoch=fit.selected_epoch,
    )
    metadata = json.dumps(
        provenance,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    contents = save_tensors(dict(sorted(state.items())), metadata={"topolab": metadata})
    digest = hashlib.sha256(contents).hexdigest()
    reference = M1CheckpointReference(
        manifest_sha256=manifest_sha256,
        label_source_revision=materialization.manifest.source_revision,
        training_source_revision=training_source_revision,
        runtime=runtime,
        seed=fit.seed,
        selected_epoch=fit.selected_epoch,
        sha256=digest,
        byte_size=len(contents),
        relative_path=_checkpoint_relative_path(manifest_sha256, fit.seed, digest),
    )
    return reference, contents


def _checkpoint_metadata(reference: M1CheckpointReference) -> dict[str, object]:
    return _checkpoint_metadata_values(
        manifest_sha256=reference.manifest_sha256,
        label_source_revision=reference.label_source_revision,
        training_source_revision=reference.training_source_revision,
        runtime=reference.runtime,
        seed=reference.seed,
        selected_epoch=reference.selected_epoch,
    )


def _checkpoint_metadata_values(
    *,
    manifest_sha256: str,
    label_source_revision: str,
    training_source_revision: str,
    runtime: M1RuntimeEnvironment,
    seed: int,
    selected_epoch: int,
) -> dict[str, object]:
    return {
        "artifact_version": M1_CHECKPOINT_ARTIFACT_VERSION,
        "label_source_revision": label_source_revision,
        "manifest_sha256": manifest_sha256,
        "model_version": "topolab.m1.cnn.v1",
        "runtime": runtime.model_dump(mode="json"),
        "seed": seed,
        "selected_epoch": selected_epoch,
        "source_tree_clean": True,
        "training_contract_version": "topolab.m1.training.v1",
        "training_source_revision": training_source_revision,
    }


def _read_checkpoint_metadata(contents: bytes) -> object:
    try:
        header_size = int.from_bytes(contents[:8], "little")
        header = json.loads(contents[8 : 8 + header_size])
        metadata = header["__metadata__"]["topolab"]
        return json.loads(metadata)
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise M1ArtifactError("checkpoint provenance metadata is invalid") from error


def _validate_checkpoint_state(state: dict[str, Tensor]) -> None:
    with torch.random.fork_rng(devices=[]):
        expected = WarmStartCNN().state_dict()
    if set(state) != set(expected):
        raise M1ArtifactError("checkpoint tensors do not match the frozen model")
    for name, tensor in state.items():
        if tensor.dtype != torch.float32:
            raise M1ArtifactError("checkpoint tensors must have dtype float32")
        if tuple(tensor.shape) != tuple(expected[name].shape):
            raise M1ArtifactError("checkpoint tensor shape does not match the frozen model")
        if not torch.isfinite(tensor).all():
            raise M1ArtifactError("checkpoint tensors must contain only finite values")


def _validate_fit_context(
    materialization: DatasetMaterializationIndex,
    training_dataset: M1TensorDataset,
    validation_dataset: M1TensorDataset,
) -> None:
    if materialization.state != "complete" or any(
        isinstance(entry, MaterializationFailure) for entry in materialization.entries
    ):
        raise M1ArtifactError("M1 artifacts require a complete zero-failure materialization")
    expected_training = tuple(
        sample.case.case_id
        for sample in materialization.manifest.samples
        if sample.split == "train"
    )
    expected_validation = tuple(
        sample.case.case_id
        for sample in materialization.manifest.samples
        if sample.split == "validation"
    )
    if training_dataset.split != "train" or training_dataset.case_ids != expected_training:
        raise M1ArtifactError("training dataset does not match the manifest train split")
    if (
        validation_dataset.split != "validation"
        or validation_dataset.case_ids != expected_validation
    ):
        raise M1ArtifactError(
            "validation dataset does not match the manifest validation split"
        )


def _canonical_json_bytes(payload: object) -> bytes:
    serialized = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"{serialized}\n".encode()


def _write_content_addressed(
    root: Path,
    relative_path: str,
    contents: bytes,
    kind: str,
) -> None:
    target = root.joinpath(*PurePosixPath(relative_path).parts)
    temporary_path: Path | None = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != contents:
                raise M1ArtifactError(f"existing {kind} has different content")
            return
        with NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".topolab-m1-{kind}-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(contents)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, target)
    except M1ArtifactError:
        raise
    except OSError as error:
        raise M1ArtifactError(f"could not write {kind}") from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass


def _read_content_addressed(
    root: Path,
    reference: M1CheckpointReference | M1SelectionReference,
    kind: str,
) -> bytes:
    target = root.joinpath(*PurePosixPath(reference.relative_path).parts)
    try:
        contents = target.read_bytes()
    except FileNotFoundError as error:
        raise M1ArtifactError(f"{kind} is missing") from error
    except OSError as error:
        raise M1ArtifactError(f"could not read {kind}") from error
    if len(contents) != reference.byte_size:
        raise M1ArtifactError(f"{kind} byte size does not match reference")
    if hashlib.sha256(contents).hexdigest() != reference.sha256:
        raise M1ArtifactError(f"{kind} checksum does not match reference")
    return contents


def _checkpoint_relative_path(manifest_sha256: str, seed: int, digest: str) -> str:
    return f"m1/checkpoints/{manifest_sha256}/{seed}/{digest}.safetensors"


def _selection_relative_path(manifest_sha256: str, seed: int, digest: str) -> str:
    return f"m1/selections/{manifest_sha256}/{seed}/{digest}.json"
