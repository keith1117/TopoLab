# B4.2 fixed development screen and prospective freeze

Date: 2026-10-01 (America/New_York)

This implements Section 6 of the unchanged [B3 contract](b3_experiment_contract.md).
The passed [B3.4 data receipt](validation/b3_4_data_gate.md) and
[B4.1 fitting receipt](validation/b4_1_fixed_fitting.md) are prerequisites.
It introduces no solver, fitting, workload, tolerance or selection change.

## Inputs and permitted access

The screen binds the exact final B4.1 training-index checksum
`229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7`.
That index transitively binds all twelve checkpoints/histories, every upstream
data reference and the passed B3.4 data index. The actual current data-index
bytes must also match that receipt. Its context records the clean merged
screening source, frozen numerical anchor, lockfile and Apple CPU runtime.

Planning opens only index metadata. It creates no output root, loads no model
or label, and invokes no solver. Execution loads and verifies all twelve fixed
models. It authorizes the complete 528-label NN training population before
opening its first byte, then streams labels into the two original ten-channel
NN indexes. Same-shape lookup retains float64 MSE and case-ID ties. Neither
fit-validation labels nor screening-reference bytes enter a query.
Screening uses only the reference compliance metadata in the immutable data
index. Final artifacts remain forbidden.

## Queries and numerical evidence

Visit all 48 screening cases in canonical case-ID order. For each case, run:

1. Fresh timed uniform, with compliance matching its mandatory B3 reference
   at `rtol=1e-9,atol=0`.
2. Physics heuristic and all-train nearest neighbor.
3. C, P, A and P-without-S, each in seed order `17,29,43`.

This retains 15 outcomes per case, 720 in total. C/P/A use same-seed S on the
frozen large-y high-volume route; P-without-S always uses its P generalist.
The reusable learned query policy rejects unsupported x direction before
inference and charges its fresh uniform; B4's fixed y/z cohort has no rejection.
Final hash rotation is a separate B5 rule and is not applied to B4.

Each query records routing, setup, projection, refinement and independent
quality-decision time. Failed candidates retain their phase/type, finite
diagnostic metrics and available terminal witness. They pay a separately
executed uniform fallback, including every phase and reference-agreement
decision. Rejection and candidate failure remain distinct. Resource stops
propagate through both attempts rather than becoming a candidate fallback.
Uniform-reference or operational-fallback failure is terminal for this screen
and retains the partial failed case; it cannot authorize a replacement.

Numerical acceptance keeps convergence within 360 updates, finite state,
independent terminal compliance at `rtol=1e-9`, the `1.001` matched-uniform
quality factor and `0.005` physical-volume error. A versioned compact witness
keeps full terminal densities/displacement/reactions, every scalar history row
and the last eleven full density states. This is sufficient to reconstruct
terminal filtering, volume, density-change and physical-plateau evidence,
without retaining all earlier density vectors. Parsing checks state/trace
consistency; the complete post-execution audit reconstructs filtering and
independently re-solves every accepted and operational terminal state.
Failed attempts remain failed and are not counted as accepted numerical evidence.

## Atomic recovery and resources

One nonblocking filesystem lock owns a separate external screening root.
Each complete case is content addressed as one canonical outcome artifact,
and the stable `b3_screen.json` index appends its reference and independently
reconstructible measures. A terminal failed case retains its method prefix
and fatal status. Every referenced outcome is checksum, size, role, source
and summary verified before the index publishes it.

Completed cases are immutable and skipped on resume. An interrupted case
reruns all its methods with new measured times. Its earlier work remains in
cumulative charges and its durable attempted-case count. A hard crash charges
the entire unclosed interval, including downtime. Checkpoints flush at least
every five seconds through solver callbacks and before each new case.
Partial model/index loading is tracked as setup cost, including unclosed
setup intervals on recovery. Integrity, numerical and resource failure flags
cannot be cleared.

All loading, outcome serialization, record verification, restarts and audit
work count toward the 21,600-second and 2-GiB stage caps. The CLI reserves
10 seconds per invocation for final summary/freeze serialization and flush;
whole-command profiles and supplemental independent audits must be reconciled
into the same cumulative ledger before final acceptance. Artifact persistence
and supplemental audit are stage costs; they do not replace query-phase costs.
Generated artifacts, receipts, profiles and audit code stay outside Git.

## Prospective selection and freeze

The decision recomputes every paired ratio from complete charged query time,
checks operational metrics, and retains all fifteen method summaries.
It applies all frozen scale/direction, matched-control failure, non-specialist-y
failure, non-ML mean, pooled large-y quality-cell and two-passing-P-seed rules.
The primary additionally has zero failures/fallbacks and strict matched-C gain.
Ties use worst scale mean, worst direction mean, overall mean, then `17,29,43`.
Neither a control nor an ablation can replace an ineligible P panel.

Only a passed complete B4 Gate produces `topolab.b3.freeze.v1`. The artifact
embeds the complete screening index/context, all twelve fitting references,
prospective selection table, selected G/S seed, actual source/runtime and
the exact preregistered statistics specification. Its checksum binds the
closed resource ledger and all retained outcomes. Supplemental audit charges
may produce a new checksum before final access, preserving the same context,
immutable case references, comparisons and seed. A later reader must match
the final freeze to the final audited ledger; an older resource snapshot is
not final acceptance. A failed Gate leaves final evidence sealed.

From a clean merged checkout with locked dependencies synchronized:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=src \
uv run python -m topolab.b3_screen_cli \
--data-root /absolute/external/b3-v1-data \
--fit-root /absolute/external/b3-v1-fits \
--output-root /absolute/external/b3-v1-screen
```

The default is read-only planning; add `--execute` for the fixed screen or
`--audit` for existing outcomes without new queries. Exit 0 requires the
complete B4 Gate and freeze, 1 records an incomplete/failed Gate, and 2
reports a preflight or integrity error. Uniform remains the operational default.
