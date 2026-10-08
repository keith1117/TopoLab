"""Prospective cumulative accounting, unchanged science and paid invocation guards."""

import importlib
from copy import deepcopy
from decimal import Decimal
from pathlib import Path

import pytest

from topolab import b4_reflection_repair as original


@pytest.fixture
def scripts(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return {
        name: importlib.import_module("b4_30_" + name)
        for name in ("common", "native_execution", "z_reflection_repair")
    }


def test_separate_contract_preserves_all_scientific_fields_and_original_source(scripts):
    common = scripts["common"]
    old, new = original.contract(), common.contract()
    for key in (
        "candidate",
        "population",
        "sentinel_gate",
        "fresh_gate",
        "fresh_grid",
        "methods",
        "numerical_criteria",
        "independent_audit_arithmetic_rtol_atol",
        "query_order_salt",
        "protected_external_metadata_sha256",
        "preserved_historical_source_and_contract_sha256",
        "stops",
    ):
        assert new[key] == old[key]
    assert new["continuation"]["original_contract_sha256"] == original.CONTRACT_SHA256
    assert common.digest(original.CONTRACT_PATH) == original.CONTRACT_SHA256
    plan = scripts["z_reflection_repair"].execution_plan()
    assert plan["assignments"] == original.plan()["assignments"]
    assert plan["cases"] == original.plan()["cases"]
    assert plan["contract_sha256"] == common.CONTRACT_SHA != original.CONTRACT_SHA256
    assert plan["version"] != original.VERSION


def test_retained_failure_is_paid_once_and_both_reserves_remain(scripts):
    common = scripts["common"]
    assert common.whole_charge([]) == Decimal("371.9666532080154866")
    assert common.whole_charge([{"closed_charge_decimal": "1.0000000000000001"}]) == Decimal(
        "372.9666532080154867"
    )
    assert common.stage_cap("sentinel", "reference") == Decimal("3588.0333467919845134")
    assert common.stage_cap("fresh", "reference") == Decimal(3600)
    for cohort in ("sentinel", "fresh"):
        assert common.stage_cap(cohort, "screen") == 21600
        assert common.stage_cap(cohort, "audit") == common.stage_cap(cohort, "policy-audit") == 3600
        assert common.stage_cap(cohort, "independent") == 1800


@pytest.mark.parametrize(
    "charge,complete,allowed",
    [
        ("8628.0333467919845134", True, True),
        ("8628.0333467919845135", True, False),
        ("8628.0333467919845134", False, False),
        ("8820", True, False),
    ],
)
def test_full_fresh_reservation_uses_exact_paid_prefix_not_old_free_admission(
    scripts, charge, complete, allowed
):
    assert (
        scripts["common"].fresh_admissible([{"closed_charge_decimal": charge}], complete) is allowed
    )


def test_immutable_prefix_inventory_and_cost_identity_required(scripts, monkeypatch, tmp_path):
    common = scripts["common"]
    c = deepcopy(common.contract())
    f = c["continuation"]
    root = tmp_path / f["original_failed_root_name"]
    common.save(
        root / "resource_close.json",
        {
            "charged_decimal": f["original_failed_charge_decimal"],
            "closed": True,
            "fresh_sealed": True,
            "source_revision": f["original_failed_source"],
        },
    )
    common.save(root / "failed_exit.json", {"exit_code": 1, "numeric_calls": 0})
    f["original_failed_evidence_sha256"] = {p.name: common.digest(p) for p in root.iterdir()}
    audit = f["original_independent_metadata_audit"]
    common.save(tmp_path / audit["path"], {"passed": True})
    audit["sha256"] = common.digest(tmp_path / audit["path"])
    monkeypatch.setattr(common, "contract", lambda: c)
    common.guard_failed_prefix(tmp_path)
    (root / "failed_exit.json").write_bytes(b"{}\n")
    with pytest.raises(ValueError, match="prefix changed"):
        common.guard_failed_prefix(tmp_path)
    common.save(root / "extra_retry.json", {"campaigns": 3})
    with pytest.raises(ValueError, match="inventory changed"):
        common.guard_failed_prefix(tmp_path)


@pytest.mark.parametrize("changed", ["third", "refund", "extra", "final"])
def test_release_refuses_third_invocation_refund_or_expanded_authority(
    scripts, monkeypatch, tmp_path, changed
):
    common = scripts["common"]
    c = deepcopy(common.contract())
    authority = {
        "authorized": True,
        "administrative_campaign_invocations_maximum": 2,
        "additional_paid_invocations_authorized": 1,
        "already_used_administrative_invocations": 1,
        "completed_numerical_campaigns_maximum": 1,
        "approved_machine_proposal_sha256": c["authority"][
            "owner_approved_machine_proposal_sha256"
        ],
        "next_slice_authorized": False,
        "final_access": changed == "final",
    }
    if changed == "extra":
        authority["additional_paid_invocations_authorized"] = 2
    path = tmp_path / "authority.json"
    common.save(path, authority)
    c["authority"]["owner_authorization_sha256"] = common.digest(path)
    value = {
        "source_revision": "a" * 40,
        "passed": True,
        "main_ci_passed": True,
        "all_applicable_ci_passed_before_merge": True,
        "source_tree_same": True,
        "plan": {"source": "synthetic"},
        "owner_authorization_path": str(path),
        "owner_authorization_sha256": common.digest(path),
        "administrative_invocation": 3 if changed == "third" else 2,
        "retained_failed_charge_decimal": "0"
        if changed == "refund"
        else c["continuation"]["original_failed_charge_decimal"],
    }
    monkeypatch.setattr(common, "contract", lambda: c)
    monkeypatch.setattr(common, "plan_payload", lambda: value["plan"])
    monkeypatch.setattr(
        common.subprocess,
        "check_output",
        lambda argv, **kwargs: (
            "a" * 40 if argv[1] == "rev-parse" else "main" if argv[1] == "branch" else b""
        ),
    )
    for name in common.THREADS:
        monkeypatch.setenv(name, "1")
    with pytest.raises(ValueError, match="no third invocation"):
        common.validate_release_source(value)
    assert not (tmp_path / c["evidence_root_name"]).exists()


def test_native_close_retains_failed_fee_on_completed_negative_sentinel(
    scripts, monkeypatch, tmp_path
):
    common, native = scripts["common"], scripts["native_execution"]
    monkeypatch.setattr(native, "release", lambda output: "a" * 40)
    monkeypatch.setattr(
        native,
        "stage_charges",
        lambda output, cohort: (
            100,
            True,
            [
                {
                    "closed_charge_decimal": "100",
                    "peak_rss_bytes": 1000,
                }
            ],
        ),
    )
    common.save(
        tmp_path / "sentinel/independent_audit.json", {"passed": True, "gate_passed": False}
    )
    value = native.close(tmp_path)
    assert value["charged_decimal"] == "471.9666532080154866"
    assert value["aggregate_fully_paid_chain_reserve_seconds"] == 360
    assert value["administrative_campaigns"] == 2
    assert value["own_stage_resource_acceptance"] and value["fresh_sealed"]
    assert not value["repair_gate_passed_before_postexit"]
    assert value["whole_resource_acceptance"] == "PENDING_POSTEXIT"
