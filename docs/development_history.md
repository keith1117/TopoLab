# Development history

Retained project-state summaries through B4.27 active-set evidence implementation.
This history was moved from
`AGENTS.md` during the 2026-10-06 documentation cleanup; all recorded results,
failures, costs and stopping boundaries are preserved. Statements about the
next slice or a development primary describe their historical context.
Read [project status](project_status.md) for the current boundary and
[validation reports](validation/README.md) for the authoritative evidence.

## Historical baseline and early development

The historical `v1.0.0` release and Gates N1, N2, P1, M0, and A1 are complete. M1 did
not establish learned acceleration; M2 failed its data gate; the bounded M3 v1
pre-registration was superseded before fitting or final evaluation. The active v2
roadmap requires reproducible, same-quality ML end-to-end acceleration on a predefined
workload before the full flagship project is delivered. Until that evidence exists,
uniform initialization is the operational default and no accelerated claim is allowed.

Track B has development-only warm-start feasibility evidence in
[validation/ml_feasibility_probe.md](validation/ml_feasibility_probe.md), B1 failure
diagnosis in [validation/b1_failure_diagnosis.md](validation/b1_failure_diagnosis.md),
and A3 solver-ordering evidence in
[validation/a3_solver_ordering.md](validation/a3_solver_ordering.md). The fixed B2
workload pilot is recorded in
[validation/b2_workload_pilot.md](validation/b2_workload_pilot.md): Gate B2 failed
because three of six larger uniform references did not converge at the frozen limit and
the five unchanged M1 starts were slower after fallback charges.

## B2.1

B2.1's opt-in, versioned physical-plateau policy made all twelve uniform references
quality-feasible; its matched five-seed M1 panel remains slower after fallback charges.
See [validation/b2_1_convergence.md](validation/b2_1_convergence.md).

## B2.2

B2.2 froze a bounded quality-aligned development-prototype plan, but only 53/61 uniform
data sentinels converged at 120 updates.

## B2.3

B2.3 preserved all 61 source cases, versioned their iteration cap to 240, and passed
61/61 independent quality checks without changing the previous 53 accepted outcomes. See
[validation/b2_2_data_feasibility.md](validation/b2_2_data_feasibility.md) and
[validation/b2_3_data_feasibility.md](validation/b2_3_data_feasibility.md).

## B2.4

B2.4 passed the complete 522/522 development-label and resource Gate; see
[validation/b2_4_development_labels.md](validation/b2_4_development_labels.md).

## B2.5

B2.5 completed six fixed fits and all 54 development validation cases, but every learned
seed was slower than matched uniform on both mesh scales after complete fallback
charges; see [validation/b2_5_prototype.md](validation/b2_5_prototype.md).

## B2.6

B2.6 then captured all 480 fixed intermediate-trajectory targets, completed three fits
and all 12 new-case screen outcomes, but its development feasibility Gate failed: all
three new seeds were slower than matched uniform at both mesh scales after complete
fallback charges. See [validation/b2_6_trajectory.md](validation/b2_6_trajectory.md).

## B2.7

B2.7 changed only the point-load representation, reused all 480 B2.6 targets, completed
three fits and a fresh 12-case, 132-outcome screen. It improved seeds 17/29
substantially against B2.6, but its Gate failed: no new seed met the required two-scale
and direction-wise charged speed limits. See
[validation/b2_7_global_load.md](validation/b2_7_global_load.md).

## B2.8

B2.8 tested an opt-in y-direction midpoint between each fixed B2.7 prediction and
uniform start on 12 new cases. All 132 outcomes were audited, but its Gate failed: no
seed met the two-scale/direction bounds, the three seeds retained the same 2/3/4 failure
counts as the controls, and the unchanged z predictions were slow on this fresh
load-position/volume cohort. See [validation/b2_8_basin.md](validation/b2_8_basin.md).

## B2.9

B2.9's vector point-load conditioning completed three fits and all 132 new-case
outcomes. Seeds 29 and 43 had zero fallbacks and met both scale-mean charged-speed
bounds, but their large-y direction means exceeded 1.0, so the frozen Gate failed. See
[validation/b2_9_vector_load.md](validation/b2_9_vector_load.md).

## B2.10

B2.10 completed all 480 sensitivity-weight artifacts and three fits, but its frozen
screen stopped after 9/12 cases and 99/132 outcomes: the tenth case's mandatory uniform
reference did not converge at 240 updates. The failed Gate and partial learning-side
evidence are retained in
[validation/b2_10_weighted_trajectory.md](validation/b2_10_weighted_trajectory.md).

## B2.11

B2.11's versioned 360-update budget passed its twelve-pair old/new sentinel and all
twelve fresh uniform references, then retained all 132 fixed-model outcomes. Neither
B2.9 nor B2.10's three-seed panel met the two-scale/direction-wise charged-speed Gate;
see [validation/b2_11_reference_budget.md](validation/b2_11_reference_budget.md).

## B2.12

B2.12's fixed spatial-context CNN passed 12/12 new uniform references and completed
three fits plus all 132 new-case outcomes. Its validation MSE and small-z refinement
improved, but every new seed exceeded the large-scale charged-speed bound; the
high-volume y quality gap and large-z refinement regression persisted. See
[validation/b2_12_context_cnn.md](validation/b2_12_context_cnn.md).

## B2.13

The next independent slice, B2.13, froze a workload-aware routing/safe-rejection policy.
Its 12 fresh uniform references and all 144 screen outcomes passed the bounded
development Gate, but the routed policy did not beat the best fixed context model on
this cohort. See [validation/b2_13_routing.md](validation/b2_13_routing.md).

## B2.14

B2.14 then froze and completed a larger, physically disjoint 24-case development
confirmation: 24/24 new uniform references and all 192 outcomes passed completeness and
quality audits, but no routed or fixed single-model policy met the predeclared
two-scale/direction-wise Gate. See
[validation/b2_14_development_confirmation.md](validation/b2_14_development_confirmation.md).

## B2.15

B2.15's fixed position-aware route passed 24/24 fresh uniform references and retained
all 192 outcomes, but failed its development Gate: the large-y charged mean exceeded 1.0
and the overall gain over the old route was below the frozen 5% requirement. See
[validation/b2_15_position_routing.md](validation/b2_15_position_routing.md).

## B2.16

B2.16's read-only audit of the 48 exposed B2.14/B2.15 cases found optimistic
fixed-checkpoint headroom but failed coarse-cell transfer in both directions. Its
ordered decision permits one bounded online early-reliability probe while stopping
further exposed-cohort routing-threshold searches; see
[validation/b2_16_method_class.md](validation/b2_16_method_class.md).

## B2.17

B2.17's frozen two-update online signal stayed within its cost cap but missed all three
known terminal failures on the four-case exposed sentinel; its stop rule kept all 24 new
cases sealed. See
[validation/b2_17_early_reliability.md](validation/b2_17_early_reliability.md).

## B2.18

The B2.18 solver-anchored start modestly improved compliance and update counts, but all
three historically failing cases still missed terminal quality and paid fallback; its
frozen stop rule kept four new cases sealed. See
[validation/b2_18_solver_anchor.md](validation/b2_18_solver_anchor.md).

## B2.19

B2.19's paid uniform-state sensitivity input passed twelve new uniform references and
three fits, but its complete 84-outcome screen failed the learned Gate despite lower
validation MSE for all three seeds. See
[validation/b2_19_physics_input.md](validation/b2_19_physics_input.md).

## B2.20

B2.20's operational checkpoint selection completed 12 selection cases and 24 independent
screen cases, with all 132/168 outcomes audited; no selected seed passed, and 0/6
high-volume large-y selected attempts passed terminal quality. See
[validation/b2_20_operational_selection.md](validation/b2_20_operational_selection.md).

## B2.21

The next independent slice was B2.21: its terminal-design learning target passed 24/24
fresh uniform references, 12/12 validation targets, three fits, and all 168 screen
outcomes, but no new seed met the full Gate and 0/6 high-volume large-y new attempts
passed terminal quality. See
[validation/b2_21_terminal_target.md](validation/b2_21_terminal_target.md).

## B2.22

B2.22's high-volume y-direction specialist completed 24/24 new references, three fits,
and all 168 fully charged screen outcomes. Its matched high-volume large-y quality
improved from 2/6 fixed-control successes to 3/6, below the frozen 4/6 minimum; no seed
met the two-scale and direction-wise speed Gate. See
[validation/b2_22_y_specialist.md](validation/b2_22_y_specialist.md).

## B2.23

B2.23's bounded large-y load-position expansion passed its data Gate: 30/30
independently audited new uniform labels, with 20 train and 10 validation labels, within
the frozen time and memory caps. It made no model fit or acceleration claim; see
[validation/b2_23_position_labels.md](validation/b2_23_position_labels.md).

## B2.24

B2.24 completed 24/24 fresh references, three fits, ten independent diagnostic
validation labels, and all 168 fully charged screen outcomes. The expanded route
improved matched high-volume large-y terminal quality from 0/6 to 6/6, but no new seed
met the two-scale and direction-wise speed Gate; see
[validation/b2_24_expanded_training.md](validation/b2_24_expanded_training.md).

## B2.25

B2.25's read-only cost audit found all ten expanded-model failures in y, while large-z
refinement remained costly; see
[validation/b2_25_residual_cost.md](validation/b2_25_residual_cost.md).

## B2.26

B2.26 then completed 24/24 references, three weighted terminal fits, and 240 fully
charged outcomes, but no seed met the large-scale speed Gate; see
[validation/b2_26_weighted_generalist.md](validation/b2_26_weighted_generalist.md).

## B2.27

B2.27's middle-volume large-grid y/z position expansion passed its data Gate: 60/60
independently audited uniform labels, with 40 train and 20 validation labels, within
frozen time and memory caps. It performed no model fit or learned comparison; see
[validation/b2_27_middle_volume_labels.md](validation/b2_27_middle_volume_labels.md).

## B2.28

The next independent slice was B2.28: its fixed forty-label generalist expansion
completed 24/24 fresh references, three fits, twenty diagnostic labels, and all 168
charged outcomes. All three seeds passed the bounded development Gate with zero
new-panel failures and 6/6 middle-volume large-y successes; see
[validation/b2_28_expanded_generalist.md](validation/b2_28_expanded_generalist.md).

## B2.29

B2.29's larger independent confirmation completed 48/48 new references and all 432 fully
charged outcomes with unchanged checkpoints and route. Seeds 17 and 43 passed the frozen
Gate; seed 29 failed the small-scale and small-z speed bounds. The expanded panel passed
9/9 middle-volume and 9/9 high-volume large-y attempts; see
[validation/b2_29_development_confirmation.md](validation/b2_29_development_confirmation.md).

## B3.1

The next independent slice was B3.1: its new `topolab.b3.experiment.v1` contract freezes
752 case definitions, 1,376 historical exposure fingerprints, twelve fits, prospective
validation-only primary selection, finite compute limits, and final ID/OOD plus
independent replication criteria; see
[b3_experiment_contract.md](b3_experiment_contract.md) and
[validation/b3_1_contract_boundary.md](validation/b3_1_contract_boundary.md). Its
metadata-only planning audit passed without a solver call, fitting, or label access.

## B3.2

B3.2 then implemented the exact catalog/ledger and membership-specific access guards,
matching both frozen hashes and rejecting forbidden roles, changed-budget origins, and
incomplete NN populations before byte reads; see
[validation/b3_2_catalog_boundary.md](validation/b3_2_catalog_boundary.md).

## B3.3

B3.3 then implemented versioned label/reference contracts, external content-addressed
artifacts, charged single-writer recovery, independent numerical audits, and a read-only
planning/explicit execution CLI; see
[validation/b3_3_data_materializer.md](validation/b3_3_data_materializer.md). Its tests
used synthetic states, and no production B3 case was optimized in that slice.

## B3.4

B3.4 then executed all 560 labels and 48 screening references from clean merged revision
`cc151b014f9034ccc7093ef592021003d7dec252`. All 608 outcomes passed complete independent
quality, provenance, stratum and resource audits with zero failures. The total charged
data phase was 5,325.353116 seconds and peak RSS was 500,154,368 bytes; see
[validation/b3_4_data_gate.md](validation/b3_4_data_gate.md). Gate B3 passed without a
model fit or final artifact access.

## A2.1

A2.1 then introduced a versioned JSON-line manager/worker protocol and local separate
process for default numerical runs; see
[validation/a2_1_worker_protocol.md](validation/a2_1_worker_protocol.md).

## A2.2

A2.2 then added leased SQLite ownership, heartbeat, fenced writes, queued-record
recovery and versioned schema migrations; see
[validation/a2_2_run_ownership.md](validation/a2_2_run_ownership.md).

## B4.1

B4.1 then completed all twelve fixed CPU fits and their independent artifact/selection
audit, retaining all 1,902 attempted epochs and 24 artifacts within the 7,200-second and
4-GiB caps; see [validation/b4_1_fixed_fitting.md](validation/b4_1_fixed_fitting.md).

## B4.2

B4.2 then completed all 48 screening cases and 720 fully charged outcomes. Its
independent numerical/artifact/selection audit passed after repairing a supplemental
audit's forbidden single-label NN read; the rejected attempt, cost and permanent ledger
marker remain retained. No P seed passed the frozen direction/reliability Gate, so no
primary or freeze was produced; see
[validation/b4_2_development_screen.md](validation/b4_2_development_screen.md).

## B4.3

B4.3 then completed the read-only diagnosis of all 720 outcomes and 162 identical-model
pairs. It found substantial timing dispersion, two converged generalist quality gaps and
one 360-update generalist convergence failure, without changing any prior result; see
[validation/b4_3_failure_cost.md](validation/b4_3_failure_cost.md).

## B4.4

B4.4 then passed its frozen engineering sentinel: all 76 queries and 100 terminal states
were independently audited with unchanged numerical outcomes and failures. Bounded
progress and full query timing reduced callback wall by 99.8243% and query wall by
25.3881% in the checkpoint-stress sentinel, within its 7,200-second / 2-GiB caps; see
[validation/b4_4_engineering.md](validation/b4_4_engineering.md). This establishes no
learned acceleration.

## B4.5

B4.5 then completed three fixed sensitivity-weighted terminal-design fits (466 attempted
epochs), 48 fresh uniform references and all 576 fully charged outcomes. Independent
audits passed all 644 terminal states and resource closure. W/17 and W/43 passed the
bounded development Gate with zero failures/fallbacks; W/29 failed reliability. W/17 is
the development primary. Final charge was 7,578.184891 seconds and peak RSS 453,132,288
bytes; see [validation/b4_5_weighted_terminal.md](validation/b4_5_weighted_terminal.md).

## B4.6

B4.6 then completed 96/96 new uniform references, all 1,152 outcomes, 1,250 audit units
and 1,291 independent terminal/classification checks. Its larger confirmation Gate
failed: fixed W/17 had two failures/fallbacks, W/29 had four and only W/43 passed
single-seed criteria with one fallback. Both pooled large-y cells passed 18/18, but no W
primary was eligible. Final charge was 12,528.446019750 seconds with peak RSS
1,492,172,800 bytes; see
[validation/b4_6_development_confirmation.md](validation/b4_6_development_confirmation.md).

## B4.7

B4.7 then completed 48/48 fresh references, all 576 fully charged outcomes, 626
production audit units and 646 independent terminal/classification checks. Its bounded
spatial-objective rollback Gate passed for P/17 and P/43. Prospectively fixed P/17 had
zero failures/fallbacks and small/large charged means 0.857511/0.681739; P/29 retained
three failures and P/43 one. Both pooled large-y cells passed 9/9. Final charge was
6,536.080252125 seconds with peak RSS 829,194,240 bytes; see
[validation/b4_7_spatial_rollback.md](validation/b4_7_spatial_rollback.md).

## B4.8

B4.8 then completed 96/96 new references, all 1,152 outcomes, 1,250 production audit
units and 1,295 independent terminal/classification checks. Its larger rollback
confirmation Gate failed: P/17 and P/43 passed single-seed criteria, but fixed P/17
retained one quality failure/fallback and violated its zero-failure primary requirement.
P/29 retained four failures and P/43 one. P/17's charged small/large means were
0.820141/0.668344 and total ratios 0.786037/0.639162; both pooled large-y cells passed
17/18 and 18/18. Final charge was 14,105.836381712 seconds with peak RSS 1,036,238,848
bytes; see
[validation/b4_8_rollback_confirmation.md](validation/b4_8_rollback_confirmation.md).

## B4.9

B4.9 then completed bounded read-only diagnosis of all 96 references and 1,152 outcomes,
with 1,295 independent quality classifications, 48 strata and 54 identical-specialist
pairs audited. Its diagnostic acceptance passed within 81.608446500 seconds /
277,626,880 bytes, including the retained failed metadata preflight. Fixed P/17's
converged physical-plateau stop retained a compliance ratio of 1.001056679441 above
1.001; all original failures, costs and the failed confirmation remain unchanged. See
[validation/b4_9_confirmation_diagnosis.md](validation/b4_9_confirmation_diagnosis.md).

## B4.10

B4.10 then completed its frozen nine-case post-plateau sentinel: 9 references, 108
outcomes, 119 numerical/input audit units, 117 policy audit units and 132 independent
terminal classifications. All 24 prepolish witnesses, 12 fixed twenty-update
continuations and 96 unchanged outcome identities passed integrity audits. Its Gate
failed: all four known large-y P failures were repaired, but fixed P/17 gained one new
convergence failure/fallback on an originally accepted case. Its four-case large-y
generalist mean charged ratio was 1.222377 and ratio of charged sums 1.226342, both
above 1.0. All 48 fresh cases remain sealed. Final charge was 2,106.109270792 seconds
with peak RSS 635,076,608 bytes; see
[validation/b4_10_post_plateau_polish.md](validation/b4_10_post_plateau_polish.md).

## B4.11

B4.11 then completed the bounded read-only review: nine references, 108 outcomes, 132
terminal classifications, 24 prepolish certificates, 48 strata and nine specialist pairs
passed independent arithmetic audit. The P/17 regression loses its terminal convergence
certificate after 97 updates despite better compliance; it is not iteration-cap
exhaustion. Fixed-primary measured target ratios remain 1.222377/1.226342; fallback-free
diagnostic bounds are 0.980302/0.948499, with all observed failures preserved. Charge
was 59.88 seconds and peak kernel RSS 92,798,976 bytes; the retained outer diagnosis
profiler limitation is documented in
[validation/b4_11_polish_diagnosis.md](validation/b4_11_polish_diagnosis.md).

## B4.12

B4.12 then passed its exposed nine-reference/108-query preservation sentinel: all four
historical P failures were repaired, fixed P/17 had zero fallbacks, and its target
mean/sum charged ratios were 0.958024/0.938039. All 48 fresh uniform references, 576
outcomes, 626 numerical/input audit units, 624 policy audit units and 922 independent
terminal classifications completed. Its fresh Gate failed: P/17 and P/43 passed
individual criteria but each retained one converged quality failure/fallback on the same
new large-y case; P/29 retained two and exceeded the large-y direction bound. All 26
fresh continuations paid 520 updates; no fresh original witness was selected. Fixed
P/17's zero-failure primary requirement failed. Native resource closure retained and
charged its initial exact-float-comparison failure, then recovered from separately
CI-passed merged source without numerical reruns. Final charge was 8,486.600 seconds and
peak RSS 1,017,036,800 bytes; see
[validation/b4_12_terminal_preservation.md](validation/b4_12_terminal_preservation.md).

## B4.13

B4.13 then completed the bounded read-only review of both complete panels: 57
references, 684 queries, 1,101 terminal classifications, 159 candidate witness pairs, 96
strata and 36 same-specialist pairs passed independent arithmetic audit. Fixed P/17's
fresh original and twenty-update endpoint both retain plateau certificates but fail
compliance quality. The nine-case large-y generalist fallback-free mean remains
1.012013; observed failures and all original charges remain unchanged. Diagnostic charge
is 107.78 seconds and peak RSS 109,936,640 bytes; see
[validation/b4_13_preservation_diagnosis.md](validation/b4_13_preservation_diagnosis.md).

## B4.14

B4.14 then passed its bounded read-only generalist method review: all 684 certified
compact rows, 159 prior witness pairs, 96 prior strata and six mechanism dispositions
passed independent cost/headroom reconstruction. The 1,101 terminal classifications
remain prior B4.13 evidence, with no new raw state reads or numerical checks. All
failures and original charges remain unchanged. New charge is 50.39 seconds and peak RSS
42,287,104 bytes; see
[validation/b4_14_generalist_method_review.md](validation/b4_14_generalist_method_review.md).

## B4.15

B4.15 then completed its frozen eight-train-case offline compliance-adjoint probe: 16
fixed states, 48 full CPU forward/backward measurements, 64 directional differences and
200 FEM solves were retained. All 408 independent numerical conditions passed; maximum
directional error was 3.32609e-6. The separately versioned training projection leaves
the existing query path unchanged. Its bounded prospective fit Gate failed: the
predeclared three-seed / 200-epoch / 508-case planning proxy was 60,339.394 seconds,
above 7,200. No fit, new label, checkpoint or screen/final access occurred. Complete
charge is 84.33 seconds and peak RSS 510,836,736 bytes; see
[validation/b4_15_offline_compliance_adjoint.md](validation/b4_15_offline_compliance_adjoint.md).

## B4.16

B4.16 then passed its bounded read-only cost review: all 48 retained wall/CPU
observations, sixteen fixtures and 818 independent arithmetic/boundary conditions
passed. The original 60,339.394-second prospective proxy and failed Gate remain
unchanged. Even zero small physics plus observed minimum large wall gives 13325.669
seconds, above 7,200; this is diagnostic sample arithmetic, not a rigorous
optimized-method bound or revised Gate. No FEM solve, new benchmark, label/model
artifact read, fit or final access occurred. New charge is 55.99 seconds and peak RSS
305,807,360 bytes; see
[validation/b4_16_offline_adjoint_cost_review.md](validation/b4_16_offline_adjoint_cost_review.md).

## B4.17

B4.17 then completed its frozen prepared-FEM probe: eight canonical train cases, sixteen
synthetic fixtures, all 96 paired full Torch measurements, 96 phase intervals and 256
new FEM solves were retained without new label or model bytes. All 768 independent
numerical/gradient conditions and 64 fixed directional differences passed. Immutable
setup is reused while current-density assembly and numeric factorization remain fresh.
Its new full-population/three-seed/200-epoch cost proxy failed: 58,257.457957 seconds
versus 7,200, including full-population preparations and all B4.15/B4.16/current
charges. Original Gates and P/17 remain unchanged. Complete new charge is 112.34 seconds
and peak RSS 486,866,944 bytes; see
[validation/b4_17_prepared_fem_probe.md](validation/b4_17_prepared_fem_probe.md).

## B4.18

B4.18 then passed its bounded read-only FEM/objective method review: all 96 paired
observations, 96 phase intervals and six method dispositions passed 1286 independent
arithmetic/identity/boundary conditions. Original failed cost Gates and charges remain
unchanged; the large instrumented factorization share is 82.3882%. The review performs
no FEM, loss/gradient evaluation, label/model artifact read or fit. New charge is 86.13
seconds and peak RSS 301252608 observed bytes; the charged initial static-plan timer
failure has unavailable RSS, explicitly retained in
[validation/b4_18_fem_objective_method_review.md](validation/b4_18_fem_objective_method_review.md).

## B4.19

B4.19 froze and executed its single train-only signed tangent candidate, but stopped at
the anchor-compliance/normalizer rtol1e-9 integrity check. No complete numerical probe
was published; the planned independent numerical audit, local fidelity and prospective
fit cost remain unevaluated. Failed case, numerical gap, exact label/FEM counts and
buffered fields were not emitted and remain unavailable; no numerical rerun or
tolerance/normalizer change occurred. The source exposes a stored float32 physical-
density versus unquantized filtered-anchor boundary for B4.20 to verify. Metadata-only
early-stop audit and native resource closure passed, paying 73.93 seconds / 311902208
bytes; no fit, new label, model bytes, continuation, reference, screen or final access
occurred. See
[validation/b4_19_local_compliance_surrogate.md](validation/b4_19_local_compliance_surrogate.md).

## B4.20

B4.20 then completed its frozen stored-normalizer tangent correctness review: eight
guarded train cases, sixteen projected synthetic inputs, 64 directional rows and 32 new
FEM solves completed 984 independent numerical conditions; 983/984 passed, and one FD
error exceeded the unchanged 1e-4 bound. The new intercept retains the audited stored
denominator while separately analyzing float32 physical and continuous filtered states;
6/8 current anchors would reject the old equality. The original B4.19 failure/count/gap
fields stay unknown. Durable before-call journals retain complete current
counters/prefixes. New charge is 100.30 seconds and peak RSS 447741952 bytes; see
[validation/b4_20_surrogate_correctness.md](validation/b4_20_surrogate_correctness.md).

The next slice is B4.21 bounded surrogate correctness failure review. It has not
started. No fidelity or fit proxy was measured; no fitting or final access occurred. All
prior failures, P/17 and sealed cohorts stay unchanged. The failed exact-FEM candidate
stops; no fitting, alternate cache/ordering, epoch/population/physics-frequency search
or final access is automatic. Full training memory feasibility remains pending. Fixed
P/17 is unrepaired; passing repair and independent confirmation remain required before a
compatible final contract and B5. All 48 B4.10 fresh cases stay sealed. The original
B4.2 Gate remains failed and final evaluation remains sealed; uniform remains the
operational default, and no final acceleration claim is allowed before the later final
Gates. Follow the v2 English roadmap for later gates and slice order.

## B4.21

B4.21 completed the frozen read-only correctness failure review. All 80 saved
gradient/mask checks and 1152 independent scalar comparisons passed across
eight cases, sixteen fixtures and 64 original rows at both steps. The old failed
discrepancy fits the predeclared root/arithmetic envelope; missing side offsets
and volume residuals remain unknown and no cause is established. B4.20 remains
failed 983/984, with unchanged tolerance, 32 solves and 100.30-second charge. B4.19's
missing case/gap/counts and every prior charge remain. No new root/FEM,
label/model read, fit, fidelity/cost or final access occurred. New charge is
90.27 seconds; peak RSS 300400640 bytes. See
[validation/b4_21_correctness_failure_review.md](validation/b4_21_correctness_failure_review.md).

Next is B4.22 bounded stable-projection correctness probe, separately frozen
before numerical invocation. Full training memory, learned repair and independent
confirmation remain pending; fixed P/17 is unrepaired, uniform remains default
and all final/48 unused B4.10 cases stay sealed.

## B4.22

B4.22 completed the separately versioned stable-projection correctness probe;
Gate passed. 1704/1704 independent conditions passed across eight cases, sixteen fixtures
and 64 rows at both steps. Maximum directional error is 5.64e-9; 32 FEM solves
and 304 projections were paid. The one affine free-set root refinement preserves the
stored denominator, continuous intercept and mathematical projection/cotangent.
Offsets/residuals/kink margins, original steps and durable prefixes remain.
New charge is 104.62 seconds; peak RSS 433274880 bytes. All earlier failures,
B4.19 unknowns and complete charges remain; no fidelity/cost, fit or final access
occurred. See [validation/b4_22_stable_projection_correctness.md](validation/b4_22_stable_projection_correctness.md).

Next is B4.23 bounded versioned local-surrogate fidelity and cost probe, separately frozen before execution.
Full training memory, learned repair and confirmation remain pending; P/17 is
unrepaired, uniform remains default and final/48 unused B4.10 cases stay sealed.

## B4.23

B4.23 completed its separately frozen versioned local-surrogate fidelity/cost
attempt; feasibility Gate failed. Integrity passed 3907/3976, with 35 side-mask
and 34 finite-difference conditions failed. All 32 LOCAL states met the observed
fidelity criteria, which cannot clear the failed integrity Gate. Complete cost
proxy is 57546.072069 seconds against 7200, retaining the first timing and all
707.91 seconds of B4.15–22 charges. All 72 states, 216 timings and 64 directional
rows remain; 432 FEM solves and 816 projections were paid.
New charge is 143.47 seconds; peak RSS 550502400 bytes. Complete counts,
native profiles, first-inclusive costs, root scalars and numerical prefixes
remain external. The v3 kernel and all original criteria are unchanged;
B4.19 unknowns, B4.20 failure and every prior charge remain. See
[validation/b4_23_versioned_surrogate_feasibility.md](validation/b4_23_versioned_surrogate_feasibility.md).

Next is B4.24 bounded versioned surrogate correctness failure review, separately
frozen before execution.
No fit, new label/reference, model, learned repair, continuation or final access
occurred. Full training memory and confirmation remain pending; P/17 is unrepaired,
uniform remains default and final/48 unused B4.10 cases remain sealed.

## B4.24 (registered continuation; scoped review acceptance passed)

The v1 reader stopped at a three-field schema mismatch, preserving its 16.19-second
charge and unavailable complete arithmetic. Separately registered v2 source
passed 1086 tests/source/main CI, but its default planning wrapper lost RSS
inside the sandbox: wall 4.73/user 1.95/system 0.40, child exit unknown. V2 arithmetic
review/audit were not invoked. Original metadata accounting 76.19 and reserved
use 50.53/60, both failures and every original binding remain unchanged; see
[the immutable interrupted report](validation/b4_24_versioned_correctness_failure_review.md).

The owner approved one separately paid 60-second reserve under the
[v3 registration](planning/b4_24_registered_continuation_protocol.md), keeping
whole 240-second and cumulative 60-second review caps and all scientific criteria. Clean CI-passed merged
source invoked exactly one unused compatibility review and one independent
auditor: all 2104 saved-state predicates and 1728 field comparisons passed.
The 35 mask/34 FD failures overlap on 34 rows; all failed FD intervals cross
clipping sets and fit the frozen signed decomposition, without a global causal
or wrong-pointwise-gradient claim. Every original failure, first timing and
57546.072069>7200 cost remains. See [the complete v3 report](validation/b4_24_registered_continuation.md).

Total B4.24 charge 200.98 includes both paid 60-second reserves; new reserved use 42.49/60
and measured continuation RSS 415268864 bytes satisfy the registered scope. Historical
missing RSS, whole peak and global memory compliance remain unknown; the old
memory proof stays incomplete. B4.24's approved continuation is closed; full training memory
remains pending and the old scientific Gates stay failed. Next is B4.25 bounded active-set
objective-method review, not started and requiring a separately frozen read-only
boundary. B4.23/B4.20 failures, B4.19 unknowns and all 851.38 earlier seconds
remain. No new root/FEM/objective/gradient/prediction timing, label/model bytes,
fit or final access occurred. Uniform stays default, P/17 unrepaired and all
final/48 unused cases sealed. Ordinary single-slice stopping remains unchanged.

## B4.25 (bounded active-set method review; read-only acceptance passed)

The separately frozen stdlib review and auditor ran once from clean merged
CI-passed source. All 448 scalar predicates and 2222 independent field
comparisons passed. All 64 original rows, 35 mask/34 FD failures, 69 failed
positions, original fields/cost and 216 inherited first timings remain. All
failed FD intervals cross clipping sets and remain compatible with the frozen
decomposition, without global cause, pointwise-gradient failure or repaired Gate.
The strictly fixed-set derivative and six method dispositions select separate
active-set-aware evidence preregistration only. Two fixed zero-work scenarios
are sample arithmetic; original 57546.072069>7200 cost and all failures remain.
See [the complete report](validation/b4_25_active_set_method_review.md) and
[prospective protocol](planning/b4_25_active_set_method_review_protocol.md).

New charge 80.34/180 includes the entire paid 60 reserve, use 40.41/60
and peak 26492928 bytes. All five native wall/user/system/RSS profiles, unchanged
ledger and final post-exit proof passed. B4.24's 200.98, both old failures,
old 76.19/50.53 reserve and historic missing RSS/whole-memory unknowns remain;
old memory proof/full fitting-memory feasibility is not completed. All 851.38
B4.15–23 charges, B4.20 failure and B4.19 unknowns are preserved.
The source's producer-order and binary-charge compatibility issues were caught
before production, covered by 50 focused regressions and all 1158 tests; no
scientific tolerance or prior byte binding changed. No new root/FEM/objective/
gradient/prediction timing, label/model payload, fit, learned repair or final
access occurred. Uniform stays default, P/17 unrepaired and all final/48 unused
fresh cases sealed. Next is **B4.26 bounded active-set-aware correctness and cost preregistration**,
not started; require a separate prospective read-only contract and explicit
research/execution criteria. Stop after B4.25.

## B4.26 (read-only active-set-aware correctness and cost preregistration)

The separately frozen protocol and authored acceptance contract passed 66 static
metadata predicates and 28 independently implemented document/metadata checks.
They retain the unchanged v3 mathematical map, full 64-row/69-failure legacy
panel and both steps, requiring independent pointwise cotangents and complete
transition-interval evidence. Undefined central derivatives or incomplete piece
coverage stop acceptance. LOCAL fidelity, first-inclusive maximum costs, all
prior charges and 4-GiB full training-memory requirements remain separate.
No production payload, root/FEM, objective/gradient, prediction timing, fit or
final access occurred. This passes only preregistration, clearing no scientific
Gate; B4.23/B4.20 failures, B4.19 unknowns, B4.24's historic memory gap and all
previous charges remain. See [the report](validation/b4_26_active_set_preregistration.md)
and [protocol](planning/b4_26_active_set_preregistration_protocol.md).

Next is **B4.27 bounded active-set evidence implementation**, not started and
software only under a separate frozen contract. No numerical execution or fit
is inherited. Uniform stays default, P/17 unrepaired and final/all 48 unused
B4.10 cases sealed. Full training memory, learned repair and independent
confirmation remain pending. Stop after B4.26.

## B4.27 (bounded active-set evidence implementation; software acceptance passed)

The separately frozen software contract implements independent full pointwise
cotangents and complete exact affine-piece interval certificates. 42 public
synthetic analytic/exhaustive/tampering and unchanged-v3 checks passed. Every
piece retains offsets, residuals, signed one-sided slopes and simultaneous
transitions; exact coverage rejects even sub-tolerance gaps. Undefined central
states and incomplete/degenerate certificates stop; at most 256 pieces and both
original steps remain. Legacy mask/FD failures are separately retained.
See the [report](validation/b4_27_active_set_evidence.md) and
[protocol](planning/b4_27_active_set_evidence_protocol.md).

No production payload, FEM, prediction timing, numerical trial, fit or final
access occurred. The old v3/query source and 147 historical frozen records,
B4.23/B4.20 failures, all charges and historical unknowns remain. Full training
memory and learned repair/confirmation stay pending. Software resources are
separately retained; unmeasured authoring/remote resources remain unknown.
Next is **B4.28 bounded active-set numerical evidence preregistration and
execution**, not started and requiring separate explicit numerical authorization
and a frozen finite execution contract. Uniform stays default, P/17 unrepaired
and final/48 unused B4.10 cases sealed. Ordinary repository stopping rules remain;
the owner's temporary at-most-three-slice authorization applies only to this chat.

## B4.28 (bounded active-set numerical evidence and finite execution)

The separately authorized finite eight-train-case protocol executed one native
attempt under clean merged exact-head/main-CI-passed source. New integrity
**PASS**, LOCAL **PASS**; new charge **234.60** including FULL60 reserve,
native resource acceptance **FAIL / INCOMPLETE**. Added cost
**58061.992069>7200** and full training memory remains
PENDING/4GiB. Preparation native wrapper exited1 after sandbox sysctl denial;
its RSS/child-exit proof stays UNKNOWN, with no retry and the full60 reserve
paid. Later chain peak674037760 cannot repair that gap. All old3976 flags/69 failures,216 first timings,432/816 counts,
851.38/200.98/80.34 charges, historical memory unknowns and B4.19 unknown actual
case/gap/counts remain. No retry, retiming, fitted repair, search or final access.
See [the complete report](validation/b4_28_active_set_numerical_evidence.md) and
[protocol](planning/b4_28_active_set_numerical_evidence_protocol.md). Source
PR157, its pre-production thread correction and closed release bind hashes/CI;41 public focused and1241 complete
software tests passed with earlier software failures preserved. Next is the
separately frozen read-only **B4.29 outcome and cost/full-memory review**, after
full closure/main CI and the final permitted session slice. Uniform stays
default, P/17 unrepaired, final/48 unused cases sealed; no fourth slice follows.

## B4.29 (bounded read-only outcome and cost/full-memory review)

The separate frozen final-third protocol executed one float scalar reviewer
and independently implemented Decimal audit on ten hash-bound B4.28 metadata
paths, under clean merged exact-head/main-CI-passed source. Metadata review
PASS, own native resources PASS; Q29=80.26 including FULL60 reserve,
known added cost58142.252069>7200, full fit-memory PENDING/4GiB. B4.28 new
3232/3232 and32/32 stay passed; its preparation RSS/exit/whole-memory gaps
remain UNKNOWN/INCOMPLETE. Every old failure,69 positions,216 first timings,
432/816 counts and all851.38/200.98/80.34 costs/unknowns remain. No raw input,
label/model, numerical call, fit, retiming, search or final access occurred.
46 public focused/1287 full software tests pass. Source/evidence PRs,
all-upload publication review, immutable native receipts and external verified
backup bind the [report](validation/b4_29_active_set_outcome_review.md). The
temporary three-slice authorization ends here; no fourth slice. Next research
intervention is undecided, requiring an owner decision and finite contract.
Uniform/P17/final/48-unused boundaries and ordinary waiting remain unchanged.

## B4.30 (fixed-P/17 reflection repair, interrupted preflight; unfinished)

Separately authorized after complete/exhausted B4.27–29. Protocol and same-weight
reflection implementation merged via PR162 after34 focused/1321 full tests,
all applicable exact-head/main CI and tested-tree equality. One campaign under
source `d40e0198802c` stopped at the strict legacy untracked-file cleanliness
check, preserving both owner documents. Zero references/queries/predictions/
encoders/FEM/model/label payload reads;68 metadata guards/136 events matched.
Paid191.9666532080154866 includes FULL180 and failed/whole native exits.
Independent metadata-prefix audit PASS; scientific Gate NOT ESTABLISHED,
production resources FAIL/INCOMPLETE. All18/270 scientific work and conditional
48/720 remain unexecuted, full slice unfinished. Entry correction checks all
dirty paths before output/input preparation;36 focused/1323 complete software
checks and all five mandatory commands pass before the correction commit.
A separate clean checkout passed the unchanged inspector. Failed evidence and
verified66-file backup stay external, bound by the
[report](validation/b4_30_z_reflection_repair.md) and unchanged
[contract](planning/b4_30_z_reflection_repair_contract.json). The consumed
one-campaign limit needs an explicit owner decision for a paid continuation
of this same slice, retaining failed cost and43200/2GiB/66/990 limits.
No retry/count reset/new slice/fit/search/final access; uniform/P17/seals and
all old failures/cost/memory unknowns remain. This entry records an interruption,
not scientific acceptance or full B4.30 completion.


The owner subsequently approved one paid technical continuation of this same
unfinished slice, with separately versioned [v2 protocol](planning/b4_30_paid_continuation_protocol.md)
and [contract](planning/b4_30_paid_continuation_contract.json) before new access.
Retain invocation1/191.9666532080154866 and all original bytes; at most2 total
administrative invocations and1 completed numerical campaign, with no third.
Whole43200/2GiB/66/990 and every scientific criterion/role/seal remain. The new
FULL180 and deducted sentinel reference/fresh-reservation caps are explicit.
Only paid execution compatibility/accounting changes; fixed P/17 reflection
mathematics and all original cases/controls stay unchanged. Source/CI release
and complete numerical/audit/publication closure are pending.


**Same B4.30 subsequent finite closure (2026-10-08):** PR164 tested head
`a8ab5a1bc278`/main `f561f31303ec`, all applicable exact-head/main CI and whole-clean
locked independent source preceded the only additional paid invocation. All18
references/270 queries,290 numerical/input units,288 policy units and the
independent raw-JSON/native exit audits complete. Scientific FAIL: fixed R17
original case55c1b3e… ratio1.0019709437499813>1.001, target mean
1.016053130777518>1.0; pooled0.9853173206553424 does not clear either failure.
Four historical target predicates pass already in matched P; no currently
failed P target newly repaired, paired P/R failures1/3/1. All35 attempt failures/
fallbacks,323 terminal/204 guard classifications,78 prediction replays/249
old identities retained. Fresh48/720 and final/unused panels unopened. Scoped
complete v2 resource PASS, cumulative7323.1004352501081506/43200 includes
old191.9666532080154866 and both FULL180; conservative complete chain peak
800047104<2GiB. Original failed16/software115/131-file backup and old memory
gaps/FAIL/INCOMPLETE remain. Source48 focused/1335 full tests pass; evidence
publishes the [complete report](validation/b4_30_paid_continuation.md), all5
checks, protected exact-head/main CI, all-upload guards and new byte backup.
This appends the final phase to the same historical interruption entry; it is
one slice,2 paid administrative invocations/1 numerical campaign. Old3/3 stays
exhausted. Proposed B4.31 metadata-only failure/cost review is not started and
needs owner authorization/finite contract; no third trial, fit/search or B5.


## B4.31 bounded read-only reflection failure and cost review (2026-10-08)

Owner-authorized one slice, prospectively frozen [protocol](planning/b4_31_reflection_failure_cost_review_protocol.md)
and [contract](planning/b4_31_reflection_failure_cost_review_contract.json);
[report](validation/b4_31_reflection_failure_cost_review.md). PR166 head13af1a4/
main4a51ebe6fbe6, all exact-head/main CI and whole-clean locked source preceded
one reviewer/one separate Decimal audit. Eight SHA-bound scalar/resource files
per role,118/118 and430/430 PASS; no raw/model/label, predictor/FEM/fit, retiming/
search or final/fresh/unused access. All15 methods/270 outcomes/35 failures/
fallbacks and seven historical P/R statuses preserved. Four historical target
predicates pass already in P; zero currently failed P target newly repaired.
R17 quality1.0019709437499813>1.001 and mean1.016053130777518>1.0 still fail;
pooled0.9853173206553424 cannot replace mean. Cause/per-target/fallback costs
stay unestablished/outside scope/UNKNOWN. Reflection and exact-FEM routes stop.

Own native resource PASS, Q31=80.29939475003629922/FULL60/180; reserve
11.16154991695657376<60, conservative native sum219463680<1GiB, last verifier
actual exit checked and original PENDING bytes retained. Old7323.1004352501081506
unchanged incl. failed191.9666532080154866/both FULL180. Separate campaign-plus-
review7403.39983000014444982 adds once. All prior failures/unknowns/memory gaps
and full fit PENDING/4GiB remain.58 focused/1393 source/1393 evidence full tests,
all5 checks and per-path/all-upload guards support protected evidence/main CI,
owned-branch cleanup and byte-verified external backup. Both owner documents and
README preserved. The source premerge driver KeyError/incorrect continuation
into merge is retained as a process failure; postmerge protection/equal-tree/
CI-time/resolved-thread audit passed before metadata, not a premerge PASS.
This closes only B4.31; old3/3 and B4.30's2-invocation/1-campaign counters stand.
Proposed B4.32 read-only generalist reliability/cost method review and
preregistration needs new owner authorization and a finite contract; no numerical
method selected, fit/search/final grant, learned acceleration claim or B5.

## B4.32 bounded generalist method review and preregistration (2026-10-08)

The owner's continuation after closed B4.31 authorized one documentation slice.
The finite [protocol](planning/b4_32_generalist_method_preregistration_protocol.md)
and [authored contract](planning/b4_32_generalist_method_preregistration_contract.json)
passed69 static and32 independent Decimal/document predicates. Six method
dispositions preserve stopped reflection/exact-FEM/signed-tangent candidates
and propose only a fixed-anchor reciprocal-energy algebra/access hypothesis.
Its conditional PSD/Cauchy–Schwarz bound and anchor gradient require exact
equilibrium; approximate FEM states remain UNCERTIFIED without independent
residual/spectral/rounding evidence. Eight future authored toy fixtures are
preregistered, with no new candidate evaluation, production payload, fit,
retiming/search or final/fresh/unused access. See [report](validation/b4_32_generalist_method_preregistration.md).

Known disjoint paid-stage subtotal12721.16417100014444982 exceeds7200 before
new work; it is diagnostic accounting, not a new cap or replacement of old
57546.072069/58142.252069 failed proxies or the7323.1004352501081506 ledger.
Q31=80.29939475003629922 remains paid once. All failed statuses,69 predicate
positions, B4.19 unknowns, historical memory gaps and B4.31 premerge process
failure remain. Scientific FAIL/P17 unrepaired/full fit PENDING/4GiB persist.
Runtime, tests, numerical conventions, all historical frozen files and README
remain unchanged. All five checks, document/per-path/all-upload guards and
protected exact-head/main CI plus a verified external backup govern closure.
Nine primary-checkout untracked files and unrelated branches are preserved.

Next proposed **B4.33 bounded reciprocal-energy algebra and access evidence
implementation** is software only, separately authorized/frozen and not started.
No production, fitting or new-budget permission follows. Uniform remains default;
conditional48/720, final and all48 unused B4.10 cases stay sealed. Stop here.

## B4.33 bounded reciprocal-energy algebra and access evidence (2026-10-08)

Owner continuation from closed B4.32/main0dcf79ed615b authorized one software
slice. The [protocol](planning/b4_33_reciprocal_energy_evidence_protocol.md),
[contract](planning/b4_33_reciprocal_energy_evidence_contract.json) and8 public
toy fixtures were frozen before implementation/evaluation.47 tests/849 independent
exact-rational/scalar predicates PASS,8 systems/76 points/30 original-step FD
intervals; maximum1.6918219473355736e-6<1e-4. Anchor/adjoint/upper/square-gap,
common scaling/zero energy and10/11 normalized intercept pass. Exact equilibrium
is mandatory; nonzero residual, mutation/unknown/outside panel rejects. Eight
role/schema/ID/hash denials occur before bytes. No real FEM/predictor/projection/
root/network integration, production payload, fit/retiming/search/final access.
See [report](validation/b4_33_reciprocal_energy_evidence.md).

Initial mypy/Ruff and inventory failures retain source/log/cost records; fixes
change no criteria. Source/tests/independent oracle/small fixtures and frozen
contract/report enter Git; complete software evidence stays external. All5
checks, existing per-path/all-upload guards, protected exact-head/main CI,
owned cleanup and independently verified backup govern closure. Nine primary
untracked files, prior clone copy, unrelated refs and old frozen bytes remain.
Scientific FAIL/P17 unrepaired/real certificates UNKNOWN/full fit PENDING4GiB;
old69 failures/UNKNOWN/memory gaps and all ledgers/reserves remain. Diagnostic
known-paid12721.16417100014444982>7200 grants no fit or new cap. Proposed next
B4.34 bounded read-only admissibility/full-cost preregistration, separate finite
metadata contract/owner continuation, not started. Uniform and all seals remain.

## B4.34 bounded read-only admissibility/full-cost preregistration (2026-10-08)

Owner “开始” after closed B4.33/main148a72a9c9d5/all main CI/no open PR
authorized one documentation slice. The [protocol](planning/b4_34_admissibility_full_cost_preregistration_protocol.md)
and [contract](planning/b4_34_admissibility_full_cost_preregistration_contract.json)
freeze12 versioned inputs,12 certificate/16 cost/8 memory obligations and10
stops. Static129/129 and independent document/Decimal43/43 PASS; see
[report](validation/b4_34_admissibility_full_cost_preregistration.md).
Conditional intended-PSD/uniform-coercivity/residual/outward-rounding bound and
positive SAME stored normalizer remain UNKNOWN_STOP. No real certificate
implementation/evaluation, payload/scalar replay, FEM/projection/root/network
integration, fit, profiling/retiming/search or final access occurs. Exact toy
equality does not transfer to approximate anchors; diagnostic bound changes no
original objective, gradient, normalizer, tolerance or active-set requirement.

Known paid12721.16417100014444982>7200 independently reconciles; all-paid
feasibility FAIL_KNOWN_PAID_FLOOR, actual new maxima/certification costs UNKNOWN,
full fit PENDING4GiB. No cap/ledger/history/population/epoch reset or budget grant.
All old69 failures/failed proxies, original7323.1004352501081506/both FULL180,
Q31 once, UNKNOWN/memory gaps/premerge process failure/P17/seals remain. Two
authoring metadata lookup failures retain UNKNOWN costs, without scope changes.
Initial full pytest1439/1440 failed the unchanged5s jobs wait; unchanged9-test
followup passed. Root cause UNKNOWN; failed1035.096664667013s wall/native
RSS/log/source and one unchanged full-check recovery remain, no criterion change.
Five mandatory checks, explicit-path/all-upload/squash guards, protected exact-
head/main CI, only owned cleanup and verified external backup govern closure.
Nine primary files/old clone copy/unrelated refs and all frozen historical bytes
remain; README/runtime/tests/conventions/locks/CI unchanged.

Next proposed **B4.35 bounded public admissibility-certificate software evidence**
needs new owner continuation/finite public-fixture contract, not started. No
actual data/FEM/timing/integration/fit/new cap or seal grant. Uniform default;
real certification/full cost/memory and learned repair/confirmation/full B4/
compatible final contract remain required. Stop after B4.34.

## B4.35 bounded public admissibility-certificate software evidence (2026-10-08)

Owner continuation from closed B4.34/main e2ebb5121f28/all main CI/no open PR
authorized one software slice. The [protocol](planning/b4_35_public_admissibility_certificate_protocol.md),
[contract](planning/b4_35_public_admissibility_certificate_contract.json) and8
original public systems freeze before implementation/evaluation.58 tests/394
candidate-free exact-rational predicates PASS over16 fixed anchor/current points.
Intended PSD/prescribed positive G-lower_G*I, exact residual/energy arithmetic and
fixed80-bit sqrt/outward binary64 produce diagnostic C<=B and SAME stored
normalization. Tiny nonzero residual exposes unmodified U<C; no tolerant zero
or approximate equality/adjoint transfer. Nine pre-byte denial cases and fixed
negative/tampering families reject. One formal producer/audit,16/16/0 each.
No actual data/FEM/timing/integration/fit/search/new cap or sealed access.
See [report](validation/b4_35_public_admissibility_certificate.md).

Four administrative metadata failures and first Ruff style failure retain
source/diagnostics/native costs; fixes change no criteria or frozen bytes.
All5 checks PASS/full1498 tests in670.09s; existing per-path/
staged/all-upload/squash guards, protected exact-head/main CI/tree identity/owned
cleanup/byte backup govern closure. Source/
independent oracle/auditor/tests/small public fixtures/protocol/contract/report
enter Git; generated evidence/controller/CI/native logs stay external. Nine
private files, unrelated refs and old clone copy remain. README/conventions/
runtime/query/ML/dependencies/CI and all old frozen evidence stay unchanged.
Public exact-rational certification does not certify rounded real FEM.
Scientific FAIL/P17 unrepaired, known-paid12721.16417100014444982>7200/all-paid
FAIL_KNOWN_PAID_FLOOR, real costs/certificates UNKNOWN_STOP/full fit PENDING4GiB
and every failure/69 predicates/UNKNOWN/gap/ledger/FULL reserve/quota/seal remain.
Proposed next **B4.36 bounded read-only certificate limitations and real-route
preregistration** requires separate owner/finite metadata contract, not started.
No real payload/FEM/fit/new cap or final grant follows; close B4.35 and stop.

## B4.36 bounded read-only certificate limitations/real-route preregistration (2026-10-09)

Owner “开始” from closed B4.35/main45a71fcfcfd1/all main CI/no open PR authorized
one document slice. The [protocol](planning/b4_36_certificate_limitations_real_route_protocol.md) and
[contract](planning/b4_36_certificate_limitations_real_route_contract.json) freeze18 versioned text/hash inputs before
one primary review/one separately implemented stdlib/Decimal audit:141/96 PASS.
Ten limitations/twelve prospective obligations/ten stops retain the gap from
authored exact public matrices to intended real Hex8/assembly, residual/spectrum/
rounding/SAME stored C_s, unchanged fidelity/reliability, all-paid/full memory.
See [report](validation/b4_36_certificate_limitations_real_route.md).

An independently derived conditional route bounds ||G-A_hat.T*A_hat|| by
delta_plus, ||I-Y*A_hat|| by eta_plus<1 and ||Y|| by M_plus>0. A strictly positive
directed ((1-eta_plus)/M_plus)^2-delta_plus proves a lower bound for SAME intended G;
element PSD remains separate. No real A_hat/Y or values are constructed/evaluated,
no real algorithm is frozen, and no alternate witness/precision/factor/order
search or matrix repair follows a failed premise. Original residual B_plus stays
diagnostic and replaces no loss/gradient. No old numerical/backup-member replay,
real payload/FEM/timing/integration/fit/search/new cap or sealed grant.

All original criterion/failure/cost/memory objects match B4.35 unchanged.
Scientific FAIL/fixed P17 unrepaired,69 old predicate failures/UNKNOWN/gaps/
ledgers/FULL reserves/old3/3/B4.30's2/1/uniform/seals remain. Known-paid
12721.16417100014444982>7200 remains infeasible; real costs/certificates UNKNOWN_STOP,
full fit PENDING/4GiB. One administrative helper-inventory path failure retains
UNKNOWN costs; both formal audits pass first invocation. All5 checks PASS/full
1498 tests in703.12s; existing publication guards, protected exact-head/main CI/tree identity/owned cleanup/
independent byte backup govern closure. Only11 documents enter Git; complete
native/source/audit/controller/CI receipts stay external. Nine private files,
unrelated refs, README/runtime/tests/conventions/dependencies/CI and frozen
historical evidence stay. Software RSS fills no real or historical memory gap.
Proposed next **B4.37 bounded public operator-enclosure and coercivity-witness
software evidence** requires separate owner/finite public-fixture contract before
implementation/evaluation; not started. No real route/fit/budget/final grant or
B5 follows. Close B4.36 and stop.

## B4.37 bounded public operator-enclosure/coercivity-witness software (2026-10-09)

Owner “继续” after closed B4.36/main71b11bae7c45/all main CI/no open PR
authorizes exactly one public software slice. Protocol/contract/ten authored
systems freeze before implementation/evaluation;21 source inputs,2 free DOFs/
3 elements/3 factor rows maximum, one prescribed factor/witness per system.
66 focused tests and217 independent exact-rational/identity predicates PASS
(161 case checks/56 source-contract identities). One formal producer/audit each
complete10/10/0:6 strictly positive lower bounds,4 prescribed stops. Exact
intended element PSD remains separate; exact G-A_hat.T*A_hat/I-Y*A_hat/Y norm
squares with fixed80-bit/outward binary64 endpoints and directed lower stages
certify only these SAME authored intended public operators. No assumed-zero
error, factor/inverse construction, solver, matrix repair or witness/precision/
order search. Positive G can stop because this witness bound is too conservative.
See [report](validation/b4_37_public_coercivity_witness.md), [protocol](planning/b4_37_public_coercivity_witness_protocol.md) and [contract](planning/b4_37_public_coercivity_witness_contract.json).

Real intended Hex8/representation/certification/construction/cost remain
UNKNOWN_STOP; no real algorithm is frozen. Original residual B_plus stays
diagnostic; loss/gradient/SAME stored normalization unchanged, tiny nonzero
residual never certifies unmodified U. All four prior criterion/failure/cost/
memory objects match B4.36 completely. Scientific FAIL/P17 unrepaired, known
paid12721.16417100014444982>7200/all-paid FAIL/full fit PENDING4GiB remain.
All old failures/69 predicates/UNKNOWN/gaps/ledgers/FULL reserves/3/3/B4.30's2/1/
uniform/seals stay. No actual payload/FEM/timing/integration/fit/new cap or seal.
One pre-contract quoted-path inventory failure retains UNKNOWN cost/child exit;
one native Ruff line-width failure and same-criterion recovery remain. Both
formal public invocations pass first attempt; no scientific standard changes.
Mandatory full validation and publication closure are recorded below.
All native/source/audit/CI records stay external; unprofiled authoring/metadata/
controller/Git/remoteCI UNKNOWN_NOT_ZERO. Software RSS fills no old or fit gap.

All5 mandatory commands PASS before commit, including complete pytest1564/1564
in699.00s with unchanged original tests/tolerances and one-thread CPU.
Reviewed-path/staged/all-upload/actual-squash guards, protected exact-head/main CI/
equal tested tree, owned-only cleanup and independent byte backup govern closure.

Only15 reviewed source/oracle/tests/original small public fixture/document paths
enter Git. Existing publication guards, protected exact-head/main CI/equal tree,
owned-only cleanup and independent byte backup govern closure. README/existing
runtime/tests/fixtures/conventions/locks/CI/frozen history stay; nine private files
and unrelated refs remain. Next B4.38 read-only limitations/real-construction
preregistration needs new owner/finite text-only contract; not started. No B5.
