# B2.8 frozen y-load basin recentering and fresh development screen

Status: frozen before any B2.8 screen outcome. This is one development-only
initialization intervention, not a final ML acceleration claim. Read-only plan
version `topolab.b2_8.basin_recenter.v1` has canonical SHA-256
`6b74219b8411da034e1794c2184efc84d07d9260160c6df625f73147c5c24357`.

## Measured cause and one correction

B2.7's global-load model improved two seeds, but every seed missed a `y`
direction speed bound. All three failed quality on small `y/0.2375`; the two
stronger seeds also needed more updates than uniform on large `y/0.3875`.
Six of seven new failures had stopped but missed the matched-uniform
compliance bound. This indicates a prediction-to-solver-basin risk, although
the exposed screen cannot prove a unique cause. B2.7 screen outcomes are not
used to tune the correction.

Keep the exact three audited B2.7 checkpoints, global-load encoding, inference,
filtered-volume projection, 240-update physical-plateau solver, independent
quality checks, and full fresh uniform fallback. Make **one opt-in change** to
the candidate's raw design density before projection. For a `y` point load,
set `raw_B28 = 0.5 * raw_B27 + 0.5 * volume_fraction` elementwise. For a `z`
point load, copy `raw_B27` exactly. Both weights are fixed before the screen;
there is no learned threshold, retraining, seed choice, or case-specific
adjustment. This midpoint is an unproven hypothesis: it retains some learned
structure while moving `y` starts toward the known uniform initialization
basin. It could also lose useful structure and fail the speed Gate. Version it
as `topolab.b2_8.y_midpoint_start.v1`. Charge its work in candidate setup.
Historical B2.7 and default M1/M2 behavior remain unchanged. No numerical
tolerance, solver, budget, mesh, or fallback semantics change.

## Exposure and complete screen

The input checkpoints are the complete B2.7 fit index SHA-256
`36158e03a476fdff183d8c72cf0e7143700e7bac3ccc531d7eda485ec390a631`.
Re-read its three selections and checkpoints with their identities and hashes.
The historical B2.5 control fit index is
`a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53`;
control-43 checkpoint SHA-256 is
`d82b7895355c1f73cde5b80d6328bc31c43c58cd7b1580974a590ef42bce0f4d`.
Use only the frozen B2.4 training cohort for nearest-neighbor indexing. All
B2.6/B2.7 fit, selection, and screen cases are development-exposed. No M2
test/OOD label or outcome or M3 v1 final label or outcome is opened.

Freeze 12 **new, disjoint** cases before execution: volumes `0.2125, 0.3625,
0.5125`; directions `y/z`; small mesh `(12,6,3)` and physically matched
double mesh `(24,12,6)`; one fixed x-min support and one point load at the
small-mesh node `(x=max,y=3,z=2)`, doubled on the large mesh. These volumes
are absent from the B2.4/M2 and design-exposed M3 v1 catalogs and all earlier
B2.6/B2.7 screens. Every scale/direction/volume stratum occurs once. The
small/large material, dimensions, filter, OC settings, and maximum 240 updates
match B2.7. Retain every case regardless of outcome.

For each case in sorted ID order, run exactly eleven methods: fresh uniform,
physics heuristic, B2.4 training-only nearest neighbor, historical B2.5
control seed 43, the three unchanged B2.7 conditioned models, the three B2.8
recentered starts, and an impossible true own-trajectory oracle. The oracle
receives the true update-30 state only after solving that screen case; report
its generation separately and never count it as deployable. The B2.7 model
control on these same fresh cases isolates the recentering effect.

Every candidate pays input encoding, inference, transformation, filtered-volume
projection, complete refinement, and independent quality decision. Reject
nonconvergence, nonfinite or inconsistent compliance, physical-volume error
`>0.005`, or final compliance `>1.001` times the matched uniform reference.
An unsuccessful attempt keeps failure status and pays a fresh complete uniform
fallback. Preserve all eleven outcomes per case atomically. On interruption,
rerun the incomplete case and retain prior complete rows. Record phase costs,
iterations, quality, failures, fallback, all strata, and resource use.

The **B2.8 development feasibility Gate** uses only the three recentered
starts. At least two must have fallback-inclusive arithmetic mean paired time
ratio `<=0.90` on each scale and `<=1.0` in each scale/direction stratum. It
also requires zero accepted quality violations, all 12 cases and 132 method
outcomes, wall time `<=14,400 s`, and peak RSS `<=2 GiB`. Retain the three
unchanged B2.7 controls to show whether any benefit comes from the correction
on the same cases. A passing small development screen would require a separate
larger confirmation before B3. A failed Gate leads to a newly versioned,
diagnosed intervention; no final acceleration or delivery claim follows.

Run a read-only plan first, then execute from a clean committed revision with
single-thread CPU/BLAS settings and checksum-addressed external artifacts.
Never commit data, checkpoints, or run results. Report the prior B2.6 target
and B2.7 fitting costs separately from this no-fit screen.
