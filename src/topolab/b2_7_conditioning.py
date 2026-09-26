"""Opt-in, globally visible point-load encoding for B2.7 development."""

import numpy as np

from topolab.experiment import EncodedCase, ExperimentCase, encode_case
from topolab.problem import PointLoadDefinition

ENCODING_VERSION = "topolab.b2_7.global_load_distance.v1"
_AXIS = {"x": 0, "y": 1, "z": 2, 0: 0, 1: 1, 2: 2}


def encode_global_load_case(case: ExperimentCase) -> EncodedCase:
    """Replace only the three sparse load channels with signed distance fields.

    The single point load's direction is visible at every element. Its node
    location is represented by a smooth, normalized distance attenuation.
    Historical ``encode_case`` and its ten-channel contract are unchanged.
    """

    if len(case.problem.loads) != 1 or not isinstance(
        case.problem.loads[0], PointLoadDefinition
    ):
        raise ValueError("B2.7 encoding requires exactly one point load")
    load = case.problem.loads[0]
    nx, ny, nz = case.problem.mesh.element_counts
    node_count = (nx + 1) * (ny + 1) * (nz + 1)
    if load.node >= node_count:
        raise ValueError("B2.7 point-load node is outside the mesh")
    ix = load.node % (nx + 1)
    iy = load.node // (nx + 1) % (ny + 1)
    iz = load.node // ((nx + 1) * (ny + 1))
    node_position = (ix / nx, iy / ny, iz / nz)

    original = encode_case(case)
    encoded = original.input_tensor.copy()
    distance = np.sqrt(
        sum(
            np.square(encoded[6 + axis].astype(np.float64) - position)
            for axis, position in enumerate(node_position)
        )
        / 3.0
    )
    field = np.asarray(1.0 - distance, dtype=np.float32)
    encoded[3:6] = 0.0
    encoded[3 + _AXIS[load.direction]] = np.sign(load.magnitude) * field
    if encoded.shape != (10, nz, ny, nx) or not np.isfinite(encoded).all():
        raise ValueError("B2.7 encoded input is not finite and shape preserving")
    return EncodedCase(input_tensor=encoded, load_scale=original.load_scale)
