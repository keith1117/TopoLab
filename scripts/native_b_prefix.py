"""Independent R2 B verifier; the enclosing caller observes this command's own exit."""

import argparse
import importlib.util
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha", required=True)
    args = parser.parse_args()
    script = Path(__file__).resolve()
    if not sys.flags.isolated or Path.cwd() != script.parents[1]:
        parser.error("registered isolated B verifier checkout required")
    source = script.with_name("p17_m2_scientific_orchestration.py")
    spec = importlib.util.spec_from_file_location("p17_m2_scientific_orchestration", source)
    control = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(control)
    contract = control.read_contract(args.contract, args.contract_sha)
    verification = contract["b_caller_clock"]["verification_timed_argv"]
    profile = str(Path(contract["api_metadata"]["root"]) / "B-verify.time")
    if verification[:4] != ["/usr/bin/time", "-l", "-o", profile] or sys.orig_argv != (
        control.startup_argv(verification[4:], args.contract_sha, contract["runtime"])
    ):
        parser.error("B verifier command or native profile binding differs")
    evidence = control.load_role_evidence(contract, "resource-preflight", b_prefix_only=True)
    independent = control.load("p17_m2_scientific_independent")
    independent.checked_b_native_prefix(contract, evidence)
    clock = control.load("native_b_clock")
    sys.stdout.buffer.write(
        clock.prefix_stdout(args.contract_sha, evidence["b_start"], evidence["b_js_prefix"])
    )


if __name__ == "__main__":
    main()
