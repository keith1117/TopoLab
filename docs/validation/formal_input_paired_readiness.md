# Formal input stopped while opening the independent preflight receipt

On 26 November 2026 the independent entry on protected commit `07abc057df5bd81ef255efd1c96d1fc66fe41f92` returned 1 before the first role. The formal result was **0/6**. The independent author had opened both readiness files and returned 0 in preflight. The entry stopped while reading the stored envelope of that successful command. The producer received zero calls. Neither author read formal metadata or payloads, and the graph acquired no lease. The certificate command did not run. [Runtime PR](https://github.com/keith1117/TopoLab/pull/266) · [Protected-main CI](https://github.com/keith1117/TopoLab/actions/runs/45835825316)

## Readiness repair and public evidence

The first public reproduction used fresh directories and the previously released code. The primary readiness document and the two preparation receipts existed. The backup readiness document was missing. The old preflight returned 0 and the actual independent entry returned 1. The repair writes, closes and reads back both documents. The independent checker opens both files, checks their bytes, their separate physical identities and their binding to the contract, target and software. The scheduler checks the independent preflight receipt before emitting its program. [Readiness repair](https://github.com/keith1117/TopoLab/pull/265) · [Previous formal stop](formal_input_closeout_return.md)

On the final protected software, public slots 19–24 called the actual preparation, preflight and scheduler code using fixture inputs. The valid pair passed preflight, program emission and independent entry. Missing backup, one changed byte and an old pair each produced exit 1 at preflight and emission. A failed backup write produced exit 1 in preparation, preflight and emission. Replacing a successful preflight with an old receipt stopped emission. All six fixtures recorded zero formal dispatches. The fixture's receipt writer serialized keys in sorted order.

The first independent release verification stopped with exit 1 during full historical certificate replay. The historical checker tried to resolve the evidence directory of a later software generation. The correction resolves only the active generation's attribute. A separately charged candidate replay returned 0 on the same 274 sealed controls and 1,071 members. The released independent command then returned 0 in 13.681 seconds. It checked the 23 registered files, retained public results, six new public cases and historical replay. The old formal certificate command's exit 1 remains recorded. Earlier public closeouts retained 275.696 and 279.553 seconds when their binding returns arrived. The late example stopped at 30 ms past cutoff. [Historical timing and registration evidence](formal_input_closeout_return.md)

## Formal preflight and first error

The paired formal readiness documents each contained 31,923 bytes with matching SHA-256 and distinct physical identities. The independent preflight returned 0 after 5.878 seconds on the registered paths. Its return bound the target, protected commit and contract. The independent storage helper serialized the full tool packet in object insertion order. Both copies matched. The scheduler parsed that envelope and verified its stdout. The formal entry also called `staged_input_filer.read_json`, which requires byte equality with the repository's canonical JSON encoding. It rejected `input-preflight-actual-a1.json` with `STAGED_INPUT_COURIER: canonical complete metadata required`.

The actor's two original tool returns record exit 1 for entry and exit 0 for persistence of the stop. The outer call returned in 186 ms. Both evidence roots retained the original preflight envelope, stop and outer return, and the producer's zero-dispatch observation. The terminal audit returned 0 with `PASS_RETAINED_STOP_FACTS`. The archive contains 21 control files and no native role controls. Seven historical leases remain HELD.

| External paired record | SHA-256 |
| --- | --- |
| Contract | `6ef45d08ea73ea24ad2a47f010b1eb4d5357d2bfccb615753ebe0ecf66ae4aa2` |
| Released prerequisite report | `e21399e30a006144efee9186586ccbcab22d22d460c6fca5c33cbb8681a5d002` |
| Original released verification command | `2864818cb54f0c87d145c626107a78bf5e1b7b3b1fc6f368b231e85d54dbd353` |
| Formal readiness file, either copy | `f7ef1b6cadba4d3a1d0c8fffed3ffd2c8ec72b5178baa5a57ad539ce30223d3d` |
| Original formal preflight envelope | `14889ac10f9f79944bfc5f4ac35cc541a4ef7d1e4721e7ed03cf9ba8553b7097` |
| Original formal independent actor result | `49c3debf5aaa31d8d1b0d4b1bc332c33541f3469dbea70a3b4f22539812c1f8d` |
| Formal controls archive | `ad9b1ee7b7295d69fb29a4d6b69c4041142fe1ec6ce221fed5c4f71a46dce416` |
| Archive index | `6d8f407cb952735236ccaec13ecc0199cf2ac8e759c8dfb0d9a0c38afcbf9c33` |
| Original terminal audit command | `25fb35eb5f5045853a3bee63ad1a909934701e66c6297c219c319c782a49b8bd` |
| Terminal summary | `9492e287fd57b463788b6b6d2ba353ccac094e19a5d2adc8e33cdafa892deb64` |
| Closed ledger | `721bbd39d932c5935cda2e477d65b9b17442816b9a610689953f1b95f0fbfb9a` |

## Closed ledger and next contract

| Work | Entered | Ceiling (FULL) | Booked (FULL) | Closed unused (FULL) |
| --- | ---: | ---: | ---: | ---: |
| Public readiness probes | 24 | 14,400 | 14,400 | 0 |
| Release verification and candidate replay | 3 | 1,200 | 900 | 300 |
| Formal graph | 1 | 3,960 | 0 | 3,960 |
| Independent terminal audit | 1 | 1,200 | 300 | 900 |
| **Total** | | **20,760** | **15,600** | **5,160** |

The cumulative known floor advanced from 398,859 to **414,459 FULL**, plus historical unpriced costs. The next input contract requires the independent storage and admission paths to agree on the exact receipt bytes before dispatch. It preserves the original tool envelope and uses new targets and evidence directories. The continuing authorization applies to formal input acceptance. [New contract](../planning/receipt_formal_contract.json)
