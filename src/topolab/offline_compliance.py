"""Opt-in, first-order offline compliance loss on a volume-constrained start."""

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch.autograd.function import once_differentiable

from topolab.baselines import _case_system
from topolab.experiment import ExperimentCase
from topolab.mesh import Hex8Mesh
from topolab.simp import (
    DensityFilter,
    apply_density_filter,
    backpropagate_density_gradient,
    build_density_filter,
    evaluate_compliance,
)

VERSION = "topolab.offline-compliance-adjoint.v1"
VOLUME_TOLERANCE = 1e-12
KINK_TOLERANCE = 1e-10


@dataclass(frozen=True, slots=True)
class Projection:
    design: NDArray[np.float64]
    physical: NDArray[np.float64]
    weights: NDArray[np.float64]
    free: NDArray[np.bool_]
    offset: float


def project(
    filt: DensityFilter, raw: NDArray[np.floating[Any]], volume: float, minimum: float
) -> Projection:
    """Solve the mathematical additive projection, rejecting clipping kinks."""
    z = np.asarray(raw, dtype=np.float64)
    if (
        z.shape != filt.row_sums.shape
        or not np.all(np.isfinite(z))
        or np.any((z < 0) | (z > 1))
        or not 0 < minimum < volume < 1
    ):
        raise ValueError("finite raw vector and interior physical volume required")
    weights = np.asarray(filt.matrix.T @ (1 / filt.row_sums)) / z.size
    low, high = -1.0, 1.0
    for _ in range(100):
        offset = (low + high) / 2
        design = np.clip(z + offset, minimum, 1.0)
        error = float(weights @ design) - volume
        if abs(error) <= VOLUME_TOLERANCE:
            break
        if error < 0:
            low = offset
        else:
            high = offset
    else:
        raise ValueError("physical-volume root did not converge")
    shifted = z + offset
    if np.any(np.minimum(np.abs(shifted - minimum), np.abs(shifted - 1)) <= KINK_TOLERANCE):
        raise ValueError("projection is at a clipping kink")
    free = (shifted > minimum) & (shifted < 1)
    if float(weights @ free) <= 0:
        raise ValueError("projection has no free volume derivative")
    physical = apply_density_filter(filt, design)
    if abs(float(physical.mean()) - volume) > VOLUME_TOLERANCE:
        raise ValueError("filtered physical volume differs")
    return Projection(design, physical, weights, free, offset)


def pullback(state: Projection, cotangent: NDArray[np.float64]) -> NDArray[np.float64]:
    """Apply the transpose of the stable-active-set implicit Jacobian."""
    g = np.asarray(cotangent, dtype=np.float64)
    if g.shape != state.design.shape or not np.all(np.isfinite(g)):
        raise ValueError("cotangent must be a finite matching vector")
    active_weights = state.weights * state.free
    return state.free * g - active_weights * float(np.sum(state.free * g)) / float(
        np.sum(active_weights)
    )


@dataclass(frozen=True, slots=True)
class ObjectiveResult:
    value: float
    compliance: float
    gradient: NDArray[np.float64]
    projection: Projection


@dataclass(slots=True)
class OfflineCompliance:
    """Reuse immutable geometry/filter setup; charge each FEM solve and pullback."""

    case: ExperimentCase
    normalizer: float
    mesh: Hex8Mesh = field(init=False)
    loads: NDArray[np.float64] = field(init=False)
    constrained: NDArray[np.int64] = field(init=False)
    filt: DensityFilter = field(init=False)

    def __post_init__(self) -> None:
        if not np.isfinite(self.normalizer) or self.normalizer <= 0:
            raise ValueError("training compliance normalizer must be positive finite")
        self.mesh, self.loads, self.constrained = _case_system(self.case)
        self.filt = build_density_filter(self.mesh, self.case.problem.optimization.filter_radius)

    def evaluate(self, raw: NDArray[np.floating[Any]]) -> ObjectiveResult:
        problem = self.case.problem
        state = project(
            self.filt,
            raw,
            problem.optimization.volume_fraction,
            problem.optimization.minimum_density,
        )
        result = evaluate_compliance(
            self.mesh,
            state.physical,
            self.loads,
            self.constrained,
            solid_modulus=problem.material.solid_modulus,
            minimum_modulus=problem.material.minimum_modulus,
            poisson_ratio=problem.material.poisson_ratio,
            penalty=problem.optimization.penalty,
        )
        design_gradient = backpropagate_density_gradient(self.filt, result.sensitivity)
        gradient = pullback(state, design_gradient) / self.normalizer
        return ObjectiveResult(
            result.compliance / self.normalizer, result.compliance, gradient, state
        )


class _Compliance(torch.autograd.Function):
    @staticmethod
    def forward(ctx: Any, raw: torch.Tensor, kernel: OfflineCompliance) -> torch.Tensor:
        result = kernel.evaluate(raw.detach().numpy())
        ctx.save_for_backward(torch.as_tensor(result.gradient, dtype=raw.dtype))
        return raw.new_tensor(result.value)

    @staticmethod
    @once_differentiable
    def backward(ctx: Any, cotangent: torch.Tensor) -> tuple[torch.Tensor, None]:
        (gradient,) = ctx.saved_tensors
        return cotangent * gradient, None


def torch_loss(raw: torch.Tensor, kernel: OfflineCompliance) -> torch.Tensor:
    """CPU vector bridge, with explicit first-order float64 FEM arithmetic."""
    if raw.device.type != "cpu" or raw.dtype not in (torch.float32, torch.float64):
        raise ValueError("offline compliance requires float32/float64 CPU input")
    return _Compliance.apply(raw, kernel)  # type: ignore[no-any-return]
