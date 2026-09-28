# B2.20 frozen operational checkpoint selection

Status: frozen before B2.20 reference, fitting, selection, or screen
outcomes. The canonical `topolab.b2_20.operational_selection.v1` plan
SHA-256 is
`2b72bcdcfd92c32908af73ee329550d8f364dcbb8a740c197858b72deb30f192`.
This is development-only evidence. No positive outcome here alone opens B3.

## Single intervention

B2.19 lowered validation density MSE for all three seeds without improving
the complete quality and time Gate. Test whether **selecting a different
training checkpoint by operational evidence**, rather than the lowest
density MSE, repairs that mismatch. Use the unchanged B2.12 13-channel
vector input, 26,433-parameter context CNN, 468/12 training/MSE-validation
cases, 480 audited B2.6 update-30 targets, unweighted MSE, AdamW,
shape-bucketed batches, seeds `17,29,43`, 200-epoch maximum and
25-epoch patience. Copy weights after epochs `80,120,160` if reached,
and retain the earliest strict MSE-minimum checkpoint. Capturing makes
no optimizer, RNG, loss, target, architecture, or solver change. Verify
the latter checkpoint's tensors exactly match published B2.12 controls.
Their known MSE-best epochs are `160,141,160`, yielding fixed candidate
sets `17:{80,120,160}`, `29:{80,120,141,160}`,
`43:{80,120,160}`. Stop if a fit differs. Audit the B2.6 target index
SHA-256
`5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`
and fixed B2.12 fit-index SHA-256
`0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce`.
Complete all three fits in `<=7200 s`, below `2 GiB` peak RSS.

## Selection and screen boundaries

The B2.19 screen-index SHA-256 is
`2a5accb40612b0e0a4dd349ae82cf76ed648481320e03aa8c66bbd9dc8ab331b`.
Include its twelve exposed cases and all prior exposed and unopened
reservations in the blocked ledger: 676 case identities. Exclude its
volumes, the prior development volumes, M2 catalog volumes, and
design-exposed M3 v1 volumes.

Freeze twelve **selection** cases at volumes `0.3475,0.4975,0.5835`,
point-load directions `y,z`, small and large meshes, and small-grid
x-max position `(y=2,z=2)` with physical doubling on the large mesh.
These cases are separate from the 468/12 fit and MSE-validation cases.
First run all twelve independent uniform references; require 12/12
convergence, positive finite compliance, independent final-state
quality, physical-volume error `<=0.005`, `<=1800 s`, and `<2 GiB`.
Stop before fitting if any reference fails. On each selected case,
evaluate fresh projections and complete 360-update refinements for
all ten candidate checkpoints, plus the saved matched uniform reference:
132 outcomes. Charge every setup, projection, refinement, quality
decision, and complete fresh uniform fallback. Retain failed candidate
status after fallback. Complete in `<=10000 s` and `<2 GiB`.

For each seed independently, rank its checkpoints lexicographically:
(1) fewest failed terminal quality checks, (2) lowest maximum of the
four mesh-scale/direction arithmetic mean paired ratios, (3) lowest
overall arithmetic mean paired ratio, (4) earliest epoch. Every ratio
includes fallback charges and uses the corresponding saved uniform
reference time. Freeze the selected checkpoint hashes in an audited
decision artifact before opening the screen cases. No threshold or
weight may be retuned from selection outcomes.

Freeze a distinct **screen** of 24 cases at volumes
`0.3525,0.5025,0.5865`, directions `y,z`, both mesh scales, and two
small-grid x-max positions `(y=1,z=1)` and `(y=5,z=2)` with doubled
large-grid positions. First require 24/24 independent uniform references
with the same quality checks, within `<=3600 s` and `<2 GiB`.
Retain seven methods per case, in order: matched uniform, all three
unchanged B2.12 MSE-selected controls, and the three B2.20
operationally selected checkpoints. This yields 168 complete outcomes
within `<=16000 s` and `<2 GiB`. Every learned attempt uses unchanged
filtered-volume projection, full 360-update SIMP, convergence,
compliance `<=1.001` times matched uniform, volume error `<=0.005`,
and fully charged fallback on failure.

The new development Gate requires complete references, fits, selection,
and screen, zero accepted quality violations, and all resource caps.
At least two selected seeds must each attain fully charged arithmetic
mean ratios `<=0.90` on **both** scales and `<=1.0` in each of the four
scale/direction strata, with no more terminal failures than their paired
B2.12 control seed. At least four of six selected attempts on the two
high-volume large-y cases must pass terminal quality. Report the
unchanged control and all seeds even if the Gate fails. A pass only
permits a separately frozen larger development confirmation before B3.

Run a read-only plan and every stage from one clean committed revision,
with one CPU/BLAS thread. Checkpoint, reference, fit, selection, screen,
log, and audit artifacts stay outside Git. Do not open M2 held-out or
final evidence. Failure ends this exact checkpoint-selection method
without adding epochs, trying another ranking, moving volume cutoffs,
or relaxing quality or speed limits on exposed results.
