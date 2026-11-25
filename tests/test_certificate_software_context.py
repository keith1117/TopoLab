"""Synthetic software-only boundaries for certificate replay; no input IO."""

import importlib.util
import platform
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def profile(identity_name='WINDOW_FORMAL'):
    path = REPO / 'scripts/p17_m2_input_continuation.py'
    spec = importlib.util.spec_from_file_location('certificate_profiles_fixture', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module, module.profile('independent', getattr(module, identity_name))


@pytest.mark.parametrize('identity_name', ['WINDOW_FORMAL', 'CERT_FORMAL', 'CHILD_FORMAL'])
def test_window_software_selection_equals_producer_complete_tree(monkeypatch, identity_name):
    profiles, checker = profile(identity_name)
    monkeypatch.setattr(checker, 'validate_binding', lambda *_: None)
    monkeypatch.setattr(checker, 'public_prepare_suffix', lambda *_: ())
    captured = {}

    def stop(_plan, **options):
        captured.update(options)
        raise RuntimeError('captured software closure')

    monkeypatch.setattr(checker.native, '_check_software', stop)
    with pytest.raises(RuntimeError, match='captured software closure'):
        checker._check_software(dict(execution_identity=checker.REGISTERED_IDENTITY,
                                    scope=checker.FORMAL_SCOPE,
                                    source_identity_policy=checker.HASH_BOUND_POLICY,
                                    binding={'source_identity_policy': checker.HASH_BOUND_POLICY,
                                             'authority_protocol_path':
                                             checker.REGISTERED_PROTOCOL}))
    actual = checker.native._software_closure(REPO, contracts=captured['contracts'])
    identity = getattr(profiles, identity_name)
    producer = profiles.profile('control', identity).source_freeze(identity)
    assert actual == producer
    assert 'scripts/r1_window_verify.py' in actual
    assert 'docs/planning/r1_window_public_contract.json' in actual


def test_historical_context_refuses_arbitrary_or_changed_plan_before_source_read(monkeypatch):
    _, checker = profile()
    monkeypatch.setattr(checker.native, '_software_bytes',
                        lambda *_: pytest.fail('unbound historical software read'))
    with pytest.raises(ValueError, match='historical.*plan'):
        checker.historical_software_context({'source_tree': {}})


def test_context_does_not_enable_unregistered_formal_identity(monkeypatch):
    _, checker = profile()
    monkeypatch.setattr(checker, 'REGISTERED_IDENTITY', checker.CERT_FORMAL)
    assert checker._formal_only_profile()
    monkeypatch.setattr(checker, 'REGISTERED_IDENTITY', 'not-an-authority')
    assert not checker._formal_only_profile()


def test_certificate_profile_replays_only_its_new_literal_authority(monkeypatch):
    _, checker = profile('CERT_FORMAL')
    raw = (REPO / checker.REGISTERED_PROTOCOL).read_bytes()
    policy = checker.native.base.parse(raw)
    pinned = checker._prior_public_module()
    monkeypatch.setattr(checker, '_prior_public_module', lambda *_: pinned)
    monkeypatch.setattr(checker.native, '_software_bytes', lambda *_: raw)
    sha = checker.digest(raw)
    plan = dict(scope=checker.FORMAL_SCOPE,
                source_tree={checker.REGISTERED_PROTOCOL: sha},
                binding=dict(preparation_protocol_sha256=sha),
                preparation_contract_sha256=sha)
    assert checker._registered_authority(plan) == policy
    assert policy['prior_public']['bundle']['path'].startswith(
        '/Users/keith1117/Documents/TopoLab-data/certificate-20261124-formal/')
    assert checker._formal_only_profile()


def test_historical_audit_requires_the_issued_context(monkeypatch):
    _, checker = profile()
    monkeypatch.setattr(checker, 'validate_binding', lambda *_: pytest.fail('unbound audit'))
    with pytest.raises(ValueError, match='historical.*context'):
        checker.audit_certificate({'plan': {}}, trusted_tool_events={'r': []},
                                  historical_software_context={})


def test_historical_context_cannot_be_used_for_another_plan(monkeypatch):
    _, checker = profile()
    original = {'source_tree': {}, 'runtime': {'cwd': str(checker.HISTORICAL_REPO)}}
    monkeypatch.setattr(checker, 'HISTORICAL_PLAN_SHA256',
                        checker.digest(checker.canonical(original)))
    monkeypatch.setattr(checker, '_historical_context_sources', lambda *_: ({}, {}))
    context = checker.historical_software_context(original)
    wrong = deepcopy(original)
    wrong['runtime']['cwd'] += '-other'
    with pytest.raises(ValueError, match='historical.*plan'):
        checker.audit_certificate({'plan': wrong}, trusted_tool_events={'r': []},
                                  historical_software_context=context)


def software_fixture(tmp_path, checker):
    native = checker.native
    repo = tmp_path / 'published'
    (repo / 'scripts').mkdir(parents=True)
    for name in native.REQUIRED_HELPERS | {'scripts/p17_m2_source_acquisition_independent.py'}:
        (repo / name).write_bytes((name + '\n').encode())
    (repo / 'uv.lock').write_bytes((REPO / 'uv.lock').read_bytes())
    tree = native._software_closure(repo, contracts=())
    python = str(Path(sys.orig_argv[0]).resolve())
    script = str(repo / 'scripts/p17_m2_content_verified_control.py')
    root = str(tmp_path / 'unopened-input')
    runtime = dict(cwd=str(repo), python=python,
                   python_sha256=native.digest(Path(python).read_bytes()), isolated=1,
                   platform=sys.platform, os_release=platform.release(),
                   lock_sha256=native.digest((repo / 'uv.lock').read_bytes()),
                   threads={name: '1' for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS',
                            'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS', 'NUMEXPR_NUM_THREADS')},
                   orig_argv=[python, '-I', script, 'prepare-public', '--root', root])
    plan = dict(source_tree=tree, runtime=runtime, root=root, roles={}, metadata_actions={})
    for role in (*native.ROLE_ORDER, 'final-filing', 'lease-release'):
        table = plan['roles'] if role in native.ROLE_ORDER else plan['metadata_actions']
        table[role] = {'argv': [python, '-I', script, 'payload', '--root', root,
                                '--plan-sha', '@PLAN_SHA256@', '--role', role]}
    buffers = {name: (repo / name).read_bytes() for name in tree}
    audits = {str(Path(checker.__file__)): checker.MODULE_SOURCE_SHA256,
              str(Path(native.__file__)): native.MODULE_SOURCE_SHA256}
    context = native.HistoricalSoftwareContext(
        plan, repo, 'a' * 40, buffers, audits,
        _authority=native._HISTORICAL_SOFTWARE_AUTHORITY)
    options = dict(contracts=(), verifier_path='scripts/p17_m2_source_acquisition_independent.py',
                   verifier_sha256=checker.MODULE_SOURCE_SHA256,
                   historical_software_context=context)
    return plan, context, options


def test_explicit_history_checks_old_full_tree_and_separate_new_auditor(tmp_path):
    _, checker = profile()
    plan, context, options = software_fixture(tmp_path, checker)
    checker.native._check_software(plan, **options)
    summary = context.summary()
    assert summary['actual_audit_sources_sha256'][str(Path(checker.__file__))] == (
        checker.MODULE_SOURCE_SHA256)
    assert summary['historical_verifier_sha256']['scripts/p17_m2_source_acquisition_independent.py']
    with pytest.raises(ValueError, match='source freeze'):
        checker.native._check_software(plan, **dict(options, historical_software_context=None,
                                                   repo_guard=lambda path: path))


@pytest.mark.parametrize('mutation', ['missing', 'extra', 'changed'])
def test_any_old_software_inventory_or_byte_change_rejects(tmp_path, mutation):
    _, checker = profile()
    plan, context, options = software_fixture(tmp_path, checker)
    path = context.repo / 'scripts/p17_m2_content_verified_control.py'
    if mutation == 'missing':
        path.unlink()
    elif mutation == 'extra':
        (path.parent / 'p17_m2_unregistered_extra.py').write_bytes(b'no grant\n')
    else:
        path.write_bytes(b'changed published software\n')
    with pytest.raises(ValueError, match='helper missing|source freeze'):
        checker.native._check_software(plan, **options)


def test_historical_imports_execute_old_buffers_then_restore_current_modules(tmp_path, monkeypatch):
    from types import ModuleType, SimpleNamespace

    _, checker = profile()
    repo = tmp_path / 'old'
    buffers = {'scripts/' + name + '.py': b'VALUE="actual-old-buffer"\n' for name in (
        'staged_input_filer', 'r0_read_independent')}
    plan = dict(source_tree={name: checker.digest(raw) for name, raw in buffers.items()},
                runtime={'cwd': str(repo)})
    context = checker.native.HistoricalSoftwareContext(
        plan, repo, 'a' * 40, buffers, {},
        _authority=checker.native._HISTORICAL_SOFTWARE_AUTHORITY)
    old = ModuleType('staged_input_filer')
    old.VALUE = 'current-auditor'
    loader = SimpleNamespace(loaded_source_sha256={'current.py': 'original-digest'})
    monkeypatch.setitem(sys.modules, 'staged_input_filer', old)
    monkeypatch.setitem(sys.modules, 'full60_input_loader', loader)
    before_path = list(sys.path)
    token = checker._HISTORICAL_SOFTWARE_CONTEXT.set(context)
    try:
        with pytest.raises(RuntimeError, match='fixture unwind'):
            with checker._historical_import_scope(context):
                import staged_input_filer

                assert staged_input_filer.VALUE == 'actual-old-buffer'
                assert loader.loaded_source_sha256[str(repo / 'scripts/staged_input_filer.py')] == (
                    checker.digest(buffers['scripts/staged_input_filer.py']))
                assert staged_input_filer.__file__ == str(repo / 'scripts/staged_input_filer.py')
                raise RuntimeError('fixture unwind')
    finally:
        checker._HISTORICAL_SOFTWARE_CONTEXT.reset(token)
    assert sys.modules['staged_input_filer'] is old
    assert loader.loaded_source_sha256 == {'current.py': 'original-digest'}
    assert sys.path == before_path


@pytest.mark.parametrize('mutation', [None, 'published-byte', 'compiled-buffer', 'extra-git-byte'])
def test_history_factory_checks_each_published_blob_and_actual_audit_buffer(
        tmp_path, monkeypatch, mutation):
    from types import SimpleNamespace

    _, checker = profile()
    plan, context, _options = software_fixture(tmp_path, checker)
    plan.update(execution_identity=checker.WINDOW_FORMAL,
                scope=checker.FORMAL_SCOPE, formal_authority=True)
    monkeypatch.setattr(checker, 'HISTORICAL_REPO', context.repo)
    monkeypatch.setattr(checker, '_software_contracts', lambda *_args, **_kwargs: ())
    executed = dict(context.audit_sources)
    if mutation == 'compiled-buffer':
        executed[str(Path(checker.__file__))] = '0' * 64
    monkeypatch.setitem(sys.modules, 'full60_input_loader',
                        SimpleNamespace(loaded_source_sha256=executed))

    def git(args, **options):
        assert args == ['git', '--no-optional-locks', 'cat-file', '--batch']
        assert options['cwd'] == context.repo
        expected = ''.join(checker.HISTORICAL_MAIN + ':' + name + '\n'
                           for name in sorted(plan['source_tree'])).encode('ascii')
        assert options['input'] == expected
        output = bytearray()
        for index, name in enumerate(sorted(plan['source_tree'])):
            raw = context.source_bytes(context.repo / name)
            if mutation == 'published-byte' and index == 0:
                raw = b'X' + raw[1:]
            output.extend(('0' * 40 + ' blob ' + str(len(raw)) + '\n').encode())
            output.extend(raw + b'\n')
        if mutation == 'extra-git-byte':
            output.extend(b'X')
        return SimpleNamespace(returncode=0, stdout=bytes(output), stderr=b'')

    import subprocess

    monkeypatch.setattr(subprocess, 'run', git)
    if mutation:
        with pytest.raises(ValueError, match='Git|compiled source'):
            checker._historical_context_sources(plan)
    else:
        captured, audits = checker._historical_context_sources(plan)
        assert {name: checker.digest(raw) for name, raw in captured.items()} == plan['source_tree']
        assert audits == dict(context.audit_sources)


def test_repeated_and_nested_history_recompiles_dependencies_for_replaced_loader(
        tmp_path, monkeypatch):
    from types import SimpleNamespace

    _, checker = profile()
    repo = tmp_path / 'old'
    buffers = {'scripts/' + name + '.py': b'VALUE="executed-old"\n' for name in (
        'staged_input_filer', 'r0_read_independent')}
    buffers['scripts/r1_window_proof.py'] = b'''
import sys
def verified_readiness(*unused):
    from pathlib import Path
    import staged_input_filer, r0_read_independent
    observed = sys.modules['full60_input_loader'].loaded_source_sha256
    root = Path(__file__).parent
    assert str(root / 'staged_input_filer.py') in observed
    assert str(root / 'r0_read_independent.py') in observed
    return staged_input_filer.VALUE, r0_read_independent.VALUE
'''
    plan = dict(source_tree={name: checker.digest(raw) for name, raw in buffers.items()},
                runtime={'cwd': str(repo)})
    context = checker.native.HistoricalSoftwareContext(
        plan, repo, 'a' * 40, buffers, {},
        _authority=checker.native._HISTORICAL_SOFTWARE_AUTHORITY)
    initial_loader = SimpleNamespace(loaded_source_sha256={'current': 'untouched'})
    monkeypatch.setitem(sys.modules, 'full60_input_loader', initial_loader)
    token = checker._HISTORICAL_SOFTWARE_CONTEXT.set(context)
    original_code = importlib.machinery.SourceFileLoader.get_code
    try:
        with checker._historical_import_scope(context):
            proof = checker._prior_public_module('r1_window_proof')
            assert proof.verified_readiness({}, {}) == ('executed-old', 'executed-old')
            for _ in range(2):
                replacement = SimpleNamespace(loaded_source_sha256={},
                                              __file__=str(repo / 'scripts/full60_input_loader.py'))
                monkeypatch.setitem(sys.modules, 'full60_input_loader', replacement)
                with checker._historical_import_scope(context):
                    repeated = checker._prior_public_module('r1_window_proof')
                    assert repeated is proof
                    assert repeated.verified_readiness({}, {}) == ('executed-old', 'executed-old')
                    assert replacement.loaded_source_sha256[
                        str(repo / 'scripts/staged_input_filer.py')] == checker.digest(
                            buffers['scripts/staged_input_filer.py'])
    finally:
        checker._HISTORICAL_SOFTWARE_CONTEXT.reset(token)
    assert sys.modules['full60_input_loader'] is initial_loader
    assert initial_loader.loaded_source_sha256 == {'current': 'untouched'}
    assert importlib.machinery.SourceFileLoader.get_code is original_code
