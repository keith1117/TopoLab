"""Portable public API ingress and manifest regression entry point."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js metadata runtime unavailable")
def test_scientific_ingress_public_regressions(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["node", "--test", str(repo / "tests/test_p17_m2_scientific_tool_ingress.mjs")],
        cwd=repo,
        env={**os.environ, "TOPOLAB_INGRESS_TEST_ROOT": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
