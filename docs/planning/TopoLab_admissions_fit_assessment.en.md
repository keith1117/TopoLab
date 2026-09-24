# TopoLab: Graduate Admissions Fit Assessment

English counterpart of [the Chinese assessment](./TopoLab_admissions_fit_assessment.md).
Related documents: [Development timeline and resources](./TopoLab_development_timeline_and_resources.en.md) · [Numerical Core reimplementation strategy](./TopoLab_reimplementation_strategy.en.md)

## Project positioning

**TopoLab — Reproducible 3D Topology Optimization Platform**

The project has three layers:

1. **Numerical Core:** Correct and validate the 3D SIMP/finite-element solver; test sensitivities, load conservation, and volume fractions; and replace dense global matrices with sparse assembly.
2. **Software Platform:** Use FastAPI, background workers, a database, and a 3D frontend to support asynchronous runs, progress, cancellation, failure recovery, experiment versioning, and isolation between concurrent jobs.
3. **ML Acceleration:** Generate cases with different supports, loads, and volume fractions; train a density-field warm-start model; compare it with uniform, physics-based, and nearest-neighbor baselines; and test unseen loading conditions.

## Initial status and claims boundary (2026-09-17)

- The new [`keith1117/TopoLab`](https://github.com/keith1117/TopoLab) repository had been created but was still empty: no commits, README, license, or code. This is a historical starting point, not the current repository state.
- Every high fit score below describes the direction **if fully implemented**. It is neither a rating of the project at that date nor a prediction of admission probability.
- Do not say `validated` before Numerical Core validation, `scalable` before multiscale performance tests, or `accelerated` before a same-quality ML versus baseline comparison.
- If learned warm starts do not consistently reduce total runtime, use **TopoLab — Reproducible 3D Topology Optimization Platform** as the title and present the ML work as an evaluation or negative result.

## v1.0.0 outcome (2026-09-24)

- The numerical core, SIMP optimizer, platform contracts, and M0 data foundation passed their gates, with validation reports in the repository.
- A four-scale sparse benchmark was completed, but its evidence does not justify a broad `scalable` claim for the entire platform.
- The fixed five-seed M1 comparison was inconclusive on ID-test; on OOD it was slower than uniform initialization, with 25% learned failure/fallback. M2 failed its pre-registered data gate because 10 of 756 cases did not converge, so M2 fitting never started.
- The final title follows the stopping rule: **TopoLab — Reproducible 3D Topology Optimization Platform**. The ML contribution is a reproducible experiment, a negative result, and a strict stopping decision, not learned acceleration.
- v1.0.0 is locally runnable, reproducible research software. It has no distributed worker, authentication, containerized delivery, or hosted online demo.

The project spans computational mechanics, structural topology optimization, finite elements, numerical optimization, scientific computing, Scientific ML / AI for Engineering, and software systems for long-running computation. Its value for CS, SWE, AI, ML, and Information Systems comes from verifiable algorithmic, systems, and experimental contributions rather than the mechanical-engineering subject alone.

## Admissions fit if fully implemented

These ratings assume that all three layers have been completed with numerical validation, systems tests, performance measurements, ML baseline comparisons, and OOD tests. They compare narrative coverage; they should not appear in a resume, statement of purpose, or project README.

| Program area | Fit | Main support |
|---|---:|---|
| Computer Science | **9/10** | Numerical algorithms, sparse matrices, performance engineering, ML, and backend systems form a complete technical chain |
| Software Engineering / SDE | **9–9.5/10** | APIs, asynchronous work, concurrency isolation, recovery, automated tests, CI/CD, containers, and observability |
| Machine Learning | **8.5–9/10** | Data generation, warm-start models, baselines, ablations, OOD generalization, and physical constraints |
| Artificial Intelligence | **8–8.5/10** | AI for Science and learned assistance to a conventional physics solver |
| Information Systems | **8–8.5/10** | Computational workflows, experiment data, versions, input validation, and result management |
| Scientific Computing | **9.5–10/10** | Strong alignment with finite elements, numerical optimization, sparse solving, profiling, and scientific software |
| Computational Engineering / AI for Science | **9.5–10/10** | Close connection between a physics solver and an ML acceleration hypothesis |
| Data Science | **7.5–8/10** | Data generation and experimental analysis, though this is not a typical business-data project |

## Conditions for high ratings

### Minimum evidence package

A complete flagship version should provide in its public repository:

- A reproducible lockfile, installation instructions, and an end-to-end run command;
- `PROVENANCE.md` with the upstream commit, absent license, references, and independent-implementation boundary;
- Numerical validation reports with tolerances, failures, and raw results;
- Sparse/dense timing and peak-memory benchmarks over three mesh scales;
- API/worker state-machine and concurrency-isolation tests;
- Fixed splits, baselines, OOD, ablations, and multiseed ML results;
- Scripts that reproduce key tables and figures from a clean environment, not just screenshots; and
- An architecture diagram, limits, a demo video, and a clear account of individual contributions.

Every number in admissions materials should trace to repository configuration, logs, or a generating script.

### Numerical Core

- Correct load direction, total-load accounting, and final compliance recording.
- Validate sensitivity with finite differences.
- Check volume fraction, load conservation, and final-state compliance.
- Compare runtime, memory, and feasible mesh size between dense and sparse implementations.
- Re-solve the final density to avoid misaligning results with history.

Merely getting the existing code to run does not create a strong Numerical Core contribution.

### Software Platform

- Execute long-running optimization in background workers.
- Expose run IDs, progress, cancellation, failure, and recovery states.
- Use explicit input schemas and reject invalid boundary conditions and rigid-body modes.
- Isolate parameters, states, and outputs across concurrent jobs.
- Persist experiment parameters, code versions, logs, and results in a database or structured store.
- Add containers, automated tests, CI, and deployment instructions.
- Ideally provide an online demo or a complete recorded demonstration.

A FastAPI page that only starts a Python script does not demonstrate the full software-engineering scope.

### ML Acceleration

- Define clear training, validation, and test splits.
- Split by complete physical case so iterations from one optimization trajectory cannot leak across sets.
- Compare against uniform, physics-based, and nearest-neighbor baselines.
- Test unseen load locations, directions, support patterns, or volume fractions.
- Report final compliance, volume fraction, iterations, end-to-end runtime, and failures.
- Charge model inference to total runtime.
- Fall back to standard SIMP initialization when a prediction fails.

Only a reduction in total time under the same physical quality constraints justifies an ML-acceleration claim.

## If ML provides no useful improvement

A strong numerical core and software platform retain substantial value even if ML does not consistently beat the baselines:

| Program area | Fit |
|---|---:|
| Computer Science | **8.5/10** |
| Software Engineering / SDE | **9–9.5/10** |
| Artificial Intelligence / Machine Learning | **6.5–7/10** |
| Information Systems | **8/10** |
| Scientific Computing | **9/10** |

A failed ML experiment does not invalidate the whole project. An honest failure analysis, reliable 3D solver, and complete platform can still form a strong CS/SWE project; stronger AI/ML positioning requires rigorous, useful model results.

Set a stopping rule in advance: after one lightweight 3D CNN, a bounded hyperparameter budget, and at least three seeds, freeze the outcome and analyze failure if held-out cases do not reduce end-to-end time within the same compliance and volume tolerances. Do not conduct an unbounded model search.

## If the work is only superficial integration

If the project merely wraps the original script in FastAPI and adds a neural network without baselines or evaluation, estimated fit falls to:

| Program area | Fit |
|---|---:|
| Computer Science | **about 7/10** |
| Software Engineering / SDE | **6.5–7/10** |
| Artificial Intelligence / Machine Learning | **5–6/10** |
| Information Systems | **about 6.5/10** |

The substantive contribution is correctness, controls, quantitative performance, and system completeness, not the number of technologies used.

## Resume emphasis by program

### CS / SWE / SDE

Recommended order:

1. Sparse solving, numerical validation, and measured performance.
2. Asynchronous jobs, concurrency isolation, recovery, and experiment versioning.
3. Any demonstrated ML warm-start benefit.

### AI / ML

Recommended order:

1. Dataset construction, warm-start modeling, and physical-case splits.
2. Baselines, OOD tests, ablations, and failure analysis.
3. Integration with standard SIMP and reliable fallback.

### Information Systems

Recommended order:

1. Computational workflows and user-input validation.
2. Traceability of experiment data, code versions, and results.
3. Asynchronous execution, state management, result presentation, and recovery.

## Final project portfolio

At full scope, TopoLab can stand alongside Airline AgentOps as a flagship project:

- **Airline AgentOps:** General backend, Agent/RAG, reliability, and systems design.
- **TopoLab:** Numerical computing, scientific software, performance engineering, ML experiments, and interdisciplinary problem solving.
- **Hack3D MNN VIP:** Research experience adapting PyTorch/VAE code, extending target fields, and applying a mechanical-design background.

Together these projects cover CS, SWE/SDE, AI, ML, and Information Systems while preserving a distinctive Scientific Computing and AI for Science profile.

## Application-ready stages

| State | Defensible positioning | Claims to avoid |
|---|---|---|
| Numerical Core unvalidated | Work in progress / independent reimplementation | validated, scalable, production-ready |
| Core validated | Validated 3D SIMP engine | ML-accelerated, full-stack platform |
| Platform and performance evaluated | Reproducible topology-optimization platform | learned acceleration unless experimentally established |
| ML evaluation positive | Platform with learned warm starts | Generalization beyond tested distributions |
| ML negative or unstable | Platform with rigorous warm-start evaluation | accelerated optimization |

Use these boundaries consistently in the resume, GitHub README, statement of purpose, and interviews so the project title never outruns the evidence.
