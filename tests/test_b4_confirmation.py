"""Confirmation exposure, unchanged artifacts and prospective primary boundaries."""

import importlib.util
import json
from pathlib import Path

import pytest

import topolab.b4_confirmation as confirmation
from topolab.b3_catalog import (
    build_b3_case_catalog,
    build_b3_exposure_ledger,
    physical_fingerprint,
)
from topolab.b3_queries import (
    AttemptTiming,
    QueryAttempt,
    QueryOutcome,
    TerminalWitness,
    policy_route,
)
from topolab.b4_weighted_terminal import fresh_cases as previous_cases
from topolab.baselines import BaselineMetrics


def runner():
    path = Path(__file__).resolve().parents[1] / "scripts/b4_6_development_confirmation.py"
    spec = importlib.util.spec_from_file_location("confirmation_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plan_is_exact_disjoint_balanced_and_never_opens_bytes(monkeypatch):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("opened artifact"))
    plan = confirmation.plan()
    assert len(plan["cases"]) == 96 and len(plan["assignments"]) == 1152
    assert plan["fixed_primary"] == 17 and plan["new_fits"] == 0
    assert not plan["final_access"] and "fit" not in plan["caps"]
    cases = confirmation.fresh_cases()
    blocked = {e.physical_fingerprint for e in build_b3_exposure_ledger().entries}
    blocked.update(e.physical_fingerprint for e in build_b3_case_catalog().entries)
    blocked.update(physical_fingerprint(c) for c in previous_cases())
    assert not {physical_fingerprint(c) for c in cases} & blocked
    for scale in (12, 24):
        for direction in ("y", "z"):
            for volume in confirmation.VOLUMES:
                assert (
                    sum(
                        c.problem.mesh.element_counts[0] == scale
                        and c.problem.loads[0].direction == direction
                        and c.problem.optimization.volume_fraction == volume
                        for c in cases
                    )
                    == 6
                )
    for i in range(0, 1152, 12):
        rows = plan["assignments"][i : i + 12]
        assert rows[0][1] == "uniform" and len({c for c, _ in rows}) == 1
        assert {m for _, m in rows} == set(confirmation.METHODS)
    assert len(confirmation.units("audit")) == 1250
    with pytest.raises(ValueError, match="no fitting"):
        confirmation.units("fit")


def test_changed_upstream_blocks_checkpoints_and_labels_before_read(tmp_path, monkeypatch):
    module = runner()
    (tmp_path / "context.json").write_text("{}\n")
    monkeypatch.setattr(module, "read_selected_model", lambda *a: pytest.fail("opened model"))
    monkeypatch.setattr(confirmation, "read_units", lambda *a: pytest.fail("opened unit"))
    with pytest.raises(ValueError, match="before model or label"):
        module.load_models(None, tmp_path, tmp_path)


def packets(reference, failing=None):
    witness = TerminalWitness.from_result(reference.result)
    metrics = BaselineMetrics(
        iterations=len(witness.trace),
        final_compliance=witness.result.compliance,
        physical_volume_error=0,
    )
    cases = {c.case_id: c for c in confirmation.fresh_cases()}
    failed = False
    for case_id, policy in confirmation.assignments():
        name, _, text = policy.partition("/")
        method = "P" if name == "W" else name
        success = QueryAttempt(
            succeeded=True, timing=AttemptTiming(), metrics=metrics, state=witness
        )
        attempt, fallback = success, None
        if policy == failing and not failed:
            failed = True
            attempt = success.model_copy(
                update={
                    "succeeded": False,
                    "failure_code": "quality_error",
                    "failure_type": "ValueError",
                }
            )
            fallback = success
        outcome = QueryOutcome(
            method=method,
            seed=int(text) if text else None,
            route=policy_route(cases[case_id], method),
            attempt=attempt,
            fallback=fallback,
        )
        yield {
            "case_id": case_id,
            "policy": policy,
            "outcome": outcome.model_dump(mode="json"),
            "timing": {
                "wall_seconds": 10 if name == "uniform" else (5 if name == "W" else 8),
                "legacy_phase_seconds": 0,
            },
            "recording_allowance_seconds": 1.0,
        }


def test_fixed_primary_cannot_be_reselected_and_failed_seed_retained(b3_reference):
    result = confirmation.confirmation_gate(packets(b3_reference, "W/29"))
    assert result["confirmation_gate_passed"] and result["fixed_primary"] == 17
    assert result["passing_seeds"] == [17, 43]
    assert result["quality_cells"] == {"0.5389": 18, "0.5989": 18}
    assert result["table"]["W/29"]["failures"] == result["table"]["W/29"]["fallbacks"] == 1
    result = confirmation.confirmation_gate(packets(b3_reference, "W/17"))
    assert result["passing_seeds"] == [29, 43]
    assert result["fixed_primary"] == 17 and not result["confirmation_gate_passed"]
    assert "development_primary" not in result
    with pytest.raises(ValueError, match="every fixed"):
        confirmation.confirmation_gate(list(packets(b3_reference))[:-1])


def test_scale_total_gate_cannot_be_hidden_by_equal_case_ratios(b3_reference):
    retained = list(packets(b3_reference))
    case_id = next(
        c.case_id for c in confirmation.fresh_cases() if c.problem.mesh.element_counts[0] == 12
    )
    for p in retained:
        if p["case_id"] == case_id and p["policy"] in ("uniform", "W/17"):
            p["timing"]["wall_seconds"] = 1000 if p["policy"] == "uniform" else 1100
    result = confirmation.confirmation_gate(retained)
    assert result["table"]["W/17"]["primary_eligible"]
    assert result["table"]["W/17"]["scale_means"]["small"] < 0.9
    assert result["table"]["W/17"]["scale_total_ratios"]["small"] > 0.9
    assert not result["confirmation_gate_passed"]


def test_default_cli_has_no_preflight_output_or_final_artifact_access(
    tmp_path, monkeypatch, capsys
):
    module = runner()
    monkeypatch.setattr(module, "screening_preflight", lambda *a: pytest.fail("opened input"))
    monkeypatch.setattr(module, "run", lambda *a: pytest.fail("called solver"))
    monkeypatch.setattr("sys.argv", ["b4_6", "--output", str(tmp_path / "uncreated")])
    module.main()
    assert not (tmp_path / "uncreated").exists()
    plan = json.loads(capsys.readouterr().out)
    assert plan["fixed_primary"] == 17 and not plan["final_access"]
