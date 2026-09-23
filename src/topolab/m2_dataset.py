"""Frozen catalog and exposure-aware dataset contract for the M2 follow-up."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from topolab.catalog import build_m0_case_catalog
from topolab.dataset import DatasetEnvironment
from topolab.experiment import (
    INPUT_CHANNEL_NAMES,
    ExperimentCase,
    build_case_id,
    encode_case,
)
from topolab.problem import (
    ContractModel,
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)

M2_CASE_CATALOG_VERSION = "topolab.m2.catalog.v1"
M2_CASE_CATALOG_ID_PREFIX = "tlcatalog-m2-v1-"
M2_CASE_CATALOG_ID = (
    "tlcatalog-m2-v1-af5b7fcffed5a070c3fc370a318605d3652e98c57b706f432203a7fd173fea12"
)
M2_DATASET_MANIFEST_VERSION = "topolab.m2.dataset.v1"
M2_DATASET_SAMPLE_VERSION = "topolab.m2.sample.v1"
M2_SPLIT_CONTRACT_VERSION = "topolab.m2.split.v1"

type M2DatasetSplit = Literal["train", "validation", "test", "ood"]

_SHA256_PATTERN = r"^[0-9a-f]{64}$"
_REVISION_PATTERN = r"^[0-9a-f]{40}$"
_CATALOG_ID_PATTERN = rf"^{M2_CASE_CATALOG_ID_PREFIX}[0-9a-f]{{64}}$"
_ELEMENT_COUNTS = (12, 6, 3)
_LENGTHS = (12.0, 6.0, 3.0)
_LOAD_Y_INDICES = tuple(range(7))
_LOAD_Z_INDICES = tuple(range(4))
_VOLUME_FRACTIONS = (0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6)
_ID_DIRECTIONS: tuple[Literal["y"], Literal["z"]] = ("y", "z")
_OOD_DIRECTION: Literal["x"] = "x"
_VALIDATION_CASES_PER_STRATUM = 2
_TEST_CASES_PER_STRATUM = 2


class M2CaseCatalog(ContractModel):
    """One immutable, content-identified M2 physical-case collection."""

    catalog_version: Literal["topolab.m2.catalog.v1"] = "topolab.m2.catalog.v1"
    catalog_id: Annotated[str, Field(pattern=_CATALOG_ID_PATTERN)]
    cases: Annotated[tuple[ExperimentCase, ...], Field(min_length=1)]

    @classmethod
    def from_cases(cls, cases: Iterable[ExperimentCase]) -> M2CaseCatalog:
        """Build a catalog after canonical case-ID ordering."""

        normalized = tuple(sorted(cases, key=lambda case: case.case_id))
        return cls(catalog_id=build_m2_catalog_id(normalized), cases=normalized)

    @field_validator("cases", mode="after")
    @classmethod
    def sort_cases(cls, cases: tuple[ExperimentCase, ...]) -> tuple[ExperimentCase, ...]:
        return tuple(sorted(cases, key=lambda case: case.case_id))

    @model_validator(mode="after")
    def validate_identity(self) -> M2CaseCatalog:
        case_ids = tuple(case.case_id for case in self.cases)
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("M2 catalog cases must have unique case IDs")
        if self.catalog_id != build_m2_catalog_id(self.cases):
            raise ValueError("M2 catalog_id does not match the canonical cases")
        return self

    def canonical_identity_json(self) -> str:
        """Return the canonical JSON hashed by the catalog identity."""

        return canonical_m2_catalog_json(self.cases)

    def build_manifest(
        self,
        *,
        source_revision: str,
        environment: DatasetEnvironment,
    ) -> M2DatasetManifest:
        """Build the exact exposure-aware M2 dataset manifest."""

        return M2DatasetManifest.from_catalog(
            self,
            source_revision=source_revision,
            environment=environment,
        )


class M2DatasetSample(ContractModel):
    """One M2 physical case and its frozen partition assignment."""

    sample_version: Literal["topolab.m2.sample.v1"] = "topolab.m2.sample.v1"
    case: ExperimentCase
    split: M2DatasetSplit
    load_scale: Annotated[float, Field(gt=0.0)]

    @model_validator(mode="after")
    def validate_load_scale(self) -> M2DatasetSample:
        if self.load_scale != encode_case(self.case).load_scale:
            raise ValueError("M2 sample load_scale does not match the encoded case")
        return self


class M2DatasetSplitCounts(ContractModel):
    """Recorded population of every required M2 partition."""

    train: Annotated[int, Field(strict=True, gt=0)]
    validation: Annotated[int, Field(strict=True, gt=0)]
    test: Annotated[int, Field(strict=True, gt=0)]
    ood: Annotated[int, Field(strict=True, gt=0)]


class M2DatasetManifest(ContractModel):
    """Exact M2 catalog plus its exposure-aware leakage boundary."""

    manifest_version: Literal["topolab.m2.dataset.v1"] = "topolab.m2.dataset.v1"
    case_schema_version: Literal["topolab.m0.case.v1"] = "topolab.m0.case.v1"
    generator_version: Literal["topolab.m0.generator.v1"] = "topolab.m0.generator.v1"
    solver_contract_version: Literal["topolab.simp.v1"] = "topolab.simp.v1"
    split_contract_version: Literal["topolab.m2.split.v1"] = "topolab.m2.split.v1"
    catalog_id: Literal[
        "tlcatalog-m2-v1-af5b7fcffed5a070c3fc370a318605d3652e98c57b706f432203a7fd173fea12"
    ] = "tlcatalog-m2-v1-af5b7fcffed5a070c3fc370a318605d3652e98c57b706f432203a7fd173fea12"
    source_revision: Annotated[str, Field(pattern=_REVISION_PATTERN)]
    source_tree_clean: Literal[True] = True
    environment: DatasetEnvironment
    input_channels: tuple[str, ...] = INPUT_CHANNEL_NAMES
    tensor_dtype: Literal["float32"] = "float32"
    tensor_axis_order: Literal["channel,z,y,x"] = "channel,z,y,x"
    split_counts: M2DatasetSplitCounts
    samples: Annotated[tuple[M2DatasetSample, ...], Field(min_length=1)]

    @classmethod
    def from_catalog(
        cls,
        catalog: M2CaseCatalog,
        *,
        source_revision: str,
        environment: DatasetEnvironment,
    ) -> M2DatasetManifest:
        """Build the manifest after independently deriving every split."""

        if catalog.catalog_id != M2_CASE_CATALOG_ID:
            raise ValueError("M2 manifest requires the exact frozen catalog")
        assignments = assign_m2_case_splits(catalog)
        samples = tuple(
            M2DatasetSample(
                case=case,
                split=assignments[case.case_id],
                load_scale=encode_case(case).load_scale,
            )
            for case in catalog.cases
        )
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
            raise ValueError("input_channels must match the frozen M2 channel order")
        return channels

    @field_validator("samples", mode="after")
    @classmethod
    def sort_samples(cls, samples: tuple[M2DatasetSample, ...]) -> tuple[M2DatasetSample, ...]:
        return tuple(sorted(samples, key=lambda sample: sample.case.case_id))

    @model_validator(mode="after")
    def validate_dataset(self) -> M2DatasetManifest:
        cases = tuple(sample.case for sample in self.samples)
        catalog = M2CaseCatalog.from_cases(cases)
        if catalog.catalog_id != M2_CASE_CATALOG_ID:
            raise ValueError("M2 manifest samples do not match the frozen catalog")
        expected = assign_m2_case_splits(catalog)
        if any(sample.split != expected[sample.case.case_id] for sample in self.samples):
            raise ValueError("M2 sample split does not match the frozen split")
        if self.split_counts != _split_counts(self.samples):
            raise ValueError("M2 split_counts do not match dataset samples")
        case_ids = {case.case_id for case in cases}
        if any(
            _case_direction(case) == _OOD_DIRECTION
            and _id_counterpart_case_id(case) not in case_ids
            for case in cases
        ):
            raise ValueError("every M2 OOD case must have its matched ID counterpart")
        return self


def canonical_m2_catalog_json(cases: Iterable[ExperimentCase]) -> str:
    """Serialize one M2 catalog identity deterministically."""

    normalized = tuple(sorted(cases, key=lambda case: case.case_id))
    case_ids = tuple(case.case_id for case in normalized)
    if not case_ids:
        raise ValueError("M2 catalog must contain at least one case")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("M2 catalog cases must have unique case IDs")
    return json.dumps(
        {
            "case_ids": case_ids,
            "catalog_version": M2_CASE_CATALOG_VERSION,
        },
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def build_m2_catalog_id(cases: Iterable[ExperimentCase]) -> str:
    """Return the content-derived identity of one canonical M2 catalog."""

    digest = hashlib.sha256(canonical_m2_catalog_json(cases).encode("utf-8")).hexdigest()
    return f"{M2_CASE_CATALOG_ID_PREFIX}{digest}"


def build_m2_case_catalog() -> M2CaseCatalog:
    """Enumerate and verify the exact bounded M2 physical-case population."""

    catalog = M2CaseCatalog.from_cases(_enumerate_m2_cases())
    if catalog.catalog_id != M2_CASE_CATALOG_ID:
        raise RuntimeError("the M2 case catalog changed without a version update")
    return catalog


def assign_m2_case_splits(catalog: M2CaseCatalog) -> dict[str, M2DatasetSplit]:
    """Derive the frozen exposure-aware, stratified split for the exact catalog."""

    if catalog.catalog_id != M2_CASE_CATALOG_ID:
        raise ValueError("M2 split assignment requires the exact frozen catalog")
    exposed = {case.case_id for case in build_m0_case_catalog().cases}
    assignments: dict[str, M2DatasetSplit] = {}
    strata: defaultdict[tuple[str, float], list[ExperimentCase]] = defaultdict(list)

    for case in catalog.cases:
        direction = _case_direction(case)
        if direction == _OOD_DIRECTION:
            assignments[case.case_id] = "ood"
        elif case.case_id in exposed:
            assignments[case.case_id] = "train"
        else:
            strata[(direction, case.problem.optimization.volume_fraction)].append(case)

    expected_strata = {
        (direction, volume_fraction)
        for direction in _ID_DIRECTIONS
        for volume_fraction in _VOLUME_FRACTIONS
    }
    if set(strata) != expected_strata:
        raise ValueError("M2 non-exposed cases do not cover every frozen stratum")

    for cases in strata.values():
        ordered = sorted(cases, key=lambda case: (_split_digest(case), case.case_id))
        validation_end = _VALIDATION_CASES_PER_STRATUM
        test_end = validation_end + _TEST_CASES_PER_STRATUM
        if len(ordered) < test_end:
            raise ValueError("M2 stratum is too small for the frozen split")
        for case in ordered[:validation_end]:
            assignments[case.case_id] = "validation"
        for case in ordered[validation_end:test_end]:
            assignments[case.case_id] = "test"
        for case in ordered[test_end:]:
            assignments[case.case_id] = "train"

    if len(assignments) != len(catalog.cases):
        raise ValueError("M2 split assignment did not cover the complete catalog")
    counts = _assignment_counts(assignments.values())
    if counts != {"train": 432, "validation": 36, "test": 36, "ood": 252}:
        raise ValueError("M2 split assignment changed its frozen counts")
    return assignments


def _enumerate_m2_cases() -> Iterable[ExperimentCase]:
    return (
        _build_case(y_index, z_index, volume_fraction, direction)
        for y_index in _LOAD_Y_INDICES
        for z_index in _LOAD_Z_INDICES
        for volume_fraction in _VOLUME_FRACTIONS
        for direction in (*_ID_DIRECTIONS, _OOD_DIRECTION)
    )


def _build_case(
    y_index: int,
    z_index: int,
    volume_fraction: float,
    direction: Literal["x", "y", "z"],
) -> ExperimentCase:
    nx, ny, _ = _ELEMENT_COUNTS
    loaded_node = nx + (nx + 1) * (y_index + (ny + 1) * z_index)
    return ExperimentCase.from_problem(
        TopologyProblem(
            mesh=MeshDefinition(element_counts=_ELEMENT_COUNTS, lengths=_LENGTHS),
            material=MaterialDefinition(
                solid_modulus=1000.0,
                minimum_modulus=1.0,
                poisson_ratio=0.3,
            ),
            supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
            loads=(
                PointLoadDefinition(
                    node=loaded_node,
                    direction=direction,
                    magnitude=-1.0,
                ),
            ),
            optimization=OptimizationDefinition(
                volume_fraction=volume_fraction,
                filter_radius=1.5,
                penalty=3.0,
                minimum_density=0.05,
                move_limit=0.2,
                convergence_tolerance=0.01,
                max_iterations=120,
            ),
        )
    )


def _case_direction(case: ExperimentCase) -> Literal["x", "y", "z"]:
    if len(case.problem.loads) != 1:
        raise ValueError("M2 cases must contain exactly one point load")
    load = case.problem.loads[0]
    if not isinstance(load, PointLoadDefinition) or load.direction not in {
        "x",
        "y",
        "z",
    }:
        raise ValueError("M2 cases must contain one axis-directed point load")
    return load.direction


def _split_digest(case: ExperimentCase) -> str:
    return hashlib.sha256(f"{M2_SPLIT_CONTRACT_VERSION}:{case.case_id}".encode()).hexdigest()


def _split_counts(samples: tuple[M2DatasetSample, ...]) -> M2DatasetSplitCounts:
    counts = _assignment_counts(sample.split for sample in samples)
    return M2DatasetSplitCounts.model_validate(counts)


def _assignment_counts(
    splits: Iterable[M2DatasetSplit],
) -> dict[M2DatasetSplit, int]:
    counts: dict[M2DatasetSplit, int] = {
        "train": 0,
        "validation": 0,
        "test": 0,
        "ood": 0,
    }
    for split in splits:
        counts[split] += 1
    return counts


def _id_counterpart_case_id(case: ExperimentCase) -> str:
    payload = case.problem.model_dump(mode="json")
    loads = payload["loads"]
    if not isinstance(loads, list):  # pragma: no cover - Pydantic guarantees this
        raise TypeError("problem loads must serialize as a list")
    for load in loads:
        if not isinstance(load, dict):  # pragma: no cover - Pydantic guarantees this
            raise TypeError("problem loads must serialize as objects")
        load["direction"] = "y"
    return build_case_id(TopologyProblem.model_validate(payload))
