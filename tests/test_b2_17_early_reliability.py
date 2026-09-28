"""Frozen B2.17 cohort, early decision, and charged rejection tests."""

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import b2_17_early_reliability as runner  # noqa: E402


def test_plan_is_frozen_and_physically_disjoint() -> None:
    fresh, exposed = runner.cohorts()
    plan = runner.plan_payload(fresh, exposed)
    assert plan["plan_sha256"] == runner.EXPECTED_PLAN_SHA256
    assert len(fresh) == 24 and len(exposed) == 636
    assert set(plan["fresh_case_ids"]).isdisjoint(plan["exposed_case_ids"])
    assert sum(runner._at_risk(case) for case in fresh) == 2


@pytest.mark.parametrize("early_compliance,expected_reject", [(11.0, True), (9.0, False)])
def test_early_signal_charges_shadow_and_stops_only_rejected_solve(
    monkeypatch: pytest.MonkeyPatch, early_compliance: float, expected_reject: bool
) -> None:
    case = next(case for case in runner.cohorts()[0] if runner._at_risk(case))
    calls = []
    monkeypatch.setattr(runner, "_predict", lambda *args, **kwargs: np.ones((1, 6, 12, 24)))
    monkeypatch.setattr(runner, "project_design_density", lambda *args: SimpleNamespace(
        design_density=np.full(24 * 12 * 6, 0.5)))

    def fake_solve(problem: object, *, termination_policy: str,
                   iteration_callback: object = None) -> SimpleNamespace:
        calls.append(problem.optimization.max_iterations)  # type: ignore[attr-defined]
        if iteration_callback is None:
            return SimpleNamespace(history=[SimpleNamespace(compliance=12.0),
                                            SimpleNamespace(compliance=10.0)])
        iteration_callback(SimpleNamespace(iteration=1, compliance=12.0))  # type: ignore[operator]
        iteration_callback(SimpleNamespace(iteration=2, compliance=early_compliance))  # type: ignore[operator]
        return SimpleNamespace(history=[], converged=True)

    monkeypatch.setattr(runner, "solve_problem", fake_solve)
    monkeypatch.setattr(runner, "_uniform_fallback", lambda *args: (
        {"final_compliance": 1.0, "physical_volume_error": 0.0}, 5.0))
    monkeypatch.setattr(runner, "validate_refinement_quality", lambda *args: SimpleNamespace(
        model_dump=lambda **kwargs: {"final_compliance": 1.0, "physical_volume_error": 0.0}))
    reference = {"uniform_reference_compliance": 1.0,
                 "timing": {"end_to_end_seconds": 5.0}}
    outcome = runner.probe_result(case, reference, object())
    assert calls == [2, 360]
    assert outcome["rejected"] is expected_reject
    assert outcome["signal"] == pytest.approx(early_compliance / 10.0)
    assert outcome["timing"]["end_to_end_seconds"] == pytest.approx(
        sum(value for key, value in outcome["timing"].items()
            if key != "end_to_end_seconds"))
    assert outcome["timing"]["rejection_uniform_seconds"] == (5.0 if expected_reject else 0.0)
    assert outcome["predecision_seconds"] < outcome["timing"]["end_to_end_seconds"]
