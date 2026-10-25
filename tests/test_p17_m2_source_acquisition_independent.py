"""Independent raw-evidence and source-binding behavior; NEW public data only."""

import importlib.util
from pathlib import Path

IDENTITY = "topolab.v2.p17-m2-content-verified-source-acquisition.v1"


def public_role_facts():
    path = Path(__file__).with_name("test_p17_m2_content_verified_independent.py")
    spec = importlib.util.spec_from_file_location("acquisition_independent_public_facts", path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    checker = fixture.load()
    pending, completion, events, inner, profiles = fixture.public_role_facts()
    for row in (pending, completion):
        row["execution_identity"] = IDENTITY
    fixture.seal_native_facts(checker, pending, completion, inner, profiles, events)
    return checker, pending, completion, events, inner, profiles


def test_new_identity_uses_same_raw_native_checks_without_changing_public_default():
    checker, pending, completion, events, inner, profiles = public_role_facts()
    new = checker.audit_role(
        pending,
        completion,
        raw_tool_events=events,
        expected_role="exporter-r0",
        expected_plan_sha256="a" * 64,
        inner_evidence=inner,
        native_profiles=profiles,
        expected_identity=IDENTITY,
    )
    assert new["full_role_evidence_accepted"] is True
    assert new["execution_identity"] == IDENTITY
    public = checker.audit_role(
        pending,
        completion,
        raw_tool_events=events,
        expected_role="exporter-r0",
        expected_plan_sha256="a" * 64,
        inner_evidence=inner,
        native_profiles=profiles,
    )
    assert public["full_role_evidence_accepted"] is False
    assert public["known_cost_lower_bound_seconds"] == 300


def load_acquisition():
    path = Path(__file__).parents[1] / "scripts/p17_m2_source_acquisition_independent.py"
    spec = importlib.util.spec_from_file_location("acquisition_independent_subject", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_or_target_permission_flip_is_denied_before_any_path_io(monkeypatch):
    checker = load_acquisition()
    plan = {
        "scope": "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY",
        "formal_authority": False,
        "binding": {
            "formal_authority": False,
            "old_original_access": False,
            "target_access": True,
            "B_C": False,
        },
    }

    def forbidden_open(*args, **kwargs):
        raise AssertionError("permission flip reached filesystem before refusal")

    monkeypatch.setattr("os.open", forbidden_open)
    try:
        checker.validate_binding(plan)
    except ValueError as error:
        assert "author" in str(error) or "permission" in str(error)
    else:
        raise AssertionError("public preparation granted target authority")


def binding_plan():
    import json
    from copy import deepcopy
    from datetime import UTC, datetime

    checker = load_acquisition()
    root = "/private/tmp/topolab-public-formal-binding-literal-unit"
    content = json.loads((checker.REPO / checker.CONTENT_CONTRACT).read_bytes())
    content["R0"]["embedded_B3_data_index_sha256"] = "1" * 64
    for row in content["R0"]["literal_bootstrap_files"]:
        row["expected_sha256"] = "2" * 64
    protocol = checker.digest((checker.REPO / checker.PREPARATION_PROTOCOL).read_bytes())
    roles = [
        "independent-public-check",
        "exporter-r0",
        "independent-r0",
        "exporter-r1",
        "independent-r1",
        "shared-closeout",
    ]
    deadline = (
        datetime.fromtimestamp(5500, UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    )
    plan = {
        "schema": "topolab.v2.m2-source-acquisition-plan.v1",
        "execution_identity": IDENTITY,
        "scope": checker.REHEARSAL_SCOPE,
        "formal_authority": False,
        "root": root,
        "source_root": root + "/public-source",
        "content_root": root + "/content",
        "backup_root": root + "/backup-content",
        "proposal_sha256": checker.PROPOSAL_SHA256,
        "preparation_contract_sha256": protocol,
        "contract_sha256": protocol,
        "content_contract": content,
        "public_source_identity": {"B3_DATA_HASH": "1" * 64, "CATALOG_HASH": "3" * 64},
        "source_tree": {
            checker.PROPOSAL: checker.PROPOSAL_SHA256,
            checker.PREPARATION_PROTOCOL: protocol,
            checker.CONTENT_CONTRACT: checker.CONTENT_CONTRACT_SHA256,
        },
        "role_order": roles,
        "roles": {r: {"argv": ["frozen-runtime", r]} for r in roles},
        "metadata_actions": {
            r: {"argv": ["frozen-runtime", r]}
            for r in ("final-filing", "lease-release", "public-consumer", "reader-ack")
        },
        "actor_activation_UTC_seconds": 1000.0,
        "actor_window_seconds": 4500,
        "actor_deadlines_UTC": {"exporter": deadline, "independent": deadline},
        "binding": {
            "proposal_sha256": checker.PROPOSAL_SHA256,
            "content_contract_sha256": checker.digest(checker.canonical(content)),
            "preparation_protocol_sha256": protocol,
            "intended_formal_scope": checker.FORMAL_SCOPE,
            "formal_authority": False,
            "old_original_access": False,
            "target_access": False,
            "B_C": False,
        },
    }
    return checker, deepcopy(plan)


def test_rehearsal_binding_requires_exact_role_order_without_probing_projected_targets():
    import pytest

    checker, plan = binding_plan()
    assert checker.validate_binding(plan)["formal_authority"] is False
    plan["role_order"][1], plan["role_order"][2] = plan["role_order"][2], plan["role_order"][1]
    with pytest.raises(ValueError, match="role|order"):
        checker.validate_binding(plan)


def test_binding_rejects_semantic_contract_drift_even_when_its_digest_is_resealed():
    import pytest

    checker, plan = binding_plan()
    assert checker.validate_binding(plan)["formal_authority"] is False
    plan["content_contract"]["checkpoints"]["fixed_rows"][3]["selected_epoch"] = 124
    plan["binding"]["content_contract_sha256"] = checker.digest(
        checker.canonical(plan["content_contract"])
    )
    with pytest.raises(ValueError, match="content|fixed|projection"):
        checker.validate_binding(plan)


def new_public_case(tmp_path):
    checker, plan = binding_plan()
    root = tmp_path / "topolab-public-formal-binding-independent"
    root.mkdir(mode=0o700)
    contract, source_identity = checker.helper(
        "acquisition_independent_fixture", "p17_m2_content_verified_public_fixture.py"
    ).create_sources(
        root / "public-source",
        checker.helper("acquisition_fixture_source", "p17_m2_input_export_independent.py"),
    )
    plan.update(
        root=str(root),
        source_root=str(root / "public-source"),
        content_root=str(root / "content"),
        backup_root=str(root / "backup-content"),
        content_contract=contract,
        public_source_identity=source_identity,
    )
    plan["binding"]["content_contract_sha256"] = checker.digest(checker.canonical(contract))
    producer = checker.helper("acquisition_producer_subject", "p17_m2_input_export.py")
    source_reader = producer.Reader(
        root / "public-source",
        execution_identity=producer.LOCAL_IDENTITY,
        source_identity_checks=True,
    )
    registry = producer.register(source_reader, contract)
    return checker, plan, producer, source_reader, registry


def test_independent_r0_reads_the_complete_new_public_closure_with_own_algorithm(tmp_path):
    checker, plan, _, producer, registry = new_public_case(tmp_path)
    proof = checker.independent_r0(
        Path(plan["source_root"]),
        plan["content_contract"],
        registry,
        producer.source_observations,
        plan["public_source_identity"],
        plan=plan,
    )
    assert proof["status"] == "SOURCE_ACQUISITION_R0_CHECKED"
    assert proof["execution_identity"] == IDENTITY
    assert proof["source_count"] == 40
    assert proof["scope"] == "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
    assert proof["formal_or_scientific_admission"] is False
    assert proof["helper_identity_relabelled"] is False


def test_bound_source_escape_refuses_before_any_filesystem_io(monkeypatch):
    import pytest

    checker, plan = binding_plan()
    plan["source_root"] = "/Users/keith1117/Documents/TopoLab-data"

    def forbidden_open(*args, **kwargs):
        raise AssertionError("source escape reached filesystem")

    monkeypatch.setattr("os.open", forbidden_open)
    with pytest.raises(ValueError, match="root|literal|source"):
        checker.validate_binding(plan)


def test_independent_r1_compares_all_new_payloads_and_restricted_content(tmp_path):
    checker, plan, producer, _, registry = new_public_case(tmp_path)
    local = checker.helper("acquisition_local_content_subject", "p17_m2_local_input_version.py")
    content = local.LocalContent(Path(plan["content_root"]), registry, plan["contract_sha256"])
    content.write("source_registry.json", producer.canonical(registry))
    source_reader = producer.Reader(
        Path(plan["source_root"]),
        execution_identity=producer.LOCAL_IDENTITY,
        source_identity_checks=True,
    )
    producer.export(
        source_reader, registry, plan["content_contract"], content.root, local_content=content
    )
    closed = content.finish()
    closed["root_identity"] = checker.native._checked_root(content.root)
    proof = checker.independent_r1(
        Path(plan["source_root"]),
        content.root,
        registry,
        source_reader.source_observations,
        closed,
        plan["contract_sha256"],
        plan["public_source_identity"],
        plan=plan,
    )
    assert proof["status"] == "SOURCE_ACQUISITION_R1_CHECKED"
    assert proof["source_count"] == 558
    assert len(proof["local_identity_rows"]) == 1071
    assert proof["version_id"] == closed["version_id"]
    assert proof["formal_or_scientific_admission"] is False


def test_binding_uses_actual_frozen_preparation_protocol_and_proposal_bytes():
    import pytest

    checker, plan = binding_plan()
    plan["preparation_contract_sha256"] = "f" * 64
    plan["contract_sha256"] = "f" * 64
    plan["binding"]["preparation_protocol_sha256"] = "f" * 64
    plan["source_tree"][checker.PREPARATION_PROTOCOL] = "f" * 64
    with pytest.raises(ValueError, match="protocol|contract|preparation"):
        checker.validate_binding(plan)


def test_new_result_projection_and_closed_failure_keep_their_explicit_identity():
    checker, pending, completion, events, inner, profiles = public_role_facts()
    observed = checker.check_closed_attempt(
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
        expected_identity=IDENTITY,
        result_seconds=(7200, 7200),
    )
    assert observed["closed_attempt_verified"] is True
    assert observed["input_version_accepted"] is False
    assert observed["known_cost_lower_bound_seconds"] == 300


def test_new_backup_cannot_use_projected_original_as_content_even_before_io(monkeypatch):
    import pytest

    checker, plan = binding_plan()

    def forbidden_open(*args, **kwargs):
        raise AssertionError("backup source escape reached filesystem")

    monkeypatch.setattr("os.open", forbidden_open)
    with pytest.raises(ValueError, match="root|literal|source"):
        checker.independent_backup(
            Path("/Users/keith1117/Documents/TopoLab-data"),
            Path(plan["backup_root"]),
            {},
            {},
            plan["contract_sha256"],
            plan=plan,
        )


def test_serialized_preparation_PASS_cannot_construct_a_source_input_capability():
    import pytest

    checker = load_acquisition()
    with pytest.raises(ValueError, match="independent|authority|verified"):
        checker.CheckedAcquisitionInput(
            {
                "status": "PASS",
                "scope": checker.REHEARSAL_SCOPE,
                "formal_authority": False,
                "source_input_accepted": True,
            }
        )


def formal_binding_plan(tmp_path, monkeypatch):
    """Future authority policy fixture in a NEW software-only directory, no target IO."""
    import json

    checker, plan = binding_plan()
    software = tmp_path / "software-policy"
    for name in (checker.PROPOSAL, checker.PREPARATION_PROTOCOL, checker.CONTENT_CONTRACT):
        out = software / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes((checker.REPO / name).read_bytes())
    content = json.loads((software / checker.CONTENT_CONTRACT).read_bytes())
    authority = {
        "schema": "topolab.v2.m2-source-acquisition-execution-authority.v1",
        "execution_identity": IDENTITY,
        "proposal_sha256": checker.PROPOSAL_SHA256,
        "owner_approval_reference": "SYNTHETIC_UNIT_POLICY_ONLY_NOT_CURRENT_OWNER_GRANT",
        "actors": {"executor": "unit-producer", "independent": "unit-checker"},
        "preparation_closure_sha256": "7" * 64,
        "independent_preflight_sha256": "8" * 64,
        "implementation_commit": "9" * 40,
        "permissions": {
            "formal_activation": True,
            "old_original_access": True,
            "target_access": True,
            "B_C": False,
        },
        "formal_seconds": 4500,
        "result_seconds": {"exporter": 7200, "independent": 7200},
    }
    authority_path = "docs/planning/p17_m2_source_acquisition_execution_protocol.json"
    raw = checker.canonical(authority)
    (software / authority_path).write_bytes(raw)
    authority_sha = checker.digest(raw)
    target = "/Users/keith1117/Library/Application Support/TopoLab-custody/"
    target += "p17-m2-local-input-version-v2"
    plan.update(
        scope=checker.FORMAL_SCOPE,
        formal_authority=True,
        root=target,
        source_root="/Users/keith1117/Documents/TopoLab-data",
        content_root=target + "/content",
        backup_root=target + "-independent-backup",
        content_contract=content,
        source_identity={
            "B3_DATA_HASH": checker.native.base.B3_DATA_HASH,
            "CATALOG_HASH": checker.native.base.CATALOG_HASH,
        },
        contract_sha256=authority_sha,
    )
    del plan["public_source_identity"]
    plan["source_tree"][authority_path] = authority_sha
    plan["binding"].update(
        formal_authority=True,
        old_original_access=True,
        target_access=True,
        content_contract_sha256=checker.digest(checker.canonical(content)),
        execution_protocol_sha256=authority_sha,
    )
    monkeypatch.setattr(checker, "REPO", software)
    return checker, plan, software / authority_path


def test_future_formal_binding_needs_separate_frozen_authority_and_exact_original_contract(
    tmp_path, monkeypatch
):
    import pytest

    checker, plan, authority = formal_binding_plan(tmp_path, monkeypatch)
    assert checker.validate_binding(plan)["formal_authority"] is True
    plan["content_contract"]["checkpoints"]["fixed_rows"][3]["selected_epoch"] = 124
    plan["binding"]["content_contract_sha256"] = checker.digest(
        checker.canonical(plan["content_contract"])
    )
    with pytest.raises(ValueError, match="content|fixed|original"):
        checker.validate_binding(plan)
    authority.unlink()
    with pytest.raises(ValueError, match="author|protocol|grant"):
        checker.validate_binding(plan)


def test_future_failure_prefix_has_only_the_already_registered_direct_backup(tmp_path, monkeypatch):
    checker, plan, _ = formal_binding_plan(tmp_path, monkeypatch)
    captured = {}

    def pure_receiver(root, backup, rows, **kwargs):
        captured.update(kwargs)
        assert kwargs["root_guard"](backup) == Path(plan["backup_root"])
        return {"status": kwargs["checked_status"]}

    monkeypatch.setattr(checker.native, "independent_prefix_backup", pure_receiver)
    observed = checker.independent_prefix_backup(
        Path(plan["root"]), Path(plan["backup_root"]), [], plan=plan
    )
    assert observed["status"] == "SOURCE_ACQUISITION_FAILED_PREFIX_BACKUP_CHECKED"
    assert captured["expected_backup"] == Path(plan["backup_root"])


def test_new_certificate_factory_requires_actual_complete_tool_observations():
    import pytest

    checker, plan = binding_plan()
    with pytest.raises(ValueError, match="actual trusted tool"):
        checker.audit_certificate({"plan": plan}, trusted_tool_events={})


def test_new_result_profile_requires_both_7200_deadlines_and_keeps_FULL180():
    from datetime import UTC, datetime

    checker, pending, completion, events, inner, profiles = public_role_facts()
    fixture_spec = importlib.util.spec_from_file_location(
        "acquisition_result_unit_native_facts",
        Path(__file__).with_name("test_p17_m2_content_verified_independent.py"),
    )
    fixture = importlib.util.module_from_spec(fixture_spec)
    fixture_spec.loader.exec_module(fixture)
    inner["expected_role"] = inner["record"]["role"] = "final-filing"
    for record in (pending, completion):
        record.update(
            role="final-filing",
            frozen_FULL_seconds=180,
            result_start_UTC_seconds=5500.0,
            result_deadlines_UTC={
                actor: datetime.fromtimestamp(12700, UTC)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
                for actor in ("exporter", "independent")
            },
        )
    events[0].update(start_seconds=9500.0, end_seconds=9507.015)
    events[1].update(start_seconds=9517.0, end_seconds=9517.25)
    next(row for row in completion["resource_components"] if row["kind"] == "wait4")["record"][
        "launched_UTC_seconds"
    ] = 9500.01
    fixture.seal_native_facts(checker, pending, completion, inner, profiles, events)
    kwargs = dict(
        raw_tool_events=events,
        expected_role="final-filing",
        expected_plan_sha256="a" * 64,
        inner_evidence=inner,
        native_profiles=profiles,
        expected_identity=IDENTITY,
    )
    accepted = checker.audit_role(pending, completion, result_seconds=(7200, 7200), **kwargs)
    assert accepted["full_role_evidence_accepted"] is True
    assert accepted["known_cost_lower_bound_seconds"] == accepted["frozen_FULL_seconds"] == 180
    old_profile = checker.audit_role(pending, completion, **kwargs)
    assert old_profile["full_role_evidence_accepted"] is False
    assert old_profile["known_cost_lower_bound_seconds"] == 180


def test_future_authority_cannot_skip_distinct_authors_or_published_preparation_references(
    tmp_path, monkeypatch
):
    import json

    import pytest

    checker, plan, path = formal_binding_plan(tmp_path, monkeypatch)
    grant = json.loads(path.read_bytes())
    grant["actors"]["independent"] = grant["actors"]["executor"]
    raw = checker.canonical(grant)
    path.write_bytes(raw)
    changed = checker.digest(raw)
    plan["binding"]["execution_protocol_sha256"] = changed
    plan["contract_sha256"] = plan["source_tree"][checker.EXECUTION_PROTOCOL] = changed
    with pytest.raises(ValueError, match="author|preparation|appoint|authority"):
        checker.validate_binding(plan)


def test_future_authority_rejects_duplicate_keys_before_declared_path_io(tmp_path, monkeypatch):
    import pytest

    checker, plan, path = formal_binding_plan(tmp_path, monkeypatch)
    raw = path.read_bytes().replace(
        b'"formal_seconds":4500', b'"formal_seconds":1,"formal_seconds":4500'
    )
    path.write_bytes(raw)
    changed = checker.digest(raw)
    plan["binding"]["execution_protocol_sha256"] = changed
    plan["contract_sha256"] = plan["source_tree"][checker.EXECUTION_PROTOCOL] = changed
    with pytest.raises(ValueError, match="duplicate|JSON|parse"):
        checker.validate_binding(plan)


def setup_metadata_case():

    checker, plan = binding_plan()
    plan_sha = checker.digest(checker.canonical(plan))
    source_sha = checker.digest(checker.canonical(plan["source_tree"]))
    initial = {
        "scope": "COOPERATIVE_REGISTERED_TOPOLAB_ONLY",
        "execution_identity": IDENTITY,
        "root": plan["content_root"],
        "version_id": None,
        "state": "HELD",
        "registered_readers": [*plan["role_order"], "final-filing"],
        "plan_sha256": plan_sha,
        "source_tree_sha256": source_sha,
        "acquired_UTC_seconds": 1000.5,
        "acquired_monotonic": 100.5,
    }
    physical = {
        "st_dev": 1,
        "st_ino": 2,
        "st_size": len(checker.canonical(initial)),
        "st_mtime_ns": 3,
    }
    setup = {
        "execution_identity": IDENTITY,
        "scope": checker.REHEARSAL_SCOPE,
        "plan_sha256": plan_sha,
        "contract_sha256": plan["contract_sha256"],
        "source_tree_sha256": source_sha,
        "lease_record_sha256": checker.digest(checker.canonical(initial)),
        "lease_identity": physical,
        "setup_start_UTC_seconds": 1000.0,
        "setup_end_UTC_seconds": 1001.0,
        "setup_seconds": 1.0,
    }
    bundle = {
        "plan": plan,
        "plan_sha256": plan_sha,
        "setup": setup,
        "initial_lease": initial,
        "initial_lease_identity": physical,
        "backup": {"custody_log": [initial], "custody_lease": initial},
        "lease": initial,
    }
    proof = {"setup_proof_sha256": checker.digest(checker.canonical(setup))}
    return checker, bundle, proof


def test_setup_binding_rejects_resealed_plan_source_or_lease_metadata():
    import pytest

    checker, bundle, proof = setup_metadata_case()
    checker.validate_setup(bundle, proof, {"T0": 1010.0})
    bundle["setup"]["source_tree_sha256"] = "0" * 64
    proof["setup_proof_sha256"] = checker.digest(checker.canonical(bundle["setup"]))
    with pytest.raises(ValueError, match="setup|source|lease"):
        checker.validate_setup(bundle, proof, {"T0": 1010.0})


def test_setup_binding_uses_exact_frozen_actor_start_even_if_proof_hash_is_resealed():
    import pytest

    checker, bundle, proof = setup_metadata_case()
    bundle["setup"]["setup_start_UTC_seconds"] = 999.0
    proof["setup_proof_sha256"] = checker.digest(checker.canonical(bundle["setup"]))
    with pytest.raises(ValueError, match="setup|start|window"):
        checker.validate_setup(bundle, proof, {"T0": 1010.0})


def test_software_reader_rejects_new_public_FIFO_without_blocking(tmp_path):
    import os
    import subprocess
    import sys

    fifo = tmp_path / "public-software-fifo"
    os.mkfifo(fifo, 0o600)
    program = Path(__file__).parents[1] / "scripts/p17_m2_content_verified_independent.py"
    code = """
import importlib.util,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('fifo_guard_software_only',sys.argv[1])
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
try:
    m._software_bytes(Path(sys.argv[2]))
except ValueError:
    print('REJECTED_NONREGULAR_SOFTWARE')
else:
    raise AssertionError('software FIFO was accepted')
"""
    observed = subprocess.run(
        [str(Path(sys.orig_argv[0]).resolve()), "-I", "-c", code, str(program), str(fifo)],
        timeout=2,
        capture_output=True,
        text=True,
    )
    assert observed.returncode == 0, observed.stderr
    assert observed.stdout.strip() == "REJECTED_NONREGULAR_SOFTWARE"


def test_public_software_closure_includes_a_safely_present_future_contract(tmp_path, monkeypatch):
    checker, _, authority = formal_binding_plan(tmp_path, monkeypatch)
    _, plan = binding_plan()
    plan["source_tree"][checker.EXECUTION_PROTOCOL] = checker.digest(authority.read_bytes())
    plan["runtime"] = {"python": "/unit/python", "cwd": str(checker.REPO)}
    plan["result_window_projection_seconds"] = {"exporter": 7200, "independent": 7200}
    for role in ("public-consumer", "reader-ack"):
        plan["metadata_actions"][role]["argv"] = [
            "/unit/python",
            "-I",
            str(checker.REPO / "scripts/p17_m2_source_acquisition_control.py"),
            "payload",
            "--root",
            plan["root"],
            "--plan-sha",
            "@PLAN_SHA256@",
            "--role",
            role,
            "--reader-role",
            "@READER_ROLE@",
        ]
    captured = {}

    def inspect_closure_context(plan, **kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(checker.native, "_check_software", inspect_closure_context)
    checker._check_software(plan)
    assert checker.EXECUTION_PROTOCOL in captured["contracts"]
    assert plan["binding"]["old_original_access"] is False
    assert plan["binding"]["target_access"] is False


def test_fixed_content_contract_rejects_JSON_boolean_for_integer_one(tmp_path, monkeypatch):
    import pytest

    checker, plan = binding_plan()
    plan["content_contract"]["R0"]["metadata_read_passes_per_role"] = True
    plan["binding"]["content_contract_sha256"] = checker.digest(
        checker.canonical(plan["content_contract"])
    )
    with pytest.raises(ValueError, match="content|fixed|projection"):
        checker.validate_binding(plan)
    checker, plan, _ = formal_binding_plan(tmp_path, monkeypatch)
    plan["content_contract"]["R0"]["metadata_read_passes_per_role"] = True
    plan["binding"]["content_contract_sha256"] = checker.digest(
        checker.canonical(plan["content_contract"])
    )
    with pytest.raises(ValueError, match="content|fixed|original"):
        checker.validate_binding(plan)


def test_future_authority_requires_literal_boolean_permission_not_integer_one(
    tmp_path, monkeypatch
):
    import json

    import pytest

    checker, plan, path = formal_binding_plan(tmp_path, monkeypatch)
    authority = json.loads(path.read_bytes())
    authority["permissions"]["target_access"] = 1
    raw = checker.canonical(authority)
    path.write_bytes(raw)
    changed = checker.digest(raw)
    plan["binding"]["execution_protocol_sha256"] = changed
    plan["contract_sha256"] = plan["source_tree"][checker.EXECUTION_PROTOCOL] = changed
    with pytest.raises(ValueError, match="authority|grant|permission"):
        checker.validate_binding(plan)
