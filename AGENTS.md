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

The latest completed slice is **B4.22**: versioned stable-projection correctness
passed all 1704 conditions at the unchanged FD 1e-4 bound. B4.20 remains failed;
B4.21's diagnostic compatibility is not a causal finding. B4.19's failed case,
gap and counts stay unknown. No local fidelity, fit-cost or full training-memory
acceptance is established. Next is **B4.23 bounded versioned local-surrogate
fidelity and cost probe**, not started; freeze a separate boundary before execution.

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
