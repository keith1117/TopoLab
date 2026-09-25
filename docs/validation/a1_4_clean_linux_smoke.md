# A1.4 clean Linux stack validation

Date: 2026-09-25

Slice decision: **PASS**

Gate A1 decision: **PASS for the documented local-stack path on clean Ubuntu
24.04 x86-64**. This is a local reproducibility gate, not a hosted or production
service claim.

Parent revision: `6cfdd1b` (A1.3 architecture and demo evidence)

## Method and environment

The new `clean-linux-smoke` CI job checked out implementation commit `d9ab8de`
on a fresh GitHub-hosted `ubuntu-24.04` runner. Its
[successful run](https://github.com/keith1117/TopoLab/actions/runs/36095264051)
recorded Linux `6.17.0-1022-azure x86_64`, Python `3.12.3` on the runner, Docker
Engine `28.0.4` (`linux/amd64`), and Compose `v2.38.2`. The API image uses pinned
Python `3.12.10`; the web build uses pinned Node `26.2.0`. The separate frontend CI
job used Node 24 and also passed its lockfile install, type check, 22 tests, and
production build.

The runner used the committed `compose.yaml` and
[`scripts/a1_clean_linux_smoke.py`](../../scripts/a1_clean_linux_smoke.py) without
project data or prebuilt TopoLab artifacts. Its commands were:

```bash
docker compose -p topolab-a14 config -q
docker compose -p topolab-a14 up --build --wait -d
python3 scripts/a1_clean_linux_smoke.py
docker compose -p topolab-a14 down -v
```

The image build executed `uv sync --locked --no-dev --no-editable`, `npm ci`, and
`npm run build` from the committed lockfiles. The CI job removed its isolated
containers, network, and SQLite named volume after the checks. No generated run
snapshot, database, or build output was committed.

## Observed result

| Check | Fresh Linux observation |
|---|---|
| Build and start | Both images built and services reached Compose readiness in 50 s. |
| Frontend | `GET /` returned HTML; its referenced built JavaScript asset returned JavaScript. |
| API | `GET /runs` returned a JSON run page; posting the unchanged `canonical_demo_v1.json` through the same-origin proxy returned HTTP 202. |
| Canonical result | Run `29f6d13d7ab24474a7251eec63c02b37` succeeded and converged in 16 iterations; compliance was `0.0816793139346208`, physical volume was `0.500000006944751`, and the run completed in 1.016 s after submission. |
| Contract checks | Result had 16 physical-density cells and 16 history entries; final history compliance agreed with final compliance within the existing `1e-9` relative check, and volume error was below the existing `5e-3` bound. |
| SQLite and identity | The SQLite file existed and was nonempty at `/data/topolab.sqlite3`; API and web containers ran as UIDs `10001` and `101`. |
| Restart/read | After `docker compose restart api`, the complete terminal snapshot was unchanged and `GET /runs?limit=10` still listed the successful run; restart and read took 4.690 s. |
| Cleanup | `down -v` removed the disposable containers, network, and named volume. |

The smoke checker took 5.962 s after the stack was ready. These timings are one
runner observation, not a performance guarantee; image pulls, network speed, cache
state, and runner load can change build time. The canonical compliance is likewise
an observation, while the frozen numerical checks remain in
[A1.1](a1_1_canonical_demo.md) and the numerical gate reports.

The same checker passed locally on macOS arm64 with Docker Linux arm64, using an
isolated temporary port `18080` because an unrelated existing TopoLab stack owned
`8080`. The local successful run had 16 iterations and compliance
`0.08167931393462119`. The temporary port override and its volume were outside Git
and were removed after the dry run.

## Gate A1 and limits

The documented one-path Compose command built the complete stack from a fresh Linux
checkout; the fixed canonical case reached a valid terminal result in a stated time;
the smoke checked the API, SQLite restart behavior, and served frontend assets; and
the frontend's separate Linux CI job built and tested the UI. The A1.1–A1.3
reports cover the canonical case, container packaging, architecture, and recorded
interaction. Together these meet Gate A1 as defined in the
[v2 roadmap](../planning/TopoLab_v2_development_roadmap.md).

This evidence covers one fresh Ubuntu x86-64 runner. The Linux smoke reads built
assets but does not automate browser interaction; the A1.3 video shows that flow on
the prior local stack. The frontend build emitted Vite size warnings for its Plotly
chunks; they did not prevent the build and are not a loading-performance result.
The service is bound to loopback and has no authentication, quotas,
process-isolated worker, optimizer checkpoint/resume, or hosted deployment.
It does not establish universal scalability or learned acceleration.

The repository's required pre-commit gate also passed locally for this slice:
`uv sync --dev --locked`, `uv run ruff check .`, `uv run mypy src`,
`uv run pytest` (265 passed), and `git diff --check`. The fresh Linux CI quality job
independently passed the same source checks and 265 Python tests.
