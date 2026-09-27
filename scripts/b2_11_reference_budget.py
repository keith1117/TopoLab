"""B2.11 versioned reference budget, feasibility sentinels, and fixed-model screen."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

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
from b2_7_global_load import _peak_rss
from b2_7_global_load import cohorts as b27_cohorts
from b2_8_basin import cohorts as b28_cohorts
from b2_9_vector_load import _index
from b2_9_vector_load import _read_model as read_b29_model
from b2_9_vector_load import _read_selection as read_b29_selection
from b2_9_vector_load import cohorts as b29_cohorts
from b2_10_weighted_trajectory import _read_model as read_b210_model
from b2_10_weighted_trajectory import _read_selection as read_b210_selection
from b2_10_weighted_trajectory import cohorts as b210_cohorts
from b2_workload_pilot import scaled_case

from topolab.b2_5_evaluation import _attempt, _charged_result, build_shape_neighbors
from topolab.b2_6_trajectory import SEEDS
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.experiment import ExperimentCase
from topolab.problem import TopologyProblem

PLAN_VERSION = "topolab.b2_11.reference_budget.v1"
EXPECTED_PLAN_SHA256 = "8cbd77c8fdace2ef12512a6aa001e94152e2fc60b1fd9b4375d4c6f1e5af610a"
BUDGET = 360
VOLUMES = (0.2975, 0.4475, 0.5975)
OLD_FAILURE_ID = "tlcase-v1-dc08005b63bfbdbfe06e98ba9d377dfb38b5b51990d11dee0dff904f2c3157da"
B29_FIT_INDEX_SHA256 = "96dc550ac89e4bb661d06c384055bca5be1350781443000b6e0a61cfa80920b3"
B210_FIT_INDEX_SHA256 = "0d2138bfdcfc4f9d730c6261bccc1ce8bf2ddda2f50a70f5e5e0958b5fcc1851"
B25_FIT_INDEX_SHA256 = "a16d8c58cb5329de57f31df0063e46e97b024edef46cc0e7f157cd0e49fd1a53"
B25_CONTROL43_SHA256 = "d82b7895355c1f73cde5b80d6328bc31c43c58cd7b1580974a590ef42bce0f4d"
B210_PARTIAL_SCREEN_SHA256 = "a5a538f580e0ab03185e6d2c58d207a85f8c33ca7c77d7c5a56c0b196df6ceae"
SENTINEL_CAP = 1_800.0
REFERENCE_CAP = 1_800.0
SCREEN_CAP = 14_400.0
MAX_RSS = 2_147_483_648
METHODS = (
    "uniform", "physics_heuristic", "nearest_neighbor", "control_43",
    *(f"vector_{seed}" for seed in SEEDS),
    *(f"weighted_{seed}" for seed in SEEDS),
    "trajectory_oracle",
)


def versioned_case(source: ExperimentCase) -> ExperimentCase:
    """Change only the development iteration budget and thus the case identity."""

    payload = source.problem.model_dump(mode="json")
    if payload["optimization"]["max_iterations"] != 240:
        raise ValueError("B2.11 source must use the 240-update contract")
    payload["optimization"]["max_iterations"] = BUDGET
    return ExperimentCase.from_problem(TopologyProblem.model_validate(payload))


def cohorts() -> tuple[
    tuple[ExperimentCase, ...], tuple[ExperimentCase, ...],
    tuple[ExperimentCase, ...], tuple[ExperimentCase, ...],
]:
    """Keep the failed B2.10 cohort and freeze a physically new screen."""

    old, source = b210_cohorts()
    _, b27_screen = b27_cohorts()
    _, b28_screen = b28_cohorts()
    _, b29_screen = b29_cohorts()
    exposed = tuple(sorted(
        (*[case for group in old.values() for case in group],
         *b27_screen, *b28_screen, *b29_screen, *source),
        key=lambda case: case.case_id,
    ))
    prior_volumes = {case.problem.optimization.volume_fraction for case in exposed}
    prior_volumes.update(index / 100 for index in range(20, 61, 5))
    prior_volumes.update(index / 1000 for index in range(225, 576, 50))
    if set(VOLUMES) & prior_volumes:
        raise ValueError("B2.11 volume intersects development or final-design exposure")
    repaired = tuple(versioned_case(case) for case in source)
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for direction in ("y", "z"):
            small = _small_case(volume, direction, 3, 2)
            selected.extend((versioned_case(small), versioned_case(scaled_case(small))))
    fresh = tuple(sorted(selected, key=lambda case: case.case_id))
    strata = Counter(
        (case.problem.mesh.element_counts, case.problem.loads[0].direction,
         case.problem.optimization.volume_fraction)
        for case in fresh
    )
    if (
        len(source) != 12 or len(repaired) != 12 or len(fresh) != 12
        or len({case.case_id for case in (*repaired, *fresh)}) != 24
        or set(case.case_id for case in fresh) & set(case.case_id for case in exposed)
        or len(strata) != 12 or any(value != 1 for value in strata.values())
        or sum(case.case_id == OLD_FAILURE_ID for case in source) != 1
    ):
        raise ValueError("B2.11 source or fresh cohort differs")
    return source, repaired, fresh, exposed


def plan_payload(
    source: tuple[ExperimentCase, ...], repaired: tuple[ExperimentCase, ...],
    fresh: tuple[ExperimentCase, ...], exposed: tuple[ExperimentCase, ...],
) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "old_budget": 240, "new_budget": BUDGET,
        "source_case_ids": [case.case_id for case in source],
        "repaired_case_ids": [case.case_id for case in repaired],
        "screen_case_ids": [case.case_id for case in fresh],
        "exposed_case_ids": sorted({case.case_id for case in exposed}),
        "exposed_volumes": sorted({case.problem.optimization.volume_fraction for case in exposed}
                                  | {index / 100 for index in range(20, 61, 5)}
                                  | {index / 1000 for index in range(225, 576, 50)}),
        "screen_volumes": list(VOLUMES), "screen_load_node_small": [12, 3, 2],
        "old_failure_case_id": OLD_FAILURE_ID,
        "b29_fit_index_sha256": B29_FIT_INDEX_SHA256,
        "b210_fit_index_sha256": B210_FIT_INDEX_SHA256,
        "b25_fit_index_sha256": B25_FIT_INDEX_SHA256,
        "b25_control43_checkpoint_sha256": B25_CONTROL43_SHA256,
        "b210_partial_screen_sha256": B210_PARTIAL_SCREEN_SHA256,
        "methods": list(METHODS),
        "sentinel_cap_seconds": SENTINEL_CAP,
        "reference_cap_seconds": REFERENCE_CAP,
        "screen_cap_seconds": SCREEN_CAP,
        "max_rss_bytes": MAX_RSS,
        "gate_two_scale_mean_max": 0.90,
        "gate_each_direction_mean_max": 1.0,
        "gate_required_seeds_per_panel": 2,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _quality(attempt: dict[str, Any]) -> bool:
    candidate = attempt["candidate"]
    return (
        attempt["succeeded"] and candidate is not None
        and math.isfinite(candidate["final_compliance"])
        and candidate["final_compliance"] > 0
        and candidate["physical_volume_error"] <= 0.005
    )


def sentinel_gate(index: dict[str, Any], source: tuple[ExperimentCase, ...],
                  repaired: tuple[ExperimentCase, ...]) -> bool:
    if len(index["rows"]) != 12 or index["elapsed_seconds"] > SENTINEL_CAP or (
        index["peak_rss_bytes"] > MAX_RSS
    ):
        return False
    for row, old_case, new_case in zip(index["rows"], source, repaired, strict=True):
        if row["source_case_id"] != old_case.case_id or row["repaired_case_id"] != new_case.case_id:
            return False
        old, new = row["old_uniform"], row["new_uniform"]
        if not _quality(new):
            return False
        if old_case.case_id == OLD_FAILURE_ID:
            if (old["succeeded"] or old["failure_code"] != "quality_error"
                or old["failure_type"] != "_BaselineQualityError"
                or old["candidate"] is None or (
                old["candidate"]["iterations"] != 240
                or new["candidate"]["iterations"] <= 240
            )):
                return False
        elif (
            not _quality(old)
            or old["candidate"]["iterations"] != new["candidate"]["iterations"]
            or not math.isclose(old["candidate"]["final_compliance"],
                                new["candidate"]["final_compliance"], rel_tol=1e-10)
        ):
            return False
    return True


def run_sentinel(root: Path, context: dict[str, Any],
                 source: tuple[ExperimentCase, ...],
                 repaired: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    index: dict[str, Any] = _index(root, "sentinel_index.json", context, 12)
    for position, row in enumerate(index["rows"]):
        if (row["source_case_id"], row["repaired_case_id"]) != (
            source[position].case_id, repaired[position].case_id
        ):
            raise ValueError("B2.11 persisted sentinel identity differs")
    if len(index["rows"]) == 12:
        return index
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 12):
        if prior + perf_counter() - started > SENTINEL_CAP:
            raise ValueError("B2.11 sentinel wall budget exhausted")
        old_case, new_case = source[position], repaired[position]
        row = {
            "source_case_id": old_case.case_id,
            "repaired_case_id": new_case.case_id,
            "old_uniform": _attempt(old_case, method="uniform", reference_compliance=None),
            "new_uniform": _attempt(new_case, method="uniform", reference_compliance=None),
        }
        index["rows"].append(row)
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "sentinel_index.json", canonical_bytes(index))
        print(f"B2.11 sentinel {position + 1}/12", file=sys.stderr, flush=True)
    return index


def reference_gate(index: dict[str, Any], fresh: tuple[ExperimentCase, ...]) -> bool:
    return (
        len(index["rows"]) == 12
        and index["elapsed_seconds"] <= REFERENCE_CAP
        and index["peak_rss_bytes"] <= MAX_RSS
        and all(row["case_id"] == case.case_id and _quality(row["uniform"])
                for row, case in zip(index["rows"], fresh, strict=True))
    )


def run_references(root: Path, context: dict[str, Any],
                   fresh: tuple[ExperimentCase, ...]) -> dict[str, Any]:
    index: dict[str, Any] = _index(root, "reference_index.json", context, 12)
    for position, row in enumerate(index["rows"]):
        if row["case_id"] != fresh[position].case_id:
            raise ValueError("B2.11 persisted reference identity differs")
    if len(index["rows"]) == 12:
        return index
    started, prior = perf_counter(), index["elapsed_seconds"]
    for position in range(len(index["rows"]), 12):
        if prior + perf_counter() - started > REFERENCE_CAP:
            raise ValueError("B2.11 reference wall budget exhausted")
        case = fresh[position]
        row = {
            "case_id": case.case_id,
            "scale": "small" if case.problem.mesh.element_counts[0] == 12 else "large",
            "direction": case.problem.loads[0].direction,
            "volume": case.problem.optimization.volume_fraction,
            "uniform": _attempt(case, method="uniform", reference_compliance=None),
        }
        index["rows"].append(row)
        index["elapsed_seconds"] = prior + perf_counter() - started
        index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
        atomic_write(root / "reference_index.json", canonical_bytes(index))
        print(f"B2.11 reference {position + 1}/12", file=sys.stderr, flush=True)
    return index


def screen_models(root: Path, context: dict[str, Any], fresh: tuple[ExperimentCase, ...],
                  b29_root: Path, b210_root: Path, b24_root: Path,
                  b25_root: Path) -> dict[str, Any]:
    index = _index(root, "screen_index.json", context, 12)
    for position, row in enumerate(index["rows"]):
        if row["case"]["case_id"] != fresh[position].case_id or [
            item["method"] for item in row["outcomes"]
        ] != list(METHODS):
            raise ValueError("B2.11 persisted screen identity differs")
    if len(index["rows"]) == 12:
        return screen_summary(root, index)
    started, prior = perf_counter(), index["elapsed_seconds"]
    loaded = perf_counter()
    if sha256((b29_root / "fit_index.json").read_bytes()) != B29_FIT_INDEX_SHA256:
        raise ValueError("B2.9 fixed fit index differs")
    if sha256((b210_root / "fit_index.json").read_bytes()) != B210_FIT_INDEX_SHA256:
        raise ValueError("B2.10 fixed fit index differs")
    if sha256((b210_root / "screen_index.json").read_bytes()) != B210_PARTIAL_SCREEN_SHA256:
        raise ValueError("B2.10 failed screen provenance differs")
    old_fit = json.loads((b29_root / "fit_index.json").read_bytes())
    weighted_fit = json.loads((b210_root / "fit_index.json").read_bytes())
    old_models = {}
    weighted_models = {}
    for row in old_fit["rows"]:
        read_b29_selection(b29_root, row, old_fit["context"])
        old_models[row["seed"]] = read_b29_model(b29_root, row, old_fit["context"])
    for row in weighted_fit["rows"]:
        read_b210_selection(b210_root, row, weighted_fit["context"])
        weighted_models[row["seed"]] = read_b210_model(
            b210_root, row, weighted_fit["context"]
        )
    if set(old_models) != set(SEEDS) or set(weighted_models) != set(SEEDS):
        raise ValueError("B2.11 requires every fixed model seed")
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
            raise ValueError("B2.11 screen wall budget exhausted")
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
                case, "candidate", seed, outcomes[0], model=weighted_models[seed],
                encoder=encode_vector_load_case,
            )
            item["method"] = f"weighted_{seed}"
            outcomes.append(item)
        outcomes.append(oracle_outcome)
        if [item["method"] for item in outcomes] != list(METHODS):
            raise ValueError("B2.11 method order differs")
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
        print(f"B2.11 screen {position + 1}/12", file=sys.stderr, flush=True)
    return screen_summary(root, index)


def screen_summary(root: Path, index: dict[str, Any]) -> dict[str, Any]:
    vector = _screen_summary(
        root, index, learned_prefix="vector_",
        summary_version="topolab.b2_11.vector_screen.v1",
    )
    weighted = _screen_summary(
        root, index, learned_prefix="weighted_",
        summary_version="topolab.b2_11.weighted_screen.v1",
    )
    return {
        **weighted,
        "version": "topolab.b2_11.screen_summary.v1",
        "vector_passing_seeds": vector["passing_seeds"],
        "weighted_passing_seeds": weighted["passing_seeds"],
        "passing_panel": (
            "vector" if vector["prototype_gate_passed"] else
            "weighted" if weighted["prototype_gate_passed"] else None
        ),
        "prototype_gate_passed": (
            vector["prototype_gate_passed"] or weighted["prototype_gate_passed"]
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b29-root", type=Path, default=Path("/tmp/topolab-b29"))
    parser.add_argument("--b210-root", type=Path, default=Path("/tmp/topolab-b210"))
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b25-root", type=Path, default=Path("/tmp/topolab-b25"))
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--sentinel", action="store_true")
    group.add_argument("--references", action="store_true")
    group.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    source, repaired, fresh, exposed = cohorts()
    plan = plan_payload(source, repaired, fresh, exposed)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.11 plan differs from frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b29_root = _external_root(repository, args.b29_root)
    b210_root = _external_root(repository, args.b210_root)
    if len({root, b29_root, b210_root}) != 3:
        raise ValueError("B2.11 output and model roots must differ")
    context = {
        "plan_sha256": plan["plan_sha256"],
        "source_revision": revision,
        "runtime": runtime,
    }
    if not (args.sentinel or args.references or args.screen):
        print(json.dumps({**plan, **context}, sort_keys=True))
        return 0
    if args.sentinel:
        index = run_sentinel(root, context, source, repaired)
        passed = sentinel_gate(index, source, repaired)
        print(json.dumps({
            "sentinel_index_sha256": sha256((root / "sentinel_index.json").read_bytes()),
            "cases": len(index["rows"]), "passed": passed,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"],
        }, sort_keys=True))
        return 0 if passed else 1
    sentinel = _index(root, "sentinel_index.json", context, 12)
    if not sentinel_gate(sentinel, source, repaired):
        raise ValueError("B2.11 complete reference-repair sentinel required")
    reference_context = {
        **context, "sentinel_index_sha256": sha256((root / "sentinel_index.json").read_bytes()),
    }
    if args.references:
        index = run_references(root, reference_context, fresh)
        passed = reference_gate(index, fresh)
        print(json.dumps({
            "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
            "cases": len(index["rows"]), "passed": passed,
            "elapsed_seconds": index["elapsed_seconds"],
            "peak_rss_bytes": index["peak_rss_bytes"],
        }, sort_keys=True))
        return 0 if passed else 1
    references = _index(root, "reference_index.json", reference_context, 12)
    if not reference_gate(references, fresh):
        raise ValueError("B2.11 complete fresh reference-feasibility Gate required")
    screen_context = {
        **reference_context,
        "reference_index_sha256": sha256((root / "reference_index.json").read_bytes()),
        "b29_fit_index_sha256": B29_FIT_INDEX_SHA256,
        "b210_fit_index_sha256": B210_FIT_INDEX_SHA256,
    }
    summary = screen_models(
        root, screen_context, fresh, b29_root, b210_root,
        args.b24_root.resolve(), args.b25_root.resolve(),
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["prototype_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
