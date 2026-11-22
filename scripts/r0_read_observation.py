"""Measure one registered R0 unit through the published reader. Store source bytes privately."""

import argparse
import base64
import hashlib
import json
import os
import resource
import runpy
import subprocess
import sys
import time
from pathlib import Path

E = Path("/Users/keith1117/Documents/TopoLab-data/r0-read-acceptance-20261122")
B = E.with_name(E.name + "-backup")
NEW = Path("/private/tmp/topolab-r0-read-20261122")
SOURCE = Path("/Users/keith1117/Documents/TopoLab-data")
UNIT = "b4-30-z-reflection-repair-v2/sentinel/reference/units/0011.json"
BUDGET = "149fe42c5df8849c49d3cb39b62004a8b0d7d82bf3ce1c7bca131f24f9c0b666"
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.r0-read-20261122.v1"
EXPECTED = "b75b1942e547a027744bc08f5b70a001cfc309804d00f04f983bc9236e774802"


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def pair(name, wire):
    primary, backup = E / name, B / name
    raw = wire["read_private"](primary)
    check(
        raw == wire["read_private"](backup) and not primary.samefile(backup),
        "observation pair differs",
    )
    return raw


def observe(reader):
    """Profile this reader's existing calls without reopening its source descriptor."""
    trace = []
    buffers = []
    origin = reader.read.__func__.__code__
    identity = reader._identity.__func__.__code__

    def record(frame, event, value):
        if frame.f_code is identity and event == "call" and frame.f_locals.get("self") is reader:
            st = frame.f_locals["value"]
            trace.append(
                dict(
                    stage=frame.f_locals["stage"],
                    mono_ns=time.monotonic_ns(),
                    flags=getattr(st, "st_flags", None),
                    blocks=st.st_blocks,
                )
            )
        if frame.f_code is origin and event == "return" and type(value) is bytes:
            buffers.append(value)

    started = time.time_ns()
    mono = time.monotonic_ns()
    previous = sys.getprofile()
    error = None
    try:
        sys.setprofile(record)
        packet = reader.packet(UNIT, 32768, total=32 * 1024**2)
        check(len(buffers) == 1 and canonical(packet) == buffers[0], "raw canonical unit differs")
        check(len(buffers[0]) == 490 and sha(buffers[0]) == EXPECTED, "registered unit differs")
    except (OSError, ValueError) as exc:
        error = dict(type=type(exc).__name__, reason=str(exc), errno=getattr(exc, "errno", None))
    finally:
        sys.setprofile(previous)
    return dict(
        read_start_ns=started,
        read_end_ns=time.time_ns(),
        read_elapsed_ns=time.monotonic_ns() - mono,
        status="COMPLETE" if error is None else "STOP",
        error=error,
        reader_facts=reader.source_facts.get(UNIT),
        source_observations=reader.source_observations,
        open_identity_trace=trace,
        raw_b64=base64.b64encode(buffers[0]).decode("ascii") if buffers else None,
        helper_records=getattr(reader, "claim_records", []),
    )


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", required=True, type=int, choices=range(1, 13))
    parser.add_argument("--purpose", required=True, choices=["candidate"])
    args = parser.parse_args()
    name = f"observation-{args.slot:02d}"
    repo = Path.cwd()
    check(
        repo == NEW
        and Path(__file__).resolve() == repo / "scripts/r0_read_observation.py"
        and sys.flags.isolated,
        "fixed isolated observation worker required",
    )
    wire = runpy.run_path(str(repo / "scripts/staged_input_filer.py"))
    claim_raw = pair(name + "-claim.json", wire)
    claim = json.loads(claim_raw)
    policy = pair("owner-budget-registration.json", wire)
    budget = json.loads(policy)
    check(
        sha(policy) == BUDGET
        and budget["start_ms"] <= claim["claimed_ms"] <= time.time_ns() // 10**6 < budget["end_ms"],
        "new observation scope",
    )
    check(
        claim["schema"] == "topolab.r0-read-claim.v1"
        and claim["slot"] == args.slot
        and claim["purpose"] == args.purpose
        and claim["relative_path"] == UNIT
        and claim["budget_sha256"] == BUDGET
        and claim["charge_FULL"] == 300
        and claim["worker_sha256"] == sha(Path(__file__).read_bytes())
        and claim["repo"] == str(repo)
        and claim["actor"] == "/root"
        and claim["argv"] == ["/usr/bin/timeout", "-k", "2", "290", sys.executable, "-I", *sys.argv]
        and all(
            os.environ.get(key) == "1"
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        ),
        "invalid one-file diagnostic claim",
    )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    check(
        head == claim["source_main"]
        and subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip() == head
        and not subprocess.check_output(["git", "status", "--porcelain"]),
        "published source changed",
    )
    # Claim consumption is exclusive even when a clock, IO or process return subsequently fails.
    entered = canonical(
        dict(slot=args.slot, claim_sha256=sha(claim_raw), entered_ns=time.time_ns())
    )
    for root in (E, B):
        wire["write_private"](root / (name + "-entered.json"), entered)
    subject = runpy.run_path(str(repo / "scripts/r0_registered_input.py"))["subject"]
    auth = subject.authority_raw()
    check(
        subject.IDENTITY == IDENTITY and sha(auth) == claim["authority_sha256"],
        "published authority differs from observation claim",
    )
    pin = subject.authority(auth)["registration"]["formal"]
    ref = subject.registration_reference(
        "formal", pin["certificate_sha256"], pin["finalize_actual_sha256"]
    )
    plan = dict(
        execution_identity=subject.IDENTITY,
        source_identity_policy=subject.POLICY,
        scope=subject.control.FORMAL_SCOPE,
        source_root=str(SOURCE),
        binding=dict(strict23_registration=ref),
    )
    reader = subject.source_reader(
        plan,
        SOURCE,
        execution_identity=subject.producer.LOCAL_IDENTITY,
        source_identity_checks=True,
        source_identity_policy=subject.POLICY,
    )
    bound = reader._registrations[UNIT]
    check(
        bound["sha256"] == EXPECTED and bound["byte_size"] == 490, "original registration differs"
    )
    result = observe(reader)
    result.update(
        schema="topolab.r0-read-observation.v1",
        slot=args.slot,
        purpose=args.purpose,
        execution_identity=IDENTITY,
        source_main=head,
        authority_sha256=sha(auth),
        budget_sha256=BUDGET,
        source_root=str(SOURCE),
        relative_path=UNIT,
        registration=bound,
        claim_sha256=sha(claim_raw),
        worker_sha256=sha(Path(__file__).read_bytes()),
        registration_sha256=pin["certificate_sha256"],
        runtime=subject.control.base().runtime(),
        rss_self_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )
    data = canonical(result)
    for root in (E, B):
        wire["write_private"](root / (name + "-receipt.json"), data)
    print(
        canonical(
            dict(
                schema="topolab.r0-read-return.v1",
                slot=args.slot,
                status=result["status"],
                receipt_sha256=sha(data),
                own_future_return="NOT_CLAIMED",
            )
        ).decode(),
        end="",
    )
    return int(result["status"] != "COMPLETE")


if __name__ == "__main__":
    raise SystemExit(main())
