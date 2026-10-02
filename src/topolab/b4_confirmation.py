"""Frozen B4.6 cohort, passed upstream receipts and fixed-primary confirmation."""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np

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
from topolab.b4_weighted_terminal import (
    METHODS,
    RECORDING_ALLOWANCE,
    development_gate,
    read_units,
)
from topolab.b4_weighted_terminal import (
    fresh_cases as previous_cases,
)
from topolab.experiment import ExperimentCase

VERSION = "topolab.b4_6.development-confirmation.v1"
RECEIPT_VERSION = "topolab.b4_6.recording.v1"
PRIMARY = 17
VOLUMES = (0.3329, 0.4679, 0.5389, 0.5989)
POSITIONS = ((1, 1), (2, 2), (3, 2), (4, 1), (4, 2), (5, 1))
CAPS = {
    "reference": (7200.0, 2_147_483_648),
    "screen": (43200.0, 2_147_483_648),
    "audit": (7200.0, 2_147_483_648),
}
UPSTREAM_CONTEXT = "0454eee24c1c72c051f10dce0162f0f41d5a5ade1fb3a4e5b42c9c82c9d11071"
UPSTREAM_FILES = {
    "context.json": UPSTREAM_CONTEXT,
    "fit/progress.json": "5e54f8cede96d9e4b60acc17586d25d29903bd4927461a8d6b4b18f3b49e43ac",
    "fit/summary.json": "513064fe615456fe8204b511f850a71150895038c3541ad23f5cd35642b0cc6c",
    "reference/progress.json": "24dcf3909d8f9b1ca3db66d7a844556a0314e8e3ac0133f23219af7151d34af4",
    "reference/summary.json": "86db0bf3bb16dd28914d5a5fce043b073f563f19879b3750df0258b01f5aad9a",
    "screen/progress.json": "2ec2bf6b80ac340a6b770f34a0682dc0cd118122c31a426ef0a10ce6868953dd",
    "screen/summary.json": "d835c7e3aa88c080c3e1c52f2e8ec02d14fb2470f5b81e88c2b8ad54fb3e9f4b",
    "audit/progress.json": "9814b82a518a525526259e47cf45e3524db58e6e3e8759b30504e21909cc1940",
    "audit/summary.json": "1cf0ba874536cd58a05145c63ecf29474cc813a63dc8734696baea0abbb92100",
    "independent_audit.json": "5ab85296186739f61a4d94a0a8645199f9fdd935cadfdd447036bd31287997d5",
    "resource_close.json": "9dff4ba3334ba623fcc6f43db3a790f5135de2d370feefb66a5d49fdab7a3c1f",
}


def fresh_cases() -> tuple[ExperimentCase, ...]:
    cases = tuple(sorted(_grid(VOLUMES, POSITIONS, 360), key=lambda c: c.case_id))
    blocked = {e.physical_fingerprint for e in build_b3_exposure_ledger().entries}
    blocked.update(e.physical_fingerprint for e in build_b3_case_catalog().entries)
    blocked.update(physical_fingerprint(c) for c in previous_cases())
    fingerprints = {physical_fingerprint(c) for c in cases}
    if len(cases) != 96 or len(fingerprints) != 96 or fingerprints & blocked:
        raise ValueError("confirmation crosses a previous physical exposure")
    return cases


def assignments() -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    other = METHODS[1:]
    for case in fresh_cases():
        offset = int(digest(("topolab.b4_6.order.v1:" + case.case_id).encode())[:8], 16) % len(
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
        raise ValueError("confirmation has no fitting stage")
    return (
        "inputs",
        "nn_labels",
        *(f"reference:{c}" for c in units("reference")),
        *(f"screen:{a}" for a in units("screen")),
    )


def plan() -> dict[str, Any]:
    payload = {
        "version": VERSION,
        "cases": [c.model_dump(mode="json") for c in fresh_cases()],
        "assignments": assignments(),
        "methods": METHODS,
        "seeds": SEEDS,
        "fixed_primary": PRIMARY,
        "new_fits": 0,
        "upstream_files": UPSTREAM_FILES,
        "recording_allowance_seconds": RECORDING_ALLOWANCE,
        "caps": CAPS,
        "quality_volumes": VOLUMES[2:],
        "quality_minimum": 12,
        "primary_total_ratio_maximum": 0.9,
        "final_access": False,
    }
    return {**payload, "plan_sha256": digest(canonical_metadata_bytes(payload))}


def upstream_fits(root: Path) -> list[dict[str, Any]]:
    """Reject changed upstream metadata before opening any checkpoint/label bytes."""
    for path, expected in UPSTREAM_FILES.items():
        raw = safe_path(root, path).read_bytes()
        if digest(raw) != expected or canonical_metadata_bytes(json.loads(raw)) != raw:
            raise ValueError("passed B4.5 upstream receipt differs before model or label bytes")
    summary = json.loads(safe_path(root, "audit/summary.json").read_bytes())
    if (
        not summary["decision"]["development_gate_passed"]
        or summary["decision"]["development_primary"] != PRIMARY
    ):
        raise ValueError("upstream does not authorize the fixed confirmation primary")
    return read_units(root / "fit", UPSTREAM_CONTEXT, tuple(f"W/{s}" for s in SEEDS))


def confirmation_gate(packets: Iterable[dict[str, Any]]) -> dict[str, Any]:
    retained = tuple(packets)
    result = development_gate(
        retained,
        cohort=fresh_cases(),
        expected=assignments(),
        quality_volumes=VOLUMES[2:],
        quality_minimum=12,
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
    primary = result["table"][f"W/{PRIMARY}"]
    passed = (
        result["development_gate_passed"]
        and primary["primary_eligible"]
        and max(primary["scale_total_ratios"].values()) <= 0.9
        and all(np.isfinite(v) for row in totals.values() for v in row.values())
    )
    # No confirmation-result reselection: keep 17 even if 43 has better means.
    result.pop("development_primary")
    result.update(
        fixed_primary=PRIMARY,
        confirmation_gate_passed=bool(passed),
        development_gate_passed=bool(passed),
    )
    return result
