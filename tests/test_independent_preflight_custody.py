"""Exercise lossless preflight custody, including the historical key-order mismatch."""

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def custody(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    import independent_preflight_custody as worker
    import paired_readiness_independent as checked
    import r0_read_independent as originals
    import staged_input_filer as filer

    evidence, observation = tmp_path / "formal", tmp_path / "observation"
    for area in (evidence, observation):
        area.mkdir()
        area.with_name(area.name + "-backup").mkdir()
    peers = (evidence, evidence.with_name(evidence.name + "-backup"))
    policy = dict(
        execution_identity=checked.RECEIPT_ID,
        preflight_custody_entry=checked.CUSTODY_ENTRY,
        preparation_entry="receipt_formal_preparation.py",
        independent_preflight_original_path=str(evidence / checked.ORIGINAL),
        readiness_paths=[str(folder / checked.READY) for folder in peers],
        readiness_path=str(evidence / checked.READY),
        readiness_original_actual_path=str(evidence / checked.PREPARED),
        independent_preflight_actual_path=str(evidence / checked.PREFLIGHT),
        readiness_verification_paths=dict(
            package=str(evidence / "readiness-release.json"),
            actual=str(evidence / "readiness-release-actual.json"),
        ),
        actors={"independent": "public-independent"},
        new_input_budget={"path": str(observation / "owner-budget.json")},
        independent_author_start_ms=1,
        global_deadline_ms=9999999999999,
    )
    subject = SimpleNamespace(
        authority=lambda: policy,
        REPO=tmp_path,
        PROTOCOL="protocol",
        IDENTITY=checked.RECEIPT_ID,
        CLI_ENTRY="receipt_formal_registered.py",
        control=SimpleNamespace(
            CONTINUATION_CONFIG={"evidence_root": str(evidence)}, source_freeze=lambda _: {}
        ),
    )
    ready = dict(
        runtime={"python": "/public/python"},
        published_source_sha256={},
        paired_readiness_verification={"source_main": "b" * 40},
    )
    ready.update(actors=policy["actors"], new_input_budget=policy["new_input_budget"])
    readiness = checked.canonical(ready)
    observed = {"attempt": "current"}
    monkeypatch.setattr(checked, "capture", lambda *_: (readiness, observed, 2))
    digest = checked.sha(readiness)
    argv = [
        "/public/python",
        "-I",
        str(tmp_path / "scripts" / subject.CLI_ENTRY),
        "preflight",
        "--readiness-sha",
        digest,
    ]
    request = {"workdir": str(tmp_path), "cmd": originals.literal_command(argv), "extra": "測試"}
    output = checked.canonical(checked.summary(policy, ready, digest, observed)).decode()
    payload = dict(
        schema=originals.ACTUAL_SCHEMA,
        author="public-independent",
        argv=argv,
        request=request,
        responses=[
            dict(
                tool="exec_command",
                arguments=request,
                requested_ms=3,
                returned_ms=4,
                result=dict(output="", session_id=110, wall_time_seconds=0.01),
            ),
            dict(
                tool="write_stdin",
                arguments={"session_id": 110, "chars": ""},
                requested_ms=5,
                returned_ms=6,
                result=dict(output=output, exit_code=0, wall_time_seconds=0.02),
            ),
        ],
    )

    def preserve(packet):
        raw = (json.dumps(packet, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
        for area in (observation, observation.with_name(observation.name + "-backup")):
            filer.write_private(area / checked.ORIGINAL, raw)
        return raw

    return SimpleNamespace(
        worker=worker,
        checked=checked,
        filer=filer,
        subject=subject,
        peers=peers,
        observation=observation,
        packet=payload,
        preserve=preserve,
        audit=lambda: checked.audit_dispatch(
            policy, {}, "protocol", tmp_path, subject.CLI_ENTRY, evidence
        ),
    )


def test_custody_preserves_original_and_files_entry_compatible_bytes(custody, monkeypatch, capsys):
    c = custody
    raw = c.preserve(c.packet)
    canonical = c.checked.canonical(c.packet)
    assert raw != canonical
    monkeypatch.setattr(sys, "argv", ["custody", "--original-sha256", c.checked.sha(raw)])
    c.worker.main((c.subject, c.checked, c.filer.write_private))
    response = json.loads(capsys.readouterr().out)
    assert response["canonical_sha256"] == c.audit() == c.checked.sha(canonical)
    assert response["original_sha256"] == c.checked.sha(raw)
    for folder in c.peers:
        assert (folder / c.checked.ORIGINAL).read_bytes() == raw
        assert c.filer.read_json(folder / c.checked.PREFLIGHT) == (c.packet, canonical)
        (folder / c.checked.PREFLIGHT).write_bytes(raw)
    with pytest.raises(ValueError, match="canonical complete metadata"):
        c.audit()


@pytest.mark.parametrize("defect", ["exit", "stdout", "changed_argv", "original_sha"])
def test_custody_refuses_incomplete_or_unbound_original_before_filing(custody, defect):
    c = custody
    if defect == "exit":
        c.packet["responses"][-1]["result"]["exit_code"] = 1
    if defect == "stdout":
        c.packet["responses"][-1]["result"]["output"] = "{}\n"
    if defect == "changed_argv":
        c.packet["argv"][-1] = "0" * 64
    raw = c.preserve(c.packet)
    expected = "0" * 64 if defect == "original_sha" else c.checked.sha(raw)
    with pytest.raises(ValueError):
        c.worker.retain(c.subject, c.checked, c.filer.write_private, expected)
    assert all(not (folder / c.checked.PREFLIGHT).exists() for folder in c.peers)
    assert (c.observation / c.checked.ORIGINAL).read_bytes() == raw


@pytest.mark.parametrize("conflict", [False, True])
def test_custody_resumes_readback_after_partial_filing(custody, conflict):
    c = custody
    raw = c.preserve(c.packet)
    expected = c.checked.sha(raw)
    first = c.peers[0] / c.checked.ORIGINAL

    def interrupted(path, content):
        if path != first:
            raise OSError("public interruption before second file")
        c.filer.write_private(path, content)

    with pytest.raises(OSError, match="public interruption"):
        c.worker.retain(c.subject, c.checked, interrupted, expected)
    first_stat = first.stat()
    if conflict:
        first.write_bytes(b"conflicting control")
        with pytest.raises(ValueError, match="conflicting preflight custody"):
            c.worker.retain(c.subject, c.checked, c.filer.write_private, expected)
        assert first.read_bytes() == b"conflicting control"
        assert not (c.peers[1] / c.checked.ORIGINAL).exists()
    else:
        response = c.worker.retain(c.subject, c.checked, c.filer.write_private, expected)
        assert response["canonical_sha256"] == c.audit()
        assert (first.stat().st_ino, first.stat().st_mtime_ns) == (
            first_stat.st_ino,
            first_stat.st_mtime_ns,
        )
