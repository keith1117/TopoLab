"""Actual producer schema, independent adaptation and cumulative failed charges."""

import ast
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_24_saved_schema_recovery as recovery  # noqa: E402
from test_b4_24_versioned_correctness_failure_review import fixture, resource_fixture  # noqa: E402


def actual_schema(panel):
    value = copy.deepcopy(panel)
    for row in value["rows"]:
        for item in row["differences"]:
            for key in ("fd", "derivative", "error"):
                item["surrogate_" + key] = item.pop(key)
    return value


def test_schema_matches_actual_b4_23_writer_and_preserves_every_value(monkeypatch):
    producer = (
        Path(__file__).resolve().parents[1] / "scripts/b4_23_versioned_surrogate_feasibility.py"
    )
    tree = ast.parse(producer.read_text())
    keys = next(
        {k.value for k in node.value.keys}
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id == "diff" for t in node.targets)
        and isinstance(node.value, ast.Dict)
    )
    assert {"surrogate_fd", "surrogate_derivative", "surrogate_error"} <= keys
    assert not {"fd", "derivative", "error"} & keys
    panel, prior, closed = fixture(monkeypatch)
    actual = actual_schema(panel)
    before = recovery.original.canonical(actual)
    assert recovery.candidate_schema(actual) == {
        **panel,
        "rows": [
            {
                **row,
                "differences": [
                    {
                        **item,
                        "surrogate_fd": item["fd"],
                        "surrogate_derivative": item["derivative"],
                        "surrogate_error": item["error"],
                    }
                    for item in row["differences"]
                ],
            }
            for row in panel["rows"]
        ],
    }
    report = recovery.review(actual, prior, closed)
    result = recovery.audit(actual, prior, closed, report)
    assert report["scalar_conditions"] == 2104 and result["independent_scalar_conditions"] == 1728
    assert report["first_failed_review_charge_seconds"] == 16.19 and result["passed"]
    assert not report["original_correctness_gate_passed"]
    assert recovery.original.canonical(actual) == before
    monkeypatch.setattr(recovery, "candidate_schema", lambda *a: pytest.fail("shared adapter"))
    assert recovery.audit(actual, prior, closed, report)["passed"]


def test_ambiguous_schema_is_rejected(monkeypatch):
    panel, _, _ = fixture(monkeypatch)
    with pytest.raises(ValueError, match="ambiguous"):
        recovery.candidate_schema(panel)


def test_plan_has_no_artifact_read_or_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("artifact read"))
    output = tmp_path / "absent"
    assert (
        recovery.main(
            [
                "--mode",
                "plan",
                "--probe-root",
                str(tmp_path / "prior"),
                "--output-root",
                str(output),
            ]
        )
        == 0
    )
    plan = json.loads(capsys.readouterr().out)
    assert plan == recovery.plan_payload() and plan["max_seconds"] == 240
    assert plan["process_seconds"] == 60 and plan["stage_caps_are_cumulative"]
    assert not output.exists()


def test_cumulative_cost_retains_failed_attempt_and_full_reserve(tmp_path, monkeypatch):
    commands, report, result = resource_fixture(tmp_path, monkeypatch)
    report["plan"] = recovery.plan_payload()
    result["review_sha256"] = recovery.original.sha(recovery.original.canonical(report))
    failed = copy.deepcopy(commands[1])
    failed["exit_code"] = 1
    recovered = copy.deepcopy(commands[1])
    recovered["name"] = "review-recovery"
    recovered["profile"] = "profiles/review-recovery.time"
    recovered["log"] = "logs/review-recovery.log"
    plan = copy.deepcopy(commands[0])
    plan["name"] = "recovery-plan"
    plan["profile"] = "profiles/recovery-plan.time"
    plan["log"] = "logs/recovery-plan.log"
    for c in (recovered, plan):
        (tmp_path / c["profile"]).write_bytes(b"synthetic\n")
        (tmp_path / c["log"]).write_bytes(b"synthetic\n")
    ordered = [commands[0], failed, plan, recovered, commands[2]]
    monkeypatch.setattr(recovery.original, "peak_rss", lambda: 100)
    monkeypatch.setattr(
        recovery, "profile", lambda p: (6.19 if p.name == "review.time" else 1, 100)
    )
    closed = recovery.close_resources(tmp_path, ordered, report, result)
    assert closed["charged_seconds"] == 98.19 and closed["failed_attempts"] == 1
    assert closed["cumulative_stage_charges"]["review"] == 27.19
    report["charged_seconds"] = 50
    result["review_sha256"] = recovery.original.sha(recovery.original.canonical(report))
    with pytest.raises(ValueError, match="cumulative"):
        recovery.close_resources(tmp_path, ordered, report, result)
