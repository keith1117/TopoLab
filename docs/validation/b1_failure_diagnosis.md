# B1 numerical convergence and learned-quality diagnosis

Date: 2026-09-25

Source revision before this slice: `8eb64654b739318a68d26a4033ee3d81ac28982f`

Status: **Gate B1 passes as a reproducible diagnosis with an explicit unchanged-solver
decision.** No learned-acceleration or v2 delivery claim follows. The next slice is
A3 baseline-affecting solver performance, followed by B2's workload pilot.

## Evidence and access boundary

The read-only `scripts/b1_failure_diagnosis.py` verifies the frozen M2 index SHA-256
`c1374735bc80ace561f99a6e03497ad2dce3e08c1fb600a4e1d938c73383fd7f`
and manifest SHA-256
`99b63e4b49d29764b033b8d8af6664801454d6e5bcf34df68d9e6471a71ba33f`.
It opens only the 36 M2 **validation** label artifacts. It reads the case definitions
and sanitized failure status of all ten failed entries: seven train, one ID test,
and two OOD. It never opens any M2 test/OOD label artifact. The five M1 selections
and Safetensors checkpoints are the exact content-addressed production artifacts
listed in `docs/validation/m1_training.md`. A synthetic boundary test poisons
held-out artifact references and verifies that the selector ignores them.

The script prints JSON to standard output. Diagnostic output was kept outside Git;
no generated label, model, dataset, or result artifact was committed. The original
M1/M2 experiment outcomes and case identities remain unchanged.

Two consecutive full replays produced identical JSON bytes (SHA-256
`cbdc4e651ddaa95b45f87f46ea98aa43f2385c4638e43f09832be12b3e885a6e`).
The timed replay on the local Apple arm64 machine took **137.22 seconds wall**,
125.98 seconds user CPU, and 8.78 seconds system CPU, with peak resident memory
280,854,528 bytes (267.84 MiB). No data generation or model fitting occurred.

## Frozen-budget failure mechanism

All ten failed case definitions were rerun through the unchanged public SIMP solver
with an **in-memory diagnostic maximum of 240 iterations**. This is not a new M2
catalog or a successful label-generation run. Iterations 1–120 use the same
settings as the frozen M2 cases. The recorded state at iteration 120 reproduced all
ten terminal density changes from the M2 validation report; every value remained
above the frozen `0.01` tolerance.

| Diagnostic observation | Result |
|---|---:|
| Failed M2 outcomes reproduced at iteration 120 | 10/10 |
| Last ten density-change and compliance values strictly decreasing | 10/10 each |
| Smallest cosine between the last two update vectors at iteration 120 | `0.960059` |
| Largest independently recomputed physical-volume error | `8.865e-9` |
| Largest disagreement with recorded volume | `0` |
| Largest independent compliance re-solve relative error at iteration 120 | `0` |
| Diagnostic runs converged by iteration 240 | 10/10 |

The eight `y`-direction cases, including the seven failed training cases, first met
the unchanged `0.01` criterion at iterations 127–128. The two `x`-direction OOD
cases met it at iteration 195. Their initial 120-step failure is therefore an
insufficient **frozen iteration budget for these cases**, with slow terminal
progress rather than a simple two-state cycle or an observed loss of volume
control. The last-step update cosines and monotonically decreasing tails support
that local interpretation; they do not prove global optimizer stability or that
240 iterations would suffice for a new cohort.

**Solver decision:** Do not change `topolab.simp.v1`, the `0.01` tolerance, or the
historical M2 outcomes in B1. Merely raising M2's original budget after its data
gate would invalidate its case/catalog identity. A future contract may choose a
different budget only with a new version and labels, numerical acceptance tests,
and every compared method rerun under the same solver revision. The workload and
optimized uniform reference must be settled first.

## Fixed M1 model replay on development validation cases

Every one of the five fixed M1 models was replayed on each of the 36 M2 validation
cases: 180 attempts, split evenly between `y` and `z` load directions. The M1 model
was trained on `y` cases. For every query, the diagnostic compared raw and
filtered-volume-projected predictions with that case's verified final design label;
computed physical volume and initial compliance; ran the unchanged SIMP refinement;
and applied the shared convergence, independent compliance, volume, and
`1.001 * uniform final compliance` checks. Uniform and impossible own-label oracle
starts were rerun for the same cases. No checkpoint was selected or altered from
these observations. These are diagnostic candidate outcomes, with no fallback or
paired wall-time claim.

| Measure | All | `y` | `z` |
|---|---:|---:|---:|
| Learned attempts | 180 | 90 | 90 |
| Quality failures | 46 | 17 | 29 |
| Non-converged attempts | 22 | 3 | 19 |
| Median raw design-density MSE | `0.14339` | `0.10604` | `0.26668` |
| Median projected design-density MSE | `0.14146` | `0.10529` | `0.26299` |
| Median projected initial/uniform initial compliance | `0.6091` | `0.4442` | `1.2111` |
| Median projected initial/oracle initial compliance | `3.5900` | `2.1777` | `5.3863` |
| Median compliance after first refinement/uniform final | `2.1742` | `1.6145` | `2.5737` |
| Median compliance after tenth refinement/uniform final | `1.1188` | `1.0329` | `1.3396` |
| Median learned iterations | 47.5 | 39 | 77.5 |
| Median uniform iterations | 40.5 | 40.5 | 39.5 |
| Median own-label oracle iterations | 1 | 1 | 1 |

Projection reduced design-density MSE in **179/180** attempts and held the maximum
projected physical-volume error below `9.63e-7`. It did not solve the quality gap:
24 attempts converged but failed the final quality check; 40 finished above the
compliance limit, with some overlap with non-convergence. Thirty failed attempts
began with *lower* compliant physical initial states than the uniform start, and 13
failed despite taking fewer iterations than uniform. Only 61/180 attempts both
passed quality and used fewer iterations. These are iteration counts, not proof of
end-to-end speedup.

Quality failures also varied by volume: the `0.40`, `0.45`, and `0.60` strata
each had ten failures in 20 attempts, while `0.20` had none. Every `0.60`
attempt converged, so the quality gap is not explained solely by iteration budget.

The unseen `z` direction had about 2.5 times the `y` median projected MSE,
29 versus 17 quality failures, and a median initial compliance worse than
uniform. This is consistent with a direction-coverage/generalization bottleneck.
The 17 failures on familiar `y` cases, including failures after an initially lower
compliance or fewer iterations, show that adding `z` examples alone cannot be
assumed sufficient. The squared-error training target and initial compliance are
imperfect proxies for reaching the correct final quality basin. The diagnostic
cannot causally isolate data volume, architecture, representation, and objective
without a new bounded ablation; it identifies direction coverage and
quality-aligned warm-start behavior as the next measured hypotheses.

## Gate decision, limits, and next slice

Gate B1 passes its *diagnostic* requirement: the observed M2 failures are
reproducible finite-budget slow convergence, and the learned-quality gap is
measured against the label-informed fixed-point neighborhood. No numerical bug
was demonstrated, so the solver and all old labels stay unchanged. The next
model intervention must directly test the measured direction and quality-basin
issues; more epochs of the same final-density MSE fit are not a remedy by itself.

These are development-exposed cases and local diagnostic computations. They are
not fresh final evidence, a new training run, an optimized-uniform benchmark, or a
learned-acceleration claim. **A3 is next:** profile and freeze baseline-affecting
solver performance with numerical equivalence before B2 chooses a repeated-query
workload and two mesh scales. B3 will then pre-register any new label budget,
model intervention, and sealed final cohort.

## Repository validation

Before commit, `uv sync --dev --locked`, `uv run ruff check .`, `uv run mypy src`,
`MYPYPATH=src uv run mypy scripts/b1_failure_diagnosis.py`, and `uv run pytest`
(**269 passed**) succeeded. The synthetic held-out artifact-boundary tests were
included. `git diff --check` and `git diff --cached --check` passed. No tolerance
was loosened and no numerical behavior was changed.
