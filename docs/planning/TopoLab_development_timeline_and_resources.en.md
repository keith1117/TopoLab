# TopoLab Development Timeline and Resource Assessment

English counterpart of [the Chinese assessment](./TopoLab_development_timeline_and_resources.md).
Related documents: [Admissions fit](./TopoLab_admissions_fit_assessment.en.md) · [Numerical Core reimplementation strategy](./TopoLab_reimplementation_strategy.en.md)

Current v1.x scheduling override: this document retains the original estimates
and `v1.0.0` closeout as historical planning evidence. The active
[v1.x roadmap](./TopoLab_post_v1_development_roadmap.en.md) makes reproducible
learned end-to-end acceleration a required full-flagship delivery gate. Its
research duration is uncertain and cannot be guaranteed by the 10–14-week
historical estimate.

## Target project

**TopoLab — Reproducible 3D Topology Optimization Platform**

This report estimates the schedule, stages, computing resources, and physical-world requirements for turning the initial Hack3D/3D SIMP code base into a graduate-application-quality project with substantial development assistance. Estimates are planning assumptions, not completion promises.

## Starting point (2026-09-17)

- [`keith1117/TopoLab`](https://github.com/keith1117/TopoLab) had completed G0 repository preparation: README, MIT license, provenance, locked environment, minimal package, tests, and CI.
- The upstream reference was fixed at `Jiangce2017/3D_SIMP_Topology_Optimization_Numpy@584cb8ee570d375f8ba9b10272020c5c2daa8c30`.
- The upstream repository declared no open-source license. It was to be used only as a behavioral and audit baseline, with no source copied or redistributed. The new core would be independently derived from standard SIMP/Hex8 references and documented in `PROVENANCE.md`.
- Local upstream code, figures, and an earlier audit existed, but none counted as the new TopoLab implementation.

### G0 execution record (2026-09-17)

- [x] Clone the repository and retain its initial README commit.
- [x] Choose MIT for original TopoLab code and documentation.
- [x] Add README, `PROVENANCE.md`, `.gitignore`, `pyproject.toml`, and contribution rules.
- [x] Lock Python 3.12, NumPy, SciPy, Pydantic, pytest, Ruff, and mypy.
- [x] Add GitHub Actions CI and a package-import smoke test.
- [x] Record non-sensitive hardware information and numerical conventions.
- [x] Move the three planning documents into `docs/planning/`.
- [x] Push G0 and confirm GitHub Actions run `35275304334` passed.

G0 established development and audit foundations, not a Numerical Core implementation.

## v1.0.0 closeout (2026-09-24)

Gates N1, N2, P1, and M0 passed. The fixed M1 held-out experiment did not establish learned acceleration. The pre-registered M2 follow-up failed its data gate because ten deterministic cases did not converge, so the learned-model expansion stopped under its rule. v1.0.0 uses uniform initialization by default and ships the validated numerical core, reproducible sparse benchmark, local API/SQLite/React workspace, and positive and negative experiment records. It does not include a hosted online demo, distributed worker, authentication, or containerized delivery.

## Git branching and release strategy

TopoLab uses lightweight **GitHub Flow**. A solo project in rapid iteration does not need long-lived `develop`, `release/*`, or `hotfix/*` branches.

### Branch rules

- Keep `main` runnable and tested as the only long-lived branch; prohibit force pushes.
- Create a short-lived branch from current `main` for each reviewable change, ideally completing it within half a day to three days.
- Use descriptive `feat/`, `fix/`, `docs/`, `test/`, `bench/`, or `experiment/` prefixes. Branch names describe deliverables, not people.
- Keep one clear slice per branch; do not mix numerical, platform, and ML work in one PR.
- Merge through PRs, even for solo work, to retain design notes, CI, and review history. Squash merge after all checks pass and delete the remote branch.
- Prefer required checks, an up-to-date base, and no force pushes on `main`. A required reviewer can wait for stable collaborators.

### Planned short-lived branches

| Branch | Scope |
|---|---|
| `feat/n1-hex8-mesh` | Structured Hex8 mesh, node/element/DOF conventions, tests |
| `feat/n1-element-stiffness` | Material matrix, Hex8 stiffness, local numerical checks |
| `feat/n1-sparse-assembly` | COO/CSR assembly, boundary conditions, linear solve |
| `feat/n1-boundary-load-models` | Supports, point/face loads, load-conservation tests |
| `feat/n2-sensitivity` | Compliance, analytical sensitivity, finite differences |
| `feat/n2-simp-optimizer` | Filter, OC, full SIMP loop |
| `feat/p1-api-jobs` | API, job states, run isolation after N2 |
| `feat/platform-run-persistence` | SQLite, terminal recovery, interrupted-process semantics |
| `feat/platform-run-history` | UTC timestamps, cursor pagination, run-history API |
| `feat/frontend-run-history` | React/TypeScript history, status, details |
| `feat/frontend-density-visualization` | Interactive final physical-density 3D view |
| `feat/frontend-run-submission` | Problem form, submission, terminal refresh |
| `feat/frontend-convergence-visualization` | Same-state compliance, volume, density-change charts |
| `feat/frontend-run-cancellation` | Cooperative cancellation control and polling |
| `bench/sparse-solver-performance` | Four-scale sparse time/memory and dense-storage comparison |
| `experiment/m1-warm-start-cnn` | Learned warm-start comparison after M0 |

This was an execution order, not a list of branches to create in advance. Start the next branch only after the prior interface and tests stabilize; use a new `fix/*` branch from current `main` for independent defects.

### Milestone versions

Use annotated tags rather than release branches:

- `v0.1.0`: Gate N1 passed;
- `v0.2.0`: Gate N2 passed;
- `v0.3.0`: Gate P1 passed;
- `v1.0.0`: local software, experiments, validation evidence, and documentation met the release standard.

After P1, SQLite persistence, restart recovery, stable pagination, run history and details, 3D density visualization, problem submission, convergence charts, and cooperative cancellation were completed. A four-scale sparse benchmark was also documented in `docs/validation/sparse_solver_benchmark.md`.

M0 froze the case schema, generator, split, baselines, typed case identity, encoding, filtered-volume projection, typed manifest, single-case label validation, content-addressed atomic artifacts, recoverable index, controlled executor, and a bounded 160-case production catalog. The first materialization yielded 156 successful labels and four correctly rejected OOD non-convergence cases under a 100-iteration budget. A separately versioned 120-iteration catalog v2 retained the cases and `0.01` convergence tolerance, then produced 160 valid labels with no failures. Gate M0 passed; the fixed uniform, physics-based, and training-only nearest-neighbor baseline runner was implemented.

M1 froze a lightweight model, loss, budget, checkpoint selection, and a train/validation-only adapter. Deterministic five-seed fitting, epoch history, content-addressed checkpoints, and a clean-revision production entry point were built. Production training completed and was audited without opening test/OOD labels (`docs/validation/m1_training.md`). The learned inference, volume projection, shared refinement/quality audit, timing, and fully charged uniform fallback were implemented. The held-out runner evaluated all six ID-test and 80 OOD cases and froze the evidence in `docs/validation/m1_held_out_evaluation.md`. ID-test did not prove stable acceleration; OOD was slower with 25% learned fallback. Uniform remained the operational default.

The bounded M2 contract preserved the M1 model, loss, optimizer, and five seeds while increasing direction-balanced data and adding a finite validation-calibrated gate with fresh 36-case ID-test and 252-case OOD reserves. Its 756-case catalog, exposure-aware 432/36/36/252 split, recoverable executor, and guarded production entry point were implemented. Materialization produced 746 valid labels and ten deterministic non-convergence failures, seven in training. The pre-registered data gate failed; fitting, calibration, and final evaluation did not start (`docs/validation/m2_catalog_materialization.md`). ML expansion stopped and the project moved to release closeout.

## Overall time estimates

For an independent Numerical Core, validation, platform, ML warm starts, controlled comparisons, OOD tests, deployment, and documentation:

| Effective development time per day | Estimated duration |
|---|---:|
| 6–8 hours | **about 8–11 weeks** |
| 3–5 hours | **about 10–14 weeks** |
| 1–2 hours | **about 16–22 weeks** |

A safer aggregate budget was **10–14 weeks and about 250–400 effective hours**. A strong CS/SWE version without waiting for positive ML results might fit in 6–9 weeks. Existing 3D SIMP code, run outputs, and audit material reduced startup effort, but development assistance could not eliminate numerical verification, sparse-solver debugging, generation/training time, baseline comparison, OOD/ablation/multiseed work, or learning the system well enough for applications and interviews.

## Stage-by-stage estimate

| Stage | Estimated time | Main output |
|---|---:|---|
| Repository cleanup and baseline | 2–3 days | Independent repository, environment, original outputs, rules, reproducible entry point |
| Numerical defect repair | 5–8 days | Load direction/total, compliance, final-state, BC corrections |
| Numerical validation | 5–8 days | Finite differences, load balance, volume, small meshes |
| Sparse performance | 7–12 days | Sparse stiffness/filter, time and memory benchmark |
| FastAPI and asynchronous jobs | 8–12 days | API, worker, run ID, progress, cancellation, failure, database |
| 3D frontend and results | 5–8 days | Configuration, 3D view, convergence, history |
| Data-generation pipeline | 4–7 development days plus compute time | Varied loads, supports, volumes |
| ML warm starts | 7–12 days | Training, inference, SIMP integration, fallback |
| Baselines, OOD, ablations | 7–12 days | Quantitative report |
| Deployment, CI, documents, demo | 4–7 days | Containers, CI, README, architecture, demo video |

Some work can overlap, such as frontend development while data generation runs. Numerical, platform, and ML work should not all start at once: N2 must establish a credible core before platform/data work, and large-scale ML training requires a frozen dataset and split.

## Gates and release conditions

| Gate | Required evidence | Permitted next work |
|---|---|---|
| G0 repository ready | README, license decision, provenance, locked environment, CI smoke, upstream baseline | Numerical Core |
| N1 FEM correct | Small-mesh stiffness symmetry, dense-reference displacement, load/reaction balance | SIMP and sensitivity |
| N2 optimization correct | Finite differences, volume, final-state compliance, deterministic regression | API, worker, data generation |
| P1 platform credible | State machine, cancellation, failure, isolation, two concurrent jobs | Frontend and public demo |
| M0 data frozen | Case schema, generator, train/val/test split, baselines | ML training |
| M1 ML conclusion supported | Multiseed, OOD, and end-to-end same-quality comparison | A learned/accelerated claim, only if positive |

If a gate fails, fix that layer before building over it.

## Three levels of completion

### Level 1: Runnable MVP

**Estimated 3–5 weeks.** Correct main numerical defects, add basic tests, provide a FastAPI interface and simple 3D results page. This demonstrates a full flow but not yet a high-standard flagship project; estimated overall project strength was **6.5–7.5/10**.

### Level 2: Strong CS/SWE project

**Estimated 6–9 weeks.** Add a sparse FEM solver; time/memory benchmarks; asynchronous state management; database and result versioning; concurrency isolation; containers, tests, and CI; and a complete 3D frontend with history. Even without positive ML evidence, estimated CS/SWE fit could reach **8.5–9/10**.

### Level 3: Full flagship project

**Historical estimate: 10–14 weeks, now open-ended for delivery.** Extend Level 2
with a reproducible generation pipeline, a learned acceleration method,
uniform/physics/nearest-neighbor baselines, OOD tests, ablations, multiple seeds,
time/iteration/compliance/volume/failure statistics, deployment, a technical
report, and a demo. Full v1.x flagship delivery additionally requires the positive
ML gate in the active roadmap.

Estimated fit under that *hypothetical complete scope*:

| Program area | Fit |
|---|---:|
| Computer Science | **about 9/10** |
| Software Engineering / SDE | **9–9.5/10** |
| Artificial Intelligence / Machine Learning | **8.5–9/10** |
| Information Systems | **8–8.5/10** |
| Scientific Computing / AI for Science | **about 9.5/10** |

## Main schedule risk

Whether ML beats conventional initialization is the biggest uncertainty. The
original **2–4 additional weeks** was a planning estimate, not a bound on the
remaining research. If a model fails, preserve the result, diagnose the cause,
and register a finite new intervention with fresh final evidence. A negative ML
result does not erase numerical/platform contributions, but it means the full
v1.x flagship project has not met its delivery condition.

## Physical equipment and materials

All necessary development for the stated project standard can be performed on a computer. No 3D printer, specimen material, tensile machine, sensor, laboratory, physical break test, or commercial FEM license is required. The FEM/SIMP solver can generate labels without manual annotation.

Numerical checks can use a simple beam or small-grid analytical case, finite-difference sensitivity, element symmetry and six rigid-body modes, constrained positive definiteness, load/reaction balance, volume constraints, mesh convergence, a dense cross-check, and, when useful, an independent open-source FEM comparison.

Physical fabrication and loading experiments are optional enhancements. They become relevant if the project is extended into mechanical-engineering research with manufacturing or experimental claims.

## Computing resources

An ordinary personal computer can support solver development, small/medium 3D SIMP, FastAPI/database/frontend, small-scale generation, and a basic warm-start experiment. A GPU or cloud machine may help with large 3D CNN/U-Net models, thousands of 3D samples, larger voxel grids, or large multiseed searches.

Start with small meshes and a lightweight model. A Mac CPU or MPS is sufficient for a prototype; consider school servers, Colab, or hourly GPU only if fitting becomes too slow. GPU access is an efficiency option, not a project prerequisite. Local deployment can precede cloud deployment.

## Suggested first-version stack

Use one concrete stack to control scope:

- **Environment/quality:** Python 3.12, `uv`, Ruff, mypy, pytest, GitHub Actions;
- **Numerical Core:** NumPy and SciPy sparse;
- **API:** FastAPI and Pydantic;
- **Persistence:** SQLAlchemy with SQLite first, PostgreSQL only when needed;
- **Background jobs:** A stable process job/state boundary first, then Redis + RQ for a later Level 2, not Celery in the MVP;
- **Frontend:** React + TypeScript, Plotly for first convergence/voxel views, vtk.js/Three.js only for demonstrated interaction needs;
- **ML:** PyTorch, starting with a small 3D CNN rather than a large U-Net or unbounded search; and
- **Artifacts:** Small reviewed fixtures in Git; large outputs and datasets outside Git with manifests, checksums, and generators.

Revisit the stack at a gate, not by preparing several competing frameworks at startup.

## Stage zero before development (1–2 days)

1. Clone the repository and create a first short-lived branch (`feat/n1-hex8-mesh` was the planned first development branch).
2. Add README, `PROVENANCE.md`, LICENSE, `.gitignore`, `pyproject.toml`, minimal CI, and the three planning documents in `docs/planning/`.
3. Fix the upstream URL, SHA, license absence, and no-copy boundary in provenance.
4. Record CPU, memory, OS, and Python for later benchmarks.
5. Save default upstream case parameters and output summaries without committing unlicensed source.
6. Specify first executable checks: Hex8 symmetry, face-load total, fixed DOFs, and small dense/sparse agreement.

G0 then releases Numerical Core work; no GPU, cloud server, printer, or additional dataset is needed.

## Concrete targets for the first two weeks

### Week 1

- Complete G0; freeze coordinates, node/DOF order, units, load signs, and density conventions;
- Build the structured Hex8 mesh, material matrix, element stiffness, and a small dense reference; and
- Test stiffness symmetry, rigid modes, constrained DOFs, and load conservation.

### Week 2

- Implement SciPy COO/CSR assembly and constrained solving;
- Add compliance and analytical sensitivity;
- Check central finite differences and small dense/sparse agreement; and
- Begin filtering, OC, and full SIMP only after those checks pass.

The success criterion is independently testable, repeatable numerical behavior, not attractive 3D images.

## ML experiment stopping and flagship delivery rules

- Establish uniform, physics-based, and nearest-neighbor baselines before neural training.
- Use one lightweight model family, a bounded hyperparameter budget, and at least three seeds in the first round.
- Warm starts must meet the same volume and final compliance tolerance, with inference charged to end-to-end time.
- If held-out/OOD cases show no stable gain, freeze that experiment and write a
  failure analysis. Keep the existing truthful public title, but do not mark the
  full v1.x flagship delivered.
- Use a measured root cause, a new finite contract, and fresh final evidence for
  each subsequent attempt. Do not expand models, data, or cloud spending without
  a reviewable budget to obtain a resume number.

## Current execution strategy

1. Keep the completed numerical and platform milestones as independently
   validated interim outputs.
2. Prioritize measured warm-start feasibility, numerical failure repair, and a
   meaningful workload/scale pilot before any new production ML fitting.
3. Freeze a new bounded experiment only after the pilot identifies attainable
   quality-preserving savings. Run final evaluation once on new evidence.
4. If the ML gate fails, retain the negative result, plan a finite new versioned
   intervention, and keep the full flagship delivery status open.

The active roadmap defines the detailed gates. These stages do not promise a
completion date or a positive empirical result in advance.
