# A1.2 local stack validation

Date: 2026-09-24

Slice decision: **PASS on macOS arm64 with Docker's Linux arm64 runtime**

Parent revision: `b714c97` (English planning documents)

## Scope

This slice packages the existing FastAPI and React application as a two-service local
Compose stack. It adds no numerical behavior, API route, frontend feature, worker
isolation, ML experiment, or persistence-schema change. Gate A1 remains open pending
the architecture/demo evidence and clean Linux smoke in A1.3–A1.4.

## Reproducibility and data boundary

- Both Dockerfiles pin base and tool images by version and multi-architecture digest.
- The API installs the existing `uv.lock` with `uv sync --locked --no-dev --no-editable`;
  the frontend installs its existing `package-lock.json` with `npm ci`.
- The API runs as UID/GID `10001`; the frontend runs as UID/GID `101` in the
  unprivileged NGINX image. Only the frontend maps a host port, on `127.0.0.1:8080`.
- `/runs` is proxied to the API on the internal Compose network. A health-checked API
  starts before the frontend.
- SQLite is stored at `/data/topolab.sqlite3` on the `topolab-data` named volume.
  The images copy only application code and installed dependencies or compiled static
  assets. No database, generated result, dataset, or model artifact is copied.

## Observed smoke

The following checks passed on Docker Engine 29.5.2 / Compose 5.1.4, Linux arm64
containers on a macOS arm64 host:

| Check | Observation |
|---|---|
| `docker compose config -q` | Exit 0 |
| `docker compose build` | API and frontend images built |
| `docker compose up --build -d` | Both services started; API healthy |
| `GET /` through `127.0.0.1:8080` | HTTP 200 with frontend HTML |
| `GET` the built frontend JavaScript asset | HTTP 200, JavaScript content type |
| `GET /runs` through the same origin | HTTP 200 |
| `POST /runs` with unchanged `canonical_demo_v1.json` | HTTP 202, run ID `90847a5340bd45598d15a224d2a7e1f8` |
| Poll `GET /runs/{run_id}` | `succeeded`, 16 iterations, converged, compliance `0.08167931393462119` |
| `docker compose restart api`, then read same run | Same successful record and compliance returned |
| `docker compose up --build -d` after the smoke | Both containers recreated; the same successful record remained readable |
| Container identity | API UID/GID 10001; frontend UID/GID 101 |
| SQLite path | `/data/topolab.sqlite3` exists on the named volume |

The scalar result is a smoke observation, not a new cross-platform numerical
tolerance or performance claim. The existing canonical problem and core tests retain
their own acceptance criteria.

The repository's pre-commit gate also passed: `uv sync --dev --locked`,
`uv run ruff check .`, `uv run mypy src` (27 source files), `uv run pytest`
(265 passed), and `git diff --check`.

## Limits

This test did not use a clean Linux host or Linux x86-64; that environment belongs
to A1.4. The stack is for a trusted local machine. It inherits the v1 in-process
executor and interruption semantics and provides no authentication, quotas,
checkpoint/resume, hosted service, or production deployment claim.
