"""Training-only signed compliance tangent; no prediction-state FEM solve."""

from dataclasses import InitVar, dataclass, field
from typing import Any

import numpy as np
import torch
from numpy.typing import NDArray
from torch.autograd.function import once_differentiable

from topolab.baselines import _case_system
from topolab.experiment import ExperimentCase
from topolab.offline_compliance import ObjectiveResult, project, pullback
from topolab.simp import (
    ComplianceResult,
    DensityFilter,
    apply_density_filter,
    backpropagate_density_gradient,
    build_density_filter,
    evaluate_compliance,
)

VERSION = "topolab.local-compliance-tangent.v1"
STORED_NORMALIZER_VERSION = "topolab.stored-normalizer-tangent.v2"


@dataclass(slots=True)
class LocalCompliance:
    """Pay one anchor solve; retain signed, un-clipped normalized derivatives."""

    case: ExperimentCase
    anchor: NDArray[np.float64]
    normalizer: float
    filt: DensityFilter = field(init=False)
    design_gradient: NDArray[np.float64] = field(init=False)
    anchor_compliance: float = field(init=False)

    def __post_init__(self) -> None:
        mesh, loads, constrained = _case_system(self.case)
        p = self.case.problem
        self.filt = build_density_filter(mesh, p.optimization.filter_radius)
        self.anchor = np.array(self.anchor, dtype=np.float64, copy=True)
        if (
            self.anchor.shape != self.filt.row_sums.shape
            or not np.all(np.isfinite(self.anchor))
            or np.any((self.anchor < p.optimization.minimum_density) | (self.anchor > 1))
            or not np.isfinite(self.normalizer)
            or self.normalizer <= 0
        ):
            raise ValueError("finite bounded anchor and positive normalizer required")
        result = evaluate_compliance(
            mesh,
            apply_density_filter(self.filt, self.anchor),
            loads,
            constrained,
            solid_modulus=p.material.solid_modulus,
            minimum_modulus=p.material.minimum_modulus,
            poisson_ratio=p.material.poisson_ratio,
            penalty=p.optimization.penalty,
        )
        if not np.isclose(result.compliance, self.normalizer, rtol=1e-9, atol=0):
            raise ValueError("anchor compliance differs from audited normalizer")
        self.anchor_compliance = result.compliance
        self.design_gradient = (
            backpropagate_density_gradient(self.filt, result.sensitivity) / self.normalizer
        )
        # Only immutable arrays persist; mesh, displacements and factors are released.
        for array in self.retained_arrays():
            array.setflags(write=False)

    def retained_arrays(self) -> tuple[NDArray[Any], ...]:
        return (
            self.anchor,
            self.design_gradient,
            self.filt.row_sums,
            self.filt.matrix.data,
            self.filt.matrix.indices,
            self.filt.matrix.indptr,
        )

    def evaluate(self, raw: NDArray[np.floating[Any]]) -> ObjectiveResult:
        settings = self.case.problem.optimization
        state = project(self.filt, raw, settings.volume_fraction, settings.minimum_density)
        value = 1.0 + float(self.design_gradient @ (state.design - self.anchor))
        return ObjectiveResult(
            value, value * self.normalizer, pullback(state, self.design_gradient), state
        )


@dataclass(slots=True)
class StoredNormalizerTangent:
    """Continuous tangent with a stored constant denominator and paid analysis.

    The caller must audit the supplied analysis at F(float64(anchor)) separately
    from the serialized physical state. No solve or quantization derivative is
    hidden in construction. Only immutable tangent/filter arrays are retained.
    """

    case: ExperimentCase
    anchor: NDArray[np.float64]
    normalizer: float
    analysis: InitVar[ComplianceResult]
    filt: DensityFilter = field(init=False)
    design_gradient: NDArray[np.float64] = field(init=False)
    anchor_compliance: float = field(init=False)

    def __post_init__(self, analysis: ComplianceResult) -> None:
        mesh, _, _ = _case_system(self.case)
        settings = self.case.problem.optimization
        self.filt = build_density_filter(mesh, settings.filter_radius)
        self.anchor = np.array(self.anchor, dtype=np.float64, copy=True)
        if (
            self.anchor.shape != self.filt.row_sums.shape
            or not np.all(np.isfinite(self.anchor))
            or np.any((self.anchor < settings.minimum_density) | (self.anchor > 1))
            or not np.isfinite(self.normalizer)
            or self.normalizer <= 0
            or not np.isfinite(analysis.compliance)
            or analysis.compliance <= 0
            or analysis.sensitivity.shape != self.anchor.shape
            or not np.all(np.isfinite(analysis.sensitivity))
        ):
            raise ValueError("finite bounded anchor, positive normalizer and analysis required")
        self.anchor_compliance = analysis.compliance
        self.design_gradient = (
            backpropagate_density_gradient(self.filt, analysis.sensitivity) / self.normalizer
        )
        for array in self.retained_arrays():
            array.setflags(write=False)

    def retained_arrays(self) -> tuple[NDArray[Any], ...]:
        return (
            self.anchor,
            self.design_gradient,
            self.filt.row_sums,
            self.filt.matrix.data,
            self.filt.matrix.indices,
            self.filt.matrix.indptr,
        )

    def evaluate(self, raw: NDArray[np.floating[Any]]) -> ObjectiveResult:
        settings = self.case.problem.optimization
        state = project(self.filt, raw, settings.volume_fraction, settings.minimum_density)
        value = self.anchor_compliance / self.normalizer + float(
            self.design_gradient @ (state.design - self.anchor)
        )
        return ObjectiveResult(
            value, value * self.normalizer, pullback(state, self.design_gradient), state
        )


class _LocalCompliance(torch.autograd.Function):
    @staticmethod
    def forward(
        ctx: Any, raw: torch.Tensor, kernel: LocalCompliance | StoredNormalizerTangent
    ) -> torch.Tensor:
        result = kernel.evaluate(raw.detach().numpy())
        ctx.save_for_backward(torch.as_tensor(result.gradient, dtype=raw.dtype))
        return raw.new_tensor(result.value)

    @staticmethod
    @once_differentiable
    def backward(ctx: Any, cotangent: torch.Tensor) -> tuple[torch.Tensor, None]:
        (gradient,) = ctx.saved_tensors
        return cotangent * gradient, None


def torch_local_loss(
    raw: torch.Tensor, kernel: LocalCompliance | StoredNormalizerTangent
) -> torch.Tensor:
    """First-order CPU bridge; affine estimates are deliberately not clipped."""
    if raw.device.type != "cpu" or raw.dtype not in (torch.float32, torch.float64):
        raise ValueError("local compliance requires float32/float64 CPU input")
    return _LocalCompliance.apply(raw, kernel)  # type: ignore[no-any-return]
