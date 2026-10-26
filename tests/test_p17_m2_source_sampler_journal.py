"""Complete sampler evidence fits fixed acquisition file bounds without less sampling."""

import base64
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]



@pytest.fixture(autouse=True)
def isolated_native_adapter_module():
    # Acquisition adapters customize this module per CLI invocation. Keep the
    # prior default/native/SCI callers' module object entirely untouched.
    name = "p17_m2_resource_control"
    previous = sys.modules.pop(name, None)
    try:
        yield
    finally:
        sys.modules.pop(name, None)
        if previous is not None:
            sys.modules[name] = previous


def controller():
    spec = importlib.util.spec_from_file_location(
        "source_sampler_journal_test", REPO / "scripts/p17_m2_source_acquisition_control.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def setup(tmp_path):
    control = controller()
    root = tmp_path / "topolab-public-hash-bound-sampler-storage"
    root.mkdir(mode=0o700)
    folder = root / "receipts" / "public-consumer" / "public-consumer"
    folder.mkdir(parents=True, mode=0o700)
    transport = control.AcquisitionTransport(root, "1" * 64)
    native = transport.native_module(root)
    return control, root, folder, transport, native


def save_sample(control, native, folder, index, raw=b"native bytes\x00\xff\n"):
    profile = folder / f"sampler-{index}.time"
    profile.write_bytes(raw)
    helper = {"role": f"rss-sampler-{index}", "profile": profile.name,
              "profile_sha256": control.base().sha(raw), "problem": None,
              "cleanup": {"group_gone": True}, "timer_native_exit": {"exit_code": 0}}
    native.atomic_new(folder / f"sampler-{index}.json", helper)
    return helper



def saved_record(native, folder, helpers):
    native.atomic_new(folder / "command.json", {"helpers": helpers})
    return json.loads((folder / "command.json").read_bytes())


def test_three_hundred_complete_samples_fit_unchanged_evidence_file_cap(tmp_path):
    control, root, folder, transport, native = setup(tmp_path)
    helpers = [save_sample(control, native, folder, index) for index in range(300)]
    assert transport.namespace_check(root)["evidence_count"] < 512
    raw = (folder / "sampler-evidence.jsonl").read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    assert len(rows) == 300
    assert rows[-1]["helper"] == helpers[-1]
    assert base64.b64decode(rows[-1]["profile_base64"], validate=True) == b"native bytes\x00\xff\n"
    profiles = transport.helper_profiles_reader(folder, saved_record(native, folder, helpers))
    assert profiles["sampler-299.time"] == b"native bytes\x00\xff\n"
    assert not list(folder.glob("sampler-*.time"))


def test_independent_audit_rejects_truncated_journal_even_with_complete_json(tmp_path):
    control, _, folder, transport, native = setup(tmp_path)
    helper = save_sample(control, native, folder, 0)
    record = saved_record(native, folder, [helper])
    journal = folder / "sampler-evidence.jsonl"
    journal.write_bytes(journal.read_bytes().removesuffix(b"\n"))
    with pytest.raises(ValueError, match="journal final newline"):
        transport.helper_profiles_reader(folder, record)


@pytest.mark.parametrize("change", ["hash", "short", "replacement", "missing_close"])
def test_profile_observation_failures_retain_original_bytes_and_helper(
    tmp_path, monkeypatch, change
):
    control, _, folder, _, native = setup(tmp_path)
    raw = b"complete original native profile\n"
    profile = folder / "sampler-0.time"
    profile.write_bytes(raw)
    helper = {"role": "rss-sampler-0", "profile": profile.name,
              "profile_sha256": control.base().sha(raw), "problem": None}
    if change == "hash":
        helper["profile_sha256"] = "0" * 64
    original_read, original_stat = control.os.read, control.os.stat
    reads = observations = 0

    def shortened(fd, amount):
        nonlocal reads
        reads += 1
        return original_read(fd, 1) if reads == 1 else b""

    def changed(path, *args, **kwargs):
        nonlocal observations
        if path == profile.name and kwargs.get("dir_fd") is not None:
            observations += 1
            if change == "replacement":
                replacement = folder / "replacement"
                replacement.write_bytes(raw)
                replacement.replace(profile)
            elif change == "missing_close" and observations == 1:
                raise OSError("closing observation unavailable")
        return original_stat(path, *args, **kwargs)

    with monkeypatch.context() as guard:
        if change == "short":
            guard.setattr(control.os, "read", shortened)
        elif change in {"replacement", "missing_close"}:
            guard.setattr(control.os, "stat", changed)
        with pytest.raises((ValueError, OSError)):
            native.atomic_new(folder / "sampler-0.json", helper)
    assert profile.read_bytes() == raw
    retained = json.loads((folder / "sampler-0.json").read_bytes())
    assert retained["profile_sha256"] == helper["profile_sha256"]
    assert retained["sampler_journal_failure"]["reason"]
    assert not (folder / "sampler-evidence.jsonl").exists()


def test_failed_durable_append_keeps_raw_profile_and_complete_failure_metadata(
    tmp_path, monkeypatch
):
    control, _, folder, _, native = setup(tmp_path)
    original_fsync = control.os.fsync
    calls = 0

    def fail_first(fd):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("injected durable append failure")
        return original_fsync(fd)

    with monkeypatch.context() as guard:
        guard.setattr(control.os, "fsync", fail_first)
        with pytest.raises(OSError, match="durable append failure"):
            save_sample(control, native, folder, 0)
    assert (folder / "sampler-0.time").read_bytes() == b"native bytes\x00\xff\n"
    assert (folder / "sampler-evidence.jsonl").read_bytes()
    failure = json.loads((folder / "sampler-0.json").read_bytes())
    assert failure["sampler_journal_failure"]["reason"] == "injected durable append failure"


@pytest.mark.parametrize("change", [
    "metadata", "hash", "identity", "missing", "order", "extra_field", "count",
])
def test_independent_audit_rejects_journal_mismatch(tmp_path, change):
    control, _, folder, transport, native = setup(tmp_path)
    helper = save_sample(control, native, folder, 0)
    record = saved_record(native, folder, [helper])
    journal = folder / "sampler-evidence.jsonl"
    row = json.loads(journal.read_bytes())
    if change == "metadata":
        row["helper"]["cleanup"]["group_gone"] = False
    elif change == "hash":
        row["profile_base64"] = base64.b64encode(b"wrong native bytes").decode()
    elif change == "identity":
        row["profile_identity"]["st_ino"] = True
    elif change == "order":
        row["index"] = 1
    elif change == "extra_field":
        row["unknown"] = "unregistered metadata"
    elif change == "count":
        record["helpers"] = []
    elif change == "missing":
        journal.unlink()
    if change != "missing":
        journal.write_bytes(control.base().canonical(row))
        # A faulty producer may bind malformed bytes; raw SHA alone cannot
        # replace independent full metadata/order/provenance reconciliation.
        record["sampler_journal_sha256"] = control.base().sha(journal.read_bytes())
    with pytest.raises((ValueError, FileNotFoundError)):
        transport.helper_profiles_reader(folder, record)


def test_zero_helper_native_failure_keeps_primary_record_and_missing_evidence_context(tmp_path):
    _, root, folder, transport, native = setup(tmp_path)
    record = {"helpers": [], "exit_code": 7, "software_result": "FAIL_PUBLIC_COMMAND"}
    native.atomic_new(folder / "command.json", record)
    assert record["sampler_evidence_storage"] == "topolab.source-sampler-evidence.v1"
    assert record["sampler_journal_sha256"] is None
    assert record["sampler_journal_binding_failure"]["type"] == "FileNotFoundError"
    (folder / "command.time").write_bytes(b"failure native profile")
    (folder / "command.log").write_bytes(b"primary command failed")
    evidence = transport.resource_evidence(root, "1" * 64, "public-consumer", tolerate_missing=True)
    assert evidence["inner_evidence"]["record"] == record
    assert evidence["inner_evidence"]["helper_profiles"] == {}
    assert any("sampler-evidence.jsonl" in row["reason"]
               for row in evidence["resource_read_failures"])


@pytest.mark.parametrize("kind", ["fifo", "symlink", "empty", "malformed", "not_object"])
def test_independent_journal_requires_complete_regular_canonical_rows(tmp_path, kind):
    control, _, folder, transport, native = setup(tmp_path)
    helper = save_sample(control, native, folder, 0)
    record = saved_record(native, folder, [helper])
    journal = folder / "sampler-evidence.jsonl"
    journal.unlink()
    if kind == "fifo":
        os.mkfifo(journal)
    elif kind == "symlink":
        journal.symlink_to(folder / "sampler-0.time")
    elif kind == "empty":
        journal.write_bytes(b"")
    elif kind == "malformed":
        journal.write_bytes(b"{broken\n")
    else:
        journal.write_bytes(b"[]\n")
    if kind not in {"fifo", "symlink"}:
        record["sampler_journal_sha256"] = control.base().sha(journal.read_bytes())
    with pytest.raises((ValueError, OSError)):
        transport.helper_profiles_reader(folder, record)


def test_incomplete_append_preserves_native_profile_helper_and_partial_journal(
    tmp_path, monkeypatch
):
    control, _, folder, _, native = setup(tmp_path)
    original_write = control.os.write

    def short_append(fd, raw):
        return original_write(fd, raw[:-1])

    with monkeypatch.context() as guard:
        guard.setattr(control.os, "write", short_append)
        with pytest.raises(ValueError, match="SAMPLER_JOURNAL_SHORT_APPEND"):
            save_sample(control, native, folder, 0)
    assert (folder / "sampler-0.time").read_bytes() == b"native bytes\x00\xff\n"
    assert (folder / "sampler-evidence.jsonl").read_bytes()
    helper = json.loads((folder / "sampler-0.json").read_bytes())
    assert helper["sampler_journal_failure"]["reason"] == "SAMPLER_JOURNAL_SHORT_APPEND"


def test_wrong_final_profile_observation_keeps_durable_journal_and_replacement(
    tmp_path, monkeypatch
):
    control, _, folder, _, native = setup(tmp_path)
    original_stat = control.os.stat
    observations = 0

    def replace_on_final(path, *args, **kwargs):
        nonlocal observations
        if path == "sampler-0.time" and kwargs.get("dir_fd") is not None:
            observations += 1
            if observations == 2:
                replacement = folder / "replacement"
                replacement.write_bytes(b"native bytes\x00\xff\n")
                replacement.replace(folder / path)
        return original_stat(path, *args, **kwargs)

    with monkeypatch.context() as guard:
        guard.setattr(control.os, "stat", replace_on_final)
        with pytest.raises(ValueError, match="SAMPLER_PROFILE_CLOSING_OBSERVATION_CHANGED"):
            save_sample(control, native, folder, 0)
    assert (folder / "sampler-0.time").read_bytes() == b"native bytes\x00\xff\n"
    assert (folder / "sampler-evidence.jsonl").read_bytes()
    assert (folder / "sampler-0.json").exists()


def test_native_command_record_binds_full_journal_including_original_metadata(tmp_path):
    control, _, folder, transport, native = setup(tmp_path)
    helper = save_sample(control, native, folder, 0)
    native.atomic_new(folder / "command.json", {"helpers": [helper]})
    record = json.loads((folder / "command.json").read_bytes())
    journal = folder / "sampler-evidence.jsonl"
    assert record["sampler_evidence_storage"] == "topolab.source-sampler-evidence.v1"
    assert record["sampler_journal_sha256"] == control.base().sha(journal.read_bytes())
    row = json.loads(journal.read_bytes())
    row["profile_identity"]["st_mtime_ns"] += 1
    journal.write_bytes(control.base().canonical(row))
    with pytest.raises(ValueError, match="journal complete-byte binding"):
        transport.helper_profiles_reader(folder, record)
