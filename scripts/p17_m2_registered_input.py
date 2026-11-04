"""Exact23 preread registration for the NEW bounded acquisition identity.

No source/target IO occurs at import or literal routing. Registration admission is
metadata-only and replays the independent native certificate and actual returns.
The existing bounded Reader still owns single-buffer hashing/parsing and failures.
"""

import hashlib
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.20261104.v2"
PROTOCOL = "docs/planning/p17_m2_registered_input_v2_protocol.json"
SCHEMA = "topolab.v2.m2-registered-source-acquisition-authority.v2"
PUBLIC_PREFIX = "topolab-public-registered-source-acquisition-"
POLICY = "topolab.source-identity.prebound-sha256.v1"
REGISTRATION_IDENTITY = "topolab.strict23-preread-registration.v1"
PARENT = "/Users/keith1117/Library/Application Support/TopoLab-custody"
GENERATIONS = tuple(
    PARENT + "/p17-m2-local-input-version-v" + number + "-strict-binding-" + suffix
    for number, suffix in (("8", "20261103"), ("9", "remedy-20261103"))
)
PHYSICAL = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
REGISTRATION_KEYS = {
    "certificate_path",
    "certificate_sha256",
    "finalize_actual_path",
    "finalize_actual_sha256",
}


def load_control():
    name = "p17_m2_source_acquisition_control"
    existing = sys.modules.get(name)
    if existing is not None:
        return existing
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name + ".py"))
    if spec is None or spec.loader is None:
        raise ValueError("missing source acquisition controller")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


control = load_control()
producer = control.load("p17_m2_input_export")


def need(ok, reason):
    if not ok:
        raise ValueError("STOP: " + reason)


def is_root(root):
    """Memory-only routing, with no authority or existence inference."""
    return str(root) in GENERATIONS or Path(root).name.startswith(PUBLIC_PREFIX)


def registration_bindings(certificate):
    """Project accepted original strict observations, preserving integer tuples."""
    specs = control.load("p17_m2_source_binding_independent").metadata_specs()
    rows = certificate.get("source_observations")
    need(
        isinstance(rows, list)
        and len(rows) == 23
        and [row.get("path") for row in rows] == [row["path"] for row in specs],
        "registration exact23 observations required",
    )
    result = {}
    for row, spec in zip(rows, specs, strict=True):
        size, digest = row.get("byte_size"), row.get("sha256")
        need(
            type(size) is int
            and 0 < size <= spec["max_bytes"]
            and isinstance(digest, str)
            and re.fullmatch("[0-9a-f]{64}", digest),
            "registration hash/size invalid",
        )
        observed = [row.get(point) for point in ("declared", "before", "after", "closing")]
        need(
            all(
                isinstance(value, dict)
                and set(value) == set(PHYSICAL)
                and all(type(value[key]) is int for key in PHYSICAL)
                for value in observed
            )
            and all(value == observed[0] for value in observed)
            and observed[0]["st_size"] == size,
            "registration observations must be complete strict identical tuples",
        )
        result[row["path"]] = {"sha256": digest, "byte_size": size, "declared": dict(observed[0])}
    return result


def trusted_registration(plan):
    """Replay actual acceptance before deriving any expected source hash."""
    need(
        plan.get("execution_identity") == IDENTITY and plan.get("source_identity_policy") == POLICY,
        "registered execution identity required",
    )
    reference = plan.get("binding", {}).get("strict23_registration")
    need(
        isinstance(reference, dict) and set(reference) == REGISTRATION_KEYS,
        "strict23 registration proof required",
    )
    values = []
    checker = control.load("p17_m2_source_acquisition_independent")
    for prefix in ("certificate", "finalize_actual"):
        path, expected = reference[prefix + "_path"], reference[prefix + "_sha256"]
        need(
            isinstance(path, str)
            and Path(path).is_absolute()
            and str(Path(path)) == path
            and ".." not in Path(path).parts
            and isinstance(expected, str)
            and re.fullmatch("[0-9a-f]{64}", expected),
            "registration literal proof path/hash required",
        )
        raw = checker.native._software_bytes(Path(path))
        need(hashlib.sha256(raw).hexdigest() == expected, "registration proof SHA differs")
        values.append(producer.parse(raw))
    kind = "formal" if plan.get("scope") == control.FORMAL_SCOPE else "public"
    pin = authority()["registration"][kind]
    need(
        reference["certificate_path"] == pin["certificate_paths"][0]
        and reference["finalize_actual_path"] == pin["finalize_actual_path"],
        "registration frozen proof paths differ",
    )
    recovery = control.load("p17_m2_source_binding_recovery")
    paired, paths = recovery.certificate_pair(kind, 1, reference["certificate_sha256"])
    need(
        [str(path) for path in paths] == pin["certificate_paths"]
        and producer.canonical(paired) == producer.canonical(values[0]),
        "registration independent certificate pair differs",
    )
    need(
        plan.get("scope") in (control.FORMAL_SCOPE, control.REHEARSAL_SCOPE),
        "registration source scope differs",
    )
    certificate, proof = control.load("p17_m2_source_binding_recovery").verify_registration(
        *values, kind=kind
    )
    need(proof.get("full_role_evidence_accepted") is True, "registration actual audit not accepted")
    need(
        certificate["registered_context"]["source_root"] == plan.get("source_root"),
        "registration source root differs",
    )
    return certificate, registration_bindings(certificate)


class _RegisteredReader(producer.Reader):
    def __init__(self, root, journal=None, *, registration, **kwargs):
        self._registrations = registration
        need(
            kwargs.get("source_identity_checks") is True
            and kwargs.get("source_identity_policy") == POLICY,
            "registered Reader closing/hash policy required",
        )
        super().__init__(root, journal, **kwargs)

    def _read(self, relative, limit, *, expected=None, size=None, group="metadata", total=None):
        bound = self._registrations.get(relative)
        if bound is not None:
            self._read_facts["registered_preread_anchor"] = dict(bound["declared"])
            need(
                expected is None or expected == bound["sha256"],
                "registered expected hash conflicts",
            )
            need(size is None or size == bound["byte_size"], "registered expected size conflicts")
            expected, size = bound["sha256"], bound["byte_size"]
            self._read_facts["expected_sha256"] = expected
        return super()._read(
            relative, limit, expected=expected, size=size, group=group, total=total
        )

    def _identity(self, stage, value):
        super()._identity(stage, value)
        bound = self._registrations.get(self._read_facts["path"])
        if bound is not None:
            need(
                all(getattr(value, key) == bound["declared"][key] for key in PHYSICAL[:-1]),
                "registered physical anchor differs at " + stage,
            )


def source_reader(plan, root, journal=None, **kwargs):
    """The only producer factory; no caller-supplied registration map admitted."""
    need(str(Path(root).absolute()) == plan.get("source_root"), "registered source root differs")
    _, bindings = trusted_registration(plan)
    return _RegisteredReader(root, journal, registration=bindings, **kwargs)


def authority_raw():
    return control.load("p17_m2_source_acquisition_independent").native._software_bytes(
        REPO / PROTOCOL
    )


def authority(raw=None):
    value = producer.parse(authority_raw() if raw is None else raw)
    need(
        value.get("schema") == SCHEMA
        and value.get("execution_identity") == IDENTITY
        and value.get("source_identity_policy") == POLICY
        and value.get("registration_identity") == REGISTRATION_IDENTITY,
        "registered authority identity/policy differs",
    )
    need(
        value.get("profile") == "NEW_REGISTERED_INPUT_COMPACT_RESULT_1800"
        and value.get("formal_seconds") == 4500
        and value.get("result_seconds") == {"exporter": 1800, "independent": 1800}
        and value.get("global_deadline_ms") == 1793828280000,
        "registered finite compact profile differs",
    )
    need(
        value.get("fixed_target")
        == {
            "parent": PARENT,
            "attempts": {
                str(index + 1): {"generation": name, "backup": name + "-independent-backup"}
                for index, name in enumerate(GENERATIONS)
            },
        },
        "registered fixed targets differ",
    )
    need(
        value.get("permissions")
        == {
            "formal_activation": True,
            "old_original_access": True,
            "target_access": True,
            "B_C": False,
        },
        "registered permissions differ",
    )
    need(
        value.get("new_input_budget")
        == {
            "path": "/Users/keith1117/Documents/TopoLab-data/"
            "p17-m2-source-binding-v1-20261103T173800Z/"
            "NEW-unstarted-input-closure-coordination-repair-v22.json",
            "sha256": "b8d09dec380471e61b112dd7d91411860787e782c606528c0c47cee10b7f07fb",
        },
        "registered new input budget pin differs",
    )
    limits = value.get("input_limits", {})
    need(
        limits
        == {
            "attempts": 2,
            "source_reads_each_author_each_attempt": 598,
            "source_reads_all_input_attempts": 2392,
            "original_reads_including_closed_registration": 2484,
            "registered_foundation_helpers_all": 138,
            "source_counts": [40, 558],
            "version_members": 1071,
            "FULL_each_input_ceiling": 3780,
            "FULL_all_input_attempts_ceiling": 7560,
            "formal_top_control_CLI_all": 52,
            "public_graphs_max": 1,
            "public_top_control_CLI_all": 64,
            "public_FULL_all_ceiling": 3780,
            "original_public1_2_and_new3_total_attempts": 3,
            "coordination_seconds_max": 240,
            "prepare_to_first_SUP_seconds_max": 30,
            "RSS_bytes": 4294967296,
            "metadata_action_cap": 180,
        }
        and value.get("FULL_by_role") == dict(control.base().CAPS),
        "registered exact input/FULL/resource limits differ",
    )
    actors = value.get("actors", {})
    need(
        set(actors) == {"executor", "independent"}
        and all(isinstance(actor, str) and actor.strip() for actor in actors.values())
        and actors["executor"] != actors["independent"],
        "registered independent actors required",
    )
    return value


def _registration_plan(root, kind, reference):
    policy = authority()
    need(
        isinstance(reference, dict) and set(reference) == REGISTRATION_KEYS,
        "accepted new strict23 registration is not frozen",
    )
    envelope_raw = control.load("p17_m2_source_acquisition_independent").native._software_bytes(
        Path(reference["certificate_path"])
    )
    need(
        producer.sha(envelope_raw) == reference["certificate_sha256"],
        "registered envelope SHA differs",
    )
    envelope = producer.parse(envelope_raw)
    source = envelope["core_bundle"]["certificate"]["registered_context"]["source_root"]
    partial = {
        "execution_identity": IDENTITY,
        "source_identity_policy": POLICY,
        "scope": control.FORMAL_SCOPE if kind == "formal" else control.REHEARSAL_SCOPE,
        "source_root": source,
        "binding": {"strict23_registration": reference},
    }
    trusted_registration(partial)
    return policy, reference, envelope


def prepare_rehearsal(root, reference):
    """Reuse only the captured NEW public source inode, with fresh custody/lease."""
    import os
    import time

    root = control.rehearsal_root(root)
    policy, reference, envelope = _registration_plan(root, "public", reference)
    need(str(root) in policy["public_roots"], "unregistered public input generation")
    core_plan = envelope["core_bundle"]["plan"]
    checker = control.load("p17_m2_source_acquisition_independent")
    values = []
    for name, key in (
        ("public-content-contract.json", "public_content_contract_sha256"),
        ("public-source-identity.json", "public_source_identity_sha256"),
    ):
        raw = checker.native._software_bytes(Path(core_plan["root"]) / name)
        need(producer.sha(raw) == core_plan["entry"][key], "captured public projection SHA differs")
        values.append(producer.parse(raw))
    plan = control.make_plan(root, *values, strict23_registration=reference)
    plan["source_root"] = core_plan["context"]["source_root"]
    checker.validate_binding(plan)
    helper = control.base()
    parent = helper.nofollow_directory(root.parent)
    began = time.monotonic()
    try:
        os.mkdir(root.name, 0o700, dir_fd=parent)
        os.fsync(parent)
    finally:
        os.close(parent)
    helper.put(root / "plan.json", plan)
    control.initial_lease(root, plan)
    control.finish_setup(root, plan, began=began)
    return {
        "plan_sha256": producer.sha(producer.canonical(plan)),
        "scope": control.REHEARSAL_SCOPE,
        "formal_authority": False,
        "source_stat_reads": 0,
    }


def formal_plan(raw, *, attempt=1, strict23_registration=None):
    """Pure plan construction; no original source or custody inspection."""
    policy = authority(raw)
    need(type(attempt) is int and attempt in (1, 2), "registered attempt differs")
    reference = strict23_registration
    need(
        isinstance(reference, dict) and set(reference) == REGISTRATION_KEYS,
        "accepted formal strict23 registration is not frozen",
    )
    contract = producer.parse(
        (REPO / "docs/planning/p17_m2_input_export_preparation_proposal.json").read_bytes()
    )
    known = control.load("p17_m2_input_export_independent")
    source_identity = {"B3_DATA_HASH": known.B3_DATA_HASH, "CATALOG_HASH": known.CATALOG_HASH}
    target = policy["fixed_target"]["attempts"][str(attempt)]
    plan = control.make_plan(
        Path(target["generation"]), contract, source_identity, strict23_registration=reference
    )
    del plan["public_source_identity"]
    proposal = producer.parse((REPO / control.PROPOSAL).read_bytes())
    digest = producer.sha(raw)
    plan.update(
        scope=control.FORMAL_SCOPE,
        formal_authority=True,
        source_root=proposal["source_whitelist"]["original_root_literal"],
        backup_root=target["backup"],
        source_identity=source_identity,
        contract_sha256=digest,
    )
    plan["binding"].update(
        formal_authority=True,
        old_original_access=True,
        target_access=True,
        formal_attempt=attempt,
        execution_protocol_sha256=digest,
    )
    return plan


def registration_reference(kind, certificate_sha, finalize_actual_sha):
    pin = authority()["registration"][kind]
    need(
        all(
            isinstance(value, str) and re.fullmatch("[0-9a-f]{64}", value)
            for value in (certificate_sha, finalize_actual_sha)
        ),
        "actual new registration hashes required",
    )
    return {
        "certificate_path": pin["certificate_paths"][0],
        "certificate_sha256": certificate_sha,
        "finalize_actual_path": pin["finalize_actual_path"],
        "finalize_actual_sha256": finalize_actual_sha,
    }


def _read_pin(reference):
    need(
        isinstance(reference, dict)
        and set(reference) == {"path", "sha256"}
        and isinstance(reference["path"], str)
        and Path(reference["path"]).is_absolute()
        and isinstance(reference["sha256"], str)
        and re.fullmatch("[0-9a-f]{64}", reference["sha256"]),
        "bounded evidence pin required",
    )
    raw = control.load("p17_m2_source_acquisition_independent").native._software_bytes(
        Path(reference["path"])
    )
    need(producer.sha(raw) == reference["sha256"], "external readiness proof SHA differs")
    return producer.parse(raw)


def readiness_inputs(policy):
    """Re-audit exact public native and actual outer return; no source/target IO."""
    checker = control.load("p17_m2_source_acquisition_independent")
    raw = checker.native._software_bytes(Path(policy["readiness_path"]))
    ready = producer.parse(raw)
    frozen = {
        key: digest for key, digest in control.source_freeze(IDENTITY).items() if key != PROTOCOL
    }
    runtime = control.base().runtime()
    need(
        ready.get("schema") == "topolab.registered-input.activation-readiness.v1"
        and ready.get("execution_identity") == IDENTITY
        and ready.get("actors") == policy["actors"]
        and ready.get("new_input_budget") == policy["new_input_budget"]
        and ready.get("published_source_sha256") == frozen
        and all(
            ready.get("runtime", {}).get(key) == value
            for key, value in runtime.items()
            if key != "orig_argv"
        ),
        "registered readiness software/runtime/actors/budget differs",
    )
    _read_pin(policy["new_input_budget"])
    public_pin = ready.get("public_native_acceptance", {})
    need(
        public_pin.get("path")
        in {root + "/accepted-acquisition-bundle.json" for root in policy["public_roots"]},
        "registered public acceptance literal differs",
    )
    accepted = control.base().evidence_json(_read_pin(public_pin), decode=True)
    checker.audit_certificate(accepted["bundle"], trusted_tool_events=accepted["events"])
    public_plan = accepted["bundle"]["plan"]
    need(
        public_plan["execution_identity"] == IDENTITY
        and public_plan["scope"] == control.REHEARSAL_SCOPE
        and public_plan["source_tree"] == control.source_freeze(IDENTITY),
        "registered exact public adapter acceptance required",
    )
    public_root = Path(public_plan["root"])
    need(
        str(public_root) in policy["public_roots"]
        and ready["public_native_acceptance"]["path"]
        == str(public_root / "accepted-acquisition-bundle.json"),
        "registered public acceptance literal differs",
    )
    need(
        ready.get("public_certificate_actual", {}).get("path")
        == str(public_root / policy["public_certificate_actual_name"]),
        "registered public certificate actual literal differs",
    )
    actual = _read_pin(ready["public_certificate_actual"])
    argv = control.argv_for(
        public_root,
        "certify-rehearsal",
        producer.sha(producer.canonical(public_plan)),
        "certificate",
    )
    recovery = control.load("p17_m2_source_binding_recovery")
    first, last = recovery.exact_actual(actual, argv, policy["actors"]["executor"])
    result = {
        "scope": control.REHEARSAL_SCOPE,
        "formal_authority": False,
        "source_input_accepted": False,
        "formal_or_scientific_admission": False,
        "B_C_admission": False,
        "member_count": len(accepted["bundle"]["manifest"]["members"]),
        "version_id": accepted["bundle"]["version_id"],
    }
    stdout = "".join(row["result"]["output"] for row in actual["responses"]).encode("utf-8")
    need(
        stdout == producer.canonical(result)
        and first
        >= max(
            event["end_seconds"] * 1000
            for events in accepted["events"].values()
            for event in events
        ),
        "registered public certificate actual stdout/chronology differs",
    )
    need(last <= policy["global_deadline_ms"], "registered public actual exceeds global deadline")
    paths = ready.get("preparation_closure_paths")
    need(
        paths == policy["preparation_closure_paths"],
        "registered preparation closure literal paths differ",
    )
    import stat

    identities = []
    closure = None
    for path in paths:
        before = Path(path).lstat()
        captured = _read_pin({"path": path, "sha256": ready.get("preparation_closure_sha256")})
        after = Path(path).lstat()
        need(
            stat.S_ISREG(before.st_mode)
            and before.st_nlink == 1
            and stat.S_IMODE(before.st_mode) == 0o600
            and all(getattr(before, key) == getattr(after, key) for key in PHYSICAL),
            "registered private stable preparation closure required",
        )
        identities.append((before.st_dev, before.st_ino))
        need(closure is None or closure == captured, "registered preparation closure copies differ")
        closure = captured
    need(len(set(identities)) == 2, "registered independent closure inodes required")
    need(
        closure.get("schema") == "topolab.registered-input.preparation-closure.v1"
        and closure.get("execution_identity") == IDENTITY
        and closure.get("source_tree") == control.source_freeze(IDENTITY)
        and closure.get("public_native_acceptance") == ready["public_native_acceptance"]
        and closure.get("new_input_budget") == policy["new_input_budget"]
        and closure.get("status") == "COMPLETE_SOFTWARE_ONLY"
        and closure.get("own_future_return") == "NOT_CLAIMED",
        "registered actual preparation closure content differs",
    )
    retention_pin = ready.get("preparation_retention_actual", {})
    need(
        retention_pin.get("path") == policy["preparation_retention_actual_path"],
        "registered preparation actual literal differs",
    )
    retention = _read_pin(retention_pin)
    retained_first, retained_last = recovery.exact_actual(
        retention, closure["retention_argv"], policy["actors"]["executor"]
    )
    summary = {
        "status": "REGISTERED_INPUT_PREPARATION_PAIR_RETAINED",
        "closure_paths": paths,
        "sha256": ready["preparation_closure_sha256"],
        "own_future_return": "NOT_CLAIMED",
    }
    need(
        "".join(row["result"]["output"] for row in retention["responses"]).encode("utf-8")
        == producer.canonical(summary)
        and last <= retained_first <= retained_last <= policy["global_deadline_ms"],
        "registered actual pair retention return/stdout/chronology differs",
    )
    ready["_preparation_actual_returned_ms"] = retained_last
    return ready, producer.sha(raw)


def preflight_summary(policy, ready, digest):
    return {
        "status": "PASS_REGISTERED_INPUT_METADATA_PREFLIGHT",
        "execution_identity": IDENTITY,
        "author": policy["actors"]["independent"],
        "readiness_path": policy["readiness_path"],
        "readiness_sha256": digest,
        "published_source_sha256": ready["published_source_sha256"],
        "runtime": ready["runtime"],
        "actors": ready["actors"],
        "new_input_budget": ready["new_input_budget"],
        "source_stat_reads": 0,
        "target_stat_reads": 0,
        "own_future_return": "NOT_CLAIMED",
    }


def activation_readiness(value, plan):
    """Input clocks and source registration precede shared publication gates."""
    import time

    policy = authority(producer.canonical(value))
    need(
        time.time_ns() // 10**6 + (4500 + 1800) * 1000 <= policy["global_deadline_ms"],
        "registered complete formal/result suffix unavailable",
    )
    trusted_registration(plan)
    return publication_readiness(policy)


def publication_readiness(value):
    """Actual publication evidence without starting a second input clock."""
    import time

    policy = authority(producer.canonical(value))
    ready, digest = readiness_inputs(policy)
    checker = control.load("p17_m2_source_acquisition_independent")
    raw = checker.native._software_bytes(Path(policy["independent_preflight_actual_path"]))
    actual = producer.parse(raw)
    argv = [
        control.base().runtime()["python"],
        "-I",
        str(Path(__file__).resolve()),
        "preflight",
        "--readiness-sha",
        digest,
    ]
    started, ended = control.load("p17_m2_source_binding_recovery").exact_actual(
        actual, argv, policy["actors"]["independent"]
    )
    need(
        "".join(row["result"]["output"] for row in actual["responses"]).encode("utf-8")
        == producer.canonical(preflight_summary(policy, ready, digest))
        and ready["_preparation_actual_returned_ms"]
        <= started
        <= ended
        <= time.time_ns() // 10**6
        <= policy["global_deadline_ms"],
        "registered independent actual preflight differs",
    )
    combined = dict(
        policy,
        preparation_closure_sha256=ready["preparation_closure_sha256"],
        independent_preflight_sha256=producer.sha(raw),
    )
    main = control.published_main_readiness(combined, funded=True)
    return dict(
        main,
        readiness_reference={"path": policy["readiness_path"], "sha256": digest},
        independent_preflight_reference={
            "path": policy["independent_preflight_actual_path"],
            "sha256": producer.sha(raw),
        },
    )


def activate_formal(root, reference):
    policy = authority()
    need(str(root) in GENERATIONS, "registered formal literal required")
    attempt = GENERATIONS.index(str(root)) + 1
    need(attempt == 1, "registered remedy requires separately diagnosed published readiness")
    plan = formal_plan(producer.canonical(policy), attempt=attempt, strict23_registration=reference)
    ready = activation_readiness(policy, plan)
    plan = formal_plan(producer.canonical(policy), attempt=attempt, strict23_registration=reference)
    plan["activation_readiness"] = ready["readiness_reference"]
    plan["independent_preflight"] = ready["independent_preflight_reference"]
    control.load("p17_m2_source_acquisition_independent").validate_binding(plan)
    return control.setup_formal(plan, ready)


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("preflight",))
    parser.add_argument("--readiness-sha", required=True)
    args = parser.parse_args()
    need(
        Path.cwd() == REPO and sys.flags.isolated == 1,
        "registered preflight isolated working directory required",
    )
    policy = authority()
    ready, digest = readiness_inputs(policy)
    need(digest == args.readiness_sha, "registered readiness actual SHA differs")
    print(producer.canonical(preflight_summary(policy, ready, digest)).decode(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
