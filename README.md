# TopoLab

TopoLab is a planned, independently implemented platform for validated 3D SIMP
topology optimization. The project will combine a sparse finite-element numerical
core, reproducible experiment workflows, and a controlled evaluation of learned
warm starts.

> **Status:** Gate P1 has passed for the `v0.3.0` in-memory platform. It combines the
> validated numerical core with serializable problem/result contracts, isolated run
> state, cooperative cancellation, and a minimal HTTP adapter. Post-P1 development
> adds optional SQLite run persistence, explicit restart recovery, and paginated run
> history. The React workspace consumes that contract for run history, result detail,
> problem configuration, submission and cancellation, and interactive 3D
> physical-density inspection with state-consistent convergence charts. A reproducible
> sparse assembly/solve benchmark now records four mesh scales, wall time, matrix
> storage, and peak memory. The first M0 slices freeze versioned ML case identity,
> tensor/label semantics, leakage-safe splits, baselines, and evaluation rules, and
> implement deterministic case encoding, warm-start volume projection, a typed
> dataset manifest with verified partitions and provenance metadata, and validated
> single-case label generation with content-addressed, checksum-verified atomic
> artifacts plus an append-only, atomically recoverable manifest-to-label index.
> A single-process executor now materializes supplied manifests in canonical order
> with per-case checkpoints and interruption recovery. Process workers, broad
> scalability evidence, a bounded production case catalog, and ML remain incomplete.

## Intended scope

The first implementation targets a structured rectangular Hex8 mesh, isotropic
linear elasticity, small deformation, single-load-case minimum-compliance SIMP,
point and face loads, density filtering, and an Optimality Criteria
update.

Development is gated in this order:

1. validate the finite-element and SIMP numerical core;
2. benchmark sparse assembly and solving;
3. add API, job execution, persistence, and visualization;
4. generate versioned cases and evaluate learned density-field warm starts.

## Non-goals for the first release

- unstructured meshes or CAD import;
- nonlinear, dynamic, thermal, or multi-physics analysis;
- multiple materials or manufacturing constraints;
- GPU finite-element solving;
- an end-to-end neural replacement for the physics solver.

## Development setup

Requirements: Python 3.12, [`uv`](https://docs.astral.sh/uv/), and Node.js 24 or later.

```bash
uv sync --dev
uv run ruff check .
uv run mypy src
uv run pytest

cd frontend
npm ci
npm run typecheck
npm test
npm run build
```

## Repository map

```text
docs/
  numerical_conventions.md     Numerical definitions that code and tests must follow
  ml_experiment_contract.md    Frozen M0 case, representation, split, and evaluation rules
  reference_baseline.md        Frozen upstream reference and known limitations
  planning/                    Admissions, schedule, and implementation planning
  validation/                  Gate evidence, thresholds, results, and limitations
src/topolab/                   TopoLab package and finite-element foundation
tests/                         Package and numerical convention tests
frontend/                      React/TypeScript optimization workspace
```

The platform contract and run lifecycle are documented in
[`docs/platform_contract.md`](docs/platform_contract.md); the additive persistence
contract is in [`docs/run_persistence.md`](docs/run_persistence.md).
Frontend scope and local development are documented in
[`docs/frontend.md`](docs/frontend.md).
The first M0 data and evaluation contract is documented in
[`docs/ml_experiment_contract.md`](docs/ml_experiment_contract.md). Its typed manifest
and recoverable executor do not yet define or materialize the bounded production case
catalog and therefore do not constitute a passed M0 gate.

## Sparse solver benchmark

The fixed local benchmark uses isolated single-threaded workers, one cold numerical
run, and three repeated runs at each of four mesh sizes. On the recorded Apple M2
environment, the `45 x 18 x 9` case completed with 726.44 MiB peak process RSS; one
equivalent dense global `float64` matrix would require an estimated 5.12 GiB before
factorization or workspace. These results support the sparse solver design without
claiming that the entire platform is universally scalable.

Reproduce the machine-readable report with:

```bash
PYTHONPATH=src uv run python -m topolab.benchmark \
  --repeated-runs 3 \
  --output results/sparse_solver_benchmark.json
```

Methodology, full measurements, numerical guards, and limitations are recorded in
[`docs/validation/sparse_solver_benchmark.md`](docs/validation/sparse_solver_benchmark.md).

## Provenance

TopoLab is not a fork or redistribution of the Hack3D reference implementation.
That repository currently declares no open-source license. Its behavior and fixed
commit are documented in [PROVENANCE.md](PROVENANCE.md), while TopoLab's code will
be implemented independently from published SIMP and Hex8 references.

## Claims policy

The README and application materials will use `validated`, `scalable`, and
`accelerated` only after the corresponding gates and reproducible evidence in
[`docs/planning`](docs/planning/) are complete.

## License

TopoLab's original code and documentation are licensed under the [MIT License](LICENSE).
This license does not apply to external repositories, papers, or datasets.
