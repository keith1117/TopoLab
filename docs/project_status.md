# Current project status

Updated: 2026-10-06. Latest completed research slice: **B4.20**.
Next: **B4.21 bounded surrogate correctness failure review**, not started.

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

[B4.20's fixed correctness panel](validation/b4_20_surrogate_correctness.md)
completed eight guarded train cases, sixteen projected synthetic inputs,
64 directional rows and 32 new FEM solves. All 984 independent numerical
conditions completed; 983 passed. One directional error, `0.000125254361629`,
exceeded the unchanged `1e-4` bound, so **the correctness Gate failed**. Complete
new charge was 100.30 seconds and observed peak RSS 447,741,952 bytes.

The stored-denominator tangent separates serialized physical density from the
continuous filtered anchor; 6/8 current anchors would reject the old equality.
This does not recover [B4.19's](validation/b4_19_local_compliance_surrogate.md)
unpublished failed case, gap or exact label/FEM counts. Those fields stay unknown.
Durable before-call journals preserve the complete current B4.20 population.
No local fidelity, prospective fit-cost or full training-memory acceptance is
established; no fitting or final access occurred.

## Current stop and next slice

Only **B4.21 bounded surrogate correctness failure review** is next. Its finite
boundary must be separately registered before execution. This documentation
maintenance does not start it. No fidelity/cost probe, numerical rerun or fit
follows the failed correctness Gate automatically.

The failed exact-FEM candidate stops. Alternate cache/ordering, continuation,
epoch/population/physics-frequency searches, threshold changes and seed replacement
are not authorized by prior failures. Preserve all historical statuses, unknown
fields, complete charges and access guards.

All final evidence and the **48 unused B4.10 fresh cases remain sealed**. Passing
versioned learned repair, independent confirmation, the complete new B4 Gate and
a compatible final contract remain required before B5. The
[English v2 roadmap](planning/TopoLab_v2_development_roadmap.md) controls the later
Gate order; the [B4.20 protocol](planning/b4_20_surrogate_correctness_protocol.md)
and its result control this current stop.
