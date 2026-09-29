# B2.25 frozen residual quality and cost diagnosis

Status: frozen before reading B2.24 result bytes for this diagnosis. The
canonical `topolab.b2_25.residual_cost.v1` plan SHA-256 is
`11a03776d87828c0100381d6276a515b72dd4f59c311eeb67963f507e69a2cc0`.
This is a read-only development diagnosis, not a learned acceleration Gate.

## Fixed source and integrity boundary

Read only B2.24's 24 exposed, physically disjoint development cases and
their seven methods (uniform, three old routed specialists, three expanded
routed specialists). Bind B2.24 plan
`50230a66db17c26ed4665bce41142c61b3e5ffc5f2dcfb83988d77d84884dd94`
and source revision `dd110b8067acccdcc900709a20809c924b7fbbc8`.
Require exact SHA-256 of its reference, fit, and screen indices:

```text
reference c3703ab52820f618f3ec664a4a515432d5e95bb3c6d8464210b6003d24935eb7
fit       89bacfec6fbdfd2732ab74404626dc33a914b7cf788750f02276319b7e73700a
screen    e77ad2eb6670dcae64e14c51d67b4b6ad6dc05d2d8e57448be39c8c584db1075
```

Reconstruct the ordered B2.24 case identities from its fixed cohort
definition. Verify 24 references, three fit records, and all 168 ordered
screen outcomes, context links, resource caps, phase sums, paired uniform
denominators, routes, terminal quality, and complete charged fallback.
Summarize expanded failures by scale, direction, volume, compliance ratio,
candidate iterations, and fallback seconds. Summarize mean refinement and
fallback seconds plus candidate/uniform iterations by scale and direction.
The old routed seeds remain matched measured controls.

## Three optimistic speed-only bounds and ordered decision

For every expanded seed, retain the same 24 cases and arithmetic paired
time-ratio means. Compute the measured result, then these hypothetical lower
times using each case's own uniform denominator:

1. **Fallback-free:** subtract recorded fallback seconds from a failed
   attempt's total, leaving its failed candidate cost.
2. **Large-z zero:** set the entire expanded time on each six-case large-z
   stratum to zero, leaving all other charged cases unchanged.
3. **Combined:** subtract fallback seconds and set all large-z times to
   zero.

These bounds leave the recorded failure status intact. They are deliberately
optimistic cost limits, not quality-feasible methods or acceleration claims.
For each bound, ask how many of seeds `17,29,43` satisfy both scale means
`<=0.90` and all four scale/direction means `<=1.0`. Select one next
mechanism in this order: at least two seeds under fallback-free means y
reliability; otherwise at least two under large-z zero means z refinement;
otherwise at least two under combined means one joint non-specialist
large-grid mechanism while keeping the expanded high-volume y specialist
fixed; otherwise reassess the method class. A selected mechanism requires a
separately frozen fresh development experiment before any B3 decision.

Run the read-only plan and diagnosis from a clean committed revision with
one CPU/BLAS thread; limit diagnosis to `<=60 s` and `<=1 GiB` peak RSS.
Write only an external canonical JSON report. No fitting, solver call,
route/threshold search, new case, or M2 held-out/OOD/final exposure is
allowed. Uniform initialization remains the operational default.
