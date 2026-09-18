# TopoLab

TopoLab is a planned, independently implemented platform for validated 3D SIMP
topology optimization. The project will combine a sparse finite-element numerical
core, reproducible experiment workflows, and a controlled evaluation of learned
warm starts.

> **Status:** Gate P1 has passed for the `v0.3.0` in-memory platform. It combines the
> validated numerical core with serializable problem/result contracts, isolated run
> state, cooperative cancellation, and a minimal HTTP adapter. Persistence, process
> workers, scalability evidence, frontend work, and ML remain incomplete.

## Intended scope

The first implementation targets a structured rectangular Hex8 mesh, isotropic
linear elasticity, small deformation, single-load-case minimum-compliance SIMP,
point and face loads, density filtering, and an Optimality Criteria
update.

Development is gated in this order:

1. validate the finite-element and SIMP numerical core;
2. benchmark sparse assembly and solving;
3. add API, job execution, persistence, and visualization;
4. generate versioned cases and evaluate learned density-field warm starts.

## Non-goals for the first release

- unstructured meshes or CAD import;
- nonlinear, dynamic, thermal, or multi-physics analysis;
- multiple materials or manufacturing constraints;
- GPU finite-element solving;
- an end-to-end neural replacement for the physics solver.

## Development setup

Requirements: Python 3.12 and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync --dev
uv run ruff check .
uv run mypy src
uv run pytest
```

## Repository map

```text
docs/
  numerical_conventions.md     Numerical definitions that code and tests must follow
  reference_baseline.md        Frozen upstream reference and known limitations
  planning/                    Admissions, schedule, and implementation planning
  validation/                  Gate evidence, thresholds, results, and limitations
src/topolab/                   TopoLab package and finite-element foundation
tests/                         Package and numerical convention tests
```

The provisional platform contract and run lifecycle are documented in
[`docs/platform_contract.md`](docs/platform_contract.md).

## Provenance

TopoLab is not a fork or redistribution of the Hack3D reference implementation.
That repository currently declares no open-source license. Its behavior and fixed
commit are documented in [PROVENANCE.md](PROVENANCE.md), while TopoLab's code will
be implemented independently from published SIMP and Hex8 references.

## Claims policy

The README and application materials will use `validated`, `scalable`, and
`accelerated` only after the corresponding gates and reproducible evidence in
[`docs/planning`](docs/planning/) are complete.

## License

TopoLab's original code and documentation are licensed under the [MIT License](LICENSE).
This license does not apply to external repositories, papers, or datasets.
