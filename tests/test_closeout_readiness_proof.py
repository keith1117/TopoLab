"""Synthetic original transport rows; no source, custody target or Native call."""

import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture
def proof(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "closeout_proof_test", SCRIPTS / "closeout_readiness_proof.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "REPO", SCRIPTS.parent)
    monkeypatch.setattr(module, "PYTHON", sys.executable)
    return module


def courier(proof):
    original = dict(
        schema=proof.ACTUAL_SCHEMA,
        author="/root",
        event_id="shared-record",
        argv=["python", "record"],
        request={},
        responses=[dict(wire="untouched")],
    )
    raw = proof.canonical(original)
    paths = ["/private/tmp/test-primary/record.json", "/private/tmp/test-backup/record.json"]
    timing = {
        name: dict(utc_us=1001000 + n * 1000, monotonic_us=5000000 + n * 1000)
        for n, name in enumerate(proof.TIMING_KEYS)
    }
    saved = dict(
        status="PAIRED_PERSISTED",
        bytes=len(raw),
        sha256=proof.sha(raw),
        path=paths[0],
        copies=[dict(path=p, bytes=len(raw), sha256=proof.sha(raw)) for p in paths],
        failures=[],
        program_sha256="a" * 64,
        file_intent_sha256="b" * 64,
        timing=timing,
    )
    argv = [
        proof.PYTHON,
        "-I",
        "/private/tmp/filer.py",
        "persist-closeout-record",
        "--deadline-ms",
        "2000",
    ]
    request = dict(
        cmd=proof.literal(argv),
        workdir="/private/tmp",
        login=False,
        tty=True,
        yield_time_ms=1000,
        max_output_tokens=3000,
    )
    rows = [
        dict(
            tool="exec_command",
            arguments=request,
            requested_ms=1000,
            returned_ms=1001,
            result=dict(output=proof.READY, session_id=71, exit_code=None),
        ),
        dict(
            tool="write_stdin",
            arguments=dict(
                session_id=71,
                chars=json.dumps(original, separators=(",", ":")) + "\n",
                yield_time_ms=999,
                max_output_tokens=3000,
            ),
            requested_ms=1001,
            returned_ms=1006,
            result=dict(output=proof.canonical(saved).decode(), exit_code=0),
        ),
    ]
    packet = dict(
        schema=proof.ACTUAL_SCHEMA, author="/root", argv=argv, request=request, responses=rows
    )
    return packet, original, argv, paths, saved


def checked(proof, fixture, **kw):
    packet, original, argv, paths, _ = fixture
    return proof.audit_courier(
        packet,
        original,
        argv=argv,
        author="/root",
        cwd="/private/tmp",
        deadline_ms=2000,
        expected_paths=paths,
        **kw,
    )


def test_courier_binds_one_original_data_message_and_pair(proof):
    result = checked(proof, courier(proof))
    assert result["actual_terminal_ms"] == 1006
    assert result["caller_on_time"] is True
    assert result["data_writes"] == 1


def test_actual_terminal_preserved_but_late_delivery_vetoes(proof):
    result = checked(proof, courier(proof), delivery_ms=2001)
    assert result["actual_terminal_ms"] == 1006
    assert result["caller_delivery_ms"] == 2001
    assert result["caller_on_time"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "author",
        "argv",
        "tty",
        "cmd",
        "foreign-session",
        "duplicate-data",
        "early-data",
        "changed-data",
        "bool-exit",
        "live",
        "truncate",
        "clock",
        "late-terminal",
        "timing",
        "pair",
        "hash",
        "extra-row",
        "bool-yield",
    ],
)
def test_courier_original_counterexamples(proof, damage):
    fixture = courier(proof)
    packet, original, argv, paths, saved = fixture
    rows = packet["responses"]
    if damage == "author":
        packet["author"] = "/someone"
    elif damage == "argv":
        packet["argv"] = ["other"]
    elif damage == "tty":
        packet["request"]["tty"] = False
    elif damage == "cmd":
        packet["request"]["cmd"] += " extra"
    elif damage == "foreign-session":
        rows[1]["arguments"]["session_id"] = 72
    elif damage == "duplicate-data":
        repeated = deepcopy(rows[1])
        repeated["result"] = dict(output="", session_id=71)
        rows.insert(1, repeated)
    elif damage == "early-data":
        rows[0]["result"]["output"] = ""
    elif damage == "changed-data":
        rows[1]["arguments"]["chars"] = "{}\n"
    elif damage == "bool-exit":
        rows[1]["result"]["exit_code"] = False
    elif damage == "live":
        rows[1]["result"]["session_id"] = 71
    elif damage == "truncate":
        rows[1]["result"]["original_token_count"] = 3001
    elif damage == "clock":
        rows[1]["requested_ms"] = 999
    elif damage == "late-terminal":
        rows[1]["returned_ms"] = 2001
    elif damage == "timing":
        saved["timing"]["packet_received"]["monotonic_us"] = 1
    elif damage == "pair":
        saved["copies"][1]["path"] = paths[0]
    elif damage == "hash":
        saved["sha256"] = "c" * 64
    elif damage == "extra-row":
        rows.append(deepcopy(rows[-1]))
    else:
        rows[1]["arguments"]["yield_time_ms"] = True
    if damage in ("timing", "pair", "hash"):
        rows[1]["result"]["output"] = proof.canonical(saved).decode()
    with pytest.raises(ValueError):
        checked(proof, fixture)


def test_blank_owned_polls_only_after_data_and_ready(proof):
    fixture = courier(proof)
    packet, _, _, _, _ = fixture
    packet["argv"][-1] = "10000"
    packet["request"]["cmd"] = proof.literal(packet["argv"])
    rows = packet["responses"]
    first = deepcopy(rows[0])
    first["result"]["output"] = ""
    ready = deepcopy(first)
    ready.update(
        tool="write_stdin",
        requested_ms=1001,
        returned_ms=1001,
        arguments=dict(session_id=71, chars="", yield_time_ms=5000, max_output_tokens=3000),
    )
    ready["result"]["output"] = proof.READY
    rows[:] = [first, ready, rows[1]]
    result = proof.audit_courier(
        packet,
        fixture[1],
        argv=fixture[2],
        author="/root",
        cwd="/private/tmp",
        deadline_ms=10000,
        expected_paths=fixture[3],
    )
    assert result["data_writes"] == 1


def readiness(proof, monkeypatch):
    tree = {
        n: proof.sha((proof.REPO / n).read_bytes())
        for n in (*proof.SOFTWARE, *proof.PRODUCTION, proof.PROTOCOL)
    }
    start = proof.START + 1000
    entry = dict(argv=proof.gate_args([3, 4, 5]), start_ms=start, end_ms=start + 290000)
    policy = dict(
        execution_identity=proof.IDENTITY,
        new_input_budget=dict(path=str(proof.DATA / "owner-budget.json"), sha256=proof.BUDGET),
        closeout_verification_paths=dict(
            package=str(proof.FORMAL / proof.PACKAGE), actual=str(proof.FORMAL / proof.ACTUAL)
        ),
        prior_public=dict(old="immutable proof"),
        registration=dict(formal=dict(bindings=23)),
    )
    report = dict(
        status=proof.STATUS,
        execution_identity=proof.IDENTITY,
        source_main="a" * 40,
        budget_sha256=proof.BUDGET,
        pricing_sha256=proof.PRICING,
        slots=[3, 4, 5],
        verification_slot=1,
        independent_entry=entry,
        authority_sha256=tree[proof.PROTOCOL],
        software_tree_sha256=proof.sha(proof.canonical(tree)),
        worker_sha256=tree[proof.WORKER],
        executed={n: tree[n] for n in proof.SOFTWARE},
        external_production_sources={n: tree[n] for n in proof.PRODUCTION},
        prior_public=policy["prior_public"],
        registration=policy["registration"]["formal"],
    )
    raw = proof.canonical(report)
    request = dict(
        cmd=proof.literal(entry["argv"]),
        workdir=str(proof.REPO),
        login=False,
        yield_time_ms=1000,
        max_output_tokens=3000,
    )
    actual = dict(
        schema=proof.ACTUAL_SCHEMA,
        author=proof.AUTHOR,
        argv=entry["argv"],
        request=request,
        responses=[
            dict(
                tool="exec_command",
                arguments=request,
                requested_ms=start,
                returned_ms=start + 100,
                result=dict(
                    output=proof.canonical(
                        dict(status=proof.STATUS, report_sha256=proof.sha(raw), verification_slot=1)
                    ).decode(),
                    exit_code=0,
                ),
            )
        ],
    )
    values = {proof.PACKAGE: raw, proof.ACTUAL: proof.canonical(actual)}
    seen = []

    def paired(folder, name, maximum=16 * 1024**2):
        assert folder == proof.FORMAL
        seen.append(name)
        return values[name]

    monkeypatch.setattr(proof, "pair", paired)
    monkeypatch.setattr(proof, "pricing", lambda: {})
    monkeypatch.setattr(
        proof, "history", lambda: SimpleNamespace(checkout_commit=lambda _: "a" * 40)
    )
    monkeypatch.setattr(proof.time, "time_ns", lambda: (start + 200) * 10**6)
    monkeypatch.setitem(
        sys.modules,
        "full60_input_loader",
        SimpleNamespace(
            loaded_source_sha256={str(proof.REPO / n): tree[n] for n in proof.SOFTWARE}
        ),
    )
    return policy, tree, report, values, actual, seen


def test_measured_gate_uses_small_report_and_actual_without_subprocess_or_archive(
    proof, monkeypatch
):
    policy, tree, _, _, _, seen = readiness(proof, monkeypatch)
    monkeypatch.setattr(
        subprocess, "Popen", lambda *a, **k: pytest.fail("measured process spawned")
    )
    monkeypatch.setattr(proof, "public_run", lambda *a, **k: pytest.fail("archive replayed"))
    monkeypatch.setattr(proof, "prior_evidence", lambda *a: pytest.fail("old tree replayed"))
    result = proof.verified_readiness(policy, tree)
    assert result["source_main"] == "a" * 40
    assert seen == [proof.PACKAGE, proof.ACTUAL]


@pytest.mark.parametrize(
    "damage",
    [
        "slot",
        "tree",
        "compiled",
        "source",
        "exit",
        "future",
        "package",
        "stdout",
        "registration",
        "production",
    ],
)
def test_measured_gate_rejects_original_or_release_mutation(proof, monkeypatch, damage):
    policy, tree, report, values, actual, _ = readiness(proof, monkeypatch)
    if damage == "slot":
        report["verification_slot"] = 2
    elif damage == "tree":
        tree[proof.PROTOCOL] = "b" * 64
    elif damage == "compiled":
        sys.modules["full60_input_loader"].loaded_source_sha256[str(proof.REPO / proof.WORKER)] = (
            "b" * 64
        )
    elif damage == "source":
        report["source_main"] = "b" * 40
    elif damage == "exit":
        actual["responses"][-1]["result"]["exit_code"] = 1
    elif damage == "future":
        actual["responses"][-1]["returned_ms"] += 1000
    elif damage == "package":
        report["status"] = "FAKE"
    elif damage == "stdout":
        actual["responses"][-1]["result"]["output"] = "{}\n"
    elif damage == "registration":
        report["registration"] = {}
    else:
        report["external_production_sources"] = {}
    values[proof.PACKAGE] = proof.canonical(report)
    values[proof.ACTUAL] = proof.canonical(actual)
    with pytest.raises(ValueError):
        proof.verified_readiness(policy, tree)


@pytest.mark.parametrize("missing", [None, "scripts/p17_m2_source_acquisition_independent.py"])
def test_real_source_only_launcher_profiles_have_complete_executed_verifier_set(proof, missing):
    """Use the real isolated launcher/loader and both profiles, with public buffers mocked.

    No paid evidence/entry, subprocess Git or Native path is opened. In particular
    production receipt code is an external frozen dependency, not falsely listed
    as code executed by this independent checker.
    """
    harness = r"""
import json, runpy, sys
from pathlib import Path
missing = MISSING
def trace(frame, event, arg):
    if event != 'call' or frame.f_code.co_name != 'verify' or not frame.f_globals.get(
            '__file__','').endswith('/closeout_readiness_proof.py'):
        return trace
    sys.settrace(None)
    p = sys.modules['closeout_readiness_proof']
    from types import SimpleNamespace
    p.REPO=Path.cwd()
    p.PYTHON=sys.executable
    p.sys=SimpleNamespace(flags=sys.flags,executable=sys.executable,platform='darwin',modules=sys.modules)
    import subprocess, formal_input_independent as public, staged_binding_evidence as reg
    import resource
    resource.getrusage=lambda kind:SimpleNamespace(ru_maxrss=1024)
    import child_readiness_proof as child, staged_input_filer as wire
    h = p.history()
    main='a'*40
    h.checkout_commit=lambda repo:main
    h.verified_readiness=lambda policy,tree:dict(
        source_main='671a21b3d47fae16610e13884993abee5bee8e12',
        verified_returned_ms=1795519025567,
        package=dict(path=str(p.DATA.parent/'certificate-20261124-formal/certificate-replay.json'),
            sha256='133553193c411d565860c0a04ac81b65f8bad47152d1b89caa88e28ee3b75c81'),
        actual=dict(path=str(p.DATA.parent/'certificate-20261124-formal/certificate-replay-actual.json'),
            sha256='7b3af893a673787cce4992eb9ca92db91c08e4112e81a0d225265cf839edbeda'))
    child.historical_inputs=lambda:({}, {})
    public.verify_prior_public=lambda *a:dict(public_end_ms=1)
    reg.verified_formal_registration=lambda:({},[dict(path=str(i)) for i in range(23)])
    p.pair=lambda *a,**k:b'{}\n'
    p.pricing=lambda:{}
    p.public_reservations=lambda slots:dict(reserved_FULL=9000,remaining_FULL=600)
    p.time.time_ns=lambda:(p.START+1000)*10**6
    subprocess.check_output=lambda args,**kw:b'' if 'status' in args else (main+'\n').encode()
    import p17_m2_input_continuation as profiles
    control=profiles.profile('control',profiles.CLOSEOUT_FORMAL)
    profiles.profile('independent',profiles.CLOSEOUT_FORMAL)
    tree=control.source_freeze(p.IDENTITY)
    entry=dict(argv=p.gate_args([3,4,5]),start_ms=p.START,end_ms=p.START+290000)
    p.verification_entry=lambda slots,tree:(1,entry)
    p.public_run=lambda slot,origins=None:dict(slot=slot,source_main=main,source_tree=tree,
        kind='REPLAY_NEGATIVE' if origins is not None else 'FULL_POSITIVE')
    original=p.compiled
    def compiled(tree,*,verification):
        if missing:
            sys.modules['full60_input_loader'].loaded_source_sha256.pop(str(p.REPO/missing),None)
        return original(tree,verification=verification)
    p.compiled=compiled
    outputs=[]
    def save(path, raw):
        report=p.parse(raw)
        assert set(report['executed'])==set(p.SOFTWARE)
        assert 'scripts/closeout_receipt.py' not in report['executed']
        assert report['external_production_sources']['scripts/closeout_receipt.py']==tree[
            'scripts/closeout_receipt.py']
        outputs.append(str(path))
    wire.write_private=save
    return None
sys.settrace(trace)
sys.argv=['closeout_verify.py','verify','3','4','5']
runpy.run_path('scripts/closeout_verify.py',run_name='__main__')
""".replace("MISSING", repr(missing))
    result = subprocess.run(
        [proof.PYTHON, "-I", "-c", harness],
        cwd=proof.REPO,
        env={**os.environ, **dict(s.split("=", 1) for s in proof.THREADS)},
        capture_output=True,
        text=True,
        timeout=30,
    )
    if missing:
        assert result.returncode != 0
        assert "actual compiled source differs" in result.stderr
    else:
        assert result.returncode == 0, result.stderr
        value = proof.parse(result.stdout.encode())
        assert value["verification_slot"] == 1 and value["status"] == proof.STATUS


def full_fixture(proof, monkeypatch):
    """Six synthetic role wires; the published resource oracle is a separate seam."""
    from r0_caller_receipt import project

    slot = 3
    root = f"/private/tmp/topolab-public-closeout-20261125-a{slot}"
    start = proof.START + 1000
    tree = {"scripts/closeout_public_schedule.mjs": "a" * 64}
    claim = dict(
        schema="topolab.closeout-public-entry.v1",
        slot=slot,
        root=root,
        mode="released",
        fixture_kind="FULL_POSITIVE",
        formal_authority=False,
        author=proof.PUBLIC_AUTHOR,
        budget_sha256=proof.BUDGET,
        pricing_sha256=proof.PRICING,
        fee_reservation_FULL=3600,
        charge_FULL=600,
        start_ms=start,
        end_ms=start + 780000,
        checkout_head="b" * 40,
        software_sha256=tree,
        scheduler_sha256="c" * 64,
    )
    plan = dict(
        root=root,
        execution_identity=proof.PUBLIC_ID,
        scope=proof.PUBLIC_SCOPE,
        formal_authority=False,
        role_order=list(proof.ROLES),
        runtime=dict(cwd=str(proof.REPO)),
        source_tree={**tree, "fixture/scheduler": claim["scheduler_sha256"]},
    )
    files = {"native/plan.json": proof.canonical(plan), "caller/entry.json": proof.canonical(claim)}
    plan_sha = proof.sha(files["native/plan.json"])
    prefix = [proof.PYTHON, "-I", str(proof.REPO / "scripts/closeout_public_control.py")]
    calls, role_info, results, wires = {}, {}, {}, {}
    clock = start

    def call(key, argv, value):
        nonlocal clock
        request = dict(
            cmd=proof.literal(argv),
            workdir=str(proof.REPO),
            login=False,
            yield_time_ms=1000,
            max_output_tokens=6000,
        )
        packet = dict(
            schema=proof.ACTUAL_SCHEMA,
            author=proof.PUBLIC_AUTHOR,
            event_id=key,
            argv=argv,
            request=request,
            responses=[
                dict(
                    tool="exec_command",
                    arguments=request,
                    requested_ms=clock,
                    returned_ms=clock + 1,
                    result=dict(output=proof.canonical(value).decode(), exit_code=0),
                )
            ],
        )
        clock += 2
        calls[key] = packet
        files[f"caller/{key}-actual.json"] = proof.canonical(packet)
        return packet

    call("prepare", prefix + ["prepare-public", "--root", root], dict(plan_sha256=plan_sha))
    for role, cap in zip(proof.ROLES, proof.CAPS, strict=True):
        deadline = min(claim["end_ms"], clock + cap * 1000 - 10000)
        role_info[role] = dict(entered_ms=clock, deadline_ms=deadline)
        tail = ["--root", root, "--plan-sha", plan_sha, "--role", role]
        native = dict(pending=dict(role=role), completion=dict(role=role))
        wires[role] = native
        files[f"native/receipts/{role}-wire.json"] = proof.canonical(native)
        events = []
        for mode in ("supervise", "record"):
            key = role + "-" + mode
            packet = call(
                key,
                prefix + [mode, *tail],
                dict(status="PENDING_EXTERNAL_EXIT", controller_exit=0)
                if mode == "supervise"
                else project(mode, role, plan_sha, native, proof.canonical(native)),
            )
            raw = proof.canonical(packet)
            row = packet["responses"][0]
            event = dict(
                event_id=key,
                raw_packet_sha256=proof.sha(raw),
                author=proof.PUBLIC_AUTHOR,
                exit_code=0,
                complete=True,
                start_seconds=row["requested_ms"] / 1000,
                end_seconds=row["returned_ms"] / 1000,
            )
            events.append(event)
            files[f"native/{role}-{mode}-actual-event.json"] = proof.canonical(event)
            for copy in ("primary", "backup"):
                files[f"custody/{copy}/{role}-{mode}-actual.json"] = raw
            outputs = [f"{role}-{mode}-actual-event.json"] + (
                [f"{role}-events.json"] if mode == "record" else []
            )
            intent = dict(
                schema="topolab.public-closeout.filing-intent.v1",
                program_sha256=tree["scripts/closeout_public_schedule.mjs"],
                role=role,
                mode=mode,
                author=proof.PUBLIC_AUTHOR,
                root=root,
                plan_sha256=plan_sha,
                outputs=outputs,
                event=event,
            )
            intent_raw = proof.canonical(intent)
            paths = [
                root + suffix + f"/{role}-{mode}-actual.json"
                for suffix in ("-evidence", "-evidence-backup")
            ]
            saved = dict(
                status="PAIRED_PERSISTED",
                sha256=proof.sha(raw),
                bytes=len(raw),
                failures=[],
                path=paths[0],
                copies=[dict(path=p, sha256=proof.sha(raw), bytes=len(raw)) for p in paths],
                program_sha256=intent["program_sha256"],
                file_intent_sha256=proof.sha(intent_raw),
            )
            persist_key = role + "-persist-" + mode
            if role == "shared-closeout" and mode == "record":
                saved["timing"] = {
                    name: dict(utc_us=clock * 1000 + n, monotonic_us=clock * 1000 + n)
                    for n, name in enumerate(proof.TIMING_KEYS)
                }
                argv = prefix + [
                    "persist-closeout-record",
                    *tail,
                    "--event-mode",
                    mode,
                    "--deadline-ms",
                    str(deadline),
                ]
                request = dict(
                    cmd=proof.literal(argv),
                    workdir=str(proof.REPO),
                    login=False,
                    tty=True,
                    yield_time_ms=1000,
                    max_output_tokens=3000,
                )
                courier_packet = dict(
                    schema=proof.ACTUAL_SCHEMA,
                    author=proof.PUBLIC_AUTHOR,
                    argv=argv,
                    request=request,
                    responses=[
                        dict(
                            tool="exec_command",
                            arguments=request,
                            requested_ms=clock,
                            returned_ms=clock + 1,
                            result=dict(output=proof.READY, session_id=81),
                        ),
                        dict(
                            tool="write_stdin",
                            arguments=dict(
                                session_id=81,
                                chars=json.dumps(packet, separators=(",", ":")) + "\n",
                                yield_time_ms=1000,
                                max_output_tokens=3000,
                            ),
                            requested_ms=clock + 1,
                            returned_ms=clock + 2,
                            result=dict(output=proof.canonical(saved).decode(), exit_code=0),
                        ),
                    ],
                )
                clock += 3
                calls[persist_key] = courier_packet
                files[f"caller/{persist_key}-actual.json"] = proof.canonical(courier_packet)
            else:
                call(
                    persist_key,
                    prefix
                    + [
                        "persist-public",
                        *tail,
                        "--event-mode",
                        mode,
                        "--packet-json",
                        json.dumps(packet, separators=(",", ":")),
                    ],
                    saved,
                )
            for copy in ("primary", "backup"):
                files[f"custody/{copy}/filing-{role}-{mode}-intent.json"] = intent_raw
                files[f"custody/{copy}/filing-{role}-{mode}-spent.json"] = proof.canonical(
                    dict(intent_sha256=proof.sha(intent_raw), event_id=key, outputs=outputs)
                )
            call(
                role + "-file-" + mode,
                prefix
                + [
                    "file-public",
                    *tail,
                    "--event-mode",
                    mode,
                    "--packet-sha",
                    proof.sha(raw),
                    "--intent-sha",
                    proof.sha(intent_raw),
                    "--program-sha",
                    intent["program_sha256"],
                ],
                dict(
                    status="ACTUAL_EVENT_FILED",
                    role=role,
                    mode=mode,
                    intent_sha256=proof.sha(intent_raw),
                ),
            )
        files[f"native/{role}-events.json"] = proof.canonical(events)
        result = dict(role=role, full_role_evidence_accepted=True)
        results[role] = result
        binder = call(
            role + "-bind",
            prefix + ["bind", *tail],
            project("bind", role, plan_sha, result, proof.canonical(result)),
        )
        role_info[role]["bind_return_ms"] = binder["responses"][-1]["returned_ms"]
    reservation = dict(
        shared_reserved_FULL_seconds=300,
        scope=proof.PUBLIC_SCOPE,
        execution_identity=proof.PUBLIC_ID,
        plan_sha256=plan_sha,
        refunds_allowed=False,
    )
    files["native/ledger-reservation.json"] = proof.canonical(reservation)
    for role, cap in zip(proof.ROLES, proof.CAPS, strict=True):
        files[f"native/{role}-dispatch-charge.json"] = proof.canonical(
            dict(
                role=role,
                plan_sha256=plan_sha,
                scope=proof.PUBLIC_SCOPE,
                execution_identity=proof.PUBLIC_ID,
                frozen_FULL_seconds=cap,
                charged_FULL_seconds=0 if role == "shared-closeout" else cap,
                shared_reservation_sha256=proof.sha(proof.canonical(reservation)),
            )
        )

    def observations(count, prefix, dev=1):
        rows = []
        for n in range(count):
            point = dict(st_dev=dev, st_ino=n + 1, st_size=n + 1, st_mtime_ns=1)
            rows.append(
                dict(
                    path=f"{prefix}/{n}",
                    byte_size=n + 1,
                    sha256="d" * 64,
                    **{stage: dict(point) for stage in ("declared", "before", "after", "closing")},
                )
            )
        return rows

    local = observations(1071, "data")
    manifest = dict(members=[{k: r[k] for k in ("path", "byte_size", "sha256")} for r in local])
    version = proof.sha(proof.canonical(manifest))
    files["native/closed.json"] = proof.canonical(
        dict(manifest=manifest, version_id=version, local_identity_rows=local)
    )
    files["native/registry.json"] = b"{}\n"
    for r, count in (("r0", 40), ("r1", 558)):
        source = observations(count, r)
        files[f"native/{r}-source-rows.json"] = proof.canonical(source)
        value = dict(
            status=f"PUBLIC_INDEPENDENT_{r.upper()}_CHECKED",
            scope=proof.PUBLIC_SCOPE,
            execution_identity=proof.PUBLIC_ID,
            B_C_admission=False,
            source_count=count,
            source_rows=source,
            source_registry_sha256=proof.sha(b"{}\n"),
        )
        if r == "r1":
            value["local_identity_rows"] = local
            files["native/r1-proof.json"] = proof.canonical(value)
        files[f"native/receipts/independent-{r}/independent-{r}/command.log"] = proof.canonical(
            value
        )
    backup = dict(
        status="PUBLIC_INDEPENDENT_BACKUP_CHECKED",
        scope=proof.PUBLIC_SCOPE,
        execution_identity=proof.PUBLIC_ID,
        B_C_admission=False,
        manifest=manifest,
        version_id=version,
        member_count=1071,
        identity_rows=observations(1071, "data", dev=2),
    )
    files["native/backup-proof.json"] = proof.canonical(backup)
    files["native/receipts/shared-closeout/shared-closeout/command.log"] = proof.canonical(backup)
    files["native/shared-packet.json"] = proof.canonical(
        dict(
            scope=proof.PUBLIC_SCOPE,
            execution_identity=proof.PUBLIC_ID,
            plan_sha256=plan_sha,
            status="SEALED_HANDOFF_PENDING_INDEPENDENT_FILING",
            secondary_failures=[],
            role_results=results,
            raw_packets={
                role: dict(
                    wire=wires[role],
                    raw_tool_events=proof.parse(files[f"native/{role}-events.json"]),
                )
                for role in proof.ROLES
            },
        )
    )
    outer = dict(
        status="PASS_PUBLIC_NATIVE_CLOSEOUT",
        mode="released",
        root=root,
        controlled=[],
        roles=role_info,
        calls=calls,
    )
    files["caller/outer-original.json"] = proof.canonical(outer)
    summary = dict(slot=slot, root=root, fixture_charge_FULL=3600)
    monkeypatch.setattr(proof, "native_role", lambda role, *a: (results[role], wires[role]))
    return slot, claim, summary, files


def test_complete_original_43_call_full_chain(proof, monkeypatch):
    fixture = full_fixture(proof, monkeypatch)
    result = proof.audit_full(*fixture)
    assert result["known_FULL"] == 3600
    assert result["member_count"] == 1071 and len(result["role_results"]) == 6


@pytest.mark.parametrize(
    "damage",
    [
        "missing-role",
        "native-event",
        "record-output",
        "copy",
        "spent",
        "file-argv",
        "bind-output",
        "deadline",
        "charge",
        "version",
        "stop",
    ],
)
def test_full_public_original_chain_mutation_veto(proof, monkeypatch, damage):
    slot, claim, summary, files = full_fixture(proof, monkeypatch)
    outer = proof.parse(files["caller/outer-original.json"])
    role = "shared-closeout"
    if damage == "missing-role":
        del outer["roles"][role]
    elif damage == "native-event":
        files[f"native/{role}-record-actual-event.json"] = b"{}\n"
    elif damage == "record-output":
        outer["calls"][role + "-record"]["responses"][0]["result"]["output"] = "{}\n"
    elif damage == "copy":
        files[f"custody/backup/{role}-record-actual.json"] = b"{}\n"
    elif damage == "spent":
        files[f"custody/primary/filing-{role}-record-spent.json"] = b"{}\n"
    elif damage == "file-argv":
        outer["calls"][role + "-file-record"]["argv"][-1] = "e" * 64
    elif damage == "bind-output":
        outer["calls"][role + "-bind"]["responses"][0]["result"]["output"] = "{}\n"
    elif damage == "deadline":
        outer["roles"][role]["deadline_ms"] += 1
    elif damage == "charge":
        charge = proof.parse(files[f"native/{role}-dispatch-charge.json"])
        charge["charged_FULL_seconds"] = 300
        files[f"native/{role}-dispatch-charge.json"] = proof.canonical(charge)
    elif damage == "version":
        backup = proof.parse(files["native/backup-proof.json"])
        backup["version_id"] = "e" * 64
        files["native/backup-proof.json"] = proof.canonical(backup)
    else:
        files["native/STOP.json"] = b"{}\n"
    files["caller/outer-original.json"] = proof.canonical(outer)
    with pytest.raises(ValueError):
        proof.audit_full(slot, claim, summary, files)


def negative_fixture(proof, monkeypatch):
    positive_fixture = full_fixture(proof, monkeypatch)
    positive = proof.audit_full(*positive_fixture)
    original_calls = proof.parse(positive_fixture[3]["caller/outer-original.json"])["calls"]
    positive.update(
        result_sha256="e" * 64,
        index_sha256="f" * 64,
        archive_sha256="1" * 64,
        original_shared_returns={
            m: original_calls["shared-closeout-" + m] for m in ("supervise", "record")
        },
    )
    slot = 5
    root = f"/private/tmp/topolab-public-closeout-20261125-a{slot}"
    claim = deepcopy(positive_fixture[1])
    ref = dict(
        slot=3,
        rec_sha256=positive["shared_original"]["packet_sha256"],
        plan_sha256=positive["plan_sha256"],
        report_sha256=positive["result_sha256"],
        index_sha256=positive["index_sha256"],
        archive_sha256=positive["archive_sha256"],
    )
    start = positive["original_end_ms"] + 1000
    claim.update(
        slot=slot,
        root=root,
        mode="late",
        fixture_kind="REPLAY_NEGATIVE",
        fee_reservation_FULL=600,
        positive_origin=ref,
        start_ms=start,
        end_ms=start + 780000,
    )
    entered = start + 2
    deadline = entered + 290000
    prefix = [proof.PYTHON, "-I", str(proof.REPO / "scripts/closeout_public_control.py")]
    prepare_argv = prefix + ["prepare-replay", "--root", root]
    request = dict(
        cmd=proof.literal(prepare_argv),
        workdir=str(proof.REPO),
        login=False,
        yield_time_ms=1000,
        max_output_tokens=6000,
    )
    prepare = dict(
        schema=proof.ACTUAL_SCHEMA,
        author=proof.PUBLIC_AUTHOR,
        argv=prepare_argv,
        request=request,
        responses=[
            dict(
                tool="exec_command",
                arguments=request,
                requested_ms=start,
                returned_ms=start + 1,
                result=dict(
                    exit_code=0,
                    output=proof.canonical(
                        dict(
                            scope="PUBLIC_CLOSEOUT_RECEIPT_REPLAY_ONLY",
                            formal_authority=False,
                            origin=ref,
                            native_roles_dispatched=0,
                            original_returns=positive["original_shared_returns"],
                        )
                    ).decode(),
                ),
            )
        ],
    )
    original = positive["shared_original"]["packet"]
    original_raw = proof.canonical(original)
    paths = [
        root + suffix + "/shared-closeout-record-actual.json"
        for suffix in ("-evidence", "-evidence-backup")
    ]
    intent = dict(
        schema="topolab.public-closeout.replay-intent.v1",
        formal_authority=False,
        fixture_root=root,
        origin=ref,
        program_sha256="a" * 64,
        packet_sha256=proof.sha(original_raw),
        event_id=original["event_id"],
        author=proof.PUBLIC_AUTHOR,
    )
    saved = dict(
        status="PAIRED_PERSISTED",
        bytes=len(original_raw),
        sha256=proof.sha(original_raw),
        path=paths[0],
        copies=[
            dict(path=p, bytes=len(original_raw), sha256=proof.sha(original_raw)) for p in paths
        ],
        failures=[],
        program_sha256="a" * 64,
        file_intent_sha256=proof.sha(proof.canonical(intent)),
        timing={
            name: dict(utc_us=(entered + 2) * 1000 + n, monotonic_us=(entered + 2) * 1000 + n)
            for n, name in enumerate(proof.TIMING_KEYS)
        },
    )
    argv = prefix + [
        "persist-closeout-record",
        "--root",
        root,
        "--plan-sha",
        ref["plan_sha256"],
        "--role",
        "shared-closeout",
        "--event-mode",
        "record",
        "--deadline-ms",
        str(deadline),
    ]
    request = dict(
        cmd=proof.literal(argv),
        workdir=str(proof.REPO),
        login=False,
        tty=True,
        yield_time_ms=1000,
        max_output_tokens=3000,
    )
    courier_packet = dict(
        schema=proof.ACTUAL_SCHEMA,
        author=proof.PUBLIC_AUTHOR,
        argv=argv,
        request=request,
        responses=[
            dict(
                tool="exec_command",
                arguments=request,
                requested_ms=entered,
                returned_ms=entered + 1,
                result=dict(output=proof.READY, session_id=91),
            ),
            dict(
                tool="write_stdin",
                arguments=dict(
                    session_id=91,
                    chars=json.dumps(original, separators=(",", ":")) + "\n",
                    yield_time_ms=1000,
                    max_output_tokens=3000,
                ),
                requested_ms=entered + 1,
                returned_ms=entered + 3,
                result=dict(output=proof.canonical(saved).decode(), exit_code=0),
            ),
        ],
    )
    key = "shared-closeout-persist-record"
    outer = dict(
        status="STOP_PUBLIC_CLOSEOUT",
        mode="late",
        root=root,
        stage=key,
        error="Error: closeout receipt returned late or lacks original clock",
        end_ms=deadline + 30,
        roles={
            "shared-closeout": dict(
                entered_ms=entered,
                deadline_ms=deadline,
                native_replay=True,
                source_plan=positive["plan_sha256"],
                origin_slot=3,
            )
        },
        calls=dict(prepare=prepare, **{key: courier_packet}),
        controlled=[
            dict(
                stage=key,
                tool="write_stdin",
                underlying_tool_returned_ms=entered + 3,
                caller_delivery_ms=deadline + 1,
            )
        ],
    )
    files = {
        "caller/outer-original.json": proof.canonical(outer),
        "caller/entry.json": proof.canonical(claim),
        "caller/prepare-actual.json": proof.canonical(prepare),
        "caller/" + key + "-actual.json": proof.canonical(courier_packet),
    }
    for copy in ("primary", "backup"):
        files[f"custody/{copy}/shared-closeout-record-actual.json"] = original_raw
        files[f"custody/{copy}/filing-shared-closeout-record-intent.json"] = proof.canonical(intent)
    return slot, claim, dict(slot=slot, fixture_charge_FULL=600), files, {3: positive}


def test_replay_negative_keeps_origin_native_and_new_pair_but_no_authority(proof, monkeypatch):
    result = proof.audit_negative(*negative_fixture(proof, monkeypatch))
    assert (
        result["actual_native_roles"] == result["filed_events"] == result["bind_invocations"] == 0
    )
    assert result["courier"]["caller_on_time"] is False


@pytest.mark.parametrize(
    "damage",
    ["origin", "fake-native", "filed", "delivery", "original", "intent", "original-return-clock"],
)
def test_replay_negative_does_not_promote_saved_bytes(proof, monkeypatch, damage):
    slot, claim, summary, files, origins = negative_fixture(proof, monkeypatch)
    outer = proof.parse(files["caller/outer-original.json"])
    if damage == "origin":
        claim["positive_origin"]["rec_sha256"] = "9" * 64
    elif damage == "fake-native":
        files["native/plan.json"] = b"{}\n"
    elif damage == "filed":
        files["custody/primary/filing-shared-closeout-record-spent.json"] = b"{}\n"
    elif damage == "delivery":
        outer["controlled"][0]["caller_delivery_ms"] = outer["roles"]["shared-closeout"][
            "deadline_ms"
        ]
    elif damage == "original":
        files["custody/backup/shared-closeout-record-actual.json"] = b"{}\n"
    elif damage == "intent":
        files["custody/primary/filing-shared-closeout-record-intent.json"] = b"{}\n"
    else:
        outer["controlled"][0]["underlying_tool_returned_ms"] += 1
    files["caller/outer-original.json"] = proof.canonical(outer)
    with pytest.raises(ValueError):
        proof.audit_negative(slot, claim, summary, files, origins)


def test_fixed_alias_promotion_recovers_partial_write_without_overwriting(proof, monkeypatch):
    _, _, report, values, actual, _ = readiness(proof, monkeypatch)
    import staged_input_filer as wire

    raw, actual_raw = values[proof.PACKAGE], proof.canonical(actual)
    stored = {}
    attempts = 0

    def paired(folder, name, maximum=16 * 1024**2):
        if folder == proof.FORMAL and name == "closeout-readiness-slot-1.json":
            return raw
        if folder == proof.DATA and name == "released-verification-1-entry.json":
            return proof.canonical(report["independent_entry"])
        a = stored[folder / name]
        b = stored[folder.with_name(folder.name + "-backup") / name]
        assert a == b
        return a

    def save(path, value):
        nonlocal attempts
        attempts += 1
        if path in stored:
            raise FileExistsError(path)
        if attempts == 2:
            raise OSError("synthetic interrupted alias persistence")
        stored[path] = value

    monkeypatch.setattr(proof, "pair", paired)
    monkeypatch.setattr(wire, "write_private", save)
    monkeypatch.setattr(wire, "read_private", lambda path, maximum: stored[path])
    with pytest.raises(OSError, match="interrupted"):
        proof.promote(actual_raw)
    assert len(stored) == 1
    result = proof.promote(actual_raw)
    assert result["actual_sha256"] == proof.sha(actual_raw)
    assert len(stored) == 4
    assert all(
        stored[folder / proof.PACKAGE] == raw and stored[folder / proof.ACTUAL] == actual_raw
        for folder in (proof.FORMAL, proof.FORMAL.with_name(proof.FORMAL.name + "-backup"))
    )
    stored[proof.FORMAL / proof.PACKAGE] = b"different original"
    with pytest.raises(ValueError, match="conflicting"):
        proof.promote(actual_raw)


def standard_native_fixture(proof):
    """Use the existing authored standard Native fixture and its real audit API.

    No new process or named role is launched. The generic public controller
    retains helper profiles as individual files, unlike formal acquisition's
    sampler journal. Both resource and original-return checks below are real.
    """
    path = SCRIPTS.parent / "tests/test_p17_m2_content_verified_independent.py"
    spec = importlib.util.spec_from_file_location("closeout_standard_fixture", path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    pending, completion, events, inner, outer = fixture.public_role_facts()
    controller_profile = outer["F-outer-native"]
    outer = {"outer-controller": controller_profile}
    for item in completion["resource_components"]:
        if item.get("profile") == "F-outer-native":
            item["profile"] = "outer-controller"
    fixture.seal_native_facts(fixture.load(), pending, completion, inner, outer, events)
    expected = fixture.audit_public_role(
        fixture.load(), (pending, completion, events, inner, outer)
    )
    assert expected["full_role_evidence_accepted"] is True
    role = "exporter-r0"
    folder = f"native/receipts/{role}/{role}/"
    files = {
        folder + "command.json": proof.canonical(inner["record"]),
        folder + "command.time": inner["profile"],
        folder + "command.log": inner["log"],
        f"native/receipts/{role}-controller.time": controller_profile,
        f"native/receipts/{role}-wire.json": proof.canonical(
            dict(pending=pending, completion=completion)
        ),
        f"native/{role}-events.json": proof.canonical(events),
        f"native/{role}-accepted.json": proof.canonical(
            dict(raw_tool_events=events, result=expected)
        ),
    }
    files.update({folder + name: raw for name, raw in inner["helper_profiles"].items()})
    return role, files, events, inner["expected_argv"], "a" * 64


def test_standard_public_native_archive_uses_real_oracle_without_formal_journal(proof):
    fixture = standard_native_fixture(proof)
    assert not any(name.endswith("sampler-evidence.jsonl") for name in fixture[1])
    result, _ = proof.native_role(*fixture)
    assert result["RSS_envelope_bytes"] == 980
    assert result["full_role_evidence_accepted"] is True


@pytest.mark.parametrize(
    "damage", ["helper", "missing", "extra", "name", "controller", "record", "event"]
)
def test_standard_public_native_artifact_change_is_rejected_by_real_oracle(proof, damage):
    role, files, events, argv, plan_sha = standard_native_fixture(proof)
    folder = f"native/receipts/{role}/{role}/"
    if damage == "helper":
        files[folder + "sampler-0.time"] += b"changed"
    elif damage == "missing":
        del files[folder + "sampler-0.time"]
    elif damage == "extra":
        files[folder + "sampler-1.time"] = files[folder + "sampler-0.time"]
    elif damage == "name":
        record = proof.parse(files[folder + "command.json"])
        record["helpers"][0]["profile"] = "other.time"
        files[folder + "command.json"] = proof.canonical(record)
    elif damage == "controller":
        files[f"native/receipts/{role}-controller.time"] += b"changed"
    elif damage == "record":
        record = proof.parse(files[folder + "command.json"])
        record["exit_code"] = False
        files[folder + "command.json"] = proof.canonical(record)
    else:
        events[-1]["observed_completion_sha256"] = "0" * 64
    with pytest.raises((ValueError, KeyError)):
        proof.native_role(role, files, events, argv, plan_sha)


def test_complete_six_role_index_above_old_single_role_cap(proof):
    files = {f"native/receipts/r/sampler-{n}.time": b"tiny public profile" for n in range(600)}
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, raw in files.items():
            item = tarfile.TarInfo(name)
            item.size = len(raw)
            archive.addfile(item, io.BytesIO(raw))
    index = proof.canonical(
        {n: dict(bytes=len(raw), sha256=proof.sha(raw)) for n, raw in files.items()}
    )
    assert proof.archive_buffers(buffer.getvalue(), index) == files
    changed = proof.parse(index)
    changed[next(iter(changed))]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        proof.archive_buffers(buffer.getvalue(), proof.canonical(changed))


def test_six_role_index_count_above_new_finite_cap_is_rejected_before_tar(proof):
    index = {f"native/item-{n}": dict(bytes=1, sha256="0" * 64) for n in range(8193)}
    with pytest.raises(ValueError, match="bounded six-role index"):
        proof.archive_buffers(b"not opened", proof.canonical(index))


@pytest.mark.parametrize("damage", ["member-size", "total-size", "link", "unsafe"])
def test_six_role_archive_caps_are_checked_before_any_member_read(proof, monkeypatch, damage):
    count = 9 if damage == "total-size" else 1
    members = [tarfile.TarInfo(f"native/item-{n}.json") for n in range(count)]
    for member in members:
        member.size = 15 * 1024**2 if damage == "total-size" else 1
    if damage == "member-size":
        members[0].size = 16 * 1024**2 + 1
    elif damage == "link":
        members[0].type = tarfile.SYMTYPE
    elif damage == "unsafe":
        members[0].name = "native/../payload.json"

    class HeaderOnly:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def getmembers(self):
            return members

        def extractfile(self, member):
            pytest.fail("unsafe/oversize member was read")

    monkeypatch.setattr(proof.tarfile, "open", lambda **kw: HeaderOnly())
    index = {m.name: dict(bytes=m.size, sha256="0" * 64) for m in members}
    with pytest.raises(ValueError, match="archive inventory"):
        proof.archive_buffers(b"synthetic headers", proof.canonical(index))
