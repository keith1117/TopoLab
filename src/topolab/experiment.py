"""Versioned case identity contract for reproducible ML experiments."""

import hashlib
import json
from dataclasses import dataclass
from typing import Annotated, Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import Field, field_validator, model_validator

from topolab.fem import build_constrained_dofs, build_load_vector
from topolab.mesh import Hex8Mesh, generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport, PointLoad
from topolab.problem import (
    ContractModel,
    FaceLoadDefinition,
    PointLoadDefinition,
    TopologyProblem,
)
from topolab.simp import apply_density_filter, build_density_filter

CASE_SCHEMA_VERSION = "topolab.m0.case.v1"
CASE_ID_PREFIX = "tlcase-v1-"
LABEL_GENERATOR_VERSION = "topolab.m0.generator.v1"
SOLVER_CONTRACT_VERSION = "topolab.simp.v1"
INPUT_CHANNEL_NAMES = (
    "support_x",
    "support_y",
    "support_z",
    "load_x",
    "load_y",
    "load_z",
    "coord_x",
    "coord_y",
    "coord_z",
    "volume_fraction",
)
INPUT_CHANNEL_COUNT = len(INPUT_CHANNEL_NAMES)
PROJECTION_VOLUME_TOLERANCE = 1e-6
PROJECTION_MAX_ITERATIONS = 100

_CASE_ID_PATTERN = rf"^{CASE_ID_PREFIX}[0-9a-f]{{64}}$"
_DIRECTION_NAMES = {0: "x", 1: "y", 2: "z"}
_AXIS_ORDER = {"x": 0, "y": 1, "z": 2}
_SIDE_ORDER = {"min": 0, "max": 1}


@dataclass(frozen=True, slots=True)
class EncodedCase:
    """One channel-first model input and its dimensional load scale."""

    input_tensor: NDArray[np.float32]
    load_scale: float


@dataclass(frozen=True, slots=True)
class ProjectedDensity:
    """Projected x-fast densities ready for the numerical core."""

    design_density: NDArray[np.float64]
    physical_density: NDArray[np.float64]


class ExperimentCase(ContractModel):
    """One immutable optimization case with a verified content-derived ID."""

    schema_version: Literal["topolab.m0.case.v1"] = "topolab.m0.case.v1"
    case_id: Annotated[str, Field(pattern=_CASE_ID_PATTERN)]
    problem: TopologyProblem

    @field_validator("problem", mode="after")
    @classmethod
    def normalize_problem(cls, problem: TopologyProblem) -> TopologyProblem:
        return _normalized_problem(problem)

    @classmethod
    def from_problem(cls, problem: TopologyProblem) -> "ExperimentCase":
        """Build a case after removing initialization as a source of identity."""

        _require_generator_problem(problem)
        return cls(case_id=build_case_id(problem), problem=problem)

    @model_validator(mode="after")
    def validate_identity(self) -> "ExperimentCase":
        _require_generator_problem(self.problem)
        expected = build_case_id(self.problem)
        if self.case_id != expected:
            raise ValueError("case_id does not match the canonical problem identity")
        return self

    def canonical_identity_json(self) -> str:
        """Return the exact canonical JSON hashed by ``case_id``."""

        return canonical_case_json(self.problem)


def encode_case(case: ExperimentCase) -> EncodedCase:
    """Encode one case as the frozen ``(10, nz, ny, nx)`` float32 tensor."""

    problem = case.problem
    mesh = _case_mesh(case)
    nx, ny, nz = mesh.element_counts
    spatial_shape = (nz, ny, nx)
    input_tensor = np.zeros(
        (INPUT_CHANNEL_COUNT, *spatial_shape),
        dtype=np.float32,
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
    for direction in range(3):
        constrained_nodes = constrained_dofs[constrained_dofs % 3 == direction] // 3
        node_mask = np.zeros(mesh.coordinates.shape[0], dtype=np.bool_)
        node_mask[constrained_nodes] = True
        element_mask = np.any(node_mask[mesh.connectivity], axis=1)
        input_tensor[direction] = element_mask.reshape(spatial_shape)

    load_vector = build_load_vector(
        mesh,
        [_core_load(load) for load in problem.loads],
    )
    load_scale = float(np.sum(np.abs(load_vector)))
    if not np.isfinite(load_scale) or load_scale <= 0.0:
        raise ValueError("case load scale must be positive and finite")
    nodal_loads = load_vector.reshape(-1, 3)
    incident_counts = np.bincount(
        mesh.connectivity.reshape(-1),
        minlength=mesh.coordinates.shape[0],
    )
    element_loads = np.sum(
        nodal_loads[mesh.connectivity]
        / incident_counts[mesh.connectivity, np.newaxis],
        axis=1,
    )
    for direction in range(3):
        input_tensor[3 + direction] = (
            element_loads[:, direction] / load_scale
        ).reshape(spatial_shape)

    element_z, element_y, element_x = np.indices(spatial_shape, dtype=np.float32)
    input_tensor[6] = (element_x + 0.5) / nx
    input_tensor[7] = (element_y + 0.5) / ny
    input_tensor[8] = (element_z + 0.5) / nz
    input_tensor[9].fill(problem.optimization.volume_fraction)
    return EncodedCase(input_tensor=input_tensor, load_scale=load_scale)


def project_design_density(
    case: ExperimentCase,
    raw_density: NDArray[np.float32] | NDArray[np.float64],
) -> ProjectedDensity:
    """Project one model field to the case's filtered physical-volume target."""

    nx, ny, nz = case.problem.mesh.element_counts
    expected_shape = (1, nz, ny, nx)
    if not isinstance(raw_density, np.ndarray):
        raise TypeError("raw_density must be a NumPy array")
    if raw_density.shape != expected_shape:
        raise ValueError(f"raw_density must have shape {expected_shape}")
    if not np.issubdtype(raw_density.dtype, np.floating):
        raise TypeError("raw_density must have a floating-point dtype")
    if not np.all(np.isfinite(raw_density)):
        raise ValueError("raw_density must contain only finite values")
    if np.any(raw_density < 0.0) or np.any(raw_density > 1.0):
        raise ValueError("raw_density must lie in the interval [0, 1]")

    raw = np.asarray(raw_density, dtype=np.float64).reshape(-1)
    mesh = _case_mesh(case)
    density_filter = build_density_filter(
        mesh,
        case.problem.optimization.filter_radius,
    )
    minimum_density = case.problem.optimization.minimum_density
    target_volume = case.problem.optimization.volume_fraction

    def candidate(offset: float) -> ProjectedDensity:
        design = np.clip(raw + offset, minimum_density, 1.0)
        physical = apply_density_filter(density_filter, design)
        return ProjectedDensity(
            design_density=design,
            physical_density=physical,
        )

    lower_offset = -1.0
    upper_offset = 1.0
    projected = candidate(lower_offset)
    lower_volume = float(np.mean(projected.physical_density))
    upper_projected = candidate(upper_offset)
    upper_volume = float(np.mean(upper_projected.physical_density))
    if target_volume < lower_volume or target_volume > upper_volume:
        raise ValueError("target volume is outside the projection bracket")
    if abs(lower_volume - target_volume) <= PROJECTION_VOLUME_TOLERANCE:
        return projected
    if abs(upper_volume - target_volume) <= PROJECTION_VOLUME_TOLERANCE:
        return upper_projected

    for _ in range(PROJECTION_MAX_ITERATIONS):
        midpoint = 0.5 * (lower_offset + upper_offset)
        projected = candidate(midpoint)
        physical_volume = float(np.mean(projected.physical_density))
        if abs(physical_volume - target_volume) <= PROJECTION_VOLUME_TOLERANCE:
            return projected
        if physical_volume < target_volume:
            lower_offset = midpoint
        else:
            upper_offset = midpoint
    raise RuntimeError("density projection did not reach the physical-volume tolerance")


def canonical_case_json(problem: TopologyProblem) -> str:
    """Serialize one problem deterministically for versioned case identity."""

    _require_generator_problem(problem)
    payload = {
        "problem": _canonical_problem_payload(problem),
        "schema_version": CASE_SCHEMA_VERSION,
    }
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def build_case_id(problem: TopologyProblem) -> str:
    """Return the stable SHA-256 identifier for one canonical problem."""

    digest = hashlib.sha256(canonical_case_json(problem).encode("utf-8")).hexdigest()
    return f"{CASE_ID_PREFIX}{digest}"


def _case_mesh(case: ExperimentCase) -> Hex8Mesh:
    return generate_structured_hex8(
        *case.problem.mesh.element_counts,
        lengths=case.problem.mesh.lengths,
    )


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


def _require_generator_problem(problem: TopologyProblem) -> None:
    if problem.initial_density is not None:
        raise ValueError("experiment cases must not define initial_density")


def _canonical_problem_payload(problem: TopologyProblem) -> dict[str, object]:
    payload = problem.model_dump(mode="json", exclude={"initial_density"})
    payload["supports"] = _canonical_supports(problem)
    payload["loads"] = _canonical_loads(problem)
    return payload


def _normalized_problem(problem: TopologyProblem) -> TopologyProblem:
    payload = problem.model_dump(mode="json")
    payload["supports"] = _canonical_supports(problem)
    payload["loads"] = _canonical_loads(problem)
    return TopologyProblem.model_validate(payload)


def _canonical_supports(problem: TopologyProblem) -> list[dict[str, object]]:
    constrained_directions: dict[tuple[str, str], set[str]] = {}
    for support in problem.supports:
        key = (support.axis, support.side)
        directions = constrained_directions.setdefault(key, set())
        directions.update(_direction_name(direction) for direction in support.directions)

    return [
        {
            "axis": axis,
            "directions": sorted(
                directions,
                key=_AXIS_ORDER.__getitem__,
            ),
            "side": side,
        }
        for (axis, side), directions in sorted(
            constrained_directions.items(),
            key=lambda item: (
                _AXIS_ORDER[item[0][0]],
                _SIDE_ORDER[item[0][1]],
            ),
        )
    ]


def _canonical_loads(problem: TopologyProblem) -> list[dict[str, object]]:
    loads: list[dict[str, object]] = []
    for load in problem.loads:
        if isinstance(load, PointLoadDefinition):
            loads.append(
                {
                    "direction": _direction_name(load.direction),
                    "kind": "point",
                    "magnitude": load.magnitude,
                    "node": load.node,
                }
            )
        elif isinstance(load, FaceLoadDefinition):
            loads.append(
                {
                    "axis": load.axis,
                    "direction": _direction_name(load.direction),
                    "kind": "face",
                    "side": load.side,
                    "total": load.total,
                }
            )
        else:  # pragma: no cover - the discriminated union prevents this state
            raise TypeError(f"unsupported load definition: {type(load).__name__}")

    return sorted(loads, key=_canonical_sort_key)


def _canonical_sort_key(value: dict[str, object]) -> str:
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def _direction_name(direction: str | int) -> str:
    if isinstance(direction, int):
        return _DIRECTION_NAMES[direction]
    return direction
