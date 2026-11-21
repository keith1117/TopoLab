# Staged public registration, public rehearsal and formal activation stop

Both readers verified the 23 physical anchors at the fixed public source. The
six-role public rehearsal accepted all 1,071 version members. Formal preflight
passed. Formal activation returned exit 1 before creating the generation,
acquiring its lease or dispatching its first role. The activation and both
caller returns close this attempt. [Finite contract](../planning/staged_source_input_acceptance.md)

## Published source and registration

[PR 244](https://github.com/keith1117/TopoLab/pull/244) merged as
`259766dbe6ee1598a6100e58fe2b669fd2907841`. The 305-file freeze bound the
source, both reviews and the protected-main checks. Local validation passed
3,739 tests with two skips in 1,721.86 s. Two superseded local runs ended after
332 and 318 passing tests. Their elapsed time, the earlier focused failures and
the host-native rerun remain in the private evidence.
[Exact PR checks](https://github.com/keith1117/TopoLab/actions/runs/44953628600) · [Protected main](https://github.com/keith1117/TopoLab/actions/runs/44957039144)

Both availability checks passed. Each reader then opened the same 23 public
files and hashed 75,085 bytes. Device, inode, size and nanosecond modification
time matched across the declared, opened, post-read and reopened observations.
The independent certificate audit passed, the finalizer returned exit 0 in
0.346 s, and the new registration lease was released. The existing formal
metadata certificate also passed replay against its original verifier and
finalizer. The replay required zero new original registration reads.

## Public rehearsal

| Role | Caller interval (s) | Native RSS envelope (bytes) | Native dispatch (FULL) |
| --- | ---: | ---: | ---: |
| Independent public check | 9.007 | 853,491,712 | 300 |
| Exporter R0 | 19.942 | 995,115,008 | 300 |
| Independent R0 | 13.208 | 1,157,529,600 | 300 |
| Exporter R1 | 23.842 | 1,470,414,848 | 1,200 |
| Independent R1 | 22.771 | 1,824,325,632 | 1,200 |
| Shared closeout | 23.436 | 951,336,960 | 0 at dispatch, 300 prepaid |
| Final filing | 13.709 | 883,949,568 | 180 |
| Lease release | 9.331 | 889,520,128 | Fixed native charge unreported, observed floor 20 |

Every listed action returned both supervisor and recorder exit 0. The lease
was accepted as a metadata action. Its nested resource evidence records the RSS
shown above. Its top-level full-role acceptance flag is false. The exporter
and independent reader each processed 40 metadata files and 558 payloads.
The exporter recorded 18,167,884 metadata bytes and 108,544,941 payload bytes.
Independent R0 compared 9,361 fields and R1 compared 7,325,084 fields. The
backup matched all 1,071 members. The new public lease reached RELEASED.
The public certificate returned exit 0 in 3.448 s, 257.000 s after the original
graph request, inside its 4,500 s window. The public version is
`c9ad14f2ca9c5e4d6859aa22dead7f98ef2ebd8ce8c24debf94ed1b634a8bd73`.

## Formal input

After both preparation commands returned exit 0, the independent preflight
returned exit 0 in 7.794 s with zero source or target stats. The producer then
called formal activation once. It returned exit 1 in 11.176 s. Its first error
was `hash-bound execution authority freeze differs`. The independent waiter
observed the producer STOP and exited its graph. Both callers retained their
original events. Formal roles accepted **0/6**. The activation stopped before
target setup, shared reservation or source reads. Formal filing, version
certification and scientific B/C had zero launches.

The formal plan builder reserializes the parsed authority and hashes those
bytes into both `contract_sha256` and `binding.execution_protocol_sha256`.
The independent verifier hashes the published contract file. Recomputing just
these hashes from the merged Git blob reproduced the failed comparison.
The activation stopped before writing the plan. The values below follow from
the published code path. The earlier software checks exercised the builder
but missed this comparison against the independent verifier.

| Representation of the same JSON object | Bytes | SHA-256 |
| --- | ---: | --- |
| Published file | 13,314 | `753e1b7c90fb41aa90f484b6df80570db497e1692d5e5ea752a0e18fedcb1893` |
| Compact serialization used by formal activation | 11,810 | `e6a5dcd6762b02db78931d49cd1e8abe0efac2c18ee163a8092e0c7e21cb7a5f` |

The next software repair is to derive both formal plan fields from the exact
published authority buffer. Exercise the formal plan builder and independent
comparison on a formatted contract without opening the original input or target.
A subsequent named activation requires a new finite grant. Fixed P/17 remains
unrepaired. Uniform stays the default and full-fit evidence at 4 GiB is pending.

## Accounting and custody

The new ceiling was 9,120 FULL. Registration used 1,200. Public roles and
filing booked 3,780, including the prepayment counted once. The contract set
aside 180 for the public lease action and the action ran, bringing the
contract allocation used to **5,160 FULL**. The 3,960 formal allocation closes
unused. The failed activation consumed real time before chargeable role entry.

The public lease's native record gives a 20 FULL lower bound and leaves its
fixed charge null. Combining that observation with 4,980 fixed charges gives
5,000 FULL on native evidence alone. The new contract books 180 for the executed
lease. Counting it once gives **5,160 FULL this round** and raises the cumulative
known lower bound from 337,539 to **342,699 FULL**. Control, software and other
unpriced costs remain unknown. The earlier metadata failure, the prior 3/6 rehearsal with
278 payload receipts and its HELD lease, and the old all-paid result
12,721.16417100014444982 above 7,200 remain recorded. All consumed quotas and
the final, conditional and unused cohort seals stay closed.
[Prior result](metadata_input_20261121.md) · [Public throughput](public_input_r1_throughput.md)

Both private data roots retain the registration proof, caller packets, STOPs
and a byte-verified archive of 164 generated public control and native receipt
files. Both original workspaces retained their HEAD, index, status and all 25
dirty file digests.

| Private evidence | SHA-256 |
| --- | --- |
| Finite budget registration | `7212bce05d9f1d953c44b800c59d941e2e1e44111777845ae57f2479be170687` |
| Public physical registration certificate | `e059ea5b8945f4eda69c2e13cb6675552a5b0de401033ed1822bb5bdf1fcdcc8` |
| Public 1,071-member acceptance bundle | `b5ffbe59de881707a2794118470c8c01fdef62e8860b668d91c9b312c3bb8f53` |
| Original public certificate command return | `46a1f6ae72925c9bf28bb6eb57f7221999b9095d6d6244e220d8a31a573ca72b` |
| Public controls archive | `fe4727c30cb340d01ad0478f02c51d15001d9addcad366ec58d18eaa00d0c5db` |
| Independent formal preflight return | `c6c1231d9fe631d0a31dc79f89b02f0601ee3bb24f4e70f5bc4efbeaf8160656` |
| Formal producer / independent STOP | `c70d77bcbf4c9994b3c066f4392a082b7c490f1034f58359cd2499b247a3b597` / `c173f12db8c69f121c9b834644f4cf97eb26c8cd08f93ab16e60d26764e5b6e4` |
| Combined outcome, costs and workspace checks | `2f5ed579f3accf2ba883f28e0003b715c38c211e83a60354bf088ce594316f7e` |
| Independent failure and accounting review | `1fddc2b25596d8538d5e1d6388e84da450c381f35f8413c736dcc9ffe147dc89` |
