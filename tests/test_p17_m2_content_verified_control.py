"""Approved S2 CLI: formal authority is denied before any path access."""

import subprocess
import sys
from pathlib import Path

import pytest


def private_events(path, events):
    import json
    import os

    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(events, stream)


def observed_fields(output):
    import hashlib
    import json

    packet = json.loads(output)

    def digest(value):
        raw = (
            json.dumps(
                value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
            )
            + "\n"
        ).encode("ascii")
        return hashlib.sha256(raw).hexdigest()

    return {
        "observed_pending_sha256": digest(packet["pending"]),
        "observed_completion_sha256": digest(packet["completion"]),
    }


@pytest.fixture(autouse=True)
def frozen_threads(monkeypatch):
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        monkeypatch.setenv(key, "1")


def frozen_program(tmp_path):
    """Freeze a new source-only runtime while authors continue working elsewhere."""
    import shutil

    repo = Path(__file__).parents[1]
    runtime = tmp_path / "frozen-runtime"
    (runtime / "scripts").mkdir(parents=True)
    (runtime / "docs/planning").mkdir(parents=True)
    for path in (repo / "scripts").glob("p17_m2_*"):
        if path.is_file():
            shutil.copyfile(path, runtime / "scripts" / path.name)
    for name in (
        "p17_m2_content_verified_custody_protocol.json",
        "p17_m2_content_verified_custody_proposal.json",
        "p17_m2_input_export_preparation_proposal.json",
    ):
        shutil.copyfile(repo / "docs/planning" / name, runtime / "docs/planning" / name)
    shutil.copyfile(repo / "uv.lock", runtime / "uv.lock")
    return runtime / "scripts/p17_m2_content_verified_control.py"


def test_current_preparation_cannot_stat_a_formal_source_or_target(tmp_path):
    program = frozen_program(tmp_path)
    result = subprocess.run(
        [sys.executable, "-I", str(program), "formal", "--root", str(tmp_path / "must-not-exist")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "FORMAL_AUTHORITY_NOT_GRANTED" in result.stderr
    assert not (tmp_path / "must-not-exist").exists()


def test_public_plan_freezes_new_closed_source_graph_and_rejects_reuse(tmp_path):
    import json

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-content-verified"
    argv = [sys.executable, "-I", str(program), "prepare-public", "--root", str(root)]
    result = subprocess.run(argv, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    plan = json.loads((root / "plan.json").read_bytes())
    assert plan["scope"] == "PUBLIC_SOFTWARE_FIXTURE_ONLY"
    assert plan["formal_authority"] is False
    assert len(plan["public_source_identity"]) == 2
    assert len(plan["roles"]) == 6
    assert plan["runtime"]["python"] == str(Path(sys.orig_argv[0]).resolve())
    assert plan["runtime"]["lock_sha256"]
    assert len(list((root / "public-source").rglob("*.safetensors"))) == 12
    labels = list((root / "public-source/b3-v1-data").rglob("*.json"))
    assert len(labels) == 528
    assert max(p.stat().st_size for p in labels) == 64 * 1048576
    assert (root / "public-source/b3-v1-fits/b3_training.json").stat().st_size == 16 * 1048576
    repeated = subprocess.run(argv, capture_output=True, text=True)
    assert repeated.returncode != 0


def test_public_payload_reads_closed_graph_only_after_independent_r0(tmp_path):
    import json

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-content-verified"
    prepare = subprocess.run(
        [sys.executable, "-I", str(program), "prepare-public", "--root", str(root)],
        capture_output=True,
        text=True,
        check=True,
    )
    plan_sha = json.loads(prepare.stdout)["plan_sha256"]
    prefix = [
        sys.executable,
        "-I",
        str(program),
        "payload",
        "--root",
        str(root),
        "--plan-sha",
        plan_sha,
        "--role",
    ]
    early = subprocess.run([*prefix, "exporter-r1"], capture_output=True, text=True)
    assert early.returncode != 0
    assert not (root / "content").exists()
    # New independent launch gets its own namespace; a stopped plan is never retried.
    assert "predecessor" in early.stderr


def test_first_public_role_records_native_exit_but_needs_actual_external_return(tmp_path):
    import json

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-native"
    args = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*args, "prepare-public", "--root", str(root)], capture_output=True, text=True, check=True
    )
    plan_sha = json.loads(prepared.stdout)["plan_sha256"]
    role_args = ["--root", str(root), "--plan-sha", plan_sha, "--role", "independent-public-check"]
    result = subprocess.run([*args, "supervise", *role_args], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    wire = subprocess.run([*args, "record", *role_args], capture_output=True, text=True)
    assert wire.returncode == 0, wire.stderr
    packet = json.loads(wire.stdout)
    assert packet["completion"]["status"] == "PENDING_EXTERNAL_EXIT"
    assert packet["completion"]["domain_status"] == "PASS"
    assert len(packet["completion"]["resource_components"]) == 4
    assert packet["completion"]["cleanup"]["group_gone"] is True
    assert packet["completion"]["pending_sha256"]
    assert len(wire.stdout.encode()) <= 32768
    assert not (root / "independent-public-check-accepted.json").exists()


def test_forged_predecessor_PASS_does_not_authorize_next_public_payload(tmp_path):
    import json

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-forged"
    argv = [sys.executable, "-I", str(program)]
    prepared = subprocess.run(
        [*argv, "prepare-public", "--root", str(root)], capture_output=True, text=True, check=True
    )
    plan_sha = json.loads(prepared.stdout)["plan_sha256"]
    (root / "independent-public-check-accepted.json").write_text('{"status":"PASS"}')
    result = subprocess.run(
        [*argv, "payload", "--root", str(root), "--plan-sha", plan_sha, "--role", "exporter-r0"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "predecessor" in result.stderr
    assert not (root / "registry.json").exists()


@pytest.mark.parametrize("shared_write_error", [False, True, "bind-persistence"])
def test_public_closed_graph_runs_all_native_roles_with_independent_comparison(
    tmp_path, shared_write_error
):
    """S2 real CLI. UTC event values are test inputs, not functions.exec observations.

    The separately retained public capability run uses the actual functions tool clock.
    No receipt here may authorize a formal/scientific successor.
    """
    import json
    import time

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-connected"
    argv = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*argv, "prepare-public", "--root", str(root)], capture_output=True, text=True, check=True
    )
    plan_sha = json.loads(prepared.stdout)["plan_sha256"]
    roles = [
        "independent-public-check",
        "exporter-r0",
        "independent-r0",
        "exporter-r1",
        "independent-r1",
        "shared-closeout",
        "final-filing",
        "lease-release",
    ]
    for role in roles:
        if role == "shared-closeout" and shared_write_error is True:
            (root / "backup-proof.json").mkdir(mode=0o700)
        if role == "shared-closeout" and shared_write_error == "bind-persistence":
            (root / "shared-packet.json").mkdir(mode=0o700)
        args = ["--root", str(root), "--plan-sha", plan_sha, "--role", role]
        events = []
        for mode in ("supervise", "record"):
            command = [*argv, mode, *args]
            start = round(time.time(), 3)
            result = subprocess.run(command, capture_output=True, text=True)
            end = round(time.time(), 3)
            assert result.returncode == 0, result.stderr
            events.append(
                {
                    "event_id": role + "-" + mode,
                    "start_seconds": start,
                    "end_seconds": end,
                    "wall_seconds": end - start,
                    "clock_domain": "functions.exec.Date.now.UTC-seconds",
                    "argv": command,
                    "complete": True,
                    "exit_code": result.returncode,
                }
            )
            if mode == "record":
                events[-1].update(observed_fields(result.stdout))
        event_file = root / (role + "-events.json")
        private_events(event_file, events)
        accepted = subprocess.run([*argv, "bind", *args], capture_output=True, text=True)
        if role == "shared-closeout" and shared_write_error == "bind-persistence":
            assert accepted.returncode == 1
            stopped = json.loads(accepted.stdout)
            assert stopped["whole_wall_seconds"] > 0
            assert stopped["known_cost_lower_bound_seconds"] >= 300
            assert stopped["full_role_evidence_accepted"] is False
            assert stopped["primary_failure"]["stage"] == "bind persistence"
            assert set(stopped["unfiled_shared_packet"]["raw_packets"]) == set(roles[:6])
            assert set(stopped["unfiled_shared_packet"]["role_results"]) == set(roles[:6])
            assert (root / "STOP.json").is_file()
            assert not (root / "filing-snapshot.json").exists()
            return
        if role == "shared-closeout" and shared_write_error is True:
            assert accepted.returncode == 1
            failure = json.loads(
                (root / "receipts/shared-closeout/shared-closeout/command.log").read_bytes()
            )
            assert failure["status"] == "STOP_NO_RETRY"
            assert len(failure["shared_context"]["copied_members"]) == 1071
            assert failure["shared_context"]["held_lease"]["state"] == "HELD"
            assert (
                failure["shared_context"]["billing_reservation"]["shared_reserved_FULL_seconds"]
                == 300
            )
            assert failure["primary_failure"]["type"] == "FileExistsError"
            assert not (root / "active.json").exists()
            return
        assert accepted.returncode == 0, accepted.stderr + accepted.stdout
    r0 = json.loads((root / "r0-proof.json").read_bytes())
    r1 = json.loads((root / "r1-proof.json").read_bytes())
    assert r0["source_count"] == 40 and r1["source_count"] == 558
    assert len(r1["local_identity_rows"]) == 1071
    assert r1["compared_fields"] > 10000
    backup = json.loads((root / "backup-proof.json").read_bytes())
    assert backup["member_count"] == 1071
    assert backup["version_id"] == r1["version_id"]
    filing = json.loads((root / "filing-snapshot.json").read_bytes())
    assert filing["version_id"] == r1["version_id"]
    assert filing["endpoint"] == "FINITE_SNAPSHOT_EXCLUDES_OWN_FUTURE_RETURN"
    released = json.loads((root / "lease-release.json").read_bytes())
    assert released["state"] == "RELEASED"
    assert released["last_reader_return"]["event_id"] == "final-filing-record"
    assert not (root / "content.cooperative-reader.lease").exists()
    certified = subprocess.run(
        [
            *argv,
            "certify-public",
            "--root",
            str(root),
            "--plan-sha",
            plan_sha,
            "--role",
            "lease-release",
        ],
        capture_output=True,
        text=True,
    )
    assert certified.returncode == 0, certified.stderr
    summary = json.loads(certified.stdout)
    assert summary["formal_authority"] is False
    assert summary["scope"] == "PUBLIC_SOFTWARE_FIXTURE_ONLY"
    assert summary["member_count"] == 1071
    for role in ("public-consumer", "reader-ack"):
        args = [
            "--root",
            str(root),
            "--plan-sha",
            plan_sha,
            "--role",
            role,
            "--reader-role",
            "scientific-auditor",
        ]
        events = []
        for mode in ("supervise", "record"):
            command = [*argv, mode, *args]
            start = round(time.time(), 3)
            result = subprocess.run(command, capture_output=True, text=True)
            end = round(time.time(), 3)
            assert result.returncode == 0, result.stderr + result.stdout
            events.append(
                dict(
                    event_id=role + "-" + mode,
                    start_seconds=start,
                    end_seconds=end,
                    wall_seconds=end - start,
                    clock_domain="functions.exec.Date.now.UTC-seconds",
                    argv=command,
                    complete=True,
                    exit_code=result.returncode,
                )
            )
            if mode == "record":
                events[-1].update(observed_fields(result.stdout))
        private_events(root / (role + "-events.json"), events)
        accepted = subprocess.run([*argv, "bind", *args], capture_output=True, text=True)
        if role == "shared-closeout" and shared_write_error:
            assert accepted.returncode == 1
            failure = json.loads(
                (root / "receipts/shared-closeout/shared-closeout/command.log").read_bytes()
            )
            assert failure["status"] == "STOP_NO_RETRY"
            assert len(failure["shared_context"]["copied_members"]) == 1071
            assert failure["shared_context"]["held_lease"]["state"] == "HELD"
            assert (
                failure["shared_context"]["billing_reservation"]["shared_reserved_FULL_seconds"]
                == 300
            )
            assert failure["primary_failure"]["type"] == "FileExistsError"
            assert not (root / "active.json").exists()
            return
        assert accepted.returncode == 0, accepted.stderr + accepted.stdout
        if role == "public-consumer":
            assert (root / "content.cooperative-reader.lease").is_file()
            assert (
                json.loads((root / "public-consumption.json").read_bytes())["member_count"] == 1069
            )
    assert not (root / "content.cooperative-reader.lease").exists()


def test_failed_shared_collection_keeps_complete_packet_and_secondary_failures(tmp_path):
    import json

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-missing-shared"
    prefix = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*prefix, "prepare-public", "--root", str(root)], capture_output=True, text=True, check=True
    )
    plan_sha = json.loads(prepared.stdout)["plan_sha256"]
    result = subprocess.run(
        [
            *prefix,
            "record",
            "--root",
            str(root),
            "--plan-sha",
            plan_sha,
            "--role",
            "shared-closeout",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    packet = json.loads(result.stdout)
    assert packet["pending"] == {}
    assert packet["completion"]["status"] == "FAILED_INTERNAL_COMPLETION"
    assert packet["completion"]["secondary_failures"]
    assert packet["full_collector_record"]["sha256"]
    collector = root / packet["full_collector_record"]["path"]
    retained = json.loads(collector.read_bytes())
    assert retained["pending"] == {}
    assert retained["completion"]["secondary_failures"]


def test_public_root_symlink_is_denied_before_following_an_unregistered_namespace(tmp_path):
    program = frozen_program(tmp_path)
    outside = tmp_path / "unregistered"
    outside.mkdir()
    root = tmp_path / "topolab-public-symlink"
    root.symlink_to(outside, target_is_directory=True)
    result = subprocess.run(
        [
            str(Path(sys.orig_argv[0]).resolve()),
            "-I",
            str(program),
            "record",
            "--root",
            str(root),
            "--plan-sha",
            "a" * 64,
            "--role",
            "shared-closeout",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "nofollow public directory" in result.stderr
    assert list(outside.iterdir()) == []


def test_direct_public_payload_cannot_bypass_registered_native_launch(tmp_path):
    import json

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-direct"
    prefix = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*prefix, "prepare-public", "--root", str(root)], capture_output=True, text=True, check=True
    )
    plan_sha = json.loads(prepared.stdout)["plan_sha256"]
    result = subprocess.run(
        [
            *prefix,
            "payload",
            "--root",
            str(root),
            "--plan-sha",
            plan_sha,
            "--role",
            "independent-public-check",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert not (root / "independent-public-fixture").exists()


def test_public_source_failure_retains_all_original_read_facts(tmp_path):
    import json
    import time

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-source-failure"
    prefix = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*prefix, "prepare-public", "--root", str(root)], capture_output=True, text=True, check=True
    )
    digest = json.loads(prepared.stdout)["plan_sha256"]
    args = ["--root", str(root), "--plan-sha", digest, "--role", "independent-public-check"]
    events = []
    for mode in ("supervise", "record"):
        command = [*prefix, mode, *args]
        start = round(time.time(), 3)
        result = subprocess.run(command, capture_output=True, text=True)
        end = round(time.time(), 3)
        assert result.returncode == 0, result.stderr
        events.append(
            dict(
                event_id=mode,
                start_seconds=start,
                end_seconds=end,
                wall_seconds=end - start,
                clock_domain="functions.exec.Date.now.UTC-seconds",
                argv=command,
                complete=True,
                exit_code=result.returncode,
            )
        )
        if mode == "record":
            events[-1].update(observed_fields(result.stdout))
    private_events(root / "independent-public-check-events.json", events)
    subprocess.run([*prefix, "bind", *args], capture_output=True, text=True, check=True)
    plan = json.loads((root / "plan.json").read_bytes())
    member = plan["content_contract"]["R0"]["literal_bootstrap_files"][0]["relative_path"]
    (root / "public-source" / member).write_bytes(b"{}\n")
    args[-1] = "exporter-r0"
    failed_start = round(time.time(), 3)
    subprocess.run([*prefix, "supervise", *args], capture_output=True, text=True, check=True)
    failed_end = round(time.time(), 3)
    failure = json.loads((root / "exporter-r0-failure.json").read_bytes())
    assert failure["status"] == "STOP_NO_RETRY"
    assert failure["execution_identity"] == "topolab.v2.p17-m2-content-verified-input.v1"
    assert failure["helper_identity_relabelled"] is False
    assert failure["attempted_source_paths"] == [member]
    fact = failure["source_facts"][member]
    assert all(fact[k] is not None for k in ("declared", "before", "after", "closing"))
    assert fact["returned_bytes"] == 3
    assert failure["source_failures"] and failure["secondary_failures"] == []
    assert not (root / "content").exists()
    start = round(time.time(), 3)
    recorded = subprocess.run(
        [*prefix, "record", *args], capture_output=True, text=True, check=True
    )
    end = round(time.time(), 3)
    # Python-clock observations are unit inputs, not functions tool evidence.
    t0 = failed_start
    failed_events = [
        dict(
            event_id="failed-supervise",
            start_seconds=t0,
            end_seconds=failed_end,
            wall_seconds=failed_end - t0,
            clock_domain="functions.exec.Date.now.UTC-seconds",
            argv=[*prefix, "supervise", *args],
            complete=True,
            exit_code=0,
        ),
        dict(
            event_id="failed-record",
            start_seconds=start,
            end_seconds=end,
            wall_seconds=end - start,
            clock_domain="functions.exec.Date.now.UTC-seconds",
            argv=[*prefix, "record", *args],
            complete=True,
            exit_code=0,
            **observed_fields(recorded.stdout),
        ),
    ]
    private_events(root / "exporter-r0-events.json", failed_events)
    stopped = subprocess.run([*prefix, "bind", *args], capture_output=True, text=True)
    assert stopped.returncode == 1 and (root / "STOP.json").is_file()
    assert not (root / "active.json").exists()
    args[-1] = "shared-closeout"
    shared_start = round(time.time(), 3)
    shared = subprocess.run([*prefix, "supervise", *args], capture_output=True, text=True)
    shared_end = round(time.time(), 3)
    assert shared.returncode == 0, shared.stderr
    assert (root / "failed-prefix-backup-proof.json").is_file(), (
        root / "receipts/shared-closeout/shared-closeout/command.log"
    ).read_text()
    proof = json.loads((root / "failed-prefix-backup-proof.json").read_bytes())
    assert proof["status"] == "PUBLIC_FAILED_PREFIX_BACKUP_CHECKED"
    assert proof["input_version_accepted"] is False
    assert proof["old_original_reads"] == 0
    assert proof["member_count"] > 0
    event_start = round(time.time(), 3)
    wire = subprocess.run([*prefix, "record", *args], capture_output=True, text=True, check=True)
    event_end = round(time.time(), 3)
    t0 = shared_start
    shared_events = [
        dict(
            event_id="shared-supervise",
            start_seconds=t0,
            end_seconds=shared_end,
            wall_seconds=shared_end - t0,
            clock_domain="functions.exec.Date.now.UTC-seconds",
            argv=[*prefix, "supervise", *args],
            complete=True,
            exit_code=0,
        ),
        dict(
            event_id="shared-record",
            start_seconds=event_start,
            end_seconds=event_end,
            wall_seconds=event_end - event_start,
            clock_domain="functions.exec.Date.now.UTC-seconds",
            argv=[*prefix, "record", *args],
            complete=True,
            exit_code=0,
            **observed_fields(wire.stdout),
        ),
    ]
    private_events(root / "shared-closeout-events.json", shared_events)
    stopped = subprocess.run([*prefix, "bind", *args], capture_output=True, text=True)
    assert stopped.returncode == 1
    assert not (root / "active.json").exists()
    packet = json.loads((root / "shared-packet.json").read_bytes())
    assert set(packet["raw_packets"]) == {
        "independent-public-check",
        "exporter-r0",
        "shared-closeout",
    }
    assert packet["secondary_failures"]


def test_public_namespace_rejects_excess_evidence_before_creating_another_record(tmp_path):
    import json

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-file-cap"
    prefix = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*prefix, "prepare-public", "--root", str(root)], capture_output=True, text=True, check=True
    )
    digest = json.loads(prepared.stdout)["plan_sha256"]
    for index in range(513):
        (root / f"new-evidence-{index}").touch(mode=0o600)
    result = subprocess.run(
        [*prefix, "record", "--root", str(root), "--plan-sha", digest, "--role", "shared-closeout"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "EVIDENCE_FILE_CAP" in result.stderr
    assert not (root / "receipts/shared-closeout-collector.json").exists()


def test_shared_collector_write_error_still_returns_full_packet(tmp_path):
    import json

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-collector-write-error"
    prefix = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*prefix, "prepare-public", "--root", str(root)], capture_output=True, text=True, check=True
    )
    digest = json.loads(prepared.stdout)["plan_sha256"]
    (root / "receipts/shared-closeout-collector.json").mkdir(parents=True)
    result = subprocess.run(
        [*prefix, "record", "--root", str(root), "--plan-sha", digest, "--role", "shared-closeout"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    packet = json.loads(result.stdout)
    assert packet["pending"] == {}
    assert packet["completion"]["status"] == "FAILED_INTERNAL_COMPLETION"
    stages = {item["stage"] for item in packet["completion"]["secondary_failures"]}
    assert {"pending", "collect", "collector write"} <= stages
    assert packet["full_collector_record"]["sha256"] is None


@pytest.mark.parametrize(
    "fault", ["outer-watchdog", "outer-watchdog-missing-started", "outer-watchdog-corrupt-started"]
)
def test_public_outer_watchdog_reaps_registered_launch_once_and_keeps_stop(tmp_path, fault):
    import json
    import time

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-watchdog"
    prefix = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*prefix, "prepare-public", "--root", str(root), "--public-fault", fault],
        capture_output=True,
        text=True,
    )
    assert prepared.returncode == 0, prepared.stderr
    digest = json.loads(prepared.stdout)["plan_sha256"]
    args = ["--root", str(root), "--plan-sha", digest, "--role", "independent-public-check"]
    started = round(time.time(), 3)
    result = subprocess.run(
        [*prefix, "supervise", *args], capture_output=True, text=True, timeout=20
    )
    finished = round(time.time(), 3)
    events = [
        dict(
            event_id="supervise",
            start_seconds=started,
            end_seconds=finished,
            wall_seconds=finished - started,
            clock_domain="functions.exec.Date.now.UTC-seconds",
            argv=[*prefix, "supervise", *args],
            complete=True,
            exit_code=result.returncode,
        )
    ]
    assert result.returncode == 0, result.stderr
    sup = json.loads((root / "receipts/independent-public-check-supervisor.json").read_bytes())
    assert type(sup["exit_code"]) is int
    assert sup["watchdog_cleanup"]["group_gone"] is True
    assert sup["native"]["rss_bytes"] > 0
    for row in sup["watchdog_cleanup"]["observed"]:
        if row["pgid"] != sup["pid"]:
            import os

            with pytest.raises(ProcessLookupError):
                os.killpg(row["pgid"], 0)
    started = round(time.time(), 3)
    recorded = subprocess.run([*prefix, "record", *args], capture_output=True, text=True)
    finished = round(time.time(), 3)
    events.append(
        dict(
            event_id="record",
            start_seconds=started,
            end_seconds=finished,
            wall_seconds=finished - started,
            clock_domain="functions.exec.Date.now.UTC-seconds",
            argv=[*prefix, "record", *args],
            complete=True,
            exit_code=recorded.returncode,
            **observed_fields(recorded.stdout),
        )
    )
    private_events(root / "independent-public-check-events.json", events)
    packet = json.loads(recorded.stdout)
    assert packet["completion"]["domain_status"] != "PASS"
    assert packet["pending"]["frozen_FULL_seconds"] == 300
    assert packet["completion"]["observed_supervisor"]["exit_code"] == sup["exit_code"]
    # Missing inner resources cannot erase an independently observed outer span.
    (root / "receipts/independent-public-check/independent-public-check/command.time").unlink(
        missing_ok=True
    )
    bound = subprocess.run([*prefix, "bind", *args], capture_output=True, text=True)
    accepted = json.loads(bound.stdout)
    assert bound.returncode == 1
    assert accepted["whole_wall_seconds"] > 0
    assert accepted["known_cost_lower_bound_seconds"] >= 300
    assert any(e["stage"] == "inner resource evidence" for e in accepted["secondary_failures"])
    assert (root / "active.json").exists()  # missing exit/resources cannot admit shared


def test_known_lost_custody_lock_stops_public_payload_before_data_io(tmp_path):
    import json

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-lost-custody"
    prefix = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*prefix, "prepare-public", "--root", str(root)], capture_output=True, text=True, check=True
    )
    digest = json.loads(prepared.stdout)["plan_sha256"]
    (root / "content.cooperative-reader.lease").unlink()
    args = ["--root", str(root), "--plan-sha", digest, "--role", "independent-public-check"]
    subprocess.run([*prefix, "supervise", *args], capture_output=True, text=True, check=True)
    assert not (root / "independent-public-fixture").exists()
    failure = json.loads(
        (
            root / "receipts/independent-public-check/independent-public-check/command.log"
        ).read_bytes()
    )
    assert failure["status"] == "STOP_NO_RETRY"
    assert failure["primary_failure"]["stage"] == "custody hold"


@pytest.mark.parametrize("fault", ["native-cleanup", "accepted-write"])
def test_failed_native_or_filing_retains_stop_and_existing_accounting(tmp_path, fault):
    import json
    import time

    program = frozen_program(tmp_path)
    root = tmp_path / "topolab-public-untrusted-cleanup"
    prefix = [str(Path(sys.orig_argv[0]).resolve()), "-I", str(program)]
    prepared = subprocess.run(
        [*prefix, "prepare-public", "--root", str(root)], capture_output=True, text=True, check=True
    )
    digest = json.loads(prepared.stdout)["plan_sha256"]
    role = "independent-public-check"
    args = ["--root", str(root), "--plan-sha", digest, "--role", role]
    events = []
    for mode in ("supervise", "record"):
        command = [*prefix, mode, *args]
        start = round(time.time(), 3)
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        end = round(time.time(), 3)
        event = dict(
            event_id=mode,
            start_seconds=start,
            end_seconds=end,
            wall_seconds=end - start,
            clock_domain="functions.exec.Date.now.UTC-seconds",
            argv=command,
            complete=True,
            exit_code=0,
        )
        if mode == "record":
            event.update(observed_fields(result.stdout))
        events.append(event)
    private_events(root / (role + "-events.json"), events)
    if fault == "native-cleanup":
        native_path = root / "receipts" / role / role / "command.json"
        native = json.loads(native_path.read_bytes())
        native["cleanup"]["group_gone"] = False
        native_path.write_text(json.dumps(native))
    else:
        (root / (role + "-accepted.json")).mkdir(mode=0o700)
    result = subprocess.run([*prefix, "bind", *args], capture_output=True, text=True)
    assert result.returncode == 1
    if fault == "accepted-write":
        stopped = json.loads(result.stdout)
        assert stopped["whole_wall_seconds"] > 0
        assert stopped["known_cost_lower_bound_seconds"] >= 300
        assert stopped["full_role_evidence_accepted"] is False
        assert stopped["metadata_evidence_accepted"] is False
        assert stopped["primary_failure"]["stage"] == "bind persistence"
        assert stopped["primary_failure"]["type"] == "FileExistsError"
        assert (root / "STOP.json").is_file()
        args[-1] = "exporter-r0"
        source = subprocess.run([*prefix, "supervise", *args], capture_output=True, text=True)
        assert source.returncode != 0
        assert not (root / "registry.json").exists()
        return
    assert (root / "active.json").is_file()
    args[-1] = "shared-closeout"
    shared = subprocess.run([*prefix, "supervise", *args], capture_output=True, text=True)
    assert shared.returncode != 0
    assert not (root / "backup-prefix").exists()
