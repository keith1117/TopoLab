# B2.23 frozen large-y position coverage and label feasibility

Status: frozen before any new B2.23 solver or label outcome. Canonical
`topolab.b2_23.position_labels.v1` plan SHA-256:
`d7ca55687e1f92fdd113991228f95e589242df8ba2ab112fe0c2153b36595a72`.
This is development-only **data feasibility**. No model fit, new checkpoint,
learned screen, final case, or acceleration claim belongs to this slice.

## Exposure-bound diagnosis

Bind B2.22's complete screen-index SHA-256
`62ffe463c863f5ff57b88687a5cc9aeb0abf5261087335f4e790e5f3b3f58632`.
The existing B2.4/B2.21 large-mesh y training subset at volume `>=0.55`
contains four cases and four load positions in `(ny=12,nz=6)` node
coordinates: `(0,0)`, `(8,0)`, `(2,4)`, and `(12,6)`. The B2.22 high-y
case at `(8,2)` failed for all three specialists; the one at `(2,4)`
passed for all three. `(8,2)` is absent from the four old high-volume
large-y training positions while `(2,4)` is present. This is an observed
coverage association, not a causal diagnosis or a reason to relabel the
exposed B2.22 screen as training data.

## Fixed 30-label expansion and Gate

Block all 760 earlier exposed or reserved physical case IDs and the prior
development and design-exposed final volumes. Freeze three unused high
volume fractions `0.5585,0.5785,0.5985`. At each volume, use the complete
ten-position interior small-grid pattern `y=1..5` and `z=1..2`, physically
doubled to large-mesh x-max point-load nodes on `(24,12,6)`. All cases
have negative y load, the unchanged material/support/filter/SIMP settings,
and the B2.3/B2.4 **240-update physical-plateau** label solver. Give each
new 240-update case its own identity and a linked 120-update source identity.

The 20 cases at `0.5585` and `0.5985` are future **train** labels; all ten
cases at `0.5785` are future **validation** labels. No iteration of one case
crosses the split. The future training-position union would expand from
four to thirteen distinct large-mesh high-y positions, including `(8,2)`;
the new validation volume remains physically disjoint. The plan freezes
case IDs, split, volume, position, source/result mapping, and exposure hash.

Materialize all 30 cases in fixed case-ID order with recoverable atomic
checkpoints. Reuse the audited B2.4 terminal-label artifact schema, CPU
float32 design/physical densities, and independent compliance, volume,
convergence, and sensitivity checks. Bind every artifact to the clean
source revision, runtime, case ID, split, and exact-byte SHA-256. Preserve
every nonconvergent case as a failure row rather than dropping it. Require
30/30 successful, independently audited labels: 20 train and 10 validation;
physical-volume error `<=0.005`, positive finite compliance, valid
240-update terminal stop, elapsed materialization `<=3600 s`, and peak RSS
`<1 GiB`. A failed case or resource cap fails this exact data Gate.

Run a read-only plan and then label generation and audit from one clean
committed revision with one CPU/BLAS thread. Persist labels, index, logs,
and any separate audit artifacts outside Git. M2 held-out/OOD and new
final evidence remain sealed. A pass permits **B2.24** to freeze one
training intervention and fresh independent screen; it does not permit
B3 or an acceleration claim. A failure requires a new versioned data
diagnosis before fitting.
