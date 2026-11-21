"""NEW input clock/command contracts using public in-memory records only."""

import importlib.util
import sys
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
INPUT = 'topolab.v2.p17-m2-registered-source-acquisition.20261121.v1'


@pytest.fixture(autouse=True)
def isolate_profile_module_cache():
    before = dict(sys.modules)
    yield
    for name in set(before) | set(sys.modules):
        if name.startswith(('p17_m2_', 'full60_', 'metadata_input_window_')):
            if name in before:
                sys.modules[name] = before[name]
            else:
                sys.modules.pop(name, None)


def module(name):
    path = ROOT / 'scripts' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    exec(compile(path.read_bytes(), str(path), 'exec'), value.__dict__)
    return value


@pytest.fixture
def profiles():
    return module('p17_m2_input_continuation')


def test_new_input_result_cannot_extend_the_original_whole4500():
    subject = module('p17_m2_content_verified_independent')
    first = 1795238460000
    whole_end = first + 4500000
    end_iso = datetime.fromtimestamp(whole_end / 1000, UTC).isoformat(
        timespec='milliseconds').replace('+00:00', 'Z')
    record = dict(execution_identity=INPUT, whole_start_ms=first, whole_end_ms=whole_end,
                  actor_activation_UTC_seconds=first / 1000,
                  result_start_UTC_seconds=(whole_end - 100000) / 1000,
                  result_deadlines_UTC={key: end_iso for key in ('exporter', 'independent')})
    assert subject._result_window(record, result_seconds=(1800, 1800)) == (
        (whole_end - 100000) / 1000, whole_end / 1000)
    record['result_deadlines_UTC']['exporter'] = datetime.fromtimestamp(
        (whole_end + 1800000) / 1000, UTC).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    with pytest.raises(ValueError, match='deadlines'):
        subject._result_window(record, result_seconds=(1800, 1800))


def test_new_authority_is_exactly_one_attempt_and_preserves_closed_history(profiles):
    registered = profiles.profile('registered', INPUT)
    policy = registered.authority()
    assert policy['input_limits']['attempts'] == 1
    assert policy['input_limits']['source_reads_all_input_attempts'] == 1196
    assert policy['input_limits']['FULL_all_input_attempts_ceiling'] == 3780
    assert policy['input_limits']['original_reads_including_closed_registration'] == 2484
    assert policy['input_limits']['registered_foundation_helpers_all'] == 138
    assert policy['new_Original_registration_reads'] == policy['new_Foundation_helpers'] == 0
    policy['input_limits']['source_reads_all_input_attempts'] = 2392
    with pytest.raises(ValueError, match='exact input'):
        registered.authority(registered.producer.canonical(policy))
    with pytest.raises(ValueError, match='attempt'):
        registered.formal_plan(registered.authority_raw(), attempt=2)


def test_new_routing_and_window_do_not_admit_old_alias_or_old_clock(profiles):
    control = profiles.profile('control', INPUT)
    registered = profiles.profile('registered', INPUT)
    selected = profiles.config(INPUT)
    for root in (selected['public_root'], *selected['generations']):
        assert control.registered_root(root) and registered.is_root(root)
    for root in (selected['public_root'] + '-other',
                 '/private/tmp/topolab-public-full60-source-acquisition-20261116-a1'):
        assert not control.registered_root(root) and not registered.is_root(root)
    window = profiles.window(INPUT)
    start = 1795238460000
    assert window.declare(start, start + 1000)['whole_end_ms'] == start + 4500000
    with pytest.raises(ValueError, match='whole'):
        window.declare(1794834000000, 1794834000000)
    with pytest.raises(ValueError, match='first-SUP'):
        window.declare(start, start + 30001)


def test_new_public_prepare_needs_formal_metadata_before_any_graph_io(profiles, monkeypatch):
    subject = profiles.profile('registered', INPUT)
    root = profiles.config(INPUT)['public_root']
    monkeypatch.setattr(subject.control, 'rehearsal_root',
                        lambda *_: pytest.fail('public graph guard entered before metadata'))
    monkeypatch.setattr(subject, '_registration_plan',
                        lambda *_a, **_k: pytest.fail('proof opened without formal reference'))
    with pytest.raises(ValueError, match='formal metadata'):
        subject.prepare_rehearsal(root, {})


def proof_fixture(subject):
    policy = subject.authority()
    references, blobs, envelopes = {}, {}, {}
    for kind in ('formal', 'public'):
        pin = policy['registration'][kind]
        source = ('/Users/keith1117/Documents/TopoLab-data' if kind == 'formal'
                  else '/private/tmp/declared-public-fixture-source')
        envelope = {'core_bundle': {'certificate': {'registered_context': {'source_root': source}}}}
        raw = subject.producer.canonical(envelope)
        actual = subject.producer.canonical({'declared_fixture': kind})
        references[kind] = dict(certificate_path=pin['certificate_paths'][0],
                                certificate_sha256=subject.producer.sha(raw),
                                finalize_actual_path=pin['finalize_actual_path'],
                                finalize_actual_sha256=subject.producer.sha(actual))
        blobs[pin['certificate_paths'][0]] = raw
        blobs[pin['finalize_actual_path']] = actual
        envelopes[kind] = envelope
    return policy, references, blobs, envelopes


def test_producer_replays_actual_formal_metadata_before_public_metadata(profiles, monkeypatch):
    subject = profiles.profile('registered', INPUT)
    _policy, references, blobs, envelopes = proof_fixture(subject)
    monkeypatch.setattr(subject, 'authority', lambda _raw=None: _policy)
    checker = subject.control.load('p17_m2_source_acquisition_independent')
    reads = []

    def read(path):
        reads.append(str(path))
        return blobs[str(path)]

    monkeypatch.setattr(checker.native, '_software_bytes', read)
    recovery = subject.control.load('p17_m2_source_binding_recovery')
    monkeypatch.setattr(recovery, 'certificate_pair', lambda kind, _attempt, _sha: (
        envelopes[kind], [Path(p) for p in subject.authority()['registration'][kind][
            'certificate_paths']]))
    calls = []

    def verify(envelope, actual, *, kind):
        assert actual == {'declared_fixture': kind}
        calls.append(kind)
        return envelope['core_bundle']['certificate'], {'full_role_evidence_accepted': True}

    monkeypatch.setattr(recovery, 'verify_registration', verify)
    monkeypatch.setattr(subject, 'registration_bindings', lambda _certificate: {})
    plan = dict(execution_identity=INPUT, source_identity_policy=subject.POLICY,
                scope=subject.control.REHEARSAL_SCOPE,
                source_root='/private/tmp/declared-public-fixture-source',
                binding=dict(strict23_registration=references['public'],
                             formal_strict23_registration=references['formal']))
    subject.trusted_registration(plan)
    assert calls == ['formal', 'public']
    assert reads.count(references['formal']['certificate_path']) == 1
    calls.clear()
    plan['binding']['formal_strict23_registration']['finalize_actual_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='proof SHA'):
        subject.trusted_registration(plan)
    assert calls == []


def test_new_prepare_suffix_binds_both_actual_metadata_proofs(profiles):
    subject = profiles.profile('independent', INPUT)
    first = profiles.window(INPUT).START_MS
    plan = dict(execution_identity=INPUT, scope=subject.REHEARSAL_SCOPE,
                whole_start_ms=first, whole_end_ms=first + 4500000,
                actor_activation_UTC_seconds=first / 1000,
                binding=dict(strict23_registration=dict(certificate_sha256='a' * 64,
                             finalize_actual_sha256='b' * 64),
                             formal_strict23_registration=dict(certificate_sha256='c' * 64,
                             finalize_actual_sha256='d' * 64)))
    assert subject.public_prepare_suffix(plan) == (
        '--registration-certificate-sha', 'a' * 64,
        '--registration-finalize-actual-sha', 'b' * 64,
        '--formal-registration-certificate-sha', 'c' * 64,
        '--formal-registration-finalize-actual-sha', 'd' * 64,
        '--whole-start-ms', str(first))
    del plan['binding']['formal_strict23_registration']
    with pytest.raises(ValueError, match='formal metadata'):
        subject.public_prepare_suffix(plan)


def test_independent_public_certificate_replay_uses_new_neutral_entry(profiles, monkeypatch):
    subject = profiles.profile('independent', INPUT)
    registered = profiles.profile('registered', INPUT)
    policy = registered.authority()
    root = policy['public_roots'][0]
    raw = b'fixture-actual-packet'
    source_tree = {'declared-software-fixture': 'a' * 64}
    runtime = {'python': '/declared/python', 'cwd': '/declared/repo'}
    plan = dict(scope=subject.FORMAL_SCOPE, source_tree=source_tree, runtime=runtime,
                activation_readiness={'path': policy['readiness_path'], 'sha256': 'b' * 64},
                independent_preflight={'path': policy['independent_preflight_actual_path'],
                                       'sha256': subject.digest(raw)})
    public_plan = dict(execution_identity=INPUT, scope=subject.REHEARSAL_SCOPE,
                       source_tree=source_tree, root=root)
    ready = dict(schema='topolab.registered-input.activation-readiness.v1',
                 execution_identity=INPUT, actors=policy['actors'], runtime=runtime,
                 new_input_budget=policy['new_input_budget'], published_source_sha256=source_tree,
                 public_native_acceptance={'path': root + '/accepted-acquisition-bundle.json'},
                 public_certificate_actual={'path': root + '/' + policy[
                     'public_certificate_actual_name']})
    monkeypatch.setattr(subject, '_registered_authority', lambda _: policy)
    monkeypatch.setattr(subject, '_registered_read_pin', lambda reference: ready if reference[
        'path'] == policy['readiness_path'] else {})
    monkeypatch.setattr(subject, 'audit_certificate', lambda *_a, **_k: None)
    seen = []

    def exact_actual(_actual, argv, author):
        seen.append((argv, author))
        raise LookupError('captured exact actual argv without IO')

    original = subject.helper

    def helper(key, filename):
        if key == 'registered_public_serialization':
            return SimpleNamespace(evidence_json=lambda *_a, **_k: {
                'bundle': {'plan': public_plan}, 'events': {}})
        if key == 'registered_preflight_return':
            return SimpleNamespace(exact_actual=exact_actual)
        return original(key, filename)

    monkeypatch.setattr(subject, 'helper', helper)
    with pytest.raises(LookupError, match='captured exact actual'):
        subject._registered_preflight(plan, raw)
    assert seen == [([
        '/declared/python', '-I', '/declared/repo/scripts/input_control_20261121.py',
        'certify-rehearsal', '--root', root, '--plan-sha', subject.digest(
            subject.canonical(public_plan)), '--role', 'certificate'],
        policy['actors']['executor'])]


@pytest.mark.parametrize('key', ['certificate_path', 'finalize_actual_path'])
def test_registration_rejects_foreign_literal_before_open(profiles, monkeypatch, key):
    subject = profiles.profile('registered', INPUT)
    policy = subject.authority()
    monkeypatch.setattr(subject, 'authority', lambda _raw=None: policy)
    reference = subject.registration_reference('formal', 'a' * 64, 'b' * 64)
    reference[key] = '/declared/forbidden-formal-target'
    checker = subject.control.load('p17_m2_source_acquisition_independent')
    monkeypatch.setattr(checker.native, '_software_bytes',
                        lambda *_a: pytest.fail('foreign literal reached file open'))
    plan = dict(execution_identity=INPUT, source_identity_policy=subject.POLICY,
                scope=subject.control.FORMAL_SCOPE,
                binding={'strict23_registration': reference})
    with pytest.raises(ValueError, match='frozen proof paths'):
        subject.trusted_registration(plan)
    with pytest.raises(ValueError, match='frozen proof paths'):
        subject._registration_plan(None, 'formal', reference)


@pytest.mark.parametrize('role', ['exporter-r1', 'independent-r1'])
def test_new_r1_stops_without_actual_independent_r0_before_payload_reader(
        profiles, monkeypatch, tmp_path, role):
    control = profiles.profile('control', INPUT)
    root = Path(profiles.config(INPUT)['public_root'])
    transport = control.AcquisitionTransport(root, 'a' * 64)
    assert transport.identity == INPUT
    helper = control.base()
    helper.put(tmp_path / 'independent-r0-accepted.json', {'raw_tool_events': ['FIXTURE_ONLY']})
    (tmp_path / 'receipts').mkdir(mode=0o700)
    helper.put(tmp_path / 'receipts/independent-r0-wire.json', {'declared_fixture': True})
    monkeypatch.setattr(control.AcquisitionTransport, 'resource_evidence', lambda *_a: {})
    monkeypatch.setattr(control.AcquisitionTransport, 'audit_saved',
                        lambda *_a, **_k: {'full_role_evidence_accepted': False})
    monkeypatch.setattr(control.AcquisitionTransport, 'source_reader',
                        lambda *_a, **_k: pytest.fail('R1 source reader entered before R0'))
    monkeypatch.setattr(control.AcquisitionTransport, 'put', lambda *_a: None)
    plan = dict(execution_identity=INPUT, source_root='/declared/never-opened-source',
                content_contract={})
    result = control.payload_body(tmp_path, plan, role, transport)
    assert result['status'] == 'STOP_NO_RETRY'
    assert result['reason'] == 'R0_REGISTRY_NATIVE_ACCEPTANCE_REQUIRED'
    assert result['attempted_source_paths'] == []
    assert result['independent_context']['original_payload_reads'] == 0
    assert result['independent_context']['metadata_reader']['attempts'] == [
        'independent-r0-accepted.json', 'receipts/independent-r0-wire.json']


def test_new_independent_compiler_and_producer_freeze_same_complete_sources(profiles, monkeypatch):
    subject = profiles.profile('independent', INPUT)
    first = profiles.window(INPUT).START_MS
    captured = {}

    def capture(_plan, **kwargs):
        captured.update(kwargs)
        raise LookupError('source compiler captured before any runtime or metadata IO')

    monkeypatch.setattr(subject, 'validate_binding', lambda _plan: None)
    monkeypatch.setattr(subject.native, '_check_software', capture)
    plan = dict(execution_identity=INPUT, scope=subject.REHEARSAL_SCOPE,
                source_identity_policy=subject.HASH_BOUND_POLICY,
                whole_start_ms=first, whole_end_ms=first + 4500000,
                actor_activation_UTC_seconds=first / 1000,
                binding=dict(source_identity_policy=subject.HASH_BOUND_POLICY,
                             authority_protocol_path=subject.REGISTERED_PROTOCOL,
                             strict23_registration=dict(certificate_sha256='a' * 64,
                                                        finalize_actual_sha256='b' * 64),
                             formal_strict23_registration=dict(certificate_sha256='c' * 64,
                                                               finalize_actual_sha256='d' * 64)))
    with pytest.raises(LookupError, match='compiler captured'):
        subject._check_software(plan)
    assert captured['controller'] == 'input_control_20261121.py'
    assert captured['prepare_mode'] == 'prepare-rehearsal'
    required = {'scripts/metadata_input_window_20261121.py',
                'scripts/input_control_20261121.py', 'scripts/registered_input_20261121.py',
                'scripts/binding_recovery_20261121.py', 'scripts/input_preparation_20261121.py',
                'scripts/await_input_receipt_20261121.py', 'scripts/file_input_event_20261121.py',
                'scripts/full60_input_loader.py', 'scripts/full60_public_capability.py',
                'scripts/full60_input_actual_boundary.mjs', 'scripts/full60_input_cohort.mjs',
                'scripts/build_input_caller_20261121.py',
                'docs/planning/input_review_20261121.json'}
    assert required <= set(captured['contracts'])
    closure = subject.native._software_closure(ROOT, contracts=captured['contracts'])
    assert closure == profiles.profile('control', INPUT).source_freeze(INPUT)
    assert all(closure[name] == subject.digest((ROOT / name).read_bytes()) for name in required)


def test_independent_replay_reuses_only_one_validation_and_clears_failure(profiles, monkeypatch):
    subject = profiles.profile('independent', INPUT)
    registered = profiles.profile('registered', INPUT)
    policy, references, blobs, envelopes = proof_fixture(registered)
    calls = []

    def verify(envelope, actual, *, kind):
        assert actual == {'declared_fixture': kind}
        calls.append(kind)
        return envelope['core_bundle']['certificate'], {}

    recovery = SimpleNamespace(
        authority=lambda: {'certificate_paths': {kind: [policy['registration'][kind][
            'certificate_paths']] for kind in ('public', 'formal')}},
        _root=lambda kind, _attempt: Path(policy['registration'][kind][
            'finalize_actual_path']).parent,
        certificate_pair=lambda kind, _attempt, _sha: (envelopes[kind], []),
        verify_registration=verify)
    original = subject.helper
    monkeypatch.setattr(subject, 'helper', lambda key, filename: recovery if key ==
                        'registered_recovery_audit' else original(key, filename))
    monkeypatch.setattr(subject.native, '_software_bytes', lambda path: blobs[str(path)])
    monkeypatch.setattr(subject, 'registered_source_bindings', lambda _: {})
    first = profiles.window(INPUT).START_MS
    plan = dict(execution_identity=INPUT, scope=subject.REHEARSAL_SCOPE,
                source_root='/private/tmp/declared-public-fixture-source',
                whole_start_ms=first, whole_end_ms=first + 4500000,
                actor_activation_UTC_seconds=first / 1000,
                binding=dict(strict23_registration=references['public'],
                             formal_strict23_registration=references['formal']))
    fail = False

    def validate(value):
        assert subject._REGISTERED_SOURCE_REPLAY.get() == {}
        for _ in range(4):
            subject._trusted_registered_sources(value)
        assert len(subject._REGISTERED_SOURCE_REPLAY.get()) == 2
        forged = deepcopy(value)
        forged['binding']['formal_strict23_registration']['finalize_actual_sha256'] = '0' * 64
        with pytest.raises(ValueError, match='finalize actual buffer SHA'):
            subject._trusted_registered_sources(forged)
        assert len(subject._REGISTERED_SOURCE_REPLAY.get()) == 2
        if fail:
            raise ValueError('declared validation failure after proof replay')
        return value['binding']

    monkeypatch.setattr(subject, '_validate_hash_bound_binding', validate)
    subject.validate_binding(plan)
    assert calls == ['formal', 'public']
    assert subject._REGISTERED_SOURCE_REPLAY.get() is None
    fail = True
    with pytest.raises(ValueError, match='declared validation failure'):
        subject.validate_binding(plan)
    assert calls == ['formal', 'public', 'formal', 'public']
    assert subject._REGISTERED_SOURCE_REPLAY.get() is None


def test_new_entry_rejects_old_or_aliased_root_before_routing_or_clock(profiles, monkeypatch):
    subject = profiles.profile('control', INPUT)
    for root in ('/private/tmp/topolab-public-full60-source-acquisition-20261116-a1',
                 profiles.config(INPUT)['public_root'].replace('/private/tmp', '/private//tmp')):
        monkeypatch.setattr(sys, 'argv', ['input_control_20261121.py', 'prepare-rehearsal',
                                         '--root', root])
        with pytest.raises(ValueError, match='NEW_INPUT_LITERAL_ROOT_REQUIRED'):
            subject.main()
