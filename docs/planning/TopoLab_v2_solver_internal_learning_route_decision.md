# Solver-internal learned-update route — bounded inception decision

Date: 2026-10-15 (America/New_York). Baseline: merged main
`06d0b77b8702c386d6b426278511425bdcd941c9`, [PR194](https://github.com/keith1117/TopoLab/pull/194),
with successful [main CI](https://github.com/keith1117/TopoLab/actions/runs/38811295699).
Chinese decision: [roadmap Section 6](TopoLab_v2_开发路线图.md#6-推荐执行顺序).

**Decision: REJECTED_CURRENT_RESOURCE_ADMISSION.** Eliminate the one candidate
defined below from the current implementation queue. It has a distinct saving
mechanism, but lacks defensible independent simultaneous-memory admission for
its indispensable exact solver and audit path. Complete cost and scientific
performance remain UNKNOWN_NOT_TESTED. This is a resource-admission rejection,
not a measured scientific failure or a theorem excluding all learned updates.
No actionable execution contract is issued. Full v2 remains OPEN; uniform is
default and the owner-closed exact-physics rescue program stays closed.

## 1. Authority and finite evidence boundary

The owner explicitly approved one inception slice under
[closure handoff Section 4](TopoLab_v2_rescue_program_closure_handoff.md#4-unique-next-item--concrete-owner-decision-not-authorized--not-started):

> 批准按关闭交接第4节开展一次有限的替代学习路线立项，仅评估“求解器内学习更新”这一假设。保留4GiB、独立预检和完整v2目标；交付可实施合同提案或明确淘汰结论后停止，不授权新预算、真实输入或实验执行，不自动启动后继。

This later grant resolves only the handoff's pending planning authority. The
handoff and its validation report retain their original bytes and historical
NOT AUTHORIZED wording. It grants no implementation, numerical campaign, new
scientific ceiling, real-input role, old retry/reset or sealed access.

One candidate only: **online sensitivity learning inside the existing OC/FEM
optimization sequence**, with occasional predicted-sensitivity OC updates and
mandatory real-state refresh and exact terminal refinement. Assessment identity
`topolab.v2.solver-internal-sensitivity-update.v1` names this rejected design;
it is not a frozen executable experiment or an allocated role. No second model,
coarse solver, learned preconditioner, new warm start or alternate route is
selected. R1's retrospective and three-route comparison are not repeated.

Reads use versioned documents, committed TopoLab source as TEXT/AST and public
primary literature. Old external evidence/compact-metadata allowlist and actual
read set are **empty**. No embedded raw-evidence, backup, model, label, index,
reserved or sealed pointer is followed. Ordinary complete software regression
and publication checks have a separate software namespace. No research program,
toy/guard implementation, prediction, FEM, fit, timing or memory trial occurs.

## 2. Mechanism, primary support and own-code boundary

Chi, Zhang, Tang, Mirabella, Dalloro, Song and Paulino,
[*Universal machine learning for topology optimization*](https://doi.org/10.1016/j.cma.2019.112739),
*Computer Methods in Applied Mechanics and Engineering* 375 (2021), 112739,
provides the primary mechanism context. Its Sections4.1–4.3 describe learning
sensitivities from optimization history, periodic physical refresh, and a
two-scale local formulation supplying coarse-state information. The author-hosted
[full text](https://paulino.scholar.princeton.edu/document/1161) was read at those
sections. It supports the idea of replacing some internal state solves; it does
not certify TopoLab's quality, resource bounds or speed. Bibliographic year2021
is verified on the [author's publication page](https://paulino.scholar.princeton.edu/publications/universal-machine-learning-topology-optimization);
the DOI's2019 component is not a conflicting publication year.

The considered TopoLab design would collect a bounded window of its own exact
per-query states, learn a small local mapping to **design-coordinate negative
compliance sensitivities**, and pass a predicted gradient to the existing
move-limited filtered-volume OC equation on selected internal steps. Genuine
fine-mesh solves refresh that window; model state is reset between physical
queries. Online training, storage and refresh are charged to each query. A
bounded local regressor is considered to avoid assuming a global dense network
or importing the old CNN/autograd training chain. Architecture, feature map,
window, update schedule, precision and training-step count remain
UNKNOWN_UNREGISTERED; there is no parameter search or implementation here.

This differs from a terminal-design warm start: the learned quantity changes
repeated internal updates, and any saving must come from **fewer real FEM solves**.
It also differs from D1: there is no gradient through current-prediction FEM to
train the old CNN. Avoiding Conv3d/autograd does not remove mandatory FEM, native
factorization or full runtime/lifetime accounting. The paper's coarse analysis
is not silently adopted or treated as free information; adding it would be an
additional numerical intervention outside this candidate.

Only independently authored TopoLab equations/source could be used for any later
implementation. No paper implementation, architecture, dataset, weights, figure,
performance measurement or unlicensed Hack3D content is imported. This review
introduces no numerical source. See [provenance](../../PROVENANCE.md).

## 3. Contract compatibility and independent numerical acceptance

The committed [SIMP loop](../../src/topolab/simp.py) computes an initial analysis,
then a fresh `evaluate_compliance` after **every** OC update. Each history row's
densities, volume, compliance and convergence describe that same analyzed state.
The [sparse FEM](../../src/topolab/fem.py) reduces to CSC, calls `splu`, inspects
U pivots and solves. There is no existing learned-gradient insertion hook or
permission to skip those analyses under the frozen solver identity.

A sensitivity-predicted step without a real re-solve cannot carry a genuine
compliance history row. Its small density change cannot certify convergence;
neither can a predicted plateau. If every such step instead receives the existing
fresh FEM, the intended solve-skipping saving disappears and learning adds work.
Consequently a useful implementation needs a **new, separately authorized solver/
experiment identity**, explicit candidate-phase state semantics and compatible
new reference/result identities. It cannot be inserted into the old B3/B4 runner
while claiming unchanged solver semantics. Old labels/results are not relabeled.

Any future within-query online adaptation would need to be part of the frozen
operational method and its query charge, with no cross-query model persistence
or training from reference/terminal-quality labels. It does not turn a final
cohort into offline training or permit final access during development. The
current grant supplies none of those future operational permissions.

A finite functional path can be described: exact-state collection → bounded
online learning → learned-gradient OC step → paid true re-solve/refresh →
unchanged exact-OC terminal refinement. It would have to work at both12×6×3 and
24×12×6 scales. Predicted steps count toward the total360 design-update cap;
entering exact refinement cannot reset or extend it. Only genuine exact-OC
states can populate the terminal convergence window; candidate-phase predictions
cannot fill its ten changes/eleven compliances. A design-change stop must also
come from a genuine exact-OC update, not a learned no-op. No uniform reference
or final-quality value may be fed back to choose an internal update or stop.

The minimum useful actual capability would be that composed two-scale query,
with recorded real/predicted update counts and fully paid controls, followed by
candidate-free reconstruction of terminal filtering, volume, exact compliance
and convergence. Merely fitting a sensitivity regressor, passing public examples
or writing a guard would not qualify. This capability is **eliminated from the
queue**, not scheduled subject to another text or toy prerequisite.

Independent review would need its own assembly/energy/gradient reconstruction
and terminal classifier, not the candidate's predictor or acceptance/cost helpers.
Refresh errors and accumulated drift must be measured, not excused by regression
loss. Preserve exact-physics FD/consistency tolerances where applicable; no new
surrogate-error tolerance is invented here. Final operational acceptance keeps
convergence within360, exact compliance agreement rtol1e-9, compliance ratio
<=1.001 and volume error<=0.005. No failed attempt is rescued by successful
fallback. Keep fixed P/17 and all historical controls/failures; a new policy
cannot replace it retrospectively or select a favorable seed.

The [full-v2 minimum](TopoLab_v2_development_roadmap.md#2-flagship-delivery-condition-and-priorities)
and [B3 final requirements](../b3_experiment_contract.md#7-final-order-statistics-and-delivery-decision)
remain: all fresh, physically disjoint evidence, both mesh scales, zero primary
ID attempt failures/fallbacks, point mean and charged-sum ratios<=0.90,
upper95% mean-ratio limit<1, direction means<=1, paired non-ML differences
upper limit<0, paid OOD safe rejection/zero accepted failures/upper limit<=1.05,
and independent Linux replication. Full new B4 and compatible final contract
must precede B5; no currently sealed cohort becomes available.

## 4. Optimistic complete-cost assessment

Retained diagnostic known-paid floor including D1's booked reserve is
**H >= K+60 =12781.16417100014444982 s**, where K=12721.16417100014444982>7200.
The unchanged old all-paid condition therefore remains permanently FAIL even
with zero future work. K is not the complete project ledger. Old failed work,
BOTH FULL180, Q31 once, other history and unmeasured software/CI costs remain.
D1's unused600 caps and eight-label scope are closed, not resources for this
candidate. No new scientific reserve or incremental ceiling is allocated.

For a new physical query let E be the complete initial/refresh exact-analysis
cost, L all online learning, P all prediction/OC/projection work, R exact terminal
refinement and independent quality decision, J recording/controller/I/O and
F all rejection or fresh fallback costs. Its full charged time would be:

```text
T_query = E + L + P + R + J + F
T_program = H + sum(all attempted references, controls and candidate queries)
            + all independent audits, launch/exit, failures, FULL reserves
            + new offline preparation, loading and publication costs
```

Use disjoint inclusive envelopes: do not add a complete query again on top of
its phases. Every first/failed call, data/hash/encode/copy, model state/gradient,
refresh, projection/filter, terminal check, durable recording, process/controller
and observed-exit cost is paid. No per-query learning is hidden as amortized
offline training. The old fixed508-case/200-epoch program remains unchanged and
closed; choosing online learning would require a new program, not setting its
old epoch cost to zero or declaring its7200 Gate passed.

An optimistic diagnostic scenario sets L,P,J,F to zero while still paying all
mandatory exact collection/refresh, terminal refinement and independent checks.
Even that scenario has UNKNOWN solve counts/maxima and UNKNOWN refinement after
predicted updates; it supplies no numerical speed or affordable-ceiling estimate.
For any real implementation, removed exact work must exceed *all* new learning,
prediction, refresh, verification and failure overhead, plus the required10%
paired saving. A saved-solve count alone is not a time bound. An always-paid full
uniform solve plus positive learning work cannot accelerate a successful query.

All new complete costs, safe finite ceiling and break-even count are UNKNOWN,
not zero. No budget request is justified by borrowing D1's1260 or a published
speedup. A future owner-approved incremental ceiling would still retain H and
all additional UNKNOWN; it would not repair old all-paid feasibility.

## 5. Simultaneous-memory assessment — decisive admission failure

The limit remains **4294967296 bytes**, with an independent complete allocation/
lifetime upper bound **before real input**, followed by separate native evidence
through the observed exit of any later actual program. The
[D1 report](../validation/d1_physics_resource_feasibility.md) and current committed
FEM caller establish the unresolved interface; D1 is not reopened to prove it.

| Simultaneous category | Effect of this candidate | Paper admission |
|---|---|---|
| Controllers/children/runtime | Candidate, reference and independent audit chains still need interpreter, allocator and thread residency/lifetimes | UNKNOWN; complete envelope absent |
| Inputs/I/O/history | Per-query exact-state window can avoid resident old label populations; current case, encoded states, decode/copy and persistence still live | Shape/window/source ownership UNREGISTERED, not zero |
| Physics setup/arrays | Existing mesh/filter/load/free-space setup is still required for refresh, exact tail and audit; no reciprocal certificate is introduced | Complete simultaneous bound absent |
| Model/optimizer/gradients | A small local learner avoids assuming the old CNN's26433-parameter/autograd chain | Exact model and learning allocations UNKNOWN_UNREGISTERED |
| Activations/training state | No mandatory Conv3d, but the chosen learner's working/saved state still requires a bound | UNKNOWN; no invented zero graph/workspace term |
| Projection/filter buffers | Existing filtered-volume OC and exact terminal filtering remain | Explicit arrays alone are not a lifetime bound |
| Python/storage objects | Histories, case/array metadata, ownership, serialization and allocator overhead remain | UNKNOWN |
| Assembly/factorization/transients | Exact checks still call `splu`, including conversion, fill, native workspace, U inspection and solve while other state is live | **UNKNOWN; no independent closed bound** |

For scale only, a hypothetical float64 window W=12 of d=8 features plus one
target uses `8*W*N*(d+1)` packed payload bytes:186624 at N=216 and1492992 at
N=1728. These are integer paper examples, **not selected parameters or a peak
upper bound**. They exclude all other rows. Removing Conv3d does not bound the
mandatory native solver or the independent audit process. Neither the old
2287564048-byte prepared-array estimate, small learner payloads, historical
sequential RSS, a memory monitor nor a hypothetical backend change supplies it.

No mandatory native/runtime term is assigned a safety factor or inferred from
available headroom. No complete candidate-free simultaneous bound is available
from the admitted evidence. **Admission therefore fails now, before source
implementation, input registration or a resource trial.** This does not prove a
physical >4GiB peak. Building a different bounded FEM backend or reopening native
proof work would be additional work/another mechanism, not this slice's successor.

## 6. Decision and retained failure categories

| Question | Disposition |
|---|---|
| Is the mechanism distinct from terminal warm starts/D1? | Yes: learn internal sensitivities and try to replace actual state solves; no saving established |
| Is there a finite functional integration and independent acceptance path? | Described in Section3; not implemented or admitted |
| Is unchanged old solver/experiment reuse compatible? | No; skipped analyses need new semantics/identity and compatible reference/result contracts |
| Is complete cost admitted? | No; old7200 permanently FAIL, new maxima/ceiling UNKNOWN |
| Is independent simultaneous4GiB admission established? | **No; mandatory native/runtime/lifetime terms UNKNOWN** |
| Candidate result | **REJECTED_CURRENT_RESOURCE_ADMISSION**; remove from implementation queue and stop |
| Scientific quality/speed | UNKNOWN_NOT_TESTED for this candidate; historical scientific FAIL/P17 unchanged |
| New engineering/formal execution failure | None: no implementation or formal launch attempted; ordinary software preparation failures are recorded separately |

Full fit remains PENDING4GiB; old B4.24/28 gaps stay UNKNOWN. B4.51 remains
FAIL_PROCESS_SOURCE_FREEZE with consumed1/1 roles and post-stop217/404 only.
All69 old predicate failures, B4.19 UNKNOWN, old quotas/costs/fixed checkpoints,
real reciprocal UNFROZEN/UNKNOWN_STOP and final/conditional48/720/unused48 seals
remain. This decision creates no TEXT scientific Gate or independent audit PASS.

## 7. Publication and actual action boundary

Same assigned worktree `/Users/keith1117/.codex/worktrees/a99d/TopoLab`, branch
`docs/solver-internal-learning-decision`; initial main clean, CI passed and no
open PR/unfinished duplicate existed. No primary-checkout edit or extra worktree.
No old external evidence, input, label/model/index or backup member is read;
no new research call, fit, FEM, search, timing/memory trial or old formal retry.
The current decision records an admission elimination, not preregistered numerical
execution. Future paths/hashes/roles/caps remain UNASSIGNED_DENY/UNALLOCATED.

[Planning validation](../validation/solver_internal_learning_route_decision.md)
records the required complete software checks and publication boundary. Source,
tests, fixtures, tolerances, locks, CI, public README and frozen R1/D1/closure
records retain their bytes. New software/search/review/CI/backup records stay at
`/Users/keith1117/Documents/TopoLab-data/solver-internal-learning-route-2026-10-15`.
Whole software cost/peak is UNKNOWN_NOT_ZERO_ADDITIONAL. No scientific resource
admission follows from software test memory or CI.

## 8. Sole next owner item and stop

**No executable scientific successor.** This one inception authorization is
exhausted by the explicit elimination. No second inception, resource-proof,
public-toy, guard, implementation, experiment or platform slice follows.
No new budget/access/role decision is requested for this rejected candidate.

The concrete next owner route decision is whether to retain
**FULL_V2_OPEN_NO_ADMITTED_ROUTE with scientific work stopped** (recommended),
while keeping4GiB/independent preflight and the full-v2 goal. This is a program
direction decision, not permission to obey STOP or a request to relax those
requirements. Any choice to pursue further scientific work must instead name a
materially different mechanism and an already reviewable route to its complete
independent resource admission; a plain “continue” supplies neither that scope
nor budget, real inputs or execution authority. This document does not commission
that further work. A2.3/A2.4/A4 remain separately scoped backlog requiring their
own instruction, not the next default. Publish this decision, retain the worktree
and STOP.
