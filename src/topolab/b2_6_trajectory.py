"""B2.6 development target: predict a reachable uniform SIMP trajectory state."""

from dataclasses import dataclass
from time import perf_counter
from typing import Literal

import numpy as np
import torch
from numpy.typing import NDArray
from torch import Tensor
from torch.optim import AdamW

from topolab.experiment import ExperimentCase, encode_case
from topolab.mesh import generate_structured_hex8
from topolab.problem import IterationResult, solve_problem
from topolab.simp import SimpIteration, apply_density_filter, build_density_filter
from topolab.training import (
    M1_ADAM_BETAS,
    M1_ADAM_EPSILON,
    M1_MODEL_PARAMETER_COUNT,
    WarmStartCNN,
)

TARGET_UPDATE = 30
SEEDS = (17, 29, 43)
MAX_EPOCHS = 200
PATIENCE = 25
BATCH_SIZE = 8
SHAPES = ((3, 6, 12), (6, 12, 24))


class _StopAtTarget(Exception):
    """Stop an otherwise unchanged SIMP solve after its re-solved target state."""


@dataclass(frozen=True, slots=True)
class TrajectoryTarget:
    density: NDArray[np.float32]
    iterations: int
    converged_before_target: bool
    compliance: float
    physical_volume_error: float


def capture_uniform_target(
    case: ExperimentCase, *, update: int = TARGET_UPDATE
) -> TrajectoryTarget:
    """Capture the post-update design at ``update`` or an earlier converged stop."""

    if update < 1 or update > case.problem.optimization.max_iterations:
        raise ValueError("trajectory update must be inside the case budget")
    selected: SimpIteration | None = None
    state: SimpIteration | IterationResult

    def capture(state: SimpIteration) -> None:
        nonlocal selected
        if state.iteration == update:
            selected = state
            raise _StopAtTarget

    try:
        result = solve_problem(
            case.problem, iteration_callback=capture, termination_policy="physical_plateau"
        )
    except _StopAtTarget:
        if selected is None:
            raise RuntimeError("trajectory stop lacked a captured state") from None
        state = selected
        converged_early = False
    else:
        if not result.converged or not result.history or len(result.history) >= update:
            raise ValueError("uniform trajectory did not reach a valid early stop")
        state = result.history[-1]
        converged_early = True

    counts = case.problem.mesh.element_counts
    shape = (counts[2], counts[1], counts[0])
    density = np.asarray(state.design_density, dtype=np.float32).reshape((1, *shape)).copy()
    if (
        not np.isfinite(density).all()
        or np.any(density < case.problem.optimization.minimum_density - 1e-7)
        or np.any(density > 1.0)
    ):
        raise ValueError("captured trajectory density is outside the numerical contract")
    mesh = generate_structured_hex8(*counts, lengths=case.problem.mesh.lengths)
    density_filter = build_density_filter(mesh, case.problem.optimization.filter_radius)
    physical = apply_density_filter(density_filter, density.astype(np.float64).reshape(-1))
    volume_error = abs(float(np.mean(physical)) - case.problem.optimization.volume_fraction)
    if volume_error > 0.005 or not np.isfinite(state.compliance) or state.compliance <= 0:
        raise ValueError("captured trajectory state failed the volume/compliance audit")
    return TrajectoryTarget(
        density=density,
        iterations=state.iteration,
        converged_before_target=converged_early,
        compliance=state.compliance,
        physical_volume_error=volume_error,
    )


@dataclass(frozen=True, slots=True)
class TrajectorySample:
    case_id: str
    split: Literal["train", "validation"]
    inputs: Tensor
    target: Tensor

    @classmethod
    def from_target(
        cls, case: ExperimentCase, split: Literal["train", "validation"], target: TrajectoryTarget
    ) -> "TrajectorySample":
        sample = cls(
            case_id=case.case_id,
            split=split,
            inputs=torch.from_numpy(encode_case(case).input_tensor.copy()),
            target=torch.from_numpy(target.density.copy()),
        )
        sample.validate()
        return sample

    def validate(self) -> None:
        shape = tuple(self.inputs.shape[1:])
        if (
            shape not in SHAPES
            or tuple(self.inputs.shape) != (10, *shape)
            or tuple(self.target.shape) != (1, *shape)
        ):
            raise ValueError("trajectory sample shape differs from the frozen meshes")
        for tensor in (self.inputs, self.target):
            if tensor.dtype != torch.float32 or tensor.device.type != "cpu":
                raise ValueError("trajectory sample must be CPU float32")
            if not torch.isfinite(tensor).all():
                raise ValueError("trajectory sample contains nonfinite values")

    @property
    def shape(self) -> tuple[int, int, int]:
        return tuple(self.inputs.shape[1:])  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class TrajectoryFit:
    seed: int
    history: tuple[dict[str, float | int], ...]
    selected_epoch: int
    selected_validation_loss: float
    seconds: float
    state: dict[str, Tensor]


def _batches(
    samples: tuple[TrajectorySample, ...], generator: torch.Generator
) -> tuple[tuple[int, ...], ...]:
    batches: list[tuple[int, ...]] = []
    for shape in SHAPES:
        indices = [index for index, sample in enumerate(samples) if sample.shape == shape]
        if not indices:
            raise ValueError("trajectory fitting requires both mesh scales")
        shuffled = torch.randperm(len(indices), generator=generator).tolist()
        ordered = [indices[index] for index in shuffled]
        batches.extend(
            tuple(ordered[start : start + BATCH_SIZE])
            for start in range(0, len(ordered), BATCH_SIZE)
        )
    order = torch.randperm(len(batches), generator=generator).tolist()
    return tuple(batches[index] for index in order)


def _tensors(
    samples: tuple[TrajectorySample, ...], indices: tuple[int, ...]
) -> tuple[Tensor, Tensor]:
    return (
        torch.stack([samples[index].inputs for index in indices]),
        torch.stack([samples[index].target for index in indices]),
    )


def fit_trajectory_seed(
    train: tuple[TrajectorySample, ...], validation: tuple[TrajectorySample, ...], *, seed: int
) -> TrajectoryFit:
    """Fit one fixed-seed CNN to the 30-update design target."""

    if seed not in SEEDS or len(train) != 468 or len(validation) != 12:
        raise ValueError("trajectory fit seed or population differs from the plan")
    if (
        any(sample.split != "train" for sample in train)
        or any(sample.split != "validation" for sample in validation)
        or len({sample.case_id for sample in (*train, *validation)}) != 480
    ):
        raise ValueError("trajectory fitting partitions overlap or differ")
    for partition in (train, validation):
        if [sample.case_id for sample in partition] != sorted(
            sample.case_id for sample in partition
        ):
            raise ValueError("trajectory samples must have sorted case IDs")
        for sample in partition:
            sample.validate()

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
                raise ValueError("trajectory model differs from the fixed CNN")
            optimizer = AdamW(
                model.parameters(),
                lr=0.001,
                weight_decay=0.0001,
                betas=M1_ADAM_BETAS,
                eps=M1_ADAM_EPSILON,
                amsgrad=False,
            )
            history: list[dict[str, float | int]] = []
            best = float("inf")
            best_epoch = 0
            best_state: dict[str, Tensor] = {}
            stale = 0
            val_by_shape = {
                shape: tuple(i for i, sample in enumerate(validation) if sample.shape == shape)
                for shape in SHAPES
            }
            for epoch in range(1, MAX_EPOCHS + 1):
                model.train()
                train_sum = 0.0
                train_elements = 0
                batches = _batches(train, generator)
                if len(batches) != 59:
                    raise ValueError("trajectory training must have 59 batches per epoch")
                for batch in batches:
                    inputs, targets = _tensors(train, batch)
                    optimizer.zero_grad(set_to_none=True)
                    loss = torch.mean(torch.square(model(inputs) - targets))
                    torch.autograd.backward(loss)
                    optimizer.step()
                    train_sum += loss.item() * targets.numel()
                    train_elements += targets.numel()
                model.eval()
                val_sum = 0.0
                val_elements = 0
                with torch.no_grad():
                    for shape in SHAPES:
                        indices = val_by_shape[shape]
                        for start in range(0, len(indices), BATCH_SIZE):
                            inputs, targets = _tensors(
                                validation, indices[start : start + BATCH_SIZE]
                            )
                            loss = torch.mean(torch.square(model(inputs) - targets))
                            val_sum += loss.item() * targets.numel()
                            val_elements += targets.numel()
                if train_elements == 0 or val_elements == 0:
                    raise ValueError("trajectory training has an empty objective denominator")
                train_loss = train_sum / train_elements
                val_loss = val_sum / val_elements
                history.append(
                    {"epoch": epoch, "training_loss": train_loss, "validation_loss": val_loss}
                )
                if val_loss < best:
                    best = val_loss
                    best_epoch = epoch
                    best_state = {
                        name: tensor.detach().cpu().clone().contiguous()
                        for name, tensor in sorted(model.state_dict().items())
                    }
                    stale = 0
                else:
                    stale += 1
                    if stale >= PATIENCE:
                        break
        finally:
            torch.use_deterministic_algorithms(previous_deterministic, warn_only=previous_warn_only)
    if best_epoch == 0:
        raise ValueError("trajectory fit produced no selection")
    return TrajectoryFit(
        seed, tuple(history), best_epoch, best, perf_counter() - started, best_state
    )
