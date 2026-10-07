"""Public metadata fixtures exercise access boundaries, independent sums and stops."""

import ast
import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_29_common as common  # noqa: E402
import b4_29_independent_audit as independent  # noqa: E402
import b4_29_native_execution as execution  # noqa: E402
import b4_29_outcome_review as candidate  # noqa: E402


@pytest.fixture
def panel(tmp_path):
    c = common.contract()
    metrics = {
        "normalized_value_error": 1e-6,
        "increment_relative_error": 0.001,
        "gradient_relative_error": 0.003,
        "increment_sign_agrees": True,
        "exact_gradient_norm": 1.0,
        "surrogate_gradient_norm": 1.0,
    }
    intervals = [
        {
            "case_id": str(case),
            "state": state,
            "direction": direction,
            "step": step,
            "crossing": False,
            "passed": True,
            "pieces": 1,
            "predicates": [True] * 3,
        }
        for case in range(8)
        for state in (0, 4)
        for direction in ("sine", "cosine")
        for step in (0.0001, 0.0002)
    ]
    for row in intervals[:35]:
        row.update(crossing=True, pieces=81)
    x = {
        "source_revision": c["b4_28"]["source_revision"],
        "integrity_passed": True,
        "local_fidelity_passed": True,
        "new_predicate_count": 3232,
        "new_predicates_passed": 3232,
        "pointwise_states": 200,
        "intervals": intervals,
        "local_states": [
            {"case_id": str(case), "state": state, "passed": True, "metrics": dict(metrics)}
            for case in range(8)
            for state in range(4)
        ],
        "central_diagnostics": [
            {
                "case_id": str(case),
                "state": state,
                "region": ("uniform", "local", "outside")[state % 3],
                "surrogate_value": 1.0,
                "negative_surrogate": False,
                "exact_value": 1.0,
                "metrics": dict(metrics),
            }
            for case in range(8)
            for state in range(9)
        ],
        "legacy_failed_positions": list(range(69)),
        "legacy_predicates": 3976,
        "legacy_failed": 69,
        "legacy_first_timings": 216,
        "legacy_fem": 432,
        "legacy_projections": 816,
        "historical_b4_24_seconds": 200.98,
        "historical_b4_25_seconds": 80.34,
        "historical_b4_24_planning_rss": None,
        "historical_b4_24_whole_peak_rss": None,
        "historical_b4_24_whole_memory_proof": False,
        "historical_b4_19_case_gap_counts": "UNKNOWN",
        "full_training_memory": "PENDING",
        "full_training_memory_cap_bytes": 4294967296,
        "whole_native_resource_proof": "PENDING_POSTEXIT",
        "cost_feasible": False,
        "fits": 0,
        "final_access": False,
        "old_fresh_sealed": True,
        "next_route": c["route"],
        "original_failed_proxy_seconds": 57546.0720687792,
        "cost_limit_seconds": 7200,
        "fixed_cost_without_new_charges": 57827.3920687792,
        "added_cost_view_seconds": 58061.9920687792,
        "ledger": {
            "fully_paid_reserve_seconds": 60,
            "stage_charges": {"producer": 89.94, "independent": 84.66},
            "total_charged_seconds": 234.60,
        },
    }
    for stage, kinds in c["b4_28"]["numeric_counts"].items():
        x[stage + "_counts"] = {kind: {"attempted": n, "completed": n} for kind, n in kinds.items()}
    records = {
        "compact_outcome.json": x,
        "resource_close.json": {"ledger": copy.deepcopy(x["ledger"])},
        "audit_receipts/final_scope_summary.json": {"complete_resource_acceptance": False},
        "audit_receipts/final_postexit_proof.json": {"passed": True},
        "audit_receipts/platform_exit_binding.json": {
            "passed": False,
            "whole_observed_peak_rss_bytes": None,
            "preparation_native": None,
        },
        "audit_receipts/platform_prepare_command.json": {"exit_code": 1, "native": None},
    }
    commands = []
    for stage, wall in (("producer", 79.94), ("independent", 74.66)):
        text = f"{wall} real 10.2 user .2 sys\n32768 maximum resident set size\n"
        records["profiles/" + stage + ".time"] = text
        commands.append({"name": stage, "exit_code": 0, "native": common.native(text)})
    records["audit_receipts/execution_commands.json"] = commands
    return records, c, tmp_path


def both(panel):
    records, c, output = panel
    reviewed = candidate.review(records, c, output)
    common.save(output / "review.json", reviewed)
    return reviewed, independent.audit(records, c, output)


def test_full_review_separate_decimal_and_unknowns(panel):
    reviewed, audited = both(panel)
    assert reviewed["passed"] and audited["passed"]
    assert audited["facts"]["cost_before_q29"] > 7200
    assert audited["facts"]["q28"] == 234.60
    assert audited["facts"]["full_training_memory"] == "PENDING"
    assert audited["facts"]["b4_28_whole_peak_rss_bytes"] is None
    assert not audited["facts"]["fit_authorized"]


@pytest.mark.parametrize(
    "key,value",
    [
        ("source_revision", "unmerged"),
        ("integrity_passed", False),
        ("local_fidelity_passed", False),
        ("new_predicates_passed", 3231),
        ("legacy_failed", 68),
        ("legacy_fem", 431),
        ("legacy_first_timings", 215),
        ("pointwise_states", 199),
        ("historical_b4_24_seconds", 0),
        ("historical_b4_25_seconds", 0),
        ("historical_b4_24_planning_rss", 0),
        ("historical_b4_24_whole_peak_rss", 32768),
        ("historical_b4_24_whole_memory_proof", True),
        ("historical_b4_19_case_gap_counts", "known"),
        ("full_training_memory", "PASS"),
        ("fits", 1),
        ("final_access", True),
        ("old_fresh_sealed", False),
        ("cost_feasible", True),
        ("added_cost_view_seconds", 7000),
        ("whole_native_resource_proof", "PASS"),
    ],
)
def test_scalar_tampering(panel, key, value):
    panel[0]["compact_outcome.json"][key] = value
    reviewed, audited = both(panel)
    assert not reviewed["passed"] and not audited["passed"]


@pytest.mark.parametrize(
    "change",
    [
        "missing_interval",
        "duplicate_interval",
        "failed_interval",
        "too_many_pieces",
        "local_value",
        "local_increment",
        "local_gradient",
        "local_sign",
        "duplicate_failure",
        "native_charge",
        "repaired_prep",
    ],
)
def test_complete_population_and_resource_tampering(panel, change):
    records, _, _ = panel
    x = records["compact_outcome.json"]
    if change == "missing_interval":
        x["intervals"].pop()
    elif change == "duplicate_interval":
        x["intervals"][-1] = copy.deepcopy(x["intervals"][0])
    elif change == "failed_interval":
        x["intervals"][0]["predicates"][0] = False
    elif change == "too_many_pieces":
        x["intervals"][0]["pieces"] = 257
    elif change.startswith("local_"):
        key = {
            "local_value": "normalized_value_error",
            "local_increment": "increment_relative_error",
            "local_gradient": "gradient_relative_error",
            "local_sign": "increment_sign_agrees",
        }[change]
        x["local_states"][0]["metrics"][key] = False if change == "local_sign" else 1.0
    elif change == "duplicate_failure":
        x["legacy_failed_positions"][-1] = x["legacy_failed_positions"][0]
    elif change == "native_charge":
        x["ledger"]["stage_charges"]["producer"] = 0
    else:
        records["audit_receipts/platform_exit_binding.json"]["whole_observed_peak_rss_bytes"] = (
            32768
        )
    reviewed, audited = both(panel)
    assert not reviewed["passed"] and not audited["passed"]


def reader(tmp_path, data=b'{"x":1}', name="compact.json"):
    root = tmp_path / "b4-28-active-set-numerical-evidence"
    root.mkdir()
    (root / name).write_bytes(data)
    spec = {
        "allowed_input_root_name": root.name,
        "inputs_sha256": {name: common.sha(data)},
        "max_input_file_bytes": 100,
    }
    return common.Inputs(root, tmp_path / "access.jsonl", spec), root


def test_forbidden_read_rejected_before_any_open(tmp_path, monkeypatch):
    inputs, _ = reader(tmp_path)
    monkeypatch.setattr(Path, "read_bytes", lambda self: pytest.fail("input bytes opened"))
    with pytest.raises(ValueError, match="before open"):
        inputs.load("producer.json")
    assert inputs.journal.stat().st_size == 0


def test_sha_before_json_decode_and_durable_prefix(tmp_path):
    inputs, root = reader(tmp_path)
    (root / "compact.json").write_bytes(b"broken")
    with pytest.raises(ValueError, match="identity"):
        inputs.load("compact.json")
    events = [json.loads(line) for line in inputs.journal.read_text().splitlines()]
    assert [v["phase"] for v in events] == ["before"]


@pytest.mark.parametrize("data", [b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1,"x":2}'])
def test_nonfinite_duplicate_keys_fail(tmp_path, data):
    inputs, _ = reader(tmp_path, data)
    with pytest.raises(ValueError):
        inputs.load("compact.json")


def test_symlink_and_size_rejected_without_bytes(tmp_path):
    inputs, root = reader(tmp_path)
    (root / "compact.json").unlink()
    (root / "compact.json").symlink_to(tmp_path / "sealed.json")
    (tmp_path / "sealed.json").write_bytes(b'{"x":1}')
    with pytest.raises(ValueError):
        inputs.load("compact.json")
    (root / "compact.json").unlink()
    (root / "compact.json").write_bytes(b" " * 101)
    with pytest.raises(ValueError):
        inputs.load("compact.json")


def test_independent_audit_never_calls_reviewer(panel, monkeypatch):
    records, c, output = panel
    common.save(output / "review.json", candidate.review(records, c, output))
    monkeypatch.setattr(
        candidate, "review", lambda *a: pytest.fail("reviewer called by independent audit")
    )
    assert independent.audit(records, c, output)["passed"]
    tree = ast.parse(Path(independent.__file__).read_text())
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    assert "b4_29_outcome_review" not in imports


def test_plan_does_not_open_inputs_or_create_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(
        common.Inputs, "all", lambda *a: pytest.fail("metadata opened while planning")
    )
    output = tmp_path / "output"
    assert (
        execution.main(["--input-root", str(tmp_path / "missing"), "--output-root", str(output)])
        == 0
    )
    assert not output.exists()
    assert json.loads(capsys.readouterr().out)["numerical_calls"] == 0


@pytest.mark.parametrize(
    "profile", [".1 real .1 user .0 sys", ".1 real .1 user .0 sys\n0 maximum resident set size"]
)
def test_missing_native_rss_not_zero_acceptance(profile):
    with pytest.raises(ValueError):
        common.native(profile)


def test_source_gate_before_metadata_or_output(tmp_path, monkeypatch):
    monkeypatch.setattr(
        common, "release", lambda *a: (_ for _ in ()).throw(ValueError("source gate"))
    )
    with pytest.raises(ValueError, match="source gate"):
        common.execute_stage(
            "review", tmp_path, tmp_path, lambda *a: pytest.fail("algorithm entered")
        )
    assert not (tmp_path / "review.access.jsonl").exists()


def test_stage_failure_traceback_and_exclusive_no_retry(tmp_path, monkeypatch):
    inputs, root = reader(tmp_path)
    spec = inputs.spec
    inputs.journal.unlink()
    monkeypatch.setattr(common, "contract", lambda: spec)
    monkeypatch.setattr(common, "release", lambda *a: "released")
    monkeypatch.setattr(common, "plan_payload", lambda: {"plan_sha256": "plan"})
    result = common.execute_stage(
        "review", root, tmp_path, lambda *a: (_ for _ in ()).throw(RuntimeError("kept failure"))
    )
    assert not result["passed"] and "kept failure" in result["traceback"]
    assert result["numerical_calls"] == 0
    prior = (tmp_path / "review.json").read_bytes()
    with pytest.raises(FileExistsError):
        common.execute_stage("review", root, tmp_path, lambda *a: {})
    assert (tmp_path / "review.json").read_bytes() == prior


def test_resource_charge_full_reserve_and_failure_stop(tmp_path, monkeypatch):
    (tmp_path / "audit_receipts").mkdir()
    monkeypatch.setattr(execution, "release", lambda *a: "source")
    monkeypatch.setattr(execution, "plan_payload", lambda: {"plan_sha256": "plan"})
    commands = []
    for stage in ("review", "independent"):
        common.save(
            tmp_path / (stage + ".json"),
            {"passed": True, "internal_seconds": 1, "facts": {"cost_before_q29": 58061.9920687792}},
        )
        commands.append(
            {
                "name": stage,
                "native": None,
                "observed_outer_wall_seconds": 2,
                "exit_code": 1,
                "terminated": False,
            }
        )
    common.save(tmp_path / "audit_receipts/execution_commands.json", commands)
    result = execution.close(tmp_path)
    assert result["q29_seconds"] == 84 and result["fully_paid_reserve_seconds"] == 60
    assert not result["own_stage_resource_acceptance"]
    assert not result["cost_feasible"] and not result["fit_authorized"]
    assert (
        result["b4_28_whole_peak_rss_bytes"] is None and result["full_training_memory"] == "PENDING"
    )
