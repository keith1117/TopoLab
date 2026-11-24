"""The new certificate command identifies its own plan only after the audit returns."""

import runpy
from pathlib import Path
from types import SimpleNamespace

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
control = runpy.run_path(str(SCRIPTS / "p17_m2_source_acquisition_control.py"))
result = control["certificate_result"]


def facts():
    return {
        "scope": "SOURCE_ATTESTED_RESTRICTED_INPUT_VERSION_ONLY",
        "plan": {
            "formal_authority": True,
            "execution_identity": ("topolab.v2.p17-m2-registered-source-acquisition."
                                   "certificate-20261124.v1"),
        },
        "plan_sha256": "a" * 64,
        "version_id": "b" * 64,
        "manifest": {"members": ["test member"]},
    }


def test_formal_result_binds_exact_plan_and_version_after_audit():
    source, actual, observed = facts(), {"role": []}, []

    def audit(bundle, *, trusted_tool_events):
        observed.append((bundle, trusted_tool_events))

    value = result(source, actual, SimpleNamespace(audit_certificate=audit))
    assert observed == [(source, actual)]
    assert value["plan_sha256"] == source["plan_sha256"]
    assert value["version_id"] == source["version_id"]
    assert value["member_count"] == 1 and value["source_input_accepted"] is True


def test_rejected_audit_cannot_generate_formal_result():
    def reject(bundle, *, trusted_tool_events):
        raise ValueError("software closure/source freeze differs")

    with pytest.raises(ValueError, match="source freeze"):
        result(facts(), {}, SimpleNamespace(audit_certificate=reject))
