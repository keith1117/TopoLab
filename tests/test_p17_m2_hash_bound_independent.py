"""Independent source-policy regressions on freshly authored public files."""

import importlib.util
import os
from copy import deepcopy
from pathlib import Path

import pytest


def load(name):
    spec = importlib.util.spec_from_file_location(
        name, Path(__file__).parents[1] / "scripts" / (name + ".py")
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


independent = load("p17_m2_input_export_independent")
local = load("p17_m2_local_input_independent")
POLICY = "topolab.source-identity.prebound-sha256.v1"


def new_reader(tmp_path, *, policy=POLICY, journal=None):
    return independent.OnceReader(
        tmp_path, 1, 1024, source_identity_checks=True,
        source_identity_policy=policy, journal=journal,
    )


def change_after_read(tmp_path, monkeypatch, *, replace=False):
    source = tmp_path / "public.bin"
    source.write_bytes(b"abc")
    real_read = os.read
    changed = False

    def read(fd, maximum):
        nonlocal changed
        raw = real_read(fd, maximum)
        if not changed:
            if replace:
                replacement = tmp_path / "replacement.bin"
                replacement.write_bytes(b"abc")
                os.replace(replacement, source)
            else:
                value = source.stat()
                os.utime(source, ns=(value.st_atime_ns, value.st_mtime_ns + 89))
            changed = True
        return raw

    monkeypatch.setattr(os, "read", read)
    return source


@pytest.mark.parametrize("delta", [89, 1000000001, -12345])
def test_prebound_reader_keeps_exact_mtime_changes(tmp_path, monkeypatch, delta):
    source = tmp_path / "public.bin"
    source.write_bytes(b"abc")
    real_read = os.read
    changed = False

    def read(fd, maximum):
        nonlocal changed
        raw = real_read(fd, maximum)
        if not changed:
            value = source.stat()
            os.utime(source, ns=(value.st_atime_ns, value.st_mtime_ns + delta))
            changed = True
        return raw

    reader = independent.OnceReader(
        tmp_path, 1, 1024, source_identity_checks=True, source_identity_policy=POLICY
    )
    monkeypatch.setattr(os, "read", read)
    assert reader.read("public.bin", 1024, sha256=independent.digest(b"abc")) == b"abc"
    row = reader.observations[0]
    assert row["expected_sha256"] == independent.digest(b"abc")
    assert row["mtime_changes"] == {"before": 0, "after": delta, "closing": delta}
    assert local.identity_table([row], 1, source_identity_policy=POLICY)["public.bin"] == row
    with pytest.raises(ValueError):
        local.identity_table([row], 1)


@pytest.mark.parametrize("policy", [None, POLICY])
def test_without_prebound_hash_mtime_change_is_strict(tmp_path, monkeypatch, policy):
    source = change_after_read(tmp_path, monkeypatch)
    reader = new_reader(tmp_path, policy=policy)
    with pytest.raises(ValueError, match="changed during descriptor read"):
        reader.read(source.name, 1024)
    facts = reader.failures[0]
    assert facts["after"]["st_mtime_ns"] - facts["before"]["st_mtime_ns"] == 89
    assert facts["changed_fields"] == ["st_mtime_ns"]
    assert facts["returned_bytes"] == 3 and facts["closing"] is None


def test_legacy_policy_with_prebound_hash_remains_strict(tmp_path, monkeypatch):
    source = change_after_read(tmp_path, monkeypatch)
    reader = new_reader(tmp_path, policy=None)
    with pytest.raises(ValueError, match="changed during descriptor read"):
        reader.read(source.name, 1024, sha256=independent.digest(b"abc"))
    assert reader.failures[0]["changed_fields"] == ["st_mtime_ns"]
    assert "identity_policy" not in reader.failures[0]


@pytest.mark.parametrize("expected", ["", "0" * 63, "G" * 64, True, 1])
def test_invalid_prebound_hash_is_refused_before_source_open(tmp_path, monkeypatch, expected):
    def unexpected(*args, **kwargs):
        pytest.fail("invalid expected hash must not open source")

    monkeypatch.setattr(os, "open", unexpected)
    reader = new_reader(tmp_path)
    with pytest.raises(ValueError, match="prebound SHA256 is invalid"):
        reader.read("public.bin", 1024, sha256=expected)
    assert reader.failures[0]["declared"] is None


def test_prebound_policy_requires_closing_checks(tmp_path):
    with pytest.raises(ValueError, match="requires closing observations"):
        independent.OnceReader(tmp_path, 1, 1024, source_identity_policy=POLICY)


def test_hash_mismatch_keeps_closing_and_raw_facts(tmp_path, monkeypatch):
    source = change_after_read(tmp_path, monkeypatch)
    journal = tmp_path / "journal.jsonl"
    reader = new_reader(tmp_path, journal=journal)
    with pytest.raises(ValueError, match="source SHA differs"):
        reader.read(source.name, 1024, sha256="0" * 64)
    facts = reader.failures[0]
    assert facts["closing"] is not None
    assert facts["mtime_changes"] == {"before": 0, "after": 89, "closing": 89}
    assert facts["source"]["sha256"] == independent.digest(b"abc")
    assert facts["expected_sha256"] == "0" * 64 and facts["returned_bytes"] == 3
    assert reader.observations == []


def test_same_content_replaced_inode_still_stops(tmp_path, monkeypatch):
    source = change_after_read(tmp_path, monkeypatch, replace=True)
    reader = new_reader(tmp_path)
    with pytest.raises(ValueError, match="closing literal path"):
        reader.read(source.name, 1024, sha256=independent.digest(b"abc"))
    facts = reader.failures[0]
    assert facts["after"]["st_ino"] != facts["closing"]["st_ino"]
    assert "st_ino" in facts["changed_fields"]


def test_prebound_hash_does_not_accept_short_read(tmp_path, monkeypatch):
    source = tmp_path / "public.bin"
    source.write_bytes(b"abc")
    real_read = os.read
    first = True

    def read(fd, maximum):
        nonlocal first
        if not first:
            return b""
        first = False
        return real_read(fd, 1)

    monkeypatch.setattr(os, "read", read)
    reader = new_reader(tmp_path)
    with pytest.raises(ValueError, match="read length differs"):
        reader.read(source.name, 1024, sha256=independent.digest(b"abc"))
    assert reader.failures[0]["returned_bytes"] == 1


def test_missing_closing_observation_retains_primary_and_secondary(tmp_path, monkeypatch):
    (tmp_path / "public.bin").write_bytes(b"abc")
    missing_journal = tmp_path / "absent" / "journal.jsonl"
    reader = new_reader(tmp_path, journal=missing_journal)
    real_parent = independent.nofollow_parent
    count = 0

    def parent(path):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("public closing observation missing")
        return real_parent(path)

    monkeypatch.setattr(independent, "nofollow_parent", parent)
    with pytest.raises(OSError, match="closing observation missing"):
        reader.read("public.bin", 1024, sha256=independent.digest(b"abc"))
    facts = reader.failures[0]
    assert facts["closing"] is None and facts["after"] is not None
    assert facts["path"] == "public.bin" and facts["attempt_ordinal"] == 1
    assert facts["returned_bytes"] == 3
    assert "closing observation missing" in facts["primary_reason"]
    assert "FileNotFoundError" in facts["recording_error"]


def test_independent_row_audit_rejects_missing_or_forged_facts(tmp_path):
    (tmp_path / "public.bin").write_bytes(b"abc")
    reader = new_reader(tmp_path)
    reader.read("public.bin", 1024, sha256=independent.digest(b"abc"))
    original = reader.observations[0]
    for field, value in (("declared", None), ("before", None), ("after", None),
                         ("closing", None), ("expected_sha256", "0" * 64),
                         ("mtime_changes", {"before": 0, "after": 89, "closing": 0})):
        corrupted = deepcopy(original)
        corrupted[field] = value
        with pytest.raises(ValueError):
            local.identity_table([corrupted], 1, source_identity_policy=POLICY)


def test_cross_author_mtime_may_differ_only_for_same_prebound_source(tmp_path):
    source = tmp_path / "public.bin"
    source.write_bytes(b"abc")
    first = new_reader(tmp_path)
    first.read(source.name, 1024, sha256=independent.digest(b"abc"))
    value = source.stat()
    os.utime(source, ns=(value.st_atime_ns, value.st_mtime_ns + 89))
    second = new_reader(tmp_path)
    second.read(source.name, 1024, sha256=independent.digest(b"abc"))
    local.compare_identity_tables(first.observations, second.observations, 1,
                                  source_identity_policy=POLICY)
    replaced = deepcopy(second.observations)
    for stage in ("declared", "before", "after", "closing"):
        replaced[0][stage]["st_ino"] += 1
    with pytest.raises(ValueError):
        local.compare_identity_tables(first.observations, replaced, 1,
                                      source_identity_policy=POLICY)


def new_acquisition_binding(monkeypatch):
    fixture = load("../tests/test_p17_m2_source_acquisition_independent")
    checker, plan = fixture.binding_plan()
    plan["execution_identity"] = "topolab.v2.p17-m2-hash-bound-source-acquisition.v1"
    plan["source_identity_policy"] = POLICY
    plan["binding"]["source_identity_policy"] = POLICY
    path = "docs/planning/p17_m2_hash_bound_acquisition_protocol.json"
    authority = {
        "schema": "topolab.v2.m2-hash-bound-acquisition-authority.v1",
        "execution_identity": plan["execution_identity"],
        "source_identity_policy": POLICY,
        "owner_approval_reference": "new direct owner authority",
        "permissions": {"formal_activation": True, "old_original_access": True,
                        "target_access": True, "B_C": False},
        "formal_seconds": 4500,
        "result_seconds": {"exporter": 1200, "independent": 1200},
        "outer_wall_seconds": 14400,
        "total_new_author_charged_seconds_cap": 18000,
        "actors": {"executor": "new-producer", "independent": "new-independent"},
    }
    raw = checker.canonical(authority)
    bound = checker.digest(raw)
    plan["binding"]["preparation_protocol_sha256"] = bound
    plan["preparation_contract_sha256"] = plan["contract_sha256"] = bound
    plan["source_tree"][path] = bound
    original = checker.native._software_bytes

    def software(pathname):
        return raw if pathname == checker.REPO / path else original(pathname)

    monkeypatch.setattr(checker.native, "_software_bytes", software)
    return checker, plan


def test_new_acquisition_binding_accepts_only_explicit_frozen_policy(monkeypatch):
    checker, plan = new_acquisition_binding(monkeypatch)
    assert checker.validate_binding(plan)["source_identity_policy"] == POLICY
    plan["source_identity_policy"] = None
    with pytest.raises(ValueError, match="policy"):
        checker.validate_binding(plan)


def new_public_policy_case(tmp_path, monkeypatch):
    checker, plan = new_acquisition_binding(monkeypatch)
    root = tmp_path / "topolab-public-formal-binding-new-hash-policy"
    root.mkdir(mode=0o700)
    contract, source_identity = checker.helper(
        "hash_bound_independent_fixture", "p17_m2_content_verified_public_fixture.py"
    ).create_sources(root / "public-source", independent)
    plan.update(root=str(root), source_root=str(root / "public-source"),
                content_root=str(root / "content"), backup_root=str(root / "backup-content"),
                content_contract=contract, public_source_identity=source_identity)
    plan["binding"]["content_contract_sha256"] = checker.digest(checker.canonical(contract))
    producer = load("p17_m2_input_export")
    reader = producer.Reader(root / "public-source", execution_identity=producer.LOCAL_IDENTITY,
                             source_identity_checks=True, source_identity_policy=POLICY)
    registry = producer.register(reader, contract)
    return checker, plan, producer, reader, registry


def test_new_source_lineage_and_cross_author_r0_use_same_policy(tmp_path, monkeypatch):
    checker, plan, _, reader, registry = new_public_policy_case(tmp_path, monkeypatch)
    root, contract, source_identity = (
        Path(plan["root"]), plan["content_contract"], plan["public_source_identity"])
    selection = registry["models"][0]["selection"]
    path = root / "public-source" / selection["path"]
    value = path.stat()
    os.utime(path, ns=(value.st_atime_ns, value.st_mtime_ns + 89))
    proof = checker.independent_r0(root / "public-source", contract, registry,
                                   reader.source_observations, source_identity, plan=plan)
    assert proof["execution_identity"] == plan["execution_identity"]
    assert proof["source_count"] == 40
    assert proof["source_comparison"] == (
        "PREBOUND_HASH_AND_PHYSICAL_IDENTITY_MATCHED_TIMESTAMPS_RETAINED")
    forged = deepcopy(proof["source_rows"])
    next(row for row in forged if row["path"] == selection["path"])["expected_sha256"] = None
    with pytest.raises(ValueError, match="accepted lineage"):
        checker.check_expected_source_hashes(forged, registry, contract, "r0")


def test_new_r1_checks_558_payloads_and_1071_content_members(tmp_path, monkeypatch):
    checker, plan, producer, _, registry = new_public_policy_case(tmp_path, monkeypatch)
    content_module = load("p17_m2_local_input_version")
    content = content_module.LocalContent(Path(plan["content_root"]), registry,
                                          plan["contract_sha256"])
    content.write("source_registry.json", producer.canonical(registry))
    reader = producer.Reader(Path(plan["source_root"]), execution_identity=producer.LOCAL_IDENTITY,
                             source_identity_checks=True, source_identity_policy=POLICY)
    producer.export(reader, registry, plan["content_contract"], content.root,
                    local_content=content)
    closed = content.finish()
    closed["root_identity"] = checker.native._checked_root(content.root)
    source = Path(plan["source_root"]) / registry["models"][0]["checkpoint"]["path"]
    info = source.stat()
    os.utime(source, ns=(info.st_atime_ns, info.st_mtime_ns + 89))
    proof = checker.independent_r1(
        Path(plan["source_root"]), content.root, registry, reader.source_observations,
        closed, plan["contract_sha256"], plan["public_source_identity"], plan=plan)
    assert proof["source_count"] == 558 and len(proof["local_identity_rows"]) == 1071
    assert proof["version_id"] == closed["version_id"]
    assert all(row["identity_policy"] == POLICY for row in proof["source_rows"])
    forged = deepcopy(proof["source_rows"])
    forged[0]["expected_sha256"] = None
    with pytest.raises(ValueError, match="accepted lineage"):
        checker.check_expected_source_hashes(forged, registry, plan["content_contract"], "r1")
