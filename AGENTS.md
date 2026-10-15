# TopoLab agent instructions

## Read before starting work

At session start, slice start and context recovery, read these files in order:

1. `PROVENANCE.md`
2. `docs/numerical_conventions.md`
3. `docs/reference_baseline.md`
4. `docs/planning/TopoLab_reimplementation_strategy.md`
5. `docs/planning/TopoLab_development_timeline_and_resources.md`
6. `docs/planning/TopoLab_v2_delivery_reassessment.md` (English working reference)
7. `docs/planning/TopoLab_v2_development_roadmap.md`
8. `docs/project_status.md`
9. The contracts and latest validation reports relevant to the requested slice.
10. `docs/repository_policy.md` before staging or publishing changes.

## Current project state and delivery direction

Historical v1.0.0 is complete and usable as an interim delivery. Full v2 remains
open and still requires reproducible same-quality learned end-to-end acceleration.
Uniform is the default; original B4.2/scientific FAIL and fixed P/17 remain.

B4.51 closed FAIL_PROCESS_SOURCE_FREEZE: changing a frozen reviewer triggered
S02. Its217/404 are post-stop TEXT results only, not protocol acceptance.
Primary/independent quotas are each1/1 consumed; no further formal call/reset/retry.
See [report](docs/validation/b4_51_real_certification_executable_full_resource_preregistration.md)
and [current status](docs/project_status.md) for all retained evidence and stops.

The owner-approved [English delivery reassessment](docs/planning/TopoLab_v2_delivery_reassessment.md)
is the development reference, with a [Chinese reading companion](docs/planning/TopoLab_v2_交付复盘与后续开发约束.md).
Read the [R1 execution plan](docs/planning/TopoLab_v2_delivery_execution_plan.md)
after that reassessment. R1 closed NO_ADMISSIBLE_ROUTE under current authority;
unchanged all-paid7200 is impossible and direct dense certification fails the
large-mesh paper memory bound. B4.52 is NOT_SELECTED_BY_R1. The unique next item
is owner decision D1: a proposed new1260s/4GiB full-size exact-physics integration
feasibility capability, with limited eight-train-label access and a new identity.
It is NOT AUTHORIZED; a plain “continue” grants no budget/access or old retry.
No automatic text/toy/guard chain. Review progress after at most two capability slices.

Known-paid12721.16417100014444982>7200 cannot pass unchanged all-paid feasibility.
All old failures/costs/UNKNOWN, fixed models, stopped mechanisms, consumed quotas
and final/conditional48/720/unused48 seals remain. Real executable is UNFROZEN,
certificates/cost UNKNOWN_STOP, full fit PENDING4GiB. No new budget, real input,
FEM/integration/fit/search, old retry/reset or sealed grant follows this planning
change. Software RSS fills no historical/full-fit gap. Read the applicable frozen
contracts before dependent work; unresolved conflicts stop that work.

A later “continue” finishes the current authorized slice first; after closure it
authorizes only the next item in current status. Close one slice and stop. The
English v2 roadmap controls scientific Gate order; README is the public entry.

## Provenance boundary

The Hack3D reference repository has no declared open-source license. Do not copy,
translate, patch, vendor, or redistribute its code, comments, file structure, or
figures. Implement from published equations and independent derivation. Use the fixed
upstream commit only for historical behavior comparison, and record any comparison or
new source in `PROVENANCE.md`.

## Development rules

- Follow the delivery reassessment: feasibility first, an explicit blocker/capability
  result per slice, and enforced preflight/freeze/stop controls before formal calls.
- Before commit/push, recheck current rules/status and actual records; do not rely
  only on memory or rerun completed formal experiments.
- Keep each change scoped to one numerical behavior with tests.
- Freeze conventions in `docs/numerical_conventions.md` before relying on them.
- Prefer the current small module plan; split modules only when stable responsibilities
  or multiple callers justify it.
- Do not add FastAPI, React, Redis, PyTorch, data generation, or ML before gate N2.
- Do not claim `validated`, `scalable`, or `accelerated` until the documented evidence
  gate is complete.
- Never commit generated datasets, run artifacts, caches, secrets, or device IDs.
- Follow `docs/repository_policy.md`: keep protocols and validation reports in Git,
  keep generated evidence external, and stage only reviewed paths.
- Close slices by updating current status, one history entry and the relevant
  roadmap section/index. Keep this file concise; do not append the full chronology.
  Update README for public usage/claims changes or final delivery, not every slice.
- Name branches by deliverable without `codex` or other agent-name tokens;
  merge PRs only after CI passes and report the next slice after each slice.

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
