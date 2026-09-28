"""B2.15 frozen position-aware routing development screen."""

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
from b2_4_materialize_labels import select_cases as b24_cases
from b2_5_prototype import (
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
from b2_12_context_cnn import (
    B29_FIT_INDEX_SHA256,
    _control_models,
    _read_model,
    _read_selection,
)
from b2_13_routing import (
    B212_FIT_INDEX_SHA256,
    B212_SCREEN_INDEX_SHA256,
)
from b2_13_routing import (
    routed_result as old_routed_result,
)
from b2_14_development_confirmation import (
    EXPECTED_PLAN_SHA256 as B214_PLAN_SHA256,
)
from b2_14_development_confirmation import (
    cohorts as b214_cohorts,
)
from b2_workload_pilot import scaled_case

from topolab.b2_5_evaluation import _attempt, _charged_result, build_shape_neighbors
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_15_position_routing import route_case
from topolab.experiment import ExperimentCase
from topolab.problem import PointLoadDefinition

PLAN_VERSION = "topolab.b2_15.position_routing.v1"
EXPECTED_PLAN_SHA256 = "edeab8ca4cc1f059984ebbe84917991e9aef76fffd8ac47e226cbd8965c3b8b8"
B213_SCREEN_INDEX_SHA256 = "183e3448a9d7e3e82de6ed4dd3f38e5184977b7243aa9edd13284f950f8d3de0"
B214_SCREEN_INDEX_SHA256 = "2c2bb58c40bf1e2099fd21ecf3cc74a5425ca3f1ad28ac183611c1535bb4e6c9"
VOLUMES = (0.3175, 0.4675, 0.5825)
LOAD_POSITIONS = ((2, 1), (4, 2))
METHODS = (
    "uniform", "physics_heuristic", "nearest_neighbor", "vector_29",
    "context_17", "context_43", "old_routed", "new_routed",
)
FIXED = METHODS[3:6]
CASE_COUNT = 24
REFERENCE_CAP = 3_600.0
SCREEN_CAP = 10_800.0
MAX_RSS = 2_147_483_648
MAX_FAILURES = 2
ROUTER_ADVANTAGE = 0.95


def cohorts() -> tuple[tuple[ExperimentCase, ...], tuple[ExperimentCase, ...]]:
    previous, old_exposed = b214_cohorts()
    exposed = tuple(sorted({case.case_id: case for case in (
        *old_exposed, *previous,
    )}.values(), key=lambda case: case.case_id))
    exposed_volumes = {case.problem.optimization.volume_fraction for case in exposed}
    exposed_volumes.update(index / 100 for index in range(20, 61, 5))
    exposed_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & exposed_volumes:
        raise ValueError("B2.15 volume intersects exposed development or final design")
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for y, z in LOAD_POSITIONS:
            for direction in ("y", "z"):
                small = _small_case(volume, direction, y, z)
                selected.extend((versioned_case(small), versioned_case(scaled_case(small))))
    fresh = tuple(sorted(selected, key=lambda case: case.case_id))
    strata = Counter(
        (case.problem.mesh.element_counts, case.problem.loads[0].direction,
         case.problem.optimization.volume_fraction, _point_node(case))
        for case in fresh
    )
    if (
        len(fresh) != CASE_COUNT or len(strata) != CASE_COUNT
        or any(count != 1 for count in strata.values())
        or {case.case_id for case in fresh} & {case.case_id for case in exposed}
    ):
        raise ValueError("B2.15 screen population or physical disjointness differs")
    return fresh, exposed


def _point_node(case: ExperimentCase) -> int:
    load = case.problem.loads[0]
    if not isinstance(load, PointLoadDefinition):
        raise ValueError("B2.15 requires one point load")
    return load.node


def plan_payload(
    fresh: tuple[ExperimentCase, ...], exposed: tuple[ExperimentCase, ...]
) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 360,
        "b29_fit_index_sha256": B29_FIT_INDEX_SHA256,
        "b212_fit_index_sha256": B212_FIT_INDEX_SHA256,
        "b212_screen_index_sha256": B212_SCREEN_INDEX_SHA256,
        "b213_screen_index_sha256": B213_SCREEN_INDEX_SHA256,
        "b214_plan_sha256": B214_PLAN_SHA256,
        "b214_screen_index_sha256": B214_SCREEN_INDEX_SHA256,
        "screen_case_ids": [case.case_id for case in fresh],
        "exposed_case_ids": [case.case_id for case in exposed],
        "exposed_volumes": sorted(
            {case.problem.optimization.volume_fraction for case in exposed}
            | {index / 100 for index in range(20, 61, 5)}
            | {index / 1000 for index in range(225, 576, 50)}
        ),
        "screen_volumes": list(VOLUMES),
        "screen_load_nodes_small": [[12, y, z] for y, z in LOAD_POSITIONS],
        "methods": list(METHODS),
        "reference_cap_seconds": REFERENCE_CAP,
        "screen_cap_seconds": SCREEN_CAP,
        "max_rss_bytes": MAX_RSS,
        "gate_two_scale_mean_max": 0.90,
        "gate_each_direction_mean_max": 1.0,
        "gate_max_failed_attempts": MAX_FAILURES,
        "new_vs_best_eligible_fixed_multiplier": ROUTER_ADVANTAGE,
        "new_vs_old_route_multiplier": ROUTER_ADVANTAGE,
        "selection_order": list(FIXED),
        "routes": {case.case_id: route_case(case) for case in fresh},
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def reference_gate(index: dict[str, Any], fresh: tuple[ExperimentCase, ...]) -> bool:
    return (
        len(index["rows"]) == CASE_COUNT
        and index["elapsed_seconds"] <= REFERENCE_CAP
        and index["peak_rss_bytes"] <= MAX_RSS
        and all(
            row["case_id"] == case.case_id
            and row["uniform"]["succeeded"]
            and (candidate := row["uniform"]["candidate"]) is not None
            and math.isfinite(candidate["final_compliance"])
            and candidate["final_compliance"] > 0
            and candidate["physical_volume_error"] <= 0.005
            for row, case in zip(index["rows"], fresh, strict=True)
        )
    )


def run_references(
    root: Path, context: dict[str, Any], fresh: tuple[ExperimentCase, ...]
) -> dict[str, Any]:
    index = _index(root, "reference_index.json", context, CASE_COUNT)
    for position, row in enumerate(index["rows"]):
        if row["case_id"] != fresh[position].case_id:
            raise ValueError("B2.15 persisted reference identity differs")
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), CASE_COUNT):
        if prior + perf_counter() - started > REFERENCE_CAP:
            raise ValueError("B2.15 reference wall budget exhausted")
        case = fresh[position]
        index["rows"].append({
            "case_id": case.case_id,
            "scale": "small" if case.problem.mesh.element_counts[0] == 12 else "large",
            "direction": case.problem.loads[0].direction,
            "volume": case.problem.optimization.volume_fraction,
            "node": _point_node(case),
            "uniform": _attempt(case, method="uniform", reference_compliance=None),
        })
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "reference_index.json", canonical_bytes(index))
        print(f"B2.15 reference {position + 1}/{CASE_COUNT}", file=sys.stderr, flush=True)
    return index


def _uniform_result(case: ExperimentCase) -> dict[str, Any]:
    attempt = _attempt(case, method="uniform", reference_compliance=None)
    if not attempt["succeeded"]:
        raise ValueError("B2.15 mandatory fresh uniform failed")
    phases = attempt["timing"]
    return {
        "case_id": case.case_id, "method": "uniform", "seed": None,
        "succeeded": True, "failure_code": None, "fallback_used": False,
        "candidate": attempt["candidate"], "operational": attempt["candidate"],
        "matched_case_id": None,
        "uniform_reference_compliance": attempt["candidate"]["final_compliance"],
        "timing": {**phases, "end_to_end_seconds": sum(phases.values())},
        "paired_time_ratio": 1.0,
    }


def new_routed_result(
    case: ExperimentCase, reference: dict[str, Any],
    vector: dict[int, Any], context_models: dict[int, Any],
) -> dict[str, Any]:
    started = perf_counter()
    route = route_case(case)
    decision_seconds = perf_counter() - started
    if route == "uniform_reject":
        attempt = _attempt(case, method="uniform", reference_compliance=None)
        if not attempt["succeeded"]:
            raise ValueError("B2.15 rejected case's fresh uniform failed")
        operational = attempt["candidate"]
        reference_compliance = reference["uniform_reference_compliance"]
        if not math.isclose(
            operational["final_compliance"], reference_compliance, rel_tol=1e-9
        ):
            raise ValueError("B2.15 rejected uniform differs from matched reference")
        phases = {key: 0.0 for key in reference["timing"] if key != "end_to_end_seconds"}
        phases["decision_seconds"] = decision_seconds
        phases["rejection_uniform_seconds"] = sum(attempt["timing"].values())
        total = sum(phases.values())
        return {
            "case_id": case.case_id, "method": "new_routed", "seed": None,
            "route": route, "rejected": True, "succeeded": True,
            "failure_code": None, "failure_type": None, "fallback_used": False,
            "candidate": None, "operational": operational, "matched_case_id": None,
            "uniform_reference_compliance": reference_compliance,
            "timing": {**phases, "end_to_end_seconds": total},
            "paired_time_ratio": total / reference["timing"]["end_to_end_seconds"],
        }
    model = vector[29] if route == "vector_29" else context_models[
        17 if route == "context_17" else 43
    ]
    result = _charged_result(
        case, "candidate", None, reference, model=model, encoder=encode_vector_load_case
    )
    phases = result["timing"]
    phases["decision_seconds"] += decision_seconds
    phases["end_to_end_seconds"] += decision_seconds
    result["paired_time_ratio"] = (
        phases["end_to_end_seconds"] / reference["timing"]["end_to_end_seconds"]
    )
    result.update(method="new_routed", route=route, rejected=False)
    return result


def eligible_policies(
    means: dict[str, float], directions: dict[str, float], failures: Counter[str],
    quality_failures: Counter[str],
) -> list[str]:
    return [method for method in (*FIXED, "old_routed", "new_routed") if (
        quality_failures[method] == 0 and failures[method] <= MAX_FAILURES
        and all(means[f"{method}_{scale}"] <= 0.90 for scale in ("small", "large"))
        and all(directions[f"{method}_{scale}_{direction}"] <= 1.0
                for scale in ("small", "large") for direction in ("y", "z"))
    )]


def new_route_gate(
    means: dict[str, float], eligible: list[str], failures: Counter[str],
) -> bool:
    if "new_routed" not in eligible:
        return False
    fixed = min((method for method in FIXED if method in eligible),
                key=lambda method: (means[f"{method}_overall"], FIXED.index(method)),
                default=None)
    return (
        means["new_routed_overall"] < ROUTER_ADVANTAGE * means["old_routed_overall"]
        and (fixed is None or (
            means["new_routed_overall"] < ROUTER_ADVANTAGE * means[f"{fixed}_overall"]
            and failures["new_routed"] <= failures[fixed]
        ))
        and means["new_routed_overall"] < min(
            means["physics_heuristic_overall"], means["nearest_neighbor_overall"]
        )
    )


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    ratios: defaultdict[tuple[str, str], list[float]] = defaultdict(list)
    directions: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    overall: defaultdict[str, list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    fallbacks: Counter[str] = Counter()
    quality_failures: Counter[str] = Counter()
    phases: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in index["rows"]:
        case = row["case"]
        for item in row["outcomes"]:
            method, ratio = item["method"], item["paired_time_ratio"]
            ratios[(method, case["scale"])].append(ratio)
            directions[(method, case["scale"], case["direction"])].append(ratio)
            overall[method].append(ratio)
            failures[method] += not item["succeeded"]
            fallbacks[method] += item["fallback_used"]
            phases[method].update(item["timing"])
            if item["succeeded"] and (
                item["operational"]["final_compliance"]
                > 1.001 * item["uniform_reference_compliance"]
                or item["operational"]["physical_volume_error"] > 0.005
            ):
                quality_failures[method] += 1
    means = {
        **{f"{method}_{scale}": float(np.mean(values))
           for (method, scale), values in sorted(ratios.items())},
        **{f"{method}_overall": float(np.mean(values))
           for method, values in sorted(overall.items())},
    }
    direction_means = {
        f"{method}_{scale}_{direction}": float(np.mean(values))
        for (method, scale, direction), values in sorted(directions.items())
    }
    complete = len(index["rows"]) == CASE_COUNT and all(
        [item["method"] for item in row["outcomes"]] == list(METHODS)
        for row in index["rows"]
    )
    eligible = (eligible_policies(means, direction_means, failures, quality_failures)
                if complete else [])
    passed = (
        complete and sum(quality_failures.values()) == 0
        and index["elapsed_seconds"] <= SCREEN_CAP
        and index["peak_rss_bytes"] <= MAX_RSS
        and new_route_gate(means, eligible, failures)
    )
    return {
        "version": "topolab.b2_15.screen_summary.v1",
        "context": index["context"],
        "screen_index_sha256": sha256((root / "screen_index.json").read_bytes()),
        "cases": len(index["rows"]),
        "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
        "mean_time_ratios": means,
        "direction_mean_time_ratios": direction_means,
        "failure_counts": dict(sorted(failures.items())),
        "fallback_counts": dict(sorted(fallbacks.items())),
        "accepted_quality_failures": dict(sorted(quality_failures.items())),
        "route_rejections": {
            method: sum(item["rejected"] for row in index["rows"]
                        for item in row["outcomes"] if item["method"] == method)
            for method in ("old_routed", "new_routed")
        },
        "eligible_policies": eligible,
        "phase_seconds": {
            key: dict(sorted(value.items())) for key, value in sorted(phases.items())
        },
        "model_loading_seconds": index.get("model_loading_seconds", 0.0),
        "neighbor_loading_seconds": index.get("neighbor_loading_seconds", 0.0),
        "neighbor_bytes": index.get("neighbor_bytes", 0),
        "screen_seconds": index["elapsed_seconds"],
        "peak_rss_bytes": index["peak_rss_bytes"],
        "prototype_gate_passed": passed,
    }


def screen(
    root: Path, b29_root: Path, b212_root: Path, b213_root: Path, b214_root: Path,
    b24_root: Path, fresh: tuple[ExperimentCase, ...], context: dict[str, Any],
) -> dict[str, Any]:
    if sha256((b212_root / "screen_index.json").read_bytes()) != B212_SCREEN_INDEX_SHA256:
        raise ValueError("B2.12 exposed screen evidence differs")
    if sha256((b213_root / "screen_index.json").read_bytes()) != B213_SCREEN_INDEX_SHA256:
        raise ValueError("B2.13 exposed screen evidence differs")
    if sha256((b214_root / "screen_index.json").read_bytes()) != B214_SCREEN_INDEX_SHA256:
        raise ValueError("B2.14 exposed screen evidence differs")
    index = _index(root, "screen_index.json", context, CASE_COUNT)
    for position, row in enumerate(index["rows"]):
        if row["case"]["case_id"] != fresh[position].case_id or [
            item["method"] for item in row["outcomes"]
        ] != list(METHODS):
            raise ValueError("B2.15 persisted screen identity differs")
    if len(index["rows"]) == CASE_COUNT:
        return screen_summary(root, index)
    started, prior = perf_counter(), index["elapsed_seconds"]
    loaded = perf_counter()
    vector = _control_models(b29_root)
    if sha256((b212_root / "fit_index.json").read_bytes()) != B212_FIT_INDEX_SHA256:
        raise ValueError("B2.12 fixed fit index differs")
    fit = json.loads((b212_root / "fit_index.json").read_bytes())
    if [row["seed"] for row in fit["rows"]] != [17, 29, 43]:
        raise ValueError("B2.12 fixed seed order differs")
    context_models = {}
    for row in fit["rows"]:
        _read_selection(b212_root, row, fit["context"])
        context_models[row["seed"]] = _read_model(b212_root, row, fit["context"])
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
    for position in range(len(index["rows"]), CASE_COUNT):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.15 screen wall budget exhausted")
        case = fresh[position]
        case_started = perf_counter()
        nx, ny, nz = case.problem.mesh.element_counts
        reference = _uniform_result(case)
        outcomes = [reference]
        for method in ("physics_heuristic", "nearest_neighbor"):
            outcomes.append(_charged_result(
                case, method, None, reference,
                neighbors=neighbors[(nz, ny, nx)] if method == "nearest_neighbor" else None,
            ))
        for method, model in (
            ("vector_29", vector[29]),
            *((f"context_{seed}", context_models[seed]) for seed in (17, 43)),
        ):
            item = _charged_result(
                case, "candidate", None, reference, model=model,
                encoder=encode_vector_load_case,
            )
            item["method"] = method
            outcomes.append(item)
        old = old_routed_result(case, reference, vector, context_models)
        old["method"] = "old_routed"
        outcomes.append(old)
        outcomes.append(new_routed_result(case, reference, vector, context_models))
        if [item["method"] for item in outcomes] != list(METHODS):
            raise ValueError("B2.15 method order differs")
        index["rows"].append({
            "case": {
                "case_id": case.case_id,
                "scale": "small" if nx == 12 else "large",
                "direction": case.problem.loads[0].direction,
                "volume": case.problem.optimization.volume_fraction,
                "node": _point_node(case),
            },
            "outcomes": outcomes,
            "seconds": perf_counter() - case_started,
        })
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "screen_index.json", canonical_bytes(index))
        print(f"B2.15 screen {position + 1}/{CASE_COUNT}", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b29-root", type=Path, default=Path("/tmp/topolab-b29"))
    parser.add_argument("--b212-root", type=Path, default=Path("/tmp/topolab-b212"))
    parser.add_argument("--b213-root", type=Path, default=Path("/tmp/topolab-b213"))
    parser.add_argument("--b214-root", type=Path, default=Path("/tmp/topolab-b214"))
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--references", action="store_true")
    group.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    fresh, exposed = cohorts()
    plan = plan_payload(fresh, exposed)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.15 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b29_root = _external_root(repository, args.b29_root)
    b212_root = _external_root(repository, args.b212_root)
    b213_root = _external_root(repository, args.b213_root)
    b214_root = _external_root(repository, args.b214_root)
    b24_root = _external_root(repository, args.b24_root)
    if len({root, b29_root, b212_root, b213_root, b214_root, b24_root}) != 6:
        raise ValueError("B2.15 output and source roots must differ")
    context = {
        "plan_sha256": plan["plan_sha256"],
        "source_revision": revision,
        "runtime": runtime,
    }
    if not (args.references or args.screen):
        print(json.dumps({**plan, **context}, sort_keys=True))
        return 0
    if args.references:
        references = run_references(root, context, fresh)
        passed = reference_gate(references, fresh)
        print(json.dumps({
            "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
            "cases": len(references["rows"]),
            "passed": passed,
            "elapsed_seconds": references["elapsed_seconds"],
            "peak_rss_bytes": references["peak_rss_bytes"],
        }, sort_keys=True))
        return 0 if passed else 1
    references = _index(root, "reference_index.json", context, CASE_COUNT)
    if not reference_gate(references, fresh):
        raise ValueError("B2.15 complete quality-feasible uniform references required")
    screen_context = {
        **context,
        "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
        "b29_fit_index_sha256": B29_FIT_INDEX_SHA256,
        "b212_fit_index_sha256": B212_FIT_INDEX_SHA256,
            "b213_screen_index_sha256": B213_SCREEN_INDEX_SHA256,
            "b214_screen_index_sha256": B214_SCREEN_INDEX_SHA256,
    }
    summary = screen(
        root, b29_root, b212_root, b213_root, b214_root, b24_root, fresh,
        screen_context,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["prototype_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
