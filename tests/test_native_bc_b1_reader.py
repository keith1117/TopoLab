"""Exercise grant and lease operations with private files containing only public fixture names."""

import importlib.util
import json
import os
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
PRODUCER = "scientific-producer"
AUDITOR = "scientific-auditor"
PUBLIC_HASH = "1" * 64


def public_reader_case(tmp_path, monkeypatch):
    entry = SCRIPTS / "p17_m2_scientific_orchestration.py"
    spec = importlib.util.spec_from_file_location("public_reader_orchestration", entry)
    orchestration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orchestration)
    science = orchestration.load("p17_m2_scientific_independent")
    acquisition = science.acquisition
    parent = tmp_path.resolve() / "topolab-public-formal-binding-reader"
    parent.mkdir(mode=0o700)
    root = parent / "content"
    root.mkdir(mode=0o700)
    models = [
        f"checkpoints/{family}-{seed}.safetensors"
        for family in ("C", "P", "W", "S")
        for seed in (17, 29, 43)
    ]
    labels = [f"nn/producer/tlcase-v1-{i:064x}.json" for i in range(528)]
    audit_labels = [name.replace("/producer/", "/audit/") for name in labels]
    views = {
        PRODUCER: sorted([*models, "models.json", *labels]),
        AUDITOR: sorted([*models, "models.json", *labels, *audit_labels]),
        "reference-compatibility": ["uniform-scalars.json"],
    }
    members, identities = [], []
    groups = [
        ("checkpoint", models),
        ("models", ["models.json"]),
        ("nn-producer", labels),
        ("nn-audit", audit_labels),
        ("uniform-scalars", ["uniform-scalars.json"]),
    ]
    for kind, names in groups:
        for name in names:
            raw = name.encode("ascii")
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(raw)
            member = {"path": name, "byte_size": len(raw), "sha256": science.digest(raw)}
            physical = acquisition.native._physical(path.stat())
            identities.append(
                {**member, **dict.fromkeys(("declared", "before", "after", "closing"), physical)}
            )
            members.append({**member, "type": kind})
    manifest = {"members": members, "role_views": views}
    version = science.digest(science.canonical(manifest))
    plan = {
        "execution_identity": "test-rehearsal-only",
        "scope": acquisition.REHEARSAL_SCOPE,
        "formal_authority": False,
        "root": str(parent),
        "content_root": str(root),
    }
    binding = {
        "root": str(root),
        "root_identity": acquisition.native._physical(root.stat()),
        "plan_sha256": science.digest(science.canonical(plan)),
        "verified_plan": plan,
        "contract_sha256": PUBLIC_HASH,
        "shared_packet_sha256": PUBLIC_HASH,
        "version_id": version,
        "scope": acquisition.REHEARSAL_SCOPE,
        "manifest": manifest,
        "local_identity_rows": identities,
        "role_views": views,
    }
    certificate = acquisition.CheckedAcquisitionInput(
        binding, _authority=acquisition._ACQUISITION_AUTHORITY
    )
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        monkeypatch.setenv(key, "1")
    runtime = orchestration.scientific_runtime()
    # The test process performs the actual public read. Freeze its observed argv.
    command = [runtime["python_entry"], *sys.orig_argv[1:]]
    actions = {"consume": command, "ack": command}
    sources = [
        "p17_m2_scientific_control.py",
        "p17_m2_scientific_independent.py",
        "p17_m2_scientific_orchestration.py",
        "p17_m2_independent_audit.py",
    ]
    contract = {
        "entry_repair": "native-bc-entry-20261126-r2",
        "public_fixture_only": True,
        "schema": "topolab.v2.m2-scientific-contract.v1",
        "execution_identity": science.IDENTITY,
        "permissions": {"B": True, "C": True},
        "resource_limit_bytes": 4294967296,
        "source_freeze": {
            "scripts/" + name: science.digest((SCRIPTS / name).read_bytes()) for name in sources
        },
        "runtime": runtime,
        "proposal_sha256": science.digest(
            (SCRIPTS.parent / "docs/planning" / "p17_m2_native_homotopy_proposal.json").read_bytes()
        ),
        "independent_operation_caps": dict(science.OPERATIONS),
        "acquisition": {
            "plan_sha256": binding["plan_sha256"],
            "version_id": version,
            "manifest_sha256": version,
            "content_root": str(root),
            "shared_packet_sha256": PUBLIC_HASH,
        },
        "input_version_id": version,
        "reader_actions": {PRODUCER: actions, AUDITOR: actions},
        "input_role_views": {
            role: [*views[role], "uniform-scalars.json"] for role in (PRODUCER, AUDITOR)
        },
    }
    return science, certificate, contract


def public_admission(science, contract):
    """Isolate the grant under test. These synthetic facts confer no formal input authority."""
    assert contract["public_fixture_only"] is True
    digest = science.check_contract(contract)
    proof = {
        "status": "PASS_PREFLIGHT_RSS_EXIT_EMPIRICAL",
        "role": "resource-preflight",
        "scientific_contract_sha256": digest,
        "actual_final_verifier_exit_observed": True,
        "b_caller_return_sha256": PUBLIC_HASH,
    }
    return science.CheckedBAdmission(digest, proof, _authority=science._SCIENCE_AUTHORITY)


@pytest.mark.parametrize(("role", "count"), [(PRODUCER, 542), (AUDITOR, 1070)])
def test_public_role_reads_exact_view_through_bound_lease(tmp_path, monkeypatch, role, count):
    science, certificate, contract = public_reader_case(tmp_path, monkeypatch)
    permission = science.grant_scientific_input(
        certificate, contract, role, public_admission(science, contract)
    )
    reader = science.helper("p17_m2_source_verified_input").VerifiedAcquisitionInput
    with pytest.raises(ValueError, match="opaque reader lease"):
        reader(permission, role, reader_lease={"state": "HELD"})
    lease = permission.acquire_reader(role)
    other = AUDITOR if role == PRODUCER else PRODUCER
    with pytest.raises(ValueError, match="lease"):
        reader(permission, other, reader_lease=lease)

    actual = reader(permission, role, reader_lease=lease)
    assert len(contract["input_role_views"][role]) == count
    for name in contract["input_role_views"][role]:
        assert actual.consume(name, lambda raw: raw.decode("ascii")) == name
    assert len(actual.reader.source_observations) == count
    assert actual.reader.source_observations[-1]["path"] == "uniform-scalars.json"
    print(
        json.dumps(
            {
                "scope": "public reader fixture",
                "role": role,
                "opened": count,
                "physical_identity_sha256_matches": len(actual.reader.source_observations),
                "uniform_scalar_reads": sum(
                    row["path"] == "uniform-scalars.json"
                    for row in actual.reader.source_observations
                ),
                "formal_payload_reads": 0,
                "B_prerequisite": "synthetic public unit fixture",
            }
        )
    )
    lease.pending_return()
    with pytest.raises(ValueError, match="lease"):
        actual.consume(
            "uniform-scalars.json", lambda raw: pytest.fail("expired lease delivered bytes")
        )


def test_public_consumer_denies_outside_its_role_before_read(tmp_path, monkeypatch):
    science, certificate, contract = public_reader_case(tmp_path, monkeypatch)
    grant = science.grant_scientific_input(
        certificate, contract, PRODUCER, public_admission(science, contract)
    )
    lease = grant.acquire_reader(PRODUCER)
    consumer = science.helper("p17_m2_source_verified_input").VerifiedAcquisitionInput(
        grant, PRODUCER, reader_lease=lease
    )
    audit_only = next(
        name for name in contract["input_role_views"][AUDITOR] if name.startswith("nn/audit/")
    )
    with pytest.raises(ValueError, match="ROLE_VIEW_DENIED"):
        consumer.consume(audit_only, lambda raw: pytest.fail("wrong role received bytes"))
    assert consumer.reader.attempts == []


def test_public_and_formal_input_authorities_are_disjoint(tmp_path, monkeypatch):
    science, certificate, contract = public_reader_case(tmp_path, monkeypatch)
    admission = public_admission(science, contract)
    reader = science.helper("p17_m2_source_verified_input")
    with pytest.raises(ValueError, match="actual checked B"):
        science.grant_scientific_input(certificate, contract, PRODUCER, {"status": "PASS"})
    proof = deepcopy(admission.proof)
    proof.pop("b_caller_return_sha256")
    native_only = science.CheckedBAdmission(
        admission.contract_sha256, proof, _authority=science._SCIENCE_AUTHORITY
    )
    with pytest.raises(ValueError, match="complete same-contract B"):
        science.grant_scientific_input(certificate, contract, PRODUCER, native_only)
    native_only.proof["b_caller_return_sha256"] = PUBLIC_HASH
    with pytest.raises(ValueError, match="complete same-contract B"):
        science.grant_scientific_input(certificate, contract, PRODUCER, native_only)
    for field in ("plan_sha256", "version_id"):
        changed = deepcopy(contract)
        changed["acquisition"][field] = "8" * 64
        with pytest.raises(ValueError, match="another contract"):
            science.grant_scientific_input(certificate, changed, PRODUCER, admission)
        with pytest.raises(ValueError, match="accepted input identity differs"):
            science.grant_scientific_input(
                certificate, changed, PRODUCER, public_admission(science, changed)
            )
    with pytest.raises(ValueError, match="independently accepted acquisition"):
        science.grant_scientific_input({"status": "PASS"}, contract, PRODUCER, admission)
    forged_type = type("CheckedAcquisitionInput", (), {"__module__": reader.B1_ISSUER_MODULE})
    assert reader.checked_acquisition_issuer(forged_type(), science.acquisition) is None
    with monkeypatch.context() as isolated:
        impostor = ModuleType("scientific_b1_history")
        impostor.__file__ = str(SCRIPTS / "scientific_b1_history.py")
        impostor.historical_issuer = lambda obj: science.acquisition
        isolated.setitem(sys.modules, impostor.__name__, impostor)
        assert reader.checked_acquisition_issuer(forged_type(), science.acquisition) is None
    # Even a current opaque test certificate cannot pass as a B1 historical issuer.
    certificate._binding["verified_plan"]["execution_identity"] = reader.B1_IDENTITY
    with pytest.raises(ValueError, match="public grant cannot use B1"):
        science.grant_scientific_input(certificate, contract, PRODUCER, admission)
    legacy = dict(contract)
    del legacy["entry_repair"]
    with pytest.raises(ValueError, match="B1 scientific contract required"):
        science.grant_scientific_input(
            certificate, legacy, PRODUCER, public_admission(science, legacy)
        )
    formal = dict(contract, public_fixture_only=False)
    with pytest.raises(ValueError, match="another contract"):
        science.grant_scientific_input(certificate, formal, PRODUCER, admission)
    assert (
        not Path(certificate._binding["root"])
        .with_name("content.cooperative-reader.lease")
        .exists()
    )

@pytest.mark.parametrize("live", [False, True])
def test_successor_preserves_stopped_lease_and_serializes_roles(tmp_path, monkeypatch, live):
    science, certificate, contract = public_reader_case(tmp_path, monkeypatch)
    root = Path(contract["acquisition"]["content_root"])
    old = root.with_name(root.name + ".cooperative-reader.lease")
    if live:
        pid = os.getpid()
    else:
        process = subprocess.Popen([sys.executable, "-I", "-c", "pass"])
        pid = process.pid
        assert process.wait(timeout=10) == 0
    raw = science.canonical({"root": str(root), "lease_path": str(old), "consumer_pid": pid})
    with old.open("xb") as stream:
        os.fchmod(stream.fileno(), 0o600)
        stream.write(raw)
    identity = science.acquisition.native._physical(old.stat())
    contract.update(attempt_id="native-bc-entry-20261127-r3", retained_reader={
        "record_sha256": science.digest(raw),
        "identity_sha256": science.digest(science.canonical(identity)),
    })
    def grant(role):
        return science.grant_scientific_input(
            certificate, contract, role, public_admission(science, contract)
        )
    producer = grant(PRODUCER)
    if live:
        with pytest.raises(ValueError, match="process still present"):
            producer.acquire_reader(PRODUCER)
        assert not root.with_name(root.name + ".r3.cooperative-reader.lease").exists()
    else:
        lease = producer.acquire_reader(PRODUCER)
        assert Path(lease.path) == root.with_name(root.name + ".r3.cooperative-reader.lease")
        with pytest.raises(ValueError, match="already held"):
            grant(AUDITOR).acquire_reader(AUDITOR)
        assert lease.pending_return()["lease_path"] == lease.path
        old.write_bytes(raw.replace(b"consumer_pid", b"consumer_pIx"))
        with pytest.raises(ValueError, match="identity changed"):
            producer._reader_lease_path(root)
        return
    assert old.read_bytes() == raw and science.acquisition.native._physical(old.stat()) == identity
