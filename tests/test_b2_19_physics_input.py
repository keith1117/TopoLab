"""B2.19 physical feature, model, and sealed development cohort."""

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_6_trajectory import _small_case  # noqa: E402
from b2_19_physics_input import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    METHODS,
    VOLUMES,
    cohorts,
    plan_payload,
    reference_gate,
)

from topolab.b2_9_vector_load import encode_vector_load_case  # noqa: E402
from topolab.b2_19_physics_input import (  # noqa: E402
    MODEL_PARAMETER_COUNT,
    PhysicsContextCNN,
    encode_physics_case,
)


def test_uniform_physical_feature_is_spatial_and_preserves_vector_input() -> None:
    case = _small_case(0.45, "y", 1, 2)
    encoded = encode_physics_case(case)
    original = encode_vector_load_case(case)
    assert encoded.input_tensor.shape == (14, 3, 6, 12)
    np.testing.assert_array_equal(encoded.input_tensor[:13], original.input_tensor)
    assert encoded.load_scale == original.load_scale
    feature = encoded.input_tensor[13]
    assert np.isfinite(feature).all()
    assert feature.min() >= 0
    assert feature.max() == pytest.approx(1.0, abs=1e-6)
    assert np.std(feature) > 0.01
    alternate = encode_physics_case(_small_case(0.45, "z", 1, 2))
    assert not np.array_equal(feature, alternate.input_tensor[13])


def test_physical_context_model_shape_and_parameter_count() -> None:
    model = PhysicsContextCNN()
    assert sum(parameter.numel() for parameter in model.parameters()) == (
        MODEL_PARAMETER_COUNT
    )
    for shape in ((3, 6, 12), (6, 12, 24)):
        output = model(torch.zeros((1, 14, *shape), dtype=torch.float32))
        assert output.shape == (1, 1, *shape)
        assert torch.isfinite(output).all()
    with pytest.raises(ValueError):
        model(torch.zeros((1, 13, 3, 6, 12), dtype=torch.float32))


def test_frozen_plan_and_reference_gate() -> None:
    groups, fresh, blocked = cohorts()
    plan = plan_payload(groups, fresh, blocked)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(groups["train"]) == 468
    assert len(groups["validation"]) == 12
    assert len(blocked) == 664
    assert len(fresh) == 12
    assert len(METHODS) == 7
    assert {case.problem.optimization.volume_fraction for case in fresh} == set(VOLUMES)
    assert {case.problem.loads[0].direction for case in fresh} == {"y", "z"}
    assert {case.problem.mesh.element_counts for case in fresh} == {
        (12, 6, 3), (24, 12, 6)
    }
    assert set(plan["screen_case_ids"]).isdisjoint(plan["blocked_case_ids"])
    index = {
        "rows": [{"case_id": case.case_id, "uniform": {
            "succeeded": True,
            "candidate": {"final_compliance": 1.0, "physical_volume_error": 0.0},
        }} for case in fresh],
        "elapsed_seconds": 100.0,
        "peak_rss_bytes": 100_000_000,
    }
    assert reference_gate(index, fresh)
    index["rows"][0]["uniform"]["succeeded"] = False
    assert not reference_gate(index, fresh)
