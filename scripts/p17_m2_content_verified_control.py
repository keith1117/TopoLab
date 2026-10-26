"""Public content-verification preparation; formal entry is closed before path IO."""

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import stat
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IDENTITY = "topolab.v2.p17-m2-content-verified-input.v1"
SCOPE = "PUBLIC_SOFTWARE_FIXTURE_ONLY"
CAPS = {
    "independent-public-check": 300,
    "exporter-r0": 300,
    "independent-r0": 300,
    "exporter-r1": 1200,
    "independent-r1": 1200,
    "shared-closeout": 300,
}
METADATA_CAPS = {
    "final-filing": 180,
    "lease-release": 180,
    "public-consumer": 180,
    "reader-ack": 180,
}
READER_ROLE = "@READER_ROLE@"
THREADS = {
    key: "1"
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    )
}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
        + "\n"
    ).encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    need(spec and spec.loader, "missing implementation")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def physical(info):
    return {key: getattr(info, key) for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")}


def namespace_check(root, *, additional_bytes=0, additional_files=0, evidence=True):
    """Stat only this new public tree, including partial writes; never follow links."""
    count = size = evidence_count = evidence_size = 0
    stack = [(nofollow_directory(root), evidence)]
    try:
        while stack:
            descriptor, evidence = stack.pop()
            try:
                for name in os.listdir(descriptor):
                    info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                    child_evidence = evidence and name not in (
                        "public-source",
                        "content",
                        "backup-content",
                        "independent-public-fixture",
                    )
                    if stat.S_ISDIR(info.st_mode):
                        stack.append(
                            (
                                os.open(
                                    name,
                                    os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                    dir_fd=descriptor,
                                ),
                                child_evidence,
                            )
                        )
                    else:
                        need(
                            stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                            "NAMESPACE_ORDINARY_SINGLE_LINK_REQUIRED",
                        )
                        count += 1
                        size += info.st_size
                        if child_evidence:
                            evidence_count += 1
                            evidence_size += info.st_size
            finally:
                os.close(descriptor)
        need(count + additional_files <= 4096, "NAMESPACE_FILE_CAP")
        need(size + additional_bytes <= 2 * 1024**3, "NAMESPACE_BYTE_CAP")
        need(evidence_count + additional_files <= 512, "EVIDENCE_FILE_CAP")
        need(evidence_size + additional_bytes <= 256 * 1024**2, "EVIDENCE_BYTE_CAP")
        return dict(
            count=count, size=size, evidence_count=evidence_count, evidence_size=evidence_size
        )
    finally:
        for descriptor, _ in stack:
            os.close(descriptor)


def put(path, value):
    raw = canonical(value)
    root = next((p for p in path.parents if p.name.startswith("topolab-public-")), None)
    if root is not None:
        namespace_check(root, additional_bytes=len(raw), additional_files=1)
    parent = nofollow_directory(path.parent)
    try:
        fd = os.open(
            path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent
        )
        with os.fdopen(fd, "wb") as stream:
            need(stream.write(raw) == len(raw), "partial write")
            stream.flush()
            os.fsync(stream.fileno())
            identity = physical(os.fstat(stream.fileno()))
        os.fsync(parent)
        return identity
    finally:
        os.close(parent)


def public_root(root):
    # Lexical gate precedes any stat/open. Never inspect a proposed custody target.
    root = Path(root).absolute()
    need(
        root.name.startswith("topolab-public-")
        and ".." not in root.parts
        and (
            root.is_relative_to("/private/tmp")
            or root.is_relative_to("/private/var/folders")
            or root.is_relative_to("/tmp")
        ),
        "PUBLIC_ROOT_REQUIRED",
    )
    return root


def source_freeze():
    paths = sorted(
        [
            *Path("scripts").glob("p17_m2_*.py"),
            *Path("scripts").glob("p17_m2_*.js"),
            Path("docs/planning/p17_m2_content_verified_custody_protocol.json"),
            Path("docs/planning/p17_m2_content_verified_custody_proposal.json"),
            Path("docs/planning/p17_m2_input_export_preparation_proposal.json"),
        ]
    )
    return {str(p): sha((REPO / p).read_bytes()) for p in paths}


def runtime():
    return {
        "python": str(Path(sys.orig_argv[0]).resolve()),
        "orig_argv": sys.orig_argv,
        "python_sha256": sha(Path(sys.orig_argv[0]).resolve().read_bytes()),
        "isolated": sys.flags.isolated,
        "cwd": str(REPO),
        "platform": sys.platform,
        "os_release": platform.release(),
        "lock_sha256": sha((REPO / "uv.lock").read_bytes()),
        "threads": {k: os.environ.get(k) for k in THREADS},
    }


def nofollow_directory(path):
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in Path(path).absolute().parts[1:]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except OSError as error:
        os.close(fd)
        raise ValueError("nofollow public directory") from error


def private_backup_parent(root, relative):
    """Create descendants only through held no-follow private directory descriptors."""
    parts = Path(relative).parts
    need(
        parts
        and not Path(relative).is_absolute()
        and all(part not in (".", "..") for part in parts),
        "BACKUP_RELATIVE_PATH_REQUIRED",
    )
    descriptor = nofollow_directory(root)
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, mode=0o700, dir_fd=descriptor)
                os.fsync(descriptor)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            info = os.fstat(child)
            if info.st_uid != os.geteuid() or stat.S_IMODE(info.st_mode) != 0o700:
                os.close(child)
                raise ValueError("PRIVATE_BACKUP_PARENT_REQUIRED")
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def prepare(root, public_fault=None):
    root = public_root(root)
    parent = nofollow_directory(root.parent)
    try:
        os.mkdir(root.name, mode=0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    fixture = load("p17_m2_content_verified_public_fixture")
    checker = load("p17_m2_input_export_independent")
    contract, binding = fixture.create_sources(root / "public-source", checker)
    now = round(time.time(), 3)
    deadline = datetime.fromtimestamp(now + 4500, UTC).isoformat(timespec="milliseconds")
    plan = {
        "execution_identity": IDENTITY,
        "scope": SCOPE,
        "formal_authority": False,
        "public_fault": public_fault,
        "root": str(root),
        "public_source_identity": binding,
        "content_contract": contract,
        "contract_sha256": sha(
            (REPO / "docs/planning/p17_m2_content_verified_custody_protocol.json").read_bytes()
        ),
        "source_tree": source_freeze(),
        "runtime": runtime(),
        "role_order": list(CAPS),
        "roles": {r: {"argv": argv_for(root, "payload", "@PLAN_SHA256@", r)} for r in CAPS},
        "registered_reader_lease_sibling": "content.cooperative-reader.lease",
        "metadata_actions": {
            r: {"argv": argv_for(root, "payload", "@PLAN_SHA256@", r)} for r in METADATA_CAPS
        },
        "actor_activation_UTC_seconds": now,
        "actor_window_seconds": 4500,
        "actor_deadlines_UTC": {
            k: deadline.replace("+00:00", "Z") for k in ("exporter", "independent")
        },
    }
    put(root / "plan.json", plan)
    acquired = {
        "scope": "COOPERATIVE_REGISTERED_TOPOLAB_ONLY",
        "execution_identity": IDENTITY,
        "root": str(root / "content"),
        "state": "HELD",
        "version_id": None,
        "registered_readers": list(CAPS) + ["final-filing"],
        "acquired_UTC_seconds": time.time(),
        "acquired_monotonic": time.monotonic(),
    }
    put(root / "custody-acquired.json", acquired)
    lease_identity = put(root / "content.cooperative-reader.lease", acquired)
    put(root / "custody-lock-identity.json", lease_identity)
    return {"plan_sha256": sha(canonical(plan)), "scope": SCOPE, "formal_authority": False}


def read_json(path, cap=16 * 1024 * 1024):
    parent = nofollow_directory(Path(path).parent)
    try:
        fd = os.open(Path(path).name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
    finally:
        os.close(parent)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        need(0 < info.st_size <= cap and info.st_nlink == 1, "bounded ordinary record")
        raw = stream.read(cap + 1)
        need(len(raw) == info.st_size, "record short read")
    return json.loads(raw)


def checked(root, expected):
    root = public_root(root)
    namespace_check(root)
    plan = read_json(root / "plan.json")
    need(
        sha(canonical(plan)) == expected
        and plan["root"] == str(root)
        and plan["scope"] == SCOPE
        and plan["execution_identity"] == IDENTITY
        and plan["formal_authority"] is False,
        "public plan identity",
    )
    need(plan["source_tree"] == source_freeze(), "source freeze changed")
    actual = runtime()
    need(
        all(plan["runtime"][k] == actual[k] for k in actual if k != "orig_argv"),
        "runtime binding changed",
    )
    return root, plan


def predecessor(root, plan, role):
    need(role in plan["roles"] or role in plan["metadata_actions"], "unregistered role")
    order = plan["role_order"] + list(METADATA_CAPS)
    index = order.index(role)
    if role == "shared-closeout":
        attempted = [
            r
            for r in plan["role_order"][:-1]
            if (root / "receipts" / (r + "-pending.json")).exists()
        ]
        need(
            attempted
            and (
                not (root / "active.json").exists()
                or read_json(root / "active.json").get("role") == "shared-closeout"
            ),
            "shared needs closed nonempty prefix",
        )
        need(
            attempted == plan["role_order"][: len(attempted)],
            "shared requires exact attempt prefix",
        )
        for prior in attempted:
            events = read_json(root / (prior + "-events.json"))
            closed = closed_saved(root, sha(canonical(plan)), prior, events)
            need(
                closed.get("closed_attempt_verified") is True,
                "shared prefix cleanup/actual return UNKNOWN: " + str(closed.get("reason")),
            )
        return
    if index:
        previous = order[index - 1]
        need(
            (root / (previous + "-accepted.json")).is_file(),
            "predecessor actual external acceptance missing",
        )
        evidence = read_json(root / (previous + "-accepted.json"))
        try:
            checked_role = audit_saved(root, previous, evidence["raw_tool_events"])
            need(
                checked_role.get("full_role_evidence_accepted")
                or checked_role.get("metadata_evidence_accepted"),
                "predecessor not independently accepted",
            )
        except (KeyError, ValueError, OSError) as error:
            raise ValueError("predecessor acceptance invalid") from error


def payload(root, plan, role, *, adapter=None):
    transport = adapter or _PublicTransport()
    transport.predecessor(root, plan, role)
    active = read_json(root / "active.json")
    started = read_json(root / "receipts" / role / role / "started.json")
    need(
        active == {"role": role, "plan_sha256": sha(canonical(plan)), "status": "ACTIVE"}
        and started["role"] == role
        and started["software_only"] is True
        and started["argv"] == transport.argv_for(root, "payload", sha(canonical(plan)), role)
        and started["pid"] == os.getppid() == os.getpgrp(),
        "registered native launch/actual parent/group required",
    )
    if role == "shared-closeout" or (role not in CAPS and role != "final-filing"):
        return transport.payload_body(root, plan, role)
    try:
        transport.custody_hold(root)
    except Exception as error:
        return dict(
            status="STOP_NO_RETRY",
            scope=transport.scope,
            execution_identity=transport.identity,
            primary_failure=dict(
                stage="custody hold", type=type(error).__name__, reason=str(error)
            ),
            secondary_failures=[],
            formal_authority=False,
        )
    result = transport.payload_body(root, plan, role)
    try:
        transport.custody_hold(root)
    except Exception as error:
        detail = dict(stage="custody hold", type=type(error).__name__, reason=str(error))
        if result.get("status") == "STOP_NO_RETRY":
            result.setdefault("secondary_failures", []).append(detail)
            return result
        return dict(
            status="STOP_NO_RETRY",
            scope=transport.scope,
            execution_identity=transport.identity,
            primary_failure=detail,
            completed_payload=result,
            secondary_failures=[],
            formal_authority=False,
        )
    return result


def custody_hold(root):
    acquired = read_json(root / "custody-acquired.json")
    need(
        read_json(root / "content.cooperative-reader.lease") == acquired,
        "custody lease content changed",
    )
    parent = nofollow_directory(root)
    try:
        current = os.stat("content.cooperative-reader.lease", dir_fd=parent, follow_symlinks=False)
        need(
            physical(current) == read_json(root / "custody-lock-identity.json"),
            "custody lease physical identity changed",
        )
    finally:
        os.close(parent)


def payload_body(root, plan, role):
    if role == "independent-public-check":
        if str(plan.get("public_fault", "")).startswith("outer-watchdog"):
            fault = plan["public_fault"]
            started_path = root / "receipts" / role / role / "started.json"
            if fault == "outer-watchdog-missing-started":
                started_path.unlink()
            elif fault == "outer-watchdog-corrupt-started":
                started_path.write_bytes(b"{invalid\n")
            time.sleep(5)
        result = load("p17_m2_input_export_independent").public_check(
            root / "independent-public-fixture"
        )
        return dict(result, execution_identity=IDENTITY, scope=SCOPE, formal_authority=False)
    if role == "shared-closeout":
        return shared_payload(root, plan)
    if role in ("public-consumer", "reader-ack"):
        facts = evidence_json(read_json(root / "accepted-public-bundle.json"), decode=True)
        independent = load("p17_m2_content_verified_independent")
        certificate = independent.audit_public_certificate(
            facts["bundle"], trusted_tool_events=facts["events"]
        )
        if role == "reader-ack":
            wire = observed_wire(root, sha(canonical(plan)), "public-consumer")
            receipt = json.loads(wire["inner_evidence"]["log"])
            return certificate.acknowledge_returned_reader(
                receipt,
                {"wire": wire, "raw_tool_events": read_json(root / "public-consumer-events.json")},
            )
        lease = certificate.acquire_reader(READER_ROLE)
        consumer = load("p17_m2_verified_input").VerifiedInput(
            certificate, READER_ROLE, reader_lease=lease
        )
        count = total = 0
        for name in consumer.binding["role_views"][READER_ROLE]:
            if name.endswith(".json"):
                value = consumer.consume(name, consumer.helper.parse)
                del value
            else:
                consumer.consume(name, lambda raw: len(raw))
            count += 1
            total += consumer.members[name]["byte_size"]
        put(
            root / "public-consumption.json",
            dict(
                scope=SCOPE,
                execution_identity=IDENTITY,
                role=READER_ROLE,
                member_count=count,
                total_bytes=total,
                formal_authority=False,
                same_read_buffer=True,
            ),
        )
        return lease.pending_return()
    if role == "final-filing":
        closed = read_json(root / "closed.json")
        packet = role_results(root, plan)
        need(all(v["full_role_evidence_accepted"] for v in packet.values()), "shared frontier")
        proof = {
            "status": "PUBLIC_FILING_SNAPSHOT_WRITTEN",
            "scope": SCOPE,
            "execution_identity": IDENTITY,
            "plan_sha256": sha(canonical(plan)),
            "version_id": closed["version_id"],
            "manifest_sha256": sha(canonical(closed["manifest"])),
            "shared_packet_sha256": sha(canonical(packet)),
            "endpoint": "FINITE_SNAPSHOT_EXCLUDES_OWN_FUTURE_RETURN",
            "billing_charge": read_json(root / "final-filing-dispatch-charge.json"),
        }
        put(root / "filing-snapshot.json", proof)
        return proof
    if role == "lease-release":
        held = read_json(root / "backup-proof.json")["custody_lease"]
        acquired = read_json(root / "custody-acquired.json")
        need(read_json(root / "content.cooperative-reader.lease") == acquired, "lease replaced")
        last = read_json(root / "final-filing-events.json")[-1]
        need(
            last["complete"] is True
            and last["exit_code"] == 0
            and last["end_seconds"] <= time.time(),
            "actual last reader return missing",
        )
        parent = nofollow_directory(root)
        try:
            need(
                physical(
                    os.stat(
                        "content.cooperative-reader.lease", dir_fd=parent, follow_symlinks=False
                    )
                )
                == read_json(root / "custody-lock-identity.json"),
                "custody lock physical identity replaced",
            )
            os.unlink("content.cooperative-reader.lease", dir_fd=parent)
            os.fsync(parent)
        finally:
            os.close(parent)
        released = dict(
            held,
            state="RELEASED",
            released_UTC_seconds=time.time(),
            last_reader_return={
                "event_id": last["event_id"],
                "sha256": sha(canonical(last)),
                "end_seconds": last["end_seconds"],
            },
        )
        put(root / "lease-release.json", released)
        return released
    return content_step(root, plan, role)


class FailureJournal:
    def __init__(self, path):
        self.path = path

    def open(self, mode):
        need(mode == "ab", "failure journal append only")
        parent = nofollow_directory(self.path.parent)
        try:
            descriptor = os.open(
                self.path.name,
                os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW,
                0o600,
                dir_fd=parent,
            )
            info = os.fstat(descriptor)
            if info.st_nlink != 1 or info.st_uid != os.geteuid() or info.st_mode & 0o777 != 0o600:
                os.close(descriptor)
                raise OSError("private single-link journal required")
            return os.fdopen(descriptor, "ab")
        finally:
            os.close(parent)


def content_step(root, plan, role, *, adapter=None):
    transport = adapter or _PublicTransport()
    readers = []
    try:
        return _content_step(root, plan, role, readers, adapter=adapter)
    except Exception as error:
        context = getattr(error, "independent_read_failure", {})
        failure = dict(
            status="STOP_NO_RETRY",
            scope=transport.scope,
            execution_identity=transport.identity,
            role=role,
            error_type=type(error).__name__,
            reason=str(error),
            helper_identity_relabelled=False,
            attempted_source_paths=[],
            source_read_table=[],
            source_identities=[],
            source_failures=[],
            source_facts={},
            secondary_failures=[],
        )
        for reader in readers:
            failure["helper_execution_identity"] = reader.execution_identity
            failure["attempted_source_paths"].extend(reader.attempts)
            failure["source_read_table"].extend(reader.rows)
            failure["source_identities"].extend(reader.source_observations)
            failure["source_failures"].extend(reader.failures)
            failure["source_facts"].update(reader.source_facts)
        failure["independent_context"] = context
        for fact in failure["source_failures"]:
            if fact.get("recording_error"):
                failure["secondary_failures"].append(
                    dict(stage="source journal", reason=fact["recording_error"])
                )
        try:
            transport.put(root / (role + "-failure.json"), failure)
        except Exception as secondary:
            failure["secondary_failures"].append(
                dict(stage="failure record", type=type(secondary).__name__, reason=str(secondary))
            )
        return failure


def _content_step(root, plan, role, readers, *, adapter=None):
    transport = adapter or _PublicTransport()
    producer = load("p17_m2_input_export")
    local = load("p17_m2_local_input_version")
    independent = transport.independent()
    source = Path(plan["source_root"]) if adapter is not None else root / "public-source"
    contract = plan["content_contract"]
    if role == "exporter-r0":
        reader = producer.Reader(
            source,
            FailureJournal(root / (role + "-source-failure-rows.jsonl")),
            execution_identity=local.IDENTITY,
            source_identity_checks=True,
            source_identity_policy=getattr(transport, "source_identity_policy", None),
        )
        readers.append(reader)
        registry = producer.register(reader, contract)
        transport.put(root / "registry.json", registry)
        transport.put(root / "r0-source-rows.json", reader.source_observations)
        return {
            "scope": transport.scope,
            "execution_identity": transport.identity,
            "source_count": len(reader.rows),
            "helper_execution_identity": local.IDENTITY,
            "helper_identity_relabelled": False,
        }
    registry = read_json(root / "registry.json")
    if role == "independent-r0":
        proof = independent.independent_r0(
            source,
            contract,
            registry,
            read_json(root / "r0-source-rows.json"),
            plan["source_identity"]
            if adapter is not None and transport.scope != SCOPE and "source_identity" in plan
            else plan["public_source_identity"],
            **({"plan": plan} if adapter is not None else {}),
        )
        transport.put(root / "r0-proof.json", proof)
        return proof
    if role == "exporter-r1":
        content = (
            transport.new_content(root / "content", registry, plan["contract_sha256"])
            if adapter is not None
            else local.LocalContent(root / "content", registry, plan["contract_sha256"])
        )
        content.write("source_registry.json", producer.canonical(registry))
        reader = producer.Reader(
            source,
            FailureJournal(root / (role + "-source-failure-rows.jsonl")),
            execution_identity=local.IDENTITY,
            source_identity_checks=True,
            source_identity_policy=getattr(transport, "source_identity_policy", None),
        )
        readers.append(reader)
        producer.export(reader, registry, contract, content.root, local_content=content)
        closed = content.finish()
        descriptor = nofollow_directory(content.root)
        try:
            closed["root_identity"] = physical(os.fstat(descriptor))
        finally:
            os.close(descriptor)
        transport.put(root / "closed.json", closed)
        transport.put(root / "r1-source-rows.json", reader.source_observations)
        transport.put(
            root / "custody-version-bound.json",
            {
                "event": "VERSION_BOUND",
                "acquired_record_sha256": sha((root / "custody-acquired.json").read_bytes()),
                "version_id": closed["version_id"],
                "UTC_seconds": time.time(),
                "monotonic": time.monotonic(),
            },
        )
        return {
            "scope": transport.scope,
            "execution_identity": transport.identity,
            "source_count": len(reader.rows),
            "member_count": len(closed["manifest"]["members"]),
            "version_id": closed["version_id"],
            "helper_execution_identity": local.IDENTITY,
            "helper_identity_relabelled": False,
        }
    closed = read_json(root / "closed.json")
    need(role == "independent-r1", "unknown content role")
    proof = independent.independent_r1(
        source,
        root / "content",
        registry,
        read_json(root / "r1-source-rows.json"),
        closed,
        plan["contract_sha256"],
        plan["source_identity"]
        if adapter is not None and "source_identity" in plan
        else plan["public_source_identity"],
        **({"plan": plan} if adapter is not None else {}),
    )
    transport.put(root / "r1-proof.json", proof)
    return proof


def shared_payload(root, plan, *, adapter=None):
    transport = adapter or _PublicTransport()
    context = {
        "copied_members": [],
        "source_read_table": [],
        "source_identities": [],
        "source_failures": [],
        "source_facts": {},
        "secondary_failures": [],
    }
    try:
        context["held_lease"] = read_json(root / "custody-acquired.json")
        context["billing_reservation"] = read_json(root / "ledger-reservation.json")
        context["dispatch_charges"] = [
            read_json(root / (r + "-dispatch-charge.json"))
            for r in plan["role_order"]
            if (root / (r + "-dispatch-charge.json")).exists()
        ]
        context["primary_stop"] = (
            read_json(root / "STOP.json") if (root / "STOP.json").exists() else None
        )
        custody_hold(root)
        result = (
            transport.backup_failed_prefix(root, plan, context)
            if context["primary_stop"]
            else transport.backup_content(root, plan, context)
        )
        custody_hold(root)
        return result
    except Exception as error:
        failure = {
            "status": "STOP_NO_RETRY",
            "scope": transport.scope,
            "execution_identity": transport.identity,
            "formal_authority": False,
            "input_version_accepted": False,
            "primary_failure": {"type": type(error).__name__, "reason": str(error)},
            "shared_context": context,
            "independent_context": getattr(error, "independent_read_failure", {}),
            "secondary_failures": [],
        }
        try:
            transport.put(root / "shared-payload-failure.json", failure)
        except Exception as secondary:
            failure["secondary_failures"].append(
                dict(
                    stage="shared failure record",
                    type=type(secondary).__name__,
                    reason=str(secondary),
                )
            )
        return failure


def backup_failed_prefix(root, plan, context, *, adapter=None):
    transport = adapter or _PublicTransport()
    """One reserved closeout, only explicitly inventoried NEW closed-prefix files."""
    backup = transport.backup_prefix_root(plan) if adapter is not None else root / "backup-prefix"
    backup.mkdir(mode=0o700)
    excluded = {"public-source", "independent-public-fixture", "backup-prefix"}
    members = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        relative = Path(directory).relative_to(root)
        if relative == Path("."):
            dirs[:] = sorted(d for d in dirs if d not in excluded)
        if relative.parts[:1] == ("receipts",):
            dirs[:] = [d for d in dirs if d != "shared-closeout"]
        for name in sorted(files):
            path = (relative / name).as_posix()
            if (
                relative == Path("receipts") and name.startswith("shared-closeout-")
            ) or name == "active.json":
                continue
            members.append(path)
    members.append("failed-prefix-inventory.json")
    members.sort()
    transport.put(
        root / "failed-prefix-inventory.json",
        {
            "paths": members,
            "scope": transport.scope,
            "frozen_UTC_seconds": time.time(),
            "future_mutable_shared_files_excluded": True,
        },
    )
    context["frozen_paths"] = members
    producer = load("p17_m2_input_export")
    reader = producer.Reader(
        root, execution_identity=producer.LOCAL_IDENTITY, source_identity_checks=True
    )
    rows = context["copied_members"]
    context.update(
        source_read_table=reader.rows,
        source_identities=reader.source_observations,
        source_failures=reader.failures,
        source_facts=reader.source_facts,
    )
    for name in members:
        raw = reader.read(name, 64 * 1024**2, group="new-prefix", total=512 * 1024**2)
        if adapter is not None:
            transport.namespace_check(
                root, additional_bytes=len(raw), additional_files=1, additional_evidence=False
            )
        destination = backup / name
        descriptor = private_backup_parent(backup, name)
        try:
            fd = os.open(
                destination.name,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o600,
                dir_fd=descriptor,
            )
            with os.fdopen(fd, "wb") as stream:
                need(stream.write(raw) == len(raw), "prefix backup short write")
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        rows.append(
            dict(
                path=name,
                byte_size=len(raw),
                sha256=sha(raw),
                identity=reader.source_observations[-1],
            )
        )
    proof = transport.independent().independent_prefix_backup(
        root, backup, rows, **({"plan": plan} if adapter is not None else {})
    )
    transport.put(root / "failed-prefix-backup-proof.json", proof)
    return dict(
        status="STOP_NO_RETRY",
        scope=transport.scope,
        execution_identity=transport.identity,
        primary_stop=read_json(root / "STOP.json"),
        failed_prefix_backup=proof,
        input_version_accepted=False,
        formal_authority=False,
    )


def backup_content(root, plan, context, *, adapter=None):
    transport = adapter or _PublicTransport()
    local = load("p17_m2_local_input_version")
    producer = load("p17_m2_input_export")
    registry, closed = read_json(root / "registry.json"), read_json(root / "closed.json")
    backup_root = Path(plan["backup_root"]) if adapter is not None else root / "backup-content"
    backup = (
        transport.new_content(backup_root, registry, plan["contract_sha256"])
        if adapter is not None
        else local.LocalContent(backup_root, registry, plan["contract_sha256"])
    )
    reader = producer.Reader(
        root / "content", execution_identity=local.IDENTITY, source_identity_checks=True
    )
    context.update(
        source_read_table=reader.rows,
        source_identities=reader.source_observations,
        source_failures=reader.failures,
        source_facts=reader.source_facts,
    )
    identities = {r["path"]: r for r in closed["local_identity_rows"]}
    for member in closed["manifest"]["members"]:
        kind, each, total = backup.allowed[member["path"]]
        raw = reader.read(
            member["path"],
            each,
            expected=member["sha256"],
            size=member["byte_size"],
            group=kind,
            total=total,
        )
        need(reader.source_observations[-1] == identities[member["path"]], "backup source identity")
        backup.write(member["path"], raw)
        context["copied_members"].append(member)
    copied = backup.finish()
    need(copied["version_id"] == closed["version_id"], "backup version differs")
    proof = transport.independent().independent_backup(
        root / "content",
        backup.root,
        closed,
        registry,
        plan["contract_sha256"],
        **({"plan": plan} if adapter is not None else {}),
    )
    acquired = read_json(root / "custody-acquired.json")
    bound = read_json(root / "custody-version-bound.json")
    need(
        bound["acquired_record_sha256"] == sha(canonical(acquired))
        and bound["version_id"] == closed["version_id"],
        "custody version chain",
    )
    proof["custody_lease"] = dict(acquired, version_id=closed["version_id"])
    proof["custody_log"] = [acquired, bound]
    proof["billing_ledger"] = {
        "reservation": read_json(root / "ledger-reservation.json"),
        "dispatch_charges": [
            read_json(root / (r + "-dispatch-charge.json")) for r in plan["role_order"]
        ],
        "first_dispatch_launch_UTC_seconds": read_json(
            root / "receipts" / (plan["role_order"][0] + "-supervisor.json")
        )["launched_UTC_seconds"],
    }
    transport.put(root / "backup-proof.json", proof)
    return proof


def role_results(root, plan):
    return {
        role: audit_saved(root, role, read_json(root / (role + "-events.json")))
        for role in plan["role_order"]
    }


def bind(root, plan, plan_sha, role, *, adapter=None):
    transport = adapter or _PublicTransport()
    result = None
    packet = None
    try:
        events = read_json(root / (role + "-events.json"))
        result = transport.audit_saved(root, role, events)
        if role == "shared-closeout":
            packet = {
                "scope": transport.scope,
                "execution_identity": transport.identity,
                "plan_sha256": plan_sha,
                "status": "SEALED_HANDOFF_PENDING_INDEPENDENT_FILING",
                "role_results": {},
                "raw_packets": {},
                "secondary_failures": [],
            }
            for prior in plan["role_order"]:
                try:
                    raw = read_json(root / "receipts" / (prior + "-wire.json"))
                    raw_events = read_json(root / (prior + "-events.json"))
                    packet["raw_packets"][prior] = dict(wire=raw, raw_tool_events=raw_events)
                    packet["role_results"][prior] = transport.audit_saved(root, prior, raw_events)
                except Exception as error:
                    packet["status"] = "STOP_NO_RETRY"
                    packet["secondary_failures"].append(
                        dict(
                            role=prior,
                            type=type(error).__name__,
                            reason=str(error),
                            unavailable="UNKNOWN_NOT_ZERO",
                        )
                    )
            transport.put(root / "shared-packet.json", packet)
        transport.put(
            root / (role + "-accepted.json"), {"raw_tool_events": events, "result": result}
        )
    except Exception as error:
        # Filing failure cannot erase an already independently measured result.
        if result is None:
            result = dict(
                role=role,
                execution_identity=transport.identity,
                frozen_FULL_seconds=CAPS.get(role, 180 if role == "final-filing" else None),
                known_cost_lower_bound_seconds=CAPS.get(
                    role, 180 if role == "final-filing" else None
                ),
                missing_evidence_cost="UNKNOWN_NOT_ZERO",
                secondary_failures=[],
            )
        detail = dict(stage="bind persistence", type=type(error).__name__, reason=str(error))
        if result.get("primary_failure") is None:
            result.update(
                primary_failure=detail, reason=str(error), error_type=type(error).__name__
            )
        else:
            result.setdefault("secondary_failures", []).append(detail)
        result.update(
            status="STOP_NO_RETRY",
            full_role_evidence_accepted=False,
            metadata_evidence_accepted=False,
        )
        if packet is not None:
            result["unfiled_shared_packet"] = packet
    finally:
        try:
            clearable = bool(
                result
                and (
                    result.get("full_role_evidence_accepted")
                    or result.get("metadata_evidence_accepted")
                )
            )
            if not clearable:
                events = read_json(root / (role + "-events.json"))
                closed = transport.closed_saved(root, plan_sha, role, events)
                clearable = closed.get("closed_attempt_verified") is True
                if not clearable and result is not None:
                    result["cleanup_acceptance"] = closed
            if clearable:
                (root / "active.json").unlink(missing_ok=True)
        except Exception as error:
            if result is not None:
                result.setdefault("secondary_failures", []).append(
                    dict(stage="active cleanup", type=type(error).__name__, reason=str(error))
                )
    if not (result.get("full_role_evidence_accepted") or result.get("metadata_evidence_accepted")):
        if not (root / "STOP.json").exists():
            try:
                transport.put(root / "STOP.json", result)
            except Exception as error:
                result.setdefault("secondary_failures", []).append(
                    dict(stage="STOP record", type=type(error).__name__, reason=str(error))
                )
    return result


def closed_saved(root, plan_sha, role, events):
    wire = observed_wire(root, plan_sha, role)
    return load("p17_m2_content_verified_independent").check_closed_attempt(
        wire,
        raw_tool_events=events,
        expected_role=role,
        expected_plan_sha256=plan_sha,
        expected_argv=argv_for(root, "payload", plan_sha, role),
    )


class _PublicTransport:
    """Fixed public defaults; explicit adapters reuse native transport only."""

    identity = IDENTITY
    scope = SCOPE
    result_windows = (("exporter", 7200), ("independent", 3600))

    def independent(self):
        return load("p17_m2_content_verified_independent")

    def __getattr__(self, name):
        if name in {
            "argv_for",
            "put",
            "native_module",
            "namespace_check",
            "predecessor",
            "audit_saved",
            "closed_saved",
            "resource_evidence",
            "backup_content",
            "backup_failed_prefix",
            "payload_body",
            "custody_hold",
        }:
            return globals()[name]
        raise AttributeError(name)


def resource_evidence(root, plan_sha, role, *, tolerate_missing=False, adapter=None):
    transport = adapter or _PublicTransport()
    folder = root / "receipts" / role / role
    failures = []

    def take(stage, read):
        try:
            return read()
        except Exception as error:
            if not tolerate_missing:
                raise
            failures.append(dict(stage=stage, type=type(error).__name__, reason=str(error)))
            return None

    record = take("inner resource evidence", lambda: read_json(folder / "command.json"))
    inner = None
    if record is not None:
        inner = {
            "record": record,
            "profile": take(
                "inner resource evidence", lambda: (folder / "command.time").read_bytes()
            ),
            "log": take("inner resource evidence", lambda: (folder / "command.log").read_bytes()),
            "helper_profiles": {},
            "expected_role": role,
            "expected_argv": transport.argv_for(root, "payload", plan_sha, role),
            "platform": sys.platform,
        }

        def read_helpers():
            for helper in record["helpers"]:
                name = helper["profile"]
                raw = take(
                    "inner resource evidence", lambda name=name: (folder / name).read_bytes()
                )
                if raw is not None:
                    inner["helper_profiles"][name] = raw

        take("inner resource evidence", read_helpers)
    outer = take(
        "outer resource evidence",
        lambda: (root / "receipts" / (role + "-controller.time")).read_bytes(),
    )
    result = dict(
        inner_evidence=inner,
        native_profiles={"outer-controller": outer} if outer is not None else {},
    )
    if tolerate_missing:
        result["resource_read_failures"] = failures
    return result


def audit_saved(root, role, events):
    packet = read_json(root / "receipts" / (role + "-wire.json"))
    independent = load("p17_m2_content_verified_independent")
    resources = resource_evidence(
        root, packet["pending"]["plan_sha256"], role, tolerate_missing=True
    )
    failures = resources.pop("resource_read_failures")
    if role in METADATA_CAPS and role != "final-filing":
        wire = dict(packet, **resources)
        result = independent.audit_metadata(
            wire,
            raw_tool_events=events,
            plan_sha256=packet["pending"]["plan_sha256"],
            expected_argv=argv_for(root, "payload", packet["pending"]["plan_sha256"], role),
            expected_role=role,
        )
    else:
        result = independent.audit_role(
            packet["pending"],
            packet["completion"],
            raw_tool_events=events,
            expected_role=role,
            expected_plan_sha256=packet["pending"]["plan_sha256"],
            **resources,
        )
    result.setdefault("secondary_failures", []).extend(failures)
    return result


def argv_for(root, mode, plan_sha, role):
    args = [
        str(Path(sys.orig_argv[0]).resolve()),
        "-I",
        str(Path(__file__).resolve()),
        mode,
        "--root",
        str(root),
        "--plan-sha",
        plan_sha,
        "--role",
        role,
    ]
    if role in ("public-consumer", "reader-ack"):
        args += ["--reader-role", READER_ROLE]
    return args


def role_cap(role):
    return CAPS[role] if role in CAPS else METADATA_CAPS[role]


def native_module(root=None):
    load("p17_m2_homotopy")
    native = load("p17_m2_resource_control")
    if root is not None:
        snapshot = native._snapshot

        def bounded_snapshot(*args, **kwargs):
            # Reserve the full failure tail before another sampler can add files.
            namespace_check(root, additional_bytes=4 * 1024**2, additional_files=16)
            return snapshot(*args, **kwargs)

        native._snapshot = bounded_snapshot
        native.atomic_new = put
    return native


def supervise(root, plan, plan_sha, role, *, adapter=None):
    transport = adapter or _PublicTransport()
    import resource
    import subprocess

    transport.predecessor(root, plan, role)
    need(not (root / "STOP.json").exists() or role == "shared-closeout", "STOP_NO_RETRY")
    folder = root / "receipts"
    folder.mkdir(mode=0o700, exist_ok=True)
    pending = {
        k: plan[k]
        for k in ("actor_activation_UTC_seconds", "actor_window_seconds", "actor_deadlines_UTC")
    }
    pending.update(
        execution_identity=transport.identity,
        role=role,
        plan_sha256=plan_sha,
        frozen_FULL_seconds=role_cap(role) if role in CAPS or role == "final-filing" else None,
        clock_domain="functions.exec.Date.now.UTC-seconds",
        clock_resolution_seconds=0.001,
        status="PENDING_BEFORE_DISPATCH",
        external_argv=[
            transport.argv_for(root, m, plan_sha, role) for m in ("supervise", "record")
        ],
    )
    if role == "final-filing":
        frontier = transport.audit_saved(
            root, "shared-closeout", read_json(root / "shared-closeout-events.json")
        )["T1"]
        pending["result_start_UTC_seconds"] = frontier
        pending["result_deadlines_UTC"] = {
            k: datetime.fromtimestamp(frontier + seconds, UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
            for k, seconds in transport.result_windows
        }
    transport.put(folder / (role + "-pending.json"), pending)
    if role in CAPS:
        now = time.time()
        remaining = sum(CAPS[r] for r in plan["role_order"][plan["role_order"].index(role) :])
        deadline = plan["actor_activation_UTC_seconds"] + 4500
        need(
            now >= plan["actor_activation_UTC_seconds"] and deadline - now >= remaining + 240 + 360,
            "remaining full sequence/coordination/seal window unavailable",
        )
    # Native timer's actual exit is observed by wait4; supervisor exit is external.
    if not (root / "ledger-reservation.json").exists():
        transport.put(
            root / "ledger-reservation.json",
            {
                "shared_reserved_FULL_seconds": 300,
                "role_FULL_seconds": CAPS,
                "refunds_allowed": False,
                "scope": transport.scope,
                "reserved_UTC_seconds": time.time(),
                "execution_identity": transport.identity,
                "plan_sha256": plan_sha,
            },
        )
    transport.put(root / "active.json", {"role": role, "plan_sha256": plan_sha, "status": "ACTIVE"})
    transport.put(
        root / (role + "-dispatch-charge.json"),
        {
            "role": role,
            "frozen_FULL_seconds": role_cap(role)
            if role in CAPS or role == "final-filing"
            else None,
            "charged_FULL_seconds": 0
            if role == "shared-closeout"
            else (role_cap(role) if role in CAPS or role == "final-filing" else None),
            "charged_UTC_seconds": time.time(),
            "execution_identity": transport.identity,
            "plan_sha256": plan_sha,
            "scope": transport.scope,
            "shared_reservation_sha256": sha((root / "ledger-reservation.json").read_bytes()),
        },
    )
    native = transport.native_module()
    command = transport.argv_for(root, "run", plan_sha, role)
    profile = folder / (role + "-controller.time")
    started = time.monotonic()
    launched_UTC_seconds = time.time()
    with (folder / (role + "-controller.log")).open("xb") as stream:
        child = subprocess.Popen(
            native._timed(command, profile),
            cwd=REPO,
            stdout=stream,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        child.native_started = started
        watchdog_cleanup = None
        observed, watchdog_helper, failures = [], None, []
        descendant_groups = []
        try:
            while native._native_poll(child) is None:
                if time.monotonic() - started > (
                    1
                    if str(plan.get("public_fault", "")).startswith("outer-watchdog")
                    else role_cap(role) - 5
                ):
                    transport.namespace_check(
                        root, additional_files=16, additional_bytes=4 * 1024**2
                    )
                    observed, watchdog_helper = native._snapshot(
                        folder, "watchdog-" + role, child.pid
                    )
                    child.registered_command_pids = tuple(
                        r["pid"]
                        for r in observed
                        if r["parent"] == child.pid and r["pgid"] == child.pid
                    )
                    # started.json is evidence, never the only cleanup registry.
                    # The sampler contains only this still-owned launch's tree.
                    try:
                        inner_started = read_json(folder / role / role / "started.json")
                        need(
                            inner_started["argv"]
                            == transport.argv_for(root, "payload", plan_sha, role)
                            and inner_started["pgid"] == inner_started["pid"],
                            "watchdog registered inner identity unknown",
                        )
                    except Exception as error:
                        failures.append(
                            dict(
                                stage="inner started", type=type(error).__name__, reason=str(error)
                            )
                        )
                    break
                time.sleep(0.01)
        except Exception as error:
            failures.append(
                dict(stage="outer watchdog", type=type(error).__name__, reason=str(error))
            )
        finally:
            if getattr(child, "timer_native_exit", None) is None or observed or failures:
                import signal

                for pgid in sorted({r["pgid"] for r in observed} - {child.pid}):
                    rows = [r for r in observed if r["pgid"] == pgid]
                    item = dict(
                        pgid=pgid,
                        observed_pids=sorted(r["pid"] for r in rows),
                        signals=[],
                        observations=[],
                        group_gone=None,
                    )
                    began = time.monotonic()
                    # Signal only actually observed descendants while the owned
                    # outer timer is still alive; never use an arbitrary PID file.
                    if native._native_poll(child) is None:
                        for sig in (signal.SIGTERM, signal.SIGKILL):
                            for row in rows:
                                if row["pid"] == pgid:
                                    continue  # let the timer reap its command first
                                try:
                                    os.kill(row["pid"], sig)
                                    item["signals"].append(sig.name + "_OBSERVED_COMMAND")
                                except ProcessLookupError:
                                    pass
                                except PermissionError:
                                    item["signals"].append("EPERM_OBSERVED_COMMAND")
                            time.sleep(0.05)
                            try:
                                os.killpg(pgid, sig)
                                item["signals"].append(sig.name)
                            except ProcessLookupError:
                                break
                            except PermissionError:
                                item["signals"].append("EPERM_GROUP_SIGNAL")
                    while True:
                        try:
                            os.killpg(pgid, 0)
                            gone = False
                        except ProcessLookupError:
                            gone = True
                        except PermissionError:
                            gone = None
                        elapsed = time.monotonic() - began
                        item["observations"].append(dict(elapsed_seconds=elapsed, group_gone=gone))
                        item["group_gone"] = gone
                        if gone is not False or elapsed >= 4.9:
                            break
                        time.sleep(0.01)
                    descendant_groups.append(item)
                # Even namespace, sampler or started-record errors must close the
                # outer owned launch and preserve its actual wait4, never bypass it.
                try:
                    watchdog_cleanup = dict(
                        native._terminate(child.pid, child),
                        helper=watchdog_helper,
                        observed=observed,
                        descendant_groups=descendant_groups,
                        secondary_failures=failures,
                    )
                except Exception as error:
                    failures.append(
                        dict(
                            stage="outer termination", type=type(error).__name__, reason=str(error)
                        )
                    )
                    watchdog_cleanup = dict(
                        group_gone=None,
                        helper=watchdog_helper,
                        observed=observed,
                        descendant_groups=descendant_groups,
                        secondary_failures=failures,
                    )
    actual_exit = getattr(child, "timer_native_exit", None)
    measured = (
        actual_exit["native"]
        if actual_exit is not None
        else dict(wall_seconds=None, user_seconds=None, system_seconds=None, rss_bytes=None)
    )
    rss = measured["rss_bytes"]
    result = {
        "pid": child.pid,
        "launched_UTC_seconds": launched_UTC_seconds,
        "statistics_source": "os.wait4"
        if actual_exit is not None
        else "UNKNOWN_NATIVE_CONTROLLER_EXIT",
        "wall_source": "controller_monotonic_observed" if actual_exit is not None else "UNKNOWN",
        "exit_code": child.returncode,
        "rss_unit": "bytes" if sys.platform == "darwin" else "KiB*1024",
        "native": {
            "wall_seconds": measured["wall_seconds"],
            "user_seconds": measured["user_seconds"],
            "system_seconds": measured["system_seconds"],
            "rss_bytes": rss,
        },
        "watchdog_cleanup": watchdog_cleanup,
        "supervisor_pid": os.getpid(),
        "supervisor_rss": native._rss_self(),
    }
    transport.put(folder / (role + "-supervisor.json"), result)
    result["supervisor_rss_final"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) * (
        1 if sys.platform == "darwin" else 1024
    )
    transport.put(folder / (role + "-last-rss.json"), result)
    return {"status": "PENDING_EXTERNAL_EXIT", "controller_exit": child.returncode}


def collect(root, plan_sha, role, *, adapter=None):
    transport = adapter or _PublicTransport()
    folder = root / "receipts"
    folder.mkdir(mode=0o700, exist_ok=True)
    native = transport.native_module()
    own = {
        "pid": os.getpid(),
        "kind": "self_high_water",
        "statistics_source": "resource.getrusage",
        "rss_unit": "bytes",
        "phases": ["preflush", "postflush"],
        "samples_bytes": [native._rss_self(), native._rss_self()],
    }
    pending, failures = {}, []
    try:
        pending = read_json(folder / (role + "-pending.json"))
    except (ValueError, OSError, KeyError, TypeError) as error:
        failures.append({"stage": "pending", "type": type(error).__name__, "reason": str(error)})
    completion = dict(
        pending,
        pending_sha256=sha(canonical(pending)),
        status="PENDING_EXTERNAL_EXIT",
        domain_status="UNKNOWN",
        resource_components=[own],
        final_serializer_pid=os.getpid(),
        cleanup={"group_gone": None},
        primary_failure=None,
        secondary_failures=failures,
    )
    packet = {"pending": pending, "completion": completion}
    try:
        need(not failures, "UNKNOWN_MISSING_PENDING")
        sup = read_json(folder / (role + "-supervisor.json"))
        completion["observed_supervisor"] = sup
        last = read_json(folder / (role + "-last-rss.json"))
        inner = read_json(folder / role / role / "command.json")
        outer_raw = (folder / (role + "-controller.time")).read_bytes()
        completion.update(
            domain_status="PASS"
            if sup["exit_code"] == inner["exit_code"] == 0 and sup.get("watchdog_cleanup") is None
            else "STOP",
            cleanup=inner["cleanup"],
        )
        if completion["domain_status"] == "STOP":
            completion["primary_failure"] = {
                "stage": "payload/controller",
                "type": "ExitCode",
                "reason": str(inner["exit_code"]),
            }
        raw_evidence = transport.resource_evidence(root, pending["plan_sha256"], role)
        inner_evidence = raw_evidence["inner_evidence"]
        completion["native_evidence_hashes"] = {
            "inner_record_canonical_sha256": sha(canonical(inner_evidence["record"])),
            "inner_profile_sha256": sha(inner_evidence["profile"]),
            "inner_log_sha256": sha(inner_evidence["log"]),
            "helper_profiles_sha256": {
                k: sha(v) for k, v in inner_evidence["helper_profiles"].items()
            },
            "outer_profiles_sha256": {
                k: sha(v) for k, v in raw_evidence["native_profiles"].items()
            },
        }
        completion["resource_components"] = [
            {
                "pid": inner["controller_pid"],
                "kind": "native_profile",
                "profile": "outer-controller",
                "profile_sha256": sha(outer_raw),
                "platform": sys.platform,
                "actual_exit_code": sup["exit_code"],
            },
            {"pid": sup["pid"], "kind": "wait4", "platform": sys.platform, "record": sup},
            {
                "pid": sup["supervisor_pid"],
                "kind": "self_high_water",
                "statistics_source": "resource.getrusage",
                "rss_unit": "bytes",
                "phases": ["preflush", "postflush"],
                "samples_bytes": [sup["supervisor_rss"], last["supervisor_rss_final"]],
            },
            own,
        ]
    except (ValueError, OSError, KeyError, TypeError) as error:
        completion["status"] = "FAILED_INTERNAL_COMPLETION"
        completion["secondary_failures"].append(
            {"stage": "collect", "type": type(error).__name__, "reason": str(error)}
        )
    # Full failure packet retained first; bounded stdout is never evidence trimming for PASS.
    collector = folder / (role + "-collector.json")
    try:
        identity = transport.put(collector, packet)
        packet["full_collector_record"] = {
            "path": str(collector.relative_to(root)),
            "byte_size": identity["st_size"],
            "sha256": sha(canonical(packet)),
        }
    except Exception as error:
        completion["status"] = "FAILED_INTERNAL_COMPLETION"
        completion["domain_status"] = "STOP"
        completion["secondary_failures"].append(
            dict(stage="collector write", type=type(error).__name__, reason=str(error))
        )
        packet["full_collector_record"] = {
            "path": str(collector.relative_to(root)),
            "byte_size": None,
            "sha256": None,
            "unavailable": "UNKNOWN_NOT_ZERO",
        }
    own["samples_bytes"][1] = native._rss_self()
    raw = canonical(packet)
    if len(raw) > 32768:
        packet = {
            "pending": pending,
            "completion": dict(
                completion,
                status="FAILED_INTERNAL_COMPLETION",
                domain_status="STOP",
                resource_components=[own],
                secondary_failures=completion["secondary_failures"]
                + [{"stage": "wire", "reason": "WIRE_SIZE_STOP"}],
            ),
            "full_collector_record": packet["full_collector_record"],
        }
    need(len(canonical(packet)) <= 32768, "WIRE_SIZE_STOP")
    try:
        transport.put(folder / (role + "-wire.json"), packet)
    except Exception as error:
        packet["completion"]["status"] = "FAILED_INTERNAL_COMPLETION"
        packet["completion"]["domain_status"] = "STOP"
        packet["completion"]["secondary_failures"].append(
            dict(stage="wire write", type=type(error).__name__, reason=str(error))
        )
    return packet


def evidence_json(value, *, decode=False):
    import base64

    if decode and isinstance(value, dict) and set(value) == {"$bytes_base64"}:
        return base64.b64decode(value["$bytes_base64"], validate=True)
    if type(value) is bytes:
        return {"$bytes_base64": base64.b64encode(value).decode("ascii")}
    if isinstance(value, dict):
        return {k: evidence_json(v, decode=decode) for k, v in value.items()}
    if isinstance(value, list):
        return [evidence_json(v, decode=decode) for v in value]
    return value


def observed_wire(root, plan_sha, role):
    packet = read_json(root / "receipts" / (role + "-wire.json"))
    return dict(packet, **resource_evidence(root, plan_sha, role))


def public_bundle(root, plan, plan_sha):
    closed = read_json(root / "closed.json")
    roles = {r: observed_wire(root, plan_sha, r) for r in plan["role_order"]}
    bundle = {
        "schema": "topolab.v2.m2-content-verified-public-bundle.v1",
        "execution_identity": IDENTITY,
        "scope": SCOPE,
        "plan": plan,
        "plan_sha256": plan_sha,
        "contract_sha256": plan["contract_sha256"],
        "root": str(root / "content"),
        "registry": read_json(root / "registry.json"),
        **closed,
        "role_views": closed["manifest"]["role_views"],
        "roles": roles,
        "lease": read_json(root / "lease-release.json"),
        "backup": read_json(root / "backup-proof.json"),
        "filing": observed_wire(root, plan_sha, "final-filing"),
        "lease_release_evidence": observed_wire(root, plan_sha, "lease-release"),
        "shared_packet_sha256": sha(canonical(role_results(root, plan))),
    }
    events = {
        r: read_json(root / (r + "-events.json"))
        for r in [*plan["role_order"], "final-filing", "lease-release"]
    }
    return bundle, events


def certify_public(root, plan, plan_sha):
    bundle, events = public_bundle(root, plan, plan_sha)
    certificate = load("p17_m2_content_verified_independent").audit_public_certificate(
        bundle, trusted_tool_events=events
    )
    need(type(certificate).__name__ == "CheckedPublicInput", "independent capability missing")
    put(root / "accepted-public-bundle.json", evidence_json({"bundle": bundle, "events": events}))
    return {
        "status": "PUBLIC_CAPABILITY_VERIFIED_FORMAL_CLOSED",
        "scope": SCOPE,
        "formal_authority": False,
        "old_original_reads": 0,
        "member_count": 1071,
        "version_id": bundle["version_id"],
        "plan_sha256": plan_sha,
    }


def main():
    global READER_ROLE
    # Deny formal before parsing or accessing any proposed source or target path.
    modes = ("prepare-public", "payload", "supervise", "run", "record", "bind", "certify-public")
    if len(sys.argv) < 2 or sys.argv[1] not in modes:
        print("FORMAL_AUTHORITY_NOT_GRANTED", file=sys.stderr)
        return 2
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=modes)
    parser.add_argument("--root", required=True)
    parser.add_argument("--plan-sha")
    parser.add_argument("--role")
    parser.add_argument("--reader-role")
    parser.add_argument(
        "--public-fault",
        choices=[
            "outer-watchdog",
            "outer-watchdog-missing-started",
            "outer-watchdog-corrupt-started",
        ],
    )
    args = parser.parse_args()
    if args.reader_role is not None:
        READER_ROLE = args.reader_role
    if args.mode == "prepare-public":
        need(
            args.plan_sha is None and args.role is None and args.reader_role is None,
            "public setup accepts no source/role grant",
        )
        result = prepare(args.root, args.public_fault)
    else:
        need(args.public_fault is None, "public fault is frozen only at new public setup")
        root, plan = checked(args.root, args.plan_sha)
        need(
            sys.flags.isolated == 1 and runtime()["threads"] == THREADS,
            "isolated locked single-thread runtime required",
        )
        need(
            sys.orig_argv == argv_for(root, args.mode, args.plan_sha, args.role),
            "actual orig_argv differs from frozen entry",
        )
        if args.mode == "certify-public":
            result = certify_public(root, plan, args.plan_sha)
        elif args.mode == "supervise":
            result = supervise(root, plan, args.plan_sha, args.role)
        elif args.mode == "run":
            result = native_module(root).invoke(
                root / "receipts" / args.role,
                args.role,
                argv_for(root, "payload", args.plan_sha, args.role),
                timeout=160 if args.role == "final-filing" else role_cap(args.role) - 10,
            )
        elif args.mode == "bind":
            result = bind(root, plan, args.plan_sha, args.role)
        elif args.mode == "record":
            result = collect(root, args.plan_sha, args.role)
        else:
            result = payload(root, plan, args.role)
    print(canonical(result).decode(), end="")
    return (
        1
        if (
            result.get("status") == "STOP_NO_RETRY"
            or result.get("completion", {}).get("status") == "FAILED_INTERNAL_COMPLETION"
        )
        else 0
    )


if __name__ == "__main__":
    raise SystemExit(main())
