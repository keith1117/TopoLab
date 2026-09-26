"""B2.7 frozen global-load encoding fit and independent development screen."""

from __future__ import annotations

import argparse
import json
import resource
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

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
from b2_6_trajectory import (
    _read_model as read_b26_model,
)
from b2_6_trajectory import (
    _read_selection as read_b26_selection,
)
from b2_6_trajectory import (
    cohorts as b26_cohorts,
)
from b2_workload_pilot import scaled_case
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_5_evaluation import _charged_result, build_shape_neighbors
from topolab.b2_6_trajectory import SEEDS, TrajectorySample, fit_trajectory_seed
from topolab.b2_7_conditioning import ENCODING_VERSION, encode_global_load_case
from topolab.experiment import ExperimentCase
from topolab.training import WarmStartCNN

PLAN_VERSION = "topolab.b2_7.global_load.v1"
EXPECTED_PLAN_SHA256 = "1311405f25e20cc7214cc744bb8843bfa791af1232351c71a4c2c639af369e9d"
B26_TARGET_INDEX_SHA256 = "5bff3753871a088a8e5217410ca0d692b5bb5e04496bab8c28f198b5c974a8bf"
B26_FIT_INDEX_SHA256 = "9ed71fa5929b12cd731a77a0a17a32d81b1cc933f9accd6e501222f018d1e062"
VOLUMES = (0.2375, 0.3875, 0.5375)
FIT_CAP = 7_200.0
SCREEN_CAP = 14_400.0
MAX_RSS = 2_147_483_648
METHODS = (
    "uniform", "physics_heuristic", "nearest_neighbor", "control_43",
    *(f"trajectory_{seed}" for seed in SEEDS),
    *(f"conditioned_{seed}" for seed in SEEDS),
    "trajectory_oracle",
)


def _peak_rss() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def cohorts() -> tuple[dict[str, tuple[ExperimentCase, ...]], tuple[ExperimentCase, ...]]:
    """Retain B2.6 fitting definitions and create one untouched screen."""

    old = b26_cohorts()
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for direction in ("y", "z"):
            small = _small_case(volume, direction, 5, 2)
            selected.extend((small, scaled_case(small)))
    screen = tuple(sorted(selected, key=lambda case: case.case_id))
    old_ids = {case.case_id for cases in old.values() for case in cases}
    ids = [case.case_id for case in screen]
    if len(screen) != 12 or len(set(ids)) != 12 or old_ids.intersection(ids):
        raise ValueError("B2.7 screen overlaps historical fitting or screen cases")
    strata = Counter(
        (
            case.problem.mesh.element_counts,
            case.problem.loads[0].direction,
            case.problem.optimization.volume_fraction,
        )
        for case in screen
    )
    if len(strata) != 12 or any(count != 1 for count in strata.values()):
        raise ValueError("B2.7 screen strata differ")
    return old, screen


def plan_payload(
    old: dict[str, tuple[ExperimentCase, ...]], screen: tuple[ExperimentCase, ...]
) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "encoding_version": ENCODING_VERSION,
        "b26_target_index_sha256": B26_TARGET_INDEX_SHA256,
        "b26_fit_index_sha256": B26_FIT_INDEX_SHA256,
        "b25_fit_index_sha256": B25_FIT_SHA256,
        "b25_control43_checkpoint_sha256": B25_CONTROL43_SHA256,
        "target_update": 30,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 240,
        "seeds": list(SEEDS),
        "train_case_ids": [case.case_id for case in old["train"]],
        "validation_case_ids": [case.case_id for case in old["validation"]],
        "screen_case_ids": [case.case_id for case in screen],
        "screen_volumes": list(VOLUMES),
        "screen_load_node_small": [12, 5, 2],
        "methods": list(METHODS),
        "fit_cap_seconds": FIT_CAP,
        "screen_cap_seconds": SCREEN_CAP,
        "max_rss_bytes": MAX_RSS,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _prior(
    b26_root: Path, old: dict[str, tuple[ExperimentCase, ...]]
) -> tuple[dict[str, Any], dict[str, Any]]:
    target_bytes = (b26_root / "target_index.json").read_bytes()
    fit_bytes = (b26_root / "fit_index.json").read_bytes()
    if sha256(target_bytes) != B26_TARGET_INDEX_SHA256 or sha256(fit_bytes) != B26_FIT_INDEX_SHA256:
        raise ValueError("B2.6 source artifact checksum differs")
    targets = json.loads(target_bytes)
    fits = json.loads(fit_bytes)
    if len(targets["rows"]) != 480 or len(fits["rows"]) != 3:
        raise ValueError("B2.6 source artifact population differs")
    ordered = [(split, case) for split in ("train", "validation") for case in old[split]]
    for row, (split, case) in zip(targets["rows"], ordered, strict=True):
        _read_target(b26_root, row, case, split, targets["context"])
    for row, seed in zip(fits["rows"], SEEDS, strict=True):
        if row["seed"] != seed:
            raise ValueError("B2.6 source model order differs")
        read_b26_selection(b26_root, row, fits["context"])
    return targets, fits


def _samples(
    b26_root: Path,
    old: dict[str, tuple[ExperimentCase, ...]],
    targets: dict[str, Any],
    split: str,
) -> tuple[TrajectorySample, ...]:
    offset = 0 if split == "train" else 468
    samples: list[TrajectorySample] = []
    for index, case in enumerate(old[split]):
        target = _read_target(
            b26_root, targets["rows"][offset + index], case, split, targets["context"]
        )
        sample = TrajectorySample(
            case_id=case.case_id,
            split=split,  # type: ignore[arg-type]
            inputs=torch.from_numpy(encode_global_load_case(case).input_tensor.copy()),
            target=torch.from_numpy(target.density.copy()),
        )
        sample.validate()
        samples.append(sample)
    return tuple(samples)


def _index(root: Path, name: str, context: dict[str, Any], maximum: int) -> dict[str, Any]:
    path = root / name
    if not path.exists():
        return {"context": context, "rows": [], "elapsed_seconds": 0.0, "peak_rss_bytes": 0}
    index = json.loads(path.read_bytes())
    if index.get("context") != context or len(index.get("rows", [])) > maximum:
        raise ValueError(f"B2.7 {name} context or population differs")
    return index


def _checkpoint_path(root: Path, seed: int, digest: str) -> Path:
    return root / "checkpoints" / str(seed) / f"{digest}.safetensors"


def _selection_path(root: Path, seed: int, digest: str) -> Path:
    return root / "selections" / str(seed) / f"{digest}.json"


def _read_model(root: Path, row: dict[str, Any], context: dict[str, Any]) -> WarmStartCNN:
    seed = row["seed"]
    contents = _checkpoint_path(root, seed, row["checkpoint_sha256"]).read_bytes()
    if sha256(contents) != row["checkpoint_sha256"] or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.7 checkpoint checksum or size differs")
    header_length = int.from_bytes(contents[:8], "little")
    header = json.loads(contents[8 : 8 + header_length])
    metadata = json.loads(header["__metadata__"]["topolab"])
    if metadata != {
        "version": "topolab.b2_7.checkpoint.v1",
        "context": context,
        "seed": seed,
        "selected_epoch": row["selected_epoch"],
    }:
        raise ValueError("B2.7 checkpoint provenance differs")
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
        raise ValueError("B2.7 checkpoint tensor differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_selection(root: Path, row: dict[str, Any], context: dict[str, Any]) -> None:
    contents = _selection_path(root, row["seed"], row["selection_sha256"]).read_bytes()
    if sha256(contents) != row["selection_sha256"] or len(contents) != row["selection_bytes"]:
        raise ValueError("B2.7 selection checksum or size differs")
    selection = json.loads(contents)
    if (
        canonical_bytes(selection) != contents
        or selection["version"] != "topolab.b2_7.selection.v1"
        or selection["context"] != context
        or selection["seed"] != row["seed"]
        or selection["checkpoint_sha256"] != row["checkpoint_sha256"]
        or selection["selected_epoch"] != row["selected_epoch"]
        or selection["selected_validation_loss"] != row["selected_validation_loss"]
    ):
        raise ValueError("B2.7 selection provenance differs")
    history = selection["history"]
    if (
        not history or len(history) > 200
        or [entry["epoch"] for entry in history] != list(range(1, len(history) + 1))
    ):
        raise ValueError("B2.7 selection history differs")
    minimum = min(entry["validation_loss"] for entry in history)
    first = next(entry["epoch"] for entry in history if entry["validation_loss"] == minimum)
    if first != row["selected_epoch"] or minimum != row["selected_validation_loss"]:
        raise ValueError("B2.7 selection is not the earliest minimum")
    if len(history) < 200 and len(history) - first != 25:
        raise ValueError("B2.7 selection violates patience")
    _read_model(root, row, context)


def fit_models(
    root: Path,
    b26_root: Path,
    old: dict[str, tuple[ExperimentCase, ...]],
    targets: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    index = _index(root, "fit_index.json", context, 3)
    for row, seed in zip(index["rows"], SEEDS, strict=False):
        if row["seed"] != seed:
            raise ValueError("B2.7 fit order differs")
        _read_selection(root, row, context)
    started = perf_counter()
    prior = index["elapsed_seconds"]
    if len(index["rows"]) < 3:
        train = _samples(b26_root, old, targets, "train")
        validation = _samples(b26_root, old, targets, "validation")
        for position in range(len(index["rows"]), 3):
            if prior + perf_counter() - started > FIT_CAP:
                raise ValueError("B2.7 fit wall budget exhausted")
            seed = SEEDS[position]
            fit = fit_trajectory_seed(train, validation, seed=seed)
            metadata = {
                "version": "topolab.b2_7.checkpoint.v1",
                "context": context,
                "seed": seed,
                "selected_epoch": fit.selected_epoch,
            }
            checkpoint = save_tensors(
                dict(sorted(fit.state.items())),
                metadata={"topolab": canonical_bytes(metadata).decode("utf-8")},
            )
            digest = sha256(checkpoint)
            atomic_write(_checkpoint_path(root, seed, digest), checkpoint)
            selection = {
                "version": "topolab.b2_7.selection.v1",
                "context": context,
                "seed": seed,
                "history": fit.history,
                "selected_epoch": fit.selected_epoch,
                "selected_validation_loss": fit.selected_validation_loss,
                "fit_seconds": fit.seconds,
                "checkpoint_sha256": digest,
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
                "checkpoint_sha256": digest,
                "checkpoint_bytes": len(checkpoint),
                "selection_sha256": selection_sha,
                "selection_bytes": len(selection_bytes),
            }
            _read_selection(root, row, context)
            index["rows"].append(row)
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "fit_index.json", canonical_bytes(index))
            print(f"B2.7 fit {position + 1}/3 seed={seed}", file=sys.stderr, flush=True)
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "fit_index.json", canonical_bytes(index))
    if (
        len(index["rows"]) != 3 or index["elapsed_seconds"] > FIT_CAP
        or index["peak_rss_bytes"] > MAX_RSS
    ):
        raise ValueError("B2.7 complete fit resource Gate failed")
    return index


def screen_models(
    root: Path,
    b26_root: Path,
    b24_root: Path,
    b25_root: Path,
    old: dict[str, tuple[ExperimentCase, ...]],
    screen: tuple[ExperimentCase, ...],
    context: dict[str, Any],
) -> dict[str, Any]:
    fits = _index(root, "fit_index.json", context, 3)
    if (
        len(fits["rows"]) != 3
        or fits["elapsed_seconds"] > FIT_CAP
        or fits["peak_rss_bytes"] > MAX_RSS
    ):
        raise ValueError("B2.7 screen requires complete audited fits")
    for row, seed in zip(fits["rows"], SEEDS, strict=True):
        if row["seed"] != seed:
            raise ValueError("B2.7 model order differs")
        _read_selection(root, row, context)
    screen_context = {
        **context,
        "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
    }
    index = _index(root, "screen_index.json", screen_context, 12)
    for position, row in enumerate(index["rows"]):
        case = screen[position]
        if (
            row["case"]["case_id"] != case.case_id
            or [outcome["method"] for outcome in row["outcomes"]] != list(METHODS)
            or any(outcome["case_id"] != case.case_id for outcome in row["outcomes"])
        ):
            raise ValueError("B2.7 screen row identity or method order differs")
    started = perf_counter()
    prior = index["elapsed_seconds"]
    if len(index["rows"]) < 12:
        load_started = perf_counter()
        new_models = {row["seed"]: _read_model(root, row, context) for row in fits["rows"]}
        old_fits = json.loads((b26_root / "fit_index.json").read_bytes())
        old_models = {
            row["seed"]: read_b26_model(b26_root, row, old_fits["context"])
            for row in old_fits["rows"]
        }
        if sha256((b25_root / "fit_index.json").read_bytes()) != B25_FIT_SHA256:
            raise ValueError("B2.5 fixed fit index differs")
        old_b25 = json.loads((b25_root / "fit_index.json").read_bytes())
        audited_b25 = read_b25_fits(b25_root, old_b25["context"])
        control_row = next(
            row for row in audited_b25["rows"]
            if (row["arm"], row["seed"]) == ("control", 43)
        )
        if control_row["checkpoint_sha256"] != B25_CONTROL43_SHA256:
            raise ValueError("B2.5 fixed control differs")
        control = read_b25_checkpoint(b25_root, control_row, audited_b25["context"])
        index["model_loading_seconds"] = (
            index.get("model_loading_seconds", 0.0) + perf_counter() - load_started
        )
        neighbor_started = perf_counter()
        from b2_4_materialize_labels import select_cases as b24_cases

        source_cases = b24_cases()
        source_index = read_data_index(b24_root, source_cases)
        neighbors = build_shape_neighbors(load_samples(b24_root, source_index, split="train"))
        index["neighbor_loading_seconds"] = (
            index.get("neighbor_loading_seconds", 0.0) + perf_counter() - neighbor_started
        )
        index["neighbor_bytes"] = sum(value.stored_size_bytes for value in neighbors.values())
        for position in range(len(index["rows"]), 12):
            if prior + perf_counter() - started > SCREEN_CAP:
                raise ValueError("B2.7 screen wall budget exhausted")
            case = screen[position]
            case_started = perf_counter()
            nx, ny, nz = case.problem.mesh.element_counts
            outcomes, oracle = _case_outcomes(
                case, old_models, control, neighbors[(nz, ny, nx)]
            )
            oracle_outcome = outcomes.pop()
            for seed in SEEDS:
                item = _charged_result(
                    case, "candidate", seed, outcomes[0], model=new_models[seed],
                    encoder=encode_global_load_case,
                )
                item["method"] = f"conditioned_{seed}"
                outcomes.append(item)
            outcomes.append(oracle_outcome)
            if [item["method"] for item in outcomes] != list(METHODS):
                raise ValueError("B2.7 method order differs")
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
                f"B2.7 screen {position + 1}/12 {row['case']['scale']}",
                file=sys.stderr,
                flush=True,
            )
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "screen_index.json", canonical_bytes(index))
    return _screen_summary(
        root, index, learned_prefix="conditioned_",
        summary_version="topolab.b2_7.screen_summary.v1",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b26-root", type=Path, default=Path("/tmp/topolab-b26"))
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b25-root", type=Path, default=Path("/tmp/topolab-b25"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--fit", action="store_true")
    group.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    old, screen = cohorts()
    plan = plan_payload(old, screen)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.7 plan differs from its frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b26_root = _external_root(repository, args.b26_root)
    if root == b26_root:
        raise ValueError("B2.7 output and B2.6 source roots must differ")
    context = {
        "plan_sha256": plan["plan_sha256"],
        "source_revision": revision,
        "runtime": runtime,
        "b26_target_index_sha256": B26_TARGET_INDEX_SHA256,
    }
    if not (args.fit or args.screen):
        print(json.dumps({**plan, **context}, sort_keys=True))
        return 0
    targets, _ = _prior(b26_root, old)
    if args.fit:
        index = fit_models(root, b26_root, old, targets, context)
        print(json.dumps({
            "fit_index_sha256": sha256((root / "fit_index.json").read_bytes()),
            "fits": index["rows"],
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"],
        }, sort_keys=True))
        return 0
    summary = screen_models(
        root, b26_root, args.b24_root.resolve(), args.b25_root.resolve(),
        old, screen, context,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["prototype_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
