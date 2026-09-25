# B2 development-only workload and scale pilot

Date: 2026-09-25

Runner/protocol revision: `4ef92f1`

Status: **the fixed pilot completed; Gate B2 does not pass.** The oracle shows
conditional headroom, but three of six larger uniform references fail the
frozen convergence gate and the current learned panel is slower after full
fallback charges. This is not an ML-acceleration claim.

## Frozen pilot boundary

The [protocol](../planning/b2_workload_pilot_protocol.md) fixed twelve
cantilever cases before execution: six `(y/z direction, 0.20/0.45/0.60
volume)` strata at each of two nested Hex8 scales. The small definitions are
development-exposed M2 validation metadata; the large definitions preserve the
physical load position on a refined mesh. The A3 automatic SuperLU ordering,
120-iteration cap, `0.01` density-change tolerance, physical domain, and
material/settings apply equally to all methods. The pilot never opens M2
test/OOD or any M2 label artifact. All twelve cases and their outcomes will
remain in the denominator.

The methods are optimized uniform, an impossible own-uniform-result oracle,
the frozen sensitivity heuristic, the fixed M1 training-only nearest-neighbor
index on the small scale, and all five unchanged M1 checkpoints at both
scales. Every failed non-uniform candidate pays for a fresh uniform fallback.
Per-query setup, projection, refinement, FEM, fallback, memory, and
index/checkpoint setup are recorded separately. The independent quality-audit
re-solve is excluded from each method's timed cost.

## Execution and resource evidence

The protocol and runner were committed at `4ef92f1` before execution. The
read-only plan printed exactly the twelve fixed case IDs. Execution then read
the verified M2 materialization index SHA-256
`c1374735bc80ace561f99a6e03497ad2dce3e08c1fb600a4e1d938c73383fd7f`
and only its validation case definitions; it opened no M2 label artifact.
The nearest-neighbor index opened only the frozen M1 **training** labels, and
all five exact M1 production selections/checkpoints were loaded. Generated
diagnostic JSON was written outside Git to `/tmp/topolab-b2-pilot.json`
(SHA-256 `5b5959087ef8cd863e075c11fa1c7e4301f484775c130dfe91ba50262f9e400a`).

The local run used Apple M2 arm64, macOS 26.5, the locked Python 3.12.10,
NumPy 2.5.3 and SciPy 1.18.1 environment, and one thread for OpenMP, BLAS,
VECLIB, and MKL. The measured pilot loop took **592.85 s wall** with a
process-wide peak RSS of **418.20 MiB**. M1 training-index loading took 0.353 s
and stored 0.603 MiB; loading the five checkpoints took 0.0275 s. These are
one-time setup costs, reported separately from the per-query comparisons;
any deployment claim must amortize them over its actual query count. The
process peak includes PyTorch, SciPy, models, all cases, and allocator
retention, so it cannot attribute a method-specific memory footprint.

Uniform reference time across the six small cases totaled 2.67 s and across
the six large cases 114.19 s. Each method's query time includes its own setup,
projection, refinement, and charged fallback. The independent quality-audit
re-solve is excluded consistently from method timings. Median FEM time per
uniform analysis call was 0.0090 s at the small scale and 0.1758 s at the
large scale; FEM consumed median 92.5% and 97.6% of refinement wall time,
respectively. A single timed run supports a development decision, not a
confidence interval or a portable performance guarantee.

## Fixed case outcomes

The learned column includes all five fixed seeds for that case. A `pass` means
the candidate itself met the frozen convergence, independent compliance,
volume, and uniform-quality checks; any failure triggered a fresh, fully
charged uniform fallback. Ratios divide by that case's optimized uniform
query time. Failed uniform cases have no valid paired denominator and remain
in the planned cohort.

| Mesh | Direction | Volume | Uniform iterations / status | Oracle charged ratio | Learned passes / 5 | Learned mean charged ratio |
|---|---|---:|---:|---:|---:|---:|
| `12 x 6 x 3` | y | 0.20 | 32 / pass | 0.083 | 5 | 1.161 |
| `24 x 12 x 6` | y | 0.20 | 103 / pass | 0.031 | 4 | 1.066 |
| `12 x 6 x 3` | z | 0.20 | 29 / pass | 0.092 | 5 | 1.543 |
| `24 x 12 x 6` | z | 0.20 | 58 / pass | 0.055 | 3 | 2.265 |
| `12 x 6 x 3` | y | 0.45 | 25 / pass | 0.102 | 5 | 0.800 |
| `24 x 12 x 6` | y | 0.45 | 100 / pass | 0.032 | 1 | 1.971 |
| `12 x 6 x 3` | z | 0.45 | 46 / pass | 0.060 | 0 | 3.579 |
| `24 x 12 x 6` | z | 0.45 | 120 / fail | — | — | — |
| `12 x 6 x 3` | y | 0.60 | 54 / pass | 0.049 | 5 | 1.131 |
| `24 x 12 x 6` | y | 0.60 | 120 / fail | — | — | — |
| `12 x 6 x 3` | z | 0.60 | 76 / pass | 0.037 | 0 | 1.649 |
| `24 x 12 x 6` | z | 0.60 | 120 / fail | — | — | — |

| Scale | Valid uniform / planned | Oracle pass / mean ratio | Physics heuristic pass / mean ratio | Nearest neighbor pass / mean ratio | Learned pass / mean charged ratio |
|---|---:|---:|---:|---:|---:|
| Small | 6 / 6 | 6 / 6; 0.070 | 6 / 6; 1.080 | 2 / 6; 2.366 | 20 / 30; 1.644 |
| Large | 3 / 6 | 3 / 3; 0.039 | 3 / 3; 1.014 | fixed-shape index ineligible | 8 / 15; 1.767 |

On the six small cases, ten of 30 learned attempts failed quality and spent
6.26 s in charged fallbacks. On the three large cases with valid references,
seven of 15 learned attempts failed and spent 108.87 s in fallbacks. Even
before fallback, the learned mean ratio was about 1.31 at either scale. Only
ten of the 20 small-scale successful attempts and four of the eight
large-scale successful attempts were faster than their matched uniform
reference. The favorable `y, 0.45` small-scale row cannot replace the frozen
full-cohort Gate. The fixed physics heuristic passed quality but did not
produce a mean charged speedup; the small-scale nearest neighbor failed four
of six cases. All model and baseline failures remain in these denominators.

## Separate nonconvergence diagnosis

The three failed large uniform cases were rerun **only as an in-memory
diagnostic** with a new 240-iteration problem identity. This does not revise
their 120-step B2 failures, change the pilot ratio, or create a label. The
diagnostic JSON stayed outside Git (SHA-256
`e2550218e815735683aa1728f60bcbea9d49d6d4f49d7fe76e883dddbbf3ec29`).

| Large case | Change at 120 | Diagnostic outcome at 240 |
|---|---:|---|
| `z, 0.45` | 0.02275 | converged at 175, terminal change 0.00981 |
| `y, 0.60` | 0.02221 | still not converged at 240, terminal change 0.03104 |
| `z, 0.60` | 0.01145 | converged at 137, terminal change 0.00494 |

For `y, 0.60`, sampled physical-volume errors were within about `1e-8` of target and
compliance continued to decrease, but the last twenty maximum density changes
rose from 0.01793 to 0.03104. Adjacent update-vector cosines in the final
segment exceeded 0.9993. This is not evidence of a simple two-state cycle or
volume-control failure; it also does not establish eventual convergence.
Merely raising the budget to 240 would still leave a planned difficult case
unsolved. The 120-step solver, tolerance, and historical M2 outcomes remain
unchanged.

## Gate decision and next independent slice

**Gate B2 fails** its prewritten two-scale rule. The impossible oracle passed
quality and stayed below 0.50 mean ratio on every case with a valid reference,
so conditional headroom exists. But the higher scale had only three of six
valid uniform references, and all five unchanged M1 seeds together were
slower after fallback charges at both comparable scales. A larger mesh by
itself did not fix the quality or time gap. No model was trained or selected,
no held-out outcome was opened, and no ML acceleration or full v2 delivery
claim follows.

The next slice is **B2.1**, a bounded high-volume/large-mesh convergence
intervention. It must first freeze numerical acceptance cases, then test one
explicit OC or termination-policy correction against the observed `0.45`
and `0.60` failures; version any changed solver/case identity and rerun every
compared method under the same settings. If a safe correction cannot make the
intended workload quality-feasible, a new, explicitly versioned workload pilot
is required. After the uniform denominator is stable, a separate development
prototype must address B1's direction coverage and quality-basin gap before
B3 pre-registration. More epochs of the unchanged density-MSE model are not
a response to this B2 result.

## Reproduction and repository validation

Run `python scripts/b2_workload_pilot.py --m2-index <verified-index>` without
`--execute` to print the immutable plan. Execution requires the exact external
M1 training-data and checkpoint roots plus `--execute`; the script prints
per-case progress to stderr and one JSON report to stdout. Set
`PYTHONPATH=src:scripts` and each numerical thread environment variable to
one, as in the A3 benchmark. Do not direct stdout into the repository.

The runner/protocol commit passed locked sync, Ruff, mypy, all **274 tests**,
and diff checks before diagnostic execution. A synthetic test poisoned a
held-out artifact reference and verified the selector ignored it. Final
report-commit and CI validation are recorded by the PR workflow.
