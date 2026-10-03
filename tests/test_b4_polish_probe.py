"""Numerical continuation oracle and frozen probe access/stop boundaries."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from torch import nn

from topolab import b3_queries
from topolab import b4_polish as numerical
from topolab import b4_polish_probe as probe
from topolab import b4_rollback_confirmation as previous
from topolab.b3_catalog import physical_fingerprint
from topolab.b3_queries import (
    AttemptTiming,
    QueryAttempt,
    QueryOutcome,
    TerminalWitness,
    policy_route,
)
from topolab.baselines import BaselineMetrics
from topolab.experiment import ExperimentCase
from topolab.problem import solve_problem


def runner():
    import sys

    folder = Path(__file__).resolve().parents[1] / "scripts"
    sys.path.insert(0, str(folder))
    try:
        spec = importlib.util.spec_from_file_location(
            "polish_runner", folder / "b4_10_post_plateau_probe.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(folder))


def test_metadata_plan_is_disjoint_exact_and_opens_no_bytes(monkeypatch):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("artifact opened"))
    plan = probe.plan()
    assert len(plan["cases"]["sentinel"]) == 9
    assert len(plan["cases"]["fresh"]) == 48
    assert len(plan["assignments"]["sentinel"]) == 108
    assert len(plan["assignments"]["fresh"]) == 576
    assert plan["fixed_primary"] == 17 and plan["polish_updates"] == 20
    assert plan["plan_sha256"] == "6583e32416d789e719e6bccc9707e7083d30acfefb7c2fc2b5ae314fd77aa983"
    assert plan["new_fits"] == 0 and not plan["final_access"]
    assert not {physical_fingerprint(c) for c in probe.fresh_cases()} & {
        physical_fingerprint(c) for c in previous.fresh_cases()
    }
    assert len(probe.sentinel_cases()) == len(probe.SENTINEL)
    for cohort in ("sentinel", "fresh"):
        rows = probe.assignments(cohort)
        for i in range(0, len(rows), 12):
            assert rows[i][1] == "uniform"
            assert {m for _, m in rows[i : i + 12]} == set(probe.METHODS)
    with pytest.raises(ValueError, match="unknown"):
        probe.cases("final")


def test_trigger_scope_and_design_change_precedence(b3_reference):
    case = next(
        c
        for c in probe.sentinel_cases()
        if c.problem.mesh.element_counts[0] == 24
        and c.problem.loads[0].direction == "y"
        and c.problem.optimization.volume_fraction == 0.5413
    )
    template = b3_reference.result
    states = tuple(
        template.history[0].model_copy(update={"iteration": i, "density_change": 0.02})
        for i in range(1, 12)
    )
    result = template.model_copy(update={"history": states})
    assert numerical.qualifies(case, result)
    for control in probe.sentinel_cases():
        if (
            control.problem.mesh.element_counts[0] == 12
            or control.problem.loads[0].direction == "z"
            or control.problem.optimization.volume_fraction >= 0.55
        ):
            assert not numerical.qualifies(control, result)
            assert (
                numerical.polish(control, result, lambda: pytest.fail("solver invoked")) is result
            )
    design_stop = result.model_copy(
        update={"history": (*states[:-1], states[-1].model_copy(update={"density_change": 0.01}))}
    )
    assert not numerical.qualifies(case, design_stop)
    assert not numerical.qualifies(case, result.model_copy(update={"converged": False}))
    assert not numerical.qualifies(case, result.model_copy(update={"history": states[:10]}))


@pytest.mark.parametrize("cap", [31, 25])
def test_continuation_equals_uninterrupted_anchored_oc_oracle(b3_reference, monkeypatch, cap):
    payload = b3_reference.entry.case.problem.model_dump(mode="json")
    payload["optimization"].update(max_iterations=cap, convergence_tolerance=1e-12)
    case = ExperimentCase.from_problem(
        type(b3_reference.entry.case.problem).model_validate(payload)
    )
    oracle = solve_problem(case.problem, termination_policy="design_max")
    assert len(oracle.history) == cap
    state = oracle.history[10]
    # Synthetic prefix enables the extension without exposing a production case.
    mesh, loads, constraints = numerical._case_system(case)
    analysis = numerical.evaluate_compliance(
        mesh,
        np.asarray(state.physical_density),
        loads,
        constraints,
        solid_modulus=case.problem.material.solid_modulus,
        minimum_modulus=case.problem.material.minimum_modulus,
        poisson_ratio=case.problem.material.poisson_ratio,
        penalty=case.problem.optimization.penalty,
    )
    prefix = oracle.model_copy(
        update={
            "history": oracle.history[:11],
            "design_density": state.design_density,
            "physical_density": state.physical_density,
            "compliance": state.compliance,
            "displacements": tuple(analysis.displacements),
            "reactions": tuple(analysis.reactions),
            "converged": True,
        }
    )
    monkeypatch.setattr(numerical, "qualifies", lambda *a: True)
    calls = []
    continued = numerical.polish(case, prefix, lambda: calls.append(1))
    assert continued.history == oracle.history
    assert continued.design_density == oracle.design_density
    assert continued.physical_density == oracle.physical_density
    assert continued.displacements == oracle.displacements
    assert continued.reactions == oracle.reactions
    assert continued.compliance == oracle.compliance
    assert len(calls) == 1 + 2 * (cap - 11)
    assert not continued.converged  # Strict unchanged terminal stop, and incomplete cap at 25.


def packet_sets(reference):
    witness = TerminalWitness.from_result(reference.result)
    metrics = BaselineMetrics(
        iterations=len(witness.trace),
        final_compliance=witness.result.compliance,
        physical_volume_error=0,
    )
    success = QueryAttempt(succeeded=True, timing=AttemptTiming(), metrics=metrics, state=witness)
    old, packets = {}, []
    for case_id, policy in probe.assignments("sentinel"):
        case = next(c for c in probe.sentinel_cases() if c.case_id == case_id)
        name, _, text = policy.partition("/")
        method = "P" if name == "W" else name
        route = policy_route(case, method)
        outcome = QueryOutcome(
            method=method, seed=int(text) if text else None, route=route, attempt=success
        )
        known = (case_id, policy) in {
            ("tlcase-v1-d9dc312497ba5ade125c1b6d432ca029e375718fe301909a75a5db8f9c7b3e3f", "P/17"),
            ("tlcase-v1-033f380c2181d9d1f94fc7f3d4b4a6507992c5e1a5004018bff779ca92add82a", "P/29"),
            ("tlcase-v1-033f380c2181d9d1f94fc7f3d4b4a6507992c5e1a5004018bff779ca92add82a", "P/43"),
            ("tlcase-v1-838e2ccc7891b194c1ab5d5b9854c658320e5b191a3d4ca38b78bbb4fc04d16e", "P/29"),
        }
        negative = (
            name == "P"
            and text == "29"
            and case.problem.mesh.element_counts[0] == 12
            and case.problem.loads[0].direction == "z"
        )
        failure = success.model_copy(
            update={
                "succeeded": False,
                "failure_code": "quality_error",
                "failure_type": "ValueError",
            }
        )
        old_outcome = (
            outcome.model_copy(update={"attempt": failure, "fallback": success})
            if known or negative
            else outcome
        )
        old[(case_id, policy)] = {"outcome": old_outcome.model_dump(mode="json")}
        packets.append(
            {
                "case_id": case_id,
                "policy": policy,
                "outcome": (old_outcome if negative else outcome).model_dump(mode="json"),
                "timing": {"wall_seconds": 10 if name == "uniform" else 5},
                "recording_allowance_seconds": 1.0,
            }
        )
    return packets, old


def test_sentinel_requires_repairs_no_regressions_and_full_cost(b3_reference):
    packets, old = packet_sets(b3_reference)
    decision = probe.sentinel_gate(packets, old)
    assert decision["sentinel_gate_passed"] and len(decision["repaired"]) == 4
    assert len(decision["negative_controls"]) == 2
    target = next(
        p
        for p in packets
        if p["policy"] == "P/17"
        and p["case_id"]
        == "tlcase-v1-d9dc312497ba5ade125c1b6d432ca029e375718fe301909a75a5db8f9c7b3e3f"
    )
    target["timing"]["wall_seconds"] = 1000
    assert not probe.sentinel_gate(packets, old)["sentinel_gate_passed"]
    target["timing"]["wall_seconds"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        probe.sentinel_gate(packets, old)
    with pytest.raises(ValueError, match="every"):
        probe.sentinel_gate(packets[:-1], old)
    target["timing"]["wall_seconds"] = 5
    target["outcome"] = old[(target["case_id"], "P/17")]["outcome"]
    decision = probe.sentinel_gate(packets, old)
    assert not decision["sentinel_gate_passed"] and decision["primary_failures"]


def test_changed_receipt_blocks_model_bytes_and_fresh_remains_sealed(tmp_path, monkeypatch):
    source = tmp_path / "b4-8-rollback-confirmation"
    source.mkdir()
    (source / "context.json").write_text("{}\n")
    monkeypatch.setattr(previous, "upstream_fits", lambda *a: pytest.fail("read checkpoints"))
    with pytest.raises(ValueError, match="before model or label"):
        probe.upstream_fits(tmp_path / "b4-5-weighted-terminal")
    module = runner()
    folder = tmp_path / "sentinel"
    (folder / "policy-audit").mkdir(parents=True)
    from topolab.b3_catalog import canonical_metadata_bytes
    from topolab.b4_telemetry import digest

    raw = canonical_metadata_bytes({"context_sha256": "a" * 64, "passed": False})
    (folder / "policy-audit/summary.json").write_bytes(raw)
    (folder / "independent_audit.json").write_bytes(
        canonical_metadata_bytes({"passed": True, "policy_summary_sha256": digest(raw)})
    )
    with pytest.raises(ValueError, match="sealed"):
        module.require_sentinel(tmp_path, "a" * 64)


def test_refinement_hook_excludes_baselines_specialists_and_uniform_fallback(
    b3_reference, monkeypatch
):
    witness = TerminalWitness.from_result(b3_reference.result)
    success = QueryAttempt(
        succeeded=True,
        timing=AttemptTiming(),
        metrics=BaselineMetrics(
            iterations=1, final_compliance=witness.result.compliance, physical_volume_error=0
        ),
        state=witness,
    )
    calls = []

    def fake_attempt(
        case, method, reference, checkpoint, model=None, neighbors=None, refinement=None
    ):
        calls.append((method, refinement))
        if method == "P" and refinement is not None:
            return success.model_copy(
                update={
                    "succeeded": False,
                    "failure_code": "quality_error",
                    "failure_type": "ValueError",
                }
            )
        return success

    monkeypatch.setattr(b3_queries, "_attempt", fake_attempt)
    models = {(r, 17): nn.Identity() for r in ("C", "P", "S")}

    def hook(*a):
        return None

    generalist = b3_reference.entry.case
    specialist = next(
        c for c in probe.sentinel_cases() if c.problem.optimization.volume_fraction >= 0.55
    )
    for case, method in (
        (generalist, "uniform"),
        (generalist, "C"),
        (specialist, "P"),
        (generalist, "P"),
    ):
        b3_queries.evaluate_query(
            case,
            method,
            None if method == "uniform" else 17,
            None,
            models,
            None,
            lambda: None,
            refinement=hook,
        )
    assert calls == [("uniform", None), ("C", None), ("P", None), ("P", hook), ("uniform", None)]


def test_default_runner_is_metadata_only(monkeypatch, capsys):
    import sys

    module = runner()
    monkeypatch.setattr(sys, "argv", ["probe"])
    monkeypatch.setattr(module, "screening_preflight", lambda *a: pytest.fail("opened labels"))
    module.main()
    assert json.loads(capsys.readouterr().out)["new_fits"] == 0


def test_independent_raw_arithmetic_reproduces_both_gates_without_helpers(b3_reference):
    path = Path(__file__).resolve().parents[1] / "scripts/b4_10_independent_audit.py"
    spec = importlib.util.spec_from_file_location("independent_polish_audit", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    packets, old = packet_sets(b3_reference)
    cases = {c.case_id: c.model_dump(mode="json") for c in probe.sentinel_cases()}
    module.close(probe.sentinel_gate(packets, old), module.sentinel_decision(packets, old, cases))
    reference = packets[0]["outcome"]["attempt"]
    fresh = []
    by_id = {c.case_id: c for c in probe.fresh_cases()}
    for case_id, policy in probe.assignments("fresh"):
        name, _, seed = policy.partition("/")
        method = "P" if name == "W" else name
        outcome = QueryOutcome(
            method=method,
            seed=int(seed) if seed else None,
            route=policy_route(by_id[case_id], method),
            attempt=QueryAttempt.model_validate(reference),
        )
        fresh.append(
            {
                "case_id": case_id,
                "policy": policy,
                "outcome": outcome.model_dump(mode="json"),
                "timing": {
                    "wall_seconds": 10 if name == "uniform" else (5 if name == "P" else 8),
                    "legacy_phase_seconds": 0,
                },
                "recording_allowance_seconds": 1.0,
            }
        )
    raw_cases = {k: c.model_dump(mode="json") for k, c in by_id.items()}
    result = probe.fresh_gate(fresh)
    module.close(result, module.fresh_decision(fresh, raw_cases))
    assert result["polish_gate_passed"] and result["fixed_primary"] == 17
    target = next(p for p in fresh if p["policy"] == "P/17")
    failed = dict(
        target["outcome"]["attempt"],
        succeeded=False,
        failure_code="quality_error",
        failure_type="ValueError",
    )
    target["outcome"] = dict(target["outcome"], attempt=failed, fallback=reference)
    result = probe.fresh_gate(fresh)
    assert not result["polish_gate_passed"] and result["passing_seeds"] == [29, 43]
    module.close(result, module.fresh_decision(fresh, raw_cases))
