"""B2.29 independent population, reference stop, and charged confirmation Gate."""

import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import b2_29_development_confirmation as runner  # noqa: E402


@pytest.fixture(scope="module")
def population() -> tuple:
    return runner.cohorts()


def test_fixed_confirmation_is_larger_and_physically_disjoint(population: tuple) -> None:
    cases, blocked = population
    plan = runner.plan_payload(cases, blocked)
    assert plan["plan_sha256"] == runner.EXPECTED_PLAN_SHA256
    assert len(cases) == 48 and len(blocked) == 922
    assert len(set(plan["screen_case_ids"]) | set(plan["blocked_case_ids"])) == 970
    assert set(runner.VOLUMES).isdisjoint(
        case.problem.optimization.volume_fraction for case in blocked)
    assert Counter((case.problem.mesh.element_counts, case.problem.loads[0].direction)
                   for case in cases) == {
                       ((12, 6, 3), "y"): 12, ((12, 6, 3), "z"): 12,
                       ((24, 12, 6), "y"): 12, ((24, 12, 6), "z"): 12,
                   }
    assert sum(runner.specialist_case(case) for case in cases) == 3
    assert len(runner.METHODS) == 9


def _passing_metrics() -> tuple[dict, dict, dict]:
    scales = {f"{method}/{scale}": 0.8 for method in runner.METHODS
              for scale in ("small", "large")}
    directions = {f"{method}/{scale}/{direction}": 0.8 for method in runner.METHODS
                  for scale in ("small", "large") for direction in ("y", "z")}
    overall = {method: 0.8 for method in runner.METHODS}
    overall.update({method: 0.9 for method in runner.NON_ML})
    return scales, directions, overall


def test_seed_must_beat_both_non_ml_with_no_extra_failures() -> None:
    scales, directions, overall = _passing_metrics()
    assert runner.passing_seeds(scales, directions, overall, Counter(), Counter()) == [17, 29, 43]
    overall["nearest_neighbor"] = 0.8  # Equal cost is not an advantage.
    assert runner.passing_seeds(scales, directions, overall, Counter(), Counter()) == []
    overall["nearest_neighbor"] = 0.9
    directions["expanded_17/large/z"] = 1.01
    failures = Counter({"expanded_29": 3, "old_29": 3})
    assert runner.passing_seeds(scales, directions, overall, failures, Counter()) == [43]
    failures = Counter({"expanded_43": 1})
    assert runner.passing_seeds(scales, directions, overall, failures, Counter()) == [29]
    failures["old_43"] = 1
    assert runner.passing_seeds(
        scales, directions, overall, failures, Counter({"expanded_43": 1})) == [29]


def test_reference_failure_keeps_confirmation_closed(population: tuple) -> None:
    cases, _ = population
    index = {"rows": [{"case_id": case.case_id, "uniform": {
        "succeeded": True, "candidate": {"final_compliance": 1.0,
                                          "physical_volume_error": 0.0}}} for case in cases],
             "elapsed_seconds": 100.0, "peak_rss_bytes": 1024}
    assert runner.reference_gate(index, cases, runner.REFERENCE_CAP)
    index["rows"][0]["uniform"]["succeeded"] = False
    assert not runner.reference_gate(index, cases, runner.REFERENCE_CAP)


def test_confirmation_requires_quality_cells_complete_methods_and_resources(
    population: tuple, tmp_path: Path,
) -> None:
    cases, _ = population
    (tmp_path / "screen_index.json").write_text("{}")
    rows = [{"case": runner._case_metadata(case), "outcomes": [
        {"method": method, "succeeded": True,
         "paired_time_ratio": 1.0 if method == "uniform" else (
             0.9 if method in runner.NON_ML else 0.8),
         "timing": {"end_to_end_seconds": 1.0},
         "operational": {"final_compliance": 1.0, "physical_volume_error": 0.0,
                         "iterations": 50}, "uniform_reference_compliance": 1.0}
        for method in runner.METHODS]} for case in cases]
    index = {"rows": rows, "elapsed_seconds": 100.0, "peak_rss_bytes": 1024}
    summary = runner.screen_summary(tmp_path, index)
    assert summary["gate_passed"] and summary["outcomes"] == 432
    assert summary["middle_volume_large_y_successes"]["expanded"] == 9
    index["elapsed_seconds"] = runner.SCREEN_CAP + 1
    assert not runner.screen_summary(tmp_path, index)["gate_passed"]
    index["elapsed_seconds"] = 100.0
    rows[0]["outcomes"][0]["operational"]["final_compliance"] = 1.002
    assert not runner.screen_summary(tmp_path, index)["gate_passed"]
    rows[0]["outcomes"][0]["operational"]["final_compliance"] = 1.0
    middle = [row for row in rows if row["case"]["scale"] == "large"
              and row["case"]["direction"] == "y"
              and row["case"]["volume"] == runner.VOLUMES[2]]
    for row in middle:
        row["outcomes"][3]["succeeded"] = False
        row["outcomes"][6]["succeeded"] = False
    middle[0]["outcomes"][4]["succeeded"] = False
    middle[0]["outcomes"][7]["succeeded"] = False
    result = runner.screen_summary(tmp_path, index)
    assert result["passing_seeds"] == [29, 43]
    assert result["middle_volume_large_y_successes"]["expanded"] == 5
    assert not result["gate_passed"]
    rows[0]["outcomes"].pop()
    assert not runner.screen_summary(tmp_path, index)["gate_passed"]
