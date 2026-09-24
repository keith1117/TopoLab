# TopoLab Numerical Core Reimplementation Strategy

English counterpart of [the Chinese strategy](./TopoLab_reimplementation_strategy.md).
Related documents: [Admissions fit](./TopoLab_admissions_fit_assessment.en.md) · [Development timeline and resources](./TopoLab_development_timeline_and_resources.en.md)

## Core decision

TopoLab should not keep adding features directly to Jiangce's original `3D_SIMP_Topology_Optimization_Numpy` code. Instead:

> **Use the original repository as a reference baseline and validation target; independently design, implement, and validate TopoLab's Numerical Core.**

The fixed reference is the [Jiangce2017 repository](https://github.com/Jiangce2017/3D_SIMP_Topology_Optimization_Numpy), commit `584cb8ee570d375f8ba9b10272020c5c2daa8c30`. As checked on 2026-09-17, GitHub showed no open-source license. Public visibility does not grant permission to copy or redistribute code. TopoLab should commit independent implementation, references to standard algorithms, and behavioral comparisons, but no upstream source files or rewrites of them.

The original repository is useful for teaching, understanding the algorithm flow, and obtaining quick results. It is not a suitable long-term core for a maintainable, extensible, testable platform. Reimplementation also makes individual contribution, code quality, extensibility, and graduate-application value easier to demonstrate.

## Why reimplement

The small original 3D SIMP repository has three main Python files, but the following problems or limits have been identified:

- `direction=-1` acts as a DOF-index offset rather than a negative load direction.
- Both the caller and load function may divide the total load among nodes.
- Compliance and density in history may describe different iteration states.
- Dense global stiffness makes larger meshes rapidly expensive in time and memory.
- The density filter computes all-pairs element distances, limiting growth.
- Solver, optimizer, plotting, and entry script lack clean interfaces.
- Automated numerical validation and regression tests are missing.
- The structure is not ready for asynchronous jobs, persistence, experiment tracking, or ML data generation.

Continued patching can preserve historical coupling and raise platform costs. A new core can begin with clear data models, sparse finite-element assembly, independently testable numerical modules, serializable inputs and outputs, traceable optimization state, and stable interfaces for API, workers, and ML. Pause/resume belongs to a later, explicit state contract.

## Role of the original repository

Keep the original as a reference implementation outside the TopoLab repository. Record its URL, commit SHA, default mesh/material/load/support/optimizer configuration, outputs, and known defects with their scope. Do not copy complete upstream files into the public repository without explicit authorization for public modification and redistribution.

## Recommended implementation steps

### 1. Freeze the original baseline

Before changing logic, save the original configuration, density/compliance/volume history, figures, runtime environment, upstream commit, and known-bug list. These results are historical baseline evidence, not TopoLab's final output.

### 2. Establish small benchmark cases

Extract problem definitions rather than implementation: a small cantilever, fixed-face support, point load, distributed face load, several volume fractions, and short density/compliance histories. Keep a few verifiable numerical fixtures for cross-checking; migrating every historical image and output is unnecessary.

### 3. Independently implement the Numerical Core

Start with a small structure rather than ten tiny modules:

```text
src/topolab/
├── model.py       # problem/config/result models
├── mesh.py        # structured Hex8 mesh
├── fem.py         # element, assembly, BC/load, solve
├── simp.py        # filter, sensitivity, OC, optimization loop
└── io.py          # reproducible config/result serialization
```

Only when responsibilities are stable and a file is clearly too large should it evolve toward this target structure:

```text
src/topolab/core/
├── mesh.py
├── elements.py
├── materials.py
├── boundary_conditions.py
├── loads.py
├── assembly.py
├── solver.py
├── sensitivities.py
├── filters.py
├── optimizer.py
└── result.py
```

The second tree is a possible architecture, not an advance checklist. Each split needs a test boundary or at least two callers to justify it.

Freeze these conventions in `docs/numerical_conventions.md` before coding:

- Right-handed coordinates, node numbering, and Hex8 local-node order;
- `(ux, uy, uz)` DOF order per node;
- `direction` restricted to `x/y/z` or `0/1/2`, with sign in the magnitude;
- SI units and the dimensions of each input;
- Density range, `E_min/E_0`, and the penalization equation;
- Density versus sensitivity filtering and where filtering enters OC;
- Whether compliance, reactions, history, and stopping describe density before or after an update.

Recommended order: (1) structured Hex8 mesh; (2) element stiffness; (3) sparse global assembly; (4) supports and loads; (5) displacement solve and compliance; (6) sensitivities; (7) filtering; (8) OC update; (9) SIMP loop and convergence; (10) result serialization and experiment state.

Version one should support only a structured rectangular mesh, isotropic linear elasticity, small deformation, one load case, and point/face loads. Multiple materials, unstructured meshes, dynamics, multiphysics, and GPU solving are outside its scope.

### 4. Cross-validate

On cases unaffected by known upstream defects, compare coordinates, element connectivity, total load, displacements, compliance, sensitivities, one density update, volume per iteration, and final small-mesh topology. Add independent checks for finite-difference sensitivity, load/reaction balance, stiffness symmetry, completeness of constraints, mesh convergence, dense versus sparse solving, and a final-density re-solve.

Set thresholds as test constants and record hardware, mesh, and numerical scales in the report. Initial targets are:

| Check | Initial acceptance target |
|---|---|
| Element/global stiffness symmetry | `||K-Kᵀ|| / ||K|| ≤ 1e-10` |
| Dense versus sparse displacement/compliance on small meshes | `rtol ≤ 1e-9` |
| Load/reaction balance | Relative residual `≤ 1e-8` |
| Central finite-difference sensitivity | Relative error `≤ 1e-4` for most non-boundary variables; maximum `≤ 1e-3` |
| Post-OC volume | Absolute distance from target `≤ 5e-3` |
| Final-state consistency | Re-solved returned density agrees with recorded final compliance within `rtol ≤ 1e-9` |
| Determinism | Same input, environment, and version give the same history within floating-point tolerance |

Explain any change to a threshold because of conditioning or scale; never loosen it silently. Because the upstream code is unlicensed and has known bugs, its outputs are secondary evidence. Resolve disagreements with independent physics and numerical checks; do not make correct behavior imitate an upstream error.

### 5. Build stable upper-layer interfaces

Once the core is stable, expose one problem/result entry point to API, workers, frontend, and ML, for example:

```python
problem = TopologyProblem(
    mesh=mesh,
    material=material,
    supports=supports,
    loads=loads,
    volume_fraction=0.2,
)

result = optimize(problem, config)
```

This is an illustrative target interface, not the current API signature. The Web layer should not manipulate FEM arrays directly. FastAPI, workers, experiment management, and ML generation should call through the common problem/result boundary.

From the first version, `optimize` should accept optional `initial_density` and return same-state metrics per iteration. Add a narrow progress callback and cancellation token in the platform phase without pulling Web or ML dependencies into the core. Checkpoint/resume can follow once the state model is stable; it is not a blocker for the first core version.

### 6. Build the platform and ML on the new core

Start large platform and ML work only after small-mesh numerical tests, sensitivity verification, dense/sparse agreement, correct load/volume/final compliance, and stable serialization are established. Then add asynchronous jobs, database persistence, a 3D frontend, dataset generation, and learned warm starts.

### 7. Freeze the ML experiment contract

Before large-scale data generation, commit `docs/ml_experiment_contract.md` with at least:

- A unique case ID and schema for mesh, material, supports, loads, and volume fraction;
- Input channels for axis-aware support/load voxels, coordinates, and broadcast volume fraction;
- `[0,1]` density output projected or normalized to target volume before SIMP;
- The exact solver/data-generator version and termination rule that produce labels;
- Train/validation/test splitting by whole physical case, never by iterations of one trajectory;
- Fixed uniform, physics-based, and nearest-neighbor baselines;
- Final compliance, volume, and failure quality rules;
- Data-generation, inference, SIMP refinement, and end-to-end time accounting;
- An OOD axis fixed before viewing test results, such as load position/direction, support pattern, or volume fraction; and
- Multiple seeds, confidence intervals, and a uniform fallback rule for model failure.

The first model should answer only whether a predicted initial density reaches an equal-quality solution sooner. Do not simultaneously add a compliance surrogate, generative model, reinforcement learning, or an end-to-end solver replacement.

## What may be learned from references

With clear citation, learn from the problem setting, standard SIMP sequence, Hex8 equations, OC concept, default parameters, example supports/loads, result presentation, and implementation difficulties exposed by the original repository.

### Preferred standard references

- Kai Liu and Andrés Tovar, [*An efficient 3D topology optimization code written in Matlab*](https://doi.org/10.1007/s00158-014-1107-x), 2014: the main theoretical and numerical reference for 3D Hex8, minimum compliance, sensitivities, filters, and OC.
- Andrés Tovar's [Top3d documentation](https://www.top3d.app/): standard 3D problem settings and paper errata.
- Ole Sigmund, [*A 99 line topology optimization code written in MATLAB*](https://doi.org/10.1007/s001580050176), 2001: the classic teaching reference for density-based SIMP, filtering, and OC.

Implement from published equations and independent derivation, not a line-by-line translation of any reference code. Document every equation, convention, and departure from literature.

## What must not be copied directly

- Complete Python files;
- Upstream function structure and module layout;
- Long comments or the original variable-naming scheme;
- Plotting and entry scripts;
- Known defective load logic; or
- Unauthorized source excerpts.

If a piece of upstream code truly must be used, first obtain explicit permission from Jiangce for public modification and redistribution, then preserve author, source, and applicable license in affected files.

## Provenance and contribution records

`PROVENANCE.md` should identify the upstream URL and commit, SIMP/FEA references, behaviors compared with the original, independently implemented modules, any authorized upstream code, and numerical/performance differences. Describe the work as independent reimplementation, validation, and engineering of standard algorithms, not invention of topology optimization.

TopoLab should choose an explicit license in its first commit. If author permission is later obtained and upstream code enters the project, recheck license compatibility and mark the affected files and `PROVENANCE.md`. Oral permission alone is not a general open-source license.

## A verifiable meaning of “scalable”

SciPy sparse use alone does not prove scalability. At minimum:

- Report elements, DOFs, assembly time, solve time, peak memory, and total time on at least three increasing meshes;
- Verify numerical agreement with dense computation on a small mesh;
- Show a larger sparse case completes after the dense form becomes memory-limited;
- Fix hardware, thread count, tolerances, and solver settings, and provide the benchmark script; and
- Separate cold and repeated runs to expose caching and one-time setup.

Until that evidence exists, use `sparse` or `performance-oriented` in README and resume, not `scalable`.

## First reviewable repository milestone

The first milestone should include only: (1) problem, scope, and exclusions in README; (2) `PROVENANCE.md` with a fixed upstream commit; (3) locked environment, quality settings, and CI smoke; (4) numerical conventions; (5) structured Hex8 mesh and element stiffness; and (6) tests for stiffness symmetry, node/DOF numbering, face-load total, and fixed DOFs.

Do not mix FastAPI, React, Redis, or PyTorch into that milestone. The first commits should demonstrate numerical design and verification rather than a long technology list.

## Suggested resume wording

Once supported by evidence:

> Independently reimplemented and validated a 3D SIMP topology-optimization engine, using the original Hack3D NumPy implementation as a reference baseline; introduced sparse finite-element assembly, typed boundary/load models, finite-difference sensitivity checks, and regression benchmarks.

Avoid `Invented a new topology-optimization algorithm`, `Implemented entirely from scratch`, and `Developed the original 3D SIMP method`. “Independently reimplemented and validated” states the contribution while crediting the standard method and reference.

## Time and admissions value

Reimplementing the Numerical Core rather than adding a UI around the old code was estimated to add **1–2 weeks** but provide clearer code ownership, more reliable numerics, easier maintenance, more credible performance benchmarks, a stronger ML data foundation, deeper CS/SWE interview material, and a clearer authorization boundary.

Reusing the original core behind a webpage could look like a wrapper around a mentor's code. Independently reimplementing, validating, and sparsifying the core instead demonstrates work across algorithms, software architecture, and ML systems.

## Final recommendation

TopoLab should not be a Web wrapper around Jiangce's repository. Keep the original as historical baseline, learning material, and cross-check; independently build a validated, sparse, modular 3D SIMP Numerical Core; then build the platform and evaluate ML warm starts on that core. This improves the license boundary, attribution of individual work, engineering quality, and admissions narrative.
