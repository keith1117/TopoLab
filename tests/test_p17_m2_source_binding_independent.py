"""Independently authored strict registration on newly written public sources."""

import importlib.util
import os
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
IDENTITY = "topolab.v2.p17-source-binding-and-conditional-repair.20261103.v1"
AUTHOR = "/root/binding_route_independent_v1"
PATHS = (
    "b4-30-z-reflection-repair-v2/sentinel/reference/progress.json",
    "b4-30-z-reflection-repair-v2/sentinel/reference/summary.json",
    *(f"b4-5-weighted-terminal/fit/units/{i:04d}.json" for i in range(3)),
    *(f"b4-30-z-reflection-repair-v2/sentinel/reference/units/{i:04d}.json"
      for i in range(18)),
)


def load_binding():
    spec = importlib.util.spec_from_file_location(
        "strict_binding_independent_test", REPO / "scripts/p17_m2_source_binding_independent.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def public_source(tmp_path):
    source = tmp_path / "topolab-public-source-binding" / "public-source"
    for name in PATHS:
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"{}\n")
    context = {
        "execution_identity": IDENTITY,
        "scope": "PUBLIC_STRICT_BINDING_REGISTRATION_ONLY",
        "attempt": 1,
        "source_root": str(source),
        "authority_sha256": "1" * 64,
        "source_tree": {"scripts/p17_m2_source_binding_independent.py": "2" * 64},
        "actors": {"producer": "/root", "independent": AUTHOR},
    }
    return source, context


def producer_wire(source, context):
    spec = importlib.util.spec_from_file_location(
        "strict_binding_public_producer", REPO / "scripts/p17_m2_input_export.py")
    assert spec and spec.loader
    producer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(producer)
    reader = producer.Reader(source, execution_identity=producer.LOCAL_IDENTITY,
                             source_identity_checks=True)
    for ordinal, name in enumerate(PATHS):
        reader.read(name, 1048576 if ordinal < 2 else 32768)
    return {
        "schema": "topolab.v2.m2-strict-source-binding.read.v1",
        **deepcopy(context),
        "role": "producer", "author": "/root",
        "rows": reader.source_observations, "attempts": list(PATHS), "failures": [],
        "helper_execution_identity": producer.LOCAL_IDENTITY,
        "helper_identity_relabelled": False,
        "source_identity_policy": None, "pre_read_expected_sha256": None,
    }


def test_registers_exact23_complete_strict_observations_without_bootstrap_hash(tmp_path):
    source, context = public_source(tmp_path)
    wire = load_binding().register(source, context)
    assert wire["schema"] == "topolab.v2.m2-strict-source-binding.read.v1"
    assert wire["attempts"] == list(PATHS)
    assert [row["path"] for row in wire["rows"]] == list(PATHS)
    assert wire["failures"] == []
    assert wire["helper_identity_relabelled"] is False
    for row in wire["rows"]:
        assert row["byte_size"] == 3
        assert row["declared"] == row["before"] == row["after"] == row["closing"]
        assert row.get("expected_sha256") is None


def test_both_readers_register_same_strict23_before_returning_semantic_bindings(tmp_path):
    source, context = public_source(tmp_path)
    primary = producer_wire(source, context)
    binding = load_binding()
    independent = binding.register(source, context, primary=primary)
    hashes = binding.validate_pair(primary, independent, context)
    assert list(hashes) == list(PATHS)
    assert all(row["byte_size"] == 3 for row in hashes.values())
    assert all(row["sha256"] == primary["rows"][0]["sha256"] for row in hashes.values())


def test_first_unbound_mtime_change_stops_with_full_original_observations(tmp_path, monkeypatch):
    source, context = public_source(tmp_path)
    primary = producer_wire(source, context)
    target = source / PATHS[0]
    before = target.stat()
    native_read = os.read
    mutated = False

    def changed_read(fd, maximum):
        nonlocal mutated
        raw = native_read(fd, maximum)
        if not mutated and os.fstat(fd).st_ino == before.st_ino:
            os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns - 63))
            mutated = True
        return raw

    monkeypatch.setattr(os, "read", changed_read)
    with pytest.raises(ValueError, match="changed during descriptor read") as stopped:
        load_binding().register(source, context, primary=primary)
    packet = stopped.value.strict_binding_failure
    assert packet["attempts"] == [PATHS[0]] and packet["rows"] == []
    fact = packet["source_failures"][0]
    assert fact["path"] == PATHS[0] and fact["returned_bytes"] == 3
    assert fact["declared"] == fact["before"]
    assert fact["after"]["st_mtime_ns"] == before.st_mtime_ns - 63
    assert fact["closing"] is None and fact["changed_fields"] == ["st_mtime_ns"]
    assert packet["primary_error"]["type"] == "ValueError"
    assert packet["pre_read_expected_sha256"] is None


@pytest.mark.parametrize("corruption", [
    "boolean_attempt", "author", "scope", "authority", "source_tree", "order",
    "missing_row", "duplicate_row", "missing_closing", "prebound", "relabelled", "failed",
    "wrong_helper",
])
def test_bad_primary_is_refused_before_independent_source_io(tmp_path, monkeypatch, corruption):
    source, context = public_source(tmp_path)
    primary = producer_wire(source, context)
    if corruption == "boolean_attempt":
        primary["attempt"] = True
    elif corruption == "author":
        primary["author"] = AUTHOR
    elif corruption == "scope":
        primary["scope"] = "FORMAL_STRICT_BINDING_REGISTRATION_ONLY"
    elif corruption == "authority":
        primary["authority_sha256"] = "3" * 64
    elif corruption == "source_tree":
        primary["source_tree"] = {}
    elif corruption == "order":
        primary["rows"][0], primary["rows"][1] = primary["rows"][1], primary["rows"][0]
    elif corruption == "missing_row":
        primary["rows"].pop()
    elif corruption == "duplicate_row":
        primary["rows"][-1] = deepcopy(primary["rows"][0])
    elif corruption == "missing_closing":
        primary["rows"][0]["closing"] = None
    elif corruption == "prebound":
        primary["pre_read_expected_sha256"] = primary["rows"][0]["sha256"]
    elif corruption == "relabelled":
        primary["helper_identity_relabelled"] = True
    elif corruption == "wrong_helper":
        primary["helper_execution_identity"] = "topolab.v2.p17-m2-source-stable-export.v1"
    else:
        primary["failures"] = [{"status": "STOP_NO_RETRY"}]

    def forbidden_read(*args):
        pytest.fail("invalid producer evidence reached independent content read")

    monkeypatch.setattr(os, "read", forbidden_read)
    with pytest.raises(ValueError) as stopped:
        load_binding().register(source, context, primary=primary)
    assert stopped.value.strict_binding_failure["attempts"] == []


@pytest.mark.parametrize("fault", [
    "short_read", "same_hash_inode", "missing_closing", "wrong_buffer",
])
def test_registration_rejects_actual_read_faults_without_a_binding(tmp_path, monkeypatch, fault):
    source, context = public_source(tmp_path)
    primary = producer_wire(source, context)
    target = source / PATHS[0]
    original_inode = target.stat().st_ino
    native_read = os.read
    changed = False

    def faulty_read(fd, maximum):
        nonlocal changed
        raw = native_read(fd, maximum)
        if changed or os.fstat(fd).st_ino != original_inode:
            return raw
        changed = True
        if fault == "short_read":
            return raw[:1]
        if fault == "same_hash_inode":
            replacement = source / "new-public-replacement"
            replacement.write_bytes(raw)
            replacement.replace(target)
        elif fault == "missing_closing":
            target.unlink()
        elif fault == "wrong_buffer":
            return b"[]\n"
        return raw

    monkeypatch.setattr(os, "read", faulty_read)
    with pytest.raises((ValueError, FileNotFoundError)) as stopped:
        load_binding().register(source, context, primary=primary)
    packet = stopped.value.strict_binding_failure
    assert packet["status"] == "STOP_NO_RETRY"
    if fault == "wrong_buffer":
        assert packet["attempts"] == list(PATHS) and packet["source_failures"] == []
    else:
        assert packet["attempts"] == [PATHS[0]] and packet["rows"] == []
        assert packet["source_failures"][0]["path"] == PATHS[0]


@pytest.mark.parametrize("change", ["mtime", "inode", "content"])
def test_separately_stable_reads_still_require_cross_author_identity(tmp_path, change):
    source, context = public_source(tmp_path)
    primary = producer_wire(source, context)
    target = source / PATHS[0]
    if change == "mtime":
        before = target.stat()
        os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns + 89))
    elif change == "inode":
        replacement = source / "new-public-replacement"
        replacement.write_bytes(b"{}\n")
        replacement.replace(target)
    else:
        target.write_bytes(b"[]\n")
    with pytest.raises(ValueError, match="independent content/physical") as stopped:
        load_binding().register(source, context, primary=primary)
    packet = stopped.value.strict_binding_failure
    assert packet["attempts"] == list(PATHS)
    assert len(packet["rows"]) == 23 and packet["source_failures"] == []


def test_cleanup_error_retains_original_identity_rejection_and_secondary_error(
    tmp_path, monkeypatch,
):
    source, context = public_source(tmp_path)
    primary = producer_wire(source, context)
    target = source / PATHS[0]
    before = target.stat()
    native_read, native_close = os.read, os.close
    changed = raised = False

    def changed_read(fd, maximum):
        nonlocal changed
        raw = native_read(fd, maximum)
        if not changed and os.fstat(fd).st_ino == before.st_ino:
            os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns + 1))
            changed = True
        return raw

    def failed_close(fd):
        nonlocal raised
        reject = changed and not raised and os.fstat(fd).st_ino == before.st_ino
        native_close(fd)
        if reject:
            raised = True
            raise OSError("public injected close failure")

    monkeypatch.setattr(os, "read", changed_read)
    monkeypatch.setattr(os, "close", failed_close)
    with pytest.raises(OSError, match="public injected close failure") as stopped:
        load_binding().register(source, context, primary=primary)
    packet = stopped.value.strict_binding_failure
    assert packet["primary_error"]["type"] == "ValueError"
    assert "changed during descriptor read" in packet["primary_error"]["reason"]
    assert packet["raised_error"]["type"] == "OSError"
    assert packet["secondary_errors"] == [
        {"type": "OSError", "reason": "public injected close failure"}]
    assert packet["source_failures"][0]["changed_fields"] == ["st_mtime_ns"]


@pytest.mark.parametrize("raw", [
    b"not json\n", b"{ }\n", b'{"x":1,"x":2}\n', b'{"x":NaN}\n',
])
def test_independent_rejects_noncanonical_or_malformed_captured_buffer(tmp_path, raw):
    source, context = public_source(tmp_path)
    (source / PATHS[0]).write_bytes(raw)
    primary = producer_wire(source, context)
    with pytest.raises(ValueError) as stopped:
        load_binding().register(source, context, primary=primary)
    packet = stopped.value.strict_binding_failure
    assert packet["attempts"] == [PATHS[0]]
    fact = packet["source_failures"][0]
    assert fact["stage"] in ("json_parse", "canonical_json")
    assert fact["returned_bytes"] == len(raw)
    assert fact["declared"] == fact["before"] == fact["after"] == fact["closing"]
