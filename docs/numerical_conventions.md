# Numerical conventions

Status: **N1 conventions frozen at v0.1.0; N2 conventions frozen at v0.2.0; M0
experiment-contract conventions frozen at m0.v1; M1 fitting conventions frozen at
m1.v1**. Any change to a frozen convention requires a documented reason and
regression-test update.

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
- Store strain in engineering-Voigt order
  `(epsilon_xx, epsilon_yy, epsilon_zz, gamma_xy, gamma_yz, gamma_xz)` and stress in
  the matching order `(sigma_xx, sigma_yy, sigma_zz, tau_xy, tau_yz, tau_xz)`.
- Derive the Hex8 stiffness from `Ke = integral(B.T @ D @ B) dV`, using the local
  node and DOF order above, trilinear isoparametric shape functions, and `2 x 2 x 2`
  Gauss integration. The first implementation supports axis-aligned rectangular
  elements with positive finite side lengths.
- Assemble the global stiffness by scattering each element's 24-by-24 matrix through
  its documented DOF map. Sum duplicate COO entries when converting to canonical CSR.
- Apply zero-displacement constraints by solving the reduced free-free system; do not
  overwrite stiffness rows or add artificial diagonal penalties. Recover reactions as
  `r = K @ u - f`, so free-DOF residuals vanish and constrained reactions balance the
  applied load. Reject a reduced system when sparse factorization fails or its pivot
  scale indicates numerical singularity at the matrix-size-scaled machine precision.
- The unconstrained element/global stiffness is positive semidefinite because of rigid
  body modes; test positive definiteness only after sufficient supports are applied.

## Boundary conditions and loads

- A direction is an axis (`x`, `y`, `z`) or DOF index (`0`, `1`, `2`).
- The load's signed magnitude determines positive or negative direction. Never use a
  negative direction index to encode sign.
- A face selector uses a global axis and the `min` or `max` side of the structured
  domain. A fixed-face support constrains the selected displacement components for
  every node on that face.
- A point load adds its signed magnitude once at one node and direction. Multiple load
  objects superpose in the same global vector.
- A distributed load's `total` means the resultant over the selected nodes or face;
  discretization performs exactly one distribution step. The initial `FaceLoad`
  distributes this total equally over the selected face nodes; it represents a
  discrete resultant, not a pressure or consistent surface-traction integration.
- Reject problems with no loads, no supports, out-of-domain selectors, or remaining
  rigid body modes with explicit validation errors.

## SIMP state

- Design and physical density values lie in `[rho_min, 1]`, where the optimizer will
  require `0 < rho_min < 1`. The standalone compliance analysis accepts physical
  densities in `(0, 1]`.
- Use the SIMP interpolation
  `E(rho) = E_min + rho**p * (E_0 - E_min)`, with `p >= 1`. `E_min` and `E_0` are
  absolute Young's moduli in pascals and must satisfy `0 < E_min < E_0`; `E_min` is
  not a ratio.
- For element `e`, let `K0_e` be its stiffness at unit Young's modulus. Evaluate
  `C = f.T @ u = sum_e E(rho_e) * u_e.T @ K0_e @ u_e`, and use the unfiltered
  physical-density derivative
  `dC/drho_e = -p * rho_e**(p - 1) * (E_0 - E_min) * u_e.T @ K0_e @ u_e`.
- Use a density filter in the optimizer: design density `x` is filtered to physical
  density `rho = (H @ x) / Hs` before stiffness interpolation. Back-propagate
  compliance and volume derivatives through that linear map before the OC update.
  For element-center distance `d_ij`, use sparse weights
  `H_ij = max(0, r_min - d_ij)` and `Hs_i = sum_j H_ij`.
- Define volume as the mean physical density. Apply the OC move limit and
  `[rho_min, 1]` bounds to design density, while bisection evaluates the filtered
  physical volume constraint.
- Because every filter row is a nonnegative normalized weighted average, its exact
  result lies in the closed interval from the minimum to the maximum input design
  density. Clip the computed sparse quotient to that convex interval to remove only
  last-bit floating-point reduction overshoot at a bound.
- Record each history row after an OC update and a fresh finite-element solve. Its
  design density, physical density, volume, compliance, and maximum design-density
  change therefore describe the same updated state. Convergence uses that maximum
  design-density change.
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

## M0 experiment representation

- A versioned experiment case contains one complete `TopologyProblem` with no
  `initial_density`. Its stable ID is the SHA-256 digest of the canonical mesh,
  material, support, load, and optimization payload. Initialization is a compared
  method, not part of physical case identity.
- ML tensors are channel-first and use spatial order `(z, y, x)`, so array access is
  `[channel, ez, ey, ex]` and `x` remains the fastest flattened axis. No image-style
  axis reversal is allowed.
- The first input representation has ten element-grid channels: three support masks,
  three signed load components, three normalized element-center coordinates, and one
  broadcast target physical volume fraction.
- The learned output initializes design density, not physical density. Project it to
  the target filtered physical volume before SIMP; derive physical density only by
  the frozen density filter.
- Dataset partitions operate on complete case IDs. Optimizer history states, derived
  tensors, repeated labels, and augmentations from one case cannot cross partitions.
- Dataset materialization checkpoints are keyed by the canonical complete-manifest
  digest. Recorded case outcomes are append-only, and a complete checkpoint contains
  exactly one success or sanitized terminal failure for every manifest case.
- The materialization executor visits pending samples in canonical `case_id` order,
  checkpoints each known success or terminal failure, and leaves an unexpectedly
  interrupted case pending for a later resume.
- The bounded `topolab.m0.catalog.v2` production catalog has its own content-derived identity over
  the sorted complete case IDs. Its exact fixed cohort, load-location grid, volume
  fractions, ID/OOD pairing, and partition counts are frozen in
  `docs/ml_experiment_contract.md`; changing the population requires a new catalog
  version and identity.
- Catalog v2 keeps the v1 case schema and `0.01` density-change tolerance but freezes
  the maximum at 120 iterations. Catalog v1 and its 100-iteration failed
  materialization remain immutable validation evidence.
- The production catalog entrypoint builds a manifest only from a clean Git
  worktree, capturing the exact commit, active Python/NumPy/SciPy versions, and the
  repository `uv.lock` digest. Planning is read-only, solver execution requires an
  explicit flag, and every output root must resolve outside the source repository.
- Exact identity, encoding, projection, label, split, OOD, baseline, quality,
  statistics, and fallback rules are frozen in `docs/ml_experiment_contract.md`.

## M1 deterministic fitting and artifacts

- Production M1 fitting accepts only the frozen catalog-v2 materialization with
  manifest SHA-256
  `7e732446d683a3609ec3e4af4b87d334caeb583c69da3db9ea0f47f91d119d5a`.
  Its entrypoint requires a clean Git checkout, the repository `uv.lock`, and data
  and artifact roots that both resolve outside the source repository. Omission of
  the explicit execution flag is a read-only plan.
- Production preflight reads and canonically validates the embedded materialization
  index but does not open label artifacts. Execution opens and verifies only train
  and validation label artifacts through the fitting adapter; held-out test and OOD
  label bytes remain unopened.
- M1 fitting runs only on CPU and only opens the frozen train and validation
  partitions. Test and OOD labels remain inaccessible to the fitting adapter and
  all-seed runner.
- Each seed initializes the model and the training-shuffle generator independently.
  PyTorch deterministic algorithms are required during fitting; the prior process RNG
  and deterministic-algorithm settings are restored afterward.
- Epoch loss is the elementwise squared-error sum divided by the exact number of
  target elements, so a smaller final batch is weighted by its sample count rather
  than as one full batch.
- Select the first epoch with the strictly lowest mean validation MSE. An equal value
  never replaces an earlier checkpoint. Stop after 25 consecutive epochs without a
  strict improvement, subject to the 200-epoch maximum.
- Checkpoints contain only the selected model state, not pickle, optimizer state, or
  a resumable training process. Named tensors are finite `float32` Safetensors and
  are addressed by the SHA-256 of those exact bytes.
- A selection artifact records every epoch metric, selected epoch/value, early-stop
  state, duration, train/validation case IDs, manifest digest, label and training
  revisions, locked runtime versions, hardware/thread metadata, and the verified
  checkpoint reference. Generated training artifacts remain outside Git.

## M1 learned evaluation

- Learned evaluation rejects training samples. It accepts one verified selection and
  its matching checkpoint only when both refer to the frozen M1 data manifest, and
  runs the frozen model as CPU `float32` without gradients.
- Per-query learned setup time includes deterministic case encoding, host-tensor
  construction, model inference, and output validation. Checkpoint loading is an
  experiment setup cost and is not hidden inside per-query inference time.
- A prediction must be CPU `float32`, finite, within `[0, 1]`, and have shape
  `(1, 1, nz, ny, nx)`. Remove only the leading batch dimension before the frozen
  filtered-volume projection.
- Learned refinement uses the same public SIMP path and the same quality boundary as
  the fixed baselines.
- The matching uniform reference is timed separately and is not charged to a
  successful learned attempt. A failed attempt runs a fresh uniform fallback, fully
  charges it, and remains failed even when the fallback succeeds.
