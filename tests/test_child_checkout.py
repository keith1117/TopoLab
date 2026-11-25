"""The measured certificate proof must preserve the published commit without launching Git."""

import hashlib
import importlib.util
import os
import py_compile
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def proof(monkeypatch):
    monkeypatch.syspath_prepend(str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "certificate_pin_under_test", SCRIPTS / "certificate_replay_proof.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def repository(tmp_path, head):
    git = tmp_path / ".git"
    (git / "refs/heads").mkdir(parents=True)
    (git / "HEAD").write_text(head + "\n")
    return git


@pytest.mark.parametrize("layout", ["detached", "loose", "packed", "linked"])
def test_exact_checkout_without_child(tmp_path, monkeypatch, layout):
    mod = proof(monkeypatch)
    monkeypatch.setattr(mod.subprocess, "Popen", lambda *a, **k: pytest.fail("spawned a child"))
    oid = "a" * 40
    git = repository(tmp_path, oid if layout == "detached" else "ref: refs/heads/main")
    root = tmp_path
    if layout == "loose":
        (git / "refs/heads/main").write_text(oid + "\n")
        (git / "packed-refs").write_text("b" * 40 + " refs/heads/main\n")
    if layout in ("packed", "linked"):
        (git / "packed-refs").write_text("# pack-refs with: peeled\n" + oid + " refs/heads/main\n")
    if layout == "linked":
        root = tmp_path / "work"
        root.mkdir()
        g = git / "worktrees/work"
        g.mkdir(parents=True)
        (root / ".git").write_text("gitdir: " + str(g) + "\n")
        (g / "gitdir").write_text(str(root / ".git") + "\n")
        (g / "commondir").write_text("../..\n")
        (g / "HEAD").write_text("ref: refs/heads/main\n")
    assert mod.checkout_commit(root) == oid


@pytest.mark.parametrize(
    "head", ["ref: ../bad", "ref: refs/heads/../../../bad", "z" * 40, "ref: refs/heads/main"]
)
def test_malformed_or_ambiguous_revision_refused(tmp_path, monkeypatch, head):
    mod = proof(monkeypatch)
    git = repository(tmp_path, head)
    (git / "packed-refs").write_text(("a" * 40 + " refs/heads/main\n") * 2)
    with pytest.raises((OSError, ValueError)):
        mod.checkout_commit(tmp_path)


def test_checkout_change_invalidates_pin(tmp_path, monkeypatch):
    mod = proof(monkeypatch)
    git = repository(tmp_path, "ref: refs/heads/main")
    ref = git / "refs/heads/main"
    ref.write_text("a" * 40 + "\n")
    frozen = mod.checkout_commit(tmp_path)
    ref.write_text("b" * 40 + "\n")
    assert mod.checkout_commit(tmp_path) != frozen


def test_public_bootstrap_uses_frozen_source_when_timestamp_bytecode_is_stale(
    tmp_path, monkeypatch
):
    spec = importlib.util.spec_from_file_location(
        "public_entry_test", SCRIPTS / "child_public_control.py"
    )
    public = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(public)
    monkeypatch.delitem(sys.modules, "full60_input_loader", raising=False)
    path = tmp_path / "full60_input_loader.py"
    path.write_text("loaded_source_sha256 = {}\nmarker = 1\n")
    fixed = path.stat()
    py_compile.compile(
        str(path), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP
    )
    raw = path.read_bytes().replace(b"marker = 1", b"marker = 2")
    path.write_bytes(raw)
    os.utime(path, ns=(fixed.st_atime_ns, fixed.st_mtime_ns))
    try:
        loaded = public.source_loader(path)
        assert loaded.marker == 2
        assert loaded.loaded_source_sha256[str(path.resolve())] == hashlib.sha256(raw).hexdigest()
    finally:
        sys.modules.pop("full60_input_loader", None)
