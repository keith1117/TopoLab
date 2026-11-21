"""The timing comparison must use the stopped run's content-version contract."""

import subprocess
import sys
from pathlib import Path


def test_different_contract_stops_before_public_fixture_creation(tmp_path):
    scripts = Path(__file__).resolve().parents[1] / "scripts"
    different_contract = tmp_path / "contract.json"
    different_contract.write_bytes(b"{}\n")
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); "
            "import benchmark_public_input_r1 as bench; "
            "bench.WIRE_CONTRACT = Path(sys.argv[2]); bench.benchmark()",
            str(scripts),
            str(different_contract),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode != 0
    assert "retained acquisition contract differs" in result.stderr
    assert "Public software evidence" not in result.stderr
