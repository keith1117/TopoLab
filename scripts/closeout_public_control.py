"""Exercise the registered public closeout in a new, synthetic native graph."""

import argparse
import hashlib
import io
import json
import os
import re
import sys
import tarfile
import time
from pathlib import Path
from types import ModuleType

ENTRY = Path(__file__).resolve()
CHECKOUT = ENTRY.parents[1]
ENTRY_DIGEST = globals().get("ENTRY_DIGEST")
EVIDENCE = Path("/Users/keith1117/Documents/TopoLab-data/closeout-20261125")
BUDGET = "9afb732330236b115a42621441c5b5e7d019c05ce02d1154cd14902dde64b577"
AUTHOR = "/root/closeout_public"
SHARED = "shared-closeout"
PYTHON = (
    "/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python"
)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError("PUBLIC_CLOSEOUT: " + message)


def paired(folder, name):
    a = folder / name
    b = folder.with_name(folder.name + "-backup") / name
    raw = a.read_bytes()
    need(
        not a.is_symlink() and not b.is_symlink() and not a.samefile(b) and b.read_bytes() == raw,
        "paired control differs: " + name,
    )
    return raw


def claim_for(root):
    match = re.fullmatch(
        r"/private/tmp/topolab-public-closeout-20261125-a([1-9]|1[0-6])", str(root)
    )
    need(match and root.resolve() == root, "literal fixture root required")
    budget = paired(EVIDENCE, "owner-budget.json")
    raw = paired(EVIDENCE, "public-" + match[1] + "-entry.json")
    claim = json.loads(raw)
    need(
        digest(budget) == claim["budget_sha256"] == BUDGET
        and claim["root"] == str(root)
        and claim["slot"] == int(match[1])
        and claim["mode"] in ("late", "released")
        and claim["start_ms"]
        <= time.time_ns() // 10**6
        <= claim["end_ms"]
        <= json.loads(budget)["diagnostic_end_ms"]
        and claim["end_ms"] - claim["start_ms"] == 780_000
        and claim["charge_FULL"] == 600
        and claim["pricing_sha256"] == digest(paired(EVIDENCE, "public-pricing.json"))
        and claim["fee_reservation_FULL"] == (600 if claim["mode"] == "late" else 3600),
        "budget, clock or scope differs",
    )
    need(
        sys.flags.isolated and sys.executable == PYTHON and Path.cwd() == CHECKOUT, "fixed runtime"
    )
    need(
        ENTRY_DIGEST == claim["software_sha256"]["scripts/closeout_public_control.py"],
        "compiled public entry differs",
    )
    for name, expected in claim["software_sha256"].items():
        need(
            isinstance(name, str)
            and Path(name).parent in (Path("scripts"), Path("docs/planning"))
            and Path(name).name not in ("", ".", ".."),
            "unregistered software path",
        )
        need(
            digest((CHECKOUT / name).read_bytes()) == expected,
            "fixture candidate source changed: " + name,
        )
    return claim


def source_loader(path, expected):
    raw = path.read_bytes()
    actual = digest(raw)
    need(actual == expected, "compiled public loader differs")
    loader = ModuleType("full60_input_loader")
    loader.__file__ = str(path)
    sys.modules[loader.__name__] = loader
    exec(compile(raw, str(path), "exec"), loader.__dict__)
    loader.loaded_source_sha256[str(path.resolve())] = actual
    return loader


def configure(root, claim):
    scripts = CHECKOUT / "scripts"
    loader = source_loader(
        scripts / "full60_input_loader.py",
        claim["software_sha256"]["scripts/full60_input_loader.py"],
    )
    loader.loaded_source_sha256[str(ENTRY)] = ENTRY_DIGEST
    loader.install(require_locked_environment=True)
    sys.path.insert(0, str(scripts))
    native = loader.load("closeout_fixture_native", scripts / "p17_m2_content_verified_control.py")
    wire = loader.load("staged_input_filer", scripts / "staged_input_filer.py")
    intents = loader.load("cycle_filing_intent", scripts / "cycle_filing_intent.py")
    wire.EVIDENCE = root.with_name(root.name + "-evidence")
    wire.BACKUP = wire.EVIDENCE.with_name(wire.EVIDENCE.name + "-backup")
    wire.PUBLIC = str(root)
    wire.ROOTS = (str(root),)
    wire.graph_root = str(root)
    import p17_m2_input_continuation as profiles

    released = profiles.profile("control", profiles.CLOSEOUT_FORMAL)
    need(
        claim["software_sha256"] == released.source_freeze(profiles.CLOSEOUT_FORMAL),
        "full production software freeze differs",
    )
    need(
        claim["scheduler_sha256"] == claim["software_sha256"]["scripts/staged_input_actor.mjs"]
        and re.fullmatch(r"[a-f0-9]{40}", claim["checkout_head"]),
        "released scheduler or revision differs",
    )
    original = native.source_freeze
    native.source_freeze = lambda: {
        **original(),
        **claim["software_sha256"],
        "fixture/scheduler": claim["scheduler_sha256"],
    }
    native.argv_for = lambda root, mode, plan_sha, role: [
        PYTHON,
        "-I",
        str(ENTRY),
        mode,
        "--root",
        str(root),
        "--plan-sha",
        plan_sha,
        "--role",
        role,
    ]
    return native, wire, intents


def compact(native, mode, role, plan_sha, value):
    from r0_caller_receipt import project

    return project(mode, role, plan_sha, value, native.canonical(value))


def event_value(native, wire, root, plan_sha, role, mode, packet, raw):
    argv = native.argv_for(root, mode, plan_sha, role)
    first, last, code = wire.validate_terminal(packet, argv, AUTHOR, str(Path.cwd()))
    need(code == 0 and packet["event_id"] == role + "-" + mode, "unexpected terminal or id")
    pending = native.read_json(root / "receipts" / (role + "-pending.json"))
    need(
        pending["plan_sha256"] == plan_sha and pending["external_argv"][mode == "record"] == argv,
        "native pending and actual return disagree",
    )
    event = dict(
        event_id=packet["event_id"],
        author=AUTHOR,
        argv=argv,
        exit_code=0,
        complete=True,
        start_seconds=first / 1000,
        end_seconds=last / 1000,
        wall_seconds=(last - first) / 1000,
        clock_domain="functions.exec.Date.now.UTC-seconds",
        raw_packet_sha256=digest(raw),
        observed_pending_sha256=digest(native.canonical(pending)),
    )
    expected = {"status": "PENDING_EXTERNAL_EXIT", "controller_exit": 0}
    if mode == "record":
        record = native.read_json(root / "receipts" / (role + "-wire.json"))
        expected = compact(native, mode, role, plan_sha, record)
        event["observed_completion_sha256"] = digest(native.canonical(record["completion"]))
    stdout = "".join(row["result"]["output"] for row in packet["responses"])
    need(json.loads(stdout) == expected, "returned native output differs")
    return event


def intent_value(native, wire, intents, root, plan_sha, role, mode, packet, raw):
    return dict(
        schema="topolab.public-closeout.filing-intent.v1",
        program_sha256=digest((CHECKOUT / "scripts/closeout_public_schedule.mjs").read_bytes()),
        role=role,
        mode=mode,
        author=AUTHOR,
        root=str(root),
        plan_sha256=plan_sha,
        outputs=intents.outputs(role, mode),
        event=event_value(native, wire, root, plan_sha, role, mode, packet, raw),
    )


def save_packet(native, wire, intents, root, plan_sha, role, mode, packet, timing=None):
    import contextlib

    destination = wire.EVIDENCE / f"{role}-{mode}-actual.json"
    raw = wire.canonical(packet)
    value = intent_value(native, wire, intents, root, plan_sha, role, mode, packet, raw)
    context = contextlib.nullcontext()
    if timing is not None:
        import closeout_receipt

        context = closeout_receipt.track_writes(
            wire, destination, wire.BACKUP / destination.name, timing
        )
    with context:
        saved = wire.publish_pair(destination, raw)
    need(
        saved["status"] == "PAIRED_PERSISTED" and paired(wire.EVIDENCE, destination.name) == raw,
        "original publication differs",
    )
    intent = intents.exclusive_pair(wire, intents.ticket(role, mode, "intent"), value)
    return dict(saved, file_intent_sha256=intent, program_sha256=value["program_sha256"])


def file_event(
    native, wire, intents, root, plan_sha, role, mode, receipt_sha, intent_sha, driver_sha
):
    packet, raw = wire.read_json(wire.EVIDENCE / f"{role}-{mode}-actual.json")
    need(raw == paired(wire.EVIDENCE, f"{role}-{mode}-actual.json"), "changed original pair")
    expected = intent_value(native, wire, intents, root, plan_sha, role, mode, packet, raw)
    registered, sha = intents.pair(wire, intents.ticket(role, mode, "intent"))
    need(
        digest(raw) == receipt_sha
        and sha == intent_sha
        and expected["program_sha256"] == driver_sha
        and registered == expected
        and not any((root / n).exists() for n in registered["outputs"])
        and not (root / "STOP.json").exists(),
        "changed or consumed intent",
    )
    event = registered["event"]
    if mode == "record":
        previous = native.read_json(root / f"{role}-supervise-actual-event.json")
        need(
            previous["end_seconds"] <= event["start_seconds"]
            and previous["observed_pending_sha256"] == event["observed_pending_sha256"],
            "missing or overlapping supervisor event",
        )
    intents.exclusive_pair(
        wire,
        intents.ticket(role, mode, "spent"),
        dict(intent_sha256=sha, event_id=event["event_id"], outputs=registered["outputs"]),
    )
    native.put(root / f"{role}-{mode}-actual-event.json", event)
    if mode == "record":
        native.put(root / f"{role}-events.json", [previous, event])
    return dict(status="ACTUAL_EVENT_FILED", role=role, mode=mode, intent_sha256=sha)


def replay_controls(root, claim, wire):
    """Open only the paired immutable positive fixture from this campaign."""
    ref = claim["positive_origin"]
    slot = ref["slot"]
    need(type(slot) is int and 1 <= slot < claim["slot"] <= 16, "replay origin slot")
    raw_report = paired(EVIDENCE, f"public-{slot}-result.json")
    positive = json.loads(raw_report)
    origin = f"/private/tmp/topolab-public-closeout-20261125-a{slot}"
    index_raw = paired(EVIDENCE, f"public-{slot}-index.json")
    archive = paired(EVIDENCE, f"public-{slot}-evidence.tar.gz")
    index = json.loads(index_raw)
    need(
        positive["status"] == "PASS_PUBLIC_NATIVE_CLOSEOUT"
        and positive["mode"] == "released"
        and positive["root"] == origin
        and positive["rec_pair_equal"] is True
        and ref["rec_sha256"] == positive["rec_pair_sha256"]
        and ref["report_sha256"] == digest(raw_report)
        and digest(index_raw) == ref["index_sha256"] == positive["index_sha256"]
        and digest(archive) == ref["archive_sha256"] == positive["archive_sha256"]
        and positive["plan_sha256"] == ref["plan_sha256"]
        and root != Path(origin),
        "unbound positive source",
    )
    results = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as t:
        for kind in ("supervise", "record"):
            name = f"shared-closeout-{kind}-actual.json"
            primary, backup = [f"custody/{copy}/{name}" for copy in ("primary", "backup")]
            original = f"caller/{name}"
            copies = []
            for path in (primary, backup, original):
                member = t.getmember(path)
                need(member.isfile() and 0 < member.size <= 128 * 1024, "bounded public record")
                raw = t.extractfile(member).read()
                need(
                    index[path] == dict(bytes=len(raw), sha256=digest(raw)),
                    "original index differs",
                )
                copies.append(raw)
            need(copies[0] == copies[1] == copies[2], "positive return copies differ")
            packet = json.loads(copies[0])
            argv = [
                PYTHON,
                "-I",
                str(ENTRY),
                kind,
                "--root",
                origin,
                "--plan-sha",
                ref["plan_sha256"],
                "--role",
                SHARED,
            ]
            _, _, code = wire.validate_terminal(packet, argv, AUTHOR, str(CHECKOUT))
            need(code == 0 and wire.canonical(packet) == copies[0], "public native return differs")
            if kind == "record":
                need(digest(copies[0]) == ref["rec_sha256"], "positive recorder SHA differs")
            results[kind] = packet
    return results


def replay(a, claim, wire, intents):
    import closeout_receipt

    need(claim["mode"] == "late", "late replay grant required")
    root = a.root
    returns = replay_controls(root, claim, wire)
    origin = claim["positive_origin"]
    if a.mode == "prepare-replay":
        root.mkdir(mode=0o700)
        for d in (wire.EVIDENCE, wire.BACKUP):
            d.mkdir(mode=0o700)
        result = dict(
            scope="PUBLIC_CLOSEOUT_RECEIPT_REPLAY_ONLY",
            formal_authority=False,
            origin=origin,
            native_roles_dispatched=0,
            original_returns=returns,
        )
        print(wire.canonical(result).decode(), end="")
        return 0
    need(
        a.mode == "persist-closeout-record"
        and a.role == SHARED
        and a.event_mode == "record"
        and a.plan_sha == origin["plan_sha256"]
        and a.packet_json is None
        and root.is_dir()
        and not root.is_symlink()
        and a.deadline_ms <= claim["end_ms"],
        "disallowed replay command",
    )

    def save(packet, timing):
        raw = wire.canonical(packet)
        name = "shared-closeout-record-actual.json"
        need(
            raw == wire.canonical(returns["record"]) and digest(raw) == origin["rec_sha256"],
            "replay must retain the exact original public data",
        )
        with closeout_receipt.track_writes(wire, wire.EVIDENCE / name, wire.BACKUP / name, timing):
            saved = wire.publish_pair(wire.EVIDENCE / name, raw)
        need(
            saved["status"] == "PAIRED_PERSISTED" and paired(wire.EVIDENCE, name) == raw,
            "replay dual custody differs",
        )
        driver = claim["software_sha256"]["scripts/closeout_public_schedule.mjs"]
        ticket = dict(
            schema="topolab.public-closeout.replay-intent.v1",
            formal_authority=False,
            fixture_root=str(root),
            origin=origin,
            program_sha256=driver,
            packet_sha256=digest(raw),
            event_id=packet["event_id"],
            author=AUTHOR,
        )
        pin = intents.exclusive_pair(wire, intents.ticket(SHARED, "record", "intent"), ticket)
        return dict(saved, file_intent_sha256=pin, program_sha256=driver)

    return closeout_receipt.serve(save, a.deadline_ms)


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument(
        "mode",
        choices=(
            "prepare-public",
            "prepare-replay",
            "supervise",
            "run",
            "payload",
            "record",
            "bind",
            "persist-public",
            "persist-closeout-record",
            "file-public",
        ),
    )
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--plan-sha")
    parser.add_argument("--role")
    parser.add_argument("--event-mode", choices=("supervise", "record"))
    parser.add_argument("--packet-json")
    parser.add_argument("--deadline-ms", type=int)
    parser.add_argument("--packet-sha")
    parser.add_argument("--intent-sha")
    parser.add_argument("--program-sha")
    a = parser.parse_args()
    os.umask(0o077)
    claim = claim_for(a.root)
    native, wire, intents = configure(a.root, claim)
    if claim["mode"] == "late":
        return replay(a, claim, wire, intents)
    need(claim["mode"] == "released", "full graph requires a released positive slot")
    if a.mode == "prepare-public":
        for d in (wire.EVIDENCE, wire.BACKUP):
            d.mkdir(mode=0o700)
        return native.main()
    need(a.role in native.CAPS, "unregistered public role")
    root, _ = native.checked(a.root, a.plan_sha)
    if a.mode == "persist-closeout-record":
        need(
            a.role == SHARED
            and a.event_mode == "record"
            and a.packet_json is None
            and a.deadline_ms <= claim["end_ms"],
            "stdin scope",
        )
        import closeout_receipt

        return closeout_receipt.serve(
            lambda packet, timing: save_packet(
                native, wire, intents, root, a.plan_sha, a.role, a.event_mode, packet, timing
            ),
            a.deadline_ms,
        )
    if a.mode == "persist-public":
        result = save_packet(
            native, wire, intents, root, a.plan_sha, a.role, a.event_mode, json.loads(a.packet_json)
        )
    elif a.mode == "file-public":
        result = file_event(
            native,
            wire,
            intents,
            root,
            a.plan_sha,
            a.role,
            a.event_mode,
            a.packet_sha,
            a.intent_sha,
            a.program_sha,
        )
    elif a.mode in ("record", "bind"):
        need(
            sys.orig_argv == native.argv_for(root, a.mode, a.plan_sha, a.role),
            "native argv differs",
        )
        if a.mode == "record":
            value = native.collect(root, a.plan_sha, a.role)
        else:
            value = native.bind(root, native.read_json(root / "plan.json"), a.plan_sha, a.role)
        result = compact(native, a.mode, a.role, a.plan_sha, value)
        print(native.canonical(result).decode(), end="")
        return int(
            value.get("status") == "STOP_NO_RETRY"
            or value.get("completion", {}).get("status") == "FAILED_INTERNAL_COMPLETION"
        )
    else:
        return native.main()
    print(wire.canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raw = ENTRY.read_bytes()
    entry_scope = {
        "__name__": "closeout_public_entry",
        "__file__": str(ENTRY),
        "ENTRY_DIGEST": digest(raw),
    }
    exec(compile(raw, str(ENTRY), "exec"), entry_scope)
    raise SystemExit(entry_scope["main"]())
