# Current project status

Updated: 2026-10-06. Latest completed research slice: **B4.22**.
Next: **B4.23 bounded versioned local-surrogate fidelity and cost probe**, not started.

## Delivery and operational boundary

The historical `v1.0.0` release and Gates N1, N2, P1, M0, A1 and A3 are complete.
A2.1–A2.2 implemented local process workers and durable run ownership; the full
A2 Gate remains open pending optimizer recovery and cancellation/resource bounds.
M1 did not establish acceleration; M2 failed its data Gate. M3 v1 was superseded
before fitting or final evaluation. Their results and exposure boundaries remain.

Full v2 flagship delivery requires reproducible, same-quality learned end-to-end
acceleration on a prospectively defined workload. **Uniform remains the operational
default.** No final acceleration or full-delivery claim is allowed.

B3's [complete data Gate](validation/b3_4_data_gate.md) and the twelve fixed
[B4.1 fits](validation/b4_1_fixed_fitting.md) passed. The original
[B4.2 development Gate](validation/b4_2_development_screen.md) failed and produced
no primary or freeze. Later bounded development passes did not clear the required
independent confirmations. Fixed P/17 remains unrepaired; outcome-based primary
replacement is forbidden. The [complete history](development_history.md) and
[validation index](validation/README.md) retain every intervening result.

## Latest result and unresolved evidence

[B4.22's versioned correctness probe](validation/b4_22_stable_projection_correctness.md)
passed its frozen correctness Gate. 1704/1704 independent conditions passed across eight cases, sixteen fixtures
and 64 rows at both steps. Maximum directional error is 5.64e-9; 32 FEM solves
and 304 projections were paid.
Complete new charge is 104.62 seconds; peak RSS 433274880 bytes.

[B4.20](validation/b4_20_surrogate_correctness.md) remains failed 983/984 at the
unchanged 1e-4 bound, with 32 solves and 100.30-second charge.
[B4.21](validation/b4_21_correctness_failure_review.md) passed read-only acceptance,
but its envelope compatibility did not establish a cause. B4.19's failed case,
gap and exact counters remain unknown. All prior failures and charges remain.
No local fidelity, fit-cost or full training-memory acceptance is established.

## Current stop and next slice

Only **B4.23 bounded versioned local-surrogate fidelity and cost probe** is next, not started.
Freeze its separate finite boundary before any new invocation. Existing stored
normalizer/intercept, cotangent, root/gradient criteria and all prior outcomes
remain. No fitting or learned repair follows correctness alone.

The failed exact-FEM candidate stops. Alternate cache/ordering, continuation,
epoch/population/physics-frequency searches, threshold changes and seed replacement
are not authorized. Preserve every failure, unknown field and complete charge.
Final evidence and all **48 unused B4.10 fresh cases stay sealed**. Passing learned
repair, independent confirmation, the complete new B4 Gate and a compatible final
contract remain required before B5. The
[English roadmap](planning/TopoLab_v2_development_roadmap.md) controls Gate order;
the [B4.22 protocol](planning/b4_22_stable_projection_correctness_protocol.md) and
result control the current stop.
