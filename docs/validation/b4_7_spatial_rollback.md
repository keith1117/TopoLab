# B4.7 bounded spatial-objective rollback

Prepared: 2026-10-02 (America/New_York)

**Complete; bounded repair Gate passed.**
Fixed P/17 retained 0 terminal failures and 0 paid fallbacks.
All 48 references, 576 queries and independent audits are retained. Uniform
remains the operational default; B5 and all final artifacts remain sealed.

## 1. Frozen source and one intervention

The [protocol](../planning/b4_7_spatial_rollback_protocol.md) and
[implementation boundary](b4_7_contract_boundary.md) merged in
[PR #113](https://github.com/keith1117/TopoLab/pull/113) after all CI passed:
quality 10m49s/10m50s, frontend 15s/16s, and required Linux smoke 1m1s.
The push-only smoke was intentionally skipped; the PR smoke passed.
Clean merged execution source: `ea7e56ada9d552954f95756f59af16debea694e2`
(merged `2026-10-02T14:27:18Z`). Identity: `topolab.b4_7.spatial-rollback.v1`.

Use unchanged B4.1 P/17,29,43 generalists instead of the spatially weighted
W generalists, retaining unchanged same-seed S on large-grid y at volume
>=0.55. P/17 was fixed before any new outcome; no result selected another
primary. All P/W/C seeds and uniform/physics/NN controls remain reported.
No fit, label addition, checkpoint selection, routing threshold, numerical
equation, tolerance, projection or 360-update budget changed.

The original B4.2 and W/17 B4.6 failures remain failed. Historical P/17
failures and P/43's worse B4.6 reliability are not erased by this new cohort.
This repair cannot turn B4.6's descriptive P/17 result into confirmation.

The isolated execution checkout was `/private/tmp/topolab-b47-source`.
External root: `/Users/keith1117/Documents/TopoLab-data/b4-7-spatial-rollback`.
Locked Apple M2/arm64/Darwin 25.5.0, 8 GiB RAM, Python 3.12.10, NumPy 2.5.3,
SciPy 1.18.1 and Torch 2.14.0; BLAS/intra-op threads 1, inter-op threads 8.

| Receipt | SHA-256 |
|---|---|
| audit_receipts/plan.json | `36c51cbab9963b3e6e8c23868aef6cc9fe9f8bc4e8ad5b3316caac4cdd8ec2c0` |
| context.json | `57b21d1d25dbcd9ee604a97857b31e9e521f11741d999e30b38abcb8242d34df` |
| reference/summary.json | `7c84e94c5196b996c2f8b3c589df0519fbaf8a1437ed4c6953688470e7d73250` |
| screen/summary.json | `17eaf004a87a52c7afddf70a48eaf7a7d6702d26f8c99597dd5f581f06be35f8` |
| audit/summary.json | `583dea5c2f356e2cf460a553b4030512d8c84fd9543984a6265a37013f1dfe7e` |
| independent_audit.json | `ce9f267a8c5ec696a4982aa25e07cdc607b01137b5087725db21627a65d0f856` |
| resource_close.json | `46a6167303c0bcb5c5bd7bd58acdc9ec950740caa37962aff94e7d9f5b0d6c92` |
| audit/progress.json | `a6e48222e8e7b0af1e211020ae83101d3d77885ce99ec6951d7d89dc1a5a8e82` |
| protocol bytes | `8bfe2bf55deed9b892e5c2c2654c08f06de00ce5e272e75e55951842ad7639c5` |
| plan identity | `7f161aa36d9071bf17beae5e26f93f274e1c3b6ffdaf12f104f57f0f1faf8825` |
| independent audit source | `c3d5c4fce30ab405f4f48e2a5d7b23b2fa5c31750d57e47100ed01286775ac58` |
| resource closure source | `46478cbc181c3ca563da2b0e9d785525491aea41fd1089b0d0093b905a8ab4d8` |

## 2. Complete population and independent checks

All **48/48 mandatory uniform references** passed before screening.
All **576/576** queries completed: three cases per scale/direction/volume
cell, 24 per scale and twelve methods per case. The volumes were
0.3341/0.4691/0.5401/0.6001, positions (1,2)/(3,1)/(5,2), y/z directions,
and small/large meshes (12,6,3)/(24,12,6); large load indices double.
All fingerprints were unique and absent from the historical ledger,
all B3 definitions including final metadata, and B4.5/B4.6 populations.
This entire cohort is now exposed for future experiments.

All **626/626 production audit units** checked twelve used checkpoints,
528 complete-population NN labels, 48 references and every query witness.
The supplemental audit independently reconstructed **646**
terminal states/classifications, method/seed/route assignments and all
mean/total-cost arithmetic without invoking the production Gate function.
Means matched at rtol=1e-14; counts, eligibility and Gate matched exactly.
Every accepted and operational state passed the unchanged independent
compliance/convergence/volume rules. Failed attempts remain failed after
their separately executed successful uniform fallbacks.

## 3. Fixed Gate decision

Each query pays full outer wall plus a one-second recording allowance.
Fallback, callbacks, projection, inference and quality decision are included.
Ratios retain every case; lower values alone are not final acceleration.

| Policy | Small mean | Large mean | Overall | Failures / fallbacks | Small total ratio | Large total ratio |
|---|---:|---:|---:|---:|---:|---:|
| C/17 | 0.909138 | 0.953962 | 0.931550 | 3 / 3 | 0.908510 | 0.967893 |
| C/29 | 0.850307 | 0.800714 | 0.825511 | 2 / 2 | 0.838715 | 0.767479 |
| C/43 | 0.885209 | 0.851279 | 0.868244 | 1 / 1 | 0.876922 | 0.833988 |
| P/17 | 0.857511 | 0.681739 | 0.769625 | 0 / 0 | 0.847199 | 0.665699 |
| P/29 | 0.846163 | 0.829781 | 0.837972 | 3 / 3 | 0.836739 | 0.905310 |
| P/43 | 0.805106 | 0.656768 | 0.730937 | 1 / 1 | 0.794671 | 0.645162 |
| W/17 | 0.877700 | 0.695301 | 0.786501 | 0 / 0 | 0.873931 | 0.685053 |
| W/29 | 0.817437 | 0.696425 | 0.756931 | 1 / 1 | 0.803971 | 0.696192 |
| W/43 | 0.833852 | 0.671784 | 0.752818 | 1 / 1 | 0.826914 | 0.679560 |
| nearest_neighbor | 0.832556 | 1.623242 | 1.227899 | 8 / 8 | 0.821151 | 1.604946 |
| physics_heuristic | 1.055521 | 1.035009 | 1.045265 | 2 / 2 | 1.066628 | 1.026775 |
| uniform | 1.000000 | 1.000000 | 1.000000 | 0 / 0 | 1.000000 | 1.000000 |

| P seed | Small y | Small z | Large y | Large z | Non-specialist y failures | Seed Gate | Primary eligible |
|---|---:|---:|---:|---:|---:|---|---|
| 17 | 0.816528 | 0.898494 | 0.748929 | 0.614548 | 0 | pass | yes |
| 29 | 0.777783 | 0.914543 | 0.863826 | 0.795735 | 2 | fail | no |
| 43 | 0.777800 | 0.832413 | 0.716489 | 0.597047 | 1 | pass | no |

Passing P seeds: **[17, 43]**. Fixed P/17 requires zero
failures/fallbacks, both scale means <=0.90, all direction means <=1.0,
matched C/W reliability and non-ML gains, strict C/17 gain, either a
W/17 overall gain or fewer failures, and total ratios <=0.90 at both scales.

P/17: met every seed criterion.
Its overall mean 0.769625 strictly improved C/17's 0.931550 and W/17's
0.786501; matched W/17 also had zero failures on this cohort. Both fixed-primary
total ratios, 0.847199/0.665699, were below 0.90. This small matched improvement
over W/17 establishes the predeclared repair condition, not a final claim.

P/29: its three failures exceeded matched C/29's two and W/29's one;
its two non-specialist-y failures also exceeded both controls' one.

P/43: met every seed criterion but its one fallback made it ineligible for a
zero-failure primary. P/17 remained fixed despite P/43's lower overall mean.

Pooled P middle/high large-y terminal successes: **9/9** at 0.5401, **9/9** at 0.6001;
the frozen minimum was 6/9 in each cell. No different primary was selected.

## 4. Retained terminal failures

All **22** failed attempts retained their original statuses and paid fallbacks.
The external independent report retains complete IDs, compliance ratios,
convergence status, updates, codes and fallback timing for every method.

| P policy | Case ID | Converged | Updates | Compliance / uniform |
|---|---|---|---:|---:|
| P/43 | `tlcase-v1-9389528e7093be3c1b0c90cf594c1349d911d741d2657320ace799469854c9bc` | True | 59 | 1.001097833782 |
| P/29 | `tlcase-v1-cf7077267c576bebbfcc4c9046532caa2445df0a855d1898f27416a3b5137484` | True | 65 | 1.001020302818 |
| P/29 | `tlcase-v1-dd9ce55b945e588dbbc0655a5ca17e2863a3c25a19a1cd15039efbcb278c1138` | True | 106 | 1.001022682451 |
| P/29 | `tlcase-v1-e0b13e08965f78fbbc853bbf7c743c87fbbd7eb7c4be8dd89af3209bb28f3d5c` | True | 18 | 1.009386684301 |

## 5. Resource and cost closure

| Stage | Final charged seconds | Peak RSS bytes | Frozen cap |
|---|---:|---:|---|
| reference | 510.037747459 | 358842368 | 3,600 s / 2 GiB |
| screen | 5518.693303999 | 829194240 | 21,600 s / 2 GiB |
| audit | 507.349200667 | 763248640 | 3,600 s / 2 GiB |
| total | **6536.080252125** | **829194240** | 28,800 s / stage RSS caps |

Every production numerical/audit unit completed once, with no pending units or
permanent resource/integrity failure. The first sandboxed runtime preflight
was denied the CPU-brand sysctl before labels/models/solver work; its
original trace and 1.60-second whole-command floor remain retained and
are additionally charged to closure. It did not rerun a numerical case.

Whole-command floors, including the failed preflight: audit=471.21 s, reference=455.85 s, screen=4935.71 s.
Additional floor-deficit charge: 0.000000000 s.
Final closure is charged separately in the audit ledger without rewriting
the immutable production audit summary or any outcome. The closure command's
3.32-second profile floor is covered by the final audit charge, including its
reserved closing allowance.

Screen inclusive timings: callback_bytes=369234, callback_cpu=2.211197000, callback_wall=5.089693514, query_cpu=4602.681458000, query_wall=4752.796328872, recording_before_receipt=8.728259990.
Legacy phase sum: 4751.824876695 s. No time was subtracted.
All recording receipts matched their outcomes and stayed within one second.
Upstream B3/B4 indices and all B4.5/B4.6 receipts remained unchanged.
Artifacts, logs, profiles and independent audit sources remain outside Git.

## 6. Next independent slice

**B4.8: separately frozen larger physically disjoint development confirmation**,
with unchanged P/17, all fixed checkpoints, route, quality and complete-cost
criteria. This one repair cohort is not independent confirmation.
A compatible final contract/freeze and B5 remain separate later Gates.

Report this slice and wait for a new instruction before starting B4.8.

## 7. Repository validation

Before the evidence commit, locked dependency sync, Ruff, mypy (60 source
files), all **687 tests (444.14 seconds)** and `git diff --check` passed.
The implementation also passed all 687 tests (441.46 seconds) before its commit
and all required CI before merge. Evidence publication is gated on all required
CI passing before merge.
The two user-owned untracked duplicate documents remain untouched.
