"""Keep B4.24 historical unknowns and enforce owner-approved continuation caps."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_24_registered_continuation as continuation  # noqa: E402
from test_b4_24_saved_schema_recovery import actual_schema  # noqa: E402
from test_b4_24_versioned_correctness_failure_review import fixture, resource_fixture  # noqa: E402


def history_fixture():
    return (
        {
            "closed": False,
            "resource_proof_complete": False,
            "peak_rss_bytes": None,
            "planning_child_exit_code": None,
            "native_profiles": {"recovery-plan": {"rss_bytes": None}},
            "time_charge_seconds": 76.19,
            "paid_reservation_seconds": 60,
            "failed_review_charge_seconds": 16.19,
            "failed_native_processes": 2,
            "registered_recovery_review_attempts": 0,
            "arithmetic_audit_attempts": 0,
        },
        {"passed": True, "resource_proof_complete": False, "combined_reserved_use_seconds": 50.53},
        [
            {"name": "plan", "exit_code": 0},
            {"name": "review", "exit_code": 1},
            {"name": "recovery-plan", "exit_code": 1},
        ],
    )


def test_plan_preserves_population_and_unknowns_without_artifact_access(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("artifact access"))
    output = tmp_path / "absent"
    assert (
        continuation.main(
            [
                "--mode",
                "plan",
                "--probe-root",
                str(tmp_path / "probe"),
                "--prior-review-root",
                str(tmp_path / "prior"),
                "--output-root",
                str(output),
            ]
        )
        == 0
    )
    value = json.loads(capsys.readouterr().out)
    assert value == continuation.plan_payload() and not output.exists()
    assert value["max_seconds"] == 240 and value["total_paid_reservation_seconds"] == 120
    assert value["maximum_new_review_charge_seconds"] == 43.81
    assert value["historical_whole_peak_rss_bytes"] is None
    assert value["scalar_conditions"] == 2104 and value["independent_scalar_conditions"] == 1728
    assert value["original_mask_failures"] == 35 and value["original_fd_failures"] == 34
    assert value["solver_calls"] == value["new_projection_calls"] == 0


def test_frozen_arithmetic_and_separate_auditor_preserve_complete_panel(monkeypatch):
    panel, prior, closed = fixture(monkeypatch)
    panel = actual_schema(panel)
    before = continuation.original.canonical(panel)
    report = continuation.review(panel, prior, closed)
    monkeypatch.setattr(
        continuation.recovery, "candidate_schema", lambda *a: pytest.fail("candidate adapter")
    )
    result = continuation.audit(panel, prior, closed, report)
    assert result["passed"] and result["independent_scalar_conditions"] == 1728
    assert report["scalar_conditions"] == 2104 and len(report["rows"]) == 64
    assert not report["original_correctness_gate_passed"]
    assert continuation.original.canonical(panel) == before
    assert result["review_sha256"] == continuation.original.sha(
        continuation.original.canonical(report)
    )
    report["plan"]["total_paid_reservation_seconds"] = 60
    with pytest.raises(ValueError, match="boundary"):
        continuation.audit(panel, prior, closed, report)


@pytest.mark.parametrize(
    "field,value",
    [
        ("peak_rss_bytes", 482017280),
        ("planning_child_exit_code", 0),
        ("time_charge_seconds", 0),
        ("paid_reservation_seconds", 120),
        ("failed_native_processes", 1),
        ("registered_recovery_review_attempts", 1),
    ],
)
def test_historical_memory_or_charges_cannot_be_repaired_or_reset(field, value):
    partial, reserve, commands = history_fixture()
    continuation.validate_history(partial, reserve, commands)
    partial[field] = value
    with pytest.raises(ValueError, match="historical"):
        continuation.validate_history(partial, reserve, commands)


def test_exact_standard_json_metadata_bytes_remain_unchanged(tmp_path, monkeypatch):
    name = "resource_close_incomplete.json"
    raw = (json.dumps(history_fixture()[0], sort_keys=True) + "\n").encode()
    assert raw != continuation.original.canonical(history_fixture()[0])
    (tmp_path / name).write_bytes(raw)
    monkeypatch.setattr(continuation, "HISTORY_BINDINGS", {name: continuation.original.sha(raw)})
    assert continuation.history_metadata(tmp_path, name) == history_fixture()[0]
    assert (tmp_path / name).read_bytes() == raw
    (tmp_path / name).write_bytes(continuation.original.canonical(history_fixture()[0]))
    with pytest.raises(ValueError):
        continuation.history_metadata(tmp_path, name)


def new_resource_fixture(tmp_path, monkeypatch):
    commands, report, result = resource_fixture(tmp_path, monkeypatch)
    report["plan"] = continuation.plan_payload()
    report["registered_continuation"] = True
    result["review_sha256"] = continuation.original.sha(continuation.original.canonical(report))
    monkeypatch.setattr(
        continuation,
        "native_profile",
        lambda p: {
            "wall_seconds": 1.0,
            "user_seconds": 0.5,
            "system_seconds": 0.1,
            "rss_bytes": 100,
        },
    )
    return commands, report, result


def test_both_full_reserves_and_failure_are_paid_with_scoped_memory(tmp_path, monkeypatch):
    commands, report, audit = new_resource_fixture(tmp_path, monkeypatch)
    value = continuation.close_resources(tmp_path, commands, report, audit)
    assert value["charged_seconds"] == 158.19 and value["paid_reservation_seconds"] == 120
    assert value["historical_time_charge_seconds"] == 76.19
    assert value["cumulative_review_charge_seconds"] == 27.19
    assert value["historical_failed_native_processes"] == 2
    assert value["whole_slice_peak_rss_bytes"] is None
    assert value["whole_slice_memory_compliance"] is None
    assert not value["historical_resource_proof_complete"]
    report["charged_seconds"] = 43.81
    audit["charged_seconds"] = 60
    audit["review_sha256"] = continuation.original.sha(continuation.original.canonical(report))
    assert continuation.close_resources(tmp_path, commands, report, audit)["charged_seconds"] == 240
    commands[-1]["exit_code"] = 1
    failed = continuation.close_resources(tmp_path, commands, report, None)
    assert failed["continuation_failed_processes"] == 1 and not failed["full_panel_review_complete"]
    assert failed["next_slice"] == continuation.original.EVIDENCE_NEXT


@pytest.mark.parametrize(
    "change", ["duplicate", "reviewcap", "auditcap", "rss", "hash", "escape", "gate"]
)
def test_registered_resource_guards_reject_invalid_closure(tmp_path, monkeypatch, change):
    commands, report, result = new_resource_fixture(tmp_path, monkeypatch)
    if change == "duplicate":
        commands.append(copy.deepcopy(commands[1]))
    elif change == "reviewcap":
        report["charged_seconds"] = 43.82
        result["review_sha256"] = continuation.original.sha(continuation.original.canonical(report))
    elif change == "auditcap":
        result["charged_seconds"] = 60.01
    elif change == "rss":
        monkeypatch.setattr(
            continuation,
            "native_profile",
            lambda p: {
                "wall_seconds": 1,
                "user_seconds": 0,
                "system_seconds": 0,
                "rss_bytes": 1073741825,
            },
        )
    elif change == "hash":
        commands[1]["log_sha256"] = "0" * 64
    elif change == "escape":
        commands[1]["profile"] = "../other.time"
    else:
        report["repaired_gate"] = True
        result["review_sha256"] = continuation.original.sha(continuation.original.canonical(report))
    with pytest.raises(ValueError):
        continuation.close_resources(tmp_path, commands, report, result)


@pytest.mark.parametrize(
    "mode,name",
    [
        ("review", "review.json"),
        ("audit", "independent_audit.json"),
        ("close", "resource_close.json"),
        ("verify", "resource_verification.json"),
    ],
)
def test_exclusive_outputs_refuse_repeat_before_source_or_evidence_read(
    tmp_path, monkeypatch, mode, name
):
    output = tmp_path / "b4-24-registered-continuation-v3"
    output.mkdir()
    (output / name).write_bytes(b"retain")
    monkeypatch.setattr(
        continuation.original, "execution_release", lambda *a: pytest.fail("source/evidence read")
    )
    with pytest.raises(ValueError, match="overwrite"):
        continuation.main(
            [
                "--mode",
                mode,
                "--probe-root",
                str(tmp_path / "b4-23-versioned-surrogate-feasibility"),
                "--prior-review-root",
                str(tmp_path / "b4-24-versioned-correctness-failure-review"),
                "--output-root",
                str(output),
                "--execute",
            ]
        )
    assert (output / name).read_bytes() == b"retain"


def test_future_native_profile_requires_all_cpu_and_memory_fields(tmp_path):
    path = tmp_path / "native.time"
    path.write_text(
        "4.73 real 1.95 user 0.40 sys\ntime: sysctl kern.clockrate: Operation not permitted\n"
    )
    with pytest.raises(ValueError, match="complete native"):
        continuation.native_profile(path)
    path.write_text("4.73 real 1.95 user 0.40 sys\n274432000 maximum resident set size\n")
    assert continuation.native_profile(path) == {
        "wall_seconds": 4.73,
        "user_seconds": 1.95,
        "system_seconds": 0.40,
        "rss_bytes": 274432000,
    }
