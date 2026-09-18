import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event

import pytest

from topolab.jobs import RunCursorError, RunManager, RunStatus
from topolab.persistence import SqliteRunStore, StoredRun
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


def test_completed_runs_survive_restart_and_keep_results_isolated(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "runs.sqlite3"

    def runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del should_cancel, iteration_callback
        return _result(float(problem.mesh.element_counts[0]))

    store = SqliteRunStore(database_path)
    with RunManager(max_workers=2, runner=runner, store=store) as manager:
        first_id = manager.submit(_problem(element_counts=(1, 1, 1))).run_id
        second_id = manager.submit(_problem(element_counts=(2, 1, 1))).run_id
        assert manager.wait(first_id, timeout=5.0).status is RunStatus.SUCCEEDED
        assert manager.wait(second_id, timeout=5.0).status is RunStatus.SUCCEEDED
    store.close()

    restored_store = SqliteRunStore(database_path)
    with RunManager(max_workers=1, store=restored_store) as restored_manager:
        first = restored_manager.get(first_id)
        second = restored_manager.get(second_id)
    restored_store.close()

    assert first.status is RunStatus.SUCCEEDED
    assert second.status is RunStatus.SUCCEEDED
    assert first.result is not None
    assert second.result is not None
    assert first.result.compliance == 1.0
    assert second.result.compliance == 2.0
    assert first.result is not second.result
    assert first.created_at <= first.updated_at
    assert second.created_at <= second.updated_at


def test_restart_marks_interrupted_run_failed_and_persists_the_transition(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "runs.sqlite3"
    store = SqliteRunStore(database_path)
    timestamp = datetime(2026, 9, 18, tzinfo=UTC)
    store.save(
        StoredRun(
            run_id="interrupted",
            problem=_problem(),
            status=RunStatus.RUNNING.value,
            iteration=7,
            cancel_requested=False,
            result=None,
            error=None,
            created_at=timestamp,
            updated_at=timestamp,
        )
    )
    store.close()

    restored_store = SqliteRunStore(database_path)
    with RunManager(max_workers=1, store=restored_store) as manager:
        interrupted = manager.get("interrupted")
    restored_store.close()

    assert interrupted.status is RunStatus.FAILED
    assert interrupted.iteration == 7
    assert interrupted.result is None
    assert interrupted.error == (
        "RunInterruptedError: process exited before run reached a terminal state"
    )

    verified_store = SqliteRunStore(database_path)
    persisted = verified_store.load_all()
    verified_store.close()
    assert len(persisted) == 1
    assert persisted[0].status == RunStatus.FAILED.value
    assert persisted[0].error == interrupted.error


def test_failed_and_cancelled_terminal_states_survive_restart(tmp_path: Path) -> None:
    database_path = tmp_path / "runs.sqlite3"
    started = Event()
    pause = Event()

    def runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del iteration_callback
        if problem.mesh.element_counts[0] == 1:
            raise ValueError("deliberate test failure")
        started.set()
        while not should_cancel():
            pause.wait(0.001)
        raise OptimizationCancelledError("optimization was cancelled")

    store = SqliteRunStore(database_path)
    with RunManager(max_workers=2, runner=runner, store=store) as manager:
        failed_id = manager.submit(_problem()).run_id
        failed = manager.wait(failed_id, timeout=5.0)
        cancelled_id = manager.submit(_problem(element_counts=(2, 1, 1))).run_id
        assert started.wait(timeout=2.0)
        assert manager.cancel(cancelled_id)
        cancelled = manager.wait(cancelled_id, timeout=5.0)
    store.close()

    assert failed.status is RunStatus.FAILED
    assert cancelled.status is RunStatus.CANCELLED

    restored_store = SqliteRunStore(database_path)
    with RunManager(max_workers=1, store=restored_store) as restored_manager:
        restored_failed = restored_manager.get(failed_id)
        restored_cancelled = restored_manager.get(cancelled_id)
    restored_store.close()

    assert restored_failed.status is RunStatus.FAILED
    assert restored_failed.error == "ValueError: deliberate test failure"
    assert restored_failed.result is None
    assert restored_cancelled.status is RunStatus.CANCELLED
    assert restored_cancelled.cancel_requested
    assert restored_cancelled.result is None


def test_history_pages_are_stable_across_equal_timestamps_and_restart(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "runs.sqlite3"
    start = datetime(2026, 9, 18, tzinfo=UTC)
    store = SqliteRunStore(database_path)
    for run_id, created_at in (
        ("oldest", start),
        ("middle-a", start + timedelta(seconds=1)),
        ("middle-b", start + timedelta(seconds=1)),
        ("newest", start + timedelta(seconds=2)),
    ):
        store.save(_completed_run(run_id, created_at))
    store.close()

    def runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del problem, should_cancel, iteration_callback
        return _result(2.0)

    restored_store = SqliteRunStore(database_path)
    with RunManager(max_workers=1, runner=runner, store=restored_store) as manager:
        first_page = manager.list_runs(limit=2)
        inserted_id = manager.submit(_problem()).run_id
        assert manager.wait(inserted_id, timeout=5.0).status is RunStatus.SUCCEEDED
        second_page = manager.list_runs(
            limit=2,
            cursor=first_page.next_cursor,
        )
        with pytest.raises(RunCursorError):
            manager.list_runs(cursor="unknown")
    restored_store.close()

    assert [run.run_id for run in first_page.items] == ["newest", "middle-b"]
    assert first_page.next_cursor == "middle-b"
    assert [run.run_id for run in second_page.items] == ["middle-a", "oldest"]
    assert inserted_id not in {run.run_id for run in second_page.items}
    assert second_page.next_cursor is None


@pytest.mark.parametrize("limit", [True, 0, 101])
def test_history_rejects_invalid_page_limits(limit: object) -> None:
    with RunManager(max_workers=1) as manager:
        with pytest.raises((TypeError, ValueError)):
            manager.list_runs(limit=limit)  # type: ignore[arg-type]


def test_store_migrates_pre_timestamp_database(tmp_path: Path) -> None:
    database_path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE runs (
                run_id VARCHAR(32) PRIMARY KEY,
                problem_json TEXT NOT NULL,
                status VARCHAR(16) NOT NULL,
                iteration INTEGER NOT NULL,
                cancel_requested BOOLEAN NOT NULL,
                result_json TEXT,
                error TEXT
            )
            """
        )
        connection.execute(
            """
            INSERT INTO runs (
                run_id, problem_json, status, iteration,
                cancel_requested, result_json, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "legacy",
                _problem().model_dump_json(),
                RunStatus.SUCCEEDED.value,
                3,
                False,
                _result(1.0).model_dump_json(),
                None,
            ),
        )

    store = SqliteRunStore(database_path)
    migrated = store.load_all()
    store.close()

    assert len(migrated) == 1
    assert migrated[0].run_id == "legacy"
    assert migrated[0].created_at.tzinfo is UTC
    assert migrated[0].updated_at == migrated[0].created_at


def _problem(
    *,
    element_counts: tuple[int, int, int] = (1, 1, 1),
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
            max_iterations=10,
        ),
    )


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


def _completed_run(run_id: str, created_at: datetime) -> StoredRun:
    return StoredRun(
        run_id=run_id,
        problem=_problem(),
        status=RunStatus.SUCCEEDED.value,
        iteration=3,
        cancel_requested=False,
        result=_result(1.0),
        error=None,
        created_at=created_at,
        updated_at=created_at + timedelta(milliseconds=1),
    )
