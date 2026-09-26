# B2.5 fixed two-arm development prototype and full validation screen

Date: 2026-09-25 (America/New_York)

Status: **six-fit execution and 54-case development screen completed; the B2.5
learned-prototype Gate failed.** No tested arm or seed achieved the frozen
fallback-inclusive `<=0.90` mean time ratio at either mesh scale. This is
development evidence, not a final held-out ML result or a v2 delivery claim.

## Frozen boundary and execution

The [B2.5 protocol](../planning/b2_5_prototype_protocol.md) fixed the two
11,281-parameter M1 CNN arms, three paired seeds, batch schedule, objective,
selection rule, all 54 exposed validation cases, nine methods per case, quality
rule, full fallback charge, and resource limits before fitting. Its canonical
plan SHA-256 is
`03978254d4cba90113a83813109e0415201885e66c28c1b7cc7bf9e5b392c5ff`.
The B2.4 522-label index SHA-256 is
`dad9109aca6d4e14a851c266fd1b8a490885cf2565281ee85ceba1d164f59244`;
its source revision is `7f4d0f6a1512b5be8f6ea192430608108bafe2cc`.
The execution source was clean tracked revision
`73b9ba163d08fb53a9c72bf9692ca4ea2542b265`. No test/OOD label,
outcome, or new final case was opened.

The run used Apple arm64, macOS 26.5, Python 3.12.10, NumPy 2.5.3, SciPy
1.18.1, PyTorch 2.14.0, and safetensors 0.8.0. `uv.lock` SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.
PyTorch intra-op threads and OpenBLAS/OMP/VECLIB/MKL/BLIS threads were set to
one; the runtime recorded eight PyTorch inter-op threads. Data, weights,
selections, per-case outcomes, and summaries stayed outside Git under
`/tmp/topolab-b24-labels`, `/tmp/topolab-b25`, and `/tmp`.

## Six matched fits

Each arm used 468 train and 54 validation cases with the same model and
seed-specific exposure order. `Control` minimized unweighted design MSE;
`candidate` minimized the audited sensitivity-weighted design MSE. The
validation objectives differ and must not be interpreted as a direct speed
comparison.

| Arm | Seed | Trained epochs | Selected epoch | Own validation objective | Fit seconds |
|---|---:|---:|---:|---:|---:|
| Control | 17 | 102 | 77 | 0.170744 | 33.66 |
| Control | 29 | 79 | 54 | 0.170815 | 24.89 |
| Control | 43 | 175 | 150 | 0.169077 | 56.99 |
| Candidate | 17 | 110 | 85 | 0.139688 | 34.46 |
| Candidate | 29 | 168 | 143 | 0.135285 | 52.36 |
| Candidate | 43 | 89 | 64 | 0.138016 | 28.40 |

The six-fit stage, including data loading and checkpoint verification, took
**239.30 s** against its 14,400 s cap and peaked at **371,998,720 bytes**
(354.8 MiB) against its 2 GiB cap. All six selected checkpoints and complete
epoch histories were checksum-addressed and re-read. The fit index SHA-256 is
`a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53`;
the fit summary SHA-256 is
`c82cba3b91a07ea0fe99566f0778275bb6764d14993c3c189cc8f3f32189bb30`.

## Complete version-matched screen and Gate

All **54/54** validation cases produced **486/486** method outcomes: 36 small
and 18 large, balanced by `y/z` direction. Every case used a fresh optimized
budget-240 uniform reference, the physics heuristic, the training-only nearest
neighbor, and all six selected models. The table gives the arithmetic mean of
per-case, fully charged time ratios to each matched uniform reference. A failed
candidate remains a failure even when a fresh uniform fallback succeeds.

| Method | Small mean | Large mean | Failed / 54 | Fallbacks / 54 |
|---|---:|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 0 | 0 |
| Physics heuristic | 1.112 | 1.033 | 0 | 0 |
| Nearest neighbor | 1.172 | 2.960 | 19 | 19 |
| Control 17 | 1.475 | 1.603 | 6 | 6 |
| Control 29 | 1.358 | 1.341 | 6 | 6 |
| Control 43 | 1.289 | 1.336 | 2 | 2 |
| Candidate 17 | 1.548 | 1.929 | 10 | 10 |
| Candidate 29 | 1.342 | 1.958 | 7 | 7 |
| Candidate 43 | 1.490 | 1.825 | 9 | 9 |

No arm has even one passing seed; the frozen Gate requires at least two of
three seeds in one arm at **both** scales with means `<=0.90`, direction means
`<=1.0`, and zero accepted quality failures. Every learned seed also exceeds
`1.0` in all four scale/direction mean strata:

| Method | Small y | Small z | Large y | Large z |
|---|---:|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 1.000 | 1.000 |
| Physics heuristic | 1.160 | 1.065 | 1.046 | 1.021 |
| Nearest neighbor | 1.459 | 0.885 | 2.998 | 2.921 |
| Control 17 | 1.167 | 1.782 | 1.642 | 1.564 |
| Control 29 | 1.170 | 1.546 | 1.275 | 1.407 |
| Control 43 | 1.049 | 1.529 | 1.347 | 1.325 |
| Candidate 17 | 1.523 | 1.573 | 1.899 | 1.959 |
| Candidate 29 | 1.271 | 1.414 | 1.922 | 1.994 |
| Candidate 43 | 1.281 | 1.699 | 1.506 | 2.143 |

The screen took **4,235.76 s (70.60 min)** against its separate 14,400 s cap
and peaked at **342,065,152 bytes (326.2 MiB)** against 2 GiB. One-time model
loading took 0.0023 s and training-only nearest-neighbor indexing took 6.6176 s
for 6,877,512 stored bytes; these are reported separately from per-query
timing. The atomic case index SHA-256 is
`cd335b6d1a2545007287c7038a5cfca9c2ae896026237f1cb68a02493b32a76d`;
the summary SHA-256 is
`c26264f5782999b96c32ba92307e8c1d2d611517d9aefd59a5c99e39ecd38c52`.

## Failure mechanism and phase costs

All 40 learned failed attempts were classified as quality-check failures and
paid a complete fresh uniform fallback. Of these, **18** reached the
240-update limit without convergence (control 5; candidate 13); the other
**22** stopped but exceeded the `1.001 ×` matched-uniform compliance bound
(control 9; candidate 13). None was a volume failure. The nearest-neighbor
baseline had 19 failures: 10 at the iteration limit and 9 at the compliance
bound. All accepted attempts met the frozen convergence, volume, and
independent compliance checks; there were **zero accepted quality failures**.

| Method | Failed small y | Failed small z | Failed large y | Failed large z |
|---|---:|---:|---:|---:|
| Uniform | 0 | 0 | 0 | 0 |
| Physics heuristic | 0 | 0 | 0 | 0 |
| Nearest neighbor | 5 | 2 | 6 | 6 |
| Control 17 | 1 | 1 | 2 | 2 |
| Control 29 | 2 | 1 | 2 | 1 |
| Control 43 | 1 | 0 | 1 | 0 |
| Candidate 17 | 4 | 1 | 2 | 3 |
| Candidate 29 | 2 | 0 | 2 | 3 |
| Candidate 43 | 2 | 1 | 2 | 4 |

Each failed count is also the count of full uniform fallbacks in that cell.

Failures alone do not explain the negative Gate. Among accepted starts,
23–30 of 44–52 cases per learned seed were still slower than uniform, and
accepted-only mean ratios ranged from 1.234 to 1.316. The actual refinement
solve, not model inference or projection, dominates time. The sensitivity-
weighted candidate has a lower value of its *own* validation objective, but
more failures and larger charged ratios than the unweighted control. This is
evidence that the present final-design weighting does not align sufficiently
with solver convergence, quality, and speed on this development workload.

The following values are **total seconds across 54 cases**, including failed
attempts and their complete fresh fallback. `Setup` includes method query or
inference; `decision` includes the independent quality check.

| Method | Setup | Projection | Refinement | Decision | Fallback | Charged total |
|---|---:|---:|---:|---:|---:|---:|
| Uniform | 0.00 | 2.16 | 286.74 | 3.54 | 0.00 | 292.44 |
| Physics heuristic | 3.42 | 2.30 | 293.79 | 3.60 | 0.00 | 303.11 |
| Nearest neighbor | 0.32 | 2.13 | 623.01 | 1.79 | 182.32 | 809.57 |
| Control 17 | 0.79 | 2.15 | 378.44 | 3.04 | 59.08 | 443.50 |
| Control 29 | 0.19 | 2.13 | 324.51 | 3.39 | 47.76 | 377.98 |
| Control 43 | 0.20 | 2.13 | 349.28 | 3.72 | 16.81 | 372.14 |
| Candidate 17 | 0.15 | 2.14 | 467.33 | 2.91 | 77.62 | 550.14 |
| Candidate 29 | 0.25 | 2.10 | 473.88 | 2.68 | 75.96 | 554.88 |
| Candidate 43 | 0.25 | 2.13 | 415.81 | 2.83 | 103.04 | 524.07 |

The complete volume-stratum means, including all seeds and fixed non-ML
baselines, follow below. Columns are target volume fractions. Each small
scale/direction/volume cell averages two cases; each large cell has one case.
These exposed development cells are diagnostic, not candidate cohorts for a
post hoc acceleration claim.

| Method | Scale | Direction | .20 | .25 | .30 | .35 | .40 | .45 | .50 | .55 | .60 |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Uniform | small | y | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Uniform | small | z | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Uniform | large | y | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Uniform | large | z | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| Physics Heuristic | small | y | 1.34 | 1.08 | 1.21 | 1.17 | 1.08 | 1.36 | 1.28 | 0.97 | 0.93 |
| Physics Heuristic | small | z | 1.13 | 1.05 | 1.07 | 1.12 | 1.03 | 1.10 | 1.01 | 0.96 | 1.11 |
| Physics Heuristic | large | y | 1.02 | 1.08 | 1.06 | 1.01 | 1.05 | 1.01 | 0.96 | 0.95 | 1.28 |
| Physics Heuristic | large | z | 1.00 | 1.05 | 1.02 | 1.02 | 1.03 | 0.96 | 1.10 | 1.03 | 0.98 |
| Nearest Neighbor | small | y | 1.72 | 0.49 | 0.71 | 1.13 | 1.23 | 2.02 | 1.96 | 1.97 | 1.90 |
| Nearest Neighbor | small | z | 1.74 | 1.85 | 0.79 | 0.38 | 1.21 | 0.31 | 0.71 | 0.60 | 0.38 |
| Nearest Neighbor | large | y | 3.26 | 3.37 | 1.84 | 4.75 | 1.95 | 3.13 | 2.78 | 4.11 | 1.79 |
| Nearest Neighbor | large | z | 4.96 | 3.17 | 4.11 | 1.04 | 3.32 | 2.66 | 0.58 | 5.11 | 1.34 |
| Control 17 | small | y | 1.44 | 0.73 | 1.31 | 0.95 | 1.09 | 1.56 | 1.22 | 0.85 | 1.36 |
| Control 17 | small | z | 2.44 | 1.81 | 1.24 | 1.13 | 4.89 | 1.15 | 1.03 | 0.86 | 1.48 |
| Control 17 | large | y | 0.58 | 1.18 | 1.14 | 1.07 | 1.22 | 1.10 | 3.45 | 4.14 | 0.90 |
| Control 17 | large | z | 4.96 | 0.57 | 0.88 | 0.75 | 0.82 | 0.70 | 1.00 | 1.22 | 3.19 |
| Control 29 | small | y | 1.26 | 0.77 | 1.13 | 0.88 | 1.09 | 1.22 | 2.07 | 0.88 | 1.23 |
| Control 29 | small | z | 2.24 | 1.78 | 1.10 | 1.30 | 2.92 | 1.00 | 1.05 | 0.90 | 1.63 |
| Control 29 | large | y | 0.69 | 1.18 | 1.25 | 0.97 | 1.06 | 0.97 | 2.20 | 2.24 | 0.91 |
| Control 29 | large | z | 3.88 | 0.56 | 0.74 | 0.64 | 0.75 | 0.68 | 1.03 | 1.19 | 3.20 |
| Control 43 | small | y | 0.86 | 0.82 | 0.91 | 0.83 | 0.95 | 1.47 | 1.33 | 0.95 | 1.33 |
| Control 43 | small | z | 2.48 | 1.36 | 0.93 | 1.76 | 2.60 | 1.04 | 0.99 | 0.91 | 1.70 |
| Control 43 | large | y | 0.61 | 1.79 | 1.00 | 0.95 | 1.08 | 1.00 | 2.50 | 2.27 | 0.92 |
| Control 43 | large | z | 3.93 | 0.62 | 0.99 | 0.73 | 0.67 | 0.62 | 0.94 | 1.34 | 2.09 |
| Candidate 17 | small | y | 1.33 | 0.82 | 0.91 | 0.80 | 0.98 | 2.11 | 1.66 | 3.68 | 1.44 |
| Candidate 17 | small | z | 2.28 | 1.93 | 1.13 | 1.88 | 2.90 | 1.16 | 0.94 | 0.97 | 0.96 |
| Candidate 17 | large | y | 1.00 | 1.63 | 1.47 | 1.06 | 0.99 | 1.06 | 3.25 | 4.17 | 2.46 |
| Candidate 17 | large | z | 4.97 | 0.70 | 0.84 | 3.21 | 3.39 | 0.67 | 1.16 | 1.13 | 1.58 |
| Candidate 29 | small | y | 0.81 | 0.98 | 0.84 | 0.83 | 0.97 | 1.46 | 1.63 | 2.85 | 1.07 |
| Candidate 29 | small | z | 1.86 | 1.31 | 1.16 | 1.44 | 2.97 | 1.18 | 0.90 | 0.86 | 1.05 |
| Candidate 29 | large | y | 0.58 | 1.94 | 1.50 | 1.11 | 1.00 | 1.13 | 3.45 | 4.13 | 2.46 |
| Candidate 29 | large | z | 4.93 | 0.82 | 0.87 | 3.21 | 3.37 | 0.67 | 1.16 | 1.12 | 1.79 |
| Candidate 43 | small | y | 1.75 | 0.73 | 1.06 | 0.80 | 0.95 | 1.58 | 1.32 | 1.67 | 1.68 |
| Candidate 43 | small | z | 2.00 | 2.01 | 1.87 | 1.55 | 3.80 | 1.05 | 0.95 | 0.90 | 1.16 |
| Candidate 43 | large | y | 0.71 | 1.66 | 1.34 | 1.12 | 1.04 | 1.13 | 2.66 | 2.86 | 1.04 |
| Candidate 43 | large | z | 4.91 | 0.92 | 0.82 | 3.21 | 3.40 | 0.58 | 1.08 | 1.16 | 3.20 |

## Artifact and numerical audit

The runner re-read all 522 B2.4 label checksums and identities, then all six
selection histories and tensor checkpoints. A separate read-only audit
rechecked these artifacts and the frozen order of all 54 complete screen rows.
An independent standard-library audit verified nine methods per unique
physical case, all 486 outcome-to-case identities, method/seed order, timing phase sums,
recomputed paired ratios, success/fallback consistency, and uniform
operational equality after each failed attempt. It found no accepted
compliance or volume violation. The screen returned exit code 1 **because the
predeclared prototype Gate is false**, after writing the complete summary;
there was no execution exception or missing case.

## Decision and next slice

**B2.5 fails the development learned-prototype Gate.** The conditional oracle
headroom shown in earlier B0/B2 work remains physically possible, but this
fixed final-design CNN and sensitivity-weighted objective did not turn it into
reliable, same-quality end-to-end acceleration. No B3 final-cohort contract is
registered; no v2 ML delivery or `accelerated` claim follows.

The next independent slice should be **B2.6**, a versioned development-only
intervention aimed at the measured refinement/quality bottleneck. It should
first freeze a new evidence boundary and a specific intermediate-state or
solver-trajectory target hypothesis, then test whether that target can reduce
iterations while retaining the frozen compliance and volume checks. It must
retain complete fallback charges and a genuinely new validation boundary for
the new intervention; merely adding epochs or selecting favorable exposed
strata would not address this result. Begin B2.6 only on a new user request.

The source commit passed locked offline `uv sync --dev --locked`, Ruff,
`mypy src`, full `pytest` (**293 passed**), and Git diff checks before the
production fit. The same checks passed before the report commit, with
**293/293** tests passing again. PR checks provide the final integration gate.
