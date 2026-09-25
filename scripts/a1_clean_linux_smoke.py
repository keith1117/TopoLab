"""Exercise the local Compose stack from a clean Linux checkout.

Run after ``docker compose -p topolab-a14 up --build --wait -d``. All generated
state stays in the Compose volume, which the caller should remove with ``down -v``.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "src/topolab/examples/canonical_demo_v1.json"


def _read(url: str, *, payload: bytes | None = None) -> tuple[int, str, bytes]:
    headers = {"Content-Type": "application/json"} if payload is not None else {}
    request = Request(url, data=payload, headers=headers)
    with urlopen(request, timeout=15) as response:
        return response.status, response.headers.get_content_type(), response.read()


def _json(url: str) -> dict[str, object]:
    status, content_type, body = _read(url)
    assert status == 200 and content_type == "application/json"
    value = json.loads(body)
    assert isinstance(value, dict)
    return value


def _wait_for_run(url: str, *, deadline: float) -> dict[str, object]:
    while time.monotonic() < deadline:
        try:
            snapshot = _json(url)
        except (URLError, TimeoutError):
            time.sleep(1)
            continue
        if snapshot["status"] in {"succeeded", "failed", "cancelled"}:
            return snapshot
        time.sleep(1)
    raise TimeoutError(f"run did not become terminal within the timeout: {url}")


def _wait_for_frontend(url: str) -> tuple[int, str, bytes]:
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        try:
            return _read(url)
        except (URLError, TimeoutError):
            time.sleep(1)
    raise TimeoutError("frontend did not start within 30 seconds")


def _compose(project: str, *args: str) -> str:
    completed = subprocess.run(
        ["docker", "compose", "-p", project, *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8080/")
    parser.add_argument("--project", default="topolab-a14")
    args = parser.parse_args()
    base = args.base_url.rstrip("/") + "/"
    started = time.monotonic()

    status, content_type, html = _wait_for_frontend(base)
    assert status == 200 and content_type == "text/html"
    script = re.search(rb'<script\b[^>]*\bsrc="([^"]+\.js)"', html)
    assert script is not None, "built frontend script missing from HTML"
    asset_url = urljoin(base, script.group(1).decode("ascii"))
    asset_status, asset_type, asset = _read(asset_url)
    assert asset_status == 200 and "javascript" in asset_type and asset

    page = _json(urljoin(base, "runs"))
    assert isinstance(page["items"], list)
    case = json.loads(CASE.read_text(encoding="utf-8"))
    submitted_at = time.monotonic()
    status, content_type, body = _read(
        urljoin(base, "runs"), payload=json.dumps(case).encode("utf-8")
    )
    assert status == 202 and content_type == "application/json"
    submitted = json.loads(body)
    run_id = submitted["run_id"]
    assert isinstance(run_id, str) and run_id
    run_url = urljoin(base, f"runs/{run_id}")
    snapshot = _wait_for_run(run_url, deadline=submitted_at + 180)
    solve_seconds = time.monotonic() - submitted_at

    assert snapshot["status"] == "succeeded", snapshot.get("error")
    assert snapshot["problem"]["mesh"] == case["mesh"]
    result = snapshot["result"]
    assert result is not None and result["converged"] is True
    history = result["history"]
    density = result["physical_density"]
    assert len(density) == 16
    assert snapshot["iteration"] == len(history)
    assert 0 < len(history) <= case["optimization"]["max_iterations"]
    compliance = result["compliance"]
    assert math.isfinite(compliance) and compliance > 0
    assert math.isclose(history[-1]["compliance"], compliance, rel_tol=1e-9)
    volume = sum(density) / len(density)
    assert abs(volume - case["optimization"]["volume_fraction"]) <= 5e-3

    assert _compose(args.project, "exec", "-T", "api", "id", "-u") == "10001"
    assert _compose(args.project, "exec", "-T", "web", "id", "-u") == "101"
    _compose(args.project, "exec", "-T", "api", "test", "-s", "/data/topolab.sqlite3")

    restarted_at = time.monotonic()
    _compose(args.project, "restart", "api")
    recovered = _wait_for_run(run_url, deadline=restarted_at + 90)
    restart_seconds = time.monotonic() - restarted_at
    assert recovered == snapshot, "terminal record changed across API restart"
    page = _json(urljoin(base, "runs?limit=10"))
    assert any(
        item["run_id"] == run_id and item["status"] == "succeeded"
        for item in page["items"]
    )

    print(
        json.dumps(
            {
                "run_id": run_id,
                "status": snapshot["status"],
                "iterations": len(history),
                "converged": result["converged"],
                "compliance": compliance,
                "physical_volume": volume,
                "solve_seconds": round(solve_seconds, 3),
                "restart_read_seconds": round(restart_seconds, 3),
                "smoke_seconds": round(time.monotonic() - started, 3),
                "frontend_asset": script.group(1).decode("ascii"),
                "sqlite_record_recovered": True,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
