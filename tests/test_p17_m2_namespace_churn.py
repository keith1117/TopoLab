"""Capacity inventories of NEW trees tolerate finite owned temporary-file churn."""

import errno
import importlib.util
import os
import sys
from pathlib import Path

import pytest


def control():
    path = Path(__file__).parents[1] / 'scripts/p17_m2_content_verified_control.py'
    spec = importlib.util.spec_from_file_location('namespace_churn_test', path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_completed_sampler_unlink_during_capacity_inventory_gets_complete_rescan(
    tmp_path, monkeypatch
):
    module = control()
    root = tmp_path / 'topolab-public-namespace-one-churn'
    root.mkdir(mode=0o700)
    (root / 'retained-evidence').write_bytes(b'abc')
    (root / 'sampler-0.time').write_bytes(b'transient')
    original = os.listdir
    removed = False

    def listed_then_unlinked(fd):
        nonlocal removed
        names = original(fd)
        if not removed and 'sampler-0.time' in names:
            os.unlink('sampler-0.time', dir_fd=fd)
            removed = True
        return names

    monkeypatch.setattr(module.os, 'listdir', listed_then_unlinked)
    result = module.namespace_check(root)
    assert result['count'] == result['evidence_count'] == 1
    assert result['size'] == result['evidence_size'] == 3
    assert (root / 'retained-evidence').read_bytes() == b'abc'


def test_continuously_changing_capacity_inventory_stops_with_complete_attempt_context(
    tmp_path, monkeypatch
):
    module = control()
    root = tmp_path / 'topolab-public-namespace-continuous-churn'
    root.mkdir(mode=0o700)
    original = os.listdir
    snapshots = 0

    def always_unlink_after_listing(fd):
        nonlocal snapshots
        name = f'sampler-{snapshots}.time'
        out = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=fd)
        os.close(out)
        names = original(fd)
        os.unlink(name, dir_fd=fd)
        snapshots += 1
        return names

    monkeypatch.setattr(module.os, 'listdir', always_unlink_after_listing)
    with pytest.raises(FileNotFoundError) as caught:
        module.namespace_check(root)
    assert snapshots == 3
    assert caught.value.errno == errno.ENOENT
    assert len(caught.value.namespace_inventory_failures) == 3
    assert [r['entry'] for r in caught.value.namespace_inventory_failures] == [
        'sampler-0.time', 'sampler-1.time', 'sampler-2.time'
    ]
    assert all(f'sampler-{i}.time' in str(caught.value) for i in range(3))


def test_capacity_inventory_rejects_root_replaced_during_scan(tmp_path, monkeypatch):
    module = control()
    root = tmp_path / 'topolab-public-namespace-root-replaced'
    root.mkdir(mode=0o700)
    moved = root.with_name(root.name + '-original')
    original = os.listdir
    replaced = False

    def replace_after_listing(fd):
        nonlocal replaced
        names = original(fd)
        if not replaced:
            root.rename(moved)
            root.mkdir(mode=0o700)
            replaced = True
        return names

    monkeypatch.setattr(module.os, 'listdir', replace_after_listing)
    with pytest.raises(ValueError, match='NAMESPACE_ROOT_IDENTITY_CHANGED'):
        module.namespace_check(root)


def test_capacity_inventory_rejects_root_ABA_opened_at_closing_observation(
    tmp_path, monkeypatch
):
    module = control()
    root = tmp_path / 'topolab-public-namespace-root-ABA'
    root.mkdir(mode=0o700)
    (root / 'evidence').write_bytes(b'a')
    saved = root.with_name(root.name + '-original')
    replacement = root.with_name(root.name + '-replacement')
    original = os.open
    root_opens = 0

    def open_with_temporary_replacement(path, flags, *args, **kwargs):
        nonlocal root_opens
        if path == root.name:
            root_opens += 1
            if root_opens == 2:
                root.rename(saved)
                root.mkdir(mode=0o700)
                (root / 'evidence').write_bytes(b'bbbbbbb')
                descriptor = original(path, flags, *args, **kwargs)
                root.rename(replacement)
                saved.rename(root)
                return descriptor
        return original(path, flags, *args, **kwargs)

    monkeypatch.setattr(module.os, 'open', open_with_temporary_replacement)
    with pytest.raises(ValueError, match='NAMESPACE_ROOT_IDENTITY_CHANGED'):
        module.namespace_check(root)


@pytest.mark.parametrize('with_errno', [False, True])
def test_inventory_rescan_context_survives_later_permission_failure(
    tmp_path, monkeypatch, with_errno
):
    module = control()
    root = tmp_path / 'topolab-public-namespace-late-permission'
    root.mkdir(mode=0o700)
    (root / 'sampler-0.time').write_bytes(b'transient')
    original = os.listdir
    snapshots = 0

    def disappear_then_deny(fd):
        nonlocal snapshots
        snapshots += 1
        if snapshots > 1:
            if with_errno:
                raise PermissionError(errno.EACCES, 'late enumeration denial', 'public-directory')
            raise PermissionError('late enumeration denial')
        names = original(fd)
        os.unlink('sampler-0.time', dir_fd=fd)
        return names

    monkeypatch.setattr(module.os, 'listdir', disappear_then_deny)
    with pytest.raises(PermissionError, match='late enumeration denial') as caught:
        module.namespace_check(root)
    assert 'sampler-0.time' in str(caught.value)
    assert len(caught.value.namespace_inventory_failures) == 1
    assert caught.value.errno == (errno.EACCES if with_errno else None)
    assert caught.value.filename == ('public-directory' if with_errno else None)


@pytest.mark.parametrize('kind', ['symlink', 'hardlink', 'cap', 'permission'])
def test_capacity_inventory_does_not_retry_other_failures(tmp_path, monkeypatch, kind):
    module = control()
    root = tmp_path / ('topolab-public-namespace-fail-' + kind)
    root.mkdir(mode=0o700)
    stable = root / 'evidence'
    stable.write_bytes(b'abc')
    if kind == 'symlink':
        (root / 'link').symlink_to(stable)
    elif kind == 'hardlink':
        os.link(stable, root / 'link')
    original = os.listdir
    snapshots = 0

    def counted(fd):
        nonlocal snapshots
        snapshots += 1
        if kind == 'permission':
            raise PermissionError('injected enumeration denial')
        return original(fd)

    monkeypatch.setattr(module.os, 'listdir', counted)
    with pytest.raises(PermissionError if kind == 'permission' else ValueError):
        module.namespace_check(root, additional_files=512 if kind == 'cap' else 0)
    assert snapshots == 1
