"""New public-only unit regressions for the admitted strict23 registration seam."""

import hashlib
import importlib.util
import os
import sys
from contextlib import contextmanager
from pathlib import Path

import pytest

REPO = Path(__file__).parents[1]


def module(name):
    path = REPO / "scripts" / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


producer = module("p17_m2_input_export")


def mutation(monkeypatch, source, mode):
    original, real = source.stat(), os.fdopen

    @contextmanager
    def opened(fd, *args, **kwargs):
        with real(fd, *args, **kwargs) as stream:

            class Stream:
                def read(self, limit):
                    raw = stream.read(1 if mode == "short" else limit)
                    if mode == "mtime":
                        os.utime(source, ns=(original.st_atime_ns, original.st_mtime_ns + 89))
                    elif mode == "replacement":
                        replacement = source.with_name("replacement")
                        replacement.write_bytes(raw)
                        replacement.replace(source)
                    elif mode == "missing":
                        source.unlink()
                    return raw

            yield Stream()

    monkeypatch.setattr(os, "fdopen", opened)


def test_old_unbound_metadata_remains_strict(tmp_path, monkeypatch):
    source = tmp_path / "metadata.json"
    source.write_bytes(b'{"public":true}\n')
    mutation(monkeypatch, source, "mtime")
    reader = producer.Reader(
        tmp_path,
        execution_identity=producer.LOCAL_IDENTITY,
        source_identity_checks=True,
        source_identity_policy=producer.PREBOUND_SHA256_POLICY,
    )
    with pytest.raises(ValueError, match="source changed"):
        reader.packet(source.name, 100)
    assert reader.failures[0]["expected_sha256"] is None
    assert reader.failures[0]["mtime_changes"]["after"] == 89


@pytest.fixture
def registered(tmp_path, monkeypatch):
    registered = module("p17_m2_registered_input")
    source = tmp_path / "new-public-source"
    source.mkdir()
    specs = registered.control.load("p17_m2_source_binding_independent").metadata_specs()
    rows = []
    for spec in specs:
        path = source / spec["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = b'{"public":true}\n'
        path.write_bytes(raw)
        identity = {
            key: getattr(path.stat(), key) for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")
        }
        rows.append(
            {
                "path": spec["path"],
                "byte_size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                **{point: dict(identity) for point in ("declared", "before", "after", "closing")},
            }
        )
    certificate = {"registered_context": {"source_root": str(source)}, "source_observations": rows}
    envelope, actual = tmp_path / "certificate.json", tmp_path / "actual.json"
    envelope.write_bytes(b'{"public_envelope":true}\n')
    actual.write_bytes(b'{"actual":true}\n')
    recovery = registered.control.load("p17_m2_source_binding_recovery")
    calls = []

    def verify(envelope_value, actual_value, *, kind):
        calls.append((envelope_value, actual_value, kind))
        assert envelope_value == {"public_envelope": True}
        assert actual_value == {"actual": True}
        assert kind == "public"
        return certificate, {"full_role_evidence_accepted": True}

    monkeypatch.setattr(recovery, "verify_registration", verify, raising=False)
    plan = {
        "execution_identity": registered.IDENTITY,
        "scope": registered.control.REHEARSAL_SCOPE,
        "source_root": str(source),
        "source_identity_policy": producer.PREBOUND_SHA256_POLICY,
        "binding": {
            "strict23_registration": {
                "certificate_path": str(envelope),
                "certificate_sha256": hashlib.sha256(envelope.read_bytes()).hexdigest(),
                "finalize_actual_path": str(actual),
                "finalize_actual_sha256": hashlib.sha256(actual.read_bytes()).hexdigest(),
            }
        },
    }
    original_authority = registered.authority

    def authority(raw=None):
        value = original_authority(raw)
        value["registration"]["public"] = {
            "certificate_paths": [str(envelope), str(tmp_path / "backup-certificate.json")],
            "finalize_actual_path": str(actual),
        }
        return value

    monkeypatch.setattr(registered, "authority", authority)

    def pair(kind, attempt, expected):
        assert (kind, attempt, expected) == (
            "public",
            1,
            plan["binding"]["strict23_registration"]["certificate_sha256"],
        )
        return {"public_envelope": True}, [envelope, tmp_path / "backup-certificate.json"]

    monkeypatch.setattr(recovery, "certificate_pair", pair)
    return registered, plan, source, rows, calls


def reader_for(registered, plan, source):
    return registered.source_reader(
        plan,
        source,
        execution_identity=producer.LOCAL_IDENTITY,
        source_identity_checks=True,
        source_identity_policy=producer.PREBOUND_SHA256_POLICY,
    )


def test_registered_mtime_uses_same_buffer_and_raw_times(registered, monkeypatch):
    api, plan, source, rows, calls = registered
    path = source / rows[0]["path"]
    before = path.stat().st_mtime_ns
    reader = reader_for(api, plan, source)
    mutation(monkeypatch, path, "mtime")
    assert reader.packet(rows[0]["path"], 100) == {"public": True}
    assert len(calls) == 1
    observed = reader.source_observations[0]
    assert observed["expected_sha256"] == rows[0]["sha256"]
    assert observed["declared"]["st_mtime_ns"] == before
    assert observed["mtime_changes"] == {"before": 0, "after": 89, "closing": 89}


@pytest.mark.parametrize("mode", ["short", "replacement", "missing"])
def test_registered_mtime_policy_retains_other_guards(registered, monkeypatch, mode):
    api, plan, source, rows, _ = registered
    reader = reader_for(api, plan, source)
    mutation(monkeypatch, source / rows[0]["path"], mode)
    with pytest.raises((ValueError, FileNotFoundError)):
        reader.packet(rows[0]["path"], 100)
    assert reader.failures[0]["path"] == rows[0]["path"]
    assert reader.failures[0]["declared"] is not None
    assert reader.source_observations == []


def test_registered_anchor_rejects_same_hash_replacement_before_read(registered):
    api, plan, source, rows, _ = registered
    reader = reader_for(api, plan, source)
    path = source / rows[0]["path"]
    other = source / "replacement"
    other.write_bytes(path.read_bytes())
    other.replace(path)
    with pytest.raises(ValueError, match="registered physical anchor"):
        reader.packet(rows[0]["path"], 100)
    assert reader.failures[0]["returned_bytes"] is None
    assert reader.failures[0]["declared"]["st_ino"] != rows[0]["declared"]["st_ino"]


def test_remaining_unbound_metadata_is_still_strict(registered, monkeypatch):
    api, plan, source, _, _ = registered
    path = source / "not-registered.json"
    path.write_bytes(b'{"public":true}\n')
    reader = reader_for(api, plan, source)
    mutation(monkeypatch, path, "mtime")
    with pytest.raises(ValueError, match="source changed"):
        reader.packet(path.name, 100)
    assert reader.failures[0]["expected_sha256"] is None


@pytest.mark.parametrize("change", ["wrong_hash", "wrong_size", "source_root", "missing_proof"])
def test_registered_rejects_conflicts_without_source_bytes(registered, change):
    api, plan, source, rows, _ = registered
    if change == "missing_proof":
        del plan["binding"]["strict23_registration"]
        with pytest.raises(ValueError, match="registration"):
            reader_for(api, plan, source)
        return
    if change == "source_root":
        with pytest.raises(ValueError, match="source root"):
            reader_for(api, plan, source / "different")
        return
    reader = reader_for(api, plan, source)
    kwargs = {"expected": "0" * 64} if change == "wrong_hash" else {"size": 1}
    with pytest.raises(ValueError, match="registered expected"):
        reader.read(rows[0]["path"], 100, **kwargs)
    assert reader.failures[0]["returned_bytes"] is None


def test_missing_registered_observation_is_rejected(registered):
    api, _, _, rows, _ = registered
    del rows[0]["closing"]
    with pytest.raises(ValueError, match="registration observations"):
        api.registration_bindings({"source_observations": rows})


def test_registered_wrong_buffer_hash_retains_context(registered):
    api, plan, source, rows, _ = registered
    reader = reader_for(api, plan, source)
    path = source / rows[0]["path"]
    path.write_bytes(b'{"public":null}\n')
    with pytest.raises(ValueError, match="source SHA"):
        reader.read(rows[0]["path"], 100)
    failed = reader.failures[0]
    assert failed["expected_sha256"] == rows[0]["sha256"]
    assert failed["returned_bytes"] == rows[0]["byte_size"]
    assert failed["closing"] is not None
    assert failed["registered_preread_anchor"] == rows[0]["declared"]


def test_registered_bad_proof_sha_never_constructs_reader(registered):
    api, plan, source, _, _ = registered
    plan["binding"]["strict23_registration"]["finalize_actual_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="proof SHA"):
        reader_for(api, plan, source)


def test_registered_rejected_native_registration_never_constructs_reader(registered, monkeypatch):
    api, plan, source, _, _ = registered

    def rejected(*args, **kwargs):
        raise ValueError("native actual return is not accepted")

    monkeypatch.setattr(
        api.control.load("p17_m2_source_binding_recovery"), "verify_registration", rejected
    )
    with pytest.raises(ValueError, match="native actual return"):
        reader_for(api, plan, source)


def test_new_plan_is_pure_and_dynamic_proof_bound(registered, monkeypatch):
    api, plan, _, _, _ = registered
    reference = plan["binding"]["strict23_registration"]
    raw = api.authority_raw()

    def no_source_observation(*args, **kwargs):
        pytest.fail("formal plan observed a source/target")

    monkeypatch.setattr(api, "trusted_registration", no_source_observation)
    declared = api.formal_plan(raw, strict23_registration=reference)
    assert declared["root"] == api.GENERATIONS[0]
    assert declared["source_root"] == "/Users/keith1117/Documents/TopoLab-data"
    assert declared["binding"]["strict23_registration"] == reference
    assert declared["result_window_projection_seconds"] == {"exporter": 1800, "independent": 1800}
    assert declared["source_tree"][api.PROTOCOL] == hashlib.sha256(raw).hexdigest()
    assert "public_source_identity" not in declared


def test_new_controller_factory_and_old_factory_routes(registered, tmp_path, monkeypatch):
    api, plan, source, _, _ = registered
    control = api.control
    root = tmp_path / (api.PUBLIC_PREFIX + "factory")
    root.mkdir()
    (root / "plan.json").write_bytes(producer.canonical(plan))
    transport = control.AcquisitionTransport(root, producer.sha(producer.canonical(plan)))
    assert transport.identity == api.IDENTITY
    assert transport.result_windows == (("exporter", 1800), ("independent", 1800))
    assert isinstance(
        transport.source_reader(
            source,
            execution_identity=producer.LOCAL_IDENTITY,
            source_identity_checks=True,
            source_identity_policy=api.POLICY,
        ),
        producer.Reader,
    )
    old = control.AcquisitionTransport(tmp_path / "topolab-public-formal-binding-old", "old")
    assert old.identity == control.IDENTITY
    assert old.result_windows == (("exporter", 7200), ("independent", 7200))
    assert old.source_reader(source).__class__ is producer.Reader


def test_new_authority_rejects_forged_resource_or_full_limits(registered):
    api, _, _, _, _ = registered
    value = producer.parse(api.authority_raw())
    value["input_limits"]["source_reads_all_input_attempts"] += 1
    with pytest.raises(ValueError, match="exact input/FULL/resource"):
        api.authority(producer.canonical(value))


@pytest.mark.parametrize("deadline_offset_ms", [-1, 0, 1])
def test_publication_seam_never_restarts_formal_input(registered, monkeypatch, deadline_offset_ms):
    import time
    api, _, _, _, _ = registered
    policy = api.authority()
    monkeypatch.setattr(time, "time_ns",
                        lambda: (policy["global_deadline_ms"] + deadline_offset_ms) * 10**6)
    ready = {"preparation_closure_sha256": "1" * 64, "_preparation_actual_returned_ms": 1}
    digest = "2" * 64
    actual = {"responses": [{"result": {"output": ""}}]}
    helper = api.control.load("p17_m2_source_acquisition_independent")
    monkeypatch.setattr(api, "readiness_inputs", lambda value: (ready, digest))
    monkeypatch.setattr(helper.native, "_software_bytes", lambda path: producer.canonical(actual))
    summary = {"public_actual": "already independently audited"}
    monkeypatch.setattr(api, "preflight_summary", lambda *args: summary)
    actual["responses"][0]["result"]["output"] = producer.canonical(summary).decode()
    recovery = api.control.load("p17_m2_source_binding_recovery")
    seen = []

    def actual_check(packet, argv, author):
        seen.append((argv, author))
        return 1, 2

    monkeypatch.setattr(recovery, "exact_actual", actual_check)
    monkeypatch.setattr(api, "trusted_registration", lambda *args: pytest.fail("input restarted"))
    monkeypatch.setattr(
        api.control, "published_main_readiness", lambda value, **kwargs: {"main_CI_run": 17}
    )
    if deadline_offset_ms > 0:
        with pytest.raises(ValueError, match="actual preflight differs"):
            api.publication_readiness(policy)
        assert len(seen) == 1
        return
    result = api.publication_readiness(policy)
    assert result["main_CI_run"] == 17
    assert result["readiness_reference"]["sha256"] == digest
    assert seen[0][0][-3:] == ["preflight", "--readiness-sha", digest]
    assert seen[0][1] == policy["actors"]["independent"]
    actual["responses"][0]["result"]["output"] = "{}\n"
    with pytest.raises(ValueError, match="actual preflight differs"):
        api.publication_readiness(policy)


def test_reserved_remedy_cannot_blindly_start(registered, monkeypatch):
    api, _, _, _, _ = registered
    monkeypatch.setattr(
        api, "trusted_registration", lambda *args: pytest.fail("remedy consumed registration")
    )
    with pytest.raises(ValueError, match="remedy requires separately diagnosed"):
        api.activate_formal(api.GENERATIONS[1], None)

@pytest.mark.parametrize('changed', [None, 'readiness', 'preflight'])
def test_registered_checked_setup_uses_actual_dynamic_proofs(registered, monkeypatch, changed):
    api, _, _, _, _ = registered
    control = api.control
    helper = control.base()
    root = Path(api.GENERATIONS[0])
    ready_ref = {'path': '/new-public/readiness.json', 'sha256': '1' * 64}
    pre_raw = b'{"new_public_actual":true}\n'
    pre_ref = {'path': '/new-public/preflight.json', 'sha256': producer.sha(pre_raw)}
    policy = {'actors': {'executor': '/root', 'independent': '/new-reviewer'},
              'execution_identity': api.IDENTITY, 'readiness_path': ready_ref['path'],
              'independent_preflight_actual_path': pre_ref['path']}
    plan = {'formal_authority': True, 'execution_identity': api.IDENTITY,
            'scope': control.FORMAL_SCOPE, 'contract_sha256': '2' * 64, 'source_tree': {},
            'actor_activation_UTC_seconds': 1, 'activation_readiness': ready_ref,
            'independent_preflight': pre_ref}
    plan_sha, source_sha = helper.sha(helper.canonical(plan)), helper.sha(helper.canonical({}))
    acquired = {'plan_sha256': plan_sha, 'source_tree_sha256': source_sha}
    proof = {'plan_sha256': plan_sha, 'source_tree_sha256': source_sha,
             'contract_sha256': plan['contract_sha256'],
             'lease_record_sha256': helper.sha(helper.canonical(acquired)), 'lease_identity': {},
             'scope': plan['scope'], 'execution_identity': api.IDENTITY,
             'setup_start_UTC_seconds': 1, 'setup_end_UTC_seconds': 2, 'setup_seconds': 1,
             'formal_readiness_verified': True, 'filesystem': {'local_filesystem': True},
             'readiness': dict(actors=policy['actors'], main='3' * 40, main_CI_run=7,
                preparation_closure_sha256='4' * 64,
                independent_preflight_sha256=pre_ref['sha256'],
                readiness_reference=dict(ready_ref), independent_preflight_reference=dict(pre_ref))}
    if changed:
        key = 'readiness_reference' if changed == 'readiness' else 'independent_preflight_reference'
        proof['readiness'][key]['sha256'] = '0' * 64
    records = {'setup-proof.json': proof, 'custody-acquired.json': acquired,
               'custody-lock-identity.json': {}}
    monkeypatch.setattr(helper, 'read_json', lambda p: records[p.name])
    monkeypatch.setattr(control, 'authority_for_root', lambda p: (producer.canonical(policy), 1))
    monkeypatch.setattr(api, 'readiness_inputs', lambda p: (
        {'preparation_closure_sha256': '4' * 64}, ready_ref['sha256']))
    checker = control.load('p17_m2_source_acquisition_independent')
    monkeypatch.setattr(checker.native, '_software_bytes', lambda p: pre_raw)
    checked = []
    monkeypatch.setattr(checker, 'check_funded_preflight',
                        lambda p, raw: checked.append((p, raw)))
    if changed:
        with pytest.raises(ValueError, match='REGISTERED_SETUP_DYNAMIC_PROOFS_REQUIRED'):
            control.checked_setup(root, plan)
    else:
        assert control.checked_setup(root, plan) is proof
        assert checked == [(plan, pre_raw)]


def test_new_registration_certificate_pairs_match_metadata4_contract():
    import json

    inputs_path = REPO / 'docs/planning/p17_m2_registered_input_v2_protocol.json'
    inputs = json.loads(inputs_path.read_bytes())
    metadata_path = (REPO / 'docs/planning'
                     / 'p17_m2_source_binding_certificate_recovery_v4_protocol.json')
    metadata = json.loads(metadata_path.read_bytes())
    for kind in ('public', 'formal'):
        expected = metadata['certificate_paths'][kind][0]
        assert inputs['registration'][kind]['certificate_paths'] == expected


def test_checked_reconstruction_keeps_validated_dynamic_refs(registered, monkeypatch):
    api, _, _, _, _ = registered
    control, root = api.control, Path(api.GENERATIONS[0])
    refs = {'activation_readiness': {'path': '/public/readiness', 'sha256': '1' * 64},
            'independent_preflight': {'path': '/public/preflight', 'sha256': '2' * 64}}
    saved = {'binding': {'strict23_registration': {'public': True}}, **refs}
    expected = producer.sha(producer.canonical(saved))
    policy = {'readiness_path': refs['activation_readiness']['path'],
              'independent_preflight_actual_path': refs['independent_preflight']['path']}
    monkeypatch.setattr(control.base(), 'read_json', lambda path: saved)
    monkeypatch.setattr(control, 'authority_for_root', lambda path: (b'{}', 1))
    monkeypatch.setattr(api, 'authority', lambda raw: policy)
    pins = []
    monkeypatch.setattr(api, '_read_pin', lambda ref: pins.append(ref))
    monkeypatch.setattr(control, 'formal_plan', lambda *args, **kwargs: {'public': True})
    checker = control.load('p17_m2_source_acquisition_independent')

    class VerifiedBeforeAnyTargetIO(Exception):
        pass

    def validate(plan):
        assert all(plan.get(key) == ref for key, ref in refs.items())
        raise VerifiedBeforeAnyTargetIO

    monkeypatch.setattr(checker, 'validate_binding', validate)
    with pytest.raises(VerifiedBeforeAnyTargetIO):
        control.checked(root, expected)
    assert pins == list(refs.values())
