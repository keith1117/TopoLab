"""Public fake receipts only; no actual source IO or role launch."""

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "r_control", Path(__file__).parents[1] / "scripts/p17_m2_input_export_control.py"
)
assert SPEC and SPEC.loader
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


def test_isolated_entry_imports_only_stdlib():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-I", str(Path(c.__file__)), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0 and "supervise" in result.stdout


def test_binding_rejects_missing_exit_and_rss(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "ROOT", tmp_path)
    role = "exporter-r0"
    folder = tmp_path / "receipts" / role / role
    folder.mkdir(parents=True)
    record = {
        "exit_code": 0,
        "software_result": "PUBLIC_COMMAND_EXIT_OBSERVED",
        "cleanup": {"group_gone": True},
        "argv": ["public"],
        "native": {"wall_seconds": 0.2},
        "observed_outer_wall_seconds": 0.3,
        "timer_native_exit": {"native": {"rss_bytes": 100}},
        "native_plus_controller_and_sampler_rss_bytes": 1000,
    }
    (folder / "command.json").write_text(json.dumps(record))
    (tmp_path / "receipts" / f"{role}-controller.time").write_text("new")
    monkeypatch.setattr(
        c.native_recording, "native", lambda *_: {"wall_seconds": 0.5, "rss_bytes": 2000}
    )
    (folder / "command.time").write_text("new")
    (folder / "command.log").write_bytes(b"")
    record["helpers"] = []
    (folder / "command.json").write_text(json.dumps(record))
    monkeypatch.setattr(
        c.independent, "audit_native_record", lambda *a, **k: {"inner_empirical_RSS_bytes": 1000}
    )
    plan = {"roles": {role: {"argv": ["public"]}}}
    with pytest.raises(ValueError, match="exit"):
        c.bind(plan, role, None, "a" * 64)
    result = c.bind(plan, role, 0, "a" * 64)
    assert result["plan_sha256"] == "a" * 64 and result["conservative_RSS_bytes"] == 3000
    assert result["charge_before_binder_wall_seconds"] == 10.5
    assert result["status"] == "PENDING_BINDER_NATIVE_EXIT"


def test_missing_source_freeze_refuses(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "ROOT", tmp_path)
    plan = {"source_files": {}, "merged_source": "publichead"}
    raw = c.canonical(plan)
    p = tmp_path / "launch_plan.json"
    p.write_bytes(raw)
    monkeypatch.setattr(
        c.subprocess, "check_output", lambda argv, **_: b"" if "status" in argv else b"publichead\n"
    )
    with pytest.raises(ValueError, match="complete source freeze"):
        c.plan_checked(p, c.digest(raw))


@pytest.mark.skipif(c.sys.platform != "darwin", reason="Darwin native-time public adapter")
def test_supervisor_real_timer_wait4_new_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "ROOT", tmp_path)
    original = c.subprocess.Popen

    def public_child(argv, **kwargs):
        # Substitute only the child payload with a new printing fixture. Keep the
        # real registered outer time helper, os.wait4 and supervisor bookkeeping.
        return original(argv[:5] + ["-I", "-c", "print('new public supervisor fixture')"], **kwargs)

    monkeypatch.setattr(c.subprocess, "Popen", public_child)
    monkeypatch.setattr(c, "bind", lambda *a, **k: {"conservative_RSS_bytes": 1024})
    result = c.supervise(
        {"external_argv": c.external_templates(c.sys.executable)}, "exporter-r0", "a" * 64
    )
    assert result["outer_timer_exit"] == 0 and result["outer_timer_native_rss_bytes"] > 0
    assert result["supervisor_rss_after_verification_bytes"] > 0
    assert result["supervisor_complete_exit"] == "PENDING_EXTERNAL_CALLER_OBSERVATION"
    assert (tmp_path / "receipts/exporter-r0-last-rss.json").is_file()


def test_timeout_closes_registered_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "ROOT", tmp_path)
    role = "exporter-r0"
    folder = tmp_path / "receipts" / role / role
    folder.mkdir(parents=True)
    (folder / "started.json").write_text(
        json.dumps({"role": role, "status": "STARTED", "pid": 98762})
    )
    monkeypatch.setattr(
        c.native_recording,
        "_snapshot",
        lambda *a, **k: ([{"pgid": 98763}], {"native": {"rss_bytes": 1024}}),
    )
    killed = []

    def kill(group, sig):
        if sig == 0:
            raise ProcessLookupError()
        killed.append((group, sig))

    monkeypatch.setattr(c.os, "killpg", kill)
    result = c.stop_registered(role, 98761)
    assert {group for group, sig in killed} == {98761, 98762, 98763}
    assert all(row["group_gone"] for row in result["registered_groups"])
    assert result["complete_exit"] is False  # requires actual parent reap/observer


def test_v2_full_caps_and_exact_outer_call_table():
    assert list(c.CAPS.values()) == [120, 120, 120, 780, 660, 60]
    assert sum(c.CAPS.values()) == 1860
    table = c.external_templates('/new/python')
    assert set(table) == set(c.CAPS)
    for role, calls in table.items():
        assert [argv[3] for argv in calls] == ['supervise', 'finalize']
        assert all(argv[-1] == role for argv in calls)
        assert c.resolved(calls[0], 'a' * 64)[-3] == 'a' * 64


def v2_finalizer_files(tmp_path, monkeypatch):
    from test_p17_m2_input_export_independent import resource_subject

    monkeypatch.setattr(c, 'ROOT', tmp_path)
    monkeypatch.setattr(c.native_recording, '_rss_self', lambda: 4096)
    monkeypatch.setattr(c.sys, 'platform', 'darwin')
    role = 'independent-public-check'
    base = tmp_path / 'receipts'
    folder = base / role / role
    folder.mkdir(parents=True)
    record, profile, helpers = resource_subject()
    record.update(role=role, controller_pid=101)
    (folder / 'command.json').write_bytes(c.canonical(record))
    (folder / 'command.time').write_bytes(profile)
    (folder / 'command.log').write_bytes(b'')
    for name, data in helpers.items():
        (folder / name).write_bytes(data)
    (base / (role + '-controller.time')).write_bytes(profile)
    pending = {
        'execution_identity': c.IDENTITY, 'role': role, 'plan_sha256': 'a' * 64,
        'frozen_FULL_seconds': 120, 'clock_domain': c.CLOCK, 'clock_resolution_seconds': 0.001,
    }
    (base / (role + '-pending.json')).write_bytes(c.canonical(pending))
    (base / (role + '-supervisor.json')).write_bytes(c.canonical({
        'controller_exit': 0, 'supervisor_pid': 102,
        'supervisor_rss_after_verification_bytes': 200,
    }))
    (base / (role + '-last-rss.json')).write_bytes(c.canonical({'rss_bytes': 210}))
    timer = record['timer_native_exit'].copy()
    timer.update(pid=103)
    (base / (role + '-outer-timer-exit.json')).write_bytes(c.canonical({'wait4': timer}))
    return {'roles': {role: {'argv': ['new-public-tool']}}}, role


def test_real_finalizer_wire_remains_pending_until_actual_external_exit(
    tmp_path, monkeypatch, capsys
):
    plan, role = v2_finalizer_files(tmp_path, monkeypatch)
    assert c.finish_record(plan, role, 'a' * 64) == 0
    packet = json.loads(capsys.readouterr().out)
    assert packet['completion']['status'] == 'PENDING_EXTERNAL_EXIT'
    assert packet['completion']['pending_sha256'] == c.digest(
        (tmp_path / 'receipts' / (role + '-pending.json')).read_bytes()
    )
    assert packet['resourceEvidence']['status'] == 'PENDING_EXTERNAL_EXIT'
    assert packet['resourceEvidence']['full_role_evidence_accepted'] is False
    assert packet['resourceEvidence']['RSS_envelope_bytes'] == 190 + 100 + 10 + 210 + 4096
    assert packet['completion']['resource_components'][-1]['samples_bytes'] == [4096, 4096]


def test_failed_finalizer_retains_own_peak_and_nonzero_exit(tmp_path, monkeypatch, capsys):
    plan, role = v2_finalizer_files(tmp_path, monkeypatch)
    (tmp_path / 'receipts' / (role + '-outer-timer-exit.json')).unlink()
    assert c.finish_record(plan, role, 'a' * 64) == 1
    packet = json.loads(capsys.readouterr().out)
    assert packet['failure']['status'] == 'STOP_NO_RETRY'
    assert packet['completion']['resource_components'][0]['samples_bytes'] == [4096, 4096]
    assert packet['resourceEvidence']['status'] == 'STOP_NO_RETRY'


def test_inner_or_legacy_PASS_cannot_open_source_suffix(tmp_path, monkeypatch):
    monkeypatch.setattr(c, 'ROOT', tmp_path)
    (tmp_path / 'receipts').mkdir()
    (tmp_path / 'receipts/independent-public-check-observed.json').write_text(
        json.dumps({'status': 'PASS_R_NATIVE_EXIT'})
    )
    with pytest.raises(ValueError, match='predecessor'):
        c.source_gate({}, 'exporter-r0', 'a' * 64)


def test_backup_excludes_active_shared_files_then_copies_stable_late_records(tmp_path, monkeypatch):
    root = tmp_path / 'new-prefix'
    root.mkdir()
    monkeypatch.setattr(c, 'ROOT', root)
    (root / 'new-view.json').write_bytes(b'{"new":true}\n')
    (root / 'receipts/shared-closeout/live').mkdir(parents=True)
    live = root / 'receipts/shared-closeout/live/command.log'
    live.write_bytes(b'open')
    c.archive_new()
    backup = root.with_name(root.name + '-independent-backup')
    assert not (backup / live.relative_to(root)).exists()
    live.write_bytes(b'closed complete\n')
    c.backup_late(backup)
    result = c.independent.audit_new_backup(root, backup, public_fixture=True)
    assert result['status'] == 'PASS_INDEPENDENT_NEW_BACKUP'
    assert result['member_count'] == 2
    (backup / 'new-view.json').write_bytes(b'changed')
    with pytest.raises(ValueError, match='immutable'):
        c.backup_late(backup)


def test_large_backup_inventory_stays_on_disk_with_bounded_stdout_summary(tmp_path, monkeypatch):
    root = tmp_path / 'new-prefix'
    root.mkdir()
    monkeypatch.setattr(c, 'ROOT', root)
    for i in range(350):
        (root / f'new-{i:04d}.json').write_bytes(b'{"new":true}\n')
    c.archive_new()
    summary = c.backup_evidence(public_fixture=True)
    raw = (root / 'backup_manifest.json').read_bytes()
    assert len(raw) > 40000
    assert len(c.canonical(summary)) < 1024
    assert summary['manifest_sha256'] == c.digest(raw)
    assert summary['member_count'] == 351
    assert json.loads(raw)['member_count'] == 350
    backup = root.with_name(root.name + '-independent-backup')
    assert (backup / 'backup_manifest.json').read_bytes() == raw


@pytest.mark.skipif(shutil.which('node') is None, reason='existing Node runtime unavailable')
@pytest.mark.parametrize('fault', ['none', 'exit', 'truncated'])
def test_frozen_dispatcher_serial_once_stop_and_partial_tool_output(fault):
    # NEW synthetic tool replies only. No native role, actual data root or delay.
    command = r'''
const fs = require('fs'), vm = require('vm');
const state = new Map(), emitted = [], calls = [];
let milliseconds = 1000000;
const identity = 'topolab.v2.p17-m2-input-export-preparation.v2';
const roles = ['independent-public-check', 'exporter-r0', 'independent-r0',
  'exporter-r1', 'independent-r1', 'shared-closeout'];
const caps = [120,120,120,780,660,60];
const context = {execution_identity:identity, plan_sha256:'a'.repeat(64),
  repository:'/new/public/repo', thread_environment:{OMP_NUM_THREADS:'1'},
  actor_deadlines_UTC:{exporter:'2026-10-19T07:33:59Z',
    independent:'2026-10-19T06:34:17Z'},
  FULL_caps_seconds:Object.fromEntries(roles.map((r,i)=>[r,caps[i]])),
  external_argv:Object.fromEntries(roles.map(r=>[r,[[r,'supervise'],[r,'finalize']]]))};
const fault = process.argv[2];
const sandbox = {module:{exports:{}},
  load:k=>state.get(k), store:(k,v)=>state.set(k,v), text:v=>emitted.push(v),
  Date:{now:()=>milliseconds+=100,parse:Date.parse},
  tools:{exec_command:async args=>{
    calls.push(args);
    const role = state.get('r2-active-role');
    const p = {execution_identity:identity, role, plan_sha256:context.plan_sha256,
      frozen_FULL_seconds:context.FULL_caps_seconds[role],
      clock_domain:'functions.exec.Date.now.UTC-seconds', clock_resolution_seconds:0.001,
      external_argv:context.external_argv[role]};
    const done = args.cmd.includes("'finalize'");
    const completion = {...p,status:'PENDING_EXTERNAL_EXIT',pending_sha256:'b'.repeat(64),
      cleanup:{group_gone:true}};
    const evidence = {...completion,full_role_evidence_accepted:false,
      RSS_envelope_bytes:1024,RSS_components_bytes:{new_public:1024},
      inner_minimum_charge_seconds:11};
    const output = done && fault==='truncated' ? '{"incomplete":' : JSON.stringify(done
      ? {pending:p,completion,resourceEvidence:evidence}
      : {pending:p,pending_sha256:'b'.repeat(64)});
    return {output,exit_code:done && fault==='exit'?1:0,wall_time_seconds:0.01};
  }}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),sandbox);
const dispatch = sandbox.module.exports.dispatchRoleV2;
async function rejected(role,ctx=context) {
  const before=calls.length;
  try { await dispatch(ctx,role); throw new Error('guard allowed role'); }
  catch(e) { if(e.message==='guard allowed role') throw e; }
  if(calls.length!==before) throw new Error('guard dispatched a tool');
}
(async()=>{
  await rejected('extra',{...context,external_argv:{...context.external_argv,extra:[]}});
  milliseconds=Date.parse('2026-10-19T06:34:17Z')-caps[0]*1000+1;
  await rejected(roles[0]);
  milliseconds=1000000;
  const first = await dispatch(context,roles[0]);
  await rejected(roles[0]);
  await rejected(roles[2]);
  if(fault==='none') {
    if(first.terminal.status!=='PASS_R_V2_FULL_ROLE') throw new Error('valid role refused');
    await dispatch(context,roles[1]);
    if(!calls[2].cmd.includes('TOPOLAB_R2_PREVIOUS_TOOL_RECORDS=')) throw new Error('no replay');
    await rejected(roles[1]);
  } else {
    if(first.terminal.status!=='STOP_NO_RETRY') throw new Error('bad role passed');
    await rejected(roles[1]);
    if(fault==='truncated' && !first.events[1].unparsed_output) throw new Error('lost prefix');
  }
  process.stdout.write(JSON.stringify({calls:calls.length,status:first.terminal.status,
    events:first.events.length,actual:first.terminal.actual_exit_codes}));
})().catch(e=>{process.stderr.write(e.stack);process.exitCode=1;});
'''
    script = Path(__file__).parents[1] / 'scripts/p17_m2_input_export_dispatch.js'
    result = subprocess.run(
        ['node', '-e', command, str(script), fault], capture_output=True, text=True, check=False
    )
    assert result.returncode == 0, result.stderr
    checked = json.loads(result.stdout)
    assert checked['calls'] == (4 if fault == 'none' else 2)
    assert checked['events'] == 2
    assert checked['actual'] == ([0, 1] if fault == 'exit' else [0, 0])
