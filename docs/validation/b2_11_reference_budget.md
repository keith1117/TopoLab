# B2.11 versioned reference budget and fixed-model development confirmation

Date: 2026-09-27 (America/New_York)

Status: **The bounded reference repair passed; the learned-prototype
development Gate failed.** The old/new uniform sentinel passed 12/12, all
twelve fresh uniform references passed, and the new screen retained all
132/132 method outcomes. Neither unchanged three-seed model panel had a
seed meeting every frozen speed stratum. This is development evidence, not
final ML evidence or a v2 delivery result. Uniform remains the operational
default.

## Frozen numerical boundary and provenance

The [B2.11 protocol](../planning/b2_11_reference_budget_protocol.md) and
[numerical convention](../numerical_conventions.md) fixed one opt-in change
before solving: every compared case and method used `max_iterations=360`
instead of 240. The `topolab.simp.physical_plateau.v1` stopping rule, OC,
filter, stiffness, materials, loads, independent quality checks, and fallback
policy were unchanged. The cap change created new physical-case IDs; the
old 240-update B2.10 results stayed failed/immutable. No model was refitted
or reselected. The B2.9 and B2.10 fit-index SHA-256 values were
`96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`
and `0d2138bfdcfc4f9d730c6261bccc1ce8bf2ddda2f50a70f5e5e0958b5fcc1851`;
their six selections/checkpoints were checksum- and history-audited before
screening. B2.10's nine-case partial screen with SHA-256
`a5a538f580e0ab03185e6d2c58d207a85f8c33ca7c77d7c5a56c0b196df6ceae`
was exposure provenance only, never a training or selection input.

The read-only plan's canonical SHA-256 was
`8cbd77c8fdace2ef12512a6aa001e94152e2fc60b1fd9b4375d4c6f1e5af610a`;
its saved file SHA-256 was
`2723cddcaa89206bb6a0dccef5e2c3b5e507c23c157f9eab994398aa77614465`.
The clean tracked execution revision was
`71e7784986cc4497cc1ac870d17cc376e0de270a`. The twelve new screen
geometries crossed volumes `0.2975,0.4475,0.5975`, y/z load directions,
and `(12,6,3)`/`(24,12,6)` meshes, with the small-mesh point load at
`(x=max,y=3,z=2)` and a physically matched doubled node. They were disjoint
from 540 previously exposed development case IDs and from the B2.4/M2 and
design-exposed M3 v1 volume catalogs. No M2 test/OOD or M3 final label or
outcome was opened.

Execution used Apple arm64, macOS, Python 3.12.10, NumPy 2.5.3, SciPy
1.18.1, PyTorch 2.14.0, and safetensors 0.8.0. PyTorch intra-op and
BLAS/OMP/VECLIB/MKL/BLIS threads were one; PyTorch reported eight inter-op
threads. `uv.lock` SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.
All generated indices, outcomes, and logs remained outside Git.

## Old/new sentinel and fresh reference feasibility

All twelve B2.10 screen definitions were re-solved from uniform at both
the old 240 and new 360 caps. The eleven previously successful source cases
kept exactly the same stop iteration and final compliance within the frozen
relative `1e-10` guard. The former large `z/0.2875` failure remained a
failure at old update 240; its new-identity run passed at **update 282**,
with compliance `0.243903721134` and physical-volume error `2.55e-9`.
Every new result passed unchanged convergence and independent quality checks.
The complete sentinel took **303.06 s** against 1,800 s and peaked at
**440,680,448 bytes** against 2 GiB. Its index SHA-256 was
`277a8aaaa163302a4ba7b8c9de365a401cc92cc5a0f4c480afcf00eeaaa175a0`;
summary-file SHA-256 was
`a4ae80f1acd0b3f5d2301bb472143c0c92d020d8318fb0c1211a25d36a6e31b6`.

Before loading any learned model, all **12/12 fresh uniform references**
passed the same convergence, finite-compliance, and volume checks. Their
stop iterations ranged **36–189**, so none used the additional budget
beyond the old 240 limit. The independent stage took **131.81 s** against
1,800 s and peaked at **339,591,168 bytes** against 2 GiB. Its index
SHA-256 was
`a8fc2771f9f42a0f275cfce14e7b9d179ba671aa1338ec4c698a1c9001fac45c`;
summary-file SHA-256 was
`27b70459dcae01e6523d2d1b0f9fcd6e6643afe4ab22ef5bdb08d6c2880e544d`.
The screen later ran a **fresh** uniform per case for matched timing;
preflight time was not substituted as its denominator.

## Complete fixed-model screen and Gate

Each new case received eleven fixed methods: fresh uniform, physics
heuristic, B2.4 training-only nearest neighbor, B2.5 control seed 43,
three unchanged B2.9 vector models, three unchanged B2.10 weighted models,
and an impossible own-trajectory oracle. Every candidate received full
projection and refinement, independent quality re-solve, and a fresh
complete uniform fallback if rejected. The following are arithmetic means
of six fully charged paired time ratios per scale.

| Method | Small mean | Large mean | Rejected / 12 |
|---|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 0 |
| Physics heuristic | 1.133 | 1.022 | 0 |
| Nearest neighbor | 0.142 | 2.903 | 3 |
| B2.5 control 43 | 1.326 | 1.117 | 0 |
| B2.9 vector 17 | 1.051 | 0.872 | 1 |
| B2.9 vector 29 | 1.085 | 0.994 | 1 |
| B2.9 vector 43 | 0.955 | 0.914 | 1 |
| B2.10 weighted 17 | 1.154 | 1.228 | 2 |
| B2.10 weighted 29 | 1.235 | 0.983 | 2 |
| B2.10 weighted 43 | 0.921 | 0.918 | 1 |
| Exact own-trajectory oracle, impossible | 0.411 | 0.735 | 0 |

The frozen development Gate requires **at least two seeds within one
predeclared panel**, each with both scale means `<=0.90` and all four
scale/direction means `<=1.0`, plus zero accepted quality violations, all
12 cases/132 outcomes, and all resource caps. Favorable seeds cannot be
mixed across the two panels. **Neither panel had even one fully passing
seed.** Direction-wise means for the six fixed learned models were:

| Method | Small y | Small z | Large y | Large z |
|---|---:|---:|---:|---:|
| Vector 17 | 0.821 | 1.281 | 1.100 | 0.645 |
| Vector 29 | 1.035 | 1.136 | 1.236 | 0.751 |
| Vector 43 | 0.894 | 1.016 | 1.253 | 0.576 |
| Weighted 17 | 1.268 | 1.041 | 1.341 | 1.115 |
| Weighted 29 | 1.141 | 1.328 | 1.235 | 0.732 |
| Weighted 43 | 0.813 | 1.028 | 1.125 | 0.712 |

Per-case ratios show the six models and the nondeployable oracle. `*`
means the candidate was rejected and paid a complete fresh uniform
fallback. The external index retains every baseline, numerical metric,
failure code, and phase time.

| Scale | Direction | Volume | Vector 17 | Vector 29 | Vector 43 | Weighted 17 | Weighted 29 | Weighted 43 | Oracle |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| small | z | 0.5975 | 1.385 | 1.108 | 0.833 | 0.867 | 1.568 | 0.748 | 0.620 |
| small | y | 0.4475 | 1.179 | 0.960 | 1.232 | 1.150 | 1.473* | 1.097 | 0.605 |
| large | y | 0.5975 | 1.667* | 1.629* | 1.556* | 1.932* | 1.799* | 1.783* | 0.785 |
| large | z | 0.4475 | 0.339 | 0.499 | 0.343 | 0.654 | 0.725 | 0.314 | 0.813 |
| small | y | 0.2975 | 0.752 | 0.916 | 0.820 | 1.692* | 0.963 | 0.747 | 0.256 |
| large | y | 0.2975 | 0.921 | 1.348 | 1.424 | 1.316 | 1.101 | 0.977 | 0.651 |
| small | z | 0.2975 | 1.990 | 1.806 | 1.755 | 1.760 | 1.657 | 1.735 | 0.343 |
| large | y | 0.4475 | 0.712 | 0.731 | 0.778 | 0.774 | 0.804 | 0.614 | 0.749 |
| large | z | 0.5975 | 0.723 | 0.985 | 0.669 | 1.926 | 0.591 | 0.555 | 0.731 |
| large | z | 0.2975 | 0.871 | 0.769 | 0.716 | 0.767 | 0.879 | 1.266 | 0.683 |
| small | y | 0.5975 | 0.533 | 1.230 | 0.631 | 0.962 | 0.989 | 0.596 | 0.431 |
| small | z | 0.4475 | 0.467 | 0.493 | 0.462 | 0.495 | 0.759 | 0.601 | 0.210 |

All **132 operational outcomes** met physical-volume error `<=0.005`
and final compliance `<=1.001` times matched uniform. There were zero
accepted quality violations. Eight learned attempts were rejected and
paid full fallbacks: one per vector seed and two/two/one for weighted
seeds 17/29/43. Nearest neighbor had three more rejected attempts. The
screen index SHA-256 was
`7c8aca732e3cc4d3c410158ab3f92c1945420e1854211c35bee0271bef113d8d`;
screen-summary file SHA-256 was
`fd999a34c2ee2c90bc1ecfb8abc1ac7551ab0c99ed0f92b230649f4ee5a83047`.
The complete screen took **1,600.70 s** against 14,400 s and peaked at
**344,080,384 bytes** against 2 GiB. One-time model loading took 0.034 s;
training-only neighbor indexing took 6.127 s and 6,877,512 bytes.
Nondeployable oracle target generation took 35.183 s separately.

Actual phase sums over twelve cases are below. They are not the Gate's
mean of paired per-case ratios because uniform case durations differ.

| Method | Setup | Projection | Refinement | Decision | Fallback | Charged total, s |
|---|---:|---:|---:|---:|---:|---:|
| Uniform | 0.00 | 0.72 | 128.25 | 1.14 | 0.00 | 130.11 |
| Vector 17 | 0.04 | 0.70 | 84.15 | 1.12 | 22.70 | 108.70 |
| Vector 29 | 0.03 | 0.67 | 98.95 | 1.14 | 22.68 | 123.47 |
| Vector 43 | 0.03 | 0.69 | 87.22 | 1.11 | 22.52 | 111.57 |
| Weighted 17 | 0.03 | 0.67 | 128.52 | 1.14 | 22.92 | 153.28 |
| Weighted 29 | 0.06 | 0.68 | 102.65 | 1.12 | 23.36 | 127.87 |
| Weighted 43 | 0.03 | 0.67 | 87.78 | 1.13 | 22.53 | 112.14 |
| Exact own-trajectory oracle | 0.00 | 0.68 | 94.75 | 1.16 | 0.00 | 96.59 |

## Diagnosed learning-side gap and next slice

At large `y/0.5975`, uniform converged in 126 updates with compliance
`0.026631439381`. All six learned starts converged in **68–117** updates,
but their final compliances were **1.00546–1.00626 times** uniform,
exceeding the frozen `1.001` bound. All six thus failed quality and paid
roughly 22.5 s each for fresh fallback. This is a solution-basin gap, not
insufficient iteration budget. At small `z/0.2975`, all six learned starts
passed quality but took **83–102** updates versus uniform's 44, yielding
fully charged ratios **1.657–1.990**. The oracle ratios at those cases were
0.785 and 0.343, respectively; conditional trajectory headroom remains.
Increasing the uniform budget alone did not repair either learned failure
mode. All fresh uniform references stopped before the old 240 cap, so the
negative result is not driven by an artificially slower new denominator.

An independent standard-library audit recomputed the canonical plan,
source-index hashes, all six unchanged selection/checkpoint hashes and
earliest minima, twelve old/new sentinel identities and regression guards,
twelve new reference identities/quality results, twelve unique disjoint
screen strata, all 132 ordered outcomes, phase sums, charged ratios,
fallback states, means, caps, and the two separate panel Gates. It
reproduced zero passing seeds. Local repository checks passed before
execution. The runner exited with code 1 solely because the fully retained
screen failed its fixed learned-prototype Gate.

**B2.11 repairs reference feasibility but fails learned-prototype
feasibility.** The next independent slice, **B2.12**, should freeze one
learning-side intervention aimed at the measured high-volume y compliance
basin and low-volume z refinement burden, with a new disjoint development
screen and the same full quality/cost accounting. It should not merely
increase the iteration cap or training epochs, select a favorable exposed
subgroup, or enter B3. No stable acceleration or v2 flagship delivery
claim is justified. Stop after this slice until separately started.

## Repository validation

Before the clean-revision numerical run, `uv sync --dev --locked`, Ruff,
mypy on `src`, all **313 Python tests**, and `git diff --check` passed.
The B2.11 runner also passed a focused mypy check. The same required
repository Gate was repeated before committing this report; generated
indices, model files, and diagnostic logs were not committed.
