"""Prospective second-attempt software authority; no original or target IO."""

import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
REMEDY = "docs/planning/p17_m2_funded_acquisition_remedy2_protocol.json"
EVIDENCE = "/private/tmp/topolab-funded-continuation-20261026/"


def controller():
    spec = importlib.util.spec_from_file_location(
        "source2_remedy_control_test", REPO / "scripts/p17_m2_source_acquisition_control.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_new_remedy_plan_uses_separate_protocol_and_preserves_native_window():
    control = controller()
    raw = (REPO / REMEDY).read_bytes()
    plan = control.formal_plan(raw, attempt=2)
    assert plan["binding"]["authority_protocol_path"] == REMEDY
    assert plan["binding"]["formal_attempt"] == 2
    assert plan["root"].endswith("/p17-m2-local-input-version-v6-hash-bound-20261026")
    assert plan["execution_identity"] == control.FUNDED_IDENTITY
    assert plan["actor_window_seconds"] == 4500
    assert plan["result_window_projection_seconds"] == {"exporter": 7200, "independent": 7200}


def remedy_fixture(tmp_path, monkeypatch, *, formal=False):
    spec = importlib.util.spec_from_file_location(
        "source2_remedy_funded_fixtures",
        Path(__file__).with_name("test_p17_m2_funded_acquisition_independent.py"),
    )
    assert spec and spec.loader
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    checker, plan, _ = fixtures.fixture(tmp_path, monkeypatch, formal=formal)
    authority = json.loads((REPO / REMEDY).read_bytes())
    authority["readiness_freeze_state"] = "DRAFT_NOT_YET_REVIEWED"
    (checker.REPO / checker.FUNDED_PROTOCOL).write_bytes(
        (REPO / checker.FUNDED_PROTOCOL).read_bytes()
    )
    plan["source_tree"][checker.FUNDED_PROTOCOL] = checker.digest(
        (REPO / checker.FUNDED_PROTOCOL).read_bytes()
    )
    if formal:
        root = authority["fixed_target"]["attempts"]["2"]["generation"]
        plan["binding"]["formal_attempt"] = 2
        plan["backup_root"] = root + "-independent-backup"
    else:
        root = str(tmp_path.resolve() / "topolab-public-funded-acquisition-remedy2-new")
        plan["source_root"] = root + "/public-source"
        plan["backup_root"] = root + "/backup-content"
    plan.update(root=root, content_root=root + "/content")
    plan["binding"]["authority_protocol_path"] = REMEDY
    stop = {
        "schema": "topolab.source-attempt1-zero-role-stop.v1",
        "status": "FROZEN_ZERO_ROLE_CALLER_FIRST_SUFFIX_UNAVAILABLE",
        "classification": "ENGINEERING_ORCHESTRATION_WINDOW_ACCOUNTING",
        "attempt": 1, "authority_sha256": authority["remedy"]["base_authority_sha256"],
        "plan_sha256": "39f4bbd750345e95cbdeaae3c53448efb6c2ac9ba2ae1412b48adf3166d517f3",
        "activation_actual_exit_code": 0, "activation_final_observed_unix_ms": 1793068615323,
        "activation_actual_return_sha256":
            "3a27f5491dc3637c07bc8927772a154512045844b3a08cebd19028899f820452",
        "primary_error": "CALLER_FIRST_ROLE_FULL_SUFFIX_UNAVAILABLE",
        "formal_native_roles_launched": 0, "old_original_stat_reads": 0,
        "metadata_completed": 0, "payload_completed": 0, "source_input_accepted": False,
        "source_FULL_paid_seconds": 0, "source_FULL_unused_closed_seconds": 3600,
        "version_members_accepted": 0, "formal_control_CLI_calls": 1,
        "backup_created": False, "old_generations_backups_leases_modified": False,
        "lease_state": "HELD_NO_MANUAL_RELEASE",
        "native_shared_T_result": "NOT_ESTABLISHED_NO_NATIVE_SHARED_ROLE",
        "B_admitted": False, "C_admitted": False, "seed17_repaired": False,
    }
    budget = {
        "schema": "topolab.finite-source-orchestration-remedy-budget.v12",
        "new_total_author_cap_seconds": 235800, "executor_cap_seconds": 162900,
        "independent_cap_seconds": 72900, "unchanged_action_start_utc": "2026-10-26T16:28:00Z",
        "unchanged_outer_wall_seconds": 129600, "native_formal_seconds_unchanged": 4500,
        "native_result_seconds_each_unchanged": 7200,
        "source_attempt2_proposed_caller_common_seconds": 5400,
        "source_attempt2_proposed_each_author_cap_seconds": 12600,
        "minimum_native_first_role_suffix_seconds_unchanged": 4200,
        "source_formal_attempts_total_max_unchanged": 2,
        "old_original_reads_each_attempt_max_unchanged": 1196,
        "per_author_per_original_unchanged": 1,
        "scientific_FULL_unchanged": [180, 10800, 3600, 180],
        "external_paid_commitments": 0,
    }
    metadata = {}
    for key, record in (("prior_zero_role_stop", stop), ("budget", budget)):
        path = tmp_path / (key + ".json")
        raw = checker.canonical(record)
        path.write_bytes(raw)
        authority["remedy"][key]["sha256"] = checker.digest(raw)
        metadata[Path(authority["remedy"][key]["path"])] = path
    real_read = checker.native._software_bytes

    def public_metadata_only(path):
        path = Path(path)
        assert not str(path).startswith("/Users/keith1117/Library/")
        assert not str(path).startswith("/Users/keith1117/Documents/TopoLab-data")
        if path in metadata:
            return real_read(metadata[path])
        if str(path).startswith(EVIDENCE):
            assert path.is_relative_to(tmp_path), "unregistered external metadata read"
        return real_read(path)

    monkeypatch.setattr(checker.native, "_software_bytes", public_metadata_only)
    return checker, plan, authority, metadata


def seal(checker, plan, authority):
    raw = checker.canonical(authority)
    (checker.REPO / REMEDY).write_bytes(raw)
    digest = checker.digest(raw)
    plan["source_tree"][REMEDY] = digest
    plan["preparation_contract_sha256"] = plan["contract_sha256"] = digest
    plan["binding"]["preparation_protocol_sha256"] = digest
    if plan["formal_authority"]:
        plan["binding"]["execution_protocol_sha256"] = digest


def test_public_remedy_validates_separate_protocol_and_bound_zero_role_stop(tmp_path, monkeypatch):
    checker, plan, authority, _ = remedy_fixture(tmp_path, monkeypatch)
    seal(checker, plan, authority)
    assert checker.validate_binding(plan)["authority_protocol_path"] == REMEDY


def test_real_349_second_caller_prelude_needs_new_budget_and_both_clocks(tmp_path, monkeypatch):
    checker, _, authority, _ = remedy_fixture(tmp_path, monkeypatch)
    control = controller()
    monkeypatch.setattr(control.load("p17_m2_source_acquisition_independent").native,
                        "_software_bytes", checker.native._software_bytes)
    old = json.loads((REPO / control.FUNDED_PROTOCOL).read_bytes())
    # Same observed return as the failed source1 scenario: 349.972 seconds
    # since the original caller BOOT, only199.972 since later native setup T0.
    with pytest.raises(ValueError, match="SOURCE_CALLER_SUFFIX_UNAVAILABLE"):
        control.source_role_windows(old, 1000.0, 1150.0, 1349.972)
    windows = control.source_role_windows(authority, 1000.0, 1150.0, 1349.972)
    assert windows["caller_deadline"] == 6400.0
    assert windows["native_deadline"] == 5650.0
    assert windows["caller_remaining"] == pytest.approx(5050.028)
    assert windows["native_remaining"] == pytest.approx(4300.028)
    with pytest.raises(ValueError, match="SOURCE_CALLER_SUFFIX_UNAVAILABLE"):
        control.source_role_windows(authority, 1000.0, 2499.0, 2500.0)
    with pytest.raises(ValueError, match="SOURCE_NATIVE_SUFFIX_UNAVAILABLE"):
        control.source_role_windows(authority, 1000.0, 1001.0, 1402.0)


def freeze_review(checker, plan, authority, metadata, tmp_path):
    authority["readiness_freeze_state"] = "REVIEWED_FROZEN"
    authority["published_source_sha256"] = {
        k: v for k, v in plan["source_tree"].items() if k != REMEDY
    }
    authority["independent_preflight_sha256"] = "a" * 64
    projection = deepcopy(authority)
    for key in ("readiness_freeze_state", "published_source_sha256",
                "independent_preflight_sha256"):
        projection.pop(key, None)
    projection["remedy"]["review"].pop("sha256", None)
    admission = {
        "status": "PASS_SOURCE2_REMEDY_REVIEW", "execution_identity": checker.FUNDED_IDENTITY,
        "formal_attempt": 2,
        "base_authority_sha256": authority["remedy"]["base_authority_sha256"],
        "prior_zero_role_stop_sha256": authority["remedy"]["prior_zero_role_stop"]["sha256"],
        "budget_sha256": authority["remedy"]["budget"]["sha256"],
        "published_source_sha256": authority["published_source_sha256"],
        "reviewed_remedy_projection_sha256": checker.digest(checker.canonical(projection)),
    }
    raw = checker.canonical({"status": "PASS_SOURCE2_REMEDY_REVIEW",
                             "author": authority["actors"]["independent"], "admission": admission})
    path = tmp_path / "review.json"
    path.write_bytes(raw)
    authority["remedy"]["review"]["sha256"] = checker.digest(raw)
    metadata[Path(authority["remedy"]["review"]["path"])] = path
    seal(checker, plan, authority)


def test_independent_formal_remedy_requires_actual_distinct_review_and_frozen_map(
    tmp_path, monkeypatch
):
    checker, plan, authority, metadata = remedy_fixture(tmp_path, monkeypatch, formal=True)
    freeze_review(checker, plan, authority, metadata, tmp_path)
    assert checker.validate_binding(plan)["formal_attempt"] == 2
    assert checker.result_window_seconds(plan) == (7200, 7200)
    authority["readiness_freeze_state"] = "DRAFT_NOT_YET_REVIEWED"
    seal(checker, plan, authority)
    with pytest.raises(ValueError, match="freeze/preflight"):
        checker.validate_binding(plan)


@pytest.mark.parametrize("key,value", [
    ("classification", "SCIENTIFIC_FAIL"), ("formal_native_roles_launched", 1),
    ("old_original_stat_reads", 1), ("plan_sha256", "b" * 64),
    ("activation_final_observed_unix_ms", 1793068615324),
    ("source_input_accepted", True), ("lease_state", "RELEASED"),
    ("primary_error", "SCIENTIFIC_FAIL"), ("source_FULL_unused_closed_seconds", 0),
])
def test_resealed_prior_stop_cannot_be_scientific_or_nonzero_role(
    tmp_path, monkeypatch, key, value
):
    checker, plan, authority, metadata = remedy_fixture(tmp_path, monkeypatch)
    path = metadata[Path(authority["remedy"]["prior_zero_role_stop"]["path"])]
    stop = json.loads(path.read_bytes())
    stop[key] = value
    raw = checker.canonical(stop)
    path.write_bytes(raw)
    authority["remedy"]["prior_zero_role_stop"]["sha256"] = checker.digest(raw)
    seal(checker, plan, authority)
    with pytest.raises(ValueError, match="engineering zero-role STOP"):
        checker.validate_binding(plan)


@pytest.mark.parametrize("key,value", [
    ("new_total_author_cap_seconds", 235801),
    ("native_formal_seconds_unchanged", 5400),
    ("source_formal_attempts_total_max_unchanged", 3),
    ("per_author_per_original_unchanged", 2),
    ("unchanged_action_start_utc", "2026-10-27T02:39:00Z"),
])
def test_resealed_budget_cannot_reset_start_or_expand_native_or_reads(
    tmp_path, monkeypatch, key, value
):
    checker, plan, authority, metadata = remedy_fixture(tmp_path, monkeypatch)
    path = metadata[Path(authority["remedy"]["budget"]["path"])]
    budget = json.loads(path.read_bytes())
    budget[key] = value
    raw = checker.canonical(budget)
    path.write_bytes(raw)
    authority["remedy"]["budget"]["sha256"] = checker.digest(raw)
    seal(checker, plan, authority)
    with pytest.raises(ValueError, match="finite budget"):
        checker.validate_binding(plan)


@pytest.mark.parametrize("reference", ["prior_zero_role_stop", "budget", "review"])
def test_formal_remedy_rejects_missing_or_wrong_proof_hash(tmp_path, monkeypatch, reference):
    checker, plan, authority, metadata = remedy_fixture(tmp_path, monkeypatch, formal=True)
    freeze_review(checker, plan, authority, metadata, tmp_path)
    authority["remedy"][reference]["sha256"] = "c" * 64
    seal(checker, plan, authority)
    with pytest.raises(ValueError, match="metadata SHA256"):
        checker.validate_binding(plan)


@pytest.mark.parametrize("reference", ["prior_zero_role_stop", "budget", "review"])
def test_formal_remedy_rejects_unregistered_metadata_path_before_read(
    tmp_path, monkeypatch, reference
):
    checker, plan, authority, metadata = remedy_fixture(tmp_path, monkeypatch, formal=True)
    freeze_review(checker, plan, authority, metadata, tmp_path)
    authority["remedy"][reference]["path"] = "/private/tmp/unregistered-remedy-evidence.json"
    seal(checker, plan, authority)
    with pytest.raises(ValueError, match="metadata reference"):
        checker.validate_binding(plan)


def test_review_cannot_be_reused_for_changed_contract_or_source_map(tmp_path, monkeypatch):
    checker, plan, authority, metadata = remedy_fixture(tmp_path, monkeypatch, formal=True)
    freeze_review(checker, plan, authority, metadata, tmp_path)
    authority["owner_approval_reference"] += " changed"
    seal(checker, plan, authority)
    with pytest.raises(ValueError, match="review/source projection"):
        checker.validate_binding(plan)


@pytest.mark.parametrize("root", [
    "/Users/keith1117/Library/Application Support/TopoLab-custody/"
    "p17-m2-local-input-version-v5-hash-bound-20261026",
    "/Users/keith1117/Library/Application Support/TopoLab-custody/"
    "p17-m2-local-input-version-v7-hash-bound-20261026",
])
def test_new_remedy_plan_cannot_target_first_or_third_generation(tmp_path, monkeypatch, root):
    checker, plan, authority, metadata = remedy_fixture(tmp_path, monkeypatch, formal=True)
    freeze_review(checker, plan, authority, metadata, tmp_path)
    plan["root"] = root
    plan["content_root"] = root + "/content"
    plan["backup_root"] = root + "-independent-backup"
    with pytest.raises(ValueError, match="generation literal"):
        checker.validate_binding(plan)


def test_exact_authority_selection_keeps_first_old_and_routes_only_second(monkeypatch):
    control = controller()
    old = control.FUNDED_AUTHORITY_RAW
    new = control.REMEDY_AUTHORITY_RAW
    authority = json.loads(old)
    first = authority["fixed_target"]["attempts"]["1"]["generation"]
    second = authority["fixed_target"]["attempts"]["2"]["generation"]
    assert control.authority_for_root(first) == (old, 1)
    assert control.authority_for_root(second) == (new, 2)
    monkeypatch.setattr(control, "REMEDY_AUTHORITY_RAW", None)
    assert control.authority_for_root(second) == (old, 2)
    with pytest.raises(ValueError, match="NEW_FROZEN_REMEDY_REQUIRED"):
        control.activate_formal(second)


def test_new_public_prefix_constructs_new_protocol_without_formal_access(tmp_path):
    control = controller()
    old = control.formal_plan(control.FUNDED_AUTHORITY_RAW)
    root = tmp_path.resolve() / "topolab-public-funded-acquisition-remedy2-explicit"
    plan = control.make_plan(root, old["content_contract"], old["source_identity"])
    assert plan["binding"]["authority_protocol_path"] == REMEDY
    assert plan["formal_authority"] is False
    assert plan["source_root"] == str(root / "public-source")
    assert not root.exists()


def test_unreviewed_new_remedy_stops_before_formal_directory_io(monkeypatch):
    control = controller()
    authority = json.loads((REPO / REMEDY).read_bytes())
    authority["readiness_freeze_state"] = "DRAFT_NOT_YET_REVIEWED"
    monkeypatch.setattr(control, "REMEDY_AUTHORITY_RAW", control.base().canonical(authority))

    def forbidden(*args, **kwargs):
        pytest.fail("DRAFT remedy reached a formal directory syscall")

    with monkeypatch.context() as guard:
        guard.setattr(control.os, "open", forbidden)
        with pytest.raises(ValueError, match="FUNDED_READINESS_NOT_FROZEN"):
            control.activate_formal(authority["fixed_target"]["attempts"]["2"]["generation"])


def test_review_does_not_allow_source_map_replacement(tmp_path, monkeypatch):
    checker, plan, authority, metadata = remedy_fixture(tmp_path, monkeypatch, formal=True)
    freeze_review(checker, plan, authority, metadata, tmp_path)
    plan["source_tree"]["scripts/public-only-changed.py"] = "e" * 64
    authority["published_source_sha256"] = {
        key: value for key, value in plan["source_tree"].items() if key != REMEDY
    }
    seal(checker, plan, authority)
    with pytest.raises(ValueError, match="review/source projection"):
        checker.validate_binding(plan)


def test_review_from_executor_cannot_replace_distinct_author(tmp_path, monkeypatch):
    checker, plan, authority, metadata = remedy_fixture(tmp_path, monkeypatch, formal=True)
    freeze_review(checker, plan, authority, metadata, tmp_path)
    path = metadata[Path(authority["remedy"]["review"]["path"])]
    review = json.loads(path.read_bytes())
    review["author"] = authority["actors"]["executor"]
    raw = checker.canonical(review)
    path.write_bytes(raw)
    authority["remedy"]["review"]["sha256"] = checker.digest(raw)
    seal(checker, plan, authority)
    with pytest.raises(ValueError, match="distinct review"):
        checker.validate_binding(plan)


def test_new_formal_preflight_cannot_replay_old_protocol_with_same_identity(tmp_path, monkeypatch):
    checker, plan, authority, metadata = remedy_fixture(tmp_path, monkeypatch, formal=True)
    freeze_review(checker, plan, authority, metadata, tmp_path)
    plan["runtime"] = {"python": "/public/locked-python", "cwd": str(checker.REPO),
                       "isolated": 1, "threads": {"OMP_NUM_THREADS": "1"}}
    preflight = {
        "status": "PASS_PUBLIC_METADATA_LAUNCH_PREFLIGHT",
        "execution_identity": checker.FUNDED_IDENTITY, "actors": authority["actors"],
        "published_source_sha256": authority["published_source_sha256"],
        "runtime": {k: v for k, v in plan["runtime"].items() if k != "orig_argv"},
        "expected_white_list_contract": {
            "raw_sha256": checker.CONTENT_CONTRACT_SHA256, "r0_metadata": 40,
            "r1_payload": 558, "version_members": 1071,
            "total_old_source_reads_per_attempt_max": 1196, "per_author_per_file_reads": 1,
        },
        "authority_protocol_path": REMEDY, "remedy_formal_attempt": 2,
        "remedy_projection_sha256": checker.remedy_projection_sha256(authority),
    }
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    seal(checker, plan, authority)
    assert checker.check_funded_preflight(plan, raw)["remedy_formal_attempt"] == 2
    preflight["authority_protocol_path"] = checker.FUNDED_PROTOCOL
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    seal(checker, plan, authority)
    with pytest.raises(ValueError, match="remedy preflight"):
        checker.check_funded_preflight(plan, raw)


@pytest.mark.parametrize("clock", [False, float("nan"), float("inf"), -1])
def test_supplied_clock_cannot_be_missing_nonfinite_or_boolean(tmp_path, monkeypatch, clock):
    control = controller()
    authority = json.loads(control.FUNDED_AUTHORITY_RAW)
    with pytest.raises(ValueError, match="ACTUAL_CLOCKS_REQUIRED"):
        control.source_role_windows(authority, clock, 1150.0, 1349.972)
