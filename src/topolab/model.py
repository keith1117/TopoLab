"""Typed input models for TopoLab's numerical core."""

from dataclasses import dataclass
from typing import Literal

type Axis = Literal["x", "y", "z"]
type Direction = Literal["x", "y", "z", 0, 1, 2]
type FaceSide = Literal["min", "max"]


@dataclass(frozen=True, slots=True)
class FixedFaceSupport:
    """Zero-displacement support on selected components of a mesh face."""

    axis: Axis
    side: FaceSide
    directions: tuple[Direction, ...] = ("x", "y", "z")


@dataclass(frozen=True, slots=True)
class PointLoad:
    """A signed nodal force in one displacement direction."""

    node: int
    direction: Direction
    magnitude: float


@dataclass(frozen=True, slots=True)
class FaceLoad:
    """A signed total force distributed equally over one mesh face."""

    axis: Axis
    side: FaceSide
    direction: Direction
    total: float


type Load = PointLoad | FaceLoad
