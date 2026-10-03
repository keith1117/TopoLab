# B4.10 fixed post-plateau polish probe

Prepared: 2026-10-03 (America/New_York). Freeze before production optimization.

Metadata plan SHA-256:
`6583e32416d789e719e6bccc9707e7083d30acfefb7c2fc2b5ae314fd77aa983`.

## Identity and compatibility

`topolab.b4_10.post-plateau-probe.v1` tests one candidate refinement policy,
`topolab.b4_10.large-y-post-plateau.v1`. The prospective primary remains P/17.
There are no fits, checkpoint/seed substitutions, length searches, threshold
searches, source label changes or final-artifact access. B4.2, B4.6 and B4.8
remain failed. Uniform stays the operational default.

All six B3 numerical-anchor modules remain byte-identical to the frozen anchor.
The original physical-plateau solver first executes normally. An explicit
query-local continuation then reuses its existing FEM, density-filter gradient
and OC operations, without changing uniform labels, mandatory references,
fallback semantics or P/W/C/S checkpoint inputs. The same-quality terminal
audit remains applicable. This is a new candidate policy, not the original B3
final experiment or authorization to reuse its final contract unchanged.
The original B3 manifest anchor and membership/population guards are retained.

Before any model/label bytes, bind all eleven B4.8 metadata receipts and the
three B4.9 diagnosis/audit/resource receipts in `b4_polish_probe.py`; retain the
exact original indented plan/release serialization. Then retain the existing
B4.7/B4.6/B4.5 fixed-fit guards. The B3 labels and twelve selected C/P/S/W
checkpoints are unchanged; nearest neighbor still opens the complete 528-label
training population through its membership-specific guard.

## Candidate rule

Apply only to P generalists on mesh `(24,12,6)`, y load, volume below 0.55.
Require the first original solver stop to be converged with final design change
strictly greater than 0.01 and the existing physical-plateau signal: eleven
post-update states, ten physical-density changes at most 0.01 and nonnegative
ten-update relative compliance improvement at most 0.0002. Design-change stops
have precedence and receive no polish. All specialist, z, small-grid, C/W and
non-ML paths remain unchanged. Apply prospectively to every qualifying P seed
and stop, including originally accepted cases. Matched uniform compliance is
never supplied to the continuation or consulted as an online oracle.

Re-solve the input terminal state, verify exact compliance identity, and perform
exactly **20** more existing OC/FEM updates. Do not stop at intermediate quality
or convergence crossings. Keep the **360 total-update cap**. If fewer than 20
updates fit, retain the truncated terminal witness as nonconverged and pay the
original fresh uniform fallback. After the full twenty, convergence must again
meet the unchanged design-change or physical-plateau rule. Volume error <=0.005,
compliance <=1.001 times matched reference, finiteness and all numerical audits
remain unchanged. No accepted state or test tolerance is loosened.

Store a content-addressed prepolish witness, exact first-stop count, trigger,
performed count and postpolish witness digest for every P generalist. Retain the
entire scalar trace and last eleven density states. Repeated attempts retain
charges and cannot overwrite a differing continuation receipt. The original
query-phase and outer wall/CPU envelopes include the input re-solve, all twenty
updates, callback/receipt I/O, decisions and fresh fallback. Each query keeps
the conservative additional one-second recording allowance.

## Exposed regression sentinel and stop rule

Nine exact B4.8 cases are selected using already published B4.9 metadata.
Coordinates below are the small-grid `(y,z)` node indices; double them on the
large grid. Case IDs and all assignments are frozen in the metadata-only plan.

| Mesh scale | Direction | Volume | Position | Purpose |
|---|---|---:|---|---|
| large | y | 0.5413 | (3,1) | fixed P/17 failure |
| large | y | 0.4703 | (1,1) | P/29 and P/43 plateau failures |
| large | y | 0.4703 | (1,2) | other P/29 plateau failure |
| small | z | 0.4703 | (3,1), (3,2) | unchanged P/29 design-change failures |
| large | y | 0.3353 | (3,1) | successful generalist control |
| large | y | 0.6013 | (3,1) | shared specialist control |
| large | z | 0.4703 | (3,1) | other direction control |
| small | y | 0.4703 | (3,1) | other scale control |

Execute nine fresh unchanged uniform references and all 108 queries: uniform,
physics heuristic, nearest neighbor, C/P/W seeds 17/29/43 with the unchanged S
route. Uniform goes first; rotate the other eleven by the first eight hex digits
of SHA-256(`VERSION + ':' + case_id`) modulo eleven. Case order is sorted ID.
Compare every control numerical status, witness, metrics and NN identity against
immutable B4.8, excluding timings. Every P prepolish witness must be exactly its
original B4.8 witness. Every originally accepted P attempt must remain accepted.
Both small-z negative failures must retain their original failed status/state.
All **four** known large-y failed P attempts must become quality successes;
P/17 must have zero failures/fallbacks across the nine cases. On the four
large-y generalist cases, the fixed P/17 mean paired charged ratio and ratio of
charged sums must both be <=1.0 versus this sentinel's uniform queries. This
bounded diagnostic cost cap does not substitute for the fresh-panel speed Gate.

Complete independent FEM/filter terminal audits, prepolish/policy identity audits
and a separate raw-JSON arithmetic/continuation audit before progression.
**Any completeness, integrity, resource, identity, quality or cost failure stops
the slice and keeps all 48 fresh cases sealed.** No retest with changed length,
seed, sentinel subset, timing convention or acceptance rule is permitted.

## Conditional fresh development panel

Only after the independently audited sentinel passes, execute 48 physically
disjoint cases: both fixed meshes, y/z directions, volumes
`(0.3367,0.4717,0.5427,0.6027)`, positions `(1,1),(3,1),(5,2)`.
Check physical fingerprints against every historical exposure, the complete B3
catalog and all B4.5/B4.6/B4.7/B4.8 cohorts before numerical work. Freeze 48
uniform references, all 576 twelve-method queries and the same order rule.
No selection or retraining follows from the panel. Require the unchanged
two-scale mean <=0.9, all four direction means <=1.0, matched reliability,
non-specialist-y and non-ML comparisons for at least two P seeds, pooled
middle/high-volume large-y successes >=6/9 each, and zero-failure fixed P/17
primary eligibility with both scale charged-sum ratios <=0.9. A passing panel
still requires a separately frozen independent confirmation before B5.

## Source, resources and publication

Execute only from clean, CI-passed **merged** source. Output is the separate
external sibling `b4-10-post-plateau-polish`, with one bound context and
`sentinel`/`fresh` children. Metadata-only planning opens no artifact bytes and
performs no solver call. Each cohort has single-writer, hash-chained stages:
reference 3,600 s, screen 21,600 s, terminal/input audit 3,600 s, policy audit
3,600 s, each at 2 GiB. Each raw-JSON audit has a 1,800-second cap; closure has
180 seconds. The **whole slice** is capped at 43,200 charged seconds / 2 GiB,
including all startup, failed/recovered attempts, publication, whole-command
floors and ten-second close allowance per process. Stop before fresh execution
if its maximum reserved stage budgets plus remaining audit/closure allowances
cannot fit the remaining whole-slice budget. No generated artifact enters Git.

Retain all failed decisions and protected historical indices. Publish exact
source/plan/receipt hashes, production and independent classification counts,
charged costs, resource closure, local required checks and final-head CI. If
the sentinel or fresh Gate fails, B4.11 is a bounded read-only failure/cost
review before another method-class decision; if both pass, B4.11 is an
independent larger fixed-policy confirmation. Neither outcome authorizes a
polish-length search or final access.
