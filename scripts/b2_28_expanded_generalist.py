"""B2.28 fixed middle-volume label expansion and matched development screen."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
import torch
from b2_4_materialize_labels import select_cases
from b2_5_prototype import (
    DATA_INDEX_SHA256,
    atomic_write,
    canonical_bytes,
    read_data_index,
    sha256,
    source_snapshot,
)
from b2_6_trajectory import _external_root, _small_case
from b2_7_global_load import _peak_rss
from b2_9_vector_load import _index
from b2_11_reference_budget import versioned_case
from b2_20_operational_selection import (
    _uniform_result,
    reference_gate,
    run_references,
)
from b2_21_terminal_target import _samples
from b2_24_expanded_training import _diagnostic_mse, specialist_case
from b2_24_expanded_training import _read_fit_index as read_specialist_fit_index
from b2_24_expanded_training import _read_model as read_specialist_model
from b2_26_weighted_generalist import _read_fit_index as read_old_fit_index
from b2_26_weighted_generalist import _read_model as read_old_model
from b2_26_weighted_generalist import cohorts as b226_cohorts
from b2_27_middle_volume_labels import EXPECTED_PLAN_SHA256 as B227_PLAN_SHA256
from b2_27_middle_volume_labels import _environment as label_environment
from b2_27_middle_volume_labels import _read_label as read_position_label
from b2_27_middle_volume_labels import cohorts as b227_cohorts
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import _charged_result
from topolab.b2_6_trajectory import SEEDS, TrajectorySample, fit_trajectory_seed
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_12_context_cnn import CONTEXT_MODEL_PARAMETER_COUNT, ContextCNN
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_28.expanded_generalist.v1"
EXPECTED_PLAN_SHA256 = "1e33936caedaa5702d14ffe3bbfa349211b44c170d13d9a0f3d4f0a90a865da0"
B221_TARGET_SHA256 = "3e7add2c85650bcb5ac0329236678887baaf2fc3acd4882a1f8f8fc7070796ab"
B226_FIT_SHA256 = "02b95a940de87cc8e9e5d8d297b619b461425bece0ca933a588b9072ce8a5c8e"
B226_SCREEN_SHA256 = "05fa1f1e825060b144db0cbab728dfe98e3785594fce42ff7aad85e26813307a"
B227_LABEL_SHA256 = "aa422ab98f9ca102c55cea991ff679b6b5b703abcb4b5456424fbb8878ca1d35"
B227_SOURCE = "1c26baf77b603af83505582adefe447d8f370618"
B224_FIT_SHA256 = "89bacfec6fbdfd2732ab74404626dc33a914b7cf788750f02276319b7e73700a"
B224_SCREEN_SHA256 = "e77ad2eb6670dcae64e14c51d67b4b6ad6dc05d2d8e57448be39c8c584db1075"
VOLUMES = (0.3745, 0.5295, 0.5935)
POSITIONS = ((2, 2), (5, 1))
Y_WEIGHT = 8.0
Y_MIN_VOLUME = 0.5
WEIGHTED_COUNT = 98
TRAIN_COUNT = 508
BATCH_COUNT = 64
REFERENCE_CAP = 3_600.0
FIT_CAP = 7_200.0
SCREEN_CAP = 24_000.0
MAX_RSS = 2_147_483_648
METHODS = ("uniform", *(f"old_{seed}" for seed in SEEDS),
           *(f"expanded_{seed}" for seed in SEEDS))


def cohorts() -> tuple[dict[str, tuple[ExperimentCase, ...]],
                       tuple[ExperimentCase, ...], tuple[ExperimentCase, ...]]:
    groups, _, _ = b226_cohorts()
    identities, labels, prior_blocked = b227_cohorts()
    blocked = tuple(sorted({case.case_id: case for case in (
        *prior_blocked, *labels,
    )}.values(), key=lambda case: case.case_id))
    groups = {**groups,
              "expanded_train": tuple(sorted((*groups["train"], *(case
                  for identity, case in zip(identities, labels, strict=True)
                  if identity["split"] == "train")), key=lambda case: case.case_id)),
              "diagnostic": tuple(case for identity, case in zip(identities, labels, strict=True)
                                  if identity["split"] == "validation")}
    excluded = {case.problem.optimization.volume_fraction for case in blocked}
    excluded.update(index / 100 for index in range(20, 61, 5))
    excluded.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & excluded:
        raise ValueError("B2.28 screen volume intersects exposed or reserved evidence")
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for y, z in POSITIONS:
            for direction in ("y", "z"):
                small = _small_case(volume, direction, y, z)
                selected.extend((versioned_case(small),
                                 versioned_case(scaled_case(small))))
    screen = tuple(sorted(selected, key=lambda case: case.case_id))
    strata = Counter((case.problem.mesh.element_counts, case.problem.loads[0].direction)
                     for case in screen)
    if (len(blocked) != 898 or len(screen) != 24
            or len(groups["expanded_train"]) != TRAIN_COUNT or len(groups["diagnostic"]) != 20
            or len({case.case_id for case in (*blocked, *screen)}) != 922
            or len(strata) != 4 or set(strata.values()) != {6}
            or sum(specialist_case(case) for case in screen) != 2
            or any(case.problem.optimization.max_iterations != 360 for case in screen)):
        raise ValueError("B2.28 population, strata, or route differs")
    return groups, screen, blocked


def weighted_case_ids(groups: dict[str, tuple[ExperimentCase, ...]]) -> tuple[str, ...]:
    selected = tuple(sorted(case.case_id for case in groups["expanded_train"]
                            if case.problem.loads[0].direction == "y"
                            and case.problem.optimization.volume_fraction >= Y_MIN_VOLUME))
    if len(selected) != WEIGHTED_COUNT:
        raise ValueError("B2.28 weighted training population differs")
    return selected


def plan_payload(groups: dict[str, tuple[ExperimentCase, ...]],
                 screen: tuple[ExperimentCase, ...],
                 blocked: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "intervention": "add_40_middle_volume_large_y_z_train_terminal_labels",
        "b24_data_index_sha256": DATA_INDEX_SHA256,
        "b221_target_index_sha256": B221_TARGET_SHA256,
        "b226_fit_index_sha256": B226_FIT_SHA256,
        "b226_screen_index_sha256": B226_SCREEN_SHA256,
        "b227_label_index_sha256": B227_LABEL_SHA256,
        "b224_fit_index_sha256": B224_FIT_SHA256,
        "b224_screen_index_sha256": B224_SCREEN_SHA256,
        "model_version": "topolab.b2_12.context_cnn.v1",
        "input_version": "topolab.b2_9.vector_load.v1",
        "target": "audited_uniform_terminal_design_float32",
        "train_case_ids": [case.case_id for case in groups["expanded_train"]],
        "old_train_case_ids": [case.case_id for case in groups["train"]],
        "validation_case_ids": [case.case_id for case in groups["validation"]],
        "diagnostic_case_ids": [case.case_id for case in groups["diagnostic"]],
        "train_count": TRAIN_COUNT,
        "batches_per_epoch": BATCH_COUNT,
        "weighted_train_case_ids": weighted_case_ids(groups),
        "weighted_case_value": Y_WEIGHT,
        "other_case_value": 1.0,
        "selection": "earliest_strict_minimum_unweighted_mse_all_12_validation_cases",
        "blocked_case_ids": [case.case_id for case in blocked],
        "screen_case_ids": [case.case_id for case in screen],
        "screen_volumes": VOLUMES,
        "screen_positions_small": POSITIONS,
        "methods": METHODS,
        "seeds": SEEDS,
        "route": {"specialist_mesh": (24, 12, 6), "direction": "y",
                  "minimum_volume": 0.55},
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "screen_solver_budget": 360,
        "caps_seconds": {"references": REFERENCE_CAP, "fit": FIT_CAP,
                         "screen": SCREEN_CAP},
        "max_rss_bytes": MAX_RSS,
        "gate_scale_mean_max": 0.90,
        "gate_direction_mean_max": 1.0,
        "gate_required_expanded_seeds": 2,
        "gate_failures_no_more_than_old": True,
        "gate_non_specialist_y_failures_per_seed_max": 2,
        "gate_non_specialist_y_failures_no_more_than_old": True,
        "gate_middle_volume_large_y_successes_min": 4,
        "gate_high_volume_large_y_successes_min": 4,
        "gate_accepted_quality_violations_max": 0,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _checkpoint_path(root: Path, seed: int, digest: str) -> Path:
    return root / "checkpoints" / str(seed) / f"{digest}.safetensors"


def _read_model(root: Path, row: dict[str, Any], context: dict[str, Any]) -> ContextCNN:
    contents = _checkpoint_path(root, row["seed"], row["checkpoint_sha256"]).read_bytes()
    if sha256(contents) != row["checkpoint_sha256"] or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.28 checkpoint checksum or size differs")
    length = int.from_bytes(contents[:8], "little")
    metadata = json.loads(json.loads(contents[8:8 + length])["__metadata__"]["topolab"])
    if metadata != {"version": "topolab.b2_28.checkpoint.v1", "context": context,
                    "seed": row["seed"], "selected_epoch": row["selected_epoch"]}:
        raise ValueError("B2.28 checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = ContextCNN()
    expected = model.state_dict()
    if set(state) != set(expected) or any(
        tensor.dtype != torch.float32 or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all() for name, tensor in state.items()
    ):
        raise ValueError("B2.28 checkpoint tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_fit_index(root: Path, context: dict[str, Any]) -> dict[str, Any]:
    index = _index(root, "fit_index.json", context, 3)
    for row, seed in zip(index["rows"], SEEDS, strict=False):
        if row["seed"] != seed:
            raise ValueError("B2.28 fit seed order differs")
        _read_model(root, row, context)
        contents = (root / "histories" / str(seed) / f"{row['history_sha256']}.json").read_bytes()
        if sha256(contents) != row["history_sha256"] or len(contents) != row["history_bytes"]:
            raise ValueError("B2.28 fit history checksum or size differs")
        history = json.loads(contents)
        if (canonical_bytes(history) != contents or history["context"] != context
                or history["seed"] != seed or history["version"] != "topolab.b2_28.history.v1"
                or not history["entries"] or len(history["entries"]) > 200):
            raise ValueError("B2.28 fit history provenance differs")
        entries = history["entries"]
        minimum = min(item["validation_loss"] for item in entries)
        first = next(item["epoch"] for item in entries if item["validation_loss"] == minimum)
        if (first != row["selected_epoch"] or minimum != row["selected_validation_loss"]
                or [item["epoch"] for item in entries] != list(range(1, len(entries) + 1))
                or (len(entries) < 200 and len(entries) - first != 25)):
            raise ValueError("B2.28 fit selection differs")
        for name in ("diagnostic_mse_by_direction", "old_diagnostic_mse_by_direction"):
            if set(row[name]) != {"y", "z"} or any(
                    not np.isfinite(value) or value < 0 for value in row[name].values()):
                raise ValueError("B2.28 diagnostic MSE differs")
    return index


def _read_label_index(root: Path) -> dict[str, Any]:
    contents = (root / "label_index.json").read_bytes()
    if sha256(contents) != B227_LABEL_SHA256:
        raise ValueError("B2.28 source label index checksum differs")
    index: dict[str, Any] = json.loads(contents)
    identities, _, _ = b227_cohorts()
    if (len(index["rows"]) != 60 or index["context"]["source_revision"] != B227_SOURCE
            or index["context"]["plan_sha256"] != B227_PLAN_SHA256
            or index["elapsed_seconds"] > 3600 or index["peak_rss_bytes"] >= 1_073_741_824
            or any(row["identity"] != identity or row["status"] != "succeeded"
                   for row, identity in zip(index["rows"], identities, strict=True))):
        raise ValueError("B2.28 source label population or provenance differs")
    return index


def _new_samples(root: Path, index: dict[str, Any], split: str,
                 repository: Path) -> tuple[TrajectorySample, ...]:
    if split not in ("train", "validation"):
        raise ValueError("B2.28 may open only development labels")
    environment = label_environment(repository)
    selected = []
    for row in index["rows"]:
        identity = row["identity"]
        if identity["split"] != split:
            continue
        label = read_position_label(root, row, identity, index["context"], environment)
        nx, ny, nz = label.case.problem.mesh.element_counts
        sample = TrajectorySample(
            case_id=label.case.case_id, split=split,  # type: ignore[arg-type]
            inputs=torch.from_numpy(encode_vector_load_case(label.case).input_tensor.copy()),
            target=torch.from_numpy(np.asarray(label.design_density, dtype=np.float32)
                                    .reshape((1, nz, ny, nx)).copy()), input_channels=13,
        )
        sample.validate()
        selected.append(sample)
    return tuple(sorted(selected, key=lambda sample: sample.case_id))


def run_fits(root: Path, data_root: Path, b221_root: Path, b226_root: Path,
             b227_root: Path, repository: Path, labels: dict[str, Any],
             groups: dict[str, tuple[ExperimentCase, ...]],
             targets: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    index = _read_fit_index(root, context)
    started, prior = perf_counter(), index["elapsed_seconds"]
    if len(index["rows"]) < 3:
        data_index = read_data_index(data_root, select_cases())
        train = _samples(b221_root, data_root, data_index, groups, "train",
                         targets, targets["context"])
        validation = _samples(b221_root, data_root, data_index, groups, "validation",
                              targets, targets["context"])
        new_train = _new_samples(b227_root, labels, "train", repository)
        train = tuple(sorted((*train, *new_train), key=lambda sample: sample.case_id))
        diagnostic = _new_samples(b227_root, labels, "validation", repository)
        diagnostic_groups = {direction: tuple(sample for sample in diagnostic
            if sample.case_id in {case.case_id for case in groups["diagnostic"]
                                 if case.problem.loads[0].direction == direction})
                             for direction in ("y", "z")}
        old_context = json.loads((b226_root / "fit_index.json").read_text())["context"]
        old_index = read_old_fit_index(b226_root, old_context)
        old_models = {row["seed"]: read_old_model(b226_root, row, old_context)
                      for row in old_index["rows"]}
        selected = frozenset(weighted_case_ids(groups))
        weights = {sample.case_id: Y_WEIGHT if sample.case_id in selected else 1.0
                   for sample in train}
        if (len(train) != TRAIN_COUNT or len(validation) != 12 or len(weights) != TRAIN_COUNT
                or len(diagnostic) != 20
                or {sample.case_id for sample in train}
                    != {case.case_id for case in groups["expanded_train"]}
                or any(len(samples) != 10 for samples in diagnostic_groups.values())):
            raise ValueError("B2.28 training or validation population differs")
        for position in range(len(index["rows"]), 3):
            if prior + perf_counter() - started > FIT_CAP:
                raise ValueError("B2.28 fit budget exhausted")
            seed = SEEDS[position]
            fit = fit_trajectory_seed(train, validation, seed=seed,
                                      model_factory=ContextCNN,
                                      expected_parameter_count=CONTEXT_MODEL_PARAMETER_COUNT,
                                      input_channels=13, case_weights=weights,
                                      expected_train_count=TRAIN_COUNT,
                                      expected_batches=BATCH_COUNT)
            metadata = {"version": "topolab.b2_28.checkpoint.v1", "context": context,
                        "seed": seed, "selected_epoch": fit.selected_epoch}
            checkpoint = save_tensors(dict(sorted(fit.state.items())),
                                      metadata={"topolab": canonical_bytes(metadata).decode()})
            checkpoint_sha = sha256(checkpoint)
            atomic_write(_checkpoint_path(root, seed, checkpoint_sha), checkpoint)
            history = {"version": "topolab.b2_28.history.v1", "context": context,
                       "seed": seed, "entries": fit.history}
            history_bytes = canonical_bytes(history)
            history_sha = sha256(history_bytes)
            atomic_write(root / "histories" / str(seed) / f"{history_sha}.json", history_bytes)
            selected_model = _read_model(root, {"seed": seed,
                "checkpoint_sha256": checkpoint_sha, "checkpoint_bytes": len(checkpoint),
                "selected_epoch": fit.selected_epoch}, context)
            index["rows"].append({"seed": seed, "epochs": len(fit.history),
                                  "selected_epoch": fit.selected_epoch,
                                  "selected_validation_loss": fit.selected_validation_loss,
                                  "fit_seconds": fit.seconds, "checkpoint_sha256": checkpoint_sha,
                                  "checkpoint_bytes": len(checkpoint),
                                  "history_sha256": history_sha,
                                  "history_bytes": len(history_bytes),
                                  "diagnostic_mse_by_direction": {direction: _diagnostic_mse(
                                      selected_model, samples)
                                      for direction, samples in diagnostic_groups.items()},
                                  "old_diagnostic_mse_by_direction": {direction: _diagnostic_mse(
                                      old_models[seed], samples)
                                      for direction, samples in diagnostic_groups.items()}})
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "fit_index.json", canonical_bytes(index))
            print(f"B2.28 fit {position + 1}/3", file=sys.stderr, flush=True)
    if (len(index["rows"]) != 3 or index["elapsed_seconds"] > FIT_CAP
            or index["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.28 fit Gate failed")
    return index


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    ratios: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    generalist_y_failures: Counter[str] = Counter()
    high_y_successes: Counter[str] = Counter()
    middle_y_successes: Counter[str] = Counter()
    quality_violations = 0
    for row in index["rows"]:
        case = row["case"]
        for item in row["outcomes"]:
            method = item["method"]
            ratios[(method, case["scale"], case["direction"])].append(item["paired_time_ratio"])
            if not item["succeeded"]:
                failures[method] += 1
                if case["direction"] == "y" and not case["specialist_route"]:
                    generalist_y_failures[method] += 1
            if item["succeeded"] and (item["operational"]["final_compliance"]
                > 1.001 * item["uniform_reference_compliance"]
                or item["operational"]["physical_volume_error"] > 0.005):
                quality_violations += 1
            if method != "uniform" and case["specialist_route"] and item["succeeded"]:
                high_y_successes[method.split("_")[0]] += 1
            if (method != "uniform" and case["scale"] == "large"
                    and case["direction"] == "y" and case["volume"] == VOLUMES[1]
                    and item["succeeded"]):
                middle_y_successes[method.split("_")[0]] += 1
    direction_means = {f"{method}/{scale}/{direction}": sum(values) / len(values)
                       for (method, scale, direction), values in sorted(ratios.items())}
    scale_means = {}
    for method in METHODS:
        for scale in ("small", "large"):
            values = [value for direction in ("y", "z")
                      for value in ratios[(method, scale, direction)]]
            if values:
                scale_means[f"{method}/{scale}"] = sum(values) / len(values)
    passing = []
    if len(index["rows"]) == 24:
        for seed in SEEDS:
            method = f"expanded_{seed}"
            if (all(scale_means[f"{method}/{scale}"] <= 0.90
                    and all(direction_means[f"{method}/{scale}/{direction}"] <= 1.0
                            for direction in ("y", "z"))
                    for scale in ("small", "large"))
                and failures[method] <= failures[f"old_{seed}"]
                and generalist_y_failures[method] <= 2
                and generalist_y_failures[method]
                    <= generalist_y_failures[f"old_{seed}"]):
                passing.append(seed)
    gate = (len(index["rows"]) == 24
            and all(len(row["outcomes"]) == len(METHODS) for row in index["rows"])
            and len(passing) >= 2 and high_y_successes["expanded"] >= 4
            and middle_y_successes["expanded"] >= 4
            and quality_violations == 0 and index["elapsed_seconds"] <= SCREEN_CAP
            and index["peak_rss_bytes"] <= MAX_RSS)
    return {"screen_index_sha256": sha256((root / "screen_index.json").read_bytes()),
            "cases": len(index["rows"]),
            "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
            "scale_means": scale_means, "direction_means": direction_means,
            "failure_counts": dict(sorted(failures.items())),
            "generalist_y_failure_counts": dict(sorted(generalist_y_failures.items())),
            "high_volume_large_y_successes": dict(high_y_successes),
            "middle_volume_large_y_successes": dict(middle_y_successes),
            "accepted_quality_violations": quality_violations,
            "passing_seeds": passing, "gate_passed": gate,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"]}


def run_screen(root: Path, b226_root: Path, b224_root: Path,
               cases: tuple[ExperimentCase, ...], references: dict[str, Any],
               context: dict[str, Any]) -> dict[str, Any]:
    fits = _read_fit_index(root, context)
    if len(fits["rows"]) != 3:
        raise ValueError("B2.28 screen requires complete fit")
    screen_context = {
        **context,
        "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
        "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
    }
    index = _index(root, "screen_index.json", screen_context, 24)
    for row, case in zip(index["rows"], cases, strict=False):
        if (row["case"]["case_id"] != case.case_id
                or [item["method"] for item in row["outcomes"]] != list(METHODS)):
            raise ValueError("B2.28 persisted screen case differs")
    if len(index["rows"]) == 24:
        return screen_summary(root, index)
    old_context = json.loads((b226_root / "fit_index.json").read_text())["context"]
    old_index = read_old_fit_index(b226_root, old_context)
    old = {row["seed"]: read_old_model(b226_root, row, old_context)
           for row in old_index["rows"]}
    specialist_context = json.loads((b224_root / "fit_index.json").read_text())["context"]
    specialist_index = read_specialist_fit_index(b224_root, specialist_context)
    specialist = {row["seed"]: read_specialist_model(b224_root, row, specialist_context)
                  for row in specialist_index["rows"]}
    expanded = {row["seed"]: _read_model(root, row, context) for row in fits["rows"]}
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 24):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.28 screen budget exhausted")
        case = cases[position]
        reference = _uniform_result(case, references["rows"][position]["uniform"])
        outcomes = [reference]
        for prefix, panel in (("old", old), ("expanded", expanded)):
            for seed in SEEDS:
                route_start = perf_counter()
                use_specialist = specialist_case(case)
                model = specialist[seed] if use_specialist else panel[seed]
                route_seconds = perf_counter() - route_start
                item = _charged_result(case, "candidate", seed, reference,
                                       model=model, encoder=encode_vector_load_case)
                item["method"] = f"{prefix}_{seed}"
                item["route"] = "specialist" if use_specialist else "generalist"
                item["timing"]["route_seconds"] = route_seconds
                item["timing"]["end_to_end_seconds"] += route_seconds
                item["paired_time_ratio"] = (item["timing"]["end_to_end_seconds"]
                                             / reference["timing"]["end_to_end_seconds"])
                outcomes.append(item)
        nx = case.problem.mesh.element_counts[0]
        index["rows"].append({"case": {"case_id": case.case_id,
                                       "scale": "small" if nx == 12 else "large",
                                       "direction": case.problem.loads[0].direction,
                                       "volume": case.problem.optimization.volume_fraction,
                                       "specialist_route": specialist_case(case)},
                              "outcomes": outcomes})
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "screen_index.json", canonical_bytes(index))
        print(f"B2.28 screen {position + 1}/24", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b221-root", type=Path, default=Path("/tmp/topolab-b221"))
    parser.add_argument("--b224-root", type=Path, default=Path("/tmp/topolab-b224"))
    parser.add_argument("--b226-root", type=Path, default=Path("/tmp/topolab-b226"))
    parser.add_argument("--b227-root", type=Path, default=Path("/tmp/topolab-b227"))
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--references", action="store_true")
    stage.add_argument("--fit", action="store_true")
    stage.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    groups, screen, blocked = cohorts()
    plan = plan_payload(groups, screen, blocked)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.28 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    data_root = _external_root(repository, args.b24_root)
    b221_root = _external_root(repository, args.b221_root)
    b224_root = _external_root(repository, args.b224_root)
    b226_root = _external_root(repository, args.b226_root)
    b227_root = _external_root(repository, args.b227_root)
    if len({root, data_root, b221_root, b224_root, b226_root, b227_root}) != 6:
        raise ValueError("B2.28 source and output roots must differ")
    for source, filename, digest in (
        (b221_root, "validation_target_index.json", B221_TARGET_SHA256),
        (b224_root, "fit_index.json", B224_FIT_SHA256),
        (b224_root, "screen_index.json", B224_SCREEN_SHA256),
        (b226_root, "fit_index.json", B226_FIT_SHA256),
        (b226_root, "screen_index.json", B226_SCREEN_SHA256),
        (b227_root, "label_index.json", B227_LABEL_SHA256),
    ):
        if sha256((source / filename).read_bytes()) != digest:
            raise ValueError(f"B2.28 source {filename} digest differs")
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime, "b221_validation_target_index_sha256": B221_TARGET_SHA256,
               "b226_fit_index_sha256": B226_FIT_SHA256,
               "b227_label_index_sha256": B227_LABEL_SHA256,
               "b224_fit_index_sha256": B224_FIT_SHA256}
    if not any((args.references, args.fit, args.screen)):
        print(json.dumps({"plan_sha256": plan["plan_sha256"],
                          "source_revision": revision,
                          "train_cases": len(groups["expanded_train"]),
                          "validation_cases": len(groups["validation"]),
                          "diagnostic_cases": len(groups["diagnostic"]),
                          "weighted_cases": WEIGHTED_COUNT,
                          "screen_cases": len(screen), "blocked_cases": len(blocked)},
                         sort_keys=True))
        return 0
    if args.references:
        references = run_references(root, "reference_index.json", context,
                                    screen, REFERENCE_CAP)
        passed = reference_gate(references, screen, REFERENCE_CAP)
        print(json.dumps({"cases": len(references["rows"]), "passed": passed,
                          "index_sha256": sha256((root / "reference_index.json").read_bytes())},
                         sort_keys=True))
        return 0 if passed else 1
    references = _index(root, "reference_index.json", context, 24)
    if not reference_gate(references, screen, REFERENCE_CAP):
        raise ValueError("B2.28 reference Gate required")
    target_context = json.loads((b221_root / "validation_target_index.json").read_text())["context"]
    targets = _index(b221_root, "validation_target_index.json", target_context, 12)
    if len(targets["rows"]) != 12:
        raise ValueError("B2.21 validation targets incomplete")
    if args.fit:
        labels = _read_label_index(b227_root)
        fits = run_fits(root, data_root, b221_root, b226_root, b227_root,
                        repository, labels, groups, targets, context)
        print(json.dumps({"fits": [(row["seed"], row["selected_epoch"])
                                   for row in fits["rows"]],
                          "elapsed_seconds": fits["elapsed_seconds"],
                          "fit_index_sha256": sha256((root / "fit_index.json").read_bytes())},
                         sort_keys=True))
        return 0
    summary = run_screen(root, b226_root, b224_root,
                         screen, references, context)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
