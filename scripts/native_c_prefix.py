"""Replay the four C-only helpers and both C roles before the final caller return."""

import argparse
import importlib.util
import json
import sys
from pathlib import Path


def evidence_for(control, contract, *, completed):
    root = Path(contract["api_metadata"]["root"])
    reader = control.load("p17_m2_input_export_independent").OnceReader(
        root, 16, 32 * 1024**2, source_identity_checks=True
    )

    def read(path, cap=1024**2):
        return reader.read(str(Path(path).relative_to(root)), cap)

    data = {
        "start": read(root / "C-clock-start.json", 4096),
        "js_prefix": read(root / "C-js-prefix.json", 65536),
        "manifest": read(contract["api_metadata"]["manifests"]["FINAL"], 16 * 1024**2),
        "publications": {},
    }
    for role in ("scientific-producer", "scientific-auditor"):
        spec = contract["roles"][role]
        data["publications"][role] = {
            "raw": read(spec["publication_readiness_path"]),
            "event": json.loads(read(spec["publication_return_path"])),
            "profile": read(spec["publication_profile_path"]),
            "resource": read(spec["publication_profile_path"] + ".resource.json", 4 * 1024**2),
        }
    if completed:
        data["verify_profile"] = read(root / "C-verify.time")
        data["actual"] = read(root / "C-clock-return.json")
        data["verify_resource"] = read(root / "C-verify.time.resource.json", 4 * 1024**2)
    return data


def check(control, contract, contract_sha, *, completed=False):
    audit = control.load("p17_m2_scientific_independent")
    clock = control.load("native_c_clock")
    roles = ("resource-preflight", "scientific-producer", "scientific-auditor")
    actual_roles = {role: control.load_role_evidence(contract, role) for role in roles}
    shared = [
        {
            **control.load_shared_helper_evidence(contract, role, label),
            "role": role,
            "action": label,
        }
        for role in roles[1:]
        for label in ("reservation", "reader-ack")
    ]
    evidence = evidence_for(control, contract, completed=completed)
    prefix = clock.native_prefix(contract, contract_sha, actual_roles, shared, evidence, audit)
    if completed:
        return clock.complete(contract, prefix, evidence, audit)
    return control.load("native_b_clock").prefix_stdout(
        contract_sha, evidence["start"], evidence["js_prefix"], "c"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--contract-sha", required=True)
    args = parser.parse_args()
    script = Path(__file__).resolve()
    if not sys.flags.isolated or Path.cwd() != script.parents[1]:
        parser.error("registered isolated C verifier checkout required")
    source = script.with_name("p17_m2_scientific_orchestration.py")
    spec = importlib.util.spec_from_file_location("p17_m2_scientific_orchestration", source)
    control = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(control)
    contract = control.read_contract(args.contract, args.contract_sha)
    verification = contract["c_caller_clock"]["verification_timed_argv"]
    profile = str(Path(contract["api_metadata"]["root"]) / "C-verify.time")
    if verification[:4] != ["/usr/bin/time", "-l", "-o", profile] or sys.orig_argv != (
        control.startup_argv(verification[4:], args.contract_sha, contract["runtime"])
    ):
        parser.error("C verifier command or native profile binding differs")
    sys.stdout.buffer.write(check(control, contract, args.contract_sha))


if __name__ == "__main__":
    main()
