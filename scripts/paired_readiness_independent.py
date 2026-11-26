"""Independently read and bind the two activation documents and original tool returns."""

import os
import stat
import time
from pathlib import Path

from certificate_replay_proof import checkout_commit
from r0_read_independent import canonical, need, parse, sha, terminal
from staged_input_filer import MAX_BYTES, parent_fd

PHYSICAL = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_uid", "st_mode", "st_nlink")
READY = "input-activation-readiness-a1.json"
PREPARED = "input-readiness-original-return-a1.json"
PREFLIGHT = "input-preflight-actual-a1.json"
ORIGINAL = "input-preflight-original-a1.json"
CUSTODY_ENTRY = "independent_preflight_custody.py"
RECEIPT_ID = "topolab.v2.p17-m2-registered-source-acquisition.receipt-20261126-b1.v1"
PREPARATION_ENTRY = "readiness_formal_preparation.py"


def physical(info):
    return {name: getattr(info, name) for name in PHYSICAL}


def private_read(path):
    parent = parent_fd(path)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            first = os.fstat(stream.fileno())
            need(
                stat.S_ISREG(first.st_mode)
                and stat.S_IMODE(first.st_mode) == 0o600
                and first.st_uid == os.getuid()
                and first.st_nlink == 1
                and 0 < first.st_size <= MAX_BYTES,
                "private readiness file identity/size",
            )
            raw = stream.read(first.st_size + 1)
            observed = physical(first)
            need(observed == physical(os.fstat(stream.fileno())), "readiness changed during read")
        closing_parent = parent_fd(path)
        try:
            need(
                os.path.samestat(os.fstat(parent), os.fstat(closing_parent))
                and observed
                == physical(os.stat(path.name, dir_fd=closing_parent, follow_symlinks=False))
                and len(raw) == first.st_size,
                "readiness changed at close",
            )
        finally:
            os.close(closing_parent)
        return raw, dict(path=str(path), sha256=sha(raw), **observed)
    finally:
        os.close(parent)


def pair(evidence, name):
    left, right = (
        directory / name for directory in (evidence, evidence.with_name(evidence.name + "-backup"))
    )
    raw, a = private_read(left)
    peer, b = private_read(right)
    need(
        raw == peer and (a["st_dev"], a["st_ino"]) != (b["st_dev"], b["st_ino"]),
        "readiness control copies differ",
    )
    return raw, [a, b]


def uses_canonical_preflight(policy):
    return policy.get("execution_identity") == RECEIPT_ID or "preflight_custody_entry" in policy


def require_policy_paths(policy, evidence):
    evidence = Path(evidence)
    peer = evidence.with_name(evidence.name + "-backup")
    need(
        policy.get("readiness_path") == str(evidence / READY)
        and policy.get("readiness_paths") == [str(evidence / READY), str(peer / READY)]
        and policy.get("readiness_original_actual_path") == str(evidence / PREPARED)
        and policy.get("independent_preflight_actual_path") == str(evidence / PREFLIGHT)
        and policy.get("readiness_verification_paths")
        == dict(
            package=str(evidence / "readiness-release.json"),
            actual=str(evidence / "readiness-release-actual.json"),
        ),
        "paired readiness authority requires all literal paths",
    )
    if uses_canonical_preflight(policy):
        need(
            policy.get("preflight_custody_entry") == CUSTODY_ENTRY
            and policy.get("preparation_entry") == "receipt_formal_preparation.py"
            and policy.get("independent_preflight_original_path") == str(evidence / ORIGINAL),
            "fixed preflight custody and original evidence paths required",
        )


def capture(policy, tree, protocol, repo, evidence):
    """Return the same bytes used to check the CLI expectation and full ready schema."""
    evidence = Path(evidence)
    raw, copies = pair(evidence, READY)
    paths = [copy["path"] for copy in copies]
    ready = parse(raw)
    digest = sha(raw)
    contract_sha = sha((repo / protocol).read_bytes())
    target = policy["fixed_target"]["attempts"]["1"]["generation"]
    need(
        paths == policy["readiness_paths"] == ready.get("readiness_paths")
        and paths[0] == policy["readiness_path"]
        and raw == canonical(ready)
        and ready.get("execution_identity") == policy["execution_identity"]
        and ready.get("new_input_budget") == policy["new_input_budget"]
        and ready.get("actors") == policy["actors"]
        and ready.get("source_tree") == tree
        and ready.get("target") == target
        and tree[protocol] == ready.get("contract_sha256") == contract_sha
        and ready.get("published_source_sha256")
        == {k: v for k, v in tree.items() if k != protocol},
        "readiness contract/target/release binding differs",
    )
    main = checkout_commit(repo)
    need(
        ready["paired_readiness_verification"]["source_main"] == main,
        "readiness release commit differs",
    )
    prepared, _ = pair(evidence, PREPARED)
    need(
        policy["readiness_original_actual_path"] == str(evidence / PREPARED),
        "readiness preparation receipt location differs",
    )
    start, end, output = terminal(
        parse(prepared),
        [
            ready["runtime"]["python"],
            "-I",
            str(
                repo
                / "scripts"
                / (
                    policy["preparation_entry"]
                    if uses_canonical_preflight(policy)
                    else PREPARATION_ENTRY
                )
            ),
            "readiness",
        ],
        cwd=str(repo),
        author=policy["actors"]["executor"],
        window=(policy["independent_author_start_ms"], policy["global_deadline_ms"]),
        full=None,
    )
    need(
        output == canonical(dict(path=paths[0], sha256=digest, readiness_copies=copies))
        and ready["paired_readiness_verification"]["verified_returned_ms"] <= start
        and end <= time.time_ns() // 1_000_000,
        "original readiness return differs from both reopened files",
    )
    observed = dict(
        readiness_copies=copies,
        contract_sha256=contract_sha,
        target=target,
        readiness_paths=paths,
        source_main=main,
        preparation_readiness_actual_sha256=sha(prepared),
    )
    return raw, observed, end


def summary(policy, ready, digest, observed):
    return dict(
        status="PASS_REGISTERED_INPUT_METADATA_PREFLIGHT",
        execution_identity=policy["execution_identity"],
        author=policy["actors"]["independent"],
        readiness_path=policy["readiness_path"],
        readiness_sha256=digest,
        published_source_sha256=ready["published_source_sha256"],
        runtime=ready["runtime"],
        actors=ready["actors"],
        new_input_budget=ready["new_input_budget"],
        source_stat_reads=0,
        target_stat_reads=0,
        own_future_return="NOT_CLAIMED",
        paired_readiness=observed,
        paired_readiness_verification=ready["paired_readiness_verification"],
    )


def validate_preflight(policy, repo, input_entry, captured, packet):
    """Replay the complete original tool rows against the current readiness documents."""
    raw, observed, prepared_end = captured
    ready, digest = parse(raw), sha(raw)
    argv = [
        ready["runtime"]["python"],
        "-I",
        str(repo / "scripts" / input_entry),
        "preflight",
        "--readiness-sha",
        digest,
    ]
    start, end, output = terminal(
        packet,
        argv,
        cwd=str(repo),
        author=policy["actors"]["independent"],
        window=(prepared_end, policy["global_deadline_ms"]),
        full=None,
    )
    need(
        prepared_end <= start <= end <= time.time_ns() // 1_000_000
        and output == canonical(summary(policy, ready, digest, observed)),
        "original independent preflight disagrees with readiness pair",
    )


def observation_directory(policy):
    return Path(policy["new_input_budget"]["path"]).parent


def audit_dispatch(policy, tree, protocol, repo, input_entry, evidence):
    """Require the same original and exact bytes the filing entry will consume."""
    from staged_input_filer import read_json

    repo, evidence = Path(repo), Path(evidence)
    captured = capture(policy, tree, protocol, repo, evidence)
    need(
        policy["independent_preflight_actual_path"] == str(evidence / PREFLIGHT),
        "independent preflight location differs",
    )
    if uses_canonical_preflight(policy):
        require_policy_paths(policy, evidence)
        # This is the formal entry's actual canonical file reader. Its bytes must
        # reproduce every original field, including unmodified tool-output strings.
        packet_raw, _ = pair(evidence, PREFLIGHT)
        packet, _ = read_json(evidence / PREFLIGHT, sha(packet_raw))
        original, _ = pair(observation_directory(policy), ORIGINAL)
        archived_original, _ = pair(evidence, ORIGINAL)
        need(
            original == archived_original and canonical(parse(original)) == packet_raw,
            "canonical preflight disagrees with preserved original packet",
        )
    else:
        packet_raw, _ = pair(evidence, PREFLIGHT)
        packet = parse(packet_raw)
    validate_preflight(policy, repo, input_entry, captured, packet)
    return sha(packet_raw)
