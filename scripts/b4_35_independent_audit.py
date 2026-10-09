"""Independent, candidate-free finite public receipt audit; no real input access."""

import argparse
import hashlib
import json
from pathlib import Path

from b4_35_certificate_oracle import audit_point

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = "docs/planning/b4_35_public_admissibility_certificate_contract.json"
CONTRACT_DIGEST = "81235df59699dcd6bfc911f7584e9b924fced8a42c1da146f0025d4e33f54add"
SOURCE_PATHS = {
    "src/topolab/admissibility_certificate.py",
    "scripts/b4_35_certificate_oracle.py",
    "scripts/b4_35_public_certificate_evidence.py",
    "scripts/b4_35_independent_audit.py",
    "tests/test_admissibility_certificate.py",
}


def unique_fields(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate public JSON field")
        result[key] = value
    return result


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--receipt-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    out, path = args.output_dir.resolve(), args.receipt.resolve()
    if out.is_relative_to(ROOT) or path.is_relative_to(ROOT) or not out.is_dir():
        raise ValueError("external public software evidence only")
    if path.name != "public_certificate_evidence.json" or path.stat().st_size > 65536:
        raise ValueError("only bounded new public-software receipt")
    def digest(raw):
        return hashlib.sha256(raw).hexdigest()

    contract_raw = (ROOT / CONTRACT).read_bytes()
    if digest(contract_raw) != CONTRACT_DIGEST:
        raise ValueError("frozen public contract mismatch before inputs")
    contract = json.loads(contract_raw, object_pairs_hook=unique_fields)
    fixture_path = ROOT / "tests/fixtures/b4_35_admissibility_certificate.json"
    if contract["fixture_bundle_path"] != str(fixture_path.relative_to(ROOT)):
        raise ValueError("literal public fixture path required")
    fixture_raw = fixture_path.read_bytes()
    if digest(fixture_raw) != contract["fixture_bundle_sha256"]:
        raise ValueError("public fixture digest mismatch")
    bundle = json.loads(fixture_raw, object_pairs_hook=unique_fields)
    receipt_raw = path.read_bytes()
    if digest(receipt_raw) != args.receipt_sha256:
        raise ValueError("bound new public receipt digest mismatch")
    receipt = json.loads(receipt_raw, object_pairs_hook=unique_fields)
    expected_keys = {
        "scope",
        "starting_main",
        "source_head",
        "source_sha256",
        "contract_sha256",
        "fixture_bundle_sha256",
        "attempted",
        "completed",
        "pending",
        "production_attempts",
        "production_payload_reads",
        "passed",
        "rows",
    }
    conditions = []
    checks = {
        "closed_receipt": set(receipt) == expected_keys,
        "same_source_contract": receipt.get("starting_main") == contract["starting_main"]
        and receipt.get("contract_sha256") == CONTRACT_DIGEST,
        "same_public_bundle": receipt.get("fixture_bundle_sha256") == digest(fixture_raw),
        "closed_source_map": set(receipt.get("source_sha256", {})) == SOURCE_PATHS,
        "full_finite_counters": (
            receipt.get("attempted"),
            receipt.get("completed"),
            receipt.get("pending"),
        )
        == (16, 16, 0),
        "software_only": receipt.get("scope") == "public-software-only"
        and receipt.get("production_attempts") == 0
        and receipt.get("production_payload_reads") == 0,
        "producer_exit_positive": receipt.get("passed") is True,
    }
    for name, passed in checks.items():
        conditions.append({"id": name, "passed": passed})
    for name, expected in receipt.get("source_sha256", {}).items():
        if name not in SOURCE_PATHS:
            raise ValueError("unknown source path")
        conditions.append(
            {"id": "source:" + name, "passed": digest((ROOT / name).read_bytes()) == expected}
        )
    for name, expected in contract["source_inputs_sha256"].items():
        conditions.append(
            {"id": "starting:" + name, "passed": digest((ROOT / name).read_bytes()) == expected}
        )
    population = [
        (row["id"], point) for row in bundle["fixtures"] for point in ("anchor", "current")
    ]
    if (
        len(population) != 16
        or [(x["fixture_id"], x["point"]) for x in receipt["rows"]] != population
    ):
        raise ValueError("same complete ordered finite16 points required")
    save(
        out / "independent_audit_before.json",
        {
            "input_receipt_sha256": args.receipt_sha256,
            "attempted": 0,
            "completed": 0,
            "pending": 16,
            "candidate_imports": False,
            "source_sha256": receipt["source_sha256"],
            "contract_sha256": CONTRACT_DIGEST,
        },
    )
    attempted = 0
    references = []
    try:
        for i, evidence in enumerate(receipt["rows"]):
            attempted += 1
            if set(evidence) != {"fixture_id", "point", "certificate"}:
                raise ValueError("closed public point schema")
            row = bundle["fixtures"][i // 2]
            fingerprint = digest(
                (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
            )
            conditions.append(
                {
                    "id": str(i) + ":fingerprint",
                    "passed": fingerprint == contract["fixture_fingerprints_sha256"][row["id"]],
                }
            )
            point_checks, ref = audit_point(row, evidence["point"], evidence["certificate"])
            conditions.extend(
                {"id": str(i) + ":" + key, "passed": value} for key, value in point_checks.items()
            )
            references.append(
                {
                    "fixture_id": row["id"],
                    "point": evidence["point"],
                    "exact": {
                        key: str(ref[key])
                        for key in (
                            "upper",
                            "compliance",
                            "residual_squared",
                            "coercivity",
                            "stored",
                            "anchor_compliance",
                        )
                    },
                }
            )
        if len(conditions) > 600:
            raise ValueError("frozen predicate limit")
        passed = all(x["passed"] for x in conditions)
        result = {
            "passed": passed,
            "input_receipt_sha256": args.receipt_sha256,
            "contract_sha256": CONTRACT_DIGEST,
            "conditions": conditions,
            "predicate_count": len(conditions),
            "attempted": attempted,
            "completed": len(references),
            "pending": 16 - len(references),
            "reference_values": references,
            "candidate_imports": False,
            "production_attempts": 0,
            "real_certificate_status": "UNKNOWN_STOP",
        }
        save(out / "independent_certificate_audit.json", result)
        print(
            json.dumps(
                {
                    "passed": passed,
                    "predicates": len(conditions),
                    "fixed_points": len(references),
                    "audit_sha256": digest(
                        (out / "independent_certificate_audit.json").read_bytes()
                    ),
                }
            )
        )
        if not passed:
            raise SystemExit(1)
    except Exception as exc:
        save(
            out / "independent_audit_failed.json",
            {
                "passed": False,
                "attempted": attempted,
                "completed": len(references),
                "pending": 16 - len(references),
                "conditions": conditions,
                "reference_values": references,
                "error": repr(exc),
            },
        )
        raise


if __name__ == "__main__":
    main()
