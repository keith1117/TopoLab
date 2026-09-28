# B2.16 frozen method-class and speed-headroom reassessment

Status: frozen before running the B2.16 derived assessment. This is a
read-only development diagnosis, not a new fit, solver run, workload change,
checkpoint selection, or final acceleration test. Plan version
`topolab.b2_16.method_class.v1` has canonical SHA-256
`fa1370508e5a94650b80e6f1b3170699072625abc39b88287d498104e04f1c03`.

## Question and fixed evidence

B2.14 and B2.15 each retained 24 physically disjoint two-scale cases and
all fully charged outcomes. B2.14 rejected every deployable policy; B2.15's
new route failed its large-y and 5%-improvement criteria. Determine whether
the **existing fixed checkpoints and coarse metadata routing** have enough
optimistic same-quality headroom to justify more work, and whether a
strictly bounded, query-time reliability intervention is worth a separate
experiment. Do not tune a new route on these exposed cases or change any
historical Gate.

Read only these already exposed artifacts:

| Cohort | Reference-index SHA-256 | Screen-index SHA-256 | Frozen source |
|---|---|---|---|
| B2.14 | `b44c98573d50b1e9c26b5a8ff3bf42ebe211197455c88d5f65f2a01f941a010e` | `2c2bb58c40bf1e2099fd21ecf3cc74a5425ca3f1ad28ac183611c1535bb4e6c9` | `884a3371c8aa919f96b4db27018b5066677bbf69` |
| B2.15 | `1e21d3f2a4ac21522c76911a12640ba551bf4f7939b72121c19fdb6b1146f998` | `2bcf6d313257d85f13199241f0cc603203596e062a2429012f371d0c7e5c36b0` | `c70a0d92d26bda3df1da0168c135404493df8c3b` |

Verify both file hashes, source/plan/reference identities, 24 references,
24 unique cases and eight ordered method outcomes per cohort, quality,
fallback status, timing-phase sums, and paired ratios before deriving any
decision. Use only the common actions: fresh uniform, vector 29, context
17, and context 43. Context 29 appears only in B2.14 and cannot enter a
matched-cohort comparison. Keep all 48 cases and all failed attempts.
M2 test/OOD and new final evidence remain sealed. Generated summaries and
audit logs remain outside Git. Read-only plan and assessment run from one
clean committed source revision. Cap assessment at 60 s and 1 GiB peak RSS.

## Predeclared analyses

1. **Perfect-selector floor.** For each case choose the fastest *successful*
   fully charged common action, breaking exact ties in order uniform,
   vector 29, context 17, context 43. This outcome-aware choice is an
   optimistic, undeployable lower bound on those fixed actions. Report
   overall, two-scale, four direction means, and failures separately for
   B2.14 and B2.15.
2. **Coarse-cell transfer.** Match cohorts by mesh scale, y/z load direction,
   ascending low/middle/high volume tier, and lower/upper free-end z
   position: 24 one-case cells per cohort. Pick each training cell's
   successful perfect-selector action, then apply that action to its
   counterpart in the other cohort, in both directions. Charge the full
   fixed-method outcome and fallback on the target case, even if the
   transferred action fails. Assume zero lookup overhead, making transfer
   optimistic. Report action disagreements and both target summaries.
3. **Perfect failure rejection.** On the unchanged B2.15 new route only,
   replace each failed learned attempt's ratio by exactly `1.0`, an
   impossible zero-cost early rejection to fresh uniform. Keep all other
   measured route results, including existing rejections. Recompute the
   B2.15 scale/direction and strict 0.95-times-old-route Gate. For a
   hypothetical diagnostic run on the two high-volume large-y positions,
   compute the greatest equal *additional seconds per position* allowed
   by the large-scale, large-y, strict old-route-improvement, and non-ML
   constraints. This is a supremum, not an observed runtime. Compare it
   with one measured uniform refinement update per at-risk case, calculated
   as refinement seconds divided by completed updates.

The common retrospective feasibility threshold for (1) and (2) is at most
two failed learned attempts, fully charged paired mean `<=0.90` at each
scale, mean `<=1.0` in all four scale/direction cells, and overall mean
strictly below both fixed non-ML comparators. All accepted operational
results must preserve the `1.001` compliance and `0.005` volume bounds.
This threshold is a diagnostic from the B2 development Gates, not a
retroactive pass of B2.14/B2.15 or a final confidence-interval claim.

## Decision rule

Apply the following ordered decision without revising thresholds:

1. If the perfect-selector floor fails the common feasibility threshold
   on either cohort, retire routing among these fixed checkpoints: even
   impossible case-by-case selection lacks sufficient observed headroom.
2. Otherwise, if coarse-cell transfer passes in both directions, coarse
   metadata routing remains plausible but still requires a separately
   frozen, physically fresh development confirmation before B3.
3. Otherwise, if perfect failure rejection passes the B2.15 Gate and its
   per-position pilot budget exceeds the larger of the two measured
   one-update costs, permit **one bounded online reliability probe** in a
   new slice. This is only a cost-floor screen; the probe must later show
   an observable early quality signal and pass its own fresh Gate.
4. Otherwise, stop the current fixed-checkpoint warm-start family pending
   a genuinely new, bounded mechanism. Do not continue changing
   position/volume thresholds on exposed cohorts.

No outcome here opens B3 or permits an acceleration claim. A method-class
pivot needs a new frozen protocol, explicit cost and stopping rule, and
fresh development evidence. A negative decision does not withdraw the
historical v1 platform or prove that all ML acceleration is impossible.
