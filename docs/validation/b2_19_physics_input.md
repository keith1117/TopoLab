# B2.19 uniform-state sensitivity input

Date: 2026-09-28 (America/New_York)

Status: **the frozen B2.19 development Gate failed.** The new physical
feature reduced all three held-out trajectory MSE values, but no new
seed met the required two-scale, direction-wise, and reliability bounds.
Uniform initialization remains the operational default. B3 and final
evidence remain closed.

## Frozen change and provenance

The [B2.19 protocol](../planning/b2_19_physics_input_protocol.md) froze
one learning-side input change: one uniform-state FEM solve supplies a
log-normalized negative SIMP sensitivity as channel 14. The B2.12
spatial-context CNN otherwise keeps its topology; the first layer grows
to 26,865 total parameters. The B2.6 update-30 targets, loss, 468/12
fit/selection cases, three seeds, SIMP solver, 360-update limit,
projection, terminal quality, and complete fallback charging were
unchanged. The plan SHA-256 was
`e75e3eb9796729d9ef9921b617ca28783f5c96762a6a5b8acc95389bb0e6d664`.
The clean execution revision was
`989840c560562900b9741ecc9b99a21ec59e1a27`.

The screen volumes `0.3375,0.4875,0.5795` crossed both meshes and `y/z`
loads at a new point-load position. Its twelve case IDs were disjoint
from the 664 recorded exposed or unopened reserved development case
identities; the volumes also excluded M2 and design-exposed M3 v1
volumes. No M2 held-out or final case was opened.

## Complete stages

| Stage | Completeness | Elapsed | Peak RSS | Limit | Outcome |
|---|---:|---:|---:|---:|---|
| Uniform references | 12/12 | 99.536 s | 369,000,448 B | 1,800 s / 2 GiB | Pass |
| Physical-feature fits | 3/3 | 328.504 s | 311,590,912 B | 7,200 s / 2 GiB | Pass |
| Matched screen | 12 cases, 84 outcomes | 552.345 s | 304,250,880 B | 8,000 s / 2 GiB | Complete, Gate failed |

All uniform references converged with finite positive compliance and
physical-volume error `<=0.005`. All three selections and checkpoint
bytes were hash-verified. Selected validation MSE decreased versus the
unchanged B2.12 checkpoints: seed 17 `0.028346 → 0.026428`, seed 29
`0.026953 → 0.025871`, and seed 43 `0.029582 → 0.026867`. This supervised
metric did not predict a better charged end-to-end result.

| Seed | B2.12 small / large mean | B2.19 small / large mean | B2.19 large-y mean | B2.12 / B2.19 failures | New-seed Gate |
|---:|---:|---:|---:|---:|---|
| 17 | 0.843 / 0.758 | 0.851 / 0.815 | 0.823 | 0 / 1 | Fail: more failures |
| 29 | 0.825 / 0.748 | 0.622 / 1.045 | 1.188 | 1 / 0 | Fail: large-scale and y cost |
| 43 | 0.767 / 0.862 | 0.876 / 1.140 | 1.546 | 1 / 2 | Fail: large-scale, y cost, failures |

Every ratio includes inference, the new FEM feature solve, projection,
full refinement, terminal decision, and complete fallback when needed.
The physical-feature setup averaged `0.012 s` on small and `0.289 s` on
large meshes. B2.19 seed 17 failed the high-volume **small-y** case at
compliance ratio `1.001917`; seed 43 failed that case at `1.001754` and
the high-volume **large-y** case at `1.001047`. Seed 29 had no quality
failures but was slow on large-y. Two new seeds passed terminal quality
on the high-volume large-y case, satisfying that one subcondition.
There were zero accepted quality violations. A failed learned attempt
remained failed even after its separately charged uniform fallback.

The fixed B2.12 seeds 17 and 29 happen to satisfy the numerical
two-scale/direction speed bounds on this twelve-case cohort. That is
descriptive development evidence on this cohort. It does not reverse
the [B2.14 larger confirmation failure](b2_14_development_confirmation.md)
or establish transferable acceleration. The B2.19 Gate concerns the
predeclared new input, and **zero** of its three seeds passed.

The reference, fit, and screen index SHA-256 values were respectively
`2c27dbad1dc8e3f2bd89f2487a3e14c10d1507869cc68ab5b7a3c340de1e578d`,
`5be8f80ec6d2f6c81326ddaabd90a45bffdbd3becf3b62c04c4b31797b2e4784`,
and `2a5accb40612b0e0a4dd349ae82cf76ed648481320e03aa8c66bbd9dc8ab331b`.
An independent standard-library audit checked source/context binding,
checkpoint and selection hashes, all twelve strata and 84 method rows,
phase sums, paired denominators, quality statuses, fallback charges,
resource limits, and the frozen Gate. It reproduced zero passing new
seeds and the failed decision. All generated artifacts and the audit
script remain outside Git.

## Decision and next slice

The extra physical information made the update-30 density target easier
to predict, but did not reliably move complete refinements into faster,
quality-feasible basins. This is a measured mismatch between validation
MSE and the operational objective; no input normalization, threshold,
or quality limit is retuned on these exposed cases. The next independent
slice is **B2.20**, a bounded investigation of a different training
target or selection objective aligned with terminal quality and charged
runtime. It must freeze one intervention and new development evidence
before execution. A later, larger confirmation is still required before
B3 even if a future small screen passes.

## Repository validation

Before the clean execution commit, `uv sync --dev --locked`, Ruff,
mypy on `src`, all 342 Python tests, and `git diff --check` passed.
The required checks are repeated before committing this report.
