# B4.5 sensitivity-weighted terminal generalist

Evidence date: 2026-10-02 (America/New_York); protocol frozen 2026-10-01.

Status: **complete; bounded development Gate passed** with W/17 and W/43.
All three fits, 48 references, 576 outcomes and independent artifact/numerical/
arithmetic/resource audits closed. W/17 is the prospective development primary;
W/29 failed reliability and remains retained. Uniform remains the operational
default; B5 final evidence remains sealed pending independent confirmation and
the complete new B4 Gate. This is not a final end-to-end acceleration claim.

## Frozen source and single intervention

The [finite protocol](../planning/b4_5_weighted_terminal_protocol.md), runner,
versioned artifact boundary and tests were first committed at
`243c0919cfe02376ea50f181a150d5dcc5a174fb`. PR
[#109](https://github.com/keith1117/TopoLab/pull/109) passed both quality checks,
frontend checks and the required clean Linux smoke before merging. Production
uses clean merged revision `ed1acd4aa60fba62607874f6c888663747c1c595` in a separate
checkout, with the unchanged numerical anchor, lockfile and one-thread Apple M2
runtime. The user's two untracked workspace files remain untouched.

Identity: `topolab.b4_5.weighted-terminal.v1`. The sole learning change is an
element-weighted terminal-design objective: each case's squared prediction error
is multiplied by its existing audited float32 sensitivity weights before taking
the case mean. Those weights use the mean-normalized absolute design-compliance
derivative, clipped to [0.25,4] and renormalized to mean one. P's fixed case
weights remain 8 for y at volume >=0.5 and 1 otherwise, on the exact 508 train
and 32 fit-validation labels. No new label or inference-time feature is added.

Thirteen-channel vector input, 26,433-parameter context CNN, terminal **design**
targets, CPU float32, AdamW, shape buckets, batch size 8, seeds 17/29/43,
200-epoch limit and patience 25 are unchanged. Selection is the earliest strict
minimum unweighted equal-case MSE over all 32 fit-validation cases. The new W
checkpoint/selection wrappers bind the new objective and source. Same-seed fixed
S remains the route on large-grid y at volume >=0.55; C/P controls are unchanged.

All cases retain the original 360-update physical-plateau solver, projection,
A3 ordering, compliance re-solve rtol=1e-9, physical-volume error <=0.005 and
terminal compliance <=1.001 times matched uniform. No tolerance changed.
Historical B4.2 failures, costs and permanent integrity flag remain unchanged.
The old three P failures were not rerun or relabelled by this new experiment.

## Fixed fitting outcomes

| Seed | Retained / attempted epochs | Selected epoch | W selection MSE | Matched old P MSE | Fit-loop seconds |
|---|---:|---:|---:|---:|---:|
| 17 | 118 / 118 | 93 | 0.025851757 | 0.018779806 | 101.277818 |
| 29 | 181 / 181 | 156 | 0.019613444 | 0.018037449 | 150.772628 |
| 43 | 167 / 167 | 142 | 0.020439929 | 0.016658671 | 142.237285 |

All three new fits completed with 466 attempted epochs, below the frozen 600
cap, and no repeated fit or production restart. Unweighted validation MSE is
higher than matched P for every seed. Operational quality and charged time are
assessed on the full frozen new screen, independently of that image metric.

## Fresh development population and complete timing

The frozen 48-case Cartesian product uses volumes 0.3317, 0.4657, 0.5397,
0.5977; small-grid load positions (y,z)=(1,2),(3,1),(5,2), doubled on the large
grid; y/z directions; and (12,6,3)/(24,12,6) meshes. Budget-insensitive physical
fingerprints are disjoint from all 1,376 historical exposures and all 752 B3
catalog definitions, including sealed final definitions. Only final metadata is
compared; final artifacts are never accessed.

All **48/48 mandatory uniform references passed** before screening. The fixed
screen retains twelve methods for each case: timed uniform, physics heuristic,
complete 528-train-label nearest neighbor, and all C/P/W seeds. Uniform runs
first; the other eleven rotate by the frozen case-derived hash. Each method
uses the same inclusive wall/process-CPU envelope, compact five-second heartbeat,
terminal witness packaging, and fully charged fresh uniform fallback on failure.

Charged query ratios are `(outer query wall + 1 second) / (matched uniform outer
wall + 1 second)`. Every method pays the same recording allowance. Actual durable
pending, result/unit publication and completion receipt cost must stay below that
allowance. The resource ledger pays the full allowance before each attempt in
addition to all actual elapsed wall. Callback and fallback time are retained
inside query wall; setup, labels, reference generation, full independent audits
and resource closure remain additional charged stage work.

## Development results and independent audit

All 576 outcomes, the 626-unit production audit, separately derived arithmetic/
status audit and final resource closure passed.
Each table entry is the arithmetic mean of the per-case charged ratio, uniform=1.
Scale means use 24 cases and direction means use 12. All methods, seeds and
fully paid failures remain in the denominator.

| Method | Small | Large | Small y | Small z | Large y | Large z | Overall | Failures / fallbacks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| uniform | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 0 / 0 |
| physics heuristic | 1.063515 | 1.024763 | 1.074666 | 1.052364 | 0.992818 | 1.056708 | 1.044139 | 1 / 1 |
| nearest neighbor | 0.874542 | 1.638527 | 0.936117 | 0.812967 | 1.308655 | 1.968399 | 1.256535 | 8 / 8 |
| C/17 | 0.911683 | 0.979781 | 0.801157 | 1.022208 | 1.085171 | 0.874392 | 0.945732 | 3 / 3 |
| C/29 | 0.847476 | 0.814183 | 0.769369 | 0.925584 | 0.968630 | 0.659737 | 0.830830 | 1 / 1 |
| C/43 | 0.911667 | 0.927908 | 0.862228 | 0.961107 | 1.031109 | 0.824708 | 0.919788 | 1 / 1 |
| P/17 | 0.845459 | 0.720707 | 0.814910 | 0.876008 | 0.837355 | 0.604058 | 0.783083 | 1 / 1 |
| P/29 | 0.852498 | 0.799245 | 0.803903 | 0.901093 | 0.844819 | 0.753670 | 0.825871 | 2 / 2 |
| P/43 | 0.817851 | 0.660863 | 0.806538 | 0.829163 | 0.700021 | 0.621705 | 0.739357 | 1 / 1 |
| W/17 | 0.855946 | 0.667218 | 0.819538 | 0.892354 | 0.686527 | 0.647908 | 0.761582 | 0 / 0 |
| W/29 | 0.870151 | 0.741707 | 0.873905 | 0.866397 | 0.795485 | 0.687930 | 0.805929 | 2 / 2 |
| W/43 | 0.872024 | 0.646105 | 0.919112 | 0.824935 | 0.663346 | 0.628864 | 0.759064 | 0 / 0 |

W/17 and W/43 satisfy both <=0.90 scale bounds, all four <=1.0 direction bounds,
zero failure/fallback requirements, matched C/P reliability comparisons and both
non-ML comparisons. W/29 meets the speed bounds but fails reliability: its two
failures and two non-specialist-y failures exceed matched C/29's one. It remains
ineligible and is retained in every table.

The pooled middle-volume and high-volume large-y W cells both passed **9/9**,
above the frozen 6/9 thresholds. The high-volume cell uses the unchanged S
specialist and does not isolate the weighted generalist's effect.
Both W/17 and W/43 are prospective development-primary eligible. W/17 improves
over P/17 in both overall charged mean and failure count. W/43's overall mean
is slower than P/43's, but its zero failures improve over P/43's one, as permitted
by the frozen rule. **W/17 is selected as the development primary** because its
worst scale mean, 0.855946, is lower than W/43's 0.872024; the rule does not select
by overall mean alone. This is a development choice, without a final freeze.

All **20 failed candidates** paid successful fresh uniform fallback: C=5, P=4,
W=2, nearest neighbor=8 and physics heuristic=1. Seventeen failures converged but
exceeded terminal compliance; three nearest-neighbor failures reached 360 updates
without convergence. No failed attempt was removed, relabelled or given more
updates. All 576 operational outcomes passed unchanged terminal quality.

The two W/29 failures both converged on large-grid y at volume 0.4657:

| Full case ID | Load node | Updates | Compliance / uniform | Frozen limit |
|---|---:|---:|---:|---:|
| `tlcase-v1-6f9e7a071c7ec4acaa513b918064801b8a1f5033b899e87df7aba7de37de710e` | 1374 | 71 | 1.001253448 | 1.001 |
| `tlcase-v1-dde15fbfea4ddc0ef7380bdf7e8984ceb8dea6d01d4c4a049b4063975c8f2fcb` | 1574 | 59 | 1.001199772 | 1.001 |

The complete failure records retain witnesses and fallback times externally.
W/17 and W/43 have zero failures on this new panel; this does not erase the three
historical P failures or establish that the new models pass those old cases.

The first full audit independently re-solves all label targets/sensitivity fields,
reproduces selected-model MSE and checks all references and screen witnesses.
The separate external audit verifies clean source, exact 540-label membership,
canonical checksums, checkpoint headers/histories and separately batched unweighted
MSE. It reconstructs the counterbalanced assignments and all means, reliability
counts, eligibility, quality cells and primary choice without calling the
production `development_gate` or `validation_mse` helpers. Its arithmetic agrees
at rtol=1e-14, integer decisions agree exactly, and all three MSE values reproduce
exactly. It independently checks each accepted/failed status from the unchanged
quality rule, including the failed attempts: **644/644 terminal states**
(48 mandatory references + 576 candidates + 20 fallbacks) passed witness/status
audits. Shared provenance readers and the independent FEM witness solver remain
the original tested numerical boundary.

## Resource closure and evidence identities

Generated evidence remains external at
`/Users/keith1117/Documents/TopoLab-data/b4-5-weighted-terminal`.
The context SHA is
`0454eee24c1c72c051f10dce0162f0f41d5a5ade1fb3a4e5b42c9c82c9d11071`;
the metadata-only plan SHA is
`b4c620b4e1ee7e0814ed562979c10e00af8e2f3e3ce3dcc11d3ab5d9d6728b5b`.
The protocol SHA is
`d0ee69cb579b36dac23b7e288d40d21d085d0306b68de6a97482c1aa9f76ab93`.
The unchanged upstream B3 data index and B4.1 fit index are bound in that context
and in the protocol.

| Stage | Complete units | Final charged seconds / cap | Peak RSS bytes / cap |
|---|---:|---:|---:|
| Fitting | 3 / 3 | 529.773028 / 3,600 | 376,160,256 / 4,294,967,296 |
| Mandatory references | 48 / 48 | 504.059403 / 3,600 | 394,936,320 / 2,147,483,648 |
| Development screen | 576 / 576 | 5,790.063358 / 21,600 | 359,956,480 / 2,147,483,648 |
| Full audits and resource closure | 626 / 626 | 754.289102 / 3,600 | 453,132,288 / 2,147,483,648 |
| **Total new experiment** | | **7,578.184891 / 32,400** | **453,132,288 maximum** |

Attempted and completed unit counts match for every stage. There was no production
restart, missing recording receipt or permanent integrity/resource failure.
All ledgers are closed without pending work. The 466 attempted epochs include
every retained epoch and stayed below 600. The six new model/selection files total
363,724 bytes; the 48 reference blobs total 21,509,803 bytes and the 576 screen
blobs total 270,264,463 bytes. Generated artifacts remain outside Git.

The three fit loops sum to 394.287731 seconds, leaving **135.485297 seconds** for
label/model setup, publication/checks and closure. Mandatory-reference outer wall
is 436.270409 seconds plus 48 recording-allowance seconds, leaving **19.788995
seconds** additional stage work. Screening outer wall is **5,009.025836 seconds**
plus 576 allowance seconds, leaving **205.037522 seconds** for model/NN setup,
live independent terminal audits, actual recording and closure. Query process CPU
is 4,780.591764 seconds; legacy phase sums are 5,007.938225 seconds, retained
separately. Inclusive callback wall/CPU are 6.689964 / 2.580569 seconds and callback
writes total 395,378 bytes. No callback or fallback cost was subtracted.

Measured screen recording before its small completion receipt sums to 9.617172
seconds. The largest pre-receipt recording among all 624 numerical queries is
0.200705 seconds. Every live combined pending/publication/receipt check stayed
within the one-second allowance, or the runner would have permanently failed the
Gate. The resource ledger pays all 624 allowance seconds in addition to actual
elapsed work. These conservatively bounded costs are not historical retiming.

The first full audit charged 440.115445 seconds. The supplemental complete audit
raised the audit ledger to 736.770163 seconds; closure and its reserved allowance
raised it to 754.289102. Whole-command floors are fit=521.67, reference=448.21,
screen=5,206.34, combined audits=719.77 and closure=2.87 seconds, totaling
**6,898.86 seconds**, below the final charge. No profile-floor deficit was dropped.
Resource closure also independently verified the exact unchanged B3 data index,
B4.1 fit index, failed B4.2 screen index and final B4.4 progress hash. The original
failed Gate, costs and permanent marker remain retained; no final bytes were read.

| Evidence | SHA-256 |
|---|---|
| Immutable fit summary | `513064fe615456fe8204b511f850a71150895038c3541ad23f5cd35642b0cc6c` |
| Immutable reference summary | `86db0bf3bb16dd28914d5a5fce043b073f563f19879b3750df0258b01f5aad9a` |
| Immutable screen summary | `d835c7e3aa88c080c3e1c52f2e8ec02d14fb2470f5b81e88c2b8ad54fb3e9f4b` |
| Complete screen-chain head | `cd32ef13a52fa1d53889197951e9bb9e9d19c73077c0ae2b619407d04a88eb59` |
| Immutable production audit summary | `1cf0ba874536cd58a05145c63ecf29474cc813a63dc8734696baea0abbb92100` |
| Independent complete audit | `5ab85296186739f61a4d94a0a8645199f9fdd935cadfdd447036bd31287997d5` |
| Independent audit source | `e792a51e2c6f63a7c19a990a4653214d6d90c7e2c91b76ee3241414098702390` |
| Resource closure | `9dff4ba3334ba623fcc6f43db3a790f5135de2d370feefb66a5d49fdab7a3c1f` |
| Resource-closure source | `908d1215ddd9019a196f9f986ab8d302c8afef5b3c1fd147291184c13e3afa62` |
| Final charged audit progress | `9814b82a518a525526259e47cf45e3524db58e6e3e8759b30504e21909cc1940` |

External `audit_receipts` retain the metadata plan, complete logs/profiles and
independent source scripts. Immutable summaries keep their original stage charges;
final progress includes supplemental audit and closure without rewriting outcomes.

## Required validation and next slice

Fifteen focused tests cover the objective's arithmetic and gradient, unit-weight
equivalence with the original fit path and RNG restoration, invalid weights,
complete membership before label/model bytes, physical exposure disjointness,
source-bound checkpoint corruption rejection, charged journals, complete Gate
denominators and retained ineligible seeds, recording receipts, the epoch cap
before an update, metadata-only planning, and durable recording-allowance charges
before a solver call. These tests use synthetic inputs; the production cohort is
retained separately.

Before implementation commit, locked sync, Ruff, mypy (56 source files) and
diff checks passed. The full suite collected before two final tests were added
passed 672 tests in 441.53 seconds; the final focused 15-test file then passed
in 2.17 seconds, covering those two additions and its preceding thirteen tests.
Both current implementation quality CI checks ran the complete 674-test suite
and passed in 13m36s / 10m18s. Frontend and required Linux smoke also passed
before merge.

Before the evidence commit, locked sync, Ruff, mypy (56 source files), all
**674 tests in 427.40 seconds** and diff checks passed again. The evidence PR
follows the same required-CI-before-merge rule.

The actual passing branch of the frozen disposition permits **B4.6: separately
freeze a larger, physically disjoint development confirmation using unchanged
W/17/29/43 checkpoints, the same S route, quality limits and complete timing**.
Retain every seed and comparator, including W/29; do not tune on the exposed
48-case panel or replace the primary using confirmation results. This slice has
one development cohort and two passing seeds; it does not establish independent
replication, final ID/OOD performance or amortized end-to-end acceleration.
Independent confirmation and the complete new B4 Gate remain required before B5.
Report this slice and wait for a new instruction before starting B4.6.
