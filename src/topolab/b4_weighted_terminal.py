"""Separate B4.5 identity, guarded weighted labels and fixed development Gate."""

import json
from collections.abc import Callable, Iterable
from dataclasses import replace
from pathlib import Path
from typing import Any, Literal

import numpy as np
import torch
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from topolab.b2_6_trajectory import TrajectorySample
from topolab.b2_12_context_cnn import ContextCNN
from topolab.b3_access import B3Access
from topolab.b3_artifacts import read_b3_record, safe_path
from topolab.b3_catalog import (
    _grid,
    build_b3_case_catalog,
    build_b3_exposure_ledger,
    canonical_metadata_bytes,
    physical_fingerprint,
)
from topolab.b3_dataset import B3LabelRecord
from topolab.b3_materialization import B3DataSuccess
from topolab.b3_queries import QueryOutcome, policy_route
from topolab.b3_training import (
    SEEDS,
    B3Fit,
    _fit_samples,
    case_weights,
    fitting_entries,
    sample_from_label,
)
from topolab.b3_training_artifacts import B3Selection, B3TrainingContext, FitFile
from topolab.b4_telemetry import Progress, digest, durable_write
from topolab.experiment import ExperimentCase

VERSION = "topolab.b4_5.weighted-terminal.v1"
RECORDING_ALLOWANCE = 1.0
MAX_EPOCH_ATTEMPTS = 600
METHODS = (
    "uniform",
    "physics_heuristic",
    "nearest_neighbor",
    *(f"{p}/{s}" for p in ("C", "P", "W") for s in SEEDS),
)
CAPS = {
    "fit": (3600.0, 4_294_967_296),
    "reference": (3600.0, 2_147_483_648),
    "screen": (21600.0, 2_147_483_648),
    "audit": (3600.0, 2_147_483_648),
}


def fresh_cases() -> tuple[ExperimentCase, ...]:
    cases = tuple(
        sorted(
            _grid((0.3317, 0.4657, 0.5397, 0.5977), ((1, 2), (3, 1), (5, 2)), 360),
            key=lambda c: c.case_id,
        )
    )
    blocked = {e.physical_fingerprint for e in build_b3_exposure_ledger().entries}
    blocked.update(e.physical_fingerprint for e in build_b3_case_catalog().entries)
    fingerprints = {physical_fingerprint(c) for c in cases}
    if len(cases) != 48 or len(fingerprints) != 48 or fingerprints & blocked:
        raise ValueError("new development cohort crosses a prior physical exposure")
    return cases


def method_order(case: ExperimentCase) -> tuple[str, ...]:
    other = METHODS[1:]
    offset = int(digest(("topolab.b4_5.order.v1:" + case.case_id).encode())[:8], 16) % len(other)
    return ("uniform", *other[offset:], *other[:offset])


def assignments() -> tuple[tuple[str, str], ...]:
    return tuple((c.case_id, method) for c in fresh_cases() for method in method_order(c))


def plan() -> dict[str, Any]:
    payload = {
        "version": VERSION,
        "cases": [c.model_dump(mode="json") for c in fresh_cases()],
        "methods": METHODS,
        "assignments": assignments(),
        "seeds": SEEDS,
        "objective": "mean spatial sensitivity MSE then unchanged P case weighting",
        "selection": "earliest strict minimum unweighted equal-case validation MSE",
        "train_cases": 508,
        "validation_cases": 32,
        "recording_allowance_seconds": RECORDING_ALLOWANCE,
        "max_epoch_attempts": MAX_EPOCH_ATTEMPTS,
        "caps": CAPS,
        "final_access": False,
    }
    return {**payload, "plan_sha256": digest(canonical_metadata_bytes(payload))}


def weighted_samples(
    data_root: Path, context: B3TrainingContext, pulse: Callable[[], None]
) -> tuple[tuple[TrajectorySample, ...], tuple[TrajectorySample, ...]]:
    access = B3Access(consumer="fitting", training_set="expanded")
    train, validation = fitting_entries("P")
    ids = set((*train, *validation))
    artifacts = tuple(
        o.artifact
        for o in context.data_index.entries
        if isinstance(o, B3DataSuccess) and o.entry.case.case_id in ids
    )
    actual = tuple(a.access.entry.case.case_id for a in artifacts)
    if len(actual) != len(ids) or set(actual) != ids:
        raise ValueError("weighted fitting requires the full expanded membership before bytes")
    for artifact in artifacts:
        access._authorize_bytes(artifact.access)
    samples = {}
    for artifact in artifacts:
        pulse()
        record = read_b3_record(data_root, context.data_index.manifest, artifact, access)
        if not isinstance(record, B3LabelRecord):
            raise ValueError("weighted fitting requires a terminal label")
        sample = sample_from_label(record)
        if sample.split == "train":
            sample = replace(
                sample,
                weight=torch.from_numpy(
                    np.asarray(record.stored.sensitivity_weight, dtype=np.float32)
                    .reshape(record.stored.tensor_shape)
                    .copy()
                ),
            )
        sample.validate()
        samples[sample.case_id] = sample
    return tuple(samples[i] for i in train), tuple(samples[i] for i in validation)


def fit_weighted(
    train: tuple[TrajectorySample, ...],
    validation: tuple[TrajectorySample, ...],
    seed: int,
    checkpoint: Callable[[bool], None],
) -> B3Fit:
    train_ids, validation_ids = fitting_entries("P")
    if (
        seed not in SEEDS
        or tuple(s.case_id for s in train) != train_ids
        or tuple(s.case_id for s in validation) != validation_ids
    ):
        raise ValueError("weighted fit differs from the fixed seed/membership")
    for split, samples in (("train", train), ("validation", validation)):
        for sample in samples:
            sample.validate()
            if (
                sample.split != split
                or sample.input_channels != 13
                or (sample.weight is not None) != (split == "train")
            ):
                raise ValueError("weighted sample representation differs")
    return _fit_samples(
        train,
        validation,
        seed=seed,
        weights=case_weights("P"),
        checkpoint=checkpoint,
        element_weighted=True,
    )


def publish_blob(root: Path, kind: str, raw: bytes) -> dict[str, Any]:
    sha = digest(raw)
    suffix = "safetensors" if kind == "checkpoint" else "json"
    path = f"artifacts/{kind}/{sha}.{suffix}"
    target = safe_path(root, path)
    if target.exists():
        if target.read_bytes() != raw:
            raise ValueError("content-addressed bytes differ")
    else:
        durable_write(target, raw)
    return {"path": path, "sha256": sha, "byte_size": len(raw)}


def read_blob(root: Path, ref: dict[str, Any], kind: str) -> bytes:
    suffix = "safetensors" if kind == "checkpoint" else "json"
    if ref["path"] != f"artifacts/{kind}/{ref['sha256']}.{suffix}":
        raise ValueError("artifact path differs from its content identity")
    raw = safe_path(root, ref["path"]).read_bytes()
    if digest(raw) != ref["sha256"] or len(raw) != ref["byte_size"]:
        raise ValueError("artifact byte hash or size differs")
    return raw


def checkpoint_metadata(context_sha: str, seed: int, epoch: int) -> str:
    return canonical_metadata_bytes(
        {
            "version": "topolab.b4_5.checkpoint.v1",
            "context_sha256": context_sha,
            "seed": seed,
            "epoch": epoch,
            "objective": VERSION,
        }
    ).decode()


def publish_weighted_fit(root: Path, context_sha: str, seed: int, fit: B3Fit) -> dict[str, Any]:
    checkpoint = publish_blob(
        root,
        "checkpoint",
        save_tensors(
            fit.state,
            metadata={"topolab": checkpoint_metadata(context_sha, seed, fit.selected_epoch)},
        ),
    )
    # B3Selection is reused only as the already tested history/early-stop schema.
    history = B3Selection.model_validate(
        {
            "context_sha256": context_sha,
            "recipe": "P",
            "seed": seed,
            "history": fit.history,
            "selected_epoch": fit.selected_epoch,
            "selected_validation_loss": fit.selected_validation_loss,
            "fit_seconds": fit.seconds,
            "checkpoint": FitFile(
                kind="checkpoint", sha256=checkpoint["sha256"], byte_size=checkpoint["byte_size"]
            ),
        }
    )
    payload = {
        "version": "topolab.b4_5.selection.v1",
        "objective": VERSION,
        "history_schema": history.model_dump(mode="json"),
        "checkpoint": checkpoint,
    }
    return publish_blob(root, "selection", canonical_metadata_bytes(payload))


def read_weighted_model(
    root: Path, context_sha: str, seed: int, ref: dict[str, Any]
) -> tuple[B3Selection, ContextCNN]:
    raw = read_blob(root, ref, "selection")
    packet = json.loads(raw)
    if (
        canonical_metadata_bytes(packet) != raw
        or set(packet) != {"version", "objective", "history_schema", "checkpoint"}
        or packet["version"] != "topolab.b4_5.selection.v1"
        or packet["objective"] != VERSION
    ):
        raise ValueError("weighted selection identity differs")
    history = B3Selection.model_validate(packet["history_schema"])
    checkpoint = packet["checkpoint"]
    if (
        history.context_sha256 != context_sha
        or history.seed != seed
        or history.recipe != "P"
        or history.checkpoint.sha256 != checkpoint["sha256"]
        or history.checkpoint.byte_size != checkpoint["byte_size"]
    ):
        raise ValueError("weighted selection source or selected checkpoint differs")
    raw = read_blob(root, checkpoint, "checkpoint")
    length = int.from_bytes(raw[:8], "little")
    header = json.loads(raw[8 : 8 + length])
    if header.get("__metadata__", {}) != {
        "topolab": checkpoint_metadata(context_sha, seed, history.selected_epoch)
    }:
        raise ValueError("weighted checkpoint provenance differs")
    tensors = load_tensors(raw)
    with torch.random.fork_rng(devices=[]):
        model = ContextCNN()
    expected = model.state_dict()
    if set(tensors) != set(expected) or any(
        t.dtype != torch.float32 or t.shape != expected[n].shape or not torch.isfinite(t).all()
        for n, t in tensors.items()
    ):
        raise ValueError("weighted checkpoint architecture or finite float32 tensors differ")
    model.load_state_dict(tensors, strict=True)
    model.eval()
    return history, model


def read_units(
    root: Path,
    context_sha: str,
    units: tuple[str, ...],
    *,
    caps: dict[str, tuple[float, int]] | None = None,
) -> list[dict[str, Any]]:
    limits = CAPS if caps is None else caps
    raw = safe_path(root, "progress.json").read_bytes()
    progress = Progress.model_validate_json(raw)
    if (
        canonical_metadata_bytes(progress.model_dump(mode="json")) != raw
        or progress.context_sha256 != context_sha
        or progress.units_sha256 != digest(canonical_metadata_bytes(list(units)))
        or progress.active_at is not None
        or progress.pending is not None
        or progress.completed != len(units)
        or progress.integrity_failed
        or progress.resource_failed
        or progress.charged_seconds > limits[root.name][0]
        or progress.peak_rss_bytes > limits[root.name][1]
    ):
        raise ValueError("source journal lacks a closed complete passed prefix")
    records, previous = [], "0" * 64
    for ordinal, unit in enumerate(units):
        raw = safe_path(root, f"units/{ordinal:04d}.json").read_bytes()
        packet = json.loads(raw)
        if (
            canonical_metadata_bytes(packet) != raw
            or packet["unit"] != unit
            or packet["context_sha256"] != context_sha
            or packet["version"] != "topolab.b4.unit.v1"
            or packet["previous_sha256"] != previous
        ):
            raise ValueError("source journal chain or assignment differs")
        records.append(packet["payload"])
        previous = digest(raw)
    if previous != progress.head_sha256:
        raise ValueError("source journal head differs")
    return records


def development_gate(
    packets: Iterable[dict[str, Any]],
    *,
    cohort: tuple[ExperimentCase, ...] | None = None,
    expected: tuple[tuple[str, str], ...] | None = None,
    quality_volumes: tuple[float, float] = (0.5397, 0.5977),
    quality_minimum: int = 6,
    candidate: Literal["W", "P"] = "W",
) -> dict[str, Any]:
    expected = assignments() if expected is None else expected
    cases = {c.case_id: c for c in (fresh_cases() if cohort is None else cohort)}
    by_method: dict[str, list[tuple[ExperimentCase, dict[str, Any], float]]] = {
        m: [] for m in METHODS
    }
    uniform = {}
    count = 0
    for p in packets:
        if count >= len(expected) or (p["case_id"], p["policy"]) != expected[count]:
            raise ValueError("Gate requires every fixed case/method exactly once in order")
        count += 1
        outcome = QueryOutcome.model_validate(p["outcome"])
        policy = p["policy"]
        name, _, seed_text = policy.partition("/")
        method: Literal["uniform", "physics_heuristic", "nearest_neighbor", "C", "P"]
        method = "P" if name == "W" else name
        seed = int(seed_text) if seed_text else None
        wall = p["timing"]["wall_seconds"]
        if (
            outcome.method != method
            or outcome.seed != seed
            or outcome.operational is None
            or outcome.route != policy_route(cases[p["case_id"]], method)
            or not np.isfinite(wall)
            or wall <= 0
            or p["timing"]["legacy_phase_seconds"] > wall
            or p["recording_allowance_seconds"] != RECORDING_ALLOWANCE
        ):
            raise ValueError("Gate outcome quality, timing or assignment differs")
        seconds = wall + RECORDING_ALLOWANCE
        if policy == "uniform":
            uniform[p["case_id"]] = seconds
        by_method[policy].append(
            (
                cases[p["case_id"]],
                {
                    "failed": outcome.attempt is not None and not outcome.attempt.succeeded,
                    "fallback": outcome.fallback is not None,
                    "route": outcome.route,
                },
                seconds / uniform[p["case_id"]],
            )
        )
    if count != len(expected):
        raise ValueError("Gate requires every fixed case/method exactly once in order")
    table = {}
    for name, rows in by_method.items():
        scales = {
            s: float(
                np.mean(
                    [
                        r
                        for c, _, r in rows
                        if (c.problem.mesh.element_counts[0] == 12) == (s == "small")
                    ]
                )
            )
            for s in ("small", "large")
        }
        directions = {
            f"{s}/{d}": float(
                np.mean(
                    [
                        r
                        for c, _, r in rows
                        if (c.problem.mesh.element_counts[0] == 12) == (s == "small")
                        and c.problem.loads[0].direction == d
                    ]
                )
            )
            for s in ("small", "large")
            for d in ("y", "z")
        }
        table[name] = {
            "overall_mean": float(np.mean([r for _, _, r in rows])),
            "scale_means": scales,
            "direction_means": directions,
            "failures": sum(q["failed"] for _, q, _ in rows),
            "fallbacks": sum(q["fallback"] for _, q, _ in rows),
            "non_specialist_y_failures": sum(
                q["failed"]
                for c, q, _ in rows
                if c.problem.loads[0].direction == "y" and q["route"] != "specialist"
            ),
        }
    comparison = "P" if candidate == "W" else "W"
    passing, eligible = [], []
    for seed in SEEDS:
        w, c, p = (table[f"{name}/{seed}"] for name in (candidate, "C", comparison))
        passed = (
            max(w["scale_means"].values()) <= 0.9
            and max(w["direction_means"].values()) <= 1.0
            and w["failures"] <= min(2, c["failures"], p["failures"])
            and w["non_specialist_y_failures"]
            <= min(c["non_specialist_y_failures"], p["non_specialist_y_failures"])
            and w["overall_mean"]
            < min(table[n]["overall_mean"] for n in ("physics_heuristic", "nearest_neighbor"))
        )
        primary = (
            passed
            and w["failures"] == w["fallbacks"] == 0
            and w["overall_mean"] < c["overall_mean"]
            and (w["overall_mean"] < p["overall_mean"] or w["failures"] < p["failures"])
        )
        w.update(seed_gate_passed=passed, primary_eligible=primary)
        if passed:
            passing.append(seed)
        if primary:
            eligible.append(seed)
    cells = {
        str(v): sum(
            not q["failed"]
            for seed in SEEDS
            for c, q, _ in by_method[f"{candidate}/{seed}"]
            if c.problem.mesh.element_counts[0] == 24
            and c.problem.loads[0].direction == "y"
            and c.problem.optimization.volume_fraction == v
        )
        for v in quality_volumes
    }
    selected = (
        min(
            eligible,
            key=lambda seed: (
                max(table[f"{candidate}/{seed}"]["scale_means"].values()),
                max(table[f"{candidate}/{seed}"]["direction_means"].values()),
                table[f"{candidate}/{seed}"]["overall_mean"],
                SEEDS.index(seed),
            ),
        )
        if eligible
        else None
    )
    return {
        "table": table,
        "passing_seeds": passing,
        "development_primary": selected,
        "quality_cells": cells,
        "development_gate_passed": len(passing) >= 2
        and selected is not None
        and min(cells.values()) >= quality_minimum,
        "final_access": False,
    }
