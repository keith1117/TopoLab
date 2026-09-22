# M0 catalog materialization validation

Date: 2026-09-22

Source revision: `6586454efca776abf9f93b0224f8f8f6a7e220d5`

Catalog ID:
`tlcatalog-v1-e532ad3d9de3083918e1ab074e7ba3b88a254d0b6729af508f96959ea1eedc3d`

Manifest SHA-256:
`8623006fe376b69362ea7704e23c140b6771d3727db68e0973f7b96b243c9aff`

## Scope and decision

This validation executed the complete frozen 160-case M0 v1 catalog through the
production entrypoint. Labels and the recoverable checkpoint were written only to an
external, untracked directory; no generated artifact is committed to TopoLab.

The materialization index reached `complete`, but four cases recorded the terminal
code `label_generation_error`. The outcome is therefore **156 succeeded and 4
failed**. Under the frozen contract, `complete` means every case has an auditable
outcome; it does not mean the dataset is suitable for training. **Gate M0 has not
passed, and this materialization must not be used for model training.**

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

From the repository root, the execution form was:

```bash
OMP_NUM_THREADS=1 \
OPENBLAS_NUM_THREADS=1 \
MKL_NUM_THREADS=1 \
VECLIB_MAXIMUM_THREADS=1 \
BLIS_NUM_THREADS=1 \
PYTHONPATH=src \
uv run --locked python -m topolab.dataset_cli \
  --output-root <external-root> \
  --execute
```

The full run took 205.00 seconds wall time, 193.23 seconds user CPU, and 10.19
seconds system CPU. Process peak resident set size was 174,374,912 bytes (166.30
MiB). These are single-machine observations, not portable performance guarantees.

## Complete outcome

The pre-label split counts remained frozen and were not rebalanced after failures.

| Partition | Planned | Succeeded | Failed |
|---|---:|---:|---:|
| Train | 60 | 60 | 0 |
| Validation | 9 | 9 | 0 |
| Test | 11 | 11 | 0 |
| OOD | 80 | 76 | 4 |
| **Total** | **160** | **156** | **4** |

All 156 successful references were reopened through
`read_materialization_index` and `read_label_artifact`. This rechecked the canonical
index, manifest identity, artifact path, byte length, SHA-256, label schema, canonical
JSON, complete case payload, source revision, environment, stored float32 tensors,
density-filter relation, physical volume, convergence metadata, and provenance.

Aggregate contract checks over the successful labels were:

| Check | Observed result | Contract limit |
|---|---:|---:|
| Iterations | min 29, median 51, max 93 | at most 100 |
| Maximum terminal density change | `0.009992659742825982` | at most `0.01` |
| Maximum physical-volume absolute error | `1.044461017674081e-08` | at most `5e-3` |
| Compliance range | `0.025029927289042034` to `0.562557261144619` | finite and positive |

The 156 label files contain 1,315,194 bytes. The complete canonical index contains
211,186 bytes and has SHA-256
`9f517be3816e4fb978b5034cd677393de93246cd0cd9cb8e1ab4efe902b73ef0`.
The full external directory occupies approximately 1.8 MiB on disk.

Re-running the production command against the complete index regenerated no labels.
It reverified all successful artifacts, reproduced the 156/4 outcome and required
nonzero exit status, and completed in 1.63 seconds. The index checksum remained
unchanged.

## Failure analysis

Every failure is an OOD case with a `z`-directed point load, target physical volume
fraction `0.2`, and one of the four load nodes interior to both the loaded face's
`y` and `z` grids. All other catalog cases, including the matched ID cases, produced
valid labels.

| Case ID | Loaded node | Face-grid `(y, z)` | Iterations | Terminal density change |
|---|---:|---:|---:|---:|
| `tlcase-v1-ae10d88c0ad345f819637c6ef93f007937beab86922cee35c8e986a506c1d7da` | 246 | `(4, 2)` | 100 | `0.011526471327585636` |
| `tlcase-v1-b1e359727179039457acc3bb464468fb006d486b364af40ddc5838022d974bbb` | 155 | `(4, 1)` | 100 | `0.01152647132706211` |
| `tlcase-v1-ba46127be16f06623727b32b0b0dad07c2beef0b0e59d8dad6b532f195eb5c1a` | 220 | `(2, 2)` | 100 | `0.01152647132684334` |
| `tlcase-v1-d7f4d193fab051b95c13af6662b625081285d57c8a90870b2ea9fb95650efdb2` | 129 | `(2, 1)` | 100 | `0.01152647132834922` |

Each failed solve preserved the target volume to approximately `3.2e-9` absolute
error, but the density change remained above `0.01` after the frozen 100 iterations.
For one representative case, the final three changes decreased from
`0.014195280038695246` to `0.012772814603313504` and then
`0.011526471327585636`; the solver correctly reported non-convergence.

As a diagnosis only, the four problems were re-solved without materializing labels
after changing `max_iterations` from 100 to 120. All four crossed the unchanged
`0.01` threshold at iteration 102, with terminal density changes near
`0.009600929394`. This indicates that the frozen iteration budget is the immediate
limiting condition. It does not repair M0 v1: `max_iterations` is part of physical
case identity, so changing it requires new case IDs, a new catalog identity, a new
manifest, and a new auditable materialization.

## Gate result and next action

No numerical tolerance was loosened, no case was removed, no split was rebalanced,
and no failed outcome was overwritten. The complete index remains the immutable
record of this unsuccessful M0 v1 attempt.

The follow-up contract slice adopted the diagnosed termination-budget correction as
`topolab.m0.catalog.v2`, increasing only `max_iterations` from 100 to 120. It keeps
the `topolab.m0.case.v1` schema, the `0.01` tolerance, the 160-case population, and
the `topolab.m0.split.v1` algorithm. The resulting catalog identity is
`tlcatalog-v2-4ba44e175ca47f85aa0fbcafbc9456b2a1b672fd181430ec9aef29a468f46500`;
the new pre-label split counts are 66 train, 8 validation, 6 test, and 80 OOD.

At that point, the next independent slice had to materialize and audit a new v2
manifest. PyTorch, training, hyperparameter selection, and M1 remained blocked until
that complete materialization had zero failures.

That follow-up completed successfully and is recorded separately in
`docs/validation/m0_catalog_v2_materialization.md`. This v1 report remains the
immutable record of the failed 100-iteration attempt.
