# B2.6 intermediate-trajectory target and independent development screen

Date: 2026-09-26 (America/New_York)

Status: **B2.6 execution complete; the frozen development feasibility Gate
failed.** All 480 targets, three fits, and 96 outcomes on 12 new screen cases
were retained. No learned seed met the two-scale, fully charged speed rule.
This is development evidence, not final held-out ML evidence or a v2 delivery
claim. Uniform initialization remains the operational default.

## Frozen boundary and execution

The [B2.6 protocol](../planning/b2_6_trajectory_protocol.md) froze one change
from B2.5: the training target is the uniform solver's post-update-30 **design
density**, or its earlier converged terminal state. The 11,281-parameter CNN,
ten-channel input, optimizer, three seeds, shape-bucketed batch schedule,
projection, 240-update physical-plateau solver, independent quality rule, and
fresh uniform fallback stayed fixed. The read-only plan version is
`topolab.b2_6.trajectory.v1`, canonical SHA-256
`e783f4b8e74b08b1855ea62b9c69dcee9fc812e38786561d93c25ef38fa9a8d8`;
the plan file SHA-256 is
`2ae29458b3a595f48f6fce8519525c5c7ae84770bf96c3e7fe0e052555c211aa`.
The clean tracked execution revision was
`247f5027ef5d728d30211fdc414fbfff0450f638`.

The 468 training cases came only from B2.4 training **definitions**. Twelve
new physical cases, disjoint from that cohort and M2, supplied checkpoint
selection targets. A separate 12-case physical cohort at a different load
point was fixed for the screen before target capture. The screen never selected
checkpoints, seeds, epochs, or thresholds. No B2.4 validation label, M2
test/OOD label or outcome, or M3 final evidence was opened. The B2.4 index
SHA-256 was
`dad9109aca6d4e14a851c266fd1b8a490885cf2565281ee85ceba1d164f59244`;
the fixed B2.5 fit index SHA-256 was
`a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53`.

The run used Apple arm64, macOS 26.5, Python 3.12.10, NumPy 2.5.3, SciPy
1.18.1, PyTorch 2.14.0, and safetensors 0.8.0. The locked `uv.lock` SHA-256
was `9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.
PyTorch intra-op and BLAS/OMP/VECLIB/MKL/BLIS threads were set to one;
PyTorch reported eight inter-op threads. Generated artifacts and summaries
stayed outside Git under `/tmp/topolab-b26` and `/tmp`.

## Target capture and three fixed fits

All **480/480** target artifacts were generated and independently audited:
468 train plus 12 checkpoint-selection cases. Of these, 447 reached update 30;
33 converged earlier at updates 14, 20, or 22–29. The maximum persisted
filtered-physical-volume error was `1.054e-8`, below the fixed `0.005` bound.
The target index SHA-256 is
`5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`.
Capture took **376.86 s** under its 7,200 s cap and peaked at
**331,923,456 bytes** under its 2 GiB cap.

Each seed used the frozen 468 training cases and 12 selection cases with
elementwise trajectory-target MSE. The strict earliest selection minimum and
patience rule gave:

| Seed | Trained epochs | Selected epoch | Selection MSE | Fit seconds |
|---:|---:|---:|---:|---:|
| 17 | 38 | 13 | 0.145938 | 12.77 |
| 29 | 27 | 2 | 0.149085 | 7.62 |
| 43 | 29 | 4 | 0.145619 | 8.70 |

The fit index SHA-256 is
`9ed71fa5929b12cd731a77a0a17a32d81b1cc933f9accd6e501222f018d1e062`.
The complete three-fit stage took **36.09 s** under its 7,200 s cap and
peaked at **380,534,784 bytes** under its 2 GiB cap. All checkpoints and
selection histories were checksum-addressed, re-read, and kept outside Git.
The selected checkpoint SHA-256 values for seeds 17, 29, and 43 respectively
are `ee73ee398f719b481c836d65196fd6553f19a4831ca6e2a8e270d1f27cd35fed`,
`a68ffe75f41dfa6358a05f8cc4ed7b283a64e950ac169d3e1015cad3703150c1`,
and `9aef970fe8033cdfed5a14e241360b257b4837bcc5f5d803adff7f679385598e`.

## Complete screen and Gate

All **12/12** screen cases and **96/96** method outcomes completed: six small,
six large, one case for each scale/direction/volume combination at volume
fractions `0.225`, `0.375`, and `0.525`. Each case had fresh uniform, physics
heuristic, B2.4 training-only nearest neighbor, historical B2.5 control 43,
three new trajectory seeds, and an impossible exact own-trajectory oracle.
The following arithmetic means use every case at each mesh scale, including
the complete attempted cost and fresh uniform fallback on a failed candidate.

| Method | Small mean ratio | Large mean ratio | Failed / 12 | Fallbacks / 12 |
|---|---:|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 0 | 0 |
| Physics heuristic | 1.221 | 1.013 | 0 | 0 |
| Nearest neighbor | 0.825 | 2.413 | 5 | 5 |
| B2.5 control 43 | 1.154 | 1.115 | 1 | 1 |
| Trajectory 17 | 1.486 | 1.701 | 4 | 4 |
| Trajectory 29 | 1.564 | 2.642 | 7 | 7 |
| Trajectory 43 | 1.635 | 2.546 | 7 | 7 |
| Exact own-trajectory oracle, impossible | 0.490 | 0.748 | 0 | 0 |

The frozen Gate requires at least two of the three new seeds to average
`<=0.90` at **both** scales, average `<=1.0` in each scale/direction stratum,
have zero accepted quality violations, and stay within resource caps. **Zero
seeds pass**: each new seed is slower than uniform at both scales. Direction
means expose the largest gap in the `y` cases:

| Method | Small y | Small z | Large y | Large z |
|---|---:|---:|---:|---:|
| B2.5 control 43 | 1.140 | 1.167 | 0.954 | 1.276 |
| Trajectory 17 | 1.874 | 1.098 | 2.120 | 1.282 |
| Trajectory 29 | 2.332 | 0.795 | 2.615 | 2.669 |
| Trajectory 43 | 2.369 | 0.902 | 2.754 | 2.339 |
| Exact own-trajectory oracle | 0.486 | 0.495 | 0.691 | 0.805 |

The screen index SHA-256 is
`083a36a74cfa6e461d98e9ec5aeec14933ae0d7f245dc211a4ac051fa7089339`;
its summary SHA-256 is
`db82dd81ac9fa8c1590d68e2d4b655c85133955603501b99f7df5b1088b4a601`.
The screen took **1,712.67 s (28.54 min)** under its 14,400 s cap and peaked
at **420,364,288 bytes** under its 2 GiB cap. One-time model loading took
0.0081 s, training-only nearest-neighbor indexing 5.993 s for 6,877,512
stored bytes, and exact oracle-target generation 34.928 s. These one-time
and impossible-oracle costs were reported separately from deployable per-case
timing. The runner returned exit code 1 solely because the predeclared Gate
was false after it wrote every outcome and summary.

## Quality and cost diagnosis

The three new seeds had **18 failed attempts**: eight reached the 240-update
limit without convergence and ten stopped but missed the matched-uniform
compliance bound. Every failed attempt paid a full fresh uniform fallback;
none was relabeled as an accepted learned success. The historical control had
one compliance failure. The nearest neighbor had five failures. All accepted
attempts passed the independent convergence, compliance, and volume checks;
there were **zero accepted quality violations**.

| Method | Accepted / 12 | Accepted-only mean ratio | Accepted cases slower than uniform | Failed at 240 | Failed compliance after stop |
|---|---:|---:|---:|---:|---:|
| B2.5 control 43 | 11 | 1.098 | 6 | 0 | 1 |
| Trajectory 17 | 8 | 1.261 | 6 | 1 | 3 |
| Trajectory 29 | 5 | 1.239 | 3 | 4 | 3 |
| Trajectory 43 | 5 | 1.355 | 3 | 3 | 4 |

Refinement and fallback, rather than inference or projection, dominate the
observed cost. The following totals are seconds across the same 12 cases:

| Method | Setup | Projection | Refinement | Decision | Fallback | Charged total |
|---|---:|---:|---:|---:|---:|---:|
| Uniform | 0.00 | 0.68 | 129.88 | 1.13 | 0.00 | 131.69 |
| B2.5 control 43 | 0.16 | 0.68 | 128.68 | 1.18 | 0.49 | 131.19 |
| Trajectory 17 | 0.03 | 0.69 | 179.24 | 0.96 | 21.22 | 202.14 |
| Trajectory 29 | 0.08 | 0.68 | 218.27 | 0.42 | 114.48 | 333.93 |
| Trajectory 43 | 0.07 | 0.68 | 227.77 | 0.65 | 99.32 | 328.48 |
| Exact own-trajectory oracle | 0.00 | 0.67 | 98.91 | 1.14 | 0.00 | 100.72 |

The charged-total ratio and the arithmetic mean of per-case ratios differ
because cases have different uniform run times; the predeclared Gate uses the
arithmetic mean of matched per-case ratios above.

The oracle starts from a screen case's true trajectory state, which cannot be
known without first solving that case. Its favorable ratio shows conditional
solver headroom, **not** a deployable model result. The early checkpoint
selection epochs, frequent new-seed quality failures, and slow accepted
refinements show that this fixed trajectory-MSE predictor has not transferred
the oracle's advantage to the new screen cases. The records do not isolate
whether representation, loss, target update, or data coverage is the dominant
cause; these remain hypotheses for a separately versioned intervention.

## Independent audit and next slice

An independent standard-library audit rechecked all 480 target artifact
checksums, shapes, finite values, iteration identities, and stored volume
bounds; all three checkpoint and selection checksums; the frozen 12 case IDs
and eight-method order; all 96 outcome identities; phase-time sums and paired
ratios; success/fallback consistency; and operational equality to fresh
uniform after each rejection. It recomputed the three new seeds' 8+10 failure
classification and found no accepted compliance or volume violation. The
runner's own independent filtered-volume audit also passed on every target.

**B2.6 fails its development feasibility Gate.** No B3 final-cohort contract
is registered and no learned acceleration or v2 delivery claim follows. The
next independent slice, **B2.7**, should pre-register one targeted repair for
the observed direction-dependent prediction/quality and refinement gap,
using fresh disjoint development cases and full fallback-inclusive costs.
It must preserve this negative result and cannot tune on the exposed B2.6
screen. Development work stops here until that slice is separately started.
