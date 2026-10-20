# Provenance and implementation boundary

## Hack3D reference baseline

- Repository: <https://github.com/Jiangce2017/3D_SIMP_Topology_Optimization_Numpy>
- Fixed commit: `584cb8ee570d375f8ba9b10272020c5c2daa8c30`
- Author/account: Jiangce2017
- License status checked on 2026-09-17: no open-source license is declared in the
  GitHub repository.

The reference repository is kept outside TopoLab and is used only to understand the
original Hack3D problem statement, preserve a historical behavior baseline, and
identify cases for independent numerical validation. TopoLab does not copy,
translate, modify, or redistribute its source files, comments, module structure, or
figures.

## TopoLab implementation boundary

TopoLab's source code will be independently written from published equations,
documented numerical conventions, and tests. Cross-checking against the Hack3D
reference is secondary to analytical checks, finite differences, equilibrium, and
dense-versus-sparse verification. TopoLab will not reproduce an upstream behavior
when independent evidence shows that behavior is incorrect.

If upstream code is ever introduced, development must stop until written permission
and license compatibility are documented here and in the affected files.

## Primary technical references

1. Kai Liu and Andrés Tovar, "An efficient 3D topology optimization code written in
   Matlab," *Structural and Multidisciplinary Optimization* 50, 1175–1196 (2014).
   <https://doi.org/10.1007/s00158-014-1107-x>
2. Top3d documentation and errata. <https://www.top3d.app/>
3. Ole Sigmund, "A 99 line topology optimization code written in MATLAB,"
   *Structural and Multidisciplinary Optimization* 21, 120–127 (2001).
   <https://doi.org/10.1007/s001580050176>

These sources define standard methods; they do not imply that TopoLab invented SIMP,
Hex8 finite elements, density filtering, or the Optimality Criteria method.

## ML planning references, not implemented results

The v2 acceleration roadmap considers, as possible future interventions, the
published ideas of theory-guided topology learning
([Cang, Yao, and Ren, 2019](https://arxiv.org/abs/1807.10787)),
algorithm-aware 3D learning from intermediate states
([Rade et al., 2021](https://arxiv.org/abs/2012.05359)), and strain-energy
conditioning ([Chen, Joglekar, and Kara, 2023](https://arxiv.org/abs/2305.10460)).
They motivated hypotheses only; no architecture, code, dataset, weights, figures,
or reported speedup was imported. Any later implementation needs its own
independent design, provenance entry, and TopoLab validation.

## Contribution log

| Date | Component | Source/derivation | Notes |
|---|---|---|---|
| 2026-09-17 | G0 repository scaffolding | Original TopoLab work | No numerical implementation |
| 2026-09-17 | Structured Hex8 mesh | Independent Cartesian-grid derivation from the conventions documented in this repository | No upstream source code or file structure used |
| 2026-09-17 | Isotropic material matrix and Hex8 element stiffness | Independent implementation of standard small-strain elasticity, trilinear Hex8 shape functions, and Gauss quadrature; see Liu and Tovar (2014) in Primary technical references | No upstream source code or hard-coded upstream stiffness matrix used |
| 2026-09-17 | Sparse global assembly and constrained solve | Independent implementation of standard finite-element scatter assembly, direct elimination of zero-displacement DOFs, and reaction recovery | No upstream source code used |
| 2026-09-17 | Fixed-face supports and point/face loads | Original typed models and independent discretization following this repository's direction, sign, and total-resultant conventions | No upstream source code used |
| 2026-09-17 | Gate N1 validation | Original automated tests and documented analytical/dense-sparse checks | Release evidence is recorded in `docs/validation/n1_fem_validation.md` |
| 2026-09-17 | SIMP compliance and analytical sensitivity | Independent implementation of the standard interpolation and adjoint derivative documented by Sigmund (2001) and Liu and Tovar (2014) | Validated against independent central finite differences; no upstream source code used |
| 2026-09-17 | Density filter, OC update, and SIMP loop | Independent implementation from the documented density-filter and Optimality Criteria equations in the primary references | State consistency, volume, final re-solve, and determinism are covered by original tests |
| 2026-09-17 | Gate N2 validation | Original automated tests and documented numerical audit | Release evidence is recorded in `docs/validation/n2_optimization_validation.md` |
| 2026-09-18 | Problem/result contracts, run lifecycle, and HTTP adapter | Original TopoLab platform work | No upstream reference code used; platform semantics are documented in `docs/platform_contract.md` |
| 2026-09-18 | Gate P1 validation | Original automated tests and documented platform audit | Release evidence is recorded in `docs/validation/p1_platform_validation.md` |
| 2026-09-18 | SQLite run persistence and restart recovery | Original TopoLab platform work using the public SQLAlchemy API | No upstream reference code used; persistence semantics are documented in `docs/run_persistence.md` |
| 2026-09-18 | Paginated run history and UTC lifecycle timestamps | Original TopoLab platform work | Stable ordering, cursor behavior, timestamp migration, and HTTP boundaries have original tests |
| 2026-09-18 | React run-history workspace | Original TopoLab frontend work using the documented public API contract | No upstream reference code, figures, or visual assets used |
| 2026-09-18 | 3D physical-density visualization | Original TopoLab geometry mapping using the frozen element-index convention and the public Plotly API | No upstream reference code, plotting code, figures, or visual assets used |
| 2026-09-19 | Problem configuration and run submission workspace | Original TopoLab frontend work over the frozen problem and run-lifecycle contracts | No upstream reference code, forms, or visual assets used |
| 2026-09-19 | State-consistent convergence visualization | Original TopoLab frontend mapping of the frozen iteration-history contract using the public Plotly API | No upstream plotting code, figures, or visual assets used |
| 2026-09-19 | Frontend run cancellation workflow | Original TopoLab frontend work over the frozen cooperative-cancellation contract | No upstream reference code, controls, or visual assets used |
| 2026-09-19 | Sparse solver performance and peak-memory benchmark | Original TopoLab benchmark harness over the independently implemented FEM path | No upstream benchmark code, measurements, or figures used |
| 2026-09-19 | M0 experiment contract and case identity | Original TopoLab schema, canonical serialization, data-isolation, baseline, and evaluation design over the frozen public problem contract | No upstream source code, dataset, model, experiment definition, or figures used |
| 2026-09-19 | M0 case tensor encoding and density projection | Original TopoLab mapping from the frozen problem contract to element-grid channels and independent monotone bisection over the existing density filter | No upstream encoding, projection, dataset, model, or source code used |
| 2026-09-20 | M0 dataset manifest and deterministic partition assignment | Original TopoLab typed metadata schema and direct implementation of the repository's frozen hash-split, fixed-cohort, and matched-OOD rules | No upstream manifest, generator, dataset, model, source code, or figures used |
| 2026-09-20 | M0 single-case label generation | Original TopoLab typed label record and validation adapter over the independently implemented SIMP solver, including terminal-state and independent compliance checks | No upstream label format, generator, dataset, model, source code, or figures used |
| 2026-09-21 | M0 content-addressed label artifacts | Original TopoLab canonical JSON, checksum reference, stable relative-path, atomic-write, and verified-read contract over the typed label record | No upstream artifact layout, serialization code, dataset, model, source code, or figures used |
| 2026-09-21 | M0 recoverable materialization index | Original TopoLab canonical manifest identity, append-only outcome ledger, atomic checkpoint, and manifest-to-label provenance verification | No upstream index format, orchestration code, dataset, model, source code, or figures used |
| 2026-09-21 | M0 controlled materialization executor | Original TopoLab canonical-order, single-writer generation loop with per-case atomic checkpoints, known-failure recording, and interruption recovery | No upstream orchestration code, dataset, model, source code, or figures used |
| 2026-09-21 | Density-filter convex-bound roundoff guard | Independent enforcement of the mathematical range invariant of TopoLab's existing nonnegative normalized filter, with original regression cases | No upstream source code, tests, dataset, or figures used |
| 2026-09-22 | M0 bounded case catalog | Original TopoLab typed catalog identity and independently selected fixed-cohort Cartesian enumeration over the public problem contract | No upstream catalog, parameter grid, dataset, model, source code, or figures used |
| 2026-09-22 | M0 production materialization entrypoint | Original TopoLab clean-revision and locked-environment capture, read-only planning mode, explicit execution control, and external-output guard over the frozen catalog and executor | No upstream orchestration code, dataset, model, source code, file structure, or figures used |
| 2026-09-22 | M0 catalog materialization validation | Original TopoLab labels generated exclusively by the independently implemented solver, plus aggregate integrity, convergence, volume, cost, and failure evidence | Generated artifacts remain outside Git; no upstream dataset, label, code, model, or figures used |
| 2026-09-22 | M0 catalog v2 termination-budget revision | Original TopoLab contract revision based only on the recorded v1 materialization and independent diagnostic re-solves; preserves tolerance and cohort while versioning all affected identities | No upstream code, dataset, experiment definition, file structure, or figures used |
| 2026-09-22 | M0 catalog v2 materialization validation | Original TopoLab labels generated exclusively by the independently implemented solver, plus complete artifact, convergence, volume, cost, and reproducibility audit | Generated artifacts remain outside Git; no upstream dataset, label, code, model, file structure, or figures used |
| 2026-09-22 | Fixed M0 baseline runner | Original TopoLab uniform, analytical-sensitivity heuristic, training-only tensor nearest-neighbor lookup, quality audit, timing, and charged-fallback integration over the frozen contracts | No upstream baseline code, experiment runner, dataset, model, source code, file structure, or figures used |
| 2026-09-22 | M1 training contract, lightweight CNN, and fitting-data adapter | Original TopoLab experiment recipe and small shape-preserving PyTorch model over the frozen M0 tensor/label contracts; framework and CPU-only dependency configuration follow the public [PyTorch documentation](https://docs.pytorch.org/) and [uv PyTorch guide](https://docs.astral.sh/uv/guides/integration/pytorch/) | No upstream model, training code, checkpoint, dataset, source code, file structure, or figures used; no training run performed |
| 2026-09-22 | M1 deterministic fitting and training artifacts | Original TopoLab per-seed training loop, weighted epoch metrics, strict earliest-minimum selection, content addressing, atomic persistence, and provenance verification over the frozen M1 contract; checkpoint tensor serialization follows the public [Safetensors format and API](https://huggingface.co/docs/safetensors/) | No upstream training loop, artifact schema, checkpoint, model weights, dataset, source code, file structure, or figures used; production training remains unexecuted |
| 2026-09-22 | M1 production training entrypoint | Original TopoLab clean-revision, exact-manifest, external-root, read-only-plan, explicit-execution, and five-selection audit boundary over the frozen M1 fitting contract | No upstream training entrypoint, experiment orchestration, model weights, dataset, source code, file structure, or figures used; execution evidence is recorded separately below |
| 2026-09-22 | M1 production fitting validation | Original TopoLab five-seed execution and artifact audit over the independently generated, frozen catalog-v2 train/validation partitions | Generated checkpoints and selection records remain outside Git; no upstream model weights, dataset, training results, source code, file structure, or figures used; test/OOD remained unopened |
| 2026-09-23 | M1 learned warm-start evaluator | Original TopoLab checkpoint-bound CPU inference, filtered-volume projection, shared SIMP quality audit, phase timing, and charged uniform fallback over the frozen experiment contract | No upstream evaluation runner, inference code, model weights, dataset, source code, file structure, or figures used; production test/OOD evaluation remains unexecuted |
| 2026-09-23 | M1 recoverable held-out experiment runner | Original TopoLab five-selection audit, training-only nearest-neighbor setup, per-physical-case atomic checkpoint/recovery, paired method summaries, and case-cluster bootstrap implementation | No upstream experiment orchestration, statistics code, model weights, dataset, source code, file structure, or figures used; production test/OOD evaluation remains unexecuted |
| 2026-09-23 | M1 held-out evaluation validation | Original TopoLab execution and audit of the frozen five-seed ID-test/OOD comparison, including charged failures, case-cluster bootstrap statistics, artifact identity, and claims decision | Generated evaluation artifacts remain outside Git; no upstream dataset, result, model weight, code, file structure, or figure used; the negative/inconclusive result is preserved without seed or case selection |
| 2026-09-23 | M2 bounded follow-up contract | Original TopoLab exposure-aware cohort, stratified split, fixed five-model ensemble, finite reliability-gate calibration, fresh evidence boundary, statistics, and stopping rule motivated by the frozen M1 result | No upstream experiment design, dataset, model, result, code, file structure, or figure used; no M2 data generation, fitting, calibration, or evaluation performed |
| 2026-09-23 | M2 catalog and exposure-aware split | Original TopoLab enumeration and content identity for the pre-registered 756-case cohort plus deterministic direction/volume strata that force all M1-exposed cases into training | No upstream catalog, split, dataset, model, code, file structure, or figure used; this metadata-only slice runs no solver and opens no label artifact |
| 2026-09-23 | M2 production materialization entrypoint | Original TopoLab M2-specific manifest/index discrimination over the existing recoverable executor, plus clean-revision and locked-environment capture, read-only planning, explicit execution, and external-output safeguards | No upstream orchestration code, dataset, label, model, source code, file structure, or figure used; no M2 solver execution performed |
| 2026-09-24 | M2 catalog materialization validation | Original TopoLab execution and audit of the pre-registered 756-case cohort, including a safely detected checkpoint-version defect, complete artifact verification, deterministic failure diagnosis, and the frozen data-gate decision | Generated artifacts remain outside Git; no upstream dataset, label, result, model weight, code, file structure, or figure used; 10 failures are preserved and no M2 fitting was performed |
| 2026-09-24 | v1.0.0 release closeout | Original TopoLab version metadata, evidence index, release notes, and claims-boundary consolidation over the repository's completed validation records | No external implementation or artifact introduced; historical gate outcomes and negative ML results are preserved |
| 2026-09-24 | A1.1 canonical local demo | Original TopoLab versioned public problem input, narrow CLI over the existing run manager, and end-to-end smoke test | No upstream source code, figure, example file, or generated run artifact used; demo outputs remain outside Git |
| 2026-09-24 | A1.2 local container stack | Original TopoLab Compose topology, API persistence entry point, and static frontend proxy configuration, informed by [Docker Compose](https://docs.docker.com/compose/how-tos/startup-order/), [uv's Docker guide](https://docs.astral.sh/uv/guides/integration/docker/), and the [NGINX unprivileged image](https://github.com/nginx/docker-nginx-unprivileged/blob/main/README.md) documentation | No upstream project code, figure, dataset, result, or model artifact used; runtime SQLite data stays in a Docker named volume outside Git |
| 2026-09-24 | A1.3 architecture and demo evidence | Original TopoLab SVG architecture diagram and screen recording of the existing local Compose stack, derived from this repository's code and contracts | No upstream figure, media, source code, dataset, checkpoint, or generated run artifact used; captured run records remain outside Git |
| 2026-09-25 | A1.4 clean Linux stack smoke | Original TopoLab CI and standard-library smoke checker for the existing Compose stack and canonical public problem, with environment and timing evidence recorded separately | No upstream source code, test script, dataset, result, or figure used; the disposable SQLite volume and run result are removed after the smoke |
| 2026-09-25 | Development-only warm-start feasibility probe | Original TopoLab read-only comparison using the frozen M2 validation labels, public SIMP adapter, projection, and quality boundary; seven failed training case definitions were re-solved without changing their status | No M2 test/OOD or M3 final label read; no upstream code, dataset, result, model weight, or figure used; generated summaries stayed out of Git |
| 2026-09-25 | B1 convergence and learned-quality diagnosis | Original TopoLab read-only replay of the ten failed M2 case definitions and five verified M1 checkpoints on M2 validation labels, using the independently implemented SIMP solver and shared quality boundary | No M2 test/OOD label read, new fitting, solver change, or external code/data imported; extended iterations were diagnostic only and their summaries stayed out of Git |
| 2026-09-25 | A3 sparse factorization ordering | Original TopoLab measurement-led selection of SuperLU's documented minimum-degree ordering for larger reduced systems, with the former COLAMD ordering retained as an explicit fallback and matched numerical/benchmark checks | No upstream implementation, dataset, model, result, code, figure, or artifact imported; performance findings are limited to the reported environments and meshes |
| 2026-09-25 | B2 development-only workload pilot | Original TopoLab fixed two-scale cantilever cohort, matched optimized-uniform/oracle/heuristic/nearest-neighbor/five-checkpoint runner, charged-fallback quality audit, and separate convergence diagnosis | M2 validation definitions were development-exposed; no M2 label or test/OOD artifact was read, no new fitting occurred, and all generated pilot and diagnostic summaries remained outside Git; no upstream code, data, model, or result imported |
| 2026-09-25 | B2.1 opt-in physical-plateau convergence policy and matched development audit | Original TopoLab filtered-physical-density/compliance plateau rule derived from its own B2 traces, with the historical design-density stop retained; all twelve fixed cases and methods were independently rerun under a versioned solver/result identity | No external implementation, code, dataset, model, result, or figure imported; M2 catalog/split definitions and M1 training/checkpoint artifacts only were read, no M2 label or held-out outcome was opened, and generated comparison JSON stayed outside Git |
| 2026-09-25 | B2.2/B2.3 development-data feasibility and versioned budget repair | Original TopoLab 522-case metadata plan, fixed 61-case sentinel, read-only failure extension, and one 240-update per-case budget intervention using the existing physical-plateau solver and unchanged numerical tolerances | No external code, dataset, model, result, or figure imported; no M2 test/OOD or new final outcome opened, no model fitted, and all generated plans and probe JSON stayed outside Git |
| 2026-09-25 | B2.4 development-label plan and materializer | Original TopoLab 522-case budget-240 label contract, independent stored-state sensitivity weighting, checksum-addressed external artifacts, and recoverable complete-population audit, using only the existing development case/split metadata and implemented solver | No upstream code, dataset, model, result, or figure imported; no M2 test/OOD or new final outcome opened, and generated labels and checkpoints remain outside Git |
| 2026-09-25 | B2.4 complete development-label execution | Original TopoLab single-thread generation and numerical/checksum audit of all 522 new policy/budget train/validation labels from a clean committed revision | Generated density labels and checkpoint remain outside Git; no external or held-out dataset, model, result, code, or figure imported, and no model fitting or new final evaluation occurred |
| 2026-09-25 | B2.5 fixed development prototype | Original TopoLab mixed-shape deterministic batch schedule, same-model control/candidate objective comparison, checksum-bound external checkpoints, and matched-policy fallback-inclusive development screen over B2.4 labels | No upstream training or evaluation code, weights, results, dataset, or figure imported; no M2 test/OOD or new final outcome opened |
| 2026-09-25 | B2.5 complete fit and development screen | Original TopoLab six-seed-arm execution and 54-case matched validation audit from a clean tracked revision, with independently checked paired time, quality, and complete fallback charges | Generated weights, selections, case outcomes, and summaries remain outside Git; the negative development Gate is preserved, with no M2 test/OOD or new final outcome opened |
| 2026-09-26 | B2.6 intermediate-trajectory target and fresh development screen | Original TopoLab hypothesis based on its B2.5 refinement and quality evidence: capture the unchanged uniform solver's thirtieth post-update design state, fit the existing CNN to that state, and compare on newly defined disjoint development cases | No upstream code, dataset, weights, result, or figure imported; no M2 test/OOD or new final evidence opened; all generated targets, checkpoints, and outcomes stay outside Git |
| 2026-09-26 | B2.6 complete target, fit, and screen audit | Original TopoLab clean-revision execution of all 480 development trajectory targets, three fixed CNN fits, and 96 quality-audited outcomes on 12 new physical cases; the negative Gate is retained in `docs/validation/b2_6_trajectory.md` | All generated targets, weights, selections, and case outcomes remain outside Git; no upstream or held-out final artifact was opened or imported |
| 2026-09-26 | B2.7 global point-load representation and fixed screen | Original TopoLab input-field intervention derived from its two-convolution receptive field and B2.6 direction/cost evidence, plus an independently versioned same-target development fit and new-case screen | No external implementation, weights, labels, or results imported; prior negative results and final evidence remain sealed; all generated artifacts stay outside Git |
| 2026-09-26 | B2.7 complete fit and new-case screen audit | Original TopoLab clean-revision execution of three globally conditioned CNN fits and 132 quality-audited method outcomes on twelve new development physical cases; the negative Gate is retained in `docs/validation/b2_7_global_load.md` | Existing B2.6 target artifacts were checksum- and volume-audited; generated B2.7 checkpoints, selections, and outcomes remain outside Git; no final evidence was opened |
| 2026-09-26 | B2.8 versioned y-load start recentering and fresh screen plan | Original TopoLab fixed midpoint toward the uniform initial field, motivated by its B2.7 y-direction compliance failures and slow refinements; the unchanged three B2.7 checkpoints and solver are matched against the opt-in start policy on new development cases | No upstream code, weights, labels, result, or figure imported; B2.6/B2.7 cases are only exposed development evidence, final evidence remains sealed, and all generated outcomes stay outside Git |
| 2026-09-26 | B2.8 complete midpoint-start development screen | Original TopoLab clean-revision evaluation and independent audit of 132 matched outcomes on 12 new physical cases; the negative Gate and unchanged 2/3/4 learned failure counts are retained in `docs/validation/b2_8_basin.md` | All generated case outcomes and summaries remain outside Git; no external model, label, result, code, figure, or final evidence was imported or opened |
| 2026-09-26 | B2.9 vector point-load conditioning and frozen development plan | Original TopoLab 13-channel direction and relative-position encoding, same-depth CNN, unchanged B2.6 target population, and new disjoint twelve-case screen, motivated by B2.7/B2.8 directional failures | No upstream implementation, weights, labels, results, or figures imported; previous screens are diagnosis only, final evidence remains sealed, and generated fit and screen artifacts stay outside Git |
| 2026-09-26 | B2.9 complete vector-load fit and new-case audit | Original TopoLab clean-revision three-seed fit on audited development targets and 132 matched quality-audited outcomes on twelve new cases; the negative direction-wise Gate is retained in `docs/validation/b2_9_vector_load.md` | All generated checkpoints, selections, case outcomes, and summaries remain outside Git; no external model, label, code, figure, or final evidence was imported or opened |
| 2026-09-26 | B2.10 sensitivity-weighted trajectory objective and frozen screen | Original TopoLab reuse of its B2.4 bounded design-compliance sensitivity rule at the audited B2.6 intermediate states, with unchanged B2.9 vector input/model and a new disjoint development screen | Earlier B2.5 negative weighted-loss evidence is retained; no external implementation, weights, labels, results, or final evidence imported or opened; generated artifacts stay outside Git |
| 2026-09-26 | B2.10 complete offline fit and reference-feasibility stop | Original TopoLab clean-revision generation/audit of 480 sensitivity weights and three fixed fits, followed by 99 quality-audited outcomes on nine fresh cases; the tenth mandatory uniform reference failed the 240-update convergence check, and the negative/incomplete Gate is retained in `docs/validation/b2_10_weighted_trajectory.md` | Generated weights, selections, checkpoints, case outcomes, and diagnostic cap runs remain outside Git; no external or final evidence was imported or opened; a 360-update diagnostic with a new case identity was not used in the frozen comparison |
| 2026-09-27 | B2.11 frozen reference-budget repair and fixed-model screen | Original TopoLab versioned 360-update development comparison, motivated by the independently repeated B2.10 mandatory-uniform 240-update failure and a separately identified 282-update diagnostic stop; old/new sentinel and new disjoint screen use the existing solver and model checkpoints | No external implementation, labels, weights, result, or figure imported; B2.10's failed evidence is preserved, final evidence remains sealed, and generated metadata/outcomes stay outside Git |
| 2026-09-27 | B2.11 complete sentinel, reference, and fixed-model screen audit | Original TopoLab clean-revision 12-pair old/new uniform regression, 12 quality-feasible fresh uniform references, and 132 fully charged method outcomes on disjoint development cases; the negative learned Gate is retained in `docs/validation/b2_11_reference_budget.md` | Checkpoint bytes were verified but unchanged; all generated indices and outcomes remain outside Git, no external model/data/result was imported, and M2 test/OOD plus new final evidence remained sealed |
| 2026-09-27 | B2.12 bounded spatial-context model and fresh development plan | Original TopoLab architecture hypothesis from B2.11's measured solution-basin and refinement-cost failures, using a fixed axis-aware dilation schedule with unchanged vector input, trajectory targets, fitting objective, and comparison rules | No external architecture, weights, labels, results, code, or figures imported; prior screens are diagnosis only, final evidence remains sealed, and generated artifacts stay outside Git |
| 2026-09-27 | B2.12 complete references, fits, and development screen audit | Original TopoLab clean-revision execution of twelve disjoint quality-feasible uniform references, three fixed CNN fits, and 132 fully charged method outcomes; the negative two-scale learned Gate is retained in `docs/validation/b2_12_context_cnn.md` | All generated checkpoints, selections, indices, and outcomes remain outside Git; no external model/data/result was imported, and final evidence remained sealed |
| 2026-09-27 | B2.13 frozen workload routing and safe rejection | Original TopoLab metadata-only routing hypothesis from exposed B2.12 scale/direction/cost evidence, selecting previously audited B2.9/B2.12 checkpoints and a fresh-uniform rejection on high-volume large-y cases | No external implementation, weights, labels, data, result, or figure imported; earlier results are diagnosis only, final evidence remains sealed, and generated artifacts stay outside Git |
| 2026-09-27 | B2.13 complete reference and routed development audit | Original TopoLab clean-revision execution of twelve disjoint quality-feasible uniform references and 144 fixed-method outcomes, with an independent identity, numerical, cost, and Gate audit retained in `docs/validation/b2_13_routing.md` | The small development Gate passed, but a fixed context model was faster on this cohort; generated indices and outcomes remain outside Git, no external result was imported, and final evidence remained sealed |
| 2026-09-27 | B2.14 frozen larger development confirmation | Original TopoLab 24-case disjoint cohort and deterministic selection rule comparing the unchanged B2.13 route with audited B2.9/B2.12 checkpoints and fixed non-ML baselines | No external code, weights, labels, outcomes, or figures imported; all new results remain unopened until the committed protocol and runner execute, and final evidence remains sealed |
| 2026-09-27 | B2.14 complete reference and development confirmation audit | Original TopoLab clean-revision execution of 24 quality-feasible uniform references and 192 fully charged outcomes on disjoint cases, with independent artifact, numerical, cost, and selection audit retained in `docs/validation/b2_14_development_confirmation.md` | The frozen confirmation Gate failed with no eligible policy; generated plans, indices, summaries, logs, and audit script remain outside Git, and final evidence remains sealed |
| 2026-09-27 | B2.15 frozen position-aware routing and safe rejection | Original TopoLab metadata-only policy derived from exposed B2.14 position, quality, and cost diagnoses, selecting already audited B2.9/B2.12 checkpoints or fresh uniform work | No external code, weights, labels, outcomes, or figures imported; new development cases remain unopened until the committed protocol and runner execute, and final evidence remains sealed |
| 2026-09-27 | B2.15 complete development reference, screen, and independent audit | Original TopoLab clean-revision execution of 24 quality-feasible uniform references and 192 fully charged outcomes on new cases, plus independent identity, numerical, cost, and Gate recomputation recorded in `docs/validation/b2_15_position_routing.md` | The frozen Gate failed; all generated plans, indices, summaries, logs, and audit code remain outside Git, and final evidence remains sealed |
| 2026-09-27 | B2.16 frozen method-class reassessment | Original TopoLab read-only audit and optimistic bound definitions over already exposed B2.14/B2.15 development artifacts, including fixed-checkpoint selection, coarse-cell transfer, and zero-cost failure rejection | No external implementation, model, dataset, outcome, or figure imported; no new solver or learned outcome is opened, and all derived artifacts remain outside Git |
| 2026-09-27 | B2.16 complete read-only method-class audit | Original TopoLab hash-bound reassessment of 48 exposed cases and 384 fully charged outcomes, independently recomputing optimistic selector floors, cross-cohort metadata transfer, ideal early rejection, and the frozen method-class decision in `docs/validation/b2_16_method_class.md` | No new solver, model, label, or final outcome opened; generated derived summaries and independent audit code remain outside Git; B3 and final evidence stay closed |
| 2026-09-28 | B2.17 frozen online early-reliability probe | Original TopoLab query-time comparison of two independently computed SIMP compliance trajectories, with a paid uniform shadow, fixed early signal, exposed sentinel, and conditional fresh development Gate | No external implementation, model, data, weight, or figure imported; the existing solver equations and quality limits remain unchanged; new cases stay sealed until the committed sentinel passes |
| 2026-09-28 | B2.17 complete exposed-sentinel failure audit | Original TopoLab clean-revision execution of four paid two-update diagnostics and independent hash, quality, timing, signal, and stopping-rule recomputation, recorded in `docs/validation/b2_17_early_reliability.md` | Three missed terminal failures stopped the experiment before new cases; no new fit, fresh development outcome, M2 test/OOD, or final evidence was opened; generated records stayed outside Git |
| 2026-09-28 | B2.18 frozen solver-anchored start | Original TopoLab fixed blend of a paid two-update uniform physical trajectory with the audited context-17 projected design, followed by unchanged SIMP and independent quality checks | No external implementation, weights, labels, results, or figure imported; the previously failed early-score policy is not retuned; new cases stay sealed until a clean-revision sentinel passes |
| 2026-09-28 | B2.18 complete solver-anchor sentinel audit | Original TopoLab clean-revision run and independent identity, numerical, timing, quality, fallback, and Gate recomputation of four high-volume large-y development-exposed cases, recorded in `docs/validation/b2_18_solver_anchor.md` | Three terminal failures remained and paid full fallback; the four reserved new cases, M2 test/OOD, and final evidence remained sealed; generated artifacts stayed outside Git |
| 2026-09-28 | B2.19 uniform-state sensitivity feature and frozen protocol | Original TopoLab computation from its independently implemented FEM/SIMP derivative at the uniform initial physical state, with a fixed log-normalized spatial channel, unchanged trajectory targets and fresh development cases | No external code, weights, labels, or figures imported; each query-time solve and any fallback are charged; M2 held-out and final evidence stay sealed |
| 2026-09-28 | B2.19 complete physical-input fit and screen audit | Original TopoLab clean-revision execution of twelve quality-feasible uniform references, three fixed physical-input fits, and 84 fully charged outcomes on twelve new development cases, independently recomputed in `docs/validation/b2_19_physics_input.md` | The new-input Gate failed despite lower validation MSE; generated checkpoints, indices, and audit code remain outside Git, and M2 held-out plus final evidence remained sealed |
| 2026-09-28 | B2.20 frozen operational checkpoint selection | Original TopoLab quality-first lexicographic checkpoint selection over fixed training epochs and independently timed end-to-end development outcomes, with unchanged B2.12 inputs, model, target, optimizer and solver | No external model, code, weights, dataset, figure, or result imported; selection and screen cohorts are disjoint; generated artifacts remain outside Git and final evidence stays sealed |
| 2026-09-28 | B2.20 complete checkpoint-selection and screen audit | Original TopoLab clean-revision execution of 12 selection references, three unchanged context-model fits, 132 selection outcomes, 24 independent screen references, and 168 fully charged screen outcomes, independently recomputed in `docs/validation/b2_20_operational_selection.md` | The operational checkpoint-selection Gate failed; all six selected high-volume large-y attempts missed terminal quality; generated checkpoints, indices, and audit code remain outside Git, with M2 held-out and final evidence sealed |
| 2026-09-28 | B2.21 frozen terminal-design target | Original TopoLab reuse of its independently generated and audited uniform terminal designs as supervised density targets for the fixed B2.12 context CNN, with twelve newly audited development validation targets and a disjoint screen | No external implementation, model, weights, labels, results, or figures imported; query-time input, solver, quality, and fallback semantics stay fixed; all generated artifacts remain outside Git and final evidence stays sealed |
| 2026-09-28 | B2.21 complete terminal-target and screen audit | Original TopoLab clean-revision execution of 24 quality-feasible uniform references, twelve new terminal validation targets, three fixed fits, and 168 fully charged outcomes on disjoint development cases, independently recomputed in `docs/validation/b2_21_terminal_target.md` | The new-target Gate failed despite better large-z timing; all six high-volume large-y attempts missed quality; generated labels, weights, indices, and audit code remain outside Git, and M2 held-out plus final evidence stay sealed |
| 2026-09-28 | B2.22 high-volume y specialist and complete screen | Original TopoLab case-normalized training weights for its 52 high-volume y development labels, fixed large-y query route, and 24-case/168-outcome independent quality and cost audit recorded in `docs/validation/b2_22_y_specialist.md` | The frozen Gate failed despite three of six high-volume large-y specialist attempts passing quality; generated weights, indices, and audit code remain outside Git, and M2 held-out plus final evidence stay sealed |
| 2026-09-28 | B2.23 large-y load-position label-feasibility plan | Original TopoLab metadata coverage audit and fixed new development-only position/volume grid using the existing independently implemented uniform SIMP solver and B2.4 terminal-label checks | No external code, model, label, dataset, or figure imported; no new solver outcome is opened before the committed plan, and all generated labels will stay outside Git |
| 2026-09-29 | B2.23 complete position-label feasibility audit | Original TopoLab clean-revision materialization of 30 fixed large-mesh y-direction uniform labels and independent identity, byte-hash, numerical-quality, resource, and Gate recomputation recorded in `docs/validation/b2_23_position_labels.md` | The frozen data Gate passed; no model fit, learned screen, M2 held-out/OOD, or final evidence was opened; generated labels, indices, logs, and audit code remain outside Git |
| 2026-09-29 | B2.24 frozen expanded-position specialist protocol | Original TopoLab opt-in 20-label addition to its existing case-weighted terminal-design fit, unchanged checkpoint selection and query route, and fixed disjoint development screen with matched old-specialist controls | No external code, model, data, weight, or figure imported; no new reference, fit, diagnostic, or screen outcome is opened before the committed protocol; all generated artifacts remain outside Git |
| 2026-09-29 | B2.24 complete expanded-position fit and screen audit | Original TopoLab clean-revision execution of 24 quality-feasible uniform references, three fixed fits, ten diagnostic validation labels, and 168 fully charged matched outcomes, independently recomputed in `docs/validation/b2_24_expanded_training.md` | The frozen development Gate failed despite high-volume large-y quality improving from 0/6 to 6/6; generated checkpoints, indices, and audit code remain outside Git, with M2 held-out/OOD and final evidence sealed |
| 2026-09-29 | B2.25 frozen residual-cost diagnosis | Original TopoLab checksum-bound, read-only decomposition of B2.24's exposed quality failures and paid costs with three predeclared optimistic speed-only bounds | No new fit, solver call, dataset, model, external source, or final outcome; derived JSON remains outside Git and failed attempts retain failure status |
| 2026-09-29 | B2.25 complete residual-cost audit | Original TopoLab clean-revision arithmetic and independent mean/failure recomputation on its own previously generated B2.24 development indices, reported in `docs/validation/b2_25_residual_cost.md` | The ordered decision selects a later joint generalist intervention, not acceleration; no new case, fit, solver outcome, or final evidence opened |
| 2026-09-29 | B2.26 frozen y-weighted terminal generalist protocol | Original TopoLab opt-in case weights on its own audited terminal-design training population, unchanged high-volume large-y specialist route, and a fresh three-panel matched development screen | No external implementation, model, label, dataset, outcome, or figure imported; no new reference, fit, or screen outcome is opened before the committed protocol, and final evidence remains sealed |
| 2026-09-29 | B2.26 complete weighted-generalist fit and screen audit | Original TopoLab clean-revision execution of 24 quality-feasible uniform references, three fixed weighted fits, and 240 fully charged matched outcomes, independently recomputed in `docs/validation/b2_26_weighted_generalist.md` | The frozen development Gate failed despite one improved seed; generated checkpoints, indices, and audit code remain outside Git, with M2 held-out/OOD and final evidence sealed |
| 2026-09-29 | B2.27 frozen middle-volume y/z position-label protocol | Original TopoLab exposure-bound position and volume grid for its existing independently implemented uniform SIMP solver and B2.4 terminal-label checks | No external implementation, model, dataset, outcome, or figure imported; no new solver outcome is opened before the committed protocol, and generated labels remain outside Git |
| 2026-09-29 | B2.27 complete middle-volume position-label feasibility audit | Original TopoLab clean-revision materialization of 60 fixed large-mesh y/z uniform labels and independent identity, byte-hash, numerical-quality, resource, and Gate recomputation recorded in `docs/validation/b2_27_middle_volume_labels.md` | The frozen data Gate passed; no model fit, learned screen, M2 held-out/OOD, or final evidence was opened; generated labels, index, and audit code remain outside Git |
| 2026-09-29 | B2.28 frozen middle-volume generalist label expansion | Original TopoLab opt-in addition of 40 independently audited train labels to its weighted terminal-design fit, fixed validation diagnostics, unchanged specialist route, and physically disjoint matched screen | No external implementation, model, dataset, outcome, or figure imported; new outcomes remain unopened until the merged protocol, and generated artifacts stay outside Git |
| 2026-09-29 | B2.28 complete expanded-generalist fit and screen audit | Original TopoLab clean-revision execution of 24 quality-feasible uniform references, three fixed fits, twenty diagnostic validation labels, and 168 fully charged matched outcomes, independently recomputed in `docs/validation/b2_28_expanded_generalist.md` | All three seeds passed the bounded development Gate with zero new-panel failures; separate larger confirmation and final Gates remain required, generated artifacts remain outside Git, and final evidence stays sealed |
| 2026-09-29 | B2.29 frozen larger independent development confirmation | Original TopoLab physically disjoint 48-case confirmation of its existing checkpoints and fixed specialist route, with original non-ML comparators, independent quality checks, and full fallback charges | No new fit, numerical solver change, external implementation, dataset, model, or figure; new outcomes remain unopened until the merged protocol and all generated artifacts remain outside Git |
| 2026-09-29 | B2.29 complete independent confirmation and cost audit | Original TopoLab clean-revision execution of 48 quality-feasible references and 432 fixed-policy outcomes, with independent checkpoint, exposure, quality, resource, and charged-time audit in `docs/validation/b2_29_development_confirmation.md` | Seeds 17 and 43 passed the frozen development confirmation; seed 29 and all failed attempts remain reported. B3.1 planning is permitted, later final Gates remain required, and no external source or generated artifact enters Git |
| 2026-09-30 | B3.1 versioned ML contract and final exposure boundary | Original TopoLab preregistration of its B2-supported weighted generalist/specialist method, fixed controls/ablations, 752-case catalog, budget-insensitive historical exposure ledger, validation-only selection, paired final statistics, replication, and finite stopping rules | Metadata-only independent audit reproduced the historical M3 catalog and verified zero new-role exposure intersections; no external implementation, new source, solver call, label/checkpoint read, fitting, or final outcome; generated audit/catalog/ledger files remain outside Git |
| 2026-09-30 | B3.2 frozen catalog and artifact-access guards | Original TopoLab metadata reconstruction from its published M0/M2/M3/B2 case rules, exact B3 memberships and budget-insensitive fingerprints, and consumer-specific checksum/read guards with complete-population checks | Catalog/ledger bytes match the independent B3.1 audit exactly; guard tests use synthetic callback bytes only. No external code/source, generated label/checkpoint read, solver execution, fitting, or final outcome; generated metadata remains outside Git |
| 2026-09-30 | B3.3 guarded label/reference materializer | Original TopoLab versioned data/artifact/index contracts, shared B2.4 numerical adapters, guarded external IO, charged recovery/audits and clean merged-source CPU entrypoint | Synthetic FEM states and interruption/IO spies test implementation boundaries; one historical B2.4 before/after label is byte-identical. No production B3 optimization, fit, final artifact, external source or copied implementation; generated parity/test artifacts remain outside Git |
| 2026-09-30 | B3.4 complete production data and resource audit | Original TopoLab clean-merged-source uniform regeneration of 560 labels and 48 screening references, plus complete independent metadata, FEM, float32 sensitivity, artifact and cumulative resource acceptance calculations in `docs/validation/b3_4_data_gate.md` | Gate B3 passed with all 608 outcomes and zero failures; no external implementation, model fit, final artifact access or acceleration claim. Generated labels, traces, indices, profiles, audit code and receipts remain outside Git |
| 2026-09-30 | A2.1 serialized local worker protocol | Original TopoLab versioned JSON-line manager/worker contract, one separate Python process per active numerical run, cooperative cancellation, progress/result validation, and process-exit failure handling | No upstream code, numerical intervention, queue framework, generated data, or model artifact introduced; A2.2 durable ownership and recovery remain separate |
| 2026-09-30 | A2.2 durable run ownership and schema migrations | Original TopoLab SQLite compare-and-swap claims, leased manager ownership, heartbeat, fenced writes, queued-record recovery, crash handling, and numbered transactional schema upgrades | No upstream source, numerical method, queue service, dataset or model artifact introduced; optimizer checkpoint/resume remains a later separate contract |
| 2026-10-01 | B4.1 fixed fitting and artifact implementation | Original TopoLab equal-case validation MSE, fixed recipe/membership adapter over its own B3 labels, deterministic CPU fits, checksum-bound Safetensors selections and charged single-writer recovery | Reuses the independently implemented B2 encoder/network/batch schedule; no external code, label, model, result or figure imported. Production execution follows a clean merged runner revision; screen and final evidence remain separate |
| 2026-10-01 | B4.1 complete fixed fitting and independent artifact audit | Original TopoLab clean-merged-source execution of the twelve preregistered CPU fits, independent label/checkpoint/history/selection verification and cumulative resource-floor acceptance in `docs/validation/b4_1_fixed_fitting.md` | All twelve fits and 1,902 attempted epochs passed the bounded fitting Gate; 24 generated artifacts and all audit receipts remain outside Git. No new solver outcome, screening or final artifact access, primary selection or acceleration claim |
| 2026-10-01 | B4.2 fixed screen and prospective freeze implementation | Original TopoLab guarded 528-label streaming NN setup, fixed fifteen-method queries, compact independent terminal witnesses, atomic charged case recovery and validation-only primary selection over its own frozen B3 contract and B4.1 fits | Reuses the independent encoder, network, projection, SIMP and quality equations without numerical changes. Synthetic boundary tests precede clean-merged-source production execution; no external code, label, model or result imported, and final evidence stays sealed |
| 2026-10-01 | B4.2 complete fixed development screen and independent audit | Original TopoLab clean-merged-source execution of all 48 fixed cases / 720 outcomes, guarded independent 528-label NN audit, 745 terminal witness checks and complete charge/selection/resource verification in `docs/validation/b4_2_development_screen.md` | Gate B4 failed with no primary or freeze. All 25 candidate failures and successful paid fallbacks, the supplemental audit's pre-byte guard rejection / permanent flag, and 9,869.911762 seconds remain retained externally. No retiming, extra fit, numerical change, final access or acceleration claim |
| 2026-10-01 | B4.3 frozen failure/cost diagnosis and reader | Original TopoLab checksum-bound read-only decomposition of its retained B4.2 terminal witnesses, charged phases, identical-model repetitions and optimistic cost bounds | No external implementation or new numerical evidence; synthetic tests cover failure preservation, root/byte boundaries and quality-cause separation. Generated diagnosis and audit receipts remain external; B4 stays failed and B5 stays sealed |
| 2026-10-01 | B4.3 complete read-only mechanism and timing audit | Original TopoLab guarded diagnosis of 48 exposed cases / 720 outcomes and 162 identical-model pairs, independently reproducing 745 terminal statuses, failure causes and complete cost arithmetic in `docs/validation/b4_3_failure_cost.md` | Identified timing dispersion, two converged generalist compliance gaps and one generalist nonconvergence; recommends a new finite timing/checkpoint repair before fresh generalist evidence. Original indices, cases and permanent failures remain unchanged; no solver, fit, final access or acceleration claim |

| 2026-10-01 | B4.4 finite engineering protocol, query envelope and bounded journal | Original TopoLab complete wall/process-CPU measurement, fixed-size durable heartbeat, immutable chained publication and charged single-writer recovery, with a preregistered exposed-case sentinel | No external implementation copied; original numerical/model/quality contracts remain unchanged. Tests use synthetic states and a subprocess crash; new sentinel artifacts remain external and cannot establish acceleration |

| 2026-10-01 | B4.4 complete matched recording sentinel and independent resource audit | Original TopoLab new-source engineering experiment on six exposed cases, four unchanged models, 76 counterbalanced queries and 100 independently re-solved terminal states, recorded in `docs/validation/b4_4_engineering.md` | Exact prior numerical/failure identity retained; compact progress reduced callback/query wall in the frozen checkpoint-stress fixture. All artifacts remain external, 2,406.653985 seconds and 705,953,792-byte peak stayed within limits. No fit, label/final access, historical retiming or learned acceleration claim |

| 2026-10-01 | B4.5 finite sensitivity-weighted terminal generalist | Original TopoLab combination of its audited terminal sensitivity weights and fixed case-normalized objective, separate artifact identity, exposure-disjoint cohort and compact charged runner | No external code, data, model or figure imported; preserves old failures and numerical limits. Synthetic objective/gradient, artifact, membership, timing and Gate tests precede production from clean merged source; final evidence stays sealed |

| 2026-10-02 | B4.5 complete weighted-terminal development evidence | Original TopoLab three-seed fixed fits, 48 exposure-disjoint references, 576 fully charged queries and separate 644-terminal-state/selection/arithmetic/resource audits from clean merged `ed1acd4aa60fba62607874f6c888663747c1c595`, recorded in `docs/validation/b4_5_weighted_terminal.md` | Bounded development Gate passed for W/17 and W/43; W/29's two converged quality failures remain charged and retained. Primary W/17 awaits larger independent confirmation; 7,578.184891 seconds and 453,132,288-byte peak stayed within caps. Original inputs/failed flags unchanged; generated artifacts external; no final access or end-to-end acceleration claim |

| 2026-10-02 | B4.7 spatial-objective rollback contract and runner | Original TopoLab physically disjoint development catalog, fixed P/17 policy and matched P/W/C/non-ML Gate; shares the existing charged execution loop with B4.6 | No new model fit, upstream code, external dataset or final artifact access; historical P/W failures stay retained; generated evidence remains outside Git |

## B4.6 independent development confirmation

The new confirmation contract/cohort, immutable upstream receipt checks,
fixed-primary decision and shared query publication/audit helpers were derived
from TopoLab's independently implemented B3/B4.5 contracts and measured
B4.5 evidence. No new external source or Hack3D code, structure, comment or
figure was consulted. The 96-case plan is development metadata; execution
and generated records remain external and require a clean merged revision.
The shared helpers preserve B4.5's full timing/recording and quality boundaries.

B4.6 executed only from clean merged revision
`a6c01acccebdd2e02c4155a1a0b4abe83a755dae`, with unchanged B3/B4.1/B4.5
inputs. The complete 96-reference/1,152-outcome cohort and its 1,291 independent
terminal/classification checks are recorded in
`docs/validation/b4_6_development_confirmation.md`. All upstream indices and
B4.5 receipts remained unchanged. The confirmation Gate failed and every
candidate failure/fallback remains retained; no final artifact was accessed.
The next rollback proposal is based on these independently derived TopoLab
controlled comparisons and is not executed or claimed passing here.

## B4.7 bounded spatial-objective rollback evidence

B4.7 executed from clean merged `ea7e56ada9d552954f95756f59af16debea694e2`
with unchanged B4.1 P/C/S and B4.5 W checkpoints. Its 48 fresh references,
576 fully charged outcomes, 626 production audit units and independently
recomputed 646 terminal states/classifications are retained in
`docs/validation/b4_7_spatial_rollback.md`. The fixed P/17 repair Gate passed;
P/29's three failures and P/43's one remain charged and retained. Total final
charge was 6,536.080252125 seconds and peak RSS 829,194,240 bytes. The failed
1.60-second sandbox runtime preflight preceded all model/label/solver work,
remains retained and is additionally charged. All upstream indices/receipts
remained unchanged. No new external source, fit, label, numerical convention,
checkpoint selection, upstream code or final artifact was used. Generated
records and independent audit sources remain external. This is bounded repair
evidence; independent B4.8 confirmation remains required before any compatible
final contract and B5. Historical B4.2/B4.6 failures remain failed.

## B4.8 independent rollback confirmation contract

The B4.8 larger catalog, receipt guard, fixed-primary Gate and execution
wrapper derive solely from original TopoLab B4.7/B4.6 contracts and measured
B4.7 evidence. Its six-position grid completes geometric mirrors of the
previous three positions; its fixed new volumes are chosen from metadata
before any new numerical work. Existing shared charged execution and query
quality are unchanged. No external code, data, fit or final artifact is used.
Execution requires the clean merged contract/runner; generated records remain
outside Git. Historical failed Gates and every P/W failure remain retained.

## B4.8 complete independent confirmation evidence

B4.8 executed from clean merged `c185caffd5f3b3cd16b2f2f80948caee1e836784`
after contract/runner PR #115 passed all required CI. All 96 new uniform
references, 1,152 fixed outcomes, 1,250 production audit units and 1,295
independent terminal/classification checks are retained in
`docs/validation/b4_8_rollback_confirmation.md`. The frozen confirmation Gate
failed: fixed P/17 paid one quality fallback despite passing single-seed speed
and reliability criteria; its prospectively fixed zero-failure requirement
was not met. P/29's four and P/43's one failures remain retained. Final charge
was 14,105.836381712 seconds and peak RSS 1,036,238,848 bytes. Whole-command
floors, all recording receipts and unchanged upstream hashes passed closure.
The entire new cohort is now development-exposed. No new external source,
fit, input label, solver, quality tolerance, checkpoint selection, upstream
code or final artifact was used. Generated artifacts, profiles and independent
audit sources remain external. B4.9 is bounded read-only diagnosis; the failed
confirmation cannot authorize final evaluation or a substituted primary.

## B4.9 bounded confirmation diagnosis contract

The B4.9 receipt guard and arithmetic reader derive only from original TopoLab
B4.3 diagnostic helpers, B4.8 artifacts/contracts and existing quality and
recording conventions. No new external source or Hack3D content was consulted.
The committed protocol binds the complete failed B4.8 population before new
individual outcome reads. It permits no solver, fitting, label/checkpoint byte
reads or final access. Generated diagnosis and independent audit sources remain
external. Its ordered recommendation is a prospective hypothesis; all original
P/W failures, measured costs and the failed fixed-primary decision stay retained.

The first B4.9 metadata preflight from `9dfcd7512b1637dd3b85395578e7a35866782fd4`
incorrectly demanded compact JSON for the original indented plan/release
receipts. It stopped before all journal/outcome/numerical reads. Its 2.31-second
wall plus ten-second allowance is retained and carried into the versioned v2
plan. The v2 guard preserves the exact original SHA-256 bindings and fixes only
serialization validation; scientific analyses, input bytes and caps are unchanged.

## B4.9 complete read-only diagnostic evidence

Active v2 diagnosis executed from clean committed
`714c0035fc227da25c3c8cdff7cc6ac918479aec`. All 96 references, 1,152 outcomes,
1,250 production audit journal units, 1,295 arithmetic quality classifications,
48 strata and 54 same-specialist pairs passed guarded reads and independent
raw-JSON arithmetic audit. The complete acceptance and unchanged failed B4.8
decision are recorded in `docs/validation/b4_9_confirmation_diagnosis.md`.
The new diagnostic charge is 81.608446500 seconds with peak RSS 277,626,880 bytes,
including the retained 12.31-second failed metadata preflight. All eleven B4.8
receipts, four protected indices and original 14,105.836381712-second charge
remain unchanged. No FEM re-solve, model/label byte access, fit, continuation,
new external source or final access occurred. Generated evidence and independent
audit/closure sources remain external. The fixed twenty-update post-plateau
polish is only the frozen diagnostic recommendation for a separately versioned
B4.10 probe; no repair or final acceleration is established here.

## B4.10 fixed candidate continuation implementation (2026-10-03)

The independently implemented TopoLab OC/FEM/filter operations are reused by
one opt-in, candidate-only twenty-update continuation after an original
large-grid y generalist physical-plateau stop. No numerical-anchor source,
uniform data, selected checkpoint or original result is changed. The
[protocol](docs/planning/b4_10_post_plateau_protocol.md) freezes compatibility,
the exposed stop sentinel, conditional disjoint cohort and resource caps
before execution. Numerical tests compare the extension with an uninterrupted
run of TopoLab's unchanged core. No upstream repository/source, comment, figure
or file structure was consulted, copied or translated. This implementation
records no production repair or learned acceleration result.

## B4.10 complete fixed-polish sentinel evidence (2026-10-03)

The frozen probe executed from clean, CI-passed merged TopoLab revision
`fd13aa1c85a05e638ea02e74712c216319c7488d`, with the original six numerical
anchor modules, checkpoints, route and quality tolerances unchanged. Nine
uniform references, 108 queries, 119 numerical/input audit units, 117 policy
units and 132 independent terminal classifications completed. The guarded NN
audit read the complete 528-label training population and twelve fixed
checkpoints. All 24 prepolish witnesses matched immutable B4.8 states; twelve
fixed twenty-update continuations and 96 unchanged query identities passed
policy/independent audits. No new fit or source-label modification occurred.

The sentinel Gate failed: its four known large-y failures were repaired, but
one originally accepted fixed P/17 attempt became nonconverged and paid fresh
fallback. Both fixed-primary charged cost bounds failed. All 48 fresh cases
remain sealed, as do final artifacts; no primary or polish length was replaced.
All eighteen protected historical metadata/index hashes and original charges
remain unchanged. Final charge was 2,106.109270792 seconds and peak RSS
635,076,608 bytes. The complete report is
`docs/validation/b4_10_post_plateau_polish.md`; generated evidence remains at
`/Users/keith1117/Documents/TopoLab-data/b4-10-post-plateau-polish` outside Git.
No external or upstream source, comment, figure or file structure was consulted,
copied or translated. This failed development probe establishes no acceleration
and permits only the next bounded B4.11 read-only failure/cost review.

## B4.11 read-only polish diagnosis implementation (2026-10-04)

The frozen B4.11 reader, independent arithmetic auditor and resource closer
derive only from original TopoLab B4.10 development receipts, witness formats
and unchanged numerical conventions. Their fourteen metadata bindings and
eighteen historical guards are checked before new outcome access. They
reconstruct terminal certificates and complete costs without FEM, model/label
byte reads, polish-length search or final access. No new external scientific
source or upstream code, comments, layout or figures were consulted or copied.
The candidate terminal-witness preservation recommendation is a prospective
mechanism hypothesis; this implementation changes no numerical behavior or
historical scientific decision. Execution and independent evidence follow
only from clean merged source after CI passes.

## B4.11 complete read-only diagnostic evidence (2026-10-04)

Clean merged source `eb248a62829f4fdd3d8f1508421d7e91352da172` completed the
frozen nine-reference/108-query read-only diagnosis after PR #120's final-head
CI passed. A separate stdlib auditor reproduced 132 terminal classifications,
24 prepolish certificates, 48 strata, nine same-specialist pairs and all cost
bounds. It preserved fourteen B4.10 bindings, eighteen historical metadata
hashes and the failed fixed-P/17 decision. The observed convergence regression
occurs at 97 updates despite improved compliance, rather than iteration-cap
exhaustion. Fallback-free arithmetic leaves only prospective guard headroom;
no failure was reclassified or primary replaced.

All new artifacts remain external. Final diagnostic charge is 59.88 seconds
and peak retained kernel RSS 92,798,976 bytes. The initial outer profiler's
sandbox sysctl failure, raw partial profile and explicitly sourced normalization
are retained: complete wall plus the successful diagnostic process's kernel
self-RSS, with no analysis rerun. Independent audit and closure have complete
native profiles; closure reserves thirty seconds and passes its post-exit check.
No solver, fit, model/label byte read, numerical continuation or final access
occurred. All 48 B4.10 fresh cases remain sealed; original charges and failures
remain unchanged. The ordered decision permits only separately frozen B4.12
candidate terminal-witness preservation probing and subsequent independent
confirmation, with uniform still default. No upstream/external code or new
scientific source was consulted or copied.

## B4.12 candidate witness preservation implementation (2026-10-04)

The new contract, candidate-only terminal choice, two-witness recording and
independent raw-JSON audit derive from original TopoLab B4.10/B4.11 evidence
and the existing independently implemented solver and charged runner. The
twenty-update continuation remains unchanged; only a fully paid endpoint
losing its own convergence certificate may return its original converged
candidate witness. No reference-compliance oracle, fit, threshold/length
search, external implementation or new scientific source is introduced.
The fresh 48-case metadata cohort also excludes the still-sealed B4.10 panel.
Clean merged execution follows CI; all generated records remain external,
historical failures remain intact and final evidence stays sealed.

## B4.12 resource-closure arithmetic repair (2026-10-04)

The complete B4.12 numerical and independent audits retained a failed fresh
development Gate. The first resource closer incorrectly required byte-exact
float equality between independently recomputed timing means; their maximum
difference was 2.220446049250313e-16. The repair uses the existing independent
auditor's frozen 1e-14 arithmetic agreement, with exact non-float fields and
Gate flags, and charges retained unsuccessful command profiles from the
execution ledger. It changes no solver, terminal choice, quality/compute
threshold, plan, checkpoint, outcome or scientific Gate. Source review and
CI precede the closure-only recovery; the original failed command, native
profile and every numerical receipt remain retained. No new scientific
source or external implementation was consulted or copied.

## B4.12 complete terminal-preservation evidence (2026-10-04)

Clean merged numerical revision `44cdb7e8b17692bc3b87300b383b478836d2fac8`
passed the frozen nine-reference/108-query exposed sentinel and retained all
48 physically disjoint fresh references and 576 method outcomes. Complete
independent audits checked 1,101 terminal classifications across both panels,
including both candidate witnesses. The fresh Gate failed: fixed P/17 retains
one converged quality failure/fallback; no P primary is eligible. All historical
results, checkpoints, 38 protected metadata hashes, the unused B4.10 fresh
panel and final seal remain unchanged.

The original failed resource-close command remains retained and charged.
CI-passed merged closure revision `5716279c08a47432bd5abcc31b5382ebf84d893e`
performed only read-only resource recovery, preserving 34 original B4.12
receipts/profiles and performing zero numerical retries. Final charge is
8,486.600 seconds and peak kernel RSS 1,017,036,800 bytes, within frozen
limits. See `docs/validation/b4_12_terminal_preservation.md`; all artifacts
remain external. The next slice is only bounded B4.13 read-only preservation
failure/cost review. Uniform remains default, and a passing repair plus
separate independent confirmation are still required before final access.
No upstream/external code or new scientific source was consulted or copied.

## B4.13 read-only preservation diagnosis implementation (2026-10-04)

The thirty-binding reader, separate raw-JSON arithmetic auditor and finite
resource closer derive solely from original TopoLab B4.12 evidence and earlier
independent format/certificate/cost helpers. The frozen protocol retains the
complete sentinel and fresh populations, both candidate witnesses, actual work,
all failure/fallback costs, unchanged fixed P/17 and historical/final seals.
Synthetic tests precede clean merged execution after CI; this implementation
makes no new numerical claim. No solver, fit, threshold/length search, model/
label byte read, external scientific source or upstream code, comment, figure
or file structure is used. Generated diagnosis and receipts remain external.

## B4.13 complete read-only diagnostic evidence (2026-10-04)

Clean merged source `b24e7ee3674ed11711b0a86b5d239d2615ed63c1` completed both
retained B4.12 panels after PR #125's exact-head CI passed. The separate
stdlib-only raw-JSON auditor reproduced all 1,101 terminal classifications,
159 original/endpoint pairs, 96 strata, 36 same-specialist pairs, original Gate
arithmetic and the frozen cost/recommendation analyses. All thirty B4.12
bindings, 38 historical guards, 34 recovery-protected receipts/profiles and
original 8,486.600-second charge stayed unchanged. P/17's fresh original and
endpoint retain convergence but miss compliance quality; optimistic fallback
removal leaves its target mean above 1. All failures and failed Gates persist.

Native whole-command closure charged 107.78 seconds with peak RSS 109,936,640
bytes, retaining the entire thirty-second closer reservation and passing its
post-exit profile check without a failed attempt or retry. No solver, numerical
continuation, fit, label/model byte read, threshold/length search, new scientific
source or final access occurred. The ordered next slice is only B4.14 bounded
generalist reliability/refinement method review before any new repair. See
`docs/validation/b4_13_preservation_diagnosis.md`; generated records remain
external. All unused B4.10 fresh cases and final evidence stay sealed. No
upstream/external code, comments, layout or figures were consulted or copied.

## B4.14 bounded generalist method-review implementation (2026-10-04)

The compact-row reader, independent cost/headroom auditor and resource closer
derive solely from TopoLab's closed B4.13 records and prior guarded arithmetic
helpers. They preserve fixed P/17 and all original controls, failed statuses,
charges and seals. The method matrix consults primary-source abstracts and
Cang et al.'s discussion of direct theory-driven learning
([v3](https://arxiv.org/abs/1807.10787v3)), algorithm-consistent learning
([Rade et al., v2](https://arxiv.org/abs/2012.05359v2)) and per-problem energy
conditioning ([Chen et al., v1](https://arxiv.org/abs/2305.10460v1)). These
motivate hypotheses only; no paper's implementation, architecture, data,
weights, figures or speedup is imported. The prospective current-prediction
compliance objective uses TopoLab's frozen SIMP/filter/adjoint equations and
requires a separate projection-gradient and resource feasibility probe.
No Hack3D source, comments, structure or figures were consulted or copied.
B4.14 implements no numerical loss/gradient, solver call, fit, continuation,
label/checkpoint/final read or acceleration claim. Production follows clean
CI-passed merged source and keeps all generated artifacts external.


## B4.14 complete bounded method-review evidence (2026-10-04)

Execution from clean CI-passed merged source `258423eb5c93af2d31bdcdfc7ac95a844de160d0`
(source PR #127) retained all 684 B4.13-certified compact rows, 159 prior
witness pairs and 96 prior strata. The prior 1,101 terminal classifications
were not repeated. Independent cost/headroom/shadow reconstruction and all
six fixed mechanism dispositions passed; no original outcome/density, label,
model or final bytes, solver, continuation, fit or new label was used.
All ten B4.13 metadata bindings and prior B4.12/historical/recovery guards
remain unchanged. New closed charge is 50.39 seconds and peak retained
RSS 42,287,104 bytes, within 180 seconds / 1 GiB; native post-exit closure proof
fits the full thirty-second reservation without rewriting the closed ledger.
All original failures and charges remain unchanged, including B4.12's
8,486.600-second recovery-inclusive cost and B4.13's 107.78 seconds.
The primary-source context remains limited to the hypotheses recorded above
and in the frozen protocol; no source code, data, weights, figures or speedup
result is imported.
The ordered next slice is B4.15 bounded offline compliance-adjoint feasibility,
separately registered before train-only gradient/volume/cost checks, with no fit
or fresh/final outcome access. It has not started. B4.12 remains failed,
uniform remains default, and all unused B4.10/final cases stay sealed.
See `docs/validation/b4_14_generalist_method_review.md`; generated receipts,
profiles, logs and results remain external and are not committed.

### B4.15 offline compliance-adjoint feasibility implementation (2026-10-05)

The training-only clipped additive projection Jacobian and normalized
current-prediction compliance objective were independently derived from
TopoLab's frozen SIMP/filter equations. The kernel versions a tighter
`1e-12` physical-volume projection separately from the unchanged query path.
A CPU first-order Torch boundary propagates the analytical FEM/filter/offset
adjoint. Synthetic central-difference, clipping, shift/volume and independent
assembly tests exercise the chain; an exact eight-train-case probe and
independent 24-solve auditor are frozen before label access. B4.14's released
method review and the complete B3 index are immutable hashed inputs. No
Hack3D source, structure, comments or figures were consulted or reused; no
new external implementation source was introduced. This implementation
establishes neither a fitted repair nor learned acceleration. Production
results and complete cost closure follow only from CI-passed merged source.


### B4.15 complete numerical probe and negative cost evidence (2026-10-05)

Source PR #129 merged as `2450b0c754f0c9ba1ed17b7ef7cacce913147d81`
after all applicable exact-head CI passed. The complete eight-train-label,
sixteen-fixture, 48 forward/backward, 64 difference and 200 FEM-solve population
passed all 408 independent numerical conditions, maximum directional error
3.3260894088978595e-6. No projection step or numerical tolerance was adjusted
after production access. The frozen prospective fit-cost Gate failed at
60,339.39413004646 seconds versus 7,200; the original maximum-time proxy is
preserved. New charge is 84.33 seconds / peak RSS 510,836,736 bytes, including
whole-command floors and the full 30-second closure reservation. All three
production processes exited zero with no retry. No network fit, checkpoint,
new label/reference, screening/final artifact or unused B4.10 case was opened.
The separately versioned offline projection does not change the query path.
B4.14 and all earlier results/charges/guards are unchanged. The next slice is
B4.16's bounded offline adjoint cost-feasibility review; correctness is no
repair or acceleration claim. See `docs/validation/b4_15_offline_compliance_adjoint.md`.


### B4.16 bounded offline adjoint cost-review implementation (2026-10-05)

The new protocol and read-only review/auditor/closer use only our complete,
closed B4.15 timing/resource JSON, native profiles and prior metadata guards.
All 48 observations, including the first, and the original maximum-time
proxy are preserved. Independently derived diagnostic arithmetic quantifies
unit-cost requirements without changing epochs, populations or any Gate.
Static inspection of our own FEM/projection code identifies possible immutable
setup reuse, with no measured phase attribution or promised saving. No
upstream reference code, new external source, FEM solve, label/model artifact,
fit, retiming or final access is used. Numerical conventions and query paths
are unchanged. Production review follows only from CI-passed merged source;
B4.15 remains cost-infeasible and P/17 unrepaired. See
`docs/planning/b4_16_offline_adjoint_cost_review_protocol.md`.


### B4.16 complete read-only cost evidence (2026-10-05)

The CI-passed merged implementation independently reconstructed all 48
retained wall/CPU observations and 818 cost/identity/boundary conditions.
B4.15's original maximum-wall proxy remains 60,339.39413004646 seconds;
its failed Gate and 84.33-second charge are unchanged. Zero small cost plus
minimum observed large wall gives 13325.669211 seconds with fixed costs,
a diagnostic sample quantity rather than a rigorous performance bound.
All native process CPU/wall/RSS and setup observations remain complete.
The new review charges 55.99 seconds and peaks at 305,807,360 bytes,
including native command floors and the full 30-second closure reservation.
There were no failed production attempts or retries. No FEM call, retiming,
label/model artifact, optimized terminal-state read, fit or final access
occurred. Static setup-reuse hypotheses come solely from our bound source;
no component timing or saving is inferred. No upstream code or new external
source was used. The ordered next slice is B4.17 bounded offline FEM
phase-cost and setup-reuse feasibility probe; it needs its own finite
contract and permits no fitting. P/17 stays unrepaired, all previous
failures/charges remain unchanged, and final/48 unused B4.10 cases stay sealed.
See `docs/validation/b4_16_offline_adjoint_cost_review.md`.

## B4.17 prepared offline FEM probe

B4.17 independently prepares immutable indices, unit Hex8 stiffness, free-DOF
maps and physical-volume weights from TopoLab's own FEM and B4.15 equations.
It preserves fresh density assembly, A3 ordering and numeric factorization,
with an opt-in training-only kernel and six diagnostic phase timers. The
frozen probe reuses eight train cases and sixteen metadata-defined synthetic
fixtures with prior certified normalizers without new label bytes. Independent uncached energy/
Brent-root checks and fixed directional differences test numerical identity.
No upstream code, comments, structure or figures, or new external source, is
used. Source/test completion is distinct from production feasibility evidence;
fixed P/17, all historical failures/charges and final seals stay unchanged.


### B4.17 complete prepared-FEM evidence (2026-10-05)

B4.17 then completed its frozen prepared-FEM probe: eight canonical train
cases, sixteen synthetic fixtures, all 96 paired full Torch measurements,
96 phase intervals and 256 new FEM solves were retained without new label
or model bytes. All 768 independent numerical/gradient conditions and
64 fixed directional differences passed. Immutable setup is reused while
current-density assembly and numeric factorization remain fresh. Its new
full-population/three-seed/200-epoch cost proxy failed: 58,257.457957
seconds versus 7,200, including full-population preparations and all
B4.15/B4.16/current charges. Original Gates and P/17 remain unchanged.
Complete new charge is 112.34 seconds and peak RSS 486,866,944 bytes; see
`docs/validation/b4_17_prepared_fem_probe.md`.
The separately CI-passed merged candidate reuses only immutable own-code
preparation; all changing-density numeric factorizations remain fresh. The
independent auditor uses uncached own FEM energies and Brent projection,
never the candidate assembly/projection/pullback. All first observations,
paired control times, six sequential phase intervals, complete setup and
native CPU/wall/RSS remain retained. No label/model bytes, optimized-state
artifact, fit, query repair, continuation or final access occurred. No upstream
code or new external reference was used. The ordered next slice is B4.18
bounded offline FEM bottleneck and training-objective method review; it
authorizes no fit or search. P/17 and all historical failures stay unchanged.

## B4.18 bounded FEM/objective method-review implementation (2026-10-05)

The thirteen-binding read-only timing/phase reader, separate scalar arithmetic
reconstructor and native resource closer derive solely from TopoLab's closed
B4.17 evidence and prior guarded own-code helpers. The local signed compliance
Taylor hypothesis follows independently from our frozen SIMP/filter adjoint;
it is not a global error bound, implemented loss, fitted repair or query policy.
No external code, data, weights, figures, new scientific source or Hack3D
content was used. The prospective protocol freezes complete populations,
diagnostic sample scenarios, six method dispositions and a finite stop before
production access. Original Gates/charges, fixed P/17 and all final seals stay
unchanged. Execution follows only from separately CI-passed merged source;
generated evidence remains external. No FEM, loss/gradient evaluation, new
label/model artifact, fit, retiming or final access occurs in this slice.


## B4.18 complete read-only method-review evidence (2026-10-05)

Clean separately CI-passed merged source completed the frozen review of eight
canonical training cases, sixteen synthetic states, 96 paired observations,
96 sequential phases and six method dispositions. All 1286 independent scalar
arithmetic/identity/boundary conditions passed. The original prepared
58,257.457957-second proxy and every previous failed Gate/charge stay unchanged.
Large instrumented factorization/pivot wall share is 82.3882%; hypothetical phase
removal is diagnostic sample arithmetic, not a revised Gate or timing bound.
No FEM, benchmark, loss/gradient evaluation, label/model artifact, fit or final
access occurred. Complete native charge is 86.13 seconds and retained peak RSS
301252608 bytes, including the full sixty-second plan/closure/controller
reservation and unchanged closed ledger. The failed static metadata-plan native
timer is retained and pays 12.76 seconds inside that reservation; its RSS is
unavailable and is not imputed. Complete successful native profiles certify the
reported observed peak, with that failed-attempt memory limitation explicit.
All prior hashes and final/unused
B4.10 seals remain intact. The ordered next slice is only separately registered
B4.19 train-only local compliance-surrogate fidelity/gradient/cost feasibility;
no fit or repaired P/17 is claimed. See the complete validation report. No
external source, upstream code, comments, file structure or figure was used;
all new evidence remains external.

## B4.19 local compliance-surrogate probe implementation (2026-10-05)

One training-only signed terminal-state Taylor tangent is independently derived
from our SIMP/filter adjoint and continuous volume projection. The kernel pays
one anchor FEM solve, retains un-clipped signed normalized derivatives and
releases FEM state; it never uses serialized positive/clipped loss weights.
The finite eight-train-case fidelity/gradient/cost protocol, guarded runner,
uncached independent assembly/Brent auditor and native closer authorize no fit,
new label, model read, solver repair or final access. Exact physics and query
quality tolerances remain unchanged. No upstream code, layout, comments,
figures or new external source is used. Generated artifacts remain external.

## B4.19 retained train-only anchor rejection (2026-10-05)

Clean CI-passed merged source invoked the frozen signed tangent once,
but its anchor-compliance versus stored-normalizer rtol1e-9 check
rejected the attempt. No full numerical probe or independent numerical
audit was published; local fidelity and prospective cost are unevaluated.
Failure case, gap, exact label/FEM counts and buffered fields were not
emitted and remain unavailable. Source inspection identifies distinct
serialized float32 physical density and unquantized filtered-anchor
states as a representation hypothesis, not measured diagnosis.

Separate metadata-only traceback/source/guard audit and native early-
stop closure paid 73.93 seconds / 311902208 bytes. Original command,
failure profile, unchanged source, CI cancellations/interruption/retries
and procedural metadata-controller sources remain external. No numerical
rerun, new normalizer/tolerance, fit, new label, model bytes, reference,
continuation or screen/final access occurred. No upstream code or new
external implementation/source was used. Prior failures and charges,
P/17, uniform default and all sealed evidence remain unchanged.
The next slice is B4.20 bounded surrogate correctness review, before
any new numerical invocation. See
`docs/validation/b4_19_local_compliance_surrogate.md`.

## B4.20 stored-normalizer tangent correctness implementation (2026-10-05)

Independently derive the continuous tangent of the existing B4.15 objective
with its stored audited constant denominator. Separately analyze serialized
float32 physical density and the continuous filtered anchor; use the latter's
normalized intercept and signed filter-transpose derivative. Existing v1
checks, labels, numerical tolerances and query behavior stay unchanged.
The frozen eight-train-case correctness panel uses independent uncached Hex8
energy derivatives and Brent projection, with exclusive fsync'ed before-call
FEM/label records and durable partial numerical prefixes. All artifacts remain
external. No upstream code, comments, layout or figures are used. No fidelity,
fit-cost, fitting, learned repair or final claim follows from implementation.

## B4.20 independently audited representation correctness (2026-10-05)

The prospectively fixed stored-denominator/continuous-intercept tangent completed
984 independent numerical conditions on eight guarded train cases,
sixteen synthetic inputs, 64 directions and 32 new FEM solves. Of those
conditions, 983 passed; one directional error exceeded the unchanged 1e-4
threshold, so the frozen correctness Gate failed. Separate stored
physical/continuous anchor analyses showed 6/8 current anchors reject the old
equality; B4.19's actual failed case, gap and counters remain unknown.
Uncached energy/Brent reconstruction and durable before-call journals retain
the complete failed panel. It establishes no fidelity, fit cost, full training
memory or learned repair. New charge 100.30 seconds / 447741952 bytes preserves all
prior failed Gates/charges and P/17. No upstream material or new external
source was used; no model fit, new label, optimization or final access occurred.
See `docs/validation/b4_20_surrogate_correctness.md`. Next is
B4.21 bounded surrogate correctness failure review, not started.

## B4.21 bounded correctness failure-review implementation (2026-10-06)

The frozen complete-panel scalar review and independent Cartesian-neighbor
filter-weight reconstruction derive from TopoLab's own SIMP/filter/projection
equations and retained B4.20 format. Diagnostic root-residual and floating
arithmetic envelopes preserve the original failed Gate and absent side-state
fields; they do not assert a measured cause or replace any observation. No
upstream content, external implementation or new scientific source is used.
Synthetic arithmetic, tampering, independent-weight and resource tests precede
production from clean CI-passed merged source. No FEM, new root, objective
invocation, label/model artifact, fit or final access occurs in this review.

## B4.21 read-only execution evidence

The original TopoLab scalar review retained the complete bound B4.20 failed
panel and independently reconstructed filter weights from Cartesian geometry.
Diagnostic envelope compatibility selects a separate prospective hypothesis;
it does not establish cause or revise the old correctness Gate. All execution
receipts, profiles and scalar payloads remain external; the report preserves
source/plan/hash/resource identities. No external source or upstream Hack3D
code, structure, figure, dataset or implementation was accessed or imported.

## B4.22 stable-projection correctness implementation (2026-10-06)

Independently derive one affine free-set refinement of TopoLab's existing
continuous clipped additive volume projection, with compensated summation.
The stored normalizer, continuous intercept, signed tangent and implicit
cotangent retain their equations and frozen criteria. Existing v1/v2 and query
paths remain unchanged. Reuse only TopoLab's own durable journal, guarded
training lookup, original Hex8 energy auditor and native-resource machinery;
the independent root uses Brent arithmetic rather than the candidate kernel.
The prospectively fixed complete correctness panel retains both original
steps and adds saved offset/residual/kink evidence. Synthetic regression,
complete-panel, tampering and interrupted-call tests precede production.
No upstream content or new external implementation/scientific source is used.
No production label/model artifact was read during implementation; no fit,
local fidelity/cost, learned repair or final claim follows from source tests.

## B4.22 versioned stable-projection execution evidence

The original TopoLab root refinement passed its frozen correctness Gate.
All actual numerical results/prefixes, root scalar evidence and independent
uncached energy/Brent audit remain external. Source, plan, command, native resource
and closure hashes bind the committed report. Every earlier failed Gate, charge
and unknown remains; this does not establish local fidelity/cost, training memory
or learned repair. No upstream material, new external implementation/scientific
source, model fit, generated label or final evidence was accessed.

## B4.23 versioned local-surrogate feasibility implementation (2026-10-06)

Reuse TopoLab's original v3 stable projection and stored-normalizer tangent,
without a new numerical candidate. Restore the prospectively frozen B4.19
finite fidelity/cost population with explicit separate stored/continuous anchor
physics, unchanged approximation/exact thresholds and both original steps.
Our independent uncached Hex8 energy adjoint and Brent reconstruction verify
the full panel without the candidate tangent, projection, pullback, fidelity
or cost functions. Durable label/FEM/root journals retain complete timings and
central/directional prefixes, pending calls and errors; native closure preserves
all prior charges and the original full-population cost formula.
Only TopoLab's independently implemented equations and source are reused.
No upstream content or new external implementation/scientific source is used.
Synthetic public-case inputs precede production; no production label bytes,
model, fit, learned repair, new label/reference or final evidence was accessed
during implementation. Full training memory remains pending regardless of the
finite probe's later outcome.

## B4.23 versioned surrogate execution evidence

The original TopoLab v3 tangent completed its frozen attempt; the feasibility
Gate failed. Actual fidelity/correctness observations, complete first-inclusive
timings, uncached energy/Brent audit, native profiles and durable prefixes stay
external, bound to the committed source/report by hashes. Every original failed
Gate, unknown field and complete charge remains. No upstream content, new
external scientific/implementation source, model bytes, fit, generated label,
reference, learned repair, continuation or final evidence was accessed.
Full training memory and later independent learned confirmation remain pending.

## B4.24 versioned correctness failure-review implementation (2026-10-06)

Independently derive a saved projected-secant decomposition from TopoLab's own
clipped additive projection, signed affine tangent and physical-volume weights.
Read-only arithmetic retains every B4.23 row, original failure identity,
first timing, cost and unknown. A separate Cartesian-neighbor/math.fsum auditor
uses no candidate decomposition, sparse filter, root, FEM or objective function.
Synthetic complete-row, finite-interval clipping, tampering, independent-weight
and paid-resource checks precede access to production numerical evidence.
No new scientific source or upstream Hack3D code, comments, structure, figures
or implementation is accessed or imported. No new numerical invocation, model,
label payload, fit or final access is authorized; all old Gates remain intact.

## B4.24 saved-schema compatibility recovery implementation

The first released read-only attempt stopped because it expected three legacy
names while TopoLab's own B4.23 writer retained surrogate-prefixed names. Preserve
that source, failure and charge. A separately registered literal adapter reuses
the original candidate and independent scalar mathematics, with separate schema
adapters and cumulative original resource caps. Tests inspect the actual original
writer as well as synthetic records. No upstream/external source, changed
numerical method, new root/FEM, tolerance, data/model role or final access occurs.

## B4.24 interrupted execution and unknown native memory

Own-code v1 read-only review stopped on a saved-field serialization mismatch;
its source, unavailable complete result and 16.19-second charge remain. A separately
registered own-code compatibility source passed exact-head/main CI but its
default planning wrapper lost native RSS at sandboxed sysctl kern.clockrate.
The failed profile, wall 4.73, stdout and source version remain; no recovered
arithmetic review/audit was invoked. A separate metadata-only controller
verified immutable identities and 50.53/60 reserved time, retaining 76.19 known
time charge and unknown whole peak RSS. It establishes no scientific acceptance
or complete memory proof. The controllers and logs are bound externally;
the [interrupted report](docs/validation/b4_24_versioned_correctness_failure_review.md)
retains the exact source/CI/failure hashes. No new numerical source, upstream
Hack3D code, data/model payload, fit, altered criterion or final access occurred.
B4.24 remains incomplete pending an explicit resource/execution decision.

## B4.24 owner-approved continuation registration

The owner approved one additional fully paid 60-second execution reserve while
retaining the whole 240-second and cumulative review caps. The v3 wrapper reuses
TopoLab's byte-frozen v1 scalar equations and separate v2 schema adapters; it adds
only prospectively registered resource/source/history boundaries. The two exact
SHA-bound standard-JSON metadata receipts retain their original bytes. Historical
missing RSS remains unknown; only the new continuation can establish its own
complete native memory evidence. Original protocols, interruption, charges and
scientific failures remain. No external implementation, upstream material,
changed numerical criterion, label/model payload, fit or final access occurs.

## B4.24 registered continuation evidence

TopoLab's frozen candidate and separately adapted independent scalar mathematics
completed the original saved panel, with all 2104 predicates and 1728 row-field
comparisons passing. The finite-interval clipping identity preserves original
scientific failures and does not assert a global cause or altered pointwise
gradient. Owner-approved v3 time/native scope closes at 200.98 seconds; missing
historic RSS stays unknown and the original memory proof remains incomplete.
All old sources, interruptions, profiles, charges and numerical fields retain
their identities. No upstream material, new external scientific/implementation
source, numerical root/FEM/objective/gradient/prediction timing, label/model bytes,
fit or final evidence is accessed or imported. Raw evidence remains external.

## B4.25 bounded active-set method-review implementation

The prospective scalar review and separate stdlib auditor derive from TopoLab's
closed B4.24 compact evidence and its original clipped additive projection,
signed tangent and full-population cost equations. They preserve every saved
row, exact failed position, first-inclusive maximum, prior charge and historical
unknown. The finite method matrix recommends preregistration only; it introduces
no numerical objective, root, gradient, fit or changed scientific criterion.
No upstream Hack3D material or new external scientific/implementation source,
label, checkpoint or final artifact is accessed or imported. Synthetic public
scalar records test independent enumeration, immutable failure/cost identities,
metadata roles and native-resource boundaries before merged-source production.
All generated review/audit/resource evidence remains external.

## B4.25 closed scalar method review and immutable prior evidence

The registered read-only review passed 448 predicates and 2222 independently
enumerated scalar/identity/disposition comparisons. It retained every original
row/failure/cost and inherited first timing identity without reopening raw
numerical panels. New complete native charge 80.34, reserve use 40.41/60
and peak 26492928 bytes remain separate from B4.24's 200.98 and all prior charges.
The fixed-set derivative and six method dispositions use only TopoLab's frozen
equations/closed scalar evidence; they implement no new mathematical map,
derivative, criterion, objective, root/FEM or fitted model. All historical
failures/memory unknowns and final/unused-fresh seals remain. No Hack3D material
or new external scientific/implementation source, production label/model or
final artifact was accessed or imported. See the
[complete report](docs/validation/b4_25_active_set_method_review.md).

## B4.26 active-set-aware evidence preregistration

The separately versioned read-only protocol and authored acceptance JSON derive
prospective evidence requirements from our frozen clipped-volume equations and
B4.25's strictly fixed-set derivation. They prescribe independently reconstructed
pointwise cotangents and complete transition-piece intervals while retaining
every old row, step, tolerance, failure and charge. No numerical map, derivative,
root, FEM, model or production artifact is implemented or evaluated in this
slice. The 66/28 checks are document/metadata acceptance, not scientific evidence.
Local fidelity, complete first-inclusive costs and full training-memory bounds
remain separate future prerequisites. No new upstream source/code/figure or
external scientific reference was read or copied. See the
[protocol](docs/planning/b4_26_active_set_preregistration_protocol.md) and
[validation report](docs/validation/b4_26_active_set_preregistration.md).

## B4.27 independent active-set evidence implementation

The in-memory pointwise and exact rational interval certificate checker derives
solely from TopoLab's frozen clipped-volume equations and B4.26 criteria.
An independently authored exhaustive rational small-vector fixture oracle and
analytic/tampering tests use no candidate checker or production artifact reader.
No upstream Hack3D code, comments, structure, figure, new scientific reference,
external implementation, production label/model or final evidence is consulted
or imported. The original numerical kernels/queries and historical evidence
stay unchanged. Synthetic software acceptance is not numerical-panel correctness,
fidelity, feasible full costs/memory, learned repair or acceleration. See the
[protocol](docs/planning/b4_27_active_set_evidence_protocol.md) and
[report](docs/validation/b4_27_active_set_evidence.md); generated software receipts
and command profiles remain external.

## B4.28 bounded active-set numerical evidence implementation

The separately owner-authorized finite numerical contract implements exact
rational volume-offset tracing from our own frozen equations. The independently
authored auditor assembles density filters, solves numerical volume roots and
reconstructs uncached FEM energy/adjoints with the established original public
FEM primitives; it calls no candidate projection/tangent/certificate classifier.
Synthetic public fixtures compare complete partitions to the independent small
exhaustive oracle and exercise full pipeline/legacy fields, access guards,
durable failed calls and native budget limits. The original v3/root/objective
and B4.27 checker remain unchanged. No Hack3D material, external implementation
or new scientific reference is consulted or copied. Production evidence is
pending clean merged CI-passed source; no label/model/production payload was
opened during authoring. See the [prospective protocol](docs/planning/b4_28_active_set_numerical_evidence_protocol.md).

## B4.28 pre-production CPU pool boundary correction

Source review before first production access found that the independent auditor
indirectly imports Torch through the established guarded label reader. Both
producer and auditor now explicitly set and verify intra/inter-op pools at one
and retain those observed values in durable runtime events. Public metadata-only
abort regressions verify zero input/numerical calls and rejection before any
output when the settings are not frozen. This changes no mathematical map,
tolerance, case, role, budget or seal and opens no production artifact.

## B4.28 closed finite numerical evidence

The separately approved bounded producer and independently implemented auditor
use the same original TopoLab v3 equations/public FEM primitives and frozen
eight expanded-train population. New integrity PASS, LOCAL PASS; all
prior failures/costs/unknowns remain. Generated input/output/journal/profile
evidence stays external and is hash-bound by the
[report](docs/validation/b4_28_active_set_numerical_evidence.md). No Hack3D
material or new external scientific/implementation source was read or copied.
No model fitting, novel label/reference, retiming, learned repair or final
access occurred. Full costs/memory and learned confirmation remain unresolved.

## B4.29 prospective read-only outcome review

The [finite protocol](docs/planning/b4_29_active_set_outcome_review_protocol.md)
and [contract](docs/planning/b4_29_active_set_outcome_review_contract.json) bind
only compact scalar/native/resource metadata from closed B4.28. The standard
library float reviewer and separately implemented Decimal audit enumerate
counts/summary predicates and inherited cost without raw arrays or numerical
kernels. No new external scientific or implementation source, Hack3D material,
label/reference or model was read/copied. Metadata execution waits for clean
locked merged source and exact-head/main CI; old failures and unknowns remain.

## B4.29 closed read-only scalar evidence

One standard-library reviewer and independent Decimal audit read only fixed
B4.28 compact scalar/native/resource metadata under the prospective contract.
The [report](docs/validation/b4_29_active_set_outcome_review.md) binds original
and new hashes, retained costs and unknowns. No upstream code, new scientific
source, raw arrays, labels/references, models or numerical kernel was accessed.
Metadata review cannot establish learned repair, acceleration or full fit-memory.

## B4.30 prospective fixed-checkpoint reflection repair

The [protocol](docs/planning/b4_30_z_reflection_repair_protocol.md) derives
a two-element z-reflection average from TopoLab's own isotropic elasticity,
structured mesh and Euclidean-filter equations. The same original P checkpoint
predicts the original and re-encoded mirror; the inverse-mapped raw float32
predictions are averaged before the unchanged projection/refinement. No
Hack3D material, external code, architecture, weight, data, figure or new
scientific source was consulted or imported. Geometric equivariance does not
establish the failure's cause or an improvement in quality or complete cost.
The owner approved one new finite contract, fixed primary17 and unchanged
seals; old exact-FEM failures/cost/memory gaps remain. Production awaits
clean locked merged CI-passed source.

## B4.30 interrupted entry and strict-source correction

The [failed-prefix report](docs/validation/b4_30_z_reflection_repair.md) records
zero numerical/model/label calls: the legacy clean-source entry rejected the
preserved untracked owner documents. The correction checks all dirty paths
before output creation/input preparation and leaves that legacy requirement
unchanged. Same P weights/reflection formula, Gates, roles and seals remain;
no new scientific source/upstream material or model/label payload was consulted
or imported.
Original failed native profiles and191.9666532080154866 charge remain; no repair
or acceleration evidence is claimed. A clean independent checkout contains only
TopoLab's own committed source. A separate paid continuation requires an owner
decision covering the consumed one-campaign limit before new numerical access.


## B4.30 owner-approved paid source compatibility

The separately versioned [v2 protocol](docs/planning/b4_30_paid_continuation_protocol.md)
binds the owner's one paid continuation following zero-numerical preflight.
Original TopoLab reflection/Gate/population mathematical source stays unchanged;
only versioned clean-source access, immutable-prefix identity and cumulative
Decimal resource accounting change. Both failed cost and full-chain reserves
remain paid. No new external scientific/implementation source, Hack3D material,
model/label payload, fit, result adaptation or final evidence was used during
authoring. New production waits for clean locked merged main after all CI.

## B4.31 scalar review and source preregistration

The owner authorized one bounded read-only reflection failure/cost review. The
[protocol](docs/planning/b4_31_reflection_failure_cost_review_protocol.md) and
[contract](docs/planning/b4_31_reflection_failure_cost_review_contract.json) bind
eight existing compact JSON files by published SHA before any production access.
Schema preparation used TopoLab's committed B4.30 writer source and the actual
prior chat's reporting commands; no new production metadata was opened during
authoring. Original float review and separate Decimal/status enumeration use
only the Python standard library and unchanged TopoLab scalar IO/native helpers.
No new external scientific/implementation source or Hack3D material was consulted
or imported. Synthetic software checks do not rerun FEM/prediction or establish
learned repair, causality, full fit memory or acceleration. Every old failure,
unknown, cost, fixed primary and sealed boundary remains. Production awaits
whole-clean locked merged main after applicable exact-head/main CI.

## B4.31 completed scalar evidence boundary

Clean locked source PR166/main4a51ebe6fbe6 and all exact-head/main CI preceded
the only eight-input review and separate Decimal audit. Metadata118/118 and
430/430 PASS, own native resource PASS; no payload/model/label, predictor/FEM,
fit, retiming, root/objective search or final/fresh access. The
[report](docs/validation/b4_31_reflection_failure_cost_review.md) retains all
failed P/R statuses, mean versus sum, the original immutable cost ledger,
full reserves and every unknown. Small attempted-compliance changes do not
establish a cause or repair; four historical predicate passes already occurred
in matched P. No new external scientific or implementation source or Hack3D
material was used. Original source-premerge-driver failure and subsequent
postmerge verification retain distinct timing, without a premerge PASS claim.
No scientific tolerance/model/population/role/seal changed. B4.32 is only a
proposed later read-only method review/preregistration requiring new authority.

## B4.32 reciprocal-energy method preregistration provenance

B4.32 reviews six fixed method dispositions using fifteen starting-main-bound
versioned inputs. No generated evidence replay, label/model/raw payload,
objective/gradient/FEM/projection/root, fit or final/fresh access occurs.

New primary reference: Peeters, Hong and Abdalla,
[A compliance approximation method applied to variable stiffness composite optimisation](https://link.springer.com/article/10.1007/s00158-018-2007-2)
(2018), sections3–4/equations19–25. Its complementary-energy principle motivates
a fixed-admissible-force reciprocal approximation. Composite/truss performance,
code, figures and optimizer/damping choices are not imported. The conditional
discrete PSD/SIMP Cauchy–Schwarz proof, square-gap identity and residual-bound
obligation are independently derived from TopoLab's existing equations.
No new Hack3D comparison or content is used.

The [protocol](docs/planning/b4_32_generalist_method_preregistration_protocol.md)
and [authored contract](docs/planning/b4_32_generalist_method_preregistration_contract.json)
preregister one unimplemented training-only hypothesis and eight future public
toy fixtures. Exact anchor equilibrium is essential; floating residuals need
an independent admissibility/spectral/rounding certificate. No real-state
upper bound, cost feasibility, P17 repair or learned acceleration is claimed.
Old signed-tangent/exact-FEM/reflection failures, costs and unknowns remain.
B4.33 software implementation is only proposed under a separate contract.

## B4.33 finite public reciprocal-energy software provenance

The [software protocol](docs/planning/b4_33_reciprocal_energy_evidence_protocol.md)
and [contract](docs/planning/b4_33_reciprocal_energy_evidence_contract.json) were
frozen before implementation/evaluation. Eight small original authored systems
retain B4.32's exact matrices/loads/densities/materials. Original stdlib candidate
uses the already derived reciprocal energy and exact input validation; a
separately authored Fraction oracle independently assembles/solves1x1/2x2 and
checks compliance/adjoint/square-gap. No candidate imports in the oracle/auditor.
Toy C_s=(11/10)*C_star independently exposes the stored-normalizer distinction.
No new external scientific/implementation source, Hack3D content, figure, code,
label/model/old generated payload, real FEM or learned result was consulted or
imported.47 software tests and849 predicates establish public toy algebra only;
real admissibility/fidelity/cost/memory/learned repair remain unresolved.

## B4.34 conditional real-admissibility and full-cost preregistration

The [protocol](docs/planning/b4_34_admissibility_full_cost_preregistration_protocol.md)
and [authored contract](docs/planning/b4_34_admissibility_full_cost_preregistration_contract.json)
derive one conditional uniform coercivity route and residual-energy enclosure
from TopoLab's own B4.32 PSD/SIMP proof and B4.33 exact toy boundary. For the
same intended operators, certified G>=lower_G*I>0 and E>=E_min give a uniform
lower spectral bound; triangle inequality bounds f using the approximate anchor's
f+r energy plus independently enclosed residual. Outward arithmetic and SAME
stored-normalizer lower enclosure remain unimplemented blocking obligations.
The corrected bound is diagnostic, never a replacement objective/gradient or
approximate anchor-equality claim.129/43 checks accept documentary consistency
only; no real certificate, numerical payload/FEM/integration/fit/timing or
scientific repair is performed. Full costs/unknowns and PENDING4GiB remain.
No new external scientific/implementation source, Hack3D code/comment/structure/
figure, dataset, model or final evidence was consulted or imported. Historical
equation references and frozen records retain their identities.

## B4.35 finite public diagnostic certificate software provenance

The [protocol](docs/planning/b4_35_public_admissibility_certificate_protocol.md)
and [contract](docs/planning/b4_35_public_admissibility_certificate_contract.json)
freeze8 original authored rational systems/16 points before implementation.
Independent derivation from TopoLab's B4.34 proof uses exact principal minors/
uniform coercivity/residual/energy, fixed80-bit integer sqrt enclosures and
exact represented-binary64 comparisons for outward diagnostic bounds. Separate
stdlib oracle/auditor uses its own intended assembly/1x1 or2x2 elimination and
exact inequality checks without candidate helpers.58 tests/394 predicates pass
only these public numbers. No new external scientific/implementation source,
Hack3D code/comment/structure/figure, real label/model/raw evidence, FEM,
network integration or fit was consulted/imported. Corrected bound changes no
original loss/gradient. Real certificates/cost/memory/learned repair remain
UNKNOWN_STOP/failed/PENDING; all historical frozen evidence/seals stay.

## B4.36 conditional intended-operator witness provenance

The [protocol](docs/planning/b4_36_certificate_limitations_real_route_protocol.md) and
[contract](docs/planning/b4_36_certificate_limitations_real_route_contract.json) freeze a finite text-only review.
Independent derivation uses the triangle/operator-norm inequality for a fixed
represented energy factor A_hat and left-inverse witness Y, Frobenius upper
bounds and a separately certified intended-operator error delta_plus. This gives
the conditional lower bound ((1-eta_plus)/M_plus)^2-delta_plus for SAME intended G,
with independent intended element PSD and strictly positive directed transfer.
The document/Decimal audits141/96 verify schema, identities and retained criteria;
they construct/evaluate no witness or real FEM certificate. No new external
scientific/implementation source or Hack3D content was consulted. Historical
frozen conventions/records and source stay; B4.35's public arithmetic scope is
unchanged. This is no real algorithm, loss/gradient change, cost/memory proof,
learned repair or permission to access sealed evidence.

## B4.37 authored public coercivity-witness software provenance

The [protocol](docs/planning/b4_37_public_coercivity_witness_protocol.md) and
[contract](docs/planning/b4_37_public_coercivity_witness_contract.json) freeze10 original rational systems and one
prescribed factor/left-inverse witness each before implementation/evaluation.
Independent derivation from TopoLab's B4.36 norm inequality uses intended
element principal minors, exact intended-to-factor/residual/witness Frobenius
squares, fixed80-bit integer sqrt enclosures and outward binary64 directed
lower stages. The separate stdlib oracle imports no candidate and audits exact
squared endpoints and intended G-lower_G*I principal minors; it uses no shared
sqrt helper or numerical solver.66 tests/217 independent predicates establish
only6 prescribed public certificates and4 prescribed stops. Positive G may stop
with a conservative witness. No new external scientific/implementation source,
Hack3D code/comment/structure/figure, actual label/model/payload/FEM/construction,
integration or fit was consulted/imported. Real intended representation/element
proof/construction/cost remain UNKNOWN_STOP, original loss/gradient unchanged,
P17 unrepaired/full fit PENDING4GiB/all old evidence/charges/seals remain.

## B4.38 public-witness limits and prospective construction obligations

The [protocol](docs/planning/b4_38_public_witness_limitations_real_construction_protocol.md) and
[contract](docs/planning/b4_38_public_witness_limitations_real_construction_contract.json) freeze a text-only review of28 TopoLab source
identities. Original derivation from our engineering-Voigt Hex8 energy equations
describes one prospective canonical quadrature energy stack and unpivoted QR/
triangular left inverse, with separate intended PSD/representation/outward-error
proofs. No factor, inverse, geometry, numerical value or executable real algorithm
is constructed/evaluated.197/135 document/Decimal checks verify schema, preserved
identities/criteria and stops only. B4.37's public evidence and conservative
positive-operator stop remain; diagnostic bounds change no original loss/gradient.
No new external scientific/implementation source or Hack3D content was consulted
or imported. Real certificates/cost/memory remain UNKNOWN_STOP/PENDING4GiB,
all-paid infeasible/scientific FAIL/P17 unrepaired; all old costs/failures/seals stay.

## B4.39 original public fixed-construction witness provenance

The [protocol](docs/planning/b4_39_public_fixed_construction_witness_protocol.md) and [contract](docs/planning/b4_39_public_fixed_construction_witness_contract.json)
freeze10 original rational matrices/stacks before implementation/evaluation.
The independent scalar Householder reflection derives v=x-alpha*e_k,
H=I-2*v*v.T/(v.T*v); left updates form R and Q.T, fixed positive-diagonal signs
and scalar backward substitution construct ONE represented Y=R_inverse*Q.T.
Every binary64 operation/order is pinned and recorded; no external implementation,
scientific source or Hack3D code/comments/structure/figures consulted/copied.
The separately written stdlib oracle consumes all692 operations with exact
adjacent midpoint RN-even proofs (sqrt by squared midpoints), separately proves
intended element PSD, both error components and complete error/left residual/
Y norms, all fixed80-bit/outward lower stages and intended shifted principal
minors.72 tests/993 predicates certify only7 authored public witnesses with3
prescribed stops. Rational A0 does not prove real Hex8 energy/irrational/assembly
representation or real construction. No actual payload/FEM/geometry/integration/
fit; original loss/gradient/normalizer and all failures/cost/memory/seals stay.
Real certification/cost UNKNOWN_STOP/full fit PENDING4GiB/P17 unrepaired remain.

## B4.40 intended representation and constructed-public limitations

The [protocol](docs/planning/b4_40_constructed_witness_limitations_real_representation_protocol.md) and
[contract](docs/planning/b4_40_constructed_witness_limitations_real_representation_contract.json) freeze38 text/hash inputs before one primary205 and one separate
stdlib/document/Decimal171 static audit. Original derivation from TopoLab's frozen
rectangular Hex8/engineering-Voigt/isotropic equations specifies accepted-bit
intended geometry, positive upper constitutive factor, Gauss polynomial exactness,
canonical energy/scatter identity, BOTH factor errors and DISTINCT actual
assembly/load/residual error obligations. Gram expansion and triangle/norm
inequalities supply conditional enclosures only; no real scalar/matrix/FEM/
interval/factor/witness is evaluated. Full public Q_transpose storage prevents
a thin-QR memory assumption. No new external source or Hack3D material consulted
or imported. Document consistency establishes no real representation/certificate/
cost/memory or learned repair; original loss/gradient/criteria/failures/charges/
UNKNOWN/seals remain. See [report](docs/validation/b4_40_constructed_witness_limitations_real_representation.md).

## B4.41 public intended-versus-represented arithmetic

The [protocol](docs/planning/b4_41_public_intended_representation_enclosure_protocol.md) and
[contract](docs/planning/b4_41_public_intended_representation_enclosure_contract.json) freeze41 starting-main text/hash inputs, twelve original public scalar-expression
systems and accepted IEEE bit words before implementation/evaluation. Exact
Fraction endpoint arithmetic and fixed80-fractional-bit sqrt enclosures follow
independent squared-endpoint derivation; Gram expansion and Frobenius/spectral
inequalities yield conservative diagnostic bounds for BOTH intended/represented
errors and the complete error. The independent stdlib oracle uses its own integer
binary-search root and exact adjacent midpoint/squared-midpoint RN-even proofs,
imports no candidate/TopoLab/producer/shared arithmetic, and checks935 predicates/
66 nodes. No new scientific source, external algorithm or Hack3D code/comments/
structure/figures consulted/copied. Twelve authored systems establish8 public
enclosures and4 prescribed stops only; no real FEM/assembly/PSD/coercivity/Y,
certificate/cost/memory or learned repair claim. Original loss/gradient/normalizer,
all frozen failures/charges/UNKNOWN/reserves/seals stay. See [report](docs/validation/b4_41_public_intended_representation_enclosure.md).

## B4.42 documentary assembly/residual obligations and failed checker

The [protocol](docs/planning/b4_42_public_enclosure_limitations_real_assembly_protocol.md) and
[contract](docs/planning/b4_42_public_enclosure_limitations_real_assembly_contract.json) freeze48 texts before reviewer implementation/calls.
Independent derivation from existing TopoLab intended-operator/triangle/Frobenius
inequalities separates actual assembly/load/residual-product/norm rounding from
Gram representation error. All formulas remain unimplemented/unevaluated TEXT;
no real executable/value/cost/memory certificate. Primary formal review FAIL196
at an erroneous shortened-status equality, no retry; separate document/Decimal
audit179 PASS after full-status correction BEFORE its first call. Original failed
source/receipt and independent pre-correction/freeze remain external. No new
external scientific/implementation source or Hack3D code/comment/structure/figure,
payload/model/label/numerical trace/real FEM was consulted/imported. All original
loss/gradient/normalizer/criteria/failures/charges/UNKNOWN/seals remain. See
[failed report](docs/validation/b4_42_public_enclosure_limitations_real_assembly.md).

## B4.43 public assembly/residual diagnostic provenance

Ten tiny scalar contribution lists are authored independently before evaluation;
no mesh/material/actual FEM data/reference source is consulted. Existing original
TopoLab B4.41 scalar intended-interval helpers retain their exact frozen bytes.
The separate oracle carries the project's existing independent integer-bisection/
IEEE midpoint proof method in its own source, with no candidate/producer/shared
numerical import. Triangle and Frobenius-dominates-spectral inequalities transfer
separate operator/force/evaluation/norm errors without PSD/Gram or loss changes.
The formal launch and missing-receipt audit failures remain negative evidence,
distinct from94 passed regression tests. No Hack3D code/comments/layout/figures,
external new source, actual geometry/FEM/fit/access or acceleration claim.

## B4.44 public assembled-residual limitations and real prerequisites

The [protocol](docs/planning/b4_44_public_assembled_residual_limitations_real_certification_protocol.md) and
[contract](docs/planning/b4_44_public_assembled_residual_limitations_real_certification_contract.json) freeze72 starting-main public TEXT/hash inputs,14 literal compact metadata and four
primary-only archived failure source/log texts before new reviewers. Independent
stdlib text/hash/AST/Decimal50 implementations establish407/332 document predicates;
no old checker/producer/oracle is imported or executed. Existing original TopoLab
triangle/Frobenius/Gram/energy derivations remain conditional TEXT obligations,
not evaluated real representation/assembly/residual/coercivity/cost certificates.
The old import failure and missing runtime are retained without inferred cause,
new numerical campaign or retry. No new external scientific/reference source or
Hack3D code/comments/layout/figures consulted/copied. All loss/gradient/SAME
normalizer/criteria/failures/unknowns/charges/reserves/seals remain. See [report](docs/validation/b4_44_public_assembled_residual_limitations_real_certification.md).

## B4.45 public launch-context and immutable-receipt software

Four tiny original marker texts and12 cases are authored independently before
implementation. Original stdlib exclusive/fsynced parent-child receipts and
PathFinder/checked-byte probe execution establish bounded origin/context and
failure-preserving software behavior; separate stdlib audit277 checks receipt
identities without candidate/TopoLab/shared imports. No external algorithm,
Hack3D code/comments/structure/figures, real FEM/data/model/fit or numerical
source is consulted/imported. New runtime observations do not reconstruct
B4.43 runtime/cause; every old scientific/formal failure/cost/seal remains.
See [report](docs/validation/b4_45_public_launch_context_immutable_receipts.md).

## B4.46 public launch limitations and fresh arithmetic prerequisites

The [protocol](docs/planning/b4_46_public_launch_limitations_arithmetic_prerequisites_protocol.md) and
[contract](docs/planning/b4_46_public_launch_limitations_arithmetic_prerequisites_contract.json) freeze27 public TEXT inputs,
5 literal compact closure metadata and3 primary-only source texts before
reviewer implementation. Separately authored stdlib JSON/hash/AST/Decimal50
text reviewers establish253/257 predicates ONCE/no retry. No old controller,
candidate, TopoLab/shared checker or fixture expression is imported/evaluated;
independent reads no primary-only source/reviewer/receipt. Existing original
derivations remain unchanged conditional TEXT, with no new arithmetic or real
certificate. No external scientific/reference source or Hack3D code/comments/
structure/figures consulted/copied. Old failures/runtime UNKNOWN/costs/memory/
loss/gradient/SAME normalizer/seals remain. See [report](docs/validation/b4_46_public_launch_limitations_arithmetic_prerequisites.md).

## B4.47 fresh public arithmetic and durable bootstrap implementation

Ten new small contribution lists/accepted IEEE words were authored and frozen
before candidate/oracle implementation, with no normalized B4.43 input reuse.
The standalone journal-aware candidate derives from TopoLab's own B4.41 scalar
conventions and B4.43 assembly/residual/error equations. The separate independent
oracle retains its own integer-bisection80 and exact adjacent/squared-midpoint
RN-even proofs, importing no candidate/producer/TopoLab/shared numerical helper.
Checked actual candidate/dependency import, exclusive fsynced pending/started/
operation/terminal and exact new input snapshots use original stdlib engineering.
No new external scientific/implementation source or Hack3D code/comments/layout/
figures consulted/copied. Old mathematical sources/receipts/failures/UNKNOWN/
loss/gradient/SAME normalizer/costs/memory/seals retain their identities.54 public
regressions are software only; formal arithmetic awaits clean locked merged
all-CI-passed source. See the [prospective protocol](docs/planning/b4_47_public_arithmetic_campaign_protocol.md).

B4.47 first-only formal evidence from clean protected merged source
`cadad75a86548e6f71a87f5444064475a5c23ccc` retains GatePASS_FRESH_PUBLIC_ARITHMETIC_ONLY/4328 independent predicates/
104 RN proofs/10 case audits. New runtime/immutable prefixes/native
costs describe ONLY this public panel; every old failure/unknown/charge/seal
remains. No external source, actual geometry/FEM/fit or scientific repair. See
[result](docs/validation/b4_47_public_arithmetic_campaign.md).

## B4.48 public arithmetic limits and conditional real-certification bridge

The [protocol](docs/planning/b4_48_public_arithmetic_limitations_real_certification_protocol.md) and
[contract](docs/planning/b4_48_public_arithmetic_limitations_real_certification_contract.json) freeze30 public TEXT/four compact
closure metadata/four primary-only source texts BEFORE separate stdlib reviewers.
233/231 first-only document/hash/AST/Decimal50 predicates verify consistency,
not new arithmetic/real values/certificates. Existing original TopoLab intended-
operator/triangle/Frobenius/Gram/coercivity/residual/SAME-normalizer derivations
remain conditional TEXT, no loss/gradient change or real execution. No new
external scientific/implementation source or Hack3D code/comment/structure/
figure consulted/copied. All old failures/unknowns/costs/full-memory/seals remain.
See [report](docs/validation/b4_48_public_arithmetic_limitations_real_certification.md).

## B4.49 public combined diagnostic certificate software

Twelve new original tiny rational systems and accepted A_hat/Y/u IEEE words,
ONE combined recipe/expected stops/caps were frozen BEFORE implementation.
Original standalone stdlib candidate combines TopoLab's existing B4.34--37
PSD/coercivity/residual/SAME-normalizer derivations with separately retained
assembly/load/residual errors and BOTH Gram discrepancies. Separately authored
candidate-free oracle uses its own integer binary-search roots/IEEE midpoint
proofs and exact1x1/2x2 toy solves; immutable checked-byte parent/child receipts
bind public launch only. No new external scientific/source reference or Hack3D
code/comment/structure/figure/data/model/label/real FEM is consulted/imported.
51 registered focused checks are software only; formal awaits clean locked
merged all-CI-passed source. No original loss/gradient/normalizer or scientific
repair/full-memory/cost claim. [Report](docs/validation/b4_49_public_combined_diagnostic_certificate.md).

B4.49 first-only formal evidence from clean protected merged `1a05cca3ce1bb78e630fc594025a6c78fd987c04`: PASS_PUBLIC_COMBINED_DIAGNOSTIC_ONLY/6059 independent predicates/455 RN proofs/12 case audits.
New public software observations prove no actual FEM/fidelity/cost/full-memory
certificate or learned repair. All failed/unknown/paid historical evidence and
original loss/gradient/SAME normalizer stay; no new external source used.

## B4.50 combined public limitations and conditional real prerequisites

The [protocol](docs/planning/b4_50_combined_public_certificate_limitations_real_prerequisites_protocol.md) and
[contract](docs/planning/b4_50_combined_public_certificate_limitations_real_prerequisites_contract.json) freeze36 public TEXT/3 literal compact
metadata/4 primary-only source texts before separately authored stdlib reviewers.
250/244 first-only document/hash/AST/Decimal50 predicates check consistency only;
independent reads no primary-only source,primary reviewer/result or shared helper.
Existing original TopoLab intended-PSD/Gram/coercivity/residual/SAME-normalizer
derivations remain conditional TEXT;no new equation implementation,real value,
certificate or numerical panel is evaluated. Supplied public A0/A_hat/Y/u are not
real construction. No new external scientific/implementation source or Hack3D
code/comment/structure/figure used. All old failures/UNKNOWN/paid costs/full-memory/
loss/gradient/normalizer/P17/uniform/seals stay. See [report](docs/validation/b4_50_combined_public_certificate_limitations_real_prerequisites.md).

## B4.51 real-executable and full-resource requirement preregistration

The [protocol](docs/planning/b4_51_real_certification_executable_full_resource_preregistration_protocol.md) and
[contract](docs/planning/b4_51_real_certification_executable_full_resource_preregistration_contract.json) freeze39 public TEXT/3 compact metadata/2 primary-only
source texts BEFORE separately authored stdlib document reviewers.217/404 first-
only JSON/hash/AST/Decimal50 predicates accept documentary consistency only.
18 executable/10 domain/5 role-path/12 resource requirements leave all14 real
slots UNKNOWN_STOP_UNFROZEN,no real executable algorithm,input,path/quota grant,
new paid budget or fit-memory evaluation. Existing original intended-PSD/Gram/
coercivity/residual/SAME-normalizer derivations remain conditional TEXT;original
loss/gradient/normalizer and all old failures/unknowns/charges/seals stay. Failed
prefirst-call lint/v1 source admission remains with original bytes;style-only v2
freeze preceded both first calls,no formal retry. No upstream Hack3D material,
new external scientific/implementation source or real data/model/label was used.
See [report](docs/validation/b4_51_real_certification_executable_full_resource_preregistration.md).

Frozen S02 applies: changing the reviewer after v1 freeze triggers STOP with no
automatic alternative. Generating v2 and running the later TEXT checks did not
restore protocol compliance. Overall slice Gate is FAIL_PROCESS_SOURCE_FREEZE;
217/404 are retained post-stop document checks ONLY,not accepted protocol evidence.
Both quotas are consumed1/1;no further formal call,source reset or retry follows.

## R1 delivery feasibility decision (2026-10-15)

The [R1 plan](docs/planning/TopoLab_v2_delivery_execution_plan.md) derives integer
paper storage floors from TopoLab's existing Hex8/Voigt/Gauss conventions,
B4.38/40 stack equations and committed full-Q public constructor as TEXT only.
Cost arithmetic uses versioned B4.34/51 components with Decimal precision50.
No old external evidence, upstream Hack3D content or new external scientific
source was read; no production matrix/mesh/FEM, model, label, fit or formal
program ran. Mandatory ordinary software regression is separate.
The direct dense construction's resource exclusion and NO_ADMISSIBLE_ROUTE
are planning decisions, not numerical acceptance or learned acceleration.

## D1 exact-physics resource-admission stop (2026-10-15)

The owner-approved [D1](docs/validation/d1_physics_resource_feasibility.md) inspected
TopoLab's existing context CNN, exact FEM/adjoint and prepared immutable setup as
text, plus installed SciPy/Torch Python wrappers as text. Official SciPy splu,
PyTorch2.14 Conv3d API documentation and the SuperLU project FAQ supplied interface
context only;their native programs/workspaces were not evaluated or imported.
No implementation was copied,translated,vendored or modified. Integer payload
arithmetic is partial, not a native/lifetime upper bound or memory trial.
The missing independent complete pre-input proof triggers STOP_UNKNOWN_PREFIT_BOUND.
No integration implementation, old evidence/index/label/model read, formal call,
FEM/fit/search/sealed access or scientific acceptance;all old provenance and
numerical identities stay. Required ordinary software regression is separate.


## Solver-internal learned-update inception (2026-10-15)

One candidate assessment consults Chi et al.,
[Universal machine learning for topology optimization](https://doi.org/10.1016/j.cma.2019.112739)
(2021), Sections4.1–4.3, via the author's
[public full text](https://paulino.scholar.princeton.edu/document/1161).
It supplies the online sensitivity-learning/physical-refresh mechanism context
only. No implementation, architecture, weights, dataset, figure or performance
result is imported. The [decision](docs/planning/TopoLab_v2_solver_internal_learning_route_decision.md)
uses TopoLab's committed OC/FEM source as TEXT/AST to identify state-consistency,
full-charge and mandatory independent simultaneous-memory obligations. The
candidate is REJECTED_CURRENT_RESOURCE_ADMISSION, not numerically tested or a
universal impossibility result. No new Hack3D comparison/content, old external
research payload, real input/FEM/fit/search/timing/memory trial, source numerical
change or formal program occurs. Ordinary software regression remains separate.

## P/17 bounded-runtime penalty-homotopy proposal (2026-10-16)

The [finite proposal](docs/planning/TopoLab_v2_P17_bounded_homotopy_proposal.md)
uses Liu and Tovar (2014), Section6.1.6, from the primary article already listed
above, for penalty-continuation mechanism context only. Its8/8 p=1/p=2 choice
is an independently specified untested hypothesis, not the paper's schedule or
a global/TopoLab guarantee. Official Netlib DPBTRF parameter/storage documentation
supplies band-factor storage context; Linux kernel ELF and /proc documentation
supplies executable/mapping interface context only. No linked-library workspace
or complete runtime bound is inferred. A preliminary author-hosted Shewchuk CG
reference was retrieved; CG is not selected. No reference code, comments, figures,
data, weights or performance results are imported/copied, and no new Hack3D
comparison occurs. Bandwidth/storage arithmetic follows TopoLab's own frozen
Hex8 connectivity and a proposed z-fast internal solve permutation.

The proposal is CONDITIONAL_IMPLEMENTATION_PROPOSAL_NOT_ADMITTED. No numerical
source, new native kernel, real input, FEM, inference, fit/search, timing/memory
trial or formal program is implemented/executed. Old external evidence read sets
are empty. Model/solver portability, independent complete resource admission and
all new science/cost remain UNKNOWN. Ordinary complete software checks are separate.


## I1 bounded native public software (2026-10-16)

The [I1 protocol](docs/planning/i1_bounded_native_software_protocol.md) implements
standard Hex8/SIMP/filter/OC equations and TopoLab's committed ContextCNN graph
with original fixed-storage C. An initial same-primary-author checker draft
was preserved externally and replaced by a fresh implementation from the
owner-authorized independent audit role. That role derives Hex8 stiffness from
analytic one-dimensional basis integrals, writes its own band LDLᵀ/terminal/
evaluation checker and native controller, and imports no candidate numerical
helper. Earlier exposure to the primary draft is disclosed, not claimed blinded.
The primary separately reviews those roles. Independent actual-binary review
retains a decisive selected-host pre-entry startup/lifetime UNKNOWN, closing
I1's route NO_ADMISSIBLE_ROUTE without final admission dispatch/freeze. No
Hack3D code/comment/structure/figure is read, copied, translated or compared.

New primary references are the [GCC stack-usage specification](https://gcc.gnu.org/onlinedocs/gcc/Developer-Options.html),
Linux [ELF](https://www.kernel.org/doc/html/latest/userspace-api/ELF.html),
[/proc](https://www.kernel.org/doc/html/latest/filesystems/proc.html),
[seccomp](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html),
[execveat](https://man7.org/linux/man-pages/man2/execveat.2.html),
[memfd/sealing](https://man7.org/linux/man-pages/man2/memfd_create.2.html),
[signals](https://man7.org/linux/man-pages/man2/sigaction.2.html),
[core-dump semantics](https://man7.org/linux/man-pages/man5/core.5.html),
[GitHub custom-shell interface](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax),
[runner launch](https://raw.githubusercontent.com/actions/runner/main/src/Runner.Worker/Handlers/ScriptHandler.cs) /
[process invocation](https://raw.githubusercontent.com/actions/runner/main/src/Runner.Sdk/ProcessInvoker.cs),
[x86 red-zone ABI](https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html),
and Linux [ELF loading](https://raw.githubusercontent.com/torvalds/linux/master/fs/binfmt_elf.c),
[exec setup](https://raw.githubusercontent.com/torvalds/linux/master/fs/exec.c) /
[mapping relocation](https://raw.githubusercontent.com/torvalds/linux/master/mm/mremap.c),
and the [x86 UAPI stat layout](https://github.com/torvalds/linux/blob/master/arch/x86/include/uapi/asm/stat.h),
for interface/layout facts only. Original bounded SHA-256 follows the equations
and constants in [FIPS180-4](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.180-4.pdf);
no third-party implementation is copied, vendored or called. Known-answer tests
are not a cryptographic certification. Native binary/startup/stack/lifetime
admission remains independent work, not inferred from these documents.

New public software fixtures/weights and ordinary numerical regressions do not
read old labels/models/index/raw evidence, run a scientific experiment or repair
P/17. Old external research/backup read set remains empty. All existing numerical
identities and full-fit/historical resource gaps stay.

The Linux [proc ownership specification](https://man7.org/linux/man-pages/man5/proc_pid.5.html)
explains the pre-freeze startup correction: disabling dumping changes proc-file
ownership. Selected auxv now comes from the actual kernel-provided entry stack,
with its location retained before bounded CI environment erasure, following the
ELF stack layout above. No permission escalation or dumpability relaxation.
Actual GCC command traces also expose a default linker LTO plugin and an
available wrapper. Their exact build-time file origins are recorded separately
from native runtime closure; no third-party plugin implementation is imported.
The same independent audit role originally authored the offline ELF/call/frame
and constant-RSP review tools now published in `scripts/i1_independent_*_review.py`.
They parse explicit hash-bound new public build evidence and committed native
blobs without importing the primary inspector or executing target binaries.
The primary reviewed their read/execute/output boundary and actual source;
their facts remain UNKNOWN for complete admission. No external implementation
or old research payload was imported.

## B prospective resource-assurance specification (2026-10-18)

The owner commissions one document proposal in the existing
[roadmap](docs/planning/TopoLab_v2_development_roadmap.md#b-resource-assurance-specification),
not an implementation, resource proof or adopted standard. The
[QEMU invocation manual](https://www.qemu.org/docs/master/system/invocation.html),
[Linux KVM memory-region API](https://docs.kernel.org/virt/kvm/api.html#kvm-set-user-memory-region)
the [cgroup v2 manual](https://docs.kernel.org/admin-guide/cgroup-v2.html)
and [GitHub-hosted runner documentation](https://docs.github.com/en/actions/concepts/runners/github-hosted-runners)
were read on2026-10-18 for public capacity/configuration/limit interface context
only, including the provider's unsupported nested-virtualization limitation.
Current/master documents bind no deployed version, selected host or
complete resource certificate. The normative guest-capacity/trust-boundary
specification is original planning; no new kernel/hypervisor proof or algorithm
is implemented or evaluated, and no VM is executed. No reference code, figure
or implementation is copied, translated or vendored.
No Hack3D content/comparison or old external research/backup/sealed payload is
read. Required ordinary regression remains separate software verification.

## M2 native fixed H stage A (2026-10-18)

The [A protocol](docs/planning/p17_m2_native_homotopy_a_protocol.md) implements
only the owner-fixed8×p1/8×p2/p3 schedule using TopoLab's independently authored
FEM/filter/OC/legacy projection and CPU ContextCNN/encoding. No upstream source,
new algorithm/kernel/backend, training or old model/label/index/evidence was used.
The new3×2×1 point-node19/y/-1 software fixture and reinitialized public weights
are original tests, never historical P/17 bits or scientific samples.
The independent author wrote its numerical checker/original two-element fixtures
before reading the new driver, then cross-reviewed software; exposure is
nonblind and shared unchanged foundational FEM is explicit. RSS/exit adaptation
uses existing B4.30 recording semantics and Python's existing os.wait4/native
statistics; no new allocation/kernel proof or external scientific source.
Old native and guest contracts/results retain scope. See [software report](docs/validation/p17_m2_native_homotopy_a.md)
and [independent review](docs/validation/p17_m2_native_homotopy_a_independent_review.md).


## M2 bounded input/export preparation R (2026-10-18)

Owner-authorized [R protocol](docs/planning/p17_m2_input_export_preparation_protocol.md)
adds original stdlib-only bounded metadata registration and literal field/IEEE
transcription for12 checkpoint copies,528 train-only two-view cases and18 uniform
scalars. The independent author writes its own source registry/field/word/tensor
comparisons before primary source exposure, then cross-reviews; review is not blind.
No external implementation or Hack3D source is used. Existing native RSS/exit
recording is reused for non-scientific IO only. No model execution, numerical
revalidation, new algorithm, label generation, B/C or old proof reconstruction.
Actual source access/results are reported separately; raw originals remain read-only
and only the explicitly granted R roles may parse them under the frozen whitelist.

## 2026-10-19 — NEW R/v2 billing and source preparation

Original standard-library v2 identity/FULL/external-exit orchestration and a
separately authored raw event/RSS/exit/new-only-backup comparator extend the
existing R field tools. No upstream implementation, scientific algorithm or
external data was imported. Original R/v1 source remains at its frozen commit;
actual restricted source acceptance is separately recorded in the new report.

## 2026-10-20 — NEW R/v3 readiness binding

Original finite identity/root/readiness-window binding and versioned plan builder
reuse TopoLab's published field/IEEE/FULL/native RSS/observed-exit algorithms. The
new different author independently specifies/checks window and raw-event coverage
before nonblind cross-review. No external implementation, new numerical method,
Hack3D content or old research payload is imported during software preparation.
Actual explicitly granted source access is recorded only in the new validation
report; preparation cannot establish scientific repair or reopen historical grants.

## 2026-10-20 — F-only public failure recording repair

Original standard-library failure-stage bookkeeping, finite raw-event binding
and public-only F entry evolve four existing TopoLab tools. The different author
first writes its own failure matrix/arithmetic, then performs nonblind review
and fresh public native fixture checks. No upstream implementation, historical
raw input/receipt/profile, Hack3D material, numerical method or scientific data
is read, copied or imported; old source revisions remain reproducible.

## 2026-10-20 — R-STABLE software and zero source admission

Original stdlib-only new identity/actual-argv/lease/role bindings, same-read
closing identity sidecars and bounded cleanup observations reuse TopoLab's H,
field transcription, independently authored IEEE/source comparison and F
recording algorithms. A fresh different author freezes expectations before
producer-patch exposure, then cross-reviews NONBLIND and tests NEW public/native
fixtures. No external implementation, numerical method, Hack3D material or old
source/evidence is imported. Unknown operational writer coverage closes formal
entry unlaunched0/6/old stat-read0. See the
[software/zero-launch report](docs/validation/p17_m2_source_stability_export.md)
and [independent review](docs/validation/p17_m2_source_stability_export_independent_review.md).
