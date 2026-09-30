"""B2.29 fixed-checkpoint, larger independent development confirmation."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from b2_4_materialize_labels import select_cases
from b2_5_prototype import (
    DATA_INDEX_SHA256,
    atomic_write,
    canonical_bytes,
    load_samples,
    read_data_index,
    sha256,
    source_snapshot,
)
from b2_6_trajectory import _external_root, _small_case
from b2_7_global_load import _peak_rss
from b2_9_vector_load import _index
from b2_11_reference_budget import versioned_case
from b2_14_development_confirmation import _point_node, _uniform_result
from b2_20_operational_selection import reference_gate, run_references
from b2_24_expanded_training import _read_fit_index as read_specialist_fit_index
from b2_24_expanded_training import _read_model as read_specialist_model
from b2_24_expanded_training import specialist_case
from b2_26_weighted_generalist import _read_fit_index as read_old_fit_index
from b2_26_weighted_generalist import _read_model as read_old_model
from b2_28_expanded_generalist import B224_FIT_SHA256, B226_FIT_SHA256
from b2_28_expanded_generalist import EXPECTED_PLAN_SHA256 as B228_PLAN_SHA256
from b2_28_expanded_generalist import _read_fit_index as read_expanded_fit_index
from b2_28_expanded_generalist import _read_model as read_expanded_model
from b2_28_expanded_generalist import cohorts as b228_cohorts
from b2_workload_pilot import scaled_case

from topolab.b2_5_evaluation import _charged_result, build_shape_neighbors
from topolab.b2_6_trajectory import SEEDS
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_29.development_confirmation.v1"
EXPECTED_PLAN_SHA256 = "5cc928fedfe5827dab3fb24b4203361e4ca866d9bc1203a054859d5e2c835590"
B228_FIT_SHA256 = "0d874a0ea7c0c4f87740b1630033dc80418e44975f0c1e0a266f4f6fe553f402"
B228_SCREEN_SHA256 = "55bfc7e74b2b5250e49b5beafcfbc5af844c9d2ec514edd02d2d0fdf088b2586"
B228_SOURCE = "d8e97010e94ce63d1939a4a1454746c68f7124e8"
VOLUMES = (0.3185, 0.4565, 0.5315, 0.5895)
POSITIONS = ((1, 1), (3, 2), (5, 1))
CASE_COUNT = 48
REFERENCE_CAP = 7_200.0
SCREEN_CAP = 48_000.0
MAX_RSS = 2_147_483_648
MAX_FAILURES = 2
MIN_Y_SUCCESSES = 6
NON_ML = ("physics_heuristic", "nearest_neighbor")
METHODS = ("uniform", *NON_ML, *(f"old_{seed}" for seed in SEEDS),
           *(f"expanded_{seed}" for seed in SEEDS))


def cohorts() -> tuple[tuple[ExperimentCase, ...], tuple[ExperimentCase, ...]]:
    _, previous, earlier = b228_cohorts()
    blocked = tuple(sorted({case.case_id: case for case in (*earlier, *previous)}.values(),
                           key=lambda case: case.case_id))
    excluded = {case.problem.optimization.volume_fraction for case in blocked}
    excluded.update(index / 100 for index in range(20, 61, 5))
    excluded.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & excluded:
        raise ValueError("B2.29 volume intersects exposed or reserved evidence")
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for y, z in POSITIONS:
            for direction in ("y", "z"):
                small = _small_case(volume, direction, y, z)
                selected.extend((versioned_case(small), versioned_case(scaled_case(small))))
    cases = tuple(sorted(selected, key=lambda case: case.case_id))
    strata = Counter((case.problem.mesh.element_counts, case.problem.loads[0].direction,
                      case.problem.optimization.volume_fraction) for case in cases)
    if (len(blocked) != 922 or len(cases) != CASE_COUNT
            or len({case.case_id for case in (*blocked, *cases)}) != 970
            or len(strata) != 16 or set(strata.values()) != {3}
            or sum(specialist_case(case) for case in cases) != 3
            or any(case.problem.optimization.max_iterations != 360 for case in cases)):
        raise ValueError("B2.29 population, strata, or route differs")
    return cases, blocked


def plan_payload(cases: tuple[ExperimentCase, ...],
                 blocked: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "intervention": "fixed_checkpoints_larger_independent_confirmation_no_fit",
        "b24_data_index_sha256": DATA_INDEX_SHA256,
        "b224_fit_index_sha256": B224_FIT_SHA256,
        "b226_fit_index_sha256": B226_FIT_SHA256,
        "b228_fit_index_sha256": B228_FIT_SHA256,
        "b228_screen_index_sha256": B228_SCREEN_SHA256,
        "b228_source_revision": B228_SOURCE,
        "screen_case_ids": [case.case_id for case in cases],
        "blocked_case_ids": [case.case_id for case in blocked],
        "screen_volumes": VOLUMES,
        "screen_positions_small": POSITIONS,
        "methods": METHODS,
        "seeds": SEEDS,
        "nearest_neighbor_train_cases": 468,
        "route": {"specialist_mesh": (24, 12, 6), "direction": "y",
                  "minimum_volume": 0.55},
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "solver_budget": 360,
        "screen_denominator": "fresh_timed_uniform_each_screen_case",
        "caps_seconds": {"references": REFERENCE_CAP, "screen": SCREEN_CAP},
        "max_rss_bytes": MAX_RSS,
        "gate_scale_mean_max": 0.90,
        "gate_direction_mean_max": 1.0,
        "gate_required_expanded_seeds": 2,
        "gate_failures_per_seed_max": MAX_FAILURES,
        "gate_failures_no_more_than_old": True,
        "gate_non_specialist_y_failures_no_more_than_old": True,
        "gate_each_eligible_seed_overall_below_both_non_ml": True,
        "gate_middle_volume_large_y_successes_min": MIN_Y_SUCCESSES,
        "gate_high_volume_large_y_successes_min": MIN_Y_SUCCESSES,
        "gate_accepted_quality_violations_max": 0,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def passing_seeds(scale_means: dict[str, float], directions: dict[str, float],
                  overall: dict[str, float], failures: Counter[str],
                  y_failures: Counter[str]) -> list[int]:
    return [seed for seed in SEEDS if (
        all(scale_means[f"expanded_{seed}/{scale}"] <= 0.90
            and all(directions[f"expanded_{seed}/{scale}/{direction}"] <= 1.0
                    for direction in ("y", "z")) for scale in ("small", "large"))
        and failures[f"expanded_{seed}"] <= min(MAX_FAILURES, failures[f"old_{seed}"])
        and y_failures[f"expanded_{seed}"] <= y_failures[f"old_{seed}"]
        and overall[f"expanded_{seed}"] < min(overall[method] for method in NON_ML)
    )]


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    ratios: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    y_failures: Counter[str] = Counter()
    high_success: Counter[str] = Counter()
    middle_success: Counter[str] = Counter()
    phases: defaultdict[str, Counter[str]] = defaultdict(Counter)
    quality_violations = 0
    for row in index["rows"]:
        case = row["case"]
        for item in row["outcomes"]:
            method = item["method"]
            ratios[(method, case["scale"], case["direction"])].append(item["paired_time_ratio"])
            phases[method].update(item["timing"])
            if not item["succeeded"]:
                failures[method] += 1
                if case["direction"] == "y" and not case["specialist_route"]:
                    y_failures[method] += 1
            else:
                metrics = item["operational"]
                if (not math.isfinite(metrics["final_compliance"])
                        or not 0 < metrics["final_compliance"]
                        <= 1.001 * item["uniform_reference_compliance"]
                        or not 0 <= metrics["physical_volume_error"] <= 0.005
                        or not 0 < metrics["iterations"] <= 360):
                    quality_violations += 1
                if method.startswith(("old_", "expanded_")):
                    panel = method.split("_")[0]
                    if case["specialist_route"]:
                        high_success[panel] += 1
                    if (case["scale"] == "large" and case["direction"] == "y"
                            and case["volume"] == VOLUMES[2]):
                        middle_success[panel] += 1
    directions = {"/".join(key): sum(values) / len(values)
                  for key, values in sorted(ratios.items())}
    scale_means, overall = {}, {}
    for method in METHODS:
        all_values = []
        for scale in ("small", "large"):
            values = [value for direction in ("y", "z")
                      for value in ratios[(method, scale, direction)]]
            if values:
                scale_means[f"{method}/{scale}"] = sum(values) / len(values)
                all_values.extend(values)
        if all_values:
            overall[method] = sum(all_values) / len(all_values)
    complete = len(index["rows"]) == CASE_COUNT and all(
        [item["method"] for item in row["outcomes"]] == list(METHODS)
        for row in index["rows"])
    passing = (passing_seeds(scale_means, directions, overall, failures, y_failures)
               if complete else [])
    gate = (complete and len(passing) >= 2
            and middle_success["expanded"] >= MIN_Y_SUCCESSES
            and high_success["expanded"] >= MIN_Y_SUCCESSES
            and quality_violations == 0 and index["elapsed_seconds"] <= SCREEN_CAP
            and index["peak_rss_bytes"] <= MAX_RSS)
    return {"version": "topolab.b2_29.screen_summary.v1",
            "screen_index_sha256": sha256((root / "screen_index.json").read_bytes()),
            "cases": len(index["rows"]),
            "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
            "scale_means": scale_means, "direction_means": directions,
            "overall_means": overall, "failure_counts": dict(sorted(failures.items())),
            "generalist_y_failure_counts": dict(sorted(y_failures.items())),
            "middle_volume_large_y_successes": dict(middle_success),
            "high_volume_large_y_successes": dict(high_success),
            "accepted_quality_violations": quality_violations,
            "phase_seconds": {key: dict(value) for key, value in sorted(phases.items())},
            "model_loading_seconds": index.get("model_loading_seconds", 0.0),
            "neighbor_loading_seconds": index.get("neighbor_loading_seconds", 0.0),
            "neighbor_bytes": index.get("neighbor_bytes", 0),
            "passing_seeds": passing, "gate_passed": gate,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"]}


def _case_metadata(case: ExperimentCase) -> dict[str, Any]:
    return {"case_id": case.case_id,
            "scale": "small" if case.problem.mesh.element_counts[0] == 12 else "large",
            "direction": case.problem.loads[0].direction,
            "volume": case.problem.optimization.volume_fraction,
            "node": _point_node(case), "specialist_route": specialist_case(case)}


def run_screen(root: Path, data_root: Path, b224_root: Path, b226_root: Path,
               b228_root: Path, cases: tuple[ExperimentCase, ...],
               references: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    context = {**context,
               "reference_index_sha256": sha256((root / "reference_index.json").read_bytes())}
    index = _index(root, "screen_index.json", context, CASE_COUNT)
    for row, case in zip(index["rows"], cases, strict=False):
        if (row["case"] != _case_metadata(case)
                or [item["method"] for item in row["outcomes"]] != list(METHODS)):
            raise ValueError("B2.29 persisted screen identity differs")
    if len(index["rows"]) == CASE_COUNT:
        return screen_summary(root, index)
    started, prior = perf_counter(), index["elapsed_seconds"]
    loading = perf_counter()
    panels = {}
    for name, source, reader, model_reader in (
        ("old", b226_root, read_old_fit_index, read_old_model),
        ("expanded", b228_root, read_expanded_fit_index, read_expanded_model),
        ("specialist", b224_root, read_specialist_fit_index, read_specialist_model),
    ):
        source_context = json.loads((source / "fit_index.json").read_bytes())["context"]
        if name == "expanded" and (source_context["source_revision"] != B228_SOURCE
                                   or source_context["plan_sha256"] != B228_PLAN_SHA256):
            raise ValueError("B2.29 expanded model source differs")
        fits = reader(source, source_context)
        if [row["seed"] for row in fits["rows"]] != list(SEEDS):
            raise ValueError("B2.29 fixed model panel is incomplete")
        panels[name] = {row["seed"]: model_reader(source, row, source_context)
                        for row in fits["rows"]}
    index["model_loading_seconds"] = index.get("model_loading_seconds", 0.0) + (
        perf_counter() - loading)
    loading = perf_counter()
    data = read_data_index(data_root, select_cases())
    samples = load_samples(data_root, data, split="train")
    if len(samples) != 468 or any(sample.split != "train" for sample in samples):
        raise ValueError("B2.29 nearest neighbor requires exactly B2.4 training")
    neighbors = build_shape_neighbors(samples)
    index["neighbor_loading_seconds"] = index.get("neighbor_loading_seconds", 0.0) + (
        perf_counter() - loading)
    index["neighbor_bytes"] = sum(value.stored_size_bytes for value in neighbors.values())
    for position in range(len(index["rows"]), CASE_COUNT):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.29 screen budget exhausted")
        case = cases[position]
        reference = _uniform_result(case)
        if not np.isclose(reference["candidate"]["final_compliance"],
                          references["rows"][position]["uniform"]["candidate"]["final_compliance"],
                          rtol=1e-9, atol=0.0):
            raise ValueError("B2.29 timed uniform differs from mandatory reference")
        outcomes = [reference]
        nx, ny, nz = case.problem.mesh.element_counts
        for method in NON_ML:
            outcomes.append(_charged_result(
                case, method, None, reference,
                neighbors=neighbors[(nz, ny, nx)] if method == "nearest_neighbor" else None,
            ))
        for prefix in ("old", "expanded"):
            for seed in SEEDS:
                route_start = perf_counter()
                use_specialist = specialist_case(case)
                model = panels["specialist" if use_specialist else prefix][seed]
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
        index["rows"].append({"case": _case_metadata(case), "outcomes": outcomes})
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "screen_index.json", canonical_bytes(index))
        print(f"B2.29 screen {position + 1}/{CASE_COUNT}", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b224-root", type=Path, default=Path("/tmp/topolab-b224"))
    parser.add_argument("--b226-root", type=Path, default=Path("/tmp/topolab-b226"))
    parser.add_argument("--b228-root", type=Path, default=Path("/tmp/topolab-b228"))
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--references", action="store_true")
    stage.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    cases, blocked = cohorts()
    plan = plan_payload(cases, blocked)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.29 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    roots = [_external_root(repository, path) for path in
             (args.output_root, args.b24_root, args.b224_root, args.b226_root, args.b228_root)]
    root, data_root, b224_root, b226_root, b228_root = roots
    if len(set(roots)) != 5:
        raise ValueError("B2.29 source and output roots must differ")
    for source, filename, digest in (
        (data_root, "b2_4_index.json", DATA_INDEX_SHA256),
        (b224_root, "fit_index.json", B224_FIT_SHA256),
        (b226_root, "fit_index.json", B226_FIT_SHA256),
        (b228_root, "fit_index.json", B228_FIT_SHA256),
        (b228_root, "screen_index.json", B228_SCREEN_SHA256),
    ):
        if sha256((source / filename).read_bytes()) != digest:
            raise ValueError(f"B2.29 source {filename} checksum differs")
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime, "b228_fit_index_sha256": B228_FIT_SHA256,
               "b224_fit_index_sha256": B224_FIT_SHA256,
               "b226_fit_index_sha256": B226_FIT_SHA256,
               "b24_data_index_sha256": DATA_INDEX_SHA256}
    if not any((args.references, args.screen)):
        print(json.dumps({"plan_sha256": plan["plan_sha256"], "source_revision": revision,
                          "screen_cases": len(cases), "blocked_cases": len(blocked),
                          "outcomes": CASE_COUNT * len(METHODS), "new_fits": 0}, sort_keys=True))
        return 0
    if args.references:
        references = run_references(root, "reference_index.json", context, cases, REFERENCE_CAP)
        passed = reference_gate(references, cases, REFERENCE_CAP)
        print(json.dumps({"cases": len(references["rows"]), "passed": passed,
                          "index_sha256": sha256((root / "reference_index.json").read_bytes())},
                         sort_keys=True))
        return 0 if passed else 1
    references = _index(root, "reference_index.json", context, CASE_COUNT)
    if not reference_gate(references, cases, REFERENCE_CAP):
        raise ValueError("B2.29 mandatory reference Gate required")
    summary = run_screen(root, data_root, b224_root, b226_root, b228_root,
                         cases, references, context)
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
