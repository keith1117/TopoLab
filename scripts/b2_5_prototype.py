"""Guarded B2.5 two-arm fitting and full development-validation screen."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import resource
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from time import perf_counter
from typing import Any

import numpy as np
import torch
from b2_4_materialize_labels import plan_payload as b24_plan_payload
from b2_4_materialize_labels import row_identity, select_cases
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_4_labels import B24Label
from topolab.b2_5_evaluation import build_shape_neighbors, evaluate_b25_case
from topolab.b2_5_training import SEEDS, B25Arm, B25Sample, fit_b25_arm
from topolab.training import M1_MODEL_PARAMETER_COUNT, WarmStartCNN

DATA_PLAN_SHA256 = "015ab799be88a5fef763720b2e1c58281dc17aea67c61435bcb87d254f64169c"
DATA_INDEX_SHA256 = "dad9109aca6d4e14a851c266fd1b8a490885cf2565281ee85ceba1d164f59244"
LABEL_SOURCE_REVISION = "7f4d0f6a1512b5be8f6ea192430608108bafe2cc"
PLAN_VERSION = "topolab.b2_5.prototype.v1"
FIT_INDEX_VERSION = "topolab.b2_5.fits.v1"
SCREEN_INDEX_VERSION = "topolab.b2_5.screen.v1"
FIT_MAX_SECONDS = 14_400.0
SCREEN_MAX_SECONDS = 14_400.0
MAX_RSS_BYTES = 2_147_483_648
EXPECTED_PLAN_SHA256 = "03978254d4cba90113a83813109e0415201885e66c28c1b7cc7bf9e5b392c5ff"
ARMS: tuple[B25Arm, ...] = ("control", "candidate")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def sha256(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def atomic_write(path: Path, contents: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=".b25-", suffix=".tmp", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(contents)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return value if sys.platform == "darwin" else value * 1024


def source_snapshot() -> tuple[Path, str, dict[str, Any]]:
    repository = Path(
        subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
    ).resolve()
    for args in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"]):
        if subprocess.run(args, cwd=repository, check=False).returncode != 0:
            raise ValueError("B2.5 execution requires a clean tracked revision")
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    runtime = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": importlib.metadata.version("scipy"),
        "torch": torch.__version__,
        "safetensors": importlib.metadata.version("safetensors"),
        "uv_lock_sha256": sha256((repository / "uv.lock").read_bytes()),
        "system": platform.system(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "torch_threads": torch.get_num_threads(),
        "torch_interop_threads": torch.get_num_interop_threads(),
    }
    return repository, revision, runtime


def external_root(repository: Path, requested: Path, data_root: Path) -> Path:
    root = requested.resolve()
    if root == repository or root.is_relative_to(repository):
        raise ValueError("B2.5 output root must be outside the repository")
    if root == data_root or root.is_relative_to(data_root):
        raise ValueError("B2.5 output root must not alter B2.4 labels")
    return root


def read_data_index(data_root: Path, cases: tuple[Any, ...]) -> dict[str, Any]:
    contents = (data_root / "b2_4_index.json").read_bytes()
    if sha256(contents) != DATA_INDEX_SHA256:
        raise ValueError("B2.4 data index differs from the passed Gate evidence")
    index: dict[str, Any] = json.loads(contents)
    if (
        index.get("plan_sha256") != DATA_PLAN_SHA256
        or index.get("source_revision") != LABEL_SOURCE_REVISION
        or len(index.get("rows", ())) != 522
    ):
        raise ValueError("B2.4 index has the wrong identity or population")
    for position, item in enumerate(cases):
        row = index["rows"][position]
        if row["identity"] != row_identity(item) or row["status"] != "succeeded":
            raise ValueError("B2.4 index has a missing or changed label row")
    return index


def plan_payload(cases: tuple[Any, ...]) -> dict[str, Any]:
    validation = [row_identity(item) for item in cases if item.source.split == "validation"]
    identity = {
        "plan_version": PLAN_VERSION,
        "data_plan_sha256": DATA_PLAN_SHA256,
        "data_index_sha256": DATA_INDEX_SHA256,
        "model_version": "topolab.m1.cnn.v1",
        "model_parameter_count": M1_MODEL_PARAMETER_COUNT,
        "arms": list(ARMS),
        "seeds": list(SEEDS),
        "training_cases": 468,
        "validation_cases": validation,
        "train_batch_schedule": "shape_bucketed_shuffle_once_per_epoch_v1",
        "methods": ["uniform", "physics_heuristic", "nearest_neighbor",
                    *[f"{arm}_{seed}" for arm in ARMS for seed in SEEDS]],
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 240,
        "fit_max_seconds": FIT_MAX_SECONDS,
        "screen_max_seconds": SCREEN_MAX_SECONDS,
        "max_rss_bytes": MAX_RSS_BYTES,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _artifact_path(root: Path, kind: str, arm: B25Arm, seed: int, digest: str) -> Path:
    suffix = "safetensors" if kind == "checkpoints" else "json"
    return root / kind / arm / str(seed) / f"{digest}.{suffix}"


def _read_label(data_root: Path, row: dict[str, Any], data_index: dict[str, Any]) -> B24Label:
    identity = row["identity"]
    digest = row["artifact_sha256"]
    path = data_root / "labels" / identity["new_case_id"] / f"{digest}.json"
    contents = path.read_bytes()
    if sha256(contents) != digest or len(contents) != row["artifact_bytes"]:
        raise ValueError("B2.4 label checksum or length changed")
    label = B24Label.model_validate_json(contents)
    if (
        label.case.case_id != identity["new_case_id"]
        or label.source_case_id != identity["source_case_id"]
        or label.result_id != identity["result_id"]
        or label.split != identity["split"]
        or label.scale != identity["scale"]
        or label.direction != identity["direction"]
        or label.volume != identity["volume"]
        or label.source_revision != LABEL_SOURCE_REVISION
        or label.environment.model_dump(mode="json") != data_index["environment"]
    ):
        raise ValueError("B2.4 label differs from the frozen development plan")
    return label


def load_samples(
    data_root: Path,
    data_index: dict[str, Any],
    *,
    split: str,
) -> tuple[B25Sample, ...]:
    if split not in ("train", "validation"):
        raise ValueError("B2.5 must not open test or OOD labels")
    samples = [
        B25Sample.from_label(_read_label(data_root, row, data_index))
        for row in data_index["rows"] if row["identity"]["split"] == split
    ]
    result = tuple(sorted(samples, key=lambda sample: sample.case.case_id))
    if len(result) != (468 if split == "train" else 54):
        raise ValueError("B2.5 development split is incomplete")
    return result


def _fit_index_path(root: Path) -> Path:
    return root / "fit_index.json"


def _screen_index_path(root: Path) -> Path:
    return root / "screen_index.json"


def _checkpoint_metadata(
    context: dict[str, Any], arm: B25Arm, seed: int, epoch: int
) -> dict[str, Any]:
    return {
        "artifact_version": "topolab.b2_5.checkpoint.v1",
        "context": context,
        "arm": arm,
        "seed": seed,
        "selected_epoch": epoch,
        "model_version": "topolab.m1.cnn.v1",
    }


def _checkpoint_bytes(
    state: dict[str, torch.Tensor], metadata: dict[str, Any]
) -> bytes:
    return save_tensors(
        dict(sorted(state.items())),
        metadata={"topolab": canonical_bytes(metadata).decode("utf-8")},
    )


def _read_checkpoint(
    root: Path, row: dict[str, Any], context: dict[str, Any]
) -> WarmStartCNN:
    arm: B25Arm = row["arm"]
    seed: int = row["seed"]
    digest: str = row["checkpoint_sha256"]
    contents = _artifact_path(root, "checkpoints", arm, seed, digest).read_bytes()
    if sha256(contents) != digest or len(contents) != row["checkpoint_bytes"]:
        raise ValueError("B2.5 checkpoint checksum or size differs")
    header_length = int.from_bytes(contents[:8], "little")
    header = json.loads(contents[8 : 8 + header_length])
    metadata = json.loads(header["__metadata__"]["topolab"])
    if metadata != _checkpoint_metadata(context, arm, seed, row["selected_epoch"]):
        raise ValueError("B2.5 checkpoint provenance differs")
    state = load_tensors(contents)
    with torch.random.fork_rng(devices=[]):
        model = WarmStartCNN()
    expected = model.state_dict()
    if set(state) != set(expected):
        raise ValueError("B2.5 checkpoint tensor names differ")
    for name, tensor in state.items():
        if (
            tensor.dtype != torch.float32
            or tensor.shape != expected[name].shape
            or not torch.isfinite(tensor).all()
        ):
            raise ValueError("B2.5 checkpoint tensor shape, type, or value differs")
    model.load_state_dict(state, strict=True)
    model.eval()
    return model


def _read_selection(root: Path, row: dict[str, Any], context: dict[str, Any]) -> None:
    arm: B25Arm = row["arm"]
    seed: int = row["seed"]
    digest: str = row["selection_sha256"]
    contents = _artifact_path(root, "selections", arm, seed, digest).read_bytes()
    if sha256(contents) != digest or len(contents) != row["selection_bytes"]:
        raise ValueError("B2.5 selection checksum or size differs")
    selection = json.loads(contents)
    if canonical_bytes(selection) != contents:
        raise ValueError("B2.5 selection is not canonical JSON")
    if (
        selection["selection_version"] != "topolab.b2_5.selection.v1"
        or selection["context"] != context
        or selection["arm"] != arm
        or selection["seed"] != seed
        or selection["checkpoint_sha256"] != row["checkpoint_sha256"]
        or selection["selected_epoch"] != row["selected_epoch"]
        or selection["selected_validation_loss"] != row["selected_validation_loss"]
    ):
        raise ValueError("B2.5 selection provenance or outcome differs")
    history = selection["history"]
    if (
        not history
        or len(history) > 200
        or [metric["epoch"] for metric in history] != list(range(1, len(history) + 1))
    ):
        raise ValueError("B2.5 selection epoch history is invalid")
    minimum = min(metric["validation_loss"] for metric in history)
    first = next(metric["epoch"] for metric in history if metric["validation_loss"] == minimum)
    if first != row["selected_epoch"] or minimum != row["selected_validation_loss"]:
        raise ValueError("B2.5 selection is not the earliest objective minimum")
    if len(history) < 200 and len(history) - first != 25:
        raise ValueError("B2.5 selection violates the patience rule")
    _read_checkpoint(root, row, context)


def _fit_context(plan: dict[str, Any], revision: str, runtime: dict[str, Any]) -> dict[str, Any]:
    return {
        "plan_sha256": plan["plan_sha256"],
        "data_index_sha256": DATA_INDEX_SHA256,
        "label_source_revision": LABEL_SOURCE_REVISION,
        "training_source_revision": revision,
        "source_tree_clean": True,
        "runtime": runtime,
    }


def _read_fit_index(
    root: Path, context: dict[str, Any]
) -> dict[str, Any]:
    path = _fit_index_path(root)
    if not path.exists():
        return {
            "index_version": FIT_INDEX_VERSION,
            "context": context,
            "rows": [],
            "elapsed_seconds": 0.0,
            "peak_rss_bytes": 0,
        }
    index: dict[str, Any] = json.loads(path.read_bytes())
    if index.get("index_version") != FIT_INDEX_VERSION or index.get("context") != context:
        raise ValueError("B2.5 fit index belongs to a different frozen context")
    required = [(arm, seed) for arm in ARMS for seed in SEEDS]
    if len(index["rows"]) > 6:
        raise ValueError("B2.5 fit index has too many selections")
    for position, row in enumerate(index["rows"]):
        if (row["arm"], row["seed"]) != required[position]:
            raise ValueError("B2.5 fit order differs from the frozen plan")
        _read_selection(root, row, context)
    return index


def _write_fit_artifacts(
    root: Path,
    fit: Any,
    context: dict[str, Any],
) -> dict[str, Any]:
    metadata = _checkpoint_metadata(context, fit.arm, fit.seed, fit.selected_epoch)
    checkpoint = _checkpoint_bytes(fit.state, metadata)
    checkpoint_sha = sha256(checkpoint)
    checkpoint_path = _artifact_path(root, "checkpoints", fit.arm, fit.seed, checkpoint_sha)
    if checkpoint_path.exists():
        if checkpoint_path.read_bytes() != checkpoint:
            raise ValueError("existing B2.5 checkpoint differs")
    else:
        atomic_write(checkpoint_path, checkpoint)
    selection = {
        "selection_version": "topolab.b2_5.selection.v1",
        "context": context,
        "arm": fit.arm,
        "seed": fit.seed,
        "train_case_count": 468,
        "validation_case_count": 54,
        "history": fit.history,
        "selected_epoch": fit.selected_epoch,
        "selected_validation_loss": fit.selected_validation_loss,
        "fit_seconds": fit.duration_seconds,
        "checkpoint_sha256": checkpoint_sha,
    }
    selection_bytes = canonical_bytes(selection)
    selection_sha = sha256(selection_bytes)
    selection_path = _artifact_path(root, "selections", fit.arm, fit.seed, selection_sha)
    if selection_path.exists():
        if selection_path.read_bytes() != selection_bytes:
            raise ValueError("existing B2.5 selection differs")
    else:
        atomic_write(selection_path, selection_bytes)
    row = {
        "arm": fit.arm,
        "seed": fit.seed,
        "epochs": len(fit.history),
        "selected_epoch": fit.selected_epoch,
        "selected_validation_loss": fit.selected_validation_loss,
        "fit_seconds": fit.duration_seconds,
        "checkpoint_sha256": checkpoint_sha,
        "checkpoint_bytes": len(checkpoint),
        "selection_sha256": selection_sha,
        "selection_bytes": len(selection_bytes),
    }
    _read_selection(root, row, context)
    return row


def run_fits(
    root: Path,
    data_root: Path,
    data_index: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    started = perf_counter()
    index = _read_fit_index(root, context)
    base_seconds = float(index["elapsed_seconds"])
    if len(index["rows"]) < 6:
        train = load_samples(data_root, data_index, split="train")
        validation = load_samples(data_root, data_index, split="validation")
        ordered = [(arm, seed) for arm in ARMS for seed in SEEDS]
        for position in range(len(index["rows"]), 6):
            if base_seconds + perf_counter() - started > FIT_MAX_SECONDS:
                raise ValueError("B2.5 six-fit wall budget exhausted")
            arm, seed = ordered[position]
            fit = fit_b25_arm(train, validation, arm=arm, seed=seed)
            row = _write_fit_artifacts(root, fit, context)
            index["rows"].append(row)
            index["elapsed_seconds"] = base_seconds + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], peak_rss_bytes())
            atomic_write(_fit_index_path(root), canonical_bytes(index))
            print(
                f"B2.5 fit {position + 1}/6 {arm} seed={seed} "
                f"selected={fit.selected_epoch} epochs={len(fit.history)}",
                file=sys.stderr, flush=True,
            )
    index["elapsed_seconds"] = base_seconds + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], peak_rss_bytes())
    atomic_write(_fit_index_path(root), canonical_bytes(index))
    if (
        len(index["rows"]) != 6
        or index["elapsed_seconds"] > FIT_MAX_SECONDS
        or index["peak_rss_bytes"] > MAX_RSS_BYTES
    ):
        raise ValueError("B2.5 complete six-fit resource Gate failed")
    return index


def _read_screen_index(
    root: Path, context: dict[str, Any], validation: tuple[Any, ...]
) -> dict[str, Any]:
    path = _screen_index_path(root)
    if not path.exists():
        return {
            "index_version": SCREEN_INDEX_VERSION,
            "context": context,
            "rows": [],
            "elapsed_seconds": 0.0,
            "peak_rss_bytes": 0,
            "model_loading_seconds": 0.0,
            "neighbor_loading_seconds": 0.0,
            "neighbor_bytes": 0,
        }
    index: dict[str, Any] = json.loads(path.read_bytes())
    if index.get("index_version") != SCREEN_INDEX_VERSION or index.get("context") != context:
        raise ValueError("B2.5 screen index belongs to a different frozen context")
    if len(index["rows"]) > len(validation):
        raise ValueError("B2.5 screen index has too many cases")
    methods = ["uniform", "physics_heuristic", "nearest_neighbor",
               *[arm for arm in ARMS for _ in SEEDS]]
    seeds = [None, None, None, *[seed for _arm in ARMS for seed in SEEDS]]
    for position, row in enumerate(index["rows"]):
        identity = row_identity(validation[position])
        if row["identity"] != identity or len(row["outcomes"]) != 9:
            raise ValueError("B2.5 screen row identity or method count differs")
        if [(item["method"], item["seed"]) for item in row["outcomes"]] != list(
            zip(methods, seeds, strict=True)
        ):
            raise ValueError("B2.5 screen method order differs")
        if any(item["case_id"] != identity["new_case_id"] for item in row["outcomes"]):
            raise ValueError("B2.5 screen outcome has a different case identity")
    return index


def _screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    rows = index["rows"]
    ratios: defaultdict[tuple[str, int | None, str], list[float]] = defaultdict(list)
    direction_ratios: defaultdict[
        tuple[str, int | None, str, str], list[float]
    ] = defaultdict(list)
    volume_ratios: defaultdict[
        tuple[str, int | None, str, str, float], list[float]
    ] = defaultdict(list)
    failures: Counter[str] = Counter()
    fallbacks: Counter[str] = Counter()
    accepted_quality_failures = 0
    for row in rows:
        identity = row["identity"]
        for item in row["outcomes"]:
            method = item["method"]
            seed = item["seed"]
            key = f"{method}_{seed}" if seed is not None else method
            if not item["succeeded"]:
                failures[key] += 1
            if item["fallback_used"]:
                fallbacks[key] += 1
            if item["succeeded"] and (
                item["operational"]["final_compliance"]
                > 1.001 * item["uniform_reference_compliance"]
                or item["operational"]["physical_volume_error"] > 0.005
            ):
                accepted_quality_failures += 1
            ratio = float(item["paired_time_ratio"])
            ratios[(method, seed, identity["scale"])].append(ratio)
            direction_ratios[(method, seed, identity["scale"], identity["direction"])].append(
                ratio
            )
            volume_ratios[(method, seed, identity["scale"], identity["direction"],
                           identity["volume"])].append(ratio)
    means = {
        f"{method}_{seed}_{scale}": float(np.mean(values))
        for (method, seed, scale), values in sorted(ratios.items(), key=str)
    }
    direction_means = {
        f"{method}_{seed}_{scale}_{direction}": float(np.mean(values))
        for (method, seed, scale, direction), values in sorted(direction_ratios.items(), key=str)
    }
    volume_means = {
        f"{method}_{seed}_{scale}_{direction}_{volume:.2f}": float(np.mean(values))
        for (method, seed, scale, direction, volume), values in sorted(
            volume_ratios.items(), key=str
        )
    }
    passing: dict[str, list[int]] = {arm: [] for arm in ARMS}
    if len(rows) == 54 and accepted_quality_failures == 0:
        for arm in ARMS:
            for seed in SEEDS:
                if all(
                    means[f"{arm}_{seed}_{scale}"] <= 0.90
                    and all(
                        direction_means[f"{arm}_{seed}_{scale}_{direction}"] <= 1.0
                        for direction in ("y", "z")
                    )
                    for scale in ("small", "large")
                ):
                    passing[arm].append(seed)
    gate = (
        len(rows) == 54
        and accepted_quality_failures == 0
        and any(len(seeds) >= 2 for seeds in passing.values())
        and index["elapsed_seconds"] <= SCREEN_MAX_SECONDS
        and index["peak_rss_bytes"] <= MAX_RSS_BYTES
    )
    return {
        "summary_version": "topolab.b2_5.screen-summary.v1",
        "context": index["context"],
        "screen_index_sha256": sha256(_screen_index_path(root).read_bytes()),
        "cases": len(rows),
        "outcomes": sum(len(row["outcomes"]) for row in rows),
        "mean_time_ratios": means,
        "direction_mean_time_ratios": direction_means,
        "volume_mean_time_ratios": volume_means,
        "failure_counts": dict(sorted(failures.items())),
        "fallback_counts": dict(sorted(fallbacks.items())),
        "accepted_quality_failures": accepted_quality_failures,
        "passing_seeds": passing,
        "model_loading_seconds": index["model_loading_seconds"],
        "neighbor_loading_seconds": index["neighbor_loading_seconds"],
        "neighbor_bytes": index["neighbor_bytes"],
        "screen_seconds": index["elapsed_seconds"],
        "peak_rss_bytes": index["peak_rss_bytes"],
        "prototype_gate_passed": gate,
    }


def run_screen(
    root: Path,
    data_root: Path,
    data_index: dict[str, Any],
    plan: dict[str, Any],
    cases: tuple[Any, ...],
    fit_context: dict[str, Any],
) -> dict[str, Any]:
    started = perf_counter()
    fit_index = _read_fit_index(root, fit_context)
    if len(fit_index["rows"]) != 6:
        raise ValueError("B2.5 screen requires all six audited fits")
    if (
        fit_index["elapsed_seconds"] > FIT_MAX_SECONDS
        or fit_index["peak_rss_bytes"] > MAX_RSS_BYTES
    ):
        raise ValueError("B2.5 six-fit resource Gate failed")
    context = {
        **fit_context,
        "fit_index_sha256": sha256(_fit_index_path(root).read_bytes()),
        "screen_plan_sha256": plan["plan_sha256"],
    }
    validation = tuple(item for item in cases if item.source.split == "validation")
    if len(validation) != 54:
        raise ValueError("B2.5 validation population differs")
    index = _read_screen_index(root, context, validation)
    base_seconds = float(index["elapsed_seconds"])
    if len(index["rows"]) < 54:
        model_started = perf_counter()
        models = {
            (row["arm"], row["seed"]): _read_checkpoint(root, row, fit_context)
            for row in fit_index["rows"]
        }
        index["model_loading_seconds"] += perf_counter() - model_started
        neighbor_started = perf_counter()
        train = load_samples(data_root, data_index, split="train")
        neighbors = build_shape_neighbors(train)
        index["neighbor_loading_seconds"] += perf_counter() - neighbor_started
        index["neighbor_bytes"] = sum(item.stored_size_bytes for item in neighbors.values())
        for position in range(len(index["rows"]), len(validation)):
            if base_seconds + perf_counter() - started > SCREEN_MAX_SECONDS:
                raise ValueError("B2.5 screen wall budget exhausted")
            item = validation[position]
            case_started = perf_counter()
            nx, ny, nz = item.case.problem.mesh.element_counts
            outcomes = evaluate_b25_case(
                item.case, models=models, neighbors=neighbors[(nz, ny, nx)]
            )
            index["rows"].append(
                {
                    "identity": row_identity(item),
                    "outcomes": outcomes,
                    "seconds": perf_counter() - case_started,
                }
            )
            index["elapsed_seconds"] = base_seconds + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], peak_rss_bytes())
            atomic_write(_screen_index_path(root), canonical_bytes(index))
            print(
                f"B2.5 screen {position + 1}/54 {item.source.scale} "
                f"{item.case.case_id}", file=sys.stderr, flush=True,
            )
    index["elapsed_seconds"] = base_seconds + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], peak_rss_bytes())
    atomic_write(_screen_index_path(root), canonical_bytes(index))
    return _screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--fit", action="store_true")
    parser.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    if args.fit and args.screen:
        parser.error("run fitting and screening in separate invocations")
    cases = select_cases()
    if b24_plan_payload(cases)["plan_sha256"] != DATA_PLAN_SHA256:
        raise ValueError("B2.4 case metadata differs from frozen source")
    plan = plan_payload(cases)
    if EXPECTED_PLAN_SHA256 and plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.5 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    data_root = args.data_root.resolve()
    root = external_root(repository, args.output_root, data_root)
    data_index = read_data_index(data_root, cases)
    context = _fit_context(plan, revision, runtime)
    if not args.fit and not args.screen:
        print(json.dumps({**plan, "source_revision": revision, "runtime": runtime}, sort_keys=True))
        return 0
    if not EXPECTED_PLAN_SHA256:
        parser.error("execution requires a frozen plan checksum")
    if args.fit:
        index = run_fits(root, data_root, data_index, context)
        print(json.dumps({
            "fit_index_sha256": sha256(_fit_index_path(root).read_bytes()),
            "fits": index["rows"],
            "fit_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"],
        }, sort_keys=True))
        return 0
    summary = run_screen(root, data_root, data_index, plan, cases, context)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["prototype_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
