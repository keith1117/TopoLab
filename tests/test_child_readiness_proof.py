"""Public control buffers, never business inputs or scheduled Native calls."""

import importlib.util
import io
import json
import sys
import tarfile
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


@pytest.fixture
def proof(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "child_readiness_under_test", SCRIPTS / "child_readiness_proof.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def trace(proof, *, negative=False):
    common = dict(pid=21, ppid=20, pgid=20)
    rows = [dict(kind="trace-start", observer_processes=0)]
    rows.append(dict(kind="readiness", scope="VERIFIED_PRIOR_RELEASE_AND_CANDIDATE_BYTES",
                     sha256=proof.OLD_REPORT, actual_sha256=proof.OLD_ACTUAL,
                     proof_sha256="a" * 64, checkout_head="b" * 40))
    if negative:
        rows.extend([dict(kind="spawn", api="subprocess.Popen", executable="/bin/sleep",
                          argv=["/bin/sleep", "3"], cwd=str(proof.REPO), stack=[["s", "f", 1]]),
                     dict(kind="spawn-return", child_pid=22)])
    else:
        rows.append(dict(kind="trace-complete", plan_sha256="c" * 64, entry_sha256="d" * 64))
    return b"".join(proof.canonical(dict(row, **common, seq=i + 1, time_ns=1000 + i))
                    for i, row in enumerate(rows))


def test_complete_no_child_trace(proof):
    assert proof.check_trace(trace(proof), plan_sha="c" * 64, proof_sha="a" * 64,
                             entry_sha="d" * 64, main="b" * 40, negative=False)["spawn_count"] == 0


def test_active_child_trace_is_preserved_negative(proof):
    result = proof.check_trace(trace(proof, negative=True), plan_sha="c" * 64,
                               proof_sha="a" * 64, entry_sha="d" * 64,
                               main="b" * 40, negative=True)
    assert result["spawn_count"] == 1 and result["spawned_pids"] == [22]


@pytest.mark.parametrize("change", ["duplicate_seq", "clock", "pid", "old_report",
                                    "proof", "main", "entry", "missing_complete", "child"])
def test_changed_or_incomplete_positive_trace_denied(proof, change):
    rows = [proof.parse(row) for row in trace(proof).splitlines()]
    if change == "duplicate_seq":
        rows[-1]["seq"] = 1
    elif change == "clock":
        rows[-1]["time_ns"] = 1
    elif change == "pid":
        rows[-1]["pid"] = 99
    elif change == "old_report":
        rows[1]["sha256"] = "e" * 64
    elif change == "proof":
        rows[1]["proof_sha256"] = "e" * 64
    elif change == "main":
        rows[1]["checkout_head"] = "e" * 40
    elif change == "entry":
        rows[-1]["entry_sha256"] = "e" * 64
    elif change == "missing_complete":
        rows.pop()
    else:
        rows = [proof.parse(row) for row in trace(proof, negative=True).splitlines()]
    with pytest.raises(ValueError):
        proof.check_trace(b"".join(proof.canonical(row) for row in rows), plan_sha="c" * 64,
                          proof_sha="a" * 64, entry_sha="d" * 64,
                          main="b" * 40, negative=False)


def test_same_execution_bytes_are_required_for_both_positive_and_negative(proof):
    runs = [dict(slot=i, source_tree={"scripts/a.py": "a" * 64,
                                     "public-entry": str(i)}, driver_sha256="b" * 64)
            for i in (3, 4, 5)]
    proof.same_candidate(runs)
    changed = deepcopy(runs)
    changed[2]["source_tree"]["scripts/a.py"] = "c" * 64
    with pytest.raises(ValueError, match="candidate"):
        proof.same_candidate(changed)


@pytest.mark.parametrize("slots", [[True, 2, 3], [1, 1, 2], [0, 2, 3], [1, 2, 19], [1, 2]])
def test_slot_shape_is_exact(proof, slots):
    with pytest.raises(ValueError):
        proof.check_slots(slots)


def test_historical_proof_reuses_the_fixed_shared_checker_without_spawn(proof, monkeypatch):
    old = dict(source_main=proof.OLD_MAIN,
               package=dict(path=str(proof.OLD_FORMAL / "certificate-replay.json"),
                            sha256=proof.OLD_REPORT),
               actual=dict(path=str(proof.OLD_FORMAL / "certificate-replay-actual.json"),
                           sha256=proof.OLD_ACTUAL), verified_returned_ms=proof.OLD_RETURNED)
    calls = []
    monkeypatch.setattr(proof, "historical_inputs", lambda: ({"p": 1}, {"t": "a" * 64}))
    monkeypatch.setattr(proof.history(), "verified_readiness",
                        lambda policy, tree: calls.append((policy, tree)) or old)
    monkeypatch.setattr(proof.history().subprocess, "Popen",
                        lambda *a, **k: pytest.fail("measured proof spawned"))
    assert proof.prior_certificate() == old
    assert calls == [({"p": 1}, {"t": "a" * 64})]
    old["package"]["sha256"] = "e" * 64
    with pytest.raises(ValueError, match="historical"):
        proof.prior_certificate()


def readiness_fixture(proof, monkeypatch):
    import r0_read_independent as original

    main, budget_raw = "a" * 40, b"synthetic budget\n"
    monkeypatch.setattr(proof, "BUDGET", proof.sha(budget_raw))
    tree = {name: "b" * 64 for name in (*proof.SOFTWARE, proof.PROTOCOL)}
    slots = [3, 4, 5]
    source = {"freeze/" + name: value for name, value in tree.items()}
    runs = [dict(slot=i, source_tree=dict(source, **{"public-entry": str(i)}),
                 source_main="c" * 40, driver_sha256="d" * 64) for i in slots]
    prior = {"unchanged": "historical verified result"}
    report = dict(status=proof.STATUS, execution_identity=proof.IDENTITY, source_main=main,
                  slots=slots, runs=runs, prior_certificate=prior,
                  budget_sha256=proof.BUDGET, authority_sha256=tree[proof.PROTOCOL],
                  worker_sha256=tree[proof.WORKER], executed={n: tree[n] for n in proof.SOFTWARE},
                  software_tree_sha256=proof.sha(proof.canonical(tree)))
    argv = proof.gate_args(slots)
    request = dict(cmd=original.literal_command(argv), workdir=str(proof.REPO),
                   login=False, yield_time_ms=1000, max_output_tokens=3000)
    packet = dict(schema=original.ACTUAL_SCHEMA, author=proof.AUTHOR, argv=argv, request=request,
                  responses=[dict(tool="exec_command", arguments=deepcopy(request),
                                  requested_ms=proof.START + 1000, returned_ms=proof.START + 2000,
                                  result=dict(exit_code=0, output=""))])
    policy = dict(execution_identity=proof.IDENTITY,
                  new_input_budget=dict(path=str(proof.DATA / "owner-budget.json"),
                                        sha256=proof.BUDGET),
                  child_verification_paths=dict(package=str(proof.FORMAL / proof.PACKAGE),
                                                actual=str(proof.FORMAL / proof.ACTUAL)))
    monkeypatch.setattr(proof.history(), "checkout_commit", lambda _: main)
    monkeypatch.setattr(proof.history().subprocess, "Popen",
                        lambda *a, **k: pytest.fail("measured readiness spawned"))
    monkeypatch.setattr(proof, "prior_certificate", lambda: deepcopy(prior))
    monkeypatch.setattr(proof, "public_run", lambda slot, **_: deepcopy(runs[slots.index(slot)]))
    monkeypatch.setattr(proof, "compiled", lambda *a, **k: {})

    def install(*, output=None):
        report_raw = proof.canonical(report)
        terminal_output = proof.canonical(dict(status=proof.STATUS,
                                               report_sha256=proof.sha(report_raw))).decode()
        packet["responses"][-1]["result"]["output"] = (
            output if output is not None else terminal_output)
        buffers = {"owner-budget.json": budget_raw, proof.PACKAGE: report_raw,
                   proof.ACTUAL: proof.canonical(packet)}
        monkeypatch.setattr(proof, "pair", lambda _, name: buffers[name])
        return report_raw

    install()
    return policy, tree, report, packet, runs, install


def test_measured_readiness_replays_original_return_without_child(proof, monkeypatch):
    policy, tree, report, packet, _runs, _install = readiness_fixture(proof, monkeypatch)
    result = proof.verified_readiness(policy, tree)
    assert result["source_main"] == report["source_main"]
    assert result["verified_returned_ms"] == packet["responses"][-1]["returned_ms"]
    assert result["actual"]["path"] == str(proof.FORMAL / proof.ACTUAL)


@pytest.mark.parametrize("change", ["worker", "authority", "tree", "executed", "status",
                                    "actual_exit", "actor", "clock", "wire", "source_main",
                                    "mixed_candidate", "prior"])
def test_readiness_rejects_changed_software_wire_authority_and_history(proof, monkeypatch, change):
    policy, tree, report, packet, runs, install = readiness_fixture(proof, monkeypatch)
    if change in ("worker", "authority"):
        report[change + "_sha256"] = "e" * 64
    elif change == "tree":
        report["software_tree_sha256"] = "e" * 64
    elif change == "executed":
        report["executed"][proof.LAUNCHER] = "e" * 64
    elif change == "status":
        report["status"] = "producer PASS"
    elif change == "actual_exit":
        packet["responses"][-1]["result"]["exit_code"] = False
    elif change == "actor":
        packet["author"] = "/root"
    elif change == "clock":
        packet["responses"][-1]["returned_ms"] += 300000
    elif change == "source_main":
        report["source_main"] = "e" * 40
    elif change == "mixed_candidate":
        runs[-1]["source_tree"]["freeze/" + proof.WORKER] = "e" * 64
    elif change == "prior":
        report["prior_certificate"] = {"producer": "PASS"}
    install(output="forged return\n" if change == "wire" else None)
    with pytest.raises(ValueError):
        proof.verified_readiness(policy, tree)


def public_fixture(proof, monkeypatch, *, negative=False, released_context=None):
    slot = 7 if negative else 6
    root = f"/private/tmp/topolab-public-child-20261125-a{slot}"
    start = proof.START + 1000
    mode = "released" if released_context is not None else "negative" if negative else "candidate"
    claim = dict(slot=slot, root=root, mode=mode,
                 budget_sha256=proof.BUDGET, charged_FULL=600, start_ms=start,
                 end_ms=start + 420000, checkout_head="b" * 40,
                 driver_sha256="e" * 64, scheduler_sha256="f" * 64)
    source = {"candidate/child_public_control.py": "d" * 64,
              "candidate/certificate_replay_proof.py": "a" * 64,
              "candidate/child_public_schedule.mjs": "e" * 64,
              "freeze/scripts/staged_input_actor.mjs": "f" * 64,
              "public-entry": proof.sha(json.dumps(claim, sort_keys=True).encode())}
    plan = dict(root=root, formal_authority=False, execution_identity=proof.PUBLIC_ID,
                scope=proof.PUBLIC_SCOPE, runtime=dict(cwd=str(proof.REPO)), source_tree=source)
    plan_raw = proof.canonical(plan)
    plan_sha = proof.sha(plan_raw)
    native = dict(pending={"original": "pending"}, completion={"original": "completion"})
    result = dict(full_role_evidence_accepted=not negative, evidence_complete=not negative,
                  actual_exit_codes=[0, 0], RSS_envelope_bytes=None if negative else 1024)
    cleanup = dict(closed_attempt_verified=False, reason="native cleanup remains unknown")
    stopped = dict(result, cleanup_acceptance=cleanup)
    files = {"native/plan.json": plan_raw}
    packets, events = {}, []
    order = ("prepare", "supervise", "file-supervise", "record", "file-record", "bind")
    for i, stage in enumerate(order):
        argv = [proof.PYTHON, "-I", str(proof.REPO / "scripts/child_public_control.py"),
                "prepare-public" if stage == "prepare" else stage, "--root", root]
        if stage != "prepare":
            argv += ["--plan-sha", plan_sha, "--role", proof.ROLE]
        if stage == "prepare":
            output = proof.canonical(dict(plan_sha256=plan_sha))
        elif stage == "supervise":
            output = proof.canonical(dict(status="PENDING_EXTERNAL_EXIT", controller_exit=0))
        elif stage == "record":
            output = proof.canonical(native)
        elif stage == "bind":
            output = proof.canonical(stopped if negative else result)
        else:
            output = proof.canonical(dict(status="ACTUAL_EVENT_FILED",
                                          mode=stage.removeprefix("file-")))
        request = dict(cmd=proof.wire().literal_command(argv), workdir=str(proof.REPO))
        first, last = start + i * 2000, start + i * 2000 + 1000
        packet = dict(schema=proof.wire().ACTUAL_SCHEMA, author="/root", argv=argv,
                      request=request, event_id="event-" + stage,
                      responses=[dict(tool="exec_command", arguments=request,
                                      requested_ms=first, returned_ms=last,
                                      result=dict(exit_code=1 if negative and stage == "bind"
                                                  else 0, output=output.decode()))])
        packets[stage] = packet
        packet_raw = proof.canonical(packet)
        files[f"caller/{stage}-actual.json"] = packet_raw
        if stage in ("supervise", "record"):
            event = dict(event_id=packet["event_id"], raw_packet_sha256=proof.sha(packet_raw),
                         start_seconds=first / 1000, end_seconds=last / 1000)
            files[f"native/{proof.ROLE}-{stage}-actual-event.json"] = proof.canonical(event)
            events.append(event)
    accepted = dict(result=result, raw_tool_events=events)
    files[f"native/{proof.ROLE}-accepted.json"] = proof.canonical(accepted)
    files[f"native/{proof.ROLE}-events.json"] = proof.canonical(events)
    files[f"native/receipts/{proof.ROLE}-wire.json"] = proof.canonical(native)
    folder = f"native/receipts/{proof.ROLE}/{proof.ROLE}/"
    processes = [dict(pid=20, parent=19, pgid=20), dict(pid=21, parent=20, pgid=20)]
    if negative:
        processes.append(dict(pid=22, parent=21, pgid=20))
    files[folder + "command.json"] = proof.canonical(dict(pid=20, samples=[dict(roles=processes)],
        helpers=[], status="PENDING_POSTEXIT",
        software_result="RESOURCE_UNKNOWN_STOP_UNREGISTERED_DESCENDANT" if negative
        else "PUBLIC_COMMAND_EXIT_OBSERVED"))
    for name in (folder + "command.time", folder + "command.log",
                 f"native/receipts/{proof.ROLE}-controller.time"):
        files[name] = b"synthetic native profile\n"
    rows = [proof.parse(line) for line in trace(proof, negative=negative).splitlines()]
    if released_context is not None:
        item = {k: v for k, v in released_context.items() if k != "preflight_returned_ms"}
        item.update(kind="released-readiness", pid=21, ppid=20, pgid=20)
        rows.insert(-1, item)
    for i, row in enumerate(rows):
        row["time_ns"] = (start + 2100) * 10**6 + i
        row["seq"] = i + 1
    if not negative:
        rows[-1]["plan_sha256"] = plan_sha
    files["native/process-trace.jsonl"] = b"".join(proof.canonical(r) for r in rows)
    if negative:
        files["native/STOP.json"] = proof.canonical(stopped)
    calls = []

    def audit(pending, completion, **kwargs):
        assert pending == native["pending"] and completion == native["completion"]
        assert kwargs["raw_tool_events"] == events
        assert kwargs["expected_plan_sha256"] == plan_sha
        assert kwargs["inner_evidence"]["expected_argv"][3] == "payload"
        calls.append(kwargs)
        return deepcopy(result)

    monkeypatch.setitem(sys.modules, "p17_m2_content_verified_independent",
                        SimpleNamespace(audit_role=audit,
                                        check_closed_attempt=lambda *a, **k: cleanup))
    summary = dict(slot=slot, root=root, mode=claim["mode"], plan_sha256=plan_sha,
                   source_tree=source,
                   call_exits={s: 1 if negative and s == "bind" else 0 for s in order})
    return slot, claim, summary, files, calls


@pytest.mark.parametrize("negative", [False, True])
def test_full_original_public_buffer_chain_including_native_replay(proof, monkeypatch, negative):
    slot, claim, summary, files, calls = public_fixture(proof, monkeypatch, negative=negative)
    result = proof.audit_public(slot, claim, summary, files, negative=negative)
    assert result["trace"]["spawn_count"] == int(negative)
    assert len(calls) == 1


@pytest.mark.parametrize("damage", ["stdout", "event", "plan", "window", "exit", "wire"])
def test_public_original_buffer_mutations_stop(proof, monkeypatch, damage):
    slot, claim, summary, files, _calls = public_fixture(proof, monkeypatch)
    if damage == "stdout":
        path = "caller/record-actual.json"
        packet = proof.parse(files[path])
        packet["responses"][0]["result"]["output"] = "different original\n"
        files[path] = proof.canonical(packet)
    elif damage == "event":
        rows = proof.parse(files[f"native/{proof.ROLE}-events.json"])
        rows[0]["raw_packet_sha256"] = "f" * 64
        files[f"native/{proof.ROLE}-events.json"] = proof.canonical(rows)
    elif damage == "plan":
        plan = proof.parse(files["native/plan.json"])
        plan["formal_authority"] = True
        files["native/plan.json"] = proof.canonical(plan)
    elif damage == "window":
        claim["end_ms"] -= 420000
    elif damage == "exit":
        path = "caller/bind-actual.json"
        packet = proof.parse(files[path])
        packet["responses"][0]["result"]["exit_code"] = False
        files[path] = proof.canonical(packet)
    else:
        files[f"native/receipts/{proof.ROLE}-wire.json"] = proof.canonical(dict(
            pending={"changed": True}, completion={}))
    with pytest.raises((ValueError, AssertionError)):
        proof.audit_public(slot, claim, summary, files, negative=False)


def test_child_independent_profile_uses_new_namespace_and_complete_software_tree(monkeypatch):
    from test_certificate_software_context import (
        profile,
        test_window_software_selection_equals_producer_complete_tree,
    )

    profiles, checker = profile("CHILD_FORMAL")
    raw = (SCRIPTS.parent / checker.REGISTERED_PROTOCOL).read_bytes()
    pinned = checker._prior_public_module()
    monkeypatch.setattr(checker.native, "_software_bytes", lambda _: raw)
    monkeypatch.setattr(checker, "_prior_public_module", lambda *_: pinned)
    digest = checker.digest(raw)
    plan = dict(scope=checker.FORMAL_SCOPE, source_tree={checker.REGISTERED_PROTOCOL: digest},
                binding=dict(preparation_protocol_sha256=digest),
                preparation_contract_sha256=digest)
    policy = checker._registered_authority(plan)
    assert checker._formal_only_profile()
    assert policy["prior_public"] == pinned.expected_prior(pinned.CHILD_EVIDENCE)
    assert profiles.PROOF_MODULES[profiles.CHILD_FORMAL] == (
        "child_verification", "child_readiness_proof")
    # Restore the byte reader before the existing whole-tree comparison seam.
    monkeypatch.undo()
    test_window_software_selection_equals_producer_complete_tree(monkeypatch, "CHILD_FORMAL")


def test_child_preflight_binds_original_return_to_its_independent_proof(monkeypatch):
    from test_formal_input_independent import preflight_fixture

    checker, plan, actual_raw, expected, calls = preflight_fixture(monkeypatch, child=True)
    assert checker._registered_preflight(plan, actual_raw) == expected
    assert "child_verification" in expected and len(calls) == 1


@pytest.mark.parametrize("damage", ["r0-ready", "r0-closure", "r0-stdout", "r0-late",
                                    "actual-exit-bool"])
def test_child_preflight_rejects_unbound_or_failed_proof(monkeypatch, damage):
    from test_formal_input_independent import preflight_fixture

    checker, plan, actual_raw, _expected, _calls = preflight_fixture(
        monkeypatch, child=True, damage=damage)
    with pytest.raises(ValueError):
        checker._registered_preflight(plan, actual_raw)


@pytest.mark.parametrize("damage", ["unsampled", "parent", "time", "driver", "scheduler"])
def test_child_negative_requires_actual_sample_and_frozen_schedule(proof, monkeypatch, damage):
    slot, claim, summary, files, _calls = public_fixture(proof, monkeypatch, negative=True)
    if damage == "unsampled":
        path = f"native/receipts/{proof.ROLE}/{proof.ROLE}/command.json"
        command = proof.parse(files[path])
        command["samples"][0]["roles"].pop()
        files[path] = proof.canonical(command)
    elif damage in ("parent", "time"):
        rows = [proof.parse(line) for line in files["native/process-trace.jsonl"].splitlines()]
        for row in rows:
            if damage == "parent":
                row["ppid"] = 99
            else:
                row["time_ns"] += 1000000000000
        files["native/process-trace.jsonl"] = b"".join(proof.canonical(row) for row in rows)
    else:
        claim[damage + "_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        proof.audit_public(slot, claim, summary, files, negative=True)


def archive_fixture(proof, *, duplicate=False, link=False):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:gz") as archive:
        info = tarfile.TarInfo("native/plan.json")
        raw = b"{}\n"
        info.size = len(raw)
        if link:
            info.type = tarfile.SYMTYPE
            info.linkname = "/unregistered/file"
        archive.addfile(info, io.BytesIO(raw))
        if duplicate:
            archive.addfile(info, io.BytesIO(raw))
    index = {"native/plan.json": dict(bytes=len(raw), sha256=proof.sha(raw))}
    return stream.getvalue(), index


def test_archive_replays_complete_bounded_member_inventory(proof):
    raw, index = archive_fixture(proof)
    assert proof.archive_buffers(raw, proof.canonical(index)) == {"native/plan.json": b"{}\n"}


@pytest.mark.parametrize("damage", ["duplicate", "link", "hash", "extra", "bool_size"])
def test_archive_refuses_member_aliases_or_changed_bytes(proof, damage):
    raw, index = archive_fixture(proof, duplicate=damage == "duplicate", link=damage == "link")
    if damage == "hash":
        index["native/plan.json"]["sha256"] = "e" * 64
    elif damage == "extra":
        index["not-archived"] = dict(bytes=1, sha256="e" * 64)
    elif damage == "bool_size":
        index["native/plan.json"]["bytes"] = True
    with pytest.raises(ValueError):
        proof.archive_buffers(raw, proof.canonical(index))


def released_fixture(proof, monkeypatch):
    import r0_read_independent as original
    from p17_m2_content_verified_independent import _software_bytes

    policy, tree, child_report, child_packet, _old_runs, _install = readiness_fixture(
        proof, monkeypatch)
    policy.update(readiness_path=str(proof.FORMAL / "input-activation-readiness-a1.json"),
                  independent_preflight_actual_path=str(
                      proof.FORMAL / "input-preflight-actual-a1.json"),
                  child_released_paths=dict(package=str(proof.FORMAL / proof.RELEASED_PACKAGE),
                                            actual=str(proof.FORMAL / proof.RELEASED_ACTUAL)),
                  actors=dict(executor="/root", independent=proof.AUTHOR))
    policy_raw = proof.canonical(policy)
    tree[proof.PROTOCOL] = proof.sha(policy_raw)
    child_report["authority_sha256"] = tree[proof.PROTOCOL]
    child_report["software_tree_sha256"] = proof.sha(proof.canonical(tree))
    child_raw = proof.canonical(child_report)
    child_packet["responses"][0]["result"]["output"] = proof.canonical(dict(
        status=proof.STATUS, report_sha256=proof.sha(child_raw))).decode()
    child_actual_raw = proof.canonical(child_packet)
    child = dict(source_main=child_report["source_main"], verified_returned_ms=proof.START + 2000,
                 package=dict(path=str(proof.FORMAL / proof.PACKAGE), sha256=proof.sha(child_raw)),
                 actual=dict(path=str(proof.FORMAL / proof.ACTUAL),
                             sha256=proof.sha(child_actual_raw)))
    ready = dict(schema="topolab.registered-input.activation-readiness.v1",
                 execution_identity=proof.IDENTITY, actors=policy["actors"],
                 new_input_budget=policy["new_input_budget"], child_verification=child,
                 published_source_sha256={k: v for k, v in tree.items() if k != proof.PROTOCOL},
                 runtime=dict(python=proof.PYTHON, cwd=str(proof.REPO)))
    ready_raw = proof.canonical(ready)
    preflight_argv = [proof.PYTHON, "-I", str(proof.REPO / "scripts/child_formal_registered.py"),
                      "preflight", "--readiness-sha", proof.sha(ready_raw)]
    preflight_summary = dict(status="PASS_REGISTERED_INPUT_METADATA_PREFLIGHT",
                             execution_identity=proof.IDENTITY, author=proof.AUTHOR,
                             readiness_path=policy["readiness_path"],
                             readiness_sha256=proof.sha(ready_raw),
                             published_source_sha256=ready["published_source_sha256"],
                             runtime=ready["runtime"], actors=policy["actors"],
                             new_input_budget=policy["new_input_budget"], source_stat_reads=0,
                             target_stat_reads=0, own_future_return="NOT_CLAIMED",
                             child_verification=child)

    def packet(argv, first, last, output):
        request = dict(cmd=original.literal_command(argv), workdir=str(proof.REPO))
        return dict(schema=original.ACTUAL_SCHEMA, author=proof.AUTHOR, argv=argv, request=request,
                    responses=[dict(tool="exec_command", arguments=deepcopy(request),
                                    requested_ms=first, returned_ms=last,
                                    result=dict(exit_code=0, output=output))])

    preflight = packet(preflight_argv, proof.START + 3000, proof.START + 4000,
                       proof.canonical(preflight_summary).decode())
    preflight_raw = proof.canonical(preflight)
    context = dict(readiness_sha256=proof.sha(ready_raw),
                   new_proof_package_sha256=child["package"]["sha256"],
                   new_proof_actual_sha256=child["actual"]["sha256"],
                   source_main=child["source_main"],
                   software_tree_sha256=proof.sha(proof.canonical(tree)),
                   preflight_actual_sha256=proof.sha(preflight_raw),
                   preflight_returned_ms=proof.START + 4000)
    slots = [6, 7]
    runs = [dict(slot=n, mode="released", original_end_ms=proof.START + 9000 + i * 1000,
                 source_main=child["source_main"],
                 source_tree={"freeze/" + k: v for k, v in tree.items()},
                 driver_sha256="d" * 64) for i, n in enumerate(slots)]
    report = dict(status=proof.RELEASED_STATUS, execution_identity=proof.IDENTITY,
                  source_main=child["source_main"], slots=slots, runs=runs, source_tree=tree,
                  software_tree_sha256=proof.sha(proof.canonical(tree)),
                  authority_sha256=tree[proof.PROTOCOL],
                  executed={n: tree[n] for n in proof.SOFTWARE},
                  child_verification=child, released_context=context, budget_sha256=proof.BUDGET)
    actual = packet(proof.gate_args(slots, released=True), proof.START + 11000,
                    proof.START + 12000, "")
    buffers = {"owner-budget.json": b"synthetic budget\n", proof.PACKAGE: child_raw,
               proof.ACTUAL: child_actual_raw, "input-activation-readiness-a1.json": ready_raw,
               "input-preflight-actual-a1.json": preflight_raw}
    monkeypatch.setattr(proof, "current_tree", lambda: tree)
    monkeypatch.setattr(sys.modules[_software_bytes.__module__], "_software_bytes",
                        lambda _: policy_raw)
    monkeypatch.setattr(proof, "pair", lambda _, name: buffers[name])
    monkeypatch.setattr(proof, "public_run",
                        lambda slot, **kwargs: deepcopy(runs[slots.index(slot)]))
    monkeypatch.setattr(proof, "verified_readiness",
                        lambda *_: pytest.fail("activation recursively replayed readiness"))

    def install():
        raw = proof.canonical(report)
        actual["responses"][0]["result"]["output"] = proof.canonical(dict(
            status=proof.RELEASED_STATUS, report_sha256=proof.sha(raw))).decode()
        buffers[proof.RELEASED_PACKAGE] = raw
        buffers[proof.RELEASED_ACTUAL] = proof.canonical(actual)

    install()
    return policy, tree, report, actual, buffers, install


def test_released_entry_replays_two_original_checks_without_recursive_readiness(proof, monkeypatch):
    policy, _tree, report, actual, _buffers, _install = released_fixture(proof, monkeypatch)
    result = proof.require_released(policy)
    assert result["source_main"] == report["source_main"]
    assert result["verified_returned_ms"] == actual["responses"][0]["returned_ms"]


@pytest.mark.parametrize("damage", ["exit", "actor", "late", "source", "tree", "context",
                                    "unperformed", "preflight", "missing"])
def test_missing_changed_or_expired_released_original_denied(proof, monkeypatch, damage):
    policy, _tree, report, actual, buffers, install = released_fixture(proof, monkeypatch)
    if damage == "exit":
        actual["responses"][0]["result"]["exit_code"] = 1
    elif damage == "actor":
        actual["author"] = "/root"
    elif damage == "late":
        actual["responses"][0]["returned_ms"] = proof.END + 1
    elif damage == "source":
        report["source_main"] = "e" * 40
    elif damage == "tree":
        report["source_tree"] = dict(report["source_tree"], **{proof.WORKER: "e" * 64})
    elif damage == "context":
        report["released_context"] = dict(report["released_context"],
                                           preflight_actual_sha256="e" * 64)
    elif damage == "unperformed":
        report["runs"] = []
    elif damage == "preflight":
        packet = proof.parse(buffers["input-preflight-actual-a1.json"])
        packet["responses"][0]["result"]["output"] = "{}\n"
        buffers["input-preflight-actual-a1.json"] = proof.canonical(packet)
    install()
    if damage == "missing":
        buffers.pop(proof.RELEASED_ACTUAL)
    with pytest.raises((ValueError, KeyError)):
        proof.require_released(policy)


def released_trace_context(proof):
    return dict(readiness_sha256="1" * 64, new_proof_package_sha256="2" * 64,
                new_proof_actual_sha256="3" * 64, source_main="b" * 40,
                software_tree_sha256="4" * 64, preflight_actual_sha256="5" * 64,
                preflight_returned_ms=proof.START + 500)


def test_released_native_checks_same_ready_proof_main_and_original_preflight(proof, monkeypatch):
    context = released_trace_context(proof)
    slot, claim, summary, files, _calls = public_fixture(
        proof, monkeypatch, released_context=context)
    result = proof.audit_public(slot, claim, summary, files, negative=False,
                                released_context=context)
    assert result["mode"] == "released" and result["trace"]["released_context"] == context


@pytest.mark.parametrize("damage", ["missing", "duplicate", "proof", "main", "preflight",
                                    "SUP_before_preflight"])
def test_released_trace_or_preflight_order_mutation_denied(proof, monkeypatch, damage):
    context = released_trace_context(proof)
    slot, claim, summary, files, _calls = public_fixture(
        proof, monkeypatch, released_context=context)
    rows = [proof.parse(line) for line in files["native/process-trace.jsonl"].splitlines()]
    released = rows[2]
    if damage == "missing":
        rows.remove(released)
    elif damage == "duplicate":
        rows.insert(3, deepcopy(released))
    elif damage == "proof":
        released["new_proof_actual_sha256"] = "e" * 64
    elif damage == "main":
        released["source_main"] = "e" * 40
    elif damage == "preflight":
        released["preflight_actual_sha256"] = "e" * 64
    else:
        context["preflight_returned_ms"] += 10000
    for i, row in enumerate(rows):
        row["seq"] = i + 1
        row["time_ns"] = rows[0]["time_ns"] + i
    files["native/process-trace.jsonl"] = b"".join(proof.canonical(row) for row in rows)
    with pytest.raises(ValueError):
        proof.audit_public(slot, claim, summary, files, negative=False,
                            released_context=context)


def test_released_verifier_exercises_independent_original_metadata_interface(proof, monkeypatch):
    import p17_m2_input_continuation as profiles

    policy, tree, _report, _actual, buffers, _install = released_fixture(proof, monkeypatch)
    calls = []

    def preflight(plan, raw):
        assert raw == buffers["input-preflight-actual-a1.json"]
        assert plan["source_tree"] == tree and plan["scope"] == "DECLARED_METADATA_ONLY_VIEW"
        assert plan["activation_readiness"] == dict(path=policy["readiness_path"],
            sha256=proof.sha(buffers["input-activation-readiness-a1.json"]))
        assert "root" not in plan and "formal_authority" not in plan
        calls.append((plan, raw))
        return proof.parse(proof.parse(raw)["responses"][0]["result"]["output"].encode())

    checker = SimpleNamespace(FORMAL_SCOPE="DECLARED_METADATA_ONLY_VIEW",
                               _registered_preflight=preflight)
    monkeypatch.setattr(profiles, "profile", lambda kind, identity: checker)
    result = proof.independent_preflight_replay(policy, tree)
    assert result["source_stat_reads"] == result["target_stat_reads"] == 0 and len(calls) == 1


def test_full_cli_registry_requires_actual_independent_checker_compile(proof, monkeypatch):
    tree = {name: proof.sha((SCRIPTS.parent / name).read_bytes()) for name in proof.SOFTWARE}
    observed = {str(proof.REPO / name): value for name, value in tree.items()}
    loader = SimpleNamespace(loaded_source_sha256=observed)
    monkeypatch.setitem(sys.modules, "full60_input_loader", loader)
    assert proof.compiled(tree, verification=True) == tree
    observed.pop(str(proof.REPO / "scripts/p17_m2_source_acquisition_independent.py"))
    with pytest.raises(ValueError, match="actual compiled.*acquisition_independent"):
        proof.compiled(tree, verification=True)
