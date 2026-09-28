"""Frozen B2.16 retrospective decision and timing-floor checks."""

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import b2_16_method_class as runner  # noqa: E402


def _item(ratio: float, *, succeeded: bool = True) -> dict[str, object]:
    return {"paired_time_ratio": ratio, "succeeded": succeeded,
            "timing": {"end_to_end_seconds": 2.0, "refinement_seconds": 1.2},
            "candidate": {"iterations": 12}}


def _records() -> runner.Records:
    records = {}
    for scale in runner.SCALES:
        for direction in runner.DIRECTIONS:
            for tier in runner.VOLUME_TIERS:
                for position in runner.POSITIONS:
                    cell = (scale, direction, tier, position)
                    records[cell] = {"outcomes": {
                        "uniform": _item(1.0),
                        "vector_29": _item(0.8),
                        "context_17": _item(0.8),
                        "context_43": _item(0.8),
                        "old_routed": _item(0.8),
                        "new_routed": _item(0.7),
                        "physics_heuristic": _item(1.2),
                        "nearest_neighbor": _item(1.1),
                    }}
    return records


def test_plan_identity_and_position_cell() -> None:
    assert runner.plan_payload()["plan_sha256"] == runner.EXPECTED_PLAN_SHA256
    b214 = runner.COHORTS["b214"]
    assert runner.case_cell({
        "scale": "small", "direction": "y", "volume": 0.3125,
        "node": 12 + 13 * (3 + 7 * 1),
    }, b214) == ("small", "y", "low", "lower_z")
    assert runner.case_cell({
        "scale": "large", "direction": "z", "volume": 0.5925,
        "node": 24 + 25 * (10 + 13 * 4),
    }, b214) == ("large", "z", "high", "upper_z")


def test_hindsight_selector_excludes_fast_failed_action() -> None:
    records = _records()
    row = next(iter(records.values()))
    row["outcomes"]["vector_29"] = _item(0.1, succeeded=False)
    row["outcomes"]["context_17"] = _item(0.6)
    assert runner.best_successful_action(row) == "context_17"


def test_transferred_failure_pays_full_cost_and_count() -> None:
    records = _records()
    choices = {cell: "vector_29" for cell in records}
    assert runner.metrics(records, choices)["gate_passed"]
    for cell in list(records)[:3]:
        records[cell]["outcomes"]["vector_29"] = _item(1.5, succeeded=False)
    result = runner.metrics(records, choices)
    assert result["failures"] == 3
    assert not result["gate_passed"]
    assert result["overall"] > 0.8


def test_perfect_failure_rejection_is_only_a_cost_floor() -> None:
    records = _records()
    failed = ("large", "y", "high", "upper_z")
    records[failed]["outcomes"]["new_routed"] = _item(1.5, succeeded=False)
    result = runner.ideal_rescue(records)
    assert result["rescued_cells"] == [list(failed)]
    assert result["ideal_gate_passed"]
    assert result["pilot_floor_feasible"]
    assert result["max_equal_pilot_seconds_per_at_risk_case_supremum"] > 0.1
