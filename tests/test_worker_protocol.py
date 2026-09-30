import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from topolab.problem import (
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)
from topolab.worker_protocol import (
    Cancel,
    Cancelled,
    Progress,
    Start,
    Started,
    Succeeded,
    encode,
    parse_command,
    parse_event,
)


def test_protocol_rejects_wrong_version_and_extra_fields() -> None:
    with pytest.raises(ValidationError):
        parse_command('{"version":"other","kind":"cancel","run_id":"r"}')
    with pytest.raises(ValidationError):
        parse_event(
            '{"version":"topolab.a2.worker.v1","kind":"progress",'
            '"run_id":"r","iteration":1,"unrecognized":true}'
        )


def test_local_worker_process_sends_typed_progress_and_result() -> None:
    with _worker_process() as process:
        assert process.stdin is not None
        assert process.stdout is not None
        process.stdin.write(encode(Start(run_id="test-run", problem=_problem())))
        process.stdin.flush()
        events = [parse_event(line) for line in process.stdout]
        assert process.wait(timeout=10) == 0

    assert isinstance(events[0], Started)
    assert events[0].pid == process.pid
    assert events[0].pid != os.getpid()
    assert any(isinstance(event, Progress) for event in events)
    assert isinstance(events[-1], Succeeded)
    assert events[-1].result.converged
    assert all(event.run_id == "test-run" for event in events)


def test_local_worker_process_accepts_cooperative_cancel() -> None:
    with _worker_process() as process:
        assert process.stdin is not None
        assert process.stdout is not None
        process.stdin.write(encode(Start(run_id="cancel-run", problem=_problem())))
        process.stdin.flush()
        assert isinstance(parse_event(process.stdout.readline()), Started)
        process.stdin.write(encode(Cancel(run_id="cancel-run")))
        process.stdin.flush()
        events = [parse_event(line) for line in process.stdout]
        assert process.wait(timeout=10) == 0

    assert isinstance(events[-1], Cancelled)
    assert all(event.run_id == "cancel-run" for event in events)


def test_worker_cancels_when_manager_pipe_closes() -> None:
    with _worker_process() as process:
        assert process.stdin is not None
        assert process.stdout is not None
        process.stdin.write(encode(Start(run_id="orphan", problem=_problem())))
        process.stdin.flush()
        assert isinstance(parse_event(process.stdout.readline()), Started)
        process.stdin.close()
        events = [parse_event(line) for line in process.stdout]
        assert process.wait(timeout=10) == 0

    assert isinstance(events[-1], Cancelled)


def _worker_process() -> subprocess.Popen[str]:
    environment = os.environ.copy()
    source_root = str(Path(__file__).resolve().parents[1] / "src")
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (source_root, environment.get("PYTHONPATH", "")) if part
    )
    return subprocess.Popen(
        [sys.executable, "-m", "topolab.worker"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        env=environment,
    )


def _problem() -> TopologyProblem:
    return TopologyProblem(
        mesh=MeshDefinition(element_counts=(4, 2, 1), lengths=(4.0, 2.0, 1.0)),
        material=MaterialDefinition(
            solid_modulus=1000.0,
            minimum_modulus=1.0,
            poisson_ratio=0.3,
        ),
        supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
        loads=(PointLoadDefinition(node=29, direction="y", magnitude=-1.0),),
        optimization=OptimizationDefinition(
            volume_fraction=0.5,
            filter_radius=1.5,
            minimum_density=0.05,
            convergence_tolerance=0.01,
            max_iterations=60,
        ),
    )
