"""Diagnose recorded CI status without granting scientific acceptance.

Accept the JSON from ``gh run view --json headSha,status,conclusion,jobs`` or a
successful recorded command whose stdout contains that JSON. The caller retains
the command's actual return; this report cannot attest to its own future return.
"""

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-record", required=True)
    parser.add_argument("--job-log", required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--expected-job-id", type=int, required=True)
    args = parser.parse_args()
    report = {
        "expected_head": args.expected_head,
        "expected_job_id": args.expected_job_id,
        "cancellation_cause": "UNKNOWN",
        "input_accepted": False,
        "seed17_repaired": False,
        "own_future_tool_exit": "NOT_CLAIMED",
    }
    try:
        record_bytes = Path(args.run_record).read_bytes()
        report["run_record_sha256"] = hashlib.sha256(record_bytes).hexdigest()
        log_bytes = Path(args.job_log).read_bytes()
        report["job_log_sha256"] = hashlib.sha256(log_bytes).hexdigest()
        record = json.loads(record_bytes)
        if not isinstance(record, dict):
            raise ValueError("RUN_RECORD_NOT_OBJECT")
        if "stdout" in record:
            report.update(
                {
                    "command_actual_exit": record.get("actual_exit"),
                    "command_start_ns": record.get("start_ns"),
                    "command_end_ns": record.get("end_ns"),
                }
            )
            if type(record.get("actual_exit")) is not int or record["actual_exit"] != 0:
                raise ValueError("COMMAND_EXIT_NOT_SUCCESSFUL")
            if not isinstance(record["stdout"], str):
                raise ValueError("STDOUT_NOT_TEXT")
            record = json.loads(record["stdout"])
        if not isinstance(record, dict):
            raise ValueError("RUN_RECORD_NOT_OBJECT")
        report["observed_head"] = record.get("headSha")
        if record.get("headSha") != args.expected_head:
            raise ValueError("HEAD_MISMATCH")
        jobs = record.get("jobs")
        if not isinstance(jobs, list) or not all(isinstance(job, dict) for job in jobs):
            raise ValueError("JOBS_NOT_OBJECT_LIST")
        matches = [job for job in jobs if job.get("name") == "quality"]
        if len(matches) != 1:
            raise ValueError("QUALITY_JOB_NOT_UNIQUE")
        quality = matches[0]
        report["observed_job_id"] = quality.get("databaseId")
        if (
            type(quality.get("databaseId")) is not int
            or quality["databaseId"] != args.expected_job_id
        ):
            raise ValueError("JOB_ID_MISMATCH")
        steps = quality.get("steps")
        if not isinstance(steps, list) or not all(isinstance(step, dict) for step in steps):
            raise ValueError("STEPS_NOT_OBJECT_LIST")
        matches = [step for step in steps if step.get("name") == "Run uv run pytest"]
        if len(matches) != 1:
            raise ValueError("PYTEST_STEP_NOT_UNIQUE")
        pytest = matches[0]
        shutdown_in_log = b"The runner has received a shutdown signal." in log_bytes
        report.update(
            {
                "classification": "CI_CANCELLATION_RECORDED"
                if pytest.get("conclusion") == "cancelled"
                else "CI_STATUS_RECORDED",
                "run_status": record.get("status"),
                "run_conclusion": record.get("conclusion"),
                "pytest_conclusion": pytest.get("conclusion"),
                "runner_shutdown_signal_in_supplied_log": shutdown_in_log,
                "job_log_provenance": "CALLER_SUPPLIED_NOT_PROVEN_BY_THIS_PARSER",
            }
        )
    except json.JSONDecodeError:
        report.update({"classification": "DIAGNOSTIC_INPUT_REJECTED", "error": "INVALID_JSON"})
        print(json.dumps(report))
        return 2
    except (OSError, ValueError) as error:
        report.update({"classification": "DIAGNOSTIC_INPUT_REJECTED", "error": str(error)})
        print(json.dumps(report))
        return 2
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
