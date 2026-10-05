"""Prepared setup parity, current-density factors and complete first derivatives."""

import numpy as np
import pytest
import torch
from scipy.sparse import csc_matrix

import topolab.prepared_compliance as prepared
from topolab.b3_catalog import build_b3_case_catalog
from topolab.offline_compliance import OfflineCompliance, project, torch_loss


@pytest.fixture(params=[12, 24])
def kernel(request):
    case = next(
        e.case
        for e in build_b3_case_catalog().entries
        if e.role == "train" and e.case.problem.mesh.element_counts[0] == request.param
    )
    return prepared.PreparedCompliance(case, 2.0)


def raw(kernel):
    i = np.arange(1, kernel.weights.size + 1)
    return kernel.case.problem.optimization.volume_fraction + 0.02 * np.sin(0.37 * i)


@pytest.mark.parametrize("clipped", [False, True])
def test_prepared_original_and_instrumented_full_gradient_parity(kernel, clipped):
    z = np.resize([0.02, 0.5, 0.98], kernel.weights.size) if clipped else raw(kernel)
    phases = []
    result = kernel.evaluate(z, phases)
    original = OfflineCompliance(kernel.case, kernel.normalizer).evaluate(z)
    np.testing.assert_array_equal(result.projection.design, original.projection.design)
    np.testing.assert_array_equal(result.projection.physical, original.projection.physical)
    np.testing.assert_allclose(result.gradient, original.gradient, rtol=1e-9, atol=1e-10)
    assert result.value == pytest.approx(original.value, rel=1e-9)
    assert [p["phase"] for p in phases] == list(prepared.PHASES)
    assert all(p[k] >= 0 for p in phases for k in ("wall_seconds", "cpu_seconds"))
    with pytest.raises(ValueError, match="empty"):
        kernel.evaluate(z, phases)


def test_changing_prediction_refactors_and_keeps_cache_readonly(kernel, monkeypatch):
    calls = []
    original = prepared.splu

    def observed(matrix, **kw):
        calls.append((matrix.copy(), kw))
        return original(matrix, **kw)

    monkeypatch.setattr(prepared, "splu", observed)
    first = kernel.evaluate(raw(kernel))
    i = np.arange(kernel.weights.size)
    second = kernel.evaluate(raw(kernel) + 0.01 * np.cos(0.13 * i))
    assert len(calls) == 2 and all(isinstance(c[0], csc_matrix) for c in calls)
    assert (
        calls[0][1]
        == calls[1][1]
        == {"permc_spec": "MMD_AT_PLUS_A" if kernel.free_dofs.size >= 5000 else "COLAMD"}
    )
    assert not np.array_equal(calls[0][0].data, calls[1][0].data)
    assert first.value != second.value
    for a in (
        kernel.unit,
        kernel.rows,
        kernel.columns,
        kernel.weights,
        kernel.free_dofs,
        kernel.free_loads,
        kernel.loads,
        kernel.filt.matrix.data,
    ):
        assert not a.flags.writeable
        with pytest.raises(ValueError):
            a.flat[0] = 0
    assert kernel.retained_array_bytes > kernel.rows.nbytes + kernel.columns.nbytes


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_torch_dtype_bridge_uses_complete_prepared_gradient(kernel, dtype):
    z = torch.tensor(raw(kernel), dtype=dtype, requires_grad=True)
    value = torch_loss(z, kernel)
    value.backward()
    expected = kernel.evaluate(z.detach().numpy())
    assert z.grad.dtype == dtype
    np.testing.assert_allclose(z.grad.numpy(), expected.gradient, rtol=1e-6, atol=1e-8)
    assert value.item() == pytest.approx(expected.value, rel=1e-6)


@pytest.mark.parametrize("bad", ["nan", "shape", "range"])
def test_bad_raw_rejected_before_factorization(kernel, monkeypatch, bad):
    monkeypatch.setattr(
        prepared, "splu", lambda *a, **k: pytest.fail("invalid input reached solve")
    )
    z = raw(kernel)
    if bad == "nan":
        z[0] = np.nan
    elif bad == "shape":
        z = z[:-1]
    else:
        z[0] = -0.1
    with pytest.raises(ValueError, match="raw"):
        kernel.evaluate(z)


def test_kink_rejected_same_as_original(kernel):
    z = raw(kernel)
    z[0] = kernel.case.problem.optimization.minimum_density
    volume = float(kernel.weights @ z)
    opt = kernel.case.problem.optimization.model_copy(update={"volume_fraction": volume})
    problem = kernel.case.problem.model_copy(update={"optimization": opt})
    case = kernel.case.model_copy(update={"problem": problem})
    altered = prepared.PreparedCompliance(case, 2.0)
    with pytest.raises(ValueError, match="kink"):
        altered.projection(z)
    with pytest.raises(ValueError, match="kink"):
        project(altered.filt, z, volume, opt.minimum_density)


def test_singular_and_nonfinite_solve_checks_remain(kernel, monkeypatch):
    def singular(*a, **k):
        raise RuntimeError("singular")

    monkeypatch.setattr(prepared, "splu", singular)
    with pytest.raises(ValueError, match="singular"):
        kernel.evaluate(raw(kernel))

    class Factor:
        U = csc_matrix(np.eye(kernel.free_dofs.size))

        def solve(self, loads):
            return np.full(loads.shape, np.nan)

    monkeypatch.setattr(prepared, "splu", lambda *a, **k: Factor())
    with pytest.raises(ValueError, match="non-finite"):
        kernel.evaluate(raw(kernel))


def test_independent_brent_energy_and_fixed_step_gradient(kernel):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    from b4_15_independent_audit import independent_state

    z = np.resize([0.02, 0.5, 0.98], kernel.weights.size)
    result = kernel.evaluate(z)
    design, physical, free, gradient, value = independent_state(kernel.case, z, 2.0)
    np.testing.assert_allclose(result.projection.design, design, rtol=0, atol=2e-11)
    np.testing.assert_allclose(result.projection.physical, physical, rtol=0, atol=2e-11)
    np.testing.assert_array_equal(result.projection.free, free)
    np.testing.assert_allclose(result.gradient, gradient, rtol=1e-9, atol=1e-10)
    assert result.value == pytest.approx(value, rel=1e-9)
    vector = np.sin(0.37 * np.arange(1, z.size + 1))
    vector /= np.max(np.abs(vector))
    fd = (
        kernel.evaluate(z + 1e-4 * vector).value - kernel.evaluate(z - 1e-4 * vector).value
    ) / 2e-4
    adjoint = float(result.gradient @ vector)
    assert abs(fd - adjoint) / max(abs(fd), abs(adjoint), 1e-8) <= 1e-4
