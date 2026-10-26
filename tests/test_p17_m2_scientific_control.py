"""NEW public scientific orchestration seams; no historical input is opened."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def load():
    spec = importlib.util.spec_from_file_location(
        "m2_scientific_control_test", REPO / "scripts/p17_m2_scientific_control.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_plain_P17_counterexample_removal_stops_after_retaining_row_and_cost(monkeypatch):
    import hashlib
    from time import perf_counter
    from types import SimpleNamespace

    driver = load()
    target = "tlcase-v1-55c1b3e64135c23125fc286de5d780fc5d9a1e226d5e43ff0dbc8925b423936a"
    evaluated, filed = [], {}

    class Queries:
        def __init__(self, *args, **kwargs):
            self.totals, self.failure = {}, None

        def evaluate(self, case, method, reference, *, phase):
            evaluated.append(method)
            return {
                "attempt": {
                    "succeeded": True,
                    "phase_witness": None,
                    "legacy_witness": {"result": {"compliance": 1.0}},
                },
                "fallback": None,
                "wall_seconds": 0.1,
                "charged_seconds": 1.1,
            }

    monkeypatch.setattr(driver, "MeasuredQueries", Queries)

    def writer(name, packet):
        raw = driver.canonical(packet)
        filed[name] = json.loads(raw)
        return {"path": name, "byte_size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    assets = SimpleNamespace(
        models={},
        identities={},
        row_setup_counts={},
        metadata={},
        load_for_row=lambda case, method: ({}, None, {"wall_seconds": 0}),
    )
    table = {
        "references": [],
        "queries": [
            {"ordinal": 1, "case_id": target, "method": "plain-P/17"},
            {"ordinal": 2, "case_id": target, "method": "H/17"},
        ],
    }
    with pytest.raises(ValueError, match="STOP_ROUTE_NOT_ISOLATED") as caught:
        driver._run_panel(
            [SimpleNamespace(case_id=target)],
            table,
            assets,
            None,
            contract_sha256="a" * 64,
            checkpoint=lambda: None,
            writer=writer,
            public_fixture_only=False,
            role_started=perf_counter(),
        )
    assert evaluated == ["plain-P/17"]
    failure = caught.value.scientific_failure
    assert failure["attempted_rows"] == 1 and len(failure["completed_rows"]) == 1
    assert failure["internal_row_charge_seconds"] >= 1.1
    assert any(name.startswith("queries/") for name in filed)
    assert "row-costs/query-001.json" in filed and "producer-failure.json" in filed


def test_complete_fixed_call_table_keeps_every_reference_query_and_untransferable_cap():
    driver = load()
    proposal = json.loads(
        (REPO / "docs/planning/p17_m2_native_homotopy_proposal.json").read_bytes()
    )
    table = driver.build_call_plan(proposal)
    assert len(table["references"]) == 18
    assert len(table["queries"]) == 342
    assert table["references"][0] == {
        "ordinal": 1,
        "case_id": proposal["prospective_pilot"]["case_ids"][0],
        "method": "uniform",
        "fem_max": 362,
        "projection_max": 1,
    }
    assert table["queries"][0]["method"] == "uniform"
    assert table["queries"][12]["method"] == "plain-P/17"
    assert table["queries"][-1]["method"] == "uniform-homotopy"
    assert table["producer_FEM_max"] == 254808
    assert table["independent_partitions"] == {
        "terminal_and_windows": 16632,
        "homotopy_prefix_and_transitions": 1368,
        "NN_label_input_reanalysis": 1056,
    }
    assert table["input_reads_per_role"] == {
        "scientific-producer": 542,
        "scientific-auditor": 1070,
        "reference-compatibility": 1,
    }


def test_checkpoint_decoder_uses_supplied_bytes_and_retains_fixed_f32_weights():
    import torch
    from safetensors.torch import save

    from topolab.b2_12_context_cnn import ContextCNN

    driver = load()
    item = {"family": "P", "seed": 17, "epoch": 23, "context_sha256": "1" * 64}
    metadata = {
        "checkpoint_version": "topolab.b3.checkpoint.v1",
        "context_sha256": "1" * 64,
        "recipe": "P",
        "seed": 17,
        "selected_epoch": 23,
    }
    model = ContextCNN()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.fill_(0.125)
    raw = save(model.state_dict(), metadata={"topolab": json.dumps(metadata)})
    decoded = driver.decode_checkpoint(raw, item)
    assert decoded.training is False
    assert decoded.network[-2].bias.item() == 0.125
    assert sum(p.numel() for p in decoded.parameters()) == 26433
    with pytest.raises(ValueError, match="provenance"):
        driver.decode_checkpoint(raw, {**item, "seed": 29})


def test_measured_public_query_counts_real_fem_projection_and_preserves_resource_stop():
    from topolab.b3_queries import QueryResourceExceeded

    driver = load()
    query = driver.load("p17_m2_homotopy")
    case = query.read_public_manifest(
        query.PUBLIC_FIXTURE, query.PUBLIC_FIXTURE_SHA256, expected_bytes=query.PUBLIC_FIXTURE_BYTES
    )
    measured = driver.MeasuredQueries({}, None, checkpoint=lambda: None)
    row = measured.evaluate(case, "uniform")
    assert row["attempt"]["succeeded"] is True
    assert row["measured_operations"]["projections"] == 1
    assert row["measured_operations"]["predictions"] == 0
    assert row["measured_operations"]["NN_queries"] == 0
    updates = len(row["attempt"]["legacy_witness"]["trace"])
    assert row["measured_operations"]["FEM"] == updates + 2
    assert row["measured_operations"]["OC_updates"] == updates
    initial = row["attempt"]["initialization_witness"]
    assert initial["raw_dtype"] == "float32" and initial["raw_shape"] == [1, 1, 2, 3]
    assert len(initial["raw_density"]) == len(initial["projected_design_density"]) == 6
    assert len(initial["projected_physical_density"]) == 6
    assert initial["status"] == "PROJECTED"
    assert row["charged_seconds"] >= row["wall_seconds"] + 1
    refused = driver.MeasuredQueries({}, None, checkpoint=lambda: None, fem_cap=0)
    with pytest.raises(QueryResourceExceeded, match="FEM"):
        refused.evaluate(case, "uniform")
    assert refused.failure["method"] == "uniform"
    assert refused.failure["reason"].startswith("FEM")
    assert refused.events[-1]["status"] == "REFUSED_BEFORE_CALL"


def test_nn_decoder_preserves_stored_f32_design_and_train_only_case_identity():
    import hashlib
    import struct

    import numpy as np

    driver = load()
    query = driver.load("p17_m2_homotopy")
    case = query.read_public_manifest(
        query.PUBLIC_FIXTURE, query.PUBLIC_FIXTURE_SHA256, expected_bytes=query.PUBLIC_FIXTURE_BYTES
    )
    design = [0.5] * 6
    record = {
        "schema": "topolab.v2.m2-nn-producer-view.v1",
        "case": case.model_dump(mode="json"),
        "membership": {"role": "train"},
        "initialization": {},
        "source": {},
        "stored": {
            "tensor_dtype": "float32",
            "tensor_axis_order": "channel,z,y,x",
            "tensor_shape": [1, 1, 2, 3],
            "design_density": design,
        },
        "bit_digests": {
            "/stored/design_density": hashlib.sha256(struct.pack("<6f", *design)).hexdigest()
        },
    }
    decoded, inputs, stored = driver.decode_nn_producer(driver.canonical(record), case.case_id)
    assert decoded == case
    assert inputs.shape == (10, 1, 2, 3)
    assert stored.shape == (1, 1, 2, 3) and stored.dtype == np.float32
    assert np.array_equal(stored, np.full((1, 1, 2, 3), 0.5, dtype=np.float32))
    record["membership"]["role"] = "validation"
    with pytest.raises(ValueError, match="train"):
        driver.decode_nn_producer(driver.canonical(record), case.case_id)


def test_serialized_acquisition_pass_does_not_grant_scientific_buffer_consumption():
    driver = load()
    serialized = {
        "status": "PASS",
        "scientific_permissions": {"producer": True},
        "scientific_execution_identity": driver.IDENTITY,
        "scientific_contract_sha256": "a" * 64,
    }
    with pytest.raises(ValueError, match="opaque scientific consumer"):
        driver.load_assets(serialized, "a" * 64)
    with pytest.raises(ValueError, match="opaque scientific consumer"):
        driver.load_references(serialized, "a" * 64, ["case"] * 18)


def test_new_uniform_reference_and_timed_query_have_distinct_counted_rows():
    driver = load()
    query = driver.load("p17_m2_homotopy")
    case = query.read_public_manifest(
        query.PUBLIC_FIXTURE, query.PUBLIC_FIXTURE_SHA256, expected_bytes=query.PUBLIC_FIXTURE_BYTES
    )
    measured = driver.MeasuredQueries({}, None, checkpoint=lambda: None)
    reference = measured.evaluate(case, "uniform", phase="reference")
    compliance = reference["attempt"]["legacy_witness"]["result"]["compliance"]
    row = measured.evaluate(case, "uniform", compliance)
    assert row["phase"] == "query" and reference["phase"] == "reference"
    assert row["attempt"]["legacy_witness"] == reference["attempt"]["legacy_witness"]
    assert measured.totals["FEM"] == 2 * row["measured_operations"]["FEM"]


def test_real_public_panel_files_queries_and_costs_with_pending_audit_status(tmp_path):
    import hashlib

    driver = load()
    helper = driver.load("p17_m2_content_verified_control")

    def writer(relative, packet):
        path = tmp_path / relative
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        helper.put(path, packet)
        raw = path.read_bytes()
        return {"path": relative, "byte_size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    result = driver.public_fixture_panel(writer=writer)
    assert result["software_only"] is True
    assert result["status"] == "PRODUCER_PANEL_COMPLETE_PENDING_INDEPENDENT_AUDIT"
    assert result["attempted_rows"] == 20 and len(result["rows"]) == 20
    assert result["rows"][0]["phase"] == "reference"
    assert [row["method"] for row in result["rows"][1:]] == list(driver.METHODS)
    assert result["measured_operations"]["FEM"] > 0
    assert result["measured_operations"]["NN_queries"] == 1
    for row in result["rows"]:
        packet = json.loads((tmp_path / row["packet"]["path"]).read_bytes())
        cost = json.loads((tmp_path / row["cost"]["path"]).read_bytes())
        assert cost["packet_sha256"] == row["packet"]["sha256"]
        assert cost["charged_seconds"] >= packet["wall_seconds"] + 1


def test_new_public_model_prediction_retains_initial_bits_and_rejects_parameter_mutation():
    import torch

    from topolab.b2_12_context_cnn import ContextCNN
    from topolab.b3_queries import QueryResourceExceeded
    from topolab.experiment import ExperimentCase
    from topolab.problem import TopologyProblem

    driver = load()
    query = driver.load("p17_m2_homotopy")
    problem = json.loads(query.PUBLIC_FIXTURE.read_bytes())["problem"]
    problem["mesh"]["element_counts"] = [12, 6, 3]
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(problem))
    model = ContextCNN()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.fill_(0.01)
    identity = {"checkpoint_sha256": "a" * 64, "parameter_sha256": driver.parameter_digest(model)}
    measured = driver.MeasuredQueries(
        {("P", 17): model}, None, checkpoint=lambda: None, model_identities={("P", 17): identity}
    )
    row = measured.evaluate(case, "plain-P/17")
    assert row["dispatched_method"] == "P/17"
    assert row["selected_weight_identity"] == identity
    assert row["measured_operations"]["predictions"] == 1
    assert row["attempt"]["initialization_witness"]["raw_shape"] == [1, 3, 6, 12]
    with torch.no_grad():
        model.network[-2].bias.add_(0.25)
    refused = driver.MeasuredQueries(
        {("P", 17): model}, None, checkpoint=lambda: None, model_identities={("P", 17): identity}
    )
    with pytest.raises(QueryResourceExceeded, match="MODEL_STATE_IDENTITY_CHANGED"):
        refused.evaluate(case, "plain-P/17")
    assert refused.totals["FEM"] == 0
    assert refused.failure["operation_events"][-1]["status"] == "RAISED"


def test_failed_packet_writer_keeps_complete_query_context_primary_and_secondary_errors():
    driver = load()
    primary = OSError("new public packet writer failed")

    def failed_writer(relative, packet):
        raise primary

    with pytest.raises(OSError) as caught:
        driver.public_fixture_panel(writer=failed_writer)
    assert caught.value is primary
    failure = caught.value.scientific_failure
    assert failure["attempted_rows"] == 1
    assert failure["current_packet"]["attempt"]["legacy_witness"]["result"]["compliance"] > 0
    assert failure["measured_operations"]["FEM"] > 0
    assert failure["known_role_charge_lower_bound_seconds"] >= 11
    assert failure["secondary_errors"] == [
        {"stage": "failure filing", "type": "OSError", "reason": "new public packet writer failed"}
    ]


@pytest.mark.parametrize("family,direction,volume", [("P", "z", 0.5), ("S", "y", 0.6)])
def test_query_row_reloads_selected_verified_model_and_refuses_changed_buffer(
    family, direction, volume
):
    import hashlib

    import torch
    from safetensors.torch import save

    from topolab.b2_12_context_cnn import ContextCNN

    driver = load()
    model = ContextCNN()
    with torch.no_grad():
        for parameter in model.parameters():
            parameter.fill_(0.125)
    metadata = {
        "checkpoint_version": "topolab.b3.checkpoint.v1",
        "context_sha256": "1" * 64,
        "recipe": family,
        "seed": 17,
        "selected_epoch": 23,
    }
    raw = save(model.state_dict(), metadata={"topolab": json.dumps(metadata)})
    item = {
        "family": family,
        "seed": 17,
        "epoch": 23,
        "context_sha256": "1" * 64,
        "output": {
            "path": f"checkpoints/{family}-17.safetensors",
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
    }
    assets = driver.ScientificAssets(
        {(family, 17): model},
        {},
        {(family, 17): {"parameter_sha256": driver.parameter_digest(model)}},
        {},
        _authority=driver._ASSET_AUTHORITY,
    )
    assets.row_buffers = {item["output"]["path"]: raw}
    assets.model_rows = {(family, 17): item}
    from topolab.experiment import ExperimentCase
    from topolab.problem import TopologyProblem

    problem = json.loads(driver.load("p17_m2_homotopy").PUBLIC_FIXTURE.read_bytes())["problem"]
    problem["mesh"]["element_counts"] = [24, 12, 6]
    problem["loads"][0]["direction"] = direction
    problem["optimization"]["volume_fraction"] = volume
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(problem))
    loaded, neighbors, facts = assets.load_for_row(case, "H/17")
    assert loaded[(family, 17)] is not model and neighbors is None
    assert loaded[(family, 17)].network[-2].bias.item() == 0.125
    assert facts["checkpoint_decodes"] == 1 and facts["buffer_rehashes"] == 1
    assert facts["source_file_rereads"] == 0
    assets.row_buffers[item["output"]["path"]] = raw[:-1] + bytes([raw[-1] ^ 1])
    with pytest.raises(ValueError, match="verified query buffer hash changed"):
        assets.load_for_row(case, "H/17")


def test_selected_query_buffer_follows_specialist_and_reject_routes():
    from topolab.experiment import ExperimentCase
    from topolab.problem import TopologyProblem

    driver = load()
    problem = json.loads(driver.load("p17_m2_homotopy").PUBLIC_FIXTURE.read_bytes())["problem"]
    problem["mesh"]["element_counts"] = [24, 12, 6]
    problem["optimization"]["volume_fraction"] = 0.6
    problem["loads"][0]["direction"] = "y"
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(problem))
    assets = driver.ScientificAssets({}, {}, {}, {}, _authority=driver._ASSET_AUTHORITY)
    # The exact missing key establishes that S, not the generalist P, was selected.
    with pytest.raises(KeyError) as error:
        assets.load_for_row(case, "H/17")
    assert error.value.args == (("S", 17),)
    problem["mesh"]["element_counts"] = [3, 2, 1]
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(problem))
    models, neighbors, facts = assets.load_for_row(case, "H/17")
    assert models == {} and neighbors is None and facts["checkpoint_decodes"] == 0


def test_active_uniform_homotopy_keeps_derived_control_with_fixed_weight_checks():
    from topolab.experiment import ExperimentCase
    from topolab.problem import TopologyProblem

    driver = load()
    public = driver.load("p17_m2_homotopy")
    problem = json.loads(public.PUBLIC_FIXTURE.read_bytes())["problem"]
    problem["mesh"]["element_counts"] = [24, 12, 6]
    problem["loads"][0]["direction"] = "y"
    case = ExperimentCase.from_problem(TopologyProblem.model_validate(problem))
    measured = driver.MeasuredQueries(
        {},
        None,
        checkpoint=lambda: None,
        model_identities={("P", 17): {"parameter_sha256": "a" * 64}},
    )
    row = measured.evaluate(case, "uniform-homotopy")
    assert row["attempt"]["phase_witness"] is not None
    events = [e for e in row["operation_events"] if e["operation"] == "predictions"]
    assert len(events) == 1 and events[0]["status"] == "RETURNED"
    assert events[0]["model_identity"]["fixed_derived_control"] == "uniform-homotopy"
