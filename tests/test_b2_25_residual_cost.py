"""B2.25 frozen identity and optimistic-bound arithmetic."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from b2_25_residual_cost import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    audited_rows,
    choose_next,
    effective_ratio,
    plan_payload,
)


def test_frozen_plan() -> None:
    plan = plan_payload()
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(plan["case_ids"]) == len(set(plan["case_ids"])) == 24


def test_optimistic_bound_arithmetic() -> None:
    row = {"case": {"scale": "large", "direction": "z"},
           "outcomes": [{"timing": {"end_to_end_seconds": 10.0}}]}
    item = {"timing": {"end_to_end_seconds": 15.0, "fallback_seconds": 4.0}}
    assert effective_ratio(row, item, "measured") == 1.5
    assert effective_ratio(row, item, "fallback_free") == 1.1
    assert effective_ratio(row, item, "z_zero") == 0.0
    assert effective_ratio(row, item, "combined") == 0.0
    row["case"]["direction"] = "y"
    assert effective_ratio(row, item, "z_zero") == 1.5
    assert effective_ratio(row, item, "combined") == 1.1


def test_ordered_decision() -> None:
    bounds = {name: {str(seed): {"speed_bounds_met": False}
                     for seed in (17, 29, 43)}
              for name in ("fallback_free", "z_zero", "combined")}
    assert choose_next(bounds) == "method_class_reassessment"
    for bound, expected in (("combined", "joint_generalist"),
                            ("z_zero", "z_refinement"),
                            ("fallback_free", "y_reliability")):
        bounds[bound]["17"]["speed_bounds_met"] = True
        bounds[bound]["29"]["speed_bounds_met"] = True
        assert choose_next(bounds) == expected


def test_missing_source_index_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        audited_rows(tmp_path, {"case_ids": []})
