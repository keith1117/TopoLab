"""S1 new source-attested capability stays separate from public certificates."""

import importlib.util
import sys
from pathlib import Path

import pytest

ENTRY = Path(__file__).parents[1] / "scripts/p17_m2_source_verified_input.py"


def load():
    spec = importlib.util.spec_from_file_location("source_verified_input_test", ENTRY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_serialized_or_old_public_pass_cannot_open_new_source_attested_reader(monkeypatch):
    module = load()

    def forbidden(*args, **kwargs):
        pytest.fail("unverified capability reached scientific IO")

    monkeypatch.setattr("os.open", forbidden)
    for packet in ({"status": "PASS", "formal_authority": True}, object()):
        with pytest.raises(ValueError, match="UNVERIFIED_SOURCE_CERTIFICATE"):
            module.VerifiedAcquisitionInput(packet, "scientific-producer")


def prospective_certificate():
    path = ENTRY.with_name('p17_m2_input_continuation.py')
    spec = importlib.util.spec_from_file_location('p17_m2_input_continuation', path)
    profiles = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = profiles
    spec.loader.exec_module(profiles)
    checker = profiles.profile('independent')
    binding = {'root': '/PUBLIC_NOT_OPENED/content', 'root_identity': {},
               'version_id': 'a' * 64, 'contract_sha256': 'b' * 64,
               'plan_sha256': 'c' * 64, 'shared_packet_sha256': 'd' * 64,
               'verified_plan': {'execution_identity': profiles.INPUT},
               'scope': checker.REHEARSAL_SCOPE}
    return checker, checker.CheckedAcquisitionInput(
        binding, _authority=checker._ACQUISITION_AUTHORITY)


def test_isolated_verified_certificate_reaches_existing_consumer_binding(monkeypatch):
    reader = load()
    checker, certificate = prospective_certificate()

    def binding(*args, **kwargs):
        raise RuntimeError('checked issuer reached binding without input IO')

    monkeypatch.setattr(checker.CheckedAcquisitionInput, 'binding_for', binding)
    with pytest.raises(RuntimeError, match='checked issuer reached binding'):
        reader.VerifiedAcquisitionInput(certificate, 'scientific-producer')
    certificate._binding['verified_plan']['execution_identity'] = 'UNREGISTERED'
    with pytest.raises(ValueError, match='UNVERIFIED_SOURCE_CERTIFICATE'):
        reader.VerifiedAcquisitionInput(certificate, 'scientific-producer')
    with pytest.raises(ValueError, match='independent authority'):
        checker.CheckedAcquisitionInput({})


def test_isolated_certificate_crosses_scientific_type_gate_without_granting_role(monkeypatch):
    path = ENTRY.with_name('p17_m2_scientific_independent.py')
    spec = importlib.util.spec_from_file_location('prospective_scientific_issuer_test', path)
    science = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(science)
    _, certificate = prospective_certificate()
    admission = object.__new__(science.CheckedBAdmission)
    admission.contract_sha256 = 'c' * 64
    monkeypatch.setattr(science, 'check_contract', lambda contract: 'c' * 64)
    with pytest.raises(ValueError, match='scientific reader role differs'):
        science.grant_scientific_input(certificate, {}, 'UNREGISTERED', admission)
    with pytest.raises(ValueError, match='independently accepted acquisition'):
        science.grant_scientific_input({'status': 'PASS'}, {}, 'UNREGISTERED', admission)


@pytest.mark.parametrize('attempt', [1, 2])
def test_registered_formal_roots_and_scientific_reader_keep_issuing_profile(monkeypatch, attempt):
    import json

    checker, certificate = prospective_certificate()
    policy = json.loads((ENTRY.parents[1] / checker.REGISTERED_PROTOCOL).read_bytes())
    generation = policy['fixed_target']['attempts'][str(attempt)]['generation']
    plan = {'execution_identity': checker.REGISTERED_IDENTITY, 'scope': checker.FORMAL_SCOPE,
            'binding': {'formal_attempt': attempt}, 'root': generation,
            'content_root': generation + '/content'}
    monkeypatch.setattr(checker, '_registered_authority', lambda value: policy)
    monkeypatch.setattr(checker, 'validate_binding', lambda value: None)
    assert checker._member_root(plan, 'content_root', Path(plan['content_root'])) == Path(
        plan['content_root'])
    path = ENTRY.with_name('p17_m2_scientific_independent.py')
    spec = importlib.util.spec_from_file_location('scientific_reader_profile_test', path)
    science = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(science)
    binding = dict(certificate._binding, verified_plan=plan)
    granted = science.CheckedScientificInput(binding, {}, _authority=science._SCIENCE_AUTHORITY)
    assert granted._reader_root(Path(plan['content_root'])) == Path(plan['content_root'])
    assert granted._reader_result_seconds() == (1800, 1800)
