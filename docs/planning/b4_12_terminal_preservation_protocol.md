# B4.12 bounded candidate terminal-witness preservation probe

Prepared: 2026-10-04 (America/New_York). Freeze and merge after CI before
production outcome/model/label access or solver calls.

Identity: `topolab.b4_12.terminal-preservation-probe.v1`.
Metadata plan SHA-256:
`48171ac3beebf5abb19f59585bb6c387d4b72469e73a9fcaf749930b56bbae00`.
Policy: `topolab.b4_12.candidate-terminal-preservation.v1`.

## Single intervention and own-state choice

Keep fixed P/17, all twelve C/P/S/W checkpoints, the complete 528-label
train-only nearest neighbor, projected starts, specialist route, original
physical-plateau solver, quality limits and 360-update cap unchanged. There
are no fits, seed replacements, threshold/length searches or final reads.
B4.2, B4.6, B4.8 and B4.10 remain failed; uniform stays operational default.

Reuse B4.10's exact qualifying P-generalist rule: `(24,12,6)`, y, volume
below 0.55, originally converged physical plateau and design change >0.01.
Run its unchanged input terminal re-solve and exactly twenty OC/FEM updates,
without intermediate stopping. The policy receives no matched reference.
Then choose between exactly two candidate witnesses:

1. An unqualified start or incomplete continuation returns the endpoint;
   an incomplete continuation remains nonconverged and pays ordinary fallback.
2. A completed endpoint with its own unchanged convergence certificate returns
   that endpoint. No reference-quality comparison can select an earlier state.
3. Only after all twenty updates, when the endpoint loses its own convergence
   certificate, return the original converged candidate witness. Require its
   finite density/compliance, density bounds, original plateau certificate
   and physical volume error <=0.005. Reject inconsistent endpoint flags.

The own certificate remains design change <=0.01, or eleven states with
maximum ten-update physical change <=0.01 and relative compliance gain in
`[0,0.0002]`. The later ordinary independent quality decision still requires
convergence, volume <=0.005 and compliance <=1.001 times matched uniform.
A preserved witness that misses reference quality still fails and pays fresh
uniform fallback. The rule does not compare candidate compliance to reference
or search intermediate states. Original and endpoint states are immutable;
store both plus selected identity, first-stop iteration and performed updates.
Selected iterations may be fewer than performed iterations: report both and
charge the full re-solve, twenty updates, choice, witness construction/I/O,
callback, quality decision and any fallback. Retain outer wall/CPU envelopes,
inclusive callbacks and the conservative one-second recording allowance.

## Inputs and regression sentinel

Before any model/label bytes, verify all fourteen B4.10 bindings and six
B4.11 bindings in `b4_terminal_preservation.py`, then the unchanged B4.10,
B4.8/B4.7/B4.6/B4.5 guards. Bind original closed journals and canonical
metadata; source labels/checkpoints remain unchanged. NN opens/audits all
528 train labels only through its complete-population guard.

Use the exact nine B4.10 sentinel cases and 108 twelve-method outcomes:
uniform, heuristic, NN, C/P/W seeds 17/29/43, with the unchanged specialist.
Sorted case IDs, uniform first and the existing B4.10 SHA-derived rotation
salt preserve query order. P/17 remains primary before all execution.
The sentinel contains the four historical large-y P failures, the newly
nonconverged P/17 case `033f380c…`, two small-z P/29 negative controls,
accepted low-volume generalist, specialist, z and small-grid controls.

Re-execute uniform references and every query. Compare prepolish witnesses
against immutable B4.8 and every retained endpoint against B4.10's hash-chained
outcome population. Independently FEM/filter-audit both witnesses and selected
outcomes; separately recompute raw-JSON certificates, choice, classifications,
full costs, journal/recording identities and Gate arithmetic without importing
the new numerical/choice helper. Retain all failed endpoint certificates even
when an earlier own witness is chosen. Controls retain numerical/status/NN
identity; both small-z failures stay failed. Never substitute historical times.

The sentinel passes only when all four known P failures are repaired, every
originally accepted P remains accepted, P/17 has zero failures/fallbacks,
and its mean paired charged ratio and ratio of charged sums on all four
large-y generalist cases are each <=1.0. Require complete numerical,
policy, independent and resource integrity. Any failure stops the slice;
no repeat, changed length/seed/threshold or post hoc sentinel subset is allowed.

## Conditional independent development panel

Only after the complete independently audited sentinel and whole-command
resource floors pass, open **48 new** cases: both fixed meshes, y/z,
volumes `(0.3379,0.4729,0.5439,0.6039)`, positions `(1,1),(3,1),(5,2)`
in small-grid y/z indices, doubled on the large mesh. Metadata-only planning
checks budget-insensitive physical fingerprints against the complete historical
ledger, B3 catalog and B4.5/B4.6/B4.7/B4.8 cohorts. Also exclude all 48
unexecuted B4.10 fresh definitions: that older panel stays sealed in this slice.
No B4.12 new reference/query is opened before the sentinel admission rule.

Retain 48 references and all 576 twelve-method outcomes. Require the unchanged
development criteria for at least two P seeds: both scale means <=0.90,
four direction means <=1.0, failures <=min(2, matched C, matched W), no worse
non-specialist-y failures, and overall mean below both non-ML comparators.
Each pooled middle/high-volume large-y cell requires >=6/9 successes.
Fixed P/17 additionally requires zero failures/fallbacks, the existing
primary comparison criteria and scale charged-sum ratios <=0.90. No primary
reselection follows. A passing repair still requires separate independent
larger confirmation and a compatible final contract before B5.

## Execution and finite resources

The CLI defaults to metadata-only planning with no output. Explicit `--execute`
requires clean CI-passed merged source, the locked CPU environment, one BLAS/
OpenMP thread and the separate external sibling `b4-12-terminal-preservation`.
Use existing charged single-writer/hash-chain recovery and immutable publication;
retain every attempted/failed process and profile. Generated artifacts stay
outside Git. All previous receipts, indices, charges and failures stay intact.

Per cohort caps: references 3,600 seconds; queries 21,600 seconds;
numerical/input audit 3,600 seconds; policy/two-witness audit 3,600 seconds;
independent JSON audit 1,800 seconds. Each uses at most 2 GiB. Whole-slice
cap: **43,200 charged seconds / 2 GiB**. Whole-command startup/exit work and
ten-second allowances are charged; reference/query attempts also retain their
one-second recording allowance. Admission reserves the maximum fresh stage
budgets plus independent audit and full 180-second closure cap, after closing
all sentinel whole-command floors. Stop if these cannot fit the whole cap.

Closure reserves its **entire 180 seconds**, since its own native profile is
available only after exit. Afterwards verify whole-command wall +10 and
internal elapsed +10 fit this reservation and native RSS fits the retained
peak; do not rewrite a closed ledger. Use permitted native `/usr/bin/time -l`
profiling to retain complete wall/kernel-RSS records. Any violated profile,
cap or reservation invalidates acceptance.

Publish source/plan/protocol/input hashes, all counts, chosen and performed
iterations, full charges, failed endpoints/fallbacks, independent agreement,
local required checks and exact-final-head CI-before-merge receipts.
If the sentinel or fresh Gate fails, **B4.13** is a bounded read-only
preservation failure/cost review. If both pass, **B4.13** is a separately
frozen larger fixed-policy independent confirmation. Stop after reporting
that next slice. No outcome here establishes final acceleration.
