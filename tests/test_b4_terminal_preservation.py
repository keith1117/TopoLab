"""Own-certificate rollback, fully paid continuation and exposure boundaries."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from topolab import b4_polish_probe as previous
from topolab import b4_terminal_preservation as probe
from topolab.b3_catalog import canonical_metadata_bytes, physical_fingerprint
from topolab.b3_queries import TerminalWitness
from topolab.b4_telemetry import digest


def script(name):
    folder = Path(__file__).resolve().parents[1] / "scripts"
    sys.path.insert(0, str(folder))
    try:
        spec = importlib.util.spec_from_file_location(name, folder / (name + ".py"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(folder))


def states(reference):
    case = next(
        c
        for c in probe.sentinel_cases()
        if c.problem.mesh.element_counts[0] == 24
        and c.problem.loads[0].direction == "y"
        and c.problem.optimization.volume_fraction == 0.4703
    )
    template = reference.result
    volume = case.problem.optimization.volume_fraction
    density = tuple(volume for _ in template.design_density)
    recent = tuple(
        template.history[0].model_copy(
            update={
                "iteration": i,
                "density_change": 0.02,
                "compliance": 100 - i * 0.001,
                "volume_fraction": volume,
                "design_density": density,
                "physical_density": density,
            }
        )
        for i in range(1, 12)
    )
    before = template.model_copy(
        update={
            "history": recent,
            "design_density": density,
            "physical_density": density,
            "compliance": recent[-1].compliance,
            "converged": True,
        }
    )
    history = (
        *recent,
        *(
            recent[-1].model_copy(
                update={
                    "iteration": i,
                    "compliance": 100 - i * 0.004,
                }
            )
            for i in range(12, 32)
        ),
    )
    after = before.model_copy(
        update={
            "history": history,
            "compliance": history[-1].compliance,
            "converged": False,
        }
    )
    return case, before, after


def test_certificate_loss_preserves_original_despite_better_compliance(b3_reference):
    case, before, after = states(b3_reference)
    assert after.compliance < before.compliance
    assert probe.select_terminal(case, before, after) == "original"
    # The rule works on complete histories and compact retained witnesses alike.
    assert (
        probe.select_terminal(
            case,
            TerminalWitness.from_result(before).result,
            TerminalWitness.from_result(after).result,
        )
        == "original"
    )
    auditor = script("b4_12_independent_audit")
    assert (
        auditor.selection(
            case.model_dump(mode="json"),
            TerminalWitness.from_result(before).model_dump(mode="json"),
            TerminalWitness.from_result(after).model_dump(mode="json"),
        )
        == "original"
    )


def test_valid_endpoint_is_chosen_without_reference_or_quality_oracle(b3_reference):
    case, before, after = states(b3_reference)
    last = after.history[-1].model_copy(update={"density_change": 0.01, "compliance": 120.0})
    after = after.model_copy(
        update={
            "history": (*after.history[:-1], last),
            "compliance": 120.0,
            "converged": True,
        }
    )
    # A reference-quality failure must still reach ordinary classification/fallback.
    assert probe.select_terminal(case, before, after) == "endpoint"


@pytest.mark.parametrize("count", [0, 19])
def test_incomplete_continuation_never_hides_its_cap_failure(b3_reference, count):
    case, before, after = states(b3_reference)
    history = after.history[: 11 + count]
    truncated = after.model_copy(update={"history": history, "compliance": history[-1].compliance})
    assert probe.select_terminal(case, before, truncated) == "endpoint"


def test_flags_and_original_volume_cannot_bypass_certificate(b3_reference):
    case, before, after = states(b3_reference)
    with pytest.raises(ValueError, match="certificate"):
        probe.select_terminal(case, before, after.model_copy(update={"converged": True}))
    with pytest.raises(ValueError, match="valid own"):
        probe.select_terminal(case, before.model_copy(update={"physical_density": (0.1,)}), after)


def test_unqualified_stops_remain_endpoint(b3_reference):
    case, before, after = states(b3_reference)
    for control in probe.sentinel_cases():
        if (
            control.problem.mesh.element_counts[0] == 12
            or control.problem.loads[0].direction == "z"
            or control.problem.optimization.volume_fraction >= 0.55
        ):
            assert probe.select_terminal(control, before, after) == "endpoint"
    assert (
        probe.select_terminal(case, before.model_copy(update={"converged": False}), after)
        == "endpoint"
    )


def test_recording_keeps_both_witnesses_and_pays_full_twenty(b3_reference, tmp_path, monkeypatch):
    runner = script("b4_12_terminal_preservation")
    case, before, endpoint = states(b3_reference)
    work = []

    def fixed_polish(case, result, checkpoint):
        assert result is before
        for _ in range(20):
            work.append(1)
            checkpoint()
        return endpoint

    monkeypatch.setattr(runner, "polish", fixed_polish)
    pulses = []
    selected = runner.recorded_refinement(
        tmp_path, "a" * 64, 17, case, before, lambda: pulses.append(1)
    )
    assert selected is before and len(work) == len(pulses) == 20
    record = json.loads((tmp_path / f"polish/{case.case_id}_17.json").read_bytes())
    assert record["updates"] == 20 and record["first_stop_iteration"] == 11
    assert record["selection"] == "original"
    assert record["after_witness_sha256"] == digest(
        canonical_metadata_bytes(TerminalWitness.from_result(endpoint).model_dump(mode="json"))
    )
    assert runner.read_blob(tmp_path, record["endpoint"], "endpoint") == canonical_metadata_bytes(
        TerminalWitness.from_result(endpoint).model_dump(mode="json")
    )
    assert record["selected_witness_sha256"] == record["before"]["sha256"]
    # Recovery cannot overwrite a differing raw endpoint or choice.
    changed = endpoint.model_copy(
        update={"displacements": tuple(0.0 for _ in endpoint.displacements)}
    )
    monkeypatch.setattr(runner, "polish", lambda *a: changed)
    with pytest.raises(ValueError, match="changed on recovery"):
        runner.recorded_refinement(tmp_path, "a" * 64, 17, case, before, lambda: None)


def test_plan_has_new_disjoint_cases_and_no_artifact_access(monkeypatch):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("opened artifact"))
    plan = probe.plan()
    assert len(plan["cases"]["fresh"]) == 48 and len(plan["assignments"]["fresh"]) == 576
    assert probe.assignments("sentinel") == previous.assignments("sentinel")
    assert plan["fixed_primary"] == 17 and plan["polish_updates"] == 20
    assert plan["plan_sha256"] == "48171ac3beebf5abb19f59585bb6c387d4b72469e73a9fcaf749930b56bbae00"
    assert not plan["final_access"] and not plan["old_fresh_panel_access"]
    assert not {physical_fingerprint(c) for c in probe.fresh_cases()} & {
        physical_fingerprint(c) for c in previous.fresh_cases()
    }
    assert (
        digest(canonical_metadata_bytes({k: v for k, v in plan.items() if k != "plan_sha256"}))
        == plan["plan_sha256"]
    )
    with pytest.raises(ValueError, match="unknown"):
        probe.cases("final")


def test_independent_fresh_gate_reproduces_fixed_primary_and_full_cost(b3_reference):
    from topolab.b3_queries import AttemptTiming, QueryAttempt, QueryOutcome, policy_route
    from topolab.baselines import BaselineMetrics

    witness = TerminalWitness.from_result(b3_reference.result)
    success = QueryAttempt(
        succeeded=True,
        timing=AttemptTiming(),
        state=witness,
        metrics=BaselineMetrics(
            iterations=len(witness.trace),
            final_compliance=witness.result.compliance,
            physical_volume_error=0,
        ),
    )
    cases = {c.case_id: c for c in probe.fresh_cases()}
    packets = []
    for case_id, policy in probe.assignments("fresh"):
        name, _, seed = policy.partition("/")
        method = "P" if name == "W" else name
        outcome = QueryOutcome(
            method=method,
            seed=int(seed) if seed else None,
            route=policy_route(cases[case_id], method),
            attempt=success,
        )
        packets.append(
            {
                "case_id": case_id,
                "policy": policy,
                "outcome": outcome.model_dump(mode="json"),
                "timing": {
                    "wall_seconds": 10 if name == "uniform" else 5 if name == "P" else 7,
                    "legacy_phase_seconds": 0.0,
                },
                "recording_allowance_seconds": 1.0,
            }
        )
    auditor = script("b4_12_independent_audit")
    raw_cases = {k: c.model_dump(mode="json") for k, c in cases.items()}
    decision = probe.fresh_gate(packets)
    assert decision["polish_gate_passed"] and decision["fixed_primary"] == 17
    auditor.close(decision, auditor.fresh_decision(packets, raw_cases))
    target = next(p for p in packets if p["policy"] == "P/17")
    target["timing"]["wall_seconds"] = 1000
    assert not probe.fresh_gate(packets)["polish_gate_passed"]
    auditor.close(probe.fresh_gate(packets), auditor.fresh_decision(packets, raw_cases))


def test_changed_input_rejected_before_model_bytes(tmp_path, monkeypatch):
    source = tmp_path / "b4-10-post-plateau-polish/audit_receipts"
    source.mkdir(parents=True)
    (source / "evidence_release.json").write_text("{}\n")
    monkeypatch.setattr(previous, "upstream_fits", lambda *a: pytest.fail("opened model"))
    with pytest.raises(ValueError, match="before model or label"):
        probe.upstream_fits(tmp_path / "b4-5-weighted-terminal")


def test_default_is_metadata_only_and_failed_sentinel_keeps_fresh_sealed(
    tmp_path, monkeypatch, capsys
):
    runner = script("b4_12_terminal_preservation")
    monkeypatch.setattr(sys, "argv", ["probe"])
    monkeypatch.setattr(runner, "screening_preflight", lambda *a: pytest.fail("opened labels"))
    runner.main()
    assert json.loads(capsys.readouterr().out)["version"] == probe.VERSION
    folder = tmp_path / "sentinel/policy-audit"
    folder.mkdir(parents=True)
    (folder / "summary.json").write_bytes(
        canonical_metadata_bytes({"context_sha256": "a" * 64, "passed": False})
    )
    (tmp_path / "sentinel/independent_audit.json").write_bytes(
        canonical_metadata_bytes({"passed": True})
    )
    with pytest.raises(ValueError, match="sealed"):
        runner.require_sentinel(tmp_path, "a" * 64)
