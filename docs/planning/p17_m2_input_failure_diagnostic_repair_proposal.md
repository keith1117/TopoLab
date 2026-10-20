# M2 input failure diagnosis and minimal recording repair — proposal

Date: 2026-10-20 (America/New_York). Status **PROPOSED_NOT_AUTHORIZED**.
Proposal identity: `topolab.v2.p17-m2-input-failure-diagnostic-repair.proposal.v1`.
[Structured companion](p17_m2_input_failure_diagnostic_repair_proposal.json).
English controls; both files describe the same finite proposal, not an executable
plan, an R/v4 identity or a scientific Gate. The current owner instruction grants
**documentation only**. It grants none of the future reads, implementation or
diagnostic execution below. No independent author is commissioned by this file.

中文要点：分开核对第12份元数据身份变化与失败记录缺陷。拟议最小方案不重读该原文件；历史原因可继续
UNKNOWN，公开fixtures上的记录修复可独立验收。拟议实现2小时、不同作者审查1小时；仅F加一轮90分钟
回归/发布。如另批D，增加双方同一10分钟诊断窗口和一轮90分钟结果发布。全部待批准；旧失败、费用、配额及封存不变。

## 1. Baseline and two separate questions

Recovered assigned ec0b worktree: clean detached
`85644c423ab7151c22dd861639369642ed630f1a`; remote main agrees, no open PR.
[PR209](https://github.com/keith1117/TopoLab/pull/209) is merged; all four
[exact-main CI39399796173 jobs](https://github.com/keith1117/TopoLab/actions/runs/39399796173)
passed. The old [protocol](p17_m2_input_export_readiness_protocol.md),
[actual report](../validation/p17_m2_input_export_readiness.md#actual-rv3-execution--stopped-during-metadata-registration)
and [independent report](../validation/p17_m2_input_export_readiness_independent_review.md)
remain unchanged. They establish:

| Question | Established observation | Missing evidence / limit |
|---|---|---|
| D: why did metadata attempt12 stop? | R0 reached post-read `fstat`; `(st_dev, st_ino, st_size, st_mtime_ns)` differed. There were12 attempts,11 completed byte/hash rows/2619248 bytes. | Neither tuple nor returned byte count for attempt12 was retained. Differing member, mechanism, failed-read bytes and lock/sleep causation remain UNKNOWN. No evidence establishes damaged contents. |
| F: why is the failed execution incompletely recorded? | Controller exit1 prevents the complete supervisor receipt; finalizer expects that receipt and exits1. JS rejects incomplete completion before deriving raw wall; Python retains37.579999924s but rejects incomplete RSS coverage. Shared replay finds null-vs-derived-wall mismatch. | Full failed-role RSS remains UNKNOWN. Actual outer exits1/1 and source STOP remain valid. Known wall and partial facts must survive rejection in future versions. |

The target locator is
`b3-v1-fits/artifacts/selection/62245b313b64d17fdd5d5ee2e77dcf28158dd4aea098810e11a910a1ba4ffb09.json`.
It is a documentary locator, **not a permitted path to stat, open or reread**.
The three later source roles were CLOSED_UNLAUNCHED, not three failed executions.
No historical H/17 scientific run occurred; neither algorithm failure nor sleep
has been established as the cause of this STOP.

The strict before/after identity check is an existing hard requirement. Retaining
which fields changed is the proposed small observability improvement. Obtaining
a retrospective kernel/filesystem proof, proving sleep impossible, recovering
lost tuples, or guaranteeing every allocation in advance is **not required** by
this proposal. D may close UNKNOWN without preventing fixture-only F acceptance.
Neither outcome admits real inputs or a new R attempt.

## 2. Future permissions: exact, read-only and separately authorized

The current documentation slice's old external read/stat set is **empty**. Only
versioned documentation/source and ordinary software/publication records are
used now. The following exception would require a later explicit owner grant:

| Future reader | Permitted source and fields | Bound |
|---|---|---|
| Executor, once per literal file | The five R/v3 receipts below: complete-byte SHA verification, then only identity, attempt/count/byte summaries, failure stage/reason, event clocks/argv/exits, available RSS/cleanup and cost fields | Each <=4MiB; aggregate <=16MiB; five files maximum; no reread. Read-only nofollow traversal, regular files, before/after identity checks; mismatch STOP. |
| New different author | New copies of those five receipts, bound to their published SHA and capture manifest; independently parse/reconcile facts, not the executor's conclusion | Same per-file/aggregate limits; one pass. Does not independently reread the historical originals. This nonblind exposure is disclosed. |
| Executor, one optional query | Local sleep/wake event types/timestamps only, from `2026-10-20T08:36:30Z` through `08:38:15Z` (04:36:30–04:38:15 EDT); no full log history | One query, <=30s and <=1MiB output, within the common600s diagnostic window. No sudo, installation, power-setting change, remote log upload or retry. |

All receipt paths are relative to the literal external root
`/Users/keith1117/Documents/TopoLab-data/p17-m2-input-export-preparation-v3`.
Hashes below are copied from committed reports, not reverified in this slice.

| Literal receipt | Required SHA256 |
|---|---|
| `launch_plan.json` | `7252429be4107800f4f7dc889c0a9432ab059eb1953198e2f8ca12850492d0fe` |
| `exporter-r0/failure.json` | `54563ec4b3cd71c74a1282a933cfbc906550d13d2a59c3b84b05b9c720c1f518` |
| `exporter-r0/source-read.jsonl` | `4f82b6e2c2faac2686ec99d41e37479397c89a9687ec192139246ac11d4a34f3` |
| `STOP.json` | `2279221e6fbf99ee2320eee73487cebb7aab47c4508582f546a62b1711a0a7b6` |
| `result-publication/trusted-frontier-packets.json` | `7840e4446adf47056e7144e1fa43f6cfc586a6dde1739523ae97ae8aad0c5dcb` |

No recursive enumeration or pointer following; no old native profiles, backup
members, other receipts, raw inputs, checkpoints, labels, packets, model/trajectory
parsing, xattrs, cloud-account configuration or seals. Hashing these receipts
does not grant semantic access to any incidental embedded source payload. An
unexpected schema/content stops that parse without following a pointer.
Recorded argv and paths are inert evidence text; never execute a receipt-supplied
command or open its source pointers.

The optional OS query must be frozen against public documentation before use and
enforce the time/event restriction at selection, not by exporting all history
then filtering it. If that restriction, permission or retained events are absent,
record `UNKNOWN_LOG_UNAVAILABLE` and close D; no alternative probe or escalation.
Only event time/type and nonidentifying reason classification enter the new
report. A temporal overlap is association, not proof that sleep changed a file;
no event found is not proof of no sleep. The reviewer reads the same bounded new
export; no second OS query. No old target metadata query is included, since a
current `stat` cannot reconstruct the missing historical tuple.

## 3. Minimal prospective source changes (F), public fixtures only

Future code work is limited to the four existing tools and their existing test
modules: `scripts/p17_m2_input_export.py`,
`scripts/p17_m2_input_export_control.py`,
`scripts/p17_m2_input_export_dispatch.js`,
`scripts/p17_m2_input_export_independent.py`, and
`tests/test_p17_m2_input_export*.py`. No FEM, H schedule, model, optimizer,
resource kernel, dependency, backend, provider or workflow change is proposed.

1. Reader: retain attempted ordinal/path, declared/before/after tuples when
   available, exact check stage, differing field names, returned byte count or
   UNKNOWN, and exception. Emit the failure row before propagating STOP. Keep
   current nofollow, limits, byte/SHA and all identity predicates unchanged.
   No second read, tolerance, retry, snapshot replacement or source repair.
2. Supervisor/finalizer: preserve already available native profiles, actual
   wait4/nonzero exit, own high-water/flush and cleanup facts on the failure path.
   Missing supervisor success must not erase other observations or prevent a
   bounded failure completion. Missing components remain explicitly UNKNOWN.
   Record original domain failure separately from evidence/serializer defects;
   do not manufacture a complete RSS envelope from partial peaks.
3. JS boundary and Python independent replay: first validate identity and the
   supplied raw event stream as far as independently possible, then retain valid
   T0/T1/span, actual exits and the known cost lower bound even if internal
   completion/resource evidence is incomplete. Untrusted, missing or malformed
   events remain labelled partial/UNKNOWN, never certified by an internal flag.
   Reconcile the same decisive fields on failed packets; preserve the original
   source cause and list secondary defects instead of replacing it.
4. Keep execution outcome separate from measurement completeness. A deliberately
   failing payload remains STOP even if its entire RSS/exit chain is recorded.
   Internal records never certify their future exit. The existing finite trusted
   external-tool return observes the final serializer's actual return; no extra
   observer-of-observer chain or kernel/allocation proof is introduced.

Version new failure records explicitly and bind the new diagnostic/software
identity `topolab.v2.p17-m2-input-failure-diagnostic-repair.v1`. Historical v1/v2/v3
contracts, reports, receipts and source revisions stay frozen and reproducible.
Evolving those four working source files in a future commit does not patch a
stopped execution. New public-fixture/diagnostic entry rejects all historical R
roots as execution or output destinations and cannot dispatch any R source role;
only D's five-receipt read-only exception may use its literal historical input
root. No R/v4 plan/root or source-successor permission is created.

## 4. Obtainable acceptance and independent review

Appoint a **fresh different author**, NOT_YET_APPOINTED, only under a later grant;
no closed v1/v2/v3 reviewer or unused time is reactivated. Before reading the patch,
that author writes its expected failure matrix/calculations from the old committed
specification and new public fixtures. Then cross-review is explicitly nonblind.
It may reuse disclosed independent algorithms but not a primary PASS oracle.

New tiny fixtures must cover: mtime-only/size changes, replacement before open,
read exception, payload exit1, absent supervisor receipt, serializer failure,
missing helper/RSS, malformed/missing/out-of-order raw events, missing actual
exit, cap overrun, and uncertain cleanup. Include an unchanged-file success
control. Deliberately injected errors are expected software test cases, never a
retry of R. No historical bytes/shape-derived scientific fixture is used.

Acceptance requires independently checked raw event spans/exits, unchanged strict
source rejection and byte counters, retained primary/secondary failures, and
JS/Python agreement on valid facts and explicit UNKNOWNs. With enough evidence,
the failing-payload fixture has complete empirical RSS/exit evidence <=4294967296
bytes **while its domain outcome stays STOP**. Removing a mandatory component
must keep acceptance closed, not turn missing memory into0. Preserve immutable
FULL charging and `max(whole_wall+10, independently reconciled minimum)<=FULL`;
any overrun is additionally recorded, never clipped/refunded. No numerical
tolerance, protection, source predicate or scientific threshold is relaxed.

D acceptance is an evidence-bounded finding **or explicitly unresolved UNKNOWN**;
it need not establish causation or reconstruct the old failed-role RSS envelope.
That historical RSS remains UNKNOWN; it is not a prerequisite for accepting a
bounded D finding. F acceptance is public software only, independently
reviewed and regression-tested. A failed F fixture/review or mandatory resource
UNKNOWN prevents acceptance of F; an unresolved D cause does not. Neither is
`PREPARATION_COMPLETE_SOURCE_BOUND`, formal B preflight or P/17 repair.

## 5. Proposed new budget and order — none granted yet

Only the current M2 and existing GitHub CI. No installation or purchased capacity.
Amounts are new ceilings, not old unused balances. No separate scientific budget.

| Future phase | Executor maximum | Different author maximum | Start / charging boundary |
|---|---:|---:|---|
| F public implementation, fixtures, substantive review and source-report drafting |7200s (2h)|3600s (1h)| Each starts at that author's first preparation tool; continuous, includes debugging and directed waits; ends before source publication. |
| Source regression/protected PR/main-CI publication |5400s (90min)|0 additional CI-wait duty| Starts at first mandatory source check; includes every check, PR/push/main job wait and freeze filing. |
| D once-only diagnosis and independent new-copy review |600s (10min)|600s (10min), same common window| Starts only after source/main CI readiness and both authors ready; includes independent public I/O preflight, capture, optional OS query, review and shutdown. |
| Result regression/protected publication and final filing, if both F/D were granted |5400s (90min)|0 additional CI-wait duty| Starts at D close or post-source pre-D STOP/omission; includes result drafting, five checks, all CI and final observed return. |
| Total disjoint author-phase maxima |18600s (5h10m)|4200s (1h10m)| No phase/author transfer, pause, reset or hidden directed waiting. |

If **F only** is granted initially, its source PR already contains the final
fixture/review report and D UNRUN disposition: no D phase or second result PR.
Its smaller ceiling is executor12600s (**3h30m**, including one90min publication)
and independent3600s (**1h**). The full table applies only if both F/D are granted;
an omitted phase has0 cost/closed allowance and cannot fund extra implementation.

The common D window additionally has one immutable **FULL600s total diagnostic
I/O charge** if entered, covering both authors, all reads/helpers/gaps/serialization
and observed final return; if not entered,0. This overlaps the author view and
is not added twice to project cost. New-receipt replay is not one of R's six roles
or a debit against its closed1860. Actual diagnostic wall+10 must fit600; retain
known actual overrun as well. Before any historical receipt read or OS query, a
once-only independent **public-fixture I/O preflight**, capped120s within600,
must pass complete empirical RSS/exit/cost checks on the frozen new tools. This
is diagnostic software entry, not formal B or R. Preserve4GiB and independent
preflight. Failure closes D without historical reads; no second preflight.

Before D activation: explicit grant, appointed author, frozen literal commands,
roots, five hashes, actor/clock/charge plan, clean locked merged source and all
four exact-main CI jobs. New evidence root is the literal
`/Users/keith1117/Documents/TopoLab-data/p17-m2-input-failure-diagnostic-v1`;
it must be absent. Existing root STOP; no deletion/name search/old backup reuse.
Raw copies, logs, tuples and event packets stay external; only reviewed summaries,
contracts, source/tests and report hashes enter Git. No host/device IDs or secrets.

Reserve the last120s of each author/publication phase and last60s of D for
shutdown/final recording; start no new work that cannot fit its full known bound
plus reserve. Actual observed closure must fit, not just an internal timestamp.
If CI is still pending at a phase cap, retain pending status and stop publication
work; no bypass, automatic extra10min, rerun or clock transfer. A later grant
would be separately recorded, never retroactive. F may be published while D stays
UNRUN/UNKNOWN; the F-only option ends there. No partial R prefix follows. Unexpected software failures may be
debugged only in the unfrozen public phase within its cap; first frozen D failure
closes D without retry or patch-and-continue.

Each commit requires all five [policy checks](../repository_policy.md#required-checks),
reviewed-path staging/all-upload guard, latest-head all-four PR CI, protected
merge and exact-main all-four CI. Source publication precedes D; result publication
preserves its failure/UNKNOWN too. No environment workflow dispatch or CI used
to probe a host. Paid expansion/new purchases USD0; electricity/subscription/CI
fees remain UNKNOWN_NOT_ZERO. Record actual author/command/CI job wall and failed
attempt costs separately; overlapping views are not summed twice. No old ledger
or quota is reset. These future phase caps do not apply retroactively to the
currently authorized documentation proposal, whose regression/publication costs
are recorded separately.

## 6. STOP, preserved history and the only next decision

No explicit grant/appointed reviewer, scope or hash/identity/schema mismatch,
symlink/path escape, prohibited source access, unexpected extra file, missing
mandatory evidence, resource/cap breach, cleanup uncertainty or frozen mutation
stops the dependent track. Do not retry/replace the original file, repair metadata,
disable sync/sleep, widen OS logs, choose a substitute input/provider, reopen R,
run B/C or start an automatic successor. Optional log unavailability closes D
UNKNOWN; missing historical tuples cannot be reconstructed by assertion. D's
unresolved cause alone is not a STOP on independent public F development.

Retain FULL_V2_OPEN_NO_ADMITTED_ROUTE, fixed unrepaired P/17, uniform/science
pause, full-fit PENDING4GiB, native empirical acceptance/independent preflight;
separate B guest adoption/environment unadmitted/host overhead UNKNOWN. B4.51
FAIL_PROCESS_SOURCE_FREEZE/consumed quotas, D1 STOP/FULL60/owner-closed rescue,
I1 UNKNOWN, B4.52 NOT_SELECTED_BY_R1, known-paid12721.16417100014444982>7200,
all other costs/UNKNOWN/quotas/final seals and B3 M2+independent Ubuntu24.04/both
scales/final reproduction remain. R/v1 paid180/closed1680; R/v2 unlaunched0/
closed1860; R/v3 STOP/paid300/closed1560 and all frozen bytes remain.

Later publication supplement: PR209/main85644c4/all-four CI completed; source
and result branches were safely removed, worktree retained. The original R/v3
executor result phase actually closed3618.633086/3600s: **18.633086s overrun**
retained, not excused by the later owner grant. That separate <=600s publication
verification grant consumed335.755696s; unused264.244304s closed. Its scope was
existing main-CI verification/merged-branch cleanup only, no role/input/CI rerun.
The original reports' pending-at-authoring statements retain their historical
bytes; this supplement changes no failed acceptance.

**Only next decision:** owner may decline this route, approve F only (D UNRUN),
or expressly approve both F and the exact bounded D exception/budget above with
a fresh reviewer. No decision is inferred from publication of this proposal.
The recommended smallest execution option is **F only**: the missing historical
tuples are already documented, and optional D cannot promise a causal diagnosis.
Even successful F/D ends with a report and STOP; any future R preparation needs
a separate source-stability/input/cost contract and explicit grant. The current
documentation-only slice stops after required normal publication, with no old
input/stat access, implementation, diagnostic query, preflight, R retry or B/C.
