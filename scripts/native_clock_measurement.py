"""Independently reconstruct the measured command, its timer, observer and concurrent samplers."""

import json
import math


def check(audit, contract, digest, role, phase, *, resource, profile, stdout, start, end):
    need = audit.require
    need(
        contract["runtime"]["platform"] == "darwin" and 0 < len(resource) <= 4 * 1024**2,
        "bounded native Darwin clock resource packet required",
    )
    if phase == "publication":
        spec = contract["roles"][role]
        timed, wrapper = spec["publication_timed_argv"], spec["publication_argv"]
        path = spec["publication_profile_path"]
    else:
        need(
            phase == "verification" and role in ("resource-preflight", "scientific-auditor"),
            "unregistered native clock phase",
        )
        stage = "B" if role == "resource-preflight" else "C"
        spec = contract[stage.lower() + "_caller_clock"]
        timed, wrapper = spec["verification_timed_argv"], spec["verification_argv"]
        path = contract["api_metadata"]["root"] + "/" + stage + "-verify.time"
    timed = audit.resolve_argv(timed, digest)
    need(
        timed[:4] == ["/usr/bin/time", "-l", "-o", path] and len(timed) > 4,
        "native clock command or profile registration differs",
    )
    sidecar = json.loads(resource)
    need(
        resource == audit.canonical(sidecar)
        and set(sidecar)
        == {"schema", "preflush_text", "record_text", "samples", "wrapper_rss_before_output"}
        and sidecar["schema"] == "topolab.native-clock-watch.v1",
        "native clock resource schema",
    )
    dispatch = sidecar["record_text"].encode("ascii")
    record = json.loads(dispatch)
    files = {"dispatch_argv": wrapper, "timeout_seconds": 170, "log_path": path + ".command.log"}
    evidence = {
        "dispatch": dispatch,
        "preflush": sidecar["preflush_text"].encode("ascii"),
        "log": stdout,
        "profile": profile,
        "event": {"start_seconds": start, "end_seconds": end},
    }
    recorded = audit._check_native_record(
        contract, digest, role, "clock-" + phase, files, timed, evidence
    )
    need(
        record["native_log_facts"]["path"] == files["log_path"], "native clock log identity differs"
    )
    old = audit.helper("p17_m2_independent_audit")
    samples = sidecar["samples"]
    wrapper = sidecar["wrapper_rss_before_output"]
    need(
        type(wrapper) is int
        and wrapper >= recorded["dispatcher_self_rss_bytes"]
        and type(samples) is list
        and 0 < len(samples) <= 342,
        "native clock wrapper self RSS or process samples missing",
    )
    previous = None
    helper_peak = sampled_peak = 0
    for index, sample in enumerate(samples):
        h = sample["helper"]
        raw = sample["profile_text"].encode("ascii")
        measured = old._native_bytes(raw, "darwin")
        name = f"sampler-{index}.time"
        expected_argv = [
            "/usr/bin/time",
            "-l",
            "-o",
            path + ".samplers/" + name,
            "/bin/ps",
            "-axo",
            "pid=,ppid=,pgid=,rss=",
        ]
        need(
            h["role"] == f"rss-sampler-{index}"
            and h["argv"] == expected_argv
            and h["profile"] == name
            and h["profile_sha256"] == audit.digest(raw)
            and h["native"] == measured
            and type(h["exit_code"]) is int
            and h["exit_code"] == 0
            and h["problem"] is None
            and h["cleanup"]["group_gone"] is True
            and h["cleanup"]["final_group_gone"] is True
            and h["cleanup"]["leader_exit"] == 0
            and h["cleanup"]["signals"] == []
            and h["cleanup"]["observation_limit_exceeded"] is False,
            "unregistered, incomplete or failed native clock sampler",
        )
        timer = h["timer_native_exit"]
        need(
            type(h["pid"]) is int
            and h["pid"] > 0
            and timer["pid"] == h["pid"]
            and timer["source"]
            == "parent os.wait4 native exit rusage; possible descendant aggregation",
            "native clock sampler timer PID differs",
        )
        cost = measured["rss_bytes"] + old._timer_exit(timer, 0, "darwin")
        offset, own, rows = sample["offset_seconds"], sample["controller_rss_bytes"], sample["rows"]
        need(
            type(offset) in (int, float)
            and math.isfinite(offset)
            and 0 <= offset <= recorded["monotonic_wall_seconds"]
            and (previous is None or previous < offset)
            and type(own) is int
            and 0 < own <= wrapper,
            "native clock sampler interval or controller RSS differs",
        )
        previous = offset
        pid = record["native_pid"]
        need(
            type(rows) is list
            and len(rows) <= 2
            and len({row["pid"] for row in rows}) == len(rows)
            and len([row for row in rows if row["parent"] == pid]) <= 1
            and all(
                type(row["pid"]) is int
                and row["pid"] > 0
                and type(row["parent"]) is int
                and row["parent"] >= 0
                and row["pgid"] == pid
                and (row["pid"] == pid or row["parent"] == pid)
                and type(row["rss_bytes"]) is int
                and row["rss_bytes"] >= 0
                for row in rows
            ),
            "unregistered native clock descendant or invalid group RSS",
        )
        helper_peak = max(helper_peak, cost)
        sampled_peak = max(sampled_peak, own + cost + sum(row["rss_bytes"] for row in rows))
    peak = max(
        sampled_peak,
        wrapper
        + recorded["command_native_rss_bytes"]
        + recorded["timer_wait4_rss_bytes"]
        + helper_peak,
    )
    need(peak <= 4294967296, "clock command/timer/observer/concurrent sampler exceeds 4GiB")
    wall = max(
        recorded["monotonic_wall_seconds"], old._native_bytes(profile, "darwin")["wall_seconds"]
    )
    return {"wall_seconds": wall, "rss_bytes": peak}
