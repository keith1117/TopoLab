"""New temporary public sources only; no historical input or production dispatch."""

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / (name + ".py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def controls(c):
    return {"schema": "topolab.v2.m2-writer-quiescence.v1",
            "execution_identity": c.STABLE_IDENTITY, "custodian": "/root",
            "no_write_until_release": True, "writers": [],
            "namespaces": {name: {"accepted": True, "basis": "new public fixture only",
                "no_writer_explanation": "temporary fixture owned by this test"}
                for name in c.SOURCE_NAMESPACES},
            "acquisition_ack": {"by": "/root", "UTC_seconds": 1001,
                                "basis": "public acquisition fixture"}}


@pytest.mark.parametrize("replacement", [None, "leaf", "ancestor"])
def test_same_bytes_replacement_is_rejected_with_actual_read_facts(
    tmp_path, monkeypatch, replacement
):
    r = load("p17_m2_input_export")
    parent = tmp_path / "original"
    parent.mkdir()
    (parent / "source").write_bytes(b"abc")
    reader = r.Reader(tmp_path, execution_identity=r.STABLE_IDENTITY, source_identity_checks=True)
    original = reader._closing_stat

    def closing(relative):
        if replacement == "leaf":
            target = parent / "replacement"
            target.write_bytes(b"abc")
            target.replace(parent / "source")
        elif replacement == "ancestor":
            parent.rename(tmp_path / "retained-original")
            parent.mkdir()
            (parent / "source").write_bytes(b"abc")
        return original(relative)

    monkeypatch.setattr(reader, "_closing_stat", closing)
    if replacement:
        with pytest.raises(ValueError, match="path replaced"):
            reader.read("original/source", 3, expected=r.sha(b"abc"))
        failure = reader.failures[0]
        assert failure["returned_bytes"] == 3 and "st_ino" in failure["changed_fields"]
        assert failure["execution_identity"] == r.STABLE_IDENTITY
        assert reader.rows == [] and reader.source_observations == []
    else:
        assert reader.read("original/source", 3, expected=r.sha(b"abc")) == b"abc"
        row = reader.source_observations[0]
        assert row["declared"] == row["before"] == row["after"] == row["closing"]
        assert row["byte_size"] == 3


def test_historical_boolean_cannot_authorize_production_source():
    r = load("p17_m2_input_export")
    with pytest.raises(ValueError, match="closed historical R"):
        r.main(["r0", "--data-root", str(r.DATA), "--output",
                str(r.DATA / r.STABLE_ROOT_NAME / "exporter-r0"), "--authorize-old-read"])


@pytest.mark.parametrize("fault", ["missing_isolation", "other_interpreter", "extra_flag"])
def test_actual_producer_invocation_cannot_invent_isolation(monkeypatch, fault):
    r = load("p17_m2_input_export")
    args = ["r0", "--data-root", str(r.DATA), "--output",
            str(r.DATA / r.STABLE_ROOT_NAME / "exporter-r0"), "--authorize-old-read",
            "--execution-identity", r.STABLE_IDENTITY, "--plan", "/private/tmp/new-plan.json",
            "--plan-sha", "a" * 64]
    expected = [r.sys.executable, "-I", str(Path(r.__file__).resolve()), *args]
    actual = expected.copy()
    if fault == "missing_isolation":
        actual.remove("-I")
    elif fault == "other_interpreter":
        actual[0] = "/private/tmp/not-the-frozen-interpreter"
    else:
        actual.insert(1, "-B")
    monkeypatch.setattr(r.sys, "orig_argv", actual)
    controller = SimpleNamespace(
        validate_stable_source_entry=lambda *unused: {"roles": {"exporter-r0": {"argv": expected}}},
        resolved=lambda argv, sha: argv)
    loader = SimpleNamespace(exec_module=lambda _: None)
    monkeypatch.setattr(r.importlib.util, "spec_from_file_location",
                        lambda *unused: SimpleNamespace(loader=loader))
    monkeypatch.setattr(r.importlib.util, "module_from_spec", lambda unused: controller)
    with pytest.raises(ValueError, match="actual source argv"):
        r.main(args)  # Rejected before output.resolve or Reader/any DATA stat.


@pytest.mark.parametrize("fault", [None, "coverage", "missing_namespace", "empty_basis",
                                   "no_writer", "unacknowledged", "late_ack"])
def test_unknown_or_uncontrolled_writer_refuses(fault):
    c = load("p17_m2_input_export_control")
    statement = controls(c)
    first = next(iter(statement["namespaces"].values()))
    if fault == "coverage":
        first["accepted"] = "UNKNOWN"
    elif fault == "missing_namespace":
        statement["namespaces"].pop(next(iter(statement["namespaces"])))
    elif fault == "empty_basis":
        first["basis"] = ""
    elif fault == "no_writer":
        first.pop("no_writer_explanation")
    elif fault == "unacknowledged":
        statement["writers"] = [{"name": "new-public-generator",
            "namespace": "b3-v1-data", "action": "pause", "status": "REQUESTED",
            "evidence": "not actually paused"}]
    elif fault == "late_ack":
        statement["acquisition_ack"]["UTC_seconds"] = 1301
    if fault:
        with pytest.raises((ValueError, KeyError)):
            c.stable_controls_checked(statement, 1000)
    else:
        c.stable_controls_checked(statement, 1000)


def test_source_entry_is_consumed_once_before_any_original_access(tmp_path, monkeypatch):
    c = load("p17_m2_input_export_control")
    plan = {"source_controls": controls(c)}
    monkeypatch.setattr(c, "configure_stable", lambda: None)
    monkeypatch.setattr(c, "ROOT", tmp_path)
    monkeypatch.setattr(c, "plan_checked", lambda *args: plan)
    monkeypatch.setattr(c, "stable_lease_checked", lambda *args: None)
    monkeypatch.setattr(c, "source_gate", lambda *args: None)
    assert c.validate_stable_source_entry(tmp_path / "plan", "a" * 64, "exporter-r0") == plan
    with pytest.raises(FileExistsError):
        c.validate_stable_source_entry(tmp_path / "plan", "a" * 64, "exporter-r0")
    assert json.loads((tmp_path / "source-access-exporter-r0.json").read_bytes())["retry"] is False


def test_actual_closed_protocol_cannot_reopen_unused_formal_allowance():
    c = load("p17_m2_input_export_control")
    protocol = json.loads((REPO / c.STABLE_PROTOCOL).read_bytes())
    assert protocol["actual_admission"]["formal_FULL_paid_seconds"] == 0
    with pytest.raises(ValueError, match="closed unlaunched"):
        c.stable_authority_checked(protocol)


def test_large_collector_stays_complete_on_disk_and_bounded_on_wire(tmp_path, monkeypatch):
    c = load("p17_m2_input_export_control")
    monkeypatch.setattr(c, "ROOT", tmp_path)
    (tmp_path / "receipts").mkdir()
    completion = {"status": "PENDING_EXTERNAL_EXIT", "cleanup": {"group_gone": True},
        "resource_components": [{"samples_bytes": [100, 200]}], "primary_failure": None,
        "secondary_failures": [], "available_outer_records": {"large": "x" * 400000},
        "available_native_evidence": {str(i): {"sha256": "a" * 64} for i in range(4096)}}
    packet = {"pending": {}, "completion": completion, "resourceEvidence": {"status": "new"}}
    wire = c.stable_wire_packet(packet, "exporter-r0")
    assert len(c.canonical(wire)) < 2000
    assert wire["completion"]["cleanup"] == completion["cleanup"]
    assert wire["completion"]["resource_components"] == completion["resource_components"]
    full = (tmp_path / wire["full_collector_record"]["path"]).read_bytes()
    assert json.loads(full) == packet and len(full) > 400000
    assert c.digest(full) == wire["full_collector_record"]["sha256"]


def test_late_resource_wire_growth_fails_without_shortened_cleanup_pass():
    c = load("p17_m2_input_export_control")
    completion = {key: "public" for key in (
        "execution_identity", "role", "plan_sha256", "frozen_FULL_seconds", "clock_domain",
        "clock_resolution_seconds", "actor_activation_UTC_seconds", "actor_window_seconds",
        "actor_deadlines_UTC", "pending_sha256")}
    completion.update(status="PENDING_EXTERNAL_EXIT", cleanup={"group_gone": True},
                      resource_components=[{"samples_bytes": [100, 200]}],
                      final_serializer_pid=123, primary_failure=None)
    collector = {"path": "receipts/exporter-r0-final-wire-source.json", "sha256": "a" * 64}
    packet = {"pending": {}, "completion": completion,
              "resourceEvidence": {"late_growth": "x" * 32768}}
    wire = c.bounded_stable_wire(packet, collector)
    assert len(c.canonical(wire)) < 32768
    assert wire["completion"]["status"] == "FAILED_INTERNAL_COMPLETION"
    assert wire["completion"]["cleanup"]["group_gone"] is None
    assert wire["completion"]["resource_components"][0]["samples_bytes"] == [100, 200]
    assert wire["full_collector_record"] == collector


@pytest.mark.parametrize("state", ["gone", "delayed", "permission", "persistent", "overrun"])
def test_cleanup_retains_initial_and_final_facts_without_relaunch(monkeypatch, state):
    c = load("p17_m2_resource_control")
    child = SimpleNamespace(returncode=0, registered_command_pids=())
    now, probes, signals = [0.0], [], []
    monkeypatch.setattr(c, "monotonic", lambda: now[0])
    monkeypatch.setattr(c, "sleep", lambda value: now.__setitem__(0, now[0] + value
                                              + (0.001 if state == "overrun" else 0)))
    monkeypatch.setattr(c, "_native_poll", lambda child: child.returncode)
    monkeypatch.setattr(c, "_native_wait", lambda *args: 0)

    def signal(group, sig):
        assert group == 98765
        if sig:
            signals.append(sig.name)
            return
        probes.append(now[0])
        if state == "gone" or (state == "delayed" and len(probes) >= 4):
            raise ProcessLookupError
        if state == "permission":
            raise PermissionError

    monkeypatch.setattr(c.os, "killpg", signal)
    result = c._terminate(98765, child)
    assert result["leader_exit"] == 0 and len(signals) <= 2
    assert result["initial_group_gone"] is (True if state == "gone" else
                                            None if state == "permission" else False)
    assert result["final_group_gone"] is (True if state in ("gone", "delayed") else
                                          None if state == "permission" else False)
    assert result["group_gone"] == result["final_group_gone"]
    if state == "overrun":
        assert result["observation_limit_exceeded"] is True
    if state == "delayed":
        assert result["observations"][0]["group_gone"] is False
        assert 0 < result["post_signal_observation_seconds"] <= 5


@pytest.mark.parametrize("fault", ["missing_profile", "invalid_log", "child_failure"])
def test_final_helper_failure_keeps_parent_rss_exit_and_primary(
    tmp_path, monkeypatch, capsys, fault
):
    c = load("p17_m2_input_export_control")
    monkeypatch.setattr(c, "ROOT", tmp_path / "new-results")
    monkeypatch.setattr(c, "FINAL_HELPER_ROOT", tmp_path / "new-helper")
    monkeypatch.setattr(c, "final_packet_checked", lambda *args: {})
    expected = [c.sys.executable, "-I", str(Path(c.__file__).resolve()), "final-file", "--r-stable",
                "--plan", str(c.ROOT / "launch_plan.json"), "--plan-sha", "a" * 64]
    plan = {"final_helper_root": str(c.FINAL_HELPER_ROOT), "final_filing_child_argv": expected}
    child = {"exit_code": 1 if fault == "child_failure" else 0,
             "software_result": "FAIL_PUBLIC_COMMAND" if fault == "child_failure"
             else "PUBLIC_COMMAND_EXIT_OBSERVED", "helpers": []}
    folder = c.FINAL_HELPER_ROOT / "final-filing"
    folder.mkdir(parents=True)
    (folder / "command.log").write_bytes(b"invalid json")
    if fault != "missing_profile":
        (folder / "command.time").write_bytes(b"new fixture")
    monkeypatch.setattr(c.native_recording, "invoke", lambda *args, **kwargs: child)
    monkeypatch.setattr(c.native_recording, "_rss_self", lambda: 1024)
    monkeypatch.setattr(c.independent, "audit_native_record", lambda *args, **kwargs: {})
    assert c.final_helper(plan, "a" * 64) == 1
    packet = json.loads(capsys.readouterr().out)
    assert packet["status"] == "FAILED_INTERNAL_COMPLETION"
    assert packet["controller_RSS_samples_bytes"] == [1024, 1024]
    assert packet["available_child_exit"] == child["exit_code"]
    if fault == "child_failure":
        assert packet["primary_failure"]["stage"] == "final-filing-child"
        assert packet["secondary_failures"][0]["stage"] == "final-filing-recording"


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node unavailable")
def test_final_filing_refuses_unconfirmed_prefix_without_tool():
    script = """
const fs=require('fs'),vm=require('vm'),state=new Map();let calls=0;
const sandbox={module:{exports:{}},load:k=>state.get(k),store:(k,v)=>state.set(k,v),text:()=>{},
 tools:{exec_command:async()=>{calls++;throw Error('no tool allowed');}}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),sandbox);
const c={execution_identity:'topolab.v2.p17-m2-source-stable-export.v1',
 final_helper_external_argv:[],plan_sha256:'a'.repeat(64)};
(async()=>{let stopped=false;try{await sandbox.module.exports.dispatchFinalFilingStable(c);}
 catch(e){stopped=true;}console.log(JSON.stringify({stopped,calls}));})();
"""
    result = subprocess.run(["node", "-e", script,
        str(REPO / "scripts/p17_m2_input_export_dispatch.js")],
        capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == {"stopped": True, "calls": 0}


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node unavailable")
def test_serialization_gap_is_checked_at_actual_first_event():
    script = """
const fs=require('fs'),vm=require('vm'),state=new Map();let calls=0,ticks=0;
const activation=1792533500,clock=[activation+299.99,activation+300.001];
const sandbox={module:{exports:{}},load:k=>state.get(k),store:(k,v)=>state.set(k,v),text:()=>{},
 Date:class extends Date{static now(){return clock[Math.min(ticks++,1)]*1000;}},
 tools:{exec_command:async()=>{calls++;throw Error('no launch after setup300');}}};
vm.runInNewContext(fs.readFileSync(process.argv[1],'utf8'),sandbox);
const caps={'independent-public-check':300,'exporter-r0':300,'independent-r0':300,
 'exporter-r1':1200,'independent-r1':1200,'shared-closeout':300};
const deadline=new Date((activation+4500)*1000).toISOString();
const c={execution_identity:'topolab.v2.p17-m2-source-stable-export.v1',plan_sha256:'a'.repeat(64),
 actor_activation_UTC_seconds:activation,actor_window_seconds:4500,
 actor_deadlines_UTC:{exporter:deadline,independent:deadline},FULL_caps_seconds:caps,
 thread_environment:{},external_argv:{'independent-public-check':[['public1'],['public2']]}};
(async()=>{let stopped=false;try{await sandbox.module.exports.dispatchRoleStable(
 c,'independent-public-check');}catch(e){stopped=true;}console.log(JSON.stringify({stopped,calls,
 attempted:state.has('rstable-attempted-independent-public-check')}));})();
"""
    result = subprocess.run(["node", "-e", script,
        str(REPO / "scripts/p17_m2_input_export_dispatch.js")],
        capture_output=True, text=True, check=True)
    assert json.loads(result.stdout) == {"stopped": True, "calls": 0, "attempted": False}
