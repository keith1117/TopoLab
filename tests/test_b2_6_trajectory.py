"""B2.6 target capture, disjointness, artifact, and feasibility-Gate checks."""

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_6_trajectory import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    _read_target,
    _screen_summary,
    _target_path,
    _target_payload,
    atomic_write,
    canonical_bytes,
    cohorts,
    plan_payload,
    sha256,
)

from topolab.b2_6_trajectory import (  # noqa: E402
    TrajectorySample,
    _batches,
    capture_uniform_target,
)
from topolab.experiment import encode_case  # noqa: E402
from topolab.problem import TopologyProblem, solve_problem  # noqa: E402


@pytest.fixture(scope="module")
def groups():  # type: ignore[no-untyped-def]
    return cohorts()


def test_plan_has_new_selection_and_screen_boundaries(groups) -> None:  # type: ignore[no-untyped-def]
    plan = plan_payload(groups)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert {split: len(cases) for split, cases in groups.items()} == {
        "train": 468,
        "validation": 12,
        "screen": 12,
    }
    assert len({case.case_id for cases in groups.values() for case in cases}) == 492
    assert {case.problem.optimization.volume_fraction for case in groups["screen"]} == {
        0.225,
        0.375,
        0.525,
    }
    assert all(case.problem.optimization.max_iterations == 240 for case in groups["screen"])


def test_captured_third_state_matches_uninterrupted_solver_prefix(groups) -> None:  # type: ignore[no-untyped-def]
    case = next(case for case in groups["train"] if case.problem.mesh.element_counts == (12, 6, 3))
    target = capture_uniform_target(case, update=3)
    payload = case.problem.model_dump(mode="json")
    payload["optimization"]["max_iterations"] = 3
    prefix = solve_problem(
        TopologyProblem.model_validate(payload), termination_policy="physical_plateau"
    )
    assert target.iterations == 3
    assert not target.converged_before_target
    np.testing.assert_array_equal(
        target.density.reshape(-1), np.asarray(prefix.design_density, dtype=np.float32)
    )
    assert target.compliance == pytest.approx(prefix.compliance, rel=1e-12)
    assert target.physical_volume_error <= 0.005


def test_shape_schedule_covers_each_training_case_once(groups) -> None:  # type: ignore[no-untyped-def]
    small = next(case for case in groups["train"] if case.problem.mesh.element_counts == (12, 6, 3))
    large = next(
        case for case in groups["train"] if case.problem.mesh.element_counts == (24, 12, 6)
    )
    samples = []
    for index, case in enumerate((small,) * 432 + (large,) * 36):
        inputs = torch.from_numpy(encode_case(case).input_tensor.copy())
        samples.append(
            TrajectorySample(
                str(index),
                "train",
                inputs,
                torch.full((1, *inputs.shape[1:]), 0.5, dtype=torch.float32),
            )
        )
    first = _batches(tuple(samples), torch.Generator().manual_seed(17))
    second = _batches(tuple(samples), torch.Generator().manual_seed(17))
    assert first == second
    assert len(first) == 59
    assert sorted(i for batch in first for i in batch) == list(range(468))
    assert all(len({samples[i].shape for i in batch}) == 1 for batch in first)


def test_target_artifact_rejects_corruption_and_wrong_split(groups, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    case = groups["train"][0]
    target = capture_uniform_target(case)
    context = {"plan_sha256": EXPECTED_PLAN_SHA256}
    payload = _target_payload(case, "train", target, context)
    contents = canonical_bytes(payload)
    digest = sha256(contents)
    path = _target_path(tmp_path, digest)
    atomic_write(path, contents)
    row = {
        "case_id": case.case_id,
        "split": "train",
        "artifact_sha256": digest,
        "artifact_bytes": len(contents),
    }
    assert _read_target(tmp_path, row, case, "train", context).iterations == target.iterations
    with pytest.raises(ValueError, match="case or split"):
        _read_target(tmp_path, row, case, "validation", context)
    path.write_bytes(contents + b"x")
    with pytest.raises(ValueError, match="checksum"):
        _read_target(tmp_path, row, case, "train", context)


def test_gate_needs_two_trajectory_seeds_on_both_scales(groups, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    methods = [
        "uniform",
        "physics_heuristic",
        "nearest_neighbor",
        "control_43",
        "trajectory_17",
        "trajectory_29",
        "trajectory_43",
        "trajectory_oracle",
    ]
    rows = []
    for case in groups["screen"]:
        nx, _ny, _nz = case.problem.mesh.element_counts
        rows.append(
            {
                "case": {
                    "case_id": case.case_id,
                    "scale": "small" if nx == 12 else "large",
                    "direction": case.problem.loads[0].direction,
                    "volume": case.problem.optimization.volume_fraction,
                },
                "oracle": {"oracle_generation_seconds": 0.5},
                "outcomes": [
                    {
                        "method": method,
                        "succeeded": True,
                        "fallback_used": False,
                        "operational": {"final_compliance": 1.0, "physical_volume_error": 0.0},
                        "uniform_reference_compliance": 1.0,
                        "paired_time_ratio": (
                            0.85 if method in ("trajectory_17", "trajectory_29") else 1.0
                        ),
                        "timing": {"setup_seconds": 0.1, "end_to_end_seconds": 1.0},
                    }
                    for method in methods
                ],
            }
        )
    index = {
        "context": {},
        "rows": rows,
        "elapsed_seconds": 10.0,
        "peak_rss_bytes": 1,
        "model_loading_seconds": 0.1,
        "neighbor_loading_seconds": 0.1,
        "neighbor_bytes": 1,
    }
    atomic_write(tmp_path / "screen_index.json", canonical_bytes(index))
    assert _screen_summary(tmp_path, index)["passing_seeds"] == [17, 29]
    assert _screen_summary(tmp_path, index)["prototype_gate_passed"]
    rows[0]["outcomes"][5]["paired_time_ratio"] = 2.0
    atomic_write(tmp_path / "screen_index.json", canonical_bytes(index))
    assert not _screen_summary(tmp_path, index)["prototype_gate_passed"]
