"""R-LOCAL preparation checks only; no formal executor or source IO capability.

These structural checks do not observe native exits, resources, source bytes or
owner identity. The production activation command always closes fail-safe until
a separately reviewed executable launch binding exists.
"""

import argparse
import hashlib
import json
import math
import re
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IDENTITY = "topolab.v2.p17-m2-local-input-version.v1"
PROTOCOL = REPO / "docs/planning/p17_m2_local_input_version_protocol.json"
ORIGINAL_ROOT = "/Users/keith1117/Documents/TopoLab-data"
GENERATION_ROOT = "/Users/Shared/TopoLab-input-versions/p17-m2-local-input-version-v1"
BACKUP_ROOT = GENERATION_ROOT + "-independent-backup"
SOURCE_FILES = {
    "scripts/p17_m2_local_input_control.py", "scripts/p17_m2_local_input_version.py",
    "scripts/p17_m2_local_input_independent.py", "scripts/p17_m2_input_export.py",
    "scripts/p17_m2_input_export_independent.py", "scripts/p17_m2_input_export_control.py",
    "scripts/p17_m2_input_export_dispatch.js", "scripts/p17_m2_resource_control.py",
    "scripts/p17_m2_homotopy.py", "uv.lock",
    "docs/planning/p17_m2_input_export_preparation_proposal.json",
    "docs/planning/p17_m2_local_input_version_protocol.md",
    "docs/planning/p17_m2_local_input_version_protocol.json",
}
CONTENT_SHA256 = "f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad"
CAPS = {
    "independent-public-check": 300,
    "exporter-r0": 300,
    "independent-r0": 300,
    "exporter-r1": 1200,
    "independent-r1": 1200,
    "shared-closeout": 300,
}


def require(condition, reason):
    if not condition:
        raise ValueError("R_LOCAL_STOP: " + reason)


def authority_checked(protocol, phase):
    """Validate separate grants as records, never create an execution token."""
    require(phase in {"preparation", "formal"}, "registered phase")
    require(protocol.get("schema") == "topolab.v2.m2-local-input-contract.v1"
            and protocol.get("execution_identity") == IDENTITY,
            "approved NEW R-LOCAL schema and identity; drafts and old grants refuse")
    authority = protocol["authority"]
    require(isinstance(authority.get("owner_adoption_record"), str)
            and bool(authority["owner_adoption_record"].strip())
            and authority.get("new_custody_model_adopted") is True
            and authority.get(
                "software_implementation_public_checks_and_target_preparation_authorized")
                is True, "attributed owner adoption and preparation grant")
    require(all(authority.get(name) is False for name in (
        "scientific_B_authorized", "scientific_C_authorized", "old_quota_reopening_authorized")),
        "B/C and old quotas remain closed")
    grant = protocol.get("preparation_grant", {})
    require(type(grant.get("executor_seconds")) is int and grant["executor_seconds"] == 14400
            and type(grant.get("independent_seconds")) is int
            and grant["independent_seconds"] == 10800
            and grant.get("continuous_clock") is True, "actual continuous preparation grant")
    budgets = protocol["budget_request_NOT_GRANTED"]
    prep = budgets["preparation_including_public_checks_CI_and_target_readiness"]
    require(type(prep["executor_seconds"]) is int and prep["executor_seconds"] == 14400
            and type(prep["independent_seconds"]) is int
            and prep["independent_seconds"] == 10800, "exact new preparation caps")
    formal = budgets["formal"]
    fixed = {"common_window_seconds": 4500, "FULL_sum_seconds": 3600,
             "setup_lease_seconds": 300, "between_roles_total_seconds": 240,
             "final_frontier_seal_handoff_seconds": 360,
             "first_dispatch_remaining_minimum": 4200}
    require(all(type(formal.get(key)) is int and formal[key] == value
                for key, value in fixed.items())
            and formal.get("FULL_seconds_by_role") == CAPS
            and all(type(value) is int for value in formal["FULL_seconds_by_role"].values()),
            "immutable 4500 window, six FULL caps and overhead reserves")
    if phase == "formal":
        require(all(authority.get(name) is True for name in (
            "old_metadata_and_payload_stat_read_temporary_parse_authorized",
            "new_six_role_activation_authorized", "source_copy_now_authorized")),
            "separate source and six-role activation grants required")
        return "FORMAL_GRANT_RECORDS_ONLY_NO_EXECUTABLE_ADMISSION"
    return "PREPARATION_AUTHORIZED_FORMAL_CLOSED"


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_plan(plan, now):
    """Check a proposed plan's structure; this never certifies actual frozen IO.

    No filesystem is consulted. A passing result cannot satisfy source, runtime,
    actual CI, independent readiness, target admission or launch authority.
    """
    require(plan.get("schema") == "topolab.v2.m2-local-input-launch-plan.v1"
            and plan.get("execution_identity") == IDENTITY, "NEW local plan identity")
    require(plan.get("original_root_literal") == ORIGINAL_ROOT
            and plan.get("generation_root_literal") == GENERATION_ROOT
            and plan.get("backup_root_literal") == BACKUP_ROOT,
            "separate literal original, generation and backup roots")
    require(plan.get("content_sha256") == CONTENT_SHA256
            and isinstance(plan.get("protocol_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", plan["protocol_sha256"]),
            "content and approved protocol hash bindings")
    for field in ("merged_source", "merged_tree"):
        require(isinstance(plan.get(field), str) and re.fullmatch(r"[0-9a-f]{40}", plan[field]),
                "frozen source and tree identities")
    sources = plan.get("source_files", {})
    require(set(sources) == SOURCE_FILES
            and all(isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
                    for value in sources.values()), "complete frozen source file identities")
    authors = plan.get("authors", {})
    require(set(authors) == {"executor", "independent"}
            and all(isinstance(value, str) and bool(value.strip()) for value in authors.values())
            and authors["executor"] != authors["independent"], "different registered authors")
    activation = plan.get("actor_activation_UTC_seconds")
    require(finite_number(activation) and activation > 0 and round(activation, 3) == activation
            and finite_number(now) and activation <= now <= activation + 4500,
            "immutable finite once-activated 4500 second window")
    deadline = datetime.fromtimestamp(activation + 4500, UTC).isoformat(
        timespec="milliseconds").replace("+00:00", "Z")
    require(type(plan.get("actor_window_seconds")) is int
            and plan["actor_window_seconds"] == 4500
            and plan.get("actor_deadlines_UTC") == {"exporter": deadline, "independent": deadline}
            and plan.get("FULL_caps_seconds") == CAPS
            and all(type(value) is int for value in plan["FULL_caps_seconds"].values()),
            "exact FULL and common deadline bindings")
    require(plan.get("formal_overhead_caps") == {
        "setup_lease_seconds": 300, "between_roles_total_seconds": 240,
        "final_frontier_seal_handoff_seconds": 360}, "full setup/coordination/handoff reserves")
    return "PLAN_STRUCTURE_ONLY_NO_LAUNCH_ADMISSION"


def target_lease_checked(plan, lease, release=None):
    """Validate an active local lease record, not actual writer exclusion."""
    activation = plan["actor_activation_UTC_seconds"]
    validate_plan(plan, activation)
    raw = (json.dumps(plan, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")
    require(lease.get("schema") == "topolab.v2.m2-local-generation-lease.v1"
            and lease.get("execution_identity") == IDENTITY
            and lease.get("plan_sha256") == hashlib.sha256(raw).hexdigest()
            and lease.get("root") == GENERATION_ROOT and lease.get("backup") == BACKUP_ROOT,
            "new local target lease identity/plan/literal roots")
    require(lease.get("custodian") == plan["authors"]["executor"]
            and lease.get("active") is True and release is None,
            "active attributed local lease; release refuses further use")
    acquired = lease.get("acquired_UTC_seconds")
    require(finite_number(acquired) and activation <= acquired <= activation + 300,
            "actual acquisition record inside setup300")
    require(lease.get("scope") == "LOCAL_GENERATION_WRITER_EXCLUSION_ONLY"
            and lease.get("old_source_quiescence_claim") is False
            and lease.get("held_until") == "LAST_REGISTERED_READER_ACTUAL_RETURN_INCLUDING_FILING"
            and lease.get("content_writers") == ["exporter-r0", "exporter-r1"]
            and lease.get("content_mutation_after_exporter_r1_exit") is False,
            "local-only target custody through last reader; no post-export content writes")
    return "LEASE_STRUCTURE_ONLY_NO_CUSTODY_ADMISSION"


def dispatch_gate(plan, state, role, now):
    """Compute a proposed reserve/charge without launching or changing a ledger.

    Observed rows are structural inputs, not independent raw-event verification.
    Actual dispatch/recording is deliberately unavailable in this preparation.
    """
    validate_plan(plan, now)
    order = list(CAPS)
    require(role in CAPS and state.get("active_role") is None, "registered idle next role")
    attempted = state.get("attempted_roles")
    require(isinstance(attempted, list) and len(attempted) == len(set(attempted))
            and all(name in CAPS for name in attempted) and role not in attempted,
            "no retry or unregistered attempted role")
    source_attempted = [name for name in attempted if name != "shared-closeout"]
    require(source_attempted == order[:len(source_attempted)]
            and "shared-closeout" not in attempted, "closed exact role order")
    require(type(state.get("STOP")) is bool, "explicit STOP state")
    require(role == "shared-closeout" or state["STOP"] is False,
            "STOP closes every source suffix role")
    require(role == "shared-closeout" or order[len(source_attempted)] == role,
            "exact next role only")
    used = state.get("between_roles_seconds_used")
    require(finite_number(used) and 0 <= used <= 240, "coordination total cap")
    charges = state.get("FULL_charges_seconds", {})
    expected_charges = {name: CAPS[name] for name in attempted}
    if attempted:
        expected_charges["shared-closeout"] = 300
    require(charges == expected_charges
            and all(type(value) is int for value in charges.values()),
            "retained full started charges and shared reservation; no refund")
    observed = state.get("observed", {})
    for previous in attempted:
        row = observed.get(previous, {})
        require(row.get("cleanup", {}).get("group_gone") is True,
                "UNKNOWN cleanup refuses further dispatch")
        if role != "shared-closeout":
            require(row.get("status") == "PASS_R_LOCAL_FULL_ROLE",
                    "complete predecessor needed before source suffix")
    if role == "shared-closeout":
        require(bool(attempted), "shared requires actual nonempty prefix")
        required = 300 + (240 - used) + 360
    else:
        required = sum(CAPS[name] for name in order[order.index(role):]) + (240 - used) + 360
    require(plan["actor_activation_UTC_seconds"] + 4500 - now >= required,
            "complete remaining suffix plus coordination and handoff must fit")
    after = dict(charges)
    after[role] = CAPS[role]
    after["shared-closeout"] = 300
    return {"status": "RESERVE_STRUCTURE_ONLY_NO_DISPATCH_ADMISSION",
            "required_remaining_seconds": required,
            "new_FULL_charge_if_started": sum(after.values()) - sum(charges.values()),
            "FULL_charges_after_start": after}


def main(argv=None):
    import sys

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("capability", "activate"))
    args = parser.parse_args(argv)
    result = {
        "execution_identity": IDENTITY,
        "status": "STOP_NO_RETRY",
        "reason": "FORMAL_LAUNCH_BINDING_INCOMPLETE",
        "formal_launch_binding": "INCOMPLETE",
        "old_source_stat_read_copy": 0,
        "formal_roles_started": 0,
        "B_C_authorized": False,
        "old_quota_reopened": False,
    }
    if not sys.flags.isolated or Path.cwd() != REPO:
        result["reason"] = "ACTUAL_ISOLATED_ENTRY_REQUIRED"
    elif args.mode == "capability":
        result.update(status="SOFTWARE_PREPARATION_CAPABILITY_ONLY", reason=None,
                      runtime={"isolated": True, "python": sys.executable,
                               "orig_argv": sys.orig_argv, "cwd": str(Path.cwd()),
                               "module_origin": str(Path(__file__).resolve()),
                               "dependencies": "stdlib only"})
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return int(result["status"] == "STOP_NO_RETRY")


if __name__ == "__main__":
    raise SystemExit(main())
