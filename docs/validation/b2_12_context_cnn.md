# B2.12 spatial-context CNN and fresh development screen

Date: 2026-09-27 (America/New_York)

Status: **The reference and fit Gates passed; the learned-prototype
development Gate failed.** All twelve new uniform references converged,
all three fixed CNN fits completed, and all 132 method outcomes on twelve
new cases were retained and independently audited. No new seed met the
frozen two-scale and direction-wise charged-speed limits. This is
development evidence only. Uniform remains the operational default;
neither a learned-acceleration nor full-v2-delivery claim is supported.

## Frozen intervention, identity, and exposure

The [B2.12 protocol](../planning/b2_12_context_cnn_protocol.md) and
[numerical convention](../numerical_conventions.md) fixed one change before
execution: expand the B2.9 vector-input CNN from two local 3³ convolutions
to four 16-channel convolutions with `(z,y,x)` dilations `(1,1,1)`,
`(1,1,2)`, `(1,2,4)`, `(1,2,8)`. The new model has 26,433 parameters.
The 13-channel input, all 480 B2.6 update-30 targets, unweighted MSE,
three seeds `17,29,43`, optimizer and schedule, validation selection,
projection, SIMP solver, 360-update budget, quality boundary, and fully
charged fresh uniform fallback were unchanged. No B2.11 result entered
training or checkpoint selection. Historical checkpoints stayed immutable.

The canonical read-only plan SHA-256 was
`968d503bbdf30d3831e525a359a45315a620a114ac54ec61823b3df2ff7a8f97`;
the saved plan-file SHA-256 was
`621962bb96597c373cce4e806701a3fb656cf87eb0cdb9af7b13e6fbbf950905`.
The clean tracked execution revision was
`a72d836dc21fdb4249c817ed053f319609c133d3`.
The B2.6 target-index and unchanged B2.9 fit-index SHA-256 values were
`5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`
and `96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`.
All source targets and old-model selections/checkpoints were verified
before fitting. B2.4 nearest-neighbor sources and the B2.5 control were
also audited before screening.

The screen crossed volumes `0.3025,0.4525,0.6025`, y/z point-load
directions, and `(12,6,3)`/`(24,12,6)` meshes, with one case per
scale/direction/volume stratum. Its small-mesh load node was
`(x=max,y=4,z=1)` with the doubled physical counterpart on the large
mesh. The twelve case IDs were disjoint from 564 development-exposed IDs;
the volumes were absent from earlier development and design-exposed final
catalogs. M2 test/OOD and new final labels/outcomes remained sealed.

Execution used Apple arm64, macOS, Python 3.12.10, NumPy 2.5.3, SciPy
1.18.1, PyTorch 2.14.0, and safetensors 0.8.0. PyTorch intra-op and
BLAS/OMP/VECLIB/MKL/BLIS threads were one; PyTorch reported eight
inter-op threads. The `uv.lock` SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.
All generated artifacts and logs remained outside Git.

## Reference and fit Gates

Before fitting or loading a learned model, all **12/12** new uniform
references passed unchanged convergence, independent final-state
quality, and physical-volume error `<=0.005`. Their stop iterations
ranged **39–133**, entirely below the historical 240-update cap. Thus
the 360-update comparison did not inflate any fresh uniform denominator.
The reference stage took **124.77 s** against 1,800 s and peaked at
**374,423,552 bytes** against 2 GiB. Its index SHA-256 was
`3e7b66f1e802e79828b7505c60a2f70766a4ef17722f8c4f7657b7bbde591905`;
the summary-file SHA-256 was
`6f17bcfab0eb1312a066996822a0e0c62b300fd52ea9d2f9439bc2de9a5bf735`.
The screen later ran a fresh uniform per case for paired timing; it did
not substitute preflight time as a denominator.

Three deterministic fits used the same 468 training and 12 checkpoint-
selection cases. Each model selected the earliest strict validation-MSE
minimum under the unchanged 200-epoch/25-patience rule:

| Seed | Epochs run | Selected epoch | Validation MSE | Fit seconds |
|---:|---:|---:|---:|---:|
| 17 | 185 | 160 | 0.028346 | 115.05 |
| 29 | 166 | 141 | 0.026953 | 98.95 |
| 43 | 185 | 160 | 0.029582 | 111.12 |

These MSE values were below the old B2.9 seeds' 0.047949, 0.057367,
and 0.054440, respectively. The three-fit stage took **331.65 s**
against 7,200 s and peaked at **343,408,640 bytes** against 2 GiB.
Its index SHA-256 was
`0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce`;
the fit-summary file SHA-256 was
`0699c67918b07fb59ee643204a71472ef5063d372351185625c3c5da9cc3d71c`.
Prior B2.6 target generation cost 376.86 s and the old B2.9 fit cost
169.53 s; both are separate offline costs, not hidden in query time.

## Complete screen and Gate

Every case received eleven methods: fresh uniform, physics heuristic,
B2.4 training-only nearest neighbor, B2.5 MSE control seed 43, the
three unchanged B2.9 vector models, the three new B2.12 context models,
and an impossible exact own-trajectory oracle. Each candidate received
full projection, SIMP refinement, independent quality re-solve, and a
fresh complete uniform fallback if rejected. The table reports the
arithmetic mean of six complete paired time ratios per mesh scale.

| Method | Small mean | Large mean | Rejected / 12 |
|---|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 0 |
| Physics heuristic | 1.727 | 1.082 | 1 |
| Nearest neighbor | 0.216 | 2.826 | 3 |
| B2.5 control 43 | 1.406 | 1.894 | 3 |
| B2.9 vector 17 | 0.856 | 1.193 | 3 |
| B2.9 vector 29 | 0.653 | 0.927 | 1 |
| B2.9 vector 43 | 1.160 | 1.039 | 2 |
| B2.12 context 17 | 0.799 | 1.348 | 1 |
| B2.12 context 29 | 0.857 | 1.376 | 2 |
| B2.12 context 43 | 0.686 | 1.283 | 2 |
| Exact own-trajectory oracle, impossible | 0.559 | 0.799 | 0 |

The frozen Gate requires at least **two of three new B2.12 seeds**, each
with both scale means `<=0.90` and all four scale/direction means
`<=1.0`, plus zero accepted quality violations, full outcomes, and
resource compliance. No new seed met the large-scale mean bound; none
passed the complete Gate. Their direction-wise means were:

| Method | Small y | Small z | Large y | Large z |
|---|---:|---:|---:|---:|
| B2.9 vector 17 | 1.117 | 0.595 | 1.572 | 0.815 |
| B2.9 vector 29 | 0.686 | 0.620 | 1.207 | 0.646 |
| B2.9 vector 43 | 1.491 | 0.829 | 1.307 | 0.771 |
| B2.12 context 17 | 1.047 | 0.551 | 1.251 | 1.446 |
| B2.12 context 29 | 1.121 | 0.594 | 1.361 | 1.391 |
| B2.12 context 43 | 0.812 | 0.560 | 1.107 | 1.459 |

Per-case ratios expose the improvement and regression. `*` marks a
rejected candidate that paid a fresh uniform fallback.

| Scale | Direction | Volume | Old 17 | Old 29 | Old 43 | New 17 | New 29 | New 43 | Oracle |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| small | y | 0.3025 | 0.491 | 0.662 | 0.456 | 0.536 | 0.599 | 0.436 | 0.384 |
| small | y | 0.4525 | 1.181 | 0.614 | 1.200 | 1.663 | 1.185 | 0.492 | 0.612 |
| large | z | 0.6025 | 0.463 | 0.533 | 0.561 | 0.743 | 0.530 | 1.005 | 1.028 |
| small | z | 0.6025 | 0.394 | 0.429 | 0.521 | 0.539 | 0.427 | 0.414 | 0.297 |
| large | y | 0.4525 | 0.680 | 0.657 | 0.743 | 0.680 | 0.676 | 0.608 | 0.721 |
| large | y | 0.6025 | 1.844* | 1.731* | 2.036* | 2.035* | 2.089* | 1.653* | 0.744 |
| large | z | 0.3025 | 1.385 | 0.511 | 0.932 | 1.944 | 1.777 | 1.498 | 0.786 |
| large | z | 0.4525 | 0.596 | 0.894 | 0.820 | 1.652 | 1.866 | 1.873 | 0.853 |
| large | y | 0.3025 | 2.193* | 1.234 | 1.143 | 1.036 | 1.317 | 1.061 | 0.659 |
| small | z | 0.4525 | 0.444 | 0.531 | 1.302 | 0.515 | 0.559 | 0.823 | 0.555 |
| small | z | 0.3025 | 0.946 | 0.900 | 0.663 | 0.599 | 0.795 | 0.442 | 0.441 |
| small | y | 0.6025 | 1.678* | 0.784 | 2.819* | 0.942 | 1.580* | 1.507* | 1.063 |

All **132 operational outcomes** met the frozen volume and compliance
quality bounds; there were zero accepted quality violations. The new
seeds had one/two/two rejected attempts, each fully charged with fallback.
At large `y/0.6025`, all three new starts stopped in 68–116 updates
versus uniform's 107, but their final compliance was **1.00391–1.00458
times** uniform, above the allowed 1.001, so all paid roughly 19 s for
fresh fallback. Larger spatial context alone did not repair this solution-
basin gap. At small `z/0.3025`, all three new starts passed quality and
took 31–51 updates versus uniform's 62; their charged ratios 0.442–0.795
improved on their matched old models' 0.663–0.946. Yet at large z volumes
0.3025 and 0.4525, the new starts took 173–257 updates where uniform
took 117–133, yielding charged ratios 1.498–1.944. Lower validation MSE
therefore did not translate into robust two-scale operational speed.

The screen-index SHA-256 was
`cb671b2e9b5194606964faed0c6022c4a9a181b978827f906bfe416f72516443`;
the summary-file SHA-256 was
`553fe8fed28d6cceb811bff3d0aa705970e56d3aa6a65c04863b409566220833`.
The complete screen took **1,849.15 s** against 14,400 s and peaked at
**334,938,112 bytes** against 2 GiB. One-time model loading took
0.018 s; training-only neighbor indexing took 6.113 s and 6,877,512
bytes. The impossible oracle's own-case target generation took 43.939 s
separately. The runner exited with code 1 solely because its fully
retained learned-prototype Gate was false.

| Method | Setup | Projection | Refinement | Decision | Fallback | Charged total, s |
|---|---:|---:|---:|---:|---:|---:|
| Uniform | 0.00 | 0.73 | 121.48 | 1.15 | 0.00 | 123.37 |
| B2.9 vector 29 | 0.06 | 0.70 | 89.10 | 1.24 | 18.87 | 109.96 |
| B2.12 context 17 | 0.21 | 0.70 | 145.46 | 1.19 | 19.26 | 166.82 |
| B2.12 context 29 | 0.13 | 0.68 | 147.07 | 1.26 | 19.69 | 168.82 |
| B2.12 context 43 | 0.09 | 0.69 | 135.51 | 1.21 | 19.81 | 157.31 |
| Exact own-trajectory oracle | 0.00 | 0.68 | 96.42 | 1.17 | 0.00 | 98.27 |

## Independent audit, decision, and next slice

A separate standard-library audit recomputed the canonical plan SHA-256,
source-index hashes, 12 unique unexposed screen IDs and strata, all 12
reference identities/quality results, all three checkpoint/selection
checksums and earliest validation minima, 132 ordered outcomes, phase-time
sums, paired ratios, fallback identities, operational quality, per-scale
and direction means, resource caps, and the frozen Gate. It reproduced
zero passing new seeds. The smaller validation MSE is a training result,
not a substitute for the failed operational Gate.

**B2.12 fails learned-prototype feasibility.** The next independent
slice, **B2.13**, should freeze one deployable workload-aware routing and
rejection policy motivated by the exposed evidence: retain the older
vector model where large-z context predictions regress, use the context
model where small-z refinement improves, and safely reject known
high-volume y risk. Charge any selected inference, decision, rejection,
and uniform work. This is a hypothesis from exposed development data,
not a passed gate or permission to mix favorable outcomes post hoc; it
requires a new, physically disjoint screen and fixed rules before
execution. Do not enter B3, open final evidence, or announce acceleration
until the prescribed development and final Gates pass. Stop after this
slice until separately started.

## Repository validation

Before the clean-revision run, `uv sync --dev --locked`, Ruff, mypy on
`src`, all **316 Python tests**, and `git diff --check` passed. The
B2.12 runner also passed a focused mypy check. The required repository
Gate is repeated before committing this report; generated indices,
checkpoints, selections, and diagnostic logs are not committed.
