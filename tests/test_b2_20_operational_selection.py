"""B2.20 sealed cohorts and quality-first operational selection."""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_20_operational_selection import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    _selection_decision,
    cohorts,
    plan_payload,
    reference_gate,
)

from topolab.b2_6_trajectory import fit_trajectory_seed  # noqa: E402


def test_plan_freezes_disjoint_selection_and_screen_cohorts() -> None:
    groups, selection, screen, blocked = cohorts()
    plan = plan_payload(groups, selection, screen, blocked)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(groups["train"]) == 468
    assert len(groups["validation"]) == 12
    assert len(selection) == 12
    assert len(screen) == 24
    assert len(blocked) == 676
    assert len({case.case_id for case in (*blocked, *selection, *screen)}) == 712
    assert set(plan["selection_volumes"]).isdisjoint(plan["screen_volumes"])
    assert set(plan["selection_volumes"] + plan["screen_volumes"]).isdisjoint(
        plan["blocked_volumes"]
    )
    assert {case.problem.mesh.element_counts for case in screen} == {
        (12, 6, 3), (24, 12, 6)
    }
    assert {case.problem.loads[0].direction for case in screen} == {"y", "z"}
    index = {"rows": [{"case_id": case.case_id, "uniform": {
        "succeeded": True,
        "candidate": {"final_compliance": 1.0, "physical_volume_error": 0.0},
    }} for case in selection], "elapsed_seconds": 10.0, "peak_rss_bytes": 1000}
    assert reference_gate(index, selection, 1800.0)
    index["rows"][0]["uniform"]["candidate"]["physical_volume_error"] = 0.006
    assert not reference_gate(index, selection, 1800.0)


def test_capture_epoch_schedule_rejects_adaptive_or_invalid_choices() -> None:
    with pytest.raises(ValueError, match="capture epochs"):
        fit_trajectory_seed((), (), seed=17, capture_epochs=(120, 80))
    with pytest.raises(ValueError, match="capture epochs"):
        fit_trajectory_seed((), (), seed=17, capture_epochs=(80, 80))
    with pytest.raises(ValueError, match="capture epochs"):
        fit_trajectory_seed((), (), seed=17, capture_epochs=(201,))


def test_operational_selection_prioritizes_fewer_quality_failures(tmp_path: Path) -> None:
    (tmp_path / "selection_index.json").write_bytes(b"{}")
    cases = []
    for scale in ("small", "large"):
        for direction in ("y", "z"):
            cases.extend({"scale": scale, "direction": direction} for _ in range(3))
    rows = []
    for position, case in enumerate(cases):
        outcomes = []
        for seed in (17, 29, 43):
            for epoch in (80, 120):
                outcomes.append({"method": f"candidate_{seed}_{epoch}",
                                 "succeeded": epoch == 80 or position != 0,
                                 "paired_time_ratio": 0.95 if epoch == 80 else 0.50})
        rows.append({"case": case, "outcomes": outcomes})
    index = {"context": {"plan_sha256": "fixture"}, "rows": rows,
             "elapsed_seconds": 100.0, "peak_rss_bytes": 1000}
    fits = {"rows": [{"seed": seed, "candidates": [
        {"epoch": epoch, "checkpoint_sha256": f"{seed}-{epoch}"}
        for epoch in (80, 120)]} for seed in (17, 29, 43)]}
    decision = _selection_decision(tmp_path, index, fits)
    assert [(row["seed"], row["epoch"]) for row in decision["selected"]] == [
        (17, 80), (29, 80), (43, 80)
    ]
