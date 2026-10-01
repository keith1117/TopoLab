# B4.4 complete timing and bounded checkpoint engineering

Date: 2026-10-01 (America/New_York)

Status: **implementation and preregistration; numerical sentinel pending**.
Gate B4 remains failed and B5 remains sealed.

The [finite protocol](../planning/b4_4_engineering_protocol.md) freezes six
already exposed cases, four unchanged selected artifacts, 76 counterbalanced
queries, complete numerical/status identity, independent terminal audits,
callback and full-wall bounds, and 7,200-second / 2-GiB resource limits.
No label, nearest-neighbor population, new fit or final artifact is opened.

The new query envelope retains complete wall and process CPU alongside legacy
phase sums and inclusive callback/flush channels. The separate progress contract
has a 4-KiB bound. Single-writer ownership, immutable canonical chained units,
durable pending attempts, directory fsync and charged UTC recovery preserve
completed outcomes and failed attempts. The cadence starts after each write.
Full results are published only at query boundaries; callbacks touch no ledger.
The existing failed B4.2 runner, files and scientific decision are unchanged.

Thirteen focused tests pass, including an actual child process exit before
completion, recovery after publication but before progress acknowledgement,
retained attempt counts and downtime, permanent cap/integrity flags, ownership,
corrupt/missing prefixes, symlink and changed population rejection, byte bounds
with 48 large completed records, post-write cadence and unphased query timing.
Before the implementation commit, locked dependency synchronization, Ruff,
mypy (55 source files), all 659 tests (483.66 seconds) and `git diff --check`
passed. Execution
will use the clean merged implementation revision; this report will then retain
all engineering results and a separately charged independent audit.

The first implementation PR's push checks passed; its PR quality run exposed
an existing wall-clock-dependent SQLite heartbeat test (658 passed, one failed).
That test used a 300-ms lease and a blind 700-ms sleep, allowing CI scheduler
starvation to produce false recovery. It now advances a controlled clock by
200 ms only after observing each actual successful persisted renewal, crossing
the original lease in four steps before opening the observer. Production lease
and heartbeat code, numerical tolerances and the sentinel protocol are unchanged.
The failed CI run is retained; locked sync, Ruff, mypy (55 source files),
all 659 tests (429.34 seconds) and `git diff --check` passed again before
committing the deterministic test fix.

If engineering acceptance passes, the next slice is **B4.5**, a separately
frozen sensitivity-weighted terminal-design generalist intervention and fresh
validation. No acceleration claim or B5 access follows from this engineering
sentinel alone.
