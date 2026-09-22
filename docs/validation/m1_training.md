# M1 production training validation

Date: 2026-09-22

Training source revision: `a538d40ffaf3da20e8a06ff9e3ac136da72b5718`

M0 label source revision: `015ec12779c5983bb55eaa41f31ee33de47493eb`

Catalog ID:
`tlcatalog-v2-4ba44e175ca47f85aa0fbcafbc9456b2a1b672fd181430ec9aef29a468f46500`

Manifest SHA-256:
`7e732446d683a3609ec3e4af4b87d334caeb583c69da3db9ea0f47f91d119d5a`

## Scope and decision

The guarded M1 production entrypoint fitted all five frozen seeds against the exact
catalog-v2 training and validation partitions. It wrote generated checkpoints and
selection records only to a new external, untracked directory. The entrypoint then
reopened and verified every selection and checkpoint against the manifest, source
revision, runtime, case IDs, tensor schema, provenance metadata, byte length, and
SHA-256 digest.

The run completed with **five verified selections and zero failures**. All five runs
stopped after exactly 25 epochs without a strict validation improvement, as required
by the frozen contract. This completes the M1 fitting prerequisite. It does not show
that a learned warm start improves SIMP: test and OOD labels remained unopened, no
learned initialization was refined through SIMP, and no baseline comparison occurred.

## Fixed data and training boundary

- Train cases: 66.
- Validation cases: 8.
- Test cases opened: 0.
- OOD cases opened: 0.
- Tensor shape per input: `(10, 3, 6, 12)`.
- Tensor shape per target: `(1, 3, 6, 12)`.
- Model: `topolab.m1.cnn.v1`, 11,281 parameters.
- Seeds: `17, 29, 43, 71, 113`.
- Maximum epochs per seed: 200.
- Early-stopping patience: 25.
- Batch size: 8.
- Device: CPU.

The preflight opened only the canonical materialization index. During execution,
label access remained inside the train/validation dataset adapter. The production
entrypoint contains no test/OOD fitting option, and all five seeds were retained.

## Recorded environment and execution

- Hardware: Apple M2, 8 logical cores, 8 GiB memory.
- Operating system: macOS 26.5, `arm64`.
- Python 3.12.10.
- NumPy 2.5.3, SciPy 1.18.1, PyTorch 2.14.0, Safetensors 0.8.0.
- `uv.lock` SHA-256:
  `34e089881d5601a4331cb26896413b9850d8ffc69f87eeaffda352d68db2111d`.
- PyTorch intra-op threads: 1; inter-op threads: 8.
- `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`,
  `VECLIB_MAXIMUM_THREADS`, and `BLIS_NUM_THREADS` were set to `1`.
- Source worktree: clean, with the training entrypoint merged and its `main` CI
  passing before execution.

The production command used the documented `python -m topolab.training_cli` form
with both external roots and `--execute`. End-to-end process wall time was 22.25
seconds, with 16.89 seconds user CPU, 4.08 seconds system CPU, and peak resident set
size 353,452,032 bytes (337.08 MiB). The sum of the five recorded fitting durations
was 19.37 seconds. These are single-machine observations, not portable performance
guarantees.

## Seed results

| Seed | Epochs completed | Selected epoch | Selected train MSE | Selected validation MSE | Fit seconds | Checkpoint SHA-256 | Selection SHA-256 |
|---:|---:|---:|---:|---:|---:|---|---|
| 17 | 166 | 141 | `0.10582749590729222` | `0.12093227356672287` | `5.149617874994874` | `4c0291ee05e4180f36e99040c7de4d5dc0932f71ff8d8ba719f438e985cf08c2` | `09b38b66bf10b05f572d6238db628a626b7bdd20be8858b90be8e48ec3577d0e` |
| 29 | 143 | 118 | `0.11616571924903175` | `0.12162672728300095` | `3.6754648749993066` | `654b0ef2a6dd13a25af2a615e327d78ef910f46ace7c9143ca86a8d733a54b1a` | `df41955903a0e6ef8867f54197ac564f90f3608eb51ad47fd035045f2ba341f0` |
| 43 | 146 | 121 | `0.10625914326219847` | `0.12029650807380676` | `3.8939666249934817` | `f50dff12ad2396357f18a9e1ed5672a6e709a4e0ebccc1b48783187e3b73b544` | `30504204cef125ae8beae6d973d69f6bd62b530cbd83da63c4d07241597f68d8` |
| 71 | 100 | 75 | `0.11484489657662132` | `0.12420342862606049` | `2.610643499996513` | `f3a4cd11502879d17a5b40794d22fb6e7391eaa7dd7c9f682e16d50607f659ee` | `a011c03fdf74ed8287169543cc5bfa0cf16092eaaba39d84afecc23fb488fc76` |
| 113 | 159 | 134 | `0.10821565466396736` | `0.12185458093881607` | `4.041776999998547` | `7331d703d8df7b5a5c5cf213f6474b6c56dd8b59b26d8e1880847f33b1da275b` | `b100af75f5d706981b7fd640467aad97a8420e2d4f5a349e58d77416b2015a39` |

Across the five fixed seeds, 714 epochs were completed. Selected validation MSE had
mean `0.12178270369768143`, minimum `0.12029650807380676`, and maximum
`0.12420342862606049`. Seed 43 had the lowest validation MSE, but no seed was dropped
or promoted to a held-out conclusion from this observation.

## Artifact audit

The external run directory contained exactly five Safetensors checkpoints and five
canonical JSON selection records. Every checkpoint was 46,476 bytes, for 232,380
checkpoint bytes total. Selection records totaled 108,311 bytes, so the ten files
contained 340,691 bytes and occupied 356 KiB on disk.

Independent `shasum -a 256` output matched every content-addressed filename. The
production audit additionally rechecked checkpoint tensor names, shapes, `float32`
dtype, finite values, embedded provenance, selection schema, earliest-minimum rule,
exact early stopping, and checkpoint-to-selection linkage. Generated artifacts were
not added to Git.

## Gate result and next action

The frozen M1 fitting stage is complete for all five seeds. The result establishes
reproducible trained candidates, not learned acceleration or final model quality.
The next independently reviewed slice should implement the frozen learned-inference,
filtered-volume projection, SIMP refinement, fallback, and cost/quality evaluator.
Only after that boundary is tested should the project open held-out test/OOD labels
and run the predefined comparison against all fixed baselines.
