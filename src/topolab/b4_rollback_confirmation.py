"""Frozen B4.8 larger rollback confirmation with prospectively fixed P/17."""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np

from topolab import b4_confirmation as confirmation
from topolab import b4_rollback as rollback
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

VERSION = "topolab.b4_8.rollback-confirmation.v1"
RECEIPT_VERSION = "topolab.b4_8.recording.v1"
PRIMARY = 17
VOLUMES = (0.3353, 0.4703, 0.5413, 0.6013)
POSITIONS = ((1, 1), (1, 2), (3, 1), (3, 2), (5, 1), (5, 2))
CAPS = {
    "reference": (7200.0, 2_147_483_648),
    "screen": (43200.0, 2_147_483_648),
    "audit": (7200.0, 2_147_483_648),
}
UPSTREAM_FILES = {
    "context.json": "57b21d1d25dbcd9ee604a97857b31e9e521f11741d999e30b38abcb8242d34df",
    "reference/progress.json": "9fde5a3d4f4299a13471c592b9f4d3520b28e1d2b03185f9402d4a028bb15f78",
    "reference/summary.json": "7c84e94c5196b996c2f8b3c589df0519fbaf8a1437ed4c6953688470e7d73250",
    "screen/progress.json": "e323451a23d1ab63599d1d57dd920694840ddd8b3ae6a5f12ffd25238da93765",
    "screen/summary.json": "17eaf004a87a52c7afddf70a48eaf7a7d6702d26f8c99597dd5f581f06be35f8",
    "audit/summary.json": "583dea5c2f356e2cf460a553b4030512d8c84fd9543984a6265a37013f1dfe7e",
    "audit/progress.json": "a6e48222e8e7b0af1e211020ae83101d3d77885ce99ec6951d7d89dc1a5a8e82",
    "independent_audit.json": "ce9f267a8c5ec696a4982aa25e07cdc607b01137b5087725db21627a65d0f856",
    "resource_close.json": "46a6167303c0bcb5c5bd7bd58acdc9ec950740caa37962aff94e7d9f5b0d6c92",
}


def fresh_cases() -> tuple[ExperimentCase, ...]:
    cases = tuple(sorted(_grid(VOLUMES, POSITIONS, 360), key=lambda c: c.case_id))
    blocked = {e.physical_fingerprint for e in build_b3_exposure_ledger().entries}
    blocked.update(e.physical_fingerprint for e in build_b3_case_catalog().entries)
    blocked.update(
        physical_fingerprint(c)
        for c in (*weighted_cases(), *confirmation.fresh_cases(), *rollback.fresh_cases())
    )
    fingerprints = {physical_fingerprint(c) for c in cases}
    if len(cases) != 96 or len(fingerprints) != 96 or fingerprints & blocked:
        raise ValueError("rollback confirmation crosses a previous physical exposure")
    return cases


def assignments() -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    other = METHODS[1:]
    for case in fresh_cases():
        offset = int(digest(("topolab.b4_8.order.v1:" + case.case_id).encode())[:8], 16) % len(
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
        "confirmation_files": rollback.UPSTREAM_FILES,
        "weighted_files": confirmation.UPSTREAM_FILES,
        "recording_allowance_seconds": RECORDING_ALLOWANCE,
        "caps": CAPS,
        "quality_volumes": VOLUMES[2:],
        "quality_minimum": 12,
        "primary_total_ratio_maximum": 0.9,
        "final_access": False,
    }
    return {**payload, "plan_sha256": digest(canonical_metadata_bytes(payload))}


def upstream_fits(root: Path) -> list[dict[str, Any]]:
    """Bind the passed repair before any model or label bytes are opened."""
    previous = root.parent / "b4-7-spatial-rollback"
    for path, expected in UPSTREAM_FILES.items():
        raw = safe_path(previous, path).read_bytes()
        if digest(raw) != expected or canonical_metadata_bytes(json.loads(raw)) != raw:
            raise ValueError("B4.7 receipt differs before model or label bytes")
    summary = json.loads(safe_path(previous, "audit/summary.json").read_bytes())
    if (
        not summary["decision"]["rollback_gate_passed"]
        or summary["decision"]["fixed_primary"] != PRIMARY
    ):
        raise ValueError("confirmation requires the passed fixed P/17 repair")
    return rollback.upstream_fits(root)


def confirmation_gate(packets: Iterable[dict[str, Any]]) -> dict[str, Any]:
    retained = tuple(packets)
    result = development_gate(
        retained,
        cohort=fresh_cases(),
        expected=assignments(),
        quality_volumes=VOLUMES[2:],
        quality_minimum=12,
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
        confirmation_gate_passed=bool(passed),
        development_gate_passed=bool(passed),
    )
    return result
