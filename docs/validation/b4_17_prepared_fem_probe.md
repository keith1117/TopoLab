# B4.17 bounded offline FEM phase-cost and setup-reuse probe

Date: 2026-10-05 (America/New_York).

**Numerical parity passed; prospective fit-cost feasibility failed.**
All eight canonical expanded-train cases, sixteen fixed synthetic states,
96 complete paired Torch forward/backward measurements, 96 phase intervals
and 256 new FEM solves were retained. No label/model bytes, optimized terminal
artifact, fit, optimizer, new reference, continuation, screen or final artifact
was opened. Fixed P/17 remains unrepaired; uniform stays default. All original
failures, charges, failed Gates, final evaluation and 48 unused B4.10 cases
remain unchanged/sealed. Next slice: **B4.18 bounded offline FEM bottleneck and training-objective method review**.

## Frozen source and complete input boundary

The [protocol](../planning/b4_17_prepared_fem_probe_protocol.md), optional
[prepared kernel](../../src/topolab/prepared_compliance.py), paired probe,
independent auditor and resource closer merged in [PR #133](https://github.com/keith1117/TopoLab/pull/133)
after all applicable exact-head CI passed. Tested head `730e524898d24b3e67c5b7286438f499458476bb`;
clean merged execution revision `8530c500993d8252f6c58f7b380f9655b91953cd`;
merge timestamp `2026-10-05T15:15:44Z`. Tested and merged trees match.
Production release binds 138 source/protocol/convention/runtime files.
Plan SHA-256: `4bf1897acb550947fe9723c83c8c39a2bd8a8fac1aa2fa09dec5b1ebf6426af4`.
Artifacts stay outside Git at `/Users/keith1117/Documents/TopoLab-data/b4-17-prepared-fem-probe`.
Execution uses locked Python, one BLAS/OpenMP thread and one Torch intra-op
CPU thread. The original query and B4.15 numerical sources are unchanged.

Twelve exact B4.16 bindings, complete native profiles, post-exit closure and
its retained controller-failure reservation passed before/after every process.
All B4.15/B4.14/B4.13/B4.12, historical/recovery and B3 index guards stayed
unchanged. Only the bound B4.15 synthetic-fixture JSON was reopened. The eight
normalizers remain previously certified constants; no label bytes or stored
optimized density artifact was reread. Exact canonical case/state/raw/normalizer
identity is checked before any new FEM. Normalizer solves remain prior evidence.

## One prepared candidate and independent numerical evidence

`topolab.prepared-offline-compliance.v1` owns read-only unit Hex8 stiffness,
COO row/column indices, free-DOF/load maps and physical-volume weights.
Each current prediction still computes fresh density-dependent coefficients,
COO/CSR summation, reduced CSC and numeric SuperLU factorization with the
unchanged A3 automatic ordering/pivot checks. No density, factorization, output
or cross-case cache is reused. Projection/filter/offset pullback and CPU Torch
first-order dtype semantics preserve B4.15. Reaction work remains fully paid.

Three paired repeats per fixture alternate prepared/original arm order:
even repeats prepared first, odd repeats original first. Every first
observation, tensor construction, forward/backward and gradient extraction
is retained. Recorded full wall also conservatively includes gradient-list
conversion before reading its stop clock. No warmup or slow value is dropped.
The sixteen additional instrumented NumPy evaluations measure six sequential
phases with outer/residual time retained; they do not replace the Torch timers.

The auditor does not call the prepared projection/FEM/pullback. It uses
uncached assembly, independent element energies, row-normalized filter and
Brent volume root for all sixteen central states; it reconstructs all 64
fixed-step differences and checks every original/prepared repeat loss/gradient.
Population, paired order, phase sums/residuals and setup/cost arithmetic are
independently checked. Frozen projection atol is 2e-11, compliance rtol 1e-9,
gradient rtol 1e-9/atol 1e-10, physical volume 1e-12 and shift sum 1e-10.
Differences keep steps 1e-4/2e-4, stable active sets and normalized error
<=1e-4 with 1e-8 denominator floor. No tolerance or scientific boundary changed.

| Evidence | Result |
|---|---:|
| Probe solves: 96 paired + 16 instrumented + 128 difference sides | 240 |
| Independent uncached central solves | 16 |
| Total new FEM solves | 256 |
| Independent numerical/gradient/difference conditions | 768 |
| Failed conditions | 0 |
| Fixed directional checks | 64 |
| Maximum normalized directional error | 0.000003326 |

| Case prefix / fixture | Prepared wall max | Original wall max | Prepared / original repeat gradient max difference | Directional error max |
|---|---:|---:|---:|---:|
| `0079bd9f` / interior | 0.135041583 | 0.010270292 | 0.000000000 / 0.000000000 | 0.000002746 |
| `0079bd9f` / clipped | 0.008079625 | 0.008576417 | 0.000000000 / 0.000000000 | 0.000000420 |
| `01504c9e` / interior | 0.008940375 | 0.008923833 | 0.000000000 / 0.000000000 | 0.000000515 |
| `01504c9e` / clipped | 0.008155875 | 0.008527666 | 0.000000000 / 0.000000000 | 0.000000160 |
| `03a2c406` / interior | 0.008218584 | 0.008698791 | 0.000000000 / 0.000000000 | 0.000000157 |
| `03a2c406` / clipped | 0.008094292 | 0.008553958 | 0.000000000 / 0.000000000 | 0.000000236 |
| `04ab9b94` / interior | 0.008201417 | 0.008647667 | 0.000000000 / 0.000000000 | 0.000000369 |
| `04ab9b94` / clipped | 0.012545750 | 0.011439917 | 0.000000000 / 0.000000000 | 0.000000603 |
| `0ca7ef4d` / interior | 0.172796667 | 0.207558375 | 0.000000000 / 0.000000000 | 0.000000213 |
| `0ca7ef4d` / clipped | 0.161456750 | 0.171137000 | 0.000000000 / 0.000000000 | 0.000002264 |
| `144d548f` / interior | 0.181372708 | 0.337907208 | 0.000000000 / 0.000000000 | 0.000000257 |
| `144d548f` / clipped | 0.166382333 | 0.171279375 | 0.000000000 / 0.000000000 | 0.000003326 |
| `02947490` / interior | 0.180847000 | 0.174302084 | 0.000000000 / 0.000000000 | 0.000002480 |
| `02947490` / clipped | 0.166915291 | 0.167527959 | 0.000000000 / 0.000000000 | 0.000001112 |
| `0ea4104d` / interior | 0.171261541 | 0.165015708 | 0.000000000 / 0.000000000 | 0.000000453 |
| `0ea4104d` / clipped | 0.163429084 | 0.172822500 | 0.000000000 / 0.000000000 | 0.000000887 |

These maximum repeat differences are reconstructed from all retained raw
gradients and stored here; no observation is replaced by this summary.

## Complete phase, setup and prospective cost

Each scale has eight instrumented states. Phase intervals include local timer
work and sum to complete NumPy outer time minus its retained residual.
They are diagnostic attribution within this fixed probe, not standalone
Torch timings, removable-cost guarantees or measured training savings.

| Phase (sum over eight states per scale) | Small wall | Small CPU | Large wall | Large CPU |
|---|---:|---:|---:|---:|
| projection_filter | 0.001139043 | 0.001140000 | 0.003450125 | 0.003452000 |
| assembly | 0.017432957 | 0.017395000 | 0.152899875 | 0.152726000 |
| reduction | 0.002364708 | 0.002366000 | 0.019097708 | 0.019084000 |
| factorization | 0.039900167 | 0.039894000 | 1.092382582 | 1.088342000 |
| solve_energy | 0.002926584 | 0.002925000 | 0.031530543 | 0.031512000 |
| pullback | 0.000345374 | 0.000348000 | 0.001176084 | 0.001175000 |
| Complete instrumented outer | 0.065683248 | 0.065621000 | 1.325896999 | 1.318909000 |

| Scale | Prepared paired wall sum | Original paired wall sum | Prepared CPU sum | Original CPU sum | Max prepared setup wall | Max retained array bytes |
|---|---:|---:|---:|---:|---:|---:|
| small | 0.328674834 | 0.211487788 | 0.251460000 | 0.210205000 | 0.005885791 | 2124292 |
| large | 4.008388624 | 4.259613961 | 3.984314000 | 4.146179000 | 0.116987333 | 18024604 |

In these eight large instrumented states, factorization plus pivot checks
accounts for 82.3882% of complete NumPy outer wall. Immutable setup reuse
does not remove this fresh numerical work. This is measured phase attribution
for these states, not a forecast of achievable training or query savings.

Both original and prepared case setup, all difference solves, audits, imports,
process startup/exit and publication are charged through complete native
profiles and fixed allowances. Paired sums describe this cohort only;
no statistical/learned/whole-workload acceleration claim follows.

The new prospective proxy preserves three seeds, 200 full epochs, 432 small
and 76 large cases per epoch, and factor 1.25. It uses all 24 prepared wall
observations per scale, including the first, and three full-population setup
charges using maximum prepared setup wall with the same factor. Add ALL twelve
B4.1 fits, previous B4.15/B4.16 charges and this complete probe cost.

| Frozen planning quantity | Seconds |
|---|---:|
| Maximum small prepared forward/backward | 0.135041583 |
| Maximum large prepared forward/backward | 0.181372708 |
| Additional physics, 304,800 objectives × fixed factor | 54091.717244941 |
| Full-population preparation, three seeds × fixed factor | 42.876371394 |
| Conservative all-twelve-fit baseline | 3870.204341 |
| Prior B4.15 / B4.16 charges | 84.33 / 55.99 |
| Complete new probe charge | 112.340000000 |
| Total new prospective fit proxy | 58257.457957335 |
| Frozen prospective cap | 7200 |

Cost feasibility fails. This is small-sample planning, not a measured full fit or a rigorous
all-case bound. B4.15's original 60339.394130 proxy and failed Gate remain
unchanged. Sequential RSS does not certify all training activations/optimizer
or preparation ownership. The maximum-array per-scale full-population estimate
is **2287564048 bytes**, excluding Python/SciPy object
overhead and future network/optimizer state. Full training memory remains pending.
Shared B3 data (5325.353116 seconds), all earlier development and all future
fit/screen/final/replication costs remain required in a full experiment ledger.

## Complete native resource closure and software checks

Probe/audit caps are 600 charged seconds each, whole cap 1260 seconds / 1 GiB.
The full 60-second metadata-plan/closure/controller reservation is paid.
All production commands exited zero; no failed attempt, retry or numerical
rerun occurred. Complete native wall/user/system CPU/RSS are retained.

| Process | Native wall | User CPU | System CPU | Native peak RSS bytes | Closed charge |
|---|---:|---:|---:|---:|---:|
| plan | 2.70 | 1.77 | 0.26 | 275906560 | within full 60-second reserve |
| probe | 26.26 | 23.08 | 2.17 | 403767296 | 36.260000000 |
| independent | 6.08 | 5.06 | 0.50 | 486866944 | 16.080000000 |
| closure | 3.98 | 2.92 | 0.36 | 313491456 | within full 60-second reserve |
| verification | 3.26 | 2.38 | 0.33 | 318685184 | within full 60-second reserve |

Closed charge is **112.340000000 seconds**, retained peak
**486866944 bytes**. Combined plan/closure/verification cost
is 39.940000000 <=60 seconds and their native peaks fit
the retained peak. The controller uses locked Python; all command/profile hashes
and independent final proxy arithmetic passed. The immutable ledger was not
rewritten. B4.15/B4.16 charges and all protected metadata remain unchanged.

Before source commit, locked dev sync, Ruff, mypy (66 files), all **906
tests in 479.12 seconds**, and working/staged whitespace checks passed.
Forty-eight new tests cover both scales, independent Brent/energy gradients,
fresh changing-density factors, immutable caches, dtype/kink/invalid/singular
boundaries, exact populations, failed-attempt charges and ordered stop rules.
Evidence publication repeats all required checks and merges only after its
own exact-head CI passes. No numerical source, convention or production receipt
is changed by evidence publication. Generated artifacts stay outside Git.
No upstream code or new external reference was used.
Before evidence commit, locked dev sync, Ruff, mypy (66 files), all **906
tests in 470.68 seconds**, and working/staged whitespace checks passed again.

| External receipt | SHA-256 |
|---|---|
| `audit_receipts/plan.json` | `7844801266232c5d7637628167fe27979319bde9eba5cfa8701481f3d574b7c7` |
| `audit_receipts/production_release.json` | `6ae265e7464293945220f7e395ca2a26655f88154d0253eca41537831c7c2889` |
| `audit_receipts/source_final_head_ci.json` | `61890b2b7ef2f9be76b26458da294d7c2330fd69a70885b4091169449c44c42b` |
| `probe.json` | `009478f60ba859c2ed4ad6072e09efe9d6a296650c73acc1cc31686e8cc4491b` |
| `independent_audit.json` | `ed1c8e4c7946639ca535094b26b707cbef75850f708d83c347e46c4872e3b413` |
| `resource_close.json` | `83c211164fffd693256d611f926f1128d8f0938174ea3bdee1ef6faf4bfbdf2d` |
| `audit_receipts/execution_commands.json` | `a081f939cffc5bc6dcdabd2688afe14e1552538959971d2aa5a616035d4af529` |
| `audit_receipts/plan_command.json` | `89194bc5d1bc94d4ea0e4b1fe13ce2d92b5fa75709033688a904a843521f371b` |
| `audit_receipts/closure_command.json` | `fb02ee086b461601f4e971a7ed8c9c37bb1cc1654bf01fd45972707870073647` |
| `audit_receipts/closure_profile_verification.json` | `65b9123f275ac6b370deb395187a43c1c14d3a8551d39f1f2653a6a14993244e` |
| `audit_receipts/postexit_command.json` | `6a24b176e75896595a407ed8ca2e686a1d4b584ae3d2e8902675f7225fe526ab` |
| `audit_receipts/postexit_controller_reservation.json` | `0fcd8a93abd37cd020eac9641b6e3f6b9a0edad23b0df1ef4da46d76a5ee9899` |

The frozen ordered decision selects **B4.18 bounded offline FEM bottleneck and training-objective method review**. It has not started.
No fit, second caching candidate, epoch/population/physics-frequency search,
new seed, continuation or fresh cohort follows automatically. A passing learned
repair and independent confirmation, then a compatible final contract and
later Gates, remain required before B5. Report the next slice and stop.
