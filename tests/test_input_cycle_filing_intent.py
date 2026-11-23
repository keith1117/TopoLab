"""A3's original actor entry and two native event filings in disposable custody."""

import json
import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def graph(tmp_path):
    route = runpy.run_path(str(REPO / "scripts/cycle_filing_input_route.py"))
    load = route["sibling"]
    wire = route["filer"]()
    gate = load("cycle_filing_intent")
    builder = load("build_staged_input_caller")
    root = tmp_path.resolve() / "control"
    wire.RUNTIME_REPO = REPO
    wire.EVIDENCE = root.parent / "primary"
    wire.BACKUP = root.parent / "backup"
    wire.ROOTS = (str(root),)
    wire.FORMAL = str(root)
    for directory in (root, root / "receipts", wire.EVIDENCE, wire.BACKUP):
        directory.mkdir(mode=0o700)
    actor = "independent"
    role = "independent-public-check"
    contract = json.loads((REPO / "docs/planning/input_cycle_a3_contract.json").read_bytes())
    reg = contract["registration"]["formal"]
    source = (REPO / "scripts/staged_input_actor.mjs").read_bytes()
    frozen = wire.sha(source)
    config = dict(
        formal=True,
        author=actor,
        execution_identity=wire.IDENTITY,
        root=str(root),
        repo=str(REPO),
        evidence_root=str(wire.EVIDENCE),
        owner_budget_sha256=wire.BUDGET_SHA,
        event_prefix=gate.prefix(actor),
        registration_certificate_sha=reg["certificate_sha256"],
        registration_finalize_actual_sha=reg["finalize_actual_sha256"],
        formal_registration_certificate_sha=reg["certificate_sha256"],
        formal_registration_finalize_actual_sha=reg["finalize_actual_sha256"],
    )
    raw_program = builder.build(config, source, frozen, wire=wire)
    gate.exclusive_pair(wire, gate.prefix(actor) + "-program.json", raw_program)
    tree = {
        str(Path(path).relative_to(REPO)): digest for path, digest in wire.SOURCE_DIGESTS.items()
    }
    tree["scripts/staged_input_actor.mjs"] = frozen
    ready = dict(
        execution_identity=wire.IDENTITY,
        new_input_budget=dict(sha256=wire.BUDGET_SHA),
        published_source_sha256=tree,
    )
    ready_sha = gate.exclusive_pair(wire, "input-activation-readiness-a1.json", ready)
    pre_sha = gate.exclusive_pair(wire, "input-preflight-actual-a1.json", {"fixture": True})
    gate.dispatch(wire, load, ["enter-independent", "--root", str(root)])
    clocks = dict(
        actor_window_seconds=4500,
        actor_deadlines_UTC={},
        whole_start_ms=10000,
        whole_end_ms=4510000,
    )
    plan = dict(
        execution_identity=wire.IDENTITY,
        root=str(root),
        formal_authority=True,
        activation_readiness=dict(sha256=ready_sha),
        independent_preflight=dict(sha256=pre_sha),
        source_tree=tree,
        **clocks,
    )
    pin = wire.write_private(root / "plan.json", wire.canonical(plan))["sha256"]
    gate.exclusive_pair(wire, wire.activation_path().name, dict(root=str(root), plan_sha256=pin))
    commands = [wire.control_argv(str(root), mode, pin, role) for mode in gate.MODES]
    pending = dict(
        execution_identity=wire.IDENTITY,
        role=role,
        plan_sha256=pin,
        status="PENDING_BEFORE_DISPATCH",
        frozen_FULL_seconds=300,
        external_argv=commands,
        actor_activation_UTC_seconds=10,
        clock_domain="functions.exec.Date.now.UTC-seconds",
        clock_resolution_seconds=0.001,
        **clocks,
    )

    def put(path, data):
        return wire.write_private(path, wire.canonical(data))

    put(root / "receipts" / (role + "-pending.json"), pending)
    completion = {"completion": {"fixture": True}}
    put(root / "receipts" / (role + "-wire.json"), completion)
    native = SimpleNamespace(CAPS={role: 300}, put=put)
    wire.input_profile = lambda: SimpleNamespace(
        base=lambda: native,
        checked=lambda *_: (None, plan),
        argv_for=lambda folder, mode, sha, who: wire.control_argv(str(folder), mode, sha, who),
    )

    def request(mode):
        argv = commands[gate.MODES.index(mode)]
        launch = dict(
            cmd=wire.literal_command(argv),
            workdir=str(REPO),
            sandbox_permissions="require_escalated",
        )
        stdout = wire.return_bytes(
            "record", role, pin, completion, wire.canonical(completion)
        ).decode()
        stem = gate.prefix(actor) + "-" + actor
        path = str(wire.EVIDENCE / f"{stem}-{role}-{mode}-actual.json")
        start = 10100 if mode == "supervise" else 10300
        packet = dict(
            schema=wire.ACTUAL_SCHEMA,
            author=gate.AUTHORS[actor],
            argv=argv,
            request=launch,
            event_id=f"{stem}-{gate.MODES.index(mode)}",
            responses=[
                dict(
                    tool="exec_command",
                    arguments=launch,
                    requested_ms=start,
                    returned_ms=start + 100,
                    result=dict(exit_code=0, output=stdout if mode == "record" else ""),
                )
            ],
        )
        saved = gate.persist_return(wire, builder, packet, path)
        return SimpleNamespace(
            root=str(root),
            role=role,
            event_mode=mode,
            plan_sha=pin,
            packet=path,
            packet_sha=saved["sha256"],
            intent_sha=saved["file_intent_sha256"],
            program_sha=saved["program_sha256"],
        )

    return gate, wire, builder, load, root, role, request


def test_exclusive_enter_and_paired_real_file_operation(graph):
    gate, wire, builder, load, root, role, request = graph
    with pytest.raises(ValueError, match="duplicate"):
        gate.dispatch(wire, load, ["enter-independent", "--root", str(root)])
    for mode in gate.MODES:
        args = request(mode)
        assert gate.consume(wire, builder, args)["status"] == "ACTUAL_EVENT_FILED"
        spent, _ = gate.pair(wire, gate.ticket(role, mode, "spent"))
        assert spent["intent_sha256"] == args.intent_sha
        assert all((root / path).exists() for path in spent["outputs"])
        with pytest.raises(ValueError, match="spent"):
            gate.consume(wire, builder, args)
    stored, _ = wire.read_json(root / (role + "-events.json"))
    assert [r["raw_packet_sha256"] for r in stored] == [
        gate.pair(wire, gate.ticket(role, mode, "intent"))[0]["packet_sha256"]
        for mode in gate.MODES
    ]


@pytest.mark.parametrize(
    "change",
    [
        "program_sha",
        "packet_sha",
        "plan_sha",
        "role",
        "intent_sha",
        "peer_packet",
        "peer_entry",
        "STOP",
        "existing",
    ],
)
def test_no_native_event_on_different_or_occupied_filing(graph, change):
    gate, wire, builder, _, root, role, request = graph
    args = request("supervise")
    output = root / (role + "-supervise-actual-event.json")
    if change in ("program_sha", "packet_sha", "plan_sha", "intent_sha", "role"):
        setattr(args, change, "exporter-r0" if change == "role" else "0" * 64)
    elif change == "STOP":
        wire.write_private(wire.BACKUP / wire.stop_path(str(root)).name, b"declared fixture STOP")
    elif change == "existing":
        output.write_bytes(b"previous event")
    else:
        filename = (
            Path(args.packet).name if change == "peer_packet" else gate.entry_name("independent")
        )
        (wire.BACKUP / filename).write_bytes(b"fixture peer drift")
    with pytest.raises(ValueError):
        gate.consume(wire, builder, args)
    assert not gate.either(wire, gate.ticket(role, "supervise", "spent"))
    assert output.read_bytes() == b"previous event" if change == "existing" else not output.exists()


def test_unfiled_supervisor_cannot_admit_recorder(graph):
    gate, wire, _, _, root, role, request = graph
    request("supervise")
    with pytest.raises(FileNotFoundError):
        request("record")
    assert not gate.either(wire, gate.ticket(role, "record", "intent"))
    assert not (root / (role + "-events.json")).exists()
