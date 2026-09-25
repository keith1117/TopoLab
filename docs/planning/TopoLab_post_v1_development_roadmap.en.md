# TopoLab v1.x Development Roadmap

English counterpart of [the Chinese roadmap](./TopoLab_post_v1_development_roadmap.md).

Status: **v1.x plan, starting from the released `v1.0.0`; Gate A1 passed on 2026-09-25**

Prepared: 2026-09-24

Related documents:

- [Graduate admissions fit assessment](./TopoLab_admissions_fit_assessment.en.md)
- [Development timeline and resources](./TopoLab_development_timeline_and_resources.en.md)
- [v1.0.0 release validation](../validation/v1_release_validation.md)
- [M1 held-out evaluation](../validation/m1_held_out_evaluation.md)
- [M2 materialization outcome](../validation/m2_catalog_materialization.md)
- [A1.1 canonical demo validation](../validation/a1_1_canonical_demo.md)
- [A1.4 clean Linux validation and Gate A1 decision](../validation/a1_4_clean_linux_smoke.md)

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

## 2. Goals and priorities

Two independent tracks:

- **Track A: Productization and scientific software engineering.** Improve reproducibility, demonstrations, run isolation, recovery, and performance evidence for CS/SWE/Scientific Computing applications.
- **Track B: M3 learned warm starts.** Within a bounded pre-registered budget, address data availability and generalization and seek a new positive ML result while keeping failures auditable.

| Priority | Stage | Rationale |
|---|---|---|
| P0 | A1 reproducible demo | Low cost and high presentation value without new experimental results |
| P0 | M3.0 diagnosis and pre-registration | Freeze scope and compute budget before more training |
| P1 | A2 process isolation and recovery | Address the clearest platform gap |
| P1 | M3.1 data gate | Decide whether M3 may proceed to fitting |
| P1 | A3 performance/cross-environment evidence | Expand evidence without a broad scalability claim |
| P2 | M3.2–M3.4 fitting and final evaluation | Only after the data gate passes |
| P2 | A4 controlled deployment and feedback | Only after isolation and resource limits |

Rough effective development effort for scheduling, not a commitment; production generation and evaluation wait time are additional:

| Stage | Estimated effort |
|---|---:|
| A1 reproducible demo | 4–7 days |
| A2 process isolation and recovery | 8–15 days |
| A3 performance engineering | 4–8 days |
| A4 controlled deployment | 3–7 days |
| M3.0 diagnosis and pre-registration | 2–4 days |
| M3.1 data gate | 3–6 days plus materialization |
| M3.2–M3.3 fitting and freeze | 7–14 days plus training |
| M3.4 final evaluation | 2–4 days plus evaluation |

The tracks may alternate, but each PR handles one verifiable behavior. Do not mix platform restructuring, numerical-semantic changes, data generation, and model training in one slice.

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

Suggested milestone: `v1.2.0`. Consider `v2.0.0` only if the public API becomes incompatible; do not increment the major version merely for perceived importance.

### A3: Performance engineering and wider evidence

Profile first, optimize one bounded bottleneck, and expand benchmark environments and scales.

1. Record assembly, factorization/solve, filter, OC, and serialization phases.
2. Select one dominant bottleneck, such as repeated sparse-structure construction or linear solving.
3. Test numerical equivalence and provide a fallback for the candidate optimization.
4. Repeat a fixed mesh ladder on Apple arm64 and Linux x86-64.
5. Report cold/repeated time, peak RSS, DOFs, nonzeros, and failure boundaries.

**Gate A3:** Compare before/after on the same problem, environment, thread count, and protocol; preserve frozen small-mesh tolerances; obtain a stable gain on the target metric without obvious regression at other scales. Use `faster` or `lower-memory` only within measured scope, and avoid a broad `scalable` claim without larger cross-platform evidence.

Suggested milestone: `v1.3.0`.

### A4: Controlled deployment and external feedback

After A2 isolation and limits, offer a safe, low-cost public demonstration or a complete recording instead.

1. Threat-model CPU/memory exhaustion, oversized inputs, database growth, and abuse.
2. Expose only preset mesh ranges and a fixed concurrency budget.
3. Add health checks, structured logs, error-rate and run-time metrics.
4. Retain local Compose plus a recording if cost or safety prevents hosting.
5. Collect a little genuine trial feedback, separating defects from feature wishes.

**Gate A4:** Deployment cannot bypass Numerical Core input validation or limits; internal paths, device identifiers, databases, and external experiment artifacts are not exposed; shutdown, cleanup, and cost bounds are clear; README distinguishes local demo, hosted demo, and production service.

## 4. Track B: M3 learned warm starts

### M3 evidence boundary

M3 is a new experiment, not a rerun or retrospective “fix” of M2:

- M1's six ID-test and 80 OOD cases have been exposed and may be used only for diagnosis.
- M2 materialization outcomes, failure patterns, and inspected statistics are development information.
- Successful M2 labels may be considered for development train/validation only after a new contract records their provenance. This does not turn M2 into a passed gate.
- M3 needs new, physically disjoint final ID-test and OOD sets.
- Final labels cannot inform fitting, selection, reliability thresholds, or stopping.
- M1/M2 artifacts and reports remain immutable.

### M3.0: Failure diagnosis and pre-registration

Before writing new model code or training, determine whether failure arises from data, representation, objective, optimization budget, or the warm-start approach itself.

Allowed diagnosis: stratify exposed M1/M2 cases by direction, volume, load location, and convergence; examine projection before/after, initial compliance, final quality failures, and refinement iterations; study the ten M2 non-convergent cases without silently turning them into successful labels; estimate an ideal warm start's speedup ceiling; and use a train/validation-only pilot for data loading and loss computation without opening new final evidence.

Pre-registration must freeze one main question and success metric; case schema/catalog/split/exposure ledger/artifact version; label success/failure policy and maximum solver budget; at most two model candidates, one main loss, and one defined ablation; seeds, epochs, early stopping, selection, and hardware budget; a finite set of reliability/fallback strategies; and the final ID/OOD gates and one-time opening order.

**Gate M3.0:** The diagnosis yields one falsifiable main hypothesis and a bounded budget. If no proposed intervention plausibly improves end-to-end time, stop M3 and continue Track A.

### M3.1: Data availability and a new evidence boundary

Establish the data gate before fitting:

1. Build an exposure ledger of every physical case seen in M0/M1/M2.
2. Freeze new train/validation/final-ID/OOD generation and a content-derived catalog ID.
3. Specify solver termination, failure retention, and usable-label policy in the contract.
4. Run a read-only production plan before authorized materialization outside the repository.
5. Audit manifest, index, checksums, split counts, failure strata, and label quality.
6. Implement or run fitting only after the data gate passes.

M3 need not demand universal label success, but it must choose one rule before seeing outcomes:

- **Complete-label gate:** Every train/validation case converges; or
- **Pre-registered availability gate:** Retain each failure, apply a fixed split-independent rule for usable successful labels, and require minimum coverage by stratum.

Do not raise iterations, remove cases, change splits, or issue a second catalog under the same name after observing particular failures.

**Gate M3.1:** All artifacts pass audit; train/validation coverage meets pre-registration; final cases remain unread by model-development code. Otherwise stop before training.

### M3.2: Bounded model improvement

Test one main intervention rather than an unbounded architecture search:

1. **Control:** Retrain the small M1 CNN on M3 training data to isolate the benefit of more data.
2. **Primary candidate:** Choose one change from M3.0 diagnosis, such as direction/geometry-aware representation, a solution-quality-aligned objective, or a small multiscale network.
3. **One ablation:** Remove only the candidate's core new component.
4. Use the same fixed seeds, data boundary, and selection rule for each candidate.
5. Record training cost, parameter count, peak memory, and checkpoints.

Do not combine large models, generative models, reinforcement learning, a surrogate solver, and GPU FEM in M3. If the primary candidate cannot improve both quality reliability and the prospect of end-to-end time on validation, do not open final test.

**Gate M3.2:** Selection uses only train/validation. Retain every seed; no apparent validation gain may depend on deleting seeds or cases or ignoring fallback.

### M3.3: Reliability strategy and freeze

Reduce poor warm starts without hiding cost. Pre-register a finite list of reliability scores and thresholds and choose on validation only. Reject-to-uniform charges inference, decision, and full uniform cost. Accepted failures remain visible and charge a fresh uniform fallback. Freeze model, checkpoint, threshold, statistics code, and runtime before final evaluation.

**Gate M3.3:** Rebuild frozen artifacts from a clean revision and locked environment. No final case may undergo a learned comparison before the freeze.

### M3.4: One-time final evaluation

Answer whether learned warm starts help on fresh untouched evidence. Report uniform, physics heuristic, training-only nearest neighbor, M1 control, and M3 candidate; setup/inference/projection/refinement/fallback/end-to-end times; compliance, volume error, iterations, failures, rejections, and fallback; physical-case-cluster bootstrap intervals; and ID and OOD separately.

Suggested conservative claim gate carried from M2:

- Upper 95% confidence limit for the ID mean candidate/uniform time ratio `< 1.0`;
- Zero quality failures/fallbacks among accepted learned attempts;
- Every operational result meets convergence, volume, and compliance quality bounds; and
- No post-observation removal of cases, seeds, methods, or timing phases.

Use `OOD-safe` only if OOD failures are zero and the upper 95% limit for the OOD mean time ratio is `<= 1.05`. Otherwise publish the negative result, keep uniform as default, and do not start an unregistered M3.5 search for a favorable answer.

## 5. Version, branch, and validation rules

- Each slice starts from current `main`, has a short-lived branch, and merges via PR and CI.
- Version new platform contracts, checkpoints, and ML artifacts explicitly.
- Write a failing test or independent acceptance case before changing numerical behavior.
- Commit a production contract/runner first; run a read-only plan from its clean merged revision before production execution.
- Never commit datasets, checkpoints, databases, logs, screenshots, or run results.
- Close each stage with a validation report, including failed gates.
- Update README, resume, or title claims only after their supporting gate actually passes.

## 6. Recommended sequence

Based on admissions value, risk, and dependencies:

1. **A1.1 canonical demo and end-to-end smoke**;
2. **A1.2 Docker/Compose local stack**;
3. **A1.3 architecture diagram and demo video**;
4. **A1.4 clean Linux smoke and Gate A1 decision**;
5. **M3.0 diagnosis and pre-registration**;
6. **A2.1–A2.2 separate-process worker and durable ownership**;
7. **M3.1 new catalog, exposure ledger, and data gate**;
8. **M3.2–M3.4**, only if M3.1 passes; and
9. **A2.3, A3, A4** when profiling and deployment needs justify them.

**Gate A1 and Gate M3.0 are complete:** The canonical case, local stack,
architecture and demo, and clean Linux smoke passed their separate validation
slices. Exposed-failure diagnosis and the bounded M3 pre-registration are recorded
in `docs/validation/m3_preregistration.md` and `docs/m3_preregistration.md`.
No new data generation or model fitting occurred in M3.0. The next independent
slice is **A2.1**, limited to the separate-process worker protocol.

## 7. Stage completion evidence

Measure later work by evidence rather than feature count:

| Goal | Completion evidence |
|---|---|
| Easier reproduction | One clean-environment path, fixed demo, smoke, run report |
| More reliable platform | Crash/restart/cancel/concurrency/duplicate-claim tests and an explicit state machine |
| Stronger performance | Phased profile, cross-environment benchmark, numerical equivalence |
| More credible ML | New exposure boundary, pre-registered budget, one-time final evaluation |
| Better application presentation | Traceable resume numbers; demos and README within claims boundaries |

Even if M3 fails, completed A1–A3 would strengthen the CS/SWE/Scientific Computing project. A positive ML result is an added benefit, not a single point of failure for the development program.
