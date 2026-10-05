"""Complete timing population, independent arithmetic and immutable closure."""

import copy
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import b4_16_independent_audit as independent  # noqa: E402
import b4_16_offline_adjoint_cost_review as review  # noqa: E402
import b4_16_resource_close as closure  # noqa: E402


def fixture():
    plan = review.prior_plan()
    rows, setup = [], []
    for entry in plan["entries"]:
        cid = entry["case"]["case_id"]
        scale = "small" if entry["case"]["problem"]["mesh"]["element_counts"][0] == 12 else "large"
        setup.append({"case_id": cid, "wall_seconds": 0.1, "cpu_seconds": 0.09})
        for state in plan["states"]:
            rows.append(
                {
                    "case_id": cid,
                    "state": state,
                    "scale": scale,
                    "timings": [
                        {
                            "wall_seconds": 0.01 if scale == "small" else 0.2,
                            "cpu_seconds": 0.009 if scale == "small" else 0.19,
                        }
                        for _ in range(3)
                    ],
                }
            )
    rows[0]["timings"][0]["wall_seconds"] = 0.14
    closed = {
        "charged_seconds": 84.33000000000001,
        "peak_rss_bytes": 100,
        "processes": [],
        "fit_proxy": {
            "additional_physics_seconds": 56760.0,
            "total_prospective_seconds": 56760.0 + 3870.204341 + 84.33,
        },
    }
    return {"plan": plan, "rows": rows, "setup": setup}, closed


def test_plan_reads_no_bytes_or_creates_output(monkeypatch, tmp_path, capsys):
    def forbidden(*args, **kwargs):
        pytest.fail("metadata plan must not read any artifact")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    output = tmp_path / "new"
    assert review.main(["--probe-root", str(tmp_path / "old"), "--output-root", str(output)]) == 0
    assert not output.exists()
    assert json.loads(capsys.readouterr().out) == review.plan_payload()


def test_complete_original_proxy_keeps_first_outlier():
    source, closed = fixture()
    result = review.review(source, closed)
    assert len(result["observations"]) == 48
    assert result["scenarios"]["original_maximum"]["unit_seconds"] == [0.14, 0.2]
    assert result["scenarios"]["zero_small"]["total_prospective_seconds"] > 7200
    assert result["next_slice"] == review.PHASE_NEXT
    assert independent.reconstruct(source, closed, result)["observations"] == 48
    assert not result["original_cost_gate_passed"] and not result["next_slice_started"]
    assert result["budget_requirements"][
        "weighted_unit_target_seconds"
    ] * 750 * 508 == pytest.approx(7200 - 3870.204341 - 84.33)


@pytest.mark.parametrize(
    "change",
    ["drop", "duplicate", "order", "repeat", "nan", "negative", "scale", "setup", "original"],
)
def test_complete_population_and_original_cost_guard(change):
    source, closed = fixture()
    if change == "drop":
        source["rows"].pop()
    elif change == "duplicate":
        source["rows"][1] = copy.deepcopy(source["rows"][0])
    elif change == "order":
        source["rows"].reverse()
    elif change == "repeat":
        source["rows"][0]["timings"].pop(0)
    elif change in ("nan", "negative"):
        source["rows"][0]["timings"][0]["wall_seconds"] = float("nan") if change == "nan" else -1
    elif change == "scale":
        source["rows"][0]["scale"] = "large"
    elif change == "setup":
        source["setup"].pop()
    else:
        closed["fit_proxy"]["total_prospective_seconds"] -= 100
    with pytest.raises(ValueError):
        review.review(source, closed)


@pytest.mark.parametrize("field", ["mean", "observation", "gate", "next"])
def test_independent_audit_detects_changed_cost_or_boundary(field):
    source, closed = fixture()
    report = review.review(source, closed)
    if field == "mean":
        report["distributions"]["large"]["wall_seconds"]["mean"] *= 0.5
    elif field == "observation":
        report["observations"].pop(0)
    elif field == "gate":
        report["original_cost_gate_passed"] = True
    else:
        report["next_slice"] = "fit now"
    with pytest.raises(ValueError):
        independent.reconstruct(source, closed, report)


def test_changed_metadata_rejected_before_probe_read(tmp_path, monkeypatch):
    path = tmp_path / "audit_receipts/plan.json"
    path.parent.mkdir()
    path.write_bytes(b"{}\n")
    reads, original = [], review.read

    def observed(root, name, *args):
        reads.append(name)
        return original(root, name, *args)

    monkeypatch.setattr(review, "read", observed)
    with pytest.raises(ValueError, match="checksum"):
        review.check_inputs(tmp_path)
    assert reads == ["audit_receipts/plan.json"]


@pytest.mark.parametrize(
    "main,name",
    [
        (review.main, "review.json"),
        (independent.main, "independent_audit.json"),
        (closure.main, "resource_close.json"),
    ],
)
def test_refuses_overwrite_before_input_access(tmp_path, main, name):
    root, output = (
        tmp_path / "b4-15-offline-compliance-adjoint",
        tmp_path / "b4-16-offline-adjoint-cost-review",
    )
    output.mkdir()
    path = output / name
    path.write_bytes(b"keep\n")
    with pytest.raises(ValueError, match="overwrite"):
        main(["--probe-root", str(root), "--output-root", str(output), "--execute"])
    assert path.read_bytes() == b"keep\n"


def test_ordered_stability_branch_requires_large_only_headroom():
    source, closed = fixture()
    for row in source["rows"]:
        if row["scale"] == "large":
            for timing in row["timings"]:
                timing.update(wall_seconds=0.02, cpu_seconds=0.019)
    additional = 750 * (432 * 0.14 + 76 * 0.02)
    closed["fit_proxy"].update(
        additional_physics_seconds=additional,
        total_prospective_seconds=additional + 3870.204341 + closed["charged_seconds"],
    )
    report = review.review(source, closed)
    assert report["next_slice"] == review.STABILITY_NEXT
    assert independent.reconstruct(source, closed, report)["next_slice"] == review.STABILITY_NEXT


def resource_fixture(tmp_path, monkeypatch):
    source, closed = fixture()
    report = review.review(source, closed)
    report.update(charged_seconds=10.1, peak_rss_bytes=100)
    audit = independent.reconstruct(source, closed, report)
    audit.update(
        review_sha256=review.sha(review.canonical(report)), charged_seconds=10.2, peak_rss_bytes=200
    )
    directory = tmp_path / "profiles"
    directory.mkdir()
    commands = []
    for name in ("review", "independent", "failed_attempt"):
        path = directory / (name + ".time")
        path.write_bytes(b"synthetic\n")
        commands.append(
            {
                "profile": "profiles/" + path.name,
                "exit_code": int(name == "failed_attempt"),
                "profile_sha256": review.sha(path.read_bytes()),
            }
        )
    monkeypatch.setattr(closure, "profile", lambda path: (1.0, 300))
    monkeypatch.setattr(closure, "peak_rss", lambda: 250)
    return report, audit, commands


def test_closure_retains_failed_attempt_and_full_reserve(tmp_path, monkeypatch):
    report, audit, commands = resource_fixture(tmp_path, monkeypatch)
    closed = closure.close_resources(tmp_path, report, audit, commands)
    assert closed["charged_seconds"] == 63
    assert closed["close_charge_seconds"] == 30 and not closed["original_cost_gate_passed"]


@pytest.mark.parametrize("change", ["hash", "duplicate", "escape", "cost", "gate", "whole", "rss"])
def test_closure_rejects_changed_receipt_and_cap_violation(tmp_path, monkeypatch, change):
    report, audit, commands = resource_fixture(tmp_path, monkeypatch)
    if change == "hash":
        commands[0]["profile_sha256"] = "0" * 64
    elif change == "duplicate":
        commands.append(commands[0])
    elif change == "escape":
        commands[-1]["profile"] = "../escaped.time"
    elif change == "cost":
        report["charged_seconds"] = 61
        audit["review_sha256"] = review.sha(review.canonical(report))
    elif change == "gate":
        report["repaired_gate"] = True
        audit["review_sha256"] = review.sha(review.canonical(report))
    elif change == "whole":
        monkeypatch.setattr(
            closure, "profile", lambda path: (170 if path.stem == "failed_attempt" else 1, 300)
        )
    else:
        monkeypatch.setattr(closure, "peak_rss", lambda: 1073741825)
    with pytest.raises(ValueError):
        closure.close_resources(tmp_path, report, audit, commands)


def test_native_profiles_preserve_complete_process_cpu(tmp_path):
    (tmp_path / "profiles").mkdir()
    for name in ("probe", "independent", "closure"):
        (tmp_path / "profiles" / (name + ".time")).write_text(
            " 1.25 real 1.1 user 0.1 sys\n 300 maximum resident set size\n"
        )
    assert review.native_profiles(tmp_path)["probe"] == {
        "wall_seconds": 1.25,
        "user_seconds": 1.1,
        "system_seconds": 0.1,
        "peak_rss_bytes": 300,
    }
