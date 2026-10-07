"""One native producer/auditor attempt and fully paid metadata closure."""

import os
import signal
import subprocess
import sys
from time import perf_counter

from b4_28_common import (
    REPO,
    THREADS,
    arguments,
    canonical,
    digest,
    plan_payload,
    read,
    release,
    save,
)
from b4_28_resource_close import native


def command(output, name, argv, numerical=False, metadata_timeout=15):
    receipts = output / "audit_receipts"
    marker = receipts / (name + "_attempt.json")
    save(
        marker,
        {
            "name": name,
            "argv": argv,
            "plan_sha256": plan_payload()["plan_sha256"],
            "attempted": True,
        },
    )
    profile, log = output / "profiles" / (name + ".time"), output / "logs" / (name + ".log")
    if profile.exists() or log.exists():
        raise ValueError("exclusive native command files required")
    env = {**os.environ, "PYTHONPATH": str(REPO / "src") + os.pathsep + str(REPO / "scripts")}
    env.update({key: "1" for key in THREADS})
    started, timed_out = perf_counter(), False
    with log.open("xb") as stream:
        process = subprocess.Popen(
            ["/usr/bin/time", "-l", "-o", str(profile), *argv],
            cwd=REPO,
            env=env,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            exit_code = process.wait(timeout=585 if numerical else metadata_timeout)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                exit_code = process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                exit_code = process.wait()
    elapsed = perf_counter() - started
    try:
        measured = native(profile)
    except (ValueError, FileNotFoundError):
        measured = None
    result = {
        "name": name,
        "argv": argv,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "observed_outer_wall_seconds": elapsed,
        "native": measured,
        "profile": str(profile.relative_to(output)),
        "profile_sha256": digest(profile) if profile.exists() else None,
        "log": str(log.relative_to(output)),
        "log_sha256": digest(log),
    }
    save(receipts / (name + "_command.json"), result)
    return result


def execute(old, data, output):
    started = perf_counter()
    release(output)
    if (output / "audit_receipts/native_execution_attempt.json").exists():
        raise ValueError("one execution chain only; no retry/reset")
    save(
        output / "audit_receipts/native_execution_attempt.json",
        {
            "source_revision": read(output / "audit_receipts/production_release.json")[
                "source_revision"
            ],
            "plan": plan_payload(),
            "fully_paid_reserve_seconds": 60,
        },
    )
    common = ["--legacy-root", str(old), "--data-root", str(data), "--output-root", str(output)]
    producer = [sys.executable, "scripts/b4_28_active_set_numerical_evidence.py", *common]
    commands = [command(output, "plan", producer)]
    if commands[0]["exit_code"] != 0 or commands[0]["native"] is None:
        save(
            output / "audit_receipts/plan_abort.json",
            {
                "passed": False,
                "commands": commands,
                "numerical_stages_started": 0,
                "whole_charge_seconds": 60,
                "native_resource_proof_complete": False,
                "no_retry": True,
            },
        )
    else:
        commands.append(command(output, "producer", [*producer, "--execute"], numerical=True))
        # A failed producer permits only metadata prefix accounting in the auditor.
        commands.append(
            command(
                output,
                "independent",
                [sys.executable, "scripts/b4_28_independent_audit.py", *common, "--execute"],
                numerical=True,
            )
        )
    save(output / "audit_receipts/execution_commands.json", commands)
    numerical_wall = sum(c["observed_outer_wall_seconds"] for c in commands[1:])

    def remaining_reserve():
        # Leave fifteen seconds for native controller exit and post-exit proof.
        used = perf_counter() - started - numerical_wall
        remaining = 45 - used
        if remaining <= 2:
            raise RuntimeError("combined metadata reserve exhausted; no retry")
        return min(15, remaining - 2)

    close = [sys.executable, "scripts/b4_28_resource_close.py", "--output-root", str(output)]
    closer = command(output, "closure", close, metadata_timeout=remaining_reserve())
    if closer["exit_code"] != 0:
        return 1
    verifier = command(
        output, "verification", [*close, "--verify"], metadata_timeout=remaining_reserve()
    )
    if verifier["exit_code"] != 0:
        return 1
    save(
        output / "audit_receipts/native_chain_completed.json",
        {
            "passed": True,
            "commands_sha256": digest(output / "audit_receipts/execution_commands.json"),
            "closure_command_sha256": digest(output / "audit_receipts/closure_command.json"),
            "verification_command_sha256": digest(
                output / "audit_receipts/verification_command.json"
            ),
            "postexit_proof_pending": True,
        },
    )
    return 0


def main(argv=None):
    args, old, data, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    return execute(old, data, output)


if __name__ == "__main__":
    raise SystemExit(main())
