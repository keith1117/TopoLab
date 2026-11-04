"""Bounded exact NEW plan/receipt signalling; native predecessors still re-audit evidence."""

import argparse
import hashlib
import json
import os
import stat
import time
from decimal import Decimal
from pathlib import Path

IDENTITY = 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v2'
PUBLIC = '/private/tmp/topolab-public-registered-source-acquisition-20261104-v3'
PARENT = '/Users/keith1117/Library/Application Support/TopoLab-custody/'
FORMAL = tuple(
    PARENT + name
    for name in (
    'p17-m2-local-input-version-v8-strict-binding-20261103',
    'p17-m2-local-input-version-v9-strict-binding-remedy-20261103',
    )
)
NEW_IDENTITY = 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v3'
NEW_PUBLIC = '/private/tmp/topolab-public-registered3-source-acquisition-20261104-v4'
NEW_FORMAL = tuple(
    PARENT + name
    for name in (
    'p17-m2-local-input-version-v10-strict-binding-20261104',
    'p17-m2-local-input-version-v11-strict-binding-remedy-20261104',
    )
)
V31_IDENTITY = 'topolab.v2.p17-m2-registered-source-acquisition.20261104.v4'
V31_PUBLIC = (
    '/private/tmp/topolab-public-registered4-source-acquisition-20261104-v5',
              '/private/tmp/topolab-public-registered4-source-acquisition-20261104-v6',
)
V31_FORMAL = tuple(
    PARENT + name
    for name in (
    'p17-m2-local-input-version-v12-strict-binding-20261104',
    'p17-m2-local-input-version-v13-strict-binding-remedy-20261104',
    )
)

V33_IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v5"
V33_PUBLIC = "/private/tmp/topolab-public-registered5-source-acquisition-20261104-v7"
V33_FORMAL = (
    PARENT + "p17-m2-local-input-version-v14-strict-binding-20261104",
    PARENT + "p17-m2-local-input-version-v15-strict-binding-remedy-20261104",
)
V33_ROOTS = (V33_PUBLIC, *V33_FORMAL)

ROLES = (
    'independent-public-check',
    'exporter-r0',
    'independent-r0',
         'exporter-r1',
    'independent-r1',
    "shared-closeout",
)


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def milliseconds(seconds):
    value = Decimal(str(seconds)) * 1000
    need(value.is_finite() and value == value.to_integral_value()
         and 0 <= value <= 2**53 - 1, 'exact integer milliseconds required')
    return int(value)


def read_metadata(path):
    """One strict no-follow buffer; this helper never reads a source or payload."""
    fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_mode', 'st_nlink')
    facts = {'path': str(path), 'declared': None, 'before': None, 'after': None,
             'closing': None, 'returned_bytes': None}
    def observed(value):
        return {name: getattr(value, name) for name in fields}
    parent = os.open('/', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in path.parent.parts[1:]:
            following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=parent)
            os.close(parent)
            parent = following
        declared = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        facts['declared'] = observed(declared)
        need(stat.S_ISREG(declared.st_mode) and declared.st_nlink == 1
             and stat.S_IMODE(declared.st_mode) == 0o600
             and 0 <= declared.st_size <= 16 * 1024**2, 'metadata private regular/cap required')
        if declared.st_size == 0:
            raise FileNotFoundError('owned metadata publication has not completed')
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, 'rb') as stream:
            facts['before'] = observed(os.fstat(stream.fileno()))
            raw = stream.read(declared.st_size + 1)
            facts['returned_bytes'] = len(raw)
            facts['after'] = observed(os.fstat(stream.fileno()))
        facts['closing'] = observed(os.stat(path.name, dir_fd=parent, follow_symlinks=False))
        need(facts['declared'] == facts['before'] == facts['after'] == facts['closing']
             and len(raw) == declared.st_size, 'metadata identity/complete closing changed')
        return json.loads(raw, parse_float=Decimal), raw
    except BaseException as error:
        error.wait_metadata_facts = facts
        raise
    finally:
        os.close(parent)


def project(plan, raw, root):
    identity = (
        V33_IDENTITY
        if root in V33_ROOTS
        else V31_IDENTITY
        if root in (*V31_PUBLIC, *V31_FORMAL, *V33_ROOTS)
        else NEW_IDENTITY
        if root in (NEW_PUBLIC, *NEW_FORMAL)
        else IDENTITY
    )
    need(plan.get("execution_identity") == identity, "new execution identity required")
    need(
        plan.get("root") == root
        and plan.get("role_order") == list(ROLES)
        and plan.get("actor_window_seconds") == 4500,
        "exact plan profile/root required",
    )
    formal = root in (*FORMAL, *NEW_FORMAL, *V31_FORMAL, *V33_FORMAL)
    need(
        plan.get("formal_authority") is formal
        and plan.get("scope")
        == (
            "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY"
            if formal
            else "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
        ),
        "exact plan scope required",
    )
    return {
        "root": root,
        "plan_sha256": hashlib.sha256(raw).hexdigest(),
        "execution_identity": identity,
        "scope": plan["scope"],
        "formal_authority": formal,
        "actor_window_seconds": 4500,
        "actor_start_ms": milliseconds(plan["actor_activation_UTC_seconds"]),
        "role_order": list(ROLES),
        "coordination_limit_ms": 240000,
        "applicable_deadline_ms": (
            1793869680000
            if root in V33_FORMAL
            else 1793837617118
            if root == V33_PUBLIC
            else 1793849880000
            if root in V31_FORMAL
            else 1793818000406
            if root in V31_PUBLIC
            else 1793828280000
            if formal
            else 1793810821805
            if root == NEW_PUBLIC
            else 1793796540022
        ),
    }


def role_projection(accepted, plan_sha, role, *, identity=IDENTITY):
    proof = accepted.get('result', {})
    events = accepted.get('raw_tool_events', [])
    need(proof.get('full_role_evidence_accepted') is True
         and proof.get('evidence_complete') is True and proof.get('role') == role
         and proof.get('execution_identity') == identity
         and proof.get('plan_sha256') == plan_sha and proof.get('actual_exit_codes') == [0, 0]
         and isinstance(events, list) and len(events) == 2
         and all(event.get('complete') is True and event.get('exit_code') == 0
                 and event.get('clock_domain') == 'functions.exec.Date.now.UTC-seconds'
                 for event in events), 'actual accepted predecessor required')
    first, last = milliseconds(events[0]['start_seconds']), milliseconds(events[-1]['end_seconds'])
    need(first == milliseconds(proof['T0']) and last == milliseconds(proof['T1'])
         and first <= last, 'actual accepted endpoints differ')
    return {'role': role, 'T0_ms': first, 'T1_ms': last, 'accepted': True,
            'complete': True, 'actual_exit_codes': [0, 0], 'signal_only': True}


def wait(root, role, seconds):
    need(
        root in (PUBLIC, *FORMAL, NEW_PUBLIC, *NEW_FORMAL, *V31_PUBLIC, *V31_FORMAL, *V33_ROOTS)
        and os.path.normpath(root) == root,
        "exact literal root required",
    )
    need(type(seconds) is int and 1 <= seconds <= 160, "bounded wait maximum160 seconds")
    need(role == "plan" or role in ROLES, "exact receipt role required")
    end = time.monotonic() + seconds
    while True:
        try:
            plan, raw = read_metadata(Path(root) / "plan.json")
            projection = project(plan, raw, root)
            if role == "plan":
                return {"plan": projection, "proofs": [], "source_or_payload_reads": 0}
            proofs = []
            for name in ROLES[: ROLES.index(role) + 1]:
                value, _ = read_metadata(Path(root) / (name + "-accepted.json"))
                proofs.append(
                    role_projection(
                        value,
                        projection["plan_sha256"],
                        name,
                        identity=projection["execution_identity"],
                    )
                )
            return {"plan": projection, "proofs": proofs, "source_or_payload_reads": 0}
        except FileNotFoundError:
            if time.monotonic() >= end:
                raise TimeoutError("bounded receipt wait expired") from None
            time.sleep(min(0.05, max(0, end - time.monotonic())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--role', required=True)
    parser.add_argument('--timeout-seconds', type=int, default=160)
    args = parser.parse_args()
    print(json.dumps(wait(args.root, args.role, args.timeout_seconds),
                     sort_keys=True, separators=(',', ':')))


if __name__ == '__main__':
    main()
