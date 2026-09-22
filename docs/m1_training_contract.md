# M1 learned warm-start training contract

Status: **model, loss, fitting-data boundary, training budget, and checkpoint-selection
rules frozen at `topolab.m1.training.v1`; no training run has started**.

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

## Checkpoint selection

Each seed is an independent run. After every epoch, compute mean validation
design-density MSE over all eight validation cases. The selected checkpoint is the
strictly lowest validation mean; an exact tie selects the earliest epoch. Early
stopping occurs after 25 consecutive epochs without a strictly lower value. The
maximum-epoch checkpoint is not preferred unless it satisfies the same rule.

Test and OOD labels remain unopened until all five seed-specific checkpoints exist
and their selection records have been frozen. No seed may be dropped because of an
unfavorable validation result. A later training artifact must record the M0 manifest
digest, M1 contract/model/loss versions, exact source revision, `uv.lock` digest,
Python/NumPy/SciPy/PyTorch versions, seed, epoch history, selected epoch, hardware,
thread settings, and checkpoint checksum.

## Next implementation slice

The next slice may implement deterministic fitting and content-addressed checkpoint
artifacts for this exact recipe. It must still stop before test/OOD evaluation. The
five trained checkpoints and auditable selection records are the prerequisite for
opening held-out labels and running the frozen end-to-end comparison.
