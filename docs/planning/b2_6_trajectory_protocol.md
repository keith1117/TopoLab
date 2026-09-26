# B2.6 versioned intermediate-trajectory target and new development screen

Status: frozen before target capture, fitting, or screening. B2.6 is one
development-only intervention after B2.5's negative Gate. It cannot establish
the final v2 acceleration claim. The read-only plan version is
`topolab.b2_6.trajectory.v1`, with canonical SHA-256
`e783f4b8e74b08b1855ea62b9c69dcee9fc812e38786561d93c25ef38fa9a8d8`.

## Hypothesis and numerical boundary

B2.5's final-design MSE and sensitivity-weighted target produced 40 learned
failures and accepted-only time ratios above 1.0. Refinement, not inference,
dominated charged cost. This slice changes **only the training target**: train
the same 11,281-parameter shape-preserving CNN to predict the uniform solver's
post-update **design density at update 30**. If the fixed physical-plateau
solver converges before update 30, use its terminal design state and record
the actual update. The callback is invoked after that state's finite-element
re-solve. It terminates target capture without changing solver behavior.
The model still receives only the frozen ten-channel case encoding; no
trajectory, sensitivity, query label, or quality result enters inference.

Keep the B2.3/B2.4 versioned 240-update physical-plateau solver, filter,
projection, OC rule, convergence thresholds, optimized sparse ordering,
independent quality check, and fresh uniform fallback unchanged. A captured
target must be finite CPU float32, within design-density bounds, and have
filtered physical-volume error `<=0.005`. Target generation time is an
offline cost and is reported separately. Predicting the state is a deployable
candidate; using the true state of a screen case is an impossible oracle and
must never count as a learned success.

## Exposure and fitting

Use exactly the 468 B2.4 **training case definitions** and no B2.4 validation,
M2 test/OOD, or M3 v1 final label or outcome. The B2.4 plan/index identities
are `015ab799be88a5fef763720b2e1c58281dc17aea67c61435bcb87d254f64169c`
and `dad9109aca6d4e14a851c266fd1b8a490885cf2565281ee85ceba1d164f59244`.
Generate every new target with the unchanged uniform solver from a clean
committed revision, then checksum-address each external artifact. Preserve
every captured case and actual stopping update. Require all 480 target
artifacts and audits before fitting; no missing case can be dropped.

Create a **new, physically disjoint** 12-case model-selection cohort: volumes
`0.225, 0.375, 0.525`, directions `y/z`, small `(12,6,3)` and large
`(24,12,6)` meshes, one paired load location at small-mesh `x=max, y=2, z=1`.
All problem fields other than the new volume, load node, scale, and 240-update
budget match the development cantilever convention. The large case maps the
same physical point by doubling node indices. These definitions have not
entered the B2.4 or M2 catalogs. Their 12 trajectories are selection targets
only. The separately frozen screen below is not used to select checkpoints,
seeds, epochs, or thresholds.

Fit seeds `17, 29, 43` from independent initializations. Use the unchanged
M1 CNN, AdamW `(lr=1e-3, weight_decay=1e-4, betas=(0.9,0.999), eps=1e-8)`,
CPU float32, batch size at most eight, the B2.5 fixed 59-step shape-bucketed
schedule, no augmentation, and elementwise trajectory-target MSE. Evaluate
all 12 selection cases after each epoch. Choose the strict earliest minimum
of each seed's own validation MSE; stop after 25 unimproved epochs or 200
epochs. No architecture, target-update, hyperparameter, or seed search.
Content-addressed checkpoint and full selection histories stay outside Git.
Target capture has a 7,200 s wall and 2 GiB peak-RSS cap; the complete three
fits have a separate 7,200 s wall and 2 GiB cap.

## Separate fixed screen and decision

Screen 12 additional **new** physical cases at the same three volumes, two
directions, and two mesh scales, but with a distinct small-mesh load at
`x=max, y=4, z=2`. These cases are disjoint from all training and selection
cases and from the M2 catalog. Freeze their IDs before any target capture.
Run in sorted case-ID order. Each case receives eight methods: fresh uniform,
physics heuristic, B2.4 training-only nearest neighbor, the fixed B2.5
control-seed-43 checkpoint, all three new trajectory models, and the
impossible own-trajectory oracle. The B2.5 fit index SHA-256 is
`a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53`;
its control-43 checkpoint SHA-256 is
`d82b7895355c1f73cde5b80d6328bc31c43c58cd7b1580974a590ef42bce0f4d`.
Model and neighbor-index loading and oracle target generation are reported
separately from deployable per-query time. The oracle's per-query time starts
with its supplied exact trajectory density and must be labeled impossible.

Every deployable attempt pays encoding/inference or baseline setup, filtered
volume projection, complete refinement, independent quality decision, and a
fresh complete uniform fallback on rejection or failure. A fallback never
rewrites the failed attempt as accepted. Require convergence, independently
re-solved finite positive compliance within relative `1e-9`, physical-volume
error `<=0.005`, and final compliance `<=1.001` times the matched uniform
reference. Preserve all eight outcomes per case atomically; an interrupted
case reruns in full. The screen has a separate 14,400 s wall and 2 GiB
peak-RSS cap.

B2.6's **development feasibility Gate** passes only if at least two of three
new learned seeds have fallback-inclusive arithmetic mean paired time ratio
`<=0.90` at both scales, `<=1.0` for each direction at each scale, and zero
accepted quality failures. Report every method, seed, case, volume, failure,
fallback, phase cost, oracle headroom, total generation/training/loading cost,
and resource cap. A passing 12-case screen remains a small exposed
development result and requires a separate, larger confirmation before B3.
If it fails, preserve every outcome and select the next versioned hypothesis
from the measured mechanism. Do not tune on these 12 screen outcomes, open
final evidence, or claim learned acceleration.
