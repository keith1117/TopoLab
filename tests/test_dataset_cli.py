import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import topolab.dataset_cli as dataset_cli
from topolab.catalog import M0_CASE_CATALOG_ID
from topolab.materialization import (
    DatasetMaterializationIndex,
    MaterializationFailure,
    build_manifest_sha256,
)


def test_repository_snapshot_captures_clean_revision_and_environment(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path)

    snapshot = dataset_cli.inspect_repository(repository / "nested")

    assert snapshot.root == repository.resolve()
    assert snapshot.source_revision == _git(repository, "rev-parse", "HEAD")
    assert snapshot.environment.python_version
    assert snapshot.environment.numpy_version
    assert snapshot.environment.scipy_version
    assert snapshot.environment.lockfile_sha256 == hashlib.sha256(
        (repository / "uv.lock").read_bytes()
    ).hexdigest()


def test_repository_snapshot_rejects_dirty_worktree(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    (repository / "untracked.txt").write_text("dirty\n", encoding="utf-8")

    with pytest.raises(dataset_cli.DatasetEntrypointError, match="must be clean"):
        dataset_cli.inspect_repository(repository)


def test_output_root_must_resolve_outside_repository(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    external = tmp_path / "generated"

    assert dataset_cli.validate_external_output_root(repository, external) == (
        external.resolve()
    )
    with pytest.raises(dataset_cli.DatasetEntrypointError, match="outside"):
        dataset_cli.validate_external_output_root(repository, repository)
    with pytest.raises(dataset_cli.DatasetEntrypointError, match="outside"):
        dataset_cli.validate_external_output_root(repository, repository / "data")


def test_cli_defaults_to_read_only_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = _repository(tmp_path)
    output_root = tmp_path / "generated"
    monkeypatch.chdir(repository)

    def fail_if_called(*args: object, **kwargs: object) -> DatasetMaterializationIndex:
        raise AssertionError("plan mode must not materialize the catalog")

    monkeypatch.setattr(dataset_cli, "materialize_dataset", fail_if_called)

    assert dataset_cli.main(["--output-root", str(output_root)]) == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "catalog_id": M0_CASE_CATALOG_ID,
        "environment": {
            "lockfile_sha256": hashlib.sha256(
                (repository / "uv.lock").read_bytes()
            ).hexdigest(),
            "numpy_version": snapshot_version("numpy"),
            "python_version": dataset_cli.platform.python_version(),
            "scipy_version": snapshot_version("scipy"),
        },
        "manifest_sha256": summary["manifest_sha256"],
        "mode": "plan",
        "source_revision": _git(repository, "rev-parse", "HEAD"),
        "source_tree_clean": True,
        "split_counts": {"ood": 80, "test": 6, "train": 66, "validation": 8},
        "state": "planned",
        "summary_version": dataset_cli.MATERIALIZATION_SUMMARY_VERSION,
        "total_cases": 160,
    }
    assert len(summary["manifest_sha256"]) == 64
    assert not output_root.exists()


def test_cli_execute_reports_terminal_failures_and_returns_nonzero(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = _repository(tmp_path)
    output_root = tmp_path / "generated"
    monkeypatch.chdir(repository)
    called_with: list[Path] = []

    def record_failures(
        root: Path,
        manifest: dataset_cli.DatasetManifest,
    ) -> DatasetMaterializationIndex:
        called_with.append(root)
        entries = tuple(
            MaterializationFailure(
                case_id=sample.case.case_id,
                split=sample.split,
                failure_code="label_generation_error",
            )
            for sample in manifest.samples
        )
        return DatasetMaterializationIndex(
            state="complete",
            manifest_sha256=build_manifest_sha256(manifest),
            manifest=manifest,
            entries=entries,
        )

    monkeypatch.setattr(dataset_cli, "materialize_dataset", record_failures)

    assert dataset_cli.main(["--output-root", str(output_root), "--execute"]) == 1

    summary = json.loads(capsys.readouterr().out)
    assert called_with == [output_root.resolve()]
    assert summary["mode"] == "execute"
    assert summary["state"] == "complete"
    assert summary["succeeded"] == 0
    assert summary["failed"] == 160


def snapshot_version(distribution: str) -> str:
    return dataset_cli.importlib.metadata.version(distribution)


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    (repository / "nested").mkdir()
    (repository / "uv.lock").write_text("version = 1\n", encoding="utf-8")
    _git(repository, "init", "--quiet", "--initial-branch=main")
    _git(repository, "add", "uv.lock")
    _git(
        repository,
        "-c",
        "user.name=TopoLab Tests",
        "-c",
        "user.email=tests@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "fixture",
    )
    return repository


def _git(repository: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=repository,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()
