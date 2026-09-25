# Development-only warm-start feasibility probe

Date: 2026-09-25

Source revision before this slice: `8601908e2afa9a538ad8c8f0a5e9da1132acce09`

Status: **Gate B0 passes for actual conditional warm-start headroom. No learned
acceleration claim follows.** The next slice must diagnose the numerical and
learned-quality gap before any new fitting. The full v1.x flagship ML delivery
gate remains open.

## Evidence boundary

The read-only `scripts/ml_feasibility_probe.py` verified the frozen M2
materialization index SHA-256
`c1374735bc80ace561f99a6e03497ad2dce3e08c1fb600a4e1d938c73383fd7f`
and manifest SHA-256
`99b63e4b49d29764b033b8d8af6664801454d6e5bcf34df68d9e6471a71ba33f`.
It opened exactly the **36 successful M2 validation label artifacts** and parsed
the case definitions of the **seven failed M2 training entries**. The 36 M2
test, 252 M2 OOD, and every pre-registered M3 final label artifact remained
unopened. The script does not create data, checkpoint, or result files; it emits
an aggregate JSON summary to standard output. A synthetic boundary test includes
invalid held-out artifact payloads and confirms that the selector ignores them.

The case cohort is the existing `(12,6,3)` M2 mesh, with the frozen SIMP
`topolab.simp.v1` solver, tolerance `0.01`, 120-iteration limit, filtered-volume
projection, and shared M1 quality audit. The validation set contains two cases
for each of nine volumes from `0.20` to `0.60` in each `y` and `z` load direction.
No training, new labels, numerical convention changes, or tolerance changes
occurred.

## Method

For every validation case, the probe runs two starts through the same public
SIMP adapter: the target-volume uniform field and the case's own verified final
design-density label. The latter is an **impossible oracle**: a deployable method
cannot know the query's answer. Both fields are independently projected with the
frozen volume projection. The solver order alternates by sorted case ID to reduce
a systematic warm-cache advantage. The same independent convergence, finite,
volume, re-solve, and `1.001 * uniform final compliance` checks apply to the
oracle result. A failed oracle attempt would pay for a fresh uniform fallback;
none failed here.

Timing is paired per case and includes each start's projection and SIMP solve.
Label-artifact reading is intentionally excluded because this is a non-deployable
oracle. Quality-audit re-solves are excluded from both method times, consistent
with the frozen baseline timing boundary. Model inference is absent, so this
ratio is **not** a model speedup, a realistic prediction bound, or an amortized
production number. It measures how quickly the existing solver can refine an
essentially exact answer. Timing was repeated twice on the same local Apple
arm64 development machine; the numerical results were identical. These local
wall times are diagnostic and have no held-out confidence interval.

For each of the seven failed `train` case definitions, the probe independently
reruns the frozen uniform solver without opening a label. It checks the terminal
120-iteration state and compares the final ten density-change and compliance
values, plus one- and two-step design-field differences.

## Observations

| Measure | First local run | Second local run |
|---|---:|---:|
| Development validation cases | 36 | 36 |
| Oracle quality/convergence failures | 0 | 0 |
| Median uniform iterations | 40.5 | 40.5 |
| Oracle iterations | 1 for every case | 1 for every case |
| Mean paired projected-start/uniform time ratio | 0.072153 | 0.072310 |
| Median paired time ratio | 0.067657 | 0.067723 |
| Largest oracle/uniform final-compliance ratio | 0.9999962 | 0.9999962 |

All 18 `(direction, volume)` validation strata had zero oracle failures and a
mean local time ratio below `0.14` in both runs. This demonstrates an actual
one-iteration fixed-point neighborhood and a large *conditional* reduction in
solver work. It does not show that any CNN can predict that neighborhood, that
the ratio survives inference or other per-query costs, or that new final cases
will behave similarly. The M1 evaluation found 107 learned quality failures and
mean charged ratios above `1.0`; that gap remains the main ML problem.

All seven failed training cases reproduced non-convergence at iteration 120,
with terminal density changes from `0.0149457` to `0.0150505`, above the frozen
`0.01` limit. For all seven, each of the final ten recorded density changes and
compliances decreased. Their latest two-step design differences were nonzero;
the largest was about `0.03094`. The observed tails are more consistent with
slow terminal progress than a simple alternating two-state cycle, but the
underlying cause and an appropriate solver correction remain unproven. No case
was relabeled or counted as converged.

## Decision and next slice

Gate B0 passes because exact-label starts demonstrably cut solver work while
meeting the frozen quality contract on all development validation cases. This
supports further *targeted* ML work rather than extra MSE epochs as a default.
The old `topolab.m3.experiment.v1` pre-registration is superseded before fitting
or final evidence. The active
`docs/planning/TopoLab_post_v1_development_roadmap.en.md` requires positive
learned end-to-end acceleration for full flagship delivery, with a fresh
versioned experiment and sealed final cohort.

The next independent slice is **B1**: reproduce and diagnose the `0.45`
convergence traces and replay exposed M1 predictions on development cases to
locate the quality gap. It must leave numerical semantics unchanged unless a
separate tested and versioned fix is justified. Start it only on a new user
instruction.

## Repository validation

Before commit: `uv sync --dev --locked`, `uv run ruff check .`, `uv run mypy src`,
`MYPYPATH=src uv run mypy scripts/ml_feasibility_probe.py`, `uv run pytest`
(267 passed), `git diff --check`, and `git diff --cached --check` passed. The
synthetic held-out boundary tests were included in the full test run. No
generated dataset, label, checkpoint, or diagnostic output was committed.
