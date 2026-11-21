"""Bounded metadata I/O for the staged public registration and historical replay."""

import hashlib
import os
import stat
from pathlib import Path

from p17_m2_content_verified_control import nofollow_directory
from p17_m2_input_export import canonical, need, parse, sha

REPO = Path(__file__).resolve().parents[1]
RUNTIME = Path("/private/tmp/topolab-staged-input-20261121")
DATA = Path("/Users/keith1117/Documents/TopoLab-data")
E = DATA / "staged-input-acceptance-20261121"
B = E.with_name(E.name + "-backup")
OLD = DATA / "metadata-input-acceptance-20261121"
ARCHIVE = DATA / "exporter-r1-throughput-20261121"
POLICY = REPO / "docs/planning/staged_public_binding_contract.json"
CAP = 16 * 1024**2
FIELDS = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
SECURITY = ("st_uid", "st_mode", "st_nlink")


def attributes(value, keys):
    return {key: getattr(value, key) for key in keys}


def bounded(path, pin=None):
    parent = nofollow_directory(path.parent)
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        with os.fdopen(os.open(path.name, flags, dir_fd=parent), "rb") as stream:
            first = os.fstat(stream.fileno())
            need(
                stat.S_ISREG(first.st_mode) and first.st_nlink == 1 and 0 < first.st_size <= CAP,
                "bounded regular metadata required",
            )
            raw = stream.read(first.st_size + 1)
            last = os.fstat(stream.fileno())
        closing = nofollow_directory(path.parent)
        try:
            current = os.stat(path.name, dir_fd=closing, follow_symlinks=False)
        finally:
            os.close(closing)
        need(
            len(raw) == first.st_size
            and attributes(first, FIELDS + SECURITY)
            == attributes(last, FIELDS + SECURITY)
            == attributes(current, FIELDS + SECURITY),
            "metadata changed during read",
        )
        need(pin is None or sha(raw) == pin, "pinned metadata differs: " + path.name)
        return raw, (first.st_dev, first.st_ino)
    finally:
        os.close(parent)


def receipt(path, pin=None):
    return parse(bounded(path, pin)[0])


def pair(root, relative, pin=None):
    a, first = bounded(root / relative, pin)
    b, second = bounded(root.with_name(root.name + "-backup") / relative, pin)
    need(first != second and a == b, "independent-inode evidence pair differs")
    return a


def write_new(path, value):
    raw = canonical(value)
    need(len(raw) <= CAP, "metadata creation exceeds byte limit")
    parent = nofollow_directory(path.parent)
    try:
        flags = os.O_EXCL | os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW
        with os.fdopen(os.open(path.name, flags, 0o600, dir_fd=parent), "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)
    return sha(raw)


def write_pair(relative, value):
    digest = write_new(E / relative, value)
    write_new(B / relative, value)
    pair(E, relative, digest)
    return digest


def policy():
    return parse(POLICY.read_bytes())


def frozen_formal(*, certificate_raw=None, finalize_actual_raw=None):
    pins = policy()["old_formal_admission"]
    stage = parse(pair(OLD, "metadata-stage-accepted-a1.json", pins["acceptance_sha256"]))
    cert = pair(OLD, "formal-metadata-certificate-a1.json", pins["certificate_sha256"])
    final = pair(
        OLD, "metadata-formal-a1/finalize-result-raw-actual-call.json", pins["actual_sha256"]
    )
    need(
        (certificate_raw is None or certificate_raw == cert)
        and (finalize_actual_raw is None or finalize_actual_raw == final),
        "historical buffers differ",
    )
    envelope, actual = parse(cert), parse(final)
    attestation = stage["captures"]["formal"]
    need(
        stage["status"] == "FORMAL_METADATA_ACCEPTED"
        and stage["source_main"] == pins["main"]
        and attestation["bindings"] == 23
        and attestation["certificate_sha256"] == pins["certificate_sha256"]
        and attestation["finalize_actual_sha256"] == pins["actual_sha256"]
        and attestation["finalizer_returned_ms"] == actual["responses"][-1]["returned_ms"],
        "historical admission mismatch",
    )
    return envelope, actual


def verified_formal_registration(*, certificate_raw=None, finalize_actual_raw=None):
    envelope, actual = frozen_formal(
        certificate_raw=certificate_raw, finalize_actual_raw=finalize_actual_raw
    )
    certificate = envelope["core_bundle"]["certificate"]
    stdout = parse("".join(row["result"]["output"] for row in actual["responses"]).encode())
    need(
        stdout["sha256"] == policy()["old_formal_admission"]["certificate_sha256"]
        and stdout["bindings"] == len(certificate["bindings"]) == 23
        and certificate["scope"] == "FORMAL_STRICT_BINDING_REGISTRATION_ONLY"
        and actual["responses"][-1]["result"]["exit_code"] == 0,
        "historical finalizer differs",
    )
    return certificate["registered_context"], certificate["source_observations"]


def replay_historical():
    """Run only the frozen, metadata-only verifier, on its original source tree."""
    import types

    env, actual = frozen_formal()
    plan = env["metadata_plan"]
    checkout = Path(plan["runtime"]["cwd"])
    need(checkout == Path("/private/tmp/topolab-meta-input-20261121"), "historical cwd differs")
    tree = plan["context"]["source_tree"]
    for name, digest in tree.items():
        need(
            hashlib.sha256((checkout / name).read_bytes()).hexdigest() == digest,
            "historical verifier source differs",
        )
    entry_path = checkout / "scripts/binding_recovery_20261121.py"
    entry = types.ModuleType("historical_formal_metadata_only")
    entry.__file__ = str(entry_path)
    raw = entry_path.read_bytes()
    need(sha(raw) == tree["scripts/binding_recovery_20261121.py"], "historical entry differs")
    exec(compile(raw, str(entry_path), "exec"), entry.__dict__)
    recovery = entry.bootstrap()
    certificate, proof = recovery.verify_registration(env, actual, kind="formal")
    need(
        len(certificate["bindings"]) == 23 and proof["full_role_evidence_accepted"] is True,
        "historical metadata replay rejected",
    )
    return {
        "bindings": 23,
        "audit_T1": proof["T1"],
        "source_reads": 0,
        "pins": policy()["old_formal_admission"],
    }
