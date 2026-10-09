"""One finite public-software receipt; no production runner or arbitrary input."""

import argparse
import hashlib
import json
import subprocess
from dataclasses import asdict
from pathlib import Path

from topolab.admissibility_certificate import (
    BUNDLE_SHA256,
    BUNDLE_VERSION,
    FIXTURE_SHA256,
    ROLE,
    SOURCE_MAIN,
    certify_public_point,
    read_public_fixture,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = "docs/planning/b4_35_public_admissibility_certificate_contract.json"
CONTRACT_SHA256 = "81235df59699dcd6bfc911f7584e9b924fced8a42c1da146f0025d4e33f54add"
SOURCE_PATHS = (
    "src/topolab/admissibility_certificate.py",
    "scripts/b4_35_certificate_oracle.py",
    "scripts/b4_35_public_certificate_evidence.py",
    "scripts/b4_35_independent_audit.py",
    "tests/test_admissibility_certificate.py",
)


def write_exclusive(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.is_relative_to(ROOT) or not out.is_dir():
        raise ValueError("existing external software-output directory required")
    def sha(raw):
        return hashlib.sha256(raw).hexdigest()

    raw = (ROOT / CONTRACT_PATH).read_bytes()
    if sha(raw) != CONTRACT_SHA256:
        raise ValueError("frozen public contract mismatch before fixture bytes")
    contract = json.loads(raw)
    for path, digest in contract["source_inputs_sha256"].items():
        if sha((ROOT / path).read_bytes()) != digest:
            raise ValueError("changed starting-source prerequisite")
    if contract["fixture_bundle_sha256"] != BUNDLE_SHA256 or contract["public_point_count"] != 16:
        raise ValueError("frozen finite public population mismatch")
    identities = {path: sha((ROOT / path).read_bytes()) for path in SOURCE_PATHS}
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    before = {
        "scope": "public-software-only",
        "starting_main": SOURCE_MAIN,
        "source_head": head,
        "source_sha256": identities,
        "contract_sha256": CONTRACT_SHA256,
        "fixture_bundle_sha256": BUNDLE_SHA256,
        "attempted": 0,
        "completed": 0,
        "pending": 16,
        "production_attempts": 0,
        "production_payload_reads": 0,
    }
    write_exclusive(out / "public_certificate_before.json", before)
    rows = []
    attempted = 0
    try:
        for identifier in FIXTURE_SHA256:
            binding = {
                "version": BUNDLE_VERSION,
                "role": ROLE,
                "fixture_id": identifier,
                "source_main": SOURCE_MAIN,
                "sha256": BUNDLE_SHA256,
            }
            fixture = read_public_fixture(
                binding, lambda: (ROOT / contract["fixture_bundle_path"]).read_bytes()
            )
            for name, density in (
                ("anchor", fixture.anchor_density),
                ("current", fixture.current_density),
            ):
                attempted += 1
                result = certify_public_point(fixture, density)
                rows.append(
                    {"fixture_id": identifier, "point": name, "certificate": asdict(result)}
                )
        if any(sha((ROOT / path).read_bytes()) != digest for path, digest in identities.items()):
            raise ValueError("source changed during finite evidence")
        receipt = before | {
            "passed": True,
            "attempted": attempted,
            "completed": len(rows),
            "pending": 16 - len(rows),
            "rows": rows,
        }
        write_exclusive(out / "public_certificate_evidence.json", receipt)
        print(
            json.dumps(
                {
                    "passed": True,
                    "attempted": attempted,
                    "completed": len(rows),
                    "receipt_sha256": sha((out / "public_certificate_evidence.json").read_bytes()),
                }
            )
        )
    except Exception as exc:
        write_exclusive(
            out / "public_certificate_failed.json",
            before
            | {
                "passed": False,
                "attempted": attempted,
                "completed": len(rows),
                "pending": 16 - len(rows),
                "rows": rows,
                "error": repr(exc),
            },
        )
        raise


if __name__ == "__main__":
    main()
