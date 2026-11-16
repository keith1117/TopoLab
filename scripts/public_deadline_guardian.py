"""Keep an isolated public entry's final filing under its original deadline.

Call arm_guardian before arbitrary work, with PID == PGID == SID. The guardian
stays in that group, so its membership pins the group even after parent death.
After every final fsync, cancel_and_reap observes the guardian's actual exit.
The caller must then use only memory/clock checks and os._exit: no further
filing, print, atexit or interpreter shutdown. Actual external return remains a
separate obligation; this does not promise scheduling or kernel-I/O bounds.
"""

import os
import select
import signal
import time
from collections import namedtuple

Guardian = namedtuple(
    "Guardian",
    "pid cancel_fd parent_pid process_group session deadline_unix_ns deadline_monotonic_ns "
    "armed_unix_ns armed_monotonic_ns",
)


def _remaining(deadline_unix_ns: int, deadline_monotonic_ns: int) -> float:
    left = min(deadline_unix_ns - time.time_ns(), deadline_monotonic_ns - time.monotonic_ns())
    if left <= 0:
        raise TimeoutError("original guardian deadline reached")
    return left / 10**9


def _kill_own_group() -> None:
    # The guardian never leaves the verified isolated group. Its own membership
    # pins the PGID; there is no parent-PID liveness check or PID-reuse race.
    os.killpg(os.getpgrp(), signal.SIGKILL)
    os._exit(125)


def _watch(
    cancel_fd: int, ready_fd: int, parent: int, group: int, utc: int, mono: int, initial_utc: int
) -> None:
    try:
        if os.getpgrp() != group or os.getsid(0) != group or os.getppid() != parent:
            _kill_own_group()
        for fd in (0, 1, 2):
            if fd not in (cancel_fd, ready_fd):
                try:
                    os.close(fd)
                except OSError:
                    pass
        _remaining(utc, mono)
        os.write(ready_fd, b"R")
        os.close(ready_fd)
        previous_utc = initial_utc
        while True:
            now_utc = time.time_ns()
            if now_utc < previous_utc:
                _kill_own_group()
            previous_utc = now_utc
            ready, _, _ = select.select([cancel_fd], [], [], min(0.02, _remaining(utc, mono)))
            if ready:
                token = os.read(cancel_fd, 2)
                _remaining(utc, mono)
                if token == b"C":
                    os._exit(0)
                # EOF means parent death or abandonment, not successful filing.
                _kill_own_group()
    except BaseException:
        _kill_own_group()


def arm_guardian(deadline_unix_ns: int, deadline_monotonic_ns: int) -> Guardian:
    """Arm before work in an already isolated entry; never create a new group."""
    parent, group, session = os.getpid(), os.getpgrp(), os.getsid(0)
    if not parent == group == session:
        raise ValueError("guardian requires an isolated session leader: PID == PGID == SID")
    if type(deadline_unix_ns) is not int or type(deadline_monotonic_ns) is not int:
        raise ValueError("guardian deadlines must be integer absolute nanoseconds")
    if max(deadline_unix_ns - time.time_ns(), deadline_monotonic_ns - time.monotonic_ns()) > 45e9:
        raise ValueError("guardian deadline exceeds the public 45-second maximum")
    _remaining(deadline_unix_ns, deadline_monotonic_ns)
    initial_utc = time.time_ns()
    cancel_r, cancel_w = os.pipe()
    ready_r, ready_w = os.pipe()
    try:
        pid = os.fork()
    except BaseException:
        for fd in (cancel_r, cancel_w, ready_r, ready_w):
            os.close(fd)
        raise
    if pid == 0:
        os.close(cancel_w)
        os.close(ready_r)
        _watch(
            cancel_r, ready_w, parent, group, deadline_unix_ns, deadline_monotonic_ns, initial_utc
        )
        os._exit(125)
    os.close(cancel_r)
    os.close(ready_w)
    try:
        ready, _, _ = select.select(
            [ready_r], [], [], _remaining(deadline_unix_ns, deadline_monotonic_ns)
        )
        if not ready or os.read(ready_r, 1) != b"R":
            raise RuntimeError("guardian did not acknowledge armed state")
        _remaining(deadline_unix_ns, deadline_monotonic_ns)
        return Guardian(
            pid, cancel_w, parent, group, session, deadline_unix_ns, deadline_monotonic_ns,
            time.time_ns(), time.monotonic_ns(),
        )
    except BaseException:
        # No positive-PID signal. EOF requests fail-closed termination by the
        # guardian in its still-pinned group, under the unchanged deadline.
        os.close(cancel_w)
        raise
    finally:
        os.close(ready_r)


def cancel_and_reap(guardian: Guardian) -> dict:
    """After final fsync, cancel once and observe waitpid before original limits."""
    if (os.getpid(), os.getpgrp(), os.getsid(0)) != (
        guardian.parent_pid, guardian.process_group, guardian.session
    ):
        raise ValueError("guardian belongs to another isolated parent")
    if time.time_ns() < guardian.armed_unix_ns:
        raise ValueError("parent UTC clock moved backwards")
    _remaining(guardian.deadline_unix_ns, guardian.deadline_monotonic_ns)
    try:
        if os.write(guardian.cancel_fd, b"C") != 1:
            raise RuntimeError("guardian cancellation was incomplete")
    finally:
        os.close(guardian.cancel_fd)
    while True:
        pid, status = os.waitpid(guardian.pid, os.WNOHANG)
        if pid == guardian.pid:
            break
        time.sleep(min(0.01, _remaining(guardian.deadline_unix_ns, guardian.deadline_monotonic_ns)))
    _remaining(guardian.deadline_unix_ns, guardian.deadline_monotonic_ns)
    return {
        "guardian_pid": guardian.pid,
        "parent_pid": guardian.parent_pid,
        "process_group": guardian.process_group,
        "session": guardian.session,
        "guardian_exit": os.waitstatus_to_exitcode(status),
        "guardian_reaped": True,
        "deadline_unix_ns": guardian.deadline_unix_ns,
        "deadline_monotonic_ns": guardian.deadline_monotonic_ns,
        "armed_unix_ns": guardian.armed_unix_ns,
        "armed_monotonic_ns": guardian.armed_monotonic_ns,
        "finished_unix_ns": time.time_ns(),
        "finished_monotonic_ns": time.monotonic_ns(),
    }
