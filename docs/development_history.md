# Development history

Retained project-state summaries through the B4.24 interruption. This history
was moved from
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

## B4.24 (interrupted; incomplete)

B4.24 froze a complete read-only failure review, but its v1 reader stopped at
a three-field schema mismatch; its 16.19-second charge and unavailable complete
arithmetic remain. A separately registered compatibility source passed 1086
tests and all applicable source/main CI. Its default planning wrapper then
failed native instrumentation inside the sandbox, retaining wall 4.73,
user 1.95/system 0.40 and unknown RSS. No registered recovery review or independent
arithmetic audit was invoked. Metadata/time accounting passed with 76.19 known
charge and 50.53/60 reserve use, preserving both failures and all source/hash
bindings. Whole-slice peak RSS, memory-cap compliance and full resource closure
remain unknown. B4.24 is not fully closed; B4.25 has not started. See
[the interrupted report](validation/b4_24_versioned_correctness_failure_review.md).

Resume requires an explicit separate resource/execution decision preserving
the failures, complete charges and missing RSS. No scientific criterion,
input, role, model or seal changed. B4.23/B4.20 failures and B4.19 unknowns
remain; no fit, learned repair, full memory acceptance or final access occurred.
Uniform remains default, P/17 unrepaired and all final/48 unused cases sealed.
