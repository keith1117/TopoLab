# TopoLab agent instructions

## Read before changing code

Read these files in order:

1. `PROVENANCE.md`
2. `docs/numerical_conventions.md`
3. `docs/reference_baseline.md`
4. `docs/planning/TopoLab_reimplementation_strategy.md`
5. `docs/planning/TopoLab_development_timeline_and_resources.md`
6. `docs/planning/TopoLab_v2_development_roadmap.md`
7. The contracts and latest validation reports relevant to the requested slice.

## Current project state

The historical `v1.0.0` release and Gates N1, N2, P1, M0, and A1 are complete.
M1 did not establish learned acceleration; M2 failed its data gate; the bounded
M3 v1 pre-registration was superseded before fitting or final evaluation. The
active v2 roadmap requires reproducible, same-quality ML end-to-end acceleration
on a predefined workload before the full flagship project is delivered. Until
that evidence exists, uniform initialization is the operational default and no
accelerated claim is allowed.

Track B has development-only warm-start feasibility evidence in
`docs/validation/ml_feasibility_probe.md`, B1 failure diagnosis in
`docs/validation/b1_failure_diagnosis.md`, and A3 solver-ordering evidence in
`docs/validation/a3_solver_ordering.md`. The fixed B2 workload pilot is recorded
in `docs/validation/b2_workload_pilot.md`: Gate B2 failed because three of six
larger uniform references did not converge at the frozen limit and the five
unchanged M1 starts were slower after fallback charges. B2.1's opt-in,
versioned physical-plateau policy made all twelve uniform references
quality-feasible; its matched five-seed M1 panel remains slower after fallback
charges. See `docs/validation/b2_1_convergence.md`. B2.2 froze a bounded
quality-aligned development-prototype plan, but only 53/61 uniform data
sentinels converged at 120 updates. B2.3 preserved all 61 source cases,
versioned their iteration cap to 240, and passed 61/61 independent quality
checks without changing the previous 53 accepted outcomes. See
`docs/validation/b2_2_data_feasibility.md` and
`docs/validation/b2_3_data_feasibility.md`. B2.4 passed the complete 522/522
development-label and resource Gate; see
`docs/validation/b2_4_development_labels.md`. B2.5 completed six fixed fits
and all 54 development validation cases, but every learned seed was slower
than matched uniform on both mesh scales after complete fallback charges; see
`docs/validation/b2_5_prototype.md`. B2.6 then captured all 480 fixed
intermediate-trajectory targets, completed three fits and all 12 new-case
screen outcomes, but its development feasibility Gate failed: all three new
seeds were slower than matched uniform at both mesh scales after complete
fallback charges. See `docs/validation/b2_6_trajectory.md`. B2.7 changed only
the point-load representation, reused all
480 B2.6 targets, completed three fits and a fresh 12-case, 132-outcome
screen. It improved seeds 17/29 substantially against B2.6, but its Gate
failed: no new seed met the required two-scale and direction-wise charged
speed limits. See `docs/validation/b2_7_global_load.md`. B2.8 tested an
opt-in y-direction midpoint between each fixed B2.7 prediction and uniform
start on 12 new cases. All 132 outcomes were audited, but its Gate failed:
no seed met the two-scale/direction bounds, the three seeds retained the
same 2/3/4 failure counts as the controls, and the unchanged z predictions
were slow on this fresh load-position/volume cohort. See
`docs/validation/b2_8_basin.md`. B2.9's vector point-load conditioning
completed three fits and all 132 new-case outcomes. Seeds 29 and 43 had
zero fallbacks and met both scale-mean charged-speed bounds, but their
large-y direction means exceeded 1.0, so the frozen Gate failed. See
`docs/validation/b2_9_vector_load.md`. B2.10 completed all 480
sensitivity-weight artifacts and three fits, but its frozen screen stopped
after 9/12 cases and 99/132 outcomes: the tenth case's mandatory uniform
reference did not converge at 240 updates. The failed Gate and partial
learning-side evidence are retained in
`docs/validation/b2_10_weighted_trajectory.md`. B2.11's versioned 360-update
budget passed its twelve-pair old/new sentinel and all twelve fresh uniform
references, then retained all 132 fixed-model outcomes. Neither B2.9 nor
B2.10's three-seed panel met the two-scale/direction-wise charged-speed
Gate; see `docs/validation/b2_11_reference_budget.md`. B2.12's fixed
spatial-context CNN passed 12/12 new uniform references and
completed three fits plus all 132 new-case outcomes. Its validation MSE and
small-z refinement improved, but every new seed exceeded the large-scale
charged-speed bound; the high-volume y quality gap and large-z refinement
regression persisted. See `docs/validation/b2_12_context_cnn.md`. The next
independent slice, B2.13, froze a workload-aware routing/safe-rejection
policy. Its 12 fresh uniform references and all 144 screen outcomes passed
the bounded development Gate, but the routed policy did not beat the best
fixed context model on this cohort. See `docs/validation/b2_13_routing.md`.
B2.14 then froze and completed a larger, physically disjoint 24-case
development confirmation: 24/24 new uniform references and all 192
outcomes passed completeness and quality audits, but no routed or fixed
single-model policy met the predeclared two-scale/direction-wise Gate.
See `docs/validation/b2_14_development_confirmation.md`. B2.15's fixed
position-aware route passed 24/24 fresh uniform references and retained all
192 outcomes, but failed its development Gate: the large-y charged mean
exceeded 1.0 and the overall gain over the old route was below the frozen
5% requirement. See `docs/validation/b2_15_position_routing.md`. B2.16's
read-only audit of the 48 exposed B2.14/B2.15 cases found optimistic
fixed-checkpoint headroom but failed coarse-cell transfer in both
directions. Its ordered decision permits one bounded online early-reliability
probe while stopping further exposed-cohort routing-threshold searches;
see `docs/validation/b2_16_method_class.md`. B2.17's frozen two-update
online signal stayed within its cost cap but missed all three known
terminal failures on the four-case exposed sentinel; its stop rule kept
all 24 new cases sealed. See `docs/validation/b2_17_early_reliability.md`.
The B2.18 solver-anchored start modestly improved compliance and update
counts, but all three historically failing cases still missed terminal
quality and paid fallback; its frozen stop rule kept four new cases sealed.
See `docs/validation/b2_18_solver_anchor.md`. B2.19's paid uniform-state
sensitivity input passed twelve new uniform references and three fits,
but its complete 84-outcome screen failed the learned Gate despite lower
validation MSE for all three seeds. See
`docs/validation/b2_19_physics_input.md`. B2.20's operational checkpoint
selection completed 12 selection cases and 24 independent screen cases,
with all 132/168 outcomes audited; no selected seed passed, and 0/6
high-volume large-y selected attempts passed terminal quality. See
`docs/validation/b2_20_operational_selection.md`. The next independent
slice was B2.21: its terminal-design learning target passed 24/24 fresh
uniform references, 12/12 validation targets, three fits, and all 168
screen outcomes, but no new seed met the full Gate and 0/6 high-volume
large-y new attempts passed terminal quality. See
`docs/validation/b2_21_terminal_target.md`. B2.22's high-volume y-direction
specialist completed 24/24 new references, three fits, and all 168
fully charged screen outcomes. Its matched high-volume large-y quality
improved from 2/6 fixed-control successes to 3/6, below the frozen
4/6 minimum; no seed met the two-scale and direction-wise speed Gate.
See `docs/validation/b2_22_y_specialist.md`. B2.23's bounded large-y
load-position expansion passed its data Gate: 30/30 independently audited
new uniform labels, with 20 train and 10 validation labels, within the
frozen time and memory caps. It made no model fit or acceleration claim;
see `docs/validation/b2_23_position_labels.md`. B2.24 completed 24/24
fresh references, three fits, ten independent diagnostic validation
labels, and all 168 fully charged screen outcomes. The expanded route
improved matched high-volume large-y terminal quality from 0/6 to 6/6,
but no new seed met the two-scale and direction-wise speed Gate; see
`docs/validation/b2_24_expanded_training.md`. B2.25's read-only cost
audit found all ten expanded-model failures in y, while large-z
refinement remained costly; see `docs/validation/b2_25_residual_cost.md`.
B2.26 then completed 24/24 references, three weighted terminal fits,
and 240 fully charged outcomes, but no seed met the large-scale speed
Gate; see `docs/validation/b2_26_weighted_generalist.md`. B2.27's
middle-volume large-grid y/z position expansion passed its data Gate:
60/60 independently audited uniform labels, with 40 train and 20
validation labels, within frozen time and memory caps. It performed no
model fit or learned comparison; see
`docs/validation/b2_27_middle_volume_labels.md`. The next independent
slice was B2.28: its fixed forty-label generalist expansion completed
24/24 fresh references, three fits, twenty diagnostic labels, and all
168 charged outcomes. All three seeds passed the bounded development
Gate with zero new-panel failures and 6/6 middle-volume large-y
successes; see `docs/validation/b2_28_expanded_generalist.md`. B2.29's
larger independent confirmation completed 48/48 new references and all
432 fully charged outcomes with unchanged checkpoints and route. Seeds
17 and 43 passed the frozen Gate; seed 29 failed the small-scale and
small-z speed bounds. The expanded panel passed 9/9 middle-volume and
9/9 high-volume large-y attempts; see
`docs/validation/b2_29_development_confirmation.md`. The next independent
slice was B3.1: its new `topolab.b3.experiment.v1` contract freezes 752
case definitions, 1,376 historical exposure fingerprints, twelve fits,
prospective validation-only primary selection, finite compute limits,
and final ID/OOD plus independent replication criteria; see
`docs/b3_experiment_contract.md` and
`docs/validation/b3_1_contract_boundary.md`. Its metadata-only planning
audit passed without a solver call, fitting, or label access. B3.2 then
implemented the exact catalog/ledger and membership-specific access
guards, matching both frozen hashes and rejecting forbidden roles,
changed-budget origins, and incomplete NN populations before byte reads;
see `docs/validation/b3_2_catalog_boundary.md`. B3.3 then implemented
versioned label/reference contracts, external content-addressed artifacts,
charged single-writer recovery, independent numerical audits, and a
read-only planning/explicit execution CLI; see
`docs/validation/b3_3_data_materializer.md`. Its tests used synthetic
states, and no production B3 case was optimized in that slice. B3.4 then
executed all 560 labels and 48 screening references from clean merged
revision `cc151b014f9034ccc7093ef592021003d7dec252`. All 608 outcomes passed
complete independent quality, provenance, stratum and resource audits with
zero failures. The total charged data phase was 5,325.353116 seconds and
peak RSS was 500,154,368 bytes; see `docs/validation/b3_4_data_gate.md`.
Gate B3 passed without a model fit or final artifact access. A2.1 then
introduced a versioned JSON-line manager/worker protocol and local separate
process for default numerical runs; see
`docs/validation/a2_1_worker_protocol.md`. A2.2 then added leased SQLite
ownership, heartbeat, fenced writes, queued-record recovery and versioned
schema migrations; see `docs/validation/a2_2_run_ownership.md`. B4.1 then
completed all twelve fixed CPU fits and their independent artifact/selection
audit, retaining all 1,902 attempted epochs and 24 artifacts within the
7,200-second and 4-GiB caps; see `docs/validation/b4_1_fixed_fitting.md`.
B4.2 then completed all 48 screening cases and 720 fully charged outcomes.
Its independent numerical/artifact/selection audit passed after repairing a
supplemental audit's forbidden single-label NN read; the rejected attempt,
cost and permanent ledger marker remain retained. No P seed passed the
frozen direction/reliability Gate, so no primary or freeze was produced;
see `docs/validation/b4_2_development_screen.md`. B4.3 then completed the
read-only diagnosis of all 720 outcomes and 162 identical-model pairs.
It found substantial timing dispersion, two converged generalist quality
gaps and one 360-update generalist convergence failure, without changing
any prior result; see `docs/validation/b4_3_failure_cost.md`. B4.4 then
passed its frozen engineering sentinel: all 76 queries and 100 terminal states
were independently audited with unchanged numerical outcomes and failures.
Bounded progress and full query timing reduced callback wall by 99.8243%
and query wall by 25.3881% in the checkpoint-stress sentinel, within its
7,200-second / 2-GiB caps; see `docs/validation/b4_4_engineering.md`.
This establishes no learned acceleration. B4.5 then completed three fixed
sensitivity-weighted terminal-design fits (466 attempted epochs), 48 fresh
uniform references and all 576 fully charged outcomes. Independent audits
passed all 644 terminal states and resource closure. W/17 and W/43 passed the
bounded development Gate with zero failures/fallbacks; W/29 failed reliability.
W/17 is the development primary. Final charge was 7,578.184891 seconds and peak
RSS 453,132,288 bytes; see `docs/validation/b4_5_weighted_terminal.md`.
B4.6 then completed 96/96 new uniform references, all 1,152 outcomes,
1,250 audit units and 1,291 independent terminal/classification checks. Its
larger confirmation Gate failed: fixed W/17 had two failures/fallbacks,
W/29 had four and only W/43 passed single-seed criteria with one fallback.
Both pooled large-y cells passed 18/18, but no W primary was eligible.
Final charge was 12,528.446019750 seconds with peak RSS 1,492,172,800 bytes;
see `docs/validation/b4_6_development_confirmation.md`. B4.7 then completed
48/48 fresh references, all 576 fully charged outcomes, 626 production audit
units and 646 independent terminal/classification checks. Its bounded
spatial-objective rollback Gate passed for P/17 and P/43. Prospectively fixed
P/17 had zero failures/fallbacks and small/large charged means 0.857511/0.681739;
P/29 retained three failures and P/43 one. Both pooled large-y cells passed 9/9.
Final charge was 6,536.080252125 seconds with peak RSS 829,194,240 bytes;
see `docs/validation/b4_7_spatial_rollback.md`. B4.8 then completed 96/96 new
references, all 1,152 outcomes, 1,250 production audit units and 1,295 independent
terminal/classification checks. Its larger rollback confirmation Gate failed:
P/17 and P/43 passed single-seed criteria, but fixed P/17 retained one quality
failure/fallback and violated its zero-failure primary requirement. P/29 retained
four failures and P/43 one. P/17's charged small/large means were
0.820141/0.668344 and total ratios 0.786037/0.639162; both pooled large-y
cells passed 17/18 and 18/18. Final charge was 14,105.836381712 seconds with
peak RSS 1,036,238,848 bytes; see
`docs/validation/b4_8_rollback_confirmation.md`. The next slice is B4.9:
bounded read-only diagnosis of the complete failed confirmation, retaining every
outcome, cost and fixed-primary failure. No new fit, threshold search, seed
substitution or final access is authorized by that diagnosis. A passing repair
and independent confirmation remain required before a compatible final contract
and B5. Diagnosis alone does not authorize progression.
The original B4.2 Gate remains failed and final evaluation remains sealed;
uniform remains the operational default, and no final acceleration claim
is allowed before the later final Gates.
Follow the v2 English roadmap for later gates and slice order.

## Provenance boundary

The Hack3D reference repository has no declared open-source license. Do not copy,
translate, patch, vendor, or redistribute its code, comments, file structure, or
figures. Implement from published equations and independent derivation. Use the fixed
upstream commit only for historical behavior comparison, and record any comparison or
new source in `PROVENANCE.md`.

## Development rules

- Keep each change scoped to one numerical behavior with tests.
- Freeze conventions in `docs/numerical_conventions.md` before relying on them.
- Prefer the current small module plan; split modules only when stable responsibilities
  or multiple callers justify it.
- Do not add FastAPI, React, Redis, PyTorch, data generation, or ML before gate N2.
- Do not claim `validated`, `scalable`, or `accelerated` until the documented evidence
  gate is complete.
- Never commit generated datasets, run artifacts, caches, secrets, or device IDs.
- Name branches by deliverable without `codex` or other agent-name tokens;
  merge PRs only after CI passes and report the next slice after each slice.

## Required validation

Run before every commit:

```bash
uv sync --dev --locked
uv run ruff check .
uv run mypy src
uv run pytest
git diff --check
```

If a numerical test requires a tolerance change, explain the scale/conditioning reason
in the validation report; do not silently loosen it.
