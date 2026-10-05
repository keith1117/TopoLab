# B4.17 bounded offline FEM phase-cost and setup-reuse probe

Prepared: 2026-10-05 (America/New_York), before candidate execution.

Freeze one candidate, `topolab.prepared-offline-compliance.v1`: reuse only
case-local unit Hex8 stiffness, COO row/column indices, free-DOF/load maps
and filter physical-volume weights. Keep the B4.15 mathematical projection,
filter, SIMP adjoint, CPU Torch dtype/first-order bridge and tolerances.
COO-to-CSR summation, fresh density coefficients, reduced CSC construction,
A3 automatic ordering (COLAMD below 5,000 free DOFs, MMD_AT_PLUS_A otherwise),
fresh numeric SuperLU factorization, singular-pivot rejection and displacement
solve remain unchanged. No factorization, density or output is cached.
Prepared arrays are read-only; no cross-case global cache. Query solver,
B4.15 kernel/default, labels, fixed P/17 and historical failures stay unchanged.

Bind complete closed B4.16 evidence, releases, exact-head CI, native profiles,
closure proof and controller reservation, plus all B4.15 and prior guards.
Reuse only the eight canonical expanded-train cases and sixteen synthetic
fixtures already certified in the hash-bound B4.15 probe JSON. Normalizers
are the independently certified constants from that JSON. Verify exact case,
state, raw fixture and normalizer identities before any new FEM call.
No label, checkpoint, optimized-state artifact, fit, optimizer, new reference,
continuation, screen or final artifact is opened. All 48 unused B4.10 cases
and final evaluation remain sealed. Default CLI only prints metadata; it
reads no evidence bytes and creates no output. Execution requires clean,
separately CI-passed merged source, locked CPU runtime, one BLAS/OpenMP and
Torch thread, fixed sibling external roots and no successful-result overwrite.

For each case construct both original and prepared kernels; time/charge every
setup including immutable precomputation. For each interior/clipped fixture
run three paired complete CPU float64 Torch forward/backward measurements.
Even repeats execute prepared then original; odd repeats original then prepared.
Keep all 96 measurements including each first observation. Store every loss
and raw gradient plus the maximum repeat difference; no discarded warmup.
Then run exactly one instrumented prepared NumPy objective, retaining six
sequential exclusive phase wall/CPU intervals: projection/filter, numeric
assembly, reduction, factorization/pivot checks, solve/energy, filter/projection
pullback. Complete outer time and residual clock/instrumentation work remain
reported; phases never replace/subtract from complete query/probe charges.
Instrumented NumPy timings are diagnostic, not the Torch timing population.

Retain the B4.15 two fixed directions and steps 1e-4/2e-4: eight prepared
central-difference sides per fixture (128 solves). Three paired repeats give
96 solves and sixteen phase calls give 16, so probe exactly 240 FEM solves.
An independent auditor uses the existing independent Brent projection and
uncached FEM/energy formulas for all sixteen central states (16 more): total
256 new solves. Normalizers remain prior certified evidence, not new solves.
All 64 differences must retain their central free set and normalized error
<=1e-4. Original/prepared and independent projection densities use absolute
2e-11, compliance/loss rtol=1e-9, gradients rtol=1e-9/atol=1e-10, physical
volume <=1e-12, shift-gradient sum <=1e-10. No tolerance, step, density,
ordering or population search; all numerical failures stay reported.
Tests must also exercise changing-density fresh factorizations, read-only
cache, invalid/kink inputs, original-path identity, float32/64 bridge, singular
systems, missing/reordered timings, forbidden metadata reads and failed costs.

The new candidate planning proxy keeps three seeds, 200 full epochs, 432 small
and 76 large cases, and factor 1.25. Use maximum complete prepared Torch wall
per scale across all 24 observations, plus three full-population preparations
using maximum observed prepared setup wall per scale with the same factor.
Add ALL twelve B4.1 fits' 3,870.204341 seconds, B4.15's 84.33 seconds,
B4.16's 55.99 seconds and this complete closed probe charge. Require <=7,200
seconds. This sample extrapolation is not a measured full fit or a rigorous
all-case bound. Keep B4.15's original failed 60,339.394130 proxy unchanged.
Report all matched control times, phases, CPU, setup and static retained array
bytes. The full-population sum using maximum retained bytes per scale is a
planning estimate; sequential RSS cannot certify full network/optimizer memory.
Shared data and all historical development/future screen/final/replication
charges remain additional in a later full experiment ledger. No learned
quality, repair or acceleration claim follows from caching or correct gradients.

Probe/audit each have 600 charged seconds (complete wall plus ten seconds),
whole cap 1,260 seconds, RSS 1 GiB. Fully pay a 60-second closure/controller
reservation including the metadata plan and post-exit verification; retain their native profiles and
commands. Their combined native wall + ten seconds per process and internal
closure charge must fit the reserve; native peaks must fit the retained peak.
All failed attempts and process startup/I/O/exit stay charged in the same ledger;
no free retry, budget reset or numerical rerun. Arithmetic rtol/atol=1e-12.

Ordered next decision: numerical/integrity failure => B4.18 bounded prepared-
adjoint correctness review; otherwise failed cost => B4.18 bounded offline FEM
bottleneck and training-objective method review; otherwise => B4.18 full-
population setup-memory and objective-fit preregistration. Report the next
slice and stop. No automatic fit, alternative candidate, epoch/population/
physics-frequency search, seed replacement or fresh cohort access. A passing
versioned learned repair, independent confirmation and compatible final
contract remain required before B5; fixed P/17 remains unrepaired.
