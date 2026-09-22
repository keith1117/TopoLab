import hashlib
from pathlib import Path, PurePosixPath

import pytest
import torch
from pydantic import ValidationError

import topolab.training_artifacts as artifact_module
from topolab.dataset import DatasetEnvironment, DatasetManifest
from topolab.experiment import ExperimentCase
from topolab.label_artifacts import LabelArtifactReference
from topolab.materialization import (
    DatasetMaterializationIndex,
    MaterializationSuccess,
    build_manifest_sha256,
)
from topolab.problem import (
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)
from topolab.training import (
    M1_SEEDS,
    M1EpochMetrics,
    M1FitResult,
    M1TensorDataset,
    WarmStartCNN,
)
from topolab.training_artifacts import (
    M1ArtifactError,
    M1CheckpointReference,
    M1RuntimeEnvironment,
    M1SelectionRecord,
    M1SelectionReference,
    canonical_selection_bytes,
    capture_m1_runtime,
    load_m1_model,
    read_m1_checkpoint,
    read_m1_selection,
    train_all_m1_seeds,
    write_m1_checkpoint,
    write_m1_fit_artifacts,
)


@pytest.fixture
def artifact_context() -> tuple[
    DatasetMaterializationIndex,
    M1TensorDataset,
    M1TensorDataset,
    M1RuntimeEnvironment,
]:
    manifest = DatasetManifest.from_cases(
        _partition_cases(),
        source_revision="b" * 40,
        environment=_environment(),
    )
    entries = tuple(
        MaterializationSuccess(
            case_id=sample.case.case_id,
            split=sample.split,
            artifact=_label_reference(sample.case.case_id),
        )
        for sample in manifest.samples
    )
    materialization = DatasetMaterializationIndex(
        state="complete",
        manifest_sha256=build_manifest_sha256(manifest),
        manifest=manifest,
        entries=entries,
    )
    training_ids = tuple(
        sample.case.case_id for sample in manifest.samples if sample.split == "train"
    )
    validation_ids = tuple(
        sample.case.case_id
        for sample in manifest.samples
        if sample.split == "validation"
    )
    return (
        materialization,
        _dataset("train", training_ids),
        _dataset("validation", validation_ids),
        _runtime(),
    )


def test_checkpoint_and_selection_are_canonical_verified_and_loadable(
    tmp_path: Path,
    artifact_context: tuple[
        DatasetMaterializationIndex,
        M1TensorDataset,
        M1TensorDataset,
        M1RuntimeEnvironment,
    ],
) -> None:
    materialization, training, validation, runtime = artifact_context
    fit = _fit_result(17)

    first = write_m1_fit_artifacts(
        tmp_path,
        fit,
        materialization=materialization,
        training_dataset=training,
        validation_dataset=validation,
        training_source_revision="c" * 40,
        runtime=runtime,
    )
    repeated = write_m1_fit_artifacts(
        tmp_path,
        fit,
        materialization=materialization,
        training_dataset=training,
        validation_dataset=validation,
        training_source_revision="c" * 40,
        runtime=runtime,
    )
    selection = read_m1_selection(tmp_path, first)
    checkpoint_state = read_m1_checkpoint(tmp_path, selection.checkpoint)
    loaded = load_m1_model(tmp_path, selection.checkpoint)

    assert repeated == first
    assert first.sha256 == hashlib.sha256(canonical_selection_bytes(selection)).hexdigest()
    assert selection.seed == 17
    assert selection.selected_epoch == 1
    assert selection.history == fit.history
    assert selection.checkpoint.seed == selection.seed
    assert selection.checkpoint.selected_epoch == selection.selected_epoch
    assert selection.checkpoint.manifest_sha256 == materialization.manifest_sha256
    assert selection.checkpoint.relative_path.endswith(".safetensors")
    assert selection.training_case_ids == training.case_ids
    assert selection.validation_case_ids == validation.case_ids
    loaded_state = loaded.state_dict()
    for name, expected in fit.selected_state:
        torch.testing.assert_close(checkpoint_state[name], expected, rtol=0.0, atol=0.0)
        torch.testing.assert_close(loaded_state[name], expected, rtol=0.0, atol=0.0)


def test_selection_enforces_earliest_minimum_and_manifest_datasets(
    tmp_path: Path,
    artifact_context: tuple[
        DatasetMaterializationIndex,
        M1TensorDataset,
        M1TensorDataset,
        M1RuntimeEnvironment,
    ],
) -> None:
    materialization, training, validation, runtime = artifact_context
    fit = _fit_result(17)
    checkpoint = write_m1_checkpoint(
        tmp_path,
        fit,
        materialization=materialization,
        training_source_revision="c" * 40,
        runtime=runtime,
    )
    selection = M1SelectionRecord.from_fit(
        fit,
        materialization=materialization,
        training_dataset=training,
        validation_dataset=validation,
        training_source_revision="c" * 40,
        runtime=runtime,
        checkpoint=checkpoint,
    )
    payload = selection.model_dump(mode="json")
    payload["selected_epoch"] = 2
    payload["checkpoint"]["selected_epoch"] = 2  # type: ignore[index]

    with pytest.raises(ValidationError, match="earliest validation minimum"):
        M1SelectionRecord.model_validate(payload)

    wrong_training = _dataset("train", ("not-in-manifest",))
    with pytest.raises(M1ArtifactError, match="manifest train split"):
        write_m1_fit_artifacts(
            tmp_path,
            fit,
            materialization=materialization,
            training_dataset=wrong_training,
            validation_dataset=validation,
            training_source_revision="c" * 40,
            runtime=runtime,
        )


def test_artifact_tampering_and_atomic_write_failure_are_rejected(
    tmp_path: Path,
    artifact_context: tuple[
        DatasetMaterializationIndex,
        M1TensorDataset,
        M1TensorDataset,
        M1RuntimeEnvironment,
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization, _, _, runtime = artifact_context
    fit = _fit_result(17)
    reference = write_m1_checkpoint(
        tmp_path,
        fit,
        materialization=materialization,
        training_source_revision="c" * 40,
        runtime=runtime,
    )
    target = _artifact_path(tmp_path, reference.relative_path)
    original = target.read_bytes()
    corrupted = bytearray(original)
    corrupted[-2] ^= 1
    target.write_bytes(corrupted)

    with pytest.raises(M1ArtifactError, match="checksum"):
        read_m1_checkpoint(tmp_path, reference)

    target.write_bytes(original)
    changed_payload = reference.model_dump(mode="json")
    changed_payload["runtime"]["processor"] = "different"  # type: ignore[index]
    changed_reference = M1CheckpointReference.model_validate(changed_payload)
    with pytest.raises(M1ArtifactError, match="provenance"):
        read_m1_checkpoint(tmp_path, changed_reference)

    separate_root = tmp_path / "atomic"
    atomic_target = _artifact_path(separate_root, reference.relative_path)

    def fail_replace(source: object, destination: object) -> None:
        raise OSError("injected replace failure")

    monkeypatch.setattr(artifact_module.os, "replace", fail_replace)
    with pytest.raises(M1ArtifactError, match="write checkpoint"):
        write_m1_checkpoint(
            separate_root,
            fit,
            materialization=materialization,
            training_source_revision="c" * 40,
            runtime=runtime,
        )
    assert not atomic_target.exists()
    assert not tuple(atomic_target.parent.glob(".topolab-m1-checkpoint-*.tmp"))


def test_runtime_capture_hashes_lockfile(tmp_path: Path) -> None:
    lockfile = tmp_path / "uv.lock"
    lockfile.write_text("version = 1\n", encoding="utf-8")

    runtime = capture_m1_runtime(lockfile)

    assert runtime.lockfile_sha256 == hashlib.sha256(lockfile.read_bytes()).hexdigest()
    assert runtime.python_version
    assert runtime.numpy_version
    assert runtime.scipy_version
    assert runtime.torch_version
    assert runtime.safetensors_version
    assert runtime.torch_num_threads > 0
    assert runtime.torch_num_interop_threads > 0


def test_all_seed_runner_opens_only_fitting_splits(
    tmp_path: Path,
    artifact_context: tuple[
        DatasetMaterializationIndex,
        M1TensorDataset,
        M1TensorDataset,
        M1RuntimeEnvironment,
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization, training, validation, runtime = artifact_context
    requested_splits: list[str] = []
    fitted_seeds: list[int] = []

    def build(
        root: Path,
        index: DatasetMaterializationIndex,
        *,
        split: str,
    ) -> M1TensorDataset:
        requested_splits.append(split)
        return training if split == "train" else validation

    def fit(
        training_dataset: M1TensorDataset,
        validation_dataset: M1TensorDataset,
        *,
        seed: int,
    ) -> M1FitResult:
        fitted_seeds.append(seed)
        return _fit_result(seed)

    def write(
        root: Path,
        fit_result: M1FitResult,
        **kwargs: object,
    ) -> M1SelectionReference:
        digest = f"{fit_result.seed:064x}"
        return M1SelectionReference(
            manifest_sha256=materialization.manifest_sha256,
            seed=fit_result.seed,
            sha256=digest,
            byte_size=1,
            relative_path=(
                f"m1/selections/{materialization.manifest_sha256}/"
                f"{fit_result.seed}/{digest}.json"
            ),
        )

    monkeypatch.setattr(artifact_module, "build_m1_tensor_dataset", build)
    monkeypatch.setattr(artifact_module, "fit_m1_model", fit)
    monkeypatch.setattr(artifact_module, "write_m1_fit_artifacts", write)

    references = train_all_m1_seeds(
        tmp_path / "data",
        tmp_path / "artifacts",
        materialization,
        training_source_revision="c" * 40,
        runtime=runtime,
    )

    assert requested_splits == ["train", "validation"]
    assert fitted_seeds == list(M1_SEEDS)
    assert tuple(reference.seed for reference in references) == M1_SEEDS


def _fit_result(seed: int) -> M1FitResult:
    torch.manual_seed(seed)
    model = WarmStartCNN()
    state = tuple(
        (name, tensor.detach().clone())
        for name, tensor in sorted(model.state_dict().items())
    )
    history = tuple(
        M1EpochMetrics(
            epoch=epoch,
            mean_training_mse=0.2 + epoch / 1000.0,
            mean_validation_mse=0.1,
        )
        for epoch in range(1, 27)
    )
    return M1FitResult(
        seed=seed,
        history=history,
        selected_epoch=1,
        selected_validation_mse=0.1,
        stopped_early=True,
        duration_seconds=0.25,
        selected_state=state,
    )


def _dataset(split: str, case_ids: tuple[str, ...]) -> M1TensorDataset:
    count = len(case_ids)
    return M1TensorDataset(
        split=split,  # type: ignore[arg-type]
        case_ids=case_ids,
        inputs=torch.zeros((count, 10, 1, 1, 2), dtype=torch.float32),
        targets=torch.full((count, 1, 1, 1, 2), 0.5, dtype=torch.float32),
    )


def _label_reference(case_id: str) -> LabelArtifactReference:
    digest = hashlib.sha256(case_id.encode()).hexdigest()
    return LabelArtifactReference(
        case_id=case_id,
        generator_version="topolab.m0.generator.v1",
        source_revision="b" * 40,
        sha256=digest,
        byte_size=1,
        relative_path=f"labels/{case_id}/{digest}.json",
    )


def _runtime() -> M1RuntimeEnvironment:
    return M1RuntimeEnvironment(
        python_version="3.12.10",
        numpy_version="2.3.3",
        scipy_version="1.16.2",
        torch_version="2.14.0+cpu",
        safetensors_version="0.8.0",
        lockfile_sha256="a" * 64,
        platform_system="TestOS",
        platform_machine="test-machine",
        processor="test-processor",
        torch_num_threads=1,
        torch_num_interop_threads=1,
    )


def _environment() -> DatasetEnvironment:
    return DatasetEnvironment(
        python_version="3.12.10",
        numpy_version="2.3.3",
        scipy_version="1.16.2",
        lockfile_sha256="a" * 64,
    )


def _partition_cases() -> tuple[ExperimentCase, ...]:
    return (
        ExperimentCase.from_problem(_problem(volume_fraction=0.06)),
        ExperimentCase.from_problem(_problem(volume_fraction=0.18)),
        ExperimentCase.from_problem(_problem(volume_fraction=0.08)),
        ExperimentCase.from_problem(
            _problem(volume_fraction=0.06, load_direction="z")
        ),
    )


def _problem(
    *,
    volume_fraction: float,
    load_direction: str = "y",
) -> TopologyProblem:
    return TopologyProblem(
        mesh=MeshDefinition(
            element_counts=(2, 1, 1),
            lengths=(2.0, 1.0, 1.0),
        ),
        material=MaterialDefinition(
            solid_modulus=1000.0,
            minimum_modulus=1.0,
            poisson_ratio=0.3,
        ),
        supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
        loads=(
            PointLoadDefinition(
                node=11,
                direction=load_direction,  # type: ignore[arg-type]
                magnitude=-1.0,
            ),
        ),
        optimization=OptimizationDefinition(
            volume_fraction=volume_fraction,
            filter_radius=1.5,
            minimum_density=0.05,
            convergence_tolerance=0.01,
            max_iterations=60,
        ),
    )


def _artifact_path(root: Path, relative_path: str) -> Path:
    return root.joinpath(*PurePosixPath(relative_path).parts)
