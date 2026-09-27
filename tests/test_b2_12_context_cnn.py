"""B2.12 spatial context and physically disjoint development cohort."""

import sys
from pathlib import Path

import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_12_context_cnn import (  # noqa: E402
    BUDGET,
    EXPECTED_PLAN_SHA256,
    METHODS,
    VOLUMES,
    cohorts,
    plan_payload,
    reference_gate,
)

from topolab.b2_12_context_cnn import (  # noqa: E402
    CONTEXT_MODEL_PARAMETER_COUNT,
    ContextCNN,
)


def test_context_model_reaches_beyond_the_prior_local_field() -> None:
    model = ContextCNN()
    assert CONTEXT_MODEL_PARAMETER_COUNT == 26_433
    assert sum(parameter.numel() for parameter in model.parameters()) == (
        CONTEXT_MODEL_PARAMETER_COUNT
    )
    for shape in ((3, 6, 12), (6, 12, 24)):
        outputs = model(torch.zeros((1, 13, *shape), dtype=torch.float32))
        assert outputs.shape == (1, 1, *shape)
        assert torch.isfinite(outputs).all()
        assert torch.all((outputs > 0) & (outputs < 1))
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.fill_(0.01)
    inputs = torch.zeros((1, 13, 6, 12, 24), dtype=torch.float32, requires_grad=True)
    model(inputs)[0, 0, 3, 6, 15].backward()
    assert inputs.grad is not None
    assert inputs.grad[0, 0, 3, 6, 0] > 0
    with pytest.raises(ValueError):
        model(torch.zeros((1, 10, 6, 12, 24), dtype=torch.float32))


def test_plan_freezes_complete_disjoint_reference_and_screen() -> None:
    source, screen, exposed = cohorts()
    plan = plan_payload(source, screen, exposed)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(source["train"]) == 468
    assert len(source["validation"]) == 12
    assert len(screen) == 12
    assert len(METHODS) == 11
    assert {case.problem.optimization.volume_fraction for case in screen} == set(VOLUMES)
    assert {case.problem.loads[0].direction for case in screen} == {"y", "z"}
    assert {case.problem.mesh.element_counts for case in screen} == {
        (12, 6, 3), (24, 12, 6)
    }
    assert all(case.problem.optimization.max_iterations == BUDGET for case in screen)
    assert set(plan["screen_case_ids"]).isdisjoint(set(plan["exposed_case_ids"]))
    assert set(VOLUMES).isdisjoint(set(plan["exposed_volumes"]))


def test_reference_gate_retains_a_failed_mandatory_denominator() -> None:
    _, screen, _ = cohorts()
    index = {
        "rows": [
            {
                "case_id": case.case_id,
                "uniform": {
                    "succeeded": True,
                    "candidate": {
                        "final_compliance": 1.0,
                        "physical_volume_error": 0.0,
                    },
                },
            }
            for case in screen
        ],
        "elapsed_seconds": 100.0,
        "peak_rss_bytes": 100_000_000,
    }
    assert reference_gate(index, screen)
    index["rows"][5]["uniform"]["succeeded"] = False
    assert not reference_gate(index, screen)
    assert len(index["rows"]) == 12
