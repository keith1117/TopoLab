"""Versioned case identity contract for reproducible ML experiments."""

import hashlib
import json
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator

from topolab.problem import (
    ContractModel,
    FaceLoadDefinition,
    PointLoadDefinition,
    TopologyProblem,
)

CASE_SCHEMA_VERSION = "topolab.m0.case.v1"
CASE_ID_PREFIX = "tlcase-v1-"
LABEL_GENERATOR_VERSION = "topolab.m0.generator.v1"
SOLVER_CONTRACT_VERSION = "topolab.simp.v1"

_CASE_ID_PATTERN = rf"^{CASE_ID_PREFIX}[0-9a-f]{{64}}$"
_DIRECTION_NAMES = {0: "x", 1: "y", 2: "z"}
_AXIS_ORDER = {"x": 0, "y": 1, "z": 2}
_SIDE_ORDER = {"min": 0, "max": 1}


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
