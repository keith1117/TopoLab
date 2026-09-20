# Sparse finite-element performance and memory benchmark

Date: 2026-09-19

Benchmark harness baseline: `e3e851d`

Numerical implementation baseline: `4535362`

## Scope and decision

This benchmark measures TopoLab's structured Hex8 global stiffness assembly and
constrained sparse direct solve on four increasing cantilever meshes. It records cold
and repeated wall time, CSR matrix payload, process peak resident memory, matrix size,
and an equilibrium residual.

The results demonstrate that the current sparse path completes a 7,290-element case
within the local 8 GiB memory limit while the equivalent dense global matrix alone
would require an estimated 5.12 GiB before factorization, copies, or solver workspace.
This is evidence for the finite-element solver's sparse storage behavior; it is not a
claim that the full platform, optimizer, or future ML pipeline is universally
scalable.

## Fixed environment and configuration

- Machine: MacBook Air, Apple M2, 8 logical cores, 8 GiB memory.
- Operating system: macOS 26.5, `arm64`.
- Python 3.12.10, NumPy 2.5.3, SciPy 1.18.1.
- Domain: `1.0 x 0.4 x 0.2 m` with structured, axis-aligned Hex8 elements.
- Material: `E = 200 GPa`, `nu = 0.3`.
- Support: the `x=min` face is fixed in `ux`, `uy`, and `uz`.
- Load: a total `-1000 N` face resultant in `y` on the `x=max` face.
- Solver: `scipy.sparse.linalg.splu` through `solve_linear_static`, using
  SuperLU's default COLAMD ordering and the documented TopoLab pivot check.
- Thread environment: `OMP_NUM_THREADS=1`, `OPENBLAS_NUM_THREADS=1`,
  `MKL_NUM_THREADS=1`, `VECLIB_MAXIMUM_THREADS=1`, and `BLIS_NUM_THREADS=1`;
  dynamic OpenMP/MKL threading is disabled.
- Each mesh runs in a fresh subprocess. The first timed numerical pass is cold and
  three more passes run in the same process; repeated values below are their median.

`time.perf_counter` measures wall time. Peak resident set size is the subprocess
`ru_maxrss`, so it includes Python, imported numerical libraries, meshes, matrices,
SuperLU factorization, solutions, and allocator retention across that case's four
runs. The reported peak increase is relative to the worker's pre-measurement peak.

## Results

| Case | Mesh | Elements | DOF | NNZ | Assembly cold / repeated | Solve cold / repeated | Total cold / repeated | Peak RSS | Peak increase |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Small | `10 x 4 x 2` | 80 | 495 | 25,389 | 3.21 / 0.87 ms | 3.75 / 1.35 ms | 8.71 / 2.53 ms | 87.13 MiB | 3.20 MiB |
| Medium | `20 x 8 x 4` | 640 | 2,835 | 178,425 | 8.40 / 8.31 ms | 43.06 / 31.34 ms | 52.07 / 39.78 ms | 143.36 MiB | 59.14 MiB |
| Large | `30 x 12 x 6` | 2,160 | 8,463 | 575,757 | 34.82 / 28.34 ms | 355.41 / 356.54 ms | 391.42 / 385.61 ms | 260.53 MiB | 176.36 MiB |
| Memory pressure | `45 x 18 x 9` | 7,290 | 26,220 | 1,884,960 | 115.14 / 85.89 ms | 3.593 / 3.573 s | 3.710 / 3.666 s | 726.44 MiB | 642.92 MiB |

The storage comparison uses the actual CSR array payload
`data.nbytes + indices.nbytes + indptr.nbytes`. Dense storage is an analytical
estimate of one `float64` global matrix, `8 * ndof^2`; no large dense allocation was
performed.

| Case | CSR payload | Dense global estimate | Dense / CSR payload |
|---|---:|---:|---:|
| Small | 0.292 MiB | 0.00183 GiB | 6.39x |
| Medium | 2.053 MiB | 0.0599 GiB | 29.87x |
| Large | 6.621 MiB | 0.534 GiB | 82.53x |
| Memory pressure | 21.672 MiB | 5.122 GiB | 242.03x |

The memory-pressure case's dense matrix estimate is about 64% of the machine's total
physical memory for a single array. A practical dense solve would additionally need
factorization, copies, right-hand sides, outputs, and runtime workspace. The sparse
case completed with a measured full-process peak of 726.44 MiB, about 9% of physical
memory. This is why the report does not attempt a potentially disruptive dense solve
at that size.

## Numerical guard

Every timed solve also checks total applied load plus total reaction. Relative
residuals increased from `3.56e-14` on the smallest mesh to `7.62e-12` on the largest,
remaining below the documented `1e-8` equilibrium acceptance criterion. No numerical
tolerance was changed for this benchmark.

Small-mesh sparse/dense entry and displacement agreement remains covered by
`tests/test_assembly.py` at `rtol=1e-9`. The dense figures above are storage estimates,
not measured dense execution times.

## Reproduction

From the repository root:

```bash
uv sync --dev --locked
PYTHONPATH=src uv run python -m topolab.benchmark \
  --repeated-runs 3 \
  --output results/sparse_solver_benchmark.json
```

The `results/` directory is ignored because timing artifacts are environment-specific.
The benchmark emits JSON containing the code revision, environment, fixed solver
configuration, every repeated timing, matrix statistics, and memory measurements.

## Limitations

- Results describe one Apple M2 machine and one sparse direct solver configuration;
  they are not portable performance guarantees.
- Wall time remains sensitive to operating-system load, power state, and thermal
  conditions even with numerical thread counts fixed.
- Peak RSS is process-wide and cannot attribute SuperLU factorization memory separately
  from Python, SciPy, mesh, and assembled-matrix memory.
- The benchmark covers one linear finite-element analysis per run, not a complete SIMP
  optimization, concurrent API workload, distributed worker, or dataset pipeline.
- No large dense solve is attempted. The dense comparison combines existing N1
  small-case numerical equivalence with an exact storage calculation for larger
  matrix dimensions.
