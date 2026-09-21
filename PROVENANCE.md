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
