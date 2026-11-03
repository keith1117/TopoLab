"""Strict first registration never turns a changed read into its own expectation."""

import importlib.util
import json
import sys
from pathlib import Path

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
        capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    output = json.loads(result.stdout)
    plan = json.loads((root / "plan.json").read_bytes())
    return root, output, plan


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
        capture_output=True, text=True, check=False)
    assert result.returncode == 1
    failed = json.loads(result.stdout)
    assert failed["status"] == "STOP_NO_RETRY"
    assert failed["stage"] == "payload_launch"
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
