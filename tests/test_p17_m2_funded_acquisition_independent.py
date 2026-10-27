"""Independent NEW funded authority acceptance; no old input or target path IO."""

import importlib.util
import json
import shutil
import tempfile
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]
IDENTITY = "topolab.v2.p17-m2-hash-bound-source-acquisition.v2"
PROTOCOL = "docs/planning/p17_m2_funded_acquisition_protocol.json"
POLICY = "topolab.source-identity.prebound-sha256.v1"
PARENT = "/Users/keith1117/Library/Application Support/TopoLab-custody"
FULL = {
    "independent-public-check": 300, "exporter-r0": 300, "independent-r0": 300,
    "exporter-r1": 1200, "independent-r1": 1200, "shared-closeout": 300,
}


@contextmanager
def copied_public_source_plan(checker, plan):
    """Only NEW public metadata is created; no original or custody target IO."""
    with tempfile.TemporaryDirectory(
        prefix="topolab-public-funded-acquisition-independent-origin-",
        dir=Path(tempfile.gettempdir()).resolve(),
    ) as directory:
        root = Path(directory)
        origin = deepcopy(plan)
        origin.update(root=str(root), source_root=str(root / "public-source"),
                      content_root=str(root / "content"), backup_root=str(root / "backup-content"))
        path = root / "plan.json"
        raw = checker.canonical(origin)
        path.write_bytes(raw)
        plan["binding"].update(public_source_plan=str(path),
                               public_source_plan_sha256=checker.digest(raw))
        yield path, origin


def test_funded_public_copy_plan_has_exact_real_prepare_CLI_suffix(tmp_path, monkeypatch):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    with copied_public_source_plan(checker, plan) as (path, _):
        binding = checker.validate_binding(plan)
        assert checker.public_prepare_suffix(plan) == (
            "--public-source-plan", str(path), "--public-source-plan-sha",
            binding["public_source_plan_sha256"],
        )


def test_public_copy_plan_uses_platform_temporary_directory(tmp_path, monkeypatch):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(tempfile, "tempdir", "/tmp")
    with copied_public_source_plan(checker, plan) as (path, _):
        assert path.parent.parent == Path("/tmp").resolve()
        assert checker.validate_binding(plan)["public_source_plan"] == str(path)


def test_prebound_public_graph_keeps_its_historical_authority_freeze(tmp_path, monkeypatch):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    with copied_public_source_plan(checker, plan) as (path, origin):
        historical = "d" * 64
        assert historical != plan["source_tree"][PROTOCOL]
        origin["source_tree"][PROTOCOL] = historical
        origin["binding"]["preparation_protocol_sha256"] = historical
        origin["contract_sha256"] = historical
        origin["preparation_contract_sha256"] = historical
        raw = checker.canonical(origin)
        path.write_bytes(raw)
        plan["binding"]["public_source_plan_sha256"] = checker.digest(raw)

        # Public data provenance is bound to these exact historical plan bytes.
        # The current plan still receives its complete current-authority check.
        assert checker.validate_binding(plan)["preparation_protocol_sha256"] != historical
        assert checker.public_prepare_suffix(plan)[-1] == checker.digest(raw)


@pytest.mark.parametrize("scope", ["formal", "old-hash", "old-strict"])
def test_public_copy_fields_do_not_grant_formal_or_old_identity_entry(
    tmp_path, monkeypatch, scope
):
    checker, plan, _ = fixture(tmp_path, monkeypatch, formal=scope == "formal")
    plan["binding"].update(public_source_plan="/private/tmp/topolab-public-funded-acquisition-x/plan.json",
                           public_source_plan_sha256="a" * 64)
    if scope == "old-hash":
        plan["execution_identity"] = checker.HASH_BOUND_IDENTITY
    elif scope == "old-strict":
        plan["execution_identity"] = checker.IDENTITY
    monkeypatch.setattr(checker.native, "_software_bytes",
                        lambda _: pytest.fail("copy permission must reject before metadata IO"))
    with pytest.raises(ValueError, match="public source plan"):
        checker.validate_binding(plan)


@pytest.mark.parametrize("wrong", [
    "/Users/keith1117/Documents/TopoLab-data/plan.json",
    "/Users/keith1117/Library/Application Support/TopoLab-custody/x/plan.json",
    "/private/tmp/topolab-public-funded-acquisition-a/../plan.json",
    "/private/tmp/topolab-public-funded-acquisition-a/not-plan.json",
    "/private/tmp/topolab-public-funded-acquisition-a/nested/plan.json",
])
def test_copy_plan_path_whitelist_rejects_before_any_metadata_open(tmp_path, monkeypatch, wrong):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    plan["binding"].update(public_source_plan=wrong, public_source_plan_sha256="a" * 64)
    monkeypatch.setattr(checker.native, "_software_bytes",
                        lambda _: pytest.fail("literal path must reject before metadata IO"))
    with pytest.raises(ValueError, match="public source plan"):
        checker.validate_binding(plan)


@pytest.mark.parametrize("change", ["sha", "formal", "identity", "source-root", "content"])
def test_copy_plan_requires_exact_new_public_provenance(tmp_path, monkeypatch, change):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    with copied_public_source_plan(checker, plan) as (path, origin):
        if change == "sha":
            plan["binding"]["public_source_plan_sha256"] = "b" * 64
        else:
            if change == "formal":
                origin["formal_authority"] = True
            elif change == "identity":
                origin["execution_identity"] = checker.HASH_BOUND_IDENTITY
            elif change == "source-root":
                origin["source_root"] = "/Users/keith1117/Documents/TopoLab-data"
            else:
                original = origin["content_contract"]["R0"]["literal_bootstrap_files"][0]
                original["expected_sha256"] = "c" * 64
                origin["binding"]["content_contract_sha256"] = checker.digest(
                    checker.canonical(origin["content_contract"]))
            raw = checker.canonical(origin)
            path.write_bytes(raw)
            plan["binding"]["public_source_plan_sha256"] = checker.digest(raw)
        with pytest.raises(ValueError, match="public source plan"):
            checker.validate_binding(plan)


def test_copy_plan_symlink_is_rejected(tmp_path, monkeypatch):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    with copied_public_source_plan(checker, plan) as (path, _):
        raw = path.read_bytes()
        path.unlink()
        alternate = path.with_name("actual-plan.json")
        alternate.write_bytes(raw)
        path.symlink_to(alternate.name)
        with pytest.raises((ValueError, OSError)):
            checker.validate_binding(plan)


@pytest.mark.parametrize("root", [
    "/private/tmp/topolab-public-funded-acquisition-origin",
    "/tmp/topolab-public-funded-acquisition-origin",
    "/private/var/folders/test/T/topolab-public-funded-acquisition-origin",
])
def test_copy_plan_uses_existing_cross_platform_public_root_boundary(tmp_path, monkeypatch, root):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    origin = deepcopy(plan)
    origin.update(root=root, source_root=root + "/public-source",
                  content_root=root + "/content", backup_root=root + "/backup-content")
    path = Path(root) / "plan.json"
    raw = checker.canonical(origin)
    plan["binding"].update(public_source_plan=str(path),
                           public_source_plan_sha256=checker.digest(raw))
    software_bytes = checker.native._software_bytes

    def explicit_new_public_metadata(candidate):
        return raw if Path(candidate) == path else software_bytes(candidate)

    monkeypatch.setattr(checker.native, "_software_bytes", explicit_new_public_metadata)
    assert checker.validate_binding(plan)["public_source_plan"] == str(path)


def fixture(tmp_path, monkeypatch, *, formal=False, attempt=1):
    spec = importlib.util.spec_from_file_location(
        "funded_independent_fixture", Path(__file__).with_name(
            "test_p17_m2_source_acquisition_independent.py"))
    assert spec and spec.loader
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    checker, plan = fixtures.binding_plan()
    frozen = tmp_path / "git-software"
    for name in (checker.CONTENT_CONTRACT, checker.PROPOSAL, checker.PREPARATION_PROTOCOL):
        (frozen / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / name, frozen / name)
    authority = {
        "schema": "topolab.v2.m2-funded-acquisition-authority.v1",
        "execution_identity": IDENTITY,
        "source_identity_policy": POLICY,
        "owner_approval_reference": "Direct owner retry-unstarted and expand authorization",
        "permissions": {"formal_activation": True, "old_original_access": True,
                        "target_access": True, "B_C": False},
        "formal_seconds": 4500,
        "result_seconds": {"exporter": 7200, "independent": 7200},
        "outer_wall_seconds": 129600,
        "total_new_author_charged_seconds_cap": 194400,
        "actors": {"executor": "/root", "independent": "/root/acquisition_funded_audit"},
        "formal_admission": "CONDITIONAL_ON_FROZEN_READINESS",
        "readiness_freeze_state": "REVIEWED_FROZEN",
        "role_order": list(FULL), "FULL_by_role": deepcopy(FULL),
        "source_whitelist": {
            "original_contract": checker.CONTENT_CONTRACT,
            "raw_sha256": checker.CONTENT_CONTRACT_SHA256,
            "per_author_per_file_reads": 1, "r0_metadata": 40, "r1_payload": 558,
            "version_members": 1071, "total_old_source_reads_per_attempt_max": 1196,
            "metadata_acceptance_before_payload_stat_open": True,
        },
        "fixed_target": {"parent": PARENT, "attempts": {
            str(index): {"generation": PARENT + f"/p17-m2-local-input-version-v{index+4}"
                        "-hash-bound-20261026",
                        "backup": PARENT + f"/p17-m2-local-input-version-v{index+4}"
                        "-hash-bound-20261026-independent-backup"}
            for index in (1, 2)}},
        "implementation_base_commit": "2f67feee4d89c94b36196122a5930a56d5b8433f",
        "published_source_sha256": deepcopy(plan["source_tree"]),
        "preparation_closure_sha256":
            "0636d0713cfa15840516b8aff20d904ec09be7577cfdfdafcb416c375a97e314",
        "preparation_closure_paths": [
            "/Users/keith1117/Documents/TopoLab-data/"
            "p17-m2-hash-bound-custody-20261026-results/publication-closure.json",
            "/private/tmp/topolab-hash-bound-custody-20261026-results-backup/"
            "publication-closure.json",
        ],
        "independent_preflight_path":
            "/private/tmp/topolab-funded-continuation-20261026/independent/preflight-remedy3.json",
        "independent_preflight_sha256": "a" * 64,
    }
    root = str(tmp_path.resolve() / "topolab-public-funded-acquisition-independent")
    plan.update(execution_identity=IDENTITY, source_identity_policy=POLICY, root=root,
                source_root=root+"/public-source", content_root=root+"/content",
                backup_root=root+"/backup-content")
    plan["binding"].update(source_identity_policy=POLICY, authority_protocol_path=PROTOCOL)
    if formal:
        generation = authority["fixed_target"]["attempts"][str(attempt)]["generation"]
        plan.update(scope=checker.FORMAL_SCOPE, formal_authority=True, root=generation,
                    source_root="/Users/keith1117/Documents/TopoLab-data",
                    content_root=generation+"/content",
                    backup_root=generation+"-independent-backup",
                    content_contract=json.loads((frozen/checker.CONTENT_CONTRACT).read_bytes()),
                    source_identity={"B3_DATA_HASH": checker.native.base.B3_DATA_HASH,
                                     "CATALOG_HASH": checker.native.base.CATALOG_HASH})
        del plan["public_source_identity"]
        plan["binding"].update(formal_authority=True, old_original_access=True,
                               target_access=True, formal_attempt=attempt)
        plan["binding"]["content_contract_sha256"] = checker.digest(
            checker.canonical(plan["content_contract"]))
    monkeypatch.setattr(checker, "REPO", frozen)
    reseal(checker, plan, authority)
    return checker, plan, authority


def reseal(checker, plan, authority):
    raw = checker.canonical(authority)
    (checker.REPO / PROTOCOL).write_bytes(raw)
    sha = checker.digest(raw)
    plan["source_tree"][PROTOCOL] = sha
    plan["preparation_contract_sha256"] = sha
    plan["contract_sha256"] = sha
    plan["binding"]["preparation_protocol_sha256"] = sha
    if plan["formal_authority"]:
        plan["binding"]["execution_protocol_sha256"] = sha


def test_new_funded_public_authority_is_accepted_without_formal_grant(tmp_path, monkeypatch):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    binding = checker.validate_binding(plan)
    assert binding["formal_authority"] is False
    assert binding["target_access"] is False
    assert binding["authority_protocol_path"] == PROTOCOL


def test_funded_formal_metadata_and_complete_result_window_before_target_io(
    tmp_path, monkeypatch
):
    checker, plan, _ = fixture(tmp_path, monkeypatch, formal=True)
    real_open = checker.os.open

    def software_only(path, *args, **kwargs):
        if isinstance(path, (str, bytes, Path)):
            assert "TopoLab-custody" not in str(path)
            assert "Documents/TopoLab-data" not in str(path)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(checker.os, "open", software_only)
    assert checker.validate_binding(plan)["formal_attempt"] == 1
    assert checker.result_window_seconds(plan) == (7200, 7200)


def test_reserved_second_attempt_needs_new_frozen_remedy_before_external_io(
    tmp_path, monkeypatch
):
    checker, plan, _ = fixture(tmp_path, monkeypatch, formal=True, attempt=2)
    software_bytes = checker.native._software_bytes

    def software_only(path):
        assert Path(path).is_relative_to(checker.REPO), "external evidence/target IO is forbidden"
        return software_bytes(path)

    monkeypatch.setattr(checker.native, "_software_bytes", software_only)
    with pytest.raises(ValueError, match="NEW_FROZEN_REMEDY_REQUIRED"):
        checker.validate_binding(plan)
    with pytest.raises(ValueError, match="NEW_FROZEN_REMEDY_REQUIRED"):
        checker.result_window_seconds(plan)


def test_funded_authority_binds_both_fresh_targets_before_either_attempt(tmp_path, monkeypatch):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    authority["fixed_target"]["attempts"]["2"]["generation"] = (
        PARENT + "/p17-m2-local-input-version-v2")
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="target"):
        checker.validate_binding(plan)


@pytest.mark.parametrize("path,value", [
    (("result_seconds", "exporter"), 1200),
    (("result_seconds", "independent"), 4860),
    (("outer_wall_seconds",), 14400),
    (("outer_wall_seconds",), 86400),
    (("total_new_author_charged_seconds_cap",), 18000),
    (("total_new_author_charged_seconds_cap",), 129600),
    (("permissions", "B_C"), True),
    (("permissions", "formal_activation"), 1),
    (("actors", "independent"), "/root/compat_independent"),
    (("FULL_by_role", "exporter-r1"), 1199),
    (("source_whitelist", "per_author_per_file_reads"), 2),
    (("source_whitelist", "per_author_per_file_reads"), True),
    (("source_whitelist", "r0_metadata"), 39),
    (("source_whitelist", "r1_payload"), 557),
    (("source_whitelist", "version_members"), 1070),
    (("source_whitelist", "metadata_acceptance_before_payload_stat_open"), 1),
    (("formal_admission",), "CLOSED_UNFUNDED_COMPLETE_RESULT_SUFFIX"),
    (("published_source_sha256",), {}),
    (("readiness_freeze_state",), "DRAFT_NOT_YET_REVIEWED"),
    (("implementation_base_commit",), "0" * 40),
    (("independent_preflight_path",), "/private/tmp/other-preflight.json"),
    (("independent_preflight_sha256",), "UNKNOWN_NOT_RUN"),
])
def test_resealed_funded_authority_cannot_change_scope_cost_or_lineage(
    tmp_path, monkeypatch, path, value
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    record = authority
    for key in path[:-1]:
        record = record[key]
    record[path[-1]] = value
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="authority|readiness"):
        checker.validate_binding(plan)


@pytest.mark.parametrize("attempt", [True, 0, 3, "1"])
def test_funded_formal_attempt_is_finite_and_not_boolean(tmp_path, monkeypatch, attempt):
    checker, plan, _ = fixture(tmp_path, monkeypatch, formal=True)
    plan["binding"]["formal_attempt"] = attempt
    with pytest.raises(ValueError, match="attempt"):
        checker.validate_binding(plan)


def test_funded_public_plan_cannot_claim_a_formal_attempt_or_old_protocol(tmp_path, monkeypatch):
    checker, plan, _ = fixture(tmp_path, monkeypatch)
    plan["binding"]["formal_attempt"] = 1
    with pytest.raises(ValueError, match="schema"):
        checker.validate_binding(plan)
    del plan["binding"]["formal_attempt"]
    plan["binding"]["authority_protocol_path"] = checker.HASH_BOUND_PROTOCOL
    with pytest.raises(ValueError, match="protocol"):
        checker.validate_binding(plan)


def test_closed_hash_v1_formal_result_window_retains_1200(tmp_path, monkeypatch):
    checker, plan, _ = fixture(tmp_path, monkeypatch, formal=True)
    old = json.loads((REPO / checker.HASH_BOUND_PROTOCOL).read_bytes())
    old.update(implementation_commit="2f67feee4d89c94b36196122a5930a56d5b8433f",
               preparation_closure_sha256="b"*64, independent_preflight_sha256="c"*64)
    raw = checker.canonical(old)
    (checker.REPO / checker.HASH_BOUND_PROTOCOL).write_bytes(raw)
    sha = checker.digest(raw)
    plan.update(execution_identity=checker.HASH_BOUND_IDENTITY, attempt_index=1,
                root=PARENT+"/p17-m2-local-input-version-v3-hash-bound-20261026")
    plan["content_root"] = plan["root"]+"/content"
    plan["backup_root"] = plan["root"]+"-independent-backup"
    del plan["binding"]["authority_protocol_path"]
    del plan["binding"]["formal_attempt"]
    plan["source_tree"][checker.HASH_BOUND_PROTOCOL] = sha
    plan["preparation_contract_sha256"] = plan["contract_sha256"] = sha
    plan["binding"]["preparation_protocol_sha256"] = sha
    plan["binding"]["execution_protocol_sha256"] = sha
    assert checker.result_window_seconds(plan) == (1200, 1200)


def test_independent_preflight_replay_checks_bound_actual_source_and_runtime(tmp_path, monkeypatch):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    plan["runtime"] = {"python": "/fixed/public/python", "isolated": 1,
                       "cwd": str(checker.REPO), "threads": {"OMP_NUM_THREADS": "1"}}
    preflight = {
        "status": "PASS_PUBLIC_METADATA_LAUNCH_PREFLIGHT", "execution_identity": IDENTITY,
        "actors": authority["actors"],
        "published_source_sha256": authority["published_source_sha256"],
        "runtime": plan["runtime"],
        "expected_white_list_contract": {
            "raw_sha256": checker.CONTENT_CONTRACT_SHA256, "r0_metadata": 40,
            "r1_payload": 558, "version_members": 1071,
            "total_old_source_reads_per_attempt_max": 1196, "per_author_per_file_reads": 1},
    }
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    reseal(checker, plan, authority)
    assert checker.check_funded_preflight(plan, raw)["status"] == preflight["status"]
    preflight["runtime"] = {**preflight["runtime"], "isolated": 0}
    raw = checker.canonical(preflight)
    authority["independent_preflight_sha256"] = checker.digest(raw)
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="preflight"):
        checker.check_funded_preflight(plan, raw)


def test_remedy_preflight_binds_new_file_and_preserves_historical_receipt(tmp_path, monkeypatch):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    authority["independent_preflight_path"] = (
        "/private/tmp/topolab-funded-continuation-20261026/independent/preflight-remedy3.json")
    reseal(checker, plan, authority)
    checker.validate_binding(plan)
    for old_name in ("preflight.json", "preflight-remedy1.json", "preflight-remedy2.json"):
        authority["independent_preflight_path"] = (
            "/private/tmp/topolab-funded-continuation-20261026/independent/" + old_name)
        reseal(checker, plan, authority)
        with pytest.raises(ValueError, match="preflight"):
            checker.validate_binding(plan)


def test_funded_preflight_path_cannot_escape_the_frozen_metadata_file(tmp_path, monkeypatch):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    authority["independent_preflight_path"] = (
        "/private/tmp/topolab-funded-continuation-20261026/independent/../../old-original.json")
    reseal(checker, plan, authority)
    with pytest.raises(ValueError, match="preflight"):
        checker.validate_binding(plan)


@pytest.mark.parametrize("changed", ["first_path", "order", "hash"])
def test_prior_closure_whitelist_is_closed_before_external_metadata_io(
    tmp_path, monkeypatch, changed
):
    checker, plan, authority = fixture(tmp_path, monkeypatch, formal=True)
    if changed == "first_path":
        authority["preparation_closure_paths"][0] = "/private/tmp/unknown-old-original.json"
    elif changed == "order":
        authority["preparation_closure_paths"].reverse()
    else:
        authority["preparation_closure_sha256"] = "b" * 64
    reseal(checker, plan, authority)
    real_open = checker.os.open

    def git_only(path, *args, **kwargs):
        if isinstance(path, (str, bytes, Path)):
            assert "unknown-old-original" not in str(path)
            assert "custody-20261026-results" not in str(path)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(checker.os, "open", git_only)
    with pytest.raises(ValueError, match="closure"):
        checker.validate_binding(plan)
