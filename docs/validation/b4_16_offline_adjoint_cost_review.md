# B4.16 bounded offline adjoint cost-feasibility review

Date: 2026-10-05 (America/New_York).

**Read-only review acceptance passed; B4.15's prospective cost Gate remains failed.**
All eight cases, sixteen synthetic fixtures and 48 wall/CPU observations,
including the first, were retained and independently reconstructed.
No new FEM solve, benchmark, label/model artifact read, fit, optimized
terminal-state read, reference, continuation or screen/final access occurred.
Fixed P/17 remains unrepaired. Uniform stays default, final evaluation and
all 48 unused B4.10 cases stay sealed. Next slice: **B4.17 bounded offline FEM phase-cost and setup-reuse feasibility probe**.

## Frozen execution and complete boundary

The [protocol](../planning/b4_16_offline_adjoint_cost_review_protocol.md),
review, separate auditor and native resource closer merged in
[PR #131](https://github.com/keith1117/TopoLab/pull/131)
after all applicable exact-head CI passed. Tested source head
`c85e695fd2d4576753e4e1075ee9a459ad6f49ba`; clean merged execution revision
`8fee3345f090b652ab1633bc279a5d5b7ee8f10e`; merge timestamp `2026-10-05T07:04:35Z`.
Tested and merged trees match. Production release binds
134 source/protocol/convention/runtime files.
Plan SHA-256: `c06a072badbc8b297aeff8d35e7ac09723cc1b47fe7dac1fe04dc1079ab8667b`.
Artifacts are external at
`/Users/keith1117/Documents/TopoLab-data/b4-16-offline-adjoint-cost-review`.

Ten exact B4.15 metadata bindings, the complete probe hash, native profiles
and closure proof passed before/after every process. B4.14/B4.13/B4.12,
historical/recovery guards and the complete B3 index remain unchanged.
Only B4.15's synthetic-fixture JSON was opened for its identity/setup/timing
scalars; contained fixture density vectors were not numerically analyzed.
No training artifact bytes were reopened. B4.15's 64 directional checks,
408 numerical conditions and 200 FEM solves remain prior evidence, not
new numerical validation in this slice.

The separate auditor calls no review distribution/proxy arithmetic. It
rebuilds all observation identities, descriptions, scenarios and budget
requirements from bound raw JSON, then separately parses native CPU/wall/RSS.
All **818 arithmetic/identity/boundary conditions** passed
at frozen rtol/atol `1e-12`. No numerical convention or quality tolerance changed.

## All retained timing evidence

Per-scale values below use every one of 24 prepared forward/backward
observations, with no warmup exclusion. CPU is process CPU; wall-minus-CPU
is signed and is not a measured causal initialization or scheduling cost.

| Scale / timer | Min seconds | Median seconds | Mean seconds | Max seconds | Sum seconds |
|---|---:|---:|---:|---:|---:|
| small / wall_seconds | 0.008340959 | 0.008740105 | 0.014302880 | 0.138534458 | 0.343269127 |
| small / cpu_seconds | 0.008341000 | 0.008740500 | 0.011183750 | 0.064008000 | 0.268410000 |
| small / wall_minus_cpu_seconds | -0.000001583 | 0.000000042 | 0.003119130 | 0.074526458 | 0.074859127 |
| large / wall_seconds | 0.164405875 | 0.168902646 | 0.173971238 | 0.201749042 | 4.175309707 |
| large / cpu_seconds | 0.164372000 | 0.167847500 | 0.171914542 | 0.193210000 | 4.125949000 |
| large / wall_minus_cpu_seconds | 0.000033875 | 0.001069583 | 0.002056696 | 0.011686042 | 0.049360707 |

| Repeat position (zero-based, 16 observations each) | Wall min | Wall median | Wall mean | Wall max | CPU sum |
|---|---:|---:|---:|---:|---:|
| 0 | 0.008613167 | 0.152266125 | 0.101623451 | 0.201749042 | 1.527264000 |
| 1 | 0.008340959 | 0.086931396 | 0.091970839 | 0.198163917 | 1.454851000 |
| 2 | 0.008356916 | 0.087263896 | 0.088816888 | 0.179992417 | 1.412244000 |

| Case prefix / fixture (three observations each) | Wall min | Wall median | Wall max | CPU min | CPU max |
|---|---:|---:|---:|---:|---:|
| `0079bd9f` / clipped | 0.008503375 | 0.008592584 | 0.008613167 | 0.008501000 | 0.008613000 |
| `0079bd9f` / interior | 0.008744125 | 0.009212417 | 0.138534458 | 0.008744000 | 0.064008000 |
| `01504c9e` / clipped | 0.008340959 | 0.008356916 | 0.008645208 | 0.008341000 | 0.008642000 |
| `01504c9e` / interior | 0.009028000 | 0.009064334 | 0.009563375 | 0.009029000 | 0.009304000 |
| `02947490` / clipped | 0.166641583 | 0.167370083 | 0.168525750 | 0.166152000 | 0.167523000 |
| `02947490` / interior | 0.175513291 | 0.179992417 | 0.201749042 | 0.173489000 | 0.190063000 |
| `03a2c406` / clipped | 0.008660166 | 0.008721542 | 0.009329333 | 0.008661000 | 0.009322000 |
| `03a2c406` / interior | 0.008523833 | 0.008736084 | 0.009148125 | 0.008524000 | 0.009145000 |
| `04ab9b94` / clipped | 0.008642084 | 0.008830167 | 0.009490208 | 0.008643000 | 0.009433000 |
| `04ab9b94` / interior | 0.008702500 | 0.009456917 | 0.009829250 | 0.008704000 | 0.009827000 |
| `0ca7ef4d` / clipped | 0.167055458 | 0.179792416 | 0.186878667 | 0.166121000 | 0.184215000 |
| `0ca7ef4d` / interior | 0.166375083 | 0.166743375 | 0.172008167 | 0.165585000 | 0.171543000 |
| `0ea4104d` / clipped | 0.167877958 | 0.181047708 | 0.198163917 | 0.167830000 | 0.193210000 |
| `0ea4104d` / interior | 0.164964417 | 0.166763791 | 0.181144125 | 0.164867000 | 0.174772000 |
| `144d548f` / clipped | 0.164405875 | 0.165997792 | 0.167153250 | 0.164372000 | 0.166236000 |
| `144d548f` / interior | 0.169279542 | 0.174229333 | 0.175636667 | 0.167865000 | 0.174402000 |

Complete setup wall/CPU sums remain 3.349470918/
3.289321000 seconds. The first small observation is
retained in the original maximum and complete descriptions. Neither its
cause nor any removable portion is identified by these records.

| Prior B4.15 process | Native wall | User CPU | System CPU | Peak RSS bytes |
|---|---:|---:|---:|---:|
| closure | 4.01 | 2.73 | 0.40 | 300679168 |
| independent | 10.49 | 8.73 | 0.86 | 434962432 |
| probe | 23.84 | 21.27 | 1.84 | 510836736 |

There are no retained phase timers for projection, element stiffness,
assembly, numeric factorization, solve or Torch initialization. These
complete process records cannot establish which component dominates.

## Unchanged failed proxy and diagnostic requirements

Keep exactly three seeds, 200 full epochs, 432 small plus 76 large cases per
epoch, factor 1.25, ALL twelve B4.1 fits' 3,870.204341-second baseline and
B4.15's complete 84.33-second charge. This is 304,800 physics objectives.
The first row reproduces the frozen maximum-wall planning proxy. All other
rows are predeclared **diagnostic-only** arithmetic on observed samples:
no revised Gate, actual fit, rigorous timing lower bound or generalization
claim follows. Even observed minima need not bound a future optimized method.

| Scenario | Small unit seconds | Large unit seconds | Physics small seconds | Physics large seconds | Total including fixed costs |
|---|---:|---:|---:|---:|---:|
| original_maximum | 0.138534458 | 0.201749042 | 44885.164394 | 11499.695395 | 60339.394130 |
| wall_minimum | 0.008340959 | 0.164405875 | 2702.470744 | 9371.134870 | 16028.139955 |
| wall_median | 0.008740105 | 0.168902646 | 2831.793859 | 9627.450818 | 16413.779018 |
| cpu_minimum | 0.008341000 | 0.164372000 | 2702.484000 | 9369.204000 | 16026.222341 |
| zero_small | 0.000000000 | 0.164405875 | 0.000000 | 9371.134870 | 13325.669211 |

The original proxy remains **60339.394130 seconds
versus 7,200**. With small physics hypothetically free, observed minimum large
wall still gives **13325.669211 seconds** including
fixed costs. Thus replacing only the small first observation with cheaper
arithmetic cannot establish budget feasibility on this retained evidence.
This does not prove an optimized large FEM objective cannot be faster.

| Conditional requirement under unchanged B4.15 fixed costs | Value |
|---|---:|
| Available additional physics budget, seconds | 3245.465659 |
| Population-weighted unit-cost target, seconds | 0.008518283 |
| Small-only ceiling with large cost free, seconds | 0.010016869 |
| Large-only ceiling with small cost free, seconds | 0.056937994 |
| Required common speed factor relative to original maxima | 17.373427 |
| Required fractional physics-cost reduction | 0.942440831 |

The two isolated ceilings cannot both be spent simultaneously. This slice's
new 55.99-second charge is additional and is not substituted
into B4.15's immutable proxy. A future full ledger must also retain shared
B3 data (5,325.353116 seconds), prior development/selection costs and future
fit, screen, inference/refinement, final and replication charges. Neither a
sequential RSS nor this arithmetic certifies full training memory or
end-to-end acceleration. No epoch/population reduction, physics-frequency
search or post-hoc replacement of the failed cost Gate occurred.

## Static method disposition and next slice

Our bound source recomputes a unit Hex8 matrix, sparse assembly indices,
free-DOF maps and projection weights despite immutable case geometry/filter.
These are candidates for reuse. Numeric stiffness coefficients and sparse
factorization depend on each current prediction and must remain fresh.
No measured saving can be attributed to these components from B4.15.
Caching feasibility, numerical/gradient identity and its setup/memory charge
require a new prospective probe; changing solver ordering, sharing an obsolete
factorization or relaxing residual/quality checks is not justified.

The frozen ordered decision selects **B4.17 bounded offline FEM phase-cost and setup-reuse feasibility probe**. It has not started.
That slice must separately freeze one bounded phase-cost/setup-reuse candidate,
complete projection/compliance/gradient parity and all cost/memory charges
before execution. It authorizes no fit, checkpoint/seed replacement,
continuation, quality threshold or final cohort access. If the prospective
cost candidate fails, retain it and stop rather than start a search. A passing
versioned learned repair and independent confirmation, then a compatible
final contract, remain required before B5. Fixed P/17 remains unrepaired.

## Complete new resource closure and software checks

Review/audit each cap at 60 charged seconds, whole review 180 seconds /
1 GiB, with a fully paid 30-second closure reservation. All production
processes exited zero; there were no retries or failed production attempts.

| Process | Complete native wall | Closed charge | Peak RSS bytes |
|---|---:|---:|---:|
| review | 3.13 | 13.130000 | 305807360 |
| independent | 2.86 | 12.860000 | 292913152 |
| closure, full reservation | 3.61 | 30 | 289423360 |

Total new charge **55.99 seconds**, retained peak
**305807360 bytes**. The post-exit closure wall plus ten seconds,
internal charge and native RSS fit its full reservation/retained peak. The
closed ledger was not rewritten. A separate post-exit controller initially
used system Python and failed before importing NumPy/Torch. Its exception,
command and tool-reported 0.007069042-second duration are retained; native
RSS/profile for that controller failure are unavailable. A conservative
one-second wall plus ten-second failure reserve was charged inside the
already fully paid closure reservation. The successful locked-Python checker
was separately profiled (3.27 seconds,
295731200 bytes); combined closure/controller
reserved cost is 27.88 <=30 seconds. Its RSS fits
the retained production peak. No production stage or numerical work was
rerun, and the ledger was not rewritten. B4.15's 84.33-second
charge and all original failure/quality/cost decisions remain unchanged.

Before source commit, locked dev sync, Ruff, mypy (65 files), all
**858 tests in 485.17 seconds** and working/staged whitespace
checks passed. Twenty-nine new tests cover complete populations, outlier
preservation, both ordered decisions, independent mutation detection,
metadata-before-result guards, native CPU and failed-attempt/cap accounting.
An initial development Ruff check detected a misplaced new test block; it
was corrected before the full checks, with its software log retained. This
was not a production attempt or numerical failure. Evidence publication
repeats all required checks and merges only after its own exact-head CI passes.
Before evidence commit, locked dev sync, Ruff, mypy (65 files), all **858
tests in 468.99 seconds** and working/staged whitespace checks passed again.
Numerical source, conventions and every production receipt remain unchanged;
no generated dataset, profile, result or cache is committed. No upstream
reference code or new external source was used.

| External receipt | SHA-256 |
|---|---|
| `audit_receipts/plan.json` | `2854d228df3455c7ff379a3a064f475619a8059325126ffefed12c0f73522fb3` |
| `audit_receipts/production_release.json` | `bb68e581e10659c2124c6d4b485267dfc630d3e8eaff0fac500e3240fda39a62` |
| `audit_receipts/source_final_head_ci.json` | `e3f04801281809abdaf454bdb3a4fe8e411883ff3ac4d96683683132f8c068d2` |
| `review.json` | `7ebbe7570046c472e9ca77b417b6904940a34a792430f04f8bba143c5f850249` |
| `independent_audit.json` | `2769e9057ee38bad333a68925141a7a0999aca06177b702d5f5369c73e00843c` |
| `resource_close.json` | `2bf31e3b9495f65964c4ba015afd872f0270154e72a551ec10160f96596437cc` |
| `audit_receipts/execution_commands.json` | `460ac132b92229662bc516fbc8a0fd3a91b691f02817ecc93cfaf33bb64c63ba` |
| `audit_receipts/closure_command.json` | `41fc848c7c9f6785e4e41249524cefedc36b4df43eac6a694b1ced32790b1f1f` |
| `audit_receipts/closure_profile_verification.json` | `b1de723d7f248b847e7f42d298bcfd4911dd5c51ec630ac599b2dd39106d8368` |
| `audit_receipts/postexit_controller_reservation.json` | `9f1105badde9a20ab5721150f65014ca2c4967c7665ea573e83113d20fbad76f` |
