"""Opt-in physical-state feature for the B2.19 development model."""

import numpy as np
import torch
from torch import Tensor, nn

from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.experiment import EncodedCase, ExperimentCase
from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.mesh import generate_structured_hex8
from topolab.model import FixedFaceSupport, PointLoad
from topolab.problem import PointLoadDefinition
from topolab.simp import evaluate_compliance

ENCODING_VERSION = "topolab.b2_19.uniform_sensitivity.v1"
MODEL_VERSION = "topolab.b2_19.physics_context_cnn.v1"
INPUT_CHANNELS = 14
MODEL_PARAMETER_COUNT = 26_865


def encode_physics_case(case: ExperimentCase) -> EncodedCase:
    """Append normalized uniform-state strain energy from one paid FEM solve."""

    if len(case.problem.loads) != 1:
        raise ValueError("B2.19 requires exactly one point load")
    load = case.problem.loads[0]
    if not isinstance(load, PointLoadDefinition):
        raise ValueError("B2.19 requires exactly one point load")
    original = encode_vector_load_case(case)
    problem = case.problem
    nx, ny, nz = problem.mesh.element_counts
    mesh = generate_structured_hex8(nx, ny, nz, lengths=problem.mesh.lengths)
    supports = [
        FixedFaceSupport(item.axis, item.side, item.directions)
        for item in problem.supports
    ]
    loads = build_load_vector(mesh, [PointLoad(load.node, load.direction, load.magnitude)])
    constrained = build_constrained_dofs(mesh, supports)
    density = np.full(nx * ny * nz, problem.optimization.volume_fraction, dtype=np.float64)
    state = evaluate_compliance(
        mesh, density, loads, constrained,
        solid_modulus=problem.material.solid_modulus,
        minimum_modulus=problem.material.minimum_modulus,
        poisson_ratio=problem.material.poisson_ratio,
        penalty=problem.optimization.penalty,
    )
    energy = -state.sensitivity
    if not np.isfinite(energy).all() or np.any(energy < 0):
        raise ValueError("B2.19 uniform sensitivity must be finite and nonnegative")
    mean = float(np.mean(energy))
    maximum = float(np.max(energy))
    if not np.isfinite(mean) or mean <= 0 or maximum <= 0:
        raise ValueError("B2.19 uniform sensitivity has no positive energy")
    feature = np.log1p(energy / mean) / np.log1p(maximum / mean)
    encoded = np.empty((INPUT_CHANNELS, nz, ny, nx), dtype=np.float32)
    encoded[:13] = original.input_tensor
    encoded[13] = feature.reshape((nz, ny, nx)).astype(np.float32)
    if not np.isfinite(encoded).all() or np.any(encoded[13] < 0) or np.any(encoded[13] > 1):
        raise ValueError("B2.19 physical feature leaves normalized bounds")
    return EncodedCase(encoded, original.load_scale)


class PhysicsContextCNN(nn.Module):
    """The unchanged B2.12 receptive field with one physical input channel."""

    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Conv3d(INPUT_CHANNELS, 16, 3, padding=1),
            nn.ReLU(),
            nn.Conv3d(16, 16, 3, padding=(1, 1, 2), dilation=(1, 1, 2)),
            nn.ReLU(),
            nn.Conv3d(16, 16, 3, padding=(1, 2, 4), dilation=(1, 2, 4)),
            nn.ReLU(),
            nn.Conv3d(16, 16, 3, padding=(1, 2, 8), dilation=(1, 2, 8)),
            nn.ReLU(),
            nn.Conv3d(16, 1, 1),
            nn.Sigmoid(),
        )

    def forward(self, inputs: Tensor) -> Tensor:
        if inputs.ndim != 5 or inputs.shape[1] != INPUT_CHANNELS:
            raise ValueError("inputs must have shape (batch, 14, z, y, x)")
        if inputs.dtype != torch.float32 or inputs.device.type != "cpu":
            raise TypeError("inputs must be CPU float32")
        outputs = self.network(inputs)
        if not isinstance(outputs, Tensor):  # pragma: no cover - Sequential is fixed
            raise TypeError("model output must be a tensor")
        return outputs
