"""B2.25 read-only cost diagnosis of the fixed B2.24 development screen."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import resource
import statistics
import subprocess
from collections import defaultdict
from pathlib import Path
from time import perf_counter
from typing import Any

from b2_24_expanded_training import METHODS, cohorts

VERSION = "topolab.b2_25.residual_cost.v1"
EXPECTED_PLAN_SHA256 = "11a03776d87828c0100381d6276a515b72dd4f59c311eeb67963f507e69a2cc0"
B224_SOURCE = "dd110b8067acccdcc900709a20809c924b7fbbc8"
B224_PLAN = "50230a66db17c26ed4665bce41142c61b3e5ffc5f2dcfb83988d77d84884dd94"
DIGESTS = {
    "reference_index.json": "c3703ab52820f618f3ec664a4a515432d5e95bb3c6d8464210b6003d24935eb7",
    "fit_index.json": "89bacfec6fbdfd2732ab74404626dc33a914b7cf788750f02276319b7e73700a",
    "screen_index.json": "e77ad2eb6670dcae64e14c51d67b4b6ad6dc05d2d8e57448be39c8c584db1075",
}
SEEDS = (17, 29, 43)
SCALES = ("small", "large")
DIRECTIONS = ("y", "z")
BOUND_ORDER = ("measured", "fallback_free", "z_zero", "combined")
MAX_SECONDS = 60.0
MAX_RSS_BYTES = 1_073_741_824


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan_payload() -> dict[str, Any]:
    _, cases, _ = cohorts()
    identity = {
        "version": VERSION,
        "b224_source_revision": B224_SOURCE,
        "b224_plan_sha256": B224_PLAN,
        "b224_index_sha256": DIGESTS,
        "case_ids": [case.case_id for case in cases],
        "methods": METHODS,
        "seeds": SEEDS,
        "scale_mean_max": 0.90,
        "direction_mean_max": 1.0,
        "required_speed_seeds": 2,
        "bounds": BOUND_ORDER,
        "decision_order": (
            "fallback_free_two_seed_speed_then_y_reliability",
            "z_zero_two_seed_speed_then_z_refinement",
            "combined_two_seed_speed_then_joint_generalist",
            "otherwise_method_class_reassessment",
        ),
        "max_seconds": MAX_SECONDS,
        "max_rss_bytes": MAX_RSS_BYTES,
        "scope": "read_only_exposed_b224_development_outcomes",
    }
    return {**identity, "plan_sha256": hashlib.sha256(canonical_bytes(identity)).hexdigest()}


def source_snapshot() -> tuple[Path, str]:
    repository = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True
    ).strip()).resolve()
    for command in (["git", "diff", "--quiet"], ["git", "diff", "--cached", "--quiet"]):
        if subprocess.run(command, cwd=repository, check=False).returncode:
            raise ValueError("B2.25 requires a clean tracked revision")
    revision = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repository, text=True
    ).strip()
    return repository, revision


def external_root(repository: Path, root: Path) -> Path:
    resolved = root.resolve()
    if resolved == repository or resolved.is_relative_to(repository):
        raise ValueError("B2.25 artifacts must stay outside Git")
    return resolved


def close(left: float, right: float) -> bool:
    return math.isclose(left, right, rel_tol=1e-8, abs_tol=1e-8)


def audited_rows(root: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    indices: dict[str, dict[str, Any]] = {}
    for filename, expected in DIGESTS.items():
        path = root / filename
        if digest(path) != expected:
            raise ValueError(f"B2.25 {filename} digest differs")
        indices[filename] = json.loads(path.read_bytes())
    reference, fit, screen = (indices[name] for name in DIGESTS)
    for index in (reference, fit, screen):
        context = index["context"]
        if (context["source_revision"] != B224_SOURCE
                or context["plan_sha256"] != B224_PLAN):
            raise ValueError("B2.25 frozen B2.24 context differs")
    if (screen["context"]["reference_index_sha256"] != DIGESTS["reference_index.json"]
            or screen["context"]["fit_index_sha256"] != DIGESTS["fit_index.json"]
            or len(reference["rows"]) != 24 or len(fit["rows"]) != 3
            or len(screen["rows"]) != 24
            or [row["seed"] for row in fit["rows"]] != list(SEEDS)):
        raise ValueError("B2.25 incomplete or unbound source stages")
    for index, cap in ((reference, 3600), (fit, 7200), (screen, 16000)):
        if (index["elapsed_seconds"] > cap
                or index["peak_rss_bytes"] > 2_147_483_648):
            raise ValueError("B2.25 source resource cap differs")
    rows = screen["rows"]
    if [row["case"]["case_id"] for row in rows] != plan["case_ids"]:
        raise ValueError("B2.25 physical case ordering differs")
    for reference_row, row in zip(reference["rows"], rows, strict=True):
        case = row["case"]
        if (reference_row["case_id"] != case["case_id"]
                or not reference_row["uniform"]["succeeded"]
                or case["scale"] not in SCALES or case["direction"] not in DIRECTIONS
                or case["volume"] not in (0.3665, 0.5165, 0.5965)
                or case["specialist_route"] != (
                    case["scale"] == "large" and case["direction"] == "y"
                    and case["volume"] >= 0.55
                )):
            raise ValueError("B2.25 reference/case identity differs")
        outcomes = row["outcomes"]
        if tuple(item["method"] for item in outcomes) != METHODS:
            raise ValueError("B2.25 method ordering differs")
        uniform = outcomes[0]
        denominator = uniform["timing"]["end_to_end_seconds"]
        compliance = uniform["operational"]["final_compliance"]
        if (not uniform["succeeded"] or denominator <= 0 or compliance <= 0
                or not close(uniform["paired_time_ratio"], 1.0)
                or not close(compliance,
                             reference_row["uniform"]["candidate"]["final_compliance"])):
            raise ValueError("B2.25 uniform denominator differs")
        for item in outcomes:
            timing = item["timing"]
            total = timing["end_to_end_seconds"]
            candidate = item["candidate"]
            operational = item["operational"]
            if (item["case_id"] != case["case_id"]
                    or any(not math.isfinite(value) or value < 0 for value in timing.values())
                    or not close(total, sum(value for key, value in timing.items()
                                            if key != "end_to_end_seconds"))
                    or not close(item["paired_time_ratio"], total / denominator)
                    or not close(item["uniform_reference_compliance"], compliance)
                    or item["fallback_used"] != (not item["succeeded"])
                    or operational["physical_volume_error"] > 0.005
                    or operational["final_compliance"] > 1.001 * compliance):
                raise ValueError("B2.25 invalid charged outcome")
            if item["method"] == "uniform":
                if candidate != operational or item["seed"] is not None:
                    raise ValueError("B2.25 uniform candidate differs")
            else:
                seed = int(item["method"].split("_")[1])
                if (item["seed"] != seed or candidate is None
                        or item["route"] != ("specialist" if case["specialist_route"]
                                             else "context")
                        or (item["succeeded"] and (candidate != operational
                            or candidate["final_compliance"] > 1.001 * compliance
                            or candidate["physical_volume_error"] > 0.005))
                        or (not item["succeeded"] and (
                            item["failure_code"] is None
                            or timing["fallback_seconds"] <= 0
                            or not close(operational["final_compliance"], compliance)))):
                    raise ValueError("B2.25 learned quality or route differs")
    return rows


def effective_ratio(row: dict[str, Any], item: dict[str, Any], bound: str) -> float:
    time = item["timing"]["end_to_end_seconds"]
    if bound in ("fallback_free", "combined"):
        time -= item["timing"]["fallback_seconds"]
    if bound in ("z_zero", "combined") and row["case"]["scale"] == "large" \
            and row["case"]["direction"] == "z":
        time = 0.0
    return time / row["outcomes"][0]["timing"]["end_to_end_seconds"]


def speed_metrics(rows: list[dict[str, Any]], method: str, bound: str) -> dict[str, Any]:
    ratios: defaultdict[str, list[float]] = defaultdict(list)
    failures: list[dict[str, Any]] = []
    fallback_seconds = 0.0
    for row in rows:
        item = next(item for item in row["outcomes"] if item["method"] == method)
        case = row["case"]
        ratio = effective_ratio(row, item, bound)
        ratios[case["scale"]].append(ratio)
        ratios[f"{case['scale']}_{case['direction']}"].append(ratio)
        if not item["succeeded"]:
            failures.append({
                "case_id": case["case_id"], "scale": case["scale"],
                "direction": case["direction"], "volume": case["volume"],
                "candidate_compliance_ratio": item["candidate"]["final_compliance"]
                / item["uniform_reference_compliance"],
                "candidate_iterations": item["candidate"]["iterations"],
                "fallback_seconds": item["timing"]["fallback_seconds"],
            })
            fallback_seconds += item["timing"]["fallback_seconds"]
    means = {key: statistics.fmean(values) for key, values in sorted(ratios.items())}
    passed = (all(means[scale] <= 0.90 for scale in SCALES)
              and all(means[f"{scale}_{direction}"] <= 1.0
                      for scale in SCALES for direction in DIRECTIONS))
    return {"means": means, "speed_bounds_met": passed, "failures": failures,
            "fallback_seconds": fallback_seconds}


def choose_next(bounds: dict[str, dict[str, dict[str, Any]]]) -> str:
    for bound, decision in (
        ("fallback_free", "y_reliability"),
        ("z_zero", "z_refinement"),
        ("combined", "joint_generalist"),
    ):
        if sum(bounds[bound][str(seed)]["speed_bounds_met"] for seed in SEEDS) >= 2:
            return decision
    return "method_class_reassessment"


def diagnose(rows: list[dict[str, Any]]) -> dict[str, Any]:
    bounds = {
        bound: {str(seed): speed_metrics(rows, f"expanded_{seed}", bound)
                for seed in SEEDS}
        for bound in BOUND_ORDER
    }
    old = {str(seed): speed_metrics(rows, f"old_{seed}", "measured")
           for seed in SEEDS}
    phase: dict[str, dict[str, Any]] = {}
    for seed in SEEDS:
        for scale in SCALES:
            for direction in DIRECTIONS:
                selected = [(row, next(item for item in row["outcomes"]
                                       if item["method"] == f"expanded_{seed}"))
                            for row in rows if row["case"]["scale"] == scale
                            and row["case"]["direction"] == direction]
                phase[f"{seed}_{scale}_{direction}"] = {
                    "mean_refinement_seconds": statistics.fmean(
                        item["timing"]["refinement_seconds"] for _, item in selected),
                    "mean_fallback_seconds": statistics.fmean(
                        item["timing"]["fallback_seconds"] for _, item in selected),
                    "mean_uniform_refinement_seconds": statistics.fmean(
                        row["outcomes"][0]["timing"]["refinement_seconds"]
                        for row, _ in selected),
                    "mean_candidate_iterations": statistics.fmean(
                        item["candidate"]["iterations"] for _, item in selected),
                    "mean_uniform_iterations": statistics.fmean(
                        row["outcomes"][0]["candidate"]["iterations"]
                        for row, _ in selected),
                }
    return {"bounds": bounds, "old_measured": old, "phase": phase,
            "next_mechanism": choose_next(bounds),
            "caveat": "optimistic_time_only_bounds_preserve_failed_quality_status"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--source-root", type=Path, default=Path("/tmp/topolab-b224"))
    parser.add_argument("--output-root", type=Path, default=Path("/tmp/topolab-b225"))
    args = parser.parse_args()
    start = perf_counter()
    repository, revision = source_snapshot()
    plan = plan_payload()
    if plan["plan_sha256"] != EXPECTED_PLAN_SHA256:
        raise ValueError("B2.25 frozen plan differs")
    if not args.audit:
        print(json.dumps({"source_revision": revision, "plan": plan}, sort_keys=True))
        return
    source = external_root(repository, args.source_root)
    output = external_root(repository, args.output_root)
    rows = audited_rows(source, plan)
    result = {"version": VERSION, "source_revision": revision,
              "plan_sha256": plan["plan_sha256"], "source_index_sha256": DIGESTS,
              "diagnosis": diagnose(rows)}
    elapsed = perf_counter() - start
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if os.uname().sysname != "Darwin":
        peak *= 1024
    if elapsed > MAX_SECONDS or peak > MAX_RSS_BYTES:
        raise ValueError("B2.25 diagnostic resource cap exceeded")
    result["elapsed_seconds"] = elapsed
    result["peak_rss_bytes"] = peak
    output.mkdir(parents=True, exist_ok=True)
    target = output / "diagnosis.json"
    temporary = output / "diagnosis.json.tmp"
    temporary.write_bytes(canonical_bytes(result))
    temporary.replace(target)
    print(json.dumps({"result": str(target), "sha256": digest(target),
                      "next_mechanism": result["diagnosis"]["next_mechanism"]},
                     sort_keys=True))


if __name__ == "__main__":
    main()
