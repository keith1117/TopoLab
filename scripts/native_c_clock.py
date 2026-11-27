"""Count all C-only shared work around the two already charged, disjoint C roles."""

import json
import math


def native_prefix(contract, contract_sha, role_evidence, records, clock_evidence, audit):
    b = audit.helper("native_b_clock")
    native = audit.helper("p17_m2_independent_audit")._native_bytes
    platform = contract["runtime"]["platform"]
    c_start = b.start_time(clock_evidence["start"], contract_sha, "c")
    closed = audit.check_shared_closeout(contract, records, role_evidence=role_evidence)
    clock = closed["b_admission_proof"]
    helpers = closed["helpers"]
    b.need(clock["b_caller_end_ms"] <= c_start, "C started before complete B caller return")
    roles = ("scientific-producer", "scientific-auditor")
    expected = {
        "schema": "topolab.c-verified-native-prefix.v1",
        "contract_sha256": contract_sha,
        "start_sha256": b.sha(clock_evidence["start"]),
        "manifest_sha256": b.sha(clock_evidence["manifest"]),
        "b_caller_return_sha256": clock["b_caller_return_sha256"],
        "b_caller_end_ms": clock["b_caller_end_ms"],
        "last_ack_dispatch_sha256": b.sha(records[-1]["dispatch"]),
        "last_ack_end_seconds": records[-1]["event"]["end_seconds"],
    }
    spans = []
    peak = closed["native_peak_bytes"]
    native_seconds = 0.0
    for row, checked in zip(records, helpers, strict=True):
        profile = native(row["profile"], platform)
        native_seconds += max(
            profile["wall_seconds"], checked["native_dispatch"]["monotonic_wall_seconds"]
        )
    previous = c_start / 1000
    for index, role in enumerate(roles):
        pub = clock_evidence["publications"][role]
        evidence = role_evidence[role]
        first, last = evidence["raw_tool_events"][0], evidence["raw_tool_events"][-1]
        rs, ack = records[2 * index : 2 * index + 2]
        raw = pub["raw"]
        pending = rs["pending"]["publication_readiness"]
        event = pub["event"]
        b.need(
            event.get("complete") is True
            and type(event.get("exit_code")) is int
            and event["exit_code"] == 0
            and event["argv"]
            == audit.resolve_argv(contract["roles"][role]["publication_argv"], contract_sha)
            and raw == b.canonical(pending)
            and event["stdout_sha256"] == b.sha(raw)
            and event.get("profile_sha256") == b.sha(pub["profile"])
            and event.get("publication_resource_sha256") == b.sha(pub["resource"])
            and rs["event"]["publication_readiness_sha256"] == b.sha(raw)
            and pending["role"] == role
            and pending["scientific_contract_sha256"] == contract_sha
            and previous
            <= event["start_seconds"]
            <= pending["start_seconds"]
            <= pending["end_seconds"]
            <= event["end_seconds"]
            <= rs["event"]["start_seconds"]
            <= event["end_seconds"] + 30
            and rs["event"]["end_seconds"]
            <= first["start_seconds"]
            <= last["end_seconds"]
            <= ack["event"]["start_seconds"],
            "C shared publication/role chronology differs",
        )
        profile = audit.helper("native_clock_measurement").check(
            audit,
            contract,
            contract_sha,
            role,
            "publication",
            profile=pub["profile"],
            resource=pub["resource"],
            stdout=raw,
            start=event["start_seconds"],
            end=event["end_seconds"],
        )
        b.need(
            profile["wall_seconds"] <= event["end_seconds"] - event["start_seconds"] + 1,
            "C publication native profile exceeds actual lifetime",
        )
        native_seconds += profile["wall_seconds"]
        peak = max(peak, profile["rss_bytes"])
        spans.append([first["start_seconds"], last["end_seconds"]])
        previous = ack["event"]["end_seconds"]
    expected.update(
        role_spans=spans,
        native_shared_seconds=native_seconds,
        active_helper_charge_seconds=sum(p["active_charge_seconds"] for p in helpers),
        shared_prefix_peak_bytes=peak,
    )
    b.need(peak <= b.CAP, "C shared RSS exceeds 4GiB")
    candidate = json.loads(clock_evidence["js_prefix"])
    b.need(
        set(candidate) == set(expected) | {"observer_started_ms", "observer_completed_ms"},
        "C JS prefix fields differ",
    )
    for key, value in expected.items():
        if key in ("active_helper_charge_seconds", "native_shared_seconds"):
            b.need(
                type(candidate[key]) in (int, float)
                and math.isfinite(candidate[key])
                and abs(candidate[key] - value) <= 1e-9,
                "C JS shared subtotal differs",
            )
        else:
            b.need(candidate[key] == value, "C JS/Python prefix differs: " + key)
    b.need(
        type(candidate["observer_started_ms"]) is int
        and type(candidate["observer_completed_ms"]) is int
        and expected["last_ack_end_seconds"] <= candidate["observer_started_ms"] / 1000
        and candidate["observer_started_ms"] <= candidate["observer_completed_ms"],
        "C JS replay must follow final ACK",
    )
    return {**expected, "observer_completed_ms": candidate["observer_completed_ms"]}


def complete(contract, proof, evidence, audit):
    b = audit.helper("native_b_clock")
    policy = contract["c_caller_clock"]
    digest = proof["contract_sha256"]
    started = b.start_time(evidence["start"], digest, "c")
    packet = json.loads(evidence["actual"])
    profile = evidence["verify_profile"]
    b.need(
        set(packet)
        == {
            "schema",
            "contract_sha256",
            "start_sha256",
            "verification_profile_sha256",
            "verification_resource_sha256",
            "actual",
        }
        and policy["schema"] == "topolab.c-shared-clock.v1"
        and packet.get("schema") == "topolab.c-clock-return.v1"
        and packet.get("contract_sha256") == digest
        and packet.get("start_sha256") == b.sha(evidence["start"])
        and packet.get("verification_profile_sha256") == b.sha(profile)
        and packet.get("verification_resource_sha256") == b.sha(evidence["verify_resource"]),
        "C shared final raw packet/profile binding differs",
    )
    argv = audit.resolve_argv(policy["verification_argv"], digest)
    first, ended, stdout = audit.helper("r0_read_independent").terminal(
        packet["actual"],
        argv,
        author=policy["author"],
        cwd=contract["runtime"]["cwd"],
        window=(started, started + 14580000),
        full=180,
    )
    b.need(
        first >= proof["observer_completed_ms"]
        and stdout == b.prefix_stdout(digest, evidence["start"], evidence["js_prefix"], "c"),
        "C verifier actual stdout differs",
    )
    measured = audit.helper("native_clock_measurement").check(
        audit,
        contract,
        digest,
        "scientific-auditor",
        "verification",
        profile=profile,
        resource=evidence["verify_resource"],
        stdout=stdout,
        start=first / 1000,
        end=ended / 1000,
    )
    b.need(measured["wall_seconds"] <= (ended - first) / 1000 + 1, "C final verifier span differs")
    # Compute disjoint gaps separately to preserve the exact boundary at realistic epoch times.
    start_p, end_p = proof["role_spans"][0]
    start_a, end_a = proof["role_spans"][1]
    active_ms = (
        (start_p * 1000 - started) + (1000 * start_a - 1000 * end_p) + (ended - 1000 * end_a)
    )
    native = proof["native_shared_seconds"] + measured["wall_seconds"]
    peak = max(proof["shared_prefix_peak_bytes"], measured["rss_bytes"])
    charge = max(proof["active_helper_charge_seconds"] + 10, max(active_ms / 1000, native) + 14)
    b.need(
        peak <= b.CAP and 0 <= active_ms and math.isfinite(charge) and charge <= 180,
        "C complete shared charge/RSS exceeds limit",
    )
    return {
        "FULL_charged_seconds": 180,
        "known_complete_charge_seconds": charge,
        "shared_wall_seconds": active_ms / 1000,
        "shared_native_seconds": native,
        "shared_peak_bytes": peak,
        "C_helper_recording_seconds": 4,
        "B_reservation_charge_seconds": 0,
        "c_caller_start_ms": started,
        "c_caller_end_ms": ended,
        "c_caller_return_sha256": b.sha(evidence["actual"]),
    }
