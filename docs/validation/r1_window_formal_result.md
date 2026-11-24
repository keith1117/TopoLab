# Six formal input roles passed. The certificate command returned 1.

The sole formal attempt on protected main `96edccd4357472de7ae4565fd3f8494ffe000090` accepted all six roles, final filing and lease release. The certificate command returned 1 while comparing its software file list with the frozen plan. Formal input certification remains open. The attempt is closed, the new lease is RELEASED, and all five historical leases remain HELD. [Contract](../planning/r1_window_input.md) · [Main CI](https://github.com/keith1117/TopoLab/actions/runs/45302141744)

## Formal results

| Evidence | Exporter | Independent |
| --- | ---: | ---: |
| Registered metadata paths and matching hashes | 40/40 | 40/40 |
| Metadata bytes | 2,777,259 | 2,777,259 |
| Registered payload paths and matching hashes | 558/558 | 558/558 |
| Payload bytes | 567,896,449 | 567,896,449 |
| Matching version members | 1,071 | 1,071 |
| Native R1 payload elapsed, seconds | 20.89 | 28.53 |
| Role start to original binding return, seconds | 73.844 | 90.310 |
| Usable time left at binding after ten-second reserve, seconds | 1,116.156 | 1,099.690 |

Both R1 returns passed SUP, REC, single-use event filing and binding. The source tables agree on every path, length and SHA-256. The independent local identity rows, exporter manifest and backup agree on the same 1,071 path-length-hash triples. The version is `981ff827c0ef6592e684bbff9c7b5745a2b7bd62a1b6c6b76eff0eae8ed3a21a`. The accepted resource envelopes were 1,387,069,440 bytes for exporter R1 and 1,385,480,192 for independent R1. On this formal run the exporter spent 0.886 s on label reads and 6.577 s on label parsing. The receipts do not establish how much of the improvement from A3 came from storage availability.

The independent released-source replay returned 0 in 6.878 s. A fresh independent preflight returned 0 in 13.561 s and checked the 107-file formal tree, the 23-entry registration and the historical public evidence. Both formal actors started from the first role. The original six-role sequence completed, followed by final filing and lease release. Only the subsequent certificate failed.

## First failure at certificate issuance

`certify-input-version` first returned a live session and then a complete terminal traceback with exit 1 in 10.527 s. The first exception was `ValueError: software closure/source freeze differs`. The producer filed the original packet and recorded `STAGED_CALLER_STOP: certificate actual return rejected`. There was no secondary caller error or issued certificate. The independent actor had already returned successfully. The caller STOP points to its paired original failure.

A read-only comparison used the sealed plan and the released verifier's software-path selection. The plan freezes 107 files. The certificate verifier selects 98. All 98 common file hashes match, including the verifier's own hash. The plan also includes the public timing contract, seven public timing scripts and the independent verification launcher. The exact omitted files are listed below.

```text
docs/planning/r1_window_public_contract.json
scripts/r1_window_public.py
scripts/r1_window_public_clock.py
scripts/r1_window_public_control.py
scripts/r1_window_public_filer.py
scripts/r1_window_public_independent.py
scripts/r1_window_public_route.py
scripts/r1_window_public_waiter.py
scripts/r1_window_verify.py
```

The minimum next authorization under the current source-freeze rule is a bounded software repair and offline certificate regression on the sealed controls, followed, only after that passes, by one new formal graph of up to 3,960 FULL on the repaired protected revision. A regression should exercise the formal certificate's software check with all 107 paths, reject a missing or changed identity and cover the later certificate checks. The old successful roles and released lease belong to the closed graph. Scientific admission remains outside this slice.

## What stopped the previous formal R1

The two A3 archives matched on all 87 control files. The following clocks are UTC on November 23. The dispatch deadline keeps the original ten seconds for completion.

| Archived observation | Time or duration |
| --- | --- |
| Exporter R1 role start | 09:48:34.658 |
| Supervisor launch of the native command | 09:48:47.310 |
| Payload exit | Code 0 after 1,159.41 s. The absolute exit time is unknown. The profile file modification time was 10:08:15.605. |
| Supervisor terminal return | 10:08:16.289 |
| SUP filing request | 10:08:16.493 |
| First filing response | 10:08:23.253, live after 6.760 s |
| Caller STOP write | Requested 10:08:23.273 and returned 10:08:23.382 |
| Dispatch deadline | 10:08:24.658, leaving 1.405 s at the first response |
| Separate post-stop observation | 10:08:47.439, exit 1 after the consumed intent saw STOP |

Native CPU time was 28.07 s user and 6.74 s system. Across 528 labels, the intervals between the preceding audit or index write and the next producer write totalled 1,116.519 s. The median was 1.610 s and 30 intervals exceeded five seconds. These intervals include source access, validation, computation and output. The seal provides no per-operation times within them. A storage-provider attribution remains unverified. The recorder had no dispatch.

## Repairs and public diagnostics

The first isolated probe stopped on a missing explicit execution identity. The second profiled a full export. Its timed wrapper returned 1 when the sandbox denied a system query. The isolated process produced its measurements, and the wrapper failure remains in custody. The third probe exited 0. Both completed payload profiles used 558 generated files totalling 567,895,559 bytes and produced 1,071 members totalling 92,430,259 bytes. A3's corresponding sizes were 567,896,449 and 91,214,092 bytes.

The strict parser consumed 39.954 s in the original profiled export and 15.289 s in the revised one. Full profiled exporter time went from 50.126 to 25.149 s. The revised parser uses the JSON decoder's native float conversion and then checks finite values and nesting in one pass. Duplicate-key rejection and signed-zero behaviour remain under regression. The public full graph also records per-stage read, parse, validation, serialization and output times. These local public measurements cannot apportion the old formal file waits.

For filing, recording and binding, the actor gives the original hosted command up to 30 seconds on its first wait, clipped to the current dispatch deadline. It keeps the five-second minimum for each later poll, the original clock and a single filing intent. On the same 1.8-second public command, the former 1-second wait returned a live session with only 2.336 s to poll. With a bounded 3.5-second first wait the terminal result returned 0 with 1.608 s left. This tests the observed timing boundary at the actual host interface.

Public graph 1 stopped after the first two roles. Its independent reader rejected the registration document in a shared parent. The revised public registration lives in the paired private evidence directories. Its 23 physical anchors and the independent R0/R1 registry binding passed on the later fixtures. Public graph 2 completed both real R1 binders. The subsequent admission checks also replay the native sampler, single-use event intent and original binder output. Offline mutations of the sampler journal and binder stdout both failed replay with the archive hashes recomputed. Graph 2 remains evidence for its own candidate.

## Repeated full-chain public verification

Runs 3 and 4 used new private sources and destinations. All 94 executed source files had the same digests, and the original driver program had SHA-256 `85f592f357e0ed8044ba613d4d5c442386dbd20de251cec37e20ae9d1b69f838`. Each side verified 40 metadata and 558 payload files. Both independently verified the same 1,071-member version, `a2c03108f04c138fe0d667bf8bf25a8240cd9aa38764a65d05ea6c90021b8b1b`.

| Full-chain measurement | Public run 3 | Public run 4 |
| --- | ---: | ---: |
| Exporter R1 native elapsed, seconds | 12.34 | 15.04 |
| Independent R1 native elapsed, seconds | 20.47 | 25.26 |
| Exporter time left at original bind, seconds | 1,177.773 | 1,175.798 |
| Exporter time left after preserving ten seconds | 1,167.773 | 1,165.798 |
| Independent time left at original bind, seconds | 1,171.100 | 1,163.937 |
| Independent time left after preserving ten seconds | 1,161.100 | 1,153.937 |
| Archived control files per copy | 167 | 167 |

On run 3, the exporter spent 0.880 s reading labels, 4.581 s parsing them, 1.263 s validating, 1.761 s serializing, 2.569 s checking and writing output, and 0.357 s finishing. Run 4 recorded 1.026, 5.563, 1.555, 2.107, 3.239 and 0.493 s in those stages. Each graph used its native supervisor and recorder, original host returns, single-use filing intents, resource sampler and independent binder. The four public scratch leases are diagnostic custody.

The merged tree `c683afbf4256b143675f8de3e6c85d7f58c6cf61` matched the reviewed candidate. Each public archive can be replayed against execution-tree digest `099595e4159883d0e33ef3583506b35fb3ee856d4d012ef47d44d2518d692635`. The local suite passed 4,219 tests with two platform skips. [Released source](https://github.com/keith1117/TopoLab/pull/256) · [PR CI](https://github.com/keith1117/TopoLab/actions/runs/45297077025)

| Timing evidence | SHA-256 |
| --- | --- |
| New budget registration | `d867948e0cf23b8a860a230be66fbedfc3c7cb5398168dada7fa71199fc2a35e` |
| Public run 1 stop archive | `0b01391a64fdfe6fe19a9f5a8d2dcc269b02a63bc652c0def823bb57fa1e6041` |
| Public run 2 archive | `a7da3e70b1db1129b72d14d168559bfa34f232cbdf5685db4fc958eb2d1ec7d9` |
| Final candidate run 3 archive | `f95736a56d25c68955cc475e7a0664636a75e7123400845e043eca7ec23410d6` |
| Final candidate run 4 archive | `ebf38b10c5fa47237986da7ba48cfa164014b7e984a897471c9d04b80ede0536` |

## Custody and charges

Both archives contain 274 controls, including 179 native controls and 95 caller or preparation records, totalling 15,910,570 uncompressed bytes. Every member matched its indexed length and SHA-256. The two evidence directories agree. The producer and independent records retain 76 and 46 original tool rows. The new lease release and the absence of the live lease marker were observed before closure. The earlier approval refusal, failed attempts, unknown costs and old seals remain in their original ledger. [A1–A3 ledger](formal_input_cycle_result.md)

| New allocation | Ceiling FULL | Booked FULL | Closed unused FULL |
| --- | ---: | ---: | ---: |
| Three isolated public probes | 3,600 | 3,600 | 0 |
| Six public graph slots, four used | 23,760 | 12,000 | 11,760 |
| Independent offline checks, one used | 1,200 | 300 | 900 |
| Sole formal graph | 3,960 | 3,960 | 0 |
| **Total** | **32,520** | **19,860** | **12,660** |

The four public bookings were 1,200, 3,600, 3,600 and 3,600 FULL. The formal native numeric bookings sum to 3,780 FULL including the single shared reservation. The lease-release dispatch was observed and accepted. Its native amount is null and the new contract charges 180 FULL for that invocation. The cumulative known lower bound is **375,459 FULL plus unpriced costs**, up from 355,599. The 12,780 FULL closed before this campaign was never reopened. No new formal attempt remains.

During archive reconciliation, the first local summary tried to add the native null price and the next expected a public-fixture-only member count field. The completed audit uses the contract rate for the observed release and compares all formal `local_identity_rows` with the manifest and backup. All reconciliations used sealed bytes.

| Paired formal evidence | SHA-256 |
| --- | --- |
| Independent public replay actual | `c7af9a51a9997e5914b31df8a4cca2a5a96bef431b4d737ce630475d4ff1579e` |
| Independent formal preflight actual | `302a6c80bd251d3eb6d37eef27086b5c8c5516b6bf21a358e33f2b5c496390db` |
| Original certificate command packet | `6d108fb692015e3c9d82a1d6fb8fcec11150bfbfa5f2dbdbf13c45adb6a65fac` |
| Producer original result | `23d6ec6ce1d34c63bb5f7364120910f7e21b42870de722af1c1e6578b80ab4aa` |
| Independent original result | `570f01ce1295d7831c0a6940f1cde7a3290eb7b0a96034a1f19708bfe77e06c8` |
| Control archive | `6a797c9327762298638d2b3f224bd51cbcba46a9f1c24657f818d346c3c3a282` |
| Archive index | `bb9e396ec42c532a50f195d0a0ab7c0fab19e67c0446447fd1ba05bf3dc7a6a2` |
| Formal terminal audit | `8e226102d39b0f638321311a4df95c43d06e0e3f8ddc384a6dcf96c3253edcbb` |
| Certificate software path comparison | `f6e3cfece5a6646936f297aa918c4680397aafeec4b60f8e563e30117a7661de` |
| Final ledger | `dad3aee1189820ea11b05d8c053d369370dd092a25a74a76643f5420b91fab23` |
