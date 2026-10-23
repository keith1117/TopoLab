"""Read completeness at both public readers, using new local sources only."""

import importlib.util
import json
import os
from contextlib import contextmanager
from pathlib import Path

import pytest


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parents[1] / "scripts" / (name + ".py")
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


producer = load("p17_m2_input_export")
independent = load("p17_m2_input_export_independent")


def source_reader(kind, root, journal, stable):
    if kind == "producer":
        return producer.Reader(
            root, journal, execution_identity=producer.STABLE_IDENTITY if stable else None,
            source_identity_checks=stable,
        )
    return independent.OnceReader(root, 1, 1024, source_identity_checks=stable, journal=journal)


def early_eof(monkeypatch, returned):
    """Inject EOF at OS IO boundaries without changing file metadata."""
    real_fdopen, real_read = os.fdopen, os.read

    @contextmanager
    def fdopen(fd, *args, **kwargs):
        with real_fdopen(fd, *args, **kwargs) as stream:
            class ShortStream:
                def read(self, maximum):
                    return stream.read(min(maximum, returned))

            yield ShortStream()

    remaining = returned

    def read(fd, maximum):
        nonlocal remaining
        if not remaining:
            return b""
        chunk = real_read(fd, min(maximum, remaining))
        remaining -= len(chunk)
        return chunk

    monkeypatch.setattr(os, "fdopen", fdopen)
    monkeypatch.setattr(os, "read", read)


@pytest.mark.parametrize("kind", ["producer", "independent"])
@pytest.mark.parametrize("stable", [False, True])
@pytest.mark.parametrize("returned", [0, 1])
def test_short_read_stops_with_length_reason_and_unchanged_tuples(
    tmp_path, monkeypatch, kind, stable, returned
):
    source = tmp_path / "new-source.bin"
    source.write_bytes(b"abc")
    actual = source.stat()
    identity = {key: getattr(actual, key)
                for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")}
    journal = tmp_path / "new-journal.jsonl"
    reader = source_reader(kind, tmp_path, journal, stable)
    early_eof(monkeypatch, returned)
    real_open = os.open
    source_opens = []

    def open_file(path, *args, **kwargs):
        if path == source.name:
            source_opens.append(path)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(os, "open", open_file)
    with pytest.raises(ValueError, match="source read length differs from descriptor size"):
        reader.read(source.name, 1024)

    failure = reader.failures[0]
    assert failure["status"] == "STOP_NO_RETRY"
    assert failure["path"] == source.name and failure["attempt_ordinal"] == 1
    assert failure["stage"] == "read_size_consistency"
    assert failure["returned_bytes"] == returned
    assert failure["declared"] == failure["before"] == failure["after"] == identity
    assert failure.get("closing") is None
    assert failure["changed_fields"] == []
    assert "source read length differs" in failure["primary_reason"]
    assert json.loads(journal.read_bytes().splitlines()[-1]) == failure
    with pytest.raises(ValueError, match="reread|repeat"):
        reader.read(source.name, 1024)
    assert source_opens == [source.name]


@pytest.mark.parametrize("kind", ["producer", "independent"])
@pytest.mark.parametrize("returned", [0, 1, 3])
def test_tuple_change_keeps_identity_reason_even_with_short_read(
    tmp_path, monkeypatch, kind, returned
):
    source = tmp_path / "new-source.bin"
    source.write_bytes(b"abc")
    journal = tmp_path / "new-journal.jsonl"
    reader = source_reader(kind, tmp_path, journal, True)
    early_eof(monkeypatch, returned)
    real_fstat = os.fstat
    observations = []

    def fstat(fd):
        if len(observations) == 1:
            before = source.stat()
            os.utime(source, ns=(before.st_atime_ns, before.st_mtime_ns + 1))
        value = real_fstat(fd)
        observations.append(value)
        return value

    monkeypatch.setattr(os, "fstat", fstat)
    with pytest.raises(ValueError) as stopped:
        reader.read(source.name, 1024)

    reason = "STOP: source changed" if kind == "producer" else (
        "source changed during descriptor read")
    assert str(stopped.value) == reason
    failure = reader.failures[0]
    assert failure["status"] == "STOP_NO_RETRY"
    assert failure["primary_reason"] == reason
    assert failure["stage"] == "after_read_identity"
    assert failure["changed_fields"] == ["st_mtime_ns"]
    assert failure["returned_bytes"] == returned
    assert failure["after"]["st_mtime_ns"] == failure["before"]["st_mtime_ns"] + 1
    assert len(observations) == 2 and failure.get("closing") is None
    assert json.loads(journal.read_bytes().splitlines()[-1]) == failure


@pytest.mark.parametrize("kind", ["producer", "independent"])
@pytest.mark.parametrize("stable", [False, True])
def test_complete_read_accepts_existing_size_and_hash_with_short_os_chunks(
    tmp_path, monkeypatch, kind, stable
):
    source = tmp_path / "new-source.bin"
    source.write_bytes(b"abc")
    reader = source_reader(kind, tmp_path, tmp_path / "new-journal.jsonl", stable)
    real_read = os.read

    def read(fd, maximum):
        return real_read(fd, min(maximum, 1))

    monkeypatch.setattr(os, "read", read)
    kwargs = ({"size": 3, "expected": producer.sha(b"abc")} if kind == "producer"
              else {"byte_size": 3, "sha256": independent.digest(b"abc")})
    assert reader.read(source.name, 3, **kwargs) == b"abc"
    assert reader.failures == []
