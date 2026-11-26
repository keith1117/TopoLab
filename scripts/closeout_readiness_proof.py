"""Independent replay of complete public closeout and original data-only IPC.

The measured admission API reads retained control/software bytes in process.
Publication and actual verifier scheduling belong to the separate CLI.
"""

import io
import re
import shlex
import sys
import tarfile
import time
from decimal import Decimal
from pathlib import Path

from child_readiness_proof import canonical, pair, parse, sha

REPO = Path("/private/tmp/topolab-closeout-20261125")
DATA = Path("/Users/keith1117/Documents/TopoLab-data/closeout-20261125")
FORMAL = Path(str(DATA) + "-formal")
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.closeout-20261125.v1"
PUBLIC_ID = "topolab.v2.p17-m2-content-verified-input.v1"
PUBLIC_SCOPE = "PUBLIC_SOFTWARE_FIXTURE_ONLY"
PUBLIC_AUTHOR = "/root/closeout_public"
AUTHOR = "/root/full60_independent"
PROTOCOL = "docs/planning/closeout_formal_contract.json"
WORKER = "scripts/closeout_readiness_proof.py"
LAUNCHER = "scripts/closeout_verify.py"
PACKAGE, ACTUAL = "closeout-readiness.json", "closeout-readiness-actual.json"
BUDGET = "9afb732330236b115a42621441c5b5e7d019c05ce02d1154cd14902dde64b577"
PRICING = "6354250da78fe859cbb01bc6dc9c1bee0dff44a8439c702508c6b14e04507d15"
START, DIAGNOSTIC_END, END = 1795659597213, 1795745997213, 1795918797213
PYTHON = (
    "/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python"
)
THREADS = [
    f"{name}=1"
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    )
]
ACTUAL_SCHEMA = "topolab.v2.m2-strict-source-binding.actual-call.v1"
READY = "CLOSEOUT_RECEIPT_READY_V1\n"
TIMING_KEYS = (
    "worker_entered",
    "packet_received",
    "primary_write_verified",
    "backup_write_verified",
    "before_result_write",
)
ROLES = (
    "independent-public-check",
    "exporter-r0",
    "independent-r0",
    "exporter-r1",
    "independent-r1",
    "shared-closeout",
)
CAPS = (300, 300, 300, 1200, 1200, 300)
STATUS = "PASS_RELEASED_FULL_CLOSEOUT_AND_LATE_RETURN_VETO"
SOFTWARE = (
    WORKER,
    LAUNCHER,
    "scripts/child_readiness_proof.py",
    "scripts/certificate_replay_proof.py",
    "scripts/certificate_replay_archive.py",
    "scripts/formal_input_independent.py",
    "scripts/staged_binding_evidence.py",
    "scripts/full60_input_loader.py",
    "scripts/staged_input_filer.py",
    "scripts/r0_read_independent.py",
    "scripts/p17_m2_source_acquisition_independent.py",
    "scripts/p17_m2_content_verified_independent.py",
)
PRODUCTION = (
    "scripts/closeout_receipt.py",
    "scripts/staged_input_actor.mjs",
    "scripts/closeout_public_control.py",
    "scripts/closeout_public_schedule.mjs",
)
MODULE_SOURCE_SHA256 = None


def need(value, reason):
    if not value:
        raise ValueError("CLOSEOUT_READINESS_STOP: " + reason)


def literal(argv):
    return "exec " + shlex.join(["env", *THREADS, *argv])


def integer(value, *, minimum=0):
    return type(value) is int and value >= minimum


def digest(value):
    return type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None


def audit_courier(
    packet, original, *, argv, author, cwd, deadline_ms, expected_paths, delivery_ms=None
):
    """Replay one owned terminal; only its one REC JSON message may be nonempty.

    ``delivery_ms`` is the separately captured downstream transport observation.
    It never replaces any original tool row or its actual terminal clock.
    """
    need(
        integer(deadline_ms, minimum=1)
        and packet.get("schema") == ACTUAL_SCHEMA
        and packet.get("author") == author
        and packet.get("argv") == argv
        and argv[-2:] == ["--deadline-ms", str(deadline_ms)],
        "courier authority differs",
    )
    request = packet.get("request", {})
    need(
        request.get("cmd") == literal(argv)
        and request.get("workdir") == cwd
        and request.get("login") is False
        and request.get("tty") is True
        and request.get("yield_time_ms") == 1000
        and type(request["yield_time_ms"]) is int
        and request.get("max_output_tokens") == 3000
        and set(request)
        == {"cmd", "workdir", "login", "tty", "yield_time_ms", "max_output_tokens"},
        "courier literal request differs",
    )
    rows = packet.get("responses")
    need(type(rows) is list and 2 <= len(rows) <= 65, "courier rows required")
    previous, session, output, data_writes, terminal = None, None, "", 0, None
    for index, row in enumerate(rows):
        first, last = row.get("requested_ms"), row.get("returned_ms")
        need(
            integer(first, minimum=1)
            and integer(last, minimum=1)
            and first <= last <= deadline_ms
            and (previous is None or previous <= first)
            and terminal is None,
            "courier original clock/order/terminal differs",
        )
        args = row.get("arguments", {})
        if index == 0:
            need(
                row.get("tool") == "exec_command" and args == request, "courier first exec differs"
            )
        else:
            need(
                row.get("tool") == "write_stdin"
                and integer(session, minimum=1)
                and args.get("session_id") == session
                and type(args["session_id"]) is int
                and type(args.get("chars")) is str
                and integer(args.get("yield_time_ms"), minimum=1)
                and args["yield_time_ms"] <= min(30000, deadline_ms - first)
                and args.get("max_output_tokens") == 3000
                and type(args["max_output_tokens"]) is int
                and set(args) == {"session_id", "chars", "yield_time_ms", "max_output_tokens"},
                "courier foreign session or poll differs",
            )
            if args["chars"]:
                need(
                    data_writes == 0
                    and output == READY
                    and args["chars"].endswith("\n")
                    and len(args["chars"].encode()) <= 128 * 1024
                    and parse(args["chars"].encode()) == original,
                    "courier original data message differs",
                )
                data_writes += 1
            else:
                need(
                    args["yield_time_ms"] >= 5000,
                    "courier empty poll has no finite minimum allowance",
                )
        result = row.get("result")
        need(
            type(result) is dict
            and "error" not in row
            and type(result.get("output")) is str
            and "Warning: truncated output" not in result["output"]
            and "tokens truncated" not in result["output"]
            and (
                result.get("original_token_count") is None
                or (
                    integer(result["original_token_count"])
                    and result["original_token_count"] <= args["max_output_tokens"]
                )
            ),
            "courier original output incomplete",
        )
        output += result["output"]
        need(len(output.encode()) <= 64 * 1024, "courier stdout exceeds bound")
        if not data_writes:
            need(READY.startswith(output), "courier ready marker differs")
        code, observed = result.get("exit_code"), result.get("session_id")
        if observed is not None:
            need(
                integer(observed, minimum=1)
                and code is None
                and (session is None or observed == session),
                "courier live session differs",
            )
            session = observed
        else:
            need(
                type(code) is int and code == 0 and data_writes == 1,
                "courier terminal not successful",
            )
            terminal = last
        previous = last
    need(
        terminal is not None and output.startswith(READY) and data_writes == 1,
        "courier original terminal missing",
    )
    saved = parse(output[len(READY) :].encode())
    raw = canonical(original)
    need(
        saved.get("status") == "PAIRED_PERSISTED"
        and saved.get("failures") == []
        and type(expected_paths) is list
        and len(expected_paths) == 2
        and len(set(expected_paths)) == 2
        and saved.get("path") == expected_paths[0]
        and saved.get("bytes") == len(raw)
        and type(saved["bytes"]) is int
        and saved.get("sha256") == sha(raw)
        and saved.get("copies")
        == [dict(path=p, bytes=len(raw), sha256=sha(raw)) for p in expected_paths]
        and digest(saved.get("program_sha256"))
        and digest(saved.get("file_intent_sha256")),
        "courier paired receipt differs",
    )
    timing = saved.get("timing", {})
    need(set(timing) == set(TIMING_KEYS), "courier timing points incomplete")
    clocks = []
    for name in TIMING_KEYS:
        point = timing[name]
        need(
            type(point) is dict
            and set(point) == {"utc_us", "monotonic_us"}
            and all(integer(v, minimum=1) for v in point.values()),
            "courier timing types differ",
        )
        clocks.append((point["utc_us"], point["monotonic_us"]))
    need(
        all(a[0] <= b[0] and a[1] <= b[1] for a, b in zip(clocks, clocks[1:], strict=False))
        and rows[0]["requested_ms"] * 1000 <= clocks[0][0]
        and clocks[-1][0] <= terminal * 1000 + 999,
        "courier write/terminal clock differs",
    )
    delivery = terminal if delivery_ms is None else delivery_ms
    need(integer(delivery, minimum=terminal), "courier delivery clock differs")
    return dict(
        actual_start_ms=rows[0]["requested_ms"],
        actual_terminal_ms=terminal,
        caller_delivery_ms=delivery,
        caller_on_time=delivery <= deadline_ms,
        data_writes=1,
        packet_sha256=sha(raw),
        receipt=saved,
    )


def history():
    import certificate_replay_proof

    need(
        Path(certificate_replay_proof.__file__).resolve()
        == REPO / "scripts/certificate_replay_proof.py",
        "current shared proof required",
    )
    return certificate_replay_proof


def pricing():
    raw = pair(DATA, "public-pricing.json")
    need(
        sha(raw) == PRICING and sha(pair(DATA, "owner-budget.json")) == BUDGET,
        "fixed owner/pricing bytes differ",
    )
    value = parse(raw)
    need(
        value["bound_owner_budget_sha256"] == BUDGET
        and value["fixed_total_diagnostic_FULL"] == 9600
        and value["total_named_campaign_ceiling_FULL"] == 15960
        and value["formal_reserve_FULL"] == 3960
        and value["full_public_closeout"]["reserve_before_entry_FULL"] == 3600
        and value["narrow_probe"]["charge_on_entry_FULL"] == 600,
        "finite public pricing differs",
    )
    return value


def prior_evidence(policy):
    """Full historic metadata replay, only in the independently scheduled CLI."""
    import formal_input_independent as public
    import staged_binding_evidence as registration
    from child_readiness_proof import historical_inputs

    old_policy, old_tree = historical_inputs()
    old = history().verified_readiness(old_policy, old_tree)
    need(
        old
        == dict(
            source_main="671a21b3d47fae16610e13884993abee5bee8e12",
            verified_returned_ms=1795519025567,
            package=dict(
                path=str(DATA.parent / "certificate-20261124-formal/certificate-replay.json"),
                sha256="133553193c411d565860c0a04ac81b65f8bad47152d1b89caa88e28ee3b75c81",
            ),
            actual=dict(
                path=str(
                    DATA.parent / "certificate-20261124-formal/certificate-replay-actual.json"
                ),
                sha256="7b3af893a673787cce4992eb9ca92db91c08e4112e81a0d225265cf839edbeda",
            ),
        ),
        "historical full certificate original differs",
    )
    prior = policy["prior_public"]
    need(prior == public.expected_prior(FORMAL), "fixed historical public namespace differs")
    bundle = pair(FORMAL, "prior-public-bundle.json")
    actual = pair(FORMAL, "prior-public-certificate-actual.json")
    accepted = public.verify_prior_public(prior, bundle, actual)
    context, observations = registration.verified_formal_registration()
    need(
        len(observations) == 23 and len({r["path"] for r in observations}) == 23,
        "complete historical strict23 required",
    )
    pin = policy["registration"]["formal"]
    need(
        pin["certificate_sha256"]
        == "56a7ef886ba8c634eb505004f0498d739c45cafa4bd63d925e424f92811da167"
        and pin["finalize_actual_sha256"]
        == "c1709f92c3ed9544b49ebe428714e50f2685b1ff95d2d02a340dcdd47b7204b5",
        "fixed strict23 certificate pins differ",
    )
    return dict(
        certificate=old,
        public=accepted,
        registration=dict(
            certificate_sha256=pin["certificate_sha256"],
            finalize_actual_sha256=pin["finalize_actual_sha256"],
            bindings=23,
            context_sha256=sha(canonical(context)),
            observations_sha256=sha(canonical(observations)),
        ),
    )


def milliseconds(value):
    result = Decimal(str(value)) * 1000
    need(
        result.is_finite() and result == result.to_integral_value(),
        "original exact millisecond missing",
    )
    return int(result)


def public_claim(slot, claim, *, negative):
    root = f"/private/tmp/topolab-public-closeout-20261125-a{slot}"
    need(
        type(slot) is int
        and 1 <= slot <= 16
        and claim["slot"] == slot
        and type(claim["slot"]) is int
        and claim["root"] == root
        and claim["schema"] == "topolab.closeout-public-entry.v1"
        and claim["formal_authority"] is False
        and claim["author"] == PUBLIC_AUTHOR
        and claim["fixture_kind"] == ("REPLAY_NEGATIVE" if negative else "FULL_POSITIVE")
        and claim["mode"] == ("late" if negative else "released")
        and claim["fee_reservation_FULL"] == (600 if negative else 3600)
        and type(claim["fee_reservation_FULL"]) is int
        and claim["charge_FULL"] == 600
        and type(claim["charge_FULL"]) is int
        and claim["budget_sha256"] == BUDGET
        and claim["pricing_sha256"] == PRICING
        and integer(claim["start_ms"])
        and integer(claim["end_ms"])
        and START <= claim["start_ms"] < claim["end_ms"] <= DIAGNOSTIC_END
        and claim["end_ms"] - claim["start_ms"] == 780000,
        "public entry authority differs",
    )
    return root


def normal_call(packet, argv, claim):
    import staged_input_filer as wire

    first, last, code = wire.validate_terminal(packet, argv, PUBLIC_AUTHOR, str(REPO))
    need(
        code == 0
        and "prefix_rule" not in packet["request"]
        and packet["request"].get("login") is False
        and claim["start_ms"] <= first <= last <= claim["end_ms"]
        and all(
            integer(r["arguments"].get("yield_time_ms"), minimum=5000)
            and r["arguments"]["yield_time_ms"] <= 30000
            for r in packet["responses"][1:]
        ),
        "original public return differs",
    )
    return first, last, "".join(r["result"]["output"] for r in packet["responses"]).encode()


def native_role(role, files, events, argv, plan_sha):
    import p17_m2_content_verified_independent as independent

    def obj(name):
        return parse(files[name])

    native = obj(f"native/receipts/{role}-wire.json")
    accepted = obj(f"native/{role}-accepted.json")
    need(
        accepted["raw_tool_events"] == events == obj(f"native/{role}-events.json"),
        "native original event pair differs",
    )
    folder = f"native/receipts/{role}/{role}/"
    record = obj(folder + "command.json")
    helpers = record["helpers"]
    need(
        type(helpers) is list
        and all(h.get("profile") == f"sampler-{i}.time" for i, h in enumerate(helpers)),
        "standard public sampler profile order differs",
    )
    expected_profiles = {folder + h["profile"] for h in helpers}
    actual_profiles = {
        name for name in files if name.startswith(folder + "sampler-") and name.endswith(".time")
    }
    need(actual_profiles == expected_profiles, "standard public sampler inventory differs")
    inner = dict(
        record=record,
        profile=files[folder + "command.time"],
        log=files[folder + "command.log"],
        expected_role=role,
        expected_argv=argv,
        helper_profiles={h["profile"]: files[folder + h["profile"]] for h in record["helpers"]},
        platform="darwin",
    )
    profiles = {"outer-controller": files[f"native/receipts/{role}-controller.time"]}
    result = independent.audit_role(
        native["pending"],
        native["completion"],
        raw_tool_events=events,
        expected_role=role,
        expected_plan_sha256=plan_sha,
        inner_evidence=inner,
        native_profiles=profiles,
        expected_identity=PUBLIC_ID,
    )
    need(
        result == accepted["result"]
        and result["full_role_evidence_accepted"] is True
        and result["evidence_complete"] is True
        and result["actual_exit_codes"] == [0, 0]
        and all(type(v) is int for v in result["actual_exit_codes"])
        and integer(result["RSS_envelope_bytes"], minimum=1)
        and result["RSS_envelope_bytes"] <= 4 * 1024**3,
        "full public native role failed",
    )
    return result, native


def archive_buffers(raw, inventory):
    """Finite six-role metadata archive; unchanged sixteen MiB member limit."""
    need(type(raw) is bytes and 0 < len(raw) <= 128 * 1024**2, "bounded public archive required")
    index = parse(inventory)
    need(type(index) is dict and 1 <= len(index) <= 8192, "bounded six-role index required")
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:
        members = archive.getmembers()
        need(
            len(members) == len(index) == len({m.name for m in members})
            and {m.name for m in members} == set(index)
            and all(
                m.isfile()
                and m.name.startswith(("native/", "caller/", "custody/"))
                and Path(m.name).as_posix() == m.name
                and ".." not in Path(m.name).parts
                and not m.name.startswith(("native/content/", "native/backup-content/"))
                and Path(m.name).suffix not in (".npy", ".npz", ".pt", ".pth")
                and 0 <= m.size <= 16 * 1024**2
                for m in members
            )
            and sum(m.size for m in members) <= 128 * 1024**2,
            "six-role metadata archive inventory differs",
        )
        files = {m.name: archive.extractfile(m).read() for m in members}
    for name, member_raw in files.items():
        item = index[name]
        need(
            type(item.get("bytes")) is int
            and item == dict(bytes=len(member_raw), sha256=sha(member_raw)),
            "public archive member bytes/hash differs: " + name,
        )
    return files


def observation_table(rows, count):
    """Public fixtures use the unchanged strict four-point identity policy."""
    need(type(rows) is list and len(rows) == count, "exact public observation count required")
    result = {}
    for row in rows:
        name = row.get("path")
        need(
            type(row) is dict
            and set(row)
            == {"path", "byte_size", "sha256", "declared", "before", "after", "closing"}
            and type(name) is str
            and name not in result
            and name not in ("", ".")
            and not Path(name).is_absolute()
            and ".." not in Path(name).parts
            and Path(name).as_posix() == name
            and digest(row["sha256"])
            and integer(row["byte_size"], minimum=1),
            "unsafe public observation row",
        )
        for stage in ("declared", "before", "after", "closing"):
            point = row[stage]
            need(
                type(point) is dict
                and set(point) == {"st_dev", "st_ino", "st_size", "st_mtime_ns"}
                and all(integer(v) for v in point.values())
                and point == row["before"]
                and point["st_size"] == row["byte_size"],
                "public observation identity/bytes changed",
            )
        result[name] = row
    return result


def public_content(files, closed, backup, results, events_all, plan_sha):
    def obj(name):
        return parse(files[name])

    logs = {
        role: obj(f"native/receipts/{role}/{role}/command.log")
        for role in ("independent-r0", "independent-r1", "shared-closeout")
    }
    r0, r1 = logs["independent-r0"], logs["independent-r1"]
    for role, status in (
        ("independent-r0", "PUBLIC_INDEPENDENT_R0_CHECKED"),
        ("independent-r1", "PUBLIC_INDEPENDENT_R1_CHECKED"),
        ("shared-closeout", "PUBLIC_INDEPENDENT_BACKUP_CHECKED"),
    ):
        value = logs[role]
        need(
            value["status"] == status
            and value["execution_identity"] == PUBLIC_ID
            and value["scope"] == PUBLIC_SCOPE
            and value["B_C_admission"] is False,
            "public content proof log identity/status differs",
        )
    need(
        r1 == obj("native/r1-proof.json")
        and logs["shared-closeout"] == backup
        and r0["source_count"] == 40
        and r1["source_count"] == 558
        and r0["source_registry_sha256"]
        == r1["source_registry_sha256"]
        == sha(files["native/registry.json"]),
        "public Native content artifacts differ",
    )
    for proof, name, count in ((r0, "r0-source-rows.json", 40), (r1, "r1-source-rows.json", 558)):
        need(
            observation_table(proof["source_rows"], count)
            == observation_table(obj("native/" + name), count),
            "public producer/independent source observations differ",
        )
    own = observation_table(closed["local_identity_rows"], 1071)
    need(
        own == observation_table(r1["local_identity_rows"], 1071),
        "public independent complete local observations differ",
    )
    copied = observation_table(backup["identity_rows"], 1071)
    for member in closed["manifest"]["members"]:
        name = member["path"]
        need(
            name in own
            and name in copied
            and all(
                own[name][k] == copied[name][k] == member[k]
                for k in ("path", "byte_size", "sha256")
            ),
            "public backup member bytes/hash differs",
        )
    shared = obj("native/shared-packet.json")
    need(
        shared["status"] == "SEALED_HANDOFF_PENDING_INDEPENDENT_FILING"
        and shared["scope"] == PUBLIC_SCOPE
        and shared["execution_identity"] == PUBLIC_ID
        and shared["plan_sha256"] == plan_sha
        and shared["secondary_failures"] == []
        and shared["role_results"] == results
        and shared["raw_packets"]
        == {
            role: dict(
                wire=obj(f"native/receipts/{role}-wire.json"), raw_tool_events=events_all[role]
            )
            for role in ROLES
        },
        "complete original shared handoff differs",
    )
    return dict(
        metadata_each=40,
        payloads_each=558,
        compared_members=1071,
        observations_verified_from_sealed_controls=True,
    )


def audit_full(slot, claim, summary, files):
    """Reconcile all six genuine Native roles and original return/file/bind rows."""
    from r0_caller_receipt import project

    root = public_claim(slot, claim, negative=False)

    def obj(name):
        return parse(files[name])

    plan_raw = files["native/plan.json"]
    plan, plan_sha = parse(plan_raw), sha(plan_raw)
    need(
        plan["root"] == root
        and plan["execution_identity"] == PUBLIC_ID
        and plan["scope"] == PUBLIC_SCOPE
        and plan["formal_authority"] is False
        and plan["role_order"] == list(ROLES)
        and plan["runtime"]["cwd"] == str(REPO)
        and all(plan["source_tree"].get(k) == v for k, v in claim["software_sha256"].items())
        and plan["source_tree"]["fixture/scheduler"] == claim["scheduler_sha256"],
        "public plan/source authority differs",
    )
    outer = obj("caller/outer-original.json")
    need(
        outer["status"] == "PASS_PUBLIC_NATIVE_CLOSEOUT"
        and outer["mode"] == "released"
        and outer["root"] == root
        and outer["controlled"] == []
        and set(outer["roles"]) == set(ROLES)
        and summary["slot"] == slot
        and summary["root"] == root
        and summary["fixture_charge_FULL"] == 3600,
        "full public actual cohort missing",
    )
    entry = str(REPO / "scripts/closeout_public_control.py")
    prefix = [PYTHON, "-I", entry]
    calls = outer["calls"]
    expected_calls = {"prepare"} | {
        r + "-" + op
        for r in ROLES
        for op in (
            "supervise",
            "persist-supervise",
            "file-supervise",
            "record",
            "persist-record",
            "file-record",
            "bind",
        )
    }
    need(set(calls) == expected_calls, "complete original call inventory differs")
    need(
        not any(n == "native/STOP.json" or n.endswith("-caller-STOP.json") for n in files),
        "public STOP veto",
    )
    results, originals, events_all = {}, {}, {}
    first, previous, prepared = normal_call(
        calls["prepare"], prefix + ["prepare-public", "--root", root], claim
    )
    need(
        canonical(calls["prepare"]) == files["caller/prepare-actual.json"]
        and parse(prepared)["plan_sha256"] == plan_sha,
        "true prepare return differs",
    )
    for role, cap in zip(ROLES, CAPS, strict=True):
        role_info = outer["roles"][role]
        entered, deadline = role_info["entered_ms"], role_info["deadline_ms"]
        need(
            integer(entered)
            and integer(deadline)
            and previous <= entered
            and deadline == min(claim["end_ms"], entered + cap * 1000 - 10000),
            "original role deadline differs",
        )
        tail = ["--root", root, "--plan-sha", plan_sha, "--role", role]
        events = obj(f"native/{role}-events.json")
        need(type(events) is list and len(events) == 2, "two original Native events required")
        native = obj(f"native/receipts/{role}-wire.json")
        for mode, event in zip(("supervise", "record"), events, strict=True):
            key = role + "-" + mode
            packet, packet_raw = calls[key], files["caller/" + key + "-actual.json"]
            start, end, output = normal_call(packet, prefix + [mode, *tail], claim)
            need(
                canonical(packet) == packet_raw
                and previous <= start <= end <= deadline
                and event == obj(f"native/{role}-{mode}-actual-event.json")
                and event["event_id"] == packet["event_id"]
                and event["raw_packet_sha256"] == sha(packet_raw)
                and event["author"] == PUBLIC_AUTHOR
                and type(event["exit_code"]) is int
                and event["exit_code"] == 0
                and event["complete"] is True
                and milliseconds(event["start_seconds"]) == start
                and milliseconds(event["end_seconds"]) == end,
                "filed Native original differs",
            )
            expected = (
                dict(status="PENDING_EXTERNAL_EXIT", controller_exit=0)
                if mode == "supervise"
                else project(mode, role, plan_sha, native, canonical(native))
            )
            need(output == canonical(expected), "Native compact/full return binding differs")
            previous = end
            original_raw = files[f"custody/primary/{role}-{mode}-actual.json"]
            need(
                original_raw == files[f"custody/backup/{role}-{mode}-actual.json"] == packet_raw,
                "paired original role bytes differ",
            )
            persist_key = role + "-persist-" + mode
            persist = calls[persist_key]
            need(
                canonical(persist) == files["caller/" + persist_key + "-actual.json"],
                "persistence original differs",
            )
            paths = [
                root + suffix + f"/{role}-{mode}-actual.json"
                for suffix in ("-evidence", "-evidence-backup")
            ]
            if role == "shared-closeout" and mode == "record":
                expected_argv = prefix + [
                    "persist-closeout-record",
                    *tail,
                    "--event-mode",
                    mode,
                    "--deadline-ms",
                    str(deadline),
                ]
                courier = audit_courier(
                    persist,
                    packet,
                    argv=expected_argv,
                    author=PUBLIC_AUTHOR,
                    cwd=str(REPO),
                    deadline_ms=deadline,
                    expected_paths=paths,
                )
                need(courier["caller_on_time"] is True, "late courier cannot file/bind")
                saved, persist_first, persist_last = (
                    courier["receipt"],
                    courier["actual_start_ms"],
                    courier["actual_terminal_ms"],
                )
                originals["shared_record"] = dict(
                    packet=packet, packet_sha256=sha(packet_raw), courier=courier
                )
            else:
                actual_argv = persist["argv"]
                expected_argv = prefix + ["persist-public", *tail, "--event-mode", mode]
                need(
                    actual_argv[:-2] == expected_argv
                    and actual_argv[-2] == "--packet-json"
                    and parse(actual_argv[-1].encode()) == packet,
                    "wrong saved Native buffer",
                )
                persist_first, persist_last, persist_output = normal_call(
                    persist, actual_argv, claim
                )
                saved = parse(persist_output)
                need(
                    saved["status"] == "PAIRED_PERSISTED"
                    and saved["sha256"] == sha(packet_raw)
                    and saved["bytes"] == len(packet_raw)
                    and saved["failures"] == []
                    and saved["copies"]
                    == [dict(path=p, bytes=len(packet_raw), sha256=sha(packet_raw)) for p in paths],
                    "original paired custody differs",
                )
            need(
                previous <= persist_first <= persist_last <= deadline,
                "actual persistence exceeded original role deadline",
            )
            intent_name = f"filing-{role}-{mode}-intent.json"
            intent_raw = files["custody/primary/" + intent_name]
            intent = parse(intent_raw)
            outputs = [f"{role}-{mode}-actual-event.json"] + (
                [f"{role}-events.json"] if mode == "record" else []
            )
            need(
                intent_raw == files["custody/backup/" + intent_name]
                and intent
                == dict(
                    schema="topolab.public-closeout.filing-intent.v1",
                    program_sha256=claim["software_sha256"]["scripts/closeout_public_schedule.mjs"],
                    role=role,
                    mode=mode,
                    author=PUBLIC_AUTHOR,
                    root=root,
                    plan_sha256=plan_sha,
                    outputs=outputs,
                    event=event,
                )
                and sha(intent_raw) == saved["file_intent_sha256"]
                and intent["program_sha256"] == saved["program_sha256"],
                "single-use intent differs from actual original",
            )
            spent_name = f"filing-{role}-{mode}-spent.json"
            spent_raw = files["custody/primary/" + spent_name]
            need(
                spent_raw == files["custody/backup/" + spent_name]
                and parse(spent_raw)
                == dict(intent_sha256=sha(intent_raw), event_id=event["event_id"], outputs=outputs),
                "intent was not consumed exactly once",
            )
            file_key = role + "-file-" + mode
            filed = calls[file_key]
            file_first, file_last, file_output = normal_call(
                filed,
                prefix
                + [
                    "file-public",
                    *tail,
                    "--event-mode",
                    mode,
                    "--packet-sha",
                    sha(packet_raw),
                    "--intent-sha",
                    sha(intent_raw),
                    "--program-sha",
                    saved["program_sha256"],
                ],
                claim,
            )
            need(
                canonical(filed) == files["caller/" + file_key + "-actual.json"]
                and persist_last <= file_first <= file_last <= deadline
                and parse(file_output)
                == dict(
                    status="ACTUAL_EVENT_FILED", role=role, mode=mode, intent_sha256=sha(intent_raw)
                ),
                "actual event filing differs",
            )
            previous = file_last
        result, _ = native_role(role, files, events, prefix + ["payload", *tail], plan_sha)
        bind = calls[role + "-bind"]
        bind_first, bind_last, bind_output = normal_call(bind, prefix + ["bind", *tail], claim)
        need(
            canonical(bind) == files[f"caller/{role}-bind-actual.json"]
            and previous <= bind_first <= bind_last <= deadline
            and bind_output == canonical(project("bind", role, plan_sha, result, canonical(result)))
            and role_info["bind_return_ms"] == bind_last,
            "actual bind caller did not return accepted in time",
        )
        previous = bind_last
        results[role], events_all[role] = result, events
    reservation = obj("native/ledger-reservation.json")
    need(
        reservation["shared_reserved_FULL_seconds"] == 300
        and reservation["scope"] == PUBLIC_SCOPE
        and reservation["execution_identity"] == PUBLIC_ID
        and reservation["plan_sha256"] == plan_sha
        and reservation["refunds_allowed"] is False,
        "shared original reservation differs",
    )
    charges = []
    for role, cap in zip(ROLES, CAPS, strict=True):
        charge = obj(f"native/{role}-dispatch-charge.json")
        need(
            charge["role"] == role
            and charge["plan_sha256"] == plan_sha
            and charge["execution_identity"] == PUBLIC_ID
            and charge["scope"] == PUBLIC_SCOPE
            and charge["frozen_FULL_seconds"] == cap
            and type(charge["frozen_FULL_seconds"]) is int
            and charge["charged_FULL_seconds"] == (0 if role == "shared-closeout" else cap)
            and type(charge["charged_FULL_seconds"]) is int
            and charge["shared_reservation_sha256"] == sha(canonical(reservation)),
            "public Native actual charge differs",
        )
        charges.append(charge)
    closed, backup = obj("native/closed.json"), obj("native/backup-proof.json")
    manifest = closed["manifest"]
    members = manifest["members"]
    need(
        len(members) == len({m["path"] for m in members}) == 1071
        and closed["version_id"] == sha(canonical(manifest)) == backup["version_id"]
        and manifest == backup["manifest"]
        and backup["member_count"] == 1071
        and all(
            digest(m["sha256"])
            and integer(m["byte_size"])
            and not Path(m["path"]).is_absolute()
            and ".." not in Path(m["path"]).parts
            for m in members
        ),
        "1071-member backup/version differs",
    )
    content = public_content(files, closed, backup, results, events_all, plan_sha)
    return dict(
        slot=slot,
        kind="FULL_POSITIVE",
        source_main=claim["checkout_head"],
        root=root,
        source_tree=claim["software_sha256"],
        plan_sha256=plan_sha,
        role_results=results,
        shared_original=originals["shared_record"],
        member_count=1071,
        version_id=closed["version_id"],
        known_FULL=300 + sum(c["charged_FULL_seconds"] for c in charges),
        original_start_ms=first,
        original_end_ms=previous,
        content=content,
    )


def audit_negative(slot, claim, summary, files, origins):
    """A new receipt-only replay cannot create a new Native predecessor history."""
    root = public_claim(slot, claim, negative=True)
    ref = claim["positive_origin"]
    need(ref["slot"] in origins, "negative must reference an independently passed positive")
    origin = origins[ref["slot"]]
    need(
        ref
        == dict(
            slot=origin["slot"],
            rec_sha256=origin["shared_original"]["packet_sha256"],
            plan_sha256=origin["plan_sha256"],
            report_sha256=origin["result_sha256"],
            index_sha256=origin["index_sha256"],
            archive_sha256=origin["archive_sha256"],
        ),
        "negative origin raw pins differ",
    )
    need(
        ref["slot"] < slot and origin["original_end_ms"] <= claim["start_ms"],
        "negative replay cannot precede its original positive",
    )
    outer = parse(files["caller/outer-original.json"])
    key = "shared-closeout-persist-record"
    need(
        outer["status"] == "STOP_PUBLIC_CLOSEOUT"
        and outer["root"] == root
        and outer["mode"] == "late"
        and outer["stage"] == key
        and "closeout receipt returned late or lacks original clock" in outer["error"]
        and set(outer["calls"]) == {"prepare", key}
        and set(outer["roles"]) == {"shared-closeout"}
        and summary["fixture_charge_FULL"] == 600
        and summary["slot"] == slot,
        "late replay did not stop at the original transport boundary",
    )
    need(
        set(files)
        == {
            "caller/entry.json",
            "caller/outer-original.json",
            "caller/prepare-actual.json",
            "caller/" + key + "-actual.json",
            "custody/primary/shared-closeout-record-actual.json",
            "custody/backup/shared-closeout-record-actual.json",
            "custody/primary/filing-shared-closeout-record-intent.json",
            "custody/backup/filing-shared-closeout-record-intent.json",
        },
        "replay must not contain new Native, filed/spent, bind or successor evidence",
    )
    info = outer["roles"]["shared-closeout"]
    entered, deadline = info["entered_ms"], info["deadline_ms"]
    need(
        integer(entered)
        and deadline == entered + 290000
        and info["native_replay"] is True
        and info["source_plan"] == origin["plan_sha256"]
        and info["origin_slot"] == ref["slot"],
        "replay deadline/origin differs",
    )
    prefix = [PYTHON, "-I", str(REPO / "scripts/closeout_public_control.py")]
    prepare = outer["calls"]["prepare"]
    _, prepared_end, prepared_output = normal_call(
        prepare, prefix + ["prepare-replay", "--root", root], claim
    )
    need(
        canonical(prepare) == files["caller/prepare-actual.json"]
        and prepared_end <= entered
        and parse(prepared_output)
        == dict(
            scope="PUBLIC_CLOSEOUT_RECEIPT_REPLAY_ONLY",
            formal_authority=False,
            origin=ref,
            native_roles_dispatched=0,
            original_returns=origin["original_shared_returns"],
        ),
        "replay prepare must retain the original origin returns",
    )
    controlled = outer["controlled"]
    packet = outer["calls"][key]
    need(
        type(controlled) is list
        and len(controlled) == 1
        and controlled[0]["stage"] == key
        and controlled[0]["tool"] == packet["responses"][-1]["tool"]
        and controlled[0]["underlying_tool_returned_ms"] == packet["responses"][-1]["returned_ms"]
        and canonical(packet) == files["caller/" + key + "-actual.json"],
        "controlled original upstream/downstream clocks differ",
    )
    original = origin["shared_original"]["packet"]
    original_raw = canonical(original)
    need(
        files["custody/primary/shared-closeout-record-actual.json"]
        == files["custody/backup/shared-closeout-record-actual.json"]
        == original_raw,
        "replay new custody did not retain the original public REC bytes",
    )
    argv = prefix + [
        "persist-closeout-record",
        "--root",
        root,
        "--plan-sha",
        ref["plan_sha256"],
        "--role",
        "shared-closeout",
        "--event-mode",
        "record",
        "--deadline-ms",
        str(deadline),
    ]
    paths = [
        root + suffix + "/shared-closeout-record-actual.json"
        for suffix in ("-evidence", "-evidence-backup")
    ]
    courier = audit_courier(
        packet,
        original,
        argv=argv,
        author=PUBLIC_AUTHOR,
        cwd=str(REPO),
        deadline_ms=deadline,
        expected_paths=paths,
        delivery_ms=controlled[0]["caller_delivery_ms"],
    )
    need(
        courier["caller_on_time"] is False
        and courier["actual_start_ms"] >= entered
        and deadline < courier["caller_delivery_ms"] <= outer["end_ms"] <= claim["end_ms"],
        "late delivery must veto despite actual paired writes",
    )
    intent_raw = files["custody/primary/filing-shared-closeout-record-intent.json"]
    need(
        intent_raw == files["custody/backup/filing-shared-closeout-record-intent.json"]
        and parse(intent_raw)
        == dict(
            schema="topolab.public-closeout.replay-intent.v1",
            formal_authority=False,
            fixture_root=root,
            origin=ref,
            program_sha256=claim["software_sha256"]["scripts/closeout_public_schedule.mjs"],
            packet_sha256=sha(original_raw),
            event_id=original["event_id"],
            author=PUBLIC_AUTHOR,
        )
        and sha(intent_raw) == courier["receipt"]["file_intent_sha256"],
        "replay single-use intent/origin differs",
    )
    return dict(
        slot=slot,
        kind="REPLAY_NEGATIVE",
        root=root,
        origin=ref,
        source_main=claim["checkout_head"],
        source_tree=claim["software_sha256"],
        actual_native_roles=0,
        filed_events=0,
        bind_invocations=0,
        known_FULL=600,
        courier=courier,
        original_end_ms=outer["end_ms"],
    )


def public_run(slot, *, origins=None):
    claim_raw = pair(DATA, f"public-{slot}-entry.json")
    claim = parse(claim_raw)
    summary_raw = pair(DATA, f"public-{slot}-result.json")
    summary = parse(summary_raw)
    inventory = pair(DATA, f"public-{slot}-index.json")
    archive = pair(DATA, f"public-{slot}-evidence.tar.gz", 128 * 1024**2)
    need(
        sha(archive) == summary["archive_sha256"] and sha(inventory) == summary["index_sha256"],
        "public raw archive SHA differs",
    )
    files = archive_buffers(archive, inventory)
    need(files["caller/entry.json"] == claim_raw, "archived original claim differs")
    result = (
        audit_full(slot, claim, summary, files)
        if origins is None
        else audit_negative(slot, claim, summary, files, origins)
    )
    if origins is None:
        result["original_shared_returns"] = {
            m: parse(files[f"caller/shared-closeout-{m}-actual.json"])
            for m in ("supervise", "record")
        }
    return dict(
        result,
        result_sha256=sha(summary_raw),
        archive_sha256=sha(archive),
        index_sha256=sha(inventory),
    )


def candidate(runs, tree, main):
    need(
        type(main) is str
        and re.fullmatch("[0-9a-f]{40}", main)
        and history().checkout_commit(REPO) == main,
        "current protected checkout differs",
    )
    need(
        len(runs) == 3 and all(r["source_main"] == main and r["source_tree"] == tree for r in runs),
        "all public fixtures must use the exact released formal software",
    )
    need(
        [r["kind"] for r in runs] == ["FULL_POSITIVE", "FULL_POSITIVE", "REPLAY_NEGATIVE"],
        "complete positives and scoped replay negative required",
    )


def public_reservations(slots):
    """Keep all scheduled failures: reservations cannot be erased by later PASS."""
    total, records = 0, []
    for slot in range(1, 17):
        try:
            raw = pair(DATA, f"public-{slot}-entry.json")
        except FileNotFoundError:
            # A single missing peer cannot silently remove an already booked claim.
            a = DATA / f"public-{slot}-entry.json"
            b = DATA.with_name(DATA.name + "-backup") / a.name
            need(not a.exists() and not b.exists(), "unpaired scheduled public entry")
            continue
        entry = parse(raw)
        amount = entry["fee_reservation_FULL"]
        need(
            entry["budget_sha256"] == BUDGET
            and entry["pricing_sha256"] == PRICING
            and entry["slot"] == slot
            and type(entry["slot"]) is int
            and type(amount) is int
            and amount in (600, 3600)
            and total == entry["prior_charged_FULL"],
            "public prior reservation changed",
        )
        total += amount
        records.append(dict(slot=slot, sha256=sha(raw), reserved_FULL=amount))
    need(
        total <= 9600 and all(n in [r["slot"] for r in records] for n in slots),
        "finite diagnostic ceiling exceeded",
    )
    return dict(
        records=records, reserved_FULL=total, remaining_FULL=9600 - total, failures_retained=True
    )


def gate_args(slots):
    need(
        type(slots) is list
        and len(slots) == len(set(slots)) == 3
        and all(type(n) is int and 1 <= n <= 16 for n in slots),
        "two positives and a distinct negative required",
    )
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


def compiled(tree, *, verification):
    loader = sys.modules["full60_input_loader"]
    names = SOFTWARE if verification else (WORKER, "scripts/certificate_replay_proof.py")
    result = {}
    for name in names:
        actual = loader.loaded_source_sha256.get(str(REPO / name))
        if name == WORKER and actual is None:
            actual = MODULE_SOURCE_SHA256
        need(
            actual == tree[name] == sha((REPO / name).read_bytes()),
            "actual compiled source differs: " + name,
        )
        result[name] = actual
    return result


def verified_readiness(policy, tree):
    """Small, repeatable in-process gate; full archives were checked by the CLI.

    No Git/subprocess, source input, custody target, lease or large archive opens
    occur here. The independent original terminal binds the complete report.
    """
    import r0_read_independent as original

    need(
        policy["execution_identity"] == IDENTITY
        and policy["new_input_budget"] == dict(path=str(DATA / "owner-budget.json"), sha256=BUDGET)
        and policy["closeout_verification_paths"]
        == dict(package=str(FORMAL / PACKAGE), actual=str(FORMAL / ACTUAL)),
        "new closeout namespace/budget differs",
    )
    pricing()
    raw, actual_raw = pair(FORMAL, PACKAGE), pair(FORMAL, ACTUAL)
    report = parse(raw)
    first, last, output = original.terminal(
        parse(actual_raw),
        gate_args(report["slots"]),
        author=AUTHOR,
        cwd=str(REPO),
        window=(START, END),
        full=300,
    )
    need(
        report["status"] == STATUS
        and report["execution_identity"] == IDENTITY
        and report["budget_sha256"] == BUDGET
        and report["pricing_sha256"] == PRICING
        and report["authority_sha256"] == tree[PROTOCOL]
        and report["software_tree_sha256"] == sha(canonical(tree))
        and report["executed"] == {n: tree[n] for n in SOFTWARE}
        and report["external_production_sources"] == {n: tree[n] for n in PRODUCTION}
        and report["worker_sha256"] == tree[WORKER]
        and report["prior_public"] == policy["prior_public"]
        and report["registration"] == policy["registration"]["formal"]
        and report["independent_entry"]["argv"] == gate_args(report["slots"])
        and report["independent_entry"]["start_ms"]
        <= first
        <= last
        <= report["independent_entry"]["end_ms"]
        and last <= time.time_ns() // 10**6
        and output
        == canonical(
            dict(
                status=STATUS, report_sha256=sha(raw), verification_slot=report["verification_slot"]
            )
        ),
        "independent closeout original/report differs",
    )
    need(history().checkout_commit(REPO) == report["source_main"], "current exact release differs")
    compiled(tree, verification=False)
    return dict(
        source_main=report["source_main"],
        verified_returned_ms=last,
        package=dict(path=str(FORMAL / PACKAGE), sha256=sha(raw)),
        actual=dict(path=str(FORMAL / ACTUAL), sha256=sha(actual_raw)),
    )


def verification_entry(slots, tree):
    argv = gate_args(slots)
    now = time.time_ns() // 10**6
    matches = []
    for slot in range(1, 5):
        try:
            raw = pair(DATA, f"released-verification-{slot}-entry.json")
        except FileNotFoundError:
            continue
        entry = parse(raw)
        if entry.get("argv") == argv and entry.get("start_ms", now + 1) <= now <= entry.get(
            "end_ms", now - 1
        ):
            matches.append((slot, entry))
    need(len(matches) == 1, "one current independent verifier entry required")
    slot, entry = matches[0]
    need(
        entry["schema"] == "topolab.closeout-verification-entry.v1"
        and entry["author"] == AUTHOR
        and entry["slot"] == slot
        and type(entry["slot"]) is int
        and entry["repo"] == str(REPO)
        and entry["worker_sha256"] == tree[WORKER]
        and entry["budget_sha256"] == BUDGET
        and entry["pricing_sha256"] == PRICING
        and entry["charge_FULL"] == 300
        and type(entry["charge_FULL"]) is int
        and integer(entry["start_ms"])
        and integer(entry["end_ms"])
        and START <= entry["start_ms"] <= now < entry["end_ms"] <= END
        and entry["end_ms"] - entry["start_ms"] <= 290000,
        "independent verifier authority differs",
    )
    return slot, entry


def verify(slots):
    """One registered offline call, before ordinary independent preflight."""
    import resource
    import subprocess

    import p17_m2_input_continuation as profiles
    import r0_read_independent  # noqa: F401 - original actual-return checker
    import staged_input_filer as wire

    gate_args(slots)
    need(
        sys.flags.isolated
        and Path.cwd() == REPO
        and sys.executable == PYTHON
        and START <= time.time_ns() // 10**6 < END,
        "released verifier runtime differs",
    )

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=REPO, timeout=15).decode().strip()

    main = git("rev-parse", "HEAD")
    need(
        main == git("rev-parse", "origin/main") and not git("status", "--porcelain", "-uall"),
        "clean protected release required",
    )
    live = profiles.profile("control", profiles.CLOSEOUT_FORMAL)
    profiles.profile("independent", profiles.CLOSEOUT_FORMAL)
    tree = live.source_freeze(IDENTITY)
    slot, entry = verification_entry(slots, tree)
    pricing()
    policy = profiles.profile("registered", profiles.CLOSEOUT_FORMAL).authority()
    prior = prior_evidence(policy)
    positives = [public_run(n) for n in slots[:2]]
    negative = public_run(slots[2], origins={r["slot"]: r for r in positives})
    runs = [*positives, negative]
    candidate(runs, tree, main)
    ledger = public_reservations(slots)
    executed = compiled(tree, verification=True)
    need(
        sys.platform == "darwin"
        and resource.getrusage(resource.RUSAGE_SELF).ru_maxrss <= 4 * 1024**3
        and time.time_ns() // 10**6 < entry["end_ms"],
        "independent verifier resource/deadline exceeded",
    )
    report = dict(
        status=STATUS,
        execution_identity=IDENTITY,
        source_main=main,
        slots=slots,
        runs=runs,
        diagnostic_ledger=ledger,
        prior_evidence=prior,
        prior_public=policy["prior_public"],
        registration=policy["registration"]["formal"],
        executed=executed,
        external_production_sources={n: tree[n] for n in PRODUCTION},
        worker_sha256=tree[WORKER],
        authority_sha256=tree[PROTOCOL],
        software_tree_sha256=sha(canonical(tree)),
        budget_sha256=BUDGET,
        pricing_sha256=PRICING,
        verification_slot=slot,
        independent_entry=entry,
        own_future_return="NOT_CLAIMED",
    )
    raw = canonical(report)
    need(
        len(raw) <= 16 * 1024**2 and time.time_ns() // 10**6 < entry["end_ms"],
        "complete bounded verifier report required before filing",
    )
    for folder in (FORMAL, FORMAL.with_name(FORMAL.name + "-backup")):
        wire.write_private(folder / f"closeout-readiness-slot-{slot}.json", raw)
    return dict(status=STATUS, report_sha256=sha(raw), verification_slot=slot)


def promote(actual_raw):
    """Publish fixed aliases only after the independent caller observed terminal0.

    Called with that caller's unmodified canonical original packet. No original
    slot package or actual is overwritten, including failed or late attempts.
    """
    import r0_read_independent as original
    import staged_input_filer as wire

    actual = parse(actual_raw)
    need(canonical(actual) == actual_raw, "canonical unmodified original required")
    slots = [int(n) for n in actual["argv"][-3:]]
    first, last, output = original.terminal(
        actual, gate_args(slots), author=AUTHOR, cwd=str(REPO), window=(START, END), full=300
    )
    returned = parse(output)
    slot = returned["verification_slot"]
    need(type(slot) is int and 1 <= slot <= 4, "registered original slot required")
    raw = pair(FORMAL, f"closeout-readiness-slot-{slot}.json")
    report = parse(raw)
    entry_raw = pair(DATA, f"released-verification-{slot}-entry.json")
    need(
        report["independent_entry"] == parse(entry_raw)
        and report["slots"] == slots
        and report["verification_slot"] == slot
        and report["status"] == STATUS
        and report["budget_sha256"] == BUDGET
        and returned == dict(status=STATUS, report_sha256=sha(raw), verification_slot=slot)
        and report["independent_entry"]["start_ms"]
        <= first
        <= last
        <= report["independent_entry"]["end_ms"]
        and last <= time.time_ns() // 10**6,
        "late/changed independent result cannot be promoted",
    )
    for folder in (FORMAL, FORMAL.with_name(FORMAL.name + "-backup")):
        for name, value in ((PACKAGE, raw), (ACTUAL, actual_raw)):
            try:
                wire.write_private(folder / name, value)
            except FileExistsError:
                need(
                    wire.read_private(folder / name, 16 * 1024**2) == value,
                    "conflicting existing fixed alias",
                )
    need(
        pair(FORMAL, PACKAGE) == raw and pair(FORMAL, ACTUAL) == actual_raw,
        "fixed aliases must retain distinct-inode same bytes",
    )
    need(
        pair(FORMAL, f"closeout-readiness-slot-{slot}.json") == raw
        and pair(DATA, f"released-verification-{slot}-entry.json") == entry_raw,
        "original slot changed during fixed publication",
    )
    return dict(
        package_sha256=sha(raw),
        actual_sha256=sha(actual_raw),
        verified_returned_ms=last,
        verification_slot=slot,
    )
