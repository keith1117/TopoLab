"""Early armed filing guardian for the new public-only containment contract.

Exit0 has a deliberately small meaning: the guarded work returned0, every final
fsync finished, and this entry actually reaped its guardian with exit0. Its
before-return file cannot attest its own future return; an external author must
retain that original terminal result and the complete request-to-response span.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import types
from pathlib import Path


def load(name):
    path = Path(__file__).resolve().with_name(name + ".py")
    raw = path.read_bytes()
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    module.loaded_source_sha256 = hashlib.sha256(raw).hexdigest()
    return module


def guardian_facts(guardian):
    return dict(guardian._asdict(), cancel_fd="PRIVATE_NOT_A_RETURN_RECEIPT")


def controller(driver, ticket_path, expected, guard):
    """The surviving wrapper alone signals its still-unreaped work child."""
    ticket = driver.pinned_json(ticket_path, expected)
    driver.validate_plan(ticket["plan"])
    output = Path(ticket["output"])
    argv = [sys.executable, "-I", "-u", str(Path(driver.__file__).resolve()),
            "--controller-work", ticket_path, "--sha256", expected]
    record = {"argv": argv, "work_actual_exit": None, "work_reaped": False,
              "prescribed_fault_requested": False, "primary_error": None, "secondary_errors": [],
              "guardian": guardian_facts(guard)}
    child = None
    try:
        with (output / "controller-work.stdout").open("xb") as stdout, (
            output / "controller-work.stderr"
        ).open("xb") as stderr:
            child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                     close_fds=True)  # Same guardian-pinned group/session.
        record["work_pid"] = child.pid
        record.update(work_launched_unix_ns=time.time_ns(),
                      work_launched_monotonic_ns=time.monotonic_ns())
        request_path = output / "controller-kill-request.json"
        for _ in range(2000):
            driver.Cli(ticket["plan"]).remaining()
            # Do not reap before the prescribed signal. This unreaped child pins PID.
            if request_path.is_file():
                request = json.loads(request_path.read_bytes())
                driver.need(request == {"cid": ticket["cid"], "owner": ticket["case"]["owner"],
                                        "ticket_sha256": expected,
                                        "fault": "KILL_OWN_UNREAPED_CONTROLLER_WORK"},
                            "prescribed controller fault binding differs")
                driver.need(ticket["case"]["mode"] == "host-controller-death",
                            "fault forbidden in PID1 case")
                child.kill()
                record["prescribed_fault_requested"] = True
                record["work_actual_exit"] = child.wait(timeout=2)
                record["work_reaped"] = True
                break
            if ticket["case"]["mode"] == "pid1-death":
                code = child.poll()
                if code is not None:
                    record.update(work_actual_exit=code, work_reaped=True)
                    break
            time.sleep(.01)
        else:
            raise TimeoutError("finite controller wrapper observations exhausted")
        expected_exit = -9 if ticket["case"]["mode"] == "host-controller-death" else 0
        driver.need(record["work_actual_exit"] == expected_exit and record["work_reaped"],
                    "actual owned controller work exit differs")
        record.update(work_waited_unix_ns=time.time_ns(),
                      work_waited_monotonic_ns=time.monotonic_ns())
    except BaseException as error:
        record["primary_error"] = driver.error_record(error)
        # Failure keeps the guardian armed until all same-group work is bounded.
        if child is not None and child.returncode is None:
            try:
                child.kill()
                record.update(work_actual_exit=child.wait(timeout=2), work_reaped=True)
            except BaseException as cleanup_error:
                record["secondary_errors"].append(driver.error_record(cleanup_error))
    driver.new_json(output / "controller-work-actual.json", record)
    return (0 if record["primary_error"] is None and not record["secondary_errors"] else 1,
            record["work_reaped"])


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for name in ("plan", "watchdog", "controller", "preflight", "audit"):
        group.add_argument("--" + name)
    parser.add_argument("--sha256")
    parser.add_argument("--metadata-plan")
    parser.add_argument("--public-static-sha256")
    parser.add_argument("--requested-ms", type=int)
    parser.add_argument("--deadline-unix-ns", type=int)
    parser.add_argument("--deadline-monotonic-ns", type=int)
    args = parser.parse_args()
    entry_unix, entry_mono = time.time_ns(), time.monotonic_ns()
    if args.requested_ms is not None:
        start_unix = args.requested_ms * 1_000_000
        elapsed = entry_unix - start_unix
        if elapsed < 0 or elapsed >= 45 * 10**9:
            os.write(2, b"expired original entry or future requested clock\n")
            os._exit(2)
        start_mono = entry_mono - elapsed
        end_unix, end_mono = start_unix + 45 * 10**9, start_mono + 45 * 10**9
    else:
        end_unix, end_mono = args.deadline_unix_ns, args.deadline_monotonic_ns
        if end_unix is None or end_mono is None:
            os.write(2, b"absolute helper deadlines required\n")
            os._exit(2)
        start_unix, start_mono = end_unix - 45 * 10**9, end_mono - 45 * 10**9
    if (os.getpid(), os.getpid()) != (os.getpgrp(), os.getsid(0)):
        os.setsid()
    guardian_module = load("public_deadline_guardian")
    guard = guardian_module.arm_guardian(end_unix, end_mono)
    driver = load("public_containment_driver")
    code, record_path, safe_to_cancel = 1, None, not args.controller
    record = {"pid": os.getpid(), "pgid": os.getpgrp(), "sid": os.getsid(0),
              "guardian": guardian_facts(guard), "start_unix_ns": start_unix,
              "start_monotonic_ns": start_mono, "Original_reads": 0, "Foundation_helpers": 0,
              "primary_error": None, "guardian_future_cancel_reap": "PENDING_ACTUAL_ENTRY_EXIT0",
              "own_future_tool_return": "NOT_CLAIMED"}
    try:
        if args.preflight:
            record_path, code = Path(args.preflight), 0
            if args.metadata_plan:
                static = driver.pinned_json(args.metadata_plan, args.sha256)
                driver.validate_static(static)
                metadata = dict(static, start_unix_ns=start_unix, start_monotonic_ns=start_mono,
                                work_end_unix_ns=start_unix + 40 * 10**9,
                                work_end_monotonic_ns=start_mono + 40 * 10**9)
                cli = driver.Cli(metadata, max_calls=2)
                raw = cli.call(["image", "inspect", static["image"]])
                image = json.loads(raw)
                driver.need(len(image) == 1 and image[0]["Id"] == static["image"]
                            and image[0]["Os"] == "linux" and image[0]["Architecture"] == "arm64",
                            "literal local public image unavailable")
                record.update(metadata_only=True, static_plan_sha256=args.sha256,
                              cli_rows=cli.rows, container_create_or_start=0)
        elif args.audit:
            driver.need(start_unix + 7260 * 10**9 <= driver.GLOBAL_END,
                        "complete independent audit and result suffix unavailable")
            auditor = load("public_containment_audit")
            verdict = auditor.audit_file(args.audit, args.sha256, args.public_static_sha256)
            driver.need(all(verdict["expected_source_sha256"][name + ".py"]
                            == module.loaded_source_sha256
                            for name, module in (("public_containment_driver", driver),
                                                 ("public_deadline_guardian", guardian_module),
                                                 ("public_containment_audit", auditor))),
                        "executed independent audit source differs")
            output = Path(verdict["audit_output"])
            output.mkdir(mode=0o700)
            record_path = output / "independent-audit-before-return.json"
            record["verdict"] = verdict
            code = 0
        elif args.plan:
            static = driver.pinned_json(args.plan, args.sha256)
            driver.validate_static(static)
            driver.need(all(static["source_sha256"][name + ".py"] == module.loaded_source_sha256
                            for name, module in (("public_containment_driver", driver),
                                                 ("public_deadline_guardian", guardian_module))),
                        "executed source buffers differ from frozen source")
            driver.need(start_unix + 7260 * 10**9 <= static["global_end_unix_ns"],
                        "complete public call and mandatory result suffix unavailable")
            output = Path(static["output"])
            output.mkdir(mode=0o700)
            record_path = output / "entry-before-return.json"
            plan = dict(static, schema="topolab.public-containment-runtime.v1",
                        start_unix_ns=start_unix, start_monotonic_ns=start_mono,
                        work_end_unix_ns=start_unix + 40 * 10**9,
                        work_end_monotonic_ns=start_mono + 40 * 10**9,
                        static_plan_sha256=args.sha256,
                        entry_argv=[sys.executable, "-I", "-u", str(Path(__file__).resolve()),
                                    "--plan", args.plan, "--sha256", args.sha256,
                                    "--requested-ms", str(args.requested_ms)], cwd=os.getcwd())
            runtime_path = output / "runtime-plan.json"
            driver.new_json(runtime_path, plan)
            worker = load("public_worker_deadline")
            driver.need(worker.loaded_source_sha256 == static["source_sha256"][
                "public_worker_deadline.py"], "executed worker source differs")
            report = worker.execute(
                [sys.executable, "-I", "-u", str(Path(driver.__file__).resolve()),
                 "--plan", str(runtime_path), "--sha256", driver.sha(driver.canonical(plan))],
                output / "worker-supervision", start_unix + 42 * 10**9,
                start_mono + 42 * 10**9,
            )
            record["worker_report"] = report
            code = 0 if report["status"] == "WORKER_EXITED" else 1
        else:
            ticket_path = args.watchdog or args.controller
            ticket = driver.pinned_json(ticket_path, args.sha256)
            driver.validate_plan(ticket["plan"])
            driver.need(end_unix == ticket["plan"]["start_unix_ns"] + 45 * 10**9
                        and end_mono == ticket["plan"]["start_monotonic_ns"] + 45 * 10**9,
                        "helper reset original guardian clock")
            kind = "watchdog" if args.watchdog else "controller"
            record_path = Path(ticket["output"]) / (kind + "-entry-before-return.json")
            driver.need(all(ticket["plan"]["source_sha256"][name + ".py"]
                            == module.loaded_source_sha256
                            for name, module in (("public_containment_driver", driver),
                                                 ("public_deadline_guardian", guardian_module))),
                        "executed helper source buffers differ")
            if args.watchdog:
                code = driver.helper("watchdog", ticket_path, args.sha256)
            else:
                code, safe_to_cancel = controller(driver, ticket_path, args.sha256, guard)
    except BaseException as error:
        record["primary_error"] = driver.error_record(error)
        code = 1
    record["work_return"] = code
    if record_path is not None:
        driver.new_json(record_path, record)  # Last arbitrary IO, guardian still armed.
    else:
        os.write(2, driver.canonical(record))
    if not safe_to_cancel:
        # Retain the guardian: EOF requests its owned-group kill. Never abandon
        # an unknown/unreaped work child by cancelling its only group deadline.
        os.close(guard.cancel_fd)
        os._exit(1)
    try:
        actual = guardian_module.cancel_and_reap(guard)
        # Only memory/clock checks and _exit follow actual guardian reap.
        if actual["guardian_exit"] != 0 or not actual["guardian_reaped"]:
            os._exit(1)
        if time.time_ns() >= end_unix or time.monotonic_ns() >= end_mono:
            os._exit(1)
    except BaseException:
        # Cancellation can fail after waitpid; never print/traceback/finalize.
        os._exit(1)
    os._exit(code)


if __name__ == "__main__":
    main()
