# Contributing

TopoLab is an individual portfolio and research-software project in active v2
development. Read [AGENTS.md](AGENTS.md), [current status](docs/project_status.md)
and the [repository policy](docs/repository_policy.md) before changing or
publishing a slice.

Keep each change reviewable on a short-lived deliverable branch from current
`main`. Preserve provenance and numerical conventions; add an independent test
before changing established numerical behavior. External implementation requires
its own license and attribution in [PROVENANCE.md](PROVENANCE.md).

Run these checks before every commit:

```bash
uv sync --dev --locked
uv run ruff check .
uv run mypy src
uv run pytest
git diff --check
```

Run frontend type checks, tests and build when that workspace changes. Merge
through a PR only after all exact-head CI checks pass. Scope claims to the
supporting evidence; keep failed Gates and all charges in the published record.

Commit source, contracts, protocols and validation reports. Keep generated
experiment data, models, run artifacts, caches, secrets and device identifiers
outside Git. Update the current status, relevant roadmap/indices and one history
entry at research closeout. README stays a concise public entry point.
