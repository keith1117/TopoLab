# B2.3 bounded data-feasibility repair protocol

Status: fixed diagnostic boundary before any extended B2.3 solve. This
document will receive exactly one candidate amendment, committed before
corrected sentinel execution. B2.2's failed 61-case result remains historical.

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
