"""Frozen B2.13 route and charged rejection behavior."""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import b2_13_routing as runner  # noqa: E402

from topolab.b2_13_routing import route_case  # noqa: E402
from topolab.experiment import ExperimentCase  # noqa: E402
from topolab.problem import TopologyProblem  # noqa: E402


def test_frozen_routes_cover_disjoint_two_scale_screen() -> None:
    fresh, exposed = runner.cohorts()
    plan = runner.plan_payload(fresh, exposed)
    assert plan["plan_sha256"] == runner.EXPECTED_PLAN_SHA256
    assert len(fresh) == 12
    assert len(runner.METHODS) == 12
    assert set(plan["screen_case_ids"]).isdisjoint(plan["exposed_case_ids"])
    assert set(runner.VOLUMES).isdisjoint(plan["exposed_volumes"])
    routes = {
        (case.problem.mesh.element_counts[0], case.problem.loads[0].direction,
         case.problem.optimization.volume_fraction): route_case(case)
        for case in fresh
    }
    assert len(routes) == 12
    for volume in runner.VOLUMES:
        assert routes[(12, "y", volume)] == "vector_29"
        assert routes[(12, "z", volume)] == "context_17"
        assert routes[(24, "z", volume)] == "vector_29"
        assert routes[(24, "y", volume)] == (
            "uniform_reject" if volume >= 0.55 else "context_43"
        )


def test_rejection_runs_and_charges_fresh_uniform(monkeypatch: pytest.MonkeyPatch) -> None:
    fresh, _ = runner.cohorts()
    case = next(case for case in fresh if route_case(case) == "uniform_reject")
    calls = []

    def uniform_attempt(*args: object, **kwargs: object) -> dict[str, object]:
        calls.append((args, kwargs))
        return {
            "succeeded": True,
            "candidate": {"final_compliance": 10.0, "physical_volume_error": 0.0},
            "timing": {"setup_seconds": 0.1, "refinement_seconds": 4.9},
        }

    monkeypatch.setattr(runner, "_attempt", uniform_attempt)
    reference = {
        "uniform_reference_compliance": 10.0,
        "timing": {
            "setup_seconds": 0.0, "decision_seconds": 0.0,
            "fallback_seconds": 0.0, "end_to_end_seconds": 5.0,
        },
    }
    outcome = runner.routed_result(case, reference, {}, {})
    assert len(calls) == 1
    assert calls[0][1] == {"method": "uniform", "reference_compliance": None}
    assert outcome["rejected"] and outcome["succeeded"]
    assert not outcome["fallback_used"] and outcome["candidate"] is None
    assert outcome["timing"]["rejection_uniform_seconds"] == pytest.approx(5.0)
    assert outcome["paired_time_ratio"] >= 1.0


def test_outside_fixed_numerical_workload_rejects_to_uniform() -> None:
    fresh, _ = runner.cohorts()
    case = next(case for case in fresh if route_case(case) == "vector_29")
    payload = case.problem.model_dump(mode="json")
    payload["material"]["solid_modulus"] = 1200.0
    changed = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
    assert route_case(changed) == "uniform_reject"


def test_reference_failure_stops_screen_before_models() -> None:
    fresh, _ = runner.cohorts()
    index = {
        "rows": [
            {
                "case_id": case.case_id,
                "uniform": {
                    "succeeded": True,
                    "candidate": {
                        "final_compliance": 1.0,
                        "physical_volume_error": 0.0,
                    },
                },
            }
            for case in fresh
        ],
        "elapsed_seconds": 100.0,
        "peak_rss_bytes": 100_000_000,
    }
    assert runner.reference_gate(index, fresh)
    index["rows"][0]["uniform"]["succeeded"] = False
    assert not runner.reference_gate(index, fresh)
