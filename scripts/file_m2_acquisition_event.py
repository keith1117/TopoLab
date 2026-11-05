"""Canonical actual-call courier and narrow input event compiler, without source IO."""

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = Path('/Users/keith1117/Documents/TopoLab-data/p17-m2-source-binding-v1-20261103T173800Z')
PUBLIC = '/private/tmp/topolab-public-registered-source-acquisition-20261104-v3'
PARENT = '/Users/keith1117/Library/Application Support/TopoLab-custody/'
ROOTS = (
    PUBLIC,
    PARENT + 'p17-m2-local-input-version-v8-strict-binding-20261103',
         PARENT + 'p17-m2-local-input-version-v9-strict-binding-remedy-20261103',
)
NEW_PUBLIC = '/private/tmp/topolab-public-registered3-source-acquisition-20261104-v4'
NEW_ROOTS = (
    NEW_PUBLIC,
    *tuple(
        PARENT + name
        for name in (
    'p17-m2-local-input-version-v10-strict-binding-20261104',
    'p17-m2-local-input-version-v11-strict-binding-remedy-20261104',
        )
    ),
)
V31_PUBLIC = (
    '/private/tmp/topolab-public-registered4-source-acquisition-20261104-v5',
              '/private/tmp/topolab-public-registered4-source-acquisition-20261104-v6',
)
V31_ROOTS = (
    *V31_PUBLIC,
    *tuple(
        PARENT + name
        for name in (
    'p17-m2-local-input-version-v12-strict-binding-20261104',
    'p17-m2-local-input-version-v13-strict-binding-remedy-20261104',
        )
    ),
)

V33_IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v5"
V33_PUBLIC = "/private/tmp/topolab-public-registered5-source-acquisition-20261104-v7"
V33_FORMAL = (
    PARENT + "p17-m2-local-input-version-v14-strict-binding-20261104",
    PARENT + "p17-m2-local-input-version-v15-strict-binding-remedy-20261104",
)
V33_ROOTS = (V33_PUBLIC, *V33_FORMAL)

V35_IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v6"
V35_PUBLIC = "/private/tmp/topolab-public-registered6-source-acquisition-20261104-v7"
V35_FORMAL = (
    PARENT + "p17-m2-local-input-version-v16-strict-binding-20261104",
    PARENT + "p17-m2-local-input-version-v17-strict-binding-remedy-20261104",
)
V35_ROOTS = (V35_PUBLIC, *V35_FORMAL)

IDENTITY = 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v2'


def load():
    spec = importlib.util.spec_from_file_location('m2_event_recovery',
        REPO / 'scripts/p17_m2_source_binding_recovery.py')
    if spec is None or spec.loader is None:
        raise ValueError('frozen recovery helper unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'),
                       ensure_ascii=True, allow_nan=False) + '\n').encode('ascii')


def persist(packet, destination):
    path = Path(destination)
    assert path.is_absolute() and os.path.normpath(destination) == destination
    assert packet["schema"] in (
        "topolab.v2.m2-strict-source-binding.actual-call.v1",
        "topolab.m2-acquisition-caller-failure.v1",
    )
    certificate = path in {
        Path(value) / "certify-rehearsal-raw-actual-call.json"
        for value in (PUBLIC, NEW_PUBLIC, *V31_PUBLIC, V33_PUBLIC, V35_PUBLIC)
    }
    assert path.is_relative_to(EVIDENCE) or certificate, "literal courier path refused"
    raw = canonical(packet)
    assert len(raw) <= 16 * 1024**2
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parent.parts[1:]:
            following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = following
        fd = os.open(
            path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent
        )
        with os.fdopen(fd, "wb") as stream:
            assert stream.write(raw) == len(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def file_event(root, plan_sha, role, mode, path, pin):
    assert root in (*ROOTS, *NEW_ROOTS, *V31_ROOTS, *V33_ROOTS, *V35_ROOTS) and mode in (
        "supervise",
        "record",
    ), "literal root/mode refused"
    recovery = load()
    control = recovery.load("p17_m2_source_acquisition_control")
    identity = IDENTITY
    if root in NEW_ROOTS:
        identity = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v3"
        control = control.for_registered_identity(identity)
    if root in V31_ROOTS:
        identity = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v4"
        control = control.for_registered_identity(identity)
    if root in V33_ROOTS:
        identity = V33_IDENTITY
        control = control.for_registered_identity(identity)
    if root in V35_ROOTS:
        identity = V35_IDENTITY
        control = control.for_registered_identity(identity)
    core = recovery.load("p17_m2_source_binding")
    base = control.base()
    plan, _ = core.read_metadata(
        Path(root) / "plan.json", 16 * 1024**2, expected=plan_sha, canonical_required=True
    )
    assert plan["execution_identity"] == identity
    assert role in [
        *plan["role_order"],
        "final-filing",
        "lease-release",
        "public-consumer",
        "reader-ack",
    ]
    packet, _ = core.read_metadata(Path(path), 16 * 1024**2, expected=pin, canonical_required=True)
    author = (
        (
            "/root/ci_clock_reader_v1"
            if root in V35_ROOTS
            else "/root/permission_remedy_reader_v1"
            if root in V33_ROOTS
            else "/root/binding_route_independent_v1"
        )
        if role.startswith("independent-")
        else "/root"
    )
    argv = control.argv_for(Path(root), mode, plan_sha, role)
    first, last = recovery.exact_actual(packet, argv, author)
    result = packet["responses"][-1]["result"]
    event = {
        "event_id": packet["event_id"],
        "author": author,
        "argv": argv,
        "start_seconds": first / 1000,
        "end_seconds": last / 1000,
        "wall_seconds": (last - first) / 1000,
        "exit_code": result["exit_code"],
        "complete": True,
        "clock_domain": "functions.exec.Date.now.UTC-seconds",
        "raw_packet_sha256": pin,
    }
    folder = Path(root)
    pending = base.read_json(folder / "receipts" / (role + "-pending.json"))
    event["observed_pending_sha256"] = base.sha(base.canonical(pending))
    if mode == "record":
        wire = base.read_json(folder / "receipts" / (role + "-wire.json"))
        returned = "".join(item["result"]["output"] for item in packet["responses"]).encode()
        assert returned == base.canonical(wire), "complete original record buffer differs"
        event["observed_completion_sha256"] = base.sha(base.canonical(wire["completion"]))
        previous = base.read_json(folder / (role + "-supervise-actual-event.json"))
        assert previous["observed_pending_sha256"] == event["observed_pending_sha256"]
        assert previous["end_seconds"] <= event["start_seconds"]
    base.put(folder / (role + "-" + mode + "-actual-event.json"), event)
    if mode == "record":
        base.put(folder / (role + "-events.json"), [previous, event])
    return {
        "status": "ACTUAL_EVENT_FILED",
        "role": role,
        "mode": mode,
        "exit_code": result["exit_code"],
        "new_source_reads": 0,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('persist', 'file'))
    parser.add_argument('--packet-json')
    parser.add_argument('--destination')
    parser.add_argument('--root')
    parser.add_argument('--plan-sha')
    parser.add_argument('--role')
    parser.add_argument('--event-mode')
    parser.add_argument('--packet')
    parser.add_argument('--packet-sha')
    args = parser.parse_args()
    os.umask(0o077)
    if args.mode == 'persist':
        value = persist(json.loads(args.packet_json), args.destination)
    else:
        value = file_event(args.root, args.plan_sha, args.role, args.event_mode,
                           args.packet, args.packet_sha)
    print(json.dumps(value, sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
