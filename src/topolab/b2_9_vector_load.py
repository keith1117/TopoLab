"""Opt-in vector-load conditioning and shape-preserving B2.9 CNN."""

import numpy as np
import torch
from torch import Tensor, nn

from topolab.experiment import EncodedCase, ExperimentCase, encode_case
from topolab.problem import PointLoadDefinition

ENCODING_VERSION = "topolab.b2_9.vector_load.v1"
MODEL_VERSION = "topolab.b2_9.vector_cnn.v1"
VECTOR_INPUT_CHANNELS = 13
VECTOR_MODEL_PARAMETER_COUNT = 12_577
_AXIS = {"x": 0, "y": 1, "z": 2, 0: 0, 1: 1, 2: 2}


def encode_vector_load_case(case: ExperimentCase) -> EncodedCase:
    """Separate signed load direction from load-relative position at every voxel."""

    if len(case.problem.loads) != 1 or not isinstance(
        case.problem.loads[0], PointLoadDefinition
    ):
        raise ValueError("B2.9 requires exactly one point load")
    load = case.problem.loads[0]
    nx, ny, nz = case.problem.mesh.element_counts
    node_count = (nx + 1) * (ny + 1) * (nz + 1)
    if load.node < 0 or load.node >= node_count:
        raise ValueError("B2.9 point-load node is outside the mesh")
    ix = load.node % (nx + 1)
    iy = load.node // (nx + 1) % (ny + 1)
    iz = load.node // ((nx + 1) * (ny + 1))
    position = (ix / nx, iy / ny, iz / nz)

    original = encode_case(case)
    encoded = np.zeros((VECTOR_INPUT_CHANNELS, nz, ny, nx), dtype=np.float32)
    encoded[:10] = original.input_tensor
    encoded[3:6] = 0.0
    encoded[3 + _AXIS[load.direction]] = np.sign(load.magnitude)
    for axis, coordinate in enumerate(position):
        encoded[10 + axis] = encoded[6 + axis] - np.float32(coordinate)
    if not np.isfinite(encoded).all() or np.any(np.abs(encoded[10:13]) > 1.0):
        raise ValueError("B2.9 encoded vector is outside its finite normalized bounds")
    return EncodedCase(input_tensor=encoded, load_scale=original.load_scale)


class VectorLoadCNN(nn.Module):
    """The M1 local CNN depth with 13 explicit direction/position channels."""

    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Conv3d(VECTOR_INPUT_CHANNELS, 16, 3, padding=1),
            nn.ReLU(),
            nn.Conv3d(16, 16, 3, padding=1),
            nn.ReLU(),
            nn.Conv3d(16, 1, 1),
            nn.Sigmoid(),
        )

    def forward(self, inputs: Tensor) -> Tensor:
        if inputs.ndim != 5 or inputs.shape[1] != VECTOR_INPUT_CHANNELS:
            raise ValueError("inputs must have shape (batch, 13, z, y, x)")
        if inputs.dtype != torch.float32:
            raise TypeError("inputs must have dtype float32")
        outputs = self.network(inputs)
        if not isinstance(outputs, Tensor):  # pragma: no cover - Sequential is fixed
            raise TypeError("model output must be a tensor")
        return outputs
