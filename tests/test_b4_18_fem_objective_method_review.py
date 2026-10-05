"""Read-only populations, phase arithmetic, independent mutations and paid closure."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_18_fem_objective_method_review as review  # noqa: E402
import b4_18_independent_audit as independent  # noqa: E402
import b4_18_resource_close as closure  # noqa: E402


def fixture():
    plan = review.prior_plan()
    rows, setup = [], []
    for entry in plan["entries"]:
        cid = entry["case"]["case_id"]
        scale = "small" if entry["case"]["problem"]["mesh"]["element_counts"][0] == 12 else "large"
        for arm in ("original", "prepared"):
            setup.append(
                {
                    "case_id": cid,
                    "arm": arm,
                    "wall_seconds": 0.1,
                    "cpu_seconds": 0.09,
                    "retained_array_bytes": 100 if arm == "prepared" else None,
                }
            )
        for state in plan["states"]:
            measurements = []
            for i in range(3):
                for arm in ("prepared", "original") if i % 2 == 0 else ("original", "prepared"):
                    measurements.append(
                        {
                            "repeat": i,
                            "arm": arm,
                            "wall_seconds": 0.01 if scale == "small" else 0.2,
                            "cpu_seconds": 0.009 if scale == "small" else 0.19,
                        }
                    )
            phases = [
                {
                    "phase": p,
                    "wall_seconds": 0.001 if p != "factorization" else 0.1,
                    "cpu_seconds": 0.0009 if p != "factorization" else 0.09,
                }
                for p in plan["phases"]
            ]
            rows.append(
                {
                    "case_id": cid,
                    "state": state,
                    "scale": scale,
                    "measurements": measurements,
                    "phases": phases,
                    "phase_total": {"wall_seconds": 0.106, "cpu_seconds": 0.0955},
                    "phase_residual": {"wall_seconds": 0.001, "cpu_seconds": 0.001},
                }
            )
    rows[0]["measurements"][0]["wall_seconds"] = 0.14
    prepare = 3.75 * 508 * 0.1
    physics = 750 * (432 * 0.14 + 76 * 0.2)
    closed = {
        "charged_seconds": 112.34,
        "peak_rss_bytes": 300,
        "fit_proxy": {
            "additional_physics_seconds": physics,
            "total_prospective_seconds": physics + prepare + 3870.204341 + 84.33 + 55.99 + 112.34,
            "population_retained_array_bytes_estimate": 50800,
        },
    }
    return {"plan": plan, "rows": rows, "setup": setup}, closed


def test_metadata_plan_has_no_reads_or_outputs(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("artifact read"))
    output = tmp_path / "absent"
    assert review.main(["--probe-root", str(tmp_path / "prior"), "--output-root", str(output)]) == 0
    assert not output.exists()
    assert json.loads(capsys.readouterr().out) == review.plan_payload()


def test_complete_first_observation_phases_original_gate_and_next():
    probe, closed = fixture()
    report = review.review(probe, closed)
    assert len(report["observations"]) == 96
    assert report["scenarios"]["prepared_maximum"]["unit_seconds"] == [0.14, 0.2]
    assert report["next_slice"] == review.SURROGATE_NEXT
    assert report["phase_attribution"]["large"]["wall_seconds"][
        "factorization_share"
    ] == pytest.approx(0.1 / 0.106)
    assert report["scenarios"]["zero_factorization_instrumented"]["unit_seconds"] == pytest.approx(
        [0.006, 0.006]
    )
    assert not report["original_cost_gate_passed"] and report["solver_calls"] == 0
    audit = independent.reconstruct(probe, closed, report)
    assert audit["passed"] and audit["phase_intervals"] == 96
    assert audit["method_dispositions"] == 6


@pytest.mark.parametrize(
    "change",
    [
        "drop",
        "duplicate",
        "order",
        "repeat",
        "scale",
        "phase",
        "phase_total",
        "residual",
        "nan",
        "negative",
        "setup",
        "bytes",
        "proxy",
        "memory",
    ],
)
def test_population_and_original_arithmetic_guards(change):
    probe, closed = fixture()
    row = probe["rows"][0]
    if change == "drop":
        probe["rows"].pop()
    elif change == "duplicate":
        probe["rows"][1] = copy.deepcopy(row)
    elif change == "order":
        probe["rows"].reverse()
    elif change == "repeat":
        row["measurements"].pop(0)
    elif change == "scale":
        row["scale"] = "large"
    elif change == "phase":
        row["phases"].reverse()
    elif change == "phase_total":
        row["phase_total"]["wall_seconds"] = 0.01
    elif change == "residual":
        row["phase_residual"]["cpu_seconds"] = 0.5
    elif change in ("nan", "negative"):
        row["measurements"][0]["wall_seconds"] = float("nan") if change == "nan" else -1
    elif change == "setup":
        probe["setup"].reverse()
    elif change == "bytes":
        probe["setup"][1]["retained_array_bytes"] = -1
    elif change == "proxy":
        closed["fit_proxy"]["additional_physics_seconds"] += 1
    else:
        closed["fit_proxy"]["population_retained_array_bytes_estimate"] += 1
    with pytest.raises(ValueError):
        review.review(probe, closed)


@pytest.mark.parametrize(
    "field",
    [
        "scenarios",
        "phase_attribution",
        "observations",
        "method_dispositions",
        "memory",
        "next_slice",
        "original_cost_gate_passed",
    ],
)
def test_separate_auditor_detects_modified_report(field):
    probe, closed = fixture()
    report = review.review(probe, closed)
    if field == "scenarios":
        report[field]["zero_small"]["total_prospective_seconds"] += 1
    elif field == "phase_attribution":
        report[field]["large"]["wall_seconds"]["factorization_share"] -= 0.1
    elif field == "observations":
        report[field].pop(0)
    elif field == "method_dispositions":
        report[field] = {**report[field], "new_fit": "allowed"}
    elif field == "memory":
        report[field]["full_fit_feasibility_pending"] = False
    elif field == "next_slice":
        report[field] = "B5"
    else:
        report[field] = True
    with pytest.raises(ValueError):
        independent.reconstruct(probe, closed, report)


def test_ordered_exact_method_branch_with_low_factor_share():
    probe, closed = fixture()
    for row in probe["rows"]:
        row["phases"][3].update(wall_seconds=0.001, cpu_seconds=0.0009)
        row["phase_total"].update(wall_seconds=0.007, cpu_seconds=0.0064)
    report = review.review(probe, closed)
    assert report["next_slice"] == review.SOLVER_NEXT
    assert independent.reconstruct(probe, closed, report)["next_slice"] == review.SOLVER_NEXT


@pytest.mark.parametrize(
    "main,name",
    [
        (review.main, "review.json"),
        (independent.main, "independent_audit.json"),
        (closure.main, "resource_close.json"),
    ],
)
def test_exclusive_successful_result_creation(tmp_path, main, name):
    root, output = (
        tmp_path / "b4-17-prepared-fem-probe",
        tmp_path / "b4-18-fem-objective-method-review",
    )
    output.mkdir()
    target = output / name
    target.write_bytes(b"keep\n")
    with pytest.raises(ValueError, match="overwrite"):
        main(["--probe-root", str(root), "--output-root", str(output), "--execute"])
    assert target.read_bytes() == b"keep\n"


def test_closed_metadata_failure_precedes_probe_bytes(monkeypatch):
    opened = []

    def reject(root, name, digest):
        opened.append(name)
        raise ValueError("metadata changed")

    monkeypatch.setattr(review, "read", reject)
    with pytest.raises(ValueError, match="metadata"):
        review.check_inputs(Path("/external/prior"))
    assert opened == ["audit_receipts/plan.json"]


def resource_fixture(tmp_path, monkeypatch):
    probe, prior = fixture()
    report = review.review(probe, prior)
    report.update(charged_seconds=10.1, peak_rss_bytes=100)
    audit = independent.reconstruct(probe, prior, report)
    audit.update(
        review_sha256=review.sha(review.canonical(report)), charged_seconds=10.2, peak_rss_bytes=200
    )
    (tmp_path / "profiles").mkdir()
    commands = []
    for name in ("review", "independent", "failed_attempt"):
        path = tmp_path / "profiles" / (name + ".time")
        path.write_bytes(b"synthetic\n")
        commands.append(
            {
                "profile": "profiles/" + path.name,
                "exit_code": int(name == "failed_attempt"),
                "profile_sha256": review.sha(path.read_bytes()),
            }
        )
    monkeypatch.setattr(closure, "profile", lambda p: (1.0, 300))
    monkeypatch.setattr(closure, "peak_rss", lambda: 250)
    return report, audit, commands


def test_failed_attempt_and_whole_reservation_paid(tmp_path, monkeypatch):
    report, audit, commands = resource_fixture(tmp_path, monkeypatch)
    result = closure.close_resources(tmp_path, report, audit, commands)
    assert result["charged_seconds"] == 93
    assert result["close_charge_seconds"] == 60
    assert not result["original_cost_gate_passed"]


@pytest.mark.parametrize("change", ["hash", "duplicate", "escape", "gate", "cost", "whole", "rss"])
def test_closure_rejects_hash_gate_population_and_cap_mutations(tmp_path, monkeypatch, change):
    report, audit, commands = resource_fixture(tmp_path, monkeypatch)
    if change == "hash":
        commands[0]["profile_sha256"] = "0" * 64
    elif change == "duplicate":
        commands.append(commands[0])
    elif change == "escape":
        commands[-1]["profile"] = "../outside.time"
    elif change == "gate":
        report["repaired_gate"] = True
        audit["review_sha256"] = review.sha(review.canonical(report))
    elif change == "cost":
        audit["charged_seconds"] = 61
    elif change == "whole":
        monkeypatch.setattr(
            closure, "profile", lambda p: (200 if p.stem == "failed_attempt" else 1, 300)
        )
    else:
        monkeypatch.setattr(closure, "peak_rss", lambda: 1073741825)
    with pytest.raises(ValueError):
        closure.close_resources(tmp_path, report, audit, commands)
