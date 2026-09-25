"""B2.2 fixed development exposure and feasibility-gate invariants."""

import sys
from collections import Counter
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_2_data_feasibility import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    HISTORICAL_FAILED_TRAIN,
    MAX_PROBE_RSS_BYTES,
    MAX_PROBE_SECONDS,
    plan_payload,
    probe_gate,
    result_id,
    select_plan,
    select_sentinel,
)

from topolab.m2_dataset import assign_m2_case_splits, build_m2_case_catalog  # noqa: E402


def test_plan_identity_counts_and_held_out_boundary() -> None:
    catalog = build_m2_case_catalog()
    frozen_splits = assign_m2_case_splits(catalog)
    plan = select_plan()
    payload = plan_payload(plan)

    assert payload["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert payload["counts"] == {
        "large_train": 36,
        "large_validation": 18,
        "small_train": 432,
        "small_validation": 36,
    }
    assert Counter(row.direction for row in plan) == {"y": 261, "z": 261}
    assert len({row.case.case_id for row in plan}) == 522
    assert len({result_id(row.case.case_id) for row in plan}) == 522
    assert all(result_id(row.case.case_id).startswith("tlcase-b22-v1-") for row in plan)
    assert all(frozen_splits[row.source_case_id] == row.split for row in plan)
    assert all(row.split in ("train", "validation") for row in plan)
    assert all(
        row.case.case_id == row.source_case_id
        if row.scale == "small"
        else row.case.case_id != row.source_case_id
        for row in plan
    )
    assert set(payload["sentinel_case_ids"]) <= {row.case.case_id for row in plan}


def test_sentinel_covers_failure_and_scale_direction_volume_strata() -> None:
    sentinel = select_sentinel(select_plan())

    assert len(sentinel) == 61
    assert HISTORICAL_FAILED_TRAIN <= {row.case.case_id for row in sentinel}
    assert Counter((row.scale, row.split) for row in sentinel) == {
        ("small", "train"): 7,
        ("small", "validation"): 18,
        ("large", "train"): 18,
        ("large", "validation"): 18,
    }
    assert all(
        len(
            [
                row
                for row in sentinel
                if row.scale == scale
                and row.split == split
                and row.direction == direction
                and row.volume == volume
            ]
        )
        == 1
        for scale, split in (
            ("small", "validation"),
            ("large", "train"),
            ("large", "validation"),
        )
        for direction in ("y", "z")
        for volume in (0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60)
    )


def test_probe_gate_keeps_every_case_and_resource_bound() -> None:
    rows = [{"quality_passed": True} for _ in range(61)]

    assert probe_gate(rows, MAX_PROBE_SECONDS, MAX_PROBE_RSS_BYTES)
    assert not probe_gate(rows[:-1], 1.0, 1)
    assert not probe_gate(rows[:-1] + [{"quality_passed": False}], 1.0, 1)
    assert not probe_gate(rows, MAX_PROBE_SECONDS + 0.001, 1)
    assert not probe_gate(rows, 1.0, MAX_PROBE_RSS_BYTES + 1)
