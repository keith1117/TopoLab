"""Frozen M1 learned warm-start inference and fallback-aware evaluation."""

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Annotated, Literal

import numpy as np
import torch
from numpy.typing import NDArray
from pydantic import Field, model_validator

from topolab.baselines import (
    BASELINE_COMPLIANCE_RELATIVE_TOLERANCE,
    BaselineCaseResult,
    BaselineEvaluationError,
    BaselineFailureCode,
    BaselineMetrics,
    BaselineTiming,
    run_uniform_baseline,
    safe_refinement_metrics,
    solve_case_with_initial_density,
    validate_refinement_quality,
)
from topolab.dataset import DatasetSample, DatasetSplit
from topolab.experiment import encode_case, project_design_density
from topolab.problem import ContractModel, TopologyResult
from topolab.training import M1_DATA_MANIFEST_SHA256, M1_SEEDS, WarmStartCNN
from topolab.training_artifacts import (
    M1CheckpointReference,
    M1SelectionReference,
    load_m1_model,
    read_m1_selection,
)

M1_EVALUATION_VERSION = "topolab.m1.evaluation.v1"


class M1EvaluationError(RuntimeError):
    """Raised when a learned evaluation lacks a valid uniform reference or fallback."""


@dataclass(frozen=True, slots=True)
class M1LearnedCandidate:
    """One verified checkpoint loaded into the frozen M1 architecture."""

    selection: M1SelectionReference
    checkpoint: M1CheckpointReference
    model: WarmStartCNN

    def __post_init__(self) -> None:
        if (
            self.selection.seed != self.checkpoint.seed
            or self.selection.manifest_sha256 != self.checkpoint.manifest_sha256
        ):
            raise ValueError("selection and checkpoint references must match")
        if self.selection.seed not in M1_SEEDS:
            raise ValueError("candidate seed must belong to the frozen M1 sequence")
        if self.selection.manifest_sha256 != M1_DATA_MANIFEST_SHA256:
            raise ValueError("candidate must use the frozen M1 data manifest")
        if any(
            parameter.device.type != "cpu" or parameter.dtype != torch.float32
            for parameter in self.model.parameters()
        ):
            raise ValueError("the frozen M1 evaluation model must use CPU float32")

    @property
    def seed(self) -> int:
        return self.selection.seed


class M1CaseResult(ContractModel):
    """One learned candidate outcome and its charged operational fallback."""

    evaluation_version: Literal["topolab.m1.evaluation.v1"] = (
        "topolab.m1.evaluation.v1"
    )
    case_id: str
    split: DatasetSplit
    seed: Annotated[int, Field(strict=True)]
    selection: M1SelectionReference
    checkpoint: M1CheckpointReference
    succeeded: bool
    failure_code: BaselineFailureCode | None = None
    fallback_used: bool
    timing: BaselineTiming
    candidate: BaselineMetrics | None
    operational: BaselineMetrics
    uniform_reference_compliance: Annotated[float, Field(gt=0.0)]

    @model_validator(mode="after")
    def validate_outcome(self) -> "M1CaseResult":
        if self.split == "train":
            raise ValueError("learned evaluation results cannot use training samples")
        if self.seed not in M1_SEEDS or self.selection.seed != self.seed:
            raise ValueError("result seed must match one frozen M1 selection")
        if (
            self.checkpoint.seed != self.seed
            or self.checkpoint.manifest_sha256 != self.selection.manifest_sha256
        ):
            raise ValueError("result checkpoint must match the M1 selection")
        if self.succeeded and (self.failure_code is not None or self.fallback_used):
            raise ValueError("successful learned outcomes cannot record fallback")
        if not self.succeeded and (self.failure_code is None or not self.fallback_used):
            raise ValueError("failed learned outcomes must record fallback")
        if self.succeeded and self.candidate is None:
            raise ValueError("successful learned outcomes require candidate metrics")
        return self


@dataclass(frozen=True, slots=True)
class _LearnedAttemptOutcome:
    timing: BaselineTiming
    metrics: BaselineMetrics


class _LearnedAttemptFailure(RuntimeError):
    def __init__(
        self,
        code: BaselineFailureCode,
        timing: BaselineTiming,
        result: TopologyResult | None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.timing = timing
        self.result = result


def load_m1_candidate(
    artifact_root: Path,
    reference: M1SelectionReference,
) -> M1LearnedCandidate:
    """Load one verified selection and bind its checkpoint to the frozen model."""

    selection = read_m1_selection(artifact_root, reference)
    return M1LearnedCandidate(
        selection=reference,
        checkpoint=selection.checkpoint,
        model=load_m1_model(artifact_root, selection.checkpoint),
    )


def run_learned_warm_start(
    sample: DatasetSample,
    candidate: M1LearnedCandidate,
    uniform_reference: BaselineCaseResult,
) -> M1CaseResult:
    """Infer, project, refine, audit, and fall back for one non-training sample."""

    if sample.split == "train":
        raise ValueError("learned evaluation queries must not be training samples")
    _validate_uniform_reference(sample, uniform_reference)
    uniform_compliance = uniform_reference.operational.final_compliance

    try:
        outcome = _attempt_learned(sample, candidate, uniform_compliance)
    except _LearnedAttemptFailure as failure:
        try:
            fallback = run_uniform_baseline(sample)
        except BaselineEvaluationError as error:
            raise M1EvaluationError("uniform fallback failed") from error
        if not np.isclose(
            fallback.operational.final_compliance,
            uniform_compliance,
            rtol=BASELINE_COMPLIANCE_RELATIVE_TOLERANCE,
            atol=0.0,
        ):
            raise M1EvaluationError(
                "uniform fallback does not reproduce the reference"
            ) from failure
        return M1CaseResult(
            case_id=sample.case.case_id,
            split=sample.split,
            seed=candidate.seed,
            selection=candidate.selection,
            checkpoint=candidate.checkpoint,
            succeeded=False,
            failure_code=failure.code,
            fallback_used=True,
            timing=BaselineTiming.from_phases(
                setup=failure.timing.setup_seconds,
                projection=failure.timing.projection_seconds,
                refinement=failure.timing.refinement_seconds,
                fallback=fallback.timing.end_to_end_seconds,
            ),
            candidate=safe_refinement_metrics(sample.case, failure.result),
            operational=fallback.operational,
            uniform_reference_compliance=uniform_compliance,
        )

    return M1CaseResult(
        case_id=sample.case.case_id,
        split=sample.split,
        seed=candidate.seed,
        selection=candidate.selection,
        checkpoint=candidate.checkpoint,
        succeeded=True,
        fallback_used=False,
        timing=outcome.timing,
        candidate=outcome.metrics,
        operational=outcome.metrics,
        uniform_reference_compliance=uniform_compliance,
    )


def _attempt_learned(
    sample: DatasetSample,
    candidate: M1LearnedCandidate,
    uniform_compliance: float,
) -> _LearnedAttemptOutcome:
    setup = projection = refinement = 0.0
    result: TopologyResult | None = None
    phase: BaselineFailureCode = "setup_error"
    try:
        started = perf_counter()
        try:
            raw = _predict_design_density(sample, candidate)
        finally:
            setup = perf_counter() - started

        phase = "projection_error"
        started = perf_counter()
        try:
            projected = project_design_density(sample.case, raw)
        finally:
            projection = perf_counter() - started

        phase = "refinement_error"
        started = perf_counter()
        try:
            result = solve_case_with_initial_density(
                sample.case,
                projected.design_density,
            )
        finally:
            refinement = perf_counter() - started

        phase = "quality_error"
        metrics = validate_refinement_quality(
            sample.case,
            result,
            uniform_compliance,
        )
    except Exception as error:
        raise _LearnedAttemptFailure(
            phase,
            BaselineTiming.from_phases(
                setup=setup,
                projection=projection,
                refinement=refinement,
            ),
            result,
        ) from error
    return _LearnedAttemptOutcome(
        timing=BaselineTiming.from_phases(
            setup=setup,
            projection=projection,
            refinement=refinement,
        ),
        metrics=metrics,
    )


def _predict_design_density(
    sample: DatasetSample,
    candidate: M1LearnedCandidate,
) -> NDArray[np.float32]:
    encoded = encode_case(sample.case).input_tensor
    inputs = torch.from_numpy(encoded).unsqueeze(0)
    candidate.model.eval()
    with torch.no_grad():
        prediction = candidate.model(inputs)

    nx, ny, nz = sample.case.problem.mesh.element_counts
    expected_shape = (1, 1, nz, ny, nx)
    if prediction.shape != expected_shape:
        raise ValueError("model prediction does not match the case shape")
    if prediction.device.type != "cpu" or prediction.dtype != torch.float32:
        raise ValueError("model prediction must be CPU float32")
    if not torch.isfinite(prediction).all():
        raise ValueError("model prediction must contain only finite values")
    if torch.any(prediction < 0.0) or torch.any(prediction > 1.0):
        raise ValueError("model prediction must lie in [0, 1]")
    return np.asarray(
        prediction.squeeze(0).detach().numpy(),
        dtype=np.float32,
    ).copy()


def _validate_uniform_reference(
    sample: DatasetSample,
    reference: BaselineCaseResult,
) -> None:
    if (
        reference.method != "uniform"
        or reference.case_id != sample.case.case_id
        or reference.split != sample.split
        or not reference.succeeded
        or reference.fallback_used
    ):
        raise M1EvaluationError(
            "learned evaluation requires the matching successful uniform reference"
        )
