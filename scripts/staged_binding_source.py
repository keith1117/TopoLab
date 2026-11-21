"""Producer observation of the newly staged public fixture's 23 physical anchors."""

import os
import stat
from pathlib import Path

from p17_m2_content_verified_control import nofollow_directory
from p17_m2_input_export import canonical, need, sha
from p17_m2_source_binding import whitelist
from staged_binding_evidence import ARCHIVE, FIELDS, SECURITY, attributes, policy, receipt


def expectations():
    p = policy()
    # Use the archived candidate receipt for replay, including on machines where
    # the Library source is no longer available after an accepted read.
    candidate = receipt(ARCHIVE / "staged-source-candidate.json", p["candidate_sha256"])
    index = receipt(ARCHIVE / "public-benchmark-scene-index.json", p["index_sha256"])
    refs = {name[7:]: value for name, value in index["files"].items() if name.startswith("source/")}
    need(
        candidate["source"] == p["source"]
        and candidate["archive_sha256"] == index["archive_sha256"]
        and len(refs) == candidate["source_files"] == 598
        and sha(canonical(refs)) == candidate["file_manifest_sha256"] == p["manifest_sha256"],
        "staged public candidate and source index differ",
    )
    return {item["path"]: tuple(refs[item["path"]]) for item in whitelist()}


def scan(source, expected, *, availability):
    specs = whitelist()
    need(
        len(specs) == 23 and set(expected) == {s["path"] for s in specs},
        "producer requires the exact 23 anchors",
    )
    rows = []
    for spec in specs:
        relative = spec["path"]
        path = source / relative
        row = {"path": relative, "sha256": None}
        rows.append(row)
        try:
            parent = nofollow_directory(path.parent)
            try:
                first = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
                row["declared"] = attributes(first, FIELDS + SECURITY)
                size, expected_sha = expected[relative]
                need(
                    stat.S_ISREG(first.st_mode)
                    and stat.S_IMODE(first.st_mode) == 0o600
                    and first.st_uid == os.geteuid()
                    and first.st_nlink == 1
                    and 0 < first.st_size == size <= spec["max_bytes"],
                    "producer source type, owner, permissions or size differs",
                )
                flags = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW
                with os.fdopen(os.open(path.name, flags, dir_fd=parent), "rb") as stream:
                    row["before"] = attributes(os.fstat(stream.fileno()), FIELDS + SECURITY)
                    need(row["before"] == row["declared"], "opened source differs")
                    if not availability:
                        raw = stream.read(size + 1)
                        row["sha256"] = sha(raw)
                        need(
                            len(raw) == size and row["sha256"] == expected_sha,
                            "producer exact content differs",
                        )
                    row["after"] = attributes(os.fstat(stream.fileno()), FIELDS + SECURITY)
                fresh = nofollow_directory(path.parent)
                try:
                    need(
                        os.path.samestat(os.fstat(parent), os.fstat(fresh)),
                        "source directory replaced",
                    )
                    closing = os.stat(path.name, dir_fd=fresh, follow_symlinks=False)
                    row["closing"] = attributes(closing, FIELDS + SECURITY)
                finally:
                    os.close(fresh)
            finally:
                os.close(parent)
            need(
                row["declared"] == row["after"] == row["closing"],
                "source physical identity changed",
            )
            row["physical"] = attributes(first, FIELDS)
        except BaseException as exc:
            exc.binding_prefix = rows
            raise
    return rows


def check_candidate():
    p = policy()
    source = Path(p["source"])
    from p17_m2_source_acquisition_control import local_filesystem

    receipt(source.parent / "candidate.json", p["candidate_sha256"])
    fd = nofollow_directory(source)
    try:
        volume = local_filesystem(fd)
        need(
            volume["local_filesystem"] and volume["filesystem"] == "apfs",
            "fixed staged source requires the registered local APFS volume",
        )
    finally:
        os.close(fd)
    return source
