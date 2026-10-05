"""Continuous projection derivatives and the paid CPU FEM autograd boundary."""

import numpy as np
import pytest
import torch
from scipy.sparse import csr_matrix

from topolab.offline_compliance import OfflineCompliance, project, pullback, torch_loss
from topolab.simp import DensityFilter


def filter_fixture():
    matrix = csr_matrix(
        np.array(
            [[2.0, 1.0, 0.0, 0.0], [1.0, 2.0, 1.0, 0.0], [0.0, 1.0, 2.0, 1.0], [0.0, 0.0, 1.0, 2.0]]
        )
    )
    return DensityFilter(matrix, np.asarray(matrix.sum(axis=1)).ravel())


def test_projection_clipped_offset_gradient_and_volume():
    filt = filter_fixture()
    raw = np.array([0.01, 0.35, 0.6, 0.99])
    state = project(filt, raw, 0.51, 0.05)
    gradient = np.array([2.0, -3.0, 4.0, 5.0])
    actual = pullback(state, gradient)
    assert state.free.tolist() == [False, True, True, False]
    assert abs(state.physical.mean() - 0.51) <= 1e-12
    assert abs(actual.sum()) <= 1e-12
    np.testing.assert_allclose(pullback(state, state.weights), 0, atol=1e-15)
    direction = np.array([0.2, -0.4, 0.3, 0.1])
    step = 1e-5
    plus = project(filt, raw + step * direction, 0.51, 0.05)
    minus = project(filt, raw - step * direction, 0.51, 0.05)
    fd = float(gradient @ (plus.design - minus.design)) / (2 * step)
    assert float(actual @ direction) == pytest.approx(fd, rel=1e-6)
    assert actual[0] == actual[3] == 0


@pytest.mark.parametrize(
    "raw", [np.array([np.nan] * 4), np.zeros(3), np.array([-0.1, 0.3, 0.6, 0.9])]
)
def test_invalid_raw_rejected(raw):
    with pytest.raises(ValueError):
        project(filter_fixture(), raw, 0.5, 0.05)


def test_clipping_kink_rejected():
    with pytest.raises(ValueError, match="kink"):
        project(
            filter_fixture(),
            np.array([0.05, 0.4, 0.6, 0.8]),
            float(
                np.array([0.05, 0.4, 0.6, 0.8])
                @ np.asarray(filter_fixture().matrix.T @ (np.ones(4) / filter_fixture().row_sums))
                / 4
            ),
            0.05,
        )


def test_fem_torch_bridge_and_gradient_dtype():
    from topolab.b3_catalog import build_b3_case_catalog

    case = next(
        e.case
        for e in build_b3_case_catalog().entries
        if e.role == "train" and e.case.problem.mesh.element_counts[0] == 12
    )
    kernel = OfflineCompliance(case, 1.0)
    i = np.arange(1, kernel.mesh.element_dofs.shape[0] + 1)
    raw = case.problem.optimization.volume_fraction + 0.02 * np.sin(0.37 * i)
    for dtype in (torch.float64, torch.float32):
        value = torch.tensor(raw, dtype=dtype, requires_grad=True)
        loss = torch_loss(value, kernel)
        loss.backward()
        expected = kernel.evaluate(value.detach().numpy())
        assert value.grad is not None and value.grad.dtype == dtype
        np.testing.assert_allclose(value.grad.numpy(), expected.gradient, rtol=1e-6, atol=1e-8)
        assert loss.item() == pytest.approx(expected.value, rel=1e-6)
    with pytest.raises(ValueError):
        OfflineCompliance(case, 0.0)
