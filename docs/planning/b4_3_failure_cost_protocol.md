# B4.3 bounded failure and cost diagnosis

Date: 2026-10-01 (America/New_York)

This read-only slice diagnoses the exposed B4.2 screen and specifies the next
repair mechanism. It cannot clear the failed B4 Gate or open B5. Any repair
needs a separately versioned finite experiment and prospective verification.
The plan is frozen before reading case-outcome bytes for this diagnosis:
`topolab.b4_3.failure_cost.v1`, SHA-256
`a1a3a42deeff9e863b8c2310bc8a907770e0420889c20ca5bd6fa5def7f26392`.

## Immutable inputs

Bind source `4279d20c4922cc2cbfaba0bca722aba8868cd914` and these receipts:

| Input | SHA-256 |
|---|---|
| Final charged B4.2 index | `a647f420cb2d498c961a6e8ca965511b4a18e33e26056b10cf987d989df8a421` |
| Original complete execution snapshot | `89a7e66ce2c61294c8dcf36585965d04ffeabe1a00b479cf5bd1843427bd588c` |
| Independent audit receipt | `55bd68b3786b56e30cd74d584f7603e40ed3adf0d701bd9aba62b5cc5b59cab0` |

Require identical contexts and all 48 immutable case references across both
indices, closed charges, the retained permanent integrity marker, and the
complete failed scientific selection decision. The original numerical audit
remains prior evidence; this slice does not independently re-solve FEM states.

Read all 48 cases / 720 outcomes through the existing screen access guard,
verifying checksum, size, canonical bytes, role, source, mandatory compliance,
route, method order and recomputed measures. No label, checkpoint or final
artifact bytes are permitted. Keep the B4.2 indices and artifacts unchanged.

## Fixed analyses

1. Diagnose every candidate failure separately: convergence, terminal
   compliance against `1.001 * uniform`, physical volume, iterations,
   stopping evidence and complete charged fallback. Retain scalar trace
   samples at updates 1, 10, 30, 60, 120, 240 and terminal, as available.
   Full density evidence is available only for the final eleven states.
2. Summarize all fifteen methods by scale/direction: paired time,
   candidate/uniform iteration ratio, refinement time, failures and fallback.
   Keep case/volume/load-position detail for mechanism diagnosis.
3. Compare P with P-without-S on every generalist case, and C/P/A pairwise
   on every shared-specialist case, for each seed. Require bit-identical
   retained numerical witnesses, metrics and status. Retain both measured
   times; summarize spread, using 1.25 as a descriptive timing-spread flag.
   These repetitions do not identify the causal duration of a checkpoint.
4. For P/17, P/29 and P/43 compute three arithmetic cost scenarios using
   each case's own uniform denominator: measured; subtract full fallback
   time; replace a failed candidate's entire cost with exactly uniform time.
   The latter two are optimistic diagnostic bounds. They preserve observed
   failure counts, authorize no method and cannot satisfy the old Gate.
5. Inspect the frozen runner's timing/recovery code and independent
   quality acceptance. Determine a bounded repair sequence: establish
   faithful complete timing and record checkpoint costs; address terminal
   reliability; address residual refinement cost if still required. Distinguish
   demonstrated mechanisms from hypotheses and missing measurements.

## Execution and acceptance

Use a clean committed tracked checkout; record its revision and script hash.
The committed diagnostic script remains reproducible source; generated JSON,
profiles and independent audit scripts remain external. The default plan reads
no indices or cases and creates no output directory. Execution writes only a
new, separate external diagnosis directory, refuses overwrites and uses one
BLAS/OpenMP thread. The independent analysis budget is 180 seconds / 1 GiB,
including startup, audit work and a conservative 10-second close allowance.
Its receipt does not rewrite or extend the stopped B3/B4 experiment ledger.

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=src \
uv run python scripts/b4_3_failure_cost.py \
--screen-root /absolute/external/b3-v1-screen \
--output-root /absolute/external/b4-3-diagnosis
```

Add `--execute` for diagnosis. Independent arithmetic must reproduce phase
sums, all seed/stratum means, failure causes and same-model comparisons.
Acceptance requires complete guarded reads, unchanged inputs, resource bounds,
and a concrete repair/verification sequence. It establishes diagnostic evidence
only. No solver run, fit, retiming, tolerance adjustment, route search,
primary substitution or final access occurs in B4.3. Uniform remains default.
