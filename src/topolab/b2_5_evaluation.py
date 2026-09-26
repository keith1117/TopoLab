"""Version-matched B2.5 validation with fully charged uniform fallback."""

from collections.abc import Callable
from time import perf_counter
from typing import Any, Literal

import numpy as np
import torch
from numpy.typing import NDArray

from topolab.b2_5_training import SEEDS, B25Arm, B25Sample
from topolab.baselines import (
    NearestNeighborIndex,
    _physics_heuristic_raw_density,
    safe_refinement_metrics,
    validate_refinement_quality,
)
from topolab.experiment import EncodedCase, ExperimentCase, encode_case, project_design_density
from topolab.problem import TopologyProblem, TopologyResult, solve_problem
from topolab.training import WarmStartCNN

type B25Method = Literal[
    "uniform", "physics_heuristic", "nearest_neighbor", "control", "candidate"
]


def build_shape_neighbors(
    train: tuple[B25Sample, ...]
) -> dict[tuple[int, int, int], NearestNeighborIndex]:
    """Build independent input/design indexes from training labels only."""

    result: dict[tuple[int, int, int], NearestNeighborIndex] = {}
    for shape in ((3, 6, 12), (6, 12, 24)):
        selected = tuple(sample for sample in train if sample.shape == shape)
        if not selected or any(sample.split != "train" for sample in selected):
            raise ValueError("nearest-neighbor index requires both training buckets")
        result[shape] = NearestNeighborIndex(
            case_ids=tuple(sample.case.case_id for sample in selected),
            input_tensors=np.stack([sample.inputs.numpy() for sample in selected]),
            design_tensors=np.stack([sample.design.numpy() for sample in selected]),
        )
    return result


def _raw_uniform(case: ExperimentCase) -> NDArray[np.float32]:
    nx, ny, nz = case.problem.mesh.element_counts
    return np.full(
        (1, nz, ny, nx), case.problem.optimization.volume_fraction, dtype=np.float32
    )


def _predict(
    case: ExperimentCase,
    model: WarmStartCNN,
    *,
    encoder: Callable[[ExperimentCase], EncodedCase] = encode_case,
) -> NDArray[np.float32]:
    inputs = torch.from_numpy(encoder(case).input_tensor.copy()).unsqueeze(0)
    model.eval()
    with torch.no_grad():
        prediction = model(inputs)
    nx, ny, nz = case.problem.mesh.element_counts
    if prediction.shape != (1, 1, nz, ny, nx):
        raise ValueError("B2.5 model prediction has the wrong shape")
    if prediction.device.type != "cpu" or prediction.dtype != torch.float32:
        raise ValueError("B2.5 prediction must be CPU float32")
    if (
        not torch.isfinite(prediction).all()
        or torch.any(prediction < 0)
        or torch.any(prediction > 1)
    ):
        raise ValueError("B2.5 prediction is not a finite design density")
    return np.asarray(prediction.squeeze(0).detach().numpy(), dtype=np.float32).copy()


def _solve(case: ExperimentCase, design: NDArray[np.float64]) -> TopologyResult:
    payload = case.problem.model_dump(mode="json")
    payload["initial_density"] = tuple(float(value) for value in design)
    return solve_problem(
        TopologyProblem.model_validate(payload), termination_policy="physical_plateau"
    )


def _attempt(
    case: ExperimentCase,
    *,
    method: B25Method,
    reference_compliance: float | None,
    model: WarmStartCNN | None = None,
    neighbors: NearestNeighborIndex | None = None,
    encoder: Callable[[ExperimentCase], EncodedCase] = encode_case,
    raw_transform: (
        Callable[[ExperimentCase, NDArray[np.float32]], NDArray[np.float32]] | None
    ) = None,
) -> dict[str, Any]:
    phases = {
        "setup_seconds": 0.0,
        "projection_seconds": 0.0,
        "refinement_seconds": 0.0,
        "decision_seconds": 0.0,
        "fallback_seconds": 0.0,
    }
    result: TopologyResult | None = None
    matched_case_id: str | None = None
    phase = "setup_error"
    try:
        started = perf_counter()
        try:
            if method == "uniform":
                raw = _raw_uniform(case)
            elif method == "physics_heuristic":
                raw = _physics_heuristic_raw_density(case)
            elif method == "nearest_neighbor":
                if neighbors is None:
                    raise ValueError("B2.5 nearest neighbor index is missing")
                match = neighbors.query(case)
                raw = match.design_density
                matched_case_id = match.case_id
            else:
                if model is None:
                    raise ValueError("B2.5 learned model is missing")
                raw = _predict(case, model, encoder=encoder)
                if raw_transform is not None:
                    raw = raw_transform(case, raw)
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
            result = _solve(case, projected.design_density)
        finally:
            phases["refinement_seconds"] = perf_counter() - started

        phase = "quality_error"
        started = perf_counter()
        try:
            metrics = validate_refinement_quality(case, result, reference_compliance)
        finally:
            phases["decision_seconds"] = perf_counter() - started
    except Exception as error:
        return {
            "succeeded": False,
            "failure_code": phase,
            "failure_type": type(error).__name__,
            "candidate": (
                None if result is None else _safe_metrics(case, result)
            ),
            "matched_case_id": matched_case_id,
            "timing": phases,
        }
    return {
        "succeeded": True,
        "failure_code": None,
        "candidate": metrics.model_dump(mode="json"),
        "matched_case_id": matched_case_id,
        "timing": phases,
    }


def _safe_metrics(case: ExperimentCase, result: TopologyResult) -> dict[str, Any] | None:
    try:
        safe = safe_refinement_metrics(case, result)
        return None if safe is None else safe.model_dump(mode="json")
    except (ValueError, RuntimeError, ArithmeticError):
        return None


def _charged_result(
    case: ExperimentCase,
    method: B25Method,
    seed: int | None,
    reference: dict[str, Any],
    *,
    model: WarmStartCNN | None = None,
    neighbors: NearestNeighborIndex | None = None,
    encoder: Callable[[ExperimentCase], EncodedCase] = encode_case,
    raw_transform: (
        Callable[[ExperimentCase, NDArray[np.float32]], NDArray[np.float32]] | None
    ) = None,
) -> dict[str, Any]:
    reference_compliance = float(reference["operational"]["final_compliance"])
    attempt = _attempt(
        case,
        method=method,
        reference_compliance=reference_compliance,
        model=model,
        neighbors=neighbors,
        encoder=encoder,
        raw_transform=raw_transform,
    )
    phases = attempt["timing"]
    if attempt["succeeded"]:
        operational = attempt["candidate"]
    else:
        fallback = _attempt(case, method="uniform", reference_compliance=None)
        if not fallback["succeeded"]:
            raise ValueError("B2.5 fresh uniform fallback failed")
        operational = fallback["candidate"]
        if not np.isclose(
            operational["final_compliance"], reference_compliance,
            rtol=1e-9, atol=0.0,
        ):
            raise ValueError("B2.5 uniform fallback differs from matched reference")
        phases["fallback_seconds"] = sum(fallback["timing"].values())
    return {
        "case_id": case.case_id,
        "method": method,
        "seed": seed,
        "succeeded": attempt["succeeded"],
        "failure_code": attempt["failure_code"],
        "failure_type": attempt.get("failure_type"),
        "fallback_used": not attempt["succeeded"],
        "candidate": attempt["candidate"],
        "operational": operational,
        "matched_case_id": attempt["matched_case_id"],
        "uniform_reference_compliance": reference_compliance,
        "timing": {**phases, "end_to_end_seconds": sum(phases.values())},
        "paired_time_ratio": sum(phases.values()) / reference["timing"]["end_to_end_seconds"],
    }


def evaluate_b25_case(
    case: ExperimentCase,
    *,
    models: dict[tuple[B25Arm, int], WarmStartCNN],
    neighbors: NearestNeighborIndex,
) -> tuple[dict[str, Any], ...]:
    """Evaluate one complete nine-method, version-matched physical case."""

    if set(models) != {(arm, seed) for arm in ("control", "candidate") for seed in SEEDS}:
        raise ValueError("B2.5 evaluation requires all six frozen models")
    first = _attempt(case, method="uniform", reference_compliance=None)
    if not first["succeeded"]:
        raise ValueError("B2.5 mandatory uniform reference failed")
    phases = first["timing"]
    reference = {
        "case_id": case.case_id,
        "method": "uniform",
        "seed": None,
        "succeeded": True,
        "failure_code": None,
        "fallback_used": False,
        "candidate": first["candidate"],
        "operational": first["candidate"],
        "matched_case_id": None,
        "uniform_reference_compliance": first["candidate"]["final_compliance"],
        "timing": {**phases, "end_to_end_seconds": sum(phases.values())},
        "paired_time_ratio": 1.0,
    }
    results = [reference]
    for method in ("physics_heuristic", "nearest_neighbor"):
        results.append(
            _charged_result(
                case, method, None, reference,
                neighbors=neighbors if method == "nearest_neighbor" else None,
            )
        )
    for arm in ("control", "candidate"):
        for seed in SEEDS:
            results.append(
                _charged_result(
                    case, arm, seed, reference, model=models[(arm, seed)]
                )
            )
    if len(results) != 9:
        raise ValueError("B2.5 case must preserve nine method outcomes")
    return tuple(results)
