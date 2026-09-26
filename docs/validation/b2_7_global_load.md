# B2.7 global point-load conditioning and new development screen

Date: 2026-09-26 (America/New_York)

Status: **B2.7 complete; the frozen development feasibility Gate failed.**
The single input-representation intervention improved two seeds greatly against
their B2.6 counterparts on the same new cases, but no new seed met the required
two-scale and per-direction fallback-inclusive rule. This remains exposed
development evidence, not a final held-out ML or v2 delivery claim. Uniform
initialization remains the operational default.

## Frozen identity, exposure, and execution

The [B2.7 protocol](../planning/b2_7_global_load_protocol.md) changed only
the three point-load input channels: a signed, globally visible normalized
load-distance field replaces the sparse incident-element load field. The
ten-channel shape, M1 CNN and parameter count, 480 B2.6 trajectory targets,
three seeds, fitting schedule, filtered-volume projection, numerical solver,
quality rule, and charged uniform fallback were unchanged. The read-only plan
version `topolab.b2_7.global_load.v1` has canonical SHA-256
`1311405f25e20cc7214cc744bb8843bfa791af1232351c71a4c2c639af369e9d`;
the plan file SHA-256 is
`2c3819b3713d95710dbb17eb2135e7545cc762c5833df065e937b1ecbc25a2c9`.
The clean tracked execution revision was
`f7ae676582ae0545347959dbe3651edfdd34c372`.

The 468 training and 12 checkpoint-selection physical cases and their
post-update-30 target artifacts were exactly B2.6's; the complete target-index
SHA-256 was
`5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`.
The three old-model fit-index SHA-256 was
`9ed71fa5929b12cd731a77a0a17a32d81b1cc933f9accd6e501222f018d1e062`.
Before fitting and screening, the runner re-read every old target and model
artifact, identity, checksum, target shape, finite value, and independent
filtered-volume check. No B2.6 screen case was used for model selection.

The new 12-case screen was frozen before fitting: three volumes `0.2375`,
`0.3875`, `0.5375`, two `y/z` directions, two 3D mesh scales, and the new
small-mesh loaded node `(x=max,y=5,z=2)` with its physically matched doubled
large-mesh node. Every scale/direction/volume stratum occurs once. The
volumes and complete case IDs are disjoint from B2.4/M2, B2.6's train,
selection, and screen cohorts, and the design-exposed M3 v1 final catalog.
No M2 test/OOD label or outcome or M3 final label or outcome was opened.
All new checkpoints, selections, case outcomes, and summaries remained outside
Git under `/tmp/topolab-b27` and `/tmp`.

The run used Apple arm64, macOS 26.5, Python 3.12.10, NumPy 2.5.3, SciPy
1.18.1, PyTorch 2.14.0, and safetensors 0.8.0. `uv.lock` SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.
PyTorch intra-op and BLAS/OMP/VECLIB/MKL/BLIS threads were set to one;
PyTorch reported eight inter-op threads. The existing B2.6 target-generation
cost, **376.86 s** with 331,923,456 peak RSS bytes, is reported separately;
B2.7 generated no new fitting targets.

## Three fixed fits

All three seeds fit the same 468 training targets, selected checkpoints on the
same 12 targets, and used strict earliest validation-MSE minima. Compared
with B2.6's own same-target selections, the new encoding reduced seed 17/29
selection MSE, but target MSE is not the operational Gate.

| Seed | Trained epochs | Selected epoch | B2.7 selection MSE | B2.6 selection MSE | Fit seconds |
|---:|---:|---:|---:|---:|---:|
| 17 | 93 | 68 | 0.098851 | 0.145938 | 27.77 |
| 29 | 116 | 91 | 0.089376 | 0.149085 | 33.12 |
| 43 | 28 | 3 | 0.136238 | 0.145619 | 8.06 |

The complete fit index SHA-256 is
`36158e03a476fdff183d8c72cf0e7143700e7bac3ccc531d7eda485ec390a631`;
the fit summary SHA-256 is
`af5b8e9a8a5b0618b9811cc995d5ebd2ff702f0318693caa4a51453623b95409`.
The three-fit stage, including source-artifact checks, took **75.45 s** under
its 7,200 s cap and peaked at **410,714,112 bytes** under its 2 GiB cap.
Selected checkpoint SHA-256 values for seeds 17, 29, and 43 are respectively
`fcee0a6f431130ef700243c4f27fcfd9b29ba0fde0eb4310442386122b4daf14`,
`27a9ebac7415e020d0fedfc3fbfb1caf9e073ff38623e80a135d7e0a488e067b`,
and `7572c40c18ab550d1ed1b5b10690d99faa63bae83c1933a72827408244631057`.

## Complete 12-case screen and frozen Gate

Every new physical case produced all eleven predeclared methods, for **132/132
outcomes**. Each method used a fresh matched uniform reference, unchanged
240-update physical-plateau solver, projection, independent quality check,
and full fresh uniform fallback after a failed attempt. The impossible exact
own-trajectory oracle is label-informed and cannot be deployed. The table is
the arithmetic mean of the six fully charged per-case time ratios per scale.

| Method | Small mean ratio | Large mean ratio | Failed / 12 | Fallbacks / 12 |
|---|---:|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 0 | 0 |
| Physics heuristic | 1.100 | 1.052 | 0 | 0 |
| Nearest neighbor | 0.640 | 2.514 | 3 | 3 |
| B2.5 control 43 | 0.875 | 1.221 | 0 | 0 |
| B2.6 trajectory 17 | 1.712 | 1.739 | 4 | 4 |
| B2.6 trajectory 29 | 1.970 | 2.109 | 3 | 3 |
| B2.6 trajectory 43 | 2.039 | 2.099 | 6 | 6 |
| B2.7 conditioned 17 | 0.842 | 1.049 | 1 | 1 |
| B2.7 conditioned 29 | 0.933 | 0.920 | 2 | 2 |
| B2.7 conditioned 43 | 1.190 | 2.003 | 4 | 4 |
| Exact own-trajectory oracle, impossible | 0.297 | 0.648 | 0 | 0 |

The frozen Gate requires at least **two of three new seeds** with mean ratio
`<=0.90` at both scales and `<=1.0` in every scale/direction stratum, zero
accepted quality violations, all 12 cases and 132 outcomes, and fit/screen
resource caps. **Zero seeds pass.** Seed 17 passes the small-scale aggregate
but misses the large-scale bound; seed 29 narrowly misses both aggregate
bounds; seed 43 misses both by more. All three miss a `y` direction bound:

| New seed | Small y | Small z | Large y | Large z |
|---|---:|---:|---:|---:|
| 17 | 1.104 | 0.580 | 1.209 | 0.890 |
| 29 | 1.280 | 0.586 | 1.052 | 0.788 |
| 43 | 1.634 | 0.747 | 3.057 | 0.950 |

The following per-case ratios expose every new and historical trajectory seed
and the oracle. `*` means the candidate failed and paid a full uniform
fallback. Full uniform, heuristic, nearest-neighbor, and B2.5-control rows
are preserved in the checksum-addressed external index.

| Scale | Direction | Volume | Old 17 | Old 29 | Old 43 | New 17 | New 29 | New 43 | Oracle |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| large | y | 0.2375 | 2.91* | 2.89* | 2.91* | 1.02 | 0.91 | 2.54* | 0.76 |
| large | y | 0.3875 | 1.55 | 4.47* | 3.80* | 1.40 | 1.30 | 2.64 | 0.75 |
| large | y | 0.5375 | 2.62* | 1.64 | 2.45* | 1.21 | 0.95 | 3.99* | 0.63 |
| large | z | 0.2375 | 0.99 | 0.95 | 0.95 | 0.94 | 0.83 | 0.85 | 0.63 |
| large | z | 0.3875 | 1.09 | 1.33 | 1.27 | 0.97 | 0.89 | 1.10 | 0.55 |
| large | z | 0.5375 | 1.27 | 1.37 | 1.21 | 0.76 | 0.65 | 0.89 | 0.57 |
| small | y | 0.2375 | 3.17* | 3.94* | 4.23* | 2.04* | 1.76* | 2.02* | 0.21 |
| small | y | 0.3875 | 1.94 | 3.58 | 3.04* | 0.78 | 1.59* | 1.58* | 0.40 |
| small | y | 0.5375 | 2.20* | 1.75 | 2.30* | 0.49 | 0.49 | 1.30 | 0.47 |
| small | z | 0.2375 | 0.78 | 0.64 | 0.64 | 0.63 | 0.50 | 0.63 | 0.13 |
| small | z | 0.3875 | 1.24 | 0.97 | 1.09 | 0.59 | 0.56 | 0.82 | 0.22 |
| small | z | 0.5375 | 0.95 | 0.94 | 0.94 | 0.51 | 0.70 | 0.80 | 0.35 |

The screen index SHA-256 is
`f2b8ec748c40d3032df1241f688d15fa4718eded80f78abde67557a823488746`;
the summary SHA-256 is
`c4e566caa04903b91623f722d6f63779819d3473f311106864aa1ba239293ccf`.
The complete screen took **1,601.59 s (26.69 min)** under its 14,400 s cap
and peaked at **436,584,448 bytes** under its 2 GiB cap. One-time model
loading took 0.0095 s, B2.4 training-only nearest-neighbor indexing 5.839 s
for 6,877,512 stored bytes, and nondeployable oracle-target generation
37.390 s. These are separate from deployable per-query charges. The runner
returned exit code 1 only because the complete predeclared Gate was false.

## Failure and phase-cost diagnosis

The new seeds had seven failed attempts: **one** reached the 240-update
limit and **six** stopped but missed the matched-uniform compliance bound.
Seed 17 had one failure, seed 29 two, and seed 43 four; every one paid a fresh
uniform fallback and remained a failed candidate. The B2.6 old seeds had
13 failures on the same new cases. There were **zero accepted quality
violations** across all 132 outcomes. Among accepted new starts, seed 17 was
slower than uniform on 3/11, seed 29 on 1/10, and seed 43 on 3/8 cases.

The decisive residual gap is concentrated in `y`: all three new models failed
the small `y/0.2375` case, and both otherwise strongest seeds remained slower
on the large `y/0.3875` case despite passing quality. Seed 29's accepted-only
mean ratio was 0.776, but its two rejected cases made its complete small
mean 0.933, above the 0.90 Gate. The true-trajectory oracle had means 0.297
and 0.648, showing conditional headroom without a deployable prediction.
This evidence supports a narrower next hypothesis about quality and
solver-basin alignment on `y` cases; it does not prove which model or loss
change will repair it.

The following sums are actual seconds across all 12 cases. Refinement and
fallback dominate, while candidate encoding/inference is small. Aggregate
charged-total ratios need not equal the predeclared arithmetic mean of
paired per-case ratios because uniform case times vary.

| Method | Setup | Projection | Refinement | Decision | Fallback | Charged total |
|---|---:|---:|---:|---:|---:|---:|
| Uniform | 0.00 | 0.73 | 90.31 | 1.17 | 0.00 | 92.21 |
| Old trajectory 17 | 0.03 | 0.73 | 134.64 | 0.98 | 36.77 | 173.15 |
| Old trajectory 29 | 0.07 | 0.74 | 170.37 | 0.80 | 41.58 | 213.57 |
| Old trajectory 43 | 0.11 | 0.72 | 153.74 | 0.77 | 56.07 | 211.40 |
| New conditioned 17 | 0.12 | 0.75 | 95.45 | 1.15 | 0.35 | 97.83 |
| New conditioned 29 | 0.03 | 0.73 | 83.91 | 1.15 | 0.82 | 86.63 |
| New conditioned 43 | 0.03 | 0.73 | 156.95 | 1.05 | 36.81 | 195.57 |
| Exact own-trajectory oracle | 0.00 | 0.72 | 58.64 | 1.14 | 0.00 | 60.51 |

## Artifact audit, decision, and next slice

An independent standard-library audit rechecked the B2.7 plan identity,
three selected checkpoint and selection checksums, strict earliest selection
epochs, 12 unique frozen case IDs and their complete strata, all 132 method
identities and ordering, phase-time sums, recomputed paired and stratum means,
fallback/operational equality, accepted compliance and physical volume, and
the exact Gate rule. It reproduced the seven new-seed failure classifications
and found no accepted quality violation. The runner independently rechecked
all 480 B2.6 target artifacts and their filtered physical-volume bounds on
both fit and screen entry.

**B2.7 fails its development feasibility Gate.** Its improvement over B2.6
is real on these exposed development cases but cannot justify B3 final-cohort
registration, a learned-acceleration claim, or v2 flagship delivery. The next
independent slice, **B2.8**, should freeze one quality/solver-basin-aligned
intervention for the measured `y` failures and slow accepted refinements,
then screen on fresh disjoint development cases with every cost charged.
Do not select a favorable B2.7 subgroup or tune this version on its exposed
screen. Stop after this slice until the next is explicitly started.
