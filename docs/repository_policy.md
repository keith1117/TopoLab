# Repository and publication policy

GitHub is TopoLab's reviewable source, contract and evidence record throughout
development. A clear public entry point and complete research trace belong in
different documents. Generated experiment payloads remain outside the source
repository, bound to the committed implementation by immutable identities.

## What belongs in GitHub

| Content | Destination and rule |
|---|---|
| Source, tests, small reviewed public fixtures and example inputs | `src/`, `tests/`, `scripts/`, `frontend/`; retain meaningful checks |
| Dependency locks, build/CI configuration, license and provenance | Commit so a clean checkout can reproduce the environment and implementation |
| Overall project plans and English/Chinese reading companions | `docs/planning/`; English controls current development decisions |
| Frozen slice protocols and numerical/platform/ML contracts | Keep in Git before execution, at their existing paths and version identities |
| Validation reports, including failed and interrupted Gates | `docs/validation/`; retain completeness, source revision, resource charges, limitations and artifact hashes |
| Current status, history and directory indices | `docs/`; update at closeout without duplicating the growing chronology |
| Reviewed original architecture and demonstration assets | `docs/assets/`; document provenance and scope, use a deliberately bounded asset size |

The protocol files after the eight overall plans are preregistrations, not
disposable notes. They make the declared population, tolerances, budgets and
stopping rules reviewable before results exist. Validation reports make the
outcome auditable, including negative results. **Both stay on GitHub.** Removing
failed records would break the evidence trail rather than improve presentation.

Existing protocols have path and byte bindings in scripts and external release
receipts. Keep those paths and historical contents stable; use indices to improve
navigation. A protocol change requires a separate version and compatibility
boundary, not a formatting-only rewrite of the frozen record. Old Git revisions
and external release bindings remain part of reproduction.

## What stays outside Git

| Content | Storage |
|---|---|
| Generated labels, densities, trajectories, datasets and model weights | External experiment root such as the sibling `TopoLab-data` directory |
| Outcome indices, raw audit receipts/journals, native profiles, execution logs and caches | Same external root, with the complete successful and failed attempts retained |
| Runtime databases, run histories and temporary build outputs | Runtime volumes or ignored output/cache directories |
| Credentials, tokens, local environment values and device identifiers | Local configuration or secret storage; never in commits or reports |
| Personal drafts, scratch notes and incidental screenshots | Ignored repository-root `local/` or another directory outside Git |

The external root is not an expendable cache. Preserve the original files and
before-call journals, use an independent backup outside the repository, and
verify their identities through the committed reports and replay/audit tools.
`.gitignore` prevents accidental staging; it does not provide backup or access
control. Sealed evidence keeps its existing access guards during documentation
and repository maintenance.

Do not globally ignore Markdown, JSON, CSV, images or whole documentation
directories: protocols, public examples and reviewed fixtures use these formats.
The ignore rules target runtime roots, local secrets and generated array/model
formats, with explicit support for reviewed `tests/fixtures/` and `.env.example`.
New large assets need a deliberate distribution decision; Git history should not
become experiment storage. Do not delete or silently ignore another person's
untracked documents just to obtain a clean status.

## Stable document roles

- `README.md`: concise purpose, current usable capabilities, quick start and links.
  Keep it stable during research; update public usage when it changes and finish
  the presentation when the delivery Gates pass. Do not append slice metrics.
- `AGENTS.md`: reading order, non-negotiable boundaries, concise current stop and
  next slice. Read the linked current status at session start; retrieve relevant
  history and contracts on demand rather than injecting all history into context.
- `docs/project_status.md`: replace the current snapshot at each slice closeout.
  Keep the latest failed/passed Gate, fixed primary, unresolved evidence, sealed
  cohorts and exact next permitted slice explicit.
- `docs/development_history.md`: add one concise, linked entry per research slice.
  Historical results and old next-slice decisions retain their original context.
- The English v2 roadmap: keep the active sequence and Gate dependencies current;
  use a distinct paragraph or subsection per B4 slice. Chinese companions point
  to the English working version and current status.
- Planning/validation indices: add links when a protocol/report is published.
  Claims, full measurements and hash tables remain in the original reports.

Documentation maintenance may update these entry points and policies without
creating a new scientific Gate or repeating a numerical experiment. Preserve
frozen scientific files and all prior outcomes.

## Slice and GitHub workflow

1. Inspect current `main`, open PRs, current status and relevant contracts. Start
   one deliverable-named branch (`docs/`, `feat/`, `fix/`, `test/`, `bench/` or
   `experiment/`); keep `main` the only long-lived branch.
2. Freeze a numerical/experimental contract and commit its implementation before
   production access. Execute only from the required clean, CI-passed merged
   revision with a locked environment and external output root.
3. At closeout publish the relevant validation report, including failed Gates;
   retain provenance, full cost and immutable external artifact bindings. Update
   current status, one history entry and the relevant roadmap/index links. Adjust
   the concise AGENTS current boundary when needed; README changes only for public
   usage or evidence-backed claims. Routine maintenance needs no history entry.
4. Run every mandatory check before each commit, review `git status`, the complete
   diff and the staged paths, then stage only the intended files. Inspect ignore
   behavior for any new output format; do not rely on a blanket `git add .`.
5. Open a PR with the concrete behavior/document change, validation and any
   material limitations. Attach source/evidence PRs to the slice as applicable.
   Require `quality`, `frontend` and `clean-linux-smoke` on the exact PR head;
   intentionally skipped feature-push smoke is not the PR's acceptance evidence.
6. Keep `main` protected: require an up-to-date PR with those three checks and
   resolved review conversations, apply the rules to administrators, and disable
   force pushes and branch deletion. A solo maintainer need not require another
   human approver. Never merge while a required check is pending or failed.
7. Squash merge after CI passes, remove the merged short-lived remote branch,
   verify merged `main` and its CI, and report the next permitted slice without
   automatically starting it.

A hosted-runner interruption may be retried on the same source after inspecting
its cause; retain the failed/interrupted attempt when it is part of experimental
release evidence. Changing source requires fresh exact-head validation.

## Required checks

Run before every commit, including documentation-only changes:

```bash
uv sync --dev --locked
uv run ruff check .
uv run mypy src
uv run pytest
git diff --check
```

For bounded local numerical-test CPU usage, prefix the complete pytest command
with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1`. Run the same complete test
population and preserve every tolerance; this is a test-resource setting.

Run the frontend checks when its workspace changes; CI covers them on every PR.
For documentation changes, also verify relative links, preserved protocol/report
identities, Markdown paragraph separation and the intended `.gitignore` behavior.
For numerical changes, follow the relevant contract's independent audit and
explain any conditioning/scale reason for a tolerance change in its report.
