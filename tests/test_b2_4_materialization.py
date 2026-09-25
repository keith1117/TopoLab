"""B2.4 population, persisted-label, and corruption boundaries."""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_3_budget_sentinel import select_cases as select_sentinel_cases  # noqa: E402
from b2_4_materialize_labels import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    _artifact_path,
    _audit,
    _canonical_bytes,
    _index_path,
    _read_index,
    _write_artifact,
    plan_payload,
    row_identity,
    select_cases,
)

from topolab.b2_4_labels import B24Label, audit_label, generate_b24_label  # noqa: E402
from topolab.dataset import DatasetEnvironment  # noqa: E402


@pytest.fixture(scope="module")
def cohort():  # type: ignore[no-untyped-def]
    return select_cases()


@pytest.fixture(scope="module")
def example(cohort):  # type: ignore[no-untyped-def]
    item = next(
        row for row in cohort if row.source.scale == "small" and row.source.volume == 0.2
    )
    identity = row_identity(item)
    environment = DatasetEnvironment(
        python_version="3.12.10",
        numpy_version="2.5.3",
        scipy_version="1.18.1",
        lockfile_sha256="a" * 64,
    )
    label = generate_b24_label(
        case=item.case,
        source_case_id=identity["source_case_id"],
        result_id=identity["result_id"],
        split=item.source.split,
        scale=item.source.scale,
        direction=item.source.direction,
        volume=item.source.volume,
        source_revision="b" * 40,
        environment=environment,
    )
    return item, label, environment


def test_full_plan_preserves_frozen_population_and_sentinel(cohort) -> None:  # type: ignore[no-untyped-def]
    plan = plan_payload(cohort)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert len(plan["cases"]) == 522
    assert Counter((row.source.scale, row.source.split) for row in cohort) == {
        ("small", "train"): 432,
        ("small", "validation"): 36,
        ("large", "train"): 36,
        ("large", "validation"): 18,
    }
    assert all(row.source.split in ("train", "validation") for row in cohort)
    full = {row.case.case_id: row_identity(row) for row in cohort}
    for sentinel in select_sentinel_cases():
        assert full[sentinel.case.case_id]["result_id"] == row_identity(sentinel)["result_id"]


def test_label_round_trip_and_independent_sensitivity_audit(example) -> None:  # type: ignore[no-untyped-def]
    _item, label, _environment = example
    restored = B24Label.model_validate_json(_canonical_bytes(label.model_dump(mode="json")))
    assert restored == label
    assert label.iterations <= 240
    assert len(label.design_density) == len(label.sensitivity_weight) == 216
    audit_label(restored)

    payload = label.model_dump(mode="json")
    payload["physical_density"][0] = 0.25
    with pytest.raises(ValidationError, match="filtered design"):
        B24Label.model_validate(payload)

    payload = label.model_dump(mode="json")
    low = int(np.argmin(payload["sensitivity_weight"]))
    high = int(np.argmax(payload["sensitivity_weight"]))
    assert low != high
    payload["sensitivity_weight"][low], payload["sensitivity_weight"][high] = (
        payload["sensitivity_weight"][high],
        payload["sensitivity_weight"][low],
    )
    with pytest.raises(ValueError, match="weights failed independent audit"):
        audit_label(B24Label.model_validate(payload))


def test_index_rejects_corrupted_artifact_and_preserves_case_identity(  # type: ignore[no-untyped-def]
    tmp_path: Path, example
) -> None:
    item, label, environment = example
    plan = plan_payload((item,))
    digest, size = _write_artifact(tmp_path, label)
    row = {
        "identity": row_identity(item),
        "status": "succeeded",
        "artifact_sha256": digest,
        "artifact_bytes": size,
        "seconds": 1.0,
    }
    index = {
        "index_version": "topolab.b2_4.index.v1",
        "plan_sha256": plan["plan_sha256"],
        "source_revision": label.source_revision,
        "environment": environment.model_dump(mode="json"),
        "rows": [row],
        "elapsed_seconds": 1.0,
        "peak_rss_bytes": 1,
    }
    _index_path(tmp_path).write_bytes(_canonical_bytes(index))
    assert _read_index(tmp_path, plan, label.source_revision, environment) == index
    assert _audit(tmp_path, plan, index, environment)["data_gate_passed"] is False

    changed = json.loads(_index_path(tmp_path).read_bytes())
    changed["rows"][0]["identity"]["result_id"] = "wrong"
    _index_path(tmp_path).write_bytes(_canonical_bytes(changed))
    with pytest.raises(ValueError, match="identity"):
        _read_index(tmp_path, plan, label.source_revision, environment)

    _index_path(tmp_path).write_bytes(_canonical_bytes(index))
    artifact = _artifact_path(tmp_path, label.case.case_id, digest)
    artifact.write_bytes(artifact.read_bytes() + b" ")
    with pytest.raises(ValueError, match="checksum"):
        _read_index(tmp_path, plan, label.source_revision, environment)
