"""PUBLIC adapter unit checks; no named role or business source is opened."""

import hashlib
import importlib.util
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import pytest

REPO = Path(__file__).resolve().parents[1]


def subject():
    path = REPO / "scripts/r1_window_public_independent.py"
    raw = path.read_bytes()
    module = ModuleType("declared_r1_window_independent")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    module.MODULE_SOURCE_SHA256 = hashlib.sha256(raw).hexdigest()
    return module


def plan_fixture(module):
    root = module.ROOTS[0]
    return dict(schema="topolab.v2.m2-source-acquisition-plan.v1",
                execution_identity=module.IDENTITY, scope=module.SCOPE, formal_authority=False,
                root=str(root), source_root=str(root) + "-source", content_root=str(root/"content"),
                backup_root=str(root/"backup-content"), source_identity_policy=module.POLICY,
                public_registration=dict(path=str(Path(str(root) + "-evidence")
                                                   / "registration.json"),
                                         sha256="a"*64),
                binding=dict(formal_authority=False, old_original_access=False,
                             target_access=False, B_C=False), content_contract={"declared": True},
                public_source_identity={"B3_DATA_HASH": "b"*64, "CATALOG_HASH": "c"*64},
                contract_sha256="d"*64)


def registration_fixture(module):
    path = REPO / "scripts/p17_m2_source_binding_independent.py"
    spec = importlib.util.spec_from_file_location("declared_public_23_specs", path)
    metadata = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metadata)
    specs = metadata.metadata_specs()
    plan = plan_fixture(module)
    rows = []
    for index, item in enumerate(specs):
        point = dict(st_dev=1, st_ino=index+2, st_size=3, st_mtime_ns=4)
        rows.append(dict(path=item["path"], byte_size=3, sha256="f"*64,
                         **{name: dict(point) for name in module.POINTS}))
    certificate = dict(schema="topolab.r1-window.public-registration.v1",
                       source_root=plan["source_root"], source_observations=rows,
                       content_contract=deepcopy(plan["content_contract"]),
                       public_source_identity=deepcopy(plan["public_source_identity"]))
    return plan, certificate, specs


def test_new_public_namespace_has_six_exact_roots_and_no_formal_grant():
    module = subject()
    plan = plan_fixture(module)
    assert len(module.ROOTS) == 6
    assert module.public_paths(plan)[0] == Path(plan["root"])
    assert module.IDENTITY.endswith(".r1-window-public-20261123.v1")


@pytest.mark.parametrize("damage", ["old-root", "formal-id", "formal-scope", "source",
                                   "content", "backup", "registration", "permission", "policy"])
def test_wrong_namespace_is_rejected_before_filesystem_access(monkeypatch, damage):
    module = subject()
    plan = plan_fixture(module)
    if damage == "old-root":
        plan["root"] = "/private/tmp/topolab-public-staged-input-20261121-a1"
    elif damage == "formal-id":
        plan["execution_identity"] = (
            "topolab.v2.p17-m2-registered-source-acquisition.r1-window-20261123.v1")
    elif damage == "formal-scope":
        plan["scope"] = "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
    elif damage in ("source", "content", "backup"):
        plan[damage + "_root"] = "/Users/keith1117/Documents/TopoLab-data"
    elif damage == "registration":
        plan["public_registration"]["path"] = "/declared/old-certificate.json"
    elif damage == "permission":
        plan["binding"]["old_original_access"] = True
    else:
        plan["source_identity_policy"] = None
    monkeypatch.setattr(module, "directory", lambda *_: pytest.fail("premature source stat"))
    with pytest.raises(ValueError):
        module.public_paths(plan)


def test_independent_registration_uses_native_specs_and_complete_equal_four_points():
    module = subject()
    plan, certificate, specs = registration_fixture(module)
    anchors = module.registration_bindings(certificate, specs, plan)
    assert list(anchors) == [spec["path"] for spec in specs] and len(anchors) == 23
    assert all(anchor["byte_size"] == 3 and anchor["declared"]["st_size"] == 3
               for anchor in anchors.values())


@pytest.mark.parametrize("damage", ["count", "order", "hash", "size-bool", "point-bool",
                                   "closing", "mtime", "source", "context", "extra"])
def test_registration_rejects_missing_or_mixed_preread_facts(damage):
    module = subject()
    plan, certificate, specs = registration_fixture(module)
    rows = certificate["source_observations"]
    if damage == "count":
        rows.pop()
    elif damage == "order":
        rows[0], rows[1] = rows[1], rows[0]
    elif damage == "hash":
        rows[0]["sha256"] = "not-a-hash"
    elif damage == "size-bool":
        rows[0]["byte_size"] = True
    elif damage == "point-bool":
        rows[0]["declared"]["st_dev"] = True
    elif damage == "closing":
        rows[0].pop("closing")
    elif damage == "mtime":
        rows[0]["after"]["st_mtime_ns"] += 1
    elif damage == "source":
        certificate["source_root"] = "/declared/original"
    elif damage == "context":
        certificate["content_contract"] = {"different": True}
    else:
        rows[0]["extra"] = "not a native point"
    with pytest.raises(ValueError):
        module.registration_bindings(certificate, specs, plan)


def test_public_metadata_read_requires_private_owned_independent_file_and_real_eof(tmp_path):
    module = subject()
    folder = tmp_path / "metadata"
    folder.mkdir(mode=0o700)
    path = folder / "receipt.json"
    path.write_bytes(b"{}\n")
    path.chmod(0o600)
    assert module.private_bytes(path) == b"{}\n"
    path.chmod(0o644)
    with pytest.raises(ValueError):
        module.private_bytes(path)
    path.chmod(0o600)
    peer = folder / "another.json"
    module.os.link(path, peer)
    with pytest.raises(ValueError):
        module.private_bytes(path)


def test_public_metadata_and_ancestor_symlinks_cannot_redirect_reads(tmp_path):
    module = subject()
    folder = tmp_path / "metadata"
    folder.mkdir(mode=0o700)
    source = folder / "receipt.json"
    source.write_bytes(b"{}\n")
    source.chmod(0o600)
    linked = folder / "link.json"
    linked.symlink_to(source)
    with pytest.raises(OSError):
        module.private_bytes(linked)
    parent_link = tmp_path / "parent-link"
    parent_link.symlink_to(folder, target_is_directory=True)
    with pytest.raises(OSError):
        module.private_bytes(parent_link / source.name)


@pytest.mark.parametrize("role", ["independent-r0", "independent-r1"])
def test_native_payload_wrapper_reads_only_fixed_public_controls_then_calls_same_api(
    monkeypatch, role
):
    module = subject()
    plan = plan_fixture(module)
    root = Path(plan["root"])
    controls = {root/"registry.json": {"declared": "registry"},
                root/"r0-source-rows.json": [{"declared": "R0 raw rows"}],
                root/"r1-source-rows.json": [{"declared": "R1 raw rows"}],
                root/"closed.json": {"declared": "version"}}
    reads, calls = [], []

    def read(path, **_kwargs):
        reads.append(path)
        return module.canonical(controls[path])

    def checked(*args, **kwargs):
        calls.append((args, kwargs))
        return {"status": "DECLARED_UNIT_API_WIRING_ONLY"}

    monkeypatch.setattr(module, "private_bytes", read)
    monkeypatch.setattr(module, "standalone_accepted_registry",
                        lambda _plan: controls[root/"registry.json"])
    monkeypatch.setattr(module, role.replace("-", "_"), checked)
    result = module.verify_public_role(plan, role)
    assert result["status"] == "DECLARED_UNIT_API_WIRING_ONLY"
    assert calls[0][1] == {"plan": plan} and calls[0][0][0] == Path(plan["source_root"])
    assert (root/"registry.json" in reads) is (role == "independent-r0")
    assert not any(path.is_relative_to(Path(plan["source_root"])) for path in reads)


def test_wrapper_rejects_exporter_or_formal_roles_before_io(monkeypatch):
    module = subject()
    monkeypatch.setattr(module, "private_bytes", lambda *_: pytest.fail("premature IO"))
    with pytest.raises(ValueError):
        module.verify_public_role(plan_fixture(module), "exporter-r1")


def test_old_registration_sibling_under_nonprivate_tmp_is_rejected_without_open(monkeypatch):
    module = subject()
    plan = plan_fixture(module)
    plan["public_registration"]["path"] = plan["root"] + "-source-registration.json"
    monkeypatch.setattr(module, "private_bytes", lambda *_: pytest.fail("old sibling opened"))
    with pytest.raises(ValueError, match="registration reference"):
        module.verify_public_role(plan, "independent-r0")


def test_accepted_r1_registry_is_the_original_object_and_is_not_opened_again(monkeypatch):
    module = subject()
    plan = plan_fixture(module)
    root = Path(plan["root"])
    accepted = {"declared": "already native-audited same-buffer registry"}
    seen = []

    def read(path, **_kwargs):
        assert path != root/"registry.json"
        return module.canonical({"declared": str(path)})

    def checked(*args, **_kwargs):
        seen.append(args[2])
        return {"status": "DECLARED_UNIT_API_WIRING_ONLY"}

    monkeypatch.setattr(module, "private_bytes", read)
    monkeypatch.setattr(module, "standalone_accepted_registry",
                        lambda *_: pytest.fail("duplicate R0 gate/read"))
    monkeypatch.setattr(module, "independent_r1", checked)
    module.verify_public_role(plan, "independent-r1", accepted_registry=accepted)
    assert seen == [accepted] and seen[0] is accepted


def test_standalone_r1_must_cross_the_accepted_r0_gate_before_any_payload_control(monkeypatch):
    module = subject()
    plan = plan_fixture(module)
    monkeypatch.setattr(module, "private_bytes", lambda *_: pytest.fail("unbound registry read"))

    def refused(_plan):
        raise ValueError("declared missing independent R0 acceptance")

    monkeypatch.setattr(module, "standalone_accepted_registry", refused)
    with pytest.raises(ValueError, match="R0 acceptance"):
        module.verify_public_role(plan, "independent-r1")


def test_r0_cannot_replace_its_independent_build_with_an_accepted_object(monkeypatch):
    module = subject()
    monkeypatch.setattr(module, "private_bytes", lambda *_: pytest.fail("premature read"))
    with pytest.raises(ValueError, match="only an R1"):
        module.verify_public_role(plan_fixture(module), "independent-r0", accepted_registry={})
