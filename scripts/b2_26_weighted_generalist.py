"""B2.26 fixed y-weighted terminal generalist and fresh development screen."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any

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
    B212_FIT_INDEX_SHA256,
    _control_models,
    _uniform_result,
    reference_gate,
    run_references,
)
from b2_21_terminal_target import _read_fit_index as read_terminal_fit_index
from b2_21_terminal_target import _read_model as read_terminal_model
from b2_21_terminal_target import _samples
from b2_24_expanded_training import _read_fit_index as read_specialist_fit_index
from b2_24_expanded_training import _read_model as read_specialist_model
from b2_24_expanded_training import cohorts as b224_cohorts
from b2_24_expanded_training import specialist_case
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import _charged_result
from topolab.b2_6_trajectory import SEEDS, fit_trajectory_seed
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_12_context_cnn import CONTEXT_MODEL_PARAMETER_COUNT, ContextCNN
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_26.weighted_generalist.v1"
EXPECTED_PLAN_SHA256 = "bd6b355036024c2bbd31b09a62d4141d868afae526025f4e395c2abe97440a4c"
B221_TARGET_SHA256 = "3e7add2c85650bcb5ac0329236678887baaf2fc3acd4882a1f8f8fc7070796ab"
B221_FIT_SHA256 = "a997e1f69703126b4c0fdf7f2c87363f3fb6093c3970ab383f8765e60d2149d5"
B224_FIT_SHA256 = "89bacfec6fbdfd2732ab74404626dc33a914b7cf788750f02276319b7e73700a"
B224_SCREEN_SHA256 = "e77ad2eb6670dcae64e14c51d67b4b6ad6dc05d2d8e57448be39c8c584db1075"
VOLUMES = (0.3725, 0.5225, 0.5955)
POSITIONS = ((1, 2), (4, 1))
Y_WEIGHT = 8.0
Y_MIN_VOLUME = 0.5
WEIGHTED_COUNT = 78
REFERENCE_CAP = 3_600.0
FIT_CAP = 7_200.0
SCREEN_CAP = 24_000.0
MAX_RSS = 2_147_483_648
METHODS = ("uniform", *(f"operational_{seed}" for seed in SEEDS),
           *(f"terminal_{seed}" for seed in SEEDS),
           *(f"weighted_{seed}" for seed in SEEDS))


def cohorts() -> tuple[dict[str, tuple[ExperimentCase, ...]],
                       tuple[ExperimentCase, ...], tuple[ExperimentCase, ...]]:
    groups, prior_screen, prior_blocked = b224_cohorts()
    blocked = tuple(sorted({case.case_id: case for case in (
        *prior_blocked, *prior_screen,
    )}.values(), key=lambda case: case.case_id))
    excluded = {case.problem.optimization.volume_fraction for case in blocked}
    excluded.update(index / 100 for index in range(20, 61, 5))
    excluded.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & excluded:
        raise ValueError("B2.26 screen volume intersects exposed or reserved evidence")
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
    if (len(blocked) != 814 or len(screen) != 24
            or len({case.case_id for case in (*blocked, *screen)}) != 838
            or len(strata) != 4 or set(strata.values()) != {6}
            or sum(specialist_case(case) for case in screen) != 2
            or any(case.problem.optimization.max_iterations != 360 for case in screen)):
        raise ValueError("B2.26 population, strata, or route differs")
    return groups, screen, blocked


def weighted_case_ids(groups: dict[str, tuple[ExperimentCase, ...]]) -> tuple[str, ...]:
    selected = tuple(sorted(case.case_id for case in groups["train"]
                            if case.problem.loads[0].direction == "y"
                            and case.problem.optimization.volume_fraction >= Y_MIN_VOLUME))
    if len(selected) != WEIGHTED_COUNT:
        raise ValueError("B2.26 weighted training population differs")
    return selected


def plan_payload(groups: dict[str, tuple[ExperimentCase, ...]],
                 screen: tuple[ExperimentCase, ...],
                 blocked: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "intervention": "terminal_target_case_weight_8_y_volume_at_least_0_5",
        "b24_data_index_sha256": DATA_INDEX_SHA256,
        "b221_target_index_sha256": B221_TARGET_SHA256,
        "b221_fit_index_sha256": B221_FIT_SHA256,
        "b224_fit_index_sha256": B224_FIT_SHA256,
        "b224_screen_index_sha256": B224_SCREEN_SHA256,
        "b212_fit_index_sha256": B212_FIT_INDEX_SHA256,
        "model_version": "topolab.b2_12.context_cnn.v1",
        "input_version": "topolab.b2_9.vector_load.v1",
        "target": "audited_uniform_terminal_design_float32",
        "train_case_ids": [case.case_id for case in groups["train"]],
        "validation_case_ids": [case.case_id for case in groups["validation"]],
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
        "gate_required_weighted_seeds": 2,
        "gate_weighted_failures_no_more_than_operational": True,
        "gate_non_specialist_y_failures_per_seed_max": 2,
        "gate_non_specialist_y_failures_no_more_than_terminal": True,
        "gate_high_volume_large_y_successes_min": 4,
        "gate_accepted_quality_violations_max": 0,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _checkpoint_path(root: Path, seed: int, digest: str) -> Path:
    return root / "checkpoints" / str(seed) / f"{digest}.safetensors"


def _read_model(root: Path, row: dict[str, Any], context: dict[str, Any]) -> ContextCNN:
    contents = _checkpoint_path(root, row["seed"], row["checkpoint_sha256"]).read_bytes()
    if sha256(contents) != row["checkpoint_sha256"] or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.26 checkpoint checksum or size differs")
    length = int.from_bytes(contents[:8], "little")
    metadata = json.loads(json.loads(contents[8:8 + length])["__metadata__"]["topolab"])
    if metadata != {"version": "topolab.b2_26.checkpoint.v1", "context": context,
                    "seed": row["seed"], "selected_epoch": row["selected_epoch"]}:
        raise ValueError("B2.26 checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = ContextCNN()
    expected = model.state_dict()
    if set(state) != set(expected) or any(
        tensor.dtype != torch.float32 or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all() for name, tensor in state.items()
    ):
        raise ValueError("B2.26 checkpoint tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_fit_index(root: Path, context: dict[str, Any]) -> dict[str, Any]:
    index = _index(root, "fit_index.json", context, 3)
    for row, seed in zip(index["rows"], SEEDS, strict=False):
        if row["seed"] != seed:
            raise ValueError("B2.26 fit seed order differs")
        _read_model(root, row, context)
        contents = (root / "histories" / str(seed) / f"{row['history_sha256']}.json").read_bytes()
        if sha256(contents) != row["history_sha256"] or len(contents) != row["history_bytes"]:
            raise ValueError("B2.26 fit history checksum or size differs")
        history = json.loads(contents)
        if (canonical_bytes(history) != contents or history["context"] != context
                or history["seed"] != seed or history["version"] != "topolab.b2_26.history.v1"
                or not history["entries"] or len(history["entries"]) > 200):
            raise ValueError("B2.26 fit history provenance differs")
        entries = history["entries"]
        minimum = min(item["validation_loss"] for item in entries)
        first = next(item["epoch"] for item in entries if item["validation_loss"] == minimum)
        if (first != row["selected_epoch"] or minimum != row["selected_validation_loss"]
                or [item["epoch"] for item in entries] != list(range(1, len(entries) + 1))
                or (len(entries) < 200 and len(entries) - first != 25)):
            raise ValueError("B2.26 fit selection differs")
    return index


def run_fits(root: Path, data_root: Path, b221_root: Path,
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
        selected = frozenset(weighted_case_ids(groups))
        weights = {sample.case_id: Y_WEIGHT if sample.case_id in selected else 1.0
                   for sample in train}
        if len(train) != 468 or len(validation) != 12 or len(weights) != 468:
            raise ValueError("B2.26 training or validation population differs")
        for position in range(len(index["rows"]), 3):
            if prior + perf_counter() - started > FIT_CAP:
                raise ValueError("B2.26 fit budget exhausted")
            seed = SEEDS[position]
            fit = fit_trajectory_seed(train, validation, seed=seed,
                                      model_factory=ContextCNN,
                                      expected_parameter_count=CONTEXT_MODEL_PARAMETER_COUNT,
                                      input_channels=13, case_weights=weights)
            metadata = {"version": "topolab.b2_26.checkpoint.v1", "context": context,
                        "seed": seed, "selected_epoch": fit.selected_epoch}
            checkpoint = save_tensors(dict(sorted(fit.state.items())),
                                      metadata={"topolab": canonical_bytes(metadata).decode()})
            checkpoint_sha = sha256(checkpoint)
            atomic_write(_checkpoint_path(root, seed, checkpoint_sha), checkpoint)
            history = {"version": "topolab.b2_26.history.v1", "context": context,
                       "seed": seed, "entries": fit.history}
            history_bytes = canonical_bytes(history)
            history_sha = sha256(history_bytes)
            atomic_write(root / "histories" / str(seed) / f"{history_sha}.json", history_bytes)
            index["rows"].append({"seed": seed, "epochs": len(fit.history),
                                  "selected_epoch": fit.selected_epoch,
                                  "selected_validation_loss": fit.selected_validation_loss,
                                  "fit_seconds": fit.seconds, "checkpoint_sha256": checkpoint_sha,
                                  "checkpoint_bytes": len(checkpoint),
                                  "history_sha256": history_sha,
                                  "history_bytes": len(history_bytes)})
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "fit_index.json", canonical_bytes(index))
            print(f"B2.26 fit {position + 1}/3", file=sys.stderr, flush=True)
    if (len(index["rows"]) != 3 or index["elapsed_seconds"] > FIT_CAP
            or index["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.26 fit Gate failed")
    return index


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    ratios: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    generalist_y_failures: Counter[str] = Counter()
    high_y_successes: Counter[str] = Counter()
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
            method = f"weighted_{seed}"
            if (all(scale_means[f"{method}/{scale}"] <= 0.90
                    and all(direction_means[f"{method}/{scale}/{direction}"] <= 1.0
                            for direction in ("y", "z"))
                    for scale in ("small", "large"))
                and failures[method] <= failures[f"operational_{seed}"]
                and generalist_y_failures[method] <= 2
                and generalist_y_failures[method]
                    <= generalist_y_failures[f"terminal_{seed}"]):
                passing.append(seed)
    gate = (len(index["rows"]) == 24
            and all(len(row["outcomes"]) == len(METHODS) for row in index["rows"])
            and len(passing) >= 2 and high_y_successes["weighted"] >= 4
            and quality_violations == 0 and index["elapsed_seconds"] <= SCREEN_CAP
            and index["peak_rss_bytes"] <= MAX_RSS)
    return {"screen_index_sha256": sha256((root / "screen_index.json").read_bytes()),
            "cases": len(index["rows"]),
            "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
            "scale_means": scale_means, "direction_means": direction_means,
            "failure_counts": dict(sorted(failures.items())),
            "generalist_y_failure_counts": dict(sorted(generalist_y_failures.items())),
            "high_volume_large_y_successes": dict(high_y_successes),
            "accepted_quality_violations": quality_violations,
            "passing_seeds": passing, "gate_passed": gate,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"]}


def run_screen(root: Path, b212_root: Path, b221_root: Path, b224_root: Path,
               cases: tuple[ExperimentCase, ...], references: dict[str, Any],
               context: dict[str, Any]) -> dict[str, Any]:
    fits = _read_fit_index(root, context)
    if len(fits["rows"]) != 3:
        raise ValueError("B2.26 screen requires complete fit")
    screen_context = {
        **context,
        "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
        "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
    }
    index = _index(root, "screen_index.json", screen_context, 24)
    for row, case in zip(index["rows"], cases, strict=False):
        if (row["case"]["case_id"] != case.case_id
                or [item["method"] for item in row["outcomes"]] != list(METHODS)):
            raise ValueError("B2.26 persisted screen case differs")
    if len(index["rows"]) == 24:
        return screen_summary(root, index)
    operational = _control_models(b212_root)
    terminal_context = json.loads((b221_root / "fit_index.json").read_text())["context"]
    terminal_index = read_terminal_fit_index(b221_root, terminal_context)
    terminal = {row["seed"]: read_terminal_model(b221_root, row, terminal_context)
                for row in terminal_index["rows"]}
    specialist_context = json.loads((b224_root / "fit_index.json").read_text())["context"]
    specialist_index = read_specialist_fit_index(b224_root, specialist_context)
    specialist = {row["seed"]: read_specialist_model(b224_root, row, specialist_context)
                  for row in specialist_index["rows"]}
    weighted = {row["seed"]: _read_model(root, row, context) for row in fits["rows"]}
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 24):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.26 screen budget exhausted")
        case = cases[position]
        reference = _uniform_result(case, references["rows"][position]["uniform"])
        outcomes = [reference]
        for prefix, panel in (("operational", operational), ("terminal", terminal),
                              ("weighted", weighted)):
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
        print(f"B2.26 screen {position + 1}/24", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b212-root", type=Path, default=Path("/tmp/topolab-b212"))
    parser.add_argument("--b221-root", type=Path, default=Path("/tmp/topolab-b221"))
    parser.add_argument("--b224-root", type=Path, default=Path("/tmp/topolab-b224"))
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--references", action="store_true")
    stage.add_argument("--fit", action="store_true")
    stage.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    groups, screen, blocked = cohorts()
    plan = plan_payload(groups, screen, blocked)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.26 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    data_root = _external_root(repository, args.b24_root)
    b212_root = _external_root(repository, args.b212_root)
    b221_root = _external_root(repository, args.b221_root)
    b224_root = _external_root(repository, args.b224_root)
    if len({root, data_root, b212_root, b221_root, b224_root}) != 5:
        raise ValueError("B2.26 source and output roots must differ")
    for source, filename, digest in (
        (b212_root, "fit_index.json", B212_FIT_INDEX_SHA256),
        (b221_root, "validation_target_index.json", B221_TARGET_SHA256),
        (b221_root, "fit_index.json", B221_FIT_SHA256),
        (b224_root, "fit_index.json", B224_FIT_SHA256),
        (b224_root, "screen_index.json", B224_SCREEN_SHA256),
    ):
        if sha256((source / filename).read_bytes()) != digest:
            raise ValueError(f"B2.26 source {filename} digest differs")
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime, "b221_validation_target_index_sha256": B221_TARGET_SHA256,
               "b221_fit_index_sha256": B221_FIT_SHA256,
               "b224_fit_index_sha256": B224_FIT_SHA256}
    if not any((args.references, args.fit, args.screen)):
        print(json.dumps({"plan_sha256": plan["plan_sha256"],
                          "source_revision": revision, "train_cases": len(groups["train"]),
                          "validation_cases": len(groups["validation"]),
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
        raise ValueError("B2.26 reference Gate required")
    target_context = json.loads((b221_root / "validation_target_index.json").read_text())["context"]
    targets = _index(b221_root, "validation_target_index.json", target_context, 12)
    if len(targets["rows"]) != 12:
        raise ValueError("B2.21 validation targets incomplete")
    if args.fit:
        fits = run_fits(root, data_root, b221_root, groups, targets, context)
        print(json.dumps({"fits": [(row["seed"], row["selected_epoch"])
                                   for row in fits["rows"]],
                          "elapsed_seconds": fits["elapsed_seconds"],
                          "fit_index_sha256": sha256((root / "fit_index.json").read_bytes())},
                         sort_keys=True))
        return 0
    summary = run_screen(root, b212_root, b221_root, b224_root,
                         screen, references, context)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
