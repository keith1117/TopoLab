# TopoLab v2 Development Roadmap

Status: **active v2 flagship delivery plan; Gates A1 and A3 passed; B2.2's
120-update data gate failed, B2.3's versioned 240-update sentinel passed,
B2.4's complete 522-label development data Gate passed, and B2.5–B2.8's
fixed learned-prototype feasibility Gates failed;
ML acceleration is a required delivery gate, not an optional enhancement.**
The released `v1.0.0` and
its negative M1/M2 conclusions remain historical evidence.

Prepared: 2026-09-24
Revised: 2026-09-26

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
slice is **B2.9**: freeze and execute one learning-side quality and
load-position transfer correction, then test it on fresh disjoint development
cases with full charges. Do not enter B3 before a development prototype passes.

### B3: New versioned contract, exposure ledger, and data gate

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
15. **B2.9 learning-side quality and transfer correction:** next independent
    slice; freeze one model-side correction and test fresh disjoint cases.
16. **B3 new versioned ML contract and data gate:** after a successful
    development prototype, freeze the new final boundary, then implement and
    audit data in independently reviewable slices.
17. **A2.1–A2.2 process isolation** before expensive final ML evaluation, in
    separate PRs.
18. **B4 fitting, reliability, and freeze** only after B3 passes; **B5 final
    evaluation** only after B4 passes.
19. **A2.3–A2.4 and A4** as platform requirements and resources justify them.

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
