"""Public caller/CLI seams; all graphs and tools are declared software fixtures."""

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def load(name, checkout=REPO):
    path = checkout / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_original_terminal_checks_full_owned_poll_chain_without_rewriting_failure():
    subject = load("staged_input_filer")
    argv = ["declared-python", "-I", "declared-control", "supervise"]
    request = dict(
        cmd=subject.literal_command(argv), workdir="declared-checkout", max_output_tokens=4000
    )
    packet = dict(
        schema=subject.ACTUAL_SCHEMA,
        author="/root",
        argv=argv,
        request=request,
        responses=[
            dict(
                tool="exec_command",
                arguments=request,
                requested_ms=10,
                returned_ms=11,
                result=dict(output="start", session_id=7),
            ),
            dict(
                tool="write_stdin",
                arguments=dict(session_id=7, chars="", yield_time_ms=5000),
                requested_ms=12,
                returned_ms=13,
                result=dict(output="failure", exit_code=1),
            ),
        ],
    )
    original = copy.deepcopy(packet)
    assert subject.validate_terminal(packet, argv, "/root", "declared-checkout") == (10, 13, 1)
    assert packet == original
    for field, value in [("session_id", 8), ("yield_time_ms", True), ("chars", "input")]:
        bad = copy.deepcopy(packet)
        bad["responses"][1]["arguments"][field] = value
        with pytest.raises(ValueError):
            subject.validate_terminal(bad, argv, "/root", "declared-checkout")


def test_private_metadata_publisher_rejects_symlinks_and_preserves_first_bytes(tmp_path):
    subject = load("staged_input_filer")
    target = tmp_path / "actual.json"
    raw = subject.canonical({"original": "failure", "exit": 1})
    saved = subject.write_private(target, raw)
    assert saved["sha256"] == subject.sha(raw)
    assert subject.read_private(target) == raw
    with pytest.raises(FileExistsError):
        subject.write_private(target, b"replacement")
    link = tmp_path / "link.json"
    link.symlink_to(target)
    with pytest.raises(OSError):
        subject.read_private(link)
    assert target.read_bytes() == raw


def test_partial_existing_control_bytes_are_retained_as_partial_not_success(tmp_path):
    subject = load("staged_input_filer")
    path = tmp_path / "declared-control.log"
    path.write_bytes(b"original failed control output")
    path.chmod(0o600)
    raw, observation = subject.capture_existing(path, maximum=8)
    assert raw == b"original"
    assert observation["status"] == "PARTIAL_OBSERVED"
    assert observation["source_complete"] is False
    assert observation["returned_bytes"] == 8
    assert observation["role_resource_acceptance"] == "NOT_CLAIMED"
    snapshot = tmp_path / "observed-prefix.raw"
    subject.write_private(snapshot, raw)
    assert snapshot.read_bytes() == b"original"


def test_accepted_native_file_alone_does_not_release_the_other_author():
    subject = load("staged_input_waiter")
    wire = subject.wire
    role, pin = wire.ROLES[0], "f" * 64
    value = dict(
        result=dict(
            full_role_evidence_accepted=True,
            evidence_complete=True,
            role=role,
            execution_identity=wire.IDENTITY,
            plan_sha256=pin,
            actual_exit_codes=[0, 0],
            T0=10,
            T1=11,
        ),
        raw_tool_events=[
            dict(
                complete=True,
                exit_code=0,
                clock_domain="functions.exec.Date.now.UTC-seconds",
                start_seconds=10,
                end_seconds=10.5,
            ),
            dict(
                complete=True,
                exit_code=0,
                clock_domain="functions.exec.Date.now.UTC-seconds",
                start_seconds=10.5,
                end_seconds=11,
            ),
        ],
    )
    raw = wire.canonical(value)
    with pytest.raises(ValueError, match="returned binder release"):
        subject.returned_predecessor(value, raw, None, pin, wire.PUBLIC, role, 12000, None)
    release = dict(
        schema="topolab.staged-input-caller-release.v1",
        execution_identity=wire.IDENTITY,
        root=wire.PUBLIC,
        role=role,
        plan_sha256=pin,
        accepted_sha256=wire.sha(raw),
        native_start_ms=10000,
        native_record_end_ms=11000,
        actual_bind_start_ms=11001,
        actual_bind_end_ms=11500,
    )
    argv = wire.control_argv(wire.PUBLIC, "bind", pin, role)
    request = dict(cmd=wire.literal_command(argv), workdir=str(wire.RUNTIME_REPO))
    packet = dict(
        schema=wire.ACTUAL_SCHEMA,
        author="/root/full60_independent",
        argv=argv,
        request=request,
        responses=[
            dict(
                tool="exec_command",
                arguments=request,
                requested_ms=11001,
                returned_ms=11500,
                result=dict(exit_code=0, output=wire.canonical(value["result"]).decode()),
            )
        ],
    )
    assert subject.returned_predecessor(value, raw, release, pin, wire.PUBLIC, role, 12000, packet)[
        "accepted"
    ]
    with pytest.raises(ValueError, match="outside|response"):
        subject.returned_predecessor(
            value,
            raw,
            dict(release, actual_bind_end_ms=13000),
            pin,
            wire.PUBLIC,
            role,
            12000,
            packet,
        )


@pytest.mark.parametrize("relocated", [False, True])
def test_builder_uses_reviewed_checkout_but_only_fixed_runtime(relocated, tmp_path):
    checkout = REPO
    if relocated:
        checkout = tmp_path / "linux-like-checkout"
        (checkout / "scripts").mkdir(parents=True)
        for name in ("build_staged_input_caller.py", "staged_input_filer.py"):
            (checkout / "scripts" / name).write_bytes((REPO / "scripts" / name).read_bytes())
    subject = load("build_staged_input_caller", checkout)
    wire = subject.wire
    source = (REPO / "scripts/staged_input_actor.mjs").read_bytes()
    config = dict(
        author="independent",
        formal=False,
        root=wire.PUBLIC,
        event_prefix="software-only",
        repo=str(subject.RUNTIME_REPO),
        evidence_root=str(wire.EVIDENCE),
        execution_identity=wire.IDENTITY,
        owner_budget_sha256=wire.BUDGET_SHA,
        registration_certificate_sha="a" * 64,
        registration_finalize_actual_sha="b" * 64,
        formal_registration_certificate_sha="c" * 64,
        formal_registration_finalize_actual_sha="d" * 64,
    )
    artifact = subject.build(config, source, wire.sha(source))
    assert subject.SOURCE_CHECKOUT == checkout
    assert artifact["program_sha256"] == wire.sha(artifact["program"].encode())
    assert "await tools[tool](args)" in artifact["program"]
    with pytest.raises(ValueError, match="runtime/identity/budget"):
        subject.build(
            dict(config, repo=str(tmp_path / "unadmitted-runtime")), source, wire.sha(source)
        )
    if relocated:
        with pytest.raises(ValueError, match="runtime/identity/budget"):
            subject.build(dict(config, repo=str(checkout)), source, wire.sha(source))
    # Execute the generated actual-tool API with injected returns only. SUP1 is
    # retained and no REC is opened, including from a non-production checkout.
    script = r"""
const fs=require('node:fs'),assert=require('node:assert/strict');
const artifact=JSON.parse(fs.readFileSync(0,'utf8'));let stored,printed;
const START=Date.parse('2026-11-22T01:00:00Z');Date.now=()=>START;
const plan={root:artifact.config.root,plan_sha256:'f'.repeat(64),
 execution_identity:artifact.execution_identity,scope:'FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY',
 formal_authority:false,actor_window_seconds:4500,coordination_limit_ms:240000,
 role_order:['independent-public-check','exporter-r0','independent-r0','exporter-r1',
 'independent-r1','shared-closeout'],actor_start_ms:START,whole_start_ms:START,
 whole_end_ms:START+4500000,applicable_deadline_ms:START+4500000};
const calls=[],tools={exec_command:async(args)=>{
 calls.push(args);const cmd=args.cmd.split(' --packet-json ')[0];let exit_code=0,output='{}';
 if(cmd.includes(' prepare-rehearsal '))output=JSON.stringify({
  formal_authority:false,plan_sha256:plan.plan_sha256});
 if(cmd.includes('staged_input_waiter.py'))output=JSON.stringify({source_or_payload_reads:0,plan,proofs:[]});
 if(cmd.includes(' persist')||cmd.includes(' reserve ')||cmd.includes(' activate-release '))
  output=JSON.stringify({
  status:'PAIRED_PERSISTED',path:artifact.config.evidence_root+'/mock.json',sha256:'a'.repeat(64)});
 if(cmd.includes('.py supervise '))exit_code=1;
 return {output,exit_code};
},write_stdin:async()=>{throw Error('no declared session');}};
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
const run=new AsyncFunction('tools','store','text',artifact.program);
run(tools,(key,value)=>{stored=value;},v=>{printed=v;}).then(()=>{
 assert.equal(stored.status,'STOP_RETAINED_NO_RETRY');
 assert.ok(calls.every(x=>x.workdir==='/private/tmp/topolab-staged-input-20261121'));
 const native=calls.filter(x=>/\.py (supervise|record) /.test(x.cmd.split(' --packet-json ')[0]));
 assert.equal(native.length,1);assert.equal(native[0].sandbox_permissions,'require_escalated');
 assert.equal(stored.active.supervise.packet.responses[0].result.exit_code,1);
 assert.equal(printed.own_future_return,'NOT_CLAIMED');console.log('DECLARED_SOFTWARE_PASS');
}).catch(e=>{console.error(e);process.exitCode=1;});
"""
    result = subprocess.run(
        ["node", "-e", script],
        input=json.dumps(artifact),
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "DECLARED_SOFTWARE_PASS"


def test_actual_cli_help_and_namespace_denials_are_source_free(tmp_path):
    for name in ("staged_input_filer.py", "staged_input_waiter.py", "build_staged_input_caller.py"):
        result = subprocess.run(
            [sys.executable, "-I", str(REPO / "scripts" / name), "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0 and "usage:" in result.stdout
    destination = tmp_path / "must-not-exist.json"
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            str(REPO / "scripts/staged_input_filer.py"),
            "persist",
            "--packet-json",
            json.dumps(
                dict(schema="topolab.v2.m2-strict-source-binding.actual-call.v1", author="/root")
            ),
            "--destination",
            str(destination),
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert result.returncode != 0 and "new evidence destination" in result.stderr
    assert not destination.exists()
    missing_sha = subprocess.run(
        [
            sys.executable,
            "-I",
            str(REPO / "scripts/build_staged_input_caller.py"),
            "--emit",
            str(tmp_path / "unadmitted-artifact.json"),
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert missing_sha.returncode != 0 and "external artifact SHA256 required" in missing_sha.stderr


def test_two_author_actual_dispatch_schedule_and_failure_custody():
    result = subprocess.run(
        ["node", "--test", str(REPO / "tests/test_staged_input_caller.mjs")],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("formal", [False, True])
def test_actual_wait_cli_logic_requires_and_replays_returned_packet_pairs(
    tmp_path, formal, monkeypatch
):
    import time

    subject = load("staged_input_waiter")
    wire = subject.wire
    root = tmp_path / "declared-control-fixture"
    root.mkdir(mode=0o700)
    wire.EVIDENCE, wire.BACKUP = tmp_path / "evidence", tmp_path / "backup"
    wire.EVIDENCE.mkdir(mode=0o700)
    wire.BACKUP.mkdir(mode=0o700)
    if formal:
        wire.FORMAL = str(root)
    else:
        wire.PUBLIC = str(root)
    wire.ROOTS = (str(root),)
    # Positive software fixtures stay inside their frozen window on later CI dates.
    # Production wait() still reads the real clock; only this declared test changes it.
    fixture_now_ms = 1795309200000  # 2026-11-22 01:00 UTC
    monkeypatch.setattr(time, "time_ns", lambda: fixture_now_ms * 1000000)
    first = fixture_now_ms - 1000
    plan = dict(
        root=str(root),
        execution_identity=wire.IDENTITY,
        formal_authority=formal,
        scope="SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
        if formal
        else "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY",
        actor_window_seconds=4500,
        role_order=list(wire.ROLES),
        actor_activation_UTC_seconds=first / 1000,
        whole_start_ms=first,
        whole_end_ms=first + 4500000,
        binding={
            "formal_strict23_registration": dict(
                certificate_sha256="c" * 64, finalize_actual_sha256="d" * 64
            ),
            "strict23_registration": dict(
                certificate_sha256="a" * 64, finalize_actual_sha256="b" * 64
            ),
        },
    )
    saved_plan = wire.write_private(root / "plan.json", wire.canonical(plan))
    pin, role = saved_plan["sha256"], wire.ROLES[0]
    if formal:
        argv = [
            wire.PYTHON,
            "-I",
            str(wire.RUNTIME_REPO / "scripts/staged_input_control.py"),
            "activate-formal",
            "--root",
            str(root),
            "--registration-certificate-sha",
            "a" * 64,
            "--registration-finalize-actual-sha",
            "b" * 64,
            "--whole-start-ms",
            str(first),
        ]
        output = dict(
            plan_sha256=pin, scope=plan["scope"], formal_authority=True, source_stat_reads=0
        )
        caller = "/root"
    else:
        output = dict(
            full_role_evidence_accepted=True,
            evidence_complete=True,
            role=role,
            execution_identity=wire.IDENTITY,
            plan_sha256=pin,
            actual_exit_codes=[0, 0],
            T0=(first + 100) / 1000,
            T1=(first + 200) / 1000,
        )
        accepted = dict(
            result=output,
            raw_tool_events=[
                dict(
                    complete=True,
                    exit_code=0,
                    clock_domain="functions.exec.Date.now.UTC-seconds",
                    start_seconds=(first + 100) / 1000,
                    end_seconds=(first + 150) / 1000,
                ),
                dict(
                    complete=True,
                    exit_code=0,
                    clock_domain="functions.exec.Date.now.UTC-seconds",
                    start_seconds=(first + 150) / 1000,
                    end_seconds=(first + 200) / 1000,
                ),
            ],
        )
        accepted_saved = wire.write_private(
            root / (role + "-accepted.json"), wire.canonical(accepted)
        )
        argv = wire.control_argv(str(root), "bind", pin, role)
        caller = "/root/full60_independent"
    wanted = "plan" if formal else role
    original_read = wire.read_private
    probes = []

    def guard_before_initial(path, *args, **kwargs):
        if Path(path).is_relative_to(root):
            probes.append(str(path))
            raise AssertionError("target metadata opened before actual initial return")
        return original_read(path, *args, **kwargs)

    wire.read_private = guard_before_initial
    try:
        assert subject.wait(str(root), wanted, 1)["status"] == "NOT_READY"
        assert probes == []
    finally:
        wire.read_private = original_read
    request = dict(cmd=wire.literal_command(argv), workdir=str(wire.RUNTIME_REPO))
    packet = dict(
        schema=wire.ACTUAL_SCHEMA,
        author=caller,
        argv=argv,
        request=request,
        responses=[
            dict(
                tool="exec_command",
                arguments=request,
                requested_ms=first + 300,
                returned_ms=first + 400,
                result=dict(exit_code=0, output=wire.canonical(output).decode()),
            )
        ],
    )
    paired = wire.publish_pair(wire.EVIDENCE / "declared-return.json", wire.canonical(packet))
    reference = dict(path=paired["path"], sha256=paired["sha256"])
    if formal:
        release = dict(
            schema="topolab.staged-input-activation-release.v1",
            execution_identity=wire.IDENTITY,
            root=str(root),
            plan_sha256=pin,
            whole_start_ms=first,
            activation_actual=reference,
            actual_start_ms=first + 300,
            actual_end_ms=first + 400,
        )
        wire.publish_pair(wire.activation_path(), wire.canonical(release))
    else:
        release = dict(
            schema="topolab.staged-input-caller-release.v1",
            execution_identity=wire.IDENTITY,
            root=str(root),
            plan_sha256=pin,
            role=role,
            accepted_sha256=accepted_saved["sha256"],
            bind_actual=reference,
            actual_bind_start_ms=first + 300,
            actual_bind_end_ms=first + 400,
            native_start_ms=first + 100,
            native_record_end_ms=first + 200,
        )
        wire.publish_pair(wire.release_path(str(root), role), wire.canonical(release))
    if not formal:
        initial_argv = [
            wire.PYTHON,
            "-I",
            str(wire.RUNTIME_REPO / "scripts/staged_input_control.py"),
            "prepare-rehearsal",
            "--root",
            str(root),
            "--registration-certificate-sha",
            "a" * 64,
            "--registration-finalize-actual-sha",
            "b" * 64,
            "--formal-registration-certificate-sha",
            "c" * 64,
            "--formal-registration-finalize-actual-sha",
            "d" * 64,
            "--whole-start-ms",
            str(first),
        ]
        initial_request = dict(
            cmd=wire.literal_command(initial_argv), workdir=str(wire.RUNTIME_REPO)
        )
        initial_output = dict(
            plan_sha256=pin, scope=plan["scope"], formal_authority=False, source_stat_reads=0
        )
        initial_packet = dict(
            schema=wire.ACTUAL_SCHEMA,
            author="/root/full60_independent",
            argv=initial_argv,
            request=initial_request,
            responses=[
                dict(
                    tool="exec_command",
                    arguments=initial_request,
                    requested_ms=first + 1,
                    returned_ms=first + 50,
                    result=dict(exit_code=0, output=wire.canonical(initial_output).decode()),
                )
            ],
        )
        initial_pair = wire.publish_pair(
            wire.EVIDENCE / "declared-prepare.json", wire.canonical(initial_packet)
        )
        wire.activate_release(str(root), pin, initial_pair["path"], initial_pair["sha256"])
    assert subject.wait(str(root), wanted, 1)["plan"]["plan_sha256"] == pin
    # A JSON release alone cannot bless a changed or failing actual return.
    packet["responses"][0]["result"]["exit_code"] = 1
    Path(reference["path"]).write_bytes(wire.canonical(packet))
    with pytest.raises(ValueError, match="SHA"):
        subject.wait(str(root), wanted, 1)


def test_exact_isolated_filer_loads_registration_dependencies_without_dispatch():
    script = """
from pathlib import Path
import types
path=Path(SOURCE_PATH)
module=types.ModuleType('staged_filer_import_fixture');module.__file__=str(path)
exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
control=module.input_profile()
registration=control.load(control.CONTINUATION_CONFIG['registration_module'])
print(control.REGISTERED_IDENTITY+' '+registration.__name__)
""".replace("SOURCE_PATH", repr(str(REPO / "scripts/staged_input_filer.py")))
    result = subprocess.run(
        [sys.executable, "-I", "-c", script], capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == (
        "topolab.v2.p17-m2-registered-source-acquisition.staged-20261121.v1 staged_public_binding"
    )
