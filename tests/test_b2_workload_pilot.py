"""B2's fixed pilot may read development metadata but no held-out labels."""

import runpy
import sys
from pathlib import Path

import pytest

from topolab.m2_dataset import build_m2_case_catalog
from topolab.mesh import generate_structured_hex8

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
PILOT = runpy.run_path(str(SCRIPTS / "b2_workload_pilot.py"), run_name="b2_pilot_test")
DIRECTIONS = PILOT["DIRECTIONS"]
LARGE = PILOT["LARGE"]
SMALL = PILOT["SMALL"]
VOLUMES = PILOT["VOLUMES"]
scaled_case = PILOT["scaled_case"]
select_development_cases = PILOT["select_development_cases"]
select_pilot_cases = PILOT["select_pilot_cases"]


def test_scaled_case_preserves_physical_load_location() -> None:
    case = build_m2_case_catalog().cases[0]
    scaled = scaled_case(case)
    small_mesh = generate_structured_hex8(*SMALL, lengths=case.problem.mesh.lengths)
    large_mesh = generate_structured_hex8(*LARGE, lengths=scaled.problem.mesh.lengths)

    assert scaled.case_id != case.case_id
    assert scaled.problem.mesh.lengths == case.problem.mesh.lengths
    assert scaled.problem.optimization == case.problem.optimization
    assert scaled.problem.supports == case.problem.supports
    assert scaled.problem.loads[0].direction == case.problem.loads[0].direction
    assert tuple(large_mesh.coordinates[scaled.problem.loads[0].node]) == tuple(
        small_mesh.coordinates[case.problem.loads[0].node]
    )


def test_pilot_plan_uses_only_validation_metadata_and_fixed_strata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cases = build_m2_case_catalog().cases
    selected = []
    for volume in VOLUMES:
        for direction in DIRECTIONS:
            matches = [
                case
                for case in cases
                if case.problem.optimization.volume_fraction == volume
                and case.problem.loads[0].direction == direction
            ]
            selected.extend(matches[:2])
    monkeypatch.setitem(select_development_cases.__globals__, "EXPECTED_VALIDATION", 12)
    monkeypatch.setitem(select_development_cases.__globals__, "EXPECTED_FAILED_TRAIN", 0)
    digest = "a" * 64
    entries = [
        {
            "case_id": case.case_id,
            "split": "validation",
            "status": "succeeded",
            "artifact": {
                "case_id": case.case_id,
                "generator_version": "topolab.m0.generator.v1",
                "source_revision": "b" * 40,
                "sha256": digest,
                "byte_size": 1,
                "relative_path": f"labels/{case.case_id}/{digest}.json",
            },
        }
        for case in selected
    ]
    entries.append(
        {"case_id": "held-out", "split": "test", "artifact": {"poison": True}}
    )
    index = {
        "state": "complete",
        "manifest_sha256": (
            "99b63e4b49d29764b033b8d8af6664801454d6e5bcf34df68d9e6471a71ba33f"
        ),
        "manifest": {
            "samples": [
                {"case": case.model_dump(mode="json"), "split": "validation"}
                for case in selected
            ]
        },
        "entries": entries,
    }

    cohort = select_pilot_cases(index)

    assert len(cohort) == 12
    assert {item.source_case_id for item in cohort} <= {
        case.case_id for case in selected
    }
    assert {(item.volume, item.direction, item.scale) for item in cohort} == {
        (volume, direction, scale)
        for volume in VOLUMES
        for direction in DIRECTIONS
        for scale in ("small", "large")
    }
