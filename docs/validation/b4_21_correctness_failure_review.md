# B4.21 bounded surrogate correctness failure review

Date: 2026-10-06 (America/New_York).

**The read-only review acceptance passed; the original B4.20 correctness Gate remains failed.** All eight cases, sixteen fixtures and 64 saved directional rows were retained at both original steps. All 80 saved-gradient/mask conditions passed; 1152 separate scalar comparisons passed. No new FEM, root, label/model artifact, objective/gradient invocation, fit or final access occurred. Complete new charge is **90.27 seconds**, with peak RSS **300400640 bytes**.

Next: **B4.22 bounded stable-projection correctness probe**, requiring a separate prospective contract and CI-passed merged implementation. Compatibility with a diagnostic envelope selects this hypothesis; it does not establish the cause of the old failure. No local fidelity, fit-cost or full training-memory acceptance is established. Fixed P/17 remains unrepaired, uniform remains default, and final evidence plus all 48 unused B4.10 cases stay sealed.

## Frozen source and complete review

The [protocol](../planning/b4_21_correctness_failure_review_protocol.md) and original arithmetic/reconstruction tools merged in [PR #142](https://github.com/keith1117/TopoLab/pull/142). Tested head `61c9858e8884f7df1f01cb349d8363b1580c10da` and production revision `46a431fcd9ca661af5ec811711056f28463a12d0` have the same tree; all applicable exact-head CI passed before merge, and merged main CI passed before execution. Production binds 151 source/runtime/convention/protocol files. Plan identity `topolab.b4_21.correctness-failure-review.v1`, SHA-256 `08f6340b76d8a5bca7f05b56d886aeab23405131ca2b657c0d17eb72e30ef41a`. Locked Python and one BLAS/OpenMP thread were used.

Thirteen exact B4.20 bindings and recursive B4.19 through B3 metadata guards passed before the complete saved panel was parsed. The original 984 conditions, one failure, 32 FEM solves and 100.30-second charge are unchanged. B4.19's failed case, gap and exact counters remain unavailable. All earlier failed outcomes and charges remain part of later feasibility/amortization; no status or threshold was revised.

The review recomputed the exact saved plus/minus FD, directional dot product, relative error and failure flag for every row. It reconstructed the projection cotangent from the saved signed derivative and free mask, without projecting an input. The independent auditor derives physical-volume weights by scalar Cartesian-neighbor enumeration and fsum, rather than the production filter, projection, pullback or tangent. All 16 gradients agreed at rtol1e-9/atol1e-10 and all 64 side-mask checks passed. Independent scalar comparisons agreed at rtol/atol1e-12. Both steps and all passing rows remain in the external scalar report; no favorable row replaced the rejected row.

## Retained failure and diagnostic scale

For a stable saved free set, A=sum(g_free), D=sum(w_free)>0. The unchanged physical-volume root tolerance 1e-12 implies the diagnostic directional scale abs(A)*1e-12/(D*h). The floating arithmetic scale is gamma_(n+2)*(abs(intercept)+sum(abs(g*(design-anchor))))/h, with gamma_k=k*eps/(1-k*eps) and float64 eps. These are forward-error scales, not a changed FD criterion or a corrected observation. The same formulas were applied to all 64 rows.

The original failed case remains `tlcase-v1-0ca7ef4d765a4e8403221471f98c061684e99dde777b047a1a3f5f0642fc47b6`, clipped/sine at h1e-4. Original FD `0.00014216811283773723`, derivative `0.00014215030566151971` and relative error `0.00012525436162919332` exceed the original 1e-4 Gate. Its absolute discrepancy is `1.78071762175179e-08`; root scale `3.6799181786618705e-08`, arithmetic scale `1.0400341062264295e-08` and discrepancy/combined scale `0.37727449649290928`. The paired h2e-4 retains FD `0.00014215690902208422` and error `4.6451210918544199e-05`. That row does not replace the failed h1e-4 row.

The discrepancy fits the predeclared combined envelope. The original side offsets and volume residuals were not saved and stay unavailable; **a root-error cause is not established**. The ordered decision permits only a separately versioned affine free-set root refinement of the same continuous clipped additive projection, preserving stored denominator/nonunit intercept, free-set cotangent, volume 1e-12, kink 1e-10 and FD 1e-4. No step/tolerance/normalizer/radius/blend/search or fit is selected by this review.

## Complete native resource closure

Each read-only stage caps at 60 charged seconds; whole 240 seconds / 1 GiB includes a fully paid 60-second plan/closure/verification reservation. All first invocations retain complete wall/user/system/RSS profiles. Review and audit charge 14.90+15.37; reserved use 37.39<=60 with the whole 60 paid. There were no failed or repeated production stages. Closure was independently verified after its native profile existed; the closed ledger was not rewritten and all observed peaks are retained.

| Process | Native wall | User CPU | System CPU | Peak RSS bytes | Charge seconds |
|---|---:|---:|---:|---:|---|
| closure | 3.68 | 2.69 | 0.35 | 291553280 | within paid 60 reserve |
| independent | 5.37 | 4.67 | 0.34 | 300400640 | 15.37 |
| plan | 3.58 | 1.87 | 0.32 | 274661376 | within paid 60 reserve |
| review | 4.90 | 4.06 | 0.38 | 298270720 | 14.90 |
| verification | 0.13 | 0.03 | 0.02 | 29605888 | within paid 60 reserve |

The B4.15/16/17/18/19/20 charges 84.33/55.99/112.34/86.13/73.93/100.30 and failed exact-FEM cost proxies 60,339.394130/58,257.457957 remain unchanged. Add this review's complete charge to any later prospective comparison. Sequential read-only RSS does not establish full network/data/optimizer/activation memory feasibility.

## Software validation and publication

Before source commit: locked dev sync, Ruff, mypy (67 source files), **1004 passed in 658.02s**, and working/staged whitespace checks passed. The 26 added regression cases cover complete populations and both steps, arithmetic/gradient/mask tampering, unknown-field and failed-Gate preservation, independent reconstruction, read-free default planning, exclusive publication, complete failed-command charges and caps. Evidence publication repeats every mandatory check and requires current-head plus merged main CI before closeout. Staged paths and every pending commit were reviewed; generated arrays, journals, profiles, logs, models and the ignored local handoff are excluded. Both pre-existing untracked user documents are preserved.

No numerical tolerance was changed. No fit, optimized state, continued optimizer, label generation, model write, fidelity/cost evaluation or final access occurred. Passing learned repair and independent confirmation still precede a compatible final contract and B5. The failed exact-FEM candidate remains stopped.

## External reproduction and bindings

Evidence root: `/Users/keith1117/Documents/TopoLab-data/b4-21-correctness-failure-review`. Native command receipts retain argv, thread settings and complete profile/log identities. The external audit-source copy preserves the metadata controller used for release and execution. Default plan uses `scripts/b4_21_correctness_failure_review.py --probe-root <external B4.20 root> --output-root <external B4.21 root>`; `--execute` is bound to clean released source and refuses existing output. Reproduce in a separate compatible registered output boundary; never overwrite or repeat the original execution.

| Artifact | SHA-256 |
|---|---|
| `audit_receipts/plan.json` | `a100ac8bdb224d0937181bc687191e26f67edcb3d6316504803174d55dacdd1e` |
| `audit_receipts/production_release.json` | `d80a983672d9e2d7efcb9408b200c66bab4acd5932e4debdecdf4a0d9a172f57` |
| `review.json` | `22d698eb38d9e6dda2410e8fe4594de1a71134f059cfafa8848fb78a1b8b9819` |
| `independent_audit.json` | `b4a4401870d53f824bb905e3426c0b562df58734eace7b07d4a4455dab566f17` |
| `resource_close.json` | `8b8fb36eca3285eb1f845da26b8886a404e04765f8c8cd0750fc63bec39b8d1d` |
| `audit_receipts/execution_commands.json` | `cb2ddced8835cd8007c304a64c3871cddfd66e94712c97e6e709aefa44843703` |
| `audit_receipts/closure_profile_verification.json` | `287903096f0096d99686135c20b3e1ca822102c4fa82dbb917b23d4c6cae2712` |
| `audit_receipts/postexit_controller_reservation.json` | `a966f1b6d33643a0fa29474cd6341318f23348d2b1c7921d2d043d495bc4364f` |
