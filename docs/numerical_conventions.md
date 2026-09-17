# Numerical conventions

Status: **provisional for G0**. Any change after N1 requires a documented reason and
regression-test update.

## Geometry and indexing

- Use a right-handed Cartesian coordinate system.
- Store node coordinates as `(x, y, z)` in SI units.
- Assign each node three displacement degrees of freedom in `(ux, uy, uz)` order.
- Use zero-based Python indices internally.
- Freeze the Hex8 local node order before implementing the element stiffness matrix;
  document it with a diagram and an orientation/Jacobian test in N1.

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
