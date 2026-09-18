# Gate P1 platform validation

Date: 2026-09-18  
Release: `v0.3.0`  
Audited implementation baseline: `d12e179`

## Scope and decision

Gate P1 is **passed** for the first in-memory TopoLab platform boundary. The evidence
covers immutable and JSON-serializable problem/result contracts, explicit run-state
transitions, queued and cooperative running cancellation, failure isolation,
concurrent result isolation, and the minimal HTTP surface.

This decision permits frontend and public-demo work against the frozen `v0.3.0`
contract. It does not validate persistence, restart recovery, authentication,
process-isolated or distributed workers, scalability, a dataset contract, or ML.

## Implementation slice reviewed

| Pull request | Scope | Squash commit |
|---|---|---|
| `#10` | Problem/result contracts, run lifecycle, cancellation hooks, and FastAPI adapter | `d12e179` |

The platform layer is original TopoLab work. It calls the independently implemented
numerical core through the documented public contract and does not use source code,
comments, file structure, or figures from the unlicensed Hack3D reference repository.

## Evidence matrix

| Behavior | Executable evidence | Acceptance criterion | Result |
|---|---|---|---|
| Problem validation | `tests/test_problem.py` | Reject missing supports/loads, invalid density length/bounds, out-of-mesh nodes, booleans, and extra fields | Pass |
| Problem/result serialization | Point-load solve and JSON round trip | Restored result equals the original immutable result | Pass |
| Supported load contracts | Point-load and face-resultant solves | Both execute through the public contract and converge | Pass |
| Numerical job completion | `tests/test_jobs.py` with the real solver | `queued/running -> succeeded`, converged result retained | Pass |
| Queued cancellation | One worker occupied while a second run is queued | Second run becomes `cancelled` at iteration zero with no result | Pass |
| Running cancellation | Cooperative cancellation probe | Run becomes `cancelled`, request flag is retained, and no result is exposed | Pass |
| Shutdown cancellation | Manager closes with a running probe | Cooperative cancellation reaches the terminal state | Pass |
| Failure isolation | One deliberate failure beside one successful run | Failed run records its error; successful run and result are unaffected | Pass |
| Concurrent result isolation | Two workers synchronize at a barrier | Both execute concurrently and retain distinct result objects and values | Pass |
| HTTP creation and lookup | `tests/test_api.py` | Valid request returns `202`; completed lookup returns `200` and its result | Pass |
| HTTP error semantics | Invalid, unknown, and repeated-cancel requests | Return `422`, `404`, and `409`, respectively | Pass |

## Measured results

- The real `4 x 2 x 1` numerical job reached `succeeded` after 13 recorded iterations
  and returned a converged result.
- The queued-cancellation case ended at iteration zero. The running-cancellation case
  retained `cancel_requested=true` and exposed no partial result.
- The concurrency case required both worker threads to reach the same barrier before
  either could complete. Both runs succeeded with separate result objects and their
  own marker values.
- The failure-isolation case recorded `ValueError: deliberate test failure` for one
  run while the other run succeeded with no error.
- HTTP tests observed the specified `202`, `200`, `404`, `409`, and `422` status codes.
- The release candidate completed all 126 repository tests without warnings.

No numerical tolerance or Gate N1/N2 behavior changed during the Gate P1 audit.

## Reproduction

Environment details are recorded in `docs/development_environment.md`; exact Python
dependencies are locked in `uv.lock`. Run from the repository root:

```bash
uv sync --dev --locked
uv run ruff check .
uv run mypy src
uv run pytest
git diff --check
```

Release-candidate result: 126 tests passed on Python 3.12.10, macOS 26.5, Apple M2.
The implementation PR and post-merge `main` quality checks also passed before this
audit.

## Known limits after P1

- Run state and results live only in memory and are lost on application restart.
- The bounded thread pool provides in-process data and failure isolation, not process
  isolation or distributed execution.
- Cancellation is checked between optimizer iterations; an active sparse solve is not
  preempted.
- Full results are returned in the run snapshot; pagination, streaming, and artifact
  storage are not implemented.
- Authentication, authorization, rate limiting, database persistence, Redis, and
  external workers are outside this release.
- No runtime or memory benchmark has been completed, so the project does not claim
  scalability.
- Frontend, public deployment, dataset generation, and ML are not included in
  `v0.3.0`.
