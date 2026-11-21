"""New fixed caller profile and resource gate; no original or named-role IO."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
NEW_INPUT = "topolab.v2.p17-m2-registered-source-acquisition.20261121.v1"


def load(name):
    path = REPO / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_new_input_resource_literal_passes_only_to_finite_cap_refusal(tmp_path):
    load("p17_m2_homotopy")
    subject = load("p17_m2_resource_control")
    target = tmp_path / "not-created"
    argv = [
        sys.executable,
        "-I",
        str(REPO / "scripts/input_control_20261121.py"),
        "payload",
        "--root",
        "/private/tmp/topolab-public-source-acquisition-20261121-a1",
        "--plan-sha",
        "a" * 64,
        "--role",
        "exporter-r0",
    ]
    with pytest.raises(ValueError, match="finite registered public command/caps"):
        subject.invoke(
            target,
            "exporter-r0",
            argv,
            timeout=0,
            measurement_scope="FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY",
            measurement_execution_identity=NEW_INPUT,
        )
    assert not target.exists()


def test_new_caller_uses_fixed_new_qualification_and_legacy_default_is_retained():
    source = r"""
import {createActualBoundary,qualification20261121} from BOUNDARY;
import {launchGate} from COHORT;
const now=1795242000000;
const roles=['independent-public-check','exporter-r0','independent-r0',
 'exporter-r1','independent-r1','shared-closeout'];
const plan={root:'/private/tmp/topolab-public-source-acquisition-20261121-a1',
 plan_sha256:'a'.repeat(64),execution_identity:'topolab.v2.p17-m2-registered-source-acquisition.20261121.v1',
 scope:'FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY',formal_authority:false,actor_window_seconds:4500,
 coordination_limit_ms:240000,role_order:roles,actor_start_ms:now,whole_start_ms:now,
 whole_end_ms:now+4500000,applicable_deadline_ms:now+4500000};
launchGate(plan,roles[0],[],now);
let denied=false;
try{launchGate({...plan,execution_identity:'topolab.v2.p17-m2-registered-source-acquisition.20261116.v1'},roles[0],[],now);}catch{denied=true;}
if(!denied)throw Error('new root selected old identity');
const gate={public:{certificate_sha256:'b'.repeat(64),finalize_actual_sha256:'c'.repeat(64)},
 formal:{certificate_sha256:'d'.repeat(64),finalize_actual_sha256:'e'.repeat(64)}};
const q=qualification20261121({author:'producer',formal:false,root:plan.root,
 event_prefix:'public-root-a1',metadata_gate:gate});
const boundary=createActualBoundary(()=>{throw Error('no dispatch permitted');},q);
console.log(JSON.stringify({repo:q.repo,evidence_root:q.evidence_root,
 has_plan:typeof boundary.plan==='function',denied}));
""".replace(
        "BOUNDARY", json.dumps((REPO / "scripts/full60_input_actual_boundary.mjs").as_uri())
    ).replace("COHORT", json.dumps((REPO / "scripts/full60_input_cohort.mjs").as_uri()))
    result = subprocess.run(
        ["node", "--input-type=module", "-e", source], capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {
        "repo": "/private/tmp/topolab-meta-input-20261121",
        "evidence_root": (
            "/Users/keith1117/Documents/TopoLab-data/metadata-input-acceptance-20261121"
        ),
        "has_plan": True,
        "denied": True,
    }


def test_new_prepare_requires_formal_metadata_and_transmits_both_pins():
    script = r"""
import {createActualBoundary,qualification20261121} from BOUNDARY;
let clock=1795242000000;Date.now=()=>clock;
const gate={public:{certificate_sha256:'b'.repeat(64),finalize_actual_sha256:'c'.repeat(64)},
 formal:{certificate_sha256:'d'.repeat(64),finalize_actual_sha256:'e'.repeat(64)}};
const root='/private/tmp/topolab-public-source-acquisition-20261121-a1';
let denied=false,calls=[];
try{qualification20261121({author:'independent',formal:false,root,event_prefix:'x',
 metadata_gate:{public:gate.public}});}catch{denied=true;}
if(!denied)throw Error('formal metadata missing gate accepted');
const config=qualification20261121({author:'independent',formal:false,root,
 event_prefix:'declared-pure-case',metadata_gate:gate});
const plan={root,plan_sha256:'a'.repeat(64),whole_start_ms:clock,whole_end_ms:clock+4500000};
const dispatch=async(tool,args)=>{
 const requested_ms=clock;let output=JSON.stringify({formal_authority:false,
 plan_sha256:plan.plan_sha256});calls.push(args.cmd);
 if(args.cmd.includes('await_input_receipt_20261121.py'))
  output=JSON.stringify({source_or_payload_reads:0,plan,proofs:[]});
 return {tool,arguments:args,requested_ms,returned_ms:clock,result:{exit_code:0,output}};
};
await createActualBoundary(dispatch,config).prepare();
const command=calls[0];
if(!command.includes('--formal-registration-certificate-sha '+ 'd'.repeat(64)))
 throw Error('formal certificate omitted');
if(!command.includes('--formal-registration-finalize-actual-sha '+'e'.repeat(64)))
 throw Error('formal finalizer omitted');
if(command.indexOf('--formal-registration-finalize-actual-sha')>
 command.indexOf('--whole-start-ms'))throw Error('formal suffix order differs');
console.log(JSON.stringify({denied,calls:calls.length,original_start:true}));
""".replace("BOUNDARY", json.dumps((REPO / "scripts/full60_input_actual_boundary.mjs").as_uri()))
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script], capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == {"denied": True, "calls": 2, "original_start": True}


def test_frozen_program_binds_sources_and_preserves_tool_approval_fields():
    subject = load("build_input_caller_20261121")
    sources = {name: (REPO / "scripts" / name).read_bytes() for name in subject.SOURCE_FILES}
    pins = {name: subject.sha(raw) for name, raw in sources.items()}
    gate = {
        "public": {"certificate_sha256": "a" * 64, "finalize_actual_sha256": "b" * 64},
        "formal": {"certificate_sha256": "c" * 64, "finalize_actual_sha256": "d" * 64},
    }
    config = {
        "author": "producer",
        "formal": False,
        "root": "/private/tmp/topolab-public-source-acquisition-20261121-a1",
        "event_prefix": "declared-software-only",
        "metadata_gate": gate,
        "execution_identity": NEW_INPUT,
        "repo": str(REPO),
        "evidence_root": str(subject.EVIDENCE),
        "owner_budget_sha256": subject.BUDGET_SHA,
    }
    packet = subject.build(config, sources, pins)
    assert packet["program_sha256"] == subject.sha(packet["program"].encode())
    assert "await tools[tool](args)" in packet["program"]
    assert "sandbox_permissions" in packet["program"]
    changed = dict(sources)
    changed[subject.SOURCE_FILES[0]] += b"\n"
    with pytest.raises(ValueError, match="source buffers"):
        subject.build(config, changed, pins)


def test_two_author_scheduling_effects_and_failure_state_machine():
    result = subprocess.run(
        ["node", "--test", str(REPO / "tests/test_input_caller_20261121.mjs")],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def isolated_functions(filename, names):
    """Load pure courier seams without activating its runtime bootstrap."""
    import ast

    tree = ast.parse((REPO / "scripts" / filename).read_text())
    selected = ast.Module(
        body=[n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names],
        type_ignores=[],
    )
    namespace = {}
    exec(compile(selected, filename, "exec"), namespace)
    return namespace


def test_new_terminal_retains_nonzero_and_checks_every_owned_poll():
    import copy
    from types import SimpleNamespace

    api = isolated_functions("file_input_event_20261121.py", {"need", "exact_terminal"})
    argv = ["declared-python", "-I", "declared-entry", "supervise"]
    request = {"cmd": "declared-literal", "workdir": str(REPO), "max_output_tokens": 4000}
    recovery = SimpleNamespace(
        REPO=REPO, load=lambda _: SimpleNamespace(literal_command=lambda _: "declared-literal")
    )
    rows = [
        {
            "tool": "exec_command",
            "arguments": request,
            "requested_ms": 10,
            "returned_ms": 11,
            "result": {"output": "original-start", "session_id": 7},
        },
        {
            "tool": "write_stdin",
            "arguments": {"session_id": 7, "chars": "", "yield_time_ms": 5000},
            "requested_ms": 12,
            "returned_ms": 13,
            "result": {"output": "original-error", "exit_code": 1},
        },
    ]
    packet = dict(
        schema="topolab.v2.m2-strict-source-binding.actual-call.v1",
        author="/root",
        argv=argv,
        request=request,
        responses=rows,
    )
    before = copy.deepcopy(packet)
    assert api["exact_terminal"](packet, argv, "/root", recovery) == (10, 13)
    assert packet == before and packet["responses"][-1]["result"]["exit_code"] == 1
    for mutate, reason in [
        (lambda p: p["responses"][1]["arguments"].update(session_id=8), "unowned"),
        (lambda p: p["responses"][1]["arguments"].update(chars="input"), "unowned"),
        (lambda p: p["responses"][1]["arguments"].update(yield_time_ms=True), "unowned"),
        (lambda p: p["responses"][1].update(requested_ms=9), "clocks"),
        (lambda p: p["responses"][1]["result"].update(session_id=7), "terminal"),
        (
            lambda p: p["responses"][0]["result"].update(output="Warning: truncated output"),
            "truncated",
        ),
    ]:
        broken = copy.deepcopy(packet)
        mutate(broken)
        with pytest.raises(ValueError, match=reason):
            api["exact_terminal"](broken, argv, "/root", recovery)


def test_new_caller_stop_retains_first_full_failure_and_signals_peer(tmp_path):
    import hashlib
    import os
    from types import SimpleNamespace

    api = isolated_functions("file_input_event_20261121.py", {"need", "canonical", "persist"})
    root = "/private/tmp/declared-software-input-only"
    stop = tmp_path / "input-public-a1-caller-STOP.json"

    def read(path):
        raw = Path(path).read_bytes()
        return json.loads(raw), raw

    api.update(
        os=os,
        Path=Path,
        hashlib=hashlib,
        json=json,
        EVIDENCE=tmp_path,
        INPUT_ID=NEW_INPUT,
        signal=SimpleNamespace(
            ROOTS=(root,), PUBLIC=root, caller_stop_path=lambda _: stop, read_metadata=read
        ),
    )
    failure = dict(
        schema="topolab.m2-acquisition-caller-failure.v1",
        author="/root",
        execution_identity=NEW_INPUT,
        caller_root=root,
        caller_failure={"first": "STOP"},
    )
    first = api["persist"](failure, tmp_path / "root-failure.json")
    first_stop = stop.read_bytes()
    notice = json.loads(first_stop)
    assert notice["original_failure"] == first
    assert notice["root"] == root and notice["source_or_payload_reads"] == 0
    peer = dict(failure, author="/root/full60_independent", caller_failure={"second": "peer STOP"})
    second = api["persist"](peer, tmp_path / "independent-failure.json")
    assert Path(second["path"]).exists() and stop.read_bytes() == first_stop
    assert (stop.stat().st_mode & 0o777) == 0o600
    with pytest.raises(FileExistsError):
        api["persist"](failure, tmp_path / "root-failure.json")


def test_generated_program_executes_real_dispatch_api_shape_with_injected_tools():
    subject = load("build_input_caller_20261121")
    sources = {name: (REPO / "scripts" / name).read_bytes() for name in subject.SOURCE_FILES}
    config = {
        "author": "independent",
        "formal": False,
        "root": "/private/tmp/topolab-public-source-acquisition-20261121-a1",
        "event_prefix": "declared-generated-dispatch",
        "execution_identity": NEW_INPUT,
        "repo": str(REPO),
        "evidence_root": str(subject.EVIDENCE),
        "owner_budget_sha256": subject.BUDGET_SHA,
        "metadata_gate": {
            "public": {"certificate_sha256": "a" * 64, "finalize_actual_sha256": "b" * 64},
            "formal": {"certificate_sha256": "c" * 64, "finalize_actual_sha256": "d" * 64},
        },
    }
    packet = subject.build(
        config, sources, {name: subject.sha(raw) for name, raw in sources.items()}
    )
    script = r"""
const fs=require('node:fs'),assert=require('node:assert/strict');
const packet=JSON.parse(fs.readFileSync(0,'utf8')),calls=[];
const START=1795242000000;Date.now=()=>START;
const plan={root:packet.config.root,plan_sha256:'f'.repeat(64),
 execution_identity:packet.execution_identity,scope:'FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY',
 formal_authority:false,actor_window_seconds:4500,coordination_limit_ms:240000,
 role_order:['independent-public-check','exporter-r0','independent-r0','exporter-r1',
 'independent-r1','shared-closeout'],actor_start_ms:START,whole_start_ms:START,
 whole_end_ms:START+4500000,applicable_deadline_ms:START+4500000};
let stored,printed;
const tools={exec_command:async(args)=>{
 calls.push(args);const cmd=args.cmd.split(' --packet-json ')[0];let output='{}',exit_code=0;
 if(cmd.includes(' prepare-rehearsal '))output=JSON.stringify({
  formal_authority:false,plan_sha256:plan.plan_sha256});
 if(cmd.includes('await_input_receipt_20261121.py'))output=JSON.stringify({source_or_payload_reads:0,plan,proofs:[]});
 if(cmd.includes(' persist'))output=JSON.stringify({
  path:packet.config.evidence_root+'/mock-only.json',sha256:'a'.repeat(64)});
 if(cmd.includes('.py supervise '))exit_code=1;
 return {output,exit_code};
},write_stdin:async()=>{throw Error('no live fixture session');}};
const AsyncFunction=Object.getPrototypeOf(async function(){}).constructor;
const run=new AsyncFunction('tools','store','text',packet.program);
run(tools,(key,value)=>{stored=value;},value=>{printed=value;}).then(()=>{
 assert.equal(stored.result.status,'STOP_RETAINED_NO_RETRY');
 const native=calls.filter(x=>/\.py (supervise|record) /.test(x.cmd.split(' --packet-json ')[0]));
 assert.equal(native.length,2);assert.ok(native.every(x=>x.sandbox_permissions==='require_escalated'&&x.prefix_rule===undefined));
 assert.equal(stored.packets['independent-public-check-supervise'].packet.responses[0].result.exit_code,1);
 assert.equal(printed.final_acceptance,'REQUIRES_SEPARATE_ACTUAL_RETURN_AND_INPUT_AUDIT');
 console.log(JSON.stringify({status:stored.result.status,original_rows:stored.raw.length,native:native.length}));
}).catch(error=>{console.error(error);process.exitCode=1;});
"""
    result = subprocess.run(
        ["node", "-e", script], input=json.dumps(packet), capture_output=True, text=True, timeout=5
    )
    assert result.returncode == 0, result.stdout + result.stderr
    value = json.loads(result.stdout)
    assert value["status"] == "STOP_RETAINED_NO_RETRY" and value["native"] == 2


def test_sup_pending_must_match_new_source_established_role_plan_and_clocks():
    import copy
    from decimal import Decimal
    from types import SimpleNamespace

    api = isolated_functions("file_input_event_20261121.py", {"need", "matching_pending"})
    api.update(
        INPUT_ID=NEW_INPUT,
        Path=Path,
        signal=SimpleNamespace(
            legacy=SimpleNamespace(milliseconds=lambda seconds: int(Decimal(str(seconds)) * 1000))
        ),
    )
    root = "/private/tmp/declared-software-pending-only"
    role, pin = "independent-r1", "a" * 64
    def argv(root, mode, plan_sha, role):
        return [str(root), mode, plan_sha, role]

    control = SimpleNamespace(argv_for=argv, base=lambda: SimpleNamespace(CAPS={role: 1200}))
    plan = dict(
        actor_activation_UTC_seconds=Decimal("1795242000.123"),
        actor_window_seconds=4500,
        actor_deadlines_UTC={"independent": "2026-11-21T08:00:00.123Z"},
        whole_start_ms=1795242000123,
        whole_end_ms=1795246500123,
    )
    pending = dict(
        plan,
        actor_activation_UTC_seconds=1795242000.123,
        execution_identity=NEW_INPUT,
        role=role,
        plan_sha256=pin,
        status="PENDING_BEFORE_DISPATCH",
        frozen_FULL_seconds=1200,
        clock_domain="functions.exec.Date.now.UTC-seconds",
        clock_resolution_seconds=0.001,
        external_argv=[argv(root, mode, pin, role) for mode in ("supervise", "record")],
    )
    api["matching_pending"](pending, plan, root, pin, role, control)
    for key, value in [
        ("execution_identity", "old"),
        ("role", "independent-r0"),
        ("plan_sha256", "b" * 64),
        ("status", "AFTER_DISPATCH"),
        ("frozen_FULL_seconds", 300),
        ("whole_start_ms", 1795242000124),
        ("actor_activation_UTC_seconds", 1795242000.124),
        ("external_argv", [argv(root, "record", pin, role)]),
    ]:
        wrong = copy.deepcopy(pending)
        wrong[key] = value
        with pytest.raises(ValueError, match="pending"):
            api["matching_pending"](wrong, plan, root, pin, role, control)
