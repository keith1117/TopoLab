"""Independent registration seams on temporary synthetic bytes only."""

import hashlib
import importlib.util
import os
import stat
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def subject():
    path = REPO / 'scripts/staged_public_binding_independent.py'
    spec = importlib.util.spec_from_file_location('synthetic_staged_independent', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def fixture(module, root):
    expected = {}
    for item in module.metadata_specs():
        raw = ('synthetic public metadata: ' + item['path'] + '\n').encode()
        path = root / item['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        expected[item['path']] = (len(raw), hashlib.sha256(raw).hexdigest())
    return expected


def test_independent_scan_reads_exact23_and_compares_original_four_points(tmp_path):
    module = subject()
    expected = fixture(module, tmp_path)
    assert len(expected) == 23
    assert list(expected)[:2] == [
        'b4-30-z-reflection-repair-v2/sentinel/reference/progress.json',
        'b4-30-z-reflection-repair-v2/sentinel/reference/summary.json']
    assert list(expected)[-1].endswith('/units/0017.json')
    a = module.scan(tmp_path, expected, availability=True)
    b = module.scan(tmp_path, expected, availability=True)
    primary = module.scan(tmp_path, expected, availability=False)
    independent = module.scan(tmp_path, expected, availability=False)
    rows = module.compare(expected, a, b, primary, independent)
    assert rows == independent
    assert [r['path'] for r in rows] == list(expected)
    for row in rows:
        assert row['sha256'] == expected[row['path']][1]
        for key in ('declared', 'before', 'after', 'closing'):
            assert row[key]['st_uid'] == os.getuid()
            assert row[key]['st_nlink'] == 1
            assert {k: row[key][k] for k in row['physical']} == row['physical']
    assert all(row['sha256'] is None for row in a)


def test_availability_never_reads_file_content_and_expected_map_gates_before_open(
    tmp_path, monkeypatch
):
    module = subject()
    expected = fixture(module, tmp_path)
    monkeypatch.setattr(module.os, 'read', lambda *_: pytest.fail('availability content read'))
    assert len(module.scan(tmp_path, expected, availability=True)) == 23
    monkeypatch.setattr(module.os, 'open', lambda *_a, **_k: pytest.fail('unadmitted source open'))
    wrong = dict(expected)
    del wrong[next(iter(wrong))]
    with pytest.raises(ValueError, match='exact23'):
        module.scan(tmp_path, wrong, availability=False)
    wrong = dict(expected)
    first = next(iter(wrong))
    wrong[first] = (True, expected[first][1])
    with pytest.raises(ValueError, match='size/SHA'):
        module.scan(tmp_path, wrong, availability=False)


@pytest.mark.parametrize('fault', ['symlink', 'hardlink', 'fifo', 'directory', 'parent-link'])
def test_nonordinary_files_and_symlink_parent_stop_without_content_read(
    tmp_path, monkeypatch, fault
):
    module = subject()
    expected = fixture(module, tmp_path)
    first = next(iter(expected))
    path = tmp_path / first
    if fault == 'parent-link':
        moved = path.parent.with_name('outside-reference')
        path.parent.rename(moved)
        path.parent.symlink_to(moved, target_is_directory=True)
    else:
        path.unlink()
        if fault == 'symlink':
            path.symlink_to(tmp_path / list(expected)[1])
        elif fault == 'hardlink':
            other = tmp_path / 'owned-but-shared'
            other.write_bytes(b'x' * expected[first][0])
            os.link(other, path)
        elif fault == 'fifo':
            os.mkfifo(path)
        else:
            path.mkdir()
    monkeypatch.setattr(module.os, 'read', lambda *_: pytest.fail('nonordinary source read'))
    with pytest.raises((ValueError, OSError)):
        module.scan(tmp_path, expected, availability=False)


@pytest.mark.parametrize('fault', ['sha', 'short-read', 'extra-byte'])
def test_exact_hash_byte_count_and_real_eof_are_required(tmp_path, monkeypatch, fault):
    module = subject()
    expected = fixture(module, tmp_path)
    first = next(iter(expected))
    if fault == 'sha':
        p = tmp_path / first
        raw = p.read_bytes()
        p.write_bytes(b'!' + raw[1:])
    else:
        original = module.os.read
        reads = 0

        def altered(fd, maximum):
            nonlocal reads
            reads += 1
            if fault == 'short-read' and reads == 1:
                return b''
            if fault == 'extra-byte' and reads == 2:
                return b'!'
            return original(fd, maximum)

        monkeypatch.setattr(module.os, 'read', altered)
    with pytest.raises(ValueError, match='SHA|EOF|byte cap'):
        module.scan(tmp_path, expected, availability=False)


@pytest.mark.parametrize('replace_root', [False, True])
def test_same_byte_path_or_root_replacement_cannot_become_stable_observation(
    tmp_path, monkeypatch, replace_root
):
    module = subject()
    source = tmp_path / 'source'
    source.mkdir()
    expected = fixture(module, source)
    first = next(iter(expected))
    original = module.os.read
    changed = False

    def swap(fd, maximum):
        nonlocal changed
        raw = original(fd, maximum)
        if raw and not changed:
            changed = True
            if replace_root:
                source.rename(tmp_path / 'original-source')
                source.mkdir()
                fixture(module, source)
            else:
                replacement = tmp_path / 'same-bytes-new-inode'
                replacement.write_bytes(raw)
                replacement.replace(source / first)
        return raw

    monkeypatch.setattr(module.os, 'read', swap)
    with pytest.raises(ValueError, match='file|directory|path'):
        module.scan(source, expected, availability=False)


def test_actual_after_fstat_is_checked_and_foreign_owner_is_refused(tmp_path, monkeypatch):
    from types import SimpleNamespace

    module = subject()
    expected = fixture(module, tmp_path)
    original = module.os.fstat
    regular_calls = 0

    def changed(fd):
        nonlocal regular_calls
        info = original(fd)
        if stat.S_ISREG(info.st_mode):
            regular_calls += 1
            if regular_calls == 2:
                values = {k: getattr(info, k) for k in (*module.POINT, 'st_ctime_ns')}
                values['st_mtime_ns'] += 1
                return SimpleNamespace(**values)
        return info

    monkeypatch.setattr(module.os, 'fstat', changed)
    with pytest.raises(ValueError, match='changed during'):
        module.scan(tmp_path, expected, availability=False)
    assert regular_calls == 2
    monkeypatch.setattr(module.os, 'fstat', original)
    uid = os.getuid()
    monkeypatch.setattr(module.os, 'getuid', lambda: uid + 1)
    with pytest.raises(ValueError, match='owner'):
        module.scan(tmp_path, expected, availability=False)


def test_declared_to_open_change_stops_before_read_and_keeps_original_points(tmp_path, monkeypatch):
    from types import SimpleNamespace

    module = subject()
    expected = fixture(module, tmp_path)
    original = module.os.fstat

    def changed(fd):
        info = original(fd)
        if stat.S_ISREG(info.st_mode):
            values = {k: getattr(info, k) for k in (*module.POINT, 'st_ctime_ns')}
            values['st_ctime_ns'] += 1
            return SimpleNamespace(**values)
        return info

    monkeypatch.setattr(module.os, 'fstat', changed)
    monkeypatch.setattr(module.os, 'read', lambda *_: pytest.fail('changed source read'))
    with pytest.raises(ValueError, match='before read') as failure:
        module.scan(tmp_path, expected, availability=False)
    prefix = failure.value.binding_prefix
    assert len(prefix) == 1 and prefix[0]['path'] == next(iter(expected))
    assert set(prefix[0]) == {'path', 'sha256', 'declared', 'before'}
    assert prefix[0]['declared'] == prefix[0]['before']


@pytest.mark.parametrize('fault', [
    'missing', 'duplicate', 'order', 'bool-physical', 'float-point', 'missing-point',
    'link-point', 'owner-point', 'different-tuple', 'bad-sha', 'availability-sha', 'extra-field',
])
def test_compare_rejects_incomplete_or_tampered_evidence(tmp_path, fault):
    module = subject()
    expected = fixture(module, tmp_path)
    a = module.scan(tmp_path, expected, availability=True)
    b = module.scan(tmp_path, expected, availability=True)
    primary = module.scan(tmp_path, expected, availability=False)
    independent = module.scan(tmp_path, expected, availability=False)
    baseline = deepcopy(independent)
    if fault == 'missing':
        independent.pop()
    elif fault == 'duplicate':
        independent[-1] = independent[0]
    elif fault == 'order':
        independent[0], independent[1] = independent[1], independent[0]
    elif fault == 'bool-physical':
        independent[0]['physical']['st_ino'] = True
    elif fault == 'float-point':
        independent[0]['after']['st_dev'] = float(independent[0]['after']['st_dev'])
    elif fault == 'missing-point':
        del independent[0]['closing']
    elif fault == 'link-point':
        independent[0]['closing']['st_nlink'] = 2
    elif fault == 'owner-point':
        independent[0]['before']['st_uid'] += 1
    elif fault == 'different-tuple':
        independent[0]['physical']['st_mtime_ns'] += 1
        for key in module.OBSERVATIONS:
            independent[0][key]['st_mtime_ns'] += 1
    elif fault == 'bad-sha':
        independent[0]['sha256'] = '0' * 64
    elif fault == 'availability-sha':
        a[0]['sha256'] = primary[0]['sha256']
    else:
        independent[0]['fabricated'] = True
    with pytest.raises(ValueError):
        module.compare(expected, a, b, primary, independent)
    assert primary == baseline
