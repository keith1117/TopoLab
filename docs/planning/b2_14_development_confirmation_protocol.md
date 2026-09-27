# B2.14 frozen larger development confirmation

Status: frozen before any B2.14 reference or candidate outcome. This is a
development-only confirmation of already audited checkpoints and the B2.13
route, not new fitting or final acceleration evidence. Plan version
`topolab.b2_14.development_confirmation.v1` has canonical SHA-256
`236ceafce97fad8282b32b0c7f5def38954d22b302a761aeb64196197dad3673`.

## Hypothesis and fixed comparison

B2.13's 12-case route passed its own charged time and quality limits, but
fixed B2.12 context seed 43 was faster on both scales. B2.14 tests whether
that small-screen result transfers to a larger, physically disjoint cohort.
The unchanged B2.13 metadata-only route is compared with four unchanged
single-model policies: B2.9 vector seed 29 and B2.12 context seeds 17, 29,
and 43. Fresh uniform, the fixed physics heuristic, and the B2.4 train-only
nearest neighbor are matched non-learned comparators. No checkpoint, route,
rejection boundary, model input, solver, quality tolerance, or fallback rule
may change after this protocol is frozen.

The B2.9 and B2.12 fit-index SHA-256 values are
`96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`
and `0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce`.
The exposed B2.12 and B2.13 screen-index SHA-256 values are
`cb671b2e9b5194606964faed0c6022c4a9a181b978827f906bfe416f72516443`
and `183e3448a9d7e3e82de6ed4dd3f38e5184977b7243aa9edd13284f950f8d3de0`.
Verify source indices, all selected model checkpoints, and selection histories
before screening. Their previous outcomes are diagnosis only.

## New cases and execution boundary

Cross volumes `0.3125, 0.4625, 0.5925`, small-mesh point-load nodes
`(x=max,y=3,z=1)` and `(x=max,y=5,z=2)`, y/z negative unit loads, and
`(12,6,3)`/`(24,12,6)` element meshes with physically doubled load-node
indices. This is exactly **24** cases, two per scale/direction/volume cell.
Use x-min fixed support, the B2.11 360-update physical-plateau comparison
budget, and all existing material/filter/OC settings. The 24 case IDs and
all three volumes are absent from the 588-case development exposure ledger
and the design-exposed M3 v1 final volume definitions. M2 test/OOD and any
new final outcome remain sealed.

Run all 24 fresh uniform references before model loading. Require **24/24**
convergence, finite positive compliance, independent final-state check, and
physical-volume error `<=0.005`. Retain and report any failure, and do not
open the candidate screen if this reference Gate fails. The reference cap is
3,600 s and 2 GiB peak RSS.

The screen runs a new timed uniform per case, then physics heuristic,
nearest neighbor, vector 29, context 17/29/43, and the unchanged B2.13 route
in that order: **192** outcomes. Use one CPU/BLAS thread and one clean,
committed source revision for the read-only plan, references, and screen.
Persist each complete case atomically. Charge setup, inference, projection,
refinement, quality decision, rejection to fresh uniform, and fresh fallback
after every failed attempt. Retain the failed attempt's status. Report route,
all phases, fallbacks, one-time checkpoint/neighbor loading, and peak RSS.
The screen cap is 10,800 s and 2 GiB peak RSS. Generated indices and logs
remain outside Git.

## Confirmation Gate and selection rule

First require all 24 cases and 192 ordered outcomes, zero accepted
compliance/convergence/volume violations, and both resource caps. A candidate
policy is **eligible** only if it has at most two failed learned attempts
(with full fallbacks), a fallback/rejection-inclusive arithmetic mean paired
time ratio `<=0.90` at each scale, and a mean `<=1.0` in each of the four
scale/direction strata. The route's predeclared uniform rejections are not
failed learned attempts, but their complete cost is included.

Among eligible fixed models choose the lowest 24-case overall arithmetic
mean ratio, breaking exact ties in order vector 29, context 17, context 29,
context 43. Select the route only if it is eligible and either no fixed model
is eligible, or its overall mean is **strictly below 0.95 times** that best
fixed model's mean with no more failed attempts. Otherwise select the best
eligible fixed model. The confirmation Gate passes only if a policy is
selected and its overall mean is strictly below the overall means of **both**
non-ML comparators. The selected policy must still meet the scale/direction
and quality criteria above. No seed, case, or comparator may be dropped.

A pass permits planning B3's separate final contract; it does not change
the operational uniform default or establish accelerated performance. A
failure retains every outcome and requires a new bounded development
intervention before B3. An independent audit must recompute exposure,
checksum, quality, time, and selection results from persisted artifacts.
