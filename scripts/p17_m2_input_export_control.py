"""Explicit R-STABLE production binding; F remains public-fixture only."""

import argparse
import hashlib
import importlib.util
import json
import math
import os
import platform
import resource
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = Path("/Users/keith1117/Documents/TopoLab-data/p17-m2-input-export-preparation-v3")
IDENTITY = "topolab.v2.p17-m2-input-export-preparation.v3"
F_IDENTITY = "topolab.v2.p17-m2-input-failure-diagnostic-repair.v1"
STABLE_IDENTITY = "topolab.v2.p17-m2-source-stable-export.v1"
STABLE_ROOT = ROOT.parent / "p17-m2-source-stable-export-v1"
STABLE_CAPS = {"independent-public-check": 300, "exporter-r0": 300,
               "independent-r0": 300, "exporter-r1": 1200,
               "independent-r1": 1200, "shared-closeout": 300}
STABLE_PROTOCOL = "docs/planning/p17_m2_source_stability_export_protocol.json"
FINAL_HELPER_ROOT = Path("/private/tmp/topolab-r-stable-software-20261020/final-helper")
SOURCE_NAMESPACES = {"b3-v1-fits", "b4-5-weighted-terminal/fit", "b3-v1-data",
                     "b4-30-z-reflection-repair-v2"}
CONTENT_SHA = "f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad"
CLOCK = "functions.exec.Date.now.UTC-seconds"
# -I excludes script-directory imports. Bind this stdlib-only helper explicitly.
HELPER_SPEC = importlib.util.spec_from_file_location(
    "p17_m2_homotopy", REPO / "scripts/p17_m2_homotopy.py"
)
assert HELPER_SPEC and HELPER_SPEC.loader
helper = importlib.util.module_from_spec(HELPER_SPEC)
sys.modules["p17_m2_homotopy"] = helper
HELPER_SPEC.loader.exec_module(helper)
SPEC = importlib.util.spec_from_file_location(
    "r_native_recording", REPO / "scripts/p17_m2_resource_control.py"
)
assert SPEC and SPEC.loader
native_recording = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native_recording)
AUDIT_SPEC = importlib.util.spec_from_file_location(
    "r_independent_receipt_audit", REPO / "scripts/p17_m2_input_export_independent.py"
)
assert AUDIT_SPEC and AUDIT_SPEC.loader
independent = importlib.util.module_from_spec(AUDIT_SPEC)
AUDIT_SPEC.loader.exec_module(independent)
CAPS = {
    "independent-public-check": 120,
    "exporter-r0": 120,
    "independent-r0": 120,
    "exporter-r1": 780,
    "independent-r1": 660,
    "shared-closeout": 60,
}
ACTOR_WINDOW = 2700
SOURCE_FILES = {
    "scripts/p17_m2_input_export.py",
    "scripts/p17_m2_input_export_independent.py",
    "scripts/p17_m2_input_export_control.py",
    "scripts/p17_m2_resource_control.py",
    "scripts/p17_m2_homotopy.py",
    "scripts/p17_m2_input_export_dispatch.js",
    "uv.lock",
    "docs/planning/p17_m2_input_export_preparation_proposal.json",
    "docs/planning/p17_m2_input_export_billing_revision_proposal.json",
    "docs/planning/p17_m2_input_export_billing_revision_protocol.md",
    "docs/planning/p17_m2_input_export_readiness_protocol.md",
    "docs/planning/p17_m2_input_export_readiness_protocol.json",
}


def configure_stable():
    """Explicit NEW production binding; no old identity or F mode grants R."""
    global ROOT, IDENTITY, CAPS, ACTOR_WINDOW, SOURCE_FILES
    ROOT, IDENTITY, CAPS, ACTOR_WINDOW = STABLE_ROOT, STABLE_IDENTITY, STABLE_CAPS.copy(), 4500
    SOURCE_FILES = SOURCE_FILES | {
        "docs/planning/p17_m2_source_stability_export_proposal.md",
        "docs/planning/p17_m2_source_stability_export_proposal.json",
        "docs/planning/p17_m2_source_stability_export_protocol.md", STABLE_PROTOCOL}


def stable_controls_checked(controls, activation):
    require(controls["schema"] == "topolab.v2.m2-writer-quiescence.v1"
            and controls["execution_identity"] == STABLE_IDENTITY
            and controls["custodian"] == "/root"
            and controls["no_write_until_release"] is True,
            "new attributed in-place custodian controls")
    require(set(controls["namespaces"]) == SOURCE_NAMESPACES, "exact source namespaces")
    names = set()
    for writer in controls["writers"]:
        require(isinstance(writer["name"], str) and writer["name"]
                and writer["name"] not in names and writer["namespace"] in SOURCE_NAMESPACES
                and (writer["action"], writer["status"]) in {
                    ("pause", "PAUSED_ACKNOWLEDGED"), ("exclude", "EXCLUDED_CUSTODIAN_CONTROL")}
                and isinstance(writer["evidence"], str) and writer["evidence"],
                "every named writer actually controlled with evidence")
        names.add(writer["name"])
    for namespace, coverage in controls["namespaces"].items():
        require(coverage["accepted"] is True and isinstance(coverage["basis"], str)
                and bool(coverage["basis"].strip()), "UNKNOWN writer coverage refuses activation")
        if not any(w["namespace"] == namespace for w in controls["writers"]):
            require(isinstance(coverage.get("no_writer_explanation"), str)
                    and bool(coverage["no_writer_explanation"].strip()),
                    "affirmative no-writer explanation required")
    ack = controls["acquisition_ack"]
    require(ack["by"] == controls["custodian"] and isinstance(ack["basis"], str)
            and bool(ack["basis"].strip())
            and type(ack["UTC_seconds"]) in (int, float)
            and math.isfinite(ack["UTC_seconds"])
            and activation <= ack["UTC_seconds"] <= activation + 300,
            "actual custodian acquisition acknowledgement inside setup300")


def stable_authority_checked(protocol):
    require(protocol["execution_identity"] == STABLE_IDENTITY
            and protocol["owner_grant"]["approved"] is True
            and protocol.get("actual_admission", {}).get("status")
                != "NO_SOURCE_ADMISSION_KEEP_STOP", "closed unlaunched R-STABLE authority")


def stable_lease_checked(plan, plan_sha):
    controls = plan["source_controls"]
    stable_controls_checked(controls, plan["actor_activation_UTC_seconds"])
    raw = read(ROOT / "writer_quiescence.json")
    require(raw == canonical(controls) and digest(raw) == plan["source_controls_sha256"],
            "immutable source control bytes")
    expected = {"execution_identity": STABLE_IDENTITY, "plan_sha256": plan_sha,
                "control_sha256": plan["source_controls_sha256"],
                "custodian": controls["custodian"],
                "acquired_UTC_seconds": controls["acquisition_ack"]["UTC_seconds"], "active": True}
    require(json.loads(read(ROOT / "source-lease.json")) == expected,
            "exclusive new lease and plan binding")
    require(not os.path.lexists(ROOT / "source-release.json"), "source interval already released")


def validate_stable_source_entry(path, expected, role):
    configure_stable()
    require(role in CAPS, "registered new source role")
    plan = plan_checked(path, expected)
    stable_lease_checked(plan, expected)
    source_gate(plan, role, expected)
    write(ROOT / ("source-access-" + role + ".json"), {
        "execution_identity": STABLE_IDENTITY, "plan_sha256": expected,
        "role": role, "first_entry_UTC_seconds": time.time(), "retry": False})
    return plan


def require(ok, reason):
    if not ok:
        raise ValueError("R_STOP: " + reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def read(path, cap=16 * 1024 * 1024, *, allow_empty=False):
    require(
        path.resolve() == path.absolute()
        and not path.is_symlink()
        and (0 if allow_empty else 1) <= path.stat().st_size <= cap,
        "new bounded literal record",
    )
    return path.read_bytes()


def write(path, value):
    raw = canonical(value)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        import os

        os.fsync(stream.fileno())


def external_templates(python):
    return {
        role: [
            [python, "-I", str(Path(__file__).resolve()), mode,
             *(["--r-stable"] if IDENTITY == STABLE_IDENTITY else []), "--plan",
             str(ROOT / "launch_plan.json"), "--plan-sha", "<PLAN_SHA256>", "--role", role]
            for mode in ("supervise", "finalize")
        ] for role in CAPS
    }


def resolved(argv, plan_sha):
    return [word.replace("<PLAN_SHA256>", plan_sha) for word in argv]


def actor_window_checked(plan, now):
    activation = plan["actor_activation_UTC_seconds"]
    require(type(activation) in (int, float) and math.isfinite(activation)
            and activation > 0 and round(activation, 3) == activation,
            "actual millisecond activation required")
    deadline = activation + ACTOR_WINDOW
    iso = datetime.fromtimestamp(deadline, UTC).isoformat(
        timespec="milliseconds").replace("+00:00", "Z")
    require(type(plan["actor_window_seconds"]) is int
            and plan["actor_window_seconds"] == ACTOR_WINDOW
            and plan["actor_deadlines_UTC"] == {"exporter": iso, "independent": iso}
            and activation <= now <= deadline,
            "immutable readiness-activated actor window")


def create_plan(activation, ci_path, controls_path=None):
    """One NEW plan after release readiness; never opens historical DATA files."""
    require(subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO) == b"",
            "clean merged source before activation")
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()
    require(head == subprocess.check_output(
        ["git", "rev-parse", "origin/main"], cwd=REPO).decode().strip(), "merged main only")
    require(not ci_path.absolute().is_relative_to(ROOT.parent), "CI evidence outside DATA")
    ci_raw = read(ci_path, 4 * 1024 * 1024)
    ci = json.loads(ci_raw)
    jobs = ci["jobs"]
    require(ci["headSha"] == head and ci["headBranch"] == "main" and ci["event"] == "push"
            and type(ci["databaseId"]) is int and ci["databaseId"] > 0
            and ci["url"] == f"https://github.com/keith1117/TopoLab/actions/runs/{ci['databaseId']}"
            and ci["status"] == "completed"
            and ci["conclusion"] == "success"
            and len(jobs) == 4
            and {job["name"] for job in jobs} == {
                "quality", "frontend", "clean-linux-smoke", "i1-native-software"}
            and all(job["status"] == "completed" and job["conclusion"] == "success"
                    for job in jobs), "all four exact-main CI jobs required")
    require(sys.platform == "darwin" and platform.machine() == "arm64",
            "M2 native Darwin only")
    require(all(os.environ.get(k) == v for k, v in native_recording.ENVIRONMENT.items()),
            "locked five-thread environment")
    python = sys.executable
    control = str(Path(__file__).resolve())
    export = str(REPO / "scripts/p17_m2_input_export.py")
    audit = str(REPO / "scripts/p17_m2_input_export_independent.py")
    content = str(REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json")
    registry = str(ROOT / "exporter-r0/source_registry.json")
    source = ["--data-root", str(ROOT.parent), "--contract", content, "--authorize-old-read"]
    stable = IDENTITY == STABLE_IDENTITY
    if stable:
        require(controls_path is not None
                and not controls_path.absolute().is_relative_to(ROOT.parent),
                "new custodian package outside DATA required")
        controls = json.loads(read(controls_path))
        stable_controls_checked(controls, activation)
        protocol = json.loads((REPO / STABLE_PROTOCOL).read_bytes())
        stable_authority_checked(protocol)
        require(protocol["execution_identity"] == STABLE_IDENTITY
                and protocol["owner_grant"]["approved"] is True
                and protocol["formal_roles_FULL_seconds"] == CAPS,
                "new owner-approved protocol, not old grant")
        source += ["--execution-identity", STABLE_IDENTITY, "--plan",
                   str(ROOT / "launch_plan.json"), "--plan-sha", "<PLAN_SHA256>"]
    payloads = {
        "independent-public-check": [python, "-I", audit, "public-check", "--fixture-root",
            str(ROOT / "public-fixtures"), "--output", str(ROOT / "independent-public-check.json")],
        "exporter-r0": [python, "-I", export, "r0", *source, "--output",
            str(ROOT / "exporter-r0")],
        "independent-r0": [python, "-I", audit, "r0", *source, "--registry", registry,
            "--output", str(ROOT / "independent-r0.json")],
        "exporter-r1": [python, "-I", export, "r1", *source, "--registry", registry,
            "--independent-r0", str(ROOT / "independent-r0.json"), "--output",
            str(ROOT / "exporter-r1")],
        "independent-r1": [python, "-I", audit, "r1", *source, "--registry", registry,
            "--exports-root", str(ROOT / "exporter-r1/exports"), "--output",
            str(ROOT / "independent-r1.json")],
        "shared-closeout": [python, "-I", control, "archive", "--plan",
            str(ROOT / "launch_plan.json"), "--plan-sha", "<PLAN_SHA256>", "--role",
            "shared-closeout"],
    }
    if stable:
        payloads["independent-public-check"] += ["--execution-identity", STABLE_IDENTITY,
            "--plan", str(ROOT / "launch_plan.json"), "--plan-sha", "<PLAN_SHA256>"]
        payloads["shared-closeout"].append("--r-stable")
    deadline = datetime.fromtimestamp(activation + ACTOR_WINDOW, UTC).isoformat(
        timespec="milliseconds").replace("+00:00", "Z")
    plan = {
        "execution_identity": IDENTITY,
        ("owner_R_STABLE_authorized" if stable else "owner_R_v3_authorized"): True,
        "B_C_authorized": False, "repository": str(REPO),
        "merged_source": head,
        "merged_tree": subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=REPO).decode().strip(),
        "source_files": {name: digest((REPO / name).read_bytes()) for name in sorted(SOURCE_FILES)},
        "content_sha256": CONTENT_SHA, "all_four_main_CI_success": True,
        "main_CI": ci, "main_CI_raw_sha256": digest(ci_raw),
        "host_machine": platform.machine(), "host_platform": sys.platform,
        "host_os_release": platform.release(), "python_executable": python,
        "python_version": platform.python_version(),
        "thread_environment": native_recording.ENVIRONMENT,
        "authors": {"exporter": "/root", "independent": (
            "/root/review_r_stable_export_v1" if stable else "/root/review_r_v3")},
        "actor_activation_UTC_seconds": activation, "actor_window_seconds": ACTOR_WINDOW,
        "actor_deadlines_UTC": {"exporter": deadline, "independent": deadline},
        "FULL_caps_seconds": CAPS, "clock_domain": CLOCK, "clock_resolution_seconds": 0.001,
        "external_argv": external_templates(python),
        "roles": {role: {"cap_seconds": CAPS[role], "argv": argv}
                  for role, argv in payloads.items()},
    }
    if stable:
        plan["output_root"] = str(ROOT)
        plan.update(source_controls=controls, source_controls_sha256=digest(canonical(controls)),
                    helper_inventory=protocol["helper_inventory"],
                    public_fixture_table=protocol["public_fixture_table"],
                    runtime_binaries={p: digest(Path(p).read_bytes())
                                      for p in (sys.executable, "/usr/bin/time", "/bin/ps")},
                    formal_overhead_caps={"plan_lease": 300, "between_roles_total": 240,
                                          "final_frontier_retention_and_release": 360})
        plan["final_helper_external_argv"] = [python, "-I", control, "final-helper", "--r-stable",
            "--plan", str(ROOT / "launch_plan.json"), "--plan-sha", "<PLAN_SHA256>"]
        plan["final_filing_child_argv"] = [python, "-I", control, "final-file", "--r-stable",
            "--plan", str(ROOT / "launch_plan.json"), "--plan-sha", "<PLAN_SHA256>"]
        plan["final_helper_root"] = str(FINAL_HELPER_ROOT)
    actor_window_checked(plan, time.time())
    require(time.time() + sum(CAPS.values()) + (600 if stable else 0) <= activation + ACTOR_WINDOW,
            "complete six-role reserve before plan creation")
    require(not os.path.lexists(ROOT)
            and not os.path.lexists(ROOT.with_name(ROOT.name + "-independent-backup")),
            "exclusive NEW roots; no overwrite or retry")
    ROOT.mkdir(exist_ok=False)
    if stable:
        write(ROOT / "writer_quiescence.json", controls)
    raw = canonical(plan)
    write(ROOT / "launch_plan.json", plan)
    plan_sha = digest(raw)
    if stable:
        write(ROOT / "source-lease.json", {
            "execution_identity": STABLE_IDENTITY, "plan_sha256": plan_sha,
            "control_sha256": plan["source_controls_sha256"], "custodian": controls["custodian"],
            "acquired_UTC_seconds": controls["acquisition_ack"]["UTC_seconds"], "active": True})
    context = dict(plan, plan_sha256=plan_sha)
    context["external_argv"] = {role: [resolved(argv, plan_sha) for argv in calls]
                                for role, calls in plan["external_argv"].items()}
    return context


def plan_checked(path, expected, *, result_filing=False):
    require(path.absolute() == ROOT / "launch_plan.json", "literal new plan")
    raw = read(path)
    require(digest(raw) == expected, "plan freeze changed")
    plan = json.loads(raw)
    require(
        subprocess.check_output(["git", "status", "--porcelain"], cwd=REPO) == b"",
        "clean frozen tree",
    )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO).decode().strip()
    require(head == plan["merged_source"], "source commit changed")
    require(set(plan["source_files"]) == SOURCE_FILES, "complete source freeze")
    tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=REPO).decode().strip()
    require(tree == plan["merged_tree"], "merged source tree changed")
    for name, h in plan["source_files"].items():
        require(digest((REPO / name).read_bytes()) == h, "frozen source bytes changed")
    require(
        plan["all_four_main_CI_success"] is True
        and plan["owner_R_STABLE_authorized" if IDENTITY == STABLE_IDENTITY
                 else "owner_R_v3_authorized"] is True
        and plan["B_C_authorized"] is False,
        "admission record",
    )
    require(
        plan["execution_identity"] == IDENTITY
        and plan["content_sha256"] == CONTENT_SHA
        and plan["FULL_caps_seconds"] == CAPS
        and plan["clock_domain"] == CLOCK
        and plan["clock_resolution_seconds"] == 0.001,
        "new identity/FULL/content/clock binding",
    )
    actor_window_checked(plan, min(time.time(), plan["actor_activation_UTC_seconds"] + ACTOR_WINDOW)
                         if result_filing else time.time())
    require(not result_filing or (IDENTITY == STABLE_IDENTITY
            and time.time() >= plan["actor_activation_UTC_seconds"]), "new result filing only")
    if IDENTITY == STABLE_IDENTITY:
        stable_authority_checked(json.loads((REPO / STABLE_PROTOCOL).read_bytes()))
        require(Path.cwd() == REPO == Path(plan["repository"]), "actual frozen repository cwd")
        require(plan["authors"] == {"exporter": "/root", "independent":
                                   "/root/review_r_stable_export_v1"}, "fresh different author")
        require(set(plan["runtime_binaries"]) == {sys.executable, "/usr/bin/time", "/bin/ps"},
                "literal registered runtime helpers")
        for binary, h in plan["runtime_binaries"].items():
            require(digest(Path(binary).read_bytes()) == h, "frozen runtime helper changed")
    require(sys.platform == "darwin", "M2 native Darwin execution only")
    require(plan["external_argv"] == external_templates(sys.executable),
            "complete literal supervisor/finalizer call table")
    require(
        platform.machine() == "arm64"
        and plan["host_machine"] == platform.machine()
        and plan["host_platform"] == sys.platform
        and plan["python_executable"] == sys.executable
        and plan["python_version"] == platform.python_version()
        and plan["host_os_release"] == platform.release()
        and plan["thread_environment"] == native_recording.ENVIRONMENT
        and all(os.environ.get(k) == v for k, v in native_recording.ENVIRONMENT.items()),
        "actual frozen interpreter/M2/thread identity",
    )
    return plan


def final_packet_checked(plan, plan_sha):
    raw = os.environ.get("TOPOLAB_RSTABLE_PREVIOUS_TOOL_RECORDS", "[]")
    require(len(raw.encode()) <= 4 * 1024 * 1024, "finite final trusted packet")
    packets = json.loads(raw)
    require(isinstance(packets, list) and len(packets) == 1, "one final shared-return packet")
    packet = packets[0]
    require(packet["pending"]["execution_identity"] == STABLE_IDENTITY
            and packet["pending"]["role"] == "shared-closeout"
            and packet["pending"]["plan_sha256"] == plan_sha
            and packet["terminal"]["status"] == "PASS_R_STABLE_FULL_ROLE"
            and packet["terminal"]["cleanup"]["group_gone"] is True,
            "actual complete shared return and cleanup before final helper")
    t1 = packet["events"][-1]["end_seconds"]
    closed = packet["formal_close_UTC_seconds"]
    ack = packet["custodian_release"]
    require(t1 <= closed <= t1 + 360
            and closed <= plan["actor_activation_UTC_seconds"] + 4500
            and ack == {"by": plan["source_controls"]["custodian"], "UTC_seconds": closed,
                        "plan_sha256": plan_sha, "source_roles_closed": True}
            and closed <= time.time() <= closed + 7200,
            "actual custodian release/formal close and bounded result phase")
    return packet


def final_file(plan, plan_sha):
    """NEW-only last packet filing; independent exact backup, no source read."""
    packet = final_packet_checked(plan, plan_sha)
    ingest_external(plan, plan_sha, closing=True)
    observed = json.loads(read(ROOT / "receipts/shared-closeout-observed.json"))
    require(observed["status"] == "PASS_R_STABLE_FULL_ROLE", "independent shared replay")
    write(ROOT / "source-release.json", packet["custodian_release"])
    write(ROOT / "formal-close.json", {"UTC_seconds": packet["formal_close_UTC_seconds"],
                                      "plan_sha256": plan_sha, "no_successor": True})
    backup = ROOT.with_name(ROOT.name + "-independent-backup")
    backup_late(backup)
    first = independent.audit_new_backup(ROOT, backup, execution_identity=STABLE_IDENTITY)
    write(ROOT / "final-backup-manifest.json", first)
    write(backup / "final-backup-manifest.json", first)
    result = independent.audit_new_backup(ROOT, backup, execution_identity=STABLE_IDENTITY)
    return {key: result[key] for key in ("status", "member_count", "total_bytes")} | {
                     "shared_packet_sha256": digest(canonical(packet)),
                     "shared_role_status": observed["status"], "plan_sha256": plan_sha,
                     "formal_close_UTC_seconds": packet["formal_close_UTC_seconds"]}


def final_helper(plan, plan_sha):
    """One <=180s result helper; native child plus parent pre/post RSS and actual outer exit."""
    final_packet_checked(plan, plan_sha)
    require(plan["final_helper_root"] == str(FINAL_HELPER_ROOT), "literal new filing recorder")
    argv = resolved(plan["final_filing_child_argv"], plan_sha)
    expected = [sys.executable, "-I", str(Path(__file__).resolve()), "final-file", "--r-stable",
                "--plan", str(ROOT / "launch_plan.json"), "--plan-sha", plan_sha]
    require(argv == expected, "frozen final filing command")
    before_rss = native_recording._rss_self()
    record, raw_result, primary, secondary = None, None, None, []
    inner = FINAL_HELPER_ROOT / "final-filing"
    try:
        record = native_recording.invoke(FINAL_HELPER_ROOT, "final-filing", argv,
                                         timeout=160, limit_bytes=4294967296)
        if record["exit_code"] != 0 or record["software_result"] != "PUBLIC_COMMAND_EXIT_OBSERVED":
            primary = {"stage": "final-filing-child", "exit_code": record["exit_code"],
                       "reason": record["software_result"]}
        helpers = {h["profile"]: read(inner / h["profile"], 1048576) for h in record["helpers"]}
        independent.audit_native_record(record, profile=read(inner / "command.time", 1048576),
            log=read(inner / "command.log", allow_empty=True), helper_profiles=helpers,
            expected_role="final-filing", expected_argv=expected, platform=sys.platform,
            failure_recording=True)
        raw_result = json.loads(read(inner / "command.log"))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        failure = {"stage": "final-filing-recording", "type": type(exc).__name__,
                   "reason": str(exc)[:512]}
        if primary is None:
            primary = failure
        else:
            secondary.append(failure)
    packet = {"schema": "topolab.v2.m2-source-stable-final-filing.v1",
              "execution_identity": STABLE_IDENTITY,
              "status": ("PENDING_EXTERNAL_EXIT" if primary is None
                         else "FAILED_INTERNAL_COMPLETION"),
              "plan_sha256": plan_sha, "inner_argv_sha256": digest(canonical(expected)),
              "controller_RSS_samples_bytes": [before_rss, 0],
              "controller_RSS_unit": "bytes", "filing_result": raw_result,
              "native_record_root": str(inner), "primary_failure": primary,
              "secondary_failures": secondary,
              "available_child_exit": None if record is None else record.get("exit_code")}
    canonical(packet)
    packet["controller_RSS_samples_bytes"][1] = native_recording._rss_self()
    print(canonical(packet).decode(), end="", flush=True)
    return 0 if primary is None else 1


def recording_options(plan):
    if plan.get("execution_identity") == STABLE_IDENTITY:
        return {"failure_recording": True, "execution_identity": STABLE_IDENTITY}
    return {"failure_recording": plan.get("execution_identity") == F_IDENTITY}


def bind(plan, role, controller_exit, plan_sha):
    failure_recording = plan.get("execution_identity") in (F_IDENTITY, STABLE_IDENTITY)
    base = ROOT / "receipts"
    record_path = base / role / role / "command.json"
    record = json.loads(read(record_path, 4 * 1024 * 1024))
    profile = base / (role + "-controller.time")
    measured = native_recording.native(read(profile, 1024 * 1024).decode(), sys.platform)
    require(
        type(controller_exit) is int
        and (controller_exit == 0 or failure_recording)
        and (record["exit_code"] == 0 or failure_recording)
        and record["software_result"] in (
            ("PUBLIC_COMMAND_EXIT_OBSERVED", "FAIL_PUBLIC_COMMAND") if failure_recording
            else ("PUBLIC_COMMAND_EXIT_OBSERVED",))
        and record["cleanup"]["group_gone"] is True,
        "observed role success and full exit",
    )
    require(record["argv"] == resolved(plan["roles"][role]["argv"], plan_sha), "actual argv")
    require(
        record["native"]
        and record["timer_native_exit"]
        and record["native_plus_controller_and_sampler_rss_bytes"] is not None,
        "native role/helper profile coverage",
    )
    inner_root = record_path.parent
    require(len(record["helpers"]) <= 4096, "bounded sampler count")
    helpers = {}
    for i, h in enumerate(record["helpers"]):
        name = f"sampler-{i}.time"
        require(
            h["profile"] == name and h["role"] == f"rss-sampler-{i}",
            "literal sampler identity before any read",
        )
        helpers[name] = read(inner_root / name, 1024 * 1024)
    reconciled = independent.audit_native_record(
        record,
        profile=read(inner_root / "command.time", 1024 * 1024),
        log=read(inner_root / "command.log", 16 * 1024 * 1024, allow_empty=True),
        helper_profiles=helpers,
        expected_role=role,
        expected_argv=resolved(plan["roles"][role]["argv"], plan_sha),
        platform=sys.platform,
        **({"failure_recording": True} if failure_recording else {}),
    )
    rss = reconciled["inner_empirical_RSS_bytes"] + measured["rss_bytes"]
    require(0 < rss <= 4294967296, "recorded role RSS envelope")
    charge = (
        max(
            record["native"]["wall_seconds"],
            record["observed_outer_wall_seconds"],
            measured["wall_seconds"],
        )
        + 10
    )
    require(charge <= CAPS[role], "role charge cap")
    result = {
        "schema": "topolab.v2.m2-input-export-inner-exit-diagnostic.v2",
        "role": role,
        "plan_sha256": plan_sha,
        "status": "PENDING_BINDER_NATIVE_EXIT",
        "controller_exit": controller_exit,
        "command_exit": record["exit_code"],
        "record_sha256": digest(read(record_path)),
        "profile_sha256": digest(read(profile)),
        "controller_native": measured,
        "conservative_RSS_bytes": rss,
        "charge_before_binder_wall_seconds": charge,
        "role_cap_seconds": CAPS[role],
        "independent_inner_receipt_reconciliation": reconciled,
        "B_C_run": False,
    }
    if plan.get("execution_identity") == STABLE_IDENTITY:
        result["domain_status"] = "PASS" if record["exit_code"] == 0 else "STOP"
    write(base / (role + "-exit.json"), result)
    return result


def stop_registered(role, outer_pid):
    """Only this launch's observed descendant/session groups may be signalled."""
    folder = ROOT / "receipts" / role / role
    known = []
    started = folder / "started.json"
    if started.exists():
        packet = json.loads(read(started))
        require(
            packet["role"] == role
            and packet["status"] == "STARTED"
            and type(packet["pid"]) is int
            and packet["pid"] > 1,
            "registered timeout child",
        )
        known.append(packet["pid"])
    snapshot = ROOT / "receipts" / (role + "-timeout-snapshot")
    snapshot.mkdir(exist_ok=False)
    rows, helper = native_recording._snapshot(snapshot, 0, outer_pid, tuple(known))
    groups = {outer_pid, *known, *(row["pgid"] for row in rows)}
    require(os.getpgrp() not in groups and all(g > 1 for g in groups), "own launch groups only")
    for sig in (signal.SIGTERM, signal.SIGKILL):
        for group in groups:
            try:
                os.killpg(group, sig)
            except ProcessLookupError:
                pass
    states = []
    for group in sorted(groups):
        try:
            os.killpg(group, 0)
            gone = False
        except ProcessLookupError:
            gone = True
        states.append({"pgid": group, "group_gone": gone})
    return {
        "registered_groups": states,
        "snapshot_helper": helper,
        "complete_exit": False,
        "status": "STOP_TIMEOUT_PENDING_REAP_OR_UNKNOWN",
    }


def supervise(plan, role, plan_sha):
    """Finite observer: actual outer timer wait4 plus final own RSS sample.

    Caller observes this supervisor's actual exit and full wall after return.
    This receipt deliberately never certifies its own future exit.
    """
    started = time.monotonic()
    failure_recording = plan.get("execution_identity") in (F_IDENTITY, STABLE_IDENTITY)
    public_fixture = plan.get("execution_identity") == F_IDENTITY
    base = ROOT / "receipts"
    base.mkdir(parents=True, exist_ok=True)
    pending = {
        "execution_identity": plan.get("execution_identity", IDENTITY),
        "role": role,
        "plan_sha256": plan_sha,
        "frozen_FULL_seconds": CAPS[role],
        "clock_domain": CLOCK,
        "clock_resolution_seconds": 0.001,
        **{key: plan[key] for key in (
            "actor_activation_UTC_seconds", "actor_window_seconds", "actor_deadlines_UTC")},
        "external_argv": [resolved(argv, plan_sha) for argv in plan["external_argv"][role]],
        "status": "PENDING_BEFORE_DISPATCH",
    }
    write(base / (role + "-pending.json"), pending)
    if not public_fixture:
        ingest_external(plan, plan_sha, closing=role == "shared-closeout")
        if plan.get("execution_identity") == STABLE_IDENTITY:
            source_gate(plan, role, plan_sha)
    profile = base / (role + "-controller.time")
    log = base / (role + "-controller.log")
    write(
        base / (role + "-supervisor-pending.json"),
        {"role": role, "plan_sha256": plan_sha, "status": "PENDING_BEFORE_CONTROLLER"},
    )
    argv = [
        sys.executable,
        "-I",
        str(Path(__file__).resolve()),
        "run",
        "--plan",
        str(ROOT / "launch_plan.json"),
        "--plan-sha",
        plan_sha,
        "--role",
        role,
    ]
    if plan.get("execution_identity") == STABLE_IDENTITY:
        argv.append("--r-stable")
    if public_fixture:
        argv = [sys.executable, "-I", str(Path(__file__).resolve()), "public-payload",
                "--public-root", str(ROOT), "--fixture-exit", str(plan["fixture_exit"])]
    with log.open("xb") as stream:
        child = subprocess.Popen(
            ["/usr/bin/time", "-l", "-o", str(profile), *argv],
            cwd=REPO,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        rusage = None
        while True:
            pid, status, ru = os.wait4(child.pid, os.WNOHANG)
            if pid:
                child.returncode = os.waitstatus_to_exitcode(status)
                rusage = ru
                break
            if time.monotonic() - started > CAPS[role] - 10:
                cleanup = stop_registered(role, child.pid)
                write(base / (role + "-timeout-cleanup.json"), cleanup)
                _, status, ru = os.wait4(child.pid, 0)
                child.returncode = os.waitstatus_to_exitcode(status)
                rusage = ru
                break
            time.sleep(0.01)
    timer_peak = int(rusage.ru_maxrss) * (1 if sys.platform == "darwin" else 1024)
    wait4 = {
        "statistics_source": "os.wait4",
        "wall_source": "controller_monotonic_observed",
        "pid": child.pid,
        "exit_code": child.returncode,
        "rss_unit": "bytes" if sys.platform == "darwin" else "KiB*1024",
        "native": {
            "wall_seconds": time.monotonic() - started,
            "user_seconds": rusage.ru_utime,
            "system_seconds": rusage.ru_stime,
            "rss_bytes": timer_peak,
        },
    }
    write(
        base / (role + "-outer-timer-exit.json"),
        {
            "exit_code": child.returncode,
            "native_rss_bytes": timer_peak,
            "unit": "bytes",
            "wall_seconds": time.monotonic() - started,
            "role": role,
            "plan_sha256": plan_sha,
            "wait4": wait4,
        },
    )
    try:
        require(timer_peak > 0 and (child.returncode == 0 or failure_recording),
                "outer timer/controller exit")
        result = bind(plan, role, child.returncode, plan_sha)
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as error:
        # A failed controller still has an actual exit, native timer and supervisor.
        # Persist these before the caller observes STOP; do not demand success first.
        result = {"status": "STOP_NO_RETRY", "controller_exit": child.returncode,
                  "conservative_RSS_bytes": None, "domain_status": "STOP",
                  "secondary_failures": [
                      {"stage": "binding", "type": type(error).__name__, "reason": str(error)}
                  ], "missing": "UNKNOWN_NOT_ZERO"}
    if child.returncode != 0:
        result.setdefault("primary_failure", {"stage": "payload/controller", "type": "ExitCode",
                                               "reason": str(child.returncode)})
        result["domain_status"] = "STOP"
    self_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform != "darwin":
        self_peak *= 1024
    result.update(
        execution_identity=plan.get("execution_identity", IDENTITY),
        schema="topolab.v2.m2-input-failure-supervisor.v1" if failure_recording
               else "topolab.v2.m2-input-export-supervisor.v2",
        outer_timer_exit=child.returncode,
        outer_timer_native_rss_bytes=timer_peak,
        supervisor_rss_after_verification_bytes=self_peak,
        supervisor_observed_wall_seconds=time.monotonic() - started,
        supervisor_complete_exit="PENDING_EXTERNAL_CALLER_OBSERVATION",
        full_role_charge="EXTERNAL_FULL_WALL_PLUS10_REQUIRED",
        supervisor_pid=os.getpid(),
    )
    if result["conservative_RSS_bytes"] is not None:
        result["conservative_RSS_bytes"] += timer_peak + self_peak
    if (result["conservative_RSS_bytes"] is not None
            and result["conservative_RSS_bytes"] > 4294967296
            or result["supervisor_observed_wall_seconds"] + 10 > CAPS[role]):
        result.setdefault("secondary_failures", []).append("whole RSS/time cap exceeded")
        result["status"] = "STOP_NO_RETRY"
    write(base / (role + "-supervisor.json"), result)
    # Retain final sample after actual serialization/flush; caller still observes exit.
    write(
        base / (role + "-last-rss.json"),
        {
            "rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            * (1 if sys.platform == "darwin" else 1024),
            "unit": "bytes",
            "status": "PENDING_EXTERNAL_EXIT",
            "role": role,
            "pid": os.getpid(),
            "plan_sha256": plan_sha,
        },
    )
    return result



def resource_inputs(plan, role, plan_sha, *, available=None):
    """Read only this NEW role's literal recording outputs, never old payloads."""
    folder = ROOT / "receipts" / role / role
    failures = []

    def collect(path, cap=1048576, *, allow_empty=False):
        try:
            raw = read(path, cap, allow_empty=allow_empty)
            if available is not None:
                available[str(path.relative_to(ROOT))] = {
                    "byte_size": len(raw), "sha256": digest(raw)}
            return raw
        except (ValueError, OSError) as error:
            failures.append(f"{path.name}: {type(error).__name__}: {error}")
            return None

    # Keep the independent outer profile even if an inner/helper record is absent.
    outer = collect(ROOT / "receipts" / (role + "-controller.time"))
    command = collect(folder / "command.json", 4 * 1024 * 1024)
    profile = collect(folder / "command.time")
    log = collect(folder / "command.log", 16 * 1024 * 1024, allow_empty=True)
    require(command is not None, "UNKNOWN_MISSING_INNER_RECORD " + "; ".join(failures))
    record = json.loads(command)
    helpers = {}
    require(len(record["helpers"]) <= 4096, "bounded helper inventory")
    for index, item in enumerate(record["helpers"]):
        name = f"sampler-{index}.time"
        require(item["profile"] == name, "literal registered helper")
        helpers[name] = collect(folder / name)
    require(not failures, "UNKNOWN_MISSING_NATIVE_COMPONENT " + "; ".join(failures))
    return {
        "inner_evidence": {
            "record": record,
            "profile": profile,
            "log": log,
            "helper_profiles": helpers,
            "expected_role": role,
            "expected_argv": resolved(plan["roles"][role]["argv"], plan_sha),
            "platform": sys.platform,
        },
        "native_profiles": {
            "outer-controller": outer,
        },
    }


def ingest_external(plan, plan_sha, *, closing=False):
    """Copy actual trusted-tool events at the next role's measured prelude."""
    raw = os.environ.get("TOPOLAB_RSTABLE_PREVIOUS_TOOL_RECORDS" if IDENTITY == STABLE_IDENTITY
                         else "TOPOLAB_R3_PREVIOUS_TOOL_RECORDS", "[]")
    require(len(raw.encode()) <= 4 * 1024 * 1024, "bounded external telemetry")
    records = json.loads(raw)
    require(isinstance(records, list) and len(records) <= 1, "one actual prior tool packet")
    (ROOT / "tool-events").mkdir(exist_ok=True)
    for packet in records:
        role = packet["pending"]["role"]
        require(role in CAPS, "registered previous role")
        if IDENTITY == STABLE_IDENTITY and "full_collector_record" in packet:
            pointer = packet["full_collector_record"]
            literal = "receipts/" + role + "-final-wire-source.json"
            require(pointer["path"] == literal, "literal NEW collector record")
            collector_raw = read(ROOT / literal)
            require(len(collector_raw) == pointer["byte_size"]
                    and digest(collector_raw) == pointer["sha256"], "collector bytes/hash differ")
        write(ROOT / "tool-events" / (role + ".json"), packet)
        try:
            pending_raw = read(ROOT / "receipts" / (role + "-pending.json"))
            pending = json.loads(pending_raw)
            require(pending == packet["pending"], "literal pending identity")
            try:
                evidence = resource_inputs(plan, role, plan_sha)
            except (OSError, KeyError, ValueError):
                evidence = {}
            verified = independent.audit_full_role_v2(
                pending, packet["completion"], raw_tool_events=packet["events"],
                expected_role=role, expected_plan_sha256=plan_sha, **evidence,
                **(dict(recording_options(plan), expected_pending_sha256=digest(pending_raw))
                   if IDENTITY == STABLE_IDENTITY else {}),
            )
            for key in ("status", "whole_wall_seconds", "RSS_envelope_bytes",
                        "execution_identity", "role", "plan_sha256", "pending_sha256",
                        "frozen_FULL_seconds", "actual_exit_codes", "full_role_evidence_accepted"):
                require(verified[key] == packet["terminal"][key],
                        "independent actual external-event replay differs: " + key)
        except (OSError, KeyError, TypeError, ValueError) as error:
            if not closing:
                raise
            verified = {"status": "STOP_NO_RETRY", "role": role,
                        "reason": str(error), "missing_evidence": "UNKNOWN_NOT_ZERO"}
        write(ROOT / "receipts" / (role + "-observed.json"), verified)
        accepted = ("PASS_R_STABLE_FULL_ROLE" if IDENTITY == STABLE_IDENTITY
                    else "PASS_R_V3_FULL_ROLE")
        if verified["status"] != accepted and not os.path.lexists(ROOT / "STOP.json"):
            write(ROOT / "STOP.json", {"role": role, "outcome": verified, "retry": False})


def archive_new():
    """One NEW-prefix backup; never follows original input or backup pointers."""
    backup = ROOT.with_name(ROOT.name + "-independent-backup")
    backup.mkdir(exist_ok=False)
    return backup_late(backup, exclude_active=True)


def backup_late(backup, *, exclude_active=False):
    rows = []
    total = 0
    for path in sorted(ROOT.rglob("*")):
        relative = path.relative_to(ROOT)
        if exclude_active and str(relative).startswith("receipts/shared-closeout"):
            continue
        require(not path.is_symlink(), "NEW backup symlink")
        if path.is_dir():
            continue
        require(path.is_file(), "NEW backup regular file")
        data = read(path, 64 * 1024 * 1024, allow_empty=True)
        total += len(data)
        require(total <= 512 * 1024 * 1024 and len(rows) < 20000, "NEW backup finite cap")
        target = backup / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            require(read(target, 64 * 1024 * 1024, allow_empty=True) == data,
                    "immutable NEW snapshot changed")
        else:
            with target.open("xb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        require(read(target, 64 * 1024 * 1024, allow_empty=True) == data,
                "NEW backup actual byte comparison")
        rows.append({"path": str(relative), "bytes": len(data), "sha256": digest(data)})
    actual = {str(p.relative_to(backup)) for p in backup.rglob("*") if p.is_file()}
    require(actual == {row["path"] for row in rows}, "NEW backup exact member inventory")
    return {"status": "PASS_NEW_PREFIX_BACKUP_ONLY", "members": rows,
            "total_bytes": total, "old_input_reads": 0}


def backup_evidence(*, public_fixture=False):
    backup = ROOT.with_name(ROOT.name + "-independent-backup")
    options = {"execution_identity": STABLE_IDENTITY} if IDENTITY == STABLE_IDENTITY else {}
    first = independent.audit_new_backup(ROOT, backup, public_fixture=public_fixture, **options)
    require(first["status"] == "PASS_INDEPENDENT_NEW_BACKUP", "independent NEW backup")
    # The inventory excludes its own not-yet-created manifest. Both manifest
    # copies are then included in the final independent byte comparison.
    write(ROOT / "backup_manifest.json", first)
    write(backup / "backup_manifest.json", first)
    checked = independent.audit_new_backup(ROOT, backup, public_fixture=public_fixture, **options)
    require(checked["status"] == "PASS_INDEPENDENT_NEW_BACKUP", "NEW manifest copies")
    return {"status": checked["status"], "member_count": checked["member_count"],
            "total_bytes": checked["total_bytes"], "manifest": "backup_manifest.json",
            "manifest_sha256": digest(canonical(first))}


def stable_wire_packet(packet, role):
    """Keep full collectors on NEW disk; bounded wire preserves acceptance facts."""
    full = canonical(packet)
    path = ROOT / "receipts" / (role + "-final-wire-source.json")
    write(path, packet)
    return bounded_stable_wire(packet, {"path": str(path.relative_to(ROOT)),
                                       "byte_size": len(full), "sha256": digest(full)})


def bounded_stable_wire(packet, collector):
    completion = {key: value for key, value in packet["completion"].items()
                  if key not in ("available_outer_records", "available_native_evidence")}
    wire = dict(packet, completion=completion)
    wire["full_collector_record"] = collector
    if len(canonical(wire)) > 32768:
        # Never trim required observations to manufacture a passing receipt.
        completion = {key: completion[key] for key in (
            "execution_identity", "role", "plan_sha256", "frozen_FULL_seconds",
            "clock_domain", "clock_resolution_seconds", "actor_activation_UTC_seconds",
            "actor_window_seconds", "actor_deadlines_UTC", "pending_sha256")}
        completion.update(status="FAILED_INTERNAL_COMPLETION", domain_status="STOP",
                          cleanup={"group_gone": None},
                          resource_components=[packet["completion"]["resource_components"][-1]],
                          final_serializer_pid=packet["completion"]["final_serializer_pid"],
                          primary_failure=packet["completion"].get("primary_failure"),
                          secondary_failures=[{"stage": "wire", "reason": "finite32768 byte cap"}])
        wire = {"pending": packet["pending"], "completion": completion,
                "full_collector_record": wire["full_collector_record"],
                "resourceEvidence": {"status": "STOP_NO_RETRY", "reason": "WIRE_SIZE_STOP"}}
    require(len(canonical(wire)) <= 32768, "finite stable actual stdout")
    return wire


def finish_record(plan, role, plan_sha):
    """Retain available serializer RSS BEFORE acceptance; actual exit is external."""
    base = ROOT / "receipts"
    failure_recording = plan.get("execution_identity") in (F_IDENTITY, STABLE_IDENTITY)
    own = {
        "pid": os.getpid(), "kind": "self_high_water",
        "statistics_source": "resource.getrusage", "rss_unit": "bytes",
        "phases": ["preflush", "postflush"],
        "samples_bytes": [native_recording._rss_self(), native_recording._rss_self()],
    }
    completion = {
        "schema": "topolab.v2.m2-input-failure-completion.v1" if failure_recording
                  else "topolab.v2.m2-input-export-exit.v2",
        "execution_identity": plan.get("execution_identity", IDENTITY),
        "role": role, "plan_sha256": plan_sha,
        "frozen_FULL_seconds": CAPS[role], "clock_domain": CLOCK,
        "clock_resolution_seconds": 0.001, "status": "PENDING_EXTERNAL_EXIT",
        **{key: plan[key] for key in (
            "actor_activation_UTC_seconds", "actor_window_seconds", "actor_deadlines_UTC")},
        "pending_sha256": None, "resource_components": [own],
        "final_serializer_pid": os.getpid(), "cleanup": {"group_gone": None},
    }
    packet = {"pending": {}, "completion": completion, "resourceEvidence": {
        "status": "STOP_NO_RETRY", "reason": "UNKNOWN_INCOMPLETE_ROLE_EVIDENCE"}}
    success = False
    secondary = []
    available = {}
    # Collect independent components even if the successful supervisor receipt
    # or another component is absent. No reread, retry or old source access.
    for name in ("pending", "supervisor", "last-rss", "outer-timer-exit"):
        try:
            raw = read(base / (role + "-" + name + ".json"))
            value = json.loads(raw)
            require(isinstance(value, dict), "outer record must be an object")
            if name == "outer-timer-exit":
                require(isinstance(value.get("wait4"), dict), "wait4 record must be an object")
            if name == "supervisor":
                require(isinstance(value.get("secondary_failures", []), list),
                        "secondary failures must be a list")
            available[name] = value
            if name == "pending":
                packet["pending"] = available[name]
                completion["pending_sha256"] = digest(raw)
        except (ValueError, KeyError, TypeError, OSError, OverflowError) as error:
            secondary.append({"stage": name, "type": type(error).__name__, "reason": str(error)})
    sup = available.get("supervisor", {})
    completion["primary_failure"] = sup.get("primary_failure")
    completion["domain_status"] = sup.get("domain_status", "UNKNOWN")
    completion["available_outer_records"] = available
    completion["available_native_evidence"] = {}
    evidence = None
    try:
        evidence = resource_inputs(plan, role, plan_sha,
                                   available=completion["available_native_evidence"])
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as error:
        secondary.append({"stage": "inner/native", "type": type(error).__name__,
                          "reason": str(error)})
    # Preserve wait4 and supervisor peaks independently of the inner receipt.
    if "outer-timer-exit" in available and "wait4" in available["outer-timer-exit"]:
        timer = available["outer-timer-exit"]["wait4"]
        completion["resource_components"].append(
            {"pid": timer.get("pid"), "kind": "wait4", "platform": sys.platform,
             "record": timer})
    if "supervisor_pid" in sup and "last-rss" in available:
        completion["resource_components"].append(
            {"pid": sup["supervisor_pid"], "kind": "self_high_water",
             "statistics_source": "resource.getrusage", "rss_unit": "bytes",
             "phases": ["preflush", "postflush"],
             "samples_bytes": [sup.get("supervisor_rss_after_verification_bytes"),
                               available["last-rss"].get("rss_bytes")]})
    try:
        require(not secondary and evidence is not None, "UNKNOWN_INCOMPLETE_ROLE_EVIDENCE")
        timer = available["outer-timer-exit"]["wait4"]
        last = available["last-rss"]
        controller_pid = evidence["inner_evidence"]["record"]["controller_pid"]
        outer_raw = evidence["native_profiles"]["outer-controller"]
        completion["resource_components"] = [
            {"pid": controller_pid, "kind": "native_profile", "profile": "outer-controller",
             "profile_sha256": digest(outer_raw), "platform": sys.platform,
             "actual_exit_code": sup["controller_exit"]},
            {"pid": timer["pid"], "kind": "wait4", "platform": sys.platform, "record": timer},
            {"pid": sup["supervisor_pid"], "kind": "self_high_water",
             "statistics_source": "resource.getrusage", "rss_unit": "bytes",
             "phases": ["preflush", "postflush"],
             "samples_bytes": [sup["supervisor_rss_after_verification_bytes"], last["rss_bytes"]]},
            own,
        ]
        completion["cleanup"] = evidence["inner_evidence"]["record"]["cleanup"]
        write(base / (role + "-finalizer-preflush.json"), completion)
        own["samples_bytes"][1] = native_recording._rss_self()
        packet["resourceEvidence"] = independent.audit_v2_resource_components(
            completion, **evidence, **recording_options(plan),
        )
        write(base / (role + "-completion.json"), packet)
        if role == "shared-closeout":
            # Include all late native/serializer disk records in the one backup.
            backup_late(ROOT.with_name(ROOT.name + "-independent-backup"))
            packet["independent_backup"] = backup_evidence()
        # Exercise bounded stdout serialization before retaining this process's
        # last high-water sample. Actual exit is still the external tool event.
        canonical(packet)
        own["samples_bytes"][1] = native_recording._rss_self()
        packet["resourceEvidence"] = independent.audit_v2_resource_components(
            completion, **evidence, **recording_options(plan),
        )
        success = packet["resourceEvidence"]["status"] == "PENDING_EXTERNAL_EXIT"
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as error:
        own["samples_bytes"][1] = native_recording._rss_self()
        completion["status"] = "FAILED_INTERNAL_COMPLETION"
        packet["failure"] = {"type": type(error).__name__, "reason": str(error),
                             "status": "STOP_NO_RETRY", "missing": "UNKNOWN_NOT_ZERO"}
        secondary.append({"stage": "completion", "type": type(error).__name__,
                          "reason": str(error)})
        packet["resourceEvidence"] = independent.audit_v2_resource_components(
            completion, **(evidence or {}), **recording_options(plan),
        )
        # Preserve the independent resource result verbatim. The failed terminal
        # binding closes role acceptance without inventing missing RSS facts.
    packet["primary_failure"] = completion["primary_failure"]
    completion["secondary_failures"] = [*sup.get("secondary_failures", []), *secondary]
    packet["secondary_failures"] = completion["secondary_failures"]
    # Serialization and stdout occur inside the measured final external call.
    if plan.get("execution_identity") == STABLE_IDENTITY:
        packet = stable_wire_packet(packet, role)
        own["samples_bytes"][1] = native_recording._rss_self()
        packet["resourceEvidence"] = independent.audit_v2_resource_components(
            packet["completion"], **(evidence or {}), **recording_options(plan))
        packet = bounded_stable_wire(packet, packet["full_collector_record"])
        success = success and packet["completion"]["status"] == "PENDING_EXTERNAL_EXIT"
    raw = canonical(packet)
    require(plan.get("execution_identity") != STABLE_IDENTITY or len(raw) <= 32768,
            "final actual stable stdout cap")
    print(raw.decode(), end="", flush=True)
    return 0 if success else 1


def source_gate(plan, role, plan_sha):
    require(role == "shared-closeout" or not (ROOT / "STOP.json").exists(),
            "STOP closes all source suffix roles")
    if role == "shared-closeout":
        if plan.get("execution_identity") == STABLE_IDENTITY:
            observed = [json.loads(read(p))
                        for p in sorted((ROOT / "receipts").glob("*-observed.json"))]
            require(observed and all(p.get("cleanup", {}).get("group_gone") is True
                                     for p in observed),
                    "uncertain cleanup refuses closeout process")
        return
    if plan.get("execution_identity") == STABLE_IDENTITY:
        stable_lease_checked(plan, plan_sha)
    order = list(CAPS)
    for previous in order[:order.index(role)]:
        observed = json.loads(read(ROOT / "receipts" / (previous + "-observed.json")))
        require(observed["status"] == ("PASS_R_STABLE_FULL_ROLE" if IDENTITY == STABLE_IDENTITY
                                       else "PASS_R_V3_FULL_ROLE")
                and observed["execution_identity"] == IDENTITY
                and observed["plan_sha256"] == plan_sha
                and observed["frozen_FULL_seconds"] == CAPS[previous]
                and observed["full_role_evidence_accepted"] is True,
                "complete new predecessor exit/FULL/plan binding")
    if role != "independent-public-check":
        public = json.loads(read(ROOT / "independent-public-check.json"))
        require(public["status"] == "PASS_PUBLIC_IO_ONLY" and public["old_source_read_set"] == [],
                "independent NEW public IO prerequisite")


def public_entry(mode, root, code):
    """Only fixed new public exit fixtures; no R plan/role/input can be supplied."""
    global ROOT, CAPS
    require(root is not None and root.is_absolute()
            and root.parts[:3] == ("/", "private", "tmp") and len(root.parts) > 3
            and all(part not in (".", "..") for part in root.parts),
            "F output must be a literal NEW /private/tmp directory")
    # Reject symlink ancestors before accessing even a plan. Historical DATA
    # roots are rejected lexically above, without stat, resolve or read.
    parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in root.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
            os.close(parent)
            parent = child
    finally:
        os.close(parent)
    ROOT, CAPS = root, {"public-fixture": 120}
    role = "public-fixture"
    argv = [sys.executable, "-I", "-c", f"raise SystemExit({code})"]
    entry = [sys.executable, "-I", str(Path(__file__).resolve())]
    if mode == "public-plan":
        ROOT.mkdir(exist_ok=False)
        activation = round(time.time() * 1000) / 1000
        deadline = datetime.fromtimestamp(activation + 2700, UTC).isoformat(
            timespec="milliseconds").replace("+00:00", "Z")
        plan = {"execution_identity": F_IDENTITY, "fixture_exit": code,
                "roles": {role: {"argv": argv}},
                "actor_activation_UTC_seconds": activation, "actor_window_seconds": 2700,
                "actor_deadlines_UTC": {"exporter": deadline, "independent": deadline},
                "external_argv": {role: [
                    [*entry, command, "--public-root", str(ROOT), "--fixture-exit", str(code)]
                    for command in ("public-supervise", "public-finalize")]}}
        write(ROOT / "public-plan.json", plan)
        print(canonical({"execution_identity": F_IDENTITY, "status": "PUBLIC_FIXTURE_PLAN_ONLY",
                         "plan_sha256": digest(canonical(plan))}).decode(), end="", flush=True)
        return 0
    else:
        fd = os.open(ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        os.close(fd)
        plan = json.loads(read(ROOT / "public-plan.json"))
    require(plan["execution_identity"] == F_IDENTITY and plan["fixture_exit"] == code
            and plan["roles"] == {role: {"argv": argv}}, "F fixed public plan differs")
    plan_sha = digest(canonical(plan))
    if mode == "public-payload":
        record = native_recording.invoke(ROOT / "receipts" / role, role, argv,
                                         timeout=100, limit_bytes=4294967296)
        return 0 if record["software_result"] == "PUBLIC_COMMAND_EXIT_OBSERVED" else 1
    if mode == "public-finalize":
        return finish_record(plan, role, plan_sha)
    result = supervise(plan, role, plan_sha)
    pending = json.loads(read(ROOT / "receipts" / (role + "-pending.json")))
    print(canonical({"pending": pending, "diagnostic": result}).decode(), end="", flush=True)
    return 1 if result.get("primary_failure") or result["status"] == "STOP_NO_RETRY" else 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run", "bind", "supervise", "finalize", "archive",
                                    "final-helper", "final-file",
                                    "public-plan", "public-supervise", "public-finalize",
                                    "public-payload"))
    p.add_argument("--plan", type=Path)
    p.add_argument("--plan-sha")
    p.add_argument("--role", choices=tuple(CAPS))
    p.add_argument("--activation-utc-seconds", type=float)
    p.add_argument("--ci-evidence", type=Path)
    p.add_argument("--writer-control", type=Path)
    p.add_argument("--r-stable", action="store_true")
    p.add_argument("--controller-exit", type=int)
    p.add_argument("--public-root", type=Path)
    p.add_argument("--fixture-exit", type=int, choices=(0, 1), default=1)
    args = p.parse_args()
    if args.mode.startswith("public-"):
        require(args.plan is None and args.plan_sha is None and args.role is None
                and not args.r_stable and args.writer_control is None,
                "F public entry cannot accept an R plan or role")
        return public_entry(args.mode, args.public_root, args.fixture_exit)
    require(args.r_stable, "historical R execution is closed; explicit NEW R-STABLE required")
    configure_stable()
    if args.mode == "plan":
        require(args.activation_utc_seconds is not None and args.ci_evidence is not None,
                "readiness activation and actual CI evidence required")
        print(canonical(create_plan(args.activation_utc_seconds, args.ci_evidence,
                                    args.writer_control)).decode(),
              end="", flush=True)
        return 0
    filing = args.mode in ("final-helper", "final-file")
    require(args.plan is not None and args.plan_sha is not None
            and (filing or args.role is not None),
            "frozen plan/hash/role required")
    plan = plan_checked(args.plan, args.plan_sha, result_filing=filing)
    if filing:
        if args.mode == "final-helper":
            return final_helper(plan, args.plan_sha)
        print(canonical(final_file(plan, args.plan_sha)).decode(), end="", flush=True)
        return 0
    if args.mode == "supervise":
        result = supervise(plan, args.role, args.plan_sha)
        pending_raw = read(ROOT / "receipts" / (args.role + "-pending.json"))
        print(canonical({"pending": json.loads(pending_raw),
                         "pending_sha256": digest(pending_raw), "diagnostic": result}).decode(),
              end="", flush=True)
        return int(result.get("domain_status") == "STOP" or result["status"] == "STOP_NO_RETRY")
    if args.mode == "finalize":
        return finish_record(plan, args.role, args.plan_sha)
    if args.mode == "archive":
        require(args.role == "shared-closeout", "one NEW-only closeout")
        print(canonical(archive_new()).decode(), end="", flush=True)
        return 0
    if args.mode == "bind":
        bind(plan, args.role, args.controller_exit, args.plan_sha)
        return 0
    source_gate(plan, args.role, args.plan_sha)
    value = plan["roles"][args.role]
    require(value["cap_seconds"] == CAPS[args.role], "unchanged cap")
    result = native_recording.invoke(
        ROOT / "receipts" / args.role, args.role, resolved(value["argv"], args.plan_sha),
        timeout=CAPS[args.role] - 20, limit_bytes=4294967296,
    )
    return 0 if result["software_result"] == "PUBLIC_COMMAND_EXIT_OBSERVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
