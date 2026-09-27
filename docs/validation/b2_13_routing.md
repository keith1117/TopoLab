# B2.13 workload routing and safe-rejection development screen

Date: 2026-09-27 (America/New_York)

Status: **The frozen B2.13 development feasibility Gate passed.** All twelve
fresh uniform references passed, and all 144 outcomes on twelve new cases
were retained and independently audited. The single routed policy met both
scale and all four direction-wise, fully charged time limits with zero
accepted quality violations. This is a small **development** screen, not
final learned-acceleration evidence. Uniform remains the operational default;
a larger, separately frozen development confirmation is required before B3.

## Frozen policy and provenance

The [B2.13 protocol](../planning/b2_13_routing_protocol.md) and
[numerical convention](../numerical_conventions.md) fixed one metadata-only
policy before execution. Small y and large z use the unchanged B2.9 vector
seed 29; small z uses B2.12 context seed 17; large y below volume `0.55`
uses B2.12 context seed 43; large y at or above `0.55` rejects to a fresh
uniform solve. Out-of-workload metadata also rejects. The unchanged vector
input, filtered-volume projection, 360-update physical-plateau solver,
independent quality decision, and full failed-attempt fallback apply to every
selected model. No model was trained or selected in this slice. Checkpoint
loading is reported separately from query time.

The canonical plan SHA-256 was
`8be542da851cdb6e45325ddd94a3cde8cf6867df8d13a2d4c6b49f484a9d9d37`;
the saved plan-file SHA-256 was
`e5063bd21b9da336541d2a644d0bade829d68ee576bf8fbfdc7f59704a4f468a`.
The clean tracked execution revision was
`2fc0e44ce8f48087dcbac54d8d5e47bc7e26f092`. The fixed B2.9 and B2.12
fit-index SHA-256 values were
`96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`
and `0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce`.
All six old selections/checkpoints and the B2.5 control were checksum
checked before screening. The exposed B2.12 screen index matched its
frozen SHA-256. Generated plans, indices, logs, and the independent audit
script stayed outside Git.

The new screen crossed volumes `0.3075,0.4575,0.6075`, y/z point loads,
and `(12,6,3)`/`(24,12,6)` meshes. The small-mesh load node was
`(x=max,y=5,z=1)` with its physically doubled large-mesh counterpart.
All twelve case IDs and all three volumes were disjoint from the 576-case
development exposure ledger and the design-exposed final volume definitions.
M2 test/OOD and any new final label or outcome remained sealed.

Execution used the locked Python 3.12.10 environment on Apple arm64/macOS,
with single-thread CPU/BLAS/OMP settings. The `uv.lock` SHA-256 was
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.

## Reference and complete screen

Before model loading, **12/12** fresh uniform references passed convergence,
positive finite compliance, independent final-state quality, and physical
volume error `<=0.005`. They stopped at updates **31–108**, below both the
historical 240 and the current 360 caps. The reference stage took **99.09 s**
against 1,800 s and peaked at **378,273,792 bytes** against 2 GiB. Its
index SHA-256 was
`9c43f2bff96c6c2f4b853b676bd980e659e4f966088b01d9df9b18c10897ed64`.
The screen then ran a *new* uniform for each paired time denominator.

Every case received fresh uniform, physics heuristic, B2.4 train-only
nearest neighbor, B2.5 MSE control 43, three unchanged B2.9 vector models,
three unchanged B2.12 context models, the one routed policy, and an
impossible exact own-trajectory oracle. All **144 outcomes** were retained.
The arithmetic mean of the complete paired time ratios was:

| Method | Small mean | Large mean | Failed attempts / 12 |
|---|---:|---:|---:|
| Uniform | 1.000 | 1.000 | 0 |
| Physics heuristic | 1.314 | 1.055 | 1 |
| Nearest neighbor | 0.341 | 3.010 | 3 |
| B2.5 control 43 | 0.964 | 1.687 | 1 |
| B2.9 vector 17 | 0.689 | 0.796 | 0 |
| B2.9 vector 29 | 0.675 | 0.735 | 0 |
| B2.9 vector 43 | 0.594 | 0.825 | 0 |
| B2.12 context 17 | 0.563 | 0.916 | 1 |
| B2.12 context 29 | 0.606 | 0.781 | 0 |
| B2.12 context 43 | 0.536 | 0.668 | 0 |
| **B2.13 routed policy** | **0.635** | **0.723** | **0** |
| Exact own-trajectory oracle, impossible | 0.376 | 0.658 | 0 |

The routed policy's direction means were **0.714 small-y**, **0.555
small-z**, **0.826 large-y**, and **0.619 large-z**. Thus both scale means
were `<=0.90` and all four direction means were `<=1.0`, as frozen. Its
eleven selected learned attempts passed quality without fallback. The one
large-y/0.6075 case was rejected *before inference* and charged a fresh
uniform solve. Its ratio was 0.991 on this paired timing run; it was not
counted as a learned failure. All operational results met physical-volume
error `<=0.005` and final compliance `<=1.001` times the matched uniform;
there were **zero accepted quality violations**.

| Scale | Direction | Volume | Route | Routed paired ratio |
|---|---|---:|---|---:|
| large | z | 0.4575 | vector 29 | 0.738 |
| small | z | 0.4575 | context 17 | 0.745 |
| large | y | 0.6075 | reject to uniform | 0.991 |
| small | z | 0.6075 | context 17 | 0.347 |
| small | z | 0.3075 | context 17 | 0.572 |
| large | y | 0.4575 | context 43 | 0.612 |
| large | z | 0.6075 | vector 29 | 0.515 |
| small | y | 0.4575 | vector 29 | 0.743 |
| large | y | 0.3075 | context 43 | 0.875 |
| small | y | 0.3075 | vector 29 | 0.636 |
| large | z | 0.3075 | vector 29 | 0.604 |
| small | y | 0.6075 | vector 29 | 0.764 |

The routed policy's charged phase sums were 0.024 s setup, 0.593 s
projection, 53.224 s refinement, 0.934 s decision including quality
checks, and 17.047 s rejected-uniform work; **71.821 s total**. It had
zero failed-attempt fallback time. The gate uses the mean of *paired
per-case* ratios, not this total-time ratio. One-time model loading took
0.038 s; training-only neighbor indexing took 6.101 s and 6,877,512
bytes. The impossible oracle's own-case target generation took 35.489 s
separately. Previous B2.6 target generation (376.86 s), B2.9 fitting
(169.53 s), and B2.12 fitting (331.65 s) remain offline costs; none were
hidden in B2.13 query timing.

The full screen took **1,318.83 s** against 14,400 s and peaked at
**380,485,632 bytes** against 2 GiB. The screen-index SHA-256 was
`183e3448a9d7e3e82de6ed4dd3f38e5184977b7243aa9edd13284f950f8d3de0`;
the summary-file SHA-256 was
`5ba5687e799389fd70ad5640ecf23461d428a636fd41e5209538c68bac2a3324`.

## Independent audit and next decision

A separate standard-library audit recomputed the canonical plan and
exposure checks; source fit/screen index digests; all selected checkpoint
and selection checksums and earliest validation minima; twelve reference
identities and quality results; all twelve unique new strata; 144 ordered
outcomes; chosen route and routed-versus-fixed-model numerical equivalence;
rejection and fallback semantics; phase sums, paired ratios, per-scale and
direction means, resource caps, and the frozen Gate. It reproduced a
**passing B2.13 development Gate**.

The fresh cohort also favored some *single* models: B2.9 vector 29 and
B2.12 context 29/43 each met the same descriptive scale/direction limits,
and context 43 was faster than the router at both scales on these twelve
cases. The conservative high-volume y rejection avoided an exposed B2.12
quality failure, but on this fresh high-volume y case context 43 would
have passed quality. Therefore this screen establishes a feasible
quality-preserving prototype, **not** that routing is superior to the
simpler fixed context-43 model or that rejection is always needed.

The next independently started slice should freeze a **larger, physically
disjoint development confirmation** with the router and fixed single-model
comparators and a selection rule before observing its outcomes. Do not
freeze B3's final ML contract, open final evidence, change the operational
uniform default, or claim acceleration from this B2.13 screen alone.

## Repository validation

Before the clean-revision run, `uv sync --dev --locked`, Ruff, mypy on
`src`, focused mypy on the runner, all **320 Python tests**, and
`git diff --check` passed. Generated experiment and audit artifacts remain
outside Git. The required repository checks are repeated before committing
this validation report.
