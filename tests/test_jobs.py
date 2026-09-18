from collections.abc import Callable
from threading import Barrier, Event

import pytest

from topolab.jobs import RunManager, RunNotFoundError, RunStatus
from topolab.problem import (
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
    TopologyResult,
)
from topolab.simp import OptimizationCancelledError, SimpIteration


def test_run_manager_completes_a_numerical_problem() -> None:
    with RunManager(max_workers=1) as manager:
        submitted = manager.submit(_make_problem())
        completed = manager.wait(submitted.run_id, timeout=5.0)

    assert submitted.status in {RunStatus.QUEUED, RunStatus.RUNNING}
    assert completed.status is RunStatus.SUCCEEDED
    assert completed.iteration == 13
    assert completed.result is not None
    assert completed.result.converged
    assert completed.error is None


def test_two_runs_execute_concurrently_and_keep_results_isolated() -> None:
    barrier = Barrier(2)

    def concurrent_runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del should_cancel, iteration_callback
        barrier.wait(timeout=2.0)
        marker = float(problem.mesh.element_counts[0])
        return _result(marker)

    with RunManager(max_workers=2, runner=concurrent_runner) as manager:
        first_id = manager.submit(_make_problem(element_counts=(1, 1, 1))).run_id
        second_id = manager.submit(_make_problem(element_counts=(2, 1, 1))).run_id
        first = manager.wait(first_id, timeout=5.0)
        second = manager.wait(second_id, timeout=5.0)

    assert first.status is RunStatus.SUCCEEDED
    assert second.status is RunStatus.SUCCEEDED
    assert first.result is not None
    assert second.result is not None
    assert first.result.compliance == 1.0
    assert second.result.compliance == 2.0
    assert first.result is not second.result


def test_running_job_can_be_cancelled_cooperatively() -> None:
    started = Event()
    pause = Event()

    def cancellable_runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del problem, iteration_callback
        started.set()
        while not should_cancel():
            pause.wait(0.001)
        raise OptimizationCancelledError("optimization was cancelled")

    with RunManager(max_workers=1, runner=cancellable_runner) as manager:
        run_id = manager.submit(_make_problem()).run_id
        assert started.wait(timeout=2.0)
        assert manager.get(run_id).status is RunStatus.RUNNING
        assert manager.cancel(run_id)
        cancelled = manager.wait(run_id, timeout=5.0)

    assert cancelled.status is RunStatus.CANCELLED
    assert cancelled.cancel_requested
    assert cancelled.result is None
    assert not manager.cancel(run_id)


def test_queued_job_can_be_cancelled_before_execution() -> None:
    started = Event()
    release = Event()

    def blocking_runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del problem, should_cancel, iteration_callback
        started.set()
        release.wait(timeout=2.0)
        return _result(1.0)

    with RunManager(max_workers=1, runner=blocking_runner) as manager:
        running_id = manager.submit(_make_problem()).run_id
        assert started.wait(timeout=2.0)
        queued = manager.submit(_make_problem())
        assert queued.status is RunStatus.QUEUED
        assert manager.cancel(queued.run_id)
        cancelled = manager.wait(queued.run_id, timeout=5.0)
        release.set()
        running = manager.wait(running_id, timeout=5.0)

    assert cancelled.status is RunStatus.CANCELLED
    assert cancelled.iteration == 0
    assert running.status is RunStatus.SUCCEEDED


def test_shutdown_requests_running_cancellation() -> None:
    started = Event()
    pause = Event()

    def cancellable_runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del problem, iteration_callback
        started.set()
        while not should_cancel():
            pause.wait(0.001)
        raise OptimizationCancelledError("optimization was cancelled")

    manager = RunManager(max_workers=1, runner=cancellable_runner)
    run_id = manager.submit(_make_problem()).run_id
    assert started.wait(timeout=2.0)

    manager.shutdown()

    assert manager.get(run_id).status is RunStatus.CANCELLED


def test_failed_run_does_not_affect_another_run() -> None:
    def selective_runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del should_cancel, iteration_callback
        if problem.mesh.element_counts[0] == 1:
            raise ValueError("deliberate test failure")
        return _result(2.0)

    with RunManager(max_workers=2, runner=selective_runner) as manager:
        failed_id = manager.submit(_make_problem(element_counts=(1, 1, 1))).run_id
        successful_id = manager.submit(_make_problem(element_counts=(2, 1, 1))).run_id
        failed = manager.wait(failed_id, timeout=5.0)
        successful = manager.wait(successful_id, timeout=5.0)

    assert failed.status is RunStatus.FAILED
    assert failed.result is None
    assert failed.error == "ValueError: deliberate test failure"
    assert successful.status is RunStatus.SUCCEEDED
    assert successful.result is not None
    assert successful.error is None


def test_run_manager_rejects_unknown_ids_and_submissions_after_shutdown() -> None:
    manager = RunManager(max_workers=1)

    with pytest.raises(RunNotFoundError):
        manager.get("missing")

    manager.shutdown()
    with pytest.raises(RuntimeError, match="closed"):
        manager.submit(_make_problem())


def _result(marker: float) -> TopologyResult:
    return TopologyResult(
        design_density=(0.5,),
        physical_density=(0.5,),
        compliance=marker,
        displacements=(),
        reactions=(),
        history=(),
        converged=True,
    )


def _make_problem(
    *,
    element_counts: tuple[int, int, int] = (4, 2, 1),
) -> TopologyProblem:
    nx, ny, nz = element_counts
    loaded_node = nx + (nx + 1) * (ny + (ny + 1) * nz)
    return TopologyProblem(
        mesh=MeshDefinition(
            element_counts=element_counts,
            lengths=(float(nx), float(ny), float(nz)),
        ),
        material=MaterialDefinition(
            solid_modulus=1000.0,
            minimum_modulus=1.0,
            poisson_ratio=0.3,
        ),
        supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
        loads=(
            PointLoadDefinition(
                node=loaded_node,
                direction="y",
                magnitude=-1.0,
            ),
        ),
        optimization=OptimizationDefinition(
            volume_fraction=0.5,
            filter_radius=1.5,
            minimum_density=0.05,
            convergence_tolerance=0.01,
            max_iterations=60,
        ),
    )
