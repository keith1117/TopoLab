# TopoLab — Reproducible 3D Topology Optimization Platform

TopoLab is an independently implemented 3D SIMP topology-optimization platform. It
combines a validated sparse finite-element and optimization core, typed HTTP and
persistence boundaries, a React results workspace, and reproducible learned
warm-start experiments.

Version `1.0.0` consolidates the completed numerical, platform, benchmark, and
experiment evidence. Gates N1, N2, P1, and M0 passed. The frozen M1 comparison was
negative or inconclusive, and the pre-registered M2 follow-up stopped at its failed
data gate after 10 of 756 cases did not converge. Uniform initialization therefore
remains the operational default; TopoLab makes no learned-acceleration claim.

## Scope

The first implementation targets a structured rectangular Hex8 mesh, isotropic
linear elasticity, small deformation, single-load-case minimum-compliance SIMP,
point and face loads, density filtering, and an Optimality Criteria
update.

Development is gated in this order:

1. validate the finite-element and SIMP numerical core;
2. benchmark sparse assembly and solving;
3. add API, job execution, persistence, and visualization;
4. generate versioned cases and evaluate learned density-field warm starts.

## Version 1 limits

- unstructured meshes or CAD import;
- nonlinear, dynamic, thermal, or multi-physics analysis;
- multiple materials or manufacturing constraints;
- GPU finite-element solving;
- an end-to-end neural replacement for the physics solver;
- distributed or process-isolated workers, authentication, and quotas; and
- a hosted production deployment or public online demo.

The sparse numerical path has reproducible performance evidence, but the project does
not claim universal scalability. SQLite restart recovery preserves run records; it is
not optimizer checkpoint/resume.

## Release evidence

| Area | Evidence | Decision |
|---|---|---|
| Hex8 finite elements | [`docs/validation/n1_fem_validation.md`](docs/validation/n1_fem_validation.md) | Gate N1 passed |
| SIMP optimization | [`docs/validation/n2_optimization_validation.md`](docs/validation/n2_optimization_validation.md) | Gate N2 passed |
| API and run isolation | [`docs/validation/p1_platform_validation.md`](docs/validation/p1_platform_validation.md) | Gate P1 passed |
| Sparse performance | [`docs/validation/sparse_solver_benchmark.md`](docs/validation/sparse_solver_benchmark.md) | Four scales benchmarked |
| M0 data foundation | [`docs/validation/m0_catalog_v2_materialization.md`](docs/validation/m0_catalog_v2_materialization.md) | Gate M0 passed, 160/160 labels |
| M1 training and held-out evaluation | [`docs/validation/m1_training.md`](docs/validation/m1_training.md), [`docs/validation/m1_held_out_evaluation.md`](docs/validation/m1_held_out_evaluation.md) | No learned-acceleration claim |
| M2 bounded follow-up | [`docs/validation/m2_catalog_materialization.md`](docs/validation/m2_catalog_materialization.md) | Data gate failed; fitting not started |
| v1 release verification | [`docs/validation/v1_release_validation.md`](docs/validation/v1_release_validation.md) | Full locked test, build, package, and repository audit passed |

## Development setup

Requirements: Python 3.12, [`uv`](https://docs.astral.sh/uv/), and Node.js 24 or later.

```bash
uv sync --dev --locked
uv run ruff check .
uv run mypy src
uv run pytest

cd frontend
npm ci
npm run typecheck
npm test
npm run build
```

## Canonical local demo

Run the versioned `canonical-demo.v1` problem with one command after installing the
locked Python environment:

```bash
PYTHONPATH=src uv run --locked python -m topolab.demo --output-dir /tmp/topolab-demo
```

The command prints one JSON line with the run ID, terminal status, convergence flag,
compliance, final physical volume fraction, and absolute result path. The result file
contains the complete public run snapshot, including the problem, iteration history,
and final density fields. Choose an output directory outside any Git repository;
omitting `--output-dir` creates a new temporary directory. The example input is
[`src/topolab/examples/canonical_demo_v1.json`](src/topolab/examples/canonical_demo_v1.json)
and can also be submitted unchanged to `POST /runs`.

This small `4 x 2 x 2` cantilever is a local numerical demonstration. It does not
establish a hosted demo, production service, or broad performance claim. A1.1 smoke
evidence is recorded in
[`docs/validation/a1_1_canonical_demo.md`](docs/validation/a1_1_canonical_demo.md).

## Local API and frontend stack

With Docker and Compose installed, start the A1.2 local stack from the repository root:

```bash
docker compose up --build -d
```

Open <http://127.0.0.1:8080>. The frontend serves its built assets and sends `/runs`
requests through the same-origin proxy to the API. The API persists run records in a
Docker named volume. For a command-line check, submit the unchanged canonical case:

```bash
curl -fsS -X POST -H 'Content-Type: application/json' \
  --data-binary @src/topolab/examples/canonical_demo_v1.json \
  http://127.0.0.1:8080/runs
```

The response contains a `run_id`; inspect it at
`http://127.0.0.1:8080/runs/<run_id>`. Stop containers with `docker compose down`;
the named volume remains for later starts. `docker compose down -v` also deletes the
database and run history. The stack is bound to loopback and is intended for local
demonstration. It retains the v1 in-process worker and restart semantics described in
[`docs/run_persistence.md`](docs/run_persistence.md); it has no authentication,
resource quotas, or optimizer checkpoint/resume. Build and smoke evidence is recorded
in [`docs/validation/a1_2_local_stack.md`](docs/validation/a1_2_local_stack.md).

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
The English [v1.x development roadmap](docs/planning/TopoLab_post_v1_development_roadmap.en.md)
links to English counterparts of the other three planning documents; the original
Chinese versions remain alongside them.
Frontend scope and local development are documented in
[`docs/frontend.md`](docs/frontend.md).
The first M0 data and evaluation contract is documented in
[`docs/ml_experiment_contract.md`](docs/ml_experiment_contract.md). Its typed manifest,
recoverable executor, bounded content-identified catalog, and safe production
entrypoint are implemented, together with the fixed uniform, physics-heuristic, and
training-only nearest-neighbor runner. The v1 attempt and its four terminal
non-convergence failures are documented in
[`docs/validation/m0_catalog_materialization.md`](docs/validation/m0_catalog_materialization.md);
the zero-failure v2 execution and Gate M0 decision are documented in
[`docs/validation/m0_catalog_v2_materialization.md`](docs/validation/m0_catalog_v2_materialization.md).
The frozen M1 fitting boundary, model, loss, budget, and checkpoint-selection rule
are documented in [`docs/m1_training_contract.md`](docs/m1_training_contract.md).
Plan the production fit without opening label artifacts or writing checkpoints with:

```bash
PYTHONPATH=src uv run python -m topolab.training_cli \
  --data-root <external-m0-v2-root> \
  --artifact-root <external-m1-root>
```

Add `--execute` only for the reviewed five-seed production run. Test and OOD labels
remain outside this entrypoint's fitting path.
The completed production run, five selection/checkpoint hashes, runtime, resource
use, and current claims boundary are recorded in
[`docs/validation/m1_training.md`](docs/validation/m1_training.md).
The completed held-out comparison, artifact hash, per-seed results, failure audit,
and negative/inconclusive M1 gate decision are recorded in
[`docs/validation/m1_held_out_evaluation.md`](docs/validation/m1_held_out_evaluation.md).
A single bounded follow-up is pre-registered in
[`docs/m2_experiment_contract.md`](docs/m2_experiment_contract.md). It changes data
coverage and adds a finite validation-calibrated reliability gate while keeping the
M1 model and fitting recipe fixed. Its materialization audit and failed data-gate
decision are recorded in
[`docs/validation/m2_catalog_materialization.md`](docs/validation/m2_catalog_materialization.md);
the experiment stopped before fitting so the reserved ID-test and OOD evidence was
not used for learned evaluation.

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
That repository declares no open-source license. Its behavior and fixed commit are
documented in [PROVENANCE.md](PROVENANCE.md); TopoLab's code was implemented
independently from published SIMP and Hex8 references.

## Claims policy

`Validated` refers only to the numerical behaviors covered by the N1/N2 evidence.
`Benchmark` claims refer only to the recorded sparse cases and environment. The
project does not describe the platform as universally scalable or ML-accelerated.

## License

TopoLab's original code and documentation are licensed under the [MIT License](LICENSE).
This license does not apply to external repositories, papers, or datasets.
