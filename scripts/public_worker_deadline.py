"""Supervise a public software worker against caller-fixed absolute deadlines.

The supervisor runs outside the worker, so caught Python alarms and blocked
worker cleanup cannot extend its deadline. This is not a Docker/detached-process
containment proof, scientific admission, or authority to reopen a closed role.
The caller must separately observe this supervisor's actual return.
"""

import argparse
import json
import os
import signal
import subprocess
import time
import traceback
from pathlib import Path


def error_record(error: BaseException) -> dict:
    return {
        "type": type(error).__name__,
        "reason": str(error),
        "traceback": "".join(traceback.format_exception(error)),
    }


def write_once(path: Path, value: dict) -> None:
    raw = (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())


def execute(argv: list[str], output: Path, deadline_unix_ns: int, deadline_monotonic_ns: int):
    started_unix, started_mono = time.time_ns(), time.monotonic_ns()
    report = {
        "schema": "topolab.p17.worker-absolute-deadline.v1",
        "argv": argv,
        "started_unix_ns": started_unix,
        "started_monotonic_ns": started_mono,
        "deadline_unix_ns": deadline_unix_ns,
        "deadline_monotonic_ns": deadline_monotonic_ns,
        "primary_error": None,
        "secondary_errors": [],
        "worker_exit": None,
        "worker_reaped": False,
        "kill_requested": False,
        "status": "STOP",
        "input_accepted": False,
        "seed17_repaired": False,
        "own_future_tool_exit": "NOT_CLAIMED",
        "signal_scope": "OWNED_WORKER_PROCESS_GROUP_ONLY",
    }
    child = None
    created = False
    previous_unix = started_unix

    def remaining() -> float:
        nonlocal previous_unix
        now_unix, now_mono = time.time_ns(), time.monotonic_ns()
        if now_unix < previous_unix:
            raise ValueError("supervisor UTC clock moved backwards")
        previous_unix = now_unix
        left = min(deadline_unix_ns - now_unix, deadline_monotonic_ns - now_mono)
        if left <= 0:
            raise TimeoutError("original absolute worker deadline reached")
        return left / 10**9

    try:
        if not argv:
            raise ValueError("worker argv is required")
        if max(deadline_unix_ns - started_unix, deadline_monotonic_ns - started_mono) > 55e9:
            raise ValueError("worker deadline exceeds the public 55-second maximum")
        remaining()
        output.mkdir(mode=0o700)
        created = True
        write_once(output / "before-launch.json", report)
        with (output / "worker.stdout").open("xb") as stdout, (
            output / "worker.stderr"
        ).open("xb") as stderr:
            remaining()  # Metadata/filing time is charged before Popen too.
            child = subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                start_new_session=True,
                close_fds=True,
            )
            report["worker_pid"] = child.pid
            while True:
                try:
                    report["worker_exit"] = child.wait(timeout=min(0.05, remaining()))
                    report["worker_reaped"] = True
                    remaining()  # A late observation cannot establish an on-time exit.
                    break
                except subprocess.TimeoutExpired:
                    continue
        if report["worker_exit"] != 0:
            raise ValueError("worker returned a nonzero exit")
        report["status"] = "WORKER_EXITED"
    except BaseException as error:
        report["primary_error"] = error_record(error)
    finally:
        if child is not None and not report["worker_reaped"]:
            # The unreaped session leader pins the owned PID/PGID. Do not signal
            # a reaped PID, and never reset the work deadline to now + a suffix.
            report["kill_requested"] = True
            report["kill_requested_monotonic_ns"] = time.monotonic_ns()
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except BaseException as error:
                report["secondary_errors"].append(error_record(error))
            try:
                report["worker_exit"] = child.wait(timeout=2)
                report["worker_reaped"] = True
            except BaseException as error:
                report["secondary_errors"].append(error_record(error))
        report["finished_unix_ns"] = time.time_ns()
        report["finished_monotonic_ns"] = time.monotonic_ns()
        if created:
            try:
                write_once(output / "complete-before-own-return.json", report)
            except BaseException as error:
                # stdout remains a fallback packet when final filing fails.
                report["secondary_errors"].append(error_record(error))
                report["status"] = "STOP"
    return report


def main() -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--deadline-unix-ns", required=True, type=int)
    parser.add_argument("--deadline-monotonic-ns", required=True, type=int)
    parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    report = execute(argv, args.output, args.deadline_unix_ns, args.deadline_monotonic_ns)
    print(json.dumps(report, sort_keys=True), flush=True)
    return 0 if report["status"] == "WORKER_EXITED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
