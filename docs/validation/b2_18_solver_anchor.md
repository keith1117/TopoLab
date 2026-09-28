# B2.18 solver-anchored start

Date: 2026-09-28 (America/New_York)

Status: **The frozen four-case solver-anchor sentinel failed.** The new
initialization made a small numerical improvement on all four exposed
cases, but all three previously failing starts still violated the
unchanged terminal compliance bound and paid full uniform fallback.
The four predeclared fresh cases were not opened. Uniform initialization
remains the operational default; B3 and final evidence remain closed.

## Frozen intervention and evidence boundary

The [B2.18 protocol](../planning/b2_18_solver_anchor_protocol.md) fixed
one solver-aware repair before any new outcome: project the audited
context-17 prediction; separately run two uniform FEM/sensitivity/OC
updates; blend their **design** densities 50/50; reproject to the
existing volume target; then run an otherwise unchanged 360-update
physical-plateau solve. The two uniform updates, two projections,
inference, refinement, quality decision, and any fallback were charged.
Unlike B2.8's midpoint with the constant initial field, the anchor
was an evolved physical state. No checkpoint, learned threshold, mesh,
solver equation, or quality tolerance changed.

The canonical plan SHA-256 was
`df4959622747da50937903480d4de06f94e8d23df409049ff145ca865270f21b`;
the saved protocol SHA-256 was
`7d8aeb7b9d7e3de6032d6f1904307981000f038e847d43562edc87de50bae9a6`.
The clean execution revision was `f650ec91302cccbe0b25782fafca43064fda9f15`.
The read-only plan selected four historically exposed high-volume
large-y cases and reserved four physically disjoint new cases at
volumes `0.5675,0.5725`, separate from the 636-case development
ledger and the 24 unexecuted B2.17 reservations. B2.14/B2.15
reference and screen artifacts matched their frozen hashes; fixed
checkpoint bytes and selection histories were verified. No M2
test/OOD, final, or new B2.18 case was opened.

## Complete sentinel and Gate

Each row paid for a **new** uniform timing denominator and a separate
anchored candidate. The terminal ratio is candidate compliance divided
by matched uniform compliance; acceptance requires `<=1.001` plus all
other frozen checks. A failed candidate retained its failure code and
paid a complete fresh uniform fallback.

| Historical context-17 status | Anchored updates | Terminal compliance ratio | Pre-refinement, s | Fully charged time ratio | Anchored status |
|---|---:|---:|---:|---:|---|
| Success | 58 | 1.000931 | 0.836 | 0.597 | Accepted |
| Failure | 64 | 1.004839 | 0.826 | 1.524 | Failed, fallback |
| Failure | 118 | 1.006792 | 0.896 | 2.063 | Failed, fallback |
| Failure | 129 | 1.005722 | 0.820 | 2.116 | Failed, fallback |

Relative to the unchanged context-17 reruns in B2.17, the anchor
reduced terminal compliance ratios from `1.000941,1.004903,1.007165,
1.006413` to `1.000931,1.004839,1.006792,1.005722` and shortened
candidate refinement by 5–30 updates. These are real but insufficient
changes: the three failures remain well above `1.001`. The frozen
sentinel required all four candidates to pass terminal quality and a
fully charged mean `<=1.0`; it instead had **3 failures** and mean
**1.574960**. All four pre-refinement costs were below the strict
`2.8101 s` limit. Execution used `217.2313 s` against a `600 s`
cap and peaked at `396,460,032 bytes` against 2 GiB.

The complete sentinel-index SHA-256 was
`737c09ac00c07331196d0dc396b178e20ae273d415d3895b67f8d1fef9a143f4`.
An independent standard-library audit checked the clean revision,
frozen plan and B2.14/B2.15 screen hashes, four case IDs and prior
statuses, two-update and 50/50 metadata, every phase sum and paired
ratio, candidate and operational quality, fallback charges, resource
caps, and the Gate. It reproduced three quality failures, zero cost
overruns, and the failed mean. It confirmed that no B2.18 fresh
reference or screen index exists. Generated artifacts and audit work
remain outside Git.

## Decision and next slice

The physics-evolved anchor modestly improves the solutions, but it
does not change the terminal solution basin enough to satisfy the
existing 0.1% compliance allowance. Cost was not the blocker.
The protocol therefore stops this exact two-update/50-50 mechanism
without changing its weight, update count, model, or cases. The next
independent slice is **B2.19: a bounded learning-side quality-basin
repair**, starting from the observed terminal compliance gap. It
should freeze a materially different model input or training target,
full query-time physics cost if any, a fixed fit/screen budget, and
fresh development evidence. Passing B2.19 alone would still require
separate confirmation before B3.

## Repository validation

Before clean-revision execution, `uv sync --dev --locked`, Ruff,
mypy on `src`, all **339 Python tests**, and `git diff --check`
passed. The required checks are repeated before committing this
report.
