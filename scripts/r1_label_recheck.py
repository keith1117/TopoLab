"""Observe the single registered label implicated by a sealed R1 timeout."""

import argparse
import base64
import hashlib
import json
import os
import resource
import subprocess
import sys
import tarfile
import time
from pathlib import Path

CAMPAIGN = Path("/Users/keith1117/Documents/TopoLab-data/input-cycle-20261123")
DATA = CAMPAIGN.parent
A1 = CAMPAIGN.with_name(CAMPAIGN.name + "-a1")
OLD = Path("/private/tmp/topolab-input-cycle-20261123")
NEW = OLD.with_name(OLD.name + "-a2")
PREVIOUS = "52be62d2d4526639bedc0ca63f75aa149da9c259"
ARCHIVE = "e1ebd26314a282894de81acd28d1733e66be07b061ba35b202ab54cbec044536"
SHA = "f182bf71f5edf86333d9908585083d1c0a07af98f65d8a72d181e1b35aca3874"
CASE = "tlcase-v1-0a490c9248cdfcd1a92a893f8b19a930ec4308db6da27a61deb3e475c57f8ac8"
RELATIVE = f"b3-v1-data/artifacts/label/{CASE}/{SHA}.json"
END = 1795576346212
START = 1795403546212
BUDGET = "9ab62a69584a1ec2179b7fb9bd13a7b23a5564bcd8413a34f5ecb5f99d3c848b"
PYTHON = (
    "/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python"
)


COMPILED_SHA = globals().get("COMPILED_SHA")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def sealed_item(wire):
    import io

    path = A1 / "formal-generated-controls-a1.tar.gz"
    peer = A1.with_name(A1.name + "-backup") / path.name
    raw = wire["read_private"](path)
    need(
        not path.samefile(peer) and raw == wire["read_private"](peer) and sha(raw) == ARCHIVE,
        "sealed A1 archive differs",
    )
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as archive:

        def get(name):
            member = archive.getmember(name)
            need(member.isfile() and 0 < member.size < 8 * 1024**2, "archive member cap/type")
            return json.load(archive.extractfile(member))

        failure = get("exporter-r1-failure.json")["source_failures"][0]
        registry = get("registry.json")
        proof = get("r0-proof.json")
    need(
        proof["source_count"] == 40
        and proof["source_registry_sha256"] == sha(wire["canonical"](registry)),
        "independent R0 registry differs",
    )
    [item] = [row for row in registry["labels"] if row["artifact"]["path"] == RELATIVE]
    need(
        item["artifact"] == dict(path=RELATIVE, sha256=SHA, byte_size=472469)
        and failure["path"] == RELATIVE
        and failure["expected_sha256"] == SHA
        and failure["stage"] == "bounded_read"
        and failure["attempt_ordinal"] == 35
        and failure["declared"] == failure["before"]
        and failure["returned_bytes"] is None,
        "registered failed label differs",
    )
    return item, failure["declared"]


def observe(reader, producer, item, anchor):
    trace = []
    original = reader._identity.__func__.__code__

    def record(frame, event, _arg):
        if event == "call" and frame.f_code is original and frame.f_locals.get("self") is reader:
            stat = frame.f_locals["value"]
            trace.append(
                dict(
                    stage=frame.f_locals["stage"],
                    flags=stat.st_flags,
                    blocks=stat.st_blocks,
                    monotonic_ns=time.monotonic_ns(),
                )
            )

    clock = time.monotonic_ns()
    previous = sys.getprofile()
    raw, error = None, None
    try:
        sys.setprofile(record)
        raw = producer.read_ref(
            reader, item["artifact"], 64 * producer.MIB, group="label", total=768 * producer.MIB
        )
        with reader.validation(RELATIVE):
            producer.label_views(producer.parse(raw), item)
        facts = reader.source_facts[RELATIVE]
        for stage in ("declared", "before", "after", "closing"):
            need(
                all(facts[stage][k] == anchor[k] for k in ("st_dev", "st_ino", "st_size")),
                "archived physical identity differs at " + stage,
            )
        need(
            [r["stage"] for r in trace] == ["declared", "before", "after", "closing"]
            and reader.attempts == [RELATIVE]
            and len(raw) == 472469
            and sha(raw) == SHA,
            "single-file actual incomplete",
        )
    except (ValueError, OSError) as exc:
        error = dict(type=type(exc).__name__, reason=str(exc), errno=getattr(exc, "errno", None))
    finally:
        sys.setprofile(previous)
    return dict(
        status="PASS" if error is None else "STOP",
        error=error,
        trace=trace,
        elapsed_ns=time.monotonic_ns() - clock,
        facts=reader.source_facts.get(RELATIVE),
        attempts=reader.attempts,
        source_observations=reader.source_observations,
        raw_base64=base64.b64encode(raw).decode("ascii") if raw is not None else None,
    )


def published_blob(repo, head, name):
    return subprocess.check_output(["git", "show", head + ":" + name], cwd=repo, timeout=15)


def published_module(repo, head, name):
    path = repo / name
    raw = path.read_bytes()
    need(raw == published_blob(repo, head, name), "checkout differs from published " + name)
    module = {"__file__": str(path), "__name__": "r1_label_diagnostic_module"}
    exec(compile(raw, str(path), "exec"), module)
    return module, sha(raw)


READER_SCRIPTS = (
    "scripts/full60_input_loader.py",
    "scripts/p17_m2_input_continuation.py",
    "scripts/p17_m2_registered_input.py",
    "scripts/p17_m2_input_export.py",
    "scripts/p17_m2_source_acquisition_control.py",
)


def verify_reader_sources(repo, head, bootstrap, loaded):
    pins = dict(bootstrap)
    for name in READER_SCRIPTS:
        pins[name] = loaded.get(str(repo / name))
    for name, compiled in pins.items():
        need(
            compiled == sha(published_blob(repo, head, name)),
            "executed reader differs from published " + name,
        )
    return pins


def run(slot):
    repo = NEW
    script = Path(__file__).resolve()
    need(
        Path.cwd() == repo
        and sys.flags.isolated
        and sys.executable == PYTHON
        and all(
            os.environ.get(k) == "1"
            for k in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        ),
        "exact diagnostic environment",
    )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo).decode().strip()
    need(
        subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=repo).decode().strip()
        == head
        and not subprocess.check_output(["git", "status", "--porcelain"], cwd=repo)
        and subprocess.check_output(["git", "branch", "--show-current"], cwd=repo).strip()
        == b"main"
        and slot == 2
        and head != PREVIOUS
        and script == repo / "scripts/r1_label_recheck.py",
        "published reader or observation entry differs",
    )
    wire_name = "scripts/staged_input_filer.py"
    entry_name = "scripts/cycle_r1_registered_input.py"
    self_name = "scripts/r1_label_recheck.py"
    need(COMPILED_SHA == sha(published_blob(repo, head, self_name)), "executed worker differs")
    wire, wire_sha = published_module(repo, head, wire_name)
    name = f"real-{slot:02}"
    backup = CAMPAIGN.with_name(CAMPAIGN.name + "-backup")

    def pair(filename):
        p, q = CAMPAIGN / filename, backup / filename
        raw = wire["read_private"](p)
        need(not p.samefile(q) and wire["read_private"](q) == raw, "diagnostic pair differs")
        return raw

    claim_raw = pair(name + "-claim.json")
    claim = json.loads(claim_raw)
    argv = ["/usr/bin/timeout", "-k", "2", "1190", PYTHON, "-I", str(script), "--slot", str(slot)]
    now = time.time_ns() // 1_000_000
    need(
        sha(pair("campaign-budget.json")) == claim["budget_sha256"] == BUDGET
        and claim
        == dict(
            schema="topolab.r1-label-claim.v1",
            slot=slot,
            argv=argv,
            repo=str(repo),
            source_main=head,
            worker_sha256=COMPILED_SHA,
            charge_FULL=1200,
            budget_sha256=BUDGET,
            failed_archive_sha256=ARCHIVE,
            path=RELATIVE,
            claimed_ms=claim["claimed_ms"],
        )
        and START <= claim["claimed_ms"] <= now
        and now + 1190_000 <= END,
        "single-file finite claim differs",
    )
    for folder in (CAMPAIGN, backup):
        wire["write_private"](
            folder / (name + "-entered.json"),
            wire["canonical"](dict(slot=slot, claim_sha256=sha(claim_raw), entered_ms=now)),
        )
    item, anchor = sealed_item(wire)
    entry, entry_sha = published_module(repo, head, entry_name)
    subject = entry["subject"]
    reg = subject.authority()["registration"]["formal"]
    ref = subject.registration_reference(
        "formal", reg["certificate_sha256"], reg["finalize_actual_sha256"]
    )
    plan = dict(
        execution_identity=subject.IDENTITY,
        source_identity_policy=subject.POLICY,
        scope=subject.control.FORMAL_SCOPE,
        source_root=str(DATA),
        binding=dict(strict23_registration=ref),
    )
    reader = subject.source_reader(
        plan,
        DATA,
        execution_identity=subject.producer.LOCAL_IDENTITY,
        source_identity_checks=True,
        source_identity_policy=subject.POLICY,
    )
    bootstrap = {self_name: COMPILED_SHA, wire_name: wire_sha, entry_name: entry_sha}
    loaded = sys.modules["full60_input_loader"].loaded_source_sha256
    pins = verify_reader_sources(repo, head, bootstrap, loaded)
    need(
        subject.loaded_source_sha256 == pins["scripts/p17_m2_registered_input.py"]
        and subject.control.loaded_source_sha256
        == pins["scripts/p17_m2_source_acquisition_control.py"],
        "profile-specific reader or control compilation differs",
    )
    output = observe(reader, subject.producer, item, anchor)
    need(verify_reader_sources(repo, head, bootstrap, loaded) == pins, "reader changed during read")
    ended = time.time_ns() // 1_000_000
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    need(
        type(rss) is int and 0 < rss <= 4 * 1024**3 and now <= ended <= min(END, now + 1190_000),
        "diagnostic resource bounds exceeded",
    )
    report = dict(
        schema="topolab.r1-label-recheck.v1",
        reader_source_sha256=pins,
        slot=slot,
        source_main=head,
        archive_sha256=ARCHIVE,
        worker_sha256=claim["worker_sha256"],
        started_ms=now,
        ended_ms=ended,
        rss_bytes=rss,
        claim_sha256=sha(claim_raw),
        anchor=anchor,
        **output,
    )
    raw = wire["canonical"](report)
    for folder in (CAMPAIGN, backup):
        wire["write_private"](folder / (name + "-report.json"), raw)
    print(
        wire["canonical"](
            dict(
                status=output["status"],
                slot=slot,
                report_sha256=sha(raw),
                own_future_return="NOT_CLAIMED",
            )
        ).decode(),
        end="",
    )
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slot", type=int, required=True, choices=[2])
    slot = parser.parse_args().slot
    path = Path(__file__).resolve()
    source = path.read_bytes()
    namespace = {
        "__name__": "r1_label_candidate",
        "__file__": str(path),
        "COMPILED_SHA": sha(source),
    }
    exec(compile(source, str(path), "exec"), namespace)
    raise SystemExit(namespace["run"](slot))
