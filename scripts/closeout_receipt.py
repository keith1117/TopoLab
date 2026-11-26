"""Receive one shared closeout REC packet on an owned data-only terminal."""

import contextlib
import json
import os
import re
import signal
import sys
import termios
import time
import tty
from pathlib import Path

READY = b"CLOSEOUT_RECEIPT_READY_V1\n"
MAX_INPUT = 128 * 1024


def stamp():
    return {"utc_us": time.time_ns() // 1000, "monotonic_us": time.monotonic_ns() // 1000}


def deadline_arg(argv):
    if len(argv) != 2 or argv[0] != "--deadline-ms" or not re.fullmatch(r"[0-9]{13}", argv[1]):
        raise ValueError("the original absolute role cutoff is required")
    return int(argv[1])


@contextlib.contextmanager
def track_writes(wire, primary, backup, timing):
    """Stamp each ordinary exclusive write after its original fsync and readback."""
    original = wire.write_private
    named = {Path(primary): "primary_write_verified", Path(backup): "backup_write_verified"}

    def observed(path, raw):
        result = original(path, raw)
        key = named.get(Path(path))
        if key:
            if key in timing:
                raise ValueError("duplicate closeout receipt write")
            timing[key] = stamp()
        return result

    wire.write_private = observed
    try:
        yield
    finally:
        wire.write_private = original


def persist_record(wire, sibling, packet, timing):
    """Use the original paired writer and one-use registration ticket."""
    role = "shared-closeout"
    root = getattr(wire, "graph_root", wire.FORMAL)
    argv = packet["argv"]
    wire.need(
        packet.get("schema") == wire.ACTUAL_SCHEMA
        and packet.get("author") == "/root"
        and len(argv) == 10
        and re.fullmatch(r"[a-f0-9]{64}", argv[7])
        and argv == wire.control_argv(root, "record", argv[7], role),
        "expected this graph's shared-closeout native REC return",
    )
    wire.validate_terminal(packet, argv, "/root", str(wire.RUNTIME_REPO))
    stem = wire.actor_prefix("producer") + "-producer"
    name = f"{stem}-{role}-record-actual.json"
    destination = wire.EVIDENCE / name
    with track_writes(wire, destination, wire.BACKUP / name, timing):
        return sibling("cycle_filing_intent").persist_return(
            wire, sibling("build_staged_input_caller"), packet, str(destination)
        )


def serve(callback, deadline_ms):
    """Read one bounded JSON line, then exit after the paired result reaches stdout."""
    timing = {"worker_entered": stamp()}
    remaining = deadline_ms / 1000 - time.time()
    if not 0 < remaining <= 290 or not sys.stdin.isatty():
        raise ValueError("owned terminal and unexpired original role cutoff required")

    def expired(_signal, _frame):
        raise TimeoutError("closeout receipt worker deadline reached")

    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, remaining)
    os.umask(0o077)
    fd = sys.stdin.fileno()
    # Disable echo and canonical-line length limits before advertising readiness.
    tty.setraw(fd, termios.TCSANOW)
    sys.stdout.buffer.write(READY)
    sys.stdout.buffer.flush()
    raw = sys.stdin.buffer.readline(MAX_INPUT + 1)
    if not raw.endswith(b"\n") or len(raw) > MAX_INPUT:
        raise ValueError("bounded complete closeout packet required")
    packet = json.loads(raw)
    if not isinstance(packet, dict):
        raise ValueError("a single REC packet object is required")
    timing["packet_received"] = stamp()
    saved = callback(packet, timing)
    timing["before_result_write"] = stamp()
    result = {**saved, "timing": timing}
    sys.stdout.buffer.write(
        (json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n").encode()
    )
    sys.stdout.buffer.flush()


def formal(wire, sibling, argv):
    return serve(
        lambda packet, timing: persist_record(wire, sibling, packet, timing), deadline_arg(argv)
    )
