"""Independent v3 authority routing; all fixtures are NEW public metadata."""

import importlib.util
import json
import os
import shlex
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
IDENTITY = "topolab.v2.p17-m2-hash-bound-source-acquisition.v3"
PROTOCOL = "docs/planning/p17_m2_new_source_acquisition_protocol.json"
SCHEMA = "topolab.v2.m2-new-source-acquisition-authority.v1"
PARENT = "/Users/keith1117/Library/Application Support/TopoLab-custody"
GENERATION = PARENT + "/p17-m2-local-input-version-v7-hash-bound-20261028"
FULL = {
    "independent-public-check": 300, "exporter-r0": 300, "independent-r0": 300,
    "exporter-r1": 1200, "independent-r1": 1200, "shared-closeout": 300,
}


def fixture(tmp_path, monkeypatch, *, formal=False):
    spec = importlib.util.spec_from_file_location(
        "new_source_independent_fixture", Path(__file__).with_name(
            "test_p17_m2_source_acquisition_independent.py"))
    assert spec and spec.loader
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    checker, plan = fixtures.binding_plan()
    frozen = tmp_path / "git-software"
    for name in (checker.CONTENT_CONTRACT, checker.PROPOSAL, checker.PREPARATION_PROTOCOL):
        (frozen / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / name, frozen / name)
    authority = {
        "schema": SCHEMA, "execution_identity": IDENTITY,
        "source_identity_policy": "topolab.source-identity.prebound-sha256.v1",
        "owner_approval_reference": ("Direct continuous owner authority, "
                                     "new unstarted finite budget"),
        "permissions": {"formal_activation": True, "old_original_access": True,
                        "target_access": True, "B_C": False},
        "formal_seconds": 4500,
        "result_seconds": {"exporter": 9000, "independent": 9000},
        "outer_wall_seconds": 129600, "total_new_author_charged_seconds_cap": 201600,
        "actors": {"executor": "/root", "independent": "/root/ci_recovery_independent"},
        "formal_admission": "CONDITIONAL_ON_FROZEN_READINESS",
        "readiness_freeze_state": "PENDING_PUBLICATION_PREFLIGHT",
        "role_order": list(FULL), "FULL_by_role": deepcopy(FULL),
        "source_whitelist": {
            "original_contract": checker.CONTENT_CONTRACT,
            "raw_sha256": checker.CONTENT_CONTRACT_SHA256,
            "per_author_per_file_reads": 1, "r0_metadata": 40, "r1_payload": 558,
            "version_members": 1071, "total_old_source_reads_per_attempt_max": 1196,
            "metadata_acceptance_before_payload_stat_open": True,
        },
        "fixed_target": {"parent": PARENT, "attempts": {"1": {
            "generation": GENERATION, "backup": GENERATION + "-independent-backup"}}},
    }
    draft = json.loads((REPO / PROTOCOL).read_bytes())
    for key in ("budget", "budget_initial_raw_sha256", "budget_allocation_raw_sha256",
                "custody_integrity", "independent_preflight_path", "independent_preflight_sha256",
                "preparation_closure_paths", "preparation_closure_sha256",
                "implementation_base_commit", "published_source_sha256"):
        authority[key] = deepcopy(draft[key])
    authority["source_whitelist"]["strict_unbound_metadata_count"] = 23
    root = str(tmp_path.resolve() / "topolab-public-new-source-acquisition-independent")
    plan.update(execution_identity=IDENTITY,
                source_identity_policy="topolab.source-identity.prebound-sha256.v1", root=root,
                source_root=root+"/public-source", content_root=root+"/content",
                backup_root=root+"/backup-content")
    plan["binding"].update(source_identity_policy=plan["source_identity_policy"],
                           authority_protocol_path=PROTOCOL)
    if formal:
        plan.update(scope=checker.FORMAL_SCOPE, formal_authority=True, root=GENERATION,
                    source_root="/Users/keith1117/Documents/TopoLab-data",
                    content_root=GENERATION+"/content",
                    backup_root=GENERATION+"-independent-backup",
                    content_contract=json.loads((frozen/checker.CONTENT_CONTRACT).read_bytes()),
                    source_identity={"B3_DATA_HASH": checker.native.base.B3_DATA_HASH,
                                     "CATALOG_HASH": checker.native.base.CATALOG_HASH})
        del plan["public_source_identity"]
        plan["binding"].update(formal_authority=True, old_original_access=True,
                               target_access=True, formal_attempt=1)
        plan["binding"]["content_contract_sha256"] = checker.digest(
            checker.canonical(plan["content_contract"]))
    monkeypatch.setattr(checker, "REPO", frozen)
    reseal(checker, plan, authority)
    return checker, plan, authority


def reseal(checker, plan, authority):
    raw = checker.canonical(authority)
    (checker.REPO / PROTOCOL).write_bytes(raw)
    sha = checker.digest(raw)
    plan["source_tree"][PROTOCOL] = sha
    plan["preparation_contract_sha256"] = sha
    plan["contract_sha256"] = sha
    plan["binding"]["preparation_protocol_sha256"] = sha
    if plan["formal_authority"]:
        plan["binding"]["execution_protocol_sha256"] = sha


def test_new_public_identity_accepts_only_its_new_authority_with_zero_original_permissions(
    tmp_path, monkeypatch
):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    binding = checker.validate_binding(plan)
    assert binding["authority_protocol_path"] == PROTOCOL
    assert all(binding[key] is False for key in (
        "formal_authority", "old_original_access", "target_access", "B_C"))


@pytest.mark.parametrize("root", [
    "/private/tmp/topolab-public-funded-acquisition-old",
    "/private/tmp/topolab-public-hash-bound-old",
    "/private/tmp/topolab-public-formal-binding-old",
])
def test_new_authority_cannot_reuse_an_old_public_generation(tmp_path, monkeypatch, root):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    plan.update(root=root, source_root=root+"/public-source", content_root=root+"/content",
                backup_root=root+"/backup-content")
    with pytest.raises(ValueError, match="new source.*root|new source.*prefix"):
        checker.validate_binding(plan)


@pytest.mark.parametrize(("section", "field", "value"), [
    ("budget", "source_attempts", 2),
    ("budget", "source_CLI_max", 27),
    ("budget", "source_max_reads_each_attempt", 1197),
    ("budget", "source_FULL_max", 3781),
    ("budget", "clock_start_unix_ms", 1793169554001),
    ("budget", "total_author_seconds_cap", 198001),
    ("budget", "conditional_executor_seconds_cap", 39601),
    ("budget", "conditional_independent_seconds_cap", 39601),
    ("budget", "source_each_author_once_per_original_per_attempt", True),
    ("budget", "resource_RSS_bytes", 4294967297),
    ("source_whitelist", "strict_unbound_metadata_count", 0),
    ("custody_integrity", "permanent_0555_required", True),
])
def test_new_authority_rejects_a_resealed_budget_policy_or_unbound_quota_change(
    tmp_path, monkeypatch, section, field, value
):
    checker, plan, authority = fixture(tmp_path, monkeypatch)
    authority[section][field] = value
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="new source"):
        checker.validate_binding(plan)


def test_new_public_source_plan_reuse_binds_same_new_identity_and_exact_prepare_argv(
    tmp_path, monkeypatch
):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    origin = deepcopy(plan)
    root = tmp_path.resolve() / "topolab-public-new-source-acquisition-origin"
    root.mkdir(mode=0o700)
    origin.update(root=str(root), source_root=str(root / "public-source"),
                  content_root=str(root / "content"), backup_root=str(root / "backup-content"))
    path = root / "plan.json"
    raw = checker.canonical(origin)
    path.write_bytes(raw)
    plan["binding"].update(public_source_plan=str(path),
                           public_source_plan_sha256=checker.digest(raw))
    binding = checker.validate_binding(plan)
    assert checker.public_prepare_suffix(plan) == (
        "--public-source-plan", str(path), "--public-source-plan-sha",
        binding["public_source_plan_sha256"],
    )


def formal_ready(checker, plan, authority):
    """Public Git-local metadata fixture; never proof of real publication."""
    authority.update(readiness_freeze_state="REVIEWED_FROZEN",
                     implementation_base_commit="b" * 40,
                     preparation_closure_sha256="c" * 64,
                     independent_preflight_sha256="a" * 64,
                     published_source_sha256={key: value for key, value in
                                              plan["source_tree"].items() if key != PROTOCOL})
    reseal(checker, plan, authority)


def test_new_formal_metadata_binds_one_fresh_literal_generation_without_probing_it(
    tmp_path, monkeypatch
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)
    software_bytes = checker.native._software_bytes

    def git_only(path):
        assert Path(path).is_relative_to(checker.REPO), "formal validation probed external path"
        return software_bytes(path)

    monkeypatch.setattr(checker.native, "_software_bytes", git_only)
    assert checker.validate_binding(plan)["formal_attempt"] == 1
    assert checker.result_window_seconds(plan) == (9000, 9000)


def test_new_unstarted_result_window_requires_9000_and_rejects_closed_7200(
    tmp_path, monkeypatch
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    authority.update(result_seconds={"exporter": 9000, "independent": 9000},
                     total_new_author_charged_seconds_cap=201600,
                     budget_allocation_raw_sha256=(
                         "02d3e2853a6d9e474b2eaa201d7a1cc88675dd9c58f64e61b9ae93beec4022b3"))
    authority["budget"].update(total_author_seconds_cap=201600,
                               independent_author_seconds_cap=82800,
                               conditional_independent_seconds_cap=39600,
                               source_result_each_author_each_attempt=9000)
    formal_ready(checker, plan, authority)
    assert checker.result_window_seconds(plan) == (9000, 9000)
    authority["result_seconds"] = {"exporter": 7200, "independent": 7200}
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="authority.*budget"):
        checker.result_window_seconds(plan)


@pytest.mark.parametrize("field,value", [
    ("readiness_freeze_state", "DRAFT_PUBLIC_PREPARATION_NOT_FORMAL"),
    ("implementation_base_commit", None),
    ("implementation_base_commit", "unmerged-candidate"),
    ("preparation_closure_sha256", "0" * 64),
    ("independent_preflight_sha256", None),
    ("published_source_sha256", {}),
    ("independent_preflight_path",
     "/private/tmp/topolab-funded-continuation-20261026/preflight.json"),
    ("preparation_closure_paths", ["/private/tmp/other-closeout.json"]),
])
def test_new_formal_identity_rejects_unpublished_or_cross_action_readiness(
    tmp_path, monkeypatch, field, value
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)
    authority[field] = value
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="new source|readiness"):
        checker.validate_binding(plan)


def test_new_certificate_software_closure_includes_its_actual_new_authority(
    tmp_path, monkeypatch
):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    plan["runtime"] = {"python": "/public/python", "cwd": str(checker.REPO)}
    plan["result_window_projection_seconds"] = {"exporter": 9000, "independent": 9000}
    for role in ("public-consumer", "reader-ack"):
        plan["metadata_actions"][role]["argv"] = [
            "/public/python", "-I",
            str(checker.REPO / "scripts/p17_m2_source_acquisition_control.py"),
            "payload", "--root", plan["root"], "--plan-sha", "@PLAN_SHA256@",
            "--role", role, "--reader-role", "@READER_ROLE@",
        ]
    closure = {}

    def capture_context(value, **kwargs):
        closure.update(kwargs)

    monkeypatch.setattr(checker.native, "_check_software", capture_context)
    checker._check_software(plan)
    assert PROTOCOL in closure["contracts"]
    assert {
        "scripts/p17_m2_scientific_tool_ingress.mjs",
        "scripts/p17_m2_scientific_metadata.mjs",
        "scripts/p17_m2_scientific_metadata_manifest.mjs",
    } <= set(closure["contracts"])


def preflight_record(checker, plan, authority, monkeypatch, *, mutation=None):
    plan["runtime"] = {"python": ("/Library/Frameworks/Python.framework/Versions/3.12/Resources/"
                                 "Python.app/Contents/MacOS/Python"), "isolated": 1,
                       "cwd": "/private/tmp/topolab-source-route-20261028",
                       "threads": {name: "1" for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS",
                           "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS")}}
    plan["actor_activation_UTC_seconds"] = 1793176000.0
    projection = {key: value for key, value in authority.items() if key not in (
        "readiness_freeze_state", "published_source_sha256", "independent_preflight_sha256")}
    return {
        "schema": "topolab.new-source-v3.independent-preflight.v1",
        "author": "/root/ci_recovery_independent",
        "status": "PASS_PUBLIC_METADATA_LAUNCH_PREFLIGHT", "execution_identity": IDENTITY,
        "authority_protocol_path": PROTOCOL,
        "reviewed_authority_projection_sha256": checker.digest(checker.canonical(projection)),
        "actors": deepcopy(authority["actors"]),
        "published_source_sha256": deepcopy(authority["published_source_sha256"]),
        "runtime": deepcopy(plan["runtime"]),
        "actual_public_pipeline": pipeline_record(
            checker, plan, authority, monkeypatch, mutation=mutation),
        "expected_white_list_contract": {
            "raw_sha256": checker.CONTENT_CONTRACT_SHA256, "r0_metadata": 40,
            "r1_payload": 558, "version_members": 1071,
            "total_old_source_reads_per_attempt_max": 1196, "per_author_per_file_reads": 1},
    }



def pipeline_record(checker, plan, authority, monkeypatch, *, mutation=None):
    """Model actual-tool metadata at the filesystem seam; runs no native command."""
    evidence = "/private/tmp/topolab-ci-recovery-20261028/"
    public_root = "/private/tmp/topolab-public-new-source-acquisition-20261028-v2"
    repo = "/private/tmp/topolab-source-route-20261028"
    table = "92d9b8b48e60ce23296f6514d26fb4d7ea298ee3f32510311e1dcc7914f2cba5"
    snapshot = deepcopy(authority)
    snapshot.update(readiness_freeze_state="DRAFT_PUBLIC_PREPARATION_NOT_FORMAL",
                    published_source_sha256=None, independent_preflight_sha256=None)
    snapshot_raw = checker.canonical(snapshot)
    public = deepcopy(plan)
    public.update(root=public_root, source_root=public_root+"/public-source",
                  content_root=public_root+"/content", backup_root=public_root+"/backup-content",
                  scope=checker.REHEARSAL_SCOPE, formal_authority=False)
    public["binding"].update(formal_authority=False, old_original_access=False,
                             target_access=False)
    public["binding"].pop("formal_attempt")
    public["binding"].pop("execution_protocol_sha256")
    snapshot_sha = checker.digest(snapshot_raw)
    public["source_tree"][PROTOCOL] = snapshot_sha
    public["contract_sha256"] = public["preparation_contract_sha256"] = snapshot_sha
    public["binding"]["preparation_protocol_sha256"] = snapshot_sha
    public_raw = checker.canonical(public)
    plan_sha = checker.digest(public_raw)
    prefix = [plan["runtime"]["python"], "-I",
              repo + "/scripts/p17_m2_source_acquisition_control.py"]
    roles = [*FULL, "final-filing", "lease-release", "public-consumer", "reader-ack"]
    certificate = {"scope": checker.REHEARSAL_SCOPE, "formal_authority": False,
                   "source_input_accepted": False, "B_C_admission": False,
                   "formal_or_scientific_admission": False, "member_count": 1071,
                   "version_id": "e" * 64}
    cert_raw = checker.canonical(certificate)
    commands = [("prepare", [*prefix, "prepare-rehearsal", "--root", public_root],
                 {"scope": checker.REHEARSAL_SCOPE, "formal_authority": False,
                  "plan_sha256": plan_sha})]
    for role in roles:
        if role == "public-consumer":
            commands.append(("certificate-certify-rehearsal", [*prefix, "certify-rehearsal",
                "--root", public_root, "--plan-sha", plan_sha, "--role", "certificate"],
                certificate))
        for mode in ("supervise", "record", "bind"):
            argv = [*prefix, mode, "--root", public_root, "--plan-sha", plan_sha, "--role", role]
            if role in ("public-consumer", "reader-ack"):
                argv.extend(("--reader-role", "scientific-auditor"))
            if mode != "bind":
                output = {"public_fixture": True}
            else:
                output = {"role": role, "actual_exit_codes": [0, 0], "reason": None,
                          "secondary_failures": []}
                if role in (*FULL, "final-filing"):
                    output.update(full_role_evidence_accepted=True, evidence_complete=True,
                                  primary_failure=None, execution_identity=IDENTITY,
                                  plan_sha256=plan_sha)
                else:
                    output.update(metadata_evidence_accepted=True,
                                  full_role_evidence_accepted=False,
                                  formal_role_or_new_allowance=False, frozen_FULL_seconds=None,
                                  status="PUBLIC_METADATA_ACTION_OBSERVED")
            commands.append((role + "-" + mode, argv, output))
    rows = []
    for offset, (label, argv, output) in enumerate(commands):
        start = 1793170000000 + 10 * offset
        stdout = checker.canonical(output).decode()
        rows.append({"label": label, "argv": argv, "start": start, "end": start + 5,
                     "exit_code": 0, "stdout": stdout,
                     "rawCalls": [{"kind": "exec_command", "observed_return_ms": start + 4,
                                   "args": {"cmd": shlex.join(["env", "OMP_NUM_THREADS=1",
                                       "OPENBLAS_NUM_THREADS=1", "MKL_NUM_THREADS=1",
                                       "VECLIB_MAXIMUM_THREADS=1", "NUMEXPR_NUM_THREADS=1", *argv]),
                                            "workdir": repo, "login": False},
                                   "result": {"output": stdout, "exit_code": 0}}]})
    index = {"schema": "topolab.v3.new-source-public-tool-index.v1",
             "execution_identity": IDENTITY, "root": public_root, "repo": repo,
             "native_interpreter": plan["runtime"]["python"], "call_table_sha256": table,
             "clock_domain": "UTC_UNIX_MILLISECONDS", "clock_resolution_ms": 1,
             "planSha": plan_sha, "cliCount": 32, "completed": rows, "rolesDone": roles,
             "active": None, "pipelineComplete": True, "pipelineEnd": rows[-1]["end"]}
    summary = {
        "schema": "topolab.v3.new-source-public-pipeline-summary.v1",
        "status": "PASS_ACTUAL_PUBLIC32_SOURCE_PIPELINE",
        "scope": "NEW_PUBLIC_SOURCE_PIPELINE_ONLY",
        "execution_identity": IDENTITY,
        "source_identity_policy": "topolab.source-identity.prebound-sha256.v1",
        "root": public_root, "call_table_sha256": table, "plan_sha256": plan_sha,
        "certificate_stdout_sha256": checker.digest(cert_raw),
        "source_version_id": "e" * 64, "source_version_member_count": 1071,
        "actual_top_source_CLI_calls": 32, "actual_roles": roles,
        "consumer": {"reader_role": "scientific-auditor", "members": 1069,
                     "total_bytes": 40590471, "same_read_buffer": True},
        "reader_ack": {"actual_exit_code": 0, "metadata_evidence_accepted": True,
                       "active_lease_absent_after_actual_return": True,
                       "cooperative_lease_absent_after_actual_return": True},
        "formal_authority": False, "source_input_accepted": False,
        "B_C_admission": False, "seed17_repaired": False,
    }
    consumption = {"scope": checker.REHEARSAL_SCOPE, "execution_identity": IDENTITY,
                   "role": "scientific-auditor", "member_count": 1069,
                   "total_bytes": 40590471, "same_read_buffer": True, "formal_authority": False}
    if mutation is not None:
        mutation(index, summary, consumption)
    index_raw = checker.canonical(index)
    summary["actual_tool_index_sha256"] = checker.digest(index_raw)
    summary_raw = checker.canonical(summary)
    files = {evidence + "source-v3-public-pipeline-v2.actual.json": index_raw,
             evidence + "source-v3-public-pipeline-v2.stdout": summary_raw,
             evidence + "source-v3-public-pipeline-v2-certificate.stdout": cert_raw,
             evidence + "source-v3-public-authority-snapshot-v5.json": snapshot_raw,
             public_root + "/plan.json": public_raw,
             public_root + "/public-consumption.json": checker.canonical(consumption)}
    software_bytes = checker.native._software_bytes

    def public_metadata(path):
        return files[str(path)] if str(path) in files else software_bytes(path)

    monkeypatch.setattr(checker.native, "_software_bytes", public_metadata)
    return {"path": evidence + "source-v3-public-pipeline-v2.actual.json",
            "sha256": checker.digest(index_raw),
            "summary_stdout_sha256": checker.digest(summary_raw),
            "certificate_stdout_sha256": checker.digest(cert_raw),
            "authority_snapshot_sha256": snapshot_sha}

def test_new_independent_preflight_binds_distinct_author_source_runtime_and_projection(
    tmp_path, monkeypatch
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)
    preflight = preflight_record(checker, plan, authority, monkeypatch)
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    reseal(checker, plan, authority)
    assert checker.check_funded_preflight(plan, raw)["author"] == "/root/ci_recovery_independent"


def test_actual_pipeline_accepts_bytes_from_a_fresh_exported_fixture_manifest(
    tmp_path, monkeypatch
):
    """The NEW source generator is different from the historical PUBLIC12 graph."""
    spec = importlib.util.spec_from_file_location(
        "new_source_fresh_export_fixture", Path(__file__).with_name(
            "test_p17_m2_source_acquisition_independent.py"))
    assert spec and spec.loader
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    public = tmp_path / "fresh-graph"
    public.mkdir()
    source_checker, source_plan, producer, _, registry = fixtures.new_public_case(public)
    local = source_checker.helper("fresh_byte_manifest", "p17_m2_local_input_version.py")
    content = local.LocalContent(
        Path(source_plan["content_root"]), registry, source_plan["contract_sha256"])
    content.write("source_registry.json", producer.canonical(registry))
    reader = producer.Reader(
        Path(source_plan["source_root"]), execution_identity=producer.LOCAL_IDENTITY,
        source_identity_checks=True)
    producer.export(reader, registry, source_plan["content_contract"], content.root,
                    local_content=content)
    manifest = content.finish()["manifest"]
    members = {row["path"]: row for row in manifest["members"]}
    view = manifest["role_views"]["scientific-auditor"]
    assert len(members) == 1071 and len(view) == 1069
    assert set(members) - set(view) == {"uniform-scalars.json", "source_registry.json"}
    total = sum(members[name]["byte_size"] for name in view)
    assert total == 40590471
    assert sum(len((content.root / name).read_bytes()) for name in view) == total

    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)

    def fresh_total(index, summary, consumption):
        summary["consumer"]["total_bytes"] = total
        consumption["total_bytes"] = total

    preflight = preflight_record(checker, plan, authority, monkeypatch, mutation=fresh_total)
    checker._new_public_pipeline(plan, authority, preflight["actual_public_pipeline"])


@pytest.mark.parametrize(("members", "total_bytes"), [
    (1069, 90256736),  # Historical PUBLIC12 is a different source graph.
    (1069, 40590470),  # Agreement between two shortened projections is insufficient.
    (541, 40590471),   # Producer view cannot replace the independent auditor view.
])
def test_actual_pipeline_rejects_old_fixture_bytes_shortened_consumption_or_wrong_view(
    tmp_path, monkeypatch, members, total_bytes
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)

    def changed_consumption(index, summary, consumption):
        summary["consumer"].update(members=members, total_bytes=total_bytes)
        consumption.update(member_count=members, total_bytes=total_bytes)

    preflight = preflight_record(
        checker, plan, authority, monkeypatch, mutation=changed_consumption)
    with pytest.raises(ValueError, match="actual summary evidence|actual consumer evidence"):
        checker._new_public_pipeline(plan, authority, preflight["actual_public_pipeline"])


def test_actual_public_metadata_reader_rejects_short_read_even_with_unchanged_inode(
    tmp_path, monkeypatch
):
    checker, _, _ = fixture(tmp_path, monkeypatch)
    path = tmp_path / "public-consumption.json"
    raw = checker.canonical({"member_count": 1069, "total_bytes": 40590471})
    path.write_bytes(raw)
    before = path.stat()
    real_read = os.read
    calls = []

    def short_read(fd, size):
        if os.fstat(fd).st_ino != before.st_ino:
            return real_read(fd, size)
        calls.append(size)
        return real_read(fd, min(size, len(raw) - 1)) if len(calls) == 1 else b""

    monkeypatch.setattr(checker.native.os, "read", short_read)
    with pytest.raises(ValueError, match="software closure file identity/length changed"):
        checker.native._software_bytes(path)
    assert len(calls) == 2
    after = path.stat()
    assert (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)


@pytest.mark.parametrize("field,value", [
    ("author", "/root/acquisition_funded_audit"),
    ("authority_protocol_path", "docs/planning/p17_m2_funded_acquisition_protocol.json"),
    ("reviewed_authority_projection_sha256", "a" * 64),
    ("schema", "topolab.old-self-asserted-preflight.v1"),
])
def test_new_independent_preflight_rejects_resealed_old_author_or_self_asserted_readiness(
    tmp_path, monkeypatch, field, value
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)
    preflight = preflight_record(checker, plan, authority, monkeypatch)
    preflight[field] = value
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="new source|preflight"):
        checker.check_funded_preflight(plan, raw)


def test_new_public_namespace_cannot_borrow_a_legacy_funded_identity(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "legacy_funded_for_new_namespace", Path(__file__).with_name(
            "test_p17_m2_funded_acquisition_independent.py"))
    assert spec and spec.loader
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    checker, plan, _ = fixtures.fixture(tmp_path, monkeypatch)
    root = str(tmp_path.resolve() / "topolab-public-new-source-acquisition-borrowed")
    plan.update(root=root, source_root=root+"/public-source", content_root=root+"/content",
                backup_root=root+"/backup-content")
    with pytest.raises(ValueError, match="new source.*identity"):
        checker.validate_binding(plan)


def test_new_preflight_needs_actual_parent_observed_pipeline_before_formal_metadata(
    tmp_path, monkeypatch
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)
    preflight = preflight_record(checker, plan, authority, monkeypatch)
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    reseal(checker, plan, authority)
    del preflight["actual_public_pipeline"]
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="actual public|new source public"):
        checker.check_funded_preflight(plan, raw)


def test_actual_pipeline_rejects_a_different_exec_command_hidden_by_the_argv_projection(
    tmp_path, monkeypatch
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)

    def change(index, summary, consumption):
        index["completed"][0]["rawCalls"][0]["args"]["cmd"] = "python -c 'print(0)'"

    preflight = preflight_record(checker, plan, authority, monkeypatch, mutation=change)
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="actual.*command|actual.*argv"):
        checker.check_funded_preflight(plan, raw)


def waiting_row(index, *, wrong_session=False):
    row = index["completed"][0]
    original = row["rawCalls"][0]
    text = row["stdout"]
    first = deepcopy(original)
    first["observed_return_ms"] = row["start"] + 1
    first["result"] = {"output": text[:3], "session_id": 401}
    last = {"kind": "write_stdin", "args": {"session_id": 402 if wrong_session else 401},
            "observed_return_ms": row["start"] + 4,
            "result": {"output": text[3:], "exit_code": 0}}
    row["rawCalls"] = [first, last]


def test_actual_pipeline_accepts_only_the_actual_owned_session_until_final_return(
    tmp_path, monkeypatch
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)
    preflight = preflight_record(checker, plan, authority, monkeypatch,
                                mutation=lambda index, *_: waiting_row(index))
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    reseal(checker, plan, authority)
    assert checker.check_funded_preflight(plan, raw)["status"] == (
        "PASS_PUBLIC_METADATA_LAUNCH_PREFLIGHT")


@pytest.mark.parametrize("case", [
    "order", "argv", "bool-exit", "unfinished", "truncated", "stdout-rewrite", "overlap",
    "seconds-clock", "missing-raw", "full-bind", "metadata-bind", "certificate-rewrite",
    "seed-claim", "short-consumption", "wrong-session", "wrong-table", "false-complete",
    "consumer-formal", "stdin-control",
])
def test_actual_pipeline_refuses_incomplete_forged_or_relabelled_public_evidence(
    tmp_path, monkeypatch, case
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)

    def change(index, summary, consumption):
        row = index["completed"][0]
        if case == "order":
            index["completed"][1:3] = reversed(index["completed"][1:3])
        elif case == "argv":
            index["completed"][1]["argv"][-1] = "exporter-r0"
        elif case == "bool-exit":
            row["rawCalls"][0]["result"]["exit_code"] = False
        elif case == "unfinished":
            row["rawCalls"][0]["result"].pop("exit_code")
            row["rawCalls"][0]["result"]["session_id"] = 401
        elif case == "truncated":
            row["rawCalls"][0]["result"]["output"] += "Warning: truncated output"
        elif case == "stdout-rewrite":
            row["stdout"] = "{}\n"
        elif case == "overlap":
            index["completed"][1]["start"] = row["start"]
        elif case == "seconds-clock":
            row["start"] /= 1000
            row["end"] /= 1000
        elif case == "missing-raw":
            row["rawCalls"] = []
        elif case in ("full-bind", "metadata-bind"):
            row = index["completed"][3 if case == "full-bind" else 24]
            bound = json.loads(row["stdout"])
            bound["full_role_evidence_accepted"] = case == "metadata-bind"
            row["stdout"] = checker.canonical(bound).decode()
            row["rawCalls"][0]["result"]["output"] = row["stdout"]
        elif case == "certificate-rewrite":
            index["completed"][25]["stdout"] = "{}\n"
            index["completed"][25]["rawCalls"][0]["result"]["output"] = "{}\n"
        elif case == "seed-claim":
            summary["seed17_repaired"] = True
        elif case == "short-consumption":
            consumption["total_bytes"] -= 1
        elif case == "consumer-formal":
            consumption["formal_authority"] = True
        elif case == "wrong-session":
            waiting_row(index, wrong_session=True)
        elif case == "stdin-control":
            waiting_row(index)
            index["completed"][0]["rawCalls"][1]["args"]["chars"] = "\x03"
        elif case == "wrong-table":
            index["call_table_sha256"] = "a" * 64
        elif case == "false-complete":
            index["pipelineComplete"] = False

    preflight = preflight_record(checker, plan, authority, monkeypatch, mutation=change)
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="new source public"):
        checker.check_funded_preflight(plan, raw)


def test_public_pipeline_reads_exact_frozen_v5_snapshot_path(tmp_path, monkeypatch):
    """Missing old snapshots must not redirect a complete NEW metadata graph."""
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    formal_ready(checker, plan, authority)
    preflight = preflight_record(checker, plan, authority, monkeypatch)
    read_metadata = checker.native._software_bytes
    expected = Path(
        "/private/tmp/topolab-ci-recovery-20261028/"
        "source-v3-public-authority-snapshot-v5.json")
    observed = []

    def exact_snapshot(path):
        if path.name.startswith("source-v3-public-authority-snapshot-"):
            observed.append(path)
            assert path == expected, "stale or alternate authority snapshot selected"
        return read_metadata(path)

    monkeypatch.setattr(checker.native, "_software_bytes", exact_snapshot)
    checker._new_public_pipeline(plan, authority, preflight["actual_public_pipeline"])
    assert observed == [expected]
