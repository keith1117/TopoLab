"""NEW R/v3 readiness-bound FULL billing; no old payload reads during planning."""

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
            [python, "-I", str(Path(__file__).resolve()), mode, "--plan",
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


def create_plan(activation, ci_path):
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
    deadline = datetime.fromtimestamp(activation + ACTOR_WINDOW, UTC).isoformat(
        timespec="milliseconds").replace("+00:00", "Z")
    plan = {
        "execution_identity": IDENTITY, "owner_R_v3_authorized": True,
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
        "authors": {"exporter": "/root", "independent": "/root/review_r_v3"},
        "actor_activation_UTC_seconds": activation, "actor_window_seconds": ACTOR_WINDOW,
        "actor_deadlines_UTC": {"exporter": deadline, "independent": deadline},
        "FULL_caps_seconds": CAPS, "clock_domain": CLOCK, "clock_resolution_seconds": 0.001,
        "external_argv": external_templates(python),
        "roles": {role: {"cap_seconds": CAPS[role], "argv": argv}
                  for role, argv in payloads.items()},
    }
    actor_window_checked(plan, time.time())
    require(time.time() + sum(CAPS.values()) <= activation + ACTOR_WINDOW,
            "complete six-role reserve before plan creation")
    require(not os.path.lexists(ROOT)
            and not os.path.lexists(ROOT.with_name(ROOT.name + "-independent-backup")),
            "exclusive NEW roots; no overwrite or retry")
    ROOT.mkdir(exist_ok=False)
    raw = canonical(plan)
    write(ROOT / "launch_plan.json", plan)
    plan_sha = digest(raw)
    context = dict(plan, plan_sha256=plan_sha)
    context["external_argv"] = {role: [resolved(argv, plan_sha) for argv in calls]
                                for role, calls in plan["external_argv"].items()}
    return context


def plan_checked(path, expected):
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
        and plan["owner_R_v3_authorized"] is True
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
    actor_window_checked(plan, time.time())
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


def bind(plan, role, controller_exit, plan_sha):
    base = ROOT / "receipts"
    record_path = base / role / role / "command.json"
    record = json.loads(read(record_path, 4 * 1024 * 1024))
    profile = base / (role + "-controller.time")
    measured = native_recording.native(read(profile, 1024 * 1024).decode(), sys.platform)
    require(
        controller_exit == 0
        and record["exit_code"] == 0
        and record["software_result"] == "PUBLIC_COMMAND_EXIT_OBSERVED"
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
    base = ROOT / "receipts"
    base.mkdir(parents=True, exist_ok=True)
    pending = {
        "execution_identity": IDENTITY,
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
    ingest_external(plan, plan_sha, closing=role == "shared-closeout")
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
    require(child.returncode == 0 and timer_peak > 0, "outer timer/controller exit")
    result = bind(plan, role, child.returncode, plan_sha)
    self_peak = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform != "darwin":
        self_peak *= 1024
    result.update(
        outer_timer_exit=child.returncode,
        outer_timer_native_rss_bytes=timer_peak,
        supervisor_rss_after_verification_bytes=self_peak,
        supervisor_observed_wall_seconds=time.monotonic() - started,
        supervisor_complete_exit="PENDING_EXTERNAL_CALLER_OBSERVATION",
        full_role_charge="EXTERNAL_FULL_WALL_PLUS10_REQUIRED",
        supervisor_pid=os.getpid(),
    )
    result["conservative_RSS_bytes"] += timer_peak + self_peak
    require(result["conservative_RSS_bytes"] <= 4294967296, "whole registered RSS envelope")
    require(result["supervisor_observed_wall_seconds"] + 10 <= CAPS[role], "complete role time")
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



def resource_inputs(plan, role, plan_sha):
    """Read only this NEW role's literal recording outputs, never old payloads."""
    folder = ROOT / "receipts" / role / role
    record = json.loads(read(folder / "command.json", 4 * 1024 * 1024))
    helpers = {}
    require(len(record["helpers"]) <= 4096, "bounded helper inventory")
    for index, item in enumerate(record["helpers"]):
        name = f"sampler-{index}.time"
        require(item["profile"] == name, "literal registered helper")
        helpers[name] = read(folder / name, 1024 * 1024)
    return {
        "inner_evidence": {
            "record": record,
            "profile": read(folder / "command.time", 1024 * 1024),
            "log": read(folder / "command.log", allow_empty=True),
            "helper_profiles": helpers,
            "expected_role": role,
            "expected_argv": resolved(plan["roles"][role]["argv"], plan_sha),
            "platform": sys.platform,
        },
        "native_profiles": {
            "outer-controller": read(ROOT / "receipts" / (role + "-controller.time"), 1048576)
        },
    }


def ingest_external(plan, plan_sha, *, closing=False):
    """Copy actual trusted-tool events at the next role's measured prelude."""
    raw = os.environ.get("TOPOLAB_R3_PREVIOUS_TOOL_RECORDS", "[]")
    require(len(raw.encode()) <= 4 * 1024 * 1024, "bounded external telemetry")
    records = json.loads(raw)
    require(isinstance(records, list) and len(records) <= 1, "one actual prior tool packet")
    (ROOT / "tool-events").mkdir(exist_ok=True)
    for packet in records:
        role = packet["pending"]["role"]
        require(role in CAPS, "registered previous role")
        write(ROOT / "tool-events" / (role + ".json"), packet)
        try:
            pending = json.loads(read(ROOT / "receipts" / (role + "-pending.json")))
            require(pending == packet["pending"], "literal pending identity")
            try:
                evidence = resource_inputs(plan, role, plan_sha)
            except (OSError, KeyError, ValueError):
                evidence = {}
            verified = independent.audit_full_role_v2(
                pending, packet["completion"], raw_tool_events=packet["events"],
                expected_role=role, expected_plan_sha256=plan_sha, **evidence,
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
        if verified["status"] != "PASS_R_V3_FULL_ROLE":
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
    first = independent.audit_new_backup(ROOT, backup, public_fixture=public_fixture)
    require(first["status"] == "PASS_INDEPENDENT_NEW_BACKUP", "independent NEW backup")
    # The inventory excludes its own not-yet-created manifest. Both manifest
    # copies are then included in the final independent byte comparison.
    write(ROOT / "backup_manifest.json", first)
    write(backup / "backup_manifest.json", first)
    checked = independent.audit_new_backup(ROOT, backup, public_fixture=public_fixture)
    require(checked["status"] == "PASS_INDEPENDENT_NEW_BACKUP", "NEW manifest copies")
    return {"status": checked["status"], "member_count": checked["member_count"],
            "total_bytes": checked["total_bytes"], "manifest": "backup_manifest.json",
            "manifest_sha256": digest(canonical(first))}


def finish_record(plan, role, plan_sha):
    """Retain available serializer RSS BEFORE acceptance; actual exit is external."""
    base = ROOT / "receipts"
    own = {
        "pid": os.getpid(), "kind": "self_high_water",
        "statistics_source": "resource.getrusage", "rss_unit": "bytes",
        "phases": ["preflush", "postflush"],
        "samples_bytes": [native_recording._rss_self(), native_recording._rss_self()],
    }
    completion = {
        "schema": "topolab.v2.m2-input-export-exit.v2",
        "execution_identity": IDENTITY, "role": role, "plan_sha256": plan_sha,
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
    try:
        raw = read(base / (role + "-pending.json"))
        packet["pending"] = json.loads(raw)
        completion["pending_sha256"] = digest(raw)
        sup = json.loads(read(base / (role + "-supervisor.json")))
        last = json.loads(read(base / (role + "-last-rss.json")))
        timer = json.loads(read(base / (role + "-outer-timer-exit.json")))["wait4"]
        evidence = resource_inputs(plan, role, plan_sha)
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
            completion, **evidence
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
            completion, **evidence
        )
        success = packet["resourceEvidence"]["status"] == "PENDING_EXTERNAL_EXIT"
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as error:
        own["samples_bytes"][1] = native_recording._rss_self()
        packet["failure"] = {"type": type(error).__name__, "reason": str(error),
                             "status": "STOP_NO_RETRY", "missing": "UNKNOWN_NOT_ZERO"}
    # Serialization and stdout occur inside the measured final external call.
    print(canonical(packet).decode(), end="", flush=True)
    return 0 if success else 1


def source_gate(plan, role, plan_sha):
    require(role == "shared-closeout" or not (ROOT / "STOP.json").exists(),
            "STOP closes all source suffix roles")
    if role == "shared-closeout":
        return
    order = list(CAPS)
    for previous in order[:order.index(role)]:
        observed = json.loads(read(ROOT / "receipts" / (previous + "-observed.json")))
        require(observed["status"] == "PASS_R_V3_FULL_ROLE"
                and observed["execution_identity"] == IDENTITY
                and observed["plan_sha256"] == plan_sha
                and observed["frozen_FULL_seconds"] == CAPS[previous]
                and observed["full_role_evidence_accepted"] is True,
                "complete new predecessor exit/FULL/plan binding")
    if role != "independent-public-check":
        public = json.loads(read(ROOT / "independent-public-check.json"))
        require(public["status"] == "PASS_PUBLIC_IO_ONLY" and public["old_source_read_set"] == [],
                "independent NEW public IO prerequisite")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "run", "bind", "supervise", "finalize", "archive"))
    p.add_argument("--plan", type=Path)
    p.add_argument("--plan-sha")
    p.add_argument("--role", choices=tuple(CAPS))
    p.add_argument("--activation-utc-seconds", type=float)
    p.add_argument("--ci-evidence", type=Path)
    p.add_argument("--controller-exit", type=int)
    args = p.parse_args()
    if args.mode == "plan":
        require(args.activation_utc_seconds is not None and args.ci_evidence is not None,
                "readiness activation and actual CI evidence required")
        print(canonical(create_plan(args.activation_utc_seconds, args.ci_evidence)).decode(),
              end="", flush=True)
        return 0
    require(args.plan is not None and args.plan_sha is not None and args.role is not None,
            "frozen plan/hash/role required")
    plan = plan_checked(args.plan, args.plan_sha)
    if args.mode == "supervise":
        result = supervise(plan, args.role, args.plan_sha)
        pending_raw = read(ROOT / "receipts" / (args.role + "-pending.json"))
        print(canonical({"pending": json.loads(pending_raw),
                         "pending_sha256": digest(pending_raw), "diagnostic": result}).decode(),
              end="", flush=True)
        return 0
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
