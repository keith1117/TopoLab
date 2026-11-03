"""Independent strict first registration; semantic checks grant no native authority.

Only newly authorized exact metadata may be read. This module persists no source
buffers and never fills a missing expected hash from a failed observation.
"""

import hashlib
import importlib.util
import json
import re
from copy import deepcopy
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CONTENT_CONTRACT = "docs/planning/p17_m2_input_export_preparation_proposal.json"
CONTENT_SHA256 = "f2ed2a971e9a3d76e0d5fba6123080b94feaf5dad384a1a8cad4ca4c3a43f1ad"
IDENTITY = "topolab.v2.p17-source-binding-and-conditional-repair.20261103.v1"
SCHEMA = "topolab.v2.m2-strict-source-binding.read.v1"
CONTEXT_KEYS = (
    "execution_identity", "scope", "attempt", "source_root", "authority_sha256",
    "source_tree", "actors",
)
SHA = re.compile(r"[0-9a-f]{64}")
ACTORS = {"producer": "/root", "independent": "/root/binding_route_independent_v1"}
SCOPES = ("PUBLIC_STRICT_BINDING_REGISTRATION_ONLY", "FORMAL_STRICT_BINDING_REGISTRATION_ONLY")
PHYSICAL_KEYS = {"st_dev", "st_ino", "st_size", "st_mtime_ns"}
WIRE_KEYS = set(CONTEXT_KEYS) | {
    "schema", "role", "author", "rows", "attempts", "failures",
    "helper_execution_identity", "helper_identity_relabelled",
    "source_identity_policy", "pre_read_expected_sha256",
}


def require(ok, reason):
    if not ok:
        raise ValueError("STOP: " + reason)


def metadata_specs():
    """Derive the23 literal sources from the existing frozen content authority."""
    raw = (REPO / CONTENT_CONTRACT).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == CONTENT_SHA256, "frozen content contract differs")
    r0 = json.loads(raw)["R0"]
    bootstrap = [
        {"path": row["relative_path"], "max_bytes": row["max_bytes"]}
        for row in r0["literal_bootstrap_files"] if row["expected_sha256"] is None
    ]
    additional = r0["bounded_additional_metadata"]
    require(len(bootstrap) == 2 and len(additional["W_units"]) == 3
            and len(additional["reference_units"]) == 18, "exact23 source groups differ")
    specs = bootstrap + [
        {"path": path, "max_bytes": 32768}
        for path in additional["W_units"] + additional["reference_units"]
    ]
    require(len({row["path"] for row in specs}) == 23, "exact23 source paths differ")
    return specs


def reader_module():
    path = REPO / "scripts/p17_m2_input_export_independent.py"
    spec = importlib.util.spec_from_file_location("strict_binding_once_reader", path)
    require(spec is not None and spec.loader is not None, "independent reader unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _context(context):
    require(isinstance(context, dict) and set(context) == set(CONTEXT_KEYS),
            "registration context keys differ")
    require(context["execution_identity"] == IDENTITY and context["scope"] in SCOPES
            and type(context["attempt"]) is int and context["attempt"] in (1, 2)
            and context["actors"] == ACTORS, "registration identity/scope/actors differ")
    root = context["source_root"]
    require(isinstance(root, str) and Path(root).is_absolute()
            and str(Path(root)) == root and ".." not in Path(root).parts,
            "registration source root is not literal")
    require(isinstance(context["authority_sha256"], str)
            and SHA.fullmatch(context["authority_sha256"]) is not None,
            "registration authority hash differs")
    tree = context["source_tree"]
    require(isinstance(tree, dict) and bool(tree) and all(
        isinstance(path, str) and path and not Path(path).is_absolute()
        and str(Path(path)) == path and ".." not in Path(path).parts
        and isinstance(value, str) and SHA.fullmatch(value) is not None
        for path, value in tree.items()), "registration source tree differs")


def _wire(wire, context, role):
    require(isinstance(wire, dict) and set(wire) == WIRE_KEYS,
            "registration wire keys differ")
    _context({key: wire[key] for key in CONTEXT_KEYS})
    require(wire["schema"] == SCHEMA and all(wire[key] == context[key] for key in CONTEXT_KEYS)
            and wire["role"] == role and wire["author"] == ACTORS[role],
            "registration wire context/role/author differs")
    helpers = (("topolab.v2.p17-m2-local-input-version.v1",) if role == "producer" else
               ("topolab.v2.p17-m2-source-stable-export.v1",))
    require(wire["helper_execution_identity"] in helpers
            and wire["helper_identity_relabelled"] is False
            and wire["source_identity_policy"] is None
            and wire["pre_read_expected_sha256"] is None and wire["failures"] == [],
            "registration strict helper or failure status differs")
    specs = metadata_specs()
    paths = [row["path"] for row in specs]
    require(wire["attempts"] == paths and isinstance(wire["rows"], list)
            and len(wire["rows"]) == 23, "registration exact23 attempts/rows differ")
    for row, spec in zip(wire["rows"], specs, strict=True):
        require(isinstance(row, dict) and set(row) == {
            "path", "byte_size", "sha256", "declared", "before", "after", "closing"},
            "registration row fields differ")
        require(row["path"] == spec["path"] and type(row["byte_size"]) is int
                and 0 < row["byte_size"] <= spec["max_bytes"]
                and isinstance(row["sha256"], str) and SHA.fullmatch(row["sha256"]) is not None,
                "registration source path/size/hash differs")
        for stage in ("declared", "before", "after", "closing"):
            physical = row[stage]
            require(isinstance(physical, dict) and set(physical) == PHYSICAL_KEYS
                    and all(type(value) is int for value in physical.values())
                    and physical["st_dev"] >= 0 and physical["st_ino"] > 0
                    and physical["st_size"] == row["byte_size"],
                    "registration physical observation missing or invalid")
        require(row["declared"] == row["before"] == row["after"] == row["closing"],
                "registration strict identity changed")


def validate_pair(primary, independent, context):
    """Return semantic bindings ONLY; the caller must separately audit native evidence."""
    _context(context)
    _wire(primary, context, "producer")
    _wire(independent, context, "independent")
    require(primary["rows"] == independent["rows"],
            "registration independent content/physical observations differ")
    return {row["path"]: {"byte_size": row["byte_size"], "sha256": row["sha256"]}
            for row in independent["rows"]}


def register(source, context, primary=None):
    """Read each admitted source once, with all strict closing observations.

    The caller enforces published authority, resource and actual native returns.
    This result alone is not a pre-read binding certificate or source admission.
    """
    frozen, reader, attempts, stage = deepcopy(context), None, [], "context_validation"
    try:
        _context(frozen)
        require(str(source) == frozen["source_root"], "registration actual source root differs")
        require(primary is not None or frozen["scope"] == SCOPES[0],
                "formal independent registration requires producer evidence")
        stage = "producer_evidence_before_source_io"
        if primary is not None:
            _wire(primary, frozen, "producer")
        checker = reader_module()
        specs = metadata_specs()
        reader = checker.OnceReader(
            Path(source), 23, sum(row["max_bytes"] for row in specs),
            source_identity_checks=True, source_identity_policy=None,
        )
        stage = "strict_source_read"
        for row in specs:
            attempts.append(row["path"])
            reader.packet(row["path"], row["max_bytes"])
        wire = {
            "schema": SCHEMA, **frozen,
            "role": "independent", "author": frozen["actors"]["independent"],
            "rows": reader.observations, "attempts": attempts, "failures": reader.failures,
            "helper_execution_identity": checker.EXECUTION_STABLE,
            "helper_identity_relabelled": False,
            "source_identity_policy": None, "pre_read_expected_sha256": None,
        }
        stage = "independent_semantic_validation"
        _wire(wire, frozen, "independent")
        if primary is not None:
            validate_pair(primary, wire, frozen)
        return wire
    except BaseException as error:
        failures = [] if reader is None else reader.failures
        chain, seen, current = [], set(), error
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            chain.append({"type": type(current).__name__, "reason": str(current)})
            current = current.__cause__ if current.__cause__ is not None else current.__context__
        error.strict_binding_failure = {
            "schema": "topolab.v2.m2-strict-source-binding.failure.v1",
            "context": frozen, "status": "STOP_NO_RETRY", "stage": stage,
            "attempts": attempts, "rows": [] if reader is None else reader.observations,
            "source_facts": {} if reader is None else reader.source_facts,
            "source_failures": failures,
            "primary_error": chain[-1], "raised_error": chain[0],
            "exception_chain_raised_to_origin": chain,
            "exception_chain_cycle": current is not None,
            "secondary_errors": list(reversed(chain[:-1])) + [
                {"type": "RecordingError", "reason": row["recording_error"]}
                for row in failures if row.get("recording_error")],
            "source_identity_policy": None, "pre_read_expected_sha256": None,
            "native_resources_and_cost": "SEPARATE_ACTUAL_OUTER_EVIDENCE_REQUIRED",
        }
        raise
