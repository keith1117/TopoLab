"""The independent caller's R2 clock around the complete native B preflight."""

import hashlib
import json
import math

IDENTITY = "native-bc-entry-20261126-r2"
B = "resource-preflight"
CAP = 4294967296


def need(value, reason):
    if not value:
        raise ValueError(reason)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def enabled(contract):
    return contract.get("entry_repair") == IDENTITY


def start_time(raw, contract_sha, role="b"):
    value = json.loads(raw)
    began = value.get("start_ms")
    need(
        type(began) is int
        and 0 <= began <= 2**53 - 1
        and raw
        == canonical(
            {
                "schema": f"topolab.{role}-clock-start.v1",
                "contract_sha256": contract_sha,
                "start_ms": began,
            }
        ),
        "B original caller start or contract differs",
    )
    return began


def prefix_subject(contract, evidence, proof, audit):
    """Cross-check the read-only JS native replay with this independently rechecked native tree."""
    contract_sha = proof["scientific_contract_sha256"]
    began = start_time(evidence["b_start"], contract_sha)
    publication = evidence["b_publication_event"]
    reservation = evidence["reservation_helper"]
    pending = reservation["pending"]["publication_readiness"]
    pub_raw = evidence["b_publication_raw"]
    need(
        publication.get("complete") is True
        and type(publication.get("exit_code")) is int
        and publication["exit_code"] == 0
        and publication["argv"]
        == [
            word.replace("@SCIENTIFIC_CONTRACT_SHA256@", contract_sha)
            for word in contract["roles"][B]["publication_argv"]
        ]
        and publication.get("stdout_sha256") == sha(pub_raw)
        and publication.get("profile_sha256") == sha(evidence["b_publication_profile"])
        and publication.get("publication_resource_sha256")
        == sha(evidence["b_publication_resource"])
        and pub_raw == canonical(pending)
        and pending.get("scientific_contract_sha256") == contract_sha
        and reservation["event"].get("publication_readiness_sha256") == sha(pub_raw)
        and publication["start_seconds"]
        <= pending["start_seconds"]
        <= pending["end_seconds"]
        <= publication["end_seconds"]
        <= reservation["event"]["start_seconds"]
        <= publication["end_seconds"] + 30
        and began / 1000 <= publication["start_seconds"],
        "B original publication outside caller window or not bound to reservation",
    )
    platform = contract["runtime"]["platform"]
    native_profile = audit.helper("p17_m2_independent_audit")._native_bytes
    pub_native = audit.helper("native_clock_measurement").check(
        audit,
        contract,
        contract_sha,
        B,
        "publication",
        profile=evidence["b_publication_profile"],
        resource=evidence["b_publication_resource"],
        stdout=pub_raw,
        start=publication["start_seconds"],
        end=publication["end_seconds"],
    )
    need(
        pub_native["wall_seconds"] <= publication["end_seconds"] - publication["start_seconds"] + 1,
        "B publication native profile exceeds actual lifetime",
    )
    peak = max(proof["conservative_recorded_peak_bytes"], pub_native["rss_bytes"])
    need(peak <= CAP, "B complete native RSS exceeded")
    res_profile = native_profile(reservation["profile"], platform)
    res_dispatch = proof["reservation_helper"]["native_dispatch"]
    native_seconds = (
        proof["b_native_outer_seconds"]
        + max(res_profile["wall_seconds"], res_dispatch["monotonic_wall_seconds"])
        + pub_native["wall_seconds"]
    )
    last = evidence["raw_tool_events"][-1]
    expected = {
        "schema": "topolab.b-verified-native-prefix.v1",
        "contract_sha256": contract_sha,
        "source_main": pending["publication_readiness"]["main"],
        "input_version_id": contract["acquisition"]["version_id"],
        "start_sha256": sha(evidence["b_start"]),
        "manifest_sha256": sha(evidence["b_manifest"]),
        "publication_start_seconds": publication["start_seconds"],
        "publication_profile_sha256": sha(evidence["b_publication_profile"]),
        "reservation_dispatch_sha256": sha(reservation["dispatch"]),
        "last_dispatch_sha256": sha(evidence["last_observer_dispatch"]),
        "last_profile_sha256": sha(evidence["last_observer_profile"]),
        "last_native_end_seconds": last["end_seconds"],
        "native_nonoverlapping_seconds": native_seconds,
        "inner_case_charge_seconds": proof["inner_charge_seconds"],
        "reservation_charge_seconds": proof["reservation_helper"]["active_charge_seconds"],
        "recorded_peak_bytes": peak,
    }
    candidate = json.loads(evidence["b_js_prefix"])
    expected_fields = set(expected) | {"observer_started_ms", "observer_completed_ms"}
    need(type(candidate) is dict and set(candidate) == expected_fields, "B JS prefix fields differ")
    for key, value in expected.items():
        datum = candidate[key]
        if key in (
            "native_nonoverlapping_seconds",
            "inner_case_charge_seconds",
            "reservation_charge_seconds",
        ):
            need(
                type(datum) in (float, int) and math.isfinite(datum) and abs(datum - value) <= 1e-9,
                "B JS/Python native subtotal differs",
            )
        else:
            need(datum == value, "B JS/Python prefix differs: " + key)
    need(
        type(candidate["observer_started_ms"]) is int
        and type(candidate["observer_completed_ms"]) is int
        and last["end_seconds"] <= candidate["observer_started_ms"] / 1000
        and candidate["observer_started_ms"] <= candidate["observer_completed_ms"],
        "B JS verification must follow actual final native return",
    )
    return {**expected, "observer_completed_ms": candidate["observer_completed_ms"]}


def prefix_stdout(contract_sha, start_raw, js_prefix_raw, role="b"):
    fields = {
        "schema": f"topolab.{role}-native-prefix-return.v1",
        "status": "VERIFIED_NATIVE_PREFIX_PENDING_CALLER_RETURN",
        "contract_sha256": contract_sha,
        "start_sha256": sha(start_raw),
        "js_prefix_sha256": sha(js_prefix_raw),
    }
    if role == "b":
        prefix = json.loads(js_prefix_raw)
        fields.update(
            status="PASS_PREFLIGHT_RSS_EXIT_EMPIRICAL",
            caller_must_validate_actual_return=True,
            source_main=prefix["source_main"],
            input_version_id=prefix["input_version_id"],
        )
    return canonical(fields)


def complete(contract, evidence, prefix, audit):
    """Accept only the caller's actual final verifier return, including its native profile."""
    policy = contract["b_caller_clock"]
    digest = prefix["contract_sha256"]
    started = start_time(evidence["b_start"], digest)
    packet = json.loads(evidence["b_return"])
    profile = evidence["b_verify_profile"]
    need(
        set(packet)
        == {
            "schema",
            "contract_sha256",
            "start_sha256",
            "verification_profile_sha256",
            "verification_resource_sha256",
            "actual",
        }
        and policy["schema"] == "topolab.b-full-clock.v1"
        and packet.get("schema") == "topolab.b-clock-return.v1"
        and packet.get("contract_sha256") == digest
        and packet.get("start_sha256") == sha(evidence["b_start"])
        and packet.get("verification_profile_sha256") == sha(profile)
        and packet.get("verification_resource_sha256") == sha(evidence["b_verify_resource"]),
        "B original final caller packet/profile binding differs",
    )
    argv = [
        word.replace("@SCIENTIFIC_CONTRACT_SHA256@", digest) for word in policy["verification_argv"]
    ]
    first, ended, stdout = audit.helper("r0_read_independent").terminal(
        packet["actual"],
        argv,
        author=policy["author"],
        cwd=contract["runtime"]["cwd"],
        window=(started, started + 170000),
        full=180,
    )
    need(
        started / 1000 <= prefix["publication_start_seconds"]
        and first >= prefix["observer_completed_ms"]
        and stdout == prefix_stdout(digest, evidence["b_start"], evidence["b_js_prefix"]),
        "B JS or independent final verifier raw return differs",
    )
    verified = audit.helper("native_clock_measurement").check(
        audit,
        contract,
        digest,
        B,
        "verification",
        profile=profile,
        resource=evidence["b_verify_resource"],
        stdout=stdout,
        start=first / 1000,
        end=ended / 1000,
    )
    need(
        verified["wall_seconds"] <= (ended - first) / 1000 + 1,
        "B verification native profile exceeds actual caller return",
    )
    native = prefix["native_nonoverlapping_seconds"] + verified["wall_seconds"]
    whole = (ended - started) / 1000
    internal = prefix["inner_case_charge_seconds"] + prefix["reservation_charge_seconds"]
    charge = max(internal, max(whole, native) + 10)
    peak = max(prefix["recorded_peak_bytes"], verified["rss_bytes"])
    need(math.isfinite(charge) and charge <= 180, "B complete caller charge exceeds FULL180")
    need(peak <= CAP, "B complete recorded native RSS exceeds 4GiB")
    return {
        "FULL_charged_seconds": 180,
        "whole_wall_seconds": whole,
        "whole_native_seconds": native,
        "inner_charge_seconds": internal,
        "known_complete_charge_seconds": charge,
        "conservative_recorded_peak_bytes": peak,
        "reservation_helper_charged_in_shared_FULL180": False,
        "reservation_charge_seconds_in_C": 0,
        "actual_final_verifier_exit_observed": True,
        "b_caller_start_ms": started,
        "b_caller_end_ms": ended,
        "b_caller_return_sha256": sha(evidence["b_return"]),
    }
