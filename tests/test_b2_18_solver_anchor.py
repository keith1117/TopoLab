"""B2.18 frozen cohort and physical-state anchor tests."""

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import b2_18_solver_anchor as runner  # noqa: E402


def test_plan_separates_new_cases_from_exposed_and_reserved() -> None:
    fresh, exposed, reserved = runner.cohorts()
    plan = runner.plan_payload(fresh, exposed, reserved)
    assert plan["plan_sha256"] == runner.EXPECTED_PLAN_SHA256
    assert len(fresh) == 4 and len(exposed) == 636 and len(reserved) == 24
    assert len(plan["sentinel_case_ids"]) == 4
    assert not (set(plan["fresh_case_ids"]) &
                set(plan["exposed_case_ids"] + plan["b217_unopened_reserved_ids"]))


@pytest.mark.parametrize("quality_passes", [True, False])
def test_anchor_uses_physical_two_step_state_and_charges_fallback(
    monkeypatch: pytest.MonkeyPatch, quality_passes: bool
) -> None:
    case = runner.cohorts()[0][0]
    nx, ny, nz = case.problem.mesh.element_counts
    count = nx * ny * nz
    calls = []
    monkeypatch.setattr(runner, "_predict", lambda *args, **kwargs: np.full(
        (1, nz, ny, nx), 0.6, dtype=np.float32))
    monkeypatch.setattr(runner, "project_design_density", lambda _case, raw: SimpleNamespace(
        design_density=np.asarray(raw).reshape(-1)))

    def fake_solve(problem: object, *, termination_policy: str) -> SimpleNamespace:
        calls.append(problem)
        if len(calls) == 1:
            return SimpleNamespace(history=(object(), object()),
                                   design_density=tuple([0.4] * count))
        return SimpleNamespace(history=(object(),), converged=True)

    monkeypatch.setattr(runner, "solve_problem", fake_solve)

    def fake_quality(*args: object) -> SimpleNamespace:
        if not quality_passes:
            raise ValueError("candidate terminal quality failed")
        return SimpleNamespace(model_dump=lambda **kwargs: {
            "final_compliance": 1.0, "physical_volume_error": 0.0})

    monkeypatch.setattr(runner, "validate_refinement_quality", fake_quality)
    monkeypatch.setattr(runner, "_safe_metrics", lambda *args: {
        "final_compliance": 1.01, "physical_volume_error": 0.0})
    monkeypatch.setattr(runner, "_uniform_fallback", lambda *args: (
        {"final_compliance": 1.0, "physical_volume_error": 0.0}, 5.0))
    reference = {"uniform_reference_compliance": 1.0,
                 "timing": {"end_to_end_seconds": 10.0}}
    outcome = runner.anchored_result(case, reference, object())
    assert [problem.optimization.max_iterations for problem in calls] == [2, 360]
    assert np.allclose(calls[1].initial_density, 0.5)
    assert outcome["anchor_updates"] == 2
    assert outcome["succeeded"] is quality_passes
    assert outcome["fallback_used"] is not quality_passes
    assert outcome["timing"]["fallback_seconds"] == (0.0 if quality_passes else 5.0)
    assert outcome["timing"]["end_to_end_seconds"] == pytest.approx(
        sum(value for key, value in outcome["timing"].items()
            if key != "end_to_end_seconds"))
