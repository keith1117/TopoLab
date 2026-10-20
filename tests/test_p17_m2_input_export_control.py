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


def actor_fields():
    return {"actor_activation_UTC_seconds": 1000.0, "actor_window_seconds": 2700,
            "actor_deadlines_UTC": {"exporter": "1970-01-01T01:01:40.000Z",
                                    "independent": "1970-01-01T01:01:40.000Z"}}


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


@pytest.mark.parametrize("fault", [None, "head", "branch", "event", "job", "future"])
def test_readiness_plan_requires_exact_main_ci_and_one_fresh_window(tmp_path, monkeypatch, fault):
    # Entirely NEW public files. Damaged readiness cannot create a plan/root.
    repo = tmp_path / "public-repo"
    repo.mkdir()
    (repo / "source.txt").write_bytes(b"original public source\n")
    root = tmp_path / "outputs" / "new-preparation"
    root.parent.mkdir()
    monkeypatch.setattr(c, "REPO", repo)
    monkeypatch.setattr(c, "ROOT", root)
    monkeypatch.setattr(c, "SOURCE_FILES", {"source.txt"})
    monkeypatch.setattr(c.sys, "platform", "darwin")
    monkeypatch.setattr(c.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(c.time, "time", lambda: 1001.0)
    for name, value in c.native_recording.ENVIRONMENT.items():
        monkeypatch.setenv(name, value)
    head = "a" * 40

    def git(argv, **_):
        return b"" if "status" in argv else (head + "\n").encode()

    monkeypatch.setattr(c.subprocess, "check_output", git)
    ci = {"headSha": head, "headBranch": "main", "event": "push", "databaseId": 1,
          "url": "https://github.com/keith1117/TopoLab/actions/runs/1",
          "status": "completed", "conclusion": "success", "jobs": [
              {"name": name, "status": "completed", "conclusion": "success"}
              for name in ("quality", "frontend", "clean-linux-smoke", "i1-native-software")]}
    if fault == "head":
        ci["headSha"] = "b" * 40
    if fault == "branch":
        ci["headBranch"] = "feature"
    if fault == "event":
        ci["event"] = "pull_request"
    if fault == "job":
        ci["jobs"][0]["conclusion"] = "skipped"
    evidence = tmp_path / "actual-ci.json"
    evidence.write_bytes(c.canonical(ci))
    if fault:
        with pytest.raises(ValueError, match="CI|window"):
            c.create_plan(1002.0 if fault == "future" else 1000.0, evidence)
        assert not root.exists()
        return
    context = c.create_plan(1000.0, evidence)
    assert context["actor_deadlines_UTC"] == actor_fields()["actor_deadlines_UTC"]
    assert set(context["roles"]) == set(c.CAPS) and len(context["roles"]) == 6
    plan_raw = (root / "launch_plan.json").read_bytes()
    assert context["plan_sha256"] == c.digest(plan_raw)
    assert all("<PLAN_SHA256>" not in word for calls in context["external_argv"].values()
               for argv in calls for word in argv)
    assert json.loads(plan_raw)["main_CI_raw_sha256"] == c.digest(evidence.read_bytes())
    with pytest.raises(ValueError, match="exclusive NEW"):
        c.create_plan(1000.0, evidence)


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
        {"external_argv": c.external_templates(c.sys.executable), **actor_fields()},
        "exporter-r0", "a" * 64
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


@pytest.mark.skipif(c.sys.platform != 'darwin', reason='selected M2 native fixture only')
@pytest.mark.parametrize('code', [0, 1])
def test_supervisor_binding_error_never_replaces_observed_payload_exit(
    tmp_path, monkeypatch, code
):
    monkeypatch.setattr(c, 'ROOT', tmp_path)
    monkeypatch.setattr(c, 'CAPS', {'public-fixture': 120})
    original = c.subprocess.Popen

    def fixture(argv, **kwargs):
        return original(argv[:5] + ['-I', '-c', f'raise SystemExit({code})'], **kwargs)

    def bad_bind(*args, **kwargs):
        raise OSError('new public missing helper binding')

    monkeypatch.setattr(c.subprocess, 'Popen', fixture)
    monkeypatch.setattr(c, 'bind', bad_bind)
    result = c.supervise({
        'execution_identity': c.F_IDENTITY, 'fixture_exit': code,
        'external_argv': {'public-fixture': [['new-public-supervise'], ['new-public-finalize']]},
        **actor_fields(),
    }, 'public-fixture', 'a' * 64)
    assert result['outer_timer_exit'] == code
    assert result['outer_timer_native_rss_bytes'] > 0
    assert result['status'] == 'STOP_NO_RETRY'
    assert result['secondary_failures'][0]['reason'] == 'new public missing helper binding'
    assert result.get('primary_failure') == (
        {'stage': 'payload/controller', 'type': 'ExitCode', 'reason': '1'} if code else None)


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
        **actor_fields(),
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
    return {'roles': {role: {'argv': ['new-public-tool']}}, **actor_fields()}, role


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


def test_missing_supervisor_keeps_wait4_and_native_facts(tmp_path, monkeypatch, capsys):
    plan, role = v2_finalizer_files(tmp_path, monkeypatch)
    (tmp_path / 'receipts' / (role + '-supervisor.json')).unlink()
    assert c.finish_record(plan, role, 'a' * 64) == 1
    packet = json.loads(capsys.readouterr().out)
    assert packet['completion']['available_outer_records']['outer-timer-exit']['wait4']
    assert packet['resourceEvidence']['RSS_components_bytes']
    assert packet['resourceEvidence']['evidence_complete'] is False
    assert packet['secondary_failures'][0]['stage'] == 'supervisor'


@pytest.mark.parametrize('value', [[], None, 1, {'secondary_failures': None}])
def test_malformed_supervisor_still_emits_bounded_failure_packet(
    tmp_path, monkeypatch, capsys, value
):
    plan, role = v2_finalizer_files(tmp_path, monkeypatch)
    (tmp_path / 'receipts' / (role + '-supervisor.json')).write_bytes(c.canonical(value))
    assert c.finish_record(plan, role, 'a' * 64) == 1
    packet = json.loads(capsys.readouterr().out)
    assert packet['completion']['available_outer_records']['outer-timer-exit']['wait4']
    assert packet['completion']['resource_components'][0]['samples_bytes'] == [4096, 4096]
    assert packet['resourceEvidence']['evidence_complete'] is False
    assert packet['secondary_failures'][0]['stage'] == 'supervisor'


@pytest.mark.parametrize('value', [[], None, 1])
def test_malformed_wait4_keeps_other_components(tmp_path, monkeypatch, capsys, value):
    plan, role = v2_finalizer_files(tmp_path, monkeypatch)
    (tmp_path / 'receipts' / (role + '-outer-timer-exit.json')).write_bytes(
        c.canonical({'wait4': value}))
    assert c.finish_record(plan, role, 'a' * 64) == 1
    packet = json.loads(capsys.readouterr().out)
    assert packet['completion']['available_outer_records']['supervisor']
    assert packet['resourceEvidence']['evidence_complete'] is False
    assert packet['secondary_failures'][0]['stage'] == 'outer-timer-exit'


def test_serializer_write_failure_preserves_original_and_secondary(tmp_path, monkeypatch, capsys):
    plan, role = v2_finalizer_files(tmp_path, monkeypatch)
    path = tmp_path / 'receipts' / (role + '-supervisor.json')
    supervisor = json.loads(path.read_bytes())
    primary = {'stage': 'new-public-source', 'type': 'ValueError', 'reason': 'identity changed'}
    supervisor['primary_failure'] = primary
    path.write_bytes(c.canonical(supervisor))
    original = c.write

    def fail_completion(path, value):
        if path.name.endswith('-completion.json'):
            raise OSError('new public serializer write failure')
        return original(path, value)

    monkeypatch.setattr(c, 'write', fail_completion)
    assert c.finish_record(plan, role, 'a' * 64) == 1
    packet = json.loads(capsys.readouterr().out)
    assert packet['primary_failure'] == primary
    assert packet['completion']['primary_failure'] == primary
    assert packet['secondary_failures'][-1]['stage'] == 'completion'
    assert 'serializer write failure' in packet['secondary_failures'][-1]['reason']
    assert packet['resourceEvidence']['RSS_envelope_bytes'] > 0
    assert packet['resourceEvidence']['evidence_complete'] is True
    assert packet['completion']['status'] == 'FAILED_INTERNAL_COMPLETION'
    events = [{
        'event_id': f'new-public-event-{i}', 'clock_domain': c.CLOCK,
        'start_seconds': 1000.0 + i * 2, 'end_seconds': 1001.0 + i * 2,
        'wall_seconds': 1.0, 'argv': [f'new-public-command-{i}'],
        'complete': True, 'exit_code': i,
    } for i in range(2)]
    py = c.independent.audit_full_role_v2(
        packet['pending'], packet['completion'], raw_tool_events=events,
        expected_role=role, expected_plan_sha256='a' * 64,
        **c.resource_inputs(plan, role, 'a' * 64),
    )
    assert py['status'] == 'STOP_NO_RETRY' and py['evidence_complete'] is False
    assert py['whole_wall_seconds'] == 3.0
    if shutil.which('node'):
        script = Path(c.__file__).with_name('p17_m2_input_export_dispatch.js')
        command = (
            "const fs=require('fs');const {finishExternal}=require(process.argv[1]);"
            "console.log(JSON.stringify(finishExternal(...JSON.parse(fs.readFileSync(0,'utf8')))))"
        )
        observed = subprocess.run(
            ['node', '-e', command, str(script)], input=json.dumps([
                packet['pending'], packet['completion'], events, packet['resourceEvidence'],
                packet['completion']['pending_sha256'],
            ]), text=True, capture_output=True, check=True,
        )
        js = json.loads(observed.stdout)
        for key in ('status', 'evidence_complete', 'whole_wall_seconds', 'RSS_envelope_bytes',
                    'actual_exit_codes', 'primary_failure', 'secondary_failures'):
            assert js[key] == py[key], key


def test_missing_helper_preserves_other_new_native_inventory(tmp_path, monkeypatch, capsys):
    plan, role = v2_finalizer_files(tmp_path, monkeypatch)
    (tmp_path / 'receipts' / role / role / 'sampler-0.time').unlink()
    assert c.finish_record(plan, role, 'a' * 64) == 1
    packet = json.loads(capsys.readouterr().out)
    inventory = packet['completion']['available_native_evidence']
    assert f'receipts/{role}-controller.time' in inventory
    assert f'receipts/{role}/{role}/command.time' in inventory
    assert f'receipts/{role}/{role}/command.log' in inventory
    assert packet['resourceEvidence']['evidence_complete'] is False


@pytest.mark.parametrize('path', [
    '/Users/keith1117/Documents/TopoLab-data/p17-m2-input-export-preparation-v3',
    '/private/tmp/../outside', '/tmp/public-fixture',
])
def test_F_entry_rejects_old_or_nonliteral_root_before_any_query(path, monkeypatch):
    monkeypatch.setattr(c.os, 'open', lambda *a, **k: pytest.fail('must reject before open'))
    with pytest.raises(ValueError, match='literal NEW'):
        c.public_entry('public-finalize', Path(path), 1)


@pytest.mark.skipif(c.sys.platform != 'darwin', reason='selected M2 native fixture only')
@pytest.mark.parametrize('code', [0, 1])
def test_F_real_native_failure_exit_is_measured_without_domain_upgrade(code):
    import tempfile

    with tempfile.TemporaryDirectory(prefix='topolab-new-F-', dir='/private/tmp') as parent:
        root = Path(parent) / 'new-public-output'
        outputs = []
        setup = subprocess.run(
            [c.sys.executable, '-I', c.__file__, 'public-plan', '--public-root', str(root),
             '--fixture-exit', str(code)], capture_output=True, text=True, check=False,
            timeout=120,
        )
        assert setup.returncode == 0, setup.stderr
        for mode in ('public-supervise', 'public-finalize'):
            process = subprocess.run(
                [c.sys.executable, '-I', c.__file__, mode, '--public-root', str(root),
                 '--fixture-exit', str(code)], capture_output=True, text=True, check=False,
                timeout=120,
            )
            assert process.returncode == (code if mode == 'public-supervise' else 0), (
                process.stdout, process.stderr)
            outputs.append(json.loads(process.stdout))
        packet = outputs[-1]
        assert packet['resourceEvidence']['status'] == 'PENDING_EXTERNAL_EXIT'
        assert packet['resourceEvidence']['evidence_complete'] is True
        assert 0 < packet['resourceEvidence']['RSS_envelope_bytes'] <= 4294967296
        assert packet['resourceEvidence']['inner_actual_exit_code'] == code
        assert packet['completion']['cleanup']['group_gone'] is True
        assert packet['completion']['domain_status'] == ('STOP' if code else 'UNKNOWN')
        assert packet['completion']['primary_failure'] is not None if code else (
            packet['completion']['primary_failure'] is None)


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
const identity = 'topolab.v2.p17-m2-input-export-preparation.v3';
const roles = ['independent-public-check', 'exporter-r0', 'independent-r0',
  'exporter-r1', 'independent-r1', 'shared-closeout'];
const caps = [120,120,120,780,660,60];
const context = {execution_identity:identity, plan_sha256:'a'.repeat(64),
  repository:'/new/public/repo', thread_environment:{OMP_NUM_THREADS:'1'},
  actor_activation_UTC_seconds:1000,actor_window_seconds:2700,
  actor_deadlines_UTC:{exporter:'1970-01-01T01:01:40.000Z',
    independent:'1970-01-01T01:01:40.000Z'},
  FULL_caps_seconds:Object.fromEntries(roles.map((r,i)=>[r,caps[i]])),
  external_argv:Object.fromEntries(roles.map(r=>[r,[[r,'supervise'],[r,'finalize']]]))};
const fault = process.argv[2];
const sandbox = {module:{exports:{}},
  load:k=>state.get(k), store:(k,v)=>state.set(k,v), text:v=>emitted.push(v),
  Date:class extends Date {static now(){return milliseconds+=100;}},
  tools:{exec_command:async args=>{
    calls.push(args);
    const role = state.get('r3-active-role');
    const p = {execution_identity:identity, role, plan_sha256:context.plan_sha256,
      frozen_FULL_seconds:context.FULL_caps_seconds[role],
      clock_domain:'functions.exec.Date.now.UTC-seconds', clock_resolution_seconds:0.001,
      external_argv:context.external_argv[role],
      actor_activation_UTC_seconds:context.actor_activation_UTC_seconds,
      actor_window_seconds:context.actor_window_seconds,
      actor_deadlines_UTC:context.actor_deadlines_UTC};
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
const dispatch = sandbox.module.exports.dispatchRoleV3;
async function rejected(role,ctx=context) {
  const before=calls.length;
  try { await dispatch(ctx,role); throw new Error('guard allowed role'); }
  catch(e) { if(e.message==='guard allowed role') throw e; }
  if(calls.length!==before) throw new Error('guard dispatched a tool');
}
(async()=>{
  await rejected('extra',{...context,external_argv:{...context.external_argv,extra:[]}});
  milliseconds=Date.parse(context.actor_deadlines_UTC.independent)-1860*1000+1;
  await rejected(roles[0]);
  milliseconds=1000000;
  const first = await dispatch(context,roles[0]);
  await rejected(roles[0]);
  await rejected(roles[2]);
  if(fault==='none') {
    if(first.terminal.status!=='PASS_R_V3_FULL_ROLE') throw new Error('valid role refused');
    await dispatch(context,roles[1]);
    if(!calls[2].cmd.includes('TOPOLAB_R3_PREVIOUS_TOOL_RECORDS=')) throw new Error('no replay');
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
