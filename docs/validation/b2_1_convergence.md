# B2.1 large-mesh convergence intervention

Date: 2026-09-25

Protocol revisions: `312e3a4` (cohort before diagnosis), `1fe5793`
(single candidate before corrected execution). Runner/policy revision:
`bbd3f48`.

Status: **B2.1's bounded numerical gate passes.** All twelve fixed uniform
references now pass under the explicitly versioned opt-in termination policy.
The learned-prototype part of Gate B2 remains open: all five unchanged M1
starts together are slower after complete fallback charges. No ML acceleration
or full v2 delivery claim follows.

## Frozen boundary and numerical correction

The [protocol](../planning/b2_1_convergence_protocol.md) retained all twelve
B2 fixed-root cantilever cases at `12 x 6 x 3` and `24 x 12 x 6` elements,
including the three large cases that had failed the historical 120-update
design-density convergence rule. Case definitions were reconstructed from
frozen M2 catalog/split metadata. No M2 label or test/OOD outcome was read.
The old `topolab.simp.v1` path, public default, M1/M2 outcomes, and B2 report
were left intact.

Read-only replay first reproduced all twelve B2 iteration counts and
compliances. At update 120, the three failed large cases had maximum design
changes `0.02275`, `0.02221`, and `0.01145`, while their maximum physical
changes were only `0.00134`, `0.00096`, and `0.00065`. Their ten-update
relative compliance improvements were `0.000120`, `0.000142`, and `0.000091`.
The diagnosis JSON remained outside Git (SHA-256
`7f9d25dc6459d46982dbfb81c6f52573f552b38533a01503bd10754227d0873b`).
This supports testing a filtered-physical-state plateau criterion; it does
not prove global optimizer convergence or permit relabeling the old failures.

The one committed candidate is `topolab.simp.physical_plateau.v1`. It retains
the old design maximum `<= 0.01` stop. Otherwise, it needs at least eleven
completed updates, each of the latest ten per-update maximum **physical**
density changes `<= 0.01`, and nonnegative relative compliance improvement
`<= 0.0002` from update `k-10` to `k`. OC updates, the filtered volume
constraint, SIMP physics, A3 sparse ordering, 120-update cap, and independent
quality audit did not change. Every output binds the old physical case ID to
this solver policy in a distinct `tlcase-b21-v1-*` result ID. A design change
above `0.01` under this policy is reported as a physical-plateau stop, never
as a historical design-convergence pass.

## Execution and independent audit

The committed runner printed exactly twelve distinct versioned result
IDs before execution. Its external plan JSON has SHA-256
`acc48756f3ae4a075442ab635a5c1bd285d49d096a612d9fd891561da1a72dbf`.
The fixed cohort was then executed once with numerical thread variables set
to one on Apple M2 arm64, macOS 26.5, locked Python 3.12.10, NumPy 2.5.3,
and SciPy 1.18.1. The matched comparison JSON stayed outside Git at
`/tmp/topolab-b21-comparison.json` (SHA-256
`8f55978e112f57c7ed6229d227b447519ee9a0a7fd1d99f914b6cf1c7427fbce`).
The locked dependency file SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.

Reproduce the read-only plan with
`PYTHONPATH=src:scripts python scripts/b2_1_convergence.py`. To execute from
the same committed revision, provide `--m1-data-root <frozen-M0-root>`,
`--m1-artifact-root <frozen-M1-root>`, and `--execute`, set OpenMP/BLAS/
VECLIB/MKL/BLIS threads to one, and redirect stdout to an external path.

The full loop took **1045.73 s wall** and reached **429.33 MiB** process peak
RSS. Those are one local run, not portable performance estimates. Uniform
query times totaled 2.66 s on the six small cases and 95.33 s on the six
large cases. The M1 training-only nearest-neighbor index loaded in 0.378 s
and stored 0.603 MiB; five unchanged M1 checkpoint selections loaded in
0.0529 s. One-time setup is separate from per-query ratios and would require
amortization over a declared query count in any deployment claim. The RSS
peak includes all methods and allocator retention, so it is not a
method-specific memory comparison.

The independent audit matched all twelve output IDs to the frozen plan,
checked the six/six scale split, all expected panel methods and five seeds,
every charged fallback, each stop reason, and the plateau's ten-step
conditions. The shared quality checker independently re-solved compliance
outside the timed method cost and enforced `0.005` physical-volume error,
finite state, convergence, and the same `1.001 * uniform` candidate-quality
limit. Maximum volume error among accepted results was `9.91e-9`. No
candidate failure was changed into an accepted success.

## Uniform numerical gate

| Mesh | Direction | Volume | B2 uniform | B2.1 updates / stop | B2.1 compliance | B2.1 accepted |
|---|---|---:|---|---|---:|---|
| Small | y | 0.20 | pass | 32 / design | 0.234101596 | yes |
| Large | y | 0.20 | pass | 103 / design | 0.208268897 | yes |
| Small | z | 0.20 | pass | 29 / design | 0.775766765 | yes |
| Large | z | 0.20 | pass | 58 / design | 0.676828824 | yes |
| Small | y | 0.45 | pass | 25 / design | 0.038728321 | yes |
| Large | y | 0.45 | pass | 67 / physical plateau | 0.040808387 | yes |
| Small | z | 0.45 | pass | 46 / design | 0.111174811 | yes |
| Large | z | 0.45 | fail | 112 / physical plateau | 0.118420447 | yes |
| Small | y | 0.60 | pass | 54 / design | 0.025455237 | yes |
| Large | y | 0.60 | fail | 94 / physical plateau | 0.027276150 | yes |
| Small | z | 0.60 | pass | 76 / design | 0.079616461 | yes |
| Large | z | 0.60 | fail | 105 / physical plateau | 0.084885968 | yes |

All twelve meet the new declared criterion within the unchanged 120-update
cap. Eight of the nine historically valid cases reached the exact same
design-stop outcome and compliance. The ninth, large `y, 0.45`, stopped at
67 updates under the new rule and had compliance **0.0301%** above its B2
reference, within the predeclared **0.1%** regression guard. The four
physical-plateau stops still had terminal **design** changes between 0.0134
and 0.0241; their largest ten-update physical change was 0.00242 and their
ten-update relative compliance improvements were between 0.000182 and
0.000200. This is a newly defined numerical acceptance result, not a
retroactive pass for B2's old design-density rule.

## Same-policy method comparison

All methods were rerun with the **same** B2.1 policy and case settings. The
oracle starts from its own newly computed uniform result and is impossible in
deployment. The physics heuristic, M1 training-only nearest neighbor (small
scale only), and all five unchanged M1 checkpoints were reused. A failed
candidate paid for a fresh B2.1 uniform fallback. Independent quality-audit
re-solves were excluded from each method's timed cost, consistently with B2.
Ratios below are per-attempt charged query time divided by its matching new
uniform query time, then averaged over the fixed cohort; they are not paired
with historical B2 timings.

| Scale | Method | Candidate quality passes | Mean charged ratio | Charged fallback total |
|---|---|---:|---:|---:|
| Small | own-result oracle | 6 / 6 | 0.074 | 0 s |
| Large | own-result oracle | 6 / 6 | 0.109 | 0 s |
| Small | physics heuristic | 6 / 6 | 1.022 | 0 s |
| Large | physics heuristic | 6 / 6 | 1.031 | 0 s |
| Small | M1 train-only nearest neighbor | 2 / 6 | 2.250 | 1.76 s |
| Small | five unchanged M1 seeds | 20 / 30 | 1.556 | 5.65 s |
| Large | five unchanged M1 seeds | 16 / 30 | 1.718 | 238.24 s |

The learned panel had ten small and fourteen large quality failures. Only ten
of 30 small attempts and eight of 30 large attempts had charged time below
their paired uniform time. Every failure remained in the denominator and paid
fallback. The oracle's conditional headroom is real for this versioned
development cohort, but the existing learned initialization still does not
turn it into end-to-end savings. No model was retrained or selected.

## Gate decision, limits, and next slice

**B2.1 numerical acceptance passes:** all six large and six small uniform
references are quality-feasible under the single committed policy, without
changing the old solver or the iteration budget. **The B2 learned-prototype
gate still fails:** the unchanged five-seed learned panel is slower than
uniform at both scales after fallback charges. The roadmap's positive ML
delivery condition remains open. The fixed cohort covers one support family,
one local hardware environment, and an explicitly development-exposed
termination threshold. Fresh, physically disjoint evidence is still required
for any acceleration claim.

The next independent slice is **B2.2: a bounded development-only
quality-aligned learned-prototype plan and data-feasibility gate**. It should
freeze one control and one candidate intervention that directly address B1's
unseen `z` direction and failed warm-start quality basin, plus training/label
budget, exposure ledger, and fallback-inclusive validation rule under
`topolab.simp.physical_plateau.v1`. A small, separately reviewable fitting
slice follows only if the required development labels can pass their data
gate. Do not open a new final cohort or register B3 yet.

## Repository validation

Before the runner commit, `uv sync --dev --locked`, Ruff, mypy on `src` and
the runner, full pytest (**276 passed**), and diff checks passed. The
independent high-volume numerical acceptance test was written and observed
failing before the policy was implemented. Final report-commit and CI
validation are recorded by the PR workflow.
