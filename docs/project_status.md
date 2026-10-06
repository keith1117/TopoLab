# Current project status

Updated: 2026-10-06. Latest completed research slice: **B4.23**.
Next: **B4.24 bounded versioned surrogate correctness failure review**, not started.

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

[B4.23's versioned fidelity/cost probe](validation/b4_23_versioned_surrogate_feasibility.md)
failed its frozen feasibility Gate: integrity 3907/3976, with 35 side-mask and
34 finite-difference conditions failed. All 32 LOCAL states met the four observed
fidelity criteria, but failed integrity prevents method acceptance or fitting.
The complete cost proxy is 57546.072069 seconds against 7200. All 72 states,
216 first-inclusive timings and 64 directional rows remain; 432 FEM solves
and 816 projections were paid.
Complete charge: 143.47 seconds; peak RSS: 550502400 bytes.
Full training memory, learned repair and independent confirmation remain pending.

[B4.22](validation/b4_22_stable_projection_correctness.md) passed bounded
1704-condition correctness. [B4.20](validation/b4_20_surrogate_correctness.md)
remains failed 983/984 at unchanged 1e-4, paying 100.30 seconds.
[B4.21](validation/b4_21_correctness_failure_review.md) passed read-only acceptance;
its diagnostic compatibility did not establish a cause. B4.19's actual failed
case, gap and counters remain unknown. Every prior failure and charge remains.

## Current stop and next slice

Only **B4.24 bounded versioned surrogate correctness failure review** is next,
not started.
Freeze its separate boundary before any new invocation. No fitting follows this
finite probe automatically, and full training-memory acceptance is still absent.

The failed exact-FEM candidate stops. Alternate cache/ordering, continuation,
epoch/population/physics-frequency searches, threshold changes and seed replacement
are not authorized. Preserve every failure, unknown and complete charge.
Final evidence and all **48 unused B4.10 fresh cases stay sealed**. Passing learned
repair, independent confirmation, the complete new B4 Gate and a compatible final
contract remain required before B5. The
[English roadmap](planning/TopoLab_v2_development_roadmap.md) controls Gate order;
the [B4.23 protocol](planning/b4_23_versioned_surrogate_feasibility_protocol.md)
and its result control the current stop.
