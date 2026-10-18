"""New public subprocess fixtures; no old runs or scientific quota consumption."""

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def control(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "scripts"))
    return importlib.import_module("p17_m2_resource_control")


def test_native_explicit_units(control):
    darwin = " 0.02 real 0.01 user 0.00 sys\n 123456 maximum resident set size\n"
    assert control.native(darwin, "darwin")["rss_bytes"] == 123456
    assert control.native("TOPOLAB_NATIVE 0.02 0.01 0.00 1234", "linux")["rss_bytes"] == 1263616
    for text, platform in (
        (darwin, "unknown"),
        ("", "darwin"),
        ("TOPOLAB_NATIVE 1 0 0 0", "linux"),
    ):
        with pytest.raises(ValueError, match="RESOURCE_UNKNOWN_STOP"):
            control.native(text, platform)


def test_charge_missing_is_never_zero(control):
    assert control.role_charge(4.0, 5.0, 3, 6.0) == 18.0
    assert control.role_charge(4.0, 5.0, 3, 20.0) == 20.0
    for values in ((None, 5, 3, 2), (4, float("nan"), 3, 2), (4, 5, True, 2)):
        with pytest.raises(ValueError):
            control.role_charge(*values)


def test_registered_rss_overlap_and_missing_role(control):
    roles = [
        {
            "role": name,
            "exit_code": 0,
            "group_gone": True,
            "native_rss_bytes": peak,
            "sampled_rss_bytes": peak,
            "profile_sha256": "a" * 64,
        }
        for name, peak in (("candidate", 100), ("auditor", 200))
    ]
    assert control.rss_envelope(roles, [["candidate", "auditor"]]) == 300
    with pytest.raises(ValueError):
        control.rss_envelope(roles, [["candidate"], ["auditor"]])
    with pytest.raises(ValueError):
        control.rss_envelope([{**roles[0], "group_gone": None}], [["candidate"]])


def test_real_new_public_command_and_immutable_prefix(control, tmp_path):
    result = control.invoke(
        tmp_path,
        "short-public",
        [sys.executable, "-c", "print('new fixture')"],
        timeout=10,
        interval=0.05,
    )
    root = tmp_path / "short-public"
    assert result["software_result"] == "PUBLIC_COMMAND_EXIT_OBSERVED"
    assert result["status"] == "PENDING_POSTEXIT"
    assert result["cleanup"]["group_gone"] is True
    assert result["native"]["rss_bytes"] > 0
    assert result["helpers"] and result["samples"]
    assert all(
        s["group_plus_controller_rss_bytes"]
        == s["controller_rss_bytes"] + sum(r["rss_bytes"] for r in s["roles"])
        for s in result["samples"]
    )
    assert all(h["cleanup"]["group_gone"] for h in result["helpers"])
    assert json.loads((root / "pending.json").read_text())["status"] == "PENDING_BEFORE_INTERPRETER"
    assert result["controller_complete_exit"] == "UNKNOWN_PENDING_OUTER_PROFILE"
    assert result["scientific_resource_admission"] == "NOT_RUN"
    with pytest.raises(FileExistsError):
        control.invoke(tmp_path, "short-public", [sys.executable, "-c", "pass"], timeout=10)


def test_timeout_terminates_public_group(control, tmp_path):
    result = control.invoke(
        tmp_path,
        "timeout-public",
        [sys.executable, "-c", "import time; time.sleep(5)"],
        timeout=0.1,
        interval=0.05,
    )
    assert result["software_result"] == "STOP_SCOPE_OR_WORK_CAP"
    assert result["cleanup"]["group_gone"]
    assert result["exit_code"] != 0


def test_resource_cap_without_large_allocation(control, tmp_path):
    result = control.invoke(
        tmp_path,
        "cap-public",
        [sys.executable, "-c", "import time; time.sleep(5)"],
        timeout=10,
        limit_bytes=1,
        interval=0.05,
    )
    assert result["software_result"] == "FAIL_RESOURCE_CAP"
    assert result["cleanup"]["group_gone"]


def test_nonzero_exit_is_fatal_public_result(control, tmp_path):
    result = control.invoke(
        tmp_path,
        "failed-public",
        [sys.executable, "-c", "raise MemoryError('fixture')"],
        timeout=10,
        interval=0.05,
    )
    assert result["software_result"] == "FAIL_PUBLIC_COMMAND"
    assert result["exit_code"] != 0
    assert result["scientific_resource_admission"] == "NOT_RUN"


def test_postexit_peak_can_fail_with_exit_zero(control, tmp_path, monkeypatch):
    # Stub only the small measurement records; the child still really exits.
    def snapshot(root, index, pgid, known_pids):
        return [], {
            "role": f"sampler-{index}",
            "problem": None,
            "native": {"rss_bytes": 1},
            "timer_native_exit": {"native": {"rss_bytes": 1}},
            "cleanup": {"group_gone": True},
        }

    monkeypatch.setattr(control, "_snapshot", snapshot)
    monkeypatch.setattr(
        control, "native", lambda *args: {"wall_seconds": 0.01, "rss_bytes": control.LIMIT + 1}
    )
    result = control.invoke(
        tmp_path, "postexit-public", [sys.executable, "-c", "pass"], timeout=10, interval=0.05
    )
    assert result["exit_code"] == 0
    assert result["software_result"] == "FAIL_RESOURCE_CAP"


def test_sampler_failure_preserves_stop_and_exit(control, tmp_path, monkeypatch):
    def failed(*args):
        raise ValueError("new public sampler failure")

    monkeypatch.setattr(control, "_snapshot", failed)
    result = control.invoke(
        tmp_path, "sampler-failed", [sys.executable, "-c", "import time; time.sleep(5)"], timeout=10
    )
    assert result["software_result"] == "RESOURCE_UNKNOWN_STOP"
    assert result["cleanup"]["group_gone"]


def test_formal_cli_options_refuse_before_launch(control, tmp_path, monkeypatch):
    monkeypatch.setattr(control, "invoke", lambda *a, **k: pytest.fail("launched"))
    with pytest.raises(SystemExit):
        control.main(["--preflight", "--output", str(tmp_path / "denied")])


def test_unregistered_public_descendant_is_stopped(control, tmp_path):
    code = (
        "import subprocess,sys,time; "
        "subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)']); "
        "time.sleep(10)"
    )
    result = control.invoke(
        tmp_path, "extra-child", [sys.executable, "-c", code], timeout=5, interval=0.05
    )
    assert result["software_result"] == "RESOURCE_UNKNOWN_STOP_UNREGISTERED_DESCENDANT"
    assert result["exit_code"] != 0
    assert result["scientific_resource_admission"] == "NOT_RUN"


def test_new_public_exit_bindings_only(control, tmp_path):
    root = tmp_path / "registered-new-public"
    (root / "public-candidate").mkdir(parents=True)
    control.atomic_new(
        root / "stage-a-root.json",
        {
            "schema": control.VERSION,
            "software_only": True,
            "input_scope": "new public fixtures only",
        },
    )
    record = root / "public-candidate/command.json"
    control.atomic_new(
        record, {"schema": control.VERSION, "software_only": True, "status": "PENDING_POSTEXIT"}
    )
    text = "0.1 real 0.0 user 0.0 sys\n1024 maximum resident set size\n"
    if sys.platform == "linux":
        text = "TOPOLAB_NATIVE 0.1 0.0 0.0 1\n"
    for label in ("controller", "binder", "verifier"):
        (root / (label + ".time")).write_text(text)
        (root / (label + ".log")).write_text("new public log\n")
    first = control.bind_exit(
        root / "controller-exit.json",
        record,
        root / "controller.time",
        root / "controller.log",
        0,
        label="controller",
        root=root,
    )
    assert first["status"] == "PENDING_BINDER_EXIT"
    second = control.bind_exit(
        root / "binder-exit.json",
        root / "controller-exit.json",
        root / "binder.time",
        root / "binder.log",
        0,
        label="binder",
        root=root,
    )
    assert second["status"] == "PENDING_VERIFIER_EXIT"
    assert json.loads(record.read_text())["status"] == "PENDING_POSTEXIT"
    with pytest.raises(PermissionError):
        control.bind_exit(
            root / "verifier-exit.json",
            tmp_path / "old-input.json",
            root / "verifier.time",
            root / "verifier.log",
            0,
            label="verifier",
            root=root,
        )
    # No unrestricted binding command can read caller-selected old paths.
    with pytest.raises(SystemExit):
        control.main(["bind-exit", "--record", str(tmp_path / "old-input.json")])
