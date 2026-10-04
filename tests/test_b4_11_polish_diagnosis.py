"""Read-only boundaries, terminal evidence and failure-preserving cost bounds."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import b4_11_independent_audit as independent  # noqa: E402
import b4_11_polish_diagnosis as diagnosis  # noqa: E402


def witness(count=97, gain=0.0002063051569921597, converged=False):  # type: ignore[no-untyped-def]
    trace = [
        {
            "iteration": i,
            "compliance": 100 * (1 - gain * (i - 1) / (count - 1)),
            "volume_fraction": 0.47,
            "density_change": 0.03,
        }
        for i in range(1, count + 1)
    ]
    # The frozen certificate uses its retained ten-update window, not total gain.
    for j, point in enumerate(trace[-11:]):
        point["compliance"] = 100 * (1 - gain * j / 10)
    states = [
        {**p, "design_density": [0.47, 0.47], "physical_density": [0.47, 0.47]} for p in trace[-11:]
    ]
    return {
        "trace": trace,
        "result": {
            **states[-1],
            "history": states,
            "converged": converged,
            "displacements": [0.0],
            "reactions": [0.0],
        },
    }


def row(method="P/17", succeeded=False):  # type: ignore[no-untyped-def]
    return {
        "case_id": "retained",
        "method": method,
        "scale": "large",
        "direction": "y",
        "route": "generalist",
        "seconds": 16.0,
        "uniform_seconds": 10.0,
        "fallback_seconds": 10.0,
        "triggered": True,
        "before": {"succeeded": True, "compliance_ratio": 1.0},
        "candidate": {
            "succeeded": succeeded,
            "stop": "post_polish_nonconvergence",
            "quality_reasons": ["not_converged"],
            "compliance_ratio": 0.9995,
        },
    }


def test_plan_reads_no_experiment_bytes_and_creates_no_output(monkeypatch, tmp_path, capsys):  # type: ignore[no-untyped-def]
    def forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
        pytest.fail("metadata planning must not read experiment bytes")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    output = tmp_path / "diagnosis"
    assert (
        diagnosis.main(["--screen-root", str(tmp_path / "source"), "--output-root", str(output)])
        == 0
    )
    assert not output.exists()
    assert '"solver_calls": 0' in capsys.readouterr().out
    assert diagnosis.plan_payload()["plan_sha256"] == independent.PLAN_SHA
    assert json.loads(diagnosis.canonical(diagnosis.plan_payload())) == diagnosis.plan_payload()
    assert len(diagnosis.BINDINGS) == 14


def test_changed_receipt_rejected_before_unit_access(tmp_path):  # type: ignore[no-untyped-def]
    first = tmp_path / "audit_receipts/plan.json"
    first.parent.mkdir()
    first.write_bytes(b"{}\n")
    with pytest.raises(ValueError, match="checksum"):
        diagnosis.check_inputs(tmp_path)


@pytest.mark.parametrize(
    "reader,exception", [(diagnosis.read, ValueError), (independent.read, AssertionError)]
)
def test_symlink_escape_rejected_before_read(reader, exception, tmp_path):  # type: ignore[no-untyped-def]
    root = tmp_path / "input"
    root.mkdir()
    target = tmp_path / "forbidden.json"
    target.write_bytes(b"{}\n")
    (root / "escape.json").symlink_to(target)
    with pytest.raises(exception, match="escape"):
        reader(root, "escape.json")


def test_changed_content_address_or_serialization_is_rejected(tmp_path):  # type: ignore[no-untyped-def]
    (tmp_path / "receipt.json").write_bytes(b'{ "passed": true }\n')
    with pytest.raises(ValueError, match="canonical"):
        diagnosis.read(tmp_path, "receipt.json")
    with pytest.raises(ValueError, match="content-addressed path"):
        diagnosis.blob(tmp_path, "screen", {"sha256": "0" * 64, "path": "elsewhere"}, "outcome")


@pytest.mark.parametrize("nested", [True, False])
def test_output_must_not_overlap_input(nested, tmp_path):  # type: ignore[no-untyped-def]
    source, output = (tmp_path, tmp_path / "child") if nested else (tmp_path / "child", tmp_path)
    with pytest.raises(ValueError, match="separate"):
        diagnosis.main(["--screen-root", str(source), "--output-root", str(output)])


def test_fixed_endpoint_can_improve_compliance_but_lose_plateau_certificate():
    before = witness(count=77, gain=0.00019, converged=True)
    after = witness()
    b = diagnosis.terminal(before, 100, 0.47)
    a = diagnosis.terminal(after, 100, 0.47, polished=True)
    assert b["succeeded"] and b["plateau_certificate"]
    assert a["compliance_ratio"] < b["compliance_ratio"]
    assert a["quality_reasons"] == ["not_converged"]
    assert a["stop"] == "post_polish_nonconvergence"
    assert a["iterations"] < 360 and not a["plateau_certificate"]
    independent.close(a, independent.certificate(after, 100, 0.47, polished=True))
    assert diagnosis.terminal(witness(count=360), 100, 0.47)["stop"] == "iteration_cap"


def test_claimed_convergence_without_either_certificate_is_rejected():
    with pytest.raises(ValueError, match="certificate"):
        diagnosis.terminal(witness(converged=True), 100, 0.47, polished=True)
    with pytest.raises(AssertionError, match="certificate"):
        independent.certificate(witness(converged=True), 100, 0.47, polished=True)


@pytest.mark.parametrize("reader", [diagnosis.terminal, independent.certificate])
def test_quality_limits_are_not_relaxed(reader):  # type: ignore[no-untyped-def]
    state = witness(gain=0, converged=True)
    assert not reader(state, 99.89, 0.47)["succeeded"]
    assert reader(state, 99.89, 0.47)["quality_reasons"] == ["compliance_above_matched_uniform"]
    assert reader(state, 100, 0.476)["quality_reasons"] == ["physical_volume_error"]


def test_cost_scenarios_preserve_failures_and_full_measured_envelope():
    rows = [row()]
    original = copy.deepcopy(rows)
    for scenario, ratio in (("measured", 1.6), ("fallback_free", 0.6), ("failed_to_uniform", 1.0)):
        result = diagnosis.costs(rows, scenario)
        assert result["observed_failures"] == 1 and result["observed_statuses_preserved"]
        assert result["mean_paired_ratio"] == ratio
        assert result["diagnostic_only"] == (scenario != "measured")
        independent.close(result, independent.costs(rows, scenario))
    assert rows == original
    with pytest.raises(ValueError, match="unknown"):
        diagnosis.costs(rows, "optimized_polish_length")


def test_failed_fixed_primary_cannot_be_replaced_by_successful_seed():
    rows = [row(), row("P/43", True)]
    result = diagnosis.scientific_decision(rows)
    assert result["fixed_primary"] == 17 and result["primary_failures"] == ["retained"]
    assert not result["sentinel_gate_passed"] and not result["final_access"]


@pytest.mark.parametrize(
    "change", ["seed", "compliance", "cause", "trigger", "second_regression", "cost"]
)
def test_next_probe_requires_one_convergence_only_regression_and_strict_cost_headroom(change):  # type: ignore[no-untyped-def]
    rows, bound = [row()], {"mean_paired_ratio": 0.99, "ratio_of_sums": 0.99}
    assert (
        diagnosis.next_mechanism(rows, bound)
        == "bounded_candidate_terminal_witness_preservation_probe"
    )
    if change == "seed":
        rows[0]["method"] = "P/43"
    elif change == "compliance":
        rows[0]["candidate"]["compliance_ratio"] = 1.002
    elif change == "cause":
        rows[0]["candidate"]["quality_reasons"].append("physical_volume_error")
    elif change == "trigger":
        rows[0]["triggered"] = False
    elif change == "second_regression":
        rows.append(copy.deepcopy(rows[0]))
    else:
        bound["ratio_of_sums"] = 1.0
    assert (
        diagnosis.next_mechanism(rows, bound)
        == "generalist_reliability_and_refinement_method_review"
    )
    assert independent.recommendation(rows, bound) == diagnosis.next_mechanism(rows, bound)


@pytest.mark.parametrize("change", ["status", "ratio", "cause"])
def test_independent_comparison_rejects_tampered_arithmetic(change):  # type: ignore[no-untyped-def]
    expected = independent.certificate(witness(), 100, 0.47, polished=True)
    changed = copy.deepcopy(expected)
    key = {"status": "succeeded", "ratio": "compliance_ratio", "cause": "stop"}[change]
    changed[key] = True if change == "status" else 2 if change == "ratio" else "iteration_cap"
    with pytest.raises(AssertionError):
        independent.close(changed, expected)


def test_changed_journal_assignment_fails_before_units(tmp_path):  # type: ignore[no-untyped-def]
    prefix = tmp_path / "sentinel/reference"
    prefix.mkdir(parents=True)
    progress = {
        "context_sha256": "context",
        "units_sha256": diagnosis.sha(diagnosis.canonical(["case"])),
    }
    for name in ("progress", "summary"):
        (prefix / f"{name}.json").write_bytes(diagnosis.canonical(progress))
    with pytest.raises(ValueError, match="journal"):
        diagnosis.chain(tmp_path, "reference", ["another_case"], "context")
    with pytest.raises(AssertionError):
        independent.journal(tmp_path, "reference", ["another_case"], "context")
