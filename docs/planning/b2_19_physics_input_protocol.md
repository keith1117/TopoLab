# B2.19 frozen physical-input repair

Status: frozen before any B2.19 reference, fit, or new-case outcome.
The canonical `topolab.b2_19.physics_input.v1` plan SHA-256 is
`e75e3eb9796729d9ef9921b617ca28783f5c96762a6a5b8acc95389bb0e6d664`.
This is development evidence only; B3 remains closed.

## Single learning-side intervention

B2.17's early uniform comparison missed three terminal failures. B2.18's
two-update blend improved compliance slightly yet left all three failed.
Supply the model with a physical field that marks where the initial
uniform structure carries strain energy. At each training and query case,
run exactly one linear FEM solve at uniform density equal to the requested
volume fraction. Compute the negative physical-density SIMP compliance
derivative per element. Divide by its positive mean, apply `log1p`, and
divide by the maximum transformed value. Append the resulting `[0,1]`
spatial field as channel 14 to the unchanged B2.9 vector-load input. The
normalization is fixed per case and is not fitted to screen results.

Keep the B2.12 four-convolution shape/dilations/width and sigmoid head;
only the first layer admits one extra channel, yielding 26,865 trainable
parameters. Keep the same 468 training and 12 selection cases, 480 audited
B2.6 update-30 design targets, unweighted elementwise MSE, AdamW schedule,
seeds `17,29,43`, 200-epoch maximum, 25-epoch patience, and earliest strict
validation minimum. The B2.6 target-index SHA-256 is
`5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf`.
The fixed B2.12 control fit-index SHA-256 is
`0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce`.
Audit source targets, checkpoint bytes, and selection histories. Complete
feature encoding and all three fits in `<=7200 s` and `<=2 GiB` peak RSS.
Keep generated inputs, weights, and indices outside Git.

## Fresh cases and reference stop

Freeze twelve new cases: volumes `0.3375,0.4875,0.5795`, load directions
`y,z`, both `(12,6,3)` and `(24,12,6)` meshes, and x-max point load at
small-grid `(y=1,z=2)` with physically doubled large-grid position.
These volumes and case IDs exclude all previous exposed development
cases, the unopened B2.17 and B2.18 reservations, M2 catalog volumes,
and design-exposed M3 v1 volumes. The old exposure ledger contains 664
case identities including reservations. No final or M2 held-out outcome
is opened.

Use 360 SIMP updates and unchanged physical-plateau, projection, OC,
filter, material, solver, and independent terminal checks. Before fitting,
complete twelve uniform references. Require 12/12 convergence,
finite positive final compliance, and physical-volume error `<=0.005`
within `<=1800 s` and `<=2 GiB`; retain any failed reference and stop.

## Fully charged matched screen

On every case, retain seven outcomes in order: the saved matched uniform
reference; unchanged B2.12 context seeds `17,29,43`; new physical-input
seeds `17,29,43`. Use the saved reference's end-to-end time as the paired
denominator, as in B2.12. Every physical-feature FEM solve is charged to
the corresponding attempt's setup time. Project the model's output, run
full 360-update refinement, and independently require convergence,
compliance `<=1.001` times matched uniform, and physical-volume error
`<=0.005`. A failed attempt remains failed and pays a separate complete
uniform fallback. Retain all 84 outcomes, phase times, paired ratios,
candidate metrics, and fallback records within `<=8000 s` and `<=2 GiB`.

The development Gate requires complete references, three audited fits,
twelve complete screens, zero accepted quality violations, and all
resource caps. At least two new seeds must each attain arithmetic mean
fully charged ratios `<=0.90` on **both** mesh scales, `<=1.0` in each
scale/direction stratum, and no more terminal failures than their paired
B2.12 control seed. At least two new seeds must pass terminal quality on
the high-volume large-y case. Report all seeds and the paired control
results even if the Gate fails; do not retune the normalization, target,
case list, thresholds, or model using those results.

Run the plan, references, fits, and screen from a clean committed revision
with one CPU/BLAS thread. A pass still requires a separately frozen larger
development confirmation before B3 and cannot establish final
acceleration. A failure ends this one input intervention and informs the
next independent slice.
