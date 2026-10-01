# B4.3 failure, trajectory and timing diagnosis

Date: 2026-10-01 (America/New_York)

Status: **complete read-only diagnosis; diagnostic acceptance passed. Gate B4
remains failed.** All 48 exposed cases, 720 method outcomes and 162 identical-model
comparisons were retained. A separate arithmetic audit checked 745 candidate /
fallback terminal statuses without a solver call. No original time, failed status,
model, tolerance, ledger or primary was changed. B5 remains sealed.

## Frozen scope and reproducibility

The [B4.3 protocol](../planning/b4_3_failure_cost_protocol.md) and reader were
committed at `b9f79e6c04331fa23b2bfc4ffae5fea4cf7260b4` before reading case bytes
for this diagnosis. Its plan hash is
`a1a3a42deeff9e863b8c2310bc8a907770e0420889c20ca5bd6fa5def7f26392`;
script hash is `0776f4798635e367375a5c863b39c12bdfa1b54e510bb6b674e8dd2c4dd13f40`.
The metadata-only plan opened no index or case and created no output directory.

The reader bound the exact final charged B4.2 index, original complete execution
snapshot and independent audit receipt. Both snapshots contain identical
contexts and case references. Each content-addressed case was read through the
screen guard and checked for hash, size, canonical bytes, source, role, exact
methods/routes, mandatory compliance and recomputed measures. The final
`integrity_failed=true` marker remains retained. The scientific selection was
independently recomputed as zero passing P seeds and no primary.

Generated evidence stays outside Git at
`/Users/keith1117/Documents/TopoLab-data/b4-3-diagnosis`:

| Evidence | SHA-256 |
|---|---|
| `diagnosis.json` | `41e1aebaab43bcc9cc2158441256aa4d588f1d043100829aed81f2740dbd1306` |
| `independent_audit.json` | `fac1d5afbb2503ae2980a239a894a52e1cd1d754fa17433b757d9500602df94c` |
| Independent arithmetic script | `292346091f950ecfd6699c4a786f7a8947cbc774872ade5d7517bf911a30bedf` |

The external receipt directory retains plan, output, audit source, profiles and
resource accounting. Main analysis plus independent audit have a conservative
**50-second** charge against the new 180-second analysis budget and peak RSS
**445,284,352 bytes** against 1 GiB. Whole-command times were 17.03 and 6.54
seconds; the charge also covers metadata startup and receipt/close allowances.
The main `time -l` wrapper returned 1 after successful analysis because its
`sysctl kern.clockrate` read was denied. Its emitted real time and the
interpreter's peak self-RSS are retained; the diagnosis was not rerun. The
independent audit used `time -p` and exited 0. Neither receipt changes the
stopped B3/B4 ledger or extends that experiment's budget.

## Seed 17: numerical savings with unstable observed timing

P/17 had zero terminal failures. Its small-z candidates averaged **0.500483**
of their uniform update counts, yet charged time averaged **1.130297**. On
the same twelve cases, P-without-S/17 used the same P checkpoint, prediction,
projection and solver: every retained scalar trace, recent density state,
terminal vector, metric and status was bit-identical. Its observed small-z
time mean was **0.730870**. The two means lie on opposite sides of the frozen
direction limit, despite identical numerical work.

Two P/17 small-z cases had time ratios 2.620595 and 6.098849 while update
ratios were only 0.589041 and 0.588235. In the latter, at volume 0.5351,
20 candidate versus 34 uniform updates, P/17 refinement took 2.142607 s and
the identical P-without-S/17 refinement took 0.195249 s. This is measured
timing dispersion; choosing the faster repeat would be post-result selection
and cannot repair the old Gate.

Across the complete cohort:

| Identical-model group | Pairs | Spread >=1.25 | Median spread | Maximum spread |
|---|---:|---:|---:|---:|
| Small generalists | 72 | 15 | 1.063105 | 14.423499 |
| Large generalists / shared specialists | 90 | 16 | 1.060145 | 10.502978 |
| Complete | 162 | 31 | 1.061354 | 14.423499 |

Spread is `max(left time,right time)/min(left time,right time)`; 1.25 is
the predeclared descriptive flag, not a new acceptance threshold. All 162
pairs had identical complete retained witnesses, metrics and statuses.
The largest small discrepancy was 0.103883 versus 1.498350 seconds for
P/43 and P-without-S/43. A large-z P/43 case took 134.630886 versus
12.818354 seconds for the identical ablation, exposing a wider wall-time
fidelity problem than small-query overhead alone.

The first 24 cases had 9/84 flagged pairs and median spread 1.026975;
the last 24 had 22/78 and median 1.115760. This is descriptive chronology,
not an independent cohort comparison or proof of a single timing cause.

### Demonstrated recording mechanism and unmeasured costs

The frozen query timer encloses `solve_problem` and its iteration callback.
That callback may call `write_screen_index` every five seconds. Each write
revalidates the full embedded context and all accumulated case summaries,
reopens/parses the prior complete index to enforce append-only rules, and
serializes/replaces the complete index. These costs grow with the retained
prefix and can land inside one method's refinement interval. The flush
timestamp is taken before the write, so write duration also consumes the next
five-second interval. Fixed method order does not balance those boundaries.

No per-callback duration, process CPU time or host scheduling/suspension log
was retained. The original records cannot distinguish checkpoint work from
other wall-time interference, particularly the large 134.63-second outlier.
No precise overhead duration or corrected performance can be inferred.
The diagnosis establishes a recording design problem and numerical repeat
identity; it does not prove that removing writes alone passes B4.

## Seed 29: two different reliability mechanisms

Both failed P/29 attempts used the **generalist**, not the high-volume y
specialist. P-without-S/29 reproduced their exact witnesses and status.

| Failure | Volume / load node `(x,y,z)` | Candidate / uniform updates | Compliance / uniform | Terminal stop | Paid fallback |
|---|---|---:|---:|---|---:|
| Large y | 0.3291 / `(24,10,4)` | 140 / 156 | 1.001438087 | Physical plateau | 38.350586 s |
| Large z | 0.5351 / `(24,6,4)` | 360 / 189 | 0.966561604 | Iteration cap | 45.748211 s |

The y case converged with valid volume but never crossed the `1.001` quality
limit in its recorded trajectory. Its last ten physical changes were at most
0.001158042 and relative compliance improvement was 0.000198012: the frozen
plateau condition was correctly satisfied. Stability did not establish
matched-uniform solution quality. C/29 passed that case at ratio 0.999816630;
A/29 also missed quality, at 1.001056394. The expanded generalist produced
a poorer terminal trajectory here; the precise learning-side cause is not
identified by these comparisons alone.

The z case met the compliance allowance from update 9 and finished with
better compliance than uniform. It still failed convergence at 360 updates:
last design change 0.043083699 and ten-update compliance improvement
0.000427083 exceeded the applicable stopping limits. Its last physical
change maximum 0.002796385 alone was insufficient. C/29 passed in 60 updates;
A/29 also reached 360 without convergence. This is refinement/stability
cost, rather than a terminal compliance gap. No iteration-cap extension or
looser stop is tested or justified by this audit.

Together the two P/29 fallbacks cost **84.098797 s**. Its measured large
time mean was 0.926609. Hypothetically subtracting fallback time gives
0.839421; replacing failed complete attempts by zero-decision-cost uniform
gives 0.797704. Both satisfy the speed-only bounds, but preserve the two
recorded failures and cannot pass the quality/reliability Gate.

## Seed 43: a converged low-quality generalist state

The failed case was large y, volume **0.4631**, load `(24,10,4)`, generalist
route, case
`tlcase-v1-e934fc40079cfa70a01a44e5b62fce3d48607767140c6a85c3b4e40c409431c1`.
P/43 stopped in **65** versus **112** uniform updates at compliance ratio
**1.001407355**, never crossing the 1.001 quality allowance. Volume error
was 9.19e-9. Last-ten physical change 0.002841816 and relative compliance
improvement 0.000199105 correctly satisfied the plateau stop.

C/43 passed in 65 updates at 0.999474326; A/43 passed in 71 at 1.000008875.
P-without-S/43 exactly reproduced the failure. Removing the specialist route
therefore cannot fix this case. The loss/control comparisons motivate an
improved generalist objective, but do not prove that weighting alone caused
the gap. An iteration-cap increase would not affect an attempt that already
stopped at 65. Its successful uniform fallback cost **26.430445 s**; P/43
already met the scale/direction speed limits, so reliable quality is its
remaining scientific condition.

Across all fifteen methods, 17 failures had only a compliance gap, four had
only nonconvergence and four had both. There were no volume-caused failures.
The independent audit recomputed every cause and complete fallback cost.

## Repair sequence and decision

1. **B4.4: separately freeze a finite repair contract; implement and verify
   faithful timing and bounded checkpoint persistence.** Separate the small
   durable progress/resource receipt from the growing immutable outcome
   ledger; preserve atomic ownership, append-only failures, crash/recovery
   charges and the maximum heartbeat interval. Instrument callback/flush,
   CPU and wall durations. Count every query cost, including record work,
   in complete query or explicitly amortized setup totals. Use a fixed
   counterbalanced repeated control on exposed cases, preserving every
   repetition, and require identical numerical evidence. Do not fit a model
   or infer acceleration from this engineering sentinel. Freeze its cases,
   repetitions, criteria, time/RSS caps and stopping rule before execution.
2. **After that sentinel passes, test one new quality/trajectory-aligned
   generalist intervention.** The concrete leading hypothesis is an offline
   sensitivity-weighted **terminal-design** objective using the existing
   independently audited label weights, with unchanged input, network,
   three seeds and specialist. It targets structurally sensitive density
   errors without a paid inference FEM input. Freeze the objective, fit
   budget, selection rule, old-model controls and fresh disjoint development
   screen in the new contract. This hypothesis has no success evidence yet.
   B2.10's weighted update-30 objective failed; a terminal target and current
   coverage make this a different experiment, not evidence of superiority.
3. **Require fresh complete validation before advancing.** Keep the original
   two-scale/direction, quality and fallback obligations, at least two
   passing candidate seeds and one zero-failure primary. Keep all seeds,
   controls, denominators and costs. A repaired timing path cannot by itself
   erase P/29 or P/43 failures. A positive small development result requires
   independent confirmation and a new prospective freeze before B5.

The next slice is **B4.4: new repair contract, timing/checkpoint implementation
and bounded matched engineering verification**. B4.3 supplies its measured
failure list and verification obligations; it does not execute that repair.
Known failed checkpoint selection (B2.20), two-update anchoring (B2.18) and
the existing specialist route are not automatically retuned. No exposed-case
lookup, discarded outlier, better-repeat substitution, alternate primary or
quality/stop tolerance relaxation is permitted as a repair. Uniform remains
the operational default, and no final acceleration claim is established.

## Repository validation

Before the protocol/reader commit, locked dependency sync, Ruff, mypy on all
54 source files, **646 tests** (472.15 s) and `git diff --check` passed.
Eight new synthetic tests cover zero-byte planning, changed-input rejection,
external output separation, failure-preserving bounds, converged-quality versus
nonconvergence diagnosis and equal-state timing discrepancies. No numerical
tolerance changed. The report commit repeated locked sync, Ruff, mypy on
54 source files, all **646 tests** (478.00 s) and the diff check successfully.
Its PR is merged only after every required CI check passes.
