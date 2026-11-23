"""Independently replay the sealed A1 stop and two exact label recovery reads.

Only retained metadata and original buffers supplied by those new paid reads are
consumed. This verifier never reopens a business path or resumes an old graph.
"""

import argparse
import base64
import hashlib
import io
import os
import resource
import stat
import subprocess
import sys
import tarfile
import time
from pathlib import Path
from types import ModuleType

SOURCE_CHECKOUT = Path(__file__).resolve().parents[1]
REPO = Path("/private/tmp/topolab-input-cycle-20261123-a2")
OLD_REPO = REPO.with_name("topolab-input-cycle-20261123")
DATA = Path("/Users/keith1117/Documents/TopoLab-data")
CAMPAIGN = DATA / "input-cycle-20261123"
A1 = DATA / "input-cycle-20261123-a1"
E = DATA / "input-cycle-20261123-a2"
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.cycle-20261123-a2.v1"
PREVIOUS_MAIN = "52be62d2d4526639bedc0ca63f75aa149da9c259"
AUTHOR = "/root/full60_independent"
PROTOCOL = "docs/planning/input_cycle_a2_contract.json"
WORKER = "scripts/input_cycle_r1_proof.py"
RECHECK = "scripts/r1_label_recheck.py"
BASE = "scripts/input_cycle_proof.py"
BASE_SHA = "b6b46f8a7466fdc75b96aa29aee48fd4a7bf3c2f3f86416eca393e03391fd8dc"
BASELINE_WORKER_SHA = "ccbfa0f20f8f84285cd9b0d0eca166160f1bc47a199951b427c809ac8777cd25"
READER_SOURCES = tuple(
    "scripts/" + name
    for name in (
        "r1_label_recheck.py",
        "staged_input_filer.py",
        "cycle_r1_registered_input.py",
        "full60_input_loader.py",
        "p17_m2_input_continuation.py",
        "p17_m2_registered_input.py",
        "p17_m2_input_export.py",
        "p17_m2_source_acquisition_control.py",
    )
)
CHECKER = "scripts/p17_m2_input_export_independent.py"
CAMPAIGN_SHA = "9ab62a69584a1ec2179b7fb9bd13a7b23a5564bcd8413a34f5ecb5f99d3c848b"
ATTEMPT_SHA = "6f4168eb23d191629a98c42c469933e0016a1ba2090c521995fc0eeb606a06de"
ARCHIVE_SHA = "e1ebd26314a282894de81acd28d1733e66be07b061ba35b202ab54cbec044536"
INDEX_SHA = "ffbfc42c1f857d62048a984f49905100c29f690887c5c522d37ef08c92763222"
CLOSED_SHA = "c534d1a11d3cfdb8d8864d284d8002b6489b6644fc4b0a2916326cb90d2e19da"
AUDIT_SHA = "17f60d2c5fedfc242033e9c6163056121480e9cd5323e3d00bfde3313442d276"
LABEL_SHA = "f182bf71f5edf86333d9908585083d1c0a07af98f65d8a72d181e1b35aca3874"
CASE = "tlcase-v1-0a490c9248cdfcd1a92a893f8b19a930ec4308db6da27a61deb3e475c57f8ac8"
RELATIVE = f"b3-v1-data/artifacts/label/{CASE}/{LABEL_SHA}.json"
LABEL_SIZE = 472469
POINTS = ("declared", "before", "after", "closing")
PHYSICAL = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
BASELINE_REPORT_SHA = "87839cc88cf3e4809e296a6cf4f5f84e6a826bf1dcab11e6ac33011588301d45"
BASELINE_ACTUAL_SHA = "f1f2db0f39e5f25dbf686387452599d1fbc41113ca7fc88dadeb434f48dc293b"
PYTHON = (
    "/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python"
)
START, END = 1795403546212, 1795576346212
PACKAGE, ACTUAL = "r1-recovery-report-a2.json", "r1-recovery-actual-a2.json"
SUCCESS = "PASS_TWO_REGISTERED_LABEL_READS_FOR_A2_RELEASE"
MODULE_SOURCE_SHA256 = None
_BASE_MODULE = None


def need(ok, reason):
    if not ok:
        raise ValueError("R1_RECOVERY_PROOF_STOP: " + reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _base():
    global _BASE_MODULE
    if _BASE_MODULE is None:
        path = SOURCE_CHECKOUT / BASE
        raw = path.read_bytes()
        need(sha(raw) == BASE_SHA, "independent A1 bridge source differs")
        module = ModuleType("r1_recovery_a1_bridge")
        module.__file__ = str(path)
        exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
        module.MODULE_SOURCE_SHA256 = sha(raw)
        _BASE_MODULE = module
        loader = sys.modules.get("full60_input_loader")
        if loader is not None:
            loader.loaded_source_sha256[str(path)] = sha(raw)
    return _BASE_MODULE


def _checker():
    base = _base()
    raw = base._read(SOURCE_CHECKOUT / CHECKER)
    need(sha(raw) == base.SOURCE_PINS[CHECKER], "independent label checker source differs")
    return base._compile(raw, "r1_recovery_label_comparator", CHECKER)


def _self_sha():
    loader = sys.modules.get("full60_input_loader")
    observed = getattr(loader, "loaded_source_sha256", {}).get(str(SOURCE_CHECKOUT / WORKER))
    value = MODULE_SOURCE_SHA256 if MODULE_SOURCE_SHA256 is not None else observed
    need(
        type(value) is str and len(value) == 64 and (observed is None or value == observed),
        "actual compiled A2 proof source missing",
    )
    return value


def _policy(policy):
    base = _base()
    need(
        policy.get("execution_identity") == IDENTITY
        and policy.get("campaign_budget")
        == dict(path=str(CAMPAIGN / "campaign-budget.json"), sha256=CAMPAIGN_SHA)
        and policy.get("new_input_budget")
        == dict(path=str(CAMPAIGN / "attempt-2-budget.json"), sha256=ATTEMPT_SHA)
        and policy.get("r1_recovery_verification_paths")
        == dict(package=str(E / PACKAGE), actual=str(E / ACTUAL))
        and policy.get("predecessor_terminal")
        == dict(path=str(A1 / "attempt-one-closed.json"), sha256=CLOSED_SHA)
        and policy.get("predecessor_independent_audit")
        == dict(path=str(A1 / "independent-a1-terminal-audit.json"), sha256=AUDIT_SHA),
        "exact A2 predecessor/budget/proof policy differs",
    )
    base.pair(CAMPAIGN, "campaign-budget.json", CAMPAIGN_SHA)
    base.pair(CAMPAIGN, "attempt-2-budget.json", ATTEMPT_SHA)


def _anchor():
    """Derive physical identifiers from the sealed original observations only."""
    base = _base()
    raw = base.pair(A1, "formal-generated-controls-a1.tar.gz", ARCHIVE_SHA)
    index = base.parse(base.pair(A1, "formal-generated-controls-index-a1.json", INDEX_SHA))
    closed = base.parse(base.pair(A1, "attempt-one-closed.json", CLOSED_SHA))
    audit = base.parse(base.pair(A1, "independent-a1-terminal-audit.json", AUDIT_SHA))
    members = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        for member in archive:
            need(
                member.isfile() and member.name in index["members"] and member.name not in members,
                "sealed archive type/inventory differs",
            )
            size, pin = index["members"][member.name]
            need(type(size) is int and 0 < size == member.size <= base.CAP, "sealed member cap")
            value = archive.extractfile(member).read(size + 1)
            need(len(value) == size and sha(value) == pin, "sealed member bytes differ")
            members[member.name] = value
    need(
        set(members) == set(index["members"])
        and len(members) == index["files"] == 93
        and sum(map(len, members.values())) == index["bytes"] == 2520879
        and index["archive_sha256"] == ARCHIVE_SHA,
        "sealed complete inventory differs",
    )

    def obj(name):
        return base.parse(members[name])

    registry, proof, failure, plan = map(
        obj, ("registry.json", "r0-proof.json", "exporter-r1-failure.json", "plan.json")
    )
    need(
        closed["status"] == "CLOSED_EXPORTER_R1_BOUNDED_READ_ERRNO60"
        and closed["source_main"] == PREVIOUS_MAIN
        and closed["formal_booked"] == 2400
        and closed["formal_closed_unused"] == 1560
        and closed["cumulative_floor"] == 349599
        and audit["status"] == "VERIFIED_A1_STOP_BOTH_R0_COMPLETE_R1_BOUNDED_READ"
        and audit["source_main"] == PREVIOUS_MAIN
        and audit["plan_sha256"] == closed["plan_sha256"] == sha(base.canonical(plan))
        and proof["source_count"] == len(proof["source_rows"]) == 40
        and proof["source_registry_sha256"] == sha(members["registry.json"]),
        "A1 original closure/R0 differs",
    )
    for role in ("exporter-r0", "independent-r0"):
        bound = obj("receipts/" + role + "-bind-original.json")
        accepted = audit["native_roles"][role]
        need(
            bound["full_role_evidence_accepted"] is True
            and bound["evidence_complete"] is True
            and bound["actual_exit_codes"] == [0, 0]
            and sha(base.canonical(bound)) == accepted["native_facts_sha256"]
            and accepted["accepted"] is True,
            "independent A1 dual-R0 proof differs",
        )
    (bad,) = failure["source_failures"]
    need(
        failure["error_type"] == "TimeoutError"
        and failure["reason"] == "[Errno 60] Operation timed out"
        and len(failure["source_read_table"]) == 34
        and bad["path"] == RELATIVE
        and bad["attempt_ordinal"] == 35
        and bad["stage"] == "bounded_read"
        and bad["returned_bytes"] is None
        and bad["after"] is None
        and bad["closing"] is None
        and bad["declared"] == bad["before"]
        and bad["expected_sha256"] == LABEL_SHA,
        "exact failed label source differs",
    )
    (item,) = [row for row in registry["labels"] if row["artifact"]["path"] == RELATIVE]
    need(
        item["artifact"] == dict(path=RELATIVE, byte_size=LABEL_SIZE, sha256=LABEL_SHA),
        "sealed label registry reference differs",
    )
    old_policy = base.parse(
        base._read(SOURCE_CHECKOUT / "docs/planning/input_cycle_a1_contract.json")
    )
    historical = base.verified_readiness(old_policy, plan["source_tree"])
    need(historical["source_main"] == PREVIOUS_MAIN, "A1 B3 proof/source differs")
    return (
        item,
        bad["declared"],
        dict(
            closed_sha256=CLOSED_SHA,
            independent_audit_sha256=AUDIT_SHA,
            archive_sha256=ARCHIVE_SHA,
            source_main=PREVIOUS_MAIN,
            plan_sha256=closed["plan_sha256"],
            dual_R0_counts=[40, 40],
            failed_payload_ordinal=35,
            failed_path=RELATIVE,
            closed_ms=closed["timestamp_ms"],
            historical_B3=historical,
            old_lease_state="HELD",
        ),
    )


def recheck_args(slot):
    need(type(slot) is int and slot in (1, 2), "exact two real slots required")
    worker = CAMPAIGN / "r1_label_recheck.py" if slot == 1 else REPO / RECHECK
    return ["/usr/bin/timeout", "-k", "2", "1190", PYTHON, "-I", str(worker), "--slot", str(slot)]


def verify_observation(
    slot,
    claim_raw,
    entered_raw,
    report_raw,
    actual_raw,
    *,
    item,
    anchor,
    source_main,
    source_tree=None,
):
    """Verify supplied original bytes, never the original URL; no producer oracle."""
    base = _base()
    wire = base._wire()
    if slot == 1:
        need(
            sha(report_raw) == BASELINE_REPORT_SHA and sha(actual_raw) == BASELINE_ACTUAL_SHA,
            "sealed baseline real observation bytes differ",
        )
    claim, entry, report, actual = map(base.parse, (claim_raw, entered_raw, report_raw, actual_raw))
    head = PREVIOUS_MAIN if slot == 1 else source_main
    repo = OLD_REPO if slot == 1 else REPO
    worker_sha = BASELINE_WORKER_SHA if slot == 1 else (source_tree or {}).get(RECHECK)
    need(wire.digest_word(worker_sha), "expected candidate worker source unavailable")
    need(
        claim
        == dict(
            schema="topolab.r1-label-claim.v1",
            slot=slot,
            argv=recheck_args(slot),
            repo=str(repo),
            source_main=head,
            worker_sha256=worker_sha,
            charge_FULL=1200,
            budget_sha256=CAMPAIGN_SHA,
            failed_archive_sha256=ARCHIVE_SHA,
            path=RELATIVE,
            claimed_ms=claim.get("claimed_ms"),
        )
        and type(claim["slot"]) is int
        and type(claim["claimed_ms"]) is int
        and START <= claim["claimed_ms"] <= END,
        "real claim identity/authority differs",
    )
    first, last, output = wire.terminal(
        actual, recheck_args(slot), author="/root", cwd=str(repo), window=(START, END), full=1200
    )
    need(
        report["schema"] == "topolab.r1-label-recheck.v1"
        and type(report["slot"]) is int
        and report["slot"] == slot
        and report["status"] == "PASS"
        and report["error"] is None
        and report["source_main"] == head
        and report["archive_sha256"] == ARCHIVE_SHA
        and report["worker_sha256"] == worker_sha
        and report["claim_sha256"] == sha(claim_raw)
        and type(entry.get("slot")) is int
        and entry == dict(slot=slot, claim_sha256=sha(claim_raw), entered_ms=report["started_ms"])
        and wire.integer(report["started_ms"])
        and wire.integer(report["ended_ms"])
        and claim["claimed_ms"] <= first <= report["started_ms"] <= report["ended_ms"] <= last
        and report["ended_ms"] - report["started_ms"] <= 1190000
        and wire.integer(report["rss_bytes"], 1)
        and report["rss_bytes"] <= 4 * 1024**3
        and output
        == base.canonical(
            dict(
                status="PASS",
                slot=slot,
                report_sha256=sha(report_raw),
                own_future_return="NOT_CLAIMED",
            )
        ),
        "real report/original terminal/window differs",
    )
    need(type(report["raw_base64"]) is str, "original returned buffer absent")
    raw = base64.b64decode(report["raw_base64"], validate=True)
    need(
        len(raw) == LABEL_SIZE == item["artifact"]["byte_size"]
        and sha(raw) == LABEL_SHA == item["artifact"]["sha256"],
        "original raw bytes differ",
    )
    facts = report["facts"]
    need(
        type(facts) is dict
        and report["attempts"] == [RELATIVE]
        and facts["attempt_ordinal"] == 1
        and type(facts["attempt_ordinal"]) is int
        and facts["path"] == RELATIVE
        and facts["execution_identity"] == "topolab.v2.p17-m2-local-input-version.v1"
        and facts.get("status") is None
        and facts["identity_policy"] == "topolab.source-identity.prebound-sha256.v1"
        and facts["expected_sha256"] == LABEL_SHA
        and facts["returned_bytes"] == LABEL_SIZE
        and type(facts["returned_bytes"]) is int
        and facts["source"] == item["artifact"]
        and facts["stage"] == "source_validation",
        "single real reader facts differ",
    )
    need(base.canonical(report["anchor"]) == base.canonical(anchor), "declared anchor differs")
    for point in POINTS:
        value = facts[point]
        need(
            type(value) is dict
            and set(value) == set(PHYSICAL)
            and all(type(v) is int and v >= 0 for v in value.values())
            and all(value[k] == anchor[k] for k in PHYSICAL[:-1]),
            "real four-point identity differs",
        )
    deltas = {
        point: facts[point]["st_mtime_ns"] - facts["declared"]["st_mtime_ns"]
        for point in POINTS[1:]
    }
    need(
        base.canonical(facts["mtime_changes"]) == base.canonical(deltas)
        and base.canonical(report["source_observations"])
        == base.canonical(
            [
                dict(
                    item["artifact"],
                    **{point: facts[point] for point in POINTS},
                    identity_policy=facts["identity_policy"],
                    expected_sha256=LABEL_SHA,
                    mtime_changes=deltas,
                )
            ]
        ),
        "original source observation/mtime inventory differs",
    )
    trace = report["trace"]
    need(
        type(trace) is list and len(trace) == 4 and [row["stage"] for row in trace] == list(POINTS),
        "actual four-stage trace differs",
    )
    prior = None
    for row in trace:
        need(
            type(row["flags"]) is type(row["blocks"]) is type(row["monotonic_ns"]) is int
            and min(row["flags"], row["blocks"], row["monotonic_ns"]) >= 0
            and (prior is None or prior <= row["monotonic_ns"]),
            "native storage trace differs",
        )
        prior = row["monotonic_ns"]
    need(
        type(report["elapsed_ns"]) is int
        and 0 < report["elapsed_ns"] <= 1190 * 10**9
        and trace[-1]["monotonic_ns"] - trace[0]["monotonic_ns"] <= report["elapsed_ns"]
        and report["elapsed_ns"] <= (last - first) * 10**6,
        "actual read interval differs",
    )
    if slot == 2:
        expected_sources = {name: source_tree[name] for name in READER_SOURCES}
        need(
            base.canonical(report.get("reader_source_sha256")) == base.canonical(expected_sources),
            "actual candidate reader source differs",
        )
        storage = {row["stage"]: dict(flags=row["flags"], blocks=row["blocks"]) for row in trace}
        need(
            base.canonical(facts.get("storage")) == base.canonical(storage),
            "candidate reader four storage records differ",
        )
    checked = _checker()
    views = checked.label_views(checked.parse(raw), item)
    return dict(
        slot=slot,
        source_main=head,
        worker_sha256=worker_sha,
        reader_source_sha256=report.get("reader_source_sha256") if slot == 2 else None,
        historical_reader_loaded_digest="NOT_RECORDED" if slot == 1 else "CURRENT_TREE_BOUND",
        claim_sha256=sha(claim_raw),
        entered_sha256=sha(entered_raw),
        report_sha256=sha(report_raw),
        actual_sha256=sha(actual_raw),
        raw_sha256=sha(raw),
        byte_size=len(raw),
        original_returned_ms=last,
        original_requested_ms=first,
        elapsed_ns=report["elapsed_ns"],
        rss_bytes=report["rss_bytes"],
        physical_anchor_sha256=sha(base.canonical(anchor)),
        storage_trace=trace,
        mtime_changes=deltas,
        independent_label_views_sha256=sha(checked.canonical(views)),
        FULL=1200,
        timeout_and_preflight_overhead_RSS="UNKNOWN_NOT_MEASURED",
    )


def _recover(source_main, source_tree):
    base = _base()
    item, anchor, predecessor = _anchor()
    observations = []
    for slot in (1, 2):
        parts = [
            base.pair(CAMPAIGN, f"real-{slot:02d}-{name}.json")
            for name in ("claim", "entered", "report", "actual")
        ]
        observations.append(
            verify_observation(
                slot,
                *parts,
                item=item,
                anchor=anchor,
                source_main=source_main,
                source_tree=source_tree,
            )
        )
    need(
        type(predecessor["closed_ms"]) is int
        and predecessor["closed_ms"] <= observations[0]["original_requested_ms"]
        and observations[0]["original_returned_ms"] <= observations[1]["original_requested_ms"]
        and observations[0]["independent_label_views_sha256"]
        == observations[1]["independent_label_views_sha256"],
        "two real reads disagree/overlap",
    )
    return dict(
        predecessor=predecessor,
        observations=observations,
        real_FULL=2400,
        new_original_reads_by_verifier=0,
        live_original_path_opens=0,
        captured_original_buffers_replayed=2,
        captured_original_buffer_bytes=2 * LABEL_SIZE,
        formal_R1_admitted=False,
    )


def verify_args():
    return ["/usr/bin/timeout", "-k", "2", "290", PYTHON, "-I", str(REPO / WORKER), "verify"]


def verify_return(pin):
    return dict(
        schema="topolab.r1-recovery-return.v1",
        slot=2,
        status=SUCCESS,
        report_sha256=pin,
        own_future_return="NOT_CLAIMED",
    )


def _claim(raw, publication):
    base = _base()
    claim = base.parse(raw)
    need(
        claim
        == dict(
            schema="topolab.input-cycle-offline-claim.v1",
            slot=2,
            actor=AUTHOR,
            argv=verify_args(),
            repo=str(REPO),
            source_main=publication["source_main"],
            worker_sha256=publication["worker_sha256"],
            budget_sha256=CAMPAIGN_SHA,
            attempt_budget_sha256=ATTEMPT_SHA,
            charge_FULL=300,
            claimed_ms=claim.get("claimed_ms"),
        )
        and type(claim["slot"]) is type(claim["claimed_ms"]) is int
        and START <= claim["claimed_ms"] <= END,
        "A2 original offline claim differs",
    )
    return claim


def _save(root, name, value):
    base = _base()
    raw = base.canonical(value)
    need(
        (root, name) in ((CAMPAIGN, "offline-02-entered.json"), (E, PACKAGE))
        and len(raw) <= base.CAP,
        "fixed A2 output/cap required",
    )
    for folder in (root, root.with_name(root.name + "-backup")):
        parent = base._directory(folder)
        try:
            owner = os.fstat(parent)
            need(
                owner.st_uid == os.getuid() and stat.S_IMODE(owner.st_mode) == 0o700,
                "private A2 receipt directory required",
            )
            fd = os.open(
                name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent
            )
            try:
                count = 0
                while count < len(raw):
                    n = os.write(fd, raw[count:])
                    need(n > 0, "partial A2 receipt write")
                    count += n
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(parent)
        finally:
            os.close(parent)
    need(base.pair(root, name) == raw, "A2 receipt pair differs")
    return sha(raw)


def current_publication():
    base = _base()
    need(
        SOURCE_CHECKOUT == REPO
        and Path.cwd() == REPO
        and sys.executable == PYTHON
        and sys.flags.isolated == 1,
        "exact A2 isolated runtime required",
    )

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=REPO, timeout=20)

    head = git("rev-parse", "HEAD").decode().strip()
    need(
        base._wire().digest_word(head, 40)
        and head != PREVIOUS_MAIN
        and git("branch", "--show-current").strip() == b"main"
        and git("rev-parse", "origin/main").decode().strip() == head
        and not git("status", "--porcelain=v1", "-uall").strip(),
        "clean protected A2 release required",
    )
    result = dict(source_main=head, repo=str(REPO))
    for key, path in (
        ("authority_sha256", PROTOCOL),
        ("worker_sha256", WORKER),
        ("checker_sha256", CHECKER),
        ("recheck_worker_sha256", RECHECK),
    ):
        raw = base._read(REPO / path)
        need(raw == git("show", head + ":" + path), "A2 published source buffer differs")
        result[key] = sha(raw)
    result["reader_source_sha256"] = {}
    for name in READER_SOURCES:
        raw = base._read(REPO / name)
        need(raw == git("show", head + ":" + name), "candidate reader published source differs")
        result["reader_source_sha256"][name] = sha(raw)
    need(
        result["worker_sha256"] == _self_sha()
        and result["checker_sha256"] == base.SOURCE_PINS[CHECKER],
        "A2 executed/reader pins differ",
    )
    return result


def verify_cli():
    base = _base()
    pub = current_publication()
    _policy(base.parse(base._read(REPO / PROTOCOL)))
    claim_raw = base.pair(CAMPAIGN, "offline-02-claim.json")
    claim = _claim(claim_raw, pub)
    start = time.time_ns() // 1_000_000
    need(claim["claimed_ms"] <= start < END, "A2 original offline clock exhausted")
    entered = dict(
        slot=2, execution_identity=IDENTITY, started_ms=start, claim_sha256=sha(claim_raw)
    )
    entry_pin = _save(CAMPAIGN, "offline-02-entered.json", entered)
    recovered = _recover(pub["source_main"], pub["reader_source_sha256"])
    end = time.time_ns() // 1_000_000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    need(
        sys.platform == "darwin"
        and type(rss) is int
        and 0 < rss <= 4 * 1024**3
        and start <= end <= END
        and end - start <= 290000,
        "A2 offline time/RSS differs",
    )
    report = dict(
        schema="topolab.r1-recovery-report.v1",
        status=SUCCESS,
        slot=2,
        execution_identity=IDENTITY,
        campaign_budget_sha256=CAMPAIGN_SHA,
        attempt_budget_sha256=ATTEMPT_SHA,
        claim_sha256=sha(claim_raw),
        entered_sha256=entry_pin,
        started_ms=start,
        ended_ms=end,
        self_rss_bytes=rss,
        recovered=recovered,
        **pub,
    )
    return verify_return(_save(E, PACKAGE, report))


def verified_readiness(policy, tree):
    base = _base()
    _policy(policy)
    report_raw, actual_raw = base.pair(E, PACKAGE), base.pair(E, ACTUAL)
    report, actual = base.parse(report_raw), base.parse(actual_raw)
    claim_raw, entry_raw = (
        base.pair(CAMPAIGN, "offline-02-claim.json"),
        base.pair(CAMPAIGN, "offline-02-entered.json"),
    )
    claim, entry = _claim(claim_raw, report), base.parse(entry_raw)
    wire = base._wire()
    first, last, output = wire.terminal(
        actual, verify_args(), author=AUTHOR, cwd=str(REPO), window=(START, END), full=300
    )
    recovered = _recover(report["source_main"], tree)
    need(
        report["schema"] == "topolab.r1-recovery-report.v1"
        and report["status"] == SUCCESS
        and report["execution_identity"] == IDENTITY
        and type(report["slot"]) is int
        and report["slot"] == 2
        and report["campaign_budget_sha256"] == CAMPAIGN_SHA
        and report["attempt_budget_sha256"] == ATTEMPT_SHA
        and report["repo"] == str(REPO)
        and wire.digest_word(report["source_main"], 40)
        and report["source_main"] != PREVIOUS_MAIN
        and report["authority_sha256"] == tree[PROTOCOL]
        and report["worker_sha256"] == tree[WORKER] == _self_sha()
        and report["checker_sha256"] == tree[CHECKER] == base.SOURCE_PINS[CHECKER]
        and report["recheck_worker_sha256"] == tree[RECHECK]
        and base.canonical(report["reader_source_sha256"])
        == base.canonical({name: tree[name] for name in READER_SOURCES})
        and wire.compiled_sha256 == tree[base.WIRE]
        and BASE_SHA == tree[BASE]
        and report["claim_sha256"] == sha(claim_raw)
        and report["entered_sha256"] == sha(entry_raw)
        and type(entry.get("slot")) is int
        and entry
        == dict(
            slot=2,
            execution_identity=IDENTITY,
            started_ms=report["started_ms"],
            claim_sha256=sha(claim_raw),
        )
        and wire.integer(report["started_ms"])
        and wire.integer(report["ended_ms"])
        and claim["claimed_ms"] <= first <= report["started_ms"] <= report["ended_ms"] <= last
        and recovered["observations"][-1]["original_returned_ms"] <= first
        and wire.integer(report["self_rss_bytes"], 1)
        and report["self_rss_bytes"] <= 4 * 1024**3
        and base.canonical(report["recovered"]) == base.canonical(recovered)
        and output == base.canonical(verify_return(sha(report_raw))),
        "A2 original recovery return differs",
    )
    return dict(
        package=dict(path=str(E / PACKAGE), sha256=sha(report_raw)),
        actual=dict(path=str(E / ACTUAL), sha256=sha(actual_raw)),
        source_main=report["source_main"],
        previous_source_main=PREVIOUS_MAIN,
        authority_sha256=report["authority_sha256"],
        worker_sha256=report["worker_sha256"],
        recheck_worker_sha256=tree[RECHECK],
        checker_sha256=report["checker_sha256"],
        accepted_real_slots=[1, 2],
        failed_path=RELATIVE,
        failed_archive_sha256=ARCHIVE_SHA,
        predecessor_terminal_sha256=CLOSED_SHA,
        predecessor_independent_audit_sha256=AUDIT_SHA,
        slot=2,
        verified_returned_ms=last,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["verify"])
    parser.parse_args()
    raw = _base()._read(Path(__file__).absolute())
    module = ModuleType("input_cycle_r1_proof_runtime")
    module.__file__ = str(SOURCE_CHECKOUT / WORKER)
    exec(compile(raw, module.__file__, "exec", dont_inherit=True), module.__dict__)
    module.MODULE_SOURCE_SHA256 = sha(raw)
    print(_base().canonical(module.verify_cli()).decode(), end="")
