# B4.6 larger independent development confirmation

Prepared: 2026-10-02 (America/New_York)

**Complete; confirmation Gate failed.** The frozen W/17 primary had two
terminal-quality failures and paid two fresh uniform fallbacks. Only W/43
passed its single-seed criteria; it also had one fallback, so no W seed was
primary-eligible. Do not replace W/17, reinterpret the earlier failed B4.2
Gate, or open B5. Uniform remains the operational default.

## 1. Preregistration and execution identity

The [protocol](../planning/b4_6_confirmation_protocol.md) and
[implementation boundary](b4_6_contract_boundary.md) were merged in
[PR #111](https://github.com/keith1117/TopoLab/pull/111) after all CI passed:
quality 13m41s/10m50s, frontend 24s/13s, and Linux smoke 58s. The push-only
smoke was intentionally skipped; the PR smoke passed. Clean merged execution
source: `a6c01acccebdd2e02c4155a1a0b4abe83a755dae`, merged
`2026-10-02T07:58:26Z`. Identity: `topolab.b4_6.development-confirmation.v1`.

External root: `/Users/keith1117/Documents/TopoLab-data/b4-6-development-confirmation`.
The source clone was `/private/tmp/topolab-b46-source`. Runtime matched the
locked Apple M2/arm64/Darwin 25.5.0 environment: 8 GiB RAM, Python 3.12.10,
NumPy 2.5.3, SciPy 1.18.1, Torch 2.14.0, BLAS/intraop threads 1 and Torch
interop threads 8. All stages used that clean source and immutable B3/B4.1/B4.5
inputs. No model fit, route change, tolerance change, new input label or final
artifact access occurred.

| Receipt | SHA-256 |
|---|---|
| metadata plan | `2bde23e3da2232bd06a20607e5735d0dec81c3b5a7bc716face878e38b8c1440` |
| protocol bytes | `ee80a8f83e887f438515ba44e049f5aadfb635704da6161f3e6d6eea7fd28d49` |
| execution context | `2db3e3be8657a52ffcd582876a9eff143bc4eb446136e1bd5be2bc3c14c1dd2f` |
| reference summary | `2384f141dde14c7a928d3aba62e5d8677706386360a1d5c11ed3079cc39931f9` |
| screen summary | `6fd2358cb4808be0530fa3c063de966b042bf525f40b2b32313d3d2338c4752f` |
| original audit summary | `97ab5048e82b29ee75ca3c8245395df10914ecbb636558c5eca612c9ee31f201` |
| independent audit | `4e64822cc79910b1b13f23f8fee26a224f93b8f4725557257e4eff60b88f8629` |
| independent audit source | `f15229036698298ee2eb998dc6ef91fc7c5404cbd63abdb95819f7e451a7f2df` |
| resource closure | `833db4ce48d86ae33c0b983798f7d4ec3b6df4fdb7711246cad5a0775616277d` |
| closure source | `e7ec00811bb82359f71a884d93ad6946225e5749ea01489b262e750ad67be686` |
| final audit progress | `2a53ed036b0df07e901c96eb872ef9b7d6b1dfef41dc443c363f6db812abb22f` |

## 2. Complete population and independent audit

All **96/96** mandatory uniform references passed. All **1,152/1,152** fixed
outcomes completed, with 12 methods per case and six cases in each of the 16
scale/direction/volume cells. All 96 physical fingerprints were unique and
absent from the historical ledger, all B3 definitions and B4.5's 48 cases.
Keep this entire published cohort exposed for later experiments.

The **1,250/1,250** production audit units independently checked all 528 NN
train labels, all 12 used checkpoints, 96 reference witnesses and every
candidate/fallback witness. The supplemental script recomputed **1,291**
terminal-state/classification checks: 96 references, 1,152 initial outcomes
and 43 fresh fallbacks. It independently reconstructed mean and total-cost
arithmetic without invoking the production decision function; floating means
matched at `rtol=1e-14`, and counts/eligibility/Gate matched exactly. Numerical
quality tolerances were unchanged. Every operational outcome passed quality;
43 failed initial candidates remain failures after their successful fallbacks.

The 43 failures comprise C:13, P:4, W:7, NN:14 and physics:5. Their original
`quality_error` codes are retained: 37 converged with unacceptable terminal
quality; one P/29 and five NN attempts were non-convergent at 360 updates. No candidate,
seed, case or fallback was dropped. Every attempt count equals its completed
count (96/1,152/1,250); there were no repeated attempts, pending units, resource
failures or integrity flags. Screen chain head:
`18f1e405688e294da1dddd21abea52303577e9bcf22193b6ed7db052e7ea9336`.
Audit chain head remained
`080a72b4861f665de2363e783535f88076201f3d6b2a21ed59371ee09f009b34`
through supplemental audits and closure.

## 3. Frozen decision

Ratios include complete outer query wall plus the full one-second recording
allowance for every method, including uniform. Candidate failures include
all failed-attempt and fresh fallback work. Lower ratios mean less charged
query time; they do not by themselves establish final acceleration.

| Policy | Small mean | Large mean | Overall mean | Failures / fallbacks | Small total ratio | Large total ratio |
|---|---:|---:|---:|---:|---:|---:|
| uniform | 1.000000 | 1.000000 | 1.000000 | 0 / 0 | 1.000000 | 1.000000 |
| physics | 1.071045 | 1.037455 | 1.054250 | 5 / 5 | 1.078652 | 1.036593 |
| NN | 0.800658 | 1.624723 | 1.212690 | 14 / 14 | 0.789715 | 1.645078 |
| C/17 | 0.867191 | 0.888783 | 0.877987 | 5 / 5 | 0.857466 | 0.882843 |
| C/29 | 0.829636 | 0.922141 | 0.875889 | 3 / 3 | 0.819623 | 0.889521 |
| C/43 | 0.837542 | 1.077977 | 0.957760 | 5 / 5 | 0.825346 | 1.058139 |
| P/17 | 0.798126 | 0.684840 | 0.741483 | 0 / 0 | 0.789576 | 0.682733 |
| P/29 | 0.823837 | 0.746120 | 0.784978 | 2 / 2 | 0.816859 | 0.789794 |
| P/43 | 0.804997 | 0.641842 | 0.723419 | 2 / 2 | 0.795171 | 0.632288 |
| W/17 (fixed primary) | 0.827552 | 0.800326 | 0.813939 | 2 / 2 | 0.816608 | 0.815536 |
| W/29 | 0.820660 | 0.755709 | 0.788184 | 4 / 4 | 0.811869 | 0.747748 |
| W/43 | 0.831796 | 0.660589 | 0.746192 | 1 / 1 | 0.822602 | 0.653580 |

| W seed | Small y | Small z | Large y | Large z | Non-specialist y failures | Seed Gate | Primary eligible |
|---|---:|---:|---:|---:|---:|---|---|
| 17 | 0.781155 | 0.873950 | 0.783034 | 0.817618 | 2 | fail | no |
| 29 | 0.779574 | 0.861746 | 0.847490 | 0.663928 | 3 | fail | no |
| 43 | 0.784411 | 0.879181 | 0.709659 | 0.611519 | 1 | pass | no |

All three W seeds met the speed bounds. W/17 failed reliability against P/17
(2 versus 0 failures, including non-specialist y), zero-primary-fallback, and
P/17 improvement conditions. W/29 exceeded the maximum two failures and both
matched controls' reliability limits (4 versus C/29:3, P/29:2); its three
non-specialist y failures exceeded P/29's one. W/43 met its single-seed
criteria but had one failure/fallback. Thus only one seed passed, and the
prospectively fixed primary failed. Both pooled middle/high large-y cells
passed **18/18** against the frozen >=12/18 minimum. W/17's total ratios also
met <=0.90, which cannot rescue failed quality/reliability requirements.

## 4. Retained W terminal failures and repair evidence

All seven W attempts converged within 360 updates but exceeded the unchanged
1.001 compliance ratio against their mandatory uniform reference. These are
terminal-quality failures, not cases to extend or reinterpret after the fact.
Positions below are small-grid equivalents; large-grid indices double.

| Seed | Scale / direction | Volume | Position (y,z) | Updates | Compliance / uniform |
|---|---|---:|---|---:|---:|
| 17 | small / y | 0.3329 | (4,1) | 10 | 1.001072935462 |
| 17 | large / y | 0.4679 | (5,1) | 63 | 1.001489298730 |
| 29 | large / y | 0.4679 | (1,1) | 70 | 1.001069546701 |
| 29 | large / y | 0.3329 | (3,2) | 136 | 1.001505887086 |
| 29 | large / z | 0.3329 | (3,2) | 56 | 1.001014093298 |
| 29 | large / y | 0.4679 | (5,1) | 71 | 1.001094008272 |
| 43 | large / y | 0.4679 | (1,1) | 67 | 1.001509472050 |

Full content-derived case IDs, statuses, metrics and paid fallbacks are retained
in the external independent report. Matched P/17 passed both W/17 failing
cases (19 and 101 updates). Matched P/29 passed all four W/29 failing cases;
P/43 also failed W/43's failing case. This supports a bounded generalist
objective rollback test, not a universal reliability claim. Relative to W,
P's failure counts were 0 versus 2 (seed 17), 2 versus 4 (29), but 2 versus 1
(43). P/17's new-panel two-scale means and zero-failure result are descriptive
repair evidence. Its earlier B4.2/B4.5 failures and the present W failure remain
unchanged; this cohort cannot be reused as fresh passing confirmation.

## 5. Complete time, storage and resource closure

| Stage | Final charged seconds | Peak RSS bytes | Frozen cap |
|---|---:|---:|---|
| references | 1,018.936141792 | 372,342,784 | 7,200 s / 2 GiB |
| screen | 10,754.716284292 | 1,376,616,448 | 43,200 s / 2 GiB |
| audit and closure | 754.793593666 | 1,492,172,800 | 7,200 s / 2 GiB |
| total | **12,528.446019750** | **1,492,172,800** | 57,600 s / stage RSS caps |

The original audit summary retains 397.766325875 s. Supplemental independent
checks increased its closed ledger to 736.998785376 s; final resource closure
increased it to 754.793593666 s without changing units, statuses or chain heads.
Use the final progress/resource-close receipt for the final charge rather
than rewriting the historical audit summary.

Whole-command profile floors were reference 915.06 s, screen 9,595.01 s,
audit plus independent checks 719.87 s, and closure 3.10 s: **11,233.04 s**
combined, covered by final charges. There was no additional floor deficit.
The full 1,248 one-second query recording allowances are charged in addition
to actual elapsed resource wall. A conservative five-second closure opening
charge covers receipt copying (measured 0.009034 s); directory sync and closure
allowances remain charged.

Screen outer query wall was 9,320.564360755 s and CPU 9,265.389037 s; legacy
phase sum was 9,318.755956749 s. Inclusive callback wall/CPU were
3.868298343 / 3.282476 s with 731,900 bytes recorded. Screen recording before
receipts summed 14.659234266 s; reference recording summed 1.140578493 s.
Maximum measured pre-receipt recording was 0.265512916 s, within the one-second
allowance; the live writer also checked receipt-inclusive recording. No
callback, serialization, fallback or failed-attempt time was subtracted.

Reference artifacts: 96 files, 43,058,125 bytes. Screen artifacts: 1,152 files,
540,433,176 bytes. Artifacts, logs, profile floors and both supplementary audit
sources remain external. All eleven B4.5 receipt hashes and the protected
B3 data/B4.1 fits/B4.2 screen/B4.4 progress hashes matched after closure.
Generated evidence and caches are not committed.

## 6. Next independent slice

**B4.7 is a bounded spatial-objective rollback and fresh reliability test.**
Use the unchanged P/17 generalist and same-seed specialist as a prospectively
fixed repair candidate, retain the full three-seed P panel and W/C/non-ML
controls, and freeze a new version, physically disjoint workload, quality and
complete-cost Gate before execution. Test the measured correction to the W
objective's non-specialist failures and extra refinement cost; do not merely
record a diagnosis and proceed to final evaluation. P/43's worse reliability
must remain reported, and no routing threshold search or tolerance relaxation
is justified by this result.

This next proposal is not frozen or executed in B4.6. A passing repair and
independent confirmation remain required before a separately compatible final
contract and B5. The original B3 final grid cannot be reused as fresh final
evidence for a later hypothesis. No final-ID/OOD, independent Linux ML
replication, or amortized acceleration claim is made here.

## 7. Repository validation

Before the evidence commit: `uv sync --dev --locked`, Ruff, mypy (58 source
files), all **679 tests** (425.02 seconds), and `git diff --check` passed.
Implementation validation and CI precede all production outcomes; evidence
CI and merge follow the complete failed-Gate report. The two user-owned
untracked duplicate documents remain untouched.
