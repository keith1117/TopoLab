"""Behavior at the approved S1 consumption interface; NEW public data only."""

import importlib.util
from pathlib import Path

import pytest


def load_reader(path=None):
    path = path or Path(__file__).parents[1] / "scripts/p17_m2_verified_input.py"
    spec = importlib.util.spec_from_file_location("verified_input_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def public_facts(tmp_path, monkeypatch):
    """Immutable software snapshot; raw tool facts remain explicitly unit fixtures."""
    import shutil
    import sys

    repo = Path(__file__).parents[1]
    runtime = tmp_path / "frozen-runtime"
    (runtime / "scripts").mkdir(parents=True)
    (runtime / "tests").mkdir()
    (runtime / "docs/planning").mkdir(parents=True)
    for path in (repo / "scripts").glob("p17_m2_*"):
        if path.is_file():
            shutil.copyfile(path, runtime / "scripts" / path.name)
    for name in (
        "p17_m2_content_verified_custody_protocol.json",
        "p17_m2_content_verified_custody_proposal.json",
        "p17_m2_input_export_preparation_proposal.json",
    ):
        shutil.copyfile(repo / "docs/planning" / name, runtime / "docs/planning" / name)
    for name in (
        "test_p17_m2_content_verified_independent.py",
        "test_p17_m2_local_input_pipeline.py",
        "test_p17_m2_input_export_independent.py",
    ):
        shutil.copyfile(repo / "tests" / name, runtime / "tests" / name)
    shutil.copyfile(repo / "uv.lock", runtime / "uv.lock")
    monkeypatch.delitem(sys.modules, "p17_m2_content_verified_independent", raising=False)
    path = runtime / "tests/test_p17_m2_content_verified_independent.py"
    spec = importlib.util.spec_from_file_location("frozen_public_certificate_fixtures", path)
    fixture = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixture)
    data = tmp_path / "new-public-data"
    data.mkdir(mode=0o700)
    checker, bundle, events = fixture.public_certificate_facts(data, monkeypatch)
    return checker, bundle, events, runtime / "scripts/p17_m2_verified_input.py"


def test_unverified_certificate_refuses_before_opening_any_data(monkeypatch):
    reader = load_reader()

    def forbidden_open(*args, **kwargs):
        pytest.fail("unverified certificate reached filesystem")

    monkeypatch.setattr("os.open", forbidden_open)
    with pytest.raises(ValueError, match="UNVERIFIED_CERTIFICATE"):
        reader.VerifiedInput({"status": "PASS", "consumer_authorized": True}, "producer")


def test_verified_consumer_uses_one_captured_buffer_and_rejects_same_hash_replacement(
    tmp_path,
    monkeypatch,
):
    import json
    import os

    checker, bundle, events, reader_path = public_facts(tmp_path, monkeypatch)
    certificate = checker.audit_public_certificate(bundle, trusted_tool_events=events)
    lease = certificate.acquire_reader("scientific-producer")
    consumer = load_reader(reader_path).VerifiedInput(
        certificate, "scientific-producer", reader_lease=lease
    )
    root = Path(bundle["root"])
    models = (root / "models.json").read_bytes()
    checkpoint = next(m["path"] for m in bundle["manifest"]["members"] if m["type"] == "checkpoint")
    original_checkpoint = (root / checkpoint).read_bytes()

    def decode(captured):
        # Change disk after the verified read, while the decoder uses its exact bytes.
        (root / "models.json").write_bytes(b"{}\n")
        assert captured == models and type(captured) is bytes
        return json.loads(captured)

    assert consumer.consume("models.json", decode) == json.loads(models)
    replacement = root / "same-bytes-new-inode"
    replacement.write_bytes(original_checkpoint)
    replacement.chmod(0o600)
    os.replace(replacement, root / checkpoint)
    with pytest.raises(ValueError, match="(?i)identity"):
        consumer.consume(checkpoint, lambda _: pytest.fail("changed identity was decoded"))


def test_lease_lost_during_member_read_stops_before_decoder(tmp_path, monkeypatch):
    import os

    checker, bundle, events, reader_path = public_facts(tmp_path, monkeypatch)
    certificate = checker.audit_public_certificate(bundle, trusted_tool_events=events)
    lease = certificate.acquire_reader("scientific-producer")
    consumer = load_reader(reader_path).VerifiedInput(
        certificate, "scientific-producer", reader_lease=lease
    )
    original_stat = os.stat
    observations = 0

    def remove_lease_at_closing_stat(name, *args, **kwargs):
        nonlocal observations
        info = original_stat(name, *args, **kwargs)
        if name == "models.json" and kwargs.get("follow_symlinks") is False:
            observations += 1
            if observations == 2:
                Path(lease.path).unlink()
        return info

    monkeypatch.setattr(os, "stat", remove_lease_at_closing_stat)
    with pytest.raises((ValueError, OSError)):
        consumer.consume("models.json", lambda _: pytest.fail("decoder used a lost lease"))
    assert consumer.failure["source_facts"]["models.json"]["returned_bytes"] > 0


@pytest.mark.parametrize("damage", ["permissions", "hardlink"])
def test_consumer_refuses_nonprivate_or_linked_member_before_decoder(tmp_path, monkeypatch, damage):
    checker, bundle, events, reader_path = public_facts(tmp_path, monkeypatch)
    certificate = checker.audit_public_certificate(bundle, trusted_tool_events=events)
    lease = certificate.acquire_reader("scientific-producer")
    consumer = load_reader(reader_path).VerifiedInput(
        certificate, "scientific-producer", reader_lease=lease
    )
    target = Path(bundle["root"]) / "models.json"
    if damage == "permissions":
        target.chmod(0o644)
    else:
        (tmp_path / "new-public-extra-link").hardlink_to(target)
    with pytest.raises(ValueError, match="PRIVATE"):
        consumer.consume("models.json", lambda _: pytest.fail("nonprivate member decoded"))


def test_failed_consumer_cannot_recreate_a_reader_with_the_same_capability(tmp_path, monkeypatch):
    checker, bundle, events, path = public_facts(tmp_path, monkeypatch)
    certificate = checker.audit_public_certificate(bundle, trusted_tool_events=events)
    lease = certificate.acquire_reader("scientific-producer")
    module = load_reader(path)
    consumer = module.VerifiedInput(certificate, "scientific-producer", reader_lease=lease)

    def reject(raw):
        raise ValueError("NEW_PUBLIC_DECODER_FAILURE")

    with pytest.raises(ValueError, match="NEW_PUBLIC_DECODER_FAILURE"):
        consumer.consume("models.json", reject)
    assert consumer.failure["source_facts"]["models.json"]["returned_bytes"] > 0

    def forbidden_open(*args, **kwargs):
        pytest.fail("stopped capability reached filesystem again")

    monkeypatch.setattr("os.open", forbidden_open)
    with pytest.raises(ValueError, match="STOP"):
        module.VerifiedInput(certificate, "scientific-producer", reader_lease=lease)
