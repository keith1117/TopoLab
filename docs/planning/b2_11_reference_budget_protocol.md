# B2.11 versioned reference-budget repair and fixed-model confirmation

Status: frozen before B2.11 numerical execution. This is one development-only
**iteration-budget** change. The read-only plan version is
`topolab.b2_11.reference_budget.v1`; its canonical SHA-256 is
`8cbd77c8fdace2ef12512a6aa001e94152e2fc60b1fd9b4375d4c6f1e5af610a`.
It cannot establish final v2 acceleration by itself.

## Diagnosis and one numerical intervention

B2.10's frozen screen stopped at the tenth case, large `z/0.2875`, because
the mandatory uniform reference had not converged at the 240-update cap.
It had finite compliance and volume; repeating the 240-update run reproduced
the failure. A separate development-only, new-identity 360-update run
converged at update 282 without changing the solver's stop rules. This
supports testing one fixed ceiling of **360 updates** for every compared
B2.11 case. Do not relabel the B2.10 failure or choose a case-specific cap.

Keep `topolab.simp.physical_plateau.v1`, the `0.01` design/physical-density
scale, ten-step `0.0002` compliance bound, OC update, filter, stiffness,
load, material, and all independent quality tolerances unchanged. Change
only `optimization.max_iterations` from 240 to 360. Since this field is in
the content-derived physical-case identity, construct new cases and retain
the 240-update source IDs beside them. No B2.6 target, B2.9/B2.10 fit,
checkpoint, or historical result is rewritten. This policy is opt-in for
development comparison; the public solver default stays unchanged.

## Two reference-feasibility stages before learned screening

First map **all twelve** B2.10 screen cases to 360-update identities and
run both source-240 and repaired-360 uniform attempts once, in source-ID
order. Keep the formerly failed large `z/0.2875` case. Require the old run
to fail at 240 and its repaired run to pass after 240 and by 360. Require
the other eleven old/new pairs to pass at the same stop iteration and final
compliance within relative `1e-10`. Independently require finite positive
final compliance, filtered physical-volume error `<=0.005`, and the solver's
unchanged convergence/terminal-state checks for every repaired run. Store
only metadata, timing, and outcomes outside Git. The full sentinel has an
1,800 s wall and 2 GiB peak-RSS cap; every pair remains in the denominator.

Freeze a **fresh, physically disjoint** twelve-case development screen before
either stage runs: volumes `0.2975, 0.4475, 0.5975`; y/z point-load
directions; `(12,6,3)` and `(24,12,6)` meshes; fixed x-min support; and one
small-mesh point load at `(x=max,y=3,z=2)` with its physically matched
doubled node. Cross scale, direction, and volume once each. These volumes
are absent from the B2.4/M2, design-exposed M3 v1, and B2.6–B2.10 catalogs;
check exact case IDs against the 540 exposed development IDs. Apply the
same 360 cap to every new case and method. No M2 test/OOD or M3 final
label/outcome is opened.

Before loading a learned model, independently run and retain all twelve new
uniform references. Require 12/12 to pass unchanged convergence, finite
positive compliance, and physical-volume error `<=0.005`; record failed
references rather than dropping them. This separate feasibility stage has
an 1,800 s wall and 2 GiB peak-RSS cap. If either reference stage fails,
stop without learned screening and record the failed B2.11 Gate.

## Unchanged-model screen and Gate

If both reference stages pass, run eleven methods on each new case: fresh
uniform, physics heuristic, B2.4 training-only nearest neighbor, B2.5
control seed 43, the three unchanged B2.9 vector models, the three unchanged
B2.10 weighted models, and an impossible own-trajectory oracle. The exact
B2.9 and B2.10 fit-index SHA-256 values are
`96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`
and `0d2138bfdcfc4f9d730c6261bccc1ce8bf2ddda2f50a70f5e5e0958b5fcc1851`.
Retain B2.10's failed partial screen with SHA-256
`a5a538f580e0ab03185e6d2c58d207a85f8c33ca7c77d7c5a56c0b196df6ceae`
as exposure provenance only. No fitting, selection, threshold tuning, or
screen-result feedback changes either fixed model panel.

All methods use unchanged filtered-volume projection, full refinement,
independent quality re-solve, physical-volume error `<=0.005`, and final
compliance `<=1.001` times the matched fresh uniform. A rejected candidate
stays failed and pays full attempt plus fresh complete uniform fallback.
Atomically retain all eleven outcomes per case. Record every case, seed,
direction, volume, scale, numerical result, phase time, fallback, oracle
generation cost, and resource. The complete screen cap is 14,400 s and
2 GiB peak RSS. Prior target generation, weight generation, and both model
fits are separately reported offline costs, never hidden in query time.

The **B2.11 development feasibility Gate** requires both full reference
stages, all 12 screen cases and 132 outcomes, zero accepted quality
violations, and every resource cap. Evaluate the B2.9 and B2.10 panels
separately: a panel passes only if at least two of its three fixed seeds
have fallback-inclusive arithmetic mean paired time ratio `<=0.90` at each
mesh scale and `<=1.0` in every scale/direction stratum. Do not combine
favorable seeds across panels. A passing panel is still development-only
and requires a separately frozen larger confirmation before B3. A failed
Gate requires a newly diagnosed intervention; it never permits a final
acceleration or v2 delivery claim. Inspect whether any apparent ratio gain
is driven primarily by a slow new uniform denominator.

Run a read-only plan, then sentinel, reference-feasibility, and learned
screen stages from one clean committed revision in a single-thread CPU/BLAS
environment. Keep all generated indices, outcomes, and logs outside Git.
