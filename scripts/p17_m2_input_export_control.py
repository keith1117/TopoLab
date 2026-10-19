"""Frozen R launch plan and post-exit binding; no historical payload reads."""

import argparse
import hashlib
import importlib.util
import json
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = Path("/Users/keith1117/Documents/TopoLab-data/p17-m2-input-export-preparation-v1")
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
    expected_files = {
        "scripts/p17_m2_input_export.py",
        "scripts/p17_m2_input_export_independent.py",
        "scripts/p17_m2_input_export_control.py",
        "scripts/p17_m2_resource_control.py",
        "scripts/p17_m2_homotopy.py",
        "uv.lock",
        "docs/planning/p17_m2_input_export_preparation_proposal.json",
    }
    require(set(plan["source_files"]) == expected_files, "complete source freeze")
    for name, h in plan["source_files"].items():
        require(digest((REPO / name).read_bytes()) == h, "frozen source bytes changed")
    require(
        plan["all_four_main_CI_success"] is True
        and plan["owner_R_authorized"] is True
        and plan["B_C_authorized"] is False,
        "admission record",
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
    require(record["argv"] == plan["roles"][role]["argv"], "actual argv")
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
        expected_argv=plan["roles"][role]["argv"],
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
        "schema": "topolab.v2.m2-input-export-exit.v1",
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
    write(
        base / (role + "-outer-timer-exit.json"),
        {
            "exit_code": child.returncode,
            "native_rss_bytes": timer_peak,
            "unit": "bytes",
            "wall_seconds": time.monotonic() - started,
            "role": role,
            "plan_sha256": plan_sha,
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
            "plan_sha256": plan_sha,
        },
    )
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("run", "bind", "supervise"))
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--plan-sha", required=True)
    p.add_argument("--role", choices=tuple(CAPS), required=True)
    p.add_argument("--controller-exit", type=int)
    args = p.parse_args()
    plan = plan_checked(args.plan, args.plan_sha)
    if args.mode == "supervise":
        supervise(plan, args.role, args.plan_sha)
        return 0
    if args.mode == "bind":
        bind(plan, args.role, args.controller_exit, args.plan_sha)
        return 0
    require(not (ROOT / "STOP.json").exists(), "prior R STOP closes remaining roles")
    order = list(CAPS)
    for previous in order[: order.index(args.role)]:
        observed = json.loads(read(ROOT / "receipts" / (previous + "-observed.json")))
        require(
            observed["status"] == "PASS_R_NATIVE_EXIT" and observed["plan_sha256"] == args.plan_sha,
            "complete predecessor exit/plan binding",
        )
    if args.role != "independent-public-check":
        public = json.loads(read(ROOT / "independent-public-check.json"))
        require(public["status"] == "PASS_PUBLIC_IO_ONLY", "independent public IO prerequisite")
    value = plan["roles"][args.role]
    require(value["cap_seconds"] == CAPS[args.role], "unchanged cap")
    result = native_recording.invoke(
        ROOT / "receipts" / args.role,
        args.role,
        value["argv"],
        timeout=CAPS[args.role] - 20,
        limit_bytes=4294967296,
    )
    return 0 if result["software_result"] == "PUBLIC_COMMAND_EXIT_OBSERVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
