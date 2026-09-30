# B3 versioned warm-start experiment contract

Prepared: 2026-09-30 (America/New_York)

Status: **B3.1 planning contract frozen before B3 data generation, fitting,
or final evaluation.** B2.28 feasibility and B2.29 independent development
confirmation support this bounded experiment. Gate B3 remains pending its
complete data audit. Uniform remains the operational default. M0/M1/M2,
superseded M3 v1, and all B2 outcomes retain their original identities and
decisions. This contract introduces no numerical solver change.

## 1. Question, versions, and scope

Can the B2.28 weighted terminal-design generalist and B2.24 specialist
route yield reproducible, same-quality, fully charged query-time savings
on a predefined two-scale cantilever design scan, after selection using
new development cases and one-time evaluation on untouched evidence?

The repeated-query task varies point-load position/direction and target
volume on one fixed supported domain. The final workload is the balanced
grid in Section 2. Each measured query is a distinct physical case;
query-result caching cannot replace a solver run. Amortization scenarios
at 1,000 and 10,000 further distinct queries assume the same stratum mix
and measured costs; these are projections, not additional observations.
Claims are restricted to the tested grid and hardware, with x-direction
OOD reported as safe rejection rather than learned axial generalization.

| Boundary | Version / binding |
|---|---|
| Experiment | `topolab.b3.experiment.v1` |
| Catalog / exposure / split | `topolab.b3.catalog.v1` / `topolab.b3.exposure.v1` / `topolab.b3.split.v1` |
| Manifest / materialization / label | `topolab.b3.dataset.v1` / `topolab.b3.materialization.v1` / `topolab.b3.label.v1` |
| Training / checkpoint / selection / freeze | `topolab.b3.training.v1` / `topolab.b3.checkpoint.v1` / `topolab.b3.selection.v1` / `topolab.b3.freeze.v1` |
| Evaluation index / statistics | `topolab.b3.evaluation-index.v1` / `topolab.b3.statistics.v1` |
| Physical case / encoding / architecture | `topolab.m0.case.v1` / `topolab.b2_9.vector_load.v1` / `topolab.b2_12.context_cnn.v1` |
| Solver / numerical source anchor | `topolab.simp.physical_plateau.v1` / `5b34ff9edb8772a4b0f456a7b94c454e16579aa6` |
| Locked environment SHA-256 | `9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292` |

Each later artifact also binds its actual clean merged implementation
revision, this contract's exact byte hash, catalog/exposure hashes,
upstream artifact hashes, and locked runtime. The numerical anchor fixes
the equations, ordering, stopping policy, projection, and quality rules;
a semantic solver, workload, or budget change requires a new experiment
version and compatible new labels. Platform changes cannot silently
alter the paired denominator. Generated artifacts remain outside Git.

## 2. Frozen physical catalog and training memberships

Use domain lengths `(12.0,6.0,3.0)`, meshes `(12,6,3)` and `(24,12,6)`,
material `E0=1000,Emin=1,nu=0.3`, all-component x-min clamp, one x-max
point load of magnitude `-1`, filter radius `1.5`, penalty `3`, minimum
density `0.05`, move limit `0.2`, and density tolerance `0.01`. Large-grid
load indices double small-grid `(y,z)` indices on the same physical
domain; physical lengths and filter radius do not double. Initialization
is null in case definitions. **All labels and compared methods use a
360-update cap**, retaining the physical-plateau policy and A3 ordering.

The 528 train definitions are the union of B2.4's 468 train cases,
B2.23's 20 train additions, and B2.27's 40 train additions. Map each
240-update source definition to a new 360-update case ID, recording its
exact source case ID. Re-generate every label from uniform. Historical
labels and checkpoints are not B3 fitting inputs; no compatibility claim
or relabeling of M2 failures is needed. New roles are:

| Role | Cases | Volumes | Small-grid x-max `(y,z)` positions |
|---|---:|---|---|
| `train` | 528 | Inherited exact train definitions above | Inherited exact source positions |
| `fit_validation` | 32 | `0.3271,0.4611,0.5371,0.5951` | `(1,2),(4,1)` |
| `screen_validation` | 48 | `0.3291,0.4631,0.5351,0.5931` | `(2,1),(3,2),(5,2)` |
| `final_id` | 96 | `0.3237,0.4597,0.5337,0.5917` | `(1,1),(2,2),(3,1),(4,2),(5,1),(5,2)` |
| `final_ood` | 48 | Same as final ID | Same as final ID |

Cross each non-train row with both meshes and y/z directions; OOD uses
x only. Final ID has 48 cases per mesh, 24 per scale/direction, and six
per scale/direction/volume cell. OOD has 24 cases per mesh and each has
an exact y-direction final counterpart. There are **752** catalog cases.
Training contains 432 small and 96 large cases. Freeze memberships:

- `base`: the 468 B2.4 train definitions;
- `expanded`: base plus 40 B2.27 train definitions, 508 cases;
- `specialist`: base plus 20 B2.23 train definitions, 488 cases.

Only the explicitly inherited train definitions enter these memberships;
B2.4/B2.23/B2.27 validation cases and later B2 screen cases are excluded.
Fit-validation has eight cases per scale/direction, screening has
twelve. The specialist's checkpoint metric uses only the four
fit-validation y cases at volume `0.5951`, two positions at each scale.

Catalog identity bytes are compact, sorted-key, ASCII JSON plus one
terminal newline of `{"catalog_version":"topolab.b3.catalog.v1",
"entries":[...]}`. Entries sort by case ID and contain exactly `case_id`,
`role`, `source_case_id` (null outside train), and `training_sets`.
Membership names follow `base,expanded,specialist` order when present.
The complete problem is transitively bound by the existing case ID.
Expected catalog SHA-256:

```text
441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c
```

## 3. Exposure ledger and access boundary

The historical ledger covers these metadata sources, including failed,
superseded, design-exposed, and unopened reserved cases:

| Source membership | Case definitions |
|---|---:|
| `m0_v1` | 160, original 100-update catalog |
| `m0_v2_m1` | 160, frozen 120-update catalog and M1 |
| `m2_all` | All 756 definitions, including test/OOD and failures |
| `m3_final_design` | All 96 published M3 v1 final definitions |
| `b2_development_and_reserved` | B2.29's 922 blocked plus 48 confirmation cases |

Rebuild M3's published catalog and require its original SHA-256
`ddb0a0b4c6b3e5790187acad70459e6128b1f94d8a8b3be7ea8339395a16cbe3`.
Its inherited train/validation definitions are already in `m2_all`.
The historical union has **1,982 unique case IDs and 1,376 fingerprints**.

For each normalized problem, remove only
`optimization.max_iterations`, encode with the catalog's canonical JSON
rules and terminal newline, and SHA-256 the bytes. This supplementary
physical fingerprint does not replace case identity. Budget variants,
trajectories, tensors, repeats, and augmentations of that problem share
one exposure boundary. Ledger entries sort by fingerprint and contain
exactly `physical_fingerprint`, sorted unique `case_ids`, and sorted
unique `sources`, under `{"version":"topolab.b3.exposure.v1",
"entries":[...]}`. Expected exposure SHA-256:

```text
5ab3f2d57d390b804c4e5157f41f206155a4bee7d31a6c4edcbc614c44e1a7b7
```

All B3 roles must have pairwise disjoint fingerprints. Train is an
explicit subset of historical development exposure; every other role
must have zero intersection with that ledger. All new validation/final
volumes are absent from every historical source. Final case definitions
are public preregistration metadata. Their density labels, traces,
quality results, times, and statistics remain sealed until B5.
Upon publication, all 752 definitions also become reserved/design-exposed
for any later experiment version, even if this program stops before B5.
A later hypothesis cannot reuse this final grid as fresh final evidence.

| Consumer | Permitted access |
|---|---|
| Catalog / planning | Case and artifact-reference metadata only |
| B3 data audit | 560 train/fit-validation labels; 48 screening uniform references |
| Fitting / epoch selection | Requested train membership and fit-validation label bytes only |
| B4 screen / candidate selection | Screen case definitions, reference metadata, and timed query outcomes; no query label input |
| Nearest neighbor | Exactly all 528 B3 train labels, shape bucketed |
| B5 query evaluation | Frozen final definitions and methods; no final label input |

Consumers reject forbidden roles before opening artifact bytes. Final
references are computed only during B5; B3 generates no final label or
reference. Exact IDs, fingerprints, roles, memberships, source links,
and tensor-derived exposure must be verified on construction and read.

## 4. Label quality and Gate B3

Produce 560 terminal-design labels (528 train plus 32 fit-validation)
and 48 mandatory screening uniform reference records from one clean
merged label revision. Require complete, independently audited
**560/560 labels and 48/48 references** before fitting. No imputation,
case replacement, tolerance relaxation, or favorable subset is allowed.

Use B2.4's stored-state checks under the new B3 artifact identity:
finite converged full-precision terminal state, physical-volume error
`<=0.005`, independent final compliance agreement `rtol=1e-9,atol=0`,
CPU float32 terminal design/physical tensors in `(1,nz,ny,nx)` order,
and independently reconstructed filter, volume, stored-state compliance,
and sensitivity weights. Full-precision and serialized-state compliance
remain distinct records. Projection retains its existing `1e-6` volume
target. All numerical precision tolerances remain those in
`docs/numerical_conventions.md` and the audited B2.4 implementation.

Default planning is read-only, invokes no solver, opens no label, and
creates no output root. Execution uses external roots, canonical case
order, atomic content addressing, and append-only success/failure
records. Unexpected interruption leaves the current case pending;
recorded terminal failures are immutable. Require exact catalog/ledger
hashes, all per-role and per-stratum counts, every byte/provenance check,
and the resource Gate. A failure stops this version before fitting.

## 5. Fixed fitting program and controls

Fit from scratch, CPU float32, exactly seeds `17,29,43` for four recipes:

| Recipe | Train membership | Case-weighted design-MSE objective | Query use |
|---|---|---|---|
| C, control generalist | base, 468 | Weight 8 for y at volume `>=0.5`, otherwise 1 | Routed control |
| P, primary candidate generalist | expanded, 508 | Same as C | Routed candidate; route ablation |
| A, loss ablation generalist | expanded, 508 | All case weights 1 | Routed loss ablation |
| S, shared specialist | specialist, 488 | Weight 8 for y at volume `>=0.55`, otherwise 1 | Shared by C/P/A |

This is **12 fits and at most 2,400 attempted epochs**. C isolates the
middle-volume label addition, A isolates weighting, and P without S
isolates the specialist route without another fit. The fixed network
has 26,433 parameters: four width-16 3-cube convolutions with `(z,y,x)`
dilations `(1,1,1),(1,1,2),(1,2,4),(1,2,8)`, matching padding, ReLU,
and a one-channel sigmoid head. Retain the thirteen-channel vector-load
input and terminal design target; no query-time FEM input is added.

Use AdamW `lr=1e-3,weight_decay=1e-4,betas=(0.9,0.999),eps=1e-8`,
batch size 8, 200-epoch maximum, 25 consecutive epochs without strict
improvement, zero loader workers, deterministic algorithms, and separate
seeded initialization/shuffle generators. Each case appears once per
epoch in same-shape batches; no resizing or augmentation. Loss is
per-case elementwise MSE weighted and divided by the case-weight sum.
Checkpoint selection is earliest strict minimum **unweighted mean
per-case MSE** on all 32 fit-validation cases for C/P/A, and the four
specialist cases for S. Equal loss keeps the earlier epoch. Safetensors
checkpoints and complete histories bind every input artifact and recipe.
There is one fixed configuration; no extra seed, architecture, epoch,
weight, ensemble, or hyperparameter search is permitted.

Route C/P/A to same-seed S only on `(24,12,6)`, y, volume `>=0.55`;
use their generalist elsewhere. The route ablation always uses P for
supported y/z cases. All learned policies reject x before inference,
charge the metadata decision plus a fresh uniform solve, and record
rejection. They do not claim learned x-direction quality or speed.

## 6. B4 screening, prospective selection, and freeze

Run all 48 screening cases: uniform, fixed physics heuristic, train-only
nearest neighbor, then C/P/A/P-without-S for every seed: **720 outcomes**.
Get a fresh timed uniform per case and require compliance agreement
with the B3 mandatory reference within `rtol=1e-9,atol=0`. Each other
method uses that timed uniform as its denominator. NN retains the
original ten-channel MSE distance, same-shape lookup, and lexicographic
case-ID tie break; it uses all 528 train labels for every comparison.

Charge routing, encoding/inference or lookup, projection, full refinement,
quality decision, and complete fresh uniform fallback. A failed attempt
retains failure status. Accept only convergence within 360 updates,
finite state, independent compliance `rtol=1e-9`, compliance
`<=1.001 * uniform`, and physical-volume error `<=0.005`. Rejection,
candidate failure, accepted-quality violation, and fallback are separate.
Record one-time loading/building costs and process-wide RSS separately.

Require at least two P seeds with arithmetic paired means `<=0.90` at
both scales, `<=1.0` in all four scale/direction strata, at most two
failures and no more than matched C, no more non-specialist y failures
than C, and overall mean below both non-ML means. Across all P seeds,
require at least 6/9 middle-volume large-y successes (`0.5351`) and
6/9 high-volume large-y successes (`0.5931`). All 720 outcomes and
resource/quality checks must pass completeness audit.

The **deployable primary** additionally requires a P seed with zero
screen failures/fallbacks, all those speed bounds, and overall mean
strictly below its matched C and both non-ML means. Select among these
eligible seeds by lowest worst scale mean, then worst direction mean,
then overall mean, then frozen seed order `17,29,43`. Selection uses
only this new B4 screen; B2.29 cannot select a B3 primary. Persist every
seed and all controls/ablations, including ineligible results. The claim
will concern this prospectively selected G/S pair; other seeds are
reported diagnostics, without a claim that every fit is accelerated.

Freeze this selected seed, all twelve checkpoints/histories, catalog,
ledger, data indices, code, statistics, hardware/runtime, and the
selection table into a checksum-bound artifact before final access.
A2.1/A2.2 process ownership/isolation work must precede expensive B5
execution. If no primary qualifies, stop with final evidence sealed.

## 7. Final order, statistics, and delivery decision

On Apple M2, open final ID once in canonical case order, then OOD:
all fifteen fixed methods above, **2,160 outcomes**. On an independently
installed Ubuntu 24.04 x86-64 CPU environment, replay the same 144
definitions and frozen primary pair, with fresh local uniform, physics,
and NN comparisons: **576 outcomes**. No refitting, reselection, or
cross-platform pooling. Record actual CPU, memory, OS and library
metadata before that environment's first final query; a failure cannot
trigger replacement by a favorable host. Replication tests independent
execution of the fixed artifacts, not an independent retraining claim.

Uniform runs first. Rotate the remaining method list by
`int(sha256(utf8("topolab.b3.method-order.v1:"+case_id)).hexdigest()[:8],16)
% len(remaining_methods)`, preserving the C/P/A/route-ablation and seed
orders above before rotation. The replication list is physics, NN,
primary before rotation. Each atomic case entry retains every method;
interruption reruns only the incomplete case in full. Every attempted
run and restart contributes to cumulative stage compute charges. Never
remove, replace, or retime a completed case to improve its statistic.

The primary statistic is arithmetic mean per-case selected-primary /
uniform end-to-end ratio, separately by mesh. Report all seed-specific
and all-seed diagnostic summaries. Use 10,000 paired physical-case
bootstrap resamples, NumPy `default_rng(20260930)`, linear 2.5th/97.5th
percentiles. Within each analysis unit, sample with replacement inside
each fixed scale/direction/volume cell, preserving its size and every
method's matched observation. Cells order small/large, x/y/z as present,
then ascending volume, with case-ID order inside cells. Reset the RNG
per unit: each ID scale, each OOD scale, and pooled ID. Controls and
ablations cannot replace the primary after final access.

The complete B5 delivery Gate requires **both environments** to have:

- Every required reference and outcome, zero accepted quality violations,
  and all operational results passing the numerical contract. Any uniform
  or fallback failure defeats the Gate without changing its denominator.
- On ID, zero selected-primary attempt failures or fallbacks; each scale
  has point mean ratio `<=0.90` and upper 95% limit `<1.0`. Every
  scale/direction mean is `<=1.0`. Total primary query time is also
  `<=0.90` of total uniform time at each scale, so normalized ratios
  cannot conceal a slower complete scan.
- Pooled balanced ID primary-minus-comparator paired-ratio differences
  have upper 95% limit `<0` against each fixed non-ML comparator.
- On OOD, zero accepted failures and each scale's upper 95% primary /
  uniform ratio limit `<=1.05`, with rejection cost fully charged.
- Complete phase, quality, iteration, failure/rejection/fallback, memory,
  data generation, fitting, validation, loading, and artifact-cost tables.
  Report break-even query count against uniform and both non-ML methods,
  using absolute measured times, plus the 1,000/10,000-query scenarios.
  Separate deployment preparation from the full experiment cost and
  state any nonpositive savings or unavailable historical costs.

This freezes a minimum 10% point effect and the roadmap's uncertainty,
quality, OOD, and replication requirements. A favorable subgroup or
diagnostic seed cannot rescue a failed primary. Report the result of
this version regardless of sign; final acceleration wording follows
only the complete passed Gate and its exact scope.

## 8. Finite compute program, failures, and next slices

Apple execution uses CPU only, Python `3.12.10`, the frozen lockfile,
one BLAS/OpenMP/PyTorch intra-op thread and eight inter-op threads.
Linux uses the same Python/lockfile/thread policy. Record model/index
loading in resource elapsed/RSS; charge all restarts and audit work.

| Stage | Maximum cumulative wall compute | Peak process RSS |
|---|---:|---:|
| B3 labels, screening references, and complete audit | 14,400 s | 2 GiB |
| All twelve fits and artifact audit | 7,200 s | 4 GiB |
| Complete B4 screen and freeze audit | 21,600 s | 2 GiB |
| Apple final ID plus OOD and audit | 43,200 s | 2 GiB |
| Independent Linux replication and audit | 14,400 s | 2 GiB |
| **Entire version** | **100,800 s (28 hours)** | Stage bounds above |

These are upper bounds, not runtime or success promises. Stop before
starting another case/epoch when its remaining stage budget is exhausted;
an overrun fails that resource Gate. No automatic extensions or second
fitting program are authorized under this identity. Transport/infrastructure
interruption may resume the same pending work with unchanged identity
and cumulative charges; terminal numerical failures remain recorded.

| Failed Gate | Required disposition |
|---|---|
| B3 data / provenance / resources | Preserve the full index; stop before fitting. A semantic repair requires a separately versioned contract and labels. |
| B4 model / quality / speed / resources | Preserve all fits and comparisons; stop before final access. Diagnose and preregister any finite new intervention. |
| B5 ID / OOD / replication / resources | Freeze and publish the negative result; full flagship delivery remains open. Exposed final cases become development information; a later hypothesis requires a new version and fresh final evidence. |

Do not tune on exposed final outcomes or silently relax this contract.
After this program stops, continuation requires a new user instruction
and a reviewable new finite contract. Historical software achievements
remain valid; they do not substitute for the required ML delivery Gate.

The next slice is **B3.2: implement and test the frozen catalog,
training memberships, fingerprints, and exposure/access boundary**,
without solver execution. B3.3 implements the B3 label/reference
artifacts and guarded materializer; B3.4 executes and independently
audits the complete data Gate. Subsequent B4 fitting/screen/freeze and
B5 ID/OOD/replication remain separate reviewable slices.
