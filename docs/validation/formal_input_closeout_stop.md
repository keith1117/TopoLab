# Five formal roles passed before the shared closeout receipt arrived late

On November 25 the new formal graph accepted its first five roles. Both authors checked all 40 metadata records and 558 payloads. The exporter, independent reader and backup agreed on 1,071 version members. The shared closeout stopped while retaining its recorder return. The certificate command never started. The new lease is HELD alongside six historical HELD leases. [Source PR 260](https://github.com/keith1117/TopoLab/pull/260) · [Protected-main CI](https://github.com/keith1117/TopoLab/actions/runs/45594956067)

## First-role diagnosis and repair

The two previous seals agreed on the 95 controls. Sample 12 at 5.990902 seconds showed the timer and its child. Sample 13 at 6.530322 seconds added a child of the measured command in the same group. The controller sent SIGTERM, the payload exited −15 and the binder exited 1. The sampler recorded process relationships without executable names. The historical child’s identity remains unknown. [Previous report](formal_input_certificate.md)

Public slot 1 encountered the historical STOP when it tried to re-enter registered readiness. Slots 2 and 3 reached the old certificate proof on its sealed controls through the public first-role entry. An in-process observer recorded creation of `/usr/bin/git`, arguments `git rev-parse HEAD`, its parent and the call from `certificate_replay_proof.py` in `verified_readiness`. The old proof created this child both times. It exited between samples. The observer itself created zero processes. The native timer and sampler, the external supervisor, recorder and binder ran as part of the test. Public slot 4 deliberately created a longer-lived child and retained the native stop.

The readiness checker now resolves the exact checkout commit inside the measured process. It checks the independent replay return and the frozen software bytes against the registered plan. Regressions reject altered checkout refs, changed evidence, stale or incomplete execution buffers and mismatched source. Public slots 5 and 6 passed in fresh directories with complete creation traces. Slot 7 deliberately spawned an unregistered child. The sampler observed its PID and parent, the payload exited −15 and the binder returned 1. The approved source subsequently passed the first role again in fresh public directories 8 and 9 with the released readiness proof. Both SUP and REC, their event filings and the binder returned 0 in each directory.

Four jobs passed on the reviewed PR head and the protected merge `3f5a9b40ad066c95421505aade95209b671aee01`. The release’s local suite reported 4,327 passes and two platform skips. The independent preflight returned 0 in 10.704 seconds. The independent release checks verified the 23-file registration, public rehearsal and historical complete certificate replay before activation. The formal plan froze 122 software paths under tree digest `ef27543a8b7d43dfda95b2ee26946c0229ed4a4b756e1b249ab4c82cd2aefe22`. [Contract](../planning/first_role_child_recovery.md) · [Source PR checks](https://github.com/keith1117/TopoLab/actions/runs/45590603206)

## Formal progress

| Role or operation | Observed result |
| --- | --- |
| Independent public check | The formal SUP, REC and binder completed successfully. |
| Exporter R0 and independent R0 | Both binding commands passed. Each author recorded 40 metadata files. |
| Exporter R1 and independent R1 | Both binding commands passed. Each author recorded 558 payloads totalling 567,896,449 bytes. |
| Version and backup | All 1,071 paths, byte lengths and SHA-256 values agreed. |
| Shared closeout | SUP and REC returned 0. The paired persistence of the REC packet returned after the role cutoff. REC event filing and binding never started. |
| Final filing, lease release and formal certificate | No caller dispatch. The lease remains HELD. |

The new plan has SHA-256 `f2c215470dcdffe9b89987ed374d3938143bed7d851e909ca5a0c304b10597ba`. The new content version has SHA-256 `7a7121836cfc7fb61a8706650d8f016ffbf70239023be4fda17c408294eb1bb7`. The earlier offline certificate replay refers to plan `cfbec3406121c55db47eda369a03913c9f74937771ab51d5ef00070711413599` in its own sealed graph.

## First failure

| Caller observation on November 25 | UTC |
| --- | --- |
| Enter shared closeout | 11:20:05.026 |
| SUP terminal return | 11:20:39.494 |
| REC request and terminal exit 0 | 11:20:49.340–11:20:59.058 |
| Request paired persistence of the REC packet (event 30) | 11:20:59.060 |
| Dispatch cutoff for this role | 11:24:55.026 |
| Caller receives the terminal persistence return (exit 0) | 11:30:47.997 |
| STOP retention finishes | 11:30:48.245 |

The caller had 235.966 seconds left when it requested persistence. It received the terminal result 352.971 seconds after the cutoff. The tool reports 0.006974 seconds of command execution within the 588.937-second caller interval. The remaining time cannot be apportioned from these receipts. The paired REC packet exists and hashes to `144f1fa29773281557e26d5b14d5d69c8b28e898ca0692596c30bcb67c9d9406`. The caller preserved the first error and an empty secondary-failure list. The independent actor had completed its three roles. The one authorized graph is closed.

## Evidence custody

The two control archives each contain 228 files, including 134 native controls. They hold 16,980,173 uncompressed bytes, including the original 49 producer and 47 independent tool rows, the two outer observations, the native records and the caller stop.

The independent terminal audit consumed two 300 FULL calls. The first exited 1 because the audit picked up the archived public rehearsal certificate as a candidate for this formal run. The corrected audit checks the pinned path and SHA-256 of that historical receipt and keeps rejecting unexpected certificate files. Eighteen isolated tests passed. The second audit returned 0 in 7.296 seconds with `PASS_RETAINED_STOP_FACTS`. It verified all five accepted roles, source counts, the backup manifest, the HELD lease, 3,600 formal FULL and the absence of a current certificate. A separate comparison of the sealed exporter, reader and backup rows checked each member's path, length and recorded hash.

| Paired external evidence | SHA-256 |
| --- | --- |
| Formal controls archive | `a02ee784dc55715bf8e17432fef656707203f30f03469064e6d26a21ac95e1e6` |
| Per-file index | `8696e01d9215fad464d0389177727c4160a6c79f23f84c88e283a711bd1f0205` |
| Independent stop audit | `1f9ffd0fab5fc9f821d54b6fa4bcd33e206b1f985a07cdfbf95fbf39ae081b9e` |
| Original successful stop-audit return | `6813ec25dd7900c1a2319d2e0ac0f3c6c429f8b2923144be6d61db245fa1c312` |
| Formal terminal summary | `ac9e3deb7732e426a9251d716c8bb0c080533fa282ae3b8c8d92cbc4da592c37` |
| Final ledger | `f04cbb61ac968ea87b97a2af5341354723c103f2ceb3b51c69fb4d6df476b34e` |

## Closed ledger

| Work | Entered | Booked FULL | Closed unused FULL |
| --- | ---: | ---: | ---: |
| Public diagnosis and verification | 9 of 18 fixtures | 5,400 | 5,400 |
| Independent released-source proof | 2 of 3 calls | 600 | 300 |
| Formal graph | 1 of 1 | 3,600 | 360 |
| Independent terminal audit | 2 of 4 calls | 600 | 600 |
| Total | | **10,200** | **6,660** |

The opening known lower bound of 378,459 FULL becomes **388,659 FULL**, plus unpriced costs. The formal charge includes the single 300 FULL shared reservation and 3,300 FULL of native dispatch charges. Final filing and release incurred zero dispatch fees. All six previous HELD leases and all prior budget closures, unknowns and failures retain their original records.

## Further input work

Further input work requires a new bounded authorization for public diagnosis of the closeout packet return, using the original caller clock and the complete retention, filing and binding path. A fresh single-use formal allocation would require repeatable on-time public returns and independent preflight. This graph and its lease remain sealed. Scientific work is outside this input-only result.
