"""B4.14 immutable compact evidence and failure-preserving mechanism bounds."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import b4_14_generalist_method_review as review  # noqa: E402
import b4_14_independent_audit as independent  # noqa: E402
import b4_14_resource_close as closure  # noqa: E402


def fixture():
    cohorts = {}
    for name, (n, q, classifications, pairs) in review.plan_payload()["cohorts"].items():
        rows = []
        for i in range(n):
            generalist = i < pairs // 3
            scale = "small" if i == 0 else "large"
            for method in review.METHODS:
                has_pair = generalist and method.startswith("P/")
                failed = i == 1 and method == "P/17" and name == "fresh"
                candidate = {
                    "succeeded": not failed,
                    "converged": True,
                    "iterations": 60,
                    "quality_reasons": ["compliance_above_matched_uniform"] if failed else [],
                }
                rows.append(
                    {
                        "case_id": f"case-{i:03d}",
                        "method": method,
                        "scale": scale,
                        "direction": "y",
                        "route": "generalist" if generalist else "specialist",
                        "seconds": 15.0 if failed else 8.0,
                        "uniform_seconds": 10.0,
                        "fallback_seconds": 5.0 if failed else 0.0,
                        "candidate": candidate,
                        "fallback": {} if failed else None,
                        "performed_iterations": 60,
                        "before": {"succeeded": not failed, "compliance_ratio": 1.003}
                        if has_pair
                        else None,
                        "endpoint": {"compliance_ratio": 1.002} if has_pair else None,
                        "triggered": failed,
                        "added_updates": 20 if failed else 0,
                    }
                )
        assert len(rows) == q
        cohorts[name] = {
            "cases": n,
            "rows": rows,
            "terminal_classifications": classifications,
            "strata": [],
            "scientific_decision": {"passed": name == "sentinel"},
        }
    return {
        "cohorts": cohorts,
        "plan": {"methods": list(review.METHODS)},
        "next_mechanism": "generalist_reliability_refinement_method_review",
        "repaired_gate": False,
        "final_access": False,
        "old_fresh_sealed": True,
    }


def test_plan_opens_no_bytes_creates_nothing(monkeypatch, tmp_path, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail("static plan must not read source/evidence bytes")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    output = tmp_path / "output"
    assert (
        review.main(["--diagnosis-root", str(tmp_path / "input"), "--output-root", str(output)])
        == 0
    )
    assert not output.exists()
    plan = json.loads(capsys.readouterr().out)
    assert plan == review.plan_payload()
    assert len(plan["bindings"]) == 10
    assert plan["solver_calls"] == plan["raw_terminal_byte_reads"] == 0
    assert plan["label_model_byte_reads"] == plan["final_artifact_reads"] == 0
    assert not plan["length_or_threshold_search"]


def test_changed_metadata_rejected_before_diagnosis_read(tmp_path, monkeypatch):
    path = tmp_path / "audit_receipts/plan.json"
    path.parent.mkdir()
    path.write_bytes(b"{}\n")
    calls = []
    original = review.read

    def observed(root, name, *args):
        calls.append(name)
        return original(root, name, *args)

    monkeypatch.setattr(review, "read", observed)
    with pytest.raises(ValueError, match="checksum"):
        review.check_inputs(tmp_path)
    assert calls == ["audit_receipts/plan.json"]


def test_complete_review_agrees_with_independent_arithmetic():
    source = fixture()
    result = review.review(source)
    audited = independent.reconstruct(source, result)
    assert audited["compact_rows"] == 684 and audited["prior_witness_pairs"] == 159
    assert result["cohorts"]["fresh"]["failures"]["P/17"] == 1
    assert not result["repaired_gate"] and not result["next_slice_started"]


@pytest.mark.parametrize("change", ["drop", "duplicate", "method", "status", "cost"])
def test_changed_complete_population_rejected(change):
    source = fixture()
    rows = source["cohorts"]["fresh"]["rows"]
    if change == "drop":
        rows.pop()
    elif change == "duplicate":
        rows[1] = copy.deepcopy(rows[0])
    elif change == "method":
        rows[1]["method"] = "P/99"
    elif change == "status":
        rows[0]["candidate"]["succeeded"] = False
    else:
        rows[0]["seconds"] = float("nan")
    with pytest.raises(ValueError):
        review.review(source)


@pytest.mark.parametrize("change", ["before", "endpoint", "certificate", "seed", "seal"])
def test_method_recommendation_requires_frozen_quality_gap(change):
    source = fixture()
    failed = next(
        r
        for r in source["cohorts"]["fresh"]["rows"]
        if r["method"] == "P/17" and not r["candidate"]["succeeded"]
    )
    if change == "before":
        failed["before"]["succeeded"] = True
    elif change == "endpoint":
        failed["endpoint"]["compliance_ratio"] = 1.004
    elif change == "certificate":
        failed["candidate"]["converged"] = False
    elif change == "seed":
        failed["candidate"]["succeeded"] = True
        failed["fallback"] = None
    else:
        source["final_access"] = True
    with pytest.raises(ValueError, match="condition"):
        review.review(source)


def test_perfect_rejection_and_fallback_subtraction_preserve_observed_failure():
    rows = fixture()["cohorts"]["fresh"]["rows"]
    failed = next(r for r in rows if r["method"] == "P/17" and not r["candidate"]["succeeded"])
    for scenario in review.plan_payload()["scenarios"]:
        result = review.margin([failed], scenario, 1.0)
        assert result["observed_failures"] == 1 and result["observed_statuses_preserved"]
    failed["seconds"] = 20
    optimistic = review.margin([failed], "fallback_free", 1.0)
    assert optimistic["mean_paired_ratio"] == 1.5
    assert optimistic["signed_constant_overhead_seconds"] == pytest.approx(-5)
    assert optimistic["required_mean_ratio_reduction"] == 0.5


def test_constant_headroom_is_paid_per_case_with_paired_denominators():
    rows = [
        {
            "seconds": 5,
            "uniform_seconds": 10,
            "fallback_seconds": 0,
            "candidate": {"succeeded": True},
        },
        {
            "seconds": 15,
            "uniform_seconds": 20,
            "fallback_seconds": 0,
            "candidate": {"succeeded": True},
        },
    ]
    result = review.margin(rows, "measured", 0.9)
    overhead = result["signed_constant_overhead_seconds"]
    assert sum((r["seconds"] + overhead) / r["uniform_seconds"] for r in rows) / 2 == pytest.approx(
        0.9
    )


def test_complete_uniform_shadow_always_pays_positive_candidate_cost():
    result = review.review(fixture())
    for cohort in result["cohorts"].values():
        for floor in cohort["fixed_primary"]["complete_uniform_shadow"].values():
            assert floor["every_query_floor_above_uniform"] and floor["mean_ratio_floor"] > 1


def test_auditor_detects_failure_erasure_and_cost_retiming():
    source = fixture()
    for key, value in (("observed_failures", 0), ("mean_paired_ratio", 0.01)):
        result = review.review(source)
        result["cohorts"]["fresh"]["fixed_primary"]["scenarios"]["all"]["measured"][key] = value
        with pytest.raises(AssertionError):
            independent.reconstruct(source, result)


@pytest.mark.parametrize("nested", [True, False])
def test_output_cannot_overlap_input(tmp_path, nested):
    root, output = (tmp_path, tmp_path / "child") if nested else (tmp_path / "child", tmp_path)
    with pytest.raises(ValueError, match="separate"):
        review.roots(root, output)


def test_guard_rejects_symlink_escape_before_bytes(tmp_path):
    root = tmp_path / "input"
    root.mkdir()
    path = tmp_path / "outside.json"
    path.write_bytes(b"{}\n")
    (root / "link.json").symlink_to(path)
    with pytest.raises(ValueError, match="escapes"):
        review.read(root, "link.json")


@pytest.mark.parametrize(
    "entry,filename,error",
    [
        (review.main, "review.json", ValueError),
        (independent.main, "independent_audit.json", AssertionError),
        (closure.main, "resource_close.json", AssertionError),
    ],
)
def test_publication_refuses_overwrite_before_input_access(tmp_path, entry, filename, error):
    root = tmp_path / "b4-13-preservation-diagnosis"
    output = tmp_path / "b4-14-generalist-method-review"
    output.mkdir()
    target = output / filename
    target.write_bytes(b"unchanged publication\n")
    arguments = ["--diagnosis-root", str(root), "--output-root", str(output)]
    if entry is review.main:
        arguments.append("--execute")
    with pytest.raises(error, match="overwrite"):
        entry(arguments)
    assert target.read_bytes() == b"unchanged publication\n"


def resource_fixture(tmp_path, monkeypatch):
    source = fixture()
    report = review.review(source)
    audit = independent.reconstruct(source, report)
    audit.update(passed=True, review_sha256=review.sha(review.canonical(report)))
    report.update(charged_seconds=10.1, peak_rss_bytes=100)
    audit["review_sha256"] = review.sha(review.canonical(report))
    audit.update(charged_seconds=10.2, peak_rss_bytes=200)
    directory = tmp_path / "profiles"
    directory.mkdir()
    for name in ("review", "independent", "failed_attempt"):
        (directory / (name + ".time")).write_bytes(b"synthetic profile\n")
    monkeypatch.setattr(closure, "profile", lambda path: (1.0, 300))
    monkeypatch.setattr(closure, "peak_rss", lambda: 250)
    commands = [
        {"profile": "profiles/review.time", "exit_code": 0},
        {"profile": "profiles/independent.time", "exit_code": 0},
        {"profile": "profiles/failed_attempt.time", "exit_code": 1},
    ]
    return report, audit, commands


def test_resource_closure_pays_failed_attempt_and_full_closer(tmp_path, monkeypatch):
    report, audit, commands = resource_fixture(tmp_path, monkeypatch)
    result = closure.close_resources(tmp_path, report, audit, commands)
    assert result["charged_seconds"] == 63 and result["close_charge_seconds"] == 30
    assert len(result["processes"]) == 3


@pytest.mark.parametrize("change", ["duplicate", "escape", "cost", "gate", "audit"])
def test_resource_closure_rejects_incomplete_or_changed_evidence(tmp_path, monkeypatch, change):
    report, audit, commands = resource_fixture(tmp_path, monkeypatch)
    if change == "duplicate":
        commands.append(commands[0])
    elif change == "escape":
        commands[-1]["profile"] = "../escaped.time"
    elif change == "cost":
        report["charged_seconds"] = 61
        audit["review_sha256"] = review.sha(review.canonical(report))
    elif change == "gate":
        report["repaired_gate"] = True
        audit["review_sha256"] = review.sha(review.canonical(report))
    else:
        audit["compact_rows"] = 683
    with pytest.raises(ValueError):
        closure.close_resources(tmp_path, report, audit, commands)


def test_profile_symlink_escape_rejected_before_profiler_read(tmp_path, monkeypatch):
    report, audit, commands = resource_fixture(tmp_path, monkeypatch)
    path = tmp_path / "profiles/review.time"
    path.unlink()
    path.symlink_to(tmp_path.parent / "outside.time")

    def forbidden(path):
        pytest.fail("escaping profile must be rejected before reading bytes")

    monkeypatch.setattr(closure, "profile", forbidden)
    with pytest.raises(ValueError, match="escapes"):
        closure.close_resources(tmp_path, report, audit, commands)


@pytest.mark.parametrize("limit", ["whole_seconds", "rss"])
def test_complete_resource_caps_include_failed_attempts(tmp_path, monkeypatch, limit):
    report, audit, commands = resource_fixture(tmp_path, monkeypatch)
    if limit == "rss":
        monkeypatch.setattr(closure, "peak_rss", lambda: 1073741825)
    else:
        monkeypatch.setattr(
            closure, "profile", lambda path: (170.0 if path.stem == "failed_attempt" else 1.0, 300)
        )
    with pytest.raises(ValueError, match="whole"):
        closure.close_resources(tmp_path, report, audit, commands)
