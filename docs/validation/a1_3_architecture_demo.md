# A1.3 architecture and demo validation

Date: 2026-09-24

Slice decision: **PASS for architecture and recorded local demo evidence**

Parent revision: `e45702d` (A1.2 local stack)

## Scope and artifacts

This slice adds an original [architecture diagram](../assets/architecture.svg),
its [component map](../architecture.md), and a
[3:39 local demo video](../assets/topolab-local-demo.mp4) with a
[reproduction guide](../demo.md). It changes no numerical behavior, API, frontend,
container, or persistence code. Gate A1 remains open until the separate A1.4 clean
Linux smoke.

The SVG was drawn from this repository's implementation and contracts. It maps
the React workspace, loopback-bound NGINX proxy, FastAPI, bounded in-process
`RunManager`, numerical core, and named-volume SQLite store. It explicitly shows
the restart and cancellation limits. No figure or code from the unlicensed upstream
repository was reused.

## Capture and observed path

The video was recorded from the existing Compose stack on a macOS arm64 host with
Docker Linux arm64 containers and a real Chromium browser at 1600 × 900. It is a
silent 24 fps H.264 MP4. The 219-second cut removes waiting time and adds short
English scene captions. Its convergence scene holds an unaltered screenshot from
the same live browser session for eight seconds for legibility. No numerical values
or UI states were synthesized. Disposable run records were kept on an isolated
Compose volume during capture; neither the volume nor the raw recording is in Git.

| Evidence | Observation |
|---|---|
| Submit and complete | The default `8 × 4 × 3` workspace problem succeeded after 33 iterations; convergence was reported, final compliance was `0.015694445373841445`, and mean physical density was approximately `0.30`. |
| Progress and cancellation | A separate `32 × 12 × 6` problem showed live iteration progress and was cancelled at iteration 52. |
| Restart and recovery | The API container was restarted; the UI then read both terminal records from SQLite with their successful and cancelled states intact. |
| Convergence and 3D result | The successful run showed 33 state-consistent history entries and the 3D physical-density view. At density threshold `0.30`, 44 of 96 cells were visible. |

These demo values are observations of one local run, not new numerical acceptance
thresholds or benchmark results. The validated canonical case and its criteria are
documented in [A1.1](a1_1_canonical_demo.md); broader v1 evidence is in the
[release validation](v1_release_validation.md).

## Artifact checks

- The SVG parses as XML and was visually inspected at presentation size.
- FFmpeg decoded all 5,256 video frames without error and reported 3:39.00,
  1600 × 900, 24 fps H.264 video with no audio. The final convergence and 3D
  scenes were visually inspected.
- SHA-256 of `topolab-local-demo.mp4`:
  `33ca6d3f53b071c64a31db666cd95d4d0d38fb26bb28e612e518c7ea460a4093`.
- The repository pre-commit gate passed: `uv sync --dev --locked`,
  `uv run ruff check .`, `uv run mypy src`, `uv run pytest`, and
  `git diff --check`.

## Limits

The restart demonstrates durable **terminal run-record recovery**, not optimizer
checkpoint/resume. A running job interrupted by API process exit is marked failed.
Cancellation is cooperative between iterations and cannot preempt a sparse solve.
The local stack has no authentication, hosted-service guarantee, process-isolated
worker, or resource quota. This recording does not substitute for the A1.4 clean
Linux installation and frontend-build smoke.
