"""New public IO/transcription checks, independently authored from R fields."""

import importlib.util
import json
import shutil
import struct
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    "separate_R_source_comparator",
    Path(__file__).parents[1] / "scripts/p17_m2_input_export_independent.py",
)
assert _SPEC is not None and _SPEC.loader is not None
checker = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(checker)


def binding(source):  # type: ignore[no-untyped-def]
    return {
        "case_id": source["entry"]["case"]["case_id"],
        "entry": source["entry"],
        "manifest_sha256": source["manifest_sha256"],
        "context_sha256": checker.digest(checker.canonical(source["context"])),
        "source_revision": source["context"]["source_revision"],
        "artifact": checker.reference("new-public-label.json", checker.canonical(source)),
    }


def test_original_public_IO_complete_source_comparison(tmp_path: Path) -> None:
    result = checker.public_check(tmp_path / "new-original-public-fixtures")
    assert result["status"] == "PASS_PUBLIC_IO_ONLY"
    assert result["checkpoint_count"] == 2
    assert result["NN_cases"] == 2
    assert result["scalar_count"] == 1
    assert result["compared_scalar_fields"] > 50000
    assert result["old_source_read_set"] == []
    assert result["FEM_inference_or_complete_history_analysis"] is False
    assert result["damaged_controls_rejected"] == 2


@pytest.mark.parametrize("text", [b'{"a":1,"a":2}', b'{"x":NaN}', b'{"x":1e9999}'])
def test_strict_JSON_refuses_duplicate_nonfinite(text: bytes) -> None:
    with pytest.raises(ValueError):
        checker.parse(text)


def test_JSON_depth_limit() -> None:
    with pytest.raises(ValueError, match="depth"):
        checker.parse(b"[" * 65 + b"0" + b"]" * 65)


@pytest.mark.parametrize("actual", [{"x": 0.0}, {"x": -0.0, "extra": 1}, {"x": 0}])
def test_all_fields_and_signed_zero_are_compared(actual: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        checker.compare_words({"x": -0.0}, actual)


def test_once_reader_refuses_second_read(tmp_path: Path) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    reader = checker.OnceReader(tmp_path, 2, 100)
    assert reader.read("original.json", 100) == b"{}\n"
    with pytest.raises(ValueError, match="repeat"):
        reader.read("original.json", 100)


@pytest.mark.parametrize("relative", ["../outside.json", "/etc/passwd", "a/../original.json"])
def test_once_reader_refuses_path_escape_before_open(tmp_path: Path, relative: str) -> None:
    reader = checker.OnceReader(tmp_path, 1, 100)
    with pytest.raises(ValueError, match="unsafe"):
        reader.read(relative, 100)
    assert reader.seen == set()


def test_once_reader_refuses_symlink(tmp_path: Path) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    (tmp_path / "alias.json").symlink_to("original.json")
    reader = checker.OnceReader(tmp_path, 1, 100)
    with pytest.raises(ValueError, match="symlink"):
        reader.read("alias.json", 100)


def test_once_reader_checks_bytes_and_hash(tmp_path: Path) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    reader = checker.OnceReader(tmp_path, 1, 100)
    with pytest.raises(ValueError, match="SHA"):
        reader.read("original.json", 100, sha256="f" * 64)
    assert reader.table == [checker.reference("original.json", b"{}\n")]
    assert reader.seen == {"original.json"}


@pytest.mark.parametrize("maximum,total,files", [(2, 100, 1), (100, 2, 1), (100, 100, 0)])
def test_once_reader_file_byte_caps(tmp_path: Path, maximum: int, total: int, files: int) -> None:
    (tmp_path / "original.json").write_bytes(b"{}\n")
    reader = checker.OnceReader(tmp_path, files, total)
    with pytest.raises(ValueError, match="cap"):
        reader.read("original.json", maximum)


def test_actual_stored_physical_is_preserved_not_reconstructed() -> None:
    source = checker.public_label((12, 6, 3))
    source["stored"]["physical_density"][0] = 0.75
    row = binding(source)
    producer, audit = checker.label_views(source, row)
    assert audit["stored"]["physical_density"][0] == 0.75
    assert producer["stored"]["design_density"][0] == 0.5
    assert "physical_density" not in producer["stored"]
    assert "sensitivity_weight" not in producer["stored"]
    assert "history" not in audit
    assert "displacements" not in audit["terminal"]
    assert "reactions" not in audit["terminal"]
    assert audit["total_updates"] == 11
    assert len(audit["recent"]) == 11


def test_full_history_prefix_is_never_analyzed_or_exported() -> None:
    source = checker.public_label((12, 6, 3))
    # Prefix has no numerical fields, proving the comparator uses only n/recent.
    source["result"]["history"].insert(0, {"deliberately_unanalyzed_prefix": True})
    for state in source["result"]["history"][-11:]:
        state["iteration"] += 1
    source["stored"]["iterations"] = 12
    _, audit = checker.label_views(source, binding(source))
    assert len(audit["recent"]) == 11
    assert audit["recent"][0]["iteration"] == 2
    assert "deliberately_unanalyzed_prefix" not in json.dumps(audit)


@pytest.mark.parametrize("change", ["role", "initialization", "context", "shape", "float32"])
def test_label_binding_or_format_mismatch_stops(change: str) -> None:
    source = checker.public_label((12, 6, 3))
    row = deepcopy(binding(source))
    if change == "role":
        source["entry"]["role"] = "fit_validation"
    elif change == "initialization":
        source["initialization"] = "candidate"
    elif change == "context":
        source["context"]["source_revision"] = "0" * 40
    elif change == "shape":
        source["stored"]["tensor_shape"] = [1, 3, 6, 13]
    else:
        source["stored"]["design_density"][0] = 0.1
    with pytest.raises(ValueError):
        checker.label_views(source, row)


def test_short_physical_plateau_window_stops() -> None:
    source = checker.public_label((12, 6, 3))
    source["result"]["history"] = source["result"]["history"][-10:]
    source["stored"]["iterations"] = 10
    source["stored"]["stop_reason"] = "physical_plateau"
    with pytest.raises(ValueError, match="window"):
        checker.label_views(source, binding(source))


def model(family: str = "C"):  # type: ignore[no-untyped-def]
    return {"family": family, "seed": 17, "epoch": 1, "context_sha256": "a" * 64}


@pytest.mark.parametrize("family", ["C", "W"])
def test_exact_synthetic_Safetensors_header_body(family: str) -> None:
    row = model(family)
    checker.check_safetensors(checker.public_model(row), row)


def test_unweighted_checkpoint_cannot_replace_W() -> None:
    with pytest.raises(ValueError, match="provenance"):
        checker.check_safetensors(checker.public_model(model("C")), model("W"))


def test_Safetensors_nonfinite_tensor_stops() -> None:
    row = model()
    raw = checker.public_model(row)
    bad = raw[:-4] + struct.pack("<f", float("nan"))
    with pytest.raises(ValueError, match="nonfinite"):
        checker.check_safetensors(bad, row)


def test_source_fields_compared_even_if_claimed_digest_is_unchanged() -> None:
    source = checker.public_label((12, 6, 3))
    producer, _ = checker.label_views(source, binding(source))
    altered = deepcopy(producer)
    altered["stored"]["design_density"][0] = 0.75
    assert altered["bit_digests"] == producer["bit_digests"]
    with pytest.raises(ValueError, match="binary64"):
        checker.compare_words(producer, altered)


def test_output_extra_history_field_stops() -> None:
    source = checker.public_label((12, 6, 3))
    producer, _ = checker.label_views(source, binding(source))
    altered = dict(producer, history=source["result"]["history"])
    with pytest.raises(ValueError, match="field set"):
        checker.compare_words(producer, altered)


def primary_subject():  # type: ignore[no-untyped-def]
    """Post-authorship exposure: exporter is a subject, never comparator oracle."""
    spec = importlib.util.spec_from_file_location(
        "R_exporter_subject", Path(__file__).parents[1] / "scripts/p17_m2_input_export.py"
    )
    assert spec and spec.loader
    subject = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subject)
    return subject


@pytest.mark.parametrize("mesh", [(12, 6, 3), (24, 12, 6)])
def test_primary_projections_match_independently_authored_source_fields(mesh) -> None:  # type: ignore[no-untyped-def]
    subject = primary_subject()
    source = checker.public_label(mesh)
    row = binding(source)
    expected = checker.label_views(source, row)
    actual = subject.label_views(source, row)
    assert checker.compare_words(list(expected), list(actual)) > 1000


@pytest.mark.parametrize("family", ["C", "P", "W", "S"])
def test_primary_accepts_independently_authored_original_weight_bytes(family: str) -> None:
    subject = primary_subject()
    row = model(family)
    raw = checker.public_model(row)
    contract = checker.parse(subject.CONTRACT.read_bytes())
    subject.check_weights(raw, row, contract)
    checker.check_safetensors(raw, row)


def test_R0_wire_from_new_synthetic_metadata_only(monkeypatch, tmp_path: Path) -> None:  # type: ignore[no-untyped-def]
    # Reuse the primary's new metadata as a test subject, filling the committed
    # schema's fields its minimal fixture omitted. No historical path is read.
    spec = importlib.util.spec_from_file_location(
        "new_R_metadata_subject", Path(__file__).with_name("test_p17_m2_input_export.py")
    )
    assert spec and spec.loader
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    contract = fixture.source_metadata(tmp_path)
    subject = primary_subject()
    fit_path = tmp_path / "b3-v1-fits/b3_training.json"
    fits = checker.parse(fit_path.read_bytes())
    data = fits["context"]["data_index"]
    for i, outcome in enumerate(data["entries"], 1):
        entry = outcome["entry"]
        case_id = "tlcase-v1-" + f"{i:064x}"
        entry["case"]["case_id"] = case_id
        artifact = outcome["artifact"]
        artifact["access"]["entry"] = deepcopy(entry)
        artifact["relative_path"] = (
            f"artifacts/label/{case_id}/{artifact['access']['artifact_sha256']}.json"
        )
    manifest = data["manifest"]
    manifest["catalog"] = {
        "catalog_version": "topolab.b3.catalog.v1",
        "entries": [o["entry"] for o in data["entries"]],
    }
    manifest_sha = checker.digest(checker.canonical(manifest))
    data["manifest_sha256"] = manifest_sha
    for outcome in data["entries"]:
        outcome["artifact"]["manifest_sha256"] = manifest_sha
    data_sha = checker.digest(checker.canonical(data))
    fits["context"]["data_index_sha256"] = data_sha
    fits["index_version"] = "topolab.b3.training-index.v1"
    fits["context_sha256"] = checker.digest(checker.canonical(fits["context"]))
    contract["R0"]["embedded_B3_data_index_sha256"] = data_sha
    monkeypatch.setattr(checker, "B3_DATA_HASH", data_sha)
    monkeypatch.setattr(
        checker, "CATALOG_HASH", checker.digest(checker.canonical(manifest["catalog"]))
    )
    wroot = "b4-5-weighted-terminal/fit"
    for row in contract["checkpoints"]["fixed_rows"]:
        weighted = row["family"] == "W"
        if weighted:
            ordinal = [17, 29, 43].index(row["seed"])
            unit_path = tmp_path / f"{wroot}/units/{ordinal:04d}.json"
            unit = checker.parse(unit_path.read_bytes())
            ref = unit["payload"]
            root = wroot
        else:
            outcome = next(
                o
                for o in fits["outcomes"]
                if (o["recipe"], o["seed"]) == (row["family"], row["seed"])
            )
            ref = outcome["selection"]
            root = "b3-v1-fits"
        selection = checker.parse(
            (tmp_path / root / f"artifacts/selection/{ref['sha256']}.json").read_bytes()
        )
        history = selection["history_schema"] if weighted else selection
        history["selection_version"] = "topolab.b3.selection.v1"
        if not weighted:
            history["context_sha256"] = fits["context_sha256"]
        raw = checker.canonical(selection)
        ref.update(sha256=checker.digest(raw), byte_size=len(raw))
        (tmp_path / root / f"artifacts/selection/{ref['sha256']}.json").write_bytes(raw)
        if weighted:
            unit_path.write_bytes(checker.canonical(unit))
    fit_path.write_bytes(checker.canonical(fits))
    for base, count in ((wroot, 3), ("b4-30-z-reflection-repair-v2/sentinel/reference", 18)):
        previous = "0" * 64
        for i in range(count):
            path = tmp_path / f"{base}/units/{i:04d}.json"
            unit = checker.parse(path.read_bytes())
            unit["previous_sha256"] = previous
            raw = checker.canonical(unit)
            path.write_bytes(raw)
            previous = checker.digest(raw)
        progress_path, summary_path = (
            tmp_path / base / "progress.json",
            tmp_path / base / "summary.json",
        )
        progress = checker.parse(progress_path.read_bytes())
        progress["head_sha256"] = previous
        progress_path.write_bytes(checker.canonical(progress))
        summary = {
            key: progress[key]
            for key in ("context_sha256", "completed", "attempted", "head_sha256")
        }
        summary_path.write_bytes(checker.canonical(summary))
    for item in contract["R0"]["literal_bootstrap_files"]:
        item["expected_sha256"] = checker.digest((tmp_path / item["relative_path"]).read_bytes())
    expected = checker.build_registry(checker.OnceReader(tmp_path, 40, 32 * checker.MIB), contract)
    actual = subject.register(subject.Reader(tmp_path), contract)
    assert checker.compare_words(expected, actual) > 6000
    assert len(expected["metadata"]) == 40
    assert len(expected["labels"]) == 528
    assert not any(
        "artifacts/label/" in r["path"] or r["path"].endswith(".safetensors")
        for r in expected["metadata"]
    )


def resource_subject():  # type: ignore[no-untyped-def]
    profile = b" 1.00 real 0.10 user 0.00 sys\n100 maximum resident set size\n"
    sampler = b" 0.02 real 0.01 user 0.00 sys\n20 maximum resident set size\n"

    def timer(pid):  # type: ignore[no-untyped-def]
        return {
            "statistics_source": "os.wait4",
            "wall_source": "controller_monotonic_observed",
            "exit_code": 0,
            "pid": pid,
            "rss_unit": "bytes",
            "native": {
                "wall_seconds": 1.0,
                "user_seconds": 0.1,
                "system_seconds": 0.0,
                "rss_bytes": 10,
            },
        }

    record = {
        "schema": "topolab.v2.m2-native-rss-exit-assurance.v1",
        "status": "PENDING_POSTEXIT",
        "role": "synthetic-r-io",
        "argv": ["new-public-tool"],
        "platform": "darwin",
        "software_only": True,
        "scientific_resource_admission": "NOT_RUN",
        "controller_complete_exit": "UNKNOWN_PENDING_OUTER_PROFILE",
        "exit_code": 0,
        "software_result": "PUBLIC_COMMAND_EXIT_OBSERVED",
        "cleanup": {"group_gone": True, "leader_exit": 0},
        "ps_rss_unit": "KiB*1024",
        "native_rss_unit": "bytes",
        "profile_sha256": checker.digest(profile),
        "log_sha256": checker.digest(b""),
        "native": {
            "wall_seconds": 1.0,
            "user_seconds": 0.1,
            "system_seconds": 0.0,
            "rss_bytes": 100,
        },
        "limit_bytes": 4294967296,
        "observed_outer_wall_seconds": 1.2,
        "timeout_seconds": 100,
        "target_sample_interval_seconds": 0.5,
        "controller_rss_peak_bytes": 50,
        "pid": 10,
        "timer_native_exit": timer(10),
        "helpers": [
            {
                "profile": "sampler-0.time",
                "role": "rss-sampler-0",
                "profile_sha256": checker.digest(sampler),
                "exit_code": 0,
                "problem": None,
                "cleanup": {"group_gone": True, "leader_exit": 0},
                "pid": 20,
                "native": {
                    "wall_seconds": 0.02,
                    "user_seconds": 0.01,
                    "system_seconds": 0.0,
                    "rss_bytes": 20,
                },
                "timer_native_exit": timer(20),
            }
        ],
        "samples": [
            {
                "offset_seconds": 0.1,
                "actual_interval_seconds": None,
                "controller_rss_bytes": 50,
                "group_plus_controller_rss_bytes": 150,
                "roles": [
                    {"pid": 10, "parent": 1, "pgid": 10, "rss_bytes": 10},
                    {"pid": 11, "parent": 10, "pgid": 10, "rss_bytes": 90},
                ],
            }
        ],
        "native_plus_controller_and_sampler_rss_bytes": 190,
        "escaped_group_cleanup": [],
    }
    return record, profile, {"sampler-0.time": sampler}


def test_resource_reconciliation_requires_outer_exit_and_cost_closure() -> None:
    record, profile, helpers = resource_subject()
    result = checker.audit_native_record(
        record,
        profile=profile,
        log=b"",
        helper_profiles=helpers,
        expected_role="synthetic-r-io",
        expected_argv=["new-public-tool"],
        platform="darwin",
    )
    assert result["inner_empirical_RSS_bytes"] == 190
    assert result["inner_minimum_charge_seconds"] == 11.2
    assert result["outer_timer_supervisor_exits_and_full_role_cost"] == "CALLER_MUST_CLOSE"
    assert result["B_C_admission"] is False


@pytest.mark.parametrize("field", ["native", "units", "timer", "helper", "sum", "exit", "escape"])
def test_resource_forgery_cannot_be_hidden_by_PASS(field: str) -> None:
    record, profile, helpers = resource_subject()
    if field == "native":
        record["native"]["rss_bytes"] = 1
    elif field == "units":
        record["ps_rss_unit"] = "bytes"
    elif field == "timer":
        record["timer_native_exit"]["exit_code"] = 1
    elif field == "helper":
        helpers = {}
    elif field == "sum":
        record["samples"][0]["group_plus_controller_rss_bytes"] = 1
    elif field == "exit":
        record["cleanup"]["group_gone"] = None
    else:
        record["samples"][0]["roles"][1]["pgid"] = 99
    with pytest.raises(ValueError):
        checker.audit_native_record(
            record,
            profile=profile,
            log=b"",
            helper_profiles=helpers,
            expected_role="synthetic-r-io",
            expected_argv=["new-public-tool"],
            platform="darwin",
        )


def test_native_profile_GNU_units_and_missing_identity() -> None:
    parsed = checker.native_profile(b"TOPOLAB_NATIVE 0.1 0.0 0.0 20\n", "linux")
    assert parsed["rss_bytes"] == 20480
    with pytest.raises(ValueError):
        checker.native_profile(b"no native profile", "darwin")


def full_v2_subject():  # type: ignore[no-untyped-def]
    pending = {
        "execution_identity": checker.EXECUTION_V2,
        "role": "independent-public-check",
        "plan_sha256": "a" * 64,
        "frozen_FULL_seconds": 120,
        "clock_domain": checker.CLOCK_V2,
        "clock_resolution_seconds": 0.001,
        "external_argv": [["new-supervisor"], ["new-finalizer"]],
    }
    completion = dict(
        pending,
        status="PENDING_EXTERNAL_EXIT",
        pending_sha256=checker.digest(checker.canonical(pending)),
        cleanup={"group_gone": True},
        final_serializer_pid=102,
        resource_components=[
            {
                "pid": 101,
                "kind": "self_high_water",
                "statistics_source": "resource.getrusage",
                "rss_unit": "bytes",
                "phases": ["preflush", "postflush"],
                "samples_bytes": [200, 210],
            },
            {
                "pid": 102,
                "kind": "self_high_water",
                "statistics_source": "resource.getrusage",
                "rss_unit": "bytes",
                "phases": ["preflush", "postflush"],
                "samples_bytes": [100, 150],
            },
        ],
    )
    events = [
        {
            "event_id": "raw-observed-1",
            "clock_domain": checker.CLOCK_V2,
            "start_seconds": 1000.0,
            "end_seconds": 1007.015,
            "wall_seconds": 7.014,
            "argv": ["new-supervisor"],
            "exit_code": 0,
            "complete": True,
        },
        {
            "event_id": "raw-observed-2",
            "clock_domain": checker.CLOCK_V2,
            "start_seconds": 1109.118,
            "end_seconds": 1109.224,
            "wall_seconds": 0.106,
            "argv": ["new-finalizer"],
            "exit_code": 0,
            "complete": True,
        },
    ]
    record, profile, helpers = resource_subject()
    inner = {
        "record": record,
        "profile": profile,
        "log": b"",
        "helper_profiles": helpers,
        "expected_role": "synthetic-r-io",
        "expected_argv": ["new-public-tool"],
        "platform": "darwin",
    }
    return pending, completion, events, inner


def full_v2_audit(pending, completion, events, inner):  # type: ignore[no-untyped-def]
    return checker.audit_full_role_v2(
        pending, completion, raw_tool_events=events,
        expected_role="independent-public-check", expected_plan_sha256="a" * 64,
        inner_evidence=inner,
    )


def test_new_FULL_retains_complete_disjoint_wall_and_same_process_peak() -> None:
    pending, completion, events, inner = full_v2_subject()
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "PASS_R_V2_FULL_ROLE"
    assert result["whole_wall_seconds"] == pytest.approx(109.224)
    assert result["frozen_FULL_seconds"] == 120
    assert result["known_cost_lower_bound_seconds"] == 120
    assert result["RSS_envelope_bytes"] == 210 + 150 + 190
    assert result["source_successor_admitted"] is False
    assert result["B_C_admission"] is False


@pytest.mark.parametrize("last_end,accepted", [(1110.0, True), (1110.0001, False)])
def test_complete_outer_plus_ten_exact_and_just_over_cap(last_end: float, accepted: bool) -> None:
    pending, completion, events, inner = full_v2_subject()
    events[-1]["end_seconds"] = last_end
    result = full_v2_audit(pending, completion, events, inner)
    assert result["full_role_evidence_accepted"] is accepted
    if not accepted:
        assert result["known_cost_lower_bound_seconds"] == 121


@pytest.mark.parametrize("damage", [
    "old20", "old_identity", "final_exit", "missing_exit", "clock", "missing_RSS",
    "inner_only", "changed_plan", "changed_pending", "wrong_argv", "cleanup",
])
def test_full_role_faults_close_suffix_and_preserve_available_peaks(damage: str) -> None:
    pending, completion, events, inner = full_v2_subject()
    if damage == "old20":
        pending["frozen_FULL_seconds"] = completion["frozen_FULL_seconds"] = 20
    elif damage == "old_identity":
        pending["execution_identity"] = completion["execution_identity"] = "v1"
    elif damage == "final_exit":
        events[-1]["exit_code"] = 1
    elif damage == "missing_exit":
        events[-1]["exit_code"] = None
    elif damage == "clock":
        events[-1]["end_seconds"] = 999
    elif damage == "missing_RSS":
        completion["resource_components"].pop()
    elif damage == "inner_only":
        events.clear()
    elif damage == "changed_plan":
        completion["plan_sha256"] = "b" * 64
    elif damage == "changed_pending":
        completion["pending_sha256"] = "b" * 64
    elif damage == "wrong_argv":
        events[-1]["argv"] = ["unregistered-glue"]
    else:
        completion["cleanup"]["group_gone"] = None
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["source_successor_admitted"] is False
    if damage == "final_exit":
        assert result["RSS_envelope_bytes"] == 550
        assert result["actual_exit_codes"][-1] == 1


def test_failed_native_exit_keeps_own_available_peak_before_rejection() -> None:
    _, completion, _, inner = full_v2_subject()
    record = {
        "statistics_source": "os.wait4", "wall_source": "controller_monotonic_observed",
        "pid": 103, "rss_unit": "bytes", "exit_code": 1,
        "native": {"wall_seconds": 0.1, "user_seconds": 0.0, "system_seconds": 0.0,
                   "rss_bytes": 250},
    }
    completion["resource_components"].append(
        {"pid": 103, "kind": "wait4", "platform": "darwin", "record": record}
    )
    result = checker.audit_v2_resource_components(completion, inner_evidence=inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["RSS_components_bytes"]["103"] == 250
    assert result["RSS_envelope_bytes"] == 800


def test_outer_native_profile_and_wait4_are_independently_parsed_and_added() -> None:
    _, completion, _, inner = full_v2_subject()
    profile = b"0.1 real 0.0 user 0.0 sys\n180 maximum resident set size\n"
    completion["resource_components"].extend([
        {
            "pid": 101, "kind": "native_profile", "profile": "outer.time",
            "profile_sha256": checker.digest(profile), "platform": "darwin",
            "actual_exit_code": 0,
        },
        {
            "pid": 103, "kind": "wait4", "platform": "darwin",
            "record": {
                "statistics_source": "os.wait4",
                "wall_source": "controller_monotonic_observed", "pid": 103,
                "rss_unit": "bytes", "exit_code": 0,
                "native": {"wall_seconds": 0.1, "user_seconds": 0.0,
                           "system_seconds": 0.0, "rss_bytes": 250},
            },
        },
    ])
    result = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, native_profiles={"outer.time": profile},
    )
    assert result["status"] == "PENDING_EXTERNAL_EXIT"
    assert result["RSS_envelope_bytes"] == 210 + 150 + 250 + 190
    assert result["RSS_components_bytes"]["101"] == 210  # Same supervisor, not double counted.
    completion["resource_components"][-2]["profile_sha256"] = "b" * 64
    rejected = checker.audit_v2_resource_components(
        completion, inner_evidence=inner, native_profiles={"outer.time": profile},
    )
    assert rejected["status"] == "STOP_NO_RETRY"
    assert "profile hash" in rejected["reason"]


@pytest.mark.parametrize("excess,accepted", [(0.001, True), (0.001001, False)])
def test_tool_wall_display_resolution_is_frozen_not_a_cap_slack(
    excess: float, accepted: bool,
) -> None:
    pending, completion, events, inner = full_v2_subject()
    events[0]["wall_seconds"] = events[0]["end_seconds"] - events[0]["start_seconds"] + excess
    result = full_v2_audit(pending, completion, events, inner)
    assert result["full_role_evidence_accepted"] is accepted


def test_arbitrary_larger_clock_resolution_cannot_loosen_outer_checks() -> None:
    pending, completion, events, inner = full_v2_subject()
    pending["clock_resolution_seconds"] = completion["clock_resolution_seconds"] = 1.0
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert "resolution" in result["reason"]


def test_nonfinite_raw_clock_still_retains_failure_and_RSS_evidence() -> None:
    pending, completion, events, inner = full_v2_subject()
    events[-1]["end_seconds"] = float("nan")
    result = full_v2_audit(pending, completion, events, inner)
    assert result["status"] == "STOP_NO_RETRY"
    assert result["RSS_envelope_bytes"] == 550
    assert result["raw_tool_event_ids_and_hashes"][-1]["sha256"] is None


def test_content_snapshot_guard_retains_literal_frozen_scope() -> None:
    contract = (
        Path(__file__).parents[1]
        / "docs/planning/p17_m2_input_export_preparation_proposal.json"
    )
    assert checker.digest(contract.read_bytes()) == checker.CONTENT_CONTRACT_SHA256


def test_independent_new_backup_compares_complete_bytes_including_empty_log(tmp_path: Path) -> None:
    root, backup = tmp_path / "new-prefix", tmp_path / "new-backup"
    for folder in (root, backup):
        folder.mkdir()
        (folder / "new-view.json").write_bytes(b'{"new":true}\n')
        (folder / "empty-native.log").write_bytes(b"")
    result = checker.audit_new_backup(root, backup, public_fixture=True)
    assert result["status"] == "PASS_INDEPENDENT_NEW_BACKUP"
    assert result["member_count"] == 2
    assert result["total_bytes"] == len(b'{"new":true}\n')
    assert result["old_input_reads"] == 0
    (backup / "new-view.json").write_bytes(b'{"new":false}')
    rejected = checker.audit_new_backup(root, backup, public_fixture=True)
    assert rejected["status"] == "STOP_NO_RETRY"
    assert "bytes/hash" in rejected["reason"]


@pytest.mark.parametrize("damage", ["extra", "symlink", "ancestor_symlink"])
def test_new_backup_rejects_extra_or_symlink_member(tmp_path: Path, damage: str) -> None:
    root, backup = tmp_path / "new-prefix", tmp_path / "new-backup"
    for folder in (root, backup):
        folder.mkdir()
        (folder / "data.json").write_bytes(b"{}\n")
    if damage == "extra":
        (backup / "extra.json").write_bytes(b"{}\n")
    elif damage == "symlink":
        (backup / "data.json").unlink()
        (backup / "data.json").symlink_to(root / "data.json")
    else:
        alias = tmp_path / "alias"
        alias.symlink_to(root, target_is_directory=True)
        root = alias
    result = checker.audit_new_backup(root, backup, public_fixture=True)
    assert result["status"] == "STOP_NO_RETRY"


def test_new_backup_exclusion_is_literal_and_preserves_stable_prefix(tmp_path: Path) -> None:
    root, backup = tmp_path / "new-prefix", tmp_path / "new-backup"
    for folder in (root, backup):
        (folder / "receipts").mkdir(parents=True)
        (folder / "stable.json").write_bytes(b"{}\n")
    (root / "receipts/shared-closeout-controller.log").write_bytes(b"active-new-log")
    result = checker.audit_new_backup(
        root, backup, public_fixture=True, excluded_prefixes=("receipts/shared-closeout",),
    )
    assert result["status"] == "PASS_INDEPENDENT_NEW_BACKUP"
    assert result["member_count"] == 1


def test_backup_refuses_v1_or_old_DATA_before_stat(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden_stat(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("no old path may be stat'ed")

    monkeypatch.setattr(Path, "lstat", forbidden_stat)
    old = checker.AUTHORIZED_DATA_ROOT / "p17-m2-input-export-preparation-v1"
    result = checker.audit_new_backup(old, old.with_name(old.name + "-independent-backup"))
    assert result["status"] == "STOP_NO_RETRY"
    assert "literal NEW v2" in result["reason"]
    result = checker.audit_new_backup(old, old.with_name(old.name + "-copy"), public_fixture=True)
    assert result["status"] == "STOP_NO_RETRY"
    assert "public fixture cannot open DATA" in result["reason"]


@pytest.mark.skipif(shutil.which("node") is None, reason="existing Node runtime unavailable")
def test_trusted_JS_boundary_matches_raw_gap_cap_and_actual_exit() -> None:
    pending, completion, events, inner = full_v2_subject()
    resources = checker.audit_v2_resource_components(completion, inner_evidence=inner)
    cases = []
    for damage in (
        "none", "cap", "exit", "pending", "resource_identity", "missing_exit", "wrong_clock",
    ):
        row = deepcopy([pending, completion, events, resources, completion["pending_sha256"]])
        if damage == "cap":
            row[2][-1]["end_seconds"] = 1110.001
        elif damage == "exit":
            row[2][-1]["exit_code"] = 1
        elif damage == "pending":
            row[4] = "b" * 64
        elif damage == "resource_identity":
            row[3]["role"] = "exporter-r1"
        elif damage == "missing_exit":
            row[2][-1]["exit_code"] = None
        elif damage == "wrong_clock":
            for event in row[2]:
                event["clock_domain"] = "unregistered-derived-clock"
        cases.append(row)
    script = Path(__file__).parents[1] / "scripts/p17_m2_input_export_dispatch.js"
    command = (
        "const fs=require('fs');const {finishExternal}=require(process.argv[1]);"
        "console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,'utf8'))"
        ".map(args=>finishExternal(...args))))"
    )
    observed = subprocess.run(
        ["node", "-e", command, str(script)], input=json.dumps(cases),
        text=True, capture_output=True, check=True,
    )
    results = json.loads(observed.stdout)
    assert results[0]["whole_wall_seconds"] == pytest.approx(109.224)
    assert results[0]["status"] == "PASS_R_V2_FULL_ROLE"
    assert all(result["status"] == "STOP_NO_RETRY" for result in results[1:])
    assert results[2]["RSS_envelope_bytes"] == 550
