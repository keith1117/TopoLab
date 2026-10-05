# B4.19 bounded train-only local compliance-surrogate feasibility probe

Date: 2026-10-05 (America/New_York).

**The frozen probe stopped at its anchor-normalizer integrity check; feasibility did not pass.** The single production invocation exited one with `ValueError: anchor compliance differs from audited normalizer`. No complete `probe.json` was published and the planned independent numerical auditor did not run. The 72-state/216-measurement/64-directional-row/416-solve panel is **planned, not completed evidence**. Local fidelity and the prospective fit-cost proxy remain unevaluated. No tolerance, normalizer, fixture, gate or source was changed after this failure, and the numerical invocation was not rerun.

Complete charged early-stop cost is **73.93 seconds** and observed native peak RSS is **311902208 bytes**. A separate metadata-only audit and post-exit resource verification passed. These close the failed attempt's resources, not its missing numerical Gate. Actual failed case, label-read count, FEM-call count and numerical gap were not emitted; they remain unavailable rather than reconstructed from timing.

No model fitting, new label/reference generation, model bytes, optimization, continuation, screen or final access occurred. Existing failed Gates/charges and fixed P/17 remain unchanged; uniform stays the operational default and all 48 unused B4.10 cases stay sealed.

Next slice: **B4.20 bounded surrogate correctness review**. It has not started.

## Frozen contract and CI-passed source

The [protocol](../planning/b4_19_local_compliance_surrogate_protocol.md), kernel, runner, independent numerical auditor and complete-panel closer merged in [PR #137](https://github.com/keith1117/TopoLab/pull/137) only after all applicable exact-head CI passed. Tested head `084b41fe421b41bfbc73bac21f2f5901e8950603`; clean execution revision `4b1b75bb8961dcbdc3af5314792d147357709205`; merged `2026-10-05T21:32:25Z`. Tested and merged trees match. Production binds 145 source/protocol/convention/runtime files. Plan identity `topolab.b4_19.local-compliance-surrogate.v1`; plan SHA-256 `9239e96ff30cd7e45e10c6a67069ec40cb1938d45a5160378b2de3d3908b2fb6`. Locked Python and one BLAS/OpenMP/Torch thread were used. All artifacts remain external at `/Users/keith1117/Documents/TopoLab-data/b4-19-local-compliance-surrogate`.

Eighteen exact B4.18 bindings and all recursive B4.17/B4.16/B4.15/B4.14/B4.13/B4.12/historical/B3 index guards passed before production and during the post-stop metadata audit. They preserve B4.18's denied metadata-plan invocation, its paid cost and its unavailable RSS without imputation. Default planning reads no evidence and creates no output. Only the same eight canonical expanded train cases as B4.15 can pass the exact-subset and B3 fitting read guard; no forbidden role can reach artifact lookup. Actual opened subset within these eight was not published.

## Single candidate and failed integrity condition

For an original stored float32 terminal design x*, the new training-only kernel pays one exact anchor FEM solve at `rho=F(x*)`, computes the signed un-clipped normalized filter-transpose derivative, and intends to evaluate `L(z)=1+g*.T(P(z)-x*)` with the B4.15 continuous volume projection and pullback. It does not substitute clipped positive label weights, clip negative affine estimates, reuse numeric factors or change the query path. Before retaining a kernel, it requires that the recomputed anchor compliance agree with the stored audited normalizer at relative 1e-9 and absolute0. That check rejected the production attempt.

The intended panel had four .001 local perturbations, four .05 outside perturbations and a uniform state per case, with fixed sine/cosine directions, positive/negative signs, .0005/.9995 raw margin, three CPU-float64 Torch forward/backward observations per state and both 1e-4/2e-4 directional steps. The intended 208 production and 208 independent FEM solves were not completed or certified. The full-panel numerical closer intentionally requires a complete independent audit; its successful path was not used to approve this partial result.

Independent compliance rtol 1e-9, gradient rtol 1e-9/atol1e-10, density atol 2e-11, volume 1e-12 and derivative checks remain frozen. None was loosened to turn a rejection into success. No current train state or label was reopened after the stop and no new FEM/objective/gradient evaluation followed it.

## Representation boundary and missing runtime evidence

The source exposes a concrete precision boundary that the B4.19 anchor assumption did not handle: `store_terminal_design` first serializes design to float32, filters it in float64, **serializes physical density to float32 again**, and computes stored compliance at that serialized physical density. `StoredDesignState` explicitly validates that representation. `LocalCompliance` instead applies the float64 filter to the stored design without the second physical-density quantization and compares that compliance with the stored normalizer at 1e-9. These are distinct analyzed states. The synthetic uniform-anchor tests did not exercise a nonuniform serialized physical-density target at this boundary.

This source-level discrepancy is a candidate explanation, not an independently measured diagnosis of the failed case. The actual compliance values, gap, case ID and buffered prior states were not emitted. Platform numerical differences also cannot be quantified from the traceback alone. B4.20 must separately freeze representation/normalization correctness checks and durable attempt evidence before any repair probe. B4.19 does not choose a new normalizer, differentiate quantization, rewrite a label or change a tolerance.

| Item | Retained evidence |
|---|---|
| Production attempts | One; exited1 at the anchor-normalizer rejection |
| Published complete numerical probe | None |
| Independent numerical audit / numerical conditions | Not run / none |
| Failed case ID / exact label-read count | Unavailable |
| Actual FEM-call count / numerical gap | Unavailable |
| Frozen-flow possible FEM-call counts | 1,27,53,79,105,131,157,183; static possibilities, not observations |
| Frozen-flow possible label-case counts | 1..8; all constrained to the registered subset |
| Local fidelity / prospective fit cost | Unevaluated |
| Metadata/resource audit | Passed; zero new FEM and no current train-label/model/state bytes |
| Learned repair / final acceleration | Not established |

At a constructor rejection, each prior fully completed case would have paid one anchor, nine central objectives and sixteen side objectives (26 FEM solves); the rejecting constructor pays one. This gives the listed static possibilities for zero through seven prior cases. The runner buffers the panel until completion, so no runtime count or case identity survived publication. Neither native elapsed time nor a likely first-case explanation is used to assert an exact count. Any earlier buffered measurements remain unretained; they cannot be used as numerical or speed evidence.

## Early-stop metadata audit and resource closure

After the rejection, a separate bounded controller checked only the traceback, command/profile/stdout hashes, unchanged source/release/CI metadata, the static plan, recursive historical guards and absence of published numerical outputs. Its objective/FEM entry points were replaced with rejecting stubs during metadata validation. It did not call the candidate kernel, planned numerical audit or fit-proxy functions. The controller and independent stdlib closer/verifier sources are retained under `audit_sources/` with command-bound hashes. They were procedural early-stop resource closure after the frozen scientific stop, not a revised numerical contract.

Probe/audit cap 600 charged seconds; whole cap 1260 seconds/1 GiB. The failed process has complete native wall/user/system/RSS and pays wall+10 seconds. The full 60-second metadata-plan/audit/closure/controller reservation is paid; actual combined reservation use is separately verified. Profiles use native permissions from the first invocation. Original failure records and `execution_commands.json` remain unchanged. There is no free numerical retry, overwrite or budget reset.

| Process | Native wall | User CPU | System CPU | Peak RSS bytes | Charge |
|---|---:|---:|---:|---:|---:|
| plan | 3.03 | 1.73 | 0.28 | 279527424 | within full 60-second reserve |
| probe | 3.93 | 2.96 | 0.35 | 290684928 | 13.93 |
| abort_audit | 4.71 | 3.59 | 0.41 | 311902208 | within full 60-second reserve |
| closure | 0.13 | 0.03 | 0.03 | 19447808 | within full 60-second reserve |
| verification | 0.06 | 0.02 | 0.01 | 18497536 | within full 60-second reserve |

Failed attempt charge: **13.93 seconds**; complete slice charge: **73.93 seconds**; measured peak: **311902208 bytes**. Combined reservation use: **47.93<=60 seconds**. Complete observed profiles fit the resource limits. Resource-only acceptance does not fill missing numerical fields or establish full training memory feasibility. The latter remains pending.

B4.15/16/17/18 charges84.33/55.99/112.34/86.13 and the original 60,339.394130/58,257.457957 failed cost proxies remain unchanged. No new prospective cost is reported without the required complete timing/setup population. Future fitting and complete experiment amortization must additionally retain this failed attempt and all applicable historical/data/selection/screen/final/replication costs.

## Software checks and CI interruptions

Before source commit, locked dev sync, Ruff, mypy (67 files), **968 tests in 556.98 seconds**, and working/staged whitespace checks passed. The 26 new tests covered complete synthetic uniform-anchor reconstruction, first-order bridge/dtypes, signed gradients, prediction-time FEM exclusion, negative estimate preservation, strict role/subset access, metadata planning, exclusive outputs, fidelity criteria and failed-attempt/cap arithmetic. Their synthetic normalizers used the same unquantized state as the candidate; their pass does not certify compatibility with a nonuniform serialized label normalizer.

GitHub initially cancelled three source checks because hosted runners did not acquire them after multiple attempts. A later quality attempt reached 57% of pytest before its runner received a shutdown signal; no assertion failure was reported before interruption. Only unsuccessful/interrupted checks were retried with unchanged source. Both complete quality jobs, both frontends and the applicable Linux smoke eventually passed before merge; the intentionally skipped feature-push smoke is retained. Original cancelled check runs, diagnostic annotations and interrupted log remain in the release-bound external receipts. All occurred before production label access.

Evidence publication repeats every required repository check and merges only after its exact-head CI passes. The production numerical source, frozen conventions, original failed command/profile, all prior numerical outcomes and P/17 remain unchanged. The two pre-existing untracked user documents are preserved. No fitting, fresh cohort or alternate surrogate/normalizer search starts automatically. A passing versioned repair and independent confirmation remain required before a compatible final contract and B5.

## External reproducibility bindings

| Artifact | SHA-256 |
|---|---|
| `audit_receipts/plan.json` | `b2058c3441e869395c0038f09b6eeeaa3c71d3f120438ec95b81cb7d1c723194` |
| `audit_receipts/production_release.json` | `c87f98ab245f16b1d3f597413de235c1542d695275417baa4971c5543ed986e9` |
| `profiles/probe.time` | `97cf94ebddc4169602be27ca4aba4d3b7483cd24ead2564e3ccb37de1a88e186` |
| `audit_receipts/execution_commands.json` | `9cfb7f2cdd7c9cedb260c0a005d127debc0b6520f40c3ae3492893d08cc2dd27` |
| `independent_abort_audit.json` | `d70531a11edda20271002eb4f4f3085fe5a9e47e3581cf42cf8aa48b2d94f118` |
| `resource_close.json` | `c666b76ea79c4b58df5d774e5197fe71d73118476bd8e659a2406ff4fd455c95` |
| `audit_receipts/closure_profile_verification.json` | `9d6e91bbac52d46a3c50b520fab555888965ee2ea97095277bfb49daff5d49ed` |
| `audit_receipts/postexit_controller_reservation.json` | `4888448836b129ff6297a564625f4f4f443b3247f201f7058ed2379f50bf7e9b` |
