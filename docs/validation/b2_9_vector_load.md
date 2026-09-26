# B2.9 vector point-load conditioning and fresh development screen

Date: 2026-09-26 (America/New_York)

Status: **B2.9 complete; the frozen development feasibility Gate failed.**
The new representation substantially improved two seeds, and those seeds
completed every new case without a fallback, but their large-mesh y-direction
means exceeded the preregistered bound. All 12 new cases and 132 method
outcomes were retained. This is development evidence, not final ML evidence or
a v2 delivery result. Uniform initialization remains the operational default.

## Frozen boundary and execution

The [B2.9 protocol](../planning/b2_9_vector_load_protocol.md) and
[numerical convention](../numerical_conventions.md) fixed one learning-side
change before fitting: replace B2.7's signed radial-distance field with a
signed one-hot point-load direction and three normalized load-relative
coordinates. The 13-channel, 12,577-parameter CNN retained the old depth,
hidden width, optimizer, loss, targets, fitting schedule, seeds, projection,
240-update physical-plateau solver, quality checks, and fully charged fresh
uniform fallback. The canonical read-only plan SHA-256 was
`b7703931dfe2eadbe9300506f288787e44b011e003c4e6fef67cd73ee9000138`;
the saved plan-file SHA-256 was
`6cb08b2cc1ab33ea7f15f3c2a60f20781c8cada3804a387659103de521959faa`.
The clean tracked execution revision was
`e90159b939ce44774ba3c3c56f2f4d8cb247c9fa`.

The same 480 checksum-audited B2.6 update-30 density targets were used:
468 training and 12 checkpoint-selection cases. The target-index SHA-256 was
`5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`.
The unchanged B2.7 fit-index SHA-256 was
`36158e03a476fdff183d8c72cf0e7143700e7bac3ccc531d7eda485ec390a631`.
All source target, selection, and checkpoint artifacts were re-read and
verified. The 12 new physical screen cases crossed volumes
`0.2625, 0.4125, 0.5625`, y/z load directions, and `(12,6,3)`/`(24,12,6)`
meshes, with one case per scale/direction/volume stratum. Their point load
used small-mesh node `(x=max,y=1,z=2)` and its physically matched large-mesh
node. All 12 case IDs were disjoint from the 516 prior development-exposed
fitting, selection, and screen IDs; the volumes were absent from the B2.4/M2
and design-exposed M3 v1 catalogs. No M2 test/OOD or M3 final label or outcome
was opened.

Three deterministic CPU fits used seeds 17, 29, and 43. Their selected
epochs, validation MSE, and fit times were:

| Seed | Epochs run | Selected epoch | Validation MSE | Fit seconds |
|---:|---:|---:|---:|---:|
| 17 | 200 | 194 | 0.047949 | 62.84 |
| 29 | 127 | 102 | 0.057367 | 38.36 |
| 43 | 200 | 185 | 0.054440 | 61.60 |

The three-fit index SHA-256 was
`96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`;
fit-summary file SHA-256 was
`46c7a9375138aa6efc2f956c2d3f682b3318cbcef27214daf1d23141149a86c7`.
The complete fit took **169.53 s**, below 7,200 s, and peaked at
**354,811,904 bytes**, below 2 GiB. Earlier B2.6 target generation cost
376.86 s and the B2.7 control fits cost 75.45 s; both are separate offline
costs and were not hidden in B2.9 query times.

Execution used Apple arm64, macOS, Python 3.12.10, NumPy 2.5.3, SciPy
1.18.1, PyTorch 2.14.0, and safetensors 0.8.0. PyTorch intra-op and
BLAS/OMP/VECLIB/MKL/BLIS threads were one; PyTorch reported eight inter-op
threads. `uv.lock` SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.
Generated targets, models, selections, and results remained outside Git.

## Complete screen and Gate

Each case produced the eleven fixed methods: fresh uniform, physics
heuristic, B2.4 training-only nearest neighbor, B2.5 control seed 43, three
unchanged B2.7 conditioned models, three new B2.9 vector models, and an
impossible exact own-trajectory oracle. All candidates underwent full SIMP
refinement, independent quality re-solve, and a fresh complete uniform
fallback when rejected. The following are arithmetic means of six fully
charged paired time ratios per scale.

| Method | Small mean | Large mean | Failed / 12 | Fallbacks / 12 |
|---|---:|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 0 | 0 |
| Physics heuristic | 1.156 | 1.053 | 0 | 0 |
| Nearest neighbor | 0.631 | 2.291 | 3 | 3 |
| B2.5 control 43 | 1.097 | 1.075 | 1 | 1 |
| B2.7 conditioned 17 | 0.911 | 1.021 | 1 | 1 |
| B2.7 conditioned 29 | 0.904 | 0.954 | 1 | 1 |
| B2.7 conditioned 43 | 1.224 | 1.957 | 5 | 5 |
| B2.9 vector 17 | 0.743 | 1.002 | 1 | 1 |
| B2.9 vector 29 | 0.613 | 0.871 | 0 | 0 |
| B2.9 vector 43 | 0.639 | 0.882 | 0 | 0 |
| Exact own-trajectory oracle, impossible | 0.442 | 0.680 | 0 | 0 |

The frozen Gate requires at least **two of the three new vector seeds** to
have a fully charged mean `<=0.90` on each scale and `<=1.0` in every
scale/direction stratum, with zero accepted quality violations, all 132
outcomes, and both resource caps. Seeds 29 and 43 met the two scale-mean
bounds and had no rejected attempt. **Neither met the large-y bound**, so
zero seeds passed the full Gate:

| Seed | Method | Small y | Small z | Large y | Large z |
|---:|---|---:|---:|---:|---:|
| 17 | B2.7 | 1.135 | 0.687 | 1.350 | 0.693 |
| 17 | B2.9 | 0.970 | 0.515 | 1.216 | 0.789 |
| 29 | B2.7 | 1.075 | 0.733 | 1.242 | 0.666 |
| 29 | B2.9 | 0.700 | 0.526 | **1.032** | 0.710 |
| 43 | B2.7 | 1.717 | 0.732 | 3.224 | 0.690 |
| 43 | B2.9 | 0.711 | 0.567 | **1.080** | 0.684 |

Per-case ratios below show all six matched learned models and the impossible
oracle. `*` marks a failed candidate with a fully charged fresh fallback.
The external checksum-addressed index retains all baselines, numerical
metrics, failure codes, and phase times.

| Scale | Direction | Volume | Old 17 | Old 29 | Old 43 | B2.9 17 | B2.9 29 | B2.9 43 | Oracle |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| large | y | 0.2625 | 1.49 | 0.96 | 2.77* | 1.60 | 1.03 | 1.26 | 1.00 |
| small | y | 0.4125 | 2.02* | 2.06* | 1.80* | 1.72* | 1.01 | 1.08 | 0.56 |
| small | z | 0.5625 | 0.74 | 0.71 | 0.70 | 0.57 | 0.65 | 0.61 | 0.13 |
| small | y | 0.5625 | 0.70 | 0.51 | 2.60* | 0.59 | 0.66 | 0.42 | 0.60 |
| large | y | 0.5625 | 1.19 | 1.89 | 3.66* | 1.30 | 1.31 | 1.21 | 0.64 |
| small | y | 0.2625 | 0.69 | 0.66 | 0.75 | 0.61 | 0.44 | 0.63 | 0.67 |
| large | z | 0.2625 | 0.81 | 0.81 | 0.81 | 0.73 | 0.83 | 0.83 | 0.58 |
| large | y | 0.4125 | 1.37 | 0.87 | 3.24* | 0.75 | 0.76 | 0.77 | 0.73 |
| large | z | 0.5625 | 0.67 | 0.64 | 0.66 | 0.92 | 0.74 | 0.68 | 0.51 |
| large | z | 0.4125 | 0.60 | 0.55 | 0.61 | 0.72 | 0.56 | 0.54 | 0.63 |
| small | z | 0.4125 | 0.77 | 0.63 | 0.77 | 0.59 | 0.63 | 0.66 | 0.49 |
| small | z | 0.2625 | 0.56 | 0.85 | 0.72 | 0.39 | 0.29 | 0.43 | 0.21 |

The screen-index SHA-256 was
`1d73e1097f49df3450e46bacffa82b30965391429d705fff64749ba8d2d88e67`;
screen-summary file SHA-256 was
`1a6c4797c1d043c04b9663fb0c1050243af3c95e350f45d98dfabacff8f66df5`.
The screen took **1,308.80 s (21.81 min)**, below 14,400 s, and peaked at
**347,389,952 bytes**, below 2 GiB. One-time model loading took 0.014 s;
training-only nearest-neighbor indexing took 6.009 s for 6,877,512 bytes.
Nondeployable oracle target generation cost another 35.491 s, reported
separately. The runner exited with code 1 solely because the complete frozen
Gate was false.

## Failure and cost diagnosis

All 132 operational outcomes satisfied physical-volume error `<=0.005` and
final compliance `<=1.001` times matched uniform. There were **zero accepted
quality violations**. Among the three new seeds, only seed 17 had one
rejected quality outcome, at small `y/0.4125`, and paid its full fallback.
The three B2.7 controls had seven combined failures on this same new cohort;
the three B2.9 models had one. Seeds 29 and 43 used no fallback. This is a substantial development-screen
reliability gain, but it is not a passed speed Gate.

At large `y/0.5625`, uniform converged in 74 updates. The B2.9 seed-29 and
seed-43 starts converged in 97 and 89 updates; their refinement times were
17.20 and 15.93 s versus the uniform 13.40 s complete run. Their paired
ratios were 1.306 and 1.210 even though both passed quality. At large
`y/0.2625`, uniform used 118 updates; the two starts used 124 and 146 and
had ratios 1.033 and 1.259. At large `y/0.4125`, the starts did help
(ratios 0.758 and 0.770), but the mean over the three large-y cases remained
above 1.0. The impossible oracle's large `y/0.5625` ratio was 0.637,
indicating case-specific trajectory headroom; its large `y/0.2625` ratio
was about 1.000, so headroom is not uniform across cases.

Actual phase sums across 12 cases are below. They are not the Gate's mean
of paired per-case ratios, because uniform case times differ.

| Method | Setup | Projection | Refinement | Decision | Fallback | Charged total, s |
|---|---:|---:|---:|---:|---:|---:|
| Uniform | 0.00 | 0.73 | 94.79 | 1.13 | 0.00 | 96.64 |
| B2.7 conditioned 29 | 0.17 | 0.73 | 89.82 | 1.11 | 0.63 | 92.47 |
| B2.7 conditioned 43 | 0.05 | 0.70 | 146.02 | 0.77 | 56.92 | 204.46 |
| B2.9 vector 17 | 0.31 | 0.75 | 97.54 | 1.18 | 0.65 | 100.42 |
| B2.9 vector 29 | 0.05 | 0.77 | 82.54 | 1.09 | 0.00 | 84.45 |
| B2.9 vector 43 | 0.04 | 0.69 | 86.06 | 1.11 | 0.00 | 87.90 |
| Exact own-trajectory oracle | 0.00 | 0.67 | 66.99 | 1.21 | 0.00 | 68.87 |

This screen supports a specific remaining gap: accepted large-y starts,
especially at volume 0.5625, can still take more solver updates than
uniform. It does not isolate whether the update-30 MSE target, checkpoint
selection objective, or model prediction geometry causes that gap.

## Independent audit, decision, and next slice

An independent standard-library audit recomputed the plan identity,
verified B2.6/B2.7/B2.5 source index hashes, all three new checkpoint and
selection file hashes, earliest-minimum checkpoint selection, twelve unique
disjoint screen IDs and strata, all 132 ordered methods, phase-time sums,
charged paired ratios, success/fallback states, operational and accepted
quality bounds, means, resource caps, and the exact Gate. It reproduced
zero passing seeds. Local validation also passed `uv sync --dev --locked`,
Ruff, mypy, all 308 Python tests, and `git diff --check` before execution.

**B2.9 fails its development feasibility Gate.** The vector representation
is a meaningful quality and speed improvement on this fixed development
cohort, but the large-y cost gap prevents B3 registration, any stable
learned-acceleration claim, or v2 flagship delivery. The next independent
slice, **B2.10**, should freeze one quality/cost-aligned intervention aimed
at the measured large-y refinement burden, then test fresh disjoint cases
with the same full charges and fixed Gate discipline. B2.9 screen outcomes
remain exposed diagnosis only; do not train, select, or tune on them, and do
not open final evidence. Stop after this slice until separately started.
