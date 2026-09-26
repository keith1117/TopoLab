from collections.abc import Iterator
from pathlib import Path

import pytest
import torch
from pydantic import ValidationError
from pytest import TempPathFactory
from torch.utils.data import DataLoader

import topolab.training as training_module
from topolab.dataset import DatasetEnvironment, DatasetManifest
from topolab.experiment import ExperimentCase
from topolab.label_artifacts import LabelArtifactReference
from topolab.labels import LabelRecord
from topolab.materialization import (
    DatasetMaterializationIndex,
    MaterializationFailure,
    build_manifest_sha256,
    materialize_dataset,
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
    M1_MODEL_PARAMETER_COUNT,
    M1_SEEDS,
    M1_TRAINING_CONTRACT,
    M1DatasetError,
    M1TensorDataset,
    M1TrainingContract,
    M1TrainingError,
    WarmStartCNN,
    _fit_m1_model,
    build_m1_tensor_dataset,
    design_density_mse,
)


@pytest.fixture(scope="module")
def materialized_dataset(
    tmp_path_factory: TempPathFactory,
) -> tuple[Path, DatasetManifest, DatasetMaterializationIndex]:
    root = tmp_path_factory.mktemp("m1-data")
    manifest = DatasetManifest.from_cases(
        _partition_cases(),
        source_revision="b" * 40,
        environment=_environment(),
    )
    materialization = materialize_dataset(root, manifest)
    return root, manifest, materialization


def test_m1_training_contract_is_frozen_and_serializable() -> None:
    restored = M1TrainingContract.model_validate_json(
        M1_TRAINING_CONTRACT.model_dump_json()
    )

    assert restored == M1_TRAINING_CONTRACT
    assert restored.seeds == M1_SEEDS
    assert restored.hyperparameter_configurations == 1
    assert restored.checkpoint_metric == "mean_validation_design_density_mse"
    assert restored.checkpoint_tie_break == "earliest_epoch"

    payload = restored.model_dump(mode="json")
    payload["batch_size"] = 16
    with pytest.raises(ValidationError):
        M1TrainingContract.model_validate(payload)

    payload = restored.model_dump(mode="json")
    payload["seeds"] = [17, 29, 43]
    with pytest.raises(ValidationError, match="seed sequence"):
        M1TrainingContract.model_validate(payload)


def test_warm_start_cnn_has_frozen_shape_range_and_parameter_count() -> None:
    torch.manual_seed(17)
    model = WarmStartCNN()
    inputs = torch.zeros((2, 10, 3, 6, 12), dtype=torch.float32)

    outputs = model(inputs)

    assert outputs.shape == (2, 1, 3, 6, 12)
    assert outputs.dtype == torch.float32
    assert torch.all(outputs >= 0.0)
    assert torch.all(outputs <= 1.0)
    assert sum(parameter.numel() for parameter in model.parameters()) == (
        M1_MODEL_PARAMETER_COUNT
    )

    with pytest.raises(ValueError, match="shape"):
        model(torch.zeros((2, 9, 3, 6, 12), dtype=torch.float32))
    with pytest.raises(TypeError, match="float32"):
        model(torch.zeros((2, 10, 3, 6, 12), dtype=torch.float64))


def test_design_density_mse_is_elementwise_mean_and_differentiable() -> None:
    prediction = torch.tensor([0.2, 0.8], dtype=torch.float32, requires_grad=True)
    target = torch.tensor([0.4, 0.4], dtype=torch.float32)

    loss = design_density_mse(prediction, target)
    loss.backward()

    assert loss.item() == pytest.approx(0.1, abs=1e-7)
    assert prediction.grad is not None
    torch.testing.assert_close(
        prediction.grad,
        torch.tensor([-0.2, 0.4], dtype=torch.float32),
    )

    with pytest.raises(ValueError, match="identical shapes"):
        design_density_mse(prediction, target.reshape(1, 2))
    with pytest.raises(TypeError, match="float32"):
        design_density_mse(prediction.detach().double(), target.double())


@pytest.fixture
def single_torch_intraop_thread() -> Iterator[None]:
    """Match the one-thread environment of the frozen M1 production fitting."""

    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    try:
        yield
    finally:
        torch.set_num_threads(previous)


def test_short_fitting_loop_is_repeatable_and_restores_rng_state(
    single_torch_intraop_thread: None,
) -> None:
    training = _tensor_dataset("train", ("case-a", "case-b"), offset=0.0)
    validation = _tensor_dataset("validation", ("case-c",), offset=0.1)
    torch.manual_seed(999)
    state_before = torch.get_rng_state().clone()
    deterministic_before = torch.are_deterministic_algorithms_enabled()

    first = _fit_m1_model(
        training,
        validation,
        seed=17,
        max_epochs=3,
        early_stopping_patience=2,
    )
    second = _fit_m1_model(
        training,
        validation,
        seed=17,
        max_epochs=3,
        early_stopping_patience=2,
    )

    assert first.history == second.history
    assert first.selected_epoch == second.selected_epoch
    assert first.selected_validation_mse == second.selected_validation_mse
    assert tuple(name for name, _ in first.selected_state) == tuple(
        name for name, _ in second.selected_state
    )
    for (_, first_tensor), (_, second_tensor) in zip(
        first.selected_state,
        second.selected_state,
        strict=True,
    ):
        torch.testing.assert_close(first_tensor, second_tensor, rtol=0.0, atol=0.0)
    best = min(
        first.history,
        key=lambda metrics: (metrics.mean_validation_mse, metrics.epoch),
    )
    assert first.selected_epoch == best.epoch
    assert first.selected_validation_mse == best.mean_validation_mse
    assert torch.equal(torch.get_rng_state(), state_before)
    assert torch.are_deterministic_algorithms_enabled() is deterministic_before


def test_fitting_loop_rejects_wrong_partitions_and_unfrozen_seed() -> None:
    training = _tensor_dataset("train", ("case-a",), offset=0.0)
    validation = _tensor_dataset("validation", ("case-b",), offset=0.1)

    with pytest.raises(M1TrainingError, match="seed sequence"):
        _fit_m1_model(
            training,
            validation,
            seed=1,
            max_epochs=1,
            early_stopping_patience=1,
        )
    with pytest.raises(M1TrainingError, match="train split"):
        _fit_m1_model(
            validation,
            validation,
            seed=17,
            max_epochs=1,
            early_stopping_patience=1,
        )


@pytest.mark.parametrize("split", ["train", "validation"])
def test_m1_dataset_reads_only_requested_fitting_partition(
    split: str,
    materialized_dataset: tuple[Path, DatasetManifest, DatasetMaterializationIndex],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, manifest, materialization = materialized_dataset
    real_read = training_module.read_label_artifact
    read_case_ids: list[str] = []

    def read_selected_label(
        root_path: Path,
        reference: LabelArtifactReference,
    ) -> LabelRecord:
        read_case_ids.append(reference.case_id)
        return real_read(root_path, reference)

    monkeypatch.setattr(training_module, "read_label_artifact", read_selected_label)
    dataset = build_m1_tensor_dataset(
        root,
        materialization,
        split=split,  # type: ignore[arg-type]
    )
    expected_ids = tuple(
        sample.case.case_id for sample in manifest.samples if sample.split == split
    )
    inputs, targets = dataset[0]

    assert dataset.split == split
    assert dataset.case_ids == expected_ids
    assert tuple(read_case_ids) == expected_ids
    assert len(dataset) == len(expected_ids)
    assert inputs.shape == (10, 1, 1, 2)
    assert targets.shape == (1, 1, 1, 2)
    assert inputs.dtype == targets.dtype == torch.float32
    assert inputs.is_contiguous()
    assert targets.is_contiguous()

    batch_inputs, batch_targets = next(
        iter(DataLoader(dataset, batch_size=8, shuffle=False, num_workers=0))
    )
    assert batch_inputs.shape == (len(dataset), 10, 1, 1, 2)
    assert batch_targets.shape == (len(dataset), 1, 1, 1, 2)


def test_m1_dataset_rejects_held_out_splits_and_invalid_materialization(
    materialized_dataset: tuple[Path, DatasetManifest, DatasetMaterializationIndex],
    tmp_path: Path,
) -> None:
    _, manifest, _ = materialized_dataset
    started = DatasetMaterializationIndex.start(manifest)

    with pytest.raises(ValueError, match="train or validation"):
        build_m1_tensor_dataset(tmp_path, started, split="test")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="train or validation"):
        build_m1_tensor_dataset(tmp_path, started, split="ood")  # type: ignore[arg-type]
    with pytest.raises(M1DatasetError, match="fully materialized"):
        build_m1_tensor_dataset(tmp_path, started, split="train")

    failed = DatasetMaterializationIndex(
        state="complete",
        manifest_sha256=build_manifest_sha256(manifest),
        manifest=manifest,
        entries=tuple(
            MaterializationFailure(
                case_id=sample.case.case_id,
                split=sample.split,
                failure_code="label_generation_error",
            )
            for sample in manifest.samples
        ),
    )
    with pytest.raises(M1DatasetError, match="failed cases"):
        build_m1_tensor_dataset(tmp_path, failed, split="train")


def _partition_cases() -> tuple[ExperimentCase, ...]:
    return (
        ExperimentCase.from_problem(_problem(volume_fraction=0.06)),
        ExperimentCase.from_problem(_problem(volume_fraction=0.18)),
        ExperimentCase.from_problem(_problem(volume_fraction=0.08)),
        ExperimentCase.from_problem(
            _problem(volume_fraction=0.06, load_direction="z")
        ),
    )


def _tensor_dataset(
    split: str,
    case_ids: tuple[str, ...],
    *,
    offset: float,
) -> M1TensorDataset:
    inputs = torch.linspace(
        0.0 + offset,
        1.0 + offset,
        steps=len(case_ids) * 10 * 2,
        dtype=torch.float32,
    ).reshape(len(case_ids), 10, 1, 1, 2)
    targets = torch.linspace(
        0.2 + offset,
        0.8 + offset,
        steps=len(case_ids) * 2,
        dtype=torch.float32,
    ).reshape(len(case_ids), 1, 1, 1, 2)
    return M1TensorDataset(
        split=split,  # type: ignore[arg-type]
        case_ids=case_ids,
        inputs=inputs,
        targets=targets,
    )


def _environment() -> DatasetEnvironment:
    return DatasetEnvironment(
        python_version="3.12.10",
        numpy_version="2.3.3",
        scipy_version="1.16.2",
        lockfile_sha256="a" * 64,
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
