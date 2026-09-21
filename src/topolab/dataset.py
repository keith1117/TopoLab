"""Versioned dataset manifest and leakage-safe split contracts."""

import hashlib
from collections.abc import Iterable
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from topolab.experiment import (
    INPUT_CHANNEL_NAMES,
    ExperimentCase,
    build_case_id,
    encode_case,
)
from topolab.problem import ContractModel, TopologyProblem

DATASET_MANIFEST_VERSION = "topolab.m0.dataset.v1"
DATASET_SAMPLE_VERSION = "topolab.m0.sample.v1"
SPLIT_CONTRACT_VERSION = "topolab.m0.split.v1"

type DatasetSplit = Literal["train", "validation", "test", "ood"]

_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_REVISION_PATTERN = r"^[0-9a-f]{40}$"


class DatasetEnvironment(ContractModel):
    """Non-sensitive locked runtime metadata for one dataset."""

    python_version: Annotated[str, Field(min_length=1)]
    numpy_version: Annotated[str, Field(min_length=1)]
    scipy_version: Annotated[str, Field(min_length=1)]
    lockfile_sha256: Annotated[str, Field(pattern=_SHA256_PATTERN)]


class DatasetSample(ContractModel):
    """One complete physical case and its immutable partition assignment."""

    sample_version: Literal["topolab.m0.sample.v1"] = "topolab.m0.sample.v1"
    case: ExperimentCase
    split: DatasetSplit
    load_scale: Annotated[float, Field(gt=0.0)]

    @classmethod
    def from_case(cls, case: ExperimentCase) -> "DatasetSample":
        encoded = encode_case(case)
        return cls(
            case=case,
            split=assign_case_split(case),
            load_scale=encoded.load_scale,
        )

    @model_validator(mode="after")
    def validate_derived_fields(self) -> "DatasetSample":
        expected_split = assign_case_split(self.case)
        if self.split != expected_split:
            raise ValueError("sample split does not match the frozen split contract")
        expected_scale = encode_case(self.case).load_scale
        if self.load_scale != expected_scale:
            raise ValueError("sample load_scale does not match the encoded case")
        return self


class DatasetSplitCounts(ContractModel):
    """Recorded population of every required M0 partition."""

    train: Annotated[int, Field(strict=True, gt=0)]
    validation: Annotated[int, Field(strict=True, gt=0)]
    test: Annotated[int, Field(strict=True, gt=0)]
    ood: Annotated[int, Field(strict=True, gt=0)]


class DatasetManifest(ContractModel):
    """One fixed-cohort M0 dataset plan with validated provenance and splits."""

    manifest_version: Literal["topolab.m0.dataset.v1"] = "topolab.m0.dataset.v1"
    case_schema_version: Literal["topolab.m0.case.v1"] = "topolab.m0.case.v1"
    generator_version: Literal["topolab.m0.generator.v1"] = (
        "topolab.m0.generator.v1"
    )
    solver_contract_version: Literal["topolab.simp.v1"] = "topolab.simp.v1"
    split_contract_version: Literal["topolab.m0.split.v1"] = "topolab.m0.split.v1"
    source_revision: Annotated[str, Field(pattern=_REVISION_PATTERN)]
    source_tree_clean: Literal[True] = True
    environment: DatasetEnvironment
    input_channels: tuple[str, ...] = INPUT_CHANNEL_NAMES
    tensor_dtype: Literal["float32"] = "float32"
    tensor_axis_order: Literal["channel,z,y,x"] = "channel,z,y,x"
    split_counts: DatasetSplitCounts
    samples: Annotated[tuple[DatasetSample, ...], Field(min_length=1)]

    @classmethod
    def from_cases(
        cls,
        cases: Iterable[ExperimentCase],
        *,
        source_revision: str,
        environment: DatasetEnvironment,
    ) -> "DatasetManifest":
        samples = tuple(DatasetSample.from_case(case) for case in cases)
        return cls(
            source_revision=source_revision,
            environment=environment,
            split_counts=_split_counts(samples),
            samples=samples,
        )

    @field_validator("input_channels", mode="after")
    @classmethod
    def validate_input_channels(cls, channels: tuple[str, ...]) -> tuple[str, ...]:
        if channels != INPUT_CHANNEL_NAMES:
            raise ValueError("input_channels must match the frozen M0 channel order")
        return channels

    @field_validator("samples", mode="after")
    @classmethod
    def sort_samples(cls, samples: tuple[DatasetSample, ...]) -> tuple[DatasetSample, ...]:
        return tuple(sorted(samples, key=lambda sample: sample.case.case_id))

    @model_validator(mode="after")
    def validate_dataset(self) -> "DatasetManifest":
        case_ids = tuple(sample.case.case_id for sample in self.samples)
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("dataset samples must have unique case IDs")
        expected_counts = _split_counts(self.samples)
        if self.split_counts != expected_counts:
            raise ValueError("split_counts do not match dataset samples")

        cohort = _cohort_signature(self.samples[0].case)
        if any(_cohort_signature(sample.case) != cohort for sample in self.samples[1:]):
            raise ValueError("all dataset samples must belong to one fixed-shape cohort")

        id_cases = set(case_ids)
        for sample in self.samples:
            if sample.split == "ood" and _id_counterpart_case_id(sample.case) not in id_cases:
                raise ValueError("every OOD case must have its matched ID counterpart")
        return self


def assign_case_split(case: ExperimentCase) -> DatasetSplit:
    """Apply the frozen direction OOD rule and deterministic ID hash split."""

    directions = {load.direction for load in case.problem.loads}
    if directions == {"z"}:
        return "ood"
    if directions != {"y"}:
        raise ValueError(
            "m0.v1 cases must use only y-directed ID loads or z-directed OOD loads"
        )

    digest = hashlib.sha256(
        f"{SPLIT_CONTRACT_VERSION}:{case.case_id}".encode()
    ).hexdigest()
    bucket = int(digest[:8], 16) % 100
    if bucket < 80:
        return "train"
    if bucket < 90:
        return "validation"
    return "test"


def _split_counts(samples: tuple[DatasetSample, ...]) -> DatasetSplitCounts:
    counts = {split: 0 for split in ("train", "validation", "test", "ood")}
    for sample in samples:
        counts[sample.split] += 1
    return DatasetSplitCounts.model_validate(counts)


def _cohort_signature(case: ExperimentCase) -> tuple[object, ...]:
    problem = case.problem
    settings = problem.optimization
    return (
        problem.mesh.element_counts,
        problem.mesh.lengths,
        problem.material.solid_modulus,
        problem.material.minimum_modulus,
        problem.material.poisson_ratio,
        settings.filter_radius,
        settings.penalty,
        settings.minimum_density,
        settings.move_limit,
        settings.convergence_tolerance,
        settings.max_iterations,
    )


def _id_counterpart_case_id(case: ExperimentCase) -> str:
    payload = case.problem.model_dump(mode="json")
    loads = payload["loads"]
    if not isinstance(loads, list):  # pragma: no cover - Pydantic guarantees this
        raise TypeError("problem loads must serialize as a list")
    for load in loads:
        if not isinstance(load, dict):  # pragma: no cover - Pydantic guarantees this
            raise TypeError("problem loads must serialize as objects")
        load["direction"] = "y"
    counterpart = TopologyProblem.model_validate(payload)
    return build_case_id(counterpart)
