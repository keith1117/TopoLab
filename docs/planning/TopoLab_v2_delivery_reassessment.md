# TopoLab v2 Delivery Reassessment and Development Rules

English working reference for development. [Chinese reading companion](./TopoLab_v2_交付复盘与后续开发约束.md).
Keep both versions aligned. Resolve any substantive discrepancy before proceeding
with work that depends on it.

Date: 2026-10-15 (America/New_York). Reassessment baseline: main
`335c295fa401cf648e0ae2a802c347e9ccecaafb`, after B4.51 closed as a failure.
This document records the retrospective, new expectations and development rules
accepted by the owner in the reassessment conversation. It changes delivery
governance; it is not a new numerical experiment contract, scientific Gate or
budget authorization.

Current scheduling after D1 (2026-10-15): R1's
[execution plan](TopoLab_v2_delivery_execution_plan.md) remains historical
NO_ADMISSIBLE_ROUTE under its then-current authority. The owner subsequently
explicitly approved complete D1. [D1 closed](../validation/d1_physics_resource_feasibility.md)
STOP_UNKNOWN_PREFIT_BOUND before implementation/real input; no formal call,
no label/model/index read, new roles closed unlaunched0/1 and FULL60 retained.
B4.52 remains NOT_SELECTED_BY_R1. The unique next owner decision is to close the
current exact-physics rescue program under unchanged4GiB/prefit requirements
(recommended); no executable successor or transferred budget/access/quota.
Sections5–6 retain historical original R1 instructions, not authority to repeat
R1/reopen D1. All old Gates, costs, UNKNOWN, quotas and seals remain.

## 1. Owner-confirmed goals

- `v1.0.0` is a completed milestone that can be demonstrated. Later platform
  improvements retain its value as an interim delivery.
- Full v2 remains a flagship goal and requires evidence of same-quality,
  end-to-end learned acceleration. Platform maturity and negative experimental
  findings cannot substitute for that positive scientific condition.
- Further work must deliver capabilities with explicit acceptance evidence, or
  eliminate infeasible routes using bounded evidence. More slices, documents,
  tests or audit predicates cannot substitute for delivery progress.
- Engineering reliability can improve; no model's positive scientific outcome
  can be guaranteed in advance.

This document governs how further work proceeds. The [English v2 roadmap](TopoLab_v2_development_roadmap.md)
continues to control scientific Gate order, and existing frozen contracts control
each experiment's access, tolerances, budget and stopping rules. This document
only replaces the current default scheduling of B4.52; it does not retroactively
rewrite historical successor decisions.

## 2. Original expectations, current state and completion estimate

The [original G0 development handbook](https://github.com/keith1117/TopoLab/blob/9e08cbbf1c02e426720189f79d8e8563a4d045e6/docs/planning/TopoLab_development_timeline_and_resources.md)
distinguished a runnable MVP, a strong CS/SWE platform and a flagship project. It
allowed an honest platform delivery after negative ML results. The later v2 plan
made positive ML evidence a mandatory delivery condition; the original 10–14-week
estimate cannot guarantee its research duration. A more ambitious goal needs an
overall feasibility, budget and exit decision, rather than indefinitely appended
small slices.

At this baseline, the numerical core, sparse performance, API/SQLite/React,
data and experiment foundations exist. A1/A3, B3 and B4.1 remain complete in their
respective scopes. A2.1–A2.2 are complete; A2.3–A2.4 and A4 remain pending within
their own scopes. Learned reliability, a complete new B4, a compatible final
contract and B5 remain incomplete. See the [v1 release validation](../validation/v1_release_validation.md),
[A2.2 record](../validation/a2_2_run_ownership.md) and [current status](../project_status.md).

The management estimate for full v2 is approximately **60% (55%–65%)**. The weights
and partial credits below were assigned for this reassessment. They are not an
existing contract score, a statistical confidence interval, a research success
probability or a fraction of remaining working hours. This is a historical
snapshot of the baseline above; update it using new evidence rather than treating
it as a fixed progress value.

| Delivery capability | Management weight | Estimated credit | Evidence and gap |
|---|---:|---:|---|
| Numerical core and performance evidence | 20 | 20 | Original validation scope complete |
| Platform and job reliability | 20 | 15 | Main functions usable; complete recovery and resource boundaries pending |
| Data, training and experiment infrastructure | 15 | 15 | B3/B4.1 complete |
| Stable same-quality learned acceleration | 25 | 5 | Local positive results do not establish complete reliability acceptance |
| Final ID/OOD evaluation and independent reproduction | 15 | 0 | Not executed |
| Final release and presentation | 5 | 4 | Interim demonstration exists; full-v2 closeout pending |

The credit totals 59/100, rounded to approximately 60%. The remaining work contains
the largest research uncertainties and may consume most of the subsequent time.
An unpassed Gate remains unpassed regardless of this estimate; the percentage
cannot justify declaring v2 delivered.

## 3. Overall B4 retrospective

B4.1–B4.51 are 51 development slices covering fitting, diagnosis, software and
text work, not 51 independent training attempts.

| Phase | Progress made | Unresolved blocker |
|---|---|---|
| B4.1–8 | Fitting, timing engineering repairs and development confirmation | Larger confirmation found quality failures after smaller-scope passes |
| B4.9–14 | Failure diagnosis, additional refinement and terminal-state preservation | New cases still failed after old counterexamples improved; costs offset gains |
| B4.15–29 | Physics objectives, local surrogates and gradient verification | Partial correctness progress; excessive cost and unproven full memory |
| B4.30–31 | Reflection repair and review | Fixed P/17 failure unrepaired |
| B4.32–51 | 11 text slices and 9 small public-software slices | No actual FEM/fitting validation or new learned-repair conclusion |

The main problems are:

1. **Reliability repairs did not transfer consistently.** Local B4.5/B4.7 passes
   were followed by failures in larger confirmation. Repairing exposed
   counterexamples does not establish reliability across cases; better MSE or
   local speed cannot replace terminal quality. See [B4.8](../validation/b4_8_rollback_confirmation.md)
   and [B4.30](../validation/b4_30_paid_continuation.md).
2. **Resource feasibility did not eliminate routes early enough.** B4.15 projected
   about 60339 seconds of training against a 7200-second cap. The known-paid
   subtotal under the current accounting, `12721.16417100014444982 > 7200`, cannot
   pass the original all-paid requirement even with zero future added work. This
   subtotal is not the whole-project ledger; projected cost is not incurred cost.
   See [B4.15](../validation/b4_15_offline_compliance_adjoint.md) and
   [B4.34](../validation/b4_34_admissibility_full_cost_preregistration.md).
3. **Avoidable engineering errors consumed formal opportunities.** B4.42's status
   string check error, B4.43's launch import failure, and B4.51's freeze after a
   lint failure followed by frozen-source changes and continued calls are not
   evidence of model failure. In particular, B4.51's freeze and stop handling was
   an execution error; subsequent TEXT results cannot restore compliance. See
   [B4.42](../validation/b4_42_public_enclosure_limitations_real_assembly.md),
   [B4.43](../validation/b4_43_public_assembled_residual_enclosure.md) and
   [B4.51](../validation/b4_51_real_certification_executable_full_resource_preregistration.md).
4. **Certification-tool development drifted away from the delivery critical
   path.** Exact arithmetic and proofs on small public systems have technical
   value, but have not shown that they can improve the real learned method at an
   acceptable cost. The original platform checklist does not generally require
   certification of every operation. If a chosen mathematical route depends on
   it, that dependency still needs a necessity and feasibility justification.
5. **Project decisions across slices were insufficient.** Individually finite
   slices can still produce an indefinitely extended research program through
   continually proposed successors. Earlier work focused too heavily on compliant
   slice closeout without consistently asking whether the next slice shortened
   the path to final acceptance. The budget blocker established in B4.32–34
   should have triggered an overall route decision sooner.

Recent B4 work has therefore drifted from the delivery critical path, and its
execution and project management need correction. Failure retention, independent
audit, seals and complete charging remain necessary. Improvement must come from
route selection and execution quality, without relaxed standards, primary-model
replacement, deleted history or quota resets.

## 4. Mandatory rules for subsequent work

1. **Recover actual evidence first.** At slice start, context recovery and before
   commit or push, reread AGENTS, this document, current status and applicable
   contracts; check latest main, CI, PRs and actual execution records. Current
   entry points set scheduling; old successor wording in frozen history is not
   current authorization.
2. **Each slice must address a delivery blocker or eliminate a route.** Before
   starting, state the baseline, target capability, acceptance evidence,
   dependencies, scope, resources and decision after failure. Documentation or
   guard work must identify what it unlocks and the finite step that reconnects
   it to actual capability validation. Do not create an endless text/toy/limitation
   loop.
3. **Check attainability first.** Review historical paid costs, optimistic added
   costs and simultaneous memory constraints before implementation. If a
   requirement is already unreachable, stop investing in implementation under
   that accounting and present a concrete owner decision. A new contract proposal
   is not a budget grant and cannot exclude old costs or change an old Gate.
4. **Separate failure categories.** Report scientific quality/speed failure,
   resource infeasibility, engineering/process failure and UNKNOWN separately.
   Technical CI, text consistency and small public-software passes do not
   establish scientific acceptance. Missing runtime or cause stays UNKNOWN;
   new runs cannot manufacture historical evidence.
5. **Complete software integration preflight before formal execution.** Use
   authorized public tests to verify the actual interpreter, argv, cwd, import
   and dependency origins, role paths, atomic recording and failure controls.
   Complete required checks before freezing. Production still requires clean,
   locked, merged source with all applicable CI passed. Frozen changes, failed
   preflight or a triggered stop must refuse launch, without automatic repair and
   continuation. Ordinary development tests are not formal calls, and consumed
   formal opportunities cannot be restored.
6. **Limit consecutive ineffective work.** Review changes to critical blockers
   after at most two capability slices. If no blocker closed and no materially
   different route was eliminated, stop appending default successors and make
   an explicit route decision. This two-slice window is a governance review
   limit, not additional experimental quota, budget or authorization to execute
   multiple slices automatically.
7. **Keep interim deliveries available.** Report platform improvements and ML
   research separately. Platform work needs its own authorization and acceptance
   and cannot change a frozen numerical comparison denominator. The positive
   full-v2 delivery condition remains.
8. **Keep records concise and reproducible.** Current status contains current
   conclusions, blockers and the next item. Preserve historical and frozen
   evidence at its original path and contents. Link to details rather than
   copying the entire history into multiple entry points. Summaries must identify
   source revisions, reproduction entry points and necessary external hashes;
   data, models, logs and databases remain outside Git.

At closeout, prioritize what closed or was eliminated, fixed-primary quality and
failure changes, end-to-end cost, simultaneous memory evidence, remaining blockers
and the next step. Check counts are supporting information. All existing required
checks, publication guards, latest-PR-head CI, main CI and review requirements
continue to apply.

## 5. Current scheduling and next item R1

The former proposal **B4.52 is deferred (DEFERRED_PENDING_R1)**. It is not an
automatic repair after this failure and gains no priority from its existing
number. B4.51 remains `FAIL_PROCESS_SOURCE_FREEZE`; primary and independent
quotas are each consumed 1/1. Its 217/404 are post-stop TEXT results only; no
further call or reset is permitted. P/17, scientific FAIL, historical costs,
unknowns, memory gaps and every seal remain.

Next is **R1: v2 critical-path feasibility decision and delivery execution plan**,
authorized by an explicit instruction in a new window or a later "continue" after
this maintenance fully closes. **This maintenance neither starts nor completes
R1.** R1 is one bounded planning task, without a new one-shot TEXT scientific Gate
or a new contest of audit predicates.

R1 is limited to versioned documents, committed source as TEXT/AST, and compact
public closure metadata explicitly enumerated and hash-checked before reading.
Do not follow embedded pointers to old raw evidence, backup members, models,
labels or sealed contents. Do not execute old formal programs, actual FEM,
fitting, search, timing trials or memory trials. Complete required software
regressions still apply and cannot serve as formal experiment retries.

Within one planning slice, R1 must deliver the following without repeating this
long retrospective:

- In `TopoLab_v2_delivery_execution_plan.md`, provide one final acceptance–evidence–
  blocker matrix; compare at most three materially different routes and recommend
  exactly one, or explicitly conclude `NO_ADMISSIBLE_ROUTE`.
- For each route, state its mechanism, compatibility with current contracts,
  all-paid accounting, paper feasibility for optimistic cost and simultaneous
  memory, independent review needs, minimal next capability and exit conditions.
  Keep unknown fields UNKNOWN.
- Explicitly address the unreachable requirement caused by known-paid costs
  exceeding 7200. If new budget, access or a different experimental identity is
  needed, present a concrete scoped proposal, justify its upper limit and identify
  the required owner decision. Do not treat that proposal as authorization.
- List independently acceptable platform work separately, preserving both a
  demonstrable v1 and a v2 awaiting scientific acceptance.
- The next step can only be one capability implementation whose authorization and
  prerequisites are satisfied, or a concrete owner decision. With no feasible
  route, do not default to another text, public example or registration-guard
  slice.

At R1 closeout, update current status, one history entry and necessary indices,
then stop without executing its recommended successor. A subsequent actual
numerical route still needs a separate bounded contract, access roles, resource
limits, stop rules and source conditions first. This document grants no new paid
cap, historical retry/reset, real certification or final-evidence access.

## 6. Handoff prompt for a new window

Only the R1 work below is authorized when the owner sends this prompt in a new
window.

```text
Take over /Users/keith1117/Documents/TopoLab; GitHub: https://github.com/keith1117/TopoLab.
First check the actual branch, latest main/CI, open PRs, uncommitted contents and
merge state of this governance change. Preserve existing files.
Read root AGENTS.md and follow its required reading order, especially
docs/planning/TopoLab_v2_delivery_reassessment.md, the English v2 roadmap,
project_status.md and applicable contracts.

I accept v1 as a demonstrable interim delivery and retain the full-v2 flagship goal.
Execute only R1 as specified by current status: the v2 critical-path feasibility
decision and delivery execution plan. Do not repeat the retrospective. In one
bounded planning slice, provide an acceptance–evidence–blocker matrix, compare at
most three material routes, recommend one or conclude NO_ADMISSIBLE_ROUTE, and
write docs/planning/TopoLab_v2_delivery_execution_plan.md.
First address the unreachable all-paid requirement with known-paid costs above
7200. Distinguish concrete proposals from granted authority.
Defer the former B4.52; do not automatically add text review, public toys or guards.

This grants no new budget, formal retry/reset, actual FEM, fitting, search, memory
trial or sealed access. Preserve fixed P/17, every failure/cost/UNKNOWN, B4.51 FAIL
and consumed quotas; do not lower old Gates.
Follow the reassessment's finite read scope and progress rules. Routine authorized
operations need no repeated confirmation. For genuinely missing budget, access or
scope authority, prepare a concrete reviewable proposal before requesting the
required decision.
Follow repository_policy.md: stage reviewed paths individually, run every required
check, inspect every uploaded commit and run merge publication guards. Require
latest-PR-head CI and post-merge main CI; update status, history and indices and
clean up this task's merged branch.
At R1 closeout, report evidence, decisions, limits and the single next step, then
stop without executing its successor.
```

## 7. Validation and evidence boundary for this documentation maintenance

The original reassessment maintenance changed only ten retrospective, current-rule,
roadmap and entry documents. Numerical source, tests, fixtures, dependencies, CI,
original protocols/contracts/validation reports, the original development-history
prefix and the public README were preserved. It established no new scientific
pass. Before commit, run all five AGENTS checks, inspect each staged path, and
retain the existing publication guard checks for paths, immutable evidence,
links, sensitive information, every uploaded commit and actual merge differences.
Technical publication closes only after required CI passes on both the latest
PR head and merged main.

Raw software logs, failures, review lists, CI/PR/commit and backup receipts for the
original maintenance remain external at
`/Users/keith1117/Documents/TopoLab-data/v2-delivery-reassessment-2026-10-15`.
Its final `final_release_closure.json` binds the actual release identity and must
not be presumed complete beforehand. Software resource records remain separate
from the scientific ledger; unmeasured whole-software cost/peak stays
UNKNOWN_NOT_ZERO.

This bilingual maintenance changes language, reciprocal links and reading entry
points only. It does not change reassessment conclusions, work rules, R1 scheduling
or experimental authority. Its checks and publication receipts are recorded
separately at
`/Users/keith1117/Documents/TopoLab-data/v2-delivery-reassessment-bilingual-2026-10-15`.
