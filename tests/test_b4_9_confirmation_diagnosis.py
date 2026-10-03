"""Diagnostic byte boundaries, fixed primary and unchanged charged failure evidence."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import b4_9_confirmation_diagnosis as diagnosis  # noqa: E402

from topolab.b3_queries import QueryAttempt, TerminalWitness  # noqa: E402
from topolab.baselines import BaselineMetrics  # noqa: E402


def test_metadata_plan_reads_no_artifacts_or_output(monkeypatch, tmp_path, capsys):  # type: ignore[no-untyped-def]
    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        pytest.fail("planning must not open experiment bytes")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    output = tmp_path / "diagnosis"
    assert (
        diagnosis.main(["--screen-root", str(tmp_path / "screen"), "--output-root", str(output)])
        == 0
    )
    assert not output.exists()
    assert '"new_solver_calls": 0' in capsys.readouterr().out
    plan = diagnosis.plan_payload()
    assert plan["plan_sha256"] == (
        "eb669182ad41bb0db4e34baa8f160218bd1fbd6289615b64afe583d44e0db46b"
    )
    assert len(set(plan["case_ids"])) == 96
    assert plan["label_and_model_byte_reads"] == plan["final_artifact_reads"] == 0
    assert plan["proposed_polish_updates"] == 20


def test_changed_receipt_rejected_before_any_unit_or_outcome(tmp_path):  # type: ignore[no-untyped-def]
    first = tmp_path / "audit_receipts/plan.json"
    first.parent.mkdir()
    first.write_bytes(b"{}")
    with pytest.raises(ValueError, match="input checksum"):
        diagnosis.input_receipts(tmp_path)


@pytest.mark.parametrize("path", diagnosis.ORIGINAL_SERIALIZATION)
def test_original_plan_and_release_serialization_is_hash_bound(tmp_path, path):  # type: ignore[no-untyped-def]
    raw = (json.dumps({"passed": True}, indent=2) + "\n").encode()
    target = tmp_path / path
    target.parent.mkdir()
    target.write_bytes(raw)
    assert diagnosis.read_bound_receipt(tmp_path, path, diagnosis.digest(raw)) == {"passed": True}
    with pytest.raises(ValueError, match="checksum"):
        diagnosis.read_bound_receipt(tmp_path, path, "0" * 64)


def test_execution_metadata_still_requires_canonical_bytes(tmp_path):  # type: ignore[no-untyped-def]
    raw = b'{\n  "passed": true\n}\n'
    (tmp_path / "context.json").write_bytes(raw)
    with pytest.raises(ValueError, match="canonical"):
        diagnosis.read_bound_receipt(tmp_path, "context.json", diagnosis.digest(raw))


@pytest.mark.parametrize("nested", [True, False])
def test_output_cannot_overlap_immutable_input(tmp_path, nested):  # type: ignore[no-untyped-def]
    root, output = (tmp_path, tmp_path / "child") if nested else (tmp_path / "child", tmp_path)
    with pytest.raises(ValueError, match="separate"):
        diagnosis.main(["--screen-root", str(root), "--output-root", str(output)])


@pytest.mark.parametrize("field", ["confirmation_gate_passed", "fixed_primary", "failures"])
def test_arithmetic_audit_rejects_changed_status_or_primary(field):  # type: ignore[no-untyped-def]
    expected = {"confirmation_gate_passed": False, "fixed_primary": 17, "failures": 1}
    actual = {**expected, field: 43}
    with pytest.raises(ValueError, match="classification"):
        diagnosis.match_numbers(actual, expected)


def test_volume_is_recomputed_without_fem(b3_reference):  # type: ignore[no-untyped-def]
    result = b3_reference.result
    volume = sum(result.physical_density) / len(result.physical_density)
    metrics = BaselineMetrics(
        iterations=len(result.history),
        final_compliance=result.compliance,
        physical_volume_error=0,
    )
    attempt = QueryAttempt(
        succeeded=True, timing={}, metrics=metrics, state=TerminalWitness.from_result(result)
    )
    assert diagnosis.checked_attempt(attempt, attempt, volume)["succeeded"]
    with pytest.raises(ValueError, match="physical-volume"):
        diagnosis.checked_attempt(attempt, attempt, volume + 0.002)


def test_next_probe_requires_physical_plateau_primary_failure():
    failed = {
        "method": "P/17",
        "candidate": {
            "succeeded": False,
            "stop": "physical_plateau",
            "quality_reasons": ["compliance_above_matched_uniform"],
        },
    }
    assert diagnosis.next_mechanism([failed]) == "fixed_20_update_post_plateau_polish_probe"
    failed["candidate"]["stop"] = "design_change"
    assert diagnosis.next_mechanism([failed]) == "terminal_basin_reliability_review"
    failed["method"] = "P/43"
    assert diagnosis.next_mechanism([failed]) == "terminal_basin_reliability_review"


def test_optimistic_bounds_preserve_observed_failure():
    rows = [
        {
            "scale": s,
            "direction": d,
            "seconds": 16,
            "uniform_seconds": 10,
            "fallback_seconds": 10,
            "candidate": {"succeeded": False},
        }
        for s in ("small", "large")
        for d in ("y", "z")
    ]
    for bound, expected in (("measured", 1.6), ("fallback_free", 0.6), ("failed_to_uniform", 1.0)):
        summary = diagnosis.diagnostic_bound(rows, bound)
        assert summary["overall_mean"] == expected
        assert summary["observed_failures"] == 4
        assert summary["diagnostic_only"] and summary["observed_statuses_preserved"]


def test_complete_gate_keeps_failed_fixed_primary_despite_two_passing_seeds():
    rows = []
    for name in diagnosis.METHODS:
        for scale in ("small", "large"):
            for direction in ("y", "z"):
                for volume in (0.5413, 0.6013):
                    for position in range(6):
                        failed = name == "P/17" and (scale, direction, volume, position) == (
                            "large",
                            "y",
                            0.5413,
                            0,
                        )
                        control_failed = (
                            name.startswith(("C/", "W/"))
                            and failed is False
                            and (scale, direction, volume, position) == ("large", "y", 0.5413, 0)
                        )
                        success = not (failed or control_failed)
                        rows.append(
                            {
                                "method": name,
                                "scale": scale,
                                "direction": direction,
                                "volume": volume,
                                "route": "generalist",
                                "seconds": 6 if name.startswith("P/") else 10,
                                "uniform_seconds": 10,
                                "candidate": {"succeeded": success},
                                "fallback": None if success else {},
                            }
                        )
    result = diagnosis.measured_decision(rows)
    assert result["passing_seeds"] == [17, 29, 43]
    assert result["fixed_primary"] == 17
    assert not result["table"]["P/17"]["primary_eligible"]
    assert not result["confirmation_gate_passed"] and not result["final_access"]
