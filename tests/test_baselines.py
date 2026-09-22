from pathlib import Path

import numpy as np
import pytest
from pytest import TempPathFactory

import topolab.baselines as baselines_module
from topolab.baselines import (
    BASELINE_RUNNER_VERSION,
    BaselineCaseResult,
    BaselineEvaluationError,
    NearestNeighborIndex,
    build_nearest_neighbor_index,
    run_fixed_baselines,
)
from topolab.dataset import DatasetEnvironment, DatasetManifest
from topolab.experiment import ExperimentCase, encode_case
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


@pytest.fixture(scope="module")
def materialized_dataset(
    tmp_path_factory: TempPathFactory,
) -> tuple[Path, DatasetManifest, DatasetMaterializationIndex, NearestNeighborIndex]:
    root = tmp_path_factory.mktemp("baseline-data")
    manifest = DatasetManifest.from_cases(
        _partition_cases(),
        source_revision="b" * 40,
        environment=_environment(),
    )
    materialization = materialize_dataset(root, manifest)
    nearest_neighbors = build_nearest_neighbor_index(root, materialization)
    return root, manifest, materialization, nearest_neighbors


def test_nearest_neighbor_index_loads_only_training_labels(
    materialized_dataset: tuple[
        Path,
        DatasetManifest,
        DatasetMaterializationIndex,
        NearestNeighborIndex,
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, manifest, materialization, expected = materialized_dataset
    real_read = baselines_module.read_label_artifact
    read_case_ids: list[str] = []

    def read_training_label(
        root_path: Path,
        reference: LabelArtifactReference,
    ) -> LabelRecord:
        read_case_ids.append(reference.case_id)
        return real_read(root_path, reference)

    monkeypatch.setattr(
        baselines_module,
        "read_label_artifact",
        read_training_label,
    )
    rebuilt = build_nearest_neighbor_index(root, materialization)
    training_ids = tuple(
        sample.case.case_id for sample in manifest.samples if sample.split == "train"
    )

    assert rebuilt.case_ids == expected.case_ids == training_ids
    assert tuple(read_case_ids) == training_ids
    assert rebuilt.candidate_count == len(training_ids)
    assert rebuilt.stored_size_bytes == (
        rebuilt.input_tensors.nbytes
        + rebuilt.design_tensors.nbytes
        + sum(len(case_id.encode("utf-8")) for case_id in training_ids)
    )
    assert not rebuilt.input_tensors.flags.writeable
    assert not rebuilt.design_tensors.flags.writeable


def test_nearest_neighbor_query_breaks_exact_ties_by_case_id() -> None:
    query = ExperimentCase.from_problem(_problem(volume_fraction=0.18))
    query_tensor = encode_case(query).input_tensor
    first_id = "tlcase-v1-" + "a" * 64
    second_id = "tlcase-v1-" + "b" * 64
    first_design = np.full((1, 1, 1, 2), 0.2, dtype=np.float32)
    second_design = np.full((1, 1, 1, 2), 0.8, dtype=np.float32)
    nearest_neighbors = NearestNeighborIndex(
        case_ids=(first_id, second_id),
        input_tensors=np.stack((query_tensor, query_tensor)),
        design_tensors=np.stack((first_design, second_design)),
    )

    match = nearest_neighbors.query(query)

    assert match.case_id == first_id
    assert match.mean_squared_distance == 0.0
    np.testing.assert_array_equal(match.design_density, first_design)


def test_fixed_baselines_use_one_solver_contract_and_record_cost_and_quality(
    materialized_dataset: tuple[
        Path,
        DatasetManifest,
        DatasetMaterializationIndex,
        NearestNeighborIndex,
    ],
) -> None:
    _, manifest, _, nearest_neighbors = materialized_dataset
    sample = next(sample for sample in manifest.samples if sample.split == "validation")

    results = run_fixed_baselines(sample, nearest_neighbors)

    assert tuple(result.method for result in results) == (
        "uniform",
        "physics_heuristic",
        "nearest_neighbor",
    )
    uniform, heuristic, nearest = results
    restored = BaselineCaseResult.model_validate_json(nearest.model_dump_json())
    assert all(result.runner_version == BASELINE_RUNNER_VERSION for result in results)
    assert all(result.case_id == sample.case.case_id for result in results)
    assert all(result.split == "validation" for result in results)
    assert uniform.succeeded, uniform.model_dump()
    assert nearest.succeeded, nearest.model_dump()
    assert all(result.operational.iterations > 0 for result in results)
    assert all(result.operational.physical_volume_error <= 5e-3 for result in results)
    assert all(
        result.timing.end_to_end_seconds
        == result.timing.setup_seconds
        + result.timing.projection_seconds
        + result.timing.refinement_seconds
        + result.timing.fallback_seconds
        for result in results
    )
    assert heuristic.timing.setup_seconds > 0.0
    assert not heuristic.succeeded
    assert heuristic.failure_code == "quality_error"
    assert heuristic.fallback_used
    assert heuristic.candidate is not None
    assert heuristic.candidate.final_compliance > (
        1.001 * uniform.operational.final_compliance
    )
    assert nearest.nearest_neighbor is not None
    assert nearest.nearest_neighbor.matched_case_id == nearest_neighbors.case_ids[0]
    assert nearest.nearest_neighbor.candidate_count == nearest_neighbors.candidate_count
    assert nearest.nearest_neighbor.index_size_bytes == nearest_neighbors.stored_size_bytes
    assert restored == nearest
    assert nearest.operational.final_compliance <= (
        1.001 * uniform.operational.final_compliance
    )


def test_nonuniform_setup_failure_runs_and_charges_uniform_fallback(
    materialized_dataset: tuple[
        Path,
        DatasetManifest,
        DatasetMaterializationIndex,
        NearestNeighborIndex,
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, manifest, _, nearest_neighbors = materialized_dataset
    sample = next(sample for sample in manifest.samples if sample.split == "validation")

    def fail_setup(case: ExperimentCase) -> np.ndarray:
        raise ValueError("injected heuristic failure")

    monkeypatch.setattr(
        baselines_module,
        "_physics_heuristic_raw_density",
        fail_setup,
    )
    uniform, heuristic, nearest = run_fixed_baselines(sample, nearest_neighbors)

    assert uniform.succeeded
    assert not heuristic.succeeded
    assert heuristic.failure_code == "setup_error"
    assert heuristic.fallback_used
    assert heuristic.timing.fallback_seconds > 0.0
    assert heuristic.candidate is None
    assert heuristic.operational.final_compliance == pytest.approx(
        uniform.operational.final_compliance,
        rel=1e-12,
    )
    assert nearest.succeeded


def test_runner_rejects_training_queries_and_invalid_materialization(
    materialized_dataset: tuple[
        Path,
        DatasetManifest,
        DatasetMaterializationIndex,
        NearestNeighborIndex,
    ],
    tmp_path: Path,
) -> None:
    _, manifest, _, nearest_neighbors = materialized_dataset
    training_sample = next(sample for sample in manifest.samples if sample.split == "train")

    with pytest.raises(ValueError, match="must not be training"):
        run_fixed_baselines(training_sample, nearest_neighbors)
    with pytest.raises(BaselineEvaluationError, match="fully materialized"):
        build_nearest_neighbor_index(
            tmp_path,
            DatasetMaterializationIndex.start(manifest),
        )

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
    with pytest.raises(BaselineEvaluationError, match="failed cases"):
        build_nearest_neighbor_index(tmp_path, failed)


def test_uniform_reference_failure_is_a_dataset_evaluation_error(
    materialized_dataset: tuple[
        Path,
        DatasetManifest,
        DatasetMaterializationIndex,
        NearestNeighborIndex,
    ],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, manifest, _, nearest_neighbors = materialized_dataset
    sample = next(sample for sample in manifest.samples if sample.split == "validation")

    def fail_solver(problem: TopologyProblem) -> object:
        raise RuntimeError("injected solver failure")

    monkeypatch.setattr(baselines_module, "solve_problem", fail_solver)
    with pytest.raises(BaselineEvaluationError, match="uniform reference"):
        run_fixed_baselines(sample, nearest_neighbors)


def _partition_cases() -> tuple[ExperimentCase, ...]:
    return (
        ExperimentCase.from_problem(_problem(volume_fraction=0.06)),
        ExperimentCase.from_problem(_problem(volume_fraction=0.18)),
        ExperimentCase.from_problem(_problem(volume_fraction=0.08)),
        ExperimentCase.from_problem(
            _problem(volume_fraction=0.06, load_direction="z")
        ),
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
