"""Real isolated public processes only; no formal role, Docker or source input."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/public_deadline_guardian.py"
LOAD = f"""
import importlib.util, json, os, signal, time
spec = importlib.util.spec_from_file_location('guardian', {str(SCRIPT)!r})
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
"""


def run_parent(code: str, *, isolated: bool = True) -> subprocess.CompletedProcess:
    child = subprocess.Popen(
        [sys.executable, "-I", "-c", LOAD + code],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        start_new_session=isolated,
    )
    try:
        stdout, stderr = child.communicate(timeout=4)
        return subprocess.CompletedProcess(child.args, child.returncode, stdout, stderr)
    finally:
        if child.poll() is None:
            if isolated:
                os.killpg(child.pid, signal.SIGKILL)
            else:
                child.kill()
            child.wait(timeout=2)


def arm_code(seconds: float = 0.7) -> str:
    return (
        f"guard = module.arm_guardian(time.time_ns() + int({seconds} * 10**9), "
        f"time.monotonic_ns() + int({seconds} * 10**9))\n"
    )


def test_cancel_reaps_guardian_before_unprotected_exit() -> None:
    result = run_parent(
        arm_code(2)
        + "receipt = module.cancel_and_reap(guard)\n"
        + "print(json.dumps(receipt), flush=True)\n"
        + "try:\n os.waitpid(guard.pid, os.WNOHANG)\n"
        + "except ChildProcessError:\n os._exit(0)\n"
        + "os._exit(91)\n"
    )
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["guardian_exit"] == 0
    assert receipt["guardian_reaped"] is True
    assert receipt["parent_pid"] == receipt["process_group"] == receipt["session"]
    assert receipt["guardian_pid"] != receipt["parent_pid"]
    assert receipt["finished_monotonic_ns"] < receipt["deadline_monotonic_ns"]


def test_deadline_covers_swallowed_alarm_and_blocked_final_filing(tmp_path: Path) -> None:
    fifo = tmp_path / "final-filing"
    os.mkfifo(fifo, 0o600)
    start = time.monotonic()
    result = run_parent(
        arm_code()
        + "def expired(*args):\n raise TimeoutError('caught alarm')\n"
        + "signal.signal(signal.SIGALRM, expired)\n"
        + "signal.setitimer(signal.ITIMER_REAL, 0.05)\n"
        + "try:\n time.sleep(20)\n"
        + "except BaseException:\n"
        + " print('blocked final filing', flush=True)\n"
        + f" open({str(fifo)!r}, 'wb')\n"
    )
    assert result.returncode == -signal.SIGKILL, result.stderr
    assert result.stdout == "blocked final filing\n"
    assert time.monotonic() - start < 3


def test_parent_death_does_not_leave_same_group_descendant(tmp_path: Path) -> None:
    import fcntl

    lock = tmp_path / "descendant.lock"
    sentinel = (
        "import fcntl, time; "
        f"f=open({str(lock)!r}, 'w'); fcntl.flock(f, fcntl.LOCK_EX); "
        "print('locked', flush=True); time.sleep(20)"
    )
    result = run_parent(
        arm_code(2)
        + "import subprocess, sys\n"
        + f"child = subprocess.Popen([sys.executable, '-I', '-c', {sentinel!r}], "
        + "stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, close_fds=True)\n"
        + "assert child.stdout.readline() == 'locked\\n'\n"
        + "os._exit(37)\n"
    )
    assert result.returncode == 37, result.stderr
    # EOF on the noninherited cancellation pipe makes the guardian stop its
    # still-pinned group, including the child, even though the leader exited.
    end = time.monotonic() + 2
    with lock.open() as stream:
        while True:
            try:
                fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                assert time.monotonic() < end
                time.sleep(0.01)


def test_nonisolated_parent_is_refused_without_signaling() -> None:
    result = run_parent(
        "try:\n "
        + arm_code(1)
        + "except ValueError as error:\n print(str(error), flush=True); os._exit(0)\n"
        + "os._exit(92)\n",
        isolated=False,
    )
    assert result.returncode == 0, result.stderr
    assert "isolated session leader" in result.stdout


def test_parent_backward_clock_cannot_cancel_successfully() -> None:
    result = run_parent(
        arm_code(2)
        + "module.time.time_ns = lambda: guard.armed_unix_ns - 1\n"
        + "try:\n module.cancel_and_reap(guard)\n"
        + "except ValueError as error:\n print(str(error), flush=True); os._exit(38)\n"
        + "os._exit(94)\n"
    )
    assert result.returncode == 38, result.stderr
    assert result.stdout == "parent UTC clock moved backwards\n"


@pytest.mark.parametrize("seconds", [-1, 46])
def test_invalid_absolute_deadline_refuses_guardian(seconds: float) -> None:
    result = run_parent(
        "try:\n "
        + arm_code(seconds)
        + "except (ValueError, TimeoutError) as error:\n"
        + " print(type(error).__name__, flush=True); os._exit(0)\n"
        + "os._exit(93)\n"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() in {"ValueError", "TimeoutError"}
