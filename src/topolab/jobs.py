"""In-process optimization job lifecycle and isolated result storage."""

from collections.abc import Callable
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import StrEnum
from threading import Event, Lock
from uuid import uuid4

from pydantic import BaseModel, ConfigDict

from topolab.persistence import RunStore, StoredRun
from topolab.problem import TopologyProblem, TopologyResult, solve_problem
from topolab.simp import OptimizationCancelledError, SimpIteration

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
    status: RunStatus
    iteration: int
    cancel_requested: bool
    result: TopologyResult | None = None
    error: str | None = None


class RunNotFoundError(KeyError):
    """Raised when a run identifier is unknown."""


_RESTART_ERROR = "RunInterruptedError: process exited before run reached a terminal state"


@dataclass(slots=True)
class _RunState:
    problem: TopologyProblem
    status: RunStatus = RunStatus.QUEUED
    iteration: int = 0
    result: TopologyResult | None = None
    error: str | None = None
    cancel_event: Event = field(default_factory=Event)
    future: Future[None] | None = None


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
        self._runner = _run_problem if runner is None else runner
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
            state = _RunState(problem=problem)
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
            if state.future is not None and state.future.cancel():
                state.status = RunStatus.CANCELLED
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
        """Stop accepting work and close worker threads."""

        with self._lock:
            self._closed = True
            for run_id, state in self._runs.items():
                if state.status in {RunStatus.QUEUED, RunStatus.RUNNING}:
                    state.cancel_event.set()
                if state.status is RunStatus.QUEUED:
                    state.status = RunStatus.CANCELLED
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
                self._persist(run_id, state)
                return
            state.status = RunStatus.RUNNING
            self._persist(run_id, state)

        def on_iteration(iteration: SimpIteration) -> None:
            with self._lock:
                state.iteration = iteration.iteration
                self._persist(run_id, state)
            if state.cancel_event.is_set():
                raise OptimizationCancelledError("optimization was cancelled")

        try:
            result = self._runner(state.problem, state.cancel_event.is_set, on_iteration)
        except OptimizationCancelledError:
            with self._lock:
                state.status = RunStatus.CANCELLED
                self._persist(run_id, state)
        except Exception as error:
            with self._lock:
                state.status = RunStatus.FAILED
                state.error = f"{type(error).__name__}: {error}"
                self._persist(run_id, state)
        else:
            with self._lock:
                if state.cancel_event.is_set():
                    state.status = RunStatus.CANCELLED
                else:
                    state.status = RunStatus.SUCCEEDED
                    state.result = result
                self._persist(run_id, state)

    def _restore_runs(self) -> None:
        if self._store is None:
            return
        for stored in self._store.load_all():
            state = _RunState(
                problem=stored.problem,
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
            status=state.status,
            iteration=state.iteration,
            cancel_requested=state.cancel_event.is_set(),
            result=state.result,
            error=state.error,
        )


def _run_problem(
    problem: TopologyProblem,
    should_cancel: Callable[[], bool],
    iteration_callback: Callable[[SimpIteration], None],
) -> TopologyResult:
    return solve_problem(
        problem,
        should_cancel=should_cancel,
        iteration_callback=iteration_callback,
    )
