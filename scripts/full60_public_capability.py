"""Replay one prior public buffer, reading only the frozen auditor software."""

import base64
import hashlib
import importlib.util
import json
import shlex
from pathlib import Path

BUDGET = "cfa8ac55d9f1879fdc9242db76b78c6661f38649e97162d0fe39339600629ec0"
EVIDENCE = "/Users/keith1117/Documents/TopoLab-data/container-full60-input-admission-20261116"


def need(value, reason):
    if not value:
        raise ValueError("NEW_PUBLIC_CAPABILITY: " + reason)


def verify_public_capability(raw):
    need(type(raw) is bytes and len(raw) <= 16 * 1024**2, "bounded raw acceptance required")
    value = json.loads(raw)
    need(
        value.get("schema") == "topolab.public-full60-final-acceptance.v1"
        and value.get("owner_budget_sha256") == BUDGET,
        "exact new acceptance identity differs",
    )
    package_raw = base64.b64decode(value["public_package_base64"], validate=True)
    package = json.loads(package_raw)
    static = json.loads(base64.b64decode(package["static_base64"], validate=True))
    authority = value["independent_static_authority"]
    static_sha = authority["static_sha256"]
    need(
        authority["author"] == "/root/full60_independent"
        and authority["status"] == "PREREGISTERED_ACCEPTANCE_AUTHORITY"
        and authority["source_sha256"] == static["source_sha256"]
        and authority["registered_ms"] < package["external"]["responses"][0]["requested_ms"],
        "independent static authority did not precede actual producer call",
    )
    script = Path(__file__).with_name("public_containment_audit.py")
    source = script.read_bytes()
    need(
        hashlib.sha256(source).hexdigest() == static["source_sha256"][script.name],
        "independent public auditor source changed",
    )
    spec = importlib.util.spec_from_file_location("new_public_capability_auditor", script)
    auditor = importlib.util.module_from_spec(spec)
    exec(compile(source, str(script), "exec"), auditor.__dict__)
    verdict = auditor.audit_package(package_raw, value["public_package_sha256"], static_sha)
    actual = value["independent_actual"]
    rows = actual["responses"]
    need(
        actual["schema"] == "topolab.public-containment.actual-call.v1"
        and actual["author"] == "/root/full60_independent"
        and 1 <= len(rows) <= 17,
        "independent original terminal call missing",
    )
    t0 = rows[0]["requested_ms"]
    expected = [
        static["python"],
        "-I",
        "-u",
        static["cwd"] + "/scripts/public_containment_entry.py",
        "--audit",
        EVIDENCE + "/public-audit-package-a1.json",
        "--sha256",
        value["public_package_sha256"],
        "--public-static-sha256",
        static_sha,
        "--requested-ms",
        str(t0),
    ]
    need(
        actual["argv"] == expected
        and actual["request"]["cmd"] == shlex.join(expected)
        and actual["request"]["workdir"] == static["cwd"]
        and t0 + 7260000 <= 1794852900000,
        "independent exact argv/budget differs",
    )
    previous, session = t0, None
    for index, row in enumerate(rows):
        result, args = row["result"], row["arguments"]
        need(
            type(row["requested_ms"]) is int
            and type(row["returned_ms"]) is int
            and previous <= row["requested_ms"] <= row["returned_ms"],
            "actual clocks differ",
        )
        need(
            isinstance(result.get("output"), str) and "truncated" not in result["output"].lower(),
            "original output incomplete",
        )
        if index == 0:
            need(row["tool"] == "exec_command" and args == actual["request"], "initial request")
        else:
            need(
                row["tool"] == "write_stdin"
                and args["session_id"] == session
                and args.get("chars", "") == ""
                and type(args.get("yield_time_ms", 5000)) is int
                and 0 < args.get("yield_time_ms", 5000) <= 30000,
                "owned original bounded poll required",
            )
        count = result.get("original_token_count")
        need(
            count is None
            or (type(count) is int and 0 <= count <= args.get("max_output_tokens", 10000)),
            "original response token completeness differs",
        )
        if index == len(rows) - 1:
            need(
                type(result.get("exit_code")) is int
                and result["exit_code"] == 0
                and result.get("session_id") is None,
                "actual independent exit0 missing",
            )
        else:
            need(
                result.get("exit_code") is None
                and type(result.get("session_id")) is int
                and (session is None or session == result["session_id"]),
                "live poll changed",
            )
            session = result["session_id"]
        previous = row["returned_ms"]
    need(
        verdict["external"]["T1_ms"] <= t0 <= previous <= t0 + 50000,
        "independent actual return exceeds original FULL60 margin",
    )
    receipt = json.loads(base64.b64decode(value["independent_before_return_base64"], validate=True))
    auditor._entry(
        receipt,
        {"start_unix_ns": t0 * 10**6, "start_monotonic_ns": receipt["start_monotonic_ns"]},
        receipt["pid"],
    )
    need(
        receipt["primary_error"] is None
        and receipt["work_return"] == 0
        and receipt["verdict"] == verdict
        and receipt["pid"] == receipt["pgid"] == receipt["sid"]
        and receipt["start_unix_ns"] == t0 * 10**6
        and receipt["guardian"]["deadline_unix_ns"] == t0 * 10**6 + 45 * 10**9
        and receipt["guardian"]["parent_pid"] == receipt["pid"]
        and receipt["guardian_future_cancel_reap"] == "PENDING_ACTUAL_ENTRY_EXIT0",
        "independent guarded before-return context differs",
    )
    return {
        "status": "ACTUAL_PUBLIC_CAPABILITY_REPLAYED",
        "public_static_sha256": static_sha,
        "source_sha256": static["source_sha256"],
        "public_T1_ms": verdict["external"]["T1_ms"],
        "independent_T1_ms": previous,
        "input_accepted": False,
    }
