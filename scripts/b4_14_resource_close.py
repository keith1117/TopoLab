"""Close B4.14 review/audit charges with complete native command profiles."""

import argparse
from pathlib import Path
from time import perf_counter

from b4_10_resource_close import profile
from b4_14_generalist_method_review import (
    BINDINGS,
    canonical,
    check_inputs,
    execution_release,
    peak_rss,
    plan_payload,
    read,
    roots,
    sha,
)


def close_resources(output, review, audit, commands):
    if not audit["passed"] or audit["review_sha256"] != sha(canonical(review)):
        raise ValueError("independent review agreement differs")
    if (
        review["plan"] != plan_payload()
        or review["repaired_gate"]
        or review["final_access"]
        or not review["old_fresh_sealed"]
        or audit["next_slice"] != review["next_slice"]
        or audit["compact_rows"] != 684
        or audit["prior_witness_pairs"] != 159
    ):
        raise ValueError("complete review or unchanged failed Gate differs")
    profiles = output / "profiles"
    expected = {"profiles/review.time", "profiles/independent.time"}
    successful = [c for c in commands if c["exit_code"] == 0]
    if len(successful) != 2 or {c["profile"] for c in successful} != expected:
        raise ValueError("successful execution command population differs")
    processes, hashes, peak = [], {}, 0
    for name, receipt in (("review", review), ("independent", audit)):
        path = (profiles / (name + ".time")).resolve()
        if not path.is_relative_to(profiles.resolve()):
            raise ValueError("successful profile escapes output")
        wall, rss = profile(path)
        charge = max(wall + 10, receipt["charged_seconds"])
        if charge > 60:
            raise ValueError("successful process exceeds cap")
        hashes[path.name] = sha(path.read_bytes())
        peak = max(peak, rss, receipt["peak_rss_bytes"])
        processes.append(
            {
                "process": name,
                "command_wall_seconds": wall,
                "closed_charge_seconds": charge,
                "peak_rss_bytes": rss,
            }
        )
    failed = set(profiles.glob("failed_*.time"))
    for command in commands:
        path = (output / command["profile"]).resolve()
        if not path.is_relative_to(profiles.resolve()):
            raise ValueError("command profile escapes output")
        if command["exit_code"] != 0:
            failed.add(path)
    for path in sorted(failed):
        if not path.resolve().is_relative_to(profiles.resolve()):
            raise ValueError("failed profile escapes output")
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
    total = sum(p["closed_charge_seconds"] for p in processes) + 30
    peak = max(peak, peak_rss())
    if total > 180 or peak > 1073741824:
        raise ValueError("whole method review exceeds cap")
    return {
        "processes": processes,
        "profile_sha256": hashes,
        "charged_seconds": total,
        "peak_rss_bytes": peak,
        "close_charge_seconds": 30.0,
    }


def main(argv=None):
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--diagnosis-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args(argv)
    root, output = args.diagnosis_root.resolve(), args.output_root.resolve()
    roots(root, output)
    assert (root.name, output.name) == (
        "b4-13-preservation-diagnosis",
        "b4-14-generalist-method-review",
    )
    assert root.parent == output.parent
    target = output / "resource_close.json"
    assert not target.exists(), "refuses to overwrite resource closure"
    revision = execution_release(output)
    check_inputs(root)
    review, audit = (read(output, f) for f in ("review.json", "independent_audit.json"))
    assert review["source_revision"] == audit["source_revision"] == revision
    assert audit["source_sha256"] == sha(
        (Path(__file__).resolve().parent / "b4_14_independent_audit.py").read_bytes()
    )
    commands = read(output, "audit_receipts/execution_commands.json")
    result = close_resources(output, review, audit, commands)
    check_inputs(root)
    internal = perf_counter() - started + 10
    assert internal <= 30
    result.update(
        version=plan_payload()["version"],
        closed=True,
        method_review_acceptance_passed=True,
        repaired_gate=False,
        final_access=False,
        old_fresh_sealed=True,
        close_internal_charge_seconds=internal,
        source_revision=revision,
        source_sha256=sha(Path(__file__).read_bytes()),
        review_sha256=sha(canonical(review)),
        independent_audit_sha256=sha(canonical(audit)),
        execution_commands_sha256=sha(canonical(commands)),
        protected_inputs=BINDINGS,
        prior_b4_13_charge_seconds_unchanged=107.78,
        prior_b4_12_charge_seconds_unchanged=8486.6,
        next_slice=review["next_slice"],
    )
    with target.open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
