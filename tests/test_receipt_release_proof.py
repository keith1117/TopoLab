"""Synthetic controls for separation of diagnostic and formally released receipt evidence."""

import importlib
from pathlib import Path

import pytest


@pytest.fixture
def proof(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("receipt_release_proof")


@pytest.mark.parametrize("candidate", [False, True])
def test_candidate_cannot_be_relabelled_as_released(proof, monkeypatch, candidate):
    main = "4" * 40
    monkeypatch.setattr(proof, "checkout_commit", lambda _repo: main)
    entry = dict(
        slot=2,
        execution_identity=proof.IDENTITY,
        charge_FULL=300,
        budget_sha256=proof.BUDGET,
        argv=proof.argv_for(2, candidate=candidate),
        author=proof.AUTHOR,
        source_main=main,
        purpose="CANDIDATE_HISTORICAL_REPLAY_ONLY" if candidate else "RELEASED_PROOF",
        public_source_main=main,
        worker_sha256="9" * 64,
        start_ms=1000,
        end_ms=291000,
        public_slots=list(range(3, 10)),
    )
    tree = {proof.WORKER: entry["worker_sha256"]}
    policy = dict(independent_author_start_ms=1000, global_deadline_ms=500000)
    monkeypatch.setattr(proof, "pair", lambda *_: proof.canonical(entry))
    assert proof.reservation(2, policy, tree, candidate=candidate)[0] == entry
    with pytest.raises(ValueError, match="reservation differs"):
        proof.reservation(2, policy, tree, candidate=not candidate)
    entry["public_source_main"] = "5" * 40
    if candidate:
        assert proof.reservation(2, policy, tree, candidate=True)[0] == entry
    else:
        with pytest.raises(ValueError, match="reservation differs"):
            proof.reservation(2, policy, tree)


@pytest.mark.parametrize(
    "slots",
    [
        [2, 3, 4, 5, 6, 7, 8],
        [3, 3, 4, 5, 6, 7, 8],
        [9, 8, 7, 6, 5, 4, 3],
        [3, 4, 5, 6, 7, 8],
        [3, 4, 5, 6, 7, 8, 25],
    ],
)
def test_proof_requires_seven_fresh_cases_after_the_legacy_reproduction(proof, slots):
    with pytest.raises(ValueError, match="seven ordered"):
        list(proof.cases(slots))


def test_noncanonical_packet_is_checked_after_real_writer_and_before_emit(proof):
    from receipt_release_fixtures import exits

    legacy = exits("legacy-envelope")
    assert (
        legacy["legacy-custody"] == legacy["emit-program"] == 0 and legacy["enter-independent"] == 1
    )
    positive = exits("positive")
    assert (
        positive["preflight"]
        == positive["custody"]
        == positive["emit-program"]
        == positive["enter-independent"]
        == 0
    )
    damaged = exits("noncanonical")
    assert damaged["preflight"] == damaged["custody"] == 0 and damaged["emit-program"] == 1
    assert "enter-independent" not in damaged
