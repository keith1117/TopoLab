# Frontend run-history workspace

Status: **run history and final 3D physical-density visualization implemented**.

## Scope

The React/TypeScript workspace in `frontend/` consumes the frozen run-history
contract without importing numerical-core code. It provides:

- a newest-first list of lightweight run summaries;
- status totals for the currently loaded pages;
- cursor-based incremental loading;
- on-demand retrieval of one full run result;
- final compliance, convergence, element count, iteration, volume, and density-change
  inspection;
- an interactive thresholded 3D view of the final physical-density field; and
- explicit loading, empty, API-error, failed-run, and cancelled-run states.

History pages intentionally omit displacement, reaction, and density arrays. Those
arrays and the immutable problem geometry are requested only after the user selects
one run. Problem submission, cancellation controls, convergence charts, history
filtering, and authentication are outside this slice.

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

Component and geometry tests cover empty history, cursor pagination, detail loading,
result metrics, x-fast density mapping, interior-face removal, thresholding, UTC
labeling, small-screen detail navigation, and recovery from an API error. CI runs
these checks independently from the Python quality job. Browser QA uses Playwright CLI
against the real Vite application and API; generated screenshots and traces remain
untracked artifacts.
