"""Stage-A adaptation of B4.30 native RSS/complete-exit records (not B preflight).

Only public-run is exposed for execution. Post-exit binding preserves pending
records; the final observer must check the last verifier's own native exit/profile.
No resource PASS is emitted by this software-only entry.
"""

import argparse
import hashlib
import json
import math
import os
import re
import resource
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from time import monotonic, sleep

from p17_m2_homotopy import REPO, atomic_new

LIMIT = 4294967296
VERSION = "topolab.v2.m2-native-rss-exit-assurance.v1"
ENVIRONMENT = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def native(text, platform):
    """Explicit native units; unknown/missing fields never become zero."""
    if platform == "darwin":
        times = re.search(r"([\d.]+)\s+real\s+([\d.]+)\s+user\s+([\d.]+)\s+sys", text)
        peak = re.search(r"(\d+)\s+maximum resident set size", text)
        if times is None or peak is None:
            raise ValueError("RESOURCE_UNKNOWN_STOP: incomplete Darwin profile")
        wall, user, system = (float(times[i]) for i in (1, 2, 3))
        rss = int(peak[1])
    elif platform == "linux":
        fields = re.search(r"TOPOLAB_NATIVE ([\d.]+) ([\d.]+) ([\d.]+) (\d+)", text)
        if fields is None:
            raise ValueError("RESOURCE_UNKNOWN_STOP: incomplete GNU time profile")
        wall, user, system = (float(fields[i]) for i in (1, 2, 3))
        rss = int(fields[4]) * 1024
    else:
        raise ValueError("RESOURCE_UNKNOWN_STOP: unregistered native platform/units")
    if not all(math.isfinite(x) and x >= 0 for x in (wall, user, system)) or rss <= 0:
        raise ValueError("RESOURCE_UNKNOWN_STOP: invalid native statistics")
    return {"wall_seconds": wall, "user_seconds": user, "system_seconds": system, "rss_bytes": rss}


def _timed(argv, profile):
    if profile.exists():
        raise FileExistsError(profile)
    if sys.platform == "darwin":
        return ["/usr/bin/time", "-l", "-o", str(profile), *argv]
    if sys.platform == "linux":
        return ["/usr/bin/time", "-f", "TOPOLAB_NATIVE %e %U %S %M", "-o", str(profile), *argv]
    raise ValueError("unregistered software platform")


def _rss_self():
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value) * (1024 if sys.platform == "linux" else 1)


def _native_poll(child):
    """Observe this child's actual exit and keep wait4's native rusage.

    Unlike Popen.poll/wait, this does not discard the timing wrapper's own exit
    statistics. Some OS statistics include reaped descendants: adding this peak
    to the command's peak is deliberately conservative, never a subtraction.
    """
    if child.returncode is not None:
        return child.returncode
    pid, status, usage = os.wait4(child.pid, os.WNOHANG)
    if pid:
        child.returncode = os.waitstatus_to_exitcode(status)
        child.timer_native_exit = {
            "exit_code": child.returncode,
            "pid": child.pid,
            "native": {
                "wall_seconds": monotonic() - child.native_started,
                "user_seconds": usage.ru_utime,
                "system_seconds": usage.ru_stime,
                "rss_bytes": int(usage.ru_maxrss) * (1024 if sys.platform == "linux" else 1),
            },
            "source": "parent os.wait4 native exit rusage; possible descendant aggregation",
            "statistics_source": "os.wait4",
            "wall_source": "controller_monotonic_observed",
            "rss_unit": "bytes" if sys.platform == "darwin" else "KiB*1024",
        }
    return child.returncode


def _native_wait(child, timeout):
    deadline = monotonic() + timeout
    while _native_poll(child) is None:
        if monotonic() >= deadline:
            raise subprocess.TimeoutExpired(child.args, timeout)
        sleep(min(0.01, max(0.001, deadline - monotonic())))
    return child.returncode


def _snapshot(root, index, pgid, known_pids=()):
    """Retain only observed descendants/groups, with separately closed sampler.

    Sampling cannot rule out an unobserved short-lived escaped process. The A
    record states this limitation and never promotes observation to admission.
    """
    profile = root / f"sampler-{index}.time"
    command = _timed(["/bin/ps", "-axo", "pid=,ppid=,pgid=,rss="], profile)
    problem, stdout = None, ""
    # Anonymous output contains a transient process snapshot; persist only our
    # registered groups/descendants below, never unrelated process information.
    with tempfile.TemporaryFile(mode="w+t") as stream:
        native_started = monotonic()
        sample = subprocess.Popen(
            command, stdout=stream, stderr=subprocess.DEVNULL, start_new_session=True
        )
        sample.native_started = native_started
        try:
            _native_wait(sample, 5)
        except subprocess.TimeoutExpired:
            problem = "RESOURCE_UNKNOWN_STOP_SAMPLER_TIMEOUT"
        finally:
            cleanup = _terminate(sample.pid, sample)
        stream.seek(0)
        stdout = stream.read()
    if sample.returncode != 0 or not cleanup["group_gone"]:
        problem = problem or "RESOURCE_UNKNOWN_STOP_SAMPLER_EXIT"
    timer_exit = getattr(sample, "timer_native_exit", None)
    if timer_exit is None or timer_exit["native"]["rss_bytes"] <= 0:
        problem = problem or "RESOURCE_UNKNOWN_STOP_SAMPLER_TIMER_EXIT"
    all_rows = []
    for line in stdout.splitlines():
        fields = line.split()
        if len(fields) != 4 or not all(f.isdigit() for f in fields):
            problem = "RESOURCE_UNKNOWN_STOP_PS_UNITS"
            break
        pid, parent, group, rss = map(int, fields)
        all_rows.append({"pid": pid, "parent": parent, "pgid": group, "rss_bytes": rss * 1024})
    relevant = {pgid, *known_pids}
    while True:
        descendants = {r["pid"] for r in all_rows if r["parent"] in relevant or r["pgid"] == pgid}
        if descendants <= relevant:
            break
        relevant.update(descendants)
    rows = [r for r in all_rows if r["pid"] in relevant]
    measured = None
    try:
        measured = native(profile.read_text(), sys.platform)
    except (OSError, ValueError):
        problem = problem or "RESOURCE_UNKNOWN_STOP_SAMPLER_PROFILE"
    helper = {
        "role": f"rss-sampler-{index}",
        "exit_code": sample.returncode,
        "pid": sample.pid,
        "argv": command,
        "cleanup": cleanup,
        "timer_native_exit": getattr(sample, "timer_native_exit", None),
        "problem": problem,
        "native": measured,
        "profile": profile.name,
        "profile_sha256": digest(profile) if profile.exists() else None,
    }
    atomic_new(root / f"sampler-{index}.json", helper)
    return rows, helper


def _terminate(pgid, child):
    """Kill the session's registered process group even if its leader exited."""
    signals = []
    # Let the timing parent reap its ONE registered command first. Killing both
    # simultaneously can orphan a zombie under a non-reaping container PID1.
    # Extra/unobserved descendants still take the group cleanup path below.
    registered = getattr(child, "registered_command_pids", ())
    for sig in (signal.SIGTERM, signal.SIGKILL):
        if _native_poll(child) is not None:
            break  # Do not signal stale child identities after their parent exit.
        for pid in registered:
            try:
                os.kill(pid, sig)
                signals.append(sig.name + "_REGISTERED_COMMAND")
            except ProcessLookupError:
                pass
            except PermissionError:
                signals.append("EPERM_REGISTERED_COMMAND")
        if registered:
            try:
                _native_wait(child, 0.2)
            except subprocess.TimeoutExpired:
                pass
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(pgid, sig)
            signals.append(sig.name)
        except ProcessLookupError:
            pass
        except PermissionError:
            signals.append("EPERM_GROUP_SIGNAL")
        try:
            _native_wait(child, 2)
        except subprocess.TimeoutExpired:
            continue
        # A leader exiting does not prove its descendants have exited.
        try:
            os.killpg(pgid, 0)
        except ProcessLookupError:
            return {"signals": signals, "group_gone": True, "leader_exit": child.returncode}
        except PermissionError:
            return {"signals": signals, "group_gone": False, "leader_exit": child.returncode}
    try:
        os.killpg(pgid, 0)
        gone = False
    except ProcessLookupError:
        gone = True
    except PermissionError:
        gone = False
    return {"signals": signals, "group_gone": gone, "leader_exit": child.returncode}


def invoke(output, role, argv, *, timeout, limit_bytes=LIMIT, interval=0.5):
    """Record a bounded public command, including failure and observed group exit.

    API is also tested using newly authored subprocess fixtures. Public CLI argv
    is literal below. No scientific dispatch or PASS is available.
    """
    if (
        re.fullmatch(r"[a-z][a-z0-9-]{0,47}", role) is None
        or not math.isfinite(timeout)
        or timeout <= 0
        or type(limit_bytes) is not int
        or not 0 < limit_bytes <= LIMIT
        or not 0 < interval <= 0.5
        or not argv
        or not all(isinstance(a, str) and a for a in argv)
    ):
        raise ValueError("finite registered public command/caps required")
    root = Path(output).absolute() / role
    root.mkdir(parents=True, exist_ok=False)
    profile, log = root / "command.time", root / "command.log"
    started = monotonic()
    identity = {
        "schema": VERSION,
        "role": role,
        "software_only": True,
        "argv": argv,
        "cwd": str(REPO),
        "controller_pid": os.getpid(),
        "controller_parent_pid": os.getppid(),
        "controller_python": sys.executable,
        "platform": sys.platform,
        "lock_sha256": digest(REPO / "uv.lock"),
        "thread_environment": ENVIRONMENT,
        "native_program": "/usr/bin/time",
        "ps_program": "/bin/ps",
        "native_rss_unit": "bytes" if sys.platform == "darwin" else "KiB*1024",
        "ps_rss_unit": "KiB*1024",
        "target_sample_interval_seconds": interval,
        "timeout_seconds": timeout,
        "limit_bytes": limit_bytes,
        "profile": profile.name,
        "log": log.name,
    }
    atomic_new(root / "pending.json", {**identity, "status": "PENDING_BEFORE_INTERPRETER"})
    samples, helpers, reason, error = [], [], None, None
    known_pids, escaped_groups = set(), set()
    child = None
    cleanup = {"group_gone": None, "leader_exit": None, "signals": []}
    try:
        with log.open("xb") as stream:
            native_started = monotonic()
            child = subprocess.Popen(
                _timed(argv, profile),
                cwd=REPO,
                env={**os.environ, **ENVIRONMENT},
                stdout=stream,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
            child.native_started = native_started
            atomic_new(
                root / "started.json",
                {**identity, "status": "STARTED", "pid": child.pid, "pgid": child.pid},
            )
            while True:
                # Reap before sampling, so a normal just-exited leader does not
                # look like a descendant that outlived it in a stale snapshot.
                leader_exited = _native_poll(child) is not None
                rows, helper = _snapshot(root, len(samples), child.pid, known_pids)
                now = monotonic()
                helpers.append(helper)
                known_pids.update(r["pid"] for r in rows)
                child.registered_command_pids = tuple(
                    r["pid"] for r in rows if r["parent"] == child.pid and r["pgid"] == child.pid
                )
                escaped_groups.update(r["pgid"] for r in rows if r["pgid"] != child.pid)
                controller_peak = _rss_self()
                sample = {
                    "offset_seconds": now - started,
                    "actual_interval_seconds": None
                    if not samples
                    else now - started - samples[-1]["offset_seconds"],
                    "roles": rows,
                    "controller_rss_bytes": controller_peak,
                    "group_plus_controller_rss_bytes": sum(r["rss_bytes"] for r in rows)
                    + controller_peak,
                }
                samples.append(sample)
                if helper["problem"] is not None:
                    reason = helper["problem"]
                    break
                # The public launch registers /usr/bin/time and its ONE command,
                # no subprocess capability. Extra observed children or new
                # sessions are retained and stopped, never silently admitted.
                if (
                    escaped_groups
                    or len(rows) > 2
                    or any(r["pid"] != child.pid and r["parent"] != child.pid for r in rows)
                ):
                    reason = "RESOURCE_UNKNOWN_STOP_UNREGISTERED_DESCENDANT"
                    break
                if (
                    sample["group_plus_controller_rss_bytes"]
                    + helper["native"]["rss_bytes"]
                    + helper["timer_native_exit"]["native"]["rss_bytes"]
                    > limit_bytes
                ):
                    reason = "FAIL_RESOURCE_CAP"
                    break
                if now - started > timeout:
                    reason = "STOP_SCOPE_OR_WORK_CAP"
                    break
                if leader_exited:
                    if rows:
                        reason = "RESOURCE_UNKNOWN_STOP_DESCENDANT_OUTLIVED_LEADER"
                    break
                try:
                    _native_wait(
                        child, min(interval, max(0.001, timeout - (monotonic() - started)))
                    )
                except subprocess.TimeoutExpired:
                    pass
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        reason, error = "RESOURCE_UNKNOWN_STOP", type(exc).__name__
    finally:
        escaped_cleanup = []
        for group in escaped_groups:
            # Only groups observed as descendants of this launch are signalled.
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(group, sig)
                except ProcessLookupError:
                    pass
                except PermissionError:
                    pass  # Remains unconfirmed below; never accepted as group_gone.
            try:
                os.killpg(group, 0)
                gone = False
            except ProcessLookupError:
                gone = True
            except PermissionError:
                gone = False
            escaped_cleanup.append({"pgid": group, "group_gone": gone})
        if child is not None:
            cleanup = _terminate(child.pid, child)
        if not cleanup["group_gone"]:
            reason = reason or "RESOURCE_UNKNOWN_STOP_EXIT"
    measured = None
    try:
        measured = native(profile.read_text(), sys.platform)
    except (OSError, ValueError):
        reason = reason or "RESOURCE_UNKNOWN_STOP_PROFILE"
    # Include the controller and registered sampling helper alongside the
    # command's native high-water, including a peak seen only after exit.
    helper_peak = max(
        (
            h["native"]["rss_bytes"] + h["timer_native_exit"]["native"]["rss_bytes"]
            for h in helpers
            if h["native"] and h.get("timer_native_exit")
        ),
        default=0,
    )
    timer_exit = None if child is None else getattr(child, "timer_native_exit", None)
    if timer_exit is None or timer_exit["native"]["rss_bytes"] <= 0:
        reason = reason or "RESOURCE_UNKNOWN_STOP_TIMER_EXIT"
    final_controller_peak = _rss_self()
    native_overlap_rss = (
        None
        if measured is None or timer_exit is None
        else (
            measured["rss_bytes"]
            + timer_exit["native"]["rss_bytes"]
            + final_controller_peak
            + helper_peak
        )
    )
    if native_overlap_rss is not None and native_overlap_rss > limit_bytes:
        reason = "FAIL_RESOURCE_CAP"
    if child is not None and child.returncode != 0:
        reason = reason or "FAIL_PUBLIC_COMMAND"
    elapsed = monotonic() - started
    if elapsed > timeout:
        reason = reason or "STOP_SCOPE_OR_WORK_CAP"
    record = {
        **identity,
        "status": "PENDING_POSTEXIT",
        "software_result": reason or "PUBLIC_COMMAND_EXIT_OBSERVED",
        "error_type": error,
        "pid": None if child is None else child.pid,
        "exit_code": None if child is None else child.returncode,
        "timer_native_exit": timer_exit,
        "cleanup": cleanup,
        "observed_outer_wall_seconds": elapsed,
        "native": measured,
        "samples": samples,
        "helpers": helpers,
        "escaped_group_cleanup": escaped_cleanup,
        "native_plus_controller_and_sampler_rss_bytes": native_overlap_rss,
        "controller_rss_peak_bytes": final_controller_peak,
        "profile_sha256": digest(profile) if profile.exists() else None,
        "log_sha256": digest(log) if log.exists() else None,
        "controller_complete_exit": "UNKNOWN_PENDING_OUTER_PROFILE",
        "unobserved_escape_or_subsample_peak": "UNKNOWN_NOT_AN_INSTANTANEOUS_GUARANTEE",
        "timer_helper_individual_native_peak": "PARENT_WAIT4_EXIT_RUSAGE_RECORDED",
        "scientific_resource_admission": "NOT_RUN",
    }
    atomic_new(root / "command.json", record)
    return record


def role_charge(native_wall, observed_wall, attempted_rows, internal_charge):
    if (
        type(attempted_rows) is not int
        or attempted_rows < 0
        or any(
            x is None or not math.isfinite(x) or x < 0
            for x in (native_wall, observed_wall, internal_charge)
        )
    ):
        raise ValueError("RESOURCE_UNKNOWN_STOP: complete nonnegative charge evidence required")
    return max(internal_charge, max(native_wall, observed_wall) + attempted_rows + 10)


def rss_envelope(roles, simultaneous_sets):
    """Reconcile recorded evidence, never an allocation/instantaneous theorem.

    Missing coverage or overlap registration is UNKNOWN. Callers must put roles
    with uncertain overlap together; disjointness is not inferred from names.
    """
    names = {r["role"] for r in roles}
    if len(names) != len(roles) or not names or not simultaneous_sets:
        raise ValueError("RESOURCE_UNKNOWN_STOP: role coverage required")
    if any(set(group) != names for group in simultaneous_sets):
        # A currently conservative all-concurrent envelope avoids unsupported
        # exclusive-lifetime claims. Future disjoint tables need separate freeze.
        raise ValueError("RESOURCE_UNKNOWN_STOP: all roles conservatively concurrent in A")
    for role in roles:
        if (
            role.get("exit_code") != 0
            or role.get("group_gone") is not True
            or type(role.get("native_rss_bytes")) is not int
            or role["native_rss_bytes"] <= 0
            or type(role.get("sampled_rss_bytes")) is not int
            or role["sampled_rss_bytes"] < 0
            or not role.get("profile_sha256")
        ):
            raise ValueError("RESOURCE_UNKNOWN_STOP: incomplete role native/exit evidence")
    return max(
        sum(r["native_rss_bytes"] for r in roles), max(r["sampled_rss_bytes"] for r in roles)
    )


def bind_exit(output, record, profile, log, exit_code, *, label, root):
    """Append a binding after actual exit; never rewrite pre-exit states.

    The binder's own exit is deliberately pending; bind/verify it under a native
    outer command, then check the last verifier's actual profile in the observer.
    """
    if label not in ("controller", "binder", "verifier"):
        raise ValueError("unregistered exit role")
    root = Path(root).absolute()
    if root.resolve() != root or REPO in root.parents:
        raise PermissionError("literal new public software root required")
    table = {
        "controller": ("public-candidate/command.json", "PENDING_POSTEXIT"),
        "binder": ("controller-exit.json", "PENDING_BINDER_EXIT"),
        "verifier": ("binder-exit.json", "PENDING_VERIFIER_EXIT"),
    }
    prior, state = table[label]
    expected = [
        root / (label + "-exit.json"),
        root / prior,
        root / (label + ".time"),
        root / (label + ".log"),
    ]
    given = list(map(lambda p: Path(p).absolute(), (output, record, profile, log)))
    if given != expected or any(p.resolve() != p for p in given):
        raise PermissionError("only literal registered new public exit members allowed")
    record, profile, log = given[1:]
    if any(p.is_symlink() for p in (record, profile, log)):
        raise ValueError("immutable regular exit evidence required")
    marker = root / "stage-a-root.json"
    if (
        marker.is_symlink()
        or marker.stat().st_size > 1024
        or json.loads(marker.read_text())
        != {
            "schema": VERSION,
            "software_only": True,
            "input_scope": "new public fixtures only",
        }
    ):
        raise PermissionError("unregistered public software root")
    if record.stat().st_size > 4 * 1024 * 1024 or profile.stat().st_size > 1024 * 1024:
        raise ValueError("bounded public exit record/profile required")
    original = json.loads(record.read_text())
    if (
        original.get("schema") != VERSION
        or original.get("software_only") is not True
        or original.get("status") != state
    ):
        raise ValueError("exit binding source schema/state differs")
    if label != "controller":
        previous = "controller" if label == "binder" else "binder"
        if (
            original.get("bound_role") != previous
            or original.get("exit_code") != 0
            or original.get("resource_cap_exceeded") is not False
        ):
            raise ValueError("failed or mismatched prior exit binding")
        for field, suffix in (("profile", ".time"), ("log", ".log")):
            member = root / (previous + suffix)
            if (
                original.get(field) != str(member)
                or member.resolve() != member
                or original.get(field + "_sha256") != digest(member)
            ):
                raise ValueError("prior immutable native binding changed")
    measured = native(profile.read_text(), sys.platform)
    if type(exit_code) is not int:
        raise ValueError("actual observed exit required")
    result = {
        "schema": VERSION,
        "software_only": True,
        "bound_role": label,
        "status": "PENDING_BINDER_EXIT" if label == "controller" else "PENDING_VERIFIER_EXIT",
        "record": str(record.absolute()),
        "record_sha256": digest(record),
        "prior_status": original["status"],
        "native": measured,
        "profile": str(profile.absolute()),
        "profile_sha256": digest(profile),
        "log": str(log.absolute()),
        "log_sha256": digest(log),
        "exit_code": exit_code,
        "resource_cap_exceeded": measured["rss_bytes"] > LIMIT,
        "actual_observer_verification": "REQUIRED_AFTER_THIS_ROLE_EXITS",
        "scientific_resource_admission": "NOT_RUN",
    }
    atomic_new(Path(output), result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("public-run")
    run.add_argument("--fixture", choices=("tiny-prefix", "tiny-plain"), required=True)
    run.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.absolute()
    if REPO in output.parents or output.exists() or output.is_symlink():
        parser.error("new external software-only output required")
    output.mkdir(parents=True, exist_ok=False)
    atomic_new(
        output / "stage-a-root.json",
        {"schema": VERSION, "software_only": True, "input_scope": "new public fixtures only"},
    )
    result = invoke(
        output,
        "public-candidate",
        [
            sys.executable,
            str(REPO / "scripts/p17_m2_homotopy.py"),
            "--public-fixture",
            args.fixture,
            "--output",
            str(output / "fixture.json"),
        ],
        timeout=60,
    )
    return 0 if result["software_result"] == "PUBLIC_COMMAND_EXIT_OBSERVED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
