"""New public subprocesses only; no formal role or scientific input."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/public_worker_deadline.py"


def execute(
    tmp_path: Path, code: str, seconds: float = 1.0, argv: list[str] | None = None
) -> tuple[dict, Path]:
    output = tmp_path / "execution"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--output",
            str(output),
            "--deadline-unix-ns",
            str(time.time_ns() + int(seconds * 10**9)),
            "--deadline-monotonic-ns",
            str(time.monotonic_ns() + int(seconds * 10**9)),
            "--",
            *(argv if argv is not None else [sys.executable, "-u", "-c", code]),
        ],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    report = json.loads(result.stdout)
    assert result.returncode == (0 if report["status"] == "WORKER_EXITED" else 1)
    return report, output


def test_caught_work_alarm_cannot_postpone_hard_deadline(tmp_path: Path) -> None:
    report, output = execute(
        tmp_path,
        """
import signal, time
def expired(*args):
    raise TimeoutError('work alarm')
signal.signal(signal.SIGALRM, expired)
signal.setitimer(signal.ITIMER_REAL, 0.1)
try:
    time.sleep(20)
except BaseException:
    print('entered nested failure cleanup', flush=True)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(20)
""",
    )
    assert report["status"] == "STOP"
    assert report["primary_error"]["type"] == "TimeoutError"
    assert report["worker_exit"] == -signal.SIGKILL
    assert report["kill_requested"] is True
    assert report["worker_reaped"] is True
    assert "entered nested failure cleanup" in (output / "worker.stdout").read_text()
    assert report["kill_requested_monotonic_ns"] >= report["deadline_monotonic_ns"]
    assert report["finished_monotonic_ns"] - report["started_monotonic_ns"] < 2 * 10**9


@pytest.mark.parametrize("exit_code", [0, 37])
def test_early_exit_preserves_actual_exit_and_output(tmp_path: Path, exit_code: int) -> None:
    report, output = execute(
        tmp_path,
        f"import sys; print('worker output'); print('worker error', file=sys.stderr); "
        f"sys.exit({exit_code})",
        seconds=3,
    )
    assert report["worker_exit"] == exit_code
    assert report["worker_reaped"] is True
    assert report["kill_requested"] is False
    assert report["status"] == ("WORKER_EXITED" if exit_code == 0 else "STOP")
    assert (output / "worker.stdout").read_text() == "worker output\n"
    assert (output / "worker.stderr").read_text() == "worker error\n"
    assert json.loads((output / "complete-before-own-return.json").read_text()) == report
    assert report["input_accepted"] is report["seed17_repaired"] is False


def test_expired_deadline_refuses_launch_and_output_creation(tmp_path: Path) -> None:
    report, output = execute(tmp_path, "raise RuntimeError('must not launch')", seconds=-1)
    assert report["primary_error"]["type"] == "TimeoutError"
    assert report["worker_exit"] is None
    assert "worker_pid" not in report
    assert not output.exists()


def test_launch_failure_is_retained(tmp_path: Path) -> None:
    report, output = execute(tmp_path, "", seconds=3, argv=[str(tmp_path / "missing")])
    assert report["status"] == "STOP"
    assert report["worker_exit"] is None
    assert report["primary_error"]["type"] == "FileNotFoundError"
    assert json.loads((output / "complete-before-own-return.json").read_text()) == report


def test_blocked_worker_filing_cannot_hold_supervisor_open(tmp_path: Path) -> None:
    fifo = tmp_path / "blocked-filing"
    os.mkfifo(fifo, 0o600)
    report, _ = execute(
        tmp_path,
        f"print('starting blocked filing', flush=True); open({str(fifo)!r}, 'wb')",
    )
    assert report["primary_error"]["type"] == "TimeoutError"
    assert report["worker_exit"] == -signal.SIGKILL
    assert report["worker_reaped"] is True


def test_final_filing_failure_keeps_primary_error_in_stdout(tmp_path: Path) -> None:
    report, _ = execute(
        tmp_path,
        "from pathlib import Path; import sys; "
        f"Path({str(tmp_path / 'execution/complete-before-own-return.json')!r}).mkdir(); "
        "sys.exit(37)",
        seconds=3,
    )
    assert report["status"] == "STOP"
    assert report["worker_exit"] == 37
    assert report["primary_error"]["reason"] == "worker returned a nonzero exit"
    assert report["secondary_errors"][0]["type"] == "FileExistsError"


def test_same_group_descendant_is_killed_with_worker(tmp_path: Path) -> None:
    import fcntl

    lock = tmp_path / "descendant.lock"
    child_code = (
        "import fcntl, time; "
        f"f=open({str(lock)!r}, 'w'); "
        "fcntl.flock(f, fcntl.LOCK_EX); print('descendant locked', flush=True); time.sleep(20)"
    )
    code = (
        "import subprocess, sys, time; "
        f"subprocess.Popen([sys.executable, '-u', '-c', {child_code!r}]); time.sleep(20)"
    )
    report, output = execute(tmp_path, code)
    assert "descendant locked" in (output / "worker.stdout").read_text()
    assert report["worker_exit"] == -signal.SIGKILL
    with lock.open() as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
