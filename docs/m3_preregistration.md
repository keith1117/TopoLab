# M3 warm-start experiment pre-registration

Status: **M3.0 pre-registered; no M3 fitting or final evaluation has run.** This
contract supersedes neither the failed M1 claim gate nor the failed M2 data gate.
Uniform initialization remains the operational default. The exposed-case diagnosis
and Gate M3.0 decision are in `docs/validation/m3_preregistration.md`.

## Question and immutable evidence boundary

Can direction-balanced training plus one larger-receptive-field CNN, selected with a
validation-only reliability policy, produce a lower **fallback-inclusive paired
end-to-end time ratio** than uniform initialization on new, physically disjoint ID
cases while preserving the M1 quality bound? The first falsifiable intervention
against a retrained M1 control is dilation of the second 3-D convolution. If the
M3.2/M3.3 validation gates below fail, do not open final evidence. A failed final
comparison is published as a negative result; it does not authorize an M3.5 search.

M0 v1/v2, M1 held-out cases, and all M2 outcomes are development-exposed. In
particular, M2's 36 test and 252 OOD labels are **not** M3 fitting or selection
inputs. M2's failed gate remains failed. M3 may reuse only the successful M2
`train` and `validation` label references, after M3.1 audits them and records an
exposure ledger. No M3 final case definition, label, solver result, or statistic may
inform fitting, checkpoint selection, reliability thresholds, or stopping.

## Frozen versions and case catalog

| Boundary | Version or identity |
|---|---|
| Physical case and input encoding | `topolab.m0.case.v1`; ten-channel M0 encoding |
| Numerical solver, label, and projection | frozen `topolab.simp.v1`, `topolab.m0.label.v1`, and M0 projection |
| M3 split, catalog, training, gate, experiment | `topolab.m3.split.v1`, `topolab.m3.catalog.v1`, `topolab.m3.training.v1`, `topolab.m3.gate.v1`, `topolab.m3.experiment.v1` |
| M3 manifest, index, checkpoint, selection, evaluation | `topolab.m3.dataset.v1`, `topolab.m3.materialization.v1`, `topolab.m3.checkpoint.v1`, `topolab.m3.selection.v1`, `topolab.m3.evaluation-index.v1` |
| M2 source manifest SHA-256 | `99b63e4b49d29764b033b8d8af6664801454d6e5bcf34df68d9e6471a71ba33f` |
| M2 source index SHA-256 | `c1374735bc80ace561f99a6e03497ad2dce3e08c1fb600a4e1d938c73383fd7f` |
| M3 catalog SHA-256 | `ddb0a0b4c6b3e5790187acad70459e6128b1f94d8a8b3be7ea8339395a16cbe3` |

The M3 catalog has 564 cases: the unchanged 432 M2 `train` and 36 M2
`validation` case IDs, plus 64 new ID `test` and 32 new `ood` case IDs. Do not
rebalance or omit an M2 case because its label failed. Keep the M2 mesh
`(12, 6, 3)`, lengths `(12, 6, 3)`, material, `x=min` clamp, `x=max` point-load
magnitude, filter radius `1.5`, penalty `3.0`, minimum density `0.05`, move limit
`0.2`, tolerance `0.01`, and 120-iteration limit. All 28 loaded-face node locations
and the nine volume fractions `0.20, 0.25, ..., 0.60` remain in the inherited
train/validation pool. ID directions are `y` and `z`; OOD is `x`.

New final volumes are exactly `0.225, 0.275, 0.325, 0.375, 0.425, 0.475, 0.525,
0.575`. They lie between all M2 volumes, so the new final cases are physically
disjoint from every M0/M1/M2 case even when solver-iteration metadata is ignored.
ID final testing therefore includes interpolation to unseen volume fractions;
OOD additionally changes the load direction to `x`.
For each final volume, order the 28 `(y,z)` loaded-face node positions by the
lowercase hex SHA-256 of the UTF-8 string
`topolab.m3.final-split.v1:{volume:.3f}:{y}:{z}`, breaking ties by x-fast node
index. Take the first four positions. At each chosen position, construct one case
for each `x`, `y`, and `z` signed load direction, with all other M2 physical fields
unchanged. Assign `y/z` to `test` and `x` to `ood`. The precomputed positions are:

| Volume | Four `(y,z)` positions, in hash order |
|---:|---|
| 0.225 | `(2,1)`, `(4,3)`, `(1,1)`, `(6,2)` |
| 0.275 | `(4,2)`, `(4,0)`, `(2,3)`, `(0,1)` |
| 0.325 | `(0,3)`, `(3,2)`, `(3,0)`, `(4,0)` |
| 0.375 | `(3,2)`, `(0,1)`, `(6,0)`, `(6,1)` |
| 0.425 | `(1,3)`, `(2,3)`, `(2,2)`, `(6,1)` |
| 0.475 | `(6,2)`, `(2,2)`, `(2,3)`, `(4,3)` |
| 0.525 | `(3,1)`, `(6,3)`, `(3,0)`, `(4,1)` |
| 0.575 | `(6,0)`, `(6,1)`, `(1,2)`, `(0,2)` |

For catalog identity, build each new case with `ExperimentCase.from_problem`.
Serialize `{"catalog_version":"topolab.m3.catalog.v1","entries":[...]}` with
every entry containing exactly `case_id` and `split`. Sort entries by `case_id`,
then serialize with sorted JSON keys, ASCII escaping, no spaces, and one terminal
newline. The SHA-256 of those bytes must equal the catalog digest above. M3.1 must
verify that identity and an exposure ledger of all physical M0/M1/M2 cases before
any fitting. The ledger fingerprint is canonical full problem JSON with only
`optimization.max_iterations` removed; this supplementary fingerprint prevents an
iteration-budget change from disguising a previously exposed physical problem.
The final-case fingerprint intersection with the ledger must be empty.

## Label availability and data gate

M3.1 first verifies the exact M2 index bytes, manifest, source revision,
environment, all entry metadata, and all ten retained terminal failures. It
reopens and audits only the 461 successful `train`/`validation` label artifacts;
M2 `test`/`ood` label bytes remain unopened by M3 development. It then constructs
a read-only M3 plan from a clean, locked
revision; plan mode must not create an output root or invoke the solver. Only the
425 successful M2 training labels and 36 successful M2 validation labels are usable
for fitting/selection. Failed entries remain in the catalog, ledger, denominator,
and report; they are never imputed, silently retried, or relabeled as successes.
No new label generation is authorized by this M3.0 contract. M3.1 must present any
separate materialization need and its read-only plan before execution.

This is a pre-registered **availability gate** for M3, applied after the already
exposed M2 result. It requires at least 420/432 successful training labels, all
36/36 validation labels, and at least 16/24 successes in each of the 18
`(direction, volume)` training strata. These thresholds explicitly accommodate the
known seven failures in the `y, 0.45` stratum; they do not revise M2's failed
complete-label gate. The 36 M2 test and 252 OOD labels remain unopened by M3
fitting and calibration code even though M2 materialized them.

All solver calls retain the 120-iteration ceiling and convergence tolerance `0.01`.
A non-convergent label is unavailable, with its reason retained. Final cases have
metadata only before the frozen M3.4 evaluation; no final query label is needed or
generated for fitting. If a final uniform reference fails to converge, record the
case as a benchmark failure and fail the claim gate without removing or replacing
the case. Never raise the budget or issue a favorable replacement catalog under
this experiment identity.

## Fixed fitting and ablation budget

Fit exactly two model types from scratch on the same usable training labels:

1. **Control and ablation:** the M1 CNN with `Conv3d(10,16,3,padding=1)`, ReLU,
   `Conv3d(16,16,3,padding=1)`, ReLU, and `Conv3d(16,1,1)` plus sigmoid. This is
   also the ablation that removes the candidate's one new component.
2. **Primary candidate:** the identical 11,281-parameter network and initialization
   recipe, changing only the second convolution to `dilation=2,padding=2`. This
   increases the receptive field from five to seven cells without changing shape,
   parameter count, input, or inference target.

The sole loss is unweighted mean-squared error to final **design** density. Use
AdamW at `1e-3`, weight decay `1e-4`, batch size 8, at most 200 epochs, patience 25,
and the earliest strict minimum validation MSE checkpoint. Use seeds
`[17,29,43,71,113]` for both types; retain every seed. No learning-rate,
architecture, loss-weight, data-augmentation, or seed search is allowed. Control
and ablation are the same five fits, so the maximum is ten fits and 2,000 attempted
epochs total. Fit on the Apple M2 CPU with the locked environment, one PyTorch
intra-op thread, eight inter-op threads, no GPU, at most two hours wall time and
4 GiB peak process RSS for all fitting. If either budget is exceeded, stop; do not
substitute hardware or extend the budget under the same experiment identity.

For each type, evaluate the equal-weight five-seed ensemble. Project every member
independently, compute the mean population variance of projected element densities,
average members, and project that mean again, as in the frozen M2 ensemble recipe.
The five inferences, projections, variance, and decision time are charged per
query. Checkpoint loading and training are reported separately.

## Validation-only selection and reliability policies

Evaluate both raw ensembles and the following **seven** named policies on all
36 validation cases, using the same frozen uniform reference for each case:

| Policy | Accept when |
|---|---|
| R0 | never |
| R1 | volume `<= 0.30` and uncertainty `<= Q50` |
| R2 | volume `<= 0.30` |
| R3 | volume `<= 0.40` and uncertainty `<= Q50` |
| R4 | volume `<= 0.40` |
| R5 | uncertainty `<= Q50` |
| R6 | always |

`Q50` is the linear median of the 36 validation uncertainty scores **for that model
type**, computed before evaluating policy outcomes. No other threshold or composite
score may be tried. Rejection runs uniform after the fully charged ensemble setup
and is recorded as rejection, not learned success. An accepted failure receives a
fresh, fully charged uniform fallback and remains a learned failure. A policy is
eligible only with zero accepted quality/refinement failures on all 36 validation
cases. Choose the eligible policy with the lowest arithmetic mean of paired
end-to-end ratios; exact ties choose fewer accepted cases, then the earlier policy
in the table. Retain all policies, failures, cases, and charges in the calibration
artifact.

M3.2 proceeds to the freeze only if the primary raw ensemble has **no more**
validation quality failures than the control raw ensemble, and its selected eligible
policy accepts at least one case, has zero accepted failures, has mean ratio below
both `1.0` and the control's selected eligible policy, and is faster than the
control's raw ensemble on the fallback-inclusive mean ratio. If any condition
fails, stop before opening final evidence. This is a deliberately demanding
validation screen, not a claim of acceleration.

Freeze source revision, manifest/index digests, ten checkpoints and five selections
per type, the selected policy and Q50 value, statistics code, and runtime before
M3.4. Rebuild and audit those artifacts from a clean checkout. Do not inspect M3
final outcomes while adjusting any of them.

## One-time final evaluation and claim rule

Evaluate the 64 ID cases first, in case-ID order, then the 32 matched `x` OOD cases.
For every case run the uniform reference, unchanged physics heuristic, nearest
neighbor built only from usable M3 training labels, control ensemble with its
frozen policy, and primary ensemble with its frozen policy. Preserve the frozen M1
checks: convergence before 120 iterations, finite state, physical-volume error
`<= 5e-3`, independently checked compliance, and candidate final compliance
`<= 1.001 *` uniform final compliance. Report rejected, failed, and fallback
attempts separately; every end-to-end time includes setup, inference, projection,
refinement, decision, and any full fallback. Training, data preparation, and
checkpoint loading stay in separate cost tables.

The primary metric is the arithmetic mean per-case primary/uniform end-to-end
ratio on all 64 ID cases. Use 10,000 physical-case bootstrap resamples with
`numpy.random.default_rng(20260925)` and linear 2.5th/97.5th percentiles,
reinitializing the generator for OOD. Report the 95% interval, median, IQR,
iterations, compliance, volume error, rejection/failure/fallback rate, memory,
and all method costs for ID and OOD separately. The ID acceleration claim requires
the upper 95% limit `< 1.0`, zero failures/fallbacks among accepted primary
attempts, and every operational result meeting the quality contract. The optional
`OOD-safe` qualifier additionally requires zero accepted OOD failures and OOD upper
95% limit `<= 1.05`. A uniform-reference failure, missing case, altered threshold,
or incomplete comparison defeats the relevant claim rather than changing the
denominator. Uniform remains the default until this one-time gate actually passes.
