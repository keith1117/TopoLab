"""Stable-root regression, complete synthetic audit and retained interrupted calls."""

import copy
import json
import sys
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

import numpy as np
import pytest
import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_22_independent_audit as independent  # noqa: E402
import b4_22_resource_close as closure  # noqa: E402
import b4_22_stable_projection_correctness as probe  # noqa: E402
from test_b4_20_surrogate_correctness import synthetic  # noqa: E402

from topolab.baselines import _case_system  # noqa: E402
from topolab.local_compliance import StoredNormalizerTangent, torch_local_loss  # noqa: E402
from topolab.offline_compliance import project, pullback  # noqa: E402
from topolab.simp import build_density_filter  # noqa: E402
from topolab.stable_projection import StableStoredNormalizerTangent, project_stable  # noqa: E402


@pytest.mark.parametrize("state", ["interior", "clipped"])
def test_affine_root_preserves_operator_masks_and_implicit_cotangent(state):
    entry = probe.selected_entries()[0]
    mesh, _, _ = _case_system(entry.case)
    settings = entry.case.problem.optimization
    filt = build_density_filter(mesh, settings.filter_radius)
    raw = probe.raw_fixture(entry.case, state)
    old = project(filt, raw, settings.volume_fraction, settings.minimum_density)
    new = project_stable(filt, raw, settings.volume_fraction, settings.minimum_density)
    operator = filt.matrix.multiply((1 / filt.row_sums)[:, None]).tocsr()
    design, physical, free, _, info = independent.independent_projection(entry.case, operator, raw)
    assert np.array_equal(old.free, new.free) and np.array_equal(new.free, free)
    np.testing.assert_allclose(new.design, design, rtol=0, atol=2e-11)
    np.testing.assert_allclose(new.physical, physical, rtol=0, atol=2e-11)
    assert abs(new.physical.mean() - settings.volume_fraction) <= 1e-12
    assert abs(new.offset - info["offset"]) <= 2e-11
    g = -3 * new.weights + 1e-7 * probe.direction_vector(raw.size, "sine")
    np.testing.assert_array_equal(pullback(old, g), pullback(new, g))
    gradient = pullback(new, g)
    old_errors, new_errors = [], []
    for name in ("sine", "cosine"):
        direction = probe.direction_vector(raw.size, name)
        derivative = float(gradient @ direction)
        for h in (1e-4, 2e-4):
            for implementation, errors in ((project, old_errors), (project_stable, new_errors)):
                values = [
                    2
                    + float(
                        g
                        @ implementation(
                            filt,
                            raw + sign * h * direction,
                            settings.volume_fraction,
                            settings.minimum_density,
                        ).design
                    )
                    for sign in (1, -1)
                ]
                fd = (values[0] - values[1]) / (2 * h)
                errors.append(abs(fd - derivative) / max(abs(fd), abs(derivative), 1e-8))
    assert max(old_errors) > 1e-4
    assert max(new_errors) <= 1e-4


@pytest.mark.parametrize("kind", ["nan", "negative", "above_one", "shape", "volume"])
def test_legacy_input_rejections_are_preserved(kind):
    entry = probe.selected_entries()[0]
    mesh, _, _ = _case_system(entry.case)
    settings = entry.case.problem.optimization
    filt = build_density_filter(mesh, settings.filter_radius)
    raw = probe.raw_fixture(entry.case, "interior")
    volume = settings.volume_fraction
    if kind == "nan":
        raw[0] = np.nan
    elif kind == "negative":
        raw[0] = -1
    elif kind == "above_one":
        raw[0] = 2
    elif kind == "shape":
        raw = raw[:-1]
    else:
        volume = 1
    with pytest.raises(ValueError):
        project_stable(filt, raw, volume, settings.minimum_density)


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_paid_analysis_tangent_and_torch_have_no_fem_or_new_cache(monkeypatch, dtype):
    import topolab.local_compliance as module

    entry = probe.selected_entries()[0]
    anchor, _, cs, cc = synthetic(entry)
    monkeypatch.setattr(module, "evaluate_compliance", lambda *a, **k: pytest.fail("unpaid FEM"))
    kernel = StableStoredNormalizerTangent(entry.case, anchor, cs.compliance, cc)
    old = StoredNormalizerTangent(entry.case, anchor, cs.compliance, cc)
    assert kernel.normalizer == old.normalizer and kernel.anchor_compliance == old.anchor_compliance
    assert kernel.anchor_compliance / kernel.normalizer != 1
    assert all(not a.flags.writeable for a in kernel.retained_arrays())
    assert not hasattr(kernel, "__dict__")
    raw = probe.raw_fixture(entry.case, "clipped")
    tensor = torch.tensor(raw, dtype=dtype, requires_grad=True)
    loss = torch_local_loss(tensor, kernel)
    loss.backward()
    direct = kernel.evaluate(tensor.detach().numpy())
    assert loss.item() == pytest.approx(direct.value, rel=1e-6)
    np.testing.assert_allclose(tensor.grad.numpy(), direct.gradient, rtol=1e-6, atol=1e-8)
    kernel.design_gradient = -1e6 * (direct.projection.design - anchor)
    assert kernel.evaluate(raw).value < 0


def test_default_plan_reads_no_evidence_and_creates_no_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("artifact read"))
    args = [
        value
        for key in ("review", "data", "output")
        for value in ("--" + key + "-root", str(tmp_path / key))
    ]
    assert probe.main(args) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan == probe.plan_payload() and plan["numerical_conditions"] == 1704
    assert plan["probe_projections"] == 160 and plan["audit_projections"] == 144
    assert not any((tmp_path / k).exists() for k in ("review", "data", "output"))


def test_complete_synthetic_population_journal_and_independent_conditions(tmp_path, monkeypatch):
    records = {}
    for entry in probe.selected_entries():
        anchor, stored, cs, _ = synthetic(entry)
        records[entry.case.case_id] = SimpleNamespace(
            stored=SimpleNamespace(
                design_density=anchor.tolist(),
                physical_density=stored.tolist(),
                compliance=cs.compliance,
            )
        )

    def label(data, index, entry):
        return records[entry.case.case_id], {"synthetic": entry.case.case_id}

    monkeypatch.setattr(probe, "train_label", label)
    monkeypatch.setattr(independent, "train_label", label)
    journal = probe.Journal(tmp_path / "probe.events.jsonl", "a" * 40)
    panel = probe.probe(None, None, journal, perf_counter())
    panel["source_revision"] = "a" * 40
    journal.emit("complete")
    journal.close()
    panel["journal_sha256"] = probe.sha((tmp_path / "probe.events.jsonl").read_bytes())
    assert independent.journal_check(tmp_path, panel) == 554
    assert panel["counts"]["projection"] == {"attempted": 160, "completed": 160}
    audit_journal = probe.Journal(tmp_path / "independent.events.jsonl", "a" * 40)
    audit = independent.audit(panel, None, None, audit_journal, perf_counter())
    audit_journal.close()
    assert (
        audit["passed"]
        and audit["correctness_passed"]
        and audit["failed_numerical_conditions"] == 0
    )
    assert audit["numerical_conditions"] == 1704 and audit["total_solver_calls"] == 32
    assert audit["total_projection_calls"] == 304
    assert audit_journal.counts["projection"] == {"attempted": 144, "completed": 144}
    damaged = copy.deepcopy(panel)
    damaged["cases"][0]["rows"][0]["projection"]["offset"] += 0.01
    with pytest.raises(ValueError, match="durable numerical prefix"):
        independent.journal_check(tmp_path, damaged)
    damaged = copy.deepcopy(panel)
    damaged["counts"]["projection"]["completed"] -= 1
    with pytest.raises(ValueError, match="count"):
        independent.journal_check(tmp_path, damaged)


def test_interrupted_projection_has_exact_pending_count_and_metadata_only_audit(
    tmp_path, monkeypatch
):
    journal = probe.Journal(tmp_path / "probe.events.jsonl", "a" * 40)
    context = {
        "state": "clipped",
        "kind": "side",
        "direction": "sine",
        "step": 1e-4,
        "sign": -1,
        "raw_sha256": "b" * 64,
    }

    def rejected():
        raise ValueError("injected projection rejection")

    with pytest.raises(ValueError, match="injected"):
        journal.invoke("projection", "case", context, rejected, str)
    journal.emit("abort", error="injected")
    journal.close()
    (tmp_path / "profiles").mkdir()
    (tmp_path / "logs").mkdir()
    (tmp_path / "audit_receipts").mkdir()
    (tmp_path / "profiles/probe.time").write_text(
        "2 real 1 user 0 sys\n100 maximum resident set size\n"
    )
    (tmp_path / "logs/probe.log").write_text("injected failure")
    command = {"exit_code": 1, "profile": "profiles/probe.time", "log": "logs/probe.log"}
    for kind in ("profile", "log"):
        command[kind + "_sha256"] = probe.sha((tmp_path / command[kind]).read_bytes())
    (tmp_path / "audit_receipts/probe_command.json").write_bytes(probe.canonical(command))
    monkeypatch.setattr(independent, "energy", lambda *a: pytest.fail("FEM during abort audit"))
    monkeypatch.setattr(
        independent, "independent_projection", lambda *a: pytest.fail("new root during abort audit")
    )
    audit = independent.abort_audit(tmp_path, "a" * 40)
    assert audit["passed"] and audit["metadata_only"] and not audit["correctness_passed"]
    assert audit["actual_probe_counts"]["projection"] == {"attempted": 1, "completed": 0}
    assert (
        audit["pending_operations"] == ["projection"] and audit["actual_failed_context"] == context
    )
    assert (
        audit["full_panel_directional_error"] is None
        and audit["new_label_fem_projection_calls"] == 0
    )
    with pytest.raises(FileExistsError):
        probe.Journal(tmp_path / "probe.events.jsonl", "a" * 40)


@pytest.mark.parametrize(
    "field", ["offset", "weighted_volume_residual", "physical_volume_residual", "kink_margin"]
)
def test_independent_scalar_conditions_reject_forged_root_evidence(field):
    expected = {
        "offset": 0.1,
        "weighted_volume_residual": 0.0,
        "physical_volume_residual": 0.0,
        "kink_margin": 0.02,
    }
    actual = expected.copy()
    actual[field] += 0.001
    assert not all(independent.projection_conditions(actual, expected))


@pytest.mark.parametrize("damage", ["none", "retry", "hash", "escape", "cap", "rss"])
def test_failed_complete_native_charge_and_no_retry_extension(tmp_path, damage):
    (tmp_path / "profiles").mkdir()
    (tmp_path / "logs").mkdir()
    commands = []
    for name in ("plan", "probe", "independent"):
        (tmp_path / ("profiles/" + name + ".time")).write_text(
            "2 real 1 user 0 sys\n100 maximum resident set size\n"
        )
        (tmp_path / ("logs/" + name + ".log")).write_text("synthetic")
        c = {
            "name": name,
            "profile": "profiles/" + name + ".time",
            "log": "logs/" + name + ".log",
            "exit_code": 1,
        }
        for kind in ("profile", "log"):
            c[kind + "_sha256"] = probe.sha((tmp_path / c[kind]).read_bytes())
        commands.append(c)
    if damage == "retry":
        commands.append(commands[-1])
    elif damage == "hash":
        commands[-1]["profile_sha256"] = "0" * 64
    elif damage == "escape":
        commands[-1]["profile"] = "../escaped"
    elif damage in ("cap", "rss"):
        p = tmp_path / commands[-1]["profile"]
        p.write_text(
            "301 real 1 user 0 sys\n100 maximum resident set size\n"
            if damage == "cap"
            else "2 real 1 user 0 sys\n1073741825 maximum resident set size\n"
        )
        commands[-1]["profile_sha256"] = probe.sha(p.read_bytes())
    if damage == "none":
        result = closure.close_resources(tmp_path, commands, None, None)
        assert result["charged_seconds"] == 84 and result["paid_reservation_seconds"] == 60
        assert not result["full_panel_complete"] and result["next_slice"] == probe.FAIL_NEXT
    else:
        with pytest.raises(ValueError):
            closure.close_resources(tmp_path, commands, None, None)
