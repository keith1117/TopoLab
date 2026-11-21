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

## Current state and execution entry

The [November 21 result](docs/validation/metadata_input_20261121.md) closes the
[finite contract](docs/planning/metadata_input_20261121.md). Formal metadata
passed all 23 bindings under 16 MiB. Public input accepted three of six roles.
Exporter R1 timed out after 278 of 558 public payload receipts, its external
record stayed unopened and the public lease marker is HELD. Formal input and
scientific B/C remain unadmitted.

The [R1 throughput result](docs/validation/public_input_r1_throughput.md) checked
558 reads and 1,071 members on rebuilt public bytes with an actual 22.412 s
software return. The final staged public source contains all 598 files and
yielded the same version in an 11.443 s external return. Next obtain a fresh
strict 23-file registration at that path before a new named input grant.

Booked charges were 2,640 FULL including the nonrefundable shared reservation.
The R1 elapsed-time floor raises the cumulative known lower bound to 337,539 FULL.
Other fees remain UNKNOWN_NOT_ZERO. Preserve the November 16 metadata failure, all consumed quotas, prior costs, seals and both original
dirty workspaces. Real containment, detached helpers and FULL60 have already
passed. Fixed P/17 is unrepaired, uniform is default, full fit is PENDING4GiB
and the all-paid failure remains.

## Provenance boundary

The Hack3D reference repository has no declared open-source license. Do not copy,
translate, patch, vendor, or redistribute its code, comments, file structure, or
figures. Implement from published equations and independent derivation. Use the fixed
upstream commit only for historical behavior comparison, and record any comparison or
new source in `PROVENANCE.md`.

## Development rules

- Specify deliverable-linked acceptance and obtainable resource evidence before
  choosing an algorithm; satisfy existing applicable contracts. Debug public
  software and complete checks before freeze; enforce preflight/freeze/STOP.
- Measure P/17 failures/quality gap, fully charged speed, resource admission and
  used/remaining budget; unmeasured stays UNKNOWN. At most two ineffective
  capability slices require a route decision, never automatic continuation.
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
