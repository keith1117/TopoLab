# B4.8 larger independent rollback confirmation

Prepared: 2026-10-02 (America/New_York)

**Complete; confirmation Gate failed.**
Fixed P/17 retained one terminal failure and one paid fallback.
All 96 references, 1,152 outcomes and independent audits are retained.
Uniform remains the operational default; B5 and final artifacts stay sealed.

## 1. Preregistration and immutable inputs

The [protocol](../planning/b4_8_rollback_confirmation_protocol.md) and
[implementation audit](b4_8_contract_boundary.md) merged in
[PR #115](https://github.com/keith1117/TopoLab/pull/115) after all required CI passed.
Clean merged execution source: `c185caffd5f3b3cd16b2f2f80948caee1e836784`
(merged `2026-10-02T17:19:06Z`). Identity: `topolab.b4_8.rollback-confirmation.v1`.

All P/C/S B4.1 and W B4.5 checkpoints, inputs, projection, specialist route,
360-update physical-plateau solver, independent quality and full-cost rules
remain unchanged. P/17 was fixed before these outcomes; a better diagnostic
seed cannot replace it. Every historical failed Gate and P/W failure remains
failed. No fit, label-input expansion, threshold, tolerance or solver change.

Execution checkout: `/private/tmp/topolab-b48-source`.
External root: `/Users/keith1117/Documents/TopoLab-data/b4-8-rollback-confirmation`.
Runtime: Apple M2/arm64/Darwin 25.5.0, 8 GiB RAM, Python 3.12.10,
NumPy 2.5.3, SciPy 1.18.1, Torch 2.14.0; BLAS/intra-op threads 1,
Torch inter-op threads 8. All stages used the same clean merged source.

| Receipt | SHA-256 |
|---|---|
| audit_receipts/plan.json | `31dece2979a469ea600911036d9e2ab15ae45c593c7b22cf770a4d135758f56f` |
| audit_receipts/production_release.json | `051867604ce5b4dab18d7dca91a046faa077de0578ede07e18a4390e39d21e6c` |
| context.json | `b405d69754c5c22a1fd936581d44beea2f261db2069600ee327421f953bad5be` |
| reference/summary.json | `e55f6f54a94b754c6575bea93a183d71ae3bef3d854447c0277fda5bd15badea` |
| screen/summary.json | `9cf1eb1999c36c2340c53194830dd531c3c4149eeb156e17ab38ab7d46f903af` |
| audit/summary.json | `7a4ef6d95cbba59734f01ee260f8fae818b89fbec3238b13595f9d63ae9f783b` |
| independent_audit.json | `88c37018ca9f6ca325003c4c5f4b57debf0855bd2313eb3a62dbed50064cd663` |
| resource_close.json | `c4128a77de823b0de2cc83d093157db52e689ee4dbdc4e0f908b675e9c5150ec` |
| audit/progress.json | `f1d06c3a99351ffcfbbcc4624d176ab11b2539d6be3c7a5243db70da37d6f98d` |
| protocol bytes | `0d6f46b65b508ea80137e79fc4f08bb39c45ccaa93bdf999173660fe0f8dabe2` |
| plan identity | `1981e64c41fc6b958d530a161bc6d41739e668ca04a3cd2dcdc623aee59dec15` |
| independent audit source | `c52d8b49abb975ff0d7203f6e122ca9d194e5e683a55b62c66791f807feff0f6` |
| resource closure source | `00a019c60821eb37261629b13d77d4849309be40ebc7f12c9ffba35bdb501006` |

## 2. Complete population and quality audit

All **96/96 mandatory uniform references** passed before screening.
All **1,152/1,152** fixed queries completed, with twelve methods per case,
48 cases per scale and six per scale/direction/volume cell. Volumes were
0.3353/0.4703/0.5413/0.6013; positions (1,1)/(1,2)/(3,1)/(3,2)/(5,1)/(5,2).
Small/large meshes were (12,6,3)/(24,12,6), y/z directions, with doubled
large-grid load indices. The six-position grid completes B4.7 geometric
mirrors; volumes use the fixed 0.0012 metadata offset. No outcomes chose
these definitions. All 96 fingerprints were unique and absent from the
historical ledger, all B3 definitions including final metadata and B4.5/6/7.
This whole published cohort is now exposed for future experiment versions.

All **1,250/1,250 production audit units** checked twelve used checkpoints,
all 528 complete-population NN labels, 96 references and every query witness.
The supplemental audit independently reconstructed **1,295**
terminal states/classifications, method/seed/route and complete Gate arithmetic
without invoking the production decision function. Means matched at
rtol=1e-14; counts, eligibility and Gate matched exactly. Every accepted and
operational state passed unchanged compliance/convergence/volume checks.
Failed initial candidates remain failed after successful fresh uniform fallback.

## 3. Frozen confirmation decision

Every ratio includes full outer query wall plus the one-second recording
allowance. Inference, projection, refinement, quality, callbacks and full
fallback are included. Lower costs alone are not final acceleration.

| Policy | Small mean | Large mean | Overall | Failures / fallbacks | Small total ratio | Large total ratio |
|---|---:|---:|---:|---:|---:|---:|
| uniform | 1.000000 | 1.000000 | 1.000000 | 0 / 0 | 1.000000 | 1.000000 |
| physics_heuristic | 1.059479 | 1.031472 | 1.045475 | 4 / 4 | 1.042719 | 1.012117 |
| nearest_neighbor | 0.800311 | 1.600748 | 1.200529 | 15 / 15 | 0.769690 | 1.630104 |
| C/17 | 0.893962 | 1.059094 | 0.976528 | 8 / 8 | 0.868463 | 1.053725 |
| C/29 | 0.845921 | 0.937344 | 0.891633 | 5 / 5 | 0.811244 | 0.864345 |
| C/43 | 0.853169 | 0.979345 | 0.916257 | 4 / 4 | 0.826834 | 0.929950 |
| P/17 | 0.820141 | 0.668344 | 0.744242 | 1 / 1 | 0.786037 | 0.639162 |
| P/29 | 0.812865 | 0.775756 | 0.794311 | 4 / 4 | 0.778965 | 0.824640 |
| P/43 | 0.781361 | 0.635149 | 0.708255 | 1 / 1 | 0.748947 | 0.629214 |
| W/17 | 0.889246 | 0.672015 | 0.780631 | 2 / 2 | 0.865807 | 0.650383 |
| W/29 | 0.808676 | 0.675164 | 0.741920 | 2 / 2 | 0.773140 | 0.653342 |
| W/43 | 0.836202 | 0.614290 | 0.725246 | 1 / 1 | 0.803104 | 0.605023 |

| P seed | Small y | Small z | Large y | Large z | Non-specialist y failures | Seed Gate | Primary eligible |
|---|---:|---:|---:|---:|---:|---|---|
| 17 | 0.791090 | 0.849191 | 0.787808 | 0.548880 | 1 | pass | no |
| 29 | 0.746236 | 0.879495 | 0.827991 | 0.723520 | 2 | fail | no |
| 43 | 0.740097 | 0.822625 | 0.719691 | 0.550607 | 1 | pass | no |

Passing P seeds: **[17, 43]**; at least two were required.
Each seed requires scale means <=0.90, direction means <=1.0, failures
<=min(2, matched C, matched W), matched non-specialist-y reliability and
overall gain over both fixed non-ML controls. Fixed P/17 additionally
requires zero failures/fallbacks, strict C/17 gain, either W/17 mean gain
or fewer failures, and <=0.90 total charged ratios at both scales.

P/17: met every seed criterion.

P/29: failed matched reliability.

P/43: met every seed criterion.

Fixed P/17 did not meet the requirement for zero failures and fallbacks.

Its large-y, volume 0.5413, position (3,1) attempt converged after 40 updates,
but independent compliance/uniform was 1.001056679441, exceeding the frozen
1.001 quality factor. Its successful fresh uniform fallback does not erase
that initial failure. No quality tolerance was changed.

Pooled P middle/high large-y successes: **17/18** at 0.5413, **18/18** at 0.6013.
The fixed minimum was 12/18 in each cell. No other primary was selected.

## 4. Retained failed attempts

All **47** failed initial attempts retained their statuses and paid fallbacks.
Counts by policy: C/17=8, C/29=5, C/43=4, P/17=1, P/29=4, P/43=1, W/17=2, W/29=2, W/43=1, nearest_neighbor=15, physics_heuristic=4.
The independent report retains complete case IDs, metrics, codes and timing
for every policy. P-panel failures are shown below; positions use small-grid
equivalents and large-grid indices double.

| P seed | Scale / direction | Volume | Position | Updates | Converged | Compliance / uniform | Case ID |
|---|---|---:|---|---:|---|---:|---|
| P/43 | large / y | 0.4703 | (1,1) | 66 | True | 1.001060452864 | `tlcase-v1-033f380c2181d9d1f94fc7f3d4b4a6507992c5e1a5004018bff779ca92add82a` |
| P/29 | large / y | 0.4703 | (1,1) | 62 | True | 1.001008965090 | `tlcase-v1-033f380c2181d9d1f94fc7f3d4b4a6507992c5e1a5004018bff779ca92add82a` |
| P/29 | small / z | 0.4703 | (3,2) | 18 | True | 1.009677810789 | `tlcase-v1-53c7cbca434bdf62c946bb2bcfcf62728c39e1600be373afca82567d77191e7b` |
| P/29 | large / y | 0.4703 | (1,2) | 63 | True | 1.001017464028 | `tlcase-v1-838e2ccc7891b194c1ab5d5b9854c658320e5b191a3d4ca38b78bbb4fc04d16e` |
| P/29 | small / z | 0.4703 | (3,1) | 18 | True | 1.009613821730 | `tlcase-v1-d9431c1421f2408accd5db0614722f1842c3c7f7630db10b3d316dfde5148e80` |
| P/17 | large / y | 0.5413 | (3,1) | 40 | True | 1.001056679441 | `tlcase-v1-d9dc312497ba5ade125c1b6d432ca029e375718fe301909a75a5db8f9c7b3e3f` |

## 5. Full cost and resource closure

| Stage | Final charged seconds | Peak RSS bytes | Frozen cap |
|---|---:|---:|---|
| reference | 1116.985301917 | 355221504 | 7,200 s / 2 GiB |
| screen | 12093.694808168 | 921124864 | 43,200 s / 2 GiB |
| audit | 895.156271627 | 1036238848 | 7,200 s / 2 GiB |
| total | **14105.836381712** | **1036238848** | 57,600 s / per-stage RSS |

Every production unit completed once, with no pending units or permanent
resource/integrity failure. Whole-command floors: audit=863.21 s, reference=1014.07 s, screen=10934.64 s.
Additional floor-deficit charge: 0.000000000 s.
Supplemental audits and closure increased the audit ledger without rewriting
any outcome, immutable production summary or unit chain. Closing allowances
cover the resource-closure command floor. No time was subtracted.

Screen inclusive timings: callback_bytes=824817, callback_cpu=5.954687000, callback_wall=24.522064476, query_cpu=9902.515790000, query_wall=10576.639693614, recording_before_receipt=22.986510800.
Legacy phase sum: 10573.370716114 s.
All recording receipts matched outcomes and remained within one second.
B3 data/B4.1 fits/B4.2 screen/B4.4 indices and the complete B4.5/6/7 receipt
chain remained unchanged. Generated records, logs, profiles and both audit
sources remain outside Git.

## 6. Next independent slice

**B4.9: bounded read-only diagnosis of the complete failed confirmation**.
Bind all outcomes and costs, isolate remaining terminal-quality/reliability/
refinement mechanisms before any independently registered intervention.
No new fit, threshold search, seed substitution or final access follows here.

Report this result and wait for a new user instruction before B4.9.

## 7. Repository validation

The implementation passed locked dependency sync, Ruff, mypy (61 source files),
all 39 related B4 tests (29.07 seconds), all 698 tests (493.38 seconds) and
`git diff --check` before commit, then all required CI before merge.
The evidence commit repeated locked dependency sync, Ruff, mypy (61 source
files), all 698 tests (539.99 seconds) and `git diff --check` successfully.
Its PR requires all applicable CI checks to pass before merge.
The two user-owned untracked duplicate documents remain untouched.
