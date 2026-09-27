"""B2.12 opt-in spatial-context model for the unchanged vector-load input."""

import torch
from torch import Tensor, nn

from topolab.b2_9_vector_load import VECTOR_INPUT_CHANNELS

MODEL_VERSION = "topolab.b2_12.context_cnn.v1"
CONTEXT_MODEL_PARAMETER_COUNT = 26_433


class ContextCNN(nn.Module):
    """Shape-preserving context expansion with fixed axis-aware dilations."""

    def __init__(self) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Conv3d(VECTOR_INPUT_CHANNELS, 16, 3, padding=1),
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
        if inputs.ndim != 5 or inputs.shape[1] != VECTOR_INPUT_CHANNELS:
            raise ValueError("inputs must have shape (batch, 13, z, y, x)")
        if inputs.dtype != torch.float32 or inputs.device.type != "cpu":
            raise TypeError("inputs must be CPU float32")
        outputs = self.network(inputs)
        if not isinstance(outputs, Tensor):  # pragma: no cover - Sequential is fixed
            raise TypeError("model output must be a tensor")
        return outputs
