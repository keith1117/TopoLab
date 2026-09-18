# Frontend run-history workspace

Status: **first post-P1 frontend slice; 3D visualization is not included yet**.

## Scope

The React/TypeScript workspace in `frontend/` consumes the frozen run-history
contract without importing numerical-core code. It provides:

- a newest-first list of lightweight run summaries;
- status totals for the currently loaded pages;
- cursor-based incremental loading;
- on-demand retrieval of one full run result;
- final compliance, convergence, element count, iteration, volume, and density-change
  inspection; and
- explicit loading, empty, API-error, failed-run, and cancelled-run states.

History pages intentionally omit displacement, reaction, and density arrays. Those
arrays are requested only after the user selects one run. 3D density rendering,
problem submission, cancellation controls, filtering, and authentication are outside
this slice.

## Local development

Install both locked environments from the repository root:

```bash
uv sync --dev --locked
cd frontend
npm ci
```

Run the API in one terminal:

```bash
uv run uvicorn topolab.api:create_app --factory --reload
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

Component tests cover empty history, cursor pagination, detail loading, result metrics,
UTC labeling, small-screen detail navigation, and recovery from an API error. CI runs
these checks independently from the Python quality job. Browser QA uses Playwright CLI
against the real Vite application and API; generated screenshots and traces remain
untracked artifacts.
