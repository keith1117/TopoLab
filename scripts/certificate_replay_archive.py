"""Read the two sealed control archives and rebuild inputs to the formal certificate audit."""

import hashlib
import io
import json
import tarfile
from pathlib import Path

from staged_input_filer import canonical, read_private, validate_terminal

HERE = Path(__file__).resolve().parents[1]
HISTORICAL = Path("/private/tmp/topolab-r1-window-20261123")
DATA = Path("/Users/keith1117/Documents/TopoLab-data/formal-r1-window-20261123")
ARCHIVE = "6a797c9327762298638d2b3f224bd51cbcba46a9f1c24657f818d346c3c3a282"
INDEX = "bb9e396ec42c532a50f195d0a0ab7c0fab19e67c0446447fd1ba05bf3dc7a6a2"
PLAN = "cfbec3406121c55db47eda369a03913c9f74937771ab51d5ef00070711413599"
FAILED = "6d108fb692015e3c9d82a1d6fb8fcec11150bfbfa5f2dbdbf13c45adb6a65fac"
HISTORICAL_MAIN = "96edccd4357472de7ae4565fd3f8494ffe000090"
FAILURE = "ValueError: software closure/source freeze differs"


def need(value, reason):
    if not value:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pair(root, name, maximum=32 * 1024**2):
    a, b = root / name, root.with_name(root.name + "-backup") / name
    raw = read_private(a, maximum)
    need(raw == read_private(b, maximum) and not a.samefile(b), "sealed copies differ: " + name)
    return raw


def controls():
    raw, inventory = pair(DATA, "formal-a1-controls.tar.gz"), pair(DATA, "formal-a1-index.json")
    need(sha(raw) == ARCHIVE and sha(inventory) == INDEX, "wrong historical archive")
    index = json.loads(inventory)
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as sealed:
        members = sealed.getmembers()
        need(
            len(index) == len(members) == 274
            and {m.name for m in members} == set(index)
            and all(m.isfile() and m.size == index[m.name]["bytes"] for m in members)
            and sum(m.size for m in members) <= 32 * 1024**2,
            "archive inventory differs",
        )
        files = {m.name: sealed.extractfile(m).read() for m in members}
    for name, content in files.items():
        need(sha(content) == index[name]["sha256"], "member changed: " + name)
    return files


def historical_inputs(checker):
    from r0_caller_receipt import project

    files = controls()

    def native(name):
        return json.loads(files["native/" + name + ".json"])

    plan = native("plan")
    need(
        sha(canonical(plan)) == PLAN and plan["runtime"]["cwd"] == str(HISTORICAL),
        "wrong historical plan",
    )
    root = plan["root"]
    entry = str(HISTORICAL / "scripts/r1_window_formal_control.py")

    def argv(mode, role):
        return [
            plan["runtime"]["python"],
            "-I",
            entry,
            mode,
            "--root",
            root,
            "--plan-sha",
            PLAN,
            "--role",
            role,
        ]

    def actor_packet(role, stage, actor):
        n = f"caller/r1-window-formal-{actor}-{actor}-{role}-{stage}-actual.json"
        raw = files[n]
        packet = json.loads(raw)
        author = "/root/full60_independent" if actor == "independent" else "/root"
        start, end, code = validate_terminal(packet, argv(stage, role), author, str(HISTORICAL))
        need(code == 0, "unsuccessful original " + n)
        output = "".join(row["result"]["output"] for row in packet["responses"]).encode()
        return packet, sha(raw), start, end, output

    wires, events, results = {}, {}, {}
    for role in [*plan["role_order"], "final-filing", "lease-release"]:
        actor = "independent" if role.startswith("independent-") else "producer"
        receipt = native("receipts/" + role + "-wire")
        accepted = native(role + "-accepted")
        ev = native(role + "-events")
        need(ev == accepted["raw_tool_events"] and len(ev) == 2, "event pair differs")
        for pos, stage in enumerate(("supervise", "record", "bind")):
            packet, raw_sha, first, last, stdout = actor_packet(role, stage, actor)
            if stage != "bind":
                event = ev[pos]
                need(
                    event == native(role + "-" + stage + "-actual-event")
                    and event["event_id"] == packet["event_id"]
                    and event["raw_packet_sha256"] == raw_sha
                    and first == round(event["start_seconds"] * 1000)
                    and last == round(event["end_seconds"] * 1000),
                    "filed return differs",
                )
            if stage == "supervise":
                expected = {"status": "PENDING_EXTERNAL_EXIT", "controller_exit": 0}
            else:
                value = receipt if stage == "record" else accepted["result"]
                expected = project(stage, role, PLAN, value, canonical(value))
            need(stdout == canonical(expected), "original stdout differs: " + role + "/" + stage)
        folder = f"native/receipts/{role}/{role}/"
        rec = json.loads(files[folder + "command.json"])
        inner = dict(
            record=rec,
            profile=files[folder + "command.time"],
            log=files[folder + "command.log"],
            expected_role=role,
            expected_argv=argv("payload", role),
            platform="darwin",
            helper_profiles=checker.sampler_profile_buffers(
                files[folder + "sampler-evidence.jsonl"], rec
            ),
        )
        wires[role] = dict(
            receipt,
            inner_evidence=inner,
            native_profiles={"outer-controller": files[f"native/receipts/{role}-controller.time"]},
        )
        results[role], events[role] = accepted["result"], ev

    failed = files["caller/r1-window-formal-producer-producer-certificate-actual.json"]
    packet = json.loads(failed)
    need(
        sha(failed) == FAILED
        and validate_terminal(
            packet, argv("certify-input-version", "certificate"), "/root", str(HISTORICAL)
        )[2]
        == 1
        and packet["responses"][-1]["result"]["output"].rstrip().endswith(FAILURE),
        "historical certificate failure differs",
    )
    closed = native("closed")
    role_results = {r: results[r] for r in plan["role_order"]}
    need(native("shared-packet")["role_results"] == role_results, "shared result differs")
    bundle = dict(
        schema="topolab.v2.m2-source-acquisition-bundle.v1",
        execution_identity=plan["execution_identity"],
        scope=plan["scope"],
        plan=plan,
        plan_sha256=PLAN,
        contract_sha256=plan["contract_sha256"],
        root=plan["content_root"],
        registry=native("registry"),
        **closed,
        role_views=closed["manifest"]["role_views"],
        roles={r: wires[r] for r in plan["role_order"]},
        shared_packet_sha256=sha(canonical(role_results)),
        filing=wires["final-filing"],
        lease_release_evidence=wires["lease-release"],
        backup=native("backup-proof"),
        setup=native("setup-proof"),
        initial_lease=native("custody-acquired"),
        initial_lease_identity=native("custody-lock-identity"),
        lease=native("lease-release"),
    )
    return bundle, events
