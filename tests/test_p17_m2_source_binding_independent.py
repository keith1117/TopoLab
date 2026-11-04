"""Independently authored strict registration on newly written public sources."""

import importlib.util
import os
import sys
import time
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

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


def coordination_config(tmp_path):
    # This is a semantic public fixture, not an actual helper/native certificate.
    return {
        "identity": "topolab.source-read.foundation-coordination.v1",
        "binary": str(tmp_path / "new-public-coordination-helper"),
        "sha256": "3" * 64,
        "request_timeout_seconds": 10,
        "release_timeout_seconds": 5,
        "reading_options": 0,
        "source_swift_sha256": "4" * 64,
        "compiler_sha256": "5" * 64,
    }


def coordinated_record(source, relative, config, ordinal):
    path = source / relative
    physical = path.stat(follow_symlinks=False)
    url = path.as_uri()
    start = 1000 + ordinal * 10
    pid = 2000 + ordinal
    return {
        "path": relative, "requested_url": url, "accessor_url": url,
        "namespace_before": {key: getattr(physical, key) for key in (
            "st_dev", "st_ino", "st_size", "st_mtime_ns")},
        "helper_pid": pid, "helper_sha256": config["sha256"],
        "strategy_identity": config["identity"],
        "ready": {"event": "accessor_entered", "pid": pid,
                  "requested_url": url, "accessor_url": url, "entered_ns": start},
        "reader_start_ns": start + 1, "reader_end_ns": start + 2,
        "release_requested_ns": start + 3,
        "release": {"event": "accessor_returned", "pid": pid, "left_ns": start + 4},
        "helper_exit_code": 0,
        "helper_native_exit": {
            "pid": pid, "exit_code": 0, "statistics_source": "os.wait4",
            "platform": "darwin", "rss_unit": "bytes",
            "native": {"rss_bytes": 1024, "user_seconds": 0.01, "system_seconds": 0.01},
            "wait_finished_ns": start + 5,
        },
    }


def coordinated_fixture(tmp_path):
    source, context = public_source(tmp_path)
    context["attempt"] = 2
    primary = producer_wire(source, context)
    config = coordination_config(tmp_path)
    primary["source_coordination"] = [
        coordinated_record(source, relative, config, ordinal)
        for ordinal, relative in enumerate(PATHS)
    ]
    return source, context, primary, config


def fake_coordinator_module(monkeypatch, binding, *, replacement=False, close_error=False,
                            namespace_replacement=False):
    state = SimpleNamespace(active=False, instances=[])

    class Coordinator:
        def __init__(self, config, source):
            self.config, self.source, self.records = config, source, []
            state.instances.append(self)

        @contextmanager
        def claim(self, relative):
            row = coordinated_record(self.source, relative, self.config, len(self.records))
            self.records.append(row)
            row["ready"]["entered_ns"] = time.time_ns()
            row["reader_start_ns"] = time.time_ns()
            if namespace_replacement and len(self.records) == 1:
                target = self.source / relative
                changed = self.source / "new-public-same-byte-inode"
                changed.write_bytes(target.read_bytes())
                changed.replace(target)
            state.active = True
            try:
                yield self.source / ("unregistered" if replacement else relative)
            finally:
                state.active = False
                row["reader_end_ns"] = time.time_ns()
                row["release_requested_ns"] = time.time_ns()
                row["release"]["left_ns"] = time.time_ns()
                row["helper_native_exit"]["wait_finished_ns"] = time.time_ns()
                if close_error:
                    row["helper_exit_code"] = 1
                    raise OSError("public coordinator release failure")

    monkeypatch.setattr(binding, "coordination_module", lambda: SimpleNamespace(
        Coordinator=Coordinator), raising=False)
    return state


def test_namespace_inode_replacement_stops_before_second_claim_or_content_read(
    tmp_path, monkeypatch,
):
    source, context, primary, config = coordinated_fixture(tmp_path)
    binding = load_binding()
    state = fake_coordinator_module(monkeypatch, binding, namespace_replacement=True)
    with pytest.raises(ValueError, match="namespace identity differs") as stopped:
        binding.register(source, context, primary, coordination=config)
    failure = stopped.value.strict_binding_failure
    assert failure["attempts"] == [PATHS[0]]
    assert len(failure["rows"]) == len(failure["source_coordination"]) == 1
    assert len(state.instances[0].records) == 1
    before = failure["source_coordination"][0]["namespace_before"]
    row = failure["rows"][0]
    assert before["st_ino"] != row["declared"]["st_ino"]
    assert row["sha256"] == primary["rows"][0]["sha256"]
    assert row["declared"] == row["before"] == row["after"] == row["closing"]


def test_overlapping_helpers_cannot_use_serial_maximum_rss_assumption(tmp_path):
    source, context, primary, config = coordinated_fixture(tmp_path)
    rows = primary["source_coordination"]
    rows[0]["helper_native_exit"]["wait_finished_ns"] = rows[1]["ready"]["entered_ns"] + 1
    independent = deepcopy(primary)
    independent.update(role="independent", author=AUTHOR,
                       helper_execution_identity="topolab.v2.p17-m2-source-stable-export.v1")
    with pytest.raises(ValueError, match="coordinated helpers overlap"):
        load_binding().validate_pair(primary, independent, context, coordination=config)


def test_attempt2_holds_all_strict_reads_and_closing_observations_inside_claim(
    tmp_path, monkeypatch,
):
    source, context, primary, config = coordinated_fixture(tmp_path)
    binding = load_binding()
    state = fake_coordinator_module(monkeypatch, binding)
    checker = binding.reader_module()
    original_packet = checker.OnceReader.packet

    def packet(reader, *args, **kwargs):
        assert state.active
        value = original_packet(reader, *args, **kwargs)
        assert state.active and reader.observations[-1]["closing"] is not None
        return value

    monkeypatch.setattr(checker.OnceReader, "packet", packet)
    monkeypatch.setattr(binding, "reader_module", lambda: checker)
    wire = binding.register(source, context, primary, coordination=config)
    assert wire["source_coordination"] == state.instances[0].records
    assert len(wire["source_coordination"]) == 23 and not state.active
    assert binding.validate_pair(primary, wire, context, coordination=config) == {
        row["path"]: {"sha256": row["sha256"], "byte_size": row["byte_size"]}
        for row in primary["rows"]
    }


@pytest.mark.parametrize("attempt,config_present", [(1, True), (2, False)])
def test_strategy_must_be_explicit_and_only_used_for_attempt2_before_io(
    tmp_path, monkeypatch, attempt, config_present,
):
    source, context = public_source(tmp_path)
    context["attempt"] = attempt
    binding = load_binding()
    monkeypatch.setattr(binding, "reader_module", lambda: pytest.fail("strategy reached reader"))
    with pytest.raises(ValueError) as stopped:
        binding.register(source, context, coordination=(
            coordination_config(tmp_path) if config_present else None))
    assert stopped.value.strict_binding_failure["attempts"] == []


@pytest.mark.parametrize("fault", [
    "missing", "order", "wrong_helper", "wrong_strategy", "wrong_url", "ready_url",
    "pid", "exit", "missing_release", "released_before_read", "bool_time",
    "namespace_inode", "namespace_size", "namespace_missing", "native_missing",
    "native_pid", "native_exit", "native_units", "native_rss", "native_wait", "native_cpu",
])
def test_bad_coordinated_producer_is_refused_before_independent_source_io(
    tmp_path, monkeypatch, fault,
):
    source, context, primary, config = coordinated_fixture(tmp_path)
    rows = primary["source_coordination"]
    row = rows[0]
    if fault == "missing":
        rows.pop()
    elif fault == "order":
        rows[0], rows[1] = rows[1], rows[0]
    elif fault == "wrong_helper":
        row["helper_sha256"] = "6" * 64
    elif fault == "wrong_strategy":
        row["strategy_identity"] = "unregistered"
    elif fault == "wrong_url":
        row["accessor_url"] += "/unregistered"
    elif fault == "ready_url":
        row["ready"]["requested_url"] += "/unregistered"
    elif fault == "pid":
        row["release"]["pid"] += 1
    elif fault == "exit":
        row["helper_exit_code"] = 1
    elif fault == "missing_release":
        row["release"] = None
    elif fault == "released_before_read":
        row["release"]["left_ns"] = row["reader_start_ns"] - 1
    elif fault == "bool_time":
        row["reader_start_ns"] = True
    elif fault == "namespace_inode":
        row["namespace_before"]["st_ino"] += 1
    elif fault == "namespace_size":
        row["namespace_before"]["st_size"] += 1
    elif fault == "native_missing":
        row.pop("helper_native_exit")
    elif fault == "native_pid":
        row["helper_native_exit"]["pid"] += 1
    elif fault == "native_exit":
        row["helper_native_exit"]["exit_code"] = 1
    elif fault == "native_units":
        row["helper_native_exit"]["rss_unit"] = "kilobytes"
    elif fault == "native_rss":
        row["helper_native_exit"]["native"]["rss_bytes"] = None
    elif fault == "native_wait":
        row["helper_native_exit"]["wait_finished_ns"] = row["release"]["left_ns"] - 1
    elif fault == "native_cpu":
        row["helper_native_exit"]["native"]["user_seconds"] = float("nan")
    else:
        row["namespace_before"].pop("st_mtime_ns")
    binding = load_binding()
    monkeypatch.setattr(binding, "reader_module", lambda: pytest.fail("bad trace reached reader"))
    with pytest.raises(ValueError) as stopped:
        binding.register(source, context, primary, coordination=config)
    assert stopped.value.strict_binding_failure["attempts"] == []


def test_accessor_path_change_refused_before_first_content_read(tmp_path, monkeypatch):
    source, context, primary, config = coordinated_fixture(tmp_path)
    binding = load_binding()
    state = fake_coordinator_module(monkeypatch, binding, replacement=True)
    checker = binding.reader_module()
    monkeypatch.setattr(checker.OnceReader, "packet", lambda *args: pytest.fail(
        "changed accessor reached source read"))
    monkeypatch.setattr(binding, "reader_module", lambda: checker)
    with pytest.raises(ValueError) as stopped:
        binding.register(source, context, primary, coordination=config)
    failure = stopped.value.strict_binding_failure
    assert failure["rows"] == [] and failure["source_facts"] == {}
    assert failure["source_coordination"] == state.instances[0].records


def test_coordination_cleanup_failure_retains_original_strict_stop(tmp_path, monkeypatch):
    source, context, primary, config = coordinated_fixture(tmp_path)
    binding = load_binding()
    state = fake_coordinator_module(monkeypatch, binding, close_error=True)
    target = source / PATHS[0]
    before = target.stat()
    native_read = os.read
    changed = False

    def changing_read(fd, maximum):
        nonlocal changed
        raw = native_read(fd, maximum)
        if not changed and os.fstat(fd).st_ino == before.st_ino:
            os.utime(target, ns=(before.st_atime_ns, before.st_mtime_ns - 108))
            changed = True
        return raw

    monkeypatch.setattr(os, "read", changing_read)
    with pytest.raises(OSError, match="public coordinator release failure") as stopped:
        binding.register(source, context, primary, coordination=config)
    failure = stopped.value.strict_binding_failure
    assert failure["primary_error"]["type"] == "ValueError"
    assert "changed during descriptor read" in failure["primary_error"]["reason"]
    assert failure["raised_error"]["type"] == "OSError"
    assert failure["source_failures"][0]["changed_fields"] == ["st_mtime_ns"]
    assert failure["source_coordination"] == state.instances[0].records


def test_namespace_mtime_before_claim_is_recorded_without_weakening_strict_points(
    tmp_path, monkeypatch,
):
    source, context, primary, config = coordinated_fixture(tmp_path)
    primary["source_coordination"][0]["namespace_before"]["st_mtime_ns"] -= 108
    binding = load_binding()
    fake_coordinator_module(monkeypatch, binding)
    wire = binding.register(source, context, primary, coordination=config)
    binding.validate_pair(primary, wire, context, coordination=config)
    assert wire["rows"][0]["declared"] == wire["rows"][0]["closing"]


WINDOW2_IDENTITY = "topolab.v2.p17-source-binding-window2.20261104.v1"


def test_window2_independent_strict_pair_uses_new_identity_without_relabeling_helper(
    tmp_path, monkeypatch,
):
    source, context, primary, config = coordinated_fixture(tmp_path)
    context["execution_identity"] = primary["execution_identity"] = WINDOW2_IDENTITY
    binding = load_binding()
    state = fake_coordinator_module(monkeypatch, binding)
    independent = binding.register(source, context, primary, coordination=config)
    assert independent["execution_identity"] == WINDOW2_IDENTITY
    assert independent["helper_execution_identity"] == (
        "topolab.v2.p17-m2-source-stable-export.v1")
    assert independent["helper_identity_relabelled"] is False
    assert len(state.instances[0].records) == len(independent["rows"]) == 23
    assert binding.validate_pair(primary, independent, context, coordination=config)
    assert all(row["declared"] == row["before"] == row["after"] == row["closing"]
               for row in independent["rows"])


@pytest.mark.parametrize("identity,attempt", [
    ("topolab.v2.p17-source-binding-window2.20261104.v1", 1),
    ("topolab.v2.p17-source-binding-window2.20261104.v1-unknown", 2),
])
def test_window2_invalid_profile_stops_before_source_with_complete_context(
    tmp_path, monkeypatch, identity, attempt,
):
    source, context = public_source(tmp_path)
    context.update(execution_identity=identity, attempt=attempt)
    binding = load_binding()
    monkeypatch.setattr(binding, "reader_module", lambda: pytest.fail("source reader reached"))
    with pytest.raises(ValueError) as stopped:
        binding.register(source, context, coordination=coordination_config(tmp_path))
    packet = stopped.value.strict_binding_failure
    assert packet["context"] == context and packet["stage"] == "context_validation"
    assert packet["attempts"] == packet["rows"] == []


@pytest.mark.parametrize("new_context", [True, False])
def test_window2_and_historical_wires_cannot_be_cross_labeled_before_io(
    tmp_path, monkeypatch, new_context,
):
    source, context, primary, config = coordinated_fixture(tmp_path)
    if new_context:
        context["execution_identity"] = WINDOW2_IDENTITY
    else:
        primary["execution_identity"] = WINDOW2_IDENTITY
    binding = load_binding()
    monkeypatch.setattr(binding, "reader_module", lambda: pytest.fail("source reader reached"))
    with pytest.raises(ValueError) as stopped:
        binding.register(source, context, primary, coordination=config)
    assert stopped.value.strict_binding_failure["attempts"] == []
