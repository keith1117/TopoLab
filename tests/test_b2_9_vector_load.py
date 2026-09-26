"""B2.9 vector-load representation, model, and frozen screen."""

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_6_trajectory import _small_case  # noqa: E402
from b2_9_vector_load import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    METHODS,
    VOLUMES,
    cohorts,
    plan_payload,
)

from topolab.b2_9_vector_load import (  # noqa: E402
    VECTOR_MODEL_PARAMETER_COUNT,
    VectorLoadCNN,
    encode_vector_load_case,
)
from topolab.experiment import encode_case  # noqa: E402


def test_vector_load_exposes_signed_direction_and_relative_coordinates() -> None:
    case = _small_case(0.2625, "y", 1, 2)
    original = encode_case(case).input_tensor
    encoded = encode_vector_load_case(case).input_tensor
    assert encoded.shape == (13, 3, 6, 12)
    np.testing.assert_array_equal(encoded[:3], original[:3])
    np.testing.assert_array_equal(encoded[6:10], original[6:10])
    np.testing.assert_array_equal(encoded[3], np.zeros_like(encoded[3]))
    np.testing.assert_array_equal(encoded[4], -np.ones_like(encoded[4]))
    np.testing.assert_array_equal(encoded[5], np.zeros_like(encoded[5]))
    np.testing.assert_allclose(
        encoded[10:13, 1, 2, 11],
        [11.5 / 12 - 1, 2.5 / 6 - 1 / 6, 1.5 / 3 - 2 / 3],
        rtol=0, atol=1e-7,
    )
    np.testing.assert_array_equal(original, encode_case(case).input_tensor)


def test_vector_model_preserves_shape_and_fixed_size() -> None:
    model = VectorLoadCNN()
    assert sum(parameter.numel() for parameter in model.parameters()) == (
        VECTOR_MODEL_PARAMETER_COUNT
    )
    case = _small_case(0.2625, "z", 1, 2)
    inputs = torch.from_numpy(encode_vector_load_case(case).input_tensor).unsqueeze(0)
    result = model(inputs)
    assert result.shape == (1, 1, 3, 6, 12)
    assert result.dtype == torch.float32
    assert torch.isfinite(result).all()
    assert torch.all((result >= 0) & (result <= 1))
    with pytest.raises(ValueError, match="13"):
        model(torch.zeros((1, 10, 3, 6, 12), dtype=torch.float32))


def test_frozen_b2_9_screen_is_disjoint_and_complete() -> None:
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
