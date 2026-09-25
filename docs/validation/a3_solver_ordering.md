# A3 sparse solver ordering: paired performance and numerical audit

Date: 2026-09-25

Source revision before this slice: `874ccd0a4705c3af6e6ed6a21a4053fd10f21b60`

Status: **Gate A3 passes for the measured larger sparse-solve target.** This is
not a full-workload acceleration or broader scalability gate.

## Scope and selection

The fixed three-step SIMP profile on the local Apple M2 showed that sparse
factorization, rather than assembly, filtering, OC, or serialization, dominated
the `30 x 12 x 6` case: four `splu` calls consumed 1.262 s within 1.634 s of
profiled optimizer wall time. The earlier sparse benchmark also showed solve
time rising much faster than assembly time over the fixed mesh ladder.

This slice changes only SuperLU's column permutation for reduced systems with
at least **5,000 free DOFs**. The default uses `MMD_AT_PLUS_A` there and retains
`COLAMD` below the threshold. Callers can explicitly select `COLAMD` as the
historical fallback. The stiffness matrix, reduced-system elimination, pivot
check, force vector, filter, OC update, iteration budget, and convergence
tolerance are unchanged. The frozen M0/M1/M2 case meshes are below this threshold,
so this change does not rewrite their historical labels or outcomes. Larger
queries must record the new ordering policy in their numerical environment.

## Matched Apple arm64 benchmark

The two orderings were run from the **same code revision** on the fixed
`topolab.benchmark` four-mesh ladder. The explicit `COLAMD` path matches the
previous `splu` default. Every case ran in an isolated subprocess with one cold
pass and three repeated passes. All numerical-library thread controls were set
to one. Hardware: Apple M2, macOS 26.5, Python 3.12.10, NumPy 2.5.3, SciPy 1.18.1.
The benchmark keeps the same domain, material, support, and load specified in
[`sparse_solver_benchmark.md`](sparse_solver_benchmark.md).

Times below are cold / median repeated **assembly plus solve plus setup** in
seconds; peak RSS is process-wide and includes imports and allocator retention.

| Mesh | DOF / free DOF | NNZ | COLAMD time | Default time | Repeated ratio | COLAMD / default peak RSS |
|---|---:|---:|---:|---:|---:|---:|
| `10 x 4 x 2` | 495 / 450 | 25,389 | 0.0140 / 0.00260 | 0.0031 / 0.00256 | 0.984 | 239.5 / 240.0 MiB |
| `20 x 8 x 4` | 2,835 / 2,700 | 178,425 | 0.0478 / 0.04197 | 0.0419 / 0.03872 | 0.922 | 281.8 / 269.5 MiB |
| `30 x 12 x 6` | 8,463 / 8,190 | 575,757 | 0.3882 / 0.38343 | 0.2285 / 0.21948 | 0.572 | 402.2 / 444.6 MiB |
| `45 x 18 x 9` | 26,220 / 25,650 | 1,884,960 | 3.6269 / 3.65057 | 2.2082 / 2.19187 | 0.600 | 762.4 / 744.5 MiB |

The three repeated totals at `30 x 12 x 6` were 0.3770–0.3842 s for
`COLAMD` and 0.2099–0.2220 s for the new default. At `45 x 18 x 9` they were
3.6197–3.6539 s and 2.0989–2.2289 s. The two smaller meshes still select
`COLAMD`; their minor timing differences are run noise and are not an
optimization claim. The large mesh's measured peak RSS was **42.5 MiB higher**
under the new default, so no lower-memory claim is made.

## Complete optimization phase profile and numerical checks

On the `30 x 12 x 6` fixed three-step SIMP case, the inclusive cProfile phases
were as follows. Inclusive times overlap, especially OC with filter application
and solve with factorization; they must not be summed. The JSON serialization
sample converts the final densities and three history rows to lists; it is timed
outside the optimizer and is not a production API end-to-end measurement.

| Phase | COLAMD | Default |
|---|---:|---:|
| Profiled optimizer wall | 1.634 s | 1.033 s |
| Sparse factorization | 1.262 s | 0.644 s |
| Assembly | 0.114 s | 0.121 s |
| Filter construction | 0.114 s | 0.113 s |
| Filter application | 0.0052 s | 0.0047 s |
| OC update | 0.0058 s | 0.0060 s |
| JSON serialization sample | 0.0056 s | 0.0053 s |

The two fixed-ordering finite-element solves matched on small-mesh displacement
and reactions under the frozen `1e-9` sparse/dense relative tolerance. A
three-step large-mesh optimizer comparison matched design and physical density
within `rtol=1e-9, atol=1e-12`, and final compliance within `rtol=1e-9`.
Across the four sparse benchmark meshes, the largest relative compliance
difference was `1.02e-12`, and all equilibrium residuals remained below `1e-8`.

One further paired `30 x 12 x 6` optimizer run held the **same 60-iteration cap**
and `0.01` convergence tolerance. Both paths reached the cap without convergence;
the final design-density maximum difference was `9.83e-12` and relative
compliance difference `6.80e-14`. Wall time was 23.57 s for `COLAMD` and
13.65 s for the new default on this single run. This is a bounded nonconverged
trajectory check, not a new successful label or final quality result.

## Linux x86-64 replication and gate decision

The [A3 Linux workflow](https://github.com/keith1117/TopoLab/actions/runs/36109560023)
passed the same four-case paired benchmark and three-step phase profile on an
Ubuntu 24.04 x86-64 runner (Linux 6.17.0-1022-azure, four logical CPUs,
15.6 GiB reported memory, Python 3.12.3, NumPy 2.5.3, SciPy 1.18.1). The
one-thread controls matched the Apple protocol. The workflow checked matching
environment, sparse structure, `1e-9` relative compliance, and `1e-8`
equilibrium limits. JSON outputs were stored as a CI artifact, not in Git.

| Mesh | COLAMD cold / repeated | Default cold / repeated | Repeated ratio | COLAMD / default peak RSS |
|---|---:|---:|---:|---:|
| `10 x 4 x 2` | 0.0061 / 0.00393 s | 0.0061 / 0.00391 s | 0.994 | 285.7 / 283.0 MiB |
| `20 x 8 x 4` | 0.0586 / 0.04887 s | 0.0590 / 0.04995 s | 1.022 | 306.8 / 309.9 MiB |
| `30 x 12 x 6` | 0.4376 / 0.43888 s | 0.2936 / 0.27995 s | 0.638 | 414.2 / 405.3 MiB |
| `45 x 18 x 9` | 5.0121 / 4.96206 s | 3.6457 / 3.54186 s | 0.714 | 1088.1 / 949.4 MiB |

The three Linux repeated totals for the larger meshes were 0.4227–0.4470 s
versus 0.2790–0.2819 s, and 4.8477–4.9799 s versus 3.5324–3.5493 s. The
largest relative compliance difference was `1.32e-12`; the largest equilibrium
residual was below `8.0e-12`. The smaller meshes retain exactly the same
factorization ordering. Linux's 1.022 medium ratio is timing noise between
equivalent code paths, not a measured optimization regression.

The Linux three-step optimizer profile likewise reduced inclusive factorization
time from 1.423 to 0.920 s and profiled optimizer wall from 1.847 to 1.326 s.
Assembly, filter construction/application, OC, and serialization were also
recorded in the workflow log; their totals were small relative to factorization
and are inclusive/overlapping. CI quality, frontend, clean Linux stack smoke,
and the dedicated sparse-ordering workflow all passed on this PR. Local required
validation passed with **272 tests**, Ruff, mypy, locked sync, and diff checks.

**Gate A3 decision:** The selected factorization bottleneck has a stable
same-protocol repeated-time gain at both larger ladder scales on both tested
architectures, while smaller scales keep the former numerical path. Frozen
small-mesh tolerances and larger-mesh compliance/equilibrium checks pass. The
Apple large-mesh peak-RSS increase remains an explicit tradeoff. The optimized
uniform ordering policy is now frozen before B2's workload pilot; B2 must record
this policy and use it equally for uniform and candidate refinement.

The claim is limited to the measured larger sparse-solve and three-step SIMP
cases. This does not establish a converged end-to-end workload speedup, general
scalability, or learned acceleration. B2 must define and test its actual
repeated-query workload against the optimized uniform path.

## Reproduction

```bash
uv sync --dev --locked
PYTHONPATH=src uv run python -m topolab.benchmark --repeated-runs 3 --ordering COLAMD --output /tmp/a3-colamd.json
PYTHONPATH=src uv run python -m topolab.benchmark --repeated-runs 3 --ordering auto --output /tmp/a3-auto.json
python3 scripts/a3_benchmark_compare.py /tmp/a3-colamd.json /tmp/a3-auto.json
PYTHONPATH=src uv run python scripts/a3_optimizer_profile.py --ordering COLAMD
PYTHONPATH=src uv run python scripts/a3_optimizer_profile.py --ordering auto
```

The workflow fixes `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
`MKL_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`, and `BLIS_NUM_THREADS` to `1`, and
disables dynamic OpenMP/MKL threading. Reproduction should set the same variables.
No benchmark JSON, dataset, model, or generated optimization result is committed.
