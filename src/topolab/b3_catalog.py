"""Frozen B3 case metadata and historical exposure, without artifact or solver I/O."""

import hashlib
import json
from collections import defaultdict
from collections.abc import Iterable
from functools import cache
from typing import Annotated, Literal

from pydantic import ConfigDict, Field, model_validator

from topolab.catalog import build_m0_case_catalog
from topolab.experiment import ExperimentCase
from topolab.m2_dataset import assign_m2_case_splits, build_m2_case_catalog
from topolab.problem import (
    ContractModel,
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)

B3_CATALOG_SHA256 = "441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c"
B3_EXPOSURE_SHA256 = "5ab3f2d57d390b804c4e5157f41f206155a4bee7d31a6c4edcbc614c44e1a7b7"
B3_CONTRACT_SHA256 = "452a6c1b3664e007a258a914877c935f333c1823f3ec3d977ee0d09583129af8"

type B3Role = Literal["train", "fit_validation", "screen_validation", "final_id", "final_ood"]
type B3TrainingSet = Literal["base", "expanded", "specialist"]
type ExposureSource = Literal[
    "m0_v1", "m0_v2_m1", "m2_all", "m3_final_design", "b2_development_and_reserved"
]
type Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
type CaseId = Annotated[str, Field(pattern=r"^tlcase-v1-[0-9a-f]{64}$")]

_TRAINING_ORDER: tuple[B3TrainingSet, ...] = ("base", "expanded", "specialist")
_POSITIONS = tuple((y, z) for z in (1, 2) for y in (1, 2, 3, 4, 5))


def canonical_metadata_bytes(payload: object) -> bytes:
    """Compact sorted-key finite ASCII JSON with exactly one terminal newline."""

    return (
        json.dumps(
            payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
        )
        + "\n"
    ).encode("ascii")


def physical_fingerprint(case: ExperimentCase) -> str:
    """Normalize the complete problem and ignore only the iteration budget."""

    verified = ExperimentCase.model_validate(case.model_dump(mode="json"))
    payload = verified.problem.model_dump(mode="json")
    del payload["optimization"]["max_iterations"]
    return hashlib.sha256(canonical_metadata_bytes(payload)).hexdigest()


class B3CatalogEntry(ContractModel):
    """One verified case and its frozen role, source link, and memberships."""

    model_config = ConfigDict(revalidate_instances="always")

    case: ExperimentCase
    physical_fingerprint: Sha256
    role: B3Role
    source_case_id: CaseId | None = None
    training_sets: tuple[B3TrainingSet, ...] = ()

    @model_validator(mode="after")
    def validate_boundary(self) -> "B3CatalogEntry":
        if self.physical_fingerprint != physical_fingerprint(self.case):
            raise ValueError("physical_fingerprint does not match the normalized problem")
        if self.case.problem.optimization.max_iterations != 360:
            raise ValueError("B3 cases require the frozen 360-update budget")
        if self.role == "train":
            if not self.training_sets or self.training_sets != tuple(
                name for name in _TRAINING_ORDER if name in self.training_sets
            ):
                raise ValueError("train memberships must be unique and in frozen order")
            if self.source_case_id != _with_budget(self.case, 240).case_id:
                raise ValueError("source_case_id must identify the exact 240-update source")
        elif self.source_case_id is not None or self.training_sets:
            raise ValueError("non-train roles cannot have source links or train memberships")
        return self

    def identity_entry(self) -> dict[str, object]:
        return {
            "case_id": self.case.case_id,
            "role": self.role,
            "source_case_id": self.source_case_id,
            "training_sets": self.training_sets,
        }


class B3ExposureEntry(ContractModel):
    """All known case identities and sources for one physical fingerprint."""

    physical_fingerprint: Sha256
    case_ids: Annotated[tuple[CaseId, ...], Field(min_length=1)]
    sources: Annotated[tuple[ExposureSource, ...], Field(min_length=1)]

    @model_validator(mode="after")
    def validate_order(self) -> "B3ExposureEntry":
        if self.case_ids != tuple(sorted(set(self.case_ids))):
            raise ValueError("exposure case_ids must be sorted and unique")
        if self.sources != tuple(sorted(set(self.sources))):
            raise ValueError("exposure sources must be sorted and unique")
        return self


class B3ExposureLedger(ContractModel):
    """Exact immutable historical ledger; no label/outcome information is stored."""

    version: Literal["topolab.b3.exposure.v1"] = "topolab.b3.exposure.v1"
    entries: tuple[B3ExposureEntry, ...]

    @model_validator(mode="after")
    def validate_frozen_ledger(self) -> "B3ExposureLedger":
        fingerprints = tuple(entry.physical_fingerprint for entry in self.entries)
        case_ids = [case_id for entry in self.entries for case_id in entry.case_ids]
        if fingerprints != tuple(sorted(set(fingerprints))):
            raise ValueError("exposure fingerprints must be sorted and unique")
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("a historical case ID cannot belong to multiple fingerprints")
        if hashlib.sha256(self.canonical_identity_bytes()).hexdigest() != B3_EXPOSURE_SHA256:
            raise ValueError("exposure ledger differs from the frozen B3 hash")
        return self

    def canonical_identity_bytes(self) -> bytes:
        return canonical_metadata_bytes(self.model_dump(mode="json"))

    def contains(self, case: ExperimentCase) -> bool:
        fingerprint = physical_fingerprint(case)
        return any(entry.physical_fingerprint == fingerprint for entry in self.entries)


class B3CaseCatalog(ContractModel):
    """The complete frozen 752-case population, checked on construction and read."""

    catalog_version: Literal["topolab.b3.catalog.v1"] = "topolab.b3.catalog.v1"
    entries: tuple[B3CatalogEntry, ...]

    @model_validator(mode="after")
    def validate_frozen_catalog(self) -> "B3CaseCatalog":
        case_ids = tuple(entry.case.case_id for entry in self.entries)
        if case_ids != tuple(sorted(set(case_ids))):
            raise ValueError("B3 catalog case IDs must be sorted and unique")
        fingerprints = tuple(entry.physical_fingerprint for entry in self.entries)
        if len(set(fingerprints)) != len(fingerprints):
            raise ValueError("B3 roles cannot share physical fingerprints or budget variants")
        if hashlib.sha256(self.canonical_identity_bytes()).hexdigest() != B3_CATALOG_SHA256:
            raise ValueError("catalog differs from the frozen B3 hash")
        exposed = {entry.physical_fingerprint for entry in build_b3_exposure_ledger().entries}
        for entry in self.entries:
            if (entry.physical_fingerprint in exposed) != (entry.role == "train"):
                raise ValueError("B3 role violates the historical exposure boundary")
        return self

    def canonical_identity_bytes(self) -> bytes:
        return canonical_metadata_bytes(
            {
                "catalog_version": self.catalog_version,
                "entries": [e.identity_entry() for e in self.entries],
            }
        )

    def for_role(self, role: B3Role) -> tuple[B3CatalogEntry, ...]:
        return tuple(entry for entry in self.entries if entry.role == role)

    def for_training_set(self, membership: B3TrainingSet) -> tuple[B3CatalogEntry, ...]:
        return tuple(entry for entry in self.entries if membership in entry.training_sets)


@cache
def build_b3_case_catalog() -> B3CaseCatalog:
    """Rebuild the frozen program using metadata only, without filesystem writes."""

    entries = []
    for source, memberships in _training_sources():
        case = _with_budget(source, 360)
        entries.append(
            B3CatalogEntry(
                case=case,
                physical_fingerprint=physical_fingerprint(case),
                role="train",
                source_case_id=source.case_id,
                training_sets=memberships,
            )
        )
    grids: tuple[tuple[B3Role, tuple[float, ...], tuple[tuple[int, int], ...]], ...] = (
        ("fit_validation", (0.3271, 0.4611, 0.5371, 0.5951), ((1, 2), (4, 1))),
        ("screen_validation", (0.3291, 0.4631, 0.5351, 0.5931), ((2, 1), (3, 2), (5, 2))),
        (
            "final_id",
            (0.3237, 0.4597, 0.5337, 0.5917),
            ((1, 1), (2, 2), (3, 1), (4, 2), (5, 1), (5, 2)),
        ),
        (
            "final_ood",
            (0.3237, 0.4597, 0.5337, 0.5917),
            ((1, 1), (2, 2), (3, 1), (4, 2), (5, 1), (5, 2)),
        ),
    )
    for role, volumes, positions in grids:
        for case in _grid(volumes, positions, 360, ("x",) if role == "final_ood" else ("y", "z")):
            entries.append(
                B3CatalogEntry(
                    case=case, role=role, physical_fingerprint=physical_fingerprint(case)
                )
            )
    return B3CaseCatalog(entries=tuple(sorted(entries, key=lambda e: e.case.case_id)))


@cache
def build_b3_exposure_ledger() -> B3ExposureLedger:
    """Rebuild all historical definitions, including failed and reserved B2 cohorts."""

    m0 = build_m0_case_catalog().cases
    sources: dict[ExposureSource, tuple[ExperimentCase, ...]] = {
        "m0_v1": tuple(_with_budget(case, 100) for case in m0),
        "m0_v2_m1": m0,
        "m2_all": build_m2_case_catalog().cases,
        "m3_final_design": _m3_final_cases(),
        "b2_development_and_reserved": _b2_exposed_cases(),
    }
    case_ids: defaultdict[str, set[str]] = defaultdict(set)
    memberships: defaultdict[str, set[ExposureSource]] = defaultdict(set)
    for source, cases in sources.items():
        for case in cases:
            fingerprint = physical_fingerprint(case)
            case_ids[fingerprint].add(case.case_id)
            memberships[fingerprint].add(source)
    return B3ExposureLedger(
        entries=tuple(
            B3ExposureEntry(
                physical_fingerprint=fp,
                case_ids=tuple(sorted(ids)),
                sources=tuple(sorted(memberships[fp])),
            )
            for fp, ids in sorted(case_ids.items())
        )
    )


def _with_budget(case: ExperimentCase, budget: int) -> ExperimentCase:
    payload = case.problem.model_dump(mode="json")
    payload["optimization"]["max_iterations"] = budget
    return ExperimentCase.from_problem(TopologyProblem.model_validate(payload))


def _cantilever_case(
    volume: float, direction: Literal["x", "y", "z"], y: int, z: int, large: bool, budget: int
) -> ExperimentCase:
    nx, ny, nz = (24, 12, 6) if large else (12, 6, 3)
    if large:
        y, z = 2 * y, 2 * z
    return ExperimentCase.from_problem(
        TopologyProblem(
            mesh=MeshDefinition(element_counts=(nx, ny, nz), lengths=(12.0, 6.0, 3.0)),
            material=MaterialDefinition(
                solid_modulus=1000.0, minimum_modulus=1.0, poisson_ratio=0.3
            ),
            supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
            loads=(
                PointLoadDefinition(
                    node=nx + (nx + 1) * (y + (ny + 1) * z), direction=direction, magnitude=-1.0
                ),
            ),
            optimization=OptimizationDefinition(
                volume_fraction=volume,
                filter_radius=1.5,
                penalty=3.0,
                minimum_density=0.05,
                move_limit=0.2,
                convergence_tolerance=0.01,
                max_iterations=budget,
            ),
        )
    )


def _grid(
    volumes: Iterable[float],
    positions: Iterable[tuple[int, int]],
    budget: int,
    directions: tuple[Literal["x", "y", "z"], ...] = ("y", "z"),
    scales: tuple[bool, ...] = (False, True),
) -> tuple[ExperimentCase, ...]:
    return tuple(
        _cantilever_case(vol, direction, y, z, large, budget)
        for vol in volumes
        for y, z in positions
        for direction in directions
        for large in scales
    )


@cache
def _base_sources() -> tuple[ExperimentCase, ...]:
    """Exact B2.4 train selection: 432 small plus two large per M2 train stratum."""

    catalog = build_m2_case_catalog()
    splits = assign_m2_case_splits(catalog)
    strata: defaultdict[tuple[str, float], list[ExperimentCase]] = defaultdict(list)
    for case in catalog.cases:
        if splits[case.case_id] == "train":
            strata[
                (str(case.problem.loads[0].direction), case.problem.optimization.volume_fraction)
            ].append(case)
    sources = [_with_budget(case, 240) for cases in strata.values() for case in cases]
    for cases in strata.values():
        for case in sorted(cases, key=lambda c: c.case_id)[:2]:
            load = case.problem.loads[0]
            assert isinstance(load, PointLoadDefinition)
            z, y = divmod((load.node - 12) // 13, 7)
            direction: Literal["y", "z"] = "y" if load.direction == "y" else "z"
            sources.append(
                _cantilever_case(
                    case.problem.optimization.volume_fraction, direction, y, z, True, 240
                )
            )
    return tuple(sorted(sources, key=lambda c: c.case_id))


def _training_sources() -> tuple[tuple[ExperimentCase, tuple[B3TrainingSet, ...]], ...]:
    return (
        *((case, _TRAINING_ORDER) for case in _base_sources()),
        *(
            (case, ("specialist",))
            for case in _grid((0.5585, 0.5985), _POSITIONS, 240, ("y",), (True,))
        ),
        *(
            (case, ("expanded",))
            for case in _grid((0.5175, 0.5425), _POSITIONS, 240, scales=(True,))
        ),
    )


def _m3_final_cases() -> tuple[ExperimentCase, ...]:
    positions = {
        0.225: ((2, 1), (4, 3), (1, 1), (6, 2)),
        0.275: ((4, 2), (4, 0), (2, 3), (0, 1)),
        0.325: ((0, 3), (3, 2), (3, 0), (4, 0)),
        0.375: ((3, 2), (0, 1), (6, 0), (6, 1)),
        0.425: ((1, 3), (2, 3), (2, 2), (6, 1)),
        0.475: ((6, 2), (2, 2), (2, 3), (4, 3)),
        0.525: ((3, 1), (6, 3), (3, 0), (4, 1)),
        0.575: ((6, 0), (6, 1), (1, 2), (0, 2)),
    }
    final = tuple(
        case
        for vol, nodes in positions.items()
        for case in _grid((vol,), nodes, 120, ("x", "y", "z"), (False,))
    )
    m2 = build_m2_case_catalog()
    splits = assign_m2_case_splits(m2)
    entries = [
        {"case_id": c.case_id, "split": splits[c.case_id]}
        for c in m2.cases
        if splits[c.case_id] in ("train", "validation")
    ]
    entries.extend(
        {"case_id": c.case_id, "split": "ood" if c.problem.loads[0].direction == "x" else "test"}
        for c in final
    )
    payload = {
        "catalog_version": "topolab.m3.catalog.v1",
        "entries": sorted(entries, key=lambda e: e["case_id"]),
    }
    if hashlib.sha256(canonical_metadata_bytes(payload)).hexdigest() != (
        "ddb0a0b4c6b3e5790187acad70459e6128b1f94d8a8b3be7ea8339395a16cbe3"
    ):
        raise ValueError("historical M3 metadata does not match its published hash")
    return final


def _b2_exposed_cases() -> tuple[ExperimentCase, ...]:
    # Reconstruct published grids, preserving both budgets of B2.10's failed cohort.
    # B2.17/B2.18 reserved cases remain exposed even though their screens stopped.
    grids = (
        ((0.225, 0.375, 0.525), ((2, 1), (4, 2)), 240),  # B2.6 validation and screen
        ((0.2375, 0.3875, 0.5375), ((5, 2),), 240),  # B2.7
        ((0.2125, 0.3625, 0.5125), ((3, 2),), 240),  # B2.8
        ((0.2625, 0.4125, 0.5625), ((1, 2),), 240),  # B2.9
        ((0.2875, 0.4375, 0.5875), ((2, 2),), 240),  # B2.10
        ((0.2875, 0.4375, 0.5875), ((2, 2),), 360),  # B2.11 repaired definitions
        ((0.2975, 0.4475, 0.5975), ((3, 2),), 360),  # B2.11 fresh
        ((0.3025, 0.4525, 0.6025), ((4, 1),), 360),  # B2.12
        ((0.3075, 0.4575, 0.6075), ((5, 1),), 360),  # B2.13
        ((0.3125, 0.4625, 0.5925), ((3, 1), (5, 2)), 360),  # B2.14
        ((0.3175, 0.4675, 0.5825), ((2, 1), (4, 2)), 360),  # B2.15
        ((0.3225, 0.4725, 0.5775), ((1, 2), (5, 1)), 360),  # B2.17 reserved
        ((0.3375, 0.4875, 0.5795), ((1, 2),), 360),  # B2.19
        ((0.3475, 0.4975, 0.5835), ((2, 2),), 360),  # B2.20 selection
        ((0.3525, 0.5025, 0.5865), ((1, 1), (5, 2)), 360),  # B2.20 screen
        ((0.3575, 0.5075, 0.5915), ((2, 2), (5, 1)), 360),  # B2.21
        ((0.3645, 0.5145, 0.5945), ((1, 2), (4, 1)), 360),  # B2.22
        ((0.3665, 0.5165, 0.5965), ((2, 1), (4, 2)), 360),  # B2.24
        ((0.3725, 0.5225, 0.5955), ((1, 2), (4, 1)), 360),  # B2.26
        ((0.3745, 0.5295, 0.5935), ((2, 2), (5, 1)), 360),  # B2.28
        ((0.3185, 0.4565, 0.5315, 0.5895), ((1, 1), (3, 2), (5, 1)), 360),  # B2.29
    )
    return (
        *_base_sources(),
        *(
            case
            for volumes, positions, budget in grids
            for case in _grid(volumes, positions, budget)
        ),
        *_grid((0.5675, 0.5725), ((1, 2), (5, 1)), 360, ("y",), (True,)),  # B2.18
        *_grid((0.5585, 0.5785, 0.5985), _POSITIONS, 240, ("y",), (True,)),  # B2.23
        *_grid((0.5175, 0.5275, 0.5425), _POSITIONS, 240, scales=(True,)),  # B2.27
    )
