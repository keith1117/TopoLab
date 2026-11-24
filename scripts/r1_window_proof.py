"""Replay sealed public native R1 returns before the single formal timing attempt."""

import argparse
import hashlib
import json
import re
import resource
import subprocess
import sys
import tarfile
import time
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REPO = Path("/private/tmp/topolab-r1-window-20261123")
DATA = Path("/Users/keith1117/Documents/TopoLab-data/formal-r1-window-20261123")
FORMAL = Path(str(DATA) + "-formal")
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.r1-window-20261123.v1"
PUBLIC_ID = "topolab.v2.p17-m2-registered-source-acquisition.r1-window-public-20261123.v1"
PROTOCOL = "docs/planning/r1_window_formal_contract.json"
WORKER = "scripts/r1_window_proof.py"
PACKAGE = "public-r1-window-verification.json"
ACTUAL = "public-r1-window-verification-actual.json"
PYTHON = (
    "/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python"
)
BUDGET = "d867948e0cf23b8a860a230be66fbedfc3c7cb5398168dada7fa71199fc2a35e"
AUTHOR = "/root/full60_independent"
START, END = 1795476230895, 1795670630895
ROLES = (
    "independent-public-check",
    "exporter-r0",
    "independent-r0",
    "exporter-r1",
    "independent-r1",
)
SUCCESS = "PASS_TWO_FULL_SCALE_PUBLIC_R1_BINDING_RETURNS"
MODULE_SOURCE_SHA256 = None
LAUNCHER = "scripts/r1_window_verify.py"
AUDIT_SOFTWARE = (
    WORKER,
    LAUNCHER,
    "scripts/full60_input_loader.py",
    "scripts/staged_input_filer.py",
    "scripts/r0_read_independent.py",
    "scripts/r0_caller_receipt.py",
    "scripts/p17_m2_source_acquisition_independent.py",
    "scripts/p17_m2_content_verified_independent.py",
)


def compiled(tree, *, verification):
    loader = sys.modules["full60_input_loader"]
    observed = loader.loaded_source_sha256
    names = (
        AUDIT_SOFTWARE
        if verification
        else (WORKER, "scripts/staged_input_filer.py", "scripts/r0_read_independent.py")
    )
    for name in names:
        actual = observed.get(str(BASE / name))
        if name == WORKER and actual is None:
            actual = MODULE_SOURCE_SHA256
        require(
            actual == tree[name] and actual == digest((BASE / name).read_bytes()),
            "executed source buffer differs: " + name,
        )
    return {name: tree[name] for name in names}


def require(value, reason):
    if not value:
        raise ValueError("R1_WINDOW_PROOF: " + reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def wire():
    import staged_input_filer

    return staged_input_filer


def pair(folder, name, limit=16 * 1024**2):
    primary = folder / name
    peer = Path(str(folder) + "-backup") / name
    raw = wire().read_private(primary, limit)
    require(
        not primary.samefile(peer) and wire().read_private(peer, limit) == raw,
        "paired metadata differs",
    )
    return raw


def public_run(slot):
    require(type(slot) is int and 1 <= slot <= 6, "unregistered fixture")
    prefix = f"public-a{slot}-"
    terminal = json.loads(pair(DATA, prefix + "terminal.json"))
    require(
        terminal["accepted"] == list(ROLES) and "native_stop" not in terminal,
        "incomplete public graph",
    )
    raw_index = pair(DATA, prefix + "index.json")
    require(digest(raw_index) == terminal["index_sha256"], "archive index differs")
    index = json.loads(raw_index)
    archive = pair(DATA, prefix + "controls.tar.gz", 128 * 1024**2)
    require(digest(archive) == terminal["archive_sha256"], "archive hash differs")
    import io

    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        members = tar.getmembers()
        require(
            len(members) == len(index) <= 512
            and all(m.isfile() for m in members)
            and {m.name for m in members} == set(index)
            and sum(m.size for m in members) <= 128 * 1024**2,
            "archive member inventory differs",
        )

        def buffer(name):
            data = tar.extractfile(name).read()
            require(index[name] == dict(bytes=len(data), sha256=digest(data)), "member hash")
            return data

        def read(name):
            return json.loads(buffer(name))

        plan = read("native/plan.json")
        root = f"/private/tmp/topolab-public-r1-window-20261123-a{slot}"
        plan_sha = index["native/plan.json"]["sha256"]
        require(
            plan["root"] == root
            and plan["execution_identity"] == PUBLIC_ID
            and plan["formal_authority"] is False,
            "archived scope/plan differs",
        )
        programs = {
            a: read("caller/r1-window-" + a + "-program.json") for a in ("producer", "independent")
        }
        program_hashes = {digest(v["program"].encode()) for v in programs.values()}
        require(
            len(program_hashes) == 1
            and all(
                v["program_sha256"] in program_hashes
                and v["config"]["root"] == root
                and v["config"]["author"] == a
                and v["actor_sha256"] == plan["source_tree"]["scripts/staged_input_actor.mjs"]
                for a, v in programs.items()
            ),
            "same actual public driver required",
        )
        import p17_m2_source_acquisition_independent as independent
        import r0_caller_receipt as projected

        margins = {}
        last_record = plan["whole_start_ms"]
        previous_bind = last_record
        coordination = 0

        for role in ROLES:
            actor = "independent" if role.startswith("independent") else "producer"
            author = AUTHOR if actor == "independent" else "/root"
            accepted = read("native/" + role + "-accepted.json")
            result = accepted["result"]
            folder = f"native/receipts/{role}/{role}/"
            native = read(f"native/receipts/{role}-wire.json")
            record = read(folder + "command.json")
            inner = dict(
                record=record,
                profile=buffer(folder + "command.time"),
                log=buffer(folder + "command.log"),
                helper_profiles=independent.sampler_profile_buffers(
                    buffer(folder + "sampler-evidence.jsonl"), record
                ),
                expected_role=role,
                platform="darwin",
                expected_argv=[
                    PYTHON,
                    "-I",
                    str(REPO / "scripts/r1_window_public_control.py"),
                    "payload",
                    "--root",
                    root,
                    "--plan-sha",
                    plan_sha,
                    "--role",
                    role,
                ],
            )
            events = read("native/" + role + "-events.json")
            audited = independent.native.audit_role(
                native["pending"],
                native["completion"],
                raw_tool_events=events,
                expected_role=role,
                expected_plan_sha256=plan_sha,
                inner_evidence=inner,
                native_profiles={
                    "outer-controller": buffer(f"native/receipts/{role}-controller.time")
                },
                expected_identity=PUBLIC_ID,
                result_seconds=(1800, 1800),
            )
            require(
                audited == result and accepted["raw_tool_events"] == events,
                "native resource audit disagrees with binder",
            )
            if role in ("independent-r0", "independent-r1"):
                domain = read(
                    "native/" + ("r0-proof.json" if role.endswith("r0") else "r1-proof.json")
                )
                require(wire().canonical(domain) == inner["log"], "native domain proof differs")

            require(
                result["evidence_complete"]
                and result["full_role_evidence_accepted"]
                and result["plan_sha256"] == plan_sha
                and result["role"] == role
                and result["actual_exit_codes"] == [0, 0]
                and 0 < result["RSS_envelope_bytes"] <= 4 * 1024**3,
                "unaccepted native role",
            )
            for stage in ("supervise", "record", "bind"):
                stem = f"r1-window-{actor}-{actor}-{role}-{stage}-actual.json"
                packet = read("caller/" + stem)
                argv = [
                    PYTHON,
                    "-I",
                    str(REPO / "scripts/r1_window_public_control.py"),
                    stage,
                    "--root",
                    root,
                    "--plan-sha",
                    plan_sha,
                    "--role",
                    role,
                ]
                first, last, code = wire().validate_terminal(packet, argv, author, str(REPO))
                require(code == 0, "missing successful original")
                stdout = "".join(r["result"]["output"] for r in packet["responses"]).encode()
                if stage == "supervise":
                    start = first
                    require(
                        start >= previous_bind
                        and plan["whole_start_ms"] <= start
                        and (role != ROLES[0] or start - plan["whole_start_ms"] <= 30000)
                        and stdout
                        == wire().canonical(
                            dict(status="PENDING_EXTERNAL_EXIT", controller_exit=0)
                        ),
                        "initial supervisor chronology/output differs",
                    )
                    if role != ROLES[0]:
                        coordination += start - last_record
                        require(coordination <= 240000, "coordination ceiling")
                else:
                    obj = native if stage == "record" else result
                    require(
                        stdout
                        == wire().canonical(
                            projected.project(stage, role, plan_sha, obj, wire().canonical(obj))
                        ),
                        "record or binder original output differs",
                    )
                    if stage == "record":
                        last_record = last
                    else:
                        previous_bind = last
                if stage == "bind":
                    require(last_record <= first <= last <= plan["whole_end_ms"], "late bind")
                    release = read("caller/input-public-" + role + "-caller-release.json")
                    require(
                        release["schema"] == "topolab.staged-input-caller-release.v1"
                        and release["execution_identity"] == PUBLIC_ID
                        and release["root"] == root
                        and release["role"] == role
                        and release["plan_sha256"] == plan_sha
                        and release["bind_actual"]
                        == dict(
                            path=root + "-evidence/" + stem,
                            sha256=index["caller/" + stem]["sha256"],
                        )
                        and release["accepted_sha256"]
                        == index["native/" + role + "-accepted.json"]["sha256"]
                        and release["native_start_ms"] == start
                        and release["native_record_end_ms"] == last_record
                        and release["actual_bind_start_ms"] == first
                        and release["actual_bind_end_ms"] == last,
                        "native bind release differs",
                    )
                    margins[role] = start + (1200 if role.endswith("r1") else 300) * 1000 - last
                    require(margins[role] >= 10000, "binder missed original role reserve")
                else:
                    event = read("native/" + role + "-" + stage + "-actual-event.json")
                    require(
                        event == events[0 if stage == "supervise" else 1]
                        and round(event["start_seconds"] * 1000) == first
                        and round(event["end_seconds"] * 1000) == last
                        and event["event_id"] == packet["event_id"]
                        and event["raw_packet_sha256"] == index["caller/" + stem]["sha256"],
                        "filed original differs",
                    )
                    spent = read(f"caller/filing-{role}-{stage}-spent.json")
                    intent_name = f"caller/filing-{role}-{stage}-intent.json"
                    intent = read(intent_name)
                    require(
                        spent["event_id"] == intent["event_id"] == event["event_id"]
                        and spent["intent_sha256"] == index[intent_name]["sha256"]
                        and spent["outputs"] == intent["outputs"]
                        and intent["role"] == role
                        and intent["mode"] == stage
                        and intent["author"] == author
                        and intent["root"] == root
                        and intent["execution_identity"] == PUBLIC_ID
                        and intent["packet_sha256"] == index["caller/" + stem]["sha256"]
                        and intent["program_sha256"] == programs[actor]["program_sha256"]
                        and intent["plan_sha256"] == plan_sha,
                        "single-use filing missing",
                    )
        rows = read("native/r1-source-rows.json")
        closed = read("native/closed.json")
        r0 = read("native/r0-proof.json")
        proof = read("native/r1-proof.json")
        count = sum(row["byte_size"] for row in rows)
        output = sum(row["byte_size"] for row in closed["manifest"]["members"])
        require(
            len(read("native/r0-source-rows.json")) == r0["source_count"] == 40
            and len(rows) == len({r["path"] for r in rows}) == proof["source_count"] == 558
            and count == proof["source_bytes"]
            and abs(count - 567896449) <= 567896449 * 0.05
            and abs(output - 91214092) <= 91214092 * 0.05
            and closed["version_id"]
            == proof["version_id"]
            == digest(wire().canonical(closed["manifest"]))
            and len({r["path"] for r in closed["manifest"]["members"]})
            == proof["new_member_reads"]
            == 1071
            and all(r["expected_sha256"] == r["sha256"] for r in rows + proof["source_rows"]),
            "same-scale source rows or independent version mismatch",
        )
    return dict(
        slot=slot,
        receipt_sha256=terminal["archive_sha256"],
        source_bytes=count,
        output_bytes=output,
        version_id=proof["version_id"],
        binder_remaining_ms=margins,
        source_tree=plan["source_tree"],
        driver_sha256=program_hashes.pop(),
    )


def gate_args(slots):
    return [
        "/usr/bin/timeout",
        "-k",
        "2",
        "290",
        PYTHON,
        "-I",
        str(REPO / LAUNCHER),
        "verify",
        *map(str, slots),
    ]


def local_candidate(tree, main):
    require(bool(re.fullmatch("[a-f0-9]{40}", main)), "invalid main")
    import p17_m2_input_continuation as profiles

    control = profiles.profile("control", profiles.WINDOW_PUBLIC)
    require(tree == control.source_freeze(PUBLIC_ID), "published public execution closure differs")


def verify(slots):
    require(
        sys.flags.isolated and BASE == Path.cwd() == REPO and sys.executable == PYTHON,
        "isolated published runtime required",
    )
    require(len(slots) == len(set(slots)) == 2, "two distinct public graphs required")

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=REPO, timeout=20).decode().strip()

    main = git("rev-parse", "HEAD")
    require(
        main == git("rev-parse", "origin/main")
        and git("branch", "--show-current") == "main"
        and not git("status", "--porcelain", "-uall"),
        "clean protected checkout required",
    )
    runs = [public_run(slot) for slot in slots]
    require(
        runs[0]["source_tree"] == runs[1]["source_tree"]
        and runs[0]["driver_sha256"] == runs[1]["driver_sha256"],
        "candidate differs",
    )
    import r0_read_independent  # noqa: F401 - bind the return verifier used at admission

    actual_software = compiled(runs[0]["source_tree"], verification=True)
    local_candidate(runs[0]["source_tree"], main)
    require(
        sys.platform == "darwin"
        and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 4 * 1024**3,
        "independent verification RSS cap",
    )
    value = dict(
        status=SUCCESS,
        source_main=main,
        execution_identity=IDENTITY,
        runs=runs,
        worker_sha256=actual_software[WORKER],
        executed=actual_software,
        authority_sha256=digest((BASE / PROTOCOL).read_bytes()),
        budget_sha256=BUDGET,
    )
    raw = wire().canonical(value)
    for directory in (FORMAL, Path(str(FORMAL) + "-backup")):
        wire().write_private(directory / PACKAGE, raw)
    return dict(status=SUCCESS, report_sha256=digest(raw))


def verified_readiness(policy, tree):
    import r0_read_independent as original

    require(
        policy["execution_identity"] == IDENTITY
        and policy["new_input_budget"] == dict(path=str(DATA / "owner-budget.json"), sha256=BUDGET)
        and digest(pair(DATA, "owner-budget.json")) == BUDGET,
        "wrong timing budget or contract",
    )
    raw, actual_raw = pair(FORMAL, PACKAGE), pair(FORMAL, ACTUAL)
    require(
        policy["r1_window_verification_paths"]
        == {"package": str(FORMAL / PACKAGE), "actual": str(FORMAL / ACTUAL)},
        "timing proof paths differ",
    )
    report, actual = json.loads(raw), json.loads(actual_raw)
    runs = report["runs"]
    slots = [r["slot"] for r in runs]
    require(
        len(runs) == len(set(slots)) == 2 and all(type(s) is int and 1 <= s <= 6 for s in slots),
        "two distinct public timing observations required",
    )
    first, last, output = original.terminal(
        actual, gate_args(slots), author=AUTHOR, cwd=str(REPO), window=(START, END), full=300
    )
    require(
        output == wire().canonical(dict(status=SUCCESS, report_sha256=digest(raw)))
        and report["status"] == SUCCESS
        and report["execution_identity"] == IDENTITY
        and report["budget_sha256"] == BUDGET
        and report["worker_sha256"] == tree[WORKER]
        and report["authority_sha256"] == tree[PROTOCOL]
        and runs[0]["source_tree"] == runs[1]["source_tree"]
        and runs[0]["driver_sha256"] == runs[1]["driver_sha256"]
        and first <= last <= time.time_ns() // 10**6,
        "independent verification differs",
    )
    require(
        report["executed"] == {name: tree[name] for name in AUDIT_SOFTWARE},
        "archived executed software differs",
    )
    compiled(tree, verification=False)
    local_candidate(runs[0]["source_tree"], report["source_main"])
    return dict(
        source_main=report["source_main"],
        verified_returned_ms=last,
        package=dict(path=str(FORMAL / PACKAGE), sha256=digest(raw)),
        actual=dict(path=str(FORMAL / ACTUAL), sha256=digest(actual_raw)),
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["verify"])
    parser.add_argument("slots", type=int, nargs=2)
    args = parser.parse_args()
    print(wire().canonical(verify(args.slots)).decode(), end="")
