"""A new finite window cannot reopen the expired strict binding cohort."""

import json
import time
from types import SimpleNamespace

import pytest
from test_p17_m2_source_binding import binding_module

NEW_ID = "topolab.v2.p17-source-binding-window2.20261104.v1"


def window2_public(module, tmp_path, monkeypatch):
    authority = json.loads(module.COORDINATED_AUTHORITY.read_bytes())
    root = tmp_path / "topolab-public-coordinated-binding-window2-unit"
    authority.update(execution_identity=NEW_ID, formal_root_name="binding-formal-v3")
    authority["preparation_proofs"]["public_native_root"] = str(root)
    authority["window2"] = {"core_seconds": 1800, "post_result_seconds": 1800}
    path = tmp_path / "new-public-window2-authority.json"
    path.write_bytes(module.canonical(authority))
    monkeypatch.setattr(module, "WINDOW2_AUTHORITY", path, raising=False)
    monkeypatch.setattr(module, "window2_preparation_readiness", lambda authority: {},
                        raising=False)
    active = module.runtime()
    monkeypatch.setattr(module, "runtime", lambda: dict(
        active, isolated=1, cwd=str(module.REPO), threads=module.THREADS))
    result = module.prepare_public(root, attempt=2, window2=True)
    return module.load_plan(root / "plan.json", result["plan_sha256"])


def test_new_window_has_distinct_identity_and_keeps_actual_attempt_two(tmp_path, monkeypatch):
    module = binding_module()
    plan = window2_public(module, tmp_path, monkeypatch)
    assert plan["context"]["execution_identity"] == NEW_ID
    assert plan["context"]["attempt"] == 2
    assert plan["actor_window_seconds"] == 1800
    assert plan["deadline_unix_ns"] - plan["started_unix_ns"] == 1800 * 10**9
    assert len(plan["context"]["source_tree"]) == 19
    assert len(module.source_freeze(2)) == 18
    assert len(module.source_freeze()) == 15
    module.admit_plan(plan, "producer-availability")
    plan["actor_window_seconds"] = 3600
    with pytest.raises(ValueError, match="immutable dispatch window"):
        module.admit_plan(plan, "producer-availability")


def test_result_suffix_uses_actual_closeout_return_without_rounding(monkeypatch):
    module = binding_module()
    core = {"context": {"execution_identity": NEW_ID, "attempt": 2,
                        "scope": module.PUBLIC_SCOPE},
            "deadline_unix_ns": 1800 * 10**9}
    monkeypatch.setattr(module, "accepted_role", lambda *args: ({"T1": 100.125}, {}, []))
    module.check_metadata_suffix(core, 1600125000000)
    with pytest.raises(ValueError, match="complete fixed metadata audit suffix"):
        module.check_metadata_suffix(core, 1600125000001)
    monkeypatch.setattr(module.time, "time_ns", lambda: 1900125000001)
    monkeypatch.setattr(module, "read_metadata", lambda *args, **kw: pytest.fail(
        "late finalization must reject before reading any bundle"))
    with pytest.raises(ValueError, match="fixed result window"):
        module.finalize_result(core)


@pytest.mark.parametrize("kind", ["directory", "file", "symlink"])
def test_old_cohort_presence_refuses_new_target_without_reuse(tmp_path, kind):
    module = binding_module()
    old = tmp_path / "binding-formal-v2"
    if kind == "directory":
        old.mkdir()
    elif kind == "file":
        old.write_bytes(b"public fixture")
    else:
        old.symlink_to(tmp_path / "absent-public-fixture")
    authority = {"evidence_root": str(tmp_path), "formal_root_name": "binding-formal-v3"}
    with pytest.raises(ValueError, match="old formal2 cohort"):
        module.create_formal_root(authority, 2, window2=True)
    assert not (tmp_path / "binding-formal-v3").exists()


def test_remaining_cohort_can_be_created_once_only(tmp_path):
    module = binding_module()
    authority = {"evidence_root": str(tmp_path), "formal_root_name": "binding-formal-v3"}
    root = module.create_formal_root(authority, 2, window2=True)
    assert root == tmp_path / "binding-formal-v3" and root.is_dir()
    with pytest.raises(FileExistsError):
        module.create_formal_root(authority, 2, window2=True)


@pytest.mark.parametrize("new_identity", [False, True])
def test_resource_pending_records_selected_identity_before_interpreter(
    tmp_path, monkeypatch, new_identity,
):
    module = binding_module()
    module.load("p17_m2_homotopy")
    resource = module.load("p17_m2_resource_control")
    original = resource.atomic_new

    def pending_only(path, value):
        original(path, value)
        raise RuntimeError("public stop before interpreter")

    monkeypatch.setattr(resource, "atomic_new", pending_only)
    role = "binding-producer"
    argv = [module.runtime()["python"], "-I", str(module.REPO / "scripts/p17_m2_source_binding.py"),
            "payload", "--plan", str(tmp_path / "plan.json"), "--plan-sha", "3" * 64,
            "--role", role]
    kwargs = {"measurement_execution_identity": NEW_ID} if new_identity else {}
    with pytest.raises(RuntimeError, match="before interpreter"):
        resource.invoke(tmp_path, role, argv, timeout=290,
                        measurement_scope=module.PUBLIC_SCOPE, **kwargs)
    pending = json.loads((tmp_path / role / "pending.json").read_bytes())
    assert pending["measurement_execution_identity"] == (
        NEW_ID if new_identity else module.IDENTITY)


@pytest.mark.parametrize("identity,scope", [("unknown", "PUBLIC_STRICT_BINDING_REGISTRATION_ONLY"),
                                           (NEW_ID, None)])
def test_resource_identity_cannot_grant_an_unregistered_scope(tmp_path, identity, scope):
    module = binding_module()
    module.load("p17_m2_homotopy")
    resource = module.load("p17_m2_resource_control")
    with pytest.raises(ValueError, match="measurement identity"):
        resource.invoke(tmp_path, "binding-producer", ["unused"], timeout=1,
                        measurement_scope=scope, measurement_execution_identity=identity)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("fault", ["identity", "float_window"])
def test_wrong_selected_profile_rejects_before_budget_IO(monkeypatch, fault):
    module = binding_module()
    authority = json.loads(module.WINDOW2_AUTHORITY.read_bytes())
    if fault == "identity":
        authority["execution_identity"] = module.IDENTITY
    else:
        authority["window2"]["core_seconds"] = 1800.0
    monkeypatch.setattr(module, "read_metadata", lambda *a, **kw: pytest.fail(
        "wrong profile must reject before metadata IO"))
    with pytest.raises(ValueError, match="registered new window identity"):
        module.window2_preparation_readiness(authority)


def test_new_window_cannot_create_an_attempt_one_target(tmp_path, monkeypatch):
    module = binding_module()
    active = module.runtime()
    monkeypatch.setattr(module, "runtime", lambda: dict(
        active, isolated=1, cwd=str(module.REPO), threads=module.THREADS))
    root = tmp_path / "topolab-public-strict-binding-invalid-window"
    with pytest.raises(ValueError, match="sole remaining actual attempt2"):
        module.prepare_public(root, attempt=1, window2=True)
    assert not root.exists()
    assert not root.with_name(root.name + "-source").exists()


def test_metadata_dispatch_cannot_borrow_a_different_policy(tmp_path, monkeypatch):
    module = binding_module()
    root = tmp_path / "topolab-public-coordinated-binding-mixed-policy"
    now = time.time_ns()
    context = {"execution_identity": NEW_ID, "attempt": 2, "scope": module.PUBLIC_SCOPE,
               "source_root": str(root) + "-source",
               "authority_sha256": module.sha(module.WINDOW2_AUTHORITY.read_bytes()),
               "source_tree": module.source_freeze(2, window2=True),
               "actors": {"producer": "/root", "independent": "/root/binding_route_independent_v1"}}
    core = {"root": str(root), "context": context, "deadline_unix_ns": now + 1800 * 10**9}
    bundle = {"plan": core}
    metadata_context = dict(context, execution_identity=module.IDENTITY,
        scope=module.METADATA_SCOPE, source_root=str(root),
        authority_sha256=module.sha(module.COORDINATED_AUTHORITY.read_bytes()),
        source_tree=module.source_freeze(2))
    runtime = dict(module.runtime(), isolated=1, cwd=str(module.REPO), threads=module.THREADS)
    meta_root, role = str(root) + "-certificate-audit", module.METADATA_ROLE
    plan = {"schema": module.METADATA_SCHEMA, "root": meta_root, "context": metadata_context,
            "runtime": runtime, "role_order": [role], "roles": {role: {
                "author": context["actors"]["independent"], "FULL": 120, "timeout": 110,
                "argv": module.role_argv(meta_root, "payload", "@PLAN_SHA256@", role,
                                         runtime["python"])}},
            "started_unix_ns": now, "deadline_unix_ns": now + 300 * 10**9,
            "actor_activation_UTC_seconds": now / 10**9, "actor_window_seconds": 300,
            "bundle": {"path": str(root / "certificate-bundle.json"),
                       "sha256": module.sha(module.canonical(bundle))},
            "entry": {"scope": module.METADATA_SCOPE, "old_original_access": False,
                      "core_plan_sha256": module.sha(module.canonical(core))},
            "coordination": json.loads(module.COORDINATED_AUTHORITY.read_bytes())["coordination"]}
    monkeypatch.setattr(module, "runtime", lambda: runtime)
    monkeypatch.setattr(module, "read_metadata", lambda *a, **kw: (
        bundle, module.canonical(bundle)))
    monkeypatch.setattr(module, "replay_bundle", lambda value: {})
    monkeypatch.setattr(module, "accepted_role", lambda *a: (
        {"T1": (now // 10**6 - 1000) / 1000}, {}, []))
    with pytest.raises(ValueError, match="metadata.*(context|policy|identity)"):
        module.admit_metadata_plan(plan, role)


@pytest.mark.parametrize("field", [None, "execution_identity", "attempt", "authority_sha256",
                                    "source_tree", "actors"])
def test_result_envelope_requires_auditor_policy_equal_to_core(monkeypatch, field):
    module = binding_module()
    core = {"root": "/private/tmp/topolab-public-coordinated-binding-policy-unit", "context": {
        "execution_identity": NEW_ID, "attempt": 2, "scope": module.PUBLIC_SCOPE,
        "source_root": "/private/tmp/topolab-public-coordinated-binding-policy-unit-source",
        "authority_sha256": "3" * 64, "source_tree": {"public.py": "4" * 64},
        "actors": {"producer": "/root", "independent": "/root/binding_route_independent_v1"}}}
    context = dict(core["context"], scope=module.METADATA_SCOPE, source_root=core["root"])
    if field:
        context[field] = {"execution_identity": module.IDENTITY, "attempt": 1,
                          "authority_sha256": "5" * 64, "source_tree": {}, "actors": {}}[field]
    bundle, certificate = {"plan": core}, {"public_fixture": True}
    plan = {"context": context, "bundle": {"sha256": module.sha(module.canonical(bundle))}}
    proof = {"T1": 100.125, "full_role_evidence_accepted": True}
    native = SimpleNamespace(audit_role=lambda *a: proof)
    base = SimpleNamespace(evidence_json=lambda *a, **kw: {
        "inner_evidence": {"log": module.canonical(certificate)}})
    monkeypatch.setattr(module, "load", lambda name: native if name.endswith("_native") else base)
    monkeypatch.setattr(module, "replay_bundle", lambda value: certificate)
    envelope = {"schema": "topolab.v2.m2-strict-source-binding.accepted-result.v1",
                "core_bundle": bundle, "metadata_plan": plan, "metadata_evidence": {},
                "metadata_events": []}
    if field:
        with pytest.raises(ValueError, match="metadata.*(context|policy|identity)"):
            module.verify_result_envelope(envelope)
    else:
        assert module.verify_result_envelope(envelope) == (certificate, proof)
