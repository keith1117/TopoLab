"""Synthetic reflection, non-intervention, complete Gates and native guard checks."""

import importlib
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from torch import nn

from topolab import b4_reflection_repair as probe
from topolab.b2_5_evaluation import _predict
from topolab.b2_9_vector_load import encode_vector_load_case
from topolab.b3_catalog import _cantilever_case, canonical_metadata_bytes
from topolab.b4_reflection import (
    ReflectionAverage,
    checked_prediction,
    mirror_case,
    reflection_target,
)
from topolab.experiment import ExperimentCase
from topolab.problem import TopologyProblem


@pytest.fixture
def scripts(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return {
        name: importlib.import_module("b4_30_" + name)
        for name in ("common", "independent_audit", "native_execution", "z_reflection_repair")
    }


@pytest.fixture
def case():
    return _cantilever_case(0.41, "y", 3, 1, True, 360)


class AnalyticPredictor(nn.Module):
    def __init__(self):
        super().__init__()
        self.inputs = []

    def forward(self, inputs):
        self.inputs.append(inputs.clone())
        return torch.sigmoid(inputs[:, 7:8] + 0.4 * inputs[:, 8:9] + 0.3 * inputs[:, 12:13])


def test_same_checkpoint_twice_reencodes_and_reflects_density(case):
    model, records, pulses = AnalyticPredictor(), [], []
    wrapper = ReflectionAverage(
        case, model, lambda: pulses.append(True), lambda *args: records.append(args)
    )
    result = _predict(case, wrapper, encoder=encode_vector_load_case)
    assert len(model.inputs) == 2 and len(records) == 1 and len(pulses) == 3
    assert torch.equal(
        model.inputs[0][0], torch.from_numpy(encode_vector_load_case(case).input_tensor)
    )
    assert torch.equal(
        model.inputs[1][0],
        torch.from_numpy(encode_vector_load_case(mirror_case(case)).input_tensor),
    )
    assert not torch.equal(model.inputs[1], torch.flip(model.inputs[0], (2,)))
    mirrored, first, second, average = records[0]
    assert mirrored.case_id == mirror_case(case).case_id
    assert torch.equal(average, (first + torch.flip(second, (2,))) * 0.5)
    assert np.array_equal(result, average.squeeze(0).numpy())


def test_group_average_equivariance_without_fit_or_payload(case):
    model = AnalyticPredictor()
    first = _predict(
        case, ReflectionAverage(case, model, lambda: None), encoder=encode_vector_load_case
    )
    mirrored = mirror_case(case)
    second = _predict(
        mirrored, ReflectionAverage(mirrored, model, lambda: None), encoder=encode_vector_load_case
    )
    assert np.array_equal(first, second[:, ::-1, :, :])
    assert mirror_case(mirrored).case_id == case.case_id


@pytest.mark.parametrize(
    "large,direction,volume",
    [(False, "y", 0.41), (True, "z", 0.41), (True, "y", 0.55), (True, "y", 0.61)],
)
def test_non_target_never_activates(large, direction, volume):
    case = _cantilever_case(volume, direction, 3, 1, large, 360)
    assert not reflection_target(case)
    with pytest.raises(ValueError, match="target region"):
        ReflectionAverage(case, AnalyticPredictor(), lambda: None)


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -0.1, 1.1])
@pytest.mark.parametrize("which", [1, 2])
def test_invalid_raw_cannot_be_hidden_by_average(case, invalid, which):
    class InvalidPredictor(nn.Module):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def forward(self, inputs):
            self.calls += 1
            return torch.full((1, 1, 6, 12, 24), invalid if self.calls == which else 0.4)

    model = InvalidPredictor()
    with pytest.raises(ValueError, match="finite"):
        _predict(
            case, ReflectionAverage(case, model, lambda: None), encoder=encode_vector_load_case
        )
    assert model.calls == which


@pytest.mark.parametrize("kind", ["shape", "float64", "meta"])
def test_prediction_shape_dtype_and_cpu_are_mandatory(case, kind):
    value = torch.zeros((1, 1, 6, 12, 24))
    if kind == "shape":
        value = value[:, :, :, :, :-1]
    elif kind == "float64":
        value = value.double()
    else:
        value = torch.zeros(value.shape, device="meta")
    with pytest.raises(ValueError):
        checked_prediction(value, case)


def test_frozen_populations_order_and_single_allocation():
    c = probe.contract()
    assert c["authority"]["slice_limit"] == 1 and not c["authority"]["prior_budget_transferable"]
    for cohort, count, queries in (("sentinel", 18, 270), ("fresh", 48, 720)):
        assert len(probe.cases(cohort)) == count and len(probe.assignments(cohort)) == queries
        assert len(set(probe.assignments(cohort))) == queries
        assert all(probe.assignments(cohort)[i][1] == "uniform" for i in range(0, queries, 15))
    assert c["resources"]["fresh_admission_maximum_reservation_seconds"] + 180 + 8820 == 43200
    assert c["stops"]["final_access"] is False and c["stops"]["old_B410_fresh_access"] is False


def test_independent_raw_mean_check_rejects_one_ulp_tamper(case, scripts, tmp_path):
    model = AnalyticPredictor()

    def recorder(*args):
        scripts["z_reflection_repair"].record_prediction(tmp_path, "a" * 64, 17, case, *args)

    _predict(
        case,
        ReflectionAverage(case, model, lambda: None, recorder),
        encoder=encode_vector_load_case,
    )
    auditor = scripts["independent_audit"]
    auditor.reflection_record(tmp_path, "a" * 64, case.model_dump(mode="json"), 17)
    path = tmp_path / "prediction" / f"{case.case_id}_17.json"
    value = json.loads(path.read_bytes())
    value["average"][0] = float(np.nextafter(np.float32(value["average"][0]), np.float32(1)))
    path.write_bytes(canonical_metadata_bytes(value))
    with pytest.raises(AssertionError):
        auditor.reflection_record(tmp_path, "a" * 64, case.model_dump(mode="json"), 17)


def test_non_target_evaluator_uses_original_model_without_wrapper(
    case, scripts, monkeypatch, tmp_path
):
    small = _cantilever_case(0.41, "y", 3, 1, False, 360)
    model = AnalyticPredictor()
    models = {("P", 17): model}
    seen = []

    def legacy(case, method, seed, reference, selected, neighbors, checkpoint, **kwargs):
        seen.append((method, selected is models, selected[("P", 17)] is model))
        return "unchanged"

    driver = scripts["z_reflection_repair"]
    monkeypatch.setattr(driver, "evaluate_query", legacy)
    result = driver.evaluator(tmp_path, "a" * 64, small, "R", 17, None, models, None, lambda: None)
    assert result == "unchanged" and seen == [("P", True, True)] and not model.inputs


def test_small_synthetic_physical_reflection_invariance(case):
    from topolab.baselines import _evaluate_case_density

    payload = case.problem.model_dump(mode="json")
    payload["mesh"]["element_counts"] = [4, 2, 2]
    payload["mesh"]["lengths"] = [4.0, 2.0, 2.0]
    payload["loads"][0]["node"] = 4 + 5 * (1 + 3 * 0)
    tiny = ExperimentCase.from_problem(TopologyProblem.model_validate(payload))
    density = np.linspace(0.2, 0.8, 16)
    reflected = density.reshape(2, 2, 4)[::-1].copy().reshape(-1)
    first = _evaluate_case_density(tiny, density)
    second = _evaluate_case_density(mirror_case(tiny), reflected)
    assert np.isclose(first, second, rtol=1e-12, atol=0)


def synthetic_rows(cohort):
    by_id = {c.case_id: c for c in probe.cases(cohort)}
    rows = []
    for case_id, method in probe.assignments(cohort):
        c = by_id[case_id]
        negative = (
            cohort == "sentinel"
            and c.problem.mesh.element_counts[0] == 12
            and c.problem.loads[0].direction == "z"
            and method in ("P/29", "R/29")
        )
        failed = negative or (
            cohort == "sentinel"
            and case_id.startswith("tlcase-v1-55c1b3e")
            and method.startswith("P/")
        )
        costs = {
            "uniform": 10,
            "physics_heuristic": 11,
            "nearest_neighbor": 12,
            "C": 10,
            "P": 8,
            "W": 9,
            "R": 8,
        }
        family = method.split("/")[0]
        rows.append(
            {
                "case_id": case_id,
                "policy": method,
                "cost": 18 if failed else costs[family],
                "failed": failed,
                "fallback": failed,
                "route": "baseline"
                if "/" not in method
                else (
                    "specialist"
                    if c.problem.mesh.element_counts[0] == 24
                    and c.problem.loads[0].direction == "y"
                    and c.problem.optimization.volume_fraction >= 0.55
                    else "generalist"
                ),
                "scale": "small" if c.problem.mesh.element_counts[0] == 12 else "large",
                "direction": c.problem.loads[0].direction,
                "volume": c.problem.optimization.volume_fraction,
                "target": reflection_target(c),
            }
        )
    return rows


@pytest.mark.parametrize("cohort", ["sentinel", "fresh"])
def test_independent_gate_agreement_and_fixed_primary_cannot_be_replaced(
    cohort, scripts, monkeypatch
):
    rows = synthetic_rows(cohort)
    monkeypatch.setattr(probe, "compact_rows", lambda packets, chosen: rows)
    result = probe.decision([], cohort)
    independent = scripts["independent_audit"]
    independent.close(result, independent.decision(rows, cohort, probe.contract()))
    assert result["repair_gate_passed"]
    victim = next(r for r in rows if r["policy"] == "R/17" and r["target"])
    victim.update(failed=True, fallback=True)
    result = probe.decision([], cohort)
    independent.close(result, independent.decision(rows, cohort, probe.contract()))
    assert not result["repair_gate_passed"] and result["fixed_primary"] == 17


def test_zero_failures_do_not_clear_sentinel_full_cost_gate(scripts, monkeypatch):
    rows = synthetic_rows("sentinel")
    for row in rows:
        if row["policy"] == "R/17" and row["target"]:
            row["cost"] = 11
    monkeypatch.setattr(probe, "compact_rows", lambda packets, chosen: rows)
    result = probe.decision([], "sentinel")
    assert not result["primary_failures"] and not result["repair_gate_passed"]
    scripts["independent_audit"].close(
        result, scripts["independent_audit"].decision(rows, "sentinel", probe.contract())
    )


def test_partial_or_changed_population_cannot_establish_gate():
    with pytest.raises(ValueError, match="partial"):
        probe.compact_rows([], "sentinel")
    with pytest.raises(ValueError, match="frozen order"):
        probe.compact_rows(
            [{"case_id": probe.cases("sentinel")[0].case_id, "policy": "R/17"}], "sentinel"
        )


@pytest.mark.parametrize("bad", ["no-rss", "zero-rss", "no-cpu"])
def test_missing_native_evidence_is_rejected(scripts, bad):
    text = "1.0 real 0.5 user 0.2 sys\n4096 maximum resident set size\n"
    if bad == "no-rss":
        text = "1.0 real 0.5 user 0.2 sys\n"
    elif bad == "zero-rss":
        text = text.replace("4096", "0")
    else:
        text = "1.0 real\n4096 maximum resident set size\n"
    with pytest.raises(ValueError, match="native"):
        scripts["common"].native(text)


def test_exclusive_evidence_and_symlink_guard(scripts, tmp_path):
    common = scripts["common"]
    common.save(tmp_path / "result.json", {"passed": True})
    with pytest.raises(FileExistsError):
        common.save(tmp_path / "result.json", {"passed": False})
    outside = tmp_path.parent / (tmp_path.name + "-outside")
    outside.mkdir()
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises(ValueError, match="contained|symlink"):
        common.contained(tmp_path, "linked/result.json")


def test_unknown_native_profile_never_passes_resource_admission(scripts, tmp_path):
    common, execution = scripts["common"], scripts["native_execution"]
    common.save(
        tmp_path / "audit_receipts/sentinel_reference_command.json",
        {
            "name": "sentinel_reference",
            "native": None,
            "exit_code": 1,
            "terminated": False,
            "observed_outer_wall_seconds": 1.2,
            "observed_process_group_plus_controller_rss_bytes": 4096,
        },
    )
    total, complete, rows = execution.stage_charges(tmp_path, "sentinel")
    assert total == 11.2 and not complete and rows[0]["peak_rss_bytes"] is None
    assert rows[0]["complete_resource_evidence"] is False


def test_dirty_source_release_rejects_before_payload_access(scripts, monkeypatch, tmp_path):
    common = scripts["common"]
    output = tmp_path / common.contract()["evidence_root_name"]
    record = {
        "source_revision": "a" * 40,
        "passed": True,
        "main_ci_passed": True,
        "all_applicable_ci_passed_before_merge": True,
        "source_tree_same": True,
        "plan": common.plan_payload(),
        "owner_authorization_sha256": probe.contract()["authority"]["owner_authorization_sha256"],
    }
    common.save(output / "audit_receipts/production_release.json", record)

    def git(argv, **kwargs):
        if argv[1] == "rev-parse":
            return "a" * 40
        if argv[1] == "branch":
            return "main"
        return b" M src/topolab/b4_reflection.py"

    monkeypatch.setattr(common.subprocess, "check_output", git)
    with pytest.raises(ValueError, match="clean locked merged"):
        common.release(output)
    assert not (output / "context.json").exists()


@pytest.mark.parametrize(
    "exit_code,wall,expected", [(0, 0.3, True), (1, 0.3, False), (0, 6, False)]
)
def test_final_native_binder_exit_is_required(
    scripts, monkeypatch, tmp_path, exit_code, wall, expected
):
    native = scripts["native_execution"]
    common = scripts["common"]
    monkeypatch.setattr(native, "release", lambda output: "a" * 40)
    monkeypatch.setattr(native, "guard_failed_prefix", lambda parent: None)
    common.save(
        tmp_path / "audit_receipts/platform_exit_binding.json",
        {
            "resource_passed_before_binder_exit": True,
            "repair_gate_passed_before_binder_exit": True,
            "whole_peak_rss_bytes": 1,
            "source_revision": "a" * 40,
        },
    )
    profile, log = tmp_path / "binder.time", tmp_path / "binder.log"
    profile.write_text(f"{wall} real 0.1 user 0.1 sys\n123456 maximum resident set size\n")
    log.write_text("bound\n")
    value = native.verify_binder_exit(tmp_path, profile, log, exit_code)
    assert value["passed"] is expected and value["repair_gate_passed"] is expected
    assert value["final_verifier_native_exit_required_before_publication"]


def test_untracked_owner_document_rejects_before_output_creation(scripts, monkeypatch, tmp_path):
    native = scripts["native_execution"]
    common = scripts["common"]
    output = tmp_path / common.contract()["evidence_root_name"]
    value = {"plan": common.plan_payload()}
    source = tmp_path / "release.json"
    common.save(source, value)
    calls = []

    def git(argv, **kwargs):
        if argv[1] == "rev-parse":
            return "a" * 40
        if argv[1] == "branch":
            return "main"
        calls.append(argv)
        return b'?? "CHANGELOG 2.md"'

    monkeypatch.setattr(common.subprocess, "check_output", git)
    monkeypatch.setattr(native, "plan_payload", lambda: value["plan"])
    with pytest.raises(ValueError, match="clean locked merged"):
        native.prepare(output, source)
    assert calls == [["git", "status", "--porcelain", "--untracked-files=all"]]
    assert not output.exists()


def test_clean_source_inspector_is_not_relaxed_for_owned_untracked_files(
    scripts, monkeypatch, tmp_path
):
    from topolab import dataset_cli

    def git(cwd, *args):
        if args[:2] == ("rev-parse", "--show-toplevel"):
            return str(tmp_path)
        if args[0] == "rev-parse":
            return "a" * 40
        return '?? "CHANGELOG 2.md"'

    monkeypatch.setattr(dataset_cli, "_git_output", git)
    with pytest.raises(dataset_cli.DatasetEntrypointError, match="must be clean"):
        dataset_cli.inspect_repository(tmp_path)
