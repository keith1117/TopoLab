"""New prospective identities retain isolated historical execution policies."""
import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
NEW_RECOVERY = 'topolab.v2.p17-binding-certificate-recovery.20261104.v5'
NEW_INPUT = 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v3'


def module(name):
    spec = importlib.util.spec_from_file_location(name, REPO / 'scripts' / (name + '.py'))
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def test_new_native_recovery_uses_explicit_entry_without_relabeling_old_plan():
    native = module('p17_m2_source_binding_native')
    plan = {'schema': native.METADATA_SCHEMA,
            'context': {'execution_identity': NEW_RECOVERY, 'attempt': 1,
                        'scope': native.RECOVERY_SCOPE},
            'runtime': {'python': '/public/python', 'cwd': str(REPO)},
            'root': '/public/recovery'}
    assert native.execution_profile(plan) == (NEW_RECOVERY, 300)
    assert native.argv_for(plan, 'supervise', 'binding-certificate-auditor')[2].endswith(
        '/scripts/p17_m2_source_binding_recovery_v5.py')
    plan['context']['execution_identity'] = native.RECOVERY_V4_IDENTITY
    assert native.argv_for(plan, 'supervise', 'binding-certificate-auditor')[2].endswith(
        '/scripts/p17_m2_source_binding_recovery.py')


def test_new_recovery_profile_keeps_old_module_and_policy_unchanged():
    old = module('p17_m2_source_binding_recovery')
    original = old.IDENTITY, old.PROTOCOL_PATH, old.AUTHORITY.read_bytes()
    new = old.for_identity(NEW_RECOVERY)
    assert (old.IDENTITY, old.PROTOCOL_PATH, old.AUTHORITY.read_bytes()) == original
    assert new.IDENTITY == NEW_RECOVERY
    assert new.PROTOCOL_PATH.endswith('_recovery_v5_protocol.json')
    assert new is not old
    with pytest.raises(ValueError, match='identity'):
        old.for_identity('unregistered')


def test_new_registered_roots_select_isolated_both_author_profiles(monkeypatch):
    control = module('p17_m2_source_acquisition_control')
    old_id = control.REGISTERED_IDENTITY
    new = control.for_registered_identity(NEW_INPUT)
    root = '/Users/keith1117/Library/Application Support/TopoLab-custody/' \
           'p17-m2-local-input-version-v10-strict-binding-20261104'
    assert new.registered_root(root)
    assert not control.registered_root(root)
    assert control.REGISTERED_IDENTITY == old_id
    registered = new.load('p17_m2_registered_input')
    auditor = new.load('p17_m2_source_acquisition_independent')
    assert registered.IDENTITY == auditor.REGISTERED_IDENTITY == NEW_INPUT
    assert registered.PROTOCOL == auditor.REGISTERED_PROTOCOL
    assert registered.authority()["new_input_budget"]["sha256"] == (
        "37f0002eb2d80c9dc9dcce66fa0442b6538dd5ea4009f2c15484961b10edf9a6")
    compiled = {}

    def capture(plan, **kwargs):
        compiled.update(kwargs)
        raise RuntimeError('independent compiler arguments before runtime IO')

    monkeypatch.setattr(auditor, 'validate_binding', lambda plan: None)
    monkeypatch.setattr(auditor.native, '_check_software', capture)
    plan = {'execution_identity': NEW_INPUT, 'scope': auditor.REHEARSAL_SCOPE,
            'source_identity_policy': auditor.HASH_BOUND_POLICY,
            'binding': {'source_identity_policy': auditor.HASH_BOUND_POLICY,
                        'authority_protocol_path': auditor.REGISTERED_PROTOCOL,
                        'strict23_registration': {'certificate_sha256': 'a' * 64,
                                                  'finalize_actual_sha256': 'b' * 64}}}
    with pytest.raises(RuntimeError, match='compiler arguments'):
        auditor._check_software(plan)
    independent = auditor.native._software_closure(REPO, contracts=compiled['contracts'])
    assert independent == new.source_freeze(NEW_INPUT)
    for name in ('scripts/p17_m2_input_continuation.py',
                 'scripts/p17_m2_source_binding_recovery_v5.py',
                 'scripts/p17_m2_registered_input_v3.py',
                 'docs/planning/p17_m2_registered_input_v3_protocol.json',
                 'docs/planning/p17_m2_source_binding_certificate_recovery_v5_protocol.json'):
        assert name in new.source_freeze(NEW_INPUT)


def test_new_recovery_resource_identity_cannot_escape_metadata_scope():
    module('p17_m2_homotopy')
    resource = module('p17_m2_resource_control')
    with pytest.raises(ValueError, match='identity/scope'):
        resource.invoke(None, 'binding-certificate-auditor', ['PUBLIC_NOT_EXECUTED'], timeout=1,
                        measurement_execution_identity=NEW_RECOVERY,
                        measurement_scope='PUBLIC_STRICT_BINDING_REGISTRATION_ONLY')


@pytest.mark.parametrize('late', [False, True])
@pytest.mark.parametrize('recovery_identity', [NEW_RECOVERY,
    'topolab.v2.p17-binding-certificate-recovery.20261104.v6'])
def test_new_activation_requires_both_actual_closures_inside_its_preregistered_window(
        late, recovery_identity):
    old = module('p17_m2_source_binding_recovery')
    subject = old.for_identity(recovery_identity)
    path = REPO / 'tests/test_p17_m2_source_binding_recovery.py'
    spec = importlib.util.spec_from_file_location('continuation_actual_fixture', path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    policy = subject.authority()
    start, end = (policy['limits'][key] for key in ('software_start_ms', 'software_deadline_ms'))
    runtime = subject.load('p17_m2_source_binding').runtime()
    argv = [runtime['python'], '-I', '-c', 'NEW_PUBLIC_UNIT_METADATA_ONLY']
    software = fixture.actual_packet(subject, argv, '/root', '{}\n', start + 1, start + 2)
    publication_end = end + int(late)
    publication = fixture.actual_packet(subject, argv, '/root', '{}\n', start + 3,
                                        publication_end)
    activation = {'schema': 'topolab.v2.m2-strict-source-binding.recovery-activation.v1',
                  'execution_identity': recovery_identity,
                  'software_source_tree': subject.source_freeze(),
                  'started_ms': publication_end, 'deadline_ms': publication_end + 1200000,
                  'software_closure_actual': software, 'publication_closure_actual': publication}
    raw = subject.canonical(activation)
    if late:
        with pytest.raises(ValueError, match='actual does not establish activation'):
            subject._captured_activation(activation, raw.decode(), subject.sha(raw),
                                         subject.source_freeze())
    else:
        assert subject._captured_activation(activation, raw.decode(), subject.sha(raw),
                                            subject.source_freeze()) == activation


def test_old_v4_rejects_publication_one_millisecond_after_original7200():
    subject = module('p17_m2_source_binding_recovery')
    path = REPO / 'tests/test_p17_m2_source_binding_recovery.py'
    spec = importlib.util.spec_from_file_location('old_actual_fixture', path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    ended = 1793796389352
    argv = [subject.load('p17_m2_source_binding').runtime()['python'],
            '-I', '-c', 'PUBLIC_UNIT_OLD_CLOCK_NO_NATIVE']
    software = fixture.actual_packet(subject, argv, '/root', '{}\n', ended - 1, ended)
    late = ended + 7200001
    publication = fixture.actual_packet(subject, argv, '/root', '{}\n', ended + 1, late)
    activation = {'schema': 'topolab.v2.m2-strict-source-binding.recovery-activation.v1',
                  'execution_identity': subject.IDENTITY,
                  'software_source_tree': subject.source_freeze(),
                  'started_ms': late, 'deadline_ms': late + 1200000,
                  'software_closure_actual': software, 'publication_closure_actual': publication}
    raw = subject.canonical(activation)
    with pytest.raises(ValueError, match='actual does not establish activation'):
        subject._captured_activation(activation, raw.decode(), subject.sha(raw),
                                     subject.source_freeze())


def budget_fixture(subject, tmp_path, monkeypatch):
    import json
    policy = json.loads(subject.AUTHORITY.read_bytes())
    start = policy['limits']['software_start_ms']
    data = {
        'budget': {
            'schema': 'topolab.owner.NEW-prospective-postpublication-input-continuation.v27',
            'no_old_allowance_reopened': True, 'global_deadline_ms_UNCHANGED': 1793828280000,
            'NEW_root_independent_each': {
                'software_and_publication_seconds': 7200, 'metadata_recovery_seconds': 1200,
                'formal_input_seconds': 4500, 'input_result_seconds': 1800,
                'metadata_dispatches': 320},
            'NEW_formal': {'total_read_cap': 2392, 'new_registration_Original_reads': 0,
                           'new_registration_Foundation_helpers': 0,
                           'native_RSS_bytes': 4294967296},
            'NEW_public': {'coordination_seconds': 240}},
        'budget_review': {'author': '/root/binding_route_independent_v1',
                          'status': 'PASS_PUBLIC_UNIT_FIXTURE_ONLY'},
        'prior_failed_metadata_closure': {'public_unit_fixture': True},
        'prior_failed_metadata_closure_actual': {'public_unit_fixture': True},
        'prior_failed_publication': {
            'status': 'CLOSED_FAILED_PUBLICATION_MAIN_CI_NOT_READY_FORMAL_UNLAUNCHED',
            'hard_deadline_ms': 1793803589352}}
    raw = subject.canonical(data['budget'])
    policy['budget'] = {'path': str(tmp_path / 'budget.json'), 'sha256': subject.sha(raw)}
    data['registration_actual'] = {
        'author': '/root', 'grant_sha256': policy['budget']['sha256'],
        'activation_starts_at': start,
        'event': {'tool': 'exec_command', 'requested_ms': start - 1, 'returned_ms': start,
                  'result': {'exit_code': 0,
                             'output': str(len(raw)) + ' ' + policy['budget']['sha256'] + '\n'}}}
    data['software_activation'] = {
        'schema': 'topolab.NEW-prospective-input-continuation.software-activation.v1',
        'execution_identity': NEW_RECOVERY, 'budget_reference': policy['budget'],
        'started_ms': start, 'deadline_ms': start + 7200000,
        'global_deadline_ms': 1793828280000, 'no_old_allowance_reopened': True,
        'old_deadline_ms': 1793803589352}
    captures = {}
    for key, value in data.items():
        raw = subject.canonical(value)
        policy[key] = {'path': str(tmp_path / (key + '.json')), 'sha256': subject.sha(raw)}
        captures[key] = {'reference': policy[key], 'raw': raw.decode(), 'value': value}
    monkeypatch.setattr(subject, 'authority', lambda: policy)
    return captures


@pytest.mark.parametrize('fault',
                         [None, 'raw-sha', 'registration-return', 'budget-cap', 'old-pass'])
def test_new_budget_replays_original_raw_grant_return_and_closed_failure(
        tmp_path, monkeypatch, fault):
    subject = module('p17_m2_source_binding_recovery').for_identity(NEW_RECOVERY)
    captures = budget_fixture(subject, tmp_path, monkeypatch)
    if fault == 'raw-sha':
        captures['budget']['raw'] += ' '
    elif fault == 'registration-return':
        captures['registration_actual']['value']['event']['returned_ms'] += 1
    elif fault == 'budget-cap':
        captures['budget']['value']['NEW_root_independent_each']['metadata_dispatches'] = 321
    elif fault == 'old-pass':
        captures['prior_failed_publication']['value']['status'] = 'PASS'
    if fault and fault != 'raw-sha':
        key = {'registration-return': 'registration_actual', 'budget-cap': 'budget',
               'old-pass': 'prior_failed_publication'}[fault]
        raw = subject.canonical(captures[key]['value'])
        captures[key]['raw'] = raw.decode()
        captures[key]['reference']['sha256'] = subject.sha(raw)
    if fault:
        with pytest.raises(ValueError):
            subject._captured_budget(captures)
    else:
        assert subject._captured_budget(captures)['software_activation']['started_ms'] == (
            1793803621805)
