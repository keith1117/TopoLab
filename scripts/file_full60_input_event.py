"""NEW exact original-call courier; no old scene, Original or payload access."""

import argparse
import hashlib
import json
import os
import sys
import types
from pathlib import Path

path = Path(__file__).with_name("full60_input_loader.py")
loader = sys.modules.get("full60_input_loader")
if loader is None or Path(loader.__file__).resolve() != path.resolve():
    loader = types.ModuleType("full60_input_loader")
    loader.__file__ = str(path)
    sys.modules[loader.__name__] = loader
    raw = path.read_bytes()
    exec(compile(raw, str(path), "exec"), loader.__dict__)
    loader.loaded_source_sha256[str(path.resolve())] = loader.hashlib.sha256(raw).hexdigest()
entry = Path(__file__).resolve()
loader.loaded_source_sha256[str(entry)] = loader.hashlib.sha256(entry.read_bytes()).hexdigest()
loader.install(require_locked_environment=True)
profiles = loader.load("p17_m2_input_continuation", path.with_name("p17_m2_input_continuation.py"))
signal = loader.load("full60_exact_signal", path.with_name("await_full60_input_receipt.py"))
EVIDENCE = Path(profiles.FULL60_EVIDENCE)


def canonical(v):
    return (json.dumps(v, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def persist(packet, destination):
    target = Path(destination)
    assert (
        target.is_absolute()
        and ".." not in target.parts
        and (
            target.is_relative_to(EVIDENCE)
            or target == Path(signal.PUBLIC) / "certify-rehearsal-raw-actual-call.json"
        )
    ), "NEW courier target"
    assert packet["schema"] in (
        "topolab.v2.m2-strict-source-binding.actual-call.v1",
        "topolab.m2-acquisition-caller-failure.v1",
    )
    raw = canonical(packet)
    assert len(raw) <= 16 * 1024**2
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in target.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = child
        fd = os.open(
            target.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent
        )
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)
    return dict(path=str(target), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))


def file_event(root, plan_sha, role, mode, path, pin):
    assert root in signal.ROOTS and mode in ("supervise", "record"), "NEW root/mode"
    control = profiles.profile("control", profiles.FULL60_INPUT)
    recovery = profiles.profile("recovery", profiles.FULL60_INPUT)
    plan, raw = signal.read_metadata(Path(root) / "plan.json")
    assert hashlib.sha256(raw).hexdigest() == plan_sha
    signal.project(plan, raw, root)
    assert role in [*signal.ROLES, "final-filing", "lease-release", "public-consumer", "reader-ack"]
    assert Path(path).is_relative_to(EVIDENCE), "NEW raw packet namespace"
    packet, raw = signal.read_metadata(Path(path))
    assert hashlib.sha256(raw).hexdigest() == pin
    author = "/root/full60_independent" if role.startswith("independent-") else "/root"
    first, last = recovery.exact_actual(
        packet, control.argv_for(Path(root), mode, plan_sha, role), author
    )
    assert plan["whole_start_ms"] <= first <= last <= plan["whole_end_ms"], (
        "NEW whole4500 original return"
    )
    result = packet["responses"][-1]["result"]
    base = control.base()
    folder = Path(root)
    pending = base.read_json(folder / "receipts" / (role + "-pending.json"))
    event = dict(
        event_id=packet["event_id"],
        author=author,
        argv=packet["argv"],
        start_seconds=first / 1000,
        end_seconds=last / 1000,
        wall_seconds=(last - first) / 1000,
        exit_code=result["exit_code"],
        complete=True,
        clock_domain="functions.exec.Date.now.UTC-seconds",
        raw_packet_sha256=pin,
        observed_pending_sha256=base.sha(base.canonical(pending)),
    )
    if mode == "record":
        wire = base.read_json(folder / "receipts" / (role + "-wire.json"))
        assert "".join(
            r["result"]["output"] for r in packet["responses"]
        ).encode() == base.canonical(wire)
        event["observed_completion_sha256"] = base.sha(base.canonical(wire["completion"]))
        previous = base.read_json(folder / (role + "-supervise-actual-event.json"))
        assert (
            previous["observed_pending_sha256"] == event["observed_pending_sha256"]
            and previous["end_seconds"] <= event["start_seconds"]
        )
    base.put(folder / (role + "-" + mode + "-actual-event.json"), event)
    if mode == "record":
        base.put(folder / (role + "-events.json"), [previous, event])
    return dict(
        status="ACTUAL_EVENT_FILED",
        role=role,
        mode=mode,
        exit_code=result["exit_code"],
        new_source_reads=0,
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("persist", "file"))
    for name in (
        "packet-json",
        "destination",
        "root",
        "plan-sha",
        "role",
        "event-mode",
        "packet",
        "packet-sha",
    ):
        p.add_argument("--" + name)
    a = p.parse_args()
    os.umask(0o077)
    value = (
        persist(json.loads(a.packet_json), a.destination)
        if a.mode == "persist"
        else file_event(a.root, a.plan_sha, a.role, a.event_mode, a.packet, a.packet_sha)
    )
    print(canonical(value).decode(), end="")


if __name__ == "__main__":
    main()
