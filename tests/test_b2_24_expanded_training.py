"""B2.24 frozen population, batch count, and matched Gate."""

import sys
from pathlib import Path

import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_24_expanded_training import (  # noqa: E402
    BATCH_COUNT,
    EXPECTED_PLAN_SHA256,
    METHODS,
    TRAIN_COUNT,
    cohorts,
    plan_payload,
    screen_summary,
    specialist_case,
)

from topolab.b2_6_trajectory import TrajectorySample, _batches  # noqa: E402


def test_frozen_population_and_case_weighting() -> None:
    groups, screen, blocked = cohorts()
    plan = plan_payload(groups, screen, blocked)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(blocked) == 790
    assert len(screen) == 24
    assert len({case.case_id for case in (*blocked, *screen)}) == 814
    assert len(plan["train_case_ids"]) == 468
    assert len(plan["added_train_case_ids"]) == 20
    assert len(plan["added_diagnostic_validation_case_ids"]) == 10
    assert len(plan["selection_validation_case_ids"]) == 2
    assert len(plan["high_weight_train_case_ids"]) == 72
    assert plan["train_count"] == TRAIN_COUNT == 488
    assert sum(map(specialist_case, screen)) == 2


def test_expanded_shape_buckets_have_frozen_batch_count() -> None:
    samples = []
    for shape, count in (((3, 6, 12), 432), ((6, 12, 24), 56)):
        inputs = torch.zeros((13, *shape), dtype=torch.float32)
        target = torch.zeros((1, *shape), dtype=torch.float32)
        samples.extend(TrajectorySample(case_id=str(index), split="train",
                                        inputs=inputs, target=target,
                                        input_channels=13)
                       for index in range(count))
    batches = _batches(tuple(samples), torch.Generator().manual_seed(17))
    assert len(samples) == TRAIN_COUNT
    assert len(batches) == BATCH_COUNT == 61
    assert sorted(index for batch in batches for index in batch) == list(range(TRAIN_COUNT))


def test_gate_requires_improved_high_y_quality(tmp_path: Path) -> None:
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
    high = [row for row in rows if row["case"]["specialist_route"]]
    assert len(high) == 2
    high[0]["outcomes"][1]["succeeded"] = False  # old seed 17
    index = {"rows": rows, "elapsed_seconds": 100.0, "peak_rss_bytes": 1024}
    result = screen_summary(tmp_path, index)
    assert result["high_volume_large_y_successes"] == {"old": 5, "expanded": 6}
    assert result["gate_passed"]
    high[0]["outcomes"][4]["succeeded"] = False  # expanded seed 17
    result = screen_summary(tmp_path, index)
    assert result["high_volume_large_y_successes"] == {"old": 5, "expanded": 5}
    assert not result["gate_passed"]
