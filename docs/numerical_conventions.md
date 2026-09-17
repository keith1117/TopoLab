# Numerical conventions

Status: **frozen for the N1 mesh slice**. Any later change requires a documented
reason and regression-test update.

## Geometry and indexing

- Use a right-handed Cartesian coordinate system.
- Store node coordinates as `(x, y, z)` in SI units.
- Assign each node three displacement degrees of freedom in `(ux, uy, uz)` order.
- Use zero-based Python indices internally.
- A structured mesh contains `(nx, ny, nz)` elements along `(x, y, z)` and spans
  `[0, Lx] x [0, Ly] x [0, Lz]`. Element counts are positive integers and physical
  lengths are positive finite values.
- Number nodes with `x` varying fastest, followed by `y`, then `z`:

  `node(i, j, k) = i + (nx + 1) * (j + (ny + 1) * k)`.

- Number elements with the same axis priority:

  `element(ex, ey, ez) = ex + nx * (ey + ny * ez)`.

- Use the following Hex8 local node order. The local reference coordinates are
  `(xi, eta, zeta)` in `[-1, 1]^3`:

  | Local node | `(xi, eta, zeta)` | Structured-grid offset `(di, dj, dk)` |
  |---:|:---:|:---:|
  | 0 | `(-1, -1, -1)` | `(0, 0, 0)` |
  | 1 | `(+1, -1, -1)` | `(1, 0, 0)` |
  | 2 | `(+1, +1, -1)` | `(1, 1, 0)` |
  | 3 | `(-1, +1, -1)` | `(0, 1, 0)` |
  | 4 | `(-1, -1, +1)` | `(0, 0, 1)` |
  | 5 | `(+1, -1, +1)` | `(1, 0, 1)` |
  | 6 | `(+1, +1, +1)` | `(1, 1, 1)` |
  | 7 | `(-1, +1, +1)` | `(0, 1, 1)` |

  Looking from outside the domain toward the `z = 0` face, nodes `0-1-2-3` trace
  that face; nodes `4-5-6-7` are their counterparts in the positive `z` direction.
  The ordered physical edges `0->1`, `0->3`, and `0->4` align with positive
  `(x, y, z)`, so their scalar triple product is positive. Equivalently, every
  axis-aligned element has `det(J) = dx * dy * dz / 8 > 0` at the element center.
- Number displacement DOFs node-major. For global node `n`, `(ux, uy, uz)` have
  indices `(3*n, 3*n + 1, 3*n + 2)`. An element's 24 DOFs concatenate these three
  indices for local nodes `0` through `7` in the order above.

## Materials and analysis

- Initial scope is isotropic, linear elasticity under small deformation.
- Express Young's modulus in pascals and loads in newtons.
- Require `E > 0` and `-1 < nu < 0.5`.
- The unconstrained element/global stiffness is positive semidefinite because of rigid
  body modes; test positive definiteness only after sufficient supports are applied.

## Boundary conditions and loads

- A direction is an axis (`x`, `y`, `z`) or DOF index (`0`, `1`, `2`).
- The load's signed magnitude determines positive or negative direction. Never use a
  negative direction index to encode sign.
- A distributed load's `total` means the resultant over the selected nodes or face;
  discretization performs exactly one distribution step.
- Reject problems with no loads, no supports, out-of-domain selectors, or remaining
  rigid body modes with explicit validation errors.

## SIMP state

- Design and physical density values lie in `[rho_min, 1]`.
- Record the exact interpolation equation and whether `E_min` is an absolute modulus
  or an `E_0` ratio when the material model is implemented.
- Choose one filter definition before N2 and test its placement relative to the OC
  update; do not reproduce the reference repository's ordering without validation.
- Compliance, volume, density change, and density stored for one history row must all
  describe the same optimization state.
- Re-solve the final density before returning final compliance.

## Reproducibility

- A case records mesh, material, supports, loads, volume fraction, filter, optimizer,
  convergence tolerances, code revision, and environment metadata.
- Benchmarks report hardware, thread count, solver settings, cold/repeated runs, wall
  time, and peak memory.
- Numerical tolerances are defined in the reimplementation strategy and encoded as
  named test constants rather than scattered literals.
