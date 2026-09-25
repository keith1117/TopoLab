# B2.2 development prototype and data-feasibility protocol

Status: frozen before any B2.2 policy-label feasibility execution. This is a
development-only intervention and does not register or open the B3/B5 final
cohort. Historical M1, M2, and B2 results remain unchanged.

## Measured hypotheses and one controlled comparison

B1 observed worse unseen-`z` generalization and quality failures even on
familiar `y` loads. B2.1 established a quality-feasible two-scale uniform
reference under `topolab.simp.physical_plateau.v1`, but the unchanged M1 panel
remained slower after fallback. The first hypothesis is that training on both
`y` and `z` cases under the **same new solver policy** improves direction
coverage. The second is that error in physically sensitive elements matters
more than unweighted design-density error for a useful warm start. Neither
hypothesis is presumed true.

The future bounded fit compares exactly two arms on identical cases and seeds:

| Arm | Model/input/target | Training objective |
|---|---|---|
| Control | M1 shape-preserving 11,281-parameter CNN; 10 existing case channels; new B2.1-policy final **design** labels | Elementwise design-density MSE |
| Candidate | Same model, inputs, target, initialization, data, seeds, and optimizer | Sensitivity-weighted design-density MSE |

For each new training label, compute the absolute compliance derivative with
respect to design density at that label's independently solved physical state,
including the density-filter transpose. Divide by its within-case mean, clip
to `[0.25, 4]`, then divide by the clipped mean so weights average exactly
one. The candidate loss is the mean of `weight * (prediction - label)^2`.
Weights are stored and audited with the training label; they are not inference
inputs. Count the derivative solve and storage in data-generation cost. Both
arms use the same volume projection and refinement; no query-time physics
feature is introduced. This loss is a testable proxy for reaching a suitable
quality basin, not a proof of that behavior.

Three fixed seeds are `17, 29, 43`. Retain the M1 AdamW settings, batch size 8,
at most 200 epochs, patience 25, CPU float32, and earliest minimum of each
arm's own validation objective. The existing M1 dataset/fitter rejects mixed
spatial shapes: the later fitting slice must introduce deterministic
shape-bucketed batches with equal sample exposure and optimization steps for
both arms. Do not silently resize or interpolate labels. Cap the full
six-fit development attempt at four hours wall and 2 GiB peak RSS on the
declared local machine. If the cap is exceeded, report failure and version a
new plan before further fitting.

## Physical cases, exposure, and label identity

The committed runner selects only frozen M2 **catalog and split metadata**.
Small cases are all 432 M2 train and 36 M2 validation `y/z` problems on
`12 x 6 x 3`. Large cases are physically paired `24 x 12 x 6` refinements of
the two lexicographically first train and one first validation source case in
each of 18 `(direction, volume)` strata. That adds 36 train and 18 validation
cases. The plan is 522 distinct physical cases: 468 train, 54 validation,
261 per direction. Each small/large physical pair retains the source split.
It includes all nine volume strata from `0.20` to `0.60` and the B2.1 fixed
validation cases. The case order and full IDs are in the read-only plan.

Plan version `topolab.b2_2.plan.v1` has canonical SHA-256
`f2f7b27ff396e11fd44845f8c6811e42f86a48587f329b94a2548ca610073dc8`.
The prospective label contract is `topolab.b2_2.label.v1`; its result ID binds
the physical case ID, this label version, and
`topolab.simp.physical_plateau.v1`. Old M2 labels have the historical solver
identity and are **incompatible**, even when the physical case ID matches.
No old test/OOD label or outcome may be used; M2 validation and historical B2
cases are already development-exposed. B3 must register a new physically
disjoint final and OOD cohort before those outcomes are opened.

## B2.2 feasibility probe and Gate

Before full materialization, run a fixed 61-case uniform-start sentinel:
the seven historically failed **training** cases, one small validation case
per `(direction, volume)`, and one large train plus one large validation case
per stratum. The seven identities come from the historical M2 failure record;
the repository report has a one-character transcription error for the
`(y,z)=(5,2)` training case, corrected by verification against the frozen
catalog. All 61 IDs and result IDs are frozen by the plan hash.

Run the committed runner from a clean tracked revision with BLAS/OpenMP
threads set to one. It uses the same projected uniform start and opt-in solver
policy as B2.1. Every case remains in the denominator. Require **61/61** to
converge in at most 120 updates, filtered physical-volume error at most
`0.005`, positive finite compliance agreeing with an independent re-solve
within relative `1e-9`, and no solver exception. The total probe must stay
within 1,200 s wall and 1 GiB peak process RSS. An exceeded budget, missing
row, or any quality failure fails B2.2; no label or model fitting follows
under this plan. The runner prints only metadata JSON to an external path,
not density fields or label artifacts. The Gate says the sampled data are
feasible, not that all 522 labels exist or a learned method is accelerated.

Only after this probe passes may an **independent** slice materialize and audit
all 522 new policy labels. Freeze its source/environment manifest and compute
budget before execution. Its complete data gate requires 522/522 valid labels,
explicit policy/result identity, per-stratum and split counts, checksums,
independent numerical quality, and total generation at most two hours wall
and 1 GiB peak RSS on the declared local machine. A new failure remains a
failure and cannot be dropped to make training possible.

## Later development-prototype screen

After a complete data gate, fit the two arms without test/OOD outcomes and
evaluate all 54 exposed validation cases at both scales. Use the same
version-matched optimized uniform denominator and fixed non-ML baselines.
Charge inference, volume projection, decision, full refinement, rejection,
and fresh uniform fallback for every failed candidate. Independent quality
requires convergence, the same volume and compliance audits, and final
compliance no worse than `1.001` times its matched uniform reference. Count
every seed, direction, volume stratum, and failed attempt. One-time model or
index loading is reported separately for later query-volume amortization.

The prototype justifies proceeding to B3 only if at least one arm has at
least two of three fixed seeds with fallback-inclusive mean time ratio
`<= 0.90` **at each scale**, no accepted quality failure, and direction-wise
mean ratio `<= 1.0` at each scale. A candidate that improves image loss but
not operational time/quality does not pass. If both arms fail, diagnose the
new failure and version one different development hypothesis; keep final
evidence sealed. This is a development screening threshold, not the v2 final
confidence-interval delivery Gate.
