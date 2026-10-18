# M2 native H/17 stage A: public software implementation

Identity: `topolab.v2.p17-m2-native-homotopy.stage-a.v1`. Date: 2026-10-18.
Basis: [revised proposal](p17_m2_native_homotopy_proposal.md) and its
[structured companion](p17_m2_native_homotopy_proposal.json). The owner's later
instruction grants A only: implementation <=6 hours and separately authored
independent review <=4 hours, followed by required regression and normal GitHub
publication. This supersedes the drafts' earlier implementation-not-authorized
snapshot, without granting B or C. No formal quota is allocated or consumed.

## Scope and acceptance before implementation

Use the assigned ec0b worktree, existing M2 CPU runtime and existing GitHub CI.
Read only versioned source/documents and newly authored public fixtures/weights.
No old inputs, export preparation, old evidence pointers, scientific preflight,
scientific panel, installation, VM, training or changed backend. Public tests
may run small original FEM fixtures and mock large-shape dispatch; these are
software tests, never historical P/17 results or B resource admission.

Add the four proposed source units and corresponding public tests. Preserve
historical bound source/contract/report bytes. Keep uniform as the default.
Reuse original CPU prediction, legacy projection, filter, FEM and OC primitives.
H generalist dispatch is exactly large mesh (24,12,6), y load, volume<0.55;
all other H queries follow same-runtime plain P/S. Prefix updates are 8 at p=1
and 8 at p=2, with reanalysis at both transitions; no prefix early stop. All
updates count against 360. Only p=3 updates can certify design change<=0.01 or
the original eleven-post-update-state physical plateau (gain in [0,0.0002]).
No reflection/polish/witness rescue belongs to H. Matching P-keep retains its
original twenty-update/own-certificate policy. W maps explicitly to W weights
and the same S specialist; C and plain-P remain distinct controls.

The public-only CLI must reject B/C/formal modes and arbitrary input roots before
opening payloads. Its small fixtures and deterministic newly authored model
weights have public identities, separate from any scientific model. No command
discovers old labels, checkpoints, indices or references. A manifest reader is
bounded, explicit and hash-checked; future scientific schemas/views and exact
files remain unregistered and denied. Do not claim the future 528-label export
and formal call/fee tables are closed by this work.

## New numerical witness interface

Candidate `src/topolab/p17_m2_homotopy.py` emits JSON-compatible witness schema
`topolab.v2.m2-homotopy-witness.v1`, consumed independently without importing the
candidate module by `scripts/p17_m2_independent_audit.py`:

- `active`: whether this invocation used the fixed homotopy (low-level public
  small-mesh unit fixtures may exercise the driver directly; production dispatch
  itself never changes its activation domain).
- `initial`: state before update 1, penalty 1 if active, otherwise 3.
- `prefix`: exactly sixteen update states if active, otherwise empty.
- `transitions`: states reanalyzed at p=2 after update8 and p=3 after update16;
  no OC update is attributed to a transition.
- `trace`: all update scalar points, in global iteration order. Each contains
  `iteration`, `phase_iteration`, `penalty`, `compliance`, `volume_fraction`,
  `density_change`, `physical_change`. A density state adds `design_density` and
  `physical_density` to these fields. Initial/transition states use zero changes
  and phase_iteration=0; transition iteration is the previous global update.
- `recent`: last min(11, number of p3 updates) p3 update density states only.
- `result`: original TopologyResult fields with `history` restricted to recent
  p3 updates, preserving global iteration numbers; terminal p3 compliance and
  displacements/reactions come from a final independent-in-time re-solve.
- `fem_solves`: actual driver analyses, including initial, both transitions,
  every update and final re-solve. Other wrapper/quality/heuristic work is charged
  separately and must never be hidden in this count.

The independent checker authors its own schedule, prefix OC reconstruction,
transition/terminal FEM checks, p3-window logic and quality classification from
the unchanged foundational numerical primitives and the proposal. It must not
use the candidate H driver, its classifier/Gate or resource PASS as its oracle.
Full conversation exposure is disclosed; separate authorship is not blind review.
Corrupt phases/windows/counts/terminal states and false acceptance must reject.

## Empirical resource adaptation

Adapt B4.30 native wall/RSS (Darwin bytes; ps KiB*1024), sampled process group
plus controller, target0.5s/actual intervals, registered-role native peak overlap
composition, watchdog and complete-exit records for the new identity and4GiB.
Keep pending before interpreter/import/input, immutable pre-exit pending records,
append-only exit/binder verification, exact paths/hashes/argv/cwd/runtime/thread
identity and nonzero failure-inclusive charges. Missing mandatory measurements,
unregistered descendants, MemoryError/OOM or cap exhaustion stop the tree. An
ordinary candidate quality failure alone may pay a fresh uniform fallback.

Public software checks cover parser units, short-command native capture, actual
CLI startup/import, bad inputs, timeouts, fatal memory errors, descendants,
post-exit cap failures, atomic/non-overwriting records, charges and final verifier
exit/profile binding. Do not allocate4GiB to test a cap. Linux CI checks software
and parsing only; it cannot admit the M2. No public test result is named
PASS_PREFLIGHT_RSS_EXIT_EMPIRICAL or PASS_RSS_EXIT_EMPIRICAL for B/C.

## Budgets, records and stopping

Implementation accounting starts 2026-10-18 20:57:43 UTC, cap21600 seconds.
Record actual active windows and directed public execution/waits/failures.
Independent author records its own windows, cap14400 seconds; overlapping roles
are separate charges. Full prescribed regression, CI and publication are additional
software costs with actual records and UNKNOWN_NOT_ZERO for unavailable totals.
No purchase, scientific time allocation, old cap transfer or free export labor.
Generated software logs/profiles/weights and budget records live in a new external
stage-A namespace, never the proposed future scientific output root or Git.

STOP on authorization/input boundary, any implementation/review cap, fatal
resource/process failure or unresolved substantive contract conflict. Debugging
public software before freeze is allowed within A; it is not a formal retry.
Complete all five mandatory checks before every commit, inspect publication
guards and all uploaded commits, merge only after all four applicable exact-head
CI jobs pass, verify main/CI and clean only this merged branch. Retain worktree.

Close with a validation report, independent review, current status, one history
entry, concise AGENTS, provenance, numerical convention and synchronized roadmap
entries/indices. Report software capability separately from UNKNOWN actual H/17
quality/speed and B/C admission. Preserve every historical failure/cost/quota/seal,
B3's M2 plus independent Ubuntu24.04/two-scale/final replication requirements.
Then stop. The only next item is the finite missing manifest/domain/role/call/fee
registration and separate owner authority for B; A never starts it automatically.
