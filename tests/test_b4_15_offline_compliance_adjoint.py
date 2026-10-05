"""Frozen train-only access, independent projection/FEM and charged stop decisions."""

import copy
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_15_independent_audit as audit  # noqa: E402
import b4_15_offline_compliance_adjoint as probe  # noqa: E402
import b4_15_resource_close as closure  # noqa: E402

from topolab.b3_catalog import build_b3_case_catalog  # noqa: E402
from topolab.offline_compliance import OfflineCompliance  # noqa: E402


def test_plan_no_artifact_reads_solver_calls_or_outputs(monkeypatch, tmp_path, capsys):
    # Construct the metadata catalog first, then prohibit every byte read.
    plan = probe.plan_payload()

    def forbidden(*args, **kwargs):
        pytest.fail("planning must not read artifacts or solve FEM")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(OfflineCompliance, "evaluate", forbidden)
    out = tmp_path / "out"
    assert (
        probe.main(
            [
                "--review-root",
                str(tmp_path / "review"),
                "--data-root",
                str(tmp_path / "data"),
                "--output-root",
                str(out),
            ]
        )
        == 0
    )
    assert plan["plan_sha256"] in capsys.readouterr().out
    assert not out.exists()
    assert len(plan["entries"]) == 8
    assert all(e["role"] == "train" and "expanded" in e["training_sets"] for e in plan["entries"])


def test_forbidden_labels_rejected_before_metadata_or_byte_lookup():
    selected = probe.selected_entries()
    catalog = build_b3_case_catalog()
    entries = [
        next(e for e in catalog.entries if e.role == role)
        for role in ("fit_validation", "screen_validation", "final_id", "final_ood")
    ]
    entries.append(next(e for e in catalog.entries if e.role == "train" and e not in selected))
    for entry in entries:
        with pytest.raises(ValueError, match="only frozen eight"):
            probe.train_label(Path("/unused"), None, entry)


def test_independent_fem_projection_and_full_gradient():
    case = probe.selected_entries()[0].case
    kernel = OfflineCompliance(case, 2.0)
    raw = probe.raw_fixture(case, "clipped")
    result = kernel.evaluate(raw)
    design, physical, free, gradient, value = audit.independent_state(case, raw, 2.0)
    np.testing.assert_allclose(design, result.projection.design, rtol=0, atol=2e-11)
    np.testing.assert_allclose(physical, result.projection.physical, rtol=0, atol=2e-11)
    np.testing.assert_array_equal(free, result.projection.free)
    np.testing.assert_allclose(gradient, result.gradient, rtol=1e-9, atol=1e-10)
    assert value == pytest.approx(result.value, rel=1e-9)


def fixture():
    p = {
        "plan": probe.plan_payload(),
        "rows": [
            {"scale": s, "timings": [{"wall_seconds": t}] * 3}
            for s, t in (("small", 0.001), ("large", 0.002))
        ],
        "charged_seconds": 11.0,
        "peak_rss_bytes": 100,
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
    }
    a = {
        "passed": True,
        "probe_sha256": probe.sha(probe.canonical(p)),
        "directional_checks": 64,
        "total_solver_calls": 200,
        "numerical_passed": True,
        "charged_seconds": 11.0,
        "peak_rss_bytes": 100,
    }
    return p, a


def test_ordered_negative_cost_rule_and_conditional_amortization():
    p, _ = fixture()
    good = closure.fit_proxy(p, 52.0)
    assert good["cost_feasible"] and good["full_fit_memory_feasibility_pending"]
    expensive = copy.deepcopy(p)
    expensive["rows"][1]["timings"][0]["wall_seconds"] = 1.0
    bad = closure.fit_proxy(expensive, 52.0)
    assert not bad["cost_feasible"]
    assert all(not a["observed_acceleration"] for a in bad["conditional_amortization"])
    assert bad["additional_physics_seconds"] > good["additional_physics_seconds"]


def test_native_failed_attempts_retained_charged_and_missing_profiles_rejected(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(closure, "peak_rss", lambda: 100)
    p, a = fixture()
    directory = tmp_path / "profiles"
    directory.mkdir()
    for name, wall in (("probe", 2), ("independent", 3), ("failed_one", 4)):
        (directory / (name + ".time")).write_text(
            f"{wall}.00 real 0.10 user 0.10 sys\n100 maximum resident set size\n"
        )
    commands = [
        {
            "exit_code": 0,
            "profile": "profiles/" + name + ".time",
            "profile_sha256": probe.sha((directory / (name + ".time")).read_bytes()),
        }
        for name in ("probe", "independent")
    ]
    result = closure.close_resources(tmp_path, p, a, commands)
    assert result["charged_seconds"] == 12 + 13 + 14 + 30
    assert len(result["processes"]) == 3
    assert result["feasibility_passed"]
    a["numerical_passed"] = False
    assert "correctness" in closure.close_resources(tmp_path, p, a, commands)["next_slice"]
    commands[1]["profile"] = "../outside.time"
    with pytest.raises(ValueError):
        closure.close_resources(tmp_path, p, a, commands)


def test_malformed_or_incomplete_probe_rejected_before_independent_label_reads(tmp_path):
    p, _ = fixture()
    p["solver_calls"] = 176
    p["plan"]["steps"] = [1e-3]
    with pytest.raises(ValueError, match="complete frozen"):
        audit.audit(p, tmp_path, None, 0)
