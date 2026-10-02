# B4.6 confirmation contract and implementation boundary

Prepared: 2026-10-02 (America/New_York)

The [prospective protocol](../planning/b4_6_confirmation_protocol.md) freezes
96 new development definitions and 1,152 query assignments, with W/17 fixed
as the primary before any new reference or query outcome. The metadata-only
planning audit found 96 unique physically disjoint cases, balanced six per
scale/direction/volume cell, and all twelve methods for each case. Plan SHA-256:

`2bde23e3da2232bd06a20607e5735d0dec81c3b5a7bc716face878e38b8c1440`

The read-only upstream metadata audit matched all eleven frozen B4.5 receipt
hashes and the complete three-fit chain. No checkpoint tensor, label, final
artifact or new numerical result was read by that planning audit. Default CLI
planning opens no input bytes and creates no output root.

The shared query helper is extracted because B4.5 and B4.6 now have the same
complete timing/publication/receipt responsibility. B4.5 retains its wrappers,
version, cohort, default caps, decision arithmetic and artifact identity.
Confirmation uses the same independent witness audit and query envelope,
with its own version, journal chain, doubled finite caps and fixed-primary Gate.
No solver, tolerance, training, encoding, model or route changes occur.

Twenty targeted tests passed, including the unchanged B4.5 boundaries and
new exposure, upstream-before-bytes, completeness, failed-seed retention,
fixed-primary rejection and total-cost checks. Locked dependency sync, Ruff, mypy (58 source files), all **679 tests**
(436.92 seconds), and `git diff --check` passed before the implementation
commit. Production execution requires
the clean merged implementation and external sibling output, so this report
makes no production or confirmation-Gate claim. B5 remains sealed.
