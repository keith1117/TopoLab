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

The 2026-11-16 finite integration has actual public acceptance: container PID
namespace/detached helpers and producer/independent FULL60 returns passed.
[Integration](docs/validation/public_containment_full60_input.md) and
[input result](docs/validation/full60_input_admission.md) retain complete evidence.
Public metadata passed; formal metadata attempt1 STOPPED because its22,943,707-byte
plan exceeded the frozen16MiB reader cap before payload. Both metadata quotas
are1/1 consumed; no metadata attempt2/reset/retry or input successor is allowed.
Input0/6, Original-registration/Foundation/Library/B/C0; P17 remains unrepaired.

The [lossless byte-bound repair](docs/planning/metadata_plan_byte_bound_repair.md)
removes only a redundant parsed preflight copy, retains original raw/hash and
checks full plan size before target IO. Its13,504,549-byte projection is software
only; the stopped attempt stays FAIL/RSS UNKNOWN. Close required regression,
normal protected result publication and external retention, then STOP. The next
owner decision is one concrete fresh finite metadata/input authority, not an
automatic guard/toy chain, replacement identity or reopened allowance.

Original10:15–18:15UTC/Root and lead28800s, FULL<=24000/result7200 remain finite.
New FULL360 raises known lower334530 to334890; other fees UNKNOWN_NOT_ZERO.
K12721.16417100014444982>7200/all-paid FAIL, full-fit PENDING4GiB/uniform default,
all old failures/costs/UNKNOWN/seals and original25 dirty files/HEAD/index/status
remain. No scientific B/C, fit, search or final seal is granted.

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
