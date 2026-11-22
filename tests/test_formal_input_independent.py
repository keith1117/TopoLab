"""NEW formal-only replay gates on temporary, declared metadata fixtures."""

import importlib.util
import json
import os
import subprocess
import sys
import sysconfig
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import pytest

REPO = Path(__file__).resolve().parents[1]


def subject():
    path = REPO / 'scripts/formal_input_independent.py'
    spec = importlib.util.spec_from_file_location('formal_independent_fixture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prior_public_rejects_unbound_bytes_before_historical_execution(monkeypatch):
    module = subject()
    monkeypatch.setattr(module, '_replay_historical',
                        lambda *_: pytest.fail('unbound history executed'))
    with pytest.raises(ValueError, match='prior|SHA|buffer'):
        module.verify_prior_public({}, b'{}\n', b'{}\n')


def acquisition():
    path = REPO / 'scripts/p17_m2_input_continuation.py'
    spec = importlib.util.spec_from_file_location('formal_profiles_fixture', path)
    profiles = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profiles)
    return profiles, profiles.profile('independent', profiles.FORMAL_INPUT)


def test_formal_only_authority_rejects_public_scope_and_expanded_allowance(monkeypatch):
    profiles, module = acquisition()
    raw = (REPO / module.REGISTERED_PROTOCOL).read_bytes()
    policy = json.loads(raw)
    plan = dict(scope=module.FORMAL_SCOPE,
                source_tree={module.REGISTERED_PROTOCOL: module.digest(raw)},
                binding=dict(preparation_protocol_sha256=module.digest(raw)),
                preparation_contract_sha256=module.digest(raw))
    pinned = subject()
    monkeypatch.setattr(module, '_prior_public_module', lambda: pinned)
    monkeypatch.setattr(module.native, '_software_bytes', lambda *_: raw)
    assert module._registered_authority(plan) == policy
    wrong = deepcopy(plan)
    wrong['scope'] = module.REHEARSAL_SCOPE
    with pytest.raises(ValueError, match='formal.only|formal-only'):
        module._registered_authority(wrong)
    policy['input_limits']['public_graphs_max'] = 1
    expanded = module.canonical(policy)
    monkeypatch.setattr(module.native, '_software_bytes', lambda *_: expanded)
    plan.update(source_tree={module.REGISTERED_PROTOCOL: module.digest(expanded)},
                binding=dict(preparation_protocol_sha256=module.digest(expanded)),
                preparation_contract_sha256=module.digest(expanded))
    with pytest.raises(ValueError, match='formal.only|formal-only'):
        module._registered_authority(plan)
    assert profiles.config(profiles.STAGED_INPUT)['public_graphs_max'] == 1


def test_new_consumers_share_exact_pinned_module_cache(monkeypatch):
    _profiles, module = acquisition()
    pinned = subject()
    monkeypatch.setitem(sys.modules, 'formal_input_independent', pinned)
    assert module._prior_public_module() is pinned


def test_r0_namespace_is_selected_by_fixed_identity_not_fixture_storage(tmp_path, monkeypatch):
    profiles, _old = acquisition()
    module = profiles.profile('independent', profiles.R0_INPUT)
    raw = (REPO / module.REGISTERED_PROTOCOL).read_bytes()
    policy = json.loads(raw)
    pinned = subject()
    monkeypatch.setattr(module, 'CONTINUATION_CONFIG', dict(
        module.CONTINUATION_CONFIG, evidence_root=str(tmp_path)))
    monkeypatch.setattr(module, '_prior_public_module', lambda *_: pinned)
    monkeypatch.setattr(module.native, '_software_bytes', lambda *_: raw)
    plan = dict(scope=module.FORMAL_SCOPE,
                source_tree={module.REGISTERED_PROTOCOL: module.digest(raw)},
                binding=dict(preparation_protocol_sha256=module.digest(raw)),
                preparation_contract_sha256=module.digest(raw))
    assert module._registered_authority(plan) == policy
    assert policy['prior_public'] == pinned.expected_prior(pinned.R0_EVIDENCE)
    assert pinned.expected_prior()['bundle']['path'] != policy['prior_public']['bundle']['path']
    with pytest.raises(ValueError, match='namespace'):
        pinned.expected_prior(tmp_path)


def test_new_helper_records_compiled_buffer_digest_not_its_later_self_claim(monkeypatch):
    _profiles, module = acquisition()
    raw = b'MODULE_SOURCE_SHA256 = "a-later-file-claim"\n'
    loader = ModuleType('full60_input_loader')
    loader.loaded_source_sha256 = {}
    monkeypatch.delitem(sys.modules, 'formal_input_independent', raising=False)
    monkeypatch.setitem(sys.modules, 'full60_input_loader', loader)
    monkeypatch.setattr(module.native, '_software_bytes', lambda *_: raw)
    loaded = module._prior_public_module()
    path = str(REPO / 'scripts/formal_input_independent.py')
    assert loaded.MODULE_SOURCE_SHA256 == module.digest(raw)
    assert loader.loaded_source_sha256[path] == module.digest(raw)


@pytest.mark.parametrize('failed', [False, True])
def test_formal_registration_snapshot_is_discarded_after_each_validation(monkeypatch, failed):
    _profiles, module = acquisition()
    monkeypatch.setattr(module, 'public_prepare_suffix', lambda *_: ())
    snapshots = []

    def validate(_plan):
        memo = module._REGISTERED_SOURCE_REPLAY.get()
        assert memo == {}
        snapshots.append(memo)
        memo['declared proof'] = {'fixture': True}
        if failed:
            raise ValueError('fixture validation failed')
        return memo['declared proof']

    monkeypatch.setattr(module, '_validate_hash_bound_binding', validate)
    for _ in range(2):
        if failed:
            with pytest.raises(ValueError, match='fixture'):
                module.validate_binding(dict(execution_identity=module.REGISTERED_IDENTITY))
        else:
            assert module.validate_binding(dict(execution_identity=module.REGISTERED_IDENTITY))
        assert module._REGISTERED_SOURCE_REPLAY.get() is None
    assert snapshots[0] is not snapshots[1]


def public_fixture(module, monkeypatch):
    tree = {f'scripts/fixture-{i}.py': 'a' * 64 for i in range(74)}
    plan = dict(execution_identity=module.OLD_IDENTITY, root=module.OLD_ROOT,
                runtime=dict(cwd=str(module.OLD_REPO), python='declared-python'),
                scope='FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY', formal_authority=False,
                source_tree=tree, whole_end_ms=4500000)
    monkeypatch.setattr(module, 'TREE_SHA', module.sha(module.canonical(tree)))
    monkeypatch.setattr(module, 'PLAN_SHA', module.sha(module.canonical(plan)))
    bundle = dict(plan=plan, version_id=module.VERSION,
                  manifest={'members': {f'member-{i}': {} for i in range(1071)}},
                  roles={role: {} for role in module.ROLES})
    accepted = dict(bundle=bundle, events={role: [{'end_seconds': 10}]
                    for role in (*module.ROLES, 'final-filing', 'lease-release')})
    argv = ['declared-python', '-I', str(module.OLD_REPO / 'scripts/staged_input_control.py'),
            'certify-rehearsal', '--root', module.OLD_ROOT, '--plan-sha', module.PLAN_SHA,
            '--role', 'certificate']
    import shlex

    request = dict(cmd='exec ' + shlex.join(['env', *(k + '=1' for k in (
        'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS',
        'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')), *argv]),
        workdir=str(module.OLD_REPO), max_output_tokens=5000)
    stdout = module.canonical(dict(scope=plan['scope'], formal_authority=False,
        source_input_accepted=False, formal_or_scientific_admission=False,
        B_C_admission=False, member_count=1071, version_id=module.VERSION)).decode()
    packet = dict(schema='topolab.v2.m2-strict-source-binding.actual-call.v1',
                  author='/root', argv=argv, request=request, responses=[dict(
                      tool='exec_command', arguments=request, requested_ms=10000,
                      returned_ms=11000, result=dict(exit_code=0, output=stdout))])
    first, second = module.canonical(accepted), module.canonical(packet)
    monkeypatch.setattr(module, 'BUNDLE_SHA', module.sha(first))
    monkeypatch.setattr(module, 'ACTUAL_SHA', module.sha(second))
    return module.expected_prior(), first, second, accepted, packet


def test_pinned_history_replay_uses_same_buffers_and_caches_only_exact_bytes(monkeypatch):
    module = subject()
    prior, bundle, actual, accepted, _packet = public_fixture(module, monkeypatch)
    calls = []
    monkeypatch.setattr(module, '_replay_historical', lambda value: calls.append(value))
    first = module.verify_prior_public(prior, bundle, actual)
    assert first['public_end_ms'] == 11000 and calls == [accepted]
    first['public_plan']['root'] = 'caller-mutated'
    repeated = module.verify_prior_public(prior, bundle, actual)
    assert repeated['public_plan']['root'] == module.OLD_ROOT
    assert len(calls) == 1
    with pytest.raises(ValueError, match='SHA'):
        module.verify_prior_public(prior, bundle + b' ', actual)
    with pytest.raises(ValueError, match='prior_public'):
        module.verify_prior_public(dict(prior, source_main='0' * 40), bundle, actual)


@pytest.mark.parametrize('damage', ['scope', 'count', 'exit', 'actor', 'stdout', 'clock'])
def test_historical_facts_must_match_before_old_verifier(monkeypatch, damage):
    module = subject()
    prior, bundle, actual, accepted, packet = public_fixture(module, monkeypatch)
    if damage == 'scope':
        accepted['bundle']['plan']['scope'] = 'SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY'
    elif damage == 'count':
        accepted['bundle']['manifest']['members'].pop('member-0')
    elif damage == 'exit':
        packet['responses'][0]['result']['exit_code'] = False
    elif damage == 'actor':
        packet['author'] = '/root/full60_independent'
    elif damage == 'stdout':
        packet['responses'][0]['result']['output'] = '{}\n'
    else:
        packet['responses'][0]['returned_ms'] = 9000
    bundle, actual = module.canonical(accepted), module.canonical(packet)
    monkeypatch.setattr(module, 'BUNDLE_SHA', module.sha(bundle))
    monkeypatch.setattr(module, 'ACTUAL_SHA', module.sha(actual))
    prior = module.expected_prior()
    monkeypatch.setattr(module, '_replay_historical',
                        lambda *_: pytest.fail('damaged proof reached historical execution'))
    with pytest.raises(ValueError):
        module.verify_prior_public(prior, bundle, actual)


@pytest.mark.parametrize('failed', [False, True])
def test_historical_sandbox_denies_business_io_and_restores_new_process_state(
        tmp_path, monkeypatch, failed):
    module = subject()
    old = tmp_path / 'old-checkout'
    (old / 'scripts').mkdir(parents=True)
    code = old / 'scripts/frozen.py'
    code.write_bytes(b'VALUE = 1\n')
    monkeypatch.setattr(module, 'OLD_REPO', old)
    monkeypatch.setattr(module, 'DATA', tmp_path / 'metadata')
    tree = {'scripts/frozen.py': module.sha(code.read_bytes())}
    sentinel = ModuleType('full60_sentinel')
    monkeypatch.setitem(sys.modules, sentinel.__name__, sentinel)
    path, opening, stating = list(sys.path), os.open, os.stat
    try:
        with module._historical_view(tree, '/declared-interpreter'):
            assert sentinel.__name__ not in sys.modules
            for action in (lambda: os.open(tmp_path / 'source', os.O_RDONLY),
                           lambda: (tmp_path / 'target').stat(),
                           lambda: subprocess.Popen(['/unregistered-command']),
                           lambda: (Path(sysconfig.get_path('stdlib'))
                                    / 'site-packages/unregistered-dependency.py').stat()):
                with pytest.raises(ValueError, match='denied'):
                    action()
            assert (Path(sysconfig.get_path('stdlib')) / 'tempfile.py').stat().st_size > 0
            assert code.read_bytes() == b'VALUE = 1\n'
            if failed:
                raise LookupError('declared history exception')
    except LookupError:
        assert failed
    assert os.open is opening and os.stat is stating and sys.path == path
    assert sys.modules[sentinel.__name__] is sentinel


def preflight_fixture(monkeypatch, *, damage=None, r0=False):
    """Build original tool packets and hashed wires only; no custody path is opened."""
    profiles, module = acquisition()
    if r0:
        module = profiles.profile('independent', profiles.R0_INPUT)
    pinned = subject()
    policy_raw = (REPO / module.REGISTERED_PROTOCOL).read_bytes()
    policy = json.loads(policy_raw)
    start = policy['independent_author_start_ms']
    evidence = Path(module.CONTINUATION_CONFIG['evidence_root'])
    prior = policy['prior_public']
    history_calls = []

    def historical(value, first, second):
        assert value == prior and first == b'public bundle' and second == b'public actual'
        history_calls.append(value)
        return {'public_end_ms': start - 1}

    pinned.verify_prior_public = historical
    read_proof = dict(source_main='d'*40, accepted_slots=[3, 4],
                      verified_returned_ms=start + (11 if damage == 'r0-late' else 9))
    reader_module = ModuleType('declared_r0_verifier')
    reader_module.verified_readiness = lambda *_: read_proof
    monkeypatch.setattr(module, '_prior_public_module', lambda name='formal_input_independent':
                        reader_module if name == 'r0_read_independent' else pinned)
    runtime = dict(python='/declared/isolated-python', cwd=str(REPO), threads={'fixture': '1'})
    tree = {module.REGISTERED_PROTOCOL: module.digest(policy_raw),
            'scripts/declared-source.py': 'a' * 64}
    plan = dict(scope=module.FORMAL_SCOPE, source_tree=tree,
                binding=dict(preparation_protocol_sha256=module.digest(policy_raw)),
                preparation_contract_sha256=module.digest(policy_raw),
                runtime=dict(runtime, orig_argv=['declared actual argv']))
    paths = policy['preparation_closure_paths']
    retention_argv = [runtime['python'], '-I', str(REPO / 'scripts'
                      / module.CONTINUATION_CONFIG['preparation_entry']), 'retain']
    closure = dict(schema='topolab.registered-input.preparation-closure.v1',
                   execution_identity=module.REGISTERED_IDENTITY, source_tree=tree,
                   public_native_acceptance=prior['bundle'], prior_public=prior,
                   new_input_budget=policy['new_input_budget'],
                   status='COMPLETE_SOFTWARE_ONLY', own_future_return='NOT_CLAIMED',
                   retention_argv=retention_argv)
    if r0:
        closure['r0_read_verification'] = deepcopy(read_proof)
        if damage == 'r0-closure':
            closure['r0_read_verification']['accepted_slots'] = [3]
    if damage == 'closure':
        closure['prior_public'] = dict(prior, source_main='0' * 40)
    closure_raw = module.canonical(closure)
    core = module.helper('preflight_fixture_core', 'p17_m2_source_binding.py')

    def packet(argv, author, output, before, after):
        request = dict(cmd=core.literal_command(argv), workdir=str(REPO),
                       max_output_tokens=20000)
        return dict(schema='topolab.v2.m2-strict-source-binding.actual-call.v1',
                    author=author, argv=argv, request=request, responses=[dict(
                        tool='exec_command', arguments=request, requested_ms=before,
                        returned_ms=after, result=dict(exit_code=0, output=output))])

    retained = dict(status='REGISTERED_INPUT_PREPARATION_PAIR_RETAINED',
                    closure_paths=paths, sha256=module.digest(closure_raw),
                    own_future_return='NOT_CLAIMED')
    retention = packet(retention_argv, policy['actors']['executor'],
                       module.canonical(retained).decode(), start + 10, start + 20)
    if damage == 'retention-return':
        retention['responses'][0]['result']['exit_code'] = 1
    if damage == 'retention-clock':
        retention['responses'][0]['requested_ms'] = start - 2
    retention_raw = module.canonical(retention)
    retention_pin = dict(path=policy['preparation_retention_actual_path'],
                         sha256=module.digest(retention_raw))
    ready = dict(schema='topolab.registered-input.activation-readiness.v1',
                 execution_identity=module.REGISTERED_IDENTITY,
                 actors=policy['actors'], new_input_budget=policy['new_input_budget'],
                 published_source_sha256={k: v for k, v in tree.items()
                                          if k != module.REGISTERED_PROTOCOL},
                 runtime=runtime, prior_public=prior,
                 public_native_acceptance=prior['bundle'],
                 public_certificate_actual=prior['actual'],
                 preparation_closure_paths=paths,
                 preparation_closure_sha256=module.digest(closure_raw),
                 preparation_retention_actual=retention_pin)
    if r0:
        ready['r0_read_verification'] = deepcopy(read_proof)
        if damage == 'r0-ready':
            ready['r0_read_verification']['source_main'] = 'a'*40
    if damage == 'new-tree':
        ready['published_source_sha256'] = {'scripts/declared-source.py': 'b' * 64}
    if damage == 'new-runtime':
        ready['runtime'] = dict(runtime, cwd='/other-checkout')
    if damage == 'new-actor':
        ready['actors'] = dict(ready['actors'], independent='/same-author')
    if damage == 'new-budget':
        ready['new_input_budget'] = dict(ready['new_input_budget'], sha256='b' * 64)
    ready_raw = module.canonical(ready)
    ready_pin = dict(path=policy['readiness_path'], sha256=module.digest(ready_raw))
    plan['activation_readiness'] = ready_pin
    expected = dict(status='PASS_REGISTERED_INPUT_METADATA_PREFLIGHT',
                    execution_identity=module.REGISTERED_IDENTITY,
                    author=policy['actors']['independent'], readiness_path=ready_pin['path'],
                    readiness_sha256=ready_pin['sha256'],
                    published_source_sha256=ready['published_source_sha256'], runtime=runtime,
                    actors=policy['actors'], new_input_budget=policy['new_input_budget'],
                    source_stat_reads=0, target_stat_reads=0, own_future_return='NOT_CLAIMED')
    if r0 and damage != 'r0-stdout':
        expected['r0_read_verification'] = deepcopy(read_proof)
    argv = [runtime['python'], '-I', str(REPO / 'scripts'
            / module.CONTINUATION_CONFIG['input_entry']), 'preflight', '--readiness-sha',
            ready_pin['sha256']]
    actual = packet(argv, policy['actors']['independent'], module.canonical(expected).decode(),
                    start + 30, start + 40)
    if damage == 'actual-actor':
        actual['author'] = policy['actors']['executor']
    if damage == 'actual-exit-bool':
        actual['responses'][0]['result']['exit_code'] = False
    if damage == 'actual-clock':
        actual['responses'][0]['returned_ms'] = policy['global_deadline_ms'] + 1
    if damage == 'actual-order':
        actual['responses'][0]['requested_ms'] = start + 19
    if damage == 'actual-stdout':
        actual['responses'][0]['result']['output'] = '{}\n'
    actual_raw = module.canonical(actual)
    actual_pin = dict(path=policy['independent_preflight_actual_path'],
                      sha256=module.digest(actual_raw))
    plan['independent_preflight'] = actual_pin
    buffers = {str(REPO / module.REGISTERED_PROTOCOL): policy_raw,
               ready_pin['path']: ready_raw,
               policy['new_input_budget']['path']: b'{}\n',
               str(evidence / 'prior-public-bundle.json'): b'public bundle',
               str(evidence / 'prior-public-certificate-actual.json'): b'public actual',
               paths[0]: closure_raw, retention_pin['path']: retention_raw,
               actual_pin['path']: actual_raw}
    monkeypatch.setattr(module.native, '_software_bytes', lambda path: buffers[str(path)])
    monkeypatch.setattr(module, '_registered_read_pin',
                        lambda ref: json.loads(buffers[ref['path']]))
    monkeypatch.setattr(module, '_formal_pair', lambda ref: buffers[ref['path']])
    return module, plan, actual_raw, expected, history_calls


def test_formal_preflight_binds_new_ready_and_original_returns_to_historical_bytes(monkeypatch):
    module, plan, raw, expected, calls = preflight_fixture(monkeypatch)
    assert module._registered_preflight(plan, raw) == expected
    assert len(calls) == 1


def test_r0_preflight_binds_verified_read_receipts_and_original_verifier_return(monkeypatch):
    module, plan, raw, expected, _calls = preflight_fixture(monkeypatch, r0=True)
    assert module._registered_preflight(plan, raw) == expected


@pytest.mark.parametrize('damage', ['r0-late', 'r0-closure', 'r0-ready', 'r0-stdout'])
def test_r0_proof_cannot_be_after_prepare_or_differ_between_ready_and_closure(monkeypatch, damage):
    module, plan, raw, _expected, _calls = preflight_fixture(monkeypatch, damage=damage, r0=True)
    with pytest.raises(ValueError):
        module._registered_preflight(plan, raw)


@pytest.mark.parametrize('damage', [
    'closure', 'retention-return', 'retention-clock', 'new-tree', 'new-runtime', 'new-actor',
    'new-budget', 'actual-actor', 'actual-exit-bool', 'actual-clock', 'actual-order',
    'actual-stdout'])
def test_formal_preflight_rejects_mixed_history_new_software_and_unreturned_proofs(
        monkeypatch, damage):
    module, plan, raw, _expected, _calls = preflight_fixture(monkeypatch, damage=damage)
    with pytest.raises(ValueError):
        module._registered_preflight(plan, raw)


def test_formal_private_pair_requires_distinct_private_files_and_exact_new_literal(
        tmp_path, monkeypatch):
    _profiles, module = acquisition()
    evidence = tmp_path / 'new-evidence'
    peer = tmp_path / 'new-evidence-backup'
    evidence.mkdir()
    peer.mkdir()
    first, second = evidence / 'receipt.json', peer / 'receipt.json'
    raw = b'{"declared_fixture":true}\n'
    for path in (first, second):
        path.write_bytes(raw)
        path.chmod(0o600)
    monkeypatch.setattr(module, 'CONTINUATION_CONFIG', dict(evidence_root=str(evidence)))
    pin = dict(path=str(first), sha256=module.digest(raw))
    assert module._formal_pair(pin) == raw
    second.chmod(0o644)
    with pytest.raises(ValueError, match='pair'):
        module._formal_pair(pin)
    second.unlink()
    os.link(first, second)
    with pytest.raises(ValueError, match='pair|ordinary|link|kind'):
        module._formal_pair(pin)
    with pytest.raises(ValueError, match='literal'):
        module._formal_pair(dict(pin, path=str(tmp_path / 'other.json')))
