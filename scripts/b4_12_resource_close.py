"""Close B4.12 whole-command floors and unchanged input/resource boundaries."""

import argparse
import hashlib
import json
import re
import resource
from pathlib import Path
from time import perf_counter

from b4_10_independent_audit import close


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    raw = path.read_bytes()
    value = json.loads(raw)
    assert canonical(value) == raw
    return value


def profile(path):
    text = path.read_text()
    elapsed = re.search(r"^(?:real\s+([0-9.]+)|\s*([0-9.]+)\s+real\b)", text, re.MULTILINE)
    memory = re.search(r"([0-9]+)\s+maximum resident set size", text)
    if elapsed is None or memory is None:
        raise ValueError("unsupported whole-command time profile")
    wall = float(elapsed[1] or elapsed[2])
    rss = int(memory[1])
    return wall, rss


def protected_inputs(plan):
    protected = {
        "b3-v1-data/b3_materialization.json": (
            "b78e85f5bab56f2b05e06b43b8fd77f2bfd556150b95643e443a566165d8fc26"
        ),
        "b3-v1-fits/b3_training.json": (
            "229e1ba5a3cd4da9ebfb5e3e77a5aa97fcea37f7ff7c671bec8b70f9b5ac69e7"
        ),
        "b3-v1-screen/b3_screen.json": (
            "a647f420cb2d498c961a6e8ca965511b4a18e33e26056b10cf987d989df8a421"
        ),
        "b4-4-engineering/progress.json": (
            "4ae7f2dc48544f35a67fdec2aa67f0768a42dcb644e21383672acbc42b7c20fc"
        ),
    }
    for sibling, bindings in (
        ("b4-8-rollback-confirmation", plan["source_files"]),
        ("b4-9-diagnosis", plan["diagnosis_files"]),
        ("b4-10-post-plateau-polish", plan["polish_files"]),
        ("b4-11-polish-diagnosis", plan["review_files"]),
    ):
        protected.update({sibling + "/" + key: value for key, value in bindings.items()})
    return protected


def main():
    started = perf_counter()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.output.resolve()
    assert root.name == "b4-12-terminal-preservation"
    plan = read(root / "audit_receipts/plan.json")
    context = read(root / "context.json")
    assert context["plan_sha256"] == plan["plan_sha256"]
    protected = protected_inputs(plan)
    assert not (root.parent / "b4-10-post-plateau-polish/fresh").exists()
    for path, sha in protected.items():
        assert digest((root.parent / path).read_bytes()) == sha, path
    rows, peak, hashes = [], 0, {}
    cohorts = ["sentinel"]
    sentinel = read(root / "sentinel/policy-audit/summary.json")
    if sentinel["passed"]:
        cohorts.append("fresh")
    else:
        assert not (root / "fresh").exists(), "failed sentinel must keep new cases sealed"
    for cohort in cohorts:
        audit = read(root / cohort / "independent_audit.json")
        policy = read(root / cohort / "policy-audit/summary.json")
        assert audit["passed"] and audit["policy_summary_sha256"] == digest(
            (root / cohort / "policy-audit/summary.json").read_bytes()
        )
        # Use the independent auditor's already frozen arithmetic agreement;
        # gate flags, integer counts and identities still compare exactly.
        close(audit["decision"], policy["decision"])
        assert audit["gate_passed"] == policy["passed"]
        for stage in (*plan["caps"], "independent"):
            path = root / "profiles" / f"{cohort}_{stage}.time"
            wall, rss = profile(path)
            hashes[path.name] = digest(path.read_bytes())
            if stage == "independent":
                receipt, cap, extra = audit, plan["independent_audit_cap_seconds"], 0
            else:
                receipt, cap = read(root / cohort / stage / "progress.json"), plan["caps"][stage][0]
                assert not receipt["resource_failed"] and not receipt["integrity_failed"]
                assert receipt["active_at"] is None and receipt["pending"] is None
                extra = receipt["attempted"] if stage in ("reference", "screen") else 0
            charged = max(receipt["charged_seconds"], wall + extra + 10)
            assert charged <= cap
            peak = max(peak, rss, receipt["peak_rss_bytes"])
            rows.append(
                {
                    "process": f"{cohort}_{stage}",
                    "command_wall_seconds": wall,
                    "recorded_charge_seconds": receipt["charged_seconds"],
                    "closed_charge_seconds": charged,
                    "peak_rss_bytes": rss,
                }
            )
    failed_profiles = set((root / "profiles").glob("failed_*.time"))
    commands = root / "audit_receipts/execution_commands.json"
    if commands.exists():
        for command in read(commands):
            if command["exit_code"] != 0:
                path = (root / command["profile"]).resolve()
                assert path.is_relative_to((root / "profiles").resolve())
                failed_profiles.add(path)
    for path in sorted(failed_profiles):
        wall, rss = profile(path)
        hashes[path.name] = digest(path.read_bytes())
        peak = max(peak, rss)
        rows.append(
            {
                "process": path.stem if path.stem.startswith("failed_") else "failed_" + path.stem,
                "command_wall_seconds": wall,
                "closed_charge_seconds": wall + 10,
                "peak_rss_bytes": rss,
            }
        )
    seconds = perf_counter() - started + 10
    assert seconds <= plan["resource_close_cap_seconds"]
    peak = max(peak, resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    reserved = plan["resource_close_cap_seconds"]
    total = sum(r["closed_charge_seconds"] for r in rows) + reserved
    assert total <= plan["whole_slice_cap_seconds"] and peak <= plan["whole_slice_rss_bytes"]
    passed = (
        read(root / cohorts[-1] / "policy-audit/summary.json")["passed"] and cohorts[-1] == "fresh"
    )
    result = {
        "version": plan["version"],
        "closed": True,
        "preservation_gate_passed": passed,
        "fresh_sealed": cohorts == ["sentinel"],
        "processes": rows,
        "profile_sha256": hashes,
        "close_internal_charge_seconds": seconds,
        "close_charge_seconds": reserved,
        "charged_seconds": total,
        "peak_rss_bytes": peak,
        "protected_inputs": protected,
        "source_sha256": digest(Path(__file__).read_bytes()),
        "next_slice": "B4.13 independent larger preservation confirmation"
        if passed
        else "B4.13 read-only preservation failure/cost review",
    }
    target = root / "resource_close.json"
    assert not target.exists(), "closure receipt must not be overwritten"
    target.write_bytes(canonical(result))
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
