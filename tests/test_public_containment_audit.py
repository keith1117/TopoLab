"""Independent rejection regressions; synthetic buffers confer no acceptance."""

import copy
import hashlib
import importlib.util
import json
import shlex
import time
from pathlib import Path

import pytest


def auditor():
    path = Path(__file__).parents[1] / "scripts/public_containment_audit.py"
    import types

    module = types.ModuleType("public_containment_audit_test")
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    return module


def external_fixture():
    argv = ["/python", "-I", "/repo/scripts/public_containment_entry.py", "--plan", "/new/plan"]
    plan = {"entry_argv": argv, "cwd": "/repo", "start_unix_ns": 10_000 * 10**6,
            "global_end_unix_ns": (10_000 + 8 * 3600 * 1000) * 10**6}
    request = {"cmd": shlex.join(argv), "workdir": "/repo", "yield_time_ms": 30000,
               "max_output_tokens": 1000}
    packet = {"schema": "topolab.public-containment.actual-call.v1", "author": "/root",
              "argv": argv, "request": request,
              "responses": [{"tool": "exec_command", "arguments": copy.deepcopy(request),
                             "requested_ms": 10_010, "returned_ms": 12_010,
                             "result": {"output": "", "exit_code": 0}}]}
    return plan, packet


def test_original_complete_external_response_passes_clock_check_only() -> None:
    plan, packet = external_fixture()
    result = auditor().audit_external(plan, packet)
    assert result == {"T0_ms": 10010, "T1_ms": 12010, "span_ms": 2000,
                      "charged_FULL_seconds": 60}


@pytest.mark.parametrize("fault", ["wrong-author", "wrong-command", "wrong-request",
                                  "late", "reset-clock", "backwards", "live-session",
                                  "nonzero", "truncated", "boolean-clock", "no-suffix"])
def test_external_actual_counterexamples_stop(fault: str) -> None:
    plan, packet = external_fixture()
    row = packet["responses"][0]
    if fault == "wrong-author":
        packet["author"] = "/root/old-closed-author"
    elif fault == "wrong-command":
        packet["request"]["cmd"] += "; true"
    elif fault == "wrong-request":
        row["arguments"]["workdir"] = "/another"
    elif fault == "late":
        row["returned_ms"] = row["requested_ms"] + 50001
    elif fault == "reset-clock":
        row["requested_ms"] = 59000
        row["returned_ms"] = 61000
    elif fault == "backwards":
        row["returned_ms"] = row["requested_ms"] - 1
    elif fault == "live-session":
        row["result"]["session_id"] = 123
    elif fault == "nonzero":
        row["result"]["exit_code"] = 1
    elif fault == "truncated":
        row["result"]["output"] = "Warning: truncated output"
    elif fault == "boolean-clock":
        row["requested_ms"] = True
    elif fault == "no-suffix":
        plan["global_end_unix_ns"] = plan["start_unix_ns"] + 7259 * 10**9
    with pytest.raises(ValueError):
        auditor().audit_external(plan, packet)


def test_poll_gap_is_charged_and_only_owned_empty_poll_is_accepted() -> None:
    plan, packet = external_fixture()
    first = packet["responses"][0]
    first["result"] = {"output": "", "session_id": 123}
    packet["responses"].append(
        {"tool": "write_stdin", "arguments": {"session_id": 123, "chars": "",
                                                "yield_time_ms": 1000},
         "requested_ms": 57000, "returned_ms": 58000,
         "result": {"output": "", "exit_code": 0}}
    )
    assert auditor().audit_external(plan, packet)["span_ms"] == 47990
    packet["responses"][-1]["arguments"]["chars"] = "x"
    with pytest.raises(ValueError):
        auditor().audit_external(plan, packet)


@pytest.fixture(scope="module")
def fake_capture(tmp_path_factory):
    """Run the declared fake-CLI integration once; this is no real Docker proof."""
    tmp_path = tmp_path_factory.mktemp("independent-audit-fake-only")
    root = Path(__file__).parents[1]
    test_path = root / "tests/test_public_containment_entry.py"
    spec = importlib.util.spec_from_file_location("public_entry_fixture", test_path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    fixture.test_both_cases_observe_actual_helper_entry_and_work_exits(tmp_path)
    finished_ms = time.time_ns() // 1_000_000
    static_raw = (tmp_path / "plan.json").read_bytes()
    output = tmp_path / "output"
    runtime_raw = (output / "runtime-plan.json").read_bytes()
    runtime = json.loads(runtime_raw)
    argv = runtime["entry_argv"]
    request = {"cmd": shlex.join(argv), "workdir": str(root), "yield_time_ms": 30000,
               "max_output_tokens": 1000}
    external = {"schema": "topolab.public-containment.actual-call.v1", "author": "/root",
                "argv": argv, "request": request,
                "responses": [{"tool": "exec_command", "arguments": copy.deepcopy(request),
                               "requested_ms": runtime["start_unix_ns"] // 1_000_000,
                               "returned_ms": finished_ms,
                               "result": {"output": "", "exit_code": 0}}]}
    artifacts = {}
    for name in ("entry-before-return.json", "worker-supervision/before-launch.json",
                 "worker-supervision/complete-before-own-return.json",
                 "driver/driver-before-return.json"):
        artifacts[name] = (output / name).read_bytes()
    for index in (0, 1):
        for name in ("case-before-return.json", "ticket.json", "payload.log",
                     "controller-entry-before-return.json", "controller-work-actual.json",
                     "controller-started.json", "controller-before-return.json",
                     "controller-kill-request.json", "watchdog-ready.json",
                     "watchdog-before-return.json", "watchdog-entry-before-return.json"):
            path = output / "driver" / str(index) / name
            if path.is_file():
                artifacts[f"driver/{index}/{name}"] = path.read_bytes()
    names = ("public_containment_entry.py", "public_containment_driver.py",
             "public_deadline_guardian.py", "public_worker_deadline.py",
             "public_containment_audit.py")
    sources = {name: (root / "scripts" / name).read_bytes() for name in names}
    assert all(hashlib.sha256(sources[name]).hexdigest() == pin
               for name, pin in json.loads(static_raw)["source_sha256"].items())
    return static_raw, runtime_raw, artifacts, external, sources, str(tmp_path / "plan.json")


def test_complete_fake_cli_raw_replay_is_not_input_acceptance(fake_capture) -> None:
    result = auditor()._audit_graph(*fake_capture)
    assert result["status"] == "PUBLIC_CONTAINMENT_RAW_REPLAY_COMPLETE"
    assert result["input_accepted"] is result["seed17_repaired"] is False


@pytest.mark.parametrize("fault", ["missing-case", "source-change", "wrong-static",
                                  "wrong-runtime", "own-return-claim", "missing-helper-exit",
                                  "controller-not-killed", "namespace-survivor",
                                  "wrong-ownership", "missing-native-return", "late-controller",
                                  "boolean-helper-exit"])
def test_full_raw_graph_counterexamples_stop(fake_capture, fault: str) -> None:
    static_raw, runtime_raw, artifacts, external, sources, path = copy.deepcopy(fake_capture)
    subject = auditor()

    def change(name, mutate):
        value = json.loads(artifacts[name])
        mutate(value)
        artifacts[name] = subject.canonical(value)

    if fault == "missing-case":
        artifacts.pop("driver/1/ticket.json")
    elif fault == "source-change":
        sources["public_containment_driver.py"] += b"\n# changed\n"
    elif fault == "wrong-static":
        static_raw += b" "
    elif fault == "wrong-runtime":
        value = json.loads(runtime_raw)
        value["start_unix_ns"] += 1
        runtime_raw = subject.canonical(value)
    elif fault == "own-return-claim":
        change("entry-before-return.json", lambda x: x.update(own_future_tool_return="PASS"))
    elif fault == "missing-helper-exit":
        change("driver/driver-before-return.json",
               lambda x: x["cases"][1]["helpers"]["watchdog"].update(actual_exit=None))
    elif fault == "controller-not-killed":
        change("driver/1/controller-work-actual.json", lambda x: x.update(work_actual_exit=0))
    elif fault == "namespace-survivor":
        change("driver/1/watchdog-before-return.json",
               lambda x: x["stopped_state"].update(Running=True, Pid=123))
    elif fault == "wrong-ownership":
        change("driver/0/ticket.json", lambda x: x["case"].update(owner="f" * 64))
    elif fault == "missing-native-return":
        external["responses"][-1]["result"]["session_id"] = 123
    elif fault == "late-controller":
        stopped = json.loads(artifacts["driver/1/watchdog-before-return.json"])
        kill = next(row for row in stopped["cli_rows"] if row["argv"][2] == "kill")
        work = json.loads(artifacts["driver/1/controller-work-actual.json"])
        for clock in ("unix", "monotonic"):
            work["work_waited_" + clock + "_ns"] = kill["requested_" + clock + "_ns"] + 1
        artifacts["driver/1/controller-work-actual.json"] = subject.canonical(work)
        case = json.loads(artifacts["driver/1/case-before-return.json"])
        case["controller_work_actual"] = work
        artifacts["driver/1/case-before-return.json"] = subject.canonical(case)
        report = json.loads(artifacts["driver/driver-before-return.json"])
        report["cases"][1] = case
        artifacts["driver/driver-before-return.json"] = subject.canonical(report)
    elif fault == "boolean-helper-exit":
        case = json.loads(artifacts["driver/0/case-before-return.json"])
        case["helpers"]["watchdog"]["actual_exit"] = False
        artifacts["driver/0/case-before-return.json"] = subject.canonical(case)
        report = json.loads(artifacts["driver/driver-before-return.json"])
        report["cases"][0] = case
        artifacts["driver/driver-before-return.json"] = subject.canonical(report)
    with pytest.raises((ValueError, KeyError)):
        subject._audit_graph(static_raw, runtime_raw, artifacts, external, sources, path)


def test_actual_audit_rejects_declared_fake_fixture(fake_capture) -> None:
    with pytest.raises(ValueError, match="exact NEW budget/end"):
        auditor().audit(*fake_capture)


def test_exact_published_worker_serialization_is_not_rewritten(fake_capture) -> None:
    static_raw, runtime_raw, artifacts, external, sources, path = copy.deepcopy(fake_capture)
    subject = auditor()
    name = "worker-supervision/complete-before-own-return.json"
    artifacts[name] = subject.canonical(json.loads(artifacts[name]))
    with pytest.raises(ValueError, match="published-worker receipt serialization"):
        subject._audit_graph(static_raw, runtime_raw, artifacts, external, sources, path)


def test_package_hash_and_new_namespace_are_checked_before_read(tmp_path: Path) -> None:
    subject = auditor()
    with pytest.raises(ValueError, match="package raw SHA"):
        subject.audit_package(b"{}\n", "0" * 64, "0" * 64)
    with pytest.raises(ValueError, match="outside new admitted evidence namespace"):
        subject.audit_file(str(tmp_path / "not-opened"), "0" * 64, "0" * 64)
    assert not list(tmp_path.iterdir())


def test_fake_cli_cannot_be_promoted_by_replacing_only_fixture_marker_and_budget(fake_capture):
    authority = json.loads(fake_capture[0])
    subject = auditor()
    authority.pop("fixture_authority", None)
    authority.update(owner_budget_sha256=subject.BUDGET_SHA256,
                     global_end_unix_ns=subject.GLOBAL_END_UNIX_NS)
    with pytest.raises(ValueError, match="actual Docker/Python/runtime software pin"):
        subject._actual_authority(authority)


@pytest.mark.parametrize("fault", ["before-launch", "future-return"])
def test_original_worker_pending_and_future_flags_are_bound(fake_capture, fault):
    static_raw, runtime_raw, artifacts, external, sources, path = copy.deepcopy(fake_capture)
    subject = auditor()
    name = "worker-supervision/before-launch.json"
    before = json.loads(artifacts[name])
    if fault == "before-launch":
        before["status"] = "WORKER_EXITED"
    else:
        before["own_future_tool_exit"] = "PASS"
        complete_name = "worker-supervision/complete-before-own-return.json"
        complete = json.loads(artifacts[complete_name])
        complete["own_future_tool_exit"] = "PASS"
        artifacts[complete_name] = (json.dumps(complete, sort_keys=True) + "\n").encode()
        entry = json.loads(artifacts["entry-before-return.json"])
        entry["worker_report"] = complete
        artifacts["entry-before-return.json"] = subject.canonical(entry)
    artifacts[name] = (json.dumps(before, sort_keys=True) + "\n").encode()
    with pytest.raises(ValueError):
        subject._audit_graph(static_raw, runtime_raw, artifacts, external, sources, path)
