# B4.11 complete read-only polish failure/cost diagnosis

Date: 2026-10-04 (America/New_York)

**Diagnostic acceptance passed. B4.10's scientific Gate remains failed.**
The independent audit reproduced all 132 terminal classifications, 24
prepolish certificates, 48 strata, nine shared-specialist pairs and all fixed
cost scenarios. The sole new fixed-P/17 failure is loss of its terminal
convergence certificate after twenty updates, despite better compliance.
The ordered decision recommends **B4.12: bounded candidate terminal-witness
preservation probe**. No numerical repair, acceleration or final access is
established here; uniform remains the operational default.

## Frozen execution and complete access

The [protocol](../planning/b4_11_polish_diagnosis_protocol.md) and three
stdlib-only scripts were merged in [PR #120](https://github.com/keith1117/TopoLab/pull/120)
after all applicable final-head CI passed. Tested head:
`bed29a8b74b3a13f5674e9f1d722555063b74fd4`; merged execution source:
`eb248a62829f4fdd3d8f1508421d7e91352da172`, merged at
`2026-10-04T07:35:17Z`. Its Git tree exactly matches the tested head;
all `src` files remain identical to B4.10's execution source
`fd13aa1c85a05e638ea02e74712c216319c7488d`.

Identity: `topolab.b4_11.polish-diagnosis.v1`; frozen plan SHA-256:
`3c831763197e8e80f3295f8df085ed6339b23e5917ed69f96ca97fd6198b324f`.
Execution used a clean detached checkout at `/private/tmp/topolab-b411-source`,
Python 3.12.10 and one BLAS/OpenMP thread. Metadata planning created no
output. Explicit analysis wrote only the new external root:
`/Users/keith1117/Documents/TopoLab-data/b4-11-polish-diagnosis`.

All fourteen frozen B4.10 metadata bindings matched before and after analysis;
all eighteen protected historical metadata/index hashes remained unchanged.
Original assigned journals were closed and complete:

| Population | Count |
|---|---:|
| Uniform reference units | 9 |
| Fully charged query units | 108 |
| Prior numerical/input audit units, metadata only | 119 |
| Prior policy audit units | 117 |
| Durable reference/query recording receipts | 117 |
| Independently reclassified reference/candidate/fallback states | 132 |
| Before/after P generalist witness checks | 24 |
| Fixed twenty-update continuations / retained added updates | 12 / 240 |
| Unchanged query identities, using closed policy proofs | 96 |
| Unchanged reference identities, using closed policy proofs | 9 |

The prior complete 12-checkpoint/528-label audit was read as metadata only.
There were **zero solver calls, continuations, fits, new labels,
checkpoint/label byte reads or final-artifact reads** in this diagnosis.
The earlier independent numerical audit supplies FEM/filter verification;
the new auditor independently recomputes raw-state certificate, volume, quality
and cost arithmetic without importing B4.11's diagnosis arithmetic helpers.
All 48 B4.10 fresh cases remain sealed, with no fresh directory or outcome.

## The regression loses convergence evidence, not compliance quality

On case `tlcase-v1-033f380c2181d9d1f94fc7f3d4b4a6507992c5e1a5004018bff779ca92add82a`
(large-y, volume 0.4703, load node 724), fixed P/17 originally passed after
77 updates and received exactly twenty more. The retained values are:

| Terminal evidence | Before, 77 updates | After, 97 updates |
|---|---:|---:|
| Compliance / matched uniform | 0.9998987727123478 | 0.9994990756607028 |
| Last design change, bound 0.01 | 0.022756876754132405 | 0.029572304078613665 |
| Last-ten maximum physical change, bound 0.01 | 0.0031079945412562093 | 0.0022486112909738676 |
| Last-ten relative compliance gain, bound 0.0002 | 0.0001999755570853251 | 0.0002063051569921597 |
| Physical volume error, bound 0.005 | 2.7593668461278753e-9 | 3.602070752783959e-9 |
| Physical-plateau certificate / converged | true / true | false / false |
| Quality success | true | false |

Compliance improves and both compliance/volume quality bounds pass, but neither
unchanged convergence certificate passes at the fixed endpoint. Its only
quality reason is `not_converged`; the stop is
`post_polish_nonconvergence`, **not 360-update exhaustion**. It pays a fresh
uniform fallback: complete charge 40.5434028749587 seconds versus matched
uniform 22.81564566702582 seconds, ratio 1.7770000229953526. The legacy fallback
phase alone is 22.09233991696965 seconds; all remaining envelope and recording
cost stays charged in the optimistic scenario.

All four known large-y P failures remain repaired. Both P/29 small-z negative
controls remain failed at their unchanged design-change stops. No status,
reference, witness, iteration limit or quality/convergence tolerance changed.

## Complete costs and remaining refinement burden

The four fixed-P/17 large-y generalist targets retain these complete costs:

| Case prefix | Volume / load node | Updates before → after / uniform | Charged ratio | Fallback |
|---|---|---|---:|---|
| `033f380c` | 0.4703 / 724 | 77 → 97 / 124 | 1.777000 | yes |
| `080d09f0` | 0.3353 / 824 | 125 → 145 / 86 | 1.627662 | no |
| `838e2ccc` | 0.4703 / 1374 | 72 → 92 / 124 | 0.767265 | no |
| `d9dc3124` | 0.5413 / 824 | 40 → 60 / 89 | 0.717580 | no |

The accepted low-volume target remains expensive without fallback. Fixing
the convergence regression therefore does not demonstrate general acceleration.
All three frozen scenarios preserve the observed failure:

| Four-target scenario | Cost, seconds | Mean paired ratio | Ratio of sums | Observed failures |
|---|---:|---:|---:|---:|
| Measured | 97.51096245797817 | 1.2223768842168437 | 1.2263418349849644 | 1 |
| Fallback-free, legacy fallback phase removed only | 75.41862254100852 | 0.9803024297022989 | 0.9484986059781374 | 1 |
| Failed query assigned matched uniform cost | 79.78320525004528 | 1.0281268784680055 | 1.0033895662704266 | 1 |

Matched uniform costs total 79.51368833403103 seconds. Fallback-free arithmetic
leaves narrow mean-ratio headroom: its constant additional guard-cost budget
is at most **0.38250386136229386 seconds per target query**, taking the smaller
of mean-ratio and total-ratio slack. This is an optimistic diagnostic bound;
no safeguard was timed, no failed status was relabeled and no Gate passed.
Assigning the failed case to uniform still exceeds both target cost bounds.

All 108 queries retain wall 1,519.1172224968905 seconds, CPU
1,500.5847710000005 seconds and legacy phases 1,518.8406216615112 seconds.
The one-second recording allowances add 108 seconds. Inclusive callbacks total
0.8274507598252967 wall seconds, 0.6532359999997936 CPU seconds and 125,627 bytes;
none were subtracted from complete measured cost. Full row/phase/48-stratum
tables remain in the external diagnosis.

All nine C/P/W shared-specialist pairs have identical states, metrics and
statuses. Maximum charged spread is 1.0278882356640309; zero reach the fixed
1.25 descriptive flag. This does not correct timings or remove a failure.
All method successes/fallbacks remain: uniform 9/0, heuristic 9/0, NN 6/3,
C17 6/3, C29 7/2, C43 8/1, P17 8/1, P29 7/2, P43 9/0,
W17 7/2, W29 9/0 and W43 8/1. P/43 cannot replace fixed P/17.

## Resource closure and profiling limitation

Closed diagnostic charge is **59.88 seconds**, below 360 seconds; peak retained
kernel RSS is **92,798,976 bytes**, below 1 GiB:

| Process | Complete wall | Internal charge | Closed charge | Kernel RSS bytes |
|---|---:|---:|---:|---:|
| Diagnosis | 4.74 | 14.700515125063248 | 14.74 | 89,882,624 |
| Independent arithmetic audit | 5.14 | 15.035578749957494 | 15.14 | 92,798,976 |
| Closure, full cap reserved | 0.15 | 10.035188709036447 | 30.0 | 33,144,832 |

The initial outer `/usr/bin/time -l` utility exited 1 after successful analysis
because sandbox `sysctl kern.clockrate` access was denied. Its complete wall
measurement and original stderr are retained in
`profiles/diagnosis_native_partial.time`. It did not print outer RSS. The
normalized diagnostic profile uses that wall and the executed Python process's
retained kernel `RUSAGE_SELF` RSS; `audit_receipts/profile_provenance.json`
records both origins and hashes explicitly. **The diagnosis was not rerun or
rewritten.** This diagnostic RSS channel differs from the outer native profile.
The independent audit and closure used permitted read-only native profiling;
their kernel/native RSS agree, and the larger independent-audit peak determines
the slice peak. All diagnostic work and the profiler exit are included in the
4.74-second command floor and its ten-second allowance.

Closure conservatively charges its complete thirty-second reservation. The
post-exit verification proves its 0.15-second wall +10 and internal elapsed
+10 fit the reservation; its native RSS is below the retained peak. No failed
analysis or audit attempt was retried. B4.10's 2,106.1092707920307-second and
B4.8's 14,105.83638171223-second charges remain unchanged. The raw profiling
limitation is retained rather than presented as a complete native RSS profile.

## Receipt bindings

Paths are relative to the external diagnosis root:

| Receipt | SHA-256 |
|---|---|
| `audit_receipts/plan.json` | `21e078f4032302fab64499643523a84a29b6fb3b172db3bdf71e5074128decaf` |
| `audit_receipts/production_release.json` | `135f1d2f0d1a45e63f855f5e9da049ae6d1568085bd82805289d2aa15b2751d6` |
| `diagnosis.json` | `48a539ae7f76c5203c1ca9edd364f98094e1d5107466c90acf9f7a7780851ef0` |
| `independent_audit.json` | `8fe367af68014406ef911b703b80d362ddb822c06469d7f21ad2f289c2d35cf3` |
| `resource_close.json` | `4839612170f235d9d594f3ee718ccb3668808374d33198120ffa5bf8ca892fdc` |
| `audit_receipts/profile_provenance.json` | `8e983192eba8269fc8cbf1f6e7c761099656fea1c68d6bb591ef5d9dd7dd22a9` |
| `audit_receipts/closure_profile_verification.json` | `19f26cef716a2d68818493d71d16afd5ba073d2169d06cea49ca235d1a30f6a0` |

Reader, independent auditor, closer and protocol source hashes are respectively
`e93f9e9c45365cfb8a6d33a154217dd3fd51b232a160d7e755dcbb0f76c235c7`,
`9006c6228b284fccb0792855ba69dced9daa4a0f833e3e25e46ffe8b40bbe295`,
`d87e05bdfe55d480f9be831024d9025061d2244a2f9510e1123d0dcfdbe2676c` and
`ec35d1e0401fd8de92cb76b2179d7275e8d07952fc2091bb71613e1078a99860`.
Source final-head CI receipt SHA-256:
`7b174a0497091821fb81d8b7c549f2c4ed8a33a4f4e2b92391982ad220d0ccbb`.
The production release binds the clean source, complete source manifest and
CI-before-merge timestamps. Execution commands and evidence-release receipts
are retained separately from this frozen production release.

## Ordered decision and next slice

The predeclared preservation condition holds: exactly one previously successful
fixed-P/17 witness regressed after twenty updates, nonconvergence is its sole
quality reason despite improved compliance, and both fallback-free target
ratios are strictly below 1. The next independent slice is **B4.12: bounded
candidate terminal-witness preservation probe**. Its separate contract must
freeze a candidate-only choice rule, paid guard costs, exposed regression
sentinel, fresh physically disjoint development cases, retained P/W/C seeds
and non-ML controls, finite caps and stop rule before execution.

The hypothesis retains the original candidate's own converged witness when
its fixed-polish endpoint loses convergence; it uses no matched-uniform
compliance oracle. It changes no polish length, threshold, seed, checkpoint,
start, route or total iteration cap. This slice does not implement it.
No exposed-cohort length/threshold search or retrospective seed replacement
is authorized. A passing repair, separate independent confirmation and a
compatible final contract remain required before B5. All original failed
Gates and every historical failure are preserved; final evaluation stays sealed.

## Required software validation

Before the initial source commit: locked dev sync, Ruff, mypy (63 source
files), all 746 tests (465.61 seconds) and `git diff --check` passed.
The plan JSON round-trip check and all 23 new tests passed separately after
its serialization fix. Before the final preproduction closure commit the
same required checks passed, including all 746 tests (467.10 seconds).
Final-head CI passed before PR #120 merged. New tests cover zero-read planning,
changed/hash-addressed evidence, symlink and overlap boundaries, certificate
loss despite compliance improvement, unchanged quality limits, preserved
failure/cost arithmetic, fixed-primary identity and prospective decision rules.
No numerical tolerance was loosened. Evidence-only commit validation and its
CI-before-merge release are retained after this diagnostic execution.
Before the evidence-only commit, locked dev sync, Ruff, mypy (63 source files),
all **746 tests (465.11 seconds)** and `git diff --check` passed. This evidence
update merges only after all applicable final-head CI passes.
