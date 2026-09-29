# B2.24 frozen expanded-position specialist intervention

Status: frozen before any new B2.24 reference, fit, diagnostic, or screen
outcome. Canonical `topolab.b2_24.expanded_position_training.v1` plan
SHA-256:
`50230a66db17c26ed4665bce41142c61b3e5ffc5f2dcfb83988d77d84884dd94`.
This is development evidence only. A pass requires a separately frozen
larger development confirmation before B3 or any acceleration claim.

## One training-data intervention

B2.23 passed 30/30 new audited large-mesh y label checks. Bind its label
index SHA-256
`ca1060430f11dc6e3aec497b3297a33191686e9d410c5202bec4d65278cae850`.
Add its 20 train labels at volumes `0.5585` and `0.5985` to B2.22's
unchanged 468 B2.4 terminal-design training labels, for exactly 488
training cases. The high-volume y case-weight-8 set grows from 52 to 72,
including 24 large-mesh cases; every other case remains weight 1. Keep
the B2.12 26,433-parameter context CNN, B2.9 thirteen-channel input,
terminal **design** target, AdamW, seeds `17,29,43`, shape-bucketed batch
size 8, 200-epoch maximum, and 25-epoch patience. The fixed population
has 61 batches per epoch. The opt-in count parameters leave earlier fits'
468 cases and 59 batches unchanged.

Keep B2.22's checkpoint rule: earliest strict minimum unweighted MSE on
its two y-direction volume-`0.525` validation cases, one per scale, within
the unchanged twelve B2.21 validation targets. B2.23's ten validation
labels at volume `0.5785` are independently read and audited, then used
only for fixed-checkpoint MSE diagnosis against matched B2.22 specialists;
they do not choose epochs, weights, a route, or a screen decision. Bind
B2.22 fit-index SHA-256
`a7a0f598bff793e860b8d561976f3be4b38a00fca7864bfb86854c56acfb5dde`
and B2.21 validation-target-index SHA-256
`3e7add2c85650bcb5ac0329236678887baaf2fc3acd4882a1f8f8fc7070796ab`.
Verify every opened label and checkpoint byte and case identity before use.

At query time retain B2.22's route exactly: new or old specialist only
for `(24,12,6)` y cases at volume `>=0.55`; otherwise use the matched
unchanged B2.12 context checkpoint. Fully charge route, encoding,
inference, filtered-volume projection, 360-update physical-plateau SIMP
refinement, terminal quality decision, and complete fresh uniform
fallback on failure. A failed learned attempt remains failed after
fallback. The B2.22 specialist is the matched fixed control.

## Fresh cases and ordered Gates

Bind B2.22 screen-index SHA-256
`62ffe463c863f5ff57b88687a5cc9aeb0abf5261087335f4e790e5f3b3f58632`.
Block all 790 prior exposed or reserved physical case IDs, including all
30 B2.23 labels. Exclude prior development, M2 catalog, and design-exposed
M3 v1 volumes. Freeze 24 new 360-update cases at previously unused volumes
`0.3665,0.5165,0.5965`, small-grid x-max positions `(y=2,z=1)` and
`(y=4,z=2)` (doubled on the large mesh), y/z directions, and meshes
`(12,6,3)` and `(24,12,6)`. Each scale/direction stratum has six cases;
exactly two high-volume large-y cases invoke a specialist. These cases
are physically disjoint from all training, validation, earlier
development, and reserved final evidence.

1. Obtain 24/24 independently quality-checked uniform references within
   `<=3600 s` and `<=2 GiB`. A failed reference stops before fitting.
2. Fit all three fixed seeds within `<=7200 s` and `<=2 GiB`; retain
   selected epochs, histories, checkpoint hashes, and ten-case diagnostic
   MSE values for both old and new models outside Git.
3. Screen seven methods per case: matched uniform, three unchanged
   B2.22 routed specialists, and three new expanded-label routed
   specialists. Retain all 168 fully charged outcomes within `<=16000 s`
   and `<=2 GiB`.

An accepted learned attempt must converge, have independently checked
compliance `<=1.001` times matched uniform, and physical-volume error
`<=0.005`. Accepted quality violations must be zero. The development
Gate requires at least two expanded seeds with arithmetic paired mean
time ratios `<=0.90` on both scales and `<=1.0` on each of four
scale/direction strata. Each such seed must have no more failed attempts
than its matched B2.22 control. Across the two high-volume large-y cases,
at least four of six expanded attempts must pass terminal quality and
their success count must exceed the old specialists' count by at least
one. Report all seeds, controls, failures, phase costs, and diagnostics
even if the Gate fails. Do not tune on the new screen.

Run a read-only plan and each stage from one clean committed revision
with one CPU/BLAS thread. Generated references, labels, checkpoints,
histories, outcomes, logs, and separate audit code stay outside Git.
M2 held-out/OOD and new final evidence remain sealed. A failed Gate ends
this exact intervention and leaves uniform initialization as the
operational default.
