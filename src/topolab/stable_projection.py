"""Opt-in affine root refinement; legacy projection and tangent stay unchanged."""

import math
from itertools import chain
from typing import Any

import numpy as np
from numpy.typing import NDArray

from topolab.local_compliance import StoredNormalizerTangent
from topolab.offline_compliance import (
    KINK_TOLERANCE,
    VOLUME_TOLERANCE,
    ObjectiveResult,
    Projection,
    project,
    pullback,
)
from topolab.simp import DensityFilter, apply_density_filter

VERSION = "topolab.stable-projection-tangent.v3"


def project_stable(
    filt: DensityFilter, raw: NDArray[np.floating[Any]], volume: float, minimum: float
) -> Projection:
    """Refine exactly once on the original root's stable clipping partition."""
    initial = project(filt, raw, volume, minimum)
    z = np.asarray(raw, dtype=np.float64)
    weights, free = initial.weights, initial.free
    shifted = z + initial.offset
    lower, upper = shifted < minimum, shifted > 1
    denominator = math.fsum(float(w) for w in weights[free])
    if denominator <= 0:
        raise ValueError("stable projection has no free volume derivative")
    numerator = math.fsum(
        chain(
            (volume,),
            (-minimum * float(w) for w in weights[lower]),
            (-float(w) for w in weights[upper]),
            (-float(w) * float(x) for w, x in zip(weights[free], z[free], strict=True)),
        )
    )
    offset = numerator / denominator
    shifted = z + offset
    refined_free = (shifted > minimum) & (shifted < 1)
    if (
        not math.isfinite(offset)
        or not np.array_equal(refined_free, free)
        or not np.array_equal(shifted < minimum, lower)
        or not np.array_equal(shifted > 1, upper)
    ):
        raise ValueError("affine root changes the original clipping partition")
    if np.any(np.minimum(abs(shifted - minimum), abs(shifted - 1)) <= KINK_TOLERANCE):
        raise ValueError("stable projection is at a clipping kink")
    design = np.clip(shifted, minimum, 1)
    physical = apply_density_filter(filt, design)
    if (
        abs(float(weights @ design) - volume) > VOLUME_TOLERANCE
        or abs(float(physical.mean()) - volume) > VOLUME_TOLERANCE
    ):
        raise ValueError("refined physical volume differs")
    return Projection(design, physical, weights, refined_free, offset)


class StableStoredNormalizerTangent(StoredNormalizerTangent):
    """Stored-denominator tangent using the separately versioned root program."""

    __slots__ = ()

    def evaluate(self, raw: NDArray[np.floating[Any]]) -> ObjectiveResult:
        settings = self.case.problem.optimization
        state = project_stable(self.filt, raw, settings.volume_fraction, settings.minimum_density)
        value = self.anchor_compliance / self.normalizer + float(
            self.design_gradient @ (state.design - self.anchor)
        )
        return ObjectiveResult(
            value, value * self.normalizer, pullback(state, self.design_gradient), state
        )
