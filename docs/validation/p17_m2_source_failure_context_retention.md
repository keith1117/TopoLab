# Source failure-context retention

Date:2026-10-22 (America/New_York). Software baseline: main
`deca9ab11942ce55213356800faad3c671ead3c2`.
**SOFTWARE REPAIR ONLY; NO SOURCE OR SCIENTIFIC ACCEPTANCE.**

## Owner-selected scope

Fix two confirmed recording gaps, test first: preserve source context on
parse/validation rejection, and retain available tuples/secondary errors in
producer `failure.json`. The optional third short-read consistency finding is
deferred. These recording fixes need no STOP, time-window or billing relaxation.
No historical contract, result or resource ledger is edited. Existing local
control/diagnosis drafts and the original checkout's uncommitted files are
backed up and excluded from this change.

The `tdd` and `karpathy-guidelines` skills guide the work. Tests observe the
selected R0 registration, R1 transcription/comparison and terminal failure-file
boundaries with newly authored local files. Filesystem fault injection controls
only new-file metadata and journal writes. No formal CLI guard is disabled.

## Change and evidence

Both readers keep facts by literal source path from the original single bounded
read. Parse, canonical JSON and source-field validation use those same facts,
with explicit `json_parse`, `canonical_json` or `source_validation` stages. A
rejection retains path, attempt ordinal, available declared/before/after/closing
`(dev,inode,size,mtime_ns)` values, returned bytes, computed byte/hash reference,
changed fields and the original exception type/reason. Missing observations stay
null; the implementation does not stat or reread a source to reconstruct them.

A shared per-reader recording routine preserves the existing primary failure and
adds a secondary journal OSError without replacing it. Both implementations stay
separate; neither imports the other. Registration records the source actually
being validated, including an earlier bootstrap source after later reads.
R0 progress/unit/summary/selection and R1 checkpoint/label/scalar checks use the
same original read context. Overall registry/output cross-comparisons retain
their existing decisions; they are not relabeled as a particular source mutation.

Producer `failure.json` adds `old_read_table`, `source_failures` and
`source_identities`, retaining completed prefixes and any `recording_error`.
The original status/type/reason/count/path fields remain. The admitted stage body
is callable as `execute_stage` for new-file integration tests; `main` still
performs every original identity/root/contract/argv/controller check before
creating the reader and calling it. Tests exercise the real stage body and file
serializer, rather than extracting the exception-handler AST.

Test-first evidence in `tests/test_p17_m2_source_failure_context.py`:

| Boundary | Regression |
|---|---|
| Actual producer/independent R0 | Syntax, duplicate keys and noncanonical JSON retain complete failure facts; still reject reread |
| R0 bootstrap schema | A missing field after another read names the original earlier source |
| R0 ledgers and registered fields | Progress/unit, producer summary and model-selection failures retain their source facts |
| Actual producer/independent R1 | Invalid checkpoint, non-exact float32 label and inconsistent scalar remain STOP with complete source evidence |
| Actual producer stage/terminal file | A real1ns mtime change retains successful prefix and exact changed field, both with a writable journal and an injected secondary append error |

Each affected behavior was observed RED before its corresponding implementation:
6 parse,2 bootstrap-schema,6 R1,2 terminal-file,4 ledger and3 registered-field
cases. Extending parse facts with computed byte/hash references was separately
RED before the additive field. Initial R1 fixture construction errors (duplicate
output names, an omitted source-revision field and unsupported1-cell scale) were
corrected before treating their results as behavioral regression evidence.
The successful R1 fixtures use the existing allowed12x6x3 scale. No production
limit or fixture guard was relaxed to accommodate them.

## Verification

The four focused modules passed323 tests, including23 new regressions.
Final five required checks passed: `uv sync --dev --locked`, `uv run ruff check .`,
`uv run mypy src`, the complete CPU-bounded `uv run pytest` and `git diff --check`.
Complete pytest: **2457 passed/1 unchanged Linux-only platform skip in697.33s**.
No tolerance or selected test population changed. Ruff and
mypy passed after correcting indentation-related line lengths/import order.
The first sandboxed uv lint/type invocations failed to open the existing uv
cache; the normal-permission invocations passed. These failed attempts remain
software work, not a formal outcome or zero-cost claim.

A first complete-suite attempt was stopped after311 passes when final review
found an additional selection-reference recording path; its full log and
interruption are retained. It is not a full PASS. Final source gets a new complete
run. AST checks confirm both IO implementations (after removing the additive
fact storage), all parsers/field validators, producer CLI guard prefix and
independent main retain their original executable predicates. Controller,
dispatcher, dependency lock and CI workflow remain byte-identical. All10 managed
uncommitted draft files and13 original-checkout modified/untracked files plus
both original HEADs remain unchanged.

Publication was pending when this report was authored. PR and merged-main checks
must be observed successful before reporting software publication complete;
there is no assumption of future CI success.
Raw logs and preservation receipts are external at
`/Users/keith1117/Documents/TopoLab-data/software-source-failure-context-2026-10-22-7tk63bxg`,
with the original temporary working records also retained.
Unmeasured total software/CI wall, fees and peak remain UNKNOWN_NOT_ZERO;
there is no new provider purchase or transfer from any closed operational grant.

## Limits and handoff

No old source stat/read, formal role, provider/UI action, production FEM/fitting
experiment, sealed access, retry/reset or quota reuse occurs. The mandatory
software suite still executes its existing new numerical/training fixtures;
those tests are not scientific role reruns or new experiment acceptance. No canonical/IEEE/identity, source
count/byte cap, nofollow/one-read, STOP/window/FULL/charge or acceptance predicate
is intentionally weakened. Frozen historical protocols/reports retain bytes;
new source still needs a separately admitted future identity before formal use.
If every output sink fails, durable evidence is not guaranteed and failure must
remain failure; the repair does not claim an impossible successful persistence.

Old12th-read changed member/cause/returned bytes remain UNKNOWN. This cannot
attribute that historical failure to project logic or cloud sync, pass source
admission, repair fixed P/17 or advance a scientific Gate. Full v2 remains open,
uniform default/science pause/4GiB/independent preflight and all old costs,
failures, quotas and seals remain. Close this software slice and STOP. Next is
the separate short-read consistency repair, subject to its own selected scope.
Source admission remains a separate unresolved decision; neither a formal role
nor another repair is automatically started.
