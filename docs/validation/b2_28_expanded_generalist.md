# B2.28 middle-volume generalist expansion and fresh screen

Date: 2026-09-29 (America/New_York)

Status: **the frozen B2.28 development Gate passed.** All 24 fresh
uniform references, three fixed fits, twenty diagnostic labels, and
168 fully charged screen outcomes completed. Seeds `17,29,43` all met
the complete predeclared Gate with zero new-panel quality failures or
fallbacks. This is bounded development feasibility on one fresh cohort;
separate larger confirmation and the later final Gates remain required.
Uniform initialization remains the operational default, and B3 remains
closed.

## Frozen intervention and exposure

The [B2.28 protocol](../planning/b2_28_expanded_generalist_protocol.md)
added exactly B2.27's forty train terminal-design labels to B2.26's
weighted terminal generalist. The resulting 508 train cases formed
64 shape-bucketed batches per epoch. The existing y-case weight `8`
at volume `>=0.5`, other weight `1`, terminal target, thirteen-channel
input, 26,433-parameter context CNN, seeds, optimizer, epoch cap, and
earliest minimum unweighted MSE on twelve B2.21 validation cases stayed
fixed. The twenty new validation labels were diagnostic only. Both
panels used the unchanged B2.24 specialist on large-grid y cases at
volume `>=0.55`.

The canonical plan SHA-256 was
`1e33936caedaa5702d14ffe3bbfa349211b44c170d13d9a0f3d4f0a90a865da0`.
After protocol PR #92 passed CI and merged, the read-only plan and
all three stages ran from clean merged source revision
`d8e97010e94ce63d1939a4a1454746c68f7124e8`, with one CPU/BLAS
thread. The recorded runtime was Darwin arm64, Python `3.12.10`,
NumPy `2.5.3`, SciPy `1.18.1`, and Torch `2.14.0`; Torch intra-op
threads were one and its inter-op setting was eight. The exposure
ledger blocked 898 earlier exposed or reserved
physical case IDs. The 24 new cases used volumes
`0.3745,0.5295,0.5935`, two x-max load positions, both mesh scales,
and y/z directions, with six cases per scale/direction stratum.
Exactly two high-volume large-y cases invoked the fixed specialist.
No M2 held-out/OOD or final evidence was opened.

## Complete stages and independent audit

| Stage | Complete evidence | Elapsed | Peak RSS | Frozen limit | Result |
|---|---:|---:|---:|---|---|
| Uniform references | 24/24 | 208.109 s | 378,208,256 B | 3,600 s; <=2 GiB | Pass |
| Expanded fits and diagnostics | 3/3 fits; 20 labels | 435.209 s | 389,021,696 B | 7,200 s; <=2 GiB | Pass |
| Matched screen | 24 cases; 168 outcomes | 844.549 s | 385,449,984 B | 24,000 s; <=2 GiB | Gate passed |

All references passed independently checked terminal quality with at
most 142 updates against the frozen 360-update cap. The expanded fits
selected epochs `173,54,191` for seeds `17,29,43`. There were zero
accepted quality violations. All four old-panel failures retained
failure status and paid complete fresh uniform fallback. The stage
index SHA-256 values were:

```text
reference 982cee3614cf9a40b2baff796036444cb297f6267becb34cef542819c06058d9
fit       0d874a0ea7c0c4f87740b1630033dc80418e44975f0c1e0a266f4f6fe553f402
screen    55bfc7e74b2b5250e49b5beafcfbc5af844c9d2ec514edd02d2d0fdf088b2586
```

A separate external audit verified source/plan binding, ordered case
identities and strata, reference quality, checkpoint/history byte
hashes, earliest minimum-MSE selection and patience, every route and
outcome, timing phase sums, matched uniform denominators, accepted
quality, full fallback charges, resource limits, and independent Gate
arithmetic. It reproduced all three passing seeds. A second audit
opened the forty train and twenty diagnostic label bytes, checked their
split separation, and independently recomputed old/new diagnostic MSE.
Generated labels, weights, indices, histories, logs, and audit code
remain outside Git.

## Matched quality and charged speed

Each ratio divides the complete query-time cost by that case's
optimized uniform reference. Routing, encoding/inference, filtered
volume projection, refinement, quality decision, and fresh uniform
fallback are charged. Means are arithmetic means of per-case ratios.

| Seed | Old small / large | Expanded small / large | Expanded small-y / small-z | Expanded large-y / large-z | Failures old / expanded | Full Gate |
|---:|---:|---:|---:|---:|---:|---|
| 17 | 0.576 / 0.747 | 0.532 / 0.585 | 0.538 / 0.527 | 0.612 / 0.558 | 2 / 0 | Pass |
| 29 | 0.473 / 0.826 | 0.580 / 0.665 | 0.585 / 0.575 | 0.747 / 0.582 | 1 / 0 | Pass |
| 43 | 0.535 / 0.770 | 0.493 / 0.587 | 0.466 / 0.520 | 0.628 / 0.546 | 1 / 0 | Pass |

All three expanded seeds met both scale means `<=0.90`, all four
direction means `<=1.0`, and both matched failure constraints. Their
non-specialist y failure counts were zero, within the cap of two and
no greater than their matched old counts. The new panel passed **6/6**
middle-volume large-y attempts at volume `0.5295`, compared with
**3/6** for the old panel; each old seed failed at the same one of the
two positions. Both panels passed **6/6** high-volume large-y specialist
attempts, meeting the frozen minimum of four. The other old failure
was seed 17 on a small-y case at volume `0.3745`.

Large-y candidate updates averaged `58.5,70.0,60.0` for the expanded
panel, compared with `70.3,77.0,76.0` for the old panel; the old failed
attempts additionally paid fallback. Large-z updates averaged
`46.0,48.0,45.0`, compared with `46.0,55.3,46.8` for old. Expansion
improved large-scale charged means in all three seeds. Seed 29's
small-scale mean regressed against its old control (`0.580` versus
`0.473`), while remaining within the frozen uniform-relative bound.
These observations apply to this cohort and do not establish broad
performance or reliability.

## Diagnostic validation labels

The ten y and ten z labels were evaluated only after selection by
the unchanged twelve-case validation MSE. They did not affect fitting,
epoch selection, route, or threshold.

| Seed | Old y MSE | Expanded y MSE | Old z MSE | Expanded z MSE |
|---:|---:|---:|---:|---:|
| 17 | 0.077291 | 0.011250 | 0.046735 | 0.019799 |
| 29 | 0.086231 | 0.025370 | 0.054433 | 0.042073 |
| 43 | 0.083296 | 0.008240 | 0.058514 | 0.018544 |

All six diagnostic means improved. They support the development
coverage hypothesis; they do not independently demonstrate operational
speed or final generalization.

## Validation and next slice

Protocol implementation validation passed locked dependency sync,
Ruff, mypy, all **370 Python tests**, and diff checks before its commit.
The outcome documentation receives the same required checks before
commit; merge follows successful CI. No numerical tolerance changed.

The next independent slice is **B2.29: larger independent development
confirmation**. Separately freeze a larger physically disjoint cohort,
preserving the three B2.28 checkpoints, fixed specialist route,
quality rules, complete fallback charges, and predeclared resource
limits. It must test transfer of this feasibility result before B3 can
open. Do not tune on the exposed B2.28 screen or claim final learned
acceleration. Uniform remains the operational default.
