"""B2.22 specialist route, case objective, and frozen screen Gate."""

import sys
from pathlib import Path

import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_22_y_specialist import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    METHODS,
    cohorts,
    plan_payload,
    screen_summary,
    specialist_case,
)

from topolab.b2_6_trajectory import case_weighted_loss  # noqa: E402


def test_frozen_population_and_route() -> None:
    groups, screen, blocked = cohorts()
    plan = plan_payload(groups, screen, blocked)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(groups["train"]) == 468
    assert len(groups["validation"]) == 12
    assert len(plan["high_weight_train_case_ids"]) == 52
    assert len(plan["selection_validation_case_ids"]) == 2
    assert len(blocked) == 736
    assert len(screen) == 24
    assert sum(map(specialist_case, screen)) == 2


def test_case_weighted_loss_normalizes_per_case() -> None:
    prediction = torch.tensor([[[[[1.0]]]], [[[[3.0]]]]])
    target = torch.zeros_like(prediction)
    assert case_weighted_loss(prediction, target, torch.tensor([1.0, 3.0])).item() == 7.0
    with pytest.raises(ValueError, match="weights"):
        case_weighted_loss(prediction, target, torch.tensor([1.0, 0.0]))


def test_screen_gate_requires_specialist_quality(tmp_path: Path) -> None:
    _, cases, _ = cohorts()
    (tmp_path / "screen_index.json").write_text("{}")
    rows = []
    for case in cases:
        scale = "small" if case.problem.mesh.element_counts[0] == 12 else "large"
        metadata = {"case_id": case.case_id, "scale": scale,
                    "direction": case.problem.loads[0].direction,
                    "volume": case.problem.optimization.volume_fraction,
                    "specialist_route": specialist_case(case)}
        outcomes = [{"method": method, "succeeded": True,
                     "paired_time_ratio": 1.0 if method == "uniform" else 0.8,
                     "operational": {"final_compliance": 1.0,
                                     "physical_volume_error": 0.0},
                     "uniform_reference_compliance": 1.0} for method in METHODS]
        rows.append({"case": metadata, "outcomes": outcomes})
    index = {"rows": rows, "elapsed_seconds": 100.0, "peak_rss_bytes": 1024}
    assert screen_summary(tmp_path, index)["gate_passed"]
    high = [row for row in rows if row["case"]["specialist_route"]]
    assert len(high) == 2
    for item in high[0]["outcomes"]:
        if item["method"].startswith("routed_"):
            item["succeeded"] = False
    result = screen_summary(tmp_path, index)
    assert result["high_volume_large_y_successes"] == 3
    assert not result["gate_passed"]
