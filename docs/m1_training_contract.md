# M1 learned warm-start training contract

Status: **model, loss, fitting-data boundary, training budget, deterministic fitting,
and content-addressed checkpoint/selection formats implemented for
`topolab.m1.training.v1`; no production training run has started**.

## Scope and claims boundary

M1 asks whether one lightweight learned design-density initialization can reduce the
end-to-end SIMP time while satisfying the frozen M0 quality constraints. This slice
defines and implements the model, supervised loss, and train/validation adapter. It
does not fit parameters, select a checkpoint, inspect test/OOD labels, or support an
`accelerated` claim.

The only training data source is the zero-failure catalog-v2 materialization recorded
in `docs/validation/m0_catalog_v2_materialization.md`. The case, tensor, label,
partition, projection, baseline, quality, fallback, and reporting rules remain those
in `docs/ml_experiment_contract.md`.

## Fitting-data boundary

`topolab.training.build_m1_tensor_dataset` accepts only the frozen `train` or
`validation` split. It requires a complete materialization with no failed entries and
reads only label artifacts in the requested split. Calls using `test` or `ood` are
rejected before artifact access.

Every example is `(input, target)`:

- input: `float32` with shape `(10, nz, ny, nx)`, using the frozen M0 channel and
  `(channel, z, y, x)` order;
- target: final design density as `float32` with shape `(1, nz, ny, nx)`; and
- dataset order: lexicographic `case_id`, inherited from the verified manifest.

The adapter does not expose physical density, optimizer history, final compliance,
test labels, or OOD labels. The production catalog-v2 shapes are input
`(10, 3, 6, 12)` and target `(1, 3, 6, 12)`.

## Fixed model

The model version is `topolab.m1.cnn.v1`. `WarmStartCNN` is a shape-preserving
11,281-parameter network:

| Layer | Frozen definition |
|---|---|
| 1 | `Conv3d(10, 16, kernel_size=3, padding=1)` + ReLU |
| 2 | `Conv3d(16, 16, kernel_size=3, padding=1)` + ReLU |
| 3 | `Conv3d(16, 1, kernel_size=1)` + sigmoid |

The sigmoid produces a raw design-density field in `[0, 1]`. Model outputs are not
used directly as physical density. Evaluation passes them through the frozen M0
filtered-volume projection before SIMP refinement.

This is one fixed architecture, not a model-family search. Larger U-Nets, residual
variants, attention, compliance surrogates, generative models, and transfer learning
are outside the first experiment.

## Loss and optimizer recipe

The loss version is `topolab.m1.design-mse.v1`: elementwise mean-squared error between
predicted and labeled final design density, averaged across batch, channel, and all
spatial elements. There is no auxiliary physical-density, compliance, volume, or
adversarial loss in the first experiment.

The single frozen hyperparameter configuration is:

| Setting | Value |
|---|---:|
| Optimizer | AdamW |
| Learning rate | `1e-3` |
| Weight decay | `1e-4` |
| Adam betas | `(0.9, 0.999)` |
| Adam epsilon | `1e-8` |
| Batch size | `8` |
| Maximum epochs | `200` |
| Early-stopping patience | `25` epochs |
| DataLoader workers | `0` |
| Training device | CPU |
| Model/training seeds | `17, 29, 43, 71, 113` |

Training batches are shuffled from a generator initialized with the run seed.
Validation order is fixed and validation is evaluated without gradient tracking.
There is no augmentation and no hyperparameter sweep. The CPU/zero-worker policy is
chosen for the first small cohort to make ordering and reproducibility easier to
audit; the project pins PyTorch to its official CPU-only package index, so Linux CI
does not acquire unused CUDA runtimes. Later device changes require a new contract
version.

`fit_m1_model` seeds model initialization and a dedicated training-shuffle generator
for each run, enables strict PyTorch deterministic algorithms during fitting, and
restores the caller's RNG and deterministic settings afterward. Epoch train and
validation MSE are accumulated by squared-error element count, including the smaller
last training batch. Bitwise-repeatability is tested within one recorded CPU/runtime
environment; the artifacts record the package, hardware, and thread context rather
than claiming cross-platform floating-point identity.

## Checkpoint selection

Each seed is an independent run. After every epoch, compute mean validation
design-density MSE over all eight validation cases. The selected checkpoint is the
strictly lowest validation mean; an exact tie selects the earliest epoch. Early
stopping occurs after 25 consecutive epochs without a strictly lower value. The
maximum-epoch checkpoint is not preferred unless it satisfies the same rule.

## Checkpoint and selection artifacts

`topolab.training_artifacts` persists two content-addressed artifact formats:

- `topolab.m1.checkpoint.v1` stores the selected model's named, finite `float32`
  tensors in the documented Safetensors format. It deliberately avoids pickle and
  contains no optimizer state or training-resume claim.
- `topolab.m1.selection.v1` stores the complete epoch history, selected epoch and
  validation value, early-stop state, training duration, exact train/validation case
  IDs, M0 manifest digest, label/training revisions, runtime and thread metadata, and
  the verified checkpoint reference.

Paths are
`m1/checkpoints/<manifest_sha256>/<seed>/<sha256>.safetensors` and
`m1/selections/<manifest_sha256>/<seed>/<sha256>.json`. Writes use same-directory
temporary files, flush and `fsync`, then publish with atomic replacement. Reads check
path, byte length, SHA-256, Safetensors or selection schema, canonical selection
serialization, model tensor names and shapes, finite values, and
checkpoint-to-selection provenance before returning data.

`train_all_m1_seeds` constructs the train and validation datasets once, then fits and
persists every seed in the frozen order. It has no code path accepting test or OOD
partitions. Partial artifacts from an interrupted invocation are immutable valid
content, but this slice does not claim resumable optimizer state or provide a
production CLI.

Test and OOD labels remain unopened until all five seed-specific checkpoints exist
and their selection records have been frozen. No seed may be dropped because of an
unfavorable validation result. A later training artifact must record the M0 manifest
digest, M1 contract/model/loss versions, exact source revision, `uv.lock` digest,
Python/NumPy/SciPy/PyTorch/Safetensors versions, seed, epoch history, selected epoch,
hardware, thread settings, and checkpoint checksum.

## Next implementation slice

The next slice should add a safe production entrypoint that requires a clean source
revision, the verified external catalog-v2 materialization, the repository lockfile,
and an external training-artifact root. It can then execute and audit all five seeds.
The resulting five verified selection records remain the prerequisite for opening
test/OOD labels and running the frozen end-to-end comparison.
