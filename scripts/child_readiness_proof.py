"""Independent sealed-control replay for the child-free measured readiness path.

This module reads software and retained control bytes only. In particular, its
measured ``verified_readiness`` API never launches a process or opens a business
source, a custody target, or a lease. Publication checks belong to the CLI.
"""

import hashlib
import io
import json
import re
import resource
import sys
import tarfile
import time
from pathlib import Path

REPO = Path("/private/tmp/topolab-child-20261125")
DATA = Path("/Users/keith1117/Documents/TopoLab-data/child-20261125")
FORMAL = Path(str(DATA) + "-formal")
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.child-20261125.v1"
PUBLIC_ID = "topolab.v2.p17-m2-content-verified-input.v1"
PUBLIC_SCOPE = "PUBLIC_SOFTWARE_FIXTURE_ONLY"
PROTOCOL = "docs/planning/child_formal_contract.json"
WORKER, LAUNCHER = "scripts/child_readiness_proof.py", "scripts/child_verify.py"
PACKAGE, ACTUAL = "child-readiness.json", "child-readiness-actual.json"
RELEASED_PACKAGE = "child-released-checks.json"
RELEASED_ACTUAL = "child-released-checks-actual.json"
BUDGET = "8693ffd9e9555a5247c2569c0d4f97331fbc7f6237dce25e2a80012c7f1c26dd"
AUTHOR = "/root/full60_independent"
PYTHON = ("/Library/Frameworks/Python.framework/Versions/3.12/Resources/"
          "Python.app/Contents/MacOS/Python")
START, DIAGNOSTIC_END, END = 1795591669520, 1795656469520, 1795786069520
ROLE = "independent-public-check"
STATUS = "PASS_CHILD_FREE_READINESS_AND_ACTIVE_CHILD_VETO"
RELEASED_STATUS = "PASS_TWO_RELEASED_REGISTERED_READINESS_RETURNS"
OLD_REPO = Path("/private/tmp/topolab-certificate-20261124")
OLD_FORMAL = DATA.parent / "certificate-20261124-formal"
OLD_MAIN = "671a21b3d47fae16610e13884993abee5bee8e12"
OLD_REPORT = "133553193c411d565860c0a04ac81b65f8bad47152d1b89caa88e28ee3b75c81"
OLD_ACTUAL = "7b3af893a673787cce4992eb9ca92db91c08e4112e81a0d225265cf839edbeda"
OLD_RETURNED = 1795519025567
SOFTWARE = (WORKER, LAUNCHER, "scripts/certificate_replay_proof.py",
            "scripts/certificate_replay_archive.py", "scripts/full60_input_loader.py",
            "scripts/staged_input_filer.py", "scripts/r0_read_independent.py",
            "scripts/p17_m2_source_acquisition_independent.py",
            "scripts/p17_m2_content_verified_independent.py")
MODULE_SOURCE_SHA256 = None


def need(value, message):
    if not value:
        raise ValueError("CHILD_READINESS_STOP: " + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")


def parse(raw):
    need(type(raw) is bytes and 0 < len(raw) <= 16 * 1024**2, "bounded metadata required")

    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "duplicate metadata key")
            result[key] = value
        return result

    def invalid(_):
        raise ValueError("CHILD_READINESS_STOP: nonfinite metadata")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def wire():
    import staged_input_filer

    return staged_input_filer


def history():
    import certificate_replay_proof

    need(Path(certificate_replay_proof.__file__).resolve()
         == REPO / "scripts/certificate_replay_proof.py", "current shared proof module required")
    return certificate_replay_proof


def pair(folder, name, maximum=16 * 1024**2):
    a = folder / name
    b = folder.with_name(folder.name + "-backup") / name
    raw = wire().read_private(a, maximum)
    need(not a.samefile(b) and raw == wire().read_private(b, maximum), "paired bytes differ")
    return raw


def historical_inputs():
    from p17_m2_content_verified_independent import _software_bytes

    policy_raw = _software_bytes(OLD_REPO / "docs/planning/certificate_formal_contract.json")
    closure = parse(pair(OLD_FORMAL, "input-preparation-closure-a1.json"))
    tree = closure["source_tree"]
    need(sha(policy_raw) == tree["docs/planning/certificate_formal_contract.json"],
         "historical policy differs")
    return parse(policy_raw), tree


def prior_certificate():
    """Use the shared repaired checker against the unchanged historical proof."""
    policy, tree = historical_inputs()
    result = history().verified_readiness(policy, tree)
    need(result == dict(
        source_main=OLD_MAIN, verified_returned_ms=OLD_RETURNED,
        package=dict(path=str(OLD_FORMAL / "certificate-replay.json"), sha256=OLD_REPORT),
        actual=dict(path=str(OLD_FORMAL / "certificate-replay-actual.json"), sha256=OLD_ACTUAL)),
        "historical complete replay differs")
    return result


def check_slots(slots, *, released=False):
    need(type(slots) is list and len(slots) == len(set(slots)) == (2 if released else 3)
         and all(type(n) is int and 1 <= n <= 18 for n in slots),
         "two positives and one distinct negative slot required")


def gate_args(slots, *, released=False):
    check_slots(slots, released=released)
    return ["/usr/bin/timeout", "-k", "2", "290", PYTHON, "-I", str(REPO / LAUNCHER),
            "released" if released else "verify", *map(str, slots)]


def check_trace(raw, *, plan_sha, proof_sha, entry_sha, main, negative, released_context=None):
    rows = [parse(line) for line in raw.splitlines()]
    need(2 <= len(rows) <= 128 and rows[0].get("kind") == "trace-start"
         and rows[0].get("observer_processes") == 0, "trace start missing")
    first = rows[0]
    previous = 0
    for seq, row in enumerate(rows, 1):
        need(all(type(row.get(k)) is int and row[k] > 0
                 for k in ("pid", "ppid", "pgid", "seq", "time_ns"))
             and row["seq"] == seq and row["time_ns"] >= previous
             and all(row[k] == first[k] for k in ("pid", "ppid", "pgid")),
             "trace process/clock/order differs")
        previous = row["time_ns"]
    ready = [r for r in rows if r["kind"] == "readiness"]
    complete = [r for r in rows if r["kind"] == "trace-complete"]
    spawn = [r for r in rows if r["kind"] == "spawn"]
    returned = [r for r in rows if r["kind"] == "spawn-return"]
    released = [r for r in rows if r["kind"] == "released-readiness"]
    need(len(ready) == 1 and ready[0].get("scope")
         == "VERIFIED_PRIOR_RELEASE_AND_CANDIDATE_BYTES"
         and ready[0].get("sha256") == OLD_REPORT
         and ready[0].get("actual_sha256") == OLD_ACTUAL
         and ready[0].get("proof_sha256") == proof_sha
         and ready[0].get("checkout_head") == main, "trace readiness proof differs")
    if released_context is None:
        need(not released, "unexpected released readiness trace")
    else:
        need(not negative and len(released) == 1
             and all(released[0].get(key) == value for key, value in released_context.items()
                     if key != "preflight_returned_ms")
             and ready[0]["seq"] < released[0]["seq"] < rows[-1]["seq"],
             "released readiness context differs")
    if negative:
        need(len(spawn) == len(returned) == 1
             and spawn[0].get("executable") == "/bin/sleep"
             and spawn[0].get("argv") == ["/bin/sleep", "3"]
             and spawn[0].get("cwd") == str(REPO)
             and isinstance(spawn[0].get("stack"), list) and spawn[0]["stack"]
             and type(returned[0].get("child_pid")) is int
             and returned[0]["child_pid"] > 0
             and ready[0]["seq"] < spawn[0]["seq"] < returned[0]["seq"]
             and not complete, "active child negative trace differs")
    else:
        need(not spawn and not returned and len(complete) == 1
             and complete[0] == rows[-1]
             and complete[0].get("plan_sha256") == plan_sha
             and complete[0].get("entry_sha256") == entry_sha,
             "child-free completion trace differs")
    return dict(trace_sha256=sha(raw), spawn_count=len(spawn),
                spawned_pids=[r["child_pid"] for r in returned],
                trace_complete=bool(complete), payload_pid=first["pid"],
                payload_parent=first["ppid"], payload_group=first["pgid"],
                first_ns=first["time_ns"], last_ns=rows[-1]["time_ns"],
                released_context=released_context)


def archive_buffers(raw, inventory):
    index = parse(inventory)
    need(type(index) is dict and 1 <= len(index) <= 512, "bounded archive index required")
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = archive.getmembers()
        need(len(members) == len(index) and len({m.name for m in members}) == len(members)
             and {m.name for m in members} == set(index)
             and all(m.isfile() and not m.name.startswith("/")
                     and ".." not in Path(m.name).parts and m.size <= 16 * 1024**2
                     for m in members)
             and sum(m.size for m in members) <= 32 * 1024**2,
             "archive inventory differs")
        files = {m.name: archive.extractfile(m).read() for m in members}
    for name, raw_member in files.items():
        item = index[name]
        need(type(item.get("bytes")) is int
             and item == dict(bytes=len(raw_member), sha256=sha(raw_member)),
             "archive member differs: " + name)
    return files


def audit_public(slot, claim, summary, files, *, negative, released_context=None):
    """Reconcile original calls and the Native binder from sealed buffers only."""
    import p17_m2_content_verified_independent as independent

    def raw(name):
        return files[name]

    def obj(name):
        return parse(raw(name))

    root = f"/private/tmp/topolab-public-child-20261125-a{slot}"
    plan_raw = raw("native/plan.json")
    plan, plan_sha = parse(plan_raw), sha(plan_raw)
    mode = "released" if released_context is not None else "negative" if negative else "candidate"
    need(claim["slot"] == slot and type(claim["slot"]) is int
         and claim["root"] == root and claim["mode"] == mode
         and claim["budget_sha256"] == BUDGET and claim["charged_FULL"] == 600
         and type(claim["start_ms"]) is int and type(claim["end_ms"]) is int
         and START <= claim["start_ms"] < claim["end_ms"] <= DIAGNOSTIC_END
         and claim["end_ms"] - claim["start_ms"] <= 420000,
         "public entry authority differs")
    need(plan["root"] == root and plan["formal_authority"] is False
         and plan["execution_identity"] == PUBLIC_ID and plan["scope"] == PUBLIC_SCOPE
         and plan["runtime"]["cwd"] == str(REPO)
         and type(summary["slot"]) is int and summary["slot"] == slot
         and summary["root"] == root
         and summary["mode"] == mode and summary["plan_sha256"] == plan_sha
         and summary["source_tree"] == plan["source_tree"]
         and claim["driver_sha256"]
         == plan["source_tree"]["candidate/child_public_schedule.mjs"]
         and claim["scheduler_sha256"]
         == plan["source_tree"]["freeze/scripts/staged_input_actor.mjs"]
         and plan["source_tree"]["public-entry"]
         == sha(json.dumps(claim, sort_keys=True).encode()), "public plan scope differs")
    entry = str(REPO / "scripts/child_public_control.py")

    def argv(stage):
        return [PYTHON, "-I", entry, stage, "--root", root,
                "--plan-sha", plan_sha, "--role", ROLE]

    accepted = obj(f"native/{ROLE}-accepted.json")
    events = obj(f"native/{ROLE}-events.json")
    native = obj(f"native/receipts/{ROLE}-wire.json")
    need(accepted["raw_tool_events"] == events and len(events) == 2,
         "native original event pair differs")
    starts, ends, codes = {}, {}, {}
    for stage in ("prepare", "supervise", "file-supervise", "record", "file-record", "bind"):
        packet_raw = raw(f"caller/{stage}-actual.json")
        packet = parse(packet_raw)
        expected = ([PYTHON, "-I", entry, "prepare-public", "--root", root]
                    if stage == "prepare" else argv(stage))
        first, last, code = wire().validate_terminal(packet, expected, "/root", str(REPO))
        need("prefix_rule" not in packet["request"], "persistent permission prefix forbidden")
        need(all(type(row["arguments"].get("yield_time_ms", 5000)) is int
                 and 5000 <= row["arguments"].get("yield_time_ms", 5000) <= 30000
                 for row in packet["responses"][1:]), "bounded owned poll required")
        starts[stage], ends[stage], codes[stage] = first, last, code
        need(claim["start_ms"] <= first <= last <= claim["end_ms"],
             "public command outside original window")
        output = "".join(r["result"]["output"] for r in packet["responses"]).encode()
        if stage in ("supervise", "record"):
            event = events[0 if stage == "supervise" else 1]
            need(event == obj(f"native/{ROLE}-{stage}-actual-event.json")
                 and event["event_id"] == packet["event_id"]
                 and event["raw_packet_sha256"] == sha(packet_raw)
                 and first == round(event["start_seconds"] * 1000)
                 and last == round(event["end_seconds"] * 1000), "filed original differs")
            expected_output = (dict(status="PENDING_EXTERNAL_EXIT", controller_exit=0)
                               if stage == "supervise" else native)
            need(output == canonical(expected_output), "original role stdout differs")
        elif stage == "bind":
            need(output == (raw("native/STOP.json") if negative else canonical(accepted["result"])),
                 "original binder stdout differs")
        elif stage.startswith("file-"):
            need(output == canonical(dict(status="ACTUAL_EVENT_FILED",
                                          mode=stage.removeprefix("file-"))),
                 "filing original stdout differs")
        else:
            need(parse(output)["plan_sha256"] == plan_sha, "prepare return plan differs")
    order = ("prepare", "supervise", "file-supervise", "record", "file-record", "bind")
    need(all(ends[a] <= starts[b] for a, b in zip(order, order[1:], strict=False))
         and starts["supervise"] - starts["prepare"] <= 30000
         and ends["record"] - starts["supervise"] + 10000 <= 300000
         and codes == {s: (1 if negative and s == "bind" else 0) for s in order}
         and summary["call_exits"] == codes
         and all(type(code) is int for code in summary["call_exits"].values()),
         "original return order/code/FULL differs")
    if released_context is not None:
        need(released_context["preflight_returned_ms"] <= starts["supervise"]
             and claim["checkout_head"] == released_context["source_main"],
             "released supervisor preceded original independent preflight")
    folder = f"native/receipts/{ROLE}/{ROLE}/"
    record = obj(folder + "command.json")
    helpers = {h["profile"]: raw(folder + h["profile"]) for h in record["helpers"]}
    inner = dict(record=record, profile=raw(folder + "command.time"),
                 log=raw(folder + "command.log"), helper_profiles=helpers,
                 expected_role=ROLE, expected_argv=argv("payload"), platform="darwin")
    outer = {"outer-controller": raw(f"native/receipts/{ROLE}-controller.time")}
    result = independent.audit_role(
        native["pending"], native["completion"], raw_tool_events=events,
        expected_role=ROLE, expected_plan_sha256=plan_sha,
        inner_evidence=inner, native_profiles=outer)
    need(result == accepted["result"], "independent native reconciliation differs")
    stopped = None
    if negative:
        need(record["software_result"] == "RESOURCE_UNKNOWN_STOP_UNREGISTERED_DESCENDANT"
             and result["full_role_evidence_accepted"] is False
             and result["RSS_envelope_bytes"] is None
             and "native/STOP.json" in files, "active child was not rejected by Native")
        stopped = obj("native/STOP.json")
        closed = independent.check_closed_attempt(
            dict(native, inner_evidence=inner, native_profiles=outer), raw_tool_events=events,
            expected_role=ROLE, expected_plan_sha256=plan_sha, expected_argv=argv("payload"))
        expected_stop = dict(result, cleanup_acceptance=closed)
        need(canonical(stopped) == canonical(expected_stop),
             "original STOP cleanup/primary/secondary differs")
    else:
        need(result["full_role_evidence_accepted"] is True and result["evidence_complete"] is True
             and type(result["RSS_envelope_bytes"]) is int
             and 0 < result["RSS_envelope_bytes"] <= 4 * 1024**3
             and result["actual_exit_codes"] == [0, 0]
             and "native/STOP.json" not in files, "unaccepted native positive")
    source = plan["source_tree"]
    traced = check_trace(raw("native/process-trace.jsonl"), plan_sha=plan_sha,
                         proof_sha=source["candidate/certificate_replay_proof.py"],
                         entry_sha=source["candidate/child_public_control.py"],
                         main=claim["checkout_head"], negative=negative,
                         released_context=released_context)
    sampled = [process for sample in record["samples"] for process in sample["roles"]]
    need(traced["payload_parent"] == traced["payload_group"] == record["pid"]
         and any(p["pid"] == traced["payload_pid"]
                 and p["parent"] == record["pid"] and p["pgid"] == record["pid"]
                 for p in sampled)
         and starts["supervise"] * 10**6 <= traced["first_ns"]
         <= traced["last_ns"] <= ends["supervise"] * 10**6,
         "trace does not belong to the measured Native payload")
    if negative:
        need(all(any(p["pid"] == pid and p["parent"] == traced["payload_pid"]
                     and p["pgid"] == traced["payload_group"] for p in sampled)
                 for pid in traced["spawned_pids"]),
             "active child was not independently sampled")
    return dict(slot=slot, mode=mode, plan_sha256=plan_sha, source_tree=source,
                source_main=claim["checkout_head"],
                driver_sha256=source["candidate/child_public_schedule.mjs"],
                native_result=result, stopped_result=stopped, trace=traced,
                original_end_ms=ends["bind"], original_start_ms=starts["prepare"])


def public_run(slot, *, negative, released_context=None):
    claim = parse(pair(DATA, f"public-{slot}-entry.json"))
    summary_raw = pair(DATA, f"public-{slot}-result.json")
    summary = parse(summary_raw)
    inventory = pair(DATA, f"public-{slot}-index.json")
    archive = pair(DATA, f"public-{slot}-evidence.tar.gz", 32 * 1024**2)
    need(sha(archive) == summary["archive_sha256"]
         and sha(inventory) == summary["index_sha256"], "public archive raw SHA differs")
    result = audit_public(slot, claim, summary, archive_buffers(archive, inventory),
                          negative=negative, released_context=released_context)
    return dict(result, archive_sha256=sha(archive), index_sha256=sha(inventory),
                result_sha256=sha(summary_raw))


def same_candidate(runs):
    trees = [{k: v for k, v in run["source_tree"].items() if k != "public-entry"}
             for run in runs]
    need(len(runs) in (2, 3) and all(tree == trees[0] for tree in trees)
         and len({r["driver_sha256"] for r in runs}) == 1, "public candidate bytes differ")


def local_candidate(runs, tree, main):
    need(isinstance(main, str) and re.fullmatch("[0-9a-f]{40}", main)
         and history().checkout_commit(REPO) == main, "current released main differs")
    same_candidate(runs)
    for run in runs:
        need(isinstance(run["source_main"], str)
             and re.fullmatch("[0-9a-f]{40}", run["source_main"]),
             "public development checkout identity differs")
        frozen = {name.removeprefix("freeze/"): value
                  for name, value in run["source_tree"].items() if name.startswith("freeze/")}
        need(frozen == tree, "public/full formal software tree differs")
        for name, digest in run["source_tree"].items():
            if name == "public-entry":
                continue
            relative = "scripts/" + name.removeprefix("candidate/") if name.startswith(
                "candidate/") else name
            if relative.startswith("freeze/"):
                relative = relative.removeprefix("freeze/")
            need(tree.get(relative) == digest, "public/current software differs: " + relative)


def compiled(tree, *, verification):
    loader = sys.modules["full60_input_loader"]
    names = SOFTWARE if verification else (WORKER, "scripts/certificate_replay_proof.py")
    result = {}
    for name in names:
        actual = loader.loaded_source_sha256.get(str(REPO / name))
        if name == WORKER and actual is None:
            actual = MODULE_SOURCE_SHA256
        need(actual == tree[name] == sha((REPO / name).read_bytes()),
             "actual compiled source differs: " + name)
        result[name] = actual
    return result


def _returned_proof(policy, tree):
    """Check the frozen independent original, without recursively replaying roles."""
    import r0_read_independent as original

    need(policy["execution_identity"] == IDENTITY
         and policy["new_input_budget"] == dict(path=str(DATA / "owner-budget.json"), sha256=BUDGET)
         and sha(pair(DATA, "owner-budget.json")) == BUDGET
         and policy["child_verification_paths"] == dict(package=str(FORMAL / PACKAGE),
                                                       actual=str(FORMAL / ACTUAL)),
         "new finite child authority differs")
    raw, actual_raw = pair(FORMAL, PACKAGE), pair(FORMAL, ACTUAL)
    report = parse(raw)
    slots = report["slots"]
    first, last, output = original.terminal(parse(actual_raw), gate_args(slots), author=AUTHOR,
                                           cwd=str(REPO), window=(START, END), full=300)
    need(report["status"] == STATUS and report["execution_identity"] == IDENTITY
         and report["budget_sha256"] == BUDGET
         and report["authority_sha256"] == tree[PROTOCOL]
         and report["software_tree_sha256"] == sha(canonical(tree))
         and report["executed"] == {n: tree[n] for n in SOFTWARE}
         and report["worker_sha256"] == tree[WORKER]
         and output == canonical(dict(status=STATUS, report_sha256=sha(raw)))
         and first <= last <= time.time_ns() // 10**6, "independent child proof differs")
    return report, dict(source_main=report["source_main"], verified_returned_ms=last,
                        package=dict(path=str(FORMAL / PACKAGE), sha256=sha(raw)),
                        actual=dict(path=str(FORMAL / ACTUAL), sha256=sha(actual_raw)))


def verified_readiness(policy, tree):
    """Pure in-process admission, including original independent return and veto."""
    report, reference = _returned_proof(policy, tree)
    history()
    compiled(tree, verification=False)
    need(report["prior_certificate"] == prior_certificate(), "historical proof changed")
    runs = [public_run(slot, negative=(i == 2)) for i, slot in enumerate(report["slots"])]
    need(report["runs"] == runs, "sealed public replay differs")
    local_candidate(runs, tree, report["source_main"])
    return reference


def verify(slots):
    """Released, independently scheduled offline verification (never a role)."""
    import subprocess

    import p17_m2_input_continuation as profiles
    import r0_read_independent  # noqa: F401 - pin original-return checker

    check_slots(slots)
    need(sys.flags.isolated and Path.cwd() == REPO and sys.executable == PYTHON
         and START <= time.time_ns() // 10**6 < END, "wrong released verifier runtime/window")

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=REPO, timeout=15).decode().strip()

    main = git("rev-parse", "HEAD")
    need(main == git("rev-parse", "origin/main") and git("branch", "--show-current") == "main"
         and not git("status", "--porcelain", "-uall"), "clean protected main required")
    live = profiles.profile("control", profiles.CHILD_FORMAL)
    profiles.profile("independent", profiles.CHILD_FORMAL)
    tree = live.source_freeze(IDENTITY)
    prior = prior_certificate()
    runs = [public_run(slot, negative=(i == 2)) for i, slot in enumerate(slots)]
    local_candidate(runs, tree, main)
    executed = compiled(tree, verification=True)
    need(sys.platform == "darwin" and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
         <= 4 * 1024**3 and time.time_ns() // 10**6 <= END,
         "released verifier resource/deadline differs")
    report = dict(status=STATUS, execution_identity=IDENTITY, source_main=main, slots=slots,
                  prior_certificate=prior, runs=runs, executed=executed,
                  worker_sha256=tree[WORKER], authority_sha256=tree[PROTOCOL],
                  software_tree_sha256=sha(canonical(tree)), budget_sha256=BUDGET)
    raw = canonical(report)
    for folder in (FORMAL, FORMAL.with_name(FORMAL.name + "-backup")):
        wire().write_private(folder / PACKAGE, raw)
    return dict(status=STATUS, report_sha256=sha(raw))


def current_tree():
    import p17_m2_input_continuation as profiles

    return profiles.profile("control", profiles.CHILD_FORMAL).source_freeze(IDENTITY)


def released_context(policy, tree, child):
    """Bind the exact new readiness and its genuine independent preflight."""
    import r0_read_independent as original

    need(policy["readiness_path"] == str(FORMAL / "input-activation-readiness-a1.json")
         and policy["independent_preflight_actual_path"]
         == str(FORMAL / "input-preflight-actual-a1.json"), "released control paths differ")
    ready_raw = pair(FORMAL, "input-activation-readiness-a1.json")
    actual_raw = pair(FORMAL, "input-preflight-actual-a1.json")
    ready = parse(ready_raw)
    argv = [PYTHON, "-I", str(REPO / "scripts/child_formal_registered.py"),
            "preflight", "--readiness-sha", sha(ready_raw)]
    first, last, output = original.terminal(parse(actual_raw), argv, author=AUTHOR,
                                           cwd=str(REPO), window=(START, END), full=None)
    expected = dict(status="PASS_REGISTERED_INPUT_METADATA_PREFLIGHT",
                    execution_identity=IDENTITY, author=AUTHOR,
                    readiness_path=policy["readiness_path"], readiness_sha256=sha(ready_raw),
                    published_source_sha256=ready["published_source_sha256"],
                    runtime=ready["runtime"], actors=policy["actors"],
                    new_input_budget=policy["new_input_budget"], source_stat_reads=0,
                    target_stat_reads=0, own_future_return="NOT_CLAIMED", child_verification=child)
    need(ready["schema"] == "topolab.registered-input.activation-readiness.v1"
         and ready["execution_identity"] == IDENTITY
         and ready["new_input_budget"] == policy["new_input_budget"]
         and ready["actors"] == policy["actors"]
         and ready["child_verification"] == child
         and ready["published_source_sha256"] == {k: v for k, v in tree.items() if k != PROTOCOL}
         and ready["runtime"]["python"] == PYTHON and ready["runtime"]["cwd"] == str(REPO)
         and output == canonical(expected) and child["verified_returned_ms"] <= first
         and first <= last <= time.time_ns() // 10**6,
         "released readiness/preflight original differs")
    return dict(readiness_sha256=sha(ready_raw),
                new_proof_package_sha256=child["package"]["sha256"],
                new_proof_actual_sha256=child["actual"]["sha256"],
                source_main=child["source_main"], software_tree_sha256=sha(canonical(tree)),
                preflight_actual_sha256=sha(actual_raw), preflight_returned_ms=last)


def _released_paths(policy):
    need(policy["child_released_paths"] == dict(package=str(FORMAL / RELEASED_PACKAGE),
                                               actual=str(FORMAL / RELEASED_ACTUAL)),
         "independent released check paths differ")


def independent_preflight_replay(policy, tree):
    """Exercise the published independent preflight reader on retained metadata.

    This is a read-only validation view, not a formal plan or an activation.
    Its fields are exactly those consumed by the metadata preflight interface.
    """
    import p17_m2_input_continuation as profiles

    checker = profiles.profile("independent", profiles.CHILD_FORMAL)
    ready_raw = pair(FORMAL, "input-activation-readiness-a1.json")
    actual_raw = pair(FORMAL, "input-preflight-actual-a1.json")
    ready = parse(ready_raw)
    plan = dict(scope=checker.FORMAL_SCOPE, source_tree=tree,
                binding=dict(preparation_protocol_sha256=tree[PROTOCOL]),
                preparation_contract_sha256=tree[PROTOCOL], runtime=ready["runtime"],
                activation_readiness=dict(path=policy["readiness_path"], sha256=sha(ready_raw)),
                independent_preflight=dict(path=policy["independent_preflight_actual_path"],
                                           sha256=sha(actual_raw)))
    result = checker._registered_preflight(plan, actual_raw)
    output = "".join(row["result"]["output"] for row in parse(actual_raw)["responses"]).encode()
    need(canonical(result) == output, "full independent metadata preflight replay differs")
    return result


def require_released(policy):
    """Mandatory activation veto; only sealed metadata/software, no recursion.

    This intentionally does not call registered.readiness_inputs or
    verified_readiness. The latter is what the two measured public calls test.
    """
    import r0_read_independent as original
    from p17_m2_content_verified_independent import _software_bytes

    _released_paths(policy)
    tree = current_tree()
    policy_raw = _software_bytes(REPO / PROTOCOL)
    need(sha(policy_raw) == tree[PROTOCOL] and canonical(parse(policy_raw)) == canonical(policy)
         and START <= time.time_ns() // 10**6 <= END, "released activation policy/deadline differs")
    raw, actual_raw = pair(FORMAL, RELEASED_PACKAGE), pair(FORMAL, RELEASED_ACTUAL)
    report = parse(raw)
    first, last, stdout = original.terminal(
        parse(actual_raw), gate_args(report["slots"], released=True), author=AUTHOR,
        cwd=str(REPO), window=(START, END), full=300)
    _proof, child = _returned_proof(policy, tree)
    context = released_context(policy, tree, child)
    need(report["status"] == RELEASED_STATUS and report["execution_identity"] == IDENTITY
         and report["budget_sha256"] == BUDGET
         and report["source_tree"] == tree
         and report["software_tree_sha256"] == sha(canonical(tree))
         and report["authority_sha256"] == tree[PROTOCOL]
         and report["executed"] == {n: tree[n] for n in SOFTWARE}
         and report["child_verification"] == child and report["released_context"] == context
         and report["source_main"] == child["source_main"] == history().checkout_commit(REPO)
         and stdout == canonical(dict(status=RELEASED_STATUS, report_sha256=sha(raw)))
         and first <= last <= time.time_ns() // 10**6, "independent released original differs")
    runs = [public_run(slot, negative=False, released_context=context) for slot in report["slots"]]
    need(report["runs"] == runs and max(r["original_end_ms"] for r in runs) <= first,
         "released calls differ or follow their independent verification")
    local_candidate(runs, tree, report["source_main"])
    compiled(tree, verification=False)
    return dict(source_main=report["source_main"], verified_returned_ms=last,
                package=dict(path=str(FORMAL / RELEASED_PACKAGE), sha256=sha(raw)),
                actual=dict(path=str(FORMAL / RELEASED_ACTUAL), sha256=sha(actual_raw)))


def verify_released(slots):
    """One separately booked independent return for two full readiness payloads."""
    import subprocess

    check_slots(slots, released=True)
    need(sys.flags.isolated and Path.cwd() == REPO and sys.executable == PYTHON
         and START <= time.time_ns() // 10**6 <= END, "wrong released-check runtime/window")

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=REPO, timeout=15).decode().strip()

    main = git("rev-parse", "HEAD")
    need(main == git("rev-parse", "origin/main") and git("branch", "--show-current") == "main"
         and not git("status", "--porcelain", "-uall"),
         "clean protected released checkout required")
    from p17_m2_content_verified_independent import _software_bytes

    tree = current_tree()
    policy_raw = _software_bytes(REPO / PROTOCOL)
    policy = parse(policy_raw)
    _released_paths(policy)
    need(sha(policy_raw) == tree[PROTOCOL], "released-check protocol source differs")
    child = verified_readiness(policy, tree)
    independent_preflight_replay(policy, tree)
    context = released_context(policy, tree, child)
    need(context["source_main"] == main, "released readiness proof source differs")
    runs = [public_run(slot, negative=False, released_context=context) for slot in slots]
    local_candidate(runs, tree, main)
    need(max(r["original_end_ms"] for r in runs) <= time.time_ns() // 10**6
         and sys.platform == "darwin" and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
         <= 4 * 1024**3 and time.time_ns() // 10**6 <= END,
         "released-check clock/resource differs")
    report = dict(status=RELEASED_STATUS, execution_identity=IDENTITY, slots=slots,
                  source_main=main, source_tree=tree, software_tree_sha256=sha(canonical(tree)),
                  authority_sha256=tree[PROTOCOL], budget_sha256=BUDGET,
                  executed=compiled(tree, verification=True), child_verification=child,
                  released_context=context, runs=runs)
    raw = canonical(report)
    for folder in (FORMAL, FORMAL.with_name(FORMAL.name + "-backup")):
        wire().write_private(folder / RELEASED_PACKAGE, raw)
    return dict(status=RELEASED_STATUS, report_sha256=sha(raw))
