"""Opt-in fixed same-weight z-reflection mean; legacy predictors are unchanged."""

from collections.abc import Callable

import torch
from torch import Tensor, nn

from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.experiment import ExperimentCase
from topolab.problem import PointLoadDefinition, TopologyProblem

POLICY_VERSION = "topolab.b4_30.z-reflection-average.v1"
type PredictionRecorder = Callable[[ExperimentCase, Tensor, Tensor, Tensor], None]


def reflection_target(case: ExperimentCase) -> bool:
    """The existing generalist region, without an outcome-dependent trigger."""
    return (
        case.problem.mesh.element_counts == (24, 12, 6)
        and len(case.problem.loads) == 1
        and case.problem.loads[0].direction == "y"
        and case.problem.optimization.volume_fraction < 0.55
    )


def mirror_case(case: ExperimentCase) -> ExperimentCase:
    """Reflect a point-load location; non-target mirrors are metadata exclusions only."""
    if len(case.problem.loads) != 1 or not isinstance(case.problem.loads[0], PointLoadDefinition):
        raise ValueError("reflection metadata requires one point load")
    payload = case.problem.model_dump(mode="json")
    nx, ny, nz = case.problem.mesh.element_counts
    node = case.problem.loads[0].node
    stride = (nx + 1) * (ny + 1)
    if not 0 <= node < stride * (nz + 1):
        raise ValueError("reflection load node is outside the mesh")
    payload["loads"][0]["node"] = node % stride + stride * (nz - node // stride)
    return ExperimentCase.from_problem(TopologyProblem.model_validate(payload))


def checked_prediction(value: Tensor, case: ExperimentCase) -> Tensor:
    """Validate each raw tensor before an invalid pair could cancel in its mean."""
    nx, ny, nz = case.problem.mesh.element_counts
    if not isinstance(value, Tensor) or value.shape != (1, 1, nz, ny, nx):
        raise ValueError("reflection prediction shape differs from its case")
    if value.device.type != "cpu" or value.dtype != torch.float32:
        raise ValueError("reflection prediction must be CPU float32")
    if not torch.isfinite(value).all() or torch.any(value < 0) or torch.any(value > 1):
        raise ValueError("reflection prediction is outside finite [0,1]")
    return value


class ReflectionAverage(nn.Module):
    """Two calls to one checkpoint inside the legacy predictor's charged envelope."""

    def __init__(
        self,
        case: ExperimentCase,
        fixed_model: nn.Module,
        checkpoint: Callable[[], None],
        record: PredictionRecorder | None = None,
    ) -> None:
        super().__init__()
        if not reflection_target(case):
            raise ValueError("reflection inference is restricted to the frozen target region")
        self.case, self.fixed_model = case, fixed_model
        self.checkpoint, self.record = checkpoint, record

    def forward(self, inputs: Tensor) -> Tensor:
        nx, ny, nz = self.case.problem.mesh.element_counts
        if inputs.shape != (1, 13, nz, ny, nx) or inputs.dtype != torch.float32:
            raise ValueError("reflection input must be the original thirteen-channel tensor")
        self.checkpoint()
        first = checked_prediction(self.fixed_model(inputs), self.case)
        self.checkpoint()
        mirrored = mirror_case(self.case)
        encoded = torch.from_numpy(encode_vector_load_case(mirrored).input_tensor.copy())
        second = checked_prediction(self.fixed_model(encoded.unsqueeze(0)), mirrored)
        average = torch.mul(first + torch.flip(second, dims=(2,)), 0.5)
        checked_prediction(average, self.case)
        if self.record is not None:
            self.record(mirrored, first, second, average)
        self.checkpoint()
        return average
