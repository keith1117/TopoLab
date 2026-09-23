import math

import pytest
import torch
from pydantic import ValidationError
from torch import Tensor, nn

import topolab.learned_evaluation as evaluation_module
from topolab.baselines import run_uniform_baseline
from topolab.dataset import DatasetEnvironment, DatasetManifest, DatasetSample
from topolab.experiment import ExperimentCase
from topolab.learned_evaluation import (
    M1_EVALUATION_VERSION,
    M1CaseResult,
    M1EvaluationError,
    M1LearnedCandidate,
    run_learned_warm_start,
)
from topolab.problem import (
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)
from topolab.training import M1_DATA_MANIFEST_SHA256, WarmStartCNN
from topolab.training_artifacts import (
    M1CheckpointReference,
    M1RuntimeEnvironment,
    M1SelectionReference,
)


def test_learned_candidate_infers_projects_refines_and_records_cost() -> None:
    sample = _sample("validation")
    candidate = _candidate(sample.case.problem.optimization.volume_fraction)
    uniform = run_uniform_baseline(sample)

    result = run_learned_warm_start(sample, candidate, uniform)
    restored = M1CaseResult.model_validate_json(result.model_dump_json())

    assert result.evaluation_version == M1_EVALUATION_VERSION
    assert result.case_id == sample.case.case_id
    assert result.split == "validation"
    assert result.seed == 17
    assert result.selection == candidate.selection
    assert result.checkpoint == candidate.checkpoint
    assert result.succeeded
    assert not result.fallback_used
    assert result.failure_code is None
    assert result.candidate == result.operational
    assert result.operational.iterations == uniform.operational.iterations
    assert result.operational.final_compliance <= (
        1.001 * uniform.operational.final_compliance
    )
    assert result.operational.physical_volume_error <= 5e-3
    assert result.timing.setup_seconds > 0.0
    assert result.timing.projection_seconds > 0.0
    assert result.timing.refinement_seconds > 0.0
    assert result.timing.fallback_seconds == 0.0
    assert result.timing.end_to_end_seconds == (
        result.timing.setup_seconds
        + result.timing.projection_seconds
        + result.timing.refinement_seconds
    )
    assert restored == result


def test_invalid_model_output_runs_and_charges_uniform_fallback() -> None:
    sample = _sample("validation")
    candidate = _candidate(
        sample.case.problem.optimization.volume_fraction,
        model=_FailingWarmStartCNN(),
    )
    uniform = run_uniform_baseline(sample)

    result = run_learned_warm_start(sample, candidate, uniform)

    assert not result.succeeded
    assert result.failure_code == "setup_error"
    assert result.fallback_used
    assert result.candidate is None
    assert result.timing.setup_seconds > 0.0
    assert result.timing.projection_seconds == 0.0
    assert result.timing.refinement_seconds == 0.0
    assert result.timing.fallback_seconds > 0.0
    assert result.operational.final_compliance == pytest.approx(
        uniform.operational.final_compliance,
        rel=1e-12,
    )
    assert result.timing.end_to_end_seconds == (
        result.timing.setup_seconds + result.timing.fallback_seconds
    )


def test_projection_and_quality_failures_remain_failed_after_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sample = _sample("validation")
    candidate = _candidate(sample.case.problem.optimization.volume_fraction)
    uniform = run_uniform_baseline(sample)

    def fail_projection(*args: object, **kwargs: object) -> object:
        raise ValueError("injected projection failure")

    monkeypatch.setattr(
        evaluation_module,
        "project_design_density",
        fail_projection,
    )
    projection_failure = run_learned_warm_start(sample, candidate, uniform)

    assert not projection_failure.succeeded
    assert projection_failure.failure_code == "projection_error"
    assert projection_failure.fallback_used
    assert projection_failure.candidate is None
    assert projection_failure.timing.fallback_seconds > 0.0

    monkeypatch.undo()

    def fail_quality(*args: object, **kwargs: object) -> object:
        raise RuntimeError("injected quality failure")

    monkeypatch.setattr(
        evaluation_module,
        "validate_refinement_quality",
        fail_quality,
    )
    quality_failure = run_learned_warm_start(sample, candidate, uniform)

    assert not quality_failure.succeeded
    assert quality_failure.failure_code == "quality_error"
    assert quality_failure.fallback_used
    assert quality_failure.candidate is not None
    assert quality_failure.timing.refinement_seconds > 0.0
    assert quality_failure.timing.fallback_seconds > 0.0


def test_learned_evaluation_rejects_training_and_wrong_uniform_reference() -> None:
    training = _sample("train")
    validation = _sample("validation")
    candidate = _candidate(validation.case.problem.optimization.volume_fraction)
    validation_uniform = run_uniform_baseline(validation)

    with pytest.raises(ValueError, match="must not be training"):
        run_learned_warm_start(training, candidate, validation_uniform)

    ood = _sample("ood")
    wrong_reference = run_uniform_baseline(ood)
    with pytest.raises(M1EvaluationError, match="matching successful uniform"):
        run_learned_warm_start(validation, candidate, wrong_reference)


def test_result_contract_rejects_seed_and_fallback_inconsistency() -> None:
    sample = _sample("validation")
    candidate = _candidate(sample.case.problem.optimization.volume_fraction)
    uniform = run_uniform_baseline(sample)
    result = run_learned_warm_start(sample, candidate, uniform)
    payload = result.model_dump(mode="json")
    payload["seed"] = 29

    with pytest.raises(ValidationError, match="result seed"):
        M1CaseResult.model_validate(payload)

    payload = result.model_dump(mode="json")
    payload["succeeded"] = False
    with pytest.raises(ValidationError, match="must record fallback"):
        M1CaseResult.model_validate(payload)


class _FailingWarmStartCNN(WarmStartCNN):
    def forward(self, inputs: Tensor) -> Tensor:
        raise RuntimeError("injected inference failure")


def _candidate(
    volume_fraction: float,
    *,
    model: WarmStartCNN | None = None,
) -> M1LearnedCandidate:
    if model is None:
        model = WarmStartCNN()
        with torch.no_grad():
            for parameter in model.parameters():
                parameter.zero_()
            final = model.network[4]
            assert isinstance(final, nn.Conv3d)
            final.bias.fill_(math.log(volume_fraction / (1.0 - volume_fraction)))
    manifest_sha256 = M1_DATA_MANIFEST_SHA256
    checkpoint_sha256 = "e" * 64
    selection_sha256 = "f" * 64
    runtime = _runtime()
    checkpoint = M1CheckpointReference(
        manifest_sha256=manifest_sha256,
        label_source_revision="b" * 40,
        training_source_revision="c" * 40,
        runtime=runtime,
        seed=17,
        selected_epoch=1,
        sha256=checkpoint_sha256,
        byte_size=1,
        relative_path=(
            f"m1/checkpoints/{manifest_sha256}/17/{checkpoint_sha256}.safetensors"
        ),
    )
    selection = M1SelectionReference(
        manifest_sha256=manifest_sha256,
        seed=17,
        sha256=selection_sha256,
        byte_size=1,
        relative_path=(
            f"m1/selections/{manifest_sha256}/17/{selection_sha256}.json"
        ),
    )
    return M1LearnedCandidate(
        selection=selection,
        checkpoint=checkpoint,
        model=model,
    )


def _runtime() -> M1RuntimeEnvironment:
    return M1RuntimeEnvironment(
        python_version="3.12.10",
        numpy_version="2.5.3",
        scipy_version="1.18.1",
        torch_version="2.14.0",
        safetensors_version="0.8.0",
        lockfile_sha256="a" * 64,
        platform_system="TestOS",
        platform_machine="test-machine",
        processor="test-processor",
        torch_num_threads=1,
        torch_num_interop_threads=1,
    )


def _sample(split: str) -> DatasetSample:
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
    return next(sample for sample in manifest.samples if sample.split == split)


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
