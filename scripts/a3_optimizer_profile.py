"""Profile fixed three-step SIMP work without changing its numerical path."""

from __future__ import annotations

import argparse
import cProfile
import json
import platform
import pstats
import resource
import sys
from time import perf_counter
from typing import Any

from topolab.fem import (
    FactorizationOrdering,
    assemble_global_stiffness,
    build_constrained_dofs,
    build_load_vector,
    hex8_element_stiffness,
)
from topolab.mesh import generate_structured_hex8
from topolab.model import FaceLoad, FixedFaceSupport
from topolab.simp import SimpConfig, optimize_simp


def _cumulative(stats: pstats.Stats, filename: str, function: str) -> float:
    for (source, _line, name), (_primitive, _calls, _own, cumulative, _callers) in (
        stats.stats.items()  # type: ignore[attr-defined]
    ):
        if source.endswith(filename) and name == function:
            return float(cumulative)
    raise RuntimeError(f"profile did not record {filename}:{function}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mesh", nargs=3, type=int, default=(30, 12, 6))
    parser.add_argument(
        "--ordering", choices=("auto", "COLAMD", "MMD_AT_PLUS_A"), default="auto"
    )
    args = parser.parse_args()
    counts = tuple(args.mesh)
    if any(count <= 0 for count in counts):
        parser.error("mesh counts must be positive")
    ordering: FactorizationOrdering = args.ordering
    lengths = (1.0, 0.4, 0.2)
    mesh = generate_structured_hex8(*counts, lengths=lengths)
    loads = build_load_vector(
        mesh, [FaceLoad(axis="x", side="max", direction="y", total=-1000.0)]
    )
    fixed = build_constrained_dofs(
        mesh, [FixedFaceSupport(axis="x", side="min")]
    )
    config = SimpConfig(
        volume_fraction=0.5,
        filter_radius=0.06,
        max_iterations=3,
        convergence_tolerance=1e-12,
    )

    profiler = cProfile.Profile()
    started = perf_counter()
    profiler.enable()
    result = optimize_simp(
        mesh,
        loads,
        fixed,
        solid_modulus=2.0e11,
        minimum_modulus=2.0e8,
        poisson_ratio=0.3,
        config=config,
        ordering=ordering,
    )
    profiler.disable()
    optimizer_seconds = perf_counter() - started
    stats = pstats.Stats(profiler)
    phases = {
        "filter_build_inclusive": _cumulative(stats, "simp.py", "build_density_filter"),
        "filter_apply_inclusive": _cumulative(stats, "simp.py", "apply_density_filter"),
        "filter_gradient_inclusive": _cumulative(
            stats, "simp.py", "backpropagate_density_gradient"
        ),
        "oc_inclusive": _cumulative(stats, "simp.py", "optimality_criteria_update"),
        "element_stiffness_inclusive": _cumulative(
            stats, "fem.py", "hex8_element_stiffness"
        ),
        "assembly_inclusive": _cumulative(stats, "fem.py", "assemble_global_stiffness"),
        "factorization_inclusive": _cumulative(stats, "linsolve.py", "splu"),
        "solve_inclusive": _cumulative(stats, "fem.py", "solve_linear_static"),
    }
    serialization_started = perf_counter()
    serialized = json.dumps(
        {
            "design_density": result.design_density.tolist(),
            "physical_density": result.physical_density.tolist(),
            "compliance": result.compliance,
            "history": [
                {
                    "iteration": step.iteration,
                    "compliance": step.compliance,
                    "volume_fraction": step.volume_fraction,
                    "density_change": step.density_change,
                    "design_density": step.design_density.tolist(),
                    "physical_density": step.physical_density.tolist(),
                }
                for step in result.history
            ],
        },
        allow_nan=False,
    )
    serialization_seconds = perf_counter() - serialization_started
    unit_stiffness = hex8_element_stiffness(
        1.0,
        0.3,
        dimensions=tuple(length / count for length, count in zip(lengths, counts, strict=True)),
    )
    matrix = assemble_global_stiffness(mesh, unit_stiffness)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = peak if sys.platform == "darwin" else peak * 1024
    report: dict[str, Any] = {
        "mesh": counts,
        "elements": int(mesh.element_dofs.shape[0]),
        "degrees_of_freedom": int(loads.size),
        "nonzero_entries": int(matrix.nnz),
        "ordering": ordering,
        "iterations": len(result.history),
        "optimizer_profiled_wall_seconds": optimizer_seconds,
        "phase_inclusive_seconds": phases,
        "serialization_seconds": serialization_seconds,
        "serialized_bytes": len(serialized.encode("utf-8")),
        "peak_rss_bytes": peak_bytes,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "phase_note": "cProfile inclusive functions overlap; serialization is timed separately",
    }
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
