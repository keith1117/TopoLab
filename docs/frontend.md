# Frontend optimization workspace

Status: **problem submission, run history, and final 3D physical-density visualization implemented**.

## Scope

The React/TypeScript workspace in `frontend/` consumes the frozen run-history
contract without importing numerical-core code. It provides:

- a newest-first list of lightweight run summaries;
- a structured problem form for mesh, material, one fully fixed face, one signed
  face-resultant load, and SIMP settings;
- client-side cross-field validation followed by authoritative API validation;
- immediate insertion and selection of a newly submitted asynchronous run;
- polling of the selected active run until it reaches a terminal state;
- status totals for the currently loaded pages;
- cursor-based incremental loading;
- on-demand retrieval of one full run result;
- final compliance, convergence, element count, iteration, volume, and density-change
  inspection;
- an interactive thresholded 3D view of the final physical-density field; and
- explicit loading, empty, API-error, failed-run, and cancelled-run states.

History pages intentionally omit displacement, reaction, and density arrays. Those
arrays and the immutable problem geometry are requested only after the user selects
one run. Cancellation controls, convergence charts, dynamic multiple-support/load
editing, point-load editing, initial-density import, history filtering, and
authentication are outside this slice.

## Problem submission contract

The first form deliberately exposes one common cantilever-style problem without
inventing a second frontend schema. Its JSON payload is the frozen `TopologyProblem`:
structured element counts and lengths, isotropic material values, one fully fixed
face, one equal-node face resultant, and all current SIMP controls. The signed load
value carries direction; the axis selector never encodes sign.

The browser rejects non-finite values, invalid integer counts, invalid material and
density bounds, and zero loads before requesting the API. The API remains the source
of truth, and structured FastAPI validation locations are rendered as readable field
paths. A successful `202` response is placed at the top of the loaded history and
selected without a redundant detail request. While that selection is `queued` or
`running`, the client polls its detail every 500 ms and stops on a terminal state.

## Density visualization contract

The renderer uses the final filtered `physical_density`, not design density or an
intermediate iteration. It reconstructs element coordinates from the frozen
x-fast convention:

```text
element(ex, ey, ez) = ex + nx * (ey + ny * ez)
```

Each selected element occupies its physical cell within the problem's declared
`lengths`. The density threshold is inclusive (`rho >= threshold`). Only faces next
to the domain boundary or a hidden neighbor are sent to Plotly, so internal faces
between adjacent visible cells are removed. The color scale remains fixed to
`rho in [0, 1]` so different thresholds and runs remain visually comparable.

Plotly's GL3D-only distribution is loaded only after a successful result is selected.
This keeps the run-history entry bundle independent from the larger WebGL
visualization chunk and avoids shipping unrelated 2D trace implementations.

## Local development

Install both locked environments from the repository root:

```bash
uv sync --dev --locked
cd frontend
npm ci
```

Run the API in one terminal:

```bash
uv run uvicorn --app-dir src topolab.api:create_app --factory --reload
```

Run Vite from `frontend/` in another terminal:

```bash
npm run dev
```

Vite proxies `/runs` to `http://127.0.0.1:8000`. A deployed frontend uses the same
origin by default; `VITE_API_BASE_URL` can set an explicit API origin when the hosting
topology also provides the required routing or CORS policy.

## Quality checks

```bash
cd frontend
npm run typecheck
npm test
npm run build
```

Component, API-client, and geometry tests cover form validation, exact submission
payloads, readable API errors, active-run polling, empty history, cursor pagination,
detail loading, result metrics, x-fast density mapping, interior-face removal,
thresholding, UTC labeling, small-screen detail navigation, and recovery from an API
error. CI runs these checks independently from the Python quality job. Browser QA
uses Playwright CLI against the real Vite application and API; generated screenshots
and traces remain untracked artifacts.
