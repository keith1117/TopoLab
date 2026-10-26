"""Complete NEW public command/lease/certificate/buffer integration, never formal."""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def test_hash_bound_public_pipeline_keeps_scope_and_independent_certificate(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "hash_bound_pipeline_helpers", Path(__file__).with_name(
            "test_p17_m2_source_acquisition_control.py"))
    assert spec and spec.loader
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    program = helpers.frozen_program(tmp_path)
    name = "p17_m2_hash_bound_acquisition_protocol.json"
    shutil.copyfile(helpers.REPO / "docs/planning" / name,
                    program.parents[1] / "docs/planning" / name)
    root = tmp_path.resolve() / "topolab-public-hash-bound-connected"
    argv = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    started = subprocess.run([*argv, "prepare-rehearsal", "--root", str(root)],
        cwd=program.parents[1], capture_output=True, text=True,
        env=helpers.single_thread_environment(), check=True)
    plan_sha = json.loads(started.stdout)["plan_sha256"]
    plan = json.loads((root / "plan.json").read_bytes())
    assert plan["execution_identity"] == "topolab.v2.p17-m2-hash-bound-source-acquisition.v1"
    assert plan["source_identity_policy"] == "topolab.source-identity.prebound-sha256.v1"
    for role in ("independent-public-check", "exporter-r0", "independent-r0",
                 "exporter-r1", "independent-r1", "shared-closeout", "final-filing",
                 "lease-release"):
        helpers.run_rehearsal_role(argv, root, plan_sha, role)
        if role in ("exporter-r0", "exporter-r1"):
            registry = json.loads((root / "registry.json").read_bytes())
            ref = registry["models"][0]["selection" if role == "exporter-r0" else "checkpoint"]
            path = root / "public-source" / ref["path"]
            info = path.stat()
            os.utime(path, ns=(info.st_atime_ns, info.st_mtime_ns + 89))
    certified = subprocess.run([*argv, "certify-rehearsal", "--root", str(root),
        "--plan-sha", plan_sha, "--role", "certificate"], cwd=program.parents[1],
        capture_output=True, text=True, env=helpers.single_thread_environment())
    assert certified.returncode == 0, certified.stderr + certified.stdout
    proof = json.loads(certified.stdout)
    assert proof["member_count"] == 1071
    assert proof["formal_authority"] is False
    assert proof["source_input_accepted"] is False
    for role in ("public-consumer", "reader-ack"):
        helpers.run_rehearsal_role(argv, root, plan_sha, role)
    consumed = json.loads((root / "public-consumption.json").read_bytes())
    assert consumed["member_count"] == 541 and consumed["same_read_buffer"] is True
    assert consumed["execution_identity"] == plan["execution_identity"]
    assert not (root / "content.cooperative-reader.lease").exists()


def test_hash_bound_authority_requires_json_boolean_permissions(tmp_path, monkeypatch):
    from copy import deepcopy

    import pytest

    spec = importlib.util.spec_from_file_location(
        "hash_bound_authority_control", Path(__file__).parents[1]
        / "scripts/p17_m2_source_acquisition_control.py")
    assert spec and spec.loader
    control = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = control
    spec.loader.exec_module(control)
    checker = control.load("p17_m2_source_acquisition_independent")
    contract = json.loads((control.REPO / checker.CONTENT_CONTRACT).read_bytes())
    contract["R0"]["embedded_B3_data_index_sha256"] = "1" * 64
    for row in contract["R0"]["literal_bootstrap_files"]:
        row["expected_sha256"] = "2" * 64
    plan = control.make_plan(tmp_path.resolve() / "topolab-public-hash-bound-authority", contract,
        {"B3_DATA_HASH": "1" * 64, "CATALOG_HASH": "3" * 64})
    original = checker.native._software_bytes
    authority = json.loads(original(control.REPO / control.COMPAT_PROTOCOL))
    for name in authority["permissions"]:
        changed = deepcopy(authority)
        changed["permissions"][name] = int(changed["permissions"][name])
        raw = checker.canonical(changed)
        altered = deepcopy(plan)
        digest = checker.digest(raw)
        altered["source_tree"][control.COMPAT_PROTOCOL] = digest
        altered["preparation_contract_sha256"] = digest
        altered["binding"]["preparation_protocol_sha256"] = digest
        altered["contract_sha256"] = digest
        monkeypatch.setattr(checker.native, "_software_bytes", lambda path, raw=raw:
            raw if path == control.REPO / control.COMPAT_PROTOCOL else original(path))
        with pytest.raises(ValueError, match="authority identity/permissions/budget"):
            checker.validate_binding(altered)
