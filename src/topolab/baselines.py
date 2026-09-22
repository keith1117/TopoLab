"""Fixed M0 baseline initializations and quality-aware evaluation runner."""

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Annotated, Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import Field, model_validator

from topolab.dataset import DatasetSample, DatasetSplit
from topolab.experiment import ExperimentCase, encode_case, project_design_density
from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.label_artifacts import LabelArtifactError, read_label_artifact
from topolab.materialization import (
    DatasetMaterializationIndex,
    MaterializationFailure,
    MaterializationSuccess,
)
from topolab.mesh import Hex8Mesh, generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport, PointLoad
from topolab.problem import (
    ContractModel,
    FaceLoadDefinition,
    PointLoadDefinition,
    TopologyProblem,
    TopologyResult,
    solve_problem,
)
from topolab.simp import evaluate_compliance

BASELINE_RUNNER_VERSION = "topolab.m0.baselines.v1"
BASELINE_VOLUME_TOLERANCE = 5e-3
BASELINE_COMPLIANCE_RELATIVE_TOLERANCE = 1e-9
BASELINE_QUALITY_FACTOR = 1.001

type BaselineMethod = Literal["uniform", "physics_heuristic", "nearest_neighbor"]
type BaselineFailureCode = Literal[
    "setup_error",
    "projection_error",
    "refinement_error",
    "quality_error",
]


class BaselineEvaluationError(RuntimeError):
    """Raised when the dataset or mandatory uniform reference is invalid."""


class _BaselineQualityError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class NearestNeighborMatch:
    """One deterministic training-only nearest-neighbor lookup result."""

    case_id: str
    design_density: NDArray[np.float32]
    mean_squared_distance: float


@dataclass(frozen=True, slots=True)
class NearestNeighborIndex:
    """In-memory input/label index built exclusively from training samples."""

    case_ids: tuple[str, ...]
    input_tensors: NDArray[np.float32]
    design_tensors: NDArray[np.float32]

    def __post_init__(self) -> None:
        if not self.case_ids:
            raise ValueError("nearest-neighbor index must contain a training case")
        if self.case_ids != tuple(sorted(self.case_ids)):
            raise ValueError("nearest-neighbor case IDs must be sorted")
        if len(set(self.case_ids)) != len(self.case_ids):
            raise ValueError("nearest-neighbor case IDs must be unique")

        inputs = np.asarray(self.input_tensors, dtype=np.float32).copy()
        designs = np.asarray(self.design_tensors, dtype=np.float32).copy()
        if inputs.ndim != 5 or inputs.shape[0] != len(self.case_ids):
            raise ValueError("inputs must have shape (case, channel, z, y, x)")
        if designs.ndim != 5 or designs.shape[0] != len(self.case_ids):
            raise ValueError("labels must have shape (case, channel, z, y, x)")
        if designs.shape[1] != 1 or designs.shape[2:] != inputs.shape[2:]:
            raise ValueError("labels must match the input spatial shape")
        if not np.all(np.isfinite(inputs)) or not np.all(np.isfinite(designs)):
            raise ValueError("nearest-neighbor tensors must be finite")
        if np.any(designs < 0.0) or np.any(designs > 1.0):
            raise ValueError("nearest-neighbor labels must lie in [0, 1]")
        inputs.setflags(write=False)
        designs.setflags(write=False)
        object.__setattr__(self, "input_tensors", inputs)
        object.__setattr__(self, "design_tensors", designs)

    @property
    def candidate_count(self) -> int:
        return len(self.case_ids)

    @property
    def stored_size_bytes(self) -> int:
        identifier_bytes = sum(len(case_id.encode()) for case_id in self.case_ids)
        return self.input_tensors.nbytes + self.design_tensors.nbytes + identifier_bytes

    def query(self, case: ExperimentCase) -> NearestNeighborMatch:
        """Return the minimum-MSE training case, breaking ties by case ID."""

        query = encode_case(case).input_tensor
        if query.shape != self.input_tensors.shape[1:]:
            raise ValueError("query case does not match the nearest-neighbor cohort")
        differences = self.input_tensors.astype(np.float64) - query.astype(np.float64)
        distances = np.mean(np.square(differences), axis=(1, 2, 3, 4))
        index = int(np.argmin(distances))
        design = self.design_tensors[index].copy()
        design.setflags(write=False)
        return NearestNeighborMatch(
            case_id=self.case_ids[index],
            design_density=design,
            mean_squared_distance=float(distances[index]),
        )


class BaselineMetrics(ContractModel):
    """Quality and solver cost for one valid refined result."""

    iterations: Annotated[int, Field(strict=True, gt=0)]
    final_compliance: Annotated[float, Field(gt=0.0)]
    physical_volume_error: Annotated[float, Field(ge=0.0)]


class BaselineTiming(ContractModel):
    """Non-overlapping per-query baseline phases in seconds."""

    setup_seconds: Annotated[float, Field(ge=0.0)] = 0.0
    projection_seconds: Annotated[float, Field(ge=0.0)] = 0.0
    refinement_seconds: Annotated[float, Field(ge=0.0)] = 0.0
    fallback_seconds: Annotated[float, Field(ge=0.0)] = 0.0
    end_to_end_seconds: Annotated[float, Field(ge=0.0)]

    @classmethod
    def from_phases(
        cls,
        *,
        setup: float = 0.0,
        projection: float = 0.0,
        refinement: float = 0.0,
        fallback: float = 0.0,
    ) -> "BaselineTiming":
        return cls(
            setup_seconds=setup,
            projection_seconds=projection,
            refinement_seconds=refinement,
            fallback_seconds=fallback,
            end_to_end_seconds=setup + projection + refinement + fallback,
        )

    @model_validator(mode="after")
    def validate_total(self) -> "BaselineTiming":
        if self.end_to_end_seconds != (
            self.setup_seconds
            + self.projection_seconds
            + self.refinement_seconds
            + self.fallback_seconds
        ):
            raise ValueError("end-to-end time must equal the recorded phases")
        return self


class NearestNeighborMetadata(ContractModel):
    """Per-query nearest-neighbor selection and deterministic index size."""

    matched_case_id: str | None
    candidate_count: Annotated[int, Field(strict=True, gt=0)]
    index_size_bytes: Annotated[int, Field(strict=True, gt=0)]


class BaselineCaseResult(ContractModel):
    """One candidate outcome and its fallback-aware operational result."""

    runner_version: Literal["topolab.m0.baselines.v1"] = "topolab.m0.baselines.v1"
    case_id: str
    split: DatasetSplit
    method: BaselineMethod
    succeeded: bool
    failure_code: BaselineFailureCode | None = None
    fallback_used: bool
    timing: BaselineTiming
    candidate: BaselineMetrics | None
    operational: BaselineMetrics
    uniform_reference_compliance: Annotated[float, Field(gt=0.0)]
    nearest_neighbor: NearestNeighborMetadata | None = None

    @model_validator(mode="after")
    def validate_outcome(self) -> "BaselineCaseResult":
        if self.succeeded and (self.failure_code is not None or self.fallback_used):
            raise ValueError("successful outcomes cannot record fallback")
        if not self.succeeded and (self.failure_code is None or not self.fallback_used):
            raise ValueError("failed outcomes must record fallback")
        if self.succeeded and self.candidate is None:
            raise ValueError("successful outcomes require candidate metrics")
        if (self.method == "nearest_neighbor") != (self.nearest_neighbor is not None):
            raise ValueError("nearest-neighbor metadata must match the method")
        if self.method == "uniform" and not self.succeeded:
            raise ValueError("the mandatory uniform reference cannot fail")
        return self


@dataclass(frozen=True, slots=True)
class _AttemptOutcome:
    timing: BaselineTiming
    metrics: BaselineMetrics
    matched_case_id: str | None = None


class _AttemptFailure(RuntimeError):
    def __init__(
        self,
        code: BaselineFailureCode,
        timing: BaselineTiming,
        result: TopologyResult | None,
        matched_case_id: str | None,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.timing = timing
        self.result = result
        self.matched_case_id = matched_case_id


def build_nearest_neighbor_index(
    root: Path,
    materialization: DatasetMaterializationIndex,
) -> NearestNeighborIndex:
    """Load a verified, training-only nearest-neighbor input/label index."""

    if materialization.state != "complete":
        raise BaselineEvaluationError("nearest-neighbor data must be fully materialized")
    if any(isinstance(entry, MaterializationFailure) for entry in materialization.entries):
        raise BaselineEvaluationError("nearest-neighbor data cannot contain failed cases")

    entries = {
        entry.case_id: entry
        for entry in materialization.entries
        if isinstance(entry, MaterializationSuccess)
    }
    case_ids: list[str] = []
    inputs: list[NDArray[np.float32]] = []
    designs: list[NDArray[np.float32]] = []
    for sample in materialization.manifest.samples:
        if sample.split != "train":
            continue
        entry = entries.get(sample.case.case_id)
        if entry is None:
            raise BaselineEvaluationError("training sample is missing a label artifact")
        try:
            label = read_label_artifact(root, entry.artifact)
        except LabelArtifactError as error:
            raise BaselineEvaluationError("training label verification failed") from error
        if (
            label.case != sample.case
            or label.source_revision != materialization.manifest.source_revision
            or label.environment != materialization.manifest.environment
        ):
            raise BaselineEvaluationError("training label does not match the manifest")
        case_ids.append(sample.case.case_id)
        inputs.append(encode_case(sample.case).input_tensor)
        designs.append(label.design_tensor())

    if not case_ids:
        raise BaselineEvaluationError("nearest-neighbor data has no training samples")
    return NearestNeighborIndex(
        case_ids=tuple(case_ids),
        input_tensors=np.stack(inputs),
        design_tensors=np.stack(designs),
    )


def run_fixed_baselines(
    sample: DatasetSample,
    nearest_neighbors: NearestNeighborIndex,
) -> tuple[BaselineCaseResult, BaselineCaseResult, BaselineCaseResult]:
    """Run all frozen baselines for one held-out or OOD dataset sample."""

    if sample.split == "train":
        raise ValueError("baseline evaluation queries must not be training samples")
    try:
        uniform = _attempt(sample.case, "uniform", nearest_neighbors, None)
    except _AttemptFailure as error:
        raise BaselineEvaluationError("uniform reference failed") from error

    uniform_compliance = uniform.metrics.final_compliance
    return (
        _success_result(sample, "uniform", uniform, uniform_compliance, None),
        _nonuniform_result(
            sample,
            "physics_heuristic",
            nearest_neighbors,
            uniform_compliance,
        ),
        _nonuniform_result(
            sample,
            "nearest_neighbor",
            nearest_neighbors,
            uniform_compliance,
        ),
    )


def _attempt(
    case: ExperimentCase,
    method: BaselineMethod,
    nearest_neighbors: NearestNeighborIndex,
    uniform_compliance: float | None,
) -> _AttemptOutcome:
    setup = projection = refinement = 0.0
    result: TopologyResult | None = None
    matched_case_id: str | None = None
    phase: BaselineFailureCode = "setup_error"
    try:
        if method == "uniform":
            raw = _uniform_raw_density(case)
        else:
            started = perf_counter()
            try:
                raw, matched_case_id = _raw_initialization(
                    case,
                    method,
                    nearest_neighbors,
                )
            finally:
                setup = perf_counter() - started

        phase = "projection_error"
        started = perf_counter()
        try:
            projected = project_design_density(case, raw)
        finally:
            projection = perf_counter() - started

        phase = "refinement_error"
        started = perf_counter()
        try:
            result = _solve_with_initial_density(case, projected.design_density)
        finally:
            refinement = perf_counter() - started

        phase = "quality_error"
        metrics = _validate_quality(case, result, uniform_compliance)
    except Exception as error:
        raise _AttemptFailure(
            phase,
            BaselineTiming.from_phases(
                setup=setup,
                projection=projection,
                refinement=refinement,
            ),
            result,
            matched_case_id,
        ) from error
    return _AttemptOutcome(
        timing=BaselineTiming.from_phases(
            setup=setup,
            projection=projection,
            refinement=refinement,
        ),
        metrics=metrics,
        matched_case_id=matched_case_id,
    )


def _nonuniform_result(
    sample: DatasetSample,
    method: Literal["physics_heuristic", "nearest_neighbor"],
    nearest_neighbors: NearestNeighborIndex,
    uniform_compliance: float,
) -> BaselineCaseResult:
    try:
        outcome = _attempt(
            sample.case,
            method,
            nearest_neighbors,
            uniform_compliance,
        )
    except _AttemptFailure as failure:
        try:
            fallback = _attempt(sample.case, "uniform", nearest_neighbors, None)
        except _AttemptFailure as error:
            raise BaselineEvaluationError("uniform fallback failed") from error
        timing = BaselineTiming.from_phases(
            setup=failure.timing.setup_seconds,
            projection=failure.timing.projection_seconds,
            refinement=failure.timing.refinement_seconds,
            fallback=fallback.timing.end_to_end_seconds,
        )
        return BaselineCaseResult(
            case_id=sample.case.case_id,
            split=sample.split,
            method=method,
            succeeded=False,
            failure_code=failure.code,
            fallback_used=True,
            timing=timing,
            candidate=_safe_metrics(sample.case, failure.result),
            operational=fallback.metrics,
            uniform_reference_compliance=uniform_compliance,
            nearest_neighbor=_nearest_metadata(
                method,
                nearest_neighbors,
                failure.matched_case_id,
            ),
        )
    return _success_result(
        sample,
        method,
        outcome,
        uniform_compliance,
        nearest_neighbors,
    )


def _success_result(
    sample: DatasetSample,
    method: BaselineMethod,
    outcome: _AttemptOutcome,
    uniform_compliance: float,
    nearest_neighbors: NearestNeighborIndex | None,
) -> BaselineCaseResult:
    return BaselineCaseResult(
        case_id=sample.case.case_id,
        split=sample.split,
        method=method,
        succeeded=True,
        fallback_used=False,
        timing=outcome.timing,
        candidate=outcome.metrics,
        operational=outcome.metrics,
        uniform_reference_compliance=uniform_compliance,
        nearest_neighbor=(
            None
            if nearest_neighbors is None
            else _nearest_metadata(
                method,
                nearest_neighbors,
                outcome.matched_case_id,
            )
        ),
    )


def _nearest_metadata(
    method: BaselineMethod,
    nearest_neighbors: NearestNeighborIndex,
    matched_case_id: str | None,
) -> NearestNeighborMetadata | None:
    if method != "nearest_neighbor":
        return None
    return NearestNeighborMetadata(
        matched_case_id=matched_case_id,
        candidate_count=nearest_neighbors.candidate_count,
        index_size_bytes=nearest_neighbors.stored_size_bytes,
    )


def _raw_initialization(
    case: ExperimentCase,
    method: Literal["physics_heuristic", "nearest_neighbor"],
    nearest_neighbors: NearestNeighborIndex,
) -> tuple[NDArray[np.float32], str | None]:
    if method == "physics_heuristic":
        return _physics_heuristic_raw_density(case), None
    match = nearest_neighbors.query(case)
    return match.design_density, match.case_id


def _uniform_raw_density(case: ExperimentCase) -> NDArray[np.float32]:
    nx, ny, nz = case.problem.mesh.element_counts
    return np.full(
        (1, nz, ny, nx),
        case.problem.optimization.volume_fraction,
        dtype=np.float32,
    )


def _physics_heuristic_raw_density(case: ExperimentCase) -> NDArray[np.float32]:
    problem = case.problem
    mesh, loads, constrained_dofs = _case_system(case)
    uniform = np.full(
        mesh.connectivity.shape[0],
        problem.optimization.volume_fraction,
    )
    analysis = evaluate_compliance(
        mesh,
        uniform,
        loads,
        constrained_dofs,
        solid_modulus=problem.material.solid_modulus,
        minimum_modulus=problem.material.minimum_modulus,
        poisson_ratio=problem.material.poisson_ratio,
        penalty=problem.optimization.penalty,
    )
    score = np.maximum(0.0, -analysis.sensitivity)
    minimum, maximum = float(np.min(score)), float(np.max(score))
    raw = (score - minimum) / (maximum - minimum) if maximum > minimum else uniform
    nx, ny, nz = problem.mesh.element_counts
    return np.asarray(raw, dtype=np.float32).reshape(1, nz, ny, nx)


def _solve_with_initial_density(
    case: ExperimentCase,
    initial_density: NDArray[np.float64],
) -> TopologyResult:
    payload = case.problem.model_dump(mode="json")
    payload["initial_density"] = tuple(float(value) for value in initial_density)
    return solve_problem(TopologyProblem.model_validate(payload))


def _validate_quality(
    case: ExperimentCase,
    result: TopologyResult,
    uniform_compliance: float | None,
) -> BaselineMetrics:
    if not result.converged or not result.history:
        raise _BaselineQualityError("baseline refinement did not converge")
    if len(result.history) > case.problem.optimization.max_iterations:
        raise _BaselineQualityError("baseline refinement exceeded the iteration limit")
    vectors = (
        result.design_density,
        result.physical_density,
        result.displacements,
        result.reactions,
        *(state.design_density for state in result.history),
        *(state.physical_density for state in result.history),
    )
    scalars = (
        result.compliance,
        *(
            value
            for state in result.history
            for value in (
                state.compliance,
                state.volume_fraction,
                state.density_change,
            )
        ),
    )
    if not np.all(np.isfinite(scalars)) or any(
        not np.all(np.isfinite(values)) for values in vectors
    ):
        raise _BaselineQualityError("baseline refinement returned non-finite values")

    physical = np.asarray(result.physical_density, dtype=np.float64)
    volume_error = abs(
        float(np.mean(physical)) - case.problem.optimization.volume_fraction
    )
    if volume_error > BASELINE_VOLUME_TOLERANCE:
        raise _BaselineQualityError("baseline refinement violates the volume tolerance")
    resolved = _evaluate_case_density(case, physical)
    if not np.isclose(
        result.compliance,
        resolved,
        rtol=BASELINE_COMPLIANCE_RELATIVE_TOLERANCE,
        atol=0.0,
    ):
        raise _BaselineQualityError("baseline compliance failed independent re-solve")
    if (
        uniform_compliance is not None
        and result.compliance > BASELINE_QUALITY_FACTOR * uniform_compliance
    ):
        raise _BaselineQualityError("baseline compliance exceeds the uniform limit")
    return BaselineMetrics(
        iterations=len(result.history),
        final_compliance=result.compliance,
        physical_volume_error=volume_error,
    )


def _safe_metrics(
    case: ExperimentCase,
    result: TopologyResult | None,
) -> BaselineMetrics | None:
    if (
        result is None
        or not result.history
        or not np.isfinite(result.compliance)
        or result.compliance <= 0.0
    ):
        return None
    physical = np.asarray(result.physical_density, dtype=np.float64)
    if not np.all(np.isfinite(physical)):
        return None
    return BaselineMetrics(
        iterations=len(result.history),
        final_compliance=result.compliance,
        physical_volume_error=abs(
            float(np.mean(physical)) - case.problem.optimization.volume_fraction
        ),
    )


def _evaluate_case_density(
    case: ExperimentCase,
    physical_density: NDArray[np.float64],
) -> float:
    problem = case.problem
    mesh, loads, constrained_dofs = _case_system(case)
    return evaluate_compliance(
        mesh,
        physical_density,
        loads,
        constrained_dofs,
        solid_modulus=problem.material.solid_modulus,
        minimum_modulus=problem.material.minimum_modulus,
        poisson_ratio=problem.material.poisson_ratio,
        penalty=problem.optimization.penalty,
    ).compliance


def _case_system(
    case: ExperimentCase,
) -> tuple[Hex8Mesh, NDArray[np.float64], NDArray[np.int64]]:
    problem = case.problem
    mesh = generate_structured_hex8(
        *problem.mesh.element_counts,
        lengths=problem.mesh.lengths,
    )
    constrained_dofs = build_constrained_dofs(
        mesh,
        [
            FixedFaceSupport(
                axis=support.axis,
                side=support.side,
                directions=support.directions,
            )
            for support in problem.supports
        ],
    )
    loads = build_load_vector(mesh, [_core_load(load) for load in problem.loads])
    return mesh, loads, constrained_dofs


def _core_load(load: PointLoadDefinition | FaceLoadDefinition) -> PointLoad | FaceLoad:
    if isinstance(load, PointLoadDefinition):
        return PointLoad(
            node=load.node,
            direction=load.direction,
            magnitude=load.magnitude,
        )
    return FaceLoad(
        axis=load.axis,
        side=load.side,
        direction=load.direction,
        total=load.total,
    )
