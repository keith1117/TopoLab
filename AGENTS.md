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

Full v2 delivery remains open; uniform is the operational default. No learned
acceleration/full-delivery claim. Historical v1.0.0 stays complete with negative
M1/M2 evidence. B3 data/B4.1 fitting passed; original B4.2 and scientific Gate
failed. Fixed P/17 remains unrepaired and cannot be replaced after outcomes.

Current **B4.49 source implemented; formal NOT_RUN**:12 new authored public
systems/ONE combined recipe frozen first; independent oracle/51 focused checks.
Clean locked merged source/all exact-head/main CI MUST precede first-only
producer/independent calls. See [report](docs/validation/b4_49_public_combined_diagnostic_certificate.md),
[protocol](docs/planning/b4_49_public_combined_diagnostic_certificate_protocol.md),
[contract](docs/planning/b4_49_public_combined_diagnostic_certificate_contract.json).
B4.48 TEXT233/231 and B4.47 public4328/104/quota1/1/1 remain; B4.43 FAIL/quota1/1/
all10 unexecuted/no original receipt/runtime+cause UNKNOWN/B4.42 FAIL remain.
Scientific FAIL/P17/uniform/seals stay; real executable UNFROZEN/certificates-cost
UNKNOWN_STOP. Whole software cost/peak UNKNOWN_NOT_ZERO; no old/full-fit gap filled.

Latest numerical/audit B4.30 scientific FAIL retains R17quality1.00197094375>
1.001/target mean1.01605313078>1.0/P-R failures1/3/1. Reflection stops; old
B4.27–29 quota closed3/3, B4.30 two paid invocations/one campaign/no third.
Old7323.1004352501081506 includes failed191.9666532080154866/BOTH FULL180;
Q31 once80.29939475003629922/separate7403.39983000014444982. B4.23 all69 failures/
57546.072069>7200, known-added58142.252069, B4.24/28 memory gaps, B4.20 FAIL/
B4.19 UNKNOWN/B4.31 premerge process FAIL remain. All prior failures/charges stay.
Known-paid12721.16417100014444982>7200 is diagnostic, no new cap/ledger reset.
Real certificates/cost UNKNOWN_STOP/executable UNFROZEN; full-Q/all8 simultaneous
full fit PENDING4GiB. Software RSS fills no historical/full-fit gap. Original
loss/gradient/normalizer unchanged. Exact-FEM candidate stops; no cache/order,
epoch/population/frequency search, fit or actual geometry/FEM/integration follows.

All final/conditional48/720/unused48 evidence remains sealed. Close ONLY current
B4.49 after formal/publication/backup; no retry/reset, real FEM/fit/search/new
production budget or sealed grant. Proposed B4.50 read-only combined public
certificate limitations/real prerequisites is NOT STARTED/AUTHORIZED; new owner/
finite TEXT contract FIRST. Learned repair/independent confirmation/full new B4/
compatible final remain before B5. Report the successor and stop.

Read [project status](docs/project_status.md) and linked latest evidence at session
start. Retrieve relevant [history](docs/development_history.md) when needed.
The English v2 roadmap controls gate order; README stays the public entry point.

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
