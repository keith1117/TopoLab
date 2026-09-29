# B2.26 frozen y-weighted terminal generalist

Status: frozen before any B2.26 reference, fit, or screen outcome.
Canonical `topolab.b2_26.weighted_generalist.v1` plan SHA-256:
`bd6b355036024c2bbd31b09a62d4141d868afae526025f4e395c2abe97440a4c`.
This is a bounded development experiment, not an acceleration claim. A
positive screen requires separately frozen development confirmation before
B3.

## One generalist training intervention

B2.25 found residual y quality failures on both mesh scales and costly
large-z refinement outside B2.24's repaired high-volume large-y route.
Starting from the **B2.21 terminal-target generalist**, change only
the training-case weights: use case weight `8` for the 78 existing
train cases with y-direction load and volume fraction `>=0.5`, and `1`
for the other 390. This extends the already implemented case-weighted
loss idea to the lower-volume large-y and small-y regimes exposed by
B2.25. Keep B2.21's 468 B2.4 train cases, twelve independently audited
B2.21 validation terminal designs, thirteen-channel input, 26,433-
parameter context CNN, terminal-design target, AdamW schedule, seeds
`17,29,43`, shape-bucketed batch size 8, 200-epoch maximum, 25-epoch
patience, and earliest strict minimum **unweighted** MSE over all twelve
validation cases. No B2.23 position label enters this generalist fit.

Bind B2.4 development data-index SHA-256
`dad9109aca6d4e14a851c266fd1b8a490885cf2565281ee85ceba1d164f59244`,
B2.21 validation-target index SHA-256
`3e7add2c85650bcb5ac0329236678887baaf2fc3acd4882a1f8f8fc7070796ab`
and unweighted fit index SHA-256
`a997e1f69703126b4c0fdf7f2c87363f3fb6093c3970ab383f8765e60d2149d5`.
Read and verify each opened label, validation target, checkpoint, and
fit history byte. Fit all three seeds within `<=7200 s` and `<=2 GiB`.

## Fixed route, fresh cohort, and ordered Gates

For each method, use the **same unchanged B2.24 expanded specialist**
on `(24,12,6)` y cases at volume `>=0.55`; otherwise use the method's
matched generalist. The operational control uses the B2.12 context
checkpoint, the terminal control uses the B2.21 unweighted terminal
checkpoint, and the intervention uses the B2.26 weighted terminal
checkpoint. Bind B2.24 specialist fit-index SHA-256
`89bacfec6fbdfd2732ab74404626dc33a914b7cf788750f02276319b7e73700a`,
screen-index SHA-256
`e77ad2eb6670dcae64e14c51d67b4b6ad6dc05d2d8e57448be39c8c584db1075`,
and B2.12 context fit-index SHA-256
`0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce`.

Block all 814 earlier exposed or reserved B2.24 physical case IDs,
plus the prior development, M2 catalog, and design-exposed M3 v1
volume grid. Freeze 24 fresh 360-update cases at unused volumes
`0.3725,0.5225,0.5955`, small-grid x-max load positions `(y=1,z=2)`
and `(y=4,z=1)` (doubled on the large grid), directions y/z, and
meshes `(12,6,3)` and `(24,12,6)`. Each scale/direction stratum has
six cases; exactly two high-volume large-y cases use the unchanged
specialist. No new screen case selects a weight, epoch, route, or
threshold.

1. Obtain 24/24 independently quality-checked uniform references in
   `<=3600 s` and `<=2 GiB`. A failed reference stops before fitting.
2. Fit all three weighted seeds within the limits above, preserving
   selected epochs, checkpoint/history hashes, and fit timing.
3. Screen ten methods per case: matched uniform, three operational,
   three unweighted-terminal, and three weighted-terminal routed
   candidates. Retain all 240 fully charged outcomes within `<=24000 s`
   and `<=2 GiB`.

Every learned attempt pays route, input encoding, inference,
filtered-volume projection, 360-update physical-plateau SIMP
refinement, terminal quality decision, and a complete fresh uniform
fallback on failure. A failed attempt remains failed. An accepted
attempt must converge, have independently checked compliance
`<=1.001` times matched uniform, and physical-volume error `<=0.005`.
Accepted quality violations must be zero.

The development Gate requires at least two weighted seeds with fully
charged arithmetic paired mean time ratios `<=0.90` on **both** mesh
scales and `<=1.0` on each scale/direction stratum. Each such seed
must have no more total failed attempts than its operational control,
at most two non-specialist y failures, and no more non-specialist y
failures than its unweighted-terminal control. At least four of six
weighted high-volume large-y attempts must pass terminal quality.
Report every method, seed, quality status, phase cost, and subgroup
mean even if the Gate fails. No change to the quality or speed limits
is allowed after observing the fresh screen.

Run the read-only plan and each stage from one clean committed revision
with one CPU/BLAS thread. All generated references, weights, histories,
outcomes, logs, and independent audit code stay outside Git. M2
held-out/OOD and final cases remain sealed. Uniform initialization
remains the operational default until later Gates pass.
