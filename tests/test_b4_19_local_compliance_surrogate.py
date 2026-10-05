"""Frozen surrogate populations, independent physics, access and paid stops."""

import copy
import sys
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_19_independent_audit as independent  # noqa: E402
import b4_19_local_compliance_surrogate as probe  # noqa: E402
import b4_19_resource_close as closure  # noqa: E402

from topolab.local_compliance import LocalCompliance  # noqa: E402
from topolab.offline_compliance import OfflineCompliance  # noqa: E402


@pytest.mark.parametrize("main", [probe.main, independent.main, closure.main])
def test_static_plan_never_reads_or_creates(monkeypatch, tmp_path, capsys, main):
    plan = probe.plan_payload()

    def forbidden(*a, **kw):
        pytest.fail("metadata plan must not read evidence or call FEM")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(LocalCompliance, "__post_init__", forbidden)
    out = tmp_path / "out"
    assert (
        main(
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
    assert len(plan["entries"]) == 8 and len(plan["states"]) == 9


@pytest.mark.parametrize(
    "main,name",
    [
        (probe.main, "probe.json"),
        (independent.main, "independent_audit.json"),
        (closure.main, "resource_close.json"),
    ],
)
def test_exclusive_outputs(tmp_path, main, name):
    out = tmp_path / "b4-19-local-compliance-surrogate"
    out.mkdir()
    target = out / name
    target.write_bytes(b"keep")
    with pytest.raises(ValueError, match="overwrite"):
        main(
            [
                "--review-root",
                str(tmp_path / "b4-18-fem-objective-method-review"),
                "--data-root",
                str(tmp_path / "b3-v1-data"),
                "--output-root",
                str(out),
                "--execute",
            ]
        )
    assert target.read_bytes() == b"keep"


def test_label_and_metadata_rejection_precedes_byte_access(monkeypatch):
    from topolab.b3_catalog import build_b3_case_catalog

    for role in ("fit_validation", "screen_validation", "final_id", "final_ood"):
        entry = next(e for e in build_b3_case_catalog().entries if e.role == role)
        with pytest.raises(ValueError, match="only frozen eight"):
            probe.train_label(Path("/unused"), None, entry)

    def reject(*a, **kw):
        raise ValueError("changed metadata")

    monkeypatch.setattr(probe, "read", reject)
    with pytest.raises(ValueError, match="metadata"):
        probe.check_inputs(Path("/unused"), Path("/unused"))


def test_independent_complete_probe_with_synthetic_uniform_anchors(monkeypatch):
    # Public train definitions, synthetic uniform designs, no dataset bytes.
    records = {}
    for entry in probe.selected_entries():
        n = int(np.prod(entry.case.problem.mesh.element_counts))
        anchor = np.full(n, entry.case.problem.optimization.volume_fraction)
        result = OfflineCompliance(entry.case, 1.0).evaluate(anchor)
        records[entry.case.case_id] = SimpleNamespace(
            stored=SimpleNamespace(
                design_density=anchor,
                physical_density=result.projection.physical,
                compliance=result.compliance,
            )
        )

    def label(data, index, entry):
        return records[entry.case.case_id], {"synthetic": entry.case.case_id}

    monkeypatch.setattr(probe, "train_label", label)
    monkeypatch.setattr(independent, "train_label", label)
    p = probe.probe(None, None, perf_counter())
    a = independent.audit(p, None, None, perf_counter())
    assert a["integrity_passed"] and a["failed_numerical_conditions"] == 0
    assert a["total_solver_calls"] == 416 and a["local_states"] == 32
    assert a["central_states"] == 72 and a["measurements"] == 216
    assert a["maximum_surrogate_directional_error"] <= 1e-4
    for changed in ("plan", "order", "anchor"):
        damaged = copy.deepcopy(p)
        if changed == "plan":
            damaged["plan"]["steps"] = [1e-3]
        elif changed == "order":
            damaged["rows"].reverse()
        else:
            damaged["labels"][0]["anchor"][0] += 1e-3
        with pytest.raises(ValueError):
            independent.audit(damaged, None, None, perf_counter())


def cost_fixture():
    p = {
        "plan": probe.plan_payload(),
        "rows": [
            {"case_id": s, "scale": s, "timings": [{"wall_seconds": v}] * 3}
            for s, v in [("small", 0.001), ("large", 0.002)]
        ],
        "setup": [
            {"case_id": s, "wall_seconds": 0.01, "retained_array_bytes": 100}
            for s in ("small", "large")
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
        "measurements": 216,
        "central_states": 72,
        "directional_rows": 64,
        "total_solver_calls": 416,
        "integrity_passed": True,
        "local_fidelity_passed": True,
        "charged_seconds": 11.0,
        "peak_rss_bytes": 100,
    }
    return p, a


def test_cost_arithmetic_first_observation_and_full_preparation():
    p, _ = cost_fixture()
    cost = closure.fit_proxy(p, 100.0)
    for key, value in independent.independent_proxy(p, 100.0).items():
        assert cost[key] == pytest.approx(value, rel=1e-12)
    assert cost["cost_feasible"] and cost["full_fit_memory_feasibility_pending"]
    p["rows"][0]["timings"][0] = {"wall_seconds": 1.0}
    assert not closure.fit_proxy(p, 100.0)["cost_feasible"]
    assert closure.next_slice(False, False, False) == probe.CORRECTNESS_NEXT
    assert closure.next_slice(True, False, True) == probe.FIDELITY_NEXT
    assert closure.next_slice(True, True, False) == probe.COST_NEXT
    assert closure.next_slice(True, True, True) == probe.FIT_NEXT


def test_fidelity_requires_all_four_criteria():
    metrics = probe.fidelity(1.0, 1.0, np.ones(3), np.ones(3))
    assert probe.local_pass(metrics)
    for key, value in [
        ("normalized_value_error", 0.000101),
        ("increment_relative_error", 0.251),
        ("gradient_relative_error", 0.251),
        ("increment_sign_agrees", False),
    ]:
        damaged = {**metrics, key: value}
        assert not probe.local_pass(damaged)
        assert independent.relative_metrics(1.0, 1.0, np.ones(3), np.ones(3)) == metrics


@pytest.mark.parametrize(
    "damage", ["none", "hash", "duplicate", "escape", "memory", "process", "whole", "gate"]
)
def test_complete_native_failure_charge_and_cap_rejections(tmp_path, monkeypatch, damage):
    p, a = cost_fixture()
    profiles = tmp_path / "profiles"
    profiles.mkdir()
    commands = []
    for name in ("probe", "independent", "failed_attempt"):
        path = profiles / (name + ".time")
        path.write_text("2.00 real 0.10 user 0.10 sys\n100 maximum resident set size\n")
        commands.append(
            {
                "profile": "profiles/" + path.name,
                "exit_code": int(name == "failed_attempt"),
                "profile_sha256": probe.sha(path.read_bytes()),
            }
        )
    monkeypatch.setattr(closure, "peak_rss", lambda: 100)
    if damage == "hash":
        commands[0]["profile_sha256"] = "0" * 64
    elif damage == "duplicate":
        commands.append(commands[0])
    elif damage == "escape":
        commands[-1]["profile"] = "../outside.time"
    elif damage == "memory":
        monkeypatch.setattr(closure, "peak_rss", lambda: 1073741825)
    elif damage == "process":
        a["charged_seconds"] = 601
    elif damage == "whole":
        monkeypatch.setattr(
            closure, "profile", lambda p: (1200 if p.stem == "failed_attempt" else 2, 100)
        )
    elif damage == "gate":
        p["repaired_gate"] = True
        a["probe_sha256"] = probe.sha(probe.canonical(p))
    if damage == "none":
        r = closure.close_resources(tmp_path, p, a, commands)
        assert r["charged_seconds"] == 96 and r["feasibility_passed"]
    else:
        with pytest.raises(ValueError):
            closure.close_resources(tmp_path, p, a, commands)
