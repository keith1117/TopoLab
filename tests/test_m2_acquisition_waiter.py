"""Bounded metadata waits never read a source/payload or weaken source gates."""
import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def module():
    spec = importlib.util.spec_from_file_location(
        'm2_waiter_test', REPO / 'scripts/await_m2_acquisition_receipt.py')
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_actual_cohort_schedule_and_failed407761ms_regression():
    result = subprocess.run(['node', '--test', 'tests/test_m2_acquisition_cohort.mjs',
                             'tests/test_p17_m2_permission_preflight.mjs'],
                            cwd=REPO, capture_output=True, timeout=10)
    assert result.returncode == 0, result.stdout + result.stderr


def test_wait_refuses_old_or_unknown_root_before_any_read(monkeypatch):
    api = module()
    monkeypatch.setattr(api, 'read_metadata', lambda *a: pytest.fail('old root was read'))
    for root in ('/private/tmp/topolab-public-registered-source-acquisition-20261104-v2',
                 '/private/tmp/unregistered', 'relative/root'):
        with pytest.raises(ValueError, match='literal root'):
            api.wait(root, 'plan', 1)


def test_wait_is_finitely_bounded_and_does_not_invent_receipt(monkeypatch):
    api = module()
    clock = [0.0]
    monkeypatch.setattr(api.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(api.time, 'sleep', lambda seconds: clock.__setitem__(0, clock[0] + seconds))
    monkeypatch.setattr(api, 'read_metadata', lambda *a: (_ for _ in ()).throw(FileNotFoundError()))
    with pytest.raises(TimeoutError, match='bounded'):
        api.wait(api.PUBLIC, 'plan', 1)
    assert 1 <= clock[0] < 1.1
    with pytest.raises(ValueError, match='160'):
        api.wait(api.PUBLIC, 'plan', 161)


def test_projection_preserves_exact_original_millisecond_lexemes():
    api = module()
    assert api.milliseconds(api.Decimal('1793786884.990')) == 1793786884990
    with pytest.raises(ValueError, match='integer milliseconds'):
        api.milliseconds(api.Decimal('1793786884.9901'))


def test_wrong_identity_and_unaccepted_source_proof_refused():
    api = module()
    with pytest.raises(ValueError, match='identity'):
        api.project({'execution_identity': 'old'}, b'{}', api.PUBLIC)
    proof = {'result': {'full_role_evidence_accepted': False}, 'raw_tool_events': []}
    with pytest.raises(ValueError, match='actual accepted'):
        api.role_projection(proof, 'a' * 64, 'independent-r0')
