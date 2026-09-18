# Gate N2 optimization validation

Date: 2026-09-17  
Release: `v0.2.0`  
Audited implementation baseline: `333f436`

## Scope and decision

Gate N2 is **passed** for the initial single-load-case, density-filtered SIMP
optimizer on structured, axis-aligned Hex8 meshes. The evidence covers SIMP modulus
interpolation, analytical compliance sensitivity, sparse density filtering and its
gradient, move-limited Optimality Criteria updates, physical-volume enforcement,
state-consistent history, final-state re-solving, convergence, and deterministic
repeatability.

This decision permits work on the P1 API, worker, and controlled data-generation
layers. It does not demonstrate scalability, validate an API or asynchronous task
system, freeze an ML dataset contract, or support an ML-acceleration claim.

## Implementation slices reviewed

| Pull request | Scope | Squash commit |
|---|---|---|
| `#7` | SIMP modulus interpolation, compliance, and analytical sensitivity | `b0b3130` |
| `#8` | Sparse density filter, OC update, complete SIMP loop, and optimizer tests | `333f436` |

Both slices were independently implemented under the boundary in `PROVENANCE.md`
from the standard equations and references documented there. No source code,
comments, file structure, or figures from the unlicensed Hack3D reference repository
were used.

## Validation cases

The sensitivity case uses three unit Hex8 elements along `x`, a fixed `x=min` face,
and a unit negative-`y` point load at `(3, 1, 1)`. Its physical densities are
`[0.45, 0.65, 0.85]`; material parameters are `E_0=1000`, `E_min=1`, `nu=0.3`, and
`p=3`.

The optimizer case uses a `4 x 2 x 1` unit-element cantilever with the same support
and a unit negative-`y` point load at `(4, 2, 1)`. It uses target volume `0.5`, filter
radius `1.5`, `rho_min=0.05`, move limit `0.2`, convergence tolerance `0.01`, and at
most 60 iterations.

## Evidence matrix

| Behavior | Executable evidence | Acceptance criterion | Result |
|---|---|---|---|
| SIMP interpolation and compliance energy identity | `tests/test_sensitivity.py` | Analytical energy within `rtol=1e-12` | Pass |
| Analytical physical-density sensitivity | Three-variable central difference with step `1e-6` | At least two errors `<=1e-4`; maximum `<=1e-3` | Pass |
| Density-filter definition | Exact three-element distance-weight example | Expected weights and output within `atol=1e-15` | Pass |
| Filter-gradient propagation | Central finite difference with step `1e-7` | Agreement within `rtol=1e-8` | Pass |
| OC bounds and filtered volume | One update on the optimizer case | Move bounds respected; volume error `<=5e-3` | Pass |
| History state consistency | Every recorded optimizer iteration | Density/filter mapping and metrics describe one post-update state | Pass |
| Final-state consistency | Independent solve of returned physical density | Compliance agrees within `rtol=1e-9` | Pass |
| Determinism | Two complete runs with identical inputs | Density and history agree within floating-point tolerance | Pass |
| Invalid inputs | Filter, optimizer configuration, and initial density | Explicit `TypeError` or `ValueError` | Pass |

## Measured results

- The three central-difference sensitivity relative errors were
  `6.3084e-10`, `1.7816e-8`, and `1.7405e-7`. All three are below `1e-4`, and the
  maximum is more than three orders of magnitude below the `1e-3` limit.
- The standalone OC update produced physical volume `0.5000000085240588`, an
  absolute target error of `8.5241e-9`, while respecting the move bounds.
- The complete optimizer converged in 13 iterations. Its final maximum design-density
  change was `0.009107108670230402`, below the `0.01` convergence tolerance.
- Final physical volume was `0.499999996613351`, an absolute target error of
  `3.3866e-9`. Final compliance was `0.2778691006748881`.
- Independently re-solving the returned physical density produced exactly the same
  displayed compliance; the measured relative difference was `0.0`.
- Two repeated optimizer runs produced exactly equal final design density, physical
  density, and every stored history value on the recorded environment.

No numerical tolerance was changed or loosened during the Gate N2 audit.

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

Release-candidate result: 106 tests passed on Python 3.12.10, macOS 26.5, Apple M2.
The implementation PR quality checks also passed before this audit.

## Known limits after N2

- Meshes remain structured, axis-aligned rectangular Hex8 grids.
- Materials remain isotropic, linear elastic, and small strain.
- Optimization supports one load case and one global physical-volume constraint.
- The filter is a density filter; manufacturing constraints and sensitivity-filter
  variants are not implemented.
- Convergence evidence is for a deliberately small regression case. It is not a
  mesh-independence, design-quality, or performance study.
- No runtime or memory benchmark has been completed, so the project does not claim
  scalability.
- API, worker, persistence, frontend, dataset generation, and ML are outside this
  release.
