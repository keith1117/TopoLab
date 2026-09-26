"""Opt-in B2.8 recentering of learned starts for y-directed loads."""

import numpy as np
from numpy.typing import NDArray

from topolab.experiment import ExperimentCase

START_VERSION = "topolab.b2_8.y_midpoint_start.v1"


def recenter_y_start(
    case: ExperimentCase, raw: NDArray[np.float32]
) -> NDArray[np.float32]:
    """Move a y-load prediction halfway toward the known uniform basin.

    A z-load prediction is copied unchanged. The caller must still project,
    refine, independently audit quality, and charge a full fallback on failure.
    """

    nx, ny, nz = case.problem.mesh.element_counts
    if raw.shape != (1, nz, ny, nx):
        raise ValueError("B2.8 prediction shape differs from the case mesh")
    if raw.dtype != np.float32 or not np.isfinite(raw).all():
        raise ValueError("B2.8 prediction must be finite CPU float32")
    if np.any(raw < 0) or np.any(raw > 1):
        raise ValueError("B2.8 prediction is outside density bounds")
    if len(case.problem.loads) != 1 or case.problem.loads[0].direction not in ("y", "z"):
        raise ValueError("B2.8 requires exactly one y or z point load")
    if case.problem.loads[0].direction == "z":
        return raw.copy()
    volume = np.float32(case.problem.optimization.volume_fraction)
    return np.asarray(np.float32(0.5) * raw + np.float32(0.5) * volume, dtype=np.float32)
