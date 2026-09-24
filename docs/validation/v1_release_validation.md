# v1.0.0 release validation

Date: 2026-09-24  
Release-candidate revision: `aaec418f79a802d0f76313df50390b2e55d05a94`  
Decision: **PASS**

## Scope

This report closes the v1 release after the numerical, platform, benchmark, and ML
gate reports were frozen. It does not rerun production data generation or training:
those immutable executions and their decisions remain in their dedicated validation
reports. It verifies the repository release candidate from a clean `main`, including
locked environments, all automated tests, distributable Python artifacts, public
version metadata, and the absence of tracked generated data or obvious credentials.

The annotated `v1.0.0` tag must point at the documentation-only merge containing this
report and may be created only after that PR's required GitHub checks pass. No source,
dependency, or runtime behavior changes are permitted between the validated revision
and that merge.

## Environment

- Host: macOS 26.5, Apple arm64
- Python: 3.12.10
- NumPy: 2.5.3
- SciPy: 1.18.1
- PyTorch: 2.14.0
- FastAPI: 0.141.1
- SQLAlchemy: 2.0.54
- Node.js: 26.2.0
- npm: 11.13.0

Dependency resolution used the committed `uv.lock` and
`frontend/package-lock.json`; neither lock file changed during validation.

## Verification results

| Check | Result |
|---|---|
| `uv sync --dev --locked` | Passed; installed local package `topolab==1.0.0` |
| `uv run ruff check .` | Passed |
| `uv run mypy src` | Passed; 26 source files |
| `uv run pytest` | Passed; 262 tests in 15.28 s |
| `npm ci` | Passed; 109 packages installed from the lock file |
| `npm run typecheck` | Passed |
| `npm test` | Passed; 4 files and 22 tests |
| `npm run build` | Passed; Vite production bundle generated |
| `uv build` | Passed; source distribution and wheel generated |
| Isolated wheel smoke test | Passed; package and FastAPI versions both reported `1.0.0` |
| `git diff --check` | Passed |
| Repository status before report branch | Clean and synchronized with `origin/main` |

Vite reported its advisory warning for Plotly chunks larger than 500 kB. Plotly's 2D
and GL3D distributions are already loaded through separate dynamic chunks, the build
completed successfully, and this warning does not change the release decision.

## Package artifacts

The artifacts below were built locally for verification and remain ignored rather
than committed:

| Artifact | Bytes | SHA-256 |
|---|---:|---|
| `topolab-1.0.0.tar.gz` | 259,033 | `bdcfb414da927e0185cb2044d724e0bd103b8233888c478bc3b1bde7034fea7d` |
| `topolab-1.0.0-py3-none-any.whl` | 83,931 | `e998f280a740be3a71fab1d263d0690898f76e4cfae7332cee602de8159eda73` |

An isolated environment installed the wheel and asserted both
`topolab.__version__ == "1.0.0"` and `create_app().version == "1.0.0"`.

## Repository audit

- No tracked paths matched the ignored output classes `results/`, `artifacts/`,
  `data/generated/`, frontend build output, logs, database files, or SQLite files.
- A tracked-text signature scan found no private-key header, AWS access-key pattern,
  GitHub token pattern, or OpenAI-style secret-key pattern.
- The source distribution contains repository source, tests, frontend source,
  contracts, and validation documentation. The wheel contains only the Python
  package and standard distribution metadata/license files.
- Production datasets, solver outputs, checkpoints, and evaluation artifacts remain
  outside Git as required by the experiment contracts.

## Release decision and claims boundary

The release candidate satisfies the v1 acceptance criteria and is approved for an
annotated `v1.0.0` tag after the report PR passes CI and merges. The decision confirms
software packaging and the already documented N1/N2/P1/M0 evidence; it does not
change the frozen ML decisions. Uniform initialization remains the operational
default, M1 remains negative/inconclusive, M2 remains stopped at its failed data gate,
and TopoLab makes no universal-scalability or learned-acceleration claim.
