"""Opt-in B2.13 workload routing for audited development checkpoints."""

from typing import Literal

from topolab.experiment import ExperimentCase
from topolab.problem import FixedFaceSupportDefinition, PointLoadDefinition

type Route = Literal["vector_29", "context_17", "context_43", "uniform_reject"]


def route_case(case: ExperimentCase) -> Route:
    """Select a frozen model from public case metadata, or safely reject."""

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
        or problem.loads[0].node % (counts[0] + 1) != counts[0]
        or not 0.30 <= problem.optimization.volume_fraction <= 0.61
        or problem.optimization.filter_radius != 1.5
        or problem.optimization.penalty != 3.0
        or problem.optimization.minimum_density != 0.05
        or problem.optimization.move_limit != 0.2
        or problem.optimization.convergence_tolerance != 0.01
        or problem.optimization.max_iterations != 360
    ):
        return "uniform_reject"
    direction = problem.loads[0].direction
    if counts == (12, 6, 3):
        return "vector_29" if direction == "y" else "context_17"
    if direction == "z":
        return "vector_29"
    return (
        "uniform_reject" if problem.optimization.volume_fraction >= 0.55
        else "context_43"
    )
