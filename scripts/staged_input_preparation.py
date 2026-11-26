"""Retain the staged November 21 public input proof and prepare the independent preflight.

The first invocation writes the two closure copies. The second binds that
invocation's actual tool return to the readiness file. All paths come from the
published input contract. Neither command reads original input or formal custody.
"""

import argparse
import hashlib
import os
import runpy
import stat
import sys
import time
from pathlib import Path

ENTRY = Path(__file__).resolve()


def public_proof(subject, policy):
    subject.public_stop_veto()
    root = Path(policy["public_roots"][0])
    checker = subject.control.load("p17_m2_source_acquisition_independent")
    producer = subject.producer
    path = root / "accepted-acquisition-bundle.json"
    raw = checker.native._software_bytes(path)
    accepted = subject.control.base().evidence_json(producer.parse(raw), decode=True)
    checker.audit_certificate(accepted["bundle"], trusted_tool_events=accepted["events"])
    plan = accepted["bundle"]["plan"]
    subject.need(
        plan["root"] == str(root)
        and plan["execution_identity"] == subject.IDENTITY
        and plan["scope"] == subject.control.REHEARSAL_SCOPE
        and plan["source_tree"] == subject.control.source_freeze(subject.IDENTITY),
        "published public graph source, scope or root differs",
    )
    cert_path = root / policy["public_certificate_actual_name"]
    packet = checker.native._software_bytes(cert_path)
    actual = producer.parse(packet)
    recovery = subject.control.load("p17_m2_source_binding_recovery")
    argv = subject.control.argv_for(
        root, "certify-rehearsal", producer.sha(producer.canonical(plan)), "certificate"
    )
    first, last = recovery.exact_actual(actual, argv, policy["actors"]["executor"])
    expected = {
        "scope": subject.control.REHEARSAL_SCOPE,
        "formal_authority": False,
        "source_input_accepted": False,
        "formal_or_scientific_admission": False,
        "B_C_admission": False,
        "member_count": len(accepted["bundle"]["manifest"]["members"]),
        "version_id": accepted["bundle"]["version_id"],
    }
    subject.need(
        first
        >= max(ev["end_seconds"] * 1000 for events in accepted["events"].values() for ev in events)
        and last <= plan["whole_end_ms"]
        and last <= policy["global_deadline_ms"]
        and "".join(row["result"]["output"] for row in actual["responses"]).encode()
        == producer.canonical(expected),
        "public certificate return differs",
    )
    return (
        {"path": str(path), "sha256": producer.sha(raw)},
        {"path": str(cert_path), "sha256": producer.sha(packet)},
        last,
    )


def readiness_copy(subject, path, written, expected):
    """Reopen the closed file and bind its returned bytes to the exclusive write."""
    base = subject.control.base()
    parent = base.nofollow_directory(path.parent)
    try:
        flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW
        with os.fdopen(os.open(path.name, flags, dir_fd=parent), "rb") as stream:
            opened = os.fstat(stream.fileno())
            subject.need(
                stat.S_ISREG(opened.st_mode) and stat.S_IMODE(opened.st_mode) == 0o600
                and opened.st_uid == os.geteuid() and opened.st_nlink == 1
                and opened.st_size == len(expected) and base.physical(opened) == written,
                "readiness readback differs from the exclusive write",
            )
            raw = stream.read(len(expected) + 1)
            last = os.fstat(stream.fileno())
        closing_parent = base.nofollow_directory(path.parent)
        try:
            named = os.stat(path.name, dir_fd=closing_parent, follow_symlinks=False)
        finally:
            os.close(closing_parent)
    finally:
        os.close(parent)
    fields = (*written, "st_uid", "st_mode", "st_nlink")
    identity = {key: getattr(opened, key) for key in fields}
    subject.need(
        raw == expected and all(getattr(last, key) == getattr(named, key) == value
                                for key, value in identity.items()),
        "readiness file changed during readback",
    )
    return {"path": str(path), "sha256": subject.producer.sha(raw), **identity}


def prepare(subject, mode, *, entry=ENTRY):
    subject.public_stop_veto()
    policy = subject.authority()

    def within_budget():
        now = time.time_ns() // 1_000_000
        subject.need(
            policy["independent_author_start_ms"] <= now <= policy["global_deadline_ms"],
            "input preparation outside registered window",
        )

    within_budget()
    base = subject.control.base()
    producer = subject.producer
    profiles = subject.control.load("p17_m2_input_continuation")
    historical = subject.IDENTITY in profiles.FORMAL_ONLY_IDENTITIES
    public, certificate, public_end = (subject.prior_public_proof(policy) if historical
                                       else public_proof(subject, policy))
    tree = subject.control.source_freeze(subject.IDENTITY)
    proof_spec = profiles.PROOF_MODULES.get(subject.IDENTITY)
    verification = (subject.control.load(proof_spec[1]).verified_readiness(policy, tree)
                    if proof_spec else None)
    paths = policy["preparation_closure_paths"]
    runtime = base.runtime()
    argv = [runtime["python"], "-I", str(entry), "retain"]
    closure = {
        "schema": "topolab.registered-input.preparation-closure.v1",
        "execution_identity": subject.IDENTITY,
        "source_tree": tree,
        "public_native_acceptance": public,
        "new_input_budget": policy["new_input_budget"],
        "status": "COMPLETE_SOFTWARE_ONLY",
        "own_future_return": "NOT_CLAIMED",
        "retention_argv": argv,
    }
    if historical:
        closure["prior_public"] = policy["prior_public"]
    if proof_spec:
        closure[proof_spec[0]] = verification
    digest = producer.sha(producer.canonical(closure))
    summary = {
        "status": "REGISTERED_INPUT_PREPARATION_PAIR_RETAINED",
        "closure_paths": paths,
        "sha256": digest,
        "own_future_return": "NOT_CLAIMED",
    }
    pins = [{"path": p, "sha256": digest} for p in paths]
    subject.need(len(paths) == 2 and paths[0] != paths[1], "two distinct closure paths required")
    if mode == "retain":
        for path in paths:
            within_budget()
            base.put(Path(path), closure)
    subject.need(
        len(paths) == 2
        and all(subject._read_pin(pin) == closure for pin in pins)
        and not os.path.samefile(paths[0], paths[1]),
        "public preparation pair differs",
    )
    if mode == "retain":
        return summary
    checker = subject.control.load("p17_m2_source_acquisition_independent")
    path = Path(policy["preparation_retention_actual_path"])
    raw = checker.native._software_bytes(path)
    packet = producer.parse(raw)
    recovery = subject.control.load("p17_m2_source_binding_recovery")
    first, last = recovery.exact_actual(packet, argv, policy["actors"]["executor"])
    subject.need(
        public_end <= first <= last <= policy["global_deadline_ms"]
        and "".join(row["result"]["output"] for row in packet["responses"]).encode()
        == producer.canonical(summary),
        "public preparation actual return differs",
    )
    ready = {
        "schema": "topolab.registered-input.activation-readiness.v1",
        "execution_identity": subject.IDENTITY,
        "actors": policy["actors"],
        "published_source_sha256": {k: v for k, v in tree.items() if k != subject.PROTOCOL},
        "runtime": {k: v for k, v in runtime.items() if k != "orig_argv"},
        "new_input_budget": policy["new_input_budget"],
        "public_native_acceptance": public,
        "public_certificate_actual": certificate,
        "preparation_closure_paths": paths,
        "preparation_closure_sha256": digest,
        "preparation_retention_actual": {"path": str(path), "sha256": producer.sha(raw)},
    }
    if historical:
        ready["prior_public"] = policy["prior_public"]
    if proof_spec:
        subject.need(verification["verified_returned_ms"] <= first,
                     "read verification after retain")
        ready[proof_spec[0]] = verification
    within_budget()
    if "readiness_paths" in policy:
        copies = policy["readiness_paths"]
        subject.need(
            isinstance(copies, list) and len(copies) == 2 and copies[0] == policy["readiness_path"]
            and copies[0] != copies[1] and all(
                isinstance(name, str) and Path(name).is_absolute() and str(Path(name)) == name
                and ".." not in Path(name).parts for name in copies),
            "two distinct absolute readiness paths required",
        )
        contract = subject.authority_raw()
        contract_sha = producer.sha(contract)
        subject.need(producer.parse(contract) == policy and tree[subject.PROTOCOL] == contract_sha,
                     "readiness contract differs from frozen software")
        ready.update(contract_sha256=contract_sha, source_tree=tree, readiness_paths=copies,
                     target=policy["fixed_target"]["attempts"]["1"]["generation"])
        expected = producer.canonical(ready)
        written = []
        for name in copies:
            within_budget()
            written.append(base.put(Path(name), ready))
        records = [readiness_copy(subject, Path(name), identity, expected)
                   for name, identity in zip(copies, written, strict=True)]
        subject.need(len({(r["st_dev"], r["st_ino"]) for r in records}) == 2,
                     "readiness copies share a physical file")
        within_budget()
        return {"path": copies[0], "sha256": producer.sha(expected), "readiness_copies": records}
    base.put(Path(policy["readiness_path"]), ready)
    return {"path": policy["readiness_path"], "sha256": producer.sha(producer.canonical(ready))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("retain", "readiness"))
    args = parser.parse_args()
    if sys.flags.isolated != 1 or Path.cwd() != ENTRY.parents[1]:
        raise ValueError("preparation requires the isolated checkout interpreter")
    source_sha = hashlib.sha256(ENTRY.read_bytes()).hexdigest()
    subject = runpy.run_path(str(ENTRY.with_name("staged_registered_input.py")))["subject"]
    sys.modules["full60_input_loader"].loaded_source_sha256[str(ENTRY)] = source_sha
    print(subject.producer.canonical(prepare(subject, args.mode)).decode("ascii"), end="")


if __name__ == "__main__":
    main()
