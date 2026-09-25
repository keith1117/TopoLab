"""B2.3 budget-plan identity and immutable B2.2 comparison boundary."""

import hashlib
import json
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import b2_3_budget_sentinel as sentinel  # noqa: E402
from b2_2_data_feasibility import result_id as b22_result_id  # noqa: E402


def test_budget_plan_preserves_every_source_and_versions_each_result() -> None:
    cases = sentinel.select_cases()
    payload = sentinel.plan_payload(cases)

    assert payload["plan_sha256"] == sentinel.EXPECTED_PLAN_SHA256
    assert len(cases) == 61
    assert len({item.case.case_id for item in cases}) == 61
    assert len({item.metadata()["result_id"] for item in cases}) == 61
    assert all(item.case.problem.optimization.max_iterations == 240 for item in cases)
    assert all(item.source.case.problem.optimization.max_iterations == 120 for item in cases)
    assert all(item.case.case_id != item.source.case.case_id for item in cases)
    assert all(
        item.case.problem.model_dump(exclude={"optimization": {"max_iterations"}})
        == item.source.case.problem.model_dump(exclude={"optimization": {"max_iterations"}})
        for item in cases
    )


def test_prior_probe_requires_exact_checksum_order_and_outcomes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cases = sentinel.select_cases()
    rows = [
        {
            "case_id": item.source.case.case_id,
            "result_id": b22_result_id(item.source.case.case_id),
            "quality_passed": index < 53,
            "iterations": 20,
            "compliance": 1.0,
        }
        for index, item in enumerate(cases)
    ]
    document = {
        "source_revision": sentinel.B22_RUNNER_REVISION,
        "plan_sha256": sentinel.B22_PLAN_SHA256,
        "solver_policy": sentinel.PHYSICAL_PLATEAU_SOLVER_VERSION,
        "rows": rows,
    }
    path = tmp_path / "prior.json"

    def write_document() -> None:
        raw = json.dumps(document, sort_keys=True).encode()
        path.write_bytes(raw)
        monkeypatch.setattr(sentinel, "B22_PROBE_SHA256", hashlib.sha256(raw).hexdigest())

    write_document()
    assert len(sentinel.read_prior_probe(path, cases)) == 61

    document["rows"] = list(reversed(rows))
    write_document()
    with pytest.raises(ValueError, match="61-case order"):
        sentinel.read_prior_probe(path, cases)

    path.write_bytes(b"different bytes")
    with pytest.raises(ValueError, match="checksum"):
        sentinel.read_prior_probe(path, cases)


def test_sentinel_gate_requires_all_cases_and_resource_caps() -> None:
    rows = [{"quality_passed": True} for _ in range(61)]

    assert sentinel.gate_passed(rows, sentinel.MAX_SECONDS, sentinel.MAX_RSS_BYTES)
    assert not sentinel.gate_passed(rows[:-1], 1.0, 1)
    assert not sentinel.gate_passed(rows[:-1] + [{"quality_passed": False}], 1.0, 1)
    assert not sentinel.gate_passed(rows, sentinel.MAX_SECONDS + 1.0, 1)
    assert not sentinel.gate_passed(rows, 1.0, sentinel.MAX_RSS_BYTES + 1)
