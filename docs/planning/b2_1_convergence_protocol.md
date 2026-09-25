# B2.1 large-mesh convergence intervention protocol

Status: acceptance cohort frozen before the B2.1 trajectory diagnosis or any
corrected solve. This is development-only evidence, not an amendment of B2,
M1, or M2 and not an ML experiment registration.

## Fixed cases and historical boundary

Use all twelve B2 cantilever physical problems: the six small cases and their
six physically matched large cases, with the same loads, supports, material,
physical domain, filter radius, volume fractions, and A3 automatic sparse
ordering. The B2 protocol and report define the historical 120-step outcomes.
The large case IDs, in the fixed order `(y,z) × (0.20,0.45,0.60)`, are:

| Direction | Volume | Historical large case ID | B2 uniform status |
|---|---:|---|---|
| y | 0.20 | `tlcase-v1-3303f49ad6b4a791a18e89871b650978b10c40bdcade055283e9a068bc599ac2` | pass |
| z | 0.20 | `tlcase-v1-26085a2a8177c288f4506633fc1660fdbdae96306800fc02d69cbf988f1106b1` | pass |
| y | 0.45 | `tlcase-v1-cc988eff60275239d82a848ce0d2c5663978c0b8238a3d75c477627255795727` | pass |
| z | 0.45 | `tlcase-v1-0323121accc756500ebbbf75c037863169a128796d2950a02ffd564b9d4e1cf3` | fail |
| y | 0.60 | `tlcase-v1-17b81b5d678bd05109b31b55272ace9421584ea2e06fad1d39c39c4afa846fdd` | fail |
| z | 0.60 | `tlcase-v1-628d8eeca241819a6dc010777e25f3e990705d98d59c098446710d2770df7ef2` | fail |

The six small peers are the `source_case_id` values fixed in the B2 pilot JSON
and protocol. Reconstruct definitions from the frozen M2 catalog and split
metadata; do not read a label artifact. All twelve remain in the denominator.
No new final cases or held-out labels may be opened. Generated traces belong
outside Git.

## Diagnostic, correction, and acceptance order

1. Reproduce the three failed large uniform cases under the unchanged solver.
   Capture per-iteration maximum design-density and physical-density changes,
   compliance, and physical volume, and inspect the already successful cases
   for a guard against altered accepted outcomes. This stage is read-only.
2. Based on that full fixed diagnosis, name **one** explicit OC or termination
   policy correction, its mathematical criterion and safety checks, and its
   new solver/result identity **in a committed amendment to this protocol
   before executing the corrected cohort**. Do not tune a sequence of
   thresholds against the case outcomes or silently increase the iteration
   limit. Keep `0.01` as the density-change scale; any different termination
   metric must be stated explicitly, not described as passing the old gate.
3. Implement the correction as an opt-in numerical policy so the historical
   `topolab.simp.v1` path, M1/M2 outcomes, and public default stay unchanged.
   Write an independent acceptance test before changing numerical behavior.
   Give the new solver policy and every output an explicit version identity;
   a B2 case ID alone is insufficient to identify a corrected result.
4. Run the same twelve uniform cases once under the committed candidate.
   Require all six large and all six small cases to pass the **newly declared**
   convergence criterion within 120 updates, filtered physical-volume error
   at most `0.005`, finite positive independently re-solved compliance with
   relative agreement at most `1e-9`, and deterministic same-state history.
   On the nine historically valid cases, corrected final compliance may not
   exceed `1.001` times its B2 matched reference. Keep every failure visible.
5. Only if the uniform gate passes, rerun the B2 comparison panel under the
   **same** corrected solver policy and case settings, charging all inference,
   projection, refinement, and fallback costs. The old B2 ratios remain
   historical and cannot be paired with corrected outputs. Do not train or
   choose an M1 seed in this slice.

If the single candidate does not make the intended two-scale workload
quality-feasible, record the failed intervention and version a different
development pilot in a later slice. Passing the uniform gate alone does not
pass B2's learned-prototype requirement or the v2 ML delivery gate.
