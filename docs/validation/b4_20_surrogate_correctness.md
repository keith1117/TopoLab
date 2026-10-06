# B4.20 bounded surrogate representation and correctness review

Date: 2026-10-05 (America/New_York).

**The frozen correctness review failed.** All eight guarded expanded train cases, sixteen synthetic projected inputs and64 directional rows completed. Candidate and independent audit each paid16 anchor FEM solves,32 total. All **984 independent numerical conditions** completed, with one failed condition; maximum directional error was **0.000125254361629**. Complete new charge is **100.30 seconds** and measured peak RSS **447741952 bytes**.

The complete panel verifies the two anchor representations and retains one failing directional condition; full correctness acceptance is not established. It does not evaluate local approximation fidelity, a prospective fit-cost proxy, full training memory or learned repair. No fitting, new label/reference, model bytes, optimization, continuation, screen or final access occurred. Fixed P/17 remains unrepaired; uniform remains default and all48 unused B4.10 fresh cases/B5 stay sealed.

Next slice: **B4.21 bounded surrogate correctness failure review**. It has not started.

## Prospective boundary and CI-passed source

The [protocol](../planning/b4_20_surrogate_correctness_protocol.md), opt-in kernel, runner, independent auditor, durable journals and closer merged in [PR #139](https://github.com/keith1117/TopoLab/pull/139) after all applicable exact-head CI passed. Tested head `29e2282b9697a7cf016ff3ebbc8c8d333b8f96ab`; clean execution revision `8e17bb48654cdd9bba1c39e1d29db7980718f7b4`; merged `2026-10-06T01:39:56Z`. Tested and merged trees match. Production binds 148 source/protocol/convention/runtime files. Plan identity `topolab.b4_20.surrogate-correctness.v1`; SHA-256 `4e0d131f4dc0e4ae7d19d6313bce6bb15e776e22ed85a103ca4e7efe42e1e22f`. Locked Python and one BLAS/OpenMP/Torch thread were used. Artifacts are external at `/Users/keith1117/Documents/TopoLab-data/b4-20-surrogate-correctness`.

Eleven exact B4.19 bindings protect the closed failed attempt, original command/profile, metadata-only audit, source/evidence releases and CI, closure proof and reservation. All recursive B4.18 through B3 guards passed. B4.19's73.93-second charge, failed Gate, unknown failed case/gap/exact counters and absent numerical panel remain unchanged. Only the same eight canonical train cases as B4.15 passed its exact-subset and B3 expanded-fitting guard, before artifact lookup. Both numerical processes completed eight guarded label reads each; these are current successful operations, not B4.19's unknown read count. Default planning performs no evidence read and creates no output.

## Representation diagnosis and the fixed new intercept

Stored design x* is exactly float32 represented in float64. The label's analyzed physical density is rho_s=float64(float32(F(float64(x*)))); the continuous anchor is rho_c=F(float64(x*)). Independently solving both states confirms the stored label's compliance at unchanged rtol1e-9, and independently confirms the new continuous anchor and signed adjoint at the same tolerance. Quantization changes the analyzed state; its derivative is not included in the continuous objective.

The single `topolab.stored-normalizer-tangent.v2` candidate keeps the original audited C_s constant and the B4.15 objective C(F(P(z)))/C_s. Its tangent is

`L(z)=C(rho_c)/C_s + [F.T(dC/drho at rho_c)/C_s].T(P(z)-x*)`.

The intercept can differ from one. It receives an explicitly paid continuous anchor analysis; construction and prediction add no FEM call or retained numeric factorization. Signed sensitivities and negative affine estimates are preserved. The original v1 equality/rejection, all labels, numerical tolerances, projection and query paths stay unchanged. This is one prospectively chosen objective, with no normalizer/radius/coefficient search.

**6/8 newly measured continuous anchors** would reject the old normalizer equality; the maximum absolute normalized anchor difference is **1.33634978638e-08**. This diagnoses the precision assumption on the new complete panel. It does not identify B4.19's unknown failed case or reconstruct any lost original value. The table uses production values; independent values agree at frozen tolerances.

| Current train case prefix | Stored C_s | Continuous C(rho_c) | C(rho_c)/C_s -1 | Old equality rejects this new anchor |
|---|---:|---:|---:|---|
| tlcase-v1-0079bd9f0d927e | 0.230823975829 | 0.230823976907 | 4.66984562131e-09 | true |
| tlcase-v1-01504c9e63d2df | 0.136057678927 | 0.13605767868 | -1.81378723152e-09 | true |
| tlcase-v1-03a2c40639cc65 | 0.212982402064 | 0.21298240491 | 1.33634854294e-08 | true |
| tlcase-v1-04ab9b94039197 | 0.0787705359081 | 0.0787705354959 | -5.23309229283e-09 | true |
| tlcase-v1-0ca7ef4d765a4e | 0.0320574597821 | 0.0320574599195 | 4.28574820077e-09 | true |
| tlcase-v1-144d548fd53ff9 | 0.0527504952741 | 0.0527504950268 | -4.68771843565e-09 | true |
| tlcase-v1-0294749064eb3e | 0.0932157025744 | 0.0932157025573 | -1.825617435e-10 | false |
| tlcase-v1-0ea4104dcf6c16 | 0.0892749094658 | 0.0892749094184 | -5.30963495393e-10 | false |

## Independent correctness and durable evidence

For each case, the fixed interior and clipped B4.15 synthetic inputs are projected with the unchanged continuous root/pullback. The auditor uses its own Brent root, uncached Hex8 stiffness/energy adjoint, signed filter-transpose and active-set arithmetic; it calls neither the production tangent/projection/pullback nor Torch bridge. It re-solves both anchor representations and reconstructs all projected values, gradients and side values. Independent compliance rtol1e-9, gradient rtol1e-9/atol1e-10, density atol2e-11, volume1e-12, shift derivative1e-10 and FD error1e-4 remain unchanged. No failed state is dropped and no input, step or tolerance is adapted.

All64 sine/cosine differences at both1e-4/2e-4 steps retained stable clipping sets, but one exceeded the unchanged1e-4 directional threshold; 2664 clipped and 12888 free coordinates were audited across the sixteen inputs. One full CPU-float64 Torch forward/backward per input agreed with the direct value/gradient. These are correctness observations with no timing extrapolation or per-prediction exact-FEM fidelity measurement.

The one failed condition is current case `tlcase-v1-0ca7ef4d765a4e8403221471f98c061684e99dde777b047a1a3f5f0642fc47b6`, clipped fixture, sine direction, step1e-4. Retained plus/minus values are1.9859394732544189/1.9859394448207963; FD0.00014216811283773723 versus raw-gradient directional derivative0.0001421503056615197 gives error0.00012525436162919332. The2e-4 paired step and remaining63 rows stay retained; no step is selected to replace the failure. This report identifies the frozen rejection, without running a new root, FEM or derivative experiment or assigning an unmeasured cause.

The production journal contains **170 independently checked durable events**. Every event binds sequence/source/plan; before each label lookup/FEM invocation it retains case, operation, normalizer/density context and attempted/completed counters. Completed anchor analyses, each difference and each fixture are fsync'ed immediately. The independent process has a separate exclusive journal. Both ended with label attempted/completed8/8 and FEM16/16. No production stage failed or was retried. Injection tests confirm a rejection retains the before-call context, traceback and incomplete counter; exclusive attempt files block retry/overwrite. A hard kill can leave an attempted operation pending, which is not reported as a completed solve.

## Complete native resource closure

Probe/audit each cap300 charged seconds, complete native wall+10 and at least internal charge. Whole cap660 seconds/1GiB includes a fully paid60-second plan/closure/verification reserve. All complete native profiles retain wall/user/system/RSS from permitted first invocations. Numerical stages pay 20.26+20.04 seconds; reserve use was 36.77<=60, with the entire60 paid. Closure was independently verified after its native profile existed, without numerical reruns or ledger rewriting.

| Process | Native wall | User CPU | System CPU | Peak RSS bytes | Charge seconds |
|---|---:|---:|---:|---:|---|
| closure | 3.68 | 2.75 | 0.34 | 302006272 | within paid60 reserve |
| independent | 10.04 | 8.58 | 0.68 | 420184064 | 20.04 |
| plan | 2.99 | 1.78 | 0.30 | 273154048 | within paid60 reserve |
| probe | 10.26 | 8.62 | 0.86 | 447741952 | 20.26 |
| verification | 0.10 | 0.04 | 0.01 | 36651008 | within paid60 reserve |

The previous B4.15/16/17/18/19 charges84.33/55.99/112.34/86.13/73.93 and failed exact-FEM cost proxies60,339.394130/58,257.457957 remain unchanged. Later objective feasibility and complete experiment amortization must retain these and this review's complete charge. No new fit proxy is produced by correctness-only observations. Sequential RSS does not establish full network/data/optimizer/activation memory feasibility; that remains pending.

## Software validation and publication

Before source commit: locked dev sync, Ruff, mypy (67 source files), **978 passed in 537.49s (0:08:57)**, and working/staged whitespace checks passed. Ten new regression cases cover nonuniform serialized normalization with nonunit intercept, v1 rejection preservation, both Torch dtypes and prediction-time FEM exclusion, negative values, complete synthetic independent reconstruction, durable failure/exclusivity, default read-free planning, tampering and failed-attempt/cap closure. Evidence publication repeats all mandatory checks and merges only after its exact-head CI passes. No generated data, journal, profile or model is committed; the two pre-existing untracked user documents are preserved.

The failed correctness Gate selects only the next bounded failure review. No fidelity/cost probe follows this result. It does not authorize fitting, objective blending, additional radii, epoch/population/physics-frequency search, learned repair, primary reselection or final access. Passing learned repair and independent confirmation are still required before a compatible final contract and B5.

## External reproducibility bindings

| Artifact | SHA-256 |
|---|---|
| `audit_receipts/plan.json` | `3ab9680cd27f416c04803c20a8da96195ae921508e63a1bb7c52e0d798e19c15` |
| `audit_receipts/production_release.json` | `488f4a97d69d259d7fdb32dd6b8d5d547f214cb7caf531707f2294724f897ec2` |
| `probe.json` | `8d5424601a51f1b7a4755f4a730ff40997a0cabed66be5fb6d4919ba1f231bbb` |
| `probe.events.jsonl` | `581757fc2cd043fbb5a06f878f370569a75129ca9c585991ff4643994a41cbe9` |
| `independent_audit.json` | `f54c3ae3815a8de7710d88d8b40202f4900adb94c66f8dfef14e541ee25fc718` |
| `independent.events.jsonl` | `18f0ae95e42a1e99b0d195d8bc1ba5b78f4937dd5bcf632906d5a5b6d5fe410e` |
| `resource_close.json` | `8fa693a39a1156cb600d87807e9de27222c8e580278b8ea23e21cb7ab2d45d66` |
| `audit_receipts/closure_profile_verification.json` | `e0c9ba4033793b8c75a395c8ed088e70fbdae0fde3ce728e14a83dae0c944ce7` |
| `audit_receipts/postexit_controller_reservation.json` | `d555de75c8b525e831135ee5cbeea3f450b0c7af68d9ff37312673690f462d66` |
