# Exporter R0 passed all 40 reads. Independent R0 stopped on catalog identity.

The single formal attempt accepted two of six roles. Exporter R0 read the
registered 490-byte unit in position 34 and completed all 40 metadata files.
Independent R0 read seven bootstrap files. It rejected the embedded B3 catalog
during validation. The new formal lease is HELD. Both R1 roles, shared
closeout, final filing and lease release remained unentered. Formal input
acceptance remains open. [Finite contract](../planning/r0_read_input_recovery.md)

## Diagnosis and repair

In the previous run, reads 32 and 33 returned with closing records. Read 34
reached the bounded stream read after opening the registered 490-byte file.
The read raised OS error 60 before a buffer returned. Its returned length,
closing identity and storage-provider cause remain unknown. The native controller
returned after 120.836 s, inside its deadline. Later the binder
and failure-custody terminal outputs exceeded their limits. Both old copies
retain the failure, the 900 FULL charge, the 3,060 FULL closed balance and the
HELD lease. [Earlier failure](formal_input_published_authority.md)

Four new processes read only the registered `sentinel/reference/units/0011.json`
using the formal reader and its 290-second payload deadline. Each returned
490 bytes with SHA-256
`b75b1942e547a027744bc08f5b70a001cfc309804d00f04f983bc9236e774802`.
All four closing observations matched the registered physical identity.

| Slot | Software and observation | Read time | Result at close |
| ---: | --- | ---: | --- |
| 1 | Previous published reader, SF_DATALESS and zero blocks at open | 10.099150208 s | Flag cleared, eight blocks |
| 2 | Same published reader, new process | 0.000625208 s | Eight blocks |
| 3 | Protected candidate, first process | 0.001036917 s | Eight blocks, original call 4.364 s |
| 4 | Same protected candidate, second process | 0.000702083 s | Eight blocks, original call 3.443 s |

The first observation establishes a local materialization during the new read.
The old failing process did not record flags or block counts. The repair
performs the single-file read and repeat before activation. Preparation binds
both candidate returns and the independent verification to the published tree.
Formal R0 then opens the original file in its normal sequence. The two early
diagnostic receipt and entry files per slot inherited mode 0644 within
0700 directories. The candidate uses explicit 0600 creation. Original files
and permissions were preserved. Physical identifiers remain in private custody.

The return-path repair stores complete native records and transmits their
length and SHA-256. Replaying the old 20,962-byte native stop produced a
386-byte binder return. Its 29,687-byte custody manifest produced a 311-byte
return. A public fault fixture still reports an unknown returned length on a
bounded-read timeout. No read cap, formal deadline or content check changed.

## Publication, independent verification and formal progress

Protected source `6763a8807bcde53d696b73dfc4da0f16665ae37c` passed both
reviews and all four CI jobs on the PR and merged main. Local validation
passed 3,880 tests with two platform skips in 1,576.59 seconds. All 84 execution
paths matched their committed bytes. [Source PR](https://github.com/keith1117/TopoLab/pull/248)
· [PR checks](https://github.com/keith1117/TopoLab/actions/runs/45003630878)
· [Main checks](https://github.com/keith1117/TopoLab/actions/runs/45006696669)

The independent verifier replayed slots 3 and 4 against the accepted registration,
raw buffers, four identity observations and original terminal returns. It exited
0 in 0.267 s. Both readers replayed the 23 anchors and the previous six-role
public certificate for 1,071 members. Fresh preparation returned 0. Independent
preflight returned 0 in 11.577 s with zero source or target reads. Formal activation
returned 0 in 11.691 s. The first supervisor entered 12.059 s after the
original clock began.

| Ordered role | Formal evidence |
| --- | --- |
| Independent public check | Accepted |
| Exporter R0 | Accepted. 40 metadata files, 2,777,259 bytes, including unit 34 with matching hash and closing. |
| Independent R0 | Seven complete reads, 2,600,543 bytes. Each file path, length and SHA matched the exporter. Catalog validation failed. |
| Exporter R1 | No dispatch or payload reads |
| Independent R1 | No dispatch or payload reads |
| Shared closeout | No dispatch |

The first domain failure was `embedded manifest/catalog differs` while
validating the already-read 2,595,684-byte `b3-v1-fits/b3_training.json`.
Its nested independent-reader context records all seven reads and their
closing observations. The outer exporter's read table is empty for this
independent role. The exporter had already verified the embedded manifest
digest on the same bootstrap bytes. The independent reader additionally
hashes the entire serialized catalog and compares it with the B3 **catalog
identity** digest. The published B3 contract defines that digest over the
catalog version and an ordered projection of four fields per entry. The
independent reader used a different representation. The failure carries
the combined predicate's message and does not include a computed catalog
digest. The existing independent-registry fixture substitutes the digest of
the full fixture catalog for the published pin, so it did not exercise this
representation mismatch. [B3 catalog identity](../b3_experiment_contract.md)
· [Independent-registry test](../../tests/test_p17_m2_input_export_independent.py)

The supervisor and collector completed. The binder returned 1 and its
388-byte complete stdout binds the full 3,608-byte native stop. The producer
observed the predecessor STOP. Neither caller reported a secondary graph
failure. A later independent summary command misread the shape of the compact
custody result. The complete original actor result was already retained and
the subsequent buffer audit succeeded. Both callers retained the native
evidence. The cooperative lease marker and acquisition record show HELD.
No payload was read, no formal 1,071-member version was certified, and no
second formal run was entered. The remaining input blocker is the independent
catalog comparison. A future repair can exercise the documented catalog
identity with a public fixture before any new formal decision.

## Accounting and private evidence

| New allocation | Ceiling FULL | Booked FULL | Closed unused FULL |
| --- | ---: | ---: | ---: |
| Single-file diagnosis and candidate verification | 3,600 | 1,200 | 2,400 |
| One formal graph and closeout | 3,960 | 1,200 | 2,760 |
| Total | 7,560 | 2,400 | 5,160 |

The formal ledger includes the shared 300 prepayment once and three role
dispatches at 300 each. The prior known lower bound of 343,599 FULL rises
to **345,999 FULL**, plus unpriced costs. The B3 rejection consumed the
third role's charge. Old failures, balances, unknown costs and scientific
seals retain their original entries. Fixed P/17 remains unrepaired, uniform
is default and full fit at 4 GiB remains pending.

The two private evidence directories hold the original processes' returns,
native failure, four single-file observations, registration and public pins,
and 71 archived generated controls. The original returned buffers contain
physical identities and remain outside Git.

| Evidence | SHA-256 |
| --- | --- |
| New budget registered before diagnosis | `149fe42c5df8849c49d3cb39b62004a8b0d7d82bf3ce1c7bca131f24f9c0b666` |
| Protected source freeze | `74efb6d251191e23c287e84b62919a448f674a8523c4395245c5234b42d72b54` |
| Candidate observation package | `664edec58a06b5517d487f3b87b5f9b24063d6c20ab82f44b7ae8b95a2a3b1b2` |
| Independent candidate verification actual | `3193a2d4936e3b9385bf021d5dfd85b6836491b30ea10c6bfc0007578557b335` |
| Independent preflight actual | `28bfe16f884f28678be9dc3edf6712ee142f73cc4520b3cbe6e6484305c6883d` |
| Formal plan | `5ea3ba87bcd44f7b86024791579d7ee9ca144303211b0a19e7e196390c1c4333` |
| Independent R0 source failure | `67cc3ef7718d4f915918a4bd17b6a90b26d7e3faa6306fffa17f805263dce4a4` |
| Generated control archive | `648e114821ca2dc1ca77dd1f37a57967216d68de40af14137141ee9e58e32d51` |
| Nested reader and native binder audit | `844b7091f47e06ab08e49459c9db41a4ed4f90f5c1b1d0d4ef600d24fe61aa0a` |
| Independent three-role stop and resource replay | `39384e3191be43ee6020cf56bf02bee7223df06fb711317cc29ba89a38c928e6` |
| Verified result and accounting | `996dba655d6bfe2d30066f8261344a89f3a0cc01f56557b1347645773be4ab53` |
