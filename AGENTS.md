# TopoLab agent instructions

## Read before changing code

Read these files in order:

1. `PROVENANCE.md`
2. `docs/numerical_conventions.md`
3. `docs/reference_baseline.md`
4. `docs/planning/TopoLab_reimplementation_strategy.md`
5. `docs/planning/TopoLab_development_timeline_and_resources.md`
6. `docs/planning/TopoLab_v2_development_roadmap.md`
7. `docs/project_status.md`
8. The contracts and latest validation reports relevant to the requested slice.
9. `docs/repository_policy.md` before staging or publishing changes.

## Current project state

The full v2 flagship delivery Gate remains open. Uniform initialization is the
operational default; no learned-acceleration or full-delivery claim is allowed.
The historical `v1.0.0` release remains complete, with its negative M1/M2 evidence
preserved. B3's data Gate and B4.1 fitting passed; the original B4.2 Gate failed.
Fixed P/17 remains unrepaired and cannot be replaced after seeing outcomes.

The latest completed numerical/audit slice is **B4.30 fixed-P/17 reflection repair**:
scientific **FAIL**, complete v2 numerical/native resource **PASS**. See
[report](docs/validation/b4_30_paid_continuation.md),
[v2 protocol](docs/planning/b4_30_paid_continuation_protocol.md) and
[finite contract](docs/planning/b4_30_paid_continuation_contract.json).
All18/270 and prescribed audits complete:323 terminal/204 guard classifications,
78 prediction replays/249 old identities. R17 retains one quality failure
(1.00197094375>1.001) and target mean1.01605313078>1.0; paired P/R failures
remain1/3/1. Four historical target predicates pass already in matched P;
no currently failed P target is newly repaired. Conditional48/720 unopened.
Cumulative7323.1004352501081506/43200 retains failed191.9666532080154866 and
both FULL180 reserves; conservative new whole-chain peak800047104<2GiB.
Original failed preflight resource FAIL/INCOMPLETE and all original bytes remain.

The B4.27–29 quota remains closed3/3; B4.30 stays2 paid invocations/1 campaign,
no third. Reflection stops. B4.31 [review](docs/validation/b4_31_reflection_failure_cost_review.md)
remains118/430 metadata/native PASS, Q31=80.29939475003629922; old7323.1004352501081506
and separate combined7403.39983000014444982 remain. Its source-premerge process
failure stays failure. B4.32 [preregistration](docs/validation/b4_32_generalist_method_preregistration.md)
remains69/32 static PASS. Historical public software **B4.33 reciprocal-energy algebra/access**:
47 focused tests/849 independent exact-rational predicates PASS on8 public toys/
76 fixed points; [report](docs/validation/b4_33_reciprocal_energy_evidence.md),
[protocol](docs/planning/b4_33_reciprocal_energy_evidence_protocol.md),
[contract](docs/planning/b4_33_reciprocal_energy_evidence_contract.json).
Exact toy anchor/PSD/SPD only; real floating residual/spectral/rounding certificates,
fidelity/cost/reliability UNKNOWN. No production or actual FEM/integration/fit.
Scientific FAIL/P17 unrepaired remain. Known-paid12721.16417100014444982>7200
is diagnostic, not a cap/ledger reset. B4.34
[preregistration](docs/validation/b4_34_admissibility_full_cost_preregistration.md)
remains129/43 document PASS. Latest public software **B4.35 diagnostic certificate**:
58 tests/394 independent exact-rational predicates PASS on8 systems/16 points;
[report](docs/validation/b4_35_public_admissibility_certificate.md),
[protocol](docs/planning/b4_35_public_admissibility_certificate_protocol.md),
[contract](docs/planning/b4_35_public_admissibility_certificate_contract.json).
Exact intended rational PSD/coercivity/residual and fixed80-bit/outward binary64
only; tiny nonzero residual never certifies unmodified U. Bound diagnostic, no
loss/gradient change. Real FEM certificates/costs UNKNOWN_STOP, all-paid7200
infeasible, full fit PENDING4GiB. No actual payload/FEM/timing/integration/fit.
Proposed next **B4.36 bounded read-only certificate limitations and real-route
preregistration**, not started: owner continuation/finite metadata contract first.
No actual data/FEM/projection/root/network integration/fit/search/new cap or seal.
B4.23 stays3907/3976/all69 failures and57546.072069>7200; known-added58142.252069>7200,
B4.24/28 memory gaps/both failures, B4.20 failure and B4.19 UNKNOWN remain.
Full training memory PENDING/4GiB; software RSS fills no historical gap.

All final evidence and the 48 unused B4.10 fresh cases remain sealed. The failed
exact-FEM candidate stops; no fit, alternate cache/ordering, continuation,
epoch/population/physics-frequency search or final access follows automatically.
Passing learned repair, independent confirmation and a compatible final contract
remain required before B5. Preserve every prior failure and charge.

Read [project status](docs/project_status.md) and its linked latest evidence at
session start. The [development history](docs/development_history.md) retains the
full earlier record; read the relevant entries when a slice depends on them.
The English v2 roadmap controls gate order; README is a public entry point.

## Provenance boundary

The Hack3D reference repository has no declared open-source license. Do not copy,
translate, patch, vendor, or redistribute its code, comments, file structure, or
figures. Implement from published equations and independent derivation. Use the fixed
upstream commit only for historical behavior comparison, and record any comparison or
new source in `PROVENANCE.md`.

## Development rules

- Keep each change scoped to one numerical behavior with tests.
- Freeze conventions in `docs/numerical_conventions.md` before relying on them.
- Prefer the current small module plan; split modules only when stable responsibilities
  or multiple callers justify it.
- Do not add FastAPI, React, Redis, PyTorch, data generation, or ML before gate N2.
- Do not claim `validated`, `scalable`, or `accelerated` until the documented evidence
  gate is complete.
- Never commit generated datasets, run artifacts, caches, secrets, or device IDs.
- Follow `docs/repository_policy.md`: keep protocols and validation reports in Git,
  keep generated evidence external, and stage only reviewed paths.
- Close slices by updating current status, one history entry and the relevant
  roadmap section/index. Keep this file concise; do not append the full chronology.
  Update README for public usage/claims changes or final delivery, not every slice.
- Name branches by deliverable without `codex` or other agent-name tokens;
  merge PRs only after CI passes and report the next slice after each slice.

## Required validation

Run before every commit:

```bash
uv sync --dev --locked
uv run ruff check .
uv run mypy src
uv run pytest
git diff --check
```

If a numerical test requires a tolerance change, explain the scale/conditioning reason
in the validation report; do not silently loosen it.
