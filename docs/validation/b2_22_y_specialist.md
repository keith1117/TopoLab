# B2.22 high-volume y specialist and fixed route

Date: 2026-09-28 (America/New_York)

Status: **the frozen B2.22 development Gate failed.** All mandatory stages
completed: 24/24 independent uniform references, three fixed specialist fits,
and 168/168 fully charged screen outcomes. No routed seed met the two-scale
and direction-wise speed limits. The two high-volume large-y cases produced
3/6 successful routed attempts against the frozen minimum of 4/6. Uniform
initialization remains the operational default; B3 and final evidence stay
closed.

## Frozen intervention and exposure

The [B2.22 protocol](../planning/b2_22_y_specialist_protocol.md) gave the
52 y-direction training cases at volume `>=0.55` weight `8` in the
case-normalized terminal-design MSE, while all other cases had weight `1`.
Only four of those 52 training cases were on the large mesh. The two
y-direction, volume-`0.525` validation targets, one per scale, selected the
earliest minimum MSE checkpoint. The 13-channel input, B2.12 context CNN,
three seeds `17,29,43`, training schedule, projection, and solver stayed
fixed. At query time, the specialist was routed only to large-mesh y cases
at volume `>=0.55`; all other cases used the matched unchanged B2.12
context model. Every route decision, inference, refinement, failure decision,
and complete fresh uniform fallback was charged.

The plan SHA-256 was
`5c5a2c87ac6dae22ac48a058de6bbf04a4f9632bc2df17a8debc9a06de0a1c2a`.
The read-only plan and every stage ran from clean committed source revision
`ac2e733525638c88fcec5f88bcd925841ca63812` with one CPU/BLAS thread.
The exposure ledger blocked 736 prior or reserved physical case identities.
The 24 new cases used three previously unused volumes, two load positions,
both mesh scales, and y/z directions; they were physically disjoint from
training, validation, prior development, and final evidence. No M2 held-out,
OOD, or new final outcome was opened.

## Complete stages

| Stage | Complete evidence | Elapsed | Peak RSS | Frozen limit | Result |
|---|---:|---:|---:|---:|---|
| Uniform references | 24/24 | 229.762 s | 308,166,656 B | 3,600 s; <2 GiB | Pass |
| Specialist fits | 3/3 | 134.256 s | 385,794,048 B | 7,200 s; <2 GiB | Pass |
| Independent screen | 24 cases; 168 outcomes | 1,468.963 s | 350,240,768 B | 16,000 s; <2 GiB | Complete; Gate failed |

All references converged, had positive finite compliance, and passed
independent final quality and physical-volume checks. The three specialist
checkpoints selected epochs `39,65,25` for seeds `17,29,43`. The screen had
zero accepted quality violations. Seventeen failed learned attempts across
all methods paid and recorded a complete fresh uniform fallback; they remain
classified as failed.

## Matched screen

Each paired time ratio uses its own optimized uniform case as denominator.
The means include route decision and every fallback charge.

| Seed | Context small / large mean | Routed small / large mean | Context / routed large-y mean | Context / routed failures | Routed seed Gate |
|---:|---:|---:|---:|---:|---|
| 17 | 0.681 / 1.077 | 0.647 / 1.116 | 1.244 / 1.335 | 3 / 3 | Fail |
| 29 | 0.649 / 1.138 | 0.611 / 1.026 | 1.352 / 1.173 | 4 / 3 | Fail |
| 43 | 0.559 / 0.962 | 0.556 / 1.019 | 0.979 / 1.087 | 2 / 2 | Fail |

The fixed Gate required at least two routed seeds with scale means `<=0.90`
on both scales, four scale/direction means `<=1.0`, no more failures than
their matched context controls, and at least four of six high-volume large-y
routed attempts passing terminal quality. **Zero** routed seeds passed.
Every routed large-scale mean exceeded `0.90`, and every routed large-y mean
exceeded `1.0`. High-volume large-y quality was **3/6** for the routed
specialists, versus **2/6** for the fixed controls on this same screen.

The route selected the specialist on exactly two large-y cases at volume
`0.5945`. At small-grid load position `(y=4,z=1)`, all three specialist
attempts failed the unchanged `1.001` compliance boundary; their ratios
to uniform were approximately `1.00491`, `1.00489`, and `1.00522`.
At `(y=1,z=2)`, all three specialist attempts passed terminal quality,
where two of three fixed controls passed. Thus weighting helped one load
position on this cohort but did not transfer to the other; this is an
observation on two cases, not a general position rule. The unchanged
control and route means outside the specialist stratum also vary from
timing noise because both were measured as separate complete queries.

The reference, fit, and screen index SHA-256 values were:

```text
2d44f92e0e4b7d1e88c094a384375795e79e93b31047a371cb75099074130c00
a7a0f598bff793e860b8d561976f3be4b38a00fca7864bfb86854c56acfb5dde
62ffe463c863f5ff57b88687a5cc9aeb0abf5261087335f4e790e5f3b3f58632
```

An independent external audit checked the frozen plan and exposure index,
source/context bindings, all 24 ordered case identities, checkpoint and
history byte checksums, first-minimum checkpoint selection, 168 method
outcomes, route choices, phase sums, paired denominators, quality and full
fallback status, resource limits, all stratum means, and Gate arithmetic.
It reproduced 3/6 high-volume large-y success, zero passing seeds, and the
failed decision. Generated data, weights, histories, outcomes, and audit
code remain outside Git.

## Decision and next slice

The weighted terminal-target specialist improved high-volume large-y
quality from 2/6 to 3/6 against its matched fixed controls, but the
position-specific quality failure and large-y charged-speed gap persist.
This exact weight, validation selection, and route ends here; do not retune
them on these exposed cases. The next independent slice is **B2.23: a
bounded large-y load-position coverage and label-feasibility audit**.
It should quantify the prior training positions and test whether a fixed,
new training-label expansion can cover the failing physical regime before
another model fit. Any later fit and screen require a separately frozen
intervention and fresh disjoint development cases. B3 and any acceleration
claim remain closed.

## Repository validation

Before the clean experiment commit, `uv sync --dev --locked`, Ruff, mypy on
`src`, all 351 Python tests, and `git diff --check` passed. The required
checks are repeated before committing this report.
