import hashlib
import json
import subprocess
from pathlib import Path

import pytest

import topolab.m2_dataset_cli as m2_dataset_cli
from topolab.m2_dataset import M2_CASE_CATALOG_ID, M2DatasetManifest
from topolab.materialization import (
    M2_MATERIALIZATION_INDEX_VERSION,
    DatasetMaterializationIndex,
    MaterializationFailure,
    build_manifest_sha256,
)


def test_m2_cli_defaults_to_read_only_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = _repository(tmp_path)
    output_root = tmp_path / "generated"
    monkeypatch.chdir(repository)

    def fail_if_called(*args: object, **kwargs: object) -> DatasetMaterializationIndex:
        raise AssertionError("plan mode must not materialize the M2 catalog")

    monkeypatch.setattr(m2_dataset_cli, "materialize_dataset", fail_if_called)

    assert m2_dataset_cli.main(["--output-root", str(output_root)]) == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary == {
        "catalog_id": M2_CASE_CATALOG_ID,
        "environment": {
            "lockfile_sha256": hashlib.sha256(
                (repository / "uv.lock").read_bytes()
            ).hexdigest(),
            "numpy_version": m2_dataset_cli.inspect_repository(
                repository
            ).environment.numpy_version,
            "python_version": m2_dataset_cli.inspect_repository(
                repository
            ).environment.python_version,
            "scipy_version": m2_dataset_cli.inspect_repository(
                repository
            ).environment.scipy_version,
        },
        "manifest_sha256": summary["manifest_sha256"],
        "mode": "plan",
        "source_revision": _git(repository, "rev-parse", "HEAD"),
        "source_tree_clean": True,
        "split_counts": {
            "ood": 252,
            "test": 36,
            "train": 432,
            "validation": 36,
        },
        "state": "planned",
        "summary_version": m2_dataset_cli.M2_MATERIALIZATION_SUMMARY_VERSION,
        "total_cases": 756,
    }
    assert len(summary["manifest_sha256"]) == 64
    assert not output_root.exists()


def test_m2_cli_execute_reports_terminal_failures_and_returns_nonzero(
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
        manifest: M2DatasetManifest,
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
            index_version=M2_MATERIALIZATION_INDEX_VERSION,
            state="complete",
            manifest_sha256=build_manifest_sha256(manifest),
            manifest=manifest,
            entries=entries,
        )

    monkeypatch.setattr(m2_dataset_cli, "materialize_dataset", record_failures)

    assert m2_dataset_cli.main(["--output-root", str(output_root), "--execute"]) == 1

    summary = json.loads(capsys.readouterr().out)
    assert called_with == [output_root.resolve()]
    assert summary["mode"] == "execute"
    assert summary["state"] == "complete"
    assert summary["succeeded"] == 0
    assert summary["failed"] == 756


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
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
