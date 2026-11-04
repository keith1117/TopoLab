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

Read the [current frontier](docs/validation/p17_m2_continuous_input_profile.md)
and [status](docs/project_status.md). Fresh remote main remains1c38cbf; PR235
and its exact-main four-job CI passed. Captured strict23/46 helpers/core lease
remain; no registration reread. Full input/B/C are unaccepted; P17 unrepaired.
V27 pre-Native suffix STOP, R14 technical PASS/budget FAIL, metadata8 approval
service timeout before CreateProcess and R15 late actual closing remain failures.
Root sampling-gap cause is UNKNOWN; old independent model-capacity error is
separate. Both old source snapshots and all failed/HELD scenes remain preserved.
NEW V33 registered20:13:37.118Z; software/review/publication/public14400s ends
Nov5 00:13:37.118Z. New19800 author seconds add to122400, cumulative142200/
Nov5 09:08Z within original outer151200. Old budgets never reopen or transfer.
Explicit7/5 preserves old4/2+5/3+6/4 protocol bytes/defaults. Regression, distinct
reviews, all-five checks and protected exact-main four-job CI precede public9.
Same fresh reader must obtain harmless permission preflight before actor300.
One public9 remedy; no automatic public10. V34 corrects a prepublication
contract entry typo and funds one R17 plus new final reviewers; R16/old reviews
remain closed. Existing Root/Reader deadlines/counters and real guards apply.
Formalmeta7/gen14/15 remain unprobed; the second attempt needs an explicit NEW
complete within-global wall suffix. Input40/558/1071/2392 reads, whole2484/
helper138/4GiB/240, private copies/hashes/outside anchors/real leases remain.
Known NEW FULL lower228150; other fees UNKNOWN_NOT_ZERO. Original25 preserved;
historical all-paid FAIL/full-fitPENDING/uniform default/fullv2 open remain.
Accepted input→B180→fixed C14580 original Gates. Continuous owner authority
overrides one-slice scheduling stops only.

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
