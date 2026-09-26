# B2.8 y-load basin recentering and fresh development screen

Date: 2026-09-26 (America/New_York)

Status: **B2.8 complete; the frozen development feasibility Gate failed.**
The fixed midpoint intervention changed actual y-load optimization paths but
did not reduce total learned failures or meet the two-scale, direction-wise
charged-speed bounds. All 12 new development cases and 132 outcomes were
retained. This is not final ML evidence or a v2 delivery result. Uniform
initialization remains the operational default.

## Frozen boundary, exposure, and execution

The [B2.8 protocol](../planning/b2_8_basin_protocol.md) fixed one opt-in start
correction before opening its screen: blend a B2.7 model's raw prediction and
the uniform volume-fraction field at `0.5/0.5` for a y-directed point load;
copy the raw prediction for z. The same three B2.7 checkpoints, globally
visible load encoding, density projection, 240-update physical-plateau
solver, quality checks, and fully charged fresh uniform fallback were reused.
There was no B2.8 fitting, hyperparameter search, or solver/tolerance change.
The canonical read-only plan identity is
`6b74219b8411da034e1794c2184efc84d07d9260160c6df625f73147c5c24357`;
the saved read-only plan file SHA-256 is
`e5757e2ed0684fc828937c0f41fd00ed1aa18f58d562faecee9f3ecf021609e9`.
The clean tracked execution revision was
`1ea2436c8a5ec695040eebb56a7a83036428e018`.

The unchanged three-model B2.7 fit-index SHA-256 was
`36158e03a476fdff183d8c72cf0e7143700e7bac3ccc531d7eda485ec390a631`.
Its three checkpoint/selection hashes and metadata were re-read before the
screen. The B2.5 control and B2.4 training-only nearest-neighbor artifacts
were re-audited. The new screen used volumes `0.2125, 0.3625, 0.5125`,
directions y/z, both `(12,6,3)` and `(24,12,6)` meshes, and a new small-mesh
point-load node `(x=max,y=3,z=2)` with its matched doubled large-mesh node.
Every scale/direction/volume stratum occurred once. All 12 case IDs were
disjoint from B2.6/B2.7 fitting, selection, and screen cases; the volumes
were absent from the B2.4/M2 and design-exposed M3 v1 catalogs. No M2
test/OOD label/outcome or M3 final label/outcome was opened.

The run used Apple arm64, macOS 26.5, Python 3.12.10, NumPy 2.5.3, SciPy
1.18.1, PyTorch 2.14.0, and safetensors 0.8.0. PyTorch intra-op and
BLAS/OMP/VECLIB/MKL/BLIS threads were one; PyTorch reported eight inter-op
threads. `uv.lock` SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.
The B2.6 target capture cost of 376.86 s and B2.7 three-fit cost of 75.45 s
are historical offline costs, separate from this no-fit screen. All generated
case outcomes and summaries remained outside Git under `/tmp/topolab-b28`.

## Complete screen and Gate

Every case produced all eleven frozen methods: fresh uniform, physics
heuristic, training-only nearest neighbor, B2.5 control seed 43, three
unchanged B2.7 models, three B2.8 midpoint starts, and an impossible exact
own-trajectory oracle. The following values are arithmetic means of six
fully charged paired per-case time ratios per scale.

| Method | Small mean ratio | Large mean ratio | Failed / 12 | Fallbacks / 12 |
|---|---:|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 0 | 0 |
| Physics heuristic | 1.082 | 1.032 | 0 | 0 |
| Nearest neighbor | 0.859 | 2.997 | 5 | 5 |
| B2.5 control 43 | 2.217 | 1.490 | 1 | 1 |
| B2.7 conditioned 17 | 1.700 | 1.997 | 2 | 2 |
| B2.7 conditioned 29 | 1.518 | 1.895 | 3 | 3 |
| B2.7 conditioned 43 | 1.537 | 2.073 | 4 | 4 |
| B2.8 recentered 17 | 1.815 | 1.941 | 2 | 2 |
| B2.8 recentered 29 | 1.501 | 1.891 | 3 | 3 |
| B2.8 recentered 43 | 1.550 | 1.620 | 4 | 4 |
| Exact own-trajectory oracle, impossible | 0.290 | 0.630 | 0 | 0 |

The frozen Gate requires at least **two of three B2.8 seeds** with a charged
mean `<=0.90` on each scale and `<=1.0` in every scale/direction stratum,
zero accepted quality violations, all 132 outcomes, and the resource caps.
**Zero seeds pass.** The unchanged B2.7 controls on these same new cases
also fail; the comparison shows the correction's effect without selecting a
different case cohort. The y/z breakdown is:

| Seed | Method | Small y | Small z | Large y | Large z |
|---:|---|---:|---:|---:|---:|
| 17 | B2.7 | 1.019 | 2.380 | 0.961 | 3.034 |
| 17 | B2.8 | 1.105 | 2.524 | 0.865 | 3.018 |
| 29 | B2.7 | 1.053 | 1.983 | 0.798 | 2.993 |
| 29 | B2.8 | 0.961 | 2.041 | 0.815 | 2.967 |
| 43 | B2.7 | 1.096 | 1.979 | 2.853 | 1.294 |
| 43 | B2.8 | 1.122 | 1.978 | 1.942 | 1.298 |

The per-case ratios below retain every learned seed and the impossible
oracle; `*` denotes a failed attempt that paid a full fresh uniform fallback.
All baseline rows and complete phase/quality data are in the external
checksum-addressed index.

| Scale | Direction | Volume | Old 17 | Old 29 | Old 43 | B2.8 17 | B2.8 29 | B2.8 43 | Oracle |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| small | y | 0.3625 | 0.48 | 0.41 | 0.49 | 0.59 | 0.50 | 0.61 | 0.21 |
| large | y | 0.3625 | 0.73 | 0.62 | 2.84* | 0.74 | 0.67 | 1.93* | 0.76 |
| small | y | 0.2125 | 0.69 | 1.56* | 1.72* | 1.78* | 1.65* | 1.71* | 0.18 |
| large | z | 0.2125 | 3.55 | 3.50 | 2.45 | 3.50 | 3.46 | 2.50 | 0.38 |
| large | y | 0.2125 | 0.95 | 0.80 | 3.77* | 0.84 | 0.81 | 2.65* | 0.67 |
| small | y | 0.5125 | 1.89* | 1.19 | 1.09 | 0.95 | 0.73 | 1.04 | 0.44 |
| large | z | 0.5125 | 3.78* | 3.79* | 0.72 | 3.75* | 3.77* | 0.70 | 0.64 |
| small | z | 0.2125 | 2.44 | 2.24 | 2.93* | 2.66 | 2.44 | 2.98* | 0.18 |
| small | z | 0.3625 | 0.71 | 1.02 | 1.25 | 0.78 | 1.12 | 1.22 | 0.50 |
| large | z | 0.3625 | 1.77 | 1.69* | 0.71 | 1.81 | 1.68* | 0.70 |
| small | z | 0.5125 | 3.98 | 2.69 | 1.75 | 4.14 | 2.57 | 1.73 | 0.23 |
| large | y | 0.5125 | 1.20 | 0.97 | 1.95 | 1.02 | 0.97 | 1.24 | 0.63 |

The screen-index SHA-256 is
`5a6b2dfaab58c6d1535112b84439b7b79807abefc74457916ea36e07f95891d6`;
summary-file SHA-256 is
`a5209e3d0a1dba6967278af1fac69e46b023a6d8cac9dbe8e2885a8bcf37026b`.
The full screen took **1,676.57 s (27.94 min)** under 14,400 s and peaked at
**344,588,288 bytes** under 2 GiB. One-time model loading took 0.030 s,
training-only nearest-neighbor indexing 6.348 s for 6,877,512 bytes, and
nondeployable oracle target generation 35.225 s. These costs are reported
separately from deployable query charges. The runner exited with code 1 only
because the complete frozen Gate was false.

## Failure, basin, and phase-cost diagnosis

The three B2.8 seeds each had exactly as many failures as their B2.7 control
on the same cases: **2, 3, and 4**, for nine failed attempts and nine fully
charged fresh fallbacks. B2.8 had two nonconvergent-at-240 attempts and seven
stopped but failed compliance. All 132 operational outcomes passed the matched
independent quality and physical-volume checks; there were **zero accepted
quality violations**. The midpoint changed several y trajectories but was
not a reliable basin correction. At small `y/0.2125`, seed 17 changed from an
accepted `0.69` ratio to a rejected `1.78`; at small `y/0.5125`, it changed
from rejected `1.89` to accepted `0.95`. Seed 43 improved some large-y
refinement times but remained slow or failed. This is a mixed effect, not a
monotone quality repair.

For every one of the **18 z model pairs**, the original and B2.8 candidate
iterations, final numerical metrics, success status, and failure code were
identical. Their minor time-ratio differences are repeated timing variation;
the B2.8 rule intentionally did not change their numerical starts. The new z
cases therefore reveal a separate generalization/cost gap: for example,
large `z/0.2125` took about 2.5–3.5 times uniform for all three learned
starts, while the true-trajectory oracle averaged 0.290 small and 0.630
large over the whole cohort. This is conditional headroom, not deployable
acceleration. The screen does not isolate whether target, model capacity,
training coverage, or selection objective caused the z gap.

The following are actual phase-time sums in seconds across all 12 cases.
They should not be interpreted as the Gate's arithmetic mean of matched
per-case ratios because the uniform case times differ.

| Method | Setup | Projection | Refinement | Decision | Fallback | Charged total |
|---|---:|---:|---:|---:|---:|---:|
| Uniform | 0.00 | 0.69 | 91.85 | 1.14 | 0.00 | 93.69 |
| B2.7 conditioned 17 | 0.10 | 0.70 | 149.59 | 0.94 | 15.08 | 166.41 |
| B2.7 conditioned 29 | 0.10 | 0.67 | 122.78 | 0.98 | 31.85 | 156.39 |
| B2.7 conditioned 43 | 0.15 | 0.68 | 154.75 | 1.01 | 38.70 | 195.29 |
| B2.8 recentered 17 | 0.27 | 0.71 | 145.06 | 0.93 | 15.07 | 162.05 |
| B2.8 recentered 29 | 0.19 | 0.69 | 122.88 | 0.94 | 31.71 | 156.39 |
| B2.8 recentered 43 | 0.07 | 0.68 | 106.56 | 1.12 | 39.21 | 147.64 |
| Exact own-trajectory oracle | 0.00 | 0.68 | 59.29 | 1.09 | 0.00 | 61.05 |

## Independent audit, decision, and next slice

An independent standard-library audit rechecked the frozen plan hash,
complete B2.7 fit index and three checkpoint/selection file hashes, 12 unique
screen IDs and strata, all 132 method identities and ordering, phase-time
sums, paired ratios, success/fallback status, operational compliance and
physical volume, per-scale and direction means, resource bounds, and exact
Gate rule. It reproduced the 2/3/4 new-seed failures, all nine fallback
charges, and the failed Gate. A separate numerical comparison confirmed
identical candidate metrics and decisions for all 18 z control/new pairs.

**B2.8 fails its development feasibility Gate.** The fixed y midpoint is an
implemented and fully tested intervention, but its mixed y effect and the
untouched z transfer gap do not justify B3 final-cohort registration,
learned-acceleration claims, or v2 flagship delivery. The next independent
slice, **B2.9**, should freeze and execute one learning-side correction aimed
at quality and load-position transfer, then use fresh disjoint development
cases and complete charges. Do not tune a new version on these exposed B2.8
screen outcomes or open final evidence. Stop after this slice until it is
separately started.
