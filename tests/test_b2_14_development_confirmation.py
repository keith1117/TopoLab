"""Frozen B2.14 population and development policy-selection rules."""

import sys
from collections import Counter
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import b2_14_development_confirmation as runner  # noqa: E402

from topolab.b2_13_routing import route_case  # noqa: E402


def test_plan_is_disjoint_and_covers_each_fixed_stratum() -> None:
    fresh, exposed = runner.cohorts()
    plan = runner.plan_payload(fresh, exposed)
    assert plan["plan_sha256"] == runner.EXPECTED_PLAN_SHA256
    assert len(fresh) == 24 and len(exposed) == 588
    assert set(plan["screen_case_ids"]).isdisjoint(plan["exposed_case_ids"])
    assert set(runner.VOLUMES).isdisjoint(plan["exposed_volumes"])
    assert len({
        (case.problem.mesh.element_counts, case.problem.loads[0].direction,
         case.problem.optimization.volume_fraction, runner._point_node(case))
        for case in fresh
    }) == 24
    assert Counter(route_case(case) for case in fresh) == {
        "vector_29": 12, "context_17": 6, "context_43": 4, "uniform_reject": 2,
    }


def _passing_metrics() -> tuple[dict[str, float], dict[str, float]]:
    means = {
        f"{method}_{scale}": 0.8
        for method in runner.METHODS for scale in ("small", "large")
    }
    means.update({f"{method}_overall": 0.8 for method in runner.METHODS})
    directions = {
        f"{method}_{scale}_{direction}": 0.8
        for method in runner.METHODS for scale in ("small", "large")
        for direction in ("y", "z")
    }
    return means, directions


def test_selection_requires_material_router_gain_and_no_extra_failures() -> None:
    means, directions = _passing_metrics()
    means["routed_overall"] = 0.75
    eligible, selected = runner.select_policy(means, directions, Counter(), Counter())
    assert len(eligible) == 5 and selected == "routed"
    means["routed_overall"] = 0.76  # Exactly 95% is not a strict advantage.
    assert runner.select_policy(means, directions, Counter(), Counter())[1] == "vector_29"
    means["routed_overall"] = 0.70
    assert runner.select_policy(
        means, directions, Counter({"routed": 1}), Counter()
    )[1] == "vector_29"


def test_ineligible_quality_or_direction_cannot_be_selected() -> None:
    means, directions = _passing_metrics()
    means["routed_overall"] = 0.50
    directions["routed_large_y"] = 1.01
    assert runner.select_policy(means, directions, Counter(), Counter())[1] == "vector_29"
    for method in runner.FIXED:
        means[f"{method}_large"] = 0.91
    assert runner.select_policy(means, directions, Counter(), Counter())[1] is None
    directions["routed_large_y"] = 0.8
    assert runner.select_policy(
        means, directions, Counter(), Counter({"routed": 1})
    )[1] is None


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
