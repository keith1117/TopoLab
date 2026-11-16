"""Independent public containment audit from bounded captured buffers only.

No producer decision helper is imported. Clock checks alone do not accept a
containment proof, input, historical quality, fit, B/C or fixed seed17 repair.
"""

import ast
import base64
import hashlib
import json
import os
import re
import shlex
import stat
from pathlib import Path

IDENTITY = "topolab.container-full60-input-admission.20261116.v1"
IMAGE = "sha256:2c941e860699f878900b0edc2403613c234d4b32eda3cc9fa7036991a2a63c4a"
MODES = ["pid1-death", "host-controller-death"]
SOURCES = {"public_containment_entry.py", "public_containment_driver.py",
           "public_deadline_guardian.py", "public_worker_deadline.py",
           "public_containment_audit.py"}
BUDGET_SHA256 = "cfa8ac55d9f1879fdc9242db76b78c6661f38649e97162d0fe39339600629ec0"
GLOBAL_END_UNIX_NS = 1794852900000000000
EVIDENCE_ROOT = Path(
    "/Users/keith1117/Documents/TopoLab-data/container-full60-input-admission-20261116"
)
PACKAGE_MAX_BYTES = 8 * 1024**2
REAL_CWD = "/private/tmp/topolab-container-full60-20261116"
REAL_DOCKER = "/Applications/Docker.app/Contents/Resources/bin/docker"
REAL_DOCKER_SHA256 = "cd2bc434d320a47e104fe9241fe71c06fe343e863847baf82d944703514bf1cc"
REAL_PYTHON_SHA256 = "d4f152f2a753c94e0e7935c8ebbe6b2609979e1df7898422b577d0076383d08b"


def canonical(value) -> bytes:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    return text.encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def parsed(raw: bytes) -> dict:
    need(type(raw) is bytes and len(raw) <= 32 * 1024**2, "bounded raw JSON bytes required")
    value = json.loads(raw)
    need(isinstance(value, dict) and canonical(value) == raw, "canonical raw JSON required")
    return value


def _worker_receipt(raw: bytes) -> dict:
    need(type(raw) is bytes and len(raw) <= 1024**2, "bounded published-worker receipt required")
    value = json.loads(raw)
    need(isinstance(value, dict)
         and (json.dumps(value, sort_keys=True, allow_nan=False) + "\n").encode() == raw,
         "exact published-worker receipt serialization differs")
    return value


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError("INDEPENDENT_PUBLIC_AUDIT: " + reason)


def audit_external(plan: dict, packet: dict) -> dict:
    """Check original terminal responses against one unchanged FULL60 clock."""
    need(isinstance(packet, dict)
         and packet.get("schema") == "topolab.public-containment.actual-call.v1"
         and packet.get("author") == "/root", "new original external caller required")
    argv, request = plan["entry_argv"], packet.get("request", {})
    need(isinstance(argv, list) and argv and all(isinstance(x, str) for x in argv)
         and packet.get("argv") == argv and isinstance(request, dict)
         and request.get("cmd") == shlex.join(argv)
         and request.get("workdir") == plan["cwd"], "literal external request differs")
    need(type(plan.get("start_unix_ns")) is int
         and type(plan.get("global_end_unix_ns")) is int
         and plan["start_unix_ns"] + 7260 * 10**9 <= plan["global_end_unix_ns"],
         "whole FULL60 plus mandatory7200s result suffix unavailable")
    rows = packet.get("responses")
    need(isinstance(rows, list) and 1 <= len(rows) <= 17,
         "complete ordered original response sequence required")
    session, previous = None, None
    for index, row in enumerate(rows):
        need(isinstance(row, dict), "original response row missing")
        first, last = row.get("requested_ms"), row.get("returned_ms")
        need(type(first) is int and type(last) is int and first <= last
             and (previous is None or previous <= first), "UTC response clock invalid/backwards")
        result, arguments = row.get("result"), row.get("arguments")
        need(isinstance(result, dict) and isinstance(arguments, dict)
             and isinstance(result.get("output"), str), "original raw response incomplete")
        output = result["output"]
        need("Warning: truncated output" not in output and "tokens truncated" not in output,
             "truncated original terminal result")
        count = result.get("original_token_count")
        need(count is None or (type(count) is int and count >= 0
                               and count <= arguments.get("max_output_tokens", 10000)),
             "original token count exceeds retained output")
        if index == 0:
            need(row.get("tool") == "exec_command" and arguments == request,
                 "first original exec request differs")
        else:
            need(row.get("tool") == "write_stdin" and session is not None
                 and type(arguments.get("session_id")) is int
                 and arguments["session_id"] == session and arguments.get("chars", "") == ""
                 and type(arguments.get("yield_time_ms", 5000)) is int
                 and 0 < arguments.get("yield_time_ms", 5000) <= 30000,
                 "poll is nonempty, unowned or unbounded")
        if index == len(rows) - 1:
            need(type(result.get("exit_code")) is int and result["exit_code"] == 0
                 and result.get("session_id") is None, "actual successful terminal exit missing")
        else:
            need(result.get("exit_code") is None and type(result.get("session_id")) is int
                 and (session is None or result["session_id"] == session),
                 "intermediate original session changed or already terminal")
            session = result["session_id"]
        previous = last
    t0, t1 = rows[0]["requested_ms"], rows[-1]["returned_ms"]
    span = t1 - t0  # Includes every poll gap, startup and final native filing.
    need(plan["start_unix_ns"] <= t0 * 10**6 <= t1 * 10**6
         <= plan["start_unix_ns"] + 50 * 10**9 and span <= 50000,
         "actual return exceeds original50s clock or FULL60 tariff")
    return {"T0_ms": t0, "T1_ms": t1, "span_ms": span, "charged_FULL_seconds": 60}


def _owned(value: dict, case: dict, cid: str, payload: list[str]) -> dict:
    """Reconstruct ownership/isolation directly from raw inspect output."""
    need(value.get("Id") == cid and value.get("Name") == "/" + case["name"]
         and value.get("Image") == IMAGE, "raw inspect identity differs")
    config, host = value.get("Config", {}), value.get("HostConfig", {})
    need(config.get("Image") == IMAGE and config.get("Entrypoint") in (None, [])
         and config.get("Cmd") == payload
         and config.get("Labels", {}).get("topolab.scope") == IDENTITY
         and config.get("Labels", {}).get("topolab.owner") == case["owner"],
         "raw inspect command/owner differs")
    need(host.get("Privileged") is False and host.get("PidMode", "") == ""
         and host.get("CgroupnsMode") == "private" and not host.get("CapAdd")
         and host.get("CapDrop") == ["CAP_SYS_ADMIN"]
         and host.get("SecurityOpt") == ["no-new-privileges"]
         and not host.get("Binds") and not value.get("Mounts")
         and host.get("NetworkMode") == "none" and host.get("AutoRemove") is False
         and host.get("RestartPolicy", {}).get("Name") == "no"
         and host.get("Memory") == host.get("MemorySwap") == 3221225472
         and host.get("NanoCpus") == 1000000000 and host.get("PidsLimit") == 256,
         "raw inspect isolation/resource limits differ")
    need(isinstance(value.get("State"), dict), "raw inspect state absent")
    return value["State"]


def _terminal(state: dict, expected: int) -> None:
    need(state.get("Running") is False and type(state.get("Pid")) is int
         and state["Pid"] == 0 and state.get("ExitCode") == expected
         and state.get("Status") == "exited", "raw namespace terminal state differs")


def _cli(rows: list, plan: dict, case: dict, cid: str, payload: list[str]) -> list[dict]:
    need(isinstance(rows, list) and 1 <= len(rows) <= 96, "bounded original CLI rows required")
    previous_utc, previous_mono, outputs = plan["start_unix_ns"], plan["start_monotonic_ns"], []
    owned = None
    for row in rows:
        argv = row.get("argv", [])
        need(isinstance(argv, list) and argv[:2] == [plan["docker"], "--context=desktop-linux"]
             and len(argv) >= 4, "literal Docker context/argv differs")
        u0, u1 = row.get("requested_unix_ns"), row.get("returned_unix_ns")
        m0, m1 = row.get("requested_monotonic_ns"), row.get("returned_monotonic_ns")
        need(all(type(t) is int for t in (u0, u1, m0, m1))
             and previous_utc <= u0 <= u1 <= plan["work_end_unix_ns"]
             and previous_mono <= m0 <= m1 <= plan["work_end_monotonic_ns"],
             "CLI clock reset, backwards or outside original work bound")
        need(type(row.get("exit_code")) is int and row["exit_code"] == 0
             and row.get("primary_error") is None, "CLI actual terminal error retained")
        stdout = base64.b64decode(row["stdout_base64"], validate=True)
        stderr = base64.b64decode(row["stderr_base64"], validate=True)
        need(len(stdout) + len(stderr) <= 1048576 and not stderr, "CLI output cap/error differs")
        args = argv[2:]
        item = {"args": args, "stdout": stdout, "row": row, "state": None}
        if args == ["inspect", "--type=container", cid]:
            values = json.loads(stdout)
            need(isinstance(values, list) and len(values) == 1, "one raw inspect required")
            owned = _owned(values[0], case, cid, payload)
            item["state"] = owned
        elif args[0] in ("start", "wait", "logs", "kill"):
            need(args == [args[0], cid] and owned is not None
                 and outputs and outputs[-1]["state"] is not None,
                 "signal/collection lacks immediately preceding exact ownership inspection")
            if args[0] == "kill":
                need(owned.get("Running") is True, "kill lacks owned running namespace")
            owned = None
        elif args[0] == "create":
            expected = ["create", "--name", case["name"], "--pull=never", "--network=none",
                        "--memory=3221225472", "--memory-swap=3221225472", "--cpus=1",
                        "--pids-limit=256", "--cgroupns=private", "--cap-drop=SYS_ADMIN",
                        "--security-opt=no-new-privileges", "--restart=no",
                        "--label=topolab.scope=" + IDENTITY,
                        "--label=topolab.owner=" + case["owner"], IMAGE, *payload]
            need(args == expected and stdout.decode().strip() == cid,
                 "new exact immutable create command/CID differs")
            owned = None
        else:
            raise ValueError("INDEPENDENT_PUBLIC_AUDIT: unregistered Docker operation")
        previous_utc, previous_mono = u1, m1
        outputs.append(item)
    return outputs


def _entry(record: dict, plan: dict, actual_pid: int) -> None:
    need(type(actual_pid) is int and actual_pid > 1
         and record.get("pid") == record.get("pgid") == record.get("sid") == actual_pid
         and record.get("primary_error") is None
         and type(record.get("work_return")) is int and record["work_return"] == 0
         and record.get("Original_reads") == record.get("Foundation_helpers") == 0
         and record.get("start_unix_ns") == plan["start_unix_ns"]
         and record.get("start_monotonic_ns") == plan["start_monotonic_ns"]
         and record.get("guardian_future_cancel_reap") == "PENDING_ACTUAL_ENTRY_EXIT0"
         and record.get("own_future_tool_return") == "NOT_CLAIMED",
         "guarded entry before-return/actual ownership differs")
    guard = record.get("guardian", {})
    need(type(guard.get("pid")) is int and guard["pid"] > 1 and guard["pid"] != actual_pid
         and guard.get("parent_pid") == guard.get("process_group") == guard.get("session")
         == actual_pid and guard.get("cancel_fd") == "PRIVATE_NOT_A_RETURN_RECEIPT"
         and guard.get("deadline_unix_ns") == plan["start_unix_ns"] + 45 * 10**9
         and guard.get("deadline_monotonic_ns") == plan["start_monotonic_ns"] + 45 * 10**9
         and type(guard.get("armed_unix_ns")) is int
         and type(guard.get("armed_monotonic_ns")) is int
         and plan["start_unix_ns"] <= guard["armed_unix_ns"] < guard["deadline_unix_ns"]
         and plan["start_monotonic_ns"] <= guard["armed_monotonic_ns"]
         < guard["deadline_monotonic_ns"], "guardian isolation/original45s clock differs")


def _audit_graph(static_raw: bytes, runtime_raw: bytes, artifacts: dict[str, bytes], external: dict,
                 source_buffers: dict[str, bytes], static_path: str) -> dict:
    """Replay the NEW public proof; all paths are labels, never filesystem IO."""
    static, plan = parsed(static_raw), parsed(runtime_raw)
    need(len(static_raw) <= 262144 and len(runtime_raw) <= 262144
         and static.get("schema") == "topolab.public-containment-static.v1"
         and plan.get("schema") == "topolab.public-containment-runtime.v1"
         and static.get("identity") == IDENTITY and static.get("image") == IMAGE
         and static.get("FULL") == 60 and static.get("modes") == MODES
         and type(static.get("attempt")) is int and static["attempt"] in (1, 2)
         and static.get("binding_state") == "FROZEN_REVIEWED_PUBLISHED"
         and type(static.get("Original_reads")) is int and static["Original_reads"] == 0
         and type(static.get("Foundation_helpers")) is int and static["Foundation_helpers"] == 0,
         "new exact static/runtime public contract differs")
    extra = {"start_unix_ns", "start_monotonic_ns", "work_end_unix_ns", "work_end_monotonic_ns",
             "static_plan_sha256", "entry_argv"}
    need(set(plan) == set(static) | extra
         and all(plan[key] == value for key, value in static.items() if key != "schema")
         and plan.get("static_plan_sha256") == sha(static_raw),
         "runtime/static raw binding differs")
    for name in ("cwd", "output", "python", "docker"):
        need(isinstance(static.get(name), str) and Path(static[name]).is_absolute()
             and ".." not in Path(static[name]).parts, "absolute literal runtime path required")
    need(Path(static_path).is_absolute() and ".." not in Path(static_path).parts,
         "literal static plan label required")
    need(type(plan.get("start_unix_ns")) is int and type(plan.get("start_monotonic_ns")) is int
         and plan["work_end_unix_ns"] == plan["start_unix_ns"] + 40 * 10**9
         and plan["work_end_monotonic_ns"] == plan["start_monotonic_ns"] + 40 * 10**9,
         "original fixed40s work clock differs")
    requested = external["responses"][0]["requested_ms"]
    expected_argv = [static["python"], "-I", "-u",
                     str(Path(static["cwd"]) / "scripts/public_containment_entry.py"),
                     "--plan", static_path, "--sha256", sha(static_raw),
                     "--requested-ms", str(requested)]
    need(plan["entry_argv"] == expected_argv and plan["start_unix_ns"] == requested * 10**6,
         "entry argv/requested original clock differs")
    outer = audit_external(plan, external)
    need(set(static.get("source_sha256", {})) == set(source_buffers) == SOURCES
         and sum(len(raw) for raw in source_buffers.values()) <= 4 * 1024**2
         and all(type(raw) is bytes and len(raw) <= 1024**2
                 and sha(raw) == static["source_sha256"][name]
                 for name, raw in source_buffers.items())
         and static["driver_sha256"] == static["source_sha256"]["public_containment_driver.py"],
         "complete five-file raw source closure differs")
    tree = ast.parse(source_buffers["public_containment_driver.py"])
    payloads = [ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == "PAYLOAD" for t in node.targets)]
    need(len(payloads) == 1 and isinstance(payloads[0], str), "one frozen public payload required")
    need(isinstance(artifacts, dict) and len(artifacts) <= 64
         and sum(len(raw) for raw in artifacts.values()) <= 32 * 1024**2
         and all(type(raw) is bytes and not Path(name).is_absolute()
                 and ".." not in Path(name).parts for name, raw in artifacts.items()),
         "bounded new-output artifact buffers required")

    def obj(name):
        need(name in artifacts, "missing captured artifact: " + name)
        return parsed(artifacts[name])

    entry = obj("entry-before-return.json")
    _entry(entry, plan, entry.get("pid"))
    worker = _worker_receipt(artifacts["worker-supervision/complete-before-own-return.json"])
    before = _worker_receipt(artifacts["worker-supervision/before-launch.json"])
    initial = {key: value for key, value in worker.items()
               if key not in ("worker_pid", "finished_unix_ns", "finished_monotonic_ns")}
    initial.update(status="STOP", worker_exit=None, worker_reaped=False)
    need(before == initial, "original pending worker report differs from completed role")
    need(entry.get("worker_report") == worker and worker.get("status") == "WORKER_EXITED"
         and worker.get("schema") == "topolab.p17.worker-absolute-deadline.v1"
         and worker.get("own_future_tool_exit") == "NOT_CLAIMED"
         and worker.get("input_accepted") is False and worker.get("seed17_repaired") is False
         and worker.get("signal_scope") == "OWNED_WORKER_PROCESS_GROUP_ONLY"
         and worker.get("primary_error") is None and worker.get("secondary_errors") == []
         and type(worker.get("worker_exit")) is int and worker["worker_exit"] == 0
         and worker.get("worker_reaped") is True
         and worker.get("kill_requested") is False
         and worker.get("deadline_unix_ns") == plan["start_unix_ns"] + 42 * 10**9
         and worker.get("deadline_monotonic_ns") == plan["start_monotonic_ns"] + 42 * 10**9
         and worker.get("argv") == [static["python"], "-I", "-u",
             str(Path(static["cwd"]) / "scripts/public_containment_driver.py"),
             "--plan", str(Path(static["output"]) / "runtime-plan.json"),
             "--sha256", sha(runtime_raw)], "actual worker/source/original42s stop differs")
    need(plan["start_unix_ns"] <= worker["started_unix_ns"] <= worker["finished_unix_ns"]
         < worker["deadline_unix_ns"]
         and plan["start_monotonic_ns"] <= worker["started_monotonic_ns"]
         <= worker["finished_monotonic_ns"] < worker["deadline_monotonic_ns"],
         "worker observed return outside original clock")
    report = obj("driver/driver-before-return.json")
    need(report.get("schema") == "topolab.public-containment-driver.actual.v1"
         and report.get("identity") == IDENTITY and report.get("FULL") == 60
         and report.get("plan_sha256") == sha(runtime_raw)
         and report.get("status") == "TWO_SUBCASES_RETURNED"
         and report.get("source_original_reads") == 0
         and report.get("own_future_return") == "NOT_CLAIMED"
         and isinstance(report.get("cases"), list) and len(report["cases"]) == 2
         and len(static.get("cases", [])) == 2, "complete raw two-case report differs")
    seen_cids, seen_names, seen_owners = set(), set(), set()
    for index, mode in enumerate(MODES):
        case, row = static["cases"][index], report["cases"][index]
        prefix = f"driver/{index}/"
        need(case["mode"] == mode and re.fullmatch(r"topolab-full60-20261116-[a-z0-9-]{1,48}",
                                                   case["name"])
             and re.fullmatch(r"[0-9a-f]{64}", case["owner"])
             and row == obj(prefix + "case-before-return.json")
             and row.get("mode") == mode and row.get("name") == case["name"]
             and row.get("primary_error") is None and row.get("secondary_errors") == []
             and row.get("source_original_reads") == 0
             and row.get("status") == "PUBLIC_SUBCASE_RETURNED"
             and row.get("container_removed") is False, "new complete subcase differs")
        cid = row.get("cid")
        need(isinstance(cid, str) and re.fullmatch(r"[0-9a-f]{64}", cid)
             and cid not in seen_cids and case["name"] not in seen_names
             and case["owner"] not in seen_owners, "distinct exact scene identities required")
        seen_cids.add(cid)
        seen_names.add(case["name"])
        seen_owners.add(case["owner"])
        payload = ["python", "-I", "-u", "-c", payloads[0], mode]
        calls = _cli(row["cli_rows"], plan, case, cid, payload)
        need(calls[0]["args"][0] == "create"
             and sum(x["args"][0] == "create" for x in calls) == 1,
             "single original create required")
        ticket_raw = artifacts[prefix + "ticket.json"]
        ticket = parsed(ticket_raw)
        need(ticket["plan"] == plan and ticket["case"] == case and ticket["cid"] == cid
             and ticket["output"] == str(Path(static["output"]) / "driver" / str(index)),
             "exact helper ticket differs")
        expected_exit = 23 if index == 0 else 137
        waits = [x for x in calls if x["args"][0] == "wait"]
        logs = [x for x in calls if x["args"][0] == "logs"]
        need(len(waits) == len(logs) == 1
             and waits[0]["stdout"].decode().strip() == str(expected_exit)
             and row.get("container_wait") == str(expected_exit)
             and logs[0]["stdout"] == artifacts[prefix + "payload.log"],
             "original wait/log return differs")
        _terminal(row["stopped_state"], expected_exit)
        _terminal(row["final_stopped_state"], expected_exit)
        _terminal(calls[-1]["state"], expected_exit)
        need(row["final_stopped_state"] == calls[-1]["state"]
             and row["stopped_state"] == calls[calls.index(waits[0]) + 1]["state"],
             "claimed final/post-wait state differs from raw inspection")
        facts = [json.loads(line) for line in logs[0]["stdout"].splitlines()]
        parent = [x for x in facts if x.get("role") == "pid1"]
        detached = [x for x in facts if x.get("role") == "detached-grandchild"]
        need(len(facts) == 2 and len(parent) == len(detached) == 1
             and facts == row.get("payload_facts") and parent[0].get("pid") == 1
             and detached[0].get("ppid") == 1
             and type(detached[0].get("pid")) is int
             and detached[0]["pid"] == detached[0].get("sid") == detached[0].get("pgid") > 1
             and isinstance(parent[0].get("namespace"), str)
             and re.fullmatch(r"pid:\[[0-9]+\]", parent[0]["namespace"])
             and parent[0]["namespace"] == detached[0].get("namespace"),
             "raw PID1/reparented setsid namespace facts differ")
        need(set(row["helpers"]) == {"watchdog", "controller"},
             "all detached helper exits required")
        for kind, helper in row["helpers"].items():
            need(type(helper.get("actual_exit")) is int and helper["actual_exit"] == 0
                 and helper.get("started_new_session") is True,
                 "helper actual successful entry exit missing")
            expected = [static["python"], "-I", "-u", expected_argv[3], "--" + kind,
                        str(Path(ticket["output"]) / "ticket.json"), "--sha256", sha(ticket_raw),
                        "--deadline-unix-ns", str(plan["start_unix_ns"] + 45 * 10**9),
                        "--deadline-monotonic-ns", str(plan["start_monotonic_ns"] + 45 * 10**9)]
            need(helper.get("argv") == expected, "helper literal argv/original deadline differs")
            _entry(obj(prefix + kind + "-entry-before-return.json"), plan, helper["pid"])
            for clock, start, finish in (("unix", plan["start_unix_ns"], plan["work_end_unix_ns"]),
                                         ("monotonic", plan["start_monotonic_ns"],
                                          plan["work_end_monotonic_ns"])):
                times = [helper.get(name + "_" + clock + "_ns")
                         for name in ("requested", "launched", "waited")]
                need(all(type(t) is int for t in times) and start <= times[0] <= times[1]
                     <= times[2] <= finish, "helper actual lifetime clock differs")
        ready = obj(prefix + "watchdog-ready.json")
        stopped = obj(prefix + "watchdog-before-return.json")
        watchdog_pid = row["helpers"]["watchdog"]["pid"]
        need(ready.get("cid") == stopped.get("cid") == cid
             and ready.get("pid") == ready.get("pgid") == ready.get("sid") == watchdog_pid
             and stopped.get("pid") == stopped.get("pgid") == stopped.get("sid") == watchdog_pid
             and ready.get("primary_error") is None and stopped.get("primary_error") is None
             and stopped.get("status") == "STOPPED_PID0", "independent watchdog receipt differs")
        _terminal(stopped["stopped_state"], expected_exit)
        watcher_calls = _cli(stopped["cli_rows"], plan, case, cid, payload)
        need(stopped["stopped_state"] == watcher_calls[-1]["state"],
             "watchdog claimed terminal state differs from last raw inspection")
        _cli(ready["cli_rows"], plan, case, cid, payload)
        need(stopped["cli_rows"][:len(ready["cli_rows"])] == ready["cli_rows"],
             "watchdog READY original inspection prefix differs")
        work = obj(prefix + "controller-work-actual.json")
        started = obj(prefix + "controller-started.json")
        need(work == row.get("controller_work_actual") and work.get("primary_error") is None
             and type(work.get("work_actual_exit")) is int
             and work["work_actual_exit"] == (-9 if index else 0)
             and work.get("work_reaped") is True
             and work.get("prescribed_fault_requested") is bool(index)
             and started.get("cid") == cid and started.get("pid") == work.get("work_pid")
             and started.get("entry_pid") == started.get("pgid") == started.get("sid")
             == row["helpers"]["controller"]["pid"]
             and started["pid"] != started["entry_pid"], "actual owned controller work differs")
        controller_calls = _cli(started["cli_rows"], plan, case, cid, payload)
        need(controller_calls[-1]["args"] == ["start", cid]
             and ready["ready_unix_ns"] <= row["helpers"]["controller"]["requested_unix_ns"]
             and ready["ready_monotonic_ns"]
             <= row["helpers"]["controller"]["requested_monotonic_ns"],
             "watchdog was not independently armed before controller launch")
        kills = [x for x in watcher_calls if x["args"][0] == "kill"]
        need(len(kills) == index, "prescribed watchdog kill count differs")
        if index:
            need(obj(prefix + "controller-kill-request.json") == {
                "cid": cid, "owner": case["owner"], "ticket_sha256": sha(ticket_raw),
                "fault": "KILL_OWN_UNREAPED_CONTROLLER_WORK"}, "owned prescribed fault differs")
            need(kills[0]["row"]["requested_unix_ns"] >= ticket["kill_at_unix_ns"]
                 or kills[0]["row"]["requested_monotonic_ns"] >= ticket["kill_at_monotonic_ns"],
                 "watchdog reset/early kill differs")
            post = row["post_controller_death_state"]
            need(post.get("Running") is True and type(post.get("Pid")) is int and post["Pid"] > 0,
                 "owned namespace was not still running after actual controller death")
            wait_index = calls.index(waits[0])
            after_death = calls[wait_index - 1]
            need(after_death["state"] == post, "post-controller-death raw inspection differs")
            for clock in ("unix", "monotonic"):
                waited_at = work["work_waited_" + clock + "_ns"]
                observed = after_death["row"]["requested_" + clock + "_ns"]
                kill_at = kills[0]["row"]["requested_" + clock + "_ns"]
                need(type(waited_at) is int and waited_at < observed < kill_at,
                     "watchdog kill did not follow actual controller death and running inspection")
        else:
            before = obj(prefix + "controller-before-return.json")
            last_calls = _cli(before["cli_rows"], plan, case, cid, payload)
            need(last_calls[-1]["args"] == ["wait", cid]
                 and last_calls[-1]["stdout"].decode().strip() == "23",
                 "PID1 controller actual wait differs")
    return {"status": "PUBLIC_CONTAINMENT_RAW_REPLAY_COMPLETE", "identity": IDENTITY,
            "static_plan_sha256": sha(static_raw), "runtime_plan_sha256": sha(runtime_raw),
            "external": outer, "cases": 2, "input_accepted": False,
            "seed17_repaired": False, "own_future_return": "NOT_CLAIMED"}


def _actual_authority(authority: dict) -> None:
    need("fixture_authority" not in authority
         and authority.get("owner_budget_sha256") == BUDGET_SHA256
         and authority.get("global_end_unix_ns") == GLOBAL_END_UNIX_NS,
         "actual audit requires exact NEW budget/end and forbids fake-CLI fixture authority")
    need(authority.get("docker") == REAL_DOCKER
         and authority.get("docker_sha256") == REAL_DOCKER_SHA256
         and authority.get("python") == REAL_CWD + "/.venv/bin/python"
         and authority.get("python_sha256") == REAL_PYTHON_SHA256
         and authority.get("cwd") == REAL_CWD, "actual Docker/Python/runtime software pin differs")


def audit(static_raw: bytes, runtime_raw: bytes, artifacts: dict[str, bytes], external: dict,
          source_buffers: dict[str, bytes], static_path: str,
          expected_static_sha256: str | None = None) -> dict:
    """Public entry binds independent pre-call static pin and exact REAL runtime."""
    authority = parsed(static_raw)
    _actual_authority(authority)
    need(isinstance(expected_static_sha256, str)
         and re.fullmatch(r"[0-9a-f]{64}", expected_static_sha256)
         and sha(static_raw) == expected_static_sha256,
         "independent preregistered static SHA is missing or differs")
    output = Path(authority.get("audit_output", ""))
    need(output.is_absolute() and ".." not in output.parts and output.is_relative_to(EVIDENCE_ROOT)
         and output != EVIDENCE_ROOT and str(output) != authority.get("output"),
         "independent audit output must be a separate prebound NEW path")
    expected_names = {"entry-before-return.json", "worker-supervision/before-launch.json",
                      "worker-supervision/complete-before-own-return.json",
                      "worker-supervision/worker.stdout", "worker-supervision/worker.stderr",
                      "driver/driver-before-return.json"}
    empty_names = {"worker-supervision/worker.stdout", "worker-supervision/worker.stderr"}
    for index in (0, 1):
        prefix = f"driver/{index}/"
        names = {"case-before-return.json", "ticket.json", "payload.log",
                 "watchdog-ready.json", "watchdog-before-return.json",
                 "watchdog-entry-before-return.json", "controller-started.json",
                 "controller-work-actual.json", "controller-entry-before-return.json",
                 "controller-before-return.json" if index == 0 else "controller-kill-request.json"}
        for kind in ("watchdog", "controller", "controller-work"):
            for stream in ("stdout", "stderr"):
                name = kind + "." + stream
                names.add(name)
                empty_names.add(prefix + name)
        expected_names.update(prefix + name for name in names)
    need(set(artifacts) == expected_names, "exact permitted public artifact inventory differs")
    need(all(artifacts[name] == b"" for name in empty_names),
         "unretained/unexpected public host stdout/stderr")
    result = _audit_graph(static_raw, runtime_raw, artifacts, external, source_buffers, static_path)
    result.update(expected_source_sha256=authority["source_sha256"], audit_output=str(output),
                  independent_prebound_static_sha256=expected_static_sha256)
    return result


def audit_package(raw: bytes, expected_sha256: str, expected_static_sha256: str) -> dict:
    """Decode one hash-pinned package; embedded filesystem paths are never read."""
    need(sha(raw) == expected_sha256, "independent package raw SHA differs")
    value = parsed(raw)
    need(value.get("schema") == "topolab.public-containment-audit-package.v1"
         and value.get("audit_author") == "/root/full60_independent"
         and set(value) == {"schema", "audit_author", "static_base64", "runtime_base64",
                            "artifacts_base64", "external", "sources_base64", "static_path"},
         "new independent audit package/author required")

    def decode(encoded):
        need(isinstance(encoded, str) and len(encoded) <= 24 * 1024**2,
             "bounded raw base64 member required")
        return base64.b64decode(encoded, validate=True)

    return audit(decode(value["static_base64"]), decode(value["runtime_base64"]),
                 {name: decode(encoded) for name, encoded in value["artifacts_base64"].items()},
                 value["external"],
                 {name: decode(encoded) for name, encoded in value["sources_base64"].items()},
                 value["static_path"], expected_static_sha256)


def audit_file(path: str, expected_sha256: str, expected_static_sha256: str) -> dict:
    """Read only an exact NEW package, no-follow at every path component."""
    target = Path(path)
    need(target.is_absolute() and ".." not in target.parts
         and target.is_relative_to(EVIDENCE_ROOT) and target != EVIDENCE_ROOT,
         "independent package path outside new admitted evidence namespace")
    directory = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    stream = None
    try:
        for part in target.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        stream = os.open(target.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        info = os.fstat(stream)
        need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
             and stat.S_IMODE(info.st_mode) == 0o600 and info.st_size <= PACKAGE_MAX_BYTES,
             "private bounded independent package required")
        chunks, size = [], 0
        while True:
            raw = os.read(stream, min(65536, PACKAGE_MAX_BYTES + 1 - size))
            if not raw:
                break
            size += len(raw)
            need(size <= PACKAGE_MAX_BYTES, "independent package grew beyond cap")
            chunks.append(raw)
        return audit_package(b"".join(chunks), expected_sha256, expected_static_sha256)
    finally:
        if stream is not None:
            os.close(stream)
        os.close(directory)
