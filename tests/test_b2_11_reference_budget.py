"""B2.11 versioned iteration budget and exposure boundaries."""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_6_trajectory import _small_case  # noqa: E402
from b2_11_reference_budget import (  # noqa: E402
    BUDGET,
    EXPECTED_PLAN_SHA256,
    METHODS,
    VOLUMES,
    cohorts,
    plan_payload,
    versioned_case,
)

from topolab.b2_5_evaluation import _attempt  # noqa: E402


def test_budget_only_changes_case_identity_and_preserves_early_stop() -> None:
    source = _small_case(0.4375, "y", 2, 2)
    repaired = versioned_case(source)
    assert source.problem.optimization.max_iterations == 240
    assert repaired.problem.optimization.max_iterations == BUDGET == 360
    assert repaired.case_id != source.case_id
    original = source.problem.model_dump(mode="json")
    updated = repaired.problem.model_dump(mode="json")
    original["optimization"]["max_iterations"] = BUDGET
    assert updated == original
    before = _attempt(source, method="uniform", reference_compliance=None)
    after = _attempt(repaired, method="uniform", reference_compliance=None)
    assert before["succeeded"] and after["succeeded"]
    assert before["candidate"]["iterations"] == after["candidate"]["iterations"]
    assert before["candidate"]["final_compliance"] == pytest.approx(
        after["candidate"]["final_compliance"], rel=1e-10
    )


def test_cohorts_are_complete_disjoint_and_versioned() -> None:
    source, repaired, fresh, exposed = cohorts()
    plan = plan_payload(source, repaired, fresh, exposed)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(source) == len(repaired) == len(fresh) == 12
    assert len(METHODS) == 11
    assert {case.problem.optimization.volume_fraction for case in fresh} == set(VOLUMES)
    assert {case.problem.loads[0].direction for case in fresh} == {"y", "z"}
    assert {case.problem.mesh.element_counts for case in fresh} == {(12, 6, 3), (24, 12, 6)}
    assert all(case.problem.optimization.max_iterations == BUDGET for case in (*repaired, *fresh))
    assert len(set(plan["screen_case_ids"])) == 12
    assert set(plan["screen_case_ids"]).isdisjoint(set(plan["exposed_case_ids"]))
    assert set(VOLUMES).isdisjoint(set(plan["exposed_volumes"]))
    assert plan["source_case_ids"] == [case.case_id for case in source]
    assert plan["repaired_case_ids"] == [case.case_id for case in repaired]
