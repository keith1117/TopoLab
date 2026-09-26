# B2.9 vector-load conditioning and fresh development screen

Status: frozen before B2.9 fitting and screening. This is one
development-only learning-side input correction. The read-only plan version
`topolab.b2_9.vector_load.v1` has canonical SHA-256
`b7703931dfe2eadbe9300506f288787e44b011e003c4e6fef67cd73ee9000138`.
It cannot establish final v2 acceleration.

## Measured motivation and one intervention

B2.8's static y midpoint changed several solver paths but kept the same
2/3/4 failed-attempt counts as the unmodified B2.7 models on its fresh
screen. The z predictions were numerically unchanged and slow on several
new load-position/volume cases, while the true-trajectory oracle retained
conditional headroom. B2.7 encodes a point load as one signed radial-distance
scalar field. That scalar is symmetric around the load node; the two-layer
local CNN must infer directional displacement from it and separate absolute
coordinate channels. This is a testable representation bottleneck, not proof
of the only cause of the B2.8 result. No B2.7/B2.8 screen outcome is used
for B2.9 training, checkpoint selection, or representation tuning.

Change **only load conditioning** for the B2.9 candidate. Preserve the three
support channels, three normalized element-center coordinate channels, and
broadcast target-volume channel. Replace channels 3–5 with a spatially
constant signed one-hot load direction. Append three channels
`(c_x-q_x, c_y-q_y, c_z-q_z)`, where `c` is normalized element-center
position and `q` is the normalized loaded-node position. Each signed
relative coordinate lies in `[-1,1]` and is visible at every element.
The resulting 13-channel tensor retains CPU float32 `(channel,z,y,x)`
storage and x-fast flattening. Reject any case without exactly one valid
point load. Version this input as `topolab.b2_9.vector_load.v1`; historical
M0/M1/M2/B2.7 encoding remains untouched. Charge encoding and inference
to candidate setup.

Use the same two 3-by-3-by-3 convolutions, 16 hidden channels, ReLU,
pointwise sigmoid head, and shape preservation as the B2.7 model. Only the
first convolution's input width changes from 10 to 13, increasing the
fixed parameter count from 11,281 to **12,577**. Version the model as
`topolab.b2_9.vector_cnn.v1`. There is no extra depth, learned physics
feature, query-time FEM solve, output blend, or threshold.

Keep the 480 audited B2.6 post-update-30 design-density targets: 468 training
definitions and 12 checkpoint-selection definitions, with target-index
SHA-256 `5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`.
Keep B2.7's CPU AdamW settings, fixed 59-step shape-bucketed schedule,
elementwise target MSE, seeds `17,29,43`, 200-epoch cap, 25-epoch patience,
and strict earliest validation-MSE minimum for each seed. Re-read all source
target artifacts and checksums before fitting and screening. The existing
B2.7 fit index SHA-256 is
`36158e03a476fdff183d8c72cf0e7143700e7bac3ccc531d7eda485ec390a631`.
All new checkpoints/selections get B2.9 identities and stay outside Git.
The complete three-fit stage has a 7,200 s wall and 2 GiB peak-RSS cap.

## Exposure, screen, and Gate

Freeze **12 new physically disjoint screen cases** before fitting: volumes
`0.2625, 0.4125, 0.5625`; directions `y/z`; small `(12,6,3)` and doubled
large `(24,12,6)` meshes; fixed x-min support and one point load at
small-mesh node `(x=max,y=1,z=2)` with its physically matched doubled
large-mesh node. Each scale/direction/volume stratum occurs once. The volumes
are absent from B2.4/M2 and design-exposed M3 v1 volume catalogs and all
earlier B2.6–B2.8 screens. Check exact case IDs against every development-
exposed fit, selection, and screen case. Keep all material, geometry,
filter, OC, and 240-update physical-plateau solver settings unchanged.
No M2 test/OOD label or outcome and no M3 final label or outcome is opened.

For each sorted case ID, run eleven methods: fresh uniform, physics heuristic,
B2.4 training-only nearest neighbor, historical B2.5 control seed 43, three
unchanged B2.7 conditioned models, the three new B2.9 vector models, and an
impossible own-trajectory oracle. The B2.5 fit index is
`a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53`;
its control-43 checkpoint is
`d82b7895355c1f73cde5b80d6328bc31c43c58cd7b1580974a590ef42bce0f4d`.
The oracle receives the true update-30 state after solving its own screen
case and is nondeployable; report generation separately. The B2.7 models
serve as matched learned controls on the same new cases.

Every method uses unchanged filtered-volume projection, full refinement,
independent convergence and compliance re-solve, physical-volume error
`<=0.005`, and final compliance `<=1.001` times its matched uniform
reference. Retain a failed candidate as failed and charge its entire setup,
projection, refinement, decision, plus a fresh complete uniform fallback.
Preserve all eleven outcomes per case atomically and rerun an interrupted
case in full. Report every case, seed, direction, scale, volume, failure,
fallback, phase time, oracle headroom, source and new fit costs, and resource
use. The screen has a separate 14,400 s wall and 2 GiB peak-RSS cap.

The **B2.9 development feasibility Gate** uses only the three new vector
models. At least two must have fallback-inclusive arithmetic mean paired
time ratio `<=0.90` at both scales and `<=1.0` in every scale/direction
stratum, with zero accepted quality violations, all 12 cases and 132
outcomes, and both resource caps. A pass remains a small exposed development
result requiring a separately frozen larger confirmation before B3.
A failure preserves every outcome and requires another diagnosed, versioned
intervention. Neither outcome alone permits a final acceleration or delivery
claim.

Run a read-only plan first, then fit and screen from a clean committed
revision in a single-thread CPU/BLAS environment. Keep all generated data,
models, outcomes, and logs outside Git. Report B2.6 target-generation cost
separately; no new fitting target is generated here.
