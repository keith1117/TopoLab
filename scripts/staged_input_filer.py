"""New staged-input actual-return filing and bounded failure custody; no source reads."""

import argparse
import hashlib
import json
import os
import shlex
import stat
import sys
import types
from pathlib import Path

SOURCE_CHECKOUT = Path(__file__).resolve().parents[1]
RUNTIME_REPO = Path("/private/tmp/topolab-staged-input-20261121")
EVIDENCE = Path("/Users/keith1117/Documents/TopoLab-data/staged-input-acceptance-20261121")
BACKUP = Path(str(EVIDENCE) + "-backup")
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.staged-20261121.v1"
BUDGET_SHA = "7212bce05d9f1d953c44b800c59d941e2e1e44111777845ae57f2479be170687"
CONTROL_ENTRY = "staged_input_control.py"
PUBLIC = "/private/tmp/topolab-public-staged-input-20261121-a1"
FORMAL = (
    "/Users/keith1117/Library/Application Support/TopoLab-custody/p17-m2-staged-input-20261121-a1"
)
ROOTS = (PUBLIC, FORMAL)
SOURCE_DIGESTS = {}
return_projection = None
PYTHON = (
    "/Library/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python"
)
ROLES = (
    "independent-public-check",
    "exporter-r0",
    "independent-r0",
    "exporter-r1",
    "independent-r1",
    "shared-closeout",
)
FULL = dict(zip(ROLES, (300, 300, 300, 1200, 1200, 300), strict=True))
FULL.update({"final-filing": 180, "lease-release": 180})
ACTUAL_SCHEMA = "topolab.v2.m2-strict-source-binding.actual-call.v1"
FAILURE_SCHEMA = "topolab.staged-input-caller-failure.v1"
STOP_SCHEMA = "topolab.staged-input-caller-stop.v1"
MAX_BYTES = 16 * 1024**2
THREADS = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)


def need(condition, message):
    if not condition:
        raise ValueError("STAGED_INPUT_COURIER: " + message)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def literal_command(argv):
    return "exec " + " ".join(
        shlex.quote(s) for s in ["env", *(key + "=1" for key in THREADS), *argv]
    )


def validate_terminal(packet, argv, author, cwd):
    """Accept original terminal failure as evidence, never as role acceptance."""
    need(
        packet.get("schema") == ACTUAL_SCHEMA
        and packet.get("author") == author
        and packet.get("argv") == argv
        and packet.get("request", {}).get("cmd") == literal_command(argv)
        and packet["request"].get("workdir") == cwd,
        "literal original caller differs",
    )
    rows = packet.get("responses")
    need(isinstance(rows, list) and 1 <= len(rows) <= 65, "bounded original responses required")
    previous, session = None, None
    for index, row in enumerate(rows):
        args, result = row.get("arguments", {}), row.get("result", {})
        need(
            type(row.get("requested_ms")) is int
            and type(row.get("returned_ms")) is int
            and row["requested_ms"] <= row["returned_ms"]
            and (previous is None or previous <= row["requested_ms"])
            and isinstance(result.get("output"), str),
            "original clock/output missing",
        )
        need(
            "Warning: truncated output" not in result["output"]
            and "tokens truncated" not in result["output"]
            and (
                result.get("original_token_count") is None
                or result["original_token_count"] <= args.get("max_output_tokens", 10000)
            ),
            "truncated original response",
        )
        if index == 0:
            need(
                row.get("tool") == "exec_command" and args == packet["request"],
                "first request differs",
            )
        else:
            need(
                row.get("tool") == "write_stdin"
                and session is not None
                and type(args.get("session_id")) is int
                and args["session_id"] == session
                and args.get("chars", "") == ""
                and type(args.get("yield_time_ms", 5000)) is int
                and 0 < args.get("yield_time_ms", 5000) <= 30000,
                "unowned/nonempty poll",
            )
        if index < len(rows) - 1:
            need(
                type(result.get("session_id")) is int
                and result.get("exit_code") is None
                and (session is None or session == result["session_id"]),
                "session changed",
            )
            session = result["session_id"]
        else:
            need(
                type(result.get("exit_code")) is int and result.get("session_id") is None,
                "terminal return absent",
            )
        previous = row["returned_ms"]
    return rows[0]["requested_ms"], previous, rows[-1]["result"]["exit_code"]


def source_module(name, path):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    raw = Path(path).read_bytes()
    exec(compile(raw, str(path), "exec"), module.__dict__)
    module.source_buffer_sha256 = sha(raw)
    return module


def parent_fd(path):
    path = Path(path)
    need(path.is_absolute() and ".." not in path.parts, "absolute no-follow metadata path required")
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def read_private(path, maximum=MAX_BYTES):
    path = Path(path)
    parent = parent_fd(path)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            if before.st_size == 0:
                raise FileNotFoundError("owned metadata publication has not completed")
            need(
                stat.S_ISREG(before.st_mode)
                and before.st_nlink == 1
                and stat.S_IMODE(before.st_mode) == 0o600
                and 0 < before.st_size <= maximum,
                "bounded private ordinary metadata required",
            )
            raw = stream.read(maximum + 1)
            after = os.fstat(stream.fileno())
        closing = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        keys = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_mode", "st_nlink")
        need(
            all(getattr(before, k) == getattr(after, k) == getattr(closing, k) for k in keys)
            and len(raw) == before.st_size,
            "metadata identity/closing/length changed",
        )
        return raw
    finally:
        os.close(parent)


def write_private(path, raw):
    path = Path(path)
    need(
        type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, "bounded complete metadata wire required"
    )
    parent = parent_fd(path)
    try:
        fd = os.open(
            path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent
        )
        with os.fdopen(fd, "wb") as stream:
            need(stream.write(raw) == len(raw), "metadata short write")
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(parent)
    finally:
        os.close(parent)
    need(read_private(path) == raw, "metadata readback differs")
    return dict(path=str(path), sha256=sha(raw), bytes=len(raw))


def read_json(path, expected=None):
    raw = read_private(path)
    need(expected is None or sha(raw) == expected, "raw metadata SHA differs")
    value = json.loads(raw, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    need(canonical(value) == raw, "canonical complete metadata required")
    return value, raw


def evidence_path(path):
    path = Path(path)
    need(
        path.is_absolute()
        and ".." not in path.parts
        and path != EVIDENCE
        and path.is_relative_to(EVIDENCE),
        "exact new evidence destination required",
    )
    return path


def publish_pair(destination, raw):
    target = evidence_path(destination)
    copies, failures = [], []
    for path in (target, BACKUP / target.relative_to(EVIDENCE)):
        try:
            copies.append(write_private(path, raw))
        except Exception as error:
            failures.append(dict(path=str(path), type=type(error).__name__, reason=str(error)))
    return dict(
        status="PAIRED_PERSISTED" if not failures else "PARTIAL_CUSTODY",
        path=str(target),
        sha256=sha(raw),
        bytes=len(raw),
        copies=copies,
        failures=failures,
    )


def stop_path(root):
    need(root in ROOTS, "new STOP root differs")
    return EVIDENCE / ("input-" + ("formal" if root == FORMAL else "public") + "-caller-STOP.json")


def persist(packet, destination):
    need(
        packet.get("schema") in (ACTUAL_SCHEMA, FAILURE_SCHEMA)
        and packet.get("author") in ("/root", "/root/full60_independent"),
        "actual/failure author differs",
    )
    if packet["schema"] == FAILURE_SCHEMA:
        need(
            packet.get("execution_identity") == IDENTITY and packet.get("caller_root") in ROOTS,
            "new caller STOP identity differs",
        )
    target = Path(destination)
    public_certificate = (PUBLIC in ROOTS
                          and target == Path(PUBLIC) / "certify-rehearsal-raw-actual-call.json")
    raw = canonical(packet)
    if public_certificate:
        saved = write_private(target, raw)
        copies = publish_pair(EVIDENCE / (packet["event_id"] + "-public-certificate.json"), raw)
        result = dict(copies, path=str(target), public_certificate=saved)
    else:
        result = publish_pair(target, raw)
    if packet["schema"] == FAILURE_SCHEMA:
        notice = dict(
            schema=STOP_SCHEMA,
            execution_identity=IDENTITY,
            root=packet["caller_root"],
            author=packet["author"],
            original_failure=dict(path=str(target), sha256=sha(raw)),
            source_or_payload_reads=0,
        )
        # Publish a small first-wins STOP even if one large failure copy failed.
        for path in (
            stop_path(packet["caller_root"]),
            BACKUP / stop_path(packet["caller_root"]).name,
        ):
            try:
                write_private(path, canonical(notice))
            except FileExistsError:
                prior, _ = read_json(path)
                need(
                    prior.get("schema") == STOP_SCHEMA
                    and prior.get("root") == packet["caller_root"],
                    "first STOP identity differs",
                )
            except Exception as error:
                result["failures"].append(dict(stage="STOP", path=str(path), reason=str(error)))
                result["status"] = "PARTIAL_CUSTODY"
    return result


def input_profile():
    path = SOURCE_CHECKOUT / "scripts/full60_input_loader.py"
    loader = source_module("full60_input_loader", path)
    loader.loaded_source_sha256[str(path.resolve())] = loader.source_buffer_sha256
    loader.loaded_source_sha256[str(Path(__file__).resolve())] = sha(Path(__file__).read_bytes())
    loader.loaded_source_sha256.update(SOURCE_DIGESTS)
    loader.install(require_locked_environment=True)
    # The selected registration replayer has ordinary imports from this frozen directory.
    sys.path.insert(0, str(path.parent))
    profiles = loader.load(
        "p17_m2_input_continuation", path.with_name("p17_m2_input_continuation.py")
    )
    return profiles.profile("control", IDENTITY)


def matching_pending(pending, plan, plan_sha, role, control):
    from decimal import Decimal

    expected_full = control.base().CAPS.get(role, 180 if role == "final-filing" else None)
    need(
        pending.get("execution_identity") == IDENTITY
        and pending.get("role") == role
        and pending.get("plan_sha256") == plan_sha
        and pending.get("status") == "PENDING_BEFORE_DISPATCH"
        and type(pending.get("frozen_FULL_seconds")) is type(expected_full)
        and pending.get("frozen_FULL_seconds") == expected_full
        and pending.get("external_argv")
        == [
            control.argv_for(Path(plan["root"]), mode, plan_sha, role)
            for mode in ("supervise", "record")
        ],
        "source-established pending role/plan/FULL/argv differs",
    )
    need(
        Decimal(str(pending["actor_activation_UTC_seconds"])) * 1000 == plan["whole_start_ms"]
        and all(
            pending.get(k) == plan[k]
            for k in (
                "actor_window_seconds",
                "actor_deadlines_UTC",
                "whole_start_ms",
                "whole_end_ms",
            )
        )
        and pending.get("clock_domain") == "functions.exec.Date.now.UTC-seconds"
        and pending.get("clock_resolution_seconds") == 0.001,
        "pending original clocks differ",
    )


def check_executed(plan):
    for path, digest in SOURCE_DIGESTS.items():
        relative = str(Path(path).relative_to(SOURCE_CHECKOUT))
        need(plan.get("source_tree", {}).get(relative) == digest,
             "caller executed source differs: " + relative)


def checked_plan(root, plan_sha):
    need(
        root in ROOTS and isinstance(plan_sha, str) and len(plan_sha) == 64,
        "new literal plan required",
    )
    plan, raw = read_json(Path(root) / "plan.json", plan_sha)
    need(
        plan.get("execution_identity") == IDENTITY
        and plan.get("root") == root
        and plan.get("formal_authority") is (root == FORMAL),
        "new plan scope/root differs",
    )
    check_executed(plan)
    return plan, raw


def return_bytes(mode, role, plan_sha, value, raw):
    if return_projection is None:
        return raw
    return canonical(return_projection(mode, role, plan_sha, value, raw))


def file_event(root, plan_sha, role, mode, packet_path, packet_sha):
    need(
        root in ROOTS and role in FULL and mode in ("supervise", "record"),
        "new event role/mode differs",
    )
    plan, _ = checked_plan(root, plan_sha)
    control = input_profile()
    # checked() replays the selected source freeze and original window before any write.
    _, checked = control.checked(root, plan_sha)
    need(checked == plan, "replayed plan differs")
    packet, _ = read_json(evidence_path(packet_path), packet_sha)
    author = "/root/full60_independent" if role.startswith("independent-") else "/root"
    first, last, exit_code = validate_terminal(
        packet, control.argv_for(Path(root), mode, plan_sha, role), author, str(RUNTIME_REPO)
    )
    need(
        exit_code == 0 and plan["whole_start_ms"] <= first <= last <= plan["whole_end_ms"],
        "failed/late external return cannot open a named successor",
    )
    base = control.base()
    pending, _ = read_json(Path(root) / "receipts" / (role + "-pending.json"))
    matching_pending(pending, plan, plan_sha, role, control)
    event = dict(
        event_id=packet["event_id"],
        author=author,
        argv=packet["argv"],
        start_seconds=first / 1000,
        end_seconds=last / 1000,
        wall_seconds=(last - first) / 1000,
        exit_code=exit_code,
        complete=True,
        clock_domain="functions.exec.Date.now.UTC-seconds",
        raw_packet_sha256=packet_sha,
        observed_pending_sha256=sha(canonical(pending)),
    )
    if mode == "record":
        wire, wire_raw = read_json(Path(root) / "receipts" / (role + "-wire.json"))
        need(
            "".join(r["result"]["output"] for r in packet["responses"]).encode()
            == return_bytes("record", role, plan_sha, wire, wire_raw),
            "original complete record stdout differs",
        )
        event["observed_completion_sha256"] = sha(canonical(wire["completion"]))
        prior, _ = read_json(Path(root) / (role + "-supervise-actual-event.json"))
        need(
            prior["observed_pending_sha256"] == event["observed_pending_sha256"]
            and prior["end_seconds"] <= event["start_seconds"]
            and prior["exit_code"] == 0,
            "original successful SUP predecessor differs",
        )
    base.put(Path(root) / (role + "-" + mode + "-actual-event.json"), event)
    if mode == "record":
        base.put(Path(root) / (role + "-events.json"), [prior, event])
    return dict(status="ACTUAL_EVENT_FILED", role=role, mode=mode, new_source_reads=0)


def paired_actual(reference):
    need(
        isinstance(reference, dict) and set(reference) == {"path", "sha256"},
        "original pair pin required",
    )
    path = evidence_path(reference["path"])
    value, raw = read_json(path, reference["sha256"])
    need(raw == read_private(BACKUP / path.relative_to(EVIDENCE)), "original actual pair differs")
    return value


def control_argv(root, mode, plan_sha, role):
    return [
        PYTHON,
        "-I",
        str(RUNTIME_REPO / "scripts" / CONTROL_ENTRY),
        mode,
        "--root",
        root,
        "--plan-sha",
        plan_sha,
        "--role",
        role,
    ]


def activation_return(plan, plan_sha, packet):
    public_timing = globals().get("window_public", False)
    reference = (dict.fromkeys(("certificate_sha256", "finalize_actual_sha256"),
                               plan["public_registration"]["sha256"]) if public_timing
                 else plan["binding"]["strict23_registration"])
    formal = plan["formal_authority"]
    argv = [
        PYTHON,
        "-I",
        str(RUNTIME_REPO / "scripts" / CONTROL_ENTRY),
        "activate-formal" if formal else "prepare-rehearsal",
        "--root",
        plan["root"],
        "--registration-certificate-sha",
        reference["certificate_sha256"],
        "--registration-finalize-actual-sha",
        reference["finalize_actual_sha256"],
    ]
    if not formal and not public_timing:
        ref = plan["binding"]["formal_strict23_registration"]
        argv += [
            "--formal-registration-certificate-sha",
            ref["certificate_sha256"],
            "--formal-registration-finalize-actual-sha",
            ref["finalize_actual_sha256"],
        ]
    argv += ["--whole-start-ms", str(plan["whole_start_ms"])]
    first, last, exit_code = validate_terminal(
        packet, argv, "/root" if formal else "/root/full60_independent", str(RUNTIME_REPO)
    )
    expected = dict(
        plan_sha256=plan_sha, scope=plan["scope"], formal_authority=formal, source_stat_reads=0
    )
    need(
        exit_code == 0
        and "".join(row["result"]["output"] for row in packet["responses"]).encode()
        == canonical(expected)
        and plan["whole_start_ms"]
        <= first
        <= last
        <= min(plan["whole_start_ms"] + 30000, plan["whole_end_ms"]),
        "original initial return/clock/stdout differs",
    )
    return first, last


def activation_path(root=None):
    root = FORMAL if root is None else root
    need(root in ROOTS, "new initial release root differs")
    return EVIDENCE / (
        "input-" + ("formal" if root == FORMAL else "public") + "-activation-caller-release.json"
    )


def activate_release(root, plan_sha, packet_path, packet_sha):
    need(root in ROOTS, "new initial activation release only")
    plan, _ = checked_plan(root, plan_sha)
    reference = dict(path=packet_path, sha256=packet_sha)
    first, last = activation_return(plan, plan_sha, paired_actual(reference))
    release = dict(
        schema="topolab.staged-input-activation-release.v1",
        execution_identity=IDENTITY,
        root=root,
        plan_sha256=plan_sha,
        whole_start_ms=plan["whole_start_ms"],
        activation_actual=reference,
        actual_start_ms=first,
        actual_end_ms=last,
        source_or_payload_reads=0,
    )
    return publish_pair(activation_path(root), canonical(release))


def reserve_shared(root, plan_sha, role):
    need(role == ROLES[0], "shared reservation belongs to first input role only")
    checked_plan(root, plan_sha)
    reservation = dict(
        schema="topolab.staged-input-shared-reservation.v1",
        execution_identity=IDENTITY,
        root=root,
        plan_sha256=plan_sha,
        shared_prepaid_FULL=300,
        refunds_allowed=False,
        duplicate_of_native_shared_charge=True,
        role=role,
        source_or_payload_reads=0,
        actual_native_launch="NOT_CLAIMED",
    )
    target = EVIDENCE / (
        "input-" + ("formal" if root == FORMAL else "public") + "-caller-reservation.json"
    )
    return publish_pair(target, canonical(reservation))


def release_path(root, role):
    need(root in ROOTS and role in ROLES, "caller release root/role differs")
    return EVIDENCE / (
        "input-" + ("formal" if root == FORMAL else "public") + "-" + role + "-caller-release.json"
    )


def accept_role(root, plan_sha, role, packet_path, packet_sha):
    """Publish readiness only after the original bind returned and both copies exist."""
    need(role in ROLES, "named release role differs")
    plan, _ = checked_plan(root, plan_sha)
    control = input_profile()
    control.checked(root, plan_sha)
    packet_path = evidence_path(packet_path)
    packet, packet_raw = read_json(packet_path, packet_sha)
    backup_raw = read_private(BACKUP / packet_path.relative_to(EVIDENCE))
    need(packet_raw == backup_raw, "bind original pair differs")
    author = "/root/full60_independent" if role.startswith("independent-") else "/root"
    first, last, exit_code = validate_terminal(
        packet, control.argv_for(Path(root), "bind", plan_sha, role), author, str(RUNTIME_REPO)
    )
    accepted, accepted_raw = read_json(Path(root) / (role + "-accepted.json"))
    result = accepted.get("result", {})
    need(
        exit_code == 0
        and result.get("full_role_evidence_accepted") is True
        and result.get("evidence_complete") is True
        and result.get("role") == role
        and result.get("execution_identity") == IDENTITY
        and result.get("plan_sha256") == plan_sha
        and result.get("actual_exit_codes") == [0, 0]
        and "".join(row["result"]["output"] for row in packet["responses"]).encode()
        == return_bytes("bind", role, plan_sha, result, canonical(result)),
        "original successful bind/proof stdout differs",
    )
    from decimal import Decimal

    start_ms, record_end_ms = (Decimal(str(result[key])) * 1000 for key in ("T0", "T1"))
    need(
        plan["whole_start_ms"] <= start_ms <= record_end_ms <= first <= last <= plan["whole_end_ms"]
        and last - start_ms + 10000 <= FULL[role] * 1000,
        "original binder return outside same FULL/whole window",
    )
    release = dict(
        schema="topolab.staged-input-caller-release.v1",
        execution_identity=IDENTITY,
        root=root,
        plan_sha256=plan_sha,
        role=role,
        accepted_sha256=sha(accepted_raw),
        bind_actual=dict(path=str(packet_path), sha256=packet_sha),
        actual_bind_start_ms=first,
        actual_bind_end_ms=last,
        native_start_ms=int(start_ms),
        native_record_end_ms=int(record_end_ms),
        source_or_payload_reads=0,
    )
    return publish_pair(release_path(root, role), canonical(release))


def capture_existing(path, maximum=MAX_BYTES):
    """Observe bounded failed-control bytes, labeling incomplete or changing buffers."""
    need(type(maximum) is int and 0 < maximum <= MAX_BYTES, "failure capture cap differs")
    path = Path(path)
    parent = parent_fd(path)
    keys = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_mode", "st_nlink")

    def facts(value):
        return {key: getattr(value, key) for key in keys}

    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            need(
                stat.S_ISREG(before.st_mode)
                and before.st_nlink == 1
                and stat.S_IMODE(before.st_mode) == 0o600,
                "private control file required",
            )
            raw = stream.read(maximum)
            after = os.fstat(stream.fileno())
        closing = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        stable = facts(before) == facts(after) == facts(closing) and len(raw) == before.st_size > 0
        return raw, dict(
            status="STABLE_COPY" if stable else "PARTIAL_OBSERVED",
            before=facts(before),
            after=facts(after),
            closing=facts(closing),
            returned_bytes=len(raw),
            read_cap=maximum,
            source_complete=stable,
            role_resource_acceptance="NOT_CLAIMED",
        )
    finally:
        os.close(parent)


def retain_failure(root, plan_sha, role, packet_path, packet_sha):
    """Copy existing new control records only; expired clocks never admit a new role."""
    plan, _ = checked_plan(root, plan_sha)
    need(role in (*FULL, "none"), "new failure role differs")
    failure, _ = read_json(evidence_path(packet_path), packet_sha)
    need(
        failure.get("schema") == FAILURE_SCHEMA
        and failure.get("execution_identity") == IDENTITY
        and failure.get("caller_root") == root,
        "original failure binding differs",
    )
    prefix = Path(packet_path).stem
    need(prefix.replace("-", "").replace("_", "").isalnum(), "literal failure prefix required")
    names = [
        "plan.json",
        "STOP.json",
        "active.json",
        "ledger-reservation.json",
        "lease.json",
        "custody-lock-identity.json",
        "custody-acquired.json",
        "content.cooperative-reader.lease",
        "lease-release.json",
    ]
    if role != "none":
        names += [
            role + suffix
            for suffix in (
                "-dispatch-charge.json",
                "-supervise-actual-event.json",
                "-record-actual-event.json",
                "-accepted.json",
            )
        ]
        names += [
            "receipts/" + role + suffix
            for suffix in (
                "-pending.json",
                "-supervisor.json",
                "-last-rss.json",
                "-wire.json",
                "-controller.time",
                "-controller.log",
            )
        ]
        names += [
            "receipts/" + role + "/" + role + "/" + name
            for name in (
                "pending.json",
                "started.json",
                "command.json",
                "command.time",
                "command.log",
            )
        ]
        names += ["receipts/sampler-watchdog-" + role + suffix for suffix in (".json", ".time")]
    if return_projection is not None and role != "none":
        names += [f"receipts/{role}-{mode}-original.json" for mode in ("record", "bind")]
    captured = []
    for index, relative in enumerate(names):
        item = dict(relative=relative, acceptance="NOT_CLAIMED")
        try:
            raw, observation = capture_existing(Path(root) / relative)
            item.update(observation)
            if not raw:
                captured.append(item)
                continue
            item.update(
                custody=publish_pair(EVIDENCE / (prefix + "-existing-" + str(index) + ".raw"), raw),
            )
        except Exception as error:
            item.update(status="UNKNOWN_NOT_CAPTURED", type=type(error).__name__, reason=str(error))
        captured.append(item)
    summary = dict(
        schema="topolab.staged-input-failure-custody.v1",
        execution_identity=IDENTITY,
        root=root,
        plan_sha256=plan_sha,
        role=role,
        original_failure=dict(path=packet_path, sha256=packet_sha),
        captures=captured,
        status="FAILURE_CUSTODY_RETAINED_NO_ACCEPTANCE",
        source_or_payload_reads=0,
        new_named_roles=0,
        full_role_resource="UNKNOWN_UNLESS_ALREADY_COMPLETE",
    )
    result = publish_pair(EVIDENCE / (prefix + "-existing-custody.json"), canonical(summary))
    if return_projection is not None:
        need(result["status"] == "PAIRED_PERSISTED", "failure manifest custody incomplete")
        return dict(status=summary["status"], captures=len(captured),
                    manifest={key: result[key] for key in ("path", "sha256", "bytes")})
    return dict(summary, manifest=result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "mode",
        choices=("persist", "file", "reserve", "activate-release", "accept-role", "retain-failure"),
    )
    for field in (
        "packet-json",
        "destination",
        "root",
        "plan-sha",
        "role",
        "event-mode",
        "packet",
        "packet-sha",
    ):
        parser.add_argument("--" + field)
    args = parser.parse_args()
    os.umask(0o077)
    if args.mode == "persist":
        result = persist(json.loads(args.packet_json), args.destination)
    elif args.mode == "file":
        result = file_event(
            args.root, args.plan_sha, args.role, args.event_mode, args.packet, args.packet_sha
        )
    elif args.mode == "activate-release":
        result = activate_release(args.root, args.plan_sha, args.packet, args.packet_sha)
    elif args.mode == "reserve":
        result = reserve_shared(args.root, args.plan_sha, args.role)
    elif args.mode == "accept-role":
        result = accept_role(args.root, args.plan_sha, args.role, args.packet, args.packet_sha)
    else:
        result = retain_failure(args.root, args.plan_sha, args.role, args.packet, args.packet_sha)
    print(canonical(result).decode(), end="")


if __name__ == "__main__":
    main()
