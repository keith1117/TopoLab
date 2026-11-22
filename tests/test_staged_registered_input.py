"""Staged INPUT uses public in-memory registration facts, never live source paths."""

import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).resolve().parents[1]
IDENTITY = 'topolab.v2.p17-m2-registered-source-acquisition.staged-20261121.v1'
BINDING = 'topolab.public-local-strict23.staged-20261121.v1'


def load(name):
    if name == 'p17_m2_resource_control' and 'p17_m2_homotopy' not in sys.modules:
        load('p17_m2_homotopy')
    path = REPO / 'scripts' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


@pytest.fixture(autouse=True)
def isolate_module_cache():
    before = dict(sys.modules)
    yield
    for name in set(before) | set(sys.modules):
        if name.startswith(('p17_m2_', 'full60_', 'staged_')):
            if name in before:
                sys.modules[name] = before[name]
            else:
                sys.modules.pop(name, None)


@pytest.fixture
def profiles(tmp_path, monkeypatch):
    value = load('p17_m2_input_continuation')
    evidence = tmp_path / 'default-software-evidence'
    evidence.mkdir(mode=0o700)
    evidence.with_name(evidence.name + '-backup').mkdir(mode=0o700)
    monkeypatch.setattr(value, 'STAGED_EVIDENCE', str(evidence))
    monkeypatch.setitem(value.config(IDENTITY), 'evidence_root', str(evidence))
    formal = tmp_path / 'formal-software-evidence'
    formal.mkdir(mode=0o700)
    formal.with_name(formal.name + '-backup').mkdir(mode=0o700)
    monkeypatch.setitem(value.config(value.FORMAL_INPUT), 'evidence_root', str(formal))
    return value


def test_staged_profile_has_its_original_window_and_literal_roots(profiles):
    profile = profiles.config(IDENTITY)
    assert profiles.is_whole_input(IDENTITY)
    assert profiles.config(profiles.NOV21_INPUT)['global_deadline_ms'] == 1795281660000
    assert profile['global_deadline_ms'] == 1795351200000
    assert profiles.config_for_root(profile['public_root']) is profile
    assert profiles.config_for_root(profile['public_root'] + '-unregistered') is None
    window = profiles.window(IDENTITY)
    original = 1795293600000
    plan = window.declare(original, original + 1000)
    assert plan == {'whole_start_ms': original, 'whole_end_ms': original + 4500000}
    assert window.result_end(plan, original + 4400000) == original + 4500000
    with pytest.raises(ValueError, match='first-SUP'):
        window.declare(original, original + 30001)
    with pytest.raises(ValueError, match='whole'):
        window.check(plan, plan['whole_end_ms'] + 1)


def test_staged_authority_does_not_transfer_closed_quotas(profiles):
    subject = profiles.profile('registered', IDENTITY)
    policy = subject.authority()
    assert policy['input_limits']['attempts'] == 1
    assert policy['input_limits']['source_reads_all_input_attempts'] == 1196
    assert policy['input_limits']['FULL_each_input_ceiling'] == 3780
    assert policy['ancillary_named_FULL']['lease_release_each_graph'] == 180
    assert policy['ancillary_named_FULL']['new_FULL_ceiling'] == 9120
    assert policy['new_Original_registration_reads'] == policy['new_Foundation_helpers'] == 0
    assert policy['historical_known_FULL_floor'] == 337539
    policy['input_limits']['attempts'] = 2
    with pytest.raises(ValueError, match='exact input'):
        subject.authority(subject.producer.canonical(policy))


def test_staged_missing_formal_proof_stops_before_any_graph_guard(profiles, monkeypatch):
    subject = profiles.profile('registered', IDENTITY)
    monkeypatch.setattr(subject.control, 'rehearsal_root',
                        lambda *_a: pytest.fail('graph inspected before formal metadata'))
    with pytest.raises(ValueError, match='formal metadata'):
        subject.prepare_rehearsal(profiles.config(IDENTITY)['public_root'], {})


@pytest.fixture
def registration_fixture(profiles, monkeypatch):
    subject = profiles.profile('registered', IDENTITY)
    independent = profiles.profile('independent', IDENTITY)
    policy = subject.authority()
    specs = subject.control.load('p17_m2_source_binding_independent').metadata_specs()
    packets, references, facts, observed = {}, {}, {}, []
    for kind in ('public', 'formal'):
        source = (profiles.config(IDENTITY)['public_source'] if kind == 'public'
                  else '/Users/keith1117/Documents/TopoLab-data')
        context = {'source_root': source, 'declared_unit_fixture': kind}
        rows = []
        for index, spec in enumerate(specs):
            raw = ('declared-fixture-' + str(index)).encode()
            physical = dict(st_dev=11, st_ino=index + 100, st_size=len(raw), st_mtime_ns=123456)
            rows.append(dict(path=spec['path'], byte_size=len(raw),
                             sha256=hashlib.sha256(raw).hexdigest(),
                             **{point: dict(physical) for point in
                                ('declared', 'before', 'after', 'closing')}))
        envelope = dict(core_bundle={'certificate': {
            'registered_context': context, 'source_observations': rows}})
        raw = subject.producer.canonical(envelope)
        # Intentional spaces ensure replay receives exact bytes, not reserialization.
        actual = json.dumps({'declared_fixture_actual': kind}, indent=2).encode() + b'\n'
        pin = policy['registration'][kind]
        pin['certificate_sha256'] = subject.producer.sha(raw)
        pin['finalize_actual_sha256'] = subject.producer.sha(actual)
        references[kind] = dict(certificate_path=pin['certificate_paths'][0],
                                certificate_sha256=pin['certificate_sha256'],
                                finalize_actual_path=pin['finalize_actual_path'],
                                finalize_actual_sha256=pin['finalize_actual_sha256'])
        packets[pin['certificate_paths'][0]] = raw
        packets[pin['finalize_actual_path']] = actual
        facts[kind] = context, rows
    packets[str(REPO / subject.PROTOCOL)] = subject.producer.canonical(policy)
    checker = subject.control.load('p17_m2_source_acquisition_independent')
    monkeypatch.setattr(checker.native, '_software_bytes', lambda path: packets[str(path)])
    monkeypatch.setattr(independent.native, '_software_bytes', lambda path: packets[str(path)])

    def replay(kind, *, certificate_raw, finalize_actual_raw):
        pin = policy['registration'][kind]
        assert certificate_raw is packets[pin['certificate_paths'][0]]
        assert finalize_actual_raw is packets[pin['finalize_actual_path']]
        observed.append(kind)
        return deepcopy(facts[kind])

    helper = SimpleNamespace(
        verified_registration=lambda **kwargs: replay('public', **kwargs),
        verified_formal_registration=lambda **kwargs: replay('formal', **kwargs))
    original = subject.control.load
    monkeypatch.setattr(subject.control, 'load', lambda name: helper if name ==
                        'staged_public_binding' else original(name))
    original_independent = independent.helper
    monkeypatch.setattr(independent, 'helper', lambda name, filename: helper if name ==
                        'staged_registration_replay' else original_independent(name, filename))
    plan = dict(execution_identity=IDENTITY, scope=subject.control.REHEARSAL_SCOPE,
                source_identity_policy=subject.POLICY,
                source_root=profiles.config(IDENTITY)['public_source'],
                binding=dict(strict23_registration=references['public'],
                             formal_strict23_registration=references['formal']))
    return subject, independent, plan, references, packets, helper, observed


@pytest.mark.parametrize('side', ['producer', 'independent'])
def test_both_consumers_replay_both_exact_raw_buffers_without_source_io(registration_fixture, side):
    producer, independent, plan, _references, _packets, _helper, calls = registration_fixture
    certificate, rows = (producer.trusted_registration(plan) if side == 'producer'
                         else independent._trusted_registered_sources(plan))
    assert calls == ['formal', 'public']
    assert len(rows) == len(certificate['source_observations']) == 23
    assert all(set(value) == {'sha256', 'byte_size', 'declared'} for value in rows.values())


@pytest.mark.parametrize('side', ['producer', 'independent'])
def test_changed_staged_source_facts_cannot_borrow_valid_actual(registration_fixture, side):
    producer, independent, plan, _references, _packets, helper, _calls = registration_fixture
    original = helper.verified_registration

    def changed(**kwargs):
        context, observations = original(**kwargs)
        observations[0]['sha256'] = 'f' * 64
        return context, observations

    helper.verified_registration = changed
    with pytest.raises(ValueError, match='same-buffer'):
        if side == 'producer':
            producer.trusted_registration(plan)
        else:
            independent._trusted_registered_sources(plan)


def test_staged_uses_real_proof_hashes_in_original_prepare_argv(profiles):
    subject = profiles.profile('independent', IDENTITY)
    first = profiles.window(IDENTITY).START_MS
    plan = dict(execution_identity=IDENTITY, scope=subject.REHEARSAL_SCOPE,
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


@pytest.mark.parametrize('scope', ['public', 'formal'])
def test_staged_input_native_allowlist_stops_before_any_native_dispatch(profiles, monkeypatch,
                                                                      tmp_path, scope):
    resource = load('p17_m2_resource_control')
    config = profiles.config(IDENTITY)
    root = config['public_root'] if scope == 'public' else config['generations'][0]
    measurement = ('FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY' if scope == 'public'
                   else 'SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY')
    argv = [str(Path(sys.orig_argv[0]).resolve()), '-I',
            str(REPO / 'scripts/staged_input_control.py'),
            'payload', '--root', root, '--plan-sha', 'a' * 64, '--role', 'exporter-r0']

    def no_dispatch(*_a, **_k):
        raise LookupError('validated software guard; native remains unopened')

    monkeypatch.setattr(Path, 'mkdir', no_dispatch)
    with pytest.raises(LookupError, match='validated software guard'):
        resource.invoke(tmp_path, 'exporter-r0', argv, timeout=300,
                        measurement_scope=measurement, measurement_execution_identity=IDENTITY)
    argv[5] += '-other'
    with pytest.raises(ValueError, match='exact neutral'):
        resource.invoke(tmp_path, 'exporter-r0', argv, timeout=300,
                        measurement_scope=measurement, measurement_execution_identity=IDENTITY)


def test_staged_binding_guard_exact_venv_scope_and_six_roles(monkeypatch, tmp_path):
    resource = load('p17_m2_resource_control')

    def no_dispatch(*_a, **_k):
        raise LookupError('binding guard accepted; native remains unopened')

    monkeypatch.setattr(Path, 'mkdir', no_dispatch)
    for role in ('producer-availability', 'independent-availability', 'binding-producer',
                 'binding-independent', 'binding-closeout', 'binding-certificate-auditor'):
        argv = [str(REPO / '.venv/bin/python'), '-I',
                str(REPO / 'scripts/staged_public_binding.py'),
                'payload', role]
        with pytest.raises(LookupError, match='binding guard accepted'):
            resource.invoke(tmp_path, role, argv, timeout=120,
                            measurement_scope='STAGED_LOCAL_PUBLIC_STRICT23_ONLY',
                            measurement_execution_identity=BINDING)
        for changed in (['/wrong/python', *argv[1:]], [*argv, '--extra']):
            with pytest.raises(ValueError, match='staged binding measurement'):
                resource.invoke(tmp_path, role, changed, timeout=120,
                                measurement_scope='STAGED_LOCAL_PUBLIC_STRICT23_ONLY',
                                measurement_execution_identity=BINDING)


@pytest.mark.parametrize('staged', [True, False])
def test_shared_reservation_survives_staged_predecessor_failure_only(
        staged, monkeypatch, tmp_path):
    subject = load('p17_m2_content_verified_control')
    identity = IDENTITY if staged else 'topolab.v2.p17-m2-content-verified-input.v1'

    def predecessor(*_a):
        raise ValueError('declared predecessor refusal before dispatch')

    transport = SimpleNamespace(identity=identity, scope='DECLARED_PUBLIC_FIXTURE',
                                predecessor=predecessor, put=subject.put)
    with pytest.raises(ValueError, match='declared predecessor refusal'):
        subject.supervise(tmp_path, {'execution_identity': identity}, 'a' * 64,
                          'exporter-r0', adapter=transport)
    path = tmp_path / 'ledger-reservation.json'
    assert path.exists() is staged
    if staged:
        record = subject.read_json(path)
        assert record['shared_reserved_FULL_seconds'] == 300
        assert record['refunds_allowed'] is False
        assert record['plan_sha256'] == 'a' * 64
    assert not (tmp_path / 'active.json').exists()
    assert not (tmp_path / 'exporter-r0-dispatch-charge.json').exists()


@pytest.mark.parametrize('side', ['producer', 'independent'])
def test_invalid_scope_never_replays_registration(registration_fixture, side):
    producer, independent, plan, _refs, _packets, _helper, calls = registration_fixture
    plan['scope'] = 'UNREGISTERED_SCOPE'
    with pytest.raises(ValueError, match='scope'):
        if side == 'producer':
            producer.trusted_registration(plan)
        else:
            independent._trusted_registered_sources(plan)
    assert calls == []


def test_staged_compiler_and_producer_freeze_complete_actual_programs(profiles, monkeypatch):
    subject = profiles.profile('independent', IDENTITY)
    captured = {}

    def capture(_plan, **kwargs):
        captured.update(kwargs)
        raise LookupError('captured compiler before metadata/native IO')

    monkeypatch.setattr(subject, 'validate_binding', lambda _plan: None)
    monkeypatch.setattr(subject.native, '_check_software', capture)
    first = profiles.window(IDENTITY).START_MS
    plan = dict(execution_identity=IDENTITY, scope=subject.REHEARSAL_SCOPE,
                source_identity_policy=subject.HASH_BOUND_POLICY,
                whole_start_ms=first, whole_end_ms=first + 4500000,
                actor_activation_UTC_seconds=first / 1000,
                binding=dict(source_identity_policy=subject.HASH_BOUND_POLICY,
                             authority_protocol_path=subject.REGISTERED_PROTOCOL,
                             strict23_registration=dict(certificate_sha256='a' * 64,
                                                        finalize_actual_sha256='b' * 64),
                             formal_strict23_registration=dict(certificate_sha256='c' * 64,
                                                               finalize_actual_sha256='d' * 64)))
    with pytest.raises(LookupError, match='captured compiler'):
        subject._check_software(plan)
    required = {'scripts/' + name for name in (
        'staged_input_control.py', 'staged_registered_input.py', 'staged_input_preparation.py',
        'staged_input_window.py', 'staged_input_actor.mjs', 'staged_input_waiter.py',
        'staged_input_filer.py', 'build_staged_input_caller.py',
        *profiles.config(IDENTITY)['registration_helpers'])}
    required |= {'docs/planning/staged_registered_input_contract.json',
                 'docs/planning/staged_public_binding_contract.json'}
    assert required <= set(captured['contracts'])
    assert captured['controller'] == 'staged_input_control.py'
    closure = subject.native._software_closure(REPO, contracts=captured['contracts'])
    assert closure == profiles.profile('control', IDENTITY).source_freeze(IDENTITY)
    assert all(closure[name] == subject.digest((REPO / name).read_bytes()) for name in required)


def test_real_isolated_entry_imports_frozen_registration_helpers_without_source_io():
    import subprocess

    code = '''import json,runpy,sys
from pathlib import Path
ns=runpy.run_path(ENTRY,run_name='source_free_import_test')
import staged_binding_evidence,staged_binding_source,staged_public_binding_independent
import staged_public_binding,numpy,scipy,pydantic
modules=(staged_binding_evidence,staged_binding_source,staged_public_binding_independent,
         staged_public_binding)
print(json.dumps({'identity':ns['subject'].IDENTITY,'isolated':sys.flags.isolated,
 'helpers':[m.__file__ for m in modules],
 'dependencies':[m.__file__ for m in (numpy,scipy,pydantic)]}))
'''.replace('ENTRY', repr(str(REPO / 'scripts/staged_registered_input.py')))
    result = subprocess.run([str(Path(sys.executable).resolve()), '-I', '-c', code],
                            cwd=REPO, capture_output=True, text=True, timeout=15)
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value['identity'] == IDENTITY and value['isolated'] == 1
    assert {Path(p).parent for p in value['helpers']} == {REPO / 'scripts'}
    assert all(Path(p).is_relative_to(REPO / '.venv') for p in value['dependencies'])


@pytest.mark.parametrize('backup', [False, True])
@pytest.mark.parametrize('kind', ['empty', 'partial', 'null', 'symlink', 'directory', 'fifo'])
def test_either_public_stop_copy_vetoes_every_admission_entry_before_proof_or_target(
        profiles, monkeypatch, tmp_path, backup, kind):
    import os
    import runpy

    subject = profiles.profile('registered', IDENTITY)
    independent = profiles.profile('independent', IDENTITY)
    evidence = tmp_path / 'declared-evidence'
    peer = evidence.with_name(evidence.name + '-backup')
    evidence.mkdir(mode=0o700)
    peer.mkdir(mode=0o700)
    monkeypatch.setitem(profiles.config(IDENTITY), 'evidence_root', str(evidence))
    marker = (peer if backup else evidence) / 'input-public-caller-STOP.json'
    if kind == 'empty':
        marker.write_bytes(b'')
    elif kind == 'partial':
        marker.write_bytes(b'{"incomplete":')
    elif kind == 'null':
        marker.write_bytes(b'null\n')
    elif kind == 'symlink':
        marker.symlink_to('missing-target')
    elif kind == 'directory':
        marker.mkdir()
    else:
        os.mkfifo(marker)
    monkeypatch.setattr(subject, 'authority',
                        lambda *_a: pytest.fail('STOP ignored before authority/proof'))
    monkeypatch.setattr(independent, '_registered_authority',
                        lambda *_a: pytest.fail('STOP ignored before formal preflight'))
    prepare = runpy.run_path(str(REPO / 'scripts/staged_input_preparation.py'))
    entries = [
        lambda: subject.prepare_rehearsal(profiles.config(IDENTITY)['public_root'], {}),
        lambda: subject.readiness_inputs({}),
        lambda: subject.activation_readiness({}, {}),
        lambda: subject.publication_readiness({}),
        lambda: subject.activate_formal(subject.GENERATIONS[0], {}),
        lambda: independent._registered_preflight({}, b''),
        lambda: prepare['public_proof'](subject, {}),
        lambda: prepare['prepare'](subject, 'retain'),
    ]
    for entry in entries:
        with pytest.raises(ValueError, match='STAGED_PUBLIC_STOP_VETO'):
            entry()


def test_staged_activation_rechecks_stop_after_readiness_before_setup(
        profiles, monkeypatch, tmp_path):
    subject = profiles.profile('registered', IDENTITY)
    independent = profiles.profile('independent', IDENTITY)
    evidence = tmp_path / 'declared-evidence'
    evidence.mkdir(mode=0o700)
    evidence.with_name(evidence.name + '-backup').mkdir(mode=0o700)
    monkeypatch.setitem(profiles.config(IDENTITY), 'evidence_root', str(evidence))
    monkeypatch.setattr(subject, 'formal_plan', lambda *_a, **_k: {})
    monkeypatch.setattr(independent, 'validate_binding', lambda *_a: None)
    monkeypatch.setattr(subject.control, 'setup_formal',
                        lambda *_a: pytest.fail('target setup entered after public STOP'))

    def ready(*_a):
        (evidence / 'input-public-caller-STOP.json').write_bytes(b'')
        return dict(readiness_reference={}, independent_preflight_reference={})

    monkeypatch.setattr(subject, 'activation_readiness', ready)
    with pytest.raises(ValueError, match='STAGED_PUBLIC_STOP_VETO'):
        subject.activate_formal(subject.GENERATIONS[0], {})


def test_old_profiles_do_not_enter_staged_stop_namespace(profiles, monkeypatch):
    subject = profiles.profile('registered', profiles.NOV21_INPUT)
    monkeypatch.setattr(subject.control, 'base',
                        lambda: pytest.fail('old profile touched staged stop namespace'))
    assert subject.public_stop_veto() is None


def test_absent_stop_allows_independent_preflight_to_reach_its_own_authority(profiles, monkeypatch):
    subject = profiles.profile('registered', IDENTITY)
    independent = profiles.profile('independent', IDENTITY)
    assert subject.public_stop_veto() is None

    def authority(_plan):
        raise LookupError('independent authority reached with no retained STOP')

    monkeypatch.setattr(independent, '_registered_authority', authority)
    with pytest.raises(LookupError, match='independent authority reached'):
        independent._registered_preflight({}, b'')


def test_unobservable_stop_copy_namespace_fails_closed(profiles):
    subject = profiles.profile('registered', IDENTITY)
    evidence = Path(profiles.config(IDENTITY)['evidence_root'])
    evidence.with_name(evidence.name + '-backup').rmdir()
    with pytest.raises((OSError, ValueError)):
        subject.public_stop_veto()


@pytest.mark.parametrize("current", [False, True], ids=["staged", "formal-only"])
def test_formal_activation_and_independent_verifier_use_indented_published_bytes(
        profiles, monkeypatch, tmp_path, current):
    """Exercise the activation builder and verifier together, up to the custody boundary."""
    identity = profiles.FORMAL_INPUT if current else IDENTITY
    if current:
        old = profiles.config(IDENTITY)['evidence_root']
        monkeypatch.setattr(profiles, 'STAGED_EVIDENCE', old)
        evidence = tmp_path / 'new-formal-metadata'
        evidence.mkdir(mode=0o700)
        evidence.with_name(evidence.name + '-backup').mkdir(mode=0o700)
        monkeypatch.setitem(profiles.config(identity), 'evidence_root', str(evidence))
    subject = profiles.profile('registered', identity)
    checker = profiles.profile('independent', identity)
    published = (REPO / subject.PROTOCOL).read_bytes()
    expected = hashlib.sha256(published).hexdigest()
    assert b'\n  "' in published and subject.producer.canonical(json.loads(published)) != published
    policy = subject.authority(published)
    reference = dict(certificate_path=policy['registration']['formal']['certificate_paths'][0],
                     certificate_sha256='1' * 64, finalize_actual_path='fixture-finalizer',
                     finalize_actual_sha256='2' * 64)
    preflight = dict(path=policy['independent_preflight_actual_path'], sha256='3' * 64)
    ready = dict(readiness_reference={}, independent_preflight_reference=preflight)
    clock = profiles.window(identity).START_MS
    monkeypatch.setattr(subject.control, 'WHOLE_REQUESTED_MS', clock)
    monkeypatch.setattr(subject.control.time, 'time_ns', lambda: clock * 10**6)
    monkeypatch.setattr(subject, 'activation_readiness', lambda *_: ready)
    monkeypatch.setattr(checker, '_trusted_registered_sources', lambda *_: ({}, {}))
    monkeypatch.setattr(checker, '_registered_preflight', lambda *_: None)
    read_software = checker.native._software_bytes
    monkeypatch.setattr(checker.native, '_software_bytes',
                        lambda path: b'fixture' if str(path) == preflight['path']
                        else read_software(path))
    monkeypatch.setattr(subject.control, 'setup_formal', lambda plan, _ready: plan)
    plan = subject.activate_formal(subject.GENERATIONS[0], reference)
    assert plan['contract_sha256'] == plan['binding']['execution_protocol_sha256'] == expected
    plan['binding']['execution_protocol_sha256'] = subject.producer.sha(
        subject.producer.canonical(policy))
    with pytest.raises(ValueError, match='hash-bound execution authority freeze differs'):
        checker.validate_binding(plan)


def test_formal_only_route_binds_one_new_generation_and_no_public_quota(profiles):
    registered = profiles.profile('registered', profiles.FORMAL_INPUT)
    policy = registered.authority()
    root = policy['fixed_target']['attempts']['1']['generation']
    old_public = profiles.config(IDENTITY)['public_root']
    old_formal = profiles.config(IDENTITY)['generations'][0]
    assert registered.control.registered_root(Path(root)) and registered.is_root(root)
    assert all(not registered.is_root(p) and not registered.control.registered_root(Path(p))
               for p in (old_public, old_formal, root + '-copy'))
    assert policy['public_roots'] == [] and policy['input_limits']['public_graphs_max'] == 0
    assert policy['ancillary_named_FULL']['new_FULL_ceiling'] == 3960
    assert profiles.config_for_root(old_formal)['input'] == IDENTITY


def test_new_formal_measurement_accepts_only_the_exact_formal_role_command(
        profiles, tmp_path, monkeypatch):
    config = profiles.config(profiles.FORMAL_INPUT)
    resource = load('p17_m2_resource_control')
    argv = [str(Path(sys.orig_argv[0]).resolve()), '-I',
            str(REPO / 'scripts' / config['control_entry']), 'payload',
            '--root', config['generations'][0], '--plan-sha', 'a' * 64, '--role', 'exporter-r0']

    def accepted(*_args, **_kwargs):
        raise LookupError('reached sandboxed measurement boundary')

    monkeypatch.setattr(Path, 'mkdir', accepted)

    def invoke(scope, words):
        resource.invoke(tmp_path, 'exporter-r0', words, timeout=300, measurement_scope=scope,
                        measurement_execution_identity=config['input'])

    with pytest.raises(LookupError, match='measurement boundary'):
        invoke('SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY', argv)
    for wrong in ('FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY', 'OTHER'):
        with pytest.raises(ValueError):
            invoke(wrong, argv)
    argv[5] = profiles.config(IDENTITY)['generations'][0]
    with pytest.raises(ValueError):
        invoke('SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY', argv)


@pytest.mark.parametrize('mode', [
    'supervise', 'record', 'bind', 'run', 'payload',
    'certify-input-version', 'prepare-rehearsal', 'certify-rehearsal',
])
def test_formal_entry_routes_nested_commands_before_touching_custody(profiles, monkeypatch, mode):
    subject = profiles.profile('control', profiles.FORMAL_INPUT)
    config = profiles.config(profiles.FORMAL_INPUT)
    root = config['generations'][0]
    role = 'certificate' if mode.startswith('certify') else 'exporter-r0'
    argv = subject.argv_for(Path(root), mode, 'a' * 64, role)
    monkeypatch.setattr(sys, 'argv', argv[2:])
    monkeypatch.chdir(REPO)

    def reached(*_args, **_kwargs):
        raise LookupError('would inspect the unique formal plan')

    monkeypatch.setattr(subject, 'checked', reached)
    if mode in ('prepare-rehearsal', 'certify-rehearsal'):
        with pytest.raises(ValueError, match='FORMAL_ONLY_CONTRACT_REQUIRED'):
            subject.main()
    else:
        with pytest.raises(LookupError, match='unique formal plan'):
            subject.main()


def test_repaired_binary_cannot_reopen_closed_staged_formal_attempt(profiles, monkeypatch):
    subject = profiles.profile('registered', IDENTITY)
    evidence = Path(profiles.config(IDENTITY)['evidence_root'])
    (evidence.with_name(evidence.name + '-backup') / 'input-formal-caller-STOP.json').touch()
    monkeypatch.setattr(subject, 'authority_raw', lambda: pytest.fail('consumed authority entered'))
    with pytest.raises(ValueError, match='input-formal-caller-STOP'):
        subject.activate_formal(subject.GENERATIONS[0], {})


@pytest.mark.parametrize('mode', ['supervise', 'record', 'run', 'payload', 'bind',
                                  'certify-input-version'])
@pytest.mark.parametrize('peer', [False, True])
def test_formal_control_rejects_either_stop_before_target(profiles, monkeypatch, mode, peer):
    subject = profiles.profile('control', profiles.FORMAL_INPUT)
    config = profiles.config(profiles.FORMAL_INPUT)
    evidence = Path(config['evidence_root'])
    if peer:
        evidence = evidence.with_name(evidence.name + '-backup')
    (evidence / 'input-formal-caller-STOP.json').touch()
    role = 'certificate' if mode == 'certify-input-version' else 'exporter-r0'
    argv = subject.argv_for(Path(config['generations'][0]), mode, 'a' * 64, role)
    monkeypatch.setattr(sys, 'argv', argv[2:])
    monkeypatch.setattr(subject, 'checked', lambda *_: pytest.fail('target reached after STOP'))
    with pytest.raises(ValueError, match='input-formal-caller-STOP'):
        subject.main()
