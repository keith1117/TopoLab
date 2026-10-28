# Main CI diagnosis and failure-result closeout

The owner explicitly authorizes this new recovery and finite funding on
2026-10-28. The [new protocol](../planning/p17_m2_ci_recovery_closeout_protocol.json)
keeps every old allowance closed. Source2 remains a correct strict-unbound STOP;
input acceptance, B resource admission and fixed P17 repair have not occurred.

## Confirmed CI mechanism and diagnostic repair

Fresh remote main was627e4d9d4068ff485f1aae45c39610b406a573c2, tree
700db6f8c0662a2653e2db629a3a42a0f52774a4. PR228's exact-head run40465991026
passed all four jobs before its protected merge. Main run40469234730 attempt1
quality job122072016288 failed with its pytest step cancelled.

Independent raw job-log acquisition found a runner shutdown signal at
2026-10-27T08:17:21.2798071Z, followed by cancellation at08:17:21.3567312Z.
The raw log equals the attempt ZIP's job log byte for byte. The signal's initiator
and upstream reason remain UNKNOWN. The workflow has no quality-job timeout or
concurrency rule. Neither the roughly30-minute duration, push actor nor earlier
local watch termination identifies a cancellation actor. No assertion failure
was established by this interrupted run.

The prior inline diagnostic source was not retained. Its documented
`StopIteration` came from searching the outer command envelope for jobs rather
than decoding its stdout. A public CLI regression reconstructs that assumption;
it does not claim byte-identical historical source. It failed with the expected
exception before the minimal repair. The initial uv cache-permission failure
was not a test run and is retained separately.

The new [diagnostic CLI](../../scripts/p17_m2_ci_diagnosis.py) decodes a successful
recorded command or raw gh JSON, checks the expected commit and unique quality
job/pytest step, and emits structured rejection for missing, conflicting or
malformed records. It preserves input hashes and raw integer timestamps. Failed
or unobserved command returns cannot attest to stdout. The supplied log's
provenance is explicitly caller-controlled; its shutdown substring alone is not
an independent provenance certificate. The initiator remains UNKNOWN, and CI
status grants neither input acceptance nor scientific success.

Public CLI tests:18 passed. Different-author Standards and Spec reviews found
zero issues in script e99d7825935700d85d10bcc70537bca458938f27027eae7d5faa00d7300be3e4
and tests8aa57c246191b37328d2043d388f739d1f1cf301583e29a8aba1d14d1554b587.
Independent real-record replay returned0 and preserved exact timestamp integers.
All five local checks passed; complete pytest3004 passed/1 skipped in2117.25s.
The raw command wall and output hashes remain external; this repair's exact
PR/main CI and final retention supplements remain pending at this report's
frontier. External actual returns control completion.

One full same-source workflow retry was registered before dispatch. Its actual
gh command returned0; attempt2 subsequently passed all four exact-main jobs. This is a new
software CI charge, retaining attempt1, not an old source/scientific retry.

## Old failure and accounting facts retained

Source2 attempted6 metadata reads, completed5 hashes and read no payload.
The sixth459-byte unbound metadata file changed mtime by109ns; hash/closing
were not completed and content/writer remain UNKNOWN. The earlier prebound45ns
and93ns changes passed exact hash and closing checks. Three of six roles launched;
the shared closeout checked43 NEW failed-prefix members/521343B and returned the
original STOP. The generation and backup remain HELD and quarantined.

Both original12600-second author phases started05:59:07.911Z2026-10-27.
The result deadline08:22:07.998Z was missed. The separate600-second pending-CI
rescue preparation also exceeded its cap: at least625.236169s, overrun at least
25.236169s. Its formal fallback stager/archive calls were0 and closed unused.
The last emergency packet command failed its first deadline assertion before
creating a directory. Those failures are retained; this new grant cannot make
their original windows pass or supply missing old final-return timestamps.

Independent accounting reconciles the known closed upper subtotal
96108.43293203103603 seconds. It excludes the initial9000-second unknown-endpoint
encumbrance. Adding that and source2's25200-second two-author reservation gives
130308.43293203103603 seconds of reservation arithmetic, not actual elapsed or
an established actual upper bound. Source2's final endpoints and tail delays
remain UNKNOWN. All old unspent allowances are unavailable.

Source1+source2 formal calls total11; source2 paid FULL900, with2700 and filing180
closed. Public61 calls/FULL7860 is only the remedy2 three-generation subtotal;
the older all-action public total remains UNKNOWN. FULL and author wall are
overlapping accounting views, not additive charges. Monetary/API/CI fees remain
UNKNOWN_NOT_ZERO; no new external paid commitment is made.

## New retention and remaining scientific entry

New paired metadata snapshots use the protocol's fresh literal roots, exact
whitelist, private modes, independent inodes, complete hashes/decompression and
an outside anchor. Permanent0555 is not an integrity premise. Earlier complete
v14/v15 regression archives stay at their original independently anchored paths;
the new snapshot does not claim to recreate already-lost temporary failures.
The exact candidate contains2002 old metadata files/81432477 bytes. Four older
large public fixture-tree tar files remain at their original historical hash
anchors and are explicitly listed as exclusions; this does not reduce the
40/558/1071 scientific input requirement. Their original review/receipt records
remain in the new metadata whitelist; fresh rehash/backup of those tar files is
not claimed.
Public regressions first exposed missing frozen-file hash/tuple enforcement and
failed-read observations in the new stager. The repaired helper retains every
available raw observation, bytes/hash and primary/secondary-close errors, and
rejects a wrong frozen hash or tuple. Independent public GREEN and the complete
stage/archive/replay chain pass. Separate public tests exposed missing current-
leaf observations and a write error masked by a secondary close in the new
archiver copy; its minimal fix preserves the primary and attempts every owned
FD close. A directory-namespace failure then exposed a parent/last-child
observation mismatch; the second and final context-repair round preserves both
namespace observations on the correct directory. Final independent public
leaf/copy/namespace regressions and the complete two-archive chain pass.
The previous archiver, every public RED/failed harness and all failed prefixes
retain their bytes.
The metadata-freeze helper's public check also rejected its first non-strict
`False == 0` guard; its int0-only guard passed four public cases. Its first real
freeze then stopped while enumerating a pytest-generated `current` symlink,
before hashing old metadata or creating the job/staging/archive. The raw failure
and its0.062773-second command are retained. The failing link's original tuple
was not captured and remains UNKNOWN; later observations cannot fill that gap.
One prospective finite remedy permits only one more real freeze. Public RED
then GREEN verifies narrowly registered pytest aliases: raw link/target/closing
observations become metadata, aliases are never followed or copied, and real
sibling-directory leaves enter once. Other old/scientific symlinks still reject.
A further public RED exposed misattribution of a failed pytest-return check to
the prior candidate file; the minimal fix reads that actual-return file with
the reviewed exact reader and retains its own observations. The final eleven
independent public checks pass for freezer5aaf96cc, before the real retry.
The second and final real freeze returned0 in0.630525s, binding2397 regular
leaves/82682939 bytes and24 receipt-only public aliases. Distinct review checked
every source buffer/tuple and predicted the exact staging manifest before entry.
The single real stager returned0 in1.046689s and produced2523 members, including
125 implied directories and the2103342-byte manifest:84786281 logical bytes.
Its independently reviewed manifest matches that prediction exactly.

The single real archiver returned0 in1.892596s. Both fresh roots contain the
38233810-byte archive, SHA1179a1e68c92257f0a36aab38838692275e27328c7a05e58b18a17ca3e12370e,
and raw-member manifestd478c1f43cce61c3da9599802c41f7f0abf281a7378496f0e4b19af7b084ce37.
The archiver and a separate author fully replayed both copies. Independent
verification read each gzip through EOF/CRC, checked the exact2523 tar members,
every byte/hash/type/private mode and distinct inodes for all six artifacts.
The first independent validator rejected the manifest's documented exclusion-map
shape because it assumed a list; that validator failure and a later tool-parser
failure are retained. The corrected validator returned0 without rerunning or
modifying the archives. An integrity anchor outside both retention directories
binds the six artifacts, complete independent replay and actual helper returns.
Protected PR/main CI and fresh paired publication/author-endpoint supplements
remain pending at this authoring frontier.
No old original or Library generation was read for this snapshot. New late
retention and helper returns cannot replace UNKNOWN old source2 endpoints or
turn its original result-window MISS into PASS.

All25 pre-existing dirty file bytes, HEADs, index semantics and status match the
original preservation baseline at new entry. Workspace A's raw index bytes
differ from the previous action's last snapshot: five cached-stat entries changed
without staged object/mode/path/flag changes. Writer and timing are UNKNOWN;
the index is preserved in its observed state. Workspace B's raw index matches.
The original source/sealed sites are not reset, cleaned, stashed or chmodded.
The subsequent read-only25-file check also passed, with both raw indices exactly
matching this recovery's entry observations.

A separate optional read-only check of the two old v1 publication-closure records
returned1 on the exact reader's FD-after identity assertion. Its ad-hoc caller
failed to persist the exception's observations before exit. The failing ordinal,
raw tuples, changed field, returned buffer/hash and exact command wall therefore
remain UNKNOWN; continuous author wall includes the whole check and wait. This
recording gap is retained. The check is stopped without reread or later-stat
backfill. The old historicalf2586bbd anchors remain historical facts, but their
current hash equality was not reconfirmed. No intentional write/chmod/reset,
scientific-original or Library-generation access occurred. This separate check
does not invalidate the independently frozen NEW metadata snapshot or supply
scientific input. Future evidence checks use the reviewed observation-preserving
failure path; no retry of this optional old-scene check is authorized here.

Independent feasibility review finds a new M2 attempt conditionally feasible.
Twenty-three R0 members still lack pre-read SHA and must retain strict identity
checking. The old failed member cannot be post-hashed or a failed generation
reused. The current adapters hard-bind old authors, targets and two consumed
attempts. A reviewed new compatibility identity and publication are necessary
before one NEW exact-whitelist attempt; this is an engineering entry blocker.

The budget reserves enough finite source/B/C work subject to actual readiness.
The independent conditional36000-second clock allocates at most4500 source,
7200 source result,14760 B+C and7200 scientific result seconds, leaving2340
for other charged work. Each14400 result figure in the initial reserve is a
ceiling, not two simultaneously fundable allocations. Before any dependent family starts, the final allocation reserves three normal
publication families with four CI runs each: push/PR/main plus at most one
inspected same-head hosted-interruption retry. The running recovery's six-run
limit stays unchanged; cumulative ceiling18. Two still-unstarted software-remedy
full campaigns supplement the current four, cumulative maximum6, only when
remaining clocks can fund them. No scientific retry follows a real FAIL.
A prospective10800-second suballocation from the unstarted root reserve funds
one7200-second independent-adapter implementation and two1800-second fresh
reviews. Root's conditional cap becomes39600; independent remains36000.
The total187200 author-second ceiling and every running cap remain unchanged.
The initial128 public-native-CLI limit does not define an all-OS-process census.
Explicitly registered native-role trials in this recovery are known0; the total
native/OS subprocess population of ordinary tests/CI has not been aggregated
and is UNKNOWN, so whole-action128-cap and30240 actual-native-FULL compliance
are not certified. Synthetic
fixture FULL is not scientific paid execution. Every test/CI wait remains in
continuous author wall, and monetary/CI fees remain UNKNOWN_NOT_ZERO.

Accepted40-metadata/558-payload-per-author and1071-member input precedes B;
independent B resource acceptance and the frozen scientific contract precede C.
The fixed18-case panel, H17 primary, quality/speed/target/no-regression rules and
4GiB empirical RSS/complete-exit evidence remain required. Historical
12721.16417100014444982>7200 remains permanently FAIL and full fitPENDING4GiB
remains open; these do not alone refute the separate prospective M2 query route.
No new scientific measurement supports a P17 repair claim. Uniform stays default.

## External evidence bindings

Root: `/private/tmp/topolab-ci-recovery-20261028`.

| Evidence | SHA256 |
| --- | --- |
| new-budget-registration-v1.json | ca0338f0c3c4b7c31c83233d0c0f083efadf3f0b3435e07590af6739c7fa17b0 |
| unstarted-source-science-publication-budget-v1.json | e7b0978e0e473d8f001dc200eca6262fe5c653f4fd36a386203966483cfd3171 |
| unstarted-dependency-allocation-v2.json | 1a5dab49373eb567c7c9fdcffe74c0badfd36d81ebd03d89c76e6a340f0652e9 |
| independent/main-CI-cancellation-independent-forensic-v1.json | ab813d84384bb7f5dd135b62d8691f23fabf66196d29029f9bd64fde10ef3a56 |
| independent/main-attempt2-independent-actual-success-review-v1.json | d48e8fc2ee23e6719d7ee9d13791e5e22be67eef7dcc6a6368f3c009f6e9de40 |
| previous-action-final-allocation-closure-v1.json | 9fe6770f56595f4f0ebd995a727f0a2068efdc3fecc7d6fa898b5dd24b6731c4 |
| independent/old-allocation-closure-independent-review-v1.json | 92a59c58b3736994e1f3473070f682ad4d501bf3573d5b5708999065ebd04814 |
| stage-recovery-metadata-v1.py | a5df40df388edfbe68efdabf4ec7a36cd16e431eabd28b8cbac3ea50d24e93d8 |
| archive-recovery-result-metadata-v1.py | dc52eea113dfc452d1beed4f66a1eef2cbfeb05fc72f3deab40d9695a7268da6 |
| freeze-metadata-job-v1.py | 8a814c3214f7211f69c1bc3bc0cef68e051504fa224d7cf47f727727f577c54e |
| metadata-freeze-attempt1-STOP.json | 5bd27c549a09d43f2a8c9f93909faf2aaae6ec36f835340c8aebe66996bb1612 |
| metadata-freeze-finite-remedy-registration-v1.json | 51e263cd29e61bc46fb00d10202effe1568384c6bd3c037096353c1672a37b40 |
| freeze-metadata-job-v2.py | 5aaf96cc06c78fc0f6f1cfdff04171d8bd13b4bf3811c0af575f04e5bdbf89d0 |
| independent/freezer-v2-final-delta-review-v1.json | 5ed805e36144ba52287ee53ac185e7142adfa2a54d9d524f09a569cd29b4f89c |
| recovery-metadata-stage-job-v1.json | 988388eca651e94e2ef0bd807961660d6c925d4fa5e4e8a47d9eb08be3f978e4 |
| independent/frozen-metadata-job-independent-review-v1.json | ba2ba4090b31a021f218a17a0b30c7955507771be2173abae285da5242025dbb |
| recovery-result-metadata-inventory-v1.json | a9a3f0e38fade80a97623c336d94802445e723c778adaeae6c2947919771ab50 |
| independent/real-stage-independent-review-v1.json | df90b2931188dcef3ce6923391242319c7421a5fa6dbd0780aa1905c99518191 |
| independent/complete-paired-snapshot-independent-acceptance-v1.json | 3c94043f9d2d92c1714ac08641a6c74f19b0e6ee796a9b1529d122bbbaab8846 |
| independent/paired-snapshot-outside-anchor-draft-v1.json | cf3bc854fe55abe7f60a1755326558ce5e6d7f008e1774a10aabc1f0339a862f |
| ci-recovery-metadata-integrity-anchor-v1.json | 986216a6072fb36e078ddaba87e1746a27654427e6f06a59fca7a53b9848e72a |
| preservation-isolated-check-1793173933573542000.json | 418686068a0d8dfd0d29ca57a790400a615f0c02caca6ab34ca3c8aa88fd3e74 |
| optional-old-v1-seal-check-attempt1-STOP.json | 9ae823af728aaab61926680647673f2d2ffebd0d67d6607106feb37cb0bb43ac |
| independent/retention-tools-final-code-review-v1.json | d242e42d654edfb1a27d678fbfb4389ce83cf1e3d34fa7757891d58be4394554 |
| independent/retention-public-chain-v6-result.json | a5bd52412bad7729bd2196e7ec25f7156d944eb0d57d25a446abf1ec23269b92 |
| independent/new-source-and-fixed-P17-feasibility-v1.json | 392b604896dafc507fd404a00b168c411156af596bc1c74b2f9457a63e85b18b |
| spec/old-accounting-spec-audit-v1.json | 6c4f4b997b5e1a1a0e41bc531d98c230907d97835ca756c712ea961752bceef7 |
| spec/native-call-accounting-interpretation-v1.json | 6e42d37d46498be0a55b8d2bdcd0f0a42eb54f1cc92c6eb965e1e2168fcd3e19 |

Generated logs, packets, archive inventories, full replay results and trusted
caller-observed command returns remain external. New final endpoints are
recorded only after actual observation; this report never invents its writer's
future tool return.
