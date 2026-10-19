"""Public fake receipts only; no actual source IO or role launch."""

import importlib.util
import json
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "r_control", Path(__file__).parents[1] / "scripts/p17_m2_input_export_control.py"
)
assert SPEC and SPEC.loader
c = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c)


def test_isolated_entry_imports_only_stdlib():
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "-I", str(Path(c.__file__)), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0 and "supervise" in result.stdout


def test_binding_rejects_missing_exit_and_rss(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "ROOT", tmp_path)
    role = "exporter-r0"
    folder = tmp_path / "receipts" / role / role
    folder.mkdir(parents=True)
    record = {
        "exit_code": 0,
        "software_result": "PUBLIC_COMMAND_EXIT_OBSERVED",
        "cleanup": {"group_gone": True},
        "argv": ["public"],
        "native": {"wall_seconds": 0.2},
        "observed_outer_wall_seconds": 0.3,
        "timer_native_exit": {"native": {"rss_bytes": 100}},
        "native_plus_controller_and_sampler_rss_bytes": 1000,
    }
    (folder / "command.json").write_text(json.dumps(record))
    (tmp_path / "receipts" / f"{role}-controller.time").write_text("new")
    monkeypatch.setattr(
        c.native_recording, "native", lambda *_: {"wall_seconds": 0.5, "rss_bytes": 2000}
    )
    (folder / "command.time").write_text("new")
    (folder / "command.log").write_bytes(b"")
    record["helpers"] = []
    (folder / "command.json").write_text(json.dumps(record))
    monkeypatch.setattr(
        c.independent, "audit_native_record", lambda *a, **k: {"inner_empirical_RSS_bytes": 1000}
    )
    plan = {"roles": {role: {"argv": ["public"]}}}
    with pytest.raises(ValueError, match="exit"):
        c.bind(plan, role, None, "a" * 64)
    result = c.bind(plan, role, 0, "a" * 64)
    assert result["plan_sha256"] == "a" * 64 and result["conservative_RSS_bytes"] == 3000
    assert result["charge_before_binder_wall_seconds"] == 10.5
    assert result["status"] == "PENDING_BINDER_NATIVE_EXIT"


def test_missing_source_freeze_refuses(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "ROOT", tmp_path)
    plan = {"source_files": {}, "merged_source": "publichead"}
    raw = c.canonical(plan)
    p = tmp_path / "launch_plan.json"
    p.write_bytes(raw)
    monkeypatch.setattr(
        c.subprocess, "check_output", lambda argv, **_: b"" if "status" in argv else b"publichead\n"
    )
    with pytest.raises(ValueError, match="complete source freeze"):
        c.plan_checked(p, c.digest(raw))


@pytest.mark.skipif(c.sys.platform != "darwin", reason="Darwin native-time public adapter")
def test_supervisor_real_timer_wait4_new_fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "ROOT", tmp_path)
    original = c.subprocess.Popen

    def public_child(argv, **kwargs):
        # Substitute only the child payload with a new printing fixture. Keep the
        # real registered outer time helper, os.wait4 and supervisor bookkeeping.
        return original(argv[:5] + ["-I", "-c", "print('new public supervisor fixture')"], **kwargs)

    monkeypatch.setattr(c.subprocess, "Popen", public_child)
    monkeypatch.setattr(c, "bind", lambda *a, **k: {"conservative_RSS_bytes": 1024})
    result = c.supervise({}, "exporter-r0", "a" * 64)
    assert result["outer_timer_exit"] == 0 and result["outer_timer_native_rss_bytes"] > 0
    assert result["supervisor_rss_after_verification_bytes"] > 0
    assert result["supervisor_complete_exit"] == "PENDING_EXTERNAL_CALLER_OBSERVATION"
    assert (tmp_path / "receipts/exporter-r0-last-rss.json").is_file()


def test_timeout_closes_registered_sessions(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "ROOT", tmp_path)
    role = "exporter-r0"
    folder = tmp_path / "receipts" / role / role
    folder.mkdir(parents=True)
    (folder / "started.json").write_text(
        json.dumps({"role": role, "status": "STARTED", "pid": 98762})
    )
    monkeypatch.setattr(
        c.native_recording,
        "_snapshot",
        lambda *a, **k: ([{"pgid": 98763}], {"native": {"rss_bytes": 1024}}),
    )
    killed = []

    def kill(group, sig):
        if sig == 0:
            raise ProcessLookupError()
        killed.append((group, sig))

    monkeypatch.setattr(c.os, "killpg", kill)
    result = c.stop_registered(role, 98761)
    assert {group for group, sig in killed} == {98761, 98762, 98763}
    assert all(row["group_gone"] for row in result["registered_groups"])
    assert result["complete_exit"] is False  # requires actual parent reap/observer
