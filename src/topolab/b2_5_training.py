"""Two-arm, shape-bucketed B2.5 fitting on verified development labels."""

from dataclasses import dataclass
from time import perf_counter
from typing import Literal

import numpy as np
import torch
from torch import Tensor
from torch.optim import AdamW

from topolab.b2_4_labels import B24Label
from topolab.experiment import ExperimentCase, encode_case
from topolab.training import (
    M1_ADAM_BETAS,
    M1_ADAM_EPSILON,
    M1_MODEL_PARAMETER_COUNT,
    WarmStartCNN,
)

type B25Arm = Literal["control", "candidate"]
type B25Split = Literal["train", "validation"]

SEEDS = (17, 29, 43)
MAX_EPOCHS = 200
PATIENCE = 25
BATCH_SIZE = 8
SMALL_SHAPE = (3, 6, 12)
LARGE_SHAPE = (6, 12, 24)


@dataclass(frozen=True, slots=True)
class B25Sample:
    case: ExperimentCase
    split: B25Split
    inputs: Tensor
    design: Tensor
    weight: Tensor

    @classmethod
    def from_label(cls, label: B24Label) -> "B25Sample":
        shape = label.tensor_shape
        sample = cls(
            case=label.case,
            split=label.split,
            inputs=torch.from_numpy(encode_case(label.case).input_tensor.copy()),
            design=torch.from_numpy(
                np.asarray(label.design_density, dtype=np.float32).reshape(shape).copy()
            ),
            weight=torch.from_numpy(
                np.asarray(label.sensitivity_weight, dtype=np.float32)
                .reshape(shape)
                .copy()
            ),
        )
        sample.validate()
        return sample

    def validate(self) -> None:
        if self.split not in ("train", "validation"):
            raise ValueError("B2.5 supports only development train and validation")
        shape = tuple(self.inputs.shape[1:])
        if shape not in (SMALL_SHAPE, LARGE_SHAPE):
            raise ValueError("B2.5 sample has an unexpected spatial shape")
        if tuple(self.inputs.shape) != (10, *shape):
            raise ValueError("B2.5 sample input has the wrong channels")
        if tuple(self.design.shape) != (1, *shape) or self.weight.shape != self.design.shape:
            raise ValueError("B2.5 target and weights must share the input shape")
        for tensor in (self.inputs, self.design, self.weight):
            if tensor.dtype != torch.float32 or tensor.device.type != "cpu":
                raise ValueError("B2.5 tensors must be CPU float32")
            if not torch.isfinite(tensor).all():
                raise ValueError("B2.5 tensors must be finite")
        if not torch.all(self.weight > 0):
            raise ValueError("B2.5 sensitivity weights must be positive")

    @property
    def shape(self) -> tuple[int, int, int]:
        return tuple(self.inputs.shape[1:])  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class B25Fit:
    arm: B25Arm
    seed: int
    history: tuple[dict[str, float | int], ...]
    selected_epoch: int
    selected_validation_loss: float
    duration_seconds: float
    state: dict[str, Tensor]


def _sorted_split(samples: tuple[B25Sample, ...], split: B25Split) -> tuple[B25Sample, ...]:
    if not samples or any(sample.split != split for sample in samples):
        raise ValueError("B2.5 samples must be a nonempty single split")
    if tuple(sample.case.case_id for sample in samples) != tuple(
        sorted(sample.case.case_id for sample in samples)
    ):
        raise ValueError("B2.5 samples must be sorted by case ID")
    if len({sample.case.case_id for sample in samples}) != len(samples):
        raise ValueError("B2.5 sample case IDs must be unique")
    for sample in samples:
        sample.validate()
    return samples


def shape_batches(
    samples: tuple[B25Sample, ...], generator: torch.Generator
) -> tuple[tuple[int, ...], ...]:
    """One fixed-exposure, 59-step epoch of pure-shape batches."""

    batches: list[tuple[int, ...]] = []
    for shape in (SMALL_SHAPE, LARGE_SHAPE):
        indices = [index for index, sample in enumerate(samples) if sample.shape == shape]
        if not indices:
            raise ValueError("both frozen B2.5 spatial shapes are required")
        order = torch.randperm(len(indices), generator=generator).tolist()
        shuffled = [indices[index] for index in order]
        for start in range(0, len(shuffled), BATCH_SIZE):
            batches.append(tuple(shuffled[start : start + BATCH_SIZE]))
    order = torch.randperm(len(batches), generator=generator).tolist()
    return tuple(batches[index] for index in order)


def _loss(prediction: Tensor, sample: Tensor, weight: Tensor, arm: B25Arm) -> Tensor:
    if prediction.shape != sample.shape or weight.shape != sample.shape:
        raise ValueError("B2.5 loss tensors must have identical shape")
    if arm not in ("control", "candidate"):
        raise ValueError("B2.5 arm is invalid")
    squared = torch.square(prediction - sample)
    return torch.mean(squared if arm == "control" else squared * weight)


def _batch_tensors(
    samples: tuple[B25Sample, ...], indices: tuple[int, ...]
) -> tuple[Tensor, Tensor, Tensor]:
    return (
        torch.stack([samples[index].inputs for index in indices]),
        torch.stack([samples[index].design for index in indices]),
        torch.stack([samples[index].weight for index in indices]),
    )


def fit_b25_arm(
    train: tuple[B25Sample, ...],
    validation: tuple[B25Sample, ...],
    *,
    arm: B25Arm,
    seed: int,
) -> B25Fit:
    """Fit one frozen arm/seed; preserve the earliest own-objective minimum."""

    _sorted_split(train, "train")
    _sorted_split(validation, "validation")
    if len(train) != 468 or len(validation) != 54:
        raise ValueError("B2.5 requires the complete 468/54 development partition")
    if seed not in SEEDS or arm not in ("control", "candidate"):
        raise ValueError("B2.5 arm or seed differs from the frozen plan")
    if len({sample.case.case_id for sample in (*train, *validation)}) != 522:
        raise ValueError("B2.5 train and validation cases overlap")

    started = perf_counter()
    generator = torch.Generator(device="cpu")
    generator.manual_seed(seed)
    previous_deterministic = torch.are_deterministic_algorithms_enabled()
    previous_warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(True)
        try:
            model = WarmStartCNN()
            if (
                sum(parameter.numel() for parameter in model.parameters())
                != M1_MODEL_PARAMETER_COUNT
            ):
                raise ValueError("B2.5 model differs from the frozen M1 architecture")
            optimizer = AdamW(
                model.parameters(),
                lr=0.001,
                weight_decay=0.0001,
                betas=M1_ADAM_BETAS,
                eps=M1_ADAM_EPSILON,
                amsgrad=False,
            )
            history: list[dict[str, float | int]] = []
            selected_loss = float("inf")
            selected_epoch = 0
            selected_state: dict[str, Tensor] = {}
            stale = 0
            validation_by_shape = {
                shape: tuple(
                    index for index, sample in enumerate(validation) if sample.shape == shape
                )
                for shape in (SMALL_SHAPE, LARGE_SHAPE)
            }
            for epoch in range(1, MAX_EPOCHS + 1):
                model.train()
                train_sum = 0.0
                train_elements = 0
                batches = shape_batches(train, generator)
                if len(batches) != 59:
                    raise ValueError("B2.5 shape schedule must contain exactly 59 steps")
                for batch in batches:
                    inputs, design, weight = _batch_tensors(train, batch)
                    optimizer.zero_grad(set_to_none=True)
                    loss = _loss(model(inputs), design, weight, arm)
                    torch.autograd.backward(loss)
                    optimizer.step()
                    train_sum += loss.item() * design.numel()
                    train_elements += design.numel()

                model.eval()
                validation_sum = 0.0
                validation_elements = 0
                with torch.no_grad():
                    for shape in (SMALL_SHAPE, LARGE_SHAPE):
                        indices = validation_by_shape[shape]
                        for start in range(0, len(indices), BATCH_SIZE):
                            batch = indices[start : start + BATCH_SIZE]
                            inputs, design, weight = _batch_tensors(validation, batch)
                            loss = _loss(model(inputs), design, weight, arm)
                            validation_sum += loss.item() * design.numel()
                            validation_elements += design.numel()
                if train_elements == 0 or validation_elements == 0:
                    raise ValueError("B2.5 fitting denominator is empty")
                train_loss = train_sum / train_elements
                validation_loss = validation_sum / validation_elements
                history.append(
                    {"epoch": epoch, "training_loss": train_loss,
                     "validation_loss": validation_loss}
                )
                if validation_loss < selected_loss:
                    selected_loss = validation_loss
                    selected_epoch = epoch
                    selected_state = {
                        name: tensor.detach().cpu().clone().contiguous()
                        for name, tensor in sorted(model.state_dict().items())
                    }
                    stale = 0
                else:
                    stale += 1
                    if stale >= PATIENCE:
                        break
        finally:
            torch.use_deterministic_algorithms(
                previous_deterministic, warn_only=previous_warn_only
            )
    if not selected_state or selected_epoch == 0:
        raise ValueError("B2.5 fitting produced no selected model")
    return B25Fit(
        arm=arm,
        seed=seed,
        history=tuple(history),
        selected_epoch=selected_epoch,
        selected_validation_loss=selected_loss,
        duration_seconds=perf_counter() - started,
        state=selected_state,
    )
