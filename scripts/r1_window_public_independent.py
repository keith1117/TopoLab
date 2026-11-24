"""Independent R0/R1 payload checks for new, literal PUBLIC window fixtures.

No formal identity, historical registration or held generation is admitted here.
Native SUP/REC/binder timing, RSS and the actual outer return are caller work.
"""

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parents[1]
IDENTITY = "topolab.v2.p17-m2-registered-source-acquisition.r1-window-public-20261123.v1"
SCOPE = "FORMAL_ADAPTER_PUBLIC_REHEARSAL_ONLY"
POLICY = "topolab.source-identity.prebound-sha256.v1"
ROOTS = tuple(Path(f"/private/tmp/topolab-public-r1-window-20261123-a{i}") for i in range(1, 7))
SELF = "scripts/r1_window_public_independent.py"
SOURCES = (
    SELF, "scripts/p17_m2_input_export_independent.py",
    "scripts/p17_m2_source_binding_independent.py", "scripts/p17_m2_local_input_independent.py",
    "scripts/p17_m2_source_acquisition_independent.py", "scripts/full60_input_loader.py",
)
POINTS = ("declared", "before", "after", "closing")
PHYSICAL = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
CAP = 16 * 1024**2
TARGET_BYTES = 567896449
MODULE_SOURCE_SHA256 = None


def need(ok, reason):
    if not ok:
        raise ValueError("PUBLIC_R1_WINDOW_STOP: " + reason)


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                       allow_nan=False) + "\n").encode("ascii")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def parse(raw):
    def pairs(items):
        answer = {}
        for key, value in items:
            need(key not in answer, "duplicate JSON key")
            answer[key] = value
        return answer

    def nonfinite(_):
        raise ValueError("PUBLIC_R1_WINDOW_STOP: nonfinite JSON")

    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)
    need(canonical(result) == raw, "canonical complete JSON required")
    return result


def directory(path):
    """Open every literal ancestor without following a symlink."""
    path = Path(path)
    need(path.is_absolute() and ".." not in path.parts, "absolute literal directory required")
    fd = os.open(path.anchor, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = following
        info = os.fstat(fd)
        need(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700,
             "fresh PUBLIC directory must be private and owned")
        return fd
    except BaseException:
        os.close(fd)
        raise


def physical(info):
    return {key: getattr(info, key) for key in PHYSICAL}


def root_identity(path):
    fd = directory(path)
    try:
        return physical(os.fstat(fd))
    finally:
        os.close(fd)


def private_bytes(path, *, maximum=CAP):
    path = Path(path)
    parent = directory(path.parent)
    try:
        declared = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        fd = os.open(path.name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=parent)
        try:
            before = os.fstat(fd)
            need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                 and before.st_uid == os.getuid() and stat.S_IMODE(before.st_mode) == 0o600
                 and 0 < before.st_size <= maximum
                 and physical(declared) == physical(before), "private metadata kind/size differs")
            chunks, total = [], 0
            while True:
                chunk = os.read(fd, min(65536, maximum + 1 - total))
                if not chunk:
                    break
                chunks.append(chunk)
                total += len(chunk)
                need(total <= maximum, "metadata grew beyond cap")
            after = os.fstat(fd)
            fresh_parent = directory(path.parent)
            try:
                closing = os.stat(path.name, dir_fd=fresh_parent, follow_symlinks=False)
            finally:
                os.close(fresh_parent)
            need(physical(before) == physical(after) == physical(closing)
                 and before.st_ctime_ns == after.st_ctime_ns == closing.st_ctime_ns
                 and before.st_nlink == after.st_nlink == closing.st_nlink == 1
                 and total == before.st_size, "metadata changed or EOF/size differs")
            return b"".join(chunks)
        finally:
            os.close(fd)
    finally:
        os.close(parent)


def public_paths(plan):
    """Reject formal/old paths before any fixture path is statted or opened."""
    root = Path(plan.get("root", ""))
    need(plan.get("schema") == "topolab.v2.m2-source-acquisition-plan.v1"
         and plan.get("execution_identity") == IDENTITY and plan.get("scope") == SCOPE
         and plan.get("formal_authority") is False and root in ROOTS,
         "literal NEW PUBLIC identity/root required")
    expected = dict(source_root=str(root) + "-source", content_root=str(root / "content"),
                    backup_root=str(root / "backup-content"))
    need(all(plan.get(key) == value for key, value in expected.items()),
         "PUBLIC source/content/backup paths differ")
    need(plan.get("source_identity_policy") == POLICY, "prebound PUBLIC source policy required")
    reference = plan.get("public_registration")
    need(type(reference) is dict and set(reference) == {"path", "sha256"}
         and reference["path"] == str(Path(str(root) + "-evidence") / "registration.json")
         and type(reference["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", reference["sha256"]),
         "literal PUBLIC registration reference differs")
    binding = plan.get("binding", {})
    need(all(binding.get(key) is False
             for key in ("formal_authority", "old_original_access", "target_access", "B_C")),
         "PUBLIC binding cannot grant formal or original access")
    return root, Path(expected["source_root"]), Path(expected["content_root"])


def software(plan):
    tree = plan.get("source_tree")
    need(type(tree) is dict and all(name in tree for name in SOURCES),
         "independent PUBLIC source closure missing")
    buffers = {}
    for name in SOURCES:
        raw = (REPO / name).read_bytes()
        need(sha(raw) == tree[name], "independent PUBLIC software buffer differs")
        buffers[name] = raw
    observed = getattr(sys.modules.get("full60_input_loader"), "loaded_source_sha256", {}).get(
        str(REPO / SELF))
    need((MODULE_SOURCE_SHA256 is not None or observed is not None)
         and MODULE_SOURCE_SHA256 in (None, tree[SELF]) and observed in (None, tree[SELF]),
         "actually executed PUBLIC verifier source differs")
    loader = sys.modules.get("full60_input_loader")
    if loader is None:
        loader = ModuleType("full60_input_loader")
        loader.__file__ = str(REPO / "scripts/full60_input_loader.py")
        exec(compile(buffers["scripts/full60_input_loader.py"], loader.__file__, "exec"),
             loader.__dict__)
        sys.modules["full60_input_loader"] = loader
    loader.install(require_locked_environment=True)
    modules = {}
    for name in SOURCES[1:-1]:
        module = ModuleType("r1_window_public_" + Path(name).stem)
        module.__file__ = str(REPO / name)
        exec(compile(buffers[name], module.__file__, "exec", dont_inherit=True), module.__dict__)
        module.MODULE_SOURCE_SHA256 = sha(buffers[name])
        modules[Path(name).stem] = module
        loader = sys.modules.get("full60_input_loader")
        if loader is not None:
            prior = loader.loaded_source_sha256.get(module.__file__)
            need(prior in (None, module.MODULE_SOURCE_SHA256), "loaded PUBLIC helper changed")
            loader.loaded_source_sha256[module.__file__] = module.MODULE_SOURCE_SHA256
    return modules


def registration_bindings(registration, specs, plan):
    need(type(registration) is dict and set(registration) == {
        "schema", "source_root", "source_observations", "content_contract", "public_source_identity"
    } and registration["schema"] == "topolab.r1-window.public-registration.v1"
        and registration["source_root"] == plan["source_root"]
        and canonical(registration["content_contract"]) == canonical(plan["content_contract"])
        and canonical(registration["public_source_identity"])
        == canonical(plan["public_source_identity"]), "PUBLIC registration context differs")
    rows = registration["source_observations"]
    need(type(rows) is list and len(rows) == len(specs) == 23
         and [row.get("path") for row in rows] == [spec["path"] for spec in specs],
         "independent exact23 registration order/count differs")
    answer = {}
    for row, spec in zip(rows, specs, strict=True):
        basic = {"path", "byte_size", "sha256", *POINTS}
        extra = {"identity_policy", "expected_sha256", "mtime_changes"}
        need(set(row) in (basic, basic | extra) and type(row["byte_size"]) is int
             and 0 < row["byte_size"] <= spec["max_bytes"]
             and type(row["sha256"]) is str and re.fullmatch("[0-9a-f]{64}", row["sha256"]),
             "PUBLIC registration size/hash/fields differ")
        need(all(type(row[point]) is dict and set(row[point]) == set(PHYSICAL)
                 and all(type(v) is int and v >= 0 for v in row[point].values())
                 for point in POINTS)
             and all(row[point] == row["declared"] for point in POINTS)
             and row["declared"]["st_size"] == row["byte_size"],
             "PUBLIC strict23 original four points differ")
        if extra <= set(row):
            need(row["identity_policy"] == POLICY and row["expected_sha256"] == row["sha256"]
                 and row["mtime_changes"] == dict.fromkeys(POINTS[1:], 0)
                 and all(type(v) is int for v in row["mtime_changes"].values()),
                 "PUBLIC registration extra identity facts differ")
        answer[row["path"]] = {"byte_size": row["byte_size"], "sha256": row["sha256"],
                               "declared": dict(row["declared"])}
    return answer


def context(plan):
    root, source, content = public_paths(plan)
    modules = software(plan)
    root_identity(root)
    root_identity(source)
    raw = private_bytes(Path(plan["public_registration"]["path"]))
    need(sha(raw) == plan["public_registration"]["sha256"], "PUBLIC registration raw SHA differs")
    registration = parse(raw)
    specs = modules["p17_m2_source_binding_independent"].metadata_specs()
    anchors = registration_bindings(registration, specs, plan)
    checker = modules["p17_m2_input_export_independent"]
    identity = plan["public_source_identity"]
    need(type(identity) is dict and set(identity) == {"B3_DATA_HASH", "CATALOG_HASH"}
         and all(type(v) is str and re.fullmatch("[0-9a-f]{64}", v) for v in identity.values())
         and identity["CATALOG_HASH"] == checker.PUBLIC_FIXTURE_CATALOG_HASH,
         "independently pinned PUBLIC catalog differs")
    checker.B3_DATA_HASH, checker.CATALOG_HASH = identity["B3_DATA_HASH"], identity["CATALOG_HASH"]
    return modules, anchors, root, source, content


def independent_r0(source, contract, producer_registry, producer_rows, source_binding, *, plan):
    modules, anchors, _root, expected_source, _content = context(plan)
    checker = modules["p17_m2_input_export_independent"]
    acquisition = modules["p17_m2_source_acquisition_independent"]
    local = modules["p17_m2_local_input_independent"]
    need(Path(source) == expected_source
         and canonical(contract) == canonical(plan["content_contract"])
         and source_binding == plan["public_source_identity"], "PUBLIC R0 arguments differ")
    reader = acquisition._registered_once_reader(
        checker, source, 40, 32 * checker.MIB, registrations=anchors,
        source_identity_checks=True, source_identity_policy=POLICY)
    before = root_identity(source)
    try:
        registry = checker.build_registry(reader, contract, selection_before_reference=True)
        checker.check_registry_shape(registry, contract)
        compared = checker.compare_words(registry, producer_registry)
        local.compare_identity_tables(reader.observations, producer_rows, 40,
                                      source_identity_policy=POLICY)
        for rows in (reader.observations, producer_rows):
            acquisition.check_expected_source_hashes(rows, registry, contract, "r0",
                enforce_r0_order=True, registrations=anchors)
            observed = {row["path"]: row for row in rows}
            for name, anchor in anchors.items():
                need(all(observed[name][point] == anchor["declared"] for point in POINTS),
                     "PUBLIC strict23 actual R0 four points differ from preregistration")
        need(root_identity(source) == before and len(reader.observations) == 40,
             "PUBLIC source root/count changed")
        return dict(status="SOURCE_ACQUISITION_R0_CHECKED", execution_identity=IDENTITY,
                    scope=SCOPE,
                    root=str(source), source_count=40, source_rows=reader.observations,
                    source_registry_sha256=sha(checker.canonical(registry)),
                    source_contract_sha256=sha(checker.canonical(contract)),
                    source_identity=source_binding, public_source_identity=source_binding,
                    compared_fields=compared, strict23_registered_and_observed=23,
                    source_comparison="PREBOUND_HASH_AND_PHYSICAL_IDENTITY_MATCHED_TIMESTAMPS_RETAINED",
                    helper_identity_relabelled=False,
                    helper_native_execution_identity=checker.EXECUTION_STABLE,
                    formal_or_scientific_admission=False, B_C_admission=False)
    except BaseException as error:
        acquisition.native._capture_read_failure(error, {"source": reader},
                                                 "independent_PUBLIC_R0", {})
        raise


def independent_r1(source, content, registry, producer_rows, closed, contract_sha, source_binding,
                   *, plan):
    modules, _anchors, _root, expected_source, expected_content = context(plan)
    checker = modules["p17_m2_input_export_independent"]
    acquisition = modules["p17_m2_source_acquisition_independent"]
    local = modules["p17_m2_local_input_independent"]
    need(Path(source) == expected_source and Path(content) == expected_content
         and contract_sha == plan["contract_sha256"]
         and source_binding == plan["public_source_identity"], "PUBLIC R1 arguments differ")
    checker.check_registry_shape(registry, plan["content_contract"])
    original = checker.OnceReader(source, 558, 852 * checker.MIB, source_identity_checks=True,
                                  source_identity_policy=POLICY)
    exports = checker.OnceReader(content, 1070, 301 * checker.MIB)
    readers = dict(source=original, exports=exports)
    source_before, content_before = root_identity(source), root_identity(content)
    need(content_before == closed["root_identity"], "PUBLIC closed content root differs")
    try:
        compared = checker.audit_exports(original, exports, registry)
        local.compare_identity_tables(original.observations, producer_rows, 558,
                                      source_identity_policy=POLICY)
        for rows in (original.observations, producer_rows):
            acquisition.check_expected_source_hashes(rows, registry, plan["content_contract"], "r1")
        constructor = local.base.OnceReader

        def observe(*args, **kwargs):
            reader = constructor(*args, **kwargs)
            readers["local_content"] = reader
            return reader

        local.base.OnceReader = observe
        checked = local.audit_local_content(content, closed["manifest"], registry,
                                            closed["local_identity_rows"], contract_sha)
        need(checked["version_id"] == closed["version_id"]
             and len(original.observations) == 558 and checked["new_member_reads"] == 1071
             and 95 * TARGET_BYTES <= 100 * original.used <= 105 * TARGET_BYTES
             and root_identity(source) == source_before
             and root_identity(content) == content_before,
             "PUBLIC workload size/count/version/closing roots differ")
        return dict(status="SOURCE_ACQUISITION_R1_CHECKED", execution_identity=IDENTITY,
                    scope=SCOPE,
                    source_root=str(source), root=str(content), root_identity=content_before,
                    source_count=558, source_rows=original.observations,
                    local_identity_rows=checked["local_identity_rows"],
                    source_registry_sha256=sha(checker.canonical(registry)),
                    manifest_sha256=sha(checker.canonical(closed["manifest"])),
                    version_id=checked["version_id"], contract_sha256=contract_sha,
                    source_identity=source_binding, public_source_identity=source_binding,
                    compared_fields=compared["compared_scalar_fields"],
                    source_bytes=original.used, new_member_reads=1071,
                    source_comparison="PREBOUND_HASH_AND_PHYSICAL_IDENTITY_MATCHED_TIMESTAMPS_RETAINED",
                    helper_identity_relabelled=False,
                    helper_native_execution_identity=checker.EXECUTION_STABLE,
                    formal_or_scientific_admission=False, B_C_admission=False,
                    resource_acceptance="EXTERNAL_NATIVE_SUP_REC_BIND_AND_ACTUAL_RETURN_REQUIRED")
    except BaseException as error:
        acquisition.native._capture_read_failure(error, readers, "independent_PUBLIC_R1", {})
        raise


def standalone_accepted_registry(plan):
    """Use the production same-buffer R0 Native gate before a standalone R1."""
    root, _source, _content = public_paths(plan)
    software(plan)
    loader = sys.modules["full60_input_loader"]
    name = "scripts/p17_m2_input_continuation.py"
    path = REPO / name
    raw = path.read_bytes()
    need(sha(raw) == plan["source_tree"][name], "PUBLIC profile buffer differs")
    profiles = loader.load("p17_m2_input_continuation", path)
    need(profiles.WINDOW_PUBLIC == IDENTITY, "standalone PUBLIC profile differs")
    control = profiles.profile("control", profiles.WINDOW_PUBLIC)
    transport = control.AcquisitionTransport(root, sha(canonical(plan)), scope=SCOPE)
    # read_registry audits the independent R0 native wire and binds this exact
    # read's bytes to its source_registry_sha256 before parsing and returning.
    return transport.read_registry(root, plan, "independent-r1")


def verify_public_role(plan, role, *, accepted_registry=None):
    """Payload-body adapter. It issues no command and claims no native acceptance."""
    need(role in ("independent-r0", "independent-r1"), "independent PUBLIC role required")
    root, source, content = public_paths(plan)
    if role == "independent-r0":
        need(accepted_registry is None, "PUBLIC accepted registry is only an R1 input")
        registry = parse(private_bytes(root / "registry.json", maximum=8 * 1024**2))
        return independent_r0(source, plan["content_contract"], registry,
            parse(private_bytes(root / "r0-source-rows.json")), plan["public_source_identity"],
            plan=plan)
    registry = (standalone_accepted_registry(plan) if accepted_registry is None
                else accepted_registry)
    need(type(registry) is dict, "same-buffer accepted PUBLIC registry must be an object")
    return independent_r1(source, content, registry,
        parse(private_bytes(root / "r1-source-rows.json")),
        parse(private_bytes(root / "closed.json")), plan["contract_sha256"],
        plan["public_source_identity"], plan=plan)


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plan-sha", required=True)
    parser.add_argument("--role", choices=("independent-r0", "independent-r1"), required=True)
    args = parser.parse_args()
    need(args.plan.name == "plan.json" and args.plan.parent in ROOTS,
         "literal PUBLIC plan path required before open")
    raw = private_bytes(args.plan)
    need(sha(raw) == args.plan_sha, "PUBLIC plan raw SHA differs")
    plan = parse(raw)
    root, _source, _content = public_paths(plan)
    need(root == args.plan.parent, "PUBLIC plan and file root disagree")
    return verify_public_role(plan, args.role)


if __name__ == "__main__":
    path = Path(__file__)
    raw = path.read_bytes()
    module = ModuleType("r1_window_public_runtime")
    module.__file__ = str(path)
    exec(compile(raw, str(path), "exec", dont_inherit=True), module.__dict__)
    module.MODULE_SOURCE_SHA256 = sha(raw)
    print(canonical(module.main()).decode(), end="")
