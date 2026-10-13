"""Public subprocess acceptance for origin checks and immutable crash receipts."""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SOURCE = Path(__file__).resolve().parents[1]
RUNNER = SOURCE / "src/topolab/launch_preflight.py"
FIXTURE = json.loads((SOURCE / "tests/fixtures/b4_45_launch_preflight.json").read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_request(tmp_path, kind="healthy"):
    probe = tmp_path / "probe"
    probe.mkdir()
    marker = probe / "b4_45_public_marker.py"
    marker.write_text(FIXTURE["source_texts"][kind])
    request = {
        "version": "topolab.public-launch-preflight.v1",
        "source_root": str(SOURCE),
        "expected_executable": sys.executable,
        "expected_cwd": str(SOURCE),
        "expected_source_revision": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True
        ).strip(),
        "expected_lock_sha256": digest(SOURCE / "uv.lock"),
        "expected_pyproject_sha256": digest(SOURCE / "pyproject.toml"),
        "expected_package_sha256": digest(SOURCE / "src/topolab/__init__.py"),
        "probe_root": str(probe),
        "expected_probe_origin": str(marker),
        "expected_probe_sha256": FIXTURE["source_sha256"][kind],
        "path_mode": "source",
    }
    return request, marker


def launch(tmp_path, request, raw=None, output=None, env=None):
    path = tmp_path / "request.json"
    path.write_text(json.dumps(request) if raw is None else raw)
    output = tmp_path / "output" if output is None else output
    result = subprocess.run(
        [sys.executable, "-I", str(RUNNER), str(path), str(output)],
        cwd=SOURCE,
        capture_output=True,
        env=env,
    )
    assert result.stderr == b"", result.stderr.decode()
    status = json.loads(result.stdout)["status"]
    if status == "REFUSED_EXISTING_OUTPUT":
        return status, None, result
    terminal = json.loads((output / "terminal.json").read_text())
    assert terminal["status"] == status
    assert terminal["phase"] == "TERMINAL_AFTER_OBSERVED_EXIT"
    assert terminal["sha256"]["pending.json"] == digest(output / "pending.json")
    for name, value in terminal["sha256"].items():
        assert value == (digest(output / name) if (output / name).exists() else None)
    return status, terminal, result


def test_isolated_external_launch_records_origins_without_topolab_import(tmp_path):
    request, marker = make_request(tmp_path)
    status, terminal, result = launch(tmp_path, request)
    assert status == "PASS_PUBLIC_PREFLIGHT" and result.returncode == 0
    assert terminal["attempts"] == terminal["completed"] == 1
    context = json.loads((tmp_path / "output/probe_result.json").read_text())["context"]
    assert context["probe_origin"] == context["probe_loaded_origin"] == str(marker)
    assert context["package_origin"] == str(SOURCE / "src/topolab/__init__.py")
    assert context["application_modules_before"] == context["application_modules_after"] == []
    assert context["executable"] == sys.executable and context["isolated"] == 1


@pytest.mark.parametrize(
    ("field", "value", "status"),
    [
        ("expected_executable", "/deliberately-absent/python", "STOP_INTERPRETER"),
        ("expected_cwd", "/deliberately-absent/cwd", "STOP_CWD"),
        ("expected_source_revision", "0" * 40, "STOP_SOURCE"),
        ("expected_lock_sha256", "0" * 64, "STOP_LOCK"),
        ("expected_pyproject_sha256", "0" * 64, "STOP_LOCK"),
        ("expected_package_sha256", "0" * 64, "STOP_PACKAGE_HASH"),
        ("path_mode", "without_source", "STOP_PACKAGE_ORIGIN"),
        ("expected_probe_origin", "/deliberately-absent/probe.py", "STOP_PROBE_ORIGIN"),
    ],
)
def test_context_mismatch_stops_before_probe(tmp_path, field, value, status):
    request, _ = make_request(tmp_path)
    request[field] = value
    actual, terminal, _ = launch(tmp_path, request)
    assert actual == status and terminal["attempts"] == terminal["completed"] == 0
    assert not (tmp_path / "output/started.json").exists()


@pytest.mark.parametrize("mutation", ["changed-bytes", "shadow-origin"])
def test_probe_bytes_or_resolution_cannot_select_another_source(tmp_path, mutation):
    request, marker = make_request(tmp_path)
    if mutation == "changed-bytes":
        marker.write_text("# public mutation\n" + marker.read_text())
        expected = "STOP_PROBE_HASH"
    else:
        shadow = tmp_path / "shadow"
        shadow.mkdir()
        (shadow / marker.name).write_bytes(marker.read_bytes())
        request["probe_root"] = str(shadow)
        expected = "STOP_PROBE_ORIGIN"
    status, terminal, _ = launch(tmp_path, request)
    assert status == expected and terminal["attempts"] == 0


@pytest.mark.parametrize(
    ("kind", "expected", "completed"),
    [
        ("import_failure", "STOP_IMPORT", 0),
        ("early_exit", "FAIL_CHILD_EXIT", "UNKNOWN_NOT_WRITTEN"),
        ("timeout", "FAIL_TIMEOUT", "UNKNOWN_NOT_WRITTEN"),
    ],
)
def test_exception_exit_and_timeout_keep_terminal_and_missing_completion(
    tmp_path, kind, expected, completed
):
    request, _ = make_request(tmp_path, kind)
    status, terminal, _ = launch(tmp_path, request)
    assert status == expected and terminal["attempts"] == 1
    assert terminal["completed"] == completed
    assert (tmp_path / "output/started.json").is_file()
    if kind == "import_failure":
        outcome = json.loads((tmp_path / "output/probe_result.json").read_text())
        assert "RuntimeError" in outcome["traceback"]
    else:
        assert terminal["result_state"] == "NOT_WRITTEN"
        assert not (tmp_path / "output/probe_result.json").exists()


@pytest.mark.parametrize("kind", ["directory", "file", "symlink", "completed-receipts"])
def test_existing_output_is_refused_before_missing_request_read(tmp_path, kind):
    request, _ = make_request(tmp_path)
    output = tmp_path / "output"
    if kind in ("directory", "completed-receipts"):
        if kind == "completed-receipts":
            launch(tmp_path, request)
        else:
            output.mkdir()
            (output / "sentinel").write_text("preserve original public test bytes")
        before = {p.name: digest(p) for p in output.iterdir()}
    elif kind == "file":
        output.write_text("preserve existing public file")
        before = digest(output)
    else:
        target = tmp_path / "target"
        target.mkdir()
        output.symlink_to(target, target_is_directory=True)
        before = str(output.readlink())
    result = subprocess.run(
        [sys.executable, "-I", str(RUNNER), str(tmp_path / "missing-request"), str(output)],
        cwd=SOURCE,
        capture_output=True,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["status"] == "REFUSED_EXISTING_OUTPUT"
    after = (
        {p.name: digest(p) for p in output.iterdir()}
        if kind in ("directory", "completed-receipts")
        else digest(output)
        if kind == "file"
        else str(output.readlink())
    )
    assert before == after


@pytest.mark.parametrize(
    "mutation",
    [
        "extra",
        "missing",
        "duplicate",
        "nested-duplicate",
        "NaN",
        "Infinity",
        "nonobject",
        "bool",
        "relative",
        "bad-hash",
        "unlisted-probe",
        "large",
    ],
)
def test_invalid_request_has_immutable_stop_and_no_probe(tmp_path, mutation):
    request, _ = make_request(tmp_path)
    raw = None
    if mutation == "extra":
        request["unregistered"] = "denied"
    elif mutation == "missing":
        del request["expected_cwd"]
    elif mutation == "duplicate":
        raw = json.dumps(request)[:-1] + ', "version": "duplicate"}'
    elif mutation == "nested-duplicate":
        raw = json.dumps(request)[:-1] + ', "extra": {"a":1,"a":2}}'
    elif mutation in ("NaN", "Infinity"):
        raw = json.dumps(request)[:-1] + ', "extra": ' + mutation + "}"
    elif mutation == "nonobject":
        raw = "[]"
    elif mutation == "bool":
        request["expected_cwd"] = True
    elif mutation == "relative":
        request["probe_root"] = "relative"
    elif mutation == "bad-hash":
        request["expected_lock_sha256"] = "X" * 64
    elif mutation == "unlisted-probe":
        request["expected_probe_sha256"] = "0" * 64
    else:
        raw = " " * 32769
    status, terminal, _ = launch(tmp_path, request, raw=raw)
    assert status == ("STOP_REQUEST" if mutation == "large" else "STOP_SCHEMA")
    assert terminal["attempts"] in (0, "UNKNOWN_NOT_WRITTEN")
    assert not (tmp_path / "output/started.json").exists()


def test_pythonpath_shadow_is_ignored_by_isolated_child(tmp_path):
    request, marker = make_request(tmp_path)
    shadow = tmp_path / "injected"
    shadow.mkdir()
    (shadow / marker.name).write_text('raise RuntimeError("unregistered shadow")\n')
    status, _, _ = launch(tmp_path, request, env=dict(os.environ, PYTHONPATH=str(shadow)))
    assert status == "PASS_PUBLIC_PREFLIGHT"


def test_missing_request_has_pending_and_terminal_without_claiming_zero(tmp_path):
    output = tmp_path / "output"
    result = subprocess.run(
        [sys.executable, "-I", str(RUNNER), str(tmp_path / "missing"), str(output)],
        cwd=SOURCE,
        capture_output=True,
    )
    assert result.returncode == 1
    terminal = json.loads((output / "terminal.json").read_text())
    assert terminal["status"] == "STOP_REQUEST"
    assert terminal["request_sha256"] is None
    assert terminal["completed"] == "UNKNOWN_NOT_WRITTEN"
