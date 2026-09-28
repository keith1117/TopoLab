"""B2.16 bounded, read-only reassessment of audited warm-start outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import resource
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any

PLAN_VERSION = "topolab.b2_16.method_class.v1"
EXPECTED_PLAN_SHA256 = "fa1370508e5a94650b80e6f1b3170699072625abc39b88287d498104e04f1c03"
COMMON_ACTIONS = ("uniform", "vector_29", "context_17", "context_43")
SCALES = ("small", "large")
DIRECTIONS = ("y", "z")
VOLUME_TIERS = ("low", "middle", "high")
POSITIONS = ("lower_z", "upper_z")
SCALE_MEAN_MAX = 0.90
DIRECTION_MEAN_MAX = 1.0
MAX_FAILURES = 2
OLD_ROUTE_MULTIPLIER = 0.95
COHORTS: dict[str, dict[str, Any]] = {
    "b214": {
        "source_revision": "884a3371c8aa919f96b4db27018b5066677bbf69",
        "plan_sha256": "236ceafce97fad8282b32b0c7f5def38954d22b302a761aeb64196197dad3673",
        "reference_sha256": "b44c98573d50b1e9c26b5a8ff3bf42ebe211197455c88d5f65f2a01f941a010e",
        "screen_sha256": "2c2bb58c40bf1e2099fd21ecf3cc74a5425ca3f1ad28ac183611c1535bb4e6c9",
        "volumes": (0.3125, 0.4625, 0.5925),
        "positions_small": ((3, 1), (5, 2)),
        "methods": (
            "uniform", "physics_heuristic", "nearest_neighbor", "vector_29",
            "context_17", "context_29", "context_43", "routed",
        ),
        "old_route": "routed",
    },
    "b215": {
        "source_revision": "c70a0d92d26bda3df1da0168c135404493df8c3b",
        "plan_sha256": "edeab8ca4cc1f059984ebbe84917991e9aef76fffd8ac47e226cbd8965c3b8b8",
        "reference_sha256": "1e21d3f2a4ac21522c76911a12640ba551bf4f7939b72121c19fdb6b1146f998",
        "screen_sha256": "2bcf6d313257d85f13199241f0cc603203596e062a2429012f371d0c7e5c36b0",
        "volumes": (0.3175, 0.4675, 0.5825),
        "positions_small": ((2, 1), (4, 2)),
        "methods": (
            "uniform", "physics_heuristic", "nearest_neighbor", "vector_29",
            "context_17", "context_43", "old_routed", "new_routed",
        ),
        "old_route": "old_routed",
    },
}

type Cell = tuple[str, str, str, str]
type Records = dict[Cell, dict[str, Any]]


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan_payload() -> dict[str, Any]:
    identity = {
        "version": PLAN_VERSION,
        "cohorts": COHORTS,
        "common_actions": COMMON_ACTIONS,
        "cell_axes": (SCALES, DIRECTIONS, VOLUME_TIERS, POSITIONS),
        "gate_scale_mean_max": SCALE_MEAN_MAX,
        "gate_direction_mean_max": DIRECTION_MEAN_MAX,
        "gate_max_failed_attempts": MAX_FAILURES,
        "b215_old_route_multiplier": OLD_ROUTE_MULTIPLIER,
        "rescue_method": "replace_failed_b215_new_route_with_zero_cost_uniform",
        "pilot_scope": "b215_high_volume_large_y_two_positions",
        "transfer": "best_successful_common_action_per_training_cell_then_apply_to_other_cohort",
        "resource_cap_seconds": 60.0,
        "resource_cap_bytes": 1_073_741_824,
    }
    return {**identity, "plan_sha256": hashlib.sha256(canonical_bytes(identity)).hexdigest()}


def source_snapshot() -> tuple[Path, str]:
    repository = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()).resolve()
    for command in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"]):
        if subprocess.run(command, cwd=repository, check=False).returncode:
            raise ValueError("B2.16 requires a clean tracked revision")
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    return repository, revision


def external_root(repository: Path, path: Path) -> Path:
    root = path.resolve()
    if root == repository or root.is_relative_to(repository):
        raise ValueError("B2.16 generated artifacts must stay outside Git")
    return root


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-8, abs_tol=1e-8)


def case_cell(case: dict[str, Any], specification: dict[str, Any]) -> Cell:
    scale, direction, volume = case["scale"], case["direction"], case["volume"]
    if scale not in SCALES or direction not in DIRECTIONS:
        raise ValueError("B2.16 unexpected scale or direction")
    volumes = specification["volumes"]
    if volume not in volumes:
        raise ValueError("B2.16 unexpected development volume")
    tier = VOLUME_TIERS[volumes.index(volume)]
    nx, ny, nz = (12, 6, 3) if scale == "small" else (24, 12, 6)
    node = case["node"]
    x = node % (nx + 1)
    y = node // (nx + 1) % (ny + 1)
    z = node // ((nx + 1) * (ny + 1))
    factor = 1 if scale == "small" else 2
    positions = tuple((factor * py, factor * pz) for py, pz in specification["positions_small"])
    if x != nx or (y, z) not in positions:
        raise ValueError("B2.16 unexpected physical load position")
    return scale, direction, tier, POSITIONS[positions.index((y, z))]


def audited_records(root: Path, name: str) -> Records:
    specification = COHORTS[name]
    reference_path, screen_path = root / "reference_index.json", root / "screen_index.json"
    if sha256(reference_path) != specification["reference_sha256"]:
        raise ValueError(f"{name} reference digest differs")
    if sha256(screen_path) != specification["screen_sha256"]:
        raise ValueError(f"{name} screen digest differs")
    references = json.loads(reference_path.read_bytes())
    screen = json.loads(screen_path.read_bytes())
    expected = {key: specification[key] for key in ("source_revision", "plan_sha256")}
    for index in (references, screen):
        if any(index["context"][key] != value for key, value in expected.items()):
            raise ValueError(f"{name} frozen source context differs")
    if screen["context"]["reference_index_sha256"] != specification["reference_sha256"]:
        raise ValueError(f"{name} screen-to-reference identity differs")
    if len(references["rows"]) != 24 or len(screen["rows"]) != 24:
        raise ValueError(f"{name} incomplete case population")
    records: Records = {}
    for reference, row in zip(references["rows"], screen["rows"], strict=True):
        case = row["case"]
        if any(case[key] != reference[key] for key in (
            "case_id", "scale", "direction", "volume", "node"
        )) or not reference["uniform"]["succeeded"]:
            raise ValueError(f"{name} reference and screen differ")
        ref_candidate = reference["uniform"]["candidate"]
        if (ref_candidate is None or not math.isfinite(ref_candidate["final_compliance"])
                or ref_candidate["final_compliance"] <= 0
                or ref_candidate["physical_volume_error"] > 0.005):
            raise ValueError(f"{name} invalid uniform reference")
        outcomes = row["outcomes"]
        if tuple(item["method"] for item in outcomes) != specification["methods"]:
            raise ValueError(f"{name} method order differs")
        uniform = outcomes[0]
        denominator = uniform["timing"]["end_to_end_seconds"]
        compliance = uniform["operational"]["final_compliance"]
        if not uniform["succeeded"] or denominator <= 0 or not close(
            uniform["paired_time_ratio"], 1.0
        ):
            raise ValueError(f"{name} invalid fresh uniform denominator")
        for item in outcomes:
            timing = item["timing"]
            total = timing["end_to_end_seconds"]
            if (
                item["case_id"] != case["case_id"]
                or any(not math.isfinite(value) or value < 0 for value in timing.values())
                or not close(total, sum(value for key, value in timing.items()
                                        if key != "end_to_end_seconds"))
                or not close(item["paired_time_ratio"], total / denominator)
                or not close(item["uniform_reference_compliance"], compliance)
                or item["fallback_used"] != (not item["succeeded"])
                or item["operational"]["physical_volume_error"] > 0.005
                or item["operational"]["final_compliance"] > 1.001 * compliance
            ):
                raise ValueError(f"{name} invalid charged outcome")
        cell = case_cell(case, specification)
        if cell in records:
            raise ValueError(f"{name} duplicate workload cell")
        records[cell] = {"case": case, "outcomes": {item["method"]: item for item in outcomes}}
    if len(records) != 24:
        raise ValueError(f"{name} incomplete workload cells")
    return records


def best_successful_action(row: dict[str, Any]) -> str:
    outcomes = row["outcomes"]
    return min(
        (method for method in COMMON_ACTIONS if outcomes[method]["succeeded"]),
        key=lambda method: (outcomes[method]["paired_time_ratio"], COMMON_ACTIONS.index(method)),
    )


def metrics(records: Records, choices: dict[Cell, str]) -> dict[str, Any]:
    scale_ratios: defaultdict[str, list[float]] = defaultdict(list)
    direction_ratios: defaultdict[str, list[float]] = defaultdict(list)
    all_ratios: list[float] = []
    comparator_ratios: defaultdict[str, list[float]] = defaultdict(list)
    failures = 0
    for cell, row in sorted(records.items()):
        method = choices[cell]
        item = row["outcomes"][method]
        ratio = item["paired_time_ratio"]
        all_ratios.append(ratio)
        scale_ratios[cell[0]].append(ratio)
        direction_ratios[f"{cell[0]}_{cell[1]}"].append(ratio)
        failures += not item["succeeded"]
        for comparator in ("physics_heuristic", "nearest_neighbor"):
            comparator_ratios[comparator].append(
                row["outcomes"][comparator]["paired_time_ratio"]
            )
    scale = {key: statistics.fmean(values) for key, values in scale_ratios.items()}
    direction = {key: statistics.fmean(values) for key, values in direction_ratios.items()}
    overall = statistics.fmean(all_ratios)
    comparators = {
        key: statistics.fmean(values) for key, values in comparator_ratios.items()
    }
    return {
        "overall": overall, "scale": scale, "direction": direction,
        "failures": failures, "comparators": comparators,
        "gate_passed": (
            failures <= MAX_FAILURES
            and all(scale[key] <= SCALE_MEAN_MAX for key in SCALES)
            and all(direction[f"{scale}_{direction_name}"] <= DIRECTION_MEAN_MAX
                    for scale in SCALES for direction_name in DIRECTIONS)
            and all(overall < value for value in comparators.values())
        ),
    }


def ideal_rescue(records: Records) -> dict[str, Any]:
    old = {cell: "old_routed" for cell in records}
    old_metrics = metrics(records, old)
    ratios: dict[Cell, float] = {}
    rescued_cells: list[Cell] = []
    for cell, row in records.items():
        new = row["outcomes"]["new_routed"]
        if not new["succeeded"]:
            rescued_cells.append(cell)
        ratios[cell] = 1.0 if not new["succeeded"] else new["paired_time_ratio"]
    if not rescued_cells:
        raise ValueError("B2.16 expected the recorded B2.15 failed attempt")
    small = statistics.fmean(ratio for cell, ratio in ratios.items() if cell[0] == "small")
    large = statistics.fmean(ratio for cell, ratio in ratios.items() if cell[0] == "large")
    direction = {
        f"{scale}_{axis}": statistics.fmean(
            ratio for cell, ratio in ratios.items() if cell[:2] == (scale, axis)
        ) for scale in SCALES for axis in DIRECTIONS
    }
    overall = statistics.fmean(ratios.values())
    limit = OLD_ROUTE_MULTIPLIER * old_metrics["overall"]
    passed = (
        small <= SCALE_MEAN_MAX and large <= SCALE_MEAN_MAX
        and all(value <= DIRECTION_MEAN_MAX for value in direction.values())
        and overall < limit
        and all(overall < value for value in old_metrics["comparators"].values())
    )
    # The proposed diagnostic would run only in both high-volume, large-y cells.
    at_risk = [cell for cell in records if cell[:3] == ("large", "y", "high")]
    if len(at_risk) != 2 or not set(rescued_cells) <= set(at_risk):
        raise ValueError("B2.16 at-risk population differs")
    inverse_denominators = sum(
        1 / records[cell]["outcomes"]["uniform"]["timing"]["end_to_end_seconds"]
        for cell in at_risk
    )
    constraints = {
        "large_scale": (SCALE_MEAN_MAX - large) * 12 / inverse_denominators,
        "large_y": (DIRECTION_MEAN_MAX - direction["large_y"]) * 6
                   / inverse_denominators,
        "old_route_advantage": (limit - overall) * 24 / inverse_denominators,
        "non_ml": (min(old_metrics["comparators"].values()) - overall) * 24
                  / inverse_denominators,
    }
    pilot_budget = max(0.0, min(constraints.values()))
    one_update_costs = [
        records[cell]["outcomes"]["uniform"]["timing"]["refinement_seconds"]
        / records[cell]["outcomes"]["uniform"]["candidate"]["iterations"]
        for cell in at_risk
    ]
    return {
        "old_route_overall": old_metrics["overall"],
        "old_route_multiplier_limit": limit,
        "rescued_cells": [list(cell) for cell in sorted(rescued_cells)],
        "ideal_overall": overall,
        "ideal_scale": {"small": small, "large": large},
        "ideal_direction": direction,
        "ideal_gate_passed": passed,
        "max_equal_pilot_seconds_per_at_risk_case_supremum": pilot_budget,
        "pilot_constraint_seconds": constraints,
        "measured_uniform_update_seconds": one_update_costs,
        "pilot_floor_feasible": passed and pilot_budget > max(one_update_costs),
    }


def assess(first: Records, second: Records) -> dict[str, Any]:
    if set(first) != set(second):
        raise ValueError("B2.16 cohort strata are not matched")
    oracle_first = {cell: best_successful_action(row) for cell, row in first.items()}
    oracle_second = {cell: best_successful_action(row) for cell, row in second.items()}
    cross_first_to_second = metrics(second, oracle_first)
    cross_second_to_first = metrics(first, oracle_second)
    oracle_first_metrics = metrics(first, oracle_first)
    oracle_second_metrics = metrics(second, oracle_second)
    rescue = ideal_rescue(second)
    if not oracle_first_metrics["gate_passed"] or not oracle_second_metrics["gate_passed"]:
        decision = "retire_fixed_checkpoint_selector_no_oracle_headroom"
    elif cross_first_to_second["gate_passed"] and cross_second_to_first["gate_passed"]:
        decision = "coarse_metadata_route_not_ruled_out_requires_fresh_confirmation"
    elif rescue["pilot_floor_feasible"]:
        decision = "bounded_online_reliability_probe_warranted"
    else:
        decision = "stop_current_fixed_checkpoint_family_pending_new_mechanism"
    return {
        "b214_oracle": oracle_first_metrics,
        "b215_oracle": oracle_second_metrics,
        "b214_to_b215_transfer": cross_first_to_second,
        "b215_to_b214_transfer": cross_second_to_first,
        "transfer_disagreements": sum(
            oracle_first[cell] != oracle_second[cell] for cell in first
        ),
        "b215_ideal_failure_rescue": rescue,
        "decision": decision,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--b214-root", type=Path, default=Path("/tmp/topolab-b214"))
    parser.add_argument("--b215-root", type=Path, default=Path("/tmp/topolab-b215"))
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--audit", action="store_true")
    args = parser.parse_args()
    plan = plan_payload()
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.16 plan differs from frozen identity")
    repository, revision = source_snapshot()
    output_root = external_root(repository, args.output_root)
    first_root = external_root(repository, args.b214_root)
    second_root = external_root(repository, args.b215_root)
    if len({output_root, first_root, second_root}) != 3:
        raise ValueError("B2.16 source and output roots must differ")
    context = {"plan_sha256": plan["plan_sha256"], "source_revision": revision,
               "python": platform.python_version(), "system": platform.system()}
    if not args.audit:
        print(json.dumps({**plan, **context}, sort_keys=True))
        return 0
    started = perf_counter()
    first = audited_records(first_root, "b214")
    second = audited_records(second_root, "b215")
    analysis = assess(first, second)
    elapsed = perf_counter() - started
    raw_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss = raw_rss if platform.system() == "Darwin" else raw_rss * 1024
    if elapsed > plan["resource_cap_seconds"] or peak_rss > plan["resource_cap_bytes"]:
        raise ValueError("B2.16 analysis exceeded frozen resource cap")
    result = {"version": "topolab.b2_16.assessment.v1", "context": context,
              "input_case_count": 48, "analysis_seconds": elapsed,
              "peak_rss_bytes": peak_rss, "analysis": analysis}
    output_root.mkdir(parents=True, exist_ok=True)
    destination = output_root / "assessment.json"
    temporary = output_root / ".assessment.json.tmp"
    temporary.write_bytes(canonical_bytes(result))
    os.replace(temporary, destination)
    print(json.dumps({"assessment_sha256": sha256(destination), **result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
