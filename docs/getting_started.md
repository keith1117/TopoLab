# Getting started

These are the current local execution paths. The recorded demonstration is in
[the demo walkthrough](demo.md); working constraints and research progress are
in [project status](project_status.md). Uniform initialization remains the default.

The commands below keep experiment and runtime outputs separate from committed
source. Full v2 delivery and learned acceleration remain gated by the
[active roadmap](planning/TopoLab_v2_development_roadmap.md).

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

Run the following demo, stack and benchmark commands from the repository root.

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
[`src/topolab/examples/canonical_demo_v1.json`](../src/topolab/examples/canonical_demo_v1.json)
and can also be submitted unchanged to `POST /runs`.

This small `4 x 2 x 2` cantilever is a local numerical demonstration. It does not
establish a hosted demo, production service, or broad performance claim. A1.1 smoke
evidence is recorded in
[`docs/validation/a1_1_canonical_demo.md`](validation/a1_1_canonical_demo.md).

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
demonstration. The current default uses the A2.1
[local process worker](platform_worker_protocol.md) and A2.2
[leased run ownership](run_ownership.md). It has no authentication,
resource quotas, or optimizer checkpoint/resume. Build and smoke evidence is recorded
in [`docs/validation/a1_2_local_stack.md`](validation/a1_2_local_stack.md).

The [architecture diagram](architecture.md) and
[recorded local walkthrough](demo.md) explain the implemented data flow,
restart behavior, cancellation, convergence, and 3D result view. Their evidence and
limits are recorded in
[`docs/validation/a1_3_architecture_demo.md`](validation/a1_3_architecture_demo.md).

## Clean Linux stack smoke

From a fresh Linux checkout with Docker Engine, Compose, and Python 3 installed, use
this disposable project to repeat the A1.4 end-to-end check:

```bash
docker compose -p topolab-a14 up --build --wait -d
python3 scripts/a1_clean_linux_smoke.py
docker compose -p topolab-a14 down -v
```

The build installs locked Python and frontend dependencies inside the images. The
smoke reads the built frontend and its JavaScript asset, submits the unchanged
canonical problem through `/runs`, checks its result and the SQLite file, restarts
the API, and verifies that the terminal result and run-history entry survive. It
prints one JSON summary with elapsed times. The final command removes only this
project's disposable database volume. Run it on a machine where local port `8080`
is available; the stack serves only `127.0.0.1`.

The same path runs on a fresh Ubuntu runner in CI. Its recorded environment,
timings, and Gate A1 decision are in
[`docs/validation/a1_4_clean_linux_smoke.md`](validation/a1_4_clean_linux_smoke.md).

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
  --output /tmp/topolab-sparse-benchmark.json
```

Methodology, full measurements, numerical guards, and limitations are recorded in
[`docs/validation/sparse_solver_benchmark.md`](validation/sparse_solver_benchmark.md).
