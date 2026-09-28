# B2.21 uniform terminal-design learning target

Date: 2026-09-28 (America/New_York)

Status: **the frozen B2.21 development Gate failed.** All mandatory
stages completed within resource limits: 24/24 screen uniform references,
12/12 independent validation terminal targets, three fixed fits, and
168/168 complete screen outcomes. No new seed passed the two-scale and
direction-wise charged-speed Gate. Uniform initialization remains the
operational default; B3 and final evidence remain closed.

## Frozen intervention and provenance

The [B2.21 protocol](../planning/b2_21_terminal_target_protocol.md)
changed the B2.12 context CNN's supervised target from the uniform
solver's update-30 design to its **converged terminal design**. It kept
the 13-channel vector-load input, 26,433-parameter model, unweighted
MSE, AdamW schedule, 468/12 fitting case definitions, seeds `17,29,43`,
filtered-volume projection, 360-update screen solver, independent
terminal quality, and complete fallback charging fixed. The 468 train
targets came from hash-verified B2.4 budget-240 labels. Twelve matching
validation definitions lacked those labels and were solved and
independently quality-checked before fitting. The selected epochs were
`112,199,169` for seeds `17,29,43`.

The plan SHA-256 was
`3f5fadd4945cb0d6fbae2739cbc477244d0b7a52e657d58eb7ce5d4ffc2edaf2`.
Every stage ran from clean committed source revision
`91d6899fda6bc4cb863509c6ed12f4cd03a8dc0f` with one CPU/BLAS
thread. The blocked ledger contained 712 exposed or reserved physical
case identities. The 24 new screen cases at three new volumes, both
mesh scales and directions, and two fixed load positions were disjoint
from prior development and final evidence. No M2 held-out/OOD or new
final case was opened.

## Complete stages

| Stage | Complete evidence | Elapsed | Peak RSS | Frozen time limit | Outcome |
|---|---:|---:|---:|---:|---|
| Uniform references | 24/24 | 214.912 s | 416,251,904 B | 3,600 s | Pass |
| Validation terminal targets | 12/12 | 133.840 s | 364,675,072 B | 1,800 s | Pass |
| Fixed model fits | 3/3 | 322.196 s | 364,609,536 B | 7,200 s | Pass |
| Independent screen | 24 cases, 168 outcomes | 1,376.153 s | 444,940,288 B | 16,000 s | Complete, Gate failed |

All stages stayed below the frozen 2 GiB peak-RSS limit. The 24
uniform references converged with positive finite compliance and
physical-volume error `<=0.005`; all twelve validation targets also
passed independent convergence, compliance, and volume checks under
their unchanged 240-update label budget. There were zero accepted
quality violations. A failed learned attempt retained its failed
status after paying its complete fresh uniform fallback.

## Matched screen

All paired time ratios use the matching optimized uniform end-to-end
time as denominator, including input encoding, inference, projection,
full refinement, terminal quality decision, and full fallback where
required.

| Seed | B2.12 small / large mean | Terminal-target small / large mean | B2.12 / terminal large-y mean | B2.12 / terminal failures | New-seed Gate |
|---:|---:|---:|---:|---:|---|
| 17 | 0.671 / 1.153 | 0.737 / 1.077 | 1.335 / 1.475 | 3 / 5 | Fail |
| 29 | 0.661 / 1.132 | 0.603 / 1.052 | 1.497 / 1.471 | 4 / 4 | Fail |
| 43 | 0.598 / 1.038 | 0.619 / 0.975 | 1.306 / 1.306 | 3 / 3 | Fail |

The frozen Gate required at least two new seeds with charged mean
`<=0.90` on both scales, all four scale/direction means `<=1.0`, no
more failures than the paired B2.12 control, and at least four of six
new high-volume large-y attempts passing terminal quality. **Zero**
new seeds passed and high-volume large-y quality was **0/6**; the
unchanged controls were also 0/6 on those same two cases. Seed 17
added two terminal failures. All three terminal-target seeds improved
large-z speed relative to their controls, but none met the large-y
direction bound (`1.306–1.475`) or the large-scale mean bound.

On the two high-volume large-y cases, terminal-target final
compliance ratios to matched uniform were `1.004686/1.002037` for
seed 17, `1.004713/1.002016` for seed 29, and
`1.004694/1.001716` for seed 43. Every value exceeded the frozen
`1.001` quality boundary and incurred full fallback. A closer
terminal target did not reliably place the initialization in the
same-quality solution basin.

The uniform-reference, validation-target, fit, and screen index
SHA-256 values were, respectively:

```text
91675cd4c04d250ed2c5b878d8f28996e53b71fcb819aafb060050683a22de53
3e7add2c85650bcb5ac0329236678887baaf2fc3acd4882a1f8f8fc7070796ab
a997e1f69703126b4c0fdf7f2c87363f3fb6093c3970ab383f8765e60d2149d5
a44145fb61c7a3eb372fca02aaaef691b35f4b22630c9d50623eeb377d844d6d
```

An independent standard-library audit verified stage context and
source binding, case uniqueness and separation, target/checkpoint/
history checksums, earliest minimum-MSE selections, all 24 screen
strata and 168 method outcomes, phase sums, paired denominators,
quality statuses, full fallback charges, resource caps, and the
frozen Gate. It reproduced zero passing seeds and the failed decision.
Generated data, model weights, outcomes, and audit code remain outside
Git.

## Decision and next slice

The terminal target helped large-z runtime but did not repair the
high-volume large-y quality basin. This exact terminal-target method
ends here; its exposed cases will not be used to tune a target blend,
epoch, volume cutoff, or quality/speed threshold. The next
independent slice is **B2.22**, a bounded high-volume y-direction
specialist learning intervention with a predeclared route and disjoint
development screen. This targets the measured regime directly rather
than changing the acceptance limit. A positive screen would still
require a separate larger development confirmation before B3.

## Repository validation

Before the clean experiment commit, `uv sync --dev --locked`, Ruff,
mypy on `src`, all 348 Python tests, and `git diff --check` passed.
The required checks are repeated before committing this report.
