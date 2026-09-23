import hashlib
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

import topolab.evaluation_cli as evaluation_cli
import topolab.m1_experiment as experiment_module
from topolab.catalog import M0_CASE_CATALOG_ID, build_m0_case_catalog
from topolab.dataset import DatasetEnvironment
from topolab.label_artifacts import LabelArtifactReference
from topolab.materialization import (
    DatasetMaterializationIndex,
    MaterializationSuccess,
    build_manifest_sha256,
)
from topolab.training import M1_SEEDS
from topolab.training_artifacts import (
    M1CheckpointReference,
    M1RuntimeEnvironment,
    M1SelectionReference,
)


def test_production_selection_references_use_frozen_hashes_and_sizes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_sha256 = "a" * 64
    frozen = tuple((seed, f"{seed:064x}") for seed in M1_SEEDS)
    monkeypatch.setattr(evaluation_cli, "M1_DATA_MANIFEST_SHA256", manifest_sha256)
    monkeypatch.setattr(evaluation_cli, "M1_PRODUCTION_SELECTION_SHA256", frozen)
    for seed, digest in frozen:
        target = (
            tmp_path
            / "m1"
            / "selections"
            / manifest_sha256
            / str(seed)
            / f"{digest}.json"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f"selection-{seed}".encode())

    references = evaluation_cli.production_selection_references(tmp_path)

    assert tuple(reference.seed for reference in references) == M1_SEEDS
    assert tuple(reference.sha256 for reference in references) == tuple(
        digest for _, digest in frozen
    )
    assert references[0].byte_size == len("selection-17")

    missing = tmp_path / references[-1].relative_path
    missing.unlink()
    with pytest.raises(
        evaluation_cli.M1EvaluationEntrypointError,
        match="seed 113 is missing",
    ):
        evaluation_cli.production_selection_references(tmp_path)


def test_selection_audit_requires_exact_fitting_data_and_shared_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization = _materialization()
    references = _selection_references(materialization.manifest_sha256)
    runtime = _runtime()
    training_ids = tuple(
        sample.case.case_id
        for sample in materialization.manifest.samples
        if sample.split == "train"
    )
    validation_ids = tuple(
        sample.case.case_id
        for sample in materialization.manifest.samples
        if sample.split == "validation"
    )
    inconsistent_seed: int | None = None

    def read(root: Path, reference: M1SelectionReference) -> SimpleNamespace:
        training_revision = (
            "d" * 40 if reference.seed == inconsistent_seed else "c" * 40
        )
        return SimpleNamespace(
            checkpoint=_checkpoint_reference(
                materialization.manifest_sha256,
                reference.seed,
            ),
            label_source_revision=materialization.manifest.source_revision,
            manifest_sha256=materialization.manifest_sha256,
            runtime=runtime,
            seed=reference.seed,
            selected_epoch=1,
            training_case_ids=training_ids,
            training_source_revision=training_revision,
            validation_case_ids=validation_ids,
        )

    monkeypatch.setattr(evaluation_cli, "read_m1_selection", read)

    summaries, checkpoints = evaluation_cli.audit_evaluation_selections(
        tmp_path,
        references,
        materialization=materialization,
    )

    assert tuple(summary["seed"] for summary in summaries) == M1_SEEDS
    assert tuple(reference.seed for reference in checkpoints) == M1_SEEDS
    inconsistent_seed = 113
    with pytest.raises(
        evaluation_cli.M1EvaluationEntrypointError,
        match="one fitting context",
    ):
        evaluation_cli.audit_evaluation_selections(
            tmp_path,
            references,
            materialization=materialization,
        )


def test_cli_defaults_to_verified_read_only_plan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = _repository(tmp_path)
    materialization = _materialization()
    references = _selection_references(materialization.manifest_sha256)
    output_root = tmp_path / "output"
    monkeypatch.chdir(repository)
    monkeypatch.setattr(
        experiment_module,
        "M1_DATA_MANIFEST_SHA256",
        materialization.manifest_sha256,
    )
    monkeypatch.setattr(
        evaluation_cli,
        "load_frozen_m1_materialization",
        lambda root: materialization,
    )
    monkeypatch.setattr(
        evaluation_cli,
        "production_selection_references",
        lambda root: references,
    )
    monkeypatch.setattr(
        evaluation_cli,
        "audit_evaluation_selections",
        lambda *args, **kwargs: (
            tuple({"seed": seed} for seed in M1_SEEDS),
            _checkpoint_references(materialization.manifest_sha256),
        ),
    )

    def fail_if_called(*args: object, **kwargs: object) -> object:
        raise AssertionError("plan mode must not load models or run held-out cases")

    monkeypatch.setattr(evaluation_cli, "load_evaluation_candidates", fail_if_called)
    monkeypatch.setattr(evaluation_cli, "run_m1_experiment", fail_if_called)

    assert evaluation_cli.main(
        [
            "--data-root",
            str(tmp_path / "data"),
            "--artifact-root",
            str(tmp_path / "artifacts"),
            "--output-root",
            str(output_root),
        ]
    ) == 0

    summary = json.loads(capsys.readouterr().out)
    assert summary["catalog_id"] == M0_CASE_CATALOG_ID
    assert summary["data_manifest_sha256"] == materialization.manifest_sha256
    assert summary["mode"] == "plan"
    assert summary["state"] == "planned"
    assert summary["test_cases"] == 6
    assert summary["ood_cases"] == 80
    assert summary["seeds"] == list(M1_SEEDS)
    assert len(summary["evaluation_id"]) == 64
    assert not output_root.exists()


def test_cli_execute_loads_all_candidates_runs_and_reports_statistics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    repository = _repository(tmp_path)
    materialization = _materialization()
    references = _selection_references(materialization.manifest_sha256)
    monkeypatch.chdir(repository)
    monkeypatch.setattr(
        experiment_module,
        "M1_DATA_MANIFEST_SHA256",
        materialization.manifest_sha256,
    )
    monkeypatch.setattr(
        evaluation_cli,
        "load_frozen_m1_materialization",
        lambda root: materialization,
    )
    monkeypatch.setattr(
        evaluation_cli,
        "production_selection_references",
        lambda root: references,
    )
    monkeypatch.setattr(
        evaluation_cli,
        "audit_evaluation_selections",
        lambda *args, **kwargs: (
            tuple({"seed": seed} for seed in M1_SEEDS),
            _checkpoint_references(materialization.manifest_sha256),
        ),
    )
    calls: list[str] = []
    candidates = tuple(SimpleNamespace(selection=reference) for reference in references)

    def load(*args: object, **kwargs: object) -> tuple[SimpleNamespace, ...]:
        calls.append("load")
        return candidates

    def run(*args: object, **kwargs: object) -> SimpleNamespace:
        calls.append("run")
        return SimpleNamespace(state="complete", entries=tuple(range(86)))

    def statistics(*args: object, **kwargs: object) -> SimpleNamespace:
        calls.append("statistics")
        return SimpleNamespace(
            model_dump=lambda mode: {
                "statistics_version": "topolab.m1.statistics.v1"
            }
        )

    monkeypatch.setattr(evaluation_cli, "load_evaluation_candidates", load)
    monkeypatch.setattr(evaluation_cli, "run_m1_experiment", run)
    monkeypatch.setattr(
        evaluation_cli,
        "compute_m1_experiment_statistics",
        statistics,
    )

    assert evaluation_cli.main(
        [
            "--data-root",
            str(tmp_path / "data"),
            "--artifact-root",
            str(tmp_path / "artifacts"),
            "--output-root",
            str(tmp_path / "output"),
            "--execute",
        ]
    ) == 0

    summary = json.loads(capsys.readouterr().out)
    assert calls == ["load", "run", "statistics"]
    assert summary["mode"] == "execute"
    assert summary["state"] == "complete"
    assert summary["completed_cases"] == 86
    assert summary["statistics"]["statistics_version"] == (
        "topolab.m1.statistics.v1"
    )


def _materialization() -> DatasetMaterializationIndex:
    manifest = build_m0_case_catalog().build_manifest(
        source_revision="b" * 40,
        environment=DatasetEnvironment(
            python_version="3.12.10",
            numpy_version="2.5.3",
            scipy_version="1.18.1",
            lockfile_sha256="a" * 64,
        ),
    )
    entries = tuple(
        MaterializationSuccess(
            case_id=sample.case.case_id,
            split=sample.split,
            artifact=LabelArtifactReference(
                case_id=sample.case.case_id,
                generator_version=manifest.generator_version,
                source_revision=manifest.source_revision,
                sha256=hashlib.sha256(sample.case.case_id.encode()).hexdigest(),
                byte_size=1,
                relative_path=(
                    f"labels/{sample.case.case_id}/"
                    f"{hashlib.sha256(sample.case.case_id.encode()).hexdigest()}.json"
                ),
            ),
        )
        for sample in manifest.samples
    )
    return DatasetMaterializationIndex(
        state="complete",
        manifest_sha256=build_manifest_sha256(manifest),
        manifest=manifest,
        entries=entries,
    )


def _selection_references(
    manifest_sha256: str,
) -> tuple[
    M1SelectionReference,
    M1SelectionReference,
    M1SelectionReference,
    M1SelectionReference,
    M1SelectionReference,
]:
    return tuple(  # type: ignore[return-value]
        M1SelectionReference(
            manifest_sha256=manifest_sha256,
            seed=seed,
            sha256=f"{seed:064x}",
            byte_size=1,
            relative_path=(
                f"m1/selections/{manifest_sha256}/{seed}/{seed:064x}.json"
            ),
        )
        for seed in M1_SEEDS
    )


def _runtime() -> M1RuntimeEnvironment:
    return M1RuntimeEnvironment(
        python_version="3.12.10",
        numpy_version="2.5.3",
        scipy_version="1.18.1",
        torch_version="2.14.0",
        safetensors_version="0.8.0",
        lockfile_sha256="d" * 64,
        platform_system="TestOS",
        platform_machine="test-machine",
        processor="test-processor",
        torch_num_threads=1,
        torch_num_interop_threads=1,
    )


def _checkpoint_references(
    manifest_sha256: str,
) -> tuple[
    M1CheckpointReference,
    M1CheckpointReference,
    M1CheckpointReference,
    M1CheckpointReference,
    M1CheckpointReference,
]:
    return tuple(  # type: ignore[return-value]
        _checkpoint_reference(manifest_sha256, seed) for seed in M1_SEEDS
    )


def _checkpoint_reference(
    manifest_sha256: str,
    seed: int,
) -> M1CheckpointReference:
    digest = f"{seed + 1:064x}"
    return M1CheckpointReference(
        manifest_sha256=manifest_sha256,
        label_source_revision="b" * 40,
        training_source_revision="c" * 40,
        runtime=_runtime(),
        seed=seed,
        selected_epoch=1,
        sha256=digest,
        byte_size=1,
        relative_path=(
            f"m1/checkpoints/{manifest_sha256}/{seed}/{digest}.safetensors"
        ),
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
