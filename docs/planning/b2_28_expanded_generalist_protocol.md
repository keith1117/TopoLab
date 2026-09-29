# B2.28 frozen middle-volume generalist expansion

Status: frozen before any B2.28 reference, fit, or screen outcome.
Canonical `topolab.b2_28.expanded_generalist.v1` plan SHA-256:
`1e33936caedaa5702d14ffe3bbfa349211b44c170d13d9a0f3d4f0a90a865da0`.
This bounded development experiment requires separate confirmation before B3.

## One training-data intervention

B2.26's residual failures clustered at middle-volume y cases, and large-z
refinement varied across seeds. B2.27 passed the unchanged-quality data Gate
for new middle-volume large-grid y/z position labels. Add exactly its 40
train terminal-design labels to B2.26's 468-case weighted generalist fit.
The resulting 508-case population contains 432 small and 76 large cases,
forming 64 shape-bucketed batches of at most eight cases per epoch.

Keep B2.26's rule: weight `8` for y train cases at volume `>=0.5`, `1`
elsewhere. There are 98 weighted and 410 other cases. Keep the terminal
design target, thirteen-channel vector-load input, 26,433-parameter context
CNN, AdamW schedule, seeds `17,29,43`, 200-epoch cap, 25-epoch patience, and
earliest strict minimum unweighted MSE on the unchanged twelve B2.21
validation targets. The new 20 B2.27 validation labels are diagnostic
targets only: report selected-checkpoint MSE separately for their ten y and
ten z cases for both old and new models. They do not select an epoch,
weight, route, or threshold.

Bind these exact source-index SHA-256 values and verify every opened
label, target, checkpoint, and history byte:

```text
B2.4  data       dad9109aca6d4e14a851c266fd1b8a490885cf2565281ee85ceba1d164f59244
B2.21 targets    3e7add2c85650bcb5ac0329236678887baaf2fc3acd4882a1f8f8fc7070796ab
B2.24 fit        89bacfec6fbdfd2732ab74404626dc33a914b7cf788750f02276319b7e73700a
B2.24 screen     e77ad2eb6670dcae64e14c51d67b4b6ad6dc05d2d8e57448be39c8c584db1075
B2.26 fit        02b95a940de87cc8e9e5d8d297b619b461425bece0ca933a588b9072ce8a5c8e
B2.26 screen     05fa1f1e825060b144db0cbab728dfe98e3785594fce42ff7aad85e26813307a
B2.27 labels     aa422ab98f9ca102c55cea991ff679b6b5b703abcb4b5456424fbb8878ca1d35
```

B2.27 labels retain source revision
`1c26baf77b603af83505582adefe447d8f370618` and their 40/20 split.
No B2.23 label enters the generalist fit. All fits must complete within
`<=7200 s` and `<=2 GiB` peak RSS.

## Fixed route, fresh cases, and ordered Gates

Both panels reuse the unchanged B2.24 specialist on `(24,12,6)` y cases
at volume `>=0.55`. Elsewhere use matched B2.26 old weighted generalists
or the new B2.28 expanded generalists. The route and quality rules remain
fixed.

Block all 898 earlier exposed or reserved physical case IDs and the prior
development, M2, and design-exposed M3 volume grids. Freeze 24 fresh
360-update cases at unused volumes `0.3745,0.5295,0.5935`, small-grid
x-max positions `(y=2,z=2)` and `(y=5,z=1)`, doubled on the large grid,
directions y/z, and meshes `(12,6,3)` and `(24,12,6)`. Each scale/direction
stratum has six cases. Exactly two high-volume large-y cases invoke the
fixed specialist. No screen outcome selects training or routing settings.

1. Obtain 24/24 independently quality-checked uniform references in
   `<=3600 s` and `<=2 GiB`; failure stops before fitting.
2. Fit all three new seeds and audit all 20 diagnostic labels within
   the fitting resource limits above.
3. Retain all 168 outcomes: uniform plus three old and three expanded
   routed attempts per case, in `<=24000 s` and `<=2 GiB`.

Charge routing, encoding, inference, filtered-volume projection, full
360-update physical-plateau refinement, terminal quality decision, and
complete fresh uniform fallback on failure. Failed attempts retain failure
status. Accepted attempts must converge, have independently checked
compliance `<=1.001` times matched uniform, and physical-volume error
`<=0.005`; accepted quality violations must be zero.

Require at least two expanded seeds with charged arithmetic paired means
`<=0.90` on both mesh scales and `<=1.0` in every scale/direction stratum.
Each eligible seed must have no more total failures than its matched old
seed, at most two non-specialist y failures, and no more such failures
than its old seed. Across the three new seeds require at least four of
six successes on the middle-volume large-y cases and four of six on the
high-volume large-y specialist cases. Report every case and seed even if
the Gate fails. Do not alter any threshold after opening outcomes.

Commit and merge the protocol/runner after CI, then run the read-only plan
and all stages from one clean merged revision with one CPU/BLAS thread.
Generated labels, weights, indices, histories, outcomes, logs, and audit
code stay outside Git. M2 held-out/OOD and final evidence remain sealed;
uniform initialization remains the operational default.
