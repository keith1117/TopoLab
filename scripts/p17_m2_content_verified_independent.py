"""Independent acceptance of public content-verified preparation evidence.

Raw tool returns are supplied by the caller; producer summaries cannot replace them.
This module never authorizes scientific input or a formal role.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import platform
import secrets
import stat
import sys
import time
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Any

EXECUTION_IDENTITY = "topolab.v2.p17-m2-content-verified-input.v1"
PUBLIC_SCOPE = "PUBLIC_SOFTWARE_FIXTURE_ONLY"
FULL_SECONDS = {
    "independent-public-check": 300,
    "exporter-r0": 300,
    "independent-r0": 300,
    "exporter-r1": 1200,
    "independent-r1": 1200,
    "shared-closeout": 300,
    "final-filing": 180,
}


CLOCK = "functions.exec.Date.now.UTC-seconds"
ROLE_ORDER = [r for r in FULL_SECONDS if r != "final-filing"]


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require(condition: Any, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def number(value: Any, *, integer: bool = False, positive: bool = False) -> float | int:
    require(
        type(value) in ((int,) if integer else (int, float))
        and math.isfinite(value)
        and value >= 0
        and (not positive or value > 0),
        "invalid finite nonnegative measurement",
    )
    return value


def _window(record: dict[str, Any]) -> tuple[float, float]:
    start = number(record["actor_activation_UTC_seconds"], positive=True)
    require(
        round(start * 1000) / 1000 == start
        and type(record["actor_window_seconds"]) is int
        and record["actor_window_seconds"] == 4500,
        "immutable actor window differs",
    )
    end = start + 4500
    iso = datetime.fromtimestamp(end, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    require(
        record["actor_deadlines_UTC"] == {"exporter": iso, "independent": iso},
        "actor deadline differs",
    )
    return start, end


def _independent_module(name: str, filename: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    require(spec is not None and spec.loader is not None, "independent helper unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _independent_module(
    "content_verified_native_independent", "p17_m2_input_export_independent.py"
)


def audit_resources(
    completion: dict[str, Any],
    *,
    inner_evidence: dict[str, Any] | None,
    native_profiles: dict[str, bytes] | None,
    expected_identity: str = EXECUTION_IDENTITY,
) -> dict[str, Any]:
    """Reconcile each actual PID once; inherited native parsing is independent code."""
    result: dict[str, Any] = {
        "status": "STOP_NO_RETRY",
        "reason": None,
        "RSS_components_bytes": {},
        "RSS_envelope_bytes": None,
        "inner_minimum_charge_seconds": None,
        "actual_component_exit_codes": [],
    }
    inner, inner_problem = None, "UNKNOWN_MISSING_INNER_EVIDENCE"
    try:
        require(inner_evidence is not None, inner_problem)
        inner = base.audit_native_record(**inner_evidence, failure_recording=True)
        result["inner_minimum_charge_seconds"] = inner["inner_minimum_charge_seconds"]
        result["inner_record_sha256"] = inner["record_canonical_sha256"]
        result["inner_actual_exit_code"] = inner_evidence["record"]["exit_code"]
        result["RSS_components_bytes"]["independently_reconciled_inner"] = inner[
            "inner_empirical_RSS_bytes"
        ]
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        inner_problem = f"{type(error).__name__}: {error}"
    try:
        require(
            completion["execution_identity"] == expected_identity,
            "resource execution identity differs",
        )
        components = completion["resource_components"]
        require(
            isinstance(components, list)
            and len(components) == 4
            and sorted(i["kind"] for i in components)
            == ["native_profile", "self_high_water", "self_high_water", "wait4"],
            "UNKNOWN_INCOMPLETE_OUTER_INVENTORY",
        )
        peaks: dict[int, int] = {}
        names: set[str] = set()
        serializer_seen = False
        for item in components:
            pid = number(item["pid"], integer=True, positive=True)
            require(pid not in peaks, "duplicate outer PID")
            kind = item["kind"]
            if kind == "native_profile":
                name = item["profile"]
                require(
                    native_profiles is not None and name in native_profiles and name not in names,
                    "UNKNOWN_MISSING_NATIVE_PROFILE",
                )
                names.add(name)
                raw = native_profiles[name]
                require(item["profile_sha256"] == digest(raw), "native profile hash differs")
                peak = base.native_profile(raw, item["platform"])["rss_bytes"]
                code = item["actual_exit_code"]
            elif kind == "wait4":
                record = item["record"]
                require(
                    item["platform"] in ("darwin", "linux")
                    and record["statistics_source"] == "os.wait4"
                    and record["wall_source"] == "controller_monotonic_observed"
                    and record["pid"] == pid
                    and record["rss_unit"]
                    == ("bytes" if item["platform"] == "darwin" else "KiB*1024"),
                    "wait4 source/pid/units differ",
                )
                for key in ("wall_seconds", "user_seconds", "system_seconds"):
                    number(record["native"][key])
                peak = number(record["native"]["rss_bytes"], integer=True, positive=True)
                code = record["exit_code"]
            else:
                require(
                    item["statistics_source"] == "resource.getrusage"
                    and item["rss_unit"] == "bytes"
                    and item["phases"] == ["preflush", "postflush"]
                    and isinstance(item["samples_bytes"], list)
                    and len(item["samples_bytes"]) == 2,
                    "UNKNOWN_MISSING_SERIALIZER_RSS",
                )
                peak = max(number(v, integer=True, positive=True) for v in item["samples_bytes"])
                serializer_seen |= pid == completion["final_serializer_pid"]
                code = None
            peaks[pid] = peak
            result["RSS_components_bytes"][str(pid)] = peak
            if kind != "self_high_water":
                result["actual_component_exit_codes"].append(code)
        require(
            serializer_seen and set(native_profiles or {}) == names,
            "serializer/native inventory differs",
        )
        require(inner is not None, inner_problem)
        record = inner_evidence["record"]
        require(
            next(i["pid"] for i in components if i["kind"] == "native_profile")
            == record["controller_pid"],
            "native profile/controller PID differs",
        )
        result["inner_minimum_charge_seconds"] = inner["inner_minimum_charge_seconds"]
        result["inner_record_sha256"] = inner["record_canonical_sha256"]
        result["inner_actual_exit_code"] = record["exit_code"]
        result["RSS_components_bytes"]["independently_reconciled_inner"] = inner[
            "inner_empirical_RSS_bytes"
        ]
        result["RSS_envelope_bytes"] = sum(peaks.values()) + inner["inner_empirical_RSS_bytes"]
        hashes = {
            "inner_record_canonical_sha256": digest(canonical(record)),
            "inner_profile_sha256": digest(inner_evidence["profile"]),
            "inner_log_sha256": digest(inner_evidence["log"]),
            "helper_profiles_sha256": {
                name: digest(raw) for name, raw in inner_evidence["helper_profiles"].items()
            },
            "outer_profiles_sha256": {
                name: digest(raw) for name, raw in (native_profiles or {}).items()
            },
        }
        result["native_evidence_hashes"] = hashes
        require(
            completion.get("native_evidence_hashes") == hashes,
            "actual native evidence hash manifest differs",
        )
        base.stable_cleanup_checked(record["cleanup"], record["exit_code"])
        for helper in record["helpers"]:
            base.stable_cleanup_checked(helper["cleanup"], helper["exit_code"])
        base.stable_cleanup_checked(completion["cleanup"], record["exit_code"])
        require(
            all(type(c) is int for c in result["actual_component_exit_codes"]),
            "UNKNOWN_MISSING_NATIVE_EXIT",
        )
        watchdog = next(item for item in components if item["kind"] == "wait4")["record"].get(
            "watchdog_cleanup"
        )
        if watchdog is not None:
            # The extra watchdog sampler is outside the original four-component
            # envelope. Keep its known subtotal without claiming full accounting.
            result["known_RSS_sum_bytes"] = result["RSS_envelope_bytes"]
            result["RSS_envelope_bytes"] = None
            raise ValueError("UNKNOWN_UNRECONCILED_OUTER_WATCHDOG_RESOURCE")
        require(result["RSS_envelope_bytes"] <= 4294967296, "retained4GiB RSS cap exceeded")
        result["status"] = "PENDING_EXTERNAL_EXIT"
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        result["reason"] = f"{type(error).__name__}: {error}"
    return result


def _result_window(
    record: dict[str, Any], *, result_seconds: tuple[int, int] = (7200, 3600)
) -> tuple[float, float]:
    require(
        len(result_seconds) == 2 and all(type(v) is int and v > 0 for v in result_seconds),
        "invalid result window profile",
    )
    start = number(record["result_start_UTC_seconds"], positive=True)
    require(round(start * 1000) / 1000 == start, "result start clock resolution differs")
    expected = {
        actor: datetime.fromtimestamp(start + seconds, UTC)
        .isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
        for actor, seconds in zip(("exporter", "independent"), result_seconds, strict=True)
    }
    require(record["result_deadlines_UTC"] == expected, "immutable result deadlines differ")
    return start, start + min(result_seconds)


def evidence_digest(value: Any) -> str | None:
    try:
        return digest(canonical(value))
    except (TypeError, ValueError, OverflowError):
        return None


def _actual_record_return(
    pending: dict[str, Any], completion: dict[str, Any], events: list[dict[str, Any]]
) -> None:
    require(
        events[-1].get("observed_pending_sha256") == digest(canonical(pending))
        and events[-1].get("observed_completion_sha256") == digest(canonical(completion)),
        "actual record return does not bind supplied pending/completion",
    )


def audit_role(
    pending: dict[str, Any],
    completion: dict[str, Any],
    *,
    raw_tool_events: list[dict[str, Any]],
    expected_role: str,
    expected_plan_sha256: str,
    inner_evidence: dict[str, Any] | None = None,
    native_profiles: dict[str, bytes] | None = None,
    expected_identity: str = EXECUTION_IDENTITY,
    result_seconds: tuple[int, int] = (7200, 3600),
) -> dict[str, Any]:
    """Reconcile actual outer intervals independently and preserve failed cost facts."""
    cap = FULL_SECONDS.get(expected_role)
    result: dict[str, Any] = {
        "status": "STOP_NO_RETRY",
        "reason": "OUTER_RETURN_MISSING",
        "execution_identity": expected_identity,
        "role": expected_role,
        "plan_sha256": expected_plan_sha256,
        "pending_sha256": evidence_digest(pending),
        "completion_sha256": evidence_digest(completion),
        "whole_wall_seconds": None,
        "frozen_FULL_seconds": cap,
        "known_cost_lower_bound_seconds": cap,
        "full_role_evidence_accepted": False,
        "evidence_complete": False,
        "source_successor_admitted": False,
        "B_C_admission": False,
        "missing_evidence_cost": "UNKNOWN_NOT_ZERO",
        "RSS_envelope_bytes": None,
        "RSS_components_bytes": {},
        "inner_minimum_charge_seconds": None,
        "actual_exit_codes": [],
        "raw_tool_event_ids_and_hashes": [],
        "primary_failure": completion.get("primary_failure")
        if isinstance(completion, dict)
        else None,
        "secondary_failures": completion.get("secondary_failures", [])
        if isinstance(completion, dict)
        else [],
    }
    resources = audit_resources(
        completion,
        inner_evidence=inner_evidence,
        native_profiles=native_profiles,
        expected_identity=expected_identity,
    )
    result["resource_evidence"] = resources
    for key in ("RSS_envelope_bytes", "RSS_components_bytes", "inner_minimum_charge_seconds"):
        result[key] = resources[key]
    try:
        require(cap is not None, "unregistered role")
        require(
            isinstance(raw_tool_events, list)
            and raw_tool_events
            and all(isinstance(e, dict) for e in raw_tool_events),
            "OUTER_RETURN_MISSING",
        )
        first = number(raw_tool_events[0]["start_seconds"])
        last = number(raw_tool_events[-1]["end_seconds"])
        previous = first
        ids: set[str] = set()
        for event in raw_tool_events:
            start, end = number(event["start_seconds"]), number(event["end_seconds"])
            wall = number(event["wall_seconds"])
            require(
                isinstance(event["event_id"], str)
                and event["event_id"]
                and event["event_id"] not in ids,
                "OUTER duplicate/missing event identity",
            )
            ids.add(event["event_id"])
            require(
                event["clock_domain"] == CLOCK
                and previous <= start <= end <= last
                and wall <= end - start + 0.001
                and isinstance(event["argv"], list)
                and event["argv"]
                and all(isinstance(v, str) for v in event["argv"]),
                "OUTER clock/order/argv/native-wall differs",
            )
            previous = end
            result["actual_exit_codes"].append(event.get("exit_code"))
            result["raw_tool_event_ids_and_hashes"].append(
                {"event_id": event["event_id"], "sha256": digest(canonical(event))}
            )
        whole = last - first
        result.update(
            T0=first,
            T1=last,
            clock_domain=CLOCK,
            whole_wall_seconds=whole,
            known_cost_lower_bound_seconds=max(cap, math.ceil(whole + 10)),
        )
        minimum = resources["inner_minimum_charge_seconds"]
        if minimum is not None:
            result["known_cost_lower_bound_seconds"] = max(
                result["known_cost_lower_bound_seconds"], math.ceil(minimum)
            )
        window = (
            (lambda record: _result_window(record, result_seconds=result_seconds))
            if expected_role == "final-filing"
            else _window
        )
        activation, deadline = window(pending)
        if expected_role == "independent-public-check":
            require(
                first - activation <= 300 and deadline - first >= 4200,
                "first dispatch requires setup<=300 and remaining>=4200",
            )
        require(
            activation <= first <= last <= deadline,
            "actual role outside immutable result window"
            if expected_role == "final-filing"
            else "actual role outside immutable actor window",
        )
        require(
            pending["execution_identity"] == expected_identity
            and pending["role"] == expected_role
            and pending["plan_sha256"] == expected_plan_sha256
            and isinstance(expected_plan_sha256, str)
            and len(expected_plan_sha256) == 64
            and all(c in "0123456789abcdef" for c in expected_plan_sha256)
            and type(pending["frozen_FULL_seconds"]) is int
            and pending["frozen_FULL_seconds"] == cap
            and pending["clock_domain"] == CLOCK
            and pending["clock_resolution_seconds"] == 0.001,
            "identity/plan/FULL/external clock binding differs",
        )
        require(
            all(
                e.get("complete") is True and type(e.get("exit_code")) is int
                for e in raw_tool_events
            ),
            "OUTER actual final exit UNKNOWN",
        )
        if "external_argv" in pending:
            require(
                pending["external_argv"] == [e["argv"] for e in raw_tool_events],
                "OUTER literal argv differs",
            )
        require(isinstance(completion, dict), "completion must be an object")
        require(
            window(completion) == (activation, deadline)
            and all(
                completion.get(k) == pending[k]
                for k in (
                    "execution_identity",
                    "role",
                    "plan_sha256",
                    "frozen_FULL_seconds",
                    "clock_domain",
                    "clock_resolution_seconds",
                )
            )
            and completion["status"] == "PENDING_EXTERNAL_EXIT"
            and completion["pending_sha256"] == digest(canonical(pending)),
            "completion/pending identity binding differs",
        )
        _actual_record_return(pending, completion, raw_tool_events)
        require(
            inner_evidence is not None and inner_evidence["expected_role"] == expected_role,
            "actual native role differs from receipt role",
        )
        minimum = resources["inner_minimum_charge_seconds"]
        if minimum is not None:
            result["known_cost_lower_bound_seconds"] = max(
                result["known_cost_lower_bound_seconds"], math.ceil(minimum)
            )
        require(resources["status"] == "PENDING_EXTERNAL_EXIT", resources["reason"])
        require(
            minimum - 10 <= whole + 0.001,
            "actual outer interval cannot contain observed inner lifetime",
        )
        require(max(whole + 10, minimum) <= cap, "FAIL_FULL_NAMED_WALL_CHARGE_BINDING")
        result.update(evidence_complete=True, missing_evidence_cost=None)
        require(
            all(e["exit_code"] == 0 for e in raw_tool_events)
            and resources["inner_actual_exit_code"] == 0
            and all(c == 0 for c in resources["actual_component_exit_codes"])
            and completion.get("domain_status") == "PASS",
            "payload/domain/actual outer exit failure",
        )
        result.update(
            status="PASS_CONTENT_VERIFIED_PUBLIC_ROLE",
            reason=None,
            full_role_evidence_accepted=True,
        )
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        result["reason"] = f"{type(error).__name__}: {error}"
    return result


def public_root(root: Path) -> Path:
    """Lexical deny before stat/open: preparation owns new temporary fixtures only."""
    literal = Path(base.os.path.abspath(root))
    permitted = (Path("/private/tmp"), Path("/private/var/folders"), Path("/tmp"))
    require(
        any(literal.is_relative_to(parent) and literal != parent for parent in permitted),
        "only a new public temporary root is permitted",
    )
    return literal


def _capture_read_failure(
    error: BaseException, readers: dict[str, Any], stage: str, context: dict[str, Any]
) -> None:
    packet: dict[str, Any] = {
        "schema": "topolab.v2.m2-content-verified-independent-read-failure.v1",
        "execution_identity": EXECUTION_IDENTITY,
        "scope": PUBLIC_SCOPE,
        "stage": stage,
        "exception_type": type(error).__name__,
        "primary_reason": str(error),
        "readers": {},
        "helper_identity_relabelled": False,
        "secondary_errors": [],
        "missing_evidence_cost": "UNKNOWN_NOT_ZERO",
    }
    try:
        packet["supplied_context"] = deepcopy(context)
        for name, reader in readers.items():
            packet["readers"][name] = deepcopy(
                {
                    "attempts": len(reader.seen),
                    "used_bytes": reader.used,
                    "rows": reader.table,
                    "source_identities": reader.observations,
                    "source_facts": reader.source_facts,
                    "source_failures": reader.failures,
                }
            )
        expected = (
            {"source"}
            if stage == "independent_r0"
            else {"source", "backup"}
            if stage == "independent_prefix_backup"
            else {"source", "exports", "local_content"}
        )
        packet["reader_scopes_not_started"] = sorted(expected - set(readers))
    except BaseException as secondary:
        packet["secondary_errors"].append(
            {
                "stage": "independent_read_context_recording",
                "exception_type": type(secondary).__name__,
                "reason": str(secondary),
            }
        )
    try:
        error.independent_read_failure = packet
    except BaseException as secondary:
        error.add_note("independent context attachment failed: " + type(secondary).__name__)


def _checked_root(root: Path, *, root_guard: Any = None) -> dict[str, int]:
    root = public_root(root) if root_guard is None else root_guard(root)
    descriptor = base.nofollow_parent(root / ".root-identity")
    try:
        first = os.fstat(descriptor)
        require(
            stat.S_ISDIR(first.st_mode)
            and first.st_uid == os.geteuid()
            and stat.S_IMODE(first.st_mode) == 0o700,
            "private local root identity required",
        )
        closing = base.nofollow_parent(root / ".root-identity")
        try:
            require(_physical(first) == _physical(os.fstat(closing)), "local root identity changed")
        finally:
            os.close(closing)
        return _physical(first)
    finally:
        os.close(descriptor)


def _root_tuple(value: Any) -> dict[str, int]:
    require(
        isinstance(value, dict)
        and set(value) == {"st_dev", "st_ino", "st_size", "st_mtime_ns"}
        and all(type(v) is int and v >= 0 for v in value.values()),
        "local root identity tuple missing",
    )
    return value


def independent_r0(
    source: Path,
    contract: dict[str, Any],
    producer_registry: dict[str, Any],
    producer_rows: list[dict[str, Any]],
    public_source_identity: dict[str, str],
) -> dict[str, Any]:
    readers: dict[str, Any] = {}
    try:
        source = public_root(source)
        checker = _independent_module(
            "public_r0_private_independent", "p17_m2_input_export_independent.py"
        )
        require(
            set(public_source_identity) == {"B3_DATA_HASH", "CATALOG_HASH"}
            and all(
                isinstance(v, str) and base.SHA.fullmatch(v)
                for v in public_source_identity.values()
            ),
            "public source identity requires explicit fixture hashes",
        )
        require(
            contract["R0"]["embedded_B3_data_index_sha256"]
            == public_source_identity["B3_DATA_HASH"],
            "public source contract index binding differs",
        )
        # A fresh private helper instance checks new public bytes. No old global identity changes.
        checker.B3_DATA_HASH = public_source_identity["B3_DATA_HASH"]
        checker.CATALOG_HASH = public_source_identity["CATALOG_HASH"]
        reader = checker.OnceReader(source, 40, 32 * base.MIB, source_identity_checks=True)
        readers["source"] = reader
        registry = checker.build_registry(reader, contract)
        checker.check_registry_shape(registry, contract)
        compared = checker.compare_words(registry, producer_registry)
        local = _independent_module(
            "public_r0_local_independent", "p17_m2_local_input_independent.py"
        )
        own = local.identity_table(reader.observations, 40)
        producer = local.identity_table(producer_rows, 40)
        checker.compare_words(own, producer)
        return {
            "status": "PUBLIC_INDEPENDENT_R0_CHECKED",
            "execution_identity": EXECUTION_IDENTITY,
            "scope": PUBLIC_SCOPE,
            "root": str(source),
            "source_count": 40,
            "source_rows": reader.observations,
            "source_registry_sha256": digest(canonical(registry)),
            "source_contract_sha256": digest(canonical(contract)),
            "public_source_identity": public_source_identity,
            "compared_fields": compared,
            "source_comparison": "ALL_FIELDS_AND_PHYSICAL_TUPLES_MATCHED",
            "helper_identity_relabelled": False,
            "helper_native_execution_identity": checker.EXECUTION_STABLE,
            "formal_or_scientific_admission": False,
            "B_C_admission": False,
        }
    except BaseException as error:
        context = {"producer_source_rows": producer_rows}
        _capture_read_failure(error, readers, "independent_r0", context)
        raise


def independent_r1(
    source: Path,
    content: Path,
    registry: dict[str, Any],
    producer_rows: list[dict[str, Any]],
    closed: dict[str, Any],
    contract_sha: str,
    public_source_identity: dict[str, str],
) -> dict[str, Any]:
    readers: dict[str, Any] = {}
    try:
        source, content = public_root(source), public_root(content)
        root_observations = {
            "declared": closed.get("root_identity"),
            "before": None,
            "after": None,
            "closing": None,
        }
        root_observations["before"] = _checked_root(content)
        require(
            root_observations["before"] == _root_tuple(closed.get("root_identity")),
            "frozen local root identity changed",
        )
        require(source != content, "source and local content roots must be distinct")
        require(
            set(public_source_identity) == {"B3_DATA_HASH", "CATALOG_HASH"}
            and all(
                isinstance(v, str) and base.SHA.fullmatch(v)
                for v in public_source_identity.values()
            ),
            "public source identity requires explicit fixture hashes",
        )
        checker = _independent_module(
            "public_r1_private_independent", "p17_m2_input_export_independent.py"
        )
        original = checker.OnceReader(source, 558, 852 * base.MIB, source_identity_checks=True)
        readers["source"] = original
        exported = checker.OnceReader(content, 1070, 301 * base.MIB)
        readers["exports"] = exported
        compared = checker.audit_exports(original, exported, registry)
        local = _independent_module(
            "public_r1_local_independent", "p17_m2_local_input_independent.py"
        )
        checker.compare_words(
            local.identity_table(original.observations, 558),
            local.identity_table(producer_rows, 558),
        )
        constructor = local.base.OnceReader

        def observed_local_reader(*args: Any, **kwargs: Any) -> Any:
            instance = constructor(*args, **kwargs)
            readers["local_content"] = instance
            return instance

        local.base.OnceReader = observed_local_reader
        checked = local.audit_local_content(
            content, closed["manifest"], registry, closed["local_identity_rows"], contract_sha
        )
        root_observations["after"] = _checked_root(content)
        root_observations["closing"] = _checked_root(content)
        require(
            root_observations["declared"]
            == root_observations["after"]
            == root_observations["closing"],
            "local root identity changed during independent comparison",
        )
        require(closed["version_id"] == checked["version_id"], "local version differs")
        return {
            "status": "PUBLIC_INDEPENDENT_R1_CHECKED",
            "execution_identity": EXECUTION_IDENTITY,
            "scope": PUBLIC_SCOPE,
            "source_root": str(source),
            "root": str(content),
            "root_identity": root_observations["closing"],
            "source_count": 558,
            "source_rows": original.observations,
            "local_identity_rows": checked["local_identity_rows"],
            "source_registry_sha256": digest(canonical(registry)),
            "manifest_sha256": digest(canonical(closed["manifest"])),
            "version_id": checked["version_id"],
            "contract_sha256": contract_sha,
            "public_source_identity": public_source_identity,
            "compared_fields": compared["compared_scalar_fields"],
            "source_comparison": "ALL_FIELDS_AND_PHYSICAL_TUPLES_MATCHED",
            "helper_identity_relabelled": False,
            "helper_native_execution_identity": checker.EXECUTION_STABLE,
            "formal_or_scientific_admission": False,
            "B_C_admission": False,
        }
    except BaseException as error:
        context = {"producer_source_rows": producer_rows}
        context["expected_local_rows"] = (
            closed.get("local_identity_rows") if isinstance(closed, dict) else None
        )
        context["expected_root_identity"] = (
            closed.get("root_identity") if isinstance(closed, dict) else None
        )
        context["root_observations"] = locals().get("root_observations")
        _capture_read_failure(error, readers, "independent_r1", context)
        raise


_CHECKED_AUTHORITY = object()


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _physical(info: Any) -> dict[str, int]:
    return {key: getattr(info, key) for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")}


def _private_file(info: Any) -> None:
    require(
        stat.S_ISREG(info.st_mode)
        and info.st_uid == os.geteuid()
        and stat.S_IMODE(info.st_mode) == 0o600
        and info.st_nlink == 1,
        "reader lease must be a private single-link regular file",
    )


def _lease_read(directory: int, name: str, fd: int) -> tuple[bytes, dict[str, int]]:
    before = os.fstat(fd)
    _private_file(before)
    require(0 < before.st_size <= 65536, "reader lease bounded metadata length")
    os.lseek(fd, 0, os.SEEK_SET)
    raw = bytearray()
    while len(raw) <= before.st_size:
        block = os.read(fd, min(65536, before.st_size + 1 - len(raw)))
        if not block:
            break
        raw.extend(block)
    after = os.fstat(fd)
    closing = os.stat(name, dir_fd=directory, follow_symlinks=False)
    require(
        _physical(before) == _physical(after) == _physical(closing) and len(raw) == before.st_size,
        "reader lease identity or length changed",
    )
    return bytes(raw), _physical(before)


class CheckedReaderLease:
    """Live public-reader capability; its pending receipt can only be acknowledged."""

    __slots__ = ("_certificate", "_record", "_raw", "_identity", "_fd", "_directory", "_handed_off")

    def __init__(
        self,
        certificate: Any,
        record: dict[str, Any],
        fd: int,
        directory: int,
        *,
        _authority: Any = None,
    ):
        require(_authority is _CHECKED_AUTHORITY, "reader lease requires actual acquisition")
        self._certificate, self._record = certificate, record
        self._raw, self._identity = _lease_read(directory, Path(record["lease_path"]).name, fd)
        self._fd, self._directory, self._handed_off = fd, directory, False

    @property
    def token(self) -> str:
        return self._record["token"]

    @property
    def path(self) -> str:
        return self._record["lease_path"]

    @property
    def state(self) -> str:
        return "PENDING_ACTUAL_OUTER_RETURN" if self._handed_off else "HELD"

    def _assert_held(self, certificate: Any, role: str) -> None:
        require(
            self._certificate is certificate
            and not self._handed_off
            and self._record["role"] == role,
            "active same-certificate reader lease required",
        )
        directory = base.nofollow_parent(Path(self.path))
        try:
            current, original = os.fstat(directory), os.fstat(self._directory)
            require(
                (current.st_dev, current.st_ino) == (original.st_dev, original.st_ino),
                "reader lease parent replaced",
            )
        finally:
            os.close(directory)
        raw, identity = _lease_read(self._directory, Path(self.path).name, self._fd)
        require(
            raw == self._raw and identity == self._identity, "reader lease physical/content changed"
        )

    def pending_return(self) -> dict[str, Any]:
        self._assert_held(self._certificate, self._record["role"])
        receipt = dict(
            self._record,
            status="PENDING_ACTUAL_OUTER_RETURN",
            lease_identity=self._identity,
            lease_record_sha256=digest(self._raw),
        )
        self._handed_off = True
        os.close(self._fd)
        os.close(self._directory)
        self._fd = self._directory = -1
        return deepcopy(receipt)

    def __reduce_ex__(self, protocol: int) -> Any:
        raise TypeError(
            "live reader lease cannot be serialized; only pending ack metadata may cross processes"
        )

    def __del__(self) -> None:
        for name in ("_fd", "_directory"):
            descriptor = getattr(self, name, -1)
            if descriptor >= 0:
                os.close(descriptor)
                setattr(self, name, -1)


class CheckedPublicInput:
    """Process-local independently audited public capability, never a serialized PASS."""

    __slots__ = ("_binding", "_readonly_binding", "_certificate_id", "_reader_failed")

    def __init__(self, binding: dict[str, Any], *, _authority: Any = None):
        require(_authority is _CHECKED_AUTHORITY, "certificate requires independent verification")
        self._binding = deepcopy(binding)
        self._readonly_binding = _freeze(self._binding)
        self._certificate_id = digest(
            canonical(
                {
                    key: binding[key]
                    for key in (
                        "root",
                        "root_identity",
                        "version_id",
                        "contract_sha256",
                        "plan_sha256",
                        "shared_packet_sha256",
                    )
                }
            )
        )
        self._reader_failed = False

    def __reduce_ex__(self, protocol: int) -> Any:
        raise TypeError(
            "checked certificate cannot be serialized; replay the actual evidence bundle"
        )

    def _reader_identity(self) -> str:
        return EXECUTION_IDENTITY

    def _reader_scope(self) -> str:
        return PUBLIC_SCOPE

    def _reader_result_seconds(self) -> tuple[int, int]:
        return (7200, 3600)

    def _reader_schema(self) -> str:
        return "topolab.v2.m2-content-verified-public-reader-lease.v1"

    def _reader_ack_status(self) -> str:
        return "PUBLIC_READER_RETURN_ACKNOWLEDGED"

    def _reader_source_digest(self) -> str:
        return digest(Path(__file__).read_bytes())

    def _reader_root(self, root: Path) -> Path:
        return public_root(root)

    def _reader_root_identity(self, root: Path) -> dict[str, int]:
        return _checked_root(root)

    def _reader_argv(self, action: str, role: str) -> list[str]:
        require(not self._reader_failed, "STOP_NO_RETRY: public reader already failed")
        require(
            role in self._binding["role_views"],
            "public role or reader lease unavailable",
        )
        words = self._binding["metadata_actions"][action]["argv"]
        return [
            word.replace("@PLAN_SHA256@", self._binding["plan_sha256"]).replace(
                "@READER_ROLE@", role
            )
            for word in words
        ]

    def acquire_reader(self, role: str) -> CheckedReaderLease:
        argv = self._reader_argv("public-consumer", role)
        require(getattr(sys, "orig_argv", None) == argv, "actual public reader orig_argv differs")
        require(
            self._reader_source_digest() == self._binding["independent_source_sha256"],
            "reader verifier source freeze changed",
        )
        root = self._reader_root(Path(self._binding["root"]))
        require(
            self._reader_root_identity(root) == self._binding["root_identity"],
            "reader local root identity changed",
        )
        path = root.with_name(root.name + ".cooperative-reader.lease")
        directory = base.nofollow_parent(path)
        info = os.fstat(directory)
        require(
            info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700,
            "reader lease parent is not private",
        )
        fd = -1
        try:
            fd = os.open(
                path.name,
                os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=directory,
            )
            record = {
                "schema": self._reader_schema(),
                "scope": self._reader_scope(),
                "execution_identity": self._reader_identity(),
                "root": str(root),
                "version_id": self._binding["version_id"],
                "root_identity": self._binding["root_identity"],
                "role": role,
                "certificate_binding_sha256": self._certificate_id,
                "token": secrets.token_hex(32),
                "lease_path": str(path),
                "consumer_pid": os.getpid(),
                "consumer_orig_argv": argv,
                "independent_source_sha256": self._binding["independent_source_sha256"],
                "acquired_UTC_seconds": time.time(),
                "acquired_monotonic": time.monotonic(),
            }
            raw = canonical(record)
            require(len(raw) <= 65536 and os.write(fd, raw) == len(raw), "reader lease short write")
            os.fsync(fd)
            os.fsync(directory)
            return CheckedReaderLease(self, record, fd, directory, _authority=_CHECKED_AUTHORITY)
        except FileExistsError as error:
            os.close(directory)
            raise ValueError("cooperative reader lease already held") from error
        except BaseException:
            self._reader_failed = True
            if fd >= 0:
                os.close(fd)
            os.close(directory)
            raise

    def binding_for(self, role: str, *, reader_lease: Any = None) -> Any:
        require(not self._reader_failed, "STOP_NO_RETRY: public reader already failed")
        require(isinstance(reader_lease, CheckedReaderLease), "actual opaque reader lease required")
        reader_lease._assert_held(self, role)
        require(
            self._reader_root_identity(Path(self._binding["root"]))
            == self._binding["root_identity"],
            "reader local root identity changed",
        )
        return self._readonly_binding

    def stop_reader(self, role: str, *, reader_lease: Any = None) -> None:
        """Latch a failed read before cleanup can itself fail; never reopen its path."""
        require(
            isinstance(reader_lease, CheckedReaderLease)
            and reader_lease._certificate is self
            and reader_lease._record["role"] == role,
            "same certificate/role opaque reader lease required for STOP",
        )
        self._reader_failed = True

    def acknowledge_returned_reader(
        self, receipt: dict[str, Any], trusted_return: dict[str, Any]
    ) -> dict[str, Any]:
        require(
            isinstance(receipt, dict)
            and isinstance(trusted_return, dict)
            and "wire" in trusted_return
            and "raw_tool_events" in trusted_return,
            "actual complete reader return/resource facts required",
        )
        role = receipt["role"]
        require(
            getattr(sys, "orig_argv", None) == self._reader_argv("reader-ack", role),
            "actual reader ack orig_argv differs",
        )
        require(
            receipt["status"] == "PENDING_ACTUAL_OUTER_RETURN"
            and receipt["scope"] == self._reader_scope()
            and receipt["execution_identity"] == self._reader_identity()
            and receipt["certificate_binding_sha256"] == self._certificate_id
            and receipt["root"] == self._binding["root"]
            and receipt["version_id"] == self._binding["version_id"]
            and receipt["root_identity"] == self._binding["root_identity"]
            and receipt["consumer_orig_argv"] == self._reader_argv("public-consumer", role)
            and receipt["independent_source_sha256"] == self._binding["independent_source_sha256"]
            and type(receipt["consumer_pid"]) is int
            and receipt["consumer_pid"] > 0,
            "returned reader certificate/role/source binding differs",
        )
        wire = trusted_return["wire"]
        require(
            wire["inner_evidence"]["log"] == canonical(receipt),
            "receipt not bound to actual native reader stdout",
        )
        observed = audit_metadata(
            wire,
            raw_tool_events=trusted_return["raw_tool_events"],
            plan_sha256=self._binding["plan_sha256"],
            expected_argv=self._reader_argv("public-consumer", role),
            expected_role="public-consumer",
            expected_identity=self._reader_identity(),
            result_seconds=self._reader_result_seconds(),
        )
        require(observed["metadata_evidence_accepted"] is True, str(observed.get("reason")))
        require(
            observed["T0"]
            <= number(receipt["acquired_UTC_seconds"], positive=True)
            <= observed["T1"],
            "actual reader return does not cover lease acquisition",
        )
        path = Path(self._binding["root"]).with_name(
            Path(self._binding["root"]).name + ".cooperative-reader.lease"
        )
        require(receipt["lease_path"] == str(path), "returned lease path differs")
        directory = base.nofollow_parent(path)
        fd = -1
        try:
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
            raw, physical = _lease_read(directory, path.name, fd)
            require(
                physical == receipt["lease_identity"]
                and digest(raw) == receipt["lease_record_sha256"],
                "returned reader lease physical/content differs",
            )
            record = base.parse(raw, canonical_required=True)
            require(
                dict(
                    record,
                    status="PENDING_ACTUAL_OUTER_RETURN",
                    lease_identity=physical,
                    lease_record_sha256=digest(raw),
                )
                == receipt,
                "returned reader metadata differs from actual held lease",
            )
            os.unlink(path.name, dir_fd=directory)
            os.fsync(directory)
        except BaseException:
            self._reader_failed = True
            raise
        finally:
            if fd >= 0:
                os.close(fd)
            os.close(directory)
        return {
            "status": self._reader_ack_status(),
            "scope": self._reader_scope(),
            "consumer_actual_exit_observed": True,
            "token": receipt["token"],
            "lease_state": "RELEASED",
            "released_UTC_seconds": time.time(),
            "reader_receipt_sha256": digest(canonical(receipt)),
            "reader_cost": observed,
            "ack_own_future_exit": "UNKNOWN_PENDING_ACTUAL_OUTER_RETURN",
            "formal_or_scientific_admission": False,
            "B_C_admission": False,
        }


def resolved_argv(plan: dict[str, Any], role: str, plan_sha: str) -> list[str]:
    table = plan["roles"] if role in ROLE_ORDER else plan["metadata_actions"]
    words = table[role]["argv"]
    require(
        isinstance(words, list) and words and all(isinstance(w, str) for w in words),
        "frozen role argv missing",
    )
    return [word.replace("@PLAN_SHA256@", plan_sha) for word in words]


def _proof(
    wire: dict[str, Any],
    expected_status: str,
    *,
    expected_identity: str = EXECUTION_IDENTITY,
    expected_scope: str = PUBLIC_SCOPE,
) -> dict[str, Any]:
    raw = wire["inner_evidence"]["log"]
    require(isinstance(raw, bytes) and 0 < len(raw) <= 16 * base.MIB, "actual proof log missing")
    proof = base.parse(raw, canonical_required=True)
    require(
        isinstance(proof, dict)
        and proof.get("status") == expected_status
        and proof.get("execution_identity") == expected_identity
        and proof.get("scope") == expected_scope
        and proof.get("B_C_admission") is False,
        "actual independent proof scope/status differs",
    )
    return proof


def _raw_metadata_return(events: list[dict[str, Any]]) -> tuple[float, float]:
    require(
        isinstance(events, list) and events and all(isinstance(e, dict) for e in events),
        "actual metadata return missing",
    )
    first, last = number(events[0]["start_seconds"]), number(events[-1]["end_seconds"])
    previous, ids = first, set()
    for event in events:
        start, end = number(event["start_seconds"]), number(event["end_seconds"])
        wall = number(event["wall_seconds"])
        require(
            isinstance(event["event_id"], str)
            and event["event_id"]
            and event["event_id"] not in ids
            and previous <= start <= end <= last
            and event["clock_domain"] == CLOCK
            and wall <= end - start + 0.001
            and isinstance(event["argv"], list)
            and event["argv"]
            and all(isinstance(w, str) for w in event["argv"]),
            "actual metadata clock/order/argv differs",
        )
        ids.add(event["event_id"])
        previous = end
    return first, last


def audit_metadata(
    wire: dict[str, Any],
    *,
    raw_tool_events: list[dict[str, Any]],
    plan_sha256: str,
    expected_argv: list[str],
    expected_role: str,
    expected_identity: str = EXECUTION_IDENTITY,
    result_seconds: tuple[int, int] = (7200, 3600),
) -> dict[str, Any]:
    """Audit actual metadata lifetime with no formal FULL or new allowance."""
    result: dict[str, Any] = {
        "status": "STOP_NO_RETRY",
        "reason": None,
        "role": expected_role,
        "frozen_FULL_seconds": None,
        "T0": None,
        "T1": None,
        "whole_wall_seconds": None,
        "known_cost_lower_bound_seconds": None,
        "missing_evidence_cost": "UNKNOWN_NOT_ZERO",
        "metadata_evidence_accepted": False,
        "full_role_evidence_accepted": False,
        "formal_role_or_new_allowance": False,
        "B_C_admission": False,
    }
    try:
        require(
            expected_role in ("lease-release", "public-consumer", "reader-ack"),
            "unregistered public metadata action",
        )
        first, last = _raw_metadata_return(raw_tool_events)
        whole = last - first
        result.update(
            T0=first,
            T1=last,
            whole_wall_seconds=whole,
            known_cost_lower_bound_seconds=math.ceil(whole + 10),
            actual_exit_codes=[e.get("exit_code") for e in raw_tool_events],
        )
        pending, completion = wire["pending"], wire["completion"]
        resources = audit_resources(
            completion,
            inner_evidence=wire["inner_evidence"],
            native_profiles=wire["native_profiles"],
            expected_identity=expected_identity,
        )
        result["resource_evidence"] = resources
        result.update(
            pending_sha256=evidence_digest(pending),
            completion_sha256=evidence_digest(completion),
        )
        minimum = resources["inner_minimum_charge_seconds"]
        if minimum is not None:
            result["known_cost_lower_bound_seconds"] = max(
                result["known_cost_lower_bound_seconds"], math.ceil(minimum)
            )
        _actual_record_return(pending, completion, raw_tool_events)
        require(resources["status"] == "PENDING_EXTERNAL_EXIT", resources["reason"])
        require(
            minimum - 10 <= whole + 0.001,
            "actual outer metadata interval cannot contain observed inner lifetime",
        )
        for item in (pending, completion):
            require(
                item["execution_identity"] == expected_identity
                and item["role"] == expected_role
                and item["plan_sha256"] == plan_sha256
                and item["frozen_FULL_seconds"] is None
                and item["clock_domain"] == CLOCK
                and item["clock_resolution_seconds"] == 0.001,
                "metadata identity/clock binding differs; no formal FULL is granted",
            )
        require(
            completion["pending_sha256"] == digest(canonical(pending))
            and completion["status"] == "PENDING_EXTERNAL_EXIT"
            and completion.get("domain_status") == "PASS"
            and wire["inner_evidence"]["expected_argv"] == expected_argv
            and wire["inner_evidence"]["expected_role"] == expected_role
            and resources["inner_actual_exit_code"] == 0
            and all(c == 0 for c in resources["actual_component_exit_codes"])
            and all(
                e.get("complete") is True
                and type(e.get("exit_code")) is int
                and e["exit_code"] == 0
                for e in raw_tool_events
            ),
            "metadata actual process/pending/domain differs",
        )
        if "external_argv" in pending:
            require(
                pending["external_argv"] == [e["argv"] for e in raw_tool_events],
                "metadata actual outer argv differs",
            )
        result.update(
            status="PUBLIC_METADATA_ACTION_OBSERVED",
            metadata_evidence_accepted=True,
            missing_evidence_cost=None,
        )
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        result["reason"] = f"{type(error).__name__}: {error}"
    return result


def audit_release(
    wire: dict[str, Any],
    *,
    raw_tool_events: list[dict[str, Any]],
    plan_sha256: str,
    expected_argv: list[str],
    expected_identity: str = EXECUTION_IDENTITY,
    result_seconds: tuple[int, int] = (7200, 3600),
) -> dict[str, Any]:
    return audit_metadata(
        wire,
        raw_tool_events=raw_tool_events,
        plan_sha256=plan_sha256,
        expected_argv=expected_argv,
        expected_role="lease-release",
        expected_identity=expected_identity,
        result_seconds=result_seconds,
    )


def _closed_wait4(value: dict[str, Any], pid: int, code: int) -> None:
    require(
        type(code) is int
        and type(pid) is int
        and pid > 0
        and value["statistics_source"] == "os.wait4"
        and value["wall_source"] == "controller_monotonic_observed"
        and value["pid"] == pid
        and type(value["exit_code"]) is int
        and value["exit_code"] == code,
        "actual native exit UNKNOWN/different",
    )


def _closed_outer_watchdog(record: dict[str, Any]) -> None:
    """A closed inner command cannot prove its outer watchdog's cleanup."""
    watchdog = record.get("watchdog_cleanup")
    if watchdog is None:
        return
    base.stable_cleanup_checked(watchdog, record["exit_code"])
    helper = watchdog["helper"]
    require(
        isinstance(helper, dict) and helper["problem"] is None and helper["exit_code"] == 0,
        "outer watchdog sampler UNKNOWN",
    )
    _closed_wait4(helper["timer_native_exit"], helper["pid"], helper["exit_code"])
    base.stable_cleanup_checked(helper["cleanup"], helper["exit_code"])
    rows = watchdog["observed"]
    require(isinstance(rows, list), "outer watchdog observed inventory UNKNOWN")
    seen: set[int] = set()
    for row in rows:
        pid = number(row["pid"], integer=True, positive=True)
        number(row["parent"], integer=True)
        number(row["pgid"], integer=True, positive=True)
        number(row["rss_bytes"], integer=True)
        require(pid not in seen, "outer watchdog duplicate observed PID")
        seen.add(pid)
    own = {record["pid"]}
    while True:
        children = {
            row["pid"] for row in rows if row["parent"] in own or row["pgid"] == record["pid"]
        }
        if children <= own:
            break
        own.update(children)
    require(seen <= own, "outer watchdog observed process outside owned launch")
    expected = {row["pgid"] for row in rows} - {record["pid"]}
    groups = watchdog["descendant_groups"]
    require(
        isinstance(groups, list)
        and len(groups) == len(expected)
        and {item["pgid"] for item in groups} == expected,
        "outer watchdog descendant cleanup inventory UNKNOWN/different",
    )
    for item in groups:
        require(
            item["observed_pids"]
            == sorted(row["pid"] for row in rows if row["pgid"] == item["pgid"])
            and item["group_gone"] is True
            and isinstance(item["signals"], list)
            and all(isinstance(signal, str) for signal in item["signals"]),
            "outer watchdog descendant group not closed",
        )
        observations = item["observations"]
        require(
            isinstance(observations, list) and observations,
            "outer watchdog descendant observations UNKNOWN",
        )
        previous = 0.0
        for observation in observations:
            elapsed = number(observation["elapsed_seconds"])
            require(
                previous <= elapsed <= 5 and type(observation["group_gone"]) is bool,
                "outer watchdog descendant observation UNKNOWN/out of order",
            )
            previous = elapsed
        require(
            observations[-1]["group_gone"] is True,
            "outer watchdog descendant final observation not gone",
        )
    require(
        isinstance(watchdog["secondary_failures"], list),
        "outer watchdog secondary failures not retained",
    )


def check_closed_attempt(
    wire: dict[str, Any],
    *,
    raw_tool_events: list[dict[str, Any]],
    expected_role: str,
    expected_plan_sha256: str,
    expected_argv: list[str],
    expected_identity: str = EXECUTION_IDENTITY,
    result_seconds: tuple[int, int] = (7200, 3600),
) -> dict[str, Any]:
    """Prove returned registered groups for the one STOP archive, never role PASS.

    RSS may remain UNKNOWN or over cap: that failure must not block the already
    prepaid NEW-only closeout once exits and cleanup are independently known.
    """
    cap = FULL_SECONDS.get(expected_role)
    result: dict[str, Any] = {
        "status": "STOP_NO_RETRY",
        "reason": None,
        "closed_attempt_verified": False,
        "full_role_evidence_accepted": False,
        "input_version_accepted": False,
        "formal_or_scientific_admission": False,
        "B_C_admission": False,
        "frozen_FULL_seconds": cap,
        "whole_wall_seconds": None,
        "known_cost_lower_bound_seconds": cap,
        "missing_evidence_cost": "UNKNOWN_NOT_ZERO",
    }
    try:
        require(
            expected_role in FULL_SECONDS
            or expected_role in {"lease-release", "public-consumer", "reader-ack"},
            "unregistered returned-attempt action",
        )
        first, last = _raw_metadata_return(raw_tool_events)
        whole = last - first
        result.update(
            T0=first,
            T1=last,
            whole_wall_seconds=whole,
            known_cost_lower_bound_seconds=max(cap or 0, math.ceil(whole + 10)),
        )
        pending, completion = wire["pending"], wire["completion"]
        resources = audit_resources(
            completion,
            inner_evidence=wire["inner_evidence"],
            native_profiles=wire["native_profiles"],
            expected_identity=expected_identity,
        )
        result["resource_evidence"] = resources
        minimum = resources["inner_minimum_charge_seconds"]
        if minimum is not None:
            result["known_cost_lower_bound_seconds"] = max(
                result["known_cost_lower_bound_seconds"], math.ceil(minimum)
            )
        _actual_record_return(pending, completion, raw_tool_events)
        require(
            all(
                event.get("complete") is True and type(event.get("exit_code")) is int
                for event in raw_tool_events
            ),
            "actual outer native exit UNKNOWN",
        )
        window = (
            (lambda record: _result_window(record, result_seconds=result_seconds))
            if expected_role == "final-filing"
            else _window
        )
        require(window(pending) == window(completion), "closed attempt immutable window differs")
        for item in (pending, completion):
            require(
                item["execution_identity"] == expected_identity
                and item["role"] == expected_role
                and item["plan_sha256"] == expected_plan_sha256
                and (
                    item["frozen_FULL_seconds"] is None
                    if cap is None
                    else type(item["frozen_FULL_seconds"]) is int
                )
                and item["frozen_FULL_seconds"] == cap
                and item["clock_domain"] == CLOCK
                and item["clock_resolution_seconds"] == 0.001
                and isinstance(expected_plan_sha256, str)
                and base.SHA.fullmatch(expected_plan_sha256),
                "closed attempt identity/FULL/clock binding differs",
            )
        require(
            completion["pending_sha256"] == digest(canonical(pending)),
            "closed attempt pending binding differs",
        )
        if "external_argv" in pending:
            require(
                pending["external_argv"] == [event["argv"] for event in raw_tool_events],
                "closed attempt literal outer argv differs",
            )
        inner, profiles = wire["inner_evidence"], wire["native_profiles"]
        record = inner["record"]
        hashes = {
            "inner_record_canonical_sha256": digest(canonical(record)),
            "inner_profile_sha256": digest(inner["profile"]),
            "inner_log_sha256": digest(inner["log"]),
            "helper_profiles_sha256": {
                name: digest(raw) for name, raw in inner["helper_profiles"].items()
            },
            "outer_profiles_sha256": {name: digest(raw) for name, raw in profiles.items()},
        }
        require(
            completion.get("native_evidence_hashes") == hashes,
            "closed attempt actual native evidence manifest differs",
        )
        require(
            record["schema"] == "topolab.v2.m2-native-rss-exit-assurance.v1"
            and record["status"] == "PENDING_POSTEXIT"
            and inner["expected_role"] == record["role"] == expected_role
            and inner["expected_argv"] == record["argv"] == expected_argv
            and record["software_only"] is True
            and record["scientific_resource_admission"] == "NOT_RUN"
            and record["platform"] == inner["platform"] in {"darwin", "linux"},
            "closed registered native identity differs",
        )
        _closed_wait4(record["timer_native_exit"], record["pid"], record["exit_code"])
        base.stable_cleanup_checked(record["cleanup"], record["exit_code"])
        base.stable_cleanup_checked(completion["cleanup"], record["exit_code"])
        require(
            record["profile_sha256"] == digest(inner["profile"])
            and record["log_sha256"] == digest(inner["log"]),
            "closed inner raw profile/log differs",
        )
        elapsed = number(record["observed_outer_wall_seconds"])
        result["known_cost_lower_bound_seconds"] = max(
            result["known_cost_lower_bound_seconds"], math.ceil(elapsed + 10)
        )
        require(
            elapsed <= whole + 0.001,
            "actual outer interval cannot contain observed closed inner lifetime",
        )
        helpers, samples = record["helpers"], record["samples"]
        require(
            isinstance(helpers, list)
            and isinstance(samples, list)
            and len(helpers) == len(samples)
            and set(inner["helper_profiles"]) == {f"sampler-{i}.time" for i in range(len(helpers))},
            "closed registered helper inventory differs",
        )
        helper_pids: set[int] = set()
        for index, helper in enumerate(helpers):
            name = f"sampler-{index}.time"
            require(
                helper["profile"] == name
                and helper["role"] == f"rss-sampler-{index}"
                and helper["profile_sha256"] == digest(inner["helper_profiles"][name])
                and helper["pid"] not in helper_pids,
                "closed helper identity/raw profile differs",
            )
            helper_pids.add(helper["pid"])
            _closed_wait4(helper["timer_native_exit"], helper["pid"], helper["exit_code"])
            base.stable_cleanup_checked(helper["cleanup"], helper["exit_code"])
        for sample in samples:
            rows = sample["roles"]
            require(
                isinstance(rows, list)
                and len(rows) <= 2
                and len({row["pid"] for row in rows}) == len(rows)
                and all(
                    type(row["pid"]) is int
                    and row["pid"] > 0
                    and row["pgid"] == record["pid"]
                    and (row["pid"] == record["pid"] or row["parent"] == record["pid"])
                    for row in rows
                ),
                "closed observed process escaped registered group",
            )
        require(
            isinstance(record["escaped_group_cleanup"], list)
            and all(item["group_gone"] is True for item in record["escaped_group_cleanup"]),
            "closed escaped-group cleanup UNKNOWN",
        )
        components = completion["resource_components"]
        native = [item for item in components if item["kind"] == "native_profile"]
        wait4 = [item for item in components if item["kind"] == "wait4"]
        require(
            len(native) == len(wait4) == 1
            and native[0]["pid"] == record["controller_pid"]
            and set(profiles) == {native[0]["profile"]}
            and native[0]["profile_sha256"] == digest(profiles[native[0]["profile"]])
            and type(native[0]["actual_exit_code"]) is int,
            "closed outer controller native exit UNKNOWN",
        )
        _closed_wait4(wait4[0]["record"], wait4[0]["pid"], native[0]["actual_exit_code"])
        _closed_outer_watchdog(wait4[0]["record"])
        result.update(
            status="PUBLIC_CLOSED_ATTEMPT_FOR_STOP_ARCHIVE_ONLY",
            reason=None,
            closed_attempt_verified=True,
        )
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        result["reason"] = f"{type(error).__name__}: {error}"
    return result


SOFTWARE_CONTRACTS = (
    "docs/planning/p17_m2_content_verified_custody_protocol.json",
    "docs/planning/p17_m2_content_verified_custody_proposal.json",
    "docs/planning/p17_m2_input_export_preparation_proposal.json",
)
REQUIRED_HELPERS = {
    "scripts/p17_m2_content_verified_control.py",
    "scripts/p17_m2_verified_input.py",
    "scripts/p17_m2_content_verified_public_fixture.py",
    "scripts/p17_m2_content_verified_independent.py",
    "scripts/p17_m2_input_export.py",
    "scripts/p17_m2_input_export_independent.py",
    "scripts/p17_m2_local_input_version.py",
    "scripts/p17_m2_local_input_independent.py",
    "scripts/p17_m2_resource_control.py",
    "scripts/p17_m2_homotopy.py",
}
MODULE_SOURCE_SHA256 = digest(Path(__file__).read_bytes())


def _software_bytes(path: Path) -> bytes:
    directory = base.nofollow_parent(path)
    fd = -1
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        before = os.fstat(fd)
        require(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and 0 < before.st_size <= 16 * base.MIB,
            "software closure file kind/size differs",
        )
        raw = bytearray()
        while len(raw) <= before.st_size:
            chunk = os.read(fd, min(65536, before.st_size + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        require(
            len(raw) == before.st_size
            and _physical(before)
            == _physical(os.fstat(fd))
            == _physical(os.stat(path.name, dir_fd=directory, follow_symlinks=False)),
            "software closure file identity/length changed",
        )
        return bytes(raw)
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(directory)


def _software_closure(
    repo: Path, *, contracts: tuple[str, ...] = SOFTWARE_CONTRACTS
) -> dict[str, str]:
    directory = base.nofollow_parent(repo / "scripts" / ".software-closure")
    try:
        with os.scandir(directory) as entries:
            names = {
                "scripts/" + entry.name
                for entry in entries
                if entry.name.startswith("p17_m2_") and entry.name.endswith((".py", ".js"))
            }
    finally:
        os.close(directory)
    require(REQUIRED_HELPERS <= names, "software closure required helper missing")
    return {name: digest(_software_bytes(repo / name)) for name in sorted(names | set(contracts))}


def _check_software(
    plan: dict[str, Any],
    *,
    contracts: tuple[str, ...] = SOFTWARE_CONTRACTS,
    verifier_path: str = "scripts/p17_m2_content_verified_independent.py",
    verifier_sha256: str = MODULE_SOURCE_SHA256,
    controller: str = "p17_m2_content_verified_control.py",
    prepare_mode: str = "prepare-public",
    repo_guard: Any = None,
    prepare_suffix: tuple[str, ...] = (),
) -> None:
    require(
        isinstance(plan.get("source_tree"), dict) and REQUIRED_HELPERS <= set(plan["source_tree"]),
        "software closure is incomplete",
    )
    runtime = plan.get("runtime")
    require(isinstance(runtime, dict), "software closure runtime binding missing")
    own_repo = Path(__file__).resolve().parents[1]
    repo = Path(base.os.path.abspath(runtime["cwd"]))
    if repo != own_repo:
        (public_root if repo_guard is None else repo_guard)(repo)
    frozen = _software_closure(repo, contracts=contracts)
    require(
        frozen == plan["source_tree"] == _software_closure(own_repo, contracts=contracts)
        and frozen[verifier_path] == verifier_sha256,
        "software closure/source freeze differs",
    )
    python = Path(sys.orig_argv[0]).resolve()
    require(
        runtime["python"] == str(python)
        and runtime["python_sha256"] == digest(python.read_bytes()),
        "actual interpreter binding differs",
    )
    require(
        type(runtime["isolated"]) is int
        and runtime["isolated"] == 1
        and runtime["platform"] == sys.platform
        and runtime["os_release"] == platform.release()
        and runtime["lock_sha256"]
        == digest(_software_bytes(repo / "uv.lock"))
        == digest(_software_bytes(own_repo / "uv.lock"))
        and runtime["threads"]
        == {
            name: "1"
            for name in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
        "actual isolated platform/lock/thread binding differs",
    )
    script = str(repo / "scripts" / controller)
    require(
        runtime["orig_argv"] == [str(python), "-I", script, prepare_mode, "--root", plan["root"],
                                 *prepare_suffix],
        "actual prepare orig_argv differs",
    )
    for role in [*ROLE_ORDER, "final-filing", "lease-release"]:
        table = plan["roles"] if role in ROLE_ORDER else plan["metadata_actions"]
        require(
            table[role]["argv"]
            == [
                str(python),
                "-I",
                script,
                "payload",
                "--root",
                plan["root"],
                "--plan-sha",
                "@PLAN_SHA256@",
                "--role",
                role,
            ],
            "actual complete isolated role argv differs",
        )


class _PublicCertificatePolicy:
    """Fixed public context; other independently validated contexts are explicit adapters."""

    identity = EXECUTION_IDENTITY
    scope = PUBLIC_SCOPE
    schema = "topolab.v2.m2-content-verified-public-bundle.v1"
    formal_authority = False
    contract_path = "docs/planning/p17_m2_content_verified_custody_protocol.json"
    source_identity_key = "public_source_identity"
    r0_status = "PUBLIC_INDEPENDENT_R0_CHECKED"
    r1_status = "PUBLIC_INDEPENDENT_R1_CHECKED"
    backup_status = "PUBLIC_INDEPENDENT_BACKUP_CHECKED"
    filing_status = "PUBLIC_FILING_SNAPSHOT_WRITTEN"
    verifier_path = "scripts/p17_m2_content_verified_independent.py"
    result_seconds = (7200, 3600)
    precheck_status = None
    source_identity_policy = None

    def check_precheck(self, proof: Any, bundle: dict[str, Any], actual: dict[str, Any]) -> None:
        pass

    def guard(self, root: Path) -> Path:
        return public_root(root)

    def check_software(self, plan: dict[str, Any]) -> None:
        _check_software(plan)

    def content_root(self, plan: dict[str, Any]) -> Path:
        return self.guard(Path(plan["root"])) / "content"

    def source_root(self, plan: dict[str, Any]) -> Path:
        return self.guard(Path(plan["root"])) / "public-source"

    def backup_root(self, plan: dict[str, Any]) -> Path:
        return self.guard(Path(plan["root"])) / "backup-content"

    def source_identity(self, plan: dict[str, Any]) -> dict[str, Any]:
        return plan["public_source_identity"]

    def check_filing(self, result: dict[str, Any], wire: dict[str, Any]) -> None:
        pass

    def check_release(self, result: dict[str, Any], filing: dict[str, Any]) -> None:
        pass

    def certificate(self, binding: dict[str, Any]) -> Any:
        return CheckedPublicInput(binding, _authority=_CHECKED_AUTHORITY)


def audit_public_certificate(
    bundle: dict[str, Any], *, trusted_tool_events: dict[str, list[dict[str, Any]]]
) -> CheckedPublicInput:
    """Issue only the historical fixed public scope through the shared independent engine."""
    return _audit_certificate(
        bundle, trusted_tool_events=trusted_tool_events, policy=_PublicCertificatePolicy()
    )


def _audit_certificate(
    bundle: dict[str, Any], *, trusted_tool_events: dict[str, list[dict[str, Any]]], policy: Any
) -> Any:
    """Replay independent content/native/raw-return facts before issuing public-only capability."""
    require(
        isinstance(trusted_tool_events, dict) and trusted_tool_events,
        "actual trusted tool returns are required",
    )
    require(
        isinstance(bundle, dict)
        and bundle.get("schema") == policy.schema
        and bundle.get("execution_identity") == policy.identity
        and bundle.get("scope") == policy.scope,
        "public bundle identity/scope differs",
    )
    root = policy.guard(Path(bundle["root"]))
    plan, plan_sha = bundle["plan"], bundle["plan_sha256"]
    policy.guard(Path(plan["root"]))
    require(
        root == policy.content_root(plan)
        and plan.get("scope") == policy.scope
        and plan.get("execution_identity") == policy.identity
        and plan.get("formal_authority") is policy.formal_authority
        and plan_sha == digest(canonical(plan))
        and plan["role_order"] == ROLE_ORDER
        and set(plan["roles"]) == set(ROLE_ORDER)
        and set(plan["metadata_actions"])
        == {"final-filing", "lease-release", "public-consumer", "reader-ack"},
        "frozen public plan/scope/order/root differs",
    )
    policy.check_software(plan)
    contract = bundle["contract_sha256"]
    require(
        plan["contract_sha256"] == contract
        and contract == plan["source_tree"][policy.contract_path]
        and isinstance(contract, str)
        and base.SHA.fullmatch(contract),
        "contract identity differs from actual frozen protocol",
    )
    require(
        set(bundle["roles"]) == set(ROLE_ORDER)
        and set(trusted_tool_events) == {*ROLE_ORDER, "final-filing", "lease-release"},
        "actual role/metadata inventory differs",
    )
    results, previous = {}, None
    plan_window = _window(plan)
    coordination_seconds = 0.0
    event_ids: set[str] = set()
    for role in ROLE_ORDER:
        wire = bundle["roles"][role]
        require(
            wire["inner_evidence"]["expected_argv"] == resolved_argv(plan, role, plan_sha)
            and wire["inner_evidence"]["expected_role"] == role,
            "independent role argv/identity differs from frozen plan",
        )
        checked = audit_role(
            wire["pending"],
            wire["completion"],
            raw_tool_events=trusted_tool_events[role],
            expected_role=role,
            expected_plan_sha256=plan_sha,
            inner_evidence=wire["inner_evidence"],
            native_profiles=wire["native_profiles"],
            expected_identity=policy.identity,
            result_seconds=policy.result_seconds,
        )
        require(checked["full_role_evidence_accepted"] is True, str(checked["reason"]))
        require(
            _window(wire["pending"]) == plan_window,
            "role actor window differs from immutable common plan window",
        )
        require(previous is None or previous <= checked["T0"], "six role order overlaps/regresses")
        if previous is not None:
            coordination_seconds += checked["T0"] - previous
            require(coordination_seconds <= 240, "six roles exceed total240s coordination budget")
        for event in trusted_tool_events[role]:
            require(event["event_id"] not in event_ids, "raw event reused across roles")
            event_ids.add(event["event_id"])
        previous = checked["T1"]
        results[role] = checked
    if policy.precheck_status is not None:
        precheck = _proof(
            bundle["roles"][ROLE_ORDER[0]],
            policy.precheck_status,
            expected_identity=policy.identity,
            expected_scope=policy.scope,
        )
        policy.check_precheck(precheck, bundle, results[ROLE_ORDER[0]])
    require(previous + 360 <= plan_window[1], "common actor window final seal360s unavailable")
    shared_sha = digest(canonical(results))
    require(bundle["shared_packet_sha256"] == shared_sha, "shared actual-return packet differs")
    local = _independent_module(
        "certificate_local_independent", "p17_m2_local_input_independent.py"
    )
    manifest, registry = bundle["manifest"], bundle["registry"]
    shaped = local.validate_manifest(manifest, registry, contract)
    require(
        bundle["version_id"] == shaped["version_id"]
        and bundle["role_views"] == manifest["role_views"],
        "version/role views differ",
    )
    local_rows = local.identity_table(bundle["local_identity_rows"], 1071)
    members = {row["path"]: row for row in manifest["members"]}
    require(set(local_rows) == set(members), "local physical member closure differs")
    for name, row in members.items():
        require(
            all(local_rows[name][key] == row[key] for key in ("byte_size", "sha256")),
            "local physical bytes/hash differs",
        )
    root_identity = _root_tuple(bundle["root_identity"])
    r0 = _proof(
        bundle["roles"]["independent-r0"],
        policy.r0_status,
        expected_identity=policy.identity,
        expected_scope=policy.scope,
    )
    r1 = _proof(
        bundle["roles"]["independent-r1"],
        policy.r1_status,
        expected_identity=policy.identity,
        expected_scope=policy.scope,
    )
    registry_sha = digest(canonical(registry))
    for proof, count in ((r0, 40), (r1, 558)):
        require(
            proof["source_count"] == count
            and proof["source_registry_sha256"] == registry_sha
            and proof[policy.source_identity_key] == policy.source_identity(plan)
            and proof["source_comparison"] == getattr(
                policy, "source_comparison", "ALL_FIELDS_AND_PHYSICAL_TUPLES_MATCHED")
            and type(proof["compared_fields"]) is int
            and proof["compared_fields"] > 0
            and proof["helper_identity_relabelled"] is False,
            "independent original-source content comparison missing/different",
        )
        local.identity_table(proof["source_rows"], count,
                             source_identity_policy=getattr(policy, "source_identity_policy", None))
        if hasattr(policy, "check_source_rows"):
            policy.check_source_rows(proof, count, registry)
    require(
        r0["root"] == str(policy.source_root(plan))
        and r0["source_contract_sha256"] == digest(canonical(plan["content_contract"]))
        and r1["source_root"] == r0["root"]
        and r1["root"] == str(root)
        and r1["root_identity"] == root_identity
        and r1["manifest_sha256"] == r1["version_id"] == bundle["version_id"]
        and r1["contract_sha256"] == contract,
        "source/content proof version/root differs",
    )
    base.compare_words(r1["local_identity_rows"], bundle["local_identity_rows"])
    backup = _proof(
        bundle["roles"]["shared-closeout"],
        policy.backup_status,
        expected_identity=policy.identity,
        expected_scope=policy.scope,
    )
    base.compare_words(backup, bundle["backup"])
    billing = _audit_billing_ledger(
        backup,
        bundle["roles"],
        trusted_tool_events,
        plan_sha,
        expected_identity=policy.identity,
        expected_scope=policy.scope,
    )
    require(
        backup["own_root"] == str(root)
        and backup["root"] != str(root)
        and policy.guard(Path(backup["root"])) == policy.backup_root(plan)
        and backup["version_id"] == bundle["version_id"]
        and backup["contract_sha256"] == contract
        and backup["member_count"] == 1071
        and backup["own_root_identity"] == root_identity
        and (backup["root_identity"]["st_dev"], backup["root_identity"]["st_ino"])
        != (root_identity["st_dev"], root_identity["st_ino"])
        and _root_tuple(backup["root_identity"]),
        "backup root/version/count differs",
    )
    base.compare_words(backup["manifest"], manifest)
    backup_rows = local.identity_table(backup["identity_rows"], 1071)
    require(set(backup_rows) == set(members), "backup member closure differs")
    for name, row in members.items():
        require(
            all(backup_rows[name][key] == row[key] for key in ("byte_size", "sha256"))
            and (backup_rows[name]["before"]["st_dev"], backup_rows[name]["before"]["st_ino"])
            != (local_rows[name]["before"]["st_dev"], local_rows[name]["before"]["st_ino"]),
            "backup content/physical identity differs",
        )
    copied = backup["audit"]
    require(
        copied["status"] == "PASS_INDEPENDENT_NEW_BACKUP"
        and copied["member_count"] == 1071
        and copied["total_bytes"] == sum(row["byte_size"] for row in members.values())
        and copied["old_input_reads"] == 0
        and copied["B_C_admission"] is False
        and copied["excluded_prefixes"] == [],
        "independent backup audit incomplete",
    )
    base.compare_words(
        {r["path"]: {k: r[k] for k in ("byte_size", "sha256")} for r in copied["members"]},
        {name: {k: row[k] for k in ("byte_size", "sha256")} for name, row in members.items()},
    )
    filing = bundle["filing"]
    require(
        filing["inner_evidence"]["expected_argv"] == resolved_argv(plan, "final-filing", plan_sha)
        and filing["inner_evidence"]["expected_role"] == "final-filing"
        and filing["pending"]["result_start_UTC_seconds"] == previous,
        "filing start/argv differs from actual shared return",
    )
    filed = audit_role(
        filing["pending"],
        filing["completion"],
        raw_tool_events=trusted_tool_events["final-filing"],
        expected_role="final-filing",
        expected_plan_sha256=plan_sha,
        inner_evidence=filing["inner_evidence"],
        native_profiles=filing["native_profiles"],
        expected_identity=policy.identity,
        result_seconds=policy.result_seconds,
    )
    require(filed["full_role_evidence_accepted"] is True, str(filed["reason"]))
    policy.check_filing(filed, filing)
    filing_proof = base.parse(filing["inner_evidence"]["log"], canonical_required=True)
    require(
        filing_proof
        == {
            "status": policy.filing_status,
            "scope": policy.scope,
            "execution_identity": policy.identity,
            "plan_sha256": plan_sha,
            "version_id": bundle["version_id"],
            "manifest_sha256": bundle["version_id"],
            "shared_packet_sha256": shared_sha,
            "endpoint": "FINITE_SNAPSHOT_EXCLUDES_OWN_FUTURE_RETURN",
            "billing_charge": filing_proof.get("billing_charge"),
        },
        "filing finite content/actual-return packet binding differs",
    )
    charge = filing_proof["billing_charge"]
    first_filing = trusted_tool_events["final-filing"][0]
    filing_launch = next(
        item["record"]["launched_UTC_seconds"]
        for item in filing["completion"]["resource_components"]
        if item["kind"] == "wait4"
    )
    require(
        charge["role"] == "final-filing"
        and type(charge["frozen_FULL_seconds"]) is int
        and charge["frozen_FULL_seconds"] == charge["charged_FULL_seconds"] == 180
        and charge["scope"] == policy.scope
        and charge["execution_identity"] == policy.identity
        and charge["plan_sha256"] == plan_sha
        and charge["shared_reservation_sha256"]
        == digest(canonical(backup["billing_ledger"]["reservation"]))
        and type(charge["charged_FULL_seconds"]) is int
        and first_filing["start_seconds"]
        <= number(charge["charged_UTC_seconds"])
        <= number(filing_launch)
        <= first_filing["end_seconds"],
        "filing immutable FULL180 predispatch charge differs",
    )
    released = audit_release(
        bundle["lease_release_evidence"],
        raw_tool_events=trusted_tool_events["lease-release"],
        plan_sha256=plan_sha,
        expected_argv=resolved_argv(plan, "lease-release", plan_sha),
        expected_identity=policy.identity,
        result_seconds=policy.result_seconds,
    )
    require(released["metadata_evidence_accepted"] is True, str(released["reason"]))
    policy.check_release(released, filed)
    require(filed["T1"] <= released["T0"], "lease released before actual last reader return")
    lease, held = bundle["lease"], backup["custody_lease"]
    release_log = bundle["lease_release_evidence"]["inner_evidence"]["log"]
    require(
        base.parse(release_log, canonical_required=True) == lease,
        "release native log differs from final lease snapshot",
    )
    immutable = (
        "scope",
        "execution_identity",
        "root",
        "version_id",
        "registered_readers",
        "acquired_UTC_seconds",
        "acquired_monotonic",
    )
    require(
        all(lease[k] == held[k] for k in immutable)
        and lease["scope"] == "COOPERATIVE_REGISTERED_TOPOLAB_ONLY"
        and lease["execution_identity"] == policy.identity
        and lease["root"] == str(root)
        and lease["version_id"] == bundle["version_id"]
        and lease["registered_readers"] == [*ROLE_ORDER, "final-filing"]
        and held["state"] == "HELD"
        and held.get("last_reader_return") is None
        and lease["state"] == "RELEASED",
        "custody cooperative lease binding/state differs",
    )
    acquired = number(lease["acquired_UTC_seconds"], positive=True)
    number(lease["acquired_monotonic"], positive=True)
    require(
        bundle["roles"][ROLE_ORDER[0]]["pending"]["actor_activation_UTC_seconds"]
        <= acquired
        <= results[ROLE_ORDER[0]]["T0"],
        "lease acquisition occurs after a registered reader",
    )
    last = trusted_tool_events["final-filing"][-1]
    require(
        lease["last_reader_return"]
        == {
            "event_id": last["event_id"],
            "sha256": digest(canonical(last)),
            "end_seconds": last["end_seconds"],
        }
        and released["T0"] <= number(lease["released_UTC_seconds"]) <= released["T1"],
        "actual last-reader/release return binding missing",
    )
    log = backup["custody_log"]
    require(
        isinstance(log, list)
        and len(log) == 2
        and log[0]["version_id"] is None
        and log[0]["state"] == "HELD"
        and all(log[0][key] == lease[key] for key in immutable if key != "version_id")
        and log[1]["event"] == "VERSION_BOUND"
        and log[1]["acquired_record_sha256"] == digest(canonical(log[0]))
        and log[1]["version_id"] == bundle["version_id"]
        and acquired <= number(log[1]["UTC_seconds"]) <= results["exporter-r1"]["T1"]
        and lease["acquired_monotonic"] <= number(log[1]["monotonic"]),
        "actual custody acquisition/version log differs",
    )
    binding = {
        k: bundle[k]
        for k in (
            "manifest",
            "version_id",
            "contract_sha256",
            "root",
            "root_identity",
            "local_identity_rows",
            "role_views",
            "lease",
            "scope",
        )
    }
    binding["plan_sha256"] = plan_sha
    binding["role_results"] = results
    binding["filing_result"] = filed
    binding["release_result"] = released
    binding["billing_ledger"] = billing
    binding["shared_packet_sha256"] = shared_sha
    binding["formal_or_scientific_admission"] = False
    binding["metadata_actions"] = plan["metadata_actions"]
    binding["independent_source_sha256"] = plan["source_tree"][policy.verifier_path]
    return policy.certificate(binding)


def _audit_billing_ledger(
    backup: dict[str, Any],
    wires: dict[str, Any],
    events: dict[str, Any],
    plan_sha: str,
    *,
    expected_identity: str = EXECUTION_IDENTITY,
    expected_scope: str = PUBLIC_SCOPE,
) -> dict[str, Any]:
    ledger = backup["billing_ledger"]
    reservation = ledger["reservation"]
    caps = {role: FULL_SECONDS[role] for role in ROLE_ORDER}
    require(
        type(reservation["shared_reserved_FULL_seconds"]) is int
        and reservation["shared_reserved_FULL_seconds"] == 300
        and reservation["role_FULL_seconds"] == caps
        and all(type(v) is int for v in reservation["role_FULL_seconds"].values())
        and reservation["refunds_allowed"] is False
        and reservation["scope"] == expected_scope
        and reservation["execution_identity"] == expected_identity
        and reservation["plan_sha256"] == plan_sha,
        "billing shared reservation/FULL/no-refund differs",
    )
    reserved = number(reservation["reserved_UTC_seconds"], positive=True)
    reservation_sha = digest(canonical(reservation))
    charges = ledger["dispatch_charges"]
    require(
        isinstance(charges, list) and len(charges) == len(ROLE_ORDER),
        "billing actual dispatch inventory differs",
    )
    for role, charge in zip(ROLE_ORDER, charges, strict=True):
        first = events[role][0]
        component = next(
            item
            for item in wires[role]["completion"]["resource_components"]
            if item["kind"] == "wait4"
        )
        launch = number(component["record"]["launched_UTC_seconds"], positive=True)
        charged = number(charge["charged_UTC_seconds"], positive=True)
        require(
            charge["role"] == role
            and charge["scope"] == expected_scope
            and charge["execution_identity"] == expected_identity
            and charge["plan_sha256"] == plan_sha
            and type(charge["frozen_FULL_seconds"]) is int
            and type(charge["charged_FULL_seconds"]) is int
            and charge["frozen_FULL_seconds"] == caps[role]
            and charge["charged_FULL_seconds"] == (0 if role == "shared-closeout" else caps[role])
            and charge["shared_reservation_sha256"] == reservation_sha
            and reserved <= charged
            and first["start_seconds"] <= charged <= launch <= first["end_seconds"],
            "billing role FULL/predispatch charge differs",
        )
        if role == ROLE_ORDER[0]:
            require(
                first["start_seconds"] <= reserved <= launch
                and ledger["first_dispatch_launch_UTC_seconds"] == launch,
                "billing shared reservation must precede actual first launch",
            )
    total = reservation["shared_reserved_FULL_seconds"] + sum(
        charge["charged_FULL_seconds"] for charge in charges
    )
    require(total == 3600, "billing immutable six FULL total differs")
    return dict(ledger, six_roles_reserved_FULL_seconds=total, refunds_observed=False)


def independent_backup(
    content: Path,
    backup: Path,
    closed: dict[str, Any],
    registry: dict[str, Any],
    contract_sha: str,
    *,
    expected_identity: str = EXECUTION_IDENTITY,
    expected_scope: str = PUBLIC_SCOPE,
    checked_status: str = "PUBLIC_INDEPENDENT_BACKUP_CHECKED",
    root_guard: Any = None,
) -> dict[str, Any]:
    guard = public_root if root_guard is None else root_guard
    content, backup = guard(content), guard(backup)
    require(
        content != backup
        and not backup.is_relative_to(content)
        and not content.is_relative_to(backup),
        "backup must be a distinct sibling namespace",
    )
    own_root = _checked_root(content, root_guard=guard)
    backup_root = _checked_root(backup, root_guard=guard)
    require(
        own_root == _root_tuple(closed.get("root_identity")), "backup source root identity changed"
    )
    local = _independent_module(
        "public_backup_local_independent", "p17_m2_local_input_independent.py"
    )
    own = local.audit_local_content(
        content, closed["manifest"], registry, closed["local_identity_rows"], contract_sha
    )
    comparison = base.audit_new_backup(content, backup, public_fixture=True)
    require(comparison["status"] == "PASS_INDEPENDENT_NEW_BACKUP", comparison["reason"])
    reader = base.OnceReader(backup, 1071, 384 * base.MIB, source_identity_checks=True)
    for row in closed["manifest"]["members"]:
        reader.read(
            row["path"], local.CAPS[row["type"]], sha256=row["sha256"], byte_size=row["byte_size"]
        )
    checked = local.audit_local_content(
        backup, closed["manifest"], registry, reader.observations, contract_sha
    )
    require(
        _checked_root(content, root_guard=guard) == own_root
        and _checked_root(backup, root_guard=guard) == backup_root,
        "backup root identity changed during comparison",
    )
    require(
        checked["version_id"] == closed["version_id"] == own["version_id"],
        "backup content version differs",
    )
    return {
        "status": checked_status,
        "execution_identity": expected_identity,
        "scope": expected_scope,
        "own_root": str(content),
        "root": str(backup),
        "root_identity": backup_root,
        "own_root_identity": own_root,
        "manifest": closed["manifest"],
        "version_id": checked["version_id"],
        "contract_sha256": contract_sha,
        "identity_rows": checked["local_identity_rows"],
        "member_count": 1071,
        "audit": comparison,
        "formal_or_scientific_admission": False,
        "B_C_admission": False,
    }


def _prefix_inventory(root: Path) -> set[str]:
    paths: set[str] = set()
    total = 0

    def visit(descriptor: int, prefix: str) -> None:
        nonlocal total
        require(
            stat.S_IMODE(os.fstat(descriptor).st_mode) == 0o700,
            "prefix backup directory is not private",
        )
        with os.scandir(descriptor) as entries:
            names = sorted(entry.name for entry in entries)
        for name in names:
            info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            literal = prefix + name
            require(info.st_uid == os.geteuid(), "prefix backup owner differs")
            if stat.S_ISDIR(info.st_mode):
                child = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor
                )
                try:
                    require(
                        _physical(info) == _physical(os.fstat(child)),
                        "prefix backup directory changed",
                    )
                    visit(child, literal + "/")
                finally:
                    os.close(child)
            else:
                require(
                    stat.S_ISREG(info.st_mode)
                    and info.st_nlink == 1
                    and stat.S_IMODE(info.st_mode) == 0o600,
                    "prefix backup requires private single-link regular files",
                )
                paths.add(literal)
                total += info.st_size
                require(
                    len(paths) <= 4096 and total <= 512 * base.MIB,
                    "prefix backup inventory cap exceeded",
                )

    directory = base.nofollow_parent(root / ".prefix-inventory")
    try:
        visit(directory, "")
    finally:
        os.close(directory)
    return paths


def independent_prefix_backup(
    source_root: Path,
    backup_root: Path,
    rows: list[dict[str, Any]],
    *,
    expected_identity: str = EXECUTION_IDENTITY,
    expected_scope: str = PUBLIC_SCOPE,
    checked_status: str = "PUBLIC_FAILED_PREFIX_BACKUP_CHECKED",
    root_guard: Any = None,
    expected_backup: Path | None = None,
) -> dict[str, Any]:
    """Check only a finite failed public prefix; never issue an input certificate."""
    readers: dict[str, Any] = {}
    try:
        guard = public_root if root_guard is None else root_guard
        source_root, backup_root = guard(source_root), guard(backup_root)
        require(
            backup_root
            == (source_root / "backup-prefix" if expected_backup is None else expected_backup),
            "failed prefix backup root differs",
        )
        require(
            isinstance(rows, list) and 0 < len(rows) <= 4096,
            "failed prefix explicit nonempty inventory missing",
        )
        local = _independent_module(
            "prefix_identity_independent", "p17_m2_local_input_independent.py"
        )
        identities = local.identity_table([row["identity"] for row in rows], len(rows))
        paths = [row["path"] for row in rows]
        require(paths == sorted(identities), "failed prefix inventory order/set differs")
        for row in rows:
            name = row["path"]
            pieces = base.PurePosixPath(name)
            require(
                pieces.parts[0]
                not in {"public-source", "independent-public-fixture", "backup-prefix"}
                and pieces.name != "active.json"
                and not (
                    pieces.parts[0] == "receipts"
                    and len(pieces.parts) > 1
                    and (
                        pieces.parts[1] == "shared-closeout"
                        or pieces.parts[1].startswith("shared-closeout-")
                    )
                )
                and all(row[k] == identities[name][k] for k in ("path", "byte_size", "sha256")),
                "failed prefix inventory includes unclosed/excluded files",
            )
        original_root, copied_root = (
            _checked_root(source_root, root_guard=guard),
            _checked_root(backup_root, root_guard=guard),
        )
        require(
            _prefix_inventory(backup_root) == set(paths), "failed prefix backup inventory differs"
        )
        original = base.OnceReader(
            source_root, len(rows), 512 * base.MIB, source_identity_checks=True
        )
        copied = base.OnceReader(
            backup_root, len(rows), 512 * base.MIB, source_identity_checks=True
        )
        readers.update(source=original, backup=copied)
        for row in rows:
            name = row["path"]
            directory = base.nofollow_parent(source_root / name)
            try:
                info = os.stat(Path(name).name, dir_fd=directory, follow_symlinks=False)
                require(
                    stat.S_ISREG(info.st_mode)
                    and info.st_uid == os.geteuid()
                    and info.st_nlink == 1
                    and stat.S_IMODE(info.st_mode) == 0o600,
                    "failed prefix source requires private single-link regular files",
                )
            finally:
                os.close(directory)
            left = original.read(
                name, 64 * base.MIB, sha256=row["sha256"], byte_size=row["byte_size"]
            )
            right = copied.read(
                name, 64 * base.MIB, sha256=row["sha256"], byte_size=row["byte_size"]
            )
            require(left == right, "failed prefix backup bytes differ")
            require(
                original.observations[-1] == identities[name],
                "failed prefix original identity changed",
            )
            require(
                (
                    copied.observations[-1]["before"]["st_dev"],
                    copied.observations[-1]["before"]["st_ino"],
                )
                != (identities[name]["before"]["st_dev"], identities[name]["before"]["st_ino"]),
                "failed prefix backup shares source physical file",
            )
        require(
            _checked_root(source_root, root_guard=guard) == original_root
            and _checked_root(backup_root, root_guard=guard) == copied_root
            and _prefix_inventory(backup_root) == set(paths),
            "failed prefix root/inventory changed during comparison",
        )
        return {
            "status": checked_status,
            "scope": expected_scope,
            "execution_identity": expected_identity,
            "root": str(source_root),
            "backup_root": str(backup_root),
            "source_root_identity": original_root,
            "backup_root_identity": copied_root,
            "member_count": len(rows),
            "total_bytes": original.used,
            "paths": paths,
            "source_identity_rows": original.observations,
            "backup_identity_rows": copied.observations,
            "input_version_accepted": False,
            "formal_or_scientific_admission": False,
            "B_C_admission": False,
            "old_original_reads": 0,
        }
    except BaseException as error:
        _capture_read_failure(error, readers, "independent_prefix_backup", {"producer_rows": rows})
        raise
