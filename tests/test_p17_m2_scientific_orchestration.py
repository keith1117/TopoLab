"""Public actual resource/exit fixtures for the separately gated scientific adapter."""

import importlib.util
import json
import sys
from pathlib import Path
from time import monotonic
from types import SimpleNamespace

import pytest


def load():
    path = Path(__file__).parents[1] / "scripts/p17_m2_scientific_orchestration.py"
    spec = importlib.util.spec_from_file_location("scientific_orchestration_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_new_native_log_reader_accepts_real_empty_log_but_old_source_reader_refuses(tmp_path):
    module = load()
    path = tmp_path / "new-native.log"
    path.write_bytes(b"")
    raw, facts = module.read_native_log(path)
    assert raw == b"" and facts["returned_bytes"] == 0
    assert facts["before"] == facts["after"] == facts["closing"]
    old = module.load("p17_m2_input_export_independent").OnceReader(tmp_path, 1, 100)
    with pytest.raises(ValueError, match="byte cap"):
        old.read(path.name, 100)
    with pytest.raises(FileNotFoundError):
        module.read_native_log(tmp_path / "absent.log")


def test_new_native_log_reader_retains_raw_observations_on_inode_replacement(tmp_path, monkeypatch):
    module = load()
    path = tmp_path / "new-native.log"
    path.write_bytes(b"")
    real_close = module.os.close
    replaced = False

    def replacing(fd):
        nonlocal replaced
        if not replaced and module.os.fstat(fd).st_ino == path.stat().st_ino:
            replacement = tmp_path / "new-replacement.log"
            replacement.write_bytes(b"")
            replacement.replace(path)
            replaced = True
        return real_close(fd)

    monkeypatch.setattr(module.os, "close", replacing)
    with pytest.raises(ValueError, match="NATIVE_LOG_IDENTITY_CHANGED") as caught:
        module.read_native_log(path)
    facts = caught.value.native_log_facts
    assert facts["before"]["st_ino"] != facts["closing"]["st_ino"]
    assert facts["returned_bytes"] == 0


@pytest.mark.parametrize("exit_code", [0, 7])
def test_native_dispatch_closes_timer_wait4_and_actual_empty_log(tmp_path, monkeypatch, exit_code):
    module = load()
    resource, _ = module.native_helpers()
    profile = tmp_path / "controller.time"
    command = resource._timed(
        [sys.executable, "-I", "-c", "raise SystemExit(" + str(exit_code) + ")"], profile
    )
    dispatch = [sys.executable, "-I", "registered-public-dispatch.py"]
    monkeypatch.setattr(sys, "orig_argv", dispatch)
    spec = {
        "dispatch_argv": dispatch,
        "profile_path": str(profile),
        "log_path": str(tmp_path / "controller.log"),
        "dispatch_path": str(tmp_path / "controller.dispatch.json"),
        "timeout_seconds": 10,
    }
    contract = {
        "runtime": {"python_entry": sys.executable, "python_startup_entry": sys.executable},
        "roles": {
            "resource-preflight": {
                "FULL_seconds": 10,
                "exit_argv": {"controller": command},
                "native_dispatch": {"controller": spec},
            }
        },
    }
    packet = module.observe_native(contract, "a" * 64, "resource-preflight", "controller")
    assert packet["exit_code"] == exit_code
    assert packet["timer_native_exit"]["exit_code"] == exit_code
    assert packet["native_pid"] == packet["timer_native_exit"]["pid"]
    assert packet["timer_native_exit"]["statistics_source"] == "os.wait4"
    assert packet["timer_native_exit"]["native"]["rss_bytes"] > 0
    assert packet["self_rss_bytes_before_flush"] > 0
    assert packet["self_rss_bytes_after_flush"] > 0
    assert packet["group_gone"] is True and packet["cleanup_errors"] == []
    assert Path(spec["log_path"]).read_bytes() == b""
    assert json.loads(Path(spec["dispatch_path"]).read_bytes()) == packet


def test_native_dispatch_timeout_closes_launch_and_retains_failure(tmp_path, monkeypatch):
    module = load()
    resource, _ = module.native_helpers()
    profile = tmp_path / "controller.time"
    command = resource._timed([sys.executable, "-I", "-c", "import time;time.sleep(10)"], profile)
    dispatch = [sys.executable, "-I", "registered-public-dispatch.py"]
    monkeypatch.setattr(sys, "orig_argv", dispatch)
    spec = {
        "dispatch_argv": dispatch,
        "profile_path": str(profile),
        "log_path": str(tmp_path / "controller.log"),
        "dispatch_path": str(tmp_path / "controller.dispatch.json"),
        "timeout_seconds": 0.2,
    }
    contract = {
        "runtime": {"python_entry": sys.executable, "python_startup_entry": sys.executable},
        "roles": {
            "resource-preflight": {
                "FULL_seconds": 10,
                "exit_argv": {"controller": command},
                "native_dispatch": {"controller": spec},
            }
        },
    }
    packet = module.observe_native(contract, "a" * 64, "resource-preflight", "controller")
    assert packet["status"] == "STOP_OUTER_TIMEOUT"
    assert packet["exit_code"] != 0 and packet["group_gone"] is True
    assert packet["timer_native_exit"]["statistics_source"] == "os.wait4"
    assert packet["cleanup"]["group_gone"] is True


def test_native_dispatch_closes_owned_timer_even_when_cleanup_poll_raises(tmp_path, monkeypatch):
    module = load()
    resource, _ = module.native_helpers()
    actual_poll, actual_terminate = resource._native_poll, resource._terminate
    state = {"polls": 0, "terminated": False}

    def poll(child):
        state["polls"] += 1
        if state["polls"] in (1, 2):
            raise OSError("new public wait4 observation failure")
        return actual_poll(child)

    def terminate(group, child):
        state["terminated"] = True
        return actual_terminate(group, child)

    monkeypatch.setattr(resource, "_native_poll", poll)
    monkeypatch.setattr(resource, "_terminate", terminate)
    profile = tmp_path / "controller.time"
    command = resource._timed([sys.executable, "-I", "-c", "import time;time.sleep(.1)"], profile)
    dispatch = [sys.executable, "-I", "registered-public-dispatch.py"]
    monkeypatch.setattr(sys, "orig_argv", dispatch)
    spec = {
        "dispatch_argv": dispatch,
        "profile_path": str(profile),
        "log_path": str(tmp_path / "controller.log"),
        "dispatch_path": str(tmp_path / "controller.dispatch.json"),
        "timeout_seconds": 10,
    }
    contract = {
        "runtime": {"python_entry": sys.executable, "python_startup_entry": sys.executable},
        "roles": {
            "resource-preflight": {
                "FULL_seconds": 10,
                "exit_argv": {"controller": command},
                "native_dispatch": {"controller": spec},
            }
        },
    }
    packet = module.observe_native(contract, "a" * 64, "resource-preflight", "controller")
    assert state["terminated"] is True and packet["group_gone"] is True
    assert packet["status"] == "STOP_NATIVE_DISPATCH"
    assert any("wait4 observation" in v["reason"] for v in packet["cleanup_errors"])


def test_native_dispatch_caps_stdout_before_persisting_unbounded_output(tmp_path, monkeypatch):
    module = load()
    resource, _ = module.native_helpers()
    profile = tmp_path / "controller.time"
    command = resource._timed(
        [sys.executable, "-I", "-c", 'import os,time;os.write(1,b"x"*(5*1024**2));time.sleep(10)'],
        profile,
    )
    dispatch = [sys.executable, "-I", "registered-public-dispatch.py"]
    monkeypatch.setattr(sys, "orig_argv", dispatch)
    spec = {
        "dispatch_argv": dispatch,
        "profile_path": str(profile),
        "log_path": str(tmp_path / "controller.log"),
        "dispatch_path": str(tmp_path / "controller.dispatch.json"),
        "timeout_seconds": 10,
    }
    contract = {
        "runtime": {"python_entry": sys.executable, "python_startup_entry": sys.executable},
        "roles": {
            "resource-preflight": {
                "FULL_seconds": 10,
                "exit_argv": {"controller": command},
                "native_dispatch": {"controller": spec},
            }
        },
    }
    packet = module.observe_native(contract, "a" * 64, "resource-preflight", "controller")
    assert packet["status"] == "STOP_NATIVE_DISPATCH" and packet["group_gone"] is True
    assert Path(spec["log_path"]).stat().st_size == 4 * 1024**2
    assert any("LOG4MIB_CAP" in v["reason"] for v in packet["cleanup_errors"])


def test_public_preflight_retains_actual_success_and_failure_exit_controls(tmp_path):
    module = load()
    proof = module.public_preflight(tmp_path / "new-public-native-preflight")
    assert proof["status"] == "PUBLIC_PREFLIGHT_CONTROLS_OBSERVED"
    assert proof["old_input_reads"] == 0
    assert [row["name"] for row in proof["cases"]] == ["success", "exit-seven", "timeout"]
    assert proof["cases"][0]["record"]["exit_code"] == 0
    assert proof["cases"][1]["record"]["exit_code"] == 7
    assert proof["cases"][2]["record"]["exit_code"] != 0
    assert all(row["record"]["cleanup"]["group_gone"] for row in proof["cases"])
    assert all(row["independent_audit"]["software_record_consistent"] for row in proof["cases"])


def test_public_preflight_refuses_symlink_parent_before_creating_destination(tmp_path):
    module = load()
    destination = tmp_path / "new-public-destination"
    destination.mkdir()
    alias = tmp_path / "new-public-alias"
    alias.symlink_to(destination, target_is_directory=True)
    with pytest.raises((OSError, ValueError)):
        module.public_preflight(alias / "must-remain-absent")
    assert not (destination / "must-remain-absent").exists()


def test_scientific_runtime_refuses_wrong_editable_package_origin(tmp_path, monkeypatch):
    module = load()
    actual = module.importlib.util.find_spec
    wrong = tmp_path / "new-public-other-package.py"
    wrong.write_text("# new public origin mismatch\n")
    monkeypatch.setattr(
        module.importlib.util,
        "find_spec",
        lambda name: SimpleNamespace(origin=str(wrong)) if name == "topolab" else actual(name),
    )
    with pytest.raises(ValueError, match="TOPOLOGY_PACKAGE_ORIGIN_CHANGED"):
        module.scientific_runtime()


def test_controller_failure_keeps_actual_producer_context_and_secondary_errors(tmp_path, capsys):
    module = load()
    (tmp_path / "rows").mkdir()
    context = {
        "input_failure": {
            "member": "new-public-input.json",
            "source_facts": [
                {"before_read": {"st_dev": 1, "st_ino": 2, "st_size": 3, "st_mtime_ns": 89}}
            ],
        }
    }
    (tmp_path / "rows/producer-stop-context.json").write_text(json.dumps(context))
    (tmp_path / "rows/auditor-failure.json").write_bytes(b"{")
    primary = ValueError("original new public child failure")
    packet = module.retain_controller_failure(
        tmp_path,
        "scientific-producer",
        "a" * 64,
        {"FULL_seconds": 10800},
        primary,
        began=monotonic(),
        cases=[{"exit_code": 1}],
    )
    assert packet["reason"] == str(primary)
    assert packet["retained_context"][0]["packet"] == context
    assert packet["completed_native_cases"] == [{"exit_code": 1}]
    assert packet["secondary_errors"][0]["stage"] == "rows/auditor-failure.json"
    assert packet["known_charge_lower_bound_seconds"] >= 10800
    assert packet["actual_own_return"] == "UNKNOWN_PENDING_ACTUAL_OUTER_TOOL_RETURN"
    assert json.loads(capsys.readouterr().err)["reason"] == str(primary)


def test_payload_failure_emits_all_source_facts_when_context_filing_fails(
    tmp_path, capsys, monkeypatch
):
    module = load()
    primary = OSError("original source closing observation missing")
    primary.scientific_stop_context = {
        "input_source_facts": [{"mtime_ns": 89}],
        "secondary_errors": [{"reason": "original writer full"}],
    }
    helper = module.load("p17_m2_content_verified_control")
    monkeypatch.setattr(helper, "put", lambda *a: (_ for _ in ()).throw(OSError("disk full")))
    packet = module.retain_payload_failure(
        tmp_path,
        "scientific-producer",
        "a" * 64,
        primary,
        certificate=None,
        lease=None,
        consumer=None,
        began=monotonic(),
    )
    returned = json.loads(capsys.readouterr().err)
    assert returned == packet
    assert returned["reason"] == str(primary)
    assert (
        returned["retained_context"]["scientific_stop_context"] == primary.scientific_stop_context
    )
    assert returned["secondary_errors"][0]["reason"] == "disk full"
    assert packet["own_future_exit"] == "UNKNOWN_PENDING_ACTUAL_NATIVE_RETURN"


def test_payload_cannot_start_without_the_registered_native_parent(tmp_path):
    module = load()
    with pytest.raises((ValueError, FileNotFoundError)):
        module.check_payload_start(
            {
                "roles": {
                    "scientific-producer": {
                        "root": str(tmp_path),
                        "inner_starts": [
                            {"name": "scientific-payload", "argv": ["unregistered-public-command"]}
                        ],
                    }
                }
            },
            "a" * 64,
            "scientific-producer",
        )


def test_framework_startup_argv_keeps_both_frozen_entries_and_exact_remaining_words():
    module = load()
    runtime = {
        "python_entry": "/new-public/venv/bin/python",
        "python_startup_entry": "/new-public/framework-app/Python",
    }
    command = [
        "/new-public/venv/bin/python",
        "-I",
        "new-public-command.py",
        "--sha",
        "@SCIENTIFIC_CONTRACT_SHA256@",
    ]
    assert module.startup_argv(command, "a" * 64, runtime) == [
        "/new-public/framework-app/Python",
        "-I",
        "new-public-command.py",
        "--sha",
        "a" * 64,
    ]
    with pytest.raises(ValueError, match="FROZEN_LOGICAL_PYTHON_ENTRY_REQUIRED"):
        module.startup_argv(["/unregistered/python", *command[1:]], "a" * 64, runtime)
