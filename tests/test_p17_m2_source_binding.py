"""Strict first registration never turns a changed read into its own expectation."""

import importlib.util
import json
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).parents[1]


def binding_module():
    spec = importlib.util.spec_from_file_location(
        "binding_producer_test", REPO / "scripts/p17_m2_source_binding.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def public_context(module, source):
    return {
        "execution_identity": module.IDENTITY,
        "scope": module.PUBLIC_SCOPE,
        "attempt": 1,
        "source_root": str(source),
        "authority_sha256": module.sha(module.AUTHORITY.read_bytes()),
        "source_tree": module.source_freeze(),
        "actors": {"producer": "/root", "independent": "/root/binding_route_independent_v1"},
    }


def small_sources(module, tmp_path):
    source = tmp_path / "topolab-public-strict-binding-source"
    for i, row in enumerate(module.whitelist()):
        path = source / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(module.canonical({"new_public_fixture": i}))
    return source


def coordinated_authority(module, tmp_path, monkeypatch):
    authority = json.loads(module.AUTHORITY.read_bytes())
    authority["coordination"] = {
        "identity": "topolab.source-read.foundation-coordination.v1",
        "binary": str(tmp_path / "new-public-coordination-helper"), "sha256": "3" * 64,
        "request_timeout_seconds": 10, "release_timeout_seconds": 5, "reading_options": 0,
        "source_swift_sha256": "4" * 64, "compiler_sha256": "5" * 64,
    }
    authority["evidence_root"] = str(tmp_path)
    authority["preparation_proofs"]["public_native_root"] = str(
        tmp_path / "topolab-public-coordinated-binding-plan")
    path = tmp_path / "new-public-coordinated-authority.json"
    path.write_bytes(module.canonical(authority))
    monkeypatch.setattr(module, "COORDINATED_AUTHORITY", path, raising=False)
    return authority


def test_attempt2_public_prepare_selects_new_authority_and_frozen_coordinator(
    tmp_path, monkeypatch,
):
    module = binding_module()
    authority = coordinated_authority(module, tmp_path, monkeypatch)
    active = module.runtime()
    monkeypatch.setattr(module, "runtime", lambda: dict(
        active, isolated=1, cwd=str(module.REPO), threads=module.THREADS))
    root = tmp_path / "topolab-public-coordinated-binding-plan"
    result = module.prepare_public(root, attempt=2)
    plan = module.load_plan(root / "plan.json", result["plan_sha256"])
    assert plan["context"]["attempt"] == 2
    assert plan["context"]["authority_sha256"] == module.sha(
        module.COORDINATED_AUTHORITY.read_bytes())
    assert plan["coordination"] == authority["coordination"]
    assert len(plan["context"]["source_tree"]) == 18
    assert set(module.source_freeze()) < set(module.source_freeze(2))
    assert "coordination" not in plan["context"]
    assert (root / "custody.cooperative-reader.lease").exists()
    module.admit_plan(plan, "producer-availability")


def public_coordinator_fixture(module, monkeypatch):
    state = SimpleNamespace(active=False, records=[])

    class Coordinator:
        def __init__(self, config, source):
            self.config, self.source, self.records = config, source, []

        @contextmanager
        def claim(self, relative):
            path = self.source / relative
            info = path.stat(follow_symlinks=False)
            url = path.as_uri()
            pid = 2000 + len(self.records)
            entered = time.time_ns()
            row = {"path": relative, "requested_url": url, "accessor_url": url,
                   "namespace_before": module.physical(info), "helper_pid": pid,
                   "helper_sha256": self.config["sha256"],
                   "strategy_identity": self.config["identity"],
                   "ready": {"event": "accessor_entered", "pid": pid,
                             "requested_url": url, "accessor_url": url, "entered_ns": entered},
                   "reader_start_ns": time.time_ns()}
            self.records.append(row)
            state.records.append(row)
            state.active = True
            try:
                yield path
            finally:
                state.active = False
                row.update(reader_end_ns=time.time_ns(), release_requested_ns=time.time_ns())
                row["release"] = {"event": "accessor_returned", "pid": pid,
                                  "left_ns": time.time_ns()}
                row["helper_exit_code"] = 0
                row["helper_native_exit"] = {
                    "pid": pid, "exit_code": 0, "statistics_source": "os.wait4",
                    "platform": "darwin", "rss_unit": "bytes",
                    "native": {"rss_bytes": 1024, "user_seconds": 0.01,
                               "system_seconds": 0.01}, "wait_finished_ns": time.time_ns()}

    original = module.load
    monkeypatch.setattr(module, "load", lambda name: SimpleNamespace(Coordinator=Coordinator)
                        if name == "p17_m2_source_coordination" else original(name))
    return state, Coordinator


def test_attempt2_producer_and_independent_keep_strict_packets_inside_claim(tmp_path, monkeypatch):
    module = binding_module()
    authority = coordinated_authority(module, tmp_path, monkeypatch)
    source = small_sources(module, tmp_path).rename(
        tmp_path / "topolab-public-coordinated-binding-source")
    context = dict(public_context(module, source), attempt=2,
                   authority_sha256=module.sha(module.COORDINATED_AUTHORITY.read_bytes()),
                   source_tree=module.source_freeze(2))
    state, Coordinator = public_coordinator_fixture(module, monkeypatch)
    producer = module.load("p17_m2_input_export")
    original = producer.Reader.packet

    def packet(reader, *args, **kwargs):
        assert state.active
        value = original(reader, *args, **kwargs)
        assert state.active and reader.source_observations[-1]["closing"] is not None
        return value

    monkeypatch.setattr(producer.Reader, "packet", packet)
    primary = module.register(source, context, coordination=authority["coordination"])
    checker = module.load("p17_m2_source_binding_independent")
    monkeypatch.setattr(checker, "coordination_module", lambda: SimpleNamespace(
        Coordinator=Coordinator))
    independent = checker.register(source, context, primary, coordination=authority["coordination"])
    bindings = checker.validate_pair(primary, independent, context,
                                     coordination=authority["coordination"])
    assert len(bindings) == 23 and len(primary["source_coordination"]) == 23
    assert primary["pre_read_expected_sha256"] is None
    assert all(row["declared"] == row["closing"] for row in primary["rows"])


def test_coordinated_remedy_cannot_restart_absolute_result_stage(tmp_path, monkeypatch):
    module = binding_module()
    deadline = 1793759678449
    authority = {"reallocation_v4": {"path": str(tmp_path / "v4.json"), "sha256": "3" * 64},
                 "binding_result_deadline_ms": deadline}
    allocation = {
        "binding_result": {"deadline_ms": deadline, "cap_each_unchanged": 12240},
        "formal1": {"status": "CLOSED_STOP_NO_RETRY_HELD",
                    "failed_buffers_establish_trust": False},
        "formal2_unstarted": {"max": 1, "core_FULL": 1080, "metadata_auditor_FULL": 120},
        "all_old_balances_reopened": False,
    }
    monkeypatch.setattr(module, "read_metadata", lambda *args, **kwargs: (
        allocation, module.canonical(allocation)))
    monkeypatch.setattr(module.time, "time_ns", lambda: (deadline - 1000) * 10**6)
    with pytest.raises(ValueError, match="absolute result suffix"):
        module.coordinated_remedy_readiness(authority, deadline - 3899 * 1000)


def test_coordinated_public_family_rejects_unregistered_root_before_creation(tmp_path, monkeypatch):
    module = binding_module()
    coordinated_authority(module, tmp_path, monkeypatch)
    root = tmp_path / "topolab-public-coordinated-binding-unregistered"
    with pytest.raises(ValueError, match="registered coordinated public graph"):
        module.prepare_public(root, attempt=2)
    assert not root.exists() and not root.with_name(root.name + "-source").exists()


def test_producer_registers_exact23_stable_first_reads(tmp_path):
    module = binding_module()
    source = small_sources(module, tmp_path)
    wire = module.register(source, public_context(module, source))
    assert wire["attempts"] == [row["path"] for row in module.whitelist()]
    assert len(wire["rows"]) == 23
    assert wire["source_identity_policy"] is None
    assert wire["pre_read_expected_sha256"] is None
    assert wire["helper_identity_relabelled"] is False
    assert wire["failures"] == []
    for row in wire["rows"]:
        assert row["declared"] == row["before"] == row["after"] == row["closing"]
        assert row["byte_size"] == row["before"]["st_size"]


def test_availability_does_not_hash_or_read_source_content(tmp_path, monkeypatch):
    module = binding_module()
    source = small_sources(module, tmp_path)

    def no_content(*args, **kwargs):
        raise AssertionError("availability attempted a content read")

    monkeypatch.setattr(module.os, "read", no_content)
    monkeypatch.setattr(module.os, "fdopen", no_content)
    result = module.availability(source, public_context(module, source))
    assert result["content_read_bytes"] == 0
    assert len(result["rows"]) == 23
    assert all(row["hash"] is None for row in result["rows"])


def test_first_read_mtime_change_preserves_stop_and_original_context(tmp_path, monkeypatch):
    module = binding_module()
    source = small_sources(module, tmp_path)
    producer = module.load("p17_m2_input_export")
    original = producer.os.fdopen

    def changed(fd, *args, **kwargs):
        info = module.os.fstat(fd)
        module.os.utime(fd, ns=(info.st_atime_ns, info.st_mtime_ns + 89))
        return original(fd, *args, **kwargs)

    monkeypatch.setattr(producer.os, "fdopen", changed)
    with pytest.raises(ValueError, match="source changed") as stopped:
        module.register(source, public_context(module, source))
    packet = stopped.value.binding_failure
    assert packet["attempts"] == [module.whitelist()[0]["path"]]
    assert packet["rows"] == []
    fact = packet["failures"][0]
    assert fact["path"] == module.whitelist()[0]["path"]
    assert fact["after"]["st_mtime_ns"] - fact["before"]["st_mtime_ns"] == 89
    assert fact["closing"] is None
    assert packet["pre_read_expected_sha256"] is None


def test_unknown_cli_mode_refuses_before_any_source_io(tmp_path):
    import subprocess

    result = subprocess.run(
        [sys.executable, "-I", str(REPO / "scripts/p17_m2_source_binding.py"),
         "unregistered", "--source", str(tmp_path / "unopened")],
        capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert not (tmp_path / "unopened").exists()
    assert "STRICT_BINDING" in result.stderr


def test_binding_authority_retains_finite_exact_source_scope():
    protocol = json.loads(
        (REPO / "docs/planning/p17_m2_strict_source_binding_protocol.json").read_bytes())
    assert len(protocol["source_whitelist"]) == 23
    assert protocol["attempts"]["FULL_all_attempts"] == 2160
    assert protocol["attempts"]["original_content_reads_max_all_attempts"] == 92
    assert protocol["registration_rule"]["pre_read_expected_sha256"] is None
    assert protocol["custody"]["permanent_0555_required"] is False


def test_availability_records_first_open_mtime_change_then_strictly_registers(
    tmp_path, monkeypatch
):
    module = binding_module()
    source = small_sources(module, tmp_path)
    context = public_context(module, source)
    original, changed = module.os.open, []
    first_name = Path(module.whitelist()[0]["path"]).name

    def metadata_change(path, flags, *args, **kwargs):
        fd = original(path, flags, *args, **kwargs)
        if path == first_name and not changed:
            info = module.os.fstat(fd)
            module.os.utime(fd, ns=(info.st_atime_ns, info.st_mtime_ns + 89))
            changed.append(True)
        return fd

    monkeypatch.setattr(module.os, "open", metadata_change)
    available = module.availability(source, context)
    assert available["rows"][0]["mtime_differences_ns"] == [0] + [89] * 7
    assert all(row["hash"] is None for row in available["rows"])
    registered = module.register(source, context)
    first = registered["rows"][0]
    assert first["declared"] == first["before"] == first["after"] == first["closing"]
    assert registered["pre_read_expected_sha256"] is None


def test_actual_two_authors_agree_without_persistent_directory_0555(tmp_path):
    module = binding_module()
    source = small_sources(module, tmp_path)
    context = public_context(module, source)
    primary = module.register(source, context)
    source.chmod(0o555)
    source.chmod(0o700)
    checker = module.load("p17_m2_source_binding_independent")
    independent = checker.register(source, context, primary)
    binding = checker.validate_pair(primary, independent, context)
    assert len(binding) == 23
    assert all(binding[row["path"]] == {"byte_size": row["byte_size"], "sha256": row["sha256"]}
               for row in primary["rows"])


def test_producer_failure_retains_primary_when_descriptor_cleanup_also_fails(
    tmp_path, monkeypatch
):
    module = binding_module()
    source = small_sources(module, tmp_path)
    context = public_context(module, source)
    producer = module.load("p17_m2_input_export")
    original_open, original_close, original_fdopen = (
        producer.os.open, producer.os.close, producer.os.fdopen)
    leaf_fds = set()

    def open_leaf(path, flags, *args, **kwargs):
        fd = original_open(path, flags, *args, **kwargs)
        if path == Path(module.whitelist()[0]["path"]).name:
            leaf_fds.add(fd)
        return fd

    def changed(fd, *args, **kwargs):
        info = producer.os.fstat(fd)
        producer.os.utime(fd, ns=(info.st_atime_ns, info.st_mtime_ns + 63))
        return original_fdopen(fd, *args, **kwargs)

    def cleanup_error(fd):
        original_close(fd)
        if fd in leaf_fds:
            leaf_fds.remove(fd)
            raise OSError("secondary close failure")

    monkeypatch.setattr(producer.os, "open", open_leaf)
    monkeypatch.setattr(producer.os, "fdopen", changed)
    monkeypatch.setattr(producer.os, "close", cleanup_error)
    with pytest.raises(OSError, match="secondary close failure") as stopped:
        module.register(source, context)
    packet = stopped.value.binding_failure
    assert packet["primary_error"]["type"] == "ValueError"
    assert "source changed" in packet["primary_error"]["reason"]
    assert packet["raised_error"]["type"] == "OSError"
    assert packet["secondary_errors"] == [packet["raised_error"]]
    assert packet["source_facts"][module.whitelist()[0]["path"]]["returned_bytes"] > 0


def test_availability_stops_at_first_changed_physical_observation(tmp_path, monkeypatch):
    from types import SimpleNamespace

    module = binding_module()
    source = small_sources(module, tmp_path)
    context = public_context(module, source)
    original = module.os.fstat

    def changed(fd):
        info = original(fd)
        return SimpleNamespace(st_dev=info.st_dev + 1, st_ino=info.st_ino,
                               st_size=info.st_size, st_mtime_ns=info.st_mtime_ns)

    monkeypatch.setattr(module.os, "fstat", changed)
    with pytest.raises(ValueError, match="physical identity changed") as stopped:
        module.availability(source, context)
    assert len(stopped.value.binding_failure["rows"]) == 1
    assert len(stopped.value.binding_failure["rows"][0]["observations"]) == 2


@pytest.fixture(scope="module")
def actual_public_plan(tmp_path_factory):
    import subprocess

    root = tmp_path_factory.mktemp("binding-cli") / "topolab-public-strict-binding-cli"
    result = subprocess.run(
        [sys.executable, "-I", str(REPO / "scripts/p17_m2_source_binding.py"),
         "prepare-public", "--root", str(root)],
        capture_output=True, text=True, check=False,
        env={**os.environ, **binding_module().THREADS})
    assert result.returncode == 0, (result.stdout, result.stderr)
    output = json.loads(result.stdout)
    plan = json.loads((root / "plan.json").read_bytes())
    return root, output, plan


@pytest.mark.parametrize("inherited", [None, "7"])
def test_public_plan_fixture_sets_locked_threads_without_inherited_environment(
        tmp_path_factory, monkeypatch, inherited):
    for name in binding_module().THREADS:
        if inherited is None:
            monkeypatch.delenv(name, raising=False)
        else:
            monkeypatch.setenv(name, inherited)
    _, _, plan = actual_public_plan.__wrapped__(tmp_path_factory)
    assert plan["runtime"]["threads"] == binding_module().THREADS


def test_real_public_prepare_freezes_plan_and_actual_cooperative_lease(actual_public_plan):
    root, output, plan = actual_public_plan
    assert output["plan_sha256"] == __import__("hashlib").sha256(
        (root / "plan.json").read_bytes()).hexdigest()
    assert plan["context"]["scope"] == "PUBLIC_STRICT_BINDING_REGISTRATION_ONLY"
    assert plan["actor_window_seconds"] == 3600
    assert sum(value["FULL"] for value in plan["roles"].values()) == 1080
    assert (root / "custody.cooperative-reader.lease").is_file()
    assert (root.stat().st_mode & 0o777) == 0o700
    assert ((root / "custody.cooperative-reader.lease").stat().st_mode & 0o777) == 0o600


def test_real_payload_refuses_missing_native_launch_before_source_observations(actual_public_plan):
    import subprocess

    root, output, _ = actual_public_plan
    result = subprocess.run(
        [sys.executable, "-I", str(REPO / "scripts/p17_m2_source_binding.py"), "payload",
         "--plan", str(root / "plan.json"), "--plan-sha", output["plan_sha256"],
         "--role", "producer-availability"],
        capture_output=True, text=True, check=False,
        env={**os.environ, **binding_module().THREADS})
    assert result.returncode == 1
    failed = json.loads(result.stdout)
    assert failed["status"] == "STOP_NO_RETRY"
    assert failed["stage"] == "payload_launch"
    assert "active.json" in failed["primary_error"]["reason"]
    assert failed["source_attempts"] == []
    assert not (root / "producer-availability-output.json").exists()


@pytest.mark.parametrize("path", [
    "/Users/keith1117/Documents/TopoLab-data/b3-v1-fits/b3_training.json",
    "/Users/keith1117/Documents/TopoLab-data/p17-m2-source-acquisition-v1-results/publication-closure.json",
    "/Users/keith1117/Library/Application Support/TopoLab-custody/"
    "old-failed/certificate-bundle.json",
])
def test_metadata_reader_rejects_old_namespace_before_constructing_reader(path, monkeypatch):
    module = binding_module()

    def forbidden_reader(*args):
        raise AssertionError("metadata entry reached a reader for old evidence/source")

    monkeypatch.setattr(module, "load", forbidden_reader)
    with pytest.raises(ValueError, match="original or historical namespace"):
        module.read_metadata(Path(path), 1024)


@pytest.mark.parametrize("kind", ["empty", "oversize", "directory"])
def test_availability_retains_declared_tuple_when_stat_succeeds_but_size_rejects(tmp_path, kind):
    module = binding_module()
    source = small_sources(module, tmp_path)
    context = public_context(module, source)
    path = source / module.whitelist()[0]["path"]
    if kind == "directory":
        path.unlink()
        path.mkdir()
    else:
        with path.open("wb") as stream:
            stream.truncate(0 if kind == "empty" else module.whitelist()[0]["max_bytes"] + 1)
    actual = module.physical(path.stat())
    with pytest.raises(ValueError, match="file type/size") as stopped:
        module.availability(source, context)
    first = stopped.value.binding_failure["rows"][0]
    assert first["observations"] == [{"point": "declared", **actual}]
    assert first["hash"] is None


def test_registration_interruption_retains_completed_first_buffer_context(tmp_path, monkeypatch):
    module = binding_module()
    source = small_sources(module, tmp_path)
    context = public_context(module, source)
    producer = module.load("p17_m2_input_export")

    def interrupted_parse(raw):
        raise KeyboardInterrupt("new public parser interruption")

    monkeypatch.setattr(producer, "parse", interrupted_parse)
    with pytest.raises(KeyboardInterrupt) as stopped:
        module.register(source, context)
    failure = stopped.value.binding_failure
    assert failure["attempts"] == [module.whitelist()[0]["path"]]
    assert len(failure["rows"]) == 1
    fact = failure["source_facts"][module.whitelist()[0]["path"]]
    assert fact["returned_bytes"] > 0 and fact["closing"] is not None
    assert failure["primary_error"]["type"] == "KeyboardInterrupt"


def test_availability_interruption_retains_declared_and_opened_context(tmp_path, monkeypatch):
    module = binding_module()
    source = small_sources(module, tmp_path)
    context = public_context(module, source)

    def interrupted_wait(seconds):
        raise KeyboardInterrupt("new public availability interruption")

    monkeypatch.setattr(module.time, "sleep", interrupted_wait)
    with pytest.raises(KeyboardInterrupt) as stopped:
        module.availability(source, context)
    failure = stopped.value.binding_failure
    assert failure["content_read_bytes"] == 0
    assert [row["point"] for row in failure["rows"][0]["observations"]] == ["declared", "opened"]
    assert failure["primary_error"]["type"] == "KeyboardInterrupt"


def test_coordinated_producer_stops_after_first_replaced_namespace(tmp_path, monkeypatch):
    from contextlib import contextmanager

    module = binding_module()
    authority = coordinated_authority(module, tmp_path, monkeypatch)
    source = small_sources(module, tmp_path).rename(
        tmp_path / 'topolab-public-coordinated-binding-source')
    context = dict(public_context(module, source), attempt=2,
                   authority_sha256=module.sha(module.authority_path(2).read_bytes()),
                   source_tree=module.source_freeze(2))
    _, coordinator_class = public_coordinator_fixture(module, monkeypatch)
    original = coordinator_class.claim
    replaced = []

    @contextmanager
    def replacement(self, relative):
        with original(self, relative) as path:
            if not replaced:
                target = path.with_name('new-public-replacement.json')
                target.write_bytes(path.read_bytes())
                target.replace(path)
                replaced.append(True)
            yield path

    monkeypatch.setattr(coordinator_class, 'claim', replacement)
    with pytest.raises(ValueError, match='namespace identity differs') as stopped:
        module.register(source, context, coordination=authority['coordination'])
    packet = stopped.value.binding_failure
    assert packet['attempts'] == [module.whitelist()[0]['path']]
    assert len(packet['rows']) == len(packet['source_coordination']) == 1
    assert packet['source_coordination'][0]['namespace_before']['st_ino'] != (
        packet['rows'][0]['declared']['st_ino'])


def test_formal_metadata_auditor_cannot_start_a_new_window_after_result_deadline(
    tmp_path, monkeypatch
):
    module = binding_module()
    authority = json.loads(module.COORDINATED_AUTHORITY.read_bytes())
    core_root = tmp_path / 'topolab-public-coordinated-binding-window'
    core_root.mkdir()
    context = dict(public_context(module, core_root), attempt=2, scope=module.FORMAL_SCOPE)
    core = {'root': str(core_root), 'context': context,
            'coordination': authority['coordination'],
            'deadline_unix_ns': authority['binding_result_deadline_ms'] * 10**6}
    bundle = {'plan': core}
    monkeypatch.setattr(module, 'read_metadata', lambda *args, **kwargs: (bundle, b''))
    monkeypatch.setattr(module, 'replay_bundle', lambda value: None)
    monkeypatch.setattr(module.time, 'time_ns', lambda:
                        authority['binding_result_deadline_ms'] * 10**6 + 1)
    with pytest.raises(ValueError, match='metadata audit suffix'):
        module.prepare_metadata_audit(core_root / 'certificate-bundle.json', '3' * 64)
    assert not Path(str(core_root) + '-certificate-audit').exists()
