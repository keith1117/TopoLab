"""One local optimization process using the A2.1 JSON-line protocol."""

import os
import sys
from threading import Event, Thread

from topolab.problem import solve_problem
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
    parse_command,
)


def main() -> int:
    line = sys.stdin.readline()
    if not line:
        return 2
    try:
        start = parse_command(line)
    except ValueError:
        return 2
    if not isinstance(start, Start):
        return 2

    cancellation = Event()

    def read_controls() -> None:
        for control_line in sys.stdin:
            try:
                control = parse_command(control_line)
            except ValueError:
                cancellation.set()
                return
            if not isinstance(control, Cancel) or control.run_id != start.run_id:
                cancellation.set()
                return
            cancellation.set()
        cancellation.set()

    Thread(target=read_controls, daemon=True).start()

    def on_iteration(iteration: SimpIteration) -> None:
        _send(Progress(run_id=start.run_id, iteration=iteration.iteration))

    _send(Started(run_id=start.run_id, pid=os.getpid()))
    try:
        result = solve_problem(
            start.problem,
            should_cancel=cancellation.is_set,
            iteration_callback=on_iteration,
        )
    except OptimizationCancelledError:
        _send(Cancelled(run_id=start.run_id))
    except Exception as error:
        _send(Failed(run_id=start.run_id, error=f"{type(error).__name__}: {error}"))
    else:
        if cancellation.is_set():
            _send(Cancelled(run_id=start.run_id))
        else:
            _send(Succeeded(run_id=start.run_id, result=result))
    return 0


def _send(message: Started | Progress | Succeeded | Failed | Cancelled) -> None:
    sys.stdout.write(encode(message))
    sys.stdout.flush()


if __name__ == "__main__":
    raise SystemExit(main())
