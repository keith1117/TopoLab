"""Verify old and current public writer, scheduler and entry observations."""

import subprocess
from pathlib import Path

from certificate_replay_proof import PYTHON
from child_readiness_proof import pair
from r0_read_independent import canonical, need, parse, sha
from readiness_release_fixtures import (
    CALLBACK,
    OBSERVER,
    PREPARED,
    READY,
    command,
    contents,
    sealed_pair,
)

CASES = ("positive", "noncanonical", "missing", "changed", "stale", "partial", "stale-preflight")
ORIGINAL = "input-preflight-original-a1.json"
ACTUAL = "input-preflight-actual-a1.json"
BASE = "07abc057df5bd81ef255efd1c96d1fc66fe41f92"
OLD_RECEIVER = "f6f33cb9a30f5c9f12624e74d45f41897ff696863afd23ccb535f24f5d0fb8c3"
ADAPTER = "aa4f7bdfdbededc4393cc53f1005a3b53e476eec4251f47a9ed98de1c7c20461"
COORDINATOR = "a5bd8bcba73953e5017bedb714707c779741ac6c9608b294343c87cc7d4b5532"
BASELINE_SLOT = 2
BASELINE_ENTRY = "d516a33a1d490322629f7650827c4668f6dec868f18e99c0972cb2243848a932"
BASELINE_RESULT = "7fc4468808318ce1d2d455e6d53564c2a9c22e85f73fc27faa95bcb71012cbfa"
MEASURED = {
    "scripts/" + n
    for n in (
        "staged_input_preparation.py",
        "p17_m2_registered_input.py",
        "cycle_filing_intent.py",
        "staged_input_actor.mjs",
        "build_staged_input_caller.py",
        "staged_input_filer.py",
        "formal_input_route.py",
        "p17_m2_source_binding_recovery.py",
        "p17_m2_source_binding.py",
        "p17_m2_input_export.py",
        "p17_m2_content_verified_control.py",
        "paired_readiness_independent.py",
        "p17_m2_source_acquisition_independent.py",
        "r0_read_independent.py",
        "certificate_replay_proof.py",
    )
}
CURRENT = MEASURED | {
    "scripts/" + n
    for n in (
        "independent_preflight_custody.py",
        "receipt_formal_registered.py",
        "receipt_formal_preparation.py",
        "receipt_formal_filer.py",
    )
}


def cases(slots):
    need(
        type(slots) is list
        and len(slots) == len(set(slots)) == len(CASES)
        and slots == sorted(slots)
        and all(type(n) is int and BASELINE_SLOT < n <= 24 for n in slots),
        "seven ordered distinct candidate/released public fixtures required",
    )
    return zip(slots, CASES, strict=True)


def exits(case):
    invalid_ready = case in ("missing", "changed", "partial", "stale")
    valid_emit = case in ("legacy-envelope", "positive")
    stages = {"retain": 0, "readiness": int(case == "partial"), "preflight": int(invalid_ready)}
    if case == "legacy-envelope":
        stages["legacy-custody"] = 0
    elif not invalid_ready:
        stages["custody"] = 0
    stages.update({"freeze-program": 0, "emit-program": int(not valid_emit)})
    if valid_emit:
        stages["enter-independent"] = int(case == "legacy-envelope")
    return stages


def argv_for(stage, root, legacy, ready_sha, observed_sha):
    prefix = "readiness_formal" if legacy else "receipt_formal"
    driver = {
        "retain": prefix + "_preparation.py",
        "readiness": prefix + "_preparation.py",
        "preflight": prefix + "_registered.py",
        "legacy-custody": "legacy_receiver_cli.py",
        "custody": "independent_preflight_custody.py",
        "freeze-program": "build_staged_input_caller.py",
        "emit-program": "build_staged_input_caller.py",
        "enter-independent": prefix + "_filer.py",
    }[stage]
    args = ["--original-sha256", observed_sha] if stage == "custody" else [stage]
    if stage == "preflight":
        args += ["--readiness-sha", ready_sha]
    return [PYTHON, "-I", str(root / "checkout/scripts" / driver), *args]


def physical(raw, rows, roots, filename):
    need(
        type(rows) is list
        and len(rows) == 2
        and [r["path"] for r in rows] == [str(root / filename) for root in roots]
        and all(
            r["sha256"] == sha(raw)
            and r["st_size"] == len(raw)
            and r["st_mode"] == 0o100600
            and r["st_nlink"] == 1
            and all(type(r[k]) is int for k in ("st_uid", "st_dev", "st_ino", "st_mtime_ns"))
            for r in rows
        )
        and rows[0]["st_uid"] == rows[1]["st_uid"]
        and len({(r["st_dev"], r["st_ino"]) for r in rows}) == 2,
        "public physical receipt or separate file identity differs",
    )


def gate_observations(case, files, root, head, artifact, outputs, source):
    raw, actual = files["evidence/" + READY], sealed_pair(files, ACTUAL)
    peer = files.get("evidence-backup/" + READY)
    observed = files["preflight-original-js.json"]
    original = parse(observed)
    roots = [root / k for k in ("evidence", "evidence-backup")]
    valid_preflight = exits(case)["preflight"] == 0
    need(
        canonical(original) != observed
        and artifact["program_sha256"] == sha(artifact["program"].encode())
        and artifact["config"]["preflight_actual_sha256"] == sha(actual)
        and artifact["config"]["readiness_sha256"] == sha(raw)
        and parse(outputs["freeze-program"])["program_sha256"] == artifact["program_sha256"],
        "public original serialization or emitted artifact differs",
    )
    if valid_preflight:
        check = parse(outputs["preflight"])
        copies = parse(outputs["readiness"])["readiness_copies"]
        physical(raw, copies, roots, READY)
        need(
            peer == raw
            and check["status"] == "PASS_REGISTERED_INPUT_METADATA_PREFLIGHT"
            and check["paired_readiness"]["readiness_copies"] == copies
            and check["readiness_sha256"] == sha(raw)
            and check["paired_readiness"]["source_main"] == head
            and check["paired_readiness"]["target"] == str(root / "target"),
            "original preflight or readiness pair differs",
        )
    if case == "legacy-envelope":
        need(
            sha(files["legacy-receiver.py"]) == OLD_RECEIVER
            and actual == observed
            and b"canonical complete metadata required" in outputs["enter-independent"]
            and "evidence/fixture-independent-filing-entry.json" not in files,
            "legacy receiver did not expose the original false pass before entry",
        )
    else:
        obsdirs = [root / n for n in ("observation", "observation-backup")]
        need(
            files["observation/" + ORIGINAL] == files["observation-backup/" + ORIGINAL] == observed,
            "observer's untouched original differs",
        )
        if valid_preflight:
            kept = parse(outputs["custody"])
            need(
                kept["status"] == "CANONICAL_PREFLIGHT_AND_ORIGINAL_RETAINED"
                and kept["original_sha256"] == sha(observed)
                and kept["canonical_sha256"] == sha(canonical(original))
                and sealed_pair(files, ORIGINAL) == observed,
                "real custody return differs",
            )
            physical(observed, kept["observation_copies"], obsdirs, ORIGINAL)
            physical(observed, kept["original_copies"], roots, ORIGINAL)
            physical(canonical(original), kept["canonical_copies"], roots, ACTUAL)
        if case == "positive":
            entry = parse(sealed_pair(files, "fixture-independent-filing-entry.json"))
            need(
                actual == canonical(original)
                and parse(outputs["enter-independent"])
                == dict(
                    program_sha256=artifact["program_sha256"], status="INDEPENDENT_ACTOR_ENTERED"
                )
                and entry["preflight_sha256"] == sha(actual)
                and entry["readiness_sha256"] == sha(raw),
                "new canonical writer did not enter through the full public pathway",
            )
        else:
            need(
                "evidence/fixture-independent-filing-entry.json" not in files
                and "evidence-backup/fixture-independent-filing-entry.json" not in files,
                "negative public control produced an entry",
            )
            planted = parse(files["intentional-replay.json"])
            need(planted["sha256"] == sha(actual), "wrong public injection digest")
            if case in ("noncanonical", "stale-preflight"):
                need(
                    files["evidence-original-current-canonical.json"]
                    == files["evidence-backup-original-current-canonical.json"]
                    == canonical(original),
                    "intact pre-mutation canonical evidence differs",
                )
            if case == "noncanonical":
                need(
                    actual == observed
                    and b"canonical complete metadata required" in outputs["emit-program"],
                    "actual emitter did not reject the reversed original serialization",
                )
            else:
                need(
                    actual == source["actual"],
                    "negative case did not replay the prior positive receipt",
                )
            if case == "missing":
                need(
                    peer is None
                    and files["intentionally-missing-ready"] == raw
                    and b"FileNotFoundError" in outputs["preflight"],
                    "missing backup not exercised",
                )
            if case == "changed":
                need(
                    peer is not None
                    and len(raw) == len(peer)
                    and sum(a != b for a, b in zip(raw, peer, strict=True)) == 1
                    and b"readiness control copies differ" in outputs["preflight"],
                    "one-byte change not exercised",
                )
            if case == "stale":
                need(
                    raw == peer == source["ready"]
                    and parse(raw)["target"] != str(root / "target")
                    and b"readiness contract/target/release binding differs"
                    in outputs["preflight"],
                    "old intact pair was not injected",
                )
            if case == "partial":
                need(
                    peer is None
                    and b"FileExistsError" in outputs["readiness"]
                    and all(
                        folder + "/" + PREPARED not in files
                        for folder in ("evidence", "evidence-backup")
                    ),
                    "second write failure was not retained",
                )
            if case == "stale-preflight":
                need(
                    actual != canonical(original) and source["actual"] == actual,
                    "old canonical preflight was not injected",
                )
    expected_callbacks = {"emit-program"} | ({"enter-independent"} if case == "positive" else set())
    callbacks = {n for n in files if n.startswith("audit-callback-")}
    need(
        callbacks == {f"audit-callback-{s}.jsonl" for s in expected_callbacks}
        and all(files[n] == CALLBACK for n in callbacks),
        "actual gate invocations differ",
    )
    return dict(ready=raw, actual=actual)


def run(slot, case, data, repo, head, tree, budget, previous_end, source):
    prefix = f"public-{slot:02d}-"
    root = Path(f"/private/tmp/topolab-public-receipt-20261126-slot{slot:02d}")
    work = root / "checkout"
    entry_raw, result_raw = pair(data, prefix + "entry.json"), pair(data, prefix + "result.json")
    entry, result = parse(entry_raw), parse(result_raw)
    legacy = case == "legacy-envelope"
    if legacy:
        need(
            sha(entry_raw) == BASELINE_ENTRY
            and sha(result_raw) == BASELINE_RESULT
            and entry["repo"] == "/private/tmp/topolab-readiness-20261126",
            "old public evidence differs",
        )
    else:
        need(entry["repo"] == str(repo), "public source checkout differs")
    need(
        entry["head"] == result["source_main"] == head
        and entry["root"] == str(root)
        and entry["command_cwd"] == str(work)
        and entry["case"] == result["case"] == case
        and entry["slot"] == result["slot"] == slot
        and entry["budget_sha256"] == budget
        and entry["reserved_FULL"] == entry["booked_FULL"] == result["retained_FULL"] == 600
        and previous_end
        <= entry["clock_ms"]
        == result["start_ms"]
        <= result["end_ms"]
        <= result["start_ms"] + 780000
        and entry["max_seconds"] == 780
        and result["source_entry"] == sha(entry_raw)
        and result["same_source_at_close"] is True
        and result["outcome"] == "EXPECTED_PUBLIC_OBSERVATION"
        and result["observer_actor"] == OBSERVER
        and result["formal_dispatches"] == result["native_dispatch_attempts"] == 0,
        "public control identity, budget or scheduled window differs",
    )
    driver_sha = entry["adapter_sha256"] if legacy else ADAPTER
    coordinator_sha = entry["coordinator_sha256"] if legacy else COORDINATOR
    for key, digest in (("adapter", driver_sha), ("coordinator", coordinator_sha)):
        need(
            entry[key + "_sha256"] == digest == sha(pair(data, prefix + key + ".source.py")),
            "public driver source differs",
        )
    keys = MEASURED if legacy else CURRENT
    pins = {
        n: sha(subprocess.check_output(["git", "show", BASE + ":" + n], cwd=repo, timeout=15))
        if legacy
        else tree[n]
        for n in keys
    }
    need(
        pins == entry["input_sha256"] == result["actual_source_hashes_after"],
        "actual fixture source differs",
    )
    archive = pair(data, prefix + "controls.tar.gz")
    need(
        result["archive_filename"] == prefix + "controls.tar.gz"
        and sha(archive) == result["archive_sha256"],
        "public archive changed",
    )
    files = contents(archive, result["evidence_files"])
    need(
        sha(files["fixture_driver.py"]) == driver_sha
        and sha(files["legacy-receiver.py"]) == OLD_RECEIVER
        and not any(n.startswith("unexpected-dispatch") for n in files),
        "unexpected dispatch or public driver",
    )
    expected = exits(case)
    need(
        result["exits"] == result["case_expected_exits"] == expected
        and set(result["complete_packet_sha256"]) == {prefix + s + "-actual.json" for s in expected}
        and result["complete_program_emitted"] == (expected["emit-program"] == 0),
        "public original stages or terminal exits differ",
    )
    artifact = parse(sealed_pair(files, "fixture-independent-program.json"))
    end = result["start_ms"]
    outputs = {}
    for stage, code in expected.items():
        filename = prefix + stage + "-actual.json"
        raw = pair(data, filename)
        need(sha(raw) == result["complete_packet_sha256"][filename], "public original changed")
        argv = argv_for(
            stage,
            root,
            legacy,
            sha(files["evidence/" + READY]),
            sha(files["preflight-original-js.json"]),
        )
        need(
            sha(files["checkout/scripts/" + Path(argv[2]).name]) == driver_sha,
            "dispatched adapter bytes differ",
        )
        pkt = parse(raw)
        first, last, outputs[stage] = command(
            pkt,
            argv,
            work,
            code,
            emitted=artifact if stage == "emit-program" and code == 0 else None,
        )
        need(end <= first <= last <= result["end_ms"], "original public chronology differs")
        end = last
        if stage == "readiness" and code == 0:
            need(raw == sealed_pair(files, PREPARED), "preparation original changed")
        if stage == "preflight":
            need(
                pkt == parse(files["preflight-original-js.json"]),
                "public raw original fields changed",
            )
    captured = gate_observations(case, files, root, head, artifact, outputs, source)
    return (
        dict(
            slot=slot,
            case=case,
            source_main=head,
            entry_sha256=sha(entry_raw),
            result_sha256=sha(result_raw),
            archive_sha256=sha(archive),
        ),
        captured,
        result["end_ms"],
    )


def verify(slots, data, repo, main, tree, budget):
    old, _, end = run(BASELINE_SLOT, "legacy-envelope", data, repo, BASE, tree, budget, 0, {})
    reports, source = [], {}
    for slot, case in cases(slots):
        row, captured, end = run(slot, case, data, repo, main, tree, budget, end, source)
        if case == "positive":
            source = captured
        reports.append(row)
    return dict(baseline=old, fixtures=reports, last_returned_ms=end)
