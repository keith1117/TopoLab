"""Frozen B2.17 two-update online reliability probe and fresh development screen."""

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
from b2_13_routing import B212_FIT_INDEX_SHA256
from b2_13_routing import routed_result as old_routed_result
from b2_15_position_routing import (
    _point_node,
    _uniform_result,
    new_routed_result,
)
from b2_15_position_routing import (
    cohorts as b215_cohorts,
)
from b2_16_method_class import COHORTS, audited_records
from b2_workload_pilot import scaled_case

from topolab.b2_5_evaluation import (
    _attempt,
    _charged_result,
    _predict,
    _safe_metrics,
    build_shape_neighbors,
)
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.baselines import validate_refinement_quality
from topolab.experiment import ExperimentCase, project_design_density
from topolab.problem import TopologyProblem, solve_problem

PLAN_VERSION = "topolab.b2_17.early_reliability.v1"
EXPECTED_PLAN_SHA256 = "51c3ffd501435802298256acac05af28b95542408208989d68ea36df698d3d7e"
B215_REFERENCE_SHA256 = COHORTS["b215"]["reference_sha256"]
B215_SCREEN_SHA256 = COHORTS["b215"]["screen_sha256"]
B214_REFERENCE_SHA256 = COHORTS["b214"]["reference_sha256"]
B214_SCREEN_SHA256 = COHORTS["b214"]["screen_sha256"]
VOLUMES = (0.3225, 0.4725, 0.5775)
LOAD_POSITIONS = ((1, 2), (5, 1))
METHODS = (
    "uniform", "physics_heuristic", "nearest_neighbor", "vector_29",
    "context_17", "context_43", "old_routed", "new_routed", "probe_routed",
)
CASE_COUNT = 24
DIAGNOSTIC_UPDATES = 2
SIGNAL_LIMIT = 1.001
PER_QUERY_COST_CAP = 2.8101
SENTINEL_CAP = 600.0
REFERENCE_CAP = 3_600.0
SCREEN_CAP = 12_000.0
MAX_RSS = 2_147_483_648


class EarlyReject(RuntimeError):
    """Stop a learned solve after its observed second update."""


def _at_risk(case: ExperimentCase) -> bool:
    return (
        case.problem.mesh.element_counts == (24, 12, 6)
        and case.problem.loads[0].direction == "y"
        and case.problem.optimization.volume_fraction >= 0.55
    )


def cohorts() -> tuple[tuple[ExperimentCase, ...], tuple[ExperimentCase, ...]]:
    prior, earlier = b215_cohorts()
    exposed = tuple(sorted({case.case_id: case for case in (*prior, *earlier)}.values(),
                           key=lambda case: case.case_id))
    exposed_volumes = {case.problem.optimization.volume_fraction for case in exposed}
    exposed_volumes.update(index / 100 for index in range(20, 61, 5))
    exposed_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & exposed_volumes:
        raise ValueError("B2.17 volume intersects development or final design")
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for y, z in LOAD_POSITIONS:
            for direction in ("y", "z"):
                small = _small_case(volume, direction, y, z)
                selected.extend((versioned_case(small), versioned_case(scaled_case(small))))
    fresh = tuple(sorted(selected, key=lambda case: case.case_id))
    if (len(fresh) != CASE_COUNT or len({case.case_id for case in fresh}) != CASE_COUNT
            or {case.case_id for case in fresh} & {case.case_id for case in exposed}
            or sum(_at_risk(case) for case in fresh) != 2):
        raise ValueError("B2.17 fresh cohort differs")
    return fresh, exposed


def plan_payload(fresh: tuple[ExperimentCase, ...],
                 exposed: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "signal": "learned_compliance_at_update_2 / fresh_uniform_compliance_at_update_2",
        "signal_reject_if_greater_than": SIGNAL_LIMIT,
        "diagnostic_updates": DIAGNOSTIC_UPDATES,
        "at_risk": "large_y_volume_at_least_0.55",
        "at_risk_action": "context_17_on_both_positions",
        "other_action": "unchanged_b215_route",
        "per_query_diagnostic_cost_cap_seconds_strict": PER_QUERY_COST_CAP,
        "sentinel_source_hashes": {
            "b214_reference": B214_REFERENCE_SHA256,
            "b214_screen": B214_SCREEN_SHA256,
            "b215_reference": B215_REFERENCE_SHA256,
            "b215_screen": B215_SCREEN_SHA256,
        },
        "fit_hashes": {"b29": B29_FIT_INDEX_SHA256, "b212": B212_FIT_INDEX_SHA256},
        "fresh_case_ids": [case.case_id for case in fresh],
        "exposed_case_ids": [case.case_id for case in exposed],
        "volumes": VOLUMES,
        "positions_small": LOAD_POSITIONS,
        "methods": METHODS,
        "caps_seconds": {"sentinel": SENTINEL_CAP, "references": REFERENCE_CAP,
                         "screen": SCREEN_CAP},
        "max_rss_bytes": MAX_RSS,
        "scale_mean_max": 0.90,
        "direction_mean_max": 1.0,
        "max_failed_learned_attempts": 2,
        "probe_vs_old_and_new_multiplier": 0.95,
        "quality_factor": 1.001,
        "volume_error_max": 0.005,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _limited_problem(case: ExperimentCase) -> TopologyProblem:
    payload = case.problem.model_dump(mode="json")
    payload["optimization"]["max_iterations"] = DIAGNOSTIC_UPDATES
    payload["initial_density"] = None
    return TopologyProblem.model_validate(payload)


def _uniform_fallback(
    case: ExperimentCase, reference: dict[str, Any]
) -> tuple[dict[str, Any], float]:
    fallback = _attempt(case, method="uniform", reference_compliance=None)
    if not fallback["succeeded"]:
        raise ValueError("B2.17 mandatory fresh uniform fallback failed")
    operational = fallback["candidate"]
    if not math.isclose(operational["final_compliance"],
                        reference["uniform_reference_compliance"], rel_tol=1e-9):
        raise ValueError("B2.17 fallback differs from matched uniform")
    return operational, sum(fallback["timing"].values())


def probe_result(case: ExperimentCase, reference: dict[str, Any], model: Any) -> dict[str, Any]:
    """Charge a fresh two-update uniform shadow and one continuous learned solve."""

    timing = dict.fromkeys(("setup_seconds", "projection_seconds", "diagnostic_seconds",
                            "refinement_seconds", "decision_seconds", "fallback_seconds",
                            "rejection_uniform_seconds"), 0.0)
    start = perf_counter()
    raw = _predict(case, model, encoder=encode_vector_load_case)
    timing["setup_seconds"] = perf_counter() - start
    start = perf_counter()
    projected = project_design_density(case, raw)
    timing["projection_seconds"] = perf_counter() - start
    start = perf_counter()
    shadow = solve_problem(_limited_problem(case), termination_policy="physical_plateau")
    timing["diagnostic_seconds"] = perf_counter() - start
    if len(shadow.history) != DIAGNOSTIC_UPDATES:
        raise ValueError("B2.17 uniform shadow stopped before signal")
    uniform_early = shadow.history[-1].compliance
    signal: float | None = None
    candidate_early: float | None = None
    early_refinement_seconds: float | None = None
    learned_started = 0.0

    def check(state: Any) -> None:
        nonlocal signal, candidate_early, early_refinement_seconds
        if state.iteration == DIAGNOSTIC_UPDATES:
            candidate_early = state.compliance
            signal = candidate_early / uniform_early
            early_refinement_seconds = perf_counter() - learned_started
            if not math.isfinite(signal) or signal > SIGNAL_LIMIT:
                raise EarlyReject("B2.17 frozen early signal rejects")

    payload = case.problem.model_dump(mode="json")
    payload["initial_density"] = tuple(float(value) for value in projected.design_density)
    candidate = None
    rejection = False
    failure_code = None
    learned_started = perf_counter()
    try:
        result = solve_problem(TopologyProblem.model_validate(payload),
                               termination_policy="physical_plateau",
                               iteration_callback=check)
    except EarlyReject:
        rejection = True
        result = None
    except Exception:
        failure_code = "refinement_error"
        result = None
    timing["refinement_seconds"] = perf_counter() - learned_started
    decision_cost = (timing["setup_seconds"] + timing["projection_seconds"]
                     + timing["diagnostic_seconds"]
                     + (early_refinement_seconds or timing["refinement_seconds"]))
    if rejection:
        operational, timing["rejection_uniform_seconds"] = _uniform_fallback(case, reference)
        succeeded = True
    else:
        started = perf_counter()
        if result is not None:
            try:
                candidate = validate_refinement_quality(
                    case, result, reference["uniform_reference_compliance"]
                ).model_dump(mode="json")
            except Exception:
                failure_code = "quality_error"
                candidate = _safe_metrics(case, result)
        timing["decision_seconds"] = perf_counter() - started
        succeeded = failure_code is None
        if succeeded:
            operational = candidate
        else:
            operational, timing["fallback_seconds"] = _uniform_fallback(case, reference)
    total = sum(timing.values())
    return {
        "case_id": case.case_id, "method": "probe_routed", "seed": None,
        "route": "context_17_probe", "rejected": rejection,
        "succeeded": succeeded, "failure_code": failure_code,
        "fallback_used": not succeeded, "candidate": candidate,
        "operational": operational, "matched_case_id": None,
        "uniform_reference_compliance": reference["uniform_reference_compliance"],
        "signal": signal, "candidate_early_compliance": candidate_early,
        "uniform_early_compliance": uniform_early,
        "predecision_seconds": decision_cost,
        "timing": {**timing, "end_to_end_seconds": total},
        "paired_time_ratio": total / reference["timing"]["end_to_end_seconds"],
    }


def _models(b29_root: Path, b212_root: Path) -> tuple[dict[int, Any], dict[int, Any]]:
    vector = _control_models(b29_root)
    if sha256((b212_root / "fit_index.json").read_bytes()) != B212_FIT_INDEX_SHA256:
        raise ValueError("B2.17 context fit hash differs")
    fit = json.loads((b212_root / "fit_index.json").read_bytes())
    if [row["seed"] for row in fit["rows"]] != [17, 29, 43]:
        raise ValueError("B2.17 context seed order differs")
    context = {}
    for row in fit["rows"]:
        _read_selection(b212_root, row, fit["context"])
        context[row["seed"]] = _read_model(b212_root, row, fit["context"])
    return vector, context


def sentinel(root: Path, b214_root: Path, b215_root: Path,
             b29_root: Path, b212_root: Path, context: dict[str, Any]) -> dict[str, Any]:
    records = {name: audited_records(path, name) for name, path in
               (("b214", b214_root), ("b215", b215_root))}
    cases_by_id = {case.case_id: case for group in
                   (b215_cohorts()[0], b215_cohorts()[1]) for case in group}
    selected = sorted((row for group in records.values() for cell, row in group.items()
                       if cell[0] == "large" and cell[1] == "y" and cell[2] == "high"),
                      key=lambda row: row["case"]["case_id"])
    if len(selected) != 4:
        raise ValueError("B2.17 exposed sentinel count differs")
    index = _index(root, "sentinel_index.json", context, 4)
    if len(index["rows"]) < 4:
        _, models = _models(b29_root, b212_root)
        started, prior = perf_counter(), index["elapsed_seconds"]
        for position in range(len(index["rows"]), 4):
            if prior + perf_counter() - started > SENTINEL_CAP:
                raise ValueError("B2.17 sentinel budget exhausted")
            row = selected[position]
            case = cases_by_id[row["case"]["case_id"]]
            old = row["outcomes"]["context_17"]
            uniform = _uniform_result(case)
            outcome = probe_result(case, uniform, models[17])
            index["rows"].append({"case_id": case.case_id,
                                  "known_success": old["succeeded"],
                                  "uniform": uniform, "probe": outcome})
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "sentinel_index.json", canonical_bytes(index))
            print(f"B2.17 sentinel {position + 1}/4", file=sys.stderr, flush=True)
    false_rejections = sum(row["known_success"] and row["probe"]["rejected"]
                           for row in index["rows"])
    missed_failures = sum(not row["known_success"] and not row["probe"]["rejected"]
                          for row in index["rows"])
    over_budget = sum(row["probe"]["predecision_seconds"] >= PER_QUERY_COST_CAP
                      for row in index["rows"])
    passed = (len(index["rows"]) == 4 and false_rejections == 0
              and missed_failures == 0 and over_budget == 0
              and index["elapsed_seconds"] <= SENTINEL_CAP
              and index["peak_rss_bytes"] <= MAX_RSS)
    return {"passed": passed, "cases": len(index["rows"]),
            "false_rejections": false_rejections, "missed_failures": missed_failures,
            "over_budget": over_budget, "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"],
            "index_sha256": sha256((root / "sentinel_index.json").read_bytes())}


def reference_gate(index: dict[str, Any], fresh: tuple[ExperimentCase, ...]) -> bool:
    return (len(index["rows"]) == CASE_COUNT and index["elapsed_seconds"] <= REFERENCE_CAP
            and index["peak_rss_bytes"] <= MAX_RSS and all(
                row["case_id"] == case.case_id and row["uniform"]["succeeded"]
                and row["uniform"]["candidate"]["physical_volume_error"] <= 0.005
                for row, case in zip(index["rows"], fresh, strict=True)))


def run_references(root: Path, context: dict[str, Any],
                   fresh: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    index = _index(root, "reference_index.json", context, CASE_COUNT)
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), CASE_COUNT):
        if prior + perf_counter() - started > REFERENCE_CAP:
            raise ValueError("B2.17 reference budget exhausted")
        case = fresh[position]
        index["rows"].append({"case_id": case.case_id, "uniform": _attempt(
            case, method="uniform", reference_compliance=None)})
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "reference_index.json", canonical_bytes(index))
        print(f"B2.17 reference {position + 1}/{CASE_COUNT}", file=sys.stderr, flush=True)
    return index


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    ratios: defaultdict[tuple[str, str], list[float]] = defaultdict(list)
    directions: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    failures: Counter[str] = Counter()
    quality_violations: Counter[str] = Counter()
    false_rejections = missed_failures = over_budget = 0
    for row in index["rows"]:
        case = row["case"]
        outcomes = {item["method"]: item for item in row["outcomes"]}
        for method, item in outcomes.items():
            ratios[(method, case["scale"])].append(item["paired_time_ratio"])
            directions[(method, case["scale"], case["direction"])].append(
                item["paired_time_ratio"])
            failures[method] += not item["succeeded"]
            quality_violations[method] += (
                item["operational"]["physical_volume_error"] > 0.005
                or item["operational"]["final_compliance"]
                > 1.001 * outcomes["uniform"]["operational"]["final_compliance"]
            )
        if _at_risk_id(case):
            probe, fixed = outcomes["probe_routed"], outcomes["context_17"]
            false_rejections += bool(probe["rejected"] and fixed["succeeded"])
            missed_failures += bool(not probe["rejected"] and not fixed["succeeded"])
            over_budget += probe["predecision_seconds"] >= PER_QUERY_COST_CAP
    means = {f"{method}_{scale}": float(np.mean(values)) for
             (method, scale), values in ratios.items()}
    overall = {method: float(np.mean([item["paired_time_ratio"] for row in index["rows"]
                                      for item in row["outcomes"] if item["method"] == method]))
               for method in METHODS}
    directional = {f"{method}_{scale}_{direction}": float(np.mean(values)) for
                   (method, scale, direction), values in directions.items()}
    complete = len(index["rows"]) == CASE_COUNT and all(
        tuple(item["method"] for item in row["outcomes"]) == METHODS
        for row in index["rows"])
    probe = "probe_routed"
    passed = (complete and not sum(quality_violations.values())
              and index["elapsed_seconds"] <= SCREEN_CAP
              and index["peak_rss_bytes"] <= MAX_RSS
              and false_rejections == missed_failures == over_budget == 0
              and failures[probe] <= 2
              and all(means[f"{probe}_{scale}"] <= 0.90 for scale in ("small", "large"))
              and all(directional[f"{probe}_{scale}_{direction}"] <= 1.0
                      for scale in ("small", "large") for direction in ("y", "z"))
              and overall[probe] < 0.95 * min(overall["old_routed"],
                                               overall["new_routed"])
              and overall[probe] < min(overall["physics_heuristic"],
                                        overall["nearest_neighbor"]))
    return {"passed": passed, "cases": len(index["rows"]),
            "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
            "means": means, "overall": overall, "direction_means": directional,
            "failures": dict(failures), "quality_violations": dict(quality_violations),
            "false_rejections": false_rejections, "missed_failures": missed_failures,
            "over_budget": over_budget, "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"],
            "index_sha256": sha256((root / "screen_index.json").read_bytes())}


def _at_risk_id(case: dict[str, Any]) -> bool:
    return case["scale"] == "large" and case["direction"] == "y" and case["volume"] >= 0.55


def screen(root: Path, b29_root: Path, b212_root: Path, b24_root: Path,
           fresh: tuple[ExperimentCase, ...], context: dict[str, Any]) -> dict[str, Any]:
    index = _index(root, "screen_index.json", context, CASE_COUNT)
    if len(index["rows"]) == CASE_COUNT:
        return screen_summary(root, index)
    started, prior = perf_counter(), index["elapsed_seconds"]
    vector, models = _models(b29_root, b212_root)
    train_index = read_data_index(b24_root, b24_cases())
    neighbors = build_shape_neighbors(load_samples(b24_root, train_index, split="train"))
    for position in range(len(index["rows"]), CASE_COUNT):
        if prior + perf_counter() - started > SCREEN_CAP:
            raise ValueError("B2.17 screen budget exhausted")
        case = fresh[position]
        nx, ny, nz = case.problem.mesh.element_counts
        uniform = _uniform_result(case)
        outcomes = [uniform]
        for method in ("physics_heuristic", "nearest_neighbor"):
            outcomes.append(_charged_result(
                case, method, None, uniform,
                neighbors=neighbors[(nz, ny, nx)] if method == "nearest_neighbor" else None))
        for method, model in (("vector_29", vector[29]), ("context_17", models[17]),
                              ("context_43", models[43])):
            item = _charged_result(case, "candidate", None, uniform, model=model,
                                   encoder=encode_vector_load_case)
            item["method"] = method
            outcomes.append(item)
        old = old_routed_result(case, uniform, vector, models)
        old["method"] = "old_routed"
        outcomes.append(old)
        outcomes.append(new_routed_result(case, uniform, vector, models))
        if _at_risk(case):
            outcomes.append(probe_result(case, uniform, models[17]))
        else:
            unchanged = new_routed_result(case, uniform, vector, models)
            unchanged["method"] = "probe_routed"
            outcomes.append(unchanged)
        index["rows"].append({"case": {"case_id": case.case_id,
                                         "scale": "small" if nx == 12 else "large",
                                         "direction": case.problem.loads[0].direction,
                                         "volume": case.problem.optimization.volume_fraction,
                                         "node": _point_node(case)},
                              "outcomes": outcomes})
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "screen_index.json", canonical_bytes(index))
        print(f"B2.17 screen {position + 1}/{CASE_COUNT}", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b214-root", type=Path, default=Path("/tmp/topolab-b214"))
    parser.add_argument("--b215-root", type=Path, default=Path("/tmp/topolab-b215"))
    parser.add_argument("--b29-root", type=Path, default=Path("/tmp/topolab-b29"))
    parser.add_argument("--b212-root", type=Path, default=Path("/tmp/topolab-b212"))
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sentinel", action="store_true")
    group.add_argument("--references", action="store_true")
    group.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    fresh, exposed = cohorts()
    plan = plan_payload(fresh, exposed)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.17 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b214_root = _external_root(repository, args.b214_root)
    b215_root = _external_root(repository, args.b215_root)
    b29_root = _external_root(repository, args.b29_root)
    b212_root = _external_root(repository, args.b212_root)
    b24_root = _external_root(repository, args.b24_root)
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime}
    if not (args.sentinel or args.references or args.screen):
        print(json.dumps({**plan, **context}, sort_keys=True))
        return 0
    if args.sentinel:
        result = sentinel(root, b214_root, b215_root, b29_root, b212_root, context)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["passed"] else 1
    sentinel_index = _index(root, "sentinel_index.json", context, 4)
    if len(sentinel_index["rows"]) != 4:
        raise ValueError("B2.17 sentinel is incomplete")
    sentinel_result = sentinel(root, b214_root, b215_root, b29_root, b212_root, context)
    if not sentinel_result["passed"]:
        raise ValueError("B2.17 sentinel failed; fresh evidence stays sealed")
    if args.references:
        references = run_references(root, context, fresh)
        passed = reference_gate(references, fresh)
        print(json.dumps({"passed": passed, "cases": len(references["rows"]),
                          "index_sha256": sha256((root / "reference_index.json").read_bytes())},
                         sort_keys=True))
        return 0 if passed else 1
    references = _index(root, "reference_index.json", context, CASE_COUNT)
    if not reference_gate(references, fresh):
        raise ValueError("B2.17 uniform reference gate failed")
    screen_context = {**context, "reference_index_sha256": sha256(
        (root / "reference_index.json").read_bytes())}
    result = screen(root, b29_root, b212_root, b24_root, fresh, screen_context)
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
