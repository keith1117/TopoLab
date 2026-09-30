# B3.3 guarded data materializer

Date: 2026-09-30 (America/New_York)

Status: **B3.3 implementation Gate passed.** B3 label/reference
contracts, external artifact IO, charged recovery, independent auditing,
and the explicit execution entrypoint are implemented. **Gate B3 data
remains pending** B3.4's real 560 labels and 48 screening references.
No production B3 case was optimized, no model was fitted, and no final
artifact was opened or generated in this slice. Uniform remains the
operational default; later final Gates are still required for acceleration.

## Frozen identity and numerical behavior

The [B3.1 contract](../b3_experiment_contract.md), catalog and historical
exposure hashes remain unchanged. The new `topolab.b3.dataset.v1`
manifest contains all 752 definitions but permits exactly 608 data tasks:
528 train labels, 32 fit-validation labels, and 48 screening uniform
references. Final-ID and final-OOD definitions are metadata only.
Every task retains the frozen 360-update cap and null case initialization.
Generation reparses the manifest and exact entry before calling a solver,
including objects forged through constructor-bypassing copies.

The data context binds the experiment/solver versions, contract/catalog/
exposure hashes, numerical anchor, clean merged source revision, frozen
Python 3.12.10 and lockfile hash, and non-sensitive CPU runtime metadata.
The CLI checks installed package versions against `uv.lock`, requires
the preregistered Apple M2 host, fixes Torch intra/inter-op threads to
1/8, and requires all four BLAS/OpenMP environment variables to be 1.
Core numerical source files must match the frozen anchor. All artifacts
in one root must retain the same source and runtime identity.

The existing B2.4 projected-float32 uniform initialization, physical-
plateau solve, float32 conversion, filtered physical state, and sensitivity
analysis were extracted into shared helpers. Their numerical equations,
tolerances, and stopping policy did not change. An independent before/
after execution of one historical small B2.4 volume-0.2 case produced
identical canonical label bytes (13,885 bytes):

```text
609cc94e6067764505789392cd3b905a70efd7d48e3b911488f00454995929ba
```

This historical parity check used the original local module saved outside
Git and the changed module, with one-thread numerical execution. It is
refactor evidence, not a B3 label or acceleration result. Existing B2.4
and B2.10 regression tests also passed.

## Artifact and audit contracts

| Record | Contents and independent checks |
|---|---|
| `topolab.b3.label.v1` | Train/fit-validation role, exact case/provenance, full-precision terminal result and trace, plus exact float32 design/physical/sensitivity vectors with `(1,nz,ny,nx)` shape metadata |
| `topolab.b3.uniform-reference.v1` | Screening role, case/provenance and full-precision result/trace; no stored fitting target |
| `topolab.b3.data-artifact.v1` | Authorized physical origin, kind/case, manifest/source bindings, byte count, SHA-256 and fixed content-addressed path |
| `topolab.b3.materialization.v1` | Complete manifest, canonical outcome prefix, immutable success/failure receipts, cumulative time/peak RSS, resource/integrity flags and ordered audit receipts |

Parsing reconstructs filtered physical states, checks vector sizes,
finiteness, trace order, terminal consistency, density bounds, physical
volume and the eleven-state physical-plateau witness when applicable.
Independent audit re-solves full-precision compliance at relative
tolerance `1e-9`, separately re-solves serialized-state compliance,
and reproduces serialized sensitivity weights exactly. Full-precision
uniform compliance and stored-state compliance remain separate fields.
The physical-volume tolerance remains `0.005`; no tolerance was loosened.

Canonical JSON artifacts are flushed and published atomically under
`artifacts/{kind}/{case_id}/{sha256}.json` outside the repository. Readers
validate metadata/permissions before opening bytes, then verify byte
count, checksum, schema, canonical serialization, and embedded provenance.
Symlink escapes, stale identities and historical schemas are rejected.
The complete NN reader still requires all 528 train labels before its
first byte read and preserves canonical case-to-content pairing.

## Recovery, costs, and execution

One nonblocking filesystem lock permits one writer per root. The stable
`b3_materialization.json` path prevents a changed identity from silently
starting another budget in that root. Outcomes must form the exact
canonical task prefix; completed outcomes, terminal failures, resource
charges and failure flags cannot be removed or rewritten. Resume checks
all retained successes before another solver call. Unexpected interruption
leaves the active case pending; a convergence/quality failure retains a
terminal failure and its denominator. No failed case is replaced.

Elapsed generation, serialization, checkpointing, restart preflight and
audits accumulate across invocations. Solver callbacks check resource
limits every update and publish resource checkpoints at least every five
seconds while iterating. A normal exception closes and charges its session.
For a hard crash without a closing receipt, resume conservatively charges
the wall interval since the last durable checkpoint, including downtime;
this can exhaust the budget and never discounts unrecorded work. Peak RSS
is cumulative. Exceeding 14,400 seconds or 2 GiB stops pending work and
permanently fails the resource gate. Integrity/audit failures are also
retained and prevent continued generation. Audit-only mode rechecks existing
successes without generating pending cases.

From the clean merged label-source checkout, first plan:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=src \
uv run python -m topolab.b3_dataset_cli --output-root /absolute/external/b3-data
```

Default planning reads metadata only, creates no output root, and opens
no label/reference bytes. Add `--execute` for generation and auditing or
`--audit` for an existing index. Both require an external root; execution
must load its implementation from the recorded checkout. Exit 0 requires
the complete audited data Gate, 1 reports an incomplete/negative Gate,
and 2 reports a preflight or integrity error. All 560 labels and 48
references must succeed and pass their independent checks and fixed
role/mesh/direction/volume counts; partial success cannot pass Gate B3.

## Verification and next slice

The 62 new tests use explicitly synthetic convergence receipts on independently
FEM-solved states, metadata-only complete-population scaffolding, and
failing/spying callbacks. They exercise numerical corruption, schema and
provenance rejection, authorization-before-open, complete NN pairing,
canonical prefixes, immutable failures, pending interruption/recovery,
resource exhaustion, hard-crash charges, independent-audit failure, writer
locking, clean merged-source/runtime checks, and side-effect-free planning.
These fixtures are never evidence that production B3 cases converged.

Required locked sync, Ruff, mypy (45 source files), all **561 Python tests**
in `280.84 s`, and diff checks passed before commit. An additional focused
check passed the synthetic eleven-state plateau witness and its rejection
when compliance improvement exceeds the frozen bound. The PR must pass all CI
before merge. No generated dataset, parity audit, run receipt, cache,
checkpoint, secret or device identifier enters Git.

The next independent slice is **B3.4: execute the fixed 560-label and
48-reference program from one clean merged revision, then independently
audit complete quality, provenance, strata and cumulative resources**.
B4 fitting may begin only if that separate Gate B3 passes.
