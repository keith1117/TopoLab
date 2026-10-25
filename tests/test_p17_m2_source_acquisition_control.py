"""S2 new source-acquisition binding interface: NEW public data only."""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
ENTRY = REPO / "scripts/p17_m2_source_acquisition_control.py"


def single_thread_environment():
    return {
        **os.environ,
        **dict.fromkeys(
            (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            ),
            "1",
        ),
    }


def load():
    spec = importlib.util.spec_from_file_location("source_acquisition_control_test", ENTRY)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_formal_entry_denies_before_inspecting_any_scientific_path(monkeypatch):
    controller = load()
    monkeypatch.setattr(controller, "EXECUTION_AUTHORITY_RAW", None)

    def forbidden(*args, **kwargs):
        pytest.fail("ungranted formal entry reached filesystem")

    monkeypatch.setattr("os.open", forbidden)
    monkeypatch.setattr(Path, "stat", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    with pytest.raises(ValueError, match="FORMAL_AUTHORITY_NOT_GRANTED"):
        controller.activate_formal("not-a-public-root")


def test_rehearsal_freezes_new_identity_and_explicit_nonformal_source_target_binding(tmp_path):
    root = tmp_path.resolve() / "topolab-public-formal-binding-plan"
    result = subprocess.run(
        [
            str(Path(sys.orig_argv[0]).resolve()),
            "-I",
            str(ENTRY),
            "prepare-rehearsal",
            "--root",
            str(root),
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        env=single_thread_environment(),
        check=False,
    )
    assert result.returncode == 0, result.stderr
    packet = json.loads(result.stdout)
    plan = json.loads((root / "plan.json").read_bytes())
    assert packet["formal_authority"] is False
    assert plan["execution_identity"] == "topolab.v2.p17-m2-content-verified-source-acquisition.v1"
    assert plan["scope"] == "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
    assert plan["source_root"] == str(root / "public-source")
    assert plan["content_root"] == str(root / "content")
    assert plan["backup_root"] == str(root / "backup-content")
    assert plan["binding"]["old_original_access"] is False
    assert plan["binding"]["target_access"] is False
    assert plan["binding"]["B_C"] is False
    assert plan["actor_window_seconds"] == 4500
    assert plan["roles"]["exporter-r0"]["argv"][2] == str(ENTRY)


def test_new_binding_native_precheck_keeps_actual_new_identity_and_full_exit_inventory(tmp_path):
    root = tmp_path.resolve() / "topolab-public-formal-binding-native"
    argv = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(ENTRY)]
    prepared = subprocess.run(
        [*argv, "prepare-rehearsal", "--root", str(root)],
        cwd=Path(argv[2]).parents[1],
        capture_output=True,
        text=True,
        env=single_thread_environment(),
        check=True,
    )
    plan_sha = json.loads(prepared.stdout)["plan_sha256"]
    args = ["--root", str(root), "--plan-sha", plan_sha, "--role", "independent-public-check"]
    started = subprocess.run(
        [*argv, "supervise", *args],
        capture_output=True,
        text=True,
        env=single_thread_environment(),
    )
    assert started.returncode == 0, started.stderr
    returned = subprocess.run(
        [*argv, "record", *args],
        capture_output=True,
        text=True,
        env=single_thread_environment(),
    )
    assert returned.returncode == 0, returned.stderr
    packet = json.loads(returned.stdout)
    assert packet["pending"]["execution_identity"] == (
        "topolab.v2.p17-m2-content-verified-source-acquisition.v1"
    )
    assert packet["pending"]["external_argv"][0][2] == str(ENTRY)
    assert packet["completion"]["domain_status"] == "PASS"
    assert packet["completion"]["cleanup"]["group_gone"] is True
    assert len(packet["completion"]["resource_components"]) == 4
    assert packet["completion"]["status"] == "PENDING_EXTERNAL_EXIT"
    assert not (root / "independent-public-check-accepted.json").exists()


def frozen_program(tmp_path):
    runtime = tmp_path / "source-only-runtime"
    (runtime / "scripts").mkdir(parents=True)
    (runtime / "docs/planning").mkdir(parents=True)
    for path in (REPO / "scripts").glob("p17_m2_*"):
        if path.is_file():
            shutil.copyfile(path, runtime / "scripts" / path.name)
    for name in (
        "p17_m2_source_acquisition_adapter_preparation_protocol.json",
        "p17_m2_content_verified_source_acquisition_proposal.json",
        "p17_m2_content_verified_custody_protocol.json",
        "p17_m2_content_verified_custody_proposal.json",
        "p17_m2_input_export_preparation_proposal.json",
    ):
        shutil.copyfile(REPO / "docs/planning" / name, runtime / "docs/planning" / name)
    shutil.copyfile(REPO / "uv.lock", runtime / "uv.lock")
    return runtime / "scripts/p17_m2_source_acquisition_control.py"


def run_rehearsal_role(argv, root, plan_sha, role, *, accepted=True):
    """Unit event inputs from local subprocesses, not trusted functions observations."""
    import hashlib

    events = []
    for mode in ("supervise", "record"):
        command = [*argv, mode, "--root", str(root), "--plan-sha", plan_sha, "--role", role]
        if role in ("public-consumer", "reader-ack"):
            command += ["--reader-role", "scientific-producer"]
        start = round(time.time(), 3)
        result = subprocess.run(
            command,
            cwd=Path(argv[2]).parents[1],
            capture_output=True,
            text=True,
            env=single_thread_environment(),
        )
        end = round(time.time(), 3)
        event = dict(
            event_id=f"unit-{role}-{mode}",
            argv=command,
            start_seconds=start,
            end_seconds=end,
            wall_seconds=end - start,
            exit_code=result.returncode,
            complete=True,
            clock_domain="functions.exec.Date.now.UTC-seconds",
        )
        assert result.returncode == 0, result.stderr + result.stdout
        if mode == "record":
            packet = json.loads(result.stdout)
            for field in ("pending", "completion"):
                raw = (
                    json.dumps(
                        packet[field],
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=True,
                        allow_nan=False,
                    )
                    + "\n"
                ).encode()
                event["observed_" + field + "_sha256"] = hashlib.sha256(raw).hexdigest()
        events.append(event)
    fd = os.open(root / (role + "-events.json"), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(events, stream)
    bind_argv = [*argv, "bind", "--root", str(root), "--plan-sha", plan_sha, "--role", role]
    if role in ("public-consumer", "reader-ack"):
        bind_argv += ["--reader-role", "scientific-producer"]
    result = subprocess.run(
        bind_argv,
        cwd=Path(argv[2]).parents[1],
        capture_output=True,
        text=True,
        env=single_thread_environment(),
    )
    assert result.returncode == (0 if accepted else 1), result.stderr + result.stdout
    proof = json.loads(result.stdout)
    assert (
        bool(proof.get("full_role_evidence_accepted") or proof.get("metadata_evidence_accepted"))
        is accepted
    )
    return proof


def test_connected_new_binding_rehearsal_has_independent_source_and_finite_certificate(tmp_path):
    program = frozen_program(tmp_path)
    root = tmp_path.resolve() / "topolab-public-formal-binding-connected"
    argv = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    result = subprocess.run(
        [*argv, "prepare-rehearsal", "--root", str(root)],
        cwd=Path(argv[2]).parents[1],
        capture_output=True,
        text=True,
        env=single_thread_environment(),
        check=True,
    )
    plan_sha = json.loads(result.stdout)["plan_sha256"]
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
        run_rehearsal_role(argv, root, plan_sha, role)
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
        env=single_thread_environment(),
    )
    assert certified.returncode == 0, certified.stderr + certified.stdout
    proof = json.loads(certified.stdout)
    assert proof["formal_authority"] is False
    assert proof["scope"] == "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
    assert proof["member_count"] == 1071
    assert not (root / "active.json").exists()
    assert not (root / "content.cooperative-reader.lease").exists()
    for role in ("public-consumer", "reader-ack"):
        run_rehearsal_role(argv, root, plan_sha, role)
    consumption = json.loads((root / "public-consumption.json").read_bytes())
    assert consumption["member_count"] == 541
    assert consumption["same_read_buffer"] is True
    assert consumption["formal_authority"] is False
    assert not (root / "content.cooperative-reader.lease").exists()


def future_authority():
    return {
        "schema": "topolab.v2.m2-source-acquisition-execution-authority.v1",
        "execution_identity": "topolab.v2.p17-m2-content-verified-source-acquisition.v1",
        "proposal_sha256": "2c7d0e9243b3ab6beda9344b06c7e88cfbf03910f7104fa43f91c54670a32304",
        "owner_approval_reference": "SYNTHETIC_UNIT_METADATA_NOT_ACTUAL_AUTHORITY",
        "permissions": {
            "formal_activation": True,
            "old_original_access": True,
            "target_access": True,
            "B_C": False,
        },
        "formal_seconds": 4500,
        "result_seconds": {"exporter": 7200, "independent": 7200},
    }


@pytest.mark.parametrize("authority_present", [False, True])
def test_preparation_checks_are_isolated_from_optional_execution_authority(
    tmp_path, authority_present
):
    """The ungranted and pure-plan checks must work after authority publication too."""
    program = frozen_program(tmp_path)
    runtime = program.parents[1]
    copied_test = runtime / "tests" / Path(__file__).name
    copied_test.parent.mkdir()
    copied_test.write_bytes(Path(__file__).read_bytes())
    if authority_present:
        (runtime / "docs/planning/p17_m2_source_acquisition_execution_protocol.json").write_text(
            json.dumps(future_authority())
        )
    observed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-m",
            "pytest",
            "-q",
            str(copied_test)
            + "::test_formal_entry_denies_before_inspecting_any_scientific_path",
            str(copied_test)
            + (
                "::test_formal_plan_metadata_uses_frozen_original_contract"
                "_without_touching_declared_paths"
            ),
        ],
        cwd=runtime,
        capture_output=True,
        text=True,
        timeout=60,
        env={**single_thread_environment(), "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1"},
    )
    assert observed.returncode == 0, observed.stdout + observed.stderr


def test_formal_plan_metadata_uses_frozen_original_contract_without_touching_declared_paths(
    monkeypatch,
):
    controller = load()
    monkeypatch.setattr(controller, "EXECUTION_AUTHORITY_RAW", None)
    controller.base()  # Software imports only, before blocking data-directory operations.

    def forbidden(*args, **kwargs):
        pytest.fail("pure formal plan metadata inspected a declared source or target")

    monkeypatch.setattr(controller.base(), "nofollow_directory", forbidden)
    authority = future_authority()
    plan = controller.formal_plan(controller.base().canonical(authority))
    assert plan["scope"] == "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
    assert plan["source_root"] == "/Users/keith1117/Documents/TopoLab-data"
    assert plan["backup_root"].endswith("/p17-m2-local-input-version-v2-independent-backup")
    assert plan["content_root"] == plan["root"] + "/content"
    assert "public_source_identity" not in plan
    original = json.loads(
        (REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json").read_bytes()
    )
    assert plan["content_contract"] == original
    assert plan["binding"]["formal_authority"] is True
    assert plan["binding"]["B_C"] is False
    assert controller.EXECUTION_AUTHORITY_RAW is None  # Pure plan is not activation.


@pytest.mark.skipif(sys.platform != "darwin", reason="fixed future macOS target admission")
def test_local_filesystem_admission_uses_kernel_flags_on_new_public_directory(tmp_path):
    controller = load()
    descriptor = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        proof = controller.local_filesystem(descriptor)
        assert proof["local_filesystem"] is True
        assert proof["filesystem"] in ("apfs", "hfs")
        assert proof["available_bytes"] > 0
        assert proof["basis"] == "DARWIN_FSTATFS64_MNT_LOCAL"
    finally:
        os.close(descriptor)


def test_formal_permission_record_without_readiness_cannot_reach_target_setup(monkeypatch):
    controller = load()
    monkeypatch.setattr(controller, "EXECUTION_AUTHORITY_RAW", b"{}\n")

    def forbidden(*args, **kwargs):
        pytest.fail("incomplete authority reached target setup")

    monkeypatch.setattr("os.open", forbidden)
    with pytest.raises(ValueError, match="FROZEN_ACTIVATION_READINESS_REQUIRED"):
        controller.activate_formal("declared-future-target")


def test_new_entry_rejects_wrong_actual_working_directory_before_creating_public_root(tmp_path):
    root = tmp_path / "topolab-public-formal-binding-wrong-cwd"
    result = subprocess.run(
        [
            str(Path(sys.orig_argv[0]).resolve()),
            "-I",
            str(ENTRY),
            "prepare-rehearsal",
            "--root",
            str(root),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "ACTUAL_WORKING_DIRECTORY_CHANGED" in result.stderr
    assert not root.exists()


def test_namespace_rejects_dangling_backup_symlink_in_new_public_policy_fixture(
    tmp_path, monkeypatch
):
    """Exercise future path policy with synthetic metadata, never the real target or authority."""
    controller = load()
    root, backup = tmp_path / "topolab-public-formal-binding-directory", tmp_path / "public-backup"
    root.mkdir(mode=0o700)
    backup.symlink_to(tmp_path / "missing-public-directory", target_is_directory=True)
    proposal = tmp_path / "source-only-proposal.json"
    proposal.write_text(
        json.dumps({"target_proposal_only": {"generation": str(root), "backup": str(backup)}})
    )
    monkeypatch.setattr(controller, "REPO", tmp_path)
    monkeypatch.setattr(controller, "PROPOSAL", proposal.name)
    monkeypatch.setattr(controller, "EXECUTION_AUTHORITY_RAW", b"SYNTHETIC_PATH_POLICY_ONLY")
    transport = controller.AcquisitionTransport(root, "a" * 64, scope=controller.FORMAL_SCOPE)
    with pytest.raises(ValueError, match="BACKUP_DIRECTORY_NOFOLLOW_REQUIRED"):
        transport.namespace_check(root)


def test_new_source_failure_keeps_full_prefix_charge_and_permits_only_reserved_closeout(tmp_path):
    program = frozen_program(tmp_path)
    root = tmp_path.resolve() / "topolab-public-formal-binding-failed-prefix"
    argv = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*argv, "prepare-rehearsal", "--root", str(root)],
        cwd=program.parents[1],
        capture_output=True,
        text=True,
        env=single_thread_environment(),
        check=True,
    )
    plan_sha = json.loads(prepared.stdout)["plan_sha256"]
    plan = json.loads((root / "plan.json").read_bytes())
    first = plan["content_contract"]["R0"]["literal_bootstrap_files"][0]["relative_path"]
    (root / "public-source" / first).write_bytes(b"bad")
    run_rehearsal_role(argv, root, plan_sha, "independent-public-check")
    failed = run_rehearsal_role(argv, root, plan_sha, "exporter-r0", accepted=False)
    assert failed["known_cost_lower_bound_seconds"] == 300
    assert failed["whole_wall_seconds"] > 0
    assert not (root / "receipts/independent-r0-pending.json").exists()
    failure = json.loads((root / "exporter-r0-failure.json").read_bytes())
    assert failure["source_identities"] == []  # No successful source row before the first failure.
    fact = failure["source_failures"][0]
    assert fact["returned_bytes"] == 3
    assert fact["before"] == fact["after"] == fact["closing"]
    assert fact["path"] == first
    closed = run_rehearsal_role(argv, root, plan_sha, "shared-closeout", accepted=False)
    assert closed["known_cost_lower_bound_seconds"] == 300
    backup = json.loads((root / "failed-prefix-backup-proof.json").read_bytes())
    assert backup["status"] == "SOURCE_ACQUISITION_FAILED_PREFIX_BACKUP_CHECKED"
    assert backup["old_original_reads"] == 0
    assert not (root / "accepted-acquisition-bundle.json").exists()
    assert not (root / "active.json").exists()


def test_changed_deferred_setup_binding_blocks_first_native_dispatch(tmp_path):
    program = frozen_program(tmp_path)
    root = tmp_path.resolve() / "topolab-public-formal-binding-setup-binding"
    argv = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*argv, "prepare-rehearsal", "--root", str(root)],
        cwd=program.parents[1],
        capture_output=True,
        text=True,
        env=single_thread_environment(),
        check=True,
    )
    plan_sha = json.loads(prepared.stdout)["plan_sha256"]
    proof = json.loads((root / "setup-proof.json").read_bytes())
    assert proof["plan_sha256"] == plan_sha
    proof["plan_sha256"] = "0" * 64
    (root / "setup-proof.json").write_text(json.dumps(proof))
    result = subprocess.run(
        [
            *argv,
            "supervise",
            "--root",
            str(root),
            "--plan-sha",
            plan_sha,
            "--role",
            "independent-public-check",
        ],
        cwd=program.parents[1],
        capture_output=True,
        text=True,
        env=single_thread_environment(),
    )
    assert result.returncode != 0
    assert "SETUP_BINDING_CHANGED" in result.stderr
    assert not (root / "receipts/independent-public-check-pending.json").exists()


def test_reserved_authority_symlink_cannot_read_even_new_public_canary_before_refusal(tmp_path):
    program = frozen_program(tmp_path)
    canary = tmp_path / "unapproved-public-canary"
    os.mkfifo(canary, mode=0o600)
    reserved = (
        program.parents[1] / "docs/planning/p17_m2_source_acquisition_execution_protocol.json"
    )
    reserved.symlink_to(canary)
    root = tmp_path.resolve() / "topolab-public-formal-binding-never-created"
    try:
        result = subprocess.run(
            [
                str(Path(sys.orig_argv[0]).resolve()),
                "-I",
                str(program),
                "activate-formal",
                "--root",
                str(root),
            ],
            cwd=program.parents[1],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("reserved authority symlink was followed into the unapproved FIFO")
    assert result.returncode != 0
    assert not root.exists()


def test_pure_formal_metadata_rejects_integer_permissions_instead_of_normalizing_them():
    controller = load()
    authority = future_authority()
    authority["permissions"]["old_original_access"] = 1
    with pytest.raises(ValueError, match="FORMAL_EXECUTION_AUTHORITY_INVALID"):
        controller.formal_plan(controller.base().canonical(authority))


def test_failed_prefix_competing_symlink_cannot_create_directories_outside_new_backup(
    tmp_path, monkeypatch
):
    """A competing public writer replaces a component immediately before mkdir."""
    controller = load()
    root = tmp_path / "topolab-public-formal-binding-prefix-race"
    root.mkdir(mode=0o700)
    outside = tmp_path / "unregistered-public-directory"
    outside.mkdir(mode=0o700)
    for suffix in ("receipts", "receipts/old", "receipts/old/inner"):
        (root / suffix).mkdir(mode=0o700)
    helper = controller.base()
    helper.put(root / "STOP.json", {"status": "STOP_NO_RETRY"})
    helper.put(root / "receipts/old/inner/packet.json", {"new_public": True})
    backup = root / "backup-prefix"
    actual_mkdir = os.mkdir
    injected = False

    def competing_mkdir(path, mode=0o777, *, dir_fd=None):
        nonlocal injected
        if not injected and (
            str(path).startswith(str(backup / "receipts"))
            or str(path) == "receipts"
            and dir_fd is not None
        ):
            (backup / "receipts").symlink_to(outside, target_is_directory=True)
            injected = True
        if dir_fd is None:
            return actual_mkdir(path, mode)
        return actual_mkdir(path, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "mkdir", competing_mkdir)
    transport = controller.AcquisitionTransport(root, "a" * 64)
    with pytest.raises((ValueError, OSError)):
        transport.backup_failed_prefix(root, {}, {"copied_members": []})
    assert injected
    assert list(outside.iterdir()) == []
