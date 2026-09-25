# TopoLab agent instructions

## Read before changing code

Read these files in order:

1. `PROVENANCE.md`
2. `docs/numerical_conventions.md`
3. `docs/reference_baseline.md`
4. `docs/planning/TopoLab_reimplementation_strategy.md`
5. `docs/planning/TopoLab_development_timeline_and_resources.md`
6. `docs/planning/TopoLab_post_v1_development_roadmap.en.md`
7. The contracts and latest validation reports relevant to the requested slice.

## Current project state

The historical `v1.0.0` release and Gates N1, N2, P1, M0, and A1 are complete.
M1 did not establish learned acceleration; M2 failed its data gate; the bounded
M3 v1 pre-registration was superseded before fitting or final evaluation. The
active v1.x roadmap requires reproducible, same-quality ML end-to-end acceleration
on a predefined workload before the full flagship project is delivered. Until
that evidence exists, uniform initialization is the operational default and no
accelerated claim is allowed.

The current Track B sequence begins with development-only warm-start feasibility
evidence in `docs/validation/ml_feasibility_probe.md`. The next independent slice
is B1: diagnose numerical convergence and learned-quality failures before new
training. Follow the active English roadmap for later gates and slice order.

## Provenance boundary

The Hack3D reference repository has no declared open-source license. Do not copy,
translate, patch, vendor, or redistribute its code, comments, file structure, or
figures. Implement from published equations and independent derivation. Use the fixed
upstream commit only for historical behavior comparison, and record any comparison or
new source in `PROVENANCE.md`.

## Development rules

- Keep each change scoped to one numerical behavior with tests.
- Freeze conventions in `docs/numerical_conventions.md` before relying on them.
- Prefer the current small module plan; split modules only when stable responsibilities
  or multiple callers justify it.
- Do not add FastAPI, React, Redis, PyTorch, data generation, or ML before gate N2.
- Do not claim `validated`, `scalable`, or `accelerated` until the documented evidence
  gate is complete.
- Never commit generated datasets, run artifacts, caches, secrets, or device IDs.

## Required validation

Run before every commit:

```bash
uv sync --dev --locked
uv run ruff check .
uv run mypy src
uv run pytest
git diff --check
```

If a numerical test requires a tolerance change, explain the scale/conditioning reason
in the validation report; do not silently loosen it.
