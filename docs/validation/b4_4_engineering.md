# B4.4 complete timing and bounded checkpoint engineering

Date: 2026-10-01 (America/New_York)

Status: **complete; bounded engineering acceptance passed**. All 76 queries and
100 candidate/fallback terminal states were retained and independently audited.
The unchanged models reproduced every original numerical witness and failed
status. Gate B4 remains failed, no primary/freeze was produced, uniform remains
the operational default, and B5 remains sealed. This recording experiment makes
no learned acceleration claim.

## Frozen source and scope

The [finite protocol](../planning/b4_4_engineering_protocol.md), runner and journal
were first committed at `d41e61bd1e7fde55a36cb8e3dd874901542f8f39` before any
B4.4 model read or numerical query. A test-only CI repair followed at
`00851dc2887b742a14155bd5b0a406a208d86c7c`. PR
[#107](https://github.com/keith1117/TopoLab/pull/107) passed all required CI before
merging. Execution used clean merged revision
`6a447c7435dc2e2f894a9972e35d6b2e863984b1`, the unchanged frozen numerical anchor,
locked dependencies and Apple M2 one-thread numerical runtime. A separate clean
checkout preserved the user's untracked workspace files.

The metadata-only plan hash is
`22426cd077eb5e9e0d34ebe245f9300efdcaedf7292a6d2d0124c1dfb11f8ebe`.
Protocol hash is
`35cb0e73e0ef4eb85e17b39d9c76637f9d61f04ed3a3300e3a2c6167f1718e1a`;
runner hash is
`510f882ecd523d0d4c9c6b50029ffdf6d37d4dae915f336d10804e3e04df90dd`;
journal hash is
`1491bdf4498094d6f5329868771df6d894f4085616b425674be6b132f377b0fd`.

Six already exposed cases cover two small-grid timing outliers, the three known
P failures and a high-volume large-y shared specialist. Only four unchanged
selected models, P/17, P/29, P/43 and S/17, were opened through the existing
selection/checkpoint provenance reader. No label, nearest-neighbor population,
new fit or final artifact was accessed. Both exact B4.2 input index hashes
remained unchanged after all execution, auditing and resource closure.

## Implemented timing and persistence

The new outer wall/process-CPU envelope covers the complete `evaluate_query`,
including initial/final callbacks, terminal-witness packaging, validation and
fresh uniform fallback. Legacy phase sums remain separate. Inclusive callback
wall/CPU and flush wall/count/bytes are retained without subtracting them from
query wall. Result serialization/publication, boundary progress, model loading,
input checks and independent terminal audits are additional charged stage costs.
The report exposes that residual instead of treating recording as free.

`topolab.b4.progress.v1` has a 4-KiB bound independent of outcome count. Iteration
callbacks never parse/serialize an outcome ledger. A nonblocking exclusive OS
lock owns the root; canonical units retain frozen ordinal/identity, context and
previous-record hash. Pending attempts are durable before execution. File and
directory fsync precede acknowledgement. On recovery, unfinished work may rerun
only its unchanged unit with prior cost and downtime charged; a published pending
unit is reconciled without rerunning the completed numerical query. Permanent
flags, attempt counts, prefix, charges and peak RSS are retained. Cadence begins
after the write, with a five-second scheduling threshold at safe callbacks.

Thirteen focused tests cover ownership, corrupt/missing prefixes, symlink and
changed-population rejection, both publication windows, charged downtime and
attempts, permanent resource/integrity stops, bounded writes after 48 large
records, post-write cadence and unphased query timing. An actual child process
exits before completion and its pending work is recovered. These tests establish
process-crash recovery; they make no storage power-loss claim.

## Complete matched numerical audit

Both arms executed nineteen queries per round on the same six cases. Round one
used legacy then compact persistence; round two reversed arm and learned-alias
order. Every query forced one flush on its first solver update, then used the
fixed cadence. The legacy arm additionally wrote a shadow fixture containing
the complete 48-case execution index with an unchanged prefix. Its cadence also
uses end-of-write time. The fixture never wrote the original root and does not
represent a new authoritative B3 ledger or deployment freeze.

All **76/76** complete numerical outcomes were bit-identical to their respective
retained B4.2 outcomes after removing only timing fields: routes, failure codes,
metrics, complete scalar traces, recent density states, terminal displacement /
reaction vectors and convergence flags. Every candidate and fallback terminal
state received a live independent FEM re-solve, then another streamed independent
audit rechecked all **100/100** states, canonical bytes, chain, source, context,
case/method assignment, phase/wall relationships, callback byte bounds and costs.
No production restart or interrupted unit occurred; attempted/completed counts
are both 76 and all operational results passed terminal quality.

The three known failed P attempts remain failed: P/29's converged large-y
compliance gap, P/29's 360-update large-z nonconvergence and P/43's converged
large-y compliance gap. Their P-without-S duplicates, both rounds and both arms
retain the same statuses. Thus each arm has twelve failed candidate attempts and
twelve fully paid, successful fresh uniform fallbacks. No failed outcome was
removed, relabelled, given a larger iteration budget or replaced by a faster repeat.

## Frozen engineering acceptance

| Inclusive measurement | Legacy arm | Compact arm |
|---|---:|---:|
| Complete queries | 38 | 38 |
| Query wall seconds | 1,330.947358 | 993.045548 |
| Query process-CPU seconds | 1,302.412011 | 977.210408 |
| Callback wall seconds | 334.712875 | 0.588077 |
| Callback process-CPU seconds | 322.410755 | 0.454919 |
| Flush-callback wall seconds | 334.563532 | 0.443534 |
| Callbacks that wrote any bytes | 422 | 217 |
| Bytes written inside callbacks | 658,078,995 | 104,474 |
| Failed candidates / successful paid fallbacks | 12 / 12 | 12 / 12 |
| Independently audited candidate/fallback states | 50 | 50 |

The compact/legacy callback-wall ratio is **0.001756960**, below the frozen 0.25
bound: **99.8243% less callback wall**. Complete-query wall ratio is
**0.746119327**, below the frozen 1.05 nonregression bound: **25.3881% less query
wall in this sentinel**. Both use all counterbalanced repetitions. The closed
76-unit progress file is 458 bytes; every write is bounded by the 4,096-byte
source check and the independent callback-byte audit passed.

Flush wall means the whole callback duration on callbacks that wrote, including
resource bookkeeping. The legacy arm also maintains compact resource progress,
so its write-callback count includes compact-only and full-index writes; 422 is
not a count of full-index rewrites. Wall and process CPU are inclusive measured
channels, not estimates of host scheduling or suspension.

This deliberately stressed fixed 48-case prefix and forced first-update flush
establish the persistence mechanism and numerical identity. They do not estimate
unobserved checkpoint costs inside historical B4.2, repair its scientific Gate,
or establish learned speed over matched uniform. Later learning experiments must
adopt the complete timing/cost boundary under a new frozen identity and obtain
fresh development and independent confirmation evidence.

## Resource closure and external receipts

Generated evidence stays outside Git at
`/Users/keith1117/Documents/TopoLab-data/b4-4-engineering`.

| Charged component | Seconds |
|---|---:|
| Complete execution, live audits and close allowance | 2,363.842623 |
| Supplemental independent audit and launch/close allowance | 37.794953 |
| Resource reconciliation and receipt/close allowance | 5.016409 |
| **Final stage charge / frozen cap** | **2,406.653985 / 7,200** |

The 76 query envelopes sum to 2,323.992906 seconds. The execution-stage residual
is **39.849717 seconds**, retaining input/model setup, independent live audits,
result serialization/publication, boundary recording and its close allowance.
Whole-command profiles are 2,356.65, 30.07 and 2.00 seconds, totaling
**2,388.72 seconds**, below the final charge. Peak RSS is **705,953,792 bytes**
against **2,147,483,648 bytes**. Closed progress has no pending work or permanent
resource/integrity flag. No original B4.2 index, artifact or status changed.

| Evidence | SHA-256 |
|---|---|
| Execution context | `9eb4947fbefbf230b8b1a204d04b8735c7650bb3a258af5377709a7fcb506925` |
| Immutable execution summary | `30b3d13d6de9cb014bf112f04f7cd3d45ce76a31232fdfd4e5f55ed6742eb939` |
| Complete unit-chain head | `68903561bcd7d3e7975617761ddb2ac06af2db1af510cfe24f6c18e3702bf50e` |
| Independent streamed audit | `544439cec4565fd86cff13370ea363e751646924efa313d61129331bb64032a9` |
| Independent audit source | `3fffc5b26d746d71adbea0652b9de7a26dc4cd94409be031d80ec8c361cd7af1` |
| Resource closure | `e36d2ec7577a0ebc8bd037804d844d82fb2dc8ab6620e6603df33e975e0fd831` |
| Final charged progress | `4ae7f2dc48544f35a67fdec2aa67f0768a42dcb644e21383672acbc42b7c20fc` |

The external `audit_receipts` directory retains the metadata plan, independent
scripts, profiles and logs. The immutable execution summary keeps its original
execution charge; the final progress includes supplemental audit/closure charges.

## Required validation and next slice

Before the runner commit, locked sync, Ruff, mypy (55 source files), all **659
tests in 483.66 seconds** and diff checks passed. The first push quality check
passed; its PR run retained 658 passing tests and one existing wall-clock heartbeat
test failure. A 300-ms test lease plus blind 700-ms sleep depended on CI scheduling.
The test now advances a controlled clock by 200 ms only after each actual
successful persisted renewal, crossing the initial lease in four steps before
opening the observer. Production lease/heartbeat code, numerical tolerances and
this protocol are unchanged. Before that fix, all required validation passed
again, including **659 tests in 429.34 seconds**. Its two quality CI checks passed
in 7m24s and 14m12s; frontend and Linux smoke also passed before merge. The failed
CI history remains retained. Before the evidence commit, locked sync, Ruff,
mypy (55 source files), all **659 tests in 425.82 seconds** and diff checks
passed again.

The next independent slice is **B4.5: separately freeze and implement one bounded
sensitivity-weighted terminal-design generalist intervention, retain the fixed
specialist and unchanged numerical quality limits, and train/evaluate on fresh
development evidence under the new contract**. This is an untested learning
hypothesis, not a passed learned Gate. The complete new B4 Gate and independent
confirmation must pass before B5. Report each slice and wait for new instruction
before starting the next.
