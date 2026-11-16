"""New public-only Docker namespace proof; no historical role or input dispatch."""

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

IDENTITY = "topolab.container-full60-input-admission.20261116.v1"
IMAGE = "sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a"
MODES = ["pid1-death", "host-controller-death"]
BUDGET_SHA = "cfa8ac55d9f1879fdc9242db76b78c6661f38649e97162d0fe39339600629ec0"
GLOBAL_END = 1794852900000000000
PAYLOAD = r'''
import json, os, pathlib, time, sys
def emit(role):
    print(json.dumps(dict(role=role,pid=os.getpid(),ppid=os.getppid(),
        pgid=os.getpgrp(),sid=os.getsid(0),namespace=os.readlink('/proc/self/ns/pid'))),flush=True)
ready=pathlib.Path('/tmp/topolab-detached-ready')
child=os.fork()
if child==0:
    if os.fork()!=0: os._exit(0)
    os.setsid()
    for _ in range(500):
        if os.getppid()==1: break
        time.sleep(.01)
    if os.getppid()!=1: os._exit(91)
    emit('detached-grandchild')
    ready.write_text('ready')
    time.sleep(300)
    os._exit(92)
os.waitpid(child,0)
for _ in range(500):
    if ready.exists(): break
    time.sleep(.01)
if not ready.exists(): os._exit(93)
emit('pid1')
if sys.argv[1]=='pid1-death': os._exit(23)
time.sleep(300)
os._exit(94)
'''


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
            + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def error_record(error):
    return {"type": type(error).__name__, "reason": str(error),
            "traceback": "".join(traceback.format_exception(error))}


def new_json(path, value):
    path = Path(path)
    pending = path.with_name(path.name + ".pending")
    with pending.open("xb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())
    # READY/fault handoffs become visible only as complete fsynced bytes.
    # link is atomic and refuses to overwrite an existing retained scene.
    os.link(pending, path, follow_symlinks=False)
    pending.unlink()


def pinned_json(path, expected, maximum=262144):
    path = Path(path)
    need(not path.is_symlink() and path.is_file(), "regular pinned metadata required")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    need(len(raw) <= maximum and sha(raw) == expected, "pinned metadata hash/size differs")
    value = json.loads(raw)
    need(canonical(value) == raw, "canonical metadata required")
    return value


def payload_argv(mode):
    need(mode in MODES, "fixed public mode required")
    return ["python", "-I", "-u", "-c", PAYLOAD, mode]


def owned_state(case, cid, value):
    need(re.fullmatch(r"[0-9a-f]{64}", cid) and value.get("Id") == cid
         and value.get("Name") == "/" + case["name"] and value.get("Image") == IMAGE
         and value.get("Config", {}).get("Image") == IMAGE
         and value.get("Config", {}).get("Entrypoint") in (None, [])
         and value.get("Config", {}).get("Cmd") == payload_argv(case["mode"])
         and value.get("Config", {}).get("Labels", {}).get("topolab.scope") == IDENTITY
         and value.get("Config", {}).get("Labels", {}).get("topolab.owner") == case["owner"],
         "exact container ownership/command differs")
    host = value["HostConfig"]
    need(not host.get("Privileged") and host.get("PidMode", "") == ""
         and host.get("CgroupnsMode") == "private" and not host.get("CapAdd")
         and "CAP_SYS_ADMIN" in (host.get("CapDrop") or [])
         and "no-new-privileges" in (host.get("SecurityOpt") or [])
         and not host.get("Binds") and not value.get("Mounts")
         and host.get("NetworkMode") == "none" and not host.get("AutoRemove")
         and host.get("RestartPolicy", {}).get("Name") == "no"
         and host.get("Memory") == host.get("MemorySwap") == 3221225472
         and host.get("NanoCpus") == 1000000000 and host.get("PidsLimit") == 256,
         "exact public container isolation/resource limits differ")
    return value["State"]


class Cli:
    """One fixed clock, bounded original results, no implicit retries."""

    def __init__(self, plan, *, max_calls=96):
        self.plan = plan
        self.rows = []
        self.max_calls = max_calls
        self.previous_utc = plan["start_unix_ns"]

    def remaining(self):
        utc, mono = time.time_ns(), time.monotonic_ns()
        need(utc >= self.previous_utc, "backwards public UTC clock")
        self.previous_utc = utc
        left = min(self.plan["work_end_unix_ns"] - utc,
                   self.plan["work_end_monotonic_ns"] - mono) / 1e9
        need(left > 0, "original public work deadline exhausted")
        return left

    def call(self, args, timeout=2):
        row = {"argv": [self.plan["docker"], "--context=desktop-linux", *args],
               "requested_unix_ns": time.time_ns(), "requested_monotonic_ns": time.monotonic_ns(),
               "exit_code": None, "primary_error": None}
        self.rows.append(row)
        try:
            need(len(self.rows) <= self.max_calls, "public Docker call quota exhausted")
            result = subprocess.run(row["argv"], stdin=subprocess.DEVNULL,
                                    capture_output=True, timeout=min(timeout, self.remaining()),
                                    check=False)
            row.update(exit_code=result.returncode,
                       stdout_base64=base64.b64encode(result.stdout).decode(),
                       stderr_base64=base64.b64encode(result.stderr).decode())
            need(result.returncode == 0, "public Docker command returned nonzero")
            need(len(result.stdout) + len(result.stderr) <= 1048576, "public command output cap")
            return result.stdout
        except BaseException as error:
            row["primary_error"] = error_record(error)
            if isinstance(error, subprocess.TimeoutExpired):
                row["timeout_stdout_base64"] = base64.b64encode(error.stdout or b"").decode()
                row["timeout_stderr_base64"] = base64.b64encode(error.stderr or b"").decode()
            raise
        finally:
            row.update(returned_unix_ns=time.time_ns(), returned_monotonic_ns=time.monotonic_ns())


def inspect(plan, case, cid, cli):
    values = json.loads(cli.call(["inspect", "--type=container", cid]))
    need(isinstance(values, list) and len(values) == 1, "one owned inspection required")
    return owned_state(case, cid, values[0])


def validate_static(plan):
    need(plan.get("schema") in ("topolab.public-containment-static.v1",
                               "topolab.public-containment-runtime.v1")
         and plan.get("identity") == IDENTITY and plan.get("FULL") == 60
         and plan.get("image") == IMAGE and plan.get("modes") == MODES,
         "new exact public contract required")
    need(plan.get("binding_state") == "FROZEN_REVIEWED_PUBLISHED"
         and plan.get("Original_reads") == 0 and plan.get("Foundation_helpers") == 0,
         "public launch admission is not frozen")
    need(plan.get("owner_budget_sha256") == BUDGET_SHA
         and (plan.get("fixture_authority") == "DECLARED_FAKE_CLI_SOFTWARE_ONLY"
              or (plan.get("fixture_authority") is None
                  and plan.get("global_end_unix_ns") == GLOBAL_END)),
         "exact new budget/global clock differs")
    need(plan["attempt"] in (1, 2) and len(plan["cases"]) == 2
         and Path(plan["docker"]).is_absolute() and not Path(plan["docker"]).is_symlink()
         and Path(plan["output"]).is_absolute()
         and plan["cwd"] == str(Path(__file__).resolve().parents[1]) == os.getcwd(),
         "literal public paths differ")
    need(plan["python"] == sys.executable and Path(plan["python"]).is_absolute()
         and sha(Path(plan["python"]).read_bytes()) == plan["python_sha256"],
         "literal public interpreter differs")
    names = {"public_containment_entry.py", "public_containment_driver.py",
             "public_deadline_guardian.py", "public_worker_deadline.py",
             "public_containment_audit.py"}
    need(set(plan["source_sha256"]) == names, "complete explicit new source closure required")
    for name, expected in plan["source_sha256"].items():
        need(sha(Path(__file__).with_name(name).read_bytes()) == expected,
             "frozen public source changed: " + name)
    need(sha(Path(plan["docker"]).read_bytes()) == plan["docker_sha256"],
         "Docker executable changed")
    need(plan["source_sha256"]["public_containment_driver.py"] == plan["driver_sha256"],
         "public driver pin differs")
    for mode, case in zip(MODES, plan["cases"], strict=True):
        need(case["mode"] == mode and re.fullmatch(r"topolab-full60-20261116-[a-z0-9-]{1,48}",
                                                 case["name"])
             and re.fullmatch(r"[0-9a-f]{64}", case["owner"]), "public case identity differs")
    need(plan["cases"][0]["name"] != plan["cases"][1]["name"]
         and plan["cases"][0]["owner"] != plan["cases"][1]["owner"],
         "two distinct new owned scenes required")


def validate_plan(plan):
    validate_static(plan)
    need(plan.get("schema") == "topolab.public-containment-runtime.v1"
         and plan["work_end_unix_ns"] == plan["start_unix_ns"] + 40 * 10**9
         and plan["work_end_monotonic_ns"] == plan["start_monotonic_ns"] + 40 * 10**9
         and plan["start_unix_ns"] + (60 + 7200) * 10**9 <= plan["global_end_unix_ns"],
         "fixed common public clock/bounds differ")


def helper(kind, path, expected):
    ticket = pinned_json(path, expected)
    plan = ticket["plan"]
    validate_plan(plan)
    case, cid, output = ticket["case"], ticket["cid"], Path(ticket["output"])
    cli = Cli(plan)
    inspect(plan, case, cid, cli)
    record = {"kind": kind, "cid": cid, "pid": os.getpid(), "pgid": os.getpgrp(),
              "sid": os.getsid(0), "primary_error": None, "status": "STOP"}
    if kind == "controller-work":
        cli.call(["start", cid])
        record.update(entry_pid=os.getppid(), cli_rows=cli.rows,
                      ready_unix_ns=time.time_ns(), ready_monotonic_ns=time.monotonic_ns())
        new_json(output / "controller-started.json", record)
        if case["mode"] == "host-controller-death":
            time.sleep(300)
        else:
            inspect(plan, case, cid, cli)
            cli.call(["wait", cid], 8)
        record.update(status="RETURNING", cli_rows=cli.rows)
        new_json(output / "controller-before-return.json", record)
        return 0
    record.update(ready_unix_ns=time.time_ns(), ready_monotonic_ns=time.monotonic_ns(),
                  cli_rows=cli.rows)
    new_json(output / "watchdog-ready.json", record)
    try:
        for _ in range(64):
            cli.remaining()
            state = inspect(plan, case, cid, cli)
            if state.get("Running") is False and state.get("Pid") == 0:
                if state.get("Status") == "exited":
                    record.update(status="STOPPED_PID0", stopped_state=state)
                    break
            if (time.monotonic_ns() >= ticket["kill_at_monotonic_ns"]
                    or time.time_ns() >= ticket["kill_at_unix_ns"]):
                # Identity is revalidated immediately before the exact-CID signal.
                state = inspect(plan, case, cid, cli)
                if state.get("Running"):
                    cli.call(["kill", cid])
                state = inspect(plan, case, cid, cli)
                need(state.get("Running") is False and state.get("Pid") == 0,
                     "watchdog did not observe namespace exit")
                record.update(status="STOPPED_PID0", stopped_state=state)
                break
            time.sleep(min(0.2, cli.remaining()))
        else:
            raise ValueError("finite independent watchdog observations exhausted")
    except BaseException as error:
        record["primary_error"] = error_record(error)
    record["cli_rows"] = cli.rows
    new_json(output / "watchdog-before-return.json", record)
    return 0 if record["status"] == "STOPPED_PID0" and record["primary_error"] is None else 1


def run_case(plan, case, output):
    cli = Cli(plan)
    need(cli.remaining() >= 18, "complete public subcase suffix unavailable before entry")
    output.mkdir(mode=0o700)
    row = {"mode": case["mode"], "name": case["name"], "primary_error": None,
           "secondary_errors": [], "status": "STOP", "source_original_reads": 0,
           "helpers": {}, "container_removed": False}
    cid, watchdog, controller = None, None, None
    try:
        args = ["create", "--name", case["name"], "--pull=never", "--network=none",
                "--memory=3221225472", "--memory-swap=3221225472", "--cpus=1",
                "--pids-limit=256", "--cgroupns=private", "--cap-drop=SYS_ADMIN",
                "--security-opt=no-new-privileges", "--restart=no",
                "--label=topolab.scope=" + IDENTITY, "--label=topolab.owner=" + case["owner"],
                IMAGE, *payload_argv(case["mode"])]
        cid = cli.call(args).decode().strip()
        need(re.fullmatch(r"[0-9a-f]{64}", cid), "one immutable created CID required")
        row["cid"] = cid
        state = inspect(plan, case, cid, cli)
        need(state.get("Running") is False and state.get("Pid") == 0,
             "new unstarted container required")
        ticket = {"plan": plan, "case": case, "cid": cid, "output": str(output),
                  "kill_at_unix_ns": time.time_ns() + 8 * 10**9,
                  "kill_at_monotonic_ns": time.monotonic_ns() + 8 * 10**9}
        ticket_path = output / "ticket.json"
        new_json(ticket_path, ticket)
        ticket_sha = sha(canonical(ticket))

        def spawn(kind):
            argv = [sys.executable, "-I", "-u", str(Path(__file__).with_name(
                "public_containment_entry.py").resolve()), "--" + kind,
                str(ticket_path), "--sha256", ticket_sha,
                "--deadline-unix-ns", str(plan["start_unix_ns"] + 45 * 10**9),
                "--deadline-monotonic-ns", str(plan["start_monotonic_ns"] + 45 * 10**9)]
            requested_unix, requested_mono = time.time_ns(), time.monotonic_ns()
            with (output / (kind + ".stdout")).open("xb") as stdout, (
                output / (kind + ".stderr")
            ).open("xb") as stderr:
                child = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=stdout,
                                         stderr=stderr, start_new_session=True, close_fds=True)
            row["helpers"][kind] = {"pid": child.pid, "argv": argv,
                                     "actual_exit": None, "started_new_session": True,
                                     "requested_unix_ns": requested_unix,
                                     "requested_monotonic_ns": requested_mono,
                                     "launched_unix_ns": time.time_ns(),
                                     "launched_monotonic_ns": time.monotonic_ns()}
            return child

        watchdog = spawn("watchdog")
        for _ in range(100):
            need(watchdog.poll() is None and cli.remaining() > 0, "watchdog failed before READY")
            ready_path = output / "watchdog-ready.json"
            if ready_path.is_file():
                ready = json.loads(ready_path.read_bytes())
                need(ready["cid"] == cid and ready["pid"] == ready["pgid"] == ready["sid"]
                     == watchdog.pid, "independent watchdog ownership/isolation differs")
                break
            time.sleep(0.02)
        else:
            raise ValueError("watchdog READY timeout")
        controller = spawn("controller")
        for _ in range(100):
            if (output / "controller-started.json").is_file():
                break
            need(controller.poll() is None and cli.remaining() > 0,
                 "controller failed before start")
            time.sleep(0.02)
        else:
            raise ValueError("controller startup timeout")
        if case["mode"] == "host-controller-death":
            started = json.loads((output / "controller-started.json").read_bytes())
            need(started["entry_pid"] == started["pgid"] == started["sid"] == controller.pid
                 and started["pid"] != controller.pid and started["cid"] == cid,
                 "owned controller work READY differs")
            new_json(output / "controller-kill-request.json",
                     {"cid": cid, "owner": case["owner"], "ticket_sha256": ticket_sha,
                      "fault": "KILL_OWN_UNREAPED_CONTROLLER_WORK"})
        code = controller.wait(timeout=min(10, cli.remaining()))
        row["helpers"]["controller"]["actual_exit"] = code
        actual = json.loads((output / "controller-work-actual.json").read_bytes())
        need(code == 0 and actual["work_actual_exit"] == (
            -9 if case["mode"] == "host-controller-death" else 0)
             and actual["work_reaped"] and actual["primary_error"] is None
             and actual["prescribed_fault_requested"] == (case["mode"] == "host-controller-death"),
             "actual controller entry/work exits differ")
        row["controller_work_actual"] = actual
        state = inspect(plan, case, cid, cli)
        if case["mode"] == "host-controller-death":
            row["post_controller_death_state"] = state
            row["post_controller_death_inspect"] = cli.rows[-1]
            need(state.get("Running") is True and state.get("Pid", 0) > 0,
                 "container stopped before observed controller work death")
        waited = cli.call(["wait", cid], 12).decode().strip()
        state = inspect(plan, case, cid, cli)
        row.update(container_wait=waited, stopped_state=state)
        expected_exit = 23 if case["mode"] == "pid1-death" else 137
        need(waited == str(expected_exit) and state.get("ExitCode") == expected_exit
             and state.get("Running") is False and state.get("Pid") == 0,
             "actual PID1/namespace terminal state differs")
        logs = cli.call(["logs", cid])
        with (output / "payload.log").open("xb") as stream:
            stream.write(logs)
        facts = [json.loads(line) for line in logs.splitlines()]
        parent = [x for x in facts if x.get("role") == "pid1"]
        detached = [x for x in facts if x.get("role") == "detached-grandchild"]
        need(len(parent) == len(detached) == 1 and parent[0]["pid"] == 1
             and detached[0]["pid"] == detached[0]["sid"] == detached[0]["pgid"] > 1
             and detached[0]["ppid"] == 1
             and parent[0]["namespace"] == detached[0]["namespace"],
             "actual reparented setsid descendant in same PID1 namespace absent")
        code = watchdog.wait(timeout=min(4, cli.remaining()))
        row["helpers"]["watchdog"]["actual_exit"] = code
        guard = json.loads((output / "watchdog-before-return.json").read_bytes())
        need(code == 0 and guard["status"] == "STOPPED_PID0" and guard["primary_error"] is None,
             "independent watchdog actual return differs")
        row.update(status="PUBLIC_SUBCASE_RETURNED", payload_facts=facts)
    except BaseException as error:
        row["primary_error"] = error_record(error)
    finally:
        if cid:
            try:
                state = inspect(plan, case, cid, cli)
                if state.get("Running"):
                    cli.call(["kill", cid])
                row["final_stopped_state"] = inspect(plan, case, cid, cli)
            except BaseException as error:
                row["secondary_errors"].append(error_record(error))
        for kind, child in [("controller", controller), ("watchdog", watchdog)]:
            if child is None:
                continue
            try:
                if child.poll() is None:
                    child.wait(timeout=min(2, cli.remaining()))
                row["helpers"][kind]["actual_exit"] = child.wait(timeout=0)
                row["helpers"][kind].update(waited_unix_ns=time.time_ns(),
                                           waited_monotonic_ns=time.monotonic_ns())
            except BaseException as error:
                row["secondary_errors"].append(error_record(error))
        if row["primary_error"] or row["secondary_errors"]:
            row["status"] = "STOP"
        row["cli_rows"] = cli.rows
        new_json(output / "case-before-return.json", row)
    return row


def run(path, expected):
    plan = pinned_json(path, expected)
    validate_plan(plan)
    output = Path(plan["output"]) / "driver"
    output.mkdir(mode=0o700)
    results = []
    for index, case in enumerate(plan["cases"]):
        row = run_case(plan, case, output / str(index))
        results.append(row)
        if row["status"] != "PUBLIC_SUBCASE_RETURNED":
            break
    value = {"schema": "topolab.public-containment-driver.actual.v1", "identity": IDENTITY,
             "FULL": 60, "plan_sha256": expected, "cases": results,
             "status": "TWO_SUBCASES_RETURNED" if len(results) == 2
             and all(x["status"] == "PUBLIC_SUBCASE_RETURNED" for x in results) else "STOP",
             "source_original_reads": 0, "own_future_return": "NOT_CLAIMED"}
    new_json(output / "driver-before-return.json", value)
    return 0 if value["status"] == "TWO_SUBCASES_RETURNED" else 1


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    for name in ("plan", "watchdog", "controller-work"):
        group.add_argument("--" + name)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if args.plan:
        return run(args.plan, args.sha256)
    return helper("watchdog" if args.watchdog else "controller-work",
                  args.watchdog or args.controller_work, args.sha256)


if __name__ == "__main__":
    raise SystemExit(main())
