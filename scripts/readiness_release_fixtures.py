"""Verify original readiness and emitter returns on six independently reserved public fixtures."""

import io
import json
import tarfile
from pathlib import Path

from certificate_replay_proof import PYTHON
from child_readiness_proof import pair
from r0_read_independent import need, parse, sha
from staged_input_filer import validate_terminal

CASES = ("positive", "missing", "changed", "stale", "partial", "stale-preflight")
ADAPTER = "f376b55bbdf29c72cad1b83261da2a954aa7524df1c95f4a33c37a5a7f6ce1ce"
COORDINATOR = "8985287cd082d15e444f91a08a732e9cc40ca855bd4faf0bfffd213d6f3e7860"
BASE_ENTRY = "29e9f42e922006be8859453db931fe2f404df93568c26c10fca817234b49dfa2"
BASE_RESULT = "d0c917a5f3ecf278e19a87a0f2a2d6a441ea333bb79e69c33bb825de57b97f37"
OBSERVER = "/root/evidence"
READY = "input-activation-readiness-a1.json"
ACTUAL = "input-preflight-actual-a1.json"
PREPARED = "input-readiness-original-return-a1.json"
CALLBACK = b'{"called":"paired_readiness_independent.audit_dispatch"}\n'


def cases(slots):
    need(
        type(slots) is list
        and len(slots) == len(set(slots)) == len(CASES)
        and all(type(n) is int and 1 < n <= 24 for n in slots)
        and slots == sorted(slots),
        "six ordered distinct public release fixtures required",
    )
    return zip(slots, CASES, strict=True)


def contents(raw, expected):
    need(type(expected) is dict and 1 <= len(expected) <= 128, "bounded public inventory")
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tar:
        items = tar.getmembers()
        need(
            len(items) == len(expected)
            and {i.name for i in items} == set(expected)
            and all(
                i.isfile()
                and 0 < i.size <= 8 * 1024**2
                and not Path(i.name).is_absolute()
                and ".." not in Path(i.name).parts
                for i in items
            )
            and sum(i.size for i in items) <= 16 * 1024**2,
            "public inventory differs",
        )
        files = {i.name: tar.extractfile(i).read() for i in items}
    need({n: sha(b) for n, b in files.items()} == expected, "public archive member hash differs")
    return files


def command(packet, argv, repo, expected_code, *, emitted=None):
    rows = packet["responses"]
    stdout = "".join(r["result"]["output"] for r in rows).encode()
    if emitted is not None:
        # The complete emitted source contains literal truncation-detection strings.
        need(
            parse(stdout) == emitted
            and stdout == (json.dumps(emitted, separators=(",", ":")) + "\n").encode(),
            "actual emitter stdout is incomplete or differs from the frozen program",
        )
        packet = dict(
            packet, responses=[dict(r, result=dict(r["result"], output="")) for r in rows]
        )
    first, last, code = validate_terminal(packet, argv, OBSERVER, str(repo))
    need(code == expected_code, "public command terminal exit differs")
    return first, last, stdout


def expected_exits(case):
    exits = dict(
        retain=0,
        readiness=int(case == "partial"),
        preflight=int(case not in ("positive", "stale-preflight")),
    )
    exits.update({"freeze-program": 0, "emit-program": int(case != "positive")})
    if case == "positive":
        exits["enter-independent"] = 0
    return exits


def sealed_pair(files, name):
    raw = files["evidence/" + name]
    need(raw == files["evidence-backup/" + name], "public archived pair differs: " + name)
    return raw


def observations(case, files, outputs, source, root, positive):
    raw = files["evidence/" + READY]
    peer = files.get("evidence-backup/" + READY)
    ready = parse(raw)
    actual = sealed_pair(files, ACTUAL)
    artifact = parse(sealed_pair(files, "fixture-independent-program.json"))
    need(
        artifact["program_sha256"] == sha(artifact["program"].encode())
        and artifact["config"]["preflight_actual_sha256"] == sha(actual)
        and artifact["config"]["readiness_sha256"] == sha(raw)
        and parse(outputs["freeze-program"])["program_sha256"] == artifact["program_sha256"],
        "public program does not bind the measured documents and original preflight",
    )
    callback = [n for n in files if n.startswith("audit-callback-")]
    stages = ["emit-program", "enter-independent"] if case == "positive" else ["emit-program"]
    need(
        set(callback) == {f"audit-callback-{stage}.jsonl" for stage in stages}
        and all(files[n] == CALLBACK for n in callback),
        "actual release gate invocation differs",
    )
    if case != "positive":
        need(
            actual == positive["preflight"]
            and b"Traceback" in outputs["emit-program"]
            and not any(n.endswith("-filing-entry.json") for n in files),
            "previous actual return advanced an invalid public graph",
        )
    if case not in ("partial", "stale"):
        prepared = parse(outputs["readiness"])
        need(
            prepared["sha256"] == sha(raw) and prepared["path"] == str(root / "evidence" / READY),
            "public original readiness summary has wrong document",
        )
        docs = prepared["readiness_copies"]
        paths = [str(root / name / READY) for name in ("evidence", "evidence-backup")]
        need(
            [d["path"] for d in docs] == ready["readiness_paths"] == paths
            and all(
                d["st_size"] == len(raw)
                and d["sha256"] == sha(raw)
                and d["st_mode"] == 0o100600
                and d["st_nlink"] == 1
                for d in docs
            )
            and len({(d["st_dev"], d["st_ino"]) for d in docs}) == 2,
            "public readiness copies lack separate physical identities",
        )
    if case in ("positive", "stale-preflight"):
        check = parse(outputs["preflight"])
        need(
            raw == peer
            and check["status"] == "PASS_REGISTERED_INPUT_METADATA_PREFLIGHT"
            and check["paired_readiness"]["readiness_copies"]
            == parse(outputs["readiness"])["readiness_copies"]
            and check["paired_readiness"]["source_main"] == source
            and check["paired_readiness"]["target"] == str(root / "target")
            and check["readiness_sha256"] == sha(raw),
            "new independent preflight facts differ",
        )
        if case == "positive":
            entered = parse(sealed_pair(files, "fixture-independent-filing-entry.json"))
            need(
                parse(outputs["enter-independent"])
                == dict(
                    status="INDEPENDENT_ACTOR_ENTERED", program_sha256=artifact["program_sha256"]
                )
                and entered["preflight_sha256"] == sha(actual)
                and entered["readiness_sha256"] == sha(raw),
                "independent entry differs",
            )
        else:
            need(
                actual
                != files["evidence-current-preflight.json"]
                == files["evidence-backup-current-preflight.json"],
                "stale original was not injected",
            )
    elif case == "partial":
        need(
            peer is None
            and b"FileExistsError" in outputs["readiness"]
            and all(
                folder + "/" + PREPARED not in files for folder in ("evidence", "evidence-backup")
            ),
            "partial publication reported success",
        )
    elif case == "missing":
        need(
            peer is None
            and files["removed-public-backup"] == raw
            and b"FileNotFoundError" in outputs["preflight"],
            "missing peer was not exercised",
        )
    elif case == "changed":
        need(
            peer is not None
            and len(raw) == len(peer)
            and sum(a != b for a, b in zip(raw, peer, strict=True)) == 1
            and b"readiness control copies differ" in outputs["preflight"],
            "one-byte peer change was not exercised",
        )
    else:
        need(
            raw == peer == positive["ready"]
            and ready["target"] != str(root / "target")
            and b"readiness contract/target/release binding differs" in outputs["preflight"],
            "same-byte documents from the previous attempt were not exercised",
        )
    return dict(ready=raw, preflight=actual)


def verify(slots, data, repo, main, tree, budget):
    old_entry = pair(data, "public-01-entry.json")
    old_result = pair(data, "public-01-result.json")
    need(
        sha(old_entry) == BASE_ENTRY and sha(old_result) == BASE_RESULT, "old reproduction changed"
    )
    for name, pin in parse(old_result)["complete_packet_sha256"].items():
        need(sha(pair(data, name)) == pin, "old reproduction return changed")
    evidence = []
    positive = {}
    first_allowed = latest = parse(old_result)["end_ms"]
    for slot, case in cases(slots):
        prefix = f"public-{slot:02d}-"
        root = Path(f"/private/tmp/topolab-public-readiness-20261126-slot{slot:02d}")
        entry_raw, result_raw = (
            pair(data, prefix + "entry.json"),
            pair(data, prefix + "result.json"),
        )
        entry, result = parse(entry_raw), parse(result_raw)
        need(
            entry["head"] == result["source_main"] == main
            and entry["repo"] == str(repo)
            and entry["root"] == str(root)
            and entry["case"] == result["case"] == case
            and entry["slot"] == result["slot"] == slot
            and entry["budget_sha256"] == budget
            and entry["reserved_FULL"] == entry["booked_FULL"] == result["retained_FULL"] == 600
            and first_allowed
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
            "release fixture authority/clock/no-dispatch outcome differs",
        )
        for name, pin in (("adapter", ADAPTER), ("coordinator", COORDINATOR)):
            need(
                entry[name + "_sha256"] == pin == sha(pair(data, prefix + name + ".source.py")),
                "public adapter/observer bytes differ",
            )
        need(
            entry["input_sha256"] == result["actual_source_hashes_after"]
            and {
                "scripts/paired_readiness_independent.py",
                "scripts/staged_input_preparation.py",
                "scripts/p17_m2_registered_input.py",
                "scripts/cycle_filing_intent.py",
                "scripts/build_staged_input_caller.py",
            }
            <= set(entry["input_sha256"])
            and all(tree[name] == pin for name, pin in entry["input_sha256"].items()),
            "public fixture used another software release",
        )
        need(
            result["archive_filename"] == prefix + "controls.tar.gz", "public archive name differs"
        )
        archive = pair(data, result["archive_filename"])
        need(sha(archive) == result["archive_sha256"], "public archive hash differs")
        files = contents(archive, result["evidence_files"])
        need(sha(files["fixture_driver.py"]) == ADAPTER, "executed public adapter differs")
        outputs = {}
        expected = expected_exits(case)
        need(
            result["exits"] == result["case_expected_exits"] == expected
            and set(result["complete_packet_sha256"])
            == {prefix + s + "-actual.json" for s in expected}
            and result["complete_program_emitted"] == (case == "positive"),
            "required release commands missing or unexpected",
        )
        end = result["start_ms"]
        for stage, code in expected.items():
            name = prefix + stage + "-actual.json"
            raw = pair(data, name)
            need(sha(raw) == result["complete_packet_sha256"][name], "public original hash differs")
            argv = [PYTHON, "-I", str(root / "fixture_driver.py"), stage]
            if stage == "preflight":
                argv += ["--readiness-sha", sha(files["evidence/" + READY])]
            emitted = (
                parse(sealed_pair(files, "fixture-independent-program.json"))
                if stage == "emit-program" and case == "positive"
                else None
            )
            start, last, outputs[stage] = command(parse(raw), argv, repo, code, emitted=emitted)
            need(end <= start <= last <= result["end_ms"], "public original chronology differs")
            end = last
            if stage == "preflight" and code == 0:
                archived = (
                    files["evidence-current-preflight.json"]
                    if case == "stale-preflight"
                    else sealed_pair(files, ACTUAL)
                )
                need(raw == archived, "public original preflight receipt changed")
            if stage == "readiness" and code == 0:
                need(
                    raw == sealed_pair(files, PREPARED), "public original readiness receipt changed"
                )
        captured = observations(case, files, outputs, main, root, positive)
        if case == "positive":
            positive = captured
            first_allowed = result["end_ms"]
        evidence.append(
            dict(slot=slot, case=case, result_sha256=sha(result_raw), archive_sha256=sha(archive))
        )
        latest = max(latest, result["end_ms"])
    return dict(baseline_result_sha256=BASE_RESULT, fixtures=evidence, last_returned_ms=latest)
