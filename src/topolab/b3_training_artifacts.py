"""Checksum-bound B3 fits, guarded labels, and charged single-writer recovery."""

import fcntl
import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from math import isfinite
from pathlib import Path
from time import perf_counter
from typing import Annotated, Literal

import torch
from pydantic import Field, model_validator
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_6_trajectory import TrajectorySample
from topolab.b2_12_context_cnn import ContextCNN
from topolab.b3_access import B3Access
from topolab.b3_artifacts import atomic_write, read_b3_record, safe_path
from topolab.b3_catalog import Sha256, canonical_metadata_bytes
from topolab.b3_dataset import B3DataContext, B3LabelRecord, NonnegativeSeconds
from topolab.b3_materialization import B3DataSuccess, B3MaterializationIndex, _peak_rss_bytes
from topolab.b3_training import (
    MEMBERSHIPS,
    RECIPES,
    SEEDS,
    B3Fit,
    Recipe,
    fit_b3_seed,
    fitting_entries,
    sample_from_label,
    validation_mse,
)
from topolab.dataset_cli import validate_external_output_root
from topolab.problem import ContractModel

B3_DATA_INDEX_SHA256 = "b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26"
FIT_SECONDS = 7_200.0
FIT_RSS_BYTES = 4_294_967_296
MAX_ATTEMPTED_EPOCHS = 2_400
TASKS = tuple((recipe, seed) for recipe in RECIPES for seed in SEEDS)


def digest(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


class B3TrainingContext(ContractModel):
    training_version: Literal["topolab.b3.training.v1"] = "topolab.b3.training.v1"
    source: B3DataContext
    data_index_sha256: Literal[
        "b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26"
    ] = "b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26"
    data_index: B3MaterializationIndex

    @model_validator(mode="after")
    def validate_data_gate(self) -> "B3TrainingContext":
        contents = canonical_metadata_bytes(self.data_index.model_dump(mode="json"))
        if digest(contents) != self.data_index_sha256 or not self.data_index.data_gate_passed:
            raise ValueError("B3 fitting requires the unchanged, passed B3.4 data index")
        return self

    def sha256(self) -> str:
        return digest(canonical_metadata_bytes(self.model_dump(mode="json")))


class FitFile(ContractModel):
    kind: Literal["checkpoint", "selection"]
    sha256: Sha256
    byte_size: Annotated[int, Field(strict=True, gt=0)]

    @property
    def relative_path(self) -> str:
        suffix = "safetensors" if self.kind == "checkpoint" else "json"
        return f"artifacts/{self.kind}/{self.sha256}.{suffix}"


class EpochMetric(ContractModel):
    epoch: Annotated[int, Field(strict=True, ge=1, le=200)]
    training_loss: NonnegativeSeconds
    validation_loss: NonnegativeSeconds


class B3Selection(ContractModel):
    selection_version: Literal["topolab.b3.selection.v1"] = "topolab.b3.selection.v1"
    context_sha256: Sha256
    recipe: Recipe
    seed: Literal[17, 29, 43]
    history: tuple[EpochMetric, ...]
    selected_epoch: Annotated[int, Field(strict=True, ge=1, le=200)]
    selected_validation_loss: NonnegativeSeconds
    fit_seconds: NonnegativeSeconds
    checkpoint: FitFile

    @model_validator(mode="after")
    def validate_selection(self) -> "B3Selection":
        if (not self.history or len(self.history) > 200
                or tuple(h.epoch for h in self.history) != tuple(range(1, len(self.history) + 1))
                or self.checkpoint.kind != "checkpoint"):
            raise ValueError("selection requires a complete ordered fitting history")
        best, first, stale = float("inf"), 0, 0
        for position, row in enumerate(self.history, 1):
            if row.validation_loss < best:
                best, first, stale = row.validation_loss, row.epoch, 0
            else:
                stale += 1
            if stale >= 25 and position != len(self.history):
                raise ValueError("history continues past the frozen early stop")
        if len(self.history) != 200 and stale != 25:
            raise ValueError("history lacks a frozen epoch-limit or patience stop")
        if (self.selected_epoch, self.selected_validation_loss) != (first, best):
            raise ValueError("selection is not the earliest strict validation minimum")
        return self


class FitOutcome(ContractModel):
    recipe: Recipe
    seed: Literal[17, 29, 43]
    selection: FitFile

    @model_validator(mode="after")
    def validate_kind(self) -> "FitOutcome":
        if self.selection.kind != "selection":
            raise ValueError("fit outcome must bind a selection artifact")
        return self


class B3TrainingIndex(ContractModel):
    index_version: Literal["topolab.b3.training-index.v1"] = "topolab.b3.training-index.v1"
    context: B3TrainingContext
    context_sha256: Sha256
    outcomes: tuple[FitOutcome, ...] = ()
    audited_fits: tuple[tuple[Recipe, int], ...] = ()
    attempted_epochs: Annotated[int, Field(strict=True, ge=0)] = 0
    cumulative_seconds: NonnegativeSeconds = 0.0
    peak_rss_bytes: Annotated[int, Field(strict=True, ge=0)] = 0
    active_checkpoint_at: datetime | None = None
    resource_failed: bool = False
    integrity_failed: bool = False
    fitting_failed: bool = False

    @model_validator(mode="after")
    def validate_prefix(self) -> "B3TrainingIndex":
        actual = tuple((o.recipe, o.seed) for o in self.outcomes)
        if self.context_sha256 != self.context.sha256() or actual != TASKS[:len(actual)]:
            raise ValueError("training index must preserve its context and exact twelve-fit prefix")
        if self.audited_fits != tuple(task for task in actual if task in self.audited_fits):
            raise ValueError("fit audits must be a unique ordered subset of retained fits")
        if self.attempted_epochs < 26 * len(self.outcomes):
            raise ValueError("training index discounts attempted epochs")
        if self.active_checkpoint_at is not None and self.active_checkpoint_at.utcoffset() != (
            UTC.utcoffset(self.active_checkpoint_at)
        ):
            raise ValueError("resource checkpoint must be in UTC")
        return self

    @property
    def fitting_gate_passed(self) -> bool:
        return (len(self.outcomes) == 12 and self.audited_fits == TASKS
                and self.active_checkpoint_at is None
                and not (self.resource_failed or self.integrity_failed or self.fitting_failed)
                and self.cumulative_seconds <= FIT_SECONDS
                and self.peak_rss_bytes <= FIT_RSS_BYTES
                and self.attempted_epochs <= MAX_ATTEMPTED_EPOCHS)


def read_training_index(root: Path, context: B3TrainingContext) -> B3TrainingIndex:
    contents = safe_path(root, "b3_training.json").read_bytes()
    index = B3TrainingIndex.model_validate_json(contents)
    if (canonical_metadata_bytes(index.model_dump(mode="json")) != contents
            or index.context != context):
        raise ValueError("training index canonical bytes or identity differ")
    return index


def write_training_index(root: Path, index: B3TrainingIndex) -> None:
    index = B3TrainingIndex.model_validate(index.model_dump(mode="json"))
    target = safe_path(root, "b3_training.json")
    if target.exists():
        old = read_training_index(root, index.context)
        if (index.outcomes[:len(old.outcomes)] != old.outcomes
                or index.cumulative_seconds < old.cumulative_seconds
                or index.attempted_epochs < old.attempted_epochs
                or index.peak_rss_bytes < old.peak_rss_bytes
                or any(getattr(old, flag) and not getattr(index, flag)
                       for flag in ("resource_failed", "integrity_failed", "fitting_failed"))):
            raise ValueError("fit outcomes, charges and failures are append-only")
    atomic_write(target, canonical_metadata_bytes(index.model_dump(mode="json")))


def _write_file(root: Path, kind: Literal["checkpoint", "selection"], contents: bytes) -> FitFile:
    reference = FitFile(kind=kind, sha256=digest(contents), byte_size=len(contents))
    target = safe_path(root, reference.relative_path)
    if target.exists():
        if target.read_bytes() != contents:
            raise ValueError("existing content-addressed fit artifact differs")
    else:
        atomic_write(target, contents)
    return reference


def _read_file(root: Path, reference: FitFile) -> bytes:
    reference = FitFile.model_validate(reference.model_dump(mode="json"))
    contents = safe_path(root, reference.relative_path).read_bytes()
    if digest(contents) != reference.sha256 or len(contents) != reference.byte_size:
        raise ValueError("fit artifact checksum or size differs")
    return contents


def checkpoint_metadata(context: B3TrainingContext, recipe: Recipe, seed: int, epoch: int) -> str:
    return canonical_metadata_bytes({"checkpoint_version": "topolab.b3.checkpoint.v1",
                                     "context_sha256": context.sha256(), "recipe": recipe,
                                     "seed": seed, "selected_epoch": epoch}).decode()


def publish_fit(root: Path, context: B3TrainingContext, recipe: Recipe, seed: int,
                fit: B3Fit) -> FitOutcome:
    contents = save_tensors(fit.state, metadata={"topolab": checkpoint_metadata(
        context, recipe, seed, fit.selected_epoch)})
    checkpoint = _write_file(root, "checkpoint", contents)
    selection = B3Selection.model_validate({
        "context_sha256": context.sha256(), "recipe": recipe, "seed": seed,
        "history": fit.history, "selected_epoch": fit.selected_epoch,
        "selected_validation_loss": fit.selected_validation_loss,
        "fit_seconds": fit.seconds, "checkpoint": checkpoint,
    })
    reference = _write_file(root, "selection", canonical_metadata_bytes(
        selection.model_dump(mode="json")))
    return FitOutcome.model_validate({"recipe": recipe, "seed": seed, "selection": reference})


def read_selected_model(root: Path, context: B3TrainingContext,
                        outcome: FitOutcome) -> tuple[B3Selection, ContextCNN]:
    contents = _read_file(root, outcome.selection)
    selection = B3Selection.model_validate_json(contents)
    if (canonical_metadata_bytes(selection.model_dump(mode="json")) != contents
            or selection.context_sha256 != context.sha256()
            or (selection.recipe, selection.seed) != (outcome.recipe, outcome.seed)):
        raise ValueError("selection differs from its recipe, context or canonical bytes")
    contents = _read_file(root, selection.checkpoint)
    length = int.from_bytes(contents[:8], "little")
    header = json.loads(contents[8:8 + length])
    if header.get("__metadata__", {}) != {"topolab": checkpoint_metadata(
            context, outcome.recipe, outcome.seed, selection.selected_epoch)}:
        raise ValueError("checkpoint provenance differs")
    tensors = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = ContextCNN()
    expected = model.state_dict()
    if set(tensors) != set(expected) or any(
        tensor.dtype != torch.float32 or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all() for name, tensor in tensors.items()
    ):
        raise ValueError("checkpoint tensors differ from the finite float32 architecture")
    model.load_state_dict(tensors, strict=True)
    model.eval()
    return selection, model


def load_fitting_samples(
    data_root: Path, context: B3TrainingContext, recipe: Recipe,
    cache: dict[str, TrajectorySample], checkpoint: Callable[[bool], None],
) -> tuple[tuple[TrajectorySample, ...], tuple[TrajectorySample, ...]]:
    """Authorize the complete requested membership before streaming any label bytes."""
    access = B3Access(consumer="fitting", training_set=MEMBERSHIPS[recipe])
    train_ids, validation_ids = fitting_entries(recipe)
    ids = set((*train_ids, *validation_ids))
    artifacts = tuple(o.artifact for o in context.data_index.entries
                      if isinstance(o, B3DataSuccess) and o.entry.case.case_id in ids)
    actual = tuple(a.access.entry.case.case_id for a in artifacts)
    if len(actual) != len(ids) or set(actual) != ids:
        raise ValueError("fitting requires every requested label before its first byte read")
    for artifact in artifacts:
        access._authorize_bytes(artifact.access)
    for artifact in artifacts:
        checkpoint(False)
        case_id = artifact.access.entry.case.case_id
        if case_id not in cache:
            record = read_b3_record(data_root, context.data_index.manifest, artifact, access)
            if not isinstance(record, B3LabelRecord):
                raise ValueError("fitting target must be a B3 label")
            cache[case_id] = sample_from_label(record)
    return tuple(cache[i] for i in train_ids), tuple(cache[i] for i in validation_ids)


class FittingResourceExceeded(RuntimeError):
    """The frozen fitting program cannot extend its cumulative resource budget."""


def run_b3_fitting(
    root: Path, data_root: Path, context: B3TrainingContext, *, repository_root: Path,
    audit_only: bool = False, startup_seconds: float = 0.0,
) -> B3TrainingIndex:
    if not isfinite(startup_seconds) or startup_seconds < 0:
        raise ValueError("startup resource charge must be finite and nonnegative")
    started = perf_counter() - startup_seconds
    context = B3TrainingContext.model_validate(context.model_dump(mode="json"))
    root = validate_external_output_root(repository_root, root)
    if root.is_relative_to(data_root.resolve()) or data_root.resolve().is_relative_to(root):
        raise ValueError("fitting output must be separate from the immutable data root")
    root.mkdir(parents=True, exist_ok=True)
    with safe_path(root, ".b3-fitting.lock").open("a+b") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("another writer owns the fitting root") from error
        target = safe_path(root, "b3_training.json")
        if audit_only and not target.exists():
            raise ValueError("audit requires an existing training index")
        index = read_training_index(root, context) if target.exists() else B3TrainingIndex(
            context=context, context_sha256=context.sha256())
        base = index.cumulative_seconds
        if index.active_checkpoint_at is not None:
            base += max(0.0, (datetime.now(UTC) - index.active_checkpoint_at).total_seconds())
        last_flush = 0.0

        def pulse(new_epoch: bool = False, *, close: bool = False, force: bool = False) -> None:
            nonlocal index, last_flush
            elapsed = perf_counter() - started
            epoch_exhausted = new_epoch and index.attempted_epochs >= MAX_ATTEMPTED_EPOCHS
            attempts = index.attempted_epochs + int(new_epoch and not epoch_exhausted)
            rss = max(index.peak_rss_bytes, _peak_rss_bytes())
            exhausted = (base + elapsed > FIT_SECONDS or rss > FIT_RSS_BYTES
                         or epoch_exhausted or new_epoch and base + elapsed >= FIT_SECONDS)
            if new_epoch or close or force or exhausted or elapsed - last_flush >= 5:
                index = index.model_copy(update={
                    "cumulative_seconds": base + elapsed, "peak_rss_bytes": rss,
                    "attempted_epochs": attempts,
                    "resource_failed": index.resource_failed or exhausted,
                    "active_checkpoint_at": None if close else datetime.now(UTC),
                })
                write_training_index(root, index)
                last_flush = elapsed
            if exhausted:
                raise FittingResourceExceeded("B3 fitting resource budget exhausted")

        cache: dict[str, TrajectorySample] = {}
        try:
            pulse(force=True)
            if index.resource_failed or index.integrity_failed or index.fitting_failed:
                raise FittingResourceExceeded("fitting program already stopped at a failed Gate")
            total_retained_epochs = 0
            for outcome in index.outcomes:
                _, validation = load_fitting_samples(
                    data_root, context, outcome.recipe, cache, pulse)
                selection, model = read_selected_model(root, context, outcome)
                total_retained_epochs += len(selection.history)
                if validation_mse(model, validation) != selection.selected_validation_loss:
                    raise ValueError("selected weights do not reproduce their validation MSE")
                del model
                pulse()
            if total_retained_epochs > index.attempted_epochs:
                raise ValueError("epoch charges omit retained fitting work")
            if not audit_only:
                for recipe, seed in TASKS[len(index.outcomes):]:
                    pulse()
                    train, validation = load_fitting_samples(
                        data_root, context, recipe, cache, pulse)
                    try:
                        fit = fit_b3_seed(train, validation, recipe=recipe, seed=seed,
                                          checkpoint=pulse)
                    except FittingResourceExceeded:
                        raise
                    except (ValueError, RuntimeError):
                        index = index.model_copy(update={"fitting_failed": True})
                        raise
                    outcome = publish_fit(root, context, recipe, seed, fit)
                    selection, model = read_selected_model(root, context, outcome)
                    if validation_mse(model, validation) != selection.selected_validation_loss:
                        raise ValueError("selected weights do not reproduce their validation MSE")
                    del model, fit
                    index = index.model_copy(update={"outcomes": (*index.outcomes, outcome)})
                    pulse(force=True)
                    print(json.dumps({"recipe": recipe, "seed": seed,
                                      "selected_epoch": selection.selected_epoch,
                                      "epochs": len(selection.history),
                                      "cumulative_seconds": index.cumulative_seconds}), flush=True)
            index = index.model_copy(update={"audited_fits": tuple(
                (o.recipe, o.seed) for o in index.outcomes)})
        except FittingResourceExceeded:
            pass
        except (OSError, ValueError, RuntimeError):
            index = index.model_copy(update={"integrity_failed": True})
            raise
        finally:
            try:
                pulse(close=True)
            except FittingResourceExceeded:
                pass
        return index
