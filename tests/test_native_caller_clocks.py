"""Shared, non-numerical public events for the independent JS/Python caller clocks."""

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
BASE_MS = 1_700_000_000_000
SHA = "a" * 64
B_CASES = (
    "exact-170",
    "late-170.001",
    "internal-180.001",
    "native-170.001",
    "late-final-poll",
    "start-after-publication",
    "missing-return",
    "live-session",
    "missing-profile",
    "rss-plus-one",
    "wrong-input-version",
    "another-command",
    "C-charged-reservation",
    "double-charged-reservation",
    "receipt-without-PASS",
    "missing-timer-rusage",
    "missing-sampler",
    "sampler-rss-plus-one",
    "unregistered-descendant",
    "self-rss-unknown",
    "changed-resource-anchor",
)
C_CASES = ("C-exact-180", "C-over-180", "C-rss-plus-one", "C-live", "C-charged-B")


def module(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"


def sha(value):
    return hashlib.sha256(value.encode()).hexdigest()


def watched_resource(contract, stage, packet_argv, profile, stdout, first, case):
    from test_p17_m2_scientific_independent import dispatched_evidence, seal_dispatch

    audit = module("p17_m2_scientific_independent")
    role = "scientific-auditor" if stage == "c" else "resource-preflight"
    reg = contract[stage + "_caller_clock"]
    label = "clock-verification"
    dummy = {"runtime": contract["runtime"], "shared_helpers": {role: {label: {}}}}
    evidence = {
        "event": {"start_seconds": first / 1000},
        "log": stdout.encode(),
        "profile": profile.encode(),
    }
    record = dispatched_evidence(audit, dummy, evidence, role, label)
    path = reg["verification_timed_argv"][3]
    record["native_log_facts"]["path"] = path + ".command.log"
    record.update(
        contract_sha256=SHA,
        argv=reg["verification_timed_argv"],
        dispatch_argv=reg["verification_argv"],
        startup_orig_argv=[contract["runtime"]["python_startup_entry"], *packet_argv[1:]],
    )
    if case == "missing-timer-rusage":
        record["timer_native_exit"]["statistics_source"] = "missing"
    seal_dispatch(audit, evidence, record)
    helper_profile = "0.02 real 0.00 user 0.01 sys\n1024 maximum resident set size\n"
    helper = {
        "role": "rss-sampler-0",
        "argv": [
            "/usr/bin/time",
            "-l",
            "-o",
            path + ".samplers/sampler-0.time",
            "/bin/ps",
            "-axo",
            "pid=,ppid=,pgid=,rss=",
        ],
        "profile": "sampler-0.time",
        "profile_sha256": sha(helper_profile),
        "pid": 804,
        "exit_code": 0,
        "problem": None,
        "cleanup": record["cleanup"],
        "timer_native_exit": {**record["timer_native_exit"], "pid": 804},
        "native": audit.helper("p17_m2_independent_audit")._native_bytes(
            helper_profile.encode(), "darwin"
        ),
    }
    if case == "sampler-rss-plus-one":
        helper["timer_native_exit"] = {
            **helper["timer_native_exit"],
            "native": {
                **helper["timer_native_exit"]["native"],
                "rss_bytes": 4294967296 - 1024 * 8 + 1,
            },
        }
    rows = [
        {"pid": 102, "parent": 101, "pgid": 102, "rss_bytes": 1024},
        {"pid": 103, "parent": 102, "pgid": 102, "rss_bytes": 1024},
    ]
    if case == "unregistered-descendant":
        rows.append({"pid": 104, "parent": 103, "pgid": 102, "rss_bytes": 1024})
    return raw(
        {
            "schema": "topolab.native-clock-watch.v1",
            "record_text": evidence["dispatch"].decode(),
            "preflush_text": evidence["preflush"].decode(),
            "samples": []
            if case == "missing-sampler"
            else [
                {
                    "offset_seconds": 0.01,
                    "profile_text": helper_profile,
                    "helper": helper,
                    "rows": rows,
                    "controller_rss_bytes": 1024,
                }
            ],
            "wrapper_rss_before_output": 0 if case == "self-rss-unknown" else 1024,
        }
    )


def fixture(case):
    c = case in C_CASES
    role = "c" if c else "b"
    start = BASE_MS + (1001 if case == "start-after-publication" else 0)
    start_raw = raw(
        {"schema": "topolab." + role + "-clock-start.v1", "start_ms": start, "contract_sha256": SHA}
    )
    root = "/private/tmp/public clock"
    verify = role.upper() + "-verify.time"
    argv = [
        "/usr/bin/time",
        "-l",
        "-o",
        root + "/" + verify,
        "/public/bin/python",
        "-I",
        root + "/native_" + role + "_prefix.py",
        "--contract",
        root + "/contract.json",
        "--contract-sha",
        SHA,
    ]
    inner = argv
    argv = [
        "/public/bin/python",
        "-I",
        root + "/native_clock_watch.py",
        "--phase",
        "verification",
        "--contract-sha",
        SHA,
    ]
    policy = {
        "verification_timed_argv": inner,
        "verification_argv": argv,
        "author": "/independent",
        "schema": "topolab.c-shared-clock.v1" if c else "topolab.b-full-clock.v1",
    }
    contract = {
        "entry_repair": "native-bc-entry-20261126-r2",
        "runtime": {
            "cwd": root,
            "platform": "darwin",
            "python_entry": "/public/bin/python",
            "python_startup_entry": "/public/bin/python",
        },
        "api_metadata": {"root": root},
        "acquisition": {"version_id": "7" * 64},
        role + "_caller_clock": policy,
    }
    epoch = BASE_MS / 1000
    prefix = {
        "schema": f"topolab.{role}-verified-native-prefix.v1",
        "contract_sha256": SHA,
        "start_sha256": sha(start_raw),
        "manifest_sha256": "5" * 64,
    }
    if c:
        prefix.update(
            b_caller_return_sha256="f" * 64,
            b_caller_end_ms=BASE_MS - 1,
            last_ack_dispatch_sha256="e" * 64,
            last_ack_end_seconds=epoch + 1008,
            role_spans=[[epoch + 2, epoch + 702], [epoch + 705, epoch + 1005]],
            active_helper_charge_seconds=8,
            native_shared_seconds=7,
            shared_prefix_peak_bytes=4096,
            observer_started_ms=BASE_MS + 1010000,
            observer_completed_ms=BASE_MS + 1011000,
        )
    else:
        prefix.update(
            source_main="6" * 40,
            input_version_id=contract["acquisition"]["version_id"],
            publication_start_seconds=epoch + 1,
            publication_profile_sha256="b" * 64,
            reservation_dispatch_sha256="c" * 64,
            last_dispatch_sha256="d" * 64,
            last_profile_sha256="e" * 64,
            last_native_end_seconds=epoch + 35,
            native_nonoverlapping_seconds=170.001 if case == "native-170.001" else 45,
            inner_case_charge_seconds=177.001 if case == "internal-180.001" else 10,
            reservation_charge_seconds=3,
            recorded_peak_bytes=4096,
            observer_started_ms=BASE_MS + 36000,
            observer_completed_ms=BASE_MS + 37000,
        )
    js_prefix_raw = raw(prefix)
    text = (
        module("native_b_clock")
        .prefix_stdout(SHA, start_raw.encode(), js_prefix_raw.encode(), role)
        .decode()
    )
    if case == "receipt-without-PASS":
        text = text.replace("PASS_PREFLIGHT_RSS_EXIT_EMPIRICAL", "PENDING")
    if case == "wrong-input-version":
        text = text.replace("7" * 64, "1" * 64)
    final = BASE_MS + (1166000 if c else 170000)
    if case in ("late-170.001", "late-final-poll", "C-over-180"):
        final += 1
    if case == "another-command":
        argv = argv[:-1] + ["9" * 64]
    helper = module("r0_read_independent")
    request = {"cmd": helper.literal_command(argv), "workdir": root, "max_output_tokens": 2000}
    first = BASE_MS + (1110000 if c else 100000)
    rows = [
        {
            "tool": "exec_command",
            "arguments": request,
            "requested_ms": first,
            "returned_ms": first + 30,
            "result": {"exit_code": None, "session_id": 8931, "output": text[:20]},
        },
        {
            "tool": "write_stdin",
            "arguments": {"session_id": 8931, "chars": "", "yield_time_ms": 5000},
            "requested_ms": first + 31,
            "returned_ms": final,
            "result": {"exit_code": 0, "output": text[20:]},
        },
    ]
    if case == "missing-return":
        rows = rows[:1]
    if case in ("live-session", "C-live"):
        rows[-1]["result"].update(session_id=8931, exit_code=None)
    peak = 4294967297 if case in ("rss-plus-one", "C-rss-plus-one") else 4096
    profile = (
        ""
        if case == "missing-profile"
        else f"0.00 real 0.00 user 0.00 sys\n{peak} maximum resident set size\n"
    )
    actual = {
        "schema": helper.ACTUAL_SCHEMA,
        "argv": argv,
        "request": request,
        "responses": rows,
        "author": policy["author"],
    }
    resource = watched_resource(contract, role, argv, profile, text, first, case)
    packet = {
        "verification_resource_sha256": sha(resource)
        if case != "changed-resource-anchor"
        else "1" * 64,
        "schema": f"topolab.{role}-clock-return.v1",
        "contract_sha256": SHA,
        "start_sha256": sha(start_raw),
        "verification_profile_sha256": sha(profile),
        "actual": actual,
    }
    if case in ("C-charged-reservation", "double-charged-reservation", "C-charged-B"):
        packet["reservation_charge_seconds_in_C"] = 3
    return dict(
        case=case,
        role=role,
        contract=contract,
        contractSHA256=SHA,
        startRaw=start_raw,
        returnRaw=raw(packet),
        jsPrefixRaw=js_prefix_raw,
        verifyProfileRaw=profile,
        verifyResourceRaw=resource,
        manifestSHA256=prefix["manifest_sha256"],
        prefix=prefix,
    )


def check_python(data):
    prefix = data["prefix"]
    audit = module("p17_m2_scientific_independent")
    if data["role"] == "c":
        return module("native_c_clock").complete(
            data["contract"],
            prefix,
            {
                "start": data["startRaw"].encode(),
                "js_prefix": data["jsPrefixRaw"].encode(),
                "actual": data["returnRaw"].encode(),
                "verify_profile": data["verifyProfileRaw"].encode(),
                "verify_resource": data["verifyResourceRaw"].encode(),
            },
            audit,
        )
    return module("native_b_clock").complete(
        data["contract"],
        {
            "b_start": data["startRaw"].encode(),
            "b_js_prefix": data["jsPrefixRaw"].encode(),
            "b_return": data["returnRaw"].encode(),
            "b_verify_profile": data["verifyProfileRaw"].encode(),
            "b_verify_resource": data["verifyResourceRaw"].encode(),
        },
        prefix,
        audit,
    )


@pytest.mark.parametrize("case", B_CASES + C_CASES)
def test_python_and_js_use_identical_caller_evidence(case):
    data = fixture(case)
    try:
        py = check_python(data)
    except ValueError:
        py = None
    assert (py is not None) == (case in ("exact-170", "C-exact-180"))
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node unavailable for the independent JS replay")
    result = subprocess.run(
        [node, str(REPO / "tests" / "check_native_caller_clock.mjs")],
        input=raw(data),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == (0 if py else 1), result.stderr
    if py:
        js = json.loads(result.stdout)
        for key in py:
            assert js[key] == py[key], key


if __name__ == "__main__":
    subject = fixture(sys.argv[1])
    if len(sys.argv) > 2 and sys.argv[2] == "emit":
        sys.stdout.write(raw(subject))
    else:
        print(raw(check_python(subject)), end="")
