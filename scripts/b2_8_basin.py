"""B2.8 frozen y-load basin-recentering development screen."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

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
    _screen_summary,
    _small_case,
)
from b2_7_global_load import (
    _peak_rss,
)
from b2_7_global_load import (
    _read_model as read_b27_model,
)
from b2_7_global_load import (
    _read_selection as read_b27_selection,
)
from b2_7_global_load import (
    cohorts as b27_cohorts,
)
from b2_workload_pilot import scaled_case

from topolab.b2_5_evaluation import _charged_result, build_shape_neighbors
from topolab.b2_6_trajectory import SEEDS
from topolab.b2_7_conditioning import encode_global_load_case
from topolab.b2_8_basin import START_VERSION, recenter_y_start
from topolab.experiment import ExperimentCase

PLAN_VERSION = "topolab.b2_8.basin_recenter.v1"
EXPECTED_PLAN_SHA256 = "6b74219b8411da034e1794c2184efc84d07d9260160c6df625f73147c5c24357"
B27_FIT_INDEX_SHA256 = "36158e03a476fdff183d8c72cf0e7143700e7bac3ccc531d7eda485ec390a631"
VOLUMES = (0.2125, 0.3625, 0.5125)
SCREEN_CAP = 14_400.0
MAX_RSS = 2_147_483_648
METHODS = (
    "uniform", "physics_heuristic", "nearest_neighbor", "control_43",
    *(f"conditioned_{seed}" for seed in SEEDS),
    *(f"recentered_{seed}" for seed in SEEDS),
    "trajectory_oracle",
)


def cohorts() -> tuple[dict[str, tuple[ExperimentCase, ...]], tuple[ExperimentCase, ...]]:
    """Reuse B2.7 fits and freeze a physically disjoint complete screen."""

    old, prior_screen = b27_cohorts()
    exposed = {case.case_id for cases in old.values() for case in cases}
    exposed.update(case.case_id for case in prior_screen)
    historical_volumes = {
        *(index / 100 for index in range(20, 61, 5)),
        *(index / 1000 for index in range(225, 576, 50)),
        0.2375, 0.3875, 0.5375,
    }
    if set(VOLUMES).intersection(historical_volumes):
        raise ValueError("B2.8 volume overlaps the historical cohort")
    selected: list[ExperimentCase] = []
    for volume in VOLUMES:
        for direction in ("y", "z"):
            small = _small_case(volume, direction, 3, 2)
            selected.extend((small, scaled_case(small)))
    screen = tuple(sorted(selected, key=lambda case: case.case_id))
    ids = [case.case_id for case in screen]
    strata = Counter(
        (
            case.problem.mesh.element_counts,
            case.problem.loads[0].direction,
            case.problem.optimization.volume_fraction,
        )
        for case in screen
    )
    if len(ids) != 12 or len(set(ids)) != 12 or exposed.intersection(ids):
        raise ValueError("B2.8 screen overlaps prior development cases")
    if len(strata) != 12 or any(count != 1 for count in strata.values()):
        raise ValueError("B2.8 screen strata differ")
    return old, screen


def plan_payload(
    old: dict[str, tuple[ExperimentCase, ...]], screen: tuple[ExperimentCase, ...]
) -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "start_version": START_VERSION,
        "b27_fit_index_sha256": B27_FIT_INDEX_SHA256,
        "b25_fit_index_sha256": B25_FIT_SHA256,
        "b25_control43_checkpoint_sha256": B25_CONTROL43_SHA256,
        "solver_policy": "topolab.simp.physical_plateau.v1",
        "max_iterations": 240,
        "y_prediction_fraction": 0.5,
        "y_uniform_fraction": 0.5,
        "z_prediction_fraction": 1.0,
        "seeds": list(SEEDS),
        "train_case_ids": [case.case_id for case in old["train"]],
        "validation_case_ids": [case.case_id for case in old["validation"]],
        "prior_screen_case_ids": [case.case_id for case in (*old["screen"], *b27_cohorts()[1])],
        "screen_case_ids": [case.case_id for case in screen],
        "screen_volumes": list(VOLUMES),
        "screen_load_node_small": [12, 3, 2],
        "methods": list(METHODS),
        "screen_cap_seconds": SCREEN_CAP,
        "max_rss_bytes": MAX_RSS,
        "gate_two_scale_mean_max": 0.90,
        "gate_each_direction_mean_max": 1.0,
        "gate_required_seeds": 2,
    }
    return {**identity, "plan_sha256": sha256(canonical_bytes(identity))}


def _b27_models(root: Path) -> tuple[dict[int, Any], str]:
    contents = (root / "fit_index.json").read_bytes()
    if sha256(contents) != B27_FIT_INDEX_SHA256:
        raise ValueError("B2.7 fixed fit index differs")
    index = json.loads(contents)
    if [row["seed"] for row in index["rows"]] != list(SEEDS):
        raise ValueError("B2.7 fixed seed population differs")
    models = {}
    for row in index["rows"]:
        read_b27_selection(root, row, index["context"])
        models[row["seed"]] = read_b27_model(root, row, index["context"])
    return models, sha256(contents)


def _screen_index(root: Path, context: dict[str, Any]) -> dict[str, Any]:
    path = root / "screen_index.json"
    if not path.exists():
        return {"context": context, "rows": [], "elapsed_seconds": 0.0, "peak_rss_bytes": 0}
    index = json.loads(path.read_bytes())
    if index.get("context") != context or len(index.get("rows", [])) > 12:
        raise ValueError("B2.8 screen index context or population differs")
    return index


def screen_models(
    root: Path,
    b27_root: Path,
    b24_root: Path,
    b25_root: Path,
    screen: tuple[ExperimentCase, ...],
    context: dict[str, Any],
) -> dict[str, Any]:
    load_started = perf_counter()
    models, fit_sha = _b27_models(b27_root)
    if fit_sha != B27_FIT_INDEX_SHA256:
        raise ValueError("B2.7 fit source differs")
    index = _screen_index(root, context)
    for position, row in enumerate(index["rows"]):
        if (
            row["case"]["case_id"] != screen[position].case_id
            or [item["method"] for item in row["outcomes"]] != list(METHODS)
            or any(item["case_id"] != screen[position].case_id for item in row["outcomes"])
        ):
            raise ValueError("B2.8 persisted row identity or method order differs")
    started = perf_counter()
    prior = index["elapsed_seconds"]
    if len(index["rows"]) < 12:
        if sha256((b25_root / "fit_index.json").read_bytes()) != B25_FIT_SHA256:
            raise ValueError("B2.5 fixed fit index differs")
        b25 = json.loads((b25_root / "fit_index.json").read_bytes())
        audited = read_b25_fits(b25_root, b25["context"])
        control_row = next(
            row for row in audited["rows"] if (row["arm"], row["seed"]) == ("control", 43)
        )
        if control_row["checkpoint_sha256"] != B25_CONTROL43_SHA256:
            raise ValueError("B2.5 fixed control differs")
        control = read_b25_checkpoint(b25_root, control_row, audited["context"])
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
                raise ValueError("B2.8 screen wall budget exhausted")
            case = screen[position]
            case_started = perf_counter()
            nx, ny, nz = case.problem.mesh.element_counts
            outcomes, oracle = _case_outcomes(
                case, models, control, neighbors[(nz, ny, nx)],
                encoder=encode_global_load_case,
            )
            oracle_outcome = outcomes.pop()
            for item in outcomes:
                if item["method"].startswith("trajectory_"):
                    item["method"] = item["method"].replace("trajectory_", "conditioned_", 1)
            for seed in SEEDS:
                item = _charged_result(
                    case, "candidate", seed, outcomes[0], model=models[seed],
                    encoder=encode_global_load_case, raw_transform=recenter_y_start,
                )
                item["method"] = f"recentered_{seed}"
                outcomes.append(item)
            outcomes.append(oracle_outcome)
            if [item["method"] for item in outcomes] != list(METHODS):
                raise ValueError("B2.8 method order differs")
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
                f"B2.8 screen {position + 1}/12 {row['case']['scale']}",
                file=sys.stderr, flush=True,
            )
    index["elapsed_seconds"] = prior + perf_counter() - started
    index["peak_rss_bytes"] = max(index["peak_rss_bytes"], _peak_rss())
    atomic_write(root / "screen_index.json", canonical_bytes(index))
    return _screen_summary(
        root, index, learned_prefix="recentered_",
        summary_version="topolab.b2_8.screen_summary.v1",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--b27-root", type=Path, default=Path("/tmp/topolab-b27"))
    parser.add_argument("--b24-root", type=Path, default=Path("/tmp/topolab-b24-labels"))
    parser.add_argument("--b25-root", type=Path, default=Path("/tmp/topolab-b25"))
    parser.add_argument("--screen", action="store_true")
    args = parser.parse_args()
    old, screen = cohorts()
    plan = plan_payload(old, screen)
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.8 plan differs from its frozen identity")
    repository, revision, runtime = source_snapshot()
    root = _external_root(repository, args.output_root)
    b27_root = _external_root(repository, args.b27_root)
    if root == b27_root:
        raise ValueError("B2.8 output must differ from B2.7 source")
    context = {
        "plan_sha256": plan["plan_sha256"],
        "source_revision": revision,
        "runtime": runtime,
        "b27_fit_index_sha256": B27_FIT_INDEX_SHA256,
    }
    if not args.screen:
        print(json.dumps({**plan, **context}, sort_keys=True))
        return 0
    summary = screen_models(
        root, b27_root, args.b24_root.resolve(), args.b25_root.resolve(),
        screen, context,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["prototype_gate_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
