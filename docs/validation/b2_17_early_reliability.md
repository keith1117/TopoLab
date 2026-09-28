# B2.17 online early-reliability probe

Date: 2026-09-28 (America/New_York)

Status: **The frozen four-case mechanism sentinel failed; the 24-case fresh
development cohort was not opened.** The two-update signal stayed within its
strict per-query cost budget but missed all three known terminal quality
failures. B3 remains closed; uniform initialization remains the operational
default; no ML acceleration claim follows.

## Frozen boundary and execution

The [B2.17 protocol](../planning/b2_17_early_reliability_protocol.md) fixed
one signal, threshold, action, full query charge, four exposed sentinel
cases, 24 physically fresh cases, and an ordered stopping rule before any
online result. Its canonical plan SHA-256 was
`51c3ffd501435802298256acac05af28b95542408208989d68ea36df698d3d7e`;
the plan-file SHA-256 was
`a2e18b46349b846a2cdb36e246fcb000e0352f19f56f1c4011b60c9aa73b8ed8`.
The clean execution revision was `9304abef8fe78f15f94e5e55ee50f29cc5902046`.
The read-only plan enumerated 24 new case IDs disjoint from 636 previously
exposed development case IDs, but no new case was executed. The B2.14 and
B2.15 source indices matched their frozen hashes; selected context-17
checkpoint bytes and validation selection were verified before use. M2
test/OOD and all final evidence remained sealed.

At each exposed high-volume large-y query, the probe paid for a new
two-update uniform shadow and observed context-17's second update in a
continuous learned solve. It rejected only if learned early compliance /
uniform early compliance exceeded `1.001`; otherwise it continued to the
unchanged independent terminal quality check. A failed accepted attempt
paid a fresh full uniform fallback. The cost cap was strictly below
`2.8101 s` before the decision on **every** case.

## Four complete sentinel results

The historical fixed context-17 outcomes supplied one known success and
three known failures; they were never inputs to the online decision.
All four online trajectories reproduced those final quality labels.

| Historical terminal result | Second-update ratio | Decision cost, s | Online decision | Final compliance / uniform | Charged time / uniform |
|---|---:|---:|---|---:|---:|
| Success, B2.14 | 0.800809 | 1.3777 | Accept | 1.000941 | 0.630 |
| Failure, B2.15 | 0.793118 | 1.3542 | Accept, full fallback | 1.004903 | 1.654 |
| Failure, B2.14 | 0.810256 | 1.3354 | Accept, full fallback | 1.007165 | 2.158 |
| Failure, B2.15 | 0.784067 | 1.3920 | Accept, full fallback | 1.006413 | 2.247 |

Every early ratio was **below 1.001**, including the three failures.
The successful case's ratio (`0.800809`) lies between the failed ratios,
so a single monotone cutoff on this same two-update scalar cannot separate
all four cases in either direction. This is a mechanism diagnosis on an
exposed four-case set, not a statistical proof that all early signals fail.

The frozen sentinel required zero false rejections and zero missed failures.
It had **0 false rejections, 3 missed failures**, and 0 over-budget
decisions, so it failed. Execution took `228.9135 s` against a `600 s`
cap and peaked at `361,529,344 bytes` against 2 GiB. The complete
sentinel-index SHA-256 is
`c811bfcfa41807eefa5d9a14fcaba1d191c4324bbf596c231ff698a7fda7d2ee`.
An independent standard-library audit checked the source revision and
exposed screen hashes, four case IDs and historical statuses, signal
arithmetic, timing-phase sums, paired charges, fallback flags, terminal
quality and resource caps. It reproduced the failed Gate and verified that
no B2.17 fresh reference or screen index exists. Generated records and
logs remain outside Git.

## Decision and next slice

The failure is **signal discrimination**, not query-time computation cost:
all predecision costs were 1.34–1.39 s, while all three terminal failures
were missed and paid full fallback. Under the protocol's stop rule, B2.17
ends here. Its untouched 24-case cohort cannot be counted as confirmation
or a positive development result. Do not retune a cutoff or position/volume
rule on the exposed B2.14/B2.15 cases. The next independent slice is
**B2.18: a bounded new-mechanism assessment** that chooses and freezes a
different quality-predictive or solver-aware intervention with explicit
compute and stopping limits before new evidence. It must not reopen B3
without fresh development feasibility and separate confirmation.

## Repository validation

Before clean-revision execution, `uv sync --dev --locked`, Ruff, mypy on
`src`, all **336 Python tests**, and `git diff --check` passed. The same
required checks are repeated before committing this report.
