"""Signed tangent, constant normalization and prediction-time FEM exclusion."""

import numpy as np
import pytest
import torch

from topolab.b3_catalog import build_b3_case_catalog
from topolab.local_compliance import LocalCompliance, torch_local_loss
from topolab.offline_compliance import OfflineCompliance


@pytest.fixture
def kernel():
    case = next(
        e.case
        for e in build_b3_case_catalog().entries
        if e.role == "train" and e.case.problem.mesh.element_counts[0] == 12
    )
    anchor = np.full(
        int(np.prod(case.problem.mesh.element_counts)), case.problem.optimization.volume_fraction
    )
    exact = OfflineCompliance(case, 1.0).evaluate(anchor)
    return LocalCompliance(case, anchor, exact.compliance)


def test_signed_anchor_derivative_and_prediction_does_not_solve(kernel, monkeypatch):
    import topolab.local_compliance as module

    assert np.all(kernel.design_gradient < 0)
    assert all(not a.flags.writeable for a in kernel.retained_arrays())
    original = kernel.anchor.copy()
    raw = kernel.anchor + 0.001 * np.sin(np.arange(kernel.anchor.size))

    def forbidden(*args, **kwargs):
        pytest.fail("prediction must not call FEM")

    monkeypatch.setattr(module, "evaluate_compliance", forbidden)
    result = kernel.evaluate(raw)
    np.testing.assert_array_equal(original, kernel.anchor)
    assert result.value == 1 + kernel.design_gradient @ (result.projection.design - kernel.anchor)
    assert abs(result.gradient.sum()) <= 1e-10
    d = np.cos(np.arange(raw.size))
    h = 1e-4
    fd = (kernel.evaluate(raw + h * d).value - kernel.evaluate(raw - h * d).value) / (2 * h)
    assert fd == pytest.approx(result.gradient @ d, rel=1e-4, abs=1e-8)


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_first_order_dtype_bridge(kernel, dtype):
    raw = torch.tensor(
        kernel.anchor + 0.02 * np.sin(np.arange(kernel.anchor.size)),
        dtype=dtype,
        requires_grad=True,
    )
    loss = torch_local_loss(raw, kernel)
    (2 * loss).backward()
    result = kernel.evaluate(raw.detach().numpy())
    assert raw.grad.dtype == dtype
    assert loss.item() == pytest.approx(result.value, rel=1e-6)
    np.testing.assert_allclose(raw.grad.numpy(), 2 * result.gradient, rtol=1e-6, atol=1e-8)
    with pytest.raises(ValueError):
        torch_local_loss(torch.ones(raw.numel(), dtype=torch.int64), kernel)


def test_negative_estimates_are_retained(kernel):
    raw = kernel.anchor + 0.05 * np.sin(np.arange(kernel.anchor.size))
    kernel.design_gradient = -1e5 * (raw - kernel.anchor)
    assert kernel.evaluate(raw).value < 0


@pytest.mark.parametrize("kind", ["normalizer", "shape", "bounds", "nan"])
def test_invalid_anchor_and_normalizer_rejected(kernel, kind):
    anchor = kernel.anchor.copy()
    normalizer = kernel.normalizer
    if kind == "normalizer":
        normalizer *= 1.01
    elif kind == "shape":
        anchor = anchor[:-1]
    elif kind == "bounds":
        anchor[0] = 0
    else:
        anchor[0] = np.nan
    with pytest.raises(ValueError):
        LocalCompliance(kernel.case, anchor, normalizer)
