"""Synthetic fit artifacts, access-before-open, immutable charges and CLI planning."""

import fcntl
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import torch

import topolab.b3_training_artifacts as artifacts
import topolab.b3_training_cli as cli
from topolab.b2_12_context_cnn import ContextCNN
from topolab.b3_access import B3ArtifactReference
from topolab.b3_artifacts import B3DataArtifact
from topolab.b3_catalog import canonical_metadata_bytes
from topolab.b3_materialization import B3DataSuccess, B3MaterializationIndex
from topolab.b3_training import B3Fit
from topolab.b3_training_artifacts import (
    B3Selection,
    B3TrainingContext,
    B3TrainingIndex,
    FitFile,
    FitOutcome,
    read_selected_model,
    read_training_index,
    write_training_index,
)


@pytest.fixture(scope="module")
def synthetic_data(b3_manifest):  # type: ignore[no-untyped-def]
    entries = []
    for entry in b3_manifest.data_entries():
        kind = "reference" if entry.role == "screen_validation" else "label"
        access = B3ArtifactReference(kind=kind, entry=entry, artifact_sha256="c" * 64,
                                     origins=(entry.case,))
        entries.append(B3DataSuccess(
            entry=entry, artifact=B3DataArtifact(
                access=access, manifest_sha256=b3_manifest.sha256(),
                source_revision=b3_manifest.context.source_revision, byte_size=1,
                relative_path=f"artifacts/{kind}/{entry.case.case_id}/{'c' * 64}.json"),
            seconds=1, uniform_compliance=1, iterations=1, physical_volume_error=0))
    return B3MaterializationIndex(
        manifest=b3_manifest, manifest_sha256=b3_manifest.sha256(), entries=tuple(entries),
        audited_case_ids=tuple(e.entry.case.case_id for e in entries),
        cumulative_seconds=608, peak_rss_bytes=1)


@pytest.fixture
def context(synthetic_data, monkeypatch):  # type: ignore[no-untyped-def]
    # Only this exact synthetic metadata receipt gets a checksum substitution.
    # No production artifact is read and altered/incomplete receipts still fail.
    contents = canonical_metadata_bytes(synthetic_data.model_dump(mode="json"))
    real_digest = artifacts.digest
    monkeypatch.setattr(artifacts, "digest", lambda data: artifacts.B3_DATA_INDEX_SHA256
                        if data == contents else real_digest(data))
    return B3TrainingContext(source=synthetic_data.manifest.context, data_index=synthetic_data)


def _index(context, **kwargs):  # type: ignore[no-untyped-def]
    return B3TrainingIndex(context=context, context_sha256=context.sha256(), **kwargs)


def _selection(**updates):  # type: ignore[no-untyped-def]
    payload = {"context_sha256": "a" * 64, "recipe": "C", "seed": 17,
               "history": tuple({"epoch": e, "training_loss": 0.2, "validation_loss": 0.1}
                                for e in range(1, 27)),
               "selected_epoch": 1, "selected_validation_loss": 0.1, "fit_seconds": 1,
               "checkpoint": {"kind": "checkpoint", "sha256": "b" * 64, "byte_size": 1}}
    return B3Selection.model_validate({**payload, **updates})


def test_data_gate_requires_exact_passed_receipt(context):  # type: ignore[no-untyped-def]
    assert context.data_index.data_gate_passed
    for updates in ({"integrity_failed": True}, {"entries": ()}, {"cumulative_seconds": 1}):
        changed = context.data_index.model_copy(update=updates)
        with pytest.raises(ValueError):
            B3TrainingContext(source=context.source, data_index=changed)


@pytest.mark.parametrize("updates", [
    {"selected_epoch": 2}, {"selected_validation_loss": 0.2},
    {"history": ({"epoch": 1, "training_loss": 0.2, "validation_loss": 0.1},)},
    {"history": tuple({"epoch": e, "training_loss": 0.2, "validation_loss": 0.1}
                      for e in range(1, 28))},
    {"history": ({"epoch": 2, "training_loss": 0.2, "validation_loss": 0.1},)},
    {"fit_seconds": float("nan")},
])
def test_selection_rejects_ties_short_histories_and_invalid_metrics(updates):  # type: ignore[no-untyped-def]
    assert _selection().selected_epoch == 1
    with pytest.raises(ValueError):
        _selection(**updates)


def test_checkpoint_byte_tensor_and_provenance_verification(tmp_path, context):  # type: ignore[no-untyped-def]
    with torch.random.fork_rng(devices=[]):
        state = ContextCNN().state_dict()
    history = tuple(h.model_dump() for h in _selection().history)
    fit = B3Fit(history, 1, 0.1, 1, state)
    outcome = artifacts.publish_fit(tmp_path, context, "C", 17, fit)
    selection, model = read_selected_model(tmp_path, context, outcome)
    assert all(torch.equal(state[k], model.state_dict()[k]) for k in state)
    with pytest.raises(ValueError, match="selection differs"):
        read_selected_model(tmp_path, context, outcome.model_copy(update={"seed": 29}))
    path = tmp_path / selection.checkpoint.relative_path
    path.write_bytes(path.read_bytes() + b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        read_selected_model(tmp_path, context, outcome)


def test_index_prefix_and_monotone_charges(tmp_path, context):  # type: ignore[no-untyped-def]
    outcome = FitOutcome(recipe="C", seed=17,
                         selection=FitFile(kind="selection", sha256="a" * 64, byte_size=1))
    index = _index(context, outcomes=(outcome,), attempted_epochs=26,
                   cumulative_seconds=30, peak_rss_bytes=1, integrity_failed=True)
    write_training_index(tmp_path, index)
    assert read_training_index(tmp_path, context) == index
    for update in ({"outcomes": ()}, {"attempted_epochs": 25}, {"cumulative_seconds": 29},
                   {"peak_rss_bytes": 0}, {"integrity_failed": False}):
        with pytest.raises(ValueError):
            write_training_index(tmp_path, index.model_copy(update=update))
    with pytest.raises(ValueError, match="prefix"):
        _index(context, outcomes=(outcome.model_copy(update={"recipe": "P"}),),
               attempted_epochs=26)


def test_membership_is_complete_before_label_open(tmp_path, context, monkeypatch):  # type: ignore[no-untyped-def]
    calls = []
    monkeypatch.setattr(artifacts, "read_b3_record", lambda *a: calls.append(a))
    broken = context.model_copy(update={"data_index": context.data_index.model_copy(
        update={"entries": ()})})
    with pytest.raises(ValueError, match="every requested label"):
        artifacts.load_fitting_samples(tmp_path, broken, "C", {}, lambda _: None)
    assert calls == []
    # The first authorized read is a fitting label, never screening/final evidence.
    def stop(root, manifest, artifact, access):  # type: ignore[no-untyped-def]
        assert access.consumer == "fitting"
        assert artifact.access.entry.role in ("train", "fit_validation")
        raise KeyboardInterrupt

    monkeypatch.setattr(artifacts, "read_b3_record", stop)
    with pytest.raises(KeyboardInterrupt):
        artifacts.load_fitting_samples(tmp_path, context, "S", {}, lambda _: None)


def test_resource_recovery_preserves_hard_crash_and_epoch_charges(
    tmp_path, context, monkeypatch,
):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(artifacts, "_peak_rss_bytes", lambda: 1)
    index = _index(context, attempted_epochs=2400, cumulative_seconds=1,
                   active_checkpoint_at=datetime.now(UTC) - timedelta(seconds=10))
    write_training_index(tmp_path, index)
    monkeypatch.setattr(artifacts, "load_fitting_samples", lambda *a: ((), ()))

    def fit(*args, checkpoint, **kwargs):  # type: ignore[no-untyped-def]
        checkpoint(True)
        pytest.fail("fit entered after epoch budget exhaustion")

    monkeypatch.setattr(artifacts, "fit_b3_seed", fit)
    result = artifacts.run_b3_fitting(tmp_path, tmp_path.parent / "data", context,
                                     repository_root=Path(__file__).resolve().parents[1])
    assert result.resource_failed and result.active_checkpoint_at is None
    assert result.attempted_epochs == 2400 and result.cumulative_seconds >= 11
    assert not result.fitting_gate_passed


def test_resource_overrun_and_writer_lock_stop_before_label_open(
    tmp_path, context, monkeypatch,
):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(artifacts, "_peak_rss_bytes", lambda: artifacts.FIT_RSS_BYTES + 1)
    monkeypatch.setattr(artifacts, "load_fitting_samples", lambda *a: pytest.fail("opened label"))
    result = artifacts.run_b3_fitting(tmp_path, tmp_path.parent / "data", context,
                                     repository_root=Path(__file__).resolve().parents[1])
    assert result.resource_failed and result.active_checkpoint_at is None
    with (tmp_path / ".b3-fitting.lock").open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(RuntimeError, match="another writer"):
            artifacts.run_b3_fitting(tmp_path, tmp_path.parent / "data", context,
                                     repository_root=Path(__file__).resolve().parents[1])


def test_pending_fit_resumes_without_repeating_retained_fit(tmp_path, context, monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(artifacts, "_peak_rss_bytes", lambda: 1)
    monkeypatch.setattr(artifacts, "load_fitting_samples", lambda *a: ((), ()))
    monkeypatch.setattr(artifacts, "validation_mse", lambda *a: 0.1)
    with torch.random.fork_rng(devices=[]):
        state = ContextCNN().state_dict()
    calls = []

    def fit(*args, recipe, seed, checkpoint, **kwargs):  # type: ignore[no-untyped-def]
        calls.append((recipe, seed))
        checkpoint(True)
        if seed != 17:
            raise KeyboardInterrupt
        for _ in range(25):
            checkpoint(True)
        return B3Fit(tuple(h.model_dump() for h in _selection().history), 1, 0.1, 1, state)

    monkeypatch.setattr(artifacts, "fit_b3_seed", fit)
    kwargs = {"repository_root": Path(__file__).resolve().parents[1]}
    with pytest.raises(KeyboardInterrupt):
        artifacts.run_b3_fitting(tmp_path, tmp_path.parent / "data", context, **kwargs)
    first = read_training_index(tmp_path, context)
    assert len(first.outcomes) == 1 and first.attempted_epochs == 27
    with pytest.raises(KeyboardInterrupt):
        artifacts.run_b3_fitting(tmp_path, tmp_path.parent / "data", context, **kwargs)
    second = read_training_index(tmp_path, context)
    assert second.outcomes == first.outcomes and second.attempted_epochs == 28
    assert calls == [("C", 17), ("C", 29), ("C", 29)]
    assert second.cumulative_seconds > first.cumulative_seconds
    assert second.active_checkpoint_at is None


def test_invalid_fit_stops_program_and_preserves_failure(tmp_path, context, monkeypatch):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(artifacts, "_peak_rss_bytes", lambda: 1)
    monkeypatch.setattr(artifacts, "load_fitting_samples", lambda *a: ((), ()))

    def fail(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise ValueError("nonfinite training objective")

    monkeypatch.setattr(artifacts, "fit_b3_seed", fail)
    with pytest.raises(ValueError, match="nonfinite"):
        artifacts.run_b3_fitting(tmp_path, tmp_path.parent / "data", context,
                                 repository_root=Path(__file__).resolve().parents[1])
    recorded = read_training_index(tmp_path, context)
    assert recorded.fitting_failed and recorded.integrity_failed
    assert recorded.active_checkpoint_at is None and not recorded.fitting_gate_passed


def test_planning_has_no_artifact_reads_or_output_creation(tmp_path, context, monkeypatch,
                                                         capsys):  # type: ignore[no-untyped-def]
    monkeypatch.setattr(cli, "training_preflight", lambda *a: (tmp_path / "repository", context))
    monkeypatch.setattr(cli, "run_b3_fitting", lambda *a, **k: pytest.fail("fit invoked"))
    output = tmp_path / "outputs"
    assert cli.main(["--data-root", str(tmp_path / "data"), "--output-root", str(output)]) == 0
    assert not output.exists()
    assert '"fits": 12' in capsys.readouterr().out


def test_complete_gate_requires_every_audit_and_resource_check(context):  # type: ignore[no-untyped-def]
    outcomes = tuple(FitOutcome.model_validate({"recipe": r, "seed": s, "selection": {
        "kind": "selection", "sha256": "a" * 64, "byte_size": 1}}) for r, s in artifacts.TASKS)
    index = _index(context, outcomes=outcomes, attempted_epochs=312,
                   audited_fits=artifacts.TASKS)
    assert index.fitting_gate_passed
    for update in ({"audited_fits": ()}, {"resource_failed": True}, {"fitting_failed": True},
                   {"integrity_failed": True}, {"active_checkpoint_at": datetime.now(UTC)},
                   {"cumulative_seconds": 7201}, {"peak_rss_bytes": artifacts.FIT_RSS_BYTES + 1},
                   {"attempted_epochs": 2401}):
        assert not index.model_copy(update=update).fitting_gate_passed
