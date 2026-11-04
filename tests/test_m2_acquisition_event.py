"""Courier bytes are retained verbatim; event acceptance is a separate strict operation."""
import importlib.util
import json
import stat
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def module():
    spec = importlib.util.spec_from_file_location('m2_event_test',
        REPO / 'scripts/file_m2_acquisition_event.py')
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def test_courier_preserves_original_raw_output_and_independent_new_file(tmp_path, monkeypatch):
    api = module()
    monkeypatch.setattr(api, 'EVIDENCE', tmp_path)
    packet = {'schema': 'topolab.v2.m2-strict-source-binding.actual-call.v1',
              'responses': [{'result': {'output': '{"mtime_ns":1790843026136346817}\n'}}]}
    path = tmp_path / 'new-packet.json'
    written = api.persist(packet, str(path))
    assert json.loads(path.read_bytes()) == packet
    original = packet['responses'][0]['result']['output']
    assert json.loads(path.read_bytes())['responses'][0]['result']['output'] == original
    assert stat.S_IMODE(path.stat().st_mode) == 0o600 and path.stat().st_nlink == 1
    assert written['bytes'] == len(path.read_bytes())
    with pytest.raises(FileExistsError):
        api.persist(packet, str(path))


def test_courier_rejects_escaped_or_symlink_parent(tmp_path, monkeypatch):
    api = module()
    monkeypatch.setattr(api, 'EVIDENCE', tmp_path)
    packet = {'schema': 'topolab.m2-acquisition-caller-failure.v1', 'original_rows': []}
    target = tmp_path / 'real'
    target.mkdir()
    link = tmp_path / 'alias'
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises((OSError, AssertionError)):
        api.persist(packet, str(link / 'must-not-exist.json'))
    assert list(target.iterdir()) == []
    with pytest.raises(AssertionError):
        api.persist(packet, str(tmp_path / '..' / 'escape.json'))


def test_closed_attempt_event_refuses_before_loading_any_helper(monkeypatch):
    api = module()
    monkeypatch.setattr(api, 'load', lambda: pytest.fail('closed attempt reached helper IO'))
    with pytest.raises(AssertionError, match='literal root'):
        api.file_event('/private/tmp/topolab-public-registered-source-acquisition-20261104-v2',
                       'a' * 64, 'exporter-r0', 'supervise', '/absent', 'b' * 64)
