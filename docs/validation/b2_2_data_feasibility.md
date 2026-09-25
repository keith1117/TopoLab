# B2.2 development prototype plan and data-feasibility outcome

Date: 2026-09-25

Frozen protocol/runner revision: `d8c2e55d6fbc795c01b80e40b7b1cf9600153b97`.

Status: **B2.2 is complete with a failed data-feasibility Gate.** The fixed
61-case sentinel produced 53 independently quality-accepted uniform outcomes
and eight non-convergences under the 120-update
`topolab.simp.physical_plateau.v1` budget. No new labels were materialized,
no model was fitted, and no learned acceleration or v2 delivery claim follows.

## Frozen development boundary

The [protocol](../planning/b2_2_prototype_protocol.md) fixed a controlled
two-arm future model test: the existing M1 CNN on new `y/z` labels with its
design-MSE loss, versus the same model/data/seeds with a sensitivity-weighted
design-MSE loss. It also fixed the policy-specific label identity, source
splits, shape-bucket requirement, training/label budgets, and a
fallback-inclusive development validation rule before any fitting.

The committed plan reconstructs 522 distinct development cases exclusively
from frozen M2 catalog/split **metadata**: 432 small train, 36 small
validation, 36 paired large train, and 18 paired large validation. The
preselected sentinel comprises seven historically failed M2 **train** cases,
one small validation and one large train/validation case per `y/z` and volume
stratum. There are 61 distinct case/result IDs. M2 test/OOD labels and
outcomes, and any future final cohort, remained unopened. The old M2 labels
remain tied to `topolab.simp.v1` and cannot serve this plan.

The canonical plan SHA-256 is
`f2f7b27ff396e11fd44845f8c6811e42f86a48587f329b94a2548ca610073dc8`;
the external plan JSON at `/tmp/topolab-b22-plan.json` has file SHA-256
`2912b15c2087fe5592a70878b1351387ca10ee42d03fe2b680ddb0bc7756e3c4`.
The output identity includes the physical case, proposed B2.2 label version,
and new solver policy. The audit matched all 61 ordered case/result IDs and
splits to the frozen plan.

## Execution, numerical checks, and failures

The committed runner executed once on Apple arm64, macOS 26.5, Python
3.12.10, NumPy 2.5.3, SciPy 1.18.1, with OpenMP/BLAS/VECLIB/MKL/BLIS
threads set to one. The locked dependency file SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.
The external metadata-only result at `/tmp/topolab-b22-probe.json` has SHA-256
`45d29dd6568da34fd097a522aff072d08afc121dd98a5f784411d79db7004b78`.
It took **585.93 s wall** and reached **421,543,936 bytes (402.02 MiB)**
peak process RSS, below the predeclared 1,200 s and 1 GiB caps.

| Sentinel stratum | Cases | Quality accepted | Non-converged |
|---|---:|---:|---:|
| Large train | 18 | 17 | 1 |
| Large validation | 18 | 18 | 0 |
| Small train, seven historical failures | 7 | 0 | 7 |
| Small validation | 18 | 18 | 0 |
| **Total** | **61** | **53** | **8** |

All 53 accepted cases met the frozen convergence, finite-state, physical
volume, and independent compliance re-solve checks. Their maximum physical
volume error was `9.89e-9`; 27 stopped by the historical design maximum and
26 by the new physical-plateau rule. All eight failures exhausted 120 updates
without satisfying either stop rule. None was reclassified as an accepted
label. The seven small failures are the known `y/0.45` M2 train cases. The
additional large `z/0.20` case is
`tlcase-v1-58e145330eb9318f46e047e638b5387aa558d944c370d5ea707e3e6d3d2ba328`.

A separate read-only replay of those eight cases preserved the failures. The
diagnostic JSON at `/tmp/topolab-b22-failure-diagnosis.json` has SHA-256
`ae12e3e23e2ce2dee4d7f016b561a6879861d9d58d0bf5bbee0813c166bc6cb5`.
At update 120, the seven small cases had maximum design changes `0.014946`
or `0.015050`, maximum physical change over the last ten steps `0.006893`
or `0.007300`, and ten-step relative compliance improvements `0.000312`
or `0.000327`. The new large failure had values `0.014529`, `0.002497`, and
`0.000696`, respectively. Thus each failed the historical `0.01` design
maximum and the new policy's `0.0002` ten-step improvement bound; the
physical-change part alone was already below `0.01`. This identifies the
immediate stopping-condition gap but does not justify relaxing the policy
against these observed cases.

The historical M2 report's `(5,2)` training case ID contained one mistyped
character. This slice corrected the displayed ID after comparison to the
frozen catalog; no artifact, split, numerical outcome, or case count changed.

## Gate, limits, and next independent slice

**Gate B2.2 fails:** 53/61 is below the frozen 61/61 requirement. Resource
caps and provenance checks passed, but the 522-label materialization and
control/candidate fitting are blocked by data quality. The 12 B2.1 references
were a narrower sample and their pass cannot be generalized to all 522
planned cases. Even a passing sentinel would only justify attempting the
full 522-label data gate, not a learned speedup claim.

The next independent slice is **B2.3, bounded solver/data-feasibility
repair**. Diagnose the eight failed trajectories without changing this
report, commit one explicitly versioned numerical or iteration-budget
intervention and its independent acceptance test before execution, then
rerun all 61 fixed sentinel cases with new result identities. Preserve the
old default and B2.1 outputs, and rerun every future learned/uniform
comparison under the same selected policy. If the repaired sentinel passes,
full materialization remains a later independent slice; if it fails, record
that attempt and revise the hypothesis rather than hiding cases.

## Repository validation

Before the frozen runner commit: `uv sync --dev --locked` in offline cache,
Ruff, mypy on `src` and the runner, full pytest (**279 passed**), and diff
checks passed. The runner executed from a committed revision with a clean
tracked worktree. Result and diagnostic JSON remained outside Git.
