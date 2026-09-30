"""Optimization job lifecycle and isolated result storage."""

import os
import subprocess
import sys
from collections.abc import Callable
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from threading import Event, Lock
from uuid import uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, ValidationError

from topolab.persistence import RunStore, StoredRun
from topolab.problem import TopologyProblem, TopologyResult
from topolab.simp import OptimizationCancelledError, SimpIteration
from topolab.worker_protocol import (
    Cancel,
    Cancelled,
    Failed,
    Progress,
    Start,
    Started,
    Succeeded,
    encode,
    parse_event,
)

type JobRunner = Callable[
    [TopologyProblem, Callable[[], bool], Callable[[SimpIteration], None]],
    TopologyResult,
]


class RunStatus(StrEnum):
    """Lifecycle states for one optimization run."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RunSnapshot(BaseModel):
    """Immutable external view of one run."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    problem: TopologyProblem
    status: RunStatus
    iteration: int
    cancel_requested: bool
    result: TopologyResult | None = None
    error: str | None = None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class RunSummary(BaseModel):
    """Bounded history view without numerical result arrays."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    status: RunStatus
    iteration: int
    cancel_requested: bool
    error: str | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class RunPage(BaseModel):
    """One stable, newest-first page of run summaries."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    items: tuple[RunSummary, ...]
    next_cursor: str | None


class RunNotFoundError(KeyError):
    """Raised when a run identifier is unknown."""


class RunCursorError(ValueError):
    """Raised when a run-history cursor is unknown."""


class _WorkerFailure(Exception):
    """A failure already formatted by the worker protocol."""


_RESTART_ERROR = "RunInterruptedError: process exited before run reached a terminal state"


@dataclass(slots=True)
class _RunState:
    problem: TopologyProblem
    created_at: datetime
    updated_at: datetime
    status: RunStatus = RunStatus.QUEUED
    iteration: int = 0
    result: TopologyResult | None = None
    error: str | None = None
    cancel_event: Event = field(default_factory=Event)
    future: Future[None] | None = None
    process: subprocess.Popen[str] | None = None


class RunManager:
    """Run optimization jobs concurrently with isolated state and results."""

    def __init__(
        self,
        *,
        max_workers: int = 2,
        runner: JobRunner | None = None,
        store: RunStore | None = None,
    ) -> None:
        if isinstance(max_workers, bool) or not isinstance(max_workers, int):
            raise TypeError("max_workers must be an integer")
        if max_workers <= 0:
            raise ValueError("max_workers must be positive")
        self._runner = runner
        self._store = store
        self._runs: dict[str, _RunState] = {}
        self._lock = Lock()
        self._closed = False
        self._restore_runs()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="topolab-run",
        )

    def submit(self, problem: TopologyProblem) -> RunSnapshot:
        """Queue one immutable problem and return its initial snapshot."""

        if not isinstance(problem, TopologyProblem):
            raise TypeError("problem must be a TopologyProblem")
        run_id = uuid4().hex
        with self._lock:
            if self._closed:
                raise RuntimeError("run manager is closed")
            timestamp = datetime.now(UTC)
            state = _RunState(
                problem=problem,
                created_at=timestamp,
                updated_at=timestamp,
            )
            self._runs[run_id] = state
            try:
                self._persist(run_id, state)
            except Exception:
                del self._runs[run_id]
                raise
            state.future = self._executor.submit(self._execute, run_id)
            return self._snapshot(run_id, state)

    def get(self, run_id: str) -> RunSnapshot:
        """Return the current immutable snapshot for one run."""

        with self._lock:
            state = self._get_state(run_id)
            return self._snapshot(run_id, state)

    def list_runs(self, *, limit: int = 20, cursor: str | None = None) -> RunPage:
        """Return a stable newest-first page after an optional run-ID cursor."""

        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer")
        if limit <= 0 or limit > 100:
            raise ValueError("limit must lie within [1, 100]")
        with self._lock:
            ordered = sorted(
                self._runs.items(),
                key=lambda item: (item[1].created_at, item[0]),
                reverse=True,
            )
            start = 0
            if cursor is not None:
                try:
                    start = next(
                        index + 1
                        for index, (run_id, _) in enumerate(ordered)
                        if run_id == cursor
                    )
                except StopIteration as error:
                    raise RunCursorError(cursor) from error
            selected = ordered[start : start + limit]
            has_more = start + len(selected) < len(ordered)
            return RunPage(
                items=tuple(
                    self._summary(run_id, state) for run_id, state in selected
                ),
                next_cursor=selected[-1][0] if selected and has_more else None,
            )

    def cancel(self, run_id: str) -> bool:
        """Request cancellation, returning false for an already terminal run."""

        with self._lock:
            state = self._get_state(run_id)
            if state.status in {
                RunStatus.SUCCEEDED,
                RunStatus.FAILED,
                RunStatus.CANCELLED,
            }:
                return False
            state.cancel_event.set()
            self._send_cancel(run_id, state)
            if state.future is not None and state.future.cancel():
                state.status = RunStatus.CANCELLED
            _touch(state)
            self._persist(run_id, state)
            return True

    def wait(self, run_id: str, timeout: float | None = None) -> RunSnapshot:
        """Wait for one run to reach a terminal state and return its snapshot."""

        with self._lock:
            state = self._get_state(run_id)
            future = state.future
        if future is not None:
            try:
                future.result(timeout=timeout)
            except (CancelledError, OptimizationCancelledError):
                pass
        return self.get(run_id)

    def shutdown(self, *, wait: bool = True) -> None:
        """Stop accepting work and cancel active local workers."""

        with self._lock:
            self._closed = True
            for run_id, state in self._runs.items():
                if state.status not in {RunStatus.QUEUED, RunStatus.RUNNING}:
                    continue
                state.cancel_event.set()
                self._send_cancel(run_id, state)
                if state.status is RunStatus.QUEUED:
                    state.status = RunStatus.CANCELLED
                _touch(state)
                self._persist(run_id, state)
        self._executor.shutdown(wait=wait, cancel_futures=True)

    def __enter__(self) -> "RunManager":
        return self

    def __exit__(self, *args: object) -> None:
        self.shutdown()

    def _execute(self, run_id: str) -> None:
        with self._lock:
            state = self._get_state(run_id)
            if state.cancel_event.is_set():
                state.status = RunStatus.CANCELLED
                _touch(state)
                self._persist(run_id, state)
                return
            state.status = RunStatus.RUNNING
            _touch(state)
            self._persist(run_id, state)

        def on_iteration(iteration: SimpIteration) -> None:
            with self._lock:
                state.iteration = iteration.iteration
                _touch(state)
                self._persist(run_id, state)
            if state.cancel_event.is_set():
                raise OptimizationCancelledError("optimization was cancelled")

        try:
            if self._runner is None:
                result = self._run_worker(run_id, state)
            else:
                result = self._runner(state.problem, state.cancel_event.is_set, on_iteration)
        except OptimizationCancelledError:
            with self._lock:
                state.status = RunStatus.CANCELLED
                _touch(state)
                self._persist(run_id, state)
        except _WorkerFailure as error:
            with self._lock:
                state.status = RunStatus.FAILED
                state.error = str(error)
                _touch(state)
                self._persist(run_id, state)
        except Exception as error:
            with self._lock:
                state.status = RunStatus.FAILED
                state.error = f"{type(error).__name__}: {error}"
                _touch(state)
                self._persist(run_id, state)
        else:
            with self._lock:
                if state.cancel_event.is_set():
                    state.status = RunStatus.CANCELLED
                else:
                    state.status = RunStatus.SUCCEEDED
                    state.result = result
                _touch(state)
                self._persist(run_id, state)

    def _run_worker(self, run_id: str, state: _RunState) -> TopologyResult:
        environment = os.environ.copy()
        source_root = str(Path(__file__).resolve().parent.parent)
        environment["PYTHONPATH"] = os.pathsep.join(
            part for part in (source_root, environment.get("PYTHONPATH", "")) if part
        )
        process = subprocess.Popen(
            [sys.executable, "-m", "topolab.worker"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            env=environment,
        )
        assert process.stdin is not None
        assert process.stdout is not None
        terminal: Succeeded | Failed | Cancelled | None = None
        started = False
        try:
            process.stdin.write(encode(Start(run_id=run_id, problem=state.problem)))
            process.stdin.flush()
            with self._lock:
                state.process = process
                if state.cancel_event.is_set():
                    self._send_cancel(run_id, state)
            for line in process.stdout:
                try:
                    event = parse_event(line)
                except ValidationError as error:
                    raise _WorkerFailure("WorkerProtocolError: invalid worker event") from error
                if event.run_id != run_id or terminal is not None:
                    raise _WorkerFailure("WorkerProtocolError: unexpected worker event")
                if isinstance(event, Started):
                    if started or event.pid != process.pid:
                        raise _WorkerFailure("WorkerProtocolError: invalid worker start")
                    started = True
                elif not started:
                    raise _WorkerFailure("WorkerProtocolError: missing worker start")
                elif isinstance(event, Progress):
                    with self._lock:
                        if event.iteration <= state.iteration:
                            raise _WorkerFailure("WorkerProtocolError: nonincreasing iteration")
                        state.iteration = event.iteration
                        _touch(state)
                        self._persist(run_id, state)
                else:
                    terminal = event
            exit_code = process.wait()
            if exit_code != 0 or terminal is None:
                raise _WorkerFailure(f"WorkerProcessError: worker exited with status {exit_code}")
            if isinstance(terminal, Failed):
                raise _WorkerFailure(terminal.error)
            if isinstance(terminal, Cancelled):
                raise OptimizationCancelledError("optimization was cancelled")
            return terminal.result
        finally:
            with self._lock:
                state.process = None
            if process.poll() is None:
                process.kill()
                process.wait()
            process.stdin.close()
            process.stdout.close()

    @staticmethod
    def _send_cancel(run_id: str, state: _RunState) -> None:
        process = state.process
        if process is None or process.stdin is None:
            return
        try:
            process.stdin.write(encode(Cancel(run_id=run_id)))
            process.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    def _restore_runs(self) -> None:
        if self._store is None:
            return
        for stored in self._store.load_all():
            state = _RunState(
                problem=stored.problem,
                created_at=stored.created_at,
                updated_at=stored.updated_at,
                status=RunStatus(stored.status),
                iteration=stored.iteration,
                result=stored.result,
                error=stored.error,
            )
            if stored.cancel_requested:
                state.cancel_event.set()
            if state.status in {RunStatus.QUEUED, RunStatus.RUNNING}:
                state.status = RunStatus.FAILED
                state.result = None
                state.error = _RESTART_ERROR
                _touch(state)
                self._persist(stored.run_id, state)
            self._runs[stored.run_id] = state

    def _persist(self, run_id: str, state: _RunState) -> None:
        if self._store is None:
            return
        self._store.save(
            StoredRun(
                run_id=run_id,
                problem=state.problem,
                status=state.status.value,
                iteration=state.iteration,
                cancel_requested=state.cancel_event.is_set(),
                result=state.result,
                error=state.error,
                created_at=state.created_at,
                updated_at=state.updated_at,
            )
        )

    def _get_state(self, run_id: str) -> _RunState:
        try:
            return self._runs[run_id]
        except KeyError as error:
            raise RunNotFoundError(run_id) from error

    @staticmethod
    def _snapshot(run_id: str, state: _RunState) -> RunSnapshot:
        return RunSnapshot(
            run_id=run_id,
            problem=state.problem,
            status=state.status,
            iteration=state.iteration,
            cancel_requested=state.cancel_event.is_set(),
            result=state.result,
            error=state.error,
            created_at=state.created_at,
            updated_at=state.updated_at,
        )

    @staticmethod
    def _summary(run_id: str, state: _RunState) -> RunSummary:
        return RunSummary(
            run_id=run_id,
            status=state.status,
            iteration=state.iteration,
            cancel_requested=state.cancel_event.is_set(),
            error=state.error,
            created_at=state.created_at,
            updated_at=state.updated_at,
        )


def _touch(state: _RunState) -> None:
    state.updated_at = datetime.now(UTC)
