# Public input R1 throughput on a rebuilt fixture

The exporter completed all 558 payload reads and produced the 1,071-member
version on a fresh local reconstruction of the stopped rehearsal's public
fixture. An independently implemented reader and comparator checked the full
result. The externally observed software command returned exit 0 in 22.412 s.
The historical graph still has three accepted roles. Formal input is unlaunched.
[Original timeout and frozen role clocks](metadata_input_20261121.md)

## Input and output identity

The public fixture generator rebuilt the 540,224-byte registry exactly. Its
40 metadata references matched the retained R0 reads by path, byte size and
SHA-256. The complete new journal also matched all 278 retained payload
receipts and the original 279th attempt in order. Both readers checked every
payload against the registry. The archive comparison used retained control
records. The stopped rehearsal, its HELD output lease and the historical
public source received no new access.

The benchmark used source SHA-256
`fcbd4a6365745aec1070cfa37aa5d1c95343566bf2f4f959b4fbdb616f2cb402`
and the original acquisition contract digest
`b49a5542b34a74bb4209ba736acfc7b414eed90afc7d95f212f0fd9b6d4b5ba2` in
the version manifest. An exploratory exporter probe used the generated fixture
description's digest and produced a different version. Both observations are
retained. The benchmark rejects a changed acquisition contract before creating
a fixture. It accepts no input path. Run the checked-in command in the locked
checkout. Each invocation prints the location of its new private directory.

```sh
uv run python scripts/benchmark_public_input_r1.py
```

| Final measurement | Observed value |
| --- | ---: |
| Generate fixture, register and independently compare R0 | 2.069 s |
| Export 558 public payloads, 108,544,941 bytes | 6.530 s |
| Finish and read back the generated content | 0.272 s |
| Independent check of 558 sources, 7,325,084 scalar fields and 1,071 members | 10.319 s |
| Native wall time, including interpreter startup | 19.27 s |
| Native command, controller and sampler RSS envelope | 665,419,776 bytes |
| External request through terminal tool return | 22.412 s |

The producer and independent comparator agreed on version
`d5e9552d0ba203db7710b03fc37ce08dfb1f72449887da3ff86badb9cbde94ea`.
A separate full exporter profile on newly generated data in the data workspace
measured 0.557 s in the 558 source reads, 2.515 s in 1,071 namespace snapshots,
and 0.087 s in 3,263 file and directory sync calls. These inclusive measurements
can overlap. The historical run retained no per-operation timing that could
identify which operation consumed its 1,190 s. No scientific speedup follows
from these timings.

## Decision and budget

The selected public source is staged at
`~/Library/Application Support/TopoLab-public-fixtures/exporter-r1-20261121-v1/source`.
Its local APFS volume passed the existing writable-local check. Exclusive writes
and byte readback matched all 598 source files (40 metadata, 558 payload),
126,712,825 bytes in total. A second supervised export read all 558 payloads
from this final path. Its export took 7.000 s, finish took 0.324 s, and the
independent local check reread all 1,071 members in 0.285 s. The native command
took 7.69 s, and the original external invocation returned exit 0 in **11.443 s**.
It produced the same independently compared version as the full fixture run.

The next step is a new public registration contract bound to this exact staged
path, followed by independent strict 23-file registration there.
The existing public certificate binds physical observations at a different root.
Restoring the retained archive also creates new physical files. The earlier
formal metadata acceptance stays attached to its original formal source.
A new named input contract must check these bindings and preserve the external
return reserve through the six-role public rehearsal before any formal input.
The benchmark exercises the exporter, namespace checks, durable read journal,
readback and independent comparison. Live certificate admission, actual
SUP/REC role pairs, and lease release remain separate integration gates.

The new software window runs from 10:28 to 14:28 UTC on November 21.
It caps isolated timing trials at 12, with 3,200 s total and 1,190 s per trial,
two full local suites and six CI runs. Named FULL is zero. The previous
2,640 booked FULL, cumulative measured lower bound of 337,539 FULL, other
UNKNOWN_NOT_ZERO costs, sealed cohorts and all closed attempts are retained.
Both original workspaces matched all 25 recorded file hashes, HEADs, indexes
and status after measurement. Fixed P/17 remains unrepaired. Locked sync, Ruff,
mypy and the whitespace check passed. The full local suite passed 3,664 tests
with two platform/fixture skips in 1,578.35 s.

| External evidence, retained in two verified copies | SHA-256 |
| --- | --- |
| Terminal tool responses from the measured script | `b090fad19352ecc12cdde905e2517e98f4fdf9f38aafedab64d93e6d14f9cd13` |
| Generated source, output and result, 1,672 files | `ddb3161dafeb2b039cb1f2887ff0ba55c0752bafd97c6038da91022c2735e1c6` |
| Member index for that archive | `185ae72128ff9dcb869ebf2697c2aff09a46c5821547b4d29dd88d187ca445af` |
| Staged source candidate receipt | `2a30ad2fb1c43aa42c7edbcaa3b2affe7a9e70a449a6a064a51085f3f57e2357` |
| Full exporter and member verification at the staged path | `02978fd716e944071e65e66cb3d46e5fcf7a5f35929ee38afd808ae12923d3bc` |
| Input comparison, cost and observed time | `7faead4010aa568dcdd70eebc7707785376766286777ed5e992adc9f44ee4b4a` |
