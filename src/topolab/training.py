"""Frozen M1 recipe, model, loss, datasets, and deterministic fitting."""

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Annotated, Literal

import numpy as np
import torch
from numpy.typing import NDArray
from pydantic import Field, model_validator
from torch import Tensor, nn
from torch.optim import AdamW
from torch.utils.data import DataLoader, Dataset

from topolab.dataset import DatasetSample
from topolab.experiment import INPUT_CHANNEL_COUNT, encode_case
from topolab.label_artifacts import LabelArtifactError, read_label_artifact
from topolab.labels import LabelRecord
from topolab.materialization import (
    DatasetMaterializationIndex,
    MaterializationFailure,
    MaterializationSuccess,
)
from topolab.problem import ContractModel

M1_TRAINING_CONTRACT_VERSION = "topolab.m1.training.v1"
M1_MODEL_VERSION = "topolab.m1.cnn.v1"
M1_LOSS_VERSION = "topolab.m1.design-mse.v1"
M1_SEEDS = (17, 29, 43, 71, 113)
M1_HIDDEN_CHANNELS = 16
M1_MODEL_PARAMETER_COUNT = 11_281
M1_ADAM_BETAS = (0.9, 0.999)
M1_ADAM_EPSILON = 1e-8

type M1DatasetSplit = Literal["train", "validation"]


class M1DatasetError(RuntimeError):
    """Raised when materialized data cannot safely back an M1 dataset."""


class M1TrainingError(RuntimeError):
    """Raised when the frozen M1 fitting loop cannot run safely."""


class M1TrainingContract(ContractModel):
    """One fixed M1 architecture and training-selection recipe."""

    contract_version: Literal["topolab.m1.training.v1"] = "topolab.m1.training.v1"
    model_version: Literal["topolab.m1.cnn.v1"] = "topolab.m1.cnn.v1"
    loss_version: Literal["topolab.m1.design-mse.v1"] = (
        "topolab.m1.design-mse.v1"
    )
    input_channels: Literal[10] = 10
    hidden_channels: Literal[16] = 16
    parameter_count: Literal[11281] = 11_281
    optimizer: Literal["adamw"] = "adamw"
    learning_rate: Annotated[float, Field(strict=True, gt=0.0)] = 0.001
    weight_decay: Annotated[float, Field(strict=True, ge=0.0)] = 0.0001
    batch_size: Literal[8] = 8
    max_epochs: Literal[200] = 200
    early_stopping_patience: Literal[25] = 25
    dataloader_workers: Literal[0] = 0
    device: Literal["cpu"] = "cpu"
    seeds: tuple[Annotated[int, Field(strict=True)], ...] = M1_SEEDS
    checkpoint_metric: Literal["mean_validation_design_density_mse"] = (
        "mean_validation_design_density_mse"
    )
    checkpoint_tie_break: Literal["earliest_epoch"] = "earliest_epoch"
    hyperparameter_configurations: Literal[1] = 1

    @model_validator(mode="after")
    def validate_recipe(self) -> "M1TrainingContract":
        if self.seeds != M1_SEEDS:
            raise ValueError("seeds must match the frozen M1 seed sequence")
        if self.learning_rate != 0.001 or self.weight_decay != 0.0001:
            raise ValueError("optimizer parameters must match the frozen M1 recipe")
        return self


M1_TRAINING_CONTRACT = M1TrainingContract()


class M1EpochMetrics(ContractModel):
    """Mean elementwise losses for one completed fitting epoch."""

    epoch: Annotated[int, Field(strict=True, gt=0)]
    mean_training_mse: Annotated[float, Field(strict=True, ge=0.0)]
    mean_validation_mse: Annotated[float, Field(strict=True, ge=0.0)]


@dataclass(frozen=True, slots=True)
class M1FitResult:
    """Selected in-memory state and audit metrics for one seed."""

    seed: int
    history: tuple[M1EpochMetrics, ...]
    selected_epoch: int
    selected_validation_mse: float
    stopped_early: bool
    duration_seconds: float
    selected_state: tuple[tuple[str, Tensor], ...]


class WarmStartCNN(nn.Module):
    """The fixed shape-preserving M1 3D CNN."""

    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Conv3d(INPUT_CHANNEL_COUNT, M1_HIDDEN_CHANNELS, 3, padding=1),
            nn.ReLU(),
            nn.Conv3d(M1_HIDDEN_CHANNELS, M1_HIDDEN_CHANNELS, 3, padding=1),
            nn.ReLU(),
            nn.Conv3d(M1_HIDDEN_CHANNELS, 1, 1),
            nn.Sigmoid(),
        )

    def forward(self, inputs: Tensor) -> Tensor:
        if inputs.ndim != 5 or inputs.shape[1] != INPUT_CHANNEL_COUNT:
            raise ValueError("inputs must have shape (batch, 10, z, y, x)")
        if inputs.dtype != torch.float32:
            raise TypeError("inputs must have dtype float32")
        outputs = self.network(inputs)
        if not isinstance(outputs, Tensor):  # pragma: no cover - Sequential is fixed
            raise TypeError("model output must be a tensor")
        return outputs


def design_density_mse(prediction: Tensor, target: Tensor) -> Tensor:
    """Return the frozen elementwise mean-squared design-density loss."""

    if prediction.shape != target.shape:
        raise ValueError("prediction and target must have identical shapes")
    if prediction.dtype != torch.float32 or target.dtype != torch.float32:
        raise TypeError("prediction and target must have dtype float32")
    if not torch.isfinite(prediction).all() or not torch.isfinite(target).all():
        raise ValueError("prediction and target must contain only finite values")
    return torch.mean(torch.square(prediction - target))


def fit_m1_model(
    training_dataset: "M1TensorDataset",
    validation_dataset: "M1TensorDataset",
    *,
    seed: int,
) -> M1FitResult:
    """Fit one frozen M1 seed and select the earliest minimum validation epoch."""

    return _fit_m1_model(
        training_dataset,
        validation_dataset,
        seed=seed,
        max_epochs=M1_TRAINING_CONTRACT.max_epochs,
        early_stopping_patience=M1_TRAINING_CONTRACT.early_stopping_patience,
    )


class M1TensorDataset(Dataset[tuple[Tensor, Tensor]]):
    """An in-memory train or validation view over verified M0 artifacts."""

    def __init__(
        self,
        *,
        split: M1DatasetSplit,
        case_ids: tuple[str, ...],
        inputs: Tensor,
        targets: Tensor,
    ) -> None:
        if split not in ("train", "validation"):
            raise ValueError("M1 datasets support only train or validation")
        if not case_ids or case_ids != tuple(sorted(case_ids)):
            raise ValueError("case_ids must be a nonempty sorted sequence")
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("case_ids must be unique")
        if inputs.ndim != 5 or inputs.shape[0] != len(case_ids):
            raise ValueError("inputs must have shape (case, channel, z, y, x)")
        if inputs.shape[1] != INPUT_CHANNEL_COUNT:
            raise ValueError("inputs must have ten frozen M0 channels")
        if targets.shape != (len(case_ids), 1, *inputs.shape[2:]):
            raise ValueError("targets must match the input case and spatial dimensions")
        if inputs.dtype != torch.float32 or targets.dtype != torch.float32:
            raise TypeError("dataset tensors must have dtype float32")
        if not torch.isfinite(inputs).all() or not torch.isfinite(targets).all():
            raise ValueError("dataset tensors must contain only finite values")

        self.split = split
        self.case_ids = case_ids
        self._inputs = inputs.detach().clone().contiguous()
        self._targets = targets.detach().clone().contiguous()

    def __len__(self) -> int:
        return len(self.case_ids)

    def __getitem__(self, index: int) -> tuple[Tensor, Tensor]:
        return self._inputs[index], self._targets[index]


def _fit_m1_model(
    training_dataset: M1TensorDataset,
    validation_dataset: M1TensorDataset,
    *,
    seed: int,
    max_epochs: int,
    early_stopping_patience: int,
) -> M1FitResult:
    if seed not in M1_SEEDS:
        raise M1TrainingError("seed must belong to the frozen M1 seed sequence")
    if training_dataset.split != "train":
        raise M1TrainingError("training_dataset must use the train split")
    if validation_dataset.split != "validation":
        raise M1TrainingError("validation_dataset must use the validation split")
    if training_dataset._inputs.shape[2:] != validation_dataset._inputs.shape[2:]:
        raise M1TrainingError("training and validation spatial shapes must match")
    if max_epochs <= 0 or early_stopping_patience <= 0:
        raise ValueError("fitting limits must be positive")

    started = perf_counter()
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    deterministic_was_enabled = torch.are_deterministic_algorithms_enabled()
    deterministic_warn_only_was_enabled = (
        torch.is_deterministic_algorithms_warn_only_enabled()
    )

    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(True)
        try:
            model = WarmStartCNN()
            optimizer = AdamW(
                model.parameters(),
                lr=M1_TRAINING_CONTRACT.learning_rate,
                betas=M1_ADAM_BETAS,
                eps=M1_ADAM_EPSILON,
                weight_decay=M1_TRAINING_CONTRACT.weight_decay,
                amsgrad=False,
            )
            training_loader = DataLoader(
                training_dataset,
                batch_size=M1_TRAINING_CONTRACT.batch_size,
                shuffle=True,
                num_workers=M1_TRAINING_CONTRACT.dataloader_workers,
                generator=generator,
            )
            validation_loader = DataLoader(
                validation_dataset,
                batch_size=M1_TRAINING_CONTRACT.batch_size,
                shuffle=False,
                num_workers=M1_TRAINING_CONTRACT.dataloader_workers,
            )
            history: list[M1EpochMetrics] = []
            best_validation = float("inf")
            best_epoch = 0
            best_state: tuple[tuple[str, Tensor], ...] = ()
            epochs_without_improvement = 0

            for epoch in range(1, max_epochs + 1):
                model.train()
                training_squared_error = 0.0
                training_elements = 0
                for inputs, targets in training_loader:
                    optimizer.zero_grad(set_to_none=True)
                    predictions = model(inputs)
                    loss = design_density_mse(predictions, targets)
                    torch.autograd.backward(loss)
                    optimizer.step()
                    training_squared_error += loss.item() * targets.numel()
                    training_elements += targets.numel()

                model.eval()
                validation_squared_error = 0.0
                validation_elements = 0
                with torch.no_grad():
                    for inputs, targets in validation_loader:
                        predictions = model(inputs)
                        loss = design_density_mse(predictions, targets)
                        validation_squared_error += loss.item() * targets.numel()
                        validation_elements += targets.numel()

                if training_elements == 0 or validation_elements == 0:
                    raise M1TrainingError("fitting datasets must be nonempty")
                training_mse = training_squared_error / training_elements
                validation_mse = validation_squared_error / validation_elements
                metrics = M1EpochMetrics(
                    epoch=epoch,
                    mean_training_mse=training_mse,
                    mean_validation_mse=validation_mse,
                )
                history.append(metrics)

                if validation_mse < best_validation:
                    best_validation = validation_mse
                    best_epoch = epoch
                    best_state = tuple(
                        (name, tensor.detach().cpu().clone())
                        for name, tensor in sorted(model.state_dict().items())
                    )
                    epochs_without_improvement = 0
                else:
                    epochs_without_improvement += 1
                    if epochs_without_improvement >= early_stopping_patience:
                        break
        finally:
            torch.use_deterministic_algorithms(
                deterministic_was_enabled,
                warn_only=deterministic_warn_only_was_enabled,
            )

    if not best_state or best_epoch == 0:
        raise M1TrainingError("fitting did not produce a selected checkpoint")
    return M1FitResult(
        seed=seed,
        history=tuple(history),
        selected_epoch=best_epoch,
        selected_validation_mse=best_validation,
        stopped_early=len(history) < max_epochs,
        duration_seconds=perf_counter() - started,
        selected_state=best_state,
    )


def build_m1_tensor_dataset(
    root: Path,
    materialization: DatasetMaterializationIndex,
    *,
    split: M1DatasetSplit,
) -> M1TensorDataset:
    """Load one verified train or validation dataset without opening held-out labels."""

    if split not in ("train", "validation"):
        raise ValueError("M1 datasets support only train or validation")
    if materialization.state != "complete":
        raise M1DatasetError("M1 data must be fully materialized")
    if any(isinstance(entry, MaterializationFailure) for entry in materialization.entries):
        raise M1DatasetError("M1 data cannot contain failed cases")

    entries = {
        entry.case_id: entry
        for entry in materialization.entries
        if isinstance(entry, MaterializationSuccess)
    }
    samples = tuple(
        sample for sample in materialization.manifest.samples if sample.split == split
    )
    if not samples:
        raise M1DatasetError(f"materialization has no {split} samples")

    inputs: list[NDArray[np.float32]] = []
    targets: list[NDArray[np.float32]] = []
    for sample in samples:
        entry = entries.get(sample.case.case_id)
        if entry is None:
            raise M1DatasetError(f"{split} sample is missing a label artifact")
        label = _read_sample_label(root, materialization, sample, entry)
        inputs.append(encode_case(sample.case).input_tensor)
        targets.append(label.design_tensor())

    return M1TensorDataset(
        split=split,
        case_ids=tuple(sample.case.case_id for sample in samples),
        inputs=torch.from_numpy(np.stack(inputs)),
        targets=torch.from_numpy(np.stack(targets)),
    )


def _read_sample_label(
    root: Path,
    materialization: DatasetMaterializationIndex,
    sample: DatasetSample,
    entry: MaterializationSuccess,
) -> LabelRecord:
    try:
        label = read_label_artifact(root, entry.artifact)
    except LabelArtifactError as error:
        raise M1DatasetError(
            f"{sample.split} label artifact verification failed"
        ) from error
    manifest = materialization.manifest
    if (
        label.case != sample.case
        or label.source_revision != manifest.source_revision
        or label.environment != manifest.environment
        or label.case_schema_version != manifest.case_schema_version
        or label.generator_version != manifest.generator_version
        or label.solver_contract_version != manifest.solver_contract_version
    ):
        raise M1DatasetError(f"{sample.split} label does not match the manifest")
    return label
