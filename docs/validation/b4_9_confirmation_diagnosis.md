# B4.9 bounded confirmation failure diagnosis

Prepared: 2026-10-03 (America/New_York)

**Read-only diagnostic acceptance passed; B4.8 confirmation remains failed.**
All original failures, costs and the fixed P/17 primary are retained. The next
slice is B4.10, a separately frozen 20-update post-plateau polish probe.
Uniform remains default and final evaluation stays sealed.

## 1. Frozen source, complete reads and accounting

The [protocol](../planning/b4_9_confirmation_diagnosis_protocol.md) and guarded
reader were committed before individual outcome reads. Active identity:
`topolab.b4_9.confirmation-diagnosis.v2`; plan SHA-256:
`eb669182ad41bb0db4e34baa8f160218bd1fbd6289615b64afe583d44e0db46b`.
Implementation and evidence are in [PR #117](https://github.com/keith1117/TopoLab/pull/117).

Clean committed execution source: `714c0035fc227da25c3c8cdff7cc6ac918479aec`;
checkout: `/private/tmp/topolab-b49-source`. B4.8 source remains
`c185caffd5f3b3cd16b2f2f80948caee1e836784`. Eleven exact metadata receipt
bindings precede all journal/outcome reads. The original plan/release receipts
retain their exact indented serialization and SHA-256; execution metadata and
all units/artifacts additionally require canonical bytes.

The original v1 preflight at `9dfcd7512b1637dd3b85395578e7a35866782fd4`
incorrectly required compact serialization for the original plan/release
receipts. It stopped at the first metadata receipt, before any journal unit or
individual outcome/state. Its profile, traceback and 12.31-second charge remain
retained. V2 fixed only that metadata guard, with unchanged source hashes,
analysis population, hypotheses and caps, before individual outcome access.

All **96 references / 1,152 outcomes / 1,250 production audit journal units**
were read through exact source/context, hash-chain, size, checksum, assignment,
method/seed/route and recording-receipt guards. Compact per-case processing
avoided retaining the full density population. All **1,295 terminal quality
classifications**, **48 method/scale/direction strata** and **54 same-specialist
pairs** passed independent raw-JSON arithmetic audit. The audit imported no
TopoLab diagnostic helper or FEM solver. It reproduced every stop/quality cause,
trace summary, measured and hypothetical cost mean, phase/timing channel,
eligibility and complete failed decision at rtol/atol 1e-14. These arithmetic
tolerances do not change physical acceptance or repeat the prior FEM audit.

External evidence: `/Users/keith1117/Documents/TopoLab-data/b4-9-diagnosis`.
Runtime: Apple M2/arm64/Darwin 25.5.0, Python 3.12.10, one BLAS/OpenMP thread.
The analysis imported the existing pinned runtime but loaded no model or label
artifact. Independent audit and closure used only Python's standard library.

| Receipt/source | SHA-256 |
|---|---|
| Diagnosis | `c42b7eb640df96786820125b7570a7f68730edbb00478fe7efc5303e2c381a65` |
| Independent arithmetic audit | `5f4439a835b620817fed55f567a7a7ee3ab5d23dccbdbfa395ff9363f857c23b` |
| Resource closure | `bcd367d6ce163856ada0ecbb8875860a9cc237f55dcf6d5fb1ae856d468046da` |
| Reader source | `150f127fe66b78749149a972357ba30649474e248672961215c5d86f7ca43e5a` |
| Frozen protocol | `16e5d429ffaf5270fc20be42d12e15986a93c2ee4622a565a6ad1e12748b4735` |
| Independent audit source | `73159c8f72d5bd921bbe1aea1fca8832a1a5c12277f5a6572da09d9f945b02ea` |
| Closure source | `dc7e31aaaf323381dd15633e1c8bafb8aa4f944a968de42d330575bb27749a63` |

| Diagnostic process | Command wall (s) | Final charge (s) |
|---|---:|---:|
| Retained failed metadata preflight | 2.31 | 12.310000000 |
| Complete analysis | 23.10 | 30.891220750 |
| Independent arithmetic audit | 18.49 | 28.369520625 |
| Resource closure | 0.13 | 10.037705125 |
| Total | | **81.608446500** |

All command floors fit their charges, including startup/publication and each
ten-second close allowance. Peak whole-command RSS: **277,626,880 bytes**;
the frozen cap is 360 seconds / 1 GiB. All eleven B4.8 receipts and four protected
older indices remained unchanged. B4.8's final **14,105.836381712-second** charge
is unchanged; only the new diagnostic ledger records this analysis. There were
zero solver calls, fits, checkpoint/label byte reads and final-artifact reads.

## 2. Fixed primary and all P failures

Fixed P/17 already passed both charged scale bounds, every direction bound,
the matched C/W and non-ML comparisons, and total charged ratios. Its one
candidate quality failure and paid fallback alone block primary eligibility.
P/43 also has one failure; its better overall time cannot replace P/17.
P/29's four failures remain above its matched reliability bound.

| Seed | Scale/direction | Volume | Small-grid load indices | Updates / uniform | Stop | Compliance / uniform |
|---|---|---:|---|---:|---|---:|
| P/17 | large/y | 0.5413 | (3,1) | 40 / 89 | physical plateau | 1.001056679441 |
| P/43 | large/y | 0.4703 | (1,1) | 66 / 124 | physical plateau | 1.001060452864 |
| P/29 | large/y | 0.4703 | (1,1) | 62 / 124 | physical plateau | 1.001008965090 |
| P/29 | large/y | 0.4703 | (1,2) | 63 / 124 | physical plateau | 1.001017464028 |
| P/29 | small/z | 0.4703 | (3,2) | 18 / 80 | design change | 1.009677810789 |
| P/29 | small/z | 0.4703 | (3,1) | 18 / 80 | design change | 1.009613821730 |

Large-grid load indices are doubled. All six failures are converged, have
acceptable physical volume, and fail only compliance above **1.001**. None
ever crossed the quality bound in its complete scalar trace; each terminal
compliance is its trajectory minimum. Thus selecting an earlier retained state
cannot repair them. No P attempt failed at the 360-update cap.

The fixed primary's retained terminal design change is 0.015050699680 >0.01.
Its last ten physical changes have maximum 0.000884430529, while ten-update
relative compliance improvement is 0.000199265223 <=0.0002. The stop is
consistent with the frozen physical-plateau rule. Its eleven retained compliance
ratios decrease from 1.001256194980 to 1.001056679441, still above the 1.001
quality limit by 0.000056679441. This is a termination/quality-margin hypothesis,
not evidence of an incorrect FEM solve or a proven benefit from continuation.

On the same primary case, W/17 also stops at physical plateau and fails
(44 updates, ratio 1.001041325001), as do all three C controls. P/29, P/43,
W/29 and W/43 succeed. Removing spatial loss weighting improved the panel but
did not remove every terminal quality gap. The two P/29 small-z failures stop
through design change with roughly 0.96% compliance gaps; a physical-plateau
polish does not address those stop paths. Keep them as negative controls.

Across all twelve methods, the 47 retained failed candidates comprise 25
physical-plateau stops, 13 design-change stops and nine iteration-cap stops.
Thirty-eight fail compliance alone, eight fail both convergence and compliance,
and one C/17 failure fails convergence alone. All paid uniform fallbacks remain.

## 3. Measured cost, repeated specialists and hypothetical arithmetic

The original complete query sums reproduce B4.8: wall 10,576.639693614 seconds,
CPU 9,902.515790000 seconds, inclusive callback wall 24.522064476 seconds
(0.231851% of query wall), callback CPU 5.954687000 seconds and 824,817 callback
bytes. Recorded publication-before-receipt wall totals 22.986510800 seconds;
every query additionally retains its conservative one-second allowance.
No inclusive channel was subtracted or retimed.

All 54 pairwise C/P/W shared-specialist witnesses, metrics and statuses are
identical. **Zero** charged spread factors reach the frozen descriptive 1.25
flag; the maximum is **1.166904442**. This checks only the shared-specialist
repetitions, not all generalist or fallback timing variability. It neither
identifies causal checkpoint cost nor authorizes changes to measured costs.
The recorded timing and callback channels cannot clear a quality failure.

| P seed | Measured overall paired mean | Subtract stored fallback phases | Replace failed cost with uniform | Observed failures in every scenario |
|---|---:|---:|---:|---:|
| 17 | 0.744242428 | 0.720128482 | 0.723109159 | 1 |
| 29 | 0.794310598 | 0.767443254 | 0.787124073 | 4 |
| 43 | 0.708254832 | 0.694314057 | 0.699583049 | 1 |

Every scenario satisfies speed-only means; none changes reliability or primary
eligibility. These are hypothetical arithmetic scenarios, not guaranteed
pointwise lower bounds: replacing a failure with measured uniform cost can
increase a cell mean when the recorded uniform query was slower than a fresh
fallback. P/29's small-z mean increases from 0.879494530 to 0.882133003 in that
scenario. Stored legacy fallback phases exclude unseparated envelope overhead;
subtracting them never invents a fully measured fallback-free query.

P/17's 96 full charged queries total 728.841806208 seconds, including its
45.633617458-second legacy fallback phase. Mean candidate updates are 43.958333
versus uniform's 78.333333; reducing update counts did not ensure same quality.
All case/seed/stratum rows and phase channels remain in the external diagnosis.

## 4. Next slice and limits

The frozen ordered decision selects **B4.10: a fixed 20-update post-plateau
polish probe**. Freeze its new candidate-only query/termination contract before
numerical execution. Use unchanged P checkpoints, fixed P/17, specialist route,
starts and 360-update total cap; retain C/W/all P seeds and non-ML controls.
Focus the probe on large-y generalist physical-plateau stops. Specialist, z
and design-change stop paths retain their original policy and act as controls.
Apply the policy prospectively to qualifying candidate stops, rather than only
the known failed case. Trigger it from the candidate's own physical-plateau
signal; matched uniform compliance is not an online stopping oracle. Retain
original tolerances and charge every additional update, recording and fallback.

First use a bounded exposed regression sentinel covering the known primary
failure, other plateau failures, design-change negative controls and accepted
controls. Freeze resource, numerical-identity, quality and cost stop criteria.
If it fails, preserve that result and keep new cases sealed. If it passes,
execute only the separately preregistered physically disjoint development
cohort. Do not search polish lengths or seeds on this exposed panel.

The retained decreasing trajectories make continuation testable; they do not
prove that twenty further updates will cross the bound, remain converged or
preserve charged speed. The old failed cases/Gates remain failed. Passing
repair, independent confirmation and a compatible final contract remain
required before B5. B4.9 performs no continuation or candidate-policy change.

## 5. Source validation

Before the initial protocol/reader commit: locked dev sync, Ruff, mypy
(61 source files), all 709 tests (463.14 seconds) and `git diff --check` passed.
Before the active v2 reader commit: the same required checks passed, including
all 712 tests (443.18 seconds) and three added serialization-boundary tests.
Before the evidence commit, all five required checks passed again, including
all 712 tests (447.49 seconds). PR #117 must pass every applicable CI check on
its final head before merge. No numerical tolerance,
test tolerance or accepted historical state was changed.
