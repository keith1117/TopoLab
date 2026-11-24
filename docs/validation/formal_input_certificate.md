# Formal input stopped at the first role after the certificate checker passed offline

The repaired certificate checker passed full independent replay on protected main `671a21b3d47fae16610e13884993abee5bee8e12`. The sole new formal graph activated and stopped during the first role, `independent-public-check`. Its binder returned 1. No role passed and the formal certificate command was never dispatched. The new lease is HELD. [Source PR](https://github.com/keith1117/TopoLab/pull/258) · [Protected-main CI](https://github.com/keith1117/TopoLab/actions/runs/45378472911)

## What happened on the new graph

| Gate | Original result |
| --- | --- |
| Release | The reviewed source tree `ac0da65f1b6a335af948431cf01073d6d418c1c8` reached main unchanged. All four checks passed on each of the PR and main. Locally, Ruff and mypy passed and pytest reported 4,238 passes and two platform skips. |
| Independent release replay | Call 6 exited 0 in 7.295 s. Both copies of the report matched `133553193c411d565860c0a04ac81b65f8bad47152d1b89caa88e28ee3b75c81`. Its original packet matched `7b3af893a673787cce4992eb9ca92db91c08e4112e81a0d225265cf839edbeda`. |
| New independent preflight | Exit 0 in 11.142 s. The preflight bound the clean main, the independent replay, and the readiness SHA-256, with zero source and target stat reads. |
| Formal activation | The new plan `0bdebc474d6206647a39a8e22fd60d9f2074455d06ad1e36ae8cdfa3a4626147` froze **118** files. It bound the 23-file registration and previously accepted public rehearsal under this contract. |
| First role | The outer SUP and REC commands both exited 0. The registered native payload exited **−15**. The bind command returned the stop and exited **1** within its window. |
| Successors | Exporter R0, independent R0, both R1 roles, shared closeout, filing, release and certificate were never dispatched. There are no new 40/558 reader results or 1,071-member version. |

### Native failure and caller stop

At offset 5.990902 s the sampler saw the registered timer and its direct command. At 6.530322 s the thirteenth sample recorded a third process in the same group, a child of that command. All 13 sampler helpers returned 0. The controller recorded `RESOURCE_UNKNOWN_STOP_UNREGISTERED_DESCENDANT`, sent SIGTERM and observed the group disappear. The registered timer returned −15. Its native profile recorded 6.52 seconds of wall time and 214,990,848 bytes of RSS. The full-role RSS envelope and inner minimum charge remained unknown.

The binder reported `role child exit incomplete`. The file named `independent-public-check-accepted.json` contains `STOP_NO_RETRY` and a failed acceptance. The producer observed the predecessor stop. Both callers retained their original returns and recorded empty secondary-failure lists. The public-check child log contains only the timer's abnormal-termination line. Each sample records the process, parent, group and RSS. It does not record the extra executable or its arguments.

There is a reachable source-level explanation. The first role's payload calls `checked_setup`, which rechecks registered readiness. This profile's `verified_readiness` invokes `git rev-parse HEAD` as a subprocess. That invocation can introduce a third process inside the measured role. The sampler evidence establishes the extra process and its termination but cannot identify that PID as Git. A bounded public reproduction with child-executable attribution would distinguish this call from other sources before another grant is spent. The process-count, identity, SHA-256 and resource guards stay in force. [Frozen readiness check](https://github.com/keith1117/TopoLab/blob/671a21b3d47fae16610e13884993abee5bee8e12/scripts/certificate_replay_proof.py) · [Frozen resource controller](https://github.com/keith1117/TopoLab/blob/671a21b3d47fae16610e13884993abee5bee8e12/scripts/p17_m2_resource_control.py)

## Why the preceding certificate failed

The previous plan ran on protected main `96edccd4357472de7ae4565fd3f8494ffe000090`. All six roles, the 1,071-member comparison, filing and lease release passed. The original certificate command exited 1. Both sealed copies of all 274 control files agreed with their recorded lengths and digests. Their plan bound 107 software files. The checker selected 98, and every common file had the expected raw-byte SHA-256. [Preceding terminal report](r1_window_formal_result.md)

The omitted paths were `docs/planning/r1_window_public_contract.json`, `scripts/r1_window_public.py`, its six sibling scripts with suffixes `_clock`, `_control`, `_filer`, `_independent`, `_route`, `_waiter`, and `scripts/r1_window_verify.py`. The independent checker now derives the paths for the selected contract, compares the complete sets and verifies each selected file's original bytes. Missing files, extra files and altered file contents each have rejection cases. The independent and producer rules agree on the prior and current formal profiles. The compatibility suite passed 249 tests.

## Full offline certificate checks

All complete calls consumed their registered 300 FULL, including failures. Replay opened the two immutable control archives and checked the historical plan against its original commit blobs. The original certificate packet retains SHA-256 `6d108fb692015e3c9d82a1d6fb8fcec11150bfbfa5f2dbdbf13c45adb6a65fac` and exit 1. The repaired checker separately identifies the bytes it executed. The shared certificate command returns a historical-scope result when it receives historical evidence.

| Call | Original exit | Elapsed seconds | Actual outcome |
| ---: | ---: | ---: | --- |
| 1 | 1 | 6.759 | The frozen old checker reproduced the inventory disagreement. |
| 2 | 1 | 6.387 | Historical preflight replay lacked the frozen source buffer for `staged_input_filer.py`. |
| 3 | 1 | 6.222 | Replacing the loader during a nested replay again lost that dependency's execution record. |
| 4 | 0 | 7.219 | Recompiling the historical helpers from their original bytes in the active loader let the complete audit reach its result. |
| 5 | 0 | 7.888 | The reviewed candidate repeated the full audit with independent module hashes and an explicit prepublication revision label. |

The audit followed eight supervisor/recorder event pairs, the six accepted roles, the two closeout bindings, the member manifest, the backup and the lease release. The historical result bound plan `cfbec3406121c55db47eda369a03913c9f74937771ab51d5ef00070711413599` and version `981ff827c0ef6592e684bbff9c7b5745a2b7bd62a1b6c6b76eff0eae8ed3a21a`. The reviewed replay report has SHA-256 `5087411051044579f97b8a60202fbfed29c951166c6bfa466f4c28a8c5fd18e5`. Call 6 above verified the same historical evidence using the independent author and the exact protected release. [Registered contract](../planning/formal_input_certificate.md)

## Custody and independent terminal audit

The paired archive contains 95 controls, including 28 native controls, totalling 7,035,457 uncompressed bytes. Every archived control had an identical second copy or a byte-verified copy in the second archive. The producer original holds 12 tool rows and the independent original holds 14. The archive contains the registered target’s cooperative reader lease marker. Five earlier HELD leases and the preceding graph's RELEASED lease remain recorded. The new archival action preserved the stopped controls. Formal final filing and lease release were not reached.

| Paired evidence | SHA-256 |
| --- | --- |
| Budget registration | `7ae3b524775086003d636d15e747333bdc7c9abd96ea34ea67f9f6e0cf999595` |
| Preflight actual | `dd5f27b6cc39ecc5f1fb3f2dc8b3a70e0ef24d6d1bc9e5119f52ce301d62a0d0` |
| New formal plan | `0bdebc474d6206647a39a8e22fd60d9f2074455d06ad1e36ae8cdfa3a4626147` |
| Producer original | `303e413c4001d5761e47d8ae906c118ca2ea97f84ea221eafe7c306cdd43fec5` |
| Independent original | `2425a6ec08eec588a6f3619a27d9d78c2a858950a94b5910bcc5088534e49f4b` |
| Control archive | `c876d14eb81a48d30c2831bc05dfb99d8580c9c18728c3f1133b947ca2adf288` |
| Control index | `f7f3b7cc1a0d939b1a2873df8e662f9cd9498096fe4d537c6bf49eb3963f6543` |
| Native first-failure evidence summary | `2660022f08f283640d0e875a041dca246cf521882e0d9fbf546227ca4d644ac5` |
| Formal terminal reconciliation | `8725eecb670e9a09116d7ea5acbdc1bf073706bf892ec5f90536b914751ee634` |

The first post-stop audit command exited 1 after 0.703 s. Its adapter compared each hosted caller's twelve-field plan summary with the entire native plan. Both original callers carried the correct plan digest. The failed audit packet has SHA-256 `93a2177aedb42beccb918b3d3b9abd112558df8000626716a985cc3c45f0a249`. The separate audit budget covers that invocation.

The repaired terminal audit derives the exact twelve-field waiter output from the frozen native plan, including the plan digest and deadlines. Its original command returned **0** in 1.161 s. Independent replay of the native role reproduced the stopped binder record. The audit verified both SUP/REC returns, both filing calls, the bind return, the paired absence of a formal certificate, the held lease marker, the absence of successor dispatches and all 95 archived controls. It captured no executable name for the third process.

| Terminal audit and ledger | SHA-256 |
| --- | --- |
| Independent stop audit report | `4d83fa6b5d6f54986a628edd01879bcdd9b44c5f0a8759d516009f34b5cd8c9a` |
| Independent stop audit original return | `f5850db4c6594cb92b295ccb279ba16ef2f0287b5833903517a547fb0d9e9e77` |
| Closing ledger | `0f28d29877900e8ae891ee290ee0489c5a7888d3860681f208b25181626df329` |

## Closed ledger

| Allocation | Ceiling FULL | Booked FULL | Closed unused FULL |
| --- | ---: | ---: | ---: |
| Full offline certificate replays, six invocations | 4,800 | 1,800 | 3,000 |
| One formal graph, stopped during the first role | 3,960 | 600 | 3,360 |
| Post-stop independent audits, two invocations | 600 | 600 | 0 |
| **Total** | **9,360** | **3,000** | **6,360** |

The formal 600 FULL consists of one shared reservation of 300 and the observed 300-FULL first-role dispatch. The native and caller copies identify the same shared reservation. No final-filing or release tariff was incurred. The closing known lower bound is **378,459 FULL plus unpriced costs**, up from 375,459. All prior failures, the previous formal exit 1, earlier approval refusals, old unknowns and the previously closed 12,780 and 12,660 FULL remain recorded.

The formal grant is consumed. The smallest next authorization is a bounded software-only diagnosis and repair of the first-role child process using these controls and a public fixture. A further formal run would also require a fresh conditional single-graph contract, up to 3,960 FULL at the current tariff, with a new target and new evidence. The stopped graph grants no successor or scientific work.
