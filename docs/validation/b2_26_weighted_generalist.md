# B2.26 y-weighted terminal generalist and fresh screen

Date: 2026-09-29 (America/New_York)

Status: **the frozen B2.26 development Gate failed.** All mandatory
stages completed: 24/24 fresh uniform references, three fixed weighted
fits, and 240/240 fully charged matched outcomes. No weighted seed met
the large-scale mean `<=0.90`; zero seeds passed the complete Gate.
Uniform initialization remains the operational default. B3 and final
evidence remain closed.

## Frozen intervention and exposure

The [B2.26 protocol](../planning/b2_26_weighted_generalist_protocol.md)
changed only the B2.21 terminal-target generalist's training-case
weights: `8` for its 78 existing y-direction train cases at volume
`>=0.5`, `1` for the remaining 390. It retained the 468/12 train and
validation population, terminal-design target, 13-channel input,
26,433-parameter context CNN, AdamW, seeds, and earliest minimum
unweighted validation MSE selection. The B2.24 expanded high-volume
large-y specialist was fixed and shared by the operational, unweighted
terminal, and new weighted generalist panels. All three panels paid
route, encoding, inference, filtered-volume projection, full 360-update
physical-plateau refinement, terminal quality decision, and complete
fresh uniform fallback on failure.

The canonical plan SHA-256 was
`bd6b355036024c2bbd31b09a62d4141d868afae526025f4e395c2abe97440a4c`.
The read-only plan and all stages ran from clean merged source revision
`6ac6fdbc6d7396c48536dc75c16c44ceffe57fef` with one CPU/BLAS
thread. The exposure ledger blocked 814 prior exposed or reserved
physical case IDs. The 24 new cases used three unused volumes, two
load positions, both mesh scales and y/z directions; each stratum had
six cases and exactly two large/high-volume/y cases invoked the fixed
specialist. No M2 held-out/OOD or final case was opened.

## Complete stages and artifact audit

| Stage | Complete evidence | Elapsed | Peak RSS | Frozen limit | Result |
|---|---:|---:|---:|---|---|
| Uniform references | 24/24 | 214.074 s | 390,496,256 B | 3,600 s; <=2 GiB | Pass |
| Weighted fits | 3/3 | 309.322 s | 338,444,288 B | 7,200 s; <=2 GiB | Pass |
| Matched screen | 24 cases; 240 outcomes | 2,015.643 s | 328,450,048 B | 24,000 s; <=2 GiB | Complete; Gate failed |

All 24 references converged, had positive finite compliance, and
passed the independent final-quality and physical-volume checks. The
weighted fits selected epochs `193,141,89` for seeds `17,29,43`.
There were zero accepted quality violations. All 16 failed learned
attempts retained failure status and paid a complete fresh uniform
fallback. The three stage-index SHA-256 values were:

```text
reference c77ecdbd1e41e733794c197ecf7198306e0922885dba01e2fc229f9f4458fb63
fit       02b95a940de87cc8e9e5d8d297b619b461425bece0ca933a588b9072ce8a5c8e
screen    05fa1f1e825060b144db0cbab728dfe98e3785594fce42ff7aad85e26813307a
```

A separate external audit verified source/plan binding, all ordered
case identities, reference quality, checkpoint and history byte hashes,
earliest minimum-MSE selection, all 240 routes and outcomes, phase sums,
paired uniform denominators, accepted quality, complete fallback
charges, resource limits, and the frozen Gate arithmetic. It
reproduced zero passing seeds and the failed decision. Generated
labels, weights, histories, outcomes, logs, and audit code remain
outside Git.

## Matched quality and speed

Each paired ratio is end-to-end time divided by that case's optimized
uniform reference, including every charge. The scale and direction
means are arithmetic means of those per-case ratios.

| Seed | Operational small / large | Unweighted terminal small / large | Weighted small / large | Weighted large-y / large-z | Failures: operational / terminal / weighted |
|---:|---:|---:|---:|---:|---:|
| 17 | 0.782 / 1.009 | 0.591 / 1.124 | 0.407 / 0.960 | 0.944 / 0.977 | 2 / 2 / 1 |
| 29 | 0.605 / 0.975 | 0.638 / 0.915 | 0.579 / 1.176 | 0.953 / 1.400 | 2 / 1 / 2 |
| 43 | 0.552 / 0.940 | 0.537 / 1.222 | 0.582 / 1.045 | 1.114 / 0.977 | 1 / 2 / 3 |

All weighted small-scale means met `<=0.90`. Seed 17 improved on both
matched controls in total failures and had both large direction means
`<=1.0`, but its large-scale mean was `0.960`, still `0.060` above the
frozen limit. Seed 29's large-z mean was `1.400`: its six large-z
candidates averaged 130 updates and 25.06 s refinement, versus 87.2
updates/15.58 s for its operational control and 88.0/15.92 s for its
unweighted terminal control. Seed 43's large-y mean was `1.114` with
two lower-volume large-y failures, versus one for each matched control.
No weighted seed met the scale speed Gate, so the full Gate failed.

The fixed expanded specialist passed **6/6** high-volume large-y
attempts for each panel on the two new cases. All 16 failures across
the three learned panels were y-direction cases at volume `0.5225`:
the operational panel had `2/2/1` failures, unweighted terminal
`2/1/2`, and weighted `1/2/3` for seeds `17/29/43`. The weighted
panel's five failures in seeds 29 and 43 include two small-y attempts.
This concentration identifies a fresh
middle-volume reliability gap; it does not prove a single cause.

## Decision and next slice

The y weighting helped seed 17 but did not produce reproducible
two-seed, two-scale acceleration. The same weight and checkpoint rule
must not be retuned on these 24 exposed cases. The training population
has only two large-grid y and two large-grid z cases at each of volume
`0.5` and `0.55`, while the fresh failures clustered between them and
large-z refinement varied substantially by seed. The next independent
slice is **B2.27: a bounded, physically disjoint middle-volume
large-grid y/z position-coverage and label-feasibility audit** before
another fit. It should freeze the new position grid and data Gate first,
then test whether additional uniform terminal labels can be obtained
at unchanged numerical quality. It must not fit or select a model on
those labels in the same slice. A later learned screen and separate
confirmation would still be required before B3 or any acceleration
claim.

## Repository validation

Before the clean experiment commit, `uv sync --dev --locked`, Ruff,
mypy on `src`, all 363 Python tests, and `git diff --check` passed.
The required checks are repeated before committing this report.
