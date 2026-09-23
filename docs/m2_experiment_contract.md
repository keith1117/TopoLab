# M2 bounded warm-start follow-up contract

Status: **contract, 756-case catalog identity, exposure-aware split, and guarded
materialization entrypoint implemented for `topolab.m2.experiment.v1`; no M2 case has
been materialized, no M2 model has been fitted, and no M2 validation, ID-test, or OOD
outcome has been observed**.

## Question and stopping rule

M2 asks one bounded follow-up question motivated by the frozen M1 result:

> Can broader direction-balanced fitting data plus a validation-calibrated ensemble
> reliability gate reduce end-to-end SIMP time without increasing failures?

This is a new experiment, not a continuation of M1 checkpoint selection. M1's 6
ID-test and 80 OOD cases are development-exposed evidence. They may motivate M2 and
their physical cases may be assigned to M2 training, but they cannot serve as M2
validation or final evidence.

M2 permits exactly one catalog expansion, the unchanged M1 model/loss/optimizer
recipe, five fixed fits, one five-model ensemble, and the finite gate search defined
below. It does not permit an architecture search, loss search, learning-rate search,
seed selection, post-hoc case removal, or a second M2 catalog. If the frozen final
comparison does not pass its claim threshold, learned-model expansion stops and the
project proceeds to release with uniform initialization as the operational default.

## Version boundary

- Catalog: `topolab.m2.catalog.v1`.
- Dataset manifest and split: `topolab.m2.dataset.v1` and
  `topolab.m2.split.v1`.
- Materialization index and plan summary: `topolab.m2.materialization.v1` and
  `topolab.m2.materialization-summary.v1`.
- Training contract: `topolab.m2.training.v1`.
- Reused model architecture: `topolab.m1.cnn.v1`.
- Ensemble and gate: `topolab.m2.ensemble.v1` and `topolab.m2.gate.v1`.
- Experiment: `topolab.m2.experiment.v1`.

Every artifact identity must cover its complete versioned payload, source revision,
locked runtime, and upstream artifact references. Generated data, checkpoints,
selections, gate records, and evaluation indexes remain outside Git.

## Guarded materialization

The M2 entrypoint builds the exact frozen manifest only from a clean Git revision and
records the locked Python, NumPy, SciPy, and `uv.lock` identities. The output root
must resolve outside the repository. Omitting `--execute` is read-only: it neither
creates the output root nor invokes the solver.

```bash
PYTHONPATH=src uv run --locked python -m topolab.m2_dataset_cli \
  --output-root /absolute/external/root
```

Only a separately authorized run may add `--execute`. Execution uses the shared
canonical-order, per-case atomic checkpoint path, but writes an M2-specific index
version so an M0 consumer cannot silently accept the expanded manifest.

## Fixed physical cohort

M2 keeps the M1 mesh, material, support, load magnitude, and SIMP settings so that
the intervention changes data coverage and inference policy rather than the numerical
problem:

| Field | Frozen value |
|---|---|
| Mesh | `(nx, ny, nz) = (12, 6, 3)`, lengths `(12.0, 6.0, 3.0)` |
| Material | `E0 = 1000.0`, `Emin = 1.0`, `nu = 0.3` |
| Support | all displacement components on `x=min` |
| Loaded face | point load on `x=max` |
| Loaded-node `y` indices | `[0, 1, 2, 3, 4, 5, 6]` |
| Loaded-node `z` indices | `[0, 1, 2, 3]` |
| Load magnitude | `-1.0` |
| ID directions | `y` and `z` |
| OOD direction | `x` |
| Volume fractions | `[0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]` |
| SIMP/filter settings | radius `1.5`, penalty `3.0`, minimum density `0.05`, move limit `0.2` |
| Termination | density-change tolerance `0.01`, maximum `120` iterations |

The ID pool contains `28 * 9 * 2 = 504` cases. The OOD pool contains
`28 * 9 = 252` matched `x`-direction cases. The total catalog contains 756 unique
physical cases. Every OOD case has a matched `y`-direction ID counterpart with the
same node, magnitude, volume fraction, mesh, material, support, and optimization
settings.

The negative `x` load points from the free `x=max` face toward the fixed `x=min`
face. Its axial behavior is deliberately outside the `y/z` bending-direction fitting
distribution and must always be reported as OOD.

## Exposure-aware partition

The 160 physical cases in the frozen M1 catalog are development-exposed. All M1
overlap cases are assigned to M2 training; none may enter M2 validation or ID test.

For each of the 18 `(ID direction, volume fraction)` strata, consider only cases that
do not occur in M1. Sort them by the hexadecimal SHA-256 digest of
`"topolab.m2.split.v1:<case_id>"` in ascending order, breaking an impossible digest
tie by `case_id`. Assign the first two cases to validation, the next two to ID test,
and all remaining cases to training. Assign every `x`-direction case to OOD.

The exact frozen counts are therefore:

| Split | Cases | Label access during fitting |
|---|---:|---|
| Train | 432 | allowed |
| Validation | 36 | allowed |
| ID test | 36 | forbidden |
| OOD | 252 | forbidden |
| Total | 756 | - |

All 36 validation and 36 ID-test cases are physically absent from M1. Dataset
materialization may generate their content-addressed labels through the independent
solver, but training and evaluation adapters must reject ID-test/OOD label access
before opening artifact bytes. Final evaluation uses only the physical case
definition, the compared methods, and independent quality checks.

## Unchanged fitting intervention

M2 deliberately reuses the M1 11,281-parameter shape-preserving network:

1. `Conv3d(10, 16, kernel_size=3, padding=1)` plus ReLU;
2. `Conv3d(16, 16, kernel_size=3, padding=1)` plus ReLU; and
3. `Conv3d(16, 1, kernel_size=1)` plus sigmoid.

It also reuses design-density MSE, AdamW, learning rate `1e-3`, weight decay `1e-4`,
batch size 8, maximum 200 epochs, early-stopping patience 25, deterministic CPU
fitting, earliest strict minimum validation MSE selection, and seeds
`[17, 29, 43, 71, 113]`.

All five selected checkpoints are retained. No best seed may be promoted and no seed
may be dropped. This makes the expanded, direction-balanced fitting population the
only training intervention relative to M1.

## Ensemble candidate

For one non-training query, load and verify all five selected checkpoints, encode the
case once, and run every model as CPU `float32` without gradients. Let `p_s` be seed
`s`'s raw sigmoid output and let `q_s` be its independently filtered-volume-projected
design density.

The ensemble uncertainty score is the mean population variance over elements:

```text
u = mean_e(var_s(q_s[e], ddof=0))
```

The accepted ensemble initialization is:

```text
q = project(mean_s(q_s))
```

The final projection is mandatory even though each member was already projected.
All five inference calls, member projections, uncertainty calculation, averaging,
and final projection are charged to per-query setup/projection time. Checkpoint
loading remains a separately reported experiment setup cost.

## Finite reliability-gate calibration

Gate calibration uses only the 36 validation cases and occurs after all five
checkpoint selections are frozen. Run the ensemble and uniform reference on every
validation case, then evaluate exactly these policies:

1. reject every ensemble candidate;
2. accept when `u` is at or below the validation uncertainty 0th percentile;
3. accept when `u` is at or below the 25th percentile;
4. accept when `u` is at or below the 50th percentile;
5. accept when `u` is at or below the 75th percentile;
6. accept when `u` is at or below the 100th percentile; and
7. accept every ensemble candidate.

Percentiles use NumPy's linear quantile definition. Duplicate numeric thresholds
remain distinct named policies but produce the same decisions; no extra threshold
may be inserted. A rejection runs uniform directly after the charged ensemble/gate
setup and is recorded as `rejected_to_uniform`, not as a learned failure. An accepted
candidate is refined through the public SIMP path and the frozen M1 quality checks.
If that attempt fails, a fresh uniform fallback is fully charged and the learned
attempt remains failed.

A policy is eligible only if it has zero learned-attempt failures on validation.
Choose the eligible policy with the lowest arithmetic mean paired end-to-end time
ratio to uniform. Exact ties select the policy with fewer accepted cases, then the
earlier policy in the list above. Persist the complete calibration table and selected
policy as one content-addressed artifact before opening ID-test or OOD cases.

The always-reject policy guarantees that calibration can finish safely, but its
inference overhead means it cannot by itself establish acceleration.

## Frozen baselines and evaluation

Final evaluation compares:

1. uniform initialization;
2. the unchanged physics heuristic;
3. nearest neighbor built only from the 432 M2 training labels; and
4. the selected five-model ensemble/gate policy.

The 36 ID-test cases are evaluated first in canonical `case_id` order, followed by
the 252 OOD cases. Query-label artifacts remain unopened. Every physical case is one
atomic recoverable checkpoint entry containing all method outcomes. An interrupted
case remains pending and is rerun in full.

Every end-to-end time includes method setup, projection, refinement, and any fresh
uniform fallback. A gated rejection includes all five model inferences and the gate
decision plus the complete uniform run. Dataset generation, fitting, checkpoint
loading, and gate calibration are reported separately and are not amortized into a
speedup claim.

## Statistics and claim boundary

The primary statistic is the paired per-case ensemble/uniform end-to-end time ratio
on the 36 ID-test cases. Report its arithmetic mean, median, linear IQR, failure rate,
rejection rate, fallback rate, operational iterations, compliance, and volume error.
Use 10,000 case bootstrap resamples with `numpy.random.default_rng(20260924)` and
linear 2.5th/97.5th percentiles for the mean-ratio 95% interval. Apply the same
procedure independently to OOD after resetting the generator.

An M2 learned-acceleration claim requires all of the following on ID test:

- the upper 95% interval bound for the mean ratio is below `1.0`;
- zero accepted learned attempts fail or use fallback;
- every operational result satisfies the frozen convergence, volume, independent
  compliance, and `1.001 * uniform` quality limits; and
- no case, seed, policy, or timing component is removed after observation.

OOD is always reported separately. An `OOD-safe` statement additionally requires
zero OOD learned-attempt failures and an upper 95% mean-ratio interval bound no
greater than `1.05`. OOD performance cannot substitute for the ID acceleration
criterion, and ID performance cannot be relabeled as OOD evidence.

## Explicit non-goals

M2 does not add a larger CNN, U-Net, residual family, attention, a new loss, trajectory
labels, differentiable FEM, GPU training, multiple mesh sizes, new support families,
or a hyperparameter sweep. Larger meshes may make warm-start overhead easier to
amortize, but changing scale in this follow-up would confound the data-coverage and
reliability interventions. Any such work requires a separately reviewed experiment
after M2, not an amendment made after seeing M2 outcomes.

## Required implementation order

1. Implement and test the M2 catalog, exposure-aware split, identities, and exact
   counts without solving cases. **Complete.**
2. Implement and test a guarded M2 materialization entrypoint without solving cases.
   **Complete.**
3. Merge the entrypoint, run its read-only production plan, obtain explicit execution
   authorization, then materialize and audit the complete external artifact set.
4. Implement the train/validation-only adapter and unchanged five-seed fitting path.
5. Implement and test ensemble inference, finite gate calibration, artifacts, and
   charged rejection/fallback accounting.
6. Implement the recoverable final runner and frozen statistics.
7. Merge all final-evaluation code, run a read-only production plan, request explicit
   authorization, execute once, and commit the result regardless of outcome.

No later step may begin before the preceding contract boundary has tests and a clean,
reviewed source revision.
