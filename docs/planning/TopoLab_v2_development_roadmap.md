# TopoLab v2 Development Roadmap

Status: **active v2 flagship delivery plan; Gates A1 and A3 passed; B2.2's
120-update data gate failed, B2.3's versioned 240-update sentinel passed,
B2.4's complete 522-label development data Gate passed, B2.5–B2.9's
fixed learned-prototype feasibility Gates failed, B2.10's screen stopped
at a failed mandatory uniform reference after nine cases, and B2.11 passed
its reference repair but failed the fixed-model development Gate, B2.12's
spatial-context model passed reference/fit Gates but failed the fresh
development acceleration Gate, B2.13's fixed routing policy passed its
small fresh development screen, B2.14's larger confirmation failed with
no eligible routed or fixed policy, B2.15's position-aware route failed
its fresh development Gate, and B2.16's read-only method-class audit
supports one bounded early-reliability probe while ruling out further
coarse metadata threshold tuning;
the B2.17 paid two-update sentinel then failed to detect three of three
terminal quality failures and stopped before opening fresh cases;
the B2.18 solver-anchored start modestly improved all four exposed
solutions but retained three terminal quality failures and stopped
before fresh cases;
the B2.19 physical-input model passed twelve fresh references and three
fits but failed its 84-outcome learned Gate despite lower validation MSE;
the B2.20 operational checkpoint selection completed its 12-case
selection and 24-case independent screen, but no selected seed passed
and all six high-volume large-y selected attempts failed terminal quality;
the B2.21 terminal-design target passed all reference, target, fit, and
screen completeness/resource checks but still failed its learned Gate,
with 0/6 high-volume large-y new attempts passing terminal quality;
the B2.22 high-volume y specialist completed 24 references, three fits,
and 168 screen outcomes, improving matched high-volume large-y quality
from 2/6 to 3/6 but failing its four-of-six quality and two-scale speed Gates;
the B2.23 large-y load-position expansion passed its 30/30 independent
development-label quality and resource Gate, without a model fit or learned
speed claim;
the B2.24 expanded-position specialist completed 24 fresh references,
three fits, ten diagnostic labels, and 168 outcomes, improving matched
high-volume large-y quality from 0/6 to 6/6 but failing the full
two-scale and direction-wise charged-speed Gate;
the B2.25 read-only audit bound all B2.24 outcomes and selected a joint
non-specialist quality/refinement intervention for one fresh B2.26 screen;
the B2.26 weighted terminal generalist completed 24 fresh references,
three fits, and 240 outcomes but failed the two-seed large-scale speed
Gate, with all residual learned failures at middle-volume y cases;
the B2.27 middle-volume y/z position expansion passed its 60/60
development-label quality and resource Gate without fitting a model;
the B2.28 forty-label generalist expansion completed 24 fresh references,
three fits, twenty diagnostics, and 168 charged outcomes; all three
seeds passed its bounded development Gate;
the B2.29 larger independent confirmation then completed 48 new
references and all 432 charged outcomes; expanded seeds 17 and 43
passed, while seed 29 failed the small-scale and small-z speed bounds,
permitting B3.1 contract planning with final evidence still sealed;
the B3.1 formal contract now freezes its 752-case catalog, complete
historical exposure boundary, fixed model program, prospective primary
selection, final claim/replication rules, and finite compute budget;
its metadata planning audit passed, with Gate B3 data audit still pending;
the B3.2 implementation reproduced both frozen metadata hashes and
passed consumer-specific access and complete-population rejection tests;
the B3.3 implementation added versioned data/artifact contracts, guarded
materialization, charged recovery and independent audits; its implementation
tests passed, with actual B3 data generation reserved for B3.4;
the B3.4 production data Gate passed with all 560 labels and 48 screening
references independently audited, zero failures, 5,325.353116 charged
seconds and 500,154,368-byte peak RSS; no fit or final artifact access;
A2.1 added a versioned JSON-line manager/worker boundary and separate local
process for default numerical runs; A2.2 added leased SQLite ownership,
fencing, queued recovery and schema migrations; later A2 work remains open;
ML acceleration is a required delivery gate, not an optional enhancement.**
The released `v1.0.0` and
its negative M1/M2 conclusions remain historical evidence.

Prepared: 2026-09-24
Revised: 2026-10-01

Related documents:

- [Graduate admissions fit assessment](./TopoLab_admissions_fit_assessment.md)
- [Development timeline and resources](./TopoLab_development_timeline_and_resources.md)
- [v1.0.0 release validation](../validation/v1_release_validation.md)
- [M1 held-out evaluation](../validation/m1_held_out_evaluation.md)
- [M2 materialization outcome](../validation/m2_catalog_materialization.md)
- [M3 v1 pre-registration](../m3_preregistration.md)
- [Development-only warm-start feasibility probe](../validation/ml_feasibility_probe.md)
- [A1.1 canonical demo validation](../validation/a1_1_canonical_demo.md)
- [A1.4 clean Linux validation and Gate A1 decision](../validation/a1_4_clean_linux_smoke.md)
- [A3 solver-ordering audit](../validation/a3_solver_ordering.md)
- [B2 workload pilot and gate decision](../validation/b2_workload_pilot.md)
- [B2.1 versioned convergence correction and matched audit](../validation/b2_1_convergence.md)
- [B2.2 prototype plan and data-feasibility outcome](../validation/b2_2_data_feasibility.md)
- [B2.3 budget repair and sentinel audit](../validation/b2_3_data_feasibility.md)
- [B2.4 complete development-label audit](../validation/b2_4_development_labels.md)
- [B2.5 fixed prototype and full development screen](../validation/b2_5_prototype.md)
- [B2.6 intermediate-trajectory target and new development screen](../validation/b2_6_trajectory.md)
- [B2.7 global-load input and new development screen](../validation/b2_7_global_load.md)
- [B2.8 y-load basin recentering and new development screen](../validation/b2_8_basin.md)
- [B2.9 vector point-load conditioning and new development screen](../validation/b2_9_vector_load.md)
- [B2.10 sensitivity-weighted objective and reference-feasibility stop](../validation/b2_10_weighted_trajectory.md)
- [B2.11 versioned reference budget and fixed-model confirmation](../validation/b2_11_reference_budget.md)
- [B2.12 spatial-context model and new development screen](../validation/b2_12_context_cnn.md)
- [B2.13 workload routing and safe rejection](../validation/b2_13_routing.md)
- [B2.14 frozen larger development confirmation protocol](./b2_14_development_confirmation_protocol.md)
- [B2.14 completed larger development confirmation](../validation/b2_14_development_confirmation.md)
- [B2.15 frozen position-aware routing protocol](./b2_15_position_routing_protocol.md)
- [B2.15 completed position-aware routing screen](../validation/b2_15_position_routing.md)
- [B2.16 frozen method-class reassessment protocol](./b2_16_method_class_protocol.md)
- [B2.16 completed method-class reassessment](../validation/b2_16_method_class.md)
- [B2.17 frozen online early-reliability protocol](./b2_17_early_reliability_protocol.md)
- [B2.17 exposed-sentinel outcome](../validation/b2_17_early_reliability.md)
- [B2.18 frozen solver-anchor protocol](./b2_18_solver_anchor_protocol.md)
- [B2.18 solver-anchor sentinel outcome](../validation/b2_18_solver_anchor.md)
- [B2.19 frozen physical-input protocol](./b2_19_physics_input_protocol.md)
- [B2.19 complete physical-input fit and screen](../validation/b2_19_physics_input.md)
- [B2.20 frozen operational checkpoint-selection protocol](./b2_20_operational_selection_protocol.md)
- [B2.20 complete selection and independent screen](../validation/b2_20_operational_selection.md)
- [B2.21 frozen terminal-design target protocol](./b2_21_terminal_target_protocol.md)
- [B2.21 complete fit and independent screen](../validation/b2_21_terminal_target.md)
- [B2.22 frozen high-volume y specialist protocol](./b2_22_y_specialist_protocol.md)
- [B2.22 complete specialist fit and independent screen](../validation/b2_22_y_specialist.md)
- [B2.23 frozen position-coverage and label protocol](./b2_23_position_labels_protocol.md)
- [B2.23 complete position-label feasibility audit](../validation/b2_23_position_labels.md)
- [B2.24 frozen expanded-position specialist protocol](./b2_24_expanded_training_protocol.md)
- [B2.24 complete fit and independent screen](../validation/b2_24_expanded_training.md)
- [B2.25 frozen residual-cost diagnosis protocol](./b2_25_residual_cost_protocol.md)
- [B2.25 complete read-only cost audit](../validation/b2_25_residual_cost.md)
- [B2.26 frozen weighted generalist protocol](./b2_26_weighted_generalist_protocol.md)
- [B2.26 complete fit and matched screen](../validation/b2_26_weighted_generalist.md)
- [B2.27 frozen middle-volume position-label protocol](./b2_27_middle_volume_labels_protocol.md)
- [B2.27 complete position-label feasibility audit](../validation/b2_27_middle_volume_labels.md)
- [B2.28 frozen middle-volume generalist expansion](./b2_28_expanded_generalist_protocol.md)
- [B2.28 complete expanded fit and fresh screen](../validation/b2_28_expanded_generalist.md)
- [B2.29 frozen larger independent confirmation](./b2_29_development_confirmation_protocol.md)
- [B2.29 completed independent confirmation and audit](../validation/b2_29_development_confirmation.md)
- [B3 frozen formal experiment contract](../b3_experiment_contract.md)
- [B3.1 contract and exposure planning audit](../validation/b3_1_contract_boundary.md)
- [B3.2 catalog and access boundary](../validation/b3_2_catalog_boundary.md)
- [B3.3 guarded data materializer](../validation/b3_3_data_materializer.md)
- [B3.4 production data Gate](../validation/b3_4_data_gate.md)
- [A2.1 local worker protocol and validation](../validation/a2_1_worker_protocol.md)
- [A2.2 durable ownership and validation](../validation/a2_2_run_ownership.md)

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
[recovery validation](../validation/a2_2_run_ownership.md). **B4.1** then
completed the twelve fixed CPU fits and independent artifact/selection
audit within its frozen epoch/time/memory caps. **B4.2** completed the fixed
development screen but failed its direction/reliability Gate, with no primary
or freeze. **B4.3** completed the bounded read-only failure/cost diagnosis.
**B4.4** passed its finite timing/checkpoint engineering sentinel with all
76 queries and 100 terminal states independently audited and numerical/failure
identity preserved; see [the engineering report](../validation/b4_4_engineering.md).
The next slice is **B4.5**, a separately frozen sensitivity-weighted terminal-design
generalist intervention with fixed specialist and fresh development validation.
Final evaluation remains sealed until the complete new B4 Gate and independent
confirmation pass; uniform remains the default.

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

**B4.1 fitting Gate passed:** The [fixed fitting boundary](../b3_training_contract.md)
completed all twelve preregistered CPU fits from clean merged source
`428c96fd718a78496bcfafcc85a3d82401925ab4`. Complete independent label,
checkpoint/history and equal-case selection audits passed for every seed.
All 1,902 attempted epochs and 24 artifacts were retained, with zero failed
fits or production restarts. The final fitting-stage charge was 3,870.204341
seconds and peak RSS 437,878,784 bytes, within the frozen 7,200-second and
4-GiB caps; see the [B4.1 report](../validation/b4_1_fixed_fitting.md).
That fitting slice opened no screening query or final artifact.
The subsequent **B4.2** screen is recorded below.

**B4.2 complete screen; Gate B4 failed:** The
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
**B4.3 diagnostic acceptance passed:** The
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

**B4.4 engineering acceptance passed:** its separately frozen 76-query,
two-arm/two-round sentinel retained all 100 candidate/fallback states and passed
independent byte, numerical, chain and cost audits. Every numerical outcome and
known failed status was identical to B4.2. Compact progress reduced inclusive
callback wall by 99.8243% and complete-query wall by 25.3881% in the deliberate
checkpoint-stress fixture. Final charge was 2,406.653985 seconds and peak RSS
705,953,792 bytes, within 7,200 seconds / 2 GiB. Actual process-crash and both
publication windows passed synthetic tests. See
[the engineering report](../validation/b4_4_engineering.md). This establishes
no learned acceleration and does not retime the failed B4.2 experiment.
**B4.5** is next: separately freeze and implement one bounded sensitivity-weighted
terminal-design generalist intervention with fixed specialist, unchanged numerical
quality limits and fresh development validation under a new contract. This is an
untested hypothesis. Require independent confirmation and the complete new B4 Gate
before B5.
No retiming, new fit or selection-rule change is allowed under the failed
original contract. Preserve every result and keep final evidence sealed.

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
- Never commit datasets, checkpoints, databases, logs, screenshots, or run results.
- Close each stage with a validation report, including failed gates.
- Update README, resume, or title claims only after their supporting gate actually passes.

## 6. Recommended sequence

The user-defined ML delivery condition changes the order, not PR size or gates:

1. **A1.1–A1.4 and Gate A1:** completed as separate slices.
2. **M3 v1 planning gate:** completed, then superseded before fitting or final
   evidence because it does not address the full delivery objective.
3. **B0 development-only feasibility probe and roadmap correction:** completed.
4. **B1 numerical convergence and learned-quality root cause:** completed without
   new training, final evidence, or solver changes.
5. **A3 baseline-affecting solver performance:** completed with paired
   cross-platform evidence and a frozen larger-mesh uniform ordering policy.
6. **B2 workload/mesh headroom pilot:** completed; Gate B2 failed. Conditional
   oracle headroom did not overcome large-reference nonconvergence or the
   unchanged learned panel's charged time gap.
7. **B2.1 large-mesh/high-volume convergence intervention:** completed; all
   twelve uniform references passed under a separately versioned opt-in rule,
   but the unchanged learned panel remained slower after full charges.
8. **B2.2 bounded learned-prototype plan and data-feasibility gate:** completed;
   the control/candidate and 522-case development boundary are fixed, but the
   61-case sentinel failed 53/61 and fitting did not begin.
9. **B2.3 bounded data-feasibility repair:** completed; one versioned
   240-update budget passed all 61 fixed sentinel cases while preserving the
   previous 53 accepted outputs.
10. **B2.4 development labels:** completed; all 522 versioned labels and their
    artifact, numerical, population, and resource audits passed.
11. **B2.5 prototype fitting and screen:** completed; the six fixed fits and
    all 54 validation cases were audited, but the learned-prototype Gate
    failed after full fallback charges.
12. **B2.6 intermediate-trajectory target:** completed; 480 targets, three
    fits, and the full new 12-case screen were audited, but no new seed met
    the fallback-inclusive two-scale feasibility Gate.
13. **B2.7 global-load representation repair:** completed; the complete
    three-fit, 12-case screen improved seeds 17/29 over B2.6 but failed the
    two-scale and direction-wise feasibility Gate.
14. **B2.8 quality/solver-basin intervention:** completed; the fixed y-load
    midpoint start changed actual trajectories but did not reduce failures
    or pass the two-scale/direction-wise charged-speed Gate on 12 new cases.
15. **B2.9 vector point-load conditioning:** completed; two seeds had
    zero fallbacks and passed both scale-mean bounds, but both exceeded the
    large-y direction bound, so the fixed feasibility Gate failed.
16. **B2.10 sensitivity-weighted trajectory objective:** completed 480 weights
    and three fits; the frozen screen stopped at 9/12 cases because a
    mandatory uniform reference failed at 240 updates. Its Gate failed.
17. **B2.11 versioned reference-budget repair:** completed; twelve old/new
    sentinel pairs and twelve fresh references passed, but neither fixed
    model panel passed the full 132-outcome charged-speed Gate.
18. **B2.12 spatial-context CNN:** completed; 12 fresh references, three
    fits, and 132 outcomes passed their completion/resource audits, but
    no new seed met the two-scale/direction-wise learned Gate.
19. **B2.13 workload-aware routing/rejection policy:** completed; twelve
    fresh references and 144 fully charged outcomes passed the small
    development Gate, but the router did not beat context 43 on this cohort.
20. **B2.14 larger development confirmation:** completed; 24/24 fresh
    references and 192/192 outcomes passed completeness/quality/resource
    audits, but no policy passed the fixed scale/direction Gate.
21. **B2.15 position-aware routing/reliability intervention:** completed;
    24/24 references and 192/192 outcomes passed completeness and quality
    audits, but the new route failed its direction and improvement Gate.
22. **B2.16 method-class reassessment:** completed; 48 exposed cases and
    384 outcomes passed independent read-only audits. Perfect selection
    has headroom, but coarse-cell transfer failed in both directions;
    one bounded online early-reliability probe is warranted.
23. **B2.17 early-reliability probe:** completed; the four-case exposed
    sentinel met cost caps but missed three terminal failures and stopped
    before fresh-case execution.
24. **B2.18 solver-anchored new-mechanism assessment:** completed; the
    four exposed cases retained three terminal failures after a paid
    physical-state anchor, so no fresh case was opened.
25. **B2.19 learning-side quality-basin repair:** completed; a paid
    uniform-state sensitivity input improved held-out density MSE but
    failed the 12-case, 84-outcome development Gate.
26. **B2.20 operational checkpoint selection:** completed; three fits,
    12-case operational selection, and 24-case independent screen were
    complete, but no selected seed passed, and 0/6 high-volume large-y
    selected attempts passed terminal quality.
27. **B2.21 terminal-design learning target:** completed; 24 new
    references, twelve validation targets, three fits, and 168 screen
    outcomes passed completeness audits, but the learned Gate failed
    and 0/6 high-volume large-y new attempts passed terminal quality.
28. **B2.22 high-volume y-direction specialist:** completed; 24 references,
    three fits, and 168 fully charged screen outcomes passed completeness,
    but the route failed its 4/6 high-y quality and two-scale speed Gates.
29. **B2.23 large-y load-position coverage and label feasibility:**
    completed; all 30 new uniform labels and independent numerical,
    identity, resource, and artifact audits passed the frozen data Gate.
30. **B2.24 expanded-label training intervention:** completed; the
    24-reference, three-fit, 168-outcome screen repaired 0/6 to 6/6
    matched high-volume large-y quality but failed the full speed Gate.
31. **B2.25 residual large-grid quality and cost diagnosis:** completed;
    all B2.24 fixed outcomes were checksum-bound and audited without
    fitting or tuning. The frozen speed-only bounds select one joint
    generalist mechanism for a fresh screen; no acceleration claim follows.
32. **B2.26 joint non-specialist quality and refinement intervention:**
    completed; 24 references, three weighted terminal fits, and 240
    matched outcomes passed completeness/resource checks. No seed met
    the large-scale speed Gate despite one improved seed; B3 stays closed.
33. **B2.27 middle-volume position coverage and label feasibility:**
    completed; all 60 disjoint large-grid y/z labels passed independent
    numerical, artifact, identity, and resource checks, with no fit or
    learned screen.
34. **B2.28 middle-volume training intervention:** completed; 24 fresh
    references, three fits, twenty diagnostics, and 168 charged outcomes.
    All three expanded seeds passed the bounded development Gate with
    zero failures; larger independent confirmation remains required.
35. **B2.29 larger independent development confirmation:** completed;
    48 references and 432 charged outcomes passed complete audit.
    Expanded seeds 17 and 43 passed the frozen Gate; seed 29 failed.
    Both expanded large-y quality cells passed 9/9.
36. **B3 new versioned ML contract and data gate:** **B3.1** completed
    the contract and metadata exposure audit. **B3.2** completed the
    frozen catalog, memberships, fingerprints, and access guards with
    exact hash and byte comparisons. **B3.3** completed guarded versioned
    label/reference materialization and charged recovery/audits, tested with
    synthetic states. **B3.4** then passed the complete production data
    Gate: 560/560 labels and 48/48 screening references, zero failures,
    complete independent quality/provenance/stratum audits and resources
    within the frozen caps. No model fit or final artifact access.
37. **A2.1–A2.2 process isolation** before expensive final ML evaluation, in
    separate PRs. A2.1 worker protocol and A2.2 durable ownership/recovery
    are complete. Gate A2 remains open pending A2.3–A2.4.
38. **B4 fitting, reliability, and freeze** only after B3 passes. **B4.1**
    completed twelve fixed fits and independent artifact/selection/resource
    audits; **B4.2** completed all 720 fixed screen outcomes but failed Gate B4.
    **B4.3** completed its read-only diagnosis. **B4.4** passed the frozen
    timing/checkpoint engineering Gate with 76/76 numerical outcomes and
    100/100 terminal audits. **B4.5** next freezes and implements a bounded
    sensitivity-weighted terminal-design generalist intervention with fixed
    specialist and fresh development evidence. **B5 final evaluation** only
    after the complete new B4 Gate and independent confirmation pass.
39. **A2.3–A2.4 and A4** as platform requirements and resources justify them.

After each completed independent slice, report its gate, evidence, limitations,
and the next slice, then wait for a new user instruction before starting it.

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
