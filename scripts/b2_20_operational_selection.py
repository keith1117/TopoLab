"""B2.20 fixed-epoch operational selection and disjoint development screen."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
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
from b2_19_physics_input import _quality, _uniform_result
from b2_19_physics_input import cohorts as prior_cohorts
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import _attempt, _charged_result
from topolab.b2_6_trajectory import SEEDS, fit_trajectory_seed
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_12_context_cnn import CONTEXT_MODEL_PARAMETER_COUNT, ContextCNN
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_20.operational_selection.v1"
EXPECTED_PLAN_SHA256 = "2b72bcdcfd92c32908af73ee329550d8f364dcbb8a740c197858b72deb30f192"
B212_FIT_INDEX_SHA256 = "0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce"
B219_SCREEN_INDEX_SHA256 = "2a5accb40612b0e0a4dd349ae82cf76ed648481320e03aa8c66bbd9dc8ab331b"
CAPTURE_EPOCHS = (80, 120, 160)
MSE_BEST_EPOCHS = {17: 160, 29: 141, 43: 160}
SELECTION_VOLUMES = (0.3475, 0.4975, 0.5835)
SCREEN_VOLUMES = (0.3525, 0.5025, 0.5865)
SELECTION_POSITION = (2, 2)
SCREEN_POSITIONS = ((1, 1), (5, 2))
SELECTION_REFERENCE_CAP = 1_800.0
FIT_CAP = 7_200.0
SELECTION_CAP = 10_000.0
SCREEN_REFERENCE_CAP = 3_600.0
SCREEN_CAP = 16_000.0
MAX_RSS = 2_147_483_648
METHODS = ("uniform", *(f"context_{seed}" for seed in SEEDS),
           *(f"selected_{seed}" for seed in SEEDS))


def cohorts() -> tuple[dict[str, tuple[ExperimentCase, ...]],
                       tuple[ExperimentCase, ...], tuple[ExperimentCase, ...],
                       tuple[ExperimentCase, ...]]:
    groups, b219_screen, prior_blocked = prior_cohorts()
    blocked = tuple(sorted({case.case_id: case for case in (
        *prior_blocked, *b219_screen,
    )}.values(), key=lambda case: case.case_id))
    blocked_volumes = {case.problem.optimization.volume_fraction for case in blocked}
    blocked_volumes.update(index / 100 for index in range(20, 61, 5))
    blocked_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set((*SELECTION_VOLUMES, *SCREEN_VOLUMES)) & blocked_volumes:
        raise ValueError("B2.20 volume intersects exposed or reserved evidence")

    def cases(volumes: tuple[float, ...], positions: tuple[tuple[int, int], ...]
              ) -> tuple[ExperimentCase, ...]:
        selected: list[ExperimentCase] = []
        for volume in volumes:
            for y, z in positions:
                for direction in ("y", "z"):
                    small = _small_case(volume, direction, y, z)
                    selected.extend((versioned_case(small),
                                     versioned_case(scaled_case(small))))
        return tuple(sorted(selected, key=lambda case: case.case_id))

    selection = cases(SELECTION_VOLUMES, (SELECTION_POSITION,))
    screen = cases(SCREEN_VOLUMES, SCREEN_POSITIONS)
    ids = {case.case_id for case in (*blocked, *selection, *screen)}
    selection_strata = Counter((case.problem.mesh.element_counts,
                                case.problem.loads[0].direction) for case in selection)
    screen_strata = Counter((case.problem.mesh.element_counts,
                             case.problem.loads[0].direction) for case in screen)
    if (len(blocked) != 676 or len(selection) != 12 or len(screen) != 24
            or len(ids) != 712 or set(SELECTION_VOLUMES) & set(SCREEN_VOLUMES)
            or set(selection_strata.values()) != {3}
            or set(screen_strata.values()) != {6}
            or len(selection_strata) != 4 or len(screen_strata) != 4
            or any(case.problem.optimization.max_iterations != 360
                   for case in (*selection, *screen))):
        raise ValueError("B2.20 population, identity, or iteration budget differs")
    return groups, selection, screen, blocked


def plan_payload(groups: dict[str, tuple[ExperimentCase, ...]],
                 selection: tuple[ExperimentCase, ...],
                 screen: tuple[ExperimentCase, ...],
                 blocked: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "intervention": "fixed_epoch_operational_selection_from_unchanged_b212_training",
        "model_version": "topolab.b2_12.context_cnn.v1",
        "input_version": "topolab.b2_9.vector_load.v1",
        "target_update": 30,
        "b26_target_index_sha256": B26_TARGET_INDEX_SHA256,
        "b212_fit_index_sha256": B212_FIT_INDEX_SHA256,
        "b219_screen_index_sha256": B219_SCREEN_INDEX_SHA256,
        "capture_epochs": list(CAPTURE_EPOCHS),
        "unchanged_mse_best_epochs": MSE_BEST_EPOCHS,
        "selection_outcomes": 132,
        "screen_outcomes": 168,
        "also_capture_mse_best": True,
        "ranking": ["fewest_quality_failures", "lowest_worst_scale_direction_mean",
                    "lowest_overall_mean", "earliest_epoch"],
        "seeds": list(SEEDS),
        "train_case_ids": [case.case_id for case in groups["train"]],
        "mse_validation_case_ids": [case.case_id for case in groups["validation"]],
        "blocked_case_ids": [case.case_id for case in blocked],
        "blocked_volumes": sorted({case.problem.optimization.volume_fraction for case in blocked}
                                  | {index / 100 for index in range(20, 61, 5)}
                                  | {index / 1000 for index in range(225, 576, 50)}),
        "selection_case_ids": [case.case_id for case in selection],
        "screen_case_ids": [case.case_id for case in screen],
        "selection_volumes": list(SELECTION_VOLUMES),
        "screen_volumes": list(SCREEN_VOLUMES),
        "selection_position_small": list(SELECTION_POSITION),
        "screen_positions_small": [list(position) for position in SCREEN_POSITIONS],
        "methods": list(METHODS),
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 360,
        "caps_seconds": {"selection_references": SELECTION_REFERENCE_CAP,
                         "fit": FIT_CAP, "selection": SELECTION_CAP,
                         "screen_references": SCREEN_REFERENCE_CAP,
                         "screen": SCREEN_CAP},
        "max_rss_bytes": MAX_RSS,
        "gate_scale_mean_max": 0.90,
        "gate_direction_mean_max": 1.0,
        "gate_required_selected_seeds": 2,
        "gate_selected_failures_no_more_than_fixed_control": True,
        "gate_high_volume_large_y_successes_min": 4,
        "gate_accepted_quality_violations_max": 0,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def reference_gate(index: dict[str, Any], cases: tuple[ExperimentCase, ...],
                   cap: float) -> bool:
    return (len(index["rows"]) == len(cases) and index["elapsed_seconds"] <= cap
            and index["peak_rss_bytes"] <= MAX_RSS
            and all(row["case_id"] == case.case_id and _quality(row["uniform"])
                    for row, case in zip(index["rows"], cases, strict=True)))


def run_references(root: Path, name: str, context: dict[str, Any],
                   cases: tuple[ExperimentCase, ...], cap: float) -> dict[str, Any]:
    index: dict[str, Any] = _index(root, name, context, len(cases))
    for row, case in zip(index["rows"], cases, strict=False):
        if row["case_id"] != case.case_id:
            raise ValueError("B2.20 persisted reference order differs")
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), len(cases)):
        if prior + perf_counter() - started > cap:
            raise ValueError("B2.20 reference budget exhausted")
        case = cases[position]
        index["rows"].append({"case_id": case.case_id,
                              "uniform": _attempt(case, method="uniform",
                                                  reference_compliance=None)})
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / name, canonical_bytes(index))
        print(f"B2.20 {name} {position + 1}/{len(cases)}", file=sys.stderr, flush=True)
    return index


def _control_models(root: Path) -> dict[int, ContextCNN]:
    contents = (root / "fit_index.json").read_bytes()
    if sha256(contents) != B212_FIT_INDEX_SHA256:
        raise ValueError("B2.12 fixed fit index differs")
    index = json.loads(contents)
    if [row["seed"] for row in index["rows"]] != list(SEEDS):
        raise ValueError("B2.12 fixed seed order differs")
    for row in index["rows"]:
        read_context_selection(root, row, index["context"])
    return {row["seed"]: read_context_model(root, row, index["context"])
            for row in index["rows"]}


def _candidate_path(root: Path, seed: int, epoch: int, digest: str) -> Path:
    return root / "candidates" / str(seed) / f"{epoch}-{digest}.safetensors"


def _read_candidate(root: Path, seed: int, candidate: dict[str, Any],
                    context: dict[str, Any]) -> ContextCNN:
    epoch, digest = candidate["epoch"], candidate["checkpoint_sha256"]
    contents = _candidate_path(root, seed, epoch, digest).read_bytes()
    if sha256(contents) != digest or len(contents) != candidate["checkpoint_bytes"]:
        raise ValueError("B2.20 candidate checkpoint checksum or size differs")
    length = int.from_bytes(contents[:8], "little")
    metadata = json.loads(json.loads(contents[8:8 + length])["__metadata__"]["topolab"])
    if metadata != {"version": "topolab.b2_20.candidate.v1", "context": context,
                    "seed": seed, "epoch": epoch}:
        raise ValueError("B2.20 candidate checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = ContextCNN()
    expected = model.state_dict()
    if set(state) != set(expected) or any(
        tensor.dtype != torch.float32 or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all() for name, tensor in state.items()
    ):
        raise ValueError("B2.20 candidate tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_fit_index(root: Path, context: dict[str, Any]) -> dict[str, Any]:
    index: dict[str, Any] = _index(root, "fit_index.json", context, 3)
    for row, seed in zip(index["rows"], SEEDS, strict=False):
        if row["seed"] != seed:
            raise ValueError("B2.20 fit seed order differs")
        contents = (root / "histories" / str(seed)
                    / f"{row['history_sha256']}.json").read_bytes()
        if sha256(contents) != row["history_sha256"] or len(contents) != row["history_bytes"]:
            raise ValueError("B2.20 fit history checksum or size differs")
        history = json.loads(contents)
        entries = history["entries"]
        if (canonical_bytes(history) != contents
                or history["version"] != "topolab.b2_20.fit_history.v1"
                or history["context"] != context
                or history["seed"] != seed or not entries or len(entries) > 200
                or [item["epoch"] for item in entries] != list(range(1, len(entries) + 1))):
            raise ValueError("B2.20 fit history differs")
        minimum = min(item["validation_loss"] for item in entries)
        first = next(item["epoch"] for item in entries
                     if item["validation_loss"] == minimum)
        if (first != row["mse_best_epoch"] or minimum != row["mse_best_loss"]
                or first != MSE_BEST_EPOCHS[seed]
                or (len(entries) < 200 and len(entries) - first != 25)):
            raise ValueError("B2.20 MSE selection history differs")
        expected_epochs = sorted(set(epoch for epoch in CAPTURE_EPOCHS
                                     if epoch <= len(entries)) | {first})
        if [item["epoch"] for item in row["candidates"]] != expected_epochs:
            raise ValueError("B2.20 candidate epoch set differs")
        for candidate in row["candidates"]:
            _read_candidate(root, seed, candidate, context)
    return index


def fit_candidates(root: Path, b26_root: Path, b212_root: Path,
                   groups: dict[str, tuple[ExperimentCase, ...]],
                   context: dict[str, Any]) -> dict[str, Any]:
    controls = _control_models(b212_root)
    targets, _ = _prior(b26_root, groups)
    index = _read_fit_index(root, context)
    started, prior = perf_counter(), index["elapsed_seconds"]
    if len(index["rows"]) < 3:
        train = _samples(b26_root, groups, targets, "train",
                         encoder=encode_vector_load_case, input_channels=13)
        validation = _samples(b26_root, groups, targets, "validation",
                              encoder=encode_vector_load_case, input_channels=13)
        for position in range(len(index["rows"]), 3):
            if prior + perf_counter() - started > FIT_CAP:
                raise ValueError("B2.20 fitting budget exhausted")
            seed = SEEDS[position]
            fit = fit_trajectory_seed(
                train, validation, seed=seed, model_factory=ContextCNN,
                expected_parameter_count=CONTEXT_MODEL_PARAMETER_COUNT,
                input_channels=13, capture_epochs=CAPTURE_EPOCHS,
            )
            if fit.selected_epoch != MSE_BEST_EPOCHS[seed]:
                raise ValueError("B2.20 unchanged MSE epoch differs from B2.12")
            if any(not torch.equal(tensor, controls[seed].state_dict()[name])
                   for name, tensor in fit.state.items()):
                raise ValueError("B2.20 unchanged MSE fit differs from B2.12 control")
            states = dict(fit.captured_states or {})
            states[fit.selected_epoch] = fit.state
            candidates = []
            for epoch in sorted(states):
                metadata = {"version": "topolab.b2_20.candidate.v1",
                            "context": context, "seed": seed, "epoch": epoch}
                checkpoint = save_tensors(dict(sorted(states[epoch].items())),
                                          metadata={"topolab": canonical_bytes(metadata).decode()})
                digest = sha256(checkpoint)
                atomic_write(_candidate_path(root, seed, epoch, digest), checkpoint)
                candidates.append({"epoch": epoch, "checkpoint_sha256": digest,
                                   "checkpoint_bytes": len(checkpoint)})
            history = {"version": "topolab.b2_20.fit_history.v1", "context": context,
                       "seed": seed, "entries": fit.history}
            history_bytes = canonical_bytes(history)
            history_sha = sha256(history_bytes)
            atomic_write(root / "histories" / str(seed) / f"{history_sha}.json",
                         history_bytes)
            row = {"seed": seed, "epochs": len(fit.history),
                   "mse_best_epoch": fit.selected_epoch,
                   "mse_best_loss": fit.selected_validation_loss,
                   "fit_seconds": fit.seconds, "history_sha256": history_sha,
                   "history_bytes": len(history_bytes), "candidates": candidates}
            index["rows"].append(row)
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "fit_index.json", canonical_bytes(index))
            print(f"B2.20 fit {position + 1}/3", file=sys.stderr, flush=True)
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "fit_index.json", canonical_bytes(index))
    _read_fit_index(root, context)
    if (len(index["rows"]) != 3 or index["elapsed_seconds"] > FIT_CAP
            or index["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.20 complete fit Gate failed")
    return index


def _case_metadata(case: ExperimentCase) -> dict[str, Any]:
    nx = case.problem.mesh.element_counts[0]
    return {"case_id": case.case_id, "scale": "small" if nx == 12 else "large",
            "direction": case.problem.loads[0].direction,
            "volume": case.problem.optimization.volume_fraction}


def _candidate_method(seed: int, epoch: int) -> str:
    return f"candidate_{seed}_{epoch}"


def _selection_decision(root: Path, index: dict[str, Any],
                        fits: dict[str, Any]) -> dict[str, Any]:
    if (len(index["rows"]) != 12 or index["elapsed_seconds"] > SELECTION_CAP
            or index["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.20 operational selection requires complete evidence")
    selected = []
    for fit_row in fits["rows"]:
        seed = fit_row["seed"]
        rankings = []
        for candidate in fit_row["candidates"]:
            epoch = candidate["epoch"]
            method = _candidate_method(seed, epoch)
            outcomes = [(row["case"], item) for row in index["rows"]
                        for item in row["outcomes"] if item["method"] == method]
            if len(outcomes) != 12:
                raise ValueError("B2.20 candidate has incomplete selection outcomes")
            failures = sum(not item["succeeded"] for _, item in outcomes)
            directional = []
            for scale in ("small", "large"):
                for direction in ("y", "z"):
                    cell = [item["paired_time_ratio"] for case, item in outcomes
                            if case["scale"] == scale and case["direction"] == direction]
                    if len(cell) != 3:
                        raise ValueError("B2.20 selection stratum population differs")
                    directional.append(sum(cell) / 3)
            overall = sum(item["paired_time_ratio"] for _, item in outcomes) / 12
            score = (failures, max(directional), overall, epoch)
            rankings.append({"epoch": epoch, "checkpoint_sha256": candidate["checkpoint_sha256"],
                             "failures": failures, "direction_means": directional,
                             "overall_mean": overall, "score": list(score)})
        winner = min(rankings, key=lambda row: tuple(row["score"]))
        selected.append({"seed": seed, "epoch": winner["epoch"],
                         "checkpoint_sha256": winner["checkpoint_sha256"],
                         "ranking": rankings})
    decision = {"version": "topolab.b2_20.selection_decision.v1",
                "context": index["context"],
                "selection_index_sha256": sha256((root / "selection_index.json").read_bytes()),
                "selected": selected}
    return decision


def run_selection(root: Path, cases: tuple[ExperimentCase, ...],
                  references: dict[str, Any], fit_context: dict[str, Any]) -> dict[str, Any]:
    fits = _read_fit_index(root, fit_context)
    if (len(fits["rows"]) != 3 or fits["elapsed_seconds"] > FIT_CAP
            or fits["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.20 selection requires complete fits")
    context = {**fit_context, "fit_index_sha256": sha256((root / "fit_index.json").read_bytes())}
    index: dict[str, Any] = _index(root, "selection_index.json", context, 12)
    expected_methods = ["uniform", *(
        _candidate_method(row["seed"], candidate["epoch"])
        for row in fits["rows"] for candidate in row["candidates"]
    )]
    for row, case in zip(index["rows"], cases, strict=False):
        if (row["case"]["case_id"] != case.case_id
                or [item["method"] for item in row["outcomes"]] != expected_methods):
            raise ValueError("B2.20 persisted selection case or method differs")
    if len(index["rows"]) < 12:
        models = {(row["seed"], candidate["epoch"]): _read_candidate(
            root, row["seed"], candidate, fit_context)
            for row in fits["rows"] for candidate in row["candidates"]}
        started, prior = perf_counter(), index["elapsed_seconds"]
        for position in range(len(index["rows"]), 12):
            if prior + perf_counter() - started > SELECTION_CAP:
                raise ValueError("B2.20 selection budget exhausted")
            case = cases[position]
            reference = _uniform_result(case, references["rows"][position]["uniform"])
            outcomes = [reference]
            for row in fits["rows"]:
                seed = row["seed"]
                for candidate in row["candidates"]:
                    epoch = candidate["epoch"]
                    item = _charged_result(case, "candidate", seed, reference,
                                           model=models[(seed, epoch)],
                                           encoder=encode_vector_load_case)
                    item["method"] = _candidate_method(seed, epoch)
                    outcomes.append(item)
            index["rows"].append({"case": _case_metadata(case), "outcomes": outcomes})
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "selection_index.json", canonical_bytes(index))
            print(f"B2.20 selection {position + 1}/12", file=sys.stderr, flush=True)
    decision = _selection_decision(root, index, fits)
    path = root / "selection_decision.json"
    contents = canonical_bytes(decision)
    if path.exists() and path.read_bytes() != contents:
        raise ValueError("B2.20 persisted selection decision differs")
    atomic_write(path, contents)
    return decision


def _read_decision(root: Path, cases: tuple[ExperimentCase, ...],
                   references: dict[str, Any], fit_context: dict[str, Any]
                   ) -> dict[str, Any]:
    fits = _read_fit_index(root, fit_context)
    context = {**fit_context, "fit_index_sha256": sha256((root / "fit_index.json").read_bytes())}
    index = _index(root, "selection_index.json", context, 12)
    expected_methods = ["uniform", *(
        _candidate_method(row["seed"], candidate["epoch"])
        for row in fits["rows"] for candidate in row["candidates"]
    )]
    for row, case in zip(index["rows"], cases, strict=False):
        if (row["case"] != _case_metadata(case)
                or [item["method"] for item in row["outcomes"]] != expected_methods):
            raise ValueError("B2.20 selection evidence identity differs")
    if not reference_gate(references, cases, SELECTION_REFERENCE_CAP):
        raise ValueError("B2.20 selection references differ")
    expected = _selection_decision(root, index, fits)
    contents = (root / "selection_decision.json").read_bytes()
    if contents != canonical_bytes(expected):
        raise ValueError("B2.20 selection decision audit differs")
    return expected


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    ratio_cells: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    high_y_successes = 0
    quality_violations = 0
    for row in index["rows"]:
        case = row["case"]
        for item in row["outcomes"]:
            method = item["method"]
            ratio_cells[(method, case["scale"], case["direction"])].append(
                item["paired_time_ratio"])
            if not item["succeeded"]:
                failures[method] += 1
            if item["succeeded"] and (
                item["operational"]["final_compliance"]
                > 1.001 * item["uniform_reference_compliance"]
                or item["operational"]["physical_volume_error"] > 0.005
            ):
                quality_violations += 1
            if (method.startswith("selected_") and case["scale"] == "large"
                    and case["direction"] == "y" and case["volume"] == max(SCREEN_VOLUMES)
                    and item["succeeded"]):
                high_y_successes += 1
    direction_means = {f"{method}_{scale}_{direction}": sum(values) / len(values)
                       for (method, scale, direction), values in sorted(ratio_cells.items())}
    means = {}
    for method in METHODS:
        for scale in ("small", "large"):
            y = ratio_cells[(method, scale, "y")]
            z = ratio_cells[(method, scale, "z")]
            if y and z:
                means[f"{method}_{scale}"] = sum((*y, *z)) / (len(y) + len(z))
    passing = []
    if len(index["rows"]) == 24:
        for seed in SEEDS:
            method = f"selected_{seed}"
            if (all(means[f"{method}_{scale}"] <= 0.90
                    and all(direction_means[f"{method}_{scale}_{direction}"] <= 1.0
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
            "means": means, "direction_means": direction_means,
            "failure_counts": dict(sorted(failures.items())),
            "high_volume_large_y_successes": high_y_successes,
            "accepted_quality_violations": quality_violations,
            "passing_seeds": passing, "gate_passed": gate,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"]}


def run_screen(root: Path, b212_root: Path, cases: tuple[ExperimentCase, ...],
               references: dict[str, Any], fit_context: dict[str, Any],
               decision: dict[str, Any]) -> dict[str, Any]:
    fits = _read_fit_index(root, fit_context)
    context = {**fit_context,
               "selection_decision_sha256": sha256((root / "selection_decision.json").read_bytes()),
               "screen_reference_index_sha256": sha256(
                   (root / "screen_reference_index.json").read_bytes())}
    index: dict[str, Any] = _index(root, "screen_index.json", context, 24)
    for row, case in zip(index["rows"], cases, strict=False):
        if (row["case"]["case_id"] != case.case_id
                or [item["method"] for item in row["outcomes"]] != list(METHODS)):
            raise ValueError("B2.20 persisted screen case or method differs")
    if len(index["rows"]) == 24:
        return screen_summary(root, index)
    controls = _control_models(b212_root)
    selected = {}
    for item in decision["selected"]:
        fit_row = next(row for row in fits["rows"] if row["seed"] == item["seed"])
        candidate = next(row for row in fit_row["candidates"] if row["epoch"] == item["epoch"])
        if candidate["checkpoint_sha256"] != item["checkpoint_sha256"]:
            raise ValueError("B2.20 chosen checkpoint differs")
        selected[item["seed"]] = _read_candidate(root, item["seed"], candidate, fit_context)
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 24):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.20 screen budget exhausted")
        case = cases[position]
        reference = _uniform_result(case, references["rows"][position]["uniform"])
        outcomes = [reference]
        for prefix, models in (("context", controls), ("selected", selected)):
            for seed in SEEDS:
                item = _charged_result(case, "candidate", seed, reference,
                                       model=models[seed], encoder=encode_vector_load_case)
                item["method"] = f"{prefix}_{seed}"
                outcomes.append(item)
        index["rows"].append({"case": _case_metadata(case), "outcomes": outcomes})
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "screen_index.json", canonical_bytes(index))
        print(f"B2.20 screen {position + 1}/24", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b26-root", type=Path, default=Path("/tmp/topolab-b26"))
    parser.add_argument("--b212-root", type=Path, default=Path("/tmp/topolab-b212"))
    parser.add_argument("--b219-root", type=Path, default=Path("/tmp/topolab-b219"))
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--selection-references", action="store_true")
    stage.add_argument("--fit", action="store_true")
    stage.add_argument("--select", action="store_true")
    stage.add_argument("--screen-references", action="store_true")
    stage.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    groups, selection, screen, blocked = cohorts()
    plan = plan_payload(groups, selection, screen, blocked)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.20 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b26_root = _external_root(repository, args.b26_root)
    b212_root = _external_root(repository, args.b212_root)
    b219_root = _external_root(repository, args.b219_root)
    if len({root, b26_root, b212_root, b219_root}) != 4:
        raise ValueError("B2.20 source and output roots must differ")
    if sha256((b219_root / "screen_index.json").read_bytes()) != B219_SCREEN_INDEX_SHA256:
        raise ValueError("B2.19 exposure evidence differs")
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime}
    if not any((args.selection_references, args.fit, args.select,
                args.screen_references, args.screen)):
        print(json.dumps({"plan_sha256": plan["plan_sha256"], "source_revision": revision,
                          "train_cases": len(groups["train"]),
                          "mse_validation_cases": len(groups["validation"]),
                          "selection_cases": len(selection), "screen_cases": len(screen),
                          "blocked_cases": len(blocked), "capture_epochs": CAPTURE_EPOCHS},
                         sort_keys=True))
        return 0
    if args.selection_references:
        references = run_references(root, "selection_reference_index.json", context,
                                    selection, SELECTION_REFERENCE_CAP)
        passed = reference_gate(references, selection, SELECTION_REFERENCE_CAP)
        print(json.dumps({"cases": len(references["rows"]), "passed": passed,
                          "index_sha256": sha256(
                              (root / "selection_reference_index.json").read_bytes())},
                         sort_keys=True))
        return 0 if passed else 1
    selection_references = _index(root, "selection_reference_index.json", context, 12)
    if not reference_gate(selection_references, selection, SELECTION_REFERENCE_CAP):
        raise ValueError("B2.20 selection reference Gate required")
    fit_context = {**context,
                   "selection_reference_index_sha256": sha256(
                       (root / "selection_reference_index.json").read_bytes()),
                   "b26_target_index_sha256": B26_TARGET_INDEX_SHA256,
                   "b212_fit_index_sha256": B212_FIT_INDEX_SHA256}
    if args.fit:
        fits = fit_candidates(root, b26_root, b212_root, groups, fit_context)
        print(json.dumps({"fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
                          "fits": [(row["seed"], row["mse_best_epoch"],
                                    [item["epoch"] for item in row["candidates"]])
                                   for row in fits["rows"]],
                          "elapsed_seconds": fits["elapsed_seconds"]}, sort_keys=True))
        return 0
    if args.select:
        decision = run_selection(root, selection, selection_references, fit_context)
        print(json.dumps({"decision_sha256": sha256(
            (root / "selection_decision.json").read_bytes()),
            "selected": [(row["seed"], row["epoch"]) for row in decision["selected"]]},
            sort_keys=True))
        return 0
    decision = _read_decision(root, selection, selection_references, fit_context)
    screen_ref_context = {**fit_context,
                          "selection_decision_sha256": sha256(
                              (root / "selection_decision.json").read_bytes())}
    if args.screen_references:
        references = run_references(root, "screen_reference_index.json", screen_ref_context,
                                    screen, SCREEN_REFERENCE_CAP)
        passed = reference_gate(references, screen, SCREEN_REFERENCE_CAP)
        print(json.dumps({"cases": len(references["rows"]), "passed": passed,
                          "index_sha256": sha256(
                              (root / "screen_reference_index.json").read_bytes())},
                         sort_keys=True))
        return 0 if passed else 1
    screen_references = _index(root, "screen_reference_index.json", screen_ref_context, 24)
    if not reference_gate(screen_references, screen, SCREEN_REFERENCE_CAP):
        raise ValueError("B2.20 screen reference Gate required")
    summary = run_screen(root, b212_root, screen, screen_references, fit_context, decision)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
