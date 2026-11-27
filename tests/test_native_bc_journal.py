"""Run the API return journal fixtures on the same Node runtime as the native caller tests."""

import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="Node metadata runtime unavailable")
def test_native_bc_journal() -> None:
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["node", "--test", "tests/test_native_bc_journal.mjs"],
        cwd=root, text=True, capture_output=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
