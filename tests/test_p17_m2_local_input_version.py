"""Public files only; the local writer never receives an original source path."""

import importlib.util
import stat
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def load():
    spec = importlib.util.spec_from_file_location(
        "local_version_subject", REPO / "scripts/p17_m2_local_input_version.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def registry():
    return {
        "schema": "topolab.v2.m2-input-source-registry.v1", "metadata": [],
        "models": [{"family": family, "seed": seed}
                   for family in ("C", "P", "W", "S") for seed in (17, 29, 43)],
        "labels": [{"case_id": "tlcase-v1-" + f"{i:064x}"} for i in range(1, 529)],
        "scalars": [],
    }


def test_new_content_is_private_exclusive_and_rejects_unlisted_member(tmp_path):
    local = load()
    root = tmp_path / "content"
    content = local.LocalContent(root, registry(), "a" * 64)
    content.write("models.json", b'{"public":true}\n')
    assert stat.S_IMODE(root.stat().st_mode) == 0o700
    assert stat.S_IMODE((root / "models.json").stat().st_mode) == 0o600
    with pytest.raises(ValueError, match="duplicate"):
        content.write("models.json", b'{}\n')
    other = local.LocalContent(tmp_path / "other", registry(), "a" * 64)
    with pytest.raises(ValueError, match="whitelist"):
        other.write("raw-old-label.json", b'{}\n')
    assert not (root / "raw-old-label.json").exists()


def public_content(local, root):
    content = local.LocalContent(root, registry(), "a" * 64)
    for path in content.allowed:
        raw = content.registry_raw if path == "source_registry.json" else b'{"public":true}\n'
        content.write(path, raw)
    return content


def test_complete_manifest_binds_exact_members_and_proposed_views(tmp_path):
    local = load()
    content = public_content(local, tmp_path / "content")
    result = content.finish()
    manifest = result["manifest"]
    assert len(manifest["members"]) == 1071
    assert len(result["local_identity_rows"]) == 1071
    assert set(manifest) == {"schema", "frozen_contract_sha256", "content_scope_sha256",
                             "source_registry_sha256", "members", "role_views"}
    assert len(manifest["role_views"]["scientific-producer"]) == 541
    assert len(manifest["role_views"]["scientific-auditor"]) == 1069
    assert manifest["role_views"]["reference-compatibility"] == ["uniform-scalars.json"]
    assert len(result["version_id"]) == 64
    assert "export_manifest.json" not in {m["path"] for m in manifest["members"]}
    with pytest.raises(ValueError, match="sealed"):
        content.write("models.json", b'{}\n')


@pytest.mark.parametrize("damage", ["missing", "bytes", "same_hash_replacement", "extra"])
def test_manifest_cannot_seal_missing_changed_replaced_or_extra_new_content(tmp_path, damage):
    local = load()
    content = public_content(local, tmp_path / "content")
    target = content.root / "models.json"
    if damage == "missing":
        target.unlink()
    elif damage == "bytes":
        target.write_bytes(b'{"public":false}\n')
    elif damage == "same_hash_replacement":
        replacement = content.root / "temporary-new-replacement"
        replacement.write_bytes(target.read_bytes())
        replacement.replace(target)
    else:
        (content.root / "forbidden.json").write_bytes(b'{}\n')
    with pytest.raises((ValueError, OSError)):
        content.finish()


def test_first_write_failure_closes_generation_without_erasing_prefix(tmp_path):
    local = load()
    content = local.LocalContent(tmp_path / "content", registry(), "a" * 64)
    content.write("models.json", b'{}\n')
    with pytest.raises(ValueError, match="byte cap"):
        content.write("uniform-scalars.json", b"x" * 65537)
    with pytest.raises(ValueError, match="STOP_NO_RETRY"):
        content.write("source_registry.json", content.registry_raw)
    with pytest.raises(ValueError, match="STOP_NO_RETRY"):
        content.finish()
    assert (content.root / "models.json").read_bytes() == b'{}\n'
    assert set(content.rows) == {"models.json"}


@pytest.mark.parametrize("damage", ["root_symlink", "child_symlink", "hardlink"])
def test_sealing_refuses_links_before_following_outside_new_content(tmp_path, damage):
    local = load()
    content = public_content(local, tmp_path / "content")
    outside = tmp_path / "unlisted-public"
    if damage == "root_symlink":
        content.root.rename(outside)
        content.root.symlink_to(outside, target_is_directory=True)
    elif damage == "child_symlink":
        (content.root / "nn").rename(outside)
        (content.root / "nn").symlink_to(outside, target_is_directory=True)
    else:
        outside.hardlink_to(content.root / "models.json")
    with pytest.raises((ValueError, OSError)):
        content.finish()


@pytest.mark.parametrize("replacement", ["symlink", "directory"])
def test_changed_root_is_rejected_before_any_inventory(tmp_path, monkeypatch, replacement):
    local = load()
    content = public_content(local, tmp_path / "content")
    retained = tmp_path / "retained-new-fixture"
    content.root.rename(retained)
    if replacement == "symlink":
        content.root.symlink_to(retained, target_is_directory=True)
    else:
        content.root.mkdir(mode=0o700)

    def forbidden_inventory(*args, **kwargs):
        raise AssertionError("must reject changed root before enumerating any member")

    monkeypatch.setattr(local.os, "scandir", forbidden_inventory)
    with pytest.raises((ValueError, OSError)):
        content.finish()


@pytest.mark.parametrize("operation", ["write", "finish"])
def test_public_generation_root_cannot_write_or_seal(tmp_path, operation):
    local = load()
    if operation == "finish":
        content = public_content(local, tmp_path / "content")
    else:
        content = local.LocalContent(tmp_path / "content", registry(), "a" * 64)
    content.root.chmod(0o755)
    with pytest.raises(ValueError, match="private"):
        if operation == "write":
            content.write("models.json", b'{}\n')
        else:
            content.finish()


def test_original_namespace_is_rejected_before_any_filesystem_access(monkeypatch):
    local = load()

    def forbidden_open(*args, **kwargs):
        raise AssertionError("no original parent may be opened")

    monkeypatch.setattr(local.os, "open", forbidden_open)
    with pytest.raises(ValueError, match="original"):
        local.LocalContent(Path("/Users/keith1117/Documents/TopoLab-data/uncreated"),
                           registry(), "a" * 64)


def test_transcriber_releases_each_source_buffer_before_reading_next(tmp_path, monkeypatch):
    local = load()
    producer = local.exporter()
    spec = importlib.util.spec_from_file_location(
        "public_pipeline_fixture", Path(__file__).with_name("test_p17_m2_local_input_pipeline.py"))
    assert spec and spec.loader
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    checker = fixture.load("p17_m2_input_export_independent")
    root = tmp_path / "public-source"
    contract = fixture.complete_sources(root, checker, monkeypatch)
    source_registry = producer.register(producer.Reader(root), contract)

    class SourceBuffer(bytes):
        live = 0

        def __new__(cls, raw):
            result = super().__new__(cls, raw)
            cls.live += 1
            return result

        def __del__(self):
            type(self).live -= 1

    class BoundedReader(producer.Reader):
        def read(self, *args, **kwargs):
            assert SourceBuffer.live == 0, "previous original buffer retained across reads"
            return SourceBuffer(super().read(*args, **kwargs))

    reader = BoundedReader(root)
    producer.export(reader, source_registry, contract, tmp_path / "new-public-exports")
    assert SourceBuffer.live == 0 and len(reader.rows) == 558
