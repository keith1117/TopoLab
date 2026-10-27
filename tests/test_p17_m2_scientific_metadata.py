"""Exercise the metadata-only JavaScript seam through its public interface."""

import os
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(
    shutil.which("node") is None, reason="Node.js metadata observer runtime unavailable"
)
def test_scientific_metadata_corruption_regressions(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    environment = {**os.environ, "TOPOLAB_METADATA_TEST_ROOT": str(tmp_path)}
    result = subprocess.run(
        ["node", "--test", str(repo / "tests/test_p17_m2_scientific_metadata.mjs")],
        cwd=repo,
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
