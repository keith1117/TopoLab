"""An oversized C failure must still have an actual native EXIT and a closed profile."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]


def test_failed_c_diagnostic_pipe_closes_without_losing_timer_profile(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location(
        "test_c_failure_adapter", REPO / "scripts/p17_m2_scientific_orchestration.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    resource, _ = module.native_helpers()
    profile = tmp_path / "controller.time"
    log = tmp_path / "controller.log"
    destination = tmp_path / "controller.dispatch.json"
    (tmp_path / "controller-failure.json").write_text('{"status":"STOP_NO_RETRY"}\n')
    count = 5 * 1024**2
    command = resource._timed(
        [
            sys.executable,
            "-I",
            "-c",
            f'import sys;sys.stderr.buffer.write(b"x"*{count});sys.exit(7)',
        ],
        profile,
    )
    dispatch = [sys.executable, "-I", "public-stop-only.py"]
    monkeypatch.setattr(sys, "orig_argv", dispatch)
    role = "scientific-producer"
    paths = dict(
        profile_path=str(profile),
        dispatch_path=str(destination),
        log_path=str(log),
        dispatch_argv=dispatch,
        timeout_seconds=10,
    )
    contract = {
        "roles": {
            role: {
                "FULL_seconds": 10,
                "native_dispatch": {"controller": paths},
                "exit_argv": {"controller": command},
            }
        },
        "runtime": {"python_entry": sys.executable, "python_startup_entry": sys.executable},
    }
    packet = module.observe_native(contract, "a" * 64, role, "controller")
    assert packet["status"] == "STOP_NATIVE_DISPATCH"
    assert packet["timer_native_exit"]["exit_code"] == packet["exit_code"] == 7
    assert packet["timer_native_exit"]["statistics_source"] == "os.wait4"
    assert packet["group_gone"] is True and packet["cleanup"]["signals"] == []
    assert packet["stdout_observed_bytes"] == count
    assert packet["stdout_retained_bytes"] == log.stat().st_size == 4 * 1024**2
    assert packet["stdout_observed_truncated_bytes"] == 1024**2
    assert packet["unobserved_stdout_after_cap"] == "DRAINED_TO_EOF"
    assert [e["reason"] for e in packet["cleanup_errors"]] == ["NEW_NATIVE_LOG4MIB_CAP"]
    assert resource.native(profile.read_text(), sys.platform)["rss_bytes"] > 0
    assert hashlib.sha256(profile.read_bytes()).hexdigest() == packet["profile_sha256"]
    assert json.loads(destination.read_bytes()) == packet


@pytest.mark.parametrize(
    "stage,progress,counts",
    [
        ("BEFORE_PANEL", {}, (0, 0, 20, 0)),
        (None, {}, (None, None, None, None)),
        (
            None,
            {"attempted_rows": 2, "completed_rows": [{}], "internal_row_charge_seconds": 3.25},
            (2, 1, 18, 3.25),
        ),
    ],
)
def test_stopped_row_accounting_preserves_observations(stage, progress, counts):
    path = REPO / "scripts/native_c_stop.py"
    spec = importlib.util.spec_from_file_location("test_row_stop_metadata", path)
    metadata = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(metadata)
    payload = {
        "error_type": "OSError",
        "reason": "public failure",
        "row_execution_stage": stage,
        "retained_context": {"scientific_failure": progress},
    }
    packet = {
        "retained_context": [
            {"path": "payload-failure.json", "packet": payload, "raw_sha256": "b" * 64}
        ],
        "scientific_contract_sha256": "a" * 64,
        "role": "scientific-producer",
        "secondary_errors": [],
    }
    header = metadata.metadata(packet, planned_rows=20, original=b"public raw")
    fields = (
        "attempted_rows",
        "fully_filed_rows",
        "unattempted_rows",
        "internal_row_charge_seconds",
    )
    assert tuple(header[f] for f in fields) == counts
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node required for independent API-side row accounting")
    code = (
        "import {stoppedRows} from './scripts/native_c_stop.mjs';"
        "console.log(JSON.stringify(stoppedRows(JSON.parse(process.argv[1]),20,10)))"
    )
    result = subprocess.run(
        [node, "--input-type=module", "-e", code, json.dumps(header)],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=True,
    )
    received = json.loads(result.stdout)
    assert tuple(received[f] for f in fields) == counts
    assert received["known_role_charge_seconds"] == (None if counts[0] is None else 20 + counts[0])
    assert received["measured_role_charge_lower_bound_seconds"] >= 20
