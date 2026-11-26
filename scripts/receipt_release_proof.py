"""Verify retained admission evidence and replay the certificate on its sealed graph."""

import resource
import subprocess
import sys
import time
from pathlib import Path

from certificate_replay_proof import PYTHON, checkout_commit
from child_readiness_proof import pair
from r0_read_independent import canonical, need, parse, sha, terminal
from receipt_release_fixtures import cases
from receipt_release_fixtures import verify as verify_public

REPO = Path(__file__).resolve().parents[1]
DATA = Path("/Users/keith1117/Documents/TopoLab-data/receipt-20261126-b1")
FORMAL = DATA.with_name(DATA.name + "-formal")
PREVIOUS = DATA.parent / "readiness-20261126-a1"
PREVIOUS_REPO = Path("/private/tmp/topolab-readiness-20261126")
PROTOCOL = "docs/planning/receipt_formal_contract.json"
WORKER = "scripts/receipt_release_proof.py"
LAUNCHER = "scripts/receipt_release_verify.py"
BUDGET = "6b6cbf793c6415125d68d031c822f5e9a44eb819247756cf77c921f9e8ea49dd"
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.receipt-20261126-b1.v1"
AUTHOR = "/root/full60_independent"
STATUS = "PASS_RELEASED_INPUT_PREREQUISITES"
CANDIDATE_STATUS = "COMPLETED_CANDIDATE_HISTORICAL_REPLAY"
PACKAGE, ACTUAL = "readiness-release.json", "readiness-release-actual.json"
PREVIOUS_MAIN = "07abc057df5bd81ef255efd1c96d1fc66fe41f92"
PREVIOUS_LEDGER = "721bbd39d932c5935cda2e477d65b9b17442816b9a610689953f1b95f0fbfb9a"
PREVIOUS_ARCHIVE = "ad9b1ee7b7295d69fb29a4d6b69c4041142fe1ec6ce221fed5c4f71a46dce416"
PREVIOUS_INDEX = "6d8f407cb952735236ccaec13ecc0199cf2ac8e759c8dfb0d9a0c38afcbf9c33"
PREVIOUS_REPORT = "e21399e30a006144efee9186586ccbcab22d22d460c6fca5c33cbb8681a5d002"
PREVIOUS_ACTUAL = "2864818cb54f0c87d145c626107a78bf5e1b7b3b1fc6f368b231e85d54dbd353"


def argv_for(slot, *, candidate=False):
    need(type(slot) is int and 1 <= slot <= 4, "verification slot outside finite budget")
    return [
        "/usr/bin/timeout",
        "-k",
        "2",
        "290",
        PYTHON,
        "-I",
        str(REPO / LAUNCHER),
        "candidate" if candidate else "verify",
        str(slot),
    ]


def reservation(slot, policy, tree, *, candidate=False):
    argv = argv_for(slot, candidate=candidate)
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
        and entry["purpose"]
        == ("CANDIDATE_HISTORICAL_REPLAY_ONLY" if candidate else "RELEASED_PROOF")
        and (candidate or entry["public_source_main"] == entry["source_main"])
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
        and policy["independent_preflight_original_path"]
        == str(FORMAL / "input-preflight-original-a1.json")
        and policy["independent_preflight_actual_path"]
        == str(FORMAL / "input-preflight-actual-a1.json")
        and policy["preflight_custody_entry"] == "independent_preflight_custody.py"
        and policy["preparation_entry"] == "receipt_formal_preparation.py"
        and sha((REPO / PROTOCOL).read_bytes())
        == "8d2bf3065ed39b003e18b67d6d63baa2a0b6b40535af18cfa34e365f07a73dd1"
        and policy["readiness_verification_paths"]
        == dict(package=str(FORMAL / PACKAGE), actual=str(FORMAL / ACTUAL)),
        "wrong release verifier policy or external budget",
    )


def predecessor():
    import certificate_replay_archive as archive
    from readiness_release_fixtures import contents

    ledger_raw = pair(PREVIOUS, "final-ledger.json")
    end_raw = pair(PREVIOUS, "formal-a1-terminal.json")
    ledger, end = parse(ledger_raw), parse(end_raw)
    need(
        sha(ledger_raw) == PREVIOUS_LEDGER
        and ledger["terminal_sha256"] == sha(end_raw)
        and end["source_main"] == PREVIOUS_MAIN
        and end["confirmed_prestandby_stop"]["producer_program_invocations"] == 0
        and end["confirmed_prestandby_stop"]["producer_native_dispatches"] == 0
        and end["accepted_count"] == 0
        and end["certificate_exit"] is None
        and end["lease"] == "NOT_ACQUIRED"
        and end["named_formal_cost"]["formal_known_FULL"] == 0
        and ledger["cumulative_known_lower_bound_FULL"] == 414459
        and ledger["historical_HELD"] == 7,
        "predecessor stop or final ledger differs",
    )
    index_raw = pair(PREVIOUS, "formal-a1-index.json")
    packed = archive.pair(PREVIOUS, "formal-a1-controls.tar.gz")
    index = parse(index_raw)
    need(
        sha(packed) == end["archive_sha256"] == PREVIOUS_ARCHIVE
        and sha(index_raw) == end["index_sha256"] == PREVIOUS_INDEX
        and len(index) == 21,
        "wrong predecessor control archive",
    )
    files = contents(packed, {k: v["sha256"] for k, v in index.items()})
    need(
        all(len(b) == index[k]["bytes"] for k, b in files.items()),
        "predecessor file length differs",
    )
    report_raw = files["caller/readiness-release.json"]
    release_actual = files["caller/readiness-release-actual.json"]
    oldentry = parse(pair(PREVIOUS, "readiness-verification-3-entry.json"))
    _, _, stdout = terminal(
        parse(release_actual),
        [
            "/usr/bin/timeout",
            "-k",
            "2",
            "290",
            PYTHON,
            "-I",
            str(PREVIOUS_REPO / "scripts/readiness_release_verify.py"),
            "verify",
            "3",
        ],
        author=AUTHOR,
        cwd=str(PREVIOUS_REPO),
        window=(oldentry["start_ms"], oldentry["end_ms"]),
    )
    need(
        sha(report_raw) == PREVIOUS_REPORT
        and sha(release_actual) == PREVIOUS_ACTUAL
        and parse(report_raw)["source_main"] == PREVIOUS_MAIN
        and stdout == canonical(dict(report_sha256=PREVIOUS_REPORT, slot=3, status=STATUS)),
        "original predecessor release return differs",
    )
    independent = parse(files["caller/independent-outer-original.json"])
    first, last = independent["raw"]
    argv = [
        PYTHON,
        "-I",
        str(PREVIOUS_REPO / "scripts/readiness_formal_filer.py"),
        "enter-independent",
        "--root",
        "/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-readiness-20261126-a1",
    ]
    from staged_input_filer import literal_command

    raw = files["caller/input-preflight-actual-a1.json"]
    original = parse(raw)
    ready = files["caller/input-activation-readiness-a1.json"]
    argv0 = [
        PYTHON,
        "-I",
        str(PREVIOUS_REPO / "scripts/readiness_formal_registered.py"),
        "preflight",
        "--readiness-sha",
        sha(ready),
    ]
    _, preflight_ms, stdout = terminal(
        original,
        argv0,
        cwd=str(PREVIOUS_REPO),
        author=AUTHOR,
        window=(1795691334211, 1795950534211),
        full=None,
    )
    checked = parse(stdout)
    need(
        raw != canonical(original)
        and checked["readiness_sha256"] == sha(ready)
        and checked["status"] == "PASS_REGISTERED_INPUT_METADATA_PREFLIGHT"
        and preflight_ms <= first["requested_ms"]
        and first["tool"] == last["tool"] == "exec_command"
        and first["arguments"]["cmd"] == literal_command(argv)
        and first["result"]["exit_code"] == 1
        and "canonical complete metadata required" in first["result"]["output"]
        and last["result"]["exit_code"] == 0
        and independent["status"] == "STOP_RETAINED_NO_RETRY"
        and not independent["observed"]
        and not independent["secondary"],
        "predecessor noncanonical original or first failure differs",
    )
    emitter = parse(pair(PREVIOUS, "formal-observation-emit-independent.json"))
    program = files["caller/readiness-formal-independent-program.json"]
    artifact = parse(program)
    _, emit_end, _ = command_for_prior_emitter(emitter, artifact, sha(program))
    need(
        preflight_ms <= emit_end <= first["requested_ms"]
        and artifact["config"]["preflight_actual_sha256"] == sha(raw),
        "previous emitter did not admit the same original",
    )
    return parse(report_raw)["prerequisites"], dict(
        ledger_sha256=PREVIOUS_LEDGER,
        archive_sha256=PREVIOUS_ARCHIVE,
        index_sha256=PREVIOUS_INDEX,
        release_actual_sha256=PREVIOUS_ACTUAL,
        release_report_sha256=PREVIOUS_REPORT,
        preflight_original_sha256=sha(raw),
        canonical_preflight_sha256=sha(canonical(original)),
        entry_failure_stdout_sha256=sha(first["result"]["output"].encode()),
        formal_entered=1,
        native_roles=0,
        formal_FULL=0,
    )


def command_for_prior_emitter(packet, artifact, digest):
    import json

    path = (
        PREVIOUS.with_name(PREVIOUS.name + "-formal") / "readiness-formal-independent-program.json"
    )
    argv = [
        PYTHON,
        "-I",
        str(PREVIOUS_REPO / "scripts/build_staged_input_caller.py"),
        "--readiness",
        "--emit",
        str(path),
        "--artifact-sha256",
        digest,
    ]
    raw = "".join(row["result"]["output"] for row in packet["responses"]).encode()
    need(
        raw == (json.dumps(artifact, separators=(",", ":")) + "\n").encode()
        and sha(artifact["program"].encode()) == artifact["program_sha256"],
        "archived predecessor emitter stdout differs from the frozen program",
    )
    rows = [dict(r, result=dict(r["result"], output="")) for r in packet["responses"]]
    return terminal(
        dict(packet, responses=rows),
        argv,
        author="/root",
        cwd=str(PREVIOUS_REPO),
        window=(1795691334211, 1795950534211),
        full=None,
    )


def prerequisites(policy, tree, *, candidate=False):
    import formal_input_independent as rehearsal
    import readiness_release_proof as before

    accepted, stop = predecessor()
    old_raw = (REPO / "docs/planning/readiness_formal_contract.json").read_bytes()
    need(
        sha(old_raw) == "6ef45d08ea73ea24ad2a47f010b1eb4d5357d2bfccb615753ebe0ecf66ae4aa2",
        "historical authority changed",
    )
    repeated = before.prerequisites(parse(old_raw), tree)
    prior = policy["prior_public"]
    directory = PREVIOUS.with_name(PREVIOUS.name + "-formal") if candidate else FORMAL
    need(
        prior == rehearsal.expected_prior(FORMAL)
        and rehearsal.verify_prior_public(
            prior,
            pair(directory, "prior-public-bundle.json"),
            pair(directory, "prior-public-certificate-actual.json"),
        )
        == accepted["public"]
        == repeated["public"]
        and repeated["registration"] == accepted["registration"]
        and repeated["closeouts"] == accepted["closeouts"]
        and repeated["historical_archive_sha256"] == accepted["historical_archive_sha256"]
        and all(
            repeated["certificate"][k] == accepted["certificate"][k]
            for k in (
                "plan_sha256",
                "version_id",
                "member_count",
                "status",
                "source_input_accepted",
            )
        )
        and policy["registration"]["formal"] == parse(old_raw)["registration"]["formal"],
        "new verifier changed historical registration, public closeouts or certificate replay",
    )
    return dict(repeated, predecessor_stop=stop)


def verify(slot, *, candidate=False):
    import p17_m2_input_continuation as profiles
    import staged_input_filer as wire

    policy = profiles.profile("registered", profiles.RECEIPT_FORMAL).authority()
    tree = profiles.profile("control", profiles.RECEIPT_FORMAL).source_freeze(IDENTITY)
    check_policy(policy)
    entry, pin = reservation(slot, policy, tree, candidate=candidate)

    def git(*words):
        return subprocess.check_output(["git", *words], cwd=REPO, timeout=15).decode().strip()

    main = checkout_commit(REPO)
    need(
        sys.flags.isolated
        and sys.executable == PYTHON
        and Path.cwd() == REPO
        and entry["source_tree"] == git("rev-parse", "HEAD^{tree}")
        and (
            (
                git("branch", "--show-current") == "fix/independent-receipt-admission"
                and git("merge-base", main, entry["public_source_main"])
                == entry["public_source_main"]
            )
            if candidate
            else (
                main == git("rev-parse", "origin/main")
                and git("branch", "--show-current") == "main"
            )
        )
        and not git("status", "--porcelain", "-uall")
        and entry["start_ms"] <= time.time_ns() // 1_000_000 <= entry["end_ms"],
        "verification requires the clean released checkout inside its reserved window",
    )
    public = verify_public(
        entry["public_slots"], DATA, REPO, entry["public_source_main"], tree, BUDGET
    )
    need(public["last_returned_ms"] <= entry["start_ms"], "public gate after release reservation")
    facts = prerequisites(policy, tree, candidate=candidate)
    import full60_input_loader as loader

    executed = {}
    required = (
        WORKER,
        LAUNCHER,
        "scripts/receipt_release_fixtures.py",
        "scripts/readiness_release_fixtures.py",
        "scripts/readiness_release_proof.py",
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
    status = CANDIDATE_STATUS if candidate else STATUS
    report = dict(
        status=status,
        purpose=entry["purpose"],
        release_authority=not candidate,
        public_source_main=entry["public_source_main"],
        git_tree=entry["source_tree"],
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
    parent = DATA if candidate else FORMAL
    name = (
        f"receipt-candidate-slot-{slot}.json"
        if candidate
        else f"readiness-release-slot-{slot}.json"
    )
    for directory in (parent, parent.with_name(parent.name + "-backup")):
        wire.write_private(directory / name, raw)
    need(pair(parent, name) == raw, "new proof report did not close in both locations")
    return dict(status=status, slot=slot, report_sha256=sha(raw))


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
        and report["release_authority"] is True
        and report["purpose"] == entry["purpose"] == "RELEASED_PROOF"
        and report["git_tree"] == entry["source_tree"]
        and report["public_source_main"] == report["source_main"]
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
