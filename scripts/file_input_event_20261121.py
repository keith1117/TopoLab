"""Exact 20261121 original-call courier; no old scene, Original or payload access."""

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
signal = loader.load("nov21_exact_signal", path.with_name("await_input_receipt_20261121.py"))
INPUT_ID = "topolab.v2.p17-m2-registered-source-acquisition.20261121.v1"
EVIDENCE = Path("/Users/keith1117/Documents/TopoLab-data/metadata-input-acceptance-20261121")


def need(condition, reason):
    if not condition:
        raise ValueError("NOV21_COURIER: " + reason)


def admitted_packet_path(path):
    value = Path(path)
    need(
        value.is_absolute()
        and ".." not in value.parts
        and value.is_relative_to(EVIDENCE)
        and value != EVIDENCE,
        "exact NEW packet namespace required",
    )
    return value


def canonical(v):
    return (json.dumps(v, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def persist(packet, destination):
    target = Path(destination)
    need(
        (
            target.is_absolute()
            and ".." not in target.parts
            and (
                target.is_relative_to(EVIDENCE)
                or target == Path(signal.PUBLIC) / "certify-rehearsal-raw-actual-call.json"
            )
        ),
        "NEW courier target",
    )
    need(
        packet["schema"]
        in (
            "topolab.v2.m2-strict-source-binding.actual-call.v1",
            "topolab.m2-acquisition-caller-failure.v1",
            "topolab.input-caller-stop.20261121.v1",
        )
        and packet.get("author") in ("/root", "/root/full60_independent"),
        "packet schema/author differs",
    )
    raw = canonical(packet)
    need(len(raw) <= 16 * 1024**2, "unchanged metadata byte cap")
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
    saved = dict(path=str(target), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    if packet["schema"] == "topolab.m2-acquisition-caller-failure.v1":
        root = packet.get("caller_root")
        need(
            root in signal.ROOTS and packet.get("execution_identity") == INPUT_ID,
            "caller STOP exact NEW root/id",
        )
        notice = dict(
            schema="topolab.input-caller-stop.20261121.v1",
            execution_identity=INPUT_ID,
            root=root,
            author=packet["author"],
            original_failure=saved,
            source_or_payload_reads=0,
        )
        # First failure wins; each author's full packet has already been retained.
        try:
            persist(notice, signal.caller_stop_path(root))
        except FileExistsError:
            prior, _ = signal.read_metadata(signal.caller_stop_path(root))
            need(
                prior.get("execution_identity") == INPUT_ID and prior.get("root") == root,
                "existing caller STOP differs",
            )
    return saved


def exact_terminal(packet, argv, author, recovery):
    """Retain an actual nonzero SUP/REC exit; it never establishes acceptance."""
    core = recovery.load("p17_m2_source_binding")
    need(
        packet.get("schema") == "topolab.v2.m2-strict-source-binding.actual-call.v1"
        and packet.get("author") == author
        and packet.get("argv") == argv
        and packet.get("request", {}).get("cmd") == core.literal_command(argv)
        and packet["request"].get("workdir") == str(recovery.REPO),
        "original actual literal caller/command differs",
    )
    rows = packet.get("responses")
    need(isinstance(rows, list) and 1 <= len(rows) <= 65, "bounded original responses required")
    previous, session = None, None
    for index, row in enumerate(rows):
        result, args = row.get("result", {}), row.get("arguments", {})
        need(
            type(row.get("requested_ms")) is int
            and type(row.get("returned_ms")) is int
            and row["requested_ms"] <= row["returned_ms"]
            and (previous is None or previous <= row["requested_ms"])
            and isinstance(result.get("output"), str),
            "original terminal clocks/output incomplete",
        )
        need(
            "Warning: truncated output" not in result["output"]
            and "tokens truncated" not in result["output"]
            and (
                result.get("original_token_count") is None
                or result["original_token_count"] <= args.get("max_output_tokens", 10000)
            ),
            "truncated actual return rejected",
        )
        if index == 0:
            need(
                row.get("tool") == "exec_command" and args == packet["request"],
                "original exec request differs",
            )
        else:
            need(
                row.get("tool") == "write_stdin"
                and session is not None
                and type(args.get("session_id")) is int
                and args.get("session_id") == session
                and args.get("chars", "") == ""
                and type(args.get("yield_time_ms", 5000)) is int
                and 0 < args.get("yield_time_ms", 5000) <= 30000,
                "unowned/nonempty poll",
            )
        if index < len(rows) - 1:
            need(
                type(result.get("session_id")) is int
                and result.get("exit_code") is None
                and (session is None or session == result["session_id"]),
                "nonterminal session differs",
            )
            session = result["session_id"]
        else:
            need(
                type(result.get("exit_code")) is int and result.get("session_id") is None,
                "actual terminal return missing",
            )
        previous = row["returned_ms"]
    return rows[0]["requested_ms"], previous


def matching_pending(pending, plan, root, plan_sha, role, control):
    """The original pending must name this exact SUP/REC pair before REC is opened."""
    base = control.base()
    expected_full = base.CAPS.get(role, 180 if role == "final-filing" else None)
    need(
        pending.get("execution_identity") == INPUT_ID
        and pending.get("role") == role
        and pending.get("plan_sha256") == plan_sha
        and pending.get("status") == "PENDING_BEFORE_DISPATCH"
        and pending.get("frozen_FULL_seconds") == expected_full
        and type(pending.get("frozen_FULL_seconds")) is type(expected_full)
        and pending.get("external_argv")
        == [control.argv_for(Path(root), mode, plan_sha, role) for mode in ("supervise", "record")],
        "pending identity/role/plan/FULL/argv differs",
    )
    need(
        pending.get("clock_domain") == "functions.exec.Date.now.UTC-seconds"
        and pending.get("clock_resolution_seconds") == 0.001
        and signal.legacy.milliseconds(pending["actor_activation_UTC_seconds"])
        == signal.legacy.milliseconds(plan["actor_activation_UTC_seconds"])
        and all(
            pending.get(key) == plan[key]
            for key in (
                "actor_window_seconds",
                "actor_deadlines_UTC",
                "whole_start_ms",
                "whole_end_ms",
            )
        ),
        "pending original whole/actor clock differs",
    )


def file_event(root, plan_sha, role, mode, path, pin):
    need(root in signal.ROOTS and mode in ("supervise", "record"), "NEW root/mode")
    control = profiles.profile("control", INPUT_ID)
    recovery = profiles.profile("recovery", INPUT_ID)
    plan, raw = signal.read_metadata(Path(root) / "plan.json")
    need(hashlib.sha256(raw).hexdigest() == plan_sha, "plan SHA differs")
    signal.project(plan, raw, root)
    need(
        role in [*signal.ROLES, "final-filing", "lease-release", "public-consumer", "reader-ack"],
        "role differs",
    )
    path = admitted_packet_path(path)
    packet, raw = signal.read_metadata(Path(path))
    need(hashlib.sha256(raw).hexdigest() == pin, "raw packet SHA differs")
    author = "/root/full60_independent" if role.startswith("independent-") else "/root"
    first, last = exact_terminal(
        packet, control.argv_for(Path(root), mode, plan_sha, role), author, recovery
    )
    need(
        plan["whole_start_ms"] <= first <= last <= plan["whole_end_ms"],
        "NEW whole4500 original return",
    )
    result = packet["responses"][-1]["result"]
    base = control.base()
    folder = Path(root)
    pending = base.read_json(folder / "receipts" / (role + "-pending.json"))
    matching_pending(pending, plan, root, plan_sha, role, control)
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
        need(
            "".join(r["result"]["output"] for r in packet["responses"]).encode()
            == base.canonical(wire),
            "original record stdout differs",
        )
        event["observed_completion_sha256"] = base.sha(base.canonical(wire["completion"]))
        previous = base.read_json(folder / (role + "-supervise-actual-event.json"))
        need(
            previous["observed_pending_sha256"] == event["observed_pending_sha256"]
            and previous["end_seconds"] <= event["start_seconds"],
            "record predecessor differs",
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
