"""Synthetic queries: routes, paid failure/rejection and terminal witnesses."""

import numpy as np
import pytest
from torch import nn

import topolab.b3_queries as queries
from topolab.b3_access import B3Access
from topolab.b3_queries import (
    METHODS,
    AttemptTiming,
    QueryAttempt,
    QueryResourceExceeded,
    TerminalWitness,
    audit_witness,
    evaluate_query,
    policy_route,
)
from topolab.baselines import validate_refinement_quality
from topolab.mesh import generate_structured_hex8
from topolab.simp import apply_density_filter, build_density_filter


def test_exact_method_order_and_fixed_specialist_route() -> None:
    assert len(METHODS) == 15
    assert METHODS[:3] == (
        ("uniform", None),
        ("physics_heuristic", None),
        ("nearest_neighbor", None),
    )
    assert METHODS[3:] == tuple(
        (m, s) for m in ("C", "P", "A", "P_without_S") for s in (17, 29, 43)
    )
    for e in B3Access(consumer="screen").case_entries():
        specialist = (
            e.case.problem.mesh.element_counts == (24, 12, 6)
            and e.case.problem.loads[0].direction == "y"
            and e.case.problem.optimization.volume_fraction >= 0.55
        )
        for m in ("C", "P", "A"):
            assert policy_route(e.case, m) == ("specialist" if specialist else "generalist")
        assert policy_route(e.case, "P_without_S") == "generalist"
    for e in B3Access(consumer="final_query").case_entries():
        if e.role == "final_ood":
            assert policy_route(e.case, "P") == "reject"


@pytest.fixture
def sample(b3_record_factory):  # type: ignore[no-untyped-def]
    entry = B3Access(consumer="screen").case_entries()[0]
    result = b3_record_factory(entry).result
    metrics = validate_refinement_quality(entry.case, result, None)
    return entry, result, metrics


def test_query_records_charged_quality_failure_and_fresh_fallback(sample, monkeypatch):  # type: ignore[no-untyped-def]
    entry, result, metrics = sample
    state = TerminalWitness.from_result(result)
    failed = QueryAttempt(
        succeeded=False,
        failure_code="quality_error",
        failure_type="SyntheticFailure",
        timing=AttemptTiming(refinement_seconds=3),
        metrics=metrics,
        state=state,
    )
    successful = QueryAttempt(
        succeeded=True, timing=AttemptTiming(refinement_seconds=5), metrics=metrics, state=state
    )
    calls = []

    def attempt(case, method, reference, checkpoint, model=None, neighbors=None):  # type: ignore[no-untyped-def]
        calls.append((method, model))
        return failed if len(calls) == 1 else successful

    monkeypatch.setattr(queries, "_attempt", attempt)
    model = nn.Identity()
    outcome = evaluate_query(
        entry.case,
        "P_without_S",
        17,
        metrics.final_compliance,
        {("P", 17): model},
        None,
        lambda: None,
    )
    assert calls == [("P_without_S", model), ("uniform", None)]
    assert not outcome.attempt.succeeded and outcome.fallback.succeeded
    assert outcome.operational == outcome.fallback
    assert outcome.seconds >= 8 and outcome.route == "generalist"


def test_x_rejection_skips_prediction_and_pays_uniform(sample, monkeypatch):  # type: ignore[no-untyped-def]
    _, result, metrics = sample
    case = next(
        e.case for e in B3Access(consumer="final_query").case_entries() if e.role == "final_ood"
    )
    calls = []

    def attempt(case, method, reference, checkpoint, model=None, neighbors=None):  # type: ignore[no-untyped-def]
        calls.append(method)
        assert model is None
        return QueryAttempt(
            succeeded=True,
            timing=AttemptTiming(refinement_seconds=5),
            metrics=metrics,
            state=TerminalWitness.from_result(result),
        )

    monkeypatch.setattr(queries, "_attempt", attempt)
    outcome = evaluate_query(case, "P", 17, None, {}, None, lambda: None)
    assert calls == ["uniform"]
    assert outcome.route == "reject" and outcome.attempt is None
    assert outcome.operational == outcome.fallback and outcome.seconds >= 5


def test_real_quality_adapter_and_witness_use_same_synthetic_state(sample, monkeypatch):  # type: ignore[no-untyped-def]
    entry, result, metrics = sample
    monkeypatch.setattr(queries, "solve_problem", lambda *args, **kwargs: result)
    outcome = evaluate_query(entry.case, "uniform", None, None, {}, None, lambda: None)
    assert outcome.attempt.succeeded and outcome.attempt.metrics == metrics
    assert audit_witness(entry.case, outcome.attempt.state, None, accepted=True) == metrics
    assert outcome.attempt.timing.decision_seconds > 0


def test_solver_resource_stop_propagates_without_fallback(sample, monkeypatch):  # type: ignore[no-untyped-def]
    entry, _, _ = sample
    calls = []

    def solve(*args, iteration_callback, **kwargs):  # type: ignore[no-untyped-def]
        calls.append("solve")
        iteration_callback(None)
        pytest.fail("resource callback returned")

    def pulse():  # type: ignore[no-untyped-def]
        if calls:
            raise QueryResourceExceeded("synthetic cap")

    monkeypatch.setattr(queries, "solve_problem", solve)
    with pytest.raises(QueryResourceExceeded):
        evaluate_query(entry.case, "uniform", None, None, {}, None, pulse)
    assert calls == ["solve"]


@pytest.mark.parametrize("change", ["compliance", "filter", "volume", "converged", "trace"])
def test_independent_witness_rejects_changed_numerical_evidence(sample, change):  # type: ignore[no-untyped-def]
    entry, result, _ = sample
    payload = TerminalWitness.from_result(result).model_dump(mode="json")
    if change == "compliance":
        payload["result"]["compliance"] *= 1.01
        payload["result"]["history"][-1]["compliance"] = payload["result"]["compliance"]
        payload["trace"][-1]["compliance"] = payload["result"]["compliance"]
    elif change == "filter":
        payload["result"]["physical_density"][0] += 0.01
        payload["result"]["history"][-1]["physical_density"][0] += 0.01
    elif change == "volume":
        payload["result"]["history"][-1]["volume_fraction"] += 0.01
        payload["trace"][-1]["volume_fraction"] += 0.01
    elif change == "converged":
        payload["result"]["converged"] = False
    else:
        payload["trace"][-1]["iteration"] = 2
    with pytest.raises(ValueError):
        audit_witness(entry.case, TerminalWitness.model_validate(payload), None, accepted=True)


def test_compact_witness_keeps_exact_eleven_state_plateau(sample, monkeypatch):  # type: ignore[no-untyped-def]
    entry, result, _ = sample
    problem = entry.case.problem
    nx, ny, nz = problem.mesh.element_counts
    mesh = generate_structured_hex8(nx, ny, nz, lengths=problem.mesh.lengths)
    density_filter = build_density_filter(mesh, problem.optimization.filter_radius)
    checker = (-1.0) ** np.indices((nz, ny, nx)).sum(axis=0).reshape(-1)
    designs = [problem.optimization.volume_fraction + 0.01 * sign * checker for sign in (-1, 1)]
    changes = float(np.max(np.abs(designs[1] - designs[0])))
    history = []
    for i in range(1, 21):
        design = designs[i % 2]
        physical = apply_density_filter(density_filter, design)
        history.append(
            result.history[0].model_copy(
                update={
                    "iteration": i,
                    "density_change": changes,
                    "volume_fraction": float(np.mean(physical)),
                    "design_density": tuple(design),
                    "physical_density": tuple(physical),
                }
            )
        )
    last = history[-1]
    synthetic = result.model_copy(
        update={
            "history": tuple(history),
            "design_density": last.design_density,
            "physical_density": last.physical_density,
        }
    )
    # Isolate the plateau algebra; the synthetic oscillation is not a production solve.
    monkeypatch.setattr(queries, "_evaluate_case_density", lambda *args: result.compliance)
    witness = TerminalWitness.from_result(synthetic)
    assert len(witness.trace) == 20 and len(witness.result.history) == 11
    assert witness.result.history[0].iteration == 10
    assert audit_witness(entry.case, witness, None, accepted=True).iterations == 20
    payload = witness.model_dump(mode="json")
    payload["result"]["history"][-1]["density_change"] = 0.025
    payload["trace"][-1]["density_change"] = 0.025
    with pytest.raises(ValueError, match="design change"):
        audit_witness(entry.case, TerminalWitness.model_validate(payload), None, accepted=True)
