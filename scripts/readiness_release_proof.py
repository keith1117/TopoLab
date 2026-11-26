"""Verify retained admission evidence and replay the certificate on its sealed graph."""

import resource
import subprocess
import sys
import time
from pathlib import Path

from certificate_replay_proof import PYTHON, checkout_commit
from child_readiness_proof import pair
from r0_read_independent import canonical, need, parse, sha, terminal
from readiness_release_fixtures import cases
from readiness_release_fixtures import verify as verify_public

REPO = Path(__file__).resolve().parents[1]
DATA = Path("/Users/keith1117/Documents/TopoLab-data/readiness-20261126-a1")
FORMAL = DATA.with_name(DATA.name + "-formal")
PREVIOUS = DATA.parent / "closeout-20261125-formal"
PROTOCOL = "docs/planning/readiness_formal_contract.json"
WORKER = "scripts/readiness_release_proof.py"
LAUNCHER = "scripts/readiness_release_verify.py"
BUDGET = "640b7726526afdb5ea161ccfbb83fa9f3cf56d7f764561eaf892716b18118581"
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.readiness-20261126-a1.v1"
AUTHOR = "/root/full60_independent"
STATUS = "PASS_RELEASED_INPUT_PREREQUISITES"
PACKAGE, ACTUAL = "readiness-release.json", "readiness-release-actual.json"
PREVIOUS_REPORT = "6b00d1251094b23bba711aba9b229253152b605b88ad80e48a997191af3a1665"
PREVIOUS_ACTUAL = "95c9d0be31f0719350add64d283533fe0fe94f081f3c6af1f87ba8ad5c54d6c6"


def argv_for(slot):
    need(type(slot) is int and 1 <= slot <= 4, "verification slot outside finite budget")
    return [
        "/usr/bin/timeout",
        "-k",
        "2",
        "290",
        PYTHON,
        "-I",
        str(REPO / LAUNCHER),
        "verify",
        str(slot),
    ]


def reservation(slot, policy, tree):
    argv = argv_for(slot)
    raw = pair(DATA, f"readiness-verification-{slot}-entry.json")
    entry = parse(raw)
    need(
        entry["slot"] == slot
        and entry["execution_identity"] == IDENTITY
        and entry["charge_FULL"] == 300
        and entry["budget_sha256"] == BUDGET
        and entry["argv"] == argv
        and entry["author"] == AUTHOR
        and entry["source_main"] == checkout_commit(REPO)
        and entry["worker_sha256"] == tree[WORKER]
        and entry["end_ms"] - entry["start_ms"] == 290_000
        and policy["independent_author_start_ms"] <= entry["start_ms"]
        and entry["end_ms"] <= policy["global_deadline_ms"],
        "release verifier reservation differs",
    )
    cases(entry["public_slots"])
    return entry, sha(raw)


def check_policy(policy):
    need(
        policy["execution_identity"] == IDENTITY
        and policy["actors"]["independent"] == AUTHOR
        and policy["new_input_budget"] == dict(path=str(DATA / "owner-budget.json"), sha256=BUDGET)
        and sha(pair(DATA, "owner-budget.json")) == BUDGET
        and policy["readiness_verification_paths"]
        == dict(package=str(FORMAL / PACKAGE), actual=str(FORMAL / ACTUAL)),
        "wrong release verifier policy or external budget",
    )


def historical_closeouts(tree):
    import closeout_readiness_proof as old

    raw, actual = pair(PREVIOUS, old.PACKAGE), pair(PREVIOUS, old.ACTUAL)
    need(
        sha(raw) == PREVIOUS_REPORT and sha(actual) == PREVIOUS_ACTUAL,
        "historical public release evidence differs",
    )
    report = parse(raw)
    first, last, output = terminal(
        parse(actual),
        old.gate_args([4, 5, 6]),
        author=AUTHOR,
        cwd=str(old.REPO),
        window=(old.START, old.END),
    )
    need(
        output
        == canonical(dict(status=old.STATUS, report_sha256=PREVIOUS_REPORT, verification_slot=1))
        and report["independent_entry"]["start_ms"]
        <= first
        <= last
        <= report["independent_entry"]["end_ms"],
        "previous release original differs",
    )
    runs = [old.public_run(slot) for slot in (4, 5)]
    runs.append(old.public_run(6, origins={r["slot"]: r for r in runs}))
    need(
        runs == report["runs"]
        and [r["kind"] for r in runs] == ["FULL_POSITIVE", "FULL_POSITIVE", "REPLAY_NEGATIVE"],
        "previous public controls do not reproduce their released result",
    )
    # These are the runtime byte transport and the two public drivers that exercised it.
    unchanged = (
        "scripts/closeout_receipt.py",
        "scripts/closeout_public_control.py",
        "scripts/closeout_public_schedule.mjs",
        old.WORKER,
    )
    need(
        all(
            tree[name] == runs[0]["source_tree"][name] == sha((REPO / name).read_bytes())
            for name in unchanged
        ),
        "historical closeout worker/public driver bytes differ",
    )
    return dict(
        original_sha256=PREVIOUS_ACTUAL,
        report_sha256=PREVIOUS_REPORT,
        archive_sha256=[r["archive_sha256"] for r in runs],
        unchanged={name: tree[name] for name in unchanged},
    )


def prerequisites(policy, tree):
    import certificate_replay_archive as archive
    import certificate_replay_proof as previous_cert
    import formal_input_independent as rehearsal
    import p17_m2_input_continuation as profiles
    import staged_binding_evidence as registration

    old = historical_closeouts(tree)
    context, observations = registration.verified_formal_registration()
    need(
        len(observations) == len({row["path"] for row in observations}) == 23,
        "complete historical registration required",
    )
    prior = policy["prior_public"]
    need(prior == rehearsal.expected_prior(FORMAL), "wrong historical public namespace")
    public = rehearsal.verify_prior_public(
        prior,
        pair(FORMAL, "prior-public-bundle.json"),
        pair(FORMAL, "prior-public-certificate-actual.json"),
    )
    retained = parse(pair(PREVIOUS, "closeout-readiness.json"))
    reg = retained["prior_evidence"]["registration"]
    need(
        sha(canonical(context)) == reg["context_sha256"]
        and sha(canonical(observations)) == reg["observations_sha256"]
        and policy["registration"]["formal"] == retained["registration"]
        and public == retained["prior_evidence"]["public"],
        "historical registration/rehearsal changed",
    )

    checker = profiles.profile("independent", profiles.WINDOW_FORMAL)
    control = profiles.profile("control", profiles.WINDOW_FORMAL)
    bundle, events = archive.historical_inputs(checker)
    result = control.certificate_result(
        bundle,
        events,
        checker,
        historical_software_context=checker.historical_software_context(bundle["plan"]),
    )
    need(
        result["plan_sha256"] == archive.PLAN
        and result["version_id"] == previous_cert.VERSION
        and result["member_count"] == 1071
        and result["source_input_accepted"] is False
        and len(events) == 8
        and bundle["lease"]["state"] == "RELEASED",
        "complete historical certificate recheck failed",
    )
    return dict(
        closeouts=old,
        registration=reg,
        public=public,
        certificate=result,
        historical_certificate_command_exit=1,
        historical_archive_sha256=archive.ARCHIVE,
    )


def verify(slot):
    import p17_m2_input_continuation as profiles
    import staged_input_filer as wire

    policy = profiles.profile("registered", profiles.READINESS_FORMAL).authority()
    tree = profiles.profile("control", profiles.READINESS_FORMAL).source_freeze(IDENTITY)
    check_policy(policy)
    entry, pin = reservation(slot, policy, tree)

    def git(*words):
        return subprocess.check_output(["git", *words], cwd=REPO, timeout=15).decode().strip()

    main = checkout_commit(REPO)
    need(
        sys.flags.isolated
        and sys.executable == PYTHON
        and Path.cwd() == REPO
        and main == git("rev-parse", "origin/main")
        and git("branch", "--show-current") == "main"
        and not git("status", "--porcelain", "-uall")
        and entry["start_ms"] <= time.time_ns() // 1_000_000 <= entry["end_ms"],
        "verification requires the clean released checkout inside its reserved window",
    )
    public = verify_public(entry["public_slots"], DATA, REPO, main, tree, BUDGET)
    need(public["last_returned_ms"] <= entry["start_ms"], "public gate after release reservation")
    facts = prerequisites(policy, tree)
    import full60_input_loader as loader

    executed = {}
    required = (
        WORKER,
        LAUNCHER,
        "scripts/readiness_release_fixtures.py",
        "scripts/full60_input_loader.py",
        "scripts/certificate_replay_archive.py",
        "scripts/r0_read_independent.py",
        "scripts/p17_m2_source_acquisition_independent.py",
        "scripts/p17_m2_source_acquisition_control.py",
        "scripts/staged_binding_evidence.py",
        "scripts/closeout_readiness_proof.py",
        "scripts/formal_input_independent.py",
    )
    for name in required:
        executed[name] = loader.loaded_source_sha256.get(str(REPO / name))
        need(
            executed[name] == tree[name] == sha((REPO / name).read_bytes()),
            "actual release verifier source differs: " + name,
        )
    need(
        sys.platform == "darwin"
        and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 4 * 1024**3
        and time.time_ns() // 1_000_000 <= entry["end_ms"],
        "release verifier resource cap",
    )
    report = dict(
        status=STATUS,
        execution_identity=IDENTITY,
        source_main=main,
        slot=slot,
        entry_sha256=pin,
        software_tree_sha256=sha(canonical(tree)),
        budget_sha256=BUDGET,
        authority_sha256=tree[PROTOCOL],
        executed=executed,
        prerequisites=facts,
        public_readiness=public,
    )
    raw = canonical(report)
    for directory in (FORMAL, FORMAL.with_name(FORMAL.name + "-backup")):
        wire.write_private(directory / f"readiness-release-slot-{slot}.json", raw)
    return dict(status=STATUS, slot=slot, report_sha256=sha(raw))


def verified_readiness(policy, tree):
    check_policy(policy)
    raw, actual = pair(FORMAL, PACKAGE), pair(FORMAL, ACTUAL)
    report = parse(raw)
    slot = report["slot"]
    entry, pin = reservation(slot, policy, tree)
    first, last, output = terminal(
        parse(actual),
        argv_for(slot),
        author=AUTHOR,
        cwd=str(REPO),
        window=(entry["start_ms"], entry["end_ms"]),
    )
    need(
        report["status"] == STATUS
        and report["execution_identity"] == IDENTITY
        and report["source_main"] == checkout_commit(REPO)
        and [r["slot"] for r in report["public_readiness"]["fixtures"]] == entry["public_slots"]
        and [r["case"] for r in report["public_readiness"]["fixtures"]]
        == [case for _, case in cases(entry["public_slots"])]
        and report["entry_sha256"] == pin
        and report["budget_sha256"] == BUDGET
        and report["authority_sha256"] == tree[PROTOCOL]
        and report["software_tree_sha256"] == sha(canonical(tree))
        and report["executed"][WORKER] == tree[WORKER] == sha((REPO / WORKER).read_bytes())
        and report["executed"][LAUNCHER] == tree[LAUNCHER]
        and raw == pair(FORMAL, f"readiness-release-slot-{slot}.json")
        and first <= last <= time.time_ns() // 1_000_000
        and output == canonical(dict(status=STATUS, slot=slot, report_sha256=sha(raw))),
        "release verifier report/original differs",
    )
    return dict(
        source_main=report["source_main"],
        verified_returned_ms=last,
        package=dict(path=str(FORMAL / PACKAGE), sha256=sha(raw)),
        actual=dict(path=str(FORMAL / ACTUAL), sha256=sha(actual)),
    )
