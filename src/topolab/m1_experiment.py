"""Recoverable M1 held-out experiment orchestration and frozen statistics."""

import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Annotated, Literal, cast

import numpy as np
from pydantic import Field, ValidationError, field_validator, model_validator

from topolab.baselines import (
    BaselineCaseResult,
    build_nearest_neighbor_index,
    run_fixed_baselines,
)
from topolab.learned_evaluation import (
    M1CaseResult,
    M1LearnedCandidate,
    run_learned_warm_start,
)
from topolab.materialization import (
    DatasetMaterializationIndex,
    MaterializationFailure,
)
from topolab.problem import ContractModel
from topolab.training import M1_DATA_MANIFEST_SHA256, M1_SEEDS
from topolab.training_artifacts import (
    M1CheckpointReference,
    M1RuntimeEnvironment,
    M1SelectionReference,
)

M1_EXPERIMENT_VERSION = "topolab.m1.experiment.v1"
M1_EVALUATION_INDEX_VERSION = "topolab.m1.evaluation-index.v1"
M1_STATISTICS_VERSION = "topolab.m1.statistics.v1"
M1_BOOTSTRAP_RESAMPLES = 10_000
M1_BOOTSTRAP_SEED = 20_260_919

_REVISION_PATTERN = r"^[0-9a-f]{40}$"
_SHA256_PATTERN = r"^[0-9a-f]{64}$"

type M1EvaluationSplit = Literal["test", "ood"]
type M1ExperimentMethod = Literal[
    "uniform",
    "physics_heuristic",
    "nearest_neighbor",
    "learned",
]


class M1ExperimentError(RuntimeError):
    """Raised when an M1 experiment checkpoint or context is invalid."""


class M1EvaluationContext(ContractModel):
    """Immutable identity of one five-seed held-out experiment."""

    experiment_version: Literal["topolab.m1.experiment.v1"] = (
        "topolab.m1.experiment.v1"
    )
    manifest_sha256: Annotated[str, Field(pattern=_SHA256_PATTERN)]
    evaluation_source_revision: Annotated[str, Field(pattern=_REVISION_PATTERN)]
    runtime: M1RuntimeEnvironment
    selections: tuple[
        M1SelectionReference,
        M1SelectionReference,
        M1SelectionReference,
        M1SelectionReference,
        M1SelectionReference,
    ]
    checkpoints: tuple[
        M1CheckpointReference,
        M1CheckpointReference,
        M1CheckpointReference,
        M1CheckpointReference,
        M1CheckpointReference,
    ]

    @model_validator(mode="after")
    def validate_context(self) -> "M1EvaluationContext":
        if self.manifest_sha256 != M1_DATA_MANIFEST_SHA256:
            raise ValueError("evaluation must use the frozen M1 data manifest")
        if tuple(reference.seed for reference in self.selections) != M1_SEEDS:
            raise ValueError("evaluation selections must contain every M1 seed in order")
        if any(
            reference.manifest_sha256 != self.manifest_sha256
            for reference in self.selections
        ):
            raise ValueError("evaluation selections must match the data manifest")
        if tuple(reference.seed for reference in self.checkpoints) != M1_SEEDS:
            raise ValueError("evaluation checkpoints must contain every M1 seed in order")
        if any(
            reference.manifest_sha256 != self.manifest_sha256
            for reference in self.checkpoints
        ):
            raise ValueError("evaluation checkpoints must match the data manifest")
        return self


class M1EvaluationCaseRecord(ContractModel):
    """All fixed-baseline and learned outcomes for one physical query case."""

    case_id: str
    split: M1EvaluationSplit
    baselines: tuple[
        BaselineCaseResult,
        BaselineCaseResult,
        BaselineCaseResult,
    ]
    learned: tuple[
        M1CaseResult,
        M1CaseResult,
        M1CaseResult,
        M1CaseResult,
        M1CaseResult,
    ]

    @model_validator(mode="after")
    def validate_results(self) -> "M1EvaluationCaseRecord":
        if tuple(result.method for result in self.baselines) != (
            "uniform",
            "physics_heuristic",
            "nearest_neighbor",
        ):
            raise ValueError("case record must contain the three baselines in order")
        if tuple(result.seed for result in self.learned) != M1_SEEDS:
            raise ValueError("case record must contain every learned seed in order")
        results = (*self.baselines, *self.learned)
        if any(
            result.case_id != self.case_id or result.split != self.split
            for result in results
        ):
            raise ValueError("case results must match the record identity")
        uniform = self.baselines[0]
        if not uniform.succeeded or uniform.fallback_used:
            raise ValueError("case record requires a successful uniform reference")
        reference_compliance = uniform.operational.final_compliance
        if any(
            result.uniform_reference_compliance != reference_compliance
            for result in results
        ):
            raise ValueError("case results must share the uniform reference compliance")
        return self


class M1EvaluationIndex(ContractModel):
    """Canonical append-only checkpoint for one M1 held-out experiment."""

    index_version: Literal["topolab.m1.evaluation-index.v1"] = (
        "topolab.m1.evaluation-index.v1"
    )
    state: Literal["in_progress", "complete"]
    context: M1EvaluationContext
    entries: tuple[M1EvaluationCaseRecord, ...] = ()

    @classmethod
    def start(cls, context: M1EvaluationContext) -> "M1EvaluationIndex":
        return cls(state="in_progress", context=context)

    @field_validator("entries", mode="after")
    @classmethod
    def sort_entries(
        cls,
        entries: tuple[M1EvaluationCaseRecord, ...],
    ) -> tuple[M1EvaluationCaseRecord, ...]:
        return tuple(sorted(entries, key=lambda entry: entry.case_id))

    @model_validator(mode="after")
    def validate_entries(self) -> "M1EvaluationIndex":
        case_ids = tuple(entry.case_id for entry in self.entries)
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("evaluation entries must have unique case IDs")
        expected_references = self.context.selections
        expected_checkpoints = self.context.checkpoints
        for entry in self.entries:
            if tuple(result.selection for result in entry.learned) != expected_references:
                raise ValueError("learned results must match the evaluation selections")
            if tuple(result.checkpoint for result in entry.learned) != expected_checkpoints:
                raise ValueError("learned results must match the evaluation checkpoints")
        return self


class M1MethodStatistics(ContractModel):
    """Paired operational summary for one method and optional learned seed."""

    method: M1ExperimentMethod
    seed: Annotated[int, Field(strict=True)] | None = None
    case_count: Annotated[int, Field(strict=True, gt=0)]
    mean_time_ratio_to_uniform: Annotated[float, Field(gt=0.0)]
    median_time_ratio_to_uniform: Annotated[float, Field(gt=0.0)]
    first_quartile_time_ratio_to_uniform: Annotated[float, Field(gt=0.0)]
    third_quartile_time_ratio_to_uniform: Annotated[float, Field(gt=0.0)]
    failure_rate: Annotated[float, Field(ge=0.0, le=1.0)]
    fallback_rate: Annotated[float, Field(ge=0.0, le=1.0)]
    median_operational_iterations: Annotated[float, Field(gt=0.0)]
    median_operational_compliance_ratio: Annotated[float, Field(gt=0.0)]
    maximum_operational_volume_error: Annotated[float, Field(ge=0.0)]

    @model_validator(mode="after")
    def validate_method_seed(self) -> "M1MethodStatistics":
        if (self.method == "learned") != (self.seed is not None):
            raise ValueError("only learned method statistics have a seed")
        if self.seed is not None and self.seed not in M1_SEEDS:
            raise ValueError("learned statistics seed must be frozen by M1")
        return self


class M1LearnedAggregateStatistics(ContractModel):
    """Five-seed learned summary with the frozen case-cluster bootstrap."""

    case_count: Annotated[int, Field(strict=True, gt=0)]
    observation_count: Annotated[int, Field(strict=True, gt=0)]
    mean_time_ratio_to_uniform: Annotated[float, Field(gt=0.0)]
    confidence_interval_95_lower: Annotated[float, Field(gt=0.0)]
    confidence_interval_95_upper: Annotated[float, Field(gt=0.0)]
    median_time_ratio_to_uniform: Annotated[float, Field(gt=0.0)]
    first_quartile_time_ratio_to_uniform: Annotated[float, Field(gt=0.0)]
    third_quartile_time_ratio_to_uniform: Annotated[float, Field(gt=0.0)]
    failure_rate: Annotated[float, Field(ge=0.0, le=1.0)]
    fallback_rate: Annotated[float, Field(ge=0.0, le=1.0)]

    @model_validator(mode="after")
    def validate_interval(self) -> "M1LearnedAggregateStatistics":
        if self.observation_count != self.case_count * len(M1_SEEDS):
            raise ValueError("learned observation count must retain all seeds per case")
        if self.confidence_interval_95_lower > self.confidence_interval_95_upper:
            raise ValueError("bootstrap confidence interval bounds are reversed")
        return self


class M1SplitStatistics(ContractModel):
    """All fixed method and learned summaries for one evaluation split."""

    split: M1EvaluationSplit
    case_count: Annotated[int, Field(strict=True, gt=0)]
    methods: tuple[
        M1MethodStatistics,
        M1MethodStatistics,
        M1MethodStatistics,
        M1MethodStatistics,
        M1MethodStatistics,
        M1MethodStatistics,
        M1MethodStatistics,
        M1MethodStatistics,
    ]
    learned_aggregate: M1LearnedAggregateStatistics

    @model_validator(mode="after")
    def validate_methods(self) -> "M1SplitStatistics":
        identities = tuple((item.method, item.seed) for item in self.methods)
        expected = (
            ("uniform", None),
            ("physics_heuristic", None),
            ("nearest_neighbor", None),
            *(("learned", seed) for seed in M1_SEEDS),
        )
        if identities != expected:
            raise ValueError("split statistics methods are not in frozen order")
        if any(item.case_count != self.case_count for item in self.methods):
            raise ValueError("every method must retain every case")
        if self.learned_aggregate.case_count != self.case_count:
            raise ValueError("learned aggregate must retain every case")
        return self


class M1ExperimentStatistics(ContractModel):
    """Frozen test/OOD paired statistics for one complete experiment index."""

    statistics_version: Literal["topolab.m1.statistics.v1"] = (
        "topolab.m1.statistics.v1"
    )
    bootstrap_resamples: Literal[10000] = 10_000
    bootstrap_seed: Literal[20260919] = 20_260_919
    splits: tuple[M1SplitStatistics, M1SplitStatistics]

    @model_validator(mode="after")
    def validate_splits(self) -> "M1ExperimentStatistics":
        if tuple(summary.split for summary in self.splits) != ("test", "ood"):
            raise ValueError("statistics must report test then OOD")
        return self


def canonical_m1_evaluation_context_bytes(context: M1EvaluationContext) -> bytes:
    """Return canonical bytes used to identify one experiment context."""

    return _canonical_json_bytes(context.model_dump(mode="json"))


def build_m1_evaluation_id(context: M1EvaluationContext) -> str:
    """Return the content-derived identity of one experiment context."""

    return hashlib.sha256(canonical_m1_evaluation_context_bytes(context)).hexdigest()


def m1_evaluation_index_path(root: Path, context: M1EvaluationContext) -> Path:
    """Return the stable path for one recoverable evaluation checkpoint."""

    return (
        root
        / "m1"
        / "evaluations"
        / context.manifest_sha256
        / f"{build_m1_evaluation_id(context)}.json"
    )


def canonical_m1_evaluation_index_bytes(index: M1EvaluationIndex) -> bytes:
    """Serialize an evaluation checkpoint in canonical form."""

    return _canonical_json_bytes(index.model_dump(mode="json"))


def write_m1_evaluation_index(
    root: Path,
    index: M1EvaluationIndex,
    *,
    materialization: DatasetMaterializationIndex,
) -> Path:
    """Atomically publish one append-only evaluation checkpoint."""

    _validate_index_materialization(index, materialization)
    target = m1_evaluation_index_path(root, index.context)
    contents = canonical_m1_evaluation_index_bytes(index)
    temporary_path: Path | None = None
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            previous_contents = target.read_bytes()
            if previous_contents == contents:
                return target
            previous = _parse_m1_evaluation_index(previous_contents)
            _validate_index_materialization(previous, materialization)
            if previous.context != index.context:
                raise M1ExperimentError(
                    "existing evaluation index has a different context"
                )
            _validate_append_only(previous, index)

        with NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=".topolab-m1-evaluation-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(contents)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, target)
    except M1ExperimentError:
        raise
    except OSError as error:
        raise M1ExperimentError("could not write M1 evaluation index") from error
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
    return target


def read_m1_evaluation_index(
    root: Path,
    context: M1EvaluationContext,
    *,
    materialization: DatasetMaterializationIndex,
) -> M1EvaluationIndex:
    """Read one canonical checkpoint and verify its complete experiment context."""

    target = m1_evaluation_index_path(root, context)
    try:
        contents = target.read_bytes()
    except FileNotFoundError as error:
        raise M1ExperimentError("M1 evaluation index is missing") from error
    except OSError as error:
        raise M1ExperimentError("could not read M1 evaluation index") from error
    index = _parse_m1_evaluation_index(contents)
    if index.context != context:
        raise M1ExperimentError("M1 evaluation index does not match the context")
    _validate_index_materialization(index, materialization)
    return index


def run_m1_experiment(
    data_root: Path,
    output_root: Path,
    materialization: DatasetMaterializationIndex,
    context: M1EvaluationContext,
    candidates: tuple[
        M1LearnedCandidate,
        M1LearnedCandidate,
        M1LearnedCandidate,
        M1LearnedCandidate,
        M1LearnedCandidate,
    ],
) -> M1EvaluationIndex:
    """Evaluate every pending test/OOD case and checkpoint after each case."""

    if tuple(candidate.selection for candidate in candidates) != context.selections:
        raise M1ExperimentError("loaded candidates do not match the evaluation context")
    if tuple(candidate.checkpoint for candidate in candidates) != context.checkpoints:
        raise M1ExperimentError("loaded checkpoints do not match the evaluation context")
    start = M1EvaluationIndex.start(context)
    _validate_index_materialization(start, materialization)
    target = m1_evaluation_index_path(output_root, context)
    if target.exists():
        index = read_m1_evaluation_index(
            output_root,
            context,
            materialization=materialization,
        )
    else:
        index = start
        write_m1_evaluation_index(
            output_root,
            index,
            materialization=materialization,
        )
    if index.state == "complete":
        return index

    nearest_neighbors = build_nearest_neighbor_index(data_root, materialization)
    samples = tuple(
        sample
        for sample in materialization.manifest.samples
        if sample.split in ("test", "ood")
    )
    recorded = {entry.case_id for entry in index.entries}
    for sample in samples:
        if sample.case.case_id in recorded:
            continue
        baselines = run_fixed_baselines(sample, nearest_neighbors)
        uniform = baselines[0]
        learned = cast(
            tuple[
                M1CaseResult,
                M1CaseResult,
                M1CaseResult,
                M1CaseResult,
                M1CaseResult,
            ],
            tuple(
                run_learned_warm_start(sample, candidate, uniform)
                for candidate in candidates
            ),
        )
        record = M1EvaluationCaseRecord(
            case_id=sample.case.case_id,
            split=cast(M1EvaluationSplit, sample.split),
            baselines=baselines,
            learned=learned,
        )
        index = M1EvaluationIndex(
            state="in_progress",
            context=context,
            entries=(*index.entries, record),
        )
        write_m1_evaluation_index(
            output_root,
            index,
            materialization=materialization,
        )
        recorded.add(record.case_id)

    complete = M1EvaluationIndex(
        state="complete",
        context=context,
        entries=index.entries,
    )
    write_m1_evaluation_index(
        output_root,
        complete,
        materialization=materialization,
    )
    return complete


def compute_m1_experiment_statistics(
    index: M1EvaluationIndex,
    materialization: DatasetMaterializationIndex,
) -> M1ExperimentStatistics:
    """Compute the frozen paired summaries from one complete evaluation index."""

    _validate_index_materialization(index, materialization)
    if index.state != "complete":
        raise M1ExperimentError("statistics require a complete evaluation index")
    return M1ExperimentStatistics(
        splits=(
            _compute_split_statistics(index, "test"),
            _compute_split_statistics(index, "ood"),
        )
    )


def _compute_split_statistics(
    index: M1EvaluationIndex,
    split: M1EvaluationSplit,
) -> M1SplitStatistics:
    records = tuple(entry for entry in index.entries if entry.split == split)
    uniform_seconds = np.asarray(
        [entry.baselines[0].timing.end_to_end_seconds for entry in records],
        dtype=np.float64,
    )
    if np.any(uniform_seconds <= 0.0):
        raise M1ExperimentError("uniform end-to-end time must be positive")

    methods: list[M1MethodStatistics] = [
        _method_statistics(
            "uniform",
            None,
            tuple(entry.baselines[0] for entry in records),
            uniform_seconds,
        ),
        _method_statistics(
            "physics_heuristic",
            None,
            tuple(entry.baselines[1] for entry in records),
            uniform_seconds,
        ),
        _method_statistics(
            "nearest_neighbor",
            None,
            tuple(entry.baselines[2] for entry in records),
            uniform_seconds,
        )
    ]
    for seed_index, seed in enumerate(M1_SEEDS):
        methods.append(
            _method_statistics(
                "learned",
                seed,
                tuple(entry.learned[seed_index] for entry in records),
                uniform_seconds,
            )
        )

    learned_ratios = np.asarray(
        [
            [
                result.timing.end_to_end_seconds / uniform_seconds[case_index]
                for result in entry.learned
            ]
            for case_index, entry in enumerate(records)
        ],
        dtype=np.float64,
    )
    generator = np.random.default_rng(M1_BOOTSTRAP_SEED)
    resampled_cases = generator.integers(
        0,
        len(records),
        size=(M1_BOOTSTRAP_RESAMPLES, len(records)),
    )
    bootstrap_means = learned_ratios[resampled_cases].mean(axis=(1, 2))
    lower, upper = np.quantile(
        bootstrap_means,
        (0.025, 0.975),
        method="linear",
    )
    first, median, third = np.quantile(
        learned_ratios.reshape(-1),
        (0.25, 0.5, 0.75),
        method="linear",
    )
    learned_results = tuple(result for entry in records for result in entry.learned)
    aggregate = M1LearnedAggregateStatistics(
        case_count=len(records),
        observation_count=learned_ratios.size,
        mean_time_ratio_to_uniform=float(np.mean(learned_ratios)),
        confidence_interval_95_lower=float(lower),
        confidence_interval_95_upper=float(upper),
        median_time_ratio_to_uniform=float(median),
        first_quartile_time_ratio_to_uniform=float(first),
        third_quartile_time_ratio_to_uniform=float(third),
        failure_rate=float(np.mean([not result.succeeded for result in learned_results])),
        fallback_rate=float(
            np.mean([result.fallback_used for result in learned_results])
        ),
    )
    return M1SplitStatistics(
        split=split,
        case_count=len(records),
        methods=cast(
            tuple[
                M1MethodStatistics,
                M1MethodStatistics,
                M1MethodStatistics,
                M1MethodStatistics,
                M1MethodStatistics,
                M1MethodStatistics,
                M1MethodStatistics,
                M1MethodStatistics,
            ],
            tuple(methods),
        ),
        learned_aggregate=aggregate,
    )


def _method_statistics(
    method: M1ExperimentMethod,
    seed: int | None,
    results: tuple[BaselineCaseResult | M1CaseResult, ...],
    uniform_seconds: np.ndarray,
) -> M1MethodStatistics:
    ratios = np.asarray(
        [
            result.timing.end_to_end_seconds / uniform_seconds[index]
            for index, result in enumerate(results)
        ],
        dtype=np.float64,
    )
    first, median, third = np.quantile(
        ratios,
        (0.25, 0.5, 0.75),
        method="linear",
    )
    compliance_ratios = np.asarray(
        [
            result.operational.final_compliance
            / result.uniform_reference_compliance
            for result in results
        ],
        dtype=np.float64,
    )
    return M1MethodStatistics(
        method=method,
        seed=seed,
        case_count=len(results),
        mean_time_ratio_to_uniform=float(np.mean(ratios)),
        median_time_ratio_to_uniform=float(median),
        first_quartile_time_ratio_to_uniform=float(first),
        third_quartile_time_ratio_to_uniform=float(third),
        failure_rate=float(np.mean([not result.succeeded for result in results])),
        fallback_rate=float(np.mean([result.fallback_used for result in results])),
        median_operational_iterations=float(
            np.median([result.operational.iterations for result in results])
        ),
        median_operational_compliance_ratio=float(np.median(compliance_ratios)),
        maximum_operational_volume_error=max(
            result.operational.physical_volume_error for result in results
        ),
    )


def _validate_index_materialization(
    index: M1EvaluationIndex,
    materialization: DatasetMaterializationIndex,
) -> None:
    if materialization.state != "complete" or any(
        isinstance(entry, MaterializationFailure) for entry in materialization.entries
    ):
        raise M1ExperimentError(
            "evaluation requires a complete zero-failure materialization"
        )
    if index.context.manifest_sha256 != materialization.manifest_sha256:
        raise M1ExperimentError("evaluation context does not match the materialization")
    expected = {
        sample.case.case_id: sample
        for sample in materialization.manifest.samples
        if sample.split in ("test", "ood")
    }
    for entry in index.entries:
        sample = expected.get(entry.case_id)
        if sample is None or sample.split != entry.split:
            raise M1ExperimentError("evaluation entry is not a held-out manifest sample")
    if index.state == "complete" and {
        entry.case_id for entry in index.entries
    } != set(expected):
        raise M1ExperimentError("complete evaluation must record every held-out case")


def _validate_append_only(
    previous: M1EvaluationIndex,
    current: M1EvaluationIndex,
) -> None:
    if previous.state == "complete":
        raise M1ExperimentError("complete evaluation index is immutable")
    current_entries = {entry.case_id: entry for entry in current.entries}
    for entry in previous.entries:
        if current_entries.get(entry.case_id) != entry:
            raise M1ExperimentError(
                "evaluation updates must preserve recorded outcomes"
            )


def _parse_m1_evaluation_index(contents: bytes) -> M1EvaluationIndex:
    try:
        index = M1EvaluationIndex.model_validate_json(contents)
    except ValidationError as error:
        raise M1ExperimentError("M1 evaluation index schema validation failed") from error
    if canonical_m1_evaluation_index_bytes(index) != contents:
        raise M1ExperimentError("M1 evaluation index is not canonical JSON")
    return index


def _canonical_json_bytes(payload: object) -> bytes:
    serialized = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return f"{serialized}\n".encode()
