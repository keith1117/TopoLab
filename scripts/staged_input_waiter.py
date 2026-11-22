"""Bounded read-only new staged plan, predecessor and caller-STOP signaling."""

import argparse
import json
import time
import types
from decimal import Decimal
from pathlib import Path

if "wire" not in globals():
    path = Path(__file__).with_name("staged_input_filer.py")
    wire = types.ModuleType("staged_input_wire_for_waiter")
    wire.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), "exec"), wire.__dict__)
    window = wire.source_module("staged_input_window", path.with_name("staged_input_window.py"))



def milliseconds(seconds):
    value = Decimal(str(seconds)) * 1000
    wire.need(
        value.is_finite() and value == value.to_integral_value(), "exact milliseconds required"
    )
    return int(value)


def project(plan, raw, root, now_ms):
    wire.need(
        root in wire.ROOTS
        and plan.get("execution_identity") == wire.IDENTITY
        and plan.get("root") == root
        and plan.get("formal_authority") is (root == wire.FORMAL)
        and plan.get("scope")
        == (
            "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
            if root == wire.FORMAL
            else "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
        )
        and plan.get("actor_window_seconds") == 4500
        and plan.get("role_order") == list(wire.ROLES),
        "new literal plan identity/root/scope/order differs",
    )
    wire.check_executed(plan)
    window.check(plan, now_ms)
    start = milliseconds(plan["actor_activation_UTC_seconds"])
    wire.need(start == plan["whole_start_ms"], "original activation clock differs")
    return dict(
        root=root,
        plan_sha256=wire.sha(raw),
        execution_identity=wire.IDENTITY,
        formal_authority=plan["formal_authority"],
        scope=plan["scope"],
        actor_window_seconds=4500,
        actor_start_ms=start,
        whole_start_ms=start,
        whole_end_ms=plan["whole_end_ms"],
        role_order=list(wire.ROLES),
        coordination_limit_ms=240000,
        applicable_deadline_ms=plan["whole_end_ms"],
    )


def predecessor(value, plan_sha, role):
    proof, events = value.get("result", {}), value.get("raw_tool_events", [])
    wire.need(
        proof.get("full_role_evidence_accepted") is True
        and proof.get("evidence_complete") is True
        and proof.get("role") == role
        and proof.get("execution_identity") == wire.IDENTITY
        and proof.get("plan_sha256") == plan_sha
        and proof.get("actual_exit_codes") == [0, 0]
        and isinstance(events, list)
        and len(events) == 2
        and all(
            event.get("complete") is True
            and event.get("exit_code") == 0
            and event.get("clock_domain") == "functions.exec.Date.now.UTC-seconds"
            for event in events
        ),
        "complete accepted predecessor required",
    )
    first, last = milliseconds(events[0]["start_seconds"]), milliseconds(events[-1]["end_seconds"])
    wire.need(
        first == milliseconds(proof["T0"]) and last == milliseconds(proof["T1"]) and first <= last,
        "accepted predecessor endpoints differ",
    )
    return dict(
        role=role, T0_ms=first, T1_ms=last, accepted=True, complete=True, actual_exit_codes=[0, 0]
    )


def returned_predecessor(value, accepted_raw, release, plan_sha, root, role, now_ms, bind_packet):
    wire.need(
        isinstance(release, dict)
        and release.get("schema") == "topolab.staged-input-caller-release.v1"
        and release.get("execution_identity") == wire.IDENTITY
        and release.get("root") == root
        and release.get("role") == role
        and release.get("plan_sha256") == plan_sha
        and release.get("accepted_sha256") == wire.sha(accepted_raw),
        "actual returned binder release required",
    )
    first, last, exit_code = wire.validate_terminal(
        bind_packet,
        wire.control_argv(root, "bind", plan_sha, role),
        "/root/full60_independent" if role.startswith("independent-") else "/root",
        str(wire.RUNTIME_REPO),
    )
    wire.need(
        exit_code == 0
        and first == release["actual_bind_start_ms"]
        and last == release["actual_bind_end_ms"]
        and "".join(row["result"]["output"] for row in bind_packet["responses"]).encode()
        == wire.canonical(value["result"]),
        "actual binder response/stdout differs",
    )
    proof = predecessor(value, plan_sha, role)
    wire.need(
        release.get("native_start_ms") == proof["T0_ms"]
        and release.get("native_record_end_ms") == proof["T1_ms"]
        and all(
            type(release.get(key)) is int for key in ("actual_bind_start_ms", "actual_bind_end_ms")
        )
        and proof["T1_ms"]
        <= release["actual_bind_start_ms"]
        <= release["actual_bind_end_ms"]
        <= now_ms
        and release["actual_bind_end_ms"] - proof["T0_ms"] + 10000 <= wire.FULL[role] * 1000,
        "binder returned outside original Native FULL",
    )
    return proof


def stopped(root, *, graph=False):
    try:
        notice, _ = wire.read_json(wire.stop_path(root))
    except FileNotFoundError:
        notice = None
    if notice is not None:
        wire.need(
            notice.get("schema") == wire.STOP_SCHEMA
            and notice.get("execution_identity") == wire.IDENTITY
            and notice.get("root") == root,
            "caller STOP identity differs",
        )
        return True
    if not graph:
        return False
    try:
        wire.read_private(Path(root) / "STOP.json")
        return True
    except FileNotFoundError:
        return False


def initial_metadata(root, release):
    """Replay only E/B buffers before any custody ancestor may be opened."""
    plan_pin = release.get("plan_sha256")
    wire.need(
        isinstance(plan_pin, str)
        and len(plan_pin) == 64
        and all(c in "0123456789abcdef" for c in plan_pin),
        "initial plan SHA required",
    )
    packet = wire.paired_actual(release["activation_actual"])
    formal = root == wire.FORMAL
    argv = packet.get("argv", [])
    start = release.get("whole_start_ms")
    wire.need(
        type(start) is int
        and len(argv) == (12 if formal else 16)
        and argv[:6]
        == [
            wire.PYTHON,
            "-I",
            str(wire.RUNTIME_REPO / "scripts" / wire.CONTROL_ENTRY),
            "activate-formal" if formal else "prepare-rehearsal",
            "--root",
            root,
        ]
        and argv[6] == "--registration-certificate-sha"
        and argv[8] == "--registration-finalize-actual-sha"
        and argv[-2:] == ["--whole-start-ms", str(start)],
        "initial literal request differs",
    )
    pins = [argv[7], argv[9]]
    if not formal:
        wire.need(
            argv[10] == "--formal-registration-certificate-sha"
            and argv[12] == "--formal-registration-finalize-actual-sha",
            "initial formal proof flags differ",
        )
        pins += [argv[11], argv[13]]
    wire.need(
        all(
            isinstance(pin, str) and len(pin) == 64 and all(c in "0123456789abcdef" for c in pin)
            for pin in pins
        ),
        "initial proof SHA differs",
    )
    first, last, exit_code = wire.validate_terminal(
        packet, argv, "/root" if formal else "/root/full60_independent", str(wire.RUNTIME_REPO)
    )
    expected = dict(
        plan_sha256=release.get("plan_sha256"),
        scope="SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
        if formal
        else "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY",
        formal_authority=formal,
        source_stat_reads=0,
    )
    wire.need(
        exit_code == 0
        and first == release.get("actual_start_ms")
        and last == release.get("actual_end_ms")
        and start <= first <= last <= min(start + 30000, time.time_ns() // 10**6)
        and "".join(row["result"]["output"] for row in packet["responses"]).encode()
        == wire.canonical(expected),
        "initial original return unavailable before target access",
    )
    window.check(dict(whole_start_ms=start, whole_end_ms=start + 4500000), time.time_ns() // 10**6)
    return packet


def wait(root, role, seconds):
    wire.need(root in wire.ROOTS and role in ("plan", *wire.ROLES), "new root/receipt role differs")
    wire.need(type(seconds) is int and 1 <= seconds <= 160, "wait bound differs")
    end = time.monotonic() + seconds
    while True:
        if stopped(root):
            return dict(status="STOP", source_or_payload_reads=0)
        try:
            activation_path = wire.activation_path(root)
            activation, activation_raw = wire.read_json(activation_path)
            wire.need(
                activation_raw == wire.read_private(wire.BACKUP / activation_path.name)
                and activation.get("schema") == "topolab.staged-input-activation-release.v1"
                and activation.get("execution_identity") == wire.IDENTITY
                and activation.get("root") == root,
                "original initial pair required",
            )
            initial_metadata(root, activation)
            if stopped(root, graph=True):
                return dict(status="STOP", source_or_payload_reads=0)
            plan, raw = wire.read_json(Path(root) / "plan.json")
            projection = project(plan, raw, root, time.time_ns() // 10**6)
            wire.need(
                activation.get("plan_sha256") == projection["plan_sha256"]
                and activation.get("whole_start_ms") == plan["whole_start_ms"],
                "initial release plan differs",
            )
            first, last = wire.activation_return(
                plan, projection["plan_sha256"], wire.paired_actual(activation["activation_actual"])
            )
            wire.need(
                first == activation.get("actual_start_ms")
                and last == activation.get("actual_end_ms")
                and last <= time.time_ns() // 10**6,
                "actual initial return still unavailable",
            )
            proofs = []
            if role != "plan":
                for name in wire.ROLES[: wire.ROLES.index(role) + 1]:
                    release_path = wire.release_path(root, name)
                    release, release_raw = wire.read_json(release_path)
                    backup = wire.read_private(
                        wire.BACKUP / release_path.relative_to(wire.EVIDENCE)
                    )
                    wire.need(backup == release_raw, "caller release pair differs")
                    value, accepted_raw = wire.read_json(Path(root) / (name + "-accepted.json"))
                    proofs.append(
                        returned_predecessor(
                            value,
                            accepted_raw,
                            release,
                            projection["plan_sha256"],
                            root,
                            name,
                            time.time_ns() // 10**6,
                            wire.paired_actual(release["bind_actual"]),
                        )
                    )
            return dict(plan=projection, proofs=proofs, source_or_payload_reads=0)
        except FileNotFoundError:
            if (
                time.monotonic() >= end
                or time.time_ns() // 10**6 >= window.GLOBAL_END_MS - window.RESULT_SUFFIX_MS
            ):
                return dict(status="NOT_READY", source_or_payload_reads=0)
            time.sleep(min(0.05, max(0, end - time.monotonic())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=160)
    args = parser.parse_args()
    print(
        json.dumps(
            wait(args.root, args.role, args.timeout_seconds), sort_keys=True, separators=(",", ":")
        )
    )


if __name__ == "__main__":
    main()
