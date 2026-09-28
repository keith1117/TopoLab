"""Opt-in B2.15 position-aware route for audited development checkpoints."""

from topolab.b2_13_routing import Route
from topolab.experiment import ExperimentCase
from topolab.problem import FixedFaceSupportDefinition, PointLoadDefinition


def route_case(case: ExperimentCase) -> Route:
    """Choose one frozen model using public workload metadata only."""

    problem = case.problem
    counts = problem.mesh.element_counts
    if (
        counts not in ((12, 6, 3), (24, 12, 6))
        or problem.mesh.lengths != (12.0, 6.0, 3.0)
        or problem.material.solid_modulus != 1000.0
        or problem.material.minimum_modulus != 1.0
        or problem.material.poisson_ratio != 0.3
        or len(problem.supports) != 1
        or not isinstance(problem.supports[0], FixedFaceSupportDefinition)
        or problem.supports[0].axis != "x"
        or problem.supports[0].side != "min"
        or problem.supports[0].directions != ("x", "y", "z")
        or len(problem.loads) != 1
        or not isinstance(problem.loads[0], PointLoadDefinition)
        or problem.loads[0].direction not in ("y", "z")
        or problem.loads[0].magnitude != -1.0
        or problem.optimization.filter_radius != 1.5
        or problem.optimization.penalty != 3.0
        or problem.optimization.minimum_density != 0.05
        or problem.optimization.move_limit != 0.2
        or problem.optimization.convergence_tolerance != 0.01
        or problem.optimization.max_iterations != 360
        or not 0.30 <= problem.optimization.volume_fraction <= 0.61
    ):
        return "uniform_reject"
    nx, ny, nz = counts
    node = problem.loads[0].node
    x = node % (nx + 1)
    y = node // (nx + 1) % (ny + 1)
    z = node // ((nx + 1) * (ny + 1))
    if x != nx or not 0 < y < ny or not 0 < z < nz:
        return "uniform_reject"

    volume = problem.optimization.volume_fraction
    direction = problem.loads[0].direction
    if nx == 12:
        return "context_43"
    lower_z = 3 * z <= nz
    if direction == "y":
        if volume >= 0.55 and lower_z:
            return "uniform_reject"
        return "context_17"
    if lower_z and volume < 0.55:
        return "context_43"
    return "vector_29"
