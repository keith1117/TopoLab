# B2.12 bounded spatial-context CNN and fresh development screen

Status: frozen before B2.12 fitting or numerical screening. This is one
development-only **model-architecture** intervention. The plan version is
`topolab.b2_12.context_cnn.v1`; its canonical SHA-256 is
`968d503bbdf30d3831e525a359a45315a620a114ac54ec61823b3df2ff7a8f97`.
It cannot establish final v2 acceleration.

## Measured hypothesis and single change

B2.11 repaired reference feasibility, but every unchanged B2.9/B2.10 seed
failed the fixed learned Gate. At large `y/0.5975`, all six learned starts
reached final compliance 0.55%–0.63% above uniform and paid full fallback.
At small `z/0.2975`, all six passed quality but took 83–102 updates versus
uniform's 44. The exact own-trajectory oracle retained conditional headroom
at both cases. These observations do not prove a model-capacity cause, but
the two local 3³ convolutions in B2.9 can directly combine only a 5³
neighborhood. Test whether broader, axis-aware context improves prediction
of the same reachable update-30 trajectory state.

Keep B2.9's 13-channel signed-direction/relative-position input, 468/12
train/selection case definitions, all 480 checksum-audited B2.6 targets,
unweighted elementwise trajectory MSE, seeds `17,29,43`, 59-step
shape-bucketed CPU AdamW schedule, 200-epoch cap, 25-epoch patience, and
strict earliest validation-MSE selection. Change only the CNN: retain 16
hidden channels, ReLU, a one-channel sigmoid head, and shape preservation,
but use four 3³ convolutions with `(z,y,x)` dilations `(1,1,1)`,
`(1,1,2)`, `(1,2,4)`, `(1,2,8)` and matching padding. This gives a
31-wide x and 13-wide y receptive field in the interior, while keeping
z context bounded. The model has 26,433 trainable
parameters. This is a fixed architecture, with no layer/width/dilation
search, loss change, new label, physics feature, query-time FEM feature,
blend, or learned threshold. New checkpoints and selections have B2.12
identities; all historical B2.9/B2.10 artifacts remain immutable.

The B2.6 target index SHA-256 is
`5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`.
The unchanged B2.9 control fit-index SHA-256 is
`96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`.
Verify the target and all three control selections/checkpoints before
fitting or screening. Complete three fits within 7,200 s and 2 GiB peak
RSS. Report previous target generation and both fit costs separately.

## Fresh reference feasibility and exposure boundary

Freeze twelve physically disjoint development cases before fitting:
volumes `0.3025,0.4525,0.6025`, `y/z` point-load directions, small
`(12,6,3)` and large `(24,12,6)` meshes, fixed x-min support, and one
small-mesh point load at `(x=max,y=4,z=1)` with a physically matched doubled
large-mesh node. Cross all scale/direction/volume strata once. Use the
B2.11 opt-in 360-update per-case budget for **every** compared method,
with the unchanged `topolab.simp.physical_plateau.v1` solver, OC, filter,
stiffness, and independent quality limits. The volumes and exact case IDs
must be absent from all prior fitting/selection/development screens, the
M2 catalog, and design-exposed M3 v1 definitions. No M2 test/OOD or new
final label/outcome may be opened.

Before loading or fitting a model, run and retain all twelve uniform
references. Require 12/12 to converge with finite positive compliance,
independent final-state quality, and physical-volume error `<=0.005`.
Retain any failed reference and stop the B2.12 Gate without learned
screening. The reference stage cap is 1,800 s and 2 GiB peak RSS. The
screen later runs a fresh uniform per case for paired timing; preflight
time is not its denominator.

## Complete screen and decision

After reference and fit Gates pass, run eleven methods on each new case:
fresh uniform, physics heuristic, B2.4 training-only nearest neighbor,
B2.5 MSE control seed 43, all three unchanged B2.9 vector-load seeds,
all three new B2.12 context-CNN seeds, and an impossible exact
own-trajectory oracle. The B2.5 fit-index and control-43 checkpoint
SHA-256 values are
`a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53`
and `d82b7895355c1f73cde5b80d6328bc31c43c58cd7b1580974a590ef42bce0f4d`.
Do not tune the B2.12 model using B2.11 or screen outcomes.

All methods use unchanged filtered-volume projection, full SIMP refinement,
independent convergence/compliance re-solve, volume error `<=0.005`, and
final compliance `<=1.001` times matched uniform. A rejected candidate
remains failed and pays its entire attempt plus a fresh complete uniform
fallback. Retain all twelve cases and 132 outcomes atomically, rerunning
an interrupted case in full. Report every seed, stratum, numerical result,
failure, phase cost, fallback, oracle generation cost, and resource use.
The complete screen cap is 14,400 s and 2 GiB peak RSS.

The **B2.12 development feasibility Gate** requires complete references,
fits, cases, and 132 outcomes, zero accepted quality violations, and every
resource cap. At least two of three new B2.12 seeds must each have a
fallback-inclusive arithmetic mean paired time ratio `<=0.90` at both
mesh scales and `<=1.0` in every scale/direction stratum. Report B2.9
controls on the same cases but do not combine their seeds with B2.12.
A pass still requires a separately frozen larger development confirmation
before B3. A failure retains all evidence and requires a newly diagnosed,
finite intervention. Neither outcome is final acceleration evidence.

Run a read-only plan, then references, fitting, and screening from one
clean committed revision in a single-thread CPU/BLAS environment. Keep
generated references, checkpoints, selections, indices, and logs outside Git.
