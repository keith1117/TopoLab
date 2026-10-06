# TopoLab — Reproducible 3D Topology Optimization Platform

TopoLab independently implements structured Hex8 finite elements and 3D SIMP
minimum-compliance optimization, with a local web workspace and reproducible
ML warm-start experiments.

**Active v2 development.** The historical `v1.0.0` release is complete; full v2
flagship delivery still requires reproducible, same-quality learned end-to-end
acceleration. Uniform initialization remains the operational default. Current
progress and evidence are maintained in the [documentation](docs/README.md).

## Capabilities

- Sparse finite-element assembly and solving, density filtering and OC updates.
- Typed API, local process workers, cancellation and SQLite run persistence.
- React workspace for problem setup, run history, convergence and 3D density views.
- Versioned experiment contracts, independent quality audits and charged fallbacks.

Scope: structured rectangular meshes, isotropic linear elasticity, small
deformation and a single load case with point or face loads. Optimizer
checkpoint/resume, hosted production operation and general ML acceleration
remain outside the current delivery evidence.

## Run locally

For the numerical demo, install Python 3.12 and [uv](https://docs.astral.sh/uv/):

```bash
uv sync --dev --locked
PYTHONPATH=src uv run --locked python -m topolab.demo --output-dir /tmp/topolab-demo
```

For the API and frontend, use Docker with Compose from the repository root:

```bash
docker compose up --build -d
```

Open <http://127.0.0.1:8080>. See [getting started](docs/getting_started.md) for the
walkthrough, result format and local-stack limits.

## Documentation

| Entry | Purpose |
|---|---|
| [Documentation guide](docs/README.md) | Architecture, usage, contracts and evidence |
| [Project status](docs/project_status.md) | Current gate, stopping boundary and next slice |
| [Planning](docs/planning/README.md) | Roadmap, overall plans and frozen slice protocols |
| [Validation](docs/validation/README.md) | Numerical checks, experiments and retained failures |
| [Contributing](CONTRIBUTING.md) | Development checks and repository policy |

## Provenance and license

TopoLab's implementation is independently derived from published SIMP and Hex8
equations. The unlicensed Hack3D reference is used only for historical behavior
comparison; see [PROVENANCE.md](PROVENANCE.md).

Original TopoLab code and documentation use the [MIT License](LICENSE).
