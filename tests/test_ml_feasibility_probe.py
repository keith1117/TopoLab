"""The development probe must never deserialize held-out label references."""

import runpy
from collections.abc import Iterator
from pathlib import Path

import pytest

from topolab.catalog import build_m0_case_catalog

PROBE = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/ml_feasibility_probe.py"),
    run_name="ml_feasibility_probe_test",
)


@pytest.fixture
def case_payload() -> Iterator[dict[str, object]]:
    case = build_m0_case_catalog().cases[0]
    yield case.model_dump(mode="json")


def test_select_development_cases_ignores_held_out_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    case_payload: dict[str, object],
) -> None:
    select_development_cases = PROBE["select_development_cases"]
    assert callable(select_development_cases)
    monkeypatch.setitem(select_development_cases.__globals__, "EXPECTED_VALIDATION", 1)
    monkeypatch.setitem(select_development_cases.__globals__, "EXPECTED_FAILED_TRAIN", 0)
    case_id = case_payload["case_id"]
    digest = "a" * 64
    artifact = {
        "case_id": case_id,
        "generator_version": "topolab.m0.generator.v1",
        "source_revision": "b" * 40,
        "sha256": digest,
        "byte_size": 1,
        "relative_path": f"labels/{case_id}/{digest}.json",
    }
    index = {
        "state": "complete",
        "manifest_sha256": "99b63e4b49d29764b033b8d8af6664801454d6e5bcf34df68d9e6471a71ba33f",
        "manifest": {
            "samples": [{"case": case_payload, "split": "validation"}],
        },
        "entries": [
            {
                "case_id": case_id,
                "split": "validation",
                "status": "succeeded",
                "artifact": artifact,
            },
            {"case_id": "held-out-test", "split": "test", "artifact": {"poison": True}},
            {"case_id": "held-out-ood", "split": "ood", "artifact": {"poison": True}},
        ],
    }

    validation, failed_train = select_development_cases(index)

    assert len(validation) == 1
    assert validation[0].case.case_id == case_id
    assert failed_train == []


def test_select_development_cases_rejects_wrong_manifest(
    case_payload: dict[str, object],
) -> None:
    with pytest.raises(ValueError, match="unexpected M2 manifest"):
        PROBE["select_development_cases"](
            {"state": "complete", "manifest_sha256": "wrong", "manifest": {}}
        )
