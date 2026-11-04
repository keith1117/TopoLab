"""Native execution/return audit for a separately admitted strict23 registration.

The caller supplies actual external events. A serialized PASS is never resource
or return evidence and this adapter grants no scientific admission.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
from pathlib import Path

IDENTITY = "topolab.v2.p17-source-binding-and-conditional-repair.20261103.v1"
WINDOW2_IDENTITY = "topolab.v2.p17-source-binding-window2.20261104.v1"
RECOVERY_IDENTITY = "topolab.v2.p17-binding-certificate-recovery.20261104.v1"
RECOVERY_V3_IDENTITY = "topolab.v2.p17-binding-certificate-recovery.20261104.v3"
RECOVERY_V4_IDENTITY = "topolab.v2.p17-binding-certificate-recovery.20261104.v4"
RECOVERY_IDENTITIES = (RECOVERY_IDENTITY, RECOVERY_V3_IDENTITY, RECOVERY_V4_IDENTITY)
RECOVERY_SCOPE = "STRICT_BINDING_CERTIFICATE_RECOVERY_METADATA_ONLY"
REPO = Path(__file__).resolve().parents[1]
CAPS = {"producer-availability": 150, "independent-availability": 150,
        "binding-producer": 300, "binding-independent": 300, "binding-closeout": 180}
SCOPES = ("PUBLIC_STRICT_BINDING_REGISTRATION_ONLY", "FORMAL_STRICT_BINDING_REGISTRATION_ONLY")
METADATA_SCHEMA = "topolab.v2.m2-strict-source-binding.metadata-plan.v1"
METADATA_SCOPE = "STRICT_BINDING_CERTIFICATE_METADATA_ONLY"
METADATA_CAPS = {"binding-certificate-auditor": 120}
METADATA_AUTHORS = {"binding-certificate-auditor": "/root/binding_route_independent_v1"}
AUTHORS = {"producer-availability": "/root",
           "independent-availability": "/root/binding_route_independent_v1",
           "binding-producer": "/root",
           "binding-independent": "/root/binding_route_independent_v1",
           "binding-closeout": "/root"}


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(ok, reason):
    if not ok:
        raise ValueError("STRICT_BINDING_NATIVE: " + reason)


def load(name):
    path = REPO / "scripts" / (name + ".py")
    old = sys.modules.get(name)
    if old is not None and Path(old.__file__).resolve() == path:
        return old
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, "published helper unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def execution_profile(plan):
    """Select only a registered identity; historical windows remain unchanged."""
    context = plan.get("context")
    need(isinstance(context, dict), "native execution identity context missing")
    identity, attempt = context.get("execution_identity"), context.get("attempt", 1)
    if identity in RECOVERY_IDENTITIES:
        need(type(attempt) is int and attempt == 1 and plan.get("schema") == METADATA_SCHEMA
             and context.get("scope") == RECOVERY_SCOPE,
             "recovery execution permits only its metadata profile")
        return identity, 300
    need(type(attempt) is int and (
        (identity == IDENTITY and attempt in (1, 2))
        or (identity == WINDOW2_IDENTITY and attempt == 2)),
        "unregistered native execution identity/attempt profile")
    return identity, 1800 if identity == WINDOW2_IDENTITY else 3600


def role_profile(plan):
    """Identity selects the core window; metadata always retains its own 300s."""
    identity, core_seconds = execution_profile(plan)
    if identity in RECOVERY_IDENTITIES:
        return METADATA_CAPS, 300, (RECOVERY_SCOPE,), METADATA_AUTHORS
    if plan.get("schema") == METADATA_SCHEMA:
        return METADATA_CAPS, 300, (METADATA_SCOPE,), METADATA_AUTHORS
    return CAPS, core_seconds, SCOPES, AUTHORS


def argv_for(plan, mode, role):
    caps, _, _, _ = role_profile(plan)
    need(role in caps and mode in ("supervise", "run", "record", "payload"),
         "unregistered native command")
    script = ("p17_m2_source_binding_recovery.py"
              if plan["context"]["execution_identity"] in RECOVERY_IDENTITIES else
              "p17_m2_source_binding.py" if mode == "payload"
              else "p17_m2_source_binding_native.py")
    # Captured plans pin their original checkout. This is command reconstruction,
    # not execution admission: predecessor still requires the current runtime.
    cwd = plan["runtime"].get("cwd", str(REPO))
    need(isinstance(cwd, str) and Path(cwd).is_absolute()
         and not any(part in (".", "..") for part in cwd.split("/")),
         "captured runtime cwd must be an absolute literal")
    return [plan["runtime"]["python"], "-I", str(Path(cwd) / "scripts" / script), mode,
            "--plan", str(Path(plan["root"]) / "plan.json"),
            "--plan-sha", sha(canonical(plan)), "--role", role]


class Transport:
    """Use the existing complete native/exit engine with new declared caps."""

    identity = IDENTITY
    role_caps = CAPS
    shared_role = "binding-closeout"
    formal_seconds = 3600
    formal_reserve_seconds = 600

    def __init__(self, plan):
        self.identity, _ = execution_profile(plan)
        self.formal_seconds = role_profile(plan)[1]
        self.plan = plan
        self.root = Path(plan["root"])
        self.scope = plan["context"]["scope"]

    def predecessor(self, root, plan, role):
        need(root == self.root and plan == self.plan, "transport plan differs")
        load("p17_m2_source_binding").admit_plan(plan, role)

    def argv_for(self, root, mode, plan_sha, role):
        need(root == self.root and plan_sha == sha(canonical(self.plan)),
             "transport argv plan differs")
        return argv_for(self.plan, mode, role)

    def namespace_check(self, root, **kwargs):
        need(root == self.root, "transport namespace differs")
        return load("p17_m2_content_verified_control").namespace_check(root, **kwargs)

    def put(self, path, value):
        need(path.is_relative_to(self.root), "metadata write outside registered attempt")
        self.namespace_check(self.root, additional_bytes=len(canonical(value)), additional_files=1)
        return load("p17_m2_content_verified_control").put(path, value)

    def native_module(self):
        # A fresh instrumentation instance keeps this adapter's bounded writer
        # from changing any old/default caller in the same software process.
        load("p17_m2_homotopy")
        path = REPO / "scripts/p17_m2_resource_control.py"
        spec = importlib.util.spec_from_file_location("strict23_native_measurement", path)
        need(spec is not None and spec.loader is not None, "native measurement unavailable")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        snapshot = module._snapshot

        def bounded_snapshot(*args, **kwargs):
            self.namespace_check(self.root, additional_bytes=4 * 1024**2, additional_files=16)
            return snapshot(*args, **kwargs)

        module._snapshot = bounded_snapshot
        module.atomic_new = self.put
        return module

    def resource_evidence(self, root, plan_sha, role, **kwargs):
        return load("p17_m2_content_verified_control").resource_evidence(
            root, plan_sha, role, adapter=self, **kwargs)


class MetadataTransport(Transport):
    """A separately funded, readonly NEW-metadata verifier after actual return."""

    role_caps = METADATA_CAPS
    shared_role = None
    shared_reserved_FULL_seconds = 0
    formal_seconds = 300
    formal_reserve_seconds = 60

    def predecessor(self, root, plan, role):
        need(root == self.root and plan == self.plan, "metadata transport plan differs")
        load("p17_m2_source_binding").admit_metadata_plan(plan, role)


def transport_for(plan):
    if plan.get("context", {}).get("execution_identity") in RECOVERY_IDENTITIES:
        return load("p17_m2_source_binding_recovery").Transport(plan)
    return MetadataTransport(plan) if plan.get("schema") == METADATA_SCHEMA else Transport(plan)


def assert_payload_launch(plan, role):
    """Refuse direct payload calls before any source observation."""
    identity, _ = execution_profile(plan)
    base = load("p17_m2_content_verified_control")
    root = Path(plan["root"])
    active = base.read_json(root / "active.json")
    started = base.read_json(root / "receipts" / role / role / "started.json")
    need(active == {"role": role, "plan_sha256": sha(canonical(plan)), "status": "ACTIVE"}
         and started["role"] == role and started["software_only"] is True
         and started.get("measurement_scope") == plan["context"]["scope"]
         and started.get("measurement_execution_identity") == identity
         and started["argv"] == argv_for(plan, "payload", role)
         and started["pid"] == os.getppid() == os.getpgrp(),
         "registered native payload parent/group/scope required")


def role_evidence(root, plan_sha, role):
    """Read NEW completed metadata only; this grants no source or retry authority."""
    base = load("p17_m2_content_verified_control")
    plan = load("p17_m2_source_binding").load_plan(Path(root) / "plan.json", plan_sha)
    transport = transport_for(plan)
    return {
        **base.read_json(Path(root) / "receipts" / (role + "-wire.json")),
        **transport.resource_evidence(Path(root), plan_sha, role, tolerate_missing=True),
    }


def audit_role(plan, role, evidence, trusted_external_record):
    """Retain a failed or incomplete role and its fixed FULL charge."""
    # Keep any actual caller span even if identity validation itself fails.
    caps = METADATA_CAPS if plan.get("schema") == METADATA_SCHEMA else CAPS
    context = plan.get("context")
    identity = context.get("execution_identity") if isinstance(context, dict) else None
    cap = caps.get(role)
    result = {
        "status": "STOP_NO_RETRY", "reason": "ACTUAL_NATIVE_RETURN_REQUIRED",
        "execution_identity": identity, "role": role,
        "frozen_FULL_seconds": cap, "charged_FULL_seconds": None,
        "known_cost_lower_bound_seconds": None,
        "whole_wall_seconds": None, "missing_evidence_cost": "UNKNOWN_NOT_ZERO",
        "full_role_evidence_accepted": False, "input_acceptance": False,
        "B_C_admission": False, "RSS_envelope_bytes": None,
        "closed_attempt_verified": False,
    }
    checker = load("p17_m2_content_verified_independent")
    completion = evidence.get("completion", {}) if isinstance(evidence, dict) else {}
    try:
        # First retain any valid caller span, even when native evidence is lost.
        first, last = checker._raw_metadata_return(trusted_external_record)
        whole = last - first
        result.update(T0=first, T1=last, whole_wall_seconds=whole,
                      known_cost_lower_bound_seconds=math.ceil(whole + 10))
        caps, window_seconds, scopes, authors = role_profile(plan)
        if (cap is not None and trusted_external_record[0]["argv"]
                == argv_for(plan, "supervise", role)
                and trusted_external_record[0].get("author") == authors[role]):
            result["charged_FULL_seconds"] = cap
            result["known_cost_lower_bound_seconds"] = max(
                cap, result["known_cost_lower_bound_seconds"])
        need(cap is not None and type(plan["roles"][role]["FULL"]) is int
             and plan["roles"][role]["FULL"] == cap, "registered FULL differs")
        pending = evidence["pending"]
        inner = evidence["inner_evidence"]
        source_children = None
        if plan['context'].get('attempt') == 2 and plan.get('coordination') and role in (
                'binding-producer', 'binding-independent'):
            wire = json.loads(inner['log'])
            failed_wire = wire.get('binding_failure') or wire.get('independent_failure') or wire
            records = failed_wire.get('source_coordination', [])
            source_children = {row['helper_pid']: row['helper_native_exit']
                               for row in records if row.get('helper_native_exit') is not None}
            source_children = source_children or None
        resources = checker.audit_resources(
            completion, inner_evidence=inner, native_profiles=evidence["native_profiles"],
            expected_identity=identity, registered_source_children=source_children)
        result["resource_evidence"] = resources
        for key in ("RSS_envelope_bytes", "RSS_components_bytes", "inner_minimum_charge_seconds"):
            result[key] = resources[key]
        if resources["inner_minimum_charge_seconds"] is not None:
            result["known_cost_lower_bound_seconds"] = max(
                result["known_cost_lower_bound_seconds"],
                math.ceil(resources["inner_minimum_charge_seconds"]))
        plan_sha = sha(canonical(plan))
        expected_schema = (METADATA_SCHEMA if caps is METADATA_CAPS
                           else "topolab.v2.m2-strict-source-binding.plan.v1")
        need(plan["schema"] == expected_schema
             and plan["context"]["execution_identity"] == identity
             and plan["context"]["scope"] in scopes, "native plan scope differs")
        attempt = plan["context"].get("attempt", 1)
        need(type(attempt) is int and attempt in (1, 2), "native attempt differs")
        if attempt == 2 or plan.get("coordination") is not None:
            load("p17_m2_source_binding_independent")._coordination_config(
                {"attempt": attempt}, plan.get("coordination"))
        need(type(plan["started_unix_ns"]) is int and type(plan["deadline_unix_ns"]) is int
             and plan["deadline_unix_ns"] - plan["started_unix_ns"] == window_seconds * 10**9
             and plan["actor_activation_UTC_seconds"] == plan["started_unix_ns"] / 10**9
             and type(plan["actor_window_seconds"]) is int
             and plan["actor_window_seconds"] == window_seconds,
             "native immutable window differs")
        need(plan["started_unix_ns"] / 10**9 <= first <= last
             <= plan["deadline_unix_ns"] / 10**9, "actual role outside immutable window")
        need(len(trusted_external_record) == 2 and [event["argv"]
             for event in trusted_external_record]
             == [argv_for(plan, mode, role) for mode in ("supervise", "record")],
             "actual external literal argv/order differs")
        need(plan["roles"][role]["author"] == authors[role]
             and all(event.get("author") == authors[role] for event in trusted_external_record),
             "actual external author differs")
        need(all(event.get("complete") is True and type(event.get("exit_code")) is int
                 for event in trusted_external_record), "actual external exit UNKNOWN")
        need(pending["execution_identity"] == identity and pending["role"] == role
             and pending["plan_sha256"] == plan_sha
             and type(pending["frozen_FULL_seconds"]) is int
             and pending["frozen_FULL_seconds"] == cap
             and pending["clock_domain"] == checker.CLOCK
             and pending["clock_resolution_seconds"] == 0.001
             and pending["status"] == "PENDING_BEFORE_DISPATCH"
             and pending["external_argv"]
             == [argv_for(plan, mode, role) for mode in ("supervise", "record")],
             "pending/native role identity differs")
        need(all(pending[key] == plan[key] and completion[key] == plan[key]
                 for key in ("actor_activation_UTC_seconds", "actor_window_seconds",
                             "actor_deadlines_UTC")), "native frozen actor window changed")
        need(completion["status"] == "PENDING_EXTERNAL_EXIT"
             and completion["pending_sha256"] == sha(canonical(pending))
             and all(completion[key] == pending[key] for key in (
                 "execution_identity", "role", "plan_sha256", "frozen_FULL_seconds",
                 "clock_domain", "clock_resolution_seconds")), "completion/pending differs")
        checker._actual_record_return(pending, completion, trusted_external_record)
        need(inner["expected_role"] == role
             and inner["expected_argv"] == argv_for(plan, "payload", role)
             and inner["record"].get("measurement_execution_identity") == identity
             and inner["record"].get("measurement_scope") == plan["context"]["scope"],
             "explicit measurement identity/scope differs")
        need(inner["record"]["timeout_seconds"] == plan["roles"][role]["timeout"]
             and type(plan["roles"][role]["timeout"]) is int
             and 0 < plan["roles"][role]["timeout"] <= cap - 10
             and inner["record"]["limit_bytes"] == 4294967296,
             "native measurement timeout/limit differs")
        need(resources["status"] == "PENDING_EXTERNAL_EXIT", str(resources["reason"]))
        minimum = resources["inner_minimum_charge_seconds"]
        need(minimum is not None and minimum - 10 <= whole + 0.001,
             "outer interval cannot contain complete native lifetime")
        result["closed_attempt_verified"] = True
        need(max(whole + 10, minimum) <= cap, "FAIL_FULL_NAMED_WALL_CHARGE_BINDING")
        result["missing_evidence_cost"] = None
        need(all(event["exit_code"] == 0 for event in trusted_external_record)
             and resources["inner_actual_exit_code"] == 0
             and all(code == 0 for code in resources["actual_component_exit_codes"])
             and completion["domain_status"] == "PASS", "payload/actual exit failure")
        if plan['context'].get('attempt') == 2 and role in (
                'binding-producer', 'binding-independent'):
            need(source_children is not None and len(records) == len(source_children) == 23,
                 'exact23 source helper native exits required')
            load('p17_m2_source_binding_independent')._coordination_trace(
                wire, plan['context'], plan['coordination'])
            need(all(first <= row['ready']['entered_ns'] / 10**9
                     <= row['release']['left_ns'] / 10**9
                     <= row['helper_native_exit']['wait_finished_ns'] / 10**9 <= last
                     for row in records), 'coordinated claim outside actual source role')
        result.update(status="PASS_STRICT_BINDING_NATIVE_ROLE", reason=None,
                      full_role_evidence_accepted=True)
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        result["reason"] = f"{type(error).__name__}: {error}"
    if isinstance(completion, dict):
        result["primary_failure"] = completion.get("primary_failure")
        result["secondary_failures"] = list(completion.get("secondary_failures", []))
    if isinstance(evidence, dict) and evidence.get("resource_read_failures"):
        result["resource_read_failures"] = evidence["resource_read_failures"]
    first = trusted_external_record[0] if trusted_external_record else {}
    failure = first.get("observed_failure", {})
    primary = failure.get("primary_error") if isinstance(failure, dict) else None
    if (result["charged_FULL_seconds"] is not None and first.get("complete") is True
            and type(first.get("exit_code")) is int and first["exit_code"] != 0
            and isinstance(failure, dict)
            and failure.get("status") == "STOP_NO_RETRY" and isinstance(primary, dict)):
        previous = result.get("primary_failure")
        if previous is not None and previous != primary:
            result.setdefault("secondary_failures", []).append(previous)
        result["primary_failure"] = primary
        result["original_supervisor_failure"] = failure
    return result


def audit_certificate(plan, evidence_by_role, trusted_events_by_role, primary, independent):
    """Bind a strict semantic pair to all five actual native/return inventories.

    This is historical replay from the plan's registered source version. It must
    not consult current source admission or silently relabel a later release.
    """
    need(plan.get("role_order") == list(CAPS)
         and set(evidence_by_role) == set(CAPS) and set(trusted_events_by_role) == set(CAPS),
         "certificate exact native role inventory differs")
    audits = {}
    previous_end = None
    for role in CAPS:
        proof = audit_role(plan, role, evidence_by_role[role], trusted_events_by_role[role])
        need(proof["full_role_evidence_accepted"], role + ": " + str(proof["reason"]))
        need(previous_end is None or previous_end <= proof["T0"],
             "actual registered roles overlap or are out of order")
        previous_end = proof["T1"]
        audits[role] = proof
    need(evidence_by_role["binding-producer"]["inner_evidence"]["log"] == canonical(primary)
         and evidence_by_role["binding-independent"]["inner_evidence"]["log"]
         == canonical(independent), "strict pair differs from actual native buffers")
    bindings = load("p17_m2_source_binding_independent").validate_pair(
        primary, independent, plan["context"], coordination=plan.get("coordination"))
    if plan["context"]["attempt"] == 2:
        for role, wire in (("binding-producer", primary), ("binding-independent", independent)):
            for record in wire["source_coordination"]:
                need(audits[role]["T0"] <= record["ready"]["entered_ns"] / 10**9
                     <= record["release"]["left_ns"] / 10**9 <= audits[role]["T1"],
                     "coordinated claim outside actual source role")
    closeout_raw = evidence_by_role["binding-closeout"]["inner_evidence"]["log"]
    closeout = json.loads(closeout_raw)
    need(canonical(closeout) == closeout_raw and set(closeout) == {
        "schema", "context", "producer_wire_sha256", "independent_wire_sha256", "bindings",
        "lease_release", "reader_returns", "own_future_return"},
        "canonical closeout fields differ")
    future = "NOT_CLAIMED_REQUIRES_SEPARATE_ACTUAL_OBSERVATION"
    need(closeout["schema"] == "topolab.v2.m2-strict-source-binding.closeout.v1"
         and closeout["context"] == plan["context"] and closeout["bindings"] == bindings
         and closeout["producer_wire_sha256"] == sha(canonical(primary))
         and closeout["independent_wire_sha256"] == sha(canonical(independent))
         and closeout["own_future_return"] == future, "closeout semantic pair differs")
    reader_returns = {role: audits[role]["T1"]
                      for role in ("binding-producer", "binding-independent")}
    need(closeout["reader_returns"] == reader_returns,
         "last source reader actual return differs")
    release, lease = closeout["lease_release"], plan["lease"]
    need(set(release) == {"schema", "path", "sha256", "identity", "state",
                          "released_unix_ns", "absence_observation"}
         and release["schema"] == "topolab.v2.m2-strict-source-binding.lease-release.v1"
         and release["state"] == "RELEASED_AFTER_SOURCE_READER_RETURNS"
         and all(release[key] == lease[key] for key in ("path", "sha256", "identity")),
         "actual cooperative lease identity/release differs")
    identity = release["identity"]
    need(isinstance(identity, dict) and set(identity) == {
        "st_dev", "st_ino", "st_size", "st_mtime_ns"}
         and all(type(value) is int for value in identity.values()),
         "original cooperative lease physical identity missing")
    released = release["released_unix_ns"]
    absence = release["absence_observation"]
    need(type(released) is int and set(absence) == {
        "errno", "observed_unix_ns", "path", "parent_before", "parent_after"}
         and type(absence["errno"]) is int and absence["errno"] == 2
         and type(absence["observed_unix_ns"]) is int
         and absence["path"] == lease["path"], "actual lease absence observation missing")
    need(audits["binding-closeout"]["T0"] <= released / 10**9
         <= absence["observed_unix_ns"] / 10**9 <= audits["binding-closeout"]["T1"]
         and max(reader_returns.values()) <= released / 10**9,
         "cooperative lease released before actual readers or outside closeout")
    before, after = absence["parent_before"], absence["parent_after"]
    need(isinstance(before, dict) and set(before) == {"st_dev", "st_ino"}
         and all(type(value) is int for value in before.values()) and before == after,
         "held parent identity changed at lease absence observation")
    certificate = {
        "schema": "topolab.v2.m2-strict-source-binding.certificate.v1",
        "execution_identity": plan["context"]["execution_identity"],
        "scope": plan["context"]["scope"],
        "plan_sha256": sha(canonical(plan)), "registered_context": plan["context"],
        "registered_source_tree": plan["context"]["source_tree"],
        "bindings": bindings, "native_role_audits": audits,
        "source_observations": independent["rows"],
        "producer_wire_sha256": sha(canonical(primary)),
        "independent_wire_sha256": sha(canonical(independent)),
        "lease_release": release, "reader_returns": reader_returns,
        "charged_FULL_seconds": sum(CAPS.values()),
        "input_acceptance": False, "B_C_admission": False,
        "historical_provenance_proved": False,
        "own_future_return": future,
        "legacy_native_helper_tag": (
            "software_only=True is the retained instrumentation label; it is not an "
            "original_source_reads=0 assertion or formal/scientific admission"),
    }
    if plan["context"]["attempt"] == 2:
        certificate["coordination"] = plan["coordination"]
        certificate["source_coordination"] = {
            "producer": primary["source_coordination"],
            "independent": independent["source_coordination"],
        }
    return certificate


def main():
    parser = argparse.ArgumentParser(prog="STRICT_BINDING_NATIVE", description=__doc__)
    parser.add_argument("mode", choices=("supervise", "run", "record"))
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--plan-sha", required=True)
    parser.add_argument("--role", required=True, choices=(*CAPS, *METADATA_CAPS))
    args = parser.parse_args()
    producer = load("p17_m2_source_binding")
    plan = producer.load_plan(args.plan, args.plan_sha)
    need(args.plan == Path(plan["root"]) / "plan.json", "literal native plan path differs")
    transport = transport_for(plan)
    base = load("p17_m2_content_verified_control")
    if args.mode == "supervise":
        result = base.supervise(Path(plan["root"]), plan, args.plan_sha, args.role,
                                adapter=transport)
    elif args.mode == "record":
        result = base.collect(Path(plan["root"]), args.plan_sha, args.role, adapter=transport)
    else:
        transport.predecessor(Path(plan["root"]), plan, args.role)
        native = transport.native_module()
        output = Path(plan["root"]) / "receipts" / args.role
        output.mkdir(mode=0o700)
        result = native.invoke(
            output, args.role, argv_for(plan, "payload", args.role),
            timeout=plan["roles"][args.role]["timeout"],
            measurement_scope=plan["context"]["scope"],
            measurement_execution_identity=transport.identity,
            registered_source_child_cap=int(plan['context'].get('attempt') == 2
                and args.role in ('binding-producer', 'binding-independent')))
        print(canonical(result).decode(), end="")
        return 0 if result["software_result"] == "PUBLIC_COMMAND_EXIT_OBSERVED" else 1
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    os.umask(0o077)
    try:
        raise SystemExit(main())
    except Exception as error:
        print(canonical({"status": "STOP_NO_RETRY", "primary_error": {
            "type": type(error).__name__, "reason": str(error)},
            "binding_failure": getattr(error, "binding_failure", None),
            "strict_binding_failure": getattr(error, "strict_binding_failure", None),
            "namespace_entry_failure": getattr(error, "namespace_entry_failure", None),
        }).decode(), end="")
        raise SystemExit(1) from error
