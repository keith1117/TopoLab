"""Independent checks for newly authored public local-version fixtures only."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


def load():
    spec = importlib.util.spec_from_file_location(
        "local_input_independent",
        Path(__file__).parents[1] / "scripts/p17_m2_local_input_independent.py",
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def wire(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def registry_fixture():
    epochs = {"C": [168, 137, 92], "P": [123, 134, 169], "W": [93, 156, 142], "S": [65, 115, 127]}
    models = [
        {"family": family, "seed": seed, "epoch": epoch}
        for family in "CPWS"
        for seed, epoch in zip((17, 29, 43), epochs[family], strict=True)
    ]
    labels = [{"case_id": f"tlcase-v1-{ordinal:064x}"} for ordinal in range(528)]
    return {"models": models, "labels": labels, "scalars": []}


def manifest_fixture(registry):
    paths = {
        "source_registry.json": "registry",
        "models.json": "models",
        "uniform-scalars.json": "uniform-scalars",
    }
    for item in registry["models"]:
        paths[f"checkpoints/{item['family']}-{item['seed']}.safetensors"] = "checkpoint"
    for item in registry["labels"]:
        for view in ("producer", "audit"):
            paths[f"nn/{view}/{item['case_id']}.json"] = "nn-" + view
    members = [
        {"path": path, "type": kind, "byte_size": 3, "sha256": hashlib.sha256(b"{}\n").hexdigest()}
        for path, kind in sorted(paths.items())
    ]
    registry_raw = wire(registry)
    for member in members:
        if member["path"] == "source_registry.json":
            member.update(
                byte_size=len(registry_raw), sha256=hashlib.sha256(registry_raw).hexdigest()
            )
    producer = sorted(
        p for p in paths if p.startswith(("checkpoints/", "nn/producer/")) or p == "models.json"
    )
    audit = sorted(producer + [p for p in paths if p.startswith("nn/audit/")])
    return {
        "schema": "topolab.v2.m2-local-input-content.v1",
        "frozen_contract_sha256": "a" * 64,
        "content_scope_sha256": "f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad",
        "source_registry_sha256": hashlib.sha256(registry_raw).hexdigest(),
        "members": members,
        "role_views": {
            "scientific-producer": producer,
            "scientific-auditor": audit,
            "reference-compatibility": ["uniform-scalars.json"],
        },
    }


def test_manifest_is_complete_identity_and_not_permission():
    module = load()
    registry = registry_fixture()
    manifest = manifest_fixture(registry)
    assert len(manifest["members"]) == 1071
    result = module.validate_manifest(manifest, registry, "a" * 64)
    assert result["status"] == "MANIFEST_SHAPE_CHECKED_ONLY"
    assert result["member_count"] == 1071
    assert result["version_id"] == hashlib.sha256(wire(manifest)).hexdigest()
    assert result["consumer_authorized"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "missing",
        "duplicate",
        "extra",
        "order",
        "type",
        "role",
        "contract",
        "selfhash",
        "bytes",
        "hash",
        "epoch",
    ],
)
def test_manifest_rejects_changed_scope_or_false_identity(damage):
    module = load()
    registry = registry_fixture()
    manifest = manifest_fixture(registry)
    if damage == "missing":
        manifest["members"].pop()
    elif damage == "duplicate":
        manifest["members"][-1] = copy.deepcopy(manifest["members"][-2])
    elif damage == "extra":
        manifest["members"][-1]["path"] = "raw-old-label.json"
    elif damage == "order":
        manifest["members"].reverse()
    elif damage == "type":
        manifest["members"][0]["type"] = "raw"
    elif damage == "role":
        manifest["role_views"]["scientific-producer"].append("nn/audit/forbidden.json")
    elif damage == "contract":
        manifest["frozen_contract_sha256"] = "b" * 64
    elif damage == "selfhash":
        manifest["version_id"] = "b" * 64
    elif damage == "bytes":
        manifest["members"][0]["byte_size"] = True
    elif damage == "hash":
        manifest["members"][0]["sha256"] = "not a hash"
    elif damage == "epoch":
        registry["models"][0]["epoch"] = 1
        manifest["source_registry_sha256"] = hashlib.sha256(wire(registry)).hexdigest()
    with pytest.raises(ValueError):
        module.validate_manifest(manifest, registry, "a" * 64)


def write_local_fixture(root, registry, manifest):
    root.mkdir(mode=0o700)
    rows = []
    for member in manifest["members"]:
        name = member["path"]
        raw = wire(registry) if name == "source_registry.json" else b"{}\n"
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        target.chmod(0o600)
        directory = target.parent
        while directory != root:
            directory.chmod(0o700)
            directory = directory.parent
        info = target.stat()
        identity = {
            key: getattr(info, key) for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")
        }
        rows.append(
            {
                "path": name,
                "byte_size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                **{stage: identity for stage in ("declared", "before", "after", "closing")},
            }
        )
    return rows


def test_independent_checks_every_new_member_against_local_not_source_identity(tmp_path):
    module = load()
    registry = registry_fixture()
    manifest = manifest_fixture(registry)
    root = tmp_path / "new-content"
    rows = write_local_fixture(root, registry, manifest)
    result = module.audit_local_content(root, manifest, registry, rows, "a" * 64)
    assert result["status"] == "NEW_CONTENT_IDENTITIES_CHECKED_ONLY"
    assert result["new_member_reads"] == 1071
    assert result["old_source_reads"] == 0
    assert result["original_semantics_accepted"] is False
    assert result["consumer_authorized"] is False


def test_symlink_content_root_rejects_before_any_inventory(tmp_path, monkeypatch):
    module = load()
    registry = registry_fixture()
    manifest = manifest_fixture(registry)
    actual = tmp_path / "new-content"
    rows = write_local_fixture(actual, registry, manifest)
    alias = tmp_path / "root-alias"
    alias.symlink_to(actual, target_is_directory=True)

    def forbidden_inventory(*args, **kwargs):
        pytest.fail("symlink target was inventoried before admission")

    monkeypatch.setattr(module.base.os, "scandir", forbidden_inventory)
    with pytest.raises((ValueError, OSError)):
        module.audit_local_content(alias, manifest, registry, rows, "a" * 64)


def target_receipt():
    root = "/Users/Shared/TopoLab-input-versions/p17-m2-local-input-version-v1"
    backup = root + "-independent-backup"
    ref = {
        "path": "/private/tmp/new-public-native-observation.json",
        "sha256": "b" * 64,
        "provenance": "trusted_outer_tool_return",
    }
    coverage = {"covered_paths": [root, backup], "sources_complete": True, "evidence": [ref]}
    return {
        "schema": "topolab.v2.m2-local-target-evidence.v1",
        "execution_identity": "topolab.v2.p17-m2-local-input-version.v1",
        "root": root,
        "backup": backup,
        "started_utc": "2026-10-23T08:00:00Z",
        "finished_utc": "2026-10-23T08:00:10Z",
        "elapsed_seconds": 10,
        "physical": {"no_symlinks": True, "local_filesystem": True, "evidence": [ref]},
        "private_fixture": {
            "path": "/Users/Shared/TopoLab-input-versions/new-public-fixture",
            "owner_uid": 501,
            "expected_owner_uid": 501,
            "directory_mode": 448,
            "file_mode": 384,
            "exclusive_create": True,
            "write_flush_fsync": True,
            "evidence": [ref],
        },
        "provider_coverage": dict(coverage, status="EXCLUDED"),
        "backup_coverage": dict(coverage, status="EXCLUDED_OR_NONMUTATING_READONLY"),
        "custodian": {
            "actor": "new-public-custodian",
            "complete_writer_inventory": True,
            "controlled_writers": ["registered-exporter"],
            "no_uncontrolled_writers": True,
            "lease_plan": "LOCAL_GENERATION_WRITER_EXCLUSION_ONLY",
            "evidence": [dict(ref, provenance="responsible_custodian_statement")],
        },
    }


def test_target_positive_fields_never_substitute_for_independent_raw_review():
    module = load()
    receipt = target_receipt()
    result = module.assess_target_evidence(receipt, receipt["root"], receipt["backup"])
    assert result["status"] == "TARGET_PLAN_EVIDENCE_COMPLETE_PENDING_INDEPENDENT_RAW_REVIEW"
    assert result["gaps"] == []
    assert result["old_source_authorized"] is False
    assert result["formal_roles_authorized"] is False


@pytest.mark.parametrize(
    "damage",
    [
        "samehash-replacement",
        "bytes",
        "missing",
        "extra",
        "symlink",
        "changed-identity",
        "identity-count",
    ],
)
def test_independent_rejects_local_mutation_and_member_drift(tmp_path, damage):
    module = load()
    registry = registry_fixture()
    manifest = manifest_fixture(registry)
    root = tmp_path / "new-content"
    rows = write_local_fixture(root, registry, manifest)
    target = root / manifest["members"][0]["path"]
    if damage == "samehash-replacement":
        old = target.stat()
        target.rename(tmp_path / "preserved-new-file")
        target.write_bytes(b"{}\n")
        module.base.os.utime(target, ns=(old.st_atime_ns, old.st_mtime_ns))
    elif damage == "bytes":
        target.write_bytes(b'{"different":1}\n')
    elif damage == "missing":
        target.unlink()
    elif damage == "extra":
        (root / "raw-old-label.json").write_text("{}\n")
    elif damage == "symlink":
        target.unlink()
        target.symlink_to(root / "models.json")
    elif damage == "changed-identity":
        rows[0]["closing"] = dict(rows[0]["closing"], st_ino=rows[0]["closing"]["st_ino"] + 1)
    elif damage == "identity-count":
        rows.pop()
    with pytest.raises((ValueError, OSError)):
        module.audit_local_content(root, manifest, registry, rows, "a" * 64)


def test_independent_local_short_read_is_not_identity_change(tmp_path, monkeypatch):
    module = load()
    registry = registry_fixture()
    manifest = manifest_fixture(registry)
    root = tmp_path / "new-content"
    rows = write_local_fixture(root, registry, manifest)
    monkeypatch.setattr(module.base.os, "read", lambda *_: b"")
    with pytest.raises(ValueError, match="source read length differs from descriptor size"):
        module.audit_local_content(root, manifest, registry, rows, "a" * 64)


def test_local_audit_refuses_original_root_before_inventory(monkeypatch):
    module = load()
    registry = registry_fixture()
    manifest = manifest_fixture(registry)

    # No original stat/read: the OS boundary must remain untouched.
    def forbidden_inventory(*args, **kwargs):
        pytest.fail("original root was inventoried")

    monkeypatch.setattr(module.base.os, "scandir", forbidden_inventory)
    rows = []
    with pytest.raises(ValueError, match="cannot read original DATA"):
        module.audit_local_content(
            module.base.AUTHORIZED_DATA_ROOT, manifest, registry, rows, "a" * 64
        )


def source_sidecar(count):
    rows = []
    for ordinal in range(count):
        identity = {"st_dev": 1, "st_ino": ordinal + 1, "st_size": 3, "st_mtime_ns": 1234567890}
        rows.append(
            {
                "path": f"new-public-source-{ordinal}.json",
                "byte_size": 3,
                "sha256": "c" * 64,
                **{key: dict(identity) for key in ("declared", "before", "after", "closing")},
            }
        )
    return {
        "schema": "topolab.v2.m2-source-identity-sidecar.v1",
        "execution_identity": "topolab.v2.p17-m2-local-input-version.v1",
        "rows": rows,
    }


@pytest.mark.parametrize("stage,count", [("r0", 40), ("r1", 558)])
def test_complete_cross_author_source_observations(stage, count):
    module = load()
    producer = source_sidecar(count)
    result = module.compare_source_sets(producer, copy.deepcopy(producer), stage)
    assert result == {
        "status": "SOURCE_OBSERVATIONS_MATCHED_ONLY",
        "stage": stage,
        "source_count": count,
        "consumer_authorized": False,
    }


@pytest.mark.parametrize("stage,count", [("r0", 40), ("r1", 558)])
@pytest.mark.parametrize(
    "damage", ["count", "duplicate", "tuple", "hash", "bytes", "identity", "missing"]
)
def test_cross_author_rejects_missing_or_changed_original_observations(stage, count, damage):
    module = load()
    producer = source_sidecar(count)
    independent = copy.deepcopy(producer)
    if damage == "count":
        independent["rows"].pop()
    elif damage == "duplicate":
        independent["rows"][-1] = copy.deepcopy(independent["rows"][0])
    elif damage == "tuple":
        for key in ("declared", "before", "after", "closing"):
            independent["rows"][0][key]["st_ino"] += 1
    elif damage == "hash":
        independent["rows"][0]["sha256"] = "d" * 64
    elif damage == "bytes":
        independent["rows"][0]["byte_size"] = 2
    elif damage == "identity":
        independent["execution_identity"] = "topolab.v2.p17-m2-source-stable-export.v1"
    elif damage == "missing":
        independent["rows"][0]["closing"] = None
    with pytest.raises(ValueError):
        module.compare_source_sets(producer, independent, stage)


@pytest.mark.parametrize(
    "section,field,value",
    [
        ("physical", "no_symlinks", False),
        ("physical", "local_filesystem", None),
        ("physical", "evidence", []),
        ("private_fixture", "owner_uid", None),
        ("private_fixture", "directory_mode", 493),
        ("private_fixture", "exclusive_create", False),
        ("private_fixture", "write_flush_fsync", None),
        ("provider_coverage", "status", "UNKNOWN"),
        ("provider_coverage", "sources_complete", False),
        ("backup_coverage", "status", "UNKNOWN"),
        ("custodian", "actor", None),
        ("custodian", "complete_writer_inventory", None),
        ("custodian", "no_uncontrolled_writers", False),
        ("custodian", "evidence", []),
        ("custodian", "controlled_writers", ["*"]),
    ],
)
def test_target_unknown_or_incomplete_positive_evidence_does_not_admit(section, field, value):
    module = load()
    receipt = target_receipt()
    receipt[section][field] = value
    result = module.assess_target_evidence(receipt, receipt["root"], receipt["backup"])
    assert result["status"] == "NO_LOCAL_ROOT_ADMISSION"
    assert result["gaps"]


@pytest.mark.parametrize("damage", ["overrun", "false-span", "literal-root", "old-identity"])
def test_target_check_requires_bounded_actual_new_receipt(damage):
    module = load()
    receipt = target_receipt()
    if damage == "overrun":
        receipt["elapsed_seconds"] = 601
        receipt["finished_utc"] = "2026-10-23T08:10:01Z"
    elif damage == "false-span":
        receipt["elapsed_seconds"] = 1
    elif damage == "literal-root":
        receipt["root"] += "-another-root"
    elif damage == "old-identity":
        receipt["execution_identity"] = "topolab.v2.p17-m2-source-stable-export.v1"
    result = module.assess_target_evidence(
        receipt, target_receipt()["root"], target_receipt()["backup"]
    )
    assert result["status"] == "NO_LOCAL_ROOT_ADMISSION"


@pytest.mark.parametrize("damage", ["public-root", "public-file", "hardlink"])
def test_new_content_requires_private_ordinary_unaliased_files(tmp_path, damage):
    module = load()
    registry = registry_fixture()
    manifest = manifest_fixture(registry)
    root = tmp_path / "new-content"
    rows = write_local_fixture(root, registry, manifest)
    target = root / manifest["members"][0]["path"]
    if damage == "public-root":
        root.chmod(0o755)
    elif damage == "public-file":
        target.chmod(0o644)
    elif damage == "hardlink":
        module.base.os.link(target, tmp_path / "new-public-link")
    with pytest.raises(ValueError, match="private|hardlink"):
        module.audit_local_content(root, manifest, registry, rows, "a" * 64)


@pytest.mark.parametrize(
    "certificate",
    [
        None,
        {},
        {"status": "READY"},
        {
            "status": "LOCAL_INPUT_VERSION_ACCEPTED",
            "all_six_roles_passed": True,
            "shared_exit_observed": True,
            "filing_exit_observed": True,
            "target_released_after_last_reader": True,
            "consumer_role_authorized": True,
        },
    ],
)
def test_claimed_certificate_never_opens_consumption_without_actual_formal_verifier(certificate):
    module = load()
    with pytest.raises(ValueError, match="FORMAL_LAUNCH_BINDING_INCOMPLETE"):
        module.check_consumption_certificate(certificate, "a" * 64, "b" * 64, "scientific-producer")


def test_p43_uses_content_contract_epoch169_and_rejects101():
    module = load()
    registry = registry_fixture()
    p43 = next(m for m in registry["models"] if m["family"] == "P" and m["seed"] == 43)
    p43["epoch"] = 169
    manifest = manifest_fixture(registry)
    assert module.validate_manifest(manifest, registry, "a" * 64)["member_count"] == 1071
    p43["epoch"] = 101
    manifest = manifest_fixture(registry)
    with pytest.raises(ValueError, match="checkpoint population"):
        module.validate_manifest(manifest, registry, "a" * 64)


def test_extra_member_appearing_during_last_read_rejects(tmp_path, monkeypatch):
    module = load()
    registry = registry_fixture()
    manifest = manifest_fixture(registry)
    root = tmp_path / "new-content"
    rows = write_local_fixture(root, registry, manifest)
    final_inode = (root / "uniform-scalars.json").stat().st_ino
    real_read = module.base.os.read
    injected = False

    def read(fd, maximum):
        nonlocal injected
        result = real_read(fd, maximum)
        if not injected and result and module.base.os.fstat(fd).st_ino == final_inode:
            (root / "unexpected-after-inventory.json").write_text("{}\n")
            injected = True
        return result

    monkeypatch.setattr(module.base.os, "read", read)
    with pytest.raises(ValueError, match="extra or nonregular"):
        module.audit_local_content(root, manifest, registry, rows, "a" * 64)


# Shared new-public graph; the fixture never enters a production source command.
from test_p17_m2_local_input_pipeline import pipeline as pipeline  # noqa: E402


def test_source_buffers_are_released_before_the_next_independent_original_read(pipeline):
    _, _, independent, _, registry, sources, content, _, _, _ = pipeline
    checker = independent.base
    original = checker.OnceReader(sources, 558, 852 * checker.MIB, source_identity_checks=True)
    live = {"count": 0, "peak": 0}

    class ObservedBytes(bytes):
        def __new__(cls, raw):
            result = super().__new__(cls, raw)
            live["count"] += 1
            live["peak"] = max(live["peak"], live["count"])
            return result

        def __del__(self):
            live["count"] -= 1

    class ObservedSource:
        table = original.table
        validation = original.validation

        def read(self, *args, **kwargs):
            assert live["count"] == 0, "previous original raw buffer retained into next read"
            return ObservedBytes(original.read(*args, **kwargs))

    result = checker.audit_exports(
        ObservedSource(), checker.OnceReader(content.root, 1070, 301 * checker.MIB), registry
    )
    assert result["status"] == "PASS_R1_ALL_SOURCE_FIELDS"
    assert len(original.table) == 558
    assert live == {"count": 0, "peak": 1}


def test_actual_target_span_above600_rejects_even_when_rounded_elapsed_is600():
    module = load()
    receipt = target_receipt()
    receipt["finished_utc"] = "2026-10-23T08:10:00.000001Z"
    receipt["elapsed_seconds"] = 600
    result = module.assess_target_evidence(receipt, receipt["root"], receipt["backup"])
    assert result["status"] == "NO_LOCAL_ROOT_ADMISSION"
