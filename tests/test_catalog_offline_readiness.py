"""The offline acceptance gate consumes only fixed paired records and the I-owned return."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def verifier():
    path = ROOT / "scripts/catalog_input_offline.py"
    spec = importlib.util.spec_from_file_location("catalog_replay", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_offline_return_binds_proof_raw_receipts_and_publication(verifier, monkeypatch):
    m = verifier
    w = m.independent_wire()
    slot, first = 3, m.START + 10
    argv = m.verify_args(slot)
    policy = dict(
        execution_identity=m.IDENTITY,
        catalog_verification_paths=dict(package=str(m.E / m.PACKAGE), actual=str(m.E / m.ACTUAL)),
        new_input_budget=dict(path=str(m.E / "owner-budget-registration.json"), sha256=m.BUDGET),
    )
    tree = {
        "scripts/r0_read_independent.py": w.compiled_sha256,
        m.PROTOCOL: "b" * 64,
        m.WORKER: m.MODULE_SOURCE_SHA256,
        m.CHECKER: "c" * 64,
    }
    claim = dict(
        schema="topolab.catalog-offline-claim.v1",
        slot=slot,
        actor=m.AUTHOR,
        argv=argv,
        repo=str(m.REPO),
        source_main="d" * 40,
        worker_sha256=tree[m.WORKER],
        charge_FULL=300,
        budget_sha256=m.BUDGET,
        claimed_ms=first - 2,
    )
    entry = dict(slot=slot, started_ms=first + 1, claim_sha256=m.sha(w.canonical(claim)))
    proof = dict(
        archive_sha256=m.ARCHIVE,
        previous_unit_actual_sha256=m.UNIT_ACTUAL,
        compared_independent_refs=7,
        exporter_registry_refs=40,
        original_bootstrap_buffers_replayed=0,
        original_metadata_buffers_replayed=1,
        public_catalog_entries=752,
        sealed_train_entries_compared=528,
        full_public_catalog_sha256=m.FULL_CATALOG,
        constructed_fit_sha256=m.FIXTURE_FIT,
        expected_catalog_identity=m.CATALOG,
        new_original_reads=0,
        b3_entry="ACCEPTED_B3_SECTION",
        identity_mutation=dict(
            identity_sha256="f" * 64, outcome="embedded manifest/catalog differs"
        ),
        nonidentity_mutation=dict(
            identity_sha256=m.CATALOG,
            new_raw_sha256="e" * 64,
            outcome="ACCEPTED_B3_SECTION",
            old_raw_pin_rejected="source SHA differs",
        ),
    )
    report = dict(
        schema="topolab.catalog-offline-report.v1",
        status=m.SUCCESS,
        slot=slot,
        execution_identity=m.IDENTITY,
        budget_sha256=m.BUDGET,
        repo=str(m.REPO),
        authority_sha256=tree[m.PROTOCOL],
        worker_sha256=tree[m.WORKER],
        checker_sha256=tree[m.CHECKER],
        source_main=claim["source_main"],
        claim_sha256=entry["claim_sha256"],
        entered_sha256=m.sha(w.canonical(entry)),
        started_ms=first + 1,
        ended_ms=first + 2,
        self_rss_bytes=1000,
        proof=proof,
    )
    raw = w.canonical(report)
    request = dict(workdir=str(m.REPO), cmd=w.literal_command(argv))
    actual = dict(
        schema=w.ACTUAL_SCHEMA,
        author=m.AUTHOR,
        argv=argv,
        request=request,
        responses=[
            dict(
                tool="exec_command",
                arguments=request,
                requested_ms=first,
                returned_ms=first + 3,
                result=dict(
                    output=w.canonical(m.verify_return(slot, m.sha(raw))).decode(), exit_code=0
                ),
            )
        ],
    )
    records = {
        m.PACKAGE: raw,
        "offline-03-report.json": raw,
        m.ACTUAL: w.canonical(actual),
        "offline-03-actual.json": w.canonical(actual),
        "offline-03-claim.json": w.canonical(claim),
        "offline-03-entered.json": w.canonical(entry),
        "owner-budget-registration.json": b"public fixture",
    }
    monkeypatch.setattr(m, "pair", lambda root, name, expected=None: records[name])
    assert m.verified_readiness(policy, tree)["verified_returned_ms"] == first + 3
    with pytest.raises(ValueError):
        m.verified_readiness(policy, tree | {m.CHECKER: "0" * 64})
    records["offline-03-actual.json"] += b" "
    with pytest.raises(ValueError, match="original slot"):
        m.verified_readiness(policy, tree)
    records[m.ACTUAL] = records["offline-03-actual.json"] = w.canonical(
        actual | {"author": "/root"}
    )
    with pytest.raises(ValueError, match="actor/argv"):
        m.verified_readiness(policy, tree)
    with pytest.raises(ValueError, match="coverage differs"):
        m.validate_proof(proof | {"original_bootstrap_buffers_replayed": 7})
    with pytest.raises(ValueError, match="mutation controls"):
        m.validate_proof(
            proof
            | {
                "nonidentity_mutation": proof["nonidentity_mutation"]
                | {"old_raw_pin_rejected": "ACCEPTED_B3_SECTION"}
            }
        )


def test_replaced_source_rejected_before_execution(verifier, tmp_path):
    path = tmp_path / "sample.py"
    path.write_bytes(b"answer = 1\n")
    expected = verifier.sha(path.read_bytes())
    assert verifier.module(path, expected).answer == 1
    path.write_bytes(b"raise RuntimeError('unexpected execution')\n")
    with pytest.raises(ValueError, match="compiled source SHA differs"):
        verifier.module(path, expected)
