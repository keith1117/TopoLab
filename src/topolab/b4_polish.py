"""Candidate-only fixed continuation; the anchored uniform solver is unchanged."""

from collections.abc import Callable
from functools import partial

import numpy as np

from topolab.baselines import _case_system
from topolab.experiment import ExperimentCase
from topolab.problem import IterationResult, TopologyResult
from topolab.simp import (
    apply_density_filter,
    backpropagate_density_gradient,
    build_density_filter,
    evaluate_compliance,
    optimality_criteria_update,
)

POLISH_VERSION = "topolab.b4_10.large-y-post-plateau.v1"
POLISH_UPDATES = 20


def plateau(result: TopologyResult, tolerance: float) -> bool:
    """The existing ten-update physical signal, independent of any reference."""
    states = result.history[-11:]
    if len(states) != 11:
        return False
    physical = np.asarray([s.physical_density for s in states])
    improvement = (states[0].compliance - states[-1].compliance) / states[0].compliance
    return bool(np.max(np.abs(np.diff(physical, axis=0))) <= tolerance and 0 <= improvement <= 2e-4)


def qualifies(case: ExperimentCase, result: TopologyResult) -> bool:
    settings = case.problem.optimization
    return (
        case.problem.mesh.element_counts == (24, 12, 6)
        and case.problem.loads[0].direction == "y"
        and settings.volume_fraction < 0.55
        and result.converged
        and bool(result.history)
        # Design-change has precedence in the anchored solver's stop condition.
        and result.history[-1].density_change > settings.convergence_tolerance
        and plateau(result, settings.convergence_tolerance)
    )


def polish(
    case: ExperimentCase, result: TopologyResult, checkpoint: Callable[[], None]
) -> TopologyResult:
    """Append exactly twenty OC updates when the own-state signal qualifies.

    The total case cap is retained. An incomplete polish is nonconverged and
    therefore pays the ordinary quality failure/fallback. No intermediate stop
    or matched-reference compliance is consulted during continuation.
    """
    if not qualifies(case, result):
        return result
    problem, settings = case.problem, case.problem.optimization
    mesh, loads, constraints = _case_system(case)
    density_filter = build_density_filter(mesh, settings.filter_radius)
    design = np.asarray(result.design_density, dtype=np.float64)
    physical = np.asarray(result.physical_density, dtype=np.float64)
    analyze = partial(
        evaluate_compliance,
        solid_modulus=problem.material.solid_modulus,
        minimum_modulus=problem.material.minimum_modulus,
        poisson_ratio=problem.material.poisson_ratio,
        penalty=settings.penalty,
    )
    checkpoint()
    analysis = analyze(mesh, physical, loads, constraints)
    if analysis.compliance != result.compliance:
        raise ValueError("polish re-solve differs from its input terminal state")
    volume_gradient = backpropagate_density_gradient(
        density_filter, np.full(len(design), 1.0 / len(design))
    )
    history = list(result.history)
    first = len(history)
    for iteration in range(first + 1, min(first + POLISH_UPDATES, settings.max_iterations) + 1):
        checkpoint()
        objective = backpropagate_density_gradient(density_filter, analysis.sensitivity)
        updated = optimality_criteria_update(
            design,
            objective,
            volume_gradient,
            density_filter,
            volume_fraction=settings.volume_fraction,
            minimum_density=settings.minimum_density,
            move_limit=settings.move_limit,
        )
        change = float(np.max(np.abs(updated - design)))
        physical = apply_density_filter(density_filter, updated)
        analysis = analyze(mesh, physical, loads, constraints)
        history.append(
            IterationResult(
                iteration=iteration,
                compliance=analysis.compliance,
                volume_fraction=float(np.mean(physical)),
                density_change=change,
                design_density=tuple(float(v) for v in updated),
                physical_density=tuple(float(v) for v in physical),
            )
        )
        design = updated
        checkpoint()
    terminal = TopologyResult(
        design_density=tuple(float(v) for v in design),
        physical_density=tuple(float(v) for v in physical),
        compliance=analysis.compliance,
        displacements=tuple(float(v) for v in analysis.displacements),
        reactions=tuple(float(v) for v in analysis.reactions),
        history=tuple(history),
        converged=False,
    )
    completed = len(history) - first == POLISH_UPDATES
    converged = completed and (
        history[-1].density_change <= settings.convergence_tolerance
        or plateau(terminal, settings.convergence_tolerance)
    )
    return terminal.model_copy(update={"converged": converged})
