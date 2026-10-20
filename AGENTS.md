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

Historical v1 is a usable interim delivery. The owner retains
**FULL_V2_OPEN_NO_ADMITTED_ROUTE**, fixed P/17/unrepaired,4GiB and independent
preflight. Uniform stays default; full v2 still requires reproducible same-quality
learned end-to-end acceleration. I1 public software is published through PR197/198,
main57c73b8 and all four main CI contexts passed. Its mandatory selected-host
pre-entry lifetime UNKNOWN closes NO_ADMISSIBLE_ROUTE, not measured>4GiB or
scientific acceptance. Read [current status](docs/project_status.md) for evidence,
retained failures/costs/quotas/seals and the one next item.

Read the [R1 plan](docs/planning/TopoLab_v2_delivery_execution_plan.md) after the
[English reassessment](docs/planning/TopoLab_v2_delivery_reassessment.md).
Reassessment Section4 methods are effective; the [roadmap Section6](docs/planning/TopoLab_v2_development_roadmap.md#6-current-sequence-after-the-delivery-reassessment)
separates current rules, historical observations and pending acceptance advice.
The English roadmap controls scientific Gate order; README is the public entry.
No scientific threshold, budget, access or concrete environment admission changes.
B4.51 FAIL_PROCESS_SOURCE_FREEZE/consumed1/1 quotas, D1 STOP/unlaunched0/1/FULL60,
owner-closed rescue and solver-internal rejection remain; B4.52 NOT_SELECTED_BY_R1.
Known-paid12721.16417100014444982>7200 cannot pass unchanged all-paid feasibility;
full fit PENDING4GiB and every old UNKNOWN/seal remain. Read applicable frozen
contracts before dependent work; unresolved substantive conflicts stop that work.

B guest-capacity adoption remains ADOPTED_PROSPECTIVELY; ENVIRONMENT_NOT_ADMITTED,
for compatible future guest contracts only; excluded host overhead UNKNOWN.
The owner separately adopted B4.30-style RSS/full-exit empirical acceptance for
NEW M2 native identity only, retaining4GiB and independent preflight. This is
not a-priori allocation assurance or a change to old I1/D1/B contracts.

M2 H stage A is closed through PR202/203/main65bbbd3. Old
[R/v1](docs/planning/p17_m2_input_export_preparation_protocol.md) remains
STOP_NO_RETRY / FAIL_FULL_NAMED_WALL_CHARGE_BINDING:109.224s+10>immutable20s,
final serializer exit1, full RSS UNKNOWN, old reads0, R0/R1 closed unlaunched.
Failed FULL120+shared FULL60=180/1860s; closed1680s never transfers. Source PR204/
main43ffed0 preceded entry; result PR205/main3459dd5 and all four main CI passed.

R/v2 source PR206/main04d14c9 passed all-four CI, but formal preparation closed
unlaunched when its original independent window expired: roles/old reads/IO0,
UNKNOWN_NOT_RUN. Result PR207/main e1e52f3/all-four CI completed. Old v1/v2
frozen files, STOP/costs and closed allowances retain bytes and never transfer.

[R/v3](docs/planning/p17_m2_input_export_readiness_protocol.md) stays STOP_NO_RETRY:
3/6 launched, metadata12 attempted/11 hash rows;12th identity field/cause UNKNOWN.
Payload0/12/528/18; failed full RSS UNKNOWN/exits1/1. Paid300/closed1560 remains.
PR209/main85644c4/all-four CI and merged-branch cleanup completed, worktree retained.
Original result overrun18.633086s and separate followup335.755696s remain costs.

F public software implementation/review is complete; local2290 passed/1 platform skip.
The **F-only** grant under the unchanged
[proposal](docs/planning/p17_m2_input_failure_diagnostic_repair_proposal.md)/[JSON](docs/planning/p17_m2_input_failure_diagnostic_repair_proposal.json):
executor2h preparation, fresh different author1h, one90min regression/protected
publication. [F report](docs/validation/p17_m2_input_failure_recording_repair.md)
records public-fixture-only failure tuples, whole-wall/cost and RSS/exit repair;
measurement completeness never turns payload failure into PASS. D remains
UNRUN_NOT_AUTHORIZED, old cause/full RSS UNKNOWN. No old stat/read, D/environment-identity/power query,
R retry, B/C, reset or successor. Retain4GiB/independent preflight and all old
contracts/costs/quotas/seals. Only normal publication remains; afterward STOP and do not restart F.
Verify the associated PR/main CI rather than repeating completed implementation.

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
