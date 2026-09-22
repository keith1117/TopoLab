import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import topolab.training_cli as training_cli
from topolab.catalog import M0_CASE_CATALOG_ID, build_m0_case_catalog
from topolab.dataset import DatasetEnvironment
from topolab.label_artifacts import LabelArtifactReference
from topolab.materialization import (
    DatasetMaterializationIndex,
    MaterializationFailure,
    MaterializationSuccess,
    build_manifest_sha256,
    canonical_materialization_index_bytes,
)
from topolab.training import M1_SEEDS
from topolab.training_artifacts import M1RuntimeEnvironment, M1SelectionReference


def test_frozen_materialization_load_is_metadata_only_and_canonical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = _materialization()
    root = tmp_path / "data"
    _write_index(root, index)
    monkeypatch.setattr(
        training_cli,
        "M1_DATA_MANIFEST_SHA256",
        index.manifest_sha256,
    )

    loaded = training_cli.load_frozen_m1_materialization(root)

    assert loaded == index
    assert not (root / "labels").exists()


def test_frozen_materialization_rejects_noncanonical_and_failed_indexes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = _materialization()
    root = tmp_path / "data"
    target = _write_index(root, index)
    monkeypatch.setattr(
        training_cli,
        "M1_DATA_MANIFEST_SHA256",
        index.manifest_sha256,
    )
    target.write_text(
        json.dumps(index.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )

    with pytest.raises(
        training_cli.M1TrainingEntrypointError,
        match="canonical",
    ):
        training_cli.load_frozen_m1_materialization(root)

    failed = _materialization(failed=True)
    _write_index(root, failed)
    with pytest.raises(
        training_cli.M1TrainingEntrypointError,
        match="zero-failure",
    ):
        training_cli.load_frozen_m1_materialization(root)


def test_cli_defaults_to_verified_read_only_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = _repository(tmp_path)
    data_root = tmp_path / "data"
    artifact_root = tmp_path / "artifacts"
    index = _materialization()
    _write_index(data_root, index)
    monkeypatch.setattr(
        training_cli,
        "M1_DATA_MANIFEST_SHA256",
        index.manifest_sha256,
    )
    monkeypatch.chdir(repository)

    def fail_if_called(*args: object, **kwargs: object) -> object:
        raise AssertionError("plan mode must not fit any seed")

    monkeypatch.setattr(training_cli, "train_all_m1_seeds", fail_if_called)

    assert training_cli.main(
        [
            "--data-root",
            str(data_root),
            "--artifact-root",
            str(artifact_root),
        ]
    ) == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary["catalog_id"] == M0_CASE_CATALOG_ID
    assert summary["data_manifest_sha256"] == index.manifest_sha256
    assert summary["mode"] == "plan"
    assert summary["seeds"] == list(M1_SEEDS)
    assert summary["state"] == "planned"
    assert summary["training_cases"] == 66
    assert summary["validation_cases"] == 8
    assert summary["training_source_revision"] == _git(
        repository,
        "rev-parse",
        "HEAD",
    )
    assert not artifact_root.exists()


def test_cli_execute_trains_then_audits_all_seeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = _repository(tmp_path)
    data_root = tmp_path / "data"
    artifact_root = tmp_path / "artifacts"
    index = _materialization()
    _write_index(data_root, index)
    monkeypatch.setattr(
        training_cli,
        "M1_DATA_MANIFEST_SHA256",
        index.manifest_sha256,
    )
    monkeypatch.chdir(repository)
    references = _selection_references(index.manifest_sha256)
    called: list[str] = []

    def train(*args: object, **kwargs: object) -> tuple[M1SelectionReference, ...]:
        called.append("train")
        return references

    def audit(*args: object, **kwargs: object) -> tuple[dict[str, object], ...]:
        called.append("audit")
        return tuple({"seed": seed} for seed in M1_SEEDS)

    monkeypatch.setattr(training_cli, "train_all_m1_seeds", train)
    monkeypatch.setattr(training_cli, "audit_m1_selections", audit)

    assert training_cli.main(
        [
            "--data-root",
            str(data_root),
            "--artifact-root",
            str(artifact_root),
            "--execute",
        ]
    ) == 0

    summary = json.loads(capsys.readouterr().out)
    assert called == ["train", "audit"]
    assert summary["mode"] == "execute"
    assert summary["state"] == "complete"
    assert [selection["seed"] for selection in summary["selections"]] == list(
        M1_SEEDS
    )


def test_selection_audit_requires_all_seeds_and_exact_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = _materialization()
    runtime = _runtime()
    references = _selection_references(index.manifest_sha256)
    training_ids = tuple(
        sample.case.case_id
        for sample in index.manifest.samples
        if sample.split == "train"
    )
    validation_ids = tuple(
        sample.case.case_id
        for sample in index.manifest.samples
        if sample.split == "validation"
    )

    def read(
        root: Path,
        reference: M1SelectionReference,
    ) -> SimpleNamespace:
        return SimpleNamespace(
            checkpoint=SimpleNamespace(
                relative_path=f"checkpoint-{reference.seed}",
                sha256=f"{reference.seed + 1:064x}",
            ),
            history=(object(),),
            label_source_revision=index.manifest.source_revision,
            manifest_sha256=index.manifest_sha256,
            runtime=runtime,
            seed=reference.seed,
            selected_epoch=1,
            selected_validation_mse=0.1,
            stopped_early=True,
            training_case_ids=training_ids,
            training_duration_seconds=0.25,
            training_source_revision="c" * 40,
            validation_case_ids=validation_ids,
        )

    monkeypatch.setattr(training_cli, "read_m1_selection", read)

    summaries = training_cli.audit_m1_selections(
        tmp_path,
        references,
        materialization=index,
        training_source_revision="c" * 40,
        runtime=runtime,
    )

    assert tuple(summary["seed"] for summary in summaries) == M1_SEEDS
    with pytest.raises(
        training_cli.M1TrainingEntrypointError,
        match="every frozen M1 seed",
    ):
        training_cli.audit_m1_selections(
            tmp_path,
            references[:-1],
            materialization=index,
            training_source_revision="c" * 40,
            runtime=runtime,
        )


def _materialization(*, failed: bool = False) -> DatasetMaterializationIndex:
    manifest = build_m0_case_catalog().build_manifest(
        source_revision="b" * 40,
        environment=DatasetEnvironment(
            python_version="3.12.10",
            numpy_version="2.5.3",
            scipy_version="1.18.1",
            lockfile_sha256="a" * 64,
        ),
    )
    entries: list[MaterializationSuccess | MaterializationFailure] = []
    for index, sample in enumerate(manifest.samples):
        if failed and index == 0:
            entries.append(
                MaterializationFailure(
                    case_id=sample.case.case_id,
                    split=sample.split,
                    failure_code="label_generation_error",
                )
            )
            continue
        digest = hashlib.sha256(sample.case.case_id.encode()).hexdigest()
        entries.append(
            MaterializationSuccess(
                case_id=sample.case.case_id,
                split=sample.split,
                artifact=LabelArtifactReference(
                    case_id=sample.case.case_id,
                    generator_version=manifest.generator_version,
                    source_revision=manifest.source_revision,
                    sha256=digest,
                    byte_size=1,
                    relative_path=(
                        f"labels/{sample.case.case_id}/{digest}.json"
                    ),
                ),
            )
        )
    return DatasetMaterializationIndex(
        state="complete",
        manifest_sha256=build_manifest_sha256(manifest),
        manifest=manifest,
        entries=tuple(entries),
    )


def _write_index(root: Path, index: DatasetMaterializationIndex) -> Path:
    target = root / "materializations" / f"{index.manifest_sha256}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(canonical_materialization_index_bytes(index))
    return target


def _selection_references(
    manifest_sha256: str,
) -> tuple[M1SelectionReference, ...]:
    references = []
    for seed in M1_SEEDS:
        digest = f"{seed:064x}"
        references.append(
            M1SelectionReference(
                manifest_sha256=manifest_sha256,
                seed=seed,
                sha256=digest,
                byte_size=1,
                relative_path=(
                    f"m1/selections/{manifest_sha256}/{seed}/{digest}.json"
                ),
            )
        )
    return tuple(references)


def _runtime() -> M1RuntimeEnvironment:
    return M1RuntimeEnvironment(
        python_version="3.12.10",
        numpy_version="2.5.3",
        scipy_version="1.18.1",
        torch_version="2.8.0+cpu",
        safetensors_version="0.8.0",
        lockfile_sha256="d" * 64,
        platform_system="TestOS",
        platform_machine="test-machine",
        processor="test-processor",
        torch_num_threads=1,
        torch_num_interop_threads=1,
    )


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
