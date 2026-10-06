"""Native whole-command closure preserving the original failed B4.23 feasibility Gate."""

from time import perf_counter

from b4_10_resource_close import profile
from b4_24_versioned_correctness_failure_review import (
    EVIDENCE_NEXT,
    arguments,
    boundary_fields,
    canonical,
    check_inputs,
    execution_release,
    peak_rss,
    plan_payload,
    read,
    safe_hash,
    sha,
)


def close_resources(output, commands, review, audit):
    if [c["name"] for c in commands] not in (["plan", "review"], ["plan", "review", "independent"]):
        raise ValueError("requires exclusive ordered stages, no automatic retry")
    charges, peaks, hashes = {}, [], {}
    for command in commands:
        name = command["name"]
        if (
            command["profile"] != "profiles/" + name + ".time"
            or command["log"] != "logs/" + name + ".log"
        ):
            raise ValueError("requires contained distinct profiles and logs")
        safe_hash(output, command["profile"], command["profile_sha256"])
        safe_hash(output, command["log"], command["log_sha256"])
        wall, rss = profile(output / command["profile"])
        peaks.append(rss)
        hashes[name + ".time"] = command["profile_sha256"]
        if name != "plan":
            receipt = (review if name == "review" else audit) if command["exit_code"] == 0 else None
            if command["exit_code"] == 0 and receipt is None:
                raise ValueError("successful stage missing its complete receipt")
            charges[name] = max(wall + 10, receipt["charged_seconds"] if receipt else 0)
            if charges[name] > 60:
                raise ValueError("read-only stage cap exceeded")
        if rss > 1073741824:
            raise ValueError("native memory cap exceeded")
    complete = len(commands) == 3 and all(c["exit_code"] == 0 for c in commands)
    if complete and (
        review["plan"] != plan_payload()
        or not audit["passed"]
        or audit["review_sha256"] != sha(canonical(review))
        or any(
            v[k] != expected for v in (review, audit) for k, expected in boundary_fields().items()
        )
        or audit["directional_rows"] != 64
        or audit["next_slice"] != review["next_slice"]
    ):
        raise ValueError("complete independent review binding differs")
    charge = sum(charges.values()) + 60
    peaks.append(peak_rss())
    if charge > 240 or max(peaks) > 1073741824:
        raise ValueError("whole read-only slice cap exceeded")
    return {
        "closed": True,
        "plan_sha256": plan_payload()["plan_sha256"],
        "charged_seconds": charge,
        "paid_reservation_seconds": 60,
        "peak_rss_bytes": max(peaks),
        "stage_charges": charges,
        "profile_sha256": hashes,
        "full_panel_review_complete": complete,
        "review_acceptance_passed": bool(complete and review["review_acceptance_passed"]),
        "original_fit_proxy_unchanged": review["original_fit_proxy_unchanged"]
        if complete
        else None,
        **boundary_fields(),
        "failed_attempts": sum(c["exit_code"] != 0 for c in commands),
        "next_slice": review["next_slice"] if complete else EVIDENCE_NEXT,
        "review_sha256": sha(canonical(review)) if review else None,
        "independent_audit_sha256": sha(canonical(audit)) if audit else None,
    }


def main(argv=None):
    started = perf_counter()
    args, root, output = arguments(argv)
    if not args.execute:
        print(canonical(plan_payload()).decode(), end="")
        return 0
    if (output / "resource_close.json").exists():
        raise ValueError("refuses to overwrite resource closure")
    revision = execution_release(output)
    check_inputs(root)
    values = [
        read(output, p) if (output / p).exists() else None
        for p in ("review.json", "independent_audit.json")
    ]
    commands = read(output, "audit_receipts/execution_commands.json")
    result = close_resources(output, commands, *values)
    result.update(
        source_revision=revision,
        closure_internal_charge_seconds=perf_counter() - started + 10,
        closure_internal_peak_rss_bytes=peak_rss(),
        execution_commands_sha256=sha(canonical(commands)),
    )
    result["peak_rss_bytes"] = max(
        result["peak_rss_bytes"], result["closure_internal_peak_rss_bytes"]
    )
    if (
        result["closure_internal_charge_seconds"] > 60
        or result["closure_internal_peak_rss_bytes"] > 1073741824
    ):
        raise ValueError("resource closure reservation exceeded")
    with (output / "resource_close.json").open("xb") as stream:
        stream.write(canonical(result))
    print(canonical(result).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
