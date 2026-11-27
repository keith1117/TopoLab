"""Transport a stopped C controller's evidence without duplicating its full error log."""

import hashlib


def row_key(row):
    if not isinstance(row, dict):
        return None
    return {k: row[k] for k in ("phase", "ordinal", "case_id", "method") if k in row}


def metadata(packet, *, planned_rows, original):
    contexts = {
        item["path"]: item["packet"] for item in packet["retained_context"] if "path" in item
    }
    payload = contexts.get("payload-failure.json", {})
    retained = payload.get("retained_context", {})
    progress = (
        retained.get("scientific_failure")
        or contexts.get("rows/producer-failure.json")
        or contexts.get("rows/auditor-failure.json")
        or {}
    )
    # No count is inferred for a row whose numerical exit never reached its writer.
    completed = progress.get("completed_rows")
    filed = len(completed) if isinstance(completed, list) else completed
    attempts = progress.get("attempted_rows")
    charge = progress.get("internal_row_charge_seconds")
    if not progress and payload.get("row_execution_stage") == "BEFORE_PANEL":
        attempts, filed, charge = 0, 0, 0
    remaining = planned_rows - attempts if type(attempts) is int else None
    first = payload or progress or packet
    return {
        "schema": "topolab.c-controller-stop-metadata.v1",
        "contract_sha256": packet["scientific_contract_sha256"],
        "role": packet["role"],
        "status": "STOP_NO_RETRY",
        "first_error": {"type": first["error_type"], "reason": first["reason"][:2048]},
        "first_error_sha256": hashlib.sha256(first["reason"].encode()).hexdigest(),
        "controller_failure_sha256": hashlib.sha256(original).hexdigest(),
        "controller_failure_bytes": len(original),
        "retained_context_sha256": {
            item["path"]: item["raw_sha256"]
            for item in packet["retained_context"]
            if "path" in item
        },
        "planned_rows": planned_rows,
        "attempted_rows": attempts,
        "fully_filed_rows": filed,
        "current_row": row_key(progress.get("current_row")),
        "unattempted_rows": remaining,
        "internal_row_charge_seconds": charge,
        "row_execution_stage": payload.get("row_execution_stage"),
        "reader_lease": payload.get("lease_disposition"),
        "secondary_error_counts": {
            "payload": len(payload.get("secondary_errors", [])),
            "row": len(progress.get("secondary_errors", [])),
            "controller": len(packet["secondary_errors"]),
        },
    }


def compact_error(raw, packet):
    """Return existing small diagnostics verbatim or a bounded pointer to their evidence."""
    if len(raw) <= 64 * 1024:
        return None
    return {
        "schema": "topolab.c-payload-stop-diagnostic.v1",
        "status": "STOP_NO_RETRY",
        "scientific_contract_sha256": packet["scientific_contract_sha256"],
        "error_type": packet["error_type"],
        "reason": packet["reason"][:2048],
        "complete_packet_bytes": len(raw),
        "complete_packet_sha256": hashlib.sha256(raw).hexdigest(),
        "secondary_errors": [
            {k: str(v)[:1024] for k, v in e.items() if k in ("stage", "type", "reason")}
            for e in packet.get("secondary_errors", [])[:8]
        ],
    }
