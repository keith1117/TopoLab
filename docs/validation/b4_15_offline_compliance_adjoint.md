# B4.15 bounded offline compliance-adjoint feasibility probe

Date: 2026-10-05 (America/New_York).

**Numerical correctness passed; bounded prospective fit feasibility failed.**
All eight frozen train labels, sixteen fixed raw states, 48 complete CPU
forward/backward measurements, 64 directional checks and 24 independent
normalizer/central-state solves were retained. The complete probe performed
200 FEM solves and no optimization, fit, new label/reference, screening query,
checkpoint access or final access. Fixed P/17 and every historical failure and
charge remain unchanged. Next slice: **B4.16 bounded offline adjoint cost-feasibility review**.
Uniform remains default; B4.12's scientific Gate remains failed and B5 stays sealed.

## Frozen source, training access and objective

The [protocol](../planning/b4_15_offline_compliance_adjoint_protocol.md),
[numerical convention](../numerical_conventions.md#b415-offline-compliance-adjoint-training-only-v1),
kernel, probe, independent auditor and closer merged in
[PR #129](https://github.com/keith1117/TopoLab/pull/129) after all applicable
exact-head CI checks passed. Tested head `c0add7093a0400a19ca211d6636a53558f581bf5`;
clean merged execution revision `2450b0c754f0c9ba1ed17b7ef7cacce913147d81`;
merge timestamp `2026-10-05T05:47:31Z`. Tested and merged trees match.
Plan SHA-256: `0eb32b48abbb58ebe02e3fc00f8c4dd1f9f6a1ff74e1b8f6dec1281a31916f52`.
The source release binds 131 executable/protocol/convention/runtime
files. Production uses locked Python 3.12.10, one BLAS/OpenMP
thread and one Torch intra-op thread, with artifacts in
`/Users/keith1117/Documents/TopoLab-data/b4-15-offline-compliance-adjoint`.

Six exact B4.14 metadata/result hashes, its native closure proof and all prior
B4.13/B4.12/historical/recovery guards were checked before and after each
process. The complete B3 materialization index is fixed by SHA-256
`b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26`.
Only the first two canonical B3 expanded-train cases per mesh/direction cell
may open label bytes. An additional exact-eight/train-only check runs before
artifact lookup, then the existing B3 fitting guard verifies membership,
identity, origin, content hash and serialized state. Fit-validation and other
train cases are rejected too. Labels are read again by the independent auditor;
this is eight unique existing training artifacts, not new data generation.

| Frozen training case ID | Mesh | Direction | Volume |
|---|---|---|---:|
| `tlcase-v1-0079bd9f0d927e20866f2c73be19e1f57471576f7cd0494b6898a46f7fab9858` | [12, 6, 3] | y | 0.2 |
| `tlcase-v1-01504c9e63d2dfa11017438a813a3dfd23f27f9f9997bb59edfc3a24a3d21f50` | [12, 6, 3] | y | 0.25 |
| `tlcase-v1-03a2c40639cc65aedf22d7ddc65359616807735e87c680949b09638d4eaa1e8f` | [12, 6, 3] | z | 0.3 |
| `tlcase-v1-04ab9b94039197973b9e3ca5b1a855528197f30cce70635b1c1014002673461c` | [12, 6, 3] | z | 0.6 |
| `tlcase-v1-0ca7ef4d765a4e8403221471f98c061684e99dde777b047a1a3f5f0642fc47b6` | [24, 12, 6] | y | 0.5425 |
| `tlcase-v1-144d548fd53ff9798a62251e0d02258eda28d17fdf6fb87ff5979b3f0b904900` | [24, 12, 6] | y | 0.4 |
| `tlcase-v1-0294749064eb3e7aacc57d5f4a3ce11b01133fb2e10d01fa44722dfdb3860f26` | [24, 12, 6] | z | 0.5175 |
| `tlcase-v1-0ea4104dcf6c16b35ef4c239eb34a1341a4e554813a1ad8c15cc1eade6d54768` | [24, 12, 6] | z | 0.5175 |

The objective `C(F(P(z)))/C_train` evaluates current raw predictions through
SIMP and FEM; `C_train` is the same case's stored float32 terminal-state
compliance, independently re-solved as a constant. The probe uses fixed
metadata-defined raw fixtures, not network predictions or fitted designs.
The implementation independently derives the filter transpose and clipped
projection's implicit volume-offset derivative. It introduces a training-only
`1e-12` projection version; the existing `1e-6` query projection is unchanged.
The derivative describes the continuous mathematical stable-active-set map,
not IEEE quantization or finite bisection branches. Clipping kinks within
`1e-10` are rejected. There is no silent stop-gradient through offset/filter.
The CPU Torch bridge supports first derivatives and preserves input gradient
dtype; float32/float64 bridge behavior was exercised in software tests.

## Independent numerical checks and finite differences

The audit does not call the new projection, pullback or compliance
evaluation arithmetic. It separately builds a row-normalized sparse filter, solves the
volume root with Brent's method, assembles stiffness and solves displacement,
then obtains compliance and sensitivity from element strain energies. It
reconstructs the active-set cotangent and audits every retained directional
scalar and timing population. It re-solves eight stored label normalizers and
sixteen central probe states; finite-difference sides are produced by the
probe and their retained arithmetic is independently checked. No complete
historical outcome is reclassified.

| Evidence | Result |
|---|---:|
| Independently checked numerical conditions | 408 |
| Failed numerical conditions | 0 |
| Directional differences (2 directions × 2 steps × 16 states) | 64 |
| Maximum normalized directional error | 3.3260894089e-06 |
| Frozen directional-error limit | 0.0001 |
| Clipped raw entries across central states | 2664 |
| Free raw entries across central states | 12888 |
| Maximum central physical-volume error | 9.82658399096e-13 |
| Maximum legacy query-projection density difference | 2.71240787697e-06 |

All repeat values and gradients must match; both finite-difference sides
retain the central free set. Shift cotangent sums are independently checked.
Independent compliance retains `rtol=1e-9`; raw gradients use `rtol=1e-9`,
`atol=1e-10`. Directional error is
`abs(FD-adjoint)/max(abs(FD),abs(adjoint),1e-8)` at fixed `1e-4/2e-4`
steps. No tolerance, step, raw fixture, label or epoch cap was changed after
production access. Synthetic tests additionally cover both clipping bounds,
kinks, invalid inputs, zero volume/shift derivatives, forbidden label reads,
independent assembly, failed-attempt charges and ordered stop rules.

| Case prefix / fixture | Normalized compliance | Max directional error | Max forward+backward wall seconds | Max CPU seconds |
|---|---:|---:|---:|---:|
| `0079bd9f` / interior | 7.845826289 | 2.74572937e-06 | 0.138534458 | 0.064008000 |
| `0079bd9f` / clipped | 19.260000094 | 4.20237829e-07 | 0.008613167 | 0.008613000 |
| `01504c9e` / interior | 6.918469884 | 5.14652983e-07 | 0.009563375 | 0.009304000 |
| `01504c9e` / clipped | 20.751425013 | 1.60311375e-07 | 0.008645208 | 0.008642000 |
| `03a2c406` / interior | 7.379158129 | 1.56729605e-07 | 0.009148125 | 0.009145000 |
| `03a2c406` / clipped | 34.091954000 | 2.36066263e-07 | 0.009329333 | 0.009322000 |
| `04ab9b94` / interior | 3.178331664 | 3.69188808e-07 | 0.009829250 | 0.009827000 |
| `04ab9b94` / clipped | 8.955761574 | 6.02832993e-07 | 0.009490208 | 0.009433000 |
| `0ca7ef4d` / interior | 3.068737940 | 2.12909926e-07 | 0.172008167 | 0.171543000 |
| `0ca7ef4d` / clipped | 3.225193200 | 2.26361299e-06 | 0.186878667 | 0.184215000 |
| `144d548f` / interior | 4.604489814 | 2.57057194e-07 | 0.175636667 | 0.174402000 |
| `144d548f` / clipped | 5.011027863 | 3.32608941e-06 | 0.167153250 | 0.166236000 |
| `02947490` / interior | 3.577045011 | 2.48005635e-06 | 0.201749042 | 0.190063000 |
| `02947490` / clipped | 4.291446586 | 1.11155933e-06 | 0.168525750 | 0.167523000 |
| `0ea4104d` / interior | 3.917491940 | 4.52672668e-07 | 0.181144125 | 0.174772000 |
| `0ea4104d` / clipped | 4.679811502 | 8.87094092e-07 | 0.198163917 | 0.193210000 |

## Fully charged cost and ordered feasibility decision

Three fixed repeats include each prepared projection, sparse FEM forward,
analytical filter/offset adjoint, tensor construction and Torch backward.
Every repeat is retained; no free warmup or best-time selection. All label
reading, geometry/filter setup, difference solves, independent audit and
startup/exit are also charged by complete native process profiles. Setup wall
sum is 3.349470918 seconds and setup
CPU sum is 3.289321000 seconds. Native
profiles retain complete user/system CPU as well as wall and RSS.

The predeclared prospective proxy uses three seeds, 200 full epochs and 508
training cases per epoch (432 small, 76 large): 304,800 additional physics
objectives. Maximum measured prepared wall per scale is used with a fixed
1.25 multiplier; add ALL twelve B4.1 fits' 3,870.204341-second baseline and
this probe's complete charge. This is a conservative planning proxy on a
small fixed sample, not a measured new fit or a rigorous bound for all 508
cases. It does not substitute realized early stopping after viewing costs.

| Frozen planning quantity | Seconds |
|---|---:|
| Maximum observed small prepared forward/backward | 0.138534458 |
| Maximum observed large prepared forward/backward | 0.201749042 |
| Additional offline physics extrapolation | 56384.859789 |
| Conservative existing fit baseline | 3870.204341 |
| Complete new probe charge | 84.330000 |
| Total prospective three-fit proxy | 60339.394130 |
| Frozen prospective cap | 7200 |

Cost feasibility is **failed**.
Full training memory feasibility remains pending: the sequential probe's RSS
cannot certify all network activations, optimizer state or a complete training
population. Correct derivatives cannot establish terminal quality, learned
generalization, faster accepted refinements or query-time acceleration. No
query physics cost is introduced by this offline-only kernel, but every future
real fit and query would still require complete measured costs and quality.

The following scenarios assume future distinct queries saved exactly 0.1 or
1.0 seconds each, purely hypothetically. They include the complete fit proxy,
not a claim that a new model achieves either saving. These are fit/probe
planning scenarios, not full experiment amortization: the shared B3 data
phase alone cost another 5,325.353116 seconds, and all development screening,
selection, future inference/refinement, final evaluation and replication costs
must enter a later full ledger. Their exclusion here cannot support an
end-to-end acceleration claim.

| Queries | Assumed saving seconds/query | Physics-only extra cost/query | Net seconds after complete fit proxy | Break-even queries |
|---|---:|---:|---:|---:|
| 1000 | 0.1 | 56.384860 | -60239.394130 | 603393.941 |
| 1000 | 1.0 | 56.384860 | -59339.394130 | 60339.394 |
| 10000 | 0.1 | 5.638486 | -59339.394130 | 603393.941 |
| 10000 | 1.0 | 5.638486 | -50339.394130 | 60339.394 |

Probe and audit each have a 600-second charged cap, whole cap 1,260 seconds /
1 GiB, and the full 30-second closure reservation is paid. All three production
processes exited zero; any failed attempts would remain in the same immutable
ledger. Number of retained failed production processes: 0.
Closed charge is **84.330000 seconds**, retained peak
**510836736 bytes**.

| Process | Complete native wall seconds | Closed charge seconds | Native peak RSS bytes |
|---|---:|---:|---:|
| probe | 23.84 | 33.840000 | 510836736 |
| independent | 10.49 | 20.490000 | 434962432 |
| Closure, full cap reserved | 4.01 | 30 | 300679168 |

Post-exit closure wall plus ten seconds and internal charge both fit its
reservation; native RSS fits the retained peak. The closed ledger was not
rewritten. B4.14's charge remains 50.39 seconds and all earlier charges,
failures, seeds, model artifacts and outcomes remain unchanged.

| External receipt | SHA-256 |
|---|---|
| `audit_receipts/plan.json` | `7c1e6f8cb8b6e39ae8367b9fab02d176abbbf9b9e629d0cad6b832cfa59e7692` |
| `audit_receipts/production_release.json` | `d054d6a75efed2783ba5ef3926cf7f9b25041dc6c1a7eaf0a6b4258acb48fb83` |
| `audit_receipts/source_final_head_ci.json` | `4cd38750af814673fb4f97b4cd2104b84d69babc84f1a7250b17d6c5605eb295` |
| `probe.json` | `e34e5f652a048e07bc0f1a732ff93d63e566699f45c11017007858f003761ace` |
| `independent_audit.json` | `ea6cfc01551d53f9bf4243fd6929b53a7a2a2a83e82bddcbcfe6e31d082dfcc5` |
| `resource_close.json` | `39a49c229c5cf9e1bce04bea2446086522b9ad76dfb354363718d26b6d5a1154` |
| `audit_receipts/execution_commands.json` | `d5cbd15425ab9d96a1aa4f49a86e80f614e737f096695e9d0ef0e42dd722cf42` |
| `audit_receipts/closure_command.json` | `34e6fb3f7ab477846645f040063530c6a1ed43adf5fe9e8db22f892ff46e4487` |
| `audit_receipts/closure_profile_verification.json` | `f61eb572680bbcd46f1a2b02bbb5cad458aa8b149f24facd8c2b193a3fb4000d` |


## Software validation and next slice

Before the source commit: `uv sync --dev --locked`, `uv run ruff check .`,
`uv run mypy src` (65 files), all **829 tests in
477.25 seconds**, and working-tree/staged whitespace
checks passed. Twelve new tests cover this behavior and its access/cost
boundaries. Exact-head CI passed before source merge. Evidence publication
repeats all required checks and merges only after its own exact-head CI passes;
receipts remain outside Git. Before the evidence commit, locked dev sync,
Ruff, mypy (65 files), all **829 tests in 480.80 seconds** and working-tree /
staged whitespace checks passed again. Numerical source and every production
receipt are unchanged. No generated datasets, weights, profiles or caches
are committed. No upstream reference code or additional external source was used.

The frozen ordered decision yields **B4.16 bounded offline adjoint cost-feasibility review**. It has not started.
No automatic fit, seed replacement, threshold/step/length search, continuation
or new screen follows. A passing versioned repair, separate independent
confirmation, compatible final contract and later Gates remain required before
B5; all 48 unused B4.10 cases and final evaluation stay sealed. Report this
next slice and wait for the user to start it.
