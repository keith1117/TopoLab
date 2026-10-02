# B4.5 sensitivity-weighted terminal generalist

Date: 2026-10-01 (America/New_York)

Identity: `topolab.b4_5.weighted-terminal.v1`. This is a new finite development
experiment. The failed B4.2 contract, its permanent flags, timings and failures
remain immutable. B5 stays sealed; uniform remains the operational default.
The contract and runner must merge with passed CI before production execution.

## One intervention and fixed inputs

B4.3 identified two converged generalist compliance gaps and one generalist
nonconvergence. B4.4 repaired recording overhead while preserving those failures.
Test one hypothesis: emphasizing terminal-design errors in compliance-sensitive
regions improves the learned start. Previous B2.5/B2.10 element weighting failed;
B2.26 weighted **cases**, rather than elements. These negative findings remain
relevant and do not imply this new intervention will pass.

Reuse only the complete audited B3 expanded membership: 508 train and 32
fit-validation labels. Bind B3 data-index SHA
`b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26`
and B4.1 training-index SHA
`229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7`.
Authorize complete membership before any bytes; individual label reads retain
the B3 guard. Use the already audited float32 sensitivity weights at each
terminal design: mean-normalized absolute design compliance derivative,
clipped to [0.25,4], then renormalized to mean one. No new label, input feature
or query-time sensitivity solve is introduced.

For each training case i, set L_i = mean_e(w_ie * (prediction_ie-target_ie)^2).
The batch objective is sum_i(a_i L_i)/sum_i(a_i), keeping P's a_i=8 for y at
volume >=0.5 and 1 otherwise (98/410 cases). Retain thirteen-channel vector
input, 26,433-parameter context CNN, terminal **design** targets, CPU float32,
AdamW and shape-bucketed batch size 8 from B3. Fit exactly seeds 17,29,43
from scratch, 200 epochs maximum, patience 25, identical RNG/shuffle schedule.
Selection remains earliest strict minimum **unweighted equal-case** MSE on
all 32 validation cases. No additional configuration, epoch capture, seed,
checkpoint or selection search is permitted. New versioned checkpoint wrappers
bind source, plan, data and objective; historical artifacts keep their identities.

Reuse same-seed fixed B4.1 S on large (24,12,6), y, volume >=0.55.
Use the new W generalist elsewhere. Fixed C/P and S controls are unchanged.
All queries retain the 360-update physical-plateau solver, A3 ordering,
projection, independent compliance rtol=1e-9, volume error <=0.005 and terminal
compliance <=1.001 times uniform. Failures remain failed and pay fresh uniform.

## Fresh development evidence

Freeze all 48 cases before fitting: Cartesian product of volumes
0.3317,0.4657,0.5397,0.5977; small-grid load positions (y,z)=(1,2),(3,1),(5,2);
y/z directions; (12,6,3)/(24,12,6) grids, with doubled large-grid load nodes.
Other problem fields follow B3's independently implemented cantilever definition.
Sort by full case ID. Require unique budget-insensitive fingerprints absent from
all 1,376 historical exposure entries and every B3 catalog definition, including
sealed final definitions. Metadata-only comparisons never open final bytes.

First complete and independently audit all 48 mandatory uniform references.
A failed reference stops before screening, remains recorded and cannot be
replaced. Then execute 12 methods per case: fresh timed uniform, physics heuristic,
528-train-label nearest neighbor, C/17,29,43, P/17,29,43, W/17,29,43: 576 outcomes.
Uniform first; rotate the other eleven by SHA256 of
`topolab.b4_5.order.v1:` plus case ID, first eight hex digits modulo eleven.
Check timed/fallback uniform compliance against mandatory reference at rtol=1e-9.
All methods and seeds remain reported. The old exposed failure cases are not
checkpoint-selection or new-screen inputs.

## Timing, artifacts and recovery

Use B4.4 outer wall/process-CPU envelopes, including callbacks, terminal witness
packaging and all fallback. Use only the compact five-second heartbeat; omit the
engineering sentinel's forced first-update stress write. Record callback costs
inclusively. Each query additionally pays a conservative **1.0-second recording
allowance** for durable pending, result serialization/publication, immutable unit
publication and its small completion receipt. Verify their measured combined
wall cost <=1.0; an overrun permanently fails this evidence Gate. Apply the
identical allowance to uniform and every comparator; faster candidates are moved
toward ratio one. Ratios use outer query wall plus this allowance. The resource ledger adds the
full allowance before each attempted query **in addition to actual elapsed**
wall, conservatively counting actual recording and its allowance; repeats pay
both again. Retain actual
recording wall separately, never subtract callbacks or fallback. One-time model
and NN loading, offline reference generation, independent audits and resource
closure are separately charged stage costs. Report all stage residuals and actual
whole-command floor. This boundary cannot retime historical B4.2.

Separate external fit/reference/screen/audit roots use a context-bound, locked,
append-only journal. Large outcome artifacts are content addressed; journal
units hold small references and hashes. Durable epoch attempts precede training;
all repeats count against 600 attempted epochs. Interrupted pending work may
restart only unchanged work with downtime and prior compute charged. Published
units are reconciled without rerunning. A completed query without its recording
receipt cannot supply scientific timing; stop, retain costs and keep final sealed.
Terminal, provenance, integrity and resource failures are permanent; no resets.

Bind a clean merged implementation, unchanged B3 numerical anchor and lockfile,
Apple M2, Python 3.12.10, one BLAS/OpenMP/PyTorch intra-op thread and eight inter-op
threads. Default CLI planning is metadata only, opens no label/model bytes,
creates no root and calls no solver. Execution/audit requires explicit mode.
Protect all original data/fit/screen/engineering and final roots from writes.

| Stage (including all restarts, startup, audit and closure) | Seconds | RSS |
|---|---:|---:|
| Three fits and selected-artifact checks | 3,600 | 4 GiB |
| Mandatory references | 3,600 | 2 GiB |
| Complete development screen | 21,600 | 2 GiB |
| Independent full audit and resource closure | 3,600 | 2 GiB |
| Total new version | 32,400 | Per-stage bounds |

## Frozen Gate and disposition

Require all fits, histories, references, 576 outcomes and every independent
terminal/artifact/charge audit. Zero accepted or operational quality violations.
For at least two W seeds require scale arithmetic means <=0.90, all four
direction means <=1.0, failures <=2 and no more than both matched C and P,
non-specialist-y failures no more than both C and P, and overall mean below
both non-ML methods. Pooled W large-y terminal successes must be >=6/9 for
both middle volume 0.5397 and high volume 0.5977.

A prospective development primary additionally has zero failures/fallbacks,
overall mean below matched C, and improves over matched P either in overall
charged mean or failure count. Choose by lowest worst scale mean, worst
direction mean, overall mean, then seed order 17,29,43. At least two passing
seeds plus an eligible primary and both quality cells are necessary for the
bounded development Gate. Failed/ineligible seeds remain in every table.

A pass permits **B4.6: separately frozen larger physically disjoint confirmation
with unchanged artifacts and route**, before any new final contract/freeze or
B5. A failure permits **B4.6: read-only learned reliability/refinement diagnosis
of the complete new evidence**, followed by a separately registered mechanism;
it does not permit B5, extra fits or tuning on this screen. Report the actual
branch of this rule and wait for the user's next-slice instruction.
