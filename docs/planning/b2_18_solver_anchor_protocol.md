# B2.18 frozen solver-anchored start

Status: frozen before B2.18's solver-anchored outcome. Canonical plan
`topolab.b2_18.solver_anchor.v1` has SHA-256
`df4959622747da50937903480d4de06f94e8d23df409049ff145ca865270f21b`.
This is one direct repair of the B2.17 terminal-quality failure mode,
not another early-score cutoff or metadata threshold search. It is a
development-only mechanism test and cannot open B3 or support an ML
acceleration claim.

## One fixed mechanism

For high-volume, large-grid y-load cases, infer the unchanged audited
B2.12 context-17 density and project it to the existing filtered-volume
target. Independently run exactly **two** uniform SIMP updates on the same
case. Form a 50/50 elementwise blend of the projected learned *design*
density and the two-update uniform *design* density, then project the
blend again to the unchanged volume target. Start a fresh, otherwise
unchanged 360-update physical-plateau solve from this anchored density.
The quality check and `1.001` matched-uniform compliance and `0.005`
volume bounds stay unchanged. Any terminal failure retains its status
and pays a complete fresh uniform fallback. Every inference, projection,
two-update shadow, blend, refinement, quality check, and fallback is
charged. The pre-refinement phases must total **strictly less than
2.8101 seconds** per query; all complete paired time ratios still count.

This differs from B2.8's blend with the *initial constant* density:
the uniform state here has undergone physical FEM/sensitivity/OC
updates before it anchors the learned field. The mechanism tries to
change the eventual solver basin directly, because B2.17's early
compliance signal admitted three terminal failures. The 50/50 weight
and two updates are fixed; no exposed outcome may retune them.

## Ordered evidence and stop rule

Hash-audit the B2.14/B2.15 reference and screen indices and verify the
fixed B2.9/B2.12 checkpoints. First run the intervention on their four
known high-volume large-y context-17 cases: one historically successful
and three historically failed. Keep all four, paired to a new timed
uniform solve. This sentinel passes only if all four anchored candidates
independently pass terminal quality without fallback, their mean fully
charged paired time ratio is `<=1.0`, every pre-refinement cost is
strictly below `2.8101 s`, and the stage uses `<=600 s` and `<2 GiB`.
If it fails, stop before opening any new case. A pass is mechanistic
evidence on exposed cases, not proof of transfer.

Only after that pass, open four physically fresh large-y cases crossing
volumes `0.5675,0.5725` and small-mesh free-end positions `(y=1,z=2)`
and `(y=5,z=1)` doubled onto the `(24,12,6)` large mesh. Their case IDs
and volumes are disjoint from all 636 previously exposed development
cases, the 24 unexecuted B2.17 reservations, and design-exposed M3 v1
volumes. First run four independent uniform references, requiring 4/4
convergence, positive finite compliance, independent final-state quality,
physical-volume error `<=0.005`, `<=900 s`, and `<2 GiB`.

Then run four complete matched screens with ordered methods: new timed
uniform, unchanged fixed context-17, unchanged B2.13 high-volume-y
uniform rejection, and the new anchored start. Retain all 16 outcomes
and full phase charges, within `<=1800 s` and `<2 GiB`. The small
mechanism Gate requires 4/4 accepted anchored candidates, zero
operational quality violations, per-case anchored ratio `<=1.05`, mean
anchored ratio **strictly below 0.95**, mean anchored ratio below both
unchanged context-17 and old routed comparators, and strict per-query
pre-refinement cost compliance. A fresh pass only permits separately
freezing a two-scale/direction-wise B2.19 development screen; it does
not by itself pass B2's full feasibility Gate or open B3.

Run the read-only plan, sentinel, references, and screen from one clean
committed revision with one CPU/BLAS thread. Audit source identities,
reference quality, checkpoint hashes, blended-state construction,
fallbacks, timing sums, ratios, costs, and the ordered Gate independently.
All generated indices, weights, logs, and summaries remain outside Git.
No M2 test/OOD or final evidence is opened. Failure ends this one
solver-anchor intervention without changing its weight, number of
updates, tolerance, model, or cohort; the next slice must investigate
a learning-side quality-basin mechanism.
