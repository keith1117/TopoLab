"""Native binding admission needs real resources and returned external events."""

import importlib.util
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def adapter():
    path = REPO / "scripts/p17_m2_source_binding_native.py"
    spec = importlib.util.spec_from_file_location("binding_native_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_serialized_pass_without_actual_native_return_is_stop():
    module = adapter()
    plan = {"roles": {"binding-producer": {"FULL": 300}},
            "context": {"execution_identity": module.IDENTITY}}
    result = module.audit_role(
        plan, "binding-producer", {"status": "PASS", "native_accepted": True}, [])
    assert result["status"] == "STOP_NO_RETRY"
    assert result["full_role_evidence_accepted"] is False
    assert result["frozen_FULL_seconds"] == 300
    assert result["charged_FULL_seconds"] is None
    assert result["whole_wall_seconds"] is None
    assert result["missing_evidence_cost"] == "UNKNOWN_NOT_ZERO"


def native_subject(module, *, failed=False):
    """Reuse independently authored native scalar fixtures, never their verdict."""
    spec = importlib.util.spec_from_file_location(
        "binding_native_scalar_fixture", REPO / "tests/test_p17_m2_content_verified_independent.py")
    assert spec and spec.loader
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    pending, completion, events, inner, profiles = fixture.public_role_facts(failed=failed)
    started = events[0]["start_seconds"] - 1
    deadline = started + 3600
    roles = {
        "producer-availability": {"author": "/root", "FULL": 150, "timeout": 140},
        "independent-availability": {"author": "/root/binding_route_independent_v1",
                                     "FULL": 150, "timeout": 140},
        "binding-producer": {"author": "/root", "FULL": 300, "timeout": 290},
        "binding-independent": {"author": "/root/binding_route_independent_v1",
                                "FULL": 300, "timeout": 290},
        "binding-closeout": {"author": "/root", "FULL": 180, "timeout": 160},
    }
    context = {"execution_identity": module.IDENTITY,
               "scope": "PUBLIC_STRICT_BINDING_REGISTRATION_ONLY"}
    plan = {
        "schema": "topolab.v2.m2-strict-source-binding.plan.v1",
        "root": "/private/tmp/topolab-public-strict-binding-native-audit-unit",
        "context": context, "roles": roles, "role_order": list(roles),
        "runtime": {"python": sys.executable},
        "started_unix_ns": int(started * 1_000_000_000),
        "deadline_unix_ns": int(deadline * 1_000_000_000),
        "actor_activation_UTC_seconds": started,
        "actor_window_seconds": 3600,
        "actor_deadlines_UTC": {
            key: datetime.fromtimestamp(deadline, UTC).isoformat(timespec="milliseconds")
            .replace("+00:00", "Z") for key in ("exporter", "independent")},
    }
    plan_sha = module.sha(module.canonical(plan))
    for packet in (pending, completion):
        packet.update(execution_identity=module.IDENTITY, role="binding-producer",
                      plan_sha256=plan_sha,
                      actor_activation_UTC_seconds=started,
                      actor_window_seconds=plan["actor_window_seconds"],
                      actor_deadlines_UTC=plan["actor_deadlines_UTC"])
    pending["status"] = "PENDING_BEFORE_DISPATCH"
    inner["expected_role"] = inner["record"]["role"] = "binding-producer"
    inner["expected_argv"] = inner["record"]["argv"] = module.argv_for(
        plan, "payload", "binding-producer")
    inner["record"].update(measurement_scope=context["scope"],
                            measurement_execution_identity=module.IDENTITY,
                            timeout_seconds=290, limit_bytes=4294967296)
    for event, mode in zip(events, ("supervise", "record"), strict=True):
        event["argv"] = module.argv_for(plan, mode, "binding-producer")
        event["author"] = "/root"
    pending["external_argv"] = [event["argv"] for event in events]
    fixture.seal_native_facts(fixture.load(), pending, completion, inner, profiles, events)
    evidence = {"pending": pending, "completion": completion,
                "inner_evidence": inner, "native_profiles": profiles}
    return plan, evidence, events


def test_complete_native_inventory_and_return_are_accepted_as_binding_only():
    module = adapter()
    plan, evidence, events = native_subject(module)
    result = module.audit_role(plan, "binding-producer", evidence, events)
    assert result["status"] == "PASS_STRICT_BINDING_NATIVE_ROLE"
    assert result["whole_wall_seconds"] == 17.25
    assert result["RSS_envelope_bytes"] == 980
    assert result["charged_FULL_seconds"] == 300
    assert result["full_role_evidence_accepted"] is True
    assert result["input_acceptance"] is False
    assert result["B_C_admission"] is False


def test_new_supervisor_records_registered_caps_before_any_child(tmp_path):
    import pytest

    module = adapter()
    base = module.load("p17_m2_content_verified_control")
    root = tmp_path / "topolab-public-strict-binding-supervisor-caps"
    root.mkdir(mode=0o700)

    class CapturedBeforeChild(Exception):
        pass

    class Transport:
        identity = module.IDENTITY
        scope = "PUBLIC_STRICT_BINDING_REGISTRATION_ONLY"
        role_caps = {"producer-availability": 150, "independent-availability": 150,
                     "binding-producer": 300, "binding-independent": 300,
                     "binding-closeout": 180}
        shared_role = "binding-closeout"
        formal_seconds = 3600
        formal_reserve_seconds = 600

        def predecessor(self, *args):
            return None

        def argv_for(self, *args):
            return ["new-public-test-fixture"]

        def put(self, path, value):
            return base.put(path, value)

        def native_module(self):
            raise CapturedBeforeChild

    start = round(time.time(), 3)
    plan = {"actor_activation_UTC_seconds": start,
            "actor_window_seconds": {"exporter": 3600, "independent": 3600},
            "actor_deadlines_UTC": {}, "role_order": list(Transport.role_caps)}
    with pytest.raises(CapturedBeforeChild):
        base.supervise(root, plan, "a" * 64, "binding-producer", adapter=Transport())
    pending = base.read_json(root / "receipts/binding-producer-pending.json")
    ledger = base.read_json(root / "ledger-reservation.json")
    charge = base.read_json(root / "binding-producer-dispatch-charge.json")
    assert pending["frozen_FULL_seconds"] == 300
    assert ledger["role_FULL_seconds"] == Transport.role_caps
    assert ledger["shared_reserved_FULL_seconds"] == 180
    assert charge["charged_FULL_seconds"] == 300


def test_scoped_native_measurement_refuses_arbitrary_command_before_launch(tmp_path):
    import pytest

    module = adapter()
    native = module.Transport({"root": str(tmp_path),
                               "context": {"scope": module.SCOPES[0]}}).native_module()
    with pytest.raises(ValueError, match="strict23.*literal"):
        native.invoke(tmp_path / "uncreated", "binding-producer",
                      [sys.executable, "-c", "raise RuntimeError('not authorized')"],
                      timeout=290, measurement_scope=module.SCOPES[0])
    assert not (tmp_path / "uncreated").exists()


def reseal(module, plan, evidence, events, role="binding-producer"):
    """Keep all ordinary transport hashes valid while varying the actual premise."""
    pending, completion, inner = (evidence[key] for key in
                                  ("pending", "completion", "inner_evidence"))
    for packet in (pending, completion):
        packet["plan_sha256"] = module.sha(module.canonical(plan))
        packet["role"] = role
        packet["frozen_FULL_seconds"] = (120 if role == "binding-certificate-auditor"
                                          else module.CAPS[role])
    inner["expected_role"] = inner["record"]["role"] = role
    inner["expected_argv"] = inner["record"]["argv"] = module.argv_for(plan, "payload", role)
    for event, mode in zip(events, ("supervise", "record"), strict=True):
        event["argv"] = module.argv_for(plan, mode, role)
        event["author"] = plan["roles"][role]["author"]
    pending["external_argv"] = [event["argv"] for event in events]
    completion["pending_sha256"] = module.sha(module.canonical(pending))
    completion["native_evidence_hashes"] = {
        "inner_record_canonical_sha256": module.sha(module.canonical(inner["record"])),
        "inner_profile_sha256": module.sha(inner["profile"]),
        "inner_log_sha256": module.sha(inner["log"]),
        "helper_profiles_sha256": {key: module.sha(value)
                                    for key, value in inner["helper_profiles"].items()},
        "outer_profiles_sha256": {key: module.sha(value)
                                   for key, value in evidence["native_profiles"].items()},
    }
    events[-1]["observed_pending_sha256"] = module.sha(module.canonical(pending))
    events[-1]["observed_completion_sha256"] = module.sha(module.canonical(completion))


def test_bad_FULL_does_not_erase_valid_actual_span_or_started_charge():
    module = adapter()
    plan, evidence, events = native_subject(module)
    plan["roles"]["binding-producer"]["FULL"] = True
    reseal(module, plan, evidence, events)
    result = module.audit_role(plan, "binding-producer", evidence, events)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["whole_wall_seconds"] == 17.25
    assert result["charged_FULL_seconds"] == 300


def test_fully_returned_failed_payload_is_closed_without_binding_admission():
    module = adapter()
    plan, evidence, events = native_subject(module, failed=True)
    result = module.audit_role(plan, "binding-producer", evidence, events)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["full_role_evidence_accepted"] is False
    assert result["closed_attempt_verified"] is True
    assert result["charged_FULL_seconds"] == 300
    assert result["whole_wall_seconds"] == 17.25


@pytest.mark.parametrize("damage", ["scope-missing", "scope-other", "identity-other",
                                   "profile-missing", "cleanup-unknown", "return-incomplete",
                                   "return-changed", "author-other"])
def test_native_audit_refuses_inconsistent_scope_resources_or_actual_return(damage):
    module = adapter()
    plan, evidence, events = native_subject(module)
    record = evidence["inner_evidence"]["record"]
    if damage == "scope-missing":
        del record["measurement_scope"]
    elif damage == "scope-other":
        record["measurement_scope"] = module.SCOPES[1]
    elif damage == "identity-other":
        record["measurement_execution_identity"] = "closed-old-identity"
    elif damage == "profile-missing":
        evidence["native_profiles"] = {}
    elif damage == "cleanup-unknown":
        record["cleanup"]["group_gone"] = None
    reseal(module, plan, evidence, events)
    if damage == "return-incomplete":
        events[-1]["complete"] = False
    elif damage == "return-changed":
        events[-1]["observed_completion_sha256"] = "0" * 64
    elif damage == "author-other":
        events[-1]["author"] = "/root/closed-author"
    result = module.audit_role(plan, "binding-producer", evidence, events)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["closed_attempt_verified"] is False
    assert result["full_role_evidence_accepted"] is False
    assert result["whole_wall_seconds"] == 17.25
    assert result["charged_FULL_seconds"] == 300


def certificate_subject(module, tmp_path):
    producer = module.load("p17_m2_source_binding")
    source = tmp_path / "topolab-public-strict-binding-certificate-source"
    for ordinal, row in enumerate(producer.whitelist()):
        path = source / row["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(module.canonical({"new_public_case": ordinal}))
    context = {
        "execution_identity": module.IDENTITY, "scope": module.SCOPES[0], "attempt": 1,
        "source_root": str(source), "authority_sha256": module.sha(producer.AUTHORITY.read_bytes()),
        "source_tree": producer.source_freeze(),
        "actors": {"producer": "/root", "independent": "/root/binding_route_independent_v1"},
    }
    primary = producer.register(source, context)
    checker = module.load("p17_m2_source_binding_independent")
    independent = checker.register(source, context, primary)
    bindings = checker.validate_pair(primary, independent, context)
    plan, _, _ = native_subject(module)
    plan["context"] = context
    plan["lease"] = {
        "path": str(Path(plan["root"]) / "reader-lease.json"), "sha256": "d" * 64,
        "identity": {"st_dev": 7, "st_ino": 99, "st_size": 17, "st_mtime_ns": 123456789},
    }
    evidences, actuals = {}, {}
    for ordinal, role in enumerate(module.CAPS):
        _, evidence, events = native_subject(module)
        for event in events:
            event["start_seconds"] += 30 * ordinal
            event["end_seconds"] += 30 * ordinal
            event["event_id"] += "-" + role
        evidence["inner_evidence"]["record"]["timeout_seconds"] = plan["roles"][role]["timeout"]
        payload = (primary if role == "binding-producer" else independent
                   if role == "binding-independent" else {"public_metadata_only": role})
        evidence["inner_evidence"]["log"] = module.canonical(payload)
        evidence["inner_evidence"]["record"]["log_sha256"] = module.sha(
            evidence["inner_evidence"]["log"])
        reseal(module, plan, evidence, events, role)
        evidences[role], actuals[role] = evidence, events
    release_ns = int((actuals["binding-closeout"][0]["start_seconds"] + 1) * 10**9)
    closeout = {
        "schema": "topolab.v2.m2-strict-source-binding.closeout.v1", "context": context,
        "producer_wire_sha256": module.sha(module.canonical(primary)),
        "independent_wire_sha256": module.sha(module.canonical(independent)),
        "bindings": bindings,
        "reader_returns": {role: actuals[role][-1]["end_seconds"] for role in
                           ("binding-producer", "binding-independent")},
        "own_future_return": "NOT_CLAIMED_REQUIRES_SEPARATE_ACTUAL_OBSERVATION",
        "lease_release": {
            "schema": "topolab.v2.m2-strict-source-binding.lease-release.v1",
            **plan["lease"], "state": "RELEASED_AFTER_SOURCE_READER_RETURNS",
            "released_unix_ns": release_ns,
            "absence_observation": {
                "errno": 2, "path": plan["lease"]["path"], "observed_unix_ns": release_ns + 1,
                "parent_before": {"st_dev": 7, "st_ino": 11},
                "parent_after": {"st_dev": 7, "st_ino": 11}},
        },
    }
    seal_closeout(module, plan, evidences, actuals, closeout)
    return plan, evidences, actuals, primary, independent


def seal_closeout(module, plan, evidences, actuals, closeout):
    evidence = evidences["binding-closeout"]
    evidence["inner_evidence"]["log"] = module.canonical(closeout)
    evidence["inner_evidence"]["record"]["log_sha256"] = module.sha(
        evidence["inner_evidence"]["log"])
    reseal(module, plan, evidence, actuals["binding-closeout"], "binding-closeout")


def test_certificate_replays_native_strict_pair_and_actual_lease_return(tmp_path):
    module = adapter()
    facts = certificate_subject(module, tmp_path)
    certificate = module.audit_certificate(*facts)
    assert len(certificate["bindings"]) == 23
    assert certificate["charged_FULL_seconds"] == 1080
    assert certificate["input_acceptance"] is False
    assert certificate["B_C_admission"] is False
    assert certificate["historical_provenance_proved"] is False
    assert certificate["own_future_return"].startswith("NOT_CLAIMED")
    assert certificate["source_observations"] == facts[-1]["rows"]
    assert "coordination" not in certificate and "source_coordination" not in certificate


@pytest.mark.parametrize("damage", ["release-before-reader", "lease-replaced",
                                   "parent-replaced", "absence-missing", "reader-return-forged",
                                   "pair-log-detached"])
def test_certificate_rejects_native_sealed_false_closeout_claims(tmp_path, damage):
    module = adapter()
    plan, evidences, events, primary, independent = certificate_subject(module, tmp_path)
    closeout = json.loads(evidences["binding-closeout"]["inner_evidence"]["log"])
    if damage == "release-before-reader":
        closeout["lease_release"]["released_unix_ns"] = int(
            (closeout["reader_returns"]["binding-independent"] - 1) * 10**9)
    elif damage == "lease-replaced":
        closeout["lease_release"]["identity"]["st_ino"] += 1
    elif damage == "parent-replaced":
        closeout["lease_release"]["absence_observation"]["parent_after"]["st_ino"] += 1
    elif damage == "absence-missing":
        del closeout["lease_release"]["absence_observation"]
    elif damage == "reader-return-forged":
        closeout["reader_returns"]["binding-independent"] -= 1
    else:
        closeout["producer_wire_sha256"] = "0" * 64
    seal_closeout(module, plan, evidences, events, closeout)
    with pytest.raises(ValueError):
        module.audit_certificate(plan, evidences, events, primary, independent)


def metadata_subject(module):
    plan, evidence, events = native_subject(module)
    role = "binding-certificate-auditor"
    plan["schema"] = "topolab.v2.m2-strict-source-binding.metadata-plan.v1"
    plan["context"]["scope"] = "STRICT_BINDING_CERTIFICATE_METADATA_ONLY"
    plan["role_order"] = [role]
    plan["roles"] = {role: {"author": "/root/binding_route_independent_v1",
                            "FULL": 120, "timeout": 110}}
    plan["actor_window_seconds"] = 300
    plan["deadline_unix_ns"] = plan["started_unix_ns"] + 300 * 10**9
    deadline = plan["actor_activation_UTC_seconds"] + 300
    plan["actor_deadlines_UTC"] = {
        key: datetime.fromtimestamp(deadline, UTC).isoformat(timespec="milliseconds")
        .replace("+00:00", "Z") for key in ("exporter", "independent")}
    for packet in (evidence["pending"], evidence["completion"]):
        packet["actor_window_seconds"] = 300
        packet["actor_deadlines_UTC"] = plan["actor_deadlines_UTC"]
    evidence["inner_evidence"]["record"].update(
        measurement_scope=plan["context"]["scope"], timeout_seconds=110)
    reseal(module, plan, evidence, events, role)
    return plan, evidence, events


def test_metadata_auditor_has_separate_native_cap_and_actual_return():
    module = adapter()
    plan, evidence, events = metadata_subject(module)
    result = module.audit_role(plan, "binding-certificate-auditor", evidence, events)
    assert result["status"] == "PASS_STRICT_BINDING_NATIVE_ROLE"
    assert result["closed_attempt_verified"] is True
    assert result["charged_FULL_seconds"] == 120
    assert result["whole_wall_seconds"] == 17.25
    assert result["input_acceptance"] is False
    assert result["B_C_admission"] is False


@pytest.mark.parametrize("scope,role", [
    ("STRICT_BINDING_CERTIFICATE_METADATA_ONLY", "binding-producer"),
    ("FORMAL_STRICT_BINDING_REGISTRATION_ONLY", "binding-certificate-auditor"),
])
def test_metadata_measurement_scope_cannot_launch_source_role(tmp_path, scope, role):
    module = adapter()
    native = module.Transport({"root": str(tmp_path),
                               "context": {"scope": module.SCOPES[0]}}).native_module()
    argv = [sys.executable, "-I", str(REPO / "scripts/p17_m2_source_binding.py"), "payload",
            "--plan", str(tmp_path / "plan.json"), "--plan-sha", "a" * 64, "--role", role]
    with pytest.raises(ValueError, match="strict23.*literal"):
        native.invoke(tmp_path / "uncreated", role, argv, timeout=110, measurement_scope=scope)
    assert not (tmp_path / "uncreated").exists()


def test_metadata_supervisor_has_no_core_shared_prepayment(tmp_path):
    module = adapter()
    base = module.load("p17_m2_content_verified_control")
    root = tmp_path / "topolab-public-strict-binding-metadata-caps"
    root.mkdir(mode=0o700)

    class CapturedBeforeChild(Exception):
        pass

    class Metadata(module.MetadataTransport):
        def predecessor(self, *args):
            return None

        def native_module(self):
            raise CapturedBeforeChild

    started = round(time.time(), 3)
    plan = {"schema": module.METADATA_SCHEMA, "root": str(root),
            "runtime": {"python": sys.executable},
            "context": {"scope": module.METADATA_SCOPE},
            "actor_activation_UTC_seconds": started, "actor_window_seconds": 300,
            "actor_deadlines_UTC": {}, "role_order": ["binding-certificate-auditor"]}
    plan_sha = module.sha(module.canonical(plan))
    with pytest.raises(CapturedBeforeChild):
        base.supervise(root, plan, plan_sha, "binding-certificate-auditor", adapter=Metadata(plan))
    pending = base.read_json(root / "receipts/binding-certificate-auditor-pending.json")
    ledger = base.read_json(root / "ledger-reservation.json")
    charge = base.read_json(root / "binding-certificate-auditor-dispatch-charge.json")
    assert pending["frozen_FULL_seconds"] == 120
    assert ledger["shared_reserved_FULL_seconds"] == 0
    assert ledger["role_FULL_seconds"] == {"binding-certificate-auditor": 120}
    assert charge["charged_FULL_seconds"] == 120


def coordinated_native_subject(module, tmp_path):
    """Captured semantic/native scalar fixture, not actual Foundation execution."""
    plan, evidences, events, primary, independent = certificate_subject(module, tmp_path)
    plan["context"]["attempt"] = 2
    plan["coordination"] = {
        "identity": "topolab.source-read.foundation-coordination.v1",
        "binary": str(tmp_path / "new-public-native-helper"), "sha256": "3" * 64,
        "request_timeout_seconds": 10, "release_timeout_seconds": 5, "reading_options": 0,
        "source_swift_sha256": "4" * 64, "compiler_sha256": "5" * 64,
    }
    for role, wire in (("binding-producer", primary), ("binding-independent", independent)):
        wire["attempt"] = 2
        wire["source_coordination"] = []
        start = int(events[role][0]["start_seconds"] * 10**9) + 1000
        for ordinal, row in enumerate(wire["rows"]):
            url = (Path(wire["source_root"]) / row["path"]).as_uri()
            pid, entered = 2000 + ordinal, start + ordinal * 1000
            wire["source_coordination"].append({
                "path": row["path"], "requested_url": url, "accessor_url": url,
                "namespace_before": dict(row["declared"]),
                "helper_pid": pid, "helper_sha256": plan["coordination"]["sha256"],
                "strategy_identity": plan["coordination"]["identity"],
                "ready": {"event": "accessor_entered", "pid": pid,
                          "requested_url": url, "accessor_url": url, "entered_ns": entered},
                "reader_start_ns": entered + 1, "reader_end_ns": entered + 2,
                "release_requested_ns": entered + 3,
                "release": {"event": "accessor_returned", "pid": pid, "left_ns": entered + 4},
                "helper_exit_code": 0,
                "helper_native_exit": {"pid": pid,"exit_code":0,
                    "statistics_source":"os.wait4","platform":"darwin","rss_unit":"bytes",
                    "native":{"rss_bytes":30,"user_seconds":.01,"system_seconds":.01},
                    "wait_finished_ns":entered+5},
            })
        evidence = evidences[role]
        evidence["inner_evidence"]["record"]["registered_source_child_cap"] = 1
        evidence["inner_evidence"]["log"] = module.canonical(wire)
        evidence["inner_evidence"]["record"]["log_sha256"] = module.sha(
            evidence["inner_evidence"]["log"])
    closeout = json.loads(evidences["binding-closeout"]["inner_evidence"]["log"])
    closeout["context"] = plan["context"]
    closeout["producer_wire_sha256"] = module.sha(module.canonical(primary))
    closeout["independent_wire_sha256"] = module.sha(module.canonical(independent))
    seal_closeout(module, plan, evidences, events, closeout)
    for role in module.CAPS:
        reseal(module, plan, evidences[role], events[role], role)
    return plan, evidences, events, primary, independent


def test_attempt2_native_role_requires_frozen_coordination_without_erasing_charge():
    module = adapter()
    plan, evidence, events = native_subject(module)
    plan["context"]["attempt"] = 2
    reseal(module, plan, evidence, events)
    result = module.audit_role(plan, "binding-producer", evidence, events)
    assert result["status"] == "STOP_NO_RETRY"
    assert "coordinated strategy configuration" in result["reason"]
    assert result["charged_FULL_seconds"] == 300
    assert result["whole_wall_seconds"] == 17.25


def test_attempt2_certificate_binds_config_and_both_claim_inventories(tmp_path):
    module = adapter()
    facts = coordinated_native_subject(module, tmp_path)
    certificate = module.audit_certificate(*facts)
    assert certificate["coordination"] == facts[0]["coordination"]
    assert certificate["source_coordination"] == {
        "producer": facts[-2]["source_coordination"],
        "independent": facts[-1]["source_coordination"],
    }
    assert certificate["charged_FULL_seconds"] == 1080
    assert certificate["input_acceptance"] is False and certificate["B_C_admission"] is False


@pytest.mark.parametrize("damage", ["options", "timeout", "binary_hash", "identity"])
def test_attempt2_native_role_rejects_unfrozen_strategy_in_metadata_replay(tmp_path, damage):
    module = adapter()
    plan, evidences, events, _, _ = coordinated_native_subject(module, tmp_path)
    if damage == "options":
        plan["coordination"]["reading_options"] = True
    elif damage == "timeout":
        plan["coordination"]["request_timeout_seconds"] = 11
    elif damage == "binary_hash":
        plan["coordination"]["sha256"] = "not a hash"
    else:
        plan["coordination"]["identity"] = "unregistered-strategy"
    role = "binding-producer"
    reseal(module, plan, evidences[role], events[role], role)
    result = module.audit_role(plan, role, evidences[role], events[role])
    assert result["status"] == "STOP_NO_RETRY"
    assert result["charged_FULL_seconds"] == 300 and result["whole_wall_seconds"] == 17.25
    assert result["resource_evidence"]["RSS_envelope_bytes"] == 1010


@pytest.mark.parametrize("role", ["binding-producer", "binding-independent"])
def test_coordinated_claim_cannot_outlive_or_predate_actual_source_role(tmp_path, role):
    module = adapter()
    plan, evidences, events, primary, independent = coordinated_native_subject(module, tmp_path)
    wire = primary if role == "binding-producer" else independent
    # Shift the whole serial inventory, so only its actual-role bound is damaged.
    for row in wire["source_coordination"]:
        for key in ("reader_start_ns", "reader_end_ns", "release_requested_ns"):
            row[key] += 10**15
        row["ready"]["entered_ns"] += 10**15
        row["release"]["left_ns"] += 10**15
        row["helper_native_exit"]["wait_finished_ns"] += 10**15
    evidence = evidences[role]
    evidence["inner_evidence"]["log"] = module.canonical(wire)
    evidence["inner_evidence"]["record"]["log_sha256"] = module.sha(
        evidence["inner_evidence"]["log"])
    reseal(module, plan, evidence, events[role], role)
    with pytest.raises(ValueError, match="outside actual source role"):
        module.audit_certificate(plan, evidences, events, primary, independent)
