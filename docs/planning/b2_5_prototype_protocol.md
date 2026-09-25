# B2.5 fixed two-arm development prototype

Status: frozen before B2.5 fitting and validation execution. This is a
development screen on B2.4's exposed train/validation population, not a new
final experiment or an acceleration claim.

## Data, arms, and exact fitting schedule

Require the B2.4 external index SHA-256
`dad9109aca6d4e14a851c266fd1b8a490885cf2565281ee85ceba1d164f59244`
and canonical plan SHA-256
`015ab799be88a5fef763720b2e1c58281dc17aea67c61435bcb87d254f64169c`.
The label source revision is
`7f4d0f6a1512b5be8f6ea192430608108bafe2cc`. Admit exactly 468 train
and 54 validation cases, without test/OOD labels or outcomes. Verify every
artifact checksum, source/result identity, split, mesh shape, and stored
state before fitting. Input is the frozen ten-channel `float32` case tensor;
target is stored final **design** density. Sensitivity weights are a loss
target only, never an inference feature.

The B2.5 read-only plan has canonical SHA-256
`03978254d4cba90113a83813109e0415201885e66c28c1b7cc7bf9e5b392c5ff`.

Use the unchanged M1 11,281-parameter shape-preserving CNN in both arms.
The control uses elementwise design MSE. The candidate uses mean
`weight * (prediction - design)^2` with B2.4's audited weights. Seeds are
`17, 29, 43`. For each seed, initialize both arms identically and use the
same case/batch order. Use AdamW with learning rate `1e-3`, weight decay
`1e-4`, betas `(0.9,0.999)`, epsilon `1e-8`; CPU float32; batch size at
most 8; at most 200 epochs; patience 25; strict earliest minimum of each
arm's own validation objective. No augmentation, architecture search,
hyperparameter search, or seed exclusion.

At each epoch, shuffle lexicographically sorted case IDs independently
within the two shapes using a seed-specific CPU generator. Make consecutive
batches of at most eight within each shape, then shuffle the 59 resulting
batch descriptors using the same generator. Thus every one of 468 training
cases occurs exactly once per epoch, with 54 small and five large optimizer
steps. The two arms of a seed repeat the identical generator sequence from
the same seed, so sample exposure and optimization steps match. Never resize
or interpolate a mesh. Validation runs in sorted case-ID order within each
shape, without gradients; compute each arm's objective as the sum of weighted
or unweighted squared errors divided by the exact total number of validation
elements. Selected checkpoints and complete epoch histories are
checksum-addressed external artifacts with source revision, data index,
runtime, arm, and seed identity. A halted fit restarts only that unfinished
arm/seed; completed artifacts are verified before reuse.

The **complete six-fit** execution, including data loading and checkpoint
audits, has a cumulative cap of four hours wall and 2 GiB peak process RSS
on the declared single-thread local machine. Stop and fail the fitting Gate
if either cap is exceeded. No validation case or seed can be dropped.

## Version-matched development screen

After all six fits pass artifact audit, screen **all 54 exposed validation
cases**. For each case run a fresh, projected-uniform reference under the
same `topolab.simp.physical_plateau.v1` policy and 240-update case budget.
Also run the frozen physics-sensitivity heuristic and a shape-matched
training-only nearest-neighbor design baseline, each with the same policy,
quality rule, and fully charged fallback. Evaluate all six learned
checkpoints without using query labels or sensitivities as inference inputs.
The case order and nine methods per case are fixed before execution; retain
every outcome. One-time model and nearest-neighbor index loading are reported
separately from per-query time.

Every attempt pays its actual setup/inference, filtered-volume projection,
decision, full refinement, and quality-check time. Rejected or invalid
attempts pay a **fresh** complete uniform fallback; the failure status stays
failed. Require solver convergence, finite positive compliance independently
re-solved within relative `1e-9`, physical-volume error `<=0.005`, and final
compliance no worse than `1.001` times the matched uniform reference before
an attempt counts as accepted. Include all fallback costs in the paired time
ratio. Write one atomic outcome checkpoint per complete physical case;
interrupted cases rerun in full. This screen has a separate four-hour wall
and 2 GiB peak RSS cap; an overrun fails the screen under this plan.

At least one arm advances only if at least **two of its three seeds** have
fallback-inclusive mean ratio `<=0.90` at **both** mesh scales, no accepted
quality failure, and direction-wise mean ratio `<=1.0` at both scales.
Report every seed, arm, scale, direction, volume, failure, fallback, phase
cost, and fixed non-ML baseline. This is a development threshold, not the
fresh v2 final confidence-interval delivery Gate. If neither arm passes,
preserve the negative result and diagnose one new versioned intervention;
do not register B3 from a failed prototype or search on a final cohort.
