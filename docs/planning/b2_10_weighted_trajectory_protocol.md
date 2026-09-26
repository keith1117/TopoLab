# B2.10 sensitivity-weighted intermediate-trajectory objective

Status: frozen before B2.10 weight generation, fitting, or screening. This
is one development-only **training-objective** intervention. The read-only
plan version is `topolab.b2_10.weighted_trajectory.v1`; its canonical SHA-256
is `d3fd19a8a16d4d7d6dc2ae02a731de45654a53c0d5e44c1945331cbf61f1a079`.
It cannot by itself establish final v2 acceleration.

## Measured motivation and single intervention

B2.9's vector-load representation gave seeds 29 and 43 zero fallbacks and
small/large charged mean ratios below 0.90 on twelve new cases. Both missed
the direction-wise bound because accepted large-y starts required more
refinement updates than uniform at volume 0.5625, with a smaller gap at
0.2625. The impossible own-trajectory oracle retained headroom at the
high-volume case. Pixelwise update-30 design MSE need not prioritize errors
in elements that most affect compliance and the subsequent OC trajectory.
This motivates an independently testable loss hypothesis; it does not prove
the loss is the cause. B2.9 screen outcomes are diagnosis only and cannot
enter B2.10 weight construction, fitting, checkpoint selection, or tuning.
The earlier B2.5 sensitivity-weighted **final-density** objective failed its
own Gate; applying the same bounded weighting rule to B2.9's stronger input
and an intermediate-state target is a distinct hypothesis, not a presumed fix.

Keep the 468 train and 12 selection **physical definitions and B2.6
post-update-30 target artifacts** unchanged. The audited target-index
SHA-256 is
`5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`.
For each stored float32 target design, recompute its filtered physical
density, independently solve compliance at that physical state, back-propagate
the absolute compliance sensitivity through the same density filter to
design density, divide by its within-case mean, clip to `[0.25,4]`, and
renormalize to mean one. This is the existing B2.4 sensitivity-weight
definition, now applied at the intermediate trajectory state. Store all 480
weights, source target references, re-solved compliance, dimensions, case
and split identities, and content hashes outside Git. Audit every target
and weight before fitting. Weight generation has a 7,200 s wall and 2 GiB
peak-RSS cap; no missing source or weight can be dropped.

Keep the 13-channel B2.9 vector input, 12,577-parameter CNN, three seeds
`17,29,43`, CPU AdamW parameters, 59-step shape-bucketed schedule, 200-epoch
cap, 25-epoch patience, strict earliest selection minimum, and all source
case definitions. **Only** replace elementwise trajectory MSE for fitting
and checkpoint selection with the elementwise mean of sensitivity weight
times squared error. No architecture, target-update, data population,
optimizer hyperparameter, seed, or threshold search is allowed. The
unchanged B2.9 control fit-index SHA-256 is
`96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`.
Version new checkpoints and selections as B2.10, keep them outside Git,
and cap all three fits at 7,200 s and 2 GiB peak RSS. There is no query-time
FEM feature or weight construction; all offline generation and fitting costs
are reported separately.

## Fresh exposure boundary and complete screen

Freeze twelve physically disjoint cases before weight generation: volumes
`0.2875,0.4375,0.5875`; directions `y/z`; small `(12,6,3)` and doubled
large `(24,12,6)` meshes; fixed x-min support and one point load at
small-mesh node `(x=max,y=2,z=2)` with its physically matched doubled
large-mesh node. There is one case per scale/direction/volume stratum.
These volumes are absent from the B2.4/M2 catalog, design-exposed M3 v1
catalog, and all B2.6–B2.9 screens. Check exact case IDs against every
development-exposed training, selection, and screen case. No M2 test/OOD
or M3 final label or outcome is opened. Keep all material, geometry, filter,
OC, and 240-update physical-plateau solver settings unchanged.

For each sorted screen case, run eleven methods: fresh uniform, physics
heuristic, B2.4 training-only nearest neighbor, historical B2.5 control
seed 43, the three unchanged B2.9 vector models, the three new B2.10
weighted models, and an impossible own-trajectory oracle. The B2.5 fit
index and control checkpoint SHA-256 values are
`a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53`
and `d82b7895355c1f73cde5b80d6328bc31c43c58cd7b1580974a590ef42bce0f4d`.
The oracle's target generation is separately charged as nondeployable.

Every method receives unchanged filtered-volume projection, full
refinement, independent convergence/compliance re-solve, physical-volume
error `<=0.005`, and final compliance `<=1.001` times matched uniform.
Record a failed candidate as failed and charge its complete attempt plus a
fresh complete uniform fallback. Atomically retain all eleven outcomes per
case, rerunning an interrupted case in full. Report every seed, case,
stratum, phase cost, failure, fallback, quality result, offline cost, and
resource. The screen has a separate 14,400 s wall and 2 GiB peak-RSS cap.

The **B2.10 development feasibility Gate** uses only the three new weighted
models. At least two must have fallback-inclusive arithmetic mean paired
time ratio `<=0.90` at both scales and `<=1.0` in every scale/direction
stratum, with zero accepted quality violations, all 12 cases and 132
outcomes, and all resource caps. A pass remains a small exposed development
result requiring a separately frozen larger confirmation before B3. A
failure preserves every outcome and requires another diagnosed, versioned
intervention. Neither result alone permits a final acceleration or delivery
claim.

Run a read-only plan, then weight generation, fitting, and screening from
one clean committed revision in a single-thread CPU/BLAS environment.
Keep generated weights, models, outcomes, and logs outside Git.
