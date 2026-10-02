"""Independent objective, exposure, artifact, timing and complete-Gate boundaries."""

import importlib.util
import json
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch
from torch import nn

import topolab.b3_training as training
import topolab.b4_weighted_terminal as weighted
from topolab.b2_6_trajectory import SHAPES, TrajectorySample
from topolab.b2_12_context_cnn import ContextCNN
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_queries import (
    AttemptTiming,
    QueryAttempt,
    QueryOutcome,
    TerminalWitness,
    policy_route,
)
from topolab.b3_training import B3Fit
from topolab.b4_telemetry import Journal
from topolab.baselines import BaselineMetrics


def runner():
    path = Path(__file__).resolve().parents[1] / "scripts/b4_5_weighted_terminal.py"
    spec = importlib.util.spec_from_file_location("weighted_runner", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_combined_objective_and_gradient_match_independent_sum():
    prediction = torch.tensor([0.1, 0.3, 0.6, 0.8]).reshape(2, 1, 1, 1, 2).requires_grad_()
    target = torch.tensor([0.0, 0.5, 0.4, 1.0]).reshape_as(prediction)
    spatial = torch.tensor([0.5, 1.5, 1.25, 0.75]).reshape_as(prediction)
    cases = torch.tensor([8.0, 1.0])
    value = training.weighted_terminal_loss(prediction, target, spatial, cases)
    manual = (
        sum(
            cases[i]
            * sum(
                spatial[i].reshape(-1)[e]
                * (prediction[i].reshape(-1)[e] - target[i].reshape(-1)[e]) ** 2
                for e in range(2)
            )
            / 2
            for i in range(2)
        )
        / 9
    )
    assert torch.equal(value, manual)
    value.backward()
    expected_gradient = 2 * spatial * (prediction.detach() - target) * cases.reshape(2, 1, 1, 1, 1)
    assert torch.allclose(prediction.grad, expected_gradient / 18)


@pytest.mark.parametrize(
    "spatial,cases",
    [
        (torch.ones(1), torch.ones(2)),
        (torch.zeros(2, 1, 1, 1, 2), torch.ones(2)),
        (torch.full((2, 1, 1, 1, 2), float("nan")), torch.ones(2)),
        (torch.ones(2, 1, 1, 1, 2), torch.tensor([1.0, -1.0])),
    ],
)
def test_objective_rejects_invalid_weights(spatial, cases):
    prediction = torch.ones(2, 1, 1, 1, 2)
    with pytest.raises(ValueError):
        training.weighted_terminal_loss(prediction, prediction, spatial, cases)


def test_element_ones_preserve_old_fit_and_rng(monkeypatch):
    class Tiny(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv = nn.Conv3d(13, 1, 1)

        def forward(self, x):
            return self.conv(x).sigmoid()

    monkeypatch.setattr(training, "ContextCNN", Tiny)
    monkeypatch.setattr(training, "CONTEXT_MODEL_PARAMETER_COUNT", 14)
    monkeypatch.setattr(training, "MAX_EPOCHS", 3)
    monkeypatch.setattr(training, "PATIENCE", 2)
    monkeypatch.setattr(training, "validation_mse", lambda *a: 0.1)
    samples = tuple(
        TrajectorySample(
            str(i),
            "train",
            torch.zeros(13, *s),
            torch.full((1, *s), 0.5),
            input_channels=13,
            weight=torch.ones(1, *s),
        )
        for i, s in enumerate(SHAPES)
    )
    validation = tuple(replace(s, split="validation", weight=None) for s in samples)
    weights = {s.case_id: 1.0 for s in samples}
    rng = torch.get_rng_state().clone()
    old = training._fit_samples(
        samples, validation, seed=17, weights=weights, checkpoint=lambda _: None
    )
    new = training._fit_samples(
        samples,
        validation,
        seed=17,
        weights=weights,
        checkpoint=lambda _: None,
        element_weighted=True,
    )
    assert old.history == new.history and old.selected_epoch == new.selected_epoch == 1
    assert all(torch.equal(old.state[n], new.state[n]) for n in old.state)
    assert torch.equal(rng, torch.get_rng_state())


def test_population_rejected_before_byte_read_or_model(monkeypatch, tmp_path):
    monkeypatch.setattr(weighted, "read_b3_record", lambda *a: pytest.fail("read label"))
    context = SimpleNamespace(data_index=SimpleNamespace(entries=()))
    with pytest.raises(ValueError, match="before bytes"):
        weighted.weighted_samples(tmp_path, context, lambda: None)
    monkeypatch.setattr(weighted, "_fit_samples", lambda *a, **k: pytest.fail("fit constructed"))
    with pytest.raises(ValueError, match="membership"):
        weighted.fit_weighted((), (), 17, lambda _: None)


def test_fresh_cohort_order_and_no_final_reads(monkeypatch):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("metadata plan read artifact"))
    plan = weighted.plan()
    assert len(plan["cases"]) == 48 and len(plan["assignments"]) == 576
    assert plan["final_access"] is False
    for case in weighted.fresh_cases():
        order = weighted.method_order(case)
        assert order[0] == "uniform" and set(order) == set(weighted.METHODS)
    assert len({c.case_id for c in weighted.fresh_cases()}) == 48


def test_new_model_artifacts_reject_wrong_source_and_corrupt_bytes(tmp_path):
    model = ContextCNN()
    history = tuple(
        {"epoch": i, "training_loss": 0.2, "validation_loss": 0.1} for i in range(1, 27)
    )
    fit = B3Fit(history, 1, 0.1, 1, model.state_dict())
    ref = weighted.publish_weighted_fit(tmp_path, "a" * 64, 17, fit)
    selection, restored = weighted.read_weighted_model(tmp_path, "a" * 64, 17, ref)
    assert selection.selected_epoch == 1
    assert all(
        torch.equal(model.state_dict()[n], restored.state_dict()[n]) for n in model.state_dict()
    )
    for context, seed in (("b" * 64, 17), ("a" * 64, 29)):
        with pytest.raises(ValueError, match="source"):
            weighted.read_weighted_model(tmp_path, context, seed, ref)
    packet = json.loads((tmp_path / ref["path"]).read_bytes())
    checkpoint = tmp_path / packet["checkpoint"]["path"]
    checkpoint.write_bytes(checkpoint.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="byte"):
        weighted.read_weighted_model(tmp_path, "a" * 64, 17, ref)


def test_complete_read_only_journal_rejects_resource_and_chain_changes(tmp_path):
    root = tmp_path / "fit"
    journal = Journal(root, "a" * 64, ("W/17",), 3600, 4_294_967_296)
    journal.begin("W/17")
    journal.publish("W/17", {"value": 1})
    journal.close()
    assert weighted.read_units(root, "a" * 64, ("W/17",)) == [{"value": 1}]
    progress = json.loads((root / "progress.json").read_bytes())
    progress["charged_seconds"] = 3601
    (root / "progress.json").write_bytes(canonical_metadata_bytes(progress))
    with pytest.raises(ValueError, match="passed prefix"):
        weighted.read_units(root, "a" * 64, ("W/17",))


def packets(b3_reference, failed_seed=None):
    witness = TerminalWitness.from_result(b3_reference.result)
    metrics = BaselineMetrics(
        iterations=len(witness.trace),
        final_compliance=witness.result.compliance,
        physical_volume_error=0,
    )
    cases = {c.case_id: c for c in weighted.fresh_cases()}
    failed_once = False
    for case_id, policy in weighted.assignments():
        name, _, seed = policy.partition("/")
        method = "P" if name == "W" else name
        attempt = QueryAttempt(
            succeeded=True, timing=AttemptTiming(), metrics=metrics, state=witness
        )
        failure = failed_seed is not None and policy == f"W/{failed_seed}" and not failed_once
        fallback = None
        if failure:
            failed_once = True
            fallback = attempt
            attempt = attempt.model_copy(
                update={
                    "succeeded": False,
                    "failure_code": "quality_error",
                    "failure_type": "ValueError",
                }
            )
        outcome = QueryOutcome(
            method=method,
            seed=int(seed) if seed else None,
            route=policy_route(cases[case_id], method),
            attempt=attempt,
            fallback=fallback,
        )
        wall = 10 if name == "uniform" else (5 if name == "W" else 8)
        yield {
            "case_id": case_id,
            "policy": policy,
            "outcome": outcome.model_dump(mode="json"),
            "timing": {"wall_seconds": wall, "legacy_phase_seconds": 0},
            "recording_allowance_seconds": 1.0,
        }


def test_complete_gate_retains_ineligible_seed_and_disallows_missing_population(b3_reference):
    result = weighted.development_gate(packets(b3_reference))
    assert result["passing_seeds"] == [17, 29, 43] and result["development_primary"] == 17
    assert result["development_gate_passed"]
    assert result["quality_cells"] == {"0.5397": 9, "0.5977": 9}
    result = weighted.development_gate(packets(b3_reference, failed_seed=29))
    assert result["passing_seeds"] == [17, 43]
    assert result["table"]["W/29"]["failures"] == result["table"]["W/29"]["fallbacks"] == 1
    assert not result["table"]["W/29"]["primary_eligible"]
    with pytest.raises(ValueError, match="every fixed"):
        weighted.development_gate(iter(list(packets(b3_reference))[:-1]))


def test_recording_receipt_cannot_discount_allowance_or_change_artifact(tmp_path):
    module = runner()
    ref = {"sha256": "b" * 64}
    receipt = {
        "version": "topolab.b4_5.recording.v1",
        "context_sha256": "a" * 64,
        "outcome_sha256": "b" * 64,
        "recording_seconds_before_receipt": 1.1,
    }
    (tmp_path / "recording").mkdir()
    (tmp_path / "recording/0000.json").write_bytes(canonical_metadata_bytes(receipt))
    with pytest.raises(ValueError, match="bound"):
        module.recording_receipt(tmp_path, 0, ref, "a" * 64)


def test_epoch_cap_precedes_model_update_and_is_permanent(tmp_path, monkeypatch):
    module = runner()
    root = tmp_path / "fit"
    root.mkdir()
    ledger = {"version": "topolab.b4_5.epochs.v1", "context_sha256": "a" * 64, "attempted": 600}
    (root / "epoch_attempts.json").write_bytes(canonical_metadata_bytes(ledger))
    monkeypatch.setattr(module, "weighted_samples", lambda *a: ((), ()))
    entered = []

    def fit(train, validation, seed, checkpoint):
        checkpoint(True)
        entered.append("update")

    monkeypatch.setattr(module, "fit_weighted", fit)
    context = SimpleNamespace(training_index=SimpleNamespace(context=None))
    with pytest.raises(RuntimeError, match="resource cap"):
        module.run("fit", tmp_path, tmp_path / "data", tmp_path / "old", context, "a" * 64, 0)
    assert entered == []
    progress = json.loads((root / "progress.json").read_bytes())
    assert progress["resource_failed"] and progress["active_at"] is None
    assert json.loads((root / "epoch_attempts.json").read_bytes())["attempted"] == 600


def test_cli_default_plan_never_preflights_or_creates_output(tmp_path, monkeypatch, capsys):
    module = runner()
    monkeypatch.setattr(module, "screening_preflight", lambda *a: pytest.fail("opened input"))
    monkeypatch.setattr(module, "run", lambda *a: pytest.fail("executed numerical stage"))
    monkeypatch.setattr("sys.argv", ["b4_5", "--output", str(tmp_path / "uncreated")])
    module.main()
    assert not (tmp_path / "uncreated").exists()
    assert '"final_access": false' in capsys.readouterr().out


def test_query_charges_recording_before_solver_and_publishes_complete_receipt(
    tmp_path,
    monkeypatch,
    b3_reference,
):
    module = runner()
    case = weighted.fresh_cases()[0]
    journal = Journal(tmp_path / "screen", "a" * 64, (case.case_id,), 21600, 2_147_483_648)
    witness = TerminalWitness.from_result(b3_reference.result)
    metrics = BaselineMetrics(
        iterations=len(witness.trace),
        final_compliance=witness.result.compliance,
        physical_volume_error=0,
    )
    outcome = QueryOutcome(
        method="uniform",
        seed=None,
        route="baseline",
        attempt=QueryAttempt(
            succeeded=True, timing=AttemptTiming(), metrics=metrics, state=witness
        ),
    )

    def evaluate(*args):
        assert journal.state.pending == 0 and journal.state.attempted == 1
        persisted = json.loads((journal.root / "progress.json").read_bytes())
        assert persisted["charged_seconds"] >= 1.0
        return outcome

    monkeypatch.setattr(module, "evaluate_query", evaluate)
    packet = module.query(journal, case.case_id, "uniform", None, {}, None, "a" * 64)
    assert packet["recording_allowance_seconds"] == 1.0
    ref = journal.records[0]["payload"]
    module.recording_receipt(journal.root, 0, ref, "a" * 64)
    assert module.read_packet(journal.root, ref, "a" * 64, case.case_id, "uniform") == packet
    journal.close()
