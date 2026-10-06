"""Finite fidelity, full cost, independent reconstruction and interrupted evidence."""

import copy
import json
import sys
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_23_independent_audit as independent  # noqa: E402
import b4_23_resource_close as closure  # noqa: E402
import b4_23_versioned_surrogate_feasibility as probe  # noqa: E402
from test_b4_20_surrogate_correctness import synthetic  # noqa: E402


def argv(tmp_path, execute=False):
    paths = {
        "review": "b4-22-stable-projection-correctness",
        "data": "b3-v1-data",
        "output": "b4-23-versioned-surrogate-feasibility",
    }
    return [x for k, v in paths.items() for x in ("--" + k + "-root", str(tmp_path / v))] + (
        ["--execute"] if execute else []
    )


@pytest.mark.parametrize("main", [probe.main, independent.main, closure.main])
def test_static_plan_reads_no_artifacts_or_creates_output(tmp_path, monkeypatch, capsys, main):
    monkeypatch.setattr(Path, "read_bytes", lambda *a: pytest.fail("evidence read during plan"))
    assert main(argv(tmp_path)) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan == probe.plan_payload()
    assert len(plan["entries"]) == 8 and len(plan["states"]) == 9
    assert plan["steps"] == [1e-4, 2e-4] and plan["numerical_conditions"] == 3976
    assert plan["probe_solves"] + plan["audit_solves"] == 432
    assert plan["probe_projections"] + plan["audit_projections"] == 816
    assert len(independent.expected_events()) == 2050
    assert len(independent.expected_events(True)) == 1146
    assert not any(tmp_path.iterdir())


@pytest.mark.parametrize(
    "main,name",
    [
        (probe.main, "probe.json"),
        (independent.main, "independent_audit.json"),
        (closure.main, "resource_close.json"),
    ],
)
def test_existing_publication_is_not_overwritten(tmp_path, main, name):
    output = tmp_path / "b4-23-versioned-surrogate-feasibility"
    output.mkdir()
    target = output / name
    target.write_bytes(b"keep")
    with pytest.raises(ValueError, match="overwrite"):
        main(argv(tmp_path, True))
    assert target.read_bytes() == b"keep"


def test_role_and_changed_binding_stop_before_training_byte_lookup(monkeypatch):
    from topolab.b3_catalog import build_b3_case_catalog

    for role in ("fit_validation", "screen_validation", "final_id", "final_ood"):
        entry = next(e for e in build_b3_case_catalog().entries if e.role == role)
        with pytest.raises(ValueError, match="only frozen eight"):
            probe.train_label(Path("/unused"), None, entry)
    monkeypatch.setattr(
        probe, "safe_hash", lambda *a: (_ for _ in ()).throw(ValueError("changed binding"))
    )
    monkeypatch.setattr(probe, "train_label", lambda *a: pytest.fail("unregistered label access"))
    with pytest.raises(ValueError, match="changed binding"):
        probe.check_inputs(Path("/unused"), Path("/unused"))


def test_complete_synthetic_panel_and_every_paid_call_are_independently_reconstructed(
    tmp_path, monkeypatch
):
    # Public case definitions and synthetic designs; no production label bytes.
    records = {}
    for entry in probe.selected_entries():
        anchor, stored, cs, _ = synthetic(entry)
        records[entry.case.case_id] = SimpleNamespace(
            stored=SimpleNamespace(
                design_density=anchor.tolist(),
                physical_density=stored.tolist(),
                compliance=cs.compliance,
            )
        )

    def label(data, index, entry):
        return records[entry.case.case_id], {"synthetic": entry.case.case_id}

    monkeypatch.setattr(probe, "train_label", label)
    monkeypatch.setattr(independent, "train_label", label)
    journal = probe.Journal(tmp_path / "probe.events.jsonl", "a" * 40)
    panel = probe.probe(None, None, journal, perf_counter())
    panel.update(source_revision="a" * 40, charged_seconds=11, peak_rss_bytes=100)
    journal.emit("complete")
    journal.close()
    panel["journal_sha256"] = probe.sha((tmp_path / "probe.events.jsonl").read_bytes())
    assert independent.journal_check(tmp_path, panel) == 2050
    assert panel["counts"]["fem"] == {"attempted": 216, "completed": 216}
    audit_journal = probe.Journal(tmp_path / "independent.events.jsonl", "a" * 40)
    audit = independent.audit(panel, None, None, audit_journal, perf_counter())
    audit.update(charged_seconds=11, peak_rss_bytes=100)
    audit_journal.emit("complete")
    audit_journal.close()
    audit["journal_sha256"] = probe.sha((tmp_path / "independent.events.jsonl").read_bytes())
    assert audit["integrity_passed"] and audit["failed_numerical_conditions"] == 0
    assert audit["numerical_conditions"] == 3976 and audit["arithmetic_conditions"] == 960
    assert audit["total_solver_calls"] == 432 and audit["total_projection_calls"] == 816
    assert audit["local_states"] == 32 and audit["central_states"] == 72
    events, counts, pending = independent.event_prefix(tmp_path, "independent", "a" * 40)
    assert len(events) == 1146 and not pending and counts == audit_journal.counts
    assert [e["event"] for e in events] == independent.expected_events(True)
    for change in ("root", "first_timing", "side", "order", "counter"):
        damaged = copy.deepcopy(panel)
        if change == "root":
            damaged["rows"][0]["projection"]["offset"] += 0.01
        elif change == "first_timing":
            damaged["rows"][0]["timings"][0]["wall_seconds"] *= 0.5
        elif change == "side":
            damaged["rows"][0]["differences"][0]["sides"][1]["exact"] += 0.01
        elif change == "order":
            damaged["rows"].reverse()
        else:
            damaged["counts"]["projection"]["completed"] -= 1
        with pytest.raises(ValueError):
            independent.journal_check(tmp_path, damaged)
    commands = native_commands(tmp_path)
    monkeypatch.setattr(closure, "peak_rss", lambda: 100)
    result = closure.close_resources(tmp_path, commands, panel, audit)
    assert result["closed"] and result["charged_seconds"] == 84
    assert result["full_panel_complete"] and result["full_fit_memory_feasibility_pending"]
    assert result["fit_proxy"]["total_prospective_seconds"] == pytest.approx(
        independent.independent_proxy(panel, 84)["total_prospective_seconds"], rel=1e-12
    )


def cost_fixture():
    return {
        "rows": [
            {"case_id": s, "scale": s, "timings": [{"wall_seconds": v}] * 3}
            for s, v in (("small", 0.001), ("large", 0.002))
        ],
        "setup": [
            {"case_id": s, "wall_seconds": 0.01, "retained_array_bytes": 100}
            for s in ("small", "large")
        ],
    }


def test_all_history_full_population_and_first_timing_remain_paid():
    panel = cost_fixture()
    cost = closure.fit_proxy(panel, 100)
    assert sum(probe.plan_payload()["prior_charged_seconds"]) == pytest.approx(707.91)
    assert cost["total_prospective_seconds"] == pytest.approx(5135.164341)
    assert cost["population_retained_array_bytes_estimate"] == 50800
    assert cost["cost_feasible"] and cost["full_fit_memory_feasibility_pending"]
    for key, value in independent.independent_proxy(panel, 100).items():
        assert cost[key] == pytest.approx(value, rel=1e-12)
    panel["rows"][0]["timings"][0]["wall_seconds"] = 1
    assert not closure.fit_proxy(panel, 100)["cost_feasible"]
    panel = cost_fixture()
    panel["setup"][0]["wall_seconds"] = 2
    assert closure.fit_proxy(panel, 100)["full_population_preparation_seconds"] == pytest.approx(
        3.75 * (432 * 2 + 76 * 0.01)
    )


@pytest.mark.parametrize(
    "integrity,fidelity,cost,following",
    [
        (False, True, True, probe.CORRECTNESS_NEXT),
        (True, False, True, probe.FIDELITY_NEXT),
        (True, True, False, probe.COST_NEXT),
        (True, True, True, probe.FIT_NEXT),
    ],
)
def test_ordered_failure_cannot_select_fitting(integrity, fidelity, cost, following):
    assert closure.next_slice(integrity, fidelity, cost) == following


@pytest.mark.parametrize(
    "field,value",
    [
        ("normalized_value_error", 0.000101),
        ("increment_relative_error", 0.251),
        ("gradient_relative_error", 0.251),
        ("increment_sign_agrees", False),
    ],
)
def test_fidelity_retains_all_four_original_criteria_and_stored_baseline(field, value):
    gradient = np.ones(3)
    metrics = probe.fidelity(1, 1, gradient, gradient)
    assert probe.local_pass(metrics) and not probe.local_pass({**metrics, field: value})
    nonunit = probe.fidelity(1.00005, 1.0001, gradient, gradient)
    assert nonunit["increment_relative_error"] == pytest.approx(0.5)
    assert nonunit == independent.relative_metrics(1.00005, 1.0001, gradient, gradient)


def native_commands(root, failure=False):
    (root / "profiles").mkdir(exist_ok=True)
    (root / "logs").mkdir(exist_ok=True)
    commands = []
    for name in ("plan", "probe", "independent"):
        (root / ("profiles/" + name + ".time")).write_text(
            "2 real 1 user 0 sys\n100 maximum resident set size\n"
        )
        (root / ("logs/" + name + ".log")).write_text("synthetic")
        command = {
            "name": name,
            "profile": "profiles/" + name + ".time",
            "log": "logs/" + name + ".log",
            "exit_code": int(failure and name != "plan"),
        }
        for key in ("profile", "log"):
            command[key + "_sha256"] = probe.sha((root / command[key]).read_bytes())
        commands.append(command)
    return commands


@pytest.mark.parametrize(
    "damage", ["none", "retry", "profile_hash", "log_hash", "escape", "cap", "rss"]
)
def test_native_failures_stay_paid_and_cannot_retry_or_escape(tmp_path, monkeypatch, damage):
    commands = native_commands(tmp_path, True)
    monkeypatch.setattr(closure, "peak_rss", lambda: 100)
    if damage == "retry":
        commands.append(commands[-1])
    elif damage in ("profile_hash", "log_hash"):
        commands[-1][damage.replace("hash", "sha256")] = "0" * 64
    elif damage == "escape":
        commands[-1]["profile"] = "../escape.time"
    elif damage in ("cap", "rss"):
        path = tmp_path / commands[-1]["profile"]
        path.write_text(
            "601 real 1 user 0 sys\n100 maximum resident set size\n"
            if damage == "cap"
            else "2 real 1 user 0 sys\n1073741825 maximum resident set size\n"
        )
        commands[-1]["profile_sha256"] = probe.sha(path.read_bytes())
    if damage == "none":
        result = closure.close_resources(tmp_path, commands, None, None)
        assert result["charged_seconds"] == 84 and result["paid_reservation_seconds"] == 60
        assert result["next_slice"] == probe.CORRECTNESS_NEXT and result["fit_proxy"] is None
    else:
        with pytest.raises(ValueError):
            closure.close_resources(tmp_path, commands, None, None)


def test_interrupted_exact_fem_preserves_pending_context_and_no_numerical_audit(
    tmp_path, monkeypatch
):
    commands = native_commands(tmp_path, True)
    (tmp_path / "audit_receipts").mkdir()
    (tmp_path / "audit_receipts/probe_command.json").write_bytes(probe.canonical(commands[1]))
    journal = probe.Journal(tmp_path / "probe.events.jsonl", "a" * 40)
    context = {"state": 4, "kind": "exact_fem", "direction": "cosine", "step": 0.0002, "sign": -1}

    def interrupted():
        raise ValueError("injected exact FEM stop")

    with pytest.raises(ValueError, match="injected"):
        journal.invoke("fem", "case", context, interrupted, str)
    journal.emit("abort", error="injected")
    journal.close()
    monkeypatch.setattr(independent, "energy", lambda *a: pytest.fail("new FEM after abort"))
    monkeypatch.setattr(
        independent, "independent_projection", lambda *a: pytest.fail("new root after abort")
    )
    audit = independent.abort_audit(tmp_path, "a" * 40)
    assert audit["metadata_only"] and not audit["integrity_passed"]
    assert audit["actual_probe_counts"]["fem"] == {"attempted": 1, "completed": 0}
    assert audit["pending_operations"] == ["fem"] and audit["actual_failed_context"] == context
    assert audit["new_label_fem_projection_calls"] == 0
    assert audit["full_panel_directional_error"] is None and audit["local_fidelity_passed"] is None
    with pytest.raises(FileExistsError):
        probe.Journal(tmp_path / "probe.events.jsonl", "a" * 40)
