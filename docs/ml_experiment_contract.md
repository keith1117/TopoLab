# M0 machine-learning experiment contract

Status: **contract, deterministic representation, manifest, single-case label,
label-artifact, recoverable materialization-index, controlled materialization
executor, bounded case-catalog, production entrypoint, and fixed-baseline runner
slices implemented at `m0.v1`; production catalog revised to
`topolab.m0.catalog.v2`**. This document freezes case identity, representation,
split, label, baseline, and evaluation semantics before model training. M0 is not
complete until a bounded catalog is materialized with zero failures and the complete
outcomes are validated against this contract. The first complete attempt recorded 156 successes
and four terminal OOD generation failures. The v2 catalog corrects the bounded
iteration budget and its complete materialization recorded 160 successes and zero
failures. Gate M0 passes for the exact v2 manifest recorded in
`docs/validation/m0_catalog_v2_materialization.md`; the v1 manifest remains failed
evidence and is not training data.

## Scope and claims boundary

The first experiment asks one question: can a predicted design-density warm start
reduce the end-to-end time required by the existing SIMP solver to reach a result of
the same quality as a uniform start?

The M0 implementation provides typed case identity, deterministic input
encoding, filtered-volume projection, immutable sample metadata, a validated dataset
manifest, deterministic generation of one label, a recoverable manifest-to-label
index, a single-process executor, one bounded deterministic case catalog, a safe
production entrypoint that constructs the manifest from a clean checkout, and the
three fixed baseline initializations with quality and cost accounting. The first
complete production attempt is recorded in
`docs/validation/m0_catalog_materialization.md`; its generated artifacts remain
outside Git. The successful v2 materialization and audit are recorded in
`docs/validation/m0_catalog_v2_materialization.md`. Later M1 slices add the frozen
PyTorch model, deterministic fitting and artifacts, and a single-case learned
evaluator without changing the M0 identities or data boundary. Held-out production
evaluation is still pending, so the project does not support an `accelerated` claim.
The implementation does not turn optimizer history rows into independent samples.
The numerical and platform contracts remain unchanged.

## Versioned case schema and identity

`topolab.experiment.ExperimentCase` wraps the frozen `TopologyProblem` contract with:

- `schema_version = "topolab.m0.case.v1"`;
- a verified `case_id` with prefix `tlcase-v1-`; and
- a complete `problem` containing mesh, material, supports, loads, and optimization
  settings.

`initial_density` must be `null`. Initialization is a method under evaluation, not
part of physical case identity. The identity includes all other problem fields:

| Section | Identity fields |
|---|---|
| Mesh | `(nx, ny, nz)` element counts and `(Lx, Ly, Lz)` lengths |
| Material | solid modulus, minimum modulus, and Poisson ratio |
| Supports | face axis/side and every constrained displacement direction |
| Loads | load kind, selector, signed component direction, and signed magnitude/resultant |
| Optimization | target physical volume fraction, filter radius, penalty, minimum density, move limit, convergence tolerance, and maximum iterations |

The ID is the full lowercase SHA-256 digest of canonical UTF-8 JSON, prefixed with
`tlcase-v1-`. Canonical JSON uses sorted object keys, no insignificant whitespace,
JSON arrays for tuples, and the exact validated finite floating-point values. Support
directions use `x/y/z`, repeated constraints on the same face are merged, and support
and load order is canonicalized. Load multiplicity is retained because repeated
loads superpose physically. Any future canonicalization or field change requires a
new schema version and ID prefix; existing IDs must never be silently reinterpreted.

The stored `problem` is normalized to the same direction names and support/load
ordering when an `ExperimentCase` is constructed or read. The serialized `case_id`
is checked on every read. A stale or manually edited ID is invalid. Dataset manifests
must reject duplicate case IDs rather than silently overwrite them.

## Model cohort and input tensor

Version `m0.v1` uses one fixed-shape cohort per model. Every case in a cohort must
have identical element counts, physical lengths, material values, filter radius,
penalty, minimum density, move limit, convergence tolerance, and maximum iterations.
These values remain in each case and the manifest for auditability. Within a cohort,
supports, loads, and target volume fraction may vary. Combining cohorts or adding
constant-parameter channels requires a later contract version.

The input is a channel-first `float32` tensor with shape
`(10, nz, ny, nx)`. Spatial indexing is `(ez, ey, ex)`; `ex`/`x` is the fastest axis,
matching the numerical element index `ex + nx * (ey + ny * ez)`.

| Channel | Meaning |
|---:|---|
| 0 | `support_x`: 1 where an element touches at least one node constrained in `ux`, else 0 |
| 1 | `support_y`: same rule for `uy` |
| 2 | `support_z`: same rule for `uz` |
| 3 | `load_x`: dimensionless element-scattered signed `fx` |
| 4 | `load_y`: dimensionless element-scattered signed `fy` |
| 5 | `load_z`: dimensionless element-scattered signed `fz` |
| 6 | `coord_x = (ex + 0.5) / nx` |
| 7 | `coord_y = (ey + 0.5) / ny` |
| 8 | `coord_z = (ez + 0.5) / nz` |
| 9 | target physical volume fraction broadcast to every element |

Load channels are derived from the final nodal vector produced by the existing load
contract, after point loads and equal-node face resultants have superposed. Each
nodal component is divided equally among its incident elements, so summing one raw
voxel component reproduces the corresponding nodal resultant. All three raw channels
are then divided by the single positive scale `sum(abs(global_load_vector))`. This
keeps sign, direction, location, and relative magnitude while removing the irrelevant
single-load-case force scale. The scale is stored in sample metadata. A zero scale is
an invalid case.

No axis transposition, image-style `y` reversal, or implicit batch dimension is
allowed. Batches add one leading dimension: `(batch, 10, nz, ny, nx)`.

`topolab.experiment.encode_case` implements this mapping and returns an `EncodedCase`
whose `input_tensor` has the frozen shape/dtype and whose `load_scale` records the
dimensional L1 scale used for normalization.

## Label and warm-start density definitions

Both label arrays are `float32` tensors of shape `(1, nz, ny, nx)` with the same
`(ez, ey, ex)` spatial order:

- `design_density` is the final OC design variable `x` and lies in
  `[minimum_density, 1]`;
- `physical_density` is the final filtered field `rho = (H @ x) / Hs`, lies in the
  same interval, and is the field used for stiffness, compliance, and the physical
  volume constraint.

The supervised prediction target for the first model is final `design_density`.
`physical_density` is retained for physical checks and optional auxiliary losses,
but it must not be passed directly as the optimizer's design initialization.

Model inference produces a finite raw design field `y` in `[0, 1]`. Before SIMP, it
is projected to the requested physical volume:

```text
x(lambda) = clip(y + lambda, minimum_density, 1)
rho(lambda) = (H @ x(lambda)) / Hs
choose lambda so abs(mean(rho(lambda)) - volume_fraction) <= 1e-6
```

Bisection uses the bracket `[-1, 1]` and at most 100 iterations. The same projection
is used for baseline warm starts. Wrong shape, non-finite values, values outside
`[0, 1]`, or failure to meet the projection tolerance triggers the uniform fallback.
`topolab.experiment.project_design_density` implements the projection and returns
x-fast `float64` design and physical vectors ready for the numerical core. It raises
an explicit error for invalid predictions or failed projection; the later experiment
runner owns the required fallback and cost accounting.

## Label generator and termination

Every label record and dataset manifest must store:

- `case_schema_version = "topolab.m0.case.v1"`;
- `generator_version = "topolab.m0.generator.v1"`;
- `solver_contract_version = "topolab.simp.v1"`;
- the exact 40-character TopoLab Git commit SHA from a clean worktree;
- the locked-environment digest and Python/NumPy/SciPy versions; and
- the full case ID and problem payload.

Labels are generated only through `topolab.simp.optimize_simp` from its uniform
default design (`x_e = volume_fraction`). The per-case optimization fields define the
filter, OC update, and termination settings. A label converges only after an OC update
and fresh finite-element solve produces
`max(abs(x_new - x_old)) <= convergence_tolerance`. Reaching `max_iterations`
without that condition is a generation failure, not a successful label. The stored
design density, physical density, compliance, volume, and change must all describe
the same final state, as required by the N2 contract.

Changing code revision does not change physical `case_id`; it creates a new label
artifact version. Two labels for the same case and generator version but different
revisions may coexist only for an explicit reproducibility comparison and may not be
mixed in one training dataset.

`topolab.labels.generate_label` implements the single-case generator through the
public problem adapter, which invokes the frozen `optimize_simp` path with
`initial_density = null` and therefore the uniform default. Solver exceptions,
missing history, non-convergence, an iteration-limit violation, a terminal density
change above tolerance, inconsistent final history, excessive volume error, or an
independent compliance re-solve outside `rtol = 1e-9` raises
`LabelGenerationError`; no partial label is returned.

`LabelRecord` uses `label_version = "topolab.m0.label.v1"` and stores all required
contract versions, source/environment provenance, the complete case, tensor
metadata, convergence metrics, final compliance, and physical volume. JSON stores
each density tensor as an x-fast flat sequence together with shape
`(1, nz, ny, nx)`, dtype `float32`, and axis order `channel,z,y,x`. During generation,
the terminal design field is materialized as `float32`, physical density is derived
again from that stored design through the frozen filter, and compliance and volume
are independently evaluated for the stored physical field. Deserialization rejects
non-`float32` values, a stale shape, a changed filter mapping, or inconsistent volume
and convergence metadata.

## Label artifact format

`topolab.label_artifacts` freezes one portable label file and its reference:

- `artifact_version = "topolab.m0.label-artifact.v1"`;
- file contents are `LabelRecord.model_dump(mode="json")` serialized with sorted
  object keys, ASCII escaping, no insignificant whitespace, UTF-8 encoding, and
  exactly one final newline;
- `sha256` is the full lowercase SHA-256 digest of those exact bytes, including the
  final newline, and `byte_size` is their exact length; and
- the POSIX relative path is
  `labels/<case_id>/<sha256>.json`, allowing labels for different revisions or
  environments to coexist without changing physical case identity.

`LabelArtifactReference` also records the case ID, generator version, and source
revision. Its path is derived from the case ID and checksum and cannot be supplied
independently. Writes create the parent directory, write and `fsync` a temporary file
in that same directory, then publish it with one atomic `os.replace`. Rewriting the
same bytes is idempotent; different bytes already present at the content-addressed
path are an error rather than being overwritten.

Reads verify, in order, file presence, byte size, SHA-256, `LabelRecord` schema,
canonical byte representation, and equality between reference provenance and label
contents. Any failure raises `LabelArtifactError`. These APIs operate on one label at
a time; tests use temporary directories, and this slice commits no generated label
or dataset artifact.

## Typed sample and dataset manifest

`topolab.dataset` implements the metadata boundary without writing tensors, labels,
or generated files:

- `DatasetSample` uses `sample_version = "topolab.m0.sample.v1"`, embeds the complete
  verified `ExperimentCase`, records its derived partition and dimensional
  `load_scale`, and re-derives both fields when deserialized;
- `DatasetEnvironment` records non-sensitive Python, NumPy, and SciPy version strings
  plus the lowercase SHA-256 digest of `uv.lock`;
- `DatasetManifest` uses `manifest_version = "topolab.m0.dataset.v1"`, embeds the
  case, generator, solver, and split contract versions, requires an exact lowercase
  40-character source commit and `source_tree_clean = true`, and freezes the tensor
  dtype, axis order, and channel names; and
- manifest samples are sorted by `case_id`, must be unique, and must reproduce the
  recorded positive count for every train, validation, test, and OOD partition.

On construction and every JSON read, the manifest rejects mixed fixed-shape cohorts,
stale derived metadata, changed schema constants, extra fields, or an OOD case whose
exact `y`-load counterpart is absent. The counterpart check changes only every load
direction from `z` to `y` and then uses the canonical case identity, so all other
physical fields must match. JSON serialization uses Pydantic's strict immutable
contracts.

## Recoverable materialization index

`topolab.materialization` associates one immutable manifest with its label outcomes
without running the solver:

- `index_version = "topolab.m0.materialization.v1"`;
- `manifest_sha256` covers canonical sorted-key, compact, ASCII-escaped UTF-8 JSON of
  the complete manifest, including exactly one final newline;
- the single-writer checkpoint path is
  `materializations/<manifest_sha256>.json`;
- a `succeeded` entry stores the manifest case ID, its frozen split, and one
  `LabelArtifactReference`; and
- a `failed` entry stores the case ID, split, and only the sanitized terminal code
  `label_generation_error` or `label_artifact_error`. It never persists exception
  messages, host paths, device identifiers, or partial labels.

Entries are canonicalized by `case_id` and unique. An `in_progress` index may omit
unattempted cases; absence is the only pending state. A `complete` index must contain
exactly one success or failure for every manifest sample, so failures cannot silently
disappear. Completion records that work finished, not that the dataset is suitable
for training: any failed entry keeps M0 dataset materialization unsuccessful.

Every success must match the manifest case, split, generator version, source
revision, solver/case contract versions, and locked environment. Reads and writes
re-verify the referenced label bytes through `read_label_artifact`. Checkpoint updates
are append-only: an existing outcome cannot be removed or changed, and a complete
index is immutable. A retryable interruption therefore leaves the case absent; only
a terminal attempt is recorded as failed. Fixing a recorded terminal failure requires
a new auditable manifest/source revision rather than rewriting history.

Writes use a same-directory temporary file, flush and `fsync`, and atomic
`os.replace`. Repeating identical content is idempotent. A crash after a label is
published but before its success entry is checkpointed is safe because label writes
are content-addressed and idempotent.

`materialize_dataset` is the single-process, single-writer executor for a supplied
manifest. It creates an empty checkpoint before solving, validates and resumes an
existing checkpoint, skips every recorded case, and visits remaining samples in the
manifest's canonical `case_id` order. For each pending sample it calls the frozen
single-case generator with the manifest revision and environment, publishes the
content-addressed label, and atomically checkpoints that success before continuing.

`LabelGenerationError` becomes terminal code `label_generation_error`;
`LabelArtifactError` becomes `label_artifact_error`. Both are checkpointed and the
executor continues so every attempted case remains visible. Any other exception or
process interruption propagates immediately and leaves that case absent, preserving
an `in_progress` checkpoint for retry. Only after every manifest case has a recorded
outcome is the index changed to `complete`. Re-running a complete index performs no
generation. Tests materialize only small temporary fixtures; the repository commits
no generated label or dataset files.

## Bounded M0 v2 case catalog

`topolab.catalog` freezes the first production population independently of source
revision and runtime environment. `CaseCatalog` is a strict immutable contract with
`catalog_version = "topolab.m0.catalog.v2"`, the complete sorted `ExperimentCase`
tuple, and a verified content-derived `catalog_id`. The ID hashes compact,
sorted-key, ASCII-escaped canonical JSON containing the catalog version and sorted
case IDs. The frozen catalog identity is:

```text
tlcatalog-v2-4ba44e175ca47f85aa0fbcafbc9456b2a1b672fd181430ec9aef29a468f46500
```

Because every case ID already covers the complete normalized physical problem, the
catalog digest transitively covers every case field. Source revision, environment,
split counts, and tensor metadata enter the separately identified `DatasetManifest`
when `CaseCatalog.build_manifest` is called; they are deliberately not physical case
catalog identity.

The exact v2 enumeration is:

| Field | Frozen value |
|---|---|
| Mesh | `(nx, ny, nz) = (12, 6, 3)` and `(Lx, Ly, Lz) = (12.0, 6.0, 3.0)` |
| Material | `E0 = 1000.0`, `Emin = 1.0`, `nu = 0.3` |
| Support | all displacement components on the `x=min` face |
| Point-load face | `x=max` |
| Loaded-node `y` indices | `[0, 2, 4, 6]` |
| Loaded-node `z` indices | `[0, 1, 2, 3]` |
| ID load | one `y` component with magnitude `-1.0` |
| Matched OOD load | the same node and magnitude with direction changed only to `z` |
| Target physical volume fractions | `[0.2, 0.3, 0.4, 0.5, 0.6]` |
| SIMP/filter settings | radius `1.5`, penalty `3.0`, minimum density `0.05`, move limit `0.2` |
| Termination | density-change tolerance `0.01`, maximum `120` iterations |

Node identity follows the repository's x-fast convention:
`node = nx + (nx + 1) * (y_index + (ny + 1) * z_index)`. The mesh therefore has
unit-cube elements, 216 elements, 364 nodes, and 1,092 displacement DOFs. Cartesian
enumeration produces 16 load locations times five volume fractions: 80 ID cases plus
80 exact OOD counterparts, for 160 cases total. The frozen ID hash rule produces
66 train, 8 validation, and 6 test cases; all 80 direction-shifted cases are OOD.
These counts are pre-label and must not be rebalanced after materialization.

Catalog v1 remains frozen as
`tlcatalog-v1-e532ad3d9de3083918e1ab074e7ba3b88a254d0b6729af508f96959ea1eedc3d`
with a 100-iteration maximum and split counts 60/9/11/80. Its complete materialization
is immutable failed-gate evidence, not training data. The only physical-case change
in v2 is the maximum iteration budget. The case schema remains
`topolab.m0.case.v1`, the convergence tolerance remains `0.01`, the split algorithm
remains `topolab.m0.split.v1`, and no case is removed or rebalanced. Because maximum
iterations participates in physical case identity, all case IDs, the catalog ID, and
the next manifest identity necessarily change.

`build_m0_case_catalog` rechecks the pinned catalog ID, and the manifest constructor
rechecks uniqueness, fixed-cohort identity, positive partitions, and every OOD pair.
This slice enumerates metadata only. It does not solve the catalog or write generated
artifacts.

## Production catalog entrypoint

`topolab.dataset_cli` is the sole production entrypoint for turning the frozen M0
catalog into a revision- and environment-specific manifest. From the TopoLab
repository root, plan the operation with:

```bash
PYTHONPATH=src uv run --locked python -m topolab.dataset_cli \
  --output-root /absolute/path/outside/TopoLab
```

Planning is the default and is read-only: it does not create the output root, a
manifest file, a checkpoint, or labels. It prints one sorted-key, versioned JSON
object with the catalog ID, manifest SHA-256, exact clean-source declaration and
revision, split counts, total cases, and the non-sensitive Python/NumPy/SciPy and
`uv.lock` metadata embedded in the manifest. It deliberately omits repository and
output paths. The summary schema version is
`topolab.m0.materialization-summary.v1`.

The entrypoint requires a Git worktree with no tracked or non-ignored untracked
changes, captures the exact 40-character `HEAD`, hashes the checkout's `uv.lock`, and
records the versions of the active runtime. It resolves the requested output path and
rejects the repository root or any descendant, including paths reached through an
existing symlink. These checks apply in planning mode so the exact proposed manifest
and destination policy can be reviewed before solving.

Only an explicit execution flag starts the existing single-process, single-writer
materializer:

```bash
PYTHONPATH=src uv run --locked python -m topolab.dataset_cli \
  --output-root /absolute/path/outside/TopoLab \
  --execute
```

Execution retains the materializer's atomic per-case checkpoint and resume rules. A
complete index containing one or more terminal case failures is summarized but exits
with status 1; an unsafe checkout or output location exits with status 2. Unexpected
exceptions continue to propagate so an interrupted case remains pending. The
entrypoint never writes generated data into the source repository. Its control path
is covered with temporary fixtures. The v1 complete external execution, its four
correctly recorded failures, and the evidence for the v2 revision are documented in
`docs/validation/m0_catalog_materialization.md`; no generated artifact is committed.

## Dataset split and leakage prevention

Splitting is by complete `case_id`, before tensorization, augmentation, or access to
labels. A case, every optimizer history state, every derived tensor, and every repeat
remain in exactly one partition. Final labels are the only supervised samples in
`m0.v1`; history rows are not samples.

The primary in-distribution pool contains cases whose nonzero loads are all in the
`y` direction. Assign each ID case with:

```text
h = sha256(utf8("topolab.m0.split.v1:" + case_id))
bucket = int(first 8 hex digits of h, 16) % 100
train: 0..79; validation: 80..89; test: 90..99
```

The manifest records the resulting counts; it must not move cases to improve the
ratio after labels or metrics are inspected. Model fitting and hyperparameter choices
use train/validation only. Test labels remain unopened until the experiment plan and
checkpoint-selection rule are frozen. Nearest-neighbor search uses training cases
only.

The predeclared primary OOD axis is **load direction**. OOD cases are matched to ID
cases by mesh, material, support, load kind/location/magnitude, volume fraction, and
optimizer settings, but every `y` load component is changed to `z`. Mixed-direction
loads and `x`-directed loads are outside the primary `m0.v1` evaluation. OOD cases
never enter the hash split or model selection.

## Fixed baselines

All methods use the same volume projection and the same refinement solver/settings.

1. **Uniform.** Set every design element to the target volume fraction. A constant
   field is unchanged by the normalized density filter.
2. **Physics heuristic.** Solve once at uniform physical density. For each element,
   set `s_e = max(0, -dC/drho_e)` from the analytical compliance sensitivity. If
   `max(s) > min(s)`, min-max normalize `s` to `[0, 1]`; otherwise use the uniform
   field. Project the result to the target physical volume. The extra finite-element
   solve is part of baseline setup time.
3. **Nearest neighbor.** Among training cases in the same fixed-shape cohort, choose
   the smallest mean-squared distance between the complete 10-channel input tensors;
   break exact ties by lexicographically smallest `case_id`. Use that case's final
   design-density label, then re-project it to the query volume fraction. Query time
   and stored-index size are reported; validation, test, and OOD labels are never
   candidates.

No baseline may use a query label, final compliance, or optimizer history to choose
its initialization.

`topolab.baselines` implements these definitions for one held-out or OOD
`DatasetSample`. `build_nearest_neighbor_index` requires a complete zero-failure
materialization and reads artifacts only for samples whose frozen split is `train`.
The in-memory index stores sorted case IDs, complete `float32` input tensors, and
final `float32` design labels. Its reported storage size is the sum of those tensor
buffers and the UTF-8 case-ID bytes; Python object overhead and the external artifact
store are reported separately rather than estimated.

`run_fixed_baselines` runs uniform first as the mandatory per-case reference, then
the physics heuristic and nearest neighbor through the same projection and public
SIMP solver. Training samples are rejected as evaluation queries. Exact nearest-
neighbor distance ties select the lexicographically first case ID. A non-uniform
setup, projection, refinement, or quality failure triggers a fresh uniform fallback;
the full fallback is charged while the original method remains failed. A uniform
reference or fallback failure is a dataset/evaluation error, not a recoverable method
result.

`BaselineCaseResult` records candidate and operational metrics separately, so a
valid fallback cannot overwrite the failed candidate's status. Setup, projection,
refinement, and fallback wall times are recorded independently. Nearest-neighbor
index construction and label loading are dataset setup costs, not per-query setup
time. The current in-process runner does not report a per-method peak-memory number
because process-wide high-water marks cannot isolate sequential methods
reproducibly; that metric requires a later isolated-process experiment harness.

`topolab.learned_evaluation` applies the same per-case boundary to one verified M1
selection/checkpoint: CPU `float32` inference, frozen filtered-volume projection,
public SIMP refinement, the shared quality audit, and a fresh fully charged uniform
fallback after any failed learned attempt. It rejects training queries and accepts
no query label. Checkpoint loading is an experiment setup cost; encoding, tensor
construction, inference, and output validation are learned per-query setup time.
Production test/OOD execution remains outside this implemented single-case slice.

## Quality constraints and failures

The uniform method is the per-case quality reference. A refined candidate succeeds
only when all of the following hold:

- the solver reports convergence before the iteration limit;
- every returned density, displacement, reaction, compliance, and history metric is
  finite;
- `abs(mean(final_physical_density) - volume_fraction) <= 5e-3`;
- independently re-solving the final physical density reproduces final compliance
  within `rtol=1e-9`; and
- final compliance is no greater than `1.001 * uniform_final_compliance`.

A solver exception, invalid prediction, projection failure, non-convergence, quality
violation, missing artifact, or schema/version mismatch is a failure. A case whose
uniform reference fails is a dataset/evaluation failure and is reported separately;
it must not be used to make another method's failure rate look smaller.

## Cost and statistical reporting

Report at least these per-case values for every method:

- warm-start setup time (heuristic solve, neighbor query, or model preprocessing and
  inference);
- volume-projection time;
- SIMP refinement time and iteration count;
- end-to-end time, defined as the sum of the preceding three plus the full fallback
  time when fallback is used;
- final compliance, physical volume error, convergence/failure, and fallback use; and
- peak process memory where the runner can measure it reproducibly.

Dataset generation time, training time, hardware, thread count, and artifact size
are reported separately and are never hidden inside an amortized speedup claim.
Learned end-to-end time includes host/device transfer and synchronization.

Use model/training seeds `[17, 29, 43, 71, 113]`. Report every seed, not only the
best. The primary comparison is the paired per-case end-to-end time ratio to uniform,
reported separately for ID test and OOD. The 95% confidence interval uses 10,000
case-cluster bootstrap resamples with seed `20260919`; each resampled case retains all
five model seeds. Also report median, interquartile range, failure rate, and quality
metrics without dropping failed cases.

An acceleration claim requires the upper bound of the ID-test 95% confidence
interval for the mean learned/uniform end-to-end time ratio to be below 1.0, all
quality constraints to hold, and no increase in failure rate. OOD results are always
reported but are not relabeled as in-distribution evidence.

## Fallback and stopping rule

If model output validation or projection fails, run uniform initialization. If a
learned refinement fails a quality constraint, rerun from uniform. The fallback's
full time is added to learned end-to-end cost, and the event remains a learned-method
failure; fallback must not convert it into a learned success.

After the fixed lightweight model family, finite hyperparameter budget, five seeds,
and ID/OOD evaluation are complete, an inconclusive or negative result is frozen and
analyzed. It does not authorize unbounded search. In that outcome the project keeps
uniform as its operational default and does not use `learned-accelerated` wording.
