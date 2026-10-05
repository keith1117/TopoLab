# B4.15 bounded offline compliance-adjoint feasibility protocol

Prepared: 2026-10-05 (America/New_York). Frozen before label reads or probe.

B4.14 permits one training-only correctness and cost probe. B4.12 remains
failed; fixed P/17, all historical outcomes/charges, uniform default and the
sealed final and 48 unused B4.10 cases remain unchanged. No fitting, model
checkpoint read, optimization, new label/reference, continuation, seed
replacement, or threshold/step search is authorized by this protocol.

Select the first two case IDs in each `(nx=12/24, direction=y/z)` cell of
the canonical B3 `train` / `expanded` membership. The execution plan prints
all eight exact IDs and metadata before any artifact access. Only these
label bytes can be read, using the B3 fitting access guard plus the exact
train-only subset guard. Bind the closed B4.14 release and B3 complete index
by SHA-256. Execute only from clean, separately CI-passed merged source with
one BLAS/OpenMP and Torch thread. All artifacts stay outside Git.

For each case use two fixed raw fixtures, with `i=1..n`:
`volume + .02*sin(.37*i) + .01*cos(.13*i)` and
the repeating raw values `.02,.5,.98`. No label value enters these fixtures. Use normalized
`sin(.37*i)` and `cos(.13*i)` directions at both `1e-4` and `2e-4` central
steps. The two sides must retain the central clipping active set; a crossing
is a failed differentiability check, not permission to change the step.
Run three complete prepared forward / CPU Torch backward measurements per
state, plus eight difference solves per state. No discarded warmup.
There are 48 timed objectives and 128 difference objectives (176 FEM
solves). An independent auditor separately assembles/solves the eight stored
normalizers and sixteen central states (24 more), giving exactly 200
FEM solves. Audit fixture, projection, filter, gradient, volume, shift
invariance, active sets, all difference arithmetic and dtype bridge against
independent formulas. Preserve all raw fields and timing observations.
Legacy projection differences are quantified, never declared byte-identical.

Correctness requires all 64 directional checks within `1e-4` normalized
error, physical-volume error `<=1e-12`, and independent compliance and
raw-gradient agreement at `rtol=1e-9` (gradient `atol=1e-10`). These tolerances
are frozen before execution. Stable clipped and free entries must both be
represented in the complete panel; synthetic tests additionally cover both
bounds, kinks, invalid inputs, and zero volume/shift derivatives.

Charge complete label read/setup, every forward/backward, audit, process
startup/exit, failed attempts and closure. Probe and audit each have a
600-second wall-plus-10-second reserve cap; whole slice cap 1,260 seconds
including 30 seconds reserved for closure, maximum RSS 1 GiB. Stop at a cap;
never resume with a fresh free budget. Native `/usr/bin/time -l` profiles
and exact command receipts close the ledger. Closure must itself finish
within its 30-second reserve and retained peak. No successful output overwrite.

The prospective three-fit proxy is fixed at 3 seeds * 200 epochs * 508
expanded train cases, comprising 432 small and 76 large cases per epoch.
Use the maximum measured prepared forward/backward wall per scale over all
24 measurements, multiplied by the full population and a fixed 1.25 cost
factor, plus the conservative 3,870.204341-second cost of ALL twelve B4.1
fits and this probe's complete closed charge. This deliberate upper planning
proxy is not a measured new fit; require `<=7,200 seconds`. No early stopping
or reduced epochs is substituted after viewing cost. RSS is measured for
this sequential probe only; full training memory feasibility remains pending.
Report additional-fit cost and conditional amortization for 1,000/10,000
queries at hypothetical 0.1/1.0 seconds of saving per query. These assumptions
are not observations or acceleration claims; do not infer quality from loss.

Ordered decision: numerical failure => B4.16 bounded adjoint correctness
review; numerical pass but prospective time fails => B4.16 bounded offline
adjoint cost-feasibility review; both pass => B4.16 compliance-objective fit
preregistration, with full training memory and independent repair/confirmation
requirements still pending. No fit or fresh cohort opens automatically.
A passing repair, independent confirmation, compatible final contract and
later final Gates remain required before B5. Report the next slice and stop.
