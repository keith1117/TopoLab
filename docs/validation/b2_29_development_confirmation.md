# B2.29 larger independent development confirmation

Date: 2026-09-29 (America/New_York)

Status: **the frozen B2.29 confirmation Gate passed.** All 48 mandatory
uniform references and 432 ordered, fully charged outcomes completed.
Expanded seeds `17,43` met every predeclared seed criterion; seed `29`
failed the small-scale and small-z speed bounds and remains in the
complete record. Independent audit reproduced the decision. This permits
**B3.1 contract and final-boundary planning**. It does not pass Gate B3
or establish final learned acceleration. Uniform remains the operational
default, and final evidence remains sealed.

## Frozen policies, source, and exposure

The [B2.29 protocol](../planning/b2_29_development_confirmation_protocol.md)
fixed all three B2.28 expanded generalists, all three B2.26 old weighted
generalists, and the three shared B2.24 specialists. Both panels retained
the specialist route on large-grid y cases at volume `>=0.55`. The fixed
physics heuristic and original B2.4 train-only nearest neighbor provided
non-ML comparators. The neighbor used exactly 468 original train labels
and its original ten-channel, shape-bucketed distance rule. There was no
fit, checkpoint reselection, solver change, route change, or threshold
adjustment after exposure.

The canonical plan SHA-256 was
`5cc928fedfe5827dab3fb24b4203361e4ca866d9bc1203a054859d5e2c835590`.
After protocol PR #94 passed CI and merged, the read-only plan and both
stages ran from clean merged source revision
`9175380dbdb82fc7482fff9c26834d1959ae98dd`, with one CPU/BLAS thread.
The runtime was Darwin arm64, Python `3.12.10`, NumPy `2.5.3`, SciPy
`1.18.1`, Torch `2.14.0`, and Safetensors `0.8.0`; Torch intra-op threads
were one and its inter-op setting was eight. The lockfile SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.

The exposure ledger blocked 922 earlier exposed or reserved physical
case IDs and the old M2/M3 volume grids. The new cohort crossed volumes
`0.3185,0.4565,0.5315,0.5895`, three x-max load positions, y/z directions,
and meshes `(12,6,3)`/`(24,12,6)`: twelve cases per scale/direction
stratum and three per scale/direction/volume cell. Small-grid positions
were `(y=1,z=1),(y=3,z=2),(y=5,z=1)`, with doubled large-grid indices.
Only three high-volume large-y cases invoked the specialist. No M2
held-out/OOD or final evidence was opened.

The B2.28 fixed selected epochs remained `173,54,191`, from checkpoint
source `d8e97010e94ce63d1939a4a1454746c68f7124e8`. Their checkpoint
SHA-256 values, in seed order `17,29,43`, were:

```text
4cb8a0b73a620a98caa347b04f7e0d85a13d17703d0dd03815b43f4e9562bbc4
b33e765361a4115c344285daae583e9f5465fd72b80b81aebdba709fd2559ba9
c2f32a9415a5f180cbc54b58485cd1893a9cb1edfa4e0b49102726cac7e659a2
```

## Completeness, resources, and independent audit

| Stage | Evidence | Elapsed | Peak RSS | Frozen limits | Result |
|---|---:|---:|---:|---|---|
| Mandatory uniform references | 48/48 | 446.121 s | 414,564,352 B | 7,200 s; <=2 GiB | Pass |
| Matched confirmation | 48 cases; 432 outcomes | 4,488.168 s | 353,484,800 B | 48,000 s; <=2 GiB | Gate passed |

Every reference passed independent terminal quality checks with at most
201 updates against the unchanged 360-update cap. Each screen case
obtained a fresh timed uniform denominator; its candidate metrics
matched the mandatory reference exactly. There were zero accepted
quality violations. All failed attempts retained failure status and
paid a complete fresh uniform fallback. Stage index SHA-256 values were:

```text
reference c22b955f941e9f62a0f8ee276f7704c1df7615f3520335648d41441bd9065604
screen    a4f0c0abe3ca1491928cb96c5e0457fd2a2865e5eb6fdf4233462605b118c1d1
```

A separate external audit checked plan/source binding, all five source
index hashes, checkpoint and history byte hashes for all nine fixed
models, original earliest minimum-MSE selection and patience, ordered
case identities and strata, reference quality, routes, neighbor matches
against the 468 train IDs, every outcome, matched denominators, phase
sums, accepted quality, fallback charges, resource limits, and independent
Gate arithmetic. It reproduced passing seeds `17,43`, all failure counts,
and both quality-cell counts. Generated indices, logs, summaries,
checkpoints, neighbor labels, and audit code remain outside Git.

## Matched quality and charged time

Ratios divide each attempt's complete query cost by its fresh paired
uniform cost. Means are arithmetic means of per-case ratios, not ratios
of total times. Routing, encoding/inference or neighbor lookup,
filtered-volume projection, refinement, quality decision, and full
fallback are charged. No seed or failed case is removed from the means.

| Policy | Small | Large | Small-y | Small-z | Large-y | Large-z | Overall | Failures | Seed Gate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Uniform | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0 | — |
| Physics heuristic | 1.179 | 0.977 | 1.295 | 1.064 | 0.966 | 0.989 | 1.078 | 3 | — |
| Nearest neighbor | 0.543 | 2.689 | 0.587 | 0.498 | 3.189 | 2.188 | 1.616 | 11 | — |
| Old 17 | 0.465 | 0.978 | 0.434 | 0.497 | 1.049 | 0.907 | 0.721 | 3 | — |
| Old 29 | 0.627 | 0.956 | 0.574 | 0.681 | 1.142 | 0.770 | 0.792 | 2 | — |
| Old 43 | 0.719 | 0.952 | 0.649 | 0.788 | 1.164 | 0.739 | 0.835 | 2 | — |
| Expanded 17 | 0.776 | 0.645 | 0.635 | 0.916 | 0.744 | 0.546 | 0.710 | 0 | Pass |
| Expanded 29 | 1.196 | 0.761 | 0.624 | 1.768 | 0.780 | 0.742 | 0.978 | 1 | Fail |
| Expanded 43 | 0.611 | 0.759 | 0.472 | 0.750 | 0.729 | 0.788 | 0.685 | 2 | Pass |

Seeds 17 and 43 met both scale means `<=0.90`, all direction means
`<=1.0`, the two-failure cap, matched old failure constraints, and the
requirement to beat both non-ML overall means. Non-specialist y failures
were old `2/2/2` versus expanded `0/1/1`. The expanded middle-volume
large-y cell passed **9/9**, compared with old **3/9**; both panels passed
**9/9** high-volume large-y specialist attempts. Both frozen cell minima
were six of nine.

Seed 29's small-z mean was `1.768`, including an accepted 194-update
attempt at volume `0.5315`, node `233`, with ratio `11.227`. This case
remains in the denominator and mean. Its small-scale mean `1.196` also
failed. Expansion did not improve every seed or stratum: seed 17's
small-scale mean regressed against old, and seed 43's large-z mean was
slower than old. This confirmation does not justify selecting a final
checkpoint using these exposed outcomes.

The three expanded failures were all retained and charged:

| Seed | Scale / direction | Volume | Node | Candidate updates | Compliance / uniform | Charged ratio |
|---:|---|---:|---:|---:|---:|---:|
| 29 | Large / y | 0.4565 | 1474 | 62 | 1.001121 | 1.601 |
| 43 | Large / z | 0.5315 | 1474 | 360 | 0.979763 | 2.815 |
| 43 | Large / y | 0.3185 | 1474 | 89 | 1.001179 | 1.699 |

The two y attempts exceeded the unchanged compliance bound `1.001`.
The z attempt exhausted the 360-update cap without passing terminal
quality despite lower compliance. Physical-volume errors were below
the fixed bound in all three; no quality tolerance was relaxed.

## Complete phase costs

The following are sums of seconds across all 48 cases per policy;
they are not the primary paired-ratio statistic.

| Policy | Route | Setup | Projection | Refinement | Decision | Fallback | End to end |
|---|---:|---:|---:|---:|---:|---:|---:|
| Uniform | 0.000 | 0.044 | 3.001 | 462.941 | 4.838 | 0.000 | 470.823 |
| Physics heuristic | 0.000 | 4.650 | 2.856 | 440.408 | 4.828 | 2.496 | 455.238 |
| Nearest neighbor | 0.000 | 0.364 | 2.857 | 962.160 | 3.884 | 178.810 | 1,148.075 |
| Old 17 | 0.009 | 1.498 | 2.891 | 409.675 | 4.560 | 67.069 | 485.701 |
| Old 29 | 0.001 | 0.572 | 2.927 | 406.482 | 4.634 | 31.425 | 446.040 |
| Old 43 | 0.001 | 0.550 | 2.750 | 395.853 | 4.923 | 31.015 | 435.093 |
| Expanded 17 | 0.005 | 0.393 | 2.816 | 283.501 | 5.218 | 0.000 | 291.932 |
| Expanded 29 | 0.001 | 0.765 | 2.894 | 340.215 | 4.681 | 18.334 | 366.890 |
| Expanded 43 | 0.001 | 0.590 | 2.861 | 318.498 | 4.463 | 54.221 | 380.633 |

Separate one-time model loading cost was `0.041816 s`; original neighbor
loading/building cost was `6.149285 s`, with `6,877,512 B` stored neighbor
arrays. These were included in the screen stage resource budget. There
was no new training or label-generation cost. Stage elapsed time also
includes loading, bookkeeping, and atomic persistence.

## Validation and next slice

Protocol implementation passed locked dependency sync, Ruff, mypy, all
**374 Python tests**, and diff checks before its commit and CI merge.
Outcome validation also passed locked dependency sync, Ruff, mypy
(39 source files), all **374 Python tests** in `246.06 s`, and diff
checks before commit. The outcome PR must pass CI before merge.
No numerical convention or tolerance changed.

The next independent slice is **B3.1: freeze the new versioned ML
contract and final exposure boundary**. Specify the primary workload,
physically disjoint train/validation/final-ID/OOD strata, solver and
label rules, complete exposure ledger, fixed bounded model program,
quality and fallback-inclusive claim criteria, compute budget, and
ordered stopping rules. Preserve all exposed B2 evidence and the
historical M1/M2/M3 record. Later B3 data implementation and audits must
pass Gate B3 before B4 fitting; B5 final evaluation remains after B4.
The confirmation is development evidence on one machine and a bounded
cohort, without final uncertainty estimates or independent replication.
Uniform initialization remains the operational default.
