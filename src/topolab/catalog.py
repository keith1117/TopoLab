"""Bounded deterministic case catalog for the frozen M0 dataset contract."""

import hashlib
import json
from collections.abc import Iterable
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from topolab.dataset import DatasetEnvironment, DatasetManifest
from topolab.experiment import ExperimentCase
from topolab.problem import (
    ContractModel,
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)

CASE_CATALOG_VERSION = "topolab.m0.catalog.v1"
CASE_CATALOG_ID_PREFIX = "tlcatalog-v1-"
M0_CASE_CATALOG_ID = (
    "tlcatalog-v1-e532ad3d9de3083918e1ab074e7ba3b88a254d0b6729af508f96959ea1eedc3d"
)

_CATALOG_ID_PATTERN = rf"^{CASE_CATALOG_ID_PREFIX}[0-9a-f]{{64}}$"
_ELEMENT_COUNTS = (12, 6, 3)
_LENGTHS = (12.0, 6.0, 3.0)
_LOAD_Y_INDICES = (0, 2, 4, 6)
_LOAD_Z_INDICES = (0, 1, 2, 3)
_VOLUME_FRACTIONS = (0.2, 0.3, 0.4, 0.5, 0.6)


class CaseCatalog(ContractModel):
    """One immutable, content-identified collection of complete physical cases."""

    catalog_version: Literal["topolab.m0.catalog.v1"] = "topolab.m0.catalog.v1"
    catalog_id: Annotated[str, Field(pattern=_CATALOG_ID_PATTERN)]
    cases: Annotated[tuple[ExperimentCase, ...], Field(min_length=1)]

    @classmethod
    def from_cases(cls, cases: Iterable[ExperimentCase]) -> "CaseCatalog":
        """Build a catalog after canonical case-ID ordering."""

        normalized = tuple(sorted(cases, key=lambda case: case.case_id))
        return cls(catalog_id=build_catalog_id(normalized), cases=normalized)

    @field_validator("cases", mode="after")
    @classmethod
    def sort_cases(cls, cases: tuple[ExperimentCase, ...]) -> tuple[ExperimentCase, ...]:
        return tuple(sorted(cases, key=lambda case: case.case_id))

    @model_validator(mode="after")
    def validate_identity(self) -> "CaseCatalog":
        case_ids = tuple(case.case_id for case in self.cases)
        if len(set(case_ids)) != len(case_ids):
            raise ValueError("catalog cases must have unique case IDs")
        expected = build_catalog_id(self.cases)
        if self.catalog_id != expected:
            raise ValueError("catalog_id does not match the canonical case collection")
        return self

    def canonical_identity_json(self) -> str:
        """Return the exact canonical JSON hashed by ``catalog_id``."""

        return canonical_catalog_json(self.cases)

    def build_manifest(
        self,
        *,
        source_revision: str,
        environment: DatasetEnvironment,
    ) -> DatasetManifest:
        """Build the validated dataset manifest for this catalog."""

        return DatasetManifest.from_cases(
            self.cases,
            source_revision=source_revision,
            environment=environment,
        )


def canonical_catalog_json(cases: Iterable[ExperimentCase]) -> str:
    """Serialize a case collection deterministically for catalog identity."""

    normalized = tuple(sorted(cases, key=lambda case: case.case_id))
    case_ids = tuple(case.case_id for case in normalized)
    if not case_ids:
        raise ValueError("catalog must contain at least one case")
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("catalog cases must have unique case IDs")
    payload = {
        "case_ids": case_ids,
        "catalog_version": CASE_CATALOG_VERSION,
    }
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def build_catalog_id(cases: Iterable[ExperimentCase]) -> str:
    """Return the stable SHA-256 identifier for one canonical case catalog."""

    digest = hashlib.sha256(canonical_catalog_json(cases).encode("utf-8")).hexdigest()
    return f"{CASE_CATALOG_ID_PREFIX}{digest}"


def build_m0_case_catalog() -> CaseCatalog:
    """Enumerate the exact bounded M0 v1 ID and matched-OOD case population."""

    cases = (
        _build_case(y_index, z_index, volume_fraction, direction)
        for y_index in _LOAD_Y_INDICES
        for z_index in _LOAD_Z_INDICES
        for volume_fraction in _VOLUME_FRACTIONS
        for direction in ("y", "z")
    )
    catalog = CaseCatalog.from_cases(cases)
    if catalog.catalog_id != M0_CASE_CATALOG_ID:
        raise RuntimeError("the M0 v1 case catalog changed without a version update")
    return catalog


def _build_case(
    y_index: int,
    z_index: int,
    volume_fraction: float,
    direction: Literal["y", "z"],
) -> ExperimentCase:
    nx, ny, _ = _ELEMENT_COUNTS
    loaded_node = nx + (nx + 1) * (y_index + (ny + 1) * z_index)
    problem = TopologyProblem(
        mesh=MeshDefinition(
            element_counts=_ELEMENT_COUNTS,
            lengths=_LENGTHS,
        ),
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
            max_iterations=100,
        ),
    )
    return ExperimentCase.from_problem(problem)
