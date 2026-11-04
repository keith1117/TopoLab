"""Recovery replays captured strict buffers; fixtures grant no native admission."""

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def module():
    path = REPO / 'scripts/p17_m2_source_binding_recovery.py'
    spec = importlib.util.spec_from_file_location('binding_recovery_test', path)
    assert spec and spec.loader
    result = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = result
    spec.loader.exec_module(result)
    return result


def test_v16_protocol_keeps_captured_core_and_uses_only_new_budget_and_targets():
    subject = module()
    policy = subject.authority()
    assert subject.IDENTITY == 'topolab.v2.p17-binding-certificate-recovery.20261104.v4'
    assert subject.PROTOCOL_PATH.endswith('_recovery_v4_protocol.json')
    assert policy['budget']['sha256'] == (
        'b8d09dec380471e61b112dd7d91411860787e782c606528c0c47cee10b7f07fb')
    assert policy['budget_review']['sha256'] == (
        '1ade25d150e3d8db3d0d7ff201a9a75610303c58e0e535582de4a27369a91215')
    assert policy['software_activation']['sha256'] == (
        'b5c0fc4148c1f6303963074e6bad3b792c184f953260d8fabb9e931aaafd5782')
    assert policy['limits']['software_start_ms'] == 1793789340022
    assert policy['limits']['software_deadline_ms'] == 1793796540022
    assert policy['limits']['software_metadata_each'] == 192
    assert policy['publication_only']['seconds_each'] == 7200
    assert policy['limits']['recovery_stage_seconds'] == 1200
    assert policy['primary_public_root'].endswith('certificate-recovery-v6')
    assert subject._root('formal', 1).name == 'binding-formal-v3-certificate-recovery-v4'
    assert policy['captured_cores']['public']['sha256'] == (
        '1eb6b8ff74114fe9b856715b04f75fb8b609bd5805ad6277fcce17da5f5785ba')
    assert policy['captured_cores']['formal']['sha256'] == (
        'ff5acace575365b2eeaf94884740363631056e57b92635caba85735bb53d0bf0')
    assert len(policy['captured_cores']['formal']['context']['source_tree']) == 19
    old = REPO / 'docs/planning/p17_m2_source_binding_certificate_recovery_protocol.json'
    assert subject.sha(old.read_bytes()) == (
        '81defa06c42cd2f4b830ae6189ad7245bd3efbcea86ab323f33da4bb65acd2d4')


def captured_bundle(tmp_path):
    spec = importlib.util.spec_from_file_location(
        'recovery_public_native_fixture', REPO / 'tests/test_p17_m2_source_binding_native.py')
    assert spec and spec.loader
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    native = fixture.adapter()
    original_subject = fixture.native_subject

    def owned_subject(module, *, failed=False):
        plan, evidence, events = original_subject(module, failed=failed)
        plan['root'] = str(tmp_path / 'topolab-public-captured-core')
        fixture.reseal(module, plan, evidence, events)
        return plan, evidence, events

    fixture.native_subject = owned_subject
    plan, evidence, events, primary, independent = fixture.window2_subject(native, tmp_path)
    certificate = native.audit_certificate(plan, evidence, events, primary, independent)
    bundle = {'schema': 'topolab.v2.m2-strict-source-binding.evidence-bundle.v1',
              'plan': plan, 'evidence_by_role': native.load(
                  'p17_m2_content_verified_control').evidence_json(evidence),
              'trusted_events_by_role': events, 'primary': primary,
              'independent': independent, 'certificate': certificate}
    return native, bundle


def fixture_authority(subject, tmp_path, bundle, monkeypatch):
    value = json.loads(subject.AUTHORITY.read_bytes())
    value['captured_cores']['public'] = {
        'path': str(Path(bundle['plan']['root']) / 'certificate-bundle.json'),
        'sha256': subject.sha(subject.canonical(bundle)),
        'context': deepcopy(bundle['plan']['context'])}
    path = tmp_path / 'new-public-recovery-contract.json'
    path.write_bytes(subject.canonical(value))
    monkeypatch.setattr(subject, 'AUTHORITY', path)
    return value


def test_replay_closed_strict_core_keeps_original_identity_without_source_io(tmp_path, monkeypatch):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    fixture_authority(subject, tmp_path, bundle, monkeypatch)
    core = subject.load('p17_m2_source_binding')
    monkeypatch.setattr(core, 'read_metadata', lambda *a, **kw: pytest.fail('source/path read'))
    result = subject.replay_core(bundle, 'public')
    assert result == bundle['certificate']
    assert result['execution_identity'] != subject.IDENTITY
    assert result['bindings'] and len(result['bindings']) == 23
    assert result['input_acceptance'] is result['B_C_admission'] is False


def test_public_prepare_rejects_unreviewed_entry_before_new_target_probe(tmp_path, monkeypatch):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    value = fixture_authority(subject, tmp_path, bundle, monkeypatch)
    target = tmp_path / 'new-public-recovery'
    value['targets']['public'][0] = str(target)
    value['primary_public_root'] = str(target)
    subject.AUTHORITY.write_bytes(subject.canonical(value))
    with pytest.raises(ValueError, match='review'):
        subject.prepare('public', 1)
    assert not target.exists()


def public_preparation(subject, tmp_path, bundle, monkeypatch):
    value = fixture_authority(subject, tmp_path, bundle, monkeypatch)
    core = subject.load('p17_m2_source_binding')
    runtime = core.runtime()
    monkeypatch.setattr(core, 'runtime', lambda: dict(
        runtime, isolated=1, cwd=str(REPO), threads=dict(core.THREADS)))
    target = tmp_path / 'new-public-recovery'
    value['targets']['public'][0] = str(target)
    value['primary_public_root'] = str(target)
    for kind in ('public', 'formal'):
        value['certificate_paths'][kind] = [[str(tmp_path / (kind + str(i) + '.json')),
            str(tmp_path / (kind + str(i) + '-backup.json'))] for i in (1, 2)]
    value['preparation_proofs']['preflight_path'] = str(tmp_path / 'preflight.json')
    value['preparation_proofs']['preflight_actual_path'] = str(tmp_path / 'preflight.actual.json')
    value['preparation_proofs']['recovery_activation_path'] = str(tmp_path / 'activation.json')
    now = subject.time.time_ns() // 10**6
    value['limits']['software_start_ms'] = now - 1000
    value['limits']['software_deadline_ms'] = now + 7199000
    value['limits']['global_deadline_ms'] = now + 20000000

    def pinned(key, data):
        path = tmp_path / (key + '.json')
        path.write_bytes(subject.canonical(data))
        value[key] = {'path': str(path), 'sha256': subject.sha(path.read_bytes())}
        return path.read_bytes()

    start = value['limits']['software_start_ms']
    closed = {'status': 'CLOSED_FAILED_PUBLIC_CERTIFICATE_NOT_PREPARATION_COMPLETE'}
    pinned('prior_failed_metadata_closure', closed)
    summary = {'known_NEW_FULL_lower': 94530, 'P17': 'UNREPAIRED',
        'own_future_return': subject.FUTURE, 'input_accepted': False,
        'paths': [value['prior_failed_metadata_closure']['path']],
        'sha256': value['prior_failed_metadata_closure']['sha256'], 'status': closed['status']}
    old_actual = actual_packet(subject,
        [runtime['python'], '-I', '-c', 'PUBLIC_FIXTURE_ONLY'], value['actors']['producer'],
        subject.canonical(summary).decode(), start - 3, start - 2)
    value['prior_failed_metadata_closure_cwd'] = str(REPO)
    pinned('prior_failed_metadata_closure_actual', old_actual)
    budget = {'schema': 'topolab.owner.NEW-unstarted-input-closure-coordination-repair.v22',
              'NEW_each_seconds': {'software_preparation': 7200,
                  'publication_only': 7200, 'formal_metadata_and_result': 1200},
              'NEW_each_nested_dispatches': {'software': 192, 'publication': 128,
                  'formal_metadata': 64, 'total': 384},
              'source_registration_new_original_reads': 0,
              'source_registration_new_Foundation_helpers': 0,
              'coordination_seconds_max_UNCHANGED': 240,
              'ROOT_I_original_hard_deadline_ms_UNCHANGED': value['limits']['global_deadline_ms'],
              'old_failed_closing_actual': old_actual}
    budget_raw = pinned('budget', budget)
    pinned('budget_review', {'status': 'PASS_PUBLIC_FIXTURE_ONLY',
                            'author': value['actors']['independent']})
    pinned('registration_actual', {'event': {'tool': 'exec_command',
        'requested_ms': start - 1, 'returned_ms': start,
        'result': {'exit_code': 0, 'output': str(len(budget_raw)) + ' '
                   + value['budget']['sha256'] + '\n'}},
        'grant_sha256': value['budget']['sha256'], 'activation_starts_at': start})
    activation = {'execution_identity': subject.IDENTITY, 'budget_reference': value['budget'],
        'started_ms': start, 'deadline_ms': start + 7200000,
        'global_deadline_ms': value['limits']['global_deadline_ms'],
        'old_V16_V20_closing_actual': old_actual, 'old_closing_is_FAILED_never_PASS': True}
    pinned('software_activation', activation)
    for axis in ('standards', 'spec'):
        value['review_paths'][axis] = str(tmp_path / (axis + '.json'))
    subject.AUTHORITY.write_bytes(subject.canonical(value))
    hashes = {}
    for axis in ('standards', 'spec'):
        path = Path(value['review_paths'][axis])
        path.write_bytes(subject.canonical({'status': 'PASS', 'open_findings': [],
            'author': value['review_authors'][axis], 'execution_identity': subject.IDENTITY,
            'reviewed_source_tree': subject.source_freeze()}))
        hashes[axis] = subject.sha(path.read_bytes())
    path = Path(value['captured_cores']['public']['path'])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(subject.canonical(bundle))
    return subject.prepare('public', 1, standards_sha=hashes['standards'], spec_sha=hashes['spec'])


def test_public_preparation_returns_literal_continuous_table_and_loads_pinned_plan(
        tmp_path, monkeypatch):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    assert plan['captured_core_context'] == bundle['plan']['context']
    assert plan['context']['execution_identity'] == subject.IDENTITY
    assert plan['context']['attempt'] == 1
    assert plan['context']['source_tree'] != plan['captured_core_context']['source_tree']
    assert plan['deadline_unix_ns'] - plan['started_unix_ns'] == 300 * 10**9
    assert projection['FULL'] == 120 and projection['reserve_seconds'] == 60
    assert projection['commands']['supervise']['argv'][2].endswith(
        '/scripts/p17_m2_source_binding_recovery.py')
    assert Path(plan['root']).stat().st_mode & 0o777 == 0o700
    assert Path(projection['plan_path']).stat().st_mode & 0o777 == 0o600
    subject.admit_plan(plan, subject.ROLE)


def test_captured_pass_flags_do_not_replace_strict_native_core_replay(tmp_path, monkeypatch):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    del bundle['independent']['rows'][0]['closing']
    fixture_authority(subject, tmp_path, bundle, monkeypatch)
    with pytest.raises((ValueError, KeyError), match='closing|buffer|pair|row'):
        subject.replay_core(bundle, 'public')


def recovered_envelope(subject, tmp_path, monkeypatch):
    native, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    spec = importlib.util.spec_from_file_location(
        'recovery_metadata_scalar_fixture', REPO / 'tests/test_p17_m2_source_binding_native.py')
    assert spec and spec.loader
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    _, evidence, events = fixture.metadata_subject(native)
    start = plan['actor_activation_UTC_seconds'] + 1
    for index, event in enumerate(events):
        event['start_seconds'] = start + index * 10
        event['end_seconds'] = start + index * 10 + 7.25
    for packet in (evidence['pending'], evidence['completion']):
        packet.update(execution_identity=subject.IDENTITY,
                      actor_activation_UTC_seconds=plan['actor_activation_UTC_seconds'],
                      actor_window_seconds=300, actor_deadlines_UTC=plan['actor_deadlines_UTC'])
    inner = evidence['inner_evidence']
    inner['record'].update(measurement_execution_identity=subject.IDENTITY,
                            measurement_scope=subject.SCOPE)
    inner['log'] = subject.canonical(bundle['certificate'])
    inner['record']['log_sha256'] = subject.sha(inner['log'])
    fixture.reseal(native, plan, evidence, events, subject.ROLE)
    return {'schema': subject.ENVELOPE_SCHEMA, 'core_bundle': bundle, 'metadata_plan': plan,
            'metadata_evidence': native.load('p17_m2_content_verified_control').evidence_json(
                evidence), 'metadata_events': events, 'own_future_return': subject.FUTURE}


def test_new_return_audit_accepts_complete_native_envelope_without_relabeling_core(
        tmp_path, monkeypatch):
    subject = module()
    envelope = recovered_envelope(subject, tmp_path, monkeypatch)
    certificate, proof = subject.verify_result_envelope(envelope)
    assert certificate['execution_identity'] != subject.IDENTITY
    assert proof['execution_identity'] == subject.IDENTITY
    assert proof['full_role_evidence_accepted'] is True
    assert proof['charged_FULL_seconds'] == 120
    assert proof['RSS_envelope_bytes'] < 4 * 1024**3
    assert certificate['input_acceptance'] is certificate['B_C_admission'] is False


@pytest.mark.parametrize('fault', ['no-return', 'old-auditor-id', 'missing-profile',
                                   'wrong-core', 'changed-buffer'])
def test_new_certificate_rejects_incomplete_or_mixed_return_evidence(
        tmp_path, monkeypatch, fault):
    subject = module()
    envelope = recovered_envelope(subject, tmp_path, monkeypatch)
    if fault == 'no-return':
        envelope['metadata_events'][-1]['complete'] = False
    elif fault == 'old-auditor-id':
        envelope['metadata_plan']['context']['execution_identity'] = (
            envelope['core_bundle']['plan']['context']['execution_identity'])
    elif fault == 'missing-profile':
        envelope['metadata_evidence']['native_profiles'] = {}
    elif fault == 'wrong-core':
        envelope['metadata_plan']['captured_core_context']['attempt'] = 1
    else:
        base = subject.load('p17_m2_content_verified_control')
        evidence = base.evidence_json(envelope['metadata_evidence'], decode=True)
        evidence['inner_evidence']['log'] = b'{"serialized_PASS":true}\n'
        envelope['metadata_evidence'] = base.evidence_json(evidence)
    with pytest.raises((ValueError, KeyError)):
        subject.verify_result_envelope(envelope)


def test_preflight_requires_complete_public_final_return_before_any_proof_write(
        tmp_path, monkeypatch):
    subject = module()
    proof = tmp_path / 'must-not-write.json'
    value = json.loads(subject.AUTHORITY.read_bytes())
    value['preparation_proofs']['preflight_path'] = str(proof)
    contract = tmp_path / 'new-preflight-contract.json'
    contract.write_bytes(subject.canonical(value))
    monkeypatch.setattr(subject, 'AUTHORITY', contract)
    with pytest.raises(ValueError, match='review'):
        subject.preflight(1, '1' * 64, '2' * 64, standards_sha=None, spec_sha=None,
                          activation_sha='3' * 64)
    assert not proof.exists()


def actual_packet(subject, argv, author, output, first, last):
    request = {'cmd': subject.load('p17_m2_source_binding').literal_command(argv),
               'workdir': str(REPO), 'login': False, 'max_output_tokens': 20000}
    return {'schema': 'topolab.v2.m2-strict-source-binding.actual-call.v1',
            'author': author, 'argv': argv, 'event_id': 'public-fixture-only',
            'request': request, 'responses': [{'tool': 'exec_command', 'arguments': request,
                'requested_ms': first, 'returned_ms': last,
                'result': {'output': output, 'exit_code': 0}}]}


def test_published_preflight_and_formal_gate_bind_full_actual_return_and_four_raw_gets(
        tmp_path, monkeypatch):
    import subprocess
    subject = module()
    envelope = recovered_envelope(subject, tmp_path, monkeypatch)
    certificate, audit = subject.verify_result_envelope(envelope)
    policy, plan = subject.authority(), envelope['metadata_plan']
    public_raw = subject.canonical(envelope)
    public_sha = subject.sha(public_raw)
    for path in policy['certificate_paths']['public'][0]:
        subject.write_new(Path(path), envelope)
    now = plan['started_unix_ns'] // 10**6
    argv = [plan['runtime']['python'], '-I',
            str(REPO / 'scripts/p17_m2_source_binding_recovery.py'), 'finalize-result',
            '--plan', str(Path(plan['root']) / 'plan.json'),
            '--plan-sha', subject.sha(subject.canonical(plan))]
    actual = actual_packet(subject, argv, policy['actors']['producer'], subject.canonical(
        subject.finalize_summary(plan, certificate, audit, public_sha)).decode(),
        now + 20000, now + 21000)
    path = Path(plan['root']) / 'finalize-result-raw-actual-call.json'
    final_sha = subject.write_new(path, actual)
    closure_argv = [plan['runtime']['python'], '-I', '-c', 'public_closure_fixture']
    closure = actual_packet(subject, closure_argv, policy['actors']['producer'],
                            '{"public_fixture_only":true}\n', now + 29000, now + 30000)
    activation = {'schema': 'topolab.v2.m2-strict-source-binding.recovery-activation.v1',
                  'execution_identity': subject.IDENTITY, 'started_ms': now + 30000,
                  'deadline_ms': now + 1230000, 'software_source_tree': subject.source_freeze(),
                  'software_closure_actual': closure,
                  'publication_closure_actual': actual_packet(subject, closure_argv,
                      policy['actors']['producer'], '{"public_fixture_only":true}\n',
                      now + 30001, now + 31000)}
    activation['started_ms'] = now + 31000
    activation['deadline_ms'] = now + 1231000
    policy = subject.authority()
    activation_sha = subject.write_new(Path(policy['preparation_proofs'][
        'recovery_activation_path']), activation)
    monkeypatch.setattr(subject.time, 'time_ns', lambda: (now + 60000) * 10**6)
    gh_calls = []
    protection = {'required_status_checks': {'strict': True,
        'contexts': ['quality', 'frontend', 'clean-linux-smoke']},
        'enforce_admins': {'enabled': True}, 'allow_force_pushes': {'enabled': False},
        'allow_deletions': {'enabled': False},
        'required_conversation_resolution': {'enabled': True}}

    def command(argv, **kwargs):
        if argv[0] == 'git':
            raw = b'' if 'status' in argv else b'a' * 40 + b'\n'
        else:
            endpoint = argv[-1]
            gh_calls.append(endpoint)
            if endpoint.endswith('/branches/main'):
                value = {'protected': True, 'commit': {'sha': 'a' * 40,
                    'commit': {'tree': {'sha': 'b' * 40}}}}
            elif endpoint.endswith('/protection'):
                value = protection
            elif '/jobs?' in endpoint:
                value = {'jobs': [{'name': name, 'status': 'completed', 'conclusion': 'success'}
                    for name in ('quality', 'frontend', 'clean-linux-smoke', 'i1-native-software')]}
            else:
                value = {'workflow_runs': [{'head_sha': 'a' * 40, 'head_branch': 'main',
                    'status': 'completed', 'conclusion': 'success', 'id': 99}]}
            raw = json.dumps(value).encode()
        return subprocess.CompletedProcess(argv, 0, raw, b'')

    monkeypatch.setattr(subprocess, 'run', command)
    standards = plan['entry']['reviews']['standards']['reference']['sha256']
    spec = plan['entry']['reviews']['spec']['reference']['sha256']
    result = subject.preflight(1, public_sha, final_sha, standards_sha=standards, spec_sha=spec,
                               activation_sha=activation_sha)
    assert len(gh_calls) == 4
    proof = json.loads(Path(result['path']).read_bytes())
    assert proof['publication']['main_endpoint'] == 'branches/main'
    assert proof['source_tree'] == plan['context']['source_tree']
    argv = subject.preflight_argv(1, public_sha, final_sha, standards, spec, activation_sha)
    packet = actual_packet(subject, argv, policy['actors']['independent'],
        subject.canonical(result).decode(), now + 60000, now + 61000)
    courier = {'author': policy['actors']['independent'], 'preflight_sha256': result['sha256'],
               'actual_call': packet}
    courier_sha = subject.write_new(Path(policy['preparation_proofs']['preflight_actual_path']),
                                    courier)
    accepted = subject.formal_readiness(public_sha, result['sha256'], courier_sha, activation_sha)
    assert accepted['publication']['main_CI_run'] == 99
    subject._captured_formal(accepted, subject._context('formal'), plan['runtime'])
    for fault in ('schema', 'author', 'public-envelope'):
        broken = deepcopy(accepted)
        if fault == 'public-envelope':
            broken['preflight']['public_result'].pop('envelope')
        else:
            broken['preflight'][fault] = 'forged-public-fixture'
        raw = subject.canonical(broken['preflight'])
        broken['preflight_raw'] = raw.decode()
        broken['preflight_reference']['sha256'] = subject.sha(raw)
        with pytest.raises((ValueError, KeyError)):
            subject._captured_formal(broken, subject._context('formal'), plan['runtime'])
    assert len(gh_calls) == 8
    packet['responses'][-1]['result']['output'] = '{"PASS":true}\n'
    changed = Path(policy['preparation_proofs']['preflight_actual_path'])
    changed.write_bytes(subject.canonical(courier))
    with pytest.raises(ValueError, match='stdout/proof SHA'):
        subject.formal_readiness(public_sha, result['sha256'],
            subject.sha(changed.read_bytes()), activation_sha)


@pytest.mark.parametrize('fault', ['reference-sha', 'report-buffer', 'missing-raw'])
def test_native_admission_replays_frozen_review_raw_not_pass_fields(tmp_path, monkeypatch, fault):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    review = plan['entry']['reviews']['standards']
    if fault == 'reference-sha':
        review['reference']['sha256'] = '0' * 64
    elif fault == 'report-buffer':
        review['raw'] = '{"status":"PASS"}\n'
    else:
        review.pop('raw', None)
    with pytest.raises(ValueError, match='captured|review|raw'):
        subject.admit_plan(plan, subject.ROLE)


def test_attempt2_cannot_skip_captured_remedy_at_native_admission(tmp_path, monkeypatch):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    policy = subject.authority()
    plan['recovery_attempt'] = 2
    plan['root'] = policy['closed_public_targets']['old_v2_CLOSED_UNUSED']
    plan['roles'][subject.ROLE]['argv'] = subject.load('p17_m2_source_binding').role_argv(
        plan['root'], 'payload', '@PLAN_SHA256@', subject.ROLE, plan['runtime']['python'],
        execution_identity=subject.IDENTITY)
    with pytest.raises(ValueError, match='attempt|closed'):
        subject.admit_plan(plan, subject.ROLE)


def test_pretty_review_bytes_are_bound_without_claiming_canonical_raw_sha(tmp_path, monkeypatch):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    refs = plan['entry']['reviews']
    report = refs['standards']['report']
    path = Path(refs['standards']['reference']['path'])
    raw = (json.dumps(report, indent=2) + '\n').encode()
    path.write_bytes(raw)
    captured = subject.review_readiness(subject.sha(raw), refs['spec']['reference']['sha256'])
    assert captured['standards']['raw'].encode() == raw
    assert subject.captured_value(captured['standards'], 'report') == report
    assert subject.sha(raw) != subject.sha(subject.canonical(report))


@pytest.mark.parametrize('historical', [False, True])
def test_closed_attempt2_cannot_enter_with_minimal_forged_remedy(
        tmp_path, monkeypatch, historical):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    policy = subject.authority()
    prior = subject._root('public', 1)
    prior_plan = {'root': str(prior), 'kind': 'public', 'recovery_attempt': 1,
                  'context': {'execution_identity': subject.IDENTITY}}
    prior_raw = subject.canonical(prior_plan)
    prior_sha = subject.sha(prior_raw)
    stop = {'status': 'STOP_NO_RETRY', 'plan_sha256': prior_sha}
    stop_raw = subject.canonical(stop)
    record = {'schema': 'topolab.v2.m2-strict-source-binding.recovery-remedy.v1',
              'execution_identity': subject.IDENTITY, 'kind': 'public', 'next_attempt': 2,
              'source_tree': plan['context']['source_tree'], 'prior_plan_sha256': prior_sha,
              'prior_STOP_sha256': subject.sha(stop_raw), 'prior_closure_actual': actual_packet(
                  subject, [plan['runtime']['python'], '-I', '-c', 'pass'], '/root', '', 1, 2)}
    raw = subject.canonical(record)
    plan['entry']['remedy'] = {'reference': {'path': policy['closed_remedy_paths']['public'],
        'sha256': subject.sha(raw)}, 'record': record, 'raw': raw.decode(),
        'prior_plan_capture': {'reference': {'path': str(prior / 'plan.json'),
            'sha256': prior_sha}, 'value': prior_plan, 'raw': prior_raw.decode()},
        'prior_STOP_capture': {'reference': {'path': str(prior / 'STOP.json'),
            'sha256': subject.sha(stop_raw)}, 'value': stop, 'raw': stop_raw.decode()}}
    plan['recovery_attempt'] = 2
    plan['root'] = policy['closed_public_targets']['old_v2_CLOSED_UNUSED']
    plan['roles'][subject.ROLE]['argv'] = subject.load('p17_m2_source_binding').role_argv(
        plan['root'], 'payload', '@PLAN_SHA256@', subject.ROLE, plan['runtime']['python'],
        execution_identity=subject.IDENTITY)
    with pytest.raises(ValueError, match='attempt|closed'):
        if historical:
            subject._plan_shape(plan, historical=True)
        else:
            subject.admit_plan(plan, subject.ROLE)


def test_prepare_attempt2_stops_before_reviews_or_any_target_io(monkeypatch):
    subject = module()
    monkeypatch.setattr(subject, 'review_readiness', lambda *args: pytest.fail('review read'))
    with pytest.raises(ValueError, match='attempt|closed'):
        subject.prepare('public', 2)


@pytest.mark.parametrize('entry', ['load', 'pair', 'public', 'preflight', 'argv'])
def test_all_closed_attempt2_io_entries_reject_before_metadata_read(monkeypatch, entry):
    subject = module()
    policy = subject.authority()
    core = subject.load('p17_m2_source_binding')
    monkeypatch.setattr(core, 'read_metadata', lambda *a, **kw: pytest.fail('closed target IO'))
    with pytest.raises(ValueError):
        if entry == 'load':
            path = Path(policy['closed_public_targets']['old_v2_CLOSED_UNUSED']) / 'plan.json'
            subject.load_plan(path, '1' * 64)
        elif entry == 'pair':
            subject.certificate_pair('public', 2, '1' * 64)
        elif entry == 'public':
            subject.public_readiness(2, '1' * 64, '2' * 64)
        elif entry == 'preflight':
            subject.preflight(2, '1' * 64, '2' * 64, standards_sha=None, spec_sha=None,
                              activation_sha='3' * 64)
        else:
            subject.preflight_argv(2, '1' * 64, '2' * 64, '3' * 64, '4' * 64, '5' * 64)


def test_real_collector_retains_full_failure_packet_through_recovery_writer_adapter(
        tmp_path, monkeypatch):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    root = Path(plan['root'])
    transport = subject.Transport(plan)
    # No process is launched: exercise the real missing-pending collector path.
    # Its complete failure packet still needs a trustworthy physical file record.
    packet = subject.load('p17_m2_content_verified_control').collect(
        root, projection['plan_sha256'], subject.ROLE, adapter=transport)
    retained = root / packet['full_collector_record']['path']
    raw = retained.read_bytes()
    assert packet['full_collector_record']['sha256'] == subject.sha(raw)
    assert packet['full_collector_record']['byte_size'] == len(raw)
    stages = {row['stage'] for row in packet['completion']['secondary_failures']}
    assert {'pending', 'collect'} <= stages
    assert 'collector write' not in stages and 'wire write' not in stages
    assert json.loads(raw)['pending'] == {}
    assert packet['completion']['status'] == 'FAILED_INTERNAL_COMPLETION'


@pytest.mark.parametrize('fault', ['missing-publication-close', 'late-publication-close',
                                   'software-close-after-hard-cap'])
def test_recovery_activation_replays_both_actual_stage_closures(tmp_path, monkeypatch, fault):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    policy = subject.authority()
    now = plan['started_unix_ns'] // 10**6
    argv = [plan['runtime']['python'], '-I', '-c', 'public_metadata_closure_fixture']
    software = actual_packet(subject, argv, '/root', '{}\n', now + 10000, now + 11000)
    publication = actual_packet(subject, argv, '/root', '{}\n', now + 12000, now + 13000)
    activation = {'schema': 'topolab.v2.m2-strict-source-binding.recovery-activation.v1',
        'execution_identity': subject.IDENTITY, 'software_source_tree': subject.source_freeze(),
        'started_ms': now + 13000, 'deadline_ms': now + 1213000,
        'software_closure_actual': software, 'publication_closure_actual': publication}
    if fault == 'missing-publication-close':
        del activation['publication_closure_actual']
    elif fault == 'late-publication-close':
        publication['responses'][0]['returned_ms'] = now + 7211001
        activation['started_ms'] = now + 7211001
        activation['deadline_ms'] = now + 8411001
    else:
        software['responses'][0]['returned_ms'] = policy['limits']['software_deadline_ms'] + 1
    raw = subject.canonical(activation)
    with pytest.raises((ValueError, KeyError)):
        subject._captured_activation(activation, raw.decode(), subject.sha(raw),
                                    plan['context']['source_tree'])


def test_recovery_writer_cannot_escape_its_root_through_parent_segments(tmp_path, monkeypatch):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    root = Path(plan['root'])
    escaped = root / '..' / 'outside-writer-check.json'
    with pytest.raises(ValueError):
        subject.load('p17_m2_source_binding').metadata_path_guard(escaped)
    with pytest.raises(ValueError):
        subject.Transport(plan).put(escaped, {'public_fixture_only': True})
    assert not (root.parent / 'outside-writer-check.json').exists()


@pytest.mark.parametrize('fault', ['dot', 'dotdot', 'outside'])
def test_recovery_writer_rejects_lexical_escape_before_namespace_io(tmp_path, monkeypatch, fault):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    transport = subject.Transport(plan)
    root = Path(plan['root'])
    monkeypatch.setattr(transport, 'namespace_check',
                        lambda *a, **kw: pytest.fail('unregistered namespace IO'))
    path = (str(root) + '/./blocked.json' if fault == 'dot' else
            root / '..' / 'blocked.json' if fault == 'dotdot' else root.parent / 'blocked.json')
    with pytest.raises(ValueError):
        transport.put(path, {'public_fixture_only': True})
    assert not (root.parent / 'blocked.json').exists()


@pytest.mark.parametrize('fault', ['budget-hash', 'activation-value', 'closure-return'])
def test_v16_captured_budget_chain_rejects_mutation_at_historical_and_native_entries(
        tmp_path, monkeypatch, fault):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    captures = plan['entry']['budget_evidence']
    if fault == 'budget-hash':
        captures['budget']['reference']['sha256'] = '0' * 64
    elif fault == 'activation-value':
        captures['software_activation']['value']['deadline_ms'] += 1
    else:
        captures['prior_failed_metadata_closure_actual']['value']['responses'][0][
            'result']['output'] = '{}\n'
    with pytest.raises(ValueError):
        subject._plan_shape(plan, historical=True)
    with pytest.raises(ValueError):
        subject.admit_plan(plan, subject.ROLE)


def test_captured_historical_cwd_never_admits_foreign_current_execution(tmp_path, monkeypatch):
    subject = module()
    _, bundle = captured_bundle(tmp_path)
    projection = public_preparation(subject, tmp_path, bundle, monkeypatch)
    plan = subject.load_plan(Path(projection['plan_path']), projection['plan_sha256'])
    plan['runtime']['cwd'] = '/private/tmp/historical-foreign-runtime-only'
    monkeypatch.setattr(subject, 'read_ref', lambda *a, **kw: pytest.fail('foreign runtime IO'))
    with pytest.raises(ValueError, match='runtime'):
        subject.admit_plan(plan, subject.ROLE)


def registration_fixture(subject, tmp_path, monkeypatch):
    envelope = recovered_envelope(subject, tmp_path, monkeypatch)
    certificate, audit = subject.verify_result_envelope(envelope)
    plan = envelope['metadata_plan']
    digest = subject.sha(subject.canonical(envelope))
    argv = [plan['runtime']['python'], '-I',
            str(REPO / 'scripts/p17_m2_source_binding_recovery.py'), 'finalize-result',
            '--plan', str(Path(plan['root']) / 'plan.json'),
            '--plan-sha', subject.sha(subject.canonical(plan))]
    started = plan['started_unix_ns'] // 10**6
    actual = actual_packet(subject, argv, '/root', subject.canonical(
        subject.finalize_summary(plan, certificate, audit, digest)).decode(),
        started + 20000, started + 21000)
    return envelope, actual, certificate, audit


def test_full_input_registration_requires_complete_metadata_and_final_actual_return(
        tmp_path, monkeypatch):
    subject = module()
    envelope, actual, certificate, proof = registration_fixture(subject, tmp_path, monkeypatch)
    assert subject.verify_registration(envelope, actual, kind='public') == (certificate, proof)
    with pytest.raises(ValueError, match='formal|scope|kind'):
        subject.verify_registration(envelope, actual)
    assert len(certificate['source_observations']) == 23
    assert set(certificate['source_observations'][0]['declared']) == {
        'st_dev', 'st_ino', 'st_size', 'st_mtime_ns'}


@pytest.mark.parametrize('fault', ['stdout', 'missing-terminal', 'wrong-author', 'before-auditor'])
def test_full_input_registration_rejects_unclosed_or_detached_finalize(
        tmp_path, monkeypatch, fault):
    subject = module()
    envelope, actual, _, proof = registration_fixture(subject, tmp_path, monkeypatch)
    if fault == 'stdout':
        actual['responses'][0]['result']['output'] = '{}\n'
    elif fault == 'missing-terminal':
        actual['responses'][0]['result'].pop('exit_code')
    elif fault == 'wrong-author':
        actual['author'] = '/root/closed-author'
    else:
        actual['responses'][0]['requested_ms'] = int(proof['T0'] * 1000) - 1
    with pytest.raises(ValueError):
        subject.verify_registration(envelope, actual, kind='public')


def test_recovery_fixture_never_creates_platform_literal_directories(tmp_path, monkeypatch):
    subject = module()
    original_mkdir = Path.mkdir

    def owned_mkdir(path, *args, **kwargs):
        assert path.is_relative_to(tmp_path), 'fixture directory outside test-owned tmp_path'
        return original_mkdir(path, *args, **kwargs)

    monkeypatch.setattr(Path, 'mkdir', owned_mkdir)
    _, bundle = captured_bundle(tmp_path)
    public_preparation(subject, tmp_path, bundle, monkeypatch)
