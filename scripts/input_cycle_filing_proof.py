"""A3 admission replays sealed A2 refusal and the new filing boundary.

This module opens software and private retained metadata only. It never resumes
an old actor, retries its rejected filing, or opens a business source/target.
"""

import argparse
import hashlib
import io
import json
import os
import re
import resource
import shlex
import stat
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from types import ModuleType

SOURCE_CHECKOUT = Path(__file__).resolve().parents[1]
REPO = Path("/private/tmp/topolab-input-cycle-20261123-a3")
OLD_REPO = REPO.with_name("topolab-input-cycle-20261123-a2")
DATA = Path("/Users/keith1117/Documents/TopoLab-data")
CAMPAIGN = DATA / "input-cycle-20261123"
E = DATA / "input-cycle-20261123-a3"
PREVIOUS_E = DATA / "input-cycle-20261123-a2"
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.cycle-20261123-a3.v1"
PREVIOUS_IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.cycle-20261123-a2.v1"
PREVIOUS_MAIN = "fe6d7ff2b716b4a02b42709171faf48e9f849125"
PREVIOUS_TREE_SHA = "f27d191184f833766120ff52182ea4c974f1085d061919150cb5e2a8ec4d8808"
AUTHOR = "/root/full60_independent"
PROTOCOL = "docs/planning/input_cycle_a3_contract.json"
WORKER = "scripts/input_cycle_filing_proof.py"
BASE = "scripts/input_cycle_proof.py"
BASE_SHA = "b6b46f8a7466fdc75b96aa29aee48fd4a7bf3c2f3f86416eca393e03391fd8dc"
OLD_PROOF = "scripts/input_cycle_r1_proof.py"
OLD_PROOF_SHA = "238831eec4da218ea632ca3c433d705a3e8ace2d032eb3f7722fb6e70afbff63"
CHECKER = "scripts/p17_m2_input_export_independent.py"
ACTOR = "scripts/staged_input_actor.mjs"
INTENT = "scripts/cycle_filing_intent.py"
REPAIR_SOURCES = tuple(sorted((
    INTENT, ACTOR, "scripts/staged_input_filer.py", "scripts/cycle_filing_input_filer.py",
    "scripts/build_staged_input_caller.py", "scripts/p17_m2_input_continuation.py",
)))
ACTOR_SHA = "03414b3265ca7275cb9bdc8eec596b4084e5bde6686b1d24183220555f891e21"
CAMPAIGN_SHA = "9ab62a69584a1ec2179b7fb9bd13a7b23a5564bcd8413a34f5ecb5f99d3c848b"
ATTEMPT_SHA = "6b55fd1a56a19965a63e9073b24e984d335a25b74599b2a250586cd9fc28de80"
ARCHIVE_SHA = "3444372988d81a55ea02bef9b2f2d24abf30ca665c46c938876cec5c8b1fbf4c"
INDEX_SHA = "6b86dada1871b828c97c8532acbf050ffc9b915a59dae8ce76a8ec13b4f15bf0"
CLOSED_SHA = "c11d19b05507931a562af2840e5328587ece2a17b25971c38091a3059d2be4f5"
AUDIT_SHA = "923231ef2d5c4a138668c7f8bb4db40aea5dbb095c2dcafd3792710ac57f9232"
ROOT_SHA = "8f1e2f80ceeb7c0e0e82f7121df57585320d326373ecd134b96dad6ccd7e6ebb"
INDEPENDENT_SHA = "fee078ebd763afaf000b58f0149f257ed005c6d0a8819296e4c37b91881bfea6"
PROGRAM_SHA = "e7fcc4e6ca69c6ea7fa6a6db23fbd5907684db302825287f4954f3a21adc1ca3"
ARTIFACT_SHA = "fd7a3c617a251ef07c1094b0668edb70fb7d26c3835c348a4c7c6fc6cbe70b55"
PACKAGE, ACTUAL = "filing-verification-a3.json", "filing-verification-actual-a3.json"
SUCCESS = "PASS_A2_REFUSAL_REPLAY_AND_A3_FILING_BOUNDARY"
START, END = 1795403546212, 1795576346212
PYTHON = (
    "/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python"
)
MODULE_SOURCE_SHA256 = None
_BASE_MODULE = None


def need(ok, reason):
    if not ok:
        raise ValueError("A3_FILING_PROOF_STOP: " + reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _base():
    global _BASE_MODULE
    if _BASE_MODULE is None:
        path = SOURCE_CHECKOUT / BASE
        raw = path.read_bytes()
        need(sha(raw) == BASE_SHA, "historical bridge source differs")
        module = ModuleType("a3_filing_base")
        module.__file__ = str(path)
        exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
        module.MODULE_SOURCE_SHA256 = sha(raw)
        loader = sys.modules.get("full60_input_loader")
        if loader is not None:
            previous = loader.loaded_source_sha256.get(str(path))
            need(previous is None or previous == sha(raw), "executed bridge buffer changed")
            loader.loaded_source_sha256[str(path)] = sha(raw)
        _BASE_MODULE = module
    return _BASE_MODULE


def _self_sha():
    observed = getattr(sys.modules.get("full60_input_loader"), "loaded_source_sha256", {}).get(
        str(SOURCE_CHECKOUT / WORKER)
    )
    value = MODULE_SOURCE_SHA256 if MODULE_SOURCE_SHA256 is not None else observed
    need(type(value) is str and len(value) == 64 and (observed is None or observed == value),
         "actual compiled A3 proof source missing")
    return value


def _policy(policy):
    need(
        policy.get("execution_identity") == IDENTITY
        and policy.get("campaign_budget")
        == dict(path=str(CAMPAIGN / "campaign-budget.json"), sha256=CAMPAIGN_SHA)
        and policy.get("new_input_budget")
        == dict(path=str(CAMPAIGN / "attempt-3-budget.json"), sha256=ATTEMPT_SHA)
        and policy.get("filing_verification_paths")
        == dict(package=str(E / PACKAGE), actual=str(E / ACTUAL))
        and policy.get("predecessor_terminal")
        == dict(path=str(PREVIOUS_E / "attempt-two-closed.json"), sha256=CLOSED_SHA)
        and policy.get("predecessor_independent_audit")
        == dict(path=str(PREVIOUS_E / "independent-a2-terminal-audit.json"), sha256=AUDIT_SHA),
        "fixed A3 identity/budget/predecessor differs",
    )
    need(policy.get("filing_repair_sources") == list(REPAIR_SOURCES),
         "exact A3 repair source inventory differs")
    _base().pair(CAMPAIGN, "campaign-budget.json", CAMPAIGN_SHA)
    _base().pair(CAMPAIGN, "attempt-3-budget.json", ATTEMPT_SHA)


def verify_stop_buffers(closed, audit, root, independent, plan, actor_raw, members):
    """Check stop semantics on supplied buffers; this function performs no IO."""
    plan_pin = sha(_base().canonical(plan))
    role = "independent-public-check"
    need(
        closed.get("status") == "CLOSED_AUTO_REVIEW_DECLINED_RECORD_FILING"
        and closed.get("formal_roles_accepted") == 0
        and type(closed["formal_roles_accepted"]) is int
        and closed.get("formal_booked") == 600
        and closed.get("formal_closed_unused") == 3360
        and closed.get("cumulative_known_FULL") == 352899
        and closed.get("metadata") == closed.get("payload") == [0, 0]
        and closed.get("plan_sha256") == plan_pin
        and closed.get("source_main") == PREVIOUS_MAIN
        and closed.get("new_lease") == "HELD"
        and audit.get("status") == "VERIFIED_A2_STOP_APPROVAL_REJECTION_ORIGINAL_ACTOR"
        and audit.get("plan_sha256") == plan_pin
        and audit.get("source_main") == PREVIOUS_MAIN
        and root.get("status") == independent.get("status") == "STOP_RETAINED_NO_RETRY"
        and root.get("secondary") == independent.get("secondary") == []
        and root.get("observed") == independent.get("observed") == []
        and "predecessor STOP" in root.get("reason", "")
        and plan.get("execution_identity") == PREVIOUS_IDENTITY
        and sha(actor_raw) == ACTOR_SHA,
        "A2 sealed stop/ledger/actor semantics differ",
    )
    rows = independent["raw"]
    need(len(rows) == 15 and len(root["raw"]) == 17, "original A2 row inventory differs")
    rejected = rows[12]
    need(
        rejected.get("tool") == "exec_command" and "result" not in rejected
        and "Rejected" in rejected.get("error", "")
        and "SUP/REC" in rejected["error"]
        and rejected["error"] in independent["reason"],
        "original approval refusal differs",
    )
    native = independent["active"]
    need(native["role"] == role, "refused role differs")
    for mode in ("supervise", "record"):
        actual = native[mode]
        need(actual["ended"] is True and actual["on_time"] is True
             and type(actual["exit_code"]) is int and actual["exit_code"] == 0
             and actual["error"] is None, "original SUP/REC terminal differs")
    saved = independent["packets"][role + "-record"]
    need(sha(_base().canonical(saved["packet"])) == saved["sha256"],
         "original REC packet SHA differs")
    words = shlex.split(rejected["arguments"]["cmd"])
    filer = str(OLD_REPO / "scripts/cycle_r1_input_filer.py")
    need(filer in words and words[words.index(filer) + 1:] == [
        "file", "--root", plan["root"], "--plan-sha", plan_pin, "--role", role,
        "--event-mode", "record", "--packet", saved["path"], "--packet-sha", saved["sha256"],
    ], "refused command is not the original actor REC filing")
    need(sum(row.get("tool") == "exec_command"
             and row["arguments"]["cmd"] == rejected["arguments"]["cmd"]
             for row in rows) == 1, "repeated rejected dispatch")
    replay = audit["synthetic_original_actor_replay"]
    need(replay["rows_consumed"] == 15 and replay["actual_tool_dispatches"] == 0
         and all(replay["checks"].get(k) is True
                 for k in ("reason", "secondary", "observed", "raw", "active"))
         and replay["program_sha256"] == PROGRAM_SHA,
         "independent original-stream replay differs")
    need(role + "-supervise-actual-event.json" in members
         and role + "-record-actual-event.json" not in members
         and role + "-events.json" not in members
         and not any(name.startswith(("exporter-r0", "independent-r0", "exporter-r1",
                                      "independent-r1", "shared-closeout", "final-filing",
                                      "lease-release")) for name in members),
         "A2 accepted successor or REC event exists")
    return dict(status="A2_ORIGINAL_ACTOR_REC_FILE_REJECTED", source_main=PREVIOUS_MAIN,
                plan_sha256=plan_pin, accepted_roles=0, formal_FULL=600,
                original_SUP_REC_exits=[0, 0], rejected_original_row=12,
                source_line=150, original_error=rejected["error"], lease="HELD",
                absolute_host_no_unrecorded_dispatch="NOT_PROVEN", new_source_reads=0)


def _historical_recovery(plan):
    """Execute the original A2 checker bytes with their original namespace/tree."""
    base = _base()
    need(sha(base.canonical(plan["source_tree"])) == PREVIOUS_TREE_SHA
         and len(plan["source_tree"]) == 92, "A2 frozen source tree differs")
    for relative, pin in plan["source_tree"].items():
        need(not Path(relative).is_absolute() and ".." not in Path(relative).parts
             and sha(base._read(OLD_REPO / relative)) == pin,
             "A2 historical software buffer differs")
    path = OLD_REPO / OLD_PROOF
    raw = base._read(path)
    need(sha(raw) == OLD_PROOF_SHA == plan["source_tree"][OLD_PROOF],
         "A2 historical proof source differs")
    previous = ModuleType("a3_filing_historical_a2")
    previous.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True), previous.__dict__)
    previous.MODULE_SOURCE_SHA256 = sha(raw)
    policy = base.parse(base._read(OLD_REPO / previous.PROTOCOL))
    result = previous.verified_readiness(policy, plan["source_tree"])
    need(result["source_main"] == PREVIOUS_MAIN and result["accepted_real_slots"] == [1, 2],
         "A2 admitted two-file-read proof differs")
    return result


def _predecessor():
    base = _base()
    names = {
        "attempt-two-closed.json": CLOSED_SHA,
        "independent-a2-terminal-audit.json": AUDIT_SHA,
        "root-formal-actor-original-result-a1.json": ROOT_SHA,
        "independent-cycle-formal-actor-original-result-a2.json": INDEPENDENT_SHA,
        "formal-generated-controls-index-a1.json": INDEX_SHA,
        "cycle-20261123-independent-a2-program.json": ARTIFACT_SHA,
    }
    raw = {name: base.pair(PREVIOUS_E, name, pin) for name, pin in names.items()}
    objects = {name: base.parse(value) for name, value in raw.items()}
    archive = base.pair(PREVIOUS_E, "formal-generated-controls-a1.tar.gz", ARCHIVE_SHA)
    index = objects["formal-generated-controls-index-a1.json"]
    members = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as stream:
        for member in stream:
            need(member.isfile() and member.name in index["members"]
                 and member.name not in members, "A2 sealed member kind/name differs")
            size, pin = index["members"][member.name]
            need(type(size) is int and 0 < size == member.size <= base.CAP,
                 "A2 sealed member size differs")
            value = stream.extractfile(member).read(size + 1)
            need(len(value) == size and sha(value) == pin, "A2 sealed member bytes differ")
            members[member.name] = value
    need(set(members) == set(index["members"]) and len(members) == index["files"] == 23
         and sum(map(len, members.values())) == index["bytes"] == 176273
         and index["archive_sha256"] == sha(archive), "A2 sealed inventory differs")
    plan = base.parse(members["plan.json"])
    artifact = objects["cycle-20261123-independent-a2-program.json"]
    actor_raw = base._read(OLD_REPO / ACTOR)
    need(sha(artifact["program"].encode()) == artifact["program_sha256"] == PROGRAM_SHA
         and artifact["actor_sha256"] == ACTOR_SHA == plan["source_tree"][ACTOR],
         "A2 exact original program differs")
    # The first string literal in the emitted wrapper is the complete frozen actor.
    literal, _ = json.JSONDecoder().raw_decode(artifact["program"].split("new Function(", 1)[1])
    transformed = re.sub(rb"^export (?=(?:async )?function|const)", b"", actor_raw,
                         flags=re.MULTILINE)
    need(literal.removesuffix("\nreturn {executeActor,qualify};").encode()
         == transformed, "A2 emitted actor source differs")
    result = verify_stop_buffers(
        objects["attempt-two-closed.json"], objects["independent-a2-terminal-audit.json"],
        objects["root-formal-actor-original-result-a1.json"],
        objects["independent-cycle-formal-actor-original-result-a2.json"]["result"],
        plan, actor_raw, members,
    )
    result["prior_recovery"] = _historical_recovery(plan)
    result["terminal_sha256"], result["independent_audit_sha256"] = CLOSED_SHA, AUDIT_SHA
    result["closed_ms"] = objects["attempt-two-closed.json"]["closed_ms"]
    return result


def _repair(policy, tree):
    """The current published filing implementation supplies a pure intent checker."""
    base = _base()
    need(policy.get("filing_repair_sources") == list(REPAIR_SOURCES),
         "fixed A3 repair inventory differs")
    raw = {path: base._read(SOURCE_CHECKOUT / path) for path in REPAIR_SOURCES}
    pins = {path: sha(value) for path, value in raw.items()}
    need(pins == {path: tree[path] for path in REPAIR_SOURCES},
         "A3 repair source buffer differs from current frozen tree")
    module = ModuleType("a3_filing_intent_probe")
    module.__file__ = str(SOURCE_CHECKOUT / INTENT)
    exec(compile(raw[INTENT], module.__file__, "exec", dont_inherit=True), module.__dict__)
    loader = sys.modules.get("full60_input_loader")
    if loader is not None:
        previous = loader.loaded_source_sha256.get(module.__file__)
        need(previous is None or previous == pins[INTENT], "executed intent buffer changed")
        loader.loaded_source_sha256[module.__file__] = pins[INTENT]
    expected = dict(
        schema="topolab.formal-file-intent.v1", execution_identity=IDENTITY,
        root=str(DATA.parents[1] / "Library/Application Support/TopoLab-custody"
                 / "p17-m2-input-cycle-20261123-a3"),
        plan_sha256="1" * 64, role="independent-public-check", mode="record", author=AUTHOR,
        program_sha256="2" * 64, actor_sha256=pins[ACTOR],
        entry_sha256=pins["scripts/cycle_filing_input_filer.py"],
        packet_path=str(E / "declared-synthetic-record-actual.json"), packet_sha256="3" * 64,
        event_id="declared-synthetic-record-event",
        outputs=["independent-public-check-record-actual-event.json",
                 "independent-public-check-events.json"], first_ms=START + 1, last_ms=START + 2,
    )
    # A synthetic object never becomes an on-disk intent or a real event.
    accepted = module.validate_file_intent(dict(expected), dict(expected),
                                         consumed=False, stopped=False)
    need(accepted == expected, "production intent checker rejected the synthetic normal shape")
    rejected = []
    for field in ("execution_identity", "root", "plan_sha256", "role", "mode", "author",
                  "program_sha256", "actor_sha256", "entry_sha256", "packet_path",
                  "packet_sha256", "event_id", "outputs", "first_ms", "last_ms"):
        damaged = dict(expected)
        damaged[field] = [] if field == "outputs" else None
        try:
            module.validate_file_intent(damaged, dict(expected), consumed=False, stopped=False)
        except (ValueError, TypeError, KeyError):
            rejected.append(field)
        else:
            need(False, "production intent checker admitted mixed " + field)
    for field in ("consumed", "stopped"):
        flags = dict(consumed=False, stopped=False)
        flags[field] = True
        try:
            module.validate_file_intent(dict(expected), dict(expected), **flags)
        except (ValueError, TypeError, KeyError):
            rejected.append(field)
        else:
            need(False, "production intent checker admitted " + field)
    return dict(source_sha256=pins, pure_production_validator=True,
                synthetic_positive=True, rejected_synthetic_cases=rejected,
                actual_intents_written=0, actual_events_filed=0,
                actual_tool_dispatches=0, approval_outcome="NOT_GUARANTEED")


def verify_args():
    return ["/usr/bin/timeout", "-k", "2", "290", PYTHON, "-I", str(REPO / WORKER), "verify"]


def verify_return(pin):
    return dict(schema="topolab.filing-verification-return.v1", slot=3, status=SUCCESS,
                report_sha256=pin, own_future_return="NOT_CLAIMED")


def _claim(raw, publication):
    value = _base().parse(raw)
    need(value == dict(schema="topolab.input-cycle-offline-claim.v1", slot=3, actor=AUTHOR,
                       argv=verify_args(), repo=str(REPO), source_main=publication["source_main"],
                       worker_sha256=publication["worker_sha256"], budget_sha256=CAMPAIGN_SHA,
                       attempt_budget_sha256=ATTEMPT_SHA, charge_FULL=300,
                       claimed_ms=value.get("claimed_ms"))
         and type(value["slot"]) is type(value["claimed_ms"]) is int
         and START <= value["claimed_ms"] <= END, "A3 original claim differs")
    return value


def _save(root, name, value):
    base = _base()
    raw = base.canonical(value)
    need((root, name) in ((CAMPAIGN, "offline-03-entered.json"), (E, PACKAGE))
         and len(raw) <= base.CAP, "fixed A3 output/cap required")
    for folder in (root, root.with_name(root.name + "-backup")):
        parent = base._directory(folder)
        try:
            owner = os.fstat(parent)
            need(owner.st_uid == os.getuid() and stat.S_IMODE(owner.st_mode) == 0o700,
                 "private A3 directory required")
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=parent)
            try:
                count = 0
                while count < len(raw):
                    n = os.write(fd, raw[count:])
                    need(n > 0, "partial A3 write")
                    count += n
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(parent)
        finally:
            os.close(parent)
    need(base.pair(root, name) == raw, "A3 pair differs")
    return sha(raw)


def current_publication():
    base = _base()
    need(SOURCE_CHECKOUT == REPO and Path.cwd() == REPO and sys.executable == PYTHON
         and sys.flags.isolated == 1, "exact A3 isolated runtime required")

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=REPO, timeout=20)

    head = git("rev-parse", "HEAD").decode().strip()
    need(base._wire().digest_word(head, 40) and head != PREVIOUS_MAIN
         and git("branch", "--show-current").strip() == b"main"
         and git("rev-parse", "origin/main").decode().strip() == head
         and not git("status", "--porcelain=v1", "-uall").strip(),
         "clean protected A3 source required")
    result = dict(source_main=head, repo=str(REPO))
    for key, relative in (("worker_sha256", WORKER), ("authority_sha256", PROTOCOL),
                          ("checker_sha256", CHECKER)):
        raw = base._read(REPO / relative)
        need(raw == git("show", head + ":" + relative), "A3 published buffer differs")
        result[key] = sha(raw)
    result["repair_source_sha256"] = {}
    for path in REPAIR_SOURCES:
        raw = base._read(REPO / path)
        need(raw == git("show", head + ":" + path), "A3 published repair buffer differs")
        result["repair_source_sha256"][path] = sha(raw)
    need(result["worker_sha256"] == _self_sha()
         and result["checker_sha256"] == base.SOURCE_PINS[CHECKER],
         "A3 actually executed/checker source differs")
    return result


def verify_cli():
    base = _base()
    publication = current_publication()
    policy = base.parse(base._read(REPO / PROTOCOL))
    _policy(policy)
    claim_raw = base.pair(CAMPAIGN, "offline-03-claim.json")
    claim = _claim(claim_raw, publication)
    start = time.time_ns() // 1_000_000
    need(claim["claimed_ms"] <= start < END, "A3 offline clock exhausted")
    entered_pin = _save(CAMPAIGN, "offline-03-entered.json", dict(
        slot=3, execution_identity=IDENTITY, started_ms=start, claim_sha256=sha(claim_raw)))
    predecessor = _predecessor()
    tree = publication["repair_source_sha256"]
    repair = _repair(policy, tree)
    end = time.time_ns() // 1_000_000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    need(sys.platform == "darwin" and type(rss) is int and 0 < rss <= 4 * 1024**3
         and predecessor["closed_ms"] <= start <= end <= END and end - start <= 290000,
         "A3 offline time/RSS differs")
    report = dict(schema="topolab.filing-verification-report.v1", status=SUCCESS, slot=3,
                  execution_identity=IDENTITY, campaign_budget_sha256=CAMPAIGN_SHA,
                  attempt_budget_sha256=ATTEMPT_SHA, claim_sha256=sha(claim_raw),
                  entered_sha256=entered_pin, started_ms=start, ended_ms=end,
                  self_rss_bytes=rss, predecessor=predecessor, repair=repair, **publication)
    return verify_return(_save(E, PACKAGE, report))


def verified_readiness(policy, tree):
    base = _base()
    _policy(policy)
    raw, actual_raw = base.pair(E, PACKAGE), base.pair(E, ACTUAL)
    report, actual = base.parse(raw), base.parse(actual_raw)
    claim_raw = base.pair(CAMPAIGN, "offline-03-claim.json")
    claim = _claim(claim_raw, report)
    entered_raw = base.pair(CAMPAIGN, "offline-03-entered.json")
    entered = base.parse(entered_raw)
    wire = base._wire()
    first, last, output = wire.terminal(actual, verify_args(), author=AUTHOR, cwd=str(REPO),
                                         window=(START, END), full=300)
    predecessor, repair = _predecessor(), _repair(policy, tree)
    need(report["schema"] == "topolab.filing-verification-report.v1"
         and report["status"] == SUCCESS and report["execution_identity"] == IDENTITY
         and type(report["slot"]) is int and report["slot"] == 3
         and report["campaign_budget_sha256"] == CAMPAIGN_SHA
         and report["attempt_budget_sha256"] == ATTEMPT_SHA and report["repo"] == str(REPO)
         and wire.digest_word(report["source_main"], 40)
         and report["source_main"] != PREVIOUS_MAIN
         and report["worker_sha256"] == tree[WORKER] == _self_sha()
         and report["authority_sha256"] == tree[PROTOCOL]
         and base.canonical(report["repair_source_sha256"])
         == base.canonical({path: tree[path] for path in REPAIR_SOURCES})
         and report["checker_sha256"] == tree[CHECKER] == base.SOURCE_PINS[CHECKER]
         and tree[BASE] == BASE_SHA and wire.compiled_sha256 == tree[base.WIRE]
         and report["claim_sha256"] == sha(claim_raw)
         and report["entered_sha256"] == sha(entered_raw)
         and type(entered.get("slot")) is int
         and entered == dict(slot=3, execution_identity=IDENTITY,
                             started_ms=report["started_ms"], claim_sha256=sha(claim_raw))
         and wire.integer(report["started_ms"]) and wire.integer(report["ended_ms"])
         and predecessor["closed_ms"] <= claim["claimed_ms"] <= first
         <= report["started_ms"] <= report["ended_ms"] <= last
         and predecessor["prior_recovery"]["verified_returned_ms"] <= first
         and wire.integer(report["self_rss_bytes"], 1) and report["self_rss_bytes"] <= 4 * 1024**3
         and base.canonical(report["predecessor"]) == base.canonical(predecessor)
         and base.canonical(report["repair"]) == base.canonical(repair)
         and output == base.canonical(verify_return(sha(raw))),
         "A3 original filing verification return differs")
    return dict(package=dict(path=str(E / PACKAGE), sha256=sha(raw)),
                actual=dict(path=str(E / ACTUAL), sha256=sha(actual_raw)),
                source_main=report["source_main"], previous_source_main=PREVIOUS_MAIN,
                authority_sha256=report["authority_sha256"], worker_sha256=report["worker_sha256"],
                checker_sha256=report["checker_sha256"],
                repair_source_sha256=repair["source_sha256"],
                predecessor_terminal_sha256=CLOSED_SHA,
                predecessor_independent_audit_sha256=AUDIT_SHA,
                accepted_real_slots=[1, 2], slot=3, verified_returned_ms=last,
                approval_result="NOT_GUARANTEED")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("verify",))
    parser.parse_args()
    return verify_cli()


if __name__ == "__main__":
    # Bind the exact buffer compiled for this worker, not a later self-reread.
    path = Path(__file__)
    raw = path.read_bytes()
    module = ModuleType("input_cycle_filing_proof_runtime")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    module.MODULE_SOURCE_SHA256 = sha(raw)
    print(json.dumps(module.main(), sort_keys=True, separators=(",", ":")))
