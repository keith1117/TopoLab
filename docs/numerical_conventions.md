# Numerical conventions

Status: **N1 conventions frozen at v0.1.0; N2 conventions frozen at v0.2.0; M0
experiment-contract conventions frozen at m0.v1; M1 fitting and evaluation
conventions frozen at m1.v1; M2 follow-up conventions frozen at m2.v1**. Any change
to a frozen convention requires a documented reason and regression-test update.

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
- For the A3 solver ordering policy, use SuperLU `COLAMD` below 5,000 free DOFs and
  `MMD_AT_PLUS_A` at or above 5,000 free DOFs. An explicit `COLAMD` option preserves
  the historical fallback for matched comparisons. Assembly, pivot rejection, and
  the mathematical linear system remain unchanged; benchmark both orderings when
  evaluating a larger-mesh performance claim.
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

The historical `topolab.simp.v1` contract and public default use the maximum
**design** density change above. B2.1 has a separate opt-in termination policy,
`topolab.simp.physical_plateau.v1`, for development comparison only. It retains
that design-change stop. Otherwise, after at least eleven completed updates,
it may stop when each of the last ten maximum per-update **physical** density
changes is at most the same `0.01` density scale and the compliance improvement
over those ten updates is nonnegative and at most `0.0002` relative to the
earlier compliance. This measures stability of the analyzed filtered state;
it does not redefine an old design-change pass. OC updates, filtering,
stiffness, and the configured iteration cap are unchanged. Results under this
policy require its solver version alongside the physical-case identity.

B2.3 tests a separate, development-only **iteration-budget contract**:
`topolab.b2_3.budget240.plan.v1` retains the B2.1 physical-plateau solver
policy and every stopping tolerance, but changes each selected case's
`max_iterations` from 120 to 240. This field is part of the physical-case
identity, so B2.3 cases, prospective labels, and results require new IDs
linked explicitly to their B2.2 source IDs. The public default and old
case/result identities are unchanged. No 120-update failure is relabeled
as a success.

B2.8 tests an opt-in, development-only **initial-design contract**,
`topolab.b2_8.y_midpoint_start.v1`. For one `y` point load, blend the finite
CPU-float32 B2.7 prediction elementwise with the uniform volume-fraction
field at fixed equal weights before the unchanged filtered-volume projection.
For `z`, copy the B2.7 prediction. Keep the B2.3/B2.4 240-update
physical-plateau solver, independent quality acceptance, and fully charged
fresh uniform fallback unchanged. The historical and public initial-density
paths are unaffected; B2.8 results require their own experiment identity.

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

## B2.4 development-label representation

- The 240-update development cases retain the B2.3 physical-plateau policy,
  label identity, and result-ID mapping. Their input and target tensors retain
  the M0 channel-first `(z, y, x)` spatial order and x-fast flattening.
- Audit the solver's full-precision terminal compliance against an independent
  solve before float32 serialization. Recompute the filtered physical density
  from the stored float32 design, then independently solve that stored state
  and record its own compliance. This avoids equating the two distinct density
  precisions at the full-precision `1e-9` tolerance.
- At the stored physical state, compute the absolute compliance derivative
  with respect to design density through the transpose density filter. Divide
  by its within-case mean, clip to `[0.25, 4]`, then divide by the clipped
  mean. Store the float32 weights with each label and independently recompute
  them during the complete artifact audit. The weights are loss weights only;
  they are not inference inputs.
- The [B2.4 protocol](planning/b2_4_development_labels_protocol.md) fixes the
  522-case population, identity, quality and resource Gate. Generated labels
  and checkpoints stay outside Git.

## B2.5 mixed-shape development fitting and screening

- Keep the M1 10-channel shape-preserving CNN and CPU `float32` representation.
  Small `(3,6,12)` and large `(6,12,24)` spatial tensors form separate
  batches; neither mesh is resized or interpolated. Each train case is seen
  once per epoch. Both fixed arms use the same seed-specific shuffle and
  optimizer-step order, and each selects its own earliest strict validation
  objective minimum. The candidate's audited sensitivity weights multiply
  design-density squared error and are not inference inputs.
- Every B2.5 validation case uses a projected-uniform reference and all other
  methods under the same 240-update physical-plateau solver. Charge setup,
  projection, full refinement, quality decision, and a fresh uniform fallback
  for every failed candidate; preserve the failed status. Matched independent
  compliance, physical volume, and `1.001` uniform-quality checks precede
  acceptance. Exact population and thresholds are in the
  [B2.5 protocol](planning/b2_5_prototype_protocol.md).

## B2.6 intermediate-trajectory development target

- The B2.6 target is the uniform solver's post-update, re-solved **design**
  density at update 30 under the unchanged 240-update physical-plateau policy.
  If uniform converges earlier, use the earlier terminal state and record its
  actual update. Capturing through the public iteration callback changes no
  OC, filter, stiffness, solve, or stopping rule.
- Persist target density as CPU float32 in `(1, nz, ny, nx)` order. Independently
  reconstruct filtered physical volume from that persisted design and require
  error `<=0.005`. The target is for offline training only, never an inference
  input. Checksum-bind its case ID, split, solver/plan revision, and source
  revision; keep artifacts outside Git.
- The separately selected CNN prediction undergoes the existing filtered-
  volume projection, full SIMP refinement, matched uniform quality check,
  and fresh uniform fallback. The label-informed own-trajectory oracle is
  explicitly nondeployable and its target-generation cost is separate. Exact
  populations, resource caps, and Gate are frozen in the
  [B2.6 protocol](planning/b2_6_trajectory_protocol.md).

## B2.7 opt-in global point-load representation

- Keep the historical ten-channel case encoding unchanged. The B2.7 candidate
  alone replaces channels 3–5 with a signed, globally visible load-distance
  field for exactly one point load. For normalized element center `c` and load
  node `q`, use `1 - sqrt(sum_axis((c_axis-q_axis)^2)/3)` in the selected load
  direction, multiplied by the load sign; set other load channels to zero.
  Support, coordinate, and volume channels, CPU float32, `(z,y,x)` tensor
  order, and x-fast flattening are unchanged.
- The opt-in encoding version is `topolab.b2_7.global_load_distance.v1`.
  Historical checkpoints still use their original encoding. This feature
  requires no FEM solve at query time, but all encoding/inference setup is
  charged to B2.7's complete candidate time. The [B2.7 protocol](planning/b2_7_global_load_protocol.md)
  freezes its fitting artifacts, screen, resource caps, and Gate.

## B2.9 opt-in vector point-load representation

- The B2.9 candidate alone uses 13 CPU float32 channels in `(channel,z,y,x)`
  order. Keep the historical support channels 0–2, normalized element-center
  coordinates 6–8, and target-volume channel 9. Replace load channels 3–5
  with a spatially constant signed one-hot load direction. Append channels
  10–12 as the normalized element-center position minus the normalized
  loaded-node position, one coordinate per axis. Require exactly one valid
  point load and reject nonfinite or out-of-range relative coordinates.
- The opt-in encoding version is `topolab.b2_9.vector_load.v1`. Its
  shape-preserving CNN is `topolab.b2_9.vector_cnn.v1`, with two local 3³
  convolutions, 16 hidden channels, and 12,577 parameters. Historical
  encodings and checkpoints retain their original identities. Charge all
  encoding and inference setup to the candidate. The
  [B2.9 protocol](planning/b2_9_vector_load_protocol.md) fixes the targets,
  fit, screen, resource caps, and development Gate before execution.

## B2.10 offline sensitivity-weighted trajectory objective

- Keep the B2.9 vector input, CNN, update-30 design-density target, and all
  query-time projection, solver, quality, and fallback conventions. At each
  stored B2.6 train/selection target, independently filter and re-solve its
  float32 design state. Back-propagate the absolute physical-compliance
  sensitivity through the density filter to design density. Divide by its
  within-case mean, clip to `[0.25,4]`, and divide by the clipped mean.
  Persist the resulting positive CPU float32 weights in target tensor order;
  their within-case mean must be within `1e-6` of one. This is the B2.4
  sensitivity-weight rule evaluated at the intermediate target state.
- Fit and select each seed by the elementwise mean of
  `weight * (prediction - target)**2`. Weights are offline loss data, never
  query inputs. Version the weights and model selection separately from B2.9;
  historical checkpoints retain their original MSE objective. The
  [B2.10 protocol](planning/b2_10_weighted_trajectory_protocol.md) freezes
  the source artifacts, fresh screen, resource limits, and development Gate.

## B2.11 opt-in reference iteration budget

- B2.11 keeps the `topolab.simp.physical_plateau.v1` numerical solver and all
  OC, filter, stiffness, material, load, stopping, and independent quality
  tolerances unchanged. Only the development comparison's per-case
  `optimization.max_iterations` changes from 240 to 360 for **every** method.
  The public default and all historical 240-update outcomes remain intact.
- Since the cap is part of the physical-case identity, a 360-update case gets
  a new ID, explicitly mapped to its 240-update source where applicable.
  The [B2.11 protocol](planning/b2_11_reference_budget_protocol.md) freezes
  the old/new sentinel, independently checked new references, fresh screen,
  resource caps, and two unchanged-model panel Gates before execution.

## B2.12 opt-in spatial-context model

- Keep the B2.9 13-channel vector-load encoding, B2.6 update-30 design-density
  target, unweighted MSE, filtered-volume projection, full SIMP refinement,
  360-update B2.11 comparison budget, independent quality re-solve, and fully
  charged fresh uniform fallback unchanged. The B2.12 intervention changes
  only the learned CNN's spatial context: four 3³ convolutions of width 16
  with `(z,y,x)` dilations `(1,1,1)`, `(1,1,2)`, `(1,2,4)`, `(1,2,8)`,
  matching padding, ReLU between them, and a one-channel sigmoid head.
- The model version is `topolab.b2_12.context_cnn.v1` with 26,433 trainable
  parameters. It is opt-in development evidence; historical checkpoints and
  public defaults are unchanged. The [B2.12 protocol](planning/b2_12_context_cnn_protocol.md)
  fixes source artifacts, fresh references, fitting, complete screen, caps,
  and Gate before execution.

## B2.13 opt-in workload routing

- B2.13 changes only the query-time choice among audited B2.9/B2.12
  checkpoints and a metadata-only safe rejection to fresh uniform. The fixed
  small/large mesh, y/z direction, volume range, and `0.55` large-y rejection
  boundary are in the [B2.13 protocol](planning/b2_13_routing_protocol.md).
  Unsupported case metadata also rejects to uniform. No new weights, encoder,
  SIMP behavior, or quality tolerance are introduced.
- Charge the route decision before a selected model's full existing query
  path. A rejected case pays decision plus fresh uniform time without being
  counted as a failed learned attempt. A selected model failing independent
  quality pays its full attempt plus a separate fresh uniform fallback and
  retains failed status. All B2.13 results have a new experiment identity.

## B2.14 development confirmation

- Keep the B2.13 route, four already audited single-model checkpoints,
  360-update solver, independent quality check, and fully charged rejection
  and fallback semantics unchanged. The [B2.14 protocol](planning/b2_14_development_confirmation_protocol.md)
  freezes 24 disjoint physical cases, uniform references, comparators,
  resource limits, eligibility criteria, and deterministic policy selection
  before opening new outcomes. This is development evidence only; public
  uniform initialization and earlier case/result identities remain unchanged.

## B2.18 opt-in solver-anchored initialization

- Independently project the verified B2.12 context-17 prediction and run two
  uniform post-update SIMP states under the unchanged physical-plateau policy.
  Blend their **design** densities elementwise with fixed weights `0.5/0.5`,
  then project the blend to the existing filtered physical-volume target.
  This differs from blending with the constant initial uniform field.
- Start a fresh 360-update SIMP solve at the projected blend. The two-update
  anchor is charged query work, not a reference or terminal-quality decision.
  The new solve's own history and plateau state begin at its first update;
  its predecessor's two updates do not count toward that history. Existing
  independent terminal compliance/convergence/volume checks and fresh
  uniform fallback charges remain unchanged. See the
  [B2.18 protocol](planning/b2_18_solver_anchor_protocol.md).

## B2.19 opt-in uniform-state sensitivity input

- For the fixed one-point-load development workload, solve linear elasticity
  exactly once at the case's constant physical density equal to its volume
  fraction, using the unchanged mesh, supports, signed load, material, SIMP
  penalty, and factorization ordering. Take the negative compliance derivative
  per x-fast element as nonnegative strain-energy information. Reject
  nonfinite, negative, or all-zero energy.
- Divide each energy by its positive case mean, apply `log1p`, then divide by
  the maximum `log1p` value in that case. Reshape x-fast values to `(nz,ny,nx)`
  and append them as channel 14 to the unchanged 13-channel B2.9 input.
  The feature lies in `[0,1]`. This solve is part of every learned query's
  measured setup cost, including attempts that fail and pay uniform fallback.
- Keep the B2.12 four-convolution topology, B2.6 update-30 target, unweighted
  MSE, fixed seeds and training recipe, projection, 360-update refinement,
  and independent terminal quality and fallback rules. Only the first
  convolution expands from 13 to 14 channels, making 26,865 parameters.
  The [B2.19 protocol](planning/b2_19_physics_input_protocol.md) freezes
  disjoint development cases and all resource and performance Gates.

## B2.20 opt-in operational checkpoint selection

- Keep B2.12's 13-channel vector-load input, four-layer spatial CNN,
  B2.6 update-30 density target, unweighted MSE optimizer/shuffle/early-stop
  recipe, three seeds, 360-update physical-plateau solver, filtered-volume
  projection, and independent quality/fallback rules. Capture CPU `float32`
  weights at fixed epochs `80,120,160` when reached, plus the unchanged
  earliest minimum-MSE checkpoint. Capturing copies weights without changing
  gradient updates or random-number consumption; verify the MSE-best weights
  elementwise against audited B2.12 checkpoints.
- On disjoint development selection cases, evaluate each fixed checkpoint
  with full refinement and complete fallback charges. Per seed, select
  lexicographically by fewest terminal quality failures, then lowest worst
  mesh-scale/direction mean paired time ratio, lowest overall arithmetic
  mean ratio, and earliest epoch. The [B2.20 protocol](planning/b2_20_operational_selection_protocol.md)
  fixes both selection and later screen populations and resource Gates.

## B2.21 opt-in terminal-design learning target

- Keep B2.12's 13-channel vector-load input, context CNN, unweighted
  MSE/AdamW fitting recipe, three seeds, projection, 360-update
  physical-plateau query solver, independent quality checks, and fully
  charged fallback unchanged. Replace only the supervised update-30
  design-density target with the uniform solver's converged terminal
  **design** density. Historical B2.12/B2.20 weights and results retain
  their own identities.
- Read the 468 audited B2.4 `train` terminal labels by checksum. For the
  same twelve B2.6 validation case definitions, generate new budget-240
  terminal targets and require independent convergence, compliance, and
  physical-volume quality before fitting. Persist CPU float32 targets
  in `(1,nz,ny,nx)` order, bound to case/source context and checksum.
  Labels are offline loss data, never query inputs. The
  [B2.21 protocol](planning/b2_21_terminal_target_protocol.md) freezes
  case separation, resource caps, comparison methods, and Gate.

## B2.22 opt-in high-volume y specialist

- Reuse B2.21's audited terminal **design** labels, B2.9 thirteen-channel
  input, and B2.12 context CNN. In each training batch, calculate one
  elementwise MSE per case; weight the 52 y-direction cases with volume
  fraction `>=0.55` by `8` and the other cases by `1`, then divide by the
  sum of those case weights. Select by earliest strict minimum unweighted
  MSE on the two y-direction, volume-`0.525` validation targets, one per
  mesh scale. The unchanged B2.21 targets and B2.12 checkpoints remain
  separate artifacts.
- Route to the specialist only for `(24,12,6)` mesh, y direction, and
  volume fraction `>=0.55`; use the matched B2.12 context model elsewhere.
  Charge routing, encoding, inference, projection, full refinement,
  quality decision, and fresh uniform fallback. The
  [B2.22 protocol](planning/b2_22_y_specialist_protocol.md) freezes the
  disjoint screen, numerical quality, timing, resources, and Gate.

## B2.23 development-label position expansion

- Preserve the B2.3/B2.4 240-update physical-plateau label solver,
  convergence tolerance, uniform initialization, B2.4 CPU float32
  terminal-design/physical-density artifact schema, independent stored-state
  compliance check, and physical-volume error limit `0.005`. Give each
  B2.23 case a new result identity linked to its own 120-update source
  definition; previous B2.4 labels retain their IDs and outcomes.
- Materialize only the fixed large-mesh high-volume y train/validation
  position grid in the [B2.23 protocol](planning/b2_23_position_labels_protocol.md).
  Its labels are offline development data and never query inputs. No model
  fitting or learned comparison occurs in B2.23.

## B2.24 opt-in expanded-position specialist

- Add exactly 20 audited B2.23 **train** terminal-design labels to the
  unchanged 468-case B2.22 training population. Keep the case-weight-8
  high-volume y objective, thirteen-channel input, context CNN, optimizer,
  seeds, batch size, epoch/patience caps, and B2.22's two-case checkpoint
  selection rule. The opt-in training population has 488 cases and 61
  shape-bucketed batches per epoch; historical fitting retains 468 and 59.
- Audit the ten B2.23 **validation** labels as fixed-checkpoint diagnostic
  targets only. Preserve B2.22's route, projection, 360-update
  physical-plateau refinement, independent compliance/volume checks,
  failure status, and complete uniform fallback charges. The
  [B2.24 protocol](planning/b2_24_expanded_training_protocol.md) fixes
  exposure, disjoint screen, resource caps, and development Gate.

## B2.25 read-only residual diagnosis

- The [B2.25 protocol](planning/b2_25_residual_cost_protocol.md) reads only
  B2.24's already exposed, checksum-bound development indices. It recomputes
  paid timing and quality invariants before any cost decomposition.
- Its fallback-free, large-z-zero, and combined values are optimistic
  **speed-only** arithmetic bounds. Failed learned attempts remain failures;
  no solver, quality, routing, or operational-default convention changes.

## B2.26 opt-in weighted terminal generalist

- Retain B2.21's terminal-design target, input, context CNN, train and
  validation case identities, and unweighted twelve-case checkpoint
  selection. Give exactly the 78 y-direction train cases at volume
  `>=0.5` case weight `8`, the other 390 weight `1`. The
  [B2.26 protocol](planning/b2_26_weighted_generalist_protocol.md)
  fixes the new fit and physically disjoint screen.
- On the high-volume large-y route, reuse the unchanged B2.24 expanded
  specialist for all three panels; elsewhere compare B2.12 context,
  B2.21 unweighted terminal, and B2.26 weighted terminal generalists.
  Projection, solver, terminal quality, full fallback accounting, and
  the uniform operational default do not change.

## B2.27 development-only middle-volume position labels

- Keep the B2.3/B2.4 240-update physical-plateau uniform label solver,
  convergence tolerance, B2.4 CPU float32 terminal-design and physical-
  density artifact schema, independent stored-state compliance check,
  and physical-volume error limit `0.005` unchanged. Give every new
  label a B2.27 result identity linked to its 120-update source definition.
- Materialize only the fixed large-mesh middle-volume y/z train and
  validation position grid in the [B2.27 protocol](planning/b2_27_middle_volume_labels_protocol.md).
  The labels are offline development data and never query inputs. No
  model fitting or learned comparison occurs in B2.27.

## B2.28 opt-in expanded middle-volume generalist

- Add exactly 40 audited B2.27 train terminal-design labels to the
  468-case B2.26 generalist population. Keep case weight `8` for y
  cases at volume `>=0.5` and `1` elsewhere, giving 98 weighted cases
  and 410 other cases. Keep the thirteen-channel input, context CNN,
  optimizer, seeds, and twelve-case unweighted MSE selection rule.
  The 508 cases form 64 shape-bucketed batches per epoch.
- Read the 20 B2.27 validation labels only as diagnostic targets for
  fixed selected checkpoints. Retain the B2.24 specialist route,
  360-update physical-plateau refinement, terminal quality checks,
  and full fallback charges. The [B2.28 protocol](planning/b2_28_expanded_generalist_protocol.md)
  fixes the fresh screen, resource limits, and development Gate.

## B2.29 fixed-checkpoint development confirmation

- Preserve all B2.28 selected checkpoints and the B2.24 specialist
  route. The larger independent cohort introduces no fitting or
  numerical intervention; its [frozen protocol](planning/b2_29_development_confirmation_protocol.md)
  binds 48 cases and all 432 outcomes.
- Retain the fixed physics heuristic and the original B2.4 train-only
  nearest neighbor. Use a fresh timed uniform per screen case after
  all mandatory references pass; require its independently checked
  compliance to agree with the mandatory reference within `rtol=1e-9`.
  Quality tolerances and full fallback charges remain unchanged.

## B3 versioned formal experiment boundary

- The [B3 contract](b3_experiment_contract.md) retains the physical-plateau
  equations, A3 ordering, projection, independent terminal-state checks,
  and all numerical tolerances. It freezes 360 updates for both newly
  generated labels and query refinement; 240-update source definitions
  receive explicitly linked new case IDs. Historical labels are not B3
  fitting inputs.
- The supplementary B3 exposure fingerprint hashes the normalized full
  problem with only `optimization.max_iterations` removed, using compact,
  sorted-key ASCII JSON and one terminal newline. It prevents a budget
  variant from crossing training/validation/final exposure boundaries.
  Case IDs retain their existing complete-problem convention.
- B3's fixed twelve CPU fits use the existing thirteen-channel context CNN
  and terminal design targets. Case weights affect fitting only; earliest
  strict minimum unweighted per-case MSE selects each checkpoint on its
  frozen fit-validation subset. A separate screen selects the deployment
  seed by the prospective rule, with every seed and failure retained.
- Final per-case costs include all routing, inference, projection,
  refinement, quality decision, rejection, and fresh uniform fallback.
  The selected primary and paired statistics are frozen before final
  access; independent replication uses the same artifacts and fresh local
  references. Planning completion is distinct from Gate B3 and B5 evidence.

## B4 query evidence and prospective screening

The B4 development query boundary preserves the B3 equations and tolerances.
Its versioned outcome witness retains the full terminal state, complete scalar
trajectory and last eleven full density states, sufficient for independent
terminal filtering, volume, design-change and physical-plateau reconstruction.
Query failures and fresh uniform fallback retain separate status and full
phase charges. Exact query, audit, recovery and prospective-freeze semantics
are in the [B4.2 implementation contract](b3_screening_contract.md).

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

## M1 held-out experiment and statistics

- One evaluation context is identified by the frozen data-manifest digest, the exact
  five ordered selection and checkpoint references, the clean evaluation source
  revision, and the locked CPU runtime/thread metadata.
- Evaluate only `test` and `ood` samples, in canonical manifest order. One atomic
  checkpoint entry contains all three fixed baselines and all five learned seeds for
  one physical case; an interrupted case remains pending and is rerun in full.
- The recoverable index is append-only. Completion requires exactly every frozen
  test and OOD case, while train/validation cases are forbidden as entries.
- Every time ratio uses the matching case's uniform end-to-end time as denominator.
  Seed-specific median and interquartile range use NumPy linear quantiles over all
  cases in that split. Aggregate learned summaries flatten all five seed observations
  only for descriptive median/IQR and failure/fallback rates.
- For the primary learned mean-time ratio, arrange observations as
  `(physical case, five seeds)`. Independently for test and OOD, initialize
  `numpy.random.default_rng(20260919)`, draw 10,000 case-index samples with
  replacement, retain all five seeds in each sampled case, average across sampled
  cases and seeds, and take the linear 2.5th/97.5th percentiles.

## M2 bounded follow-up

- M1 held-out cases are development-exposed and cannot serve as M2 validation or
  final evidence. All M2 validation and ID-test cases must be physically absent from
  the M1 catalog.
- The M2 fixed-shape catalog has 504 `y/z` ID cases and 252 matched `x`-direction OOD
  cases. Its exposure-aware, direction/volume-stratified split contains 432 train,
  36 validation, 36 ID-test, and 252 OOD cases.
- Its production entrypoint requires a clean locked checkout and an external output
  root, defaults to a read-only plan, and requires `--execute` to invoke the solver.
  M2 checkpoints use `topolab.m2.materialization.v1`; the shared executor rejects an
  index version that does not match the embedded M0 or M2 manifest contract.
- M2 reuses the exact M1 architecture, design-density MSE, optimizer recipe, fitting
  budget, and five seeds. Expanded direction-balanced data is the only fitting
  intervention.
- The five-model ensemble averages independently projected seed predictions and is
  projected again before refinement. Its uncertainty is the mean elementwise
  population variance across those projected predictions.
- Reliability-gate calibration is limited to reject-all, five validation uncertainty
  percentile thresholds, and accept-all. Only zero-failure validation policies are
  eligible; mean paired time ratio selects among them with conservative fixed ties.
- Gate rejection runs and charges uniform after all ensemble setup but is not a
  learned failure. An accepted failed attempt runs a fresh fully charged uniform
  fallback and remains failed.
- M2 ID-test and OOD label artifacts are forbidden to fitting, calibration, and final
  evaluation adapters. Exact cohort, split, calibration, statistics, and stopping
  rules are frozen in `docs/m2_experiment_contract.md`.

## B4.4 versioned engineering timing boundary

`topolab.b4_4.engineering.v1` preserves the B3 numerical solver, termination and
quality conventions. Its outer wall and process-CPU clocks include the full
query, terminal-witness construction, callbacks and any fresh uniform fallback.
Callback/flush durations are inclusive diagnostic channels and are never
subtracted from reported wall time. Immutable result serialization/publication,
independent terminal audits and boundary progress are additional charged stage
costs. Report that residual and the full stage charge; do not silently treat
persistence or failure recovery as free. The stopped B4.2 phase timings remain
unchanged. The finite matched sentinel and acceptance thresholds are frozen in
`docs/planning/b4_4_engineering_protocol.md`.

## B4.5 opt-in spatially weighted terminal loss

The [B4.5 contract](planning/b4_5_weighted_terminal_protocol.md) multiplies
elementwise squared terminal-design error by the audited B3 mean-one spatial
sensitivity weights, averages within each case, then uses the unchanged P
case-weight-normalized batch objective. It retains unweighted equal-case
validation selection, all numerical equations, query quality thresholds and
specialist routing. Its new query timing pays the complete outer envelope plus
a fixed conservative one-second recording allowance for every method, verified
against actual durable recording wall. Independent audits and preparation are
additional charged offline stage costs. Old contracts and timings are unchanged.

## B4.6 independent confirmation boundary

The [B4.6 protocol](planning/b4_6_confirmation_protocol.md) doubles the fixed
B4.5 development workload to 96 physically disjoint cases while retaining
all twelve methods and the same query/quality conventions. W/17 is fixed
before confirmation; there is no fitting or outcome-based primary reselection.
The unchanged paired seed criteria require two passing seeds; the pooled
large-y minimum remains two-thirds (12/18 per middle/high volume). W/17 also
requires total charged time ratio <=0.90 at each scale. Recording, fallback,
startup and independent audits remain fully charged. No numerical tolerance
or solver behavior changes, and no final artifact is opened in this slice.
