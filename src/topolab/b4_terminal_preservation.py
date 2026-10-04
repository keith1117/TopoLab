"""Candidate-only witness choice and frozen B4.12 development boundary."""

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import numpy as np

from topolab import b4_polish_probe as previous
from topolab.b3_artifacts import safe_path
from topolab.b3_catalog import (
    _grid,
    canonical_metadata_bytes,
    physical_fingerprint,
)
from topolab.b4_polish import POLISH_UPDATES, plateau, qualifies
from topolab.b4_telemetry import digest
from topolab.b4_weighted_terminal import METHODS, development_gate
from topolab.experiment import ExperimentCase
from topolab.problem import TopologyResult

VERSION = "topolab.b4_12.terminal-preservation-probe.v1"
POLICY_VERSION = "topolab.b4_12.candidate-terminal-preservation.v1"
RECEIPT_VERSION = "topolab.b4_12.recording.v1"
VOLUMES = (0.3379, 0.4729, 0.5439, 0.6039)
POSITIONS = previous.POSITIONS
CAPS = previous.CAPS
SOURCE_FILES = previous.SOURCE_FILES
DIAGNOSIS_FILES = previous.DIAGNOSIS_FILES
POLISH_FILES = {
    "audit_receipts/evidence_release.json": (
        "4b5d38eb6fbfabba5c7af69ce0000f85a4e0a2b204afc5a6ed50528747bd4752"
    ),
    "audit_receipts/plan.json": "19c866cf2edd7c3322aa4f4360745a7a30a0827bb49b904b9c3ff1df2d36c10a",
    "audit_receipts/production_release.json": (
        "18a8b09b39e9e45dfdb917ffe42c14d2e27d10d3b45838431513869d673a705f"
    ),
    "context.json": "30d732690a14d92ae4d7dd865c84eab06dd14a241de70225effadd46beec672a",
    "resource_close.json": "f95d29fca1fe9515de887892f888417ea17e5746ef07fe9923b584d7d2157c5d",
    "sentinel/audit/progress.json": (
        "f98a5c04412480bb92d5db4be32e5f26bba5efb8fe47efbd29b609d1deca2436"
    ),
    "sentinel/audit/summary.json": (
        "0ba791238a9ae5a54f49d205719d7730f31824fa91f02334f96ed730bb1e1a1d"
    ),
    "sentinel/independent_audit.json": (
        "9b888e761bf404010cf902bb4d5b0df1fef06233b13909b734f0b7268c050fa8"
    ),
    "sentinel/policy-audit/progress.json": (
        "71e052a0dabc6f5c3523c17096d753fa9b186285667b3abe6c33f0473dfdc20b"
    ),
    "sentinel/policy-audit/summary.json": (
        "063dce98cf700eb9c2b745d0b026fb2d47b3ca39a2a1054c514912c135f2e09e"
    ),
    "sentinel/reference/progress.json": (
        "d87ac44e28d8cfcba7f636a88eb4238e6f73e302f161e242e892fdccdf8eba3b"
    ),
    "sentinel/reference/summary.json": (
        "1a9fc1d43bb554a13e23ddcde2aa142f535046b3446aa4adf589a7c2b31d8fad"
    ),
    "sentinel/screen/progress.json": (
        "aa4eed9c1c5ef61c19db66f91464f85eec5d7e88ff249d68aad7d6899dc61e46"
    ),
    "sentinel/screen/summary.json": (
        "6680f57d0b80d8c785ad8378f64c2ce5cbf05596f70fccbedb711da1449336af"
    ),
}
REVIEW_FILES = {
    "audit_receipts/closure_profile_verification.json": (
        "19f26cef716a2d68818493d71d16afd5ba073d2169d06cea49ca235d1a30f6a0"
    ),
    "audit_receipts/plan.json": "21e078f4032302fab64499643523a84a29b6fb3b172db3bdf71e5074128decaf",
    "audit_receipts/production_release.json": (
        "135f1d2f0d1a45e63f855f5e9da049ae6d1568085bd82805289d2aa15b2751d6"
    ),
    "diagnosis.json": "48a539ae7f76c5203c1ca9edd364f98094e1d5107466c90acf9f7a7780851ef0",
    "independent_audit.json": "8fe367af68014406ef911b703b80d362ddb822c06469d7f21ad2f289c2d35cf3",
    "resource_close.json": "4839612170f235d9d594f3ee718ccb3668808374d33198120ffa5bf8ca892fdc",
}


def terminal_certificate(case: ExperimentCase, result: TopologyResult) -> bool:
    tolerance = case.problem.optimization.convergence_tolerance
    return bool(result.history) and (
        result.history[-1].density_change <= tolerance or plateau(result, tolerance)
    )


def select_terminal(case: ExperimentCase, before: TopologyResult, after: TopologyResult) -> str:
    """Choose only between the candidate's two witnesses, never a reference.

    All twenty updates are paid even when the original witness is selected.
    An incomplete continuation cannot be hidden by returning the earlier stop.
    """
    if not qualifies(case, before):
        return "endpoint"
    updates = after.history[-1].iteration - before.history[-1].iteration
    if updates != POLISH_UPDATES:
        return "endpoint"
    if after.history[-1].iteration > case.problem.optimization.max_iterations:
        raise ValueError("preservation cannot exceed the frozen update cap")
    if after.converged != terminal_certificate(case, after):
        raise ValueError("endpoint convergence flag differs from its own certificate")
    if after.converged:
        return "endpoint"
    settings = case.problem.optimization
    design, physical = np.asarray(before.design_density), np.asarray(before.physical_density)
    if (
        not np.isfinite(before.compliance)
        or not np.all(np.isfinite(design))
        or not np.all(np.isfinite(physical))
        or np.any(design < settings.minimum_density)
        or np.any(design > 1)
        or abs(float(np.mean(physical)) - settings.volume_fraction) > 0.005
    ):
        raise ValueError("original candidate is not a valid own terminal witness")
    return "original"


def sentinel_cases() -> tuple[ExperimentCase, ...]:
    return previous.sentinel_cases()


def fresh_cases() -> tuple[ExperimentCase, ...]:
    # Previous builder proves disjointness from the full historical/B3/B4 ledger.
    candidates = tuple(sorted(_grid(VOLUMES, POSITIONS, 360), key=lambda c: c.case_id))
    from topolab.b3_catalog import build_b3_case_catalog, build_b3_exposure_ledger
    from topolab.b4_confirmation import fresh_cases as confirmation
    from topolab.b4_rollback import fresh_cases as rollback
    from topolab.b4_rollback_confirmation import fresh_cases as rollback_confirmation
    from topolab.b4_weighted_terminal import fresh_cases as weighted

    blocked = {e.physical_fingerprint for e in build_b3_exposure_ledger().entries}
    blocked.update(e.physical_fingerprint for e in build_b3_case_catalog().entries)
    blocked.update(
        physical_fingerprint(c)
        for c in (
            *weighted(),
            *confirmation(),
            *rollback(),
            *rollback_confirmation(),
            *previous.fresh_cases(),
        )
    )
    fingerprints = {physical_fingerprint(c) for c in candidates}
    if len(candidates) != 48 or len(fingerprints) != 48 or fingerprints & blocked:
        raise ValueError("preservation cohort crosses a previous exposure or reserved panel")
    return candidates


def cases(cohort: str) -> tuple[ExperimentCase, ...]:
    if cohort not in ("sentinel", "fresh"):
        raise ValueError("unknown preservation cohort")
    return sentinel_cases() if cohort == "sentinel" else fresh_cases()


def assignments(cohort: str) -> tuple[tuple[str, str], ...]:
    rows: list[tuple[str, str]] = []
    other = METHODS[1:]
    for case in cases(cohort):
        # Retain the B4.10 salt so sentinel query order is unchanged.
        offset = int(digest((previous.VERSION + ":" + case.case_id).encode())[:8], 16) % len(other)
        rows.extend((case.case_id, m) for m in ("uniform", *other[offset:], *other[:offset]))
    return tuple(rows)


def plan() -> dict[str, Any]:
    value = previous.plan()
    value.pop("plan_sha256")
    value.update(
        version=VERSION,
        preservation_version=POLICY_VERSION,
        choice="original_only_after_full_twenty_and_endpoint_certificate_loss",
        cases={c: [x.model_dump(mode="json") for x in cases(c)] for c in ("sentinel", "fresh")},
        assignments={c: assignments(c) for c in ("sentinel", "fresh")},
        polish_files=POLISH_FILES,
        review_files=REVIEW_FILES,
        query_order_salt=previous.VERSION,
        resource_close_cap_seconds=180,
        closure_charge="full_180_second_reservation_with_post_exit_verification",
        old_fresh_panel_access=False,
    )
    return {**value, "plan_sha256": digest(canonical_metadata_bytes(value))}


def upstream_fits(root: Path) -> list[dict[str, Any]]:
    for sibling, bindings in (
        ("b4-10-post-plateau-polish", POLISH_FILES),
        ("b4-11-polish-diagnosis", REVIEW_FILES),
    ):
        for path, expected in bindings.items():
            raw = safe_path(root.parent / sibling, path).read_bytes()
            if digest(raw) != expected or canonical_metadata_bytes(json.loads(raw)) != raw:
                raise ValueError("preservation input receipt changed before model or label bytes")
    return previous.upstream_fits(root)


identity = previous.identity
sentinel_gate = previous.sentinel_gate


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
    for packet in retained:
        scale = (
            "small" if by_id[packet["case_id"]].problem.mesh.element_counts[0] == 12 else "large"
        )
        totals[packet["policy"]][scale] += packet["timing"]["wall_seconds"] + 1
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
