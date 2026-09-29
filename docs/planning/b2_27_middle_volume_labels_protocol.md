# B2.27 frozen middle-volume y/z position labels

Status: frozen before any B2.27 solver or label outcome. Canonical
`topolab.b2_27.middle_volume_labels.v1` plan SHA-256:
`29dbfd3ba1c16667c1ba241cc9ad6586bfc26b99a34df882c170fce51fcf00d0`.
This is development-only data feasibility. No model fit, learned screen,
final case, or acceleration claim belongs to this slice.

## Exposure and position coverage

Bind B2.26's complete screen-index SHA-256
`05fa1f1e825060b144db0cbab728dfe98e3785594fce42ff7aad85e26813307a`.
The existing 468-case training population has only four large-grid y and
four large-grid z cases at volumes `0.5` and `0.55`, each direction using
four positions. B2.26's fresh learned failures all occurred at volume
`0.5225` in y; large-z refinement varied by seed. This is an observed
coverage and cost gap, not a causal finding.

## Fixed cases and data Gate

Block all 838 earlier exposed or reserved physical case IDs, plus the
prior development and design-exposed final volume grids. Freeze three
unused middle volume fractions `0.5175,0.5275,0.5425`. At each volume
and each negative point-load direction y/z, use the complete ten-position
interior small-grid pattern `y=1..5, z=1..2`, physically doubled to the
large `(24,12,6)` mesh's x-max nodes. The 40 cases at `0.5175` and
`0.5425` are future **train** labels; the 20 at `0.5275` are future
**validation** labels. Each direction has 20 train and ten validation
cases. All 60 cases are physically disjoint from the blocked population
and from one another. Case IDs, source/result mapping, position, split,
and exposure hash are fixed in the canonical plan.

Use the unchanged B2.3/B2.4 **240-update physical-plateau** uniform
label solver, convergence tolerance, independent stored-state compliance
check, physical-volume error `<=0.005`, and B2.4 CPU float32
terminal-design/physical-density artifact schema. Each result has a new
B2.27 identity linked to its 120-update source case. Preserve a failed
or nonconvergent case as a failure row; never remove it to improve the
Gate. Generate in fixed case-ID order with atomic recoverable checkpoints
and verify every label's context and exact-byte SHA-256 on read.

Require **60/60** independently audited labels with the exact 40/20
train/validation and 20/10 per-direction counts, positive finite
compliance, a valid converged stop within 240 updates, and the unchanged
volume limit. Total materialization must take `<=3600 s` and peak RSS
must be `<1 GiB`. Any failed case or resource cap fails this exact
data Gate.

Run a read-only plan and then generation and audit from one clean
committed revision with one CPU/BLAS thread. Persist labels, index,
logs, and independent audit code outside Git. M2 held-out/OOD and final
evidence remain sealed. Passing permits a separately frozen B2.28
training intervention and fresh development screen. It does not permit
B3 or an acceleration claim; a failed data Gate requires a versioned
diagnosis before fitting.
