# B2.3 bounded data-feasibility repair protocol

Status: fixed diagnostic boundary before the extended B2.3 solve; the one
candidate amendment below is fixed before corrected sentinel execution.
B2.2's failed 61-case result remains historical.

## Fixed boundary and read-only diagnosis

Use the same 61 B2.2 development sentinel source problems, strata, splits,
loads, supports, mesh sizes, material, filter, and 120-update outcome ledger.
The 53 accepted and eight failed results are documented in
`docs/validation/b2_2_data_feasibility.md`. The eight failures are exactly
the seven IDs in `HISTORICAL_FAILED_TRAIN` in the B2.2 runner and the large
`z/0.20` ID
`tlcase-v1-58e145330eb9318f46e047e638b5387aa558d944c370d5ea707e3e6d3d2ba328`.
Do not remove or substitute a case. Read only the committed M2 case/split
metadata; test/OOD labels and outcomes remain sealed.

First reproduce each failure's first 120 uniform-start updates under the
unchanged `topolab.simp.physical_plateau.v1` policy. Continue the same
in-memory trajectory to at most **240** updates, explicitly diagnostic only.
Record the first stop iteration (if any), design and physical changes,
ten-update compliance improvement, final compliance/volume, wall time, and
memory. The cap is a diagnostic ceiling, not an accepted label budget. No
density array or generated label is stored or committed. If an extension
raises an exception, preserve it as a failed diagnostic.

After inspecting all eight trajectories, commit **one** explicit candidate
intervention here before implementing or executing it on the full 61-case
sentinel. The candidate must state its mathematical stop or iteration-cap
semantics, reason grounded in the diagnosis, new case/result/label identity,
budget, and full numerical acceptance rule. Do not tune successive limits
against individual sentinel outcomes. Keep the `topolab.simp.v1` default,
B2.1 policy, B2.2 cases/results, and historical M1/M2 evidence intact.

## Candidate acceptance boundary fixed now

Under the future single candidate, rerun **all 61** source cases once from
projected uniform starts. If the intervention changes an optimization field
included in `ExperimentCase.case_id`, reconstruct each case and give every
new physical case/result an explicit versioned mapping to its B2.2 source.
Require 61/61 within the newly committed cap and stop rule, finite positive
final compliance independently re-solved within relative `1e-9`, filtered
physical-volume error `<= 0.005`, consistent final-state history, and no
solver exception. For the 53 previously accepted sources, require the same
stop iteration and final compliance within relative `1e-10`; a budget-only
extension should leave early stops unchanged. Keep failures in the
denominator. Record wall time, peak RSS, and each reason for stopping.

The complete corrected sentinel has an upper execution budget of **1,500 s
wall** and **1 GiB peak RSS** on the same single-thread local machine. A
budget overrun fails the gate. A passing 61-case sentinel only permits a
later independent 522-case materialization/data gate; it does not establish
that all 522 labels will succeed or that learned acceleration is achieved.
Every later uniform, learned, and non-ML comparison must use the same
selected policy and cap. Final B3 evidence remains sealed.

## Read-only trajectory result and one candidate

The committed eight-case diagnostic reproduced each B2.2 state at update 120
exactly, including compliance, design maximum, and ten-step physical change.
Its metadata-only JSON remains outside Git at
`/tmp/topolab-b23-diagnosis.json` (SHA-256
`33e709d68aea3754f0789bf0d1eb9e6e18a4086f9435eb5dfc0b930e3348cbb2`).
All eight trajectories eventually met an
**unchanged** stop rule within the previously fixed diagnostic ceiling: the
seven small `y/0.45` cases at update **125** and the one large `z/0.20` case
at update **170**. The large case's terminal maximum design change was
`0.009727`, below the unchanged `0.01` design criterion. The seven small
cases stopped by the unchanged ten-step physical plateau criterion, with
terminal ten-step compliance improvements between `0.0001828` and
`0.0001899`, below the unchanged `0.0002` bound. No divergent or oscillating
terminal trajectory was observed in this bounded extension.

Test exactly one budget intervention: set `max_iterations = 240` on each of
the **same 61 source problems**, and retain
`topolab.simp.physical_plateau.v1` unchanged. The value 240 was committed as
the diagnostic ceiling before observing the extended results; it is reused
as a finite budget rather than tuning a new threshold to 125 or 170. This
changes neither OC, filtering, stiffness, nor any stopping tolerance. It
also does not claim the old 120-update result passed.

Because `max_iterations` is part of `ExperimentCase.case_id`, derive a new
`ExperimentCase` for each source, retaining the original ID as
`b2_2_source_case_id`. The new plan version is
`topolab.b2_3.budget240.plan.v1`, and prospective labels have version
`topolab.b2_3.label.v1`. A result ID with prefix `tlcase-b23-v1-` is the
SHA-256 of canonical JSON containing the old source ID, the new physical
case ID, `topolab.simp.physical_plateau.v1`, and the B2.3 label version.
The source-to-new-case mapping is frozen by a content-derived plan hash
`45baa0f74c74fca3ea3d7594b7576f1150a6dc950b23daafdab5acc8e1f5c289`
before the 61-case execution. Old B2.2 and M2 labels are incompatible.

The 53 previously accepted cases should stop at exactly their old iteration
because each stopped before 120; require their final compliance to agree
within relative `1e-10` as declared above. The eight former failures must
pass the same independent quality audit within 240. Compare only
version-matched uniform, learned, and non-ML methods in later slices. The
future 522-case plan and two-hour generation budget require a separate
read-only plan and review; this 61-case result cannot guarantee them.
