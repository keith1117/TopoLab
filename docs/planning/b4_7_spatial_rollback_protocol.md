# B4.7 bounded spatial-objective rollback

Prepared: 2026-10-02 (America/New_York)

Status: frozen before any B4.7 solver call or new outcome.
Identity: `topolab.b4_7.spatial-rollback.v1`. This development repair tests
B4.6's measured non-specialist terminal-quality and refinement regression.
Uniform remains the operational default; the original failed B4.2 and W/17
confirmation remain failed. B5 and all final artifacts stay sealed.
The contract/runner must merge after passed CI before production execution.

## 1. One intervention and immutable inputs

Roll back only the generalist's spatial sensitivity-weighted objective by
using the **unchanged B4.1 P checkpoints** instead of W. **P/17 is fixed
prospectively**, with unchanged same-seed S on large `(24,12,6)`, y loads
at volume >=0.55. Keep all P/17,29,43; C/17,29,43; W/17,29,43; uniform;
physics heuristic; and complete 528-train-label nearest neighbor: twelve
methods. No fitting, checkpoint selection, new label, route threshold,
encoding, model, numerical equation, solver budget or tolerance change.
P/43's worse B4.6 reliability and every historical P failure stay reported.

Before any checkpoint or label bytes, match every B4.6 context, reference/
screen/audit summary and closed progress, independent-audit and resource-close
hash frozen in `UPSTREAM_FILES` in `src/topolab/b4_rollback.py`. Its failed
fixed W/17 decision is the prerequisite for this repair, not a passing Gate.
Also match all eleven B4.5 receipts and its closed three-W-fit chain through
the unchanged B4.6 upstream guard. Keep exact B3 data-index checksum
`b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26`
and B4.1 training-index checksum
`229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7`.
Verify all twelve used checkpoint sources, selections, checksums and finite
float32 tensors. Authorize the full NN population before its first label byte.
No query label supplies an initialization.

Bind the protocol/plan hashes, upstream receipts, actual clean merged source,
numerical anchor, lockfile, Apple M2 CPU runtime, one BLAS/OpenMP/Torch intra-op
thread and eight inter-op threads. Output is the separate external sibling
`b4-7-spatial-rollback`; B3/B4 input roots remain read-only. Default planning
opens no artifact bytes, creates no output and calls no solver.

## 2. Fresh workload and exact completeness

Cross `(12,6,3)` / `(24,12,6)` meshes, y/z loads, volumes
`0.3341,0.4691,0.5401,0.6001`, and small-grid x-max positions
`(1,2),(3,1),(5,2)`; double the large-grid load indices. All other physical
fields are unchanged B3 cantilever settings. Freeze exactly **48** cases,
three per scale/direction/volume cell, 24 per scale, sorted by complete case ID.
Require 48 unique budget-insensitive fingerprints, disjoint from all 1,376
historical fingerprints, all 752 B3 definitions including reserved final
metadata, all 48 B4.5 and all 96 B4.6 cases. Publication makes this complete
cohort design-exposed even if execution stops early.

Independently accept **48/48 mandatory uniform references** before screening.
An invalid reference permanently stops this version; do not replace it or
extend its 360-update cap. Then retain **576/576** queries, fresh uniform
first per case. Rotate the other eleven methods using the first eight hex
digits of SHA256(`topolab.b4_7.order.v1:` + case ID), modulo eleven. No cached
uniform query, favorable subset, failed-query retry or outcome reselection.
Every failed candidate retains its status and pays a fresh uniform fallback.

## 3. Quality, timing, recovery and finite resources

Retain the physical-plateau solver, A3 ordering, filtered-volume projection,
finite convergence, independent stored-state compliance `rtol=1e-9,atol=0`,
physical-volume error <=0.005 and candidate compliance <=1.001 times mandatory
uniform. Timed/fallback uniform agrees with mandatory uniform at `rtol=1e-9`.
A successful fallback never changes the failed candidate classification.

Reuse the B4.5/B4.6 full outer wall/CPU envelope, inclusive callbacks,
five-second compact heartbeat and one-second recording allowance for **every**
method, including uniform. Charge that full allowance durably before numerical
work and add it to actual resource wall; require a matching durable receipt
and measured recording <=1 second. No callback, failure, fallback or recording
time is subtracted. The shared execution loop preserves B4.6's versions,
cohort, receipts, timing and decision under its original wrapper.

| Stage | Maximum charged seconds | Maximum RSS |
|---|---:|---:|
| Mandatory references | 3,600 | 2 GiB |
| All queries | 21,600 | 2 GiB |
| All independent audits and closure | 3,600 | 2 GiB |
| Total | 28,800 (8 hours) | Per-stage caps above |

These are B4.5's unchanged non-fit caps for the same 48-case size, not runtime
promises. Charge startup, guards, model/NN loading, journal scans/fsync,
serialization, reference/query work, independent audits, recovery and closure.
Whole-command `/usr/bin/time -p` floors must be covered by final charges.
Pending interruption may resume only unchanged work with all prior cost and
downtime charged. Terminal, integrity and resource failures are permanent.
Artifacts, profile floors and supplemental audit sources remain outside Git.

## 4. Frozen repair Gate and next slice

Audit all twelve used checkpoints, all 528 NN labels, 48 reference witnesses
and every candidate/fallback witness: **626** production audit units. Require
complete populations, unchanged source/artifact hashes, independently reproduced
terminal classifications, charge arithmetic and resources, zero accepted or
operational quality violations. Supplemental arithmetic must not invoke the
production Gate function.

For at least **two P seeds**, require mean paired charged ratio <=0.90 at each
scale, <=1.0 in all four scale/direction cells, failures <=min(2, matched C
failures, matched W failures), non-specialist y failures no more than both
matched controls, and overall mean below both non-ML comparators. Across all
three P seeds, require >=**6/9** terminal successes at each middle-volume
`0.5401` and high-volume `0.6001` large-y cell. This preserves the previous
two-thirds quality fraction and speed/reliability bounds, with P replacing W
as the preregistered repair candidate and W replacing P as its matched control.

Fixed **P/17** additionally requires zero failures/fallbacks, overall mean
below C/17, and either overall mean below W/17 or fewer failures than W/17.
Its total charged query time / uniform total must be <=0.90 at each scale.
All conditions, two passing seeds and both pooled quality cells are required.
P/29 or P/43 cannot replace a failed P/17. Report every seed and comparator.
A passing screen does not rescue the original B4.2 or B4.6 Gate.

If the full repair Gate passes, **B4.8** separately freezes a larger physically
disjoint development confirmation with the same checkpoints, route and fixed
P/17, before any compatible final contract or B5. If it fails, **B4.8** is a
bounded read-only diagnosis of this complete failed repair, followed by a
separately registered mechanism; no fit or tuning is authorized on this cohort.
Report the actual branch and wait for the next-slice instruction.
