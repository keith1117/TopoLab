# B2.15 position-aware routing development screen

Date: 2026-09-27 (America/New_York)

Status: **The frozen B2.15 development Gate failed.** All 24 fresh uniform
references passed, and all 192 fixed-method screen outcomes were retained
and independently audited. The new route improved the small-y mean over the
old route, but its large-y charged mean exceeded 1.0 and its overall gain
over the old route was less than the frozen 5% requirement. Uniform
initialization remains the operational default. B3 and final evidence
remain closed.

## Frozen boundary and execution

The [B2.15 protocol](../planning/b2_15_position_routing_protocol.md) fixed
one metadata-only position/volume route, 24 physically disjoint cases,
method order, resources, and Gate before any new outcome. Its canonical
plan SHA-256 was
`edeab8ca4cc1f059984ebbe84917991e9aef76fffd8ac47e226cbd8965c3b8b8`;
the saved plan-file SHA-256 was
`6eaf4fbba831e8058fd0a683ab5ac4443b1710df4feeaac21e5072934cb7bbb5`.
The clean source revision was `c70a0d92d26bda3df1da0168c135404493df8c3b`.
The fixed B2.9/B2.12 fit indices and B2.12/B2.13/B2.14 exposed screen
indices matched their frozen hashes. All selected checkpoint bytes and
earliest validation-minimum selections were verified before screening.

The new cohort crossed volumes `0.3175, 0.4675, 0.5825`, small-mesh free-end
load positions A=`(x=max,y=2,z=1)` and B=`(x=max,y=4,z=2)` with physically
doubled large-mesh nodes, y/z directions, and `(12,6,3)`/`(24,12,6)` meshes.
Exactly two cases occupied every scale/direction/volume cell. The 24 case
IDs and all three volumes were absent from the 612-case prior development
ledger and design-exposed M3 v1 final volumes. M2 test/OOD and new final
outcomes remained sealed. No fitting, solver, tolerance, checkpoint, or
policy change followed the freeze.

The locked Python 3.12.10 environment ran on Apple arm64/macOS with one
PyTorch CPU thread and one BLAS/OMP thread. The `uv.lock` SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.

## Complete results and Gate

All **24/24** separately run uniform references converged, had finite
positive compliance, passed independent final-state checks, and had
physical-volume error `<=0.005`. Reference execution took **271.14 s**
versus a 3,600 s cap and peaked at **309,231,616 bytes** versus 2 GiB.
Its index SHA-256 was
`1e21d3f2a4ac21522c76911a12640ba551bf4f7939b72121c19fdb6b1146f998`.
The screen reran a fresh uniform per case as the paired timing denominator.

All **192/192** ordered outcomes were retained: fresh uniform, physics
heuristic, B2.4 train-only nearest neighbor, vector 29, context 17,
context 43, old B2.13 route, and new B2.15 route. The table uses arithmetic
means of fully charged *per-case* time ratios, including rejection and
fresh fallback work. All operational results met the `0.005` physical-volume
and `1.001` matched-uniform compliance bounds: **zero accepted quality
violations**.

| Method | Small | Large | Small y | Small z | Large y | Large z | Failed attempts |
|---|---:|---:|---:|---:|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 |
| Physics heuristic | 1.332 | 1.020 | 1.367 | 1.298 | 0.967 | 1.072 | 2 |
| Nearest neighbor | 0.418 | 2.692 | 0.342 | 0.495 | 3.475 | 1.909 | 7 |
| Vector 29 | 0.753 | 0.872 | 0.848 | 0.657 | 1.198 | 0.546 | 3 |
| Context 17 | 0.446 | 1.203 | 0.479 | 0.414 | 1.219 | 1.187 | 3 |
| Context 43 | 0.543 | 1.123 | 0.589 | 0.497 | 1.209 | 1.036 | 2 |
| **Old B2.13 route** | **0.636** | **0.737** | **0.848** | **0.424** | **0.932** | **0.542** | **1** |
| **New B2.15 route** | **0.535** | **0.787** | **0.598** | **0.473** | **1.006428** | **0.568** | **1** |

The new route met the two scale means (`0.535`, `0.787`), its two-failure
allowance (one failed attempt), the small-y/small-z/large-z direction
bounds, and both non-ML overall comparisons. It **missed** the large-y
direction bound (`1.006428 > 1.0`). Its overall arithmetic mean was
`0.661286` versus the old route's `0.686491`, a **3.67%** improvement;
the strict 5% requirement would need a mean below `0.652167`. Neither
new route condition may be relaxed after seeing results. The old route
was the only eligible policy on this cohort. Its local eligibility does
not erase its failed B2.14 confirmation or establish a deployable ML
acceleration claim. All three fixed checkpoint policies failed at least
one scale/direction or failure-count criterion.

The screen took **2,476.63 s** against its 10,800 s cap and peaked at
**437,338,112 bytes** against 2 GiB. Its index SHA-256 was
`2bcf6d313257d85f13199241f0cc603203596e062a2429012f371d0c7e5c36b0`;
the summary-file SHA-256 was
`d8a99abe40af7cfa908e9c21a4aa407dc146a839a5a70b18808b0472a10149e9`.
One-time verified model loading took 0.027 s; training-only neighbor
indexing took 5.875 s and 6,877,512 bytes. These are reported separately
from query ratios. The new route's query phase totals were 0.120 s setup,
1.254 s projection, 157.237 s refinement, 2.071 s decision, 21.262 s
failed-attempt fallback, and 21.680 s rejected-uniform work: **203.624 s**.
The old route's corresponding total was **189.527 s**. Aggregate raw time
and arithmetic mean paired ratio weight cases differently; neither
measure rescues the failed frozen Gate. Prior data/model preparation costs
remain offline costs in their original validation reports.

The complete routed comparison is below in persisted case order. A/B are
the physically matched positions defined above. `Fallback` retains a
failed learned attempt; `reject` is a predeclared fresh-uniform choice.

| Scale | Direction | Volume | Position | Old route | Old ratio | New route | New ratio | New status |
|---|---|---:|---|---|---:|---|---:|---|
| Small | y | 0.4675 | A | vector 29 | 1.088 | context 43 | 0.371 | accepted |
| Large | z | 0.5825 | B | vector 29 | 0.657 | vector 29 | 0.628 | accepted |
| Small | y | 0.5825 | B | vector 29 | 0.600 | context 43 | 0.814 | accepted |
| Large | y | 0.3175 | A | context 43 | 0.999 | context 17 | 1.025 | accepted |
| Large | z | 0.3175 | A | vector 29 | 0.702 | context 43 | 0.753 | accepted |
| Small | y | 0.3175 | A | vector 29 | 0.702 | context 43 | 0.475 | accepted |
| Large | z | 0.5825 | A | vector 29 | 0.526 | vector 29 | 0.519 | accepted |
| Large | y | 0.4675 | A | context 43 | 0.966 | context 17 | 0.672 | accepted |
| Small | z | 0.3175 | B | context 17 | 0.448 | context 43 | 0.467 | accepted |
| Small | y | 0.3175 | B | vector 29 | 1.526 | context 43 | 0.660 | accepted |
| Large | z | 0.4675 | B | vector 29 | 0.520 | vector 29 | 0.515 | accepted |
| Small | z | 0.4675 | A | context 17 | 0.396 | context 43 | 0.822 | accepted |
| Small | z | 0.3175 | A | context 17 | 0.416 | context 43 | 0.433 | accepted |
| Large | y | 0.4675 | B | context 43 | 0.835 | context 17 | 0.976 | accepted |
| Small | z | 0.4675 | B | context 17 | 0.553 | context 43 | 0.376 | accepted |
| Large | y | 0.5825 | B | uniform reject | 0.947 | context 17 | 1.476 | fallback |
| Large | y | 0.3175 | B | context 43 | 0.843 | context 17 | 0.859 | accepted |
| Small | z | 0.5825 | A | context 17 | 0.356 | context 43 | 0.357 | accepted |
| Small | z | 0.5825 | B | context 17 | 0.375 | context 43 | 0.380 | accepted |
| Large | y | 0.5825 | A | uniform reject | 1.002 | uniform reject | 1.030 | reject |
| Large | z | 0.4675 | A | vector 29 | 0.495 | context 43 | 0.641 | accepted |
| Small | y | 0.4675 | B | vector 29 | 0.357 | context 43 | 0.431 | accepted |
| Small | y | 0.5825 | A | vector 29 | 0.815 | context 43 | 0.836 | accepted |
| Large | z | 0.3175 | B | vector 29 | 0.351 | vector 29 | 0.353 | accepted |

## Diagnosis and next decision

The new small-y context-43 choice avoided the old vector route's quality
failure at low-volume position B and reduced small-y mean from `0.848` to
`0.598`. But the position-based high-volume large-y acceptance did not
transfer: at volume `0.5825`, position B, context 17's final compliance
was `0.02807710` versus uniform `0.02794011`, above the unchanged 0.1%
allowance. Its failed attempt plus fresh fallback cost **1.476** times
uniform; the old route's predeclared fresh-uniform rejection cost **0.947**.
At position A, both routes rejected and paid approximately uniform cost.
The presumed lower-z large-z advantage of context 43 also did not transfer:
vector 29 was faster at lower-z position A for both volumes `0.3175`
and `0.4675`. The new route's small-z context-43 choice was also slower
than the old context-17 route on several cases. These are measured
development failures, not permission to fit a new position threshold to
the exposed cohort.

An independent standard-library audit recomputed the canonical plan and
exposure separation, verified source fit/screen and checkpoint hashes and
selection minima, 24 reference records and 24 unique screen strata,
192 ordered outcomes, both route decisions, independent quality/fallback
semantics, every phase sum and paired ratio, scale/direction/overall means,
resource caps, and the frozen Gate. It reproduced **one eligible old route,
an ineligible new route, and a failed B2.15 Gate**. The audit code and
generated artifacts remain outside Git.

The next independent slice should be **B2.16, a bounded method-class
reassessment** of the learned warm-start approach and its attainable
same-quality speed headroom. Repeating local position-threshold searches
on exposed cohorts is not justified. Freeze the B2.16 question, stopping
rule, and evidence boundary before any new outcome. B3 remains closed.

## Repository validation

Before the clean-revision run, `uv sync --dev --locked`, Ruff, mypy on
`src`, all **329 Python tests**, and `git diff --check` passed. The required
checks are repeated before committing this validation report.
