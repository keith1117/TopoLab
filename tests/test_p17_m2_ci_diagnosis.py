"""CI diagnostic CLI regressions use new public metadata, never experiment data."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/p17_m2_ci_diagnosis.py"
HEAD = "a" * 40


def test_successful_command_envelope_preserves_cancelled_step(tmp_path: Path) -> None:
    record = tmp_path / "command.json"
    log = tmp_path / "job.log"
    log.write_text("pytest public_case ...\nThe operation was canceled.\n")
    record.write_text(
        json.dumps(
            {
                "actual_exit": 0,
                "start_ns": 1793089072733275000,
                "stdout": json.dumps(
                    {
                        "headSha": HEAD,
                        "status": "completed",
                        "conclusion": "failure",
                        "jobs": [
                            {
                                "name": "quality",
                                "databaseId": 42,
                                "status": "completed",
                                "conclusion": "failure",
                                "steps": [
                                    {
                                        "name": "Run uv run pytest",
                                        "status": "completed",
                                        "conclusion": "cancelled",
                                    }
                                ],
                            }
                        ],
                    }
                ),
                "stderr": "",
            }
        )
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--run-record",
            str(record),
            "--job-log",
            str(log),
            "--expected-head",
            HEAD,
            "--expected-job-id",
            "42",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["classification"] == "CI_CANCELLATION_RECORDED"
    assert report["run_conclusion"] == "failure"
    assert report["pytest_conclusion"] == "cancelled"
    assert report["cancellation_cause"] == "UNKNOWN"
    assert report["input_accepted"] is False
    assert report["seed17_repaired"] is False
    assert report["own_future_tool_exit"] == "NOT_CLAIMED"


@pytest.mark.parametrize("actual_exit", [2, None, False, "0"])
def test_failed_or_unobserved_command_does_not_attest_stdout(
    tmp_path: Path,
    actual_exit: object,
) -> None:
    record = tmp_path / "command.json"
    log = tmp_path / "job.log"
    log.write_text("The operation was canceled.\n")
    record.write_text(
        json.dumps(
            {
                "actual_exit": actual_exit,
                "start_ns": 1793089072733275000,
                "stdout": json.dumps(
                    {
                        "headSha": HEAD,
                        "conclusion": "failure",
                        "jobs": [
                            {
                                "name": "quality",
                                "databaseId": 42,
                                "steps": [{"name": "Run uv run pytest", "conclusion": "cancelled"}],
                            }
                        ],
                    }
                ),
            }
        )
    )
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--run-record",
            str(record),
            "--job-log",
            str(log),
            "--expected-head",
            HEAD,
            "--expected-job-id",
            "42",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["classification"] == "DIAGNOSTIC_INPUT_REJECTED"
    assert report["error"] == "COMMAND_EXIT_NOT_SUCCESSFUL"
    assert report["command_actual_exit"] == actual_exit
    assert report["command_start_ns"] == 1793089072733275000
    assert len(report["run_record_sha256"]) == 64
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "value,error",
    [
        ({"actual_exit": 0, "stdout": None}, "STDOUT_NOT_TEXT"),
        ({"actual_exit": 0, "stdout": []}, "STDOUT_NOT_TEXT"),
        ({"headSha": HEAD, "jobs": None}, "JOBS_NOT_OBJECT_LIST"),
        ({"headSha": HEAD, "jobs": [None]}, "JOBS_NOT_OBJECT_LIST"),
        (
            {"headSha": HEAD, "jobs": [{"name": "quality", "databaseId": 42}]},
            "STEPS_NOT_OBJECT_LIST",
        ),
    ],
)
def test_malformed_record_retains_structured_failure(
    tmp_path: Path,
    value: object,
    error: str,
) -> None:
    record = tmp_path / "command.json"
    log = tmp_path / "job.log"
    record.write_text(json.dumps(value))
    log.write_text("")
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--run-record",
            str(record),
            "--job-log",
            str(log),
            "--expected-head",
            HEAD,
            "--expected-job-id",
            "42",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"] == error
    assert "Traceback" not in result.stderr


@pytest.mark.parametrize(
    "defect,error",
    [
        ("head", "HEAD_MISMATCH"),
        ("job_id", "JOB_ID_MISMATCH"),
        ("missing_job", "QUALITY_JOB_NOT_UNIQUE"),
        ("duplicate_job", "QUALITY_JOB_NOT_UNIQUE"),
        ("missing_step", "PYTEST_STEP_NOT_UNIQUE"),
        ("duplicate_step", "PYTEST_STEP_NOT_UNIQUE"),
        ("malformed_stdout", "INVALID_JSON"),
        ("non_object", "RUN_RECORD_NOT_OBJECT"),
    ],
)
def test_diagnostic_refuses_missing_or_conflicting_binding(
    tmp_path: Path,
    defect: str,
    error: str,
) -> None:
    payload = {
        "headSha": HEAD,
        "status": "completed",
        "conclusion": "failure",
        "jobs": [
            {
                "name": "quality",
                "databaseId": 42,
                "steps": [{"name": "Run uv run pytest", "conclusion": "cancelled"}],
            }
        ],
    }
    if defect == "head":
        payload["headSha"] = "b" * 40
    elif defect == "job_id":
        payload["jobs"][0]["databaseId"] = 43
    elif defect == "missing_job":
        payload["jobs"] = []
    elif defect == "duplicate_job":
        payload["jobs"] *= 2
    elif defect == "missing_step":
        payload["jobs"][0]["steps"] = []
    elif defect == "duplicate_step":
        payload["jobs"][0]["steps"] *= 2
    record = tmp_path / "command.json"
    log = tmp_path / "job.log"
    log.write_text("The runner has received a shutdown signal.\n")
    stdout = "not-json" if defect == "malformed_stdout" else json.dumps(payload)
    if defect == "non_object":
        stdout = "[]"
    record.write_text(json.dumps({"actual_exit": 0, "stdout": stdout}))
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--run-record",
            str(record),
            "--job-log",
            str(log),
            "--expected-head",
            HEAD,
            "--expected-job-id",
            "42",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    report = json.loads(result.stdout)
    assert report["error"] == error
    assert report["classification"] == "DIAGNOSTIC_INPUT_REJECTED"
    assert report["input_accepted"] is False
    assert len(report["job_log_sha256"]) == 64
    assert "Traceback" not in result.stderr
