# M1 held-out warm-start evaluation

Date: 2026-09-23

Evaluation source revision: `d66d71ef99a8ed3f774177bc1c2ecb15fbe5fe4e`

Training source revision: `a538d40ffaf3da20e8a06ff9e3ac136da72b5718`

M0 label source revision: `015ec12779c5983bb55eaa41f31ee33de47493eb`

Catalog ID:
`tlcatalog-v2-4ba44e175ca47f85aa0fbcafbc9456b2a1b672fd181430ec9aef29a468f46500`

Manifest SHA-256:
`7e732446d683a3609ec3e4af4b87d334caeb583c69da3db9ea0f47f91d119d5a`

Evaluation ID:
`313d08d3be084e97718d5d16248e0ee0571b3308e8de3e64769401dc563f9d14`

## Scope and decision

The guarded production runner completed the single frozen M1 comparison over all 6
ID-test and 80 OOD physical cases. Each case contains the uniform,
physics-heuristic, and training-only nearest-neighbor baselines plus all five frozen
learned seeds. The final canonical index contains 86 complete entries and no omitted
case.

**M1 does not pass the learned-acceleration gate.** The ID-test aggregate mean
learned/uniform end-to-end time ratio was `1.1927843196826227`; its predefined 95%
case-cluster bootstrap interval was
`[0.8430970096578101, 1.6335695791387947]`, whose upper bound is not below `1.0`.
The learned attempts also failed and used the fully charged uniform fallback in 7 of
30 ID-test observations. On OOD, the mean ratio was `1.5496787371485803` with interval
`[1.3452806478658774, 1.7600387510507451]` and 100 failures/fallbacks among 400
observations.

These results do not support `accelerated`, `learned-accelerated`, or stable learned
speedup claims. Uniform initialization remains the operational default. The complete,
negative/inconclusive result is retained as validation evidence rather than selecting
a favorable seed or dropping failed cases.

## Frozen execution boundary

- Evaluation index version: `topolab.m1.evaluation-index.v1`.
- Experiment version: `topolab.m1.experiment.v1`.
- Statistics version: `topolab.m1.statistics.v1`.
- Model seeds: `17`, `29`, `43`, `71`, and `113`.
- ID-test physical cases: 6; learned observations: 30.
- OOD physical cases: 80; learned observations: 400.
- Compared outcomes per physical case: three baselines and five learned seeds.
- Bootstrap: 10,000 case-cluster resamples with seed `20260919`, independently reset
  for ID test and OOD.
- Every failed attempt remains failed, retains its cost, and fully charges a fresh
  uniform fallback.
- The nearest-neighbor index opened only the 66 training labels. No ID-test or OOD
  label artifact was opened, and query labels did not participate in inference,
  refinement, quality checks, or method selection.

The runner used the exact five selection and checkpoint hashes recorded in
`docs/validation/m1_training.md`. No seed, epoch, quality threshold, physical case,
or statistic changed after held-out behavior was observed.

## Aggregate learned results

Time ratios are paired to the matching physical case's uniform end-to-end time. A
ratio below `1.0` is faster than uniform; a ratio above `1.0` is slower. Failure and
fallback observations remain in every timing statistic.

| Split | Cases | Observations | Mean ratio | 95% bootstrap interval | Median | IQR | Failure/fallback rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| ID test | 6 | 30 | `1.192784` | `[0.843097, 1.633570]` | `0.876877` | `[0.746161, 1.752526]` | `23.33%` |
| OOD | 80 | 400 | `1.549679` | `[1.345281, 1.760039]` | `1.503171` | `[0.703941, 2.261668]` | `25.00%` |

The six-case ID-test interval is wide and crosses `1.0`, so its apparent median
speedup is not stable evidence. The OOD interval lies entirely above `1.0`; under the
frozen charged-fallback metric, the learned method is slower than uniform on this
direction shift.

## Per-method ID-test results

Operational iterations and compliance include the uniform fallback when an attempt
fails; the failure column preserves the original method outcome.

| Method | Seed | Mean time ratio | Median time ratio | Median operational iterations | Failure/fallback rate |
|---|---:|---:|---:|---:|---:|
| Uniform | - | `1.000000` | `1.000000` | `51.0` | `0.00%` |
| Physics heuristic | - | `1.276782` | `1.229749` | `58.0` | `16.67%` |
| Nearest neighbor | - | `1.717769` | `1.241799` | `52.0` | `50.00%` |
| Learned | 17 | `1.025115` | `0.765122` | `44.0` | `16.67%` |
| Learned | 29 | `1.169213` | `0.806129` | `44.0` | `16.67%` |
| Learned | 43 | `1.041237` | `0.824618` | `48.0` | `16.67%` |
| Learned | 71 | `1.427914` | `1.215984` | `46.5` | `50.00%` |
| Learned | 113 | `1.300443` | `0.976909` | `52.0` | `16.67%` |

Seeds 17, 29, and 43 show a descriptive median below `1.0`, but every learned seed
has at least one ID-test failure and the aggregate confidence interval does not meet
the frozen claim threshold. Seed 71 is not removed despite its higher failure rate.

## Per-method OOD results

| Method | Seed | Mean time ratio | Median time ratio | Median operational iterations | Failure/fallback rate |
|---|---:|---:|---:|---:|---:|
| Uniform | - | `1.000000` | `1.000000` | `51.5` | `0.00%` |
| Physics heuristic | - | `1.253719` | `1.167195` | `55.5` | `15.00%` |
| Nearest neighbor | - | `1.734923` | `1.731716` | `57.0` | `22.50%` |
| Learned | 17 | `1.522714` | `1.478282` | `43.0` | `23.75%` |
| Learned | 29 | `1.572927` | `1.537914` | `56.0` | `26.25%` |
| Learned | 43 | `1.525280` | `1.621894` | `44.5` | `28.75%` |
| Learned | 71 | `1.603958` | `1.239516` | `42.0` | `21.25%` |
| Learned | 113 | `1.523514` | `1.409575` | `44.0` | `25.00%` |

The OOD failure rates are distributed across all five seeds rather than isolated to
one unfavorable checkpoint. Although several operational iteration medians are below
uniform, the failed candidate plus fresh uniform fallback dominates the end-to-end
cost distribution.

## Failure audit

All 107 learned failures were classified as `quality_error`:

- 7 of 30 learned ID-test observations failed;
- 100 of 400 learned OOD observations failed;
- every failed candidate exceeded the frozen
  `1.001 * uniform_final_compliance` limit;
- 18 failed candidates also reached the 120-iteration limit;
- no failure was attributed to checkpoint loading, tensor shape, dtype, finiteness,
  prediction bounds, volume projection, or volume tolerance; and
- the maximum physical-volume error among failed learned candidates was
  `9.529292577248327e-09`, far below the frozen `5e-3` tolerance.

The evidence therefore points to solution-quality and generalization limitations,
not an invalid artifact or broken inference/projection path. The first experiment
trained on 66 `y`-direction cases and defined OOD by changing the matched load to the
previously unseen `z` direction. The outcome is consistent with a model/data/loss
boundary that does not generalize reliably across that shift, but this interpretation
is post-hoc and is not a new causal claim.

## Runtime and artifact audit

- Hardware: Apple M2, 8 logical cores, 8 GiB memory.
- Operating system: macOS 26.5, `arm64`.
- Python 3.12.10.
- NumPy 2.5.3, SciPy 1.18.1, PyTorch 2.14.0, Safetensors 0.8.0.
- Evaluation PyTorch intra-op threads: 4; inter-op threads: 8.
- `uv.lock` SHA-256:
  `34e089881d5601a4331cb26896413b9850d8ffc69f87eeaffda352d68db2111d`.
- Source worktree: clean, with both runner slices merged and CI passing before the
  read-only plan and explicit execution.

The final canonical evaluation index is stored outside Git at:

```text
m1/evaluations/7e732446d683a3609ec3e4af4b87d334caeb583c69da3db9ea0f47f91d119d5a/313d08d3be084e97718d5d16248e0ee0571b3308e8de3e64769401dc563f9d14.json
```

It records `state = complete`, has byte size `1,153,668`, and has SHA-256
`2d15a9303fb4dd6b07ff224a027b2650a0eabcaf0391d5db642f40777fed1f73`.
Generated evaluation artifacts remain outside Git.

## Gate result and next action

The predefined M1 experiment is complete and its result is frozen. It establishes a
reproducible negative/inconclusive learned-acceleration result, not a production
speedup. TopoLab retains the learned path as an audited experiment and uniform as the
operational default.

The observed ID-test and OOD cases are no longer untouched evidence for model-family,
loss, training-data, reliability-gate, or hyperparameter decisions. Any M2 study must
be versioned as a new experiment, declare its finite intervention budget before
fitting, and reserve a new untouched final holdout/OOD boundary. Existing M1 results
may motivate that contract but cannot be reused as independent confirmation of an M2
acceleration claim.
