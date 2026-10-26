"""Funded prospective formal metadata; never opens originals or custody targets."""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def controller():
    spec = importlib.util.spec_from_file_location(
        "funded_acquisition_control_test", REPO / "scripts/p17_m2_source_acquisition_control.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def authority():
    value = json.loads(
        (REPO / "docs/planning/p17_m2_hash_bound_acquisition_protocol.json").read_bytes()
    )
    value.update(
        schema="topolab.v2.m2-funded-acquisition-authority.v1",
        execution_identity="topolab.v2.p17-m2-hash-bound-source-acquisition.v2",
        proposal_sha256="2c7d0e9243b3ab6beda9344b06c7e88cfbf03910f7104fa43f91c54670a32304",
        result_seconds={"exporter": 7200, "independent": 7200},
        outer_wall_seconds=129600,
        total_new_author_charged_seconds_cap=194400,
    )
    for number, target in value["fixed_target"]["attempts"].items():
        generation = (
            value["fixed_target"]["parent"]
            + f"/p17-m2-local-input-version-v{int(number) + 4}-hash-bound-20261026"
        )
        target.update(generation=generation, backup=generation + "-independent-backup")
    return value


def test_unknown_root_with_new_authority_denies_before_loading_or_path_io(monkeypatch):
    control = controller()
    monkeypatch.setattr(control, "EXECUTION_AUTHORITY_RAW", None)
    assert control.FUNDED_AUTHORITY_RAW is not None

    def forbidden(*args, **kwargs):
        raise AssertionError("unknown root reached loader or filesystem")

    # Restore the global Path seam before pytest formats any failed assertion.
    with monkeypatch.context() as guard:
        guard.setattr(control, "load", forbidden)
        guard.setattr(control.os, "open", forbidden)
        guard.setattr(Path, "stat", forbidden)
        guard.setattr(Path, "read_bytes", forbidden)
        with pytest.raises(ValueError, match="FORMAL_AUTHORITY_NOT_GRANTED"):
            control.activate_formal("not-a-public-root")


def test_historical_preflight_path_is_rejected_before_external_metadata_read(monkeypatch):
    control = controller()
    value = json.loads((REPO / control.FUNDED_PROTOCOL).read_bytes())
    value["readiness_freeze_state"] = "REVIEWED_FROZEN"
    value["published_source_sha256"] = {}
    value["independent_preflight_path"] = (
        "/private/tmp/topolab-funded-continuation-20261026/independent/preflight.json"
    )
    checker = control.load("p17_m2_source_acquisition_independent")

    def forbidden(*args, **kwargs):
        raise AssertionError("superseded preflight path reached external metadata")

    monkeypatch.setattr(control, "source_freeze", lambda: {})
    monkeypatch.setattr(checker.native, "_software_bytes", forbidden)
    with pytest.raises(ValueError, match="EXACT_INDEPENDENT_PREFLIGHT_PATH_REQUIRED"):
        control.activation_readiness(value)


def test_new_formal_plan_selects_fresh_fixed_attempt_and_complete_result_budget():
    control = controller()
    plan = control.formal_plan(control.base().canonical(authority()), attempt=2)
    assert plan["execution_identity"] == "topolab.v2.p17-m2-hash-bound-source-acquisition.v2"
    assert plan["root"].endswith("/p17-m2-local-input-version-v6-hash-bound-20261026")
    assert plan["backup_root"] == plan["root"] + "-independent-backup"
    assert plan["source_root"] == "/Users/keith1117/Documents/TopoLab-data"
    assert plan["binding"]["formal_attempt"] == 2
    assert plan["binding"]["authority_protocol_path"] == (
        "docs/planning/p17_m2_funded_acquisition_protocol.json"
    )
    assert plan["source_identity_policy"] == "topolab.source-identity.prebound-sha256.v1"
    assert plan["result_window_projection_seconds"] == {"exporter": 7200, "independent": 7200}


def test_actual_formal_transport_uses_new_policy_on_both_registered_attempts(monkeypatch):
    control = controller()
    value = authority()
    monkeypatch.setattr(
        control, "FUNDED_AUTHORITY_RAW", control.base().canonical(value), raising=False
    )
    for target in value["fixed_target"]["attempts"].values():
        transport = control.AcquisitionTransport(
            Path(target["generation"]), "1" * 64, scope=control.FORMAL_SCOPE
        )
        assert transport.identity == "topolab.v2.p17-m2-hash-bound-source-acquisition.v2"
        assert transport.source_identity_policy == "topolab.source-identity.prebound-sha256.v1"
        assert transport.result_windows == (("exporter", 7200), ("independent", 7200))


def test_new_plan_rejects_unfunded_results_and_unregistered_attempt():
    control = controller()
    value = authority()
    with pytest.raises(ValueError, match="UNREGISTERED_FORMAL_ATTEMPT"):
        control.formal_plan(control.base().canonical(value), attempt=3)
    value["result_seconds"]["independent"] = 1200
    with pytest.raises(ValueError, match="FORMAL_EXECUTION_AUTHORITY_INVALID"):
        control.formal_plan(control.base().canonical(value))


def test_unfrozen_funding_cannot_reach_main_network_or_target(monkeypatch):
    control = controller()
    value = authority()
    value.update(
        actors={"executor": "/root", "independent": "/root/acquisition_funded_audit"},
        implementation_base_commit="2f67feee4d89c94b36196122a5930a56d5b8433f",
        readiness_freeze_state="DRAFT_NOT_YET_REVIEWED",
        preparation_closure_sha256="1" * 64,
        independent_preflight_sha256="2" * 64,
    )

    def forbidden(*args, **kwargs):
        pytest.fail("unfrozen authority reached process/network or custody filesystem")

    monkeypatch.setattr(control.subprocess, "run", forbidden)
    monkeypatch.setattr(control.os, "open", forbidden)
    with pytest.raises(ValueError, match="FUNDED_READINESS_NOT_FROZEN"):
        control.activation_readiness(value)


def test_readiness_rejects_unlisted_closure_paths_before_read(monkeypatch):
    control = controller()
    value = authority()
    value.update(
        readiness_freeze_state="REVIEWED_FROZEN",
        preparation_closure_paths=[
            "/private/tmp/ungranted-original-a.json",
            "/private/tmp/ungranted-original-b.json",
        ],
    )

    def forbidden(*args, **kwargs):
        pytest.fail("unlisted closure path reached filesystem")

    monkeypatch.setattr(control.os, "open", forbidden)
    with pytest.raises(ValueError, match="EXACT_PREPARATION_CLOSURES_REQUIRED"):
        control.activation_readiness(value)


def test_funded_public_complete_chain_and_certificate_remain_nonformal(tmp_path):
    spec = importlib.util.spec_from_file_location(
        "funded_acquisition_pipeline_helpers",
        Path(__file__).with_name("test_p17_m2_source_acquisition_control.py"),
    )
    assert spec and spec.loader
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    program = helpers.frozen_program(tmp_path)
    for name in (
        "p17_m2_hash_bound_acquisition_protocol.json",
        "p17_m2_funded_acquisition_protocol.json",
    ):
        shutil.copyfile(REPO / "docs/planning" / name, program.parents[1] / "docs/planning" / name)
    root = tmp_path.resolve() / "topolab-public-funded-acquisition-connected"
    argv = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*argv, "prepare-rehearsal", "--root", str(root)],
        cwd=program.parents[1],
        capture_output=True,
        text=True,
        env=helpers.single_thread_environment(),
        check=True,
    )
    plan_sha = json.loads(prepared.stdout)["plan_sha256"]
    plan = json.loads((root / "plan.json").read_bytes())
    assert plan["execution_identity"] == "topolab.v2.p17-m2-hash-bound-source-acquisition.v2"
    for role in (
        "independent-public-check",
        "exporter-r0",
        "independent-r0",
        "exporter-r1",
        "independent-r1",
        "shared-closeout",
        "final-filing",
        "lease-release",
    ):
        helpers.run_rehearsal_role(argv, root, plan_sha, role)
    certified = subprocess.run(
        [
            *argv,
            "certify-rehearsal",
            "--root",
            str(root),
            "--plan-sha",
            plan_sha,
            "--role",
            "certificate",
        ],
        cwd=program.parents[1],
        capture_output=True,
        text=True,
        env=helpers.single_thread_environment(),
    )
    assert certified.returncode == 0, certified.stderr + certified.stdout
    proof = json.loads(certified.stdout)
    assert proof["member_count"] == 1071
    assert proof["formal_authority"] is False and proof["source_input_accepted"] is False
    for role in ("public-consumer", "reader-ack"):
        helpers.run_rehearsal_role(argv, root, plan_sha, role)
    consumed = json.loads((root / "public-consumption.json").read_bytes())
    assert consumed["same_read_buffer"] is True and consumed["member_count"] == 541
    assert consumed["execution_identity"] == plan["execution_identity"]


def test_formal_clock_starts_after_actual_readiness_completes(monkeypatch):
    control = controller()
    value = authority()
    raw = control.base().canonical(value)
    monkeypatch.setattr(control, "authority_for_root", lambda root: (raw, 1))
    clock = [100.0]
    monkeypatch.setattr(control.time, "time", lambda: clock[0])

    def ready(authority):
        clock[0] = 200.0
        return {"actual_readiness_completed": 200.0}

    monkeypatch.setattr(control, "activation_readiness", ready)
    checker = control.load("p17_m2_source_acquisition_independent")
    monkeypatch.setattr(checker, "validate_binding", lambda plan: None)
    monkeypatch.setattr(control, "setup_formal", lambda plan, readiness: (plan, readiness))
    plan, readiness = control.activate_formal(value["fixed_target"]["attempts"]["1"]["generation"])
    assert plan["actor_activation_UTC_seconds"] >= readiness["actual_readiness_completed"]


def test_second_reserved_attempt_cannot_activate_without_new_frozen_remedy(monkeypatch):
    control = controller()
    value = authority()
    monkeypatch.setattr(
        control, "authority_for_root", lambda root: (control.base().canonical(value), 2)
    )
    checker = control.load("p17_m2_source_acquisition_independent")
    monkeypatch.setattr(checker, "validate_binding", lambda plan: None)

    def forbidden(*args):
        pytest.fail("unfrozen second attempt reached readiness or target setup")

    monkeypatch.setattr(control, "activation_readiness", forbidden)
    monkeypatch.setattr(control, "setup_formal", forbidden)
    with pytest.raises(ValueError, match="NEW_FROZEN_REMEDY_REQUIRED"):
        control.activate_formal(value["fixed_target"]["attempts"]["2"]["generation"])


def test_public_fixture_reuse_refuses_unknown_plan_hash_before_copy(tmp_path):
    control = controller()
    source = tmp_path / "topolab-public-funded-acquisition-source"
    source.mkdir()
    (source / "plan.json").write_bytes(b"{}\n")
    target = tmp_path / "topolab-public-funded-acquisition-next"
    with pytest.raises(ValueError, match="PUBLIC_SOURCE_PLAN_HASH_CHANGED"):
        control.prepare_rehearsal(
            target, public_source_plan=source / "plan.json", public_source_plan_sha="a" * 64
        )
    assert not target.exists()


@pytest.mark.parametrize("historical_authority", [False, True])
def test_real_public_prepare_cli_binds_reused_graph_and_exact_startup(
    tmp_path, historical_authority
):
    control = controller()
    source = tmp_path / "topolab-public-funded-acquisition-copy-source"
    target = tmp_path / "topolab-public-funded-acquisition-copy-target"
    argv = [
        str(Path(sys.orig_argv[0]).resolve()),
        "-I",
        str(REPO / "scripts/p17_m2_source_acquisition_control.py"),
    ]
    env = {**__import__("os").environ, **dict.fromkeys(control.base().THREADS, "1")}
    first = subprocess.run(
        [*argv, "prepare-rehearsal", "--root", str(source)],
        cwd=REPO,
        capture_output=True,
        text=True,
        env=env,
    )
    assert first.returncode == 0, first.stderr
    source_plan = source / "plan.json"
    if historical_authority:
        old = json.loads(source_plan.read_bytes())
        old["source_tree"][control.FUNDED_PROTOCOL] = "d" * 64
        old["binding"]["preparation_protocol_sha256"] = "d" * 64
        old["preparation_contract_sha256"] = old["contract_sha256"] = "d" * 64
        source_plan.write_bytes(control.base().canonical(old))
    args = [
        *argv,
        "prepare-rehearsal",
        "--root",
        str(target),
        "--public-source-plan",
        str(source_plan),
        "--public-source-plan-sha",
        control.base().sha(source_plan.read_bytes()),
    ]
    copied = subprocess.run(args, cwd=REPO, capture_output=True, text=True, env=env)
    assert copied.returncode == 0, copied.stderr
    plan = json.loads((target / "plan.json").read_bytes())
    assert plan["runtime"]["orig_argv"] == args
    assert plan["binding"]["public_source_plan"] == str(source_plan)
    proof = json.loads((target / "public-source-copy.json").read_bytes())
    assert len(proof["copies"]) == 598 and proof["old_original_reads"] == 0
    assert plan["formal_authority"] is False
    checker = control.load("p17_m2_source_acquisition_independent")
    checker._check_software(plan)
    assert plan["source_tree"][control.FUNDED_PROTOCOL] != "d" * 64


def test_public_source_copy_refuses_root_alias_before_any_directory_probe(tmp_path, monkeypatch):
    import os
    import time

    control = controller()
    actual = tmp_path / "new-public-data"
    actual.mkdir()
    alias = tmp_path / "new-public-alias"
    alias.symlink_to(actual, target_is_directory=True)
    target = tmp_path / "new-public-failed-copy"
    target.mkdir()

    def forbidden(*args, **kwargs):
        pytest.fail("source root alias reached directory traversal")

    monkeypatch.setattr(os, "scandir", forbidden)
    with pytest.raises((OSError, ValueError)):
        control.copy_public_source(target, alias, began=time.monotonic())
    failure = json.loads((target / "public-source-copy-failure.json").read_bytes())
    assert failure["status"] == "STOP_PUBLIC_COPY"
    assert failure["source_facts"] == {} and failure["copies"] == []


def test_public_inventory_failure_keeps_offending_literal_path_and_raw_stat(tmp_path):
    import time

    control = controller()
    source = tmp_path / "new-public-source"
    source.mkdir()
    (source / "forbidden-link").symlink_to("missing-new-public-member")
    target = tmp_path / "new-public-failed-copy"
    target.mkdir()
    with pytest.raises(ValueError, match="PUBLIC_SOURCE_FILE_KIND_REFUSED"):
        control.copy_public_source(target, source, began=time.monotonic())
    failure = json.loads((target / "public-source-copy-failure.json").read_bytes())
    assert failure["inventory_cursor"]["path"] == "forbidden-link"
    assert (
        failure["inventory_cursor"]["raw_stat"]["st_ino"]
        == (source / "forbidden-link").lstat().st_ino
    )
    assert failure["source_facts"] == {} and failure["copies"] == []
