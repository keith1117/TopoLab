"""Public local controls for the independent paired-document gate."""

import importlib
import os
from pathlib import Path

import pytest


@pytest.fixture
def verifier(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("paired_readiness_independent")


def fixture(verifier, tmp_path):
    repo = tmp_path / "checkout"
    repo.mkdir()
    (repo / ".git").mkdir()
    main = "a" * 40
    (repo / ".git/HEAD").write_text(main)
    protocol = "policy.json"
    evidence, backup = tmp_path / "controls", tmp_path / "controls-backup"
    for directory in (evidence, backup):
        directory.mkdir()
    paths = [str(root / verifier.READY) for root in (evidence, backup)]
    policy = dict(
        readiness_paths=paths,
        readiness_path=paths[0],
        execution_identity="fixture.2",
        new_input_budget={"sha256": "b" * 64},
        fixed_target={"attempts": {"1": {"generation": "new"}}},
        actors={"executor": "A", "independent": "B"},
        independent_author_start_ms=1,
        global_deadline_ms=9999999999999,
        readiness_original_actual_path=str(evidence / verifier.PREPARED),
        independent_preflight_actual_path=str(evidence / verifier.PREFLIGHT),
    )
    raw_policy = verifier.canonical(policy)
    (repo / protocol).write_bytes(raw_policy)
    tree = {protocol: verifier.sha(raw_policy), "scripts/public.py": "c" * 64}
    ready = dict(
        execution_identity="fixture.2",
        new_input_budget=policy["new_input_budget"],
        actors=policy["actors"],
        source_tree=tree,
        published_source_sha256={"scripts/public.py": "c" * 64},
        readiness_paths=paths,
        target="new",
        contract_sha256=tree[protocol],
        runtime={"python": "/public/python"},
        paired_readiness_verification={"source_main": main, "verified_returned_ms": 10},
    )

    def publish(name, raw):
        for directory in (evidence, backup):
            p = directory / name
            p.write_bytes(raw)
            p.chmod(0o600)

    raw = verifier.canonical(ready)
    publish(verifier.READY, raw)
    digest = verifier.sha(raw)
    records = []
    for name in paths:
        st = Path(name).stat()
        records.append(
            dict(path=name, sha256=digest, **{k: getattr(st, k) for k in verifier.PHYSICAL})
        )

    def packet(author, argv, result, at):
        from r0_read_independent import ACTUAL_SCHEMA, literal_command

        request = dict(workdir=str(repo), cmd=literal_command(argv))
        return verifier.canonical(
            dict(
                schema=ACTUAL_SCHEMA,
                author=author,
                argv=argv,
                request=request,
                responses=[
                    dict(
                        tool="exec_command",
                        arguments=request,
                        requested_ms=at,
                        returned_ms=at + 1,
                        result=dict(exit_code=0, output=verifier.canonical(result).decode()),
                    )
                ],
            )
        )

    prepare = [
        "/public/python",
        "-I",
        str(repo / "scripts" / verifier.PREPARATION_ENTRY),
        "readiness",
    ]
    prepared = packet(
        "A", prepare, dict(path=paths[0], sha256=digest, readiness_copies=records), 100
    )
    publish(verifier.PREPARED, prepared)
    args = (policy, tree, protocol, repo, "input.py", evidence)
    observed = dict(
        readiness_copies=records,
        contract_sha256=tree[protocol],
        target="new",
        readiness_paths=paths,
        source_main=main,
        preparation_readiness_actual_sha256=verifier.sha(prepared),
    )
    summary = dict(
        status="PASS_REGISTERED_INPUT_METADATA_PREFLIGHT",
        execution_identity="fixture.2",
        author="B",
        readiness_path=paths[0],
        readiness_sha256=digest,
        published_source_sha256=ready["published_source_sha256"],
        runtime=ready["runtime"],
        actors=policy["actors"],
        new_input_budget=ready["new_input_budget"],
        source_stat_reads=0,
        target_stat_reads=0,
        own_future_return="NOT_CLAIMED",
        paired_readiness=observed,
        paired_readiness_verification=ready["paired_readiness_verification"],
    )
    preflight = [
        "/public/python",
        "-I",
        str(repo / "scripts/input.py"),
        "preflight",
        "--readiness-sha",
        digest,
    ]
    original = packet("B", preflight, summary, 200)
    publish(verifier.PREFLIGHT, original)
    return args, ready, publish, original


def test_real_pair_and_original_required(verifier, tmp_path):
    args, _, _, original = fixture(verifier, tmp_path)
    assert verifier.audit_dispatch(*args) == verifier.sha(original)


@pytest.mark.parametrize(
    "damage",
    [
        "absent",
        "open-permissions",
        "byte",
        "same-inode",
        "same-bytes-new-inode",
        "old-contract",
        "old-target",
        "old-source",
        "old-identity",
        "old-commit",
        "old-stdout",
        "old-preparation-identity",
        "incomplete-original",
        "nonzero-original",
    ],
)
def test_gate_reads_actual_private_copies_before_dispatch(verifier, tmp_path, damage):
    args, ready, publish, original = fixture(verifier, tmp_path)
    path, backup = map(Path, ready["readiness_paths"])
    if damage == "absent":
        backup.unlink()
    elif damage == "open-permissions":
        backup.chmod(0o644)
    elif damage == "byte":
        backup.write_bytes(backup.read_bytes() + b" ")
    elif damage == "same-inode":
        backup.unlink()
        os.link(path, backup)
    elif damage == "same-bytes-new-inode":
        source = backup.with_name("replacement")
        source.write_bytes(path.read_bytes())
        source.chmod(0o600)
        source.replace(backup)
    elif damage in ("old-contract", "old-target", "old-source", "old-identity", "old-commit"):
        field = {
            "old-contract": "contract_sha256",
            "old-target": "target",
            "old-source": "source_tree",
            "old-identity": "execution_identity",
            "old-commit": "paired_readiness_verification",
        }[damage]
        ready[field] = {"source_main": "1" * 40} if damage == "old-commit" else "earlier"
        publish(verifier.READY, verifier.canonical(ready))
    elif damage == "old-preparation-identity":
        packet = verifier.parse((args[-1] / verifier.PREPARED).read_bytes())
        output = verifier.parse(packet["responses"][0]["result"]["output"].encode())
        output["readiness_copies"][1]["st_ino"] += 1
        packet["responses"][0]["result"]["output"] = verifier.canonical(output).decode()
        publish(verifier.PREPARED, verifier.canonical(packet))
    else:
        packet = verifier.parse(original)
        row = packet["responses"][0]["result"]
        if damage == "nonzero-original":
            row["exit_code"] = 1
        elif damage == "incomplete-original":
            row["exit_code"] = None
            row["session_id"] = 1
        else:
            output = verifier.parse(row["output"].encode())
            output.pop("paired_readiness")
            row["output"] = verifier.canonical(output).decode()
        publish(verifier.PREFLIGHT, verifier.canonical(packet))
    with pytest.raises((ValueError, OSError)):
        verifier.audit_dispatch(*args)


@pytest.mark.parametrize(
    "missing",
    [
        "readiness_path",
        "readiness_paths",
        "readiness_original_actual_path",
        "independent_preflight_actual_path",
        "readiness_verification_paths",
    ],
)
def test_authority_requires_literal_pair_without_downgrade(verifier, tmp_path, missing):
    args, _, _, _ = fixture(verifier, tmp_path)
    policy, evidence = args[0], args[-1]
    policy["readiness_verification_paths"] = dict(
        package=str(evidence / "readiness-release.json"),
        actual=str(evidence / "readiness-release-actual.json"),
    )
    verifier.require_policy_paths(policy, evidence)
    policy.pop(missing)
    with pytest.raises(ValueError, match="all literal paths"):
        verifier.require_policy_paths(policy, evidence)


def test_parent_replaced_by_symlink_during_read_is_refused(verifier, tmp_path, monkeypatch):
    parent = tmp_path / "controls"
    parent.mkdir()
    file = parent / "document"
    file.write_bytes(b"ready")
    file.chmod(0o600)
    original = verifier.parent_fd
    calls = []

    def move_parent(path):
        calls.append(path)
        if len(calls) == 2:
            destination = tmp_path / "moved"
            parent.rename(destination)
            parent.symlink_to(destination, target_is_directory=True)
        return original(path)

    monkeypatch.setattr(verifier, "parent_fd", move_parent)
    with pytest.raises(OSError):
        verifier.private_read(file)
    assert len(calls) == 2


@pytest.mark.parametrize(
    "slots",
    [[7, 8, 9, 10, 11], [7, 8, 9, 10, 11, 11], [7, 8, 9, 11, 10, 12], [7, 8, 9, 10, 11, 25]],
)
def test_release_requires_all_six_preregistered_public_controls(verifier, slots):
    proof = importlib.import_module("readiness_release_fixtures")
    with pytest.raises(ValueError, match="six ordered distinct"):
        proof.cases(slots)


@pytest.mark.parametrize(
    "case,expected",
    [
        ("positive", (0, 0, 0, 0)),
        ("missing", (0, 1, 1, None)),
        ("changed", (0, 1, 1, None)),
        ("stale", (0, 1, 1, None)),
        ("partial", (1, 1, 1, None)),
        ("stale-preflight", (0, 0, 1, None)),
    ],
)
def test_release_case_checks_preparation_preflight_emission_and_entry(verifier, case, expected):
    proof = importlib.import_module("readiness_release_fixtures")
    actual = proof.expected_exits(case)
    assert (
        tuple(
            actual.get(s) for s in ("readiness", "preflight", "emit-program", "enter-independent")
        )
        == expected
    )


def test_a_success_token_cannot_substitute_for_complete_emitter_return(verifier, tmp_path):
    proof = importlib.import_module("readiness_release_fixtures")
    packet = {"responses": [{"result": {"output": "{}\n"}}]}
    with pytest.raises(ValueError, match="actual emitter stdout"):
        proof.command(packet, ["driver", "emit-program"], tmp_path, 0, emitted={"program": "text"})
