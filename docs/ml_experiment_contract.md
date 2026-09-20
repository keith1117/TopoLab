# M0 machine-learning experiment contract

Status: **contract slice frozen at `m0.v1`**. This document freezes case identity,
representation, split, label, baseline, and evaluation semantics before any dataset
generation or model training. M0 is not complete until a later slice implements and
validates the generator and manifest against this contract.

## Scope and claims boundary

The first experiment asks one question: can a predicted design-density warm start
reduce the end-to-end time required by the existing SIMP solver to reach a result of
the same quality as a uniform start?

This slice does not generate cases, add PyTorch, train a model, select
hyperparameters, or support an `accelerated` claim. It also does not turn optimizer
history rows into independent samples. The numerical and platform contracts remain
unchanged.

## Versioned case schema and identity

`topolab.experiment.ExperimentCase` wraps the frozen `TopologyProblem` contract with:

- `schema_version = "topolab.m0.case.v1"`;
- a verified `case_id` with prefix `tlcase-v1-`; and
- a complete `problem` containing mesh, material, supports, loads, and optimization
  settings.

`initial_density` must be `null`. Initialization is a method under evaluation, not
part of physical case identity. The identity includes all other problem fields:

| Section | Identity fields |
|---|---|
| Mesh | `(nx, ny, nz)` element counts and `(Lx, Ly, Lz)` lengths |
| Material | solid modulus, minimum modulus, and Poisson ratio |
| Supports | face axis/side and every constrained displacement direction |
| Loads | load kind, selector, signed component direction, and signed magnitude/resultant |
| Optimization | target physical volume fraction, filter radius, penalty, minimum density, move limit, convergence tolerance, and maximum iterations |

The ID is the full lowercase SHA-256 digest of canonical UTF-8 JSON, prefixed with
`tlcase-v1-`. Canonical JSON uses sorted object keys, no insignificant whitespace,
JSON arrays for tuples, and the exact validated finite floating-point values. Support
directions use `x/y/z`, repeated constraints on the same face are merged, and support
and load order is canonicalized. Load multiplicity is retained because repeated
loads superpose physically. Any future canonicalization or field change requires a
new schema version and ID prefix; existing IDs must never be silently reinterpreted.

The stored `problem` is normalized to the same direction names and support/load
ordering when an `ExperimentCase` is constructed or read. The serialized `case_id`
is checked on every read. A stale or manually edited ID is invalid. Dataset manifests
must reject duplicate case IDs rather than silently overwrite them.

## Model cohort and input tensor

Version `m0.v1` uses one fixed-shape cohort per model. Every case in a cohort must
have identical element counts, physical lengths, material values, filter radius,
penalty, minimum density, move limit, convergence tolerance, and maximum iterations.
These values remain in each case and the manifest for auditability. Within a cohort,
supports, loads, and target volume fraction may vary. Combining cohorts or adding
constant-parameter channels requires a later contract version.

The input is a channel-first `float32` tensor with shape
`(10, nz, ny, nx)`. Spatial indexing is `(ez, ey, ex)`; `ex`/`x` is the fastest axis,
matching the numerical element index `ex + nx * (ey + ny * ez)`.

| Channel | Meaning |
|---:|---|
| 0 | `support_x`: 1 where an element touches at least one node constrained in `ux`, else 0 |
| 1 | `support_y`: same rule for `uy` |
| 2 | `support_z`: same rule for `uz` |
| 3 | `load_x`: dimensionless element-scattered signed `fx` |
| 4 | `load_y`: dimensionless element-scattered signed `fy` |
| 5 | `load_z`: dimensionless element-scattered signed `fz` |
| 6 | `coord_x = (ex + 0.5) / nx` |
| 7 | `coord_y = (ey + 0.5) / ny` |
| 8 | `coord_z = (ez + 0.5) / nz` |
| 9 | target physical volume fraction broadcast to every element |

Load channels are derived from the final nodal vector produced by the existing load
contract, after point loads and equal-node face resultants have superposed. Each
nodal component is divided equally among its incident elements, so summing one raw
voxel component reproduces the corresponding nodal resultant. All three raw channels
are then divided by the single positive scale `sum(abs(global_load_vector))`. This
keeps sign, direction, location, and relative magnitude while removing the irrelevant
single-load-case force scale. The scale is stored in sample metadata. A zero scale is
an invalid case.

No axis transposition, image-style `y` reversal, or implicit batch dimension is
allowed. Batches add one leading dimension: `(batch, 10, nz, ny, nx)`.

## Label and warm-start density definitions

Both label arrays are `float32` tensors of shape `(1, nz, ny, nx)` with the same
`(ez, ey, ex)` spatial order:

- `design_density` is the final OC design variable `x` and lies in
  `[minimum_density, 1]`;
- `physical_density` is the final filtered field `rho = (H @ x) / Hs`, lies in the
  same interval, and is the field used for stiffness, compliance, and the physical
  volume constraint.

The supervised prediction target for the first model is final `design_density`.
`physical_density` is retained for physical checks and optional auxiliary losses,
but it must not be passed directly as the optimizer's design initialization.

Model inference produces a finite raw design field `y` in `[0, 1]`. Before SIMP, it
is projected to the requested physical volume:

```text
x(lambda) = clip(y + lambda, minimum_density, 1)
rho(lambda) = (H @ x(lambda)) / Hs
choose lambda so abs(mean(rho(lambda)) - volume_fraction) <= 1e-6
```

Bisection uses the bracket `[-1, 1]` and at most 100 iterations. The same projection
is used for baseline warm starts. Wrong shape, non-finite values, values outside
`[0, 1]`, or failure to meet the projection tolerance triggers the uniform fallback.

## Label generator and termination

Every label record and dataset manifest must store:

- `case_schema_version = "topolab.m0.case.v1"`;
- `generator_version = "topolab.m0.generator.v1"`;
- `solver_contract_version = "topolab.simp.v1"`;
- the exact 40-character TopoLab Git commit SHA from a clean worktree;
- the locked-environment digest and Python/NumPy/SciPy versions; and
- the full case ID and problem payload.

Labels are generated only through `topolab.simp.optimize_simp` from its uniform
default design (`x_e = volume_fraction`). The per-case optimization fields define the
filter, OC update, and termination settings. A label converges only after an OC update
and fresh finite-element solve produces
`max(abs(x_new - x_old)) <= convergence_tolerance`. Reaching `max_iterations`
without that condition is a generation failure, not a successful label. The stored
design density, physical density, compliance, volume, and change must all describe
the same final state, as required by the N2 contract.

Changing code revision does not change physical `case_id`; it creates a new label
artifact version. Two labels for the same case and generator version but different
revisions may coexist only for an explicit reproducibility comparison and may not be
mixed in one training dataset.

## Dataset split and leakage prevention

Splitting is by complete `case_id`, before tensorization, augmentation, or access to
labels. A case, every optimizer history state, every derived tensor, and every repeat
remain in exactly one partition. Final labels are the only supervised samples in
`m0.v1`; history rows are not samples.

The primary in-distribution pool contains cases whose nonzero loads are all in the
`y` direction. Assign each ID case with:

```text
h = sha256(utf8("topolab.m0.split.v1:" + case_id))
bucket = int(first 8 hex digits of h, 16) % 100
train: 0..79; validation: 80..89; test: 90..99
```

The manifest records the resulting counts; it must not move cases to improve the
ratio after labels or metrics are inspected. Model fitting and hyperparameter choices
use train/validation only. Test labels remain unopened until the experiment plan and
checkpoint-selection rule are frozen. Nearest-neighbor search uses training cases
only.

The predeclared primary OOD axis is **load direction**. OOD cases are matched to ID
cases by mesh, material, support, load kind/location/magnitude, volume fraction, and
optimizer settings, but every `y` load component is changed to `z`. Mixed-direction
loads and `x`-directed loads are outside the primary `m0.v1` evaluation. OOD cases
never enter the hash split or model selection.

## Fixed baselines

All methods use the same volume projection and the same refinement solver/settings.

1. **Uniform.** Set every design element to the target volume fraction. A constant
   field is unchanged by the normalized density filter.
2. **Physics heuristic.** Solve once at uniform physical density. For each element,
   set `s_e = max(0, -dC/drho_e)` from the analytical compliance sensitivity. If
   `max(s) > min(s)`, min-max normalize `s` to `[0, 1]`; otherwise use the uniform
   field. Project the result to the target physical volume. The extra finite-element
   solve is part of baseline setup time.
3. **Nearest neighbor.** Among training cases in the same fixed-shape cohort, choose
   the smallest mean-squared distance between the complete 10-channel input tensors;
   break exact ties by lexicographically smallest `case_id`. Use that case's final
   design-density label, then re-project it to the query volume fraction. Query time
   and stored-index size are reported; validation, test, and OOD labels are never
   candidates.

No baseline may use a query label, final compliance, or optimizer history to choose
its initialization.

## Quality constraints and failures

The uniform method is the per-case quality reference. A refined candidate succeeds
only when all of the following hold:

- the solver reports convergence before the iteration limit;
- every returned density, displacement, reaction, compliance, and history metric is
  finite;
- `abs(mean(final_physical_density) - volume_fraction) <= 5e-3`;
- independently re-solving the final physical density reproduces final compliance
  within `rtol=1e-9`; and
- final compliance is no greater than `1.001 * uniform_final_compliance`.

A solver exception, invalid prediction, projection failure, non-convergence, quality
violation, missing artifact, or schema/version mismatch is a failure. A case whose
uniform reference fails is a dataset/evaluation failure and is reported separately;
it must not be used to make another method's failure rate look smaller.

## Cost and statistical reporting

Report at least these per-case values for every method:

- warm-start setup time (heuristic solve, neighbor query, or model preprocessing and
  inference);
- volume-projection time;
- SIMP refinement time and iteration count;
- end-to-end time, defined as the sum of the preceding three;
- final compliance, physical volume error, convergence/failure, and fallback use; and
- peak process memory where the runner can measure it reproducibly.

Dataset generation time, training time, hardware, thread count, and artifact size
are reported separately and are never hidden inside an amortized speedup claim.
Learned end-to-end time includes host/device transfer and synchronization.

Use model/training seeds `[17, 29, 43, 71, 113]`. Report every seed, not only the
best. The primary comparison is the paired per-case end-to-end time ratio to uniform,
reported separately for ID test and OOD. The 95% confidence interval uses 10,000
case-cluster bootstrap resamples with seed `20260919`; each resampled case retains all
five model seeds. Also report median, interquartile range, failure rate, and quality
metrics without dropping failed cases.

An acceleration claim requires the upper bound of the ID-test 95% confidence
interval for the mean learned/uniform end-to-end time ratio to be below 1.0, all
quality constraints to hold, and no increase in failure rate. OOD results are always
reported but are not relabeled as in-distribution evidence.

## Fallback and stopping rule

If model output validation or projection fails, run uniform initialization. If a
learned refinement fails a quality constraint, rerun from uniform. The fallback's
full time is added to learned end-to-end cost, and the event remains a learned-method
failure; fallback must not convert it into a learned success.

After the fixed lightweight model family, finite hyperparameter budget, five seeds,
and ID/OOD evaluation are complete, an inconclusive or negative result is frozen and
analyzed. It does not authorize unbounded search. In that outcome the project keeps
uniform as its operational default and does not use `learned-accelerated` wording.
