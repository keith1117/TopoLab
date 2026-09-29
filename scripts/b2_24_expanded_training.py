"""B2.24 expanded-position specialist fit and disjoint development screen."""

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
from b2_5_prototype import atomic_write, canonical_bytes, read_data_index, sha256, source_snapshot
from b2_6_trajectory import _external_root, _small_case
from b2_7_global_load import _peak_rss
from b2_9_vector_load import _index
from b2_11_reference_budget import versioned_case
from b2_20_operational_selection import (
    B212_FIT_INDEX_SHA256,
    _control_models,
    _uniform_result,
    reference_gate,
    run_references,
)
from b2_21_terminal_target import _samples
from b2_22_y_specialist import (
    _read_fit_index as read_old_fit_index,
)
from b2_22_y_specialist import (
    _read_model as read_old_model,
)
from b2_22_y_specialist import (
    cohorts as b222_cohorts,
)
from b2_22_y_specialist import (
    specialist_case,
)
from b2_23_position_labels import (
    _environment as b223_environment,
)
from b2_23_position_labels import (
    _read_label as read_b223_label,
)
from b2_23_position_labels import (
    cohorts as b223_cohorts,
)
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import _charged_result
from topolab.b2_6_trajectory import SEEDS, TrajectorySample, fit_trajectory_seed
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_12_context_cnn import CONTEXT_MODEL_PARAMETER_COUNT, ContextCNN
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_24.expanded_position_training.v1"
EXPECTED_PLAN_SHA256 = "50230a66db17c26ed4665bce41142c61b3e5ffc5f2dcfb83988d77d84884dd94"
B223_LABEL_SHA256 = "ca1060430f11dc6e3aec497b3297a33191686e9d410c5202bec4d65278cae850"
B222_FIT_SHA256 = "a7a0f598bff793e860b8d561976f3be4b38a00fca7864bfb86854c56acfb5dde"
B222_SCREEN_SHA256 = "62ffe463c863f5ff57b88687a5cc9aeb0abf5261087335f4e790e5f3b3f58632"
B221_TARGET_SHA256 = "3e7add2c85650bcb5ac0329236678887baaf2fc3acd4882a1f8f8fc7070796ab"
VOLUMES = (0.3665, 0.5165, 0.5965)
POSITIONS = ((2, 1), (4, 2))
SPECIALIST_VOLUME = 0.55
HIGH_Y_WEIGHT = 8.0
TRAIN_COUNT = 488
VALIDATION_COUNT = 12
BATCH_COUNT = 61
REFERENCE_CAP = 3_600.0
FIT_CAP = 7_200.0
SCREEN_CAP = 16_000.0
MAX_RSS = 2_147_483_648
METHODS = ("uniform", *(f"old_{seed}" for seed in SEEDS),
           *(f"expanded_{seed}" for seed in SEEDS))


def cohorts() -> tuple[dict[str, tuple[ExperimentCase, ...]],
                       tuple[ExperimentCase, ...], tuple[ExperimentCase, ...]]:
    groups, old_screen, prior_blocked = b222_cohorts()
    _, new_labels, _ = b223_cohorts()
    blocked = tuple(sorted({case.case_id: case for case in (
        *prior_blocked, *old_screen, *new_labels,
    )}.values(), key=lambda case: case.case_id))
    blocked_volumes = {case.problem.optimization.volume_fraction for case in blocked}
    blocked_volumes.update(index / 100 for index in range(20, 61, 5))
    blocked_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & blocked_volumes:
        raise ValueError("B2.24 screen volume intersects prior evidence")
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
    if (len(blocked) != 790 or len(screen) != 24
            or len({case.case_id for case in (*blocked, *screen)}) != 814
            or len(strata) != 4 or set(strata.values()) != {6}
            or sum(specialist_case(case) for case in screen) != 2
            or any(case.problem.optimization.max_iterations != 360 for case in screen)):
        raise ValueError("B2.24 population, strata, or route differs")
    return groups, screen, blocked


def plan_payload(groups: dict[str, tuple[ExperimentCase, ...]],
                 screen: tuple[ExperimentCase, ...],
                 blocked: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    new_identities, _, _ = b223_cohorts()
    added_train = [item["case_id"] for item in new_identities
                   if item["split"] == "train"]
    added_validation = [item["case_id"] for item in new_identities
                        if item["split"] == "validation"]
    high_train = [case.case_id for case in groups["train"]
                  if case.problem.loads[0].direction == "y"
                  and case.problem.optimization.volume_fraction >= SPECIALIST_VOLUME]
    high_validation = [case.case_id for case in groups["validation"]
                       if case.problem.loads[0].direction == "y"
                       and case.problem.optimization.volume_fraction >= 0.525]
    if (len(high_train) != 52 or len(high_validation) != 2
            or len(added_train) != 20 or len(added_validation) != 10):
        raise ValueError("B2.24 specialist development population differs")
    identity = {
        "version": PLAN_VERSION,
        "intervention": "add_20_position_labels_to_unchanged_weighted_specialist",
        "b222_screen_index_sha256": B222_SCREEN_SHA256,
        "b222_fit_index_sha256": B222_FIT_SHA256,
        "b223_label_index_sha256": B223_LABEL_SHA256,
        "b221_validation_target_index_sha256": B221_TARGET_SHA256,
        "b212_fit_index_sha256": B212_FIT_INDEX_SHA256,
        "model_version": "topolab.b2_12.context_cnn.v1",
        "input_version": "topolab.b2_9.vector_load.v1",
        "target": "audited_uniform_terminal_design_float32",
        "train_case_ids": [case.case_id for case in groups["train"]],
        "added_train_case_ids": added_train,
        "added_diagnostic_validation_case_ids": added_validation,
        "high_weight_train_case_ids": sorted((*high_train, *added_train)),
        "selection_validation_case_ids": high_validation,
        "train_count": TRAIN_COUNT,
        "validation_count": VALIDATION_COUNT,
        "batches_per_epoch": BATCH_COUNT,
        "blocked_case_ids": [case.case_id for case in blocked],
        "screen_case_ids": [case.case_id for case in screen],
        "screen_volumes": list(VOLUMES),
        "screen_positions_small": [list(position) for position in POSITIONS],
        "training_high_y_weight": HIGH_Y_WEIGHT,
        "route": {"mesh": [24, 12, 6], "direction": "y",
                  "minimum_volume": SPECIALIST_VOLUME},
        "methods": list(METHODS),
        "seeds": list(SEEDS),
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "screen_solver_budget": 360,
        "caps_seconds": {"references": REFERENCE_CAP, "fit": FIT_CAP,
                         "screen": SCREEN_CAP},
        "max_rss_bytes": MAX_RSS,
        "gate_scale_mean_max": 0.90,
        "gate_direction_mean_max": 1.0,
        "gate_required_expanded_seeds": 2,
        "gate_failures_no_more_than_old": True,
        "gate_high_volume_large_y_successes_min": 4,
        "gate_high_volume_large_y_improvement_min": 1,
        "gate_accepted_quality_violations_max": 0,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _checkpoint_path(root: Path, seed: int, digest: str) -> Path:
    return root / "checkpoints" / str(seed) / f"{digest}.safetensors"


def _read_model(root: Path, row: dict[str, Any], context: dict[str, Any]) -> ContextCNN:
    contents = _checkpoint_path(root, row["seed"], row["checkpoint_sha256"]).read_bytes()
    if sha256(contents) != row["checkpoint_sha256"] or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.24 checkpoint checksum or size differs")
    length = int.from_bytes(contents[:8], "little")
    metadata = json.loads(json.loads(contents[8:8 + length])["__metadata__"]["topolab"])
    if metadata != {"version": "topolab.b2_24.checkpoint.v1", "context": context,
                    "seed": row["seed"], "selected_epoch": row["selected_epoch"]}:
        raise ValueError("B2.24 checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = ContextCNN()
    expected = model.state_dict()
    if set(state) != set(expected) or any(
        tensor.dtype != torch.float32 or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all() for name, tensor in state.items()
    ):
        raise ValueError("B2.24 checkpoint tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_fit_index(root: Path, context: dict[str, Any]) -> dict[str, Any]:
    index = _index(root, "fit_index.json", context, 3)
    for row, seed in zip(index["rows"], SEEDS, strict=False):
        if row["seed"] != seed:
            raise ValueError("B2.24 fit seed order differs")
        _read_model(root, row, context)
        contents = (root / "histories" / str(seed) / f"{row['history_sha256']}.json").read_bytes()
        if sha256(contents) != row["history_sha256"] or len(contents) != row["history_bytes"]:
            raise ValueError("B2.24 fit history checksum or size differs")
        history = json.loads(contents)
        if (canonical_bytes(history) != contents or history["context"] != context
                or history["seed"] != seed or history["version"] != "topolab.b2_24.history.v1"
                or not history["entries"] or len(history["entries"]) > 200):
            raise ValueError("B2.24 fit history provenance differs")
        entries = history["entries"]
        minimum = min(item["validation_loss"] for item in entries)
        first = next(item["epoch"] for item in entries if item["validation_loss"] == minimum)
        if (first != row["selected_epoch"] or minimum != row["selected_validation_loss"]
                or [item["epoch"] for item in entries] != list(range(1, len(entries) + 1))
                or (len(entries) < 200 and len(entries) - first != 25)):
            raise ValueError("B2.24 fit selection differs")
        if any(not np.isfinite(row[key]) or row[key] < 0
               for key in ("diagnostic_mse", "old_diagnostic_mse")):
            raise ValueError("B2.24 diagnostic MSE differs")
    return index


def _new_samples(b223_root: Path, rows: tuple[dict[str, Any], ...],
                 label_context: dict[str, Any], split: str,
                 repository: Path) -> tuple[TrajectorySample, ...]:
    environment = b223_environment(repository)
    selected = []
    for row in rows:
        identity = row["identity"]
        if identity["split"] != split:
            continue
        label = read_b223_label(b223_root, row, identity, label_context, environment)
        nx, ny, nz = label.case.problem.mesh.element_counts
        target = torch.from_numpy(np.asarray(label.design_density, dtype=np.float32)
                                  .reshape((1, nz, ny, nx)).copy())
        sample = TrajectorySample(
            case_id=label.case.case_id, split=split,  # type: ignore[arg-type]
            inputs=torch.from_numpy(encode_vector_load_case(label.case).input_tensor.copy()),
            target=target, input_channels=13,
        )
        sample.validate()
        selected.append(sample)
    return tuple(sorted(selected, key=lambda sample: sample.case_id))


def _diagnostic_mse(model: ContextCNN,
                    samples: tuple[TrajectorySample, ...]) -> float:
    model.eval()
    with torch.no_grad():
        total = sum(float(torch.square(model(sample.inputs.unsqueeze(0))
                                       - sample.target.unsqueeze(0)).mean().item())
                    for sample in samples)
    return total / len(samples)


def run_fits(root: Path, data_root: Path, b221_root: Path, b222_root: Path,
             b223_root: Path, repository: Path, label_index: dict[str, Any],
             groups: dict[str, tuple[ExperimentCase, ...]],
             target_index: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    index = _read_fit_index(root, context)
    started, prior = perf_counter(), index["elapsed_seconds"]
    if len(index["rows"]) < 3:
        data_index = read_data_index(data_root, select_cases())
        train = _samples(b221_root, data_root, data_index, groups, "train",
                         target_index, target_index["context"])
        validation = _samples(b221_root, data_root, data_index, groups, "validation",
                              target_index, target_index["context"])
        new_train = _new_samples(b223_root, tuple(label_index["rows"]),
                                 label_index["context"], "train", repository)
        train = tuple(sorted((*train, *new_train), key=lambda sample: sample.case_id))
        diagnostic = _new_samples(b223_root, tuple(label_index["rows"]),
                                  label_index["context"], "validation", repository)
        if (len(train) != TRAIN_COUNT or len(validation) != VALIDATION_COUNT
                or len(diagnostic) != 10):
            raise ValueError("B2.24 training or diagnostic population differs")
        old_index = read_old_fit_index(
            b222_root, json.loads((b222_root / "fit_index.json").read_text())["context"]
        )
        old_models = {row["seed"]: read_old_model(
            b222_root, row, old_index["context"]) for row in old_index["rows"]}
        high_ids = {case.case_id for case in groups["train"]
                    if case.problem.loads[0].direction == "y"
                    and case.problem.optimization.volume_fraction >= SPECIALIST_VOLUME}
        high_ids.update(sample.case_id for sample in new_train)
        weights = {sample.case_id: HIGH_Y_WEIGHT if sample.case_id in high_ids else 1.0
                   for sample in train}
        selection = frozenset(case.case_id for case in groups["validation"]
                              if case.problem.loads[0].direction == "y"
                              and case.problem.optimization.volume_fraction >= 0.525)
        for position in range(len(index["rows"]), 3):
            if prior + perf_counter() - started > FIT_CAP:
                raise ValueError("B2.24 fit budget exhausted")
            seed = SEEDS[position]
            fit = fit_trajectory_seed(train, validation, seed=seed,
                                      model_factory=ContextCNN,
                                      expected_parameter_count=CONTEXT_MODEL_PARAMETER_COUNT,
                                      input_channels=13, case_weights=weights,
                                      selection_case_ids=selection,
                                      expected_train_count=TRAIN_COUNT,
                                      expected_validation_count=VALIDATION_COUNT,
                                      expected_batches=BATCH_COUNT)
            metadata = {"version": "topolab.b2_24.checkpoint.v1", "context": context,
                        "seed": seed, "selected_epoch": fit.selected_epoch}
            checkpoint = save_tensors(dict(sorted(fit.state.items())),
                                      metadata={"topolab": canonical_bytes(metadata).decode()})
            digest = sha256(checkpoint)
            atomic_write(_checkpoint_path(root, seed, digest), checkpoint)
            history = {"version": "topolab.b2_24.history.v1", "context": context,
                       "seed": seed, "entries": fit.history}
            history_bytes = canonical_bytes(history)
            history_sha = sha256(history_bytes)
            atomic_write(root / "histories" / str(seed) / f"{history_sha}.json", history_bytes)
            index["rows"].append({"seed": seed, "epochs": len(fit.history),
                                  "selected_epoch": fit.selected_epoch,
                                  "selected_validation_loss": fit.selected_validation_loss,
                                  "fit_seconds": fit.seconds, "checkpoint_sha256": digest,
                                  "checkpoint_bytes": len(checkpoint),
                                  "history_sha256": history_sha,
                                  "history_bytes": len(history_bytes),
                                  "diagnostic_mse": _diagnostic_mse(_read_model(
                                      root, {"seed": seed, "checkpoint_sha256": digest,
                                             "checkpoint_bytes": len(checkpoint),
                                             "selected_epoch": fit.selected_epoch}, context),
                                      diagnostic),
                                  "old_diagnostic_mse": _diagnostic_mse(old_models[seed],
                                                                          diagnostic)})
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "fit_index.json", canonical_bytes(index))
            print(f"B2.24 fit {position + 1}/3", file=sys.stderr, flush=True)
    if (len(index["rows"]) != 3 or index["elapsed_seconds"] > FIT_CAP
            or index["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.24 fit Gate failed")
    return index


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    ratios: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    high_y_successes: Counter[str] = Counter()
    quality_violations = 0
    for row in index["rows"]:
        case = row["case"]
        for item in row["outcomes"]:
            method = item["method"]
            ratios[(method, case["scale"], case["direction"])].append(item["paired_time_ratio"])
            if not item["succeeded"]:
                failures[method] += 1
            if item["succeeded"] and (item["operational"]["final_compliance"]
                > 1.001 * item["uniform_reference_compliance"]
                or item["operational"]["physical_volume_error"] > 0.005):
                quality_violations += 1
            if (method != "uniform" and case["specialist_route"]
                    and item["succeeded"]):
                high_y_successes["expanded" if method.startswith("expanded_")
                                 else "old"] += 1
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
                and failures[method] <= failures[f"old_{seed}"]):
                passing.append(seed)
    gate = (len(index["rows"]) == 24
            and all(len(row["outcomes"]) == len(METHODS) for row in index["rows"])
            and len(passing) >= 2 and high_y_successes["expanded"] >= 4
            and high_y_successes["expanded"] > high_y_successes["old"]
            and quality_violations == 0 and index["elapsed_seconds"] <= SCREEN_CAP
            and index["peak_rss_bytes"] <= MAX_RSS)
    return {"screen_index_sha256": sha256((root / "screen_index.json").read_bytes()),
            "cases": len(index["rows"]),
            "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
            "scale_means": scale_means, "direction_means": direction_means,
            "failure_counts": dict(sorted(failures.items())),
            "high_volume_large_y_successes": dict(high_y_successes),
            "accepted_quality_violations": quality_violations,
            "passing_seeds": passing, "gate_passed": gate,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"]}


def run_screen(root: Path, b212_root: Path, b222_root: Path,
               cases: tuple[ExperimentCase, ...],
               references: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    fits = _read_fit_index(root, context)
    if len(fits["rows"]) != 3:
        raise ValueError("B2.24 screen requires complete fit")
    screen_context = {
        **context,
        "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
        "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
    }
    index = _index(root, "screen_index.json", screen_context, 24)
    for row, case in zip(index["rows"], cases, strict=False):
        if (row["case"]["case_id"] != case.case_id
                or [item["method"] for item in row["outcomes"]] != list(METHODS)):
            raise ValueError("B2.24 persisted screen case differs")
    if len(index["rows"]) == 24:
        return screen_summary(root, index)
    controls = _control_models(b212_root)
    old_index = read_old_fit_index(
        b222_root, json.loads((b222_root / "fit_index.json").read_text())["context"]
    )
    old_specialists = {row["seed"]: read_old_model(
        b222_root, row, old_index["context"]) for row in old_index["rows"]}
    expanded = {row["seed"]: _read_model(root, row, context) for row in fits["rows"]}
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 24):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.24 screen budget exhausted")
        case = cases[position]
        reference = _uniform_result(case, references["rows"][position]["uniform"])
        outcomes = [reference]
        for name, specialists in (("old", old_specialists), ("expanded", expanded)):
            for seed in SEEDS:
                route_start = perf_counter()
                use_specialist = specialist_case(case)
                model = specialists[seed] if use_specialist else controls[seed]
                route_seconds = perf_counter() - route_start
                item = _charged_result(case, "candidate", seed, reference,
                                       model=model, encoder=encode_vector_load_case)
                item["method"] = f"{name}_{seed}"
                item["route"] = "specialist" if use_specialist else "context"
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
        print(f"B2.24 screen {position + 1}/24", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b212-root", type=Path, default=Path("/tmp/topolab-b212"))
    parser.add_argument("--b221-root", type=Path, default=Path("/tmp/topolab-b221"))
    parser.add_argument("--b222-root", type=Path, default=Path("/tmp/topolab-b222"))
    parser.add_argument("--b223-root", type=Path, default=Path("/tmp/topolab-b223"))
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--references", action="store_true")
    stage.add_argument("--fit", action="store_true")
    stage.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    groups, screen, blocked = cohorts()
    plan = plan_payload(groups, screen, blocked)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.24 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    data_root = _external_root(repository, args.b24_root)
    b212_root = _external_root(repository, args.b212_root)
    b221_root = _external_root(repository, args.b221_root)
    b222_root = _external_root(repository, args.b222_root)
    b223_root = _external_root(repository, args.b223_root)
    if len({root, data_root, b212_root, b221_root, b222_root, b223_root}) != 6:
        raise ValueError("B2.24 source and output roots must differ")
    if sha256((b222_root / "screen_index.json").read_bytes()) != B222_SCREEN_SHA256:
        raise ValueError("B2.22 exposure evidence differs")
    if sha256((b222_root / "fit_index.json").read_bytes()) != B222_FIT_SHA256:
        raise ValueError("B2.22 specialist fit differs")
    if sha256((b223_root / "label_index.json").read_bytes()) != B223_LABEL_SHA256:
        raise ValueError("B2.23 position labels differ")
    if sha256((b221_root / "validation_target_index.json").read_bytes()) != B221_TARGET_SHA256:
        raise ValueError("B2.21 validation targets differ")
    if sha256((b212_root / "fit_index.json").read_bytes()) != B212_FIT_INDEX_SHA256:
        raise ValueError("B2.12 controls differ")
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime, "b221_validation_target_index_sha256": B221_TARGET_SHA256,
               "b222_fit_index_sha256": B222_FIT_SHA256,
               "b223_label_index_sha256": B223_LABEL_SHA256}
    if not any((args.references, args.fit, args.screen)):
        print(json.dumps({"plan_sha256": plan["plan_sha256"],
                          "source_revision": revision,
                          "train_cases": TRAIN_COUNT,
                          "validation_cases": len(groups["validation"]),
                          "diagnostic_validation_cases": 10,
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
        raise ValueError("B2.24 reference Gate required")
    target_context = json.loads(
        (b221_root / "validation_target_index.json").read_text()
    )["context"]
    target_index = _index(b221_root, "validation_target_index.json", target_context, 12)
    if len(target_index["rows"]) != 12:
        raise ValueError("B2.21 validation targets incomplete")
    label_context = json.loads((b223_root / "label_index.json").read_text())["context"]
    label_index = _index(b223_root, "label_index.json", label_context, 30)
    if len(label_index["rows"]) != 30:
        raise ValueError("B2.23 label index incomplete")
    if args.fit:
        fits = run_fits(root, data_root, b221_root, b222_root, b223_root,
                        repository, label_index, groups, target_index, context)
        print(json.dumps({"fits": [(row["seed"], row["selected_epoch"])
                                   for row in fits["rows"]],
                          "elapsed_seconds": fits["elapsed_seconds"],
                          "fit_index_sha256": sha256((root / "fit_index.json").read_bytes())},
                         sort_keys=True))
        return 0
    summary = run_screen(root, b212_root, b222_root, screen, references, context)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
