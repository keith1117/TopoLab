"""Frozen populations, byte boundaries, independent arithmetic and full charges."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_17_independent_audit as audit  # noqa: E402
import b4_17_prepared_fem_probe as probe  # noqa: E402
import b4_17_resource_close as close  # noqa: E402

from topolab.prepared_compliance import PreparedCompliance  # noqa: E402


def fixture():
    rows, setup = [], []
    for entry in probe.plan_payload()["entries"]:
        cid = entry["case"]["case_id"]
        small = entry["case"]["problem"]["mesh"]["element_counts"][0] == 12
        for arm in ("original", "prepared"):
            setup.append(
                {
                    "case_id": cid,
                    "arm": arm,
                    "wall_seconds": 0.01,
                    "cpu_seconds": 0.009,
                    "retained_array_bytes": 100 if arm == "prepared" else None,
                }
            )
        for state in ("interior", "clipped"):
            measurements = [
                {
                    "repeat": i,
                    "arm": a,
                    "wall_seconds": 0.001 if small else 0.002,
                    "cpu_seconds": 0.001 if small else 0.002,
                }
                for i in range(3)
                for a in (("prepared", "original") if i % 2 == 0 else ("original", "prepared"))
            ]
            rows.append(
                {
                    "case_id": cid,
                    "state": state,
                    "scale": "small" if small else "large",
                    "measurements": measurements,
                    "phases": [
                        {"phase": p, "wall_seconds": 0.01, "cpu_seconds": 0.009}
                        for p in probe.PHASES
                    ],
                    "phase_total": {"wall_seconds": 0.061, "cpu_seconds": 0.055},
                    "phase_residual": {"wall_seconds": 0.001, "cpu_seconds": 0.001},
                    "differences": [
                        {"direction": d, "step": s}
                        for d in ("sine", "cosine")
                        for s in (1e-4, 2e-4)
                    ],
                }
            )
    return {
        "plan": probe.plan_payload(),
        "rows": rows,
        "setup": setup,
        "solver_calls": 240,
        "fits": 0,
        "final_access": False,
        "repaired_gate": False,
        "old_fresh_sealed": True,
        "charged_seconds": 11.0,
        "peak_rss_bytes": 100,
    }


@pytest.mark.parametrize("main", [probe.main, audit.main, close.main])
def test_metadata_plan_reads_no_artifacts_and_creates_no_output(
    main, monkeypatch, tmp_path, capsys
):
    plan = probe.plan_payload()
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("plan read artifact"))
    monkeypatch.setattr(PreparedCompliance, "evaluate", lambda *a: pytest.fail("plan solved"))
    output = tmp_path / "new"
    assert main(["--review-root", str(tmp_path / "old"), "--output-root", str(output)]) == 0
    assert json.loads(capsys.readouterr().out) == plan and not output.exists()


@pytest.mark.parametrize(
    "change",
    ["row", "repeat", "phase", "setup", "direction", "order", "time", "scale", "residual", "gate"],
)
def test_independent_complete_population_guards(change):
    source = fixture()
    if change == "row":
        source["rows"].pop()
    elif change == "repeat":
        source["rows"][0]["measurements"].pop(0)
    elif change == "phase":
        source["rows"][0]["phases"].pop()
    elif change == "setup":
        source["setup"].pop()
    elif change == "direction":
        source["rows"][0]["differences"].reverse()
    elif change == "order":
        source["rows"][0]["measurements"].reverse()
    elif change == "time":
        source["rows"][0]["measurements"][0]["wall_seconds"] = float("nan")
    elif change == "scale":
        source["rows"][0]["scale"] = "large"
    elif change == "residual":
        source["rows"][0]["phase_residual"]["wall_seconds"] = 0
    else:
        source["repaired_gate"] = True
    with pytest.raises(ValueError):
        audit.cost_basis(source)


def test_maximum_proxy_keeps_first_and_pays_setup_and_priors():
    source = fixture()
    source["rows"][0]["measurements"][0]["wall_seconds"] = 0.14
    p = close.fit_proxy(source, 85)
    expected = audit.independent_proxy(source, 85)
    for k, v in expected.items():
        assert p[k] == pytest.approx(v)
    assert p["maximum_seconds_per_scale"]["small"] == 0.14 and not p["cost_feasible"]
    assert p["full_population_preparation_seconds"] == pytest.approx(3 * 1.25 * 508 * 0.01)
    assert p["total_prospective_seconds"] == pytest.approx(
        p["additional_physics_seconds"]
        + p["full_population_preparation_seconds"]
        + 3870.204341
        + 84.33
        + 55.99
        + 85
    )
    assert close.next_slice(True, False) == probe.COST_NEXT
    assert close.next_slice(False, False) == probe.CORRECTNESS_NEXT
    assert close.next_slice(True, True) == probe.FIT_NEXT


def test_changed_prior_metadata_rejected_before_synthetic_inputs(tmp_path, monkeypatch):
    path = tmp_path / "audit_receipts/plan.json"
    path.parent.mkdir()
    path.write_bytes(b"{}\n")
    reads = []
    old = probe.read

    def observed(root, name, *args):
        reads.append(name)
        return old(root, name, *args)

    monkeypatch.setattr(probe, "read", observed)
    with pytest.raises(ValueError, match="checksum"):
        probe.check_inputs(tmp_path)
    assert reads == ["audit_receipts/plan.json"]


@pytest.mark.parametrize(
    "main,name",
    [
        (probe.main, "probe.json"),
        (audit.main, "independent_audit.json"),
        (close.main, "resource_close.json"),
    ],
)
def test_successful_result_not_overwritten_before_inputs(tmp_path, main, name):
    root = tmp_path / "b4-16-offline-adjoint-cost-review"
    output = tmp_path / "b4-17-prepared-fem-probe"
    output.mkdir()
    p = output / name
    p.write_bytes(b"keep\n")
    with pytest.raises(ValueError, match="overwrite"):
        main(["--review-root", str(root), "--output-root", str(output), "--execute"])
    assert p.read_bytes() == b"keep\n"


def test_changed_raw_rejected_before_any_fem(monkeypatch):
    source = {
        "plan": probe.original_plan(),
        "labels": [
            {"case_id": e.case.case_id, "normalizer": 2.0} for e in probe.selected_entries()
        ],
        "rows": [
            {"case_id": e.case.case_id, "state": s, "raw": probe.raw_fixture(e.case, s).tolist()}
            for e in probe.selected_entries()
            for s in ("interior", "clipped")
        ],
    }
    assert len(probe.input_states(source)) == 8
    source["rows"][0]["raw"][0] += 0.01
    monkeypatch.setattr(PreparedCompliance, "evaluate", lambda *a: pytest.fail("bad input solved"))
    with pytest.raises(ValueError, match="fixture"):
        probe.probe(source, 0)


def resource_fixture(tmp_path, monkeypatch):
    source = fixture()
    certificate = {
        "passed": True,
        "numerical_passed": True,
        "directional_checks": 64,
        "total_solver_calls": 256,
        "measurements": 96,
        "phase_observations": 96,
        "probe_sha256": probe.sha(probe.canonical(source)),
        "charged_seconds": 11,
        "peak_rss_bytes": 100,
    }
    (tmp_path / "profiles").mkdir()
    commands = []
    for name in ("probe", "independent", "failed_attempt"):
        path = tmp_path / "profiles" / (name + ".time")
        path.write_bytes(b"profile\n")
        commands.append(
            {
                "profile": "profiles/" + path.name,
                "exit_code": int(name == "failed_attempt"),
                "profile_sha256": probe.sha(path.read_bytes()),
            }
        )
    monkeypatch.setattr(close, "profile", lambda path: (1, 100))
    monkeypatch.setattr(close, "peak_rss", lambda: 100)
    return source, certificate, commands


def test_failed_attempt_retained_with_full_closure_reserve(tmp_path, monkeypatch):
    p, a, c = resource_fixture(tmp_path, monkeypatch)
    result = close.close_resources(tmp_path, p, a, c)
    assert result["charged_seconds"] == 93 and result["close_charge_seconds"] == 60
    assert len(result["processes"]) == 3 and not result["next_slice_started"]


@pytest.mark.parametrize("change", ["hash", "duplicate", "escape", "process", "whole", "rss"])
def test_close_rejects_changed_commands_or_caps(tmp_path, monkeypatch, change):
    p, a, c = resource_fixture(tmp_path, monkeypatch)
    if change == "hash":
        c[0]["profile_sha256"] = "0" * 64
    elif change == "duplicate":
        c.append(c[0])
    elif change == "escape":
        c[-1]["profile"] = "../escape.time"
    elif change == "process":
        p["charged_seconds"] = 601
        a["probe_sha256"] = probe.sha(probe.canonical(p))
    elif change == "whole":
        monkeypatch.setattr(
            close, "profile", lambda path: (1250 if path.stem == "failed_attempt" else 1, 100)
        )
    else:
        monkeypatch.setattr(close, "peak_rss", lambda: 1073741825)
    with pytest.raises(ValueError):
        close.close_resources(tmp_path, p, a, c)
