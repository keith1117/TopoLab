"""Frozen populations, unchanged inputs and complete charged B4.30 decisions."""

import json
import math
from collections.abc import Iterable
from functools import cache
from pathlib import Path
from typing import Any

from topolab import b4_terminal_preservation as previous
from topolab.b3_artifacts import safe_path
from topolab.b3_catalog import (
    _grid,
    build_b3_case_catalog,
    build_b3_exposure_ledger,
    canonical_metadata_bytes,
    physical_fingerprint,
)
from topolab.b3_queries import QueryOutcome, policy_route
from topolab.b4_confirmation import fresh_cases as b46_cases
from topolab.b4_polish_probe import fresh_cases as sealed_cases
from topolab.b4_reflection import mirror_case, reflection_target
from topolab.b4_rollback import fresh_cases as b47_cases
from topolab.b4_rollback_confirmation import fresh_cases as b48_cases
from topolab.b4_telemetry import digest
from topolab.b4_weighted_terminal import fresh_cases as b45_cases
from topolab.experiment import ExperimentCase

VERSION = "topolab.b4_30.z-reflection-repair.v1"
RECEIPT_VERSION = "topolab.b4_30.recording.v1"
CONTRACT_SHA256 = "ddb69d4947c01e849306b387bac5e23dbf9fd5fa42b896b29edac376b6bb63d3"
REPO = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO / "docs/planning/b4_30_z_reflection_repair_contract.json"
CAPS = {
    "reference": (3600.0, 2_147_483_648),
    "screen": (21600.0, 2_147_483_648),
    "audit": (3600.0, 2_147_483_648),
    "policy-audit": (3600.0, 2_147_483_648),
}
METHODS = (
    "uniform",
    "physics_heuristic",
    "nearest_neighbor",
    *(f"{m}/{s}" for m in ("C", "P", "W", "R") for s in (17, 29, 43)),
)


def contract() -> dict[str, Any]:
    raw = CONTRACT_PATH.read_bytes()
    if digest(raw) != CONTRACT_SHA256:
        raise ValueError("frozen reflection contract changed")
    return dict(json.loads(raw))


@cache
def cases(cohort: str) -> tuple[ExperimentCase, ...]:
    if cohort == "sentinel":
        selected = (
            *previous.sentinel_cases(),
            *(c for c in previous.fresh_cases() if reflection_target(c)),
        )
    elif cohort == "fresh":
        grid = contract()["fresh_grid"]
        selected = _grid(grid["volumes"], grid["positions"], grid["update_cap"])
    else:
        raise ValueError("unknown reflection cohort")
    result = tuple(sorted(selected, key=lambda c: c.case_id))
    bound = contract()["population"][cohort]
    fingerprints = [physical_fingerprint(c) for c in result]
    mirrors = tuple(mirror_case(c) for c in result)
    if (
        [c.case_id for c in result] != bound["case_ids"]
        or fingerprints != bound["physical_fingerprints"]
        or len(set(fingerprints)) != bound["count"]
        or [c.case_id for c in mirrors] != bound["mirrored_case_ids"]
        or [physical_fingerprint(c) for c in mirrors]
        != bound["virtual_mirror_physical_fingerprints"]
        or digest(canonical_metadata_bytes([c.model_dump(mode="json") for c in result]))
        != bound["case_definitions_sha256"]
    ):
        raise ValueError("reflection cohort differs from its prospective identity")
    if cohort == "fresh":
        blocked = {e.physical_fingerprint for e in build_b3_exposure_ledger().entries}
        blocked.update(e.physical_fingerprint for e in build_b3_case_catalog().entries)
        for population in (
            b45_cases,
            b46_cases,
            b47_cases,
            b48_cases,
            sealed_cases,
            previous.fresh_cases,
        ):
            blocked.update(physical_fingerprint(c) for c in population())
        virtual = {physical_fingerprint(c) for c in mirrors}
        if len(virtual | set(fingerprints)) != 96 or (virtual | set(fingerprints)) & blocked:
            raise ValueError("actual or virtual reflection case crosses a sealed/exposed boundary")
    return result


def assignments(cohort: str) -> tuple[tuple[str, str], ...]:
    other = METHODS[1:]
    rows: list[tuple[str, str]] = []
    for c in cases(cohort):
        offset = int(digest(("topolab.b4_30.order.v1:" + c.case_id).encode())[:8], 16) % len(other)
        rows.extend((c.case_id, method) for method in ("uniform", *other[offset:], *other[:offset]))
    result = tuple(rows)
    if (
        digest(canonical_metadata_bytes(result))
        != contract()["population"][cohort]["assignments_sha256"]
    ):
        raise ValueError("reflection query order changed")
    return result


def plan() -> dict[str, Any]:
    c = contract()
    value = {
        "version": VERSION,
        "receipt_version": RECEIPT_VERSION,
        "contract_sha256": CONTRACT_SHA256,
        "caps": CAPS,
        "methods": METHODS,
        "cases": {
            name: [x.model_dump(mode="json") for x in cases(name)] for name in ("sentinel", "fresh")
        },
        "assignments": {name: assignments(name) for name in ("sentinel", "fresh")},
        "candidate": c["candidate"],
        "resources": c["resources"],
        "sentinel_gate": c["sentinel_gate"],
        "fresh_gate": c["fresh_gate"],
        "protected_inputs": c["protected_external_metadata_sha256"],
        "source_files": previous.SOURCE_FILES,
        "diagnosis_files": previous.DIAGNOSIS_FILES,
        "polish_files": previous.POLISH_FILES,
        "review_files": previous.REVIEW_FILES,
        "fixed_primary": 17,
        "new_fits": 0,
        "final_access": False,
    }
    return {**value, "plan_sha256": digest(canonical_metadata_bytes(value))}


def protected_inputs(parent: Path) -> None:
    for name, expected in contract()["protected_external_metadata_sha256"].items():
        path = safe_path(parent, name)
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != parent.parent):
            raise ValueError("immutable input must not follow a symlink")
        if digest(path.read_bytes()) != expected:
            raise ValueError("protected input differs before model or label access: " + name)
    if (parent / "b4-10-post-plateau-polish/fresh").exists():
        raise ValueError("old B4.10 fresh panel must remain unopened")


def upstream_fits(root: Path) -> list[dict[str, Any]]:
    protected_inputs(root.parent)
    return previous.upstream_fits(root)


def compact_rows(packets: Iterable[dict[str, Any]], cohort: str) -> list[dict[str, Any]]:
    by_id = {c.case_id: c for c in cases(cohort)}
    expected = assignments(cohort)
    rows = []
    for index, packet in enumerate(packets):
        if index >= len(expected) or (packet["case_id"], packet["policy"]) != expected[index]:
            raise ValueError("Gate needs every case/method exactly once in frozen order")
        outcome = QueryOutcome.model_validate(packet["outcome"])
        name, _, seed = packet["policy"].partition("/")
        method = "P" if name in ("W", "R") else name
        case = by_id[packet["case_id"]]
        wall = packet["timing"]["wall_seconds"]
        if (
            outcome.method != method
            or outcome.seed != (int(seed) if seed else None)
            or outcome.route != policy_route(case, outcome.method)
            or outcome.operational is None
            or outcome.attempt is None
            or not math.isfinite(wall)
            or wall <= 0
            or packet["timing"]["legacy_phase_seconds"] > wall
            or packet["recording_allowance_seconds"] != 1
        ):
            raise ValueError("complete charged outcome identity or operational quality differs")
        rows.append(
            {
                "case_id": case.case_id,
                "policy": packet["policy"],
                "cost": wall + 1,
                "failed": not outcome.attempt.succeeded,
                "fallback": outcome.fallback is not None,
                "route": outcome.route,
                "scale": "small" if case.problem.mesh.element_counts[0] == 12 else "large",
                "direction": case.problem.loads[0].direction,
                "volume": case.problem.optimization.volume_fraction,
                "target": reflection_target(case),
            }
        )
    if len(rows) != len(expected):
        raise ValueError("partial population cannot establish the repair Gate")
    return rows


def decision(packets: Iterable[dict[str, Any]], cohort: str) -> dict[str, Any]:
    rows = compact_rows(packets, cohort)
    by_key = {(r["case_id"], r["policy"]): r for r in rows}
    uniform = {r["case_id"]: r["cost"] for r in rows if r["policy"] == "uniform"}
    result: dict[str, Any] = {"cohort": cohort, "fixed_primary": 17, "final_access": False}
    if cohort == "sentinel":
        repaired: list[list[str]] = []
        missing: list[list[str]] = []
        for unit in contract()["sentinel_gate"]["all_known_failed_target_units_repaired"]:
            key = (unit["case_id"], unit["policy"])
            (missing if by_key[key]["failed"] else repaired).append(list(key))
        r_rows = [r for r in rows if r["policy"].startswith("R/")]
        regressions = [
            [r["case_id"], r["policy"]]
            for r in r_rows
            if r["failed"] and not by_key[(r["case_id"], r["policy"].replace("R/", "P/"))]["failed"]
        ]
        negative = [
            r
            for r in r_rows
            if not r["target"] and by_key[(r["case_id"], r["policy"].replace("R/", "P/"))]["failed"]
        ]
        primary = [r for r in r_rows if r["policy"] == "R/17"]
        failures = [r["case_id"] for r in primary if r["failed"] or r["fallback"]]
        targets = [r for r in primary if r["target"]]
        target_mean = math.fsum(r["cost"] / uniform[r["case_id"]] for r in targets) / len(targets)
        total = math.fsum(r["cost"] for r in targets) / math.fsum(
            uniform[r["case_id"]] for r in targets
        )
        identities = all(
            (r["failed"], r["fallback"])
            == (
                by_key[(r["case_id"], r["policy"].replace("R/", "P/"))]["failed"],
                by_key[(r["case_id"], r["policy"].replace("R/", "P/"))]["fallback"],
            )
            for r in r_rows
            if not r["target"]
        )
        passed = bool(
            not missing
            and not regressions
            and not failures
            and identities
            and len(negative) == 2
            and all(r["failed"] for r in negative)
            and len(targets) == 13
            and target_mean <= 1
            and total <= 1
        )
        result.update(
            repaired=repaired,
            unrepaired=missing,
            regressions=regressions,
            primary_failures=failures,
            negative_controls=[[r["case_id"], r["policy"]] for r in negative],
            non_target_status_identity=identities,
            target_cases=len(targets),
            large_y_primary_mean=target_mean,
            large_y_primary_total_ratio=total,
            sentinel_gate_passed=passed,
            repair_gate_passed=passed,
        )
        return result
    table: dict[str, Any] = {}
    totals: dict[str, dict[str, float]] = {}
    for method in METHODS:
        selected = [r for r in rows if r["policy"] == method]

        def mean(subset: list[dict[str, Any]]) -> float:
            return math.fsum(r["cost"] / uniform[r["case_id"]] for r in subset) / len(subset)

        table[method] = {
            "overall_mean": mean(selected),
            "scale_means": {
                s: mean([r for r in selected if r["scale"] == s]) for s in ("small", "large")
            },
            "direction_means": {
                f"{s}/{d}": mean([r for r in selected if r["scale"] == s and r["direction"] == d])
                for s in ("small", "large")
                for d in ("y", "z")
            },
            "failures": sum(r["failed"] for r in selected),
            "fallbacks": sum(r["fallback"] for r in selected),
            "non_specialist_y_failures": sum(
                r["failed"]
                for r in selected
                if r["direction"] == "y" and r["route"] != "specialist"
            ),
        }
        totals[method] = {
            s: math.fsum(r["cost"] for r in selected if r["scale"] == s) for s in ("small", "large")
        }
    passing = []
    for seed in (17, 29, 43):
        r, c, w = (table[f"{m}/{seed}"] for m in ("R", "C", "W"))
        passed = bool(
            max(r["scale_means"].values()) <= 0.9
            and max(r["direction_means"].values()) <= 1
            and r["failures"] <= min(2, c["failures"], w["failures"])
            and r["non_specialist_y_failures"]
            <= min(c["non_specialist_y_failures"], w["non_specialist_y_failures"])
            and r["overall_mean"]
            < min(table[m]["overall_mean"] for m in ("physics_heuristic", "nearest_neighbor"))
        )
        r["seed_gate_passed"] = passed
        r["primary_eligible"] = bool(
            passed
            and r["failures"] == r["fallbacks"] == 0
            and r["overall_mean"] < c["overall_mean"]
            and (r["overall_mean"] < w["overall_mean"] or r["failures"] < w["failures"])
        )
        if passed:
            passing.append(seed)
    cells = {
        str(v): sum(
            not r["failed"]
            for r in rows
            if r["policy"].startswith("R/")
            and r["scale"] == "large"
            and r["direction"] == "y"
            and r["volume"] == v
        )
        for v in (0.5457, 0.6057)
    }
    ratios = {s: totals["R/17"][s] / totals["uniform"][s] for s in ("small", "large")}
    passed = bool(
        len(passing) >= 2
        and table["R/17"]["primary_eligible"]
        and min(cells.values()) >= 6
        and max(ratios.values()) <= 0.9
    )
    result.update(
        table=table,
        passing_seeds=passing,
        quality_cells=cells,
        primary_total_ratios=ratios,
        development_gate_passed=passed,
        repair_gate_passed=passed,
    )
    return result
