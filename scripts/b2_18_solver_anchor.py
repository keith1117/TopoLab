"""B2.18 frozen solver-anchored learned start and bounded quality screen."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter
from typing import Any

import numpy as np
from b2_5_prototype import atomic_write, canonical_bytes, sha256, source_snapshot
from b2_6_trajectory import _external_root, _small_case
from b2_7_global_load import _peak_rss
from b2_9_vector_load import _index
from b2_11_reference_budget import versioned_case
from b2_12_context_cnn import B29_FIT_INDEX_SHA256
from b2_13_routing import B212_FIT_INDEX_SHA256, routed_result
from b2_15_position_routing import _uniform_result
from b2_16_method_class import audited_records
from b2_17_early_reliability import (
    B214_REFERENCE_SHA256,
    B214_SCREEN_SHA256,
    B215_REFERENCE_SHA256,
    B215_SCREEN_SHA256,
    _models,
    _uniform_fallback,
)
from b2_17_early_reliability import cohorts as b217_cohorts
from b2_workload_pilot import scaled_case

from topolab.b2_5_evaluation import _attempt, _charged_result, _predict, _safe_metrics
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.baselines import validate_refinement_quality
from topolab.experiment import ExperimentCase, project_design_density
from topolab.problem import TopologyProblem, solve_problem

PLAN_VERSION = "topolab.b2_18.solver_anchor.v1"
EXPECTED_PLAN_SHA256 = "df4959622747da50937903480d4de06f94e8d23df409049ff145ca865270f21b"
ANCHOR_UPDATES = 2
LEARNED_WEIGHT = 0.5
VOLUMES = (0.5675, 0.5725)
LOAD_POSITIONS = ((1, 2), (5, 1))
SENTINEL_CAP = 600.0
REFERENCE_CAP = 900.0
SCREEN_CAP = 1_800.0
MAX_RSS = 2_147_483_648
OVERHEAD_CAP = 2.8101
METHODS = ("uniform", "context_17", "old_routed", "anchored")


def cohorts() -> tuple[tuple[ExperimentCase, ...], tuple[ExperimentCase, ...],
                       tuple[ExperimentCase, ...]]:
    reserved, exposed = b217_cohorts()
    blocked = {case.problem.optimization.volume_fraction for case in (*reserved, *exposed)}
    blocked.update(index / 100 for index in range(20, 61, 5))
    blocked.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & blocked:
        raise ValueError("B2.18 volume overlaps exposed or reserved evidence")
    selected = []
    for volume in VOLUMES:
        for y, z in LOAD_POSITIONS:
            small = _small_case(volume, "y", y, z)
            selected.append(versioned_case(scaled_case(small)))
    fresh = tuple(sorted(selected, key=lambda case: case.case_id))
    if (len(fresh) != 4 or len({case.case_id for case in fresh}) != 4
            or {case.case_id for case in fresh} &
            {case.case_id for case in (*reserved, *exposed)}
            or any(case.problem.mesh.element_counts != (24, 12, 6) for case in fresh)):
        raise ValueError("B2.18 fresh high-risk cohort differs")
    return fresh, exposed, reserved


def plan_payload(fresh: tuple[ExperimentCase, ...],
                 exposed: tuple[ExperimentCase, ...],
                 reserved: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    sentinel_ids = sorted(case.case_id for case in exposed if (
        case.problem.mesh.element_counts == (24, 12, 6)
        and case.problem.loads[0].direction == "y"
        and case.problem.optimization.volume_fraction in (0.5825, 0.5925)
    ))
    if len(sentinel_ids) != 4:
        raise ValueError("B2.18 sentinel case ledger differs")
    identity = {
        "version": PLAN_VERSION,
        "intervention": "two_uniform_updates_then_50_50_design_blend_with_projected_context17",
        "anchor_updates": ANCHOR_UPDATES,
        "learned_weight": LEARNED_WEIGHT,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 360,
        "source_hashes": {
            "b214_reference": B214_REFERENCE_SHA256,
            "b214_screen": B214_SCREEN_SHA256,
            "b215_reference": B215_REFERENCE_SHA256,
            "b215_screen": B215_SCREEN_SHA256,
            "b29_fit": B29_FIT_INDEX_SHA256,
            "b212_fit": B212_FIT_INDEX_SHA256,
        },
        "fresh_case_ids": [case.case_id for case in fresh],
        "sentinel_case_ids": sentinel_ids,
        "exposed_case_ids": [case.case_id for case in exposed],
        "b217_unopened_reserved_ids": [case.case_id for case in reserved],
        "fresh_volumes": VOLUMES,
        "fresh_positions_small": LOAD_POSITIONS,
        "methods": METHODS,
        "caps_seconds": {"sentinel": SENTINEL_CAP, "references": REFERENCE_CAP,
                         "screen": SCREEN_CAP},
        "max_rss_bytes": MAX_RSS,
        "per_query_pre_refinement_cap_seconds_strict": OVERHEAD_CAP,
        "sentinel_max_mean_paired_ratio": 1.0,
        "fresh_max_mean_paired_ratio_strict": 0.95,
        "fresh_max_individual_paired_ratio": 1.05,
        "quality_factor": 1.001,
        "volume_error_max": 0.005,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _two_update_problem(case: ExperimentCase) -> TopologyProblem:
    payload = case.problem.model_dump(mode="json")
    payload["optimization"]["max_iterations"] = ANCHOR_UPDATES
    payload["initial_density"] = None
    return TopologyProblem.model_validate(payload)


def anchored_result(case: ExperimentCase, reference: dict[str, Any],
                    model: Any) -> dict[str, Any]:
    """Pay for a uniform physical anchor, blend with a fixed learned prediction."""

    phases = dict.fromkeys(("setup_seconds", "projection_seconds", "anchor_seconds",
                            "refinement_seconds", "decision_seconds", "fallback_seconds"),
                           0.0)
    started = perf_counter()
    raw = _predict(case, model, encoder=encode_vector_load_case)
    phases["setup_seconds"] = perf_counter() - started
    started = perf_counter()
    learned = project_design_density(case, raw)
    phases["projection_seconds"] = perf_counter() - started
    started = perf_counter()
    shadow = solve_problem(_two_update_problem(case), termination_policy="physical_plateau")
    if len(shadow.history) != ANCHOR_UPDATES:
        raise ValueError("B2.18 physical anchor stopped before two updates")
    nx, ny, nz = case.problem.mesh.element_counts
    learned_field = learned.design_density.reshape((1, nz, ny, nx))
    uniform_field = np.asarray(shadow.design_density).reshape((1, nz, ny, nx))
    blend = np.asarray(LEARNED_WEIGHT * learned_field
                       + (1.0 - LEARNED_WEIGHT) * uniform_field, dtype=np.float64)
    projected = project_design_density(case, blend)
    phases["anchor_seconds"] = perf_counter() - started
    overhead = sum(phases.values())
    payload = case.problem.model_dump(mode="json")
    payload["initial_density"] = tuple(float(value) for value in projected.design_density)
    result = None
    failure_code = None
    started = perf_counter()
    try:
        result = solve_problem(TopologyProblem.model_validate(payload),
                               termination_policy="physical_plateau")
    except Exception:
        failure_code = "refinement_error"
    phases["refinement_seconds"] = perf_counter() - started
    candidate = None
    started = perf_counter()
    if result is not None:
        try:
            candidate = validate_refinement_quality(
                case, result, reference["uniform_reference_compliance"]
            ).model_dump(mode="json")
        except Exception:
            failure_code = "quality_error"
            candidate = _safe_metrics(case, result)
    phases["decision_seconds"] = perf_counter() - started
    succeeded = failure_code is None
    if succeeded:
        operational = candidate
    else:
        operational, phases["fallback_seconds"] = _uniform_fallback(case, reference)
    total = sum(phases.values())
    return {
        "case_id": case.case_id, "method": "anchored", "seed": 17,
        "succeeded": succeeded, "failure_code": failure_code,
        "fallback_used": not succeeded, "candidate": candidate,
        "operational": operational, "matched_case_id": None,
        "uniform_reference_compliance": reference["uniform_reference_compliance"],
        "anchor_updates": len(shadow.history), "learned_weight": LEARNED_WEIGHT,
        "pre_refinement_seconds": overhead,
        "timing": {**phases, "end_to_end_seconds": total},
        "paired_time_ratio": total / reference["timing"]["end_to_end_seconds"],
    }


def _sentinel_cases() -> tuple[tuple[ExperimentCase, bool], ...]:
    _, exposed, _ = cohorts()
    by_id = {case.case_id: case for case in exposed}
    rows = []
    for name in ("b214", "b215"):
        path = Path(f"/tmp/topolab-{name}")
        audited = audited_records(path, name)
        for cell, row in audited.items():
            if cell[:3] == ("large", "y", "high"):
                case_id = row["case"]["case_id"]
                rows.append((by_id[case_id], row["outcomes"]["context_17"]["succeeded"]))
    selected = tuple(sorted(rows, key=lambda item: item[0].case_id))
    if len(selected) != 4 or sum(success for _, success in selected) != 1:
        raise ValueError("B2.18 historical sentinel differs")
    return selected


def sentinel(root: Path, b29_root: Path, b212_root: Path,
             context: dict[str, Any]) -> dict[str, Any]:
    selected = _sentinel_cases()
    index = _index(root, "sentinel_index.json", context, 4)
    for row, (case, historical_success) in zip(index["rows"], selected, strict=False):
        if (row["case_id"] != case.case_id
                or row["historical_context17_success"] != historical_success):
            raise ValueError("B2.18 persisted sentinel identity differs")
    if len(index["rows"]) < 4:
        _, models = _models(b29_root, b212_root)
        started, prior = perf_counter(), index["elapsed_seconds"]
        for position in range(len(index["rows"]), 4):
            if prior + perf_counter() - started > SENTINEL_CAP:
                raise ValueError("B2.18 sentinel time cap exhausted")
            case, historical_success = selected[position]
            uniform = _uniform_result(case)
            anchored = anchored_result(case, uniform, models[17])
            index["rows"].append({"case_id": case.case_id,
                                  "historical_context17_success": historical_success,
                                  "uniform": uniform, "anchored": anchored})
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "sentinel_index.json", canonical_bytes(index))
            print(f"B2.18 sentinel {position + 1}/4", file=sys.stderr, flush=True)
    ratios = [row["anchored"]["paired_time_ratio"] for row in index["rows"]]
    failures = sum(not row["anchored"]["succeeded"] for row in index["rows"])
    over_budget = sum(row["anchored"]["pre_refinement_seconds"] >= OVERHEAD_CAP
                      for row in index["rows"])
    passed = (len(index["rows"]) == 4 and failures == over_budget == 0
              and float(np.mean(ratios)) <= 1.0
              and index["elapsed_seconds"] <= SENTINEL_CAP
              and index["peak_rss_bytes"] <= MAX_RSS)
    return {"passed": passed, "cases": len(index["rows"]),
            "failures": failures, "over_budget": over_budget,
            "mean_paired_ratio": float(np.mean(ratios)),
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"],
            "index_sha256": sha256((root / "sentinel_index.json").read_bytes())}


def reference_gate(index: dict[str, Any], fresh: tuple[ExperimentCase, ...]) -> bool:
    return (len(index["rows"]) == 4 and index["elapsed_seconds"] <= REFERENCE_CAP
            and index["peak_rss_bytes"] <= MAX_RSS and all(
                row["case_id"] == case.case_id and row["uniform"]["succeeded"]
                and row["uniform"]["candidate"]["physical_volume_error"] <= 0.005
                for row, case in zip(index["rows"], fresh, strict=True)))


def references(root: Path, context: dict[str, Any],
               fresh: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    index = _index(root, "reference_index.json", context, 4)
    for row, case in zip(index["rows"], fresh, strict=False):
        if row["case_id"] != case.case_id:
            raise ValueError("B2.18 persisted reference identity differs")
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 4):
        if prior + perf_counter() - started > REFERENCE_CAP:
            raise ValueError("B2.18 reference time cap exhausted")
        case = fresh[position]
        index["rows"].append({"case_id": case.case_id,
                              "uniform": _attempt(case, method="uniform",
                                                  reference_compliance=None)})
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "reference_index.json", canonical_bytes(index))
        print(f"B2.18 reference {position + 1}/4", file=sys.stderr, flush=True)
    return index


def screen(root: Path, b29_root: Path, b212_root: Path,
           fresh: tuple[ExperimentCase, ...], context: dict[str, Any]) -> dict[str, Any]:
    index = _index(root, "screen_index.json", context, 4)
    for row, case in zip(index["rows"], fresh, strict=False):
        if (row["case_id"] != case.case_id
                or tuple(item["method"] for item in row["outcomes"]) != METHODS):
            raise ValueError("B2.18 persisted screen identity differs")
    if len(index["rows"]) < 4:
        vector, models = _models(b29_root, b212_root)
        started, prior = perf_counter(), index["elapsed_seconds"]
        for position in range(len(index["rows"]), 4):
            if prior + perf_counter() - started > SCREEN_CAP:
                raise ValueError("B2.18 screen time cap exhausted")
            case = fresh[position]
            uniform = _uniform_result(case)
            fixed = _charged_result(case, "candidate", None, uniform, model=models[17],
                                    encoder=encode_vector_load_case)
            fixed["method"] = "context_17"
            old = routed_result(case, uniform, vector, models)
            old["method"] = "old_routed"
            anchored = anchored_result(case, uniform, models[17])
            outcomes = [uniform, fixed, old, anchored]
            index["rows"].append({"case_id": case.case_id, "volume":
                                  case.problem.optimization.volume_fraction,
                                  "node": case.problem.loads[0].node,
                                  "outcomes": outcomes})
            index["elapsed_seconds"] = prior + perf_counter() - started
            index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
            atomic_write(root / "screen_index.json", canonical_bytes(index))
            print(f"B2.18 screen {position + 1}/4", file=sys.stderr, flush=True)
    ratios = {method: [next(item["paired_time_ratio"] for item in row["outcomes"]
                            if item["method"] == method) for row in index["rows"]]
              for method in METHODS}
    means = {method: float(np.mean(values)) for method, values in ratios.items()}
    anchored = [row["outcomes"][-1] for row in index["rows"]]
    failures = sum(not item["succeeded"] for item in anchored)
    over_budget = sum(item["pre_refinement_seconds"] >= OVERHEAD_CAP
                      for item in anchored)
    complete = len(index["rows"]) == 4 and all(
        tuple(item["method"] for item in row["outcomes"]) == METHODS
        for row in index["rows"])
    quality = all(
        item["operational"]["physical_volume_error"] <= 0.005
        and item["operational"]["final_compliance"]
        <= 1.001 * row["outcomes"][0]["operational"]["final_compliance"]
        for row in index["rows"] for item in row["outcomes"])
    passed = (complete and quality and failures == over_budget == 0
              and means["anchored"] < 0.95 and max(ratios["anchored"]) <= 1.05
              and means["anchored"] < min(means["context_17"], means["old_routed"])
              and index["elapsed_seconds"] <= SCREEN_CAP
              and index["peak_rss_bytes"] <= MAX_RSS)
    return {"passed": passed, "cases": len(index["rows"]),
            "outcomes": sum(len(row["outcomes"]) for row in index["rows"]),
            "means": means, "ratios": ratios, "anchored_failures": failures,
            "over_budget": over_budget, "operational_quality_passed": quality,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"],
            "index_sha256": sha256((root / "screen_index.json").read_bytes())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b29-root", type=Path, default=Path("/tmp/topolab-b29"))
    parser.add_argument("--b212-root", type=Path, default=Path("/tmp/topolab-b212"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sentinel", action="store_true")
    group.add_argument("--references", action="store_true")
    group.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    fresh, exposed, reserved = cohorts()
    plan = plan_payload(fresh, exposed, reserved)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.18 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b29_root = _external_root(repository, args.b29_root)
    b212_root = _external_root(repository, args.b212_root)
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "runtime": runtime}
    if not (args.sentinel or args.references or args.screen):
        print(json.dumps({**plan, **context}, sort_keys=True))
        return 0
    sentinel_result = sentinel(root, b29_root, b212_root, context)
    if args.sentinel:
        print(json.dumps(sentinel_result, sort_keys=True))
        return 0 if sentinel_result["passed"] else 1
    if not sentinel_result["passed"]:
        raise ValueError("B2.18 sentinel failed; fresh evidence stays sealed")
    if args.references:
        ref = references(root, context, fresh)
        passed = reference_gate(ref, fresh)
        print(json.dumps({"passed": passed, "cases": len(ref["rows"]),
                          "index_sha256": sha256((root / "reference_index.json").read_bytes())},
                         sort_keys=True))
        return 0 if passed else 1
    ref = _index(root, "reference_index.json", context, 4)
    if not reference_gate(ref, fresh):
        raise ValueError("B2.18 uniform reference Gate failed")
    result = screen(root, b29_root, b212_root, fresh, {**context,
                    "reference_index_sha256": sha256(
                        (root / "reference_index.json").read_bytes())})
    print(json.dumps(result, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
