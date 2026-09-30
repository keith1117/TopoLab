"""B2.28 frozen label separation and charged development Gate."""

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import b2_28_expanded_generalist as runner  # noqa: E402
from b2_27_middle_volume_labels import cohorts as label_cohorts  # noqa: E402


@pytest.fixture(scope="module")
def population() -> tuple:
    return runner.cohorts()


def test_frozen_expansion_and_disjoint_screen(population: tuple) -> None:
    groups, screen, blocked = population
    plan = runner.plan_payload(groups, screen, blocked)
    assert plan["plan_sha256"] == runner.EXPECTED_PLAN_SHA256
    assert len(groups["train"]) == 468
    assert len(groups["expanded_train"]) == 508
    assert len(groups["validation"]) == 12
    assert len(groups["diagnostic"]) == 20
    assert len(runner.weighted_case_ids(groups)) == 98
    assert len(blocked) == 898
    assert len(screen) == 24
    assert len({case.case_id for case in (*blocked, *screen)}) == 922
    assert not ({case.case_id for case in groups["expanded_train"]}
                & {case.case_id for case in groups["diagnostic"]})


def test_new_label_adapter_keeps_validation_out_of_training(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    identities, cases, _ = label_cohorts()
    case_map = {case.case_id: case for case in cases}
    opened = []

    def read_label(root, row, identity, context, environment):  # type: ignore[no-untyped-def]
        opened.append(identity["split"])
        case = case_map[identity["case_id"]]
        return SimpleNamespace(case=case, design_density=[identity["volume"]] * 1728)

    monkeypatch.setattr(runner, "read_position_label", read_label)
    index = {"context": {}, "rows": [{"identity": identity} for identity in identities]}
    train = runner._new_samples(tmp_path, index, "train", Path(__file__).resolve().parents[1])
    assert len(train) == 40
    assert set(opened) == {"train"}
    with pytest.raises(ValueError, match="only development"):
        runner._new_samples(tmp_path, index, "test", tmp_path)


def test_label_index_rejects_corrupt_bytes(tmp_path: Path) -> None:
    (tmp_path / "label_index.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        runner._read_label_index(tmp_path)


def test_gate_requires_middle_y_quality_and_matched_reliability(
    population: tuple, tmp_path: Path,
) -> None:
    _, cases, _ = population
    (tmp_path / "screen_index.json").write_text("{}")
    rows = []
    for case in cases:
        metadata = {"case_id": case.case_id,
                    "scale": "small" if case.problem.mesh.element_counts[0] == 12 else "large",
                    "direction": case.problem.loads[0].direction,
                    "volume": case.problem.optimization.volume_fraction,
                    "specialist_route": runner.specialist_case(case)}
        outcomes = [{"method": method, "succeeded": True,
                     "paired_time_ratio": 1.0 if method == "uniform" else 0.8,
                     "operational": {"final_compliance": 1.0, "physical_volume_error": 0.0},
                     "uniform_reference_compliance": 1.0} for method in runner.METHODS]
        rows.append({"case": metadata, "outcomes": outcomes})
    index = {"rows": rows, "elapsed_seconds": 100.0, "peak_rss_bytes": 1024}
    assert runner.screen_summary(tmp_path, index)["gate_passed"]
    middle = [row for row in rows if row["case"]["scale"] == "large"
              and row["case"]["direction"] == "y"
              and row["case"]["volume"] == runner.VOLUMES[1]]
    for row in middle:
        row["outcomes"][1]["succeeded"] = False
        row["outcomes"][4]["succeeded"] = False
    middle[0]["outcomes"][3]["succeeded"] = False
    middle[0]["outcomes"][6]["succeeded"] = False
    result = runner.screen_summary(tmp_path, index)
    assert result["passing_seeds"] == [17, 29, 43]
    assert result["middle_volume_large_y_successes"]["expanded"] == 3
    assert not result["gate_passed"]
    for row in rows:
        for item in row["outcomes"]:
            item["succeeded"] = True
    middle[0]["outcomes"][4]["succeeded"] = False
    result = runner.screen_summary(tmp_path, index)
    assert result["passing_seeds"] == [29, 43]
