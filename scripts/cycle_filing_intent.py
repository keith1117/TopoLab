"""Bind each A3 privileged filing to one paired return of its frozen actor."""

import argparse
import json
import os
import re
from pathlib import Path

AUTHORS = {"independent": "/root/full60_independent", "producer": "/root"}
ROLE_ORDER = (
    "independent-public-check",
    "exporter-r0",
    "independent-r0",
    "exporter-r1",
    "independent-r1",
    "shared-closeout",
    "final-filing",
    "lease-release",
)
MODES = ("supervise", "record")
ENTRY_SCHEMA = "topolab.formal-file-actor-entry.v1"


def owner(role):
    if role not in ROLE_ORDER:
        raise ValueError("unknown formal role")
    return "independent" if role.startswith("independent-") else "producer"


def outputs(role, mode):
    if mode not in MODES:
        raise ValueError("unknown filing mode")
    return [f"{role}-{mode}-actual-event.json"] + (
        [f"{role}-events.json"] if mode == "record" else []
    )


def validate_file_intent(intent, expected, *, consumed, stopped):
    role, mode = expected["role"], expected["mode"]
    if (
        consumed
        or stopped
        or intent != expected
        or intent["schema"] != "topolab.formal-file-intent.v1"
        or intent["author"] != AUTHORS[owner(role)]
        or intent["outputs"] != outputs(role, mode)
    ):
        raise ValueError("unbound, spent or stopped formal filing intent")
    return intent


def prefix(actor):
    return f"cycle-20261123-{actor}-a3"


def pair(wire, name, digest=None):
    primary = wire.EVIDENCE / name
    value, raw = wire.read_json(primary, digest)
    backup = wire.BACKUP / name
    wire.need(
        raw == wire.read_private(backup) and not primary.samefile(backup),
        "filing evidence pair differs",
    )
    return value, wire.sha(raw)


def exclusive_pair(wire, name, value):
    wire.need(not either(wire, name), f"partial or duplicate {name}")
    raw = wire.canonical(value)
    # The exclusive primary is the winner. A concurrent loser never touches the peer.
    for directory in (wire.EVIDENCE, wire.BACKUP):
        wire.write_private(directory / name, raw)
    return pair(wire, name)[1]


def present(wire, path):
    parent = wire.parent_fd(path)
    try:
        try:
            os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        return True
    finally:
        os.close(parent)


def either(wire, name):
    return any(present(wire, directory / name) for directory in (wire.EVIDENCE, wire.BACKUP))


def entry_value(wire, builder, actor):
    ready, ready_sha = pair(wire, "input-activation-readiness-a1.json")
    _, preflight_sha = pair(wire, "input-preflight-actual-a1.json")
    wire.need(
        ready["execution_identity"] == wire.IDENTITY
        and ready["new_input_budget"]["sha256"] == wire.BUDGET_SHA,
        "wrong actor admission",
    )
    artifact, artifact_sha = pair(wire, prefix(actor) + "-program.json")
    config = artifact["config"]
    contract = json.loads(
        (wire.RUNTIME_REPO / "docs/planning/input_cycle_a3_contract.json").read_bytes()
    )
    reg = contract["registration"]["formal"]
    wire.need(
        config["formal"] is True
        and config["author"] == actor
        and config["event_prefix"] == prefix(actor)
        and config["registration_certificate_sha"] == reg["certificate_sha256"]
        and config["registration_finalize_actual_sha"] == reg["finalize_actual_sha256"],
        "unregistered actor or registration pins",
    )
    source = (wire.RUNTIME_REPO / "scripts/staged_input_actor.mjs").read_bytes()
    frozen = ready["published_source_sha256"]["scripts/staged_input_actor.mjs"]
    wire.need(
        artifact == builder.build(config, source, frozen, wire=wire), "frozen program differs"
    )
    return dict(
        schema=ENTRY_SCHEMA,
        execution_identity=wire.IDENTITY,
        root=wire.FORMAL,
        author=AUTHORS[actor],
        owner_budget_sha256=wire.BUDGET_SHA,
        artifact_sha256=artifact_sha,
        program_sha256=artifact["program_sha256"],
        actor_sha256=frozen,
        readiness_sha256=ready_sha,
        preflight_sha256=preflight_sha,
    )


def entry_name(actor):
    return prefix(actor) + "-filing-entry.json"


def derive(wire, builder, root, plan_sha, role, mode, path, packet_sha):
    actor = owner(role)
    stem = prefix(actor) + "-" + actor
    wire.need(
        root == wire.FORMAL and path == str(wire.EVIDENCE / f"{stem}-{role}-{mode}-actual.json"),
        "unexpected original filing path",
    )
    packet, _ = pair(wire, Path(path).name, packet_sha)
    plan, _ = wire.checked_plan(root, plan_sha)
    entry, entry_sha = pair(wire, entry_name(actor))
    wire.need(
        entry == entry_value(wire, builder, actor)
        and plan["activation_readiness"]["sha256"] == entry["readiness_sha256"]
        and plan["independent_preflight"]["sha256"] == entry["preflight_sha256"]
        and plan["source_tree"]["scripts/staged_input_actor.mjs"] == entry["actor_sha256"],
        "formal plan and entry disagree",
    )
    activation, _ = pair(wire, wire.activation_path(root).name)
    wire.need(
        activation["plan_sha256"] == plan_sha and activation["root"] == root, "unreleased plan"
    )
    previous = ROLE_ORDER.index(role)
    if previous and previous <= len(wire.ROLES):
        released, _ = pair(wire, wire.release_path(root, ROLE_ORDER[previous - 1]).name)
        wire.need(
            released["plan_sha256"] == plan_sha and released["role"] == ROLE_ORDER[previous - 1],
            "unreleased predecessor",
        )
    first, last, code = wire.validate_terminal(
        packet,
        wire.control_argv(root, mode, plan_sha, role),
        AUTHORS[actor],
        str(wire.RUNTIME_REPO),
    )
    wire.need(
        code == 0
        and plan["whole_start_ms"] <= first <= last <= plan["whole_end_ms"]
        and packet["request"].get("sandbox_permissions") == "require_escalated"
        and re.fullmatch(re.escape(stem) + "-[0-9]+", packet["event_id"]),
        "ineligible original native return",
    )
    if role == "lease-release":
        bound, _ = pair(wire, f"{stem}-final-filing-bind-actual.json")
        _, ended, code = wire.validate_terminal(
            bound,
            wire.control_argv(root, "bind", plan_sha, "final-filing"),
            AUTHORS[actor],
            str(wire.RUNTIME_REPO),
        )
        wire.need(
            code == 0 and plan["whole_start_ms"] <= ended <= first,
            "final filing did not return before lease release",
        )
    if mode == "record":
        sup, sup_sha = pair(wire, ticket(role, "supervise", "intent"))
        spent, _ = pair(wire, ticket(role, "supervise", "spent"))
        event, _ = wire.read_json(Path(root) / outputs(role, "supervise")[0])
        wire.need(
            spent["intent_sha256"] == sup_sha
            and spent["event_id"] == sup["event_id"]
            and (sup["program_sha256"], sup["plan_sha256"]) == (entry["program_sha256"], plan_sha)
            and (event["event_id"], event["raw_packet_sha256"])
            == (sup["event_id"], sup["packet_sha256"])
            and event["exit_code"] == 0
            and sup["last_ms"] <= first,
            "SUP filing has not completed",
        )
    return dict(
        schema="topolab.formal-file-intent.v1",
        execution_identity=wire.IDENTITY,
        root=root,
        plan_sha256=plan_sha,
        role=role,
        mode=mode,
        author=AUTHORS[actor],
        program_sha256=entry["program_sha256"],
        actor_sha256=entry["actor_sha256"],
        entry_sha256=entry_sha,
        packet_path=path,
        packet_sha256=packet_sha,
        event_id=packet["event_id"],
        outputs=outputs(role, mode),
        first_ms=first,
        last_ms=last,
    )


def ticket(role, mode, status):
    return f"filing-{role}-{mode}-{status}.json"


def guard(wire, intent, expected):
    role, mode = expected["role"], expected["mode"]
    validate_file_intent(
        intent,
        expected,
        consumed=either(wire, ticket(role, mode, "spent")),
        stopped=either(wire, wire.stop_path(wire.FORMAL).name),
    )
    wire.need(
        all(not present(wire, Path(wire.FORMAL) / name) for name in intent["outputs"]),
        "formal event output already exists",
    )


def persist_return(wire, builder, packet, destination):
    name = Path(destination).name
    actor = next((key for key, author in AUTHORS.items() if packet.get("author") == author), None)
    wire.need(actor is not None, "unknown submitter")
    stem = prefix(actor) + "-" + actor + "-"
    names = {stem + "caller-STOP.json"}
    for role in ROLE_ORDER:
        if owner(role) == actor:
            names.update(stem + role + "-" + kind + "-actual.json" for kind in (*MODES, "bind"))
    if actor == "producer":
        names.update(
            (
                stem + "activation-actual.json",
                stem + "certificate-actual.json",
                "input-preparation-retention-actual-a1.json",
                "input-readiness-original-return-a1.json",
            )
        )
    else:
        names.add("input-preflight-actual-a1.json")
    wire.need(Path(destination).parent == wire.EVIDENCE and name in names, "reserved filing path")
    saved = wire.persist(packet, destination)
    argv = packet.get("argv", [])
    if (
        saved["status"] != "PAIRED_PERSISTED"
        or packet.get("schema") != wire.ACTUAL_SCHEMA
        or len(argv) != 10
        or argv[3] not in MODES
    ):
        return saved
    # Failed/live original responses stay paired and cannot obtain a ticket.
    if packet["responses"][-1].get("result", {}).get("exit_code") != 0:
        return saved
    mode, root, plan_sha, role = argv[3::2]
    intent = derive(wire, builder, root, plan_sha, role, mode, destination, saved["sha256"])
    guard(wire, intent, intent)
    sha = exclusive_pair(wire, ticket(role, mode, "intent"), intent)
    return dict(saved, file_intent_sha256=sha, program_sha256=intent["program_sha256"])


def consume(wire, builder, args):
    expected = derive(
        wire,
        builder,
        args.root,
        args.plan_sha,
        args.role,
        args.event_mode,
        args.packet,
        args.packet_sha,
    )
    intent, sha = pair(wire, ticket(args.role, args.event_mode, "intent"), args.intent_sha)
    wire.need(args.program_sha == expected["program_sha256"], "different frozen program")
    guard(wire, intent, expected)
    exclusive_pair(
        wire,
        ticket(args.role, args.event_mode, "spent"),
        dict(
            schema="topolab.formal-file-intent-spent.v1",
            intent_sha256=sha,
            event_id=intent["event_id"],
            outputs=intent["outputs"],
        ),
    )
    return wire.file_event(
        args.root, args.plan_sha, args.role, args.event_mode, args.packet, args.packet_sha
    )


def dispatch(wire, sibling, argv):
    os.umask(0o077)
    # All modes are selected literally. There is no fallback for an unsigned file request.
    mode = argv[0] if argv else None
    if mode in ("enter-independent", "dispatch-note"):
        wire.need(argv == [mode, "--root", wire.FORMAL], "wrong actor entry path")
        actor = "independent" if mode == "enter-independent" else "producer"
        wire.need(not either(wire, wire.stop_path(wire.FORMAL).name), "closed graph")
        entry = entry_value(wire, sibling("build_staged_input_caller"), actor)
        exclusive_pair(wire, entry_name(actor), entry)
        if actor == "producer":
            return sibling("cycle_input_filer").dispatch(wire, argv)
        result = dict(status="INDEPENDENT_ACTOR_ENTERED", program_sha256=entry["program_sha256"])
    elif mode == "persist":
        wire.need(
            len(argv) == 5 and argv[1::2] == ["--packet-json", "--destination"],
            "wrong persist request",
        )
        result = persist_return(
            wire, sibling("build_staged_input_caller"), json.loads(argv[2]), argv[4]
        )
    elif mode == "file":
        parser = argparse.ArgumentParser(allow_abbrev=False)
        for key in (
            "root",
            "plan-sha",
            "role",
            "event-mode",
            "packet",
            "packet-sha",
            "intent-sha",
            "program-sha",
        ):
            parser.add_argument("--" + key, required=True)
        result = consume(wire, sibling("build_staged_input_caller"), parser.parse_args(argv[1:]))
    else:
        wire.need(
            mode in ("reserve", "activate-release", "accept-role", "retain-failure"),
            "unknown filing entry",
        )
        return wire.main()
    print(wire.canonical(result).decode(), end="")
