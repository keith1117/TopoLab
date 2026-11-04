"""Public process/claim boundaries; these fixtures grant no original-source IO."""

import hashlib
import importlib.util
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def subject():
    spec = importlib.util.spec_from_file_location(
        "public_source_coordination", REPO / "scripts/p17_m2_source_coordination.py")
    assert spec and spec.loader
    result = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = result
    spec.loader.exec_module(result)
    return result


def fixture(tmp_path, mode="normal"):
    source = tmp_path / "public-source"
    source.mkdir()
    (source / "unit.json").write_bytes(b'{"public":true}\n')
    helper = tmp_path / ("public-helper-" + mode)
    helper.write_text("#!" + sys.executable + "\n" +
        "import json,os,sys,time\nfrom pathlib import Path\n"
        f"mode={mode!r}\n"
        "path=Path(sys.argv[1]).as_uri()\n"
        "if mode=='timeout':time.sleep(2)\n"
        "if mode=='delayed_start':time.sleep(1.1)\n"
        "if mode=='request_error':sys.exit(3)\n"
        "actual=path+'-changed' if mode=='url' else path\n"
        "print(json.dumps(dict(event='accessor_entered',pid=os.getpid(),"
        "requested_url=path,accessor_url=actual,entered_ns=time.time_ns())),flush=True)\n"
        "if mode=='early_exit':sys.exit(0)\n"
        "line=sys.stdin.readline()\n"
        "if mode=='release_error':sys.exit(4)\n"
        "assert line=='DONE\\n'\n"
        "print(json.dumps(dict(event='accessor_returned',pid=os.getpid(),"
        "left_ns=time.time_ns())),flush=True)\n")
    helper.chmod(0o700)
    config = dict(identity="topolab.source-read.foundation-coordination.v1",
                  binary=str(helper), sha256=hashlib.sha256(helper.read_bytes()).hexdigest(),
                  request_timeout_seconds=0.25 if mode == "timeout" else 10,
                  release_timeout_seconds=5,
                  reading_options=0, source_swift_sha256="a" * 64,
                  compiler_sha256="b" * 64)
    return source, config


def test_claim_holds_owned_child_until_public_read_and_release(tmp_path):
    module = subject()
    source, config = fixture(tmp_path)
    reader = module.Coordinator(config, source)
    with reader.claim("unit.json") as accessor:
        assert accessor == source / "unit.json"
        assert accessor.read_bytes() == b'{"public":true}\n'
        assert reader.records[-1]["release_requested_ns"] is None
    row = reader.records[0]
    assert row["helper_exit_code"] == 0
    assert row["ready"]["entered_ns"] <= row["reader_start_ns"] <= row["reader_end_ns"]
    assert row["reader_end_ns"] <= row["release_requested_ns"] <= row["release"]["left_ns"]
    assert row["namespace_before"]["st_size"] == 16


def test_successful_public_helper_startup_uses_full_registered_window(tmp_path):
    module = subject()
    source, config = fixture(tmp_path, "delayed_start")
    reader = module.Coordinator(config, source)
    with reader.claim("unit.json") as accessor:
        assert accessor.read_bytes() == b'{"public":true}\n'
    row = reader.records[0]
    assert row["helper_exit_code"] == 0
    assert row["ready"]["entered_ns"] <= row["reader_start_ns"] <= row["reader_end_ns"]
    assert row["reader_end_ns"] <= row["release_requested_ns"] <= row["release"]["left_ns"]


@pytest.mark.parametrize("mode", ["url", "request_error", "timeout", "early_exit"])
def test_bad_or_missing_live_claim_refuses_public_read(tmp_path, mode):
    module = subject()
    source, config = fixture(tmp_path, mode)
    reader = module.Coordinator(config, source)
    entered = False
    with pytest.raises((ValueError, OSError)):
        with reader.claim("unit.json"):
            entered = True
            time.sleep(0.05)
    assert not entered or mode == "early_exit"
    assert reader.records[0]["failure"]
    assert reader.records[0]["helper_exit_code"] is not None


def test_reader_primary_survives_helper_release_failure(tmp_path):
    module = subject()
    source, config = fixture(tmp_path, "release_error")
    reader = module.Coordinator(config, source)
    original = ValueError("PUBLIC_READER_PRIMARY")
    with pytest.raises(ValueError, match="PUBLIC_READER_PRIMARY") as stopped:
        with reader.claim("unit.json"):
            raise original
    assert stopped.value is original
    assert original.source_coordination_failure["secondary_errors"]
    assert reader.records[0]["helper_exit_code"] == 4


def test_helper_hash_and_symlink_refuse_before_child(tmp_path, monkeypatch):
    module = subject()
    source, config = fixture(tmp_path)
    config["sha256"] = "0" * 64

    def forbidden(*args, **kwargs):
        raise AssertionError("unbound helper spawned")

    monkeypatch.setattr(module.subprocess, "Popen", forbidden)
    with pytest.raises(ValueError):
        with module.Coordinator(config, source).claim("unit.json"):
            pytest.fail("bad helper entered")
    link = source / "link.json"
    link.symlink_to(source / "unit.json")
    config["sha256"] = hashlib.sha256(Path(config["binary"]).read_bytes()).hexdigest()
    with pytest.raises(OSError):
        with module.Coordinator(config, source).claim("link.json"):
            pytest.fail("symlink entered")


@pytest.mark.parametrize("relative", ["../unit.json", "/unit.json", "a/../unit.json"])
def test_nonliteral_source_refused_before_namespace_access(tmp_path, monkeypatch, relative):
    module = subject()
    source, config = fixture(tmp_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("invalid source touched filesystem")

    monkeypatch.setattr(module.os, "open", forbidden)
    with pytest.raises(ValueError):
        with module.Coordinator(config, source).claim(relative):
            pytest.fail("invalid path entered")


@pytest.fixture(scope="module")
def foundation_runtime(tmp_path_factory):
    import shutil
    import subprocess

    if sys.platform != 'darwin' or not shutil.which('swiftc'):
        pytest.skip('Foundation NSFileCoordinator requires macOS and Swift')
    root = tmp_path_factory.mktemp('public-foundation-coordination')
    binaries = []
    for source in ('native/p17_m2_source_coordinator.swift',
                   'tests/fixtures/p17_source_coordinated_writer.swift'):
        target = root / Path(source).stem
        result = subprocess.run([
            shutil.which('swiftc'), '-O', '-target', 'arm64-apple-macosx13.0',
            '-sdk', '/Library/Developer/CommandLineTools/SDKs/MacOSX.sdk',
            '-module-cache-path', str(root / 'module-cache'), str(REPO / source),
            '-o', str(target)], capture_output=True, timeout=120)
        assert result.returncode == 0, result.stderr.decode()
        target.chmod(0o700)
        binaries.append(target)
    return binaries


def test_foundation_waits_for_coordinated_writer_and_holds_reader_claim(
    tmp_path, foundation_runtime
):
    import json
    import os
    import select
    import subprocess
    import tempfile
    import threading

    # Foundation standardizes /private/var to /var at accessor entry. Production
    # rejects such changed URLs; this success case uses a separately supplied
    # new public parent with an exact URL, like the frozen public graph.
    parent = os.environ.get('TOPOLAB_COORDINATION_PUBLIC_PARENT')
    if parent is None:
        pytest.skip('exact-URL Foundation integration needs a new public parent')
    public = tempfile.TemporaryDirectory(prefix='topolab-public-coordination-', dir=parent)
    tmp_path = Path(public.name)
    module = subject()
    source, config = fixture(tmp_path)
    config.update(binary=str(foundation_runtime[0]),
                  sha256=hashlib.sha256(foundation_runtime[0].read_bytes()).hexdigest(),
                  request_timeout_seconds=10, release_timeout_seconds=5)
    path = source / 'unit.json'
    writer = waiting = thread = None
    try:
        writer = subprocess.Popen([str(foundation_runtime[1]), str(path)], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        assert select.select([writer.stdout], [], [], 10)[0]
        assert writer.stdout.readline() == b'WRITER_ENTERED\n'
        writer_return = []

        def release_writer():
            time.sleep(.15)
            try:
                output, error = writer.communicate(b'DONE\n', timeout=10)
                writer_return.append((writer.returncode, output, error, time.time_ns()))
            except (OSError, ValueError, subprocess.TimeoutExpired) as error:
                writer_return.append(('FAIL', str(error)))

        thread = threading.Thread(target=release_writer)
        thread.start()
        coordinator = module.Coordinator(config, source)
        before = time.monotonic()
        with coordinator.claim('unit.json'):
            assert time.monotonic() - before >= .1
            assert path.read_bytes() == b'{"public":true}\n'
            # A second cooperating writer cannot enter while the reader claim lives.
            waiting = subprocess.Popen([str(foundation_runtime[1]), str(path)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            assert not select.select([waiting.stdout], [], [], .15)[0]
        assert select.select([waiting.stdout], [], [], 10)[0]
        assert waiting.stdout.readline() == b'WRITER_ENTERED\n'
        output, error = waiting.communicate(b'DONE\n', timeout=10)
        assert waiting.returncode == 0 and output == b'WRITER_RETURNED\n' and not error
        thread.join(timeout=10)
        assert not thread.is_alive() and writer_return[0][:3] == (0, b'WRITER_RETURNED\n', b'')
        record = coordinator.records[0]
        assert record['helper_native_exit']['native']['rss_bytes'] > 0
        assert record['helper_native_exit']['exit_code'] == 0
        assert record['helper_native_exit']['wait_finished_ns'] >= record['release']['left_ns']
        assert json.loads(json.dumps(record)) == record
    finally:
        # These are our two public test writers, never arbitrary system PIDs.
        for child in (writer, waiting):
            if child is not None and child.poll() is None:
                child.kill()
        if thread is not None:
            thread.join(timeout=12)
        for child in (writer, waiting):
            if child is not None:
                child.communicate(timeout=5)
        public.cleanup()


def test_reader_primary_retained_when_source_descriptor_close_fails(tmp_path, monkeypatch):
    module = subject()
    source, config = fixture(tmp_path)
    reader = module.Coordinator(config, source)
    close, fstat = module.os.close, module.os.fstat

    def failed_close(descriptor):
        value = fstat(descriptor)
        close(descriptor)
        if value.st_ino == (source / 'unit.json').stat().st_ino:
            raise OSError('PUBLIC_SOURCE_CLOSE_SECONDARY')

    monkeypatch.setattr(module.os, 'close', failed_close)
    original = ValueError('PUBLIC_READER_PRIMARY')
    with pytest.raises(ValueError, match='PUBLIC_READER_PRIMARY') as stopped:
        with reader.claim('unit.json'):
            raise original
    assert stopped.value is original
    assert reader.records[0]['secondary_errors'][-1]['reason'] == 'PUBLIC_SOURCE_CLOSE_SECONDARY'
    assert reader.records[0]['helper_native_exit']['exit_code'] == 0
