import os
import sqlite3
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Event, Lock

import pytest

import topolab.jobs as jobs
from topolab.jobs import RunManager, RunStatus
from topolab.persistence import INTERRUPTED_ERROR, SqliteRunStore, StoredRun
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


def test_versioned_migrations_upgrade_and_reject_unknown_future_schema(tmp_path: Path) -> None:
    path = tmp_path / "runs.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE runs (run_id VARCHAR(32) PRIMARY KEY, "
            "problem_json TEXT NOT NULL, status VARCHAR(16) NOT NULL, "
            "iteration INTEGER NOT NULL, cancel_requested BOOLEAN NOT NULL, "
            "result_json TEXT, error TEXT)"
        )
    store = SqliteRunStore(path)
    store.close()
    with sqlite3.connect(path) as connection:
        assert connection.execute("PRAGMA user_version").fetchone() == (2,)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(runs)")}
        assert {"created_at", "updated_at", "owner_id", "lease_expires_at"} <= columns
    reopened = SqliteRunStore(path)
    reopened.close()
    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA user_version = 99")
    with pytest.raises(ValueError, match="newer than supported"):
        SqliteRunStore(path)


def test_claim_is_atomic_and_expired_owner_cannot_write(tmp_path: Path) -> None:
    store = SqliteRunStore(tmp_path / "runs.sqlite3")
    now = datetime(2026, 9, 30, tzinfo=UTC)
    queued = _stored("shared", "queued", now)
    store.insert_queued(queued)

    assert store.claim("shared", "owner-a", now, now + timedelta(seconds=5))
    assert not store.claim("shared", "owner-b", now, now + timedelta(seconds=5))
    with pytest.raises(ValueError, match="fenced write"):
        store.save(queued)
    assert not store.save_owned(queued, "owner-b", now)
    assert store.renew(
        "shared", "owner-a", now + timedelta(seconds=1), now + timedelta(seconds=6)
    ) == (True, False)
    store.recover_expired(now + timedelta(seconds=7))
    recovered = store.load_one("shared")
    assert recovered is not None
    assert recovered.status == "failed"
    assert recovered.error == INTERRUPTED_ERROR
    assert recovered.result is None
    assert not store.save_owned(queued, "owner-a", now + timedelta(seconds=7))
    store.close()


def test_cancelled_queued_record_cannot_be_claimed(tmp_path: Path) -> None:
    store = SqliteRunStore(tmp_path / "runs.sqlite3")
    now = datetime.now(UTC)
    store.insert_queued(_stored("queued", "queued", now))
    cancelled, accepted = store.request_cancel("queued", now)
    assert accepted
    assert cancelled is not None and cancelled.status == "cancelled"
    assert cancelled.cancel_requested
    assert not store.claim("queued", "owner", now, now + timedelta(seconds=10))
    store.close()


def test_remote_cancel_survives_progress_and_wins_terminal_race(tmp_path: Path) -> None:
    store = SqliteRunStore(tmp_path / "runs.sqlite3")
    now = datetime.now(UTC)
    queued = _stored("race", "queued", now)
    store.insert_queued(queued)
    lease = now + timedelta(seconds=10)
    assert store.claim("race", "owner", now, lease)
    _, accepted = store.request_cancel("race", now + timedelta(milliseconds=1))
    assert accepted

    stale_progress = replace(
        queued, status="running", owner_id="owner", lease_expires_at=lease,
        iteration=1, updated_at=now + timedelta(milliseconds=2),
    )
    assert store.save_owned(stale_progress, "owner", now + timedelta(milliseconds=2))
    after_progress = store.load_one("race")
    assert after_progress is not None and after_progress.cancel_requested

    stale_success = replace(stale_progress, status="succeeded", result=_result())
    assert store.save_owned(stale_success, "owner", now + timedelta(milliseconds=3))
    terminal = store.load_one("race")
    assert terminal is not None and terminal.status == "cancelled"
    assert terminal.cancel_requested and terminal.result is None
    assert terminal.owner_id is None
    store.close()


def test_restarted_manager_recovers_queued_run_once(tmp_path: Path) -> None:
    path = tmp_path / "runs.sqlite3"
    store = SqliteRunStore(path)
    store.insert_queued(_stored("queued", "queued", datetime.now(UTC)))
    store.close()
    calls = 0

    def runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        nonlocal calls
        del problem, should_cancel, iteration_callback
        calls += 1
        return _result()

    restarted_store = SqliteRunStore(path)
    with RunManager(store=restarted_store, runner=runner) as manager:
        completed = manager.wait("queued", timeout=5.0)
    restarted_store.close()

    assert completed.status is RunStatus.SUCCEEDED
    assert calls == 1


def test_recovered_queued_run_survives_shutdown_before_claim(tmp_path: Path) -> None:
    path = tmp_path / "runs.sqlite3"
    store = SqliteRunStore(path)
    now = datetime.now(UTC)
    store.insert_queued(_stored("a-running", "queued", now))
    store.insert_queued(_stored("b-queued", "queued", now))
    started = Event()

    def blocking_runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del problem, iteration_callback
        started.set()
        while not should_cancel():
            time.sleep(0.01)
        raise OptimizationCancelledError("optimization was cancelled")

    manager = RunManager(max_workers=1, store=store, runner=blocking_runner)
    assert started.wait(timeout=5.0)
    manager.shutdown()
    pending = store.load_one("b-queued")
    assert pending is not None and pending.status == "queued"
    store.close()

    restarted_store = SqliteRunStore(path)
    with RunManager(store=restarted_store, runner=lambda *args: _result()) as restarted:
        assert restarted.wait("b-queued", timeout=5.0).status is RunStatus.SUCCEEDED
    restarted_store.close()


def test_two_managers_do_not_duplicate_a_claim_and_remote_cancel_reaches_owner(
    tmp_path: Path,
) -> None:
    path = tmp_path / "runs.sqlite3"
    store_a = SqliteRunStore(path)
    store_a.insert_queued(_stored("shared", "queued", datetime.now(UTC)))
    store_b = SqliteRunStore(path)
    started = Event()
    calls = 0
    calls_lock = Lock()

    def runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        nonlocal calls
        del problem, iteration_callback
        with calls_lock:
            calls += 1
        started.set()
        while not should_cancel():
            time.sleep(0.01)
        raise OptimizationCancelledError("optimization was cancelled")

    with RunManager(store=store_a, runner=runner) as owner:
        assert started.wait(timeout=5.0)
        with RunManager(store=store_b, runner=runner) as observer:
            assert observer.get("shared").status is RunStatus.RUNNING
            assert observer.cancel("shared")
            assert owner.wait("shared", timeout=5.0).status is RunStatus.CANCELLED
            assert observer.get("shared").status is RunStatus.CANCELLED
    store_a.close()
    store_b.close()
    assert calls == 1


def test_heartbeat_keeps_a_live_owner_from_false_recovery(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(jobs, "_LEASE_DURATION", timedelta(milliseconds=300))
    monkeypatch.setattr(jobs, "_HEARTBEAT_INTERVAL", 0.05)
    path = tmp_path / "runs.sqlite3"
    store_a = SqliteRunStore(path)
    store_b = SqliteRunStore(path)
    started = Event()
    release = Event()

    def runner(
        problem: TopologyProblem,
        should_cancel: Callable[[], bool],
        iteration_callback: Callable[[SimpIteration], None],
    ) -> TopologyResult:
        del problem, should_cancel, iteration_callback
        started.set()
        assert release.wait(timeout=5.0)
        return _result()

    with RunManager(store=store_a, runner=runner) as owner:
        run_id = owner.submit(_problem()).run_id
        assert started.wait(timeout=5.0)
        time.sleep(0.7)
        with RunManager(store=store_b, runner=runner) as observer:
            assert observer.get(run_id).status is RunStatus.RUNNING
        release.set()
        assert owner.wait(run_id, timeout=5.0).status is RunStatus.SUCCEEDED
    store_a.close()
    store_b.close()


def test_api_process_crash_expires_its_run_without_replay(tmp_path: Path) -> None:
    database_path = tmp_path / "runs.sqlite3"
    run_id_path = tmp_path / "run-id.txt"
    example_path = (
        Path(__file__).resolve().parents[1]
        / "src/topolab/examples/canonical_demo_v1.json"
    )
    source_root = str(Path(__file__).resolve().parents[1] / "src")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        part for part in (source_root, environment.get("PYTHONPATH", "")) if part
    )
    script = """
import os, sys, time
from datetime import timedelta
from pathlib import Path
import topolab.jobs as jobs
from topolab.persistence import SqliteRunStore
from topolab.problem import TopologyProblem
jobs._LEASE_DURATION = timedelta(milliseconds=400)
jobs._HEARTBEAT_INTERVAL = 0.05
def runner(problem, should_cancel, iteration_callback):
    while True:
        time.sleep(0.1)
store = SqliteRunStore(sys.argv[1])
manager = jobs.RunManager(store=store, runner=runner)
problem = TopologyProblem.model_validate_json(Path(sys.argv[3]).read_text())
run_id = manager.submit(problem).run_id
while store.load_one(run_id).status != 'running':
    time.sleep(0.01)
Path(sys.argv[2]).write_text(run_id)
os._exit(0)
"""
    subprocess.run(
        [sys.executable, "-c", script, str(database_path), str(run_id_path), str(example_path)],
        env=environment,
        check=True,
        timeout=10,
    )
    run_id = run_id_path.read_text()
    time.sleep(0.6)
    store = SqliteRunStore(database_path)
    with RunManager(store=store) as restarted:
        recovered = restarted.get(run_id)
    store.close()
    assert recovered.status is RunStatus.FAILED
    assert recovered.error == INTERRUPTED_ERROR
    assert recovered.result is None


def test_worker_crash_is_persisted_and_does_not_leave_running_row(tmp_path: Path) -> None:
    store = SqliteRunStore(tmp_path / "runs.sqlite3")
    with RunManager(store=store) as manager:
        run_id = manager.submit(_problem()).run_id
        deadline = time.monotonic() + 5.0
        while True:
            with manager._lock:
                process = manager._runs[run_id].process
            if process is not None:
                break
            assert time.monotonic() < deadline
            time.sleep(0.01)
        process.kill()
        failed = manager.wait(run_id, timeout=10.0)
    persisted = store.load_one(run_id)
    store.close()
    assert failed.status is RunStatus.FAILED
    assert failed.error is not None and failed.error.startswith("WorkerProcessError")
    assert persisted is not None and persisted.status == "failed"
    assert persisted.owner_id is None


def test_local_worker_cancel_persists_terminal_state(tmp_path: Path) -> None:
    store = SqliteRunStore(tmp_path / "runs.sqlite3")
    with RunManager(store=store) as manager:
        run_id = manager.submit(_problem()).run_id
        deadline = time.monotonic() + 5.0
        while True:
            with manager._lock:
                process = manager._runs[run_id].process
            if process is not None:
                break
            assert time.monotonic() < deadline
            time.sleep(0.01)
        assert manager.cancel(run_id)
        cancelled = manager.wait(run_id, timeout=10.0)
    persisted = store.load_one(run_id)
    store.close()
    assert cancelled.status is RunStatus.CANCELLED
    assert persisted is not None and persisted.status == "cancelled"
    assert persisted.cancel_requested
    assert persisted.owner_id is None


def _stored(run_id: str, status: str, timestamp: datetime) -> StoredRun:
    return StoredRun(
        run_id=run_id,
        problem=_problem(),
        status=status,
        iteration=0,
        cancel_requested=False,
        result=None,
        error=None,
        created_at=timestamp,
        updated_at=timestamp,
    )


def _problem() -> TopologyProblem:
    return TopologyProblem(
        mesh=MeshDefinition(element_counts=(1, 1, 1)),
        material=MaterialDefinition(
            solid_modulus=1000.0, minimum_modulus=1.0, poisson_ratio=0.3
        ),
        supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
        loads=(PointLoadDefinition(node=7, direction="y", magnitude=-1.0),),
        optimization=OptimizationDefinition(volume_fraction=0.5, filter_radius=1.5),
    )


def _result() -> TopologyResult:
    return TopologyResult(
        design_density=(0.5,), physical_density=(0.5,), compliance=1.0,
        displacements=(), reactions=(), history=(), converged=True,
    )
