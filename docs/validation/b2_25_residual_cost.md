# B2.25 residual quality and cost diagnosis

Date: 2026-09-29 (America/New_York)

Status: **the frozen read-only diagnosis completed and selected a joint
non-specialist intervention for B2.26.** This is a choice of what to test
next, not a passed learned acceleration Gate. B2.24's failed Gate stands,
uniform initialization remains the operational default, and B3 remains
closed.

## Frozen boundary and audit

The [B2.25 protocol](../planning/b2_25_residual_cost_protocol.md) bound
plan SHA-256
`11a03776d87828c0100381d6276a515b72dd4f59c311eeb67963f507e69a2cc0`.
The read-only plan and diagnosis ran from clean merged revision
`9178486c993aaaa9a711ce70b7aa953498004b84`, with one CPU/BLAS
thread. The diagnosis read only B2.24's 24 exposed development cases,
their 24 uniform references, three fit-index records, and 168 matched
screen outcomes. It verified the exact reference, fit, and screen index
SHA-256 values recorded in the protocol, source/plan links, case and
method order, resource caps, routes, phase sums, uniform denominators,
terminal quality, and charged fallback status. It did not call a solver,
fit a model, tune a threshold, or open a fresh, M2 held-out/OOD, or final
case. Runtime was 8.842 seconds with 263,553,024 bytes peak RSS, below
the frozen 60-second and 1-GiB caps. The external canonical diagnosis
at `/tmp/topolab-b225/diagnosis.json` has SHA-256
`7444bc1ee39a4f157149db67a3153f7f7d8811a863ff9bbaf7fe774b5426286e`.
A separate standard-library calculation reproduced every scale/direction
mean and failure count from the checksum-bound screen index.

## Where the residual failures and cost occur

The expanded seeds had **3, 4, and 3** failed attempts for seeds
`17, 29, 43`, respectively. Every seed failed the same two small-grid
y cases at volume `0.5965`; seed 17 failed one large-grid y case at
volume `0.5165`, seed 29 failed both, and seed 43 failed one. Their
candidate compliance ratios to matched uniform were `1.00222–1.00245`
for the six small-y failures and `1.00205–1.00567` for the four large-y
failures. These exceed the unchanged `1.001` acceptance limit. All ten
failed attempts retained failure status and paid complete uniform
fallback: 15.316, 29.416, and 15.788 seconds in aggregate by seed.
The B2.24 expanded high-volume large-y specialist had passed all six
attempts on its two fresh cases; the residual large-y failures are at
lower volume and use the context route.

All 18 expanded large-grid z attempts passed terminal quality and paid
no fallback. Their mean refinement times were 20.075, 19.339, and
18.420 seconds for seeds `17, 29, 43`, versus 18.978 seconds for matched
uniform. Mean candidate iteration counts were 108.8, 103.3, and 104.2,
versus 104.0 for uniform. This is a refinement-cost issue on the exposed
large-z stratum; wall-time variation cannot by itself establish a new
model effect. Outside the two specialist-routed cases, old and expanded
methods used exactly the same fixed context checkpoint: all 66 paired
old/new candidate terminal records matched exactly. The remaining
generalist problems were not repaired by the specialist's added labels.

## Frozen optimistic speed-only bounds

Each number is an arithmetic mean of per-case end-to-end seconds divided
by its own uniform reference. The fallback-free bound subtracts only
recorded fallback seconds; large-z-zero makes all six large-z times per
seed zero; combined applies both. Failed candidate status is unchanged
under every bound.

| Bound | Seed 17 large / large-y / large-z | Seed 29 large / large-y / large-z | Seed 43 large / large-y / large-z | Seeds meeting both scale and all direction speed limits |
|---|---:|---:|---:|---:|
| Measured | 0.994 / 0.932 / 1.056 | 1.064 / 1.108 / 1.020 | 1.011 / 1.047 / 0.975 | 0/3 |
| Fallback-free | 0.914 / 0.771 / 1.056 | 0.905 / 0.789 / 1.020 | 0.928 / 0.881 / 0.975 | 0/3 |
| Large-z zero | 0.466 / 0.932 / 0 | 0.554 / 1.108 / 0 | 0.523 / 1.047 / 0 | 1/3 |
| Combined | 0.386 / 0.771 / 0 | 0.395 / 0.789 / 0 | 0.440 / 0.881 / 0 | 3/3 |

The small-grid means in the measured, fallback-free, and large-z-zero
orders were `0.564/0.411/0.564`, `0.649/0.493/0.649`, and
`0.601/0.442/0.601` for seeds `17,29,43`; all met the `<=0.90` scale
limit even before hypothetical savings. The combined small-grid means
equal their fallback-free values. The table shows why a single
cost-removal idea cannot establish two qualifying seeds even under an
unrealistically favorable limit. It does not show that any bound is a
deployable, quality-preserving policy.

## Decision and next slice

The protocol's ordered decision selected **joint generalist**: zero
seeds passed with free fallbacks, only one with impossible zero-cost
large-z, and three with both. B2.26 should freeze **one** mechanism for
the non-specialist context path that addresses y terminal quality on
both mesh scales and large-z refinement work, while keeping the B2.24
expanded high-volume large-y specialist fixed. It must use new,
physically disjoint development cases, complete fallback charges, and
the unchanged compliance/volume acceptance rules. The B2.25 cases are
exposed diagnosis data and must not choose thresholds, checkpoints, or
a result on the fresh B2.26 screen. A favorable B2.26 screen would still
require separately frozen development confirmation before B3 or an ML
acceleration claim.

## Repository validation

Before the protocol commit, `uv sync --dev --locked`, Ruff, mypy on
`src`, all 361 Python tests, and `git diff --check` passed. The required
checks are repeated before committing this result report.
