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
