"""B2.21 terminal-target provenance and sealed development Gate."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest
import torch
from safetensors.torch import save as save_tensors

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_5_prototype import canonical_bytes, sha256  # noqa: E402
from b2_21_terminal_target import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    METHODS,
    _read_target,
    _target_path,
    cohorts,
    plan_payload,
    screen_summary,
)


def test_plan_freezes_b221_cases_and_terminal_intervention() -> None:
    groups, screen, blocked = cohorts()
    plan = plan_payload(groups, screen, blocked)
    assert plan["plan_sha256"] == EXPECTED_PLAN_SHA256
    assert plan["intervention"] == "uniform_terminal_design_instead_of_update_30_target"
    assert len(groups["train"]) == 468
    assert len(groups["validation"]) == 12
    assert len(screen) == 24
    assert len(blocked) == 712
    assert len({case.case_id for case in (*blocked, *screen)}) == 736


def test_validation_target_rejects_wrong_physical_volume(tmp_path: Path) -> None:
    groups, _, _ = cohorts()
    case = next(case for case in groups["validation"]
                if case.problem.mesh.element_counts == (12, 6, 3))
    nx, ny, nz = case.problem.mesh.element_counts
    context = {"plan_sha256": "test"}
    metadata = {"version": "topolab.b2_21.validation_target.v1",
                "context": context, "case_id": case.case_id,
                "iterations": 40, "compliance": 1.0}

    def persist(value: float) -> dict[str, object]:
        design = torch.from_numpy(np.full((1, nz, ny, nx), value, dtype=np.float32))
        contents = save_tensors({"design": design},
                                metadata={"topolab": canonical_bytes(metadata).decode()})
        digest = sha256(contents)
        path = _target_path(tmp_path, case.case_id, digest)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        return {"case_id": case.case_id, "iterations": 40, "compliance": 1.0,
                "target_sha256": digest, "target_bytes": len(contents)}

    good = persist(case.problem.optimization.volume_fraction)
    assert _read_target(tmp_path, good, case, context).shape == (1, nz, ny, nx)
    bad = persist(case.problem.optimization.minimum_density)
    with pytest.raises(ValueError, match="volume"):
        _read_target(tmp_path, bad, case, context)


def test_screen_gate_needs_high_volume_large_y_quality(tmp_path: Path) -> None:
    _, cases, _ = cohorts()
    (tmp_path / "screen_index.json").write_text("{}")
    rows = []
    for case in cases:
        scale = "small" if case.problem.mesh.element_counts[0] == 12 else "large"
        metadata = {"case_id": case.case_id, "scale": scale,
                    "direction": case.problem.loads[0].direction,
                    "volume": case.problem.optimization.volume_fraction}
        outcomes = [{"method": method, "succeeded": True,
                     "paired_time_ratio": 1.0 if method == "uniform" else (
                         1.1 if method.startswith("context_") else 0.8),
                     "operational": {"final_compliance": 1.0,
                                     "physical_volume_error": 0.0},
                     "uniform_reference_compliance": 1.0} for method in METHODS]
        rows.append({"case": metadata, "outcomes": outcomes})
    index = {"rows": rows, "elapsed_seconds": 100.0, "peak_rss_bytes": 1024}
    assert screen_summary(tmp_path, index)["gate_passed"]
    high = [row for row in rows if row["case"]["scale"] == "large"
            and row["case"]["direction"] == "y"
            and row["case"]["volume"] == 0.5915]
    assert len(high) == 2
    for item in high[0]["outcomes"]:
        if item["method"].startswith("terminal_"):
            item["succeeded"] = False
    result = screen_summary(tmp_path, index)
    assert result["high_volume_large_y_successes"] == 3
    assert not result["gate_passed"]
    assert json.loads(json.dumps(result))["passing_seeds"] == []
