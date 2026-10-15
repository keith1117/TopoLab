# D1 exact-physics resource feasibility — stopped before real input

Date: 2026-10-15. Baseline main `42a6fdae96229fba0d53df252c4da89c03ca2775`.
Identity: `topolab.v2.physics-resource-feasibility.v1`.

**Result: STOP_UNKNOWN_PREFIT_BOUND.** The owner approved complete D1, including
the new identity, limited mechanism reconsideration, 1260-second incremental
ceiling, 4-GiB simultaneous limit and eight-label scope. The mandatory independent
allocation/lifetime upper bound was not established. D1 therefore closes at
admission, before integration implementation, real input or formal execution.
This is an explicit resource UNKNOWN/failed admission, not a new scientific
failure or evidence that all possible exact-physics implementations exceed 4 GiB.

The [protocol](../planning/d1_physics_resource_feasibility_protocol.md) and
[contract](../planning/d1_physics_resource_feasibility_contract.json) record the
authorized proposal and incomplete registration. They were authored after this
static gap was identified; no preregistered formal result or independent formal
review is claimed. There is no new TEXT scientific Gate or checker campaign.

## Actual recovery and inspection boundary

Assigned worktree: `/Users/keith1117/.codex/worktrees/a99d/TopoLab`, initially
clean detached at the baseline above, then `docs/d1-physics-resource-admission`.
Main CI was successful, R1 PR192 merged and no open PR/unfinished D1 existed.
The main checkout was not edited and no second worktree was created.
Required rules/plans/status, B3 and relevant B4.15/17/34/51 contracts/reports
were reread. The current chat directly supplies D1 authority; no old chat is
needed to manufacture a grant or supersede a frozen contract.

Inspection used committed source as text and the installed dependency wrappers
as text without imports/evaluation. The locked versions are NumPy2.5.3,
SciPy1.18.1 and macOS Torch2.14.0. Official API context was consulted for
[SciPy splu](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html)
and [PyTorch Conv3d](https://docs.pytorch.org/docs/2.14/generated/torch.nn.Conv3d.html).
These pages describe interfaces/shapes; they do not supply this project's complete
allocation/lifetime proof. The SciPy page labels1.18.0, so it is API context,
not an exact1.18.1 runtime certificate. The SuperLU project's
[FAQ](https://portal.nersc.gov/project/sparse/superlu/faq.html) was context only;
its serial/MT/DIST statements are not interchanged or used as a memory bound.

| Local dependency text | SHA256 |
|---|---|
| scipy/sparse/linalg/_dsolve/linsolve.py | `deb673200c3b01093c849450a342df52cd80d7d1536914e3c0257e36b16f3cfc` |
| torch/nn/modules/conv.py | `ef261d946378fcb5a047d2113ef715f04b2894eef2f2f7ad6009c920f2e9ebc1` |

These bind inspected Python wrappers only. Native binary/transitive runtime
closure and its independent upper bound remain UNKNOWN_UNREGISTERED. No native
backend, solver ordering, library, objective, projection, dtype or tolerance was
changed to manufacture admission.

## Allocation/lifetime inventory and missing proof

| Simultaneous category | Source/lifetime evidence | Admission status |
|---|---|---|
| Controllers/children/runtime | D1 would need producer and separate candidate-free audit process chains; interpreter/import/allocator/thread residency needs a complete simultaneous bound | UNKNOWN; no actual formal launch preflight or source freeze |
| Labels/input/I/O | Eight named train IDs are fixed by R1; real payload sizes, literal paths/hashes, decode and conversion peaks not admitted | UNKNOWN_UNREGISTERED; no index or label opened |
| Physics setup/anchor/certificate arrays | Exact current-prediction route uses no reciprocal anchor/certificate. PreparedCompliance retains mesh, filter, COO indices, free DOFs/loads and weights across evaluations | Explicit shapes inspectable; complete population ownership/copies not independently bounded |
| Network/optimizer/gradients | Unchanged ContextCNN has26433 parameters; one float32 parameter copy105732 bytes, same payload for parameter gradients. D1 permits no optimizer updates and no optimizer is instantiated | Tensor payload arithmetic is partial; runtime, graph and allocator residency UNKNOWN |
| Activations/autograd | Four width16 layers retain a graph through all per-case physics bridges until batch backward; local Conv3d dispatches to native F.conv3d | Native forward/backward workspaces, saved tensors, copies and overlap UNKNOWN |
| Projection/filter work | Float64 clipped offset/filter/pullback; filter preparation constructs Python lists before sparse conversion | Shapes and code order known; full lifetime/storage upper bound not established |
| Python/storage objects | Case/label decoding, containers, graph nodes, ndarray/Tensor metadata and persistence require separate accounting | UNKNOWN; payload sums do not cover object/allocator peaks |
| Transient assembly/factorization/serialization | PreparedCompliance freshly builds COO→CSR→reduced CSC, calls splu, materializes U for pivot checks and solves while model graph remains live | Native SuperLU fill/workspace, transient conversion and complete overlap UNKNOWN |

The eight-category inventory is **not an independent proof**. In particular,
`PreparedCompliance.evaluate` delegates `splu(reduced, permc_spec=ordering)` to
the installed `_superlu.gstrf`; no byte workspace/lifetime envelope is supplied
by this caller. `ContextCNN.forward` delegates convolution/backward to Torch.
No candidate-free bound binding these native paths and all other live terms was
established. API absence alone proves no universal impossibility; it leaves the
required admission fact UNKNOWN. No arbitrary safety multiplier, RSS sample,
monitor limit or hypothetical backend is substituted.

Sources: [prepared physics](../../src/topolab/prepared_compliance.py),
[original bridge](../../src/topolab/offline_compliance.py),
[CNN](../../src/topolab/b2_12_context_cnn.py),
[sparse FEM](../../src/topolab/fem.py), [filter](../../src/topolab/simp.py),
[mesh](../../src/topolab/mesh.py) and [fitting lifetime](../../src/topolab/b3_training.py).
All remain byte-identical to baseline.

For a largest batch8 and N elements, the raw input's visible float32 payload is
`4*8*13*N`, and four hidden outputs alone are `4*4*8*16*N`:

| Mesh | Input bytes | Four hidden output payload bytes |
|---|---:|---:|
| 12×6×3 | 89856 | 442368 |
| 24×12×6 | 718848 | 3538944 |

This is scalar integer arithmetic, not a mesh/tensor/memory trial or graph peak.
Extra ReLU tensors, saved tensors and workspaces are not declared zero. The old
B4.17 full-population array estimate2287564048 bytes excludes object/network/
optimizer/transient terms and is a sample extrapolation, not a certified upper
bound. Its nominal2007403248-byte headroom cannot close D1. The 508-case model
and full through-fit peak remain PENDING4GiB; D1's smaller subset already lacks
its own necessary bound. No conclusion is obtained by pretending it allocated
the full prospective population.

## Execution, quota and full-cost disposition

Actual D1 research access/calls: **0 external index reads, 0 label/model reads,
0 new meshes/arrays/FEM/network integrations, 0 fits/searches/memory trials,
0 old formal calls, 0 new producer invocations and 0 new independent invocations**.
These are the agent's explicit access/action record, not inferred native program
counters. Unexecuted program counters, timings, native peak, correctness/FD and
full-fit forecast remain UNKNOWN_NOT_EXECUTED. No independent formal audit PASS
is claimed. Both new roles close unlaunched0/1, with no transferable opportunity.

The shared FULL60 is retained as a conservative D1 charge. Producer/audit600
limits are caps, not FULL reservations or invented executed time. The ceiling1260
is not an actual bill. Known ledger-floor arithmetic is:

```text
K = 12721.16417100014444982
D1 FULL shared reserve = 60
K + booked D1 reserve = 12781.16417100014444982
K + proposed maximum1260 = 13981.16417100014444982  # ceiling scenario only
```

Additional old history and every new reading/authoring/software/CI/publication
cost remain additional, with unavailable totals/peaks UNKNOWN_NOT_ZERO. Neither
the60 reserve nor a software peak certifies complete D1 resource compliance.
No whole-project or all-paid PASS, zero-work cost claim, cap reset, historical
cost exclusion or full-v2 allocation follows. Old7200 stays permanently failed.
No production root, pending/started/terminal receipt or source freeze is created.
The proposed root stays absent; missing formal evidence is not a successful exit.

## Scientific and route disposition

D1 closes at its specified UNKNOWN stop; it delivers no accepted composed
capability. This admission result rejects **this rescue proposal with the current
available proof**, not the mathematical possibility of route B. Scientific Gate
FAIL/fixed P17 unrepaired and B4.51 FAIL_PROCESS_SOURCE_FREEZE stay. Historical
failures, all69 predicate failures, costs/FULL reserves/UNKNOWN, old consumed
quotas, old memory/exit gaps and every seal remain. B4.52 is NOT_SELECTED_BY_R1.

No material scientific/resource blocker was closed. Make the route decision now;
do not spend a second default slice on a guard, toy, another timing replay or an
unfunded proof chain. The single next owner decision is whether to **close the
current exact-physics rescue program under unchanged4GiB/prefit requirements**
(recommended). v1 remains usable and full v2 remains open. No new scientific
successor, budget/access, D1 reopening or independent platform slice is implied
by “continue”; A2.3/A2.4/A4 still require their own instruction.

## Software/publication validation

No numerical source, tests, tolerance, fixture, lock, CI or public README changes.
All five precommit AGENTS commands **PASS**: locked dev sync, Ruff, mypy
(81 source files), complete **1951 pytest in657.16s**, and diff checks. The same
complete test population/tolerances ran with the allowed one-thread BLAS/OpenMP
settings. New relative links40/40 and reviewed-path/JSON/ignore/history/frozen-byte
checks PASS. Reviewed staged/every-upload/actual-squash checks and protected
latest-head/main CI with identical tested/merged trees govern final publication;
complete logs and actual release closure remain external.

New software/recovery/publication records:
`/Users/keith1117/Documents/TopoLab-data/d1-physics-resource-feasibility-software-2026-10-15`.
They contain the authority/baseline/source-text hashes, software checks and actual
PR/main/CI/guards/backup closure. No old evidence or backup member is copied.
Retain the assigned worktree, clean up only this merged deliverable branch and
stop after this D1 closure.

| New D1 software record | SHA256 |
|---|---|
| pytest.log | `26348b9e19ef97ec80ff180cd9a445798e366cc98f23f895b9926950bab0787b` |
| full_required_checks.json | `d6299b06245c95f8a732ece90263f12a148dd965082866ba6ed220aec1936f24` |
| paper_arithmetic.json | `d77950ac99707515fad9f2963f840d103198b23cf94717238aa427d9939f5d6e` |
