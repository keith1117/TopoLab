"""B2.5 exposure, artifact, fallback, and development-Gate boundaries."""

import sys
from pathlib import Path

import pytest
import torch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from b2_4_materialize_labels import select_cases  # noqa: E402
from b2_5_prototype import (  # noqa: E402
    EXPECTED_PLAN_SHA256,
    _artifact_path,
    _read_selection,
    _screen_index_path,
    _screen_summary,
    _write_fit_artifacts,
    atomic_write,
    canonical_bytes,
    load_samples,
    plan_payload,
    row_identity,
)

from topolab import b2_5_evaluation as evaluation  # noqa: E402
from topolab.b2_5_training import B25Fit, B25Sample, _loss, shape_batches  # noqa: E402
from topolab.experiment import encode_case  # noqa: E402
from topolab.training import WarmStartCNN  # noqa: E402


def _sample(case, split="train"):  # type: ignore[no-untyped-def]
    inputs = torch.from_numpy(encode_case(case).input_tensor.copy())
    shape = (1, *inputs.shape[1:])
    return B25Sample(
        case=case,
        split=split,
        inputs=inputs,
        design=torch.full(shape, 0.5, dtype=torch.float32),
        weight=torch.ones(shape, dtype=torch.float32),
    )


def test_shape_schedule_preserves_all_cases_and_identical_arm_order() -> None:
    cases = select_cases()
    assert plan_payload(cases)["plan_sha256"] == EXPECTED_PLAN_SHA256
    small = _sample(next(row.case for row in cases if row.source.scale == "small"))
    large = _sample(next(row.case for row in cases if row.source.scale == "large"))
    samples = (small,) * 432 + (large,) * 36
    first = torch.Generator().manual_seed(17)
    second = torch.Generator().manual_seed(17)
    batches = shape_batches(samples, first)

    assert batches == shape_batches(samples, second)
    assert len(batches) == 59
    assert sorted(index for batch in batches for index in batch) == list(range(468))
    assert all(1 <= len(batch) <= 8 for batch in batches)
    assert all(len({samples[index].shape for index in batch}) == 1 for batch in batches)
    assert sum(samples[batch[0]].shape == small.shape for batch in batches) == 54
    assert sum(samples[batch[0]].shape == large.shape for batch in batches) == 5


def test_dataset_adapter_rejects_held_out_split_before_artifact_access() -> None:
    with pytest.raises(ValueError, match="must not open test or OOD"):
        load_samples(Path("/missing-data-root"), {}, split="ood")


def test_candidate_loss_uses_weights_without_changing_control() -> None:
    prediction = torch.tensor([[[0.0, 1.0]]], dtype=torch.float32)
    target = torch.tensor([[[1.0, 1.0]]], dtype=torch.float32)
    weight = torch.tensor([[[1.5, 0.5]]], dtype=torch.float32)
    assert _loss(prediction, target, weight, "control").item() == pytest.approx(0.5)
    assert _loss(prediction, target, weight, "candidate").item() == pytest.approx(0.75)


def test_selection_artifact_rejects_corruption(tmp_path: Path) -> None:
    context = {"plan_sha256": "a" * 64, "source_revision": "b" * 40}
    with torch.random.fork_rng(devices=[]):
        state = WarmStartCNN().state_dict()
    history = tuple(
        {"epoch": epoch, "training_loss": 0.2, "validation_loss": 0.1 + epoch / 1000}
        for epoch in range(1, 27)
    )
    fit = B25Fit(
        arm="control",
        seed=17,
        history=history,
        selected_epoch=1,
        selected_validation_loss=history[0]["validation_loss"],
        duration_seconds=1.0,
        state=state,
    )
    row = _write_fit_artifacts(tmp_path, fit, context)
    _read_selection(tmp_path, row, context)
    checkpoint = _artifact_path(
        tmp_path, "checkpoints", "control", 17, row["checkpoint_sha256"]
    )
    checkpoint.write_bytes(checkpoint.read_bytes() + b"x")
    with pytest.raises(ValueError, match="checkpoint checksum"):
        _read_selection(tmp_path, row, context)


def test_failed_attempt_pays_fresh_uniform_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    case = select_cases()[0].case
    attempts = iter(
        (
            {"succeeded": False, "failure_code": "quality_error",
             "candidate": None, "matched_case_id": None,
             "timing": {"setup_seconds": 1.0, "projection_seconds": 2.0,
                        "refinement_seconds": 3.0, "decision_seconds": 0.0,
                        "fallback_seconds": 0.0}},
            {"succeeded": True, "failure_code": None,
             "candidate": {"final_compliance": 1.0, "physical_volume_error": 0.0},
             "matched_case_id": None,
             "timing": {"setup_seconds": 0.0, "projection_seconds": 1.0,
                        "refinement_seconds": 5.0, "decision_seconds": 1.0,
                        "fallback_seconds": 0.0}},
        )
    )
    monkeypatch.setattr(evaluation, "_attempt", lambda *_args, **_kwargs: next(attempts))
    reference = {
        "operational": {"final_compliance": 1.0},
        "timing": {"end_to_end_seconds": 10.0},
    }
    result = evaluation._charged_result(case, "control", 17, reference)
    assert result["succeeded"] is False
    assert result["fallback_used"] is True
    assert result["timing"]["fallback_seconds"] == 7.0
    assert result["timing"]["end_to_end_seconds"] == 13.0
    assert result["paired_time_ratio"] == pytest.approx(1.3)


def test_gate_needs_two_seeds_at_both_scales_and_direction_bounds(tmp_path: Path) -> None:
    cases = tuple(row for row in select_cases() if row.source.split == "validation")
    rows = []
    for item in cases:
        outcomes = []
        for method, seed in [
            ("uniform", None), ("physics_heuristic", None),
            ("nearest_neighbor", None),
            *((arm, seed) for arm in ("control", "candidate") for seed in (17, 29, 43)),
        ]:
            ratio = 0.85 if method == "candidate" and seed in (17, 29) else 1.1
            if method == "uniform":
                ratio = 1.0
            outcomes.append(
                {"case_id": item.case.case_id, "method": method, "seed": seed,
                 "succeeded": True, "fallback_used": False,
                 "operational": {"final_compliance": 1.0,
                                 "physical_volume_error": 0.0},
                 "uniform_reference_compliance": 1.0,
                 "paired_time_ratio": ratio}
            )
        rows.append({"identity": row_identity(item), "outcomes": outcomes})
    index = {
        "context": {}, "rows": rows, "elapsed_seconds": 10.0,
        "peak_rss_bytes": 1, "model_loading_seconds": 1.0,
        "neighbor_loading_seconds": 1.0, "neighbor_bytes": 1,
    }
    atomic_write(_screen_index_path(tmp_path), canonical_bytes(index))
    summary = _screen_summary(tmp_path, index)
    assert summary["passing_seeds"]["candidate"] == [17, 29]
    assert summary["prototype_gate_passed"] is True

    for row in rows:
        if row["identity"]["scale"] == "large" and row["identity"]["direction"] == "z":
            row["outcomes"][7]["paired_time_ratio"] = 1.3
    atomic_write(_screen_index_path(tmp_path), canonical_bytes(index))
    changed = _screen_summary(tmp_path, index)
    assert changed["passing_seeds"]["candidate"] == [17]
    assert changed["prototype_gate_passed"] is False
