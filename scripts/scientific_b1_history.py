"""Verify the issued B1 version in its original software and clock domain."""

import contextlib
import hashlib
import importlib.machinery
import io
import json
import os
import stat
import sys
import tarfile
from operator import attrgetter
from pathlib import Path
from types import ModuleType

ROOT = Path("/Users/keith1117/Documents/TopoLab-data/receipt-20261126-b1")
HISTORY = Path("/private/tmp/topolab-receipt-20261126-b1")
PROTOCOL = "docs/planning/receipt_formal_contract.json"
COMMIT = "d30c33b198099c09ee9c1fb7bbc14f43f8cf1676"
PLAN = "d26d69bb62ff1488e12a52f2872f07ce00eac92eb4bd30413b53925411d4f739"
VERSION = "94e1ccdd7629cfbb697797da4235351c1fdefbcde8c40085dd0876ab3b6b23a7"
ARCHIVE = "ddf1e82cf29b1a49fe7605a503f398880a41c0dac38165543fff53d455c4ca7d"
INDEX = "b9aa939e17552868b2cc8c92bb9a6ae261c87a8b43bf1676675c908d0b76b237"
BUNDLE = "33c84cb2add06ee7877ca64c7928e2489eada34921be5505d60c151ea12f7687"
CERT_ACTUAL = "68cf5367db2753e90904a6bf167c46d2d2a09ed76d0936c4770b045d5e52e2c0"
CERT_STDOUT = "2b79796e837e9d93967a8bcbb802769a936157315dea22317c4de17c9e351455"
TERMINAL = "75b2e4a5f881f60c1d9cb1f2563ae64e87534fed337d16941102f25bf8a65b78"
REPORT = "2658d414ea12b7013ead703a00f298345b86234149d250edbe068614b36d5b78"
_issued = {}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def need(condition, message):
    if not condition:
        raise ValueError("B1 history: " + message)


def pinned_pair(name, expected):
    identity = attrgetter(
        "st_dev", "st_ino", "st_mode", "st_uid", "st_nlink", "st_size", "st_mtime_ns"
    )
    copies = []
    for root in (ROOT, ROOT.with_name(ROOT.name + "-backup")):
        path = root / name
        need(path.resolve(strict=True) == path, "aliased control path")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(fd, "rb") as stream:
            info = os.fstat(fd)
            need(
                stat.S_ISREG(info.st_mode)
                and stat.S_IMODE(info.st_mode) == 0o600
                and info.st_nlink == 1
                and info.st_uid == os.getuid()
                and 0 < info.st_size <= 16 * 1024**2,
                "invalid control " + name,
            )
            raw = stream.read(info.st_size + 1)
            need(
                len(raw) == info.st_size
                and digest(raw) == expected
                and identity(info)
                == identity(os.fstat(fd))
                == identity(path.stat(follow_symlinks=False)),
                "sealed control changed: " + name,
            )
            copies.append(((info.st_dev, info.st_ino), raw))
    need(copies[0][0] != copies[1][0] and copies[0][1] == copies[1][1], "control pair differs")
    return copies[0][1]


def sealed_controls():
    index = json.loads(pinned_pair("formal-a1-index.json", INDEX))
    wanted = {
        "native/plan.json",
        "native/lease-release.json",
        "native/accepted-acquisition-bundle.json",
        "caller/receipt-formal-producer-producer-certificate-actual.json",
    }
    selected = {}
    with tarfile.open(
        fileobj=io.BytesIO(pinned_pair("formal-a1-controls.tar.gz", ARCHIVE)), mode="r|gz"
    ) as archive:
        for member in archive:
            if member.name not in wanted:
                continue
            spec = index[member.name]
            need(
                member.name not in selected
                and member.isfile()
                and member.size == spec["bytes"]
                and 0 < member.size <= 16 * 1024**2,
                "invalid archive member",
            )
            raw = archive.extractfile(member).read()
            need(len(raw) == member.size and digest(raw) == spec["sha256"], "member differs")
            selected[member.name] = raw
    need(set(selected) == wanted, "missing archive member")
    return selected


@contextlib.contextmanager
def historical_modules(plan):
    """Use source-only historical imports without reusing scientific module caches."""
    tree = plan["source_tree"]
    need(
        plan["runtime"]["cwd"] == str(HISTORY)
        and all(digest((HISTORY / k).read_bytes()) == v for k, v in tree.items()),
        "issuance software tree differs",
    )
    scripts = HISTORY / "scripts"
    names = {Path(k).stem for k in tree if k.startswith("scripts/") and k.endswith(".py")}
    original_modules = sys.modules.copy()
    original_path = sys.path[:]
    previous_loader = importlib.machinery.SourceFileLoader.get_code
    previous_bytecode = sys.dont_write_bytecode
    try:
        for name in list(sys.modules):
            if name in names or name.endswith("_receipt_formal_20261126_b1"):
                del sys.modules[name]
        sys.path.insert(0, str(scripts))
        path = scripts / "full60_input_loader.py"
        raw = path.read_bytes()
        need(digest(raw) == tree["scripts/full60_input_loader.py"], "historical loader differs")
        loader = ModuleType("full60_input_loader")
        loader.__file__ = str(path)
        sys.modules[loader.__name__] = loader
        exec(compile(raw, str(path), "exec", dont_inherit=True), loader.__dict__)
        loader.loaded_source_sha256[str(path)] = digest(raw)
        loader.install()
        paired = loader.load(
            "paired_readiness_independent", scripts / "paired_readiness_independent.py"
        )
        need(paired.checkout_commit(HISTORY) == COMMIT, "issuance checkout commit differs")
        yield loader, paired
        for filename, used_digest in loader.loaded_source_sha256.items():
            file = Path(filename)
            if file.is_relative_to(scripts):
                need(
                    tree.get(str(file.relative_to(HISTORY))) == used_digest,
                    "executed historical source differs",
                )
    finally:
        importlib.machinery.SourceFileLoader.get_code = previous_loader
        sys.dont_write_bytecode = previous_bytecode
        sys.path[:] = original_path
        for name, module in list(sys.modules.items()):
            filename = getattr(module, "__file__", None)
            if isinstance(filename, str) and Path(filename).is_relative_to(scripts):
                sys.modules.pop(name)
        for name, module in original_modules.items():
            if name in names or name.endswith("_receipt_formal_20261126_b1"):
                sys.modules[name] = module


def inspect(plan_sha, version, *, issue=False):
    need((plan_sha, version) == (PLAN, VERSION), "different acquisition plan or version")
    files = sealed_controls()
    plan_raw = files["native/plan.json"]
    plan = json.loads(plan_raw)
    need(digest(plan_raw) == PLAN, "sealed plan differs")
    actual_raw = files["caller/receipt-formal-producer-producer-certificate-actual.json"]
    need(digest(actual_raw) == CERT_ACTUAL, "certificate original differs")
    packet_raw = files["native/accepted-acquisition-bundle.json"]
    need(digest(packet_raw) == BUNDLE, "accepted bundle differs")
    terminal_raw = pinned_pair("terminal-audit-2-actual.json", TERMINAL)
    terminal = json.loads(terminal_raw)
    report = json.loads(pinned_pair("independent-terminal-audit-a2.json", REPORT))
    with historical_modules(plan) as (loader, paired):
        policy = json.loads((HISTORY / PROTOCOL).read_bytes())
        evidence = ROOT.with_name(ROOT.name + "-formal")
        captured = paired.capture(policy, plan["source_tree"], PROTOCOL, HISTORY, evidence)
        ready_raw, readiness, _ = captured
        original, _ = paired.pair(evidence, paired.ORIGINAL)
        paired.validate_preflight(
            policy, HISTORY, "receipt_formal_registered.py", captured, json.loads(original)
        )
        need(digest(ready_raw) == plan["activation_readiness"]["sha256"], "readiness differs")
        actual = json.loads(actual_raw)
        argv = [
            plan["runtime"]["python"],
            "-I",
            str(HISTORY / "scripts/receipt_formal_control.py"),
            "certify-input-version",
            "--root",
            plan["root"],
            "--plan-sha",
            PLAN,
            "--role",
            "certificate",
        ]
        first, last, output = paired.terminal(
            actual,
            argv,
            cwd=str(HISTORY),
            full=None,
            window=(plan["whole_start_ms"], plan["whole_end_ms"]),
        )
        terminal_result = terminal["responses"][-1]["result"]
        need(
            type(terminal_result.get("exit_code")) is int
            and terminal_result["exit_code"] == 0
            and json.loads(terminal_result["output"])
            == {
                "report": "independent-terminal-audit-a2.json",
                "report_sha256": REPORT,
                "status": "PASS_COMPLETE_FORMAL_INPUT_TERMINAL",
            }
            and report["accepted_count"] == 6
            and report["archive_sha256"] == ARCHIVE
            and report["index_sha256"] == INDEX
            and report["plan_sha256"] == PLAN
            and report["certificate_summary"] == json.loads(output)
            and digest(output) == CERT_STDOUT
            and report["certificate"]
            == {
                "exit_code": 0,
                "first_ms": first,
                "last_ms": last,
                "state": "TERMINAL",
                "stdout_sha256": CERT_STDOUT,
            }
            and report["lease"] == json.loads(files["native/lease-release.json"])
            and report["lease"]["state"] == "RELEASED"
            and report["lease"]["version_id"] == VERSION
            and report["compared_input"]
            == dict(
                complete_views=5,
                members=1071,
                metadata_each=40,
                payloads_each=558,
                version_id=VERSION,
            ),
            "archived certificate, terminal audit or lease differs",
        )
        summary = dict(
            issuer_main=COMMIT,
            plan_sha256=PLAN,
            version_id=VERSION,
            certificate_original_sha256=CERT_ACTUAL,
            certificate_stdout_sha256=CERT_STDOUT,
            certificate_exit=0,
            archive_sha256=ARCHIVE,
            archive_index_sha256=INDEX,
            independent_terminal_sha256=TERMINAL,
            lease="RELEASED",
            certificate_start_ms=first,
            certificate_end_ms=last,
            readiness=readiness,
            readiness_sha256=digest(ready_raw),
        )
        if not issue:
            return summary
        profiles = loader.load(
            "p17_m2_input_continuation", HISTORY / "scripts/p17_m2_input_continuation.py"
        )
        issuer = profiles.profile("independent", profiles.RECEIPT_FORMAL)
        control = profiles.profile("control", profiles.RECEIPT_FORMAL)
        packet = control.base().evidence_json(json.loads(packet_raw), decode=True)
        need(
            packet["bundle"]["plan"] == plan and packet["bundle"]["version_id"] == VERSION,
            "bundle plan or version differs",
        )
        certificate = issuer.audit_certificate(
            packet["bundle"], trusted_tool_events=packet["events"]
        )
        binding = certificate._binding
        need(
            type(certificate) is issuer.CheckedAcquisitionInput
            and binding["plan_sha256"] == PLAN
            and binding["version_id"] == VERSION
            and binding["B_C_admission"] is False
            and binding["source_input_accepted"] is True
            and binding["formal_authority"] is True,
            "historical issuer did not return the certified restricted version",
        )
    _issued[id(certificate)] = certificate, issuer, digest(canonical(binding))
    return certificate


def verify_certificate(plan_sha, version_sha):
    return inspect(plan_sha, version_sha, issue=True)


def historical_issuer(certificate):
    record = _issued.get(id(certificate))
    if record is None or record[0] is not certificate:
        return None
    _, issuer, expected = record
    need(
        type(certificate) is issuer.CheckedAcquisitionInput
        and digest(canonical(certificate._binding)) == expected,
        "issued capability changed",
    )
    return issuer
