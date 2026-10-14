"""Registered B4.49 panel, candidate-free inequalities and denial controls."""

import copy
import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from topolab.combined_certificate import (
    FINGERPRINTS,
    ROLE,
    SOURCE_MAIN,
    VERSION,
    CertificateStop,
    _closed,
    evaluate,
    load_registered,
    validate,
)

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs/planning/b4_49_public_combined_diagnostic_certificate_contract.json"
CATALOG = json.loads(CONTRACT.read_text())["catalog"]


def independent_module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grant(entry):
    return {
        "id": entry["id"],
        "sha256": entry["sha256"],
        "role": ROLE,
        "version": VERSION,
        "source_main": SOURCE_MAIN,
        "space": "b4-49-public-space:" + entry["id"],
    }


@pytest.fixture(scope="module")
def panel():
    result = {}
    for entry in CATALOG:
        fixture = load_registered(
            entry["id"], lambda e=entry: (ROOT / e["path"]).read_bytes(), grant(entry)
        )
        result[entry["id"]] = (fixture, evaluate(fixture))
    return result


@pytest.mark.parametrize("entry", CATALOG, ids=[x["id"] for x in CATALOG])
def test_registered_combination_and_independent_compliance(entry, panel):
    fixture, result = panel[entry["id"]]
    assert result["status"] == entry["expected_status"]
    oracle = independent_module("b4_49_combined_oracle")
    proof = oracle.audit(fixture, result, entry["expected_status"])
    assert proof["passed"] and proof["predicates"] < 2000
    assert not result["real_fem_certified"] and not result["loss_gradient_changed"]


def test_rounded_zero_retains_actual_evaluation_error_and_nonzero_intended_residual(panel):
    fixture, result = panel["combined-rounded-zero-residual"]
    assert result["arrays"]["r_hat"] == ["0x0.0p+0"]
    assert Fraction(result["arrays"]["intended_residual"][0]) != 0
    assert Fraction(float.fromhex(result["bounds"]["beta_eval"])) > 0
    assert result["unmodified_U_certified"] is False
    assert fixture["normalizer"]["value"] == "198/25"


def test_both_representation_errors_expansion_and_separate_assembly_errors_remain(panel):
    _, result = panel["combined-nondyadic-assembly"]
    for name in (
        "d0_plus",
        "d1_plus",
        "complete_delta_plus",
        "e_plus",
        "a_plus",
        "cross_plus",
        "factor_square_plus",
        "representation_plus",
        "delta_plus",
        "beta_G",
        "beta_K",
        "beta_f",
        "beta_eval",
        "q_hat",
        "u_plus",
        "q_eval",
        "operator_solution",
        "with_operator",
        "r_plus",
        "C_s_minus",
    ):
        assert name in result["bounds"]
    assert float.fromhex(result["bounds"]["beta_K"]) > 0
    assert float.fromhex(result["bounds"]["beta_f"]) > 0
    assert result["arrays"]["U_tilde"] == "0"


@pytest.mark.parametrize("field", ["id", "sha256", "role", "version", "source_main", "space"])
def test_wrong_grant_denies_before_callback_bytes(field):
    entry = CATALOG[0]
    broken = grant(entry)
    broken[field] = "unregistered"
    reads = []
    with pytest.raises(CertificateStop, match="before bytes"):
        load_registered(entry["id"], lambda: reads.append(True) or b"{}", broken)
    assert not reads


def test_changed_public_bytes_rejected():
    entry = CATALOG[0]
    with pytest.raises(CertificateStop, match="changed public fixture"):
        load_registered(entry["id"], lambda: b"{}", grant(entry))
    assert FINGERPRINTS[entry["id"]] == entry["sha256"]


def test_mutated_prepared_state_denied_before_arithmetic(panel):
    fixture = copy.deepcopy(panel[CATALOG[0]["id"]][0])
    fixture["force"][0] = "2"
    events = []
    result = evaluate(fixture, lambda phase, data: events.append((phase, data)))
    assert result["status"] == "STOP_BINDING" and not events
    with pytest.raises(TypeError):
        FINGERPRINTS[CATALOG[0]["id"]] = "unregistered"


@pytest.mark.parametrize(
    "family",
    [
        "unknown",
        "missing",
        "bool rational",
        "ragged matrix",
        "noncanonical rational",
        "nonfinite IEEE",
        "subnormal IEEE",
        "density outside[0,1]",
    ],
)
def test_closed_finite_schema_denials(family, panel):
    fixture = copy.deepcopy(panel[CATALOG[0]["id"]][0])
    if family == "unknown":
        fixture["unknown"] = True
    elif family == "missing":
        del fixture["force"]
    elif family == "bool rational":
        fixture["force"][0] = True
    elif family == "ragged matrix":
        fixture["elements"][0][0] = []
    elif family == "noncanonical rational":
        fixture["force"][0] = "2/2"
    elif family == "nonfinite IEEE":
        fixture["u_bits"][0] = "7ff0000000000000"
    elif family == "subnormal IEEE":
        fixture["u_bits"][0] = "0000000000000001"
    else:
        fixture["rho"][0] = "2"
    with pytest.raises(CertificateStop):
        validate(fixture, CATALOG[0]["id"])


def test_duplicate_and_nonfinite_json_denials():
    with pytest.raises(CertificateStop, match="duplicate"):
        _closed([("id", "same"), ("id", "same")])
    campaign = independent_module("b4_49_certificate_campaign")
    for raw in (b'{"id":1,"id":2}', b'{"id":NaN}'):
        with pytest.raises(ValueError):
            campaign.strict(raw)


@pytest.mark.parametrize(
    "family",
    [
        "bound",
        "trace",
        "normalizer",
        "residual",
        "both Gram errors",
        "PSD",
        "coercivity",
        "flags",
        "missing case",
        "receipt identity",
    ],
)
def test_independent_forged_certificate_denials(family, panel):
    fixture, original = panel["combined-balanced-scalar"]
    result = copy.deepcopy(original)
    if family == "bound":
        result["bounds"]["B_plus"] = "0x0.0p+0"
    elif family == "trace":
        result["trace"][0]["exact"] = "0"
    elif family == "normalizer":
        result["bounds"]["C_s_minus"] = "0x1.0000000000000p+0"
    elif family == "residual":
        result["arrays"]["intended_residual"] = ["1"]
    elif family == "both Gram errors":
        del result["square_uppers"]["d1_plus"]
    elif family == "PSD":
        result["status"] = "STOP_PSD"
    elif family == "coercivity":
        result["bounds"]["lower_G_minus"] = "0x0.0p+0"
    elif family == "flags":
        result["real_fem_certified"] = True
    elif family == "missing case":
        result["trace"].pop()
    else:
        result["id"] = "unregistered"
    with pytest.raises((ValueError, KeyError)):
        independent_module("b4_49_combined_oracle").audit(fixture, result, "PASS")


def test_standalone_actual_import_durable_receipts_and_independent_process(tmp_path):
    # Regression namespace; source need not be merged and no formal quota is used.
    builder = tmp_path / "build.json"
    source = f"""import importlib.util,json
from pathlib import Path
root=Path({str(ROOT)!r})
spec=importlib.util.spec_from_file_location('builder',root/'scripts/b4_49_certificate_campaign.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
release=module.make_release(root,Path({str(tmp_path)!r}),'REGISTERED_REGRESSION_B4_49')
Path({str(builder)!r}).write_text(json.dumps(release))
"""
    subprocess.run([sys.executable, "-I", "-c", source], cwd=ROOT, check=True)
    release = json.loads(builder.read_text())
    request = tmp_path / "primary_request.json"
    request.write_text(json.dumps({"version": VERSION, "role": "primary", "release": release}))
    primary = tmp_path / "primary"
    command = [
        sys.executable,
        "-I",
        str(ROOT / "scripts/b4_49_certificate_campaign.py"),
        "run",
        str(request),
        str(primary),
    ]
    outcome = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert outcome.returncode == 0, (
        outcome.stderr,
        (primary / "failure.txt").read_text()
        if (primary / "failure.txt").exists()
        else "no child failure",
    )
    before = (primary / "pending.json").read_bytes()
    refusal = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    assert refusal.returncode != 0 and (primary / "pending.json").read_bytes() == before
    independent = tmp_path / "independent"
    audit_request = tmp_path / "independent_request.json"
    import hashlib

    audit_request.write_text(
        json.dumps(
            {
                "version": VERSION,
                "role": "independent",
                "release": release,
                "primary_root": str(primary),
                "primary_terminal_sha256": hashlib.sha256(
                    (primary / "terminal.json").read_bytes()
                ).hexdigest(),
            }
        )
    )
    outcome = subprocess.run(
        [
            sys.executable,
            "-I",
            str(ROOT / "scripts/b4_49_certificate_audit.py"),
            "run",
            str(audit_request),
            str(independent),
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert outcome.returncode == 0, (
        outcome.stderr,
        (independent / "failure.txt").read_text()
        if (independent / "failure.txt").exists()
        else "no audit failure",
    )
    summary = json.loads((independent / "result.json").read_text())
    assert summary["case_audits"] == 12 and summary["predicates"] <= 16000
    assert summary["real_fem_certified"] is False


@pytest.mark.parametrize("field", ["root", "runtime", "lock_sha256", "program_sha256"])
def test_bad_launch_binding_stops_before_candidate_import(field, tmp_path):
    # Validate the pre-import check directly under isolated stdlib; no fixture access.
    source = f"""import importlib.util
from pathlib import Path
root=Path({str(ROOT)!r})
spec=importlib.util.spec_from_file_location('bootstrap',root/'scripts/b4_49_certificate_campaign.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
release=module.make_release(root,Path({str(tmp_path)!r}),'REGISTERED_REGRESSION_B4_49')
field={field!r}
if field=='root':release[field]=str(root/'unregistered')
elif field=='runtime':release[field]['executable']='/unregistered/python'
elif field=='lock_sha256':release[field]='0'*64
else:release[field]['src/topolab/combined_certificate.py']='0'*64
module.verify_release(release)
"""
    outcome = subprocess.run([sys.executable, "-I", "-c", source], cwd=ROOT, capture_output=True)
    assert outcome.returncode != 0


@pytest.mark.parametrize("family", ["wrong origin", "failed import"])
def test_bootstrap_failure_retains_started_and_zero_case_prefix(family, tmp_path):
    output = tmp_path / "control"
    output.mkdir()
    request = tmp_path / "request.json"
    source = f"""import importlib.util,sys,json,types
from pathlib import Path
root=Path({str(ROOT)!r});output=Path({str(output)!r});request=Path({str(request)!r})
spec=importlib.util.spec_from_file_location('control',root/'scripts/b4_49_certificate_campaign.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
release=module.make_release(root,output.parent,'REGISTERED_REGRESSION_B4_49')
request.write_text(json.dumps({{'version':module.VERSION,'role':'primary','release':release}}))
module.write(output/'pending.json',{{'registered_control':True,'before_child':True}})
original=module.verify_release
def verified(value):
    result=original(value)
    if {family!r}=='wrong origin':
        find=module.importlib.machinery.PathFinder.find_spec
        def redirected(name,*args):
            if name=='combined_certificate':return types.SimpleNamespace(origin='/wrong-origin')
            return find(name,*args)
        module.importlib.machinery.PathFinder.find_spec=redirected
    else:
        class Block:
            def find_spec(self,fullname,path=None,target=None):
                if fullname=='fractions':raise ImportError('registered actual dependency failure')
                return None
        sys.modules.pop('fractions',None);sys.meta_path.insert(0,Block())
    return result
module.verify_release=verified
raise SystemExit(module.child(request,output))
"""
    result = subprocess.run([sys.executable, "-I", "-c", source], cwd=ROOT, capture_output=True)
    assert result.returncode == 1
    assert (output / "started.json").is_file() and (output / "failure.txt").is_file()
    assert not (output / "cases").exists()
    assert not (output / "import_complete.json").exists()
    assert ((output / "import_before.json").exists()) == (family == "failed import")


def test_missing_completion_and_native_fields_stop_as_unknown(tmp_path):
    audit = independent_module("b4_49_certificate_audit")
    with pytest.raises(ValueError):
        audit.get(tmp_path / "missing-terminal.json")
    with pytest.raises(ValueError, match="UNKNOWN_STOP"):
        audit.profile(b"UNKNOWN_NOT_WRITTEN")


def test_exact_bookkeeping_receipt_precedes_actual_helper_work(panel, monkeypatch):
    import topolab.combined_certificate as candidate

    active, observed = [], []

    def journal(phase, data):
        if phase == "before":
            active.append(data["stage"])
        else:
            assert active.pop() == data["stage"]

    def inspect_helper(name, stage):
        original = getattr(candidate, name)

        def checked(*args):
            assert active[-1] == stage
            observed.append(stage)
            return original(*args)

        monkeypatch.setattr(candidate, name, checked)

    inspect_helper("_intended_operators", "intended-operators")
    inspect_helper("_residual_errors", "assembly-residual-error-bookkeeping")
    fixture = panel["combined-nondyadic-assembly"][0]
    assert candidate.evaluate(fixture, journal)["status"] == "PASS"
    assert observed == ["intended-operators", "assembly-residual-error-bookkeeping"]
    assert not active
