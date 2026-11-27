"""Construct the fixed M2 contract from accepted metadata, without input IO.

The metadata arguments are projections of a separately accepted acquisition;
this constructor does not grant acceptance, leases, B admission or C execution.
Stage the builder before construction so the normal git-ls-files science freeze
includes it. Commit canonical output at CONTRACT_PATH and pass protected main CI
before publication checks or once-only B/C. No scientific root is probed here.

The registered auditor entry provides an explicit transport projection of the
existing independent summary: completed_rows becomes its count; the exact
original descriptors, immutable summary receipt and scientific decision remain.
"""

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PROPOSAL_PATH = "docs/planning/p17_m2_native_homotopy_proposal.json"
PROPOSAL_SHA256 = "966b47825dafde6653e0943bc7674082336f629e5e99a4ab4e8a6ada4b7c1434"
CONTRACT_PATH = "docs/planning/p17_m2_scientific_execution_protocol.json"
OUTPUT_ROOT = "/private/tmp/topolab-new-source-science-20261028/fixed-h17-20261104"
TOKEN = "@SCIENTIFIC_CONTRACT_SHA256@"
GIB = 1024**3
MIB = 1024**2
ROLES = ("resource-preflight", "scientific-producer", "scientific-auditor")
_ORCHESTRATION = None


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


def orchestration():
    global _ORCHESTRATION
    if _ORCHESTRATION is None:
        path = REPO / "scripts/p17_m2_scientific_orchestration.py"
        spec = importlib.util.spec_from_file_location("p17_m2_scientific_orchestration", path)
        need(spec is not None and spec.loader is not None, "scientific orchestration unavailable")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        _ORCHESTRATION = module
    return _ORCHESTRATION


def versioned_bytes(name):
    raw = (REPO / name).read_bytes()
    committed = subprocess.run(
        ["git", "show", "HEAD:" + name], cwd=REPO, capture_output=True, check=True, timeout=15
    ).stdout
    need(raw == committed, "versioned scientific metadata changed: " + name)
    return raw


def build_contract(acquisition, case_definitions, manifest, registry, *, runtime=None,
                   source_freeze=None, entry_root=None):
    """Return full canonicalizable metadata; never follow content_root or create it."""
    control = orchestration()
    canonical, sha = control.canonical, control.sha
    proposal_raw = versioned_bytes(PROPOSAL_PATH)
    need(sha(proposal_raw) == PROPOSAL_SHA256, "fixed scientific proposal changed")
    proposal = json.loads(proposal_raw)
    need(type(acquisition) is dict and set(acquisition) == {
        "plan_sha256", "version_id", "manifest_sha256", "content_root", "shared_packet_sha256"
    }, "exact accepted acquisition projection required")
    for key in ("plan_sha256", "version_id", "manifest_sha256", "shared_packet_sha256"):
        need(type(acquisition[key]) is str and re.fullmatch(r"[0-9a-f]{64}", acquisition[key]),
             "accepted acquisition hash differs: " + key)
    root = acquisition["content_root"]
    need(type(root) is str and root.startswith("/") and root.endswith("/content")
         and not any(part in ("", ".", "..") for part in root.split("/")[1:]),
         "literal accepted content root required")
    need(type(manifest) is dict and type(registry) is dict,
         "accepted manifest and registry metadata required")
    local = control.load("p17_m2_local_input_independent")
    local.validate_manifest(manifest, registry, manifest.get("frozen_contract_sha256"))
    manifest_sha = sha(canonical(manifest))
    need(acquisition["manifest_sha256"] == acquisition["version_id"] == manifest_sha,
         "accepted input version/manifest binding differs")
    pilot = proposal["prospective_pilot"]
    need(type(case_definitions) is list and len(case_definitions) == 18
         and sha(canonical(case_definitions)) == pilot["case_definitions_sha256"],
         "exact frozen18 case definitions required")
    from topolab.experiment import ExperimentCase

    cases = [ExperimentCase.model_validate(value) for value in case_definitions]
    need([case.case_id for case in cases] == pilot["case_ids"], "fixed18 case order differs")
    actual_runtime, actual_source = control.scientific_runtime(), control.source_manifest()
    need(runtime is None or runtime == actual_runtime, "actual scientific runtime required")
    need(source_freeze is None or source_freeze == actual_source,
         "complete actual scientific source manifest required")
    need(actual_runtime["platform"] == "darwin", "fixed M2 native Darwin runtime required")
    audit = control.load("p17_m2_scientific_independent")
    python = actual_runtime["python_entry"]
    program = str(REPO / "scripts/p17_m2_scientific_orchestration.py")
    contract_path = str(REPO / CONTRACT_PATH)
    output_root = OUTPUT_ROOT
    public = False
    if entry_root is not None:
        paths = control.load("native_bc_paths")
        release_scope = paths.scope(entry_root)
        public = release_scope == "ENGINEERING_PUBLIC"
        output_root = str(entry_root)
        if public:
            contract_path = str(paths.public_contract_path(entry_root))
        need(acquisition["plan_sha256"] == paths.PLAN
             and acquisition["version_id"] == paths.VERSION,
             "registered historical B1 plan and version required")
    roles, shared, actions = {}, {}, {}

    def watch(role, phase):
        return [python, "-I", str(REPO / "scripts/native_clock_watch.py"),
                "--contract", contract_path, "--contract-sha", TOKEN,
                "--role", role, "--phase", phase]

    def command(mode, role, *tail, script=program):
        return [python, "-I", script, mode, "--contract", contract_path,
                "--contract-sha", TOKEN, "--role", role, *tail]

    def dispatch(role, label, inner, timeout, *, helper=False):
        base = (output_root + "/shared/" + role + "-" + label if helper
                else roles[role]["root"] + "/" + label)
        spec = {
            "dispatch_argv": command("observe-native", role, "--label", label),
            "profile_path": base + ".time", "log_path": base + ".log",
            "dispatch_path": base + ".dispatch.json", "timeout_seconds": timeout,
        }
        timed = ["/usr/bin/time", "-l", "-o", spec["profile_path"], *inner]
        if helper:
            spec["argv"] = timed
        return spec, timed

    # Payload time leaves room for native controllers/exits and all360 per-row
    # recording seconds. Actual complete-charge gates still enforce each FULL.
    for role, full, payload_timeout, controller_timeout in zip(
        ROLES, (180, 10800, 3600), (None, 10200, 3000), (120, 10260, 3060), strict=True
    ):
        role_root = output_root + "/roles/" + role
        roles[role] = {
            "root": role_root, "FULL_seconds": full, "outer_invocations_max": 1,
            "argv": command("run", role, "--output", role_root),
            "reserve_argv": command("reserve", role),
            "publication_argv": command("publication-check", role),
            "publication_readiness_path": output_root + "/" + role + "-publication.json",
            "publication_return_path": output_root + "/" + role + "-publication-return.json",
            "exit_argv": {}, "native_dispatch": {},
        }
        spec = roles[role]
        if entry_root is not None:
            spec["publication_profile_path"] = output_root + "/" + role + "-publication.time"
            spec["publication_timed_argv"] = [
                "/usr/bin/time", "-l", "-o", spec["publication_profile_path"],
                *spec["publication_argv"],
            ]
            spec["publication_argv"] = watch(role, "publication")
        for label, prior in (("controller", None), ("binder", "controller"),
                             ("verifier", "binder"), ("final-observer", "verifier")):
            inner = (spec["argv"] if prior is None else
                     command("bind-exit", role, "--label", prior, "--observed-exit", "0"))
            native, timed = dispatch(role, label, inner,
                                     controller_timeout if prior is None else 20)
            spec["native_dispatch"][label] = native
            spec["exit_argv"][label] = timed
        shared[role] = {"reservation": dispatch(
            role, "reservation", spec["reserve_argv"], 20, helper=True
        )[0]}
        if role == "resource-preflight":
            controls = role_root + "/controls"
            spec["inner_starts"] = [
                {"name": "success", "argv": [python, "-I",
                 str(REPO / "scripts/p17_m2_homotopy.py"), "--public-fixture", "tiny-prefix",
                 "--output", controls + "/public-success.json"], "timeout_seconds": 30,
                 "expected_exit_code": 0, "expected_status": "PUBLIC_COMMAND_EXIT_OBSERVED"},
                {"name": "exit-seven", "argv": [python, "-I", program, "public-fixture",
                 "--case", "exit-seven"], "timeout_seconds": 10, "expected_exit_code": 7,
                 "expected_status": "FAIL_PUBLIC_COMMAND"},
                {"name": "timeout", "argv": [python, "-I", program, "public-fixture",
                 "--case", "timeout"], "timeout_seconds": 1, "expected_exit_code": -15,
                 "expected_status": "STOP_SCOPE_OR_WORK_CAP"},
            ]
        else:
            payload = (command("payload", role) if role == "scientific-producer" else
                       command("auditor-payload", role,
                               script=str(REPO / "scripts/build_m2_scientific_contract.py")))
            spec["inner_starts"] = [{"name": role + "-payload", "argv": payload,
                                     "timeout_seconds": payload_timeout, "expected_exit_code": 0,
                                     "expected_status": "PUBLIC_COMMAND_EXIT_OBSERVED"}]
            ack = command("ack", role)
            shared[role]["reader-ack"] = dispatch(role, "reader-ack", ack, 20, helper=True)[0]
            actions[role] = {"consume": payload, "ack": ack}
    target = "tlcase-v1-55c1b3e64135c23125fc286de5d780fc5d9a1e226d5e43ff0dbc8925b423936a"
    failures = {(target, seed) for seed in (17, 29, 43)} | {
        (case_id, 29) for case_id in proposal["acceptance"]["negative_control_case_ids"]
    }
    historical = [{"case_id": case_id, "seed": seed} for case_id in pilot["case_ids"]
                  for seed in (17, 29, 43) if (case_id, seed) not in failures]
    evidence = {}
    for label, name in (("report", "docs/validation/b4_30_paid_continuation.md"),
                        ("contract", "docs/planning/b4_30_z_reflection_repair_contract.json")):
        evidence[label + "_path"] = name
        evidence[label + "_sha256"] = sha(versioned_bytes(name))
    limits = {"max_files": 65536, "max_total_bytes": 512 * MIB,
              "max_record_bytes": 128 * MIB, "max_log_bytes": 4 * MIB,
              "max_profile_bytes": MIB, "max_manifest_bytes": 16 * MIB,
              "max_contract_bytes": 4 * MIB}
    value = {
        "schema": "topolab.v2.m2-scientific-contract.v1", "execution_identity": audit.IDENTITY,
        "proposal_sha256": PROPOSAL_SHA256, "permissions": {"B": True, "C": True},
        "public_fixture_only": False, "resource_limit_bytes": 4294967296,
        "shared_FULL_seconds": 180, "runtime": actual_runtime, "source_freeze": actual_source,
        "acquisition": deepcopy(acquisition), "input_version_id": acquisition["version_id"],
        "input_role_views": {
            role: list(dict.fromkeys([*manifest["role_views"][role], "uniform-scalars.json"]))
            for role in ROLES[1:]
        },
        "reader_actions": actions, "case_definitions": deepcopy(case_definitions),
        "call_plan": control.load("p17_m2_scientific_control").build_call_plan(proposal),
        "independent_operation_caps": dict(audit.OPERATIONS),
        "historical_accepted_P_units": historical, "historical_accepted_P_evidence": evidence,
        "roles": roles, "shared_helpers": shared,
        "output_caps": {
            "scientific-producer": {"single_member_bytes_max": 16 * MIB,
                                     "total_bytes_max": 8 * GIB, "files_max": 1024},
            "scientific-auditor": {"single_member_bytes_max": 16 * MIB,
                                    "total_bytes_max": 2 * GIB, "files_max": 512},
        },
        "scientific_available_bytes_min": 12 * GIB,
        "output_caps_basis": "producer full360 scalar traces, initial/prefix16/transitions2/"
                             "recent11 and complete terminal windows retained;16MiB each, "
                             "721 normal producer files/361 auditor files; no truncation; "
                             "actual overflow STOP never widens this domain",
        "disk_reservation_basis": "8GiB producer +2GiB auditor +512MiB metadata +32MiB two "
                                  "manifests +remaining1504MiB startup/failure/output margin; "
                                  "actual available disk remains a future checked gate",
        "new_output_directories_before_reservation": [output_root, output_root + "/roles",
                                                       output_root + "/shared"],
        "api_metadata": {"schema": "topolab.v2.m2-api-metadata-policy.v1", "root": output_root,
                         "sample_interval_seconds": 0.5, "limits": limits,
                         "manifests": {"B": output_root + "/B-metadata-manifest.json",
                                       "FINAL": output_root + "/FINAL-metadata-manifest.json"}},
        "auditor_transport_projection": {
            "schema": "topolab.v2.m2-auditor-completion-transport.v1",
            "count_field": "completed_rows", "descriptors_field": "completed_row_descriptors",
            "original_summary_packet_unchanged": True,
            "scientific_decision_status_and_predicates_unchanged": True,
        },
        "stop_policy": "first named failure/UNKNOWN: STOP_NO_RETRY; no quota transfer; "
                       "ordinary scientific failures remain failed and fully charged",
    }
    if entry_root is not None:
        value.update({
            "entry_repair": paths.IDENTITY,
            "public_fixture_only": public,
            "historical_issuer_commit": paths.HISTORICAL,
            "host_requirement": {"cpu_brand": "Apple M2", "machine": "arm64",
                                 "rss_bytes_max": 4 * GIB},
            "budget_assignment": {
                "B_all_startup_reservation_to_observed_final_return_FULL": 180,
                "C_producer_single_charge_cap": 10800, "C_independent_single_charge_cap": 3600,
                "C_shared_prepare_control_and_closeout_FULL": 180, "mutual_transfers": False,
            },
            "activation_order": ["independent source and protected release review",
                                 "independent B public controls", "C producer",
                                 "C independent auditor",
                                 "final original return and archive"],
            "scientific_release": {
                "scope": release_scope,
                "evidence_root": str(entry_root) if public else str(paths.EVIDENCE),
                "basename": "scientific-release.json",
            },
        })
        for stage, schema in (("B", "topolab.b-full-clock.v1"),
                              ("C", "topolab.c-shared-clock.v1")):
            value[stage.lower() + "_caller_clock"] = {
                "schema": schema,
                "author": ("/root" if public and not output_root.endswith("-merged")
                           else "/root/authorize"),
                "verification_argv": watch(ROLES[0] if stage == "B" else ROLES[2],
                                           "verification"),
                "verification_timed_argv": [
                    "/usr/bin/time", "-l", "-o", output_root + "/" + stage + "-verify.time",
                    python, "-I", str(REPO / "scripts" / f"native_{stage.lower()}_prefix.py"),
                    "--contract", contract_path, "--contract-sha", TOKEN,
                ],
            }
    need([len(value["input_role_views"][r]) for r in ROLES[1:]] == [542, 1070],
         "complete fixed scientific role unions required")
    need(len(canonical(value)) <= limits["max_contract_bytes"], "scientific contract4MiB cap")
    audit.check_contract(value)
    return value


def project_auditor_completion(contract, payload):
    """Project only completion representation, retaining the original audit bytes."""
    control = orchestration()
    summary = payload["result"]
    descriptors = summary["completed_rows"]
    expected = [
        {"phase": phase, "ordinal": row["ordinal"], "case_id": row["case_id"],
         "method": row["method"]}
        for phase, key in (("reference", "references"), ("query", "queries"))
        for row in contract["call_plan"][key]
    ]
    need(summary.get("schema") == "topolab.v2.m2-scientific-auditor-summary.v1"
         and summary.get("attempted_rows") == 360 and type(descriptors) is list
         and len(descriptors) == len(expected) == 360,
         "complete independent auditor descriptor list required")
    for actual, wanted in zip(descriptors, expected, strict=True):
        need(type(actual) is dict and set(actual) == set(wanted) | {"attempt_accepted"}
             and all(actual[k] == v for k, v in wanted.items())
             and type(actual["attempt_accepted"]) is bool,
             "independent auditor completion order/fields differ")
    original = {key: value for key, value in summary.items() if key != "summary_packet"}
    raw = control.canonical(original)
    receipt = summary["summary_packet"]
    need(receipt == {"path": "auditor-summary.json", "byte_size": len(raw),
                     "sha256": control.sha(raw)}, "original independent summary receipt differs")
    projected = deepcopy(payload)
    projected["result"]["completed_rows"] = len(descriptors)
    projected["result"]["completed_row_descriptors"] = deepcopy(descriptors)
    projected["result"]["completion_transport_projection"] = {
        **contract["auditor_transport_projection"], "source_summary_packet": deepcopy(receipt),
        "source_descriptors_sha256": control.sha(control.canonical(descriptors)),
    }
    return projected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("construct", "auditor-payload"))
    parser.add_argument("--metadata", type=Path)
    parser.add_argument("--entry-root", type=Path)
    parser.add_argument("--contract", type=Path)
    parser.add_argument("--contract-sha")
    parser.add_argument("--role")
    args = parser.parse_args()
    control = orchestration()
    if args.mode == "construct":
        need(args.metadata is not None and args.contract is None and args.contract_sha is None
             and args.role is None, "explicit accepted metadata only required for construction")
        need(control.source_manifest().get("scripts/build_m2_scientific_contract.py")
             == control.sha(Path(__file__).read_bytes()),
             "tracked builder source required before release contract construction")
        with args.metadata.open("rb") as stream:
            raw = stream.read(16 * MIB + 1)
        need(len(raw) <= 16 * MIB, "accepted metadata16MiB cap")
        metadata = control.load("p17_m2_input_export_independent").parse(raw)
        need(type(metadata) is dict and set(metadata) == {
            "acquisition", "case_definitions", "manifest", "registry"
        }, "complete accepted metadata fields required")
        result = build_contract(**metadata, entry_root=args.entry_root)
    else:
        need(args.metadata is None and args.entry_root is None
             and args.contract is not None and args.contract_sha is not None
             and args.role == "scientific-auditor" and sys.flags.isolated == 1
             and Path.cwd() == REPO, "registered isolated auditor payload required")
        contract = control.read_contract(args.contract, args.contract_sha,
                                         payload_role="scientific-auditor")
        result = project_auditor_completion(contract, control.scientific_payload(
            contract, args.contract_sha, "scientific-auditor"
        ))
    sys.stdout.buffer.write(control.canonical(result))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
