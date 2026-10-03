"""Frozen B3 query policies, fully charged attempts, and terminal audit witnesses."""

from collections.abc import Callable
from time import perf_counter
from typing import Annotated, Literal, cast

import numpy as np
from pydantic import Field, model_validator
from torch import nn

from topolab.b2_5_evaluation import _predict, _raw_uniform
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b3_catalog import CaseId
from topolab.b3_dataset import NonnegativeSeconds
from topolab.b3_training import SEEDS, Recipe
from topolab.baselines import (
    BaselineMetrics,
    NearestNeighborIndex,
    _evaluate_case_density,
    _physics_heuristic_raw_density,
    safe_refinement_metrics,
    validate_refinement_quality,
)
from topolab.experiment import ExperimentCase, project_design_density
from topolab.mesh import generate_structured_hex8
from topolab.problem import ContractModel, TopologyProblem, TopologyResult, solve_problem
from topolab.simp import apply_density_filter, build_density_filter

type QueryMethod = Literal[
    "uniform", "physics_heuristic", "nearest_neighbor", "C", "P", "A", "P_without_S"
]
type QueryRoute = Literal["baseline", "generalist", "specialist", "reject"]
type FailureCode = Literal["setup_error", "projection_error", "refinement_error", "quality_error"]
METHODS: tuple[tuple[QueryMethod, int | None], ...] = (
    ("uniform", None),
    ("physics_heuristic", None),
    ("nearest_neighbor", None),
    *((method, seed) for method in ("C", "P", "A", "P_without_S") for seed in SEEDS),
)


class QueryResourceExceeded(RuntimeError):
    """Resource stops propagate through candidate and fallback attempts."""


class TraceMetric(ContractModel):
    iteration: Annotated[int, Field(strict=True, ge=1, le=360)]
    compliance: Annotated[float, Field(gt=0)]
    volume_fraction: Annotated[float, Field(ge=0, le=1)]
    density_change: NonnegativeSeconds


class TerminalWitness(ContractModel):
    """Full terminal state, scalar trajectory, and at most eleven recent density states."""

    witness_version: Literal["topolab.b3.query-state.v1"] = "topolab.b3.query-state.v1"
    result: TopologyResult
    trace: tuple[TraceMetric, ...]

    @classmethod
    def from_result(cls, result: TopologyResult) -> "TerminalWitness":
        return cls(
            result=result.model_copy(update={"history": result.history[-11:]}),
            trace=tuple(
                TraceMetric(
                    iteration=s.iteration,
                    compliance=s.compliance,
                    volume_fraction=s.volume_fraction,
                    density_change=s.density_change,
                )
                for s in result.history
            ),
        )

    @model_validator(mode="after")
    def validate_trace(self) -> "TerminalWitness":
        if (
            not self.trace
            or tuple(t.iteration for t in self.trace) != tuple(range(1, len(self.trace) + 1))
            or len(self.result.history) != min(11, len(self.trace))
        ):
            raise ValueError("query witness requires a complete trace and exact recent states")
        for state, point in zip(self.result.history, self.trace[-11:], strict=True):
            if (state.iteration, state.compliance, state.volume_fraction, state.density_change) != (
                point.iteration,
                point.compliance,
                point.volume_fraction,
                point.density_change,
            ):
                raise ValueError("recent density states differ from the scalar trajectory")
        last = self.result.history[-1]
        if (
            self.result.design_density != last.design_density
            or self.result.physical_density != last.physical_density
            or self.result.compliance != last.compliance
        ):
            raise ValueError("terminal state differs from the last updated state")
        return self


class AttemptTiming(ContractModel):
    setup_seconds: NonnegativeSeconds = 0
    projection_seconds: NonnegativeSeconds = 0
    refinement_seconds: NonnegativeSeconds = 0
    decision_seconds: NonnegativeSeconds = 0

    @property
    def seconds(self) -> float:
        return sum(
            (
                self.setup_seconds,
                self.projection_seconds,
                self.refinement_seconds,
                self.decision_seconds,
            )
        )


class QueryAttempt(ContractModel):
    succeeded: bool
    failure_code: FailureCode | None = None
    failure_type: str | None = None
    timing: AttemptTiming
    metrics: BaselineMetrics | None = None
    state: TerminalWitness | None = None
    matched_case_id: CaseId | None = None

    @model_validator(mode="after")
    def validate_status(self) -> "QueryAttempt":
        if (
            self.succeeded
            and (self.failure_code is not None or self.failure_type is not None)
            or not self.succeeded
            and (self.failure_code is None or self.failure_type is None)
        ):
            raise ValueError("attempt status differs from its failure record")
        if self.succeeded and (self.metrics is None or self.state is None):
            raise ValueError("successful attempts require audited metrics and state")
        if (
            self.state is not None
            and self.metrics is not None
            and (
                self.metrics.iterations != len(self.state.trace)
                or self.metrics.final_compliance != self.state.result.compliance
            )
        ):
            raise ValueError("attempt metrics differ from the terminal witness")
        return self


class QueryOutcome(ContractModel):
    method: QueryMethod
    seed: Literal[17, 29, 43] | None
    route: QueryRoute
    route_seconds: NonnegativeSeconds = 0
    attempt: QueryAttempt | None
    fallback: QueryAttempt | None = None

    @model_validator(mode="after")
    def validate_method(self) -> "QueryOutcome":
        baseline = self.method in ("uniform", "physics_heuristic", "nearest_neighbor")
        if baseline != (self.seed is None) or baseline != (self.route == "baseline"):
            raise ValueError("query method, seed and route differ")
        if self.route == "reject":
            if self.attempt is not None or self.fallback is None:
                raise ValueError("rejection requires no learned attempt and fresh uniform")
        elif self.attempt is None:
            raise ValueError("non-rejected queries require an attempt")
        elif self.attempt.succeeded and self.fallback is not None:
            raise ValueError("successful attempts cannot have fallback")
        elif not self.attempt.succeeded and self.method != "uniform" and self.fallback is None:
            raise ValueError("failed candidates require a fresh uniform fallback")
        if self.method == "uniform" and self.fallback is not None:
            raise ValueError("mandatory uniform has no fallback")
        return self

    @property
    def operational(self) -> QueryAttempt | None:
        selected = self.fallback if self.fallback is not None else self.attempt
        return selected if selected is not None and selected.succeeded else None

    @property
    def seconds(self) -> float:
        return (
            self.route_seconds
            + (0 if self.attempt is None else self.attempt.timing.seconds)
            + (0 if self.fallback is None else self.fallback.timing.seconds)
        )


def policy_route(case: ExperimentCase, method: QueryMethod) -> QueryRoute:
    if method in ("uniform", "physics_heuristic", "nearest_neighbor"):
        return "baseline"
    if case.problem.loads[0].direction not in (
        "y",
        "z",
    ) or case.problem.mesh.element_counts not in ((12, 6, 3), (24, 12, 6)):
        return "reject"
    if (
        method != "P_without_S"
        and case.problem.mesh.element_counts == (24, 12, 6)
        and case.problem.loads[0].direction == "y"
        and case.problem.optimization.volume_fraction >= 0.55
    ):
        return "specialist"
    return "generalist"


def _attempt(
    case: ExperimentCase,
    method: QueryMethod,
    reference: float | None,
    checkpoint: Callable[[], None],
    model: nn.Module | None = None,
    neighbors: NearestNeighborIndex | None = None,
    refinement: Callable[[ExperimentCase, TopologyResult, Callable[[], None]], TopologyResult]
    | None = None,
) -> QueryAttempt:
    phases = {
        name: 0.0
        for name in (
            "setup_seconds",
            "projection_seconds",
            "refinement_seconds",
            "decision_seconds",
        )
    }
    result = None
    metrics = None
    matched = None
    phase: FailureCode = "setup_error"
    failure_code: FailureCode | None = None
    failure_type = None
    try:
        started = perf_counter()
        try:
            if method == "uniform":
                raw = _raw_uniform(case)
            elif method == "physics_heuristic":
                raw = _physics_heuristic_raw_density(case)
            elif method == "nearest_neighbor":
                if neighbors is None:
                    raise ValueError("B3 nearest-neighbor index is missing")
                match = neighbors.query(case)
                raw, matched = match.design_density, match.case_id
            else:
                if model is None:
                    raise ValueError("B3 selected model is missing")
                raw = _predict(case, model, encoder=encode_vector_load_case)
        finally:
            phases["setup_seconds"] = perf_counter() - started
        phase = "projection_error"
        started = perf_counter()
        try:
            projected = project_design_density(case, raw)
        finally:
            phases["projection_seconds"] = perf_counter() - started
        phase = "refinement_error"
        started = perf_counter()
        try:
            payload = case.problem.model_dump(mode="json")
            payload["initial_density"] = tuple(float(v) for v in projected.design_density)
            result = solve_problem(
                TopologyProblem.model_validate(payload),
                termination_policy="physical_plateau",
                iteration_callback=lambda _: checkpoint(),
            )
            if refinement is not None:
                result = refinement(case, result, checkpoint)
        finally:
            phases["refinement_seconds"] = perf_counter() - started
        phase = "quality_error"
        started = perf_counter()
        try:
            metrics = validate_refinement_quality(case, result, reference)
        finally:
            phases["decision_seconds"] = perf_counter() - started
    except QueryResourceExceeded:
        raise
    except Exception as error:
        failure_code, failure_type = phase, type(error).__name__
        if result is not None:
            diagnostic_start = perf_counter()
            try:
                metrics = safe_refinement_metrics(case, result)
            except (ValueError, RuntimeError, ArithmeticError):
                metrics = None
            phases["decision_seconds"] += perf_counter() - diagnostic_start
    state = None
    if result is not None:
        try:
            state = TerminalWitness.from_result(result)
        except ValueError:
            if failure_code is None:
                raise
    return QueryAttempt(
        succeeded=failure_code is None,
        failure_code=failure_code,
        failure_type=failure_type,
        timing=AttemptTiming(**phases),
        metrics=metrics,
        state=state,
        matched_case_id=matched,
    )


def evaluate_query(
    case: ExperimentCase,
    method: QueryMethod,
    seed: int | None,
    reference: float | None,
    models: dict[tuple[Recipe, int], nn.Module],
    neighbors: NearestNeighborIndex | None,
    checkpoint: Callable[[], None],
    *,
    refinement: Callable[[ExperimentCase, TopologyResult, Callable[[], None]], TopologyResult]
    | None = None,
) -> QueryOutcome:
    checkpoint()
    started = perf_counter()
    route = policy_route(case, method)
    model = None
    if route in ("generalist", "specialist"):
        recipe = cast(
            Recipe, "S" if route == "specialist" else ("P" if method == "P_without_S" else method)
        )
        if seed not in SEEDS:
            raise ValueError("learned queries require a frozen seed")
        model = models[(recipe, seed)]
    route_seconds = perf_counter() - started
    attempt = None
    if route != "reject":
        if refinement is not None and method == "P" and route == "generalist":
            attempt = _attempt(
                case, method, reference, checkpoint, model, neighbors, refinement=refinement
            )
        else:
            attempt = _attempt(case, method, reference, checkpoint, model, neighbors)
    fallback = None
    if route == "reject" or (attempt is not None and not attempt.succeeded and method != "uniform"):
        fallback = _attempt(case, "uniform", reference, checkpoint)
        if fallback.succeeded and reference is not None:
            assert fallback.metrics is not None
            decision_start = perf_counter()
            matched = np.isclose(fallback.metrics.final_compliance, reference, rtol=1e-9, atol=0)
            extra = perf_counter() - decision_start
            fallback = fallback.model_copy(
                update={
                    "timing": fallback.timing.model_copy(
                        update={"decision_seconds": fallback.timing.decision_seconds + extra}
                    )
                }
            )
            if not matched:
                fallback = fallback.model_copy(
                    update={
                        "succeeded": False,
                        "failure_code": "quality_error",
                        "failure_type": "UniformReferenceMismatch",
                    }
                )
    checkpoint()
    return QueryOutcome.model_validate(
        {
            "method": method,
            "seed": seed,
            "route": route,
            "route_seconds": route_seconds,
            "attempt": attempt,
            "fallback": fallback,
        }
    )


def audit_witness(
    case: ExperimentCase, witness: TerminalWitness, reference: float | None, *, accepted: bool
) -> BaselineMetrics:
    """Reconstruct terminal quality from compact density evidence, without rerunning refinement."""
    witness = TerminalWitness.model_validate(witness.model_dump(mode="json"))
    result = witness.result
    settings, mesh_spec = case.problem.optimization, case.problem.mesh
    count = int(np.prod(mesh_spec.element_counts))
    dofs = 3 * int(np.prod(np.asarray(mesh_spec.element_counts) + 1))
    if (
        len(result.displacements) != dofs
        or len(result.reactions) != dofs
        or not np.all(np.isfinite((*result.displacements, *result.reactions)))
    ):
        raise ValueError("query terminal DOF vectors differ from the finite mesh state")
    density_filter = build_density_filter(
        generate_structured_hex8(*mesh_spec.element_counts, lengths=mesh_spec.lengths),
        settings.filter_radius,
    )
    previous = None
    changes = []
    for state in result.history:
        design, physical = np.asarray(state.design_density), np.asarray(state.physical_density)
        if (
            design.shape != (count,)
            or physical.shape != (count,)
            or not np.all(np.isfinite(design))
            or not np.all(np.isfinite(physical))
            or np.any(design < settings.minimum_density)
            or np.any(design > 1)
        ):
            raise ValueError("query witness density is outside the finite mesh bounds")
        if not np.array_equal(
            apply_density_filter(density_filter, design), physical
        ) or not np.isclose(np.mean(physical), state.volume_fraction, rtol=0, atol=1e-12):
            raise ValueError("query witness physical density or volume differs from its design")
        if previous is not None:
            if float(np.max(np.abs(design - previous[0]))) != state.density_change:
                raise ValueError("query witness design change differs from its updated states")
            changes.append(float(np.max(np.abs(physical - previous[1]))))
        previous = design, physical
    metrics = BaselineMetrics(
        iterations=len(witness.trace),
        final_compliance=result.compliance,
        physical_volume_error=abs(
            float(np.mean(result.physical_density)) - settings.volume_fraction
        ),
    )
    if not np.isclose(
        _evaluate_case_density(case, np.asarray(result.physical_density)),
        result.compliance,
        rtol=1e-9,
        atol=0,
    ):
        raise ValueError("query witness compliance failed independent re-solve")
    if accepted:
        last = result.history[-1]
        plateau = False
        if len(result.history) == 11:
            relative = (result.history[0].compliance - last.compliance) / result.history[
                0
            ].compliance
            plateau = max(changes) <= settings.convergence_tolerance and 0 <= relative <= 2e-4
        if (
            not result.converged
            or metrics.iterations > settings.max_iterations
            or metrics.physical_volume_error > 0.005
            or (last.density_change > settings.convergence_tolerance and not plateau)
            or (reference is not None and result.compliance > 1.001 * reference)
        ):
            raise ValueError("accepted query witness violates frozen terminal quality")
    return metrics
