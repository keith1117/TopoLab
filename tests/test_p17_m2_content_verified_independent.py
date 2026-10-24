"""Behavior checks at the independently authored content-verification seam."""

import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest


def load():
    path = Path(__file__).resolve().parents[1] / "scripts/p17_m2_content_verified_independent.py"
    name = "p17_m2_content_verified_independent"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def test_missing_actual_outer_return_keeps_FULL_and_refuses_consumption():
    checker = load()
    result = checker.audit_role(
        {},
        {"status": "PASS", "resource_pass": True},
        raw_tool_events=[],
        expected_role="exporter-r0",
        expected_plan_sha256="a" * 64,
    )
    assert result["status"] == "STOP_NO_RETRY"
    assert result["whole_wall_seconds"] is None
    assert result["frozen_FULL_seconds"] == 300
    assert result["known_cost_lower_bound_seconds"] == 300
    assert result["full_role_evidence_accepted"] is False
    assert result["source_successor_admitted"] is False
    assert result["B_C_admission"] is False
    assert "OUTER" in result["reason"]


def test_late_outer_return_retains_valid_wall_and_FULL_despite_window_STOP():
    checker = load()
    result = checker.audit_role(
        {
            "execution_identity": "topolab.v2.p17-m2-content-verified-input.v1",
            "role": "exporter-r0",
            "plan_sha256": "a" * 64,
            "frozen_FULL_seconds": 300,
            "clock_domain": "functions.exec.Date.now.UTC-seconds",
            "clock_resolution_seconds": 0.001,
            "actor_activation_UTC_seconds": 1000.0,
            "actor_window_seconds": 4500,
            "actor_deadlines_UTC": {
                "exporter": "1970-01-01T01:31:40.000Z",
                "independent": "1970-01-01T01:31:40.000Z",
            },
        },
        {},
        raw_tool_events=[
            {
                "event_id": "actual-late-return",
                "start_seconds": 5490.0,
                "end_seconds": 5520.0,
                "wall_seconds": 30.0,
                "clock_domain": "functions.exec.Date.now.UTC-seconds",
                "argv": ["python", "-I", "new-public-check.py"],
                "complete": True,
                "exit_code": 0,
            }
        ],
        expected_role="exporter-r0",
        expected_plan_sha256="a" * 64,
    )
    assert result["status"] == "STOP_NO_RETRY"
    assert result["whole_wall_seconds"] == 30
    assert result["known_cost_lower_bound_seconds"] == 300
    assert "window" in result["reason"]


def public_role_facts(*, failed=False):
    # Reuse only the independently authored tiny native fixture, never its PASS oracle.
    path = Path(__file__).with_name("test_p17_m2_input_export_independent.py")
    spec = importlib.util.spec_from_file_location("independent_native_fixture", path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    pending, completion, events, inner = fixture.stable_recording_subject(
        role="exporter-r0", failed=failed
    )
    for item in (pending, completion):
        item["execution_identity"] = "topolab.v2.p17-m2-content-verified-input.v1"
    inner["expected_role"] = inner["record"]["role"] = "exporter-r0"
    raw = (
        json.dumps(pending, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n"
    ).encode("ascii")
    completion["pending_sha256"] = hashlib.sha256(raw).hexdigest()
    profiles = fixture.failure_recording_profiles()
    seal_native_facts(load(), pending, completion, inner, profiles, events)
    return pending, completion, events, inner, profiles


def seal_native_facts(checker, pending, completion, inner, profiles, events):
    """Unit observer binds the returned packet to each raw artifact, without PASS flags."""
    completion["pending_sha256"] = checker.digest(checker.canonical(pending))
    completion["native_evidence_hashes"] = {
        "inner_record_canonical_sha256": checker.digest(checker.canonical(inner["record"])),
        "inner_profile_sha256": checker.digest(inner["profile"]),
        "inner_log_sha256": checker.digest(inner["log"]),
        "helper_profiles_sha256": {
            name: checker.digest(raw) for name, raw in inner["helper_profiles"].items()
        },
        "outer_profiles_sha256": {name: checker.digest(raw) for name, raw in profiles.items()},
    }
    events[-1]["observed_pending_sha256"] = checker.digest(checker.canonical(pending))
    events[-1]["observed_completion_sha256"] = checker.digest(checker.canonical(completion))


def test_actual_record_return_must_bind_the_supplied_completion_without_losing_cost():
    checker = load()
    facts = public_role_facts()
    facts[2][-1]["observed_completion_sha256"] = "0" * 64
    result = audit_public_role(checker, facts)
    assert result["status"] == "STOP_NO_RETRY"
    assert "actual record return" in result["reason"]
    assert result["whole_wall_seconds"] == 17.25
    assert result["RSS_envelope_bytes"] == 980
    assert result["known_cost_lower_bound_seconds"] == 300


def test_role_receipt_cannot_relabel_another_native_role_with_consistent_transport():
    checker = load()
    pending, completion, events, inner, profiles = public_role_facts()
    inner["expected_role"] = inner["record"]["role"] = "exporter-r1"
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    proof = audit_public_role(checker, (pending, completion, events, inner, profiles))
    assert proof["status"] == "STOP_NO_RETRY"
    assert "native role" in proof["reason"]
    assert proof["known_cost_lower_bound_seconds"] == 300


@pytest.mark.parametrize(
    "field",
    [
        "inner_record_canonical_sha256",
        "inner_profile_sha256",
        "inner_log_sha256",
        "helper_profiles_sha256",
        "outer_profiles_sha256",
    ],
)
def test_actual_return_cannot_rebind_a_different_native_artifact_manifest(field):
    checker = load()
    facts = public_role_facts()
    pending, completion, events, inner, profiles = facts
    manifest = completion["native_evidence_hashes"]
    manifest[field] = {} if isinstance(manifest[field], dict) else "0" * 64
    events[-1]["observed_completion_sha256"] = checker.digest(checker.canonical(completion))
    result = audit_public_role(checker, facts)
    assert result["status"] == "STOP_NO_RETRY"
    assert "native evidence hash manifest" in result["reason"]
    assert result["whole_wall_seconds"] == 17.25
    assert result["RSS_envelope_bytes"] == 980
    assert result["inner_minimum_charge_seconds"] is not None
    assert result["known_cost_lower_bound_seconds"] == 300


def audit_public_role(checker, facts):
    pending, completion, events, inner, profiles = facts
    return checker.audit_role(
        pending,
        completion,
        raw_tool_events=events,
        expected_role="exporter-r0",
        expected_plan_sha256="a" * 64,
        inner_evidence=inner,
        native_profiles=profiles,
    )


def test_independent_role_reconciles_raw_native_inventory_and_full_cost():
    result = audit_public_role(load(), public_role_facts())
    assert result["status"] == "PASS_CONTENT_VERIFIED_PUBLIC_ROLE"
    assert result["whole_wall_seconds"] == 17.25
    assert result["RSS_envelope_bytes"] == 980
    assert result["known_cost_lower_bound_seconds"] == 300
    assert result["full_role_evidence_accepted"] is True
    assert result["source_successor_admitted"] is False
    assert result["B_C_admission"] is False


def test_independent_adapter_refuses_old_or_proposed_roots_before_filesystem():
    import pytest

    checker = load()
    for root in (
        "/Users/keith1117/Documents/TopoLab-data",
        "/Users/keith1117/Library/Application Support/TopoLab-custody",
    ):
        with pytest.raises(ValueError, match="public temporary"):
            checker.independent_r0(Path(root), {}, {}, [], {})


def public_content_facts(tmp_path, monkeypatch, *, contract_sha="f" * 64):
    """Connected new data; the existing public constructor supplies no acceptance oracle."""
    spec = importlib.util.spec_from_file_location(
        "content_verified_public_constructor",
        Path(__file__).with_name("test_p17_m2_local_input_pipeline.py"),
    )
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    independent = fixture.load("p17_m2_local_input_independent")
    producer = fixture.load("p17_m2_input_export")
    local = fixture.load("p17_m2_local_input_version")
    source = tmp_path / "public-source"
    contract = fixture.complete_sources(source, independent.base, monkeypatch)
    public_identity = {
        "B3_DATA_HASH": independent.base.B3_DATA_HASH,
        "CATALOG_HASH": independent.base.CATALOG_HASH,
    }
    r0 = producer.Reader(source, execution_identity=local.IDENTITY, source_identity_checks=True)
    registry = producer.register(r0, contract)
    content = local.LocalContent(tmp_path / "content", registry, contract_sha)
    content.write("source_registry.json", producer.canonical(registry))
    r1 = producer.Reader(source, execution_identity=local.IDENTITY, source_identity_checks=True)
    producer.export(r1, registry, contract, content.root, local_content=content)
    closed = content.finish()
    closed["root_identity"] = {
        key: getattr(content.root.stat(), key)
        for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    }
    return (
        source,
        contract,
        registry,
        r0.source_observations,
        r1.source_observations,
        content.root,
        closed,
        public_identity,
    )


def test_new_public_adapter_derives_R0_from_exact40_and_retains_distinct_helper_scope(
    tmp_path, monkeypatch
):
    checker = load()
    source, contract, registry, producer_rows, _, _, _, public_identity = public_content_facts(
        tmp_path, monkeypatch
    )
    result = checker.independent_r0(source, contract, registry, producer_rows, public_identity)
    assert result["status"] == "PUBLIC_INDEPENDENT_R0_CHECKED"
    assert result["scope"] == "PUBLIC_SOFTWARE_FIXTURE_ONLY"
    assert result["source_count"] == 40
    assert len(result["source_rows"]) == 40
    assert result["source_comparison"] == "ALL_FIELDS_AND_PHYSICAL_TUPLES_MATCHED"
    assert result["helper_identity_relabelled"] is False
    assert result["B_C_admission"] is False


def test_new_public_R1_checks_558_source_records_and_all1071_local_identities(
    tmp_path, monkeypatch
):
    checker = load()
    source, _, registry, _, rows, content, closed, public_identity = public_content_facts(
        tmp_path, monkeypatch
    )
    result = checker.independent_r1(
        source, content, registry, rows, closed, "f" * 64, public_identity
    )
    assert result["status"] == "PUBLIC_INDEPENDENT_R1_CHECKED"
    assert result["source_count"] == 558
    assert len(result["source_rows"]) == 558
    assert len(result["local_identity_rows"]) == 1071
    assert result["version_id"] == closed["version_id"]
    assert result["source_comparison"] == "ALL_FIELDS_AND_PHYSICAL_TUPLES_MATCHED"
    assert result["compared_fields"] > 50000
    assert result["scope"] == "PUBLIC_SOFTWARE_FIXTURE_ONLY"
    assert result["B_C_admission"] is False


def test_opaque_public_certificate_cannot_be_constructed_from_a_PASS_dictionary():
    import pytest

    checker = load()
    with pytest.raises(ValueError, match="independent verification"):
        checker.CheckedPublicInput({"status": "PASS", "scope": "PUBLIC_SOFTWARE_FIXTURE_ONLY"})
    with pytest.raises(ValueError, match="actual"):
        checker.audit_public_certificate({"status": "PASS"}, trusted_tool_events={})


def test_public_filing_uses_result_deadline_and_preserves_FULL180():
    from datetime import UTC, datetime

    checker = load()
    facts = list(public_role_facts())
    pending, completion, events, inner, _ = facts
    inner["expected_role"] = inner["record"]["role"] = "final-filing"
    for item in (pending, completion):
        item.update(
            role="final-filing",
            frozen_FULL_seconds=180,
            result_start_UTC_seconds=5500.0,
            result_deadlines_UTC={
                actor: datetime.fromtimestamp(5500 + seconds, UTC)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
                for actor, seconds in (("exporter", 7200), ("independent", 3600))
            },
        )
    events[0].update(start_seconds=5600.0, end_seconds=5607.015)
    events[1].update(start_seconds=5617.0, end_seconds=5617.25)
    completion["pending_sha256"] = checker.digest(checker.canonical(pending))
    seal_native_facts(checker, pending, completion, inner, facts[-1], events)
    result = checker.audit_role(
        pending,
        completion,
        raw_tool_events=events,
        expected_role="final-filing",
        expected_plan_sha256="a" * 64,
        inner_evidence=inner,
        native_profiles=facts[-1],
    )
    assert result["status"] == "PASS_CONTENT_VERIFIED_PUBLIC_ROLE"
    assert result["frozen_FULL_seconds"] == 180
    assert result["known_cost_lower_bound_seconds"] == 180
    assert result["whole_wall_seconds"] == 17.25


def test_independent_backup_checks_all_members_and_distinct_physical_identities(
    tmp_path, monkeypatch
):
    import shutil

    checker = load()
    _, _, registry, _, _, content, closed, _ = public_content_facts(tmp_path, monkeypatch)
    backup = tmp_path / "backup"
    shutil.copytree(content, backup, copy_function=shutil.copyfile)
    for directory in [backup, *[p for p in backup.rglob("*") if p.is_dir()]]:
        directory.chmod(0o700)
    for member in [p for p in backup.rglob("*") if p.is_file()]:
        member.chmod(0o600)
    result = checker.independent_backup(content, backup, closed, registry, "f" * 64)
    assert result["status"] == "PUBLIC_INDEPENDENT_BACKUP_CHECKED"
    assert result["member_count"] == 1071
    assert result["version_id"] == closed["version_id"]
    assert result["root"] == str(backup)
    assert result["own_root"] == str(content)
    assert len(result["identity_rows"]) == 1071
    assert result["identity_rows"][0]["before"] != closed["local_identity_rows"][0]["before"]
    assert result["B_C_admission"] is False


def public_software_facts(root, checker):
    import platform

    repo = Path(__file__).parents[1]
    paths = [*repo.glob("scripts/p17_m2_*.py"), *repo.glob("scripts/p17_m2_*.js")]
    paths += [
        repo / name
        for name in (
            "docs/planning/p17_m2_content_verified_custody_protocol.json",
            "docs/planning/p17_m2_content_verified_custody_proposal.json",
            "docs/planning/p17_m2_input_export_preparation_proposal.json",
        )
    ]
    python = str(Path(sys.orig_argv[0]).resolve())
    script = str(repo / "scripts/p17_m2_content_verified_control.py")
    runtime = {
        "python": python,
        "python_sha256": checker.digest(Path(python).read_bytes()),
        "isolated": 1,
        "cwd": str(repo),
        "platform": sys.platform,
        "os_release": platform.release(),
        "lock_sha256": checker.digest((repo / "uv.lock").read_bytes()),
        "threads": {
            name: "1"
            for name in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
        "orig_argv": [python, "-I", script, "prepare-public", "--root", str(root)],
    }
    return {
        "runtime": runtime,
        "source_tree": {
            str(path.relative_to(repo)): checker.digest(path.read_bytes()) for path in paths
        },
    }


def native_facts_for_host(checker, completion, inner, profiles):
    if sys.platform != "linux":
        return

    def scale(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {
                    "rss_bytes",
                    "controller_rss_peak_bytes",
                    "controller_rss_bytes",
                    "group_plus_controller_rss_bytes",
                    "native_plus_controller_and_sampler_rss_bytes",
                }:
                    value[key] = item * 1024
                elif key == "samples_bytes":
                    value[key] = [x * 1024 for x in item]
                else:
                    scale(item)
            if value.get("statistics_source") == "os.wait4":
                value["rss_unit"] = "KiB*1024"
        elif isinstance(value, list):
            for item in value:
                scale(item)

    scale(completion["resource_components"])
    scale(inner["record"])
    inner["platform"] = inner["record"]["platform"] = "linux"
    inner["record"]["native_rss_unit"] = "KiB*1024"
    inner["profile"] = b"TOPOLAB_NATIVE 1.0 0.1 0.0 100\n"
    inner["record"]["profile_sha256"] = checker.digest(inner["profile"])
    inner["helper_profiles"] = {"sampler-0.time": b"TOPOLAB_NATIVE 0.02 0.01 0.0 20\n"}
    inner["record"]["helpers"][0]["profile_sha256"] = checker.digest(
        inner["helper_profiles"]["sampler-0.time"]
    )
    profiles["F-outer-native"] = b"TOPOLAB_NATIVE 0.1 0.0 0.0 180\n"
    for item in completion["resource_components"]:
        if "platform" in item:
            item["platform"] = "linux"
        if item["kind"] == "native_profile":
            item["profile_sha256"] = checker.digest(profiles["F-outer-native"])


def public_certificate_facts(tmp_path, monkeypatch, *, contract_sha=None):
    """Unit-only synthetic tool facts around genuinely independently checked new content."""
    import shutil
    from datetime import UTC, datetime

    checker = load()
    if contract_sha is None:
        contract_sha = checker.digest(
            (
                Path(checker.__file__).parents[1]
                / "docs/planning/p17_m2_content_verified_custody_protocol.json"
            ).read_bytes()
        )
    source, contract, registry, r0_rows, r1_rows, content, closed, public_identity = (
        public_content_facts(tmp_path, monkeypatch, contract_sha=contract_sha)
    )
    r0 = checker.independent_r0(source, contract, registry, r0_rows, public_identity)
    r1 = checker.independent_r1(
        source, content, registry, r1_rows, closed, contract_sha, public_identity
    )
    backup_root = tmp_path / "backup-content"
    shutil.copytree(content, backup_root, copy_function=shutil.copyfile)
    for member in backup_root.rglob("*"):
        member.chmod(0o700 if member.is_dir() else 0o600)
    backup_root.chmod(0o700)
    backup = checker.independent_backup(content, backup_root, closed, registry, contract_sha)
    order = [
        "independent-public-check",
        "exporter-r0",
        "independent-r0",
        "exporter-r1",
        "independent-r1",
        "shared-closeout",
    ]
    plan = {
        "execution_identity": checker.EXECUTION_IDENTITY,
        "scope": checker.PUBLIC_SCOPE,
        "root": str(tmp_path),
        "role_order": order,
        "formal_authority": False,
        "contract_sha256": contract_sha,
        "content_contract": contract,
        "public_source_identity": public_identity,
        "actor_activation_UTC_seconds": 1000.0,
        "actor_window_seconds": 4500,
        "actor_deadlines_UTC": {
            "exporter": "1970-01-01T01:31:40.000Z",
            "independent": "1970-01-01T01:31:40.000Z",
        },
        **public_software_facts(tmp_path, checker),
        "roles": {
            role: {
                "argv": [
                    str(Path(sys.orig_argv[0]).resolve()),
                    "-I",
                    str(Path(checker.__file__).with_name("p17_m2_content_verified_control.py")),
                    "payload",
                    "--root",
                    str(tmp_path),
                    "--plan-sha",
                    "@PLAN_SHA256@",
                    "--role",
                    role,
                ]
            }
            for role in order
        },
        "metadata_actions": {
            **{
                role: {
                    "argv": [
                        str(Path(sys.orig_argv[0]).resolve()),
                        "-I",
                        str(Path(checker.__file__).with_name("p17_m2_content_verified_control.py")),
                        "payload",
                        "--root",
                        str(tmp_path),
                        "--plan-sha",
                        "@PLAN_SHA256@",
                        "--role",
                        role,
                    ]
                }
                for role in ["final-filing", "lease-release"]
            },
            **{role: {"argv": list(sys.orig_argv)} for role in ["public-consumer", "reader-ack"]},
        },
    }
    plan_sha = checker.digest(checker.canonical(plan))
    roles, trusted = {}, {}
    shared_sha = "b" * 64
    filing_proof = {
        "status": "PUBLIC_FILING_SNAPSHOT_WRITTEN",
        "scope": checker.PUBLIC_SCOPE,
        "execution_identity": checker.EXECUTION_IDENTITY,
        "plan_sha256": plan_sha,
        "version_id": closed["version_id"],
        "manifest_sha256": closed["version_id"],
        "shared_packet_sha256": shared_sha,
        "endpoint": "FINITE_SNAPSHOT_EXCLUDES_OWN_FUTURE_RETURN",
    }
    caps = {
        "independent-public-check": 300,
        "exporter-r0": 300,
        "independent-r0": 300,
        "exporter-r1": 1200,
        "independent-r1": 1200,
        "shared-closeout": 300,
    }
    reservation = {
        "shared_reserved_FULL_seconds": 300,
        "role_FULL_seconds": caps,
        "refunds_allowed": False,
        "scope": checker.PUBLIC_SCOPE,
        "execution_identity": checker.EXECUTION_IDENTITY,
        "plan_sha256": plan_sha,
        "reserved_UTC_seconds": 1010.001,
    }
    reservation_sha = checker.digest(checker.canonical(reservation))
    backup["billing_ledger"] = {
        "reservation": reservation,
        "first_dispatch_launch_UTC_seconds": 1010.01,
        "dispatch_charges": [
            {
                "role": role,
                "frozen_FULL_seconds": caps[role],
                "charged_FULL_seconds": 0 if role == "shared-closeout" else caps[role],
                "charged_UTC_seconds": 1010.005 + index * 25,
                "scope": checker.PUBLIC_SCOPE,
                "execution_identity": checker.EXECUTION_IDENTITY,
                "plan_sha256": plan_sha,
                "shared_reservation_sha256": reservation_sha,
            }
            for index, role in enumerate(order)
        ],
    }
    filing_proof["billing_charge"] = {
        "role": "final-filing",
        "frozen_FULL_seconds": 180,
        "charged_FULL_seconds": 180,
        "charged_UTC_seconds": 1160.005,
        "scope": checker.PUBLIC_SCOPE,
        "execution_identity": checker.EXECUTION_IDENTITY,
        "plan_sha256": plan_sha,
        "shared_reservation_sha256": reservation_sha,
    }
    payloads = {
        "independent-r0": r0,
        "independent-r1": r1,
        "shared-closeout": backup,
        "final-filing": filing_proof,
    }
    backup["custody_lease"] = {
        "scope": "COOPERATIVE_REGISTERED_TOPOLAB_ONLY",
        "execution_identity": checker.EXECUTION_IDENTITY,
        "root": str(content),
        "version_id": closed["version_id"],
        "registered_readers": [*order, "final-filing"],
        "acquired_UTC_seconds": 1000.0,
        "acquired_monotonic": 100.0,
        "state": "HELD",
        "last_reader_return": None,
    }
    acquired = dict(backup["custody_lease"], version_id=None)
    backup["custody_log"] = [
        acquired,
        {
            "event": "VERSION_BOUND",
            "acquired_record_sha256": checker.digest(checker.canonical(acquired)),
            "version_id": closed["version_id"],
            "UTC_seconds": 1090.0,
            "monotonic": 101.0,
        },
    ]
    for index, role in enumerate([*order, "final-filing", "lease-release"]):
        if role == "final-filing":
            accepted = {
                r: checker.audit_role(
                    roles[r]["pending"],
                    roles[r]["completion"],
                    raw_tool_events=trusted[r],
                    expected_role=r,
                    expected_plan_sha256=plan_sha,
                    inner_evidence=roles[r]["inner_evidence"],
                    native_profiles=roles[r]["native_profiles"],
                )
                for r in order
            }
            shared_sha = checker.digest(checker.canonical(accepted))
            filing_proof["shared_packet_sha256"] = shared_sha
        pending, completion, events, inner, profiles = public_role_facts()
        native_facts_for_host(checker, completion, inner, profiles)
        table = plan["roles"] if role in order else plan["metadata_actions"]
        argv = [word.replace("@PLAN_SHA256@", plan_sha) for word in table[role]["argv"]]
        for item in (pending, completion):
            item.update(
                role=role, plan_sha256=plan_sha, frozen_FULL_seconds=checker.FULL_SECONDS.get(role)
            )
        delta = index * 25 + 10
        for j, event in enumerate(events):
            event.update(
                event_id=f"unit-only-{role}-{j}",
                start_seconds=event["start_seconds"] + delta,
                end_seconds=event["end_seconds"] + delta,
            )
        inner["expected_role"] = inner["record"]["role"] = role
        inner["expected_argv"] = inner["record"]["argv"] = argv
        inner["log"] = checker.canonical(payloads.get(role, {"public": role}))
        inner["record"]["log_sha256"] = checker.digest(inner["log"])
        next(item for item in completion["resource_components"] if item["kind"] == "wait4")[
            "record"
        ]["launched_UTC_seconds"] = events[0]["start_seconds"] + 0.01
        if role == "final-filing":
            start = trusted["shared-closeout"][-1]["end_seconds"]
            for item in (pending, completion):
                item.update(
                    result_start_UTC_seconds=start,
                    result_deadlines_UTC={
                        actor: datetime.fromtimestamp(start + seconds, UTC)
                        .isoformat(timespec="milliseconds")
                        .replace("+00:00", "Z")
                        for actor, seconds in (("exporter", 7200), ("independent", 3600))
                    },
                )
        seal_native_facts(checker, pending, completion, inner, profiles, events)
        wire = {
            "pending": pending,
            "completion": completion,
            "inner_evidence": inner,
            "native_profiles": profiles,
        }
        trusted[role] = events
        roles[role] = wire
    last = trusted["final-filing"][-1]
    lease = {
        "scope": "COOPERATIVE_REGISTERED_TOPOLAB_ONLY",
        "execution_identity": checker.EXECUTION_IDENTITY,
        "root": str(content),
        "version_id": closed["version_id"],
        "registered_readers": [*order, "final-filing"],
        "acquired_UTC_seconds": 1000.0,
        "acquired_monotonic": 100.0,
        "state": "RELEASED",
        "last_reader_return": {
            "event_id": last["event_id"],
            "sha256": checker.digest(checker.canonical(last)),
            "end_seconds": last["end_seconds"],
        },
        "released_UTC_seconds": trusted["lease-release"][-1]["end_seconds"],
    }
    release = roles.pop("lease-release")
    release["inner_evidence"]["log"] = checker.canonical(lease)
    release["inner_evidence"]["record"]["log_sha256"] = checker.digest(
        release["inner_evidence"]["log"]
    )
    seal_native_facts(
        checker,
        release["pending"],
        release["completion"],
        release["inner_evidence"],
        release["native_profiles"],
        trusted["lease-release"],
    )
    filing = roles.pop("final-filing")
    bundle = {
        "schema": "topolab.v2.m2-content-verified-public-bundle.v1",
        "execution_identity": checker.EXECUTION_IDENTITY,
        "scope": checker.PUBLIC_SCOPE,
        "plan": plan,
        "plan_sha256": plan_sha,
        "contract_sha256": contract_sha,
        "root": str(content),
        "registry": registry,
        "manifest": closed["manifest"],
        "version_id": closed["version_id"],
        "local_identity_rows": closed["local_identity_rows"],
        "root_identity": closed["root_identity"],
        "role_views": closed["manifest"]["role_views"],
        "roles": roles,
        "lease": lease,
        "backup": backup,
        "filing": filing,
        "shared_packet_sha256": shared_sha,
        "lease_release_evidence": release,
    }
    return checker, bundle, trusted


def test_full_public_certificate_requires_real_proof_chain_and_stays_public(tmp_path, monkeypatch):
    checker, bundle, trusted = public_certificate_facts(tmp_path, monkeypatch)
    checked = checker.audit_public_certificate(bundle, trusted_tool_events=trusted)
    assert isinstance(checked, checker.CheckedPublicInput)
    import pytest

    with pytest.raises(ValueError, match="lease"):
        checked.binding_for("scientific-producer")


def test_reader_lease_is_exclusive_and_replay_can_only_ack_actual_native_return(
    tmp_path, monkeypatch
):
    import pickle

    import pytest

    checker, bundle, trusted = public_certificate_facts(tmp_path, monkeypatch)
    certificate = checker.audit_public_certificate(bundle, trusted_tool_events=trusted)
    lease = certificate.acquire_reader("reference-compatibility")
    binding = certificate.binding_for("reference-compatibility", reader_lease=lease)
    assert binding["scope"] == "PUBLIC_SOFTWARE_FIXTURE_ONLY"
    assert binding["version_id"] == bundle["version_id"]
    with pytest.raises(TypeError):
        binding["root"] = "/unverified"
    with pytest.raises(TypeError):
        pickle.dumps(certificate)
    with pytest.raises(ValueError, match="held"):
        certificate.acquire_reader("reference-compatibility")
    receipt = lease.pending_return()
    assert receipt["status"] == "PENDING_ACTUAL_OUTER_RETURN"
    with pytest.raises(ValueError, match="lease"):
        certificate.binding_for("reference-compatibility", reader_lease=lease)
    replayed = checker.audit_public_certificate(bundle, trusted_tool_events=trusted)
    with pytest.raises(ValueError, match="actual"):
        replayed.acknowledge_returned_reader(receipt, {"status": "PASS"})
    pending, completion, events, inner, profiles = public_role_facts()
    native_facts_for_host(checker, completion, inner, profiles)
    for item in (pending, completion):
        item.update(
            role="public-consumer", frozen_FULL_seconds=None, plan_sha256=bundle["plan_sha256"]
        )
    inner["expected_role"] = inner["record"]["role"] = "public-consumer"
    inner["expected_argv"] = inner["record"]["argv"] = list(sys.orig_argv)
    inner["log"] = checker.canonical(receipt)
    inner["record"]["log_sha256"] = checker.digest(inner["log"])
    offset = receipt["acquired_UTC_seconds"] - 1001
    for event in events:
        event["start_seconds"] += offset
        event["end_seconds"] += offset
    completion["pending_sha256"] = checker.digest(checker.canonical(pending))
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    observed = {
        "wire": {
            "pending": pending,
            "completion": completion,
            "inner_evidence": inner,
            "native_profiles": profiles,
        },
        "raw_tool_events": events,
    }
    result = replayed.acknowledge_returned_reader(receipt, observed)
    assert result["status"] == "PUBLIC_READER_RETURN_ACKNOWLEDGED"
    assert result["consumer_actual_exit_observed"] is True
    assert result["reader_cost"]["frozen_FULL_seconds"] is None
    assert result["reader_cost"]["known_cost_lower_bound_seconds"] == 28
    with pytest.raises(ValueError, match="lease"):
        certificate.binding_for("reference-compatibility", reader_lease=lease)


def test_certificate_rejects_self_only_source_freeze_before_role_or_content_access(tmp_path):
    import pytest

    checker = load()
    plan = {
        "execution_identity": checker.EXECUTION_IDENTITY,
        "scope": checker.PUBLIC_SCOPE,
        "root": str(tmp_path),
        "formal_authority": False,
        "role_order": checker.ROLE_ORDER,
        "roles": {role: {} for role in checker.ROLE_ORDER},
        "metadata_actions": {
            name: {} for name in ("final-filing", "lease-release", "public-consumer", "reader-ack")
        },
        "source_tree": {
            "scripts/p17_m2_content_verified_independent.py": checker.digest(
                Path(checker.__file__).read_bytes()
            )
        },
        "contract_sha256": "a" * 64,
    }
    bundle = {
        "schema": "topolab.v2.m2-content-verified-public-bundle.v1",
        "execution_identity": checker.EXECUTION_IDENTITY,
        "scope": checker.PUBLIC_SCOPE,
        "root": str(tmp_path / "content"),
        "plan": plan,
        "plan_sha256": checker.digest(checker.canonical(plan)),
        "contract_sha256": "a" * 64,
        "roles": {role: {} for role in checker.ROLE_ORDER},
    }
    with pytest.raises(ValueError, match="closure"):
        checker.audit_public_certificate(
            bundle,
            trusted_tool_events={
                name: [] for name in [*checker.ROLE_ORDER, "final-filing", "lease-release"]
            },
        )


def test_first_dispatch_requires_the_full_4200_seconds_remaining():
    checker = load()
    pending, completion, events, inner, profiles = public_role_facts()
    for item in (pending, completion):
        item["role"] = "independent-public-check"
    for event in events:
        event["start_seconds"] += 301
        event["end_seconds"] += 301
    completion["pending_sha256"] = checker.digest(checker.canonical(pending))
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    result = checker.audit_role(
        pending,
        completion,
        raw_tool_events=events,
        expected_role="independent-public-check",
        expected_plan_sha256="a" * 64,
        inner_evidence=inner,
        native_profiles=profiles,
    )
    assert result["status"] == "STOP_NO_RETRY"
    assert "4200" in result["reason"]
    assert result["whole_wall_seconds"] == 17.25
    assert result["known_cost_lower_bound_seconds"] == 300


def test_outer_lifetime_cannot_be_shorter_than_valid_observed_inner_lifetime():
    checker = load()
    pending, completion, events, inner, profiles = public_role_facts()
    inner["record"]["observed_outer_wall_seconds"] = 290.0
    inner["record"]["timeout_seconds"] = 300
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    result = checker.audit_role(
        pending,
        completion,
        raw_tool_events=events,
        expected_role="exporter-r0",
        expected_plan_sha256="a" * 64,
        inner_evidence=inner,
        native_profiles=profiles,
    )
    assert result["status"] == "STOP_NO_RETRY"
    assert "inner" in result["reason"]
    assert result["whole_wall_seconds"] == 17.25
    assert result["inner_minimum_charge_seconds"] == 300
    assert result["known_cost_lower_bound_seconds"] == 300


def test_missing_outer_RSS_does_not_erase_valid_larger_inner_charge():
    checker = load()
    pending, completion, events, inner, profiles = public_role_facts()
    inner["record"]["observed_outer_wall_seconds"] = 390.0
    inner["record"]["timeout_seconds"] = 400
    completion["resource_components"].pop()
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    result = audit_public_role(checker, (pending, completion, events, inner, profiles))
    assert result["status"] == "STOP_NO_RETRY"
    assert result["whole_wall_seconds"] == 17.25
    assert result["RSS_envelope_bytes"] is None
    assert result["inner_minimum_charge_seconds"] == 400
    assert result["known_cost_lower_bound_seconds"] == 400


@pytest.mark.parametrize(
    "damage",
    ["OOM", "missing_rss", "cleanup", "unknown_exit", "old_identity", "NaN", "late_window"],
)
def test_failed_role_keeps_available_wall_FULL_cost_and_never_admits(damage):
    checker = load()
    facts = public_role_facts()
    pending, completion, events, inner, profiles = facts
    if damage == "OOM":
        completion["resource_components"][1]["record"]["native"]["rss_bytes"] = 4294967296
    elif damage == "missing_rss":
        completion["resource_components"].pop()
    elif damage == "cleanup":
        completion["cleanup"]["group_gone"] = None
    elif damage == "unknown_exit":
        events[-1]["exit_code"] = None
    elif damage == "old_identity":
        pending["execution_identity"] = "topolab.v2.p17-m2-source-stable-export.v1"
    elif damage == "NaN":
        events[-1]["end_seconds"] = float("nan")
    else:
        events[-1]["start_seconds"] += 4500
        events[-1]["end_seconds"] += 4500
    completion.update(resource_pass=True, status="PENDING_EXTERNAL_EXIT")
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    result = audit_public_role(checker, facts)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["full_role_evidence_accepted"] is False
    assert result["source_successor_admitted"] is False
    assert result["B_C_admission"] is False
    assert result["frozen_FULL_seconds"] == 300
    if damage == "NaN":
        assert result["whole_wall_seconds"] is None
        assert result["known_cost_lower_bound_seconds"] == 300
    elif damage == "late_window":
        assert result["whole_wall_seconds"] == 4517.25
        assert result["known_cost_lower_bound_seconds"] == 4528
    else:
        assert result["whole_wall_seconds"] == 17.25
        assert result["known_cost_lower_bound_seconds"] == 300
    if damage == "OOM":
        assert result["RSS_envelope_bytes"] > 4294967296


@pytest.mark.parametrize("exit_code", [None, 1])
def test_metadata_unknown_or_failed_exit_keeps_real_cost_without_inventing_FULL(exit_code):
    checker = load()
    pending, completion, events, inner, profiles = public_role_facts()
    for record in (pending, completion):
        record.update(role="public-consumer", frozen_FULL_seconds=None)
    inner["expected_role"] = inner["record"]["role"] = "public-consumer"
    events[-1]["exit_code"] = exit_code
    completion["pending_sha256"] = checker.digest(checker.canonical(pending))
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    result = checker.audit_metadata(
        {
            "pending": pending,
            "completion": completion,
            "inner_evidence": inner,
            "native_profiles": profiles,
        },
        raw_tool_events=events,
        expected_role="public-consumer",
        plan_sha256="a" * 64,
        expected_argv=inner["expected_argv"],
    )
    assert result["status"] == "STOP_NO_RETRY"
    assert result["metadata_evidence_accepted"] is False
    assert result["frozen_FULL_seconds"] is None
    assert result["whole_wall_seconds"] == 17.25
    assert result["known_cost_lower_bound_seconds"] == 28


def test_role_receipt_binds_entire_pending_and_completion_not_only_a_PASS_summary():
    checker = load()
    facts = public_role_facts()
    first = audit_public_role(checker, facts)
    assert first["pending_sha256"] == facts[1]["pending_sha256"]
    facts[1]["retained_secondary_context"] = {"source": "new public context", "error": "UNKNOWN"}
    seal_native_facts(checker, facts[0], facts[1], facts[3], facts[4], facts[2])
    second = audit_public_role(checker, facts)
    assert first["completion_sha256"] != second["completion_sha256"]
    assert second["plan_sha256"] == "a" * 64
    assert second["status"] == "PASS_CONTENT_VERIFIED_PUBLIC_ROLE"


def test_independent_parse_failure_retains_full_single_read_context(tmp_path):
    checker = load()
    source = tmp_path / "source"
    source.mkdir(mode=0o700)
    raw = b"{"
    (source / "bad.json").write_bytes(raw)
    (source / "bad.json").chmod(0o600)
    contract = {
        "R0": {
            "embedded_B3_data_index_sha256": "a" * 64,
            "literal_bootstrap_files": [
                {
                    "relative_path": "bad.json",
                    "max_bytes": 1024,
                    "expected_sha256": checker.digest(raw),
                }
            ],
        }
    }
    with pytest.raises(ValueError) as observed:
        checker.independent_r0(
            source, contract, {}, [], {"B3_DATA_HASH": "a" * 64, "CATALOG_HASH": "b" * 64}
        )
    failure = observed.value.independent_read_failure
    assert failure["stage"] == "independent_r0"
    assert failure["readers"]["source"]["attempts"] == 1
    facts = failure["readers"]["source"]["source_facts"]["bad.json"]
    assert facts["stage"] == "json_parse"
    assert facts["returned_bytes"] == 1
    assert all(facts[key] is not None for key in ("declared", "before", "after", "closing"))
    assert failure["missing_evidence_cost"] == "UNKNOWN_NOT_ZERO"


@pytest.fixture(scope="module")
def certificate_case(tmp_path_factory):
    patcher = pytest.MonkeyPatch()
    try:
        yield public_certificate_facts(
            tmp_path_factory.mktemp("content-verified-certificate"), patcher
        )
    finally:
        patcher.undo()


def test_release_final_snapshot_must_match_actual_native_log(certificate_case):
    checker, original, trusted = certificate_case
    bundle = deepcopy(original)
    bundle["lease"]["released_UTC_seconds"] -= 0.01
    with pytest.raises(ValueError, match="release.*log"):
        checker.audit_public_certificate(bundle, trusted_tool_events=trusted)


def reseal_certificate_transport(checker, bundle, trusted):
    """Keep unit transport honest while mutating a domain claim under test."""
    shared = bundle["roles"]["shared-closeout"]
    shared["inner_evidence"]["log"] = checker.canonical(bundle["backup"])
    for role, wire in bundle["roles"].items():
        wire["inner_evidence"]["record"]["log_sha256"] = checker.digest(
            wire["inner_evidence"]["log"]
        )
        seal_native_facts(
            checker,
            wire["pending"],
            wire["completion"],
            wire["inner_evidence"],
            wire["native_profiles"],
            trusted[role],
        )
    results = {
        role: checker.audit_role(
            wire["pending"],
            wire["completion"],
            raw_tool_events=trusted[role],
            expected_role=role,
            expected_plan_sha256=bundle["plan_sha256"],
            inner_evidence=wire["inner_evidence"],
            native_profiles=wire["native_profiles"],
        )
        for role, wire in bundle["roles"].items()
    }
    bundle["shared_packet_sha256"] = checker.digest(checker.canonical(results))
    filing = bundle["filing"]
    proof = checker.base.parse(filing["inner_evidence"]["log"], canonical_required=True)
    proof["shared_packet_sha256"] = bundle["shared_packet_sha256"]
    proof["billing_charge"]["shared_reservation_sha256"] = checker.digest(
        checker.canonical(bundle["backup"]["billing_ledger"]["reservation"])
    )
    filing["inner_evidence"]["log"] = checker.canonical(proof)
    filing["inner_evidence"]["record"]["log_sha256"] = checker.digest(
        filing["inner_evidence"]["log"]
    )
    seal_native_facts(
        checker,
        filing["pending"],
        filing["completion"],
        filing["inner_evidence"],
        filing["native_profiles"],
        trusted["final-filing"],
    )
    last = trusted["final-filing"][-1]
    bundle["lease"]["last_reader_return"] = {
        "event_id": last["event_id"],
        "sha256": checker.digest(checker.canonical(last)),
        "end_seconds": last["end_seconds"],
    }
    release = bundle["lease_release_evidence"]
    release["inner_evidence"]["log"] = checker.canonical(bundle["lease"])
    release["inner_evidence"]["record"]["log_sha256"] = checker.digest(
        release["inner_evidence"]["log"]
    )
    seal_native_facts(
        checker,
        release["pending"],
        release["completion"],
        release["inner_evidence"],
        release["native_profiles"],
        trusted["lease-release"],
    )


def test_shared_prebooking_cannot_be_zeroed_even_when_all_transport_hashes_match(certificate_case):
    checker, original, original_trusted = certificate_case
    bundle, trusted = deepcopy(original), deepcopy(original_trusted)
    ledger = bundle["backup"]["billing_ledger"]
    ledger["reservation"]["shared_reserved_FULL_seconds"] = 0
    reservation_sha = checker.digest(checker.canonical(ledger["reservation"]))
    for row in ledger["dispatch_charges"]:
        row["shared_reservation_sha256"] = reservation_sha
    reseal_certificate_transport(checker, bundle, trusted)
    with pytest.raises(ValueError, match="billing|reservation"):
        checker.audit_public_certificate(bundle, trusted_tool_events=trusted)


@pytest.mark.parametrize("damage", ["role_window", "coordination"])
def test_six_roles_share_one_plan_window_and_one240s_coordination_budget(certificate_case, damage):
    from datetime import UTC, datetime

    checker, original, original_trusted = certificate_case
    bundle, trusted = deepcopy(original), deepcopy(original_trusted)
    if damage == "role_window":
        for item in (
            bundle["roles"]["exporter-r0"]["pending"],
            bundle["roles"]["exporter-r0"]["completion"],
        ):
            item["actor_activation_UTC_seconds"] = 1001.0
            item["actor_deadlines_UTC"] = {
                "exporter": "1970-01-01T01:31:41.000Z",
                "independent": "1970-01-01T01:31:41.000Z",
            }
    else:
        delta = 202
        for role, events in trusted.items():
            if role == "independent-public-check":
                continue
            for event in events:
                event["start_seconds"] += delta
                event["end_seconds"] += delta
            wire = bundle["roles"].get(
                role,
                bundle["filing"] if role == "final-filing" else bundle["lease_release_evidence"],
            )
            next(
                item
                for item in wire["completion"]["resource_components"]
                if item["kind"] == "wait4"
            )["record"]["launched_UTC_seconds"] += delta
        for row in bundle["backup"]["billing_ledger"]["dispatch_charges"][1:]:
            row["charged_UTC_seconds"] += delta
        filing = bundle["filing"]
        proof = checker.base.parse(filing["inner_evidence"]["log"], canonical_required=True)
        proof["billing_charge"]["charged_UTC_seconds"] += delta
        filing["inner_evidence"]["log"] = checker.canonical(proof)
        for item in (filing["pending"], filing["completion"]):
            start = item["result_start_UTC_seconds"] + delta
            item["result_start_UTC_seconds"] = start
            item["result_deadlines_UTC"] = {
                actor: datetime.fromtimestamp(start + seconds, UTC)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
                for actor, seconds in (("exporter", 7200), ("independent", 3600))
            }
        bundle["lease"]["released_UTC_seconds"] += delta
    reseal_certificate_transport(checker, bundle, trusted)
    with pytest.raises(ValueError, match="window|coordination"):
        checker.audit_public_certificate(bundle, trusted_tool_events=trusted)


def test_R1_rejects_replaced_root_even_when_existing_member_inodes_are_moved_unchanged(tmp_path):
    checker = load()
    source, content = tmp_path / "source", tmp_path / "content"
    source.mkdir(mode=0o700)
    content.mkdir(mode=0o700)
    member = content / "same-member.txt"
    member.write_bytes(b"new public file")
    member.chmod(0o600)
    member_ino = member.stat().st_ino
    declared = {
        key: getattr(content.stat(), key) for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")
    }
    old = tmp_path / "old-public-content"
    content.rename(old)
    content.mkdir(mode=0o700)
    (old / "same-member.txt").rename(member)
    assert member.stat().st_ino == member_ino
    with pytest.raises(ValueError, match="root identity") as observed:
        checker.independent_r1(
            source,
            content,
            {},
            [],
            {"root_identity": declared},
            "f" * 64,
            {"B3_DATA_HASH": "a" * 64, "CATALOG_HASH": "b" * 64},
        )
    assert observed.value.independent_read_failure["reader_scopes_not_started"] == [
        "exports",
        "local_content",
        "source",
    ]


def test_failed_prefix_backup_checks_explicit_closed_files_and_never_admits(tmp_path):
    checker = load()
    root = tmp_path / "new-public-failed-prefix"
    backup = root / "backup-prefix"
    backup.mkdir(parents=True, mode=0o700)
    root.chmod(0o700)
    rows = []
    reader = checker.base.OnceReader(root, 2, 1024, source_identity_checks=True)
    for name, raw in [("plan.json", b'{"public":true}\n'), ("STOP.json", b'{"STOP":true}\n')]:
        for target in (root / name, backup / name):
            target.write_bytes(raw)
            target.chmod(0o600)
        reader.read(name, 1024)
        rows.append(
            {
                "path": name,
                "byte_size": len(raw),
                "sha256": checker.digest(raw),
                "identity": reader.observations[-1],
            }
        )
    rows.sort(key=lambda row: row["path"])
    proof = checker.independent_prefix_backup(root, backup, rows)
    assert proof["status"] == "PUBLIC_FAILED_PREFIX_BACKUP_CHECKED"
    assert proof["input_version_accepted"] is False
    assert proof["formal_or_scientific_admission"] is False
    assert proof["member_count"] == 2
    assert proof["paths"] == ["STOP.json", "plan.json"]
    assert len(proof["source_identity_rows"]) == len(proof["backup_identity_rows"]) == 2
    with pytest.raises(ValueError, match="actual|identity|scope"):
        checker.audit_public_certificate(proof, trusted_tool_events={})
    (backup / "unlisted.txt").write_bytes(b"public extra")
    (backup / "unlisted.txt").chmod(0o600)
    with pytest.raises(ValueError, match="inventory"):
        checker.independent_prefix_backup(root, backup, rows)


def test_filing_FULL180_must_be_charged_before_its_actual_launch(certificate_case):
    checker, original, original_trusted = certificate_case
    bundle, trusted = deepcopy(original), deepcopy(original_trusted)
    filing = bundle["filing"]
    proof = checker.base.parse(filing["inner_evidence"]["log"], canonical_required=True)
    proof["billing_charge"]["charged_UTC_seconds"] = (
        trusted["final-filing"][0]["start_seconds"] + 0.1
    )
    filing["inner_evidence"]["log"] = checker.canonical(proof)
    reseal_certificate_transport(checker, bundle, trusted)
    with pytest.raises(ValueError, match="filing.*predispatch|filing.*charge"):
        checker.audit_public_certificate(bundle, trusted_tool_events=trusted)


@pytest.mark.parametrize(
    "damage",
    ["none", "RSS_UNKNOWN", "late", "forged_return", "cleanup_UNKNOWN", "native_exit_UNKNOWN"],
)
def test_closed_failed_attempt_allows_only_proven_returned_groups_for_shared_backup(damage):
    checker = load()
    pending, completion, events, inner, profiles = public_role_facts(failed=True)
    if damage == "RSS_UNKNOWN":
        completion["resource_components"].pop()
        inner["record"]["native"]["rss_bytes"] = None
    elif damage == "late":
        for event in events:
            event["start_seconds"] += 4600
            event["end_seconds"] += 4600
    elif damage == "cleanup_UNKNOWN":
        inner["record"]["helpers"][0]["cleanup"]["group_gone"] = None
    elif damage == "native_exit_UNKNOWN":
        inner["record"]["timer_native_exit"]["exit_code"] = None
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    if damage == "forged_return":
        completion["cleanup"]["initial_group_gone"] = True
    proof = checker.check_closed_attempt(
        {
            "pending": pending,
            "completion": completion,
            "inner_evidence": inner,
            "native_profiles": profiles,
        },
        raw_tool_events=events,
        expected_role="exporter-r0",
        expected_plan_sha256="a" * 64,
        expected_argv=inner["expected_argv"],
    )
    assert proof["closed_attempt_verified"] is (damage in {"none", "RSS_UNKNOWN", "late"})
    assert proof["full_role_evidence_accepted"] is False
    assert proof["input_version_accepted"] is False
    assert proof["known_cost_lower_bound_seconds"] >= 300
    assert proof["whole_wall_seconds"] == 17.25


@pytest.mark.parametrize("action", ["metadata", "failed-prefix"])
def test_missing_native_packet_still_retains_the_valid_actual_tool_span(action):
    checker = load()
    pending, completion, events, inner, profiles = public_role_facts()
    if action == "metadata":
        proof = checker.audit_metadata(
            {},
            raw_tool_events=events,
            plan_sha256="a" * 64,
            expected_role="public-consumer",
            expected_argv=inner["expected_argv"],
        )
        assert proof["known_cost_lower_bound_seconds"] == 28
    else:
        proof = checker.check_closed_attempt(
            {},
            raw_tool_events=events,
            expected_role="exporter-r0",
            expected_plan_sha256="a" * 64,
            expected_argv=inner["expected_argv"],
        )
        assert proof["known_cost_lower_bound_seconds"] == 300
    assert proof["status"] == "STOP_NO_RETRY"
    assert proof["whole_wall_seconds"] == 17.25


def test_certificate_contract_hash_must_be_the_actual_frozen_protocol(tmp_path, monkeypatch):
    checker, bundle, trusted = public_certificate_facts(
        tmp_path, monkeypatch, contract_sha="f" * 64
    )
    with pytest.raises(ValueError, match="contract.*frozen|protocol"):
        checker.audit_public_certificate(bundle, trusted_tool_events=trusted)


@pytest.mark.parametrize(
    "role", ["shared-closeout", "final-filing", "lease-release", "public-consumer", "reader-ack"]
)
def test_closed_predicate_can_clear_any_registered_failed_action_without_granting_PASS(role):
    from datetime import UTC, datetime

    checker = load()
    pending, completion, events, inner, profiles = public_role_facts(failed=True)
    for item in (pending, completion):
        item.update(role=role, frozen_FULL_seconds=checker.FULL_SECONDS.get(role))
        if role == "final-filing":
            item.update(
                result_start_UTC_seconds=900.0,
                result_deadlines_UTC={
                    actor: datetime.fromtimestamp(900 + seconds, UTC)
                    .isoformat(timespec="milliseconds")
                    .replace("+00:00", "Z")
                    for actor, seconds in (("exporter", 7200), ("independent", 3600))
                },
            )
    inner["expected_role"] = inner["record"]["role"] = role
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    proof = checker.check_closed_attempt(
        {
            "pending": pending,
            "completion": completion,
            "inner_evidence": inner,
            "native_profiles": profiles,
        },
        raw_tool_events=events,
        expected_role=role,
        expected_plan_sha256="a" * 64,
        expected_argv=inner["expected_argv"],
    )
    assert proof["closed_attempt_verified"] is True
    assert proof["full_role_evidence_accepted"] is False
    assert proof["input_version_accepted"] is False
    if role in {"lease-release", "public-consumer", "reader-ack"}:
        assert proof["frozen_FULL_seconds"] is None
        assert proof["known_cost_lower_bound_seconds"] == 28
    else:
        assert proof["known_cost_lower_bound_seconds"] == checker.FULL_SECONDS[role]


def test_outer_watchdog_unknown_group_cannot_clear_a_closed_inner_attempt():
    checker = load()
    pending, completion, events, inner, profiles = public_role_facts(failed=True)
    watchdog = deepcopy(completion["cleanup"])
    watchdog["group_gone"] = None
    next(item for item in completion["resource_components"] if item["kind"] == "wait4")["record"][
        "watchdog_cleanup"
    ] = watchdog
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    proof = checker.check_closed_attempt(
        {
            "pending": pending,
            "completion": completion,
            "inner_evidence": inner,
            "native_profiles": profiles,
        },
        raw_tool_events=events,
        expected_role="exporter-r0",
        expected_plan_sha256="a" * 64,
        expected_argv=inner["expected_argv"],
    )
    assert proof["closed_attempt_verified"] is False
    assert proof["full_role_evidence_accepted"] is False
    assert proof["whole_wall_seconds"] == 17.25
    assert proof["known_cost_lower_bound_seconds"] == 300


def outer_watchdog_facts():
    checker = load()
    pending, completion, events, inner, profiles = public_role_facts(failed=True)
    outer = next(item for item in completion["resource_components"] if item["kind"] == "wait4")
    pid = outer["pid"]
    watchdog = deepcopy(completion["cleanup"])
    watchdog.update(
        helper=deepcopy(inner["record"]["helpers"][0]),
        observed=[
            {"pid": pid, "parent": 1, "pgid": pid, "rss_bytes": 10},
            {"pid": 200, "parent": pid, "pgid": 200, "rss_bytes": 10},
            {"pid": 201, "parent": 200, "pgid": 200, "rss_bytes": 10},
        ],
        descendant_groups=[
            {
                "pgid": 200,
                "observed_pids": [200, 201],
                "signals": ["SIGTERM"],
                "group_gone": True,
                "observations": [
                    {"elapsed_seconds": 0.01, "group_gone": False},
                    {"elapsed_seconds": 0.02, "group_gone": True},
                ],
            }
        ],
        secondary_failures=[
            {
                "stage": "inner started",
                "type": "FileNotFoundError",
                "reason": "new started record missing",
            }
        ],
    )
    outer["record"]["watchdog_cleanup"] = watchdog
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    return (pending, completion, events, inner, profiles), watchdog


def test_complete_watchdog_cleanup_closes_failure_without_claiming_complete_RSS():
    checker = load()
    (pending, completion, events, inner, profiles), _ = outer_watchdog_facts()
    proof = checker.check_closed_attempt(
        {
            "pending": pending,
            "completion": completion,
            "inner_evidence": inner,
            "native_profiles": profiles,
        },
        raw_tool_events=events,
        expected_role="exporter-r0",
        expected_plan_sha256="a" * 64,
        expected_argv=inner["expected_argv"],
    )
    assert proof["closed_attempt_verified"] is True
    assert proof["full_role_evidence_accepted"] is False
    resources = proof["resource_evidence"]
    assert resources["status"] == "STOP_NO_RETRY"
    assert resources["RSS_envelope_bytes"] is None
    assert resources["known_RSS_sum_bytes"] == 980
    assert resources["inner_minimum_charge_seconds"] == 11.2
    assert proof["whole_wall_seconds"] == 17.25
    assert proof["known_cost_lower_bound_seconds"] == 300


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-helper",
        "unknown-helper-cleanup",
        "missing-groups",
        "missing-descendant",
        "unknown-descendant",
        "unrelated-observed",
        "unknown-observation",
    ],
)
def test_watchdog_must_close_every_observed_group_and_sampler(mutation):
    checker = load()
    (pending, completion, events, inner, profiles), watchdog = outer_watchdog_facts()
    if mutation == "missing-helper":
        watchdog["helper"] = None
    elif mutation == "unknown-helper-cleanup":
        watchdog["helper"]["cleanup"]["group_gone"] = None
    elif mutation == "missing-groups":
        watchdog["descendant_groups"] = None
    elif mutation == "missing-descendant":
        watchdog["descendant_groups"] = []
    elif mutation == "unknown-descendant":
        watchdog["descendant_groups"][0]["group_gone"] = None
    elif mutation == "unrelated-observed":
        watchdog["observed"].append({"pid": 999, "parent": 1, "pgid": 999, "rss_bytes": 1})
    else:
        watchdog["descendant_groups"][0]["observations"][0]["group_gone"] = None
    seal_native_facts(checker, pending, completion, inner, profiles, events)
    proof = checker.check_closed_attempt(
        {
            "pending": pending,
            "completion": completion,
            "inner_evidence": inner,
            "native_profiles": profiles,
        },
        raw_tool_events=events,
        expected_role="exporter-r0",
        expected_plan_sha256="a" * 64,
        expected_argv=inner["expected_argv"],
    )
    assert proof["closed_attempt_verified"] is False
    assert proof["full_role_evidence_accepted"] is False
    assert proof["known_cost_lower_bound_seconds"] == 300
