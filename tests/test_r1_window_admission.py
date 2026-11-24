"""Boundary regressions for the new R1 timing contract."""
import hashlib
import runpy
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO = Path(__file__).parents[1]
PROOF = REPO / "scripts/r1_window_proof.py"


def test_audit_binds_the_executed_worker_buffer(monkeypatch, tmp_path):
    env = runpy.run_path(str(PROOF))
    check = env["compiled"]
    namespace = check.__globals__
    monkeypatch.setitem(namespace, "BASE", tmp_path)
    monkeypatch.setitem(namespace, "MODULE_SOURCE_SHA256", None)
    content = b"reviewed source"
    expected = hashlib.sha256(content).hexdigest()
    names = (env["WORKER"], "scripts/staged_input_filer.py", "scripts/r0_read_independent.py")
    (tmp_path / "scripts").mkdir()
    for name in names:
        (tmp_path / name).write_bytes(content)
    tree = dict.fromkeys(names, expected)
    actual = {str(tmp_path / name): expected for name in names}
    monkeypatch.setitem(namespace["sys"].modules, "full60_input_loader",
                        SimpleNamespace(loaded_source_sha256=actual))
    assert check(tree, verification=False) == tree
    actual[str(tmp_path / env["WORKER"])] = "0" * 64
    with pytest.raises(ValueError, match="executed source"):
        check(tree, verification=False)


def test_first_wait_respects_original_budget_and_host_floor():
    node = shutil.which("node")
    if not node:
        pytest.skip("node unavailable")
    script = """
import assert from 'node:assert/strict';
import {initialWait} from './scripts/staged_input_actor.mjs';
const route='topolab.v2.p17-m2-registered-source-acquisition.r1-window-20261123.v1';
assert.equal(initialWait(route,'file',8165),8165);
assert.equal(initialWait(route,'record',71000),30000);
assert.equal(initialWait(route,'bind',1405),1405);
assert.equal(initialWait(route,'supervise',8165),1000);
assert.equal(initialWait('old','file',8165),1000);
"""
    subprocess.run([node, "--input-type=module", "-e", script], cwd=REPO, check=True)
