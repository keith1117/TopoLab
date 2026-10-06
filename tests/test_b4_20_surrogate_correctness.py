"""Nonuniform serialized-state regression, independent review and durable failures."""

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
import b4_20_independent_audit as independent  # noqa: E402
import b4_20_resource_close as closure  # noqa: E402
import b4_20_surrogate_correctness as probe  # noqa: E402

from topolab.baselines import _case_system  # noqa: E402
from topolab.local_compliance import (  # noqa: E402
    LocalCompliance,
    StoredNormalizerTangent,
    torch_local_loss,
)
from topolab.simp import (  # noqa: E402
    apply_density_filter,
    build_density_filter,
    evaluate_compliance,
)


def synthetic(entry):
    case = entry.case
    mesh, loads, constrained = _case_system(case)
    p = case.problem
    n = int(np.prod(p.mesh.element_counts))
    anchor = (
        (p.optimization.volume_fraction + 0.11 * np.sin(0.37 * np.arange(1, n + 1)))
        .astype(
            np.float32,
        )
        .astype(np.float64)
    )
    filt = build_density_filter(mesh, p.optimization.filter_radius)
    continuous = apply_density_filter(filt, anchor)
    stored = continuous.astype(np.float32).astype(np.float64)

    def solve(rho):
        return evaluate_compliance(
            mesh,
            rho,
            loads,
            constrained,
            solid_modulus=p.material.solid_modulus,
            minimum_modulus=p.material.minimum_modulus,
            poisson_ratio=p.material.poisson_ratio,
            penalty=p.optimization.penalty,
        )

    cs, cc = solve(stored), solve(continuous)
    return anchor, stored, cs, cc


def test_nonuniform_serialized_normalizer_regression_and_fem_exclusion(monkeypatch):
    import topolab.local_compliance as module

    entry = probe.selected_entries()[0]
    anchor, stored, cs, cc = synthetic(entry)
    assert not np.isclose(cs.compliance, cc.compliance, rtol=1e-9, atol=0)
    with pytest.raises(ValueError, match="anchor compliance differs"):
        LocalCompliance(entry.case, anchor, cs.compliance)

    def forbidden(*args, **kwargs):
        pytest.fail("tangent construction/prediction must consume paid analysis, no FEM")

    monkeypatch.setattr(module, "evaluate_compliance", forbidden)
    kernel = StoredNormalizerTangent(entry.case, anchor, cs.compliance, cc)
    assert kernel.normalizer == cs.compliance
    assert kernel.anchor_compliance / kernel.normalizer != 1
    assert not np.array_equal(stored, apply_density_filter(kernel.filt, anchor))
    assert np.all(kernel.design_gradient < 0)
    assert all(not a.flags.writeable for a in kernel.retained_arrays())
    raw = probe.raw_fixture(entry.case, "interior")
    result = kernel.evaluate(raw)
    assert result.value == cc.compliance / cs.compliance + kernel.design_gradient @ (
        result.projection.design - anchor
    )
    for dtype in (torch.float32, torch.float64):
        tensor = torch.tensor(raw, dtype=dtype, requires_grad=True)
        loss = torch_local_loss(tensor, kernel)
        loss.backward()
        actual = kernel.evaluate(tensor.detach().numpy())
        assert loss.item() == pytest.approx(actual.value, rel=1e-6)
        np.testing.assert_allclose(tensor.grad.numpy(), actual.gradient, rtol=1e-6, atol=1e-8)
    kernel.design_gradient = -1e6 * (result.projection.design - anchor)
    assert kernel.evaluate(raw).value < 0
    with pytest.raises(ValueError):
        StoredNormalizerTangent(entry.case, anchor, -1, cc)


def test_failure_retains_before_call_and_counts_and_refuses_retry(tmp_path):
    path = tmp_path / "events"
    journal = probe.Journal(path, "a" * 40)

    def failure():
        events = [json.loads(line) for line in path.read_text().splitlines()]
        assert events[-1]["event"] == "before_fem"
        assert events[-1]["counts"]["fem"] == {"attempted": 1, "completed": 0}
        raise ValueError("injected anchor rejection")

    with pytest.raises(ValueError, match="injected"):
        journal.invoke("fem", "case", {"normalizer": 7, "state": "stored"}, failure, str)
    journal.close()
    events = [json.loads(line) for line in path.read_text().splitlines()]
    assert [e["event"] for e in events] == ["start", "before_fem", "failure"]
    assert events[-1]["context"] == {"normalizer": 7, "state": "stored"}
    assert events[-1]["counts"]["fem"]["completed"] == 0
    assert "ValueError: injected anchor rejection" in events[-1]["traceback"]
    with pytest.raises(FileExistsError):
        probe.Journal(path, "b" * 40)


def test_default_plan_has_no_reads_or_output(tmp_path, monkeypatch, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail("default plan must not open evidence or solve")

    monkeypatch.setattr(probe, "check_inputs", forbidden)
    monkeypatch.setattr(probe, "execution_release", forbidden)
    paths = [tmp_path / p for p in ("prior", "data", "output")]
    args = [
        value
        for key, path in zip(("review", "data", "output"), paths, strict=True)
        for value in ("--" + key + "-root", str(path))
    ]
    assert probe.main(args) == 0
    assert json.loads(capsys.readouterr().out) == probe.plan_payload()
    assert not any(p.exists() for p in paths)


def test_complete_synthetic_review_and_tamper_rejection(tmp_path, monkeypatch):
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
    p = probe.probe(None, None, journal, perf_counter())
    p["source_revision"] = "a" * 40
    journal.emit("complete")
    journal.close()
    p["journal_sha256"] = probe.sha((tmp_path / "probe.events.jsonl").read_bytes())
    assert independent.journal_check(tmp_path, p) == 170
    journal = probe.Journal(tmp_path / "independent.events.jsonl", "a" * 40)
    a = independent.audit(p, None, None, journal, perf_counter())
    journal.close()
    assert a["correctness_passed"] and a["failed_numerical_conditions"] == 0
    assert a["total_solver_calls"] == 32 and a["directional_rows"] == 64
    assert a["old_equality_rejects_new_anchors"] > 0
    assert a["maximum_directional_error"] <= 1e-4
    damaged = copy.deepcopy(p)
    damaged["cases"][0]["rows"][0]["raw"][0] += 0.01
    journal = probe.Journal(tmp_path / "damaged.events", "a" * 40)
    with pytest.raises(ValueError, match="fixture"):
        independent.audit(damaged, None, None, journal, perf_counter())
    journal.close()
    damaged = copy.deepcopy(p)
    damaged["journal_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="identity"):
        independent.journal_check(tmp_path, damaged)


@pytest.mark.parametrize("damage", ["none", "retry", "escape", "hash", "memory", "process"])
def test_failed_attempt_closure_and_cap_rejection(tmp_path, damage):
    (tmp_path / "profiles").mkdir()
    (tmp_path / "logs").mkdir()
    commands = []
    for name in ("plan", "probe"):
        profile = tmp_path / "profiles" / (name + ".time")
        log = tmp_path / "logs" / (name + ".log")
        profile.write_text("2.00 real 0.10 user 0.10 sys\n100 maximum resident set size\n")
        log.write_text("injected failure" if name == "probe" else "static plan")
        commands.append(
            {
                "name": name,
                "profile": "profiles/" + profile.name,
                "profile_sha256": probe.sha(profile.read_bytes()),
                "log": "logs/" + log.name,
                "log_sha256": probe.sha(log.read_bytes()),
                "exit_code": int(name == "probe"),
            }
        )
    if damage == "retry":
        commands.append(commands[-1])
    elif damage == "escape":
        commands[-1]["profile"] = "../outside"
    elif damage == "hash":
        commands[-1]["profile_sha256"] = "0" * 64
    elif damage in ("memory", "process"):
        profile = tmp_path / "profiles/probe.time"
        profile.write_text(
            "2.00 real 0.10 user 0.10 sys\n1073741825 maximum resident set size\n"
            if damage == "memory"
            else "301.00 real 0.10 user 0.10 sys\n100 maximum resident set size\n"
        )
        commands[-1]["profile_sha256"] = probe.sha(profile.read_bytes())
    if damage == "none":
        result = closure.close_resources(tmp_path, commands, None, None)
        assert result["charged_seconds"] == 72 and result["failed_attempts"] == 1
        assert not result["full_panel_complete"] and result["next_slice"] == probe.FAIL_NEXT
        assert result["fit_proxy"] is None
    else:
        with pytest.raises(ValueError):
            closure.close_resources(tmp_path, commands, None, None)
