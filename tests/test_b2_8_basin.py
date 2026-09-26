"""B2.8 opt-in basin recentering and frozen development boundary."""

import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_6_trajectory import _small_case  # noqa: E402
from b2_8_basin import EXPECTED_PLAN_SHA256, METHODS, VOLUMES, cohorts, plan_payload  # noqa: E402

from topolab.b2_8_basin import recenter_y_start  # noqa: E402


def test_recenter_y_is_convex_midpoint_and_z_is_unchanged() -> None:
    y_case = _small_case(0.2125, "y", 3, 2)
    z_case = _small_case(0.2125, "z", 3, 2)
    raw = np.linspace(0.05, 0.95, 216, dtype=np.float32).reshape(1, 3, 6, 12)
    original = raw.copy()

    y = recenter_y_start(y_case, raw)
    z = recenter_y_start(z_case, raw)

    np.testing.assert_allclose(y, 0.5 * raw + 0.5 * np.float32(0.2125), rtol=0, atol=1e-7)
    np.testing.assert_array_equal(z, raw)
    np.testing.assert_array_equal(raw, original)
    assert y.dtype == z.dtype == np.float32
    assert not np.shares_memory(y, raw)


def test_recenter_rejects_invalid_prediction() -> None:
    case = _small_case(0.2125, "y", 3, 2)
    with pytest.raises(ValueError, match="shape"):
        recenter_y_start(case, np.zeros((1, 3, 6, 11), dtype=np.float32))
    bad = np.full((1, 3, 6, 12), np.nan, dtype=np.float32)
    with pytest.raises(ValueError, match="finite"):
        recenter_y_start(case, bad)


def test_frozen_b2_8_screen_is_fresh_and_complete() -> None:
    old, screen = cohorts()
    plan = plan_payload(old, screen)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(screen) == 12 and len(METHODS) == 11
    assert len({case.case_id for case in screen}) == 12
    assert {case.problem.optimization.volume_fraction for case in screen} == set(VOLUMES)
    assert {case.problem.loads[0].direction for case in screen} == {"y", "z"}
    assert {case.problem.mesh.element_counts for case in screen} == {(12, 6, 3), (24, 12, 6)}
    small_load_nodes = {
        case.problem.loads[0].node
        for case in screen if case.problem.mesh.element_counts == (12, 6, 3)
    }
    assert small_load_nodes == {12 + 13 * (3 + 7 * 2)}
    assert set(plan["screen_case_ids"]).isdisjoint(
        {case.case_id for cases in old.values() for case in cases}
    )
