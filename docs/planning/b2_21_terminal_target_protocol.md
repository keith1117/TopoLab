# B2.21 frozen terminal-design target intervention

Status: frozen before new B2.21 reference, validation-target, fit, or screen
outcomes. Canonical `topolab.b2_21.terminal_target.v1` plan SHA-256:
`3f5fadd4945cb0d6fbae2739cbc477244d0b7a52e657d58eb7ce5d4ffc2edaf2`.
This is development-only evidence. A small-screen pass does not open B3.

## One learning-side intervention

B2.20's operational checkpoint selection retained all six high-volume
large-y terminal-quality failures. Replace the B2.12 context CNN's
**uniform update-30 design-density target** with the audited **uniform
terminal design-density target**. The 13-channel vector-load encoding,
26,433-parameter context CNN, unweighted elementwise MSE, 468/12
training/validation case definitions, three seeds `17,29,43`, AdamW,
shape-bucketed batch schedule, 200-epoch maximum, 25-epoch patience,
earliest strict minimum validation MSE selection, filtered-volume
projection, SIMP solver, and complete fallback charging are unchanged.
This tests whether teaching the final quality basin directly repairs
the intermediate-target mismatch. B2.5 previously tested terminal
labels with a smaller model and earlier input; its negative result
remains intact.

Use only the 468 `train` B2.4 budget-240 terminal labels from the complete,
audited B2.4 data index SHA-256
`dad9109aca6d4e14a851c266fd1b8a490885cf2565281ee85ceba1d164f59244`.
Verify every artifact byte checksum, case ID, split, source revision, and
stored density before fitting. The unchanged twelve B2.6 validation
case definitions have no B2.4 terminal labels, so generate their twelve
uniform terminal designs under the same 240-update physical-plateau
solver, require convergence and independent final compliance/volume
quality, persist CPU float32 tensors with case/context/checksum binding,
and use them only for validation MSE. Stop before fitting if any of the
twelve fails. Require `<=1800 s` and `<2 GiB` for this stage. Complete
all three fits in `<=7200 s` and `<2 GiB`.

## Exposure and screen

Bind the B2.20 screen-index SHA-256
`a8b3fce38f6db4017db582e04a21c0559b270e6787fb4190cc1f15afe6b834ce`.
The exposure ledger includes its 12 selection and 24 screen cases and
all earlier exposed/reserved identities: 712 blocked physical case IDs.
Exclude the prior development, M2 catalog, and design-exposed M3 v1
volumes. Freeze 24 new cases at volumes `0.3575,0.5075,0.5915`, `y/z`
point-load directions, small `(12,6,3)` and large `(24,12,6)` meshes,
and two small-grid x-max positions `(y=2,z=2)` and `(y=5,z=1)` with
physical doubling on the large mesh. Their solver case IDs use the
unchanged 360-update B2.11 physical-plateau policy. These cases are
disjoint from training, MSE validation, prior exposure, and final
evidence.

First obtain 24/24 independent uniform references, positive finite
compliance, independent final quality, and physical-volume error
`<=0.005`, within `<=3600 s` and `<2 GiB`. Stop before target generation
or fitting if any fails. After the three fits, evaluate seven methods
per new case: matched uniform, three unchanged B2.12 MSE-selected
context controls, then three B2.21 terminal-target checkpoints. Retain
all 168 outcomes within `<=16000 s` and `<2 GiB`.

Every learned query pays input encoding, inference, filtered-volume
projection, full 360-update SIMP refinement, terminal quality decision,
and a complete fresh uniform fallback on failure. A failed learned
attempt remains failed after fallback. Require solver convergence,
compliance `<=1.001` times matched uniform, and physical-volume error
`<=0.005`; accepted quality violations must be zero.

The development Gate requires at least two B2.21 seeds to have fully
charged arithmetic mean ratios `<=0.90` on **both** mesh scales and
`<=1.0` on each of the four scale/direction strata, with no more
terminal failures than the paired B2.12 control. At least four of the
six new-model attempts on the two high-volume large-y cases must pass
terminal quality. Report all seeds and controls even if this Gate fails.
A pass permits only a separately frozen, larger development confirmation
before B3.

Run the read-only plan and all stages from one clean committed source
revision with one CPU/BLAS thread. All generated references, targets,
weights, histories, outcomes, logs, and independent audit artifacts
stay outside Git. M2 held-out/OOD and new final evidence remain sealed.
Failure ends this exact terminal-target method; do not retune target
mixtures, epochs, case volumes, quality limits, or speed thresholds on
its exposed screen.
