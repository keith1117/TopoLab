"""Registered B4.47 public panel, independent proofs and actual import controls."""

import ast
import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from topolab import public_campaign_arithmetic as candidate

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "docs/planning/b4_47_public_arithmetic_campaign_contract.json").read_text()
)


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


oracle = module("b4_47_arithmetic_oracle")
launcher = module("b4_47_campaign")
auditor = module("b4_47_campaign_audit")


def fixture(entry):
    return json.loads((ROOT / entry["path"]).read_text())


def binding(entry):
    return {
        "version": CONTRACT["version"],
        "role": "fresh-public-arithmetic-software",
        "fixture_id": entry["id"],
        "sha256": entry["sha256"],
        "source_main": CONTRACT["starting_main"],
        "free_space": "b4-47-public-space:" + entry["id"],
        "path": entry["path"],
    }


@pytest.mark.parametrize("entry", CONTRACT["catalog"], ids=lambda row: row["id"])
def test_complete_registered_case_and_every_independent_operation(entry, tmp_path):
    raw = (ROOT / entry["path"]).read_bytes()
    value = candidate.read_public_fixture(binding(entry), lambda: raw)
    journal = launcher.Journal(tmp_path / "candidate")
    result = candidate.enclose_assembled_residual(value, journal.emit)
    assert result["status"] == entry["expected_status"]
    independent = auditor.ProofJournal(tmp_path / "independent")
    proof = oracle.audit_case(fixture(entry), result, independent.operation)
    assert proof["passed"], proof
    assert journal.counts()["pending"] == independent.counts()["pending"] == 0
    assert proof["RN_even_proofs"] == len(result["trace"])
    checks = auditor.Checks()
    auditor.journal_proof(
        tmp_path / "candidate", result["operations"], journal.counts(), checks.require, entry["id"]
    )
    assert all(checks.rows.values())


@pytest.mark.parametrize("key", CONTRACT["software_tests"]["binding_denials"])
def test_registered_binding_denies_before_callback_bytes(key):
    entry = CONTRACT["catalog"][0]
    request = binding(entry)
    changes = {
        "role": "final",
        "version": "changed",
        "id": "unlisted",
        "hash": "0" * 64,
        "source": "0" * 40,
        "space": "real-fem",
    }
    keys = {"id": "fixture_id", "hash": "sha256", "source": "source_main", "space": "free_space"}
    if key == "unknown":
        request["unknown"] = "x"
    elif key == "missing":
        request.pop("path")
    else:
        request[keys.get(key, key)] = changes[key]

    def forbidden():
        raise AssertionError("protected input callback reached")

    with pytest.raises(candidate.RepresentationScopeError, match="DENY_BEFORE_BYTES"):
        candidate.read_public_fixture(request, forbidden)


@pytest.mark.parametrize("denial", CONTRACT["software_tests"]["json_schema_denials"])
def test_closed_schema_prearithmetic_rejections(denial):
    if denial == "duplicate":
        with pytest.raises(ValueError, match="duplicate"):
            launcher.strict(b'{"version":1,"version":2}')
        return
    if denial == "NaN":
        with pytest.raises(ValueError, match="nonfinite"):
            launcher.strict(b'{"x":NaN}')
        return
    value = fixture(CONTRACT["catalog"][0])
    if denial == "unknown":
        value["unknown"] = 0
    elif denial == "missing":
        value.pop("u_bits")
    elif denial == "bool integer":
        value["nodes"][0]["value"] = True
    elif denial == "forward reference":
        value["nodes"][0] = {"op": "add", "args": [0, 0]}
    elif denial == "nonfinite bits":
        value["nodes"][4]["value"] = "7ff0000000000000"
    elif denial == "subnormal bits":
        value["nodes"][4]["value"] = "0000000000000001"
    elif denial == "ragged matrix":
        value["K_terms"][0][0].append(0)
    with pytest.raises(candidate.RepresentationScopeError):
        candidate.validate_public_fixture(value)


@pytest.mark.parametrize("family", CONTRACT["software_tests"]["tamper_families"])
def test_complete_error_trace_and_receipt_tampering_rejects(family, tmp_path):
    entry = CONTRACT["catalog"][3]
    value = fixture(entry)
    result = candidate.enclose_assembled_residual(candidate.validate_public_fixture(value))
    changed = copy.deepcopy(result)
    if family == "trace result":
        changed["trace"][0]["result_hex"] = "0x1.0000000000000p+2"
    elif family == "trace interval":
        changed["trace"][0]["intended_upper"] = "4"
    elif family == "trace order":
        changed["trace"][0], changed["trace"][1] = changed["trace"][1], changed["trace"][0]
    elif family == "missing prefix":
        changed["trace"].pop()
    elif family == "arrays":
        changed["arrays"]["G"][0][0] = "0x1.0000000000000p+2"
    elif family == "square":
        changed["square_uppers"]["beta_K"] = "0"
    elif family == "bound":
        changed["bounds"]["r_plus"] = "0x0.0p+0"
    elif family == "intended residual":
        changed["arrays"]["intended_residual_intervals"] = [["0", "0"]]
    elif family == "diagnostic flags":
        changed["real_fem_certified"] = True
    elif family == "stage journal":
        changed["operations"].pop(0)
    else:
        journal = launcher.Journal(tmp_path / "operations")
        original = candidate.enclose_assembled_residual(
            candidate.validate_public_fixture(value), journal.emit
        )
        path = tmp_path / "operations/000000.json"
        event = json.loads(path.read_text())
        event["previous_sha256"] = "0" * 64
        path.write_text(json.dumps(event))
        with pytest.raises(ValueError, match="immutable_prefix"):
            auditor.journal_proof(
                tmp_path / "operations",
                original["operations"],
                journal.counts(),
                auditor.Checks().require,
                "tamper",
            )
        return
    assert not oracle.audit_case(value, changed)["passed"]


def test_rounded_zero_does_not_erase_actual_or_intended_residual_error():
    entry = CONTRACT["catalog"][4]
    result = candidate.enclose_assembled_residual(candidate.validate_public_fixture(fixture(entry)))
    assert float.fromhex(result["arrays"]["r_hat"][0]) == 0
    assert Fraction(result["arrays"]["r_arrays"][0]) == Fraction(1, 2**104)
    assert Fraction(result["square_uppers"]["beta_eval"]) == Fraction(1, 2**208)
    assert Fraction(result["arrays"]["intended_residual_intervals"][0][0]) == Fraction(1, 2**104)
    assert float.fromhex(result["bounds"]["r_plus"]) > 0


def test_both_actual_triangles_stay_distinct_from_symmetric_intended_target():
    entry = CONTRACT["catalog"][2]
    result = candidate.enclose_assembled_residual(candidate.validate_public_fixture(fixture(entry)))
    assert result["arrays"]["G"][0][1] != result["arrays"]["G"][1][0]
    assert Fraction(result["square_uppers"]["symmetry_G"]) == Fraction(9, 32)
    assert Fraction(result["square_uppers"]["symmetry_K"]) == Fraction(9, 32)


def test_before_hook_interruption_retains_prefix_without_executing_next_scalar():
    entry = CONTRACT["catalog"][0]
    events = []

    def stop(phase, row):
        events.append(row)
        if phase == "before" and row["stage"] == "node:1":
            raise RuntimeError("registered before-operation interruption")

    with pytest.raises(RuntimeError):
        candidate.enclose_assembled_residual(
            candidate.validate_public_fixture(fixture(entry)), stop
        )
    assert [(r["phase"], r["stage"]) for r in events] == [
        ("before", "node:0"),
        ("after", "node:0"),
        ("before", "node:1"),
    ]


@pytest.fixture(scope="module")
def runtime():
    # Observe the ordinary test subprocess runtime; this never claims formal source/CI readiness.
    code = """import sys,json,importlib,hashlib
from pathlib import Path
names=['math','fractions','struct','dataclasses','re','json','hashlib','types']
rows={}
image_hash=hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()
for name in names:
 m=importlib.import_module(name);p=m.__spec__.origin
 digest=(image_hash if p in ('built-in','frozen')
         else hashlib.sha256(Path(p).read_bytes()).hexdigest())
 rows[name]={'origin':p,'sha256':digest}
print(json.dumps({'version':'.'.join(map(str,sys.version_info[:3])),'sys_path':sys.path,'stdlib':rows}))
"""
    return json.loads(subprocess.check_output([sys.executable, "-I", "-c", code], text=True))


def regression_release(tmp_path, runtime):
    def sha(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    return {
        "version": CONTRACT["version"],
        "execution_kind": "REGISTERED_REGRESSION_B4_47",
        "source_root": str(ROOT),
        "executable": sys.executable,
        "executable_sha256": sha(Path(sys.executable).resolve()),
        "python_version": runtime["version"],
        "isolated_sys_path": runtime["sys_path"],
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "tree": subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True
        ).strip(),
        "lock_sha256": sha(ROOT / "uv.lock"),
        "pyproject_sha256": sha(ROOT / "pyproject.toml"),
        "contract_sha256": sha(ROOT / launcher.CONTRACT),
        "protocol_sha256": sha(ROOT / launcher.PROTOCOL),
        "program_sha256": {n: sha(ROOT / n) for n in launcher.PROGRAMS},
        "stdlib_sha256": runtime["stdlib"],
        "source_manifest_sha256": "0" * 64,
        "external_root": str(tmp_path),
        "ci": [],
    }


@pytest.mark.parametrize("entry", CONTRACT["launch_controls"], ids=lambda row: row["id"])
def test_actual_candidate_import_and_registered_negative_launch_controls(entry, tmp_path, runtime):
    release = regression_release(tmp_path, runtime)
    request = tmp_path / "request.json"
    output = tmp_path / "case"
    if entry["id"] == "existing_output":
        output.mkdir()
        original = output / "original.json"
        original.write_bytes(b'{"retained":true}\n')
        with pytest.raises(FileExistsError):
            launcher.run_one(tmp_path / "NONEXISTENT_MUST_NOT_BE_READ", output, native=False)
        assert original.read_bytes() == b'{"retained":true}\n'
        assert len(list(output.iterdir())) == 1
        return
    launcher.save(request, launcher.make_request(release, entry["id"]))
    terminal = launcher.run_one(request, output, native=False)
    assert terminal["status"] == entry["expected_status"], terminal
    checks = auditor.Checks()
    auditor.receipt_proof(
        output, release, entry["expected_status"], checks.require, entry["id"], native=False
    )
    assert all(checks.rows.values())
    assert not (output / "cases").exists()


def test_formal_entry_requires_clean_released_ci_and_oracle_imports_are_separate(tmp_path, runtime):
    binary = tmp_path / "declared-interpreter-bytes"
    raw = b"registered-runtime-byte" * 500000
    binary.write_bytes(raw)
    expected = hashlib.sha256(raw).hexdigest()
    assert launcher.executable_hash(binary) == auditor.interpreter_digest(binary) == expected
    with pytest.raises(ValueError, match="bounded file"):
        launcher.read(binary)  # Text/metadata ceiling remains unchanged.
    release = regression_release(tmp_path, runtime)
    release["execution_kind"] = "FORMAL_B4_47"
    with pytest.raises(ValueError, match="CI"):
        launcher.release_schema(release)
    for name in ("b4_47_arithmetic_oracle", "b4_47_campaign_audit"):
        tree = ast.parse((ROOT / "scripts" / (name + ".py")).read_text())
        imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [
            alias.name for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names
        ]
        assert all(n.split(".")[0] in sys.stdlib_module_names for n in imports)
        assert not any(n.split(".")[0] in auditor.FORBIDDEN for n in imports)


def test_complete_registered_child_and_independent_receipt_pipeline(tmp_path, runtime):
    """Exercise the same finite panel across isolated actual imports before formal release."""
    release = regression_release(tmp_path, runtime)
    release_path = tmp_path / "release.json"
    launcher.save(release_path, release)
    controls = tmp_path / "formal-controls"
    controls.mkdir()
    cases = []
    for entry in CONTRACT["launch_controls"]:
        mode = entry["id"]
        if mode == "existing_output":
            existing = controls / "actual_candidate_import"
            originals = {
                str(p.relative_to(existing)): launcher.sha(p.read_bytes())
                for p in existing.iterdir()
                if p.is_file()
            }
            with pytest.raises(FileExistsError):
                launcher.run_one(controls / "NONEXISTENT_MUST_NOT_BE_READ", existing, native=False)
            launcher.save(
                controls / "existing_output_refusal.json",
                {
                    "status": "REFUSED_EXISTING_OUTPUT",
                    "unchanged": True,
                    "original_sha256": originals,
                    "after_sha256": originals,
                    "request_reads": 0,
                    "new_child_launches": 0,
                },
            )
            status = "REFUSED_EXISTING_OUTPUT"
        else:
            request = controls / "requests" / (mode + ".json")
            launcher.save(request, launcher.make_request(release, mode))
            status = launcher.run_one(request, controls / mode, native=False)["status"]
        assert status == entry["expected_status"]
        cases.append({"id": mode, "status": status})
    launcher.save(controls / "result.json", {"passed": True, "formal_retry": False, "cases": cases})
    producer = tmp_path / "formal-producer"
    producer.mkdir()
    request = producer / "request.json"
    launcher.save(request, launcher.make_request(release, "producer"))
    terminal = launcher.run_one(request, producer / "producer", native=False)
    assert terminal["status"] == "PASS_PUBLIC_ARITHMETIC_CASES", terminal
    output = tmp_path / "formal-independent"
    code = """import importlib.util,sys
from pathlib import Path
spec=importlib.util.spec_from_file_location('b4_47_campaign_audit',sys.argv[1])
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
sys.exit(audit.audit_evidence(*map(Path,sys.argv[2:]),native=False))
"""
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-c",
            code,
            str(ROOT / "scripts/b4_47_campaign_audit.py"),
            str(release_path),
            str(controls),
            str(producer),
            str(output),
        ],
        cwd=ROOT,
        check=False,
    )
    if result.returncode:
        pytest.fail((output / "failure.txt").read_text())
    proof = json.loads((output / "result.json").read_text())
    assert proof["passed"] and proof["cases_completed"] == 10 and proof["cases_pending"] == 0
    assert len(proof["predicates"]) <= CONTRACT["caps"]["independent_max_predicates"]
    assert sum(r["RN_even_proofs"] for r in proof["cases"]) > 0
