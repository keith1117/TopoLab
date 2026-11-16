"""New metadata dispatch only; no native role or Original/source/target IO."""

import json
import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
RECOVERY = "topolab.v2.p17-binding-certificate-recovery.20261116.v1"


def module(name):
    path = ROOT / "scripts" / (name + ".py")
    value = types.ModuleType(name)
    value.__file__ = str(path)
    sys.modules[name] = value
    exec(compile(path.read_bytes(), str(path), "exec"), value.__dict__)
    return value


def test_new_metadata_role_has_new_actor_and_neutral_literal_argv():
    native = module("p17_m2_source_binding_native")
    plan = {
        "schema": native.METADATA_SCHEMA,
        "context": {"execution_identity": RECOVERY, "attempt": 1,
                    "scope": native.RECOVERY_SCOPE},
        "runtime": {"python": "/public/python", "cwd": str(ROOT)},
        "root": "/public/new-metadata",
    }
    assert native.execution_profile(plan) == (RECOVERY, 300)
    caps, window, scopes, authors = native.role_profile(plan)
    assert caps == {"binding-certificate-auditor": 120}
    assert window == 300
    assert scopes == (native.RECOVERY_SCOPE,)
    assert authors == {"binding-certificate-auditor": "/root/full60_independent"}
    argv = native.argv_for(plan, "supervise", "binding-certificate-auditor")
    assert argv[2] == str(ROOT / "scripts/binding_recovery_full60_20261116.py")
    assert native.IDENTITY == "topolab.v2.p17-source-binding-and-conditional-repair.20261103.v1"


def test_core_command_builder_uses_same_new_metadata_entry_without_old_authority():
    core = module("p17_m2_source_binding")
    argv = core.role_argv("/public/new-metadata", "payload", "a" * 64,
                          "binding-certificate-auditor", "/public/python",
                          execution_identity=RECOVERY)
    assert argv == ["/public/python", "-I",
                    str(ROOT / "scripts/binding_recovery_full60_20261116.py"), "payload",
                    "--plan", "/public/new-metadata/plan.json", "--plan-sha", "a" * 64,
                    "--role", "binding-certificate-auditor"]


def test_captured_core_replays_from_new_buffer_without_following_historical_path(
    tmp_path, monkeypatch
):
    fixture_path = ROOT / "tests/test_p17_m2_source_binding_recovery.py"
    fixture = types.ModuleType("new_metadata_core_fixture")
    fixture.__file__ = str(fixture_path)
    exec(compile(fixture_path.read_bytes(), str(fixture_path), "exec"), fixture.__dict__)
    _, bundle = fixture.captured_bundle(tmp_path)
    subject = module("p17_m2_source_binding_recovery")
    new_capture = tmp_path / "metadata-availability-capture/public-core.json"
    logical = str(Path(bundle["plan"]["root"]) / "certificate-bundle.json")
    pin = {"path": str(new_capture), "historical_bundle_path": logical,
           "sha256": subject.sha(subject.canonical(bundle)),
           "context": bundle["plan"]["context"]}
    monkeypatch.setattr(subject, "IDENTITY", RECOVERY)
    monkeypatch.setattr(subject, "FULL60_EVIDENCE", tmp_path)
    monkeypatch.setattr(subject, "CONTINUATION_INPUT",
                        "topolab.v2.p17-m2-registered-source-acquisition.20261116.v1")
    monkeypatch.setattr(subject, "authority", lambda: {"captured_cores": {"public": pin}})
    assert subject.replay_core(bundle, "public") == bundle["certificate"]
    assert not new_capture.exists()
    pin["historical_bundle_path"] = str(tmp_path / "wrong-old-logical-path")
    with pytest.raises(ValueError, match="captured successful core/context pin"):
        subject.replay_core(bundle, "public")


@pytest.mark.parametrize("identity,scope,entry,role,root_flag", [
    (RECOVERY, "STRICT_BINDING_CERTIFICATE_RECOVERY_METADATA_ONLY",
     "binding_recovery_full60_20261116.py", "binding-certificate-auditor", "--plan"),
    ("topolab.v2.p17-m2-registered-source-acquisition.20261116.v1",
     "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY",
     "input_control_full60_20261116.py", "exporter-r0", "--root"),
])
def test_new_measurement_identity_passes_literal_gate_before_finite_cap_refusal(
    tmp_path, identity, scope, entry, role, root_flag
):
    module("p17_m2_homotopy")
    resource = module("p17_m2_resource_control")
    output = tmp_path / "never-created"
    root = ("/Users/keith1117/Documents/TopoLab-data/container-full60-input-admission-20261116/"
            "metadata-public-a1/plan.json" if root_flag == "--plan" else
            "/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-local-input-version-20261116-full60-a1")
    argv = [sys.executable, "-I", str(ROOT / "scripts" / entry), "payload", root_flag,
            root, "--plan-sha", "a" * 64, "--role", role]
    with pytest.raises(ValueError, match="finite registered public command/caps"):
        resource.invoke(output, role, argv, timeout=0,
                        measurement_scope=scope, measurement_execution_identity=identity)
    assert not output.exists()


def test_neutral_metadata_entry_executes_source_despite_valid_old_bytecode(tmp_path, monkeypatch):
    import importlib.machinery
    import os
    import py_compile

    entry = module("binding_recovery_full60_20261116")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    (tmp_path / ".venv/lib/python3.12/site-packages").mkdir(parents=True)
    (scripts / "full60_input_loader.py").write_bytes(
        (ROOT / "scripts/full60_input_loader.py").read_bytes())
    path = scripts / "p17_m2_input_continuation.py"
    template = (
        "from types import SimpleNamespace\n"
        "FULL60_INPUT='topolab.v2.p17-m2-registered-source-acquisition.20261116.v1'\n"
        "FULL60_RECOVERY='topolab.v2.p17-binding-certificate-recovery.20261116.v1'\n"
        "def profile(kind, identity):\n"
        " return SimpleNamespace(IDENTITY=FULL60_RECOVERY, marker='%s', "
        "enable_new_metadata_mode=lambda:None)\n"
    )
    path.write_text(template % "OLD")
    original = path.stat()
    py_compile.compile(str(path), doraise=True)
    path.write_text(template % "NEW")
    os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
    (scripts / "binding_recovery_full60_20261116.py").write_bytes(
        (ROOT / "scripts/binding_recovery_full60_20261116.py").read_bytes())
    monkeypatch.setattr(entry, "__file__", str(scripts / "binding_recovery_full60_20261116.py"))
    get_code, no_bytecode = importlib.machinery.SourceFileLoader.get_code, sys.dont_write_bytecode
    old_path = list(sys.path)
    try:
        assert entry.bootstrap(require_locked_environment=False).marker == "NEW"
    finally:
        importlib.machinery.SourceFileLoader.get_code = get_code
        sys.dont_write_bytecode = no_bytecode
        sys.path[:] = old_path


def test_new_metadata_namespace_is_private_and_does_not_change_old_default(monkeypatch):
    old_core = module("p17_m2_source_binding")
    subject = module("p17_m2_source_binding_recovery")
    monkeypatch.setattr(subject, "CONTINUATION_INPUT",
                        "topolab.v2.p17-m2-registered-source-acquisition.20261116.v1")
    monkeypatch.setattr(subject, "IDENTITY", RECOVERY)
    core = subject.enable_new_metadata_mode()
    allowed = (subject.FULL60_EVIDENCE / "metadata-availability-capture/public-core.json")
    core.metadata_path_guard(allowed)
    assert core is not old_core
    with pytest.raises(ValueError, match="not NEW metadata"):
        old_core.metadata_path_guard(allowed)
    with pytest.raises(ValueError, match="not NEW metadata"):
        core.metadata_path_guard(Path("/Users/keith1117/Library/never-opened"))
    backup = Path(str(subject.FULL60_EVIDENCE) + "-backup")
    for name in ("public-metadata-certificate-a1.json", "formal-metadata-certificate-a1.json"):
        core.metadata_path_guard(backup / name)
    for path in (backup / "other.json", backup / "nested/public-metadata-certificate-a1.json"):
        with pytest.raises(ValueError, match="not NEW metadata"):
            core.metadata_path_guard(path)


@pytest.mark.parametrize("role", ["public-consumer", "reader-ack"])
def test_new_reader_metadata_measurement_keeps_exact_reader_role_arguments(tmp_path, role):
    module("p17_m2_homotopy")
    resource = module("p17_m2_resource_control")
    argv = [sys.executable, "-I", str(ROOT / "scripts/input_control_full60_20261116.py"),
            "payload", "--root",
            "/private/tmp/topolab-public-full60-source-acquisition-20261116-a1",
            "--plan-sha", "a" * 64,
            "--role", role, "--reader-role", "scientific-auditor"]
    with pytest.raises(ValueError, match="finite registered public command/caps"):
        resource.invoke(tmp_path / "not-created", role, argv, timeout=0,
                        measurement_scope="FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY",
                        measurement_execution_identity=
                        "topolab.v2.p17-m2-registered-source-acquisition.20261116.v1")
    argv[-1] = "unregistered-reader"
    with pytest.raises(ValueError, match="exact neutral payload/scope/role"):
        resource.invoke(tmp_path / "not-created", role, argv, timeout=0,
                        measurement_scope="FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY",
                        measurement_execution_identity=
                        "topolab.v2.p17-m2-registered-source-acquisition.20261116.v1")
    assert not (tmp_path / "not-created").exists()


def component_reviews(subject):
    partition_path = "docs/planning/full60_input_cross_review_partition.json"
    partition_raw = (ROOT / partition_path).read_bytes()
    partition = json.loads(partition_raw)
    tree = {path: subject.sha((ROOT / path).read_bytes()) for path in partition["members"]}
    policy = subject.authority()
    captures = {}
    for slot in ("standards", "spec"):
        author = policy["review_authors"][slot]
        report = {"schema": "topolab.NEW-full60-input-component-cross-review.v1",
                  "execution_identity": RECOVERY, "author": author,
                  "kind": "COMPONENT_CROSS_REVIEW", "status": "PASS_COMPONENT_CROSS_REVIEW",
                  "axes": ["standards", "spec"], "open_findings": [],
                  "reviewed_source_tree": tree,
                  "reviewed_files": {path: tree[path] for path, item in partition["members"].items()
                                     if item["reviewer"] == author},
                  "partition_sha256": subject.sha(partition_raw)}
        raw = subject.canonical(report)
        captures[slot] = {"reference": {"path": policy["review_paths"][slot],
                                        "sha256": subject.sha(raw)},
                          "raw": raw.decode(), "report": report}
    return tree, captures


def test_new_cross_review_requires_complete_nonwriter_two_axis_coverage():
    subject = module("p17_m2_source_binding_recovery").for_identity(RECOVERY)
    tree, captures = component_reviews(subject)
    subject.validate_component_reviews(captures, tree)
    report = captures["standards"]["report"]
    report["reviewed_files"].pop(next(iter(report["reviewed_files"])))
    raw = subject.canonical(report)
    captures["standards"].update(raw=raw.decode(), reference={
        "path": captures["standards"]["reference"]["path"], "sha256": subject.sha(raw)})
    with pytest.raises(ValueError, match="component"):
        subject.validate_component_reviews(captures, tree)


@pytest.mark.parametrize("fault", ["self-author", "partition-sha", "file-sha", "one-axis",
                                  "unbound-raw", "old-whole-pass"])
def test_new_component_review_cannot_substitute_partial_or_self_review(fault):
    subject = module("p17_m2_source_binding_recovery").for_identity(RECOVERY)
    tree, captures = component_reviews(subject)
    capture = captures["standards"]
    report = capture["report"]
    if fault == "self-author":
        report["author"] = "/root/full60_independent"
    elif fault == "partition-sha":
        report["partition_sha256"] = "0" * 64
    elif fault == "file-sha":
        report["reviewed_files"][next(iter(report["reviewed_files"]))] = "0" * 64
    elif fault == "one-axis":
        report["axes"] = ["standards"]
    elif fault == "unbound-raw":
        report["open_findings"] = ["not retained in raw bytes"]
    elif fault == "old-whole-pass":
        report["status"] = "PASS"
    if fault != "unbound-raw":
        raw = subject.canonical(report)
        capture.update(raw=raw.decode(), reference={"path": capture["reference"]["path"],
                                                   "sha256": subject.sha(raw)})
    with pytest.raises(ValueError):
        subject.validate_component_reviews(captures, tree)


@pytest.mark.parametrize("fault", ["foreign-root", "wrong-scope", "bad-plan-sha"])
def test_new_measurement_cannot_label_foreign_root_or_wrong_scope_as_admitted(tmp_path, fault):
    module("p17_m2_homotopy")
    resource = module("p17_m2_resource_control")
    root = ("/Users/keith1117/Library/Application Support/TopoLab-custody/"
            "p17-m2-local-input-version-20261116-full60-a1")
    scope = "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
    argv = [sys.executable, "-I", str(ROOT / "scripts/input_control_full60_20261116.py"),
            "payload", "--root", root, "--plan-sha", "a" * 64, "--role", "exporter-r0"]
    if fault == "foreign-root":
        argv[5] = "/public/unregistered-old-root"
    elif fault == "wrong-scope":
        scope = "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
    elif fault == "bad-plan-sha":
        argv[7] = "not-a-hash"
    with pytest.raises(ValueError, match="exact neutral payload/scope/role"):
        resource.invoke(tmp_path / "not-created", "exporter-r0", argv, timeout=0,
                        measurement_scope=scope,
                        measurement_execution_identity=
                        "topolab.v2.p17-m2-registered-source-acquisition.20261116.v1")
    assert not (tmp_path / "not-created").exists()
