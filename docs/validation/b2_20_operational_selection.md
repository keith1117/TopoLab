# B2.20 operational checkpoint selection

Date: 2026-09-28 (America/New_York)

Status: **the frozen B2.20 development Gate failed.** All five stages
completed within their time and memory budgets, with 12/12 selection and
24/24 screen uniform references and all 132/168 respective outcomes.
No operationally selected seed passed the two-scale/direction-wise Gate.
Uniform initialization remains the operational default; B3 and final
evidence remain closed.

## Frozen intervention and evidence boundary

The [B2.20 protocol](../planning/b2_20_operational_selection_protocol.md)
froze one intervention: select among fixed B2.12 training checkpoints
using complete, charged development outcomes instead of validation density
MSE. The 13-channel context CNN, 26,433 parameters, 480 B2.6 update-30
targets, 468/12 fit/MSE-validation cases, loss, optimizer, seeds, solver,
360-update limit, projection, terminal quality limits, and fallback
charging stayed unchanged. Candidate epochs were `17:{80,120,160}`,
`29:{80,120,141,160}`, and `43:{80,120,160}`. The MSE-best checkpoint
tensors matched the fixed B2.12 controls element by element.

The canonical plan SHA-256 was
`2b72bcdcfd92c32908af73ee329550d8f364dcbb8a740c197858b72deb30f192`.
All stages ran from clean source revision
`33743994cc1f685ebb981945494e8cf2eb5b98e4`, with one CPU/BLAS
thread. The blocked development ledger contained 676 earlier exposed or
reserved identities. The 12 new selection cases and 24 further screen
cases were disjoint from each other and from that ledger. M2 held-out,
OOD, and final evidence remained sealed.

## Complete stages and checkpoint decision

| Stage | Complete evidence | Elapsed | Peak RSS | Frozen time limit | Outcome |
|---|---:|---:|---:|---:|---|
| Selection uniform references | 12/12 | 113.503 s | 360,775,680 B | 1,800 s | Pass |
| Fixed fits | 3/3 | 327.729 s | 379,060,224 B | 7,200 s | Pass |
| Operational selection | 12 cases, 132 outcomes | 1,149.686 s | 346,849,280 B | 10,000 s | Complete |
| Screen uniform references | 24/24 | 198.849 s | 398,983,168 B | 3,600 s | Pass |
| Independent screen | 24 cases, 168 outcomes | 1,326.662 s | 375,160,832 B | 16,000 s | Complete, Gate failed |

Every stage was below the frozen 2 GiB peak-RSS limit. All uniform
references converged, had positive finite compliance, passed independent
terminal quality, and had physical-volume error `<=0.005`. Every learned
attempt, including a failed one, retained its status and paid full uniform
fallback separately.

The frozen lexicographic rule minimized terminal failures, then the
worst of four scale/direction charged means, then overall charged mean,
then epoch. Its audited decision chose:

| Seed | B2.12 MSE-best epoch | B2.20 selected epoch | Selection failures | Worst direction mean | Overall mean |
|---:|---:|---:|---:|---:|---:|
| 17 | 160 | 120 | 1 | 1.127 | 0.713 |
| 29 | 141 | 160 | 2 | 1.376 | 0.772 |
| 43 | 160 | 80 | 2 | 1.420 | 0.907 |

The selected checkpoint hashes were frozen in the decision artifact
before screen references or outcomes were opened.

## Independent screen decision

All ratios use matched uniform end-to-end time as denominator. They
include prediction, setup, projection, full refinement, terminal quality
decision, and the complete fallback when required.

| Seed | B2.12 small / large mean | Selected small / large mean | B2.12 / selected large-y mean | B2.12 / selected failures | Selected Gate |
|---:|---:|---:|---:|---:|---|
| 17 | 0.552 / 0.980 | 0.651 / 0.992 | 1.282 / 1.269 | 3 / 3 | Fail |
| 29 | 0.622 / 1.031 | 0.571 / 1.048 | 1.383 / 1.398 | 4 / 4 | Fail |
| 43 | 0.619 / 1.027 | 0.662 / 1.073 | 1.329 / 1.420 | 4 / 4 | Fail |

The Gate required at least two selected seeds with charged mean `<=0.90`
on both scales, each of four scale/direction means `<=1.0`, no more
terminal failures than its B2.12 control, and at least four of six
selected high-volume large-y attempts passing terminal quality. It
obtained **zero** passing seeds and **0/6** high-volume large-y successes;
the matched controls also had 0/6 successes in those same cases. No
selected seed improved its failure count. Even selected seed 17, whose
large-scale mean was below 1.0, missed the `<=0.90` scale bound and had
large-y mean `1.269`. Accepted quality violations were zero.

Both high-volume large-y screen cases failed terminal quality for all
six learned methods. Their selected final compliance ratios to matched
uniform were `1.001979–1.003712`, above the frozen `1.001` bound, so
the charged fallbacks matter to the measured cost. The screen result
does not support transferable same-quality ML acceleration or a B3
transition.

The selection-reference, fit, selection-outcome, decision,
screen-reference, and screen-outcome artifact SHA-256 values were,
respectively:

```text
ac810004ebad5d1e5ece359f55ec3e65e652fc7e5422aebf01f658c5c5a1dd32
28b130c2ce56f65bff94cbad88dd455c935c2305d57d9b854a569ef38294ec4a
a16b22edee6a0552d5545b3842dfb43e4b02e08039f469544032b09041624571
9c7c1a7c65d5b32651d5fcfec17a7eac2434445d060a2d55d25bdc4ba315ec6e
22b7106f59d6c482b8d333e603558b8dc76bd7e54c4e3a7c06915a3de3f15218
a8b3fce38f6db4017db582e04a21c0559b270e6787fb4190cc1f15afe6b834ce
```

An independent standard-library audit checked source and context binding,
all checkpoint/history bytes and hashes, case uniqueness and strata,
every phase sum and paired denominator, terminal quality and fallback
charges, the frozen checkpoint ranking, resource caps, and the complete
screen Gate. It reproduced the failed decision. Generated artifacts and
audit code remain outside Git.

## Decision and next slice

Selection by observed operational cost improved the twelve-case
selection score for some epochs but did not transfer to new load
positions and volumes. The dominant observed failure is terminal quality
on high-volume large-y cases; checkpoint choice alone did not repair it.
The exact B2.20 checkpoint-selection method ends here. Its exposed
cases will not be used to add epochs, alter the ranking, move volume
cutoffs, or relax quality/speed limits.

The next independent slice is **B2.21**, a bounded learning-side
quality-basin intervention for high-volume large-y designs, with its
mechanism, stop rule, and disjoint development evidence frozen before
execution. Any positive small screen still requires a separate larger
development confirmation before B3.

## Repository validation

The protocol and executable were frozen after `uv sync --dev --locked`,
Ruff, mypy on `src`, all 345 Python tests, and `git diff --check` passed.
The required checks are repeated before committing this report.
