# November 21 formal metadata acceptance and public input timeout

The repaired reader and writer passed formal metadata acceptance on protected
main. The public input rehearsal then stopped at the fourth of six roles.
Formal input admission and the seed-17 scientific repair remain open.
[Finite contract](../planning/metadata_input_20261121.md) · [November 16 failure](full60_input_admission.md)

## Source used for acceptance

[PR 241](https://github.com/keith1117/TopoLab/pull/241) merged as
`b40fc83d569165719dd1b9f26a7b40e198705970`. The first source revision
passed locally (3,663 tests, two skips) but failed the generated-dispatch test
in both Linux runs. It used the registered runtime path to locate a source
file in the CI checkout. The correction separated those paths while retaining
the literal runtime path. Both original failed runs and their costs are retained.
The corrected revision passed the full local suite (3,663 tests, two skips)
and protected-main CI passed all four jobs. The source freeze covered 53
files. Two reviewers checked the 30 changed paths and replayed the caller
before any new metadata attempt.
[Initial CI failure](https://github.com/keith1117/TopoLab/actions/runs/44874870290) · [Corrected PR check](https://github.com/keith1117/TopoLab/actions/runs/44879249596) · [Protected-main check](https://github.com/keith1117/TopoLab/actions/runs/44882220034)

## Metadata

| New attempt | Complete plan (bytes) | Complete certificate (bytes) | Auditor wall time | RSS envelope (bytes) | Finalizer exit |
| --- | ---: | ---: | ---: | ---: | ---: |
| Public | 3,871,672 | 4,630,368 | 9.989 s | 642,908,160 | 0 |
| Formal | 13,502,329 | 14,567,437 | 10.038 s | 1,071,071,232 | 0 |

Both plans and both certificates fit the original 16,777,216-byte limit. The
formal preflight preceded dispatch. The auditor checked all 23 registrations.
Both independent-inode certificate pairs and their actual finalizer returns
passed replay. Original registration reads and Foundation helper calls were zero.
Formal certificate SHA-256 is
`56a7ef886ba8c634eb505004f0498d739c45cafa4bd63d925e424f92811da167`.
The November 16 attempt remains a consumed FAIL at 22,943,707 bytes, FULL120,
RSS unknown.

## Public input

| Ordered role | Actual result | Caller elapsed | RSS envelope (bytes) | Dispatch charge (FULL) |
| --- | --- | ---: | ---: | ---: |
| Independent public check | Accepted | 13.534 s | 1,356,693,504 | 300 |
| Exporter R0 | Accepted | 157.132 s | 1,620,738,048 | 300 |
| Independent R0 | Accepted | 19.910 s | 1,670,660,096 | 300 |
| Exporter R1 | Native timeout, external receipt deadline missed | 1,198.608 s to supervisor return | Full role unknown | 1,200 |
| Independent R1 | Unlaunched | — | — | 0 |
| Shared closeout | Unlaunched, reservation counted below | — | — | 0 |

Exporter R0 recorded all 40 public metadata reads. Exporter R1 began 279 of 558
public payload reads and recorded byte counts and hashes for 278 (9,744,782
bytes). Its native timer ended the registered command at 1,190.06 s. The native
exit was −15, and cleanup observed the process group gone. The inner RSS
measurement including controller and sampler was 639,827,968 bytes. The full
role envelope requires the missing external record.

The supervisor returned exit 0 with `PENDING_EXTERNAL_EXIT` 1,198.608 s
after its original request. The caller reserves 10 s inside the 1,200 FULL
role, so the return missed its 1,190 s boundary by at least 8.608 s. The
caller recorded STOP before dispatching the record step. The independent
caller observed that predecessor STOP and closed its next role. Both retained
their original returns. The public custody marker still records HELD.
Final filing, lease release, formal input preflight, both formal readers and
the 1,071-member version verification were never launched.

The next engineering question is whether the exporter can finish all 558
public reads and return through its caller within the frozen deadline.
The run establishes the work completed and the return latency. Time spent
on individual filesystem operations remains unknown. Finishing 558 reads
within the same interval would require at least 0.469 completed reads/s,
before allowing time for the external return. The observed rate was 0.234/s. Any new named attempt
requires a separate finite decision.

## Budget and retained evidence

The window was 05:21–17:21 UTC on November 21. Its ceiling was 8,160 FULL.
The two metadata attempts consumed 240. The public input ledger records 2,100
in four dispatch charges and a separate, nonrefundable 300 shared reservation
at first launch. The ledger therefore booked **2,640 FULL**, closing 5,520 of the named ceiling
without transfer. The elapsed-time rule also includes the mandatory 10 s tail.
The supervisor alone implies at least ceil(1,198.608 + 10) = 1,209 FULL
for R1. Replacing its booked 1,200 with that floor adds at least 9. The new
cost lower bound is **2,649 FULL**, raising the cumulative lower bound from
334,890 to **337,539 FULL**. Ancillary fees remain UNKNOWN_NOT_ZERO. The old all-paid cost
12,721.16417100014444982 exceeds 7,200. Earlier failures, quotas and seals,
the 4 GiB full-fit requirement and the uniform default remain in force.

Two external copies retain the certificates, raw caller failures and a verified
archive of the public control files and native receipts. The original 25 dirty
files in two workspaces matched their baseline bytes, Git HEADs, indexes and
status after both callers stopped. Generated evidence stays outside Git.

| External record | SHA-256 |
| --- | --- |
| Finite budget registration | `9200b495ea726459094868265e6cf61b3364e10515a91e815db2baa95dbc0d47` |
| Metadata acceptance after both replays | `84e25808d6f6fe8027a5d67cad6a875b53708e1675ac0ac1a28abbba24b90a6d` |
| Producer failure with original tool returns | `56131f73facf95259903b433dbc21929ae227e190708b291dd56447e8d81dd71` |
| Independent predecessor STOP | `036595a8d625c1169de41639c4fe9f4d5d5fc2e44e83758615ba5a95ccf0cb35` |
| Input STOP, observed clock, charges and formal frontier | `122cc67c422137d2b7de88202b3f68e74ce36e3dd96b1fa96e19ef81fe54435a` |
| Independent closeout of roles, costs, lease and workspaces | `98fa36bf5a0422086b21d865713add77aced8ccbbdfbfa739f6e377ac31c3f7d` |
| 78 public control files and native receipts | `075458b2f639e1926b380ad6dbe69f33dbd6dba3b39c7d73e9849682804fc0ad` |
