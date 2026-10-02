"""Rollback exposure, unchanged artifacts and prospective primary boundaries."""

import importlib.util
import json
from pathlib import Path

import pytest

import topolab.b4_rollback as rollback
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
from topolab.b4_confirmation import fresh_cases as confirmation_cases
from topolab.b4_weighted_terminal import fresh_cases as previous_cases
from topolab.baselines import BaselineMetrics


def runner():
    path = Path(__file__).resolve().parents[1] / "scripts/b4_7_spatial_rollback.py"
    spec = importlib.util.spec_from_file_location("rollback_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_plan_is_exact_disjoint_balanced_and_never_opens_bytes(monkeypatch):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("opened artifact"))
    plan = rollback.plan()
    assert len(plan["cases"]) == 48 and len(plan["assignments"]) == 576
    assert plan["fixed_primary"] == 17 and plan["new_fits"] == 0
    assert plan["candidate"] == "P" and plan["comparison"] == "W"
    assert plan["plan_sha256"] == "7f161aa36d9071bf17beae5e26f93f274e1c3b6ffdaf12f104f57f0f1faf8825"
    assert not plan["final_access"] and "fit" not in plan["caps"]
    cases = rollback.fresh_cases()
    blocked = {e.physical_fingerprint for e in build_b3_exposure_ledger().entries}
    blocked.update(e.physical_fingerprint for e in build_b3_case_catalog().entries)
    blocked.update(physical_fingerprint(c) for c in previous_cases())
    blocked.update(physical_fingerprint(c) for c in confirmation_cases())
    assert not {physical_fingerprint(c) for c in cases} & blocked
    for scale in (12, 24):
        for direction in ("y", "z"):
            for volume in rollback.VOLUMES:
                assert (
                    sum(
                        c.problem.mesh.element_counts[0] == scale
                        and c.problem.loads[0].direction == direction
                        and c.problem.optimization.volume_fraction == volume
                        for c in cases
                    )
                    == 3
                )
    for i in range(0, 576, 12):
        rows = plan["assignments"][i : i + 12]
        assert rows[0][1] == "uniform" and len({c for c, _ in rows}) == 1
        assert {m for _, m in rows} == set(rollback.METHODS)
    assert len(rollback.units("audit")) == 626
    with pytest.raises(ValueError, match="no fitting"):
        rollback.units("fit")


def test_changed_upstream_blocks_checkpoints_and_labels_before_read(tmp_path, monkeypatch):
    module = runner()
    previous = tmp_path.parent / "b4-6-development-confirmation"
    previous.mkdir()
    (previous / "context.json").write_text("{}\n")
    monkeypatch.setattr(module, "read_selected_model", lambda *a: pytest.fail("opened model"))
    monkeypatch.setattr(
        rollback.confirmation, "upstream_fits", lambda *a: pytest.fail("opened unit")
    )
    with pytest.raises(ValueError, match="before model or label"):
        module.load_models(None, tmp_path, tmp_path)


def packets(reference, failing=None):
    witness = TerminalWitness.from_result(reference.result)
    metrics = BaselineMetrics(
        iterations=len(witness.trace),
        final_compliance=witness.result.compliance,
        physical_volume_error=0,
    )
    cases = {c.case_id: c for c in rollback.fresh_cases()}
    failed = False
    for case_id, policy in rollback.assignments():
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
                "wall_seconds": 10 if name == "uniform" else (5 if name == "P" else 8),
                "legacy_phase_seconds": 0,
            },
            "recording_allowance_seconds": 1.0,
        }


def test_fixed_primary_cannot_be_reselected_and_failed_seed_retained(b3_reference):
    result = rollback.rollback_gate(packets(b3_reference, "P/29"))
    assert result["rollback_gate_passed"] and result["fixed_primary"] == 17
    assert result["passing_seeds"] == [17, 43]
    assert result["quality_cells"] == {"0.5401": 9, "0.6001": 9}
    assert result["table"]["P/29"]["failures"] == result["table"]["P/29"]["fallbacks"] == 1
    result = rollback.rollback_gate(packets(b3_reference, "P/17"))
    assert result["passing_seeds"] == [29, 43]
    assert result["fixed_primary"] == 17 and not result["rollback_gate_passed"]
    assert "development_primary" not in result
    with pytest.raises(ValueError, match="every fixed"):
        rollback.rollback_gate(list(packets(b3_reference))[:-1])


def test_scale_total_gate_cannot_be_hidden_by_equal_case_ratios(b3_reference):
    retained = list(packets(b3_reference))
    case_id = next(
        c.case_id for c in rollback.fresh_cases() if c.problem.mesh.element_counts[0] == 12
    )
    for p in retained:
        if p["case_id"] == case_id and p["policy"] in ("uniform", "P/17"):
            p["timing"]["wall_seconds"] = 1000 if p["policy"] == "uniform" else 1100
    result = rollback.rollback_gate(retained)
    assert result["table"]["P/17"]["primary_eligible"]
    assert result["table"]["P/17"]["scale_means"]["small"] < 0.9
    assert result["table"]["P/17"]["scale_total_ratios"]["small"] > 0.9
    assert not result["rollback_gate_passed"]


def test_default_cli_has_no_preflight_output_or_final_artifact_access(
    tmp_path, monkeypatch, capsys
):
    module = runner()
    monkeypatch.setattr(module, "screening_preflight", lambda *a: pytest.fail("opened input"))
    monkeypatch.setattr(module, "run", lambda *a: pytest.fail("called solver"))
    monkeypatch.setattr("sys.argv", ["b4_7", "--output", str(tmp_path / "uncreated")])
    module.main()
    assert not (tmp_path / "uncreated").exists()
    plan = json.loads(capsys.readouterr().out)
    assert plan["fixed_primary"] == 17 and not plan["final_access"]


def test_rollback_needs_predeclared_improvement_over_weighted_control(b3_reference):
    retained = list(packets(b3_reference))
    for packet in retained:
        if packet["policy"].startswith("W/"):
            packet["timing"]["wall_seconds"] = 5
    result = rollback.rollback_gate(retained)
    assert result["passing_seeds"] == [17, 29, 43]
    assert not result["table"]["P/17"]["primary_eligible"]
    assert not result["rollback_gate_passed"]


def test_previous_confirmation_plan_and_shared_assignment_population_are_unchanged():
    from topolab import b4_confirmation
    from topolab.b4_development import DevelopmentSpec

    assert b4_confirmation.plan()["plan_sha256"] == (
        "2bde23e3da2232bd06a20607e5735d0dec81c3b5a7bc716face878e38b8c1440"
    )
    for module, gate in (
        (rollback, rollback.rollback_gate),
        (b4_confirmation, b4_confirmation.confirmation_gate),
    ):
        spec = DevelopmentSpec(
            module.VERSION,
            module.RECEIPT_VERSION,
            module.CAPS,
            module.fresh_cases(),
            module.assignments(),
            gate,
            module.upstream_fits,
        )
        assert all(spec.units(stage) == module.units(stage) for stage in module.CAPS)


def test_shared_execution_keeps_version_receipts_complete_references_and_resume(
    b3_reference, tmp_path, monkeypatch
):
    from topolab import b4_development as execution
    from topolab.b4_weighted_terminal import read_units

    case = b3_reference.entry.case
    witness = TerminalWitness.from_result(b3_reference.result)
    success = QueryAttempt(
        succeeded=True,
        timing=AttemptTiming(),
        state=witness,
        metrics=BaselineMetrics(
            iterations=1, final_compliance=witness.result.compliance, physical_volume_error=0
        ),
    )
    invoked = []

    def evaluate(case, method, seed, *args):
        invoked.append(method)
        return QueryOutcome(
            method=method, seed=seed, route=policy_route(case, method), attempt=success
        )

    spec = execution.DevelopmentSpec(
        rollback.VERSION,
        rollback.RECEIPT_VERSION,
        rollback.CAPS,
        (case,),
        ((case.case_id, "uniform"), (case.case_id, "P/17")),
        lambda packets: {"policies": [p["policy"] for p in packets]},
        lambda root: [],
    )
    monkeypatch.setattr(execution, "load_neighbors", lambda *a: {(3, 6, 12): None})

    def run(stage):
        return execution.run_development(
            stage,
            tmp_path,
            tmp_path / "data",
            tmp_path / "old",
            tmp_path / "weighted",
            None,
            "a" * 64,
            0,
            spec=spec,
            load_models=lambda *a: ({}, {}),
            evaluate_query=evaluate,
        )

    # Screening cannot run from a partial/missing mandatory reference population.
    with pytest.raises(FileNotFoundError):
        run("screen")
    assert not invoked
    # That failed journal is permanently marked; use a separate unfailed root.
    tmp_path = tmp_path / "complete"
    assert run("reference")["completed"] == 1
    assert run("screen")["decision"]["policies"] == ["uniform", "P/17"]
    assert invoked == ["uniform", "uniform", "P"]
    assert run("screen")["attempted"] == 2
    assert invoked == ["uniform", "uniform", "P"]
    refs = read_units(tmp_path / "screen", "a" * 64, spec.units("screen"), caps=spec.caps)
    for i, ref in enumerate(refs):
        receipt = json.loads((tmp_path / "screen" / f"recording/{i:04d}.json").read_bytes())
        assert receipt["version"] == rollback.RECEIPT_VERSION
        assert receipt["outcome_sha256"] == ref["sha256"]
