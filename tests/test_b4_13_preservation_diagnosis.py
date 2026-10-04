"""B4.13 zero-read planning, immutable evidence and residual quality mechanism."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import b4_13_independent_audit as independent  # noqa: E402
import b4_13_preservation_diagnosis as diagnosis  # noqa: E402
from test_b4_11_polish_diagnosis import witness  # noqa: E402


def residual():
    return {
        "method": "P/17",
        "triggered": True,
        "selection": "endpoint",
        "added_updates": 20,
        "candidate": {
            "succeeded": False,
            "converged": True,
            "quality_reasons": ["compliance_above_matched_uniform"],
        },
        "before": {"succeeded": False, "compliance_ratio": 1.003},
        "endpoint": {
            "converged": True,
            "compliance_ratio": 1.002,
            "quality_reasons": ["compliance_above_matched_uniform"],
        },
    }


def test_planning_reads_no_bytes_creates_nothing_and_binds_both_complete_panels(
    monkeypatch, tmp_path, capsys
):
    def forbidden(*a, **k):
        pytest.fail("metadata plan must not read experiment bytes")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    output = tmp_path / "output"
    assert (
        diagnosis.main(["--screen-root", str(tmp_path / "screen"), "--output-root", str(output)])
        == 0
    )
    assert not output.exists()
    plan = json.loads(capsys.readouterr().out)
    assert plan == diagnosis.plan_payload()
    assert plan["plan_sha256"] == independent.PLAN_SHA
    assert len(plan["bindings"]) == 30
    assert plan["cohorts"]["fresh"] == [48, 576, 922, 135, 26, 0]
    assert plan["old_fresh_cases_sealed"] == 48
    assert not plan["length_or_threshold_search"]


@pytest.mark.parametrize(
    "reader,error", [(diagnosis.read, ValueError), (independent.read, AssertionError)]
)
def test_symlink_escape_rejected_before_bytes(reader, error, tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    forbidden = tmp_path / "secret.json"
    forbidden.write_bytes(b"{}\n")
    (root / "link.json").symlink_to(forbidden)
    with pytest.raises(error, match="escape"):
        reader(root, "link.json")


def test_changed_metadata_stops_before_journal_reads(tmp_path, monkeypatch):
    path = tmp_path / "audit_receipts/plan.json"
    path.parent.mkdir()
    path.write_bytes(b"{}\n")
    with pytest.raises(ValueError, match="checksum"):
        diagnosis.check_inputs(tmp_path)


@pytest.mark.parametrize("nested", [True, False])
def test_output_never_overlaps_historical_input(tmp_path, nested):
    root, output = (tmp_path, tmp_path / "child") if nested else (tmp_path / "child", tmp_path)
    with pytest.raises(ValueError, match="separate"):
        diagnosis.main(["--screen-root", str(root), "--output-root", str(output)])


def test_converged_plateau_endpoint_can_still_fail_reference_quality():
    state = witness(count=60, gain=0.00019, converged=True)
    a = diagnosis.terminal(state, 99.7, 0.47, True)
    b = independent.certificate(state, 99.7, 0.47, True)
    independent.close(a, b)
    assert a["converged"] and a["plateau_certificate"]
    assert a["quality_reasons"] == ["compliance_above_matched_uniform"]
    assert not a["succeeded"] and a["iterations"] < 360


@pytest.mark.parametrize(
    "change", ["seed", "selection", "updates", "cause", "before", "improvement", "trigger"]
)
def test_method_advice_requires_residual_quality_gap_and_retains_fixed_primary(change):
    row = residual()
    assert diagnosis.advice([row]) == "generalist_reliability_refinement_method_review"
    if change == "seed":
        row["method"] = "P/43"
    elif change == "selection":
        row["selection"] = "original"
    elif change == "updates":
        row["added_updates"] = 19
    elif change == "cause":
        row["candidate"]["quality_reasons"] = ["not_converged"]
        row["endpoint"]["quality_reasons"] = ["not_converged"]
    elif change == "before":
        row["before"]["succeeded"] = True
    elif change == "improvement":
        row["endpoint"]["compliance_ratio"] = 1.004
    else:
        row["triggered"] = False
    assert diagnosis.advice([row]) == "terminal_certificate_and_cost_method_review"
    assert diagnosis.advice([row]) == independent.recommendation([row])


def test_full_paid_cost_bounds_never_erase_failure_or_recording():
    row = {
        "seconds": 16.0,
        "uniform_seconds": 10.0,
        "fallback_seconds": 9.0,
        "candidate": {"succeeded": False},
    }
    original = copy.deepcopy(row)
    for scenario, ratio in [("measured", 1.6), ("fallback_free", 0.7), ("failed_to_uniform", 1.0)]:
        d = diagnosis.costs([row], scenario)
        assert d["mean_paired_ratio"] == ratio and d["observed_failures"] == 1
        assert d["observed_statuses_preserved"]
        independent.close(d, independent.costs([row], scenario))
    assert row == original


def test_journal_membership_mismatch_rejected_before_unit_reads(tmp_path):
    path = tmp_path / "fresh/reference"
    path.mkdir(parents=True)
    progress = {
        "context_sha256": "context",
        "units_sha256": diagnosis.sha(diagnosis.canonical(["case"])),
    }
    for name in ("progress", "summary"):
        (path / (name + ".json")).write_bytes(diagnosis.canonical(progress))
    with pytest.raises(ValueError, match="journal"):
        diagnosis.chain(tmp_path, "fresh/reference", ["forbidden"], "context")
    with pytest.raises(AssertionError):
        independent.journal(tmp_path, "fresh/reference", ["forbidden"], "context")


def test_content_address_and_size_are_checked_before_arithmetic(tmp_path):
    with pytest.raises(ValueError, match="content-addressed"):
        diagnosis.blob(
            tmp_path, "fresh/screen", {"sha256": "0" * 64, "path": "elsewhere"}, "outcome"
        )
    with pytest.raises(AssertionError):
        independent.artifact(
            tmp_path, "fresh/screen", {"sha256": "0" * 64, "path": "elsewhere"}, "outcome"
        )


def test_timing_includes_fallback_but_never_double_counts_inclusive_callback():
    packet = {
        "outcome": {
            "attempt": {"timing": {"refinement_seconds": 5.0}},
            "fallback": {"timing": {"refinement_seconds": 10.0}},
            "route_seconds": 0.1,
        },
        "timing": {"wall_seconds": 15.2, "cpu_seconds": 14.0, "legacy_phase_seconds": 15.1},
        "callback": {"wall_seconds": 1.0, "cpu_seconds": 0.8, "bytes_written": 100},
        "recording_allowance_seconds": 1,
    }
    diagnosis.timing(packet)
    changed = copy.deepcopy(packet)
    changed["timing"]["legacy_phase_seconds"] = 5.1
    with pytest.raises(ValueError, match="timing"):
        diagnosis.timing(changed)
    changed = copy.deepcopy(packet)
    changed["callback"]["wall_seconds"] = 16.0
    with pytest.raises(ValueError, match="timing"):
        diagnosis.timing(changed)


def test_independent_comparison_rejects_relabelled_failure_and_changed_performed_work():
    for field, value in [("succeeded", True), ("performed_iterations", 40)]:
        original = {"succeeded": False, "performed_iterations": 60}
        changed = {**original, field: value}
        with pytest.raises(AssertionError):
            independent.close(original, changed)


@pytest.fixture
def closure_fixture(tmp_path, monkeypatch):
    import b4_13_resource_close as closer

    root = tmp_path / "b4-12-terminal-preservation"
    output = tmp_path / "b4-13-preservation-diagnosis"
    (output / "profiles").mkdir(parents=True)
    source = Path(__file__).resolve().parents[1]
    paths = [
        "scripts/b4_13_preservation_diagnosis.py",
        "scripts/b4_13_independent_audit.py",
        "scripts/b4_13_resource_close.py",
        "docs/planning/b4_13_preservation_diagnosis_protocol.md",
    ]
    hashes = {p: diagnosis.sha((source / p).read_bytes()) for p in paths}

    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(diagnosis.canonical(value))

    report = {
        "plan": diagnosis.plan_payload(),
        "diagnostic_source_revision": "merged",
        "source_sha256": hashes[paths[0]],
        "protocol_sha256": hashes[paths[3]],
        "old_fresh_sealed": True,
        "final_access": False,
        "repaired_gate": False,
        "next_mechanism": "generalist_reliability_refinement_method_review",
        "charged_seconds": 10.0,
        "peak_rss_bytes": 1024,
        "cohorts": {
            "sentinel": {"scientific_decision": {"sentinel_gate_passed": True}},
            "fresh": {"scientific_decision": {"development_gate_passed": False}},
        },
    }
    write(output / "diagnosis.json", report)
    write(
        output / "independent_audit.json",
        {
            "passed": True,
            "diagnosis_sha256": diagnosis.sha(diagnosis.canonical(report)),
            "source_sha256": hashes[paths[1]],
            "next_mechanism": report["next_mechanism"],
            "charged_seconds": 10.0,
            "peak_rss_bytes": 1024,
        },
    )
    write(
        output / "audit_receipts/production_release.json",
        {
            "source_revision": "merged",
            "all_applicable_ci_passed_before_merge": True,
            "source_sha256": hashes,
        },
    )
    for name in ("diagnosis", "independent", "failed_preflight"):
        (output / f"profiles/{name}.time").write_text("0.10 real\n1024 maximum resident set size\n")
    write(
        output / "audit_receipts/execution_commands.json",
        [
            {"exit_code": 0, "profile": "profiles/diagnosis.time"},
            {"exit_code": 0, "profile": "profiles/independent.time"},
            {"exit_code": 1, "profile": "profiles/failed_preflight.time"},
        ],
    )
    monkeypatch.setattr(
        closer, "check_inputs", lambda *a: {"resource_close.json": {"charged_seconds": 8486.6}}
    )
    monkeypatch.setattr(closer, "peak_rss", lambda: 1024)
    return closer, root, output, write


def test_resource_closure_pays_failed_commands_reserves_full_close_and_is_immutable(
    closure_fixture,
):
    closer, root, output, _ = closure_fixture
    args = ["--screen-root", str(root), "--output-root", str(output)]
    assert closer.main(args) == 0
    closed = diagnosis.read(output, "resource_close.json")
    assert closed["diagnostic_acceptance_passed"] and not closed["repaired_gate"]
    assert closed["close_charge_seconds"] == 30
    assert closed["charged_seconds"] == pytest.approx(60.3)
    assert closed["prior_b4_12_charge_seconds_unchanged"] == 8486.6
    assert len(closed["processes"]) == 3
    assert closed["next_slice"].startswith("B4.14")
    with pytest.raises(AssertionError, match="overwrite"):
        closer.main(args)


@pytest.mark.parametrize("change", ["hash", "gate", "escape", "resource"])
def test_resource_closure_rejects_tamper_escape_or_exceeded_cap(closure_fixture, change):
    closer, root, output, write = closure_fixture
    if change in ("hash", "gate"):
        report = diagnosis.read(output, "diagnosis.json")
        report["repaired_gate"] = True
        write(output / "diagnosis.json", report)
        if change == "gate":
            audit = diagnosis.read(output, "independent_audit.json")
            audit["diagnosis_sha256"] = diagnosis.sha(diagnosis.canonical(report))
            write(output / "independent_audit.json", audit)
    elif change == "escape":
        write(
            output / "audit_receipts/execution_commands.json",
            [
                {"exit_code": 0, "profile": "profiles/diagnosis.time"},
                {"exit_code": 1, "profile": "../elsewhere.time"},
            ],
        )
    else:
        (output / "profiles/diagnosis.time").write_text(
            "111 real\n1024 maximum resident set size\n"
        )
    with pytest.raises(AssertionError):
        closer.main(["--screen-root", str(root), "--output-root", str(output)])
    assert not (output / "resource_close.json").exists()
