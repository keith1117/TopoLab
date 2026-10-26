"""New public sources: prebound content policy and unchanged strict default."""
import hashlib
import importlib.util
import os
from contextlib import contextmanager
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "hash_bound_producer", Path(__file__).parents[1] / "scripts/p17_m2_input_export.py")
assert spec and spec.loader
producer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(producer)
POLICY = "topolab.source-identity.prebound-sha256.v1"


def test_prebound_mtime_change_keeps_raw_observations_and_same_buffer(tmp_path, monkeypatch):
    source = tmp_path / "public.bin"
    source.write_bytes(b"public bytes")
    initial = source.stat().st_mtime_ns
    real_fdopen = os.fdopen

    @contextmanager
    def mutate(fd, *args, **kwargs):
        with real_fdopen(fd, *args, **kwargs) as stream:
            class Stream:
                def read(self, maximum):
                    raw = stream.read(maximum)
                    os.utime(source, ns=(source.stat().st_atime_ns, initial + 89))
                    return raw
            yield Stream()

    monkeypatch.setattr(os, "fdopen", mutate)
    reader = producer.Reader(tmp_path, execution_identity=producer.LOCAL_IDENTITY,
                             source_identity_checks=True, source_identity_policy=POLICY)
    expected = hashlib.sha256(b"public bytes").hexdigest()
    assert reader.read(source.name, 100, expected=expected) == b"public bytes"
    row = reader.source_observations[0]
    assert row["expected_sha256"] == expected
    assert row["declared"]["st_mtime_ns"] == initial
    assert row["after"]["st_mtime_ns"] == initial + 89
    assert row["mtime_changes"] == {"before": 0, "after": 89, "closing": 89}


@pytest.mark.parametrize("expected,policy,reason", [
    (None, POLICY, "source changed"),
    (None, None, "source changed"),
    ("0" * 64, POLICY, "source SHA"),
])
def test_strict_or_wrong_hash_rejects_and_keeps_failure_context(
    tmp_path, monkeypatch, expected, policy, reason
):
    source = tmp_path / "public.bin"
    source.write_bytes(b"abc")
    original = source.stat().st_mtime_ns
    real_fdopen = os.fdopen

    @contextmanager
    def mutate(fd, *args, **kwargs):
        with real_fdopen(fd, *args, **kwargs) as stream:
            class Stream:
                def read(self, limit):
                    raw = stream.read(limit)
                    os.utime(source, ns=(source.stat().st_atime_ns, original + 89))
                    return raw
            yield Stream()

    monkeypatch.setattr(os, "fdopen", mutate)
    reader = producer.Reader(tmp_path, execution_identity=producer.LOCAL_IDENTITY,
                             source_identity_checks=True, source_identity_policy=policy)
    with pytest.raises(ValueError, match=reason):
        reader.read(source.name, 100, expected=expected)
    failure = reader.failures[0]
    assert failure["path"] == source.name
    assert failure["returned_bytes"] == 3
    assert failure["after"]["st_mtime_ns"] == original + 89
    assert failure["status"] == "STOP_NO_RETRY"
    with pytest.raises(ValueError, match="reread"):
        reader.read(source.name, 100, expected=expected)


@pytest.mark.parametrize("failure_mode", ["short", "replacement", "missing_closing"])
def test_prebound_hash_never_waives_other_guards(tmp_path, monkeypatch, failure_mode):
    source = tmp_path / "public.bin"
    source.write_bytes(b"abc")
    replacement = tmp_path / "replacement.bin"
    replacement.write_bytes(b"abc")
    real_fdopen = os.fdopen

    @contextmanager
    def mutate(fd, *args, **kwargs):
        with real_fdopen(fd, *args, **kwargs) as stream:
            class Stream:
                def read(self, limit):
                    raw = stream.read(1 if failure_mode == "short" else limit)
                    if failure_mode == "replacement":
                        replacement.replace(source)
                    elif failure_mode == "missing_closing":
                        source.unlink()
                    return raw
            yield Stream()

    monkeypatch.setattr(os, "fdopen", mutate)
    reader = producer.Reader(tmp_path, execution_identity=producer.LOCAL_IDENTITY,
                             source_identity_checks=True, source_identity_policy=POLICY)
    with pytest.raises((ValueError, FileNotFoundError)):
        reader.read(source.name, 100, expected=hashlib.sha256(b"abc").hexdigest())
    assert reader.failures[0]["status"] == "STOP_NO_RETRY"
    assert reader.source_observations == []


def test_custody_manifest_anchor_survives_directory_permission_writeback(tmp_path):
    control_spec = importlib.util.spec_from_file_location(
        "custody_integrity_control", Path(__file__).parents[1]
        / "scripts/p17_m2_source_acquisition_control.py")
    assert control_spec and control_spec.loader
    import sys
    control = importlib.util.module_from_spec(control_spec)
    sys.modules[control_spec.name] = control
    control_spec.loader.exec_module(control)
    custody = tmp_path / "new-public-custody"
    custody.mkdir(mode=0o700)
    member = custody / "receipt.json"
    member.write_bytes(b"{}\n")
    member.chmod(0o600)
    manifest = producer.canonical({"members": [{"path": "receipt.json", "byte_size": 3,
        "sha256": hashlib.sha256(b"{}\n").hexdigest()}]})
    anchor = hashlib.sha256(manifest).hexdigest()
    custody.chmod(0o555)
    first = control.verify_retained_evidence(custody, manifest, anchor)
    custody.chmod(0o700)
    second = control.verify_retained_evidence(custody, manifest, anchor)
    assert first["members"] == second["members"]
    assert first["directory_modes"] != second["directory_modes"]
    member.write_bytes(b"[]\n")
    with pytest.raises(ValueError, match="SHA"):
        control.verify_retained_evidence(custody, manifest, anchor)


def test_custody_rejects_unlisted_directory_without_enumerating_it(tmp_path, monkeypatch):
    control_spec = importlib.util.spec_from_file_location(
        "custody_whitelist_control", Path(__file__).parents[1]
        / "scripts/p17_m2_source_acquisition_control.py")
    assert control_spec and control_spec.loader
    import sys
    control = importlib.util.module_from_spec(control_spec)
    sys.modules[control_spec.name] = control
    control_spec.loader.exec_module(control)
    root = tmp_path / "new-public-custody"
    root.mkdir(mode=0o700)
    (root / "receipt").write_bytes(b"abc")
    (root / "receipt").chmod(0o600)
    unexpected = root / "unregistered"
    unexpected.mkdir(mode=0o700)
    unknown_inode = unexpected.stat().st_ino
    real_listdir, real_scandir = os.listdir, os.scandir

    def listdir(fd):
        if isinstance(fd, int) and os.fstat(fd).st_ino == unknown_inode:
            pytest.fail("enumerated unregistered directory")
        return real_listdir(fd)

    def scandir(fd):
        if isinstance(fd, int) and os.fstat(fd).st_ino == unknown_inode:
            pytest.fail("enumerated unregistered directory")
        return real_scandir(fd)

    monkeypatch.setattr(os, "listdir", listdir)
    monkeypatch.setattr(os, "scandir", scandir)
    manifest = producer.canonical({"members": [{"path": "receipt", "byte_size": 3,
        "sha256": hashlib.sha256(b"abc").hexdigest()}]})
    with pytest.raises(ValueError, match="WHITELIST"):
        control.verify_retained_evidence(root, manifest, hashlib.sha256(manifest).hexdigest())
