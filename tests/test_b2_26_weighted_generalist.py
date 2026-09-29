"""B2.26 frozen population, weighting, and matched development Gate."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from b2_26_weighted_generalist import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    METHODS,
    cohorts,
    plan_payload,
    screen_summary,
    weighted_case_ids,
)


def test_frozen_training_and_screen_population() -> None:
    groups, screen, blocked = cohorts()
    plan = plan_payload(groups, screen, blocked)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(groups["train"]) == 468
    assert len(groups["validation"]) == 12
    assert len(weighted_case_ids(groups)) == 78
    assert len(blocked) == 814
    assert len(screen) == 24
    assert len({case.case_id for case in (*blocked, *screen)}) == 838


def test_gate_requires_generalist_y_reliability(tmp_path: Path) -> None:
    _, cases, _ = cohorts()
    (tmp_path / "screen_index.json").write_text("{}")
    rows = []
    for case in cases:
        scale = "small" if case.problem.mesh.element_counts[0] == 12 else "large"
        metadata = {"case_id": case.case_id, "scale": scale,
                    "direction": case.problem.loads[0].direction,
                    "volume": case.problem.optimization.volume_fraction,
                    "specialist_route": (scale == "large"
                                         and case.problem.loads[0].direction == "y"
                                         and case.problem.optimization.volume_fraction >= 0.55)}
        outcomes = [{"method": method, "succeeded": True,
                     "paired_time_ratio": 1.0 if method == "uniform" else 0.8,
                     "operational": {"final_compliance": 1.0,
                                     "physical_volume_error": 0.0},
                     "uniform_reference_compliance": 1.0} for method in METHODS]
        rows.append({"case": metadata, "outcomes": outcomes})
    index = {"rows": rows, "elapsed_seconds": 100.0, "peak_rss_bytes": 1024}
    assert screen_summary(tmp_path, index)["gate_passed"]
    generalist_y = [row for row in rows if row["case"]["direction"] == "y"
                    and not row["case"]["specialist_route"]]
    assert len(generalist_y) == 10
    for row in generalist_y[:3]:
        row["outcomes"][7]["succeeded"] = False  # weighted seed 17
    for row in generalist_y[:3]:
        row["outcomes"][8]["succeeded"] = False  # weighted seed 29
    result = screen_summary(tmp_path, index)
    assert result["generalist_y_failure_counts"] == {"weighted_17": 3, "weighted_29": 3}
    assert result["passing_seeds"] == [43]
    assert not result["gate_passed"]
    for row in generalist_y[:3]:
        row["outcomes"][7]["succeeded"] = True
        row["outcomes"][8]["succeeded"] = True
    generalist_y[0]["outcomes"][7]["succeeded"] = False
    result = screen_summary(tmp_path, index)
    assert result["generalist_y_failure_counts"] == {"weighted_17": 1}
    assert result["passing_seeds"] == [29, 43]
