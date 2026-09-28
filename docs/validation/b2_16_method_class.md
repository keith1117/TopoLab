# B2.16 method-class and speed-headroom reassessment

Date: 2026-09-27 (America/New_York)

Status: **The frozen B2.16 decision permits one bounded online reliability
probe and stops local coarse-metadata routing searches.** This read-only
development analysis opened no new solver, learned, M2 test/OOD, or final
outcome. It does not pass a new development acceleration Gate, open B3, or
change uniform initialization as the operational default.

## Frozen evidence boundary

The [B2.16 protocol](../planning/b2_16_method_class_protocol.md) fixed the
two exposed 24-case cohorts, four common actions, cell mapping, optimistic
bounds, common retrospective feasibility thresholds, resource caps, and
ordered decision rule before derived assessment. Its canonical plan
SHA-256 was
`fa1370508e5a94650b80e6f1b3170699072625abc39b88287d498104e04f1c03`;
the saved plan-file SHA-256 was
`38a26da75f5d54261fb63b6a53cbb21907775fb13c5bde0ed88dbd329aeabc09`.
The clean analysis revision was `910534b6ebf95d978122dfdc4b62906f8768a744`.

The B2.14/B2.15 reference and screen indices matched all four frozen
SHA-256 values. The runner audited 24 references, 24 unique matched
scale/direction/volume-tier/position cells, and 192 ordered fully charged
outcomes per cohort. It checked the source and reference linkage, uniform
denominators, phase sums, paired ratios, failure/fallback status, and
operational `1.001` compliance and `0.005` volume bounds. The common
actions were fresh uniform, vector 29, context 17, and context 43;
B2.14-only context 29 was excluded from transfer. All 48 cases remained
in the analysis. The assessment used **0.0044 s** and **23,085,056 bytes**
peak RSS, below its 60 s and 1 GiB caps. Its artifact SHA-256 was
`977b57a1567767f151bfa51e2217a76b4e6617637d8219fb6e634252e6c23cf1`.
Generated plans, indices, summaries, and independent audit code remain
outside Git.

## Optimistic fixed-checkpoint headroom

The impossible perfect selector chose each case's fastest successful
fully charged common action after seeing its outcome. It had zero failed
attempts and passed the common retrospective scale/direction thresholds
on **both** cohorts:

| Bound | Overall | Small | Large | Small y | Small z | Large y | Large z | Failures |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| B2.14 perfect selector | 0.644 | 0.555 | 0.733 | 0.576 | 0.534 | 0.769 | 0.697 | 0 |
| B2.15 perfect selector | 0.565 | 0.413 | 0.716 | 0.447 | 0.379 | 0.888 | 0.545 | 0 |

Thus the fixed checkpoints retain *optimistic* per-case speed headroom.
This selector is undeployable: it knows which model will succeed and be
fastest before paying for a decision. Its passing values are bounds,
not B2.14/B2.15 Gate passes or acceleration evidence.

## Transfer of a coarse metadata choice

For each one-case cell, choose the fastest successful action on one cohort
and apply it to the matching scale/direction/volume-tier/z-position cell
in the other cohort. This already grants a free outcome-informed training
choice and zero lookup cost. Yet **15 of 24** cell choices disagreed across
the two cohorts, and both transfer directions failed the common
retrospective Gate:

| Transfer | Overall | Small | Large | Large y | Large z | Failed attempts | Gate |
|---|---:|---:|---:|---:|---:|---:|---|
| B2.14 choices on B2.15 | 0.764 | 0.532 | **0.995** | **1.001907** | 0.988 | 2 | Fail |
| B2.15 choices on B2.14 | 0.813 | 0.711 | **0.914** | 0.871 | 0.957 | 1 | Fail |

The large-scale limit was `<=0.90`; the large-y limit was `<=1.0`.
The B2.14-to-B2.15 result missed both. The reverse result missed the
large-scale limit. Their failures persist even with free per-cell
selection and zero lookup cost. This does not prove that *all* metadata
policies are impossible, but it provides no basis to continue local
position/volume threshold searches on these exposed cohorts.

## Ideal rejection and attainable diagnostic budget

The B2.15 new route had one failed learned attempt at high-volume large-y,
upper-z position. Replace only that failed attempt with an impossible
zero-cost immediate fresh-uniform rejection at ratio `1.0`, leaving every
other measured route outcome unchanged. The resulting *ideal* route
would have overall mean **0.641463**, small/large means **0.535/0.748**,
and large-y mean **0.927137**. Its overall mean would be below the frozen
strict `0.95 × 0.686491 = 0.652167` old-route threshold; therefore the
ideal rejection passes B2.15's arithmetic development limits.

Assume an additional diagnostic runs at **both** high-volume large-y
positions and costs the same number of seconds per case. The tightest
frozen constraint is the 5%-over-old-route requirement. It permits
**strictly less than 2.8101 additional seconds per at-risk query** after
the impossible failed-attempt replacement; large-y and large-scale
constraints allow 4.7823 s and 20.0114 s, respectively. The measured
uniform refinement cost per update was **0.173–0.187 s** on those two cases.
The observed one-update cost is below the optimistic budget, satisfying
the protocol's minimal cost-floor decision. The analysis does **not**
show that one update can distinguish a safe learned start, nor that an
actual diagnostic will fit within 2.8101 s. A false rejection on a safe
case or a missed quality failure would consume the margin.

## Decision and next slice

An independent standard-library implementation re-read both hashed
cohorts, recomputed each selected action, all paired ratios and cell
means, the 15 action disagreements, the ideal rejection, and the
2.8101 s pilot budget. It reproduced the frozen decision
`bounded_online_reliability_probe_warranted`; its audit code SHA-256 was
`9165ac7d693045381bbaa09ab7b64f1f1dbbcdc06c3e339b709e5632b289fec9`.

The next independent slice is **B2.17, one bounded query-time early
reliability probe** on the high-volume large-y failure mode. First freeze
the observable early signal, maximum added cost, false-rejection and
missed-failure rules, cases, and stopping conditions. A diagnostic on
exposed cases may establish mechanism but cannot establish transfer;
any feasibility claim requires a new physically disjoint development
screen and then separate larger confirmation. If no observable signal
fits the charged budget, stop this fixed-checkpoint family and reassess
a genuinely different mechanism. B3 remains closed.

## Repository validation

Before clean-revision execution, `uv sync --dev --locked`, Ruff, mypy on
`src`, all **333 Python tests**, and `git diff --check` passed. The
required checks are repeated before committing this report.
