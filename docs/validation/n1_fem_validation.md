# Gate N1 finite-element validation

Date: 2026-09-17  
Release: `v0.1.0`  
Audited implementation baseline: `5b79f6e`

## Scope and decision

Gate N1 is **passed** for the initial structured, axis-aligned Hex8 finite-element
foundation. The evidence covers mesh conventions, element stiffness, sparse global
assembly, zero-displacement constraints, linear solving, reactions, fixed-face
supports, and point/equal-node face-resultant loads.

This decision permits work on N2 sensitivity and SIMP correctness. It does not validate
a SIMP optimizer, demonstrate scalability, or support an ML-acceleration claim.

## Implementation slices reviewed

| Pull request | Scope | Squash commit |
|---|---|---|
| `#2` | Structured Hex8 mesh, indexing, orientation, and invalid dimensions | `21a58bc` |
| `#3` | Isotropic elasticity and Hex8 element stiffness | `e8ddf6f` |
| `#4` | COO/CSR assembly, constrained solve, and reactions | `26c306f` |
| `#5` | Fixed-face supports and point/face load discretization | `5b79f6e` |

All four slices were developed independently under the boundary in `PROVENANCE.md`.
No source code, comments, file structure, or hard-coded stiffness matrix from the
unlicensed Hack3D reference repository were used.

## Evidence matrix

| Behavior | Executable evidence | Acceptance criterion | Result |
|---|---|---|---|
| Coordinates and x-fastest node indexing | `tests/test_mesh.py` | Exact expected arrays | Pass |
| Connectivity and local-node order | `tests/test_mesh.py` | Exact expected arrays | Pass |
| Element orientation | Center Jacobian on a non-unit multi-element mesh | Positive determinant; expected value within `atol=1e-15` | Pass |
| Element constitutive/stiffness behavior | `tests/test_fem.py` | Symmetry within `rtol=1e-12`; exactly six numerical rigid modes | Pass |
| Affine displacement energy | Constant strain containing all six Voigt components | Analytical and FE energy within `rtol=1e-12` | Pass |
| Global stiffness symmetry | Two-element mesh | `||K-K.T|| / ||K|| <= 1e-10` | Pass |
| Sparse/dense assembly | Independent dense scatter on a two-element mesh | Entries agree within `rtol=1e-9` | Pass |
| Sparse/dense displacement | Fully fixed left face and unit point load | Free displacements agree within `rtol=1e-9` | Pass |
| Free-DOF equilibrium | Same constrained solve | Residual within `atol=1e-10` at unit load scale | Pass |
| Load/reaction balance | Point-load and face-resultant cases | Resultant residual within `atol=1e-10` and `atol=1e-12`, respectively | Pass |
| Face-load conservation | Six-node selected face | Requested total preserved within `atol=1e-12` | Pass |
| Remaining rigid modes | One Hex8 with only one node fixed | Explicit singular-system error | Pass |
| Invalid inputs | Mesh, material, supports, selectors, loads, and solver inputs | Explicit `TypeError` or `ValueError` | Pass |

The absolute equilibrium tolerances above apply to test loads of magnitude one and
four, so they are stricter than the initial relative-residual target of `1e-8`. No
numerical tolerance was loosened during N1.

## Reproduction

Environment details are recorded in `docs/development_environment.md`; exact Python
dependencies are locked in `uv.lock`. Run from the repository root:

```bash
uv sync --dev --locked
uv run ruff check .
uv run mypy src
uv run pytest
git diff --check
```

Release-candidate result: 73 tests passed on Python 3.12.10, macOS 26.5, Apple M2.
The corresponding GitHub Actions quality checks also passed for every implementation
slice.

## Known limits after N1

- Meshes are structured, axis-aligned rectangular Hex8 grids only.
- Materials are isotropic, linear elastic, and small strain.
- Prescribed displacements are zero; one linear load case is solved at a time.
- `FaceLoad` is an equal-node discrete resultant, not pressure or consistent traction
  integration.
- Assembly currently repeats one uniform element stiffness matrix; density-dependent
  element scaling belongs to N2.
- No performance or memory benchmark has been completed, so the project does not claim
  scalability.
- No SIMP, sensitivity, filter, Optimality Criteria, API, frontend, dataset, or ML
  implementation is included in `v0.1.0`.
