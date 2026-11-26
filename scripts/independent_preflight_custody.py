"""Retain the original b1 preflight packet and file its lossless canonical representation."""

import argparse
import re
import runpy
import sys
from pathlib import Path


def retain(subject, verifier, writer, expected_original_sha):
    policy = subject.authority()
    repo = Path(subject.REPO)
    evidence = Path(subject.control.CONTINUATION_CONFIG["evidence_root"])
    verifier.require_policy_paths(policy, evidence)
    verifier.need(
        verifier.uses_canonical_preflight(policy), "canonical preflight contract required"
    )
    verifier.need(
        re.fullmatch("[0-9a-f]{64}", expected_original_sha),
        "literal preflight original SHA-256 required",
    )
    original, source_copies = verifier.pair(
        verifier.observation_directory(policy), verifier.ORIGINAL
    )
    verifier.need(verifier.sha(original) == expected_original_sha, "original preflight SHA differs")
    packet = verifier.parse(original)
    tree = subject.control.source_freeze(subject.IDENTITY)
    captured = verifier.capture(policy, tree, subject.PROTOCOL, repo, evidence)
    verifier.validate_preflight(policy, repo, subject.CLI_ENTRY, captured, packet)
    canonical = verifier.canonical(packet)
    for name, content in ((verifier.ORIGINAL, original), (verifier.PREFLIGHT, canonical)):
        for directory in (evidence, evidence.with_name(evidence.name + "-backup")):
            path = directory / name
            try:
                writer(path, content)
            except FileExistsError:
                retained, _ = verifier.private_read(path)
                verifier.need(retained == content, f"conflicting preflight custody file: {path}")
    canonical_sha = verifier.audit_dispatch(
        policy, tree, subject.PROTOCOL, repo, subject.CLI_ENTRY, evidence
    )
    verifier.need(canonical_sha == verifier.sha(canonical), "filed preflight digest differs")
    return {
        "status": "CANONICAL_PREFLIGHT_AND_ORIGINAL_RETAINED",
        "original_sha256": expected_original_sha,
        "canonical_sha256": canonical_sha,
        "observation_copies": source_copies,
        "original_copies": verifier.pair(evidence, verifier.ORIGINAL)[1],
        "canonical_copies": verifier.pair(evidence, verifier.PREFLIGHT)[1],
    }


def main(dependencies=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--original-sha256", required=True)
    args = parser.parse_args()
    if dependencies is None:
        entry = Path(__file__).resolve()
        if not sys.flags.isolated or Path.cwd() != entry.parents[1]:
            raise ValueError("custody requires the isolated checkout interpreter")
        subject = runpy.run_path(str(entry.with_name("receipt_formal_registered.py")))["subject"]
        loader = sys.modules["full60_input_loader"]
        loader.loaded_source_sha256[str(entry)] = loader.hashlib.sha256(
            entry.read_bytes()
        ).hexdigest()
        verifier = subject.control.load("paired_readiness_independent")
        writer = subject.control.load("staged_input_filer").write_private
    else:
        subject, verifier, writer = dependencies
    print(
        verifier.canonical(retain(subject, verifier, writer, args.original_sha256)).decode(), end=""
    )


if __name__ == "__main__":
    main()
