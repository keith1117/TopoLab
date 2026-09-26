"""B2.6 frozen trajectory-target fitting and fresh development screen."""

from __future__ import annotations

import argparse
import json
import resource
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any, Literal

import numpy as np
import torch
from b2_4_materialize_labels import plan_payload as b24_plan_payload
from b2_4_materialize_labels import select_cases as b24_cases
from b2_5_prototype import (
    DATA_INDEX_SHA256,
    DATA_PLAN_SHA256,
    atomic_write,
    canonical_bytes,
    read_data_index,
    sha256,
    source_snapshot,
)
from b2_5_prototype import (
    _read_checkpoint as read_b25_checkpoint,
)
from b2_5_prototype import (
    _read_fit_index as read_b25_fits,
)
from b2_5_prototype import (
    load_samples as load_b24_samples,
)
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import (
    _attempt,
    _charged_result,
    _solve,
    build_shape_neighbors,
)
from topolab.b2_6_trajectory import (
    SEEDS,
    TARGET_UPDATE,
    TrajectoryFit,
    TrajectorySample,
    TrajectoryTarget,
    capture_uniform_target,
    fit_trajectory_seed,
)
from topolab.baselines import validate_refinement_quality
from topolab.experiment import ExperimentCase, project_design_density
from topolab.m2_dataset import build_m2_case_catalog
from topolab.mesh import generate_structured_hex8
from topolab.problem import (
    FixedFaceSupportDefinition,
    MaterialDefinition,
    MeshDefinition,
    OptimizationDefinition,
    PointLoadDefinition,
    TopologyProblem,
)
from topolab.simp import apply_density_filter, build_density_filter
from topolab.training import WarmStartCNN

PLAN_VERSION = "topolab.b2_6.trajectory.v1"
EXPECTED_PLAN_SHA256 = "e783f4b8e74b08b1855ea62b9c69dcee9fc812e38786561d93c25ef38fa9a8d8"
B25_FIT_SHA256 = "a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53"
B25_CONTROL43_SHA256 = "d82b7895355c1f73cde5b80d6328bc31c43c58cd7b1580974a590ef42bce0f4d"
VOLUMES = (0.225, 0.375, 0.525)
CAPTURE_CAP = 7_200.0
FIT_CAP = 7_200.0
SCREEN_CAP = 14_400.0
MAX_RSS = 2_147_483_648
type B26Split = Literal["train", "validation", "screen"]


def _peak_rss() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def _small_case(volume: float, direction: Literal["y", "z"], y: int, z: int) -> ExperimentCase:
    nx, ny, _nz = (12, 6, 3)
    node = nx + (nx + 1) * (y + (ny + 1) * z)
    return ExperimentCase.from_problem(
        TopologyProblem(
            mesh=MeshDefinition(element_counts=(12, 6, 3), lengths=(12.0, 6.0, 3.0)),
            material=MaterialDefinition(
                solid_modulus=1000.0, minimum_modulus=1.0, poisson_ratio=0.3
            ),
            supports=(FixedFaceSupportDefinition(axis="x", side="min"),),
            loads=(PointLoadDefinition(node=node, direction=direction, magnitude=-1.0),),
            optimization=OptimizationDefinition(
                volume_fraction=volume,
                filter_radius=1.5,
                penalty=3.0,
                minimum_density=0.05,
                move_limit=0.2,
                convergence_tolerance=0.01,
                max_iterations=240,
            ),
        )
    )


def cohorts() -> dict[B26Split, tuple[ExperimentCase, ...]]:
    """Select only old train definitions and two new, disjoint development cohorts."""

    sources = b24_cases()
    if b24_plan_payload(sources)["plan_sha256"] != DATA_PLAN_SHA256:
        raise ValueError("B2.4 metadata changed")
    train = tuple(
        sorted(
            (item.case for item in sources if item.source.split == "train"),
            key=lambda case: case.case_id,
        )
    )

    def new_cases(y: int, z: int) -> tuple[ExperimentCase, ...]:
        selected: list[ExperimentCase] = []
        for volume in VOLUMES:
            for direction in ("y", "z"):
                small = _small_case(volume, direction, y, z)
                selected.extend((small, scaled_case(small)))
        return tuple(sorted(selected, key=lambda case: case.case_id))

    validation = new_cases(2, 1)
    screen = new_cases(4, 2)
    ids = [case.case_id for case in (*train, *validation, *screen)]
    old_ids = {item.case.case_id for item in sources}
    m2_ids = {case.case_id for case in build_m2_case_catalog().cases}
    if (
        len(train) != 468
        or len(validation) != 12
        or len(screen) != 12
        or len(set(ids)) != 492
        or any(case.case_id in old_ids | m2_ids for case in (*validation, *screen))
    ):
        raise ValueError("B2.6 cohort identity or exposure boundary changed")
    for partition in (validation, screen):
        counts = Counter(
            (case.problem.mesh.element_counts, case.problem.loads[0].direction)
            for case in partition
        )
        if counts != {
            ((12, 6, 3), "y"): 3,
            ((12, 6, 3), "z"): 3,
            ((24, 12, 6), "y"): 3,
            ((24, 12, 6), "z"): 3,
        }:
            raise ValueError("B2.6 cohort strata changed")
    return {"train": train, "validation": validation, "screen": screen}


def plan_payload(groups: dict[B26Split, tuple[ExperimentCase, ...]]) -> dict[str, Any]:
    identity = {
        "plan_version": PLAN_VERSION,
        "source_data_index_sha256": DATA_INDEX_SHA256,
        "source_plan_sha256": DATA_PLAN_SHA256,
        "b25_fit_index_sha256": B25_FIT_SHA256,
        "b25_control43_checkpoint_sha256": B25_CONTROL43_SHA256,
        "target_update": TARGET_UPDATE,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 240,
        "seeds": list(SEEDS),
        "validation_volumes": list(VOLUMES),
        "training_case_ids": [case.case_id for case in groups["train"]],
        "validation_case_ids": [case.case_id for case in groups["validation"]],
        "screen_case_ids": [case.case_id for case in groups["screen"]],
        "capture_cap_seconds": CAPTURE_CAP,
        "fit_cap_seconds": FIT_CAP,
        "screen_cap_seconds": SCREEN_CAP,
        "max_rss_bytes": MAX_RSS,
        "screen_methods": [
            "uniform",
            "physics_heuristic",
            "nearest_neighbor",
            "control_43",
            *[f"trajectory_{seed}" for seed in SEEDS],
            "trajectory_oracle",
        ],
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _external_root(repository: Path, requested: Path) -> Path:
    root = requested.resolve()
    if root == repository or root.is_relative_to(repository):
        raise ValueError("B2.6 artifacts must stay outside the repository")
    return root


def _index(root: Path, name: str, context: dict[str, Any], maximum: int) -> dict[str, Any]:
    path = root / name
    if not path.exists():
        return {"context": context, "rows": [], "elapsed_seconds": 0.0, "peak_rss_bytes": 0}
    index: dict[str, Any] = json.loads(path.read_bytes())
    if index.get("context") != context or len(index.get("rows", [])) > maximum:
        raise ValueError(f"B2.6 {name} has a different frozen context or population")
    return index


def _target_path(root: Path, digest: str) -> Path:
    return root / "targets" / f"{digest}.json"


def _target_payload(
    case: ExperimentCase, split: B26Split, target: TrajectoryTarget, context: dict[str, Any]
) -> dict[str, Any]:
    return {
        "version": "topolab.b2_6.target.v1",
        "context": context,
        "case_id": case.case_id,
        "split": split,
        "iterations": target.iterations,
        "converged_before_target": target.converged_before_target,
        "compliance": target.compliance,
        "physical_volume_error": target.physical_volume_error,
        "shape": list(target.density.shape),
        "density": target.density.reshape(-1).tolist(),
    }


def _read_target(
    root: Path,
    row: dict[str, Any],
    case: ExperimentCase,
    split: B26Split,
    context: dict[str, Any],
) -> TrajectoryTarget:
    if row["case_id"] != case.case_id or row["split"] != split:
        raise ValueError("B2.6 target row has a different case or split")
    digest = row["artifact_sha256"]
    contents = _target_path(root, digest).read_bytes()
    if sha256(contents) != digest or len(contents) != row["artifact_bytes"]:
        raise ValueError("B2.6 target checksum or length differs")
    payload = json.loads(contents)
    counts = case.problem.mesh.element_counts
    shape = (1, counts[2], counts[1], counts[0])
    if (
        canonical_bytes(payload) != contents
        or payload["version"] != "topolab.b2_6.target.v1"
        or payload["context"] != context
        or payload["case_id"] != case.case_id
        or payload["split"] != split
        or tuple(payload["shape"]) != shape
        or not 1 <= payload["iterations"] <= TARGET_UPDATE
        or payload["converged_before_target"] != (payload["iterations"] < TARGET_UPDATE)
    ):
        raise ValueError("B2.6 target provenance or trajectory step differs")
    density = np.asarray(payload["density"], dtype=np.float32).reshape(shape)
    if (
        not np.isfinite(density).all()
        or np.any(density < case.problem.optimization.minimum_density - 1e-7)
        or np.any(density > 1.0)
        or not np.isfinite(payload["compliance"])
        or payload["compliance"] <= 0.0
    ):
        raise ValueError("B2.6 target has invalid density or compliance")
    mesh = generate_structured_hex8(*counts, lengths=case.problem.mesh.lengths)
    density_filter = build_density_filter(mesh, case.problem.optimization.filter_radius)
    physical = apply_density_filter(density_filter, density.astype(np.float64).reshape(-1))
    volume_error = abs(float(np.mean(physical)) - case.problem.optimization.volume_fraction)
    if volume_error > 0.005 or not np.isclose(
        volume_error, payload["physical_volume_error"], rtol=0.0, atol=1e-12
    ):
        raise ValueError("B2.6 persisted target violates independently checked volume")
    return TrajectoryTarget(
        density,
        payload["iterations"],
        payload["converged_before_target"],
        payload["compliance"],
        volume_error,
    )


def _capture_cases(
    groups: dict[B26Split, tuple[ExperimentCase, ...]],
) -> tuple[tuple[B26Split, ExperimentCase], ...]:
    return tuple((split, case) for split in ("train", "validation") for case in groups[split])


def capture_targets(
    root: Path, groups: dict[B26Split, tuple[ExperimentCase, ...]], context: dict[str, Any]
) -> dict[str, Any]:
    ordered = _capture_cases(groups)
    index = _index(root, "target_index.json", context, len(ordered))
    for row, (split, case) in zip(index["rows"], ordered, strict=False):
        _read_target(root, row, case, split, context)
    started = perf_counter()
    prior = index["elapsed_seconds"]
    for position in range(len(index["rows"]), len(ordered)):
        if prior + perf_counter() - started > CAPTURE_CAP:
            raise ValueError("B2.6 capture wall budget exhausted")
        split, case = ordered[position]
        case_started = perf_counter()
        target = capture_uniform_target(case)
        payload = _target_payload(case, split, target, context)
        contents = canonical_bytes(payload)
        digest = sha256(contents)
        path = _target_path(root, digest)
        if path.exists() and path.read_bytes() != contents:
            raise ValueError("B2.6 target artifact differs")
        if not path.exists():
            atomic_write(path, contents)
        row = {
            "case_id": case.case_id,
            "split": split,
            "artifact_sha256": digest,
            "artifact_bytes": len(contents),
            "seconds": perf_counter() - case_started,
        }
        _read_target(root, row, case, split, context)
        index["rows"].append(row)
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "target_index.json", canonical_bytes(index))
        if (position + 1) % 24 == 0 or position + 1 == len(ordered):
            print(f"B2.6 target {position + 1}/{len(ordered)}", file=sys.stderr, flush=True)
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "target_index.json", canonical_bytes(index))
    if (
        len(index["rows"]) != len(ordered)
        or index["elapsed_seconds"] > CAPTURE_CAP
        or index["peak_rss_bytes"] > MAX_RSS
    ):
        raise ValueError("B2.6 complete target capture resource Gate failed")
    return index


def _load_target_samples(
    root: Path,
    groups: dict[B26Split, tuple[ExperimentCase, ...]],
    target_index: dict[str, Any],
    context: dict[str, Any],
    split: Literal["train", "validation"],
) -> tuple[TrajectorySample, ...]:
    offset = 0 if split == "train" else 468
    cases = groups[split]
    return tuple(
        TrajectorySample.from_target(
            case, split, _read_target(root, target_index["rows"][offset + i], case, split, context)
        )
        for i, case in enumerate(cases)
    )


def _checkpoint_path(root: Path, seed: int, digest: str) -> Path:
    return root / "checkpoints" / str(seed) / f"{digest}.safetensors"


def _selection_path(root: Path, seed: int, digest: str) -> Path:
    return root / "selections" / str(seed) / f"{digest}.json"


def _read_model(root: Path, row: dict[str, Any], context: dict[str, Any]) -> WarmStartCNN:
    seed = row["seed"]
    digest = row["checkpoint_sha256"]
    contents = _checkpoint_path(root, seed, digest).read_bytes()
    if sha256(contents) != digest or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.6 checkpoint checksum or length differs")
    header_length = int.from_bytes(contents[:8], "little")
    header = json.loads(contents[8 : 8 + header_length])
    metadata = json.loads(header["__metadata__"]["topolab"])
    if metadata != {
        "version": "topolab.b2_6.checkpoint.v1",
        "context": context,
        "seed": seed,
        "selected_epoch": row["selected_epoch"],
    }:
        raise ValueError("B2.6 checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = WarmStartCNN()
    expected = model.state_dict()
    if set(state) != set(expected) or any(
        tensor.dtype != torch.float32
        or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all()
        for name, tensor in state.items()
    ):
        raise ValueError("B2.6 checkpoint tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_selection(root: Path, row: dict[str, Any], context: dict[str, Any]) -> None:
    digest = row["selection_sha256"]
    contents = _selection_path(root, row["seed"], digest).read_bytes()
    if sha256(contents) != digest or len(contents) != row["selection_bytes"]:
        raise ValueError("B2.6 selection checksum or length differs")
    record = json.loads(contents)
    if (
        canonical_bytes(record) != contents
        or record["version"] != "topolab.b2_6.selection.v1"
        or record["context"] != context
        or record["seed"] != row["seed"]
        or record["checkpoint_sha256"] != row["checkpoint_sha256"]
        or record["selected_epoch"] != row["selected_epoch"]
        or record["selected_validation_loss"] != row["selected_validation_loss"]
    ):
        raise ValueError("B2.6 selection provenance differs")
    history = record["history"]
    if (
        not history
        or len(history) > 200
        or [item["epoch"] for item in history] != list(range(1, len(history) + 1))
    ):
        raise ValueError("B2.6 selection history differs")
    minimum = min(item["validation_loss"] for item in history)
    first = next(item["epoch"] for item in history if item["validation_loss"] == minimum)
    if first != row["selected_epoch"] or minimum != row["selected_validation_loss"]:
        raise ValueError("B2.6 selection is not the earliest minimum")
    if len(history) < 200 and len(history) - first != 25:
        raise ValueError("B2.6 selection violates patience")
    _read_model(root, row, context)


def fit_models(
    root: Path,
    groups: dict[B26Split, tuple[ExperimentCase, ...]],
    target_context: dict[str, Any],
    fit_context: dict[str, Any],
) -> dict[str, Any]:
    targets = _index(root, "target_index.json", target_context, 480)
    if (
        len(targets["rows"]) != 480
        or targets["elapsed_seconds"] > CAPTURE_CAP
        or targets["peak_rss_bytes"] > MAX_RSS
    ):
        raise ValueError("B2.6 fitting requires the complete target capture")
    index = _index(root, "fit_index.json", fit_context, 3)
    for position, row in enumerate(index["rows"]):
        if row["seed"] != SEEDS[position]:
            raise ValueError("B2.6 fit order differs")
        _read_selection(root, row, fit_context)
    started = perf_counter()
    prior = index["elapsed_seconds"]
    if len(index["rows"]) < 3:
        train = _load_target_samples(root, groups, targets, target_context, "train")
        validation = _load_target_samples(root, groups, targets, target_context, "validation")
        for position in range(len(index["rows"]), 3):
            if prior + perf_counter() - started > FIT_CAP:
                raise ValueError("B2.6 fit wall budget exhausted")
            seed = SEEDS[position]
            fit: TrajectoryFit = fit_trajectory_seed(train, validation, seed=seed)
            metadata = {
                "version": "topolab.b2_6.checkpoint.v1",
                "context": fit_context,
                "seed": seed,
                "selected_epoch": fit.selected_epoch,
            }
            checkpoint = save_tensors(
                dict(sorted(fit.state.items())),
                metadata={"topolab": canonical_bytes(metadata).decode("utf-8")},
            )
            checkpoint_sha = sha256(checkpoint)
            atomic_write(_checkpoint_path(root, seed, checkpoint_sha), checkpoint)
            selection = {
                "version": "topolab.b2_6.selection.v1",
                "context": fit_context,
                "seed": seed,
                "history": fit.history,
                "selected_epoch": fit.selected_epoch,
                "selected_validation_loss": fit.selected_validation_loss,
                "fit_seconds": fit.seconds,
                "checkpoint_sha256": checkpoint_sha,
            }
            selection_bytes = canonical_bytes(selection)
            selection_sha = sha256(selection_bytes)
            atomic_write(_selection_path(root, seed, selection_sha), selection_bytes)
            row = {
                "seed": seed,
                "epochs": len(fit.history),
                "selected_epoch": fit.selected_epoch,
                "selected_validation_loss": fit.selected_validation_loss,
                "fit_seconds": fit.seconds,
                "checkpoint_sha256": checkpoint_sha,
                "checkpoint_bytes": len(checkpoint),
                "selection_sha256": selection_sha,
                "selection_bytes": len(selection_bytes),
            }
            _read_selection(root, row, fit_context)
            index["rows"].append(row)
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "fit_index.json", canonical_bytes(index))
            print(f"B2.6 fit {position + 1}/3 seed={seed}", file=sys.stderr, flush=True)
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "fit_index.json", canonical_bytes(index))
    if (
        len(index["rows"]) != 3
        or index["elapsed_seconds"] > FIT_CAP
        or index["peak_rss_bytes"] > MAX_RSS
    ):
        raise ValueError("B2.6 complete fit resource Gate failed")
    return index


def _case_outcomes(
    case: ExperimentCase,
    models: dict[int, WarmStartCNN],
    control: WarmStartCNN,
    neighbors: Any,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    first = _attempt(case, method="uniform", reference_compliance=None)
    if not first["succeeded"]:
        raise ValueError("B2.6 mandatory uniform reference failed")
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
    outcomes = [reference]
    outcomes.append(_charged_result(case, "physics_heuristic", None, reference))
    outcomes.append(_charged_result(case, "nearest_neighbor", None, reference, neighbors=neighbors))
    old = _charged_result(case, "control", 43, reference, model=control)
    old["method"] = "control_43"
    outcomes.append(old)
    for seed in SEEDS:
        item = _charged_result(case, "candidate", seed, reference, model=models[seed])
        item["method"] = f"trajectory_{seed}"
        outcomes.append(item)

    oracle_started = perf_counter()
    target = capture_uniform_target(case)
    oracle_generation = perf_counter() - oracle_started
    phases = {
        "setup_seconds": 0.0,
        "projection_seconds": 0.0,
        "refinement_seconds": 0.0,
        "decision_seconds": 0.0,
        "fallback_seconds": 0.0,
    }
    candidate: dict[str, Any] | None = None
    failure_code: str | None = None
    failure_type: str | None = None
    projected = None
    result = None
    try:
        started = perf_counter()
        try:
            projected = project_design_density(case, target.density)
        finally:
            phases["projection_seconds"] = perf_counter() - started
        started = perf_counter()
        try:
            result = _solve(case, projected.design_density)
        finally:
            phases["refinement_seconds"] = perf_counter() - started
        started = perf_counter()
        try:
            metrics = validate_refinement_quality(
                case, result, reference["uniform_reference_compliance"]
            )
        finally:
            phases["decision_seconds"] = perf_counter() - started
        candidate = metrics.model_dump(mode="json")
    except Exception as error:
        failure_code = "oracle_quality_or_refinement_error"
        failure_type = type(error).__name__
    if candidate is None:
        fallback = _attempt(case, method="uniform", reference_compliance=None)
        if not fallback["succeeded"]:
            raise ValueError("B2.6 oracle fresh uniform fallback failed")
        operational = fallback["candidate"]
        if not np.isclose(
            operational["final_compliance"],
            reference["uniform_reference_compliance"],
            rtol=1e-9,
            atol=0.0,
        ):
            raise ValueError("B2.6 oracle fallback differs from matched uniform")
        phases["fallback_seconds"] = sum(fallback["timing"].values())
    else:
        operational = candidate
    outcomes.append(
        {
            "case_id": case.case_id,
            "method": "trajectory_oracle",
            "seed": None,
            "succeeded": candidate is not None,
            "failure_code": failure_code,
            "failure_type": failure_type,
            "fallback_used": candidate is None,
            "candidate": candidate,
            "operational": operational,
            "matched_case_id": None,
            "uniform_reference_compliance": reference["uniform_reference_compliance"],
            "timing": {**phases, "end_to_end_seconds": sum(phases.values())},
            "paired_time_ratio": sum(phases.values()) / reference["timing"]["end_to_end_seconds"],
        }
    )
    if len(outcomes) != 8:
        raise ValueError("B2.6 screen case requires eight methods")
    return outcomes, {
        "oracle_generation_seconds": oracle_generation,
        "oracle_target_iterations": target.iterations,
        "oracle_target_converged_early": target.converged_before_target,
    }


def _screen_summary(
    root: Path,
    index: dict[str, Any],
    *,
    learned_prefix: str = "trajectory_",
    summary_version: str = "topolab.b2_6.screen_summary.v1",
) -> dict[str, Any]:
    ratios: defaultdict[tuple[str, str], list[float]] = defaultdict(list)
    directions: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    volumes: defaultdict[tuple[str, str, str, float], list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    fallbacks: Counter[str] = Counter()
    phases: defaultdict[str, Counter[str]] = defaultdict(Counter)
    accepted_quality_failures = 0
    for row in index["rows"]:
        case = row["case"]
        for item in row["outcomes"]:
            method = item["method"]
            ratio = item["paired_time_ratio"]
            ratios[(method, case["scale"])].append(ratio)
            directions[(method, case["scale"], case["direction"])].append(ratio)
            volumes[(method, case["scale"], case["direction"], case["volume"])].append(ratio)
            if not item["succeeded"]:
                failures[method] += 1
            if item["fallback_used"]:
                fallbacks[method] += 1
            if item["succeeded"] and (
                item["operational"]["final_compliance"]
                > 1.001 * item["uniform_reference_compliance"]
                or item["operational"]["physical_volume_error"] > 0.005
            ):
                accepted_quality_failures += 1
            phases[method].update(item["timing"])
    means = {
        f"{method}_{scale}": float(np.mean(values))
        for (method, scale), values in sorted(ratios.items())
    }
    direction_means = {
        f"{method}_{scale}_{direction}": float(np.mean(values))
        for (method, scale, direction), values in sorted(directions.items())
    }
    volume_means = {
        f"{method}_{scale}_{direction}_{volume:.3f}": float(np.mean(values))
        for (method, scale, direction, volume), values in sorted(volumes.items())
    }
    passing: list[int] = []
    if len(index["rows"]) == 12 and accepted_quality_failures == 0:
        for seed in SEEDS:
            method = f"{learned_prefix}{seed}"
            if all(
                means[f"{method}_{scale}"] <= 0.90
                and all(
                    direction_means[f"{method}_{scale}_{direction}"] <= 1.0
                    for direction in ("y", "z")
                )
                for scale in ("small", "large")
            ):
                passing.append(seed)
    gate = (
        len(passing) >= 2
        and len(index["rows"]) == 12
        and accepted_quality_failures == 0
        and index["elapsed_seconds"] <= SCREEN_CAP
        and index["peak_rss_bytes"] <= MAX_RSS
    )
    return {
        "version": summary_version,
        "context": index["context"],
        "screen_index_sha256": sha256((root / "screen_index.json").read_bytes()),
        "cases": len(index["rows"]),
        "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
        "mean_time_ratios": means,
        "direction_mean_time_ratios": direction_means,
        "volume_mean_time_ratios": volume_means,
        "failure_counts": dict(sorted(failures.items())),
        "fallback_counts": dict(sorted(fallbacks.items())),
        "phase_seconds": {
            key: dict(sorted(value.items())) for key, value in sorted(phases.items())
        },
        "accepted_quality_failures": accepted_quality_failures,
        "passing_seeds": passing,
        "oracle_generation_seconds": sum(
            row["oracle"]["oracle_generation_seconds"] for row in index["rows"]
        ),
        "model_loading_seconds": index["model_loading_seconds"],
        "neighbor_loading_seconds": index["neighbor_loading_seconds"],
        "neighbor_bytes": index["neighbor_bytes"],
        "screen_seconds": index["elapsed_seconds"],
        "peak_rss_bytes": index["peak_rss_bytes"],
        "prototype_gate_passed": gate,
    }


def screen_models(
    root: Path,
    groups: dict[B26Split, tuple[ExperimentCase, ...]],
    target_context: dict[str, Any],
    fit_context: dict[str, Any],
    b24_root: Path,
    b25_root: Path,
) -> dict[str, Any]:
    targets = _index(root, "target_index.json", target_context, 480)
    if (
        len(targets["rows"]) != 480
        or targets["elapsed_seconds"] > CAPTURE_CAP
        or targets["peak_rss_bytes"] > MAX_RSS
    ):
        raise ValueError("B2.6 screen requires complete target capture")
    fit = _index(root, "fit_index.json", fit_context, 3)
    if len(fit["rows"]) != 3 or fit["elapsed_seconds"] > FIT_CAP or fit["peak_rss_bytes"] > MAX_RSS:
        raise ValueError("B2.6 screen requires all three audited fits")
    for position, row in enumerate(fit["rows"]):
        if row["seed"] != SEEDS[position]:
            raise ValueError("B2.6 fit order differs")
        _read_selection(root, row, fit_context)
    context = {
        **fit_context,
        "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
        "b25_fit_index_sha256": B25_FIT_SHA256,
    }
    index = _index(root, "screen_index.json", context, 12)
    methods = [
        "uniform",
        "physics_heuristic",
        "nearest_neighbor",
        "control_43",
        *[f"trajectory_{seed}" for seed in SEEDS],
        "trajectory_oracle",
    ]
    for position, row in enumerate(index["rows"]):
        case = groups["screen"][position]
        if (
            row["case"]["case_id"] != case.case_id
            or [item["method"] for item in row["outcomes"]] != methods
            or any(item["case_id"] != case.case_id for item in row["outcomes"])
        ):
            raise ValueError("B2.6 screen row has a different case or method order")
    started = perf_counter()
    prior = index["elapsed_seconds"]
    if len(index["rows"]) < 12:
        load_started = perf_counter()
        models = {row["seed"]: _read_model(root, row, fit_context) for row in fit["rows"]}
        b25_contents = (b25_root / "fit_index.json").read_bytes()
        if sha256(b25_contents) != B25_FIT_SHA256:
            raise ValueError("B2.5 historical fit index differs")
        b25_index = json.loads(b25_contents)
        old = read_b25_fits(b25_root, b25_index["context"])
        old_row = next(row for row in old["rows"] if (row["arm"], row["seed"]) == ("control", 43))
        if old_row["checkpoint_sha256"] != B25_CONTROL43_SHA256:
            raise ValueError("B2.5 control checkpoint differs")
        control = read_b25_checkpoint(b25_root, old_row, old["context"])
        index["model_loading_seconds"] = (
            index.get("model_loading_seconds", 0.0) + perf_counter() - load_started
        )
        neighbor_started = perf_counter()
        source_cases = b24_cases()
        source_index = read_data_index(b24_root, source_cases)
        train = load_b24_samples(b24_root, source_index, split="train")
        neighbors = build_shape_neighbors(train)
        index["neighbor_loading_seconds"] = (
            index.get("neighbor_loading_seconds", 0.0) + perf_counter() - neighbor_started
        )
        index["neighbor_bytes"] = sum(item.stored_size_bytes for item in neighbors.values())
        for position in range(len(index["rows"]), 12):
            if prior + perf_counter() - started > SCREEN_CAP:
                raise ValueError("B2.6 screen wall budget exhausted")
            case = groups["screen"][position]
            case_started = perf_counter()
            nx, ny, nz = case.problem.mesh.element_counts
            outcomes, oracle = _case_outcomes(case, models, control, neighbors[(nz, ny, nx)])
            row = {
                "case": {
                    "case_id": case.case_id,
                    "scale": "small" if nx == 12 else "large",
                    "direction": case.problem.loads[0].direction,
                    "volume": case.problem.optimization.volume_fraction,
                },
                "outcomes": outcomes,
                "oracle": oracle,
                "seconds": perf_counter() - case_started,
            }
            index["rows"].append(row)
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "screen_index.json", canonical_bytes(index))
            print(
                f"B2.6 screen {position + 1}/12 {row['case']['scale']}", file=sys.stderr, flush=True
            )
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "screen_index.json", canonical_bytes(index))
    return _screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b25-root", type=Path, default=Path("/tmp/topolab-b25"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--capture", action="store_true")
    group.add_argument("--fit", action="store_true")
    group.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    groups = cohorts()
    plan = plan_payload(groups)
    if EXPECTED_PLAN_SHA256 and plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.6 plan differs from the frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    target_context = {
        "plan_sha256": plan["plan_sha256"],
        "source_revision": revision,
        "runtime": runtime,
    }
    if not (args.capture or args.fit or args.screen):
        print(json.dumps({**plan, **target_context}, sort_keys=True))
        return 0
    if not EXPECTED_PLAN_SHA256:
        parser.error("B2.6 execution requires a frozen plan checksum")
    if args.capture:
        index = capture_targets(root, groups, target_context)
        print(
            json.dumps(
                {
                    "target_index_sha256": sha256((root / "target_index.json").read_bytes()),
                    "rows": len(index["rows"]),
                    "elapsed_seconds": index["elapsed_seconds"],
                    "peak_rss_bytes": index["peak_rss_bytes"],
                },
                sort_keys=True,
            )
        )
        return 0
    fit_context = {
        **target_context,
        "target_index_sha256": sha256((root / "target_index.json").read_bytes()),
    }
    if args.fit:
        index = fit_models(root, groups, target_context, fit_context)
        print(
            json.dumps(
                {
                    "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
                    "fits": index["rows"],
                    "elapsed_seconds": index["elapsed_seconds"],
                    "peak_rss_bytes": index["peak_rss_bytes"],
                },
                sort_keys=True,
            )
        )
        return 0
    summary = screen_models(
        root, groups, target_context, fit_context, args.b24_root.resolve(), args.b25_root.resolve()
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["prototype_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
