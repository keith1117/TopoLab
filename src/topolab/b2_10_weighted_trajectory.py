"""Offline sensitivity weights for the fixed B2.6 trajectory targets."""

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from topolab.b2_4_labels import _analysis_and_weights
from topolab.b2_6_trajectory import TrajectoryTarget
from topolab.experiment import ExperimentCase
from topolab.mesh import generate_structured_hex8
from topolab.simp import apply_density_filter, build_density_filter

WEIGHT_VERSION = "topolab.b2_10.trajectory_sensitivity.v1"


@dataclass(frozen=True, slots=True)
class SensitivityWeightedTarget:
    weight: NDArray[np.float32]
    compliance: float


def sensitivity_weighted_target(
    case: ExperimentCase, target: TrajectoryTarget
) -> SensitivityWeightedTarget:
    """Re-solve the stored update-30 design and weight its high-impact elements."""

    nx, ny, nz = case.problem.mesh.element_counts
    if target.density.shape != (1, nz, ny, nx):
        raise ValueError("B2.10 target shape differs from the physical case")
    design = target.density.reshape(-1)
    mesh = generate_structured_hex8(nx, ny, nz, lengths=case.problem.mesh.lengths)
    density_filter = build_density_filter(mesh, case.problem.optimization.filter_radius)
    physical = np.asarray(
        apply_density_filter(density_filter, design.astype(np.float64)),
        dtype=np.float32,
    )
    compliance, weights = _analysis_and_weights(case, design, physical)
    if (
        not np.isfinite(weights).all()
        or np.any(weights <= 0.0)
        or not np.isclose(np.mean(weights, dtype=np.float64), 1.0, rtol=0.0, atol=1e-6)
    ):
        raise ValueError("B2.10 sensitivity weights violate the fixed bounds")
    return SensitivityWeightedTarget(weight=weights.reshape(target.density.shape),
                                     compliance=compliance)
