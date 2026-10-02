"""Frozen B4.7 spatial-objective rollback with P/17 fixed before fresh outcomes."""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np

from topolab import b4_confirmation as confirmation
from topolab.b3_artifacts import safe_path
from topolab.b3_catalog import (
    _grid,
    build_b3_case_catalog,
    build_b3_exposure_ledger,
    canonical_metadata_bytes,
    physical_fingerprint,
)
from topolab.b3_training import SEEDS
from topolab.b4_telemetry import digest
from topolab.b4_weighted_terminal import METHODS, RECORDING_ALLOWANCE, development_gate
from topolab.b4_weighted_terminal import fresh_cases as weighted_cases
from topolab.experiment import ExperimentCase

VERSION = "topolab.b4_7.spatial-rollback.v1"
RECEIPT_VERSION = "topolab.b4_7.recording.v1"
PRIMARY = 17
VOLUMES = (0.3341, 0.4691, 0.5401, 0.6001)
POSITIONS = ((1, 2), (3, 1), (5, 2))
CAPS = {
    "reference": (3600.0, 2_147_483_648),
    "screen": (21600.0, 2_147_483_648),
    "audit": (3600.0, 2_147_483_648),
}
UPSTREAM_FILES = {
    "context.json": "2db3e3be8657a52ffcd582876a9eff143bc4eb446136e1bd5be2bc3c14c1dd2f",
    "reference/progress.json": "0359ee5b9407cd7d50a07a7711f78b82407e3331a599533a98098138000c3583",
    "reference/summary.json": "2384f141dde14c7a928d3aba62e5d8677706386360a1d5c11ed3079cc39931f9",
    "screen/progress.json": "95ff484b609ab68e8f122d76c921345acdad6abee450959d55f4b42d18d5e4e0",
    "screen/summary.json": "6fd2358cb4808be0530fa3c063de966b042bf525f40b2b32313d3d2338c4752f",
    "audit/summary.json": "97ab5048e82b29ee75ca3c8245395df10914ecbb636558c5eca612c9ee31f201",
    "audit/progress.json": "2a53ed036b0df07e901c96eb872ef9b7d6b1dfef41dc443c363f6db812abb22f",
    "independent_audit.json": "4e64822cc79910b1b13f23f8fee26a224f93b8f4725557257e4eff60b88f8629",
    "resource_close.json": "833db4ce48d86ae33c0b983798f7d4ec3b6df4fdb7711246cad5a0775616277d",
}


def fresh_cases() -> tuple[ExperimentCase, ...]:
    cases = tuple(sorted(_grid(VOLUMES, POSITIONS, 360), key=lambda c: c.case_id))
    blocked = {e.physical_fingerprint for e in build_b3_exposure_ledger().entries}
    blocked.update(e.physical_fingerprint for e in build_b3_case_catalog().entries)
    blocked.update(
        physical_fingerprint(c) for c in (*weighted_cases(), *confirmation.fresh_cases())
    )
    fingerprints = {physical_fingerprint(c) for c in cases}
    if len(cases) != 48 or len(fingerprints) != 48 or fingerprints & blocked:
        raise ValueError("rollback crosses a previous physical exposure")
    return cases


def assignments() -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    other = METHODS[1:]
    for case in fresh_cases():
        offset = int(digest(("topolab.b4_7.order.v1:" + case.case_id).encode())[:8], 16) % len(
            other
        )
        result.extend((case.case_id, m) for m in ("uniform", *other[offset:], *other[:offset]))
    return tuple(result)


def units(stage: str) -> tuple[str, ...]:
    if stage == "reference":
        return tuple(c.case_id for c in fresh_cases())
    if stage == "screen":
        return tuple(f"{c}:{m}" for c, m in assignments())
    if stage != "audit":
        raise ValueError("rollback has no fitting stage")
    return (
        "inputs",
        "nn_labels",
        *(f"reference:{c}" for c in units("reference")),
        *(f"screen:{u}" for u in units("screen")),
    )


def plan() -> dict[str, Any]:
    payload = {
        "version": VERSION,
        "cases": [c.model_dump(mode="json") for c in fresh_cases()],
        "assignments": assignments(),
        "methods": METHODS,
        "seeds": SEEDS,
        "fixed_primary": PRIMARY,
        "candidate": "P",
        "comparison": "W",
        "new_fits": 0,
        "upstream_files": UPSTREAM_FILES,
        "weighted_files": confirmation.UPSTREAM_FILES,
        "recording_allowance_seconds": RECORDING_ALLOWANCE,
        "caps": CAPS,
        "quality_volumes": VOLUMES[2:],
        "quality_minimum": 6,
        "primary_total_ratio_maximum": 0.9,
        "final_access": False,
    }
    return {**payload, "plan_sha256": digest(canonical_metadata_bytes(payload))}


def upstream_fits(root: Path) -> list[dict[str, Any]]:
    """Bind the failed confirmation before any model or label bytes are opened."""
    previous = root.parent / "b4-6-development-confirmation"
    for path, expected in UPSTREAM_FILES.items():
        raw = safe_path(previous, path).read_bytes()
        if digest(raw) != expected or canonical_metadata_bytes(json.loads(raw)) != raw:
            raise ValueError("B4.6 receipt differs before model or label bytes")
    summary = json.loads(safe_path(previous, "audit/summary.json").read_bytes())
    if (
        summary["decision"]["confirmation_gate_passed"]
        or summary["decision"]["fixed_primary"] != 17
    ):
        raise ValueError("rollback requires the retained failed W/17 confirmation")
    return confirmation.upstream_fits(root)


def rollback_gate(packets: Iterable[dict[str, Any]]) -> dict[str, Any]:
    retained = tuple(packets)
    result = development_gate(
        retained,
        cohort=fresh_cases(),
        expected=assignments(),
        quality_volumes=VOLUMES[2:],
        quality_minimum=6,
        candidate="P",
    )
    cases = {c.case_id: c for c in fresh_cases()}
    totals = {m: {s: 0.0 for s in ("small", "large")} for m in METHODS}
    for packet in retained:
        scale = (
            "small" if cases[packet["case_id"]].problem.mesh.element_counts[0] == 12 else "large"
        )
        totals[packet["policy"]][scale] += packet["timing"]["wall_seconds"] + RECORDING_ALLOWANCE
    for name in METHODS:
        result["table"][name]["scale_total_ratios"] = {
            s: totals[name][s] / totals["uniform"][s] for s in ("small", "large")
        }
    primary = result["table"][f"P/{PRIMARY}"]
    passed = (
        result["development_gate_passed"]
        and primary["primary_eligible"]
        and max(primary["scale_total_ratios"].values()) <= 0.9
        and all(np.isfinite(v) for row in totals.values() for v in row.values())
    )
    result.pop("development_primary")
    result.update(
        fixed_primary=PRIMARY,
        rollback_gate_passed=bool(passed),
        development_gate_passed=bool(passed),
    )
    return result
