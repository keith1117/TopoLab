# B2.14 larger development confirmation

Date: 2026-09-27 (America/New_York)

Status: **The frozen B2.14 development confirmation Gate failed.** All 24
fresh uniform references passed, and all 192 fixed-method outcomes on 24
physically disjoint cases were retained and independently audited. No
candidate met the predeclared two-scale and direction-wise limits; the
selection rule chose no policy. This negative result does not alter the
passing *small* B2.13 screen. Uniform initialization remains the operational
default, and B3's final ML contract remains closed.

## Frozen boundary and provenance

The [B2.14 protocol](../planning/b2_14_development_confirmation_protocol.md)
fixed the cases, methods, resource caps, quality rules, and policy selection
before any new outcome. The canonical plan SHA-256 was
`236ceafce97fad8282b32b0c7f5def38954d22b302a761aeb64196197dad3673`;
the saved plan-file SHA-256 was
`f121a9bd2aeb5c353daa4179dbf38dbe6051aff5143a279dc7547230a43ba8f4`.
The clean execution revision was
`884a3371c8aa919f96b4db27018b5066677bbf69`. The B2.9/B2.12
fit-index and B2.12/B2.13 exposed screen-index digests matched the frozen
values. All six model selections and checkpoint bytes were verified against
their content hashes and earliest validation minima before screening.

The new cohort crossed volumes `0.3125, 0.4625, 0.5925`, small-mesh load
positions A=`(x=max,y=3,z=1)` and B=`(x=max,y=5,z=2)` with physically
doubled large-mesh nodes, y/z directions, and `(12,6,3)`/`(24,12,6)`
meshes. Exactly two cases occupied each scale/direction/volume cell. All
24 new case IDs and all three volumes were absent from the 588-case prior
development ledger and the design-exposed M3 v1 final volumes. M2 test/OOD
and new final outcomes remained sealed. No new model was fitted, and no
solver, tolerance, checkpoint, route, or cohort was changed after freezing.

Execution used the locked Python 3.12.10 environment on Apple arm64/macOS,
one PyTorch CPU thread and one BLAS/OMP thread. The `uv.lock` SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.

## References, complete comparison, and Gate

**24/24** separately run uniform references passed convergence, positive
finite compliance, independent final-state checks, and physical-volume
error `<=0.005`. They stopped after **26–181** updates. Reference execution
took **229.74 s** versus the 3,600 s cap and peaked at **458,784,768 bytes**
versus 2 GiB. Its index SHA-256 was
`b44c98573d50b1e9c26b5a8ff3bf42ebe211197455c88d5f65f2a01f941a010e`.
The screen ran a *new* uniform for each paired timing denominator.

Every case retained fresh uniform, physics heuristic, B2.4 train-only
nearest neighbor, B2.9 vector 29, B2.12 context 17/29/43, and the B2.13
route in frozen order: **192/192 outcomes**. The table reports arithmetic
means of the fully charged *per-case* time ratios, not a ratio of summed
times. A failed attempt keeps its failed status and pays a fresh uniform
fallback. All operational results met the `0.005` physical-volume and
`1.001` matched-uniform compliance bounds; there were **zero accepted
quality violations**.

| Method | Small | Large | Small y | Small z | Large y | Large z | Failed attempts |
|---|---:|---:|---:|---:|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 |
| Physics heuristic | 1.210 | 1.048 | 1.250 | 1.170 | 1.054 | 1.042 | 1 |
| Nearest neighbor | 0.792 | 3.030 | 1.218 | 0.366 | 2.923 | 3.136 | 7 |
| B2.9 vector 29 | 1.003 | 1.024 | 1.166 | 0.840 | 1.136 | 0.913 | 3 |
| B2.12 context 17 | 0.805 | 0.931 | 0.783 | 0.826 | 1.001 | 0.862 | 2 |
| B2.12 context 29 | 0.721 | 0.997 | 0.769 | 0.673 | 1.243 | 0.752 | 3 |
| B2.12 context 43 | 0.577 | 1.025 | 0.593 | 0.560 | 1.181 | 0.868 | 2 |
| **B2.13 route** | **0.971** | **0.925** | **1.112** | **0.830** | **0.946** | **0.904** | **1** |

The route rejected both high-volume large-y cases before inference and
charged fresh uniform work, then had one failed selected attempt at small
y/0.5925/A, which paid fallback. The route's scale means exceeded the
`0.90` limit, and small-y exceeded `1.0`. Vector 29 exceeded both scale
limits and had three failures. Context 17 missed the large-scale limit
(`0.931`) and large-y limit (`1.000646`) despite only two failures.
Context 29 and 43 also missed the large-scale and large-y limits; context
29 had three failures. Thus **zero policies were eligible**, no policy was
selected, and the confirmation Gate failed. Context 43's low overall mean
of `0.801` cannot override its large-scale and large-y failures.

The route's per-case record is below. Positions A/B are defined above;
fixed-model columns show their own fully charged ratios on the same case.
`Fallback` retains a failed learned attempt; `reject` is the route's
predeclared uniform choice and is not a learned failure.

| Scale | Direction | Volume | Position | Route | Routed ratio | Status | Vector 29 | Context 17 | Context 29 | Context 43 |
|---|---|---:|---|---|---:|---|---:|---:|---:|---:|
| Large | y | 0.3125 | A | context 43 | 0.932 | accepted | 1.047 | 0.875 | 1.132 | 0.928 |
| Large | y | 0.3125 | B | context 43 | 0.848 | accepted | 0.873 | 0.724 | 0.965 | 0.836 |
| Large | y | 0.4625 | A | context 43 | 1.136 | accepted | 0.769 | 0.876 | 0.893 | 1.106 |
| Large | y | 0.4625 | B | context 43 | 0.739 | accepted | 0.629 | 0.779 | 0.714 | 0.733 |
| Large | y | 0.5925 | A | uniform reject | 1.024 | reject | 1.740 | 2.136 | 2.199 | 1.908 |
| Large | y | 0.5925 | B | uniform reject | 0.998 | reject | 1.756 | 0.614 | 1.557 | 1.576 |
| Large | z | 0.3125 | A | vector 29 | 1.116 | accepted | 1.140 | 1.405 | 1.211 | 1.009 |
| Large | z | 0.3125 | B | vector 29 | 0.661 | accepted | 0.656 | 0.580 | 0.678 | 0.806 |
| Large | z | 0.4625 | A | vector 29 | 1.531 | accepted | 1.539 | 0.458 | 0.696 | 0.507 |
| Large | z | 0.4625 | B | vector 29 | 0.579 | accepted | 0.575 | 0.607 | 0.732 | 0.670 |
| Large | z | 0.5925 | A | vector 29 | 0.975 | accepted | 0.964 | 1.297 | 0.590 | 1.516 |
| Large | z | 0.5925 | B | vector 29 | 0.565 | accepted | 0.604 | 0.826 | 0.601 | 0.701 |
| Small | y | 0.3125 | A | vector 29 | 1.251 | accepted | 1.139 | 0.702 | 0.788 | 0.567 |
| Small | y | 0.3125 | B | vector 29 | 0.750 | accepted | 0.901 | 0.661 | 0.714 | 0.697 |
| Small | y | 0.4625 | A | vector 29 | 1.550 | accepted | 1.621 | 0.616 | 0.599 | 0.611 |
| Small | y | 0.4625 | B | vector 29 | 1.026 | accepted | 1.068 | 0.812 | 0.500 | 0.617 |
| Small | y | 0.5925 | A | vector 29 | 1.474 | fallback | 1.574 | 1.394 | 1.476 | 0.483 |
| Small | y | 0.5925 | B | vector 29 | 0.624 | accepted | 0.691 | 0.516 | 0.537 | 0.582 |
| Small | z | 0.3125 | A | context 17 | 0.611 | accepted | 1.269 | 0.564 | 0.574 | 0.455 |
| Small | z | 0.3125 | B | context 17 | 0.554 | accepted | 0.568 | 0.549 | 0.557 | 0.604 |
| Small | z | 0.4625 | A | context 17 | 0.610 | accepted | 0.724 | 0.644 | 0.670 | 0.437 |
| Small | z | 0.4625 | B | context 17 | 0.728 | accepted | 0.738 | 0.736 | 0.699 | 0.387 |
| Small | z | 0.5925 | A | context 17 | 1.880 | accepted | 1.036 | 1.868 | 0.727 | 0.782 |
| Small | z | 0.5925 | B | context 17 | 0.597 | accepted | 0.705 | 0.594 | 0.811 | 0.698 |

The full screen took **2,243.87 s** against 10,800 s and peaked at
**390,971,392 bytes** against 2 GiB. Its index SHA-256 was
`2c2bb58c40bf1e2099fd21ecf3cc74a5425ca3f1ad28ac183611c1535bb4e6c9`;
the summary-file SHA-256 was
`e9bb4f3375cae9ac49133b4611793aca2ba2650f03e7426baca4c50f7354dbf5`.
One-time verified model loading took 0.059 s; train-only neighbor indexing
took 6.121 s and 6,877,512 bytes. These are reported separately from
query-time ratios. The route's complete query phase totals were 0.073 s
setup, 1.168 s projection, 176.857 s refinement, 2.010 s decision,
0.614 s failed-attempt fallback, and 42.101 s rejected-uniform work:
**222.824 s** total. Per-method aggregate phases are retained in the
external screen summary. Prior target generation and model fitting costs
remain offline costs recorded in their original validation reports.

## Independent audit and next decision

An independent standard-library audit recomputed the canonical plan,
exposure separation, all source fit/screen and checkpoint hashes, earliest
selection minima, 24 reference identities and quality records, 24 unique
screen strata, 192 ordered outcomes, route/rejection decisions, candidate
quality and fallback semantics, each phase sum and paired ratio, all
scale/direction means, resource caps, and the frozen eligibility and
selection rules. It reproduced **zero eligible policies and a failed B2.14
Gate**. Generated plans, indices, logs, and audit code remain outside Git.

The failure is concentrated in transfer across load position and high
volume. Small-y vector 29 was slower than uniform on four of six cases and
failed quality at high-volume position A: its final compliance was
`0.02551657` versus uniform `0.02548450`, exceeding the unchanged 0.1%
allowance. The route's large-z vector choice was slow at position A for
volumes `0.3125` and `0.4625`. The high-volume large-y rejection avoided
several fixed-model quality failures, but paid approximately uniform cost.
These are development diagnoses, not permission to change this Gate or to
select a favorable subgroup.

The next independently started slice should be **B2.15**, a bounded
position-aware routing/reliability intervention focused on the measured
small-y quality/refinement and large-z position transfer failures. Freeze
its exact policy, disjoint cases, resources, and Gate before opening new
outcomes. B3 and any final acceleration claim remain closed.

## Repository validation

Before the clean-revision run, `uv sync --dev --locked`, Ruff, mypy on
`src`, all **324 Python tests**, and `git diff --check` passed. The
required checks are repeated before committing this validation report.
