"""Close only the new read-only diagnostic budget against whole-command profiles."""

import argparse
from pathlib import Path
from time import perf_counter

from b4_10_resource_close import profile
from b4_13_preservation_diagnosis import (
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
    assert (
        root.name == "b4-12-terminal-preservation" and output.name == "b4-13-preservation-diagnosis"
    )
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
    assert report["cohorts"]["sentinel"]["scientific_decision"]["sentinel_gate_passed"]
    assert not report["cohorts"]["fresh"]["scientific_decision"]["development_gate_passed"]
    assert report["old_fresh_sealed"] and not report["final_access"] and not report["repaired_gate"]
    repository = Path(__file__).resolve().parents[1]
    for relative, digest in release["source_sha256"].items():
        assert sha((repository / relative).read_bytes()) == digest
    assert (
        report["source_sha256"]
        == release["source_sha256"]["scripts/b4_13_preservation_diagnosis.py"]
    )
    assert audit["source_sha256"] == release["source_sha256"]["scripts/b4_13_independent_audit.py"]
    assert (
        report["protocol_sha256"]
        == release["source_sha256"]["docs/planning/b4_13_preservation_diagnosis_protocol.md"]
    )
    processes, hashes, peak = [], {}, 0
    for process, receipt in (("diagnosis", report), ("independent", audit)):
        path = output / "profiles" / f"{process}.time"
        wall, rss = profile(path)
        charge = max(receipt["charged_seconds"], wall + 10)
        assert charge <= 120
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
    failed_profiles = set((output / "profiles").glob("failed_*.time"))
    commands = read(output, "audit_receipts/execution_commands.json")
    assert len(commands) >= 2
    for command in commands:
        path = (output / command["profile"]).resolve()
        assert path.is_relative_to((output / "profiles").resolve())
        if command["exit_code"] != 0:
            failed_profiles.add(path)
    for path in sorted(failed_profiles):
        wall, rss = profile(path)
        peak = max(peak, rss)
        hashes[path.name] = sha(path.read_bytes())
        processes.append(
            {
                "process": "failed_" + path.stem,
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
    assert internal_charge <= charge and total <= 360 and peak <= 1_073_741_824
    result = {
        "version": plan_payload()["version"],
        "closed": True,
        "diagnostic_acceptance_passed": True,
        "repaired_gate": False,
        "old_fresh_sealed": True,
        "next_mechanism": report["next_mechanism"],
        "processes": processes,
        "execution_commands_sha256": sha(
            (output / "audit_receipts/execution_commands.json").read_bytes()
        ),
        "profile_sha256": hashes,
        "close_charge_seconds": charge,
        "close_internal_charge_seconds": internal_charge,
        "charged_seconds": total,
        "peak_rss_bytes": peak,
        "prior_b4_12_charge_seconds_unchanged": inputs["resource_close.json"]["charged_seconds"],
        "protected_inputs": plan_payload()["bindings"],
        "source_sha256": sha(Path(__file__).read_bytes()),
        "diagnosis_sha256": audit["diagnosis_sha256"],
        "independent_audit_sha256": sha((output / "independent_audit.json").read_bytes()),
        "production_release_sha256": sha(
            (output / "audit_receipts/production_release.json").read_bytes()
        ),
        "next_slice": "B4.14 " + report["next_mechanism"],
    }
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
