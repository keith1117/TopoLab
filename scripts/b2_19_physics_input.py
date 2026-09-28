"""B2.19 frozen physical-input fitting and fresh development screen."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

import torch
from b2_5_prototype import atomic_write, canonical_bytes, sha256, source_snapshot
from b2_6_trajectory import _external_root, _small_case
from b2_7_global_load import B26_TARGET_INDEX_SHA256, _peak_rss, _prior, _samples
from b2_9_vector_load import _index
from b2_11_reference_budget import versioned_case
from b2_12_context_cnn import _read_model as read_context_model
from b2_12_context_cnn import _read_selection as read_context_selection
from b2_12_context_cnn import cohorts as source_cohorts
from b2_18_solver_anchor import cohorts as exposure_cohorts
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import _attempt, _charged_result
from topolab.b2_6_trajectory import SEEDS, fit_trajectory_seed
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_19_physics_input import (
    ENCODING_VERSION,
    INPUT_CHANNELS,
    MODEL_PARAMETER_COUNT,
    MODEL_VERSION,
    PhysicsContextCNN,
    encode_physics_case,
)
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_19.physics_input.v1"
EXPECTED_PLAN_SHA256 = "e75e3eb9796729d9ef9921b617ca28783f5c96762a6a5b8acc95389bb0e6d664"
B212_FIT_INDEX_SHA256 = "0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce"
VOLUMES = (0.3375, 0.4875, 0.5795)
LOAD_POSITION = (1, 2)
REFERENCE_CAP = 1_800.0
FIT_CAP = 7_200.0
SCREEN_CAP = 8_000.0
MAX_RSS = 2_147_483_648
METHODS = ("uniform", *(f"context_{seed}" for seed in SEEDS),
           *(f"physics_{seed}" for seed in SEEDS))


def cohorts() -> tuple[dict[str, tuple[ExperimentCase, ...]],
                       tuple[ExperimentCase, ...], tuple[ExperimentCase, ...]]:
    groups, prior_screen, source_exposed = source_cohorts()
    reserved_b218, exposed_b218, reserved_b217 = exposure_cohorts()
    blocked = tuple(sorted({case.case_id: case for case in (
        *source_exposed, *prior_screen, *reserved_b218, *exposed_b218, *reserved_b217,
    )}.values(), key=lambda case: case.case_id))
    blocked_volumes = {case.problem.optimization.volume_fraction for case in blocked}
    blocked_volumes.update(index / 100 for index in range(20, 61, 5))
    blocked_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & blocked_volumes:
        raise ValueError("B2.19 volume intersects development or final-design exposure")
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for direction in ("y", "z"):
            small = _small_case(volume, direction, *LOAD_POSITION)
            selected.extend((versioned_case(small), versioned_case(scaled_case(small))))
    fresh = tuple(sorted(selected, key=lambda case: case.case_id))
    if (len(fresh) != 12 or len({case.case_id for case in fresh}) != 12
            or any(case.problem.optimization.max_iterations != 360 for case in fresh)
            or {case.case_id for case in fresh} & {case.case_id for case in blocked}):
        raise ValueError("B2.19 fresh screen identity differs")
    return groups, fresh, blocked


def plan_payload(groups: dict[str, tuple[ExperimentCase, ...]],
                 fresh: tuple[ExperimentCase, ...],
                 blocked: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "encoding_version": ENCODING_VERSION,
        "model_version": MODEL_VERSION,
        "model_parameter_count": MODEL_PARAMETER_COUNT,
        "input_channels": INPUT_CHANNELS,
        "feature": "log1p_negative_uniform_simp_sensitivity_over_mean_normalized_by_max",
        "feature_solve_count_per_query": 1,
        "target_update": 30,
        "b26_target_index_sha256": B26_TARGET_INDEX_SHA256,
        "b212_fit_index_sha256": B212_FIT_INDEX_SHA256,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 360,
        "seeds": list(SEEDS),
        "train_case_ids": [case.case_id for case in groups["train"]],
        "validation_case_ids": [case.case_id for case in groups["validation"]],
        "blocked_case_ids": [case.case_id for case in blocked],
        "blocked_volumes": sorted({case.problem.optimization.volume_fraction for case in blocked}
                                  | {index / 100 for index in range(20, 61, 5)}
                                  | {index / 1000 for index in range(225, 576, 50)}),
        "screen_case_ids": [case.case_id for case in fresh],
        "screen_volumes": list(VOLUMES),
        "screen_load_position_small": list(LOAD_POSITION),
        "methods": list(METHODS),
        "reference_cap_seconds": REFERENCE_CAP,
        "fit_cap_seconds": FIT_CAP,
        "screen_cap_seconds": SCREEN_CAP,
        "max_rss_bytes": MAX_RSS,
        "gate_scale_mean_max": 0.90,
        "gate_direction_mean_max": 1.0,
        "gate_required_seeds": 2,
        "gate_high_volume_large_y_quality_successes_min": 2,
        "gate_accepted_quality_violations_max": 0,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _quality(candidate: dict[str, Any]) -> bool:
    return (candidate["succeeded"] and candidate["candidate"] is not None
            and math.isfinite(candidate["candidate"]["final_compliance"])
            and candidate["candidate"]["final_compliance"] > 0
            and candidate["candidate"]["physical_volume_error"] <= 0.005)


def reference_gate(index: dict[str, Any], fresh: tuple[ExperimentCase, ...]) -> bool:
    return (len(index["rows"]) == 12 and index["elapsed_seconds"] <= REFERENCE_CAP
            and index["peak_rss_bytes"] <= MAX_RSS
            and all(row["case_id"] == case.case_id and _quality(row["uniform"])
                    for row, case in zip(index["rows"], fresh, strict=True)))


def run_references(root: Path, context: dict[str, Any],
                   fresh: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    index: dict[str, Any] = _index(root, "reference_index.json", context, 12)
    for row, case in zip(index["rows"], fresh, strict=False):
        if row["case_id"] != case.case_id:
            raise ValueError("B2.19 persisted reference order differs")
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 12):
        if prior + perf_counter() - started > REFERENCE_CAP:
            raise ValueError("B2.19 reference budget exhausted")
        case = fresh[position]
        index["rows"].append({"case_id": case.case_id,
                              "uniform": _attempt(case, method="uniform",
                                                  reference_compliance=None)})
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "reference_index.json", canonical_bytes(index))
        print(f"B2.19 reference {position + 1}/12", file=sys.stderr, flush=True)
    return index


def _read_model(root: Path, row: dict[str, Any],
                context: dict[str, Any]) -> PhysicsContextCNN:
    contents = (root / "checkpoints" / str(row["seed"])
                / f"{row['checkpoint_sha256']}.safetensors").read_bytes()
    if sha256(contents) != row["checkpoint_sha256"] or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.19 checkpoint checksum or size differs")
    header_length = int.from_bytes(contents[:8], "little")
    metadata = json.loads(json.loads(contents[8:8 + header_length])["__metadata__"]["topolab"])
    if metadata != {"version": "topolab.b2_19.checkpoint.v1", "context": context,
                    "seed": row["seed"], "selected_epoch": row["selected_epoch"]}:
        raise ValueError("B2.19 checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = PhysicsContextCNN()
    expected = model.state_dict()
    if set(state) != set(expected) or any(
        tensor.dtype != torch.float32 or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all() for name, tensor in state.items()
    ):
        raise ValueError("B2.19 checkpoint tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_selection(root: Path, row: dict[str, Any], context: dict[str, Any]) -> None:
    contents = (root / "selections" / str(row["seed"])
                / f"{row['selection_sha256']}.json").read_bytes()
    if sha256(contents) != row["selection_sha256"] or len(contents) != row["selection_bytes"]:
        raise ValueError("B2.19 selection checksum or size differs")
    selection = json.loads(contents)
    history = selection["history"]
    if (canonical_bytes(selection) != contents
            or selection["version"] != "topolab.b2_19.selection.v1"
            or selection["context"] != context or selection["seed"] != row["seed"]
            or selection["checkpoint_sha256"] != row["checkpoint_sha256"]
            or selection["selected_epoch"] != row["selected_epoch"]
            or selection["selected_validation_loss"] != row["selected_validation_loss"]
            or not history or len(history) > 200
            or [item["epoch"] for item in history] != list(range(1, len(history) + 1))):
        raise ValueError("B2.19 selection provenance differs")
    minimum = min(item["validation_loss"] for item in history)
    first = next(item["epoch"] for item in history if item["validation_loss"] == minimum)
    if (first != row["selected_epoch"] or minimum != row["selected_validation_loss"]
            or (len(history) < 200 and len(history) - first != 25)):
        raise ValueError("B2.19 selection is not earliest strict minimum")
    _read_model(root, row, context)


def _context_models(root: Path) -> dict[int, torch.nn.Module]:
    contents = (root / "fit_index.json").read_bytes()
    if sha256(contents) != B212_FIT_INDEX_SHA256:
        raise ValueError("B2.12 fixed fit index differs")
    index = json.loads(contents)
    if [row["seed"] for row in index["rows"]] != list(SEEDS):
        raise ValueError("B2.12 fixed model order differs")
    for row in index["rows"]:
        read_context_selection(root, row, index["context"])
    return {row["seed"]: read_context_model(root, row, index["context"])
            for row in index["rows"]}


def fit_models(root: Path, b26_root: Path, b212_root: Path,
               groups: dict[str, tuple[ExperimentCase, ...]],
               context: dict[str, Any]) -> dict[str, Any]:
    _context_models(b212_root)
    targets, _ = _prior(b26_root, groups)
    index: dict[str, Any] = _index(root, "fit_index.json", context, 3)
    for row, seed in zip(index["rows"], SEEDS, strict=False):
        if row["seed"] != seed:
            raise ValueError("B2.19 fit order differs")
        _read_selection(root, row, context)
    started, prior = perf_counter(), index["elapsed_seconds"]
    if len(index["rows"]) < 3:
        train = _samples(b26_root, groups, targets, "train",
                         encoder=encode_physics_case, input_channels=INPUT_CHANNELS)
        validation = _samples(b26_root, groups, targets, "validation",
                              encoder=encode_physics_case, input_channels=INPUT_CHANNELS)
        for position in range(len(index["rows"]), 3):
            if prior + perf_counter() - started > FIT_CAP:
                raise ValueError("B2.19 fit budget exhausted")
            seed = SEEDS[position]
            fit = fit_trajectory_seed(
                train, validation, seed=seed, model_factory=PhysicsContextCNN,
                expected_parameter_count=MODEL_PARAMETER_COUNT,
                input_channels=INPUT_CHANNELS,
            )
            metadata = {"version": "topolab.b2_19.checkpoint.v1", "context": context,
                        "seed": seed, "selected_epoch": fit.selected_epoch}
            checkpoint = save_tensors(dict(sorted(fit.state.items())),
                                      metadata={"topolab": canonical_bytes(metadata).decode()})
            digest = sha256(checkpoint)
            atomic_write(root / "checkpoints" / str(seed) / f"{digest}.safetensors",
                         checkpoint)
            selection = {"version": "topolab.b2_19.selection.v1", "context": context,
                         "seed": seed, "history": fit.history,
                         "selected_epoch": fit.selected_epoch,
                         "selected_validation_loss": fit.selected_validation_loss,
                         "fit_seconds": fit.seconds, "checkpoint_sha256": digest}
            selection_bytes = canonical_bytes(selection)
            selection_sha = sha256(selection_bytes)
            atomic_write(root / "selections" / str(seed) / f"{selection_sha}.json",
                         selection_bytes)
            row = {"seed": seed, "epochs": len(fit.history),
                   "selected_epoch": fit.selected_epoch,
                   "selected_validation_loss": fit.selected_validation_loss,
                   "fit_seconds": fit.seconds, "checkpoint_sha256": digest,
                   "checkpoint_bytes": len(checkpoint),
                   "selection_sha256": selection_sha,
                   "selection_bytes": len(selection_bytes)}
            _read_selection(root, row, context)
            index["rows"].append(row)
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "fit_index.json", canonical_bytes(index))
            print(f"B2.19 fit {position + 1}/3", file=sys.stderr, flush=True)
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "fit_index.json", canonical_bytes(index))
    if (len(index["rows"]) != 3 or index["elapsed_seconds"] > FIT_CAP
            or index["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.19 complete fit resource Gate failed")
    return index


def _uniform_result(case: ExperimentCase, attempt: dict[str, Any]) -> dict[str, Any]:
    phases = attempt["timing"]
    return {"case_id": case.case_id, "method": "uniform", "seed": None,
            "succeeded": True, "failure_code": None, "fallback_used": False,
            "candidate": attempt["candidate"], "operational": attempt["candidate"],
            "matched_case_id": None,
            "uniform_reference_compliance": attempt["candidate"]["final_compliance"],
            "timing": {**phases, "end_to_end_seconds": sum(phases.values())},
            "paired_time_ratio": 1.0}


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    means: dict[str, float] = {}
    directions: dict[str, float] = {}
    failures: dict[str, int] = {}
    for method in METHODS:
        items = [(row["case"], item) for row in index["rows"]
                 for item in row["outcomes"] if item["method"] == method]
        failures[method] = sum(not item["succeeded"] for _, item in items)
        for scale in ("small", "large"):
            selected = [(case, item) for case, item in items if case["scale"] == scale]
            if selected:
                means[f"{method}_{scale}"] = (
                    sum(item["paired_time_ratio"] for _, item in selected) / len(selected)
                )
            for direction in ("y", "z"):
                cell = [item["paired_time_ratio"] for case, item in selected
                        if case["direction"] == direction]
                if cell:
                    directions[f"{method}_{scale}_{direction}"] = sum(cell) / len(cell)
    high_y = [item for row in index["rows"] if row["case"]["scale"] == "large"
              and row["case"]["direction"] == "y"
              and row["case"]["volume"] == max(VOLUMES)
              for item in row["outcomes"] if item["method"].startswith("physics_")]
    high_y_successes = sum(item["succeeded"] for item in high_y)
    accepted_quality_violations = sum(
        item["succeeded"] and (
            item["operational"]["final_compliance"] > 1.001 * item["uniform_reference_compliance"]
            or item["operational"]["physical_volume_error"] > 0.005)
        for row in index["rows"] for item in row["outcomes"]
    )
    passing = []
    if len(index["rows"]) == 12:
        for seed in SEEDS:
            method = f"physics_{seed}"
            if (all(means[f"{method}_{scale}"] <= 0.90
                    and all(directions[f"{method}_{scale}_{direction}"] <= 1.0
                            for direction in ("y", "z"))
                    for scale in ("small", "large"))
                    and failures[method] <= failures[f"context_{seed}"]):
                passing.append(seed)
    passed = (len(index["rows"]) == 12
              and all(len(row["outcomes"]) == len(METHODS) for row in index["rows"])
              and len(passing) >= 2 and high_y_successes >= 2
              and accepted_quality_violations == 0
              and index["elapsed_seconds"] <= SCREEN_CAP
              and index["peak_rss_bytes"] <= MAX_RSS)
    return {"screen_index_sha256": sha256((root / "screen_index.json").read_bytes()),
            "cases": len(index["rows"]),
            "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
            "means": means, "direction_means": directions,
            "failure_counts": failures, "high_volume_large_y_successes": high_y_successes,
            "accepted_quality_violations": accepted_quality_violations,
            "passing_seeds": passing, "gate_passed": passed,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"]}


def run_screen(root: Path, b212_root: Path, fresh: tuple[ExperimentCase, ...],
               fit_context: dict[str, Any],
               references: dict[str, Any]) -> dict[str, Any]:
    fits = _index(root, "fit_index.json", fit_context, 3)
    if (len(fits["rows"]) != 3 or fits["elapsed_seconds"] > FIT_CAP
            or fits["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.19 screen requires complete fitting")
    for row in fits["rows"]:
        _read_selection(root, row, fit_context)
    context = {**fit_context, "fit_index_sha256": sha256((root / "fit_index.json").read_bytes())}
    index: dict[str, Any] = _index(root, "screen_index.json", context, 12)
    for row, case in zip(index["rows"], fresh, strict=False):
        if (row["case"]["case_id"] != case.case_id
                or [item["method"] for item in row["outcomes"]] != list(METHODS)):
            raise ValueError("B2.19 persisted screen identity differs")
    if len(index["rows"]) == 12:
        return screen_summary(root, index)
    old_models = _context_models(b212_root)
    new_models = {row["seed"]: _read_model(root, row, fit_context) for row in fits["rows"]}
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 12):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.19 screen budget exhausted")
        case = fresh[position]
        reference = _uniform_result(case, references["rows"][position]["uniform"])
        outcomes = [reference]
        for seed in SEEDS:
            row = _charged_result(case, "candidate", seed, reference,
                                  model=old_models[seed], encoder=encode_vector_load_case)
            row["method"] = f"context_{seed}"
            outcomes.append(row)
        for seed in SEEDS:
            row = _charged_result(case, "candidate", seed, reference,
                                  model=new_models[seed], encoder=encode_physics_case)
            row["method"] = f"physics_{seed}"
            outcomes.append(row)
        nx = case.problem.mesh.element_counts[0]
        index["rows"].append({"case": {"case_id": case.case_id,
                                         "scale": "small" if nx == 12 else "large",
                                         "direction": case.problem.loads[0].direction,
                                         "volume": case.problem.optimization.volume_fraction},
                              "outcomes": outcomes})
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "screen_index.json", canonical_bytes(index))
        print(f"B2.19 screen {position + 1}/12", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b26-root", type=Path, default=Path("/tmp/topolab-b26"))
    parser.add_argument("--b212-root", type=Path, default=Path("/tmp/topolab-b212"))
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--references", action="store_true")
    stage.add_argument("--fit", action="store_true")
    stage.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    groups, fresh, blocked = cohorts()
    plan = plan_payload(groups, fresh, blocked)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.19 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b26_root = _external_root(repository, args.b26_root)
    b212_root = _external_root(repository, args.b212_root)
    if len({root, b26_root, b212_root}) != 3:
        raise ValueError("B2.19 output and source roots must differ")
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime}
    if not (args.references or args.fit or args.screen):
        print(json.dumps({**plan, **context}, sort_keys=True))
        return 0
    if args.references:
        refs = run_references(root, context, fresh)
        passed = reference_gate(refs, fresh)
        print(json.dumps({"cases": len(refs["rows"]), "passed": passed,
                          "reference_index_sha256": sha256(
                              (root / "reference_index.json").read_bytes()),
                          "elapsed_seconds": refs["elapsed_seconds"]}, sort_keys=True))
        return 0 if passed else 1
    refs = _index(root, "reference_index.json", context, 12)
    if not reference_gate(refs, fresh):
        raise ValueError("B2.19 complete reference Gate required")
    fit_context = {**context,
                   "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
                   "b26_target_index_sha256": B26_TARGET_INDEX_SHA256,
                   "b212_fit_index_sha256": B212_FIT_INDEX_SHA256}
    if args.fit:
        fits = fit_models(root, b26_root, b212_root, groups, fit_context)
        print(json.dumps({"fits": fits["rows"],
                          "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
                          "elapsed_seconds": fits["elapsed_seconds"]}, sort_keys=True))
        return 0
    _prior(b26_root, groups)
    summary = run_screen(root, b212_root, fresh, fit_context, refs)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
