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

Read the [CI-clock/input frontier](docs/validation/p17_m2_ci_clock_and_input_continuation.md)
and [status](docs/project_status.md). Main1c38cbf/PR235 all-four CI remain.
PR236 head1efe is unmerged: three CI jobs pass; quality1FAIL/3472PASS/37skip
from a public fixture using current UTC beyond old v2's21:38Z deadline. Local
RED reproduces; production expiry rejection is correct. Inject explicit test
clock and retain expired negative; do not loosen production clocks or Gates.
Old R14 wallFAIL/R15 late-returnMISS/R16STOP/R17 all-five3509PASS remain.
R18 closed1FAIL/3536PASS/1skip: old public9 fixture omitted the new pinned
context read. Failed source60/original terminal are retained in a76-member
independent pair. NEW software-only V36/R20 once fixes that fixture; four pure
old/new-context cases pass. Production/protocol bytes and V35 clocks stay.
Captured strict23 per old author/46 helpers/core lease release remain; no
registration reread. Full input/B/C unaccepted, P17 unrepaired/uniform default.
NEW V35 actual22:12:50.485Z; software14400s includes preregistration latency,
endsNov5 02:12:49.237Z. New8520 author seconds add to142200, cumulative150720/
Nov5 11:30Z inside unchanged original151200/11:38Z outer. All old elapsed,
fees, counters and closed quotas stay; old Root378 used/1606 unused closed.
Fresh Reader conservatively starts at preregistration22:12:49.237Z;45660s
ends10:53:49.237Z, stronger than global. Actual startup endpoint is UNKNOWN.
Explicit8/6 preserves old4/2+5/3+6/4+7/5 bytes/defaults. New regressions,
distinct reviews/all-five/protected PR/exact-main4CI precede FIRST public9.
Same fresh reader actual harmless prefix help must precede actor300; unchanged
120+60/110/30 guards; no automatic public10 or Source8. Public9 name was never
created; only its unstarted allocation changes, not an old failed scene.
New registered6 PUBLIC7/formalmeta8/gen16/17 at same parent remain unprobed.
Source40/558/1071/2392 reads, whole2484/helper138/4GiB/240/private copies/hashes/
outside anchors/real leases remain. Remedy2 wall stays CLOSED absent explicit
NEW full within-global suffix. Accepted input→B180→fixed C14580 original Gates.
KnownNEWFULL lower254550; other fees UNKNOWN. Original25 preserved; old v1
primary closure hash matches but exact old tmp mirror Missing/causeUNKNOWN.
No recreation, reset, lease unlock or scientific repair claim. Continuous owner
authority overrides one-slice scheduling stops only.

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
