# M0 catalog v2 materialization validation

Date: 2026-09-22

Source revision: `015ec12779c5983bb55eaa41f31ee33de47493eb`

Catalog ID:
`tlcatalog-v2-4ba44e175ca47f85aa0fbcafbc9456b2a1b672fd181430ec9aef29a468f46500`

Manifest SHA-256:
`7e732446d683a3609ec3e4af4b87d334caeb583c69da3db9ea0f47f91d119d5a`

## Scope and decision

This validation executed the complete frozen 160-case M0 catalog v2 through the
production entrypoint. Labels and the recoverable checkpoint were written only to a
new external, untracked directory; no generated artifact is committed to TopoLab.
The prior v1 materialization and its four failures remain unchanged.

The v2 materialization index reached `complete` with **160 succeeded and 0 failed**.
Every label and the complete index passed the contract audit below. The frozen M0
case, representation, label, partition, OOD, baseline, quality, cost, statistical,
and fallback rules therefore have a complete zero-failure dataset. **Gate M0 passes
for catalog v2.** This result permits the next independently reviewed experiment
infrastructure slice; it is not evidence that any learned method accelerates SIMP.

## Fixed environment and execution

- Hardware: Apple M2, 8 logical cores, 8 GiB memory.
- Operating system: macOS 26.5, `arm64`.
- Python 3.12.10, NumPy 2.5.3, SciPy 1.18.1.
- `uv.lock` SHA-256:
  `225e2362c4f30753f89e7bdc94ace83ebd9faed622419014ab26e0a2c1836978`.
- Numerical thread variables `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
  `MKL_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`, and `BLIS_NUM_THREADS` were all set
  to `1`.
- The Git worktree was clean. The production entrypoint captured the exact source
  revision and rejected repository-internal output before solving.

The production command used the form documented in
`docs/ml_experiment_contract.md`, with `--execute` and a fresh external root named
for the manifest digest. The full run took 207.34 seconds wall time, 195.48 seconds
user CPU, and 10.22 seconds system CPU. Process peak resident set size was
168,509,440 bytes (160.70 MiB). These are single-machine observations, not portable
performance guarantees.

## Complete outcome

The pre-label split counts remained frozen and were not rebalanced.

| Partition | Planned | Succeeded | Failed |
|---|---:|---:|---:|
| Train | 66 | 66 | 0 |
| Validation | 8 | 8 | 0 |
| Test | 6 | 6 | 0 |
| OOD | 80 | 80 | 0 |
| **Total** | **160** | **160** | **0** |

The complete index was reopened through `read_materialization_index`, and every
success was reopened through `read_label_artifact`. This rechecked canonical JSON,
manifest identity, artifact paths, byte lengths, SHA-256 digests, label schemas,
complete case payloads, source revision, environment, exact stored `float32`
tensors, the density-filter relation, physical volume, convergence metadata, and
provenance. The external root contained exactly the 160 referenced label files and
one materialization index; there were no extra files.

Aggregate contract checks were:

| Check | Observed result | Contract limit |
|---|---:|---:|
| Iterations | min 29, median 51, max 102 | at most 120 |
| Maximum terminal density change | `0.009992659742825982` | at most `0.01` |
| Maximum physical-volume absolute error | `1.044461017674081e-08` | at most `5e-3` |
| Compliance range | `0.025029927289042034` to `0.562557261144619` | finite and positive |

The four formerly failing physical configurations converged at iteration 102 under
the versioned 120-iteration budget. Their terminal density changes ranged from
`0.009600929393831281` to `0.009600929394928154`; the convergence tolerance was not
changed.

The 160 label files contain 1,353,078 bytes. The complete canonical index contains
213,117 bytes and has SHA-256
`4a02c67265241af7852d9f2da9caa475d2f018e2ac5882834175d60c8bcae458`.
The full external directory occupies 1,892 KiB on disk.

Re-running the production command against the complete index regenerated no labels.
It reverified all successful artifacts, reproduced the 160/0 outcome, exited with
status 0, and completed in 1.73 seconds. The index checksum remained unchanged.

## Gate result and next action

No numerical tolerance was loosened, no case was removed, no split was rebalanced,
and no v1 outcome was overwritten. The materialized v2 manifest is the training-data
boundary for the next stage; labels from v1 or another revision/environment must not
be mixed into it.

Gate M0 passes for this exact catalog and manifest. The next independent slice should
implement the fixed uniform, physics-heuristic, and training-only nearest-neighbor
baseline runner and its cost/quality accounting before adding PyTorch or training a
learned model.
