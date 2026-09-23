import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

import topolab.learned_evaluation as learned_module
import topolab.m1_experiment as experiment_module
from topolab.baselines import (
    BaselineCaseResult,
    BaselineMetrics,
    BaselineTiming,
    NearestNeighborMetadata,
)
from topolab.dataset import DatasetEnvironment, DatasetManifest, DatasetSample
from topolab.experiment import ExperimentCase
from topolab.label_artifacts import LabelArtifactReference
from topolab.learned_evaluation import M1CaseResult, M1LearnedCandidate
from topolab.m1_experiment import (
    M1EvaluationCaseRecord,
    M1EvaluationContext,
    M1EvaluationIndex,
    M1ExperimentError,
    build_m1_evaluation_id,
    canonical_m1_evaluation_index_bytes,
    compute_m1_experiment_statistics,
    m1_evaluation_index_path,
    read_m1_evaluation_index,
    run_m1_experiment,
    write_m1_evaluation_index,
)
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
from topolab.training import M1_SEEDS, WarmStartCNN
from topolab.training_artifacts import (
    M1CheckpointReference,
    M1RuntimeEnvironment,
    M1SelectionReference,
)


def test_evaluation_index_is_canonical_append_only_and_context_bound(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization = _materialization()
    context = _context(materialization, monkeypatch)
    test_sample = _sample(materialization, "test")
    started = M1EvaluationIndex.start(context)
    target = write_m1_evaluation_index(
        tmp_path,
        started,
        materialization=materialization,
    )
    record = _record(test_sample, context)
    progressed = M1EvaluationIndex(
        state="in_progress",
        context=context,
        entries=(record,),
    )
    write_m1_evaluation_index(
        tmp_path,
        progressed,
        materialization=materialization,
    )

    restored = read_m1_evaluation_index(
        tmp_path,
        context,
        materialization=materialization,
    )

    assert restored == progressed
    assert target == m1_evaluation_index_path(tmp_path, context)
    assert target.name == f"{build_m1_evaluation_id(context)}.json"
    assert target.read_bytes() == canonical_m1_evaluation_index_bytes(progressed)

    atomic_root = tmp_path / "atomic"
    atomic_target = m1_evaluation_index_path(atomic_root, context)

    def fail_replace(source: object, destination: object) -> None:
        raise OSError("injected replace failure")

    with monkeypatch.context() as atomic_patch:
        atomic_patch.setattr(experiment_module.os, "replace", fail_replace)
        with pytest.raises(M1ExperimentError, match="could not write"):
            write_m1_evaluation_index(
                atomic_root,
                started,
                materialization=materialization,
            )
    assert not atomic_target.exists()
    assert not tuple(atomic_target.parent.glob(".topolab-m1-evaluation-*.tmp"))

    changed = progressed.model_dump(mode="json")
    changed["entries"][0]["baselines"][0]["timing"]["setup_seconds"] = 1.0  # type: ignore[index]
    changed["entries"][0]["baselines"][0]["timing"]["end_to_end_seconds"] = 3.0  # type: ignore[index]
    with pytest.raises(M1ExperimentError, match="preserve recorded outcomes"):
        write_m1_evaluation_index(
            tmp_path,
            M1EvaluationIndex.model_validate(changed),
            materialization=materialization,
        )

    target.write_text(progressed.model_dump_json(indent=2), encoding="utf-8")
    with pytest.raises(M1ExperimentError, match="canonical JSON"):
        read_m1_evaluation_index(
            tmp_path,
            context,
            materialization=materialization,
        )


def test_runner_checkpoints_each_case_and_resumes_without_query_labels(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization = _materialization()
    context = _context(materialization, monkeypatch)
    candidates = _candidates(context, monkeypatch)
    held_out = tuple(
        sample
        for sample in materialization.manifest.samples
        if sample.split in ("test", "ood")
    )
    baseline_calls: list[str] = []
    build_calls: list[str] = []
    fail_case_id = held_out[1].case.case_id
    fail_once = True

    def build_index(*args: object, **kwargs: object) -> object:
        build_calls.append("build")
        return object()

    def baselines(sample: DatasetSample, index: object) -> tuple[
        BaselineCaseResult,
        BaselineCaseResult,
        BaselineCaseResult,
    ]:
        nonlocal fail_once
        baseline_calls.append(sample.case.case_id)
        if sample.case.case_id == fail_case_id and fail_once:
            fail_once = False
            raise RuntimeError("injected interruption")
        return _baseline_results(sample)

    def learned(
        sample: DatasetSample,
        candidate: M1LearnedCandidate,
        uniform: BaselineCaseResult,
    ) -> M1CaseResult:
        return _learned_result(
            sample,
            context,
            seed=candidate.seed,
            seconds=1.0,
        )

    monkeypatch.setattr(experiment_module, "build_nearest_neighbor_index", build_index)
    monkeypatch.setattr(experiment_module, "run_fixed_baselines", baselines)
    monkeypatch.setattr(experiment_module, "run_learned_warm_start", learned)

    with pytest.raises(RuntimeError, match="injected interruption"):
        run_m1_experiment(
            tmp_path / "data",
            tmp_path / "output",
            materialization,
            context,
            candidates,
        )

    checkpoint = read_m1_evaluation_index(
        tmp_path / "output",
        context,
        materialization=materialization,
    )
    assert checkpoint.state == "in_progress"
    assert tuple(entry.case_id for entry in checkpoint.entries) == (
        held_out[0].case.case_id,
    )

    complete = run_m1_experiment(
        tmp_path / "data",
        tmp_path / "output",
        materialization,
        context,
        candidates,
    )

    assert complete.state == "complete"
    assert len(complete.entries) == len(held_out)
    assert baseline_calls.count(held_out[0].case.case_id) == 1
    assert build_calls == ["build", "build"]


def test_statistics_retain_all_cases_and_seed_clusters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization = _materialization()
    context = _context(materialization, monkeypatch)
    entries = tuple(
        _record(sample, context, fail_last_seed=True)
        for sample in materialization.manifest.samples
        if sample.split in ("test", "ood")
    )
    index = M1EvaluationIndex(
        state="complete",
        context=context,
        entries=entries,
    )

    statistics = compute_m1_experiment_statistics(index, materialization)
    repeated = compute_m1_experiment_statistics(index, materialization)

    assert repeated == statistics
    assert tuple(summary.split for summary in statistics.splits) == ("test", "ood")
    for summary in statistics.splits:
        assert summary.case_count == 1
        assert tuple((item.method, item.seed) for item in summary.methods) == (
            ("uniform", None),
            ("physics_heuristic", None),
            ("nearest_neighbor", None),
            *(("learned", seed) for seed in M1_SEEDS),
        )
        assert summary.methods[0].mean_time_ratio_to_uniform == 1.0
        assert summary.methods[1].mean_time_ratio_to_uniform == 1.5
        assert summary.methods[2].mean_time_ratio_to_uniform == 0.5
        assert summary.learned_aggregate.observation_count == 5
        assert summary.learned_aggregate.mean_time_ratio_to_uniform == 1.0
        assert summary.learned_aggregate.confidence_interval_95_lower == 1.0
        assert summary.learned_aggregate.confidence_interval_95_upper == 1.0
        assert summary.learned_aggregate.failure_rate == 0.2
        assert summary.learned_aggregate.fallback_rate == 0.2


def test_complete_index_requires_every_held_out_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    materialization = _materialization()
    context = _context(materialization, monkeypatch)
    only_test = _record(_sample(materialization, "test"), context)
    incomplete = M1EvaluationIndex(
        state="complete",
        context=context,
        entries=(only_test,),
    )

    with pytest.raises(M1ExperimentError, match="every held-out case"):
        write_m1_evaluation_index(
            tmp_path,
            incomplete,
            materialization=materialization,
        )

    payload = context.model_dump(mode="json")
    payload["selections"] = payload["selections"][:-1]
    with pytest.raises(ValidationError):
        M1EvaluationContext.model_validate(payload)

    changed = incomplete.model_dump(mode="json")
    changed_digest = "e" * 64
    changed["entries"][0]["learned"][0]["checkpoint"]["sha256"] = changed_digest  # type: ignore[index]
    changed["entries"][0]["learned"][0]["checkpoint"]["relative_path"] = (  # type: ignore[index]
        f"m1/checkpoints/{context.manifest_sha256}/17/"
        f"{changed_digest}.safetensors"
    )
    with pytest.raises(ValidationError, match="evaluation checkpoints"):
        M1EvaluationIndex.model_validate(changed)


def _record(
    sample: DatasetSample,
    context: M1EvaluationContext,
    *,
    fail_last_seed: bool = False,
) -> M1EvaluationCaseRecord:
    seconds = (1.0, 1.5, 2.0, 2.5, 3.0)
    return M1EvaluationCaseRecord(
        case_id=sample.case.case_id,
        split=sample.split,  # type: ignore[arg-type]
        baselines=_baseline_results(sample),
        learned=tuple(  # type: ignore[arg-type]
            _learned_result(
                sample,
                context,
                seed=seed,
                seconds=seconds[index],
                failed=fail_last_seed and index == len(M1_SEEDS) - 1,
            )
            for index, seed in enumerate(M1_SEEDS)
        ),
    )


def _baseline_results(sample: DatasetSample) -> tuple[
    BaselineCaseResult,
    BaselineCaseResult,
    BaselineCaseResult,
]:
    return (
        _baseline_result(sample, "uniform", 2.0),
        _baseline_result(sample, "physics_heuristic", 3.0),
        _baseline_result(sample, "nearest_neighbor", 1.0),
    )


def _baseline_result(
    sample: DatasetSample,
    method: str,
    seconds: float,
) -> BaselineCaseResult:
    metrics = BaselineMetrics(
        iterations=10,
        final_compliance=100.0,
        physical_volume_error=1e-6,
    )
    return BaselineCaseResult(
        case_id=sample.case.case_id,
        split=sample.split,
        method=method,  # type: ignore[arg-type]
        succeeded=True,
        fallback_used=False,
        timing=BaselineTiming.from_phases(refinement=seconds),
        candidate=metrics,
        operational=metrics,
        uniform_reference_compliance=100.0,
        nearest_neighbor=(
            NearestNeighborMetadata(
                matched_case_id="tlcase-v1-" + "f" * 64,
                candidate_count=1,
                index_size_bytes=1,
            )
            if method == "nearest_neighbor"
            else None
        ),
    )


def _learned_result(
    sample: DatasetSample,
    context: M1EvaluationContext,
    *,
    seed: int,
    seconds: float,
    failed: bool = False,
) -> M1CaseResult:
    selection = next(reference for reference in context.selections if reference.seed == seed)
    checkpoint = _checkpoint(context, seed)
    metrics = BaselineMetrics(
        iterations=8,
        final_compliance=100.0,
        physical_volume_error=1e-6,
    )
    return M1CaseResult(
        case_id=sample.case.case_id,
        split=sample.split,
        seed=seed,
        selection=selection,
        checkpoint=checkpoint,
        succeeded=not failed,
        failure_code="quality_error" if failed else None,
        fallback_used=failed,
        timing=(
            BaselineTiming.from_phases(refinement=1.0, fallback=seconds - 1.0)
            if failed
            else BaselineTiming.from_phases(refinement=seconds)
        ),
        candidate=None if failed else metrics,
        operational=metrics,
        uniform_reference_compliance=100.0,
    )


def _context(
    materialization: DatasetMaterializationIndex,
    monkeypatch: pytest.MonkeyPatch,
) -> M1EvaluationContext:
    monkeypatch.setattr(
        experiment_module,
        "M1_DATA_MANIFEST_SHA256",
        materialization.manifest_sha256,
    )
    return M1EvaluationContext(
        manifest_sha256=materialization.manifest_sha256,
        evaluation_source_revision="c" * 40,
        runtime=_runtime(),
        selections=_selection_references(materialization.manifest_sha256),
        checkpoints=_checkpoint_references(materialization.manifest_sha256),
    )


def _candidates(
    context: M1EvaluationContext,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    M1LearnedCandidate,
    M1LearnedCandidate,
    M1LearnedCandidate,
    M1LearnedCandidate,
    M1LearnedCandidate,
]:
    monkeypatch.setattr(
        learned_module,
        "M1_DATA_MANIFEST_SHA256",
        context.manifest_sha256,
    )
    return tuple(  # type: ignore[return-value]
        M1LearnedCandidate(
            selection=selection,
            checkpoint=_checkpoint(context, selection.seed),
            model=WarmStartCNN(),
        )
        for selection in context.selections
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


def _checkpoint(
    context: M1EvaluationContext,
    seed: int,
) -> M1CheckpointReference:
    return next(reference for reference in context.checkpoints if reference.seed == seed)


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
        training_source_revision="a" * 40,
        runtime=_runtime(),
        seed=seed,
        selected_epoch=1,
        sha256=digest,
        byte_size=1,
        relative_path=(
            f"m1/checkpoints/{manifest_sha256}/{seed}/{digest}.safetensors"
        ),
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


def _materialization() -> DatasetMaterializationIndex:
    manifest = DatasetManifest.from_cases(
        _partition_cases(),
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


def _sample(
    materialization: DatasetMaterializationIndex,
    split: str,
) -> DatasetSample:
    return next(
        sample for sample in materialization.manifest.samples if sample.split == split
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
