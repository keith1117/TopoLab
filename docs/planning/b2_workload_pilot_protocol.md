# B2 development-only workload pilot protocol

Status: fixed before timed execution. This is a diagnostic protocol, not a new
ML experiment registration or a final-evidence cohort.

## Repeated-query task and cohort

The candidate task is repeated topology design for one fixed-root cantilever
domain, with independently chosen point-load location, load direction, and target
volume per query. The support is all three displacement components at `x=min`.
The material is `E0=1000`, `Emin=1`, `nu=0.3`. Both meshes span the same
`12 x 6 x 3` physical domain, so refinement changes resolution rather than
geometry. The lower scale is `12 x 6 x 3` Hex8 elements (216); the higher scale
is `24 x 12 x 6` (1,728). Load magnitude is `-1` in either `y` or `z` at a
point on `x=max`. The filter radius is 1.5 physical units; penalty 3,
minimum density 0.05, move limit 0.2, density-change tolerance 0.01, and
maximum 120 iterations are held equal at both scales. The A3 `auto` sparse
ordering applies to **every** method's solve.

The lower-scale definitions come only from the 36 development-exposed M2
validation cases. For each of the six prechosen `(volume, direction)` strata
`{0.20, 0.45, 0.60} × {y, z}`, take the lexicographically first validation
case ID. The other validation case is unused. Double each element count and
loaded-node grid index to obtain the higher-scale case at the same physical
position. These six pairs are immutable for this pilot; no case is removed after
its result is seen. The `0.45` stratum deliberately includes the prior
convergence difficulty. All twelve content-derived case IDs appear in the
read-only CLI plan.

No M2 label artifact is opened. The six existing validation case definitions
are development information. The large cases are newly development-exposed by
this protocol and must appear in B3's exposure ledger. M2 test/OOD label
artifacts and all future final labels remain sealed.

## Methods and cost boundary

1. **Optimized uniform:** target-volume constant design, frozen projection,
   public SIMP refinement, and the existing independent quality audit.
2. **Impossible own-result oracle:** use that query's freshly computed uniform
   final design as a warm start. Its reference solve is generation cost, excluded
   from oracle per-query timing. This is only a bound on attainable refinement.
3. **Frozen physics heuristic:** one uniform-density sensitivity analysis,
   normalized score, frozen projection and refinement.
4. **Frozen training-only nearest neighbor:** use the complete M1 train index
   and frozen lookup on the lower scale. The fixed-shape M1 index cannot accept
   the higher scale; mark it ineligible there rather than silently resampling.
5. **Current learned starts:** all five fixed M1 checkpoints, seeds
   `[17, 29, 43, 71, 113]`, each applied unchanged to both scales. The model
   is shape preserving, but higher-scale inference is an untrained extrapolation.

Per-query time charges setup (including encoding/inference or heuristic FEM),
volume projection, complete SIMP refinement, and a fresh uniform fallback after
every non-uniform quality failure. A failed candidate remains failed. The
independent quality-audit re-solve is excluded from all method times, as in the
frozen M1 contract. Record per-refinement FEM time and call count, iterations,
convergence, compliance, physical-volume error, fallback time, and process
peak RSS. Record index and checkpoint loading time/size separately and discuss
amortization. All paths use the same case, solver, and numerical settings.

Uniform failure on any planned case is retained and prevents a B2 pass for
that scale; candidates without a valid uniform quality reference cannot be
claimed successful. The pilot does not silently extend the 120-iteration
budget or loosen the `0.01` tolerance. Any later budget revision needs a new
case identity and a fresh matched comparison.

## Pilot decision rule

For B2 to pass as a reason to invest in a new learned experiment, all six
uniform references at each scale must pass quality. All twelve own-result
oracle starts must pass the same quality checks with mean charged ratio below
`0.50` at each scale. The current learned panel is assessed over **all five
fixed seeds and all six cases per scale**, without selecting a favorable seed
or stratum: a viable current prototype would need zero accepted quality
failures (fallbacks remain charged), a mean charged ratio below `0.95` at each
scale, and at least half of its attempts to pass without fallback. A broader
ML claim still requires B3/B4/B5 and fresh final evidence. If the oracle
headroom passes but current prototypes do not, record a failed B2 prototype
gate and specify a bounded new development intervention; do not treat extra
MSE epochs or more final-data exposure as a remedy.

This pilot addresses one fixed-support family. It cannot justify claims about
other support conditions or distributed loads. B3 must either scope the final
workload to this exact family or budget separate development evidence before
adding support/load families.
