# B2.17 frozen online early-reliability probe

Status: frozen before any B2.17 online diagnostic or new case outcome. Plan
version `topolab.b2_17.early_reliability.v1` has canonical SHA-256
`51c3ffd501435802298256acac05af28b95542408208989d68ea36df698d3d7e`.
This is one bounded development experiment over the unchanged B2.9 vector-29
and B2.12 context-17/43 checkpoints. It does not open final evidence or B3.

## Signal, action, and complete query charge

Only for the large `(24,12,6)` mesh, y point load, and volume at least 0.55,
evaluate a fresh uniform shadow through exactly two SIMP updates and run the
context-17 learned start in the **same continuous** 360-update solver through
update two. The observable scalar is learned post-update-two compliance divided
by uniform post-update-two compliance. Reject the learned attempt if this ratio
is strictly greater than `1.001` or nonfinite. On rejection, stop the learned
solve immediately and run a fresh full uniform fallback. On acceptance,
continue the existing solver trajectory and apply unchanged independent final
quality checks; any failure pays a full fresh uniform fallback. The two-update
uniform shadow, inference, projection, partial learned solve, decision, and
fallback all count in end-to-end time. A rejected attempt's entire time before
the uniform run must be **strictly below 2.8101 s** per at-risk query, the
B2.16 optimistic budget. The same predecision cost cap applies to accepted
at-risk queries. No intermediate state or matched final uniform compliance is
available to this decision beyond the paid shadow. Other cases use the
unchanged B2.15 route, with a fresh charged solve.

This rule has no fitted threshold. It uses the unchanged `1.001` compliance
factor as a conservative early comparison. There is no guarantee that the
early ratio predicts terminal quality; that is the purpose of the test.

## Ordered stopping gates

First hash-audit the exposed B2.14/B2.15 reference and screen indices using
the B2.16 audit and verify the fixed checkpoint selections. Run the online
probe on exactly four previously exposed high-volume large-y cases: B2.14's
two cases at volume `0.5925` and B2.15's two at `0.5825`. The old, fully
charged context-17 outcome supplies the known terminal success/failure label;
the online run does not use that label to decide. The sentinel passes only
if it accepts the one known successful attempt, rejects all three known
failed attempts, stays under the strict `2.8101 s` predecision cap on each
case, completes within 600 s, and peaks below 2 GiB. Count a rejected known
success as a false rejection, and an accepted known failure as a missed
failure. Retain all four results. **If this sentinel fails, stop B2.17
without running a new case**; no fresh development feasibility result exists.

Only after the sentinel passes, create fresh cases crossing volumes
`0.3225, 0.4725, 0.5775`, free-end small-mesh load positions `(y=1,z=2)`
and `(y=5,z=1)` (physically doubled on the large mesh), y/z unit negative
loads, and `(12,6,3)`/`(24,12,6)` meshes: 24 physical cases, two per
scale/direction/volume cell. Their IDs and volumes are absent from the
636-case prior development ledger and design-exposed M3 v1 final volumes.
Run all 24 new uniform references before model loading or the learned screen.
Require 24/24 convergence, finite positive compliance, independent final
quality, and physical-volume error at most `0.005`, within 3,600 s and 2 GiB.
On failure, retain outcomes and stop.

The fresh screen runs 216 ordered outcomes: fresh timed uniform, physics
heuristic, train-only nearest neighbor, fixed vector 29, fixed context 17,
fixed context 43, unchanged B2.13 route, unchanged B2.15 route, and this
probe route. Persist each complete case. Run one CPU/BLAS thread from the
same clean source revision as the read-only plan and sentinel. Screen cap:
12,000 s and 2 GiB. The screen passes only with all cases and outcomes,
zero accepted quality violations, no false rejection or missed failure on
the two at-risk cases relative to independently measured context 17,
strict diagnostic cost cap on both, at most two failed learned attempts,
paired mean ratio at most `0.90` on each scale and at most `1.0` on all
four scale/direction cells, overall ratio strictly below `0.95` times
**both** unchanged routed policies, and overall ratio below both non-ML
comparators. All rejected and failed attempts retain full cost.

An independent audit must recompute identities, quality, phases, signals,
false/missed classification, costs, and Gate from persisted artifacts.
Generated records, logs, plans, model weights, and datasets stay outside
Git. A fresh-screen pass is development feasibility only; it requires a
separate larger confirmation before B3 and cannot support an acceleration
claim. A sentinel or screen failure retires further local changes to the
current fixed-checkpoint reliability/routing family. The next slice must
assess a genuinely different, finite method mechanism.
