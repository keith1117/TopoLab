"""Close only the new read-only diagnostic budget against whole-command profiles."""

import argparse
from pathlib import Path
from time import perf_counter

from b4_10_resource_close import profile
from b4_11_polish_diagnosis import (
    MAX_RSS_BYTES,
    MAX_SECONDS,
    PROCESS_SECONDS,
    canonical,
    check_inputs,
    peak_rss,
    plan_payload,
    read,
    sha,
)


def main(argv=None):
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--screen-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    root, output = args.screen_root.resolve(), args.output_root.resolve()
    assert root.name == "b4-10-post-plateau-polish" and output.name == "b4-11-polish-diagnosis"
    assert root.parent == output.parent and not output.is_relative_to(
        Path(__file__).resolve().parents[1]
    )
    target = output / "resource_close.json"
    assert not target.exists(), "refuses to overwrite resource closure"
    inputs = check_inputs(root)
    report = read(output, "diagnosis.json")
    audit = read(output, "independent_audit.json")
    release = read(output, "audit_receipts/production_release.json")
    assert report["plan"] == plan_payload() and audit["passed"]
    assert audit["diagnosis_sha256"] == sha((output / "diagnosis.json").read_bytes())
    assert report["diagnostic_source_revision"] == release["source_revision"]
    assert release["all_applicable_ci_passed_before_merge"]
    assert audit["next_mechanism"] == report["next_mechanism"]
    assert not report["scientific_decision"]["sentinel_gate_passed"]
    assert report["fresh_sealed"] and not report["scientific_decision"]["final_access"]
    repository = Path(__file__).resolve().parents[1]
    for relative, digest in release["source_sha256"].items():
        assert sha((repository / relative).read_bytes()) == digest
    assert report["source_sha256"] == release["source_sha256"]["scripts/b4_11_polish_diagnosis.py"]
    assert audit["source_sha256"] == release["source_sha256"]["scripts/b4_11_independent_audit.py"]
    assert (
        report["protocol_sha256"]
        == release["source_sha256"]["docs/planning/b4_11_polish_diagnosis_protocol.md"]
    )
    processes, hashes, peak = [], {}, 0
    for process, receipt in (("diagnosis", report), ("independent", audit)):
        path = output / "profiles" / f"{process}.time"
        wall, rss = profile(path)
        charge = max(receipt["charged_seconds"], wall + 10)
        assert charge <= PROCESS_SECONDS
        peak = max(peak, rss, receipt["peak_rss_bytes"])
        hashes[path.name] = sha(path.read_bytes())
        processes.append(
            {
                "process": process,
                "command_wall_seconds": wall,
                "recorded_charge_seconds": receipt["charged_seconds"],
                "closed_charge_seconds": charge,
                "peak_rss_bytes": rss,
            }
        )
    for path in sorted((output / "profiles").glob("failed_*.time")):
        wall, rss = profile(path)
        peak = max(peak, rss)
        hashes[path.name] = sha(path.read_bytes())
        processes.append(
            {
                "process": path.stem,
                "command_wall_seconds": wall,
                "closed_charge_seconds": wall + 10,
                "peak_rss_bytes": rss,
            }
        )
    internal_charge = perf_counter() - started + 10
    # Its complete command profile exists only after exit; reserve the full cap.
    charge = 30.0
    peak = max(peak, peak_rss())
    total = sum(p["closed_charge_seconds"] for p in processes) + charge
    assert internal_charge <= charge and total <= MAX_SECONDS and peak <= MAX_RSS_BYTES
    result = {
        "version": plan_payload()["version"],
        "closed": True,
        "diagnostic_acceptance_passed": True,
        "repaired_gate": False,
        "fresh_sealed": True,
        "next_mechanism": report["next_mechanism"],
        "processes": processes,
        "profile_sha256": hashes,
        "close_charge_seconds": charge,
        "close_internal_charge_seconds": internal_charge,
        "charged_seconds": total,
        "peak_rss_bytes": peak,
        "prior_b4_10_charge_seconds_unchanged": inputs["resource_close.json"]["charged_seconds"],
        "protected_inputs": plan_payload()["bindings"],
        "source_sha256": sha(Path(__file__).read_bytes()),
        "diagnosis_sha256": audit["diagnosis_sha256"],
        "independent_audit_sha256": sha((output / "independent_audit.json").read_bytes()),
        "production_release_sha256": sha(
            (output / "audit_receipts/production_release.json").read_bytes()
        ),
        "next_slice": "B4.12 " + report["next_mechanism"],
    }
    target.write_bytes(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
