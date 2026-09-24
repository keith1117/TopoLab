import json
import os
import subprocess
import sys
from importlib.resources import files
from pathlib import Path

import pytest

from topolab.demo import DEMO_CASE_VERSION, load_canonical_demo_problem
from topolab.jobs import RunSnapshot, RunStatus
from topolab.problem import TopologyProblem

ROOT = Path(__file__).resolve().parents[1]


def test_canonical_demo_is_exactly_a_public_problem() -> None:
    payload = json.loads(
        files("topolab")
        .joinpath("examples/canonical_demo_v1.json")
        .read_text(encoding="utf-8")
    )
    problem = load_canonical_demo_problem()

    assert DEMO_CASE_VERSION == "canonical-demo.v1"
    assert problem.model_dump(mode="json", exclude_none=True) == payload
    assert TopologyProblem.model_validate_json(problem.model_dump_json()) == problem
    assert problem.mesh.element_counts == (4, 2, 2)
    assert problem.loads[0].node == 44
    assert problem.optimization.max_iterations == 60


def test_canonical_demo_cli_completes_and_saves_reusable_snapshot(tmp_path: Path) -> None:
    completed = _run_demo(tmp_path)

    assert completed.returncode == 0, completed.stderr
    summary = json.loads(completed.stdout)
    result_path = Path(summary["result_path"])
    snapshot = RunSnapshot.model_validate_json(result_path.read_text(encoding="utf-8"))

    assert summary["case_version"] == DEMO_CASE_VERSION
    assert summary["run_id"] == snapshot.run_id
    assert result_path.parent == tmp_path
    assert result_path.name == f"{DEMO_CASE_VERSION}-{snapshot.run_id}.json"
    assert snapshot.problem == load_canonical_demo_problem()
    assert snapshot.status is RunStatus.SUCCEEDED
    assert snapshot.result is not None
    assert snapshot.result.converged
    assert snapshot.iteration == len(snapshot.result.history)
    assert summary["status"] == "succeeded"
    assert summary["converged"] is True
    assert summary["compliance"] == snapshot.result.compliance
    assert summary["compliance"] > 0.0
    assert summary["volume_fraction"] == pytest.approx(
        sum(snapshot.result.physical_density) / len(snapshot.result.physical_density)
    )
    assert abs(summary["volume_fraction"] - 0.5) <= 5e-3


def test_canonical_demo_rejects_repository_output(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    output_dir = tmp_path / "results"

    completed = _run_demo(output_dir)

    assert completed.returncode == 2
    assert "outside a Git repository" in completed.stderr
    assert not output_dir.exists()


def _run_demo(output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "topolab.demo", "--output-dir", str(output_dir)],
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )
