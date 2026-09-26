# B2.7 globally visible load representation and fresh development screen

Status: frozen before B2.7 fitting and screening. This is one development-only
representation intervention. The read-only plan version is
`topolab.b2_7.global_load.v1`, canonical SHA-256
`1311405f25e20cc7214cc744bb8843bfa791af1232351c71a4c2c639af369e9d`.
It cannot establish a final v2 acceleration claim.

## Measured motivation and one intervention

B2.6's three trajectory-MSE models had 18 charged failed attempts and remained
slower even on many accepted cases, especially in the `y` direction. The
historical ten-channel case encoding places a point load only on incident
elements. The unchanged CNN has two 3-by-3-by-3 convolutions before its
pointwise head, so load information has at most a two-element spatial radius
at each output. Most voxels cannot directly receive it. This is a concrete
representation limitation, not proof that it alone caused B2.6's failure.

Change **only the three load-input channels** for the B2.7 candidate. For one
point load at normalized node position `q` and each element center at
normalized position `c`, set
`g(c,q) = 1 - sqrt(sum_axis((c_axis - q_axis)^2) / 3)`.
Put `sign(load magnitude) * g(c,q)` in the selected load-direction channel;
set the other two load channels to zero. Keep all three support channels,
three normalized coordinate channels, and the broadcast volume channel
exactly as before. The shape remains `(10,nz,ny,nx)`, CPU float32, with x-fast
flattening. The normalized, finite field is available to every element and
communicates direction and location without any per-query FEM solve. Reject
cases without exactly one valid point load. Version this opt-in encoding as
`topolab.b2_7.global_load_distance.v1`; do not alter the historical M0/M1/M2
case encoding or prior checkpoint interpretation. Charge encoding and
inference to candidate setup time.

Keep the B2.6 post-update-30 design-density target, all 480 audited B2.6
train/selection target artifacts, the 11,281-parameter CNN, seeds `17,29,43`,
AdamW settings, 59-step shape-bucketed batch schedule, at most 200 epochs,
patience 25, strict earliest minimum of each seed's own selection MSE,
projection, solver, 240-update physical-plateau policy, independent quality
checks, and full fresh uniform fallback unchanged. No architecture, target
update, optimization hyperparameter, seed, or checkpoint-threshold search.
The B2.6 target-index SHA-256 is
`5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`.
The B2.6 fixed-fit index SHA-256 is
`9ed71fa5929b12cd731a77a0a17a32d81b1cc933f9accd6e501222f018d1e062`.
Re-read all B2.6 target and model checksums and identities before fitting or
screening. All new checkpoints and selections use B2.7 identities and remain
outside Git.

## Exposure, screen, and decision

The 468 B2.4-derived training definitions and 12 B2.6 selection definitions
are unchanged. B2.6's twelve previous screen outcomes may motivate this
single intervention but cannot select B2.7 checkpoints, tune its formula, or
enter training. No M2 test/OOD label or outcome and no M3 final label or
outcome is opened.

Freeze **12 new, disjoint physical screen cases** before fitting: volume
fractions `0.2375, 0.3875, 0.5375`; directions `y/z`; small mesh `(12,6,3)`
and doubled large mesh `(24,12,6)`; fixed x-min support; one point load at
small-mesh node `(x=max,y=5,z=2)` and the corresponding doubled large node.
Material, geometry, filter, OC, and optimization limits match B2.6. These
volumes are absent from B2.4/M2, B2.6 selection/screen, and the design-exposed
M3 v1 final volume catalog. Check complete physical IDs against B2.6's prior
cohorts and retain all scale/direction/volume strata. The screen is never
used to select a seed or edit the representation.

For each case in sorted ID order, run exactly eleven methods: fresh uniform,
physics heuristic, B2.4 training-only nearest neighbor, historical B2.5
control seed 43, all three B2.6 trajectory models, the three B2.7 conditioned
models, and an impossible own-trajectory oracle. The B2.5 fit-index SHA-256
is `a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53`;
its control-43 checkpoint SHA-256 is
`d82b7895355c1f73cde5b80d6328bc31c43c58cd7b1580974a590ef42bce0f4d`.
The exact oracle receives the true target of its own screen case and is
nondeployable. Report its generation cost separately.

Every method uses the same projected 240-update physical-plateau solver.
Require convergence, independently re-solved finite positive compliance
within relative `1e-9`, physical-volume error `<=0.005`, and final compliance
`<=1.001` times the matched uniform reference. Report and charge encoding,
inference/baseline setup, projection, complete refinement, independent
decision, and a fresh full uniform fallback after every rejected or failed
attempt. Preserve failure status; an interrupted case reruns all methods and
writes one complete atomic row. Report all cases, seeds, strata, failures,
phase times, oracle headroom, and one-time artifact/loading costs.

The **development feasibility Gate** uses only the three *new* B2.7 seeds.
It passes if at least two have fallback-inclusive arithmetic mean paired time
ratio `<=0.90` on both mesh scales, each scale/direction mean `<=1.0`, zero
accepted quality violations, all 12 cases and 132 method outcomes, and the
resource caps below. A positive result remains an exposed small development
screen requiring a separately frozen larger confirmation before B3. A failed
Gate preserves all outcomes and prompts another evidence-based, versioned
intervention. No learned acceleration or v2 delivery claim follows here.

The complete three-fit stage has a 7,200 s wall and 2 GiB peak-RSS cap. The
complete screen has a separate 14,400 s wall and 2 GiB peak-RSS cap. The
existing B2.6 target-generation cost is carried forward and reported
separately, with no new target-generation stage. Execute from a clean,
committed revision with a read-only plan, fixed external artifact roots,
single-thread CPU/BLAS settings, and checksum-addressed results.
