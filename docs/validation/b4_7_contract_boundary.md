# B4.7 spatial-objective rollback implementation boundary

Prepared: 2026-10-02 (America/New_York)

The [frozen protocol](../planning/b4_7_spatial_rollback_protocol.md) fixes
unchanged P/17 as the repair candidate before any new B4.7 outcome. Its
metadata-only plan contains 48 new cases, 576 assignments and 626 audit units,
with all P/W/C seeds, specialist routing and non-ML comparators retained.
Plan SHA-256:

`7f161aa36d9071bf17beae5e26f93f274e1c3b6ffdaf12f104f57f0f1faf8825`

The plan audit verifies unique physical fingerprints, no historical/B3/B4.5/
B4.6 overlap, three cases per scale/direction/volume cell, complete method
membership, fixed P/17, finite caps and no fitting/final access. The read-only
upstream check matches all nine B4.6 and eleven B4.5 frozen receipt hashes,
including retained failed W/17 confirmation and the closed three-W-fit chain.
No checkpoint tensor, label byte or new numerical outcome enters planning.
Default CLI planning creates no output and invokes no solver.

The existing execution loop now has two callers, B4.6 and B4.7, and is shared
through a narrow immutable specification. The original B4.6 plan hash,
versions, complete timing, one-second recording allowance, witness audits,
recovery and decision remain unchanged. The wrapper also charges preparation
of its case/assignment specification. B4.7 changes candidate/control roles
in the existing Gate arithmetic with W preserved as the historical default;
its additional check fixes P/17 and requires both total scale costs <=0.90.
There is no numerical solver, tolerance, fitting or route change.

All **28 targeted tests** pass, including unchanged B4.5/B4.6 boundaries,
new no-byte planning/exposure checks, changed-upstream-before-model rejection,
failed-seed retention, fixed-primary rejection, strict W-control improvement,
total-cost rejection and a synthetic end-to-end reference/query/receipt/resume
exercise. The synthetic exercise also rejects screening without complete
mandatory references and retains its permanent failed journal.

Production execution requires the clean merged implementation, exact locked
CPU environment and external sibling roots. This implementation report makes
no production or repair-Gate claim. B5 remains sealed, and B4.6's failed Gate
and all historical P failures remain unchanged.

Before the implementation commit, `uv sync --dev --locked`, Ruff, mypy
(60 source files), all **687 tests** (441.46 seconds) and `git diff --check`
passed. The two user-owned untracked duplicate documents remain untouched.
