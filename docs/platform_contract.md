# Platform contract and run lifecycle

Status: **frozen at Gate P1 in v0.3.0**. Contract changes require a documented reason
and regression-test update.

## Scope

The first platform slice wraps the validated `v0.2.0` numerical core without exposing
NumPy or SciPy objects to HTTP callers. It provides:

- immutable Pydantic models for one structured Hex8 optimization problem;
- JSON-serializable optimization results and state-consistent iteration history;
- an in-memory run manager with explicit lifecycle states;
- cooperative cancellation between optimizer iterations;
- a minimal FastAPI adapter for creating, reading, and cancelling runs.

Database persistence, restart recovery, authentication, distributed workers, Redis,
frontend code, dataset generation, and ML are outside this slice.

## Problem and result boundary

`TopologyProblem` records the structured mesh, material, fixed-face supports, point or
equal-node face-resultant loads, optimization settings, and optional initial density.
Unknown fields and non-finite values are rejected. Cross-field validation ensures
that material and density bounds are consistent, point-load nodes lie inside the
mesh, and an initial density has exactly one value per element.

`TopologyResult` contains final design and physical density, compliance,
displacements, reactions, convergence status, and every post-update history state.
Arrays are converted to immutable tuples internally and JSON arrays at the HTTP
boundary.

## Run states

Each run has one generated identifier and follows one of these transitions:

```text
queued -> running -> succeeded
                  -> failed
                  -> cancelled
queued ----------------> cancelled
```

- `succeeded` is the only state containing a result.
- `failed` contains a concise exception type and message; another run is unaffected.
- Cancellation is cooperative. A queued run can be cancelled immediately; a running
  optimization observes cancellation between iterations, so an active sparse solve
  may finish before the state becomes `cancelled`.
- Terminal states cannot be cancelled again.

The current executor uses a bounded thread pool. Each run owns an immutable problem,
private numerical arrays, cancellation event, status, and result. This establishes
data and failure isolation for concurrent in-process runs, but it is not process
isolation and does not survive application restart.

## HTTP surface

| Method and path | Behavior |
|---|---|
| `POST /runs` | Validate a `TopologyProblem`, enqueue it, and return `202` with a run snapshot |
| `GET /runs/{run_id}` | Return the current snapshot or `404` |
| `POST /runs/{run_id}/cancel` | Request cancellation, return `404` if unknown or `409` if terminal |

The API owns and shuts down its default `RunManager`. Tests and embedding callers can
inject an explicit manager with a bounded worker count.

## Gate P1 evidence

The `v0.3.0` release passed and documented:

- queued/running/terminal state transitions;
- queued and running cancellation behavior;
- failure isolation;
- result isolation for two concurrent tasks;
- request validation and HTTP error semantics;
- the repository-wide locked dependency, lint, type, and test checks.

The full evidence matrix and limitations are recorded in
`docs/validation/p1_platform_validation.md`.

## Post-P1 persistence work

Optional SQLite persistence and explicit process-restart semantics are additive work
after the frozen v0.3.0 contract. Their provisional contract is documented in
`docs/run_persistence.md`; the default remains in-memory unless a database path or
store is supplied. The same post-P1 contract defines UTC run timestamps and stable
cursor pagination through `GET /runs`.
