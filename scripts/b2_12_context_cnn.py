"""B2.12 frozen context-CNN fit and disjoint development comparison."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

import torch
from b2_4_materialize_labels import select_cases as b24_cases
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
from b2_6_trajectory import _case_outcomes, _external_root, _screen_summary, _small_case
from b2_7_global_load import B26_TARGET_INDEX_SHA256, _peak_rss, _prior, _samples
from b2_9_vector_load import _index
from b2_9_vector_load import _read_model as read_b29_model
from b2_9_vector_load import _read_selection as read_b29_selection
from b2_9_vector_load import cohorts as b29_cohorts
from b2_11_reference_budget import cohorts as b211_cohorts
from b2_11_reference_budget import versioned_case
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import _attempt, _charged_result, build_shape_neighbors
from topolab.b2_6_trajectory import SEEDS, fit_trajectory_seed
from topolab.b2_9_vector_load import ENCODING_VERSION, encode_vector_load_case
from topolab.b2_12_context_cnn import (
    CONTEXT_MODEL_PARAMETER_COUNT,
    MODEL_VERSION,
    ContextCNN,
)
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_12.context_cnn.v1"
EXPECTED_PLAN_SHA256 = "968d503bbdf30d3831e525a359a45315a620a114ac54ec61823b3df2ff7a8f97"
BUDGET = 360
VOLUMES = (0.3025, 0.4525, 0.6025)
B29_FIT_INDEX_SHA256 = "96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3"
B25_FIT_INDEX_SHA256 = "a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53"
B25_CONTROL43_SHA256 = "d82b7895355c1f73cde5b80d6328bc31c43c58cd7b1580974a590ef42bce0f4d"
REFERENCE_CAP = 1_800.0
FIT_CAP = 7_200.0
SCREEN_CAP = 14_400.0
MAX_RSS = 2_147_483_648
METHODS = (
    "uniform", "physics_heuristic", "nearest_neighbor", "control_43",
    *(f"vector_{seed}" for seed in SEEDS),
    *(f"context_{seed}" for seed in SEEDS),
    "trajectory_oracle",
)


def cohorts() -> tuple[
    dict[str, tuple[ExperimentCase, ...]], tuple[ExperimentCase, ...],
    tuple[ExperimentCase, ...],
]:
    """Keep fitting sources fixed and enumerate a new two-scale screen."""

    groups, _ = b29_cohorts()
    source, repaired, prior_screen, prior_exposed = b211_cohorts()
    exposed = tuple(sorted({case.case_id: case for case in (
        *prior_exposed, *source, *repaired, *prior_screen,
    )}.values(), key=lambda case: case.case_id))
    prior_volumes = {case.problem.optimization.volume_fraction for case in exposed}
    prior_volumes.update(index / 100 for index in range(20, 61, 5))
    prior_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & prior_volumes:
        raise ValueError("B2.12 volumes intersect development or final-design exposure")
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for direction in ("y", "z"):
            small = _small_case(volume, direction, 4, 1)
            selected.extend((versioned_case(small), versioned_case(scaled_case(small))))
    fresh = tuple(sorted(selected, key=lambda case: case.case_id))
    strata = Counter(
        (case.problem.mesh.element_counts, case.problem.loads[0].direction,
         case.problem.optimization.volume_fraction)
        for case in fresh
    )
    if (
        len(groups["train"]) != 468 or len(groups["validation"]) != 12
        or len(fresh) != 12 or len(strata) != 12
        or any(value != 1 for value in strata.values())
        or set(case.case_id for case in fresh) & set(case.case_id for case in exposed)
        or any(case.problem.optimization.max_iterations != BUDGET for case in fresh)
    ):
        raise ValueError("B2.12 population, identity, or budget differs")
    return groups, fresh, exposed


def plan_payload(
    groups: dict[str, tuple[ExperimentCase, ...]],
    fresh: tuple[ExperimentCase, ...],
    exposed: tuple[ExperimentCase, ...],
) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "encoding_version": ENCODING_VERSION,
        "model_version": MODEL_VERSION,
        "model_parameter_count": CONTEXT_MODEL_PARAMETER_COUNT,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": BUDGET,
        "target_update": 30,
        "b26_target_index_sha256": B26_TARGET_INDEX_SHA256,
        "b29_fit_index_sha256": B29_FIT_INDEX_SHA256,
        "b25_fit_index_sha256": B25_FIT_INDEX_SHA256,
        "b25_control43_checkpoint_sha256": B25_CONTROL43_SHA256,
        "seeds": list(SEEDS),
        "train_case_ids": [case.case_id for case in groups["train"]],
        "validation_case_ids": [case.case_id for case in groups["validation"]],
        "exposed_case_ids": [case.case_id for case in exposed],
        "exposed_volumes": sorted(
            {case.problem.optimization.volume_fraction for case in exposed}
            | {index / 100 for index in range(20, 61, 5)}
            | {index / 1000 for index in range(225, 576, 50)}
        ),
        "screen_case_ids": [case.case_id for case in fresh],
        "screen_volumes": list(VOLUMES),
        "screen_load_node_small": [12, 4, 1],
        "methods": list(METHODS),
        "reference_cap_seconds": REFERENCE_CAP,
        "fit_cap_seconds": FIT_CAP,
        "screen_cap_seconds": SCREEN_CAP,
        "max_rss_bytes": MAX_RSS,
        "gate_two_scale_mean_max": 0.90,
        "gate_each_direction_mean_max": 1.0,
        "gate_required_new_seeds": 2,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _reference_quality(attempt: dict[str, Any]) -> bool:
    candidate = attempt["candidate"]
    return (
        attempt["succeeded"] and candidate is not None
        and math.isfinite(candidate["final_compliance"])
        and candidate["final_compliance"] > 0
        and candidate["physical_volume_error"] <= 0.005
    )


def reference_gate(index: dict[str, Any], fresh: tuple[ExperimentCase, ...]) -> bool:
    return (
        len(index["rows"]) == 12
        and index["elapsed_seconds"] <= REFERENCE_CAP
        and index["peak_rss_bytes"] <= MAX_RSS
        and all(row["case_id"] == case.case_id and _reference_quality(row["uniform"])
                for row, case in zip(index["rows"], fresh, strict=True))
    )


def run_references(
    root: Path, context: dict[str, Any], fresh: tuple[ExperimentCase, ...]
) -> dict[str, Any]:
    index: dict[str, Any] = _index(root, "reference_index.json", context, 12)
    for position, row in enumerate(index["rows"]):
        if row["case_id"] != fresh[position].case_id:
            raise ValueError("B2.12 persisted reference identity differs")
    if len(index["rows"]) == 12:
        return index
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 12):
        if prior + perf_counter() - started > REFERENCE_CAP:
            raise ValueError("B2.12 reference wall budget exhausted")
        case = fresh[position]
        index["rows"].append({
            "case_id": case.case_id,
            "scale": "small" if case.problem.mesh.element_counts[0] == 12 else "large",
            "direction": case.problem.loads[0].direction,
            "volume": case.problem.optimization.volume_fraction,
            "uniform": _attempt(case, method="uniform", reference_compliance=None),
        })
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "reference_index.json", canonical_bytes(index))
        print(f"B2.12 reference {position + 1}/12", file=sys.stderr, flush=True)
    return index


def _checkpoint_path(root: Path, seed: int, digest: str) -> Path:
    return root / "checkpoints" / str(seed) / f"{digest}.safetensors"


def _selection_path(root: Path, seed: int, digest: str) -> Path:
    return root / "selections" / str(seed) / f"{digest}.json"


def _read_model(root: Path, row: dict[str, Any], context: dict[str, Any]) -> ContextCNN:
    seed = row["seed"]
    contents = _checkpoint_path(root, seed, row["checkpoint_sha256"]).read_bytes()
    if sha256(contents) != row["checkpoint_sha256"] or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.12 checkpoint checksum or size differs")
    header_length = int.from_bytes(contents[:8], "little")
    header = json.loads(contents[8 : 8 + header_length])
    metadata = json.loads(header["__metadata__"]["topolab"])
    if metadata != {
        "version": "topolab.b2_12.checkpoint.v1", "context": context,
        "seed": seed, "selected_epoch": row["selected_epoch"],
    }:
        raise ValueError("B2.12 checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = ContextCNN()
    expected = model.state_dict()
    if set(state) != set(expected) or any(
        tensor.dtype != torch.float32
        or tensor.shape != expected[name].shape
        or not torch.isfinite(tensor).all()
        for name, tensor in state.items()
    ):
        raise ValueError("B2.12 checkpoint tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_selection(root: Path, row: dict[str, Any], context: dict[str, Any]) -> None:
    contents = _selection_path(root, row["seed"], row["selection_sha256"]).read_bytes()
    if sha256(contents) != row["selection_sha256"] or len(contents) != row["selection_bytes"]:
        raise ValueError("B2.12 selection checksum or size differs")
    selection = json.loads(contents)
    if (
        canonical_bytes(selection) != contents
        or selection["version"] != "topolab.b2_12.selection.v1"
        or selection["context"] != context
        or selection["seed"] != row["seed"]
        or selection["checkpoint_sha256"] != row["checkpoint_sha256"]
        or selection["selected_epoch"] != row["selected_epoch"]
        or selection["selected_validation_loss"] != row["selected_validation_loss"]
    ):
        raise ValueError("B2.12 selection provenance differs")
    history = selection["history"]
    if not history or len(history) > 200 or [
        entry["epoch"] for entry in history
    ] != list(range(1, len(history) + 1)):
        raise ValueError("B2.12 selection history differs")
    minimum = min(entry["validation_loss"] for entry in history)
    first = next(entry["epoch"] for entry in history if entry["validation_loss"] == minimum)
    if first != row["selected_epoch"] or minimum != row["selected_validation_loss"]:
        raise ValueError("B2.12 selection is not the earliest strict minimum")
    if len(history) < 200 and len(history) - first != 25:
        raise ValueError("B2.12 selection violates patience")
    _read_model(root, row, context)


def _control_models(b29_root: Path) -> dict[int, torch.nn.Module]:
    if sha256((b29_root / "fit_index.json").read_bytes()) != B29_FIT_INDEX_SHA256:
        raise ValueError("B2.9 fixed fit index differs")
    fit = json.loads((b29_root / "fit_index.json").read_bytes())
    if [row["seed"] for row in fit["rows"]] != list(SEEDS):
        raise ValueError("B2.9 fixed model order differs")
    models: dict[int, torch.nn.Module] = {}
    for row in fit["rows"]:
        read_b29_selection(b29_root, row, fit["context"])
        models[row["seed"]] = read_b29_model(b29_root, row, fit["context"])
    return models


def fit_models(
    root: Path, b26_root: Path, b29_root: Path,
    groups: dict[str, tuple[ExperimentCase, ...]], context: dict[str, Any],
) -> dict[str, Any]:
    _control_models(b29_root)
    targets, _ = _prior(b26_root, groups)
    index: dict[str, Any] = _index(root, "fit_index.json", context, 3)
    for row, seed in zip(index["rows"], SEEDS, strict=False):
        if row["seed"] != seed:
            raise ValueError("B2.12 fit order differs")
        _read_selection(root, row, context)
    started, prior = perf_counter(), index["elapsed_seconds"]
    if len(index["rows"]) < 3:
        train = _samples(
            b26_root, groups, targets, "train", encoder=encode_vector_load_case,
            input_channels=13,
        )
        validation = _samples(
            b26_root, groups, targets, "validation", encoder=encode_vector_load_case,
            input_channels=13,
        )
        for position in range(len(index["rows"]), 3):
            if prior + perf_counter() - started > FIT_CAP:
                raise ValueError("B2.12 fit wall budget exhausted")
            seed = SEEDS[position]
            fit = fit_trajectory_seed(
                train, validation, seed=seed, model_factory=ContextCNN,
                expected_parameter_count=CONTEXT_MODEL_PARAMETER_COUNT, input_channels=13,
            )
            metadata = {
                "version": "topolab.b2_12.checkpoint.v1", "context": context,
                "seed": seed, "selected_epoch": fit.selected_epoch,
            }
            checkpoint = save_tensors(
                dict(sorted(fit.state.items())),
                metadata={"topolab": canonical_bytes(metadata).decode("utf-8")},
            )
            digest = sha256(checkpoint)
            atomic_write(_checkpoint_path(root, seed, digest), checkpoint)
            selection = {
                "version": "topolab.b2_12.selection.v1", "context": context,
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
            print(f"B2.12 fit {position + 1}/3 seed={seed}", file=sys.stderr, flush=True)
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "fit_index.json", canonical_bytes(index))
    if len(index["rows"]) != 3 or index["elapsed_seconds"] > FIT_CAP or (
        index["peak_rss_bytes"] > MAX_RSS
    ):
        raise ValueError("B2.12 complete fit resource Gate failed")
    return index


def screen_models(
    root: Path, b29_root: Path, b24_root: Path, b25_root: Path,
    fresh: tuple[ExperimentCase, ...], fit_context: dict[str, Any],
) -> dict[str, Any]:
    fits = _index(root, "fit_index.json", fit_context, 3)
    if len(fits["rows"]) != 3 or fits["elapsed_seconds"] > FIT_CAP or (
        fits["peak_rss_bytes"] > MAX_RSS
    ):
        raise ValueError("B2.12 screen requires complete audited fits")
    for row, seed in zip(fits["rows"], SEEDS, strict=True):
        if row["seed"] != seed:
            raise ValueError("B2.12 fit order differs")
        _read_selection(root, row, fit_context)
    screen_context = {
        **fit_context, "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
    }
    index = _index(root, "screen_index.json", screen_context, 12)
    for position, row in enumerate(index["rows"]):
        if row["case"]["case_id"] != fresh[position].case_id or [
            item["method"] for item in row["outcomes"]
        ] != list(METHODS):
            raise ValueError("B2.12 persisted screen identity differs")
    if len(index["rows"]) == 12:
        return screen_summary(root, index)
    started, prior = perf_counter(), index["elapsed_seconds"]
    loaded = perf_counter()
    old_models = _control_models(b29_root)
    new_models = {row["seed"]: _read_model(root, row, fit_context) for row in fits["rows"]}
    if sha256((b25_root / "fit_index.json").read_bytes()) != B25_FIT_INDEX_SHA256:
        raise ValueError("B2.5 fixed fit index differs")
    b25 = json.loads((b25_root / "fit_index.json").read_bytes())
    audited = read_b25_fits(b25_root, b25["context"])
    control_row = next(row for row in audited["rows"] if (
        row["arm"], row["seed"]
    ) == ("control", 43))
    if control_row["checkpoint_sha256"] != B25_CONTROL43_SHA256:
        raise ValueError("B2.5 control checkpoint differs")
    control = read_b25_checkpoint(b25_root, control_row, audited["context"])
    index["model_loading_seconds"] = (
        index.get("model_loading_seconds", 0.0) + perf_counter() - loaded
    )
    neighbor_started = perf_counter()
    source_index = read_data_index(b24_root, b24_cases())
    neighbors = build_shape_neighbors(load_samples(b24_root, source_index, split="train"))
    index["neighbor_loading_seconds"] = (
        index.get("neighbor_loading_seconds", 0.0) + perf_counter() - neighbor_started
    )
    index["neighbor_bytes"] = sum(value.stored_size_bytes for value in neighbors.values())
    for position in range(len(index["rows"]), 12):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.12 screen wall budget exhausted")
        case = fresh[position]
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
            item["method"] = f"context_{seed}"
            outcomes.append(item)
        outcomes.append(oracle_outcome)
        if [item["method"] for item in outcomes] != list(METHODS):
            raise ValueError("B2.12 method order differs")
        index["rows"].append({
            "case": {
                "case_id": case.case_id,
                "scale": "small" if nx == 12 else "large",
                "direction": case.problem.loads[0].direction,
                "volume": case.problem.optimization.volume_fraction,
            },
            "outcomes": outcomes,
            "oracle": oracle,
            "seconds": perf_counter() - case_started,
        })
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "screen_index.json", canonical_bytes(index))
        print(f"B2.12 screen {position + 1}/12", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    control = _screen_summary(
        root, index, learned_prefix="vector_",
        summary_version="topolab.b2_12.vector_control_screen.v1",
    )
    candidate = _screen_summary(
        root, index, learned_prefix="context_",
        summary_version="topolab.b2_12.context_screen.v1",
    )
    return {
        **candidate,
        "control_passing_seeds": control["passing_seeds"],
        "candidate_passing_seeds": candidate["passing_seeds"],
        "prototype_gate_passed": (
            candidate["prototype_gate_passed"] and candidate["outcomes"] == 132
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b26-root", type=Path, default=Path("/tmp/topolab-b26"))
    parser.add_argument("--b29-root", type=Path, default=Path("/tmp/topolab-b29"))
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b25-root", type=Path, default=Path("/tmp/topolab-b25"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--references", action="store_true")
    group.add_argument("--fit", action="store_true")
    group.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    groups, fresh, exposed = cohorts()
    plan = plan_payload(groups, fresh, exposed)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.12 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b26_root = _external_root(repository, args.b26_root)
    b29_root = _external_root(repository, args.b29_root)
    if len({root, b26_root, b29_root}) != 3:
        raise ValueError("B2.12 output and source roots must differ")
    context = {
        "plan_sha256": plan["plan_sha256"],
        "source_revision": revision,
        "runtime": runtime,
    }
    if not (args.references or args.fit or args.screen):
        print(json.dumps({**plan, **context}, sort_keys=True))
        return 0
    if args.references:
        references = run_references(root, context, fresh)
        passed = reference_gate(references, fresh)
        print(json.dumps({
            "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
            "cases": len(references["rows"]), "passed": passed,
            "elapsed_seconds": references["elapsed_seconds"],
            "peak_rss_bytes": references["peak_rss_bytes"],
        }, sort_keys=True))
        return 0 if passed else 1
    references = _index(root, "reference_index.json", context, 12)
    if not reference_gate(references, fresh):
        raise ValueError("B2.12 complete uniform-reference Gate required")
    fit_context = {
        **context,
        "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
        "b26_target_index_sha256": B26_TARGET_INDEX_SHA256,
        "b29_fit_index_sha256": B29_FIT_INDEX_SHA256,
    }
    if args.fit:
        fits = fit_models(root, b26_root, b29_root, groups, fit_context)
        print(json.dumps({
            "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
            "fits": fits["rows"], "elapsed_seconds": fits["elapsed_seconds"],
            "peak_rss_bytes": fits["peak_rss_bytes"],
        }, sort_keys=True))
        return 0
    _prior(b26_root, groups)
    summary = screen_models(
        root, b29_root, args.b24_root.resolve(), args.b25_root.resolve(),
        fresh, fit_context,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["prototype_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
