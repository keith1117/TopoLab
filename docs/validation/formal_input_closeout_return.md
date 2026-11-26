# Formal input stopped before activation on the missing readiness copy

The single formal attempt on November 26 stopped before its first role. The independent entry returned 1 while opening the backup of the activation readiness file. The producer received no dispatch. The formal result is 0/6, with zero formal metadata or payload reads, no formal member version and no certificate return. The two public six-role graphs, the controlled late-delivery veto and the new independent preflight all completed before this stop. [Final software PR](https://github.com/keith1117/TopoLab/pull/263) · [Protected-main CI](https://github.com/keith1117/TopoLab/actions/runs/45765947856)

## Formal entry and first error

The independent release verifier replayed the historical registration of 23 physical files, the earlier public rehearsal and certificate evidence, and all three new public controls. Its original return was exit 0 after 6.456 seconds. The report and original have SHA-256 `6b00d1251094b23bba711aba9b229253152b605b88ad80e48a997191af3a1665` and `95c9d0be31f0719350add64d283533fe0fe94f081f3c6af1f87ba8ad5c54d6c6`. The generic filer initially rejected the slot-specific archive destination. The independent caller retained that error separately and used the reviewed proof publication interface to preserve the successful original. It made one paid verifier call.

Both preparation commands returned 0. At 07:02:55.185 UTC the independent preflight returned 0 after 10.484 seconds, with zero source and target stat reads. The original preflight packet has SHA-256 `ea1caa2819d99cecdd260a5097465bf06ea3e243af9ab0e6ea59818789ad98cb`. An initial check on the actor emitter mistook a truncation string literal inside the emitted program for transport metadata. Both original program strings were subsequently parsed and checked against the UTF-8 hashes in their immutable artifacts before entry.

| Formal caller observation on November 26 | UTC | Result |
| --- | --- | --- |
| New one-attempt reservation recorded | 07:05:00.767 | 3,960 FULL ceiling |
| Independent actor began | 07:06:47.960 | Original program invoked once |
| Independent entry requested and returned | 07:06:47.974–07:06:48.119 | Exit 1, `FileNotFoundError` |
| STOP persistence requested and returned | 07:06:48.121–07:06:48.199 | Exit 0, both copies retained |

The preparation writer in `staged_input_preparation.prepare` writes the 16,777-byte readiness document to the single primary `readiness_path`. The two copies of the **command return** both bind that primary file, SHA-256 `358aa02372f4a3e0cada00b9879116e2fae8c2414b6afc981f366914855834bf`. The preflight validated it. In `cycle_filing_intent.entry_value`, the first independent entry separately opens the primary and backup **documents**. The backup directory had no `input-activation-readiness-a1.json`. The raw failure, the primary file and the seal inventory establish the missing copy. The previous 5/6 graph retained two distinct, byte-identical readiness files with SHA-256 `eef082e15d651636c55e734cb69ff345ae1d3f8d07c9278bc83645c9704db19d`. The coordinator had observed the missing peer before launch and accepted the primary plus the two command returns. That decision missed the independent entry's stronger requirement.

The independent actor's outer observation spans 239 ms and contains exactly two tool rows. Its first error is the failed entry and its secondary-error list is empty. The producer was waiting for an independent standby notification that never occurred. It invoked zero actor programs or activation commands, so there is no producer return. No SUP, REC, role binding, final filing, lease release or certificate command was dispatched. The old 5/6 and all 1,071 historical members remain historical evidence.

## Complete public closeouts and the delayed return

Public slots 4 and 5 ran from the first role through shared binding in distinct directories on protected commit `f8f036f7e5d6559690266bb3f26517ca7a3a903d`. Each produced 43 original command packets, six accepted roles and 321 sealed controls. The independent verifier reconciled both 40-file metadata tables, both 558-payload tables and all 1,071 members with the public backup in each run. The table gives offsets from shared role entry. Command return times are the actual caller observations. The worker sampled the durable writes in UTC microseconds as well as monotonic microseconds.

| Shared closeout observation | Public slot 4 (s) | Public slot 5 (s) |
| --- | ---: | ---: |
| Supervisor terminal return | 10.413 | 6.383 |
| Supervisor pair returned | 10.874 | 6.814 |
| Supervisor event filed | 11.339 | 7.259 |
| Recorder terminal return | 11.836 | 7.746 |
| Recorder persistence requested | 11.837 | 7.752 |
| Receipt worker entered | 12.356281 | 8.177890 |
| Complete data packet received | 13.028357 | 8.928100 |
| Primary fsync and readback complete | 13.032577 | 8.931221 |
| Backup fsync and readback complete | 13.033179 | 8.931755 |
| Worker about to write result | 13.036261 | 8.933774 |
| Caller received complete paired result | 13.132 | 9.058 |
| Recorder event filed | 13.645 | 9.660 |
| Caller received independent binding exit 0 | 14.304 | 10.447 |
| Seconds remaining at binding return | 275.696 | 279.553 |

Slot 4's 2,276-byte native REC packet and both retained copies have SHA-256 `5bca94cfec0f16f2953e253ce9f16c65bc4bcdf4da421519b1a1a5b739a105b3`. Slot 5's 2,277-byte packet and both copies have SHA-256 `052b31f49019a13a36aba87ab27ca9a4ab3995a4e89ed7c04e10a4f1647802bf`. Each comparator checked the unmodified packet, both durable copies, the two one-use event filings and the complete native binding return.

Slot 6 reused slot 4's genuine public REC in two new destinations. Both writes completed before the role cutoff. The underlying terminal returned exit 0 at Unix millisecond `1795675900876`. The fixture withheld delivery until `1795676189623`, 30 ms after the original cutoff of `1795676189593`. The caller stopped before filing the REC event. Its eight sealed controls contain the intent, zero spent tickets, and no binding or successor. This controlled delay tests the caller's delivery rule. The source of the previous 588.937-second delay remains unresolved.

## Where the previous closeout stopped

The paired 228-file archive preserves 49 producer and 47 independent tool responses. The shared supervisor and recorder both returned 0. All times below are UTC on November 25. The actor sampled its own clock immediately before dispatch and after the awaited return. [Previous formal result](formal_input_closeout_stop.md)

| Observation | Clock or source | Time |
| --- | --- | --- |
| Shared role entered | Caller, Unix milliseconds | 11:20:05.026 |
| Supervisor terminal return | Caller | 11:20:39.494 |
| Recorder request and terminal return | Caller | 11:20:49.340–11:20:59.058 |
| Request to retain the recorder packet in both locations | Caller | 11:20:59.060 |
| Original dispatch cutoff | Frozen role clock | 11:24:55.026 |
| First and only retention response, exit 0 | Caller | 11:30:47.997 |
| STOP persistence, then failure custody complete | Caller | 11:30:48.123 and 11:30:48.245 |

The 2,969-byte REC packet has SHA-256 `144f1fa29773281557e26d5b14d5d69c8b28e898ca0692596c30bcb67c9d9406`. Both retained copies matched. The tool returned no live session, so there was no later poll. The caller waited 588.937 seconds with 235.966 seconds left at dispatch. It received the result 352.971 seconds after cutoff. The tool's own wait-for-output field was 0.006974375 seconds. The archive contains no historical worker-start, write-completion, process-exit or intermediate delivery timestamps that would allocate the rest of the interval.

## Repair and public transport diagnosis

The shared recorder return now travels as one bounded data message through an owned terminal. After the ready marker, the caller sends the complete packet once. The existing writer retains and reads back both copies and creates the single-use filing intent. The worker records UTC and monotonic ticks at entry, receipt, both durable-write verifications, and immediately before writing its result. The caller records the original terminal status and checks its own delivery time before filing. A worker exit and a caller delivery can therefore be judged separately even when host scheduling delays delivery. The original role clock, Native resource limits, event filing and independent binding apply throughout. [Recovery contract](../planning/closeout_input_recovery.md) · [Source PR 262](https://github.com/keith1117/TopoLab/pull/262)

The first two public slots each cost 600 FULL. A comparable 2,485-byte packet traversed the old paired writer in 69 ms. In the new transport probe the caller received the ready marker after 1,175 ms and the complete response 106 ms after sending the packet. Both paths returned equal copies. Neither probe reproduced the historical long tail.

Pre-publication review found two additional problems. The public poller could switch away from its original session or discard a live response prefix on failure. The first independent verifier candidate expected the formal acquisition sampler journal from an ordinary public sampler that emits separate helper timing files. Its local suite was stopped with exit 143 after this finding. The reviewed revision preserves each original row and replays the public sampler's exact file inventory and raw bytes. Twelve helper files from a previous public fixture matched their registered hashes. The first protected repair used tree `39eac895e9b416a816e6f7edc9c4e763d3b04f87`. Its complete local suite passed 4,422 cases with two platform skips. All four jobs passed on the PR head and on merged main `af118c0a437228a9ff32b9e1b2d30ea3c0e4c902`. [PR checks](https://github.com/keith1117/TopoLab/actions/runs/45750066102) · [Protected-main checks](https://github.com/keith1117/TopoLab/actions/runs/45753423832)

## Public registration stop and recovery

Public slot 3 reserved up to 3,600 FULL. Both copies of its 15,091-byte registration were written. The registration command tried to return the whole object through a 3,000-token output limit. The enclosing caller received a JSON parse error on a truncation notice and stopped before issuing the prepare command. Its original outer error and both complete registration files were sealed. The full inner command stdout was unavailable. No Native role or lease was entered. The pre-dispatch stop cost the 600 FULL minimum.

The external runner now reads back the two full registrations, verifies their identity, and returns a small receipt to the caller. In an isolated test with 18,275 registration bytes, the 348-byte response fit a 240-token limit. Before slot 4, a separate source review found that the independent verifier had counted slot 3's entire reservation as a charge. With the three actual charges of 600 FULL, the balance was 7,800 FULL. The correction checks that each full reservation fit at entry, then advances the balance by the charge established by the independent public proof. All three historical entries must remain present with their pinned original bytes. Four counterexamples remove both copies of an old entry or rebase subsequent balances. The revised local suite passed 4,444 tests with two platform skips. The opening balance and the original pre-dispatch failure remain in the evidence record. The missing inner registration return remains explicitly unknown. [Fee verification PR 263](https://github.com/keith1117/TopoLab/pull/263)

## Independent terminal audit and custody

The two control archives contain the same 21 indexed files, totaling 6,863,168 uncompressed bytes. They include the primary readiness bytes, the two independent tool responses, the outer observation and the producer's zero-dispatch declaration. The inventory identifies the missing readiness peer and contains zero Native controls. Both archives were sealed before the terminal audit. The missing peer was left in its original state.

The independent auditor replayed the paired archives on the exact protected release. Its sole terminal tool response exited 0 in 245 ms and returned `PASS_RETAINED_STOP_FACTS`. It verified the first error, the successful STOP persistence and an empty secondary-error list. The producer had no call, so it had no original return to archive. No plan or lease was created by the attempt. Seven historical leases remain HELD. The auditor used sealed control evidence and did not probe a live lease or source. The certificate command has no exit code because it never ran.

| Paired external record | SHA-256 |
| --- | --- |
| Full public graph, slot 4 result | `1ea8f1f08beee1e03caf05fc07015ca67890ac1a72f3a5f4b38438d6d5d8d0fd` |
| Full public graph, slot 5 result | `4bb10441c76578e8e8150c3634a3431007ae63e024e9e2d6395434d2ce08c4c5` |
| Delayed public delivery, slot 6 result | `6cf47a575b32e1147d005388bef3b71385b109767075e72e99384a4cf4b0e1eb` |
| Formal controls archive | `a2f7ce181592313649266f48315bda6936d2c4c7c9079925f9d6b9cee9dbd680` |
| Archive member index | `ac3456ea0f206a7ea6cb7ca2bfc08ea470c84612377b2480fa8b6d9fda04365b` |
| Independent preflight original | `ea1caa2819d99cecdd260a5097465bf06ea3e243af9ab0e6ea59818789ad98cb` |
| Independent formal actor original | `daac25acb4b33efe60dfb2c23a16ef7b432d275f5cda99cc7249ca169013f607` |
| Independent terminal audit report | `0125d2c0a2acfe4fb7588e616ddf84a1f46db96d91f51a47ad168d26d400541d` |
| Original terminal audit return | `0f11def7f3048196585601eca268a335f02c45c663aca3873068c7631c454262` |
| Formal terminal summary | `fda3f6814e3e18dfb7fa22de9771083fb928b0fba54753832ff78b9bdc6f37d0` |
| Final ledger | `17d50cc9fae69bc556c96537c5c1e7f3d01dccf6d7fece10392b2c43d7d851c6` |

## Closed ledger

| Work | Entries | Ceiling (FULL) | Booked (FULL) | Closed unused (FULL) |
| --- | ---: | ---: | ---: | ---: |
| Public diagnostics | 6 | 9,600 | 9,600 | 0 |
| Independent release replay | 1 | 1,200 | 300 | 900 |
| Formal attempt | 1 | 3,960 | 0 | 3,960 |
| Independent terminal audit | 1 | 1,200 | 300 | 900 |
| **Total** | | **15,960** | **10,200** | **5,760** |

The formal attempt is consumed. Its first independent control entry failed before the first input launch, which is where the contract charges the shared prepayment. No Native dispatch was charged. Public slots 1 through 6 cost 600, 600, 600, 3,600, 3,600 and 600 FULL. The opening known lower bound of 388,659 FULL becomes **398,859 FULL**, plus unpriced costs. All previous failures, unknowns, closed balances and seals remain recorded.

## Smallest next authorization

Further input work requires a fresh, bounded readiness repair in new directories. Publish the identical raw readiness bytes to the registered primary and backup. Exercise the actual independent entry on a complete pair and on a missing or changed peer. The preflight must detect the latter before consuming another formal attempt. Recheck the existing closeout evidence against the exact software selected for the next graph. After those gates pass, one new formal attempt needs a new contract, target, evidence area, a ceiling of 3,960 FULL and a separately budgeted independent terminal audit. The stopped graph remains sealed.
