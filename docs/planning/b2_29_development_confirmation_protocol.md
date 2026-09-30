# B2.29 frozen larger independent development confirmation

Status: frozen before any B2.29 uniform reference or screen outcome.
Plan `topolab.b2_29.development_confirmation.v1` has canonical SHA-256
`5cc928fedfe5827dab3fb24b4203361e4ca866d9bc1203a054859d5e2c835590`.
This confirmation tests transfer of B2.28's bounded development pass
before B3. Uniform initialization remains the operational default.

## Fixed policies and source binding

Keep all three B2.28 expanded generalists, all three B2.26 old weighted
generalists, and the three shared B2.24 specialists unchanged. Use the
specialist only on mesh `(24,12,6)`, direction y, volume `>=0.55`;
otherwise use the panel's generalist. No fit, new epoch selection,
training data, route, blending, or reliability threshold is introduced.

Add the existing fixed physics heuristic and B2.4 train-only nearest
neighbor as non-ML comparators. The neighbor retains its original
ten-channel input-distance rule and exactly 468 B2.4 train labels,
partitioned by mesh shape; no validation or expanded label enters it.
Every opened checkpoint, selection history, and neighbor label byte is
verified through the existing readers. Bind exact source-index hashes:

```text
B2.4  data   dad9109aca6d4e14a851c266fd1b8a490885cf2565281ee85ceba1d164f59244
B2.24 fit    89bacfec6fbdfd2732ab74404626dc33a914b7cf788750f02276319b7e73700a
B2.26 fit    02b95a940de87cc8e9e5d8d297b619b461425bece0ca933a588b9072ce8a5c8e
B2.28 fit    0d874a0ea7c0c4f87740b1630033dc80418e44975f0c1e0a266f4f6fe553f402
B2.28 screen 55bfc7e74b2b5250e49b5beafcfbc5af844c9d2ec514edd02d2d0fdf088b2586
```

B2.28 checkpoint source revision remains
`d8e97010e94ce63d1939a4a1454746c68f7124e8`, bound to its original
plan `1e33936caedaa5702d14ffe3bbfa349211b44c170d13d9a0f3d4f0a90a865da0`.
Its seed `17/29/43` epochs remain `173/54/191`; no seed is dropped or
selected using this confirmation's outcomes.

## Larger independent cohort and ordered execution

Block all 922 earlier exposed or reserved physical case IDs and the
previous development/M2 and design-exposed M3 volume grids. Cross
unused volumes `0.3185,0.4565,0.5315,0.5895`, small-grid x-max nodes
`(y=1,z=1),(y=3,z=2),(y=5,z=1)`, negative unit point loads in y/z,
and meshes `(12,6,3)`/`(24,12,6)`. Double load-node indices on the
large grid and preserve material, x-min support, filter, and OC rules.
This gives **48** new cases, twelve per scale/direction stratum and
three per scale/direction/volume cell. Exactly three high-volume
large-y cases use the fixed specialist; the middle-volume large-y
cell has three cases and nine learned attempts per panel.

1. Run all 48 mandatory uniform references with the unchanged
   360-update physical-plateau policy. Require 48/48 convergence,
   positive finite compliance, independent final-state consistency,
   and physical-volume error `<=0.005`, in `<=7200 s` and `<=2 GiB`.
   Any failure stops before loading models or neighbor labels.
2. From the same clean merged revision, run a fresh timed uniform for
   each screen case and require compliance to agree with its mandatory
   reference within `rtol=1e-9,atol=0`. This timed uniform is the paired
   denominator. Then run physics heuristic, nearest neighbor, old
   seeds `17/29/43`, and expanded seeds `17/29/43` in that order.
   Retain all **432** ordered outcomes in `<=48000 s` and `<=2 GiB`.

Charge routing, encoding/inference or neighbor lookup, filtered-volume
projection, full refinement, terminal decision, and fresh uniform
fallback on every failed attempt. Failed attempts retain failure
status. Accepted attempts must converge, have independently checked
compliance `<=1.001` times paired uniform, and physical-volume error
`<=0.005`. Record separate one-time model/neighbor loading cost and
neighbor memory, include them in the screen stage's resource budget,
and report every phase and seed.

## Predeclared confirmation decision

Require complete case/method order, zero accepted quality violations,
and both resource Gates. At least **two** expanded seeds must each:

- Have arithmetic paired-time means `<=0.90` on both mesh scales and
  `<=1.0` in all four scale/direction strata.
- Have at most **two** total failed attempts with full fallback, no
  more total failures than its matched old seed, and no more
  non-specialist y failures than that old seed.
- Have its 48-case overall arithmetic paired-time mean **strictly
  below both** fixed non-ML comparator means, including their failures
  and fallback costs.

Across all three expanded seeds, require at least **6/9** successes
in the middle-volume large-y cell (`0.5315`) and **6/9** on the
high-volume large-y specialist cell (`0.5895`). This preserves
B2.28's two-thirds minimum while increasing each cell from two to
three independent positions. Report all three seeds even if one fails.
Do not change cases, thresholds, checkpoints, or solver after exposure.

Commit and merge the protocol/runner after CI, then run its read-only
plan and both stages from that clean merged revision with one CPU/BLAS
thread. Generated labels, indices, logs, summaries, and independent
audit code remain outside Git. M2 held-out/OOD and final evidence
remain sealed.

A pass permits the next slice **B3.1**, planning the separate versioned
ML contract and final exposure boundary. It does not pass Gate B3,
change the uniform default, or establish final acceleration. A failure
preserves the full negative result and leaves B3 closed; the next
bounded slice diagnoses the observed reference or confirmation failure.
