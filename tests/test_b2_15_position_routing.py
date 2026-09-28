"""Frozen B2.15 position-aware route, disjoint cohort, and charged Gate."""

import sys
from collections import Counter
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import b2_15_position_routing as runner  # noqa: E402

from topolab.b2_15_position_routing import route_case  # noqa: E402
from topolab.experiment import ExperimentCase  # noqa: E402
from topolab.problem import TopologyProblem  # noqa: E402


def test_plan_is_disjoint_and_position_routes_are_frozen() -> None:
    fresh, exposed = runner.cohorts()
    plan = runner.plan_payload(fresh, exposed)
    assert plan["plan_sha256"] == runner.EXPECTED_PLAN_SHA256
    assert len(fresh) == 24 and len(exposed) == 612
    assert set(plan["screen_case_ids"]).isdisjoint(plan["exposed_case_ids"])
    assert set(runner.VOLUMES).isdisjoint(plan["exposed_volumes"])
    assert Counter(route_case(case) for case in fresh) == {
        "context_43": 14, "context_17": 5,
        "vector_29": 4, "uniform_reject": 1,
    }


def test_unsupported_numerics_and_boundary_load_reject() -> None:
    fresh, _ = runner.cohorts()
    case = next(case for case in fresh if route_case(case) == "context_43")
    payload = case.problem.model_dump(mode="json")
    payload["material"]["solid_modulus"] = 1200.0
    changed = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
    assert route_case(changed) == "uniform_reject"


def test_rejection_charges_new_uniform(monkeypatch: pytest.MonkeyPatch) -> None:
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
    outcome = runner.new_routed_result(case, reference, {}, {})
    assert len(calls) == 1
    assert calls[0][1] == {"method": "uniform", "reference_compliance": None}
    assert outcome["rejected"] and outcome["succeeded"]
    assert not outcome["fallback_used"] and outcome["candidate"] is None
    assert outcome["timing"]["rejection_uniform_seconds"] == pytest.approx(5.0)
    assert outcome["paired_time_ratio"] >= 1.0


def test_new_route_gate_requires_all_advantages() -> None:
    means = {f"{method}_overall": 0.8 for method in runner.METHODS}
    means["new_routed_overall"] = 0.70
    assert runner.new_route_gate(means, [*runner.FIXED, "new_routed"], Counter())
    means["new_routed_overall"] = 0.77
    assert not runner.new_route_gate(means, [*runner.FIXED, "new_routed"], Counter())
    means["new_routed_overall"] = 0.70
    assert not runner.new_route_gate(
        means, [*runner.FIXED, "new_routed"], Counter({"new_routed": 1})
    )
    assert not runner.new_route_gate(means, list(runner.FIXED), Counter())


def test_reference_failure_stops_candidate_stage() -> None:
    fresh, _ = runner.cohorts()
    index = {
        "rows": [{
            "case_id": case.case_id,
            "uniform": {"succeeded": True, "candidate": {
                "final_compliance": 1.0, "physical_volume_error": 0.0,
            }},
        } for case in fresh],
        "elapsed_seconds": 100.0,
        "peak_rss_bytes": 100_000_000,
    }
    assert runner.reference_gate(index, fresh)
    index["rows"][0]["uniform"]["succeeded"] = False
    assert not runner.reference_gate(index, fresh)
