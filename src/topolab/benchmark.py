"""Reproducible sparse finite-element assembly and solve benchmark."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import math
import os
import platform
import statistics
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import cast

from topolab.fem import FactorizationOrdering

DOMAIN_LENGTHS = (1.0, 0.4, 0.2)
YOUNGS_MODULUS = 200.0e9
POISSON_RATIO = 0.3
FACE_LOAD_TOTAL = -1000.0
EQUILIBRIUM_RELATIVE_TOLERANCE = 1.0e-8
BYTES_PER_FLOAT64 = 8
MIB = 1024**2
GIB = 1024**3

THREAD_ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "BLIS_NUM_THREADS": "1",
    "OMP_DYNAMIC": "FALSE",
    "MKL_DYNAMIC": "FALSE",
}


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    """One fixed structured-mesh benchmark case."""

    name: str
    element_counts: tuple[int, int, int]


DEFAULT_CASES = (
    BenchmarkCase("small", (10, 4, 2)),
    BenchmarkCase("medium", (20, 8, 4)),
    BenchmarkCase("large", (30, 12, 6)),
    BenchmarkCase("memory-pressure", (45, 18, 9)),
)


@dataclass(frozen=True, slots=True)
class TimingSummary:
    """Cold and repeated wall-clock measurements for one stage."""

    cold_seconds: float
    repeated_seconds: tuple[float, ...]
    repeated_median_seconds: float


@dataclass(frozen=True, slots=True)
class BenchmarkCaseResult:
    """Measured timings, memory, and matrix size for one mesh."""

    case: str
    element_counts: tuple[int, int, int]
    elements: int
    nodes: int
    degrees_of_freedom: int
    free_degrees_of_freedom: int
    nonzero_entries: int
    csr_payload_mib: float
    dense_global_gib_estimate: float
    dense_reduced_gib_estimate: float
    dense_to_csr_payload_ratio: float
    process_peak_rss_mib: float
    process_peak_rss_increase_mib: float
    compliance: float
    equilibrium_relative_residual: float
    assembly: TimingSummary
    solve: TimingSummary
    total: TimingSummary


@dataclass(frozen=True, slots=True)
class _Sample:
    assembly_seconds: float
    solve_seconds: float
    total_seconds: float
    elements: int
    nodes: int
    degrees_of_freedom: int
    free_degrees_of_freedom: int
    nonzero_entries: int
    csr_payload_bytes: int
    compliance: float
    equilibrium_relative_residual: float


def measure_case(
    case: BenchmarkCase,
    *,
    repeated_runs: int,
    ordering: FactorizationOrdering = "auto",
) -> BenchmarkCaseResult:
    """Measure one case in the current process after validating repeat count."""

    if isinstance(repeated_runs, bool) or not isinstance(repeated_runs, int):
        raise TypeError("repeated_runs must be an integer")
    if repeated_runs <= 0:
        raise ValueError("repeated_runs must be positive")

    baseline_peak_rss = _peak_rss_bytes()
    samples = tuple(
        _measure_once(case, ordering=ordering) for _ in range(repeated_runs + 1)
    )
    peak_rss = _peak_rss_bytes()
    cold = samples[0]

    for sample in samples[1:]:
        if not math.isclose(sample.compliance, cold.compliance, rel_tol=1.0e-12):
            raise RuntimeError("repeated solve changed compliance")
        if sample.nonzero_entries != cold.nonzero_entries:
            raise RuntimeError("repeated assembly changed sparse structure")
    maximum_equilibrium_residual = max(
        sample.equilibrium_relative_residual for sample in samples
    )
    if maximum_equilibrium_residual > EQUILIBRIUM_RELATIVE_TOLERANCE:
        raise RuntimeError("benchmark solve failed the equilibrium check")

    dense_global_bytes = cold.degrees_of_freedom**2 * BYTES_PER_FLOAT64
    dense_reduced_bytes = cold.free_degrees_of_freedom**2 * BYTES_PER_FLOAT64
    return BenchmarkCaseResult(
        case=case.name,
        element_counts=case.element_counts,
        elements=cold.elements,
        nodes=cold.nodes,
        degrees_of_freedom=cold.degrees_of_freedom,
        free_degrees_of_freedom=cold.free_degrees_of_freedom,
        nonzero_entries=cold.nonzero_entries,
        csr_payload_mib=cold.csr_payload_bytes / MIB,
        dense_global_gib_estimate=dense_global_bytes / GIB,
        dense_reduced_gib_estimate=dense_reduced_bytes / GIB,
        dense_to_csr_payload_ratio=dense_global_bytes / cold.csr_payload_bytes,
        process_peak_rss_mib=peak_rss / MIB,
        process_peak_rss_increase_mib=max(0, peak_rss - baseline_peak_rss) / MIB,
        compliance=cold.compliance,
        equilibrium_relative_residual=maximum_equilibrium_residual,
        assembly=_summarize(samples, "assembly_seconds"),
        solve=_summarize(samples, "solve_seconds"),
        total=_summarize(samples, "total_seconds"),
    )


def generate_report(
    *,
    cases: Sequence[BenchmarkCase] = DEFAULT_CASES,
    repeated_runs: int = 3,
    ordering: FactorizationOrdering = "auto",
) -> dict[str, object]:
    """Run every case in an isolated worker and return a JSON-ready report."""

    if len(cases) == 0:
        raise ValueError("cases must contain at least one benchmark case")
    if isinstance(repeated_runs, bool) or not isinstance(repeated_runs, int):
        raise TypeError("repeated_runs must be an integer")
    if repeated_runs <= 0:
        raise ValueError("repeated_runs must be positive")

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "git_revision": _git_revision(),
        "environment": _environment_metadata(),
        "configuration": {
            "domain_lengths": DOMAIN_LENGTHS,
            "youngs_modulus_pa": YOUNGS_MODULUS,
            "poisson_ratio": POISSON_RATIO,
            "support": "x=min, ux=uy=uz=0",
            "load": "x=max face, y direction, total=-1000 N",
            "solver": "scipy.sparse.linalg.splu through solve_linear_static",
            "solver_ordering_policy": (
                "auto selects MMD_AT_PLUS_A for >=5000 free DOFs; otherwise COLAMD"
            ),
            "requested_ordering": ordering,
            "cold_runs_per_case": 1,
            "repeated_runs_per_case": repeated_runs,
            "thread_environment": THREAD_ENVIRONMENT,
            "timing_clock": "time.perf_counter wall time",
            "memory_metric": "isolated worker peak resident set size",
        },
        "cases": [
            _run_worker(case, repeated_runs=repeated_runs, ordering=ordering)
            for case in cases
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark CLI or its isolated worker mode."""

    arguments = tuple(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] == "_worker":
        return _worker_main(arguments[1:])

    parser = argparse.ArgumentParser(
        description="Benchmark TopoLab sparse Hex8 assembly and solving.",
    )
    parser.add_argument(
        "--repeated-runs",
        type=_positive_integer,
        default=3,
        help="timed runs after the first cold numerical run (default: 3)",
    )
    parser.add_argument(
        "--ordering", choices=("auto", "COLAMD", "MMD_AT_PLUS_A"), default="auto"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="optional JSON output path; stdout is used when omitted",
    )
    parsed = parser.parse_args(arguments)
    repeated_runs = cast(int, parsed.repeated_runs)
    output = cast(Path | None, parsed.output)
    report = generate_report(
        repeated_runs=repeated_runs,
        ordering=cast(FactorizationOrdering, parsed.ordering),
    )
    serialized = json.dumps(report, indent=2, sort_keys=True, allow_nan=False)
    if output is None:
        print(serialized)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(f"{serialized}\n", encoding="utf-8")
        print(output)
    return 0


def _measure_once(
    case: BenchmarkCase, *, ordering: FactorizationOrdering
) -> _Sample:
    import numpy as np

    from topolab.fem import (
        assemble_global_stiffness,
        build_constrained_dofs,
        build_load_vector,
        hex8_element_stiffness,
        solve_linear_static,
    )
    from topolab.mesh import generate_structured_hex8
    from topolab.model import FaceLoad, FixedFaceSupport

    nx, ny, nz = case.element_counts
    lx, ly, lz = DOMAIN_LENGTHS
    total_start = perf_counter()
    mesh = generate_structured_hex8(nx, ny, nz, lengths=DOMAIN_LENGTHS)
    element_stiffness = hex8_element_stiffness(
        YOUNGS_MODULUS,
        POISSON_RATIO,
        dimensions=(lx / nx, ly / ny, lz / nz),
    )

    assembly_start = perf_counter()
    stiffness = assemble_global_stiffness(mesh, element_stiffness)
    assembly_seconds = perf_counter() - assembly_start

    constrained_dofs = build_constrained_dofs(
        mesh,
        [FixedFaceSupport(axis="x", side="min")],
    )
    loads = build_load_vector(
        mesh,
        [FaceLoad(axis="x", side="max", direction="y", total=FACE_LOAD_TOTAL)],
    )
    solve_start = perf_counter()
    solution = solve_linear_static(
        stiffness, loads, constrained_dofs, ordering=ordering
    )
    solve_seconds = perf_counter() - solve_start
    total_seconds = perf_counter() - total_start

    load_resultant = loads.reshape(-1, 3).sum(axis=0)
    reaction_resultant = solution.reactions.reshape(-1, 3).sum(axis=0)
    equilibrium_residual = float(np.linalg.norm(load_resultant + reaction_resultant))
    load_scale = float(np.linalg.norm(load_resultant))
    csr_payload_bytes = (
        stiffness.data.nbytes + stiffness.indices.nbytes + stiffness.indptr.nbytes
    )
    return _Sample(
        assembly_seconds=assembly_seconds,
        solve_seconds=solve_seconds,
        total_seconds=total_seconds,
        elements=mesh.connectivity.shape[0],
        nodes=mesh.coordinates.shape[0],
        degrees_of_freedom=stiffness.shape[0],
        free_degrees_of_freedom=stiffness.shape[0] - constrained_dofs.size,
        nonzero_entries=stiffness.nnz,
        csr_payload_bytes=csr_payload_bytes,
        compliance=float(loads @ solution.displacements),
        equilibrium_relative_residual=equilibrium_residual / load_scale,
    )


def _summarize(samples: Sequence[_Sample], attribute: str) -> TimingSummary:
    values = tuple(float(getattr(sample, attribute)) for sample in samples)
    repeated = values[1:]
    return TimingSummary(
        cold_seconds=values[0],
        repeated_seconds=repeated,
        repeated_median_seconds=statistics.median(repeated),
    )


def _run_worker(
    case: BenchmarkCase,
    *,
    repeated_runs: int,
    ordering: FactorizationOrdering,
) -> dict[str, object]:
    environment = os.environ.copy()
    environment.update(THREAD_ENVIRONMENT)
    source_root = str(Path(__file__).resolve().parents[1])
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = (
        source_root
        if not existing_pythonpath
        else f"{source_root}{os.pathsep}{existing_pythonpath}"
    )
    command = [
        sys.executable,
        "-m",
        "topolab.benchmark",
        "_worker",
        case.name,
        *(str(count) for count in case.element_counts),
        "--repeated-runs",
        str(repeated_runs),
        "--ordering",
        ordering,
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if completed.returncode != 0:
        message = completed.stderr.strip() or "worker returned no error output"
        raise RuntimeError(f"benchmark worker failed for {case.name}: {message}")
    payload = json.loads(completed.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError(f"benchmark worker returned invalid JSON for {case.name}")
    return cast(dict[str, object], payload)


def _worker_main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("name")
    parser.add_argument("nx", type=_positive_integer)
    parser.add_argument("ny", type=_positive_integer)
    parser.add_argument("nz", type=_positive_integer)
    parser.add_argument("--repeated-runs", type=_positive_integer, required=True)
    parser.add_argument(
        "--ordering", choices=("auto", "COLAMD", "MMD_AT_PLUS_A"), required=True
    )
    parsed = parser.parse_args(argv)
    case = BenchmarkCase(
        name=cast(str, parsed.name),
        element_counts=(
            cast(int, parsed.nx),
            cast(int, parsed.ny),
            cast(int, parsed.nz),
        ),
    )
    result = measure_case(
        case,
        repeated_runs=cast(int, parsed.repeated_runs),
        ordering=cast(FactorizationOrdering, parsed.ordering),
    )
    print(json.dumps(asdict(result), sort_keys=True, allow_nan=False))
    return 0


def _positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return parsed


def _peak_rss_bytes() -> int:
    import resource

    peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return peak if sys.platform == "darwin" else peak * 1024


def _environment_metadata() -> dict[str, object]:
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": _processor_name(),
        "logical_cpu_count": os.cpu_count(),
        "physical_memory_gib": _physical_memory_bytes() / GIB,
        "python": platform.python_version(),
        "numpy": importlib.metadata.version("numpy"),
        "scipy": importlib.metadata.version("scipy"),
    }


def _processor_name() -> str:
    if sys.platform == "darwin":
        completed = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            return completed.stdout.strip()
    return platform.processor() or "unknown"


def _physical_memory_bytes() -> int:
    try:
        pages = os.sysconf("SC_PHYS_PAGES")
        page_size = os.sysconf("SC_PAGE_SIZE")
    except (AttributeError, OSError, ValueError):
        return 0
    return int(pages * page_size)


def _git_revision() -> str:
    repository_root = Path(__file__).resolve().parents[2]
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
