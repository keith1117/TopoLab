# B4.1 fixed fitting and artifact audit

Date: 2026-10-01 (America/New_York)

Status: **B4.1 fitting completeness, artifact and resource Gate passed.**
All twelve fixed fits, complete histories and selected checkpoints passed
production and independent audits. The [B3 experiment contract](../b3_experiment_contract.md)
and [B3.4 passed data receipt](b3_4_data_gate.md) are unchanged. Gate B4's
screening and prospective primary selection remain open. No screening query
or final artifact was generated or opened; uniform remains the operational
default, with no acceleration claim.

## Frozen execution and provenance

The [fitting implementation](../b3_training_contract.md) first passed all
local and CI checks and merged in PR #102. Production then ran from clean
merged source `428c96fd718a78496bcfafcc85a3d82401925ab4`, in a separate
checkout with no tracked or untracked changes. The read-only plan checked
the exact B3.4 receipt, recipe counts, seeds and budget without opening a
label or creating the previously nonexistent output root.

| Binding | SHA-256 / revision |
|---|---|
| Fitting source | `428c96fd718a78496bcfafcc85a3d82401925ab4` |
| Label source | `cc151b014f9034ccc7093ef592021003d7dec252` |
| Frozen experiment contract | `452a6c1b3664e007a258a914877c935f333c1823f3ec3d977ee0d09583129af8` |
| Catalog | `441b7f74e41489e0ea29cf3ac8ee1da86da499370b504eac2067ee787480bd5c` |
| Historical exposure ledger | `5ab3f2d57d390b804c4e5157f41f206155a4bee7d31a6c4edcbc614c44e1a7b7` |
| Lockfile | `9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292` |
| Passed B3.4 data index | `b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26` |
| Complete fitting context | `122ec9e18c1b0c04c9ea1ac318ad7c5ee0dde208dba6c5de15b10c35f1ae0fae` |

The data root was `/Users/keith1117/Documents/TopoLab-data/b3-v1-data`;
the new fitting root is `/Users/keith1117/Documents/TopoLab-data/b3-v1-fits`.
The fitting context includes the complete immutable upstream index, binding
every input reference and its original source/runtime. Its checksum was
unchanged after execution and both audits. All generated weights, histories,
indices, logs, profiles, audit code and receipts remain outside Git.

Runtime: Apple M2 CPU, arm64, Darwin 25.5.0, 8 GiB host RAM, Python 3.12.10,
NumPy 2.5.3, SciPy 1.18.1, Torch 2.14.0, Pydantic 2.13.5 and Safetensors 0.8.0.
All four BLAS/OpenMP variables and Torch intra-op threads were 1; Torch
inter-op threads were 8. Every model and fitting tensor was CPU float32.
No architecture, optimizer, data membership, weight or seed was tuned.

The command from the clean source checkout was:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 PYTHONPATH=src \
UV_PROJECT_ENVIRONMENT=/Users/keith1117/Documents/TopoLab/.venv \
UV_CACHE_DIR=/tmp/topolab-uv-cache \
/usr/bin/time -l /Users/keith1117/.local/bin/uv run --no-sync python \
-m topolab.b3_training_cli \
--data-root /Users/keith1117/Documents/TopoLab-data/b3-v1-data \
--output-root /Users/keith1117/Documents/TopoLab-data/b3-v1-fits --execute
```

The lockfile was synchronized before execution. `--no-sync` reused that
environment, while `PYTHONPATH=src` loaded the recorded clean implementation.
The same command without `--execute` produced the read-only plan. Its first
sandboxed attempt could not read `sysctl` CPU metadata, opened no fitting
artifact and created no fitting root. A subsequent permitted plan passed;
both attempts' measured time is retained in the resource floor.

## Complete fitting outcomes

The implementation uses the fixed four recipes and three seeds, existing
thirteen-channel input and context CNN, terminal-design labels and AdamW
recipe. Exact label memberships are checked before byte reads. B3 checkpoint
selection gives each physical case equal weight, independently of its voxel
count; historical B2 fitting and outcomes keep their original definitions.

| Recipe | Seed | Attempted epochs | Selected epoch | Selection MSE | Fit-loop seconds |
|---|---:|---:|---:|---:|---:|
| C | 17 | 193 | 168 | 0.032070857 | 338.185075 |
| C | 29 | 162 | 137 | 0.034288427 | 283.576403 |
| C | 43 | 117 | 92 | 0.045828486 | 203.309671 |
| P | 17 | 148 | 123 | 0.018779806 | 297.798809 |
| P | 29 | 159 | 134 | 0.018037449 | 316.175700 |
| P | 43 | 194 | 169 | 0.016658671 | 386.246779 |
| A | 17 | 162 | 137 | 0.016243363 | 321.262803 |
| A | 29 | 200 | 193 | 0.016558472 | 401.257516 |
| A | 43 | 185 | 160 | 0.015742080 | 369.195367 |
| S | 17 | 90 | 65 | 0.011707835 | 164.317187 |
| S | 29 | 140 | 115 | 0.008650556 | 257.596342 |
| S | 43 | 152 | 127 | 0.007452776 | 282.178969 |

All **12/12 fits** retained their complete histories and selected finite
26,433-parameter float32 model states. The attempted/retained epoch total
is **1,902/1,902**, below 2,400, with zero interrupted production epochs,
extra seeds or repeated fits. Eleven fits stopped at their selected epoch
plus 25 non-improvements; A/29 reached the frozen 200-epoch cap. The earliest
strict minimum was recomputed for every history. Every selected checkpoint's
validation MSE reproduced exactly after reload.

C/P/A metrics average all 32 physical validation cases equally. S uses its
four fixed high-volume y cases, so its MSE is not a matched comparison with
the generalists. P's MSE is lower than matched C for all three seeds; A's
MSE is also lower than P. Neither finding selects a deployment seed or
establishes terminal quality or paid query-time gain. B4.2 must retain all
controls, ablations and seeds in its prospective operational comparison.

## Independent artifact and resource acceptance

The separate external audit does not call the production fitting or MSE
audit helpers. It reconstructs exact train/selection memberships and weight
counts from the catalog, opens and checksum-verifies all 560 permitted fitting
labels through membership-specific access guards, and independently checks
terminal-design target shapes, finite float32 values and provenance.
It never opens a screening reference or final artifact.

For all twelve selections it independently checks canonical bytes, checksums,
history order, finite losses, strict minima, patience/epoch termination and
Safetensors metadata. It reloads every checkpoint, verifies exact tensor
names/shapes/dtypes/finiteness, and recomputes equal-case validation MSE with
separate batched arithmetic. All twelve values match exactly. The physical
artifact population equals the twelve checkpoints plus twelve selections:
**24 files, 1,454,103 bytes**, with no missing, replacement or orphan artifact.
No numerical tolerance changed.

| Charged component | Seconds |
|---|---:|
| Twelve fitting loops | 3,621.100621 |
| Production metadata, labels, serialization and reload audits | 201.350133 |
| Supplemental independent audit and its 10-second launch/flush allowance | 39.830532 |
| Final resource-floor/receipt work and 5-second flush allowance | 7.923055 |
| **Final cumulative fitting-stage charge** | **3,870.204341 / 7,200** |

Whole-command profiles retain the failed sandbox plan `2.33 s`, successful
plan `3.21 s`, production `3,825.86 s`, independent audit `31.61 s` and final
resource receipt `4.56 s`. Their sum is **3,867.57 seconds**, below the final
charge. Thus the failed preflight, loading, audits and command overhead are
not discounted. Peak RSS is **437,878,784 bytes**, below **4,294,967,296**.
The complete resource Gate passed with no production restart, integrity
failure, fitting failure or resource overrun.

| Evidence | SHA-256 |
|---|---|
| Read-only plan | `e63c50ab73ad3da3aedc4e50c04b11e12c1cc0770fc36c0fc5d10d6ed61a6ac5` |
| Execution/production-audit index | `9b38ff55c68a4a21fd8f52c9a3217cd9680a25088743ab949b88b169ef1af67e` |
| Independent audit source | `47e47043f65d1d79e40fea1d49bf953eb59b4a7f0bfbb06eb065ec9d5867ee51` |
| Independent complete audit receipt | `9a1a08873d285afb7437d866b5cedc397c52774a03b3c948da081df50ca82cdc` |
| Resource-floor receipt | `c188c825ecae47d01abed1a8fb43b0c23456aedee938682a8919d16bf7f94a3e` |
| Final charged training index | `229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7` |

Receipts and audit source are retained in the external fitting root's
`audit_receipts` directory. The complete independent receipt retains every
checkpoint and selection hash, every seed's metrics, exact populations,
and zero screen/final reads. The final ledger intentionally differs from
the execution index as supplemental audit and overhead charges accumulate;
its twelve immutable outcomes and upstream data identity remain unchanged.

## Implementation verification and next slice

Synthetic tests verify exact 468/508/508/488 train and 32/32/32/4 selection
populations, weight counts, pure-shape one-exposure batches, the equal-case
MSE denominator, deterministic initialization/shuffle, earliest strict ties,
RNG restoration, exact B3.4 receipt enforcement, checksum/provenance rejection,
history termination, complete membership before opening labels, immutable
prefix/charges, pending-fit recovery, hard-crash accounting, writer exclusion,
resource/epoch stops, permanent failures and side-effect-free planning.
The tests never read production B3 label bytes or fit production cases.

Locked sync, Ruff, mypy (51 source files), all **600 Python tests** in
**352.58 seconds**, and diff checks passed before the runner commit, then
all required CI checks passed before merge. The results-only commit repeated
locked sync, Ruff, mypy, all **600 tests in 346.03 seconds**, and diff checks.
Slice PRs merge only after all required CI checks pass. The next
independent slice is **B4.2: the fixed 48-case, 720-outcome
development screen, prospective primary selection and freeze audit**.
Gate B4 and the later final acceleration Gates remain open.
