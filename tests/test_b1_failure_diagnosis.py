"""B1 may use held-out failed-case definitions, never held-out label values."""

import runpy
from pathlib import Path

import pytest

from topolab.catalog import build_m0_case_catalog

DIAGNOSIS = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/b1_failure_diagnosis.py"),
    run_name="b1_failure_diagnosis_test",
)


def test_selection_ignores_test_and_ood_label_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    select = DIAGNOSIS["select_diagnostic_cases"]
    assert callable(select)
    monkeypatch.setitem(select.__globals__, "EXPECTED_VALIDATION", 1)
    monkeypatch.setitem(
        select.__globals__, "EXPECTED_FAILURE_SPLITS", {"train": 1, "test": 1, "ood": 1}
    )
    cases = build_m0_case_catalog().cases[:6]
    splits = ("validation", "test", "ood", "train", "test", "ood")
    statuses = ("succeeded", "succeeded", "succeeded", "failed", "failed", "failed")
    digest = "a" * 64
    validation_reference = {
        "case_id": cases[0].case_id,
        "generator_version": "topolab.m0.generator.v1",
        "source_revision": "b" * 40,
        "sha256": digest,
        "byte_size": 1,
        "relative_path": f"labels/{cases[0].case_id}/{digest}.json",
    }
    entries = []
    for case, split, status in zip(cases, splits, statuses, strict=True):
        entries.append(
            {
                "case_id": case.case_id,
                "split": split,
                "status": status,
                "artifact": (validation_reference if split == "validation" else {"poison": True}),
            }
        )
    index = {
        "state": "complete",
        "manifest_sha256": DIAGNOSIS["M2_MANIFEST_SHA256"],
        "manifest": {
            "samples": [
                {"case": case.model_dump(mode="json"), "split": split}
                for case, split in zip(cases, splits, strict=True)
            ]
        },
        "entries": entries,
    }

    validation, failed = select(index)

    assert [item.case.case_id for item in validation] == [cases[0].case_id]
    assert {item.case.case_id for item in failed} == {
        cases[3].case_id,
        cases[4].case_id,
        cases[5].case_id,
    }
    assert {item.split for item in failed} == {"train", "test", "ood"}


def test_selection_rejects_wrong_manifest() -> None:
    select = DIAGNOSIS["select_diagnostic_cases"]
    assert callable(select)
    with pytest.raises(ValueError, match="unexpected M2 manifest"):
        select({"state": "complete", "manifest_sha256": "wrong"})
