"""NEW public metadata exercises the independently implemented registered reader."""

import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def checker():
    path = REPO / 'scripts/p17_m2_source_acquisition_independent.py'
    spec = importlib.util.spec_from_file_location('registered_input_independent_test', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_reader(tmp_path, *, bound=True):
    subject = checker()
    primitive = subject.helper('registered_public_reader', 'p17_m2_input_export_independent.py')
    raw = b'{"new_public_metadata":true}\n'
    path = tmp_path / 'public.json'
    path.write_bytes(raw)
    info = path.stat()
    registrations = {'public.json': {'sha256': hashlib.sha256(raw).hexdigest(),
        'byte_size': len(raw), 'declared': primitive.source_identity(info)}} if bound else {}
    reader = subject._registered_once_reader(primitive, tmp_path, 40, 32 * primitive.MIB,
        registrations=registrations, source_identity_checks=True,
        source_identity_policy=subject.HASH_BOUND_POLICY)
    return subject, primitive, reader, path, raw


@pytest.mark.parametrize('bound', [True, False])
def test_registered_hash_allows_only_the_prebound_mtime_change(tmp_path, monkeypatch, bound):
    _, primitive, reader, path, raw = public_reader(tmp_path, bound=bound)
    original = primitive.os.read
    changed = False

    def changed_read(fd, length):
        nonlocal changed
        value = original(fd, length)
        if value and not changed:
            info = path.stat()
            os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 7))
            changed = True
        return value

    monkeypatch.setattr(primitive.os, 'read', changed_read)
    if bound:
        assert reader.packet('public.json', 1024) == {'new_public_metadata': True}
        row = reader.observations[0]
        assert row['expected_sha256'] == hashlib.sha256(raw).hexdigest()
        assert row['before']['st_mtime_ns'] != row['closing']['st_mtime_ns']
        anchor = reader.source_facts['public.json']['registered_preread_anchor']
        assert anchor['st_ino'] == row['declared']['st_ino']
    else:
        with pytest.raises(ValueError, match='changed'):
            reader.packet('public.json', 1024)
        assert reader.failures and reader.failures[0]['after']


def test_registration_same_hash_replaced_inode_rejects_before_content_read(tmp_path, monkeypatch):
    _, primitive, reader, path, raw = public_reader(tmp_path)
    replacement = tmp_path / 'replacement.json'
    replacement.write_bytes(raw)
    replacement.replace(path)
    monkeypatch.setattr(primitive.os, 'read', lambda *a: pytest.fail('replacement content read'))
    with pytest.raises(ValueError, match='anchor'):
        reader.packet('public.json', 1024)
    assert reader.failures[0]['registered_preread_anchor']
    assert reader.failures[0]['declared'] and reader.failures[0]['before']


def test_registered_profile_is_separate_from_legacy_result_windows():
    subject = checker()
    plan = {'execution_identity': 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v2',
            'source_identity_policy': subject.HASH_BOUND_POLICY,
            'binding': {'source_identity_policy': subject.HASH_BOUND_POLICY,
                        'authority_protocol_path':
                            'docs/planning/p17_m2_registered_input_v2_protocol.json'}}
    assert subject._source_policy(plan) == subject.HASH_BOUND_POLICY
    assert subject._protocol_path(plan) == 'docs/planning/p17_m2_registered_input_v2_protocol.json'
    plan['execution_identity'] = 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v1'
    with pytest.raises(ValueError):
        subject._source_policy(plan)


def test_registered_formal_setup_binds_dynamic_actual_preflight_without_old_protocol_fields(
        monkeypatch):
    path = REPO / 'tests/test_p17_m2_source_acquisition_independent.py'
    spec = importlib.util.spec_from_file_location('registered_setup_public_fixture', path)
    fixture = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(fixture)
    subject, bundle, proof = fixture.setup_metadata_case()
    plan, setup, initial = bundle['plan'], bundle['setup'], bundle['initial_lease']
    plan.update(execution_identity=subject.REGISTERED_IDENTITY, scope=subject.FORMAL_SCOPE)
    plan['activation_readiness'] = {'path': '/private/tmp/public-readiness-fixture.json',
                                   'sha256': '1' * 64}
    plan['independent_preflight'] = {'path': '/private/tmp/public-actual-fixture.json',
                                    'sha256': '2' * 64}
    initial['execution_identity'] = setup['execution_identity'] = subject.REGISTERED_IDENTITY
    setup['scope'] = subject.FORMAL_SCOPE
    initial['plan_sha256'] = setup['plan_sha256'] = bundle['plan_sha256'] = subject.digest(
        subject.canonical(plan))
    setup['lease_identity']['st_size'] = len(subject.canonical(initial))
    setup['lease_record_sha256'] = subject.digest(subject.canonical(initial))
    actors = {'executor': '/root', 'independent': '/root/binding_route_independent_v1'}
    setup['readiness'] = {'actors': actors, 'preparation_closure_sha256': '3' * 64,
                         'independent_preflight_sha256': '2' * 64,
                         'main': '4' * 40, 'main_CI_run': 99}
    setup['filesystem'] = {'local_filesystem': True, 'basis': 'DARWIN_FSTATFS64_MNT_LOCAL',
                           'available_bytes': 2 * 1024**3}
    proof['setup_proof_sha256'] = subject.digest(subject.canonical(setup))
    monkeypatch.setattr(subject, 'validate_binding', lambda value: None)
    monkeypatch.setattr(subject, '_protocol_path', lambda value: subject.REGISTERED_PROTOCOL)
    monkeypatch.setattr(subject.native, '_software_bytes',
                        lambda path: subject.canonical({'actors': actors}))
    monkeypatch.setattr(subject, '_registered_read_pin',
                        lambda pin: {'preparation_closure_sha256': '3' * 64})
    seen = []
    monkeypatch.setattr(subject, '_registered_preflight', lambda value, raw: seen.append(value))
    subject.validate_setup(bundle, proof, {'T0': 1002})
    assert seen == [plan]


def test_registered_software_compiler_includes_mjs_and_actual_cohort_operators(monkeypatch):
    subject = checker()
    captured = {}

    def capture(plan, **kwargs):
        captured.update(kwargs)
        raise RuntimeError('actual registered compiler arguments captured before runtime IO')

    monkeypatch.setattr(subject, 'validate_binding', lambda plan: None)
    monkeypatch.setattr(subject.native, '_check_software', capture)
    plan = {'execution_identity': subject.REGISTERED_IDENTITY, 'scope': subject.REHEARSAL_SCOPE,
            'source_identity_policy': subject.HASH_BOUND_POLICY,
            'binding': {'source_identity_policy': subject.HASH_BOUND_POLICY,
                        'authority_protocol_path': subject.REGISTERED_PROTOCOL,
                        'strict23_registration': {'certificate_sha256': 'a' * 64,
                                                  'finalize_actual_sha256': 'b' * 64}}}
    with pytest.raises(RuntimeError, match='compiler arguments captured'):
        subject._check_software(plan)
    required = {'scripts/p17_m2_scientific_tool_ingress.mjs',
                'scripts/p17_m2_scientific_metadata.mjs',
                'scripts/p17_m2_scientific_metadata_manifest.mjs',
                'scripts/m2_acquisition_cohort.mjs',
                'scripts/m2_acquisition_actual_boundary.mjs',
                'scripts/await_m2_acquisition_receipt.py',
                'scripts/file_m2_acquisition_event.py'}
    assert required <= set(captured['contracts'])
    complete = subject.native._software_closure(REPO, contracts=captured['contracts'])
    assert required <= complete.keys()
    assert all(complete[name] == subject.digest((REPO / name).read_bytes()) for name in required)
    controller = subject.helper('registered_controller_compiler_check',
                                'p17_m2_source_acquisition_control.py')
    assert complete == controller.source_freeze(subject.REGISTERED_IDENTITY)
