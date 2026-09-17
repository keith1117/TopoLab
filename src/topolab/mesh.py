"""Structured Hex8 mesh generation."""

from dataclasses import dataclass
from math import isfinite

import numpy as np
from numpy.typing import NDArray

HEX8_LOCAL_NODE_OFFSETS: tuple[tuple[int, int, int], ...] = (
    (0, 0, 0),
    (1, 0, 0),
    (1, 1, 0),
    (0, 1, 0),
    (0, 0, 1),
    (1, 0, 1),
    (1, 1, 1),
    (0, 1, 1),
)


@dataclass(frozen=True, slots=True)
class Hex8Mesh:
    """A structured, axis-aligned Hex8 mesh with node-major displacement DOFs."""

    element_counts: tuple[int, int, int]
    lengths: tuple[float, float, float]
    coordinates: NDArray[np.float64]
    connectivity: NDArray[np.int64]
    element_dofs: NDArray[np.int64]


def generate_structured_hex8(
    nx: int,
    ny: int,
    nz: int,
    *,
    lengths: tuple[float, float, float] = (1.0, 1.0, 1.0),
) -> Hex8Mesh:
    """Generate an ``nx`` by ``ny`` by ``nz`` rectangular Hex8 mesh.

    Nodes and elements are numbered with x varying fastest, followed by y and z.
    Each element's 24 displacement DOFs are ordered by local node, then
    ``(ux, uy, uz)`` within that node.
    """

    element_counts = _validate_element_counts(nx, ny, nz)
    validated_lengths = _validate_lengths(lengths)
    nx, ny, nz = element_counts
    lx, ly, lz = validated_lengths

    x = np.linspace(0.0, lx, nx + 1, dtype=np.float64)
    y = np.linspace(0.0, ly, ny + 1, dtype=np.float64)
    z = np.linspace(0.0, lz, nz + 1, dtype=np.float64)
    zz, yy, xx = np.meshgrid(z, y, x, indexing="ij")
    coordinates = np.column_stack((xx.ravel(), yy.ravel(), zz.ravel()))

    element_z, element_y, element_x = np.indices((nz, ny, nx), dtype=np.int64)
    origin_nodes = (
        element_x + (nx + 1) * (element_y + (ny + 1) * element_z)
    ).ravel()
    node_layer_size = (nx + 1) * (ny + 1)
    local_node_offsets = np.array(
        [di + (nx + 1) * dj + node_layer_size * dk for di, dj, dk in HEX8_LOCAL_NODE_OFFSETS],
        dtype=np.int64,
    )
    connectivity = origin_nodes[:, np.newaxis] + local_node_offsets
    element_dofs = (
        3 * connectivity[:, :, np.newaxis] + np.arange(3, dtype=np.int64)
    ).reshape(-1, 24)

    return Hex8Mesh(
        element_counts=element_counts,
        lengths=validated_lengths,
        coordinates=coordinates,
        connectivity=connectivity,
        element_dofs=element_dofs,
    )


def _validate_element_counts(nx: int, ny: int, nz: int) -> tuple[int, int, int]:
    counts = (nx, ny, nz)
    axis_names = ("nx", "ny", "nz")
    for axis_name, count in zip(axis_names, counts, strict=True):
        if isinstance(count, bool) or not isinstance(count, int):
            raise TypeError(f"{axis_name} must be an integer")
        if count <= 0:
            raise ValueError(f"{axis_name} must be positive")
    return counts


def _validate_lengths(
    lengths: tuple[float, float, float],
) -> tuple[float, float, float]:
    if len(lengths) != 3:
        raise ValueError("lengths must contain exactly three values")

    validated: list[float] = []
    for axis_name, length in zip(("Lx", "Ly", "Lz"), lengths, strict=True):
        if isinstance(length, bool):
            raise TypeError(f"{axis_name} must be a real number")
        try:
            value = float(length)
        except (TypeError, ValueError) as error:
            raise TypeError(f"{axis_name} must be a real number") from error
        if not isfinite(value) or value <= 0.0:
            raise ValueError(f"{axis_name} must be positive and finite")
        validated.append(value)

    return validated[0], validated[1], validated[2]
