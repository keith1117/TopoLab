# Formal input campaign closed at 3/6

The final graph accepted the independent public check, exporter R0 and
independent R0. Each R0 verified all 40 metadata files (2,777,259 bytes).
Exporter R1 read all 558 registered payloads (567,896,449 bytes) and wrote
a 1,071-member manifest. Its role stopped during supervisor event filing.
Independent R1 and shared closeout never entered. The campaign finished
without a formal input certificate. The A3 lease is HELD.
[Released source](https://github.com/keith1117/TopoLab/pull/254)

## Changes verified on formal data

- The coordinator writes its own launch note. Scratch scheduling and duplicate
  activation tests passed, and the activator exclusively created the formal entry
  in all three new attempts. Both R0 readers accepted all 40 metadata files
  on A1 and A3. [A1 results](formal_input_cycle_a1.md)
- A1 stopped on exporter payload 35. Two separately charged single-file
  checks obtained all 472,469 registered bytes. The released exporter
  limits label reads to the registered length plus a growth-detection byte.
  A3 completed the payload table with all 558 expected hashes. The file
  provider underlying A1's Errno 60 remains unidentified.
- Automatic approval review rejected the A2 recorder filing because a
  separate filer might duplicate or alter the original actor's evidence.
  That request was sealed and never resubmitted. A3 bound each filing to
  the frozen program, plan, exclusive actor entry and paired original
  return. Individual approval and exclusive native writes remained in
  force. A3 filed both first-role events, bound the role and released its
  successor. [A2 results](formal_input_cycle_a2.md)

The released A3 source was `f6fb834344e60707a570ae3218af5df733897ce4`.
Local validation passed 4,181 tests with two skips, and all four protected-main
checks passed. The 95-file execution tree has SHA-256
`c461f5b66a59f7eb6b5b026ae1cd63da6ade3d597a6e843b1c1b79a4f32fb1a4`.
The independent offline verifier returned 0 in 0.570 seconds. A fresh
preflight returned 0 in 12.829 seconds and replayed the registered public
evidence before activation. [Main CI](https://github.com/keith1117/TopoLab/actions/runs/45143048108)

## Exporter R1 and the stopping condition

| Observation on A3 | Sealed result |
| --- | --- |
| Exporter and independent R0 | 40/40 each |
| Exporter R1 source table | 558 distinct paths and 558 matching expected hashes |
| Exporter version | 1,071 distinct manifest paths, version `b6f7e44be329f4914620d8154a21ade1aba5a9c158fc34fe44e0accb1bd31c33` |
| Independent R1 | 0/558, role never dispatched |
| Native R1 payload process | Exit 0, 1,159.41 s elapsed, 28.07 s user CPU and 6.74 s system CPU |
| External R1 supervisor | Exit 0 in 1,181.631 s, reporting pending external exit |
| Recorder, bind and release of the R1 role | Never entered |
| Shared closeout, final filing, lease release and certificate | Never entered |

The R1 actor reserved ten seconds of its 1,200 FULL window for completion.
After preserving the supervisor return, it requested the privileged event
filing with 8.165 seconds left before its dispatch deadline. The first tool
response returned an open session after 6.760 seconds. Only 1.405 seconds
remained. The frozen caller requires at least five seconds for an owned
session poll. It retained the live return and closed the graph. The
independent actor observed the predecessor STOP. Both actors reported an
empty secondary-error list.

An empty, read-only poll of that same session after the stop observed exit 1.
The original filer had consumed its single-use intent. During setup replay
it saw the new STOP marker and exited before writing a native SUP event.
The post-stop observation is separate from the frozen caller's original
return. The R1 source table and exporter manifest survive. The independent
payload comparison, accepted R1 resource evidence and version agreement
remain outstanding.

The evidence localizes the stopping condition to the remaining role time at
event filing. The native payload itself used 1,159.41 elapsed seconds. The
receipts do not attribute this interval to individual reads, output writes
or other waits. On the three accepted A3 roles, the interval from supervisor
return through recorder return was 22.718, 22.898 and 28.001 seconds in
formal order. Through binder return it was 44.812, 45.352 and 54.065
seconds. These measurements bound those three observed roles. R1's
corresponding time remains unknown. A future candidate must demonstrate
enough time for its whole SUP, recording and binding sequence within
the existing cap.

## Ledger and sealed custody

| Campaign allocation | Ceiling FULL | Booked FULL | Closed unused FULL |
| --- | ---: | ---: | ---: |
| A1 formal, 3/6 | 3,960 | 2,400 | 1,560 |
| A2 formal, 0/6 | 3,960 | 600 | 3,360 |
| A3 formal, 3/6 | 3,960 | 2,400 | 1,560 |
| Independent offline work, three calls | 2,400 | 900 | 1,500 |
| Targeted original-file rechecks, two calls | 7,200 | 2,400 | 4,800 |
| **Campaign** | **21,480** | **8,700** | **12,780** |

The known floor rose from 346,899 to **355,599 FULL plus unpriced costs**.
Each formal charge includes its shared 300 once. All three attempt slots are
consumed. The two leases held at entry and the A1, A2 and A3 leases remain
HELD. The two pre-existing working copies retain their original changes.
[Campaign contract](../planning/formal_input_cycle.md)

| A3 paired evidence | SHA-256 |
| --- | --- |
| Offline verification actual | `d6706c8eac22d4ab3d5b5dda93747adba1b20405abcdebbd38a37be6a23d28ed` |
| Preflight actual | `d198ec115f758ddcc83765d1127ea537c55e87a8c3d2a4518dcfbaf15661582a` |
| Independent R0 source proof | `e02fa38d80110ec0ba9a4d4189c195db2161839a2a0fcc8d02c0d41adc80e1c2` |
| Producer original return, 74 tool rows | `8b1f7895c6adeb570280727ab8b9fec5d6b50a2618536ba218dd7a6e448f6878` |
| Independent original return, 93 tool rows | `a2d62431c0bda08ac0699e43fee07c516884a2fb006fba4d54ec807efafed2c9` |
| Post-stop terminal observation | `abb32a06c6dfd3059c303353d3fbdbee7e8f823475d086a256d382b6b0224424` |
| Native control archive, 87 files, 13,668,964 uncompressed bytes | `d339b404cd20ed35508e3e487f3d08b51553ad417bf5377f1645811d4e5a2d7d` |
| Native archive member index | `85e787a78446e87af059e94be9002a7ea9c31cd9266b5b9b3f42766986945e42` |
| Attempt closure | `57982c76a2c28eab3f445b5bfd5fe0d6b88d32c86c74395d521c362a85e03722` |
| Independent terminal audit | `0b2cb8c84922975ab219dccb90500b8fab0e60e8db28e02947fa907f653e62f6` |
| Final evidence inventory, 87 matching entries in each directory | `ab804ff6cadf1076909665a751b5831d523969faefabe126a83c19c6bfa818bc` |
| Campaign ledger | `c9c83fd0406c1859c09b0cab2c23d3144f20722ec7a3507218d681ee42347b66` |

The independent auditor replayed the original native returns, samplers,
binders and releases for all three accepted roles from the paired archive.
For exporter R1, 2,074 inner samples support a partial RSS measurement of
616,120,320 bytes. Completion of its external recorder and full resource
measurement remain unverified. The audit retains two corrected checks. A
standalone R0 helper lacked the external 23-entry registration map, so
the auditor used the accepted independent proof together with the archived
registry bytes, identities and order. The auditor also corrected the manifest
authority comparison to use the plan's contract digest. Neither correction
advanced a formal role.

Further work requires a new finite authorization. A timing diagnosis can
use the sealed returns and a public fixture with the 558-payload and
1,071-member workload. A new formal attempt would require a verified
improvement within the current limits, its own contract, source freeze,
independent preflight, target and budget of at most 3,960 FULL.
