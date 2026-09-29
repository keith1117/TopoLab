# B2.24 expanded-position specialist fit and fresh screen

Date: 2026-09-29 (America/New_York)

Status: **the frozen B2.24 development Gate failed.** All mandatory stages
completed: 24/24 new uniform references, three expanded-label fits, ten
fixed-checkpoint diagnostic labels, and 168/168 fully charged outcomes.
The added training coverage repaired terminal quality on this screen's
two high-volume large-y cases, but no new seed met the two-scale and
direction-wise speed bounds. Uniform initialization remains the
operational default; B3 and final evidence remain closed.

## Frozen intervention and exposure

The [B2.24 protocol](../planning/b2_24_expanded_training_protocol.md)
fixed one training-data change: add the 20 audited B2.23 train labels to
the B2.22 468-case terminal-design training population. Keep the same
thirteen-channel input, context CNN, case-weight-8 high-volume y objective,
AdamW schedule, seeds, two-case B2.22 checkpoint selection, and fixed
large/high-volume/y query route. The ten new B2.23 validation labels
were read only for post-selection MSE diagnosis. The unchanged B2.22
specialists were matched controls on every fresh case. Both old and new
routes charged decision, encoding, inference, projection, full SIMP
refinement, terminal quality, and complete fresh uniform fallback.

The canonical plan SHA-256 was
`50230a66db17c26ed4665bce41142c61b3e5ffc5f2dcfb83988d77d84884dd94`.
The read-only plan and all stages ran from clean merged source revision
`dd110b8067acccdcc900709a20809c924b7fbbc8` with one CPU/BLAS
thread. The exposure ledger blocked 790 prior or reserved physical case
IDs, including all 30 B2.23 labels. The 24 new cases used three unused
volumes, two fixed load positions, both mesh scales, and y/z directions;
they were physically disjoint from training, validation, previous
development, and reserved final evidence. No M2 held-out/OOD or new
final outcome was opened.

## Complete stages

| Stage | Complete evidence | Elapsed | Peak RSS | Frozen limit | Result |
|---|---:|---:|---:|---:|---|
| Uniform references | 24/24 | 233.587 s | 333,594,624 B | 3,600 s; <=2 GiB | Pass |
| Expanded-label fits | 3/3 | 274.846 s | 349,224,960 B | 7,200 s; <=2 GiB | Pass |
| Matched independent screen | 24 cases; 168 outcomes | 1,487.823 s | 321,437,696 B | 16,000 s; <=2 GiB | Complete; Gate failed |

All 24 references converged, had positive finite compliance, and passed
independent final quality and physical-volume checks. New checkpoints
selected epochs `92,119,74` for seeds `17,29,43`. The screen had zero
accepted quality violations. Its 26 failed learned attempts (16 old,
10 new) each retained failure status and paid a complete fresh uniform
fallback.

The ten new large-y validation labels gave the following **diagnostic**
terminal-design MSE values. They did not select checkpoints or change
the Gate.

| Seed | Old B2.22 MSE | Expanded B2.24 MSE |
|---:|---:|---:|
| 17 | 0.102149 | 0.017628 |
| 29 | 0.082934 | 0.016566 |
| 43 | 0.115395 | 0.024192 |

## Matched screen and Gate

Each paired time ratio uses its own optimized uniform reference as the
denominator and includes every route and fallback charge.

| Seed | Old small / large mean | Expanded small / large mean | Old / expanded large-y mean | Old / expanded large-z mean | Old / expanded failures |
|---:|---:|---:|---:|---:|---:|
| 17 | 0.596 / 1.170 | 0.564 / 0.994 | 1.318 / 0.932 | 1.022 / 1.056 | 5 / 3 |
| 29 | 0.696 / 1.223 | 0.649 / 1.064 | 1.474 / 1.108 | 0.972 / 1.020 | 6 / 4 |
| 43 | 0.600 / 1.211 | 0.601 / 1.011 | 1.423 / 1.047 | 1.000 / 0.975 | 5 / 3 |

All three new seeds improved their large-scale mean relative to their
matched old specialists, but **none** reached the frozen `<=0.90`
large-scale bound. Seed 17 met the `<=1.0` large-y bound but missed
large-z at `1.056`; seeds 29 and 43 exceeded the large-y bound.
The Gate required at least two seeds meeting both scale means and all
four direction means, with no more failures than their matched old
controls, at least four of six high-volume large-y successes, strict
quality improvement over old specialists, and zero accepted violations.
**Zero** seeds met its speed component, so the complete Gate failed.

The two high-volume large-y cases at volume `0.5965` were the measured
quality repair: the old specialists passed **0/6** attempts, whereas
the expanded specialists passed **6/6**. Their six new paired time
ratios were `0.426–0.597`; the six old ratios were `1.478–1.935` after
fallback. This evidence covers two fresh physical cases, not a general
claim for the entire large-y distribution. Elsewhere, each new seed
still had two small-y failures and one or two lower-volume large-y
failures. On large-z, all new attempts passed quality, but mean
refinement time was roughly 18.4–20.1 s per case and two of three
direction time means exceeded uniform. The remaining speed gap is
therefore concentrated in residual y fallbacks and large-z refinement
cost on this cohort; this is a measured cost decomposition, not a
causal model diagnosis.

The reference, fit, and screen index SHA-256 values were:

```text
c3703ab52820f618f3ec664a4a515432d5e95bb3c6d8464210b6003d24935eb7
89bacfec6fbdfd2732ab74404626dc33a914b7cf788750f02276319b7e73700a
e77ad2eb6670dcae64e14c51d67b4b6ad6dc05d2d8e57448be39c8c584db1075
```

A separate external audit checked the frozen plan, source/context and
exposure bindings, all 24 ordered identities, checkpoint and history
checksums, first-minimum epoch selection, all ten B2.23 validation
labels and independently recomputed old/new diagnostic MSE, all 168
method outcomes, route and phase sums, paired denominators, quality
and complete fallback status, resources, stratum means, and Gate
arithmetic. It reproduced 0/6 versus 6/6 high-volume large-y quality,
zero passing seeds, and the failed Gate. Generated references, weights,
histories, outcomes, and audit code remain outside Git.

## Decision and next slice

The 20 new position labels produced a clear matched high-volume large-y
quality and time improvement on this cohort. The unchanged context
route outside that stratum retained y failures and costly large-z
refinement, so this exact expanded specialist does not pass the full
development Gate. Do not retune the model, route, selection rule, or
thresholds on these exposed cases. The next independent slice is
**B2.25: a bounded, read-only large-grid residual-failure and
refinement-cost diagnosis** that uses the complete B2.24 phase and
terminal records to select one new mechanism for a separately
frozen fresh development screen. B3 and any acceleration claim remain
closed.

## Repository validation

Before the clean experiment commit, `uv sync --dev --locked`, Ruff,
mypy on `src`, all 357 Python tests, and `git diff --check` passed.
The required checks are repeated before committing this report.
