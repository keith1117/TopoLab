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

Read [identity2 closure/coordination contract](docs/planning/p17_m2_registered_input_v2_protocol.md)
and [actual failures/frontier](docs/validation/p17_m2_input_closure_coordination_repair.md).
Original strict23/46 helper exits/core lease release remain captured after
PR234/mainc684a321/main4CI; later metadata STOP remains. V16 R8 all five checks
3404PASS/one platform skip and metadata-public-v5 passed software scope only.
Full public1 late-start STOP and public2 certificate38/41 STOP plus true
407.761>240 resourceFAIL remain. Public2 result close also exceeded1800s by43.605.
V16/V20 genuinely closed FAILED; old costs/quotas/HELD scenes remain. PUBLIC3
now passes six roles,40/558 per author,1071 members, real lease/backup/certificate;
firstSUP539ms, coordination8.861<240s. Its194-member paired metadata/full audit
and timely581.273s result close pass in PUBLIC scope only. R10 all five checks
3447PASS/one platform skip and finalsource unchanged; R9 source-change FAIL stays.
Root/I full fee replay gives conservative87600<100000 each, known NEW FULL lower
150030/other totalsUNKNOWN. V24 auxiliary author close overrun>=32.212s remains
FAIL; its old allowance never reopens. Original25 hashes/index/status match.
NEW V22 software10:49:00.022→12:49:00.022Z2026-11-04; originalROOT/I21:38Z stays.
Preparation actually closed12:46:29.352Z,7049.330/7200s/Root183calls; oldunused
closes. Newpublication7200s/128calls each ends14:46:29.352Z. Protected exact-head/main4CI publication,
formal metadata4 and independent preflight precede Original/Library IO. No formal
input or B/C is yet accepted. ExactSource2484/helper138/4GiB/40-558-1071 remain;
targets8/9 fixed/unprobed. Input→B180→fixedC14580 retains original scientific
Gates. Historical all-paid12721.16417100014444982>7200 FAIL, full-fitPENDING4GiB,
P17unrepaired/uniformdefault/fullv2open and every old STOP/cost/UNKNOWN/seal remain.
Owner continuous authority overrides one-slice scheduling stops only.

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
