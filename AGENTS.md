# TopoLab agent instructions

## Read before changing code

Read these files in order:

1. `PROVENANCE.md`
2. `docs/numerical_conventions.md`
3. `docs/reference_baseline.md`
4. `docs/planning/TopoLab_reimplementation_strategy.md`
5. `docs/planning/TopoLab_development_timeline_and_resources.md`
6. `docs/planning/TopoLab_v2_development_roadmap.md`
7. The contracts and latest validation reports relevant to the requested slice.

## Current project state

The historical `v1.0.0` release and Gates N1, N2, P1, M0, and A1 are complete.
M1 did not establish learned acceleration; M2 failed its data gate; the bounded
M3 v1 pre-registration was superseded before fitting or final evaluation. The
active v2 roadmap requires reproducible, same-quality ML end-to-end acceleration
on a predefined workload before the full flagship project is delivered. Until
that evidence exists, uniform initialization is the operational default and no
accelerated claim is allowed.

Track B has development-only warm-start feasibility evidence in
`docs/validation/ml_feasibility_probe.md`, B1 failure diagnosis in
`docs/validation/b1_failure_diagnosis.md`, and A3 solver-ordering evidence in
`docs/validation/a3_solver_ordering.md`. The fixed B2 workload pilot is recorded
in `docs/validation/b2_workload_pilot.md`: Gate B2 failed because three of six
larger uniform references did not converge at the frozen limit and the five
unchanged M1 starts were slower after fallback charges. B2.1's opt-in,
versioned physical-plateau policy made all twelve uniform references
quality-feasible; its matched five-seed M1 panel remains slower after fallback
charges. See `docs/validation/b2_1_convergence.md`. B2.2 froze a bounded
quality-aligned development-prototype plan, but only 53/61 uniform data
sentinels converged at 120 updates. B2.3 preserved all 61 source cases,
versioned their iteration cap to 240, and passed 61/61 independent quality
checks without changing the previous 53 accepted outcomes. See
`docs/validation/b2_2_data_feasibility.md` and
`docs/validation/b2_3_data_feasibility.md`. The next independent slice is
B2.4: a complete, versioned 522-case development-label materialization and
data gate. Do not fit a model or freeze a new final ML contract until its
development data gate and prototype screening pass. Follow the v2 English
roadmap for later gates and slice order.

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
