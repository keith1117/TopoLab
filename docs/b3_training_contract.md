# B4.1 fixed fitting and artifact implementation

Date: 2026-10-01 (America/New_York)

The immutable [B3 experiment contract](b3_experiment_contract.md) defines
the recipes, data, model, optimizer, seeds and budgets. This document explains
its implementation; it introduces no additional fitting or selection choice.
The passed [B3.4 data Gate](validation/b3_4_data_gate.md) is a prerequisite.

## Fitting inputs and selection

The CLI binds the exact final B3.4 index checksum, embedded data manifest,
all 608 upstream artifact references, frozen contract/catalog/exposure hashes,
and its actual clean merged source and locked CPU runtime. Planning reads only
metadata, creates no output root and opens no label or checkpoint bytes.
Execution requires implementation loaded from that recorded checkout.

The four recipes execute in `C,P,A,S` order, each with seeds `17,29,43`:

| Recipe | Train labels | Selection labels | Weight-8 train cases | Batches/epoch |
|---|---:|---:|---:|---:|
| C | 468 | 32 | 78 | 59 |
| P | 508 | 32 | 98 | 64 |
| A | 508 | 32 | 0 | 64 |
| S | 488 | 4 | 72 | 61 |

Complete membership is checked before the first byte read. Every individual
label read then uses the membership-specific fitting guard and verifies its
bytes and provenance. Labels are streamed into CPU float32 tensors; complete
solver traces are released after conversion. Only the permitted train and
fit-validation targets enter fitting; no screening query or final artifact is
opened. The specialist uses exactly the four frozen high-volume y validation
cases. Each seed initializes its model and shuffle generator independently.

Training uses per-case design-density MSE normalized by the sum of fixed
case weights in that batch. Epoch training metrics use the same case-weight
denominator. Selection averages unweighted per-case MSE, giving a small and
large physical case equal weight. This differs from a global voxel average.
The earliest strict minimum wins; an equal loss retains the earlier epoch.
Training stops at 200 epochs or 25 consecutive non-improvements. No existing
B2 recipe, network, encoder, solver, quality tolerance or default changes.

## Artifacts and audit

`topolab.b3.training.v1` context binds the full upstream data index and the
actual fitting source/runtime. Its canonical SHA-256 identifies all fits.
Each `topolab.b3.checkpoint.v1` Safetensors file embeds the context hash,
recipe, seed and selected epoch, and contains only the finite float32 model
state. The `topolab.b3.selection.v1` artifact retains every ordered epoch
metric, the selected value/epoch, fit duration and exact checkpoint reference.
Both are content addressed under an external `artifacts` directory.

Readers check canonical JSON, byte hashes/sizes, metadata, exact tensor
names/shapes/dtypes and finiteness. They independently recompute the earliest
strict minimum and the frozen patience stop from each complete history.
Audit reloads selected weights and reproduces their recorded validation MSE.
The audit succeeds only for all twelve ordered fits, with all histories and
checkpoints retained. It is a fitting completeness Gate; the 720-outcome B4
screen and deployable-primary selection remain a later independent slice.

## Recovery and resource accounting

One nonblocking filesystem lock owns an external output root. The stable
`b3_training.json` index preserves the exact completed-fit prefix, attempted
epochs, cumulative elapsed time, peak RSS and permanent failure flags.
Completed fits are verified and skipped on resume. A transport interruption
restarts only the pending same-recipe/same-seed fit from scratch; no optimizer
resume contract is introduced. Every repeated attempted epoch remains charged
against the 2,400-epoch total. Numerical, artifact and resource failures stop
the program and cannot authorize another fit or a reset budget.

Attempted epochs are durably recorded before updates. Resource checkpoints
are checked before each batch and flushed at least every five seconds.
Graceful interruption closes and charges the invocation. A hard-crash resume
conservatively adds elapsed wall time since the last durable checkpoint,
including downtime. Loading, serialization, verification and audits all
contribute to the same 7,200-second and 4-GiB caps. Supplemental independent
audit/whole-command overhead must also be added to this ledger before the
final fitting Gate is reported. Generated artifacts and audit receipts stay
outside Git.

From a clean merged checkout with the frozen lockfile synchronized:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=src \
uv run python -m topolab.b3_training_cli \
--data-root /absolute/external/b3-v1-data \
--output-root /absolute/external/b3-v1-fits
```

Omitting `--execute` gives a read-only plan. Add `--execute` for the fixed
program, or `--audit` for verification of existing fits without fitting.
Exit 0 in execution/audit mode requires the complete fitting Gate, 1 records
an incomplete/failed Gate, and 2 reports a preflight or integrity error.
Final data remain sealed. Uniform remains the operational default.
