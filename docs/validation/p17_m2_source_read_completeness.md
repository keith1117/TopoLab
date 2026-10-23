# Bounded source-read completeness and failure reasons

Date:2026-10-23 (America/New_York). Baseline: main
`f7e76371f27c0426518f6f0ab51f2dafba580251` (PR216).
**SOFTWARE REPAIR ONLY; SOURCE ADMISSION REMAINS CLOSED.**

## Selected behavior and minimal repair

The owner selected the third code-diagnosis finding, following the two recording
repairs in [PR216's report](p17_m2_source_failure_context_retention.md). At the
public `Reader.read` and `OnceReader.read` boundaries, the producer could accept
an early EOF when optional expected size/hash were absent. The independent
reader rejected it under a combined length/tuple predicate whose reason said
the source identity changed, even when every observed tuple was identical.

Both independently implemented readers now require total returned bytes equal
to the descriptor's pre-read size after checking exact before/after tuple equality.
The new stage is `read_size_consistency`, with reason
`source read length differs from descriptor size`. This equality also rejects
an inconsistent excess length; it does not permit extra bytes or retries.
Actual tuple changes still STOP first at `after_read_identity`, keeping each
reader's original identity reason and exact changed fields. If short length and
tuple mutation coexist, the observed mutation remains the primary failure and
returned bytes remain recorded. Neither condition is accepted or retried.

Only the producer's missing equality is added and the independent combined
predicate is split. No shared reader abstraction, new stat/content read, hashing
fallback, source reopen or dispatcher/controller/CLI change is introduced.
Both preserve the existing failure journal and available declared/before/after
tuples; closing observations stay unavailable when rejected before that stage.
Valid complete reads still perform the existing closing-path check. A short
individual OS chunk is allowed when the accumulated stream is complete.

## Test-first evidence

`tdd` and `karpathy-guidelines` guide the change. Tests use the selected public
reader boundaries and newly created local three-byte files. Only OS IO boundaries
and the new file's metadata are fault-injected; no reader collaborator is mocked.
No guarded formal CLI is invoked.

The first eight regressions were RED on unchanged main: empty and one-byte early
EOF, both readers, with/without STABLE closing checks. Producer failed to STOP;
independent STOP had the wrong reason. The minimal repair made all eight GREEN.
Each verifies the distinct stage/reason, equal known tuples, actual returned
length, durable STOP journal and refusal to reopen the same literal source.

Ten additional controls cover actual1ns mtime mutation with0/1/3 returned bytes
in both readers, and successful complete size/hash-checked reads in both modes.
The independent success cases use one-byte OS chunks through its actual read
loop. Mutation controls preserve identity-first STOP with the exact changed
field, including simultaneous short reads. All18 new cases pass.

The five focused modules pass **341 tests**. All five required precommit checks
pass: locked `uv sync --dev --locked`, `uv run ruff check .`, `uv run mypy src`,
complete CPU-bounded `uv run pytest` and `git diff --check`. Full pytest: **2475
passed/1 unchanged Linux-only platform skip in706.69s** (2476 collected). The
complete test invocation used710.0171435000375s. No tolerance or test-population
change; no failed or interrupted full-suite attempt in this slice.
Publication is pending at authoring; exact PR and merged-main CI must pass before
claiming publication complete. Original frozen protocols/reports, dependency lock,
CI, runtime controller and all other source retain their baseline bytes.

Raw red/green/full-suite logs, source-diff and preservation receipts remain
external at `/Users/keith1117/Documents/TopoLab-data/software-source-read-completeness-2026-10-23-6hiakzyy`.
Existing13 original-checkout changes and10 managed-worktree draft files are
backed up and excluded from this PR; published additions are integrated without
discarding draft text. Unmeasured total software/CI wall, fees and peak remain
UNKNOWN_NOT_ZERO, without transfer from any closed operational grant.

## Limits and handoff

No historical input stat/read, formal role, provider action, old retry/reset or
quota reuse. Ordinary software tests retain their existing numerical fixtures;
they are not formal experiment reruns or scientific acceptance. STOP, exact
tuples, nofollow/one-read, source count/byte caps, source-field/hash validation,
windows, FULL and billing remain. This strengthens producer completeness and
changes independent failure classification without widening acceptance.

The old R/v3 producer STOP used a pure tuple comparison before independent R0;
the independent misclassification cannot explain that historical STOP. Its exact
changed member/cause stays UNKNOWN. All three selected reader findings now have
software repairs, without P/17 repair, source admission or scientific Gate progress.
Keep uniform/science pause/4GiB/independent preflight and all old failures, costs,
UNKNOWNs, seals and closed allowances. Complete normal software publication then
STOP; source admission needs a separate decision and no successor starts here.
