"""B2.22 high-volume y specialist and fixed-route development screen."""

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
from b2_21_terminal_target import cohorts as b221_cohorts
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import _charged_result
from topolab.b2_6_trajectory import SEEDS, fit_trajectory_seed
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_12_context_cnn import CONTEXT_MODEL_PARAMETER_COUNT, ContextCNN
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_22.y_specialist.v1"
EXPECTED_PLAN_SHA256 = "5c5a2c87ac6dae22ac48a058de6bbf04a4f9632bc2df17a8debc9a06de0a1c2a"
B221_SCREEN_SHA256 = "a44145fb61c7a3eb372fca02aaaef691b35f4b22630c9d50623eeb377d844d6d"
B221_TARGET_SHA256 = "3e7add2c85650bcb5ac0329236678887baaf2fc3acd4882a1f8f8fc7070796ab"
VOLUMES = (0.3645, 0.5145, 0.5945)
POSITIONS = ((1, 2), (4, 1))
SPECIALIST_VOLUME = 0.55
HIGH_Y_WEIGHT = 8.0
REFERENCE_CAP = 3_600.0
FIT_CAP = 7_200.0
SCREEN_CAP = 16_000.0
MAX_RSS = 2_147_483_648
METHODS = ("uniform", *(f"context_{seed}" for seed in SEEDS),
           *(f"routed_{seed}" for seed in SEEDS))


def specialist_case(case: ExperimentCase) -> bool:
    """Use the specialist only for the prespecified large high-volume y stratum."""
    return (case.problem.mesh.element_counts == (24, 12, 6)
            and case.problem.loads[0].direction == "y"
            and case.problem.optimization.volume_fraction >= SPECIALIST_VOLUME)


def cohorts() -> tuple[dict[str, tuple[ExperimentCase, ...]],
                       tuple[ExperimentCase, ...], tuple[ExperimentCase, ...]]:
    groups, previous, prior_blocked = b221_cohorts()
    blocked = tuple(sorted({case.case_id: case for case in (*prior_blocked, *previous)
                            }.values(), key=lambda case: case.case_id))
    blocked_volumes = {case.problem.optimization.volume_fraction for case in blocked}
    blocked_volumes.update(index / 100 for index in range(20, 61, 5))
    blocked_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & blocked_volumes:
        raise ValueError("B2.22 screen volume intersects prior evidence")
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
    if (len(blocked) != 736 or len(screen) != 24
            or len({case.case_id for case in (*blocked, *screen)}) != 760
            or len(strata) != 4 or set(strata.values()) != {6}
            or sum(specialist_case(case) for case in screen) != 2
            or any(case.problem.optimization.max_iterations != 360 for case in screen)):
        raise ValueError("B2.22 population, strata, or route differs")
    return groups, screen, blocked


def plan_payload(groups: dict[str, tuple[ExperimentCase, ...]],
                 screen: tuple[ExperimentCase, ...],
                 blocked: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    high_train = [case.case_id for case in groups["train"]
                  if case.problem.loads[0].direction == "y"
                  and case.problem.optimization.volume_fraction >= SPECIALIST_VOLUME]
    high_validation = [case.case_id for case in groups["validation"]
                       if case.problem.loads[0].direction == "y"
                       and case.problem.optimization.volume_fraction >= 0.525]
    if len(high_train) != 52 or len(high_validation) != 2:
        raise ValueError("B2.22 specialist development population differs")
    identity = {
        "version": PLAN_VERSION,
        "intervention": "terminal_target_case_weight_8_high_volume_y_with_fixed_route",
        "b221_screen_index_sha256": B221_SCREEN_SHA256,
        "b221_validation_target_index_sha256": B221_TARGET_SHA256,
        "b212_fit_index_sha256": B212_FIT_INDEX_SHA256,
        "model_version": "topolab.b2_12.context_cnn.v1",
        "input_version": "topolab.b2_9.vector_load.v1",
        "target": "audited_uniform_terminal_design_float32",
        "train_case_ids": [case.case_id for case in groups["train"]],
        "high_weight_train_case_ids": high_train,
        "selection_validation_case_ids": high_validation,
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
        "gate_required_routed_seeds": 2,
        "gate_failures_no_more_than_control": True,
        "gate_high_volume_large_y_successes_min": 4,
        "gate_accepted_quality_violations_max": 0,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _checkpoint_path(root: Path, seed: int, digest: str) -> Path:
    return root / "checkpoints" / str(seed) / f"{digest}.safetensors"


def _read_model(root: Path, row: dict[str, Any], context: dict[str, Any]) -> ContextCNN:
    contents = _checkpoint_path(root, row["seed"], row["checkpoint_sha256"]).read_bytes()
    if sha256(contents) != row["checkpoint_sha256"] or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.22 checkpoint checksum or size differs")
    length = int.from_bytes(contents[:8], "little")
    metadata = json.loads(json.loads(contents[8:8 + length])["__metadata__"]["topolab"])
    if metadata != {"version": "topolab.b2_22.checkpoint.v1", "context": context,
                    "seed": row["seed"], "selected_epoch": row["selected_epoch"]}:
        raise ValueError("B2.22 checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = ContextCNN()
    expected = model.state_dict()
    if set(state) != set(expected) or any(
        tensor.dtype != torch.float32 or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all() for name, tensor in state.items()
    ):
        raise ValueError("B2.22 checkpoint tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_fit_index(root: Path, context: dict[str, Any]) -> dict[str, Any]:
    index = _index(root, "fit_index.json", context, 3)
    for row, seed in zip(index["rows"], SEEDS, strict=False):
        if row["seed"] != seed:
            raise ValueError("B2.22 fit seed order differs")
        _read_model(root, row, context)
        contents = (root / "histories" / str(seed) / f"{row['history_sha256']}.json").read_bytes()
        if sha256(contents) != row["history_sha256"] or len(contents) != row["history_bytes"]:
            raise ValueError("B2.22 fit history checksum or size differs")
        history = json.loads(contents)
        if (canonical_bytes(history) != contents or history["context"] != context
                or history["seed"] != seed or history["version"] != "topolab.b2_22.history.v1"
                or not history["entries"] or len(history["entries"]) > 200):
            raise ValueError("B2.22 fit history provenance differs")
        entries = history["entries"]
        minimum = min(item["validation_loss"] for item in entries)
        first = next(item["epoch"] for item in entries if item["validation_loss"] == minimum)
        if (first != row["selected_epoch"] or minimum != row["selected_validation_loss"]
                or [item["epoch"] for item in entries] != list(range(1, len(entries) + 1))
                or (len(entries) < 200 and len(entries) - first != 25)):
            raise ValueError("B2.22 fit selection differs")
    return index


def run_fits(root: Path, data_root: Path, b221_root: Path,
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
        high_ids = {case.case_id for case in groups["train"]
                    if case.problem.loads[0].direction == "y"
                    and case.problem.optimization.volume_fraction >= SPECIALIST_VOLUME}
        weights = {sample.case_id: HIGH_Y_WEIGHT if sample.case_id in high_ids else 1.0
                   for sample in train}
        selection = frozenset(case.case_id for case in groups["validation"]
                              if case.problem.loads[0].direction == "y"
                              and case.problem.optimization.volume_fraction >= 0.525)
        for position in range(len(index["rows"]), 3):
            if prior + perf_counter() - started > FIT_CAP:
                raise ValueError("B2.22 fit budget exhausted")
            seed = SEEDS[position]
            fit = fit_trajectory_seed(train, validation, seed=seed,
                                      model_factory=ContextCNN,
                                      expected_parameter_count=CONTEXT_MODEL_PARAMETER_COUNT,
                                      input_channels=13, case_weights=weights,
                                      selection_case_ids=selection)
            metadata = {"version": "topolab.b2_22.checkpoint.v1", "context": context,
                        "seed": seed, "selected_epoch": fit.selected_epoch}
            checkpoint = save_tensors(dict(sorted(fit.state.items())),
                                      metadata={"topolab": canonical_bytes(metadata).decode()})
            digest = sha256(checkpoint)
            atomic_write(_checkpoint_path(root, seed, digest), checkpoint)
            history = {"version": "topolab.b2_22.history.v1", "context": context,
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
                                  "history_bytes": len(history_bytes)})
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "fit_index.json", canonical_bytes(index))
            print(f"B2.22 fit {position + 1}/3", file=sys.stderr, flush=True)
    if (len(index["rows"]) != 3 or index["elapsed_seconds"] > FIT_CAP
            or index["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.22 fit Gate failed")
    return index


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    ratios: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    high_y_successes = 0
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
            if (method.startswith("routed_") and case["specialist_route"]
                    and item["succeeded"]):
                high_y_successes += 1
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
            method = f"routed_{seed}"
            if (all(scale_means[f"{method}/{scale}"] <= 0.90
                    and all(direction_means[f"{method}/{scale}/{direction}"] <= 1.0
                            for direction in ("y", "z"))
                    for scale in ("small", "large"))
                and failures[method] <= failures[f"context_{seed}"]):
                passing.append(seed)
    gate = (len(index["rows"]) == 24
            and all(len(row["outcomes"]) == len(METHODS) for row in index["rows"])
            and len(passing) >= 2 and high_y_successes >= 4
            and quality_violations == 0 and index["elapsed_seconds"] <= SCREEN_CAP
            and index["peak_rss_bytes"] <= MAX_RSS)
    return {"screen_index_sha256": sha256((root / "screen_index.json").read_bytes()),
            "cases": len(index["rows"]),
            "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
            "scale_means": scale_means, "direction_means": direction_means,
            "failure_counts": dict(sorted(failures.items())),
            "high_volume_large_y_successes": high_y_successes,
            "accepted_quality_violations": quality_violations,
            "passing_seeds": passing, "gate_passed": gate,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"]}


def run_screen(root: Path, b212_root: Path, cases: tuple[ExperimentCase, ...],
               references: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    fits = _read_fit_index(root, context)
    if len(fits["rows"]) != 3:
        raise ValueError("B2.22 screen requires complete fit")
    screen_context = {
        **context,
        "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
        "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
    }
    index = _index(root, "screen_index.json", screen_context, 24)
    for row, case in zip(index["rows"], cases, strict=False):
        if (row["case"]["case_id"] != case.case_id
                or [item["method"] for item in row["outcomes"]] != list(METHODS)):
            raise ValueError("B2.22 persisted screen case differs")
    if len(index["rows"]) == 24:
        return screen_summary(root, index)
    controls = _control_models(b212_root)
    specialists = {row["seed"]: _read_model(root, row, context) for row in fits["rows"]}
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 24):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.22 screen budget exhausted")
        case = cases[position]
        reference = _uniform_result(case, references["rows"][position]["uniform"])
        outcomes = [reference]
        for seed in SEEDS:
            item = _charged_result(case, "candidate", seed, reference,
                                   model=controls[seed], encoder=encode_vector_load_case)
            item["method"] = f"context_{seed}"
            outcomes.append(item)
        for seed in SEEDS:
            route_start = perf_counter()
            use_specialist = specialist_case(case)
            model = specialists[seed] if use_specialist else controls[seed]
            route_seconds = perf_counter() - route_start
            item = _charged_result(case, "candidate", seed, reference,
                                   model=model, encoder=encode_vector_load_case)
            item["method"] = f"routed_{seed}"
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
        print(f"B2.22 screen {position + 1}/24", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b212-root", type=Path, default=Path("/tmp/topolab-b212"))
    parser.add_argument("--b221-root", type=Path, default=Path("/tmp/topolab-b221"))
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--references", action="store_true")
    stage.add_argument("--fit", action="store_true")
    stage.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    groups, screen, blocked = cohorts()
    plan = plan_payload(groups, screen, blocked)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.22 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    data_root = _external_root(repository, args.b24_root)
    b212_root = _external_root(repository, args.b212_root)
    b221_root = _external_root(repository, args.b221_root)
    if len({root, data_root, b212_root, b221_root}) != 4:
        raise ValueError("B2.22 source and output roots must differ")
    if sha256((b221_root / "screen_index.json").read_bytes()) != B221_SCREEN_SHA256:
        raise ValueError("B2.21 exposure evidence differs")
    if sha256((b221_root / "validation_target_index.json").read_bytes()) != B221_TARGET_SHA256:
        raise ValueError("B2.21 validation targets differ")
    if sha256((b212_root / "fit_index.json").read_bytes()) != B212_FIT_INDEX_SHA256:
        raise ValueError("B2.12 controls differ")
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime, "b221_validation_target_index_sha256": B221_TARGET_SHA256}
    if not any((args.references, args.fit, args.screen)):
        print(json.dumps({"plan_sha256": plan["plan_sha256"],
                          "source_revision": revision,
                          "train_cases": len(groups["train"]),
                          "validation_cases": len(groups["validation"]),
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
        raise ValueError("B2.22 reference Gate required")
    target_context = json.loads(
        (b221_root / "validation_target_index.json").read_text()
    )["context"]
    target_index = _index(b221_root, "validation_target_index.json", target_context, 12)
    if len(target_index["rows"]) != 12:
        raise ValueError("B2.21 validation targets incomplete")
    if args.fit:
        fits = run_fits(root, data_root, b221_root, groups, target_index, context)
        print(json.dumps({"fits": [(row["seed"], row["selected_epoch"])
                                   for row in fits["rows"]],
                          "elapsed_seconds": fits["elapsed_seconds"],
                          "fit_index_sha256": sha256((root / "fit_index.json").read_bytes())},
                         sort_keys=True))
        return 0
    summary = run_screen(root, b212_root, screen, references, context)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
