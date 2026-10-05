# B4.18 bounded offline FEM bottleneck and training-objective method review

Date: 2026-10-05 (America/New_York).

**Read-only method-review acceptance passed; the original cost and learned
repair Gates remain failed.** All eight cases, sixteen synthetic fixtures,
96 paired Torch observations, 96 instrumented phase intervals and sixteen
case/arm setups were retained. The separate scalar auditor passed
**1286 arithmetic/identity/boundary conditions**, including
all six fixed method dispositions. No FEM, benchmark, loss/gradient evaluation,
label/model/optimized-state artifact, fit, reference, continuation, screening
or final access occurred. Fixed P/17 remains unrepaired; uniform stays default.
Next slice: **B4.19 bounded train-only local compliance-surrogate feasibility probe**.

## Frozen source and complete access boundary

The [protocol](../planning/b4_18_fem_objective_method_review_protocol.md),
read-only reader, separate scalar auditor and native closer merged in
[PR #135](https://github.com/keith1117/TopoLab/pull/135) only after all applicable
exact-head CI passed. Tested head `c289e83a9ff80d11760046d467a650a935870509`; clean execution
revision `7dddb5905c591f1cfb0929fa781027070dbf91f3`; merged `2026-10-05T18:40:18Z`.
Tested and merged trees match. Production binds 141 source/protocol/
convention/runtime files. Plan identity: `topolab.b4_18.fem-objective-method-review.v1`;
plan SHA-256 `acf450dcbba707f5c7165665c00d467c7c99262d4fcd72c8e4e59c9fe48f704f`. Locked Python and one BLAS/OpenMP
thread were used. Generated results stay outside Git at
`/Users/keith1117/Documents/TopoLab-data/b4-18-fem-objective-method-review`.

Thirteen exact B4.17 metadata bindings, its complete probe hash, native
plan/probe/independent/closure/controller records and all recursive prior
B4.16/B4.15/B4.14/B4.13/B4.12/historical/recovery/B3 index guards passed
before and after every process. B4.17's 112.34-second charge, B4.16's 55.99
and B4.15's 84.33 remain unchanged. Only identity/setup/timing/phase/byte-count
scalars from the old synthetic-fixture probe entered analysis; no raw vector
or gradient is copied into the review. Existing 768 numerical conditions,
64 directional differences and 256 solves remain **prior B4.17 evidence**,
not new numerical checks. All 48 unused B4.10 cases and final evaluation
remain sealed. Historical outcomes, failures, costs and controls are unchanged.

## Complete retained paired and phase evidence

Every first observation and paired order remains in `review.json`. There is
no dropped warmup, retiming or measured full fit. Torch complete forward/
backward observations and instrumented NumPy phases are different populations;
phase durations are never subtracted from Torch measurements.

| Scale / arm / metric | Count | Minimum | Median | Mean | Maximum | Sum seconds |
|---|---:|---:|---:|---:|---:|---:|
| small / prepared / wall_seconds | 24 | 0.008036125 | 0.008152605 | 0.013694785 | 0.135041583 | 0.328674834 |
| small / prepared / cpu_seconds | 24 | 0.008036000 | 0.008151500 | 0.010477500 | 0.060199000 | 0.251460000 |
| small / original / wall_seconds | 24 | 0.008336166 | 0.008552083 | 0.008811991 | 0.011439917 | 0.211487788 |
| small / original / cpu_seconds | 24 | 0.008336000 | 0.008551500 | 0.008758542 | 0.011102000 | 0.210205000 |
| large / prepared / wall_seconds | 24 | 0.159707417 | 0.165713604 | 0.167016193 | 0.181372708 | 4.008388624 |
| large / prepared / cpu_seconds | 24 | 0.159708000 | 0.164695500 | 0.166013083 | 0.179925000 | 3.984314000 |
| large / original / wall_seconds | 24 | 0.161865542 | 0.168278833 | 0.177483915 | 0.337907208 | 4.259613961 |
| large / original / cpu_seconds | 24 | 0.161866000 | 0.167565000 | 0.172757458 | 0.247494000 | 4.146179000 |

| Phase (eight states per scale) | Small wall | Small CPU | Large wall | Large CPU |
|---|---:|---:|---:|---:|
| projection_filter | 0.001139043 | 0.001140000 | 0.003450125 | 0.003452000 |
| assembly | 0.017432957 | 0.017395000 | 0.152899875 | 0.152726000 |
| reduction | 0.002364708 | 0.002366000 | 0.019097708 | 0.019084000 |
| factorization | 0.039900167 | 0.039894000 | 1.092382582 | 1.088342000 |
| solve_energy | 0.002926584 | 0.002925000 | 0.031530543 | 0.031512000 |
| pullback | 0.000345374 | 0.000348000 | 0.001176084 | 0.001175000 |
| Complete outer | 0.065683248 | 0.065621000 | 1.325896999 | 1.318909000 |
| Retained residual | 0.001574415 | 0.001553000 | 0.025360082 | 0.022618000 |
| Factorization/pivot share | 0.607463363 | 0.607945627 | 0.823881933 | 0.825183542 |

Large factorization/pivot wall share is
**82.3882%** of complete instrumented outer wall.
This is attribution for eight sampled states, not an achievable saving or
causal Torch overhead estimate. Changing-density matrices still require fresh
numeric factors in the exact method; immutable setup reuse cannot remove them.

## Original proxy and diagnostic sample arithmetic

Keep three seeds, 200 full epochs, 432 small/76 large cases, factor 1.25,
all twelve B4.1 fits (3,870.204341 seconds), prior 84.33/55.99/112.34 charges
and full-population setup extrapolation (42.876371394 seconds).
B4.18's new cost is additional to any future full ledger and is not substituted
into an old proxy. Shared data, prior development and future fit/screen/final/
replication costs remain required.

| Scenario | Small unit | Large unit | Small physics | Large physics | Total prospective seconds |
|---|---:|---:|---:|---:|---:|
| prepared_maximum | 0.135041583 | 0.181372708 | 43753.472885583 | 10338.244359358 | 58257.457957335 |
| prepared_minimum | 0.008036125 | 0.159707417 | 2603.704495355 | 9103.322769748 | 15872.767977497 |
| zero_factorization_instrumented | 0.003956625 | 0.034009668 | 1281.946501695 | 1938.551071915 | 7386.238286003 |
| zero_small | 0.000000000 | 0.159707417 | 0.000000000 | 9103.322769748 | 13269.063482142 |

The unchanged prepared maximum proxy remains **58257.457957 seconds versus
7,200**, and B4.15's original 60,339.39413004646-second proxy remains failed.
Even zero small plus minimum observed prepared large gives
**13269.063482 seconds**. Fixing only the small startup observation
cannot establish cost feasibility from these samples.

The zero-factorization scenario uses each instrumented NumPy state's own
outer minus its factor interval, then the per-scale maximum. It retains every
other phase and residual plus the same fixed costs. It is diagnostic sample
arithmetic, not a Torch correction, optimized-method lower bound, revised Gate
or permission to reuse stale factors. Observed minima and ideal phase deletion
do not bound a future solver's speed. Even the instrumented zero-factorization
scenario totals 7,386.238286 seconds, above 7,200; this remains hypothetical
sample arithmetic rather than a performance impossibility proof.

| Conditional requirement under unchanged prepared fixed costs | Value |
|---|---:|
| Available additional physics budget, seconds | 3034.259287606 |
| Population-weighted unit target, seconds | 0.007963935 |
| Small-only ceiling with large free, seconds | 0.009364998 |
| Large-only ceiling with small free, seconds | 0.053232619 |
| Common speed factor required from original physics proxy | 17.826992 |

The isolated ceilings cannot both be spent simultaneously. Static retained
array extrapolation stays **2287564048 bytes**; the difference to 4 GiB is
2007403248 bytes, excluding Python/SciPy objects, transient factors,
network/optimizer and activations. Sequential RSS and this arithmetic do not
certify full training memory feasibility; that remains pending.

## Six frozen method dispositions and prospective hypothesis

| Method | Decision |
|---|---|
| Immutable setup reuse | B4.17 stops after its failed cost Gate; no new cache search. |
| Startup-only repair | Descriptions cannot replace the Gate; large sampled cost persists with small physics free. |
| Stale numeric factors | Incompatible with changing-density stiffness and exact compliance/adjoint. |
| New ordering or iterative solve | Deferred; requires a separate numerical/residual/gradient/resource contract. No benchmark here. |
| Fixed terminal spatially weighted MSE | Preserve B4.5's bounded pass and B4.6's failed reliability confirmation. |
| Local signed compliance tangent | One separately registered train-only fidelity/gradient/cost probe before any fit. |

The last hypothesis is independently derived from the existing SIMP/filter
adjoint. At an audited training design x*, use its **signed, un-clipped**
normalized derivative g*: `C_hat(x)/C* = 1 + g*.T (x-x*)`, evaluated at
x=P(z), with gradient `J_P(z).T g*`. Offline preparation would pay train-state
FEM; the local term itself would not require a new exact FEM solve at every
prediction. B4.5's clipped positive sensitivity-weighted squared density error
is a different objective and cannot supply the signed exact derivative.

This is not an implemented loss or global compliance bound. Prediction errors,
active-set changes and low-density stiffness can invalidate fidelity; model
optimization can exploit approximation error. B4.19 must prospectively freeze
one surrogate, finite train-only states/perturbations, error/gradient tests,
complete setup/forward-backward/resource costs and a stop before fitting.
No loss coefficient, trust radius, schedule, population/epoch/frequency search
or model quality is selected here. A passing local probe still needs a separate
versioned fit/repair and independent confirmation before final access.

## Native resource closure and software verification

Review/audit each cap at 60 charged seconds; whole cap 240 seconds / 1 GiB.
The full 60-second plan/closure/controller reservation is paid. All successful
review/audit/closure/controller processes exited zero. The first static
metadata-plan invocation retained 2.76 seconds of wall, user/system CPU and
its full stdout, but the sandbox blocked the native timer
(`sysctl kern.clockrate`); RSS was unavailable and the outer command exited
one. Its original command, relocated partial profile and log remain retained.
It accessed no evidence bytes. The same static plan then ran under native
profiling permissions; no review, numerical work or result was rerun. The
failed plan pays 2.76+10=12.76 seconds inside the full sixty-second reservation.
All successful native wall/CPU/RSS records are complete. The failed plan
attempt's memory cap cannot be independently certified because its RSS was
not captured; the reported peak is the retained observed maximum, not an
imputed failed-attempt peak. No closed ledger was rewritten.

| Process | Native wall | User CPU | System CPU | Peak RSS bytes | Closed charge |
|---|---:|---:|---:|---:|---:|
| plan | 2.41 | 1.72 | 0.22 | 278331392 | within full 60-second reserve |
| review | 3.05 | 2.7 | 0.25 | 301252608 | 13.050000000 |
| independent | 3.08 | 2.73 | 0.25 | 300105728 | 13.080000000 |
| closure | 3.49 | 2.8 | 0.32 | 279756800 | within full 60-second reserve |
| verification | 0.03 | 0.02 | 0.0 | 21217280 | within full 60-second reserve |

Complete new charge is **86.13 seconds** and retained peak RSS
**301252608 bytes**. Combined reservation use is
48.69 <=60 seconds; all available native peaks fit the retained peak.
The retained metadata-plan failure and all successful plan/closure/controller
commands fit the paid reservation. The stdlib post-exit checker binds the
complete independent audit and original
metadata/source hashes without numerical work or importing the candidate loss.

Before source commit, locked dev sync, Ruff, mypy (66 files), all **942 tests
in 485.92 seconds**, and working/staged whitespace checks passed.
The 36 new tests cover complete/ordered scalar populations, first observations,
phase residuals, independent report mutations, ordered decisions, no-read
planning, exclusive publication, metadata-first rejection and failed-cost/cap
accounting. Initial development formatting/cache failures occurred before
production access and did not change a numerical tolerance or Gate.
Evidence publication repeats all required checks and waits for its exact-head
CI before merge; numerical sources, conventions and production receipts stay
unchanged. No external source or upstream content was used.
Before evidence commit, locked dev sync, Ruff, mypy (66 files), all **942
tests in 472.27 seconds**, and working/staged whitespace checks passed again.

| External receipt | SHA-256 |
|---|---|
| `audit_receipts/plan.json` | `f45b7a00add45c49b99dabbf5d6aba06f88fce797e58fe0e290f588c992b6eca` |
| `audit_receipts/production_release.json` | `eb09a3b1e7a03babc141718743a4714caa98927d12c9e25d79d688a85fc29bdf` |
| `audit_receipts/source_final_head_ci.json` | `8964ec0c46504d02311e907dff27a7bf0a38dc750381335d6f66c979dfa6da87` |
| `review.json` | `7670ef8f70c230133d27fdc6966e25aa86723aa12e616b3a5ce8eb600ab0f093` |
| `independent_audit.json` | `435fdcbe5a3d5ae7b88fd8bf1f1ae92f9a4d879743ea2ef5249540aa7a2f4e7d` |
| `resource_close.json` | `5b0bc27f242981fdd147c928b0832a0968b3e196c58d47ec3db1064079ed81ca` |
| `audit_receipts/execution_commands.json` | `5c4b46ce97b727364396283f18c329c3b2f40df5e454891e2374dc9ddd09b918` |
| `audit_receipts/plan_command.json` | `ddfd9387794d1fc79b4361ab09091210fb1dff1855f19a52e80fb3147fe142bb` |
| `audit_receipts/closure_command.json` | `8d53822742ec1c0284c8fd2e0d26cb001e5c71fc42d2f465e4dc00d07ea530c2` |
| `audit_receipts/closure_profile_verification.json` | `863baa2e59a80456aff836d629c407cd8e040982760af3db2ba9a30e2c4cebff` |
| `audit_receipts/postexit_command.json` | `feb29c764cb5768580f8e22428d4915c9b40a54fab8b044c6051440546431f3f` |
| `audit_receipts/postexit_controller_reservation.json` | `5c82a1a261138c4a6958646cc8cb6cae72cc466e29908757b7d11a126bb7a2b2` |
| `audit_receipts/plan_sandbox_denied_original_command.json` | `610757ccb4450b5d54b6783763165aad49a328ee00182f1fd9cdb5e35a80c73d` |
| `audit_receipts/plan_sandbox_denied.json` | `4fbb2352fa7e2339c96f813cc01a3b6a550569963d6f4c29917a4c792a83d9c5` |
| `profiles/plan_sandbox_denied.time` | `cc90577949e766553c99e40e5e357edef5d70f6f6dabff0d95d03024e0862683` |
| `logs/plan_sandbox_denied.log` | `f45b7a00add45c49b99dabbf5d6aba06f88fce797e58fe0e290f588c992b6eca` |

The frozen ordered decision recommends **B4.19 bounded train-only local compliance-surrogate feasibility probe**.
It has not started. No fit, alternative ordering/cache candidate, seed change,
continuation, epoch/population/physics-frequency search or final access follows
automatically. P/17 remains unrepaired. A passing repair, independent confirmation
and compatible final contract remain required before B5 and any acceleration
claim. All original failures/charges and the final/unused B4.10 seals remain.
