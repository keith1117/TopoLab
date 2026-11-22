# Formal activation passed and exporter R0 stopped on a source read

The repaired plan accepted the exact published contract. Formal activation
returned exit 0 in 15.008 s and acquired the new target and lease. One of six
roles passed. The exporter stopped while reading its 34th metadata file.
Formal input acceptance remains open. The November 22 attempt is closed.
[Finite contract](../planning/formal_input_published_authority.md)

## Contract bytes, publication and preflight

The regression reproduced the compact-JSON digest rejection using an indented
contract. Both plan constructions now hash the original buffer. The independent
verifier accepts that plan and rejects a plan with the compact digest restored.
In the actual formal plan, the preparation, contract and execution digests all
match the 11,177-byte published file. Its SHA-256 is
`efdc58736a5541d06ac52196e324df3f4af3ea1f29e992ac3e2897ac00a58b65`.

Source PR 246 merged as `0311e7a0ffce3f2f169cb65a97012f09ba5cfe84`.
Local regression passed 3,794 tests with two platform skips in 1,591.85 s.
Both source reviews passed. All four checks passed on the exact PR head and
on protected main. The producer and independent software inventories matched
on 80 files. [Source PR](https://github.com/keith1117/TopoLab/pull/246) ·
[PR checks](https://github.com/keith1117/TopoLab/actions/runs/44985193849) ·
[Main checks](https://github.com/keith1117/TopoLab/actions/runs/44988001904)

Both readers replayed the previously certified 23 formal anchors. The original
public verifier replayed the six accepted public roles and 1,071-member version.
Preparation and readiness both returned 0. The independent preflight returned
0 in 11.431 s with zero source and target reads. Its original return and the
formatted authority then passed the generated-plan comparison before activation.
[Previous public and formal outcomes](staged_source_input_acceptance.md)

## Formal input attempt

The first supervisor request was sent 15.286 s after the original activation clock,
inside the 30 s limit. The contract set the RSS cap at 4,294,967,296 bytes.

| Role | SUP/REC interval | Native RSS envelope | SUP / REC exits | Result |
| --- | ---: | ---: | --- | --- |
| Independent public check | 45.174 s | 1,355,890,688 bytes | 0 / 0 | Accepted, including the original binder return |
| Exporter R0 | 159.059 s | 1,345,634,304 bytes | 0 / 0 | Internal exit 1, binding failed |
| Independent R0 through shared closeout | — | — | — | No launches |

The exporter recorded 33 completed metadata reads (2,773,829 bytes) of the 40
required. On attempt 34,
`b4-30-z-reflection-repair-v2/sentinel/reference/units/0011.json` had a recorded
size of 490 bytes at open. Its bounded content read raised
`TimeoutError [Errno 60] Operation timed out`. The returned byte count and
closing identity for that read are unknown. The evidence identifies the
operation that timed out. The storage-level cause remains undetermined.

The original binder returned exit 1. Its 5,241-token failure output exceeded
the caller's 4,000-token capture. The subsequent failure-custody command
returned 0 and produced 7,615 tokens against a 6,000-token capture. Both
partial external responses and the complete on-disk domain and native failure
records are retained. The independent caller observed the STOP before
independent R0. R1 payload reads, final filing, lease release and scientific
B/C launches were all zero. The acquired lease remains **HELD**. The attempt
produced no formal version certificate.

## Charges and evidence

| Entry | FULL |
| --- | ---: |
| Shared reservation at first supervisor, counted once | 300 |
| Independent public check | 300 |
| Failed exporter R0 | 300 |
| **Booked under the new contract** | **900** |
| Unused allowance closed | 3,060 |

The separate ceiling was 3,960 FULL. The cumulative known lower bound rises
from 342,699 to **343,599 FULL**, plus unpriced software, control and other
costs. Both copies retain the original returns and a verified archive of 45
generated controls and native receipt files. Independent replay of the two
roles from these records reproduced the native results, RSS and charges. The November 21 failed activation,
its closed allowance, prior charges, unknown costs and cohort seals remain
recorded under their original contracts.

| Private evidence (both copies) | SHA-256 |
| --- | --- |
| Owner budget | `96c2a727428bb7d30c8d2c00dee43c1f42c7f55b73660959cc51c8c33db33f7b` |
| Source and main-check freeze | `c741f81bdd167ed8371892dc161c517230488cea938588088997c652d3af9bec` |
| Independent original preflight | `5a5fe65ed05ca3abf6586c92ee64516c555871047b7dacfd40730c89e1e07235` |
| Original successful activation | `721933368bce0943556a9ae7ae2ce14a9f4ccd7ce56f490ec83589f42c17a4cc` |
| Formal plan | `324cbd507ccb168677540da1c7609f55570a80a5dd3b34c7f132cf688e6b6184` |
| Exporter R0 source-read failure | `d8d8824a82a4440d9f74d3ccbb1ee8a21a76911112c26bb8524fbc578763e85f` |
| Native STOP | `2802563e3b667c1d219952f17cbd9829834545fa07e22eea76819a3a0bd3b711` |
| Generated control archive | `9b238f144df1301d8585f789b4aae7dc3b0d94f847c128d4f7b763e0518c6fb0` |
| Independent STOP and resource replay | `07feb8b571b21f7ed283f6e857b8781205e97328e41cc08a196386d6f7e21668` |
| Verified result and accounting | `8d71bb16e2caaa29da9c1722cbba11844806399d561b280e8311cf441da106ef` |

The next input decision concerns reliable bounded reads of the registered
metadata. Diagnose the timeout from retained evidence first. A new physical
source read or formal attempt requires a separate finite contract. Fixed P/17
remains unrepaired. Uniform stays the default and full fit at 4 GiB is pending.
