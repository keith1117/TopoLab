"""Bind the complete archived certificate replay to the protected formal release."""

import hashlib
import json
import resource
import subprocess
import sys
import time
from pathlib import Path

from certificate_replay_archive import ARCHIVE, FAILED, HISTORICAL_MAIN, PLAN, need, pair, sha
from staged_input_filer import canonical

REPO = Path("/private/tmp/topolab-certificate-20261124")
DATA = Path("/Users/keith1117/Documents/TopoLab-data/certificate-20261124")
FORMAL = Path(str(DATA) + "-formal")
PROTOCOL = "docs/planning/certificate_formal_contract.json"
BUDGET = "7ae3b524775086003d636d15e747333bdc7c9abd96ea34ea67f9f6e0cf999595"
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.certificate-20261124.v1"
PYTHON = (
    "/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python"
)
AUTHOR = "/root/full60_independent"
START = 1795512528325
DIAGNOSTIC_END = 1795570128325
STATUS = "PASS_SEALED_FULL_CERTIFICATE_REPLAY"
VERSION = "981ff827c0ef6592e684bbff9c7b5745a2b7bd62a1b6c6b76eff0eae8ed3a21a"
PACKAGE = "certificate-replay.json"
ACTUAL = "certificate-replay-actual.json"
SOFTWARE = (
    "scripts/certificate_verify.py",
    "scripts/certificate_replay_proof.py",
    "scripts/certificate_replay_archive.py",
    "scripts/p17_m2_source_acquisition_control.py",
    "scripts/p17_m2_source_acquisition_independent.py",
    "scripts/p17_m2_content_verified_independent.py",
    "scripts/full60_input_loader.py",
    "scripts/staged_input_filer.py",
    "scripts/r0_caller_receipt.py",
)
MODULE_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def gate_args():
    return [
        "/usr/bin/timeout",
        "-k",
        "2",
        "290",
        PYTHON,
        "-I",
        str(REPO / "scripts/certificate_verify.py"),
        "verify",
    ]


def run(checker, bundle, events, *, publish):
    import p17_m2_input_continuation as profiles
    import staged_input_filer as wire

    need(
        sys.flags.isolated and Path.cwd() == REPO and sys.executable == PYTHON,
        "wrong certificate replay runtime",
    )
    need(START <= time.time_ns() // 10**6 < DIAGNOSTIC_END, "diagnostic budget expired")

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=REPO, timeout=15).decode().strip()

    head = git("rev-parse", "HEAD")
    if publish:
        need(
            head == git("rev-parse", "origin/main")
            and git("branch", "--show-current") == "main"
            and not git("status", "--porcelain", "-uall"),
            "exact clean released main required",
        )
    historical = checker.historical_software_context(bundle["plan"])
    control = profiles.profile("control", profiles.WINDOW_FORMAL)
    result = control.certificate_result(
        bundle, events, checker, historical_software_context=historical
    )
    need(
        result["member_count"] == 1071
        and result["version_id"] == VERSION
        and result["source_input_accepted"] is False
        and result["plan_sha256"] == PLAN,
        "incomplete reconstructed certificate",
    )
    loader = sys.modules["full60_input_loader"]
    executed = {n: loader.loaded_source_sha256.get(str(REPO / n)) for n in SOFTWARE}
    need(
        all(executed[n] == sha((REPO / n).read_bytes()) for n in SOFTWARE),
        "actually compiled replay software differs",
    )
    live = profiles.profile("control", profiles.CERT_FORMAL)
    tree = live.source_freeze(IDENTITY)
    need(all(tree[n] == executed[n] for n in SOFTWARE), "formal and replay software differ")
    report = dict(
        status=STATUS,
        scope="OFFLINE_HISTORICAL_EVIDENCE_ONLY",
        formal_certificate_issued=False,
        historical_command_exit=1,
        historical_source_main=HISTORICAL_MAIN,
        historical_plan_sha256=PLAN,
        historical_original_sha256=FAILED,
        historical_archive_sha256=ARCHIVE,
        historical_tree_sha256=sha(canonical(bundle["plan"]["source_tree"])),
        historical_software_count=len(bundle["plan"]["source_tree"]),
        certificate_result=result,
        lease_state=bundle["lease"]["state"],
        accepted_roles=bundle["plan"]["role_order"],
        raw_event_pairs=len(events),
        checkout_head=head,
        source_main=head if publish else None,
        revision_state="CLEAN_PROTECTED_MAIN" if publish else "PREPUBLICATION",
        software_tree_sha256=sha(canonical(tree)),
        executed=executed,
        budget_sha256=BUDGET,
        contract_sha256=sha((REPO / PROTOCOL).read_bytes()),
    )
    need(
        report["lease_state"] == "RELEASED" and report["raw_event_pairs"] == 8,
        "archived closeout incomplete",
    )
    need(
        sys.platform == "darwin"
        and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 4 * 1024**3,
        "offline certificate resource cap",
    )
    need(time.time_ns() // 10**6 <= DIAGNOSTIC_END, "diagnostic completion deadline expired")
    raw = canonical(report)
    if publish:
        for folder in (FORMAL, FORMAL.with_name(FORMAL.name + "-backup")):
            wire.write_private(folder / PACKAGE, raw)
        return canonical(dict(status=STATUS, report_sha256=sha(raw))).decode()
    return raw.decode()


def verified_readiness(policy, tree):
    import r0_read_independent as original

    need(
        policy["execution_identity"] == IDENTITY
        and policy["new_input_budget"]
        == {"path": str(DATA / "owner-budget.json"), "sha256": BUDGET}
        and sha(pair(DATA, "owner-budget.json")) == BUDGET
        and policy["certificate_verification_paths"]
        == {"package": str(FORMAL / PACKAGE), "actual": str(FORMAL / ACTUAL)},
        "unexpected formal replay authority",
    )
    raw, actual_raw = pair(FORMAL, PACKAGE), pair(FORMAL, ACTUAL)
    report = json.loads(raw)
    _, last, stdout = original.terminal(
        json.loads(actual_raw),
        gate_args(),
        author=AUTHOR,
        cwd=str(REPO),
        window=(START, DIAGNOSTIC_END),
        full=300,
    )
    need(
        report["status"] == STATUS
        and stdout == canonical(dict(status=STATUS, report_sha256=sha(raw)))
        and report["scope"] == "OFFLINE_HISTORICAL_EVIDENCE_ONLY"
        and report["revision_state"] == "CLEAN_PROTECTED_MAIN"
        and report["checkout_head"] == report["source_main"]
        and report["formal_certificate_issued"] is False
        and report["historical_command_exit"] == 1
        and report["historical_archive_sha256"] == ARCHIVE
        and report["historical_original_sha256"] == FAILED
        and report["historical_plan_sha256"] == PLAN
        and report["historical_source_main"] == HISTORICAL_MAIN
        and report["certificate_result"]["member_count"] == 1071
        and report["certificate_result"]["version_id"] == VERSION
        and report["lease_state"] == "RELEASED"
        and report["raw_event_pairs"] == 8
        and report["budget_sha256"] == BUDGET
        and report["contract_sha256"] == tree[PROTOCOL]
        and report["software_tree_sha256"] == sha(canonical(tree))
        and report["executed"] == {n: tree[n] for n in SOFTWARE}
        and report["source_main"]
        == subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, timeout=15)
        .decode()
        .strip(),
        "independent complete replay or software version differs",
    )
    return dict(
        source_main=report["source_main"],
        verified_returned_ms=last,
        package=dict(path=str(FORMAL / PACKAGE), sha256=sha(raw)),
        actual=dict(path=str(FORMAL / ACTUAL), sha256=sha(actual_raw)),
    )
