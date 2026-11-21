"""New finite metadata compatibility; no Native, Original or custody IO."""

import hashlib
import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
INPUT = 'topolab.v2.p17-m2-registered-source-acquisition.20261121.v1'
RECOVERY = 'topolab.v2.p17-binding-certificate-recovery.20261121.v1'
EVIDENCE = Path('/Users/keith1117/Documents/TopoLab-data/metadata-input-acceptance-20261121')


def module(name):
    path = ROOT / 'scripts' / (name + '.py')
    value = types.ModuleType('nov21_test_' + name)
    value.__file__ = str(path)
    sys.modules[value.__name__] = value
    exec(compile(path.read_bytes(), str(path), 'exec'), value.__dict__)
    return value


def recovery(monkeypatch):
    value = module('p17_m2_source_binding_recovery')
    monkeypatch.setattr(value, 'CONTINUATION_INPUT', INPUT)
    monkeypatch.setattr(value, 'IDENTITY', RECOVERY)
    monkeypatch.setattr(value, 'CONTINUATION_CONFIG', {'evidence_root': str(EVIDENCE)})
    return value


def test_new_native_identity_uses_same_caps_and_dated_neutral_entry():
    native = module('p17_m2_source_binding_native')
    plan = {'schema': native.METADATA_SCHEMA,
            'context': {'execution_identity': RECOVERY, 'scope': native.RECOVERY_SCOPE,
                        'attempt': 1},
            'root': str(EVIDENCE / 'metadata-formal-a1'),
            'runtime': {'cwd': str(ROOT), 'python': '/public/python'}}
    assert native.execution_profile(plan) == (RECOVERY, 300)
    assert native.role_profile(plan)[0] == {'binding-certificate-auditor': 120}
    assert native.role_profile(plan)[3] == {
        'binding-certificate-auditor': '/root/full60_independent'}
    for mode in ('supervise', 'run', 'record', 'payload'):
        assert native.argv_for(plan, mode, 'binding-certificate-auditor')[2] == str(
            ROOT / 'scripts/binding_recovery_20261121.py')
    plan['context']['attempt'] = 2
    with pytest.raises(ValueError, match='only its metadata profile'):
        native.execution_profile(plan)


def test_core_dated_payload_and_exact_new_root_router(monkeypatch):
    core = module('p17_m2_source_binding')
    argv = core.role_argv(EVIDENCE / 'metadata-formal-a1', 'payload', 'a' * 64,
                          'binding-certificate-auditor', '/public/python',
                          execution_identity=RECOVERY)
    assert argv[2] == str(ROOT / 'scripts/binding_recovery_20261121.py')
    calls = []
    selected = types.SimpleNamespace(load_plan=lambda *args: calls.append(args) or {'new': True})
    dispatcher = types.SimpleNamespace(for_identity=lambda identity: (
        selected if identity == RECOVERY else pytest.fail('wrong dated identity')))
    monkeypatch.setattr(core, 'load', lambda name: dispatcher if name ==
                        'p17_m2_source_binding_recovery' else pytest.fail('unexpected IO'))
    path = EVIDENCE / 'metadata-formal-a1/plan.json'
    assert core.load_plan(path, 'a' * 64) == {'new': True}
    assert calls == [(path, 'a' * 64)]


def test_private_new_metadata_mode_does_not_admit_old_or_library_paths(monkeypatch):
    old = module('p17_m2_source_binding')
    value = recovery(monkeypatch)
    core = value.enable_new_metadata_mode()
    assert core is not old and old.FULL60_METADATA_MODE is False
    core.metadata_path_guard(EVIDENCE / 'metadata-availability-capture/public-core.json')
    backup = Path(str(EVIDENCE) + '-backup')
    core.metadata_path_guard(backup / 'public-metadata-certificate-a1.json')
    for path in (backup / 'other.json', Path('/Users/keith1117/Library/never-opened'),
                 value.FULL60_EVIDENCE / 'metadata-public-a1/plan.json'):
        with pytest.raises(ValueError, match='not NEW metadata'):
            core.metadata_path_guard(path)


def test_new_raw_only_plan_preserves_exact_raw_and_rejects_changed_hash(monkeypatch):
    value = recovery(monkeypatch)
    parsed = {'nanoseconds': 1795238585140541001, 'receipt': 'exact original raw'}
    raw = value.canonical(parsed).decode()
    original = {'preflight': parsed, 'preflight_raw': raw,
                'preflight_reference': {'path': str(EVIDENCE / 'preflight.json'),
                                        'sha256': value.sha(raw.encode())}}
    compact = value.compact_formal_entry(original)
    assert 'preflight' not in compact and original['preflight'] == parsed
    assert compact['preflight_raw'] == raw
    assert value.formal_preflight(compact) == parsed
    compact['preflight_raw'] += ' '
    with pytest.raises(ValueError, match='SHA'):
        value.formal_preflight(compact)


def test_new_metadata_capture_cap_clips_before_reader(monkeypatch):
    value = recovery(monkeypatch)
    core = value.enable_new_metadata_mode()
    calls = []
    monkeypatch.setattr(core, 'read_metadata', lambda path, maximum, **kwargs:
                        calls.append((path, maximum)) or ({}, b'{}\n'))
    reference = {'path': str(EVIDENCE / 'bounded.json'), 'sha256': 'a' * 64}
    value.read_ref(reference)
    value.capture_ref(reference, maximum=40 * 1024**2)
    assert [cap for _, cap in calls] == [16 * 1024**2, 16 * 1024**2]


def test_new_writer_rejects_oversize_before_target_io(monkeypatch, tmp_path):
    value = recovery(monkeypatch)
    monkeypatch.setattr(value, 'metadata_buffer_limit', lambda maximum: min(maximum, 32))
    path = tmp_path / 'must-not-exist/result.json'
    with pytest.raises(ValueError, match='metadata byte cap'):
        value.write_new(path, {'text': 'x' * 40})
    assert not path.parent.exists()


def test_complete_certificate_cap_includes_plan_core_events_and_native_evidence(monkeypatch):
    value = recovery(monkeypatch)
    raw_log = b'exact retained native log'
    evidence = {'inner_evidence': {'log': raw_log}}
    envelope = value.result_envelope({'plan': 'x' * 128}, {'core': 'x' * 128}, [], evidence)
    encoded_evidence = value.load('p17_m2_content_verified_control').evidence_json(evidence)
    assert envelope['metadata_evidence'] == encoded_evidence
    cap = len(value.canonical(envelope))
    monkeypatch.setattr(value, 'metadata_buffer_limit', lambda _: cap - 1)
    with pytest.raises(ValueError, match='complete NEW certificate metadata byte cap'):
        value.result_envelope(envelope['metadata_plan'], envelope['core_bundle'], [], evidence)
    assert evidence['inner_evidence']['log'] == raw_log


def test_new_native_resource_reader_bounds_raw_text_and_preserves_original_log(monkeypatch):
    native = module('p17_m2_source_binding_native')
    plan = {'schema': native.METADATA_SCHEMA,
            'context': {'execution_identity': RECOVERY, 'scope': native.RECOVERY_SCOPE,
                        'attempt': 1}, 'root': str(EVIDENCE / 'metadata-formal-a1'),
            'runtime': {'cwd': str(ROOT), 'python': '/public/python'}}
    transport = native.MetadataTransport(plan)
    calls = []
    raw_log = b'exact native text, not required to be JSON\n'

    def read(path, maximum):
        calls.append((path, maximum))
        return b'{"helpers":[]}' if path.name == 'command.json' else raw_log

    core = types.SimpleNamespace(read_metadata_bytes=read)
    selected = types.SimpleNamespace(load=lambda _: core)
    monkeypatch.setattr(native, 'load', lambda _: types.SimpleNamespace(
        for_identity=lambda identity: selected if identity == RECOVERY else None))
    result = transport.resource_evidence(transport.root, native.sha(native.canonical(plan)),
                                         'binding-certificate-auditor')
    assert result['inner_evidence']['log'] == raw_log
    assert len(calls) == 4 and all(cap == 16 * 1024**2 for _, cap in calls)


def test_dated_entry_is_present_and_binds_exact_profile():
    entry = module('binding_recovery_20261121')
    assert entry.INPUT == INPUT and entry.RECOVERY == RECOVERY
    assert 'NOV21_INPUT' in Path(entry.__file__).read_text()


@pytest.mark.parametrize('dated', [True, False])
def test_single_use_new_help_keeps_legacy_prefix_policy(monkeypatch, dated):
    value = recovery(monkeypatch)
    if not dated:
        monkeypatch.setattr(value, 'CONTINUATION_INPUT', value.FULL60_INPUT)
        monkeypatch.setattr(value, 'IDENTITY', value.FULL60_RECOVERY)
    path = str(EVIDENCE / 'permission.json')
    policy = {'permission_preflight': {'packet_paths': {'public': path}},
              'actors': {'independent': '/root/full60_independent'},
              'limits': {'software_start_ms': 1}}
    monkeypatch.setattr(value, 'authority', lambda: policy)
    monkeypatch.setattr(value, 'exact_actual', lambda *_: (10, 11))
    runtime = {'python': '/public/python'}
    packet = {'request': {'sandbox_permissions': 'require_escalated'},
              'responses': [{'result': {'exit_code': 0, 'output': 'usage: new metadata'}}]}
    prefix = ['env', 'OMP_NUM_THREADS=1', 'OPENBLAS_NUM_THREADS=1', 'MKL_NUM_THREADS=1',
              'VECLIB_MAXIMUM_THREADS=1', 'NUMEXPR_NUM_THREADS=1', '/public/python', '-I',
              str(ROOT / 'scripts' / value.CLI_ENTRY)]

    def captured():
        raw = value.canonical(packet).decode()
        return {'reference': {'path': path, 'sha256': value.sha(raw.encode())},
                'raw': raw, 'value': packet}

    if not dated:
        packet['request']['prefix_rule'] = prefix
    assert value.checked_permission(captured(), runtime, before_ms=12) == (10, 11)
    if dated:
        packet['request']['prefix_rule'] = prefix
    else:
        del packet['request']['prefix_rule']
    with pytest.raises(ValueError, match='permission actual author/prefix/help'):
        value.checked_permission(captured(), runtime, before_ms=12)


def test_new_activation_binds_literal_closures_stdout_and_fresh_publication(monkeypatch):
    value = recovery(monkeypatch)
    main, run = 'a' * 40, 123
    publication_argv = ['gh', 'run', 'view', str(run), '--exit-status', '--json',
                        'headSha,status,conclusion']
    def packet(argv, ended, output):
        return {'argv': argv, 'responses': [{'returned_ms': ended, 'result': {'output': output}}]}

    activation = {
        'schema': 'topolab.v2.m2-strict-source-binding.recovery-activation.v1',
        'execution_identity': RECOVERY, 'software_source_tree': {},
        'started_ms': 100, 'deadline_ms': 1200100, 'main': main, 'main_CI_run': run,
        'software_closure_actual': packet(
            ['git', '--no-optional-locks', 'diff', '--check', 'HEAD'], 80, ''),
        'publication_closure_actual': packet(publication_argv, 100, json.dumps({
            'headSha': main, 'status': 'completed', 'conclusion': 'success'})),
    }
    monkeypatch.setattr(value, 'authority', lambda: {
        'preparation_proofs': {'recovery_activation_path': str(EVIDENCE / 'activation.json')},
        'actors': {'producer': '/root'}, 'limits': {'global_deadline_ms': 2000000,
                                                   'software_start_ms': 1,
                                                   'software_deadline_ms': 200}})

    def actual(raw, argv, _):
        value.need(raw['argv'] == argv, 'literal closure argv differs')
        return (70 if argv[0] == 'git' else 90), raw['responses'][-1]['returned_ms']

    monkeypatch.setattr(value, 'exact_actual', actual)

    def checked():
        raw = value.canonical(activation).decode()
        return value._captured_activation(activation, raw, value.sha(raw.encode()), {})

    assert checked() == activation
    value.check_activation_publication(activation, {'main': main, 'main_CI_run': run})
    with pytest.raises(ValueError, match='activation exact-main'):
        value.check_activation_publication(activation, {'main': 'b' * 40, 'main_CI_run': run})
    activation['software_closure_actual']['argv'] = ['true']
    with pytest.raises(ValueError, match='literal closure argv'):
        checked()
    activation['software_closure_actual']['argv'] = [
        'git', '--no-optional-locks', 'diff', '--check', 'HEAD']
    activation['publication_closure_actual']['responses'][0]['result']['output'] = json.dumps({
        'headSha': main, 'status': 'completed', 'conclusion': 'failure'})
    with pytest.raises(ValueError, match='publication closure stdout'):
        checked()


def test_new_component_partition_requires_exact_contract_inventory(monkeypatch, tmp_path):
    value = recovery(monkeypatch)
    names = ['scripts/p17_m2_source_binding_recovery.py', 'scripts/helper.py']
    partition_name = 'docs/planning/input_review_20261121.json'
    partition = {'schema': 'topolab.NEW-full60-input-cross-review-partition.v1',
                 'execution_identity': RECOVERY, 'jointly_owned': 'DENY_NO_SELF_REVIEW',
                 'source_tree_is_version_pin_not_review_scope': True,
                 'members': {name: {'writer': writer, 'reviewer': reviewer,
                                    'required_axes': ['standards', 'spec']}
                             for name, writer, reviewer in [
                                 (names[0], '/root/full60_independent', '/root'),
                                 (names[1], '/root/containment_spec', '/root/full60_independent')]}}
    path = tmp_path / partition_name
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(partition))
    policy = {'review_schema': {'kind': 'NEW_COMPONENT_CROSS_REVIEW',
                              'partition_path': partition_name,
                              'required_axes': ['standards', 'spec'],
                              'full_source_tree_is_version_pin': True,
                              'expected_members': sorted(names)}}
    monkeypatch.setattr(value, 'REPO', tmp_path)
    monkeypatch.setattr(value, 'sha', lambda raw: hashlib.sha256(raw).hexdigest())
    monkeypatch.setattr(value, 'authority', lambda: policy)
    assert value.component_review_partition()[0] == partition
    del partition['members'][names[1]]
    path.write_text(json.dumps(partition))
    with pytest.raises(ValueError, match='coverage'):
        value.component_review_partition()
