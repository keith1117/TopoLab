"""B2.10 frozen sensitivity-weighted fitting and fresh development screen."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import torch
from b2_5_prototype import (
    _read_checkpoint as read_b25_checkpoint,
)
from b2_5_prototype import (
    _read_fit_index as read_b25_fits,
)
from b2_5_prototype import (
    atomic_write,
    canonical_bytes,
    load_samples,
    read_data_index,
    sha256,
    source_snapshot,
)
from b2_6_trajectory import (
    B25_CONTROL43_SHA256,
    B25_FIT_SHA256,
    _case_outcomes,
    _external_root,
    _read_target,
    _screen_summary,
    _small_case,
)
from b2_7_global_load import B26_TARGET_INDEX_SHA256, _peak_rss, _prior
from b2_7_global_load import cohorts as b27_cohorts
from b2_8_basin import cohorts as b28_cohorts
from b2_9_vector_load import (
    VECTOR_MODEL_PARAMETER_COUNT,
    _checkpoint_path,
    _index,
    _selection_path,
)
from b2_9_vector_load import _read_model as read_b29_model
from b2_9_vector_load import _read_selection as read_b29_selection
from b2_9_vector_load import cohorts as b29_cohorts
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import _charged_result, build_shape_neighbors
from topolab.b2_6_trajectory import SEEDS, TrajectorySample, fit_trajectory_seed
from topolab.b2_9_vector_load import VectorLoadCNN, encode_vector_load_case
from topolab.b2_10_weighted_trajectory import WEIGHT_VERSION, sensitivity_weighted_target
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_10.weighted_trajectory.v1"
EXPECTED_PLAN_SHA256 = "d3fd19a8a16d4d7d6dc2ae02a731de45654a53c0d5e44c1945331cbf61f1a079"
B29_FIT_INDEX_SHA256 = "96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3"
VOLUMES = (0.2875, 0.4375, 0.5875)
WEIGHT_CAP = 7_200.0
FIT_CAP = 7_200.0
SCREEN_CAP = 14_400.0
MAX_RSS = 2_147_483_648
METHODS = (
    "uniform", "physics_heuristic", "nearest_neighbor", "control_43",
    *(f"vector_{seed}" for seed in SEEDS),
    *(f"weighted_{seed}" for seed in SEEDS),
    "trajectory_oracle",
)


def cohorts() -> tuple[dict[str, tuple[ExperimentCase, ...]], tuple[ExperimentCase, ...]]:
    """Retain all source cases and freeze a fresh complete twelve-case screen."""

    old, b27_screen = b27_cohorts()
    _, b28_screen = b28_cohorts()
    _, b29_screen = b29_cohorts()
    exposed = {case.case_id for cases in old.values() for case in cases}
    exposed.update(case.case_id for case in (*b27_screen, *b28_screen, *b29_screen))
    historical_volumes = {
        *(index / 100 for index in range(20, 61, 5)),
        *(index / 1000 for index in range(225, 576, 50)),
        0.2375, 0.3875, 0.5375,
        0.2125, 0.3625, 0.5125,
        0.2625, 0.4125, 0.5625,
    }
    if set(VOLUMES).intersection(historical_volumes):
        raise ValueError("B2.10 volumes overlap development or design-exposed final cases")
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for direction in ("y", "z"):
            small = _small_case(volume, direction, 2, 2)
            selected.extend((small, scaled_case(small)))
    screen = tuple(sorted(selected, key=lambda case: case.case_id))
    strata = Counter(
        (case.problem.mesh.element_counts, case.problem.loads[0].direction,
         case.problem.optimization.volume_fraction)
        for case in screen
    )
    if (
        len(screen) != 12
        or len({case.case_id for case in screen}) != 12
        or any(case.case_id in exposed for case in screen)
        or len(strata) != 12
        or any(count != 1 for count in strata.values())
    ):
        raise ValueError("B2.10 screen identity or strata overlap")
    return old, screen


def plan_payload(
    old: dict[str, tuple[ExperimentCase, ...]], screen: tuple[ExperimentCase, ...]
) -> dict[str, Any]:
    _, b27_screen = b27_cohorts()
    _, b28_screen = b28_cohorts()
    _, b29_screen = b29_cohorts()
    exposed = tuple(sorted(
        {case.case_id for cases in old.values() for case in cases}
        | {case.case_id for case in (*b27_screen, *b28_screen, *b29_screen)}
    ))
    identity = {
        "version": PLAN_VERSION,
        "weight_version": WEIGHT_VERSION,
        "weight_rule": "abs_design_compliance_gradient_clip_0.25_4_mean_one",
        "objective": "sensitivity_weighted_update30_design_mse",
        "input_version": "topolab.b2_9.vector_load.v1",
        "model_version": "topolab.b2_9.vector_cnn.v1",
        "model_parameter_count": VECTOR_MODEL_PARAMETER_COUNT,
        "b26_target_index_sha256": B26_TARGET_INDEX_SHA256,
        "b29_fit_index_sha256": B29_FIT_INDEX_SHA256,
        "b25_fit_index_sha256": B25_FIT_SHA256,
        "b25_control43_checkpoint_sha256": B25_CONTROL43_SHA256,
        "target_update": 30,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 240,
        "seeds": list(SEEDS),
        "train_case_ids": [case.case_id for case in old["train"]],
        "validation_case_ids": [case.case_id for case in old["validation"]],
        "exposed_case_ids": list(exposed),
        "screen_case_ids": [case.case_id for case in screen],
        "screen_volumes": list(VOLUMES),
        "screen_load_node_small": [12, 2, 2],
        "methods": list(METHODS),
        "weight_cap_seconds": WEIGHT_CAP,
        "fit_cap_seconds": FIT_CAP,
        "screen_cap_seconds": SCREEN_CAP,
        "max_rss_bytes": MAX_RSS,
        "gate_two_scale_mean_max": 0.90,
        "gate_each_direction_mean_max": 1.0,
        "gate_required_seeds": 2,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _weight_path(root: Path, digest: str) -> Path:
    return root / "weights" / f"{digest}.json"


def _read_weight(
    root: Path, row: dict[str, Any], case: ExperimentCase, split: str,
    target_row: dict[str, Any], target: Any, context: dict[str, Any],
) -> np.ndarray:
    if row["case_id"] != case.case_id or row["split"] != split:
        raise ValueError("B2.10 weight row differs from its physical case")
    contents = _weight_path(root, row["artifact_sha256"]).read_bytes()
    if sha256(contents) != row["artifact_sha256"] or len(contents) != row["artifact_bytes"]:
        raise ValueError("B2.10 weight checksum or size differs")
    payload = json.loads(contents)
    expected_shape = list(target.density.shape)
    if (
        canonical_bytes(payload) != contents
        or payload["version"] != WEIGHT_VERSION
        or payload["context"] != context
        or payload["case_id"] != case.case_id
        or payload["split"] != split
        or payload["source_target_sha256"] != target_row["artifact_sha256"]
        or payload["shape"] != expected_shape
    ):
        raise ValueError("B2.10 weight provenance differs")
    stored = np.asarray(payload["weight"], dtype=np.float64)
    weight = stored.astype(np.float32).reshape(target.density.shape)
    if (
        not np.array_equal(stored, weight.reshape(-1).astype(np.float64))
        or not np.isfinite(weight).all()
        or np.any(weight <= 0.0)
        or not np.isclose(np.mean(weight, dtype=np.float64), 1.0, atol=1e-6, rtol=0.0)
    ):
        raise ValueError("B2.10 weight values differ from CPU float32 contract")
    independent = sensitivity_weighted_target(case, target)
    if not np.array_equal(weight, independent.weight) or not np.isclose(
        payload["compliance"], independent.compliance, atol=0.0, rtol=1e-9
    ):
        raise ValueError("B2.10 weight failed independent physical-state audit")
    return weight


def capture_weights(
    root: Path, b26_root: Path, old: dict[str, tuple[ExperimentCase, ...]],
    targets: dict[str, Any], context: dict[str, Any],
) -> dict[str, Any]:
    ordered = [(split, case) for split in ("train", "validation") for case in old[split]]
    index = _index(root, "weight_index.json", context, 480)
    for row, (split, case), target_row in zip(
        index["rows"], ordered, targets["rows"], strict=False
    ):
        target = _read_target(b26_root, target_row, case, split, targets["context"])
        _read_weight(root, row, case, split, target_row, target, context)
    if len(index["rows"]) == 480:
        if index["elapsed_seconds"] > WEIGHT_CAP or index["peak_rss_bytes"] > MAX_RSS:
            raise ValueError("B2.10 complete weight-generation resource Gate failed")
        return index
    started = perf_counter()
    prior = index["elapsed_seconds"]
    for position in range(len(index["rows"]), 480):
        if prior + perf_counter() - started > WEIGHT_CAP:
            raise ValueError("B2.10 weight-generation wall budget exhausted")
        split, case = ordered[position]
        target_row = targets["rows"][position]
        item_started = perf_counter()
        target = _read_target(b26_root, target_row, case, split, targets["context"])
        result = sensitivity_weighted_target(case, target)
        payload = {
            "version": WEIGHT_VERSION, "context": context, "case_id": case.case_id,
            "split": split, "source_target_sha256": target_row["artifact_sha256"],
            "shape": list(result.weight.shape), "weight": result.weight.reshape(-1).tolist(),
            "compliance": result.compliance,
        }
        contents = canonical_bytes(payload)
        digest = sha256(contents)
        atomic_write(_weight_path(root, digest), contents)
        row = {
            "case_id": case.case_id, "split": split,
            "artifact_sha256": digest, "artifact_bytes": len(contents),
            "seconds": perf_counter() - item_started,
        }
        _read_weight(root, row, case, split, target_row, target, context)
        index["rows"].append(row)
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "weight_index.json", canonical_bytes(index))
        if (position + 1) % 24 == 0 or position == 479:
            print(f"B2.10 weights {position + 1}/480", file=sys.stderr, flush=True)
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "weight_index.json", canonical_bytes(index))
    if index["elapsed_seconds"] > WEIGHT_CAP or index["peak_rss_bytes"] > MAX_RSS:
        raise ValueError("B2.10 complete weight-generation resource Gate failed")
    return index


def _audit_weights(
    root: Path, b26_root: Path, old: dict[str, tuple[ExperimentCase, ...]],
    targets: dict[str, Any], context: dict[str, Any],
) -> dict[str, Any]:
    index = _index(root, "weight_index.json", context, 480)
    if len(index["rows"]) != 480 or index["elapsed_seconds"] > WEIGHT_CAP or (
        index["peak_rss_bytes"] > MAX_RSS
    ):
        raise ValueError("B2.10 requires all weights within their resource budget")
    ordered = [(split, case) for split in ("train", "validation") for case in old[split]]
    for row, (split, case), target_row in zip(
        index["rows"], ordered, targets["rows"], strict=True
    ):
        target = _read_target(b26_root, target_row, case, split, targets["context"])
        _read_weight(root, row, case, split, target_row, target, context)
    return index


def _weighted_samples(
    root: Path, b26_root: Path, old: dict[str, tuple[ExperimentCase, ...]],
    targets: dict[str, Any], weights: dict[str, Any], context: dict[str, Any],
    split: str,
) -> tuple[TrajectorySample, ...]:
    offset = 0 if split == "train" else 468
    samples: list[TrajectorySample] = []
    for position, case in enumerate(old[split]):
        target_row = targets["rows"][offset + position]
        target = _read_target(b26_root, target_row, case, split, targets["context"])
        weight = _read_weight(
            root, weights["rows"][offset + position], case, split,
            target_row, target, context,
        )
        sample = TrajectorySample(
            case_id=case.case_id, split=split,  # type: ignore[arg-type]
            inputs=torch.from_numpy(encode_vector_load_case(case).input_tensor.copy()),
            target=torch.from_numpy(target.density.copy()), input_channels=13,
            weight=torch.from_numpy(weight.copy()),
        )
        sample.validate()
        samples.append(sample)
    return tuple(samples)


def _read_model(root: Path, row: dict[str, Any], context: dict[str, Any]) -> VectorLoadCNN:
    seed = row["seed"]
    contents = _checkpoint_path(root, seed, row["checkpoint_sha256"]).read_bytes()
    if sha256(contents) != row["checkpoint_sha256"] or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.10 checkpoint checksum or size differs")
    header_length = int.from_bytes(contents[:8], "little")
    header = json.loads(contents[8 : 8 + header_length])
    metadata = json.loads(header["__metadata__"]["topolab"])
    if metadata != {
        "version": "topolab.b2_10.checkpoint.v1", "context": context,
        "seed": seed, "selected_epoch": row["selected_epoch"],
    }:
        raise ValueError("B2.10 checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = VectorLoadCNN()
    expected = model.state_dict()
    if set(state) != set(expected) or any(
        tensor.dtype != torch.float32
        or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all()
        for name, tensor in state.items()
    ):
        raise ValueError("B2.10 checkpoint tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_selection(root: Path, row: dict[str, Any], context: dict[str, Any]) -> None:
    contents = _selection_path(root, row["seed"], row["selection_sha256"]).read_bytes()
    if sha256(contents) != row["selection_sha256"] or len(contents) != row["selection_bytes"]:
        raise ValueError("B2.10 selection checksum or size differs")
    selection = json.loads(contents)
    if (
        canonical_bytes(selection) != contents
        or selection["version"] != "topolab.b2_10.selection.v1"
        or selection["context"] != context
        or selection["seed"] != row["seed"]
        or selection["checkpoint_sha256"] != row["checkpoint_sha256"]
        or selection["selected_epoch"] != row["selected_epoch"]
        or selection["selected_validation_loss"] != row["selected_validation_loss"]
    ):
        raise ValueError("B2.10 selection provenance differs")
    history = selection["history"]
    if not history or len(history) > 200 or [
        entry["epoch"] for entry in history
    ] != list(range(1, len(history) + 1)):
        raise ValueError("B2.10 selection history differs")
    minimum = min(entry["validation_loss"] for entry in history)
    first = next(entry["epoch"] for entry in history if entry["validation_loss"] == minimum)
    if first != row["selected_epoch"] or minimum != row["selected_validation_loss"]:
        raise ValueError("B2.10 selection is not the earliest weighted-MSE minimum")
    if len(history) < 200 and len(history) - first != 25:
        raise ValueError("B2.10 selection violates patience")
    _read_model(root, row, context)


def fit_models(
    root: Path, b26_root: Path, old: dict[str, tuple[ExperimentCase, ...]],
    targets: dict[str, Any], weights: dict[str, Any],
    weight_context: dict[str, Any], context: dict[str, Any],
) -> dict[str, Any]:
    index = _index(root, "fit_index.json", context, 3)
    for row, seed in zip(index["rows"], SEEDS, strict=False):
        if row["seed"] != seed:
            raise ValueError("B2.10 fit order differs")
        _read_selection(root, row, context)
    if len(index["rows"]) == 3:
        return index
    started = perf_counter()
    prior = index["elapsed_seconds"]
    train = _weighted_samples(root, b26_root, old, targets, weights, weight_context, "train")
    validation = _weighted_samples(
        root, b26_root, old, targets, weights, weight_context, "validation"
    )
    for position in range(len(index["rows"]), 3):
        if prior + perf_counter() - started > FIT_CAP:
            raise ValueError("B2.10 fit wall budget exhausted")
        seed = SEEDS[position]
        fit = fit_trajectory_seed(
            train, validation, seed=seed, model_factory=VectorLoadCNN,
            expected_parameter_count=VECTOR_MODEL_PARAMETER_COUNT,
            input_channels=13, weighted_loss=True,
        )
        metadata = {
            "version": "topolab.b2_10.checkpoint.v1", "context": context,
            "seed": seed, "selected_epoch": fit.selected_epoch,
        }
        checkpoint = save_tensors(
            dict(sorted(fit.state.items())),
            metadata={"topolab": canonical_bytes(metadata).decode("utf-8")},
        )
        digest = sha256(checkpoint)
        atomic_write(_checkpoint_path(root, seed, digest), checkpoint)
        selection = {
            "version": "topolab.b2_10.selection.v1", "context": context,
            "seed": seed, "history": fit.history,
            "selected_epoch": fit.selected_epoch,
            "selected_validation_loss": fit.selected_validation_loss,
            "fit_seconds": fit.seconds, "checkpoint_sha256": digest,
        }
        selection_bytes = canonical_bytes(selection)
        selection_sha = sha256(selection_bytes)
        atomic_write(_selection_path(root, seed, selection_sha), selection_bytes)
        row = {
            "seed": seed, "epochs": len(fit.history),
            "selected_epoch": fit.selected_epoch,
            "selected_validation_loss": fit.selected_validation_loss,
            "fit_seconds": fit.seconds, "checkpoint_sha256": digest,
            "checkpoint_bytes": len(checkpoint),
            "selection_sha256": selection_sha,
            "selection_bytes": len(selection_bytes),
        }
        _read_selection(root, row, context)
        index["rows"].append(row)
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "fit_index.json", canonical_bytes(index))
        print(f"B2.10 fit {position + 1}/3 seed={seed}", file=sys.stderr, flush=True)
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "fit_index.json", canonical_bytes(index))
    if index["elapsed_seconds"] > FIT_CAP or index["peak_rss_bytes"] > MAX_RSS:
        raise ValueError("B2.10 complete fit resource Gate failed")
    return index


def screen_models(
    root: Path, b29_root: Path, b24_root: Path, b25_root: Path,
    screen: tuple[ExperimentCase, ...], context: dict[str, Any],
) -> dict[str, Any]:
    fits = _index(root, "fit_index.json", context, 3)
    if len(fits["rows"]) != 3 or fits["elapsed_seconds"] > FIT_CAP or (
        fits["peak_rss_bytes"] > MAX_RSS
    ):
        raise ValueError("B2.10 screen requires all three audited fits")
    for row, seed in zip(fits["rows"], SEEDS, strict=True):
        if row["seed"] != seed:
            raise ValueError("B2.10 model order differs")
        _read_selection(root, row, context)
    screen_context = {
        **context, "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
    }
    index = _index(root, "screen_index.json", screen_context, 12)
    for position, row in enumerate(index["rows"]):
        if row["case"]["case_id"] != screen[position].case_id or [
            item["method"] for item in row["outcomes"]
        ] != list(METHODS):
            raise ValueError("B2.10 persisted screen row differs")
    if len(index["rows"]) == 12:
        return _screen_summary(
            root, index, learned_prefix="weighted_",
            summary_version="topolab.b2_10.screen_summary.v1",
        )
    started = perf_counter()
    prior = index["elapsed_seconds"]
    load_started = perf_counter()
    new_models = {row["seed"]: _read_model(root, row, context) for row in fits["rows"]}
    if sha256((b29_root / "fit_index.json").read_bytes()) != B29_FIT_INDEX_SHA256:
        raise ValueError("B2.9 fixed fit index differs")
    old_fits = json.loads((b29_root / "fit_index.json").read_bytes())
    old_models = {}
    for row in old_fits["rows"]:
        read_b29_selection(b29_root, row, old_fits["context"])
        old_models[row["seed"]] = read_b29_model(b29_root, row, old_fits["context"])
    if sha256((b25_root / "fit_index.json").read_bytes()) != B25_FIT_SHA256:
        raise ValueError("B2.5 fixed fit index differs")
    b25 = json.loads((b25_root / "fit_index.json").read_bytes())
    audited = read_b25_fits(b25_root, b25["context"])
    control_row = next(
        row for row in audited["rows"] if (row["arm"], row["seed"]) == ("control", 43)
    )
    if control_row["checkpoint_sha256"] != B25_CONTROL43_SHA256:
        raise ValueError("B2.5 fixed control differs")
    control = read_b25_checkpoint(b25_root, control_row, audited["context"])
    index["model_loading_seconds"] = (
        index.get("model_loading_seconds", 0.0) + perf_counter() - load_started
    )
    neighbor_started = perf_counter()
    from b2_4_materialize_labels import select_cases as b24_cases

    sources = b24_cases()
    source_index = read_data_index(b24_root, sources)
    neighbors = build_shape_neighbors(load_samples(b24_root, source_index, split="train"))
    index["neighbor_loading_seconds"] = (
        index.get("neighbor_loading_seconds", 0.0) + perf_counter() - neighbor_started
    )
    index["neighbor_bytes"] = sum(value.stored_size_bytes for value in neighbors.values())
    for position in range(len(index["rows"]), 12):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.10 screen wall budget exhausted")
        case = screen[position]
        case_started = perf_counter()
        nx, ny, nz = case.problem.mesh.element_counts
        outcomes, oracle = _case_outcomes(
            case, old_models, control, neighbors[(nz, ny, nx)],
            encoder=encode_vector_load_case,
        )
        oracle_outcome = outcomes.pop()
        for item in outcomes:
            if item["method"].startswith("trajectory_"):
                item["method"] = item["method"].replace("trajectory_", "vector_", 1)
        for seed in SEEDS:
            item = _charged_result(
                case, "candidate", seed, outcomes[0], model=new_models[seed],
                encoder=encode_vector_load_case,
            )
            item["method"] = f"weighted_{seed}"
            outcomes.append(item)
        outcomes.append(oracle_outcome)
        if [item["method"] for item in outcomes] != list(METHODS):
            raise ValueError("B2.10 method order differs")
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
        print(f"B2.10 screen {position + 1}/12", file=sys.stderr, flush=True)
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "screen_index.json", canonical_bytes(index))
    return _screen_summary(
        root, index, learned_prefix="weighted_",
        summary_version="topolab.b2_10.screen_summary.v1",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b26-root", type=Path, default=Path("/tmp/topolab-b26"))
    parser.add_argument("--b29-root", type=Path, default=Path("/tmp/topolab-b29"))
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b25-root", type=Path, default=Path("/tmp/topolab-b25"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--weights", action="store_true")
    group.add_argument("--fit", action="store_true")
    group.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    old, screen = cohorts()
    plan = plan_payload(old, screen)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.10 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b26_root = _external_root(repository, args.b26_root)
    b29_root = _external_root(repository, args.b29_root)
    if len({root, b26_root, b29_root}) != 3:
        raise ValueError("B2.10 output and source roots must differ")
    weight_context = {
        "plan_sha256": plan["plan_sha256"], "source_revision": revision,
        "runtime": runtime, "b26_target_index_sha256": B26_TARGET_INDEX_SHA256,
    }
    if not (args.weights or args.fit or args.screen):
        print(json.dumps({**plan, **weight_context}, sort_keys=True))
        return 0
    targets, _ = _prior(b26_root, old)
    if args.weights:
        index = capture_weights(root, b26_root, old, targets, weight_context)
        print(json.dumps({
            "weight_index_sha256": sha256((root / "weight_index.json").read_bytes()),
            "weights": len(index["rows"]), "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"],
        }, sort_keys=True))
        return 0
    weights = _audit_weights(root, b26_root, old, targets, weight_context)
    fit_context = {
        **weight_context,
        "weight_index_sha256": sha256((root / "weight_index.json").read_bytes()),
        "b29_fit_index_sha256": B29_FIT_INDEX_SHA256,
    }
    if args.fit:
        index = fit_models(
            root, b26_root, old, targets, weights, weight_context, fit_context
        )
        print(json.dumps({
            "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
            "fits": index["rows"], "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"],
        }, sort_keys=True))
        return 0
    summary = screen_models(
        root, b29_root, args.b24_root.resolve(), args.b25_root.resolve(),
        screen, fit_context,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["prototype_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
