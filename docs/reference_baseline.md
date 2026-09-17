# Hack3D reference baseline

This document records historical behavior for comparison. The referenced source code
is not part of TopoLab.

## Frozen revision

- URL: <https://github.com/Jiangce2017/3D_SIMP_Topology_Optimization_Numpy>
- Commit: `584cb8ee570d375f8ba9b10272020c5c2daa8c30`
- Files at the revision: `fem3d_numpy.py`, `simp_numpy.py`,
  `run_optimization_numpy.py`
- Declared license: none found on 2026-09-17

## Default example observed at that revision

- Domain: `Lx=1.0`, `Ly=0.2`, `Lz=0.1`
- Mesh: `20 x 6 x 4` Hex8 elements
- Material: `E=200e9`, `nu=0.3`
- Volume fraction / initial density: `0.2 / 0.2`
- SIMP penalty: `3.0`
- Filter radius: `0.02`
- Iterations: `100`
- Left face fixed; a distributed load is requested on the right face

## Known comparison hazards

1. The example passes `direction=-1`, while the function treats direction as a DOF
   offset. This does not encode a negative force direction safely.
2. The caller divides the requested total load before the load function distributes it
   across selected nodes, so the resultant is divided twice.
3. Each history row stores compliance evaluated at the old density and volume evaluated
   at the new density.
4. Returned `final_compliance` is not recomputed for the returned final density.
5. Global stiffness and filter weights are dense, limiting mesh growth.

TopoLab may compare unaffected mesh/connectivity quantities with this baseline, but
independent equilibrium, finite-difference, analytical, and dense/sparse checks decide
correctness when results disagree.
