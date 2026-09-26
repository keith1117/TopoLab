"""B2.7 representation, exposure, and independent decision checks."""

import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_5_prototype import atomic_write, canonical_bytes  # noqa: E402
from b2_6_trajectory import _screen_summary  # noqa: E402
from b2_7_global_load import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    METHODS,
    VOLUMES,
    cohorts,
    plan_payload,
)

from topolab.b2_7_conditioning import encode_global_load_case  # noqa: E402
from topolab.experiment import encode_case  # noqa: E402


@pytest.fixture(scope="module")
def groups():  # type: ignore[no-untyped-def]
    return cohorts()


def test_global_load_changes_only_load_channels_and_reaches_all_elements(groups) -> None:  # type: ignore[no-untyped-def]
    old, _ = groups
    case = next(
        case for case in old["validation"]
        if case.problem.mesh.element_counts == (12, 6, 3)
        and case.problem.loads[0].direction == "y"
    )
    original = encode_case(case).input_tensor
    new = encode_global_load_case(case).input_tensor
    assert original.shape == new.shape == (10, 3, 6, 12)
    np.testing.assert_array_equal(original[:3], new[:3])
    np.testing.assert_array_equal(original[6:], new[6:])
    assert np.count_nonzero(original[4]) < original[4].size // 4
    assert np.all(new[4] < 0)
    expected = 1.0 - np.sqrt(
        ((11.5 / 12 - 1.0) ** 2 + (2.5 / 6 - 2 / 6) ** 2 + (1.5 / 3 - 1 / 3) ** 2)
        / 3.0
    )
    assert new[4, 1, 2, 11] == pytest.approx(-expected, abs=2e-7)
    np.testing.assert_array_equal(new[3], np.zeros_like(new[3]))
    np.testing.assert_array_equal(new[5], np.zeros_like(new[5]))
    np.testing.assert_array_equal(original, encode_case(case).input_tensor)


def test_global_field_encodes_load_location_and_direction(groups) -> None:  # type: ignore[no-untyped-def]
    old, screen = groups
    selection = next(
        case for case in old["validation"]
        if case.problem.mesh.element_counts == (12, 6, 3)
        and case.problem.optimization.volume_fraction == 0.375
        and case.problem.loads[0].direction == "z"
    )
    candidate = next(
        case for case in old["screen"]
        if case.problem.mesh.element_counts == (12, 6, 3)
        and case.problem.optimization.volume_fraction == 0.375
        and case.problem.loads[0].direction == "z"
    )
    a = encode_global_load_case(selection).input_tensor
    b = encode_global_load_case(candidate).input_tensor
    assert np.max(np.abs(a[5] - b[5])) > 0.05
    assert a[5, 1, 2, 11] < a[5, 1, 5, 11]
    assert b[5, 2, 4, 11] < b[5, 2, 1, 11]
    assert all(case.problem.optimization.volume_fraction in VOLUMES for case in screen)


def test_plan_retains_train_selection_and_has_fresh_complete_screen(groups) -> None:  # type: ignore[no-untyped-def]
    old, screen = groups
    plan = plan_payload(old, screen)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(old["train"]) == 468 and len(old["validation"]) == 12
    assert len(screen) == 12 and len(METHODS) == 11
    assert len(set(plan["screen_case_ids"])) == 12
    assert set(plan["screen_case_ids"]).isdisjoint(
        set(plan["train_case_ids"]) | set(plan["validation_case_ids"])
    )
    assert set(VOLUMES) == {0.2375, 0.3875, 0.5375}
    assert [method for method in METHODS if method.startswith("conditioned_")] == [
        "conditioned_17", "conditioned_29", "conditioned_43"
    ]


def test_gate_uses_only_new_seeds_and_both_scales(tmp_path: Path) -> None:
    rows = []
    for scale in ("small", "large"):
        for direction in ("y", "z"):
            for volume in VOLUMES:
                outcomes = []
                for method in METHODS:
                    ratio = 0.8 if method in ("conditioned_17", "conditioned_29") else 1.0
                    outcomes.append({
                        "method": method,
                        "paired_time_ratio": ratio,
                        "succeeded": True,
                        "fallback_used": False,
                        "operational": {
                            "final_compliance": 1.0,
                            "physical_volume_error": 0.0,
                        },
                        "uniform_reference_compliance": 1.0,
                        "timing": {"end_to_end_seconds": ratio},
                    })
                rows.append({
                    "case": {"scale": scale, "direction": direction, "volume": volume},
                    "outcomes": outcomes,
                    "oracle": {"oracle_generation_seconds": 0.0},
                })
    index = {
        "context": {}, "rows": rows, "elapsed_seconds": 1.0,
        "peak_rss_bytes": 1, "model_loading_seconds": 0.0,
        "neighbor_loading_seconds": 0.0, "neighbor_bytes": 0,
    }
    atomic_write(tmp_path / "screen_index.json", canonical_bytes(index))
    passed = _screen_summary(
        tmp_path, index, learned_prefix="conditioned_",
        summary_version="topolab.b2_7.screen_summary.v1",
    )
    assert passed["prototype_gate_passed"]
    assert passed["passing_seeds"] == [17, 29]
    rows[6]["outcomes"][8]["paired_time_ratio"] = 2.0
    failed = _screen_summary(tmp_path, index, learned_prefix="conditioned_")
    assert not failed["prototype_gate_passed"]
    assert failed["passing_seeds"] == [17]
