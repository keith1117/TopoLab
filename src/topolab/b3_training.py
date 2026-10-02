"""The twelve frozen B3 CPU fits, with equal-case checkpoint selection."""

from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite
from time import perf_counter
from typing import Literal

import numpy as np
import torch
from torch import Tensor
from torch.optim import AdamW

from topolab.b2_6_trajectory import (
    SHAPES,
    TrajectorySample,
    _batches,
    _tensors,
    case_weighted_loss,
)
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_12_context_cnn import CONTEXT_MODEL_PARAMETER_COUNT, ContextCNN
from topolab.b3_access import B3Access
from topolab.b3_catalog import B3TrainingSet, build_b3_case_catalog
from topolab.b3_dataset import B3LabelRecord

type Recipe = Literal["C", "P", "A", "S"]
RECIPES: tuple[Recipe, ...] = ("C", "P", "A", "S")
SEEDS = (17, 29, 43)
MEMBERSHIPS: dict[Recipe, B3TrainingSet] = {
    "C": "base", "P": "expanded", "A": "expanded", "S": "specialist",
}
MAX_EPOCHS = 200
PATIENCE = 25
BATCH_SIZE = 8


def fitting_entries(recipe: Recipe) -> tuple[tuple[str, ...], tuple[str, ...]]:
    entries = B3Access(consumer="fitting", training_set=MEMBERSHIPS[recipe]).case_entries()
    return (
        tuple(e.case.case_id for e in entries if e.role == "train"),
        tuple(e.case.case_id for e in entries if e.role == "fit_validation"),
    )


def case_weights(recipe: Recipe) -> dict[str, float]:
    train_ids, _ = fitting_entries(recipe)
    cases = {e.case.case_id: e.case for e in build_b3_case_catalog().entries}
    threshold = 0.55 if recipe == "S" else 0.5
    return {
        case_id: 8.0 if recipe != "A"
        and cases[case_id].problem.loads[0].direction == "y"
        and cases[case_id].problem.optimization.volume_fraction >= threshold else 1.0
        for case_id in train_ids
    }


def sample_from_label(label: B3LabelRecord) -> TrajectorySample:
    if label.entry.role not in ("train", "fit_validation"):
        raise PermissionError("fitting requires a B3 train or fit-validation label")
    case = label.entry.case
    sample = TrajectorySample(
        case_id=case.case_id,
        split="train" if label.entry.role == "train" else "validation",
        inputs=torch.from_numpy(encode_vector_load_case(case).input_tensor.copy()),
        target=torch.from_numpy(np.asarray(label.stored.design_density, dtype=np.float32)
                                .reshape(label.stored.tensor_shape).copy()),
        input_channels=13,
    )
    sample.validate()
    return sample


def validation_mse(model: ContextCNN, samples: tuple[TrajectorySample, ...]) -> float:
    """Every physical case has equal weight despite unequal voxel counts."""
    if not samples:
        raise ValueError("checkpoint selection requires validation cases")
    losses: list[float] = []
    model.eval()
    with torch.no_grad():
        for shape in SHAPES:
            indices = tuple(i for i, sample in enumerate(samples) if sample.shape == shape)
            for start in range(0, len(indices), BATCH_SIZE):
                inputs, targets = _tensors(samples, indices[start:start + BATCH_SIZE])
                per_case = torch.square(model(inputs) - targets).mean(dim=(1, 2, 3, 4))
                losses.extend(per_case.tolist())
    if len(losses) != len(samples) or any(not isfinite(loss) for loss in losses):
        raise ValueError("checkpoint selection produced invalid case losses")
    return sum(losses) / len(losses)


@dataclass(frozen=True, slots=True)
class B3Fit:
    history: tuple[dict[str, float | int], ...]
    selected_epoch: int
    selected_validation_loss: float
    seconds: float
    state: dict[str, Tensor]


def fit_b3_seed(
    train: tuple[TrajectorySample, ...], validation: tuple[TrajectorySample, ...], *,
    recipe: Recipe, seed: int, checkpoint: Callable[[bool], None],
) -> B3Fit:
    """Validate exact memberships before a from-scratch, bounded fit."""
    if recipe not in RECIPES or seed not in SEEDS:
        raise ValueError("recipe or seed differs from the frozen program")
    expected_train, expected_validation = fitting_entries(recipe)
    if (tuple(s.case_id for s in train) != expected_train
            or tuple(s.case_id for s in validation) != expected_validation):
        raise ValueError("fitting must use the exact requested train/validation membership")
    for split, samples in (("train", train), ("validation", validation)):
        for sample in samples:
            sample.validate()
            if sample.split != split or sample.input_channels != 13 or sample.weight is not None:
                raise ValueError("fitting sample differs from B3 representation")
    return _fit_samples(train, validation, seed=seed, weights=case_weights(recipe),
                        checkpoint=checkpoint)


def _fit_samples(
    train: tuple[TrajectorySample, ...], validation: tuple[TrajectorySample, ...], *,
    seed: int, weights: dict[str, float], checkpoint: Callable[[bool], None],
    element_weighted: bool = False,
) -> B3Fit:
    started = perf_counter()
    generator = torch.Generator(device="cpu").manual_seed(seed)
    deterministic = torch.are_deterministic_algorithms_enabled()
    warn_only = torch.is_deterministic_algorithms_warn_only_enabled()
    history: list[dict[str, float | int]] = []
    best, best_epoch, stale = float("inf"), 0, 0
    best_state: dict[str, Tensor] = {}
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(seed)
        torch.use_deterministic_algorithms(True)
        try:
            model = ContextCNN()
            if sum(p.numel() for p in model.parameters()) != CONTEXT_MODEL_PARAMETER_COUNT:
                raise ValueError("B3 architecture differs from the frozen context CNN")
            optimizer = AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4,
                              betas=(0.9, 0.999), eps=1e-8, amsgrad=False)
            for epoch in range(1, MAX_EPOCHS + 1):
                checkpoint(True)  # Persist the attempted epoch before its first update.
                model.train()
                objective_sum, weight_sum = 0.0, 0.0
                for batch in _batches(train, generator):
                    checkpoint(False)
                    inputs, targets = _tensors(train, batch)
                    batch_weights = torch.tensor([weights[train[i].case_id] for i in batch],
                                                 dtype=torch.float32)
                    optimizer.zero_grad(set_to_none=True)
                    prediction = model(inputs)
                    if element_weighted:
                        spatial = []
                        for i in batch:
                            weight = train[i].weight
                            if weight is None:
                                raise ValueError("element-weighted fit requires every label weight")
                            spatial.append(weight)
                        loss = weighted_terminal_loss(
                            prediction, targets, torch.stack(spatial), batch_weights)
                    else:
                        loss = case_weighted_loss(prediction, targets, batch_weights)
                    if not torch.isfinite(loss):
                        raise ValueError("nonfinite training objective")
                    torch.autograd.backward(loss)
                    optimizer.step()
                    denominator = float(batch_weights.sum().item())
                    objective_sum += loss.item() * denominator
                    weight_sum += denominator
                value = validation_mse(model, validation)
                history.append({"epoch": epoch, "training_loss": objective_sum / weight_sum,
                                "validation_loss": value})
                if value < best:
                    best, best_epoch, stale = value, epoch, 0
                    best_state = {name: tensor.detach().cpu().clone().contiguous()
                                  for name, tensor in sorted(model.state_dict().items())}
                else:
                    stale += 1
                checkpoint(False)
                if stale >= PATIENCE:
                    break
        finally:
            torch.use_deterministic_algorithms(deterministic, warn_only=warn_only)
    if not best_state:
        raise ValueError("fit produced no selected checkpoint")
    return B3Fit(tuple(history), best_epoch, best, perf_counter() - started, best_state)


def weighted_terminal_loss(
    prediction: Tensor, target: Tensor, spatial_weights: Tensor, case_weight: Tensor,
) -> Tensor:
    """B4.5: sensitivity-weighted voxel mean followed by the fixed case mean."""
    if (prediction.shape != target.shape or spatial_weights.shape != target.shape
            or prediction.ndim != 5 or case_weight.shape != (prediction.shape[0],)
            or not torch.isfinite(spatial_weights).all() or not torch.all(spatial_weights > 0)
            or not torch.isfinite(case_weight).all() or not torch.all(case_weight > 0)):
        raise ValueError("weighted terminal loss shapes or positive finite weights differ")
    per_case = (torch.square(prediction - target) * spatial_weights).mean(dim=(1, 2, 3, 4))
    return torch.sum(per_case * case_weight) / torch.sum(case_weight)
