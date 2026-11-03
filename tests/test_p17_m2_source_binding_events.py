"""Actual-event filing over NEW public files; tool-shaped fixtures are not preflight.

The fixture exercises production packet ingestion and the inherited return-hash
checker without launching a native role or claiming any actual MCP execution.
"""

import importlib.util
import os
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
ROLE = "binding-producer"
PUBLIC_NS = 1790843026136346728


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, REPO / relative)
    assert spec and spec.loader
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


def write_new(producer, path, value):
    raw = producer.canonical(value)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
    return producer.sha(raw)


def public_subject(tmp_path):
    producer = module("event_filing_producer", "scripts/p17_m2_source_binding.py")
    native = module("event_filing_native", "scripts/p17_m2_source_binding_native.py")
    # These are separately authored public scalar samples, never native results.
    fixture = module("event_public_scalar_samples", "tests/test_p17_m2_source_binding_native.py")
    plan, evidence, events = fixture.native_subject(native)
    root = tmp_path / "topolab-public-strict-binding-event-roundtrip"
    root.mkdir(mode=0o700)
    (root / "receipts").mkdir(mode=0o700)
    plan["root"] = str(root)
    evidence["pending"]["public_integer_ns"] = PUBLIC_NS
    fixture.reseal(native, plan, evidence, events)
    plan_sha = write_new(producer, root / "plan.json", plan)
    pinned = producer.load_plan(root / "plan.json", plan_sha)
    write_new(producer, root / "receipts" / (ROLE + "-pending.json"), evidence["pending"])
    wire = {key: evidence[key] for key in ("pending", "completion")}
    write_new(producer, root / "receipts" / (ROLE + "-wire.json"), wire)
    return producer, native, pinned, evidence, events, wire


def raw_packet(producer, native, plan, sample_event, mode, output, *, polls=True):
    """A declared raw-tool shape; its integer endpoints are JSON data only."""
    argv = native.argv_for(plan, mode, ROLE)
    request = {"cmd": producer.literal_command(argv), "workdir": str(REPO),
               "max_output_tokens": 20000, "yield_time_ms": 1000}
    start = round(sample_event["start_seconds"] * 1000)
    end = round(sample_event["end_seconds"] * 1000)
    packet = {"schema": "topolab.v2.m2-strict-source-binding.actual-call.v1",
              "author": plan["roles"][ROLE]["author"], "argv": argv,
              "event_id": "public-event-fixture-" + mode, "request": request}
    if polls:
        midpoint = (start + end) // 2
        split = len(output) // 2
        packet["responses"] = [
            {"tool": "exec_command", "arguments": deepcopy(request),
             "requested_ms": start, "returned_ms": midpoint,
             "result": {"output": output[:split], "session_id": 811,
                        "wall_time_seconds": (midpoint - start) / 1000}},
            {"tool": "write_stdin", "arguments": {"session_id": 811, "chars": "",
                                                   "yield_time_ms": 1000},
             "requested_ms": midpoint, "returned_ms": end,
             "result": {"output": output[split:], "exit_code": 0,
                        "wall_time_seconds": (end - midpoint) / 1000}},
        ]
    else:
        packet["responses"] = [
            {"tool": "exec_command", "arguments": deepcopy(request),
             "requested_ms": start, "returned_ms": end,
             "result": {"output": output, "exit_code": 0,
                        "wall_time_seconds": (end - start) / 1000}},
        ]
    return packet


def file_packet(producer, plan, mode, packet):
    path = Path(plan["root"]) / (mode + "-public-raw-call.json")
    packet_sha = write_new(producer, path, packet)
    return producer.file_actual_event(plan, ROLE, mode, path, packet_sha)


def test_filed_record_return_binds_both_pending_and_completion_from_public_roundtrip(tmp_path):
    producer, native, plan, evidence, samples, wire = public_subject(tmp_path)
    for index, mode in enumerate(("supervise", "record")):
        output = producer.canonical(
            {"status": "PENDING_EXTERNAL_EXIT", "controller_exit": 0}
            if mode == "supervise" else wire).decode()
        packet = raw_packet(producer, native, plan, samples[index], mode, output)
        if mode == "record":
            assert str(PUBLIC_NS) in "".join(row["result"]["output"]
                                             for row in packet["responses"])
        result = file_packet(producer, plan, mode, packet)
    actuals, _ = producer.read_metadata(
        Path(plan["root"]) / (ROLE + "-events.json"), 2 * 1024**2,
        expected=result["events_sha256"], canonical_required=True)
    expected_pending = producer.sha(producer.canonical(evidence["pending"]))
    expected_completion = producer.sha(producer.canonical(evidence["completion"]))
    assert actuals[-1]["observed_pending_sha256"] == expected_pending
    assert actuals[0]["observed_pending_sha256"] == expected_pending
    assert actuals[-1]["observed_completion_sha256"] == expected_completion
    inherited = producer.load("p17_m2_content_verified_independent")
    inherited._actual_record_return(evidence["pending"], evidence["completion"], actuals)


@pytest.mark.parametrize("corruption", [
    "wrong_author", "wrong_command", "unowned_poll", "nonempty_poll", "missing_terminal",
    "truncated_output", "too_many_responses", "poll_wait_too_long",
])
def test_invalid_actual_packet_stops_before_event_publication(tmp_path, corruption):
    producer, native, plan, _, samples, _ = public_subject(tmp_path)
    output = producer.canonical({"status": "PENDING_EXTERNAL_EXIT", "controller_exit": 0}).decode()
    packet = raw_packet(producer, native, plan, samples[0], "supervise", output)
    if corruption == "wrong_author":
        packet["author"] = "/root/binding_route_independent_v1"
    elif corruption == "wrong_command":
        packet["request"]["cmd"] += " --not-registered"
        packet["responses"][0]["arguments"] = deepcopy(packet["request"])
    elif corruption == "unowned_poll":
        packet["responses"][1]["arguments"]["session_id"] = 812
    elif corruption == "nonempty_poll":
        packet["responses"][1]["arguments"]["chars"] = "unexpected input"
    elif corruption == "missing_terminal":
        packet["responses"][1]["result"].pop("exit_code")
        packet["responses"][1]["result"]["session_id"] = 811
    elif corruption == "poll_wait_too_long":
        packet["responses"][1]["arguments"]["yield_time_ms"] = 30001
    elif corruption == "truncated_output":
        packet["responses"][1]["result"].update(
            output="Warning: truncated output (original token count: 20001)\n...",
            original_token_count=20001)
    else:
        start, end = (packet["responses"][0]["requested_ms"],
                      packet["responses"][-1]["returned_ms"])
        responses = []
        for index in range(18):
            terminal = index == 17
            result = {"output": output if terminal else "",
                      "wall_time_seconds": 0.0}
            result.update({"exit_code": 0} if terminal else {"session_id": 811})
            responses.append({
                "tool": "exec_command" if index == 0 else "write_stdin",
                "arguments": deepcopy(packet["request"]) if index == 0
                else {"session_id": 811, "chars": "", "yield_time_ms": 1000},
                "requested_ms": start + (end - start) * index // 18,
                "returned_ms": start + (end - start) * (index + 1) // 18,
                "result": result,
            })
        packet["responses"] = responses
    with pytest.raises(ValueError):
        file_packet(producer, plan, "supervise", packet)
    assert not (Path(plan["root"]) / (ROLE + "-supervise-actual-event.json")).exists()


def test_record_stdout_must_match_exact_wire_without_rounding_integer_ns(tmp_path):
    producer, native, plan, _, samples, wire = public_subject(tmp_path)
    output = producer.canonical({"status": "PENDING_EXTERNAL_EXIT", "controller_exit": 0}).decode()
    file_packet(producer, plan, "supervise",
                raw_packet(producer, native, plan, samples[0], "supervise", output))
    altered = deepcopy(wire)
    altered["pending"]["public_integer_ns"] += 1
    record_output = producer.canonical(altered).decode()
    assert str(PUBLIC_NS + 1) in record_output
    packet = raw_packet(producer, native, plan, samples[1], "record", record_output)
    with pytest.raises(ValueError):
        file_packet(producer, plan, "record", packet)
    assert not (Path(plan["root"]) / (ROLE + "-record-actual-event.json")).exists()


def test_pending_changed_after_supervise_is_rejected_before_record_event(tmp_path):
    producer, native, plan, evidence, samples, wire = public_subject(tmp_path)
    output = producer.canonical({"status": "PENDING_EXTERNAL_EXIT", "controller_exit": 0}).decode()
    file_packet(producer, plan, "supervise",
                raw_packet(producer, native, plan, samples[0], "supervise", output))
    changed = deepcopy(evidence["pending"])
    changed["public_integer_ns"] += 1
    (Path(plan["root"]) / "receipts" / (ROLE + "-pending.json")).write_bytes(
        producer.canonical(changed))
    packet = raw_packet(producer, native, plan, samples[1], "record",
                        producer.canonical(wire).decode())
    with pytest.raises(ValueError):
        file_packet(producer, plan, "record", packet)
    assert not (Path(plan["root"]) / (ROLE + "-record-actual-event.json")).exists()
