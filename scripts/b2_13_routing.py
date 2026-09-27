"""B2.13 frozen model routing and fresh development screen."""

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
from b2_6_trajectory import _case_outcomes, _external_root, _small_case
from b2_7_global_load import _peak_rss
from b2_9_vector_load import _index
from b2_11_reference_budget import versioned_case
from b2_12_context_cnn import (
    B25_CONTROL43_SHA256,
    B25_FIT_INDEX_SHA256,
    B29_FIT_INDEX_SHA256,
    _control_models,
    _read_model,
    _read_selection,
    reference_gate,
    run_references,
)
from b2_12_context_cnn import (
    cohorts as b212_cohorts,
)
from b2_workload_pilot import scaled_case

from topolab.b2_5_evaluation import _attempt, _charged_result, build_shape_neighbors
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b2_13_routing import route_case
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_13.routing.v1"
EXPECTED_PLAN_SHA256 = "8be542da851cdb6e45325ddd94a3cde8cf6867df8d13a2d4c6b49f484a9d9d37"
B212_FIT_INDEX_SHA256 = "0c8b6e7f9d64ec002cf28c5f48c19c5eecda50a581affa00ed93dc3615eee9ce"
B212_SCREEN_INDEX_SHA256 = "cb671b2e9b5194606964faed0c6022c4a9a181b978827f906bfe416f72516443"
VOLUMES = (0.3075, 0.4575, 0.6075)
REFERENCE_CAP = 1_800.0
SCREEN_CAP = 14_400.0
MAX_RSS = 2_147_483_648
METHODS = (
    "uniform", "physics_heuristic", "nearest_neighbor", "control_43",
    "vector_17", "vector_29", "vector_43",
    "context_17", "context_29", "context_43", "routed", "trajectory_oracle",
)


def cohorts() -> tuple[tuple[ExperimentCase, ...], tuple[ExperimentCase, ...]]:
    _, previous, prior_exposed = b212_cohorts()
    exposed = tuple(sorted({case.case_id: case for case in (
        *prior_exposed, *previous,
    )}.values(), key=lambda case: case.case_id))
    prior_volumes = {case.problem.optimization.volume_fraction for case in exposed}
    prior_volumes.update(index / 100 for index in range(20, 61, 5))
    prior_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & prior_volumes:
        raise ValueError("B2.13 screen volume intersects exposed development or final design")
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for direction in ("y", "z"):
            small = _small_case(volume, direction, 5, 1)
            selected.extend((versioned_case(small), versioned_case(scaled_case(small))))
    fresh = tuple(sorted(selected, key=lambda case: case.case_id))
    strata = Counter(
        (case.problem.mesh.element_counts, case.problem.loads[0].direction,
         case.problem.optimization.volume_fraction)
        for case in fresh
    )
    if (
        len(fresh) != 12 or len(strata) != 12
        or set(case.case_id for case in fresh) & set(case.case_id for case in exposed)
        or {route_case(case) for case in fresh}
        != {"vector_29", "context_17", "context_43", "uniform_reject"}
    ):
        raise ValueError("B2.13 screen population, identity, or routes differ")
    return fresh, exposed


def plan_payload(
    fresh: tuple[ExperimentCase, ...], exposed: tuple[ExperimentCase, ...]
) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 360,
        "b29_fit_index_sha256": B29_FIT_INDEX_SHA256,
        "b212_fit_index_sha256": B212_FIT_INDEX_SHA256,
        "b212_exposed_screen_index_sha256": B212_SCREEN_INDEX_SHA256,
        "b25_fit_index_sha256": B25_FIT_INDEX_SHA256,
        "b25_control43_checkpoint_sha256": B25_CONTROL43_SHA256,
        "routes": {case.case_id: route_case(case) for case in fresh},
        "screen_case_ids": [case.case_id for case in fresh],
        "exposed_case_ids": [case.case_id for case in exposed],
        "exposed_volumes": sorted(
            {case.problem.optimization.volume_fraction for case in exposed}
            | {index / 100 for index in range(20, 61, 5)}
            | {index / 1000 for index in range(225, 576, 50)}
        ),
        "screen_volumes": list(VOLUMES),
        "screen_load_node_small": [12, 5, 1],
        "methods": list(METHODS),
        "reference_cap_seconds": REFERENCE_CAP,
        "screen_cap_seconds": SCREEN_CAP,
        "max_rss_bytes": MAX_RSS,
        "gate_two_scale_mean_max": 0.90,
        "gate_each_direction_mean_max": 1.0,
        "high_volume_large_y_reject_at": 0.55,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def routed_result(
    case: ExperimentCase, reference: dict[str, Any],
    old_models: dict[int, Any], new_models: dict[int, Any],
) -> dict[str, Any]:
    started = perf_counter()
    route = route_case(case)
    decision_seconds = perf_counter() - started
    if route == "uniform_reject":
        attempt = _attempt(case, method="uniform", reference_compliance=None)
        if not attempt["succeeded"]:
            raise ValueError("B2.13 rejected case's fresh uniform failed")
        operational = attempt["candidate"]
        reference_compliance = reference["uniform_reference_compliance"]
        if not math.isclose(
            operational["final_compliance"], reference_compliance, rel_tol=1e-9
        ):
            raise ValueError("B2.13 rejected uniform differs from matched reference")
        phases = {key: 0.0 for key in reference["timing"] if key != "end_to_end_seconds"}
        phases["decision_seconds"] = decision_seconds
        phases["rejection_uniform_seconds"] = sum(attempt["timing"].values())
        total = sum(phases.values())
        return {
            "case_id": case.case_id, "method": "routed", "seed": None,
            "route": route, "rejected": True, "succeeded": True,
            "failure_code": None, "failure_type": None, "fallback_used": False,
            "candidate": None, "operational": operational, "matched_case_id": None,
            "uniform_reference_compliance": reference_compliance,
            "timing": {**phases, "end_to_end_seconds": total},
            "paired_time_ratio": total / reference["timing"]["end_to_end_seconds"],
        }
    model = old_models[29] if route == "vector_29" else new_models[
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
    result.update(method="routed", route=route, rejected=False)
    return result


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    ratios: defaultdict[tuple[str, str], list[float]] = defaultdict(list)
    directions: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    fallbacks: Counter[str] = Counter()
    phases: defaultdict[str, Counter[str]] = defaultdict(Counter)
    accepted_quality_failures = 0
    for row in index["rows"]:
        case = row["case"]
        for item in row["outcomes"]:
            method = item["method"]
            ratio = item["paired_time_ratio"]
            ratios[(method, case["scale"])].append(ratio)
            directions[(method, case["scale"], case["direction"])].append(ratio)
            failures[method] += not item["succeeded"]
            fallbacks[method] += item["fallback_used"]
            phases[method].update(item["timing"])
            if item["succeeded"] and (
                item["operational"]["final_compliance"]
                > 1.001 * item["uniform_reference_compliance"]
                or item["operational"]["physical_volume_error"] > 0.005
            ):
                accepted_quality_failures += 1
    means = {f"{method}_{scale}": float(np.mean(values))
             for (method, scale), values in sorted(ratios.items())}
    direction_means = {
        f"{method}_{scale}_{direction}": float(np.mean(values))
        for (method, scale, direction), values in sorted(directions.items())
    }
    complete = len(index["rows"]) == 12 and all(
        [item["method"] for item in row["outcomes"]] == list(METHODS)
        for row in index["rows"]
    )
    passed = (
        complete and accepted_quality_failures == 0
        and index["elapsed_seconds"] <= SCREEN_CAP
        and index["peak_rss_bytes"] <= MAX_RSS
        and all(
            means[f"routed_{scale}"] <= 0.90
            and all(direction_means[f"routed_{scale}_{direction}"] <= 1.0
                    for direction in ("y", "z"))
            for scale in ("small", "large")
        )
    )
    return {
        "version": "topolab.b2_13.screen_summary.v1",
        "context": index["context"],
        "screen_index_sha256": sha256((root / "screen_index.json").read_bytes()),
        "cases": len(index["rows"]),
        "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
        "mean_time_ratios": means,
        "direction_mean_time_ratios": direction_means,
        "failure_counts": dict(sorted(failures.items())),
        "fallback_counts": dict(sorted(fallbacks.items())),
        "routed_rejections": sum(row["outcomes"][-2]["rejected"] for row in index["rows"]),
        "phase_seconds": {
            key: dict(sorted(value.items())) for key, value in sorted(phases.items())
        },
        "accepted_quality_failures": accepted_quality_failures,
        "oracle_generation_seconds": sum(
            row["oracle"]["oracle_generation_seconds"] for row in index["rows"]
        ),
        "model_loading_seconds": index.get("model_loading_seconds", 0.0),
        "neighbor_loading_seconds": index.get("neighbor_loading_seconds", 0.0),
        "neighbor_bytes": index.get("neighbor_bytes", 0),
        "screen_seconds": index["elapsed_seconds"],
        "peak_rss_bytes": index["peak_rss_bytes"],
        "prototype_gate_passed": passed,
    }


def screen(
    root: Path, b29_root: Path, b212_root: Path, b24_root: Path, b25_root: Path,
    fresh: tuple[ExperimentCase, ...], context: dict[str, Any],
) -> dict[str, Any]:
    if sha256((b212_root / "screen_index.json").read_bytes()) != B212_SCREEN_INDEX_SHA256:
        raise ValueError("B2.12 exposed screen evidence differs")
    index = _index(root, "screen_index.json", context, 12)
    for position, row in enumerate(index["rows"]):
        if row["case"]["case_id"] != fresh[position].case_id or [
            item["method"] for item in row["outcomes"]
        ] != list(METHODS):
            raise ValueError("B2.13 persisted screen identity differs")
    if len(index["rows"]) == 12:
        return screen_summary(root, index)
    started, prior = perf_counter(), index["elapsed_seconds"]
    loaded = perf_counter()
    old_models = _control_models(b29_root)
    if sha256((b212_root / "fit_index.json").read_bytes()) != B212_FIT_INDEX_SHA256:
        raise ValueError("B2.12 fixed fit index differs")
    fit = json.loads((b212_root / "fit_index.json").read_bytes())
    if [row["seed"] for row in fit["rows"]] != [17, 29, 43]:
        raise ValueError("B2.12 fixed seed order differs")
    new_models = {}
    for row in fit["rows"]:
        _read_selection(b212_root, row, fit["context"])
        new_models[row["seed"]] = _read_model(b212_root, row, fit["context"])
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
            raise ValueError("B2.13 screen wall budget exhausted")
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
        for seed in (17, 29, 43):
            item = _charged_result(
                case, "candidate", seed, outcomes[0], model=new_models[seed],
                encoder=encode_vector_load_case,
            )
            item["method"] = f"context_{seed}"
            outcomes.append(item)
        outcomes.append(routed_result(case, outcomes[0], old_models, new_models))
        outcomes.append(oracle_outcome)
        if [item["method"] for item in outcomes] != list(METHODS):
            raise ValueError("B2.13 method order differs")
        index["rows"].append({
            "case": {
                "case_id": case.case_id,
                "scale": "small" if nx == 12 else "large",
                "direction": case.problem.loads[0].direction,
                "volume": case.problem.optimization.volume_fraction,
            },
            "outcomes": outcomes, "oracle": oracle,
            "seconds": perf_counter() - case_started,
        })
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "screen_index.json", canonical_bytes(index))
        print(f"B2.13 screen {position + 1}/12", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b29-root", type=Path, default=Path("/tmp/topolab-b29"))
    parser.add_argument("--b212-root", type=Path, default=Path("/tmp/topolab-b212"))
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b25-root", type=Path, default=Path("/tmp/topolab-b25"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--references", action="store_true")
    group.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    fresh, exposed = cohorts()
    plan = plan_payload(fresh, exposed)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.13 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b29_root = _external_root(repository, args.b29_root)
    b212_root = _external_root(repository, args.b212_root)
    if len({root, b29_root, b212_root}) != 3:
        raise ValueError("B2.13 output and fixed-model roots must differ")
    context = {
        "plan_sha256": plan["plan_sha256"], "source_revision": revision,
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
            "cases": len(references["rows"]), "passed": passed,
            "elapsed_seconds": references["elapsed_seconds"],
            "peak_rss_bytes": references["peak_rss_bytes"],
        }, sort_keys=True))
        return 0 if passed else 1
    references = _index(root, "reference_index.json", context, 12)
    if not reference_gate(references, fresh):
        raise ValueError("B2.13 complete quality-feasible uniform references required")
    screen_context = {
        **context,
        "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
        "b29_fit_index_sha256": B29_FIT_INDEX_SHA256,
        "b212_fit_index_sha256": B212_FIT_INDEX_SHA256,
    }
    summary = screen(
        root, b29_root, b212_root, args.b24_root.resolve(), args.b25_root.resolve(),
        fresh, screen_context,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["prototype_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
