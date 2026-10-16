# P/17 bounded-runtime penalty homotopy — finite proposal

Date: 2026-10-16 (America/New_York). Baseline: merged main
`2ec9303c60919aaaf2f4f3d7611e4be6837fb71c`, [PR195](https://github.com/keith1117/TopoLab/pull/195),
with all three [main CI jobs successful](https://github.com/keith1117/TopoLab/actions/runs/38826009072).
Chinese decisions: [roadmap Section6](TopoLab_v2_开发路线图.md#6-推荐执行顺序).

**Decision: CONDITIONAL_IMPLEMENTATION_PROPOSAL_NOT_ADMITTED.** One materially
different repair hypothesis is specified: fixed P/17 weights, a short prescribed
penalty homotopy, then the original physical objective and terminal tolerances.
A new bounded-storage native query implementation is its explicit prerequisite.
Its storage design is concrete; no implementation, complete independent binary/
runtime bound, fair performance result or repair evidence exists. **There is no
currently admitted executable repair route.** Do not describe this proposal as
resource PASS, P/17 repaired, accelerated, or full v2 delivered.

The sole next owner item is **whether to authorize the software capability I1 in
Section7 and identify its Linux build/preflight environment**. I1 requests no old
research payload and no scientific execution budget. A later physical pilot has
a separately reviewable, unapproved ceiling/access proposal below; I1 approval
does not authorize it. A plain “continue” presents this decision only.

## 1. Current authority and retained evidence

The owner requested one concrete reviewable proposal, retaining full v2,4GiB
and independent preflight, with no experiment. This explicitly commissions this
planning slice after the previous [candidate elimination](TopoLab_v2_solver_internal_learning_route_decision.md).
It does not reopen that candidate, D1, the owner-closed exact-physics training
rescue, B4.30 or B4.51. No budget/access/implementation follows from publication.

Read boundary: versioned rules/contracts/reports, committed source TEXT/AST,
public primary method/API documentation and GitHub publication metadata.
**Old external compact-metadata allowlist/read set: empty.** No embedded pointer,
old raw evidence, backup member, index, label, model or sealed content is read.
No prediction, FEM, fit/search, timing/memory trial or formal program is run.
Required complete software regression remains a separate software namespace.

The [B4.30 report](../validation/b4_30_paid_continuation.md) retains P/17 compliance
ratio1.0020904310312866 and R/17 ratio1.0019709437499813>1.001 on case55c1b3e…;
R/17 target mean1.016053130777518>1.0. P/R failures1/3/1 remain. The
[B4.32 dispositions](b4_32_generalist_method_preregistration_protocol.md) stop
unchanged reflection, post-plateau continuation and old training rescues.
Historical models, all failures/costs/UNKNOWN, consumed quotas and seals stay.

## 2. One hypothesis and its contract boundary

Assessment identity: `topolab.v2.p17-bounded-penalty-homotopy.v1`, proposal only.
Call the proposed method H; primary is **H/17 using the same fixed P/17 and
same-seed S weights**, not another seed/checkpoint. No fitting or weight change.

For the predeclared large24×12×6, y-load, volume<0.55 generalist stratum:

1. Encode the unchanged13-channel input and project the unreflected P prediction
   using the existing legacy filtered-volume rule.
2. Perform exactly8 ordinary OC/FEM updates at SIMP penalty p=1, then exactly8
   at p=2. Re-analyze the current state on each penalty transition. Do not stop
   early, select a witness, blend predictions or inspect reference quality.
3. Set p=3 and run the unchanged physical-plateau/design-change terminal rules.
   All16 prefix updates count inside the existing360 total: at most344 remain.
   Only p=3 states populate the terminal ten changes/eleven compliances. No
   prefix state supplies a convergence certificate or final compliance.
4. Re-solve and independently classify the selected p=3 terminal state. There is
   no inherited20-update polish or original/endpoint witness rescue in H.

Elsewhere H equals the same-runtime plain P/S policy. The activation stratum is
the already documented generalist failure stratum, not a lookup of failed case
IDs. The proposed8/8 schedule is one **untested engineering choice**, fixed
before outcomes; it is not learned, literature-prescribed, tuned or authorized.
No alternative schedule, penalty, weight, threshold, backend or seed search.

This changes the intermediate optimization objective and potentially its basin,
rather than extending the same p=3 trajectory, reflecting a prediction, training
through FEM, or learning internal sensitivities. Every update still uses real
physics. It might lose the learned advantage or worsen quality: both are exits.

Liu and Tovar (2014), [Section6.1.6](https://link.springer.com/article/10.1007/s00158-014-1107-x),
describe penalty continuation as a way to mitigate premature local convergence,
without a global-optimum guarantee. This supplies mechanism context only, not
the proposed schedule, a diagnosis of case55c1b3e…, or a TopoLab result. No code,
figure, implementation layout or performance number is imported.

A new solver/query/reference identity is mandatory under
[B3 Section1](../b3_experiment_contract.md#1-question-versions-and-scope).
Intermediate p=1/2 states are explicitly marked and never relabeled as old p=3
evidence. Old labels/checkpoints remain frozen inputs/controls, not new labels.
The physical final problem, filter radius, loads, supports, material, p=3,
360-update cap and quality tolerances remain. B5/final evidence stays sealed.

## 3. Resource admission by a concrete bounded implementation

Reusing Torch/SciPy/SuperLU would retain the exact missing native/workspace
bounds. This proposal instead requires an **opt-in standalone Linux x86-64
query executable**, single thread, with explicitly sized storage for inference,
FEM/filter/OC, input/output and histories. This is substantial numerical software
work; no such executable or bound is claimed to exist.

The fixed implementation design uses independently derived scalar CPU-float32
ContextCNN inference, bounded safetensors/JSON readers, float64 Hex8 physics,
and an in-place band Cholesky solve. It calls no Torch, SciPy, BLAS, SuperLU,
general sparse factorizer, external command or GPU on the admitted runtime path.
Scalar sqrt/sigmoid math, hashing, serialization and system interfaces also need
reviewed bounded call graphs; static linking alone establishes none of this.
No dependency implementation is copied or assumed allocation-free. The intended
ELF has no PT_INTERP/DT_NEEDED; every statically linked helper remains in the
audited source/call closure. After fixed startup, no brk/mmap/mremap, loader,
thread creation or unregistered child path may be reachable from payload handling.

An independently authored verifier reconstructs element assembly and energy,
uses its own band LDLᵀ solve, and independently checks projection, terminal
classification and charges. It imports no candidate kernel, predictor, classifier
or memory/cost helper. Its complete executable and controller need the same
admission. Ordinary Python/Torch regression is not that verifier or its bound.

### 3.1 Derived storage capacity, not an observed peak

Retain physical node/element ordering. Internally permute **only free solve DOFs**
to z-fast, then y, then x. With x-min clamped, use zero-based
`node_free(i,j,k)=k+(nz+1)*(j+(ny+1)*(i-1))`, i=1…nx.
Connected element nodes differ by at most `(ny+1)*(nz+1)+(nz+1)+1`.
Therefore n=3*nx*(ny+1)*(nz+1), half-bandwidth
`b=3*((ny+1)*(nz+1)+(nz+1)+1)+2`.

| Mesh | Free DOFs n | Half-bandwidth b | One float64 n×(b+1) band, bytes | Two bands, bytes |
|---|---:|---:|---:|---:|
| 12×6×3 | 1008 | 101 | 822528 | 1645056 |
| 24×12×6 | 6552 | 299 | 15724800 | 31449600 |

Band Cholesky preserves this SPD band; the
[Netlib DPBTRF specification](https://www.netlib.org/lapack/explore-html/dc/d58/group__pbtrf_gafd2c3ba375ecee6dba1fba62696993e0.html)
documents factor storage in the same band format. It is mathematical/storage
context, **not permission to call LAPACK or a bound on a linked library**.
The new numerical implementation must independently handle nonpositive/unsafe
pivots and preserve N1 agreement and equilibrium tolerances. No regularization,
diagonal shift, sparse fill, pivot search or alternative ordering is allowed.

At the large mesh, a fully explicit dense density filter plus row sums uses
23901696 bytes; two complete per-query histories of two density fields with361
states use19961856 bytes. Inference can stream two16-channel activation fields
and one input, with105732 raw parameter bytes per26433-parameter checkpoint.
There is no optimizer/autograd or simultaneous508-label fit. No full Q/Y or
reciprocal certificate is involved. These are integer payload calculations only.

### 3.2 Complete allocation/lifetime obligations

Proposed storage is one256MiB fixed arena per producer/verifier and a16MiB
controller arena, with typed nonoverlapping slots and fixed loops. All source
arrays, temporary math/parse buffers and object equivalents must fit these
actual capacities; no heap expansion, variable-length stack or spill file used
as uncharged memory. Oversize/malformed input is rejected before allocation.

| Retained category | Required bounded implementation, checked before real input |
|---|---|
| Controllers/children/runtime | Complete launcher/role ELF segments, startup, scalar helpers, TLS, stacks, signal/error paths, kernel helper mappings and overlap; no hidden interpreter/child |
| Inputs/I/O | Hash and stream only frozen bounded files through fixed buffers; one label/model view at a time; parser depth/token/array limits and failure paths bounded |
| Physics/setup | Explicit element connectivity, coordinates, permutation, load/free-space vectors and two bands; checked shape/index arithmetic |
| Network/optimizer/gradients | Exact accepted weight bits and graph, bounded convolution buffers; optimizer/training absent by executable call graph, not an estimated zero |
| Activations/saved state | Fixed inference slots/lifetimes and audited scalar nonlinearities; no native Conv3d/autograd dispatch |
| Projection/filter | Explicit H/row sums and OC/projection vectors, including bisection and all copies |
| Python/storage objects | No Python on this path; actual native metadata, parse/hash/journal buffers, padding and serialization remain included |
| Assembly/factorization/transients | Fixed band algorithms and independently derived verifier arrays; all copy, solve, failure and publication lifetimes included |

Target **complete mapped-process envelopes**, including the arenas, are producer
<=512MiB, verifier<=512MiB, controller<=64MiB. Conservatively summing all three
gives **1140850688<4294967296 bytes**, even though roles should be sequential.
These are build acceptance constraints, not guessed headroom or a current proof.
Any helper/overlapping process must be counted; no shell/Python helper is excluded
to make the arithmetic pass. Keep the existing whole-role/native-RSS meaning;
this is not a claim about whole-machine/kernel-cache memory.

I1 must produce a separately reviewed **source-to-binary allocation/lifetime
certificate**: slot bounds, maximal stacks, linked code/call closure, all process
overlap and a proof that no input-dependent mapping/allocation growth is reachable.
Actual preflight must verify binary hashes, argv/cwd, empty bounded environment,
one thread, origins and complete mappings before any old payload. The Linux
[ELF](https://www.kernel.org/doc/html/latest/userspace-api/ELF.html) and
[/proc documentation](https://www.kernel.org/doc/html/latest/filesystems/proc.html)
provide mapping/interface context only. A maps/RSS snapshot alone is insufficient;
the no-growth/lifetime proof must cover the complete later execution and errors.
Do not substitute RLIMIT, a monitor, a safety multiplier or a sampled RSS.

All actual binaries, compiler/host identities, mapped-runtime totals and the
independent complete bound remain **UNKNOWN_UNIMPLEMENTED / UNREGISTERED**.
Any unresolved term, unreviewable linked helper or source change after freeze
refuses real input. Native through-observed-exit evidence remains separately
required. No historical/full-fit gap is filled by this new design.

## 4. Repair acceptance and controls

A possible later pilot uses **only the18 already exposed B4.30 sentinel physical
cases**, not its closed runner or any sealed/fresh cohort. Bind the versioned
original contract SHA `ddb69d4947c01e849306b387bac5e23dbf9fd5fa42b896b29edac376b6bb63d3`,
JSON path `population.sentinel.case_ids` and definition digest
`c68758e494d62515bfe189323c328209e023b3df73dd7c4ee49495857d40a388`.
New solver/reference identities are required; register their exact definitions
and compatibility before launch. No old outcome is reused as a new timed run.

Proposed19 methods per case: uniform, physics heuristic, train-only NN;
C/P-keep/W for17/29/43; plain-P for17/29/43; H for17/29/43; uniform-initialized
homotopy as an additional non-ML comparator. Thus **18 new references and342
fully charged query outcomes**, plus separately bounded independent checks.
P-keep retains the historical fixed20/own-witness policy **as a matched control
only**; H and plain-P do not inherit it. No R reflection or old formal program
is rerun. Plain-P isolates removal of polish; uniform-homotopy tests whether
the learned start adds anything beyond the non-ML numerical intervention.

All methods share the new bounded backend and declared scalar inference graph.
Frozen checkpoint bits/architecture/seeds do not change. A port is a new
execution identity, not historical P/17 evidence. Inference and unchanged-p=3
physics require independent public parity checks first. Record numerical drift
explicitly. If plain-P/backend changes alone remove the counterexample, report
that confounding and **STOP_ROUTE_NOT_ISOLATED**; do not credit homotopy.

Required exposed-panel outcome, with candidate-free numerical/cost audit:

- H/17 zero attempt failures/fallbacks on all18; repair the seven previously
  declared seed/case target predicates and introduce no accepted-P regression.
  Preserve both non-target small-z P/29 negative controls and every old result.
- Convergence within360 shared updates, original0.01 design/physical-change and
  0.0002 plateau criteria, p=3 independent compliance rtol1e-9/atol0,
  compliance<=1.001*matched uniform and volume error<=0.005. Prefix p=1/2
  never fills a p=3 certificate. Successful fallback never repairs an attempt.
- H/17 target mean **and** charged-sum ratio<=1; both-scale overall means and
  charged-sum ratios<=0.90; each direction mean<=1. At least two H seeds meet
  the retained matched C/W reliability criteria. Overall H/17 mean must be below
  C/17 and both original non-ML controls **and** uniform-homotopy. No pooled-sum
  substitution, favorable-seed replacement or discarded failure.
- Fresh version-matched uniform/reference agreement at1e-9 and independent
  assembly/equilibrium/gradient checks retain the frozen N1/N2 targets. All
  source/model/input identities, complete attempted/performed counts, charges,
  native chains and observed exits must pass; UNKNOWN blocks acceptance.

This panel could establish only a bounded exposed-case repair. Separate fresh
independent confirmation, full new B4 and a compatible final contract remain
before B5. It cannot establish full-v2 acceleration using a weakened denominator:
the new backend's uniform is **not presumed as fast as A3's optimized uniform**.
Before full B4, a resource-admitted matched optimized-reference comparison is
required; its feasibility is UNKNOWN. If no fair admissible denominator can be
provided, stop the route. This proposal grants no old SuperLU benchmark/retry.

## 5. Complete cost and proposed later pilot ceiling

Retain K=12721.16417100014444982>7200 and booked D1 FULL60:
**H_history>=12781.16417100014444982 s**, plus all other history and additional
software/CI costs/UNKNOWN. The unchanged all-paid7200 condition is permanently
failed. No new identity, zero new fits or incremental ceiling changes that Gate.
Old508-case/200-epoch costs and programs remain closed, not set to zero.

Each new query pays load/hash/encode/inference, projection, **every** p=1/2/3
analysis/update/transition, terminal decision, recording and any full fallback.
The program also pays references, every control/ablation, independent audits,
startup/observed exit, failed work, preparation/porting and FULL reserves.
Use disjoint inclusive envelopes; do not add a whole query again to its phases.

Optimistically even with zero extra inference/I/O/audit overhead, H must recover
the16 prefix updates and transition solves through fewer p=3 updates. The old
failed case's128 uniform updates are an observation on the old backend, not a
new timing or count guarantee. Band storage is not a speed bound. Complete new
maxima, actual iterations, wall time, break-even and repair probability are
**UNKNOWN_NOT_TESTED**; no favorable wall estimate is fabricated.

For a later separately authorized **one-shot exposed-panel pilot only**, propose
an incremental ceiling **14580 charged wall seconds**: producer<=10800,
independent numerical/resource audit<=3600, shared **FULL180**. Both role ceilings
include controller/launch/observed-exit work and native-wall+10s/recording floors.
The FULL reserve stays paid unused; it is not a second role cap. No retry/reset,
extra panel or redistribution. A failed producer allows failed-prefix metadata
audit only, not numerical completion of its suffix.

Requested future quotas are exactly **one producer attempt and one independent
attempt**, consumed before their interpreter/executable starts, even on failure;
currently both remain UNALLOCATED_NO_GRANT. A producer query may perform at most
364 candidate analyses (initial/transitions/360 updates/final check), plus at
most362 for a fresh uniform fallback.18 references allow at most362 each:
`342*(364+362)+18*362=254808` producer FEM analyses maximum. For independent
terminal/window reconstruction, at most4 witnesses×12 analyses per query and12
per reference give `342*48+18*12=16632` maximum. These are conservative proposed
operation caps, not required execution counts or timings. No free pilot,
calibration or pre-probe is permitted. The later contract must partition exact
checks/order inside these ceilings; inability to do so prevents launch.

This is a **spending limit, not a runtime prediction or affordability PASS**.
It allows a bounded failure after admission. Scope precedent is B4.30's complete
18/270 finite panel and retained6951.133782042092664 stage charges; this proposal
adds72 control/ablation queries and real homotopy work, changes the backend and
host, and retains a separate audit ceiling. The larger ceiling is an explicit
owner risk decision, not extrapolated maximum performance or transferred money.
Absent that decision or a complete prelaunch reservation, do not launch.

At that unapproved ceiling the known diagnostic floor would be
**27361.16417100014444982**, plus all additional history/implementation/software/
CI/publication UNKNOWN. It is not whole-project spend or a full-v2 upper budget.
I1's ordinary development/regression costs remain additional UNKNOWN_NOT_ZERO;
no scientific allocation or FULL reserve is created by this proposal. No training,
fresh confirmation, full B4/B5, cloud purchase or hosting budget is included.

For I1 itself, propose **one capability slice and at most16 active engineering/
source-review hours**, including independent resource review. This is a bounded
owner investment decision, not a completion estimate or scientific CPU grant.
Mandatory complete regression/CI/closure is additional, recorded separately;
its cumulative cost remains UNKNOWN_NOT_ZERO. At the work limit, stop changing
the implementation, retain the failed/unfinished result and complete its honest
software/publication closeout. No self-approved extension or second proof slice.

## 6. Access decisions — future requests, all denied now

| Later stage | Exact semantic scope | Required owner decision and before-read boundary |
|---|---|---|
| I1 software implementation/preflight | Committed definitions, primary mathematics/API docs, newly authored public software fixtures, own new binary/build/runtime metadata | Approve only I1 and select one Ubuntu24.04 x86-64 CPU build/preflight environment. Recommend the repository's existing Ubuntu24.04 CI surface for public software only; this needs no new cloud purchase or research payload. Exact image/toolchain/path identities must be frozen and remain UNKNOWN_UNREGISTERED here. This does not choose or authorize a later pilot host |
| Possible later pilot metadata | New bounded role manifests naming only the12 fixed C/P/W/S checkpoints for17/29/43,528 B3 training labels needed by NN,18 exposed definitions and18 legacy uniform scalar references | Separately approve metadata preparation/reading with literal paths, byte counts and SHA256 enumerated before parsing. No discovery through an index or embedded pointer. An owner-prepared restricted export may supply these lists; its provenance/bytes must be reviewed |
| Possible later pilot payload | Exactly the admitted12 checkpoint safetensors,528 train-only NN labels and listed18 old reference scalars; generate new reference/query outcomes at a new exclusive root | Separately approve these producer/independent views and the14580 ceiling after I1. Check bytes/hashes/schema/dimensions before use; one bounded reader, no resident whole population. No fit-validation, screen/final/OOD, old raw outcomes/trajectories, backups, other models or seals |

Counts identify a finite **request**, not permission or a guessed list of paths.
All actual old literal payload paths/hashes/sizes and role views remain
UNKNOWN_UNREGISTERED_DENY until independently frozen. Independent receives no
candidate helper or candidate source as its numerical oracle. Before physical
launch, freeze every attempt/check order/count, stage/whole cap, role quota,
output path and compatibility identity. No runnable contract is issued here.
The proposed future root name is `p17-bounded-homotopy-pilot-v1` under the approved
external experiment storage; it is **not created** by this planning slice.

## 7. Unique next capability decision and finite exits

**I1 proposal — not authorized by the present request:** implement one opt-in
bounded native two-scale query path with the specified model/filter/FEM/OC/
homotopy and matched controls, plus a separately authored verifier/controller.
Keep the existing application/default/source identities unchanged. Deliver the
actual compilable integrated capability, public numerical/parsing/failure
regression, independently reviewable complete allocation/lifetime closure and
actual data-free startup preflight from clean locked merged CI-passed source.
No standalone text checker, public arithmetic campaign or guard-only substitute.

Prerequisites: explicit owner I1 scope/work-limit approval, selected Linux
environment and registered candidate-free resource-review role; actual role
identity remains UNKNOWN_UNASSIGNED here. Version its native build contract and
compiler/math-helper closure before use.
No old payload, scientific role, fit, production FEM or resource/timing trial.
Ordinary public source regression is explicitly part of the requested capability;
it supplies no historical/native/full-fit scientific evidence. Scientific budget
requested for I1: **none**; mandatory software costs are separately recorded.

Acceptance: full dimension/path coverage by the implementation, unchanged
public N1/N2 numerical tolerances and source regression, candidate-free complete
bound for all8 categories/process chains within4294967296 bytes, verified
immutable binary/runtime origins, finite parse/stack/error paths and actual
pre-input preflight. Neither256MiB arenas nor maps alone passes admission.
No numerical/software tolerance may be loosened to obtain a port.

Exit once: absent host/authority, unbounded native/runtime/lifetime term,
unverifiable model/solver compatibility, infeasible fair reference, failed
correctness/preflight, cap violation or frozen-source mutation closes I1 with
NO_ADMISSIBLE_ROUTE under this proposal. No default second backend, proof,
text/toy/guard, model search or D1 reopening. Even an I1 pass **stops** and presents
the later pilot contract/budget/access decision; it does not run that pilot.
After at most I1 and one explicitly approved pilot, review material blocker
changes and close/choose the route; no automatic confirmation chain.

This planning slice closes with [its validation report](../validation/p17_bounded_homotopy_proposal.md),
current bilingual scheduling and one history/provenance entry. Resource admission
and new science remain UNKNOWN; old scientific FAIL/P17, B4.51 failure/quotas,
full-fit PENDING4GiB and every seal remain. Publish the proposal and STOP.
