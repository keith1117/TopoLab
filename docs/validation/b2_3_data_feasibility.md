# B2.3 versioned iteration-budget repair and sentinel audit

Date: 2026-09-25

Diagnostic boundary revision: `b2471fe`; single candidate revision:
`e639dd0`; runner revision: `ad0ff619e2048bfe139c93d82d8c87e50753e48b`.

Status: **B2.3's bounded 61-case data-feasibility Gate passes.** This permits
planning a separately reviewed full development-label materialization. It
does not establish that all 522 labels will succeed, that a learned prototype
is faster, or that the v2 ML delivery condition has passed.

## Frozen diagnosis and one correction

The [protocol](../planning/b2_3_data_feasibility_protocol.md) held the
B2.2 61-case source cohort fixed. A read-only extension reproduced each of
the eight failed cases' update-120 compliance, design maximum, and ten-step
physical change exactly. Under the unchanged
`topolab.simp.physical_plateau.v1` solver, all eight met an existing stop rule
by the predeclared 240-update diagnostic ceiling: seven small `y/0.45` cases
at update **125** by physical plateau, and one large `z/0.20` case at update
**170** by design maximum. The external diagnosis JSON at
`/tmp/topolab-b23-diagnosis.json` has SHA-256
`33e709d68aea3754f0789bf0d1eb9e6e18a4086f9435eb5dfc0b930e3348cbb2`.
It took 48.25 s and peaked at 351,109,120 bytes RSS. The extension was
diagnostic, not an accepted B2.2 label.

Exactly one correction was committed before the corrected cohort ran:
increase the **explicit per-case maximum** from 120 to 240 while retaining
the B2.1 solver, `0.01` design/physical density scale, `0.0002` ten-step
compliance bound, OC update, filter, stiffness, and all quality tolerances.
The 240 ceiling had already been fixed for the diagnostic, so no threshold
was adjusted to the observed 125 or 170 stop. The historical public default
and B2.1/B2.2 outcomes remain unchanged.

Because `max_iterations` is part of the physical case identity, each of the
61 source problems receives a new `tlcase-v1-*` ID. The plan version is
`topolab.b2_3.budget240.plan.v1`; prospective label version
`topolab.b2_3.label.v1` and `tlcase-b23-v1-*` result IDs bind the old source
ID, new case ID, and unchanged solver policy. The canonical plan SHA-256 is
`45baa0f74c74fca3ea3d7594b7576f1150a6dc950b23daafdab5acc8e1f5c289`.
The external plan JSON at `/tmp/topolab-b23-plan.json` has file SHA-256
`4cf0ec5b98778c89f1d0abae3f48841661333cfb3c7ed7c3a2b7f268fc73b71d`.
No old M2/B2.2 label can be silently reused under this new identity.

## Full fixed-sentinel execution

The committed runner executed the 61 cases once on Apple arm64, macOS 26.5,
Python 3.12.10, NumPy 2.5.3, and SciPy 1.18.1, with OpenMP/BLAS/VECLIB/
MKL/BLIS threads fixed to one. It verified the exact B2.2 prior-result file
SHA-256 `45d29dd6568da34fd097a522aff072d08afc121dd98a5f784411d79db7004b78`
before use. The external metadata-only result at
`/tmp/topolab-b23-sentinel.json` has SHA-256
`70a597c4fe69ca80115726921bdbe22d7c96e51d11ccdfddc0220e2ce83628c1`.
Locked dependencies retained `uv.lock` SHA-256
`9c84a5ab362e8848d7ccab0142e9fe33aee5700abf5866d843a4c9cb23920292`.

| Sentinel stratum | Cases | Accepted | Largest iteration |
|---|---:|---:|---:|
| Large train | 18 | 18 | 170 |
| Large validation | 18 | 18 | 112 |
| Small train, seven former failures | 7 | 7 | 125 |
| Small validation | 18 | 18 | 76 |
| **Total** | **61** | **61** | **170** |

All 61 converged within 240 updates, kept a consistent final-state history,
and passed finite-state, physical-volume (`<= 0.005`), and independent
compliance re-solve (`rtol <= 1e-9`) checks. The largest observed physical
volume error was `9.89e-9`. Twenty-eight stopped by the design maximum and
33 by physical plateau. The seven former small failures stopped at update
125; the former large failure stopped at 170. The other 53 sources retained
**exactly the same** stop iteration and final compliance as in B2.2 (maximum
relative difference `0`). An independent audit matched all 61 ordered
old/new/result IDs to the frozen plan and verified these 53 regression guards
and eight recovered cases. No result row contains a density field.

Total measured wall time was **666.71 s** and peak process RSS was
**331,857,920 bytes (316.48 MiB)**, below the frozen 1,500 s and 1 GiB
caps. These are one local execution and cannot be interpreted as cross-machine
performance evidence. No B2.3 density label, training data, or model was
materialized in this slice.

## Gate, limits, and next slice

**The fixed sentinel Gate passes 61/61.** It shows the eight observed
120-update failures are resolvable under an explicitly versioned finite
budget without changing the stopping thresholds or regressing the 53 old
successful sources. The 61 cases are a development-exposed sentinel, not the
full 522-case population or a fresh ML final cohort. The B2 learned-prototype
and v2 delivery Gates remain open. Every later method comparison must use
matched 240-update cases and the same solver policy, charging all failures
and fallback; old B2.1 timing ratios cannot be reused as new denominators.

The next independent slice is **B2.4: freeze and audit the complete 522-case
development-label plan under the B2.3 budget**, then materialize all new
policy/budget labels only from a clean, committed, external-root plan. The
full data Gate must retain every case, split, stratum, checksum, failure, and
resource cost. If any required label fails, no fitting begins; diagnose and
version another intervention rather than dropping cases. The control and
candidate fitting remain the later B2.5 slice, conditional on B2.4.

## Repository validation

Before each commit, `uv sync --dev --locked` from the locked offline cache,
Ruff, mypy on `src`, full pytest, and diff checks passed. The candidate
runner also passed mypy; the independent large-failure acceptance case was
run before complete sentinel execution. The final pre-execution full suite
had **284 passed**. All generated JSON stayed outside Git; test/OOD labels,
new final evidence, model weights, and datasets were not read or written.
