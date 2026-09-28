# B2.22 frozen high-volume y specialist

Status: frozen before any new B2.22 reference, fit, or screen outcome.
Canonical `topolab.b2_22.y_specialist.v1` plan SHA-256:
`5c5a2c87ac6dae22ac48a058de6bbf04a4f9632bc2df17a8debc9a06de0a1c2a`.
This is development evidence only; a pass requires a separately frozen larger
development confirmation before B3.

## Measured bottleneck and one bounded intervention

B2.21's terminal-target context CNN retained 0/6 successful attempts on two
high-volume large-y cases. The training population contains only four large-y
cases at volume `>=0.55`, alongside 48 small-y cases in that volume range.
Fit three new 26,433-parameter context CNNs from scratch on the same 468
hash-audited B2.4 terminal design labels and thirteen-channel B2.9 inputs.
Keep AdamW, three seeds `17,29,43`, 200-epoch maximum, 25-epoch patience,
shape-bucketed batches, and all solver and projection rules fixed. Change only
the case-level training objective: give the 52 high-volume y cases weight `8`,
all other cases weight `1`, and normalize by the sum of case weights in each
batch. Select the earliest strict minimum **unweighted MSE** on the two
B2.21 validation terminal targets that are y-directed at volume `0.525`, one
per mesh scale. The other ten validation targets remain sealed from checkpoint
selection. Reuse the complete B2.21 validation-target index with SHA-256
`3e7add2c85650bcb5ac0329236678887baaf2fc3acd4882a1f8f8fc7070796ab`;
verify every source label and target byte and case identity before fitting.

At query time the fixed route uses the new specialist **only** for mesh
`(24,12,6)`, y direction, and volume fraction `>=0.55`. The other cases use
the matched B2.12 context checkpoint for the same seed. Charge the metadata
route decision, input encoding, inference, filtered-volume projection, full
360-update SIMP refinement, terminal quality decision, and a complete fresh
uniform fallback for every failure. Retain failure status after fallback.
No routing threshold, weight, epoch, target mixture, or acceptance rule may be
adjusted using the B2.22 screen.

## Disjoint screen and stage gates

Bind B2.21's screen index SHA-256
`a44145fb61c7a3eb372fca02aaaef691b35f4b22630c9d50623eeb377d844d6d`.
The blocked ledger contains 736 prior exposed or reserved physical cases.
Exclude prior development, M2 catalog, and design-exposed M3 v1 volumes.
Freeze 24 new 360-update cases at volumes `0.3645,0.5145,0.5945`, y/z
point-load directions, small `(12,6,3)` and large `(24,12,6)` meshes, and
small-grid x-max positions `(y=1,z=2)` and `(y=4,z=1)` doubled on the large
mesh. Exactly two screen cases use the specialist route. The 24 new cases
are disjoint from train, validation, all prior development and final evidence.

1. Obtain 24/24 independently quality-checked uniform references within
   `<=3600 s` and `<2 GiB`. Stop before fitting if any reference fails.
2. Fit all three seeds within `<=7200 s` and `<2 GiB`. Retain histories,
   selected epochs, checkpoints, byte checksums, and source binding outside Git.
3. Screen seven methods per case: matched uniform, three unchanged B2.12
   context controls, and three routed new specialists. Retain all 168
   fallback-inclusive outcomes within `<=16000 s` and `<2 GiB`.

An accepted learned attempt must converge, have independently checked
compliance `<=1.001` times matched uniform, and physical-volume error
`<=0.005`. Accepted quality violations must be zero. The development Gate
requires at least two routed seeds with arithmetic paired mean time ratios
`<=0.90` on both scales and `<=1.0` on each of four scale/direction strata;
each routed seed must have no more failures than its matched context control.
At least four of six routed attempts on the two high-volume large-y cases
must pass terminal quality. Report all seeds and controls even if the Gate
fails. A pass permits only a larger independent development confirmation.

Run a read-only plan and all stages from one clean committed source revision
with one CPU/BLAS thread. Generated references, weights, histories, outcomes,
logs, and independent audit artifacts stay outside Git. M2 held-out/OOD and
new final evidence remain sealed. A failed Gate ends this exact specialist
intervention and leaves uniform initialization as the operational default.
