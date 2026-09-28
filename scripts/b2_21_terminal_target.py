"""B2.21 terminal-design target fit and independent development screen."""

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
    _read_label,
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
from b2_20_operational_selection import cohorts as b220_cohorts
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import _charged_result, _raw_uniform
from topolab.b2_6_trajectory import SEEDS, TrajectorySample, fit_trajectory_seed
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_12_context_cnn import CONTEXT_MODEL_PARAMETER_COUNT, ContextCNN
from topolab.baselines import validate_refinement_quality
from topolab.experiment import ExperimentCase, project_design_density
from topolab.mesh import generate_structured_hex8
from topolab.problem import TopologyProblem, solve_problem
from topolab.simp import apply_density_filter, build_density_filter

PLAN_VERSION = "topolab.b2_21.terminal_target.v1"
EXPECTED_PLAN_SHA256 = "3f5fadd4945cb0d6fbae2739cbc477244d0b7a52e657d58eb7ce5d4ffc2edaf2"
B220_SCREEN_SHA256 = "a8b3fce38f6db4017db582e04a21c0559b270e6787fb4190cc1f15afe6b834ce"
VOLUMES = (0.3575, 0.5075, 0.5915)
POSITIONS = ((2, 2), (5, 1))
REFERENCE_CAP = 3_600.0
TARGET_CAP = 1_800.0
FIT_CAP = 7_200.0
SCREEN_CAP = 16_000.0
MAX_RSS = 2_147_483_648
METHODS = ("uniform", *(f"context_{seed}" for seed in SEEDS),
           *(f"terminal_{seed}" for seed in SEEDS))


def cohorts() -> tuple[dict[str, tuple[ExperimentCase, ...]],
                       tuple[ExperimentCase, ...], tuple[ExperimentCase, ...]]:
    groups, selection, prior_screen, prior_blocked = b220_cohorts()
    blocked = tuple(sorted({case.case_id: case for case in (
        *prior_blocked, *selection, *prior_screen,
    )}.values(), key=lambda case: case.case_id))
    excluded_volumes = {case.problem.optimization.volume_fraction for case in blocked}
    excluded_volumes.update(index / 100 for index in range(20, 61, 5))
    excluded_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & excluded_volumes:
        raise ValueError("B2.21 screen volume intersects earlier exposure")
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for position in POSITIONS:
            for direction in ("y", "z"):
                small = _small_case(volume, direction, *position)
                selected.extend((versioned_case(small),
                                 versioned_case(scaled_case(small))))
    screen = tuple(sorted(selected, key=lambda case: case.case_id))
    counts = Counter((case.problem.mesh.element_counts, case.problem.loads[0].direction)
                     for case in screen)
    if (len(blocked) != 712 or len(screen) != 24
            or len({case.case_id for case in (*blocked, *screen)}) != 736
            or len(counts) != 4 or set(counts.values()) != {6}
            or any(case.problem.optimization.max_iterations != 360 for case in screen)):
        raise ValueError("B2.21 screen population or identity differs")
    return groups, screen, blocked


def plan_payload(groups: dict[str, tuple[ExperimentCase, ...]],
                 screen: tuple[ExperimentCase, ...],
                 blocked: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "intervention": "uniform_terminal_design_instead_of_update_30_target",
        "b24_data_index_sha256": DATA_INDEX_SHA256,
        "b212_fit_index_sha256": B212_FIT_INDEX_SHA256,
        "b220_screen_index_sha256": B220_SCREEN_SHA256,
        "model_version": "topolab.b2_12.context_cnn.v1",
        "input_version": "topolab.b2_9.vector_load.v1",
        "target": "audited_uniform_terminal_design_float32",
        "training_solver_budget": 240,
        "screen_solver_budget": 360,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "train_case_ids": [case.case_id for case in groups["train"]],
        "validation_case_ids": [case.case_id for case in groups["validation"]],
        "blocked_case_ids": [case.case_id for case in blocked],
        "screen_case_ids": [case.case_id for case in screen],
        "screen_volumes": list(VOLUMES),
        "screen_positions_small": [list(position) for position in POSITIONS],
        "methods": list(METHODS),
        "seeds": list(SEEDS),
        "caps_seconds": {"references": REFERENCE_CAP, "validation_targets": TARGET_CAP,
                         "fit": FIT_CAP, "screen": SCREEN_CAP},
        "max_rss_bytes": MAX_RSS,
        "gate_scale_mean_max": 0.90,
        "gate_direction_mean_max": 1.0,
        "gate_required_terminal_seeds": 2,
        "gate_failures_no_more_than_control": True,
        "gate_high_volume_large_y_successes_min": 4,
        "gate_accepted_quality_violations_max": 0,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _target_path(root: Path, case_id: str, digest: str) -> Path:
    return root / "validation_targets" / case_id / f"{digest}.safetensors"


def _read_target(root: Path, row: dict[str, Any], case: ExperimentCase,
                 context: dict[str, Any]) -> torch.Tensor:
    contents = _target_path(root, case.case_id, row["target_sha256"]).read_bytes()
    if sha256(contents) != row["target_sha256"] or len(contents) != row["target_bytes"]:
        raise ValueError("B2.21 validation target checksum or size differs")
    length = int.from_bytes(contents[:8], "little")
    metadata = json.loads(json.loads(contents[8:8 + length])["__metadata__"]["topolab"])
    if metadata != {"version": "topolab.b2_21.validation_target.v1",
                    "context": context, "case_id": case.case_id,
                    "iterations": row["iterations"], "compliance": row["compliance"]}:
        raise ValueError("B2.21 validation target provenance differs")
    state = load_tensors(contents)
    nx, ny, nz = case.problem.mesh.element_counts
    if set(state) != {"design"} or state["design"].shape != (1, nz, ny, nx):
        raise ValueError("B2.21 validation target shape differs")
    design = state["design"]
    if (design.dtype != torch.float32 or not torch.isfinite(design).all()
            or torch.any(design < case.problem.optimization.minimum_density)
            or torch.any(design > 1)):
        raise ValueError("B2.21 validation target bounds differ")
    mesh = generate_structured_hex8(nx, ny, nz, lengths=case.problem.mesh.lengths)
    density_filter = build_density_filter(mesh, case.problem.optimization.filter_radius)
    physical = apply_density_filter(density_filter,
                                    design.numpy().astype(np.float64).reshape(-1))
    if abs(float(np.mean(physical)) - case.problem.optimization.volume_fraction) > 0.005:
        raise ValueError("B2.21 validation target volume differs")
    return design


def validation_target_gate(index: dict[str, Any],
                           cases: tuple[ExperimentCase, ...], root: Path,
                           context: dict[str, Any]) -> bool:
    return (len(index["rows"]) == len(cases) == 12
            and index["elapsed_seconds"] <= TARGET_CAP
            and index["peak_rss_bytes"] <= MAX_RSS
            and all(row["case_id"] == case.case_id
                    and row["iterations"] <= 240
                    and _read_target(root, row, case, context) is not None
                    for row, case in zip(index["rows"], cases, strict=True)))


def run_validation_targets(root: Path, context: dict[str, Any],
                           cases: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    index = _index(root, "validation_target_index.json", context, 12)
    for row, case in zip(index["rows"], cases, strict=False):
        if row["case_id"] != case.case_id:
            raise ValueError("B2.21 persisted validation case differs")
        _read_target(root, row, case, context)
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 12):
        if prior + perf_counter() - started > TARGET_CAP:
            raise ValueError("B2.21 validation-target budget exhausted")
        case = cases[position]
        raw = _raw_uniform(case)
        projected = project_design_density(case, raw)
        payload = case.problem.model_dump(mode="json")
        payload["initial_density"] = tuple(float(value) for value in projected.design_density)
        result = solve_problem(TopologyProblem.model_validate(payload),
                               termination_policy="physical_plateau")
        metrics = validate_refinement_quality(case, result, None)
        nx, ny, nz = case.problem.mesh.element_counts
        design = torch.from_numpy(np.asarray(result.design_density, dtype=np.float32)
                                  .reshape((1, nz, ny, nx)).copy())
        metadata = {"version": "topolab.b2_21.validation_target.v1",
                    "context": context, "case_id": case.case_id,
                    "iterations": metrics.iterations,
                    "compliance": metrics.final_compliance}
        contents = save_tensors({"design": design},
                                metadata={"topolab": canonical_bytes(metadata).decode()})
        digest = sha256(contents)
        atomic_write(_target_path(root, case.case_id, digest), contents)
        row = {"case_id": case.case_id, "iterations": metrics.iterations,
               "compliance": metrics.final_compliance,
               "target_sha256": digest, "target_bytes": len(contents)}
        _read_target(root, row, case, context)
        index["rows"].append(row)
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "validation_target_index.json", canonical_bytes(index))
        print(f"B2.21 validation target {position + 1}/12", file=sys.stderr, flush=True)
    return index


def _samples(root: Path, data_root: Path, data_index: dict[str, Any],
             groups: dict[str, tuple[ExperimentCase, ...]], split: str,
             target_index: dict[str, Any], target_context: dict[str, Any]
             ) -> tuple[TrajectorySample, ...]:
    if split not in ("train", "validation"):
        raise ValueError("B2.21 fitting may open only development splits")
    label_rows = {row["identity"]["new_case_id"]: row for row in data_index["rows"]
                  if row["identity"]["split"] == "train"}
    target_rows = {row["case_id"]: row for row in target_index["rows"]}
    selected = []
    for case in groups[split]:
        if split == "train":
            label = _read_label(data_root, label_rows[case.case_id], data_index)
            if label.case.case_id != case.case_id or label.split != "train":
                raise ValueError("B2.21 training label identity differs")
            nx, ny, nz = case.problem.mesh.element_counts
            target = torch.from_numpy(np.asarray(label.design_density, dtype=np.float32)
                                      .reshape((1, nz, ny, nx)).copy())
        else:
            target = _read_target(root, target_rows[case.case_id], case, target_context)
        sample = TrajectorySample(case_id=case.case_id, split=split,  # type: ignore[arg-type]
                                  inputs=torch.from_numpy(
                                      encode_vector_load_case(case).input_tensor.copy()),
                                  target=target, input_channels=13)
        sample.validate()
        selected.append(sample)
    return tuple(selected)


def _checkpoint_path(root: Path, seed: int, digest: str) -> Path:
    return root / "checkpoints" / str(seed) / f"{digest}.safetensors"


def _read_model(root: Path, row: dict[str, Any],
                context: dict[str, Any]) -> ContextCNN:
    contents = _checkpoint_path(root, row["seed"], row["checkpoint_sha256"]).read_bytes()
    if sha256(contents) != row["checkpoint_sha256"] or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.21 checkpoint checksum or size differs")
    length = int.from_bytes(contents[:8], "little")
    metadata = json.loads(json.loads(contents[8:8 + length])["__metadata__"]["topolab"])
    if metadata != {"version": "topolab.b2_21.checkpoint.v1", "context": context,
                    "seed": row["seed"], "selected_epoch": row["selected_epoch"]}:
        raise ValueError("B2.21 checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = ContextCNN()
    expected = model.state_dict()
    if set(state) != set(expected) or any(
        tensor.dtype != torch.float32 or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all() for name, tensor in state.items()
    ):
        raise ValueError("B2.21 checkpoint tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_fit_index(root: Path, context: dict[str, Any]) -> dict[str, Any]:
    index = _index(root, "fit_index.json", context, 3)
    for row, seed in zip(index["rows"], SEEDS, strict=False):
        if row["seed"] != seed:
            raise ValueError("B2.21 fit seed order differs")
        _read_model(root, row, context)
        contents = (root / "histories" / str(seed) / f"{row['history_sha256']}.json").read_bytes()
        if sha256(contents) != row["history_sha256"] or len(contents) != row["history_bytes"]:
            raise ValueError("B2.21 fit history checksum or size differs")
        history = json.loads(contents)
        if (canonical_bytes(history) != contents or history["context"] != context
                or history["seed"] != seed or history["version"] != "topolab.b2_21.history.v1"
                or not history["entries"] or len(history["entries"]) > 200):
            raise ValueError("B2.21 fit history provenance differs")
        entries = history["entries"]
        minimum = min(item["validation_loss"] for item in entries)
        first = next(item["epoch"] for item in entries if item["validation_loss"] == minimum)
        if (first != row["selected_epoch"] or minimum != row["selected_validation_loss"]
                or [item["epoch"] for item in entries] != list(range(1, len(entries) + 1))
                or (len(entries) < 200 and len(entries) - first != 25)):
            raise ValueError("B2.21 fit selection differs")
    return index


def run_fits(root: Path, data_root: Path, data_index: dict[str, Any],
             groups: dict[str, tuple[ExperimentCase, ...]],
             targets: dict[str, Any], target_context: dict[str, Any],
             context: dict[str, Any]) -> dict[str, Any]:
    index = _read_fit_index(root, context)
    started, prior = perf_counter(), index["elapsed_seconds"]
    if len(index["rows"]) < 3:
        train = _samples(root, data_root, data_index, groups, "train", targets, target_context)
        validation = _samples(root, data_root, data_index, groups, "validation",
                              targets, target_context)
        for position in range(len(index["rows"]), 3):
            if prior + perf_counter() - started > FIT_CAP:
                raise ValueError("B2.21 fit budget exhausted")
            seed = SEEDS[position]
            fit = fit_trajectory_seed(train, validation, seed=seed,
                                      model_factory=ContextCNN,
                                      expected_parameter_count=CONTEXT_MODEL_PARAMETER_COUNT,
                                      input_channels=13)
            metadata = {"version": "topolab.b2_21.checkpoint.v1", "context": context,
                        "seed": seed, "selected_epoch": fit.selected_epoch}
            checkpoint = save_tensors(dict(sorted(fit.state.items())),
                                      metadata={"topolab": canonical_bytes(metadata).decode()})
            digest = sha256(checkpoint)
            atomic_write(_checkpoint_path(root, seed, digest), checkpoint)
            history = {"version": "topolab.b2_21.history.v1", "context": context,
                       "seed": seed, "entries": fit.history}
            history_bytes = canonical_bytes(history)
            history_sha = sha256(history_bytes)
            atomic_write(root / "histories" / str(seed) / f"{history_sha}.json",
                         history_bytes)
            row = {"seed": seed, "epochs": len(fit.history),
                   "selected_epoch": fit.selected_epoch,
                   "selected_validation_loss": fit.selected_validation_loss,
                   "fit_seconds": fit.seconds, "checkpoint_sha256": digest,
                   "checkpoint_bytes": len(checkpoint), "history_sha256": history_sha,
                   "history_bytes": len(history_bytes)}
            index["rows"].append(row)
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "fit_index.json", canonical_bytes(index))
            print(f"B2.21 fit {position + 1}/3", file=sys.stderr, flush=True)
    if (len(index["rows"]) != 3 or index["elapsed_seconds"] > FIT_CAP
            or index["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.21 fit Gate failed")
    return index


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    ratios: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    quality_violations = 0
    high_y_successes = 0
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
            if (method.startswith("terminal_") and case["scale"] == "large"
                and case["direction"] == "y" and case["volume"] == max(VOLUMES)
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
            method = f"terminal_{seed}"
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
    if (len(fits["rows"]) != 3 or fits["elapsed_seconds"] > FIT_CAP
            or fits["peak_rss_bytes"] > MAX_RSS):
        raise ValueError("B2.21 screen requires complete fit")
    screen_context = {
        **context,
        "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
        "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
    }
    index = _index(root, "screen_index.json", screen_context, 24)
    for row, case in zip(index["rows"], cases, strict=False):
        if (row["case"]["case_id"] != case.case_id
            or [item["method"] for item in row["outcomes"]] != list(METHODS)):
            raise ValueError("B2.21 persisted screen case differs")
    if len(index["rows"]) == 24:
        return screen_summary(root, index)
    controls = _control_models(b212_root)
    models = {row["seed"]: _read_model(root, row, context) for row in fits["rows"]}
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 24):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.21 screen budget exhausted")
        case = cases[position]
        reference = _uniform_result(case, references["rows"][position]["uniform"])
        outcomes = [reference]
        for prefix, panel in (("context", controls), ("terminal", models)):
            for seed in SEEDS:
                item = _charged_result(case, "candidate", seed, reference,
                                       model=panel[seed], encoder=encode_vector_load_case)
                item["method"] = f"{prefix}_{seed}"
                outcomes.append(item)
        nx = case.problem.mesh.element_counts[0]
        index["rows"].append({"case": {"case_id": case.case_id,
                                       "scale": "small" if nx == 12 else "large",
                                       "direction": case.problem.loads[0].direction,
                                       "volume": case.problem.optimization.volume_fraction},
                              "outcomes": outcomes})
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "screen_index.json", canonical_bytes(index))
        print(f"B2.21 screen {position + 1}/24", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b212-root", type=Path, default=Path("/tmp/topolab-b212"))
    parser.add_argument("--b220-root", type=Path, default=Path("/tmp/topolab-b220"))
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--references", action="store_true")
    stage.add_argument("--validation-targets", action="store_true")
    stage.add_argument("--fit", action="store_true")
    stage.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    groups, screen, blocked = cohorts()
    plan = plan_payload(groups, screen, blocked)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.21 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    data_root = _external_root(repository, args.b24_root)
    b212_root = _external_root(repository, args.b212_root)
    b220_root = _external_root(repository, args.b220_root)
    if len({root, data_root, b212_root, b220_root}) != 4:
        raise ValueError("B2.21 source and output roots must differ")
    if sha256((b220_root / "screen_index.json").read_bytes()) != B220_SCREEN_SHA256:
        raise ValueError("B2.20 exposure evidence differs")
    data_index = read_data_index(data_root, select_cases())
    if sha256((b212_root / "fit_index.json").read_bytes()) != B212_FIT_INDEX_SHA256:
        raise ValueError("B2.12 control fit index differs")
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime}
    if not any((args.references, args.validation_targets, args.fit, args.screen)):
        print(json.dumps({"plan_sha256": plan["plan_sha256"],
                          "source_revision": revision, "train_cases": len(groups["train"]),
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
        raise ValueError("B2.21 screen reference Gate required")
    target_context = {**context, "reference_index_sha256": sha256(
        (root / "reference_index.json").read_bytes())}
    if args.validation_targets:
        targets = run_validation_targets(root, target_context, groups["validation"])
        passed = validation_target_gate(targets, groups["validation"], root,
                                        target_context)
        print(json.dumps({"cases": len(targets["rows"]), "passed": passed,
                          "index_sha256": sha256(
                              (root / "validation_target_index.json").read_bytes())},
                         sort_keys=True))
        return 0 if passed else 1
    targets = _index(root, "validation_target_index.json", target_context, 12)
    if not validation_target_gate(targets, groups["validation"], root, target_context):
        raise ValueError("B2.21 validation target Gate required")
    fit_context = {**target_context,
                   "validation_target_index_sha256": sha256(
                       (root / "validation_target_index.json").read_bytes()),
                   "b24_data_index_sha256": DATA_INDEX_SHA256}
    if args.fit:
        fits = run_fits(root, data_root, data_index, groups, targets, target_context,
                        fit_context)
        print(json.dumps({"fits": [(row["seed"], row["selected_epoch"])
                                   for row in fits["rows"]],
                          "elapsed_seconds": fits["elapsed_seconds"],
                          "fit_index_sha256": sha256((root / "fit_index.json").read_bytes())},
                         sort_keys=True))
        return 0
    summary = run_screen(root, b212_root, screen, references, fit_context)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
