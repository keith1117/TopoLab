# Formal input certificate for the B1 restricted input version

On 26 November 2026, the B1 attempt on protected commit `d30c33b198099c09ee9c1fb7bbc14f43f8cf1676` completed all six input roles. The formal certificate command returned **0**. An independent terminal audit verified its original return against the sealed plan and the version both readers measured. Both readers verified all 40 metadata files and 558 payload files. The exporter, independent reader and backup agreed on all **1,071 version members**. Final filing completed and the attempt's lease was released. [B1 contract](../planning/receipt_formal_contract.json) · [Runtime PR](https://github.com/keith1117/TopoLab/pull/267) · [Protected-main CI](https://github.com/keith1117/TopoLab/actions/runs/45854307606)

## Original certificate and accepted version

The producer called `receipt_formal_control.py certify-input-version` with the frozen isolated Python interpreter, the B1 target root, the plan digest below and `--role certificate`. The tool returned a live session and then its terminal result, 10.912 seconds after the first request. The two original responses and the complete stdout are preserved in `receipt-formal-producer-producer-certificate-actual.json` and in the producer's original actor trace.

```json
{"B_C_admission":false,"formal_authority":true,"formal_or_scientific_admission":false,"member_count":1071,"plan_sha256":"d26d69bb62ff1488e12a52f2872f07ce00eac92eb4bd30413b53925411d4f739","scope":"SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY","source_input_accepted":true,"version_id":"94e1ccdd7629cfbb697797da4235351c1fdefbcde8c40085dd0876ab3b6b23a7"}
```

| SHA-256 identifies | Digest |
| --- | --- |
| Published contract bytes | `8d2bf3065ed39b003e18b67d6d63baa2a0b6b40535af18cfa34e365f07a73dd1` |
| Formal plan | `d26d69bb62ff1488e12a52f2872f07ce00eac92eb4bd30413b53925411d4f739` |
| Accepted version manifest | `94e1ccdd7629cfbb697797da4235351c1fdefbcde8c40085dd0876ab3b6b23a7` |
| Original certificate command packet | `68cf5367db2753e90904a6bf167c46d2d2a09ed76d0936c4770b045d5e52e2c0` |
| Complete certificate stdout including final newline | `2b79796e837e9d93967a8bcbb802769a936157315dea22317c4de17c9e351455` |

The role order was independent public check, exporter R0, independent R0, exporter R1, independent R1 and shared closeout. The six input-role acceptance records each carry two native exit codes of 0. Their largest measured RSS envelope was 1,399,586,816 bytes on independent R1, within the 4 GiB limit. Final filing and lease release each have their own supervise, record, bind and acceptance evidence. R0 compared each metadata file with its registered digest. R1 did the same for each payload. Five complete inventories agreed on every member's relative path, byte length and SHA-256. These were the exporter manifest and local file records, the independent reader's local file records, and the backup manifest and local file records.

## From the previous stop to formal dispatch

A1 had already repaired the missing backup readiness file. Its independent preflight opened both copies and returned 0. The scheduler accepted the original field order of the resulting JSON packet, while the formal entry required canonical JSON bytes. The independent entry returned 1 before the first role. A1 acquired no lease and made no formal reads. It sealed 21 controls, booked 15,600 FULL and closed 5,160 FULL unused. Those charges raised the known lower bound from 398,859 to 414,459 FULL. [A1 stop and ledger](formal_input_paired_readiness.md) · [Earlier missing-backup reproduction](formal_input_closeout_return.md)

B1's independent custody command retains the original packet bytes and writes a second representation in the canonical encoding required by the formal entry. The scheduler reads the originals and checks the entire decoded packet, the expected hash and its binding to the current readiness files. The formal entry checks again.

| Public fixture | Candidate / released slots | Recorded behavior |
| --- | --- | --- |
| Legacy envelope | 1, 2 on the previous release | Slot 1 stopped in preparation on a missing fixture dependency. Slot 2 reproduced the A1 defect. Preflight and program emission returned 0, then the actual independent entry returned 1. |
| Current pair and receipt | 3 / 10 | Preparation, preflight, custody, program emission and independent entry all returned 0. |
| Noncanonical stored receipt | 4 / 11 | Preflight returned 0. Program emission returned 1. |
| Missing backup, one changed byte, matching pair from an earlier attempt | 5–7 / 12–14 | Preflight and program emission returned 1 in every case. |
| Backup write failed after primary write | 8 / 15 | Preparation, preflight and program emission returned 1. |
| Earlier attempt's preflight receipt | 9 / 16 | The current preflight returned 0. Substituting the earlier receipt caused program emission to return 1. |

All 16 public fixtures recorded zero formal dispatches. The independent candidate command rechecked the historical controls and returned 0 in 19.044 seconds. The protected-release command repeated the checks on the exact merged commit and returned 0 in 18.698 seconds. It verified the 23 registered bindings, the six-role public rehearsal, two timely public closeouts, the late-return rejection and the historical certificate replay. The historical certificate command's original exit 1 remains in its archive. Local regression passed 4,504 tests with two skipped. All four required CI jobs passed. [Previous certificate replay and closeout evidence](formal_input_paired_readiness.md) · [Protected-main CI](https://github.com/keith1117/TopoLab/actions/runs/45854307606)

The formal readiness copies each contained 32,912 bytes. Independent preflight opened the actual primary and backup paths, verified separate physical identities and their binding to the B1 target, contract and release, and returned 0 in 5.918 seconds. Independent custody returned 0 in 0.508 seconds. The stored original and the canonical form each contained 20,200 bytes and decoded to the same complete packet. The scheduler used that receipt before formal dispatch.

| Paired preparation or admission record | SHA-256 |
| --- | --- |
| Original released proof command | `a6a4b5d8b7b231c2d8dbf5273cc71bf79f2263b1ff910ed88cb4ec80ce08799b` |
| Released prerequisite report | `083c7732af87877afd0329ce15f89e0d21f46de963cf59004fad0907e38bf2c6` |
| Formal readiness file, either copy | `774e7f940a37e04f1c9943896b771dd33562ea70166e8935eefc2a8237e8bf7c` |
| Original independent preflight packet | `11f491cb47cc1602818c1bb7d910365b7ff4e429d8c4cd3c40f7018c5e1c7890` |
| Canonical encoding of the complete preflight packet | `49baa5ef75a8827ec524f2eb027e85aeb4e03c2c943c91cb1cf5d9c6e70aadda` |
| Original independent custody command | `66a95e3646211b6e36b254db913d99b635cac33b6bfe9fae6644735e4ead27fd` |

## Formal archive and independent verification

Both archive copies contain 270 controls, including 180 native controls, totaling 23,040,373 uncompressed bytes. The index records the length and SHA-256 of every archived member. Every primary caller file had a distinct, byte-identical backup. The external evidence directory is `receipt-20261126-b1`, with formal caller originals under `receipt-20261126-b1-formal` and corresponding backup directories.

| Paired archive record or member | SHA-256 |
| --- | --- |
| `formal-a1-controls.tar.gz` | `ddf1e82cf29b1a49fe7605a503f398880a41c0dac38165543fff53d455c4ca7d` |
| `formal-a1-index.json` | `b9aa939e17552868b2cc8c92bb9a6ae261c87a8b43bf1676675c908d0b76b237` |
| `formal-a1-seal.json` | `605bd95f1cecc2dacfa27de7b48bc7bac3d7a0eb027326485eb9ba9ab05f4cc3` |
| Producer actor original | `312d465cf490f08a7a976022de7e373a408329203db918fc44c6920ad383ca82` |
| Independent actor original | `da800f997b54c48780365376a93f6cad888b1e1fa03a3e908fd82e4359643fb0` |
| Accepted acquisition bundle | `33c84cb2add06ee7877ca64c7928e2489eada34921be5505d60c151ea12f7687` |
| Released B1 lease | `9088e0384f75bb3ccfbd84e50b92b803cfebebda59c241d1c193ed717f654068` |

The first independent terminal audit returned 1 with `caller predecessor release differs`. The auditor looked for a predecessor binding with the prior `closeout-formal-` filename prefix. All six recorded input-role releases used the contract's `receipt-formal-` prefix. The original slot 1 return has SHA-256 `5346125fd9cdb8f214aadb6373ebebf275acbfc21068d1c6e9fa5592576b4ad9`. A regression on the lease-release metadata also found that the auditor omitted the transport's `secondary_failures` field. The formal transport recorded an empty list.

The corrected auditor checked the exact B1 filenames and the transport's complete metadata. It passed 95 regression tests before repeating verification on the same archive. Its command in slot 2 returned 0 with `PASS_COMPLETE_FORMAL_INPUT_TERMINAL`. It reconstructed the certificate from the role evidence and original tool events, matched the reconstructed bundle with the filed bundle, and compared the complete certificate stdout. The plan digest matched the archived plan and the version matched all five inventories. It also verified the release record for B1's lease. The six input roles and the certificate command each ran once under the B1 contract.

| Independent verification and closure | SHA-256 |
| --- | --- |
| Original successful audit command, `terminal-audit-2-actual.json` | `75b2e4a5f881f60c1d9cb1f2563ae64e87534fed337d16941102f25bf8a65b78` |
| Independent report, `independent-terminal-audit-a2.json` | `2658d414ea12b7013ead703a00f298345b86234149d250edbe068614b36d5b78` |
| Terminal summary, `formal-a1-terminal.json` | `cf32adfd0df3405db3449a5b30e7da0987d3c2c97c1eb0347e6fafff8545b6dd` |
| Closed ledger, `final-ledger.json` | `4bfc288814a3dc9ab65120546ecfbb4e62b67980a1680a68ccd886ba27a6ab3a` |

## Closed ledger

| Work | Entered | Ceiling (FULL) | Booked (FULL) | Closed unused (FULL) |
| --- | ---: | ---: | ---: | ---: |
| Public fixtures | 16 | 14,400 | 9,600 | 4,800 |
| Candidate replay and protected-release verification | 2 | 1,200 | 600 | 600 |
| Formal input attempt | 1 | 3,960 | 3,960 | 0 |
| Independent terminal audit | 2 | 1,200 | 600 | 600 |
| **Total** | | **20,760** | **14,760** | **6,000** |

The terminal summary records `FORMAL_INPUT_CERTIFICATE_ISSUED_AND_INDEPENDENTLY_VERIFIED`. B1 raised the cumulative known cost from 414,459 to **429,219 FULL**, plus historical unpriced costs. All 6,000 unused FULL closed with this contract. Seven historical leases remain HELD. The certificate covers the source-attested restricted input version identified above. Scientific B/C, fitting, search and any further execution require separate authorization. Uniform remains the default and the fixed P/17 quality gate remains open.
