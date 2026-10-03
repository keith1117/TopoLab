"""Frozen B4.10 exposed stop gate and physically disjoint development plan."""

import json
from collections.abc import Iterable
from math import isfinite
from pathlib import Path
from typing import Any

from topolab import b4_rollback_confirmation as previous
from topolab.b3_artifacts import safe_path
from topolab.b3_catalog import (
    _grid,
    build_b3_case_catalog,
    build_b3_exposure_ledger,
    canonical_metadata_bytes,
    physical_fingerprint,
)
from topolab.b3_queries import QueryOutcome
from topolab.b3_training import SEEDS
from topolab.b4_confirmation import fresh_cases as confirmation_cases
from topolab.b4_polish import POLISH_UPDATES, POLISH_VERSION
from topolab.b4_rollback import fresh_cases as rollback_cases
from topolab.b4_telemetry import digest
from topolab.b4_weighted_terminal import METHODS, development_gate
from topolab.b4_weighted_terminal import fresh_cases as weighted_cases
from topolab.experiment import ExperimentCase
from topolab.problem import PointLoadDefinition

VERSION = "topolab.b4_10.post-plateau-probe.v1"
RECEIPT_VERSION = "topolab.b4_10.recording.v1"
VOLUMES = (0.3367, 0.4717, 0.5427, 0.6027)
POSITIONS = ((1, 1), (3, 1), (5, 2))
CAPS = {
    "reference": (3600.0, 2_147_483_648),
    "screen": (21600.0, 2_147_483_648),
    "audit": (3600.0, 2_147_483_648),
    "policy-audit": (3600.0, 2_147_483_648),
}
SOURCE_FILES = {
    "context.json": "b405d69754c5c22a1fd936581d44beea2f261db2069600ee327421f953bad5be",
    "reference/progress.json": "aaf793eac36bdbb6a600170c3dfbe26f1ec6f3b59e5eca684254c146e8396616",
    "reference/summary.json": "e55f6f54a94b754c6575bea93a183d71ae3bef3d854447c0277fda5bd15badea",
    "screen/progress.json": "241a73288bf7301c09d8fe17258d250316ea5c8703b8bb1c1c393d1a7b2d84e9",
    "screen/summary.json": "9cf1eb1999c36c2340c53194830dd531c3c4149eeb156e17ab38ab7d46f903af",
    "audit/progress.json": "f1d06c3a99351ffcfbbcc4624d176ab11b2539d6be3c7a5243db70da37d6f98d",
    "audit/summary.json": "7a4ef6d95cbba59734f01ee260f8fae818b89fbec3238b13595f9d63ae9f783b",
    "independent_audit.json": "88c37018ca9f6ca325003c4c5f4b57debf0855bd2313eb3a62dbed50064cd663",
    "resource_close.json": "c4128a77de823b0de2cc83d093157db52e689ee4dbdc4e0f908b675e9c5150ec",
    "audit_receipts/plan.json": "31dece2979a469ea600911036d9e2ab15ae45c593c7b22cf770a4d135758f56f",
    "audit_receipts/production_release.json": (
        "051867604ce5b4dab18d7dca91a046faa077de0578ede07e18a4390e39d21e6c"
    ),
}
DIAGNOSIS_FILES = {
    "diagnosis.json": "c42b7eb640df96786820125b7570a7f68730edbb00478fe7efc5303e2c381a65",
    "independent_audit.json": "5f4439a835b620817fed55f567a7a7ee3ab5d23dccbdbfa395ff9363f857c23b",
    "resource_close.json": "bcd367d6ce163856ada0ecbb8875860a9cc237f55dcf6d5fb1ae856d468046da",
}
# Metadata chosen from the already published B4.9 diagnosis, before continuation.
SENTINEL = (
    (24, "y", 0.5413, 3, 1),
    (24, "y", 0.4703, 1, 1),
    (24, "y", 0.4703, 1, 2),
    (12, "z", 0.4703, 3, 1),
    (12, "z", 0.4703, 3, 2),
    (24, "y", 0.3353, 3, 1),
    (24, "y", 0.6013, 3, 1),
    (24, "z", 0.4703, 3, 1),
    (12, "y", 0.4703, 3, 1),
)


def sentinel_cases() -> tuple[ExperimentCase, ...]:
    selected: list[ExperimentCase] = []
    for case in previous.fresh_cases():
        load = case.problem.loads[0]
        assert isinstance(load, PointLoadDefinition)
        scale = case.problem.mesh.element_counts[0]
        factor = scale // 12
        if isinstance(load.node, int):
            nx, ny, _ = case.problem.mesh.element_counts
            position = (load.node // (nx + 1) % (ny + 1), load.node // ((nx + 1) * (ny + 1)))
        else:
            position = (load.node[1], load.node[2])
        key = (
            scale,
            load.direction,
            case.problem.optimization.volume_fraction,
            position[0] // factor,
            position[1] // factor,
        )
        if key in SENTINEL:
            selected.append(case)
    if len(selected) != len(SENTINEL):
        raise ValueError("sentinel metadata differs from its nine frozen cases")
    return tuple(selected)


def fresh_cases() -> tuple[ExperimentCase, ...]:
    cases = tuple(sorted(_grid(VOLUMES, POSITIONS, 360), key=lambda c: c.case_id))
    blocked = {e.physical_fingerprint for e in build_b3_exposure_ledger().entries}
    blocked.update(e.physical_fingerprint for e in build_b3_case_catalog().entries)
    blocked.update(
        physical_fingerprint(c)
        for c in (
            *weighted_cases(),
            *confirmation_cases(),
            *rollback_cases(),
            *previous.fresh_cases(),
        )
    )
    fingerprints = {physical_fingerprint(c) for c in cases}
    if len(cases) != 48 or len(fingerprints) != 48 or fingerprints & blocked:
        raise ValueError("polish cohort crosses a previous physical exposure")
    return cases


def cases(cohort: str) -> tuple[ExperimentCase, ...]:
    if cohort not in ("sentinel", "fresh"):
        raise ValueError("unknown polish cohort")
    return sentinel_cases() if cohort == "sentinel" else fresh_cases()


def assignments(cohort: str) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    other = METHODS[1:]
    for case in cases(cohort):
        offset = int(digest((VERSION + ":" + case.case_id).encode())[:8], 16) % len(other)
        result.extend((case.case_id, m) for m in ("uniform", *other[offset:], *other[:offset]))
    return tuple(result)


def plan() -> dict[str, Any]:
    payload = {
        "version": VERSION,
        "polish_version": POLISH_VERSION,
        "polish_updates": POLISH_UPDATES,
        "fixed_primary": 17,
        "seeds": SEEDS,
        "methods": METHODS,
        "caps": CAPS,
        "cases": {c: [x.model_dump(mode="json") for x in cases(c)] for c in ("sentinel", "fresh")},
        "assignments": {c: assignments(c) for c in ("sentinel", "fresh")},
        "source_files": SOURCE_FILES,
        "diagnosis_files": DIAGNOSIS_FILES,
        "sentinel_large_y_primary_mean_and_total_ratio_maximum": 1.0,
        "fresh_primary_scale_total_ratio_maximum": 0.9,
        "new_fits": 0,
        "total_update_cap": 360,
        "final_access": False,
        "independent_audit_cap_seconds": 1800,
        "resource_close_cap_seconds": 180,
        "whole_slice_cap_seconds": 43200,
        "whole_slice_rss_bytes": 2_147_483_648,
    }
    return {**payload, "plan_sha256": digest(canonical_metadata_bytes(payload))}


def upstream_fits(root: Path) -> list[dict[str, Any]]:
    for sibling, bindings in (
        ("b4-8-rollback-confirmation", SOURCE_FILES),
        ("b4-9-diagnosis", DIAGNOSIS_FILES),
    ):
        for path, sha in bindings.items():
            raw = safe_path(root.parent / sibling, path).read_bytes()
            if digest(raw) != sha:
                raise ValueError("polish input receipt changed before model or label bytes")
            if (
                not path.startswith("audit_receipts/")
                and canonical_metadata_bytes(json.loads(raw)) != raw
            ):
                raise ValueError("polish input receipt is noncanonical")
    return previous.upstream_fits(root)


def identity(outcome: dict[str, Any]) -> dict[str, Any]:
    """Numerical status, route, NN identity and witnesses, with timings omitted."""
    value = dict(outcome)
    value.pop("route_seconds")
    for name in ("attempt", "fallback"):
        if value[name] is not None:
            value[name] = {k: v for k, v in value[name].items() if k != "timing"}
    return value


def sentinel_gate(
    packets: Iterable[dict[str, Any]], original: dict[tuple[str, str], dict[str, Any]]
) -> dict[str, Any]:
    retained = tuple(packets)
    if tuple((p["case_id"], p["policy"]) for p in retained) != assignments("sentinel"):
        raise ValueError("sentinel requires every frozen outcome in order")
    uniform = {
        p["case_id"]: p["timing"]["wall_seconds"] + 1 for p in retained if p["policy"] == "uniform"
    }
    by_id = {c.case_id: c for c in sentinel_cases()}
    repaired: list[list[str]] = []
    regressions: list[list[str]] = []
    primary_failures: list[str] = []
    negative_controls: list[list[str]] = []
    ratios, costs, denominators = [], [], []
    for p in retained:
        key = (p["case_id"], p["policy"])
        if (
            not isfinite(p["timing"]["wall_seconds"])
            or p["timing"]["wall_seconds"] <= 0
            or p["recording_allowance_seconds"] != 1
        ):
            raise ValueError("sentinel requires finite complete charged timings")
        now = QueryOutcome.model_validate(p["outcome"])
        old = QueryOutcome.model_validate(original[key]["outcome"])
        if now.operational is None:
            raise ValueError("sentinel operational result failed")
        if p["policy"].startswith("P/"):
            assert now.attempt is not None and old.attempt is not None
            case = by_id[p["case_id"]]
            target = (
                case.problem.mesh.element_counts[0] == 24
                and case.problem.loads[0].direction == "y"
                and now.route == "generalist"
            )
            if target and not old.attempt.succeeded:
                (repaired if now.attempt.succeeded else regressions).append(list(key))
            if old.attempt.succeeded and not now.attempt.succeeded:
                regressions.append(list(key))
            if not target and not old.attempt.succeeded:
                negative_controls.append(list(key))
            if p["policy"] == "P/17":
                if not now.attempt.succeeded:
                    primary_failures.append(p["case_id"])
                if target:
                    cost = p["timing"]["wall_seconds"] + 1
                    ratios.append(cost / uniform[p["case_id"]])
                    costs.append(cost)
                    denominators.append(uniform[p["case_id"]])
    mean, total = sum(ratios) / len(ratios), sum(costs) / sum(denominators)
    passed = (
        len(repaired) == 4 and not regressions and not primary_failures and mean <= 1 and total <= 1
    )
    return {
        "sentinel_gate_passed": passed,
        "fixed_primary": 17,
        "repaired": repaired,
        "regressions": regressions,
        "primary_failures": primary_failures,
        "negative_controls": negative_controls,
        "large_y_primary_mean": mean,
        "large_y_primary_total_ratio": total,
        "final_access": False,
    }


def fresh_gate(packets: Iterable[dict[str, Any]]) -> dict[str, Any]:
    retained = tuple(packets)
    result = development_gate(
        retained,
        cohort=fresh_cases(),
        expected=assignments("fresh"),
        quality_volumes=VOLUMES[2:],
        quality_minimum=6,
        candidate="P",
    )
    by_id = {c.case_id: c for c in fresh_cases()}
    totals = {m: {s: 0.0 for s in ("small", "large")} for m in METHODS}
    for p in retained:
        scale = "small" if by_id[p["case_id"]].problem.mesh.element_counts[0] == 12 else "large"
        totals[p["policy"]][scale] += p["timing"]["wall_seconds"] + 1
    ratios = {s: totals["P/17"][s] / totals["uniform"][s] for s in ("small", "large")}
    passed = (
        result["development_gate_passed"]
        and result["table"]["P/17"]["primary_eligible"]
        and max(ratios.values()) <= 0.9
    )
    result.pop("development_primary")
    result.update(
        fixed_primary=17,
        primary_total_ratios=ratios,
        polish_gate_passed=passed,
        development_gate_passed=passed,
    )
    return result
