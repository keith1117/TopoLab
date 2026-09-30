"""B3 read-only planning, frozen-runtime preflight, and explicit execution wiring."""

import json
import subprocess
from pathlib import Path

import pytest

import topolab.b3_dataset_cli as cli
import topolab.b3_materialization as materialization
from topolab.b3_materialization import B3DataFailure, B3MaterializationIndex, write_b3_index
from topolab.dataset_cli import DatasetEntrypointError, RepositorySnapshot


def _forbidden(*args, **kwargs):  # type: ignore[no-untyped-def]
    raise AssertionError("read-only planning reached generation or artifact bytes")


def test_plan_creates_no_root_and_reads_no_artifacts(tmp_path, b3_manifest, monkeypatch, capsys):  # type: ignore[no-untyped-def]
    repository = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(cli, "build_current_b3_manifest", lambda cwd: (repository, b3_manifest))
    monkeypatch.setattr(cli, "run_b3_data", _forbidden)
    monkeypatch.setattr(materialization, "read_b3_record", _forbidden)
    root = tmp_path / "absent"
    assert cli.main(["--output-root", str(root)]) == 0
    assert not root.exists()
    summary = json.loads(capsys.readouterr().out)
    assert summary["mode"] == "plan"
    assert (summary["labels"], summary["references"], summary["final_artifacts"]) == (560, 48, 0)
    root.mkdir()
    index = B3MaterializationIndex.start(b3_manifest).model_copy(
        update={
            "entries": (B3DataFailure(entry=b3_manifest.data_entries()[0], seconds=1),),
            "cumulative_seconds": 1,
        }
    )
    write_b3_index(root, index)
    assert cli.main(["--output-root", str(root)]) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary["recorded"] == 1 and summary["cumulative_seconds"] == 1


@pytest.mark.parametrize("mode", ["--execute", "--audit"])
def test_execution_is_explicit_and_charges_startup(
    tmp_path, b3_manifest, monkeypatch, capsys, mode
):  # type: ignore[no-untyped-def]
    repository = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(cli, "build_current_b3_manifest", lambda cwd: (repository, b3_manifest))
    calls = []

    def run(root, manifest, **kwargs):  # type: ignore[no-untyped-def]
        calls.append((root, manifest, kwargs))
        return B3MaterializationIndex.start(manifest)

    monkeypatch.setattr(cli, "run_b3_data", run)
    root = tmp_path / "data"
    assert cli.main(["--output-root", str(root), mode]) == 1
    assert calls[0][0] == root.resolve()
    assert calls[0][2]["audit_only"] == (mode == "--audit")
    assert calls[0][2]["startup_seconds"] >= 0
    assert json.loads(capsys.readouterr().out)["data_gate_passed"] is False
    with pytest.raises(SystemExit) as error:
        cli.main([mode])
    assert error.value.code == 2


def test_cli_rejects_repository_output_and_foreign_implementation(
    tmp_path, b3_manifest, monkeypatch, capsys
):  # type: ignore[no-untyped-def]
    repository = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(cli, "build_current_b3_manifest", lambda cwd: (repository, b3_manifest))
    monkeypatch.setattr(cli, "run_b3_data", _forbidden)
    assert cli.main(["--output-root", str(repository / "data"), "--execute"]) == 2
    assert "outside" in capsys.readouterr().err
    monkeypatch.setattr(
        cli, "build_current_b3_manifest", lambda cwd: (tmp_path / "other-checkout", b3_manifest)
    )
    assert cli.main(["--output-root", str(tmp_path / "data"), "--execute"]) == 2
    assert "recorded checkout" in capsys.readouterr().err


def _preflight_fixture(tmp_path, b3_manifest, monkeypatch):  # type: ignore[no-untyped-def]
    source = Path(__file__).resolve().parents[1]
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/b3_experiment_contract.md").write_bytes(
        (source / "docs/b3_experiment_contract.md").read_bytes()
    )
    (tmp_path / "uv.lock").write_bytes((source / "uv.lock").read_bytes())
    snapshot = RepositorySnapshot(
        root=tmp_path,
        source_revision=b3_manifest.context.source_revision,
        environment=b3_manifest.context.environment,
    )
    monkeypatch.setattr(cli, "inspect_repository", lambda cwd: snapshot)
    monkeypatch.setattr(cli, "capture_b3_runtime", lambda: b3_manifest.context.runtime)
    calls = []

    def run(command, **kwargs):  # type: ignore[no-untyped-def]
        calls.append(command)
        return subprocess.CompletedProcess(command, 0)

    monkeypatch.setattr(cli.subprocess, "run", run)
    return calls


def test_preflight_binds_contract_merged_source_lock_and_runtime(
    tmp_path, b3_manifest, monkeypatch
):  # type: ignore[no-untyped-def]
    calls = _preflight_fixture(tmp_path, b3_manifest, monkeypatch)
    repository, manifest = cli.build_current_b3_manifest(tmp_path)
    assert repository == tmp_path
    assert manifest == b3_manifest
    assert calls[0] == [
        "git",
        "merge-base",
        "--is-ancestor",
        b3_manifest.context.source_revision,
        "refs/remotes/origin/main",
    ]
    assert calls[1][:4] == ["git", "diff", "--quiet", cli.B3_NUMERICAL_ANCHOR]
    assert "src/topolab/simp.py" in calls[1]


@pytest.mark.parametrize("failure", ["dirty", "contract", "unmerged", "numerical", "package"])
def test_preflight_rejects_invalid_source_and_environment(
    tmp_path, b3_manifest, monkeypatch, failure
):  # type: ignore[no-untyped-def]
    _preflight_fixture(tmp_path, b3_manifest, monkeypatch)
    if failure == "dirty":

        def dirty(cwd):  # type: ignore[no-untyped-def]
            raise DatasetEntrypointError("source worktree must be clean")

        monkeypatch.setattr(cli, "inspect_repository", dirty)
    elif failure == "contract":
        (tmp_path / "docs/b3_experiment_contract.md").write_bytes(b"changed")
    elif failure in ("unmerged", "numerical"):

        def run(command, **kwargs):  # type: ignore[no-untyped-def]
            fail = command[1] == ("merge-base" if failure == "unmerged" else "diff")
            return subprocess.CompletedProcess(command, 1 if fail else 0)

        monkeypatch.setattr(cli.subprocess, "run", run)
    else:
        original = cli.importlib.metadata.version
        monkeypatch.setattr(
            cli.importlib.metadata,
            "version",
            lambda name: "9.9.9" if name == "numpy" else original(name),
        )
    with pytest.raises((ValueError, RuntimeError)):
        cli.build_current_b3_manifest(tmp_path)


def _runtime_fixture(monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(cli.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(cli.platform, "release", lambda: "test-runtime")
    for name in cli._BLAS_VARIABLES:
        monkeypatch.setenv(name, "1")
    monkeypatch.setattr(cli.torch, "set_num_threads", lambda count: None)
    monkeypatch.setattr(cli.torch, "get_num_threads", lambda: 1)
    monkeypatch.setattr(cli.torch, "get_num_interop_threads", lambda: 8)
    monkeypatch.setattr(
        cli.subprocess,
        "check_output",
        lambda command, **kwargs: (
            "Apple M2\n" if command[-1] == "machdep.cpu.brand_string" else str(16 * 1024**3)
        ),
    )


def test_capture_runtime_requires_actual_thread_and_cpu_settings(monkeypatch):  # type: ignore[no-untyped-def]
    _runtime_fixture(monkeypatch)
    runtime = cli.capture_b3_runtime()
    assert runtime.cpu == "Apple M2" and runtime.blas_threads == 1
    monkeypatch.setenv("OPENBLAS_NUM_THREADS", "2")
    with pytest.raises(ValueError, match="thread variables"):
        cli.capture_b3_runtime()


@pytest.mark.parametrize("failure", ["linux", "cpu", "machine", "torch_threads"])
def test_capture_runtime_rejects_foreign_host(monkeypatch, failure):  # type: ignore[no-untyped-def]
    _runtime_fixture(monkeypatch)
    if failure == "linux":
        monkeypatch.setattr(cli.platform, "system", lambda: "Linux")
    elif failure == "cpu":
        monkeypatch.setattr(
            cli.subprocess,
            "check_output",
            lambda command, **kwargs: (
                "Apple M3" if command[-1] == "machdep.cpu.brand_string" else str(16 * 1024**3)
            ),
        )
    elif failure == "machine":
        monkeypatch.setattr(cli.platform, "machine", lambda: "x86_64")
    else:
        monkeypatch.setattr(cli.torch, "get_num_threads", lambda: 2)
    with pytest.raises(ValueError):
        cli.capture_b3_runtime()
