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

B specification PR200/main1da9740 and all four main CI contexts passed. The owner
has explicitly adopted its complete metric/trust boundary prospectively:
**ADOPTED_PROSPECTIVELY; ENVIRONMENT_NOT_ADMITTED**. For new compatible contract
identities only, all guest-visible backing capacities sum to<=4294967296 bytes,
before the first guest instruction through verified teardown, including guest OS,
devices/firmware and required helpers. Excluded host overhead stays additional
UNKNOWN; this is neither native-proof equivalence nor a whole-host4GiB guarantee.
Old contracts/results remain unchanged. Do not ask for adoption again.
Current authority is this finite adoption documentation, mandatory regression and
normal publication only. The [host-evidence handoff](docs/planning/TopoLab_v2_development_roadmap.md#unique-next-item--host-eligibility-evidence-and-separate-owner-authorization)
lists missing host/provider, permission, identities, capacity/control, independent
review and finite cost/authority fields with responsible parties. No host is
admitted; existing CI is unqualified on available evidence, not proved impossible.
12-hour (8+4)/4-start/1800-second implementation terms remain unapproved. No install,
probe, VM/manual workflow, appliance/algorithm/proof implementation, A2.3, old input/
model/label/index/backup/seal access, experiment, formal retry/reset or successor.
Use versioned documents and necessary committed-source text; follow no old evidence
pointers. No D1/I1 reopening, cap transfer or backend/proof/toy/guard/platform chain.
“Continue” displays the missing evidence/decision only. Retain this worktree and
stop after this adoption slice; do not start the next capability.

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
