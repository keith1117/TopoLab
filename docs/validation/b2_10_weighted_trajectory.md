# B2.10 sensitivity-weighted trajectory objective and reference-feasibility stop

Date: 2026-09-26 (America/New_York)

Status: **B2.10 complete; the frozen development feasibility Gate failed.**
All 480 offline weights and three deterministic fits completed. The new
screen retained 9/12 cases and 99/132 ordered method outcomes, then stopped
at the tenth case because its mandatory uniform reference did not converge
within the frozen 240-update limit. An incomplete screen cannot satisfy the
Gate, regardless of any partial speed ratios. This is development evidence,
not final ML evidence or a v2 delivery result. Uniform initialization remains
the operational default.

## Frozen boundary and execution

The [B2.10 protocol](../planning/b2_10_weighted_trajectory_protocol.md)
fixed one training-objective change before any weight generation, fitting,
or screening. The 480 checksum-audited B2.6 update-30 target states, 468/12
train/selection split, B2.9 13-channel vector input and 12,577-parameter
CNN, seeds 17/29/43, optimizer, schedule, patience, 240-update solver,
quality checks, and complete fallback charges were unchanged. Only fitting
and checkpoint selection replaced unweighted design-density MSE with the
mean of squared error times the B2.4 bounded absolute compliance-sensitivity
weight at each target state. The weight is normalized, clipped to
`[0.25, 4]`, and renormalized to mean one. No query-time FEM feature or
weight construction was introduced. B2.5's earlier negative weighted
**final-density** experiment remains negative evidence.

The read-only plan's canonical SHA-256 was
`d3fd19a8a16d4d7d6dc2ae02a731de45654a53c0d5e44c1945331cbf61f1a079`;
its saved file SHA-256 was
`0862dd63d00f22a80b76a9732c5e054bc03537bf1fcc662fccc8fb2dfacf2d25`.
The clean tracked execution revision was
`c1ac05a459803289f067dd67d2b5a7fb9da6693f`. The B2.6 source
target-index SHA-256 was
`5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`;
the fixed B2.9 control fit-index SHA-256 was
`96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`.
All generated weights, models, selections, and outcomes remained outside Git.
No M2 test/OOD or M3 final label or outcome was opened.

The new screen crossed volumes `0.2875, 0.4375, 0.5875`, y/z point-load
directions, and `(12,6,3)`/`(24,12,6)` meshes, with the small-mesh load
at `(x=max,y=2,z=2)` and a physically matched large-mesh node. All twelve
case IDs were disjoint from 528 previously exposed development IDs; these
volumes were absent from the B2.4/M2 and design-exposed M3 v1 catalogs.
Each case was to receive uniform, physics heuristic, training-only nearest
neighbor, B2.5 control seed 43, three fixed B2.9 vector models, three new
B2.10 weighted models, and an impossible own-trajectory oracle.

Execution used Apple arm64, macOS, Python 3.12.10, NumPy 2.5.3, SciPy
1.18.1, PyTorch 2.14.0, and safetensors 0.8.0. PyTorch intra-op and
BLAS/OMP/VECLIB/MKL/BLIS threads were one; PyTorch reported eight inter-op
threads. `uv.lock` SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.

## Complete offline weights and fits

All 480 source targets produced a content-addressed float32 sensitivity
weight artifact with the matched case/split/target identity, re-solved
physical-state compliance, shape, and checksum. Their index SHA-256 was
`2028ad08d87679aa5bb5aca377b556f7dc0914b76b948de02c58b936211406c4`;
weight-summary file SHA-256 was
`8d6d4cedb56041a046234f35ed8d2bd313f9dc9fbbc9d6ca5b276edf0541834d`.
Generation took **57.62 s** against a 7,200 s cap, with **288,473,088
bytes** peak RSS against 2 GiB. A separate independent audit verified all
480 hashes, identities, float32 values, finite positive weights, mean-one
constraint, and source references before fitting.

| Seed | Epochs run | Selected epoch | Weighted validation loss | Fit seconds |
|---:|---:|---:|---:|---:|
| 17 | 149 | 124 | 0.057894 | 48.67 |
| 29 | 146 | 121 | 0.064327 | 46.25 |
| 43 | 200 | 193 | 0.057949 | 64.87 |

The three-fit index SHA-256 was
`0d2138bfdcfc4f9d730c6261bccc1ce8bf2ddda2f50a70f5e5e0958b5fcc1851`;
fit-summary file SHA-256 was
`26265f077af4b790541b74645c2045d95ecfc32f8ca7606b5dbbb7d14bbd1798`.
The fit took **190.39 s** against 7,200 s, with **402,472,960 bytes** peak
RSS. The audit independently checked all checkpoint and selection hashes,
ordered epoch histories, and earliest validation minimum. B2.6 target
generation and B2.9 control fitting were separate historical offline costs,
not hidden in B2.10 query times.

## Nine complete cases and the mandatory-reference failure

The first nine sorted cases retained **99/99 planned method outcomes** with
full SIMP refinement, independent quality re-solve, and a fresh complete
uniform fallback after a rejected attempt. Their screen-index SHA-256 was
`a5a538f580e0ab03185e6d2c58d207a85f8c33ca7c77d7c5a56c0b196df6ceae`.
They took **919.31 s** with **420,380,672 bytes** peak RSS, both within the
14,400 s and 2 GiB screen caps. One-time model loading took 0.015 s;
training-only neighbor indexing took 5.933 s and 6,877,512 bytes. The
nondeployable oracle's target generation took another 27.951 s, separately
reported.

The following means are **descriptive partial-cohort results**, using five
small and four large cases. They are not the frozen six-per-scale Gate means.
All ratios include complete fallback charges.

| Method | Small mean, n=5 | Large mean, n=4 | Rejected / 9 |
|---|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 0 |
| Physics heuristic | 1.312 | 1.103 | 1 |
| Nearest neighbor | 0.627 | 2.144 | 2 |
| B2.5 control 43 | 0.861 | 0.872 | 0 |
| B2.9 vector 17 | 0.578 | 0.722 | 0 |
| B2.9 vector 29 | 0.544 | 0.732 | 0 |
| B2.9 vector 43 | 0.745 | 0.934 | 1 |
| B2.10 weighted 17 | 0.648 | 0.751 | 0 |
| B2.10 weighted 29 | 0.831 | 0.845 | 1 |
| B2.10 weighted 43 | 0.513 | 0.976 | 0 |
| Exact own-trajectory oracle, impossible | 0.509 | 0.805 | 0 |

Per-case ratios for all six matched vector/weighted models are below. `*`
marks a rejected candidate with fully charged fresh uniform fallback. The
external index retains all eleven outcomes, individual numerical metrics,
failure codes, and phase times for each completed case.

| Scale | Direction | Volume | Vector 17 | Vector 29 | Vector 43 | Weighted 17 | Weighted 29 | Weighted 43 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| large | z | 0.4375 | 0.428 | 0.702 | 0.421 | 0.427 | 0.575 | 0.822 |
| small | y | 0.5875 | 0.722 | 0.650 | 0.688 | 0.701 | 0.921 | 0.610 |
| large | z | 0.5875 | 0.669 | 0.518 | 0.676 | 0.642 | 0.655 | 0.864 |
| small | y | 0.2875 | 0.459 | 0.767 | 0.514 | 0.846 | 0.616 | 0.496 |
| large | y | 0.4375 | 0.786 | 0.787 | 0.771 | 0.640 | 0.913 | 0.747 |
| large | y | 0.2875 | 1.003 | 0.923 | 1.870 | 1.294 | 1.237 | 1.469 |
| small | y | 0.4375 | 0.585 | 0.367 | 0.627 | 0.562 | 0.613 | 0.426 |
| small | z | 0.4375 | 0.368 | 0.568 | 0.592 | 0.656 | 0.511 | 0.573 |
| small | z | 0.2875 | 0.755 | 0.367 | 1.302* | 0.477 | 1.492* | 0.458 |

All 99 operational outcomes met physical-volume error `<=0.005` and final
compliance `<=1.001` times the matched uniform reference. There were zero
accepted quality violations. Five attempts were rejected and charged full
fallbacks: nearest neighbor twice, physics heuristic once, B2.9 vector 43
once, and B2.10 weighted 29 once. Three were quality failures before the
cap; the two nearest-neighbor attempts hit 240 updates. On this incomplete
cohort the weighted objective had no consistent advantage over the fixed
B2.9 vector controls, especially at large `y/0.2875`; no complete-cohort
ranking or success claim follows.

The tenth case was large `(24,12,6)`, z load, volume `0.2875`, ID
`tlcase-v1-dc08005b63bfbdbfe06e98ba9d377dfb38b5b51990d11dee0dff904f2c3157da`.
The required uniform attempt reached **240/240 updates**, with finite
compliance `0.244202641249` and physical-volume error `1.66e-9`, but
`validate_refinement_quality` rejected it for nonconvergence. A separate
repeat reproduced the same outcome. The runner correctly stopped before
assigning a reference compliance or comparing learned candidates. It did
not drop the case or relabel the failed reference. Read-only uniform
diagnosis showed cases eleven and twelve do pass at the original cap.
The diagnosis-file SHA-256 was
`24d21bd1152d8dd2796a92069b9c7da0bb04d8dd90863a5099ac1440e11b30d1`.

For **development diagnosis only**, changing the tenth geometry's cap to
360 generated a new case ID and let uniform converge in 282 updates, with
compliance `0.243903721134` and physical-volume error `2.55e-9`. The
separate cap-diagnosis file SHA-256 was
`026d4bf871525e1c32033feb34ea1023c7ce29814a73e92be66d65690589d435`.
This new-policy run is not part of B2.10, was not used as a denominator,
and cannot turn its failed Gate into a pass.

## Independent audit, Gate decision, and next slice

An independent audit recomputed the plan identity, checked all 480 weight
files and source target links, three selections/checkpoints and earliest
minima, nine ordered unique screen rows and 99 outcome methods, timing sums,
charged paired ratios, success/fallback states, and operational/accepted
quality bounds. The cap and uniform failure were independently reproduced.
The runner exited with an error at the mandatory uniform reference rather
than producing a misleading partial Gate summary. The frozen Gate required
all 12 cases and 132 outcomes plus at least two new seeds meeting both
scale means `<=0.90` and every direction mean `<=1.0`, zero accepted quality
violations, and all resource caps. **The completeness and reference-quality
conditions failed; no seed can be declared passing.**

The next independent slice, **B2.11**, should version a bounded
reference-iteration repair and independently establish full reference
feasibility before comparing the unchanged B2.9/B2.10 models on a fresh,
disjoint development screen. It must retain the failed B2.10 result,
account for all fallback and offline costs, and inspect any remaining
learning-side cost gap before B3. No final cohort registration, stable
learned-acceleration claim, or v2 flagship delivery is justified. Stop
after this slice until separately started.
