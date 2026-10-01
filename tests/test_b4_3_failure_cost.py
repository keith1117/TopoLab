"""Read-only diagnosis: failed-status preservation, numerical causes, and byte boundaries."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import b4_3_failure_cost as diagnosis  # noqa: E402

from topolab.b3_queries import (  # noqa: E402
    AttemptTiming,
    QueryAttempt,
    QueryOutcome,
    TerminalWitness,
)
from topolab.baselines import BaselineMetrics  # noqa: E402


@pytest.fixture
def attempt(b3_reference):  # type: ignore[no-untyped-def]
    result = b3_reference.result
    return QueryAttempt(
        succeeded=True,
        timing=AttemptTiming(refinement_seconds=2),
        metrics=BaselineMetrics(
            iterations=len(result.history),
            final_compliance=result.compliance,
            physical_volume_error=0,
        ),
        state=TerminalWitness.from_result(result),
    )


def test_plan_has_only_screen_cases_and_no_byte_access(monkeypatch, tmp_path, capsys):  # type: ignore[no-untyped-def]
    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        pytest.fail("planning must not open source indices or artifacts")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    output = tmp_path / "new-diagnosis"
    assert (
        diagnosis.main(
            [
                "--screen-root",
                str(tmp_path / "screen"),
                "--output-root",
                str(output),
            ]
        )
        == 0
    )
    assert not output.exists()
    assert '"final_artifact_reads": 0' in capsys.readouterr().out
    plan = diagnosis.plan_payload()
    assert plan["plan_sha256"] == (
        "a1a3a42deeff9e863b8c2310bc8a907770e0420889c20ca5bd6fa5def7f26392"
    )
    assert len(plan["case_ids"]) == len(set(plan["case_ids"])) == 48
    assert plan["label_and_model_byte_reads"] == plan["new_solver_calls"] == 0


def test_changed_index_rejected_before_case_access(tmp_path):  # type: ignore[no-untyped-def]
    (tmp_path / "b3_screen.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="input checksum"):
        diagnosis.input_index(tmp_path)
    assert list(tmp_path.iterdir()) == [tmp_path / "b3_screen.json"]


@pytest.mark.parametrize(
    "bound,expected",
    [
        ("measured", 1.6),
        ("fallback_free", 0.6),
        ("failed_to_uniform", 1.0),
    ],
)
def test_optimistic_costs_do_not_clear_failure(bound, expected):  # type: ignore[no-untyped-def]
    row = {
        "seconds": 16,
        "fallback_seconds": 10,
        "uniform_seconds": 10,
        "candidate": {"succeeded": False},
    }
    assert diagnosis.effective_ratio(row, bound) == expected
    assert row["candidate"]["succeeded"] is False


def test_converged_quality_gap_is_separate_from_nonconvergence(attempt):  # type: ignore[no-untyped-def]
    reference = attempt.model_copy(
        update={
            "metrics": attempt.metrics.model_copy(
                update={
                    "final_compliance": attempt.metrics.final_compliance / 1.01,
                }
            ),
        }
    )
    failed = attempt.model_copy(
        update={
            "succeeded": False,
            "failure_code": "quality_error",
            "failure_type": "ValueError",
        }
    )
    result = diagnosis.attempt_summary(failed, reference)
    assert result["converged"]
    assert result["quality_reasons"] == ["compliance_above_matched_uniform"]
    assert result["compliance_ratio"] == pytest.approx(1.01)
    nonconverged = attempt.model_copy(
        update={
            "succeeded": False,
            "failure_code": "quality_error",
            "failure_type": "ValueError",
            "state": attempt.state.model_copy(
                update={
                    "result": attempt.state.result.model_copy(update={"converged": False}),
                }
            ),
        }
    )
    assert diagnosis.attempt_summary(nonconverged, attempt)["quality_reasons"] == ["not_converged"]
    with pytest.raises(ValueError, match="status differs"):
        diagnosis.attempt_summary(attempt, reference)


def test_identical_states_expose_timing_difference_without_replacing_costs(attempt):  # type: ignore[no-untyped-def]
    left = QueryOutcome(method="P", seed=17, route="generalist", attempt=attempt)
    right = QueryOutcome(
        method="P_without_S",
        seed=17,
        route="generalist",
        attempt=(attempt.model_copy(update={"timing": AttemptTiming(refinement_seconds=4)})),
    )
    comparison = diagnosis.same_model_pair(left, right)
    assert comparison["states_identical"] and comparison["status_identical"]
    assert comparison["spread_factor"] == 2
    assert left.seconds == 2 and right.seconds == 4


def test_diagnostic_output_cannot_modify_screen_root(tmp_path):  # type: ignore[no-untyped-def]
    with pytest.raises(ValueError, match="separate"):
        diagnosis.main(
            [
                "--screen-root",
                str(tmp_path),
                "--output-root",
                str(tmp_path / "diagnostic"),
            ]
        )
