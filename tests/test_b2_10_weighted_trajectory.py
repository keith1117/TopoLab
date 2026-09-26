"""B2.10 sensitivity-weighted trajectory objective and frozen exposure."""

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_6_trajectory import _small_case  # noqa: E402
from b2_10_weighted_trajectory import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    METHODS,
    VOLUMES,
    cohorts,
    plan_payload,
)

from topolab.b2_6_trajectory import (  # noqa: E402
    TrajectorySample,
    capture_uniform_target,
    trajectory_loss,
)
from topolab.b2_10_weighted_trajectory import (  # noqa: E402
    sensitivity_weighted_target,
)


def test_weighted_objective_changes_gradient_and_rejects_missing_weight() -> None:
    prediction = torch.tensor([[[[0.2, 0.8]]]], dtype=torch.float32, requires_grad=True)
    target = torch.tensor([[[[0.0, 0.0]]]], dtype=torch.float32)
    weight = torch.tensor([[[[0.25, 1.75]]]], dtype=torch.float32)
    loss = trajectory_loss(prediction, target, weight)
    assert loss.detach().item() == pytest.approx((0.25 * 0.2**2 + 1.75 * 0.8**2) / 2)
    loss.backward()
    np.testing.assert_allclose(prediction.grad.numpy(), [[[[0.05, 1.4]]]], atol=1e-7)
    with pytest.raises(ValueError, match="weight"):
        trajectory_loss(prediction, target, torch.ones((1, 1, 1), dtype=torch.float32))


def test_target_sensitivity_is_finite_normalized_and_nonuniform() -> None:
    case = _small_case(0.2875, "y", 2, 2)
    target = capture_uniform_target(case)
    weighted = sensitivity_weighted_target(case, target)
    assert weighted.weight.shape == target.density.shape
    assert weighted.weight.dtype == np.float32
    assert np.isfinite(weighted.weight).all()
    assert weighted.weight.min() > 0
    assert float(np.mean(weighted.weight, dtype=np.float64)) == pytest.approx(1.0, abs=1e-6)
    assert float(np.std(weighted.weight)) > 0.01
    assert weighted.compliance > 0
    sample = TrajectorySample(
        case_id=case.case_id,
        split="train",
        inputs=torch.zeros((13, 3, 6, 12), dtype=torch.float32),
        target=torch.from_numpy(target.density.copy()),
        input_channels=13,
        weight=torch.from_numpy(weighted.weight.copy()),
    )
    sample.validate()


def test_b2_10_plan_freezes_fresh_disjoint_screen() -> None:
    old, screen = cohorts()
    plan = plan_payload(old, screen)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(old["train"]) == 468 and len(old["validation"]) == 12
    assert len(screen) == 12 and len(METHODS) == 11
    assert {case.problem.optimization.volume_fraction for case in screen} == set(VOLUMES)
    assert {case.problem.loads[0].direction for case in screen} == {"y", "z"}
    assert {case.problem.mesh.element_counts for case in screen} == {(12, 6, 3), (24, 12, 6)}
    assert len({case.case_id for case in screen}) == 12
    assert set(plan["screen_case_ids"]).isdisjoint(set(plan["exposed_case_ids"]))
