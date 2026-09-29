"""Frozen B2.23 position coverage and label-data Gate."""

import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_23_position_labels import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    _artifact_path,
    _environment,
    _read_label,
    cohorts,
    load_position,
    plan_payload,
    summary,
)


@pytest.fixture(scope="module")
def population() -> tuple:
    return cohorts()


def test_frozen_coverage_and_disjoint_split(population: tuple) -> None:
    identities, cases, blocked = population
    plan = plan_payload(identities, blocked)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(blocked) == 760
    assert len(cases) == 30
    assert len({case.case_id for case in (*blocked, *cases)}) == 790
    assert sum(item["split"] == "train" for item in identities) == 20
    assert sum(item["split"] == "validation" for item in identities) == 10
    train_positions = {tuple(item["load_position"]) for item in identities
                       if item["split"] == "train"}
    assert len(train_positions) == 10
    assert (8, 2) in train_positions
    assert all(load_position(case) == tuple(item["load_position"])
               for case, item in zip(cases, identities, strict=True))


def test_label_gate_requires_every_audited_split(population: tuple) -> None:
    identities, _, _ = population
    rows = [{"identity": item, "status": "succeeded"} for item in identities]
    index = {"rows": rows, "elapsed_seconds": 100.0, "peak_rss_bytes": 1000}
    assert summary(index)["gate_passed"]
    rows[0] = {"identity": identities[0], "status": "failed",
               "failure_code": "nonconvergence"}
    assert not summary(index)["gate_passed"]


def test_label_reader_rejects_corrupt_bytes(population: tuple, tmp_path: Path) -> None:
    identities, _, _ = population
    identity = identities[0]
    digest = "a" * 64
    path = _artifact_path(tmp_path, identity["case_id"], digest)
    path.parent.mkdir(parents=True)
    path.write_bytes(b"bad")
    row = {"identity": identity, "status": "succeeded",
           "artifact_sha256": digest, "artifact_bytes": 3}
    context = {"source_revision": "0" * 40}
    environment = _environment(Path(__file__).resolve().parents[1])
    with pytest.raises(ValueError, match="checksum"):
        _read_label(tmp_path, row, identity, context, environment)
