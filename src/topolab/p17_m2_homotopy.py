"""Opt-in fixed penalty schedule over TopoLab's unchanged FEM/filter/OC core.

No model or data access occurs here. Public small-mesh tests exercise the same
driver; query dispatch, not this numerical function, fixes H's activation domain.
"""

from collections import deque
from collections.abc import Callable
from functools import partial
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from pydantic import ConfigDict, Field

from topolab.baselines import _case_system
from topolab.experiment import ExperimentCase
from topolab.problem import ContractModel, IterationResult, TopologyResult
from topolab.simp import (
    apply_density_filter,
    backpropagate_density_gradient,
    build_density_filter,
    evaluate_compliance,
    optimality_criteria_update,
)

WITNESS_VERSION = "topolab.v2.m2-homotopy-witness.v1"


class PhasePoint(ContractModel):
    iteration: int = Field(ge=0, le=360, strict=True)
    phase_iteration: int = Field(ge=0, le=360, strict=True)
    penalty: Literal[1, 2, 3]
    compliance: float = Field(gt=0)
    volume_fraction: float = Field(ge=0, le=1)
    density_change: float = Field(ge=0)
    physical_change: float = Field(ge=0)


class PhaseState(PhasePoint):
    design_density: tuple[float, ...]
    physical_density: tuple[float, ...]


class HomotopyWitness(ContractModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        allow_inf_nan=False,
        serialize_by_alias=True,
    )
    schema_version: Literal["topolab.v2.m2-homotopy-witness.v1"] = Field(
        default="topolab.v2.m2-homotopy-witness.v1",
        alias="schema",
    )
    active: bool
    initial: PhaseState
    prefix: tuple[PhaseState, ...]
    transitions: tuple[PhaseState, ...]
    trace: tuple[PhasePoint, ...]
    recent: tuple[PhaseState, ...]
    result: TopologyResult
    fem_solves: int = Field(gt=0, strict=True)


def h_active(case: ExperimentCase, route: str) -> bool:
    """The owner-fixed activation; there is no tunable H policy."""
    return (
        route == "generalist"
        and case.problem.mesh.element_counts == (24, 12, 6)
        and case.problem.loads[0].direction == "y"
        and case.problem.optimization.volume_fraction < 0.55
    )


def solve_phases(
    case: ExperimentCase,
    initial_density: NDArray[np.float64],
    *,
    active: bool,
    checkpoint: Callable[[], None],
) -> HomotopyWitness:
    """Fixed 8/8/p3 or original plain-p3 updates, never three early-stop calls.

    All FEM analyses are counted. MemoryError and checkpoint failures propagate;
    no query fallback or resource acceptance is decided by this function.
    """
    settings, material = case.problem.optimization, case.problem.material
    if (
        settings.penalty != 3
        or settings.convergence_tolerance != 0.01
        or settings.max_iterations > 360
        or active
        and settings.max_iterations < 17
    ):
        raise ValueError("fixed H requires p3/.01/<=360 and at least17 updates when active")
    checkpoint()
    mesh, loads, constraints = _case_system(case)
    count = int(np.prod(case.problem.mesh.element_counts))
    design = np.asarray(initial_density, dtype=np.float64).copy()
    if (
        design.shape != (count,)
        or not np.all(np.isfinite(design))
        or np.any(design < settings.minimum_density)
        or np.any(design > 1)
    ):
        raise ValueError("initial density is outside the fixed finite mesh domain")
    filt = build_density_filter(mesh, settings.filter_radius)
    volume_gradient = backpropagate_density_gradient(filt, np.full(count, 1.0 / count))
    physical = apply_density_filter(filt, design)
    analyze = partial(
        evaluate_compliance,
        mesh,
        loads=loads,
        constrained_dofs=constraints,
        solid_modulus=material.solid_modulus,
        minimum_modulus=material.minimum_modulus,
        poisson_ratio=material.poisson_ratio,
    )
    penalty: Literal[1, 2, 3] = 1 if active else 3
    fem_solves = 1
    analysis = analyze(physical, penalty=penalty)

    def state(iteration: int, phase_iteration: int, dc: float = 0, pc: float = 0) -> PhaseState:
        return PhaseState(
            iteration=iteration,
            phase_iteration=phase_iteration,
            penalty=penalty,
            compliance=analysis.compliance,
            volume_fraction=float(np.mean(physical)),
            density_change=dc,
            physical_change=pc,
            design_density=tuple(float(v) for v in design),
            physical_density=tuple(float(v) for v in physical),
        )

    initial = state(0, 0)
    prefix: list[PhaseState] = []
    transitions: list[PhaseState] = []
    trace: list[PhasePoint] = []
    recent: deque[PhaseState] = deque(maxlen=11)
    converged = False
    phase_iteration = 0
    for iteration in range(1, settings.max_iterations + 1):
        checkpoint()
        if active and iteration in (9, 17):
            penalty = 2 if iteration == 9 else 3
            analysis = analyze(physical, penalty=penalty)
            fem_solves += 1
            phase_iteration = 0
            transitions.append(state(iteration - 1, 0))
        objective = backpropagate_density_gradient(filt, analysis.sensitivity)
        updated = optimality_criteria_update(
            design,
            objective,
            volume_gradient,
            filt,
            volume_fraction=settings.volume_fraction,
            minimum_density=settings.minimum_density,
            move_limit=settings.move_limit,
        )
        dc = float(np.max(np.abs(updated - design)))
        updated_physical = apply_density_filter(filt, updated)
        pc = float(np.max(np.abs(updated_physical - physical)))
        design, physical = updated, updated_physical
        analysis = analyze(physical, penalty=penalty)
        fem_solves += 1
        phase_iteration += 1
        current = state(iteration, phase_iteration, dc, pc)
        trace.append(
            PhasePoint.model_validate(
                current.model_dump(
                    exclude={
                        "design_density",
                        "physical_density",
                    }
                )
            )
        )
        if penalty != 3:
            prefix.append(current)
        else:
            recent.append(current)
            window = tuple(recent)
            plateau = (
                phase_iteration >= 11
                and len(window) == 11
                and max(s.physical_change for s in window[1:]) <= 0.01
                and 0
                <= (window[0].compliance - window[-1].compliance) / window[0].compliance
                <= 2e-4
            )
            converged = dc <= 0.01 or plateau
        checkpoint()
        if converged:
            break
    # Fresh p3 terminal solve belongs to the driver, even for a nonconverged stop.
    checkpoint()
    analysis = analyze(physical, penalty=3)
    fem_solves += 1
    result = TopologyResult(
        design_density=tuple(float(v) for v in design),
        physical_density=tuple(float(v) for v in physical),
        compliance=analysis.compliance,
        displacements=tuple(float(v) for v in analysis.displacements),
        reactions=tuple(float(v) for v in analysis.reactions),
        history=tuple(
            IterationResult.model_validate(
                s.model_dump(
                    exclude={
                        "phase_iteration",
                        "penalty",
                        "physical_change",
                    }
                )
            )
            for s in recent
        ),
        converged=converged,
    )
    checkpoint()
    return HomotopyWitness(
        active=active,
        initial=initial,
        prefix=tuple(prefix),
        transitions=tuple(transitions),
        trace=tuple(trace),
        recent=tuple(recent),
        result=result,
        fem_solves=fem_solves,
    )


def quality(witness: HomotopyWitness, reference: float | None, volume: float) -> bool:
    """Candidate decision only; the separately authored auditor reconstructs it."""
    if reference is not None and (not np.isfinite(reference) or reference <= 0):
        raise ValueError("reference must be finite positive")
    return bool(
        witness.result.converged
        and witness.trace
        and abs(float(np.mean(witness.result.physical_density)) - volume) <= 0.005
        and (reference is None or witness.result.compliance <= 1.001 * reference)
    )
