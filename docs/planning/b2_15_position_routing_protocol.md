# B2.15 frozen position-aware routing and safe rejection

Status: frozen before any B2.15 reference or learned outcome. This is one
development-only query policy intervention over already audited checkpoints,
not a new fit, solver change, or final acceleration test. Plan version
`topolab.b2_15.position_routing.v1` has canonical SHA-256
`edeab8ca4cc1f059984ebbe84917991e9aef76fffd8ac47e226cbd8965c3b8b8`.

## Hypothesis and fixed policy

B2.14 found that the old vector route paid a small-y quality fallback and
was slow at lower-z large-z load positions, while context 43 solved those
observed positions. Context 17 was faster on most large-y positions but
failed quality at high volume and lower z. Freeze this one metadata-only
policy before opening new cases:

| Mesh, direction, position | Volume | Decision |
|---|---:|---|
| Small, y or z, any interior free-end load node | 0.30–0.61 | Context seed 43 |
| Large, y, lower z third | At least 0.55 | Fresh uniform rejection |
| Large, y, other supported position | 0.30–0.61 | Context seed 17 |
| Large, z, lower z third | Below 0.55 | Context seed 43 |
| Large, z, other supported position | 0.30–0.61 | Vector seed 29 |

Only public mesh, material, support, load position/direction, solver-budget,
and volume metadata may influence the route. Unsupported metadata rejects to
fresh uniform. The numerical solver, 360-update physical-plateau policy,
filtered-volume projection, independent quality bounds, and full fresh
uniform fallback after a failed learned attempt remain unchanged. Every
decision, setup, inference, projection, refinement, quality check, rejection,
and fallback is charged. Model loading is reported separately.

The fixed B2.9 and B2.12 fit-index SHA-256 values are
`96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3`
and `0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce`.
The exposed B2.12, B2.13, and B2.14 screen-index SHA-256 values are
`cb671b2e9b5194606964faed0c6022c4a9a181b978827f906bfe416f72516443`,
`183e3448a9d7e3e82de6ed4dd3f38e5184977b7243aa9edd13284f950f8d3de0`,
and `2c2bb58c40bf1e2099fd21ecf3cc74a5425ca3f1ad28ac183611c1535bb4e6c9`.
Verify the source indices, six selected checkpoints, and selection histories
before screening. Previous outcomes are diagnosis only.

## Fresh development evidence

Cross volumes `0.3175, 0.4675, 0.5825`, small-mesh free-end load nodes
`(x=max,y=2,z=1)` and `(x=max,y=4,z=2)`, y/z negative unit directions, and
`(12,6,3)`/`(24,12,6)` element meshes with physically doubled large-mesh
load-node indices: **24** cases, two per scale/direction/volume cell. Use
fixed x-min support and all existing material/filter/OC settings. All case
IDs and volumes are absent from the 612-case prior development exposure
ledger and the design-exposed M3 v1 final volume definitions. M2 test/OOD
and any new final outcomes remain sealed.

Run all 24 fresh uniform references before loading a learned model. Require
24/24 convergence, positive finite compliance, independent final-state
check, and physical-volume error `<=0.005`. Retain any failure and stop the
learned screen if the reference Gate fails. Reference cap: 3,600 s and 2 GiB
peak RSS.

The screen runs a new timed uniform per case, then physics heuristic,
B2.4 train-only nearest neighbor, vector 29, context 17, context 43,
unchanged B2.13 route, and the new B2.15 route: **192** ordered outcomes.
Persist each complete case atomically. A failed learned attempt retains its
failure status and pays a full fresh uniform fallback; a policy rejection
is recorded separately and pays fresh uniform work. Screen cap: 10,800 s
and 2 GiB peak RSS. Run the read-only plan, references, and screen from one
clean committed revision with one CPU/BLAS thread. Generated plans, indices,
summaries, and logs stay outside Git.

## Bounded development Gate

Require all 24 references, all 24 screen cases and 192 outcomes, zero
accepted compliance/convergence/volume violations, and both resource caps.
The new route must have at most two failed learned attempts, an arithmetic
mean fallback/rejection-inclusive paired time ratio `<=0.90` at each scale,
and a mean `<=1.0` in each of four scale/direction strata. It must have an
overall mean **strictly below** 0.95 times the unchanged old route's mean.

Evaluate the three fixed checkpoint policies by the same quality, failure,
scale, and direction rules. If any fixed policy is eligible, choose the
lowest overall mean (tie order vector 29, context 17, context 43). The new
route must then have an overall mean strictly below 0.95 times that fixed
policy and no more failed attempts. It must also beat both non-ML comparators
on overall mean. No case, seed, or comparator may be dropped; the paired
ratio is computed case by case before averaging.

A pass is only a development feasibility result. It requires a separately
frozen, larger development confirmation before B3; it does not change the
operational uniform default or establish an acceleration claim. A failure
retains every outcome, closes B3, and triggers a method-class reassessment
instead of an unbounded local routing search. Independently audit exposure,
hashes, quality, full time charges, and the Gate from persisted artifacts.
