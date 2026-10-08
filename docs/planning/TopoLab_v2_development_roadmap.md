# TopoLab v2 Development Roadmap

Status: **active v2 flagship delivery plan; the ML delivery Gate remains open.**
Gates A1/A3 and B3's data Gate passed; A2.1–A2.2 are complete. The original
B4.2 Gate and subsequent fixed-primary confirmations remain failed. Uniform
initialization is the operational default and final evaluation stays sealed.

Latest completed numerical/audit slice: **B4.30 fixed-P/17 reflection repair**,
scientific **FAIL**, complete v2 numerical/native resource **PASS**. All18/270
and prescribed audits complete; fixed R17 still fails case55c1b3e… at
1.00197094375>1.001 and target mean1.01605313078>1.0. Cumulative7323.1004352501081506
includes the original failed191.9666532080154866 and both FULL180 reserves.
See [report](../validation/b4_30_paid_continuation.md). Conditional48/720 remains
unopened. Original failed preflight, all historical evidence/unknowns and
full-training memory PENDING/4GiB remain; uniform stays default.

Latest completed read-only slice **B4.32 method review/preregistration**:
69 static/32 independent Decimal document checks PASS, with zero production
or candidate numerical evaluations. See [report](../validation/b4_32_generalist_method_preregistration.md).
Six dispositions preserve all earlier stops; one prospective fixed-anchor
reciprocal-energy hypothesis requires exact equilibrium, while real floating
admissibility/residual certificates, fidelity/cost/memory/reliability are UNKNOWN.
Known disjoint paid-stage subtotal12721.16417100014444982>7200 grants no cap
reset or fit. B4.31 Q31/original7323.1004352501081506/combined7403.39983000014444982
and its source-premerge process failure remain. Old3/3 and B4.30's2/1 stand.
Next proposed B4.33 reciprocal-energy algebra/access implementation is software
only on8 public toy fixtures, separately authorized/frozen and not started.
Uniform/P17, all failures/costs/unknowns/final/fresh/unused seals and no B5 remain.
[Project status](../project_status.md) holds the current boundary;
[history](../development_history.md) preserves the chronology.

Prepared: 2026-09-24
Revised: 2026-10-08 (B4.32 finite method preregistration; scientific FAIL remains)

Related documents:

- [Overall plans and frozen slice protocols](./README.md)
- [Validation evidence index](../validation/README.md)
- [Current status and stopping boundary](../project_status.md)
- [Retained development history](../development_history.md)
- [Formal B3 experiment contract](../b3_experiment_contract.md)
- [Repository and publication policy](../repository_policy.md)

## 1. Current baseline

`v1.0.0` established:

- Passed N1, N2, P1, and M0 gates;
- Independently implemented and validated structured Hex8 FEM and 3D SIMP;
- Sparse assembly/solving and a four-scale single-machine benchmark;
- FastAPI, asynchronous in-process runs, cancellation, SQLite persistence, and restart recovery;
- React problem configuration, run history, convergence charts, and 3D physical-density visualization;
- Traceable data generation, training, evaluation, checkpoint, and recovery workflows;
- Preserved negative/inconclusive M1 results and the failed M2 data gate; and
- Locked dependencies, CI, 262 Python tests, 22 frontend tests, and an installable wheel at release time.

Remaining gaps fall into two groups:

1. **Outside ML:** No one-command demonstration, containers, hosted demo, process isolation, true optimizer checkpoint/resume, multi-machine performance evidence, or real-user feedback at v1.0.0.
2. **ML:** M1 did not establish stable acceleration; ten non-convergent M2 labels prevented fitting. Data coverage, cross-direction generalization, solution-quality reliability, and attainable speedup remain insufficiently understood.

Future work must not rewrite or erase historical `v1.0.0`, M1, or M2 conclusions. New experiments, numerical conventions, and platform contracts need fresh version identities and separate validation reports.

## 2. Flagship delivery condition and priorities

**The full v2 flagship project is not delivered until a learned method achieves
reproducible, same-quality, end-to-end acceleration on a workload defined before
final evidence is opened.** A completed platform and an honest negative ML result
remain valuable engineering outputs, but they do not satisfy this project's
requested final delivery condition. Do not rename or describe the whole project as
fully delivered while this ML gate is open. The historical `v1.0.0` release is not
retroactively withdrawn or relabeled.

The minimum ML delivery gate requires a fresh, physically disjoint final cohort;
an optimized, version-matched uniform reference and fixed non-ML baselines; all
inference, projection, decision, refinement, rejection, and fallback costs in the
paired end-to-end comparison; the frozen compliance, convergence, and volume
quality checks; zero accepted learned quality failures; and an upper 95% confidence
limit below `1.0` for the predeclared primary mean time ratio **at each of at
least two predeclared 3D mesh scales**. The predeclared OOD cohort must have zero
accepted quality failures and an upper 95% time-ratio limit `<= 1.05`; safe
rejection is allowed but its full cost is charged. Before any final evaluation,
the new experiment contract must additionally fix its meaningful repeated-query
workload, mesh/volume/load strata, hardware, seeds, minimum effect worth
claiming, independent replication, and OOD definition. Report generation,
training, and checkpoint-loading cost separately and provide an amortization
analysis. A favorable subgroup found after evaluation cannot replace the declared
primary cohort. `Accelerated` wording remains restricted to the exact workload and
environment that pass; broader stability claims require their own evidence.

Track A continues to improve the platform. Track B is now a **success-directed ML
engineering program** with a finite budget and an explicit decision at each
versioned experiment gate. A failed gate triggers diagnosis and a new independently
registered intervention; it does not count as project completion or permit an
unregistered search on an exposed final set. Time and compute estimates beyond the
next diagnostic gate remain provisional: an empirical positive result cannot be
guaranteed by scheduling more epochs.

| Priority | Stage | Reason |
|---|---|---|
| P0 | B0 measured warm-start feasibility | Establish actual solver headroom on development cases |
| P0 | B1 convergence and learned-failure diagnosis | Fix numerical failures and identify the quality bottleneck before expanding training |
| P0 | A3 baseline-affecting solver performance | Freeze a fair optimized uniform denominator before workload selection |
| P0 | B2 workload and scale pilot | Select a real repeated-query task with room for fair end-to-end gain |
| P0 | B3 new versioned experiment contract | Freeze data, model/loss, compute, reliability, and final evidence before fitting |
| P1 | A2 process isolation and recovery | Keep the platform safe for longer runs |
| P1 | B4 data, fitting, and validation | Improve and screen the learned method without final-data feedback |
| P1 | B5 one-time final evaluation and replication | Decide the ML delivery gate on new evidence |
| P2 | A4 deployment and feedback | Follow isolation and resource limits |

Each slice remains independently reviewable. Numerical-semantic changes, platform
work, data materialization, and model training stay in separate PRs. Report actual
time, memory, and data-generation cost at every gate; do not turn old estimates
into a promise of a positive result.

## 3. Track A: Work outside ML

### A1: Reproducible demo and presentation

Enable a reviewer with no project background to run a small end-to-end optimization in a clean environment and quickly understand architecture, results, and limits.

Recommended slices:

1. **A1.1 canonical demo case**
   - Add a small, versioned, public example that completes quickly.
   - Offer one command to start the API and run it, or an equivalent narrow CLI.
   - Print run ID, terminal state, compliance, volume, and result location.
   - Test exact compatibility with the public `TopologyProblem` contract.
2. **A1.2 local stack packaging**
   - Provide a minimal Docker/Compose local path for API and frontend.
   - Use non-root processes, locked dependencies, and a persistent volume.
   - Keep the database, results, and model artifacts out of images.
3. **A1.3 architecture and demo evidence**
   - Add an original architecture diagram and a 2–4 minute demo video.
   - Show submission, progress, cancellation, recovery, convergence, and 3D results.
   - Keep README numbers traceable to validation reports.
4. **A1.4 clean-machine smoke**
   - On clean Linux, install, start, submit, complete, restart/read, and build the frontend.
   - Record commands, runtime, environment, and limits in a validation report.

**Gate A1:** One documented path starts the complete local stack on clean Linux; the canonical case reaches a valid terminal result within a stated time; smoke covers API, SQLite, and frontend contracts; generated outputs remain outside Git; and the demo does not imply hosted, production-ready, scalable, or accelerated operation.

Suggested milestone: `v1.1.0`.

### A2: Process isolation, durable jobs, and numerical recovery

Upgrade the current thread pool and “interruption means failure” semantics to a verified process boundary. Distinguish recovery of a job record from optimizer checkpoint/resume.

1. **A2.1 worker protocol:** Freeze a minimal serialized manager/worker protocol; begin with a local separate process rather than Redis, RQ, or Celery; keep the Numerical Core independent of Web and queue frameworks.
2. **A2.2 durable ownership and recovery:** Give queued/running runs a lease, heartbeat, or equivalent explicit owner; test API and worker crashes, duplicate claims, and indefinite running; add a proper migration mechanism rather than accumulating inline schema upgrades.
3. **A2.3 optimizer checkpoint contract:** Independently version density, iteration, history, problem identity, and solver contract; write atomically and reject mismatched code/problem/environment; compare resumed and uninterrupted runs within frozen tolerances.
4. **A2.4 cancellation and resource bounds:** Test cancellation while queued, running, solving, and after resume; bound concurrency, mesh, runtime, and artifact size; log structured metadata without entire density arrays or sensitive inputs.

**Gate A2:** Deterministic tests cover worker crash, API restart, duplicate claim, and cancellation; two concurrent runs isolate memory, results, errors, and checkpoints; resumed final compliance, volume, and density meet consistency checks; defaults do not permit unlimited concurrency or unbounded problems.

Suggested interim milestone: `v1.2.0`. Reserve the `v2.0.0` project milestone for the full flagship delivery gate; document API compatibility separately.

### A3: Performance engineering and wider evidence

Profile first, optimize one bounded bottleneck, and expand benchmark environments and scales.

1. Record assembly, factorization/solve, filter, OC, and serialization phases.
2. Select one dominant bottleneck, such as repeated sparse-structure construction or linear solving.
3. Test numerical equivalence and provide a fallback for the candidate optimization.
4. Repeat a fixed mesh ladder on Apple arm64 and Linux x86-64.
5. Report cold/repeated time, peak RSS, DOFs, nonzeros, and failure boundaries.

**Gate A3:** Compare before/after on the same problem, environment, thread count, and protocol; preserve frozen small-mesh tolerances; obtain a stable gain on the target metric without obvious regression at other scales. Use `faster` or `lower-memory` only within measured scope, and avoid a broad `scalable` claim without larger cross-platform evidence.

Complete any A3 change that affects the uniform solver's timing or numerical
behavior before B2's workload pilot and B3's ML contract. Later measurements
cannot silently change the final comparison denominator.

Suggested milestone: `v1.3.0`.

**A3 completed:** The [paired Apple arm64 and Linux x86-64 audit](../validation/a3_solver_ordering.md)
selected a larger-system SuperLU ordering with an explicit historical fallback.
The measured sparse-solve gate passed without changing the frozen small-mesh
solver path or the old M1/M2 outcomes. The subsequent B2 pilot used the
optimized ordering equally in every compared method.

### A4: Controlled deployment and external feedback

After A2 isolation and limits, offer a safe, low-cost public demonstration or a complete recording instead.

1. Threat-model CPU/memory exhaustion, oversized inputs, database growth, and abuse.
2. Expose only preset mesh ranges and a fixed concurrency budget.
3. Add health checks, structured logs, error-rate and run-time metrics.
4. Retain local Compose plus a recording if cost or safety prevents hosting.
5. Collect a little genuine trial feedback, separating defects from feature wishes.

**Gate A4:** Deployment cannot bypass Numerical Core input validation or limits; internal paths, device identifiers, databases, and external experiment artifacts are not exposed; shutdown, cleanup, and cost bounds are clear; README distinguishes local demo, hosted demo, and production service.

## 4. Track B: required learned acceleration

### Historical boundary and M3 v1 disposition

M1's six ID-test and 80 OOD cases are exposed; M2's complete 756-case outcome
index is development information. M1/M2 artifacts, negative conclusions, and
their original gates remain immutable. The bounded `topolab.m3.experiment.v1`
contract passed its *planning* gate but is **superseded before M3.1, fitting, or
final evaluation**. Its 425-label MSE control plus one dilated 11,281-parameter
CNN was a legitimate small experiment, but it did not repair the M2 convergence
issue or establish that prediction quality would reach the actual warm-start
headroom. No M3 v1 final label or learned outcome was opened. Its final case
definitions were published in the contract, so mark them **design-exposed** and
keep them out of the next final cohort. Do not quietly edit that historical
pre-registration or treat its planning gate as an acceleration gate. The next
experiment must use a new contract/catalog identity and ledger of all
development-exposed physical cases; all new final labels and outcomes remain
sealed until the new freeze.

### B0: Actual warm-start feasibility — complete development probe

The read-only probe in `docs/validation/ml_feasibility_probe.md` used only the 36
M2 validation labels as an impossible label-informed initialization, plus the seven
failed M2 training case definitions. All 36 oracle starts passed the frozen quality
checks after one SIMP iteration; the mean paired projected-start/uniform time ratio
was about `0.072` in two local runs. This shows that the frozen solver has
substantial *conditional* warm-start headroom when an essentially exact solution
is supplied. It does **not** show a learned or deployable speedup. All seven failed
training cases still missed the 120-iteration tolerance; their final ten density
changes and compliances decreased, which points to slow terminal progress on these
cases but does not identify a general solver fix.

### B1: Fix the numerical and learned-failure bottlenecks

1. Reproduce the seven development-only `y, 0.45` traces and analyze the ten
   exposed M2 terminal failures without using M2 test/OOD label values.
2. Distinguish finite-budget slow convergence, periodic behavior, and optimizer
   instability using density/compliance trajectories and independent volume checks.
3. If a solver change is justified, predefine its numerical acceptance tests,
   version the solver and labels, and rerun **every compared method** under the
   same revision. Do not silently raise the iteration budget or loosen tolerance.
4. On development-only cases, replay M1 predictions to compare raw and projected
   fields, initial compliance, final quality, and refinement trajectory against the
   known label oracle. Identify whether data coverage, representation, density MSE,
   or warm-start basin behavior dominates the gap.

**Gate B1:** A reproducible failure mechanism and a tested correction or explicit
unchanged-solver decision are recorded. The next model intervention targets a
measured bottleneck; simply doubling epochs is not a correction.

**B1 completed:** The [development-only diagnosis](../validation/b1_failure_diagnosis.md)
reproduced all ten frozen failures at 120 iterations; all converged at 127–195
iterations in a separate in-memory extension without changing the frozen outcomes.
The unchanged-solver decision is explicit. Across 36 M2 validation cases and five
fixed M1 seeds, 46/180 learned attempts failed quality, with a larger gap on the
unseen `z` direction and persistent failures on `y`. Projection and initial
compliance alone did not predict final quality. A3 then froze the larger-mesh
uniform solver ordering, and B2 tested the resulting denominator.

### B2: Choose a workload with measured attainable savings

After the baseline-affecting A3 work is frozen, pilot a small, fixed
development-only mesh ladder and representative repeated-query
load/support/volume families. Run optimized uniform, the frozen non-ML baselines,
label-informed oracle starts, and current learned starts on matched numerical
settings. Record per-iteration FEM, inference, projection, memory, and fallback
costs. Include difficult volume strata rather than choosing only favorable
low-volume cases. Select a meaningful workload and mesh range for the new claim
*before* any new final labels or outcomes exist.

**Gate B2:** A quality-feasible oracle and at least one attainable development
prototype have enough measured savings to justify training and final evaluation.
If exact-label warm starts cannot beat an optimized uniform reference on the
intended workload, pivot to a separately versioned learned optimizer-step or
numerical-cost intervention; more final-density MSE training is not warranted.

**B2 completed; gate failed:** The [fixed development-only pilot](../validation/b2_workload_pilot.md)
tested six cases at each of two mesh scales. All six small uniform references
passed, but three of six large references did not converge within the frozen
120-iteration limit. The impossible own-result oracle showed conditional
headroom on valid references; the five unchanged M1 seeds had mean
fallback-inclusive time ratios of 1.64 (small) and 1.77 (valid large cases).
Those historical results did not establish a quality-feasible two-scale
workload or a viable learned prototype. The fixed-support pilot cannot support
a claim about other support families.

**B2.1 numerical gate passed; learned-prototype gate still open:** The
[versioned physical-plateau intervention](../validation/b2_1_convergence.md)
retained the historical solver as the default and gave the new policy and
results separate identities. All six small and six large uniform references
passed the predeclared numerical acceptance checks within 120 updates; the
three formerly invalid large cases now have matched denominators. Under the
same new policy, the impossible oracle passed all cases with mean charged
ratios 0.074 and 0.109, while the unchanged five-seed M1 panel passed 20/30
and 16/30 candidate quality checks and averaged charged ratios 1.56 and 1.72.

**B2.2 data-feasibility gate failed:** The
[frozen prototype plan and sentinel](../validation/b2_2_data_feasibility.md)
fixed a same-architecture design-MSE control and sensitivity-weighted
candidate on new-policy `y/z` labels, with an explicit exposure and compute
boundary. Only 53/61 fixed uniform sentinel cases passed independent quality
checks. Seven historically failed small `y/0.45` training cases and one new
large `z/0.20` case remained non-convergent at 120 updates. No labels were
materialized and no model was fitted.

**B2.3 bounded sentinel gate passed:** The
[versioned 240-update budget repair](../validation/b2_3_data_feasibility.md)
retained the B2.1 stopping policy and all numerical tolerances, gave each
case/result a new identity, and passed **61/61** independent quality checks.
The former seven small failures stopped at update 125 and the new large
failure at 170. The 53 previously accepted cases retained exactly their old
stop iterations and final compliance. This is a sampled data-feasibility
result, not a complete 522-label gate.

**B2.4 complete development-data Gate passed:** The
[frozen 522-case materialization and audit](../validation/b2_4_development_labels.md)
produced **522/522** valid labels across both mesh scales and every
development stratum, with 0 failures. All artifact checksums, persisted
float32 states, sensitivity weights, and independent compliance checks passed.
Generation plus audit took 1,149.58 s and peaked at 402.5 MiB, within the
frozen two-hour and 1 GiB caps.

**B2.5 complete; learned-prototype Gate failed:** The
[fixed six-fit, 54-case development screen](../validation/b2_5_prototype.md)
retained all 486 method outcomes and charged every failed attempt plus a fresh
uniform fallback. The best learned seed, unweighted control 43, averaged 1.289
and 1.336 times its matched uniform reference on small and large meshes;
all six learned seeds exceeded 1.0 at both scales. There were zero accepted
quality failures, but 40 learned attempts failed and paid fallback. The
sensitivity-weighted candidate did not correct the convergence, compliance,
or refinement-time bottleneck.

**B2.6 complete; development feasibility Gate failed:** The
[frozen intermediate-trajectory target intervention](../validation/b2_6_trajectory.md)
captured 480/480 targets and completed three fits plus a new, disjoint 12-case
screen. All three new seeds were slower than matched uniform at both scales
after complete fallback charges. Seed 17, the least slow, averaged 1.486 on
small and 1.701 on large meshes; seeds 29 and 43 had more failures. The
impossible true-trajectory oracle averaged 0.490 and 0.748, demonstrating
conditional headroom without a deployable learned result. This motivated
B2.7's separately versioned representation repair. B3 final-cohort
registration remains
premature until a development prototype establishes meaningful same-quality
end-to-end savings.

**B2.7 complete; development feasibility Gate failed:** The
[frozen global-load representation intervention](../validation/b2_7_global_load.md)
reused all 480 audited B2.6 targets and completed three fits plus a fresh,
disjoint 12-case, 132-outcome screen. The new representation cut the old
trajectory models' charged ratios substantially, but no new seed met the
required two-scale and per-direction bounds. Seed 17 averaged 0.842 small and
1.049 large; seed 29 averaged 0.933 and 0.920. Both had `y`-direction means
above 1.0. This motivated B2.8's fixed y-load start intervention.
Keep B3 final-cohort registration sealed until a development prototype
passes.

**B2.8 complete; development feasibility Gate failed:** The
[fixed y-load midpoint intervention](../validation/b2_8_basin.md) reused
the three audited B2.7 models and screened 12 fresh development cases with
132 complete outcomes. The midpoint changed y trajectories but did not
reduce the three seeds' 2/3/4 failed-attempt counts. No seed met the frozen
two-scale and direction-wise charged-speed limits. The unchanged z predictions
were slow on several new load-position/volume cases, while the impossible
own-trajectory oracle retained conditional headroom. The next independent
slice was **B2.9**: a learning-side quality and load-position transfer
correction tested on fresh disjoint development cases with full charges.

**B2.9 complete; development feasibility Gate failed:** The
[vector point-load conditioning intervention](../validation/b2_9_vector_load.md)
reused the 480 audited B2.6 targets, completed three deterministic fits,
and retained all 132 outcomes on twelve fresh cases. Seeds 29 and 43 had
zero fallbacks and charged small/large mean ratios of 0.613/0.871 and
0.639/0.882. Both missed the frozen large-y direction bound: their means
were 1.032 and 1.080, above 1.0. Accepted large-y starts at volume
0.5625 still needed more solver updates than uniform. The next independent
slice was **B2.10**: freeze one quality/cost-aligned intervention addressing
that measured refinement burden and screen it on fresh disjoint cases.

**B2.10 complete; development feasibility Gate failed:** The
[sensitivity-weighted intermediate-trajectory objective](../validation/b2_10_weighted_trajectory.md)
generated all 480 audited weights and completed three fixed fits. Its fresh
screen retained 99 outcomes on nine cases, then the tenth mandatory uniform
reference failed to converge at the frozen 240-update limit. The screen did
not silently exclude the case or compute a partial Gate. Among the nine
completed cases, the new weighted seeds did not consistently improve over
the unchanged B2.9 vector controls. A separate 360-update diagnostic
converged at update 282 under a new case identity; it is not B2.10 evidence.
The next independent slice was **B2.11**: version a bounded reference-budget
repair, establish full reference feasibility, and compare the unchanged
models on a fresh disjoint development screen.

**B2.11 reference repair passed; learned-prototype Gate failed:** The
[versioned 360-update comparison](../validation/b2_11_reference_budget.md)
passed all twelve old/new uniform sentinel pairs and all twelve fresh
uniform references. The fresh references stopped by update 189, so their
denominators were not lengthened by the higher cap. All 132 fixed-method
outcomes were retained, but neither B2.9 nor B2.10's three-seed panel had
one seed meeting every scale/direction bound. At large `y/0.5975`, all six
learned starts converged to final compliance about 0.55%–0.63% worse than
uniform, failed the unchanged 0.1% quality allowance, and paid full
fallback. At small `z/0.2975`, all six accepted starts required more
updates than uniform. The next independent slice is **B2.12**: freeze one
learning-side correction for these measured quality-basin and refinement
gaps, then screen it on fresh disjoint development evidence. Do not enter
B3 before a development prototype passes.

**B2.12 reference and fit Gates passed; learned-prototype Gate failed:** The
[fixed spatial-context CNN](../validation/b2_12_context_cnn.md) reused all
480 audited trajectory targets and completed three fits on the unchanged
vector input and MSE objective. All twelve new uniform references passed
by update 133, and the fresh 12-case screen retained all 132 fully charged
outcomes. Validation MSE improved for all three seeds, and small-z
refinement improved at low volume. Yet all three new models failed the
large-scale mean bound: their charged ratios were 1.283–1.376. At large
`y/0.6025`, all three again missed the unchanged compliance quality bound
and paid full fallback; at large z volumes 0.3025 and 0.4525, their
refinement took many more updates than uniform. No seed passed the frozen
two-scale/direction-wise Gate. The next independent slice is **B2.13**:
freeze one deployable, fully charged routing/rejection policy using the
measured complementary scale/direction behavior, then test it on fresh
disjoint development cases. This is not a post hoc passing result; B3
remains closed until a new prototype and larger confirmation pass.

**B2.13 small development Gate passed; later confirmation failed:**
The [frozen metadata-only route](../validation/b2_13_routing.md) reused
audited B2.9/B2.12 checkpoints, passed 12/12 fresh uniform references,
and retained 144/144 fully charged outcomes. Its small/large mean paired
ratios were 0.635/0.723, with four direction means 0.555–0.826, one
predeclared uniform rejection, zero learned failures, and zero accepted
quality violations. The negative B2.12 screen remains immutable. On this
fresh cohort, however, the fixed context-43 model was faster than the
router on both scales and also met the descriptive direction bounds.

**B2.14 larger development confirmation failed:** The
[frozen protocol and audit](../validation/b2_14_development_confirmation.md)
passed 24/24 new uniform references and retained all 192 fully charged
outcomes on disjoint development cases. It found zero accepted quality
violations, but no routed or fixed single-model candidate met both
scale-mean and all direction-wise charged-speed limits. The B2.13 route
averaged 0.971 small and 0.925 large, with a 1.112 small-y mean and one
failed-attempt fallback. Context 43 was fast on the small mesh but missed
the large-scale and large-y bounds. The fixed selection rule chose no
policy. The next independent slice is **B2.15**, a bounded position-aware
routing/reliability intervention on fresh development cases. B3 and any
final acceleration claim remain closed.

**B2.15 position-aware routing Gate failed:** The
[frozen 24-case development screen](../validation/b2_15_position_routing.md)
passed 24/24 new uniform references and retained all 192 fully charged
outcomes. The new route improved small-y speed and avoided one old-route
quality fallback, but its large-y mean was `1.006428` against the `1.0`
bound. Its overall paired mean was `0.661286` versus the old route's
`0.686491`, a 3.67% gain below the frozen strict 5% requirement. A
high-volume large-y position still failed candidate quality and paid a
full fallback. Independent audit confirmed failure. The next independent
slice is **B2.16**, a bounded method-class reassessment and attainable
same-quality speed-headroom decision. Stop local routing-threshold search;
B3 and any final claim remain closed.

**B2.16 method-class reassessment completed:** The
[frozen read-only audit](../validation/b2_16_method_class.md) checked
48 exposed B2.14/B2.15 cases and 384 fully charged outcomes without a
new solver or learned run. Impossible per-case successful selectors
retained speed headroom on both cohorts, but optimistic coarse-cell
routes failed transfer in both directions with 15/24 different choices.
An impossible zero-cost early rejection of B2.15's one failed learned
attempt would pass its development arithmetic Gate; the strict
old-route-improvement limit leaves less than 2.8101 s per high-volume
large-y query for an actual two-position diagnostic. The ordered B2.16
decision permits **one bounded online early-reliability probe** as B2.17
and stops further exposed-cohort position/volume threshold searches.
This is not a new acceleration pass; B3 and any final claim remain closed.

**B2.17 online early-reliability sentinel failed:** The
[frozen two-update probe](../validation/b2_17_early_reliability.md)
replayed four exposed high-volume large-y cases with a paid uniform
two-update shadow and a continuous context-17 learned solve. All four
predecision costs were below the strict 2.8101 s cap, but the early
compliance ratio accepted all four starts, including all three known
terminal quality failures. The sentinel failed with three missed
failures and stopped before opening any of the 24 predeclared fresh
cases. The next independent slice is **B2.18**, a bounded assessment of
a genuinely different quality-predictive or solver-aware mechanism.
Do not retune the two-update cutoff on exposed cases. B3 remains closed.

**B2.18 solver-anchored mechanism sentinel failed:** The
[frozen physical-state blend](../validation/b2_18_solver_anchor.md)
combined the audited context-17 prediction with a paid two-update uniform
state and reran full refinement on the same four exposed high-risk cases.
All candidate terminal compliance ratios improved slightly and refinement
shortened by 5–30 updates, but the same three cases still failed the
unchanged quality limit and paid full fallback. The sentinel's charged
mean ratio was 1.575 despite sub-0.90 s pre-refinement costs. Its frozen
stop rule kept four new cases sealed. B3 remains closed. The next slice
is **B2.19**, a bounded learning-side quality-basin repair rather than
another local blend or early-score threshold.

**B2.19 physical-input development Gate failed:** The
[frozen uniform-state sensitivity channel](../validation/b2_19_physics_input.md)
passed 12/12 fresh uniform references, completed three fixed fits, and
retained all 84 fully charged outcomes. All three validation MSE values
improved against B2.12, but no new seed met the full two-scale,
direction-wise and reliability Gate. Seed 17 added one quality failure;
seed 29's large-y mean was 1.188; seed 43 had two failures and large-y
mean 1.546. The fixed B2.12 controls performed better on this one
cohort, which does not reverse B2.14's negative larger confirmation.
B3 remains closed. The next slice is **B2.20**, a bounded intervention
on target or selection alignment with terminal quality and full cost.

**B2.20 operational checkpoint-selection Gate failed:** The
[frozen checkpoint rule](../validation/b2_20_operational_selection.md)
completed three unchanged context-model fits, 12/12 selection and 24/24
screen uniform references, 132 selection outcomes, and 168 independent
screen outcomes. Its selected epochs were 120, 160, and 80 for seeds
17, 29, and 43. None passed the two-scale/direction-wise charged-speed
Gate; every selected seed retained its control's terminal-failure count,
and all six high-volume large-y selected attempts failed quality. B3
remains closed. The next slice is **B2.21**, a bounded learning-side
quality-basin intervention with a frozen mechanism, stop rule, and new
development evidence.

**B2.21 terminal-design target Gate failed:** The
[frozen final-design target](../validation/b2_21_terminal_target.md)
passed 24/24 new uniform references, 12/12 independent validation
targets, three fits, and all 168 charged screen outcomes. Large-z time
improved for all three new seeds against matched B2.12 controls, but
none passed both scale means and four direction means. The highest
volume large-y cases still failed terminal quality for all six new
attempts, and seed 17 added two failures overall. B3 remains closed.
The next slice is **B2.22**, a bounded high-volume y-direction specialist
learning intervention with a fixed route and disjoint screen.

**B2.22 high-volume y specialist Gate failed:** The
[frozen case-weighted specialist](../validation/b2_22_y_specialist.md)
passed 24/24 new uniform references, completed three fits and all 168
fully charged screen outcomes. Its fixed route improved high-volume large-y
terminal quality from 2/6 matched context-control successes to 3/6, but
missed the frozen 4/6 requirement. All three routed large-y direction
means exceeded `1.0`, and no seed met the two-scale charged-speed Gate.
One of the two high-volume large-y load positions failed all three
specialist attempts. B3 remains closed. The next slice is **B2.23**, a
bounded large-y load-position coverage and label-feasibility audit before
any further fit.

**B2.23 large-y position-label data Gate passed:** The
[frozen position expansion](../validation/b2_23_position_labels.md)
blocked 760 exposed or reserved physical case identities and generated
30/30 new quality-feasible large-mesh y-direction uniform labels: 20 train
and 10 validation. All 30 stopped by the physical-plateau rule within
156 updates; materialization took 768.551 s with peak RSS 284,622,848 B,
within the frozen 3,600 s and 1 GiB limits. Independent byte, identity,
split, numerical-quality, resource, and Gate audits passed. The
high-volume large-y training-position union grew from four to thirteen
distinct positions. No model was fitted, so terminal learned quality and
fully charged speed remain unresolved. B3 remains closed. The next slice
is **B2.24**, a separately frozen training intervention using the new
labels and a fresh, physically disjoint development screen.

**B2.24 expanded-position specialist Gate failed:** The
[frozen 20-label training expansion](../validation/b2_24_expanded_training.md)
passed 24/24 new uniform references, three fits, all ten fixed-checkpoint
diagnostic labels, and all 168 fully charged matched outcomes. The new
experts reduced matched high-volume large-y terminal failures from 6/6
to zero and all six successful attempts beat their uniform references
on those two cases. Nevertheless, every new seed exceeded the `0.90`
large-scale charged-time mean, and no seed met every direction bound.
The new route retained lower-volume y failures and costly large-z
refinement. The complete development Gate failed; B3 remains closed.
The next slice is **B2.25**, a bounded read-only diagnosis of residual
large-grid y failures and z refinement cost before freezing another
mechanism and fresh screen.

**B2.25 residual-cost diagnosis completed:** The
[frozen read-only audit](../validation/b2_25_residual_cost.md) verified
B2.24's 24 exposed cases and 168 outcomes. All ten expanded-model
failures were y cases, including six small-grid high-volume attempts
and four lower-volume large-grid attempts. All large-z attempts passed
quality but retained costly refinement. Removing all fallback time
optimistically left zero of three seeds meeting the speed bounds;
setting all large-z times to zero left only one. Only their combined,
unattainably optimistic limit gave three speed-eligible seeds while
leaving all quality failures unresolved. The ordered next mechanism is
one joint non-specialist generalist intervention with the repaired
high-volume large-y specialist fixed. B3 remains closed. **B2.26**
must freeze and test that mechanism on a fresh development cohort.

**B2.26 y-weighted terminal generalist Gate failed:** The
[frozen weighted fit and fresh screen](../validation/b2_26_weighted_generalist.md)
completed 24/24 quality-feasible uniform references, three fits, and
240/240 fully charged outcomes. The unchanged expanded specialist
passed all six high-volume large-y attempts per panel. Weighted seed
17 reduced failures to one and met both large direction limits, but
its large-scale mean remained `0.960` against `<=0.90`; weighted seeds
29 and 43 reached `1.176` and `1.045`. All 16 learned failures on the
three panels were middle-volume y cases, and some large-z trajectories
remained costly. No weighted seed passed the full Gate. B3 remains
closed. **B2.27** is a separately frozen middle-volume large-grid y/z
position-coverage and uniform-label feasibility audit before another
fit or learned screen.

**B2.27 middle-volume y/z label data Gate passed:** The
[frozen position expansion](../validation/b2_27_middle_volume_labels.md)
produced 60/60 independently audited new uniform labels, with 40
train and 20 validation cases and exact y/z balance, inside its time
and memory caps. It made no model fit or learned comparison. B3 and
final evidence remain closed. **B2.28** must separately freeze a
bounded training intervention using the new train labels and test it
on fresh development cases with unchanged numerical quality and
complete fallback charges.

**B2.28 expanded generalist development Gate passed:** The
[fixed expansion and fresh screen](../validation/b2_28_expanded_generalist.md)
completed 24/24 uniform references, three fits, twenty diagnostic
labels, and all 168 fully charged outcomes. Seeds `17,29,43` all met
the frozen two-scale/direction speed and reliability bounds, with
small/large means `0.532/0.585`, `0.580/0.665`, and `0.493/0.587`.
The new panel had zero quality failures or fallbacks and passed all
six middle-volume large-y attempts, compared with three of six for
old; both panels passed all six high-volume specialist attempts.
All six diagnostic MSE means improved, although seed 29's small-scale
charged mean regressed against its old control. This is one bounded
development cohort. **B2.29** must separately freeze a larger physically
disjoint development confirmation with the same checkpoints and route.
Uniform remains the operational default; B3 and final evidence remain
closed until that confirmation passes.

**B2.29 independent confirmation Gate passed:** The
[larger fixed-policy confirmation](../validation/b2_29_development_confirmation.md)
completed 48/48 fresh references and all 432 fully charged outcomes,
including both non-ML comparators. Expanded seeds `17,43` met every
frozen seed criterion, with small/large means `0.776/0.645` and
`0.611/0.759`, zero and two failures, and overall paired means below
both non-ML policies. Seed 29 remained reported and failed the small
and small-z speed bounds (`1.196` and `1.768`). The expanded panel
passed 9/9 middle-volume large-y attempts versus old 3/9; both passed
9/9 high-volume specialist attempts. Independent audit reproduced the
complete decision. **B3.1** is now the next slice: separately freeze
the new versioned ML contract and final exposure boundary. This is
bounded development confirmation, not Gate B3 completion or final
acceleration evidence. Uniform remains the operational default.

### B3: New versioned contract, exposure ledger, and data gate

**B3.1 planning Gate passed:** The
[new formal contract](../b3_experiment_contract.md) freezes 528 train,
32 fit-validation, 48 screen-validation, 96 final-ID, and 48 final-OOD
definitions. A metadata-only audit reproduced the superseded M3 catalog
and verified the 1,376-fingerprint historical ledger, exact memberships,
strata, matched OOD pairs, and zero new-role exposure intersections.
All labels will be regenerated under the fixed 360-update policy.
The contract permits exactly twelve fits, keeps all three seeds, selects
the primary only on new B4 development outcomes, and requires final
quality, two-scale gains, non-ML comparisons, OOD safety, and independent
Linux execution. Its 28-hour cumulative stage budget has explicit stop
rules; failure does not authorize extra tuning or a final-set search.

**B3.2 implementation Gate passed:** The catalog and historical ledger
reproduce the exact frozen hashes and independent B3.1 identity bytes.
Access guards verify case/role/source/membership and derived origins,
reject forbidden requests before opening bytes, require all 528 train
labels for NN, and check returned artifact checksums. Synthetic tests
cover the permission table and malformed/incomplete metadata; no solver
or generated data artifact was used for this slice. See the
[B3.2 validation report](../validation/b3_2_catalog_boundary.md).

**B3.3 implementation Gate passed:** Versioned full-precision and float32
label/reference contracts, content-addressed external artifacts, single-writer
prefix recovery, cumulative resource charges, independent audits and the
read-only planning/explicit execution entrypoint are implemented. Synthetic
FEM states test quality/corruption boundaries; a historical B2.4 before/after
label is byte-identical. No production B3 case was optimized. See the
[B3.3 validation report](../validation/b3_3_data_materializer.md).

**B3.4 data Gate passed:** All 560 labels and 48 screening references were
regenerated from uniform on clean merged revision
`cc151b014f9034ccc7093ef592021003d7dec252`. Complete production and supplemental
independent audits passed exact identity, exposure, mesh/direction/volume
availability, full-precision and float32 quality, sensitivity and resource
checks. Zero cases failed or were replaced. The cumulative data charge was
5,325.353116 seconds and peak RSS 500,154,368 bytes, within the frozen caps.
See the [B3.4 validation report](../validation/b3_4_data_gate.md).
No fitting or final artifact access occurred. **A2.1** then added the
[versioned local worker protocol](../platform_worker_protocol.md) and
[process-boundary validation](../validation/a2_1_worker_protocol.md).
**A2.2** then added [leased run ownership](../run_ownership.md) and
[recovery validation](../validation/a2_2_run_ownership.md).

The subsequent fitting, development-screen failures and repair reviews are
recorded once in [B4](#b4-fit-screen-and-freeze-on-development-data-only).
Their completion does not reopen the final evidence boundary.

Freeze a new experiment identity rather than amending M3 v1. Specify the primary
workload and all train/validation/final-ID/OOD physical-case strata, content-derived
catalog, solver revision, label-success rule, and complete exposure ledger. Use
physically disjoint final cases and prevent their labels/outcomes from reaching
model development. Any new data generation has a read-only clean-revision plan,
external artifact root, fixed compute budget, and checksum audit before fitting.
Preserve every failed case and its denominator. A solver fix or new workload needs
new labels; known M2 successes may be reused only under an explicit provenance and
compatibility rule.

The bounded model program must directly address B1/B2 evidence. Candidate
interventions may include a physics-conditioned input, an intermediate-state
target, or a quality-aligned objective rather than a larger CNN by default.
[Theory-guided learning](https://arxiv.org/abs/1807.10787),
[3D algorithm-aware intermediate-state learning](https://arxiv.org/abs/2012.05359),
and [strain-energy conditioning](https://arxiv.org/abs/2305.10460) motivate
testable options; their published outcomes are not TopoLab evidence. Freeze a small
control/candidate/ablation set, seeds, epochs, selection metric, hardware and memory
budget, stopping rule, and finite reliability policies before training. Charge any
physics feature's FEM solve at query time.

**Gate B3:** Provenance, disjointness, label quality, per-stratum availability, and
the compute budget pass audit; otherwise do not fit.

### B4: Fit, screen, and freeze on development data only

#### B4.1: Fitting Gate passed

The [fixed fitting boundary](../b3_training_contract.md)
completed all twelve preregistered CPU fits from clean merged source
`428c96fd718a78496bcfafcc85a3d82401925ab4`. Complete independent label,
checkpoint/history and equal-case selection audits passed for every seed.
All 1,902 attempted epochs and 24 artifacts were retained, with zero failed
fits or production restarts. The final fitting-stage charge was 3,870.204341
seconds and peak RSS 437,878,784 bytes, within the frozen 7,200-second and
4-GiB caps; see the [B4.1 report](../validation/b4_1_fixed_fitting.md).
That fitting slice opened no screening query or final artifact.
The subsequent **B4.2** screen is recorded below.

#### B4.2: Complete screen; Gate B4 failed

The
[fixed screening boundary](../b3_screening_contract.md) retained all 48 cases
and 720 outcomes from clean merged source
`4279d20c4922cc2cbfaba0bca722aba8868cd914`. Independent byte, NN, terminal,
charge and selection audits passed for all outcomes. All 25 candidate failures
paid successful fresh uniform fallback. P/17 exceeded the small-z direction
bound (1.130297); P/29 exceeded the large-scale mean (0.926609) and matched-C
failure count; P/43 exceeded matched C's failure/non-specialist-y counts.
Neither a primary nor a freeze was produced. Both pooled large-y quality cells
passed at 9/9. The complete charge was 9,869.911762 seconds and peak RSS
602,587,136 bytes, within the frozen caps. A supplemental audit's initial
forbidden single-label NN read was rejected before label bytes; its cost and
permanent integrity marker remain retained after the corrected full-population
audit passed. See the [B4.2 report](../validation/b4_2_development_screen.md).

#### B4.3: Diagnostic acceptance passed

The
[read-only diagnosis](../validation/b4_3_failure_cost.md) verified all 720
outcomes and 162 identical-model comparisons, with an independent 745-status
and arithmetic audit. All paired numerical witnesses were identical, but
31/162 paired times differed by at least 25%, with maximum spread 14.423499.
P/17's small-z update ratio was 0.500483 while its measured time mean was
1.130297; its identical ablation measured 0.730870. The frozen refinement
timer includes periodic full-index checkpoint writes; no isolated callback
or host scheduling durations were retained, so corrected timing cannot be
inferred. P/29 had a converged low-volume large-y quality gap and a
middle-volume large-z 360-update nonconvergence; P/43 had a converged
middle-volume large-y quality gap. All original costs and failures remain
retained. The new analysis charged 50 seconds and peaked at 445,284,352 bytes,
without a solver, fit, model/label byte read or final access.

#### B4.4: Engineering acceptance passed

Its separately frozen 76-query,
two-arm/two-round sentinel retained all 100 candidate/fallback states and passed
independent byte, numerical, chain and cost audits. Every numerical outcome and
known failed status was identical to B4.2. Compact progress reduced inclusive
callback wall by 99.8243% and complete-query wall by 25.3881% in the deliberate
checkpoint-stress fixture. Final charge was 2,406.653985 seconds and peak RSS
705,953,792 bytes, within 7,200 seconds / 2 GiB. Actual process-crash and both
publication windows passed synthetic tests. See
[the engineering report](../validation/b4_4_engineering.md). This establishes
no learned acceleration and does not retime the failed B4.2 experiment.

#### B4.5: Bounded development Gate passed

Its new sensitivity-weighted
terminal-design objective retained the exact 508/32 expanded membership, all
three fixed fits (466 epochs), 48 new uniform references and 576 fully charged
outcomes. Complete label/model, 644-terminal-state, arithmetic, timing and resource
audits passed. W/17 and W/43 met both scale/direction speed and reliability bounds
with zero failures; W/29 met speed bounds but its two failures exceeded matched
C/29's one. Both pooled large-y cells passed 9/9. W/17 is the prospective
development primary by the frozen worst-scale ordering; W/43 has a lower overall
mean but a higher worst-scale mean and remains retained. Final charge was
7,578.184891 seconds and peak RSS 453,132,288 bytes. See
[the complete B4.5 report](../validation/b4_5_weighted_terminal.md).

#### B4.6: Larger independent confirmation Gate failed

All 96 new uniform
references, 1,152 fixed outcomes and 1,250 audit units completed. Independent
checks retained all 1,291 terminal states/classifications and 43 paid failures.
All W scale/direction speed bounds and both pooled large-y cells (18/18)
passed, but W/17's two failures exceeded P/17's zero and violated fixed-primary
reliability; W/29 had four failures, and W/43 had one. Only W/43 passed its
single-seed Gate and no W primary was eligible. Total final charge was
12,528.446019750 seconds and peak RSS 1,492,172,800 bytes. See
[the complete confirmation report](../validation/b4_6_development_confirmation.md).

#### B4.7: Bounded rollback Gate passed

Unchanged P generalists and the same
specialists completed 48 exposure-disjoint uniform references and all 576
fully charged outcomes. The 626 production audit units and independent
646-terminal-state/classification audit passed, with unchanged upstream receipts.
P/17 and P/43 met the frozen seed criteria; P/29's three failures exceeded
matched C/29's two and W/29's one, including two non-specialist-y failures.
Prospectively fixed P/17 had zero failures/fallbacks, charged small/large means
0.857511/0.681739 and total ratios 0.847199/0.665699. It strictly improved the
matched C/17 and W/17 overall means. P/43 retained one failure and was not
primary-eligible. Both pooled large-y quality cells passed 9/9.
Final charge was 6,536.080252125 seconds with peak RSS 829,194,240 bytes. See
[the complete rollback report](../validation/b4_7_spatial_rollback.md).

#### B4.8: Larger rollback confirmation Gate failed

Unchanged fixed P/17 and the
complete P/W/C/non-ML panel completed 96 fresh references, all 1,152 outcomes,
1,250 production audit units and 1,295 independent terminal/classification
checks. P/17 and P/43 passed single-seed criteria; P/29's four failures exceeded
its matched reliability limit. Fixed P/17 paid one quality fallback, violating
its zero-failure requirement; P/43 also retained one failure, so no P primary
was eligible. P/17's small/large charged means were 0.820141/0.668344 and total
ratios 0.786037/0.639162. Pooled large-y quality passed 17/18 and 18/18.
Final charge was 14,105.836381712 seconds with peak RSS 1,036,238,848 bytes.
All complete-cost, numerical, artifact and resource audits passed. See
[the complete B4.8 report](../validation/b4_8_rollback_confirmation.md).

#### B4.9: Read-only diagnostic acceptance passed

All 96 references and 1,152
outcomes, 1,295 stored quality classifications, 48 strata and 54 shared-specialist
pairs passed guarded reads and independent raw-JSON arithmetic audit. The fixed
P/17 failure stopped correctly at physical plateau after 40 updates while its
compliance ratio continued decreasing to 1.001056679441, above 1.001. The full
scalar trace never crossed the quality bound. All four P large-y failures use
physical plateau; P/29's two small-z failures use design change. Zero shared-
specialist charged spreads reached the fixed 1.25 descriptive flag. Diagnostic
charge was 81.608446500 seconds with peak RSS 277,626,880 bytes, including the
retained failed metadata preflight. Original B4.8 charges and failures remain
unchanged. See [the complete diagnosis](../validation/b4_9_confirmation_diagnosis.md).

#### B4.10: Frozen polish sentinel failed

Nine unchanged uniform references
and all 108 queries completed; 119 numerical/input audit units, 117 policy units
and 132 independent terminal classifications passed integrity audits. All 24
prepolish witnesses matched B4.8; twelve qualifying P generalists received
exactly twenty updates and 96 other query identities remained unchanged. All
four known large-y failed P attempts became quality successes. However, an
originally accepted P/17 case became nonconverged: its compliance improved,
but its terminal ten-update relative gain exceeded the unchanged plateau
tolerance. It paid a fresh uniform fallback. Fixed P/17's four-case large-y
generalist mean paired charged ratio was 1.222377 and ratio of charged sums
1.226342, both above 1.0. Final charge was 2,106.109270792 seconds with peak
RSS 635,076,608 bytes. All completeness, numerical, policy and resource audits
passed; all 48 fresh cases remain sealed under the frozen stop rule. Original
failures and charges remain unchanged. See
[the complete polish report](../validation/b4_10_post_plateau_polish.md).

#### B4.11: Diagnostic acceptance passed

The complete nine-reference/108-query
population, all 132 terminal classifications, 24 prepolish certificates,
48 strata and nine specialist pairs passed independent arithmetic audit.
Fixed P/17's new failure loses the plateau certificate at 97 updates despite
better compliance; it does not exhaust the 360-update cap. The measured target
ratios remain 1.222377/1.226342. Fallback-free bounds are 0.980302/0.948499,
preserving the observed failure and leaving only 0.382504 seconds of optimistic
constant guard-cost headroom per target query. No specialist timing pair reaches
the 1.25 descriptive flag. Diagnostic charge is 59.88 seconds and peak kernel
RSS 92,798,976 bytes; the initial outer profiler limitation and its kernel
self-RSS normalization are retained explicitly. No solver call, fit,
checkpoint/label byte read or fresh/final execution occurred. See
[the full B4.11 review](../validation/b4_11_polish_diagnosis.md).

#### B4.12: Preservation repair failed its fresh Gate

Candidate-only selection
passed the complete nine-reference/108-query exposed sentinel, repairing all
four historical P failures without accepted-query regressions. Fixed P/17
had zero sentinel fallbacks and target mean/sum charged ratios
0.958024/0.938039. The independently admitted 48-case physically disjoint
panel completed 48 references, 576 outcomes, 626 numerical/input audit units,
624 policy audit units and 922 independent terminal classifications. All 26
fresh continuations paid twenty updates; no fresh original witness was selected.
P/17 and P/43 passed individual seed criteria but each retained one converged
quality failure/fallback on the same new large-y case. P/29 retained two and
missed the large-y direction limit (1.001002). The pooled middle/high large-y
cells passed 6/9 and 9/9, and P/17 scale charged-sum ratios passed
0.871709/0.770209, but its zero-failure primary requirement failed. No P
primary is eligible and no seed replaces fixed P/17.

The original resource-close command incorrectly required exact float equality
for independently computed means (maximum difference 2.22e-16). Its profile
and cost were retained; separately CI-passed merged source recovered only
resource closure using the already frozen 1e-14 arithmetic agreement. No
numerical rerun, scientific tolerance or Gate changed. Complete charge is
8,486.600 seconds with peak kernel RSS 1,017,036,800 bytes, within frozen
limits. See [the full B4.12 report](../validation/b4_12_terminal_preservation.md).

#### B4.13: Diagnostic acceptance passed

Both complete retained panels,
1,101 terminal classifications, 159 original/endpoint pairs, 96 strata and
36 same-specialist pairs passed independent raw-JSON arithmetic audit.
Fixed P/17's fresh original and twenty-update endpoint both retain their
physical-plateau certificate but fail compliance quality. Its nine-case
large-y generalist measured mean/sum ratios remain 1.117567/1.115091;
fallback-free ratios are 1.012013/0.980559, retaining the observed failure.
Two accepted target refinements remain slower than uniform at ratios 1.713
and 1.505. No specialist pair reaches the frozen descriptive timing flag.
New charge is 107.78 seconds with peak RSS 109,936,640 bytes; original
B4.12's 8,486.600-second charge and all thirty metadata/38 historical guards
remain unchanged. No solver, fit, continuation, label/model byte read,
threshold/length search or final access occurred. See
[the complete B4.13 review](../validation/b4_13_preservation_diagnosis.md).

#### B4.14: Method-review acceptance passed

All 684 independently certified
compact rows, 159 prior witness pairs and 96 prior strata remain complete.
A separate auditor reconstructs three cost scenarios, conditional constant-query
overhead and complete-uniform-shadow floors, retaining every failed status.
The nine-target fallback-free mean remains 1.012013, requiring improvement even
at zero added overhead. Perfect rejection leaves slower accepted refinements;
always-paid full uniform plus positive candidate work cannot accelerate. These
are diagnostic bounds, not new Gate criteria or terminal numerical checks.
The six fixed mechanisms recommend one separately registered offline direct-
compliance feasibility probe. Charge is 50.39 seconds / 42,287,104 bytes;
all ten B4.13 bindings and prior B4.12/historical/recovery guards are unchanged.
See [the complete method review](../validation/b4_14_generalist_method_review.md).

#### B4.15: Numerical correctness passed, prospective fit feasibility failed

the frozen training-only version implements the current-prediction FEM adjoint
through clipped additive projection, physical-volume offset and density filter.
Eight exact expanded-train cases, sixteen fixed fixtures and all three repeated
forward/backward measurements per fixture were retained. The independently
assembled 24 normalizer/central-state solves completed the 200-solve population;
all 408 conditions and 64 fixed-step differences passed, maximum error
3.32609e-6. No scientific tolerance or step changed after execution. The
query projection remains unchanged; no model was fitted and no final access
occurred. Complete native charge is 84.33 seconds / 510,836,736 bytes.

The three-seed, 200-epoch, 508-case planning proxy, using per-scale maximum
prepared wall with fixed 1.25 multiplier plus the conservative existing-fit
baseline and complete probe cost, totals 60,339.394 seconds. It exceeds the
7,200-second cap; this prospective Gate remains failed. Conditional fit/probe
amortization is not measured acceleration or full experiment amortization;
shared data, screening and later final/replication costs remain additionally
required. Sequential probe RSS does not certify full fit memory.
See [the frozen probe evidence](../validation/b4_15_offline_compliance_adjoint.md).

#### B4.16: Cost-review acceptance passed

All eight cases, sixteen fixtures and
48 complete wall/CPU observations, including the first, were independently
reconstructed with 818 arithmetic/boundary conditions. The original
60,339.394-second maximum proxy and failed 7,200-second Gate remain unchanged.
Even zero small physics plus minimum observed large wall gives 13325.669
seconds with the original fixed costs. This descriptive sample arithmetic is
not an optimized-method lower bound or a revised Gate. Setup, complete native
CPU/wall/RSS and every original observation remain retained. No new FEM solve,
benchmark, label/model artifact, fit, continuation or final access occurred.
New charge is 55.99 seconds / peak RSS 305,807,360 bytes; see
[the complete review](../validation/b4_16_offline_adjoint_cost_review.md).

#### B4.17: Numerical parity passed; prospective cost Gate failed

One frozen
candidate caches immutable unit stiffness, COO indices, free-DOF maps and
physical-volume weights while freshly assembling and factorizing every
changing prediction. Eight previously certified training cases and sixteen
fixed synthetic inputs produced 96 complete paired original/prepared Torch
measurements, 96 exclusive phase intervals and 256 new FEM solves; no label
or model bytes were reopened. All 768 independent numerical/gradient
conditions and 64 fixed directional checks passed with unchanged tolerances.
The three-seed/200-epoch/508-case proxy totals 58,257.457957 seconds including
all per-case preparation extrapolation, prior B4.15/B4.16 and complete new
cost, above 7,200. B4.15's original 60,339.394130 proxy remains failed.
Complete new charge is 112.34 seconds / 486,866,944 bytes, with all native
plan/probe/audit/closure/controller profiles and reservations retained.
Sequential RSS and static-array population estimates do not certify full
training memory. See [the probe](../validation/b4_17_prepared_fem_probe.md).

#### B4.18: Read-only method-review acceptance passed

All eight cases, sixteen
synthetic states, 96 paired Torch observations, 96 instrumented phase intervals
and six frozen method dispositions passed 1286 independent scalar conditions.
The original 58,257.457957-second prepared proxy remains failed. Zero small
plus minimum observed large still exceeds 7,200; sampled large factorization/
pivot wall share is 82.3882%. Ideal phase-deletion arithmetic is diagnostic,
not a revised Gate or optimized-method lower bound. Static array estimates and
sequential RSS do not certify full training memory. Complete new charge is
86.13 seconds / 301252608 bytes. See
[the full review](../validation/b4_18_fem_objective_method_review.md).

#### B4.19: Stopped; feasibility did not pass

The single production attempt
rejected anchor compliance versus the stored normalizer at relative 1e-9.
No complete `probe.json` was emitted and the planned numerical auditor did
not run. The 72 states, 216 measurements, 64 directional rows and 416 total
solves remain planned evidence, with no local fidelity or fit-cost result.
Failed case, numerical gap, exact opened-label/FEM counts and buffered
fields were not published; they remain unknown rather than inferred from
timing. The source-level stored float32 physical-density versus unquantized
filtered-anchor boundary requires separate correctness verification.
No tolerance or normalizer change, new numerical invocation, fit or final
access followed the stop. Metadata-only independent early-stop audit and
native resource verification passed within 73.93 seconds / 311902208 bytes.
Full training memory remains pending. See
[the complete early-stop report](../validation/b4_19_local_compliance_surrogate.md).

#### B4.20: Correctness Gate failed

All eight guarded train cases, sixteen
synthetic projected inputs, 64 directional rows and 32 fresh FEM solves completed
984 independent numerical conditions. One FD error 1.2525436e-4 exceeded
the unchanged 1e-4 limit; 983/984 conditions passed. No rerun or tolerance change
followed. Retaining the stored denominator with
the continuous anchor's nonunit intercept handles the precision boundary;
6/8 current anchors reject the old equality. The original B4.19 failed case,
gap and counts remain unknown. Durable before-call/prefix evidence and native
closure passed within 100.30 seconds / 447741952 bytes. No local fidelity,
fit-cost proxy or full training memory evidence follows. See
[the review](../validation/b4_20_surrogate_correctness.md).

#### B4.21: Read-only review acceptance passed

The complete failed panel retained all 64 rows and both steps. All 80 saved
gradient/mask conditions and 1152 independent scalar comparisons passed.
The original failure fits the fixed diagnostic root/arithmetic envelope;
missing side offsets/residuals prevent a causal claim. No root/FEM or label/model
artifact read occurred. New charge is 90.27 seconds; peak RSS 300400640 bytes.
B4.20's failed Gate and every earlier unknown/charge remain; see
[the review](../validation/b4_21_correctness_failure_review.md).

#### B4.22: Versioned stable-projection correctness Gate passed

1704/1704 independent conditions passed across eight cases, sixteen fixtures
and 64 rows at both steps. Maximum directional error is 5.64e-9; 32 FEM solves
and 304 projections were paid. Actual root offsets, residuals and kink margins are retained with
durable before/after counts. The single free-set affine root refinement leaves
all old operators, labels, normalizers and thresholds intact. New charge is
104.62 seconds; peak RSS 433274880 bytes. No fidelity/cost or full training-memory
acceptance follows. See [the probe](../validation/b4_22_stable_projection_correctness.md).

#### B4.23: Versioned local-surrogate feasibility Gate failed

Integrity passed 3907/3976, with 35 side-mask and 34 finite-difference conditions
failed. All 32 LOCAL states met the observed fidelity criteria, which cannot
clear failed integrity or authorize fitting. Complete cost proxy is
57546.072069 seconds against 7200. All 72 states, 216 timings and 64 directional
rows remain; 432 FEM solves and 816 projections were paid. No failed state,
first timing, historical charge or original step was removed. New charge is
143.47 seconds; peak RSS 550502400 bytes.
Full training memory and learned repair remain pending. See
[the finite probe](../validation/b4_23_versioned_surrogate_feasibility.md).

#### B4.24: Registered saved-panel review acceptance passed

All 2104 saved-state predicates and 1728 independent row-field comparisons
passed across eight cases, 72 central states, 128 sides and 64 directional rows.
All 216 first timings and exact original 69 failed condition identities remain.
35 mask and 34 FD failures overlap on 34 rows; all failed FD rows cross the
central active set and their signed gaps are clipping-compatible within the
frozen diagnostic envelope. This is a finite-interval description, not a global
cause, changed pointwise gradient or repaired scientific Gate. B4.23 remains
failed 3907/3976 and cost 57546.072069>7200.

Original v1 field mismatch and v2 sandboxed planning lost-RSS failures remain,
with old 76.19 charge, old 50.53/60 reserve and zero v2 recovery review/audit.
The owner-approved v3 continuation paid another full 60 reserve under unchanged
whole 240/cumulative-review 60. One review and one independent audit completed
from clean merged CI-passed source. Total B4.24 charge is 200.98; new reserve
use 42.49/60 and continuation peak 415268864 bytes pass the scoped requirements.
Historic planning RSS/child exit, whole peak and global memory compliance remain
unknown; the original memory proof stays incomplete. Full training memory and
learned repair remain pending. See [the complete new report](../validation/b4_24_registered_continuation.md)
and unchanged [interrupted report](../validation/b4_24_versioned_correctness_failure_review.md).

#### B4.25: Bounded active-set method review acceptance passed

The separately frozen complete scalar review passed 448 predicates and 2222
independent field comparisons. All 64 rows, 35 mask/34 FD failures, 69 failed
positions, both original steps and the full 57546.072069>7200 cost object remain.
All failed FD rows cross the central clipping set and remain clipping-compatible;
this neither proves a global cause nor repairs scientific correctness. Original
216 first timings remain inherited hash-bound evidence, without raw-panel reads.
The independently derived strictly fixed-set derivative and six method dispositions
recommend active-set-aware evidence preregistration only. Two fixed zero-work
scenarios retain setup/fits/prior charges and are not optimized-method bounds.

One review/audit ran from clean merged CI-passed source. New charge 80.34/180
includes paid 60 reserve, use 40.41/60 and peak 26492928 bytes; complete
native/post-exit/ledger proof passed. B4.24's 200.98, both failures and historic
missing RSS/whole-memory unknowns remain; full training-memory evidence, fixed
P/17 repair and independent confirmation stay pending. See
[the complete report](../validation/b4_25_active_set_method_review.md).

#### B4.26: Read-only correctness and cost preregistration accepted

The separate [protocol](b4_26_active_set_preregistration_protocol.md) and
[authored acceptance contract](b4_26_active_set_acceptance_contract.json) passed
66 static metadata predicates and 28 independent document/metadata checks.
Future evidence separately requires full pointwise cotangents and complete
same-step interval/transition coverage; all legacy rows, failures and both
steps remain. Undefined central derivatives or incomplete coverage stop.
The 32 LOCAL criteria, complete first-inclusive maxima, all prior charges,
three seeds/200 FULL epochs/432+76 cases/factor1.25 and 7200-second limit remain.
Full training memory remains pending under 4 GiB; static/sequential evidence
cannot certify it. No production or numerical execution occurred. This is
preregistration acceptance, not scientific correctness, cost feasibility or
learned repair; see [the report](../validation/b4_26_active_set_preregistration.md).

#### B4.27: Synthetic software implementation acceptance passed

The separate [software protocol](b4_27_active_set_evidence_protocol.md) implements
independent full cotangents and exact complete affine-interval certificates.
42 analytic/exhaustive/tampering and unchanged-v3 tests pass. Complete
coverage, continuity, signed integrals and simultaneous transitions are proven;
central kinks, degenerate partitions and missing/overlapping pieces reject.
All original tolerances/steps and the 256-piece bound remain. No production
payload, FEM, timing, numerical trial or fit occurred. Independent physical/FEM
origins remain future numerical-audit prerequisites. See
[the software report](../validation/b4_27_active_set_evidence.md).

#### B4.28: Finite numerical evidence executed and closed

New integrity PASS, LOCAL PASS; single registered attempt and
independent audit under source main `db9460a743b5` after CI.
All original populations, steps, tolerances,69 failures and first/failure-inclusive
costs remain. New charge 234.60, added view 58061.992069>7200.
Preparation native RSS/child-exit proof remains UNKNOWN after its
retained sandbox sysctl failure; whole resource acceptance is INCOMPLETE.
Full training memory PENDING; no fit/search/final access. See
[report](../validation/b4_28_active_set_numerical_evidence.md).
#### B4.28 historical successor boundary

Next is separately frozen/read-only **B4.29 outcome and cost/full-memory review**,
after full closure/main CI, the last session slice. The ordered route is
cost-and-full-memory-review. Ordinary waiting remains default; no fourth slice follows.

#### B4.29: Read-only outcome and cost/full-memory review closed

One review and independent Decimal audit under separate finite contract and
clean merged CI-passed source; only ten hash-bound compact metadata paths.
Metadata review PASS, own resource PASS, Q29=80.26, added known
cost58142.252069>7200. B4.28's3232/3232 and32/32 observations remain bounded;
its preparation RSS/exit/whole-resource proof stays UNKNOWN/INCOMPLETE. Every
prior failure/charge/unknown remains; no raw/numerical/fit/final access. See
[report](../validation/b4_29_active_set_outcome_review.md). At full publication
closure, the three-slice session stops; next intervention requires an owner
decision and independent finite contract. No fourth slice is authorized.

B4.23 remains failed 3907/3976 and 57546.072069>7200; all 69 failures, first
timings and charges remain. B4.20 stays failed, B4.19 fields unknown, B4.24's
historical memory proof incomplete. Full training memory, fixed P/17 repair,
independent confirmation, complete new B4 Gate and compatible final contract
remain required. Uniform stays default; final/48 unused B4.10 cases sealed.
No cache/ordering, continuation, epoch/population/physics-frequency or
quality-threshold search follows. Ordinary single-slice waiting remains the
repository default; session-specific authorization does not amend it.

#### B4.30: Fixed-primary reflection repair interrupted before numerical work

The owner-approved [protocol](b4_30_z_reflection_repair_protocol.md) and
[finite contract](b4_30_z_reflection_repair_contract.json) remain unchanged.
Same P checkpoint/re-encoded mirror/0.5 mean only in large-y volume<0.55,
fixed17/seeds17/29/43, all C/P/W/non-ML controls and old solver/witness criteria.
Tested merged source passed CI, but the one native campaign's legacy entry
rejected preserved untracked owner documents before numerical/payload access.
0/18 refs,0/270 queries, fresh48/720 unopened; paid191.9666532080154866/FULL180.
Scientific NOT ESTABLISHED, production resource FAIL/INCOMPLETE; independent
metadata-prefix audit PASS. A strict early source check and clean independent
checkout are prepared; the old clean requirement is not relaxed. The consumed
one-campaign limit needs an owner decision for exactly one paid technical
continuation of this unfinished slice. Whole cap43200/2GiB and66/990 remain,
failed cost is retained; no count reset, third attempt or new research slice.
See [report](../validation/b4_30_z_reflection_repair.md). No outcome was seen for
adaptation; repair/full new B4/independent confirmation/final compatibility
remain before B5. The three-slice old quota stays exhausted and waiting remains.

#### B4.30 paid continuation complete; fixed-primary repair failed

The owner's one paid technical continuation used the separately frozen
[v2 protocol](b4_30_paid_continuation_protocol.md) and
[contract](b4_30_paid_continuation_contract.json), retaining every original
scientific criterion/model/role/seal. PR164 tested/protected-merged/main-CI-passed
source and whole-clean locked independent checkout preceded access. All18/270
and numerical/input290/290, policy288/288, independent raw-JSON and native exit
verification complete. Scientific FAIL: common large-y case55c1b3e… still fails
R17/29/43; R17 ratio1.0019709437499813>1.001 and thirteen-target mean
1.016053130777518>1.0. Pooled0.9853173206553424 passes only its separate predicate.
Four historical target predicates pass already in current P; no currently
failed P target newly repaired, P/R failures1/3/1. Retain35 failures/fallbacks,
323 terminal/204 guard classifications,78 prediction replays/249 old identities.
No accepted regression; two negative controls and all non-target identities remain.

Complete v2 chain resource PASS, cumulative7323.1004352501081506/43200 retaining
old191.9666532080154866 and both FULL180, conservative whole-chain bound
800047104<2GiB. Conditional48/720 remains unopened; original failed prefix,
all old memory gaps and full-fit PENDING/4GiB stay. See
[complete report](../validation/b4_30_paid_continuation.md). Report/indices,
all5 validations, evidence PR/exact-head/main CI/byte backup close this same
slice; exactly2 administrative invocations/1 numerical campaign, old3/3 retained.
The reflection mechanism stops. B4.31 was proposed at this historical closure;
its current owner-authorized preregistration is below. No third B4.30 trial,
changed math/model/budget/tolerance/role/seal, fit/search or B5 follows.

Compare each model to uniform and non-ML baselines on fallback-inclusive
validation time, independent compliance, convergence, volume, and failure strata.
Calibrate only predeclared reliability thresholds. Rejected candidates pay all
inference/decision plus uniform time; accepted failures retain a full fallback
charge. A candidate that improves image MSE but not operational quality and time
does not advance. Retain every case and seed. Freeze code, checkpoints, thresholds,
statistics, environment, and source revision before final evaluation.

**Gate B4:** A meaningful validation gain over the optimized uniform and fixed
non-ML alternatives survives all charges and quality checks. Otherwise diagnose,
version a new hypothesis, and leave final evidence sealed.

### B4.31: Bounded read-only reflection failure and cost review

The owner's 2026-10-08 single-slice takeover froze the
[protocol](b4_31_reflection_failure_cost_review_protocol.md) and
[contract](b4_31_reflection_failure_cost_review_contract.json). Source PR166
head13af1a4/main4a51ebe6fbe6, all exact-head/main CI and whole-clean locked
independent source preceded the only metadata campaign. Eight scalar inputs
per role,118/118 float review and430/430 separate Decimal/status audit PASS.
No old raw/model/label/profile dereference, predictor/FEM/fit, retiming/search,
final/fresh/unused access. See [report](../validation/b4_31_reflection_failure_cost_review.md).

All15 methods/270 outcomes/35 failures/fallbacks and all seven historical units
retain matched P/R statuses: four passes already in P, no currently failed P
target newly repaired. Fixed R17 ratio1.0019709437499813>1.001 and13-target mean
1.016053130777518>1.0 remain failed. Pooled0.9853173206553424 cannot substitute.
Per-target costs/fallback phase times stay outside scope/UNKNOWN; cause remains
unestablished. Reflection stops, fixed primary17 cannot be replaced.

Own native resource PASS, Q31=80.29939475003629922 including FULL60, reserve
observed+floor11.16154991695657376<60, conservative complete native sum219463680
<1GiB. Last verifier actual exit checked; original PENDING receipts stay.
Old7323.1004352501081506 ledger unchanged, separate campaign-plus-review
7403.39983000014444982. Preserve old cost/memory failures, full fit PENDING/4GiB.
Source premerge-driver failure/incorrect continuation and later protection/tree/
CI-time audit remain explicit.58 focused/1393 source/1393 evidence tests and
all5 checks, all-upload guards, protected evidence/main CI and byte backup close
only this slice. Metadata/resource/CI PASS never repairs scientific FAIL.

Proposed B4.32 read-only generalist reliability/cost method review and
preregistration requires new owner authorization/finite contract. No numerical
intervention is selected, fit/search or final access granted. Full learned
repair, independent confirmation and compatible final contract remain before B5.

### B4.32: Bounded generalist method review and preregistration

The owner's continuation after closed B4.31 authorized one documentation slice.
The [protocol](b4_32_generalist_method_preregistration_protocol.md) and
[authored contract](b4_32_generalist_method_preregistration_contract.json) passed
69/69 static and32/32 independent Decimal/document checks. See
[report](../validation/b4_32_generalist_method_preregistration.md). No production
scalar replay, payload, numerical candidate evaluation, objective/FEM/root/
projection, fit, retiming/search or final/fresh/unused access occurs.

Six dispositions stop historical reflection/exact-FEM/signed-tangent candidates
and preregister only one fixed-anchor reciprocal-element-energy hypothesis.
Conditional PSD/Cauchy–Schwarz proof gives an upper bound/equality/anchor gradient
under exact equilibrium; approximate anchors require independent residual/
spectral/rounding certification, still UNKNOWN. No global tightness, convexity,
fitted quality or affordable training follows. Eight future public toy fixtures
and candidate-free algebra/role rejection checks are prospective software only.

All original failures/unknowns/costs stay, including old69 predicate positions,
57546.072069/58142.252069>7200, old7323.1004352501081506 and Q31 once. Known
disjoint actual-stage subtotal12721.16417100014444982>7200 is diagnostic
accounting, not new budget permission or ledger reset. Full fit PENDING/4GiB
and real-state fidelity/cost/memory/learned repair/confirmation remain separate.
Runtime/tests/conventions/README and historical frozen bytes are unchanged.
All five checks, document/per-path/all-upload guards, protected exact-head/main
CI, owned-branch cleanup and byte backup govern publication closure.

Next proposed **B4.33 bounded reciprocal-energy algebra and access evidence
implementation**, software only, needs a separate owner instruction and frozen
contract. No actual training input, FEM, projection/root/network integration,
fit, retiming/search or changed budget follows. Uniform/P17 and seals remain;
report the next proposal and stop after B4.32.

### B5: One-time final comparison and project delivery gate

Open the new ID cohort once after B4, followed by predeclared OOD and independent
replication in the frozen order. Report phase costs, paired physical-case bootstrap
intervals, quality, volume, iterations, failed/rejected/fallback cases, memory,
training/generation cost, and amortization. The exact workload-specific claim gate
must have been fixed in B3 and must meet the minimum in Section 2. If any required
stratum or independent replication fails, publish the negative result without
changing the cohort, threshold, solver, or model. The project remains **in
development**, not fully delivered. Plan a finite new versioned experiment from
the diagnosed cause and reserve new final evidence. Do not start an unregistered
search on B5 outcomes.

## 5. Version, branch, and validation rules

- Each slice starts from current `main`, has a short-lived branch, and merges via PR and CI.
- Version new platform contracts, checkpoints, and ML artifacts explicitly.
- Write a failing test or independent acceptance case before changing numerical behavior.
- Commit a production contract/runner first; run a read-only plan from its clean merged revision before production execution.
- Keep generated datasets, checkpoints, databases, logs, raw experiment screenshots
  and run results external. Commit protocols, validation reports and reviewed original
  presentation assets according to the [repository policy](../repository_policy.md).
- Close each stage with a validation report, including failed gates.
- Update current status and the evidence/history indices at slice closeout. Keep
  AGENTS.md focused on constraints and README focused on stable public usage.
- Update README, resume, or title claims only after their supporting gate actually passes;
  routine slice results belong in the linked status and evidence documents.

## 6. Recommended sequence

The completed sequence remains in [development history](../development_history.md)
and validation reports. B4.28 passes fresh bounded integrity/LOCAL criteria;
cost remains failed and complete native resource acceptance is INCOMPLETE.
All old failures/costs/unknowns and full-memory/learned-repair requirements remain.

1. **Proposed B4.33 bounded reciprocal-energy algebra and access evidence
   implementation:** not started/authorized; software only on8 public toy
   fixtures after a separate finite contract. B4.32 is preregistration PASS
   only. Preserve all failed Gates/costs/unknowns; no production or fitting.

2. **Any later correctness/objective-feasibility intervention:** preserve all
   evidence and require independent correctness, fidelity, compute and full
   training-memory proof. The unchanged exact-FEM candidate remains stopped.
   No cache/ordering, epoch/population/frequency search or fit is authorized.
3. **Learned repair and independent confirmation:** preserve fixed P/17, all
   controls, failures and charged comparisons. A bounded development pass alone
   cannot open final evaluation or substitute another seed for the fixed primary.
4. **Compatible final contract and B5:** only after the complete new B4 Gate passes,
   freeze the compatible method and run the one-time ID/OOD/replication sequence.
5. **A2.3–A2.4 and A4:** complete optimizer recovery, cancellation/resource bounds
   and controlled delivery in separate platform slices as requirements justify.

After each completed independent slice, report its Gate, evidence, limitations
and next slice, then wait for a new user instruction before starting it.

## 7. Stage completion evidence

Measure later work by evidence rather than feature count:

| Goal | Completion evidence |
|---|---|
| Easier reproduction | One clean-environment path, fixed demo, smoke, run report |
| More reliable platform | Crash/restart/cancel/concurrency/duplicate-claim tests and an explicit state machine |
| Stronger performance | Phased profile, cross-environment benchmark, numerical equivalence |
| Required ML acceleration | Correct numerical baseline, measured headroom, new exposure boundary, bounded interventions, and a passed fresh end-to-end claim gate |
| Better application presentation | Traceable resume numbers; demos and README within claims boundaries |

Platform and numerical milestones remain separately valuable and truthfully
reportable. They do not substitute for the required positive ML result in the
full v2 flagship delivery decision. A failed ML experiment is retained as
evidence and informs the next explicitly bounded intervention; no final project
completion claim follows from a failed ML gate.
