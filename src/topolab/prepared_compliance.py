"""One opt-in immutable-setup candidate for the offline compliance objective."""

from dataclasses import dataclass, field
from time import perf_counter, process_time
from typing import Any

import numpy as np
from numpy.typing import NDArray
from scipy.sparse import coo_matrix  # type: ignore[import-untyped]
from scipy.sparse.linalg import splu  # type: ignore[import-untyped]

from topolab.fem import _LARGE_SOLVE_FREE_DOFS, hex8_element_stiffness
from topolab.offline_compliance import (
    KINK_TOLERANCE,
    VOLUME_TOLERANCE,
    ObjectiveResult,
    OfflineCompliance,
    Projection,
    pullback,
)
from topolab.simp import apply_density_filter, backpropagate_density_gradient, simp_element_moduli

VERSION = "topolab.prepared-offline-compliance.v1"
PHASES = ("projection_filter", "assembly", "reduction", "factorization", "solve_energy", "pullback")


@dataclass(slots=True)
class PreparedCompliance(OfflineCompliance):
    """Own read-only setup; always assemble and factor each current density anew."""

    unit: NDArray[np.float64] = field(init=False)
    rows: NDArray[np.int64] = field(init=False)
    columns: NDArray[np.int64] = field(init=False)
    free_dofs: NDArray[np.int64] = field(init=False)
    free_loads: NDArray[np.float64] = field(init=False)
    weights: NDArray[np.float64] = field(init=False)
    retained_array_bytes: int = field(init=False)

    def __post_init__(self) -> None:
        super(PreparedCompliance, self).__post_init__()
        nx, ny, nz = self.mesh.element_counts
        lx, ly, lz = self.mesh.lengths
        self.unit = hex8_element_stiffness(
            1.0,
            self.case.problem.material.poisson_ratio,
            dimensions=(lx / nx, ly / ny, lz / nz),
        )
        dofs = self.mesh.element_dofs
        n = dofs.shape[0]
        self.rows = np.broadcast_to(dofs[:, :, None], (n, 24, 24)).ravel()
        self.columns = np.broadcast_to(dofs[:, None, :], (n, 24, 24)).ravel()
        mask = np.ones(self.loads.size, dtype=np.bool_)
        mask[self.constrained] = False
        self.free_dofs = np.flatnonzero(mask)
        self.free_loads = self.loads[self.free_dofs].copy()
        self.weights = np.asarray(self.filt.matrix.T @ (1 / self.filt.row_sums)) / n
        arrays = (
            self.mesh.coordinates,
            self.mesh.connectivity,
            dofs,
            self.loads,
            self.constrained,
            self.filt.matrix.data,
            self.filt.matrix.indices,
            self.filt.matrix.indptr,
            self.filt.row_sums,
            self.unit,
            self.rows,
            self.columns,
            self.free_dofs,
            self.free_loads,
            self.weights,
        )
        self.retained_array_bytes = sum(a.nbytes for a in {id(a): a for a in arrays}.values())
        for array in arrays:
            array.setflags(write=False)

    def projection(self, raw: NDArray[np.floating[Any]]) -> Projection:
        z = np.asarray(raw, dtype=np.float64)
        opt = self.case.problem.optimization
        if z.shape != self.weights.shape or not np.all(np.isfinite(z)) or np.any((z < 0) | (z > 1)):
            raise ValueError("finite raw vector in [0,1] required")
        low, high = -1.0, 1.0
        for _ in range(100):
            offset = (low + high) / 2
            design = np.clip(z + offset, opt.minimum_density, 1.0)
            error = float(self.weights @ design) - opt.volume_fraction
            if abs(error) <= VOLUME_TOLERANCE:
                break
            if error < 0:
                low = offset
            else:
                high = offset
        else:
            raise ValueError("physical-volume root did not converge")
        shifted = z + offset
        if np.any(
            np.minimum(np.abs(shifted - opt.minimum_density), np.abs(shifted - 1)) <= KINK_TOLERANCE
        ):
            raise ValueError("projection is at a clipping kink")
        free = (shifted > opt.minimum_density) & (shifted < 1)
        if float(self.weights @ free) <= 0:
            raise ValueError("projection has no free volume derivative")
        physical = apply_density_filter(self.filt, design)
        if abs(float(physical.mean()) - opt.volume_fraction) > VOLUME_TOLERANCE:
            raise ValueError("filtered physical volume differs")
        return Projection(design, physical, self.weights, free, offset)

    def evaluate(
        self, raw: NDArray[np.floating[Any]], phases: list[dict[str, Any]] | None = None
    ) -> ObjectiveResult:
        if phases:
            raise ValueError("phase destination must be empty")
        wall, cpu = (perf_counter(), process_time()) if phases is not None else (0.0, 0.0)

        def mark(name: str) -> None:
            nonlocal wall, cpu
            if phases is not None:
                now_wall, now_cpu = perf_counter(), process_time()
                phases.append(
                    {"phase": name, "wall_seconds": now_wall - wall, "cpu_seconds": now_cpu - cpu}
                )
                wall, cpu = now_wall, now_cpu

        p = self.case.problem
        state = self.projection(raw)
        mark(PHASES[0])
        moduli = simp_element_moduli(
            state.physical,
            solid_modulus=p.material.solid_modulus,
            minimum_modulus=p.material.minimum_modulus,
            penalty=p.optimization.penalty,
        )
        values = (moduli[:, None, None] * self.unit).ravel()
        stiffness = coo_matrix(
            (values, (self.rows, self.columns)), shape=(self.loads.size, self.loads.size)
        ).tocsr()
        stiffness.sum_duplicates()
        stiffness.sort_indices()
        if not np.all(np.isfinite(stiffness.data)):
            raise ValueError("stiffness must contain only finite values")
        mark(PHASES[1])
        reduced = stiffness[self.free_dofs][:, self.free_dofs].tocsc()
        ordering = "MMD_AT_PLUS_A" if self.free_dofs.size >= _LARGE_SOLVE_FREE_DOFS else "COLAMD"
        mark(PHASES[2])
        try:
            factor = splu(reduced, permc_spec=ordering)
        except RuntimeError as error:
            raise ValueError("reduced stiffness is singular") from error
        pivots = np.abs(factor.U.diagonal())
        scale = float(np.max(pivots))
        threshold = np.finfo(np.float64).eps * reduced.shape[0] * scale
        if scale == 0 or float(np.min(pivots)) <= threshold:
            raise ValueError("reduced stiffness is singular")
        mark(PHASES[3])
        free_displacements = factor.solve(self.free_loads)
        if not np.all(np.isfinite(free_displacements)):
            raise ValueError("reduced stiffness solve was non-finite")
        displacement = np.zeros(self.loads.size)
        displacement[self.free_dofs] = free_displacements
        # Retain the original compliance path's reaction work in the complete cost.
        reactions = np.asarray(stiffness @ displacement).reshape(-1) - self.loads
        if not np.all(np.isfinite(reactions)):
            raise ValueError("reactions were non-finite")
        ue = displacement[self.mesh.element_dofs]
        energies = np.einsum("ei,ij,ej->e", ue, self.unit, ue)
        derivative = (
            p.optimization.penalty
            * state.physical ** (p.optimization.penalty - 1.0)
            * (p.material.solid_modulus - p.material.minimum_modulus)
        )
        sensitivity = -derivative * energies
        compliance = float(np.dot(self.loads, displacement))
        mark(PHASES[4])
        gradient = pullback(state, backpropagate_density_gradient(self.filt, sensitivity))
        result = ObjectiveResult(
            compliance / self.normalizer, compliance, gradient / self.normalizer, state
        )
        mark(PHASES[5])
        return result
