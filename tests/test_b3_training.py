"""Frozen membership, equal-case MSE, deterministic fits and interruption checks."""

from dataclasses import replace

import pytest
import torch
from torch import nn

import topolab.b3_training as training
from topolab.b2_6_trajectory import SHAPES, TrajectorySample, _batches, case_weighted_loss


def sample(case_id, split, shape, target):  # type: ignore[no-untyped-def]
    return TrajectorySample(case_id, split, torch.zeros((13, *shape)),
                            torch.full((1, *shape), target), input_channels=13)


def test_exact_recipe_memberships_weights_and_batches():
    expected = {"C": (468, 32, 78, 59), "P": (508, 32, 98, 64),
                "A": (508, 32, 0, 64), "S": (488, 4, 72, 61)}
    from topolab.b3_catalog import build_b3_case_catalog

    catalog = {e.case.case_id: e for e in build_b3_case_catalog().entries}
    for recipe, (count, validation, weighted, batches) in expected.items():
        ids, validation_ids = training.fitting_entries(recipe)
        assert (len(ids), len(validation_ids)) == (count, validation)
        weights = training.case_weights(recipe)
        assert len(weights) == count and sum(w == 8 for w in weights.values()) == weighted
        samples = tuple(sample(i, "train", tuple(reversed(
            catalog[i].case.problem.mesh.element_counts)), 0.5) for i in ids)
        schedule = _batches(samples, torch.Generator().manual_seed(17))
        assert len(schedule) == batches
        assert sorted(i for batch in schedule for i in batch) == list(range(count))
        assert all(len({samples[i].shape for i in batch}) == 1 for batch in schedule)
        assert set(ids).isdisjoint(validation_ids)


def test_selection_weights_cases_equally_across_meshes():
    class Zero(nn.Module):
        def forward(self, inputs):  # type: ignore[no-untyped-def]
            return torch.zeros((len(inputs), 1, *inputs.shape[2:]))

    samples = (sample("a", "validation", SHAPES[0], 0.0),
               sample("b", "validation", SHAPES[1], 1.0))
    assert training.validation_mse(Zero(), samples) == 0.5
    # A global voxel average would incorrectly produce 8/9.
    prediction = torch.zeros((2, 1, 3, 6, 12))
    target = torch.stack([torch.zeros((1, 3, 6, 12)), torch.ones((1, 3, 6, 12))])
    assert case_weighted_loss(prediction, target, torch.tensor([8.0, 1.0])).item() == (
        pytest.approx(1 / 9))


def test_label_conversion_retains_terminal_design_and_encoding(b3_label):  # type: ignore[no-untyped-def]
    import numpy as np

    converted = training.sample_from_label(b3_label)
    assert converted.case_id == b3_label.entry.case.case_id and converted.split == "train"
    assert converted.inputs.shape[0] == 13
    assert np.array_equal(converted.target.numpy().reshape(-1),
                          np.asarray(b3_label.stored.design_density, dtype=np.float32))


def test_public_fit_rejects_incomplete_or_forbidden_population_before_model(monkeypatch):
    def forbidden():
        pytest.fail("model constructed before membership validation")

    monkeypatch.setattr(training, "ContextCNN", forbidden)
    with pytest.raises(ValueError, match="membership"):
        training.fit_b3_seed((), (), recipe="P", seed=17, checkpoint=lambda _: None)
    with pytest.raises(ValueError, match="seed"):
        training.fit_b3_seed((), (), recipe="P", seed=99, checkpoint=lambda _: None)


def test_deterministic_fit_restores_rng_and_selects_earliest_tie(monkeypatch):
    class Tiny(nn.Module):
        def __init__(self):
            super().__init__()
            self.layer = nn.Conv3d(13, 1, 1)

        def forward(self, inputs):  # type: ignore[no-untyped-def]
            return torch.sigmoid(self.layer(inputs))

    monkeypatch.setattr(training, "ContextCNN", Tiny)
    monkeypatch.setattr(training, "CONTEXT_MODEL_PARAMETER_COUNT", 14)
    monkeypatch.setattr(training, "MAX_EPOCHS", 5)
    monkeypatch.setattr(training, "PATIENCE", 2)
    monkeypatch.setattr(training, "validation_mse", lambda *_: 0.1)
    train = tuple(sample(str(i), "train", shape, 0.5) for i, shape in enumerate(SHAPES))
    validation = tuple(replace(s, split="validation") for s in train)
    weights = {s.case_id: 1.0 for s in train}
    rng = torch.get_rng_state().clone()
    deterministic = torch.are_deterministic_algorithms_enabled()
    pulses = []
    first = training._fit_samples(train, validation, seed=17, weights=weights,
                                  checkpoint=pulses.append)
    second = training._fit_samples(train, validation, seed=17, weights=weights,
                                   checkpoint=lambda _: None)
    assert torch.equal(rng, torch.get_rng_state())
    assert torch.are_deterministic_algorithms_enabled() == deterministic
    assert len(first.history) == 3 and first.selected_epoch == 1
    assert first.history == second.history
    assert sum(pulses) == 3
    assert all(torch.equal(first.state[k], second.state[k]) for k in first.state)


def test_resource_exception_restores_rng_and_deterministic_settings():
    train = tuple(sample(str(i), "train", shape, 0.5) for i, shape in enumerate(SHAPES))
    rng = torch.get_rng_state().clone()
    deterministic = torch.are_deterministic_algorithms_enabled()

    def stop(_):  # type: ignore[no-untyped-def]
        raise RuntimeError("budget exhausted before epoch")

    with pytest.raises(RuntimeError, match="budget"):
        training._fit_samples(train, train, seed=17,
                              weights={s.case_id: 1.0 for s in train}, checkpoint=stop)
    assert torch.equal(rng, torch.get_rng_state())
    assert torch.are_deterministic_algorithms_enabled() == deterministic
